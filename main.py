import pygame
import sys
import datetime
import json
from functions import fetch_neo_update_db, update_passed, fetch_asteroids, km_to_px, utc_to_local, time_until
from gui import draw_text, draw_text_centered
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
    
    pygame.draw.circle(screen, (0, 255, 0), (width / 2, height / 2), 1) #Draw Earth
    
    #Draw moon   
    r = km_to_px(-340_000, 20_000_000, max_radius)
    x = center_x + r
    y = center_y  
    pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), 1)

    #Draw asteroids and their info   
    total_today = 0
    biggest_today = {}
    fastest_today = {}
    brightest_today = {}
    closest_today = {}
    hazardous_today = 0

    biggest_all_time = {}
    fastest_all_time = {}
    brightest_all_time = {}
    closest_all_time = {}
    hazardous_all_time = 0
    
    cursor_x, cursor_y = pygame.mouse.get_pos() 
    text_y = 185
    for asteroid in asteroids:
        
        r = km_to_px(int(asteroid["distance"]), 20_000_000, max_radius)
        
        angle_rad = math.radians(asteroid["angle"])
        x = center_x + r * math.cos(angle_rad)
        y = center_y + r * math.sin(angle_rad)
        asteroid["x"] = x
        asteroid["y"] = y            
            
        pygame.draw.line(screen, (100, 100, 100), (0, 150), (420, 150), 1)
        
        if asteroid["passed"] == 0:
            pygame.draw.circle(screen, (90, 90, 90), (int(x), int(y)), 1)
            
            draw_text(screen, asteroid["name"], font1, (255, 255, 255), 10, text_y)
            draw_text(screen, utc_to_local(str(asteroid["close_approach_utc"])[-5:]), font1, (255, 255, 255), 325, text_y)
            draw_text(screen, f'Closest approach in: {time_until(utc_to_local(str(asteroid["close_approach_utc"])[-5:]))}', font2, (175, 175, 175), 10, text_y + 35)
            text_y += 75
        else:
            pygame.draw.circle(screen, (225, 225, 225), (int(x), int(y)), 1)
            
        if cursor_x >= x - 5 and cursor_x <= x + 5 and cursor_y >= y - 5 and cursor_y <= y + 5:
            if asteroid["passed"] == 1:
                draw_text_centered(screen, asteroid["name"], font2, (225, 225, 225), x, y - 20)
            else:
                draw_text_centered(screen, asteroid["name"], font2, (90, 90, 90), x, y - 20)
                
        if "size" in biggest_all_time:
            if ((asteroid["min_diameter"] + asteroid["max_diameter"]) / 2) > biggest_all_time["size"]:
                biggest_all_time["name"] = asteroid["name"]
                biggest_all_time["size"] = (asteroid["min_diameter"] + asteroid["max_diameter"]) / 2
        else:
            biggest_all_time["name"] = asteroid["name"]
            biggest_all_time["size"] = (asteroid["min_diameter"] + asteroid["max_diameter"]) / 2
            
        if "speed" in fastest_all_time:
            if (asteroid["speed"] > fastest_all_time["speed"]):
                fastest_all_time["name"] = asteroid["name"]
                fastest_all_time["speed"] = asteroid["speed"]
        else:
            fastest_all_time["name"] = asteroid["name"]
            fastest_all_time["speed"] = asteroid["speed"]
                
        if "magnitude" in brightest_all_time:
            if asteroid["magnitude"] < brightest_all_time["magnitude"]:
                brightest_all_time["name"] = asteroid["name"]
                brightest_all_time["magnitude"] = asteroid["magnitude"]
        else:
            brightest_all_time["name"] = asteroid["name"]
            brightest_all_time["magnitude"] = asteroid["magnitude"]
            
        if "distance" in closest_all_time:
            if asteroid["distance"] < closest_all_time["distance"]:
                closest_all_time["name"] = asteroid["name"]
                closest_all_time["distance"] = asteroid["distance"]
        else:
            closest_all_time["name"] = asteroid["name"]
            closest_all_time["distance"] = asteroid["distance"]
            
        if asteroid["hazardous"] == 1:
            hazardous_all_time["hazardous"] += 1
        
        today = datetime.datetime.today()
        formatted_date = today.strftime("%Y-%b-%d")
        if formatted_date == str(asteroid["close_approach_utc"])[:11]: #If its an asteroid is from today
            total_today += 1
            
            if "size" in biggest_today:
                if ((asteroid["min_diameter"] + asteroid["max_diameter"]) / 2) > biggest_today["size"]:
                    biggest_today["name"] = asteroid["name"]
                    biggest_today["size"] = (asteroid["min_diameter"] + asteroid["max_diameter"]) / 2
            else:
                biggest_today["name"] = asteroid["name"]
                biggest_today["size"] = (asteroid["min_diameter"] + asteroid["max_diameter"]) / 2
                
            if "speed" in fastest_today:
                if (asteroid["speed"] > fastest_today["speed"]):
                    fastest_today["name"] = asteroid["name"]
                    fastest_today["speed"] = asteroid["speed"]
            else:
                fastest_today["name"] = asteroid["name"]
                fastest_today["speed"] = asteroid["speed"]
                    
            if "magnitude" in brightest_today:
                if asteroid["magnitude"] < brightest_today["magnitude"]:
                    brightest_today["name"] = asteroid["name"]
                    brightest_today["magnitude"] = asteroid["magnitude"]
            else:
                brightest_today["name"] = asteroid["name"]
                brightest_today["magnitude"] = asteroid["magnitude"]
                
            if "distance" in closest_today:
                if asteroid["distance"] < closest_today["distance"]:
                    closest_today["name"] = asteroid["name"]
                    closest_today["distance"] = asteroid["distance"]
            else:
                closest_today["name"] = asteroid["name"]
                closest_today["distance"] = asteroid["distance"]
                
            if asteroid["hazardous"] == 1:
                hazardous_today["hazardous"] += 1
            
            
                    
    draw_text_centered(screen, "Today's Stats:", font2, (255, 255, 255), 1710, 20)
    
    draw_text(screen, "Total:", font2, (255, 255, 255), 1510, 55)   
    draw_text(screen, str(total_today), font2, (255, 255, 255), 1900 - (len(str(total_today)) * 13), 55)
    
    draw_text(screen, "Biggest:", font2, (255, 255, 255), 1510, 90)
    draw_text(screen, f'{biggest_today["name"]} ({str(biggest_today["size"])}m)', font2, (255, 255, 255), 1900 - ((len(str(biggest_today["size"])) + 2 + len(biggest_today["name"])) * 13), 90)
    
    draw_text(screen, "Fastest:", font2, (255, 255, 255), 1510, 125)
    draw_text(screen, f'{fastest_today["name"]} ({str(fastest_today["speed"])}km/ph)', font2, (255, 255, 255), 1900 - ((len(str(fastest_today["speed"])) + len(fastest_today["name"])) + 6) * 13, 125)
    
    draw_text(screen, "Brightest:", font2, (255, 255, 255), 1510, 160)
    draw_text(screen, f'{brightest_today["name"]} ({brightest_today["magnitude"]})', font2, (255, 255, 255), 1900 - ((len(str(brightest_today["magnitude"]))) + (len(brightest_today["name"]))) * 13, 160)
    
    draw_text(screen, "Closest:", font2, (255, 255, 255), 1510, 195)
    draw_text(screen, f'{closest_today["name"]} ({round(closest_today["distance"])}km)', font2, (255, 255, 255), 1900 - ((len(str(round(closest_today["distance"])))) + (len(closest_today["name"])) + 3) * 13, 195)
    
    draw_text(screen, "Hazardous Percentage:", font2, (255, 255, 255), 1510, 230)
    hazardous_percentage = round((hazardous_today / total_today) * 100)
    draw_text(screen, f'{hazardous_percentage}%', font2, (255, 255, 255), 1900 - (len(str(hazardous_percentage)) + 1) * 13, 230)
    
    pygame.draw.line(screen, (100, 100, 100), (1500, 280), (1920, 280), 1)
    
    draw_text_centered(screen, "All Time Stats:", font2, (255, 255, 255), 1710, 310)
    
    draw_text(screen, "Total:", font2, (255, 255, 255), 1510, 345)
    draw_text(screen, str(len(asteroids)), font2, (255, 255, 255), 1900 - (len(str(len(asteroids))) * 13), 345)
    
    draw_text(screen, "Biggest:", font2, (255, 255, 255), 1510, 380)
    draw_text(screen, f'{biggest_all_time["name"]} ({str(biggest_all_time["size"])}m)', font2, (255, 255, 255), 1900 - ((len(str(biggest_all_time["size"])) + 2 + len(biggest_all_time["name"])) * 13), 380)
    
    draw_text(screen, "Fastest:", font2, (255, 255, 255), 1510, 415)
    draw_text(screen, f'{fastest_all_time["name"]} ({str(fastest_all_time["speed"])}km/ph)', font2, (255, 255, 255), 1900 - ((len(str(fastest_all_time["speed"])) + len(fastest_all_time["name"])) + 6) * 13, 415)
    
    draw_text(screen, "Brightest:", font2, (255, 255, 255), 1510, 450)
    draw_text(screen, f'{brightest_all_time["name"]} ({brightest_all_time["magnitude"]})', font2, (255, 255, 255), 1900 - ((len(str(brightest_all_time["magnitude"]))) + (len(brightest_all_time["name"]))) * 13, 450)
    
    draw_text(screen, "Closest:", font2, (255, 255, 255), 1510, 485)
    draw_text(screen, f'{closest_all_time["name"]} ({round(closest_all_time["distance"])}km)', font2, (255, 255, 255), 1900 - ((len(str(round(closest_all_time["distance"])))) + (len(closest_all_time["name"])) + 3) * 13, 485)
    
    draw_text(screen, "Hazardous Percentage:", font2, (255, 255, 255), 1510, 520)
    hazardous_percentage = round((hazardous_all_time / len(asteroids)) * 100)
    draw_text(screen, f'{hazardous_percentage}%', font2, (255, 255, 255), 1900 - (len(str(hazardous_percentage)) + 1) * 13, 520)

    #Draw square 
    pygame.draw.rect(screen, (100, 100, 100), (420, 0, square_size, square_size), 1)
    
      ##############################
     ### PLANETS AND ASTEROIDS ####
    ##############################
    
    #Today total
    #biggest
    #Today's fastest
    #Today's brightest
    #Today's closest
    #Hazardouse percentage
    
    #Total asteroids
    #all time biggest
    #all time fastest
    #all time brightest
    #all time closest
    #Hazardous percentage
    
    #-------------------
    
    #Name
    #When it flew by
    #size
    #speed
    #magnitude + visualisation
    #hazardous
        
    pygame.display.flip()	

pygame.quit()
sys.exit()
