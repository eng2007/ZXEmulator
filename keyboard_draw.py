import pygame
import sys
from keyboard_config import keys
from color_schemes import schemes

pygame.init()

WIDTH, HEIGHT = 1000, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ZX Spectrum Keyboard")

current_scheme = "light"  # Можно изменить на "light" или "dark"

def get_color(color_name):
    color_scheme = schemes[current_scheme]
    if isinstance(color_scheme[color_name], dict):
        return color_scheme[color_name]
    return color_scheme[color_name]

def draw_key(x, y, width, height, color, texts, text_colors, highlight=False):
    if highlight:
        pygame.draw.rect(screen, get_color("HIGHLIGHT"), (x-2, y-2, width+4, height+4))
    pygame.draw.rect(screen, color, (x, y, width, height))
    pygame.draw.rect(screen, get_color("TEXT")["main"], (x, y, width, height), 2)

    fonts = [pygame.font.Font(None, size) for size in [24, 16, 14, 12]]

    for i, (text, color) in enumerate(zip(texts, text_colors)):
        if text:
            text_surf = fonts[min(i, len(fonts)-1)].render(text, True, color)
            text_rect = text_surf.get_rect(center=(x + width/2, y + (i+1)*height/(len(texts)+1)))
            screen.blit(text_surf, text_rect)

key_positions = {}

def draw_keyboard(highlighted_key=None):
    screen.fill(get_color("BACKGROUND"))

    key_width, key_height = 80, 80
    start_x, start_y = 20, 20
    x, y = start_x, start_y

    for i, key in enumerate(keys):
        if i == 39:  # SPACE key
            key_width = 240
        elif i in [29, 30]:  # ENTER and CAPS SHIFT
            key_width = 120
        else:
            key_width = 80

        if current_scheme == "rainbow":
            color = get_color("KEY")[key["color"]]
        else:
            color = get_color("KEY") if key["color"] != "SPECIAL_KEY" else get_color("SPECIAL_KEY")

        texts = key["texts"]
        text_colors = [get_color("TEXT")["main"]]
        text_colors.extend([get_color("TEXT")["keyword"] for _ in range(len(texts) - 1)])

        highlight = (texts[0] == highlighted_key)
        draw_key(x, y, key_width, key_height, color, texts, text_colors, highlight)

        key_positions[texts[0]] = (x, y, key_width, key_height)

        x += key_width + 5
        if (i+1) % 10 == 0:
            x = start_x
            y += key_height + 5

    pygame.display.flip()

def highlight_key(key):
    draw_keyboard(key)

def change_color_scheme(scheme):
    global current_scheme
    if scheme in schemes:
        current_scheme = scheme
        draw_keyboard()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                highlight_key("SPACE")
            elif event.unicode.upper() in key_positions:
                highlight_key(event.unicode.upper())
            elif event.key == pygame.K_1:
                change_color_scheme("light")
            elif event.key == pygame.K_2:
                change_color_scheme("dark")
            elif event.key == pygame.K_3:
                change_color_scheme("rainbow")
        elif event.type == pygame.KEYUP:
            draw_keyboard()

    if not pygame.event.get():
        draw_keyboard()

pygame.quit()
sys.exit()