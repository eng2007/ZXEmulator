import const
import struct

class Memory:
    def __init__(self, total_size=128 * 1024):
        self.total_size = total_size
        self.rom = [bytearray(16 * 1024) for _ in range(2)]  # 2 ROM банка по 16KB
        self.reset()
        self.temp_files = []

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
        offset = address % 16384
        if address < 16384:
            return self.rom[self.current_rom][offset]
        bank = self.get_bank(address)
        return self.memory[bank][offset]

    def write(self, address, value):
        if address >= 16384:  # Запрещаем запись в ROM
        #if address >= 0:  # Запрещаем запись в ROM
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

    def load_snapshot_sna(self, file_path, cpu):
        with open(file_path, 'rb') as file:
            # Чтение заголовка SNA (27 байт)
            header = file.read(27)

            # Распаковка заголовка
            (i, hl_, de_, bc_, af_, hl, de, bc, iy, ix,
             iff1, r, af, sp, im, border) = struct.unpack('<B H H H H H H H H H B B H H B B', header)

            # Установка регистров CPU
            cpu.registers['I'] = i
            cpu.set_register_pair('HL_', hl_)
            cpu.set_register_pair('DE_', de_)
            cpu.set_register_pair('BC_', bc_)
            cpu.set_register_pair('AF_', af_)
            cpu.set_register_pair('HL', hl)
            cpu.set_register_pair('DE', de)
            cpu.set_register_pair('BC', bc)
            cpu.set_register_pair('IY', iy)
            cpu.set_register_pair('IX', ix)
            cpu.iff1 = cpu.iff2 = bool(iff1 & 0x04)
            cpu.registers['R'] = r
            cpu.set_register_pair('AF', af)
            cpu.set_register_pair('SP', sp)
            cpu.interrupt_mode = im

            # Чтение 48KB памяти
            memory_data = file.read(48 * 1024)
            memory_data = bytearray(memory_data)

            # Загрузка памяти в соответствующие банки
            self.memory[5] = memory_data[:16384]  # Bank 5 (16384-32767)
            self.memory[2] = memory_data[16384:32768]  # Bank 2 (32768-49151)
            self.memory[0] = memory_data[32768:]  # Bank 0 (49152-65535)

            # Установка начальной конфигурации банков памяти
            self.paged_banks = [0, 5, 2, 0]
            self.current_rom = 0  # SNA всегда загружается в режиме 48K

            # Восстановление PC из стека
            pc_low = self.read(sp)
            pc_high = self.read(sp + 1)
            pc = (pc_high << 8) | pc_low
            cpu.set_register_pair('PC', pc)

            # Корректировка SP
            cpu.set_register_pair('SP', sp + 2)

            print("SNA snapshot loaded successfully.")
            print("Registers after loading snapshot:")
            for reg, val in cpu.registers.items():
                print(f"{reg}: {val:04X}")
            print(f"IFF1: {cpu.iff1}, IFF2: {cpu.iff2}, IM: {cpu.interrupt_mode}")


    def unpack_block(self, compressed_data):
        unpacked_data = bytearray()
        i = 0
        while i < len(compressed_data):
            if compressed_data[i] == 0xED:
                if i + 1 < len(compressed_data) and compressed_data[i + 1] == 0xED:
                    if i + 3 < len(compressed_data):
                        repeat_count = compressed_data[i + 2]
                        value = compressed_data[i + 3]
                        unpacked_data.extend([value] * repeat_count)
                        i += 4
                    else:
                        # End of block marker
                        break
                else:
                    # Single ED byte followed by any other byte
                    unpacked_data.append(0xED)
                    i += 1
                    if i < len(compressed_data):
                        unpacked_data.append(compressed_data[i])
                        i += 1
            else:
                unpacked_data.append(compressed_data[i])
                i += 1

        return unpacked_data

    def load_snapshot_z80_check48(self, file_path):
        with open(file_path, 'rb') as file:
            # Чтение начального заголовка
            header = file.read(30)
            (
                a, f, bc, hl, pc, sp, i, r, flags, de, bc_, de_, hl_, a_, f_, iy, ix,
                iff1, iff2, im
            ) = struct.unpack('<B B H H H H B B B H H H H B B H H B B B', header)
            # Определение версии формата
            version = 1
            if pc == 0:
                version = 2
                len_ext, newpc, hw_mode = struct.unpack('<H H B', file.read(5))
                #print(f'Additional block length {len_ext}')
                if len_ext == 54 or len_ext == 55:
                    version = 3
        load48k = True
        if version == 2:
            if hw_mode == 3 or hw_mode == 4:
                load48k = False
        if version == 3:
            if hw_mode == 4 or hw_mode == 5 or hw_mode == 6:
                load48k = False
        return load48k

    def load_snapshot_z80(self, file_path, cpu):
        hardware_v2 = ['48k','48k + If.1','SamRam','128k','128k + If.1']
        hardware_v3 = ['48k','48k + If.1','SamRam','48k + M.G.T.','128k','128k + If.1','128k + M.G.T.']
        load48k = True

        with open(file_path, 'rb') as file:
            # Чтение начального заголовка
            header = file.read(30)
            (
                a, f, bc, hl, pc, sp, i, r, flags, de, bc_, de_, hl_, a_, f_, iy, ix,
                iff1, iff2, im
            ) = struct.unpack('<B B H H H H B B B H H H H B B H H B B B', header)

            # Установка регистров CPU
            cpu.set_register_pair('AF', (a << 8) | f)
            cpu.set_register_pair('BC', bc)
            cpu.set_register_pair('HL', hl)
            cpu.set_register_pair('PC', pc)
            cpu.set_register_pair('SP', sp)
            cpu.registers['I'] = i
            cpu.registers['R'] = r
            cpu.iff1 = bool(iff1)
            cpu.iff2 = bool(iff2)
            cpu.interrupt_mode = im & 3
            cpu.interrupts_enabled = bool(iff1)
            cpu.set_register_pair('DE', de)
            cpu.set_register_pair('BC_', bc_)
            cpu.set_register_pair('DE_', de_)
            cpu.set_register_pair('HL_', hl_)
            #cpu.set_register_pair('AF_', af_)
            cpu.registers['A_'] = a_
            cpu.registers['F_'] = f_
            cpu.set_register_pair('IY', iy)
            cpu.set_register_pair('IX', ix)
            border_color = (flags >> 1) & 0x07

            # Определение версии формата
            version = 1
            if pc == 0:
                version = 2
                len_ext, newpc = struct.unpack('<H H', file.read(4))
                print(f'Additional block length {len_ext}')
                if len_ext == 54 or len_ext == 55:
                    version = 3

            if version >= 2:
                extension = struct.pack('<H H', len_ext, pc) + file.read(len_ext - 4 + 2)
                print(len(extension))
                print(extension)
                #extension = file.read(len_ext)
                hw_mode, out_7ffd, Interface1_rom_paged = struct.unpack('<B B B', extension[4:7])
                cpu.set_register_pair('PC', newpc)

                if version == 2:
                    config_bit, out_fffd = struct.unpack('<B B', extension[7:9])

                    ay_sound_registers = list(extension[9:25])

                    print("\nAdditional header information:")
                    print(f"Header Length: {len_ext}")
                    print(f"PC: {newpc:04X}")
                    print(f"Hardware Mode: {hw_mode:02X} - {hardware_v2[hw_mode]}")
                    print(f"OUT to 0x7FFD: {out_7ffd:02X}")
                    print(f"Interface1_rom_paged: {Interface1_rom_paged}")
                    print(f"OUT to 0xFFFD: {out_fffd:02X}")
                    print(f"AY Sound Registers: {ay_sound_registers}")


                if version == 3:
                    config_bit, out_fffd = struct.unpack('<B B', extension[7:9])

                    ay_sound_registers = list(extension[9:25])
                    
                    #joystick_settings = extension[41]
                    #mgt_rom_paged = bool(extension[42] & 1)
                    #multiface_rom_paged = bool(extension[42] & 2)
                    #rom_128_0 = bool(extension[42] & 4)
                    #rom_48 = bool(extension[42] & 8)
                    #modify_hardware = bool(extension[42] & 16)
              
                    joystick_mappings = list(extension[33:43])
                    joystick_keys = list(extension[43:53])
                    MGT_type = extension[53]
                    disciple_inhibitor_in = extension[54]
                    dicsicple_pageable = extension[55]

                    print("\nAdditional header information:")
                    print(f"Header Length: {len_ext}")
                    print(f"PC: {newpc:04X}")
                    print(f"Hardware Mode: {hw_mode:02X} - {hardware_v3[hw_mode]}")
                    print(f"OUT to 0x7FFD: {out_7ffd:02X}")
                    print(f"Interface1_rom_paged: {Interface1_rom_paged}")
                    print(f"OUT to 0xFFFD: {out_fffd:02X}")
                    print(f"AY Sound Registers: {ay_sound_registers}")

                    print(f"Joystick mappings: {joystick_mappings}")
                    print(f"Joystick keys: {joystick_keys}")
                    print(f"MGT type: {MGT_type}")
                    print(f"Disciple inhibitor in: {disciple_inhibitor_in}")
                    print(f"Dicsicple pageable: {dicsicple_pageable}")

                    #print(f"Joystick Settings: {joystick_settings}")
                    #print(f"MGT ROM Paged: {mgt_rom_paged}")
                    #print(f"Multiface ROM Paged: {multiface_rom_paged}")
                    #print(f"ROM 128 (0) Paged: {rom_128_0}")
                    #print(f"ROM 48 Paged: {rom_48}")
                    #print(f"Modify Hardware: {modify_hardware}")
                    #print(f"Last OUT to 0xFFFD: {last_out_fffd}")

            print(f"Z80 version: {version}")
            print(f"Border color {border_color}")
            print("Registers after loading snapshot:")
            for reg, val in cpu.registers.items():
                print(f"{reg}: {val:04X}")
            print(f"IFF1: {cpu.iff1}, IFF2: {cpu.iff2}, IM: {cpu.interrupt_mode}")

            # Чтение и установка памяти
            if version == 1:
                compressed = (flags & 0x20) != 0
                memory_data = file.read()
                if compressed:
                    memory_data = self.unpack_block(memory_data)
                else:
                    memory_data = bytearray(memory_data)

                # Ensure we have exactly 48KB of data
                #if len(memory_data) > 48 * 1024:
                #    memory_data = memory_data[:48 * 1024]
                #elif len(memory_data) < 48 * 1024:
                #    memory_data.extend([0] * (48 * 1024 - len(memory_data)))
                self.memory[5] = memory_data[:16384]  # Bank 5 (16384-32767)
                self.memory[2] = memory_data[16384:32768]  # Bank 2 (32768-49151)
                self.memory[0] = memory_data[32768:]  # Bank 0 (49152-65535)
            else:
                while True:
                    block_header = file.read(3)
                    # print(f"Block header {block_header[0]:02X} {block_header[1]:02X} {block_header[2]:02X}")
                    if len(block_header) < 3:
                        break

                    block_size, page = struct.unpack('<H B', block_header)
                    print(f'page: {page}')
                    print(f'block size: {block_size}')
                    if block_size == 0xFFFF:
                        block_size = 16384
                        block_data = file.read(block_size)
                    else:
                        compressed_data = file.read(block_size)
                        block_data = self.unpack_block(compressed_data)

                    # Проверка и обрезка данных, если они превышают 16 КБ
                    if len(block_data) > 16384:
                        print(f"Warning: Block size exceeds 16KB for page {page}. Truncating.")
                        block_data = block_data[:16384]
                    elif len(block_data) < 16384:
                        print(f"Warning: Block size is less than 16KB for page {page}. Padding.")
                        block_data = block_data.ljust(16384, b'\x00')

                    # Загрузка блока в соответствующую страницу памяти
                    if version == 2:
                        if hw_mode == 3 or hw_mode == 4:
                            load48k = False
                    if version == 3:
                        if hw_mode == 4 or hw_mode == 5 or hw_mode == 6:
                            load48k = False


                    if load48k:
                        if page == 4:   self.memory[5] = block_data[:16384]
                        elif page == 5: self.memory[2] = block_data[:16384]
                        elif page == 8: self.memory[0] = block_data[:16384]
                    else:
                        self.memory[page-3] = block_data[:16384]


                    #if page <= 7:
                    #    self.memory[page] = block_data
                    #elif page == 8:
                    #    self.rom[0] = block_data  # ROM 0
                    #elif page == 9:
                    #    self.rom[1] = block_data  # ROM 1
                    #else:
                    #    print(f"Warning: Unknown page number {page}. Skipping.")

                    print(f"Loaded block: Page={page}, Size={len(block_data)}")

            #Цвет бордюра
            # Установка начальной конфигурации банков памяти
            cpu.io_controller.write_port(0xFE, border_color)
            #if version >= 2 and not load48k:
            #    cpu.io_controller.write_port(0x7FFD, out_7ffd)
            #    self.paged_banks = [5, 2, hw_mode & 0x07, 0]
            #    self.current_rom = (hw_mode >> 4) & 0x01

            print("Snapshot loaded successfully.")