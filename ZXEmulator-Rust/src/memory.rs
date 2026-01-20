use crate::config::{Config, MemorySize};

/// Total memory size for 128K model: 128KB RAM
/// Total memory size for 512K model: 512KB RAM
const RAM_SIZE_128K: usize = 128 * 1024;
const RAM_SIZE_512K: usize = 512 * 1024;
const MAX_RAM_SIZE: usize = RAM_SIZE_512K;
const ROM_SIZE: usize = 16 * 1024;
const BANK_SIZE: usize = 16 * 1024;

/// Memory system with banking support
pub struct Memory {
    /// RAM banks (up to 512KB)
    ram: Vec<u8>,
    /// 3 ROM banks of 16KB each (ROM 0, ROM 1, ROM 2 for TR-DOS)
    rom: [[u8; ROM_SIZE]; 3],
    /// Currently selected ROM (0 or 1)
    current_rom: usize,
    /// TR-DOS ROM active flag (overrides current_rom when true)
    trdos_rom_active: bool,
    /// TR-DOS ROM loaded flag (true if TR-DOS ROM has been loaded into ROM bank 2)
    trdos_rom_loaded: bool,
    /// Currently paged RAM banks for each 16KB slot
    /// [0] = always ROM, [1] = bank 5, [2] = bank 2, [3] = configurable
    paged_banks: [usize; 4],
    /// Screen bank (5 or 7)
    screen_bank: usize,
    /// Paging disabled flag (bit 5 of port 0x7FFD)
    paging_disabled: bool,
    /// Is 128K mode
    is_128k: bool,
    /// Configuration
    config: Config,
}

impl Memory {
    /// Create new memory instance
    pub fn new(config: Config) -> Self {
        let ram_size = match config.memory_size {
            MemorySize::K128 => RAM_SIZE_128K,
            MemorySize::K512 => RAM_SIZE_512K,
        };
        
        Self {
            ram: vec![0; ram_size],
            rom: [[0; ROM_SIZE]; 3],
            current_rom: 0,
            trdos_rom_active: false,
            trdos_rom_loaded: false,
            paged_banks: [0, 5, 2, 0], // Default: ROM, Bank 5, Bank 2, Bank 0
            screen_bank: 5,
            paging_disabled: false,
            is_128k: false,
            config,
        }
    }

    /// Reset memory to initial state
    pub fn reset(&mut self) {
        self.ram.fill(0);
        self.current_rom = 0;
        self.trdos_rom_active = false;
        // Don't reset trdos_rom_loaded - keep ROM loaded after reset
        self.paged_banks = [0, 5, 2, 0];
        self.screen_bank = 5;
        self.paging_disabled = false;
    }

    /// Load ROM data
    pub fn load_rom(&mut self, data: &[u8], rom_number: usize) {
        if rom_number < 3 && data.len() <= ROM_SIZE {
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
        let mut bank = (value & 0x07) as usize;
        
        // Handle 512K extension (Pentagon)
        if self.config.memory_size == MemorySize::K512 {
            // Bit 6: MSB 1 (adds 8 to bank number)
            if value & 0x40 != 0 {
                bank |= 0x08;
            }
            // Bit 7: MSB 2 (adds 16 to bank number)
            if value & 0x80 != 0 {
                bank |= 0x10;
            }
        }
        
        self.paged_banks[3] = bank;

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
            // 0x0000-0x3FFF: ROM (use TR-DOS ROM if active, otherwise current_rom)
            0x0000..=0x3FFF => {
                let rom_bank = if self.trdos_rom_active { 2 } else { self.current_rom };
                self.rom[rom_bank][addr]
            }
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
                // Ensure we don't access out of bounds if something went wrong, though shouldn't happen
                let bank_idx = self.paged_banks[3] % (self.ram.len() / BANK_SIZE);
                self.ram[bank_idx * BANK_SIZE + offset]
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
                let bank_idx = self.paged_banks[3] % (self.ram.len() / BANK_SIZE);
                self.ram[bank_idx * BANK_SIZE + offset] = value;
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

    /// Get current ROM bank (0 or 1)
    pub fn get_current_rom(&self) -> usize {
        self.current_rom
    }

    /// Get current screen bank (5 or 7)
    pub fn get_screen_bank(&self) -> usize {
        self.screen_bank
    }

    /// Check if paging is disabled
    pub fn is_paging_disabled(&self) -> bool {
        self.paging_disabled
    }

    /// Get RAM bank for the switchable slot (0xC000-0xFFFF)
    pub fn get_bank_at_slot_3(&self) -> usize {
        self.paged_banks[3]
    }

    /// Load TR-DOS ROM (16KB) into ROM bank 2
    pub fn load_trdos_rom(&mut self, data: &[u8]) {
        if data.len() <= ROM_SIZE {
            self.rom[2][..data.len()].copy_from_slice(data);
            self.trdos_rom_loaded = true;
        }
    }

    /// Enable TR-DOS ROM (switch to ROM bank 2)
    pub fn enable_trdos_rom(&mut self) {
        self.trdos_rom_active = true;
    }

    /// Disable TR-DOS ROM (return to normal ROM banking)
    pub fn disable_trdos_rom(&mut self) {
        self.trdos_rom_active = false;
    }

    /// Check if TR-DOS ROM is active
    pub fn is_trdos_rom_active(&self) -> bool {
        self.trdos_rom_active
    }

    /// Check if TR-DOS ROM is loaded in ROM bank 2
    pub fn is_trdos_rom_loaded(&self) -> bool {
        self.trdos_rom_loaded
    }
}

impl Default for Memory {
    fn default() -> Self {
        Self::new(Config::default())
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
