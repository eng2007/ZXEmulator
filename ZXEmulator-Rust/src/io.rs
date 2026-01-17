//! I/O controller for ZX Spectrum

use crate::memory::Memory;
use crate::keyboard::Keyboard;

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
}

impl IoController {
    /// Create new I/O controller
    pub fn new(keyboard: &mut Keyboard, memory: &mut Memory) -> Self {
        Self {
            border_color: 0,
            last_7ffd: 0,
            keyboard: keyboard as *mut Keyboard,
            memory: memory as *mut Memory,
        }
    }

    /// Read from I/O port
    pub fn read(&mut self, port: u16) -> u8 {
        // Port 0xFE - keyboard and tape
        if port & 0xFF == 0xFE {
            let keyboard = unsafe { &mut *self.keyboard };
            return keyboard.read(port);
        }

        // Kempston joystick (port 0x1F)
        if port & 0xFF == 0x1F {
            return 0x00; // No joystick
        }

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

        // Port 0x7FFD - 128K memory paging
        if port == 0x7FFD {
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
