class IOController:
	def __init__(self,emulator):self.emulator=emulator;self.border_color=0;self.last_7ffd_value=0
	def write_port(self,port,value):
		if port&255==254:self.border_color=value&7;self.emulator.set_border(self.border_color)
		elif port==32765:self.handle_7ffd_write(value)
	def handle_7ffd_write(self,value):
		if not self.last_7ffd_value&32:self.last_7ffd_value=value;ram_bank=value&7;self.emulator.memory.paged_banks[3]=ram_bank;self.emulator.memory.current_rom=value>>4&1;screen_bank=5 if value&8 else 7;self.emulator.memory.paged_banks[1]=screen_bank;print(f"Memory configuration changed: RAM bank {ram_bank}, ROM {self.emulator.memory.current_rom}, Screen bank {screen_bank}")
	def read_port(self,port):
		if port&255==254:self.emulator.keyboard.read_keyboard();result=self.emulator.keyboard.read_port_fe(port);return result
		if port==27:return 125
		if port==227:return 193
		if port==226:return 113
		if port==107:return 41
		return 255