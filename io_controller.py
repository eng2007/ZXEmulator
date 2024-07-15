# io_controller.py
class IOController:
    def __init__(self, emulator):
        self.emulator = emulator
        self.border_color = 0  # Цвет границы
        self.last_7ffd_value = 0

    def write_port(self, port, value):
        #print(f"Output to port {port:04X}: {value:02X}")
        if (port & 0xFF) == 0xFE:
            # Нижние три бита задают цвет границы
            self.border_color = value & 0x07
            #print(f"Установлен цвет границы: {self.border_color}")
            self.emulator.set_border(self.border_color)
        elif port == 0x7FFD:
            self.handle_7ffd_write(value)

    def handle_7ffd_write(self, value):
        if not (self.last_7ffd_value & 0x20):  # Проверяем бит блокировки
            self.last_7ffd_value = value
            ram_bank = value & 0x07
            self.emulator.memory.paged_banks[3] = ram_bank
            self.emulator.memory.current_rom = (value >> 4) & 0x01
            screen_bank = 5 if (value & 0x08) else 7
            self.emulator.memory.paged_banks[1] = screen_bank
            print(f"Memory configuration changed: RAM bank {ram_bank}, ROM {self.emulator.memory.current_rom}, Screen bank {screen_bank}")

    def read_port(self, port):
        if (port & 0xFF) == 0xFE:
            # Чтение состояния клавиатуры
            
            self.emulator.keyboard.read_keyboard()  # Обновляем состояние клавиатуры
            #keyboard_line = (port >> 8) & 0xFF  # Получаем старший байт для выбора строки
            #result = self.emulator.keyboard.read_port_fe(keyboard_line)
            result = self.emulator.keyboard.read_port_fe(port)
            #if (~result & 0xFF) != 0:
            #    print(f'Port:{port:04X} Key pressed {result:08b}')
            #print(f'Read keyboard port {port:04X}, result:{result:08b}')   
            #return 0 
            return result
        if port == 0x1B: return 0x7D            
        if port == 0xE3: return 0xC1
        if port == 0xE2: return 0x71
        if port == 0x6B: return 0x29
        return 0xFF  # Возвращаем значение по умолчанию для других портов