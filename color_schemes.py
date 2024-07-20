# Базовые цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
MAGENTA = (255, 0, 255)
CYAN = (0, 255, 255)
BROWN = (165, 42, 42)

# Цветовые схемы
light_scheme = {
    "KEY": WHITE,
    "SPECIAL_KEY": (230, 230, 230),
    "TEXT": {
        "main": (0, 0, 0),
        "keyword": (0, 0, 200),
        "symbol": (200, 0, 0),
        "function": (0, 150, 0),
    },
    "BACKGROUND": (240, 240, 240),
    "HIGHLIGHT": (255, 255, 0),
}

dark_scheme = {
    "KEY": BLACK,
    "SPECIAL_KEY": (50, 50, 50),
    "TEXT": {
        "main": (200, 200, 200),
        "keyword": (100, 100, 255),
        "symbol": (255, 100, 100),
        "function": (100, 255, 100),
    },
    "BACKGROUND": (30, 30, 30),
    "HIGHLIGHT": (255, 255, 0),
}

rainbow_scheme = {
    "KEY": {
        "BLACK": BLACK,
        "RED": RED,
        "GREEN": GREEN,
        "BLUE": BLUE,
        "YELLOW": YELLOW,
        "MAGENTA": MAGENTA,
        "CYAN": CYAN,
        "WHITE": WHITE,
        "BROWN": BROWN,
    },
    "SPECIAL_KEY": {
        "RED": (180, 0, 0),
        "BLUE": (0, 0, 180),
        "YELLOW": (180, 180, 0),
    },
    "TEXT": {
        "main": (255, 255, 255),
        "keyword": (255, 255, 0),
        "symbol": (255, 0, 255),
        "function": (0, 255, 255),
    },
    "BACKGROUND": (0, 0, 0),
    "HIGHLIGHT": (255, 255, 255),
}

schemes = {
    "light": light_scheme,
    "dark": dark_scheme,
    "rainbow": rainbow_scheme
}