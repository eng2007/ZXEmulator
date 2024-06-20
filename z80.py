class Z80:
    def __init__(self, memory):
        # Регистры процессора
        self.af = 0
        self.bc = 0
        self.de = 0
        self.hl = 0
        self.ix = 0
        self.iy = 0
        self.sp = 0
        self.pc = 0
        self.interrupts_enabled = False
        
        # Память на 128KB (банки памяти ZX Spectrum 128)
        self.memory = [0] * 128 * 1024  # 128KB памяти
        
        # Флаги процессора
        self.zero_flag = False
        self.sign_flag = False
        self.parity_overflow_flag = False
        self.half_carry_flag = False
        self.add_subtract_flag = False
        self.carry_flag = False

    def reset(self):
        # Сброс всех регистров и флагов
        self.af = self.bc = self.de = self.hl = 0
        self.ix = self.iy = self.sp = self.pc = 0
        self.interrupts_enabled = False

    def load_memory(self, address, data):
        # Загрузка данных в память по заданному адресу
        self.memory[address:address + len(data)] = data

    def fetch_byte(self):
        # Получение байта из текущего адреса PC
        byte = self.memory[self.pc]
        self.pc += 1
        return byte

    def fetch_word(self):
        # Получение слова (2 байта) из текущего адреса PC
        low = self.fetch_byte()
        high = self.fetch_byte()
        return (high << 8) | low

    def set_flags(self, value, subtract=False, carry=None):
        # Установка флагов для результата операции
        self.zero_flag = (value == 0)
        self.sign_flag = (value & 0x80 != 0)
        self.parity_overflow_flag = (bin(value).count('1') % 2 == 0)
        self.half_carry_flag = (value & 0x10 != 0)
        self.add_subtract_flag = subtract
        if carry is not None:
            self.carry_flag = carry

    def execute_instruction(self):
        opcode = self.fetch_byte()
        if opcode == 0x00:  # NOP
            pass
        elif opcode == 0x01:  # LD BC,nn
            self.bc = self.fetch_word()
        elif opcode == 0x02:  # LD (BC),A
            self.memory[self.bc] = (self.af >> 8) & 0xFF
        elif opcode == 0x03:  # INC BC
            self.bc = (self.bc + 1) & 0xFFFF
        elif opcode == 0x04:  # INC B
            b = (self.bc >> 8) + 1
            self.bc = (self.bc & 0xFF) | ((b & 0xFF) << 8)
            self.set_flags(b, subtract=False)
        elif opcode == 0x05:  # DEC B
            b = (self.bc >> 8) - 1
            self.bc = (self.bc & 0xFF) | ((b & 0xFF) << 8)
            self.set_flags(b, subtract=True)
        elif opcode == 0x06:  # LD B,n
            self.bc = (self.bc & 0xFF) | (self.fetch_byte() << 8)
        elif opcode == 0x0A:  # LD A,(BC)
            self.af = (self.af & 0xFF) | (self.memory[self.bc] << 8)
        elif opcode == 0x0B:  # DEC BC
            self.bc = (self.bc - 1) & 0xFFFF
        elif opcode == 0x0C:  # INC C
            c = (self.bc & 0xFF) + 1
            self.bc = (self.bc & 0xFF00) | (c & 0xFF)
            self.set_flags(c, subtract=False)
        elif opcode == 0x0D:  # DEC C
            c = (self.bc & 0xFF) - 1
            self.bc = (self.bc & 0xFF00) | (c & 0xFF)
            self.set_flags(c, subtract=True)
        elif opcode == 0x0E:  # LD C,n
            self.bc = (self.bc & 0xFF00) | self.fetch_byte()
        elif opcode == 0x0F:  # RRCA
            a = (self.af >> 8) & 0xFF
            carry = a & 1
            a = (a >> 1) | (carry << 7)
            self.af = (self.af & 0xFF) | (a << 8)
            self.set_flags(a, carry=carry)
        elif opcode == 0x11:  # LD DE,nn
            self.de = self.fetch_word()
        elif opcode == 0x12:  # LD (DE),A
            self.memory[self.de] = (self.af >> 8) & 0xFF
        elif opcode == 0x13:  # INC DE
            self.de = (self.de + 1) & 0xFFFF
        elif opcode == 0x14:  # INC D
            d = (self.de >> 8) + 1
            self.de = (self.de & 0xFF) | ((d & 0xFF) << 8)
            self.set_flags(d, subtract=False)
        elif opcode == 0x15:  # DEC D
            d = (self.de >> 8) - 1
            self.de = (self.de & 0xFF) | ((d & 0xFF) << 8)
            self.set_flags(d, subtract=True)
        elif opcode == 0x16:  # LD D,n
            self.de = (self.de & 0xFF) | (self.fetch_byte() << 8)
        elif opcode == 0x17:  # RLA
            a = (self.af >> 8) & 0xFF
            carry = self.carry_flag
            self.carry_flag = (a & 0x80) != 0
            a = ((a << 1) & 0xFF) | carry
            self.af = (self.af & 0xFF) | (a << 8)
            self.set_flags(a)
        elif opcode == 0x18:  # JR e
            offset = self.fetch_byte()
            if offset & 0x80:
                offset = offset - 256
            self.pc = (self.pc + offset) & 0xFFFF
        elif opcode == 0x19:  # ADD HL,DE
            hl = self.hl + self.de
            self.set_flags(hl & 0xFFFF, carry=hl > 0xFFFF)
            self.hl = hl & 0xFFFF
        elif opcode == 0x1A:  # LD A,(DE)
            self.af = (self.af & 0xFF) | (self.memory[self.de] << 8)
        elif opcode == 0x1B:  # DEC DE
            self.de = (self.de - 1) & 0xFFFF
        elif opcode == 0x1C:  # INC E
            e = (self.de & 0xFF) + 1
            self.de = (self.de & 0xFF00) | (e & 0xFF)
            self.set_flags(e, subtract=False)
        elif opcode == 0x1D:  # DEC E
            e = (self.de & 0xFF) - 1
            self.de = (self.de & 0xFF00) | (e & 0xFF)
            self.set_flags(e, subtract=True)
        elif opcode == 0x1E:  # LD E,n
            self.de = (self.de & 0xFF00) | self.fetch_byte()
        elif opcode == 0x1F:  # RRA
            a = (self.af >> 8) & 0xFF
            carry = self.carry_flag
            self.carry_flag = a & 1
            a = (a >> 1) | (carry << 7)
            self.af = (self.af & 0xFF) | (a << 8)
            self.set_flags(a)
        elif opcode == 0x21:  # LD HL,nn
            self.hl = self.fetch_word()
        elif opcode == 0x22:  # LD (nn),HL
            addr = self.fetch_word()
            self.memory[addr] = self.hl & 0xFF
            self.memory[addr + 1] = (self.hl >> 8) & 0xFF
        elif opcode == 0x23:  # INC HL
            self.hl = (self.hl + 1) & 0xFFFF
        elif opcode == 0x24:  # INC H
            h = (self.hl >> 8) + 1
            self.hl = (self.hl & 0xFF) | ((h & 0xFF) << 8)
            self.set_flags(h, subtract=False)
        elif opcode == 0x25:  # DEC H
            h = (self.hl >> 8) - 1
            self.hl = (self.hl & 0xFF) | ((h & 0xFF) << 8)
            self.set_flags(h, subtract=True)
        elif opcode == 0x26:  # LD H,n
            self.hl = (self.hl & 0xFF) | (self.fetch_byte() << 8)
        elif opcode == 0x27:  # DAA
            a = (self.af >> 8) & 0xFF
            if self.add_subtract_flag:
                if self.carry_flag or a > 0x99:
                    a = (a + 0x60) & 0xFF
                if self.half_carry_flag or (a & 0x0F) > 0x09:
                    a = (a + 0x06) & 0xFF
            else:
                if self.carry_flag or a > 0x99:
                    a = (a - 0x60) & 0xFF
                if self.half_carry_flag or (a & 0x0F) > 0x09:
                    a = (a - 0x06) & 0xFF
            self.af = (self.af & 0xFF) | (a << 8)
            self.set_flags(a)
        elif opcode == 0x28:  # JR Z,e
            offset = self.fetch_byte()
            if self.zero_flag:
                if offset & 0x80:
                    offset = offset - 256
                self.pc = (self.pc + offset) & 0xFFFF
        elif opcode == 0x29:  # ADD HL,HL
            hl = self.hl + self.hl
            self.set_flags(hl & 0xFFFF, carry=hl > 0xFFFF)
            self.hl = hl & 0xFFFF
        elif opcode == 0x2A:  # LD HL,(nn)
            addr = self.fetch_word()
            self.hl = self.memory[addr] | (self.memory[addr + 1] << 8)
        elif opcode == 0x2B:  # DEC HL
            self.hl = (self.hl - 1) & 0xFFFF
        elif opcode == 0x2C:  # INC L
            l = (self.hl & 0xFF) + 1
            self.hl = (self.hl & 0xFF00) | (l & 0xFF)
            self.set_flags(l, subtract=False)
        elif opcode == 0x2D:  # DEC L
            l = (self.hl & 0xFF) - 1
            self.hl = (self.hl & 0xFF00) | (l & 0xFF)
            self.set_flags(l, subtract=True)
        elif opcode == 0x2E:  # LD L,n
            self.hl = (self.hl & 0xFF00) | self.fetch_byte()
        elif opcode == 0x2F:  # CPL
            a = (self.af >> 8) & 0xFF
            a = a ^ 0xFF
            self.af = (self.af & 0xFF) | (a << 8)
            self.add_subtract_flag = True
            self.half_carry_flag = True
        elif opcode == 0x31:  # LD SP,nn
            self.sp = self.fetch_word()
        elif opcode == 0x32:  # LD (nn),A
            addr = self.fetch_word()
            self.memory[addr] = (self.af >> 8) & 0xFF
        elif opcode == 0x33:  # INC SP
            self.sp = (self.sp + 1) & 0xFFFF
        elif opcode == 0x34:  # INC (HL)
            addr = self.hl
            value = self.memory[addr] + 1
            self.memory[addr] = value & 0xFF
            self.set_flags(value, subtract=False)
        elif opcode == 0x35:  # DEC (HL)
            addr = self.hl
            value = self.memory[addr] - 1
            self.memory[addr] = value & 0xFF
            self.set_flags(value, subtract=True)
        elif opcode == 0x36:  # LD (HL),n
            self.memory[self.hl] = self.fetch_byte()
        elif opcode == 0x37:  # SCF
            self.carry_flag = True
            self.add_subtract_flag = False
            self.half_carry_flag = False
        elif opcode == 0x38:  # JR C,e
            offset = self.fetch_byte()
            if self.carry_flag:
                if offset & 0x80:
                    offset = offset - 256
                self.pc = (self.pc + offset) & 0xFFFF
        elif opcode == 0x39:  # ADD HL,SP
            hl = self.hl + self.sp
            self.set_flags(hl & 0xFFFF, carry=hl > 0xFFFF)
            self.hl = hl & 0xFFFF
        elif opcode == 0x3A:  # LD A,(nn)
            addr = self.fetch_word()
            self.af = (self.af & 0xFF) | (self.memory[addr] << 8)
        elif opcode == 0x3B:  # DEC SP
            self.sp = (self.sp - 1) & 0xFFFF
        elif opcode == 0x3C:  # INC A
            a = (self.af >> 8) + 1
            self.af = (self.af & 0xFF) | ((a & 0xFF) << 8)
            self.set_flags(a, subtract=False)
        elif opcode == 0x3D:  # DEC A
            a = (self.af >> 8) - 1
            self.af = (self.af & 0xFF) | ((a & 0xFF) << 8)
            self.set_flags(a, subtract=True)
        elif opcode == 0x3E:  # LD A,n
            self.af = (self.af & 0xFF) | (self.fetch_byte() << 8)
        elif opcode == 0x3F:  # CCF
            self.carry_flag = not self.carry_flag
            self.add_subtract_flag = False
            self.half_carry_flag = self.carry_flag
        elif opcode == 0x40:  # LD B,B
            pass
        elif opcode == 0x41:  # LD B,C
            self.bc = (self.bc & 0xFF) | ((self.bc & 0xFF) << 8)
        elif opcode == 0x42:  # LD B,D
            self.bc = (self.bc & 0xFF) | ((self.de >> 8) << 8)
        elif opcode == 0x43:  # LD B,E
            self.bc = (self.bc & 0xFF) | ((self.de & 0xFF) << 8)
        elif opcode == 0x44:  # LD B,H
            self.bc = (self.bc & 0xFF) | ((self.hl >> 8) << 8)
        elif opcode == 0x45:  # LD B,L
            self.bc = (self.bc & 0xFF) | ((self.hl & 0xFF) << 8)
        elif opcode == 0x46:  # LD B,(HL)
            self.bc = (self.bc & 0xFF) | (self.memory[self.hl] << 8)
        elif opcode == 0x47:  # LD B,A
            self.bc = (self.bc & 0xFF) | (self.af & 0xFF00)
        # ... Implement all other opcodes ...

    def run(self, steps):
        # Запуск процессора на заданное количество шагов
        for _ in range(steps):
            self.execute_instruction()

# Пример использования
#z80 = Z80()
#z80.reset()
#z80.load_memory(0, [0x01, 0x34, 0x12,  # LD BC,1234h
#                    0x03,              # INC BC
#                    0xAF,              # XOR A
#                    0xC3, 0x00, 0x10])  # JP 1000h
#z80.run(10)
#print(f"PC: {hex(z80.pc)}")
#print(f"BC: {hex(z80.bc)}")
#print(f"AF: {hex(z80.af)}")
