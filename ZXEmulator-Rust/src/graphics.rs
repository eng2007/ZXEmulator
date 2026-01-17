//! Graphics rendering for ZX Spectrum

use crate::memory::Memory;

/// Screen dimensions
pub const SCREEN_WIDTH: usize = 256;
pub const SCREEN_HEIGHT: usize = 192;
pub const BORDER_SIZE: usize = 32;

/// Total window dimensions including border
pub const WINDOW_WIDTH: usize = SCREEN_WIDTH + BORDER_SIZE * 2;
pub const WINDOW_HEIGHT: usize = SCREEN_HEIGHT + BORDER_SIZE * 2;

/// ZX Spectrum color palette (ARGB format)
pub const COLORS: [u32; 16] = [
    // Normal colors
    0xFF000000, // 0: Black
    0xFF0000D7, // 1: Blue
    0xFFD70000, // 2: Red
    0xFFD700D7, // 3: Magenta
    0xFF00D700, // 4: Green
    0xFF00D7D7, // 5: Cyan
    0xFFD7D700, // 6: Yellow
    0xFFD7D7D7, // 7: White
    // Bright colors
    0xFF000000, // 8: Black (bright)
    0xFF0000FF, // 9: Bright Blue
    0xFFFF0000, // 10: Bright Red
    0xFFFF00FF, // 11: Bright Magenta
    0xFF00FF00, // 12: Bright Green
    0xFF00FFFF, // 13: Bright Cyan
    0xFFFFFF00, // 14: Bright Yellow
    0xFFFFFFFF, // 15: Bright White
];

/// Graphics renderer
pub struct Graphics {
    /// Frame buffer (ARGB format)
    pub buffer: Vec<u32>,
    /// Current border color
    border_color: u8,
    /// Flash state (toggles every 16 frames)
    flash_state: bool,
    /// Frame counter for flash
    frame_count: u8,
}

impl Graphics {
    /// Create new graphics renderer
    pub fn new() -> Self {
        Self {
            buffer: vec![0; WINDOW_WIDTH * WINDOW_HEIGHT],
            border_color: 0,
            flash_state: false,
            frame_count: 0,
        }
    }

    /// Set border color
    pub fn set_border(&mut self, color: u8) {
        self.border_color = color & 0x07;
    }

    /// Render screen from memory
    pub fn render(&mut self, memory: &Memory) {
        // Update flash state
        self.frame_count = self.frame_count.wrapping_add(1);
        if self.frame_count >= 16 {
            self.frame_count = 0;
            self.flash_state = !self.flash_state;
        }

        // Clear buffer with border color
        let border = COLORS[self.border_color as usize];
        self.buffer.fill(border);

        // Render screen area
        let screen_data = memory.get_screen_data();
        
        for y in 0..SCREEN_HEIGHT {
            for x_byte in 0..32 {
                // Calculate pixel address using ZX Spectrum's peculiar layout
                let pixel_addr = Self::screen_address(x_byte, y);
                let attr_addr = 6144 + (y / 8) * 32 + x_byte;

                let pixels = screen_data[pixel_addr];
                let attr = screen_data[attr_addr];

                // Decode attribute
                let ink = attr & 0x07;
                let paper = (attr >> 3) & 0x07;
                let bright = if attr & 0x40 != 0 { 8 } else { 0 };
                let flash = attr & 0x80 != 0;

                // Apply flash
                let (fg, bg) = if flash && self.flash_state {
                    (paper + bright, ink + bright)
                } else {
                    (ink + bright, paper + bright)
                };

                let fg_color = COLORS[fg as usize];
                let bg_color = COLORS[bg as usize];

                // Render 8 pixels
                for bit in 0..8 {
                    let px = x_byte * 8 + (7 - bit);
                    let color = if pixels & (1 << bit) != 0 { fg_color } else { bg_color };
                    
                    let buf_x = BORDER_SIZE + px;
                    let buf_y = BORDER_SIZE + y;
                    self.buffer[buf_y * WINDOW_WIDTH + buf_x] = color;
                }
            }
        }
    }

    /// Calculate screen memory address for given coordinates
    fn screen_address(x_byte: usize, y: usize) -> usize {
        // ZX Spectrum screen layout:
        // Each third of the screen (64 lines) is divided into 8 character rows
        // Lines are interleaved: 0, 8, 16, 24, 32, 40, 48, 56, 1, 9, 17...
        let y2 = y & 0x07;           // Line within character (0-7)
        let y1 = (y >> 3) & 0x07;    // Character row within third (0-7)
        let y0 = (y >> 6) & 0x03;    // Third of screen (0-2)
        
        (y0 << 11) | (y2 << 8) | (y1 << 5) | x_byte
    }

    /// Get buffer for window update
    pub fn get_buffer(&self) -> &[u32] {
        &self.buffer
    }

    /// Reset graphics state
    pub fn reset(&mut self) {
        self.buffer.fill(0);
        self.border_color = 0;
        self.flash_state = false;
        self.frame_count = 0;
    }
}

impl Default for Graphics {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_screen_address() {
        // First line, first byte
        assert_eq!(Graphics::screen_address(0, 0), 0);
        // First line, second byte
        assert_eq!(Graphics::screen_address(1, 0), 1);
        // Second line (should be at offset 256)
        assert_eq!(Graphics::screen_address(0, 1), 256);
        // Line 8 (first of second character row)
        assert_eq!(Graphics::screen_address(0, 8), 32);
    }
}
