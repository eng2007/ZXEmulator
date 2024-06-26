# io_controller.py
class IOController:
    def __init__(self, emulator):
        self.emulator = emulator
        self.border_color = 0  # Цвет границы

    def write_port(self, port, value):
        #print(f"Output to port {port:02X}: {value:02X}")  
        if port == 0xFE:
            # Нижние три бита задают цвет границы
            self.border_color = value & 0x07
            #print(f"Установлен цвет границы: {self.border_color}")
            self.emulator.set_border(self.border_color)

    def read_port(self, port):
        #print(f"Input from port {port:02X}")  
        if port == 0xFE:
            # Чтение состояния клавиатуры
            return self.emulator.keyboard.read_keyboard()
        return 0xFF  # Возвращаем значение по умолчанию для других портов
