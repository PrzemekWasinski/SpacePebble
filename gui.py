def draw_text(window, text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    window.blit(img, (x, y))
    
def draw_text_centered(window, text, font, rgb_val, x, y):
    img = font.render(text, True, rgb_val)
    rect = img.get_rect(center=(x, y))
    window.blit(img, rect)
    
def draw_text_right(window, text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    rect = img.get_rect(topright=(x, y))
    window.blit(img, rect)
    
colours = {
    "trajectory": (136, 136, 255, 0.4),
    "live_asteroid": (255, 204, 51, 0.9),
    "passed_asteroid": (155, 155, 155, 0.4),
    "hovered_asteroid": (255, 255, 255),
    "close_approach_point": (255, 51, 51, 1.0),
    "button": (34, 34, 34, 0.9),
    "today_button_hover": (255, 204, 51, 1.0),
    "all_time_button_hover": (136, 136, 255, 1.0),
    "border": (68, 68, 68, 0.8),
    "text": (255, 255, 255),
    "gray_text": (175, 175, 175),
    "time": (255, 0, 0),
    "earth": (80, 160, 220, 1.0),
    "moon": (180, 180, 180, 1.0)
}
