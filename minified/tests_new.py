from new_cpu import Z80
from memory import Memory
from interrupt_controller import InterruptController
from io_controller import IOController
import copy
from time import sleep,time
import sys,threading,os,inspect
class Z80Tester(Z80):
	def __init__(self):self.memory_class=Memory();self.io_controller=IOController(self);super().__init__(self.memory_class,self.io_controller,0);self.interrupt_controller=InterruptController(self);self.memory=self.memory_class.memory;self._interrupted=False
	def interrupt(self):self._interrupted=True
	def step_instruction(self):
		trace='';ins,args=False,[];pc=self.registers.PC
		if self._interrupted and self.registers.IFF:
			self.registers.IFF=False;self._interrupted=False
			if self.registers.IM==1:print('!!! Interrupt  !!!');ins,args=self.instructions<<205;ins,args=self.instructions<<56;ins,args=self.instructions<<0;self.registers.IFF=False
		else:
			while not ins:
				try:ins,args=self.instructions<<self._memory[self.registers.PC]
				except:raise Exception("Can't decode instruction.")
				self.registers.PC=util.inc16(self.registers.PC)
			trace+='{0:X} : {1}\n '.format(pc,ins.assembler(args))
		rd=ins.get_read_list(args);data=[0]*len(rd)
		for(n,i)in enumerate(rd):
			if i<65536:data[n]=self._memory[i]
			else:address=i&255;data[n]=self.registers.A;print('Read IO '),;raise Exception('Skip.')
		wrt=ins.execute(data,args)
		for i in wrt:
			if i[0]>65536:address=i[0]&255;print('Write IO '),;raise Exception('Skip.')
			else:
				try:self._memory[i[0]]=i[1]
				except:print(i);print(trace);raise
		return ins.tstates,trace
if __name__=='__main__':
	mach=Z80Tester();infile=file=os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),'tests.in');expectfile=file=os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),'tests.expected')
	with open(infile,'r')as f:tests_in=f.read()
	with open(expectfile,'r')as f:tests_expected=f.read()
	fails=passes=0
	for(t,results)in zip(tests_in.split('\n\n'),tests_expected.split('\n\n')):
		print('---\n',t,'\n====\n',results,'\n---\n');test_lines=t.split('\n');test_key=test_lines[0];regs=[int(s,16)for s in test_lines[1].split()];mach.set_register_pair('AF',regs[0]);mach.set_register_pair('BC',regs[1]);mach.set_register_pair('DE',regs[2]);mach.set_register_pair('HL',regs[3]);mach.registers['A_']=regs[4]>>8;mach.registers['F_']=regs[4]&255;mach.registers['B_']=regs[5]>>8;mach.registers['C_']=regs[5]&255;mach.registers['D_']=regs[6]>>8;mach.registers['E_']=regs[6]&255;mach.registers['H_']=regs[7]>>8;mach.registers['L_']=regs[7]&255;mach.registers['IX']=regs[8];mach.registers['IY']=regs[9];mach.registers['SP']=regs[10];mach.registers['PC']=regs[11];regs2=[s for s in test_lines[2].split()];tstates=int(regs2[6])
		for memline in test_lines[3:]:
			memsplit=memline.split();base=int(memsplit[0],16)
			for val in memsplit[1:-1]:
				if int(val,16)==-1:continue
				mach.memory[base]=int(val,16);base+=1
		print(": Test '%s' : "%str(test_key)),
		if test_key.startswith('27'):print('SKIPPED');continue
		trace='';taken=0
		try:
			while taken<tstates:states=1;asm='';mach.execute_instruction(True);taken+=states;trace+='%d/%d\t%d\t'%(taken,tstates,states)+asm
		except Exception as e:
			if e=="Can't decode instruction.":print(' - NO INSTRUCTION');mach.instructions.reset_composer();continue
			elif e=='Skip.':print('Skipped.');mach.instructions.reset_composer();continue
			else:print('FAULTY');mach.instructions.reset_composer();raise
		expected_lines=results.split('\n')
		if expected_lines[0]!=test_key:print('Test expectation mismatch');sys.exit(1)
		i=1
		while expected_lines[i].startswith(' '):i+=1
		regs=[int(s,16)for s in expected_lines[i].split()];regs_exp=[int(s,16)for s in expected_lines[i].split()]
		try:
			if mach.get_register_pair('AF')!=regs[0]:raise Exception('Bad register AF')
			if mach.get_register_pair('BC')!=regs[1]:raise Exception('Bad register BC')
			if mach.get_register_pair('DE')!=regs[2]:raise Exception('Bad register DE')
			if mach.get_register_pair('HL')!=regs[3]:raise Exception('Bad register HL')
			if mach.registers['A_']!=regs[4]>>8:raise Exception('Bad register')
			if mach.registers['F_']!=regs[4]&255:raise Exception('Bad register')
			if mach.registers['B_']!=regs[5]>>8:raise Exception('Bad register')
			if mach.registers['C_']!=regs[5]&255:raise Exception('Bad register')
			if mach.registers['D_']!=regs[6]>>8:raise Exception('Bad register')
			if mach.registers['E_']!=regs[6]&255:raise Exception('Bad register')
			if mach.registers['H_']!=regs[7]>>8:raise Exception('Bad register')
			if mach.registers['L_']!=regs[7]&255:raise Exception('Bad register')
			if mach.registers['IX']!=regs[8]:raise Exception('Bad register IX')
			if mach.registers['IY']!=regs[9]:raise Exception('Bad register IY')
			if mach.registers['SP']!=regs[10]:raise Exception('Bad register SP')
			regs2=[s for s in expected_lines[i+1].split()]
			for memline in expected_lines[i+3:]:
				memsplit=memline.split();base=int(memsplit[0],16)
				for val in memsplit[1:-1]:
					if int(val,16)==-1:continue
					if mach._memory[base]!=int(val,16):raise Exception('Memory mismatch')
					base+=1
		except Exception as e:
			print('FAILED:');fails+=1;print('TRACE:');print(trace);print('');flags=['S','Z','F5','H','F3','PV','N','C'];s=''
			for(i,f)in enumerate(flags):s+=f+':'+str(regs[0]>>7-i&1)+' '
			print('\nTarget flags: ',s);s=''
			for(i,f)in enumerate(flags):s+=f+':'+str((mach.get_register_pair('AF')&255)>>7-i&1)+' '
			print('Actual flags: ',s);print;print('--INITIAL--\n',t,'\n--TARGET--\n',results,'\n==--==\n');regs=['PC','SP','I','A','F','B','C','D','E','H','L','IFF'];regsr=['IX','IY','R','A_','F_','B_','C_','D_','E_','H_','L_','IM'];print('Registers:')
			for(rl,rr)in zip(regs,regsr):
				if rl=='PC'or rl=='SP'or rr=='IX'or rr=='IY':print(f"{rl}:\t0x{mach.registers[rl]:04X}\t0x{mach.registers[rl]:016b}\t\t{rr}:\t{mach.registers[rr]:04X}\t0x{mach.registers[rr]:016b}")
				else:print(f"{rl}:\t0x{mach.registers[rl]:02X}\t0x{mach.registers[rl]:08b}\t\t{rr}:\t{mach.registers[rr]:02X}\t0x{mach.registers[rr]:08b}")
			print('Registers expected:');print(f"AF: 0x{regs_exp[0]:04X}\t0x{regs_exp[0]:016b}");print(f"BC: 0x{regs_exp[1]:04X}\t0x{regs_exp[1]:016b}");print(f"DE: 0x{regs_exp[2]:04X}\t0x{regs_exp[2]:016b}");print(f"IX: 0x{regs_exp[8]:04X}\t0x{regs_exp[8]:016b}");print(f"IY: 0x{regs_exp[9]:04X}\t0x{regs_exp[9]:016b}");raise
		print('PASSED');passes+=1
	print('Failed:',fails);print('Passed:',passes);print('Passed:',passes)