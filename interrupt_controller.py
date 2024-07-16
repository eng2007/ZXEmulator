class InterruptController:
    def __init__(self, cpu):
        self.cpu = cpu
        self.interrupt_period = 1000  # Примерное значение для частоты прерываний
        self.elapsed_cycles = 0

    def check_and_trigger_interrupt(self):
        # Логика проверки времени или количества циклов
        self.elapsed_cycles += 1
        if self.elapsed_cycles >= self.interrupt_period:
            self.cpu.handle_interrupt()
            self.elapsed_cycles = 0
