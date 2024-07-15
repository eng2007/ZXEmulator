from ext_cpu import extCPUClass
from z80_asm import z80_to_asm
import logging

class Z80(extCPUClass):
    def __init__(self, memory, io_controller, start_addr=0x0000):
        super().__init__()
        self.instructions = self.create_instruction_table()

        # Память на 128KB (банки памяти ZX Spectrum 128)
        #self.memory = [0] * 128 * 1024  # 128KB памяти
        #self.memory = memory.memory
        self.memory = memory
        self.mem_class = memory
        self.io_controller = io_controller

    def execute_instruction(self, debug = False):
        opcode = self.fetch()

        if debug:
            logging.info('#')
            logging.info(f"{self.registers['PC']-1:04X}: {z80_to_asm[opcode]}")
            logging.info(f"opcode: {opcode:02X}")

            print('#')
            print(f"{self.registers['PC']-1:04X}: {z80_to_asm[opcode]}")
            print(f"opcode: {opcode:02X}")

        if opcode in self.instructions:
            self.instructions[opcode]()
        else:
            raise ValueError(f"Unknown opcode: {opcode:02X}")

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
            0x2A: lambda: self.load_register_pair('HL', self.load_word(self.fetch_word())),
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

            0xE2: lambda: self.jp_cc('PO', self.fetch_word()),  # JP PO, nn
            0xEA: lambda: self.jp_cc('PE', self.fetch_word()),  # JP PE, nn
            0xF2: lambda: self.jp_cc('P', self.fetch_word()),   # JP P, nn
            0xFA: lambda: self.jp_cc('M', self.fetch_word()),   # JP M, nn

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

            0xE4: lambda: self.call_cc('PO', self.fetch_word()),  # CALL PO, nn
            0xEC: lambda: self.call_cc('PE', self.fetch_word()),  # CALL PE, nn
            0xF4: lambda: self.call_cc('P', self.fetch_word()),   # CALL P, nn
            0xFC: lambda: self.call_cc('M', self.fetch_word()),   # CALL M, nn

            0xC9: lambda: self.ret(),
            0xC0: lambda: self.ret_cc('NZ'),
            0xC8: lambda: self.ret_cc('Z'),
            0xD0: lambda: self.ret_cc('NC'),
            0xD8: lambda: self.ret_cc('C'),
            0xE0: lambda: self.ret_cc('PO'),  # RET PO
            0xE8: lambda: self.ret_cc('PE'),  # RET PE
            0xF0: lambda: self.ret_cc('P'),  # RET P
            0xF8: lambda: self.ret_cc('M'),  # RET M
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

    def daa(self):
        """
        Decimal Adjust Accumulator.
        Adjusts the accumulator for BCD (Binary Coded Decimal) arithmetic.
        """
        a = self.registers['A']
        cf = self.get_flag('C')
        hf = self.get_flag('H')

        if not self.get_flag('N'):
            if cf or a > 0x99:
                a += 0x60
                self.set_flag('C', 1)
            if hf or (a & 0x0F) > 0x09:
                a += 0x06
        else:
            if cf:
                a -= 0x60
            if hf:
                a -= 0x06

        self.registers['A'] = a & 0xFF
        self.set_flag('S', a & 0x80)
        self.set_flag('Z', a == 0)
        self.set_flag('H', 0)
        self.set_flag('P/V', self.parity(a))

    def cpl(self):
        """
        Complement accumulator (A = ~A).
        """
        self.registers['A'] = (~self.registers['A']) & 0xFF
        self.set_flag('H', 1)
        self.set_flag('N', 1)
        # Установка флагов 3 и 5
        self.set_flag('3', self.registers['A'] & 0x08)
        self.set_flag('5', self.registers['A'] & 0x20)

    def ccf(self):
        """
        Complement carry flag.
        """
        self. set_flag('C', not self.get_flag('C'))
        self.set_flag('H', not self.get_flag('C'))
        self.set_flag('N', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', self.registers['A'] & 0x08)
        self.set_flag('5', self.registers['A'] & 0x20)

    def scf(self):
        """
        Set carry flag.
        """
        self.set_flag('C', 1)
        self.set_flag('H', 0)
        self.set_flag('N', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', self.registers['A'] & 0x08)
        self.set_flag('5', self.registers['A'] & 0x20)

    def nop(self):
        """
        No operation.
        """
        pass  # Ничего не делает

    def di(self):
        """
        Disable interrupts.
        """
        self.interrupts_enabled = False

    def ei(self):
        """
        Enable interrupts.
        """
        self.interrupts_enabled = True

    def in_a_n(self):
        """
        Ввод в аккумулятор (A) из порта, номер которого задан следующим байтом.
        Инструкция: IN A, (n)
        """
        port = self.fetch()  # Получаем номер порта из следующего байта
        #print(f"port {port:02X}")
        value = self.io_read(port)  # Читаем из порта
        #print(f"value {value:02X}")
        self.registers['A'] = value  # Сохраняем значение в аккумуляторе

        # Устанавливаем флаги
        #self.set_flag('S', value & 0x80)  # Знаковый флаг
        #self.set_flag('Z', value == 0)    # Флаг нуля
        #self.set_flag('H', 0)             # Сбрасываем флаг полупереноса
        #self.set_flag('P/V', self.parity(value))  # Флаг четности
        #self.set_flag('N', 0)             # Сбрасываем флаг вычитания

    def out_n_a(self):
        """
        Вывод содержимого аккумулятора (A) в порт, номер которого задан следующим байтом.
        Инструкция: OUT (n), A
        """
        port = self.fetch()  # Получаем номер порта из следующего байта
        self.io_write((self.registers['A'] << 8) | port, self.registers['A'])  # Записываем в порт

    def ld_i_a(self):
        """
        Загрузка значения из аккумулятора (A) в регистр прерываний (I).
        Инструкция: LD I, A
        """
        # Копируем значение из аккумулятора в регистр I
        self.registers['I'] = self.registers['A']

        # Эта инструкция не влияет на флаги