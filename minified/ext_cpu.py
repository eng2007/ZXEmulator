from base_cpu import baseCPUClass
class extCPUClass(baseCPUClass):
	def __init__(self):super().__init__()
	def jp(self,address):self.registers['PC']=address&65535
	def jp_cc(self,condition,address):
		if self.check_condition(condition):self.registers['PC']=address&65535
	def jr(self,offset):
		if offset>127:offset-=256
		self.registers['PC']=self.registers['PC']+offset&65535
	def jr_cc(self,condition,offset):
		if self.check_condition(condition):self.jr(offset)
	def djnz(self,offset):
		self.registers['B']=self.registers['B']-1&255
		if self.registers['B']!=0:self.jr(offset)
	def call(self,address):return_address=self.registers['PC'];self.registers['SP']=self.registers['SP']-1&65535;self.memory[self.registers['SP']]=return_address>>8&255;self.registers['SP']=self.registers['SP']-1&65535;self.memory[self.registers['SP']]=return_address&255;self.registers['PC']=address
	def call_cc(self,condition,address):
		if self.check_condition(condition):self.call(address)
	def check_condition(self,condition):
		if condition=='NZ':return not self.get_flag('Z')
		elif condition=='Z':return self.get_flag('Z')
		elif condition=='NC':return not self.get_flag('C')
		elif condition=='C':return self.get_flag('C')
		elif condition=='PO':return not self.get_flag('P/V')
		elif condition=='PE':return self.get_flag('P/V')
		elif condition=='P':return not self.get_flag('S')
		elif condition=='M':return self.get_flag('S')
		else:raise ValueError(f"Неизвестное условие: {condition}")
	def ret(self):low=self.memory[self.registers['SP']];self.registers['SP']=self.registers['SP']+1&65535;high=self.memory[self.registers['SP']];self.registers['SP']=self.registers['SP']+1&65535;self.registers['PC']=high<<8|low
	def retn(self):low=self.memory[self.registers['SP']];self.registers['SP']=self.registers['SP']+1&65535;high=self.memory[self.registers['SP']];self.registers['SP']=self.registers['SP']+1&65535;self.registers['PC']=high<<8|low;self.iff1=self.iff2;self.interrupts_enabled=self.iff1;print('RETN выполнен. PC установлен на',hex(self.registers['PC']));print('IFF1 установлен в',self.iff1)
	def ret_cc(self,condition):
		if self.check_condition(condition):self.ret()
	def rlc(self,value):carry=value>>7;result=(value<<1|carry)&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);self.set_flag('H',0);self.set_flag('3',result&8);self.set_flag('5',result&32);return result
	def rrc(self,value):carry=value&1;result=(value>>1|carry<<7)&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);self.set_flag('H',0);self.set_flag('3',result&8);self.set_flag('5',result&32);return result
	def rlca(self):carry=self.registers['A']>>7;self.registers['A']=(self.registers['A']<<1|carry)&255;self.set_flag('C',carry);self.set_flag('H',0);self.set_flag('N',0);self.set_flag('3',self.registers['A']&8);self.set_flag('5',self.registers['A']&32)
	def rrca(self):carry=self.registers['A']&1;self.registers['A']=(self.registers['A']>>1|carry<<7)&255;self.set_flag('C',carry);self.set_flag('H',0);self.set_flag('N',0);self.set_flag('3',self.registers['A']&8);self.set_flag('5',self.registers['A']&32)
	def rla(self):old_carry=self.get_flag('C');new_carry=self.registers['A']>>7;self.registers['A']=(self.registers['A']<<1|old_carry)&255;self.set_flag('C',new_carry);self.set_flag('H',0);self.set_flag('N',0);self.set_flag('3',self.registers['A']&8);self.set_flag('5',self.registers['A']&32)
	def rra(self):old_carry=self.get_flag('C');new_carry=self.registers['A']&1;self.registers['A']=(self.registers['A']>>1|old_carry<<7)&255;self.set_flag('C',new_carry);self.set_flag('H',0);self.set_flag('N',0);self.set_flag('3',self.registers['A']&8);self.set_flag('5',self.registers['A']&32)
	def rl(self,value):old_carry=self.get_flag('C');carry=value>>7;result=(value<<1|old_carry)&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);self.set_flag('H',0);self.set_flag('3',result&8);self.set_flag('5',result&32);return result
	def rr(self,value):old_carry=self.get_flag('C');carry=value&1;result=(value>>1|old_carry<<7)&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);self.set_flag('H',0);self.set_flag('3',result&8);self.set_flag('5',result&32);return result
	def sla(self,value):carry=value>>7;result=value<<1&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);self.set_flag('H',0);self.set_flag('3',result&8);self.set_flag('5',result&32);return result
	def sra(self,value):carry=value&1;result=(value>>1|value&128)&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);self.set_flag('H',0);self.set_flag('3',result&8);self.set_flag('5',result&32);return result
	def sll(self,value):carry=value>>7;result=(value<<1|1)&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);self.set_flag('H',0);self.set_flag('3',result&8);self.set_flag('5',result&32);return result
	def srl(self,value):carry=value&1;result=value>>1&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);self.set_flag('H',0);self.set_flag('3',result&8);self.set_flag('5',result&32);return result
	def bit(self,bit,value):result=value&1<<bit;self.set_flag('Z',result==0);self.set_flag('H',1);self.set_flag('N',0);self.set_flag('P/V',result==0);self.set_flag('S',bit==7 and result!=0);self.set_flag('3',value&8);self.set_flag('5',value&32)
	def res(self,bit,value):return value&~(1<<bit)
	def set(self,bit,value):return value|1<<bit
	def in_r_c(self,reg):port=self.get_register_pair('BC');value=self.io_read(port);self.registers[reg]=value;self.update_flags(value,zero=True,sign=True,parity=True);self.set_flag('H',0);self.set_flag('3',value&8);self.set_flag('5',value&32)
	def out_c_r(self,reg):port=self.get_register_pair('BC');value=self.registers[reg];self.io_write(port,value)
	def add_hl(self,rp):hl=self.get_register_pair('HL');value=self.get_register_pair(rp);result=hl+value;self.set_register_pair('HL',result&65535);self.set_flag('C',result>65535);self.set_flag('H',(hl&4095)+(value&4095)>4095);self.set_flag('N',0);result_h=result>>8&255;self.set_flag('3',result_h&8);self.set_flag('5',result_h&32)
	def adc_hl(self,rp):hl=self.get_register_pair('HL');value=self.get_register_pair(rp);carry=self.get_flag('C');result=hl+value+carry;self.set_register_pair('HL',result&65535);self.set_flag('C',result>65535);self.set_flag('H',(hl&4095)+(value&4095)+carry>4095);self.set_flag('N',0);overflow=(hl^~value)&(hl^result)&32768!=0;self.set_flag('P/V',overflow);self.set_flag('Z',result&65535==0);self.set_flag('S',result&32768!=0);self.set_flag('5',result&8192!=0);self.set_flag('3',result&2048!=0)
	def sbc_hl(self,rp):hl=self.get_register_pair('HL');value=self.get_register_pair(rp);carry=self.get_flag('C');result=hl-value-carry;self.set_register_pair('HL',result&65535);self.set_flag('C',result<0);self.set_flag('H',(hl&4095)-(value&4095)-carry<0);self.update_flags(result&65535,zero=True,sign=True,parity=True);self.set_flag('N',1);self.set_flag('S',result&32768!=0)
	def neg(self):value=self.registers['A'];result=-value&255;self.registers['A']=result;self.set_flag('C',value!=0);self.set_flag('H',value&15!=0);self.update_flags(result,zero=True,sign=True,parity=True);self.set_flag('N',1);self.set_flag('3',result&8);self.set_flag('5',result&32)
	def rrd(self):a=self.registers['A'];hl=self.get_register_pair('HL');m=self.memory[hl];self.registers['A']=a&240|m&15;self.memory[hl]=(m>>4|a<<4)&255;self.update_flags(self.registers['A'],zero=True,sign=True,parity=True);self.set_flag('H',0);self.set_flag('N',0)
	def rld(self):a=self.registers['A'];hl=self.get_register_pair('HL');m=self.memory[hl];self.registers['A']=a&240|m>>4;self.memory[hl]=(m<<4|a&15)&255;self.update_flags(self.registers['A'],zero=True,sign=True,parity=True);self.set_flag('H',0);self.set_flag('N',0)
	def ldi(self):self._block_transfer(1);self.set_flag('H',0);self.set_flag('N',0);self.set_flag('P/V',self.get_register_pair('BC')!=0);n=self.registers['A']+self.memory[self.get_register_pair('HL')-1];self.set_flag('5',n&2);self.set_flag('3',n&8)
	def ldd(self):self._block_transfer(-1);self.set_flag('H',0);self.set_flag('N',0);self.set_flag('P/V',self.get_register_pair('BC')!=0);n=self.registers['A']+self.memory[self.get_register_pair('HL')+1];self.set_flag('5',n&2);self.set_flag('3',n&8)
	def ldir(self):
		self.ldi()
		if self.get_register_pair('BC')!=0:self.registers['PC']-=2
	def lddr(self):
		self.ldd()
		if self.get_register_pair('BC')!=0:self.registers['PC']-=2
	def _block_transfer(self,direction):hl=self.get_register_pair('HL');de=self.get_register_pair('DE');bc=self.get_register_pair('BC');value=self.memory[hl];self.memory[de]=value;self.set_register_pair('HL',hl+direction&65535);self.set_register_pair('DE',de+direction&65535);self.set_register_pair('BC',bc-1&65535)
	def dec_index_d(self,index_reg):offset=self.fetch_signed();address=self.registers[index_reg]+offset&65535;value=self.memory[address];result=value-1&255;self.memory[address]=result;self.update_flags(result,zero=True,sign=True,halfcarry=True);self.set_flag('S',result&128);self.set_flag('Z',result==0);self.set_flag('H',value&15==0);self.set_flag('P/V',value==128);self.set_flag('N',1);self.set_flag('5',result&32);self.set_flag('3',result&8)
	def inc_index_d(self,index_reg):offset=self.fetch_signed();address=self.registers[index_reg]+offset&65535;value=self.memory[address];result=value+1&255;self.memory[address]=result;self.update_flags(result,zero=True,sign=True,halfcarry=True);self.set_flag('S',result&128);self.set_flag('Z',result==0);self.set_flag('H',value&15==0);self.set_flag('P/V',value==128);self.set_flag('5',result&32);self.set_flag('3',result&8)
	def add_index(self,index_reg,rr):index_value=self.registers[index_reg];rr_value=self.get_register_pair(rr);result=index_value+rr_value&65535;self.registers[index_reg]=result;self.set_flag('N',0);self.set_flag('H',(index_value&4095)+(rr_value&4095)>4095);self.set_flag('C',index_value+rr_value>65535);result_high=result>>8&255;self.set_flag('5',result_high&32);self.set_flag('3',result_high&8)
	def execute_dd(self):opcode=self.fetch();self._execute_indexed('IX',opcode)
	def execute_fd(self):opcode=self.fetch();self._execute_indexed('IY',opcode)
	def _execute_indexed(self,index_reg,opcode):
		if opcode==0:0
		elif opcode==35:self.registers[index_reg]=self.registers[index_reg]+1&65535
		elif opcode==36:high_byte=self.registers[index_reg]>>8&255;result=high_byte+1&255;self.registers[index_reg]=self.registers[index_reg]&255|result<<8;self.set_flag('S',result&128);self.set_flag('Z',result==0);self.set_flag('H',high_byte&15==15);self.set_flag('P/V',result==128);self.set_flag('N',0);self.set_flag('5',result&32);self.set_flag('3',result&8)
		elif opcode==37:value=self.registers[index_reg];high_byte=self.registers[index_reg]>>8&255;result=high_byte-1&255;self.registers[index_reg]=self.registers[index_reg]&255|result<<8;self.set_flag('N',1);result_high=result&255;prev_high=value>>8&255;self.set_flag('H',result_high&15==15);self.set_flag('S',result_high&128);self.set_flag('Z',result_high==0);self.set_flag('P/V',prev_high==128 and result_high==127);self.set_flag('5',result_high&32);self.set_flag('3',result_high&8)
		elif opcode in[9,25,41,57]:rr={9:'BC',25:'DE',41:index_reg,57:'SP'}[opcode];self.add_index(index_reg,rr)
		elif opcode in[33,34,42,43,44,52,53,54,233,249]:
			if opcode==33:self.registers[index_reg]=self.fetch_word()
			elif opcode==34:address=self.fetch_word();self.store_word(address,self.registers[index_reg])
			elif opcode==42:address=self.fetch_word();self.registers[index_reg]=self.memory[address]|self.memory[address+1]<<8
			elif opcode==43:self.registers[index_reg]=self.registers[index_reg]-1&65535
			elif opcode==44:self.inc_index_l(index_reg)
			elif opcode==52:self.inc_index_d(index_reg)
			elif opcode==53:self.dec_index_d(index_reg)
			elif opcode==54:offset=self.fetch_signed();value=self.fetch();address=self.registers[index_reg]+offset&65535;self.memory[address]=value
			elif opcode==233:self.registers['PC']=self.registers[index_reg]
			elif opcode==249:self.registers['SP']=self.registers[index_reg]
		elif opcode==68:high_byte=self.registers[index_reg]>>8&255;self.registers['B']=high_byte
		elif opcode==69:low_byte=self.registers[index_reg]&255;self.registers['B']=low_byte
		elif opcode==76:high_byte=self.registers[index_reg]>>8&255;self.registers['C']=high_byte
		elif opcode==77:low_byte=self.registers[index_reg]&255;self.registers['C']=low_byte
		elif opcode==84:high_byte=self.registers[index_reg]>>8&255;self.registers['D']=high_byte
		elif opcode==85:low_byte=self.registers[index_reg]&255;self.registers['D']=low_byte
		elif opcode==92:high_byte=self.registers[index_reg]>>8&255;self.registers['E']=high_byte
		elif opcode==93:low_byte=self.registers[index_reg]&255;self.registers['E']=low_byte
		elif opcode==96:self.registers[index_reg]=self.registers['B']<<8|self.registers[index_reg]&255
		elif opcode==97:self.registers[index_reg]=self.registers['C']<<8|self.registers[index_reg]&255
		elif opcode==98:self.registers[index_reg]=self.registers['D']<<8|self.registers[index_reg]&255
		elif opcode==99:self.registers[index_reg]=self.registers['E']<<8|self.registers[index_reg]&255
		elif opcode==100:0
		elif opcode==101:self.registers[index_reg]=(self.registers[index_reg]&255)<<8|self.registers[index_reg]&255
		elif opcode==103:self.registers[index_reg]=self.registers['A']<<8|self.registers[index_reg]&255
		elif opcode==104:self.registers[index_reg]=self.registers[index_reg]&65280|self.registers['B']&255
		elif opcode==105:self.registers[index_reg]=self.registers[index_reg]&65280|self.registers['C']&255
		elif opcode==106:self.registers[index_reg]=self.registers[index_reg]&65280|self.registers['D']&255
		elif opcode==107:self.registers[index_reg]=self.registers[index_reg]&65280|self.registers['E']&255
		elif opcode==108:self.registers[index_reg]=self.registers[index_reg]&65280|self.registers[index_reg]>>8&255
		elif opcode==109:0
		elif opcode==111:self.registers[index_reg]=self.registers[index_reg]&65280|self.registers['A']&255
		elif opcode==124:high_byte=self.registers[index_reg]>>8&255;self.registers['A']=high_byte
		elif opcode==125:low_byte=self.registers[index_reg]&255;self.registers['A']=low_byte
		elif opcode&192==64:self._indexed_load(index_reg,opcode)
		elif opcode&192==128:self._indexed_arithmetic(index_reg,opcode)
		elif opcode==203:self._execute_indexed_cb(index_reg)
		elif opcode==225:self.registers[index_reg]=self.memory[self.registers['SP']]|self.memory[self.registers['SP']+1]<<8;self.registers['SP']=self.registers['SP']+2&65535
		elif opcode==227:self.ex_sp_ix(index_reg)
		elif opcode==229:self.push_index_reg(index_reg)
		else:raise ValueError(f"Unsupported {index_reg} instruction: {opcode:02X}")
	def _indexed_load(self,index_reg,opcode):
		if opcode&7==6:reg_index=(opcode&56)>>3;reg=['B','C','D','E','H','L','(HL)','A'][reg_index];offset=self.fetch_signed();address=self.registers[index_reg]+offset&65535;self.registers[reg]=self.memory[address]
		elif opcode&56==48:reg_index=opcode&7;reg=['B','C','D','E','H','L','(HL)','A'][reg_index];offset=self.fetch_signed();address=self.registers[index_reg]+offset&65535;self.memory[address]=self.registers[reg]
	def _indexed_arithmetic(self,index_reg,opcode):
		operation=(opcode&56)>>3;operand=opcode&3
		if operand==0:high_byte=self.registers[index_reg]>>8&255;value=high_byte
		elif operand==1:low_byte=self.registers[index_reg]&255;value=low_byte
		elif operand==2:offset=self.fetch_signed();address=self.registers[index_reg]+offset&65535;value=self.memory[address]
		if operation==0:self.add(value)
		elif operation==1:self.adc(value)
		elif operation==2:self.sub(value)
		elif operation==3:self.sbc(value)
		elif operation==4:self.and_a(value)
		elif operation==5:self.xor_a(value)
		elif operation==6:self.or_a(value)
		elif operation==7:self.cp(value)
	def execute_cb(self):
		opcode=self.fetch();r=['B','C','D','E','H','L','(HL)','A']
		if opcode<64:
			operation=[self.rlc,self.rrc,self.rl,self.rr,self.sla,self.sra,self.sll,self.srl][opcode>>3];operand=r[opcode&7]
			if operand=='(HL)':value=self.memory[self.get_register_pair('HL')];result=operation(value);self.store_memory(self.get_register_pair('HL'),result)
			else:self.registers[operand]=operation(self.registers[operand])
		elif opcode<128:
			bit=opcode>>3&7;operand=r[opcode&7]
			if operand=='(HL)':value=self.memory[self.get_register_pair('HL')]
			else:value=self.registers[operand]
			self.bit(bit,value)
		elif opcode<192:
			bit=opcode>>3&7;operand=r[opcode&7]
			if operand=='(HL)':value=self.memory[self.get_register_pair('HL')];result=self.res(bit,value);self.store_memory(self.get_register_pair('HL'),result)
			else:self.registers[operand]=self.res(bit,self.registers[operand])
		else:
			bit=opcode>>3&7;operand=r[opcode&7]
			if operand=='(HL)':value=self.memory[self.get_register_pair('HL')];result=self.set(bit,value);self.store_memory(self.get_register_pair('HL'),result)
			else:self.registers[operand]=self.set(bit,self.registers[operand])
	def execute_ed(self):
		opcode=self.fetch();ed_instructions={64:lambda:self.in_r_c('B'),65:lambda:self.out_c_r('B'),66:lambda:self.sbc_hl('BC'),67:lambda:self.store_word(self.fetch_word(),self.get_register_pair('BC')),68:lambda:self.neg(),69:lambda:self.retn(),70:lambda:self.im(0),71:lambda:self.ld_i_a(),72:lambda:self.in_r_c('C'),73:lambda:self.out_c_r('C'),74:lambda:self.adc_hl('BC'),75:lambda:self.load_register_pair('BC',self.load_word(self.fetch_word())),76:lambda:self.neg(),77:lambda:self.reti(),79:lambda:self.ld_r_a(),80:lambda:self.in_r_c('D'),81:lambda:self.out_c_r('D'),82:lambda:self.sbc_hl('DE'),83:lambda:self.store_word(self.fetch_word(),self.get_register_pair('DE')),86:lambda:self.im(1),87:lambda:self.ld_a_i(),88:lambda:self.in_r_c('E'),89:lambda:self.out_c_r('E'),90:lambda:self.adc_hl('DE'),91:lambda:self.load_register_pair('DE',self.load_word(self.fetch_word())),94:lambda:self.im(2),95:lambda:self.ld_a_r(),96:lambda:self.in_r_c('H'),97:lambda:self.out_c_r('H'),98:lambda:self.sbc_hl('HL'),99:lambda:self.store_word(self.fetch_word(),self.get_register_pair('HL')),103:lambda:self.rrd(),104:lambda:self.in_r_c('L'),105:lambda:self.out_c_r('L'),106:lambda:self.adc_hl('HL'),107:lambda:self.load_register_pair('HL',self.load_word(self.fetch_word())),111:lambda:self.rld(),114:lambda:self.sbc_hl('SP'),115:lambda:self.store_word(self.fetch_word(),self.get_register_pair('SP')),120:lambda:self.in_r_c('A'),121:lambda:self.out_c_r('A'),122:lambda:self.adc_hl('SP'),123:lambda:self.load_register_pair('SP',self.load_word(self.fetch_word())),160:lambda:self.ldi(),161:lambda:self.cpi(),162:lambda:self.ini(),163:lambda:self.outi(),168:lambda:self.ldd(),169:lambda:self.cpd(),170:lambda:self.ind(),171:lambda:self.outd(),176:lambda:self.ldir(),177:lambda:self.cpir(),178:lambda:self.inir(),179:lambda:self.otir(),184:lambda:self.lddr(),185:lambda:self.cpdr(),186:lambda:self.indr(),187:lambda:self.otdr()}
		if opcode in ed_instructions:ed_instructions[opcode]()
		else:raise ValueError(f"Unknown ED-prefixed opcode: {opcode:02X}")
	def _execute_indexed_cb(self,index_reg):
		offset=self.fetch_signed();opcode=self.fetch();address=self.registers[index_reg]+offset&65535;value=self.memory[address]
		if opcode<64:
			operation=[self.rlc,self.rrc,self.rl,self.rr,self.sla,self.sra,self.sll,self.srl][opcode>>3];result=operation(value);self.memory[address]=result
			if opcode&7!=6:reg=['B','C','D','E','H','L',None,'A'][opcode&7];self.registers[reg]=result
		elif opcode<128:bit=opcode>>3&7;self.bit(bit,value);high_byte=address>>8&255;self.set_flag('5',high_byte&32);self.set_flag('3',high_byte&8)
		elif opcode<192:
			bit=opcode>>3&7;result=self.res(bit,value);self.memory[address]=result
			if opcode&7!=6:reg=['B','C','D','E','H','L',None,'A'][opcode&7];self.registers[reg]=result
		else:
			bit=opcode>>3&7;result=self.set(bit,value);self.memory[address]=result
			if opcode&7!=6:reg=['B','C','D','E','H','L',None,'A'][opcode&7];self.registers[reg]=result
	def rst(self,address):self.registers['SP']=self.registers['SP']-1&65535;self.memory[self.registers['SP']]=self.registers['PC']>>8&255;self.registers['SP']=self.registers['SP']-1&65535;self.memory[self.registers['SP']]=self.registers['PC']&255;self.registers['PC']=address
	def ex_sp_ix(self,index_reg):sp=self.registers['SP'];low=self.memory[sp];high=self.memory[sp+1&65535];stack_value=high<<8|low;ix_value=self.registers[index_reg];self.registers[index_reg]=stack_value;self.memory[sp]=ix_value&255;self.memory[sp+1&65535]=ix_value>>8&255
	def push_index_reg(self,index_reg):self.registers['SP']=self.registers['SP']-1&65535;self.memory[self.registers['SP']]=self.registers[index_reg]>>8&255;self.registers['SP']=self.registers['SP']-1&65535;self.memory[self.registers['SP']]=self.registers[index_reg]&255
	def ld_a_r(self):self.registers['A']=self.registers['R'];result=self.registers['A'];self.set_flag('S',result&128!=0);self.set_flag('Z',result==0);self.set_flag('H',0);self.set_flag('P/V',self.iff2);self.set_flag('N',0);self.set_flag('3',result&8!=0);self.set_flag('5',result&32!=0)
	def ld_r_a(self):self.registers['R']=self.registers['A'];self.registers['R']&=127;self.registers['R']|=self.registers['R']&128
	def ld_a_i(self):self.registers['A']=self.registers['I'];self.set_flag('S',self.registers['A']&128);self.set_flag('Z',self.registers['A']==0);self.set_flag('H',0);self.set_flag('N',0);self.set_flag('P/V',self.iff2);self.set_flag('3',self.registers['A']&8);self.set_flag('5',self.registers['A']&32)
	def reti(self):low=self.memory[self.registers['SP']];self.registers['SP']=self.registers['SP']+1&65535;high=self.memory[self.registers['SP']];self.registers['SP']=self.registers['SP']+1&65535;self.registers['PC']=high<<8|low;self.interrupts_enabled=True;self.cycles+=14
	def inc_index_l(self,index_reg):value=self.registers[index_reg]&255;result=value+1&255;self.registers[index_reg]=self.registers[index_reg]&65280|result;self.set_flag('S',result&128);self.set_flag('Z',result==0);self.set_flag('H',value&15==15);self.set_flag('P/V',value==127);self.set_flag('N',0);self.set_flag('3',result&8);self.set_flag('5',result&32)
	def cpir(self):
		hl=self.get_register_pair('HL');bc=self.get_register_pair('BC');a=self.registers['A'];value=self.memory[hl];result=a-value&255;hl=hl+1&65535;self.set_register_pair('HL',hl);bc=bc-1&65535;self.set_register_pair('BC',bc);self.set_flag('S',result&128);self.set_flag('Z',result==0);self.set_flag('H',(a&15)-(value&15)&16);self.set_flag('P/V',bc!=0);self.set_flag('N',1);self.set_flag('3',result&8);self.set_flag('5',result&32)
		if bc!=0 and result!=0:self.registers['PC']-=2;self.cycles+=21
		else:self.cycles+=16
		self.set_flag('C',a<value)