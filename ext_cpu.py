from base_cpu import baseCPUClass

class extCPUClass(baseCPUClass):
    def __init__(self):
        super().__init__()

    def jp(self, address):
        """
        Безусловный переход на указанный адрес.

        :param address: 16-битный адрес для перехода
        """
        self.registers['PC'] = address & 0xFFFF

    def jp_cc(self, condition, address):
        """
        Условный переход на указанный адрес.

        :param condition: строка, обозначающая условие ('NZ', 'Z', 'NC', 'C')
        :param address: 16-битный адрес для перехода
        """
        if self.check_condition(condition):
            self.registers['PC'] = address & 0xFFFF

    def jr(self, offset):
        """
        Относительный переход на указанное смещение.

        :param offset: 8-битное знаковое смещение (-128 до 127)
        """
        # Преобразуем смещение в знаковое число
        if offset > 127:
            offset -= 256
        #print('******************************************************************* JUMP ', offset)
        #print(f"B:{self.registers['B']}")
        self.registers['PC'] = (self.registers['PC'] + offset) & 0xFFFF

    def jr_cc(self, condition, offset):
        """
        Условный относительный переход на указанное смещение.

        :param condition: строка, обозначающая условие ('NZ', 'Z', 'NC', 'C')
        :param offset: 8-битное знаковое смещение (-128 до 127)
        """
        if self.check_condition(condition):
            self.jr(offset)

    def djnz(self, offset):
        """
        Декремент B и переход, если не ноль.

        :param offset: 8-битное знаковое смещение (-128 до 127)
        """
        self.registers['B'] = (self.registers['B'] - 1) & 0xFF
        if self.registers['B'] != 0:
            self.jr(offset)

    def call(self, address):
        """
        Выполняет вызов подпрограммы по указанному адресу.

        :param address: 16-битный адрес для перехода
        """
        # Сохраняем текущий адрес возврата (PC) в стеке
        return_address = self.registers['PC']
        self.registers['SP'] = (self.registers['SP'] - 1) & 0xFFFF
        self.memory[self.registers['SP']] = (return_address >> 8) & 0xFF  # Сохраняем старший байт
        self.registers['SP'] = (self.registers['SP'] - 1) & 0xFFFF
        self.memory[self.registers['SP']] = return_address & 0xFF  # Сохраняем младший байт

        # Переходим по указанному адресу
        self.registers['PC'] = address

    def call_cc(self, condition, address):
        """
        Выполняет условный вызов подпрограммы по указанному адресу.

        :param condition: строка, обозначающая условие ('NZ', 'Z', 'NC', 'C')
        :param address: 16-битный адрес для перехода
        """
        if self.check_condition(condition):
            self.call(address)

    def check_condition(self, condition):
        """
        Проверяет выполнение условия.

        :param condition: строка, обозначающая условие ('NZ', 'Z', 'NC', 'C')
        :return: булево значение, указывающее, выполнено ли условие
        """
        if condition == 'NZ':
            return not self.get_flag('Z')
        elif condition == 'Z':
            return self.get_flag('Z')
        elif condition == 'NC':
            return not self.get_flag('C')
        elif condition == 'C':
            return self.get_flag('C')
        elif condition == 'PO':
            return not self.get_flag('P/V')
        elif condition == 'PE':
            return self.get_flag('P/V')
        elif condition == 'P':
            return not self.get_flag('S')
        elif condition == 'M':
            return self.get_flag('S')
        else:
            raise ValueError(f"Неизвестное условие: {condition}")

    def ret(self):
        """
        Возврат из подпрограммы.
        Инструкция: RET
        """
        # Извлекаем адрес возврата из стека
        low = self.memory[self.registers['SP']]
        self.registers['SP'] = (self.registers['SP'] + 1) & 0xFFFF
        high = self.memory[self.registers['SP']]
        self.registers['SP'] = (self.registers['SP'] + 1) & 0xFFFF

        # Устанавливаем PC на адрес возврата
        self.registers['PC'] = (high << 8) | low

    def retn(self):
        # Восстановление PC из стека
        low = self.memory[self.registers['SP']]
        self.registers['SP'] = (self.registers['SP'] + 1) & 0xFFFF
        high = self.memory[self.registers['SP']]
        self.registers['SP'] = (self.registers['SP'] + 1) & 0xFFFF
        self.registers['PC'] = (high << 8) | low

        # Копирование IFF2 в IFF1
        self.iff1 = self.iff2

        # Включение прерываний не происходит немедленно
        # Это позволяет выполнить как минимум одну инструкцию после RETN
        self.interrupts_enabled = self.iff1

        print("RETN выполнен. PC установлен на", hex(self.registers['PC']))
        print("IFF1 установлен в", self.iff1)        

    def ret_cc(self, condition):
        """
        Условный возврат из подпрограммы.
        Инструкция: RET cc

        :param condition: строка, обозначающая условие ('NZ', 'Z', 'NC', 'C')
        """
        if self.check_condition(condition):
            self.ret()
        # Если условие не выполнено, продолжаем выполнение следующей инструкции

    # Вспомогательные методы для битовых операций
    def rlc(self, value):
        carry = value >> 7
        result = ((value << 1) | carry) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)

        self.set_flag('H', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', result & 0x08)
        self.set_flag('5', result & 0x20)
        return result

    def rrc(self, value):
        carry = value & 1
        result = ((value >> 1) | (carry << 7)) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)

        self.set_flag('H', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', result & 0x08)
        self.set_flag('5', result & 0x20)
        return result

    def rlca(self):
        carry = self.registers['A'] >> 7
        self.registers['A'] = ((self.registers['A'] << 1) | carry) & 0xFF
        self.set_flag('C', carry)
        self.set_flag('H', 0)
        self.set_flag('N', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', self.registers['A'] & 0x08)
        self.set_flag('5', self.registers['A'] & 0x20)

    def rrca(self):
        carry = self.registers['A'] & 1
        self.registers['A'] = ((self.registers['A'] >> 1) | (carry << 7)) & 0xFF
        self.set_flag('C', carry)
        self.set_flag('H', 0)
        self.set_flag('N', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', self.registers['A'] & 0x08)
        self.set_flag('5', self.registers['A'] & 0x20)

    def rla(self):
        old_carry = self.get_flag('C')
        new_carry = self.registers['A'] >> 7
        self.registers['A'] = ((self.registers['A'] << 1) | old_carry) & 0xFF
        self.set_flag('C', new_carry)
        self.set_flag('H', 0)
        self.set_flag('N', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', self.registers['A'] & 0x08)
        self.set_flag('5', self.registers['A'] & 0x20)

    def rra(self):
        old_carry = self.get_flag('C')
        new_carry = self.registers['A'] & 1
        self.registers['A'] = ((self.registers['A'] >> 1) | (old_carry << 7)) & 0xFF
        self.set_flag('C', new_carry)
        self.set_flag('H', 0)
        self.set_flag('N', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', self.registers['A'] & 0x08)
        self.set_flag('5', self.registers['A'] & 0x20)

    def rl(self, value):
        old_carry = self.get_flag('C')
        carry = value >> 7
        result = ((value << 1) | old_carry) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)

        self.set_flag('H', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', result & 0x08)
        self.set_flag('5', result & 0x20)
        return result

    def rr(self, value):
        old_carry = self.get_flag('C')
        carry = value & 1
        result = ((value >> 1) | (old_carry << 7)) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)

        self.set_flag('H', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', result & 0x08)
        self.set_flag('5', result & 0x20)
        return result

    def sla(self, value):
        carry = value >> 7
        result = (value << 1) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)

        self.set_flag('H', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', result & 0x08)
        self.set_flag('5', result & 0x20)
        return result

    def sra(self, value):
        carry = value & 1
        result = ((value >> 1) | (value & 0x80)) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)

        self.set_flag('H', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', result & 0x08)
        self.set_flag('5', result & 0x20)
        return result

    def sll(self, value):
        carry = value >> 7
        result = ((value << 1) | 1) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)

        self.set_flag('H', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', result & 0x08)
        self.set_flag('5', result & 0x20)
        return result

    def srl(self, value):
        carry = value & 1
        result = (value >> 1) & 0xFF
        self.set_flag('C', carry)
        self.update_flags(result, zero=True, sign=True, parity=True)

        self.set_flag('H', 0)
        # Установка флагов 3 и 5
        self.set_flag('3', result & 0x08)
        self.set_flag('5', result & 0x20)
        return result

    def bit(self, bit, value):
        result = value & (1 << bit)
        self.set_flag('Z', result == 0)
        self.set_flag('H', 1)
        self.set_flag('N', 0)
        self.set_flag('P/V', result == 0)
        self.set_flag('S', bit == 7 and result != 0)
        # Установка флагов 3 и 5
        self.set_flag('3', value & 0x08)
        self.set_flag('5', value & 0x20)

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

        # Установка флагов
        #self.set_flag('S', value & 0x80)  # Устанавливается, если результат отрицательный
        #self.set_flag('Z', value == 0)    # Устанавливается, если результат нулевой
        self.set_flag('H', 0)             # Всегда сбрасывается
        #self.set_flag('P/V', self.parity(value))  # Устанавливается, если четный паритет
        #self.set_flag('N', 0)             # Всегда сбрасывается
        
        # Флаги 3 и 5 устанавливаются в соответствии с битами 3 и 5 входного значения
        self.set_flag('3', value & 0x08)
        self.set_flag('5', value & 0x20)        

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
        # Устанавливаем флаги 3 и 5 на основе старшего байта результата
        result_h = (result >> 8) & 0xFF
        self.set_flag('3', result_h & 0x08)
        self.set_flag('5', result_h & 0x20)

    def adc_hl(self, rp):
        hl = self.get_register_pair('HL')
        value = self.get_register_pair(rp)
        carry = self.get_flag('C')
        result = hl + value + carry
        self.set_register_pair('HL', result & 0xFFFF)
        self.set_flag('C', result > 0xFFFF)
        self.set_flag('H', (hl & 0xFFF) + (value & 0xFFF) + carry > 0xFFF)
        #self.update_flags(result & 0xFFFF, zero=True, sign=True, parity=True)
        self.set_flag('N', 0)

        # Флаг P/V (переполнение)
        overflow = ((hl ^ ~value) & (hl ^ result) & 0x8000) != 0
        self.set_flag('P/V', overflow)
        # Флаг Z (нуль)
        self.set_flag('Z', (result & 0xFFFF) == 0)        
        # Флаг S (знак) - берется из бита 15 результата
        self.set_flag('S', (result & 0x8000) != 0)
        # Флаги F5 и F3 копируются из битов 13 и 11 результата соответственно
        self.set_flag('5', (result & 0x2000) != 0)
        self.set_flag('3', (result & 0x0800) != 0)          

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
        self.set_flag('S', (result & 0x8000) != 0)  # Проверяем 15-й бит (знаковый бит для 16-битного результата)      

    # Специальные инструкции
    def neg(self):
        value = self.registers['A']
        result = (-value) & 0xFF
        self.registers['A'] = result
        self.set_flag('C', value != 0)
        self.set_flag('H', (value & 0xF) != 0)
        self.update_flags(result, zero=True, sign=True, parity=True)
        self.set_flag('N', 1)
        self.set_flag('3', result & 0x08)
        self.set_flag('5', result & 0x20)

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
        # Дополнительные флаги
        n = self.registers['A'] + self.memory[self.get_register_pair('HL') - 1]
        self.set_flag('5', n & 0x02)
        self.set_flag('3', n & 0x08)

    def ldd(self):
        self._block_transfer(-1)
        self.set_flag('H', 0)
        self.set_flag('N', 0)
        self.set_flag('P/V', self.get_register_pair('BC') != 0)

        # Дополнительные флаги
        n = self.registers['A'] + self.memory[self.get_register_pair('HL') + 1]
        self.set_flag('5', n & 0x02)
        self.set_flag('3', n & 0x08)

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

    def dec_index_d(self, index_reg):
        # Получаем смещение
        offset = self.fetch_signed()
        # Вычисляем эффективный адрес
        address = (self.registers[index_reg] + offset) & 0xFFFF
        # Получаем значение из памяти
        value = self.memory[address]
        # Уменьшаем значение на 1
        result = (value - 1) & 0xFF
        # Записываем результат обратно в память
        self.memory[address] = result
        # Обновляем флаги
        self.update_flags(result, zero=True, sign=True, halfcarry=True)
        self.set_flag('S', result & 0x80)  # Устанавливаем флаг знака
        self.set_flag('Z', result == 0)    # Устанавливаем флаг нуля
        self.set_flag('H', (value & 0x0F) == 0)  # Устанавливаем флаг полупереноса
        self.set_flag('P/V', value == 0x80)  # Устанавливаем флаг переполнения
        self.set_flag('N', 1)  # Устанавливаем флаг вычитания
        self.set_flag('5', result & 0x20)
        self.set_flag('3', result & 0x08)


    def inc_index_d(self, index_reg):
        # Получаем смещение
        offset = self.fetch_signed()
        # Вычисляем эффективный адрес
        address = (self.registers[index_reg] + offset) & 0xFFFF
        # Получаем значение из памяти
        value = self.memory[address]
        # Увеличиваем значение на 1
        result = (value + 1) & 0xFF
        # Записываем результат обратно в память
        self.memory[address] = result
        # Обновляем флаги
        self.update_flags(result, zero=True, sign=True, halfcarry=True)

        self.set_flag('S', result & 0x80)  # Устанавливаем флаг знака
        self.set_flag('Z', result == 0)    # Устанавливаем флаг нуля
        self.set_flag('H', (value & 0x0F) == 0)  # Устанавливаем флаг полупереноса
        self.set_flag('P/V', value == 0x80)  # Устанавливаем флаг переполнения
        self.set_flag('5', result & 0x20)
        self.set_flag('3', result & 0x08)

    def add_index(self, index_reg, rr):
        index_value = self.registers[index_reg]
        rr_value = self.get_register_pair(rr)
        result = (index_value + rr_value) & 0xFFFF
        self.registers[index_reg] = result

        # Update flags
        self.set_flag('N', 0)
        self.set_flag('H', ((index_value & 0xFFF) + (rr_value & 0xFFF)) > 0xFFF)
        self.set_flag('C', (index_value + rr_value) > 0xFFFF)
        # Note: S, Z, and P/V flags are not affected
        # Установка флагов F5 и F3 на основе старшего байта результата
        result_high = (result >> 8) & 0xFF
        self.set_flag('5', result_high & 0x20)  # Бит 5 старшего байта результата
        self.set_flag('3', result_high & 0x08)  # Бит 3 старшего байта результата

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
        if opcode == 0x00:  # DD 00
            # NOP - No operation
            pass  # Просто игнорируем, как обычный NO
        elif opcode == 0x23:  # DD 23 (INC IX)
                self.registers[index_reg] = (self.registers[index_reg] + 1) & 0xFFFF
        elif opcode == 0x24:  # DD 24: INC IXh
            high_byte = (self.registers[index_reg] >> 8) & 0xFF
            result = (high_byte + 1) & 0xFF
            self.registers[index_reg] = (self.registers[index_reg] & 0x00FF) | (result << 8)
            # Установка флагов
            self.set_flag('S', result & 0x80)
            self.set_flag('Z', result == 0)
            self.set_flag('H', (high_byte & 0x0F) == 0x0F)
            self.set_flag('P/V', result == 0x80)
            self.set_flag('N', 0)
            self.set_flag('5', result & 0x20)
            self.set_flag('3', result & 0x08)
        elif opcode == 0x25:  # DD 25 - DEC IXh
            value = self.registers[index_reg]
            high_byte = (self.registers[index_reg] >> 8) & 0xFF
            #value = high_byte
            result = (high_byte - 1) & 0xFF
            self.registers[index_reg] = (self.registers[index_reg] & 0x00FF) | (result << 8)

            # Установка флагов
            self.set_flag('N', 1)

            # Флаги H, S, Z, P/V устанавливаются на основе старшего байта результата
            result_high = (result) & 0xFF
            prev_high = (value >> 8) & 0xFF

            self.set_flag('H', (result_high & 0x0F) == 0x0F)
            self.set_flag('S', result_high & 0x80)
            self.set_flag('Z', result_high == 0)
            self.set_flag('P/V', prev_high == 0x80 and result_high == 0x7F)

            # Установка флагов 5 и 3
            self.set_flag('5', result_high & 0x20)
            self.set_flag('3', result_high & 0x08)

        elif opcode in [0x09, 0x19, 0x29, 0x39]:  # ADD IX/IY, rr
            rr = {0x09: 'BC', 0x19: 'DE', 0x29: index_reg, 0x39: 'SP'}[opcode]
            self.add_index(index_reg, rr)
        elif opcode in [0x21, 0x22, 0x2A, 0x34, 0x35, 0x36, 0xE9, 0xF9]:
            # Специальные случаи для LD IX/IY, nn и LD (nn), IX/IY
            if opcode == 0x21:  # LD IX/IY, nn
                self.registers[index_reg] = self.fetch_word()
            elif opcode == 0x22:  # LD (nn), IX/IY
                address = self.fetch_word()
                self.store_word(address, self.registers[index_reg])
            elif opcode == 0x2A:  # LD IX/IY, (nn)
                address = self.fetch_word()
                self.registers[index_reg] = self.memory[address] | (self.memory[address + 1] << 8)
            elif opcode == 0x34:  # INC (IX/IY+d)
                self.inc_index_d(index_reg)
            elif opcode == 0x35:  # DEC (IX/IY+d)
                self.dec_index_d(index_reg)
            elif opcode == 0x36:  # LD (IX/IY+d), n
                offset = self.fetch_signed()
                value = self.fetch()
                address = (self.registers[index_reg] + offset) & 0xFFFF
                self.memory[address] = value
            elif opcode == 0xE9:  # JP (IX/IY)
                self.registers['PC'] = self.registers[index_reg]
            elif opcode == 0xF9:  # LD SP, IX/IY
                self.registers['SP'] = self.registers[index_reg]
        elif opcode == 0x44:  # LD B,IXH
            high_byte = (self.registers[index_reg] >> 8) & 0xFF
            self.registers['B'] = high_byte
        elif opcode == 0x45:  # LD B,IXL
            low_byte = self.registers[index_reg] & 0xFF
            self.registers['B'] = low_byte
        elif opcode == 0x4C:  # LD C,IXH
            high_byte = (self.registers[index_reg] >> 8) & 0xFF
            self.registers['C'] = high_byte
        elif opcode == 0x4D:  # LD C,IXL
            low_byte = self.registers[index_reg] & 0xFF
            self.registers['C'] = low_byte
        elif opcode == 0x54:  # LD D,IXH
            high_byte = (self.registers[index_reg] >> 8) & 0xFF
            self.registers['D'] = high_byte
        elif opcode == 0x55:  # LD D,IXL
            low_byte = self.registers[index_reg] & 0xFF
            self.registers['D'] = low_byte
        elif opcode == 0x5C:  # LD C,IXH
            high_byte = (self.registers[index_reg] >> 8) & 0xFF
            self.registers['E'] = high_byte
        elif opcode == 0x5D:  # LD C,IXL
            low_byte = self.registers[index_reg] & 0xFF
            self.registers['E'] = low_byte
        elif opcode == 0x60:  # LD IXh,B
            self.registers[index_reg] = ( self.registers['B'] << 8 ) | (self.registers[index_reg] & 0xFF)
        elif opcode == 0x61:  # LD IXh,C
            self.registers[index_reg] = ( self.registers['C'] << 8 ) | (self.registers[index_reg] & 0xFF)
        elif opcode == 0x62:  # LD IXh,D
            self.registers[index_reg] = ( self.registers['D'] << 8 ) | (self.registers[index_reg] & 0xFF)
        elif opcode == 0x63:  # LD IXh,E
            self.registers[index_reg] = ( self.registers['E'] << 8 ) | (self.registers[index_reg] & 0xFF)
        elif opcode == 0x64:  # LD IXh,IXh
            pass
        elif opcode == 0x65:  # LD IXh,IXl
            self.registers[index_reg] = ( (self.registers[index_reg] & 0xFF) << 8 ) | (self.registers[index_reg] & 0xFF)
        elif opcode == 0x67:  # LD IXh,A
            self.registers[index_reg] = ( self.registers['A'] << 8 ) | (self.registers[index_reg] & 0xFF)

        elif opcode == 0x68:  # LD IXl,B
            self.registers[index_reg] = (self.registers[index_reg] & 0xFF00) | (self.registers['B'] & 0xFF)
        elif opcode == 0x69:  # LD IXl,C
            self.registers[index_reg] = (self.registers[index_reg] & 0xFF00) | (self.registers['C'] & 0xFF)
        elif opcode == 0x6A:  # LD IXl,D
            self.registers[index_reg] = (self.registers[index_reg] & 0xFF00) | (self.registers['D'] & 0xFF)
        elif opcode == 0x6B:  # LD IXl,E
            self.registers[index_reg] = (self.registers[index_reg] & 0xFF00) | (self.registers['E'] & 0xFF)
        elif opcode == 0x6C:  # LD IXl,IXh
            self.registers[index_reg] = (self.registers[index_reg] & 0xFF00) | ((self.registers[index_reg] >> 8) & 0xFF)
            pass
        elif opcode == 0x6D:  # LD IXl,IXl
            pass
        elif opcode == 0x6F:  # LD IXl,A
            self.registers[index_reg] = (self.registers[index_reg] & 0xFF00) | (self.registers['A'] & 0xFF)

        elif opcode == 0x7C:  # LD A,IXH
            high_byte = (self.registers[index_reg] >> 8) & 0xFF
            self.registers['A'] = high_byte
        elif opcode == 0x7D:  # LD A,IXL
            low_byte = self.registers[index_reg] & 0xFF
            self.registers['A'] = low_byte
        elif opcode & 0xC0 == 0x40:  # LD instructions
            self._indexed_load(index_reg, opcode)
        elif opcode & 0xC0 == 0x80:  # Arithmetic instructions
            self._indexed_arithmetic(index_reg, opcode)
        elif opcode == 0xCB:  # CB-prefixed instructions
            self._execute_indexed_cb(index_reg)
        elif opcode == 0xE1: # POP (IX/IY)
            self.registers[index_reg] = self.memory[self.registers['SP']] | (self.memory[self.registers['SP'] + 1] << 8)
            self.registers['SP'] = (self.registers['SP'] + 2) & 0xFFFF
        elif opcode == 0xE3: # EX (SP), IX/IY
            self.ex_sp_ix(index_reg)
        elif opcode == 0xE5: # PUSH IX/IY
            self.push_index_reg(index_reg)
        else:
            raise ValueError(f"Unsupported {index_reg} instruction: {opcode:02X}")

    def _indexed_load(self, index_reg, opcode):
        #print(f"reg {reg}")
        if opcode & 0x07 == 0x06:  # LD r, (IX/IY+d)
            reg_index = (opcode & 0x38) >> 3
            reg = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A'][reg_index]
            offset = self.fetch_signed()
            #if reg == '(HL)':
            #    if opcode & 0x38 == 0x30:  # Check if it's a store operation
            #    self.memory[address] = self.registers['A']  # Only 'A' can be stored
            #else:
            address = (self.registers[index_reg] + offset) & 0xFFFF
            self.registers[reg] = self.memory[address]
        elif (opcode & 0x38) == 0x30:  # LD (IX/IY+d), r
            reg_index = (opcode & 0x07)
            reg = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A'][reg_index]
            offset = self.fetch_signed()
            address = (self.registers[index_reg] + offset) & 0xFFFF
            self.memory[address] = self.registers[reg]

    def _indexed_arithmetic(self, index_reg, opcode):
        operation = (opcode & 0x38) >> 3
        #operation = (opcode & 0x1C) >> 2
        operand =  (opcode & 0x03)
        #print(f"operation {operation}")
        #print(f"operand {operand}")
        if operand == 0:
            high_byte = (self.registers[index_reg] >> 8) & 0xFF
            value = high_byte
        elif operand == 1:
            low_byte = self.registers[index_reg] & 0xFF
            value = low_byte
        elif operand == 2:
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


    def execute_cb(self):
        opcode = self.fetch()
        #if self.debug:
            #print(f"{self.registers['PC']-1:04X}: {z80_to_asm[opcode]}")
            #print(f"cb opcode: {opcode:02X}")

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
            0x4B: lambda: self.load_register_pair('BC', self.load_word(self.fetch_word())),
            0x4C: lambda: self.neg(), #*
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
            0x5B: lambda: self.load_register_pair('DE', self.load_word(self.fetch_word())),
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
            0x6B: lambda: self.load_register_pair('HL', self.load_word(self.fetch_word())),
            0x6F: lambda: self.rld(),
            0x72: lambda: self.sbc_hl('SP'),
            0x73: lambda: self.store_word(self.fetch_word(), self.get_register_pair('SP')),
            0x78: lambda: self.in_r_c('A'),
            0x79: lambda: self.out_c_r('A'),
            0x7A: lambda: self.adc_hl('SP'),
            0x7B: lambda: self.load_register_pair('SP', self.load_word(self.fetch_word())),
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

    def _execute_indexed_cb(self, index_reg):
        offset = self.fetch_signed()
        opcode = self.fetch()
        address = (self.registers[index_reg] + offset) & 0xFFFF
        value = self.memory[address]

        if opcode < 0x40:  # Rotate and Shift instructions
            operation = [self.rlc, self.rrc, self.rl, self.rr, self.sla, self.sra, self.sll, self.srl][opcode >> 3]
            result = operation(value)
            self.memory[address] = result
            if opcode & 7 != 6:  # If not (HL), store result in register
                reg = ['B', 'C', 'D', 'E', 'H', 'L', None, 'A'][opcode & 7]
                self.registers[reg] = result
        elif opcode < 0x80:  # BIT instructions
            bit = (opcode >> 3) & 7
            self.bit(bit, value)
            # Установка флагов F5 и F3 на основе старшего байта адреса
            high_byte = (address >> 8) & 0xFF
            self.set_flag('5', high_byte & 0x20)
            self.set_flag('3', high_byte & 0x08)
        elif opcode < 0xC0:  # RES instructions
            bit = (opcode >> 3) & 7
            result = self.res(bit, value)
            self.memory[address] = result
            if opcode & 7 != 6:  # If not (HL), store result in register
                reg = ['B', 'C', 'D', 'E', 'H', 'L', None, 'A'][opcode & 7]
                self.registers[reg] = result
        else:  # SET instructions
            bit = (opcode >> 3) & 7
            result = self.set(bit, value)
            self.memory[address] = result
            if opcode & 7 != 6:  # If not (HL), store result in register
                reg = ['B', 'C', 'D', 'E', 'H', 'L', None, 'A'][opcode & 7]
                self.registers[reg] = result

    def rst(self, address):
        # Push the current PC onto the stack
        self.registers['SP'] = (self.registers['SP'] - 1) & 0xFFFF
        self.memory[self.registers['SP']] = (self.registers['PC'] >> 8) & 0xFF
        self.registers['SP'] = (self.registers['SP'] - 1) & 0xFFFF
        self.memory[self.registers['SP']] = self.registers['PC'] & 0xFF

        # Jump to the restart address
        self.registers['PC'] = address

    def ex_sp_ix(self, index_reg):
        # Получаем значение из стека
        sp = self.registers['SP']
        low = self.memory[sp]
        high = self.memory[(sp + 1) & 0xFFFF]
        stack_value = (high << 8) | low

        # Получаем значение IX
        ix_value = self.registers[index_reg]

        # Меняем местами значения
        self.registers[index_reg] = stack_value
        
        # Записываем значение IX в стек
        self.memory[sp] = ix_value & 0xFF
        self.memory[(sp + 1) & 0xFFFF] = (ix_value >> 8) & 0xFF

        # Обновляем флаги
        #self.set_flag('3', high & 0x08)  # Бит 3 старшего байта нового значения IX
        #self.set_flag('5', high & 0x20)  # Бит 5 старшего байта нового значения IX

        # Другие флаги не изменяются        

    def push_index_reg(self,index_reg):
        # Уменьшаем указатель стека
        self.registers['SP'] = (self.registers['SP'] - 1) & 0xFFFF
    
        # Сохраняем старший байт IX
        self.memory[self.registers['SP']] = (self.registers[index_reg] >> 8) & 0xFF
        
        # Снова уменьшаем указатель стека
        self.registers['SP'] = (self.registers['SP'] - 1) & 0xFFFF
        
        # Сохраняем младший байт IX
        self.memory[self.registers['SP']] = self.registers[index_reg] & 0xFF        