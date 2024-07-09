from ext_cpu import extCPUClass
from z80_asm import z80_to_asm
class Z80(extCPUClass):
    def __init__(self,memory,io_controller,start_addr=0):super().__init__();self.instructions=self.create_instruction_table();self.memory=memory.memory;self.mem_class=memory;self.io_controller=io_controller
    def execute(self):
        opcode=self.fetch()
        if opcode in self.instructions:self.instructions[opcode]()
        else:raise ValueError(f"Unknown opcode: {opcode:02X}")
    def create_instruction_table(self):
        def ld_r_r(r1,r2):return lambda:self.load_register(r1,self.registers[r2])
        def ld_r_n(r):return lambda:self.load_register(r,self.fetch())
        def ld_r_hl(r):return lambda:self.load_register(r,self.memory[self.get_register_pair('HL')])
        def ld_hl_r(r):return lambda:self.store_memory(self.get_register_pair('HL'),self.registers[r])
        def ld_a_rr(rr):return lambda:self.load_register('A',self.memory[self.get_register_pair(rr)])
        def ld_rr_a(rr):return lambda:self.store_memory(self.get_register_pair(rr),self.registers['A'])
        def add_a_r(r):return lambda:self.add(self.registers[r])
        def adc_a_r(r):return lambda:self.adc(self.registers[r])
        def sub_r(r):return lambda:self.sub(self.registers[r])
        def sbc_a_r(r):return lambda:self.sbc(self.registers[r])
        def and_r(r):return lambda:self.and_a(self.registers[r])
        def xor_r(r):return lambda:self.xor_a(self.registers[r])
        def or_r(r):return lambda:self.or_a(self.registers[r])
        def cp_r(r):return lambda:self.cp(self.registers[r])
        def inc_r(r):return lambda:self.inc_register(r)
        def dec_r(r):return lambda:self.dec_register(r)
        def add_hl_rr(rr):return lambda:self.add_hl(rr)
        def inc_rr(rr):return lambda:self.inc_register_pair(rr)
        def dec_rr(rr):return lambda:self.dec_register_pair(rr)
        return{64:ld_r_r('B','B'),65:ld_r_r('B','C'),66:ld_r_r('B','D'),67:ld_r_r('B','E'),68:ld_r_r('B','H'),69:ld_r_r('B','L'),70:ld_r_hl('B'),71:ld_r_r('B','A'),72:ld_r_r('C','B'),73:ld_r_r('C','C'),74:ld_r_r('C','D'),75:ld_r_r('C','E'),76:ld_r_r('C','H'),77:ld_r_r('C','L'),78:ld_r_hl('C'),79:ld_r_r('C','A'),80:ld_r_r('D','B'),81:ld_r_r('D','C'),82:ld_r_r('D','D'),83:ld_r_r('D','E'),84:ld_r_r('D','H'),85:ld_r_r('D','L'),86:ld_r_hl('D'),87:ld_r_r('D','A'),88:ld_r_r('E','B'),89:ld_r_r('E','C'),90:ld_r_r('E','D'),91:ld_r_r('E','E'),92:ld_r_r('E','H'),93:ld_r_r('E','L'),94:ld_r_hl('E'),95:ld_r_r('E','A'),96:ld_r_r('H','B'),97:ld_r_r('H','C'),98:ld_r_r('H','D'),99:ld_r_r('H','E'),100:ld_r_r('H','H'),101:ld_r_r('H','L'),102:ld_r_hl('H'),103:ld_r_r('H','A'),104:ld_r_r('L','B'),105:ld_r_r('L','C'),106:ld_r_r('L','D'),107:ld_r_r('L','E'),108:ld_r_r('L','H'),109:ld_r_r('L','L'),110:ld_r_hl('L'),111:ld_r_r('L','A'),112:ld_hl_r('B'),113:ld_hl_r('C'),114:ld_hl_r('D'),115:ld_hl_r('E'),116:ld_hl_r('H'),117:ld_hl_r('L'),119:ld_hl_r('A'),120:ld_r_r('A','B'),121:ld_r_r('A','C'),122:ld_r_r('A','D'),123:ld_r_r('A','E'),124:ld_r_r('A','H'),125:ld_r_r('A','L'),126:ld_r_hl('A'),127:ld_r_r('A','A'),6:ld_r_n('B'),14:ld_r_n('C'),22:ld_r_n('D'),30:ld_r_n('E'),38:ld_r_n('H'),46:ld_r_n('L'),54:lambda:self.store_memory(self.get_register_pair('HL'),self.fetch()),62:ld_r_n('A'),10:ld_a_rr('BC'),26:ld_a_rr('DE'),58:lambda:self.load_register('A',self.memory[self.fetch_word()]),2:ld_rr_a('BC'),18:ld_rr_a('DE'),50:lambda:self.store_memory(self.fetch_word(),self.registers['A']),1:lambda:self.load_register_pair('BC',self.fetch_word()),17:lambda:self.load_register_pair('DE',self.fetch_word()),33:lambda:self.load_register_pair('HL',self.fetch_word()),49:lambda:self.load_register_pair('SP',self.fetch_word()),42:lambda:self.load_register_pair('HL',self.memory[self.fetch_word()]),34:lambda:self.store_word(self.fetch_word(),self.get_register_pair('HL')),249:lambda:self.load_register_pair('SP',self.get_register_pair('HL')),197:lambda:self.push('BC'),213:lambda:self.push('DE'),229:lambda:self.push('HL'),245:lambda:self.push('AF'),193:lambda:self.pop('BC'),209:lambda:self.pop('DE'),225:lambda:self.pop('HL'),241:lambda:self.pop('AF'),235:lambda:self.exchange_de_hl(),8:lambda:self.exchange_af(),217:lambda:self.exx(),227:lambda:self.exchange_sp_hl(),128:add_a_r('B'),129:add_a_r('C'),130:add_a_r('D'),131:add_a_r('E'),132:add_a_r('H'),133:add_a_r('L'),134:lambda:self.add(self.memory[self.get_register_pair('HL')]),135:add_a_r('A'),198:lambda:self.add(self.fetch()),136:adc_a_r('B'),137:adc_a_r('C'),138:adc_a_r('D'),139:adc_a_r('E'),140:adc_a_r('H'),141:adc_a_r('L'),142:lambda:self.adc(self.memory[self.get_register_pair('HL')]),143:adc_a_r('A'),206:lambda:self.adc(self.fetch()),144:sub_r('B'),145:sub_r('C'),146:sub_r('D'),147:sub_r('E'),148:sub_r('H'),149:sub_r('L'),150:lambda:self.sub(self.memory[self.get_register_pair('HL')]),151:sub_r('A'),214:lambda:self.sub(self.fetch()),152:sbc_a_r('B'),153:sbc_a_r('C'),154:sbc_a_r('D'),155:sbc_a_r('E'),156:sbc_a_r('H'),157:sbc_a_r('L'),158:lambda:self.sbc(self.memory[self.get_register_pair('HL')]),159:sbc_a_r('A'),222:lambda:self.sbc(self.fetch()),160:and_r('B'),161:and_r('C'),162:and_r('D'),163:and_r('E'),164:and_r('H'),165:and_r('L'),166:lambda:self.and_a(self.memory[self.get_register_pair('HL')]),167:and_r('A'),230:lambda:self.and_a(self.fetch()),168:xor_r('B'),169:xor_r('C'),170:xor_r('D'),171:xor_r('E'),172:xor_r('H'),173:xor_r('L'),174:lambda:self.xor_a(self.memory[self.get_register_pair('HL')]),175:xor_r('A'),238:lambda:self.xor_a(self.fetch()),176:or_r('B'),177:or_r('C'),178:or_r('D'),179:or_r('E'),180:or_r('H'),181:or_r('L'),182:lambda:self.or_a(self.memory[self.get_register_pair('HL')]),183:or_r('A'),246:lambda:self.or_a(self.fetch()),184:cp_r('B'),185:cp_r('C'),186:cp_r('D'),187:cp_r('E'),188:cp_r('H'),189:cp_r('L'),190:lambda:self.cp(self.memory[self.get_register_pair('HL')]),191:cp_r('A'),254:lambda:self.cp(self.fetch()),4:inc_r('B'),12:inc_r('C'),20:inc_r('D'),28:inc_r('E'),36:inc_r('H'),44:inc_r('L'),52:lambda:self.inc_memory(self.get_register_pair('HL')),60:inc_r('A'),5:dec_r('B'),13:dec_r('C'),21:dec_r('D'),29:dec_r('E'),37:dec_r('H'),45:dec_r('L'),53:lambda:self.dec_memory(self.get_register_pair('HL')),61:dec_r('A'),39:lambda:self.daa(),47:lambda:self.cpl(),63:lambda:self.ccf(),55:lambda:self.scf(),0:lambda:None,118:lambda:self.halt(),243:lambda:self.di(),251:lambda:self.ei(),9:add_hl_rr('BC'),25:add_hl_rr('DE'),41:add_hl_rr('HL'),57:add_hl_rr('SP'),3:inc_rr('BC'),19:inc_rr('DE'),35:inc_rr('HL'),51:inc_rr('SP'),11:dec_rr('BC'),27:dec_rr('DE'),43:dec_rr('HL'),59:dec_rr('SP'),7:lambda:self.rlca(),15:lambda:self.rrca(),23:lambda:self.rla(),31:lambda:self.rra(),195:lambda:self.jp(self.fetch_word()),194:lambda:self.jp_cc('NZ',self.fetch_word()),202:lambda:self.jp_cc('Z',self.fetch_word()),210:lambda:self.jp_cc('NC',self.fetch_word()),218:lambda:self.jp_cc('C',self.fetch_word()),233:lambda:self.jp(self.get_register_pair('HL')),24:lambda:self.jr(self.fetch_signed()),32:lambda:self.jr_cc('NZ',self.fetch_signed()),40:lambda:self.jr_cc('Z',self.fetch_signed()),48:lambda:self.jr_cc('NC',self.fetch_signed()),56:lambda:self.jr_cc('C',self.fetch_signed()),16:lambda:self.djnz(self.fetch_signed()),205:lambda:self.call(self.fetch_word()),196:lambda:self.call_cc('NZ',self.fetch_word()),204:lambda:self.call_cc('Z',self.fetch_word()),212:lambda:self.call_cc('NC',self.fetch_word()),220:lambda:self.call_cc('C',self.fetch_word()),201:lambda:self.ret(),192:lambda:self.ret_cc('NZ'),200:lambda:self.ret_cc('Z'),208:lambda:self.ret_cc('NC'),216:lambda:self.ret_cc('C'),199:lambda:self.rst(0),207:lambda:self.rst(8),215:lambda:self.rst(16),223:lambda:self.rst(24),231:lambda:self.rst(32),239:lambda:self.rst(40),247:lambda:self.rst(48),255:lambda:self.rst(56),219:lambda:self.in_a_n(),211:lambda:self.out_n_a(),203:lambda:self.execute_cb(),221:lambda:self.execute_dd(),237:lambda:self.execute_ed(),253:lambda:self.execute_fd()}
    def daa(self):
        a=self.registers['A'];cf=self.get_flag('C');hf=self.get_flag('H')
        if not self.get_flag('N'):
            if cf or a>153:a+=96;self.set_flag('C',1)
            if hf or a&15>9:a+=6
        else:
            if cf:a-=96
            if hf:a-=6
        self.registers['A']=a&255;self.set_flag('S',a&128);self.set_flag('Z',a==0);self.set_flag('H',0);self.set_flag('P/V',self.parity(a))
    def cpl(self):self.registers['A']=~self.registers['A']&255;self.set_flag('H',1);self.set_flag('N',1)
    def ccf(self):self.set_flag('C',not self.get_flag('C'));self.set_flag('H',self.get_flag('C'));self.set_flag('N',0)
    def scf(self):self.set_flag('C',1);self.set_flag('H',0);self.set_flag('N',0)
    def nop(self):0
    def di(self):self.interrupts_enabled=False
    def ei(self):self.interrupts_enabled=True
    def in_a_n(self):port=self.fetch();value=self.io_read(self.registers['A']<<8|port);self.registers['A']=value;self.set_flag('S',value&128);self.set_flag('Z',value==0);self.set_flag('H',0);self.set_flag('P/V',self.parity(value));self.set_flag('N',0)
    def out_n_a(self):port=self.fetch();self.io_write(self.registers['A']<<8|port,self.registers['A'])
    def ld_i_a(self):self.registers['I']=self.registers['A']