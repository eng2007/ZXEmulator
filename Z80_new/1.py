class Z80:
    def __init__(self):
        self.registers = {
            'A': 0, 'F': 0, 'B': 0, 'C': 0,
            'D': 0, 'E': 0, 'H': 0, 'L': 0,
            'IX': 0, 'IY': 0, 'SP': 0, 'PC': 0
        }
        self.memory = [0] * 65536
        self.instructions = self.create_instruction_table()

    def create_instruction_table(self):
        return {
            0x3E: lambda: self.load_register('A', self.fetch()),
            0x06: lambda: self.load_register('B', self.fetch()),
            0x0E: lambda: self.load_register('C', self.fetch()),
            0x78: lambda: self.load_register('A', self.registers['B']),
            0x47: lambda: self.load_register('B', self.registers['A']),
            0xC3: lambda: self.jump(),
            0x80: lambda: self.arithmetic('ADD', 'B'),
            0x90: lambda: self.arithmetic('SUB', 'B'),
            0xA0: lambda: self.logical('AND', 'B'),
            0xB0: lambda: self.logical('OR', 'B'),
            0xC6: lambda: self.arithmetic('ADD', self.fetch()),
            0xD6: lambda: self.arithmetic('SUB', self.fetch()),
            0x00: lambda: None  # NOP
        }

    def fetch(self):
        value = self.memory[self.registers['PC']]
        self.registers['PC'] += 1
        return value

    def execute(self, opcode):
        if opcode in self.instructions:
            self.instructions[opcode]()
        else:
            raise ValueError(f"Unknown opcode: {opcode:02X}")

    def load_register(self, reg, value):
        self.registers[reg] = value & 0xFF

    def jump(self):
        self.registers['PC'] = self.fetch() | (self.fetch() << 8)

    def arithmetic(self, operation, operand):
        value = self.registers[operand] if isinstance(operand, str) else operand
        if operation == 'ADD':
            self.registers['A'] = (self.registers['A'] + value) & 0xFF
        elif operation == 'SUB':
            self.registers['A'] = (self.registers['A'] - value) & 0xFF
        # Здесь должна быть установка флагов

    def logical(self, operation, operand):
        value = self.registers[operand]
        if operation == 'AND':
            self.registers['A'] &= value
        elif operation == 'OR':
            self.registers['A'] |= value
        # Здесь должна быть установка флагов

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