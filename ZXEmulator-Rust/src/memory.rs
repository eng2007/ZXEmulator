//! Memory module for ZX Spectrum emulation
//! 
//! Supports both 48K and 128K models with proper memory banking.

/// Total memory size for 128K model: 128KB RAM + 32KB ROM
const RAM_SIZE: usize = 128 * 1024;
const ROM_SIZE: usize = 16 * 1024;
const BANK_SIZE: usize = 16 * 1024;

/// Memory system with banking support for ZX Spectrum 128
pub struct Memory {
    /// 8 RAM banks of 16KB each
    ram: [u8; RAM_SIZE],
    /// 2 ROM banks of 16KB each (ROM 0 and ROM 1)
    rom: [[u8; ROM_SIZE]; 2],
    /// Currently selected ROM (0 or 1)
    current_rom: usize,
    /// Currently paged RAM banks for each 16KB slot
    /// [0] = always ROM, [1] = bank 5, [2] = bank 2, [3] = configurable
    paged_banks: [usize; 4],
    /// Screen bank (5 or 7)
    screen_bank: usize,
    /// Paging disabled flag (bit 5 of port 0x7FFD)
    paging_disabled: bool,
    /// Is 128K mode
    is_128k: bool,
}

impl Memory {
    /// Create new memory instance
    pub fn new() -> Self {
        Self {
            ram: [0; RAM_SIZE],
            rom: [[0; ROM_SIZE]; 2],
            current_rom: 0,
            paged_banks: [0, 5, 2, 0], // Default: ROM, Bank 5, Bank 2, Bank 0
            screen_bank: 5,
            paging_disabled: false,
            is_128k: false,
        }
    }

    /// Reset memory to initial state
    pub fn reset(&mut self) {
        self.ram.fill(0);
        self.current_rom = 0;
        self.paged_banks = [0, 5, 2, 0];
        self.screen_bank = 5;
        self.paging_disabled = false;
    }

    /// Load ROM data
    pub fn load_rom(&mut self, data: &[u8], rom_number: usize) {
        if rom_number < 2 && data.len() <= ROM_SIZE {
            self.rom[rom_number][..data.len()].copy_from_slice(data);
        }
    }

    /// Load 128K ROM (32KB = 2 x 16KB banks)
    pub fn load_rom_128k(&mut self, data: &[u8]) {
        if data.len() >= ROM_SIZE * 2 {
            self.rom[0].copy_from_slice(&data[..ROM_SIZE]);
            self.rom[1].copy_from_slice(&data[ROM_SIZE..ROM_SIZE * 2]);
            self.is_128k = true;
        } else if data.len() <= ROM_SIZE {
            self.rom[0][..data.len()].copy_from_slice(data);
            self.is_128k = false;
        }
    }

    /// Handle port 0x7FFD write (128K memory paging)
    pub fn write_7ffd(&mut self, value: u8) {
        if self.paging_disabled {
            return;
        }

        // Bits 0-2: RAM bank for slot 3 (0xC000-0xFFFF)
        self.paged_banks[3] = (value & 0x07) as usize;

        // Bit 3: Screen select (0 = bank 5, 1 = bank 7)
        self.screen_bank = if value & 0x08 != 0 { 7 } else { 5 };

        // Bit 4: ROM select
        self.current_rom = ((value >> 4) & 0x01) as usize;

        // Bit 5: Disable paging
        self.paging_disabled = value & 0x20 != 0;
    }

    /// Read byte from memory
    pub fn read(&self, address: u16) -> u8 {
        let addr = address as usize;
        match addr {
            // 0x0000-0x3FFF: ROM
            0x0000..=0x3FFF => self.rom[self.current_rom][addr],
            // 0x4000-0x7FFF: Bank 5 (always)
            0x4000..=0x7FFF => {
                let offset = addr - 0x4000;
                self.ram[5 * BANK_SIZE + offset]
            }
            // 0x8000-0xBFFF: Bank 2 (always)
            0x8000..=0xBFFF => {
                let offset = addr - 0x8000;
                self.ram[2 * BANK_SIZE + offset]
            }
            // 0xC000-0xFFFF: Configurable bank
            0xC000..=0xFFFF => {
                let offset = addr - 0xC000;
                self.ram[self.paged_banks[3] * BANK_SIZE + offset]
            }
            _ => 0xFF,
        }
    }

    /// Write byte to memory
    pub fn write(&mut self, address: u16, value: u8) {
        let addr = address as usize;
        match addr {
            // 0x0000-0x3FFF: ROM (read-only, ignore writes)
            0x0000..=0x3FFF => {}
            // 0x4000-0x7FFF: Bank 5
            0x4000..=0x7FFF => {
                let offset = addr - 0x4000;
                self.ram[5 * BANK_SIZE + offset] = value;
            }
            // 0x8000-0xBFFF: Bank 2
            0x8000..=0xBFFF => {
                let offset = addr - 0x8000;
                self.ram[2 * BANK_SIZE + offset] = value;
            }
            // 0xC000-0xFFFF: Configurable bank
            0xC000..=0xFFFF => {
                let offset = addr - 0xC000;
                self.ram[self.paged_banks[3] * BANK_SIZE + offset] = value;
            }
            _ => {}
        }
    }

    /// Read 16-bit word from memory (little-endian)
    pub fn read_word(&self, address: u16) -> u16 {
        let lo = self.read(address) as u16;
        let hi = self.read(address.wrapping_add(1)) as u16;
        (hi << 8) | lo
    }

    /// Write 16-bit word to memory (little-endian)
    pub fn write_word(&mut self, address: u16, value: u16) {
        self.write(address, (value & 0xFF) as u8);
        self.write(address.wrapping_add(1), ((value >> 8) & 0xFF) as u8);
    }

    /// Get screen memory base address
    pub fn get_screen_base(&self) -> usize {
        self.screen_bank * BANK_SIZE
    }

    /// Get raw screen data (6912 bytes: 6144 pixels + 768 attributes)
    pub fn get_screen_data(&self) -> &[u8] {
        let base = 5 * BANK_SIZE; // Screen is always in bank 5 at 0x4000
        &self.ram[base..base + 6912]
    }

    /// Get raw RAM slice for snapshot loading
    pub fn get_ram_mut(&mut self) -> &mut [u8] {
        &mut self.ram
    }

    /// Check if 128K mode
    pub fn is_128k_mode(&self) -> bool {
        self.is_128k
    }
}

impl Default for Memory {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_memory_read_write() {
        let mut mem = Memory::new();
        mem.write(0x4000, 0x42);
        assert_eq!(mem.read(0x4000), 0x42);
    }

    #[test]
    fn test_word_read_write() {
        let mut mem = Memory::new();
        mem.write_word(0x8000, 0x1234);
        assert_eq!(mem.read_word(0x8000), 0x1234);
    }

    #[test]
    fn test_bank_switching() {
        let mut mem = Memory::new();
        mem.write(0xC000, 0x11); // Write to bank 0
        mem.write_7ffd(0x01);     // Switch to bank 1
        mem.write(0xC000, 0x22); // Write to bank 1
        
        mem.write_7ffd(0x00);     // Back to bank 0
        assert_eq!(mem.read(0xC000), 0x11);
        
        mem.write_7ffd(0x01);     // Back to bank 1
        assert_eq!(mem.read(0xC000), 0x22);
    }
}
