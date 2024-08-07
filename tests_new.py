from new_cpu import Z80
from memory import Memory
from interrupt_controller import InterruptController
from io_controller import IOController


import copy

from time import sleep, time
import sys

import threading
import os
import inspect

# logging.basicConfig(level=logging.INFO)


class Z80Tester(Z80):
    def __init__(self):

        self.memory_class = Memory()
        self.io_controller = IOController(self)
        #self.cpu = Z80(self.memory_class, self.io_controller, 0x0000)
        super().__init__(self.memory_class, self.io_controller, 0x0000)

        self.interrupt_controller = InterruptController(self)
        self.memory = self.memory_class  #.memory

        #self.registers = registers.Registers()
        #self.instructions = instructions.InstructionSet(self.registers)
        #self._memory = bytearray(64*1024)

        self._interrupted = False

    def interrupt(self):
        self._interrupted = True

    def step_instruction(self):
        trace = ""
        ins, args = False, []
        pc = self.registers.PC

        if self._interrupted and self.registers.IFF:
            self.registers.IFF = False
            self._interrupted = False
            if self.registers.IM == 1:
                print("!!! Interrupt  !!!")
                ins, args = self.instructions << 0xCD
                ins, args = self.instructions << 0x38
                ins, args = self.instructions << 0x00
                self.registers.IFF = False
        else:
            while not ins:
                try:
                    ins, args = self.instructions << self._memory[self.registers.PC]
                except:
                    raise Exception("Can't decode instruction.")
                self.registers.PC = util.inc16(self.registers.PC)
            trace += "{0:X} : {1}\n ".format(pc, ins.assembler(args))

        rd = ins.get_read_list(args)
        data = [0] * len(rd)
        for n, i in enumerate(rd):
            if i < 0x10000:
                data[n] = self._memory[i]
            else:
                address = i & 0xFF
                #data[n] = self._iomap.address[address].read(address)
                data[n] = self.registers.A
                print("Read IO "),
                raise Exception("Skip.")
        wrt = ins.execute(data, args)
        for i in wrt:

            if i[0] > 0x10000:
                address = i[0] & 0xFF
                #iomap.address[address].write.emit(address, i[1])
                #self._iomap.address[address].write(address, i[1])
                #print (chr(i[1]))
                print("Write IO "),
                raise Exception("Skip.")
            else:
                try:
                    self._memory[i[0]] = i[1]
                except:
                    print(i)
                    print(trace)
                    raise
        return ins.tstates, trace


if __name__ == '__main__':
    ''' Main Program '''
    mach = Z80Tester()
    infile = file = os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),
                                 "tests.in")
    expectfile = file = os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),
                                     "tests.expected")

    with open(infile, "r") as f:
        tests_in = f.read()
    with open(expectfile, "r") as f:
        tests_expected = f.read()

    fails = passes = 0
    for t, results in zip(tests_in.split("\n\n"), tests_expected.split("\n\n")):
        print("---\n", t, "\n====\n", results, "\n---\n")
        test_lines = t.split("\n")
        test_key = test_lines[0]
        regs = [int(s, 16) for s in test_lines[1].split()]
        mach.set_register_pair('AF', regs[0])
        mach.set_register_pair('BC', regs[1])
        mach.set_register_pair('DE', regs[2])
        mach.set_register_pair('HL', regs[3])

        #mach.af_prime = regs[4]
        #mach.bc_prime = regs[5]
        #mach.de_prime = regs[6]
        #mach.hl_prime = regs[7]
        mach.registers['A_'] = regs[4] >> 8
        mach.registers['F_'] = regs[4] & 0xFF
        mach.registers['B_'] = regs[5] >> 8
        mach.registers['C_'] = regs[5] & 0xFF
        mach.registers['D_'] = regs[6] >> 8
        mach.registers['E_'] = regs[6] & 0xFF
        mach.registers['H_'] = regs[7] >> 8
        mach.registers['L_'] = regs[7] & 0xFF
        mach.registers['IX'] = regs[8]
        mach.registers['IY'] = regs[9]
        mach.registers['SP'] = regs[10]
        mach.registers['PC'] = regs[11]
        regs2 = [s for s in test_lines[2].split()]
        mach.registers['I'] = int(regs2[0], 16)
        mach.registers['R'] = int(regs2[1], 16)
        #mach.registers.IFF = regs2[2] == "1"
        #mach.registers.IFF2 = regs2[3] == "1"
        #mach.registers.IFF2 = regs2[3] == "1"
        #mach.registers.IM = regs2[4] == "1"
        #mach.registers.HALT = regs2[5] == "1"
        tstates = int(regs2[6])
        for memline in test_lines[3:]:
            memsplit = memline.split()
            base = int(memsplit[0], 16)
            for val in memsplit[1:-1]:
                if int(val, 16) == -1:
                    continue
                mach.memory[base] = int(val, 16)
                base += 1

        print(": Test '%s' : " % (str(test_key))),
        if test_key.startswith("27"):
            print("SKIPPED")
            continue
        trace = ""
        taken = 0
        try:
            while taken < tstates:
                #states, asm =  mach.execute_instruction()
                #states = 1
                asm = ''
                mach.execute_instruction(True)
                states = mach.cycles
                if states == 0: states = 1
                taken += states
                trace += "%d/%d\t%d\t" % (taken, tstates, states) + asm
        except Exception as e:
            if e == "Can't decode instruction.":
                print(" - NO INSTRUCTION")
                mach.instructions.reset_composer()
                continue
            elif e == "Skip.":
                print("Skipped.")
                mach.instructions.reset_composer()
                continue
            else:
                print("FAULTY")
                mach.instructions.reset_composer()
                raise

        expected_lines = results.split('\n')
        if expected_lines[0] != test_key:
            print("Test expectation mismatch")
            sys.exit(1)
        i = 1
        while expected_lines[i].startswith(" "):
            i += 1
        regs     = [int(s, 16) for s in expected_lines[i].split()]
        regs_exp = [int(s, 16) for s in expected_lines[i].split()]
        try:
            # if mach.registers.A != regs[0] >> 8:
            #    raise Exception("Bad A register")
            af = mach.get_register_pair('AF') & 0xFFD7
            af_exp = regs[0] & 0xFFD7

            #if mach.get_register_pair('AF') != regs[0]:
            if af != af_exp:
                raise Exception("Bad register AF")
            if mach.get_register_pair('BC') != regs[1]:
                raise Exception("Bad register BC")
            if mach.get_register_pair('DE') != regs[2]:
                raise Exception("Bad register DE")
            if mach.get_register_pair('HL') != regs[3]:
                raise Exception("Bad register HL")
            # if mach.af_prime != regs[4]:
            #    raise Exception("Bad register AF_prime")
            # if mach.bc_prime != regs[5]:
            #    raise Exception("Bad register BC_prime")
            # if mach.de_prime != regs[6]:
            #    raise Exception("Bad register DE_prime")
            # if mach.hl_prime != regs[7]:
            #    raise Exception("Bad register H_prime")
            if mach.registers['A_'] != regs[4] >> 8:
                raise Exception("Bad register")
            if mach.registers['F_'] != regs[4] & 0xFF:
                raise Exception("Bad register")
            if mach.registers['B_'] != regs[5] >> 8:
                raise Exception("Bad register")
            if mach.registers['C_'] != regs[5] & 0xFF:
                raise Exception("Bad register")
            if mach.registers['D_'] != regs[6] >> 8:
                raise Exception("Bad register")
            if mach.registers['E_'] != regs[6] & 0xFF:
                raise Exception("Bad register")
            if mach.registers['H_'] != regs[7] >> 8:
                raise Exception("Bad register")
            if mach.registers['L_'] != regs[7] & 0xFF:
                raise Exception("Bad register")
            if mach.registers['IX'] != regs[8]:
                raise Exception("Bad register IX")
            if mach.registers['IY'] != regs[9]:
                raise Exception("Bad register IY")
            if mach.registers['SP'] != regs[10]:
                raise Exception("Bad register SP")
            if mach.registers['PC'] != regs[11]:
                raise Exception("Bad register PC")
            regs2 = [s for s in expected_lines[i + 1].split()]
            # if mach.registers.I != int(regs2[0], 16):
            #    raise Exception("Bad register")
            # if mach.registers.R != regs2[1]:
            #raise Exception("Bad register")
            # if mach.registers.IFF != (regs2[2] == "1"):
            #    print ("Bad interrups flag flop")
            #    print (regs2[2])
            #    print (mach.registers.IFF)
            #    raise Exception("Bad register")
            # if mach.registers.IFF2 != (regs2[3] == "1"):
            #    print ("Bad interrups flag flop")
            #    print (regs2[3])
            #    print (mach.registers.IFF2)
            #    raise Exception("Bad register")
            # if mach.registers.IFF2 != (regs2[3] == "1"):
            #raise Exception("Bad register")
            # if mach.registers.IM != int(regs2[4]):
            #    raise Exception("Bad register")
            # if mach.registers.HALT != (regs2[5] == "1"):
            #    raise Exception("Bad HALT register. "+str(mach.registers.HALT)+"!="+ str(regs2[5]=='1'))
            # if taken !=  int(regs2[6]):
            #    raise Exception("Bad number of tstates taken.")

            # if mach.registers.F != regs[0] & 0xFF:
            #    raise Exception("Bad F register")

            for memline in expected_lines[i + 3:]:
                memsplit = memline.split()
                base = int(memsplit[0], 16)
                for val in memsplit[1:-1]:
                    if int(val, 16) == -1:
                        continue
                    if mach._memory[base] != int(val, 16):
                        raise Exception("Memory mismatch")
                    base += 1
        except Exception as e:
            #print ("FAILED:",e.message)
            print("FAILED:")
            fails += 1
            # continue
            print("TRACE:")
            print(trace)
            print("")
            flags = ["S", "Z", "F5", "H", "F3", "PV", "N", "C"]
            s = ""
            for i, f in enumerate(flags):
                s += f + ':' + str((regs[0] >> (7 - i)) & 0x01) + ' '
            print("\nTarget flags: ", s)
            s = ""
            for i, f in enumerate(flags):
                s += f + ':' + \
                    str(((mach.get_register_pair('AF') & 0xFF) >> (7 - i)) & 0x01) + ' '
            print("Actual flags: ", s)
            print
            print("--INITIAL--\n", t, "\n--TARGET--\n", results, "\n==--==\n")
            # regs =  ['PC', 'SP', 'I',  'A', 'F', 'B', 'C', 'D', 'E',  'H', 'L',   'IFF']
            # regsr = ['IX', 'IY', 'R','A_', 'F_', 'B_', 'C_','D_', 'E_','H_', 'L_', 'IM']
            regs = ['PC', 'SP', 'I', 'A', 'F', 'B',
                    'C', 'D', 'E', 'H', 'L', 'IFF']
            regsr = ['IX', 'IY', 'R', 'A_', 'F_', 'B_',
                     'C_', 'D_', 'E_', 'H_', 'L_', 'IM']
            # regs =  ['PC', 'SP', 'AF', 'DE', 'BC', 'HL']
            # regsr = ['IX', 'IY', 'AF', 'DE', 'BC', 'HL']
            print("Registers:")
            for rl, rr in zip(regs, regsr):
                if rl == 'PC' or rl == 'SP' or rr =='IX' or rr == 'IY':
                    print(
                        f"{rl}:\t0x{mach.registers[rl]:04X}\t0x{mach.registers[rl]:016b}\t\t{rr}:\t{mach.registers[rr]:04X}\t0x{mach.registers[rr]:016b}")
                    #print  (rl, ": {0:4X}".format( mach.get_register_pair(rl)), "\t\t", rr, ": {0:4X}".format(mach.get_register_pair(rr) ))
                else:
                    print(
                        f"{rl}:\t0x{mach.registers[rl]:02X}\t0x{mach.registers[rl]:08b}\t\t{rr}:\t{mach.registers[rr]:02X}\t0x{mach.registers[rr]:08b}")

            print("Registers expected:")
            print(f"AF: 0x{regs_exp[0]:04X}\t0x{regs_exp[0]:016b}")
            print(f"BC: 0x{regs_exp[1]:04X}\t0x{regs_exp[1]:016b}")
            print(f"DE: 0x{regs_exp[2]:04X}\t0x{regs_exp[2]:016b}")
            print(f"HL: 0x{regs_exp[3]:04X}\t0x{regs_exp[3]:016b}")
            print(f"IX: 0x{regs_exp[8]:04X}\t0x{regs_exp[8]:016b}")
            print(f"IY: 0x{regs_exp[9]:04X}\t0x{regs_exp[9]:016b}")
            print(f"PC: 0x{regs_exp[11]:04X}\t0x{regs_exp[11]:016b}")
            raise
        print("PASSED")
        passes += 1

    print("Failed:", fails)
    print("Passed:", passes)
    print("Passed:", passes)
