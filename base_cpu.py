import logging
class baseCPUClass:
    def __init__(self):self.registers={'A':0,'F':0,'B':0,'C':0,'D':0,'E':0,'H':0,'L':0,'IX':0,'IY':0,'SP':0,'PC':0,'A_':0,'F_':0,'B_':0,'C_':0,'D_':0,'E_':0,'H_':0,'L_':0};self.registers['IX']=0;self.registers['IY']=0;self.registers['I']=0;self.registers['R']=0;self.iff1=False;self.iff2=False;self.memory=[0]*65536;self.interrupts_enabled=False;self.interrupt_mode=0;self.halted=False
    def reset(self):self.registers={'A':0,'F':0,'B':0,'C':0,'D':0,'E':0,'H':0,'L':0,'IX':0,'IY':0,'SP':0,'PC':0,'A_':0,'F_':0,'B_':0,'C_':0,'D_':0,'E_':0,'H_':0,'L_':0};self.registers['IX']=0;self.registers['IY']=0;self.registers['I']=0;self.registers['R']=0;self.interrupts_enabled=False
    def display_registers(self,screen,font,offset):x,y=10,10+offset;text=font.render(f"AF: {self.get_register_pair('AF'):04X}",True,(255,255,255));screen.blit(text,(x,y));y+=20;text=font.render(f"BC: {self.get_register_pair('BC'):04X}",True,(255,255,255));screen.blit(text,(x,y));y+=20;text=font.render(f"DE: {self.get_register_pair('DE'):04X}",True,(255,255,255));screen.blit(text,(x,y));y+=20;text=font.render(f"HL: {self.get_register_pair('HL'):04X}",True,(255,255,255));screen.blit(text,(x,y));y+=20;text=font.render(f"IX: {self.registers['IX']:04X}",True,(255,255,255));screen.blit(text,(x,y));y+=20;text=font.render(f"IY: {self.registers['IY']:04X}",True,(255,255,255));screen.blit(text,(x,y));y+=20;text=font.render(f"PC: {self.registers['PC']:04X}",True,(255,255,255));screen.blit(text,(x,y));y+=20;text=font.render(f"SP: {self.registers['SP']:04X}",True,(255,255,255));screen.blit(text,(x,y));y+=20;text=font.render(f"Interrupts enabled: {self.interrupts_enabled}",True,(255,255,255));screen.blit(text,(x,y));y+=20;text=font.render(f"Interrupt mode: {self.interrupt_mode}",True,(255,255,255));screen.blit(text,(x,y))
    def load_memory(self,address,data):self.memory[address:address+len(data)]=data
    def im(self,mode):
        if mode not in[0,1,2]:raise ValueError(f"Недопустимый режим прерываний: {mode}")
        self.interrupt_mode=mode
        if mode==0:print('Установлен режим прерываний 0')
        elif mode==1:print('Установлен режим прерываний 1')
        else:print('Установлен режим прерываний 2')
    def handle_interrupt(self):
        if not self.interrupts_enabled:return
        if self.halted:self.halted=False;print('Процессор возобновил выполнение после прерывания.')
        self.interrupts_enabled=False;self.registers['SP']=self.registers['SP']-1&65535;self.memory[self.registers['SP']]=self.registers['PC']>>8&255;self.registers['SP']=self.registers['SP']-1&65535;self.memory[self.registers['SP']]=self.registers['PC']&255
        if self.interrupt_mode==0:self.registers['PC']=56
        elif self.interrupt_mode==1:self.registers['PC']=56;logging.info('========== Call interrupt ==========');logging.disable()
        elif self.interrupt_mode==2:vector=self.io_controller.get_data_bus_value();address=self.i<<8|vector;self.registers['PC']=self.memory[address+1]<<8|self.memory[address]
    def handle_nmi(self):self.sp=self.sp-1&65535;self.memory[self.sp]=self.pc>>8&255;self.sp=self.sp-1&65535;self.memory[self.sp]=self.pc&255;self.pc=102
    def fetch(self):value=self.memory[self.registers['PC']];self.registers['PC']+=1;return value
    def fetch_word(self):low=self.fetch();high=self.fetch();return high<<8|low
    def fetch_signed(self):value=self.fetch();return value if value<128 else value-256
    def set_flag(self,flag,value):
        mask={'C':1,'N':2,'P/V':4,'H':16,'Z':64,'S':128}[flag]
        if value:self.registers['F']|=mask
        else:self.registers['F']&=~mask
    def get_flag(self,flag):mask={'C':1,'N':2,'P/V':4,'H':16,'Z':64,'S':128}[flag];return self.registers['F']&mask!=0
    def update_flags(self,result,zero=False,sign=False,parity=False,halfcarry=True):
        if zero:self.set_flag('Z',result==0)
        if sign:self.set_flag('S',result&128)
        if parity:self.set_flag('P/V',bin(result).count('1')%2==0)
        if halfcarry:self.set_flag('H',self.registers['F']&~16|(16 if result&15<self.registers['A']&15 else 0))
    def io_read(self,port):return 0
    def io_write(self,port,value):0
    def load_register(self,reg,value):
        self.registers[reg]=value&255
        if reg=='A':self.update_flags(value)
    def load_register_pair(self,pair,value):high,low=pair;self.registers[high]=value>>8&255;self.registers[low]=value&255
    def get_register_pair(self,pair):high,low=pair;return self.registers[high]<<8|self.registers[low]
    def set_register_pair(self,pair,value):
        value=value&65535
        if pair=='SP':self.registers['SP']=value
        else:high,low=pair;self.registers[high]=value>>8&255;self.registers[low]=value&255
    def store_memory(self,address,value):self.memory[address]=value&255
    def store_word(self,address,value):value=value&65535;self.memory[address]=value&255;self.memory[address+1&65535]=value>>8&255
    def inc_register(self,reg):self.registers[reg]=self.registers[reg]+1&255;self.update_flags(self.registers[reg],zero=True,sign=True,halfcarry=True)
    def dec_register(self,reg):self.registers[reg]=self.registers[reg]-1&255;self.update_flags(self.registers[reg],zero=True,sign=True,halfcarry=True)
    def inc_memory(self,address):self.memory[address]=self.memory[address]+1&255;self.update_flags(self.memory[address],zero=True,sign=True,halfcarry=True)
    def dec_memory(self,address):self.memory[address]=self.memory[address]-1&255;self.update_flags(self.memory[address],zero=True,sign=True,halfcarry=True)
    def inc_register_pair(self,pair):value=self.get_register_pair(pair);value=value+1&65535;self.load_register_pair(pair,value)
    def dec_register_pair(self,pair):value=self.get_register_pair(pair);value=value-1&65535;self.load_register_pair(pair,value)
    def add(self,operand):value=self.registers[operand]if isinstance(operand,str)else operand;result=self.registers['A']+value;self.registers['A']=result&255;self.update_flags(result,zero=True,sign=True,carry=True,halfcarry=True)
    def add_hl(self,pair):hl=self.get_register_pair('HL');value=self.get_register_pair(pair);result=hl+value;self.load_register_pair('HL',result&65535);self.update_flags(result,carry=True,halfcarry=True)
    def rotate_left_carry(self,reg):value=self.registers[reg];carry=value>>7;result=(value<<1|carry)&255;self.registers[reg]=result;self.update_flags(result,carry=True)
    def rotate_right_carry(self,reg):value=self.registers[reg];carry=value&1;result=(value>>1|carry<<7)&255;self.registers[reg]=result;self.update_flags(result,carry=True)
    def exchange_de_hl(self):self.registers['D'],self.registers['H']=self.registers['H'],self.registers['D'];self.registers['E'],self.registers['L']=self.registers['L'],self.registers['E']
    def exchange_af(self):self.registers['A'],self.registers['A_']=self.registers['A_'],self.registers['A'];self.registers['F'],self.registers['F_']=self.registers['F_'],self.registers['F']
    def exx(self):self.registers['B'],self.registers['B_']=self.registers['B_'],self.registers['B'];self.registers['C'],self.registers['C_']=self.registers['C_'],self.registers['C'];self.registers['D'],self.registers['D_']=self.registers['D_'],self.registers['D'];self.registers['E'],self.registers['E_']=self.registers['E_'],self.registers['E'];self.registers['H'],self.registers['H_']=self.registers['H_'],self.registers['H'];self.registers['L'],self.registers['L_']=self.registers['L_'],self.registers['L']
    def exchange_sp_hl(self):sp=self.registers['SP'];l=self.memory[sp];h=self.memory[sp+1&65535];self.memory[sp]=self.registers['L'];self.memory[sp+1&65535]=self.registers['H'];self.registers['L']=l;self.registers['H']=h
    def xor_a(self,operand):
        if isinstance(operand,str):value=self.registers[operand]
        else:value=operand
        result=self.registers['A']^value;self.registers['A']=result&255;self.set_flag('S',result&128);self.set_flag('Z',result==0);self.set_flag('H',0);self.set_flag('P/V',self.parity(result));self.set_flag('N',0);self.set_flag('C',0)
    def or_a(self,operand):
        if isinstance(operand,str):value=self.registers[operand]
        else:value=operand
        result=self.registers['A']|value;self.registers['A']=result&255;self.set_flag('S',result&128);self.set_flag('Z',result==0);self.set_flag('H',0);self.set_flag('P/V',self.parity(result));self.set_flag('N',0);self.set_flag('C',0)
    def parity(self,value):
        value&=255;ones=0
        for i in range(8):
            if value&1<<i:ones+=1
        return ones%2==0
    def jump(self,address):self.registers['PC']=address
    def halt(self):print('Выполнение HALT. Процессор остановлен.');self.halted=True
    def cp(self,value):
        if isinstance(value,str):operand=self.registers[value]
        else:operand=value
        result=self.registers['A']-operand&255;self.set_flag('S',result&128);self.set_flag('Z',result==0);self.set_flag('H',(self.registers['A']&15)-(operand&15)&16);self.set_flag('P/V',(self.registers['A']^operand)&(self.registers['A']^result)&128!=0);self.set_flag('N',1);self.set_flag('C',self.registers['A']<operand)
    def and_a(self,value):
        if isinstance(value,str):operand=self.registers[value]
        else:operand=value
        result=self.registers['A']&operand;self.registers['A']=result;self.set_flag('S',result&128);self.set_flag('Z',result==0);self.set_flag('H',1);self.set_flag('P/V',self.parity(result));self.set_flag('N',0);self.set_flag('C',0)
    def push(self,rr):value=self.get_register_pair(rr);self.registers['SP']=self.registers['SP']-1&65535;self.memory[self.registers['SP']]=value>>8&255;self.registers['SP']=self.registers['SP']-1&65535;self.memory[self.registers['SP']]=value&255
    def pop(self,rr):low=self.memory[self.registers['SP']];self.registers['SP']=self.registers['SP']+1&65535;high=self.memory[self.registers['SP']];self.registers['SP']=self.registers['SP']+1&65535;value=high<<8|low;self.set_register_pair(rr,value)
    def sbc(self,operand):
        if isinstance(operand,str):value=self.registers[operand]
        else:value=operand
        carry=self.get_flag('C');result=self.registers['A']-value-carry;self.set_flag('H',(self.registers['A']&15)-(value&15)-carry<0);self.set_flag('C',result<0);self.set_flag('P/V',(self.registers['A']^value)&(self.registers['A']^result&255)&128!=0);self.registers['A']=result&255;self.set_flag('S',self.registers['A']&128);self.set_flag('Z',self.registers['A']==0);self.set_flag('N',1)
    def sub(self,operand):
        if isinstance(operand,str):value=self.registers[operand]
        else:value=operand
        result=self.registers['A']-value;self.set_flag('H',(self.registers['A']&15)-(value&15)<0);self.set_flag('C',result<0);self.set_flag('P/V',(self.registers['A']^value)&(self.registers['A']^result&255)&128!=0);self.registers['A']=result&255;self.set_flag('S',self.registers['A']&128);self.set_flag('Z',self.registers['A']==0);self.set_flag('N',1)
    def adc(self,operand):
        if isinstance(operand,str):value=self.registers[operand]
        else:value=operand
        carry=self.get_flag('C');result=self.registers['A']+value+carry;self.set_flag('H',(self.registers['A']&15)+(value&15)+carry>15);self.set_flag('C',result>255);self.set_flag('P/V',(self.registers['A']^~value)&(self.registers['A']^result)&128!=0);self.registers['A']=result&255;self.set_flag('S',self.registers['A']&128);self.set_flag('Z',self.registers['A']==0);self.set_flag('N',0)