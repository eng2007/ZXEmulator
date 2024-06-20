# memory.py

class Memory:
    def __init__(self, total_size=128 * 1024, rom_size=16 * 1024):
        self.total_size = total_size
        self.rom_size = rom_size
        self.memory = bytearray(total_size)

    def load_rom(self, file_path, addr = 0):
        with open(file_path, 'rb') as f:
            rom_data = f.read()
            #if len(rom_data) != self.rom_size:
            #    raise ValueError("Invalid ROM file size")
            self.memory[addr:addr + self.rom_size] = rom_data

    def read(self, address):
        return self.memory[address]

    def write(self, address, value):
        if address >= self.rom_size:
            self.memory[address] = value

    def get_memory_dump(self, start_address, length):
        return self.memory[start_address:start_address + length]

    def display_memory_dump(self, start_address, num_words, screen, font, offset):
        word_size = 2  # Каждое слово - 2 байта
        dump_size = num_words * word_size  # Количество байт для отображения

        # Получаем дамп памяти из памяти
        memory_dump = self.get_memory_dump(start_address, dump_size)

        # Создаем поверхность для отображения дампа памяти
        #width, height = 300, num_words * 20  # Ширина и высота поверхности
        #surface = pygame.Surface((width, height))
        #surface.fill((0, 0, 0))  # Заполняем черным цветом

        x, y = 10, offset
        for i in range(0, dump_size, word_size):
            word = (memory_dump[i + 1] << 8) | memory_dump[i]  # Считываем 2 байта как слово
            text = font.render(f"{start_address + i:04X}: {word:04X}", True, (255, 255, 255))
            screen.blit(text, (x, y))
            y += 20

        return 