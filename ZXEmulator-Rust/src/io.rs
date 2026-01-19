//! I/O controller for ZX Spectrum

use crate::memory::Memory;
use crate::keyboard::Keyboard;
use crate::config::{Config, PortDecoding};
use crate::fdc::FDC;

/// I/O Controller handles port read/write operations
pub struct IoController {
    /// Border color (bits 0-2 of port 0xFE write)
    pub border_color: u8,
    /// Last value written to port 0x7FFD
    pub last_7ffd: u8,
    /// Keyboard reference
    keyboard: *mut Keyboard,
    /// Memory reference for banking
    memory: *mut Memory,
    /// FDC reference for disk operations
    fdc: *mut FDC,
    /// Configuration
    config: Config,
}

impl IoController {
    /// Create new I/O controller
    pub fn new(keyboard: &mut Keyboard, memory: &mut Memory, fdc: &mut FDC, config: Config) -> Self {
        Self {
            border_color: 0,
            last_7ffd: 0,
            keyboard: keyboard as *mut Keyboard,
            memory: memory as *mut Memory,
            fdc: fdc as *mut FDC,
            config,
        }
    }

    /// Read from I/O port
    pub fn read(&mut self, port: u16) -> u8 {
        // Port 0xFE - keyboard and tape
        if port & 0xFF == 0xFE {
            let keyboard = unsafe { &mut *self.keyboard };
            return keyboard.read(port);
        }

        // FDC ports (Beta Disk interface) - enable TR-DOS ROM
        let port_low = port & 0xFF;
        if matches!(port_low, 0x1F | 0x3F | 0x5F | 0x7F | 0xFF) {
            let memory = unsafe { &mut *self.memory };
            memory.enable_trdos_rom();
            
            let fdc = unsafe { &mut *self.fdc };
            
            return match port_low {
                0x1F => fdc.read_status(),
                0x3F => fdc.read_track(),
                0x5F => fdc.read_sector(),
                0x7F => fdc.read_data(),
                0xFF => fdc.read_system(),
                _ => 0xFF,
            };
        }

        // Any other I/O - disable TR-DOS ROM
        let memory = unsafe { &mut *self.memory };
        memory.disable_trdos_rom();

        // Default - floating bus
        0xFF
    }

    /// Write to I/O port
    pub fn write(&mut self, port: u16, value: u8) {
        // Port 0xFE - border, speaker, tape
        if port & 0xFF == 0xFE {
            self.border_color = value & 0x07;
            // Bit 3: MIC
            // Bit 4: EAR (beeper)
            return;
        }

        // FDC ports (Beta Disk interface) - enable TR-DOS ROM
        let port_low = port & 0xFF;
        if matches!(port_low, 0x1F | 0x3F | 0x5F | 0x7F | 0xFF) {
            let memory = unsafe { &mut *self.memory };
            memory.enable_trdos_rom();
            
            let fdc = unsafe { &mut *self.fdc };
            
            match port_low {
                0x1F => fdc.write_command(value),
                0x3F => fdc.write_track(value),
                0x5F => fdc.write_sector(value),
                0x7F => fdc.write_data(value),
                0xFF => fdc.write_system(value),
                _ => {}
            }
            return;
        }

        // Any other I/O - disable TR-DOS ROM
        let memory = unsafe { &mut *self.memory };
        memory.disable_trdos_rom();

        // Port 0x7FFD - 128K memory paging
        let is_7ffd = match self.config.port_decoding {
            PortDecoding::Full => port == 0x7FFD,
            PortDecoding::Partial => (port & 0x8002) == 0, // Pentagon: A15=0, A1=0
        };

        if is_7ffd {
            if self.last_7ffd & 0x20 == 0 { // Not locked
                self.last_7ffd = value;
                let memory = unsafe { &mut *self.memory };
                memory.write_7ffd(value);
            }
            return;
        }
    }

    /// Get current border color
    pub fn get_border_color(&self) -> u8 {
        self.border_color
    }

    /// Reset I/O state
    pub fn reset(&mut self) {
        self.border_color = 0;
        self.last_7ffd = 0;
    }
}
