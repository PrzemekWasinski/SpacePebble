import pygame
import sys
import datetime
from functions import fetch_neo_update_db, update_passed, fetch_asteroids, km_to_px, utc_to_local, time_until, get_stats, get_virtual_mouse, draw_trajectory
from gui import draw_text, draw_text_centered, draw_text_right, colours
import sqlite3
import os 
import math

DB_FILE = "asteroids.db"

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS asteroids (
    id TEXT PRIMARY KEY,
    name TEXT,
    close_approach_utc TEXT,
    magnitude REAL,
    min_diameter REAL,
    max_diameter REAL,
    hazardous INTEGER,
    speed REAL,
    distance REAL,
    angle REAL,
    passed INTEGER DEFAULT 0
)
''')
conn.commit()
#True if using a desktop, False if using something like a small raspberry pi screen
DESKTOP = True

asteroid_size = 2
earth_size = 4
square_size = 1080
mover = 0
if not DESKTOP:
    asteroid_size = 4
    earth_size = 6
    square_size = 1280
    mover = ((1920 - 1280) / 2)

pygame.init()
pygame.mouse.set_visible(DESKTOP)
clock = pygame.time.Clock()

display_width, display_height = 0, 0
if DESKTOP:
    display_width = 1920
    display_height = 1080
else:
    display_width = 480
    display_height = 320

display = pygame.display.set_mode((display_width, display_height), pygame.FULLSCREEN)
pygame_icon = pygame.image.load('./assets/images/icon.png') 
pygame.display.set_icon(pygame_icon)

width, height = 1920, 1080
screen = pygame.Surface((width, height))
pygame.display.set_caption("Space Pebble")

#Fetch new data and save it in the db
date = datetime.date.today().strftime("%Y-%m-%d")
fetch_neo_update_db(conn, c, date)
#Save db data to memory
asteroids = fetch_asteroids(c)
#Upade any passed asteroids to passed without notifying
update_passed(conn, c, asteroids, False)

clock_font = pygame.font.Font(os.path.join("assets", "fonts", "DS-DIGI.TTF"), 64) 
date_font = pygame.font.Font(os.path.join("assets", "fonts", "DS-DIGI.TTF"), 54) 
font1 = pygame.font.Font(os.path.join("assets", "fonts", "CreatoDisplay-Regular.otf"), 24)
font2 = pygame.font.Font(os.path.join("assets", "fonts", "CreatoDisplay-Regular.otf"), 19)

if not DESKTOP:
    font1 = pygame.font.Font(os.path.join("assets", "fonts", "CreatoDisplay-Regular.otf"), 32)
    font2 = pygame.font.Font(os.path.join("assets", "fonts", "CreatoDisplay-Regular.otf"), 28)

all_time = False
  
tapped = False
running = True
while running:
    clock.tick(60)
    
    if date != datetime.date.today().strftime("%Y-%m-%d"): #If it's the next day
        date = datetime.date.today().strftime("%Y-%m-%d") #Set new date
        fetch_neo_update_db(conn, c, date) #Calls API and updates DB
        asteroids = fetch_asteroids(c) #Updates server memory with DB data
        
    update_passed(conn, c, asteroids, True)
    
    cursor_x, cursor_y = get_virtual_mouse(display_width, display_height) 
            
    screen.fill((0, 0, 0)) #Draw background

    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            tapped = not tapped
            if cursor_x > 1709 and cursor_x < 1879 and cursor_y > 10 and cursor_y < 50:
                all_time = True
            if cursor_x > 1525 and cursor_x < 1690 and cursor_y > 10 and cursor_y < 50:
                all_time = False
            if cursor_x > 0 and cursor_x < mover * 2 and cursor_y > 0 and cursor_y < 100:
                pygame.quit()
    
    ###########
    ### GUI ###
    ###########
    
    now = datetime.datetime.now()
    if DESKTOP:
        draw_text_centered(screen, f'{now.strftime("%H:%M:%S")}', clock_font, colours["time"], 210, 45)
        draw_text_centered(screen, f'{now.strftime("%d/%m/%Y")}', date_font, colours["time"], 210, 105)

        pygame.draw.line(screen, colours["border"], (0, 150), (420, 150), 1)
    else:
        draw_text_centered(screen, f'{now.strftime("%H:%M:%S")}', clock_font, colours["time"], mover, 45)

        pygame.draw.line(screen, colours["border"], (0, 90), (mover * 2, 90))
    
    ###########
    ### GUI ###
    ###########    
    
    ############################
    ### PLANETS AND ASEOIDS ####
    ############################
    center_x, center_y = width // 2, height // 2 #Center of screen
    max_radius = square_size // 2 #Max distance from earth to asteroid
    

    if DESKTOP: #Moon is a desktop version exclusive :)
        pygame.draw.rect(screen, colours["border"], (420, 0, square_size, square_size), 1)

        #Draw Earth
        pygame.draw.circle(screen, colours["earth"], (center_x, center_y), earth_size)
        #Orbit
        pygame.draw.circle(screen, colours["trajectory"], (center_x, center_y), 15, 1)

        #Position moon using 24-hour clock
        now = datetime.datetime.now()
        hours = now.hour + now.minute / 60.0 + now.second / 3600.0
        angle = math.radians((hours / 12.0) * 360.0 - 90)

        r = km_to_px(340_000, 20_000_000, max_radius)
        moon_x = center_x + (r + 6) * math.cos(angle)
        moon_y = center_y + (r + 6) * math.sin(angle)

        # Draw Moon
        pygame.draw.circle(screen, colours["moon"], (int(moon_x), int(moon_y)), 2)
    else:
        pygame.draw.rect(screen, colours["border"], (1920 - 1280, 0, square_size, square_size), 1)

        #Draw Earth
        pygame.draw.circle(screen, colours["earth"], (center_x + mover, center_y), earth_size)

    #Draw asteroids and their info       
    text_y = 200
    hovered_asteroid = None
    if DESKTOP:
        draw_text_centered(screen, "Asteroid Schedule", font1, (255, 255, 255), 210, 180)
    for asteroid in asteroids:
        r = km_to_px(int(asteroid["distance"]), 20_000_000, max_radius)
        angle_rad = math.radians(asteroid["angle"])
        x = center_x + r * math.cos(angle_rad)
        y = center_y + r * math.sin(angle_rad)
        if asteroid["passed"] == 0:
            asteroid["x"] = x
            asteroid["y"] = y 
        else:
            asteroid["x"] = x
            asteroid["y"] = y  
            
        if asteroid["passed"] == 0:
            if DESKTOP:
                draw_text(screen, asteroid["name"], font1, colours["text"], 10, text_y)
                draw_text_right(screen, utc_to_local(str(asteroid["close_approach_utc"])[-5:]), font1, colours["text"], 410, text_y)
                draw_text(screen, f'Closest approach in: {time_until(utc_to_local(str(asteroid["close_approach_utc"])[-5:]))}', font2, colours["gray_text"], 10, text_y + 30)
                text_y += 75
            pygame.draw.circle(screen, (255, 0, 0), (int(x) + mover, int(y)), asteroid_size) #The closest approach point of the asteroid
            draw_trajectory(screen, width, height, asteroid, mover, DESKTOP)  
        else:
            pygame.draw.circle(screen, colours["passed_asteroid"], (int(x) + mover, int(y)), asteroid_size)
            
        if asteroid["passed"] == 1:
            if cursor_x >= (asteroid["x"] + mover) - 25 and cursor_x <= (asteroid["x"] + mover) + 25 and cursor_y >= asteroid["y"] - 25 and cursor_y <= asteroid["y"] + 25:
                hovered_asteroid = asteroid
                pygame.draw.circle(screen, colours["hovered_asteroid"], (asteroid["x"] + mover, asteroid["y"]), asteroid_size)     
        else:
            if cursor_x >= (asteroid["x"]) - 25 and cursor_x <= (asteroid["x"]) + 25 and cursor_y >= asteroid["y"] - 25 and cursor_y <= asteroid["y"] + 15:
                hovered_asteroid = asteroid

                if asteroid["passed"] == 1:
                    pygame.draw.circle(screen, colours["hovered_asteroid"], (asteroid["x"] + mover, asteroid["y"]), asteroid_size)
                else:
                    pygame.draw.circle(screen, colours["hovered_asteroid"], (asteroid["x"], asteroid["y"]), asteroid_size)

            
        if DESKTOP:
            pygame.draw.rect(screen, (0, 0, 0), (1500, 570, 420, 510)) 
        
    if text_y == 200:
        if DESKTOP:
            draw_text_centered(screen, "No more asteroids", font1, colours["gray_text"], 210, 560)
            draw_text_centered(screen, "passing today", font1, colours["gray_text"], 210, 590)
            
    if hovered_asteroid != None:
        if not DESKTOP:
            if hovered_asteroid["passed"] == 1:
                draw_text_centered(screen, hovered_asteroid["name"], font2, colours["text"], hovered_asteroid["x"] + mover, hovered_asteroid["y"] - 20)
            else:
                draw_text_centered(screen, hovered_asteroid["name"], font2, colours["text"], hovered_asteroid["x"], hovered_asteroid["y"] - 20)
            
            if hovered_asteroid["passed"] == 0: #if asteroid hasnt passed yet draw its distance  
                draw_text_centered(screen, "Live Distances:", font1, colours["text"], mover, 890)
                
                draw_text(screen, "Cloase Approach Point:", font1, colours["text"], 10, 940)
                draw_text_right(screen, f'{str(round(hovered_asteroid["ca_distance"]))}km', font1, colours["text"], (mover * 2) - 10, 940)
                
                draw_text(screen, "Earth:", font1, colours["text"], 10, 980)
                draw_text_right(screen, f'{str(round(hovered_asteroid["earth_distance"]))}km', font1, colours["text"], (mover * 2) - 10, 980)
            
            draw_text_centered(screen, hovered_asteroid["name"], font1, colours["text"], mover, 550)
            
            draw_text(screen, "Size:", font1, colours["text"], 10, 580)
            draw_text_right(screen, str(round((hovered_asteroid["min_diameter"] + hovered_asteroid["max_diameter"]) / 2, 2)) + "m", font1, colours["text"], (mover * 2) - 10, 580)
            
            draw_text(screen, "Passed:", font1, colours["text"], 10, 620)
            if hovered_asteroid["passed"] == 0:
                draw_text_right(screen, "No", font1, colours["text"], (mover * 2), 620)
            else:
                draw_text_right(screen, "Yes", font1, colours["text"], (mover * 2), 620)
            
            dt = datetime.datetime.strptime(str(hovered_asteroid["close_approach_utc"])[:11], "%Y-%b-%d")

            draw_text(screen, "Date:", font1, colours["text"], 10, 660)
            draw_text_right(screen, dt.strftime("%d/%m/%Y"), font1, colours["text"], (mover * 2) - 10, 660)
            
            draw_text(screen, "Distance:", font1, colours["text"], 10, 700)
            draw_text_right(screen, str(round(hovered_asteroid["distance"])) + "km", font1, colours["text"], (mover * 2) - 10, 700)
            
            draw_text(screen, "Speed:", font1, colours["text"], 10, 740)
            draw_text_right(screen, str(round(hovered_asteroid["speed"])) + "km/ph", font1, colours["text"], (mover * 2) - 10, 740)
            
            draw_text(screen, "Magnitude:", font1, colours["text"], 10, 780)
            draw_text_right(screen, str(round(float(hovered_asteroid["magnitude"]), 2)) + "H", font1, colours["text"], (mover * 2) - 10, 780)
            
            draw_text(screen, "Hazardous:", font1, colours["text"], 10, 820)
            
            if hovered_asteroid["hazardous"] == 0:
                draw_text_right(screen, "No", font1, colours["text"], (mover * 2) - 10, 820)
            else:
                draw_text_right(screen, "Yes", font1, colours["text"], (mover * 2) - 10, 820)
        else:
            draw_text_centered(screen, hovered_asteroid["name"], font2, (225, 225, 225), hovered_asteroid["x"], hovered_asteroid["y"] - 20)
        
            if hovered_asteroid["passed"] == 0: #if asteroid hasnt passed yet draw its distance           
                draw_text_centered(screen, "Distances:", font1, (255, 255, 255), 1710, 825)
                
                draw_text(screen, "Cloase Approach Point:", font1, (255, 255, 255), 1510, 855)
                draw_text_right(screen, f'{str(round(hovered_asteroid["ca_distance"]))}km', font1, (255, 255, 255), 1910, 855)
                
                draw_text(screen, "Earth:", font1, (255, 255, 255), 1510, 895)
                draw_text_right(screen, f'{str(round(hovered_asteroid["earth_distance"]))}km', font1, (255, 255, 255), 1910, 895)
            
            draw_text_centered(screen, hovered_asteroid["name"], font1, (255, 255, 255), 1710, 505)
            
            draw_text(screen, "Size:", font1, (255, 255, 255), 1510, 535)
            draw_text_right(screen, str(round((hovered_asteroid["min_diameter"] + hovered_asteroid["max_diameter"]) / 2, 2)) + "m", font1, (255, 255, 255), 1910, 535)
            
            draw_text(screen, "Passed:", font1, (255, 255, 255), 1510, 575)
            if hovered_asteroid["passed"] == 0:
                draw_text_right(screen, "No", font1, (255, 255, 255), 1910, 575)
            else:
                draw_text_right(screen, "Yes", font1, (255, 255, 255), 1910, 575)
            
            dt = datetime.datetime.strptime(str(hovered_asteroid["close_approach_utc"])[:11], "%Y-%b-%d")
            draw_text(screen, "Date:", font1, (255, 255, 255), 1510, 615)
            draw_text_right(screen, dt.strftime("%d/%m/%Y"), font1, (255, 255, 255), 1910, 615)
            
            draw_text(screen, "Distance:", font1, (255, 255, 255), 1510, 655)
            draw_text_right(screen, str(round(hovered_asteroid["distance"])) + "km", font1, (255, 255, 255), 1910, 655)
            
            draw_text(screen, "Speed:", font1, (255, 255, 255), 1510, 695)
            draw_text_right(screen, str(round(hovered_asteroid["speed"])) + "km/ph", font1, (255, 255, 255), 1910, 695)
            
            draw_text(screen, "Magnitude:", font1, (255, 255, 255), 1510, 735)
            draw_text_right(screen, str(hovered_asteroid["magnitude"]), font1, (255, 255, 255), 1910, 735)
            
            draw_text(screen, "Hazardous:", font1, (255, 255, 255), 1510, 775)
            
            if hovered_asteroid["hazardous"] == 0:
                draw_text_right(screen, "No", font1, (255, 255, 255), 1910, 775)
            else:
                draw_text_right(screen, "Yes", font1, (255, 255, 255), 1910, 775)
    else:
        if DESKTOP:
            draw_text_centered(screen, "Hover over an asteroid", font1, colours["gray_text"], 1710, 720)
            draw_text_centered(screen, "to see more information", font1, colours["gray_text"], 1710, 750)
            draw_text_centered(screen, "about it", font1, colours["gray_text"], 1710, 780)
        else:
            draw_text_centered(screen, "Hover over an asteroid", font1, colours["gray_text"], mover, 730)
            draw_text_centered(screen, "to see more information", font1, colours["gray_text"], mover, 760)
            draw_text_centered(screen, "about it", font1, colours["gray_text"], mover, 790)

    
    if DESKTOP:
        if all_time:
            all_time_stats = get_stats(asteroids, True)
            #pygame.draw.line(screen, (255, 255, 255), (1719, 50), (1865, 50))
            pygame.draw.rect(screen, colours["button"], (1709, 10, 170, 50))
            
            draw_text(screen, "Total Asteroids Passed:", font1, colours["text"], 1510, 75)   
            draw_text_right(screen, str(all_time_stats["total"]), font1, colours["text"], 1910, 75)
            
            draw_text(screen, "Biggest:", font1, colours["text"], 1510, 120)
            draw_text(screen, f'{all_time_stats["biggest"]["name"]}', font2, colours["text"], 1510, 150)
            draw_text_right(screen, f'({str(round(all_time_stats["biggest"]["size"]))}m)', font2, colours["text"], 1910, 150)
            
            draw_text(screen, "Fastest:", font1, colours["text"], 1510, 195)
            draw_text(screen, f'{all_time_stats["fastest"]["name"]}', font2, colours["text"], 1510, 225)
            draw_text_right(screen, f'({str(round(all_time_stats["fastest"]["speed"]))}km/ph)', font2, colours["text"], 1910, 225)
            
            draw_text(screen, "Brightest:", font1, colours["text"], 1510, 270)
            draw_text(screen, f'{all_time_stats["brightest"]["name"]}', font2, colours["text"], 1510, 300)
            draw_text_right(screen, f'({str(round(all_time_stats["brightest"]["magnitude"]))}H)', font2, colours["text"], 1910, 300)
            
            draw_text(screen, "Closest:", font1, colours["text"], 1510, 345)
            draw_text(screen, f'{all_time_stats["closest"]["name"]}', font2, colours["text"], 1510, 375)
            draw_text_right(screen, f'({str(round(all_time_stats["closest"]["distance"]))}km)', font2, colours["text"], 1910, 375)
            
            draw_text(screen, "Hazardous Percentage:", font1, colours["text"], 1510, 420)
            if all_time_stats["hazardous"] != 0 and all_time_stats["total"] != 0:
                hazardous_percentage = round((all_time_stats["hazardous"] / all_time_stats["total"]) * 100)
            else:
                hazardous_percentage = 0
            draw_text_right(screen, f'{hazardous_percentage}%', font1, colours["text"], 1910, 420)
            
        else:    
            today_stats = get_stats(asteroids, False)    
            #pygame.draw.line(screen, colours["text"], (1535, 50), (1677, 50))
            pygame.draw.rect(screen, colours["button"], (1525, 10, 165, 50))
            
            draw_text(screen, "Total Asteroids Passed:", font1, colours["text"], 1510, 75)   
            draw_text_right(screen, str(today_stats["total"]), font1, colours["text"], 1910, 75)
            
            draw_text(screen, "Biggest:", font1, colours["text"], 1510, 120)
            draw_text(screen, f'{today_stats["biggest"]["name"]}', font2, colours["text"], 1510, 150)
            draw_text_right(screen, f'({str(round(today_stats["biggest"]["size"]))}m)', font2, colours["text"], 1910, 150)
            
            draw_text(screen, "Fastest:", font1, colours["text"], 1510, 195)
            draw_text(screen, f'{today_stats["fastest"]["name"]}', font2, colours["text"], 1510, 225)
            draw_text_right(screen, f'({str(round(today_stats["fastest"]["speed"]))}km/ph)', font2, colours["text"], 1910, 225)
            
            draw_text(screen, "Brightest:", font1, colours["text"], 1510, 270)
            draw_text(screen, f'{today_stats["brightest"]["name"]}', font2, colours["text"], 1510, 300)
            draw_text_right(screen, f'({str(round(today_stats["brightest"]["magnitude"]))}H)', font2, colours["text"], 1910, 300)
            
            draw_text(screen, "Closest:", font1, colours["text"], 1510, 345)
            draw_text(screen, f'{today_stats["closest"]["name"]}', font2, colours["text"], 1510, 375)
            draw_text_right(screen, f'({str(round(today_stats["closest"]["distance"]))}km)', font2, colours["text"], 1910, 375)
            
            draw_text(screen, "Hazardous Percentage:", font1, colours["text"], 1510, 420)
            if today_stats["hazardous"] != 0 and today_stats["total"] != 0: 
                hazardous_percentage = round((today_stats["hazardous"] / today_stats["total"]) * 100)
            else:
                hazardous_percentage = 0
            draw_text_right(screen, f'{hazardous_percentage}%', font1, colours["text"], 1910, 420)
    else:
        all_time_stats = get_stats(asteroids, True)

        draw_text(screen, "Biggest:", font2, colours["text"], 10, 100)
        draw_text(screen, f"{all_time_stats['biggest']['name']}:", font1, colours["text"], 10, 130)
        draw_text_right(screen, f"{all_time_stats['biggest']['size']}m", font1, colours["text"], (mover * 2) - 10, 130)

        draw_text(screen, "Fastest:", font2, colours["text"], 10, 180)
        draw_text(screen, f"{all_time_stats['fastest']['name']}:", font1, colours["text"], 10, 210)
        draw_text_right(screen, f"{all_time_stats['fastest']['speed']}Kmph", font1, colours["text"], (mover * 2) - 10, 210)

        draw_text(screen, "Closest:", font2, colours["text"], 10, 260)
        draw_text(screen, f"{all_time_stats['closest']['name']}:", font1, colours["text"], 10, 290)
        draw_text_right(screen, f"{all_time_stats['closest']['distance']}Km", font1, colours["text"], (mover * 2) - 10, 290)

        draw_text(screen, "Brightest:", font2, colours["text"], 10, 340)
        draw_text(screen, f"{all_time_stats['brightest']['name']}", font1, colours["text"], 10, 370)
        draw_text_right(screen, f"{all_time_stats['brightest']['magnitude']}H", font1, colours["text"], (mover * 2) - 10, 370)

        draw_text(screen, "Total:", font1, colours["text"], 10, 420)
        draw_text_right(screen, f"{all_time_stats['total']}", font1, colours["text"], (mover * 2) - 10, 420)

        draw_text(screen, "Hazardous Percentage:", font1, colours["text"], 10, 470)
        draw_text_right(screen, f"{all_time_stats['hazardous']}%", font1, colours["text"], (mover * 2) - 10, 470)

        pygame.draw.line(screen, colours["border"], (0, 520), (mover * 2, 520))
    today_text_colour = (255, 255, 255)
    if DESKTOP:
        if cursor_x > 1709 and cursor_x < 1879 and cursor_y > 10 and cursor_y < 50 and not all_time:
            pygame.draw.rect(screen, colours["all_time_button_hover"], (1709, 10, 170, 50))
            
        elif cursor_x > 1525 and cursor_x < 1690 and cursor_y > 10 and cursor_y < 50 and all_time:
            pygame.draw.rect(screen, colours["today_button_hover"], (1525, 10, 165, 50))
            today_text_colour = (0, 0, 0)
    
        draw_text(screen, "Today's Stats", font1, today_text_colour, 1535, 20)
        draw_text_right(screen, "All Time Stats", font1, colours["text"], 1865, 20)
        pygame.draw.line(screen, colours["border"], (1500, 470), (1920, 470)) 
        if cursor_x >= center_x - 5 and cursor_x <= center_x + 5 and cursor_y >= center_y - 5 and cursor_y <= center_y + 5:
            draw_text_centered(screen, "Earth", font2, colours["text"], center_x, center_y - 20)
        elif cursor_x >= moon_x - 5 and cursor_x <= moon_x + 5 and cursor_y >= moon_y - 5 and cursor_y <= moon_y + 5:
            draw_text_centered(screen, "Moon", font2, colours["text"], moon_x, moon_y - 20)

    
    
    scaled = pygame.transform.smoothscale(screen, display.get_size())
    display.blit(scaled, (0, 0))
    pygame.display.flip()	

pygame.quit()
sys.exit()