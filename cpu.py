import logging
from z80_asm import z80_to_asm

class Z80:
    def __init__(self, memory, io_controller, start_addr=0x0000):
        # Регистры процессора
        self.af = 0
        self.bc = 0
        self.de = 0
        self.hl = 0
        self.ix = 0
        self.iy = 0

        # Альтернативные регистры
        self.af_prime = 0
        self.bc_prime = 0
        self.de_prime = 0
        self.hl_prime = 0

        self.sp = 0
        self.pc = start_addr
        self.interrupts_enabled = False
        self.interrupt_mode = 0
        self.halted = False  # Состояние HALT

        # Регистр прерываний
        self.i = 0
        
        # Память на 128KB (банки памяти ZX Spectrum 128)
        #self.memory = [0] * 128 * 1024  # 128KB памяти
        self.memory = memory.memory
        self.mem_class = memory
        self.io_controller = io_controller
        
        # Флаги процессора
        self.sign_flag = False
        self.zero_flag = False
        self.f5_flag = False
        self.half_carry_flag = False
        self.f3_flag = False
        self.parity_overflow_flag = False        
        self.add_subtract_flag = False
        self.carry_flag = False
       
    def reset(self):
        # Сброс всех регистров и флагов
        self.af = self.bc = self.de = self.hl = 0
        self.ix = self.iy = self.sp = self.pc = 0
        self.interrupts_enabled = False
        self.af_prime = self.bc_prime = self.de_prime = self.hl_prime = 0

    def load_memory(self, address, data):
        # Загрузка данных в память по заданному адресу
        self.memory[address:address + len(data)] = data

    def fetch_byte(self, printLog = True):
        # Получение байта из текущего адреса PC
        byte = self.memory[self.pc]
        self.pc = (self.pc + 1) & 0xFFFF
        if printLog:
            logging.info(f"Byte: {byte:02X}")

        #альтернативный вариант в коде
        #n = memory[self.pc]
        #self.pc = (self.pc + 1) & 0xFFFF
        return byte

    def fetch_word(self):
        # Получение слова (2 байта) из текущего адреса PC
        low = self.fetch_byte(False)
        high = self.fetch_byte(False)
        word = (high << 8) | low
        logging.info(f"Word: {word:04X}")

        #альтернативный вариант в коде
        #n = self.memory[self.pc] + (self.memory[self.pc + 1] << 8)
        return word

    def flags_to_byte(self):
        return (
            (self.sign_flag << 7) |
            (self.zero_flag << 6) |
            (self.f5_flag << 5) |
            (self.half_carry_flag << 4) |
            (self.f3_flag << 3) |
            (self.parity_overflow_flag << 2) |
            (self.add_subtract_flag << 1) |
            self.carry_flag
        )        

    def set_byte_flags(self, value, subtract=False, carry=None, keepSign = False, keepZero = False,  keepHalf = False, keepParity = False, keepSub = False):
        # Установка флагов для результата операции
        #print(f"value: {value}")
        #print(f"value: {value & 0x0F}")    
        #a = (self.af >> 8) & 0xFF  
        #print(f"value {hex(value)}")  
        if not keepSign: self.sign_flag = (value & 0x80 != 0)
        if not keepZero: self.zero_flag = ((value & 0xFF) == 0)
        self.f5_flag = ((value & 0x20) != 0)      
        if not keepHalf: self.half_carry_flag = ((value & 0x10) != 0) if not subtract else (value & 0x0F) > 0
        self.f3_flag = ((value & 0x08) != 0)      
       
        if not keepParity: self.parity_overflow_flag = (bin(value).count('1') % 2 == 0)                 
        if not keepSub: self.add_subtract_flag = subtract
        if carry is not None:
            self.carry_flag = carry

        f = self.flags_to_byte()
        #print(f"f: {f}")
        self.af = (self.af & 0xFF00) | f

    def set_flags(self, value, subtract=False, carry=None, keepSign = False, keepZero = False,  keepHalf = False, keepParity = False, keepSub = False):
        # Установка флагов для результата операции
        #print(f"value: {value}")
        a = (self.af >> 8) & 0xFF
        #if not keepSign: self.sign_flag = (a & 0x80 != 0)
        if not keepZero: self.zero_flag = (value & 0xFFFF == 0)
        self.f5_flag = ((value & 0x20) != 0) 
        if not keepHalf: self.half_carry_flag = (value & 0x10 != 0) if not subtract else (value & 0xF) > 0
        self.f3_flag = ((value & 0x08) != 0) 
        if not keepParity: self.parity_overflow_flag = (bin(value).count('1') % 2 == 0)
        if not keepSub: self.add_subtract_flag = subtract
        if carry is not None:
            self.carry_flag = carry

        f = self.flags_to_byte()
        #print(f"f: {f}")
        self.af = (self.af & 0xFF00) | f        

    def get_register_value(self, reg_name):
        return getattr(self, reg_name)

    def set_register_value(self, reg_name, value):
        setattr(self, reg_name, value & 0xFFFF)

    def get_flag_value(self, flag_name):
        return getattr(self, flag_name)

    def set_flag_value(self, flag_name, value):
        setattr(self, flag_name, value)

    def update_flags_from_byte(self, value):
        self.sign_flag = (value & 0x80) != 0
        self.zero_flag = (value & 0x40) != 0
        self.half_carry_flag = (value & 0x10) != 0
        self.parity_overflow_flag = (value & 0x04) != 0        
        self.add_subtract_flag = (value & 0x02) != 0
        self.carry_flag = (value & 0x01) != 0

    #def handle_interrupt(self):
    #    if self.interrupts_enabled:
    #        self.interrupts_enabled = False  # Автоматическое отключение прерываний
            #self.memory.write(self.sp - 1, (self.pc >> 8) & 0xFF)
            #self.memory.write(self.sp - 2, self.pc & 0xFF)

    #        self.memory[self.sp - 1] = (self.pc >> 8) & 0xFF
    #        self.memory[self.sp - 2] = self.pc & 0xFF

    #        self.sp = (self.sp - 2) & 0xFFFF
    #        self.pc = 0x0038  # Адрес обработчика прерываний в ZX Spectrum   
    #    if self.halted:
    #        self.halted = False  # Выход из HALT
    #        print("Процессор возобновил выполнение после прерывания.")

    def handle_interrupt(self):
        if not self.interrupts_enabled:
            return
        
        if self.halted:
            self.halted = False  # Выход из HALT
            print("Процессор возобновил выполнение после прерывания.")

        self.interrupts_enabled = False

        self.sp = (self.sp - 1) & 0xFFFF
        self.memory[self.sp] = (self.pc >> 8) & 0xFF
        self.sp = (self.sp - 1) & 0xFFFF
        self.memory[self.sp] = self.pc & 0xFF

        if self.interrupt_mode == 0:
            self.pc = 0x0038
        elif self.interrupt_mode == 1:
            self.pc = 0x0038
        elif self.interrupt_mode == 2:
            vector = self.io_controller.get_data_bus_value()
            address = (self.i << 8) | vector
            self.pc = (self.memory[address + 1] << 8) | self.memory[address]   

        #print("Interrupt 38")         

    def handle_nmi(self):
        self.sp = (self.sp - 1) & 0xFFFF
        self.memory[self.sp] = (self.pc >> 8) & 0xFF
        self.sp = (self.sp - 1) & 0xFFFF
        self.memory[self.sp] = self.pc & 0xFF
        self.pc = 0x0066            

    def halt(self):
        """Выполняет команду HALT."""
        print("Выполнение HALT. Процессор остановлен.")
        self.halted = True  # Устанавливаем состояние HALT

    def execute_cb_instruction(self):
        opcode = self.fetch_byte(False)
        #print(f"CB prefix opcode {opcode}")
        register_lookup = [lambda: (self.bc >> 8) & 0xFF,
                           lambda: self.bc & 0xFF,
                           lambda: (self.de >> 8) & 0xFF,
                           lambda: self.de & 0xFF,
                           lambda: (self.hl >> 8) & 0xFF,
                           lambda: self.hl & 0xFF,
                           lambda: self.memory[self.hl],
                           lambda: (self.af >> 8) & 0xFF]

        update_register_lookup = [
            lambda val: self.set_register_value('bc', (self.bc & 0xFF) | (val << 8)),
            lambda val: self.set_register_value('bc', (self.bc & 0xFF00) | val),
            lambda val: self.set_register_value('de', (self.de & 0xFF) | (val << 8)),
            lambda val: self.set_register_value('de', (self.de & 0xFF00) | val),
            lambda val: self.set_register_value('hl', (self.hl & 0xFF) | (val << 8)),
            lambda val: self.set_register_value('hl', (self.hl & 0xFF00) | val),
            lambda val: self.mem_class.write(self.hl, val),  # (HL)
            lambda val: self.set_register_value('af', (self.af & 0xFF) | (val << 8))
        ]

        reg_index = opcode & 0x07
        operation = (opcode & 0xF8) >> 3
        reg_value = register_lookup[reg_index]()
        result = reg_value

        if operation == 0:  # RLC
            carry = (reg_value & 0x80) >> 7
            result = ((reg_value << 1) & 0xFF) | carry
        elif operation == 1:  # RRC
            carry = reg_value & 0x01
            result = (reg_value >> 1) | (carry << 7)
        elif operation == 2:  # RL
            carry = self.carry_flag
            new_carry = (reg_value & 0x80) >> 7
            result = ((reg_value << 1) & 0xFF) | carry
            carry = new_carry
        elif operation == 3:  # RR
            carry = self.carry_flag
            new_carry = reg_value & 0x01
            result = (reg_value >> 1) | (carry << 7)
            carry = new_carry
        elif operation == 4:  # SLA
            carry = (reg_value & 0x80) >> 7
            result = (reg_value << 1) & 0xFF
        elif operation == 5:  # SRA
            carry = reg_value & 0x01
            result = (reg_value >> 1) | (reg_value & 0x80)
        elif operation == 7:  # SRL
            carry = reg_value & 0x01
            result = reg_value >> 1
        elif operation >= 8 and operation <= 15:  # BIT, RES, SET
            bit = (operation - 8) >> 1
            if operation % 2 == 0:  # BIT
                self.zero_flag = (reg_value & (1 << bit)) == 0
                self.half_carry_flag = True
                self.add_subtract_flag = False
            elif operation % 2 == 1 and operation < 12:  # RES
                result = reg_value & ~(1 << bit)
            elif operation % 2 == 1 and operation >= 12:  # SET
                result = reg_value | (1 << bit)

        update_register_lookup[reg_index](result)
        #print(f"CB prefix, operation: {operation}")
        if operation < 8:  # Для вращений и сдвигов обновляем флаги
            self.set_flags(result, carry=carry)

    def execute_ddcb_prefix(self, cb_opcode, d):
        addr = self.ix + d
        value = self.memory[addr]
        carry = 0
        result = value

        operation = (cb_opcode & 0xF8) >> 3
        bit = (cb_opcode >> 3) & 0x07
        reg_index = cb_opcode & 0x07

        if operation == 0:  # RLC
            carry = (value & 0x80) >> 7
            result = ((value << 1) & 0xFF) | carry
        elif operation == 1:  # RRC
            carry = value & 0x01
            result = (value >> 1) | (carry << 7)
        elif operation == 2:  # RL
            carry = (value & 0x80) >> 7
            result = ((value << 1) & 0xFF) | (self.carry_flag & 1)
        elif operation == 3:  # RR
            carry = value & 0x01
            result = (value >> 1) | ((self.carry_flag & 1) << 7)
        elif operation == 4:  # SLA
            carry = (value & 0x80) >> 7
            result = (value << 1) & 0xFF
        elif operation == 5:  # SRA
            carry = value & 0x01
            result = (value >> 1) | (value & 0x80)
        elif operation == 6:  # SWAP (SRL)
            carry = value & 0x01
            result = value >> 1
        elif operation == 7:  # SRL
            carry = value & 0x01
            result = value >> 1

        if operation < 8:
            self.memory[addr] = result
            self.set_flags(result, carry=carry)
        elif 8 <= operation < 16:
            if cb_opcode & 0xC0 == 0x40:  # BIT
                self.zero_flag = (value & (1 << bit)) == 0
                self.half_carry_flag = True
                self.add_subtract_flag = False
            elif cb_opcode & 0xC0 == 0x80:  # RES
                self.memory[addr] = value & ~(1 << bit)
            elif cb_opcode & 0xC0 == 0xC0:  # SET
                self.memory[addr] = value | (1 << bit)


    def execute_dd_prefix(self, opcode):
        # Сначала нужно получить байт смещения
        
        
        # Декодируем операцию
        if opcode == 0x21:  # LD IX, nn
            low = self.fetch_byte()
            high = self.fetch_byte()
            self.ix = (high << 8) | low
        elif opcode == 0x22:  # LD (nn), IX
            low = self.fetch_byte()
            high = self.fetch_byte()
            addr = (high << 8) | low
            self.memory[addr] = self.ix & 0xFF
            self.memory[addr + 1] = (self.ix >> 8) & 0xFF
        elif opcode == 0x2A:  # LD IX, (nn)
            low = self.fetch_byte()
            high = self.fetch_byte()
            addr = (high << 8) | low
            self.ix = self.memory[addr] | (self.memory[addr + 1] << 8)
        elif opcode == 0x36:  # LD (IX+d), n
            d = self.fetch_byte()
            n = self.fetch_byte()
            self.memory[self.ix + d] = n
        elif opcode == 0x46:  # LD B, (IX+d)
            d = self.fetch_byte()
            self.bc = (self.bc & 0xFF) | (self.memory[self.ix + d] << 8)
        elif opcode == 0x4E:  # LD C, (IX+d)
            d = self.fetch_byte()
            self.bc = (self.bc & 0xFF00) | self.memory[self.ix + d]
        elif opcode == 0x56:  # LD D, (IX+d)
            d = self.fetch_byte()
            self.de = (self.de & 0xFF) | (self.memory[self.ix + d] << 8)
        elif opcode == 0x5E:  # LD E, (IX+d)
            d = self.fetch_byte()
            self.de = (self.de & 0xFF00) | self.memory[self.ix + d]
        elif opcode == 0x66:  # LD H, (IX+d)
            d = self.fetch_byte()
            self.hl = (self.hl & 0xFF) | (self.memory[self.ix + d] << 8)
        elif opcode == 0x6E:  # LD L, (IX+d)
            d = self.fetch_byte()
            self.hl = (self.hl & 0xFF00) | self.memory[self.ix + d]
        elif opcode == 0x7E:  # LD A, (IX+d)
            d = self.fetch_byte()
            self.af = (self.af & 0xFF) | (self.memory[self.ix + d] << 8)
        elif opcode == 0x77:  # LD (IX+d), A
            d = self.fetch_byte()
            self.memory[self.ix + d] = (self.af >> 8) & 0xFF
        elif opcode == 0x70:  # LD (IX+d), B
            d = self.fetch_byte()
            self.memory[self.ix + d] = (self.bc >> 8) & 0xFF
        elif opcode == 0x71:  # LD (IX+d), C
            d = self.fetch_byte()
            self.memory[self.ix + d] = self.bc & 0xFF
        elif opcode == 0x72:  # LD (IX+d), D
            d = self.fetch_byte()
            self.memory[self.ix + d] = (self.de >> 8) & 0xFF
        elif opcode == 0x73:  # LD (IX+d), E
            d = self.fetch_byte()
            self.memory[self.ix + d] = self.de & 0xFF
        elif opcode == 0x74:  # LD (IX+d), H
            d = self.fetch_byte()
            self.memory[self.ix + d] = (self.hl >> 8) & 0xFF
        elif opcode == 0x75:  # LD (IX+d), L
            d = self.fetch_byte()
            self.memory[self.ix + d] = self.hl & 0xFF
        elif opcode == 0x34:  # INC (IX+d)
            d = self.fetch_byte()
            addr = self.ix + d
            self.memory[addr] = (self.memory[addr] + 1) & 0xFF
            self.set_flags(self.memory[addr], subtract=False)
        elif opcode == 0x35:  # DEC (IX+d)
            d = self.fetch_byte()
            addr = self.ix + d
            self.memory[addr] = (self.memory[addr] - 1) & 0xFF
            self.set_flags(self.memory[addr], subtract=True)
        elif opcode == 0x09:  # ADD IX, BC
            self.ix = (self.ix + self.bc) & 0xFFFF
            self.set_flags(self.ix)
        elif opcode == 0x19:  # ADD IX, DE
            self.ix = (self.ix + self.de) & 0xFFFF
            self.set_flags(self.ix)
        elif opcode == 0x29:  # ADD IX, IX
            self.ix = (self.ix + self.ix) & 0xFFFF
            self.set_flags(self.ix)
        elif opcode == 0x39:  # ADD IX, SP
            self.ix = (self.ix + self.sp) & 0xFFFF
            self.set_flags(self.ix)
        elif opcode == 0xE1:  # POP IX
            self.ix = self.memory[self.sp] | (self.memory[self.sp + 1] << 8)
            self.sp += 2
        elif opcode == 0xE3:  # EX (SP), IX
            temp = self.ix
            self.ix = self.memory[self.sp] | (self.memory[self.sp + 1] << 8)
            self.memory[self.sp] = temp & 0xFF
            self.memory[self.sp + 1] = (temp >> 8) & 0xFF
        elif opcode == 0xE5:  # PUSH IX
            self.sp -= 2
            self.memory[self.sp] = self.ix & 0xFF
            self.memory[self.sp + 1] = (self.ix >> 8) & 0xFF
        elif opcode == 0xE9:  # JP (IX)
            self.pc = self.ix
        elif opcode == 0xF9:  # LD SP, IX
            self.sp = self.ix
        elif opcode == 0xCB:  # CB-prefixed instructions with IX
            d = self.fetch_byte()
            cb_opcode = self.fetch_byte()
            self.execute_ddcb_prefix(cb_opcode, d)
        else:
            print(f"IX prefix DD opcode: {opcode:02X} not supported")

    def execute_fdcb_prefix(self, cb_opcode, d):
        addr = self.iy + d
        value = self.memory[addr]
        carry = 0
        result = value

        operation = (cb_opcode & 0xF8) >> 3
        bit = (cb_opcode >> 3) & 0x07
        reg_index = cb_opcode & 0x07

        if operation == 0:  # RLC
            carry = (value & 0x80) >> 7
            result = ((value << 1) & 0xFF) | carry
        elif operation == 1:  # RRC
            carry = value & 0x01
            result = (value >> 1) | (carry << 7)
        elif operation == 2:  # RL
            carry = (value & 0x80) >> 7
            result = ((value << 1) & 0xFF) | (self.carry_flag & 1)
        elif operation == 3:  # RR
            carry = value & 0x01
            result = (value >> 1) | ((self.carry_flag & 1) << 7)
        elif operation == 4:  # SLA
            carry = (value & 0x80) >> 7
            result = (value << 1) & 0xFF
        elif operation == 5:  # SRA
            carry = value & 0x01
            result = (value >> 1) | (value & 0x80)
        elif operation == 6:  # SWAP (SRL)
            carry = value & 0x01
            result = value >> 1
        elif operation == 7:  # SRL
            carry = value & 0x01
            result = value >> 1

        if operation < 8:
            self.memory[addr] = result
            self.set_flags(result, carry=carry)
        elif 8 <= operation < 16:
            if cb_opcode & 0xC0 == 0x40:  # BIT
                self.zero_flag = (value & (1 << bit)) == 0
                self.half_carry_flag = True
                self.add_subtract_flag = False
            elif cb_opcode & 0xC0 == 0x80:  # RES
                self.memory[addr] = value & ~(1 << bit)
            elif cb_opcode & 0xC0 == 0xC0:  # SET
                self.memory[addr] = value | (1 << bit)


    def execute_fd_prefix(self, opcode):
        # Получаем байт смещения
        

        # Декодируем операцию
        if opcode == 0x21:  # LD IY, nn
            low = self.fetch_byte()
            high = self.fetch_byte()
            self.iy = (high << 8) | low
        elif opcode == 0x22:  # LD (nn), IY
            low = self.fetch_byte()
            high = self.fetch_byte()
            addr = (high << 8) | low
            self.memory[addr] = self.iy & 0xFF
            self.memory[addr + 1] = (self.iy >> 8) & 0xFF
        elif opcode == 0x2A:  # LD IY, (nn)
            low = self.fetch_byte()
            high = self.fetch_byte()
            addr = (high << 8) | low
            self.iy = self.memory[addr] | (self.memory[addr + 1] << 8)
        elif opcode == 0x36:  # LD (IY+d), n
            d = self.fetch_byte()
            n = self.fetch_byte()
            self.memory[self.iy + d] = n
        elif opcode == 0x46:  # LD B, (IY+d)
            d = self.fetch_byte()
            self.bc = (self.bc & 0xFF) | (self.memory[self.iy + d] << 8)
        elif opcode == 0x4E:  # LD C, (IY+d)
            d = self.fetch_byte()
            self.bc = (self.bc & 0xFF00) | self.memory[self.iy + d]
        elif opcode == 0x56:  # LD D, (IY+d)
            d = self.fetch_byte()
            self.de = (self.de & 0xFF) | (self.memory[self.iy + d] << 8)
        elif opcode == 0x5E:  # LD E, (IY+d)
            d = self.fetch_byte()
            self.de = (self.de & 0xFF00) | self.memory[self.iy + d]
        elif opcode == 0x66:  # LD H, (IY+d)
            d = self.fetch_byte()
            self.hl = (self.hl & 0xFF) | (self.memory[self.iy + d] << 8)
        elif opcode == 0x6E:  # LD L, (IY+d)
            d = self.fetch_byte()
            self.hl = (self.hl & 0xFF00) | self.memory[self.iy + d]
        elif opcode == 0x7E:  # LD A, (IY+d)
            d = self.fetch_byte()
            self.af = (self.af & 0xFF) | (self.memory[self.iy + d] << 8)
        elif opcode == 0x77:  # LD (IY+d), A
            d = self.fetch_byte()
            self.memory[self.iy + d] = (self.af >> 8) & 0xFF
        elif opcode == 0x70:  # LD (IY+d), B
            d = self.fetch_byte()
            self.memory[self.iy + d] = (self.bc >> 8) & 0xFF
        elif opcode == 0x71:  # LD (IY+d), C
            d = self.fetch_byte()
            self.memory[self.iy + d] = self.bc & 0xFF
        elif opcode == 0x72:  # LD (IY+d), D
            d = self.fetch_byte()
            self.memory[self.iy + d] = (self.de >> 8) & 0xFF
        elif opcode == 0x73:  # LD (IY+d), E
            d = self.fetch_byte()
            self.memory[self.iy + d] = self.de & 0xFF
        elif opcode == 0x74:  # LD (IY+d), H
            d = self.fetch_byte()
            self.memory[self.iy + d] = (self.hl >> 8) & 0xFF
        elif opcode == 0x75:  # LD (IY+d), L
            d = self.fetch_byte()
            self.memory[self.iy + d] = self.hl & 0xFF
        elif opcode == 0x34:  # INC (IY+d)
            d = self.fetch_byte()
            addr = self.iy + d
            self.memory[addr] = (self.memory[addr] + 1) & 0xFF
            self.set_flags(self.memory[addr], subtract=False)
        elif opcode == 0x35:  # DEC (IY+d)
            d = self.fetch_byte()
            addr = self.iy + d
            self.memory[addr] = (self.memory[addr] - 1) & 0xFF
            self.set_flags(self.memory[addr], subtract=True)
        elif opcode == 0x09:  # ADD IY, BC
            self.iy = (self.iy + self.bc) & 0xFFFF
            self.set_flags(self.iy)
        elif opcode == 0x19:  # ADD IY, DE
            self.iy = (self.iy + self.de) & 0xFFFF
            self.set_flags(self.iy)
        elif opcode == 0x29:  # ADD IY, IY
            self.iy = (self.iy + self.iy) & 0xFFFF
            self.set_flags(self.iy)
        elif opcode == 0x39:  # ADD IY, SP
            self.iy = (self.iy + self.sp) & 0xFFFF
            self.set_flags(self.iy)
        elif opcode == 0xE1:  # POP IY
            self.iy = self.memory[self.sp] | (self.memory[self.sp + 1] << 8)
            self.sp += 2
        elif opcode == 0xE3:  # EX (SP), IY
            temp = self.iy
            self.iy = self.memory[self.sp] | (self.memory[self.sp + 1] << 8)
            self.memory[self.sp] = temp & 0xFF
            self.memory[self.sp + 1] = (temp >> 8) & 0xFF
        elif opcode == 0xE5:  # PUSH IY
            self.sp -= 2
            self.memory[self.sp] = self.iy & 0xFF
            self.memory[self.sp + 1] = (self.iy >> 8) & 0xFF
        elif opcode == 0xF9:  # LD SP, IY
            self.sp = self.iy
        elif opcode == 0xCB:  # CB-prefixed instructions with IY
            d = self.fetch_byte()
            cb_opcode = self.fetch_byte()
            self.execute_fdcb_prefix(cb_opcode, d)
        else:
            print(f"IY prefix FD opcode: {opcode:02X} not supported")


    def execute_instruction_with_prefix(self, opcode, prefix):
        if prefix == 'IX': #opcode prefix #DD
            if opcode == 0x21:  # LD IX, nn
                low = self.fetch_byte()
                high = self.fetch_byte()
                self.ix = (high << 8) | low
            # Добавить больше инструкций для префикса IX здесь
            else: print(f"Ext.IX opcode: {opcode:02X}" + ' not supported')
        if prefix == 'IY': #opcode prefix #FD
            if opcode == 0x00:
                pass
            elif opcode == 0x21:  # LD IY,nn
                self.iy = self.fetch_word()
            elif opcode == 0x35:  # DEC (IY + d)
                d = self.fetch_byte()
                addr = self.iy + d
                value = self.memory[addr] - 1
                self.memory[addr] = value & 0xFF
                self.set_flags(value, subtract=True)
            elif opcode == 0x75:  # LD (IY+d), L
                displacement = self.fetch_byte()
                address = (self.iy + displacement) & 0xFFFF
                self.memory[address] = self.hl & 0xFF
            else: print(f"Ext.IY opcode: {opcode:02X}" + ' not supported')
        if prefix == 'ED': #opcode prefix #ED
            if   opcode == 0x43:  # LD (nn),BC
                nn = self.fetch_word()
                self.memory[nn] = (self.bc >> 8) & 0xFF
                self.memory[nn+1]  = (self.bc ) & 0xFF
            elif opcode == 0x45:  # RETN
                print('RETN')
            elif opcode == 0x46:  # IM 0
                self.interrupt_mode = 0                
            elif opcode == 0x47:  # LD I, A
                self.i = (self.af & 0xFF00) >> 8
            elif opcode == 0x4B:  # LD BC,(nn)
                nn = self.fetch_word()
                self.bc = self.memory[nn] + (self.memory[nn + 1] << 8)                
            elif opcode == 0x52:  # SBC HL,DE
                carry = 1 if self.carry_flag else 0
                result = self.hl - self.de - carry
                self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
            elif opcode == 0x53:  # LD (nn),DE
                nn = self.fetch_word()
                self.memory[nn] = (self.de >> 8) & 0xFF
                self.memory[nn+1]  = (self.de ) & 0xFF

            elif opcode == 0x56:  # IM 1
                self.interrupt_mode = 1
            elif opcode == 0x5B:  # LD DE,(nn)
                nn = self.fetch_word()
                self.de = self.memory[nn] + (self.memory[nn + 1] << 8)                

            elif opcode == 0x5E:  # IM 2
                self.interrupt_mode = 2

            elif opcode == 0x6B:  # LD HL,(nn)
                nn = self.fetch_word()
                self.hl = self.memory[nn] + (self.memory[nn + 1] << 8) 

            elif opcode == 0x73:  # LD (nn),SP
                nn = self.fetch_word()
                self.memory[nn] = (self.sp >> 8) & 0xFF
                self.memory[nn+1]  = (self.sp ) & 0xFF

            elif opcode == 0x78:  # IN A, (bc)
                result = self.io_controller.read_port(self.bc)
                self.af = (result << 8) | (self.af & 0xFF)

            elif opcode == 0x7B:  # LD SP,(nn)
                nn = self.fetch_word()
                self.sp = self.memory[nn] + (self.memory[nn + 1] << 8)
            elif opcode == 0xB0:  # LDIR
                while self.bc != 0:
                    #Копирование данных из HL в DE
                    self.memory[self.de] = self.memory[self.hl]
                    #print(f"Копирование {hex(self.memory[self.hl])} из {hex(self.hl)} в {hex(self.de)}")

                    # Увеличение HL и DE, уменьшение BC
                    self.hl = (self.hl + 1) & 0xFFFF
                    self.de = (self.de + 1) & 0xFFFF
                    self.bc = (self.bc - 1) & 0xFFFF
                    # Обновление флага PV
                    self.parity_overflow_flag = 1 if self.bc != 0 else 0


            elif opcode == 0xB8:  # LDDR
                while self.bc != 0:
                    # Копирование данных из HL в DE
                    self.memory[self.de] = self.memory[self.hl]
                    #print(f"Копирование {hex(self.memory[self.HL])} из {hex(self.HL)} в {hex(self.DE)}")
                    # Уменьшение HL, DE, и BC
                    self.hl -= 1
                    self.de -= 1
                    self.bc -= 1
                    # Обновление флага PVF
                    self.parity_overflow_flag = 1 if self.bc != 0 else 0
                    #print(f"HL: {hex(self.HL)}, DE: {hex(self.DE)}, BC: {hex(self.BC)}, PVF: {self.PVF}")

            else: print(f"Ext.ED opcode: {opcode:02X}" + ' not supported')
        if prefix == 'CB': #opcode prefix #CB - bit operaions
            if opcode == 0x00: #RLC B
                b = (self.bc >> 8) & 0xFF
                # Сохраняем старший бит (бит с индексом 7)
                carry = (b & 0x80) >> 7
                # Сдвигаем байт влево на 1 позицию
                b <<= 1
                # Устанавливаем младший бит в значение старшего бита
                b |= carry
                # Обновляем флаги состояния
                # Флаг Zero (Z) устанавливается, если результат равен 0
                self.zero_flag = b == 0
                # Флаг Carry (C) устанавливается, если был перенос
                self.carry_flag = carry == 1

            # Пример: BIT 7, H (0x7C)
            elif opcode == 0x7C:  # BIT 7, H
                h = (self.hl >> 8) & 0xFF
                self.zero_flag = (h & 0x80) == 0
            else: print(f"Ext.CB opcode: {opcode:02X}" + ' not supported')

    def display_registers(self, screen, font, offset):
        x, y = 10, 10 + offset
        #for reg, value in self.registers.items():
        #    text = font.render(f"{reg}: {value:04X}", True, (255, 255, 255))
        #    screen.blit(text, (x, y))
        #    y += 20
        text = font.render(f"AF: {self.af:04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))
        y += 20
        text = font.render(f"BC: {self.bc:04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))        
        y += 20
        text = font.render(f"DE: {self.de:04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))
        y += 20
        text = font.render(f"HL: {self.hl:04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))        
        y += 20
        text = font.render(f"IX: {self.ix:04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))
        y += 20
        text = font.render(f"IY: {self.iy:04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))        
        y += 20
        text = font.render(f"PC: {self.pc:04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))
        y += 20
        text = font.render(f"SP: {self.sp:04X}", True, (255, 255, 255))
        screen.blit(text, (x, y)) 

        y += 20
        text = font.render(f"Interrupts enabled: {self.interrupts_enabled}", True, (255, 255, 255))
        screen.blit(text, (x, y)) 

        y += 20
        text = font.render(f"Interrupt mode: {self.interrupt_mode}", True, (255, 255, 255))
        screen.blit(text, (x, y)) 

    def execute_instruction(self):
        opcode = self.fetch_byte(False)

        #print(f"pc: {self.pc:04X}")
        #print(f"opcode: {opcode:02X}")
        #print(f"pc: {self.pc:04X} opcode: {opcode:02X}")
        # Простой вывод в лог
        logging.info('#')
        logging.info(f"{self.pc-1:04X}: {z80_to_asm[opcode]}")
        logging.info(f"opcode: {opcode:02X}")
        #logging.info(f"af: {self.af:04X}")
        #logging.info(f"bc: {self.bc:04X}")
        #logging.info(f"de: {self.de:04X}")
        #logging.info(f"hl: {self.hl:04X}")
        #logging.info(f"Zero flag: {self.zero_flag}")
        #logging.info(f"Sign flag: {self.sign_flag}")
        #logging.info(f"Parity overflow flag: {self.parity_overflow_flag}")
        #logging.info(f"Half carry flag: {self.half_carry_flag}")
        #logging.info(f"Add subtract flag: {self.add_subtract_flag}")
        #logging.info(f"Carry flag: {self.carry_flag}")


        if opcode == 0x00:  # NOP
            pass
        elif opcode == 0x01:  # LD BC,nn
            self.bc = self.fetch_word()
        elif opcode == 0x02:  # LD (BC),A
            self.memory[self.bc] = (self.af >> 8) & 0xFF
        elif opcode == 0x03:  # INC BC
            self.bc = (self.bc + 1) & 0xFFFF
        elif opcode == 0x04:  # INC B
            b = ((self.bc >> 8) + 1) & 0xFF
            self.bc = (self.bc & 0xFF) | (b << 8)
            self.set_byte_flags(b, subtract=False)
        elif opcode == 0x05:  # DEC B
            b = ((self.bc >> 8) - 1) & 0xFF
            self.bc = (self.bc & 0xFF) | (b << 8)
            self.set_byte_flags(b, subtract=True)
        elif opcode == 0x06:  # LD B,n
            self.bc = (self.bc & 0xFF) | (self.fetch_byte() << 8)  
        elif opcode == 0x07:  # RLCA
            a = (self.af >> 8) & 0xFF
            carry = (a & 0x80) >> 7  # Сохранение старшего бита
            a = ((a << 1) | carry) & 0xFF  # Сдвиг влево и установка младшего бита в значение старшего
            self.af = (self.af & 0xFF) | (a << 8)  # Запись нового значения в A
            self.set_byte_flags(a, carry=carry, keepZero = True, keepParity = True)  # Обновление флагов
            #self.add_subtract_flag = False  # RLCA не изменяет флаг вычитания
            #self.half_carry_flag = False  # RLCA не изменяет флаг полупереноса
            # Знак, нуль и парность не изменяются для RLCA

        elif opcode == 0x08:  # EX AF, AF'
            self.af, self.af_prime = self.af_prime, self.af  
        elif opcode == 0x09:  # ADD HL,BC
            hl = self.hl + self.bc
            self.set_flags(hl, carry=hl > 0xFFFF, keepParity=True)
            self.hl = hl & 0xFFFF
        elif opcode == 0x0A:  # LD A,(BC)
            self.af = (self.af & 0xFF) | (self.memory[self.bc] << 8)
        elif opcode == 0x0B:  # DEC BC
            self.bc = (self.bc - 1) & 0xFFFF
        elif opcode == 0x0C:  # INC C
            c = (self.bc & 0xFF) + 1
            self.bc = (self.bc & 0xFF00) | (c & 0xFF)
            self.set_byte_flags(c, subtract=False)
        elif opcode == 0x0D:  # DEC C
            c = (self.bc & 0xFF) - 1
            self.bc = (self.bc & 0xFF00) | (c & 0xFF)
            self.set_byte_flags(c, subtract=True)
        elif opcode == 0x0E:  # LD C,n
            self.bc = (self.bc & 0xFF00) | self.fetch_byte()
        elif opcode == 0x0F:  # RRCA
            a = (self.af >> 8) & 0xFF
            carry = a & 1
            a = (a >> 1) | (carry << 7)
            self.af = (self.af & 0xFF) | (a << 8)
            self.set_byte_flags(a, carry=carry, keepZero=True, keepParity=True)

        elif opcode == 0x10:  # DJNZ e
            e = self.fetch_byte()
            b = ((self.bc >> 8) - 1) & 0xFF
            self.bc = (b << 8) | (self.bc & 0xFF)
            if b != 0:
                self.pc = (self.pc + ((e - 256) if e > 127 else e)) & 0xFFFF
        elif opcode == 0x11:  # LD DE,nn
            self.de = self.fetch_word()
        elif opcode == 0x12:  # LD (DE),A
            self.memory[self.de] = (self.af >> 8) & 0xFF
        elif opcode == 0x13:  # INC DE
            self.de = (self.de + 1) & 0xFFFF
        elif opcode == 0x14:  # INC D
            d = (self.de >> 8) + 1
            self.de = (self.de & 0xFF) | ((d & 0xFF) << 8)
            self.set_byte_flags(d, subtract=False)
        elif opcode == 0x15:  # DEC D
            d = (self.de >> 8) - 1
            self.de = (self.de & 0xFF) | ((d & 0xFF) << 8)
            self.set_byte_flags(d, subtract=True)
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
            self.pc = (self.pc + ((offset - 256) if offset > 127 else offset)) & 0xFFFF
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
            self.set_byte_flags(e, subtract=False)
        elif opcode == 0x1D:  # DEC E
            e = (self.de & 0xFF) - 1
            self.de = (self.de & 0xFF00) | (e & 0xFF)
            self.set_byte_flags(e, subtract=True)
        elif opcode == 0x1E:  # LD E,n
            self.de = (self.de & 0xFF00) | self.fetch_byte()
        elif opcode == 0x1F:  # RRA
            a = (self.af >> 8) & 0xFF
            carry = self.carry_flag
            self.carry_flag = a & 1
            a = (a >> 1) | (carry << 7)
            self.af = (self.af & 0xFF) | (a << 8)
            self.set_flags(a)
        elif opcode == 0x20:  # JR NZ, e
            e = self.fetch_byte()
            # Приведение смещения e к signed byte
            if e > 127: e -= 256
            if not self.zero_flag:
                self.pc = (self.pc + e) & 0xFFFF            
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
            self.set_byte_flags(h, subtract=False)
        elif opcode == 0x25:  # DEC H
            h = (self.hl >> 8) - 1
            self.hl = (self.hl & 0xFF) | ((h & 0xFF) << 8)
            self.set_byte_flags(h, subtract=True)
        elif opcode == 0x26:  # LD H,n
            self.hl = (self.hl & 0xFF) | (self.fetch_byte() << 8)
        elif opcode == 0x27:  # DAA
            a = (self.af >> 8) & 0xFF
            if not self.add_subtract_flag:
                if self.carry_flag or a > 0x99:
                    a = a + 0x60
                if self.half_carry_flag or (a & 0x0F) > 0x09:
                    a = a + 0x06
            else:
                if self.carry_flag:
                    a = (a - 0x60) & 0xFF
                if self.half_carry_flag:
                    a = (a - 0x06) & 0xFF
            self.af = (self.af & 0xFF) | (a << 8)
            self.set_flags(a, keepCarry=True, keepAddSubtract=True)
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
            self.set_byte_flags(l, subtract=False)
        elif opcode == 0x2D:  # DEC L
            l = (self.hl & 0xFF) - 1
            self.hl = (self.hl & 0xFF00) | (l & 0xFF)
            self.set_byte_flags(l, subtract=True)
        elif opcode == 0x2E:  # LD L,n
            self.hl = (self.hl & 0xFF00) | self.fetch_byte()
        elif opcode == 0x2F:  # CPL
            a = (self.af >> 8) & 0xFF
            a = a ^ 0xFF
            self.af = (self.af & 0xFF) | (a << 8)
            self.add_subtract_flag = True
            self.half_carry_flag = True
        elif opcode == 0x30:  # JR NC, e
            offset = self.memory[self.pc]
            self.pc = (self.pc + 1) & 0xFFFF
            if not self.carry_flag:
                self.pc = (self.pc + (offset if offset < 0x80 else offset - 256)) & 0xFFFF            
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
        elif opcode == 0x48:  # LD C, B
            b = (self.bc >> 8) & 0xFF
            self.bc = (self.bc & 0xFF00) | b
        elif opcode == 0x49:  # LD C, C
            c = self.bc & 0xFF
            self.bc = (self.bc & 0xFF00) | c 
        elif opcode == 0x4A:  # LD C, D
            d = (self.de >> 8) & 0xFF
            self.bc = (self.bc & 0xFF00) | d
        elif opcode == 0x4B:  # LD C, E
            e = (self.de) & 0xFF
            self.bc = (self.bc & 0xFF00) | e
        elif opcode == 0x4C:  # LD C, H
            h = (self.hl >> 8) & 0xFF
            self.bc = (self.bc & 0xFF00) | h
        elif opcode == 0x4D:  # LD C, L
            l = self.hl & 0xFF
            self.bc = (self.bc & 0xFF00) | l
        elif opcode == 0x4E:  # LD C, (HL)
            hl = self.hl
            self.bc = (self.bc & 0xFF00) | self.memory[hl]            
        elif opcode == 0x4F:  # LD C, A
            a = (self.af >> 8) & 0xFF
            self.bc = (self.bc & 0xFF00) | a  
        elif opcode == 0x51:  # LD D, C
            c = self.bc & 0xFF
            self.de = (self.de & 0xFF00) | c 
        elif opcode == 0x52:  # LD D, D
            # Ничего не делает, так как это просто копирование самого себя.
            pass                     
        elif opcode == 0x53:  # LD D, E
            e = self.de & 0xFF
            self.de = (e << 8) | e
        elif opcode == 0x54:  # LD D, H
            h = (self.hl >> 8) & 0xFF
            self.de = (self.de & 0x00FF) | (h << 8)
        elif opcode == 0x55:  # LD D, L
            l = (self.hl) & 0xFF
            self.de = (self.de & 0x00FF) | (l << 8)
        elif opcode == 0x56:  # LD D, (HL)
            result = self.memory[self.hl]
            self.de = (self.de & 0x00FF) | (result << 8)

        elif opcode == 0x57:  # LD D, A
            a = (self.af >> 8) & 0xFF
            self.de = (self.de & 0xFF00) | (a << 8)    

        elif opcode == 0x58:  # LD E, B
            b = (self.bc >> 8) & 0xFF
            self.de = (self.de & 0xFF00) | b  
        elif opcode == 0x59:  # LD E, C
            c = (self.bc) & 0xFF
            self.de = (self.de & 0xFF00) | c  
        elif opcode == 0x5A:  # LD E, D
            d = (self.de >> 8) & 0xFF
            self.de = (self.de & 0xFF00) | d
        elif opcode == 0x5B:  # LD E, E
            pass
        elif opcode == 0x5C:  # LD E, H
            h = (self.hl >> 8) & 0xFF
            self.de = (self.de & 0xFF00) | h
        elif opcode == 0x5D:  # LD E, L
            self.set_register_value('de', (self.get_register_value('de') & 0xFF00) | (self.get_register_value('hl') & 0x00FF))
        elif opcode == 0x5E:  # LD E, (HL)
            hl = self.hl
            self.de = (self.de & 0xFF00) | self.memory[hl]             
        elif opcode == 0x5F:  # LD E, A
            a = (self.af >> 8) & 0xFF
            self.de = (self.de & 0xFF00) | a  


        elif opcode == 0x60:  # LD H, B
            b = (self.bc >> 8) & 0xFF
            self.hl = (self.hl & 0x00FF) | (b << 8)            
        elif opcode == 0x61:  # LD H, C
            c = (self.bc) & 0xFF
            self.hl = (self.hl & 0x00FF) | (c << 8)


        elif opcode == 0x62:  # LD H, D
            d = (self.de >> 8) & 0xFF
            self.hl = (self.hl & 0x00FF) | (d << 8)
        elif opcode == 0x63:  # LD H, E
            e = (self.de) & 0xFF
            self.hl = (self.hl & 0x00FF) | (e << 8)

        elif opcode == 0x64:  # LD H, H
            pass           
        elif opcode == 0x65:  # LD H, L
            l = (self.hl ) & 0xFF
            self.hl = (self.hl & 0xFF00) | (l << 8)

        elif opcode == 0x66:  # LD H, (HL)
            self.set_register_value('hl', (self.memory[self.get_register_value('hl')] << 8) | (self.get_register_value('hl') & 0x00FF))
        elif opcode == 0x67:  # LD H, A
            a = (self.af >> 8) & 0xFF
            self.hl = (self.hl & 0x00FF) | (a << 8)

        elif opcode == 0x68:  # LD L, B
            b = (self.bc >> 8) & 0xFF
            self.hl = (self.hl & 0xFF00) | b   


        elif opcode == 0x6B:  # LD L, E
            e = self.de & 0xFF
            self.hl = (self.hl & 0xFF00) | e                             
        elif opcode == 0x6F:  # LD L, A
            a = (self.af >> 8) & 0xFF
            self.hl = (self.hl & 0xFF00) | a
        elif opcode == 0x6E:  # LD L, (HL)
            hl = self.hl
            l = self.memory[hl]
            self.hl = (self.hl & 0xFF00) | l
        elif opcode == 0x70:  # LD (HL), B
            b = (self.bc >> 8) & 0xFF
            self.memory[self.hl] = b 
        elif opcode == 0x71:  # LD (HL), C
            c = self.bc & 0xFF
            self.memory[self.hl] = c          
        elif opcode == 0x72:  # LD (HL), D
            d = (self.de >> 8) & 0xFF
            self.memory[self.hl] = d
        elif opcode == 0x73:  # LD (HL), E
            e = self.de & 0xFF
            self.memory[self.hl] = e
        elif opcode == 0x74:  # LD (HL), H
            h = (self.hl >> 8) & 0xFF
            self.memory[self.hl] = h
        elif opcode == 0x75:  # LD (HL), L
            l = self.hl & 0xFF
            self.memory[self.hl] = l

        elif opcode == 0x76:  # HALT
            self.halt()

        elif opcode == 0x77:  # LD (HL), A
            a = (self.af >> 8) & 0xFF
            self.memory[self.hl] = a            
        elif opcode == 0x78:  # LD A, B
            b = (self.bc >> 8) & 0xFF
            self.af = (b << 8) | (self.af & 0xFF)   
        elif opcode == 0x79:  # LD A, C
            c = (self.bc) & 0xFF
            self.af = (c << 8) | (self.af & 0xFF)       
        elif opcode == 0x7A:  # LD A, D
            d = (self.de >> 8) & 0xFF
            self.af = (d << 8) | (self.af & 0xFF) 
        elif opcode == 0x7B:  # LD A, E
            e = (self.de) & 0xFF
            self.af = (e << 8) | (self.af & 0xFF)             
        elif opcode == 0x7C:  # LD A, H
            a = (self.af >> 8) & 0xFF
            h = (self.hl >> 8) & 0xFF
            self.af = (h << 8) | (self.af & 0xFF)
        elif opcode == 0x7D:  # LD A, L
            l = (self.hl) & 0xFF
            self.af = (l << 8) | (self.af & 0xFF)

        elif opcode == 0x7E:  # LD A, (HL)
            hl = self.hl
            a = self.memory[hl]
            self.af = (a << 8) | (self.af & 0xFF)  
        elif opcode == 0x7F:  # LD A, A
            # Ничего не делает, так как это просто копирование самого себя.
            pass 
        elif opcode == 0x80:  # ADD A, B
            a = (self.af >> 8) & 0xFF
            b = (self.bc >> 8) & 0xFF
            result = a + b
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)
        elif opcode == 0x81:  # ADD A, C
            a = (self.af >> 8) & 0xFF
            c = (self.bc) & 0xFF
            result = a + c
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)

        elif opcode == 0x82:  # ADD A, D
            a = (self.af >> 8) & 0xFF
            d = (self.de >> 8) & 0xFF
            result = a + d
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)
        elif opcode == 0x83:  # ADD A, E
            a = (self.af >> 8) & 0xFF
            e = (self.de) & 0xFF
            result = a + e
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)

        elif opcode == 0x84:  # ADD A, H
            a = (self.af >> 8) & 0xFF
            h = (self.hl >> 8) & 0xFF
            result = a + h
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)
        elif opcode == 0x85:  # ADD A, L
            a = (self.af >> 8) & 0xFF
            l = (self.hl) & 0xFF
            result = a + l
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)

        elif opcode == 0x86:  # ADD A, (HL)
            a = (self.af >> 8) & 0xFF
            value = self.memory[self.hl]
            result = a + value
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)
        elif opcode == 0x87:  # ADD A, A
            a = (self.af >> 8) & 0xFF
            result = a + a
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)

        elif opcode == 0x88:  # ADC A, B
            a = (self.af >> 8) & 0xFF
            b = (self.bc >> 8) & 0xFF
            carry = 1 if self.carry_flag else 0
            result = a + b + carry
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)
        elif opcode == 0x89:  # ADC A, C
            a = (self.af >> 8) & 0xFF
            c = (self.bc) & 0xFF
            carry = 1 if self.carry_flag else 0
            result = a + c + carry
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)

        elif opcode == 0x8A:  # ADC A, D
            a = (self.af >> 8) & 0xFF
            d = (self.de >> 8) & 0xFF
            carry = 1 if self.carry_flag else 0
            result = a + d + carry
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)
        elif opcode == 0x8B:  # ADC A, E
            a = (self.af >> 8) & 0xFF
            e = (self.de) & 0xFF
            carry = 1 if self.carry_flag else 0
            result = a + e + carry
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)

        elif opcode == 0x8C:  # ADC A, H
            a = (self.af >> 8) & 0xFF
            h = (self.hl >> 8) & 0xFF
            carry = 1 if self.carry_flag else 0
            result = a + h + carry
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)
        elif opcode == 0x8D:  # ADC A, L
            a = (self.af >> 8) & 0xFF
            l = (self.hl) & 0xFF
            carry = 1 if self.carry_flag else 0
            result = a + l + carry
            self.set_flags(result & 0xFF, subtract=False, carry=(result > 0xFF))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)

        elif opcode == 0x8E:  # ADC A, (hl)
            a = (self.af >> 8) & 0xFF
            n = self.memory[self.hl]
            result = a + n + self.carry_flag
            self.carry_flag = (result > 0xFF)
            result &= 0xFF
            self.zero_flag = (result == 0)
            self.af = (result << 8) | (self.af & 0xFF)

        elif opcode == 0x90:  # SUB B
            a = (self.af >> 8) & 0xFF
            b = (self.bc >> 8) & 0xFF
            result = a - b
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)

        elif opcode == 0x91:  # SUB C
            a = (self.af >> 8) & 0xFF
            c = self.bc & 0xFF
            result = a - c
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)    
        elif opcode == 0x92:  # SUB D
            result = (self.get_register_value('af') >> 8) - (self.get_register_value('de') >> 8)
            self.set_flags(result, subtract=True, carry=(result < 0))
            self.set_register_value('af', (result & 0xFF) << 8 | (self.get_register_value('af') & 0x00FF))                 
        elif opcode == 0x95:  # SUB L
            a = (self.af >> 8) & 0xFF
            l = self.hl & 0xFF
            result = a - l
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)
        elif opcode == 0x98:  # SBC B
            a = (self.af >> 8) & 0xFF
            b = (self.bc >> 8) & 0xFF
            carry = 1 if self.carry_flag else 0
            result = a - b - carry
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
        elif opcode == 0x99:  # SBC C
            a = (self.af >> 8) & 0xFF
            c = self.bc & 0xFF
            carry = 1 if self.carry_flag else 0
            result = a - c - carry
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)  


        elif opcode == 0x9A:  # SBC D
            a = (self.af >> 8) & 0xFF
            d = (self.de >> 8) & 0xFF
            carry = 1 if self.carry_flag else 0
            result = a - d - carry
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
        elif opcode == 0x9B:  # SBC E
            a = (self.af >> 8) & 0xFF
            e = self.de & 0xFF
            carry = 1 if self.carry_flag else 0
            result = a - e - carry
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF) 


        elif opcode == 0x9C:  # SBC H
            a = (self.af >> 8) & 0xFF
            h = (self.hl >> 8) & 0xFF
            carry = 1 if self.carry_flag else 0
            result = a - h - carry
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
        elif opcode == 0x9D:  # SBC L
            a = (self.af >> 8) & 0xFF
            l = self.hl & 0xFF
            carry = 1 if self.carry_flag else 0
            result = a - l - carry
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF) 

        elif opcode == 0x9E:  # SBC (HL)
            a = (self.af >> 8) & 0xFF
            value = self.memory[self.hl]
            carry = 1 if self.carry_flag else 0
            result = a - value - carry
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF) 
        elif opcode == 0x9F:  # SBC A
            a = (self.af >> 8) & 0xFF
            carry = 1 if self.carry_flag else 0
            result = a - a - carry
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)             

        elif opcode == 0xA0:  # AND A, B
            a = (self.af >> 8) & 0xFF
            b = (self.bc >> 8) & 0xFF
            result = a & b
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)
        elif opcode == 0xA1:  # AND A, C
            a = (self.af >> 8) & 0xFF
            c = self.bc & 0xFF
            result = a & c
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)

        elif opcode == 0xA2:  # AND A, D
            a = (self.af >> 8) & 0xFF
            d = (self.de >> 8) & 0xFF
            result = a & d
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)
        elif opcode == 0xA3:  # AND A, E
            a = (self.af >> 8) & 0xFF
            e = self.de & 0xFF
            result = a & e
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)

        elif opcode == 0xA4:  # AND A, H
            a = (self.af >> 8) & 0xFF
            h = (self.hl >> 8) & 0xFF
            result = a & h
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)
        elif opcode == 0xA5:  # AND A, L
            a = (self.af >> 8) & 0xFF
            l = self.hl & 0xFF
            result = a & l
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)

        elif opcode == 0xA6:  # AND A, (HL)
            a = (self.af >> 8) & 0xFF
            value = value = self.memory[self.hl]
            result = a & value
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)

        elif opcode == 0xA7:  # AND A
            a = (self.af >> 8) & 0xFF
            result = a & a
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)

        elif opcode == 0xA8:  # XOR A, B
            a = (self.af >> 8) & 0xFF
            b = (self.bc >> 8) & 0xFF
            result = a ^ b
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF) 
        elif opcode == 0xA9:  # XOR A, C
            a = (self.af >> 8) & 0xFF
            c = self.bc & 0xFF
            result = a ^ c
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF) 

        elif opcode == 0xAA:  # XOR A, D
            a = (self.af >> 8) & 0xFF
            d = (self.de >> 8) & 0xFF
            result = a ^ d
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF) 
        elif opcode == 0xAB:  # XOR A, E
            a = (self.af >> 8) & 0xFF
            e = self.de & 0xFF
            result = a ^ e
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF) 

        elif opcode == 0xAC:  # XOR A, H
            a = (self.af >> 8) & 0xFF
            h = (self.hl >> 8) & 0xFF
            result = a ^ h
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF) 
        elif opcode == 0xAD:  # XOR A, L
            a = (self.af >> 8) & 0xFF
            l = self.hl & 0xFF
            result = a ^ l
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF) 

        elif opcode == 0xAE:  # XOR (HL)
            a = (self.af >> 8) & 0xFF
            value = self.memory[self.hl]
            result = a ^ value
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)                    
        elif opcode == 0xAF:  # XOR A
            a = (self.af >> 8) & 0xFF
            a ^= a
            self.af = (a << 8) | (self.af & 0xFF)
            self.zero_flag = (a == 0)
        elif opcode == 0xB0:  # OR B
            a = (self.af >> 8) & 0xFF
            b = (self.bc >> 8) & 0xFF
            a |= b
            self.af = (a << 8) | (self.af & 0xFF)
            self.zero_flag = (a == 0)
        elif opcode == 0xB1:  # OR C
            a = (self.af >> 8) & 0xFF
            c = self.bc & 0xFF
            a |= c
            self.af = (a << 8) | (self.af & 0xFF)
            self.zero_flag = (a == 0) 
        elif opcode == 0xB2:  # OR D
            a = (self.af >> 8) & 0xFF
            d = (self.de >> 8) & 0xFF
            a |= d
            self.af = (a << 8) | (self.af & 0xFF)
            self.zero_flag = (a == 0)
        elif opcode == 0xB3:  # OR E
            a = (self.af >> 8) & 0xFF
            e = self.de & 0xFF
            a |= e
            self.af = (a << 8) | (self.af & 0xFF)
            self.zero_flag = (a == 0)  
        elif opcode == 0xB4:  # OR H
            a = (self.af >> 8) & 0xFF
            h = (self.hl >> 8) & 0xFF
            a |= h
            self.af = (a << 8) | (self.af & 0xFF)
            self.zero_flag = (a == 0)
        elif opcode == 0xB5:  # OR L
            a = (self.af >> 8) & 0xFF
            l = self.hl & 0xFF
            a |= l
            self.af = (a << 8) | (self.af & 0xFF)
            self.zero_flag = (a == 0)   

        elif opcode == 0xB6:  # OR (HL)
            a = (self.af >> 8) & 0xFF
            value = self.memory[self.hl]
            a |= value
            self.af = (a << 8) | (self.af & 0xFF)
            self.zero_flag = (a == 0)      

        elif opcode == 0xB7:  # OR A
            a = (self.af >> 8) & 0xFF
            a |= a
            self.af = (a << 8) | (self.af & 0xFF)
            self.zero_flag = (a == 0)                      

        elif opcode == 0xB8:  # CP B
            a = (self.af >> 8) & 0xFF
            b = (self.bc >> 8) & 0xFF
            result = a - b
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
        elif opcode == 0xB9:  # CP C
            a = (self.af >> 8) & 0xFF
            c = (self.bc ) & 0xFF
            result = a - c
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))  

        elif opcode == 0xBA:  # CP D
            a = (self.af >> 8) & 0xFF
            d = (self.de >> 8) & 0xFF
            result = a - d
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
        elif opcode == 0xBB:  # CP E
            a = (self.af >> 8) & 0xFF
            e = (self.de ) & 0xFF
            result = a - e
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))  

        elif opcode == 0xBC:  # CP H
            a = (self.af >> 8) & 0xFF
            h = (self.hl >> 8) & 0xFF
            result = a - h
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))
        elif opcode == 0xBD:  # CP L
            a = (self.af >> 8) & 0xFF
            l = (self.hl ) & 0xFF
            result = a - l
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0))  

        elif opcode == 0xBE:  # CP (HL)
            a = (self.af >> 8) & 0xFF
            value = self.memory[self.hl]
            result = a - value
            self.set_flags(result & 0xFF, subtract=True, carry=(result < 0)) 


        elif opcode == 0xBF:  # CP A
            a = (self.af >> 8) & 0xFF
            result = a - a
            self.set_flags(a, subtract=True)
            #self.zero_flag = (result == 0)
            #self.sign_flag = (result & 0x80) != 0
            #self.parity_overflow_flag = bin(result).count("1") % 2 == 0
            #self.half_carry_flag = ((a & 0xF) - (a & 0xF)) < 0
            #self.add_subtract_flag = True
            #self.carry_flag = (a < a)     
        elif opcode == 0xC0:  # RET NZ
            if not self.zero_flag:
                lo = self.memory[self.sp]
                hi = self.memory[self.sp + 1]
                self.pc = (hi << 8) | lo
                self.sp = (self.sp + 2) & 0xFFFF                   
        elif opcode == 0xC1:  # POP BC
            lo = self.memory[self.sp]
            self.sp = (self.sp + 1) & 0xFFFF
            hi = self.memory[self.sp]
            self.sp = (self.sp + 1) & 0xFFFF
            self.bc = (hi << 8) | lo   
        elif opcode == 0xC2:  # JP NZ, nn
            nn = self.fetch_word()
            if not self.zero_flag:
                self.pc = nn          
        elif opcode == 0xC3:  # JP nn
            nn = self.fetch_word() 
            self.pc = nn
        elif opcode == 0xC4:  # CALL NZ, nn
            if not self.zero_flag:
                lo = self.memory[self.pc]
                hi = self.memory[self.pc + 1]
                nn = (hi << 8) | lo
                self.pc = (self.pc + 2) & 0xFFFF
                self.memory[self.sp - 1] = (self.pc >> 8)
                self.memory[self.sp - 2] = (self.pc & 0xFF)
                self.sp = (self.sp - 2) & 0xFFFF
                self.pc = nn            
        elif opcode == 0xC5:  # PUSH BC
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = (self.bc >> 8) & 0xFF
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = self.bc & 0xFF
        elif opcode == 0xC6:  # ADD A, n
            a = (self.af >> 8) & 0xFF
            n = self.fetch_byte()
            result = a + n
            self.af = (self.af & 0xFF) | ((result & 0xFF) << 8)
            self.set_flags(result, subtract=False, carry=(result > 0xFF))

        elif opcode == 0xC7:  # RST 00H
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = (self.pc >> 8) & 0xFF
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = self.pc & 0xFF
            self.pc = 0x00

        elif opcode == 0xC8:  # RET Z
            if self.zero_flag:
                lo = self.memory[self.sp]
                self.sp = (self.sp + 1) & 0xFFFF
                hi = self.memory[self.sp]
                self.sp = (self.sp + 1) & 0xFFFF
                self.pc = (hi << 8) | lo            
        elif opcode == 0xC9:  # RET
            lo = self.memory[self.sp]
            self.sp = (self.sp + 1) & 0xFFFF
            hi = self.memory[self.sp]
            self.sp = (self.sp + 1) & 0xFFFF
            self.pc = (hi << 8) | lo      
        elif opcode == 0xCA: #JP Z,(nn)
            nn = self.fetch_word
            if self.zero_flag:
                self.pc = nn
        elif opcode == 0xCB:  # Prefix CB (Bit operations)
            # Префикс для инструкций с использованием регистра CB
            #next_opcode = self.fetch_byte()
            #self.execute_instruction_with_prefix(next_opcode, 'CB')
            self.execute_cb_instruction()
            return  # Префикс изменяет поведение инструкции, преждевременный возврат
        elif opcode == 0xCC:  # CALL Z, nn
            nn = self.fetch_word()
            if self.zero_flag:
                self.sp = (self.sp - 2) & 0xFFFF
                self.memory[self.sp] = (self.pc & 0xFF)
                self.memory[self.sp + 1] = (self.pc >> 8)
                self.pc = nn

        elif opcode == 0xCD:  # CALL nn
            nn = self.fetch_word()
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = (self.pc >> 8) & 0xFF
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = self.pc & 0xFF
            self.pc = nn                
        elif opcode == 0xCE:  # ADC A, n
            a = (self.af >> 8) & 0xFF
            n = self.fetch_byte()
            result = a + n + self.carry_flag
            self.carry_flag = (result > 0xFF)
            result &= 0xFF
            self.zero_flag = (result == 0)
            self.af = (result << 8) | (self.af & 0xFF)
        elif opcode == 0xCF:  # RST 8H
            self.memory[self.sp - 1] = (self.pc >> 8)
            self.memory[self.sp - 2] = (self.pc & 0xFF)
            self.sp = (self.sp - 2) & 0xFFFF
            self.pc = 0x08
        elif opcode == 0xD0:  # RET NC
            if not self.carry_flag:
                lo = self.memory[self.sp]
                self.sp = (self.sp + 1) & 0xFFFF
                hi = self.memory[self.sp]
                self.sp = (self.sp + 1) & 0xFFFF
                self.pc = (hi << 8) | lo   
        elif opcode == 0xD1:  # POP DE
            lo = self.memory[self.sp]
            self.sp = (self.sp + 1) & 0xFFFF
            hi = self.memory[self.sp]
            self.sp = (self.sp + 1) & 0xFFFF
            self.de = (hi << 8) | lo       
        elif opcode == 0xD2:  # JP NC, nn
            nn = self.fetch_word()
            if not self.carry_flag:
                self.pc = nn                               
        elif opcode == 0xD3:  # OUT (n), A
            n = self.fetch_byte()
            a = (self.af >> 8) & 0xFF
            self.io_controller.write_port(n, a)          
        elif opcode == 0xD4:  # CALL NC, nn
            if not self.carry_flag:
                nn = fetch_word()
                self.sp = (self.sp - 1) & 0xFFFF
                self.memory[self.sp] = (self.pc >> 8) & 0xFF
                self.sp = (self.sp - 1) & 0xFFFF
                self.memory[self.sp] = self.pc & 0xFF
                self.pc = nn       
        elif opcode == 0xD5:  # PUSH DE
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = (self.de >> 8) & 0xFF
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = self.de & 0xFF 
        elif opcode == 0xD6:  # SUB n
            a = (self.af >> 8) & 0xFF
            n = self.fetch_byte()
            result = a - n
            self.af = (self.af & 0xFF) | ((result & 0xFF) << 8)
            # Обновление флагов
            self.set_flags(result, subtract=True, carry=(result < 0))
        elif opcode == 0xD7:  # RST 10H
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = (self.pc >> 8) & 0xFF
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = self.pc & 0xFF
            self.pc = 0x10

        elif opcode == 0xD8:  # RET C
            if self.carry_flag:
                lo = self.memory[self.sp]
                self.sp = (self.sp + 1) & 0xFFFF
                hi = self.memory[self.sp]
                self.sp = (self.sp + 1) & 0xFFFF
                self.pc = (hi << 8) | lo   
        elif opcode == 0xD9:  # EXX
            self.bc, self.bc_prime = self.bc_prime, self.bc
            self.de, self.de_prime = self.de_prime, self.de
            self.hl, self.hl_prime = self.hl_prime, self.hl
        elif opcode == 0xDA:  # JP C, nn
            nn = self.fetch_word()
            if self.carry_flag:
                self.pc = nn
        elif opcode == 0xDB:  # IN A, (n)
            n = self.fetch_byte()
            result = self.io_controller.read_port(n)
            self.af = (result << 8) | (self.af & 0xFF)
        elif opcode == 0xDC:  # CALL C, nn
            nn = self.fetch_word()
            if self.carry_flag:
                self.sp = (self.sp - 2) & 0xFFFF
                self.memory[self.sp] = (self.pc & 0xFF)
                self.memory[self.sp + 1] = (self.pc >> 8)
                self.pc = nn            
        elif opcode == 0xDD:  # Prefix for IX
            # Префикс для инструкций с использованием регистра IX
            next_opcode = self.fetch_byte()
            #self.execute_instruction_with_prefix(next_opcode, 'IX')
            self.execute_dd_prefix(next_opcode)
            return  # Префикс изменяет поведение инструкции, преждевременный возврат
        elif opcode == 0xDF:  # RST 18H
            self.memory[self.sp - 1] = (self.pc >> 8)
            self.memory[self.sp - 2] = (self.pc & 0xFF)
            self.sp = (self.sp - 2) & 0xFFFF
            self.pc = 0x18                     
        elif opcode == 0xE0:  # RET PO
            if not self.parity_overflow_flag:
                lo = self.memory[self.sp]
                hi = self.memory[self.sp + 1]
                self.sp = (self.sp + 2) & 0xFFFF
                self.pc = (hi << 8) | lo
        elif opcode == 0xE1:  # POP HL
            lo = self.memory[self.sp]
            self.sp = (self.sp + 1) & 0xFFFF
            hi = self.memory[self.sp]
            self.sp = (self.sp + 1) & 0xFFFF
            self.hl = (hi << 8) | lo 
        elif opcode == 0xE2:  # JP PO, nn
            nn = self.fetch_word()
            if not self.parity_overflow_flag:
                self.pc = nn
        elif opcode == 0xE3:  # EX (SP), HL
            # Чтение младшего и старшего байтов из памяти по адресу SP
            low = self.memory[self.sp]
            high = self.memory[self.sp + 1]
            # Формирование 16-битного значения из байтов
            memory_value = (high << 8) | low
            # Обмен значениями
            self.memory[self.sp] = self.hl & 0xFF              # Запись младшего байта HL
            self.memory[self.sp + 1] = (self.hl >> 8) & 0xFF  # Запись старшего байта HL
            self.hl = memory_value
        elif opcode == 0xE4:  # CALL PO, nn
            nn = self.fetch_word()
            if not self.parity_overflow_flag:
                self.sp = (self.sp - 2) & 0xFFFF
                self.memory[self.sp] = (self.pc & 0xFF)
                self.memory[self.sp + 1] = (self.pc >> 8)
                self.pc = nn
        elif opcode == 0xE5:  # PUSH HL
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = (self.hl >> 8) & 0xFF
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = self.hl & 0xFF 
        elif opcode == 0xE6:  # AND n
            n = self.memory[self.pc]
            self.pc = (self.pc + 1) & 0xFFFF
            a = (self.af >> 8) & 0xFF
            result = a & n
            self.set_flags(result & 0xFF, subtract=False, carry=False)
            self.af = (result << 8) | (self.af & 0xFF)
        elif opcode == 0xE7:  # RST 20H
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = (self.pc >> 8) & 0xFF
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = self.pc & 0xFF
            self.pc = 0x20 
        elif opcode == 0xE8:  # RET PE
            if self.parity_overflow_flag:
                lo = self.memory[self.sp]
                hi = self.memory[self.sp + 1]
                self.sp = (self.sp + 2) & 0xFFFF
                self.pc = (hi << 8) | lo
        elif opcode == 0xE9:  # JP (HL)
            self.pc = self.get_register_value('hl')
        elif opcode == 0xEA:  # JP PE, nn
            nn = self.fetch_word()
            if self.parity_overflow_flag:
                self.pc = nn
        elif opcode == 0xEB:  # EX DE, HL
            self.de, self.hl = self.hl, self.de
        elif opcode == 0xEC:  # CALL PE, nn
            nn = self.fetch_word()
            if self.parity_overflow_flag:
                self.sp = (self.sp - 2) & 0xFFFF
                self.memory[self.sp] = (self.pc & 0xFF)
                self.memory[self.sp + 1] = (self.pc >> 8)
                self.pc = nn

        elif opcode == 0xED:  # Prefix ED (Extended instructions)
            next_opcode = self.fetch_byte()
            self.execute_instruction_with_prefix(next_opcode, 'ED')
            return  # Префикс изменяет поведение инструкции, преждевременный возврат

        elif opcode == 0xEE:  # XOR A, n
            a = (self.af >> 8) & 0xFF
            n = self.fetch_byte()
            result = a ^ n
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF) 

        elif opcode == 0xEF:  # RST 28H
            self.memory[self.sp - 1] = (self.pc >> 8)
            self.memory[self.sp - 2] = (self.pc & 0xFF)
            self.sp = (self.sp - 2) & 0xFFFF
            self.pc = 0x28

        elif opcode == 0xF0:  # RET P
            if not self.sign_flag:
                lo = self.memory[self.sp]
                hi = self.memory[self.sp + 1]
                self.sp = (self.sp + 2) & 0xFFFF
                self.pc = (hi << 8) | lo

        elif opcode == 0xF1:  # POP AF
            f = self.memory[self.sp]
            self.sp = (self.sp + 1) & 0xFFFF
            a = self.memory[self.sp]
            self.sp = (self.sp + 1) & 0xFFFF
            self.af = (a << 8) | f
            self.update_flags_from_byte(f)   
        elif opcode == 0xF2:  # JP P, nn
            nn = self.fetch_word()
            if not self.sign_flag:
                self.pc = nn             
        elif opcode == 0xF3:  # DI
            self.interrupts_enabled = False
            #print('interrupts_disabled')
        elif opcode == 0xF4:  # CALL NC, nn
            nn = self.fetch_word()
            if not self.carry_flag:
                self.sp = (self.sp - 2) & 0xFFFF
                self.memory[self.sp] = (self.pc & 0xFF)
                self.memory[self.sp + 1] = (self.pc >> 8)
                self.pc = nn 
        elif opcode == 0xF5:  # PUSH AF
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = (self.af >> 8) & 0xFF
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = self.af & 0xFF  
        elif opcode == 0xF6:  # OR n
            a = (self.af >> 8) & 0xFF
            n = self.memory[self.pc]
            self.pc = (self.pc + 1) & 0xFFFF
            result = a | n
            self.set_flags(result & 0xFF, subtract=False, carry=None)
            self.af = ((result & 0xFF) << 8) | (self.af & 0xFF)     
        elif opcode == 0xF7:  # RST 30H
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = (self.pc >> 8) & 0xFF
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = self.pc & 0xFF
            self.pc = 0x30   
        elif opcode == 0xF8:  # RET M
            if self.sign_flag:
                lo = self.memory[self.sp]
                hi = self.memory[self.sp + 1]
                self.sp = (self.sp + 2) & 0xFFFF
                self.pc = (hi << 8) | lo
        elif opcode == 0xF9:  # LD SP, HL
            self.sp = self.hl
        elif opcode == 0xFA:  # JP M, nn
            nn = self.fetch_word()
            if self.sign_flag:
                self.pc = nn
        elif opcode == 0xFB:  # EI
            self.interrupts_enabled = True  
            #print('interrupts_enabled') 
        elif opcode == 0xFC:  # CALL M, nn
            nn = self.fetch_word()
            if self.sign_flag:
                self.sp = (self.sp - 2) & 0xFFFF
                self.memory[self.sp] = (self.pc & 0xFF)
                self.memory[self.sp + 1] = (self.pc >> 8)
                self.pc = nn         
        elif opcode == 0xFD:  # Prefix FD (IY instructions)
            #fd_opcode = self.memory[self.pc]
            #self.pc = (self.pc + 1) & 0xFFFF
            # Префикс для инструкций с использованием регистра IY
            next_opcode = self.fetch_byte()
            #self.execute_instruction_with_prefix(next_opcode, 'IY')
            self.execute_fd_prefix(next_opcode)
            return  # Префикс изменяет поведение инструкции, преждевременный возврат

        elif opcode == 0xFE:  # CP n
            a = (self.af >> 8) & 0xFF
            n = self.fetch_byte()
            self.zero_flag = (a == n)                
        elif opcode == 0xFF:  # RST 38H
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = (self.pc >> 8) & 0xFF
            self.sp = (self.sp - 1) & 0xFFFF
            self.memory[self.sp] = self.pc & 0xFF
            self.pc = 0x38                

        else: print(f"opcode: {opcode:02X}" + ' not supported')
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
