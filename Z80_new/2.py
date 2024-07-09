class Z80:
    def __init__(self):
        self.registers = {
            'A': 0, 'F': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'H': 0, 'L': 0,
            'IX': 0, 'IY': 0, 'SP': 0, 'PC': 0,
            'A_': 0, 'F_': 0, 'B_': 0, 'C_': 0, 'D_': 0, 'E_': 0, 'H_': 0, 'L_': 0  # Альтернативный набор регистров
        }
        self.memory = [0] * 65536
        self.instructions = self.create_instruction_table()

    def create_instruction_table(self):
        return {
            0x00: lambda: None,  # NOP
            0x01: lambda: self.load_register_pair('BC', self.fetch_word()),
            0x02: lambda: self.store_memory(self.get_register_pair('BC'), self.registers['A']),
            0x03: lambda: self.inc_register_pair('BC'),
            0x04: lambda: self.inc_register('B'),
            0x05: lambda: self.dec_register('B'),
            0x06: lambda: self.load_register('B', self.fetch()),
            0x07: lambda: self.rotate_left_carry('A'),
            0x08: lambda: self.exchange_af(),
            0x09: lambda: self.add_hl('BC'),
            0x0A: lambda: self.load_register('A', self.memory[self.get_register_pair('BC')]),
            0x0B: lambda: self.dec_register_pair('BC'),
            0x0C: lambda: self.inc_register('C'),
            0x0D: lambda: self.dec_register('C'),
            0x0E: lambda: self.load_register('C', self.fetch()),
            0x0F: lambda: self.rotate_right_carry('A'),
            # ... добавьте остальные инструкции здесь ...
            0x76: lambda: self.halt(),
            0x77: lambda: self.store_memory(self.get_register_pair('HL'), self.registers['A']),
            0x78: lambda: self.load_register('A', self.registers['B']),
            0x79: lambda: self.load_register('A', self.registers['C']),
            0x7A: lambda: self.load_register('A', self.registers['D']),
            0x7B: lambda: self.load_register('A', self.registers['E']),
            0x7C: lambda: self.load_register('A', self.registers['H']),
            0x7D: lambda: self.load_register('A', self.registers['L']),
            0x7E: lambda: self.load_register('A', self.memory[self.get_register_pair('HL')]),
            0x7F: lambda: None,  # LD A, A (no operation)
            0x80: lambda: self.add('B'),
            0x81: lambda: self.add('C'),
            0x82: lambda: self.add('D'),
            0x83: lambda: self.add('E'),
            0x84: lambda: self.add('H'),
            0x85: lambda: self.add('L'),
            0x86: lambda: self.add(self.memory[self.get_register_pair('HL')]),
            0x87: lambda: self.add('A'),
            # ... добавьте остальные инструкции здесь ...
            0xC3: lambda: self.jump(self.fetch_word()),
            0xC6: lambda: self.add(self.fetch()),
            # ... добавьте остальные инструкции здесь ...
        }

    def fetch(self):
        value = self.memory[self.registers['PC']]
        self.registers['PC'] += 1
        return value

    def fetch_word(self):
        low = self.fetch()
        high = self.fetch()
        return (high << 8) | low

    def execute(self, opcode):
        if opcode in self.instructions:
            self.instructions[opcode]()
        else:
            raise ValueError(f"Unknown opcode: {opcode:02X}")

    def load_register(self, reg, value):
        self.registers[reg] = value & 0xFF
        if reg == 'A':
            self.update_flags(value)

    def load_register_pair(self, pair, value):
        high, low = pair
        self.registers[high] = (value >> 8) & 0xFF
        self.registers[low] = value & 0xFF

    def get_register_pair(self, pair):
        high, low = pair
        return (self.registers[high] << 8) | self.registers[low]

    def set_register_pair(self, pair, value):
        """
        Устанавливает значение для пары регистров.
        
        :param pair: строка, обозначающая пару регистров ('BC', 'DE', 'HL', 'AF', 'SP')
        :param value: 16-битное значение для установки
        """
        # Убеждаемся, что значение 16-битное
        value = value & 0xFFFF
        
        if pair == 'SP':
            self.registers['SP'] = value
        else:
            # Для остальных пар регистров
            high, low = pair
            self.registers[high] = (value >> 8) & 0xFF  # Старший байт
            self.registers[low] = value & 0xFF  # Младший байт

    def store_memory(self, address, value):
        self.memory[address] = value & 0xFF

    def inc_register(self, reg):
        self.registers[reg] = (self.registers[reg] + 1) & 0xFF
        self.update_flags(self.registers[reg], zero=True, sign=True, halfcarry=True)

    def dec_register(self, reg):
        self.registers[reg] = (self.registers[reg] - 1) & 0xFF
        self.update_flags(self.registers[reg], zero=True, sign=True, halfcarry=True)

    def inc_register_pair(self, pair):
        value = self.get_register_pair(pair)
        value = (value + 1) & 0xFFFF
        self.load_register_pair(pair, value)

    def dec_register_pair(self, pair):
        value = self.get_register_pair(pair)
        value = (value - 1) & 0xFFFF
        self.load_register_pair(pair, value)

    def add(self, operand):
        value = self.registers[operand] if isinstance(operand, str) else operand
        result = self.registers['A'] + value
        self.registers['A'] = result & 0xFF
        self.update_flags(result, zero=True, sign=True, carry=True, halfcarry=True)

    def add_hl(self, pair):
        hl = self.get_register_pair('HL')
        value = self.get_register_pair(pair)
        result = hl + value
        self.load_register_pair('HL', result & 0xFFFF)
        self.update_flags(result, carry=True, halfcarry=True)

    def rotate_left_carry(self, reg):
        value = self.registers[reg]
        carry = value >> 7
        result = ((value << 1) | carry) & 0xFF
        self.registers[reg] = result
        self.update_flags(result, carry=True)

    def rotate_right_carry(self, reg):
        value = self.registers[reg]
        carry = value & 1
        result = ((value >> 1) | (carry << 7)) & 0xFF
        self.registers[reg] = result
        self.update_flags(result, carry=True)

    def exchange_af(self):
        self.registers['A'], self.registers['A_'] = self.registers['A_'], self.registers['A']
        self.registers['F'], self.registers['F_'] = self.registers['F_'], self.registers['F']

    def jump(self, address):
        self.registers['PC'] = address

    def halt(self):
        # В реальной реализации здесь должна быть логика остановки процессора
        pass

    def update_flags(self, result, zero=False, sign=False, carry=False, halfcarry=False):
        if zero:
            self.registers['F'] = (self.registers['F'] & ~0x40) | (0x40 if result & 0xFF == 0 else 0)
        if sign:
            self.registers['F'] = (self.registers['F'] & ~0x80) | (0x80 if result & 0x80 else 0)
        if carry:
            self.registers['F'] = (self.registers['F'] & ~0x01) | (0x01 if result > 0xFF else 0)
        if halfcarry:
            self.registers['F'] = (self.registers['F'] & ~0x10) | (0x10 if (result & 0xF) < (self.registers['A'] & 0xF) else 0)

    def run(self):
        while True:
            opcode = self.fetch()
            self.execute(opcode)

    def load_program(self, program, start_address=0):
        for i, byte in enumerate(program):
            self.memory[start_address + i] = byte

# Пример использования
z80 = Z80()
program = [0x3E, 0x42, 0x06, 0x23, 0x78, 0x80, 0x00]  # LD A, 42; LD B, 23; LD A, B; ADD A, B; NOP
z80.load_program(program)
z80.run()