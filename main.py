import pygame
import sys
import datetime
import json
from functions import fetch_neo_update_db, update_passed, fetch_asteroids, km_to_px, utc_to_local, time_until, get_stats
from gui import draw_text, draw_text_centered, draw_text_right
import sqlite3
import os 
import math

DB_FILE = "asteroids.db"

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS asteroids (
    id TEXT PRIMARY KEY,
    name, REAL,
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

pygame.init()
clock = pygame.time.Clock()

width, height = 1920, 1080
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Asteroid tracker")

#Fetch new data and save it in the db
date = datetime.date.today().strftime("%Y-%m-%d")
fetch_neo_update_db(conn, c, date)
#Save db data to memory
asteroids = fetch_asteroids(c)
#Upade any passed asteroids to passed without notifying
update_passed(conn, c, asteroids, False)

clock_font = pygame.font.Font(os.path.join("assets", "fonts", "DS-DIGI.TTF"), 64) 
date_font = pygame.font.Font(os.path.join("assets", "fonts", "DS-DIGI.TTF"), 54) 
font1 = pygame.font.Font(os.path.join("assets", "fonts", "CreatoDisplay-Regular.otf"), 32)
font2 = pygame.font.Font(os.path.join("assets", "fonts", "CreatoDisplay-Regular.otf"), 24)
    
running = True
while running:
    clock.tick(60)
    
    if date != datetime.date.today().strftime("%Y-%m-%d"): #If it's the next day
        fetch_neo_update_db(conn, c, date) #Calls API and updates DB
        asteroids = fetch_asteroids(c) #Updates server memory with DB data
        date = datetime.date.today().strftime("%Y-%m-%d")
        
    update_passed(conn, c, asteroids, True)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    screen.fill((0, 0, 0)) #Draw background
    
    ###########
    ### GUI ###
    ###########
    
    now = datetime.datetime.now()
    draw_text_centered(screen, f'{now.strftime("%H:%M:%S")}', clock_font, (255, 0, 0), 210, 45)
    draw_text_centered(screen, f'{now.strftime("%d/%m/%Y")}', date_font, (255, 0, 0), 210, 105)
    
    ###########
    ### GUI ###
    ###########    
    
    ############################
    ### PLANETS AND ASEOIDS ####
    ############################
    square_size = 1080 #Asteroid and planets area
    center_x, center_y = width // 2, height // 2 #Center of screen
    max_radius = square_size // 2 #Max distance from earth to asteroid
    
    pygame.draw.rect(screen, (100, 100, 100), (420, 0, square_size, square_size), 1)

    #Draw Earth
    pygame.draw.circle(screen, (0, 255, 0), (center_x, center_y), 4)
    pygame.draw.circle(screen, (100, 100, 100), (center_x, center_y), 16, 1)

    #Position moon using 24-hour clock
    now = datetime.datetime.now()
    hours = now.hour + now.minute / 60.0 + now.second / 3600.0
    angle = math.radians((hours / 24.0) * 360.0 - 90)

    r = km_to_px(340_000, 20_000_000, max_radius)
    moon_x = center_x + (r + 6) * math.cos(angle)
    moon_y = center_y + (r + 6) * math.sin(angle)

    # Draw Moon
    pygame.draw.circle(screen, (255, 255, 255), (int(moon_x), int(moon_y)), 2)

    #Draw asteroids and their info       
    cursor_x, cursor_y = pygame.mouse.get_pos() 
    text_y = 185
    hovered_asteroid = None
    for asteroid in asteroids:
        
        r = km_to_px(int(asteroid["distance"]), 20_000_000, max_radius)
        
        angle_rad = math.radians(asteroid["angle"])
        x = center_x + r * math.cos(angle_rad)
        y = center_y + r * math.sin(angle_rad)
        asteroid["x"] = x
        asteroid["y"] = y            
            
        pygame.draw.line(screen, (100, 100, 100), (0, 150), (420, 150), 1)
        
        if asteroid["passed"] == 0:
            draw_text(screen, asteroid["name"], font1, (255, 255, 255), 10, text_y)
            draw_text(screen, utc_to_local(str(asteroid["close_approach_utc"])[-5:]), font1, (255, 255, 255), 325, text_y)
            draw_text(screen, f'Closest approach in: {time_until(utc_to_local(str(asteroid["close_approach_utc"])[-5:]))}', font2, (175, 175, 175), 10, text_y + 35)
            pygame.draw.circle(screen, (150, 150, 150), (int(x), int(y)), 1)
            text_y += 75
        else:
            pygame.draw.circle(screen, (225, 225, 225), (int(x), int(y)), 1)
            
        if cursor_x >= asteroid["x"] - 5 and cursor_x <= asteroid["x"] + 5 and cursor_y >= asteroid["y"] - 5 and cursor_y <= asteroid["y"] + 5:
            hovered_asteroid = asteroid
            
        pygame.draw.rect(screen, (0, 0, 0), (1500, 570, 420, 510)) 
            
    if hovered_asteroid != None:
        if hovered_asteroid["passed"] == 1:
            draw_text_centered(screen, hovered_asteroid["name"], font2, (225, 225, 225), hovered_asteroid["x"], hovered_asteroid["y"] - 20)
        else:
            draw_text_centered(screen, hovered_asteroid["name"], font2, (90, 90, 90), hovered_asteroid["x"], hovered_asteroid["y"] - 20)
        
        draw_text_centered(screen, hovered_asteroid["name"], font1, (255, 255, 255), 1710, 610)
        
        draw_text(screen, "Size:", font1, (255, 255, 255), 1510, 650)
        draw_text_right(screen, str(round((hovered_asteroid["min_diameter"] + hovered_asteroid["max_diameter"]) / 2, 2)) + "m", font1, (255, 255, 255), 1910, 650)
        
        draw_text(screen, "Passed:", font1, (255, 255, 255), 1510, 700)
        if hovered_asteroid["passed"] == 0:
            draw_text_right(screen, "No", font1, (255, 255, 255), 1910, 700)
        else:
            draw_text_right(screen, "Yes", font1, (255, 255, 255), 1910, 700)
        
        dt = datetime.datetime.strptime(str(hovered_asteroid["close_approach_utc"])[:11], "%Y-%b-%d")
        draw_text(screen, "Date:", font1, (255, 255, 255), 1510, 750)
        draw_text_right(screen, dt.strftime("%d/%m/%Y"), font1, (255, 255, 255), 1910, 750)
        
        draw_text(screen, "Distance:", font1, (255, 255, 255), 1510, 800)
        draw_text_right(screen, str(hovered_asteroid["distance"]), font1, (255, 255, 255), 1910, 800)
        
        draw_text(screen, "Speed:", font1, (255, 255, 255), 1510, 850)
        draw_text_right(screen, str(hovered_asteroid["speed"]), font1, (255, 255, 255), 1910, 850)
        
        draw_text(screen, "Magnitude:", font1, (255, 255, 255), 1510, 900)
        draw_text_right(screen, str(hovered_asteroid["magnitude"]), font1, (255, 255, 255), 1910, 900)
        
        draw_text(screen, "Hazardous:", font1, (255, 255, 255), 1510, 950)
        
        if hovered_asteroid["hazardous"] == 0:
            draw_text_right(screen, "No", font1, (255, 255, 255), 1910, 950)
        else:
            draw_text_right(screen, "Yes", font1, (255, 255, 255), 1910, 950)
    else:
        draw_text_centered(screen, "Hover over an asteroid", font1, (100, 100, 100), 1710, 760)
        draw_text_centered(screen, "to see more information", font1, (100, 100, 100), 1710, 790)
        draw_text_centered(screen, "about it", font1, (100, 100, 100), 1710, 820)
     
                
    today_stats = get_stats(asteroids, False)
    all_time_stats = get_stats(asteroids, True)
            
    draw_text_centered(screen, "Today's Stats:", font2, (255, 255, 255), 1710, 20)
    
    draw_text(screen, "Total:", font2, (255, 255, 255), 1510, 55)   
    draw_text_right(screen, str(today_stats["total"]), font2, (255, 255, 255), 1910, 55)
    
    draw_text(screen, "Biggest:", font2, (255, 255, 255), 1510, 90)
    draw_text_right(screen, f'{today_stats["biggest"]["name"]} ({str(today_stats["biggest"]["size"])}m)', font2, (255, 255, 255), 1910, 90)
    
    draw_text(screen, "Fastest:", font2, (255, 255, 255), 1510, 125)
    draw_text_right(screen, f'{today_stats["fastest"]["name"]} ({str(today_stats["fastest"]["speed"])}km/ph)', font2, (255, 255, 255), 1910, 125)
    
    draw_text(screen, "Brightest:", font2, (255, 255, 255), 1510, 160)
    draw_text_right(screen, f'{today_stats["brightest"]["name"]} ({today_stats["brightest"]["magnitude"]})', font2, (255, 255, 255), 1910, 160)
    
    draw_text(screen, "Closest:", font2, (255, 255, 255), 1510, 195)
    draw_text_right(screen, f'{today_stats["closest"]["name"]} ({round(today_stats["closest"]["distance"])}km)', font2, (255, 255, 255), 1910, 195)
    
    draw_text(screen, "Hazardous Percentage:", font2, (255, 255, 255), 1510, 230)
    hazardous_percentage = round((today_stats["hazardous"] / today_stats["total"]) * 100)
    draw_text_right(screen, f'{hazardous_percentage}%', font2, (255, 255, 255), 1910, 230)
    
    pygame.draw.line(screen, (100, 100, 100), (1500, 280), (1920, 280), 1)
    
    draw_text_centered(screen, "All Time Stats:", font2, (255, 255, 255), 1710, 310)
    
    draw_text(screen, "Total:", font2, (255, 255, 255), 1510, 345)
    draw_text_right(screen, str(len(asteroids)), font2, (255, 255, 255), 1910, 345)
    
    draw_text(screen, "Biggest:", font2, (255, 255, 255), 1510, 380)
    draw_text_right(screen, f'{all_time_stats["biggest"]["name"]} ({str(all_time_stats["biggest"]["size"])}m)', font2, (255, 255, 255), 1910, 380)
    
    draw_text(screen, "Fastest:", font2, (255, 255, 255), 1510, 415)
    draw_text_right(screen, f'{all_time_stats["fastest"]["name"]} ({str(all_time_stats["fastest"]["speed"])}km/ph)', font2, (255, 255, 255), 1910, 415)
    
    draw_text(screen, "Brightest:", font2, (255, 255, 255), 1510, 450)
    draw_text_right(screen, f'{all_time_stats["brightest"]["name"]} ({all_time_stats["brightest"]["magnitude"]})', font2, (255, 255, 255), 1910, 450)
    
    draw_text(screen, "Closest:", font2, (255, 255, 255), 1510, 485)
    draw_text_right(screen, f'{all_time_stats["closest"]["name"]} ({round(all_time_stats["closest"]["distance"])}km)', font2, (255, 255, 255), 1910, 485)
    
    draw_text(screen, "Hazardous Percentage:", font2, (255, 255, 255), 1510, 520)
    hazardous_percentage = round((all_time_stats["hazardous"] / all_time_stats["total"]) * 100)
    draw_text_right(screen, f'{hazardous_percentage}%', font2, (255, 255, 255), 1910, 520)
    
    pygame.draw.line(screen, (100, 100, 100), (1500, 570), (1920, 570)) 
        
    pygame.display.flip()	

pygame.quit()
sys.exit()