# emulator.py
import logging
import pygame
from memory import Memory
# from cpu import Z80
from new_cpu import Z80
from interrupt_controller import InterruptController
from io_controller import IOController
from graphics import ZX_Spectrum_Graphics
from keyboard import Keyboard
import os
import const

def draw_text(surface, text, pos, font, color):
    rendered_text = font.render(text, True, color)
    surface.blit(rendered_text, pos)

def draw_rainbow_stripe(surface, height):
    colors = [
        (0, 0, 255),    # Blue
        (0, 255, 255),  # Cyan
        (0, 255, 0),    # Green
        (255, 255, 0),  # Yellow
        (255, 0, 0),    # Red
        (255, 0, 255),  # Magenta
    ]
    stripe_height = height // len(colors)
    for i, color in enumerate(colors):
        pygame.draw.rect(surface, color, (0, i * stripe_height, surface.get_width(), stripe_height))

def get_rom_files(directory):
    rom_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.rom', '.bin')):
                full_path = os.path.join(root, file)
                rom_files.append((file, full_path))
    return rom_files

def zx_spectrum_menu():
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("ZX Spectrum ROM Selector")

    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)

    font = pygame.font.Font(None, 32)
    
    files = get_rom_files('.')
    
    selected = 0
    scroll_offset = 0
    max_visible = 11
    rainbow_height = 30
    
    running = True
    while running:
        screen.fill(BLACK)
        
        # Draw rainbow stripe
        draw_rainbow_stripe(screen, rainbow_height)
        
        draw_text(screen, "ZX Spectrum ROM Selector", (20, rainbow_height + 10), font, CYAN)
        draw_text(screen, "Use UP/DOWN to select, ENTER to load", (20, rainbow_height + 50), font, WHITE)
        
        for i in range(max_visible):
            index = scroll_offset + i
            if index < len(files):
                color = MAGENTA if index == selected else WHITE
                draw_text(screen, files[index][0], (40, rainbow_height + 90 + i * 30), font, color)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(files)
                    if selected < scroll_offset:
                        scroll_offset = selected
                    elif selected >= scroll_offset + max_visible:
                        scroll_offset = max(0, selected - max_visible + 1)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(files)
                    if selected >= scroll_offset + max_visible:
                        scroll_offset = selected - max_visible + 1
                    elif selected < scroll_offset:
                        scroll_offset = selected
                elif event.key == pygame.K_RETURN:
                    pygame.quit()
                    return files[selected]
    
    pygame.quit()
    return None


class ZX_Spectrum_Emulator:
    def __init__(self):
        self.pixel_size = 3  # Увеличение пикселей для визуализации
        self.border_size = 80
        self.memory = Memory()
        self.io_controller = IOController(self)
        self.cpu = Z80(self.memory, self.io_controller, 0x0000)
        self.interrupt_controller = InterruptController(self.cpu)
        self.graphics = ZX_Spectrum_Graphics(self.memory, self.pixel_size)
        self.keyboard = Keyboard(self.io_controller)

    def load_rom(self, file_path, addr=0):
        self.memory.load_rom(file_path, addr)

    def load_rom128(self, file_path, addr=0):
        self.memory.load_rom128(file_path)
        #self.memory.load_rom(file_path, addr)        

    def load_scr_file(self, file_path):
        self.graphics.load_scr_file(file_path)

    def set_border(self, color):
        # Визуализация установки цвета границы
        #print(f"Цвет границы установлен на {color}")
        pass

    def emulate(self):


        pygame.init()

        # Удаление файла, если он существует
        #log_filename = 'example.log'
        #if os.path.exists(log_filename):
        #    os.remove(log_filename)
        # Настройка конфигурации логгера root
        #logging.basicConfig(
        #    filename=log_filename,
        #    level=logging.INFO,
            #format='%(asctime)s - %(levelname)s - %(message)s'
        #    format='%(message)s'
        #)
        #logging.disable()
        #log_on = False

        # Основное окно
        left_panel_width = 460
        main_screen = pygame.display.set_mode((self.graphics.screen_width * self.pixel_size + left_panel_width + self.border_size * 2, self.graphics.screen_height * self.pixel_size + self.border_size * 2))
        pygame.display.set_caption("ZX Spectrum Emulator")

        # Создание поверхностей
        screen = pygame.Surface((self.graphics.screen_width * self.pixel_size, self.graphics.screen_height * self.pixel_size))
        border = pygame.Surface((self.graphics.screen_width * self.pixel_size + self.border_size * 2, self.graphics.screen_height * self.pixel_size + self.border_size * 2))
        self.graphics.set_screen(screen)
        state_window = pygame.Surface((left_panel_width, self.graphics.screen_height * self.pixel_size + self.border_size * 2))

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
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1:
                        return "OPEN_MENU"  # Сигнал для открытия меню                    

            self.keyboard.read_keyboard()
            # Для демонстрации клавиатурного ввода:
            #print(self.keyboard.get_matrix())

            #for j in range(10000):
            #    if not self.cpu.halted:
            #        self.cpu.execute_instruction()  # Заглушка для обработки инструкций
            #    # Условие для вызова прерываний, например, каждые 20 мс
            #    self.interrupt_controller.check_and_trigger_interrupt()

            if not self.cpu.halted:
                #prev_pc = self.cpu.pc
                prev_pc = self.cpu.registers['PC']
                self.cpu.execute_instruction()  # обработка инструкций

            # Условие для вызова прерываний, например, каждые 20 мс
            self.interrupt_controller.check_and_trigger_interrupt()


            # Рендеринг основного окна
            #screen.fill((0, 0, 0))
            i += 1
            if i > 10000:
                i = 0

            #if self.cpu.registers['PC'] == 0x0C0A: print('init')
            #a = self.cpu.registers['A']
            #if self.cpu.registers['PC'] == 0x0010: print(const.spectrum_characters[a])

            #if self.cpu.registers['PC'] == 0x09F4:
            #    logging.disable(logging.NOTSET)
            #    log_on = True
            #if prev_pc == 0x0052:
            #    logging.disable(logging.NOTSET)
            #    logging.info('========== Finish interrupt ==========')
            #    logging.disable()
            #    if log_on: logging.disable(logging.NOTSET)


            #if self.cpu.interrupts_enabled == False and i > 0 : continue
            if i > 0: continue

            self.graphics.render_screen_fast()

            # Рендеринг окна состояния
            state_window.fill((0, 0, 0))
            self.cpu.display_registers(state_window, font, 0)
            self.keyboard.display_keyboard(state_window, font, 200)
            self.memory.display_memory_dump(0x5CA6, 32, state_window, font, 400)
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


def main_loop():
    zx_emulator = ZX_Spectrum_Emulator()

    while True:
        selected_file = zx_spectrum_menu()

        if selected_file:
            zx_emulator.cpu.reset()

            file_name, file_path = selected_file
            file_size = os.path.getsize(file_path)
            
            print(f"Loading file: {file_name}")
            print(f"File size: {file_size} bytes")

            if file_size > 16 * 1024:  # Если файл больше 16 КБ
                print("Using load_rom128 method")
                zx_emulator.load_rom128(file_path)
            else:
                print("Using load_rom method")
                zx_emulator.load_rom(file_path)

            result = zx_emulator.emulate()
            if result != "OPEN_MENU":
                break  # Выход из цикла, если эмуляция завершилась не по F1
        else:
            print("No ROM file selected. Exiting.")
            break        

# Пример использования
if __name__ == "__main__":
    #zx_emulator = ZX_Spectrum_Emulator()

    # Загрузка ROM файла
    #zx_emulator.load_rom('48.rom')
    #zx_emulator.load_rom('spectr_bk001bios.bin') #48K с русской надписью
    #zx_emulator.load_rom('pentagon_128_test.rom')  #Тест, моргает бордюром, Unsupported IY instruction: 2C
    #zx_emulator.load_rom('pentagon_128.rom') #64 KB    
    #zx_emulator.load_rom('128k.rom')
    #zx_emulator.load_rom128("128k.rom")
    #zx_emulator.load_rom128("pentagon_128bios.bin")
    #zx_emulator.load_rom128("S128_ZX81+_ROM.bin")
    #zx_emulator.load_rom('mini.rom')
    #zx_emulator.load_rom('TEST48K.rom')
    #zx_emulator.load_rom('ZX Test Rom.rom')
    #zx_emulator.load_rom('zexdoc', 0x8000)
    #zx_emulator.load_rom('vrcpwins.rom')
    #zx_emulator.load_rom('zxsemenu.rom') #меню None memtest
    #zx_emulator.load_rom('G9R_ROM.bin')
    #zx_emulator.load_rom('G10R_ROM.bin')
    #zx_emulator.load_rom('DiagROMv.171') #Матрас 76543210 потом чёрный экран
    #zx_emulator.load_rom('Globe_ROM.bin')
    #zx_emulator.load_rom('DeathStar_ROM.bin')
    #zx_emulator.load_rom('testrom.bin') #Тест soak ula mem keyb
    # Запуск эмуляции
    #zx_emulator.emulate()

    main_loop()    
