//! Z80 base instruction set implementation

use super::{Z80, Flags};
use super::flags::*;

impl Z80 {
    /// Execute opcode and return cycles taken
    pub fn execute_opcode(&mut self, opcode: u8) -> u8 {
        match opcode {
            // NOP
            0x00 => 4,
            
            // LD BC,nn
            0x01 => { self.bc = self.fetch_word(); 10 }
            // LD (BC),A
            0x02 => { self.write_byte(self.bc, self.a()); 7 }
            // INC BC
            0x03 => { self.bc = self.bc.wrapping_add(1); 6 }
            // INC B
            0x04 => { let v = self.b(); self.inc_r8(v, |s, r| s.set_b(r)); 4 }
            // DEC B
            0x05 => { let v = self.b(); self.dec_r8(v, |s, r| s.set_b(r)); 4 }
            // LD B,n
            0x06 => { let n = self.fetch(); self.set_b(n); 7 }
            // RLCA
            0x07 => { self.rlca(); 4 }
            // EX AF,AF'
            0x08 => { std::mem::swap(&mut self.af, &mut self.af_prime); 4 }
            // ADD HL,BC
            0x09 => { self.add_hl(self.bc); 11 }
            // LD A,(BC)
            0x0A => { let v = self.read_byte(self.bc); self.set_a(v); 7 }
            // DEC BC
            0x0B => { self.bc = self.bc.wrapping_sub(1); 6 }
            // INC C
            0x0C => { let v = self.c(); self.inc_r8(v, |s, r| s.set_c(r)); 4 }
            // DEC C
            0x0D => { let v = self.c(); self.dec_r8(v, |s, r| s.set_c(r)); 4 }
            // LD C,n
            0x0E => { let n = self.fetch(); self.set_c(n); 7 }
            // RRCA
            0x0F => { self.rrca(); 4 }
            
            // DJNZ d
            0x10 => { self.djnz() }
            // LD DE,nn
            0x11 => { self.de = self.fetch_word(); 10 }
            // LD (DE),A
            0x12 => { self.write_byte(self.de, self.a()); 7 }
            // INC DE
            0x13 => { self.de = self.de.wrapping_add(1); 6 }
            // INC D
            0x14 => { let v = self.d(); self.inc_r8(v, |s, r| s.set_d(r)); 4 }
            // DEC D
            0x15 => { let v = self.d(); self.dec_r8(v, |s, r| s.set_d(r)); 4 }
            // LD D,n
            0x16 => { let n = self.fetch(); self.set_d(n); 7 }
            // RLA
            0x17 => { self.rla(); 4 }
            // JR d
            0x18 => { self.jr(); 12 }
            // ADD HL,DE
            0x19 => { self.add_hl(self.de); 11 }
            // LD A,(DE)
            0x1A => { let v = self.read_byte(self.de); self.set_a(v); 7 }
            // DEC DE
            0x1B => { self.de = self.de.wrapping_sub(1); 6 }
            // INC E
            0x1C => { let v = self.e(); self.inc_r8(v, |s, r| s.set_e(r)); 4 }
            // DEC E
            0x1D => { let v = self.e(); self.dec_r8(v, |s, r| s.set_e(r)); 4 }
            // LD E,n
            0x1E => { let n = self.fetch(); self.set_e(n); 7 }
            // RRA
            0x1F => { self.rra(); 4 }
            
            // JR NZ,d
            0x20 => { self.jr_cc(!self.flag(Flags::Z)) }
            // LD HL,nn
            0x21 => { self.hl = self.fetch_word(); 10 }
            // LD (nn),HL
            0x22 => { let addr = self.fetch_word(); self.write_word(addr, self.hl); 16 }
            // INC HL
            0x23 => { self.hl = self.hl.wrapping_add(1); 6 }
            // INC H
            0x24 => { let v = self.h(); self.inc_r8(v, |s, r| s.set_h(r)); 4 }
            // DEC H
            0x25 => { let v = self.h(); self.dec_r8(v, |s, r| s.set_h(r)); 4 }
            // LD H,n
            0x26 => { let n = self.fetch(); self.set_h(n); 7 }
            // DAA
            0x27 => { self.daa(); 4 }
            // JR Z,d
            0x28 => { self.jr_cc(self.flag(Flags::Z)) }
            // ADD HL,HL
            0x29 => { let hl = self.hl; self.add_hl(hl); 11 }
            // LD HL,(nn)
            0x2A => { let addr = self.fetch_word(); self.hl = self.read_word(addr); 16 }
            // DEC HL
            0x2B => { self.hl = self.hl.wrapping_sub(1); 6 }
            // INC L
            0x2C => { let v = self.l(); self.inc_r8(v, |s, r| s.set_l(r)); 4 }
            // DEC L
            0x2D => { let v = self.l(); self.dec_r8(v, |s, r| s.set_l(r)); 4 }
            // LD L,n
            0x2E => { let n = self.fetch(); self.set_l(n); 7 }
            // CPL
            0x2F => { self.cpl(); 4 }
            
            // JR NC,d
            0x30 => { self.jr_cc(!self.flag(Flags::C)) }
            // LD SP,nn
            0x31 => { self.sp = self.fetch_word(); 10 }
            // LD (nn),A
            0x32 => { let addr = self.fetch_word(); self.write_byte(addr, self.a()); 13 }
            // INC SP
            0x33 => { self.sp = self.sp.wrapping_add(1); 6 }
            // INC (HL)
            0x34 => { let addr = self.hl; let v = self.read_byte(addr); self.inc_mem(addr, v); 11 }
            // DEC (HL)
            0x35 => { let addr = self.hl; let v = self.read_byte(addr); self.dec_mem(addr, v); 11 }
            // LD (HL),n
            0x36 => { let n = self.fetch(); self.write_byte(self.hl, n); 10 }
            // SCF
            0x37 => { self.scf(); 4 }
            // JR C,d
            0x38 => { self.jr_cc(self.flag(Flags::C)) }
            // ADD HL,SP
            0x39 => { self.add_hl(self.sp); 11 }
            // LD A,(nn)
            0x3A => { let addr = self.fetch_word(); self.set_a(self.read_byte(addr)); 13 }
            // DEC SP
            0x3B => { self.sp = self.sp.wrapping_sub(1); 6 }
            // INC A
            0x3C => { let v = self.a(); self.inc_r8(v, |s, r| s.set_a(r)); 4 }
            // DEC A
            0x3D => { let v = self.a(); self.dec_r8(v, |s, r| s.set_a(r)); 4 }
            // LD A,n
            0x3E => { let n = self.fetch(); self.set_a(n); 7 }
            // CCF
            0x3F => { self.ccf(); 4 }
            
            // LD r,r' instructions (0x40-0x7F)
            0x40 => 4, // LD B,B
            0x41 => { self.set_b(self.c()); 4 }
            0x42 => { self.set_b(self.d()); 4 }
            0x43 => { self.set_b(self.e()); 4 }
            0x44 => { self.set_b(self.h()); 4 }
            0x45 => { self.set_b(self.l()); 4 }
            0x46 => { self.set_b(self.read_byte(self.hl)); 7 }
            0x47 => { self.set_b(self.a()); 4 }
            
            0x48 => { self.set_c(self.b()); 4 }
            0x49 => 4, // LD C,C
            0x4A => { self.set_c(self.d()); 4 }
            0x4B => { self.set_c(self.e()); 4 }
            0x4C => { self.set_c(self.h()); 4 }
            0x4D => { self.set_c(self.l()); 4 }
            0x4E => { self.set_c(self.read_byte(self.hl)); 7 }
            0x4F => { self.set_c(self.a()); 4 }
            
            0x50 => { self.set_d(self.b()); 4 }
            0x51 => { self.set_d(self.c()); 4 }
            0x52 => 4, // LD D,D
            0x53 => { self.set_d(self.e()); 4 }
            0x54 => { self.set_d(self.h()); 4 }
            0x55 => { self.set_d(self.l()); 4 }
            0x56 => { self.set_d(self.read_byte(self.hl)); 7 }
            0x57 => { self.set_d(self.a()); 4 }
            
            0x58 => { self.set_e(self.b()); 4 }
            0x59 => { self.set_e(self.c()); 4 }
            0x5A => { self.set_e(self.d()); 4 }
            0x5B => 4, // LD E,E
            0x5C => { self.set_e(self.h()); 4 }
            0x5D => { self.set_e(self.l()); 4 }
            0x5E => { self.set_e(self.read_byte(self.hl)); 7 }
            0x5F => { self.set_e(self.a()); 4 }
            
            0x60 => { self.set_h(self.b()); 4 }
            0x61 => { self.set_h(self.c()); 4 }
            0x62 => { self.set_h(self.d()); 4 }
            0x63 => { self.set_h(self.e()); 4 }
            0x64 => 4, // LD H,H
            0x65 => { self.set_h(self.l()); 4 }
            0x66 => { self.set_h(self.read_byte(self.hl)); 7 }
            0x67 => { self.set_h(self.a()); 4 }
            
            0x68 => { self.set_l(self.b()); 4 }
            0x69 => { self.set_l(self.c()); 4 }
            0x6A => { self.set_l(self.d()); 4 }
            0x6B => { self.set_l(self.e()); 4 }
            0x6C => { self.set_l(self.h()); 4 }
            0x6D => 4, // LD L,L
            0x6E => { self.set_l(self.read_byte(self.hl)); 7 }
            0x6F => { self.set_l(self.a()); 4 }
            
            0x70 => { self.write_byte(self.hl, self.b()); 7 }
            0x71 => { self.write_byte(self.hl, self.c()); 7 }
            0x72 => { self.write_byte(self.hl, self.d()); 7 }
            0x73 => { self.write_byte(self.hl, self.e()); 7 }
            0x74 => { self.write_byte(self.hl, self.h()); 7 }
            0x75 => { self.write_byte(self.hl, self.l()); 7 }
            // HALT
            0x76 => { self.halted = true; 4 }
            0x77 => { self.write_byte(self.hl, self.a()); 7 }
            
            0x78 => { self.set_a(self.b()); 4 }
            0x79 => { self.set_a(self.c()); 4 }
            0x7A => { self.set_a(self.d()); 4 }
            0x7B => { self.set_a(self.e()); 4 }
            0x7C => { self.set_a(self.h()); 4 }
            0x7D => { self.set_a(self.l()); 4 }
            0x7E => { self.set_a(self.read_byte(self.hl)); 7 }
            0x7F => 4, // LD A,A
            
            // ADD A,r
            0x80 => { let b = self.b(); self.add_a(b, false); 4 }
            0x81 => { let c = self.c(); self.add_a(c, false); 4 }
            0x82 => { let d = self.d(); self.add_a(d, false); 4 }
            0x83 => { let e = self.e(); self.add_a(e, false); 4 }
            0x84 => { let h = self.h(); self.add_a(h, false); 4 }
            0x85 => { let l = self.l(); self.add_a(l, false); 4 }
            0x86 => { let v = self.read_byte(self.hl); self.add_a(v, false); 7 }
            0x87 => { let a = self.a(); self.add_a(a, false); 4 }
            
            // ADC A,r
            0x88 => { let b = self.b(); let cy = self.flag(Flags::C); self.add_a(b, cy); 4 }
            0x89 => { let c = self.c(); let cy = self.flag(Flags::C); self.add_a(c, cy); 4 }
            0x8A => { let d = self.d(); let cy = self.flag(Flags::C); self.add_a(d, cy); 4 }
            0x8B => { let e = self.e(); let cy = self.flag(Flags::C); self.add_a(e, cy); 4 }
            0x8C => { let h = self.h(); let cy = self.flag(Flags::C); self.add_a(h, cy); 4 }
            0x8D => { let l = self.l(); let cy = self.flag(Flags::C); self.add_a(l, cy); 4 }
            0x8E => { let v = self.read_byte(self.hl); let cy = self.flag(Flags::C); self.add_a(v, cy); 7 }
            0x8F => { let a = self.a(); let cy = self.flag(Flags::C); self.add_a(a, cy); 4 }
            
            // SUB r
            0x90 => { let b = self.b(); self.sub_a(b, false); 4 }
            0x91 => { let c = self.c(); self.sub_a(c, false); 4 }
            0x92 => { let d = self.d(); self.sub_a(d, false); 4 }
            0x93 => { let e = self.e(); self.sub_a(e, false); 4 }
            0x94 => { let h = self.h(); self.sub_a(h, false); 4 }
            0x95 => { let l = self.l(); self.sub_a(l, false); 4 }
            0x96 => { let v = self.read_byte(self.hl); self.sub_a(v, false); 7 }
            0x97 => { let a = self.a(); self.sub_a(a, false); 4 }
            
            // SBC A,r
            0x98 => { let b = self.b(); let cy = self.flag(Flags::C); self.sub_a(b, cy); 4 }
            0x99 => { let c = self.c(); let cy = self.flag(Flags::C); self.sub_a(c, cy); 4 }
            0x9A => { let d = self.d(); let cy = self.flag(Flags::C); self.sub_a(d, cy); 4 }
            0x9B => { let e = self.e(); let cy = self.flag(Flags::C); self.sub_a(e, cy); 4 }
            0x9C => { let h = self.h(); let cy = self.flag(Flags::C); self.sub_a(h, cy); 4 }
            0x9D => { let l = self.l(); let cy = self.flag(Flags::C); self.sub_a(l, cy); 4 }
            0x9E => { let v = self.read_byte(self.hl); let cy = self.flag(Flags::C); self.sub_a(v, cy); 7 }
            0x9F => { let a = self.a(); let cy = self.flag(Flags::C); self.sub_a(a, cy); 4 }
            
            // AND r
            0xA0 => { let b = self.b(); self.and_a(b); 4 }
            0xA1 => { let c = self.c(); self.and_a(c); 4 }
            0xA2 => { let d = self.d(); self.and_a(d); 4 }
            0xA3 => { let e = self.e(); self.and_a(e); 4 }
            0xA4 => { let h = self.h(); self.and_a(h); 4 }
            0xA5 => { let l = self.l(); self.and_a(l); 4 }
            0xA6 => { let v = self.read_byte(self.hl); self.and_a(v); 7 }
            0xA7 => { let a = self.a(); self.and_a(a); 4 }
            
            // XOR r
            0xA8 => { let b = self.b(); self.xor_a(b); 4 }
            0xA9 => { let c = self.c(); self.xor_a(c); 4 }
            0xAA => { let d = self.d(); self.xor_a(d); 4 }
            0xAB => { let e = self.e(); self.xor_a(e); 4 }
            0xAC => { let h = self.h(); self.xor_a(h); 4 }
            0xAD => { let l = self.l(); self.xor_a(l); 4 }
            0xAE => { let v = self.read_byte(self.hl); self.xor_a(v); 7 }
            0xAF => { let a = self.a(); self.xor_a(a); 4 }
            
            // OR r
            0xB0 => { let b = self.b(); self.or_a(b); 4 }
            0xB1 => { let c = self.c(); self.or_a(c); 4 }
            0xB2 => { let d = self.d(); self.or_a(d); 4 }
            0xB3 => { let e = self.e(); self.or_a(e); 4 }
            0xB4 => { let h = self.h(); self.or_a(h); 4 }
            0xB5 => { let l = self.l(); self.or_a(l); 4 }
            0xB6 => { let v = self.read_byte(self.hl); self.or_a(v); 7 }
            0xB7 => { let a = self.a(); self.or_a(a); 4 }
            
            // CP r
            0xB8 => { let b = self.b(); self.cp_a(b); 4 }
            0xB9 => { let c = self.c(); self.cp_a(c); 4 }
            0xBA => { let d = self.d(); self.cp_a(d); 4 }
            0xBB => { let e = self.e(); self.cp_a(e); 4 }
            0xBC => { let h = self.h(); self.cp_a(h); 4 }
            0xBD => { let l = self.l(); self.cp_a(l); 4 }
            0xBE => { let v = self.read_byte(self.hl); self.cp_a(v); 7 }
            0xBF => { let a = self.a(); self.cp_a(a); 4 }
            
            // RET NZ
            0xC0 => { if !self.flag(Flags::Z) { self.ret(); 11 } else { 5 } }
            // POP BC
            0xC1 => { self.bc = self.pop(); 10 }
            // JP NZ,nn
            0xC2 => { let addr = self.fetch_word(); if !self.flag(Flags::Z) { self.pc = addr; } 10 }
            // JP nn
            0xC3 => { self.pc = self.fetch_word(); 10 }
            // CALL NZ,nn
            0xC4 => { let addr = self.fetch_word(); if !self.flag(Flags::Z) { self.call(addr); 17 } else { 10 } }
            // PUSH BC
            0xC5 => { self.push(self.bc); 11 }
            // ADD A,n
            0xC6 => { let n = self.fetch(); self.add_a(n, false); 7 }
            // RST 00
            0xC7 => { self.rst(0x00); 11 }
            // RET Z
            0xC8 => { if self.flag(Flags::Z) { self.ret(); 11 } else { 5 } }
            // RET
            0xC9 => { self.ret(); 10 }
            // JP Z,nn
            0xCA => { let addr = self.fetch_word(); if self.flag(Flags::Z) { self.pc = addr; } 10 }
            // CB prefix
            0xCB => { self.execute_cb() }
            // CALL Z,nn
            0xCC => { let addr = self.fetch_word(); if self.flag(Flags::Z) { self.call(addr); 17 } else { 10 } }
            // CALL nn
            0xCD => { let addr = self.fetch_word(); self.call(addr); 17 }
            // ADC A,n
            0xCE => { let n = self.fetch(); let cy = self.flag(Flags::C); self.add_a(n, cy); 7 }
            // RST 08
            0xCF => { self.rst(0x08); 11 }
            
            // RET NC
            0xD0 => { if !self.flag(Flags::C) { self.ret(); 11 } else { 5 } }
            // POP DE
            0xD1 => { self.de = self.pop(); 10 }
            // JP NC,nn
            0xD2 => { let addr = self.fetch_word(); if !self.flag(Flags::C) { self.pc = addr; } 10 }
            // OUT (n),A
            0xD3 => { let port = self.fetch() as u16 | ((self.a() as u16) << 8); self.io_write(port, self.a()); 11 }
            // CALL NC,nn
            0xD4 => { let addr = self.fetch_word(); if !self.flag(Flags::C) { self.call(addr); 17 } else { 10 } }
            // PUSH DE
            0xD5 => { self.push(self.de); 11 }
            // SUB n
            0xD6 => { let n = self.fetch(); self.sub_a(n, false); 7 }
            // RST 10
            0xD7 => { self.rst(0x10); 11 }
            // RET C
            0xD8 => { if self.flag(Flags::C) { self.ret(); 11 } else { 5 } }
            // EXX
            0xD9 => { 
                std::mem::swap(&mut self.bc, &mut self.bc_prime);
                std::mem::swap(&mut self.de, &mut self.de_prime);
                std::mem::swap(&mut self.hl, &mut self.hl_prime);
                4 
            }
            // JP C,nn
            0xDA => { let addr = self.fetch_word(); if self.flag(Flags::C) { self.pc = addr; } 10 }
            // IN A,(n)
            0xDB => { let port = self.fetch() as u16 | ((self.a() as u16) << 8); let v = self.io_read(port); self.set_a(v); 11 }
            // CALL C,nn
            0xDC => { let addr = self.fetch_word(); if self.flag(Flags::C) { self.call(addr); 17 } else { 10 } }
            // DD prefix (IX instructions)
            0xDD => { self.execute_dd() }
            // SBC A,n
            0xDE => { let n = self.fetch(); let cy = self.flag(Flags::C); self.sub_a(n, cy); 7 }
            // RST 18
            0xDF => { self.rst(0x18); 11 }
            
            // RET PO
            0xE0 => { if !self.flag(Flags::PV) { self.ret(); 11 } else { 5 } }
            // POP HL
            0xE1 => { self.hl = self.pop(); 10 }
            // JP PO,nn
            0xE2 => { let addr = self.fetch_word(); if !self.flag(Flags::PV) { self.pc = addr; } 10 }
            // EX (SP),HL
            0xE3 => { let v = self.read_word(self.sp); self.write_word(self.sp, self.hl); self.hl = v; 19 }
            // CALL PO,nn
            0xE4 => { let addr = self.fetch_word(); if !self.flag(Flags::PV) { self.call(addr); 17 } else { 10 } }
            // PUSH HL
            0xE5 => { self.push(self.hl); 11 }
            // AND n
            0xE6 => { let n = self.fetch(); self.and_a(n); 7 }
            // RST 20
            0xE7 => { self.rst(0x20); 11 }
            // RET PE
            0xE8 => { if self.flag(Flags::PV) { self.ret(); 11 } else { 5 } }
            // JP (HL)
            0xE9 => { self.pc = self.hl; 4 }
            // JP PE,nn
            0xEA => { let addr = self.fetch_word(); if self.flag(Flags::PV) { self.pc = addr; } 10 }
            // EX DE,HL
            0xEB => { std::mem::swap(&mut self.de, &mut self.hl); 4 }
            // CALL PE,nn
            0xEC => { let addr = self.fetch_word(); if self.flag(Flags::PV) { self.call(addr); 17 } else { 10 } }
            // ED prefix
            0xED => { self.execute_ed() }
            // XOR n
            0xEE => { let n = self.fetch(); self.xor_a(n); 7 }
            // RST 28
            0xEF => { self.rst(0x28); 11 }
            
            // RET P (positive)
            0xF0 => { if !self.flag(Flags::S) { self.ret(); 11 } else { 5 } }
            // POP AF
            0xF1 => { self.af = self.pop(); 10 }
            // JP P,nn
            0xF2 => { let addr = self.fetch_word(); if !self.flag(Flags::S) { self.pc = addr; } 10 }
            // DI
            0xF3 => { self.iff1 = false; self.iff2 = false; 4 }
            // CALL P,nn
            0xF4 => { let addr = self.fetch_word(); if !self.flag(Flags::S) { self.call(addr); 17 } else { 10 } }
            // PUSH AF
            0xF5 => { self.push(self.af); 11 }
            // OR n
            0xF6 => { let n = self.fetch(); self.or_a(n); 7 }
            // RST 30
            0xF7 => { self.rst(0x30); 11 }
            // RET M (minus)
            0xF8 => { if self.flag(Flags::S) { self.ret(); 11 } else { 5 } }
            // LD SP,HL
            0xF9 => { self.sp = self.hl; 6 }
            // JP M,nn
            0xFA => { let addr = self.fetch_word(); if self.flag(Flags::S) { self.pc = addr; } 10 }
            // EI
            0xFB => { self.iff1 = true; self.iff2 = true; 4 }
            // CALL M,nn
            0xFC => { let addr = self.fetch_word(); if self.flag(Flags::S) { self.call(addr); 17 } else { 10 } }
            // FD prefix (IY instructions)
            0xFD => { self.execute_fd() }
            // CP n
            0xFE => { let n = self.fetch(); self.cp_a(n); 7 }
            // RST 38
            0xFF => { self.rst(0x38); 11 }
        }
    }

    // Helper functions for instructions

    fn inc_r8<F>(&mut self, value: u8, setter: F) where F: FnOnce(&mut Self, u8) {
        let result = value.wrapping_add(1);
        setter(self, result);
        let flags = inc_flags(value, result) | (Flags::from_bits_truncate(self.f()) & Flags::C);
        self.set_f(flags.bits());
    }

    fn dec_r8<F>(&mut self, value: u8, setter: F) where F: FnOnce(&mut Self, u8) {
        let result = value.wrapping_sub(1);
        setter(self, result);
        let flags = dec_flags(value, result) | (Flags::from_bits_truncate(self.f()) & Flags::C);
        self.set_f(flags.bits());
    }

    fn inc_mem(&mut self, addr: u16, value: u8) {
        let result = value.wrapping_add(1);
        self.write_byte(addr, result);
        let flags = inc_flags(value, result) | (Flags::from_bits_truncate(self.f()) & Flags::C);
        self.set_f(flags.bits());
    }

    fn dec_mem(&mut self, addr: u16, value: u8) {
        let result = value.wrapping_sub(1);
        self.write_byte(addr, result);
        let flags = dec_flags(value, result) | (Flags::from_bits_truncate(self.f()) & Flags::C);
        self.set_f(flags.bits());
    }

    pub(crate) fn add_a(&mut self, value: u8, carry: bool) {
        let a = self.a();
        let c = if carry { 1 } else { 0 };
        let result = a.wrapping_add(value).wrapping_add(c);
        self.set_a(result);
        self.set_f(add_flags(a, value, result, carry).bits());
    }

    pub(crate) fn sub_a(&mut self, value: u8, carry: bool) {
        let a = self.a();
        let c = if carry { 1 } else { 0 };
        let result = a.wrapping_sub(value).wrapping_sub(c);
        self.set_a(result);
        self.set_f(sub_flags(a, value, result, carry).bits());
    }

    pub(crate) fn and_a(&mut self, value: u8) {
        let result = self.a() & value;
        self.set_a(result);
        self.set_f(and_flags(result).bits());
    }

    pub(crate) fn xor_a(&mut self, value: u8) {
        let result = self.a() ^ value;
        self.set_a(result);
        self.set_f(or_xor_flags(result).bits());
    }

    pub(crate) fn or_a(&mut self, value: u8) {
        let result = self.a() | value;
        self.set_a(result);
        self.set_f(or_xor_flags(result).bits());
    }

    pub(crate) fn cp_a(&mut self, value: u8) {
        let flags = cp_flags(self.a(), value);
        self.set_f(flags.bits());
    }

    fn add_hl(&mut self, value: u16) {
        let hl = self.hl;
        let result = hl.wrapping_add(value);
        self.hl = result;
        
        let mut f = self.f() & (Flags::S | Flags::Z | Flags::PV).bits();
        // Carry from bit 15
        if (hl as u32) + (value as u32) > 0xFFFF { f |= Flags::C.bits(); }
        // Half-carry from bit 11
        if (hl & 0x0FFF) + (value & 0x0FFF) > 0x0FFF { f |= Flags::H.bits(); }
        // Undocumented flags from high byte of result
        f |= (result >> 8) as u8 & (Flags::F3 | Flags::F5).bits();
        self.set_f(f);
    }

    fn rlca(&mut self) {
        let a = self.a();
        let carry = a >> 7;
        let result = (a << 1) | carry;
        self.set_a(result);
        let mut f = self.f() & (Flags::S | Flags::Z | Flags::PV).bits();
        if carry != 0 { f |= Flags::C.bits(); }
        f |= result & (Flags::F3 | Flags::F5).bits();
        self.set_f(f);
    }

    fn rrca(&mut self) {
        let a = self.a();
        let carry = a & 1;
        let result = (a >> 1) | (carry << 7);
        self.set_a(result);
        let mut f = self.f() & (Flags::S | Flags::Z | Flags::PV).bits();
        if carry != 0 { f |= Flags::C.bits(); }
        f |= result & (Flags::F3 | Flags::F5).bits();
        self.set_f(f);
    }

    fn rla(&mut self) {
        let a = self.a();
        let old_carry = if self.flag(Flags::C) { 1 } else { 0 };
        let new_carry = a >> 7;
        let result = (a << 1) | old_carry;
        self.set_a(result);
        let mut f = self.f() & (Flags::S | Flags::Z | Flags::PV).bits();
        if new_carry != 0 { f |= Flags::C.bits(); }
        f |= result & (Flags::F3 | Flags::F5).bits();
        self.set_f(f);
    }

    fn rra(&mut self) {
        let a = self.a();
        let old_carry = if self.flag(Flags::C) { 0x80 } else { 0 };
        let new_carry = a & 1;
        let result = (a >> 1) | old_carry;
        self.set_a(result);
        let mut f = self.f() & (Flags::S | Flags::Z | Flags::PV).bits();
        if new_carry != 0 { f |= Flags::C.bits(); }
        f |= result & (Flags::F3 | Flags::F5).bits();
        self.set_f(f);
    }

    fn daa(&mut self) {
        let a = self.a();
        let mut correction = 0u8;
        let mut carry = self.flag(Flags::C);
        
        if self.flag(Flags::H) || (a & 0x0F) > 9 {
            correction |= 0x06;
        }
        if carry || a > 0x99 {
            correction |= 0x60;
            carry = true;
        }
        
        let result = if self.flag(Flags::N) {
            a.wrapping_sub(correction)
        } else {
            a.wrapping_add(correction)
        };
        
        self.set_a(result);
        let mut f = sz53_flags(result) | parity_flag(result);
        if carry { f |= Flags::C; }
        if self.flag(Flags::N) { f |= Flags::N; }
        // Half-carry for DAA
        let h = if self.flag(Flags::N) {
            self.flag(Flags::H) && (a & 0x0F) < 6
        } else {
            (a & 0x0F) > 9
        };
        if h { f |= Flags::H; }
        self.set_f(f.bits());
    }

    fn cpl(&mut self) {
        let result = !self.a();
        self.set_a(result);
        let mut f = self.f();
        f |= (Flags::H | Flags::N).bits();
        f &= !(Flags::F3 | Flags::F5).bits();
        f |= result & (Flags::F3 | Flags::F5).bits();
        self.set_f(f);
    }

    fn scf(&mut self) {
        let a = self.a();
        let mut f = self.f() & (Flags::S | Flags::Z | Flags::PV).bits();
        f |= Flags::C.bits();
        f |= a & (Flags::F3 | Flags::F5).bits();
        self.set_f(f);
    }

    fn ccf(&mut self) {
        let a = self.a();
        let old_carry = self.flag(Flags::C);
        let mut f = self.f() & (Flags::S | Flags::Z | Flags::PV).bits();
        if old_carry { f |= Flags::H.bits(); }
        if !old_carry { f |= Flags::C.bits(); }
        f |= a & (Flags::F3 | Flags::F5).bits();
        self.set_f(f);
    }

    fn jr(&mut self) {
        let offset = self.fetch() as i8;
        self.pc = self.pc.wrapping_add(offset as u16);
    }

    fn jr_cc(&mut self, condition: bool) -> u8 {
        let offset = self.fetch() as i8;
        if condition {
            self.pc = self.pc.wrapping_add(offset as u16);
            12
        } else {
            7
        }
    }

    fn djnz(&mut self) -> u8 {
        let b = self.b().wrapping_sub(1);
        self.set_b(b);
        let offset = self.fetch() as i8;
        if b != 0 {
            self.pc = self.pc.wrapping_add(offset as u16);
            13
        } else {
            8
        }
    }

    fn call(&mut self, addr: u16) {
        self.push(self.pc);
        self.pc = addr;
    }

    fn ret(&mut self) {
        let return_addr = self.pop();
        
        // Auto-disable TR-DOS ROM when returning to address >= 0x4000
        // This is the standard TR-DOS exit mechanism
        if self.mem().is_trdos_rom_active() && return_addr >= 0x4000 {
            //  println!("[CPU] RET to 0x{:04X}, exiting TR-DOS ROM", return_addr);
            self.mem_mut().disable_trdos_rom();
        }
        
        self.pc = return_addr;
    }

    fn rst(&mut self, addr: u16) {
        self.push(self.pc);
        self.pc = addr;
    }
}
