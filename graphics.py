import numpy as np
import pygame
import sys


class ZX_Spectrum_Graphics:
    def __init__(self, memory, pixel_size):
        self.screen_width = 256
        self.screen_height = 192
        self.pixel_size = pixel_size  # Увеличение пикселей для визуализации
        self.memory_size = 6912  # 6144 bytes for screen + 768 bytes for attributes
        #self.memory = np.zeros(self.memory_size, dtype=np.uint8)
        self.memory = memory
        self.scr_base_address = 16384  # 0x4000
        self.scr_addr = np.zeros(
            (self.screen_width, self.screen_height, 3), dtype=np.uint16)
        self.buffer = np.zeros((self.screen_width, self.screen_height, 3), dtype=np.uint8)

        self.colors = [
            (0, 0, 0),      # 0: Black
            (0, 0, 200),    # 1: Blue
            (200, 0, 0),    # 2: Red
            (200, 0, 200),  # 3: Magenta
            (0, 200, 0),    # 4: Green
            (0, 200, 200),  # 5: Cyan
            (200, 200, 0),  # 6: Yellow
            (200, 200, 200)  # 7: White
        ]
        self.bright_colors = [
            (0, 0, 0),      # 0: Black
            (0, 0, 255),    # 1: Bright Blue
            (255, 0, 0),    # 2: Bright Red
            (255, 0, 255),  # 3: Bright Magenta
            (0, 255, 0),    # 4: Bright Green
            (0, 255, 255),  # 5: Bright Cyan
            (255, 255, 0),  # 6: Bright Yellow
            (255, 255, 255)  # 7: Bright White
        ]
        #self.screen = pygame.display.set_mode((self.screen_width * self.pixel_size, self.screen_height * self.pixel_size))

        # Заполняем массив с заранее посчитанными адресами экрана
        self.fill_scr_addr()

        pygame.display.set_caption("ZX Spectrum Emulator")

    def set_screen(self, screen):
        self.screen = screen

    def fill_scr_addr(self):
        for y in range(self.screen_height):
            for x in range(self.screen_width):
                byte_index = x // 8
                address = self.scr_base_address + \
                    ((y & 0b11000000) << 5) | ((y & 0b00111000) << 2) | (
                        (y & 0b00000111) << 8) + byte_index
                attribute_address = self.scr_base_address + \
                    6144 + ((y // 8) * 32) + (byte_index)

                self.scr_addr[x, y][0] = address
                self.scr_addr[x, y][1] = attribute_address

    def set_pixel(self, x, y, color_index):
        assert 0 <= x < self.screen_width, "x coordinate out of bounds"
        assert 0 <= y < self.screen_height, "y coordinate out of bounds"
        assert 0 <= color_index < 8, "Invalid color index"

        byte_index, bit = divmod(x, 8)
        line_offset = ((y & 0b11000000)) | (
            (y & 0b00111000) >> 3) | ((y & 0b00000111) << 3)
        address = self.scr_base_address + (line_offset * 32) + byte_index

        #third = y // 64
        #row_in_third = (y % 64) // 8
        #y_in_row = y % 8
        #address = third * 2048 + row_in_third * 32 + y_in_row * 256 + byte_index

        if color_index:
            self.memory[address] |= (1 << (7 - bit))
        else:
            self.memory[address] &= ~(1 << (7 - bit))

    def set_attribute(self, x, y, ink, paper, bright=False):
        assert 0 <= x < self.screen_width, "x coordinate out of bounds"
        assert 0 <= y < self.screen_height, "y coordinate out of bounds"
        assert 0 <= ink < 8, "Invalid ink color index"
        assert 0 <= paper < 8, "Invalid paper color index"

        attribute_address = self.scr_base_address + \
            6144 + ((y // 8) * 32) + (x // 8)
        attribute = (bright << 6) | (paper << 3) | ink
        self.memory[attribute_address] = attribute

    def reset_screen(self, ink, paper, bright=False):
        assert 0 <= ink < 8, "Invalid ink color index"
        assert 0 <= paper < 8, "Invalid paper color index"

        attribute = (bright << 6) | (paper << 3) | ink
        for addr in range(768):
            attribute_address = self.scr_base_address + 6144 + addr
            self.memory.write(attribute_address, attribute)

    def get_pixel_color(self, x, y):
        # Координаты любой точки (x,y) экрана в этих
        # обозначениях имеют такое строение:

        # y - 11 111 111    x - 11111 111
        #     S  R  L            B   bit number

        # y = 0..191        x = 0..255

        # где: S - секция или треть (0..2);
        # R - позиция по вертикали в пределах секции (0..7);
        # L - номер линии символа (0..7)
        # B - номер столбца (0..31).

        # adr(x,y) = 16384+2048*INT(L/8)+32*(L-8*INT(L/8))+256*R+C

        byte_index, bit = divmod(x, 8)

        #third = y // 64
        #row_in_third = (y % 64) // 8
        #y_in_row = y % 8
        #address = third * 2048 + row_in_third * 32 + y_in_row * 256 + byte_index

        address = self.scr_base_address + \
            ((y & 0b11000000) << 5) | ((y & 0b00111000) << 2) | (
                (y & 0b00000111) << 8) + byte_index

        pixel_value = (self.memory[address] >> (7 - bit)) & 1
        attribute_address = self.scr_base_address + \
            6144 + ((y // 8) * 32) + (x // 8)
        #attribute_address = 6144 + ((y & 0b11111000) << 2) + byte_index

        attribute = self.memory[attribute_address]
        bright = (attribute & 0x40) >> 6
        ink = attribute & 0x07
        paper = (attribute & 0x38) >> 3

        if pixel_value:
            return self.bright_colors[ink] if bright else self.colors[ink]
        else:
            return self.bright_colors[paper] if bright else self.colors[paper]

    def get_pixel_color(self, x, y):

        byte_index, bit = divmod(x, 8)
        address = self.scr_base_address + \
            ((y & 0b11000000) << 5) | ((y & 0b00111000) << 2) | (
                (y & 0b00000111) << 8) + byte_index

        pixel_value = (self.memory.read(address) >> (7 - bit)) & 1
        attribute_address = self.scr_base_address + \
            6144 + ((y // 8) * 32) + (x // 8)

        attribute = self.memory.read(attribute_address)
        bright = (attribute & 0x40) >> 6
        ink = attribute & 0x07
        paper = (attribute & 0x38) >> 3

        if pixel_value:
            return self.bright_colors[ink] if bright else self.colors[ink]
        else:
            return self.bright_colors[paper] if bright else self.colors[paper]

    # Функция для генерации нового экрана (эмуляция ZX Spectrum)
    def generate_new_screen(self):
        # Здесь генерируется новый экран как двумерный массив
        import random
        return [[random.choice((0, 1)) for _ in range(self.screen_width)] for _ in range(self.screen_height)]

    def render_screen_fast2(self):

        buffer = np.zeros(
            (self.screen_width, self.screen_height, 3), dtype=np.uint8)
        for y in range(self.screen_height):
            address_y = self.scr_base_address + \
                ((y & 0b11000000) << 5) | (
                    (y & 0b00111000) << 2) | ((y & 0b00000111) << 8)
            attr_address_y = self.scr_base_address + 6144 + ((y // 8) * 32)

            for x in range(0, self.screen_width, 8):
                byte_index = x // 8
                address = address_y + byte_index
                attribute_address = attr_address_y + byte_index
                attribute = self.memory[attribute_address]

                bright = (attribute & 0x40) >> 6
                ink = attribute & 0x07
                paper = (attribute & 0x38) >> 3

                for x_offs in range(8):
                    xs = x + x_offs
                    pixel_value = (self.memory[address] >> (7 - x_offs)) & 1

                    if pixel_value:
                        buffer[xs, y] = self.bright_colors[ink] if bright else self.colors[ink]
                    else:
                        buffer[xs, y] = self.bright_colors[paper] if bright else self.colors[paper]

        pygame.surfarray.blit_array(self.screen, np.kron(buffer, np.ones(
            (self.pixel_size, self.pixel_size, 1), dtype=np.uint8)))
        # Обновление окна
        pygame.display.flip()

    def render_screen_fast4(self):
        #buffer = np.zeros((self.screen_width, self.screen_height, 3), dtype=np.uint8)
        for y in range(0, self.screen_height,8):
            for x in range(0, self.screen_width, 8):
                attribute_address = self.scr_addr[x, y][1]
                attribute = self.memory.read(attribute_address)
                bright = (attribute & 0x40) >> 6
                ink    = (attribute & 0x07)
                paper  = (attribute & 0x38) >> 3

                color_ink = self.bright_colors[ink] if bright else self.colors[ink]
                color_paper = self.bright_colors[paper] if bright else self.colors[paper]

                for y_offs in range(8):
                    ys = y + y_offs
                    address = self.scr_addr[x, ys][0]
                    value = self.memory.read(address)

                    for bit in range(8):
                        xs = x + bit
                        pixel_value = (value >> (7 - bit)) & 1

                        if pixel_value:
                            self.buffer[xs, ys] = color_ink
                        else:
                            self.buffer[xs, ys] = color_paper

        pygame.surfarray.blit_array(self.screen, np.kron(self.buffer, np.ones((self.pixel_size, self.pixel_size, 1), dtype=np.uint8)))
        # Обновление окна
        pygame.display.flip()

    def render_screen_fast(self):
        buffer = np.zeros((self.screen_width, self.screen_height, 3), dtype=np.uint8)
        for y in range(self.screen_height):
            for x in range(0, self.screen_width, 8):
                attribute_address = self.scr_addr[x, y][1]
                attribute = self.memory.read(attribute_address)
                bright = (attribute & 0x40) >> 6
                ink    = (attribute & 0x07)
                paper  = (attribute & 0x38) >> 3

                address = self.scr_addr[x, y][0]
                for bit in range(8):
                    xs = x + bit
                    pixel_value = (self.memory.read(address) >> (7 - bit)) & 1

                    if pixel_value:
                        color = self.bright_colors[ink] if bright else self.colors[ink]
                    else:
                        color = self.bright_colors[paper] if bright else self.colors[paper]

                    #pygame.draw.rect(self.screen, color, (xs * self.pixel_size,
                    #                                      y * self.pixel_size, self.pixel_size, self.pixel_size))
                    buffer[xs, y] = color

        pygame.surfarray.blit_array(self.screen, np.kron(buffer, np.ones((self.pixel_size, self.pixel_size, 1), dtype=np.uint8)))
        # Обновление окна
        pygame.display.flip()

    def render_screen_fast3(self):
        buffer = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)

        # Предварительно вычислим часто используемые значения
        attr_addresses = self.scr_addr[:, :, 1].reshape(-1)
        pixel_addresses = self.scr_addr[:, :, 0].reshape(-1)

        # Считываем все атрибуты и пиксели за один раз
        # Считываем все атрибуты и пиксели по одному, но используем векторизацию numpy
        attributes = np.array([self.memory.read(addr) for addr in attr_addresses])
        pixels = np.array([self.memory.read(addr) for addr in pixel_addresses])

        # Векторизуем обработку атрибутов
        bright = (attributes & 0x40) >> 6
        ink = attributes & 0x07
        paper = (attributes & 0x38) >> 3

        # Создаем массивы цветов
        ink_colors = np.where(bright[:, np.newaxis], self.bright_colors[ink], self.colors[ink])
        paper_colors = np.where(bright[:, np.newaxis], self.bright_colors[paper], self.colors[paper])

        # Обрабатываем пиксели и заполняем буфер
        for i in range(8):
            mask = (pixels >> (7 - i)) & 1
            buffer[:, i::8] = np.where(mask[:, np.newaxis], ink_colors, paper_colors).reshape(self.screen_height, -1, 3)

        # Увеличиваем буфер до нужного размера
        scaled_buffer = np.kron(buffer, np.ones((self.pixel_size, self.pixel_size, 1), dtype=np.uint8))

        # Отображаем буфер на экран
        pygame.surfarray.blit_array(self.screen, scaled_buffer)

        # Обновляем окно
        pygame.display.flip()

    def render_screen(self):
        #screen = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
        # Отрисовка экрана

        # Генерация нового экрана
        #screen_data = self.generate_new_screen()

        buffer = np.zeros(
            (self.screen_width, self.screen_height, 3), dtype=np.uint8)
        for y in range(self.screen_height):
            for x in range(self.screen_width):
                buffer[x, y] = self.get_pixel_color(x, y)

        # Используем np.repeat для увеличения массива до нужного размера
        #enlarged_buffer = np.repeat(np.repeat(buffer, self.pixel_size, axis=0), self.pixel_size, axis=1)
        #pygame.surfarray.blit_array(self.screen, enlarged_buffer)

        #pygame.surfarray.blit_array(self.screen, np.kron(buffer, np.ones((self.pixel_size, self.pixel_size, 1), dtype=np.uint8)))

        # for y in range(self.screen_height):
        #    for x in range(self.screen_width):
        #        color = self.get_pixel_color(x, y)
        #        #color = (255, 255, 255) if screen_data[y][x] == 1 else (0, 0, 0)
        #        pygame.draw.rect(self.screen, color, (x * self.pixel_size, y * self.pixel_size, self.pixel_size, self.pixel_size))
        # Обновление окна
        pygame.display.flip()

    def load_screen(self, pixel_data, attribute_data):
        assert len(pixel_data) == 6144, "Invalid pixel data size"
        assert len(attribute_data) == 768, "Invalid attribute data size"
        self.memory[self.scr_base_address:self.scr_base_address +
                    6144] = pixel_data
        self.memory[self.scr_base_address + 6144:] = attribute_data

    def load_scr_file(self, file_path):
        with open(file_path, 'rb') as f:
            scr_data = f.read()
            assert len(scr_data) == 6912, "Invalid .scr file size"
            #self.memory = np.frombuffer(scr_data, dtype=np.uint8)
            for i, _ in enumerate(scr_data):
                #self.memory.memory[:i] = np.frombuffer(scr_data[:i], dtype=np.uint8)
                self.memory.memory[self.scr_base_address:
                                   self.scr_base_address + i] = scr_data[:i]

                if i % 512 != 0 and i < 6144:
                    continue
                if i % 32 != 0:
                    continue
                self.render_screen_fast()
            self.render_screen_fast()


# Инициализация Pygame
# pygame.init()
# Пример использования
#zx_graphics = ZX_Spectrum_Graphics()
#zx_graphics.reset_screen(0, 7, 1)

# Рисуем несколько пикселей
# zx_graphics.set_pixel(10, 1, 1)  # Синий пиксель
# zx_graphics.set_pixel(10, 65, 2)  # Красный пиксель
# zx_graphics.set_pixel(10, 129, 3)  # Магента пиксель

# for i in range(192):
#    zx_graphics.set_pixel(i, i, 1)  # Синий пиксель

# zx_graphics.render_screen()

# Устанавливаем атрибуты цвета
# zx_graphics.set_attribute(10, 10, ink=1, paper=0, bright=False)  # Синий на черном
# zx_graphics.set_attribute(20, 20, ink=2, paper=0, bright=True)   # Ярко-красный на черном
# zx_graphics.set_attribute(30, 30, ink=3, paper=0, bright=False)  # Магента на черном

# Рендерим экран
# zx_graphics.render_screen()


# Пример использования
# zx_graphics.load_scr_file("example.scr")

#running = True
# while running:
#    for event in pygame.event.get():
#        if event.type == pygame.QUIT:
#            running = False

# pygame.quit()
# sys.exit()
