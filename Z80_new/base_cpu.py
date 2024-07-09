import logging

class baseCPUClass:
    def __init__(self):
        self.registers = {
            'A': 0, 'F': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'H': 0, 'L': 0,
            'IX': 0, 'IY': 0, 'SP': 0, 'PC': 0,
            'A_': 0, 'F_': 0, 'B_': 0, 'C_': 0, 'D_': 0, 'E_': 0, 'H_': 0, 'L_': 0  # Альтернативный набор регистров
        }
        # ... (предыдущая инициализация)
        self.registers['IX'] = 0
        self.registers['IY'] = 0
        self.registers['I'] = 0
        self.registers['R'] = 0

        self.iff1 = False
        self.iff2 = False
        #self.im = 0
        self.memory = [0] * 65536

        self.interrupts_enabled = False
        self.interrupt_mode = 0
        self.halted = False

    def reset(self):
        # Сброс всех регистров и флагов
        self.registers = {
            'A': 0, 'F': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'H': 0, 'L': 0,
            'IX': 0, 'IY': 0, 'SP': 0, 'PC': 0,
            'A_': 0, 'F_': 0, 'B_': 0, 'C_': 0, 'D_': 0, 'E_': 0, 'H_': 0, 'L_': 0  # Альтернативный набор регистров
        }
        # ... (предыдущая инициализация)
        self.registers['IX'] = 0
        self.registers['IY'] = 0
        self.registers['I'] = 0
        self.registers['R'] = 0

        self.interrupts_enabled = False

    def display_registers(self, screen, font, offset):
        x, y = 10, 10 + offset
        #for reg, value in self.registers.items():
        #    text = font.render(f"{reg}: {value:04X}", True, (255, 255, 255))
        #    screen.blit(text, (x, y))
        #    y += 20
        text = font.render(f"AF: {self.get_register_pair('AF'):04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))
        y += 20
        text = font.render(f"BC: {self.get_register_pair('BC'):04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))        
        y += 20
        text = font.render(f"DE: {self.get_register_pair('DE'):04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))
        y += 20
        text = font.render(f"HL: {self.get_register_pair('HL'):04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))        
        y += 20
        text = font.render(f"IX: {self.registers['IX']:04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))
        y += 20
        text = font.render(f"IY: {self.registers['IY']:04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))        
        y += 20
        text = font.render(f"PC: {self.registers['PC']:04X}", True, (255, 255, 255))
        screen.blit(text, (x, y))
        y += 20
        text = font.render(f"SP: {self.registers['SP']:04X}", True, (255, 255, 255))
        screen.blit(text, (x, y)) 

        y += 20
        text = font.render(f"Interrupts enabled: {self.interrupts_enabled}", True, (255, 255, 255))
        screen.blit(text, (x, y)) 

        y += 20
        text = font.render(f"Interrupt mode: {self.interrupt_mode}", True, (255, 255, 255))
        screen.blit(text, (x, y)) 

    def load_memory(self, address, data):
        # Загрузка данных в память по заданному адресу
        self.memory[address:address + len(data)] = data

    def im(self, mode):
        """
        Устанавливает режим прерываний (Interrupt Mode).
        
        :param mode: режим прерываний (0, 1 или 2)
        """
        if mode not in [0, 1, 2]:
            raise ValueError(f"Недопустимый режим прерываний: {mode}")
        
        self.interrupt_mode = mode
        
        if mode == 0:
            # В режиме 0 внешнее устройство может поместить любую инструкцию на шину данных
            print("Установлен режим прерываний 0")
        elif mode == 1:
            # В режиме 1 процессор всегда выполняет RST 38h при прерывании
            print("Установлен режим прерываний 1")
        else:  # mode == 2
            # В режиме 2 используется косвенная адресация через таблицу векторов прерываний
            print("Установлен режим прерываний 2")  

    def handle_interrupt(self):
        if not self.interrupts_enabled:
            return
        
        if self.halted:
            self.halted = False  # Выход из HALT
            print("Процессор возобновил выполнение после прерывания.")

        self.interrupts_enabled = False

        self.registers['SP'] = (self.registers['SP'] - 1) & 0xFFFF
        self.memory[self.registers['SP']] = (self.registers['PC'] >> 8) & 0xFF
        self.registers['SP'] = (self.registers['SP'] - 1) & 0xFFFF
        self.memory[self.registers['SP']] = self.registers['PC'] & 0xFF

        if self.interrupt_mode == 0:
            self.registers['PC'] = 0x0038
        elif self.interrupt_mode == 1:
            self.registers['PC'] = 0x0038
            logging.info('========== Call interrupt ==========')
            logging.disable()
        elif self.interrupt_mode == 2:
            vector = self.io_controller.get_data_bus_value()
            address = (self.i << 8) | vector
            self.registers['PC'] = (self.memory[address + 1] << 8) | self.memory[address]   

        #print("Interrupt 38")         

    def handle_nmi(self):
        self.sp = (self.sp - 1) & 0xFFFF
        self.memory[self.sp] = (self.pc >> 8) & 0xFF
        self.sp = (self.sp - 1) & 0xFFFF
        self.memory[self.sp] = self.pc & 0xFF
        self.pc = 0x0066 


    def fetch(self):
        value = self.memory[self.registers['PC']]
        self.registers['PC'] += 1
        return value

    def fetch_word(self):
        low = self.fetch()
        high = self.fetch()
        return (high << 8) | low

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

    def update_flags(self, result, zero=False, sign=False, parity=False, halfcarry=True):
        if zero:
            self.set_flag('Z', result == 0)
        if sign:
            self.set_flag('S', result & 0x80)
        if parity:
            self.set_flag('P/V', bin(result).count('1') % 2 == 0)
        if halfcarry:
            self.set_flag('H', (self.registers['F'] & ~0x10) | (0x10 if (result & 0xF) < (self.registers['A'] & 0xF) else 0)    )      

    # Методы ввода-вывода (заглушки, которые нужно реализовать)
    def io_read(self, port):
        # Реализуйте чтение из порта
        return 0

    def io_write(self, port, value):
        # Реализуйте запись в порт
        pass

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

    def store_word(self, address, value):
        """
        Сохраняет 16-битное слово в память по указанному адресу.
        
        :param address: адрес в памяти, куда нужно сохранить слово
        :param value: 16-битное значение для сохранения
        """
        # Убеждаемся, что значение 16-битное
        value = value & 0xFFFF
        
        # Сохраняем младший байт
        self.memory[address] = value & 0xFF
        
        # Сохраняем старший байт
        self.memory[(address + 1) & 0xFFFF] = (value >> 8) & 0xFF        

    def inc_register(self, reg):
        self.registers[reg] = (self.registers[reg] + 1) & 0xFF
        self.update_flags(self.registers[reg], zero=True, sign=True, halfcarry=True)

    def dec_register(self, reg):
        self.registers[reg] = (self.registers[reg] - 1) & 0xFF
        self.update_flags(self.registers[reg], zero=True, sign=True, halfcarry=True)

    def inc_memory(self, address):
        self.memory[address] = (self.memory[address] + 1) & 0xFF
        self.update_flags(self.memory[address], zero=True, sign=True, halfcarry=True)

    def dec_memory(self, address):
        self.memory[address] = (self.memory[address] - 1) & 0xFF
        self.update_flags(self.memory[address], zero=True, sign=True, halfcarry=True)

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

    def exchange_de_hl(self):
        """
        Обмен содержимым пар регистров DE и HL.
        Инструкция: EX DE, HL
        """
        self.registers['D'], self.registers['H'] = self.registers['H'], self.registers['D']
        self.registers['E'], self.registers['L'] = self.registers['L'], self.registers['E']

    def exchange_af(self):
        """
        Обмен содержимым основного и альтернативного набора регистров AF.
        Инструкция: EX AF, AF'
        """
        self.registers['A'], self.registers['A_'] = self.registers['A_'], self.registers['A']
        self.registers['F'], self.registers['F_'] = self.registers['F_'], self.registers['F']

    def exx(self):
        """
        Обмен содержимым регистров BC, DE, HL с их альтернативными наборами.
        Инструкция: EXX
        """
        self.registers['B'], self.registers['B_'] = self.registers['B_'], self.registers['B']
        self.registers['C'], self.registers['C_'] = self.registers['C_'], self.registers['C']
        self.registers['D'], self.registers['D_'] = self.registers['D_'], self.registers['D']
        self.registers['E'], self.registers['E_'] = self.registers['E_'], self.registers['E']
        self.registers['H'], self.registers['H_'] = self.registers['H_'], self.registers['H']
        self.registers['L'], self.registers['L_'] = self.registers['L_'], self.registers['L']

    def exchange_sp_hl(self):
        """
        Обмен содержимым HL с верхними двумя байтами стека.
        Инструкция: EX (SP), HL
        """
        sp = self.registers['SP']
        l = self.memory[sp]
        h = self.memory[(sp + 1) & 0xFFFF]
        
        self.memory[sp] = self.registers['L']
        self.memory[(sp + 1) & 0xFFFF] = self.registers['H']
        
        self.registers['L'] = l
        self.registers['H'] = h

    def xor_a(self, operand):
        """
        Выполняет операцию XOR между аккумулятором и операндом.
        Результат сохраняется в аккумуляторе.
        
        :param operand: значение для операции XOR (может быть регистром или непосредственным значением)
        """
        # Если операнд - строка, значит это имя регистра
        if isinstance(operand, str):
            value = self.registers[operand]
        else:
            value = operand
        
        # Выполняем XOR
        result = self.registers['A'] ^ value
        
        # Сохраняем результат в аккумуляторе
        self.registers['A'] = result & 0xFF  # Убеждаемся, что результат 8-битный
        
        # Устанавливаем флаги
        self.set_flag('S', result & 0x80)  # Устанавливаем флаг знака
        self.set_flag('Z', result == 0)    # Устанавливаем флаг нуля
        self.set_flag('H', 0)              # Сбрасываем флаг полупереноса
        self.set_flag('P/V', self.parity(result))  # Устанавливаем флаг четности/переполнения
        self.set_flag('N', 0)              # Сбрасываем флаг вычитания
        self.set_flag('C', 0)              # Сбрасываем флаг переноса

    def or_a(self, operand):
        """
        Выполняет побитовую операцию OR между аккумулятором и операндом.
        Результат сохраняется в аккумуляторе.
        
        :param operand: значение для операции OR (может быть регистром или непосредственным значением)
        """
        # Если операнд - строка, значит это имя регистра
        if isinstance(operand, str):
            value = self.registers[operand]
        else:
            value = operand
        
        # Выполняем OR
        result = self.registers['A'] | value
        
        # Сохраняем результат в аккумуляторе
        self.registers['A'] = result & 0xFF  # Убеждаемся, что результат 8-битный
        
        # Устанавливаем флаги
        self.set_flag('S', result & 0x80)  # Устанавливаем флаг знака
        self.set_flag('Z', result == 0)    # Устанавливаем флаг нуля
        self.set_flag('H', 0)              # Сбрасываем флаг полупереноса
        self.set_flag('P/V', self.parity(result))  # Устанавливаем флаг четности/переполнения
        self.set_flag('N', 0)              # Сбрасываем флаг вычитания
        self.set_flag('C', 0)              # Сбрасываем флаг переноса        

    def parity(self, value):
        """
        Вычисляет четность значения.
        Возвращает True, если число единичных битов четное, иначе False.
        
        :param value: 8-битное значение для проверки четности
        :return: булево значение, представляющее четность
        """
        # Убеждаемся, что значение 8-битное
        value &= 0xFF
        
        # Подсчитываем количество единичных битов
        ones = 0
        for i in range(8):
            if value & (1 << i):
                ones += 1
        
        # Возвращаем True, если количество единичных битов четное
        return ones % 2 == 0

    def jump(self, address):
        self.registers['PC'] = address

    def halt(self):
        # В реальной реализации здесь должна быть логика остановки процессора
        """Выполняет команду HALT."""
        print("Выполнение HALT. Процессор остановлен.")
        self.halted = True  # Устанавливаем состояние HALT

        #pass

    def cp(self, value):
        """
        Сравнение аккумулятора с операндом.
        Инструкция: CP n
        
        :param value: значение для сравнения (может быть регистром или непосредственным значением)
        """
        if isinstance(value, str):
            # Если value - строка, это имя регистра
            operand = self.registers[value]
        else:
            # Иначе это непосредственное значение
            operand = value
        
        result = (self.registers['A'] - operand) & 0xFF
        
        # Устанавливаем флаги
        self.set_flag('S', result & 0x80)  # Устанавливаем флаг знака
        self.set_flag('Z', result == 0)    # Устанавливаем флаг нуля
        self.set_flag('H', ((self.registers['A'] & 0xF) - (operand & 0xF)) & 0x10)  # Флаг полупереноса
        
        # Флаг переполнения устанавливается, если знак результата неверен
        self.set_flag('P/V', ((self.registers['A'] ^ operand) & (self.registers['A'] ^ result) & 0x80) != 0)
        
        self.set_flag('N', 1)  # Всегда устанавливается, так как это операция вычитания
        self.set_flag('C', self.registers['A'] < operand)  # Устанавливаем флаг переноса

    def and_a(self, value):
        """
        Выполняет побитовую операцию AND между аккумулятором и операндом.
        Результат сохраняется в аккумуляторе.
        
        :param value: значение для операции AND (может быть регистром или непосредственным значением)
        """
        if isinstance(value, str):
            # Если value - строка, это имя регистра
            operand = self.registers[value]
        else:
            # Иначе это непосредственное значение
            operand = value
        
        # Выполняем операцию AND
        result = self.registers['A'] & operand
        
        # Сохраняем результат в аккумуляторе
        self.registers['A'] = result
        
        # Устанавливаем флаги
        self.set_flag('S', result & 0x80)  # Устанавливаем флаг знака
        self.set_flag('Z', result == 0)    # Устанавливаем флаг нуля
        self.set_flag('H', 1)              # Флаг полупереноса всегда устанавливается
        self.set_flag('P/V', self.parity(result))  # Устанавливаем флаг четности
        self.set_flag('N', 0)              # Сбрасываем флаг вычитания
        self.set_flag('C', 0)              # Сбрасываем флаг переноса

    def push(self, rr):
        """
        Помещает значение регистровой пары в стек.
        
        :param rr: строка, обозначающая пару регистров ('BC', 'DE', 'HL', 'AF')
        """
        value = self.get_register_pair(rr)
        self.registers['SP'] = (self.registers['SP'] - 1) & 0xFFFF
        self.memory[self.registers['SP']] = (value >> 8) & 0xFF  # Сохраняем старший байт
        self.registers['SP'] = (self.registers['SP'] - 1) & 0xFFFF
        self.memory[self.registers['SP']] = value & 0xFF  # Сохраняем младший байт

    def pop(self, rr):
        """
        Извлекает значение из стека и помещает его в регистровую пару.
        
        :param rr: строка, обозначающая пару регистров ('BC', 'DE', 'HL', 'AF')
        """
        low = self.memory[self.registers['SP']]
        self.registers['SP'] = (self.registers['SP'] + 1) & 0xFFFF
        high = self.memory[self.registers['SP']]
        self.registers['SP'] = (self.registers['SP'] + 1) & 0xFFFF
        value = (high << 8) | low
        self.set_register_pair(rr, value)        

    def sbc(self, operand):
        """
        Выполняет вычитание с заемом (SBC A, operand).
        
        :param operand: значение для вычитания (может быть регистром или непосредственным значением)
        """
        if isinstance(operand, str):
            value = self.registers[operand]
        else:
            value = operand
        
        carry = self.get_flag('C')
        result = self.registers['A'] - value - carry
        
        self.set_flag('H', ((self.registers['A'] & 0xF) - (value & 0xF) - carry) < 0)
        self.set_flag('C', result < 0)
        self.set_flag('P/V', ((self.registers['A'] ^ value) & (self.registers['A'] ^ (result & 0xFF)) & 0x80) != 0)
        
        self.registers['A'] = result & 0xFF
        
        self.set_flag('S', self.registers['A'] & 0x80)
        self.set_flag('Z', self.registers['A'] == 0)
        self.set_flag('N', 1)

    def sub(self, operand):
        """
        Выполняет вычитание (SUB A, operand).
        
        :param operand: значение для вычитания (может быть регистром или непосредственным значением)
        """
        if isinstance(operand, str):
            value = self.registers[operand]
        else:
            value = operand
        
        result = self.registers['A'] - value
        
        self.set_flag('H', ((self.registers['A'] & 0xF) - (value & 0xF)) < 0)
        self.set_flag('C', result < 0)
        self.set_flag('P/V', ((self.registers['A'] ^ value) & (self.registers['A'] ^ (result & 0xFF)) & 0x80) != 0)
        
        self.registers['A'] = result & 0xFF
        
        self.set_flag('S', self.registers['A'] & 0x80)
        self.set_flag('Z', self.registers['A'] == 0)
        self.set_flag('N', 1)

    def adc(self, operand):
        """
        Выполняет сложение с переносом (ADC A, operand).
        
        :param operand: значение для сложения (может быть регистром или непосредственным значением)
        """
        if isinstance(operand, str):
            value = self.registers[operand]
        else:
            value = operand
        
        carry = self.get_flag('C')
        result = self.registers['A'] + value + carry
        
        self.set_flag('H', ((self.registers['A'] & 0xF) + (value & 0xF) + carry) > 0xF)
        self.set_flag('C', result > 0xFF)
        self.set_flag('P/V', ((self.registers['A'] ^ ~value) & (self.registers['A'] ^ result) & 0x80) != 0)
        
        self.registers['A'] = result & 0xFF
        
        self.set_flag('S', self.registers['A'] & 0x80)
        self.set_flag('Z', self.registers['A'] == 0)
        self.set_flag('N', 0)        