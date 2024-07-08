class Z80:
    def __init__(self):
        # ... (предыдущая инициализация)
        self.registers['IX'] = 0
        self.registers['IY'] = 0
        self.registers['I'] = 0
        self.registers['R'] = 0
        self.iff1 = False
        self.iff2 = False
        self.im = 0

        self.registers = {
            'A': 0, 'F': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'H': 0, 'L': 0,
            'IX': 0, 'IY': 0, 'SP': 0, 'PC': 0,
            'A_': 0, 'F_': 0, 'B_': 0, 'C_': 0, 'D_': 0, 'E_': 0, 'H_': 0, 'L_': 0  # Альтернативный набор регистров
        }
        self.memory = [0] * 65536
        self.instructions = self.create_instruction_table()

    # Вспомогательные методы для битовых операций
    def rlc(self, value):
        carry = value >> 7
        result = ((value << 1) | carry) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)
        return result

    def rrc(self, value):
        carry = value & 1
        result = ((value >> 1) | (carry << 7)) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)
        return result

    def rl(self, value):
        old_carry = self.get_flag('C')
        carry = value >> 7
        result = ((value << 1) | old_carry) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)
        return result

    def rr(self, value):
        old_carry = self.get_flag('C')
        carry = value & 1
        result = ((value >> 1) | (old_carry << 7)) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)
        return result

    def sla(self, value):
        carry = value >> 7
        result = (value << 1) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)
        return result

    def sra(self, value):
        carry = value & 1
        result = ((value >> 1) | (value & 0x80)) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)
        return result

    def sll(self, value):
        carry = value >> 7
        result = ((value << 1) | 1) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)
        return result

    def srl(self, value):
        carry = value & 1
        result = (value >> 1) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)
        return result

    def bit(self, bit, value):
        result = value & (1 << bit)
        self.set_flag('Z', result == 0)
        self.set_flag('H', 1)
        self.set_flag('N', 0)
        self.set_flag('P/V', result == 0)
        self.set_flag('S', bit == 7 and result != 0)

    def res(self, bit, value):
        return value & ~(1 << bit)

    def set(self, bit, value):
        return value | (1 << bit)

    # Методы для ввода/вывода
    def in_r_c(self, reg):
        port = self.registers['C']
        value = self.io_read(port)
        self.registers[reg] = value
        self.update_flags(value, zero=True, sign=True, parity=True)

    def out_c_r(self, reg):
        port = self.registers['C']
        value = self.registers[reg]
        self.io_write(port, value)

    # Методы для работы с регистровыми парами
    def add_hl(self, rp):
        hl = self.get_register_pair('HL')
        value = self.get_register_pair(rp)
        result = hl + value
        self.set_register_pair('HL', result & 0xFFFF)
        self.set_flag('C', result > 0xFFFF)
        self.set_flag('H', (hl & 0xFFF) + (value & 0xFFF) > 0xFFF)
        self.set_flag('N', 0)

    def adc_hl(self, rp):
        hl = self.get_register_pair('HL')
        value = self.get_register_pair(rp)
        carry = self.get_flag('C')
        result = hl + value + carry
        self.set_register_pair('HL', result & 0xFFFF)
        self.set_flag('C', result > 0xFFFF)
        self.set_flag('H', (hl & 0xFFF) + (value & 0xFFF) + carry > 0xFFF)
        self.update_flags(result & 0xFFFF, zero=True, sign=True, parity=True)
        self.set_flag('N', 0)

    def sbc_hl(self, rp):
        hl = self.get_register_pair('HL')
        value = self.get_register_pair(rp)
        carry = self.get_flag('C')
        result = hl - value - carry
        self.set_register_pair('HL', result & 0xFFFF)
        self.set_flag('C', result < 0)
        self.set_flag('H', (hl & 0xFFF) - (value & 0xFFF) - carry < 0)
        self.update_flags(result & 0xFFFF, zero=True, sign=True, parity=True)
        self.set_flag('N', 1)

    # Специальные инструкции
    def neg(self):
        value = self.registers['A']
        result = (-value) & 0xFF
        self.registers['A'] = result
        self.set_flag('C', value != 0)
        self.set_flag('H', (value & 0xF) != 0)
        self.update_flags(result, zero=True, sign=True, parity=True)
        self.set_flag('N', 1)

    def rrd(self):
        a = self.registers['A']
        hl = self.get_register_pair('HL')
        m = self.memory[hl]
        self.registers['A'] = (a & 0xF0) | (m & 0x0F)
        self.memory[hl] = ((m >> 4) | (a << 4)) & 0xFF
        self.update_flags(self.registers['A'], zero=True, sign=True, parity=True)
        self.set_flag('H', 0)
        self.set_flag('N', 0)

    def rld(self):
        a = self.registers['A']
        hl = self.get_register_pair('HL')
        m = self.memory[hl]
        self.registers['A'] = (a & 0xF0) | (m >> 4)
        self.memory[hl] = ((m << 4) | (a & 0x0F)) & 0xFF
        self.update_flags(self.registers['A'], zero=True, sign=True, parity=True)
        self.set_flag('H', 0)
        self.set_flag('N', 0)

    # Блочные операции
    def ldi(self):
        self._block_transfer(1)
        self.set_flag('H', 0)
        self.set_flag('N', 0)
        self.set_flag('P/V', self.get_register_pair('BC') != 0)

    def ldd(self):
        self._block_transfer(-1)
        self.set_flag('H', 0)
        self.set_flag('N', 0)
        self.set_flag('P/V', self.get_register_pair('BC') != 0)

    def ldir(self):
        self.ldi()
        if self.get_register_pair('BC') != 0:
            self.registers['PC'] -= 2

    def lddr(self):
        self.ldd()
        if self.get_register_pair('BC') != 0:
            self.registers['PC'] -= 2

    def _block_transfer(self, direction):
        hl = self.get_register_pair('HL')
        de = self.get_register_pair('DE')
        bc = self.get_register_pair('BC')
        
        value = self.memory[hl]
        self.memory[de] = value
        
        self.set_register_pair('HL', (hl + direction) & 0xFFFF)
        self.set_register_pair('DE', (de + direction) & 0xFFFF)
        self.set_register_pair('BC', (bc - 1) & 0xFFFF)

    # Реализация инструкций с префиксами DD и FD
    def execute_dd(self):
        # Implement IX-related instructions
        # This is a placeholder and should be expanded with actual IX instructions
        opcode = self.fetch()
        self._execute_indexed('IX', opcode)

    def execute_fd(self):
        # Implement IY-related instructions
        # This is a placeholder and should be expanded with actual IY instructions
        opcode = self.fetch()
        self._execute_indexed('IY', opcode)

    def _execute_indexed(self, index_reg, opcode):
        if opcode in [0x21, 0x22, 0x2A, 0x36]:
            # Специальные случаи для LD IX/IY, nn и LD (nn), IX/IY
            if opcode == 0x21:  # LD IX/IY, nn
                self.registers[index_reg] = self.fetch_word()
            elif opcode == 0x22:  # LD (nn), IX/IY
                address = self.fetch_word()
                self.store_word(address, self.registers[index_reg])
            elif opcode == 0x2A:  # LD IX/IY, (nn)
                address = self.fetch_word()
                self.registers[index_reg] = self.memory[address] | (self.memory[address + 1] << 8)
            elif opcode == 0x36:  # LD (IX/IY+d), n
                offset = self.fetch_signed()
                value = self.fetch()
                address = (self.registers[index_reg] + offset) & 0xFFFF
                self.memory[address] = value
        elif opcode & 0xC0 == 0x40:  # LD instructions
            self._indexed_load(index_reg, opcode)
        elif opcode & 0xC0 == 0x80:  # Arithmetic instructions
            self._indexed_arithmetic(index_reg, opcode)
        else:
            raise ValueError(f"Unsupported {index_reg} instruction: {opcode:02X}")

    def _indexed_load(self, index_reg, opcode):
        reg = ['B', 'C', 'D', 'E', 'H', 'L', None, 'A'][opcode & 0x07]
        if opcode & 0x07 == 0x06:  # LD r, (IX/IY+d)
            offset = self.fetch_signed()
            address = (self.registers[index_reg] + offset) & 0xFFFF
            self.registers[reg] = self.memory[address]
        elif (opcode & 0x38) == 0x30:  # LD (IX/IY+d), r
            offset = self.fetch_signed()
            address = (self.registers[index_reg] + offset) & 0xFFFF
            self.memory[address] = self.registers[reg]

    def _indexed_arithmetic(self, index_reg, opcode):
        operation = (opcode & 0x38) >> 3
        offset = self.fetch_signed()
        address = (self.registers[index_reg] + offset) & 0xFFFF
        value = self.memory[address]
        
        if operation == 0:  # ADD A, (IX/IY+d)
            self.add(value)
        elif operation == 1:  # ADC A, (IX/IY+d)
            self.adc(value)
        elif operation == 2:  # SUB (IX/IY+d)
            self.sub(value)
        elif operation == 3:  # SBC A, (IX/IY+d)
            self.sbc(value)
        elif operation == 4:  # AND (IX/IY+d)
            self.and_a(value)
        elif operation == 5:  # XOR (IX/IY+d)
            self.xor_a(value)
        elif operation == 6:  # OR (IX/IY+d)
            self.or_a(value)
        elif operation == 7:  # CP (IX/IY+d)
            self.cp(value)

    # Вспомогательные методы
    def fetch_signed(self):
        value = self.fetch()
        return value if value < 128 else value - 256

    def set_flag(self, flag, value):
        mask = {'C': 0x01, 'N': 0x02, 'P/V': 0x04, 'H': 0x10, 'Z': 0x40, 'S': 0x80}[flag]
        if value:
            self.registers['F'] |= mask
        else:
            self.registers['F'] &= ~mask

    def get_flag(self, flag):
        mask = {'C': 0x01, 'N': 0x02, 'P/V': 0x04, 'H': 0x10, 'Z': 0x40, 'S': 0x80}[flag]
        return (self.registers['F'] & mask) != 0

    def update_flags(self, result, zero=False, sign=False, parity=False):
        if zero:
            self.set_flag('Z', result == 0)
        if sign:
            self.set_flag('S', result & 0x80)
        if parity:
            self.set_flag('P/V', bin(result).count('1') % 2 == 0)

    # Методы ввода-вывода (заглушки, которые нужно реализовать)
    def io_read(self, port):
        # Реализуйте чтение из порта
        return 0

    def io_write(self, port, value):
        # Реализуйте запись в порт
        pass


    def create_instruction_table(self):
        def ld_r_r(r1, r2):
            return lambda: self.load_register(r1, self.registers[r2])

        def ld_r_n(r):
            return lambda: self.load_register(r, self.fetch())

        def ld_r_hl(r):
            return lambda: self.load_register(r, self.memory[self.get_register_pair('HL')])

        def ld_hl_r(r):
            return lambda: self.store_memory(self.get_register_pair('HL'), self.registers[r])

        def ld_a_rr(rr):
            return lambda: self.load_register('A', self.memory[self.get_register_pair(rr)])

        def ld_rr_a(rr):
            return lambda: self.store_memory(self.get_register_pair(rr), self.registers['A'])

        def add_a_r(r):
            return lambda: self.add(self.registers[r])

        def adc_a_r(r):
            return lambda: self.adc(self.registers[r])

        def sub_r(r):
            return lambda: self.sub(self.registers[r])

        def sbc_a_r(r):
            return lambda: self.sbc(self.registers[r])

        def and_r(r):
            return lambda: self.and_a(self.registers[r])

        def xor_r(r):
            return lambda: self.xor_a(self.registers[r])

        def or_r(r):
            return lambda: self.or_a(self.registers[r])

        def cp_r(r):
            return lambda: self.cp(self.registers[r])

        def inc_r(r):
            return lambda: self.inc_register(r)

        def dec_r(r):
            return lambda: self.dec_register(r)

        def add_hl_rr(rr):
            return lambda: self.add_hl(rr)

        def inc_rr(rr):
            return lambda: self.inc_register_pair(rr)

        def dec_rr(rr):
            return lambda: self.dec_register_pair(rr)

        return {
            # 8-bit load group
            0x40: ld_r_r('B', 'B'), 0x41: ld_r_r('B', 'C'), 0x42: ld_r_r('B', 'D'), 0x43: ld_r_r('B', 'E'),
            0x44: ld_r_r('B', 'H'), 0x45: ld_r_r('B', 'L'), 0x46: ld_r_hl('B'), 0x47: ld_r_r('B', 'A'),
            0x48: ld_r_r('C', 'B'), 0x49: ld_r_r('C', 'C'), 0x4A: ld_r_r('C', 'D'), 0x4B: ld_r_r('C', 'E'),
            0x4C: ld_r_r('C', 'H'), 0x4D: ld_r_r('C', 'L'), 0x4E: ld_r_hl('C'), 0x4F: ld_r_r('C', 'A'),
            0x50: ld_r_r('D', 'B'), 0x51: ld_r_r('D', 'C'), 0x52: ld_r_r('D', 'D'), 0x53: ld_r_r('D', 'E'),
            0x54: ld_r_r('D', 'H'), 0x55: ld_r_r('D', 'L'), 0x56: ld_r_hl('D'), 0x57: ld_r_r('D', 'A'),
            0x58: ld_r_r('E', 'B'), 0x59: ld_r_r('E', 'C'), 0x5A: ld_r_r('E', 'D'), 0x5B: ld_r_r('E', 'E'),
            0x5C: ld_r_r('E', 'H'), 0x5D: ld_r_r('E', 'L'), 0x5E: ld_r_hl('E'), 0x5F: ld_r_r('E', 'A'),
            0x60: ld_r_r('H', 'B'), 0x61: ld_r_r('H', 'C'), 0x62: ld_r_r('H', 'D'), 0x63: ld_r_r('H', 'E'),
            0x64: ld_r_r('H', 'H'), 0x65: ld_r_r('H', 'L'), 0x66: ld_r_hl('H'), 0x67: ld_r_r('H', 'A'),
            0x68: ld_r_r('L', 'B'), 0x69: ld_r_r('L', 'C'), 0x6A: ld_r_r('L', 'D'), 0x6B: ld_r_r('L', 'E'),
            0x6C: ld_r_r('L', 'H'), 0x6D: ld_r_r('L', 'L'), 0x6E: ld_r_hl('L'), 0x6F: ld_r_r('L', 'A'),
            0x70: ld_hl_r('B'), 0x71: ld_hl_r('C'), 0x72: ld_hl_r('D'), 0x73: ld_hl_r('E'),
            0x74: ld_hl_r('H'), 0x75: ld_hl_r('L'), 0x77: ld_hl_r('A'),
            0x78: ld_r_r('A', 'B'), 0x79: ld_r_r('A', 'C'), 0x7A: ld_r_r('A', 'D'), 0x7B: ld_r_r('A', 'E'),
            0x7C: ld_r_r('A', 'H'), 0x7D: ld_r_r('A', 'L'), 0x7E: ld_r_hl('A'), 0x7F: ld_r_r('A', 'A'),
            0x06: ld_r_n('B'), 0x0E: ld_r_n('C'), 0x16: ld_r_n('D'), 0x1E: ld_r_n('E'),
            0x26: ld_r_n('H'), 0x2E: ld_r_n('L'), 0x36: lambda: self.store_memory(self.get_register_pair('HL'), self.fetch()),
            0x3E: ld_r_n('A'),
            0x0A: ld_a_rr('BC'), 0x1A: ld_a_rr('DE'), 0x3A: lambda: self.load_register('A', self.memory[self.fetch_word()]),
            0x02: ld_rr_a('BC'), 0x12: ld_rr_a('DE'), 0x32: lambda: self.store_memory(self.fetch_word(), self.registers['A']),

            # 16-bit load group
            0x01: lambda: self.load_register_pair('BC', self.fetch_word()),
            0x11: lambda: self.load_register_pair('DE', self.fetch_word()),
            0x21: lambda: self.load_register_pair('HL', self.fetch_word()),
            0x31: lambda: self.load_register_pair('SP', self.fetch_word()),
            0x2A: lambda: self.load_register_pair('HL', self.memory[self.fetch_word()]),
            0x22: lambda: self.store_word(self.fetch_word(), self.get_register_pair('HL')),
            0xF9: lambda: self.load_register_pair('SP', self.get_register_pair('HL')),
            0xC5: lambda: self.push('BC'), 0xD5: lambda: self.push('DE'),
            0xE5: lambda: self.push('HL'), 0xF5: lambda: self.push('AF'),
            0xC1: lambda: self.pop('BC'), 0xD1: lambda: self.pop('DE'),
            0xE1: lambda: self.pop('HL'), 0xF1: lambda: self.pop('AF'),

            # Exchange, Block Transfer, and Search Group
            0xEB: lambda: self.exchange_de_hl(),
            0x08: lambda: self.exchange_af(),
            0xD9: lambda: self.exx(),
            0xE3: lambda: self.exchange_sp_hl(),

            # 8-bit arithmetic group
            0x80: add_a_r('B'), 0x81: add_a_r('C'), 0x82: add_a_r('D'), 0x83: add_a_r('E'),
            0x84: add_a_r('H'), 0x85: add_a_r('L'), 0x86: lambda: self.add(self.memory[self.get_register_pair('HL')]),
            0x87: add_a_r('A'), 0xC6: lambda: self.add(self.fetch()),
            0x88: adc_a_r('B'), 0x89: adc_a_r('C'), 0x8A: adc_a_r('D'), 0x8B: adc_a_r('E'),
            0x8C: adc_a_r('H'), 0x8D: adc_a_r('L'), 0x8E: lambda: self.adc(self.memory[self.get_register_pair('HL')]),
            0x8F: adc_a_r('A'), 0xCE: lambda: self.adc(self.fetch()),
            0x90: sub_r('B'), 0x91: sub_r('C'), 0x92: sub_r('D'), 0x93: sub_r('E'),
            0x94: sub_r('H'), 0x95: sub_r('L'), 0x96: lambda: self.sub(self.memory[self.get_register_pair('HL')]),
            0x97: sub_r('A'), 0xD6: lambda: self.sub(self.fetch()),
            0x98: sbc_a_r('B'), 0x99: sbc_a_r('C'), 0x9A: sbc_a_r('D'), 0x9B: sbc_a_r('E'),
            0x9C: sbc_a_r('H'), 0x9D: sbc_a_r('L'), 0x9E: lambda: self.sbc(self.memory[self.get_register_pair('HL')]),
            0x9F: sbc_a_r('A'), 0xDE: lambda: self.sbc(self.fetch()),
            0xA0: and_r('B'), 0xA1: and_r('C'), 0xA2: and_r('D'), 0xA3: and_r('E'),
            0xA4: and_r('H'), 0xA5: and_r('L'), 0xA6: lambda: self.and_a(self.memory[self.get_register_pair('HL')]),
            0xA7: and_r('A'), 0xE6: lambda: self.and_a(self.fetch()),
            0xA8: xor_r('B'), 0xA9: xor_r('C'), 0xAA: xor_r('D'), 0xAB: xor_r('E'),
            0xAC: xor_r('H'), 0xAD: xor_r('L'), 0xAE: lambda: self.xor_a(self.memory[self.get_register_pair('HL')]),
            0xAF: xor_r('A'), 0xEE: lambda: self.xor_a(self.fetch()),
            0xB0: or_r('B'), 0xB1: or_r('C'), 0xB2: or_r('D'), 0xB3: or_r('E'),
            0xB4: or_r('H'), 0xB5: or_r('L'), 0xB6: lambda: self.or_a(self.memory[self.get_register_pair('HL')]),
            0xB7: or_r('A'), 0xF6: lambda: self.or_a(self.fetch()),
            0xB8: cp_r('B'), 0xB9: cp_r('C'), 0xBA: cp_r('D'), 0xBB: cp_r('E'),
            0xBC: cp_r('H'), 0xBD: cp_r('L'), 0xBE: lambda: self.cp(self.memory[self.get_register_pair('HL')]),
            0xBF: cp_r('A'), 0xFE: lambda: self.cp(self.fetch()),
            0x04: inc_r('B'), 0x0C: inc_r('C'), 0x14: inc_r('D'), 0x1C: inc_r('E'),
            0x24: inc_r('H'), 0x2C: inc_r('L'), 0x34: lambda: self.inc_memory(self.get_register_pair('HL')),
            0x3C: inc_r('A'),
            0x05: dec_r('B'), 0x0D: dec_r('C'), 0x15: dec_r('D'), 0x1D: dec_r('E'),
            0x25: dec_r('H'), 0x2D: dec_r('L'), 0x35: lambda: self.dec_memory(self.get_register_pair('HL')),
            0x3D: dec_r('A'),

            # General-purpose arithmetic and CPU control groups
            0x27: lambda: self.daa(),
            0x2F: lambda: self.cpl(),
            0x3F: lambda: self.ccf(),
            0x37: lambda: self.scf(),
            0x00: lambda: None,  # NOP
            0x76: lambda: self.halt(),
            0xF3: lambda: self.di(),
            0xFB: lambda: self.ei(),

            # 16-bit arithmetic group
            0x09: add_hl_rr('BC'), 0x19: add_hl_rr('DE'),
            0x29: add_hl_rr('HL'), 0x39: add_hl_rr('SP'),
            0x03: inc_rr('BC'), 0x13: inc_rr('DE'),
            0x23: inc_rr('HL'), 0x33: inc_rr('SP'),
            0x0B: dec_rr('BC'), 0x1B: dec_rr('DE'),
            0x2B: dec_rr('HL'), 0x3B: dec_rr('SP'),

            # Rotate and Shift group
            0x07: lambda: self.rlca(),
            0x0F: lambda: self.rrca(),
            # Rotate and Shift group (продолжение)
            0x17: lambda: self.rla(),
            0x1F: lambda: self.rra(),

            # Jump group
            0xC3: lambda: self.jp(self.fetch_word()),
            0xC2: lambda: self.jp_cc('NZ', self.fetch_word()),
            0xCA: lambda: self.jp_cc('Z', self.fetch_word()),
            0xD2: lambda: self.jp_cc('NC', self.fetch_word()),
            0xDA: lambda: self.jp_cc('C', self.fetch_word()),
            0xE9: lambda: self.jp(self.get_register_pair('HL')),
            0x18: lambda: self.jr(self.fetch_signed()),
            0x20: lambda: self.jr_cc('NZ', self.fetch_signed()),
            0x28: lambda: self.jr_cc('Z', self.fetch_signed()),
            0x30: lambda: self.jr_cc('NC', self.fetch_signed()),
            0x38: lambda: self.jr_cc('C', self.fetch_signed()),
            0x10: lambda: self.djnz(self.fetch_signed()),

            # Call and Return group
            0xCD: lambda: self.call(self.fetch_word()),
            0xC4: lambda: self.call_cc('NZ', self.fetch_word()),
            0xCC: lambda: self.call_cc('Z', self.fetch_word()),
            0xD4: lambda: self.call_cc('NC', self.fetch_word()),
            0xDC: lambda: self.call_cc('C', self.fetch_word()),
            0xC9: lambda: self.ret(),
            0xC0: lambda: self.ret_cc('NZ'),
            0xC8: lambda: self.ret_cc('Z'),
            0xD0: lambda: self.ret_cc('NC'),
            0xD8: lambda: self.ret_cc('C'),
            0xC7: lambda: self.rst(0x00), 0xCF: lambda: self.rst(0x08),
            0xD7: lambda: self.rst(0x10), 0xDF: lambda: self.rst(0x18),
            0xE7: lambda: self.rst(0x20), 0xEF: lambda: self.rst(0x28),
            0xF7: lambda: self.rst(0x30), 0xFF: lambda: self.rst(0x38),

            # Input and Output group
            0xDB: lambda: self.in_a_n(),
            0xD3: lambda: self.out_n_a(),

            # Prefix Instructions
            0xCB: lambda: self.execute_cb(),
            0xDD: lambda: self.execute_dd(),
            0xED: lambda: self.execute_ed(),
            0xFD: lambda: self.execute_fd(),
        }

    def execute_cb(self):
        opcode = self.fetch()
        
        r = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
        
        if opcode < 0x40:  # Rotation and shift instructions
            operation = [self.rlc, self.rrc, self.rl, self.rr, self.sla, self.sra, self.sll, self.srl][opcode >> 3]
            operand = r[opcode & 0x07]
            if operand == '(HL)':
                value = self.memory[self.get_register_pair('HL')]
                result = operation(value)
                self.store_memory(self.get_register_pair('HL'), result)
            else:
                self.registers[operand] = operation(self.registers[operand])
        elif opcode < 0x80:  # Bit test instructions
            bit = (opcode >> 3) & 0x07
            operand = r[opcode & 0x07]
            if operand == '(HL)':
                value = self.memory[self.get_register_pair('HL')]
            else:
                value = self.registers[operand]
            self.bit(bit, value)
        elif opcode < 0xC0:  # Bit reset instructions
            bit = (opcode >> 3) & 0x07
            operand = r[opcode & 0x07]
            if operand == '(HL)':
                value = self.memory[self.get_register_pair('HL')]
                result = self.res(bit, value)
                self.store_memory(self.get_register_pair('HL'), result)
            else:
                self.registers[operand] = self.res(bit, self.registers[operand])
        else:  # Bit set instructions
            bit = (opcode >> 3) & 0x07
            operand = r[opcode & 0x07]
            if operand == '(HL)':
                value = self.memory[self.get_register_pair('HL')]
                result = self.set(bit, value)
                self.store_memory(self.get_register_pair('HL'), result)
            else:
                self.registers[operand] = self.set(bit, self.registers[operand])

    def execute_ed(self):
        opcode = self.fetch()
        ed_instructions = {
            0x40: lambda: self.in_r_c('B'),
            0x41: lambda: self.out_c_r('B'),
            0x42: lambda: self.sbc_hl('BC'),
            0x43: lambda: self.store_word(self.fetch_word(), self.get_register_pair('BC')),
            0x44: lambda: self.neg(),
            0x45: lambda: self.retn(),
            0x46: lambda: self.im(0),
            0x47: lambda: self.ld_i_a(),
            0x48: lambda: self.in_r_c('C'),
            0x49: lambda: self.out_c_r('C'),
            0x4A: lambda: self.adc_hl('BC'),
            0x4B: lambda: self.load_register_pair('BC', self.memory[self.fetch_word()]),
            0x4D: lambda: self.reti(),
            0x4F: lambda: self.ld_r_a(),
            0x50: lambda: self.in_r_c('D'),
            0x51: lambda: self.out_c_r('D'),
            0x52: lambda: self.sbc_hl('DE'),
            0x53: lambda: self.store_word(self.fetch_word(), self.get_register_pair('DE')),
            0x56: lambda: self.im(1),
            0x57: lambda: self.ld_a_i(),
            0x58: lambda: self.in_r_c('E'),
            0x59: lambda: self.out_c_r('E'),
            0x5A: lambda: self.adc_hl('DE'),
            0x5B: lambda: self.load_register_pair('DE', self.memory[self.fetch_word()]),
            0x5E: lambda: self.im(2),
            0x5F: lambda: self.ld_a_r(),
            0x60: lambda: self.in_r_c('H'),
            0x61: lambda: self.out_c_r('H'),
            0x62: lambda: self.sbc_hl('HL'),
            0x63: lambda: self.store_word(self.fetch_word(), self.get_register_pair('HL')),
            0x67: lambda: self.rrd(),
            0x68: lambda: self.in_r_c('L'),
            0x69: lambda: self.out_c_r('L'),
            0x6A: lambda: self.adc_hl('HL'),
            0x6B: lambda: self.load_register_pair('HL', self.memory[self.fetch_word()]),
            0x6F: lambda: self.rld(),
            0x72: lambda: self.sbc_hl('SP'),
            0x73: lambda: self.store_word(self.fetch_word(), self.get_register_pair('SP')),
            0x78: lambda: self.in_r_c('A'),
            0x79: lambda: self.out_c_r('A'),
            0x7A: lambda: self.adc_hl('SP'),
            0x7B: lambda: self.load_register_pair('SP', self.memory[self.fetch_word()]),
            0xA0: lambda: self.ldi(),
            0xA1: lambda: self.cpi(),
            0xA2: lambda: self.ini(),
            0xA3: lambda: self.outi(),
            0xA8: lambda: self.ldd(),
            0xA9: lambda: self.cpd(),
            0xAA: lambda: self.ind(),
            0xAB: lambda: self.outd(),
            0xB0: lambda: self.ldir(),
            0xB1: lambda: self.cpir(),
            0xB2: lambda: self.inir(),
            0xB3: lambda: self.otir(),
            0xB8: lambda: self.lddr(),
            0xB9: lambda: self.cpdr(),
            0xBA: lambda: self.indr(),
            0xBB: lambda: self.otdr(),
        }
        if opcode in ed_instructions:
            ed_instructions[opcode]()
        else:
            raise ValueError(f"Unknown ED-prefixed opcode: {opcode:02X}")

