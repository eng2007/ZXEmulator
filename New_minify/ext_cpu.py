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
    def ret_cc(self,condition):
        if self.check_condition(condition):self.ret()
    def rlc(self,value):carry=value>>7;result=(value<<1|carry)&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);return result
    def rrc(self,value):carry=value&1;result=(value>>1|carry<<7)&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);return result
    def rlca(self):carry=self.registers['A']>>7;self.registers['A']=(self.registers['A']<<1|carry)&255;self.set_flag('C',carry);self.set_flag('H',0);self.set_flag('N',0)
    def rrca(self):carry=self.registers['A']&1;self.registers['A']=(self.registers['A']>>1|carry<<7)&255;self.set_flag('C',carry);self.set_flag('H',0);self.set_flag('N',0)
    def rla(self):old_carry=self.get_flag('C');new_carry=self.registers['A']>>7;self.registers['A']=(self.registers['A']<<1|old_carry)&255;self.set_flag('C',new_carry);self.set_flag('H',0);self.set_flag('N',0)
    def rra(self):old_carry=self.get_flag('C');new_carry=self.registers['A']&1;self.registers['A']=(self.registers['A']>>1|old_carry<<7)&255;self.set_flag('C',new_carry);self.set_flag('H',0);self.set_flag('N',0)
    def rl(self,value):old_carry=self.get_flag('C');carry=value>>7;result=(value<<1|old_carry)&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);return result
    def rr(self,value):old_carry=self.get_flag('C');carry=value&1;result=(value>>1|old_carry<<7)&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);return result
    def sla(self,value):carry=value>>7;result=value<<1&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);return result
    def sra(self,value):carry=value&1;result=(value>>1|value&128)&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);return result
    def sll(self,value):carry=value>>7;result=(value<<1|1)&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);return result
    def srl(self,value):carry=value&1;result=value>>1&255;self.set_flag('C',carry);self.update_flags(result,zero=True,sign=True,parity=True);return result
    def bit(self,bit,value):result=value&1<<bit;self.set_flag('Z',result==0);self.set_flag('H',1);self.set_flag('N',0);self.set_flag('P/V',result==0);self.set_flag('S',bit==7 and result!=0)
    def res(self,bit,value):return value&~(1<<bit)
    def set(self,bit,value):return value|1<<bit
    def in_r_c(self,reg):port=self.registers['C'];value=self.io_read(port);self.registers[reg]=value;self.update_flags(value,zero=True,sign=True,parity=True)
    def out_c_r(self,reg):port=self.registers['C'];value=self.registers[reg];self.io_write(port,value)
    def add_hl(self,rp):hl=self.get_register_pair('HL');value=self.get_register_pair(rp);result=hl+value;self.set_register_pair('HL',result&65535);self.set_flag('C',result>65535);self.set_flag('H',(hl&4095)+(value&4095)>4095);self.set_flag('N',0)
    def adc_hl(self,rp):hl=self.get_register_pair('HL');value=self.get_register_pair(rp);carry=self.get_flag('C');result=hl+value+carry;self.set_register_pair('HL',result&65535);self.set_flag('C',result>65535);self.set_flag('H',(hl&4095)+(value&4095)+carry>4095);self.update_flags(result&65535,zero=True,sign=True,parity=True);self.set_flag('N',0)
    def sbc_hl(self,rp):hl=self.get_register_pair('HL');value=self.get_register_pair(rp);carry=self.get_flag('C');result=hl-value-carry;self.set_register_pair('HL',result&65535);self.set_flag('C',result<0);self.set_flag('H',(hl&4095)-(value&4095)-carry<0);self.update_flags(result&65535,zero=True,sign=True,parity=True);self.set_flag('N',1)
    def neg(self):value=self.registers['A'];result=-value&255;self.registers['A']=result;self.set_flag('C',value!=0);self.set_flag('H',value&15!=0);self.update_flags(result,zero=True,sign=True,parity=True);self.set_flag('N',1)
    def rrd(self):a=self.registers['A'];hl=self.get_register_pair('HL');m=self.memory[hl];self.registers['A']=a&240|m&15;self.memory[hl]=(m>>4|a<<4)&255;self.update_flags(self.registers['A'],zero=True,sign=True,parity=True);self.set_flag('H',0);self.set_flag('N',0)
    def rld(self):a=self.registers['A'];hl=self.get_register_pair('HL');m=self.memory[hl];self.registers['A']=a&240|m>>4;self.memory[hl]=(m<<4|a&15)&255;self.update_flags(self.registers['A'],zero=True,sign=True,parity=True);self.set_flag('H',0);self.set_flag('N',0)
    def ldi(self):self._block_transfer(1);self.set_flag('H',0);self.set_flag('N',0);self.set_flag('P/V',self.get_register_pair('BC')!=0)
    def ldd(self):self._block_transfer(-1);self.set_flag('H',0);self.set_flag('N',0);self.set_flag('P/V',self.get_register_pair('BC')!=0)
    def ldir(self):
        self.ldi()
        if self.get_register_pair('BC')!=0:self.registers['PC']-=2
    def lddr(self):
        self.ldd()
        if self.get_register_pair('BC')!=0:self.registers['PC']-=2
    def _block_transfer(self,direction):hl=self.get_register_pair('HL');de=self.get_register_pair('DE');bc=self.get_register_pair('BC');value=self.memory[hl];self.memory[de]=value;self.set_register_pair('HL',hl+direction&65535);self.set_register_pair('DE',de+direction&65535);self.set_register_pair('BC',bc-1&65535)
    def dec_index_d(self,index_reg):offset=self.fetch_signed();address=self.registers[index_reg]+offset&65535;value=self.memory[address];result=value-1&255;self.memory[address]=result;self.update_flags(result,zero=True,sign=True,halfcarry=True);self.set_flag('N',1)
    def inc_index_d(self,index_reg):offset=self.fetch_signed();address=self.registers[index_reg]+offset&65535;value=self.memory[address];result=value+1&255;self.memory[address]=result;self.update_flags(result,zero=True,sign=True,halfcarry=True)
    def add_index(self,index_reg,rr):index_value=self.registers[index_reg];rr_value=self.get_register_pair(rr);result=index_value+rr_value&65535;self.registers[index_reg]=result;self.set_flag('N',0);self.set_flag('H',(index_value&4095)+(rr_value&4095)>4095);self.set_flag('C',index_value+rr_value>65535)
    def execute_dd(self):opcode=self.fetch();self._execute_indexed('IX',opcode)
    def execute_fd(self):opcode=self.fetch();self._execute_indexed('IY',opcode)
    def _execute_indexed(self,index_reg,opcode):
        if opcode in[9,25,41,57]:rr={9:'BC',25:'DE',41:index_reg,57:'SP'}[opcode];self.add_index(index_reg,rr)
        elif opcode in[33,34,42,52,53,54,233,249]:
            if opcode==33:self.registers[index_reg]=self.fetch_word()
            elif opcode==34:address=self.fetch_word();self.store_word(address,self.registers[index_reg])
            elif opcode==42:address=self.fetch_word();self.registers[index_reg]=self.memory[address]|self.memory[address+1]<<8
            elif opcode==52:self.inc_index_d(index_reg)
            elif opcode==53:self.dec_index_d(index_reg)
            elif opcode==54:offset=self.fetch_signed();value=self.fetch();address=self.registers[index_reg]+offset&65535;self.memory[address]=value
            elif opcode==233:self.registers['PC']=self.registers[index_reg]
            elif opcode==249:self.registers['SP']=self.registers[index_reg]
        elif opcode&192==64:self._indexed_load(index_reg,opcode)
        elif opcode&192==128:self._indexed_arithmetic(index_reg,opcode)
        elif opcode==203:self._execute_indexed_cb(index_reg)
        else:raise ValueError(f"Unsupported {index_reg} instruction: {opcode:02X}")
    def _indexed_load(self,index_reg,opcode):
        reg=['B','C','D','E','H','L',None,'A'][opcode&7]
        if opcode&7==6:offset=self.fetch_signed();address=self.registers[index_reg]+offset&65535;self.registers[reg]=self.memory[address]
        elif opcode&56==48:offset=self.fetch_signed();address=self.registers[index_reg]+offset&65535;self.memory[address]=self.registers[reg]
    def _indexed_arithmetic(self,index_reg,opcode):
        operation=(opcode&56)>>3;offset=self.fetch_signed();address=self.registers[index_reg]+offset&65535;value=self.memory[address]
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
        opcode=self.fetch();ed_instructions={64:lambda:self.in_r_c('B'),65:lambda:self.out_c_r('B'),66:lambda:self.sbc_hl('BC'),67:lambda:self.store_word(self.fetch_word(),self.get_register_pair('BC')),68:lambda:self.neg(),69:lambda:self.retn(),70:lambda:self.im(0),71:lambda:self.ld_i_a(),72:lambda:self.in_r_c('C'),73:lambda:self.out_c_r('C'),74:lambda:self.adc_hl('BC'),75:lambda:self.load_register_pair('BC',self.memory[self.fetch_word()]),77:lambda:self.reti(),79:lambda:self.ld_r_a(),80:lambda:self.in_r_c('D'),81:lambda:self.out_c_r('D'),82:lambda:self.sbc_hl('DE'),83:lambda:self.store_word(self.fetch_word(),self.get_register_pair('DE')),86:lambda:self.im(1),87:lambda:self.ld_a_i(),88:lambda:self.in_r_c('E'),89:lambda:self.out_c_r('E'),90:lambda:self.adc_hl('DE'),91:lambda:self.load_register_pair('DE',self.memory[self.fetch_word()]),94:lambda:self.im(2),95:lambda:self.ld_a_r(),96:lambda:self.in_r_c('H'),97:lambda:self.out_c_r('H'),98:lambda:self.sbc_hl('HL'),99:lambda:self.store_word(self.fetch_word(),self.get_register_pair('HL')),103:lambda:self.rrd(),104:lambda:self.in_r_c('L'),105:lambda:self.out_c_r('L'),106:lambda:self.adc_hl('HL'),107:lambda:self.load_register_pair('HL',self.memory[self.fetch_word()]),111:lambda:self.rld(),114:lambda:self.sbc_hl('SP'),115:lambda:self.store_word(self.fetch_word(),self.get_register_pair('SP')),120:lambda:self.in_r_c('A'),121:lambda:self.out_c_r('A'),122:lambda:self.adc_hl('SP'),123:lambda:self.load_register_pair('SP',self.memory[self.fetch_word()]),160:lambda:self.ldi(),161:lambda:self.cpi(),162:lambda:self.ini(),163:lambda:self.outi(),168:lambda:self.ldd(),169:lambda:self.cpd(),170:lambda:self.ind(),171:lambda:self.outd(),176:lambda:self.ldir(),177:lambda:self.cpir(),178:lambda:self.inir(),179:lambda:self.otir(),184:lambda:self.lddr(),185:lambda:self.cpdr(),186:lambda:self.indr(),187:lambda:self.otdr()}
        if opcode in ed_instructions:ed_instructions[opcode]()
        else:raise ValueError(f"Unknown ED-prefixed opcode: {opcode:02X}")
    def _execute_indexed_cb(self,index_reg):
        offset=self.fetch_signed();opcode=self.fetch();address=self.registers[index_reg]+offset&65535;value=self.memory[address]
        if opcode<64:
            operation=[self.rlc,self.rrc,self.rl,self.rr,self.sla,self.sra,self.sll,self.srl][opcode>>3];result=operation(value);self.memory[address]=result
            if opcode&7!=6:reg=['B','C','D','E','H','L',None,'A'][opcode&7];self.registers[reg]=result
        elif opcode<128:bit=opcode>>3&7;self.bit(bit,value)
        elif opcode<192:
            bit=opcode>>3&7;result=self.res(bit,value);self.memory[address]=result
            if opcode&7!=6:reg=['B','C','D','E','H','L',None,'A'][opcode&7];self.registers[reg]=result
        else:
            bit=opcode>>3&7;result=self.set(bit,value);self.memory[address]=result
            if opcode&7!=6:reg=['B','C','D','E','H','L',None,'A'][opcode&7];self.registers[reg]=result
    def rst(self,address):self.registers['SP']=self.registers['SP']-1&65535;self.memory[self.registers['SP']]=self.registers['PC']>>8&255;self.registers['SP']=self.registers['SP']-1&65535;self.memory[self.registers['SP']]=self.registers['PC']&255;self.registers['PC']=address