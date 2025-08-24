import pygame
import sys
import datetime
import json
from functions import fetch_neo_update_db, update_passed, fetch_asteroids
import sqlite3
import time

DB_FILE = "asteroids.db"

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS asteroids (
    name TEXT PRIMARY KEY,
    close_approach_utc TEXT,
    magnitude REAL,
    min_diameter REAL,
    max_diameter REAL,
    hazardous INTEGER,
    speed REAL,
    distance REAL,
    passed INTEGER DEFAULT 0
)
''')
conn.commit()

pygame.init()
clock = pygame.time.Clock()

width, height = 1920, 1080
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Asteroid tracker")

date = datetime.date.today().strftime("%Y-%m-%d")
fetch_neo_update_db(conn, c, date)

asteroids = fetch_asteroids(c)
update_passed(conn, c, asteroids, False)

for i in range(0, len(asteroids)):
   print(asteroids[i])
   print("") 

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
            
    screen.fill((0, 0, 0))

    pygame.draw.circle(screen, (0, 255, 0), (width / 2, height / 2), 5)
    
    pygame.display.flip()	

pygame.quit()
sys.exit()
