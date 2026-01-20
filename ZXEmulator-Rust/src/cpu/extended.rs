//! Z80 extended instruction sets (CB, DD, ED, FD prefixes)

use super::{Z80, Flags};
use super::flags::*;

impl Z80 {
    /// Execute CB-prefixed instruction
    pub fn execute_cb(&mut self) -> u8 {
        let opcode = self.fetch();
        let reg = opcode & 0x07;
        let op = (opcode >> 3) & 0x07;
        let bit = (opcode >> 3) & 0x07;
        
        // Get value
        let value = match reg {
            0 => self.b(),
            1 => self.c(),
            2 => self.d(),
            3 => self.e(),
            4 => self.h(),
            5 => self.l(),
            6 => self.read_byte(self.hl),
            7 => self.a(),
            _ => unreachable!()
        };
        
        let cycles = if reg == 6 { 15 } else { 8 };
        
        let result = match opcode >> 6 {
            0 => { // Rotation/shift
                match op {
                    0 => self.rlc(value),
                    1 => self.rrc(value),
                    2 => self.rl(value),
                    3 => self.rr(value),
                    4 => self.sla(value),
                    5 => self.sra(value),
                    6 => self.sll(value), // Undocumented
                    7 => self.srl(value),
                    _ => unreachable!()
                }
            }
            1 => { // BIT
                self.bit(bit, value);
                return if reg == 6 { 12 } else { 8 };
            }
            2 => value & !(1 << bit), // RES
            3 => value | (1 << bit),  // SET
            _ => unreachable!()
        };
        
        // Store result
        match reg {
            0 => self.set_b(result),
            1 => self.set_c(result),
            2 => self.set_d(result),
            3 => self.set_e(result),
            4 => self.set_h(result),
            5 => self.set_l(result),
            6 => self.write_byte(self.hl, result),
            7 => self.set_a(result),
            _ => unreachable!()
        };
        
        cycles
    }

    /// Execute DD-prefixed instruction (IX)
    pub fn execute_dd(&mut self) -> u8 {
        let opcode = self.fetch();
        match opcode {
            0xCB => self.execute_ddcb(),
            _ => self.execute_index(opcode, true)
        }
    }

    /// Execute FD-prefixed instruction (IY)
    pub fn execute_fd(&mut self) -> u8 {
        let opcode = self.fetch();
        match opcode {
            0xCB => self.execute_fdcb(),
            _ => self.execute_index(opcode, false)
        }
    }

    /// Execute IX/IY instruction (shared logic)
    fn execute_index(&mut self, opcode: u8, is_ix: bool) -> u8 {
        let idx = if is_ix { self.ix } else { self.iy };
        
        match opcode {
            // ADD IX/IY,BC
            0x09 => {
                let result = self.add_idx(idx, self.bc);
                if is_ix { self.ix = result; } else { self.iy = result; }
                15
            }
            // ADD IX/IY,DE
            0x19 => {
                let result = self.add_idx(idx, self.de);
                if is_ix { self.ix = result; } else { self.iy = result; }
                15
            }
            // LD IX/IY,nn
            0x21 => {
                let val = self.fetch_word();
                if is_ix { self.ix = val; } else { self.iy = val; }
                14
            }
            // LD (nn),IX/IY
            0x22 => {
                let addr = self.fetch_word();
                self.write_word(addr, idx);
                20
            }
            // INC IX/IY
            0x23 => {
                if is_ix { self.ix = self.ix.wrapping_add(1); } 
                else { self.iy = self.iy.wrapping_add(1); }
                10
            }
            // INC IXH/IYH
            0x24 => {
                let v = (idx >> 8) as u8;
                let r = v.wrapping_add(1);
                if is_ix { self.ix = (self.ix & 0xFF) | ((r as u16) << 8); }
                else { self.iy = (self.iy & 0xFF) | ((r as u16) << 8); }
                let flags = inc_flags(v, r) | (Flags::from_bits_truncate(self.f()) & Flags::C);
                self.set_f(flags.bits());
                8
            }
            // DEC IXH/IYH
            0x25 => {
                let v = (idx >> 8) as u8;
                let r = v.wrapping_sub(1);
                if is_ix { self.ix = (self.ix & 0xFF) | ((r as u16) << 8); }
                else { self.iy = (self.iy & 0xFF) | ((r as u16) << 8); }
                let flags = dec_flags(v, r) | (Flags::from_bits_truncate(self.f()) & Flags::C);
                self.set_f(flags.bits());
                8
            }
            // LD IXH/IYH,n
            0x26 => {
                let n = self.fetch();
                if is_ix { self.ix = (self.ix & 0xFF) | ((n as u16) << 8); }
                else { self.iy = (self.iy & 0xFF) | ((n as u16) << 8); }
                11
            }
            // ADD IX/IY,IX/IY
            0x29 => {
                let result = self.add_idx(idx, idx);
                if is_ix { self.ix = result; } else { self.iy = result; }
                15
            }
            // LD IX/IY,(nn)
            0x2A => {
                let addr = self.fetch_word();
                let val = self.read_word(addr);
                if is_ix { self.ix = val; } else { self.iy = val; }
                20
            }
            // DEC IX/IY
            0x2B => {
                if is_ix { self.ix = self.ix.wrapping_sub(1); }
                else { self.iy = self.iy.wrapping_sub(1); }
                10
            }
            // INC IXL/IYL
            0x2C => {
                let v = (idx & 0xFF) as u8;
                let r = v.wrapping_add(1);
                if is_ix { self.ix = (self.ix & 0xFF00) | (r as u16); }
                else { self.iy = (self.iy & 0xFF00) | (r as u16); }
                let flags = inc_flags(v, r) | (Flags::from_bits_truncate(self.f()) & Flags::C);
                self.set_f(flags.bits());
                8
            }
            // DEC IXL/IYL
            0x2D => {
                let v = (idx & 0xFF) as u8;
                let r = v.wrapping_sub(1);
                if is_ix { self.ix = (self.ix & 0xFF00) | (r as u16); }
                else { self.iy = (self.iy & 0xFF00) | (r as u16); }
                let flags = dec_flags(v, r) | (Flags::from_bits_truncate(self.f()) & Flags::C);
                self.set_f(flags.bits());
                8
            }
            // LD IXL/IYL,n
            0x2E => {
                let n = self.fetch();
                if is_ix { self.ix = (self.ix & 0xFF00) | (n as u16); }
                else { self.iy = (self.iy & 0xFF00) | (n as u16); }
                11
            }
            // INC (IX/IY+d)
            0x34 => {
                let d = self.fetch() as i8;
                let addr = idx.wrapping_add(d as u16);
                let v = self.read_byte(addr);
                let r = v.wrapping_add(1);
                self.write_byte(addr, r);
                let flags = inc_flags(v, r) | (Flags::from_bits_truncate(self.f()) & Flags::C);
                self.set_f(flags.bits());
                23
            }
            // DEC (IX/IY+d)
            0x35 => {
                let d = self.fetch() as i8;
                let addr = idx.wrapping_add(d as u16);
                let v = self.read_byte(addr);
                let r = v.wrapping_sub(1);
                self.write_byte(addr, r);
                let flags = dec_flags(v, r) | (Flags::from_bits_truncate(self.f()) & Flags::C);
                self.set_f(flags.bits());
                23
            }
            // LD (IX/IY+d),n
            0x36 => {
                let d = self.fetch() as i8;
                let n = self.fetch();
                let addr = idx.wrapping_add(d as u16);
                self.write_byte(addr, n);
                19
            }
            // ADD IX/IY,SP
            0x39 => {
                let result = self.add_idx(idx, self.sp);
                if is_ix { self.ix = result; } else { self.iy = result; }
                15
            }
            // LD r,(IX/IY+d) - 0x46,0x4E,0x56,0x5E,0x66,0x6E,0x7E
            0x46 | 0x4E | 0x56 | 0x5E | 0x66 | 0x6E | 0x7E => {
                let d = self.fetch() as i8;
                let addr = idx.wrapping_add(d as u16);
                let v = self.read_byte(addr);
                match opcode {
                    0x46 => self.set_b(v),
                    0x4E => self.set_c(v),
                    0x56 => self.set_d(v),
                    0x5E => self.set_e(v),
                    0x66 => self.set_h(v),
                    0x6E => self.set_l(v),
                    0x7E => self.set_a(v),
                    _ => {}
                }
                19
            }
            // LD (IX/IY+d),r - 0x70-0x77 (except 0x76)
            0x70..=0x75 | 0x77 => {
                let d = self.fetch() as i8;
                let addr = idx.wrapping_add(d as u16);
                let v = match opcode & 0x07 {
                    0 => self.b(),
                    1 => self.c(),
                    2 => self.d(),
                    3 => self.e(),
                    4 => self.h(),
                    5 => self.l(),
                    7 => self.a(),
                    _ => 0
                };
                self.write_byte(addr, v);
                19
            }
            // ALU A,(IX/IY+d)
            0x86 | 0x8E | 0x96 | 0x9E | 0xA6 | 0xAE | 0xB6 | 0xBE => {
                let d = self.fetch() as i8;
                let addr = idx.wrapping_add(d as u16);
                let v = self.read_byte(addr);
                match opcode {
                    0x86 => self.add_a(v, false),
                    0x8E => { let c = self.flag(Flags::C); self.add_a(v, c); }
                    0x96 => self.sub_a(v, false),
                    0x9E => { let c = self.flag(Flags::C); self.sub_a(v, c); }
                    0xA6 => self.and_a(v),
                    0xAE => self.xor_a(v),
                    0xB6 => self.or_a(v),
                    0xBE => self.cp_a(v),
                    _ => {}
                }
                19
            }
            // POP IX/IY
            0xE1 => {
                let val = self.pop();
                if is_ix { self.ix = val; } else { self.iy = val; }
                14
            }
            // EX (SP),IX/IY
            0xE3 => {
                let v = self.read_word(self.sp);
                self.write_word(self.sp, idx);
                if is_ix { self.ix = v; } else { self.iy = v; }
                23
            }
            // PUSH IX/IY
            0xE5 => {
                self.push(idx);
                15
            }
            // JP (IX/IY)
            0xE9 => {
                self.pc = idx;
                8
            }
            // LD SP,IX/IY
            0xF9 => {
                self.sp = idx;
                10
            }
            _ => {
                // Treat as NOP for unimplemented
                4
            }
        }
    }

    /// Execute DDCB-prefixed instruction
    fn execute_ddcb(&mut self) -> u8 {
        let d = self.fetch() as i8;
        let opcode = self.fetch();
        let addr = self.ix.wrapping_add(d as u16);
        self.execute_indexed_cb(opcode, addr)
    }

    /// Execute FDCB-prefixed instruction
    fn execute_fdcb(&mut self) -> u8 {
        let d = self.fetch() as i8;
        let opcode = self.fetch();
        let addr = self.iy.wrapping_add(d as u16);
        self.execute_indexed_cb(opcode, addr)
    }

    /// Execute indexed CB instruction
    fn execute_indexed_cb(&mut self, opcode: u8, addr: u16) -> u8 {
        let value = self.read_byte(addr);
        let bit = (opcode >> 3) & 0x07;
        let op = (opcode >> 3) & 0x07;
        
        let result = match opcode >> 6 {
            0 => { // Rotation/shift
                match op {
                    0 => self.rlc(value),
                    1 => self.rrc(value),
                    2 => self.rl(value),
                    3 => self.rr(value),
                    4 => self.sla(value),
                    5 => self.sra(value),
                    6 => self.sll(value),
                    7 => self.srl(value),
                    _ => value
                }
            }
            1 => { // BIT
                self.bit(bit, value);
                return 20;
            }
            2 => value & !(1 << bit), // RES
            3 => value | (1 << bit),  // SET
            _ => value
        };
        
        self.write_byte(addr, result);
        
        // Some instructions also copy to register
        let reg = opcode & 0x07;
        if opcode >> 6 != 1 && reg != 6 {
            match reg {
                0 => self.set_b(result),
                1 => self.set_c(result),
                2 => self.set_d(result),
                3 => self.set_e(result),
                4 => self.set_h(result),
                5 => self.set_l(result),
                7 => self.set_a(result),
                _ => {}
            }
        }
        
        23
    }

    /// Execute ED-prefixed instruction
    pub fn execute_ed(&mut self) -> u8 {
        let opcode = self.fetch();
        
        match opcode {
            // IN B,(C)
            0x40 => { let v = self.io_read(self.bc); self.set_b(v); self.set_in_flags(v); 12 }
            // OUT (C),B
            0x41 => { self.io_write(self.bc, self.b()); 12 }
            // SBC HL,BC
            0x42 => { self.sbc_hl(self.bc); 15 }
            // LD (nn),BC
            0x43 => { let addr = self.fetch_word(); self.write_word(addr, self.bc); 20 }
            // NEG
            0x44 | 0x4C | 0x54 | 0x5C | 0x64 | 0x6C | 0x74 | 0x7C => { self.neg(); 8 }
            // RETN
            0x45 | 0x55 | 0x5D | 0x65 | 0x6D | 0x75 | 0x7D => { self.retn(); 14 }
            // IM 0
            0x46 | 0x4E | 0x66 | 0x6E => { self.im = 0; 8 }
            // LD I,A
            0x47 => { self.i = self.a(); 9 }
            // IN C,(C)
            0x48 => { let v = self.io_read(self.bc); self.set_c(v); self.set_in_flags(v); 12 }
            // OUT (C),C
            0x49 => { self.io_write(self.bc, self.c()); 12 }
            // ADC HL,BC
            0x4A => { self.adc_hl(self.bc); 15 }
            // LD BC,(nn)
            0x4B => { let addr = self.fetch_word(); self.bc = self.read_word(addr); 20 }
            // RETI
            0x4D => { self.reti(); 14 }
            // LD R,A
            0x4F => { self.r = self.a(); 9 }
            // IN D,(C)
            0x50 => { let v = self.io_read(self.bc); self.set_d(v); self.set_in_flags(v); 12 }
            // OUT (C),D
            0x51 => { self.io_write(self.bc, self.d()); 12 }
            // SBC HL,DE
            0x52 => { self.sbc_hl(self.de); 15 }
            // LD (nn),DE
            0x53 => { let addr = self.fetch_word(); self.write_word(addr, self.de); 20 }
            // IM 1
            0x56 | 0x76 => { self.im = 1; 8 }
            // LD A,I
            0x57 => { self.ld_a_ir(self.i); 9 }
            // IN E,(C)
            0x58 => { let v = self.io_read(self.bc); self.set_e(v); self.set_in_flags(v); 12 }
            // OUT (C),E
            0x59 => { self.io_write(self.bc, self.e()); 12 }
            // ADC HL,DE
            0x5A => { self.adc_hl(self.de); 15 }
            // LD DE,(nn)
            0x5B => { let addr = self.fetch_word(); self.de = self.read_word(addr); 20 }
            // IM 2
            0x5E | 0x7E => { self.im = 2; 8 }
            // LD A,R
            0x5F => { self.ld_a_ir(self.r); 9 }
            // IN H,(C)
            0x60 => { let v = self.io_read(self.bc); self.set_h(v); self.set_in_flags(v); 12 }
            // OUT (C),H
            0x61 => { self.io_write(self.bc, self.h()); 12 }
            // SBC HL,HL
            0x62 => { let hl = self.hl; self.sbc_hl(hl); 15 }
            // LD (nn),HL (ED version)
            0x63 => { let addr = self.fetch_word(); self.write_word(addr, self.hl); 20 }
            // RRD
            0x67 => { self.rrd(); 18 }
            // IN L,(C)
            0x68 => { let v = self.io_read(self.bc); self.set_l(v); self.set_in_flags(v); 12 }
            // OUT (C),L
            0x69 => { self.io_write(self.bc, self.l()); 12 }
            // ADC HL,HL
            0x6A => { let hl = self.hl; self.adc_hl(hl); 15 }
            // LD HL,(nn) (ED version)
            0x6B => { let addr = self.fetch_word(); self.hl = self.read_word(addr); 20 }
            // RLD
            0x6F => { self.rld(); 18 }
            // IN (C) / IN F,(C)
            0x70 => { let v = self.io_read(self.bc); self.set_in_flags(v); 12 }
            // OUT (C),0
            0x71 => { self.io_write(self.bc, 0); 12 }
            // SBC HL,SP
            0x72 => { self.sbc_hl(self.sp); 15 }
            // LD (nn),SP
            0x73 => { let addr = self.fetch_word(); self.write_word(addr, self.sp); 20 }
            // IN A,(C)
            0x78 => { let v = self.io_read(self.bc); self.set_a(v); self.set_in_flags(v); 12 }
            // OUT (C),A
            0x79 => { self.io_write(self.bc, self.a()); 12 }
            // ADC HL,SP
            0x7A => { self.adc_hl(self.sp); 15 }
            // LD SP,(nn)
            0x7B => { let addr = self.fetch_word(); self.sp = self.read_word(addr); 20 }
            // LDI
            0xA0 => { self.ldi(); 16 }
            // CPI
            0xA1 => { self.cpi(); 16 }
            // INI
            0xA2 => { self.ini(); 16 }
            // OUTI
            0xA3 => { self.outi(); 16 }
            // LDD
            0xA8 => { self.ldd(); 16 }
            // CPD
            0xA9 => { self.cpd(); 16 }
            // IND
            0xAA => { self.ind(); 16 }
            // OUTD
            0xAB => { self.outd(); 16 }
            // LDIR
            0xB0 => { self.ldi(); if self.bc != 0 { self.pc = self.pc.wrapping_sub(2); 21 } else { 16 } }
            // CPIR
            0xB1 => { 
                self.cpi(); 
                if self.bc != 0 && !self.flag(Flags::Z) { self.pc = self.pc.wrapping_sub(2); 21 } else { 16 } 
            }
            // INIR
            0xB2 => { self.ini(); if self.b() != 0 { self.pc = self.pc.wrapping_sub(2); 21 } else { 16 } }
            // OTIR
            0xB3 => { self.outi(); if self.b() != 0 { self.pc = self.pc.wrapping_sub(2); 21 } else { 16 } }
            // LDDR
            0xB8 => { self.ldd(); if self.bc != 0 { self.pc = self.pc.wrapping_sub(2); 21 } else { 16 } }
            // CPDR
            0xB9 => { 
                self.cpd(); 
                if self.bc != 0 && !self.flag(Flags::Z) { self.pc = self.pc.wrapping_sub(2); 21 } else { 16 } 
            }
            // INDR
            0xBA => { self.ind(); if self.b() != 0 { self.pc = self.pc.wrapping_sub(2); 21 } else { 16 } }
            // OTDR
            0xBB => { self.outd(); if self.b() != 0 { self.pc = self.pc.wrapping_sub(2); 21 } else { 16 } }
            
            _ => 8 // NOP for undefined
        }
    }

    // Rotation/shift helpers
    fn rlc(&mut self, value: u8) -> u8 {
        let carry = value >> 7;
        let result = (value << 1) | carry;
        self.set_rot_flags(result, carry != 0);
        result
    }

    fn rrc(&mut self, value: u8) -> u8 {
        let carry = value & 1;
        let result = (value >> 1) | (carry << 7);
        self.set_rot_flags(result, carry != 0);
        result
    }

    fn rl(&mut self, value: u8) -> u8 {
        let old_carry = if self.flag(Flags::C) { 1 } else { 0 };
        let new_carry = value >> 7;
        let result = (value << 1) | old_carry;
        self.set_rot_flags(result, new_carry != 0);
        result
    }

    fn rr(&mut self, value: u8) -> u8 {
        let old_carry = if self.flag(Flags::C) { 0x80 } else { 0 };
        let new_carry = value & 1;
        let result = (value >> 1) | old_carry;
        self.set_rot_flags(result, new_carry != 0);
        result
    }

    fn sla(&mut self, value: u8) -> u8 {
        let carry = value >> 7;
        let result = value << 1;
        self.set_rot_flags(result, carry != 0);
        result
    }

    fn sra(&mut self, value: u8) -> u8 {
        let carry = value & 1;
        let result = (value >> 1) | (value & 0x80);
        self.set_rot_flags(result, carry != 0);
        result
    }

    fn sll(&mut self, value: u8) -> u8 {
        let carry = value >> 7;
        let result = (value << 1) | 1;
        self.set_rot_flags(result, carry != 0);
        result
    }

    fn srl(&mut self, value: u8) -> u8 {
        let carry = value & 1;
        let result = value >> 1;
        self.set_rot_flags(result, carry != 0);
        result
    }

    fn set_rot_flags(&mut self, result: u8, carry: bool) {
        let mut flags = sz53_flags(result) | parity_flag(result);
        if carry { flags |= Flags::C; }
        self.set_f(flags.bits());
    }

    fn bit(&mut self, bit: u8, value: u8) {
        let test = value & (1 << bit);
        let mut f = self.f() & Flags::C.bits();
        f |= Flags::H.bits();
        if test == 0 { f |= Flags::Z.bits() | Flags::PV.bits(); }
        if bit == 7 && test != 0 { f |= Flags::S.bits(); }
        f |= value & (Flags::F3 | Flags::F5).bits();
        self.set_f(f);
    }

    fn add_idx(&mut self, idx: u16, value: u16) -> u16 {
        let result = idx.wrapping_add(value);
        let mut f = self.f() & (Flags::S | Flags::Z | Flags::PV).bits();
        if (idx as u32) + (value as u32) > 0xFFFF { f |= Flags::C.bits(); }
        if (idx & 0x0FFF) + (value & 0x0FFF) > 0x0FFF { f |= Flags::H.bits(); }
        f |= (result >> 8) as u8 & (Flags::F3 | Flags::F5).bits();
        self.set_f(f);
        result
    }

    fn set_in_flags(&mut self, value: u8) {
        let flags = sz53_flags(value) | parity_flag(value) | (Flags::from_bits_truncate(self.f()) & Flags::C);
        self.set_f(flags.bits());
    }

    fn neg(&mut self) {
        let a = self.a();
        let result = 0u8.wrapping_sub(a);
        self.set_a(result);
        let flags = sub_flags(0, a, result, false);
        self.set_f(flags.bits());
    }

    fn retn(&mut self) {
        self.iff1 = self.iff2;
        let return_addr = self.pop();
        
        // Auto-disable TR-DOS ROM when returning to address >= 0x4000
        if self.mem().is_trdos_rom_active() && return_addr >= 0x4000 {
            println!("[CPU] RETN to 0x{:04X}, exiting TR-DOS ROM", return_addr);
            self.mem_mut().disable_trdos_rom();
        }
        
        self.pc = return_addr;
    }

    fn reti(&mut self) {
        self.iff1 = self.iff2;
        let return_addr = self.pop();
        
        // Auto-disable TR-DOS ROM when returning to address >= 0x4000
        if self.mem().is_trdos_rom_active() && return_addr >= 0x4000 {
            println!("[CPU] RETI to 0x{:04X}, exiting TR-DOS ROM", return_addr);
            self.mem_mut().disable_trdos_rom();
        }
        
        self.pc = return_addr;
    }

    fn ld_a_ir(&mut self, value: u8) {
        self.set_a(value);
        let mut flags = sz53_flags(value) | (Flags::from_bits_truncate(self.f()) & Flags::C);
        if self.iff2 { flags |= Flags::PV; }
        self.set_f(flags.bits());
    }

    fn rrd(&mut self) {
        let a = self.a();
        let mem = self.read_byte(self.hl);
        let new_a = (a & 0xF0) | (mem & 0x0F);
        let new_mem = ((a & 0x0F) << 4) | (mem >> 4);
        self.set_a(new_a);
        self.write_byte(self.hl, new_mem);
        let flags = sz53_flags(new_a) | parity_flag(new_a) | (Flags::from_bits_truncate(self.f()) & Flags::C);
        self.set_f(flags.bits());
    }

    fn rld(&mut self) {
        let a = self.a();
        let mem = self.read_byte(self.hl);
        let new_a = (a & 0xF0) | (mem >> 4);
        let new_mem = ((mem & 0x0F) << 4) | (a & 0x0F);
        self.set_a(new_a);
        self.write_byte(self.hl, new_mem);
        let flags = sz53_flags(new_a) | parity_flag(new_a) | (Flags::from_bits_truncate(self.f()) & Flags::C);
        self.set_f(flags.bits());
    }

    fn adc_hl(&mut self, value: u16) {
        let hl = self.hl;
        let carry = if self.flag(Flags::C) { 1u16 } else { 0 };
        let result = hl.wrapping_add(value).wrapping_add(carry);
        self.hl = result;
        
        let mut f = Flags::empty();
        if result == 0 { f |= Flags::Z; }
        if result & 0x8000 != 0 { f |= Flags::S; }
        f |= Flags::undoc((result >> 8) as u8);
        if (hl as u32) + (value as u32) + (carry as u32) > 0xFFFF { f |= Flags::C; }
        if (hl & 0x0FFF) + (value & 0x0FFF) + carry > 0x0FFF { f |= Flags::H; }
        // Overflow
        let shl = (hl as i16) as i32;
        let sv = (value as i16) as i32;
        let sum = shl + sv + (carry as i32);
        if sum < -32768 || sum > 32767 { f |= Flags::PV; }
        self.set_f(f.bits());
    }

    fn sbc_hl(&mut self, value: u16) {
        let hl = self.hl;
        let carry = if self.flag(Flags::C) { 1u16 } else { 0 };
        let result = hl.wrapping_sub(value).wrapping_sub(carry);
        self.hl = result;
        
        let mut f = Flags::N;
        if result == 0 { f |= Flags::Z; }
        if result & 0x8000 != 0 { f |= Flags::S; }
        f |= Flags::undoc((result >> 8) as u8);
        if (hl as i32) - (value as i32) - (carry as i32) < 0 { f |= Flags::C; }
        if (hl & 0x0FFF) < (value & 0x0FFF) + carry { f |= Flags::H; }
        // Overflow
        let shl = (hl as i16) as i32;
        let sv = (value as i16) as i32;
        let diff = shl - sv - (carry as i32);
        if diff < -32768 || diff > 32767 { f |= Flags::PV; }
        self.set_f(f.bits());
    }

    // Block instructions
    fn ldi(&mut self) {
        let val = self.read_byte(self.hl);
        self.write_byte(self.de, val);
        self.hl = self.hl.wrapping_add(1);
        self.de = self.de.wrapping_add(1);
        self.bc = self.bc.wrapping_sub(1);
        
        let mut f = self.f() & (Flags::S | Flags::Z | Flags::C).bits();
        if self.bc != 0 { f |= Flags::PV.bits(); }
        let n = val.wrapping_add(self.a());
        f |= (n & 0x08) >> 3 << 3; // F3 from bit 3
        f |= (n & 0x02) << 4;       // F5 from bit 1
        self.set_f(f);
    }

    fn ldd(&mut self) {
        let val = self.read_byte(self.hl);
        self.write_byte(self.de, val);
        self.hl = self.hl.wrapping_sub(1);
        self.de = self.de.wrapping_sub(1);
        self.bc = self.bc.wrapping_sub(1);
        
        let mut f = self.f() & (Flags::S | Flags::Z | Flags::C).bits();
        if self.bc != 0 { f |= Flags::PV.bits(); }
        let n = val.wrapping_add(self.a());
        f |= (n & 0x08) >> 3 << 3;
        f |= (n & 0x02) << 4;
        self.set_f(f);
    }

    fn cpi(&mut self) {
        let val = self.read_byte(self.hl);
        let result = self.a().wrapping_sub(val);
        self.hl = self.hl.wrapping_add(1);
        self.bc = self.bc.wrapping_sub(1);
        
        let mut f = (self.f() & Flags::C.bits()) | Flags::N.bits();
        if result == 0 { f |= Flags::Z.bits(); }
        if result & 0x80 != 0 { f |= Flags::S.bits(); }
        if (self.a() & 0x0F) < (val & 0x0F) { f |= Flags::H.bits(); }
        if self.bc != 0 { f |= Flags::PV.bits(); }
        let n = result.wrapping_sub(if f & Flags::H.bits() != 0 { 1 } else { 0 });
        f |= (n & 0x08) >> 3 << 3;
        f |= (n & 0x02) << 4;
        self.set_f(f);
    }

    fn cpd(&mut self) {
        let val = self.read_byte(self.hl);
        let result = self.a().wrapping_sub(val);
        self.hl = self.hl.wrapping_sub(1);
        self.bc = self.bc.wrapping_sub(1);
        
        let mut f = (self.f() & Flags::C.bits()) | Flags::N.bits();
        if result == 0 { f |= Flags::Z.bits(); }
        if result & 0x80 != 0 { f |= Flags::S.bits(); }
        if (self.a() & 0x0F) < (val & 0x0F) { f |= Flags::H.bits(); }
        if self.bc != 0 { f |= Flags::PV.bits(); }
        let n = result.wrapping_sub(if f & Flags::H.bits() != 0 { 1 } else { 0 });
        f |= (n & 0x08) >> 3 << 3;
        f |= (n & 0x02) << 4;
        self.set_f(f);
    }

    fn ini(&mut self) {
        let val = self.io_read(self.bc);
        self.write_byte(self.hl, val);
        self.hl = self.hl.wrapping_add(1);
        let b = self.b().wrapping_sub(1);
        self.set_b(b);
        
        let mut f = if b == 0 { Flags::Z.bits() } else { 0 };
        f |= Flags::N.bits();
        if b & 0x80 != 0 { f |= Flags::S.bits(); }
        self.set_f(f);
    }

    fn ind(&mut self) {
        let val = self.io_read(self.bc);
        self.write_byte(self.hl, val);
        self.hl = self.hl.wrapping_sub(1);
        let b = self.b().wrapping_sub(1);
        self.set_b(b);
        
        let mut f = if b == 0 { Flags::Z.bits() } else { 0 };
        f |= Flags::N.bits();
        if b & 0x80 != 0 { f |= Flags::S.bits(); }
        self.set_f(f);
    }

    fn outi(&mut self) {
        let val = self.read_byte(self.hl);
        let b = self.b().wrapping_sub(1);
        self.set_b(b);
        self.io_write(self.bc, val);
        self.hl = self.hl.wrapping_add(1);
        
        let mut f = if b == 0 { Flags::Z.bits() } else { 0 };
        f |= Flags::N.bits();
        if b & 0x80 != 0 { f |= Flags::S.bits(); }
        self.set_f(f);
    }

    fn outd(&mut self) {
        let val = self.read_byte(self.hl);
        let b = self.b().wrapping_sub(1);
        self.set_b(b);
        self.io_write(self.bc, val);
        self.hl = self.hl.wrapping_sub(1);
        
        let mut f = if b == 0 { Flags::Z.bits() } else { 0 };
        f |= Flags::N.bits();
        if b & 0x80 != 0 { f |= Flags::S.bits(); }
        self.set_f(f);
    }
}
