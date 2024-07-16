import const
import struct

class Memory:
    def __init__(self, total_size=128 * 1024):
        self.total_size = total_size
        self.rom = [bytearray(16 * 1024) for _ in range(2)]  # 2 ROM банка по 16KB
        self.reset()

    def reset(self):
        self.memory = [bytearray(16 * 1024) for _ in range(8)]  # 8 банков по 16KB
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


    def load_snapshot(self, file_path, cpu):
        with open(file_path, 'rb') as file:
            # Чтение начального заголовка
            header = file.read(30)
            (
                a, f, bc, hl, pc, sp, i, r, flags, de, bc_, de_, hl_, af_, iy, ix, 
                iff1, iff2, im
            ) = struct.unpack('<B B H H H H B B B H H H H H H H B B B', header)

            # Установка регистров CPU
            cpu.set_register_pair('AF', (a << 8) | f)
            cpu.set_register_pair('BC', bc)
            cpu.set_register_pair('HL', hl)
            cpu.set_register_pair('PC', pc)
            cpu.set_register_pair('SP', sp)
            cpu.registers['I'] = i
            cpu.registers['R'] = r
            cpu.iff1 = iff1
            cpu.iff2 = iff2
            cpu.interrupt_mode = im
            cpu.set_register_pair('DE', de)
            cpu.set_register_pair('BC_', bc_)
            cpu.set_register_pair('DE_', de_)
            cpu.set_register_pair('HL_', hl_)
            cpu.set_register_pair('AF_', af_)
            cpu.set_register_pair('IY', iy)
            cpu.set_register_pair('IX', ix)

            # Проверка на расширение 2.01 или 3.0
            if pc == 0:
                len_ext, newpc = struct.unpack('<H H', file.read(4))
                extension = file.read(len_ext)

                model, p7FFD, r1, r2, p7FFD_1 = struct.unpack('<B B B B B', extension[:5])
                AY = list(struct.unpack('<16B', extension[5:21]))

                if len_ext > 23:
                    LowT, HighT, ReservedFlag, MgtRom, MultifaceRom, RamRom0, RamRom1 = struct.unpack('<H B B B B B B', extension[21:29])
                    KbMap1 = list(struct.unpack('<10B', extension[30:40]))
                    KbMap2 = list(struct.unpack('<10B', extension[40:50]))
                    MgtType, Disciple1, Disciple2, p1FFD = struct.unpack('<B B B B', extension[50:54])

                # Установка расширенных регистров и флагов
                cpu.set_register_pair('PC', newpc)

            # Вывод информации о регистрах
            print("Registers after loading snapshot:")
            for reg, val in cpu.registers.items():
                print(f"{reg}: {val:04X}")
            print(f"IFF1: {cpu.iff1}, IFF2: {cpu.iff2}, IM: {cpu.interrupt_mode}")

            # Чтение и установка памяти
            while True:
                block_header = file.read(3)
                if len(block_header) < 3:
                    break

                page, block_size = struct.unpack('<B H', block_header)
                block_data = file.read(block_size)

                # Загрузка блока в соответствующую страницу памяти
                if page <= 7:
                    self.memory[page * 0x4000:(page + 1) * 0x4000] = block_data
                else:
                    # Handle extended pages for 128K and higher models
                    self.memory[(page - 8) * 0x4000:(page - 7) * 0x4000] = block_data

                # Вывод информации о блоках
                print(f"Loaded block: Page={page}, Size={block_size}")

        print("Snapshot loaded successfully.")