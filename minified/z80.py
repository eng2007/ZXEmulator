class Z80:
	def __init__(self,memory):self.af=0;self.bc=0;self.de=0;self.hl=0;self.ix=0;self.iy=0;self.sp=0;self.pc=0;self.interrupts_enabled=False;self.memory=[0]*128*1024;self.zero_flag=False;self.sign_flag=False;self.parity_overflow_flag=False;self.half_carry_flag=False;self.add_subtract_flag=False;self.carry_flag=False
	def reset(self):self.af=self.bc=self.de=self.hl=0;self.ix=self.iy=self.sp=self.pc=0;self.interrupts_enabled=False
	def load_memory(self,address,data):self.memory[address:address+len(data)]=data
	def fetch_byte(self):byte=self.memory[self.pc];self.pc+=1;return byte
	def fetch_word(self):low=self.fetch_byte();high=self.fetch_byte();return high<<8|low
	def set_flags(self,value,subtract=False,carry=None):
		self.zero_flag=value==0;self.sign_flag=value&128!=0;self.parity_overflow_flag=bin(value).count('1')%2==0;self.half_carry_flag=value&16!=0;self.add_subtract_flag=subtract
		if carry is not None:self.carry_flag=carry
	def execute_instruction(self):
		opcode=self.fetch_byte()
		if opcode==0:0
		elif opcode==1:self.bc=self.fetch_word()
		elif opcode==2:self.memory[self.bc]=self.af>>8&255
		elif opcode==3:self.bc=self.bc+1&65535
		elif opcode==4:b=(self.bc>>8)+1;self.bc=self.bc&255|(b&255)<<8;self.set_flags(b,subtract=False)
		elif opcode==5:b=(self.bc>>8)-1;self.bc=self.bc&255|(b&255)<<8;self.set_flags(b,subtract=True)
		elif opcode==6:self.bc=self.bc&255|self.fetch_byte()<<8
		elif opcode==10:self.af=self.af&255|self.memory[self.bc]<<8
		elif opcode==11:self.bc=self.bc-1&65535
		elif opcode==12:c=(self.bc&255)+1;self.bc=self.bc&65280|c&255;self.set_flags(c,subtract=False)
		elif opcode==13:c=(self.bc&255)-1;self.bc=self.bc&65280|c&255;self.set_flags(c,subtract=True)
		elif opcode==14:self.bc=self.bc&65280|self.fetch_byte()
		elif opcode==15:a=self.af>>8&255;carry=a&1;a=a>>1|carry<<7;self.af=self.af&255|a<<8;self.set_flags(a,carry=carry)
		elif opcode==17:self.de=self.fetch_word()
		elif opcode==18:self.memory[self.de]=self.af>>8&255
		elif opcode==19:self.de=self.de+1&65535
		elif opcode==20:d=(self.de>>8)+1;self.de=self.de&255|(d&255)<<8;self.set_flags(d,subtract=False)
		elif opcode==21:d=(self.de>>8)-1;self.de=self.de&255|(d&255)<<8;self.set_flags(d,subtract=True)
		elif opcode==22:self.de=self.de&255|self.fetch_byte()<<8
		elif opcode==23:a=self.af>>8&255;carry=self.carry_flag;self.carry_flag=a&128!=0;a=a<<1&255|carry;self.af=self.af&255|a<<8;self.set_flags(a)
		elif opcode==24:
			offset=self.fetch_byte()
			if offset&128:offset=offset-256
			self.pc=self.pc+offset&65535
		elif opcode==25:hl=self.hl+self.de;self.set_flags(hl&65535,carry=hl>65535);self.hl=hl&65535
		elif opcode==26:self.af=self.af&255|self.memory[self.de]<<8
		elif opcode==27:self.de=self.de-1&65535
		elif opcode==28:e=(self.de&255)+1;self.de=self.de&65280|e&255;self.set_flags(e,subtract=False)
		elif opcode==29:e=(self.de&255)-1;self.de=self.de&65280|e&255;self.set_flags(e,subtract=True)
		elif opcode==30:self.de=self.de&65280|self.fetch_byte()
		elif opcode==31:a=self.af>>8&255;carry=self.carry_flag;self.carry_flag=a&1;a=a>>1|carry<<7;self.af=self.af&255|a<<8;self.set_flags(a)
		elif opcode==33:self.hl=self.fetch_word()
		elif opcode==34:addr=self.fetch_word();self.memory[addr]=self.hl&255;self.memory[addr+1]=self.hl>>8&255
		elif opcode==35:self.hl=self.hl+1&65535
		elif opcode==36:h=(self.hl>>8)+1;self.hl=self.hl&255|(h&255)<<8;self.set_flags(h,subtract=False)
		elif opcode==37:h=(self.hl>>8)-1;self.hl=self.hl&255|(h&255)<<8;self.set_flags(h,subtract=True)
		elif opcode==38:self.hl=self.hl&255|self.fetch_byte()<<8
		elif opcode==39:
			a=self.af>>8&255
			if self.add_subtract_flag:
				if self.carry_flag or a>153:a=a+96&255
				if self.half_carry_flag or a&15>9:a=a+6&255
			else:
				if self.carry_flag or a>153:a=a-96&255
				if self.half_carry_flag or a&15>9:a=a-6&255
			self.af=self.af&255|a<<8;self.set_flags(a)
		elif opcode==40:
			offset=self.fetch_byte()
			if self.zero_flag:
				if offset&128:offset=offset-256
				self.pc=self.pc+offset&65535
		elif opcode==41:hl=self.hl+self.hl;self.set_flags(hl&65535,carry=hl>65535);self.hl=hl&65535
		elif opcode==42:addr=self.fetch_word();self.hl=self.memory[addr]|self.memory[addr+1]<<8
		elif opcode==43:self.hl=self.hl-1&65535
		elif opcode==44:l=(self.hl&255)+1;self.hl=self.hl&65280|l&255;self.set_flags(l,subtract=False)
		elif opcode==45:l=(self.hl&255)-1;self.hl=self.hl&65280|l&255;self.set_flags(l,subtract=True)
		elif opcode==46:self.hl=self.hl&65280|self.fetch_byte()
		elif opcode==47:a=self.af>>8&255;a=a^255;self.af=self.af&255|a<<8;self.add_subtract_flag=True;self.half_carry_flag=True
		elif opcode==49:self.sp=self.fetch_word()
		elif opcode==50:addr=self.fetch_word();self.memory[addr]=self.af>>8&255
		elif opcode==51:self.sp=self.sp+1&65535
		elif opcode==52:addr=self.hl;value=self.memory[addr]+1;self.memory[addr]=value&255;self.set_flags(value,subtract=False)
		elif opcode==53:addr=self.hl;value=self.memory[addr]-1;self.memory[addr]=value&255;self.set_flags(value,subtract=True)
		elif opcode==54:self.memory[self.hl]=self.fetch_byte()
		elif opcode==55:self.carry_flag=True;self.add_subtract_flag=False;self.half_carry_flag=False
		elif opcode==56:
			offset=self.fetch_byte()
			if self.carry_flag:
				if offset&128:offset=offset-256
				self.pc=self.pc+offset&65535
		elif opcode==57:hl=self.hl+self.sp;self.set_flags(hl&65535,carry=hl>65535);self.hl=hl&65535
		elif opcode==58:addr=self.fetch_word();self.af=self.af&255|self.memory[addr]<<8
		elif opcode==59:self.sp=self.sp-1&65535
		elif opcode==60:a=(self.af>>8)+1;self.af=self.af&255|(a&255)<<8;self.set_flags(a,subtract=False)
		elif opcode==61:a=(self.af>>8)-1;self.af=self.af&255|(a&255)<<8;self.set_flags(a,subtract=True)
		elif opcode==62:self.af=self.af&255|self.fetch_byte()<<8
		elif opcode==63:self.carry_flag=not self.carry_flag;self.add_subtract_flag=False;self.half_carry_flag=self.carry_flag
		elif opcode==64:0
		elif opcode==65:self.bc=self.bc&255|(self.bc&255)<<8
		elif opcode==66:self.bc=self.bc&255|self.de>>8<<8
		elif opcode==67:self.bc=self.bc&255|(self.de&255)<<8
		elif opcode==68:self.bc=self.bc&255|self.hl>>8<<8
		elif opcode==69:self.bc=self.bc&255|(self.hl&255)<<8
		elif opcode==70:self.bc=self.bc&255|self.memory[self.hl]<<8
		elif opcode==71:self.bc=self.bc&255|self.af&65280
	def run(self,steps):
		for _ in range(steps):self.execute_instruction()