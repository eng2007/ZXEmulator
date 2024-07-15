import const

class Memory:
    def __init__(self, total_size=128 * 1024):
        self.total_size = total_size
        self.memory = [bytearray(16 * 1024) for _ in range(8)]  # 8 банков по 16KB
        self.rom = [bytearray(16 * 1024) for _ in range(2)]  # 2 ROM банка по 16KB
        self.current_rom = 0
        self.paged_banks = [0, 5, 2, 0]  # Начальная конфигурация банков

    def load_rom(self, file_path, rom_number):
        with open(file_path, 'rb') as f:
            rom_data = f.read(16 * 1024)
            self.rom[rom_number][:len(rom_data)] = rom_data

    def load_rom128(self, file_path):
        with open(file_path, 'rb') as f:
            # Читаем первые 16KB для ПЗУ 128K
            rom_128_data = f.read(16 * 1024)
            self.rom[0][:len(rom_128_data)] = rom_128_data

            # Читаем следующие 16KB для ПЗУ 48K
            rom_48_data = f.read(16 * 1024)
            self.rom[1][:len(rom_48_data)] = rom_48_data

        print(f"ROM 128K loaded: {len(rom_128_data)} bytes")
        print(f"ROM 48K loaded: {len(rom_48_data)} bytes")       

    def __getitem__(self, address):
        return self.read(address)

    def __setitem__(self, address, value):
        self.write(address, value)             

    def read(self, address):
        bank = self.get_bank(address)
        offset = address % 16384
        if address < 16384:
            return self.rom[self.current_rom][offset]
        return self.memory[bank][offset]

    def write(self, address, value):
        if address >= 16384:  # Запрещаем запись в ROM
            bank = self.get_bank(address)
            offset = address % 16384
            self.memory[bank][offset] = value

    def get_bank(self, address):
        if address < 16384:
            return self.paged_banks[0]
        elif address < 32768:
            return self.paged_banks[1]
        elif address < 49152:
            return self.paged_banks[2]
        else:
            return self.paged_banks[3]

    def get_memory_dump(self, start_address, length):
        result = bytearray()
        for i in range(length):
            result.append(self.read(start_address + i))
        return result

    def display_memory_dump(self, start_address, num_words, screen, font, offset):
        word_size = 2
        dump_size = num_words * word_size

        memory_dump = self.get_memory_dump(start_address, dump_size)

        x, y = 10, offset
        for i in range(0, dump_size, word_size):
            if x > 300:
                x = 10
                y += 20
            word = (memory_dump[i + 1] << 8) | memory_dump[i]
            text = font.render(f"{start_address + i:04X}: {word:04X} {const.spectrum_characters[memory_dump[i]]} {const.spectrum_characters[memory_dump[i+1]]}", True, (255, 255, 255))
            screen.blit(text, (x, y))
            x += 210