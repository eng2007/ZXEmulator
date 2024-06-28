# emulator.py
import logging
import pygame
from memory import Memory
from cpu import Z80
from interrupt_controller import InterruptController
from io_controller import IOController
from graphics import ZX_Spectrum_Graphics
from keyboard import Keyboard
import os

spectrum_characters = {
    # Управляющие символы и псевдографика (грубо)
    0: 'NUL',    1: 'SOH',    2: 'STX',    3: 'ETX',    4: 'EOT',
    5: 'ENQ',    6: 'ACK',    7: 'BEL',    8: 'BS',     9: 'TAB',
    10: 'LF',    11: 'VT',    12: 'FF',    13: 'CR',    14: 'SO',
    15: 'SI',    16: 'DLE',   17: 'DC1',   18: 'DC2',   19: 'DC3',
    20: 'DC4',   21: 'NAK',   22: 'SYN',   23: 'ETB',   24: 'CAN',
    25: 'EM',    26: 'SUB',   27: 'ESC',   28: 'FS',    29: 'GS',
    30: 'RS',    31: 'US',    127: 'DEL',

    # Стандартные ASCII-символы
    32: ' ',     33: '!',     34: '"',     35: '#',     36: '$',
    37: '%',     38: '&',     39: "'",     40: '(',     41: ')',
    42: '*',     43: '+',     44: ',',     45: '-',     46: '.',
    47: '/',     48: '0',     49: '1',     50: '2',     51: '3',
    52: '4',     53: '5',     54: '6',     55: '7',     56: '8',
    57: '9',     58: ':',     59: ';',     60: '<',     61: '=',
    62: '>',     63: '?',     64: '@',     65: 'A',     66: 'B',
    67: 'C',     68: 'D',     69: 'E',     70: 'F',     71: 'G',
    72: 'H',     73: 'I',     74: 'J',     75: 'K',     76: 'L',
    77: 'M',     78: 'N',     79: 'O',     80: 'P',     81: 'Q',
    82: 'R',     83: 'S',     84: 'T',     85: 'U',     86: 'V',
    87: 'W',     88: 'X',     89: 'Y',     90: 'Z',     91: '[',
    92: '\\',    93: ']',     94: '^',     95: '_',     96: '`',
    97: 'a',     98: 'b',     99: 'c',    100: 'd',    101: 'e',
    102: 'f',    103: 'g',    104: 'h',    105: 'i',    106: 'j',
    107: 'k',    108: 'l',    109: 'm',    110: 'n',    111: 'o',
    112: 'p',    113: 'q',    114: 'r',    115: 's',    116: 't',
    117: 'u',    118: 'v',    119: 'w',    120: 'x',    121: 'y',
    122: 'z',    123: '{',    124: '|',    125: '}',    126: '~',

    # Псевдографические и расширенные символы ZX Spectrum
    128: 'GRAPHICS_0',  129: 'GRAPHICS_1',  130: 'GRAPHICS_2',  131: 'GRAPHICS_3',
    132: 'GRAPHICS_4',  133: 'GRAPHICS_5',  134: 'GRAPHICS_6',  135: 'GRAPHICS_7',
    136: 'GRAPHICS_8',  137: 'GRAPHICS_9',  138: 'GRAPHICS_10', 139: 'GRAPHICS_11',
    140: 'GRAPHICS_12', 141: 'GRAPHICS_13', 142: 'GRAPHICS_14', 143: 'GRAPHICS_15',
    144: 'GRAPHICS_16', 145: 'GRAPHICS_17', 146: 'GRAPHICS_18', 147: 'GRAPHICS_19',
    148: 'GRAPHICS_20', 149: 'GRAPHICS_21', 150: 'GRAPHICS_22', 151: 'GRAPHICS_23',
    152: 'GRAPHICS_24', 153: 'GRAPHICS_25', 154: 'GRAPHICS_26', 155: 'GRAPHICS_27',
    156: 'GRAPHICS_28', 157: 'GRAPHICS_29', 158: 'GRAPHICS_30', 159: 'GRAPHICS_31',
    160: 'GRAPHICS_32', 161: 'GRAPHICS_33', 162: 'GRAPHICS_34', 163: 'GRAPHICS_35',
    164: 'GRAPHICS_36', 165: 'GRAPHICS_37', 166: 'GRAPHICS_38', 167: 'GRAPHICS_39',
    168: 'GRAPHICS_40', 169: 'GRAPHICS_41', 170: 'GRAPHICS_42', 171: 'GRAPHICS_43',
    172: 'GRAPHICS_44', 173: 'GRAPHICS_45', 174: 'GRAPHICS_46', 175: 'GRAPHICS_47',
    176: 'GRAPHICS_48', 177: 'GRAPHICS_49', 178: 'GRAPHICS_50', 179: 'GRAPHICS_51',
    180: 'GRAPHICS_52', 181: 'GRAPHICS_53', 182: 'GRAPHICS_54', 183: 'GRAPHICS_55',
    184: 'GRAPHICS_56', 185: 'GRAPHICS_57', 186: 'GRAPHICS_58', 187: 'GRAPHICS_59',
    188: 'GRAPHICS_60', 189: 'GRAPHICS_61', 190: 'GRAPHICS_62', 191: 'GRAPHICS_63',
    192: 'GRAPHICS_64', 193: 'GRAPHICS_65', 194: 'GRAPHICS_66', 195: 'GRAPHICS_67',
    196: 'GRAPHICS_68', 197: 'GRAPHICS_69', 198: 'GRAPHICS_70', 199: 'GRAPHICS_71',
    200: 'GRAPHICS_72', 201: 'GRAPHICS_73', 202: 'GRAPHICS_74', 203: 'GRAPHICS_75',
    204: 'GRAPHICS_76', 205: 'GRAPHICS_77', 206: 'GRAPHICS_78', 207: 'GRAPHICS_79',
    208: 'GRAPHICS_80', 209: 'GRAPHICS_81', 210: 'GRAPHICS_82', 211: 'GRAPHICS_83',
    212: 'GRAPHICS_84', 213: 'GRAPHICS_85', 214: 'GRAPHICS_86', 215: 'GRAPHICS_87',
    216: 'GRAPHICS_88', 217: 'GRAPHICS_89', 218: 'GRAPHICS_90', 219: 'GRAPHICS_91',
    220: 'GRAPHICS_92', 221: 'GRAPHICS_93', 222: 'GRAPHICS_94', 223: 'GRAPHICS_95',
    224: 'GRAPHICS_96', 225: 'GRAPHICS_97', 226: 'GRAPHICS_98', 227: 'GRAPHICS_99',
    228: 'GRAPHICS_100', 229: 'GRAPHICS_101', 230: 'GRAPHICS_102', 231: 'GRAPHICS_103',
    232: 'GRAPHICS_104', 233: 'GRAPHICS_105', 234: 'GRAPHICS_106', 235: 'GRAPHICS_107',
    236: 'GRAPHICS_108', 237: 'GRAPHICS_109', 238: 'GRAPHICS_110', 239: 'GRAPHICS_111',
    240: 'GRAPHICS_112', 241: 'GRAPHICS_113', 242: 'GRAPHICS_114', 243: 'GRAPHICS_115',
    244: 'GRAPHICS_116', 245: 'GRAPHICS_117', 246: 'GRAPHICS_118', 247: 'GRAPHICS_119',
    248: 'GRAPHICS_120', 249: 'GRAPHICS_121', 250: 'GRAPHICS_122', 251: 'GRAPHICS_123',
    252: 'GRAPHICS_124', 253: 'GRAPHICS_125', 254: 'GRAPHICS_126', 255: 'GRAPHICS_127',
}


class ZX_Spectrum_Emulator:
    def __init__(self):
        self.pixel_size = 4  # Увеличение пикселей для визуализации
        self.border_size = 40
        self.memory = Memory()
        self.io_controller = IOController(self)
        self.cpu = Z80(self.memory, self.io_controller, 0x0000)
        self.interrupt_controller = InterruptController(self.cpu)
        self.graphics = ZX_Spectrum_Graphics(self.memory, self.pixel_size)
        self.keyboard = Keyboard()


    def load_rom(self, file_path, addr = 0):
        self.memory.load_rom(file_path, addr)

    def load_scr_file(self, file_path):
        self.graphics.load_scr_file(file_path)

    def set_border(self, color):
        # Визуализация установки цвета границы
        print(f"Цвет границы установлен на {color}")

    def emulate(self):
        pygame.init()

        # Удаление файла, если он существует
        log_filename = 'example.log'
        if os.path.exists(log_filename):
            os.remove(log_filename)
        # Настройка конфигурации логгера root
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            #format='%(asctime)s - %(levelname)s - %(message)s'
            format='%(message)s'
        )
        logging.disable()
        
        # Основное окно
        main_screen = pygame.display.set_mode((self.graphics.screen_width * self.pixel_size + 300 + self.border_size * 2, self.graphics.screen_height * self.pixel_size + self.border_size * 2))        
        pygame.display.set_caption("ZX Spectrum Emulator")

        # Создание поверхностей
        screen = pygame.Surface((self.graphics.screen_width * self.pixel_size, self.graphics.screen_height * self.pixel_size))
        border = pygame.Surface((self.graphics.screen_width * self.pixel_size + self.border_size * 2, self.graphics.screen_height * self.pixel_size + self.border_size * 2))
        self.graphics.set_screen(screen)
        state_window = pygame.Surface((300, self.graphics.screen_height * self.pixel_size + self.border_size * 2))

        # Отрисовка на основном экране
        pygame.draw.rect(border, self.graphics.colors[self.io_controller.border_color] , (0, 0, border.get_width(), border.get_height()))
        main_screen.blit(border, (0, 0))
        main_screen.blit(screen, (self.border_size, self.border_size))
        main_screen.blit(state_window, (self.graphics.screen_width * self.pixel_size + self.border_size * 2, 0))

        font = pygame.font.SysFont('Courier', 18)
        clock = pygame.time.Clock()

        # Загрузка .scr файла
        self.graphics.reset_screen(0, 7, 1)
        #self.load_scr_file('example.scr')        
        
        running = True
        i = 0
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.keyboard.read_keyboard()
            # Для демонстрации клавиатурного ввода:
            #print(self.keyboard.get_matrix())

            #for j in range(10000):
            #    if not self.cpu.halted:
            #        self.cpu.execute_instruction()  # Заглушка для обработки инструкций
            #    # Условие для вызова прерываний, например, каждые 20 мс
            #    self.interrupt_controller.check_and_trigger_interrupt()

            if not self.cpu.halted:
                self.cpu.execute_instruction()  # Заглушка для обработки инструкций
            # Условие для вызова прерываний, например, каждые 20 мс
            self.interrupt_controller.check_and_trigger_interrupt()


            # Рендеринг основного окна
            #screen.fill((0, 0, 0))
            i += 1
            if i > 1000:                
                i = 0     

            if self.cpu.pc == 0x0C0A: print('init')
            a = (self.cpu.af >> 8) & 0xFF
            if self.cpu.pc == 0x0010: print(spectrum_characters[a])


            if self.cpu.interrupts_enabled == False and i > 0 : continue
            if i > 0: continue

            self.graphics.render_screen_fast()

            # Рендеринг окна состояния
            state_window.fill((0, 0, 0))
            self.cpu.display_registers(state_window, font, 0)
            self.keyboard.display_keyboard(state_window, font, 200)
            self.memory.display_memory_dump(0x4000, 8, state_window, font, 400)
            #pygame.display.update(state_window.get_rect())

            #заливка бордера
            pygame.draw.rect(border, self.graphics.colors[self.io_controller.border_color] , (0, 0, border.get_width(), border.get_height()))

            # Отрисовка на основном экране
            main_screen.blit(border, (0, 0))
            main_screen.blit(screen, (self.border_size, self.border_size))
            main_screen.blit(state_window, (self.graphics.screen_width * self.pixel_size + self.border_size * 2, 0))            

            pygame.display.flip()
            #clock.tick(50)

        pygame.quit()

# Пример использования
if __name__ == "__main__":
    zx_emulator = ZX_Spectrum_Emulator()

    # Загрузка ROM файла
    #zx_emulator.load_rom('48.rom')
    #zx_emulator.load_rom('128k.rom')
    #zx_emulator.load_rom('mini.rom')
    #zx_emulator.load_rom('TEST48K.rom')
    #zx_emulator.load_rom('ZX Test Rom.rom')
    #zx_emulator.load_rom('zexdoc', 0x8000)
    #zx_emulator.load_rom('vrcpwins.rom')
    #zx_emulator.load_rom('zxsemenu.rom')
    zx_emulator.load_rom('G10R_ROM.bin')

    # Запуск эмуляции
    zx_emulator.emulate()

