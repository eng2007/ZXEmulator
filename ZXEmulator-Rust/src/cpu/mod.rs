//! Z80 CPU module

mod flags;
mod instructions;
mod extended;

pub use flags::Flags;

use crate::memory::Memory;
use crate::io::IoController;

/// Z80 CPU emulator
pub struct Z80 {
    // Main registers (16-bit pairs)
    pub af: u16,
    pub bc: u16,
    pub de: u16,
    pub hl: u16,
    
    // Shadow registers
    pub af_prime: u16,
    pub bc_prime: u16,
    pub de_prime: u16,
    pub hl_prime: u16,
    
    // Index registers
    pub ix: u16,
    pub iy: u16,
    
    // Stack pointer and program counter
    pub sp: u16,
    pub pc: u16,
    
    // Interrupt and refresh registers
    pub i: u8,
    pub r: u8,
    
    // Interrupt flip-flops and mode
    pub iff1: bool,
    pub iff2: bool,
    pub im: u8,
    
    // CPU state
    pub halted: bool,
    pub cycles: u64,
    
    // Memory and I/O references (stored as indices for now)
    memory: *mut Memory,
    io: *mut IoController,
}

impl Z80 {
    /// Create new Z80 CPU
    pub fn new(memory: &mut Memory, io: &mut IoController) -> Self {
        Self {
            af: 0xFFFF,
            bc: 0,
            de: 0,
            hl: 0,
            af_prime: 0,
            bc_prime: 0,
            de_prime: 0,
            hl_prime: 0,
            ix: 0,
            iy: 0,
            sp: 0xFFFF,
            pc: 0,
            i: 0,
            r: 0,
            iff1: false,
            iff2: false,
            im: 0,
            halted: false,
            cycles: 0,
            memory: memory as *mut Memory,
            io: io as *mut IoController,
        }
    }

    /// Reset CPU to initial state
    pub fn reset(&mut self) {
        self.af = 0xFFFF;
        self.bc = 0;
        self.de = 0;
        self.hl = 0;
        self.af_prime = 0;
        self.bc_prime = 0;
        self.de_prime = 0;
        self.hl_prime = 0;
        self.ix = 0;
        self.iy = 0;
        self.sp = 0xFFFF;
        self.pc = 0;
        self.i = 0;
        self.r = 0;
        self.iff1 = false;
        self.iff2 = false;
        self.im = 0;
        self.halted = false;
    }

    // Register accessors
    #[inline] pub fn a(&self) -> u8 { (self.af >> 8) as u8 }
    #[inline] pub fn f(&self) -> u8 { (self.af & 0xFF) as u8 }
    #[inline] pub fn b(&self) -> u8 { (self.bc >> 8) as u8 }
    #[inline] pub fn c(&self) -> u8 { (self.bc & 0xFF) as u8 }
    #[inline] pub fn d(&self) -> u8 { (self.de >> 8) as u8 }
    #[inline] pub fn e(&self) -> u8 { (self.de & 0xFF) as u8 }
    #[inline] pub fn h(&self) -> u8 { (self.hl >> 8) as u8 }
    #[inline] pub fn l(&self) -> u8 { (self.hl & 0xFF) as u8 }

    #[inline] pub fn set_a(&mut self, v: u8) { self.af = (self.af & 0x00FF) | ((v as u16) << 8); }
    #[inline] pub fn set_f(&mut self, v: u8) { self.af = (self.af & 0xFF00) | (v as u16); }
    #[inline] pub fn set_b(&mut self, v: u8) { self.bc = (self.bc & 0x00FF) | ((v as u16) << 8); }
    #[inline] pub fn set_c(&mut self, v: u8) { self.bc = (self.bc & 0xFF00) | (v as u16); }
    #[inline] pub fn set_d(&mut self, v: u8) { self.de = (self.de & 0x00FF) | ((v as u16) << 8); }
    #[inline] pub fn set_e(&mut self, v: u8) { self.de = (self.de & 0xFF00) | (v as u16); }
    #[inline] pub fn set_h(&mut self, v: u8) { self.hl = (self.hl & 0x00FF) | ((v as u16) << 8); }
    #[inline] pub fn set_l(&mut self, v: u8) { self.hl = (self.hl & 0xFF00) | (v as u16); }

    // Flag accessors
    #[inline] pub fn flag(&self, f: Flags) -> bool { (self.f() & f.bits()) != 0 }
    #[inline] pub fn set_flag(&mut self, f: Flags, v: bool) {
        let flags = if v { self.f() | f.bits() } else { self.f() & !f.bits() };
        self.set_f(flags);
    }

    // Memory access through pointer
    #[inline]
    fn mem(&self) -> &Memory {
        unsafe { &*self.memory }
    }

    #[inline]
    fn mem_mut(&mut self) -> &mut Memory {
        unsafe { &mut *self.memory }
    }

    // I/O access through pointer
    #[inline]
    fn io(&self) -> &IoController {
        unsafe { &*self.io }
    }

    #[inline]
    fn io_mut(&mut self) -> &mut IoController {
        unsafe { &mut *self.io }
    }

    /// Fetch byte from PC and increment PC
    #[inline]
    pub fn fetch(&mut self) -> u8 {
        // Auto-enable TR-DOS ROM when PC enters TR-DOS area (0x3C00-0x3FFF)
        // This is necessary for RANDOMIZE USR 15616 to work correctly
        // Only activate if TR-DOS ROM is actually loaded
        if self.pc >= 0x3C00 && self.pc < 0x4000 {
            if self.mem().is_trdos_rom_loaded() && !self.mem().is_trdos_rom_active() {
                println!("[CPU] PC=0x{:04X} entering TR-DOS area, activating TR-DOS ROM", self.pc);
                self.mem_mut().enable_trdos_rom();
            }
        }
        
        let byte = self.mem().read(self.pc);
        self.pc = self.pc.wrapping_add(1);
        self.r = (self.r & 0x80) | ((self.r.wrapping_add(1)) & 0x7F);
        byte
    }

    /// Fetch 16-bit word from PC (little-endian)
    #[inline]
    pub fn fetch_word(&mut self) -> u16 {
        let lo = self.fetch() as u16;
        let hi = self.fetch() as u16;
        (hi << 8) | lo
    }

    /// Read byte from memory
    #[inline]
    pub fn read_byte(&self, addr: u16) -> u8 {
        self.mem().read(addr)
    }

    /// Write byte to memory
    #[inline]
    pub fn write_byte(&mut self, addr: u16, value: u8) {
        self.mem_mut().write(addr, value);
    }

    /// Read word from memory
    #[inline]
    pub fn read_word(&self, addr: u16) -> u16 {
        self.mem().read_word(addr)
    }

    /// Write word to memory
    #[inline]
    pub fn write_word(&mut self, addr: u16, value: u16) {
        self.mem_mut().write_word(addr, value);
    }

    /// Read from I/O port
    #[inline]
    pub fn io_read(&mut self, port: u16) -> u8 {
        self.io_mut().read(port)
    }

    /// Write to I/O port
    #[inline]
    pub fn io_write(&mut self, port: u16, value: u8) {
        self.io_mut().write(port, value);
    }

    /// Push 16-bit value onto stack
    #[inline]
    pub fn push(&mut self, value: u16) {
        self.sp = self.sp.wrapping_sub(2);
        self.write_word(self.sp, value);
    }

    /// Pop 16-bit value from stack
    #[inline]
    pub fn pop(&mut self) -> u16 {
        let value = self.read_word(self.sp);
        self.sp = self.sp.wrapping_add(2);
        value
    }

    /// Handle maskable interrupt
    pub fn handle_interrupt(&mut self) {
        if !self.iff1 {
            return;
        }

        self.halted = false;
        self.iff1 = false;
        self.iff2 = false;

        match self.im {
            0 | 1 => {
                // IM 0/1: RST 38h
                self.push(self.pc);
                self.pc = 0x0038;
                self.cycles += 13;
            }
            2 => {
                // IM 2: Jump to address at (I * 256 + data_bus)
                // Data bus is typically 0xFF
                self.push(self.pc);
                let vector_addr = ((self.i as u16) << 8) | 0xFF;
                self.pc = self.read_word(vector_addr);
                self.cycles += 19;
            }
            _ => {}
        }
    }

    /// Handle non-maskable interrupt
    pub fn handle_nmi(&mut self) {
        self.halted = false;
        self.iff2 = self.iff1;
        self.iff1 = false;
        self.push(self.pc);
        self.pc = 0x0066;
        self.cycles += 11;
    }

    /// Execute one instruction
    pub fn execute(&mut self) -> u8 {
        if self.halted {
            self.cycles += 4;
            return 4;
        }

        let opcode = self.fetch();
        self.execute_opcode(opcode)
    }

    /// Run for specified number of cycles
    pub fn run(&mut self, target_cycles: u64) {
        let start = self.cycles;
        while self.cycles - start < target_cycles {
            self.execute();
        }
    }
}
