# Space Pebble
Space Pebble is a program which passively collects data about Near Earth Objects which pass Earth such as asteroids (space pebbles) using Nasa's API. After an asteroid passes it is plotted on the map at the point where it was closest to Earth. The longer you leave it running the more space data it will collect!

# Raspberry Pi Version
![20250905_141851](https://github.com/user-attachments/assets/b4d980b7-f46a-452c-81e7-e1f6d6f8d10a)

The Raspberry Pi version uses a more compact GUI, due to its smaller size it only displays all time stats, current time and information about the asteroid that you hover over.

# Desktop Version
<img width="1920" height="1080" alt="asteroid" src="https://github.com/user-attachments/assets/8c3aa650-586d-404e-81ac-64a7cff11fd9" />

On the Desktop version the program will show you a schedule of all the asteroids that will pass Earth today and when they'll pass. Asteroids that still haven't passed can be seen on the map in their approximate position with their trajectoy and their closest approach point.

# Stats
On the Desktop version you can see statistics from today and all time such as the amount of asteroids passing, which asteroid will be the biggest, brightest, fastest or closest and how many of them are considered hazardous. Hovering over an asteroid with your cursor will also show you its statistics and its current distance from Earth and close approach point if it still hasn't passed Earth.

# Tech Stack
    Language: Python
    GUI: PyGame
    Database: SQL Lite

# Please Note!
This tracker uses NASA’s Near Earth Object data to display how close asteroids are passing by Earth. The distances are real, but not their exact location in 3D space. To show them on a 2D screen, their map positions are randomized while the distances from Earth and closest approach point remain accurate.