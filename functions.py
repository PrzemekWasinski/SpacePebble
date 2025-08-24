import requests
from datetime import datetime
import sqlite3
import os
from os.path import join, dirname
from dotenv import load_dotenv

def fetch_neo_update_db(conn, c, today):
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    API_KEY = os.environ.get("API_KEY")
    BASE_URL = "https://api.nasa.gov/neo/rest/v1/feed"
    
    
    params = {
        "start_date": today,
        "end_date": today,
        "api_key": API_KEY
    }
    
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status() 
    data = response.json()

    for i in range(len(data["near_earth_objects"][today])):
        neo = data["near_earth_objects"][today][i]
        
        distance = round(float(neo["close_approach_data"][0]["miss_distance"]["kilometers"]))
        
        if distance < 50_000_000:
            name = neo["name"].strip("()")
            date = neo["close_approach_data"][0]["close_approach_date_full"]
            magnitude = float(neo["absolute_magnitude_h"])
            min_diameter = round(float(neo["estimated_diameter"]["meters"]["estimated_diameter_min"]), 2)
            max_diameter = round(float(neo["estimated_diameter"]["meters"]["estimated_diameter_max"]), 2)

            hazardous = 1 if neo["is_potentially_hazardous_asteroid"] else 0
            speed = round(float(neo["close_approach_data"][0]["relative_velocity"]["kilometers_per_hour"]))
        
            c.execute('''
                INSERT OR IGNORE INTO asteroids (
                    name, close_approach_utc, magnitude, min_diameter, max_diameter,
                    hazardous, speed, distance, passed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, date, magnitude, min_diameter, max_diameter, hazardous, speed, distance, 0))

    conn.commit()

def update_passed(conn, c, asteroids, notify):
    
    now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    c.execute('''
    UPDATE asteroids
    SET passed = 1
    WHERE passed = 0 AND close_approach_utc <= ?
    ''', (now_utc,))
    conn.commit()
    
    
    now_utc = datetime.utcnow()  # or parse your string if you already have it

    for a in asteroids:
        # Convert the asteroid's time string to a datetime object
        close_time = datetime.strptime(a['close_approach_utc'], "%Y-%b-%d %H:%M")
        
        if a['passed'] == 0 and close_time <= now_utc:
            a['passed'] = 1
            
            if (notify):
                print(f"{a['name']} has just passed!")
                print(f"Predicted pass time: {a['close_approach_utc']} | Now: {now_utc.strftime('%Y-%m-%d %H:%M')}")
            

def fetch_asteroids(c):
    c.execute('SELECT * FROM asteroids ORDER BY close_approach_utc')
    columns = [col[0] for col in c.description]
    rows = c.fetchall()
    return [dict(zip(columns, row)) for row in rows]

