# keyboard.py

import pygame
import numpy as np

class Keyboard:
    def __init__(self):
        self.keyboard_matrix = np.ones((8, 5), dtype=bool)
        self.keymap = {
            pygame.K_1: (0, 0), pygame.K_2: (0, 1), pygame.K_3: (0, 2), pygame.K_4: (0, 3), pygame.K_5: (0, 4),
            pygame.K_0: (1, 0), pygame.K_9: (1, 1), pygame.K_8: (1, 2), pygame.K_7: (1, 3), pygame.K_6: (1, 4),
            pygame.K_q: (2, 0), pygame.K_w: (2, 1), pygame.K_e: (2, 2), pygame.K_r: (2, 3), pygame.K_t: (2, 4),
            pygame.K_p: (3, 0), pygame.K_o: (3, 1), pygame.K_i: (3, 2), pygame.K_u: (3, 3), pygame.K_y: (3, 4),
            pygame.K_a: (4, 0), pygame.K_s: (4, 1), pygame.K_d: (4, 2), pygame.K_f: (4, 3), pygame.K_g: (4, 4),
            pygame.K_RETURN: (5, 0), pygame.K_l: (5, 1), pygame.K_k: (5, 2), pygame.K_j: (5, 3), pygame.K_h: (5, 4),
            pygame.K_LSHIFT: (6, 0), pygame.K_z: (6, 1), pygame.K_x: (6, 2), pygame.K_c: (6, 3), pygame.K_v: (6, 4),
            pygame.K_SPACE: (7, 0), pygame.K_RSHIFT: (7, 1), pygame.K_m: (7, 2), pygame.K_n: (7, 3), pygame.K_b: (7, 4),            
        }

    def read_keyboard(self):
        pressed_keys = pygame.key.get_pressed()
        for key, (row, col) in self.keymap.items():
            self.keyboard_matrix[row, col] = not pressed_keys[key]
        # Объединяем все строки клавиш в один байт для порта 0xFE
        # Получаем состояние каждой строки и объединяем в один байт
        result = 0xFF
        for row in range(8):
            row_state = 0x1F  # каждая строка имеет 5 битов
            for col in range(5):
                if not self.keyboard_matrix[row, col]:
                    row_state &= ~(1 << col)
            result &= row_state << (row * 5)
        print(result)
        return result

    def get_matrix(self):
        return self.keyboard_matrix

    def display_keyboard(self, screen, font, offset):
        x, y = 10, 10 + offset
        row_text = "KEYBOARD"
        text = font.render(row_text, True, (255, 255, 255))
        screen.blit(text, (x, y))        
        y += 20
        for row_index, row in enumerate(self.keyboard_matrix):
            row_text = f"Row {row_index}: " + " ".join("P" if not pressed else "." for pressed in row)
            text = font.render(row_text, True, (255, 255, 255))
            screen.blit(text, (x, y))
            y += 20