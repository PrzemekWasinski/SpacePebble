import requests
import datetime
import os
from os.path import join, dirname
from dotenv import load_dotenv
import random
import pygame
import math
from gui import colours

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
        
        if distance < 20_000_000: #Ignore asteroids more than 20 million km away
            asteroid_id = neo["id"]
            name = neo["name"]
            close_date = neo["close_approach_data"][0]["close_approach_date_full"]
            magnitude = float(neo["absolute_magnitude_h"])
            min_diameter = round(float(neo["estimated_diameter"]["meters"]["estimated_diameter_min"]), 2)
            max_diameter = round(float(neo["estimated_diameter"]["meters"]["estimated_diameter_max"]), 2)
            angle = random.uniform(0, 360)

            hazardous = 1 if neo["is_potentially_hazardous_asteroid"] else 0
            
            speed = round(float(neo["close_approach_data"][0]["relative_velocity"]["kilometers_per_hour"]))
        
            c.execute('''
                INSERT OR IGNORE INTO asteroids (
                    id, name, close_approach_utc, magnitude, min_diameter, max_diameter,
                    hazardous, speed, distance, angle, passed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (asteroid_id, name, close_date, magnitude, min_diameter, max_diameter, hazardous, speed, distance, angle, 0))

    conn.commit()

def update_passed(conn, c, asteroids, notify):
    
    now_utc = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    c.execute('''
    UPDATE asteroids
    SET passed = 1
    WHERE passed = 0 AND close_approach_utc <= ?
    ''', (now_utc,))
    conn.commit()
    
    
    now_utc = datetime.datetime.utcnow()  

    for a in asteroids:
        close_time = datetime.datetime.strptime(a['close_approach_utc'], "%Y-%b-%d %H:%M")
        
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

def km_to_px(value, max_value, width):
    return (value / max_value) * width
    
def utc_to_local(utc_str):
    hours, minutes = map(int, utc_str.split(":"))
    
    today = datetime.date.today()   
    utc_dt = datetime.datetime(
        today.year, today.month, today.day,
        hours, minutes, tzinfo=datetime.timezone.utc
    )
    
    local_dt = utc_dt.astimezone()
    return local_dt.strftime("%H:%M")

def time_until(target_str):
    now = datetime.datetime.now()
    
    # Parse target time
    hours, minutes = map(int, target_str.split(":"))
    target = datetime.datetime(now.year, now.month, now.day, hours, minutes)
    
    # If target has already passed today, assume it's for tomorrow
    if target <= now:
        target += datetime.timedelta(days=1)
    
    delta = target - now
    total_seconds = int(delta.total_seconds())
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    return f"{hours}h {minutes}min {seconds}s"

def get_stats(asteroids, all_time):
    total = 0
    biggest = {}
    fastest = {}
    brightest = {}
    closest = {}
    hazardous = 0
    
    today = datetime.datetime.today()
    formatted_date = today.strftime("%Y-%b-%d")

    for asteroid in asteroids:
        if (formatted_date == str(asteroid["close_approach_utc"])[:11] and asteroid["passed"] == 1) or all_time:
            total += 1
            
            if "size" in biggest:
                if ((asteroid["min_diameter"] + asteroid["max_diameter"]) / 2) > biggest["size"]:
                    biggest["name"] = asteroid["name"]
                    biggest["size"] = (asteroid["min_diameter"] + asteroid["max_diameter"]) / 2
            else:
                biggest["name"] = asteroid["name"]
                biggest["size"] = (asteroid["min_diameter"] + asteroid["max_diameter"]) / 2
                    
            if "speed" in fastest:
                if (asteroid["speed"] > fastest["speed"]):
                    fastest["name"] = asteroid["name"]
                    fastest["speed"] = asteroid["speed"]
            else:
                fastest["name"] = asteroid["name"]
                fastest["speed"] = asteroid["speed"]
                    
            if "magnitude" in brightest:
                if asteroid["magnitude"] < brightest["magnitude"]:
                    brightest["name"] = asteroid["name"]
                    brightest["magnitude"] = asteroid["magnitude"]
            else:
                brightest["name"] = asteroid["name"]
                brightest["magnitude"] = asteroid["magnitude"]
                
            if "distance" in closest:
                if asteroid["distance"] < closest["distance"]:
                    closest["name"] = asteroid["name"]
                    closest["distance"] = asteroid["distance"]
            else:
                closest["name"] = asteroid["name"]
                closest["distance"] = asteroid["distance"]
                
            if asteroid["hazardous"] == 1:
                hazardous += 1

    if len(asteroids) == 0 or total == 0:
        stats = {
            "total": 0,
            "biggest": {"name": "N/A", "size": 0},
            "fastest": {"name": "N/A", "speed": 0},
            "brightest":{"name": "N/A", "magnitude": 0},
            "closest": {"name": "N/A", "distance": 0},
            "hazardous": 0
        }
        return stats
                
    stats = {
        "total": total,
        "biggest": biggest,
        "fastest": fastest,
        "brightest": brightest,
        "closest": closest,
        "hazardous": hazardous
    }
                
    return stats

def get_virtual_mouse(display_width, display_height):
    mx, my = pygame.mouse.get_pos()
    scale_x = 1920 / display_width
    scale_y = 1080 / display_height
    return int(mx * scale_x), int(my * scale_y)

def draw_trajectory(screen, display_width, display_height, asteroid, mover):
    DISPLAY_SIZE = 1080
    SPACE_SIZE_KM = 20_000_000  # km
    KM_PER_PIXEL = SPACE_SIZE_KM / DISPLAY_SIZE  # ≈ 18518.5 km per pixel

    x = asteroid["x"]
    y = asteroid["y"]
    speed_kmph = asteroid["speed"]
    close_approach_utc = asteroid["close_approach_utc"]
    
    cx, cy = display_width // 2, display_height // 2  # center of canvas

    # Vector from center to closest point
    dx = x - cx
    dy = y - cy

    if dx == 0 and dy == 0:
        return  # point is center, no preferred line

    # Direction perpendicular to center->closest point
    dir_x, dir_y = dy, -dx
    length = (dir_x**2 + dir_y**2)**0.5
    dir_x /= length
    dir_y /= length

    # Draw trajectory line
    square_size = 1080
    left   = (display_width - square_size) // 2
    top    = (display_height - square_size) // 2
    right  = left + square_size
    bottom = top + square_size

    # create a very long line along (dir_x, dir_y) through (x, y)
    scale = max(display_width, display_height) * 2
    start_pos = ((x - dir_x * scale) + mover, y - dir_y * scale)
    end_pos   = ((x + dir_x * scale) + mover, y + dir_y * scale)

    # clip against the square
    rect = pygame.Rect(left, top, square_size, square_size)
    clipped = rect.clipline(start_pos, end_pos)
    
    pygame.draw.line(screen, colours["trajectory"], clipped[0], clipped[1], 1)

    # === Calculate asteroid position ===
    close_approach = datetime.datetime.strptime(close_approach_utc, "%Y-%b-%d %H:%M")
    close_approach = close_approach.replace(tzinfo=datetime.timezone.utc)
    now = datetime.datetime.now(datetime.timezone.utc)

    # Time difference in hours
    delta_hours = (close_approach - now).total_seconds() / 3600

    # Distance in km along trajectory
    distance_km = speed_kmph * delta_hours

    # Convert km to pixels
    distance_px = distance_km / KM_PER_PIXEL

    # Current asteroid position
    asteroid_x = x - dir_x * distance_px
    asteroid_y = y - dir_y * distance_px
    
    asteroid["x"] = asteroid_x + mover
    asteroid["y"] = asteroid_y
    asteroid["ca_distance"] = distance_km
    
    pixel_distance = math.hypot(asteroid_x - cx, asteroid_y - cy)
    asteroid["earth_distance"] = pixel_distance * KM_PER_PIXEL

    # Draw asteroid
    pygame.draw.circle(screen, colours["live_asteroid"], (int(asteroid_x) + mover, int(asteroid_y)), 2)