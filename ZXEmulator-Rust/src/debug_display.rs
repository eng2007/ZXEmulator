//! Debug display for ZX Spectrum Emulator
//! Shows registers, memory at PC, and Stack

use crate::cpu::Z80;
use crate::memory::Memory;

pub const DBG_WIDTH: usize = 450;
pub const DBG_HEIGHT: usize = 400;

const COLOR_BG: u32 = 0xFF101010;
const COLOR_TEXT: u32 = 0xFFCCCCCC;
const COLOR_LABEL: u32 = 0xFF888888;
const COLOR_HIGHLIGHT: u32 = 0xFFFFFF00;
const COLOR_HEADER: u32 = 0xFF00AAAA;

pub struct DebugDisplay {
    pub buffer: Vec<u32>,
}

impl DebugDisplay {
    pub fn new() -> Self {
        Self {
            buffer: vec![COLOR_BG; DBG_WIDTH * DBG_HEIGHT],
        }
    }

    pub fn render(&mut self, cpu: &Z80, memory: &Memory, rom_name: &str) {
        self.buffer.fill(COLOR_BG);

        let mut y = 10;
        
        // --- Registers ---
        self.draw_text(10, y, "REGISTERS", COLOR_HEADER);
        y += 15;

        self.draw_register(10, y, "AF", cpu.af);
        self.draw_register(110, y, "AF'", cpu.af_prime);
        y += 10;
        self.draw_register(10, y, "BC", cpu.bc);
        self.draw_register(110, y, "BC'", cpu.bc_prime);
        y += 10;
        self.draw_register(10, y, "DE", cpu.de);
        self.draw_register(110, y, "DE'", cpu.de_prime);
        y += 10;
        self.draw_register(10, y, "HL", cpu.hl);
        self.draw_register(110, y, "HL'", cpu.hl_prime);
        y += 15;

        self.draw_register(10, y, "IX", cpu.ix);
        self.draw_register(110, y, "IY", cpu.iy);
        y += 15;

        self.draw_register(10, y, "SP", cpu.sp);
        self.draw_register(110, y, "PC", cpu.pc);
        y += 15;

        self.draw_val8(10, y, "I", cpu.i);
        self.draw_val8(80, y, "R", cpu.r);
        self.draw_val8(150, y, "IM", cpu.im);
        self.draw_bool(220, y, "IFF1", cpu.iff1);
        y += 20;

        // --- Flags ---
        let flags = cpu.f();
        let f_str = format!(
            "{}{}{}{}{}{}{}{}",
            if flags & 0x80 != 0 { 'S' } else { '-' },
            if flags & 0x40 != 0 { 'Z' } else { '-' },
            if flags & 0x20 != 0 { '5' } else { '-' },
            if flags & 0x10 != 0 { 'H' } else { '-' },
            if flags & 0x08 != 0 { '3' } else { '-' },
            if flags & 0x04 != 0 { 'P' } else { '-' },
            if flags & 0x02 != 0 { 'N' } else { '-' },
            if flags & 0x01 != 0 { 'C' } else { '-' },
        );
        self.draw_text(10, y, &format!("Flags: {}", f_str), COLOR_TEXT);
        y += 25;

        // --- Memory at PC ---
        self.draw_text(10, y, "MEMORY AT PC", COLOR_HEADER);
        y += 15;

        let pc = cpu.pc;
        for i in 0..8 {
            let addr = pc.wrapping_add(i);
            let byte = memory.read(addr);
            let prefix = if i == 0 { ">" } else { " " };
            self.draw_text(10, y, &format!("{} {:04X}: {:02X}", prefix, addr, byte), if i == 0 { COLOR_HIGHLIGHT } else { COLOR_TEXT });
            y += 10;
        }
        y += 20;

        // --- Stack ---
        self.draw_text(10, y, "STACK (Top)", COLOR_HEADER);
        y += 15;
        let sp = cpu.sp;
        for i in 0..8 {
            let addr = sp.wrapping_add(i * 2);
            let val = memory.read_word(addr);
            self.draw_text(10, y, &format!("  {:04X}: {:04X}", addr, val), COLOR_TEXT);
            y += 10;
        }

        // --- System Info (Right Side) ---
        let sys_x = 310;
        let mut sys_y = 10;
        self.draw_text(sys_x, sys_y, "SYSTEM", COLOR_HEADER);
        sys_y += 15;

        // Truncate ROM name if too long (max ~12 chars)
        let rom_display = if rom_name.len() > 12 {
            &rom_name[..12]
        } else {
            rom_name
        };
        self.draw_text(sys_x, sys_y, rom_display, COLOR_HIGHLIGHT);
        sys_y += 15;
        
        self.draw_text(sys_x, sys_y, if memory.is_128k_mode() { "128K Mode" } else { "48K Mode" }, COLOR_TEXT);
        sys_y += 10;
        
        if memory.is_128k_mode() {
            self.draw_text(sys_x, sys_y, "Paging:", COLOR_LABEL);
            sys_y += 10;
            self.draw_text(sys_x, sys_y, if memory.is_paging_disabled() { "LOCKED" } else { "ACTIVE" }, 
                if memory.is_paging_disabled() { 0xFFFF0000 } else { 0xFF00FF00 });
            sys_y += 15;

            self.draw_text(sys_x, sys_y, "Map:", COLOR_LABEL);
            sys_y += 10;
            self.draw_text(sys_x, sys_y, &format!("ROM: {}", memory.get_current_rom()), COLOR_TEXT);
            sys_y += 10;
            self.draw_text(sys_x, sys_y, "Bnk5", COLOR_LABEL); // 4000
            sys_y += 10;
            self.draw_text(sys_x, sys_y, "Bnk2", COLOR_LABEL); // 8000
            sys_y += 10;
            self.draw_text(sys_x, sys_y, &format!("Bnk{}", memory.get_bank_at_slot_3()), COLOR_HIGHLIGHT);
            sys_y += 15;
             self.draw_text(sys_x, sys_y, &format!("Scr: {}", memory.get_screen_bank()), COLOR_TEXT);
        } else {
            self.draw_text(sys_x, sys_y, "Standard", COLOR_LABEL);
            sys_y += 10;
            self.draw_text(sys_x, sys_y, "Map", COLOR_LABEL);
        }
    }

    fn draw_register(&mut self, x: usize, y: usize, label: &str, value: u16) {
        self.draw_text(x, y, &format!("{}: {:04X}", label, value), COLOR_TEXT);
    }
    
    fn draw_val8(&mut self, x: usize, y: usize, label: &str, value: u8) {
        self.draw_text(x, y, &format!("{}: {:02X}", label, value), COLOR_TEXT);
    }

    fn draw_bool(&mut self, x: usize, y: usize, label: &str, value: bool) {
        self.draw_text(x, y, &format!("{}: {}", label, if value { "1" } else { "0" }), COLOR_TEXT);
    }

    fn draw_text(&mut self, x: usize, y: usize, text: &str, color: u32) {
        let upper = text.to_uppercase();
        for (i, char) in upper.chars().enumerate() {
            self.draw_char(x + i * 8, y, char, color);
        }
    }

    fn draw_char(&mut self, x: usize, y: usize, char: char, color: u32) {
        // Minimal 5x7 font data embedded
        let font_data = match char {
           '0'..='9' => [
               0x3E, 0x41, 0x41, 0x41, 0x3E, // 0
               0x00, 0x42, 0x7F, 0x40, 0x00, // 1
               0x42, 0x61, 0x51, 0x49, 0x46, // 2
               0x21, 0x41, 0x45, 0x4B, 0x31, // 3
               0x18, 0x14, 0x12, 0x7F, 0x10, // 4
               0x27, 0x45, 0x45, 0x45, 0x39, // 5
               0x3C, 0x4A, 0x49, 0x49, 0x30, // 6
               0x01, 0x71, 0x09, 0x05, 0x03, // 7
               0x36, 0x49, 0x49, 0x49, 0x36, // 8
               0x06, 0x49, 0x49, 0x29, 0x1E, // 9
           ][((char as usize) - ('0' as usize)) * 5..].to_vec(),
           'A'..='Z' => [
               0x7E, 0x11, 0x11, 0x11, 0x7E, // A
               0x7F, 0x49, 0x49, 0x49, 0x36, // B
               0x3E, 0x41, 0x41, 0x41, 0x22, // C
               0x7F, 0x41, 0x41, 0x22, 0x1C, // D
               0x7F, 0x49, 0x49, 0x49, 0x41, // E
               0x7F, 0x09, 0x09, 0x09, 0x01, // F
               0x3E, 0x41, 0x49, 0x49, 0x7A, // G
               0x7F, 0x08, 0x08, 0x08, 0x7F, // H
               0x00, 0x41, 0x7F, 0x41, 0x00, // I
               0x20, 0x40, 0x41, 0x3F, 0x01, // J
               0x7F, 0x08, 0x14, 0x22, 0x41, // K
               0x7F, 0x40, 0x40, 0x40, 0x40, // L
               0x7F, 0x02, 0x0C, 0x02, 0x7F, // M
               0x7F, 0x04, 0x08, 0x10, 0x7F, // N
               0x3E, 0x41, 0x41, 0x41, 0x3E, // O
               0x7F, 0x09, 0x09, 0x09, 0x06, // P
               0x3E, 0x41, 0x51, 0x21, 0x5E, // Q
               0x7F, 0x09, 0x19, 0x29, 0x46, // R
               0x46, 0x49, 0x49, 0x49, 0x31, // S
               0x01, 0x01, 0x7F, 0x01, 0x01, // T
               0x3F, 0x40, 0x40, 0x40, 0x3F, // U
               0x1F, 0x20, 0x40, 0x20, 0x1F, // V
               0x3F, 0x40, 0x38, 0x40, 0x3F, // W
               0x63, 0x14, 0x08, 0x14, 0x63, // X
               0x07, 0x08, 0x70, 0x08, 0x07, // Y
               0x61, 0x51, 0x49, 0x45, 0x43, // Z
           ][((char as usize) - ('A' as usize)) * 5..].to_vec(),
           ' ' => vec![0, 0, 0, 0, 0],
           ':' => vec![0, 0x36, 0x36, 0, 0],
           '>' => vec![0x08, 0x14, 0x22, 0x41, 0],
            '.' => vec![0, 0xC0, 0xC0, 0, 0],
            '-' => vec![0x08, 0x08, 0x08, 0x08, 0x08],
            '_' => vec![0x80, 0x80, 0x80, 0x80, 0x80],
            '\'' => vec![0, 0x03, 0, 0, 0],
            '(' => vec![0, 0x41, 0x22, 0x1C, 0],
            ')' => vec![0, 0x1C, 0x22, 0x41, 0],
             _ => vec![0xFF, 0xFF, 0xFF, 0xFF, 0xFF], // Blobs for unknown
        };

        // Draw 5x7 (actually stored as columns here for easy encoding? No wait, these look like column bits)
        // Let's assume standard 5-byte per char, each byte is a column
        for (col, bits) in font_data.iter().take(5).enumerate() {
            for row in 0..8 {
                if (bits >> row) & 1 == 1 {
                    let px = x + col;
                    let py = y + row; // 7-row is up? 0 is bottom?
                    // Usually bits 0 is top.. let's try
                    // If these are from a standard font definition, low bit might be top or bottom
                    // 0x3E = 0011 1110 -> 1-5 ON.
                    if px < DBG_WIDTH && py < DBG_HEIGHT {
                         self.buffer[py * DBG_WIDTH + px] = color;
                    }
                }
            }
        }
    }
    
    pub fn get_buffer(&self) -> &[u32] {
        &self.buffer
    }
}
