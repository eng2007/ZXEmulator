//! Keyboard emulation for ZX Spectrum

use minifb::Key;

/// ZX Spectrum keyboard with 8x5 matrix
pub struct Keyboard {
    /// 8 rows x 5 columns keyboard matrix
    /// Each bit represents a key: 0 = pressed, 1 = not pressed
    matrix: [u8; 8],
}

impl Keyboard {
    /// Create new keyboard
    pub fn new() -> Self {
        Self {
            matrix: [0xFF; 8], // All keys released
        }
    }

    /// Reset keyboard state
    pub fn reset(&mut self) {
        self.matrix = [0xFF; 8];
    }

    /// Read keyboard state for given port
    /// ZX Spectrum uses address lines A8-A15 to select rows
    /// Each bit that is LOW (0) selects the corresponding row
    pub fn read(&self, port: u16) -> u8 {
        let high_byte = (port >> 8) as u8;
        let mut result = 0x1F; // Bits 0-4 are keyboard, upper bits are unused

        // ZX Spectrum port addresses (bits that are 0 select the row):
        // Row 0 (1-5):     0xFEFE -> A8=0  -> bit 0 low
        // Row 1 (6-0):     0xEFFE -> A12=0 -> actually mapped to row inverted
        // The actual mapping is based on which address bit is low
        
        // Port half-rows:
        // 0xFEFE (A8=0):  Row 0 - 1,2,3,4,5
        // 0xFDFE (A9=0):  Row 1 - Q,W,E,R,T  (wait, this is wrong in original)
        
        // Actually ZX Spectrum uses:
        // Port 0xFEFE (1111 1110): Row 0 - Caps, Z, X, C, V
        // Port 0xFDFE (1111 1101): Row 1 - A, S, D, F, G
        // Port 0xFBFE (1111 1011): Row 2 - Q, W, E, R, T
        // Port 0xF7FE (1111 0111): Row 3 - 1, 2, 3, 4, 5
        // Port 0xEFFE (1110 1111): Row 4 - 0, 9, 8, 7, 6
        // Port 0xDFFE (1101 1111): Row 5 - P, O, I, U, Y
        // Port 0xBFFE (1011 1111): Row 6 - Enter, L, K, J, H
        // Port 0x7FFE (0111 1111): Row 7 - Space, Sym, M, N, B
        
        // Map address bits to keyboard matrix rows
        let row_mapping = [
            (0x01, 0), // A8=0  -> matrix row 0 (CAPS, Z, X, C, V)
            (0x02, 1), // A9=0  -> matrix row 1 (A, S, D, F, G) 
            (0x04, 2), // A10=0 -> matrix row 2 (Q, W, E, R, T)
            (0x08, 3), // A11=0 -> matrix row 3 (1, 2, 3, 4, 5)
            (0x10, 4), // A12=0 -> matrix row 4 (0, 9, 8, 7, 6)
            (0x20, 5), // A13=0 -> matrix row 5 (P, O, I, U, Y)
            (0x40, 6), // A14=0 -> matrix row 6 (Enter, L, K, J, H)
            (0x80, 7), // A15=0 -> matrix row 7 (Space, Sym, M, N, B)
        ];

        for (mask, row) in row_mapping {
            if high_byte & mask == 0 {
                result &= self.matrix[row];
            }
        }

        result
    }

    /// Update keyboard state from window keys
    pub fn update(&mut self, keys: &[Key]) {
        // Reset all keys
        self.matrix = [0xFF; 8];

        for key in keys {
            // Handle extended keys that map to multiple ZX Spectrum keys
            match self.map_extended_key(*key) {
                Some(key_positions) => {
                    // Press multiple keys at once (e.g., Caps Shift + 6 for DOWN)
                    for (row, col) in key_positions {
                        self.matrix[row] &= !(1 << col);
                    }
                }
                None => {
                    // Handle regular single key mapping
                    if let Some((row, col)) = self.map_key(*key) {
                        self.matrix[row] &= !(1 << col);
                    }
                }
            }
        }
    }

    /// Map extended PC keys to multiple ZX Spectrum keys (for combinations)
    /// Returns None if key is not an extended key
    fn map_extended_key(&self, key: Key) -> Option<Vec<(usize, usize)>> {
        match key {
            // Cursor keys: Caps Shift + 5/6/7/8
            Key::Left => Some(vec![
                (0, 0), // Caps Shift
                (3, 4), // 5
            ]),
            Key::Down => Some(vec![
                (0, 0), // Caps Shift
                (4, 4), // 6
            ]),
            Key::Up => Some(vec![
                (0, 0), // Caps Shift
                (4, 3), // 7
            ]),
            Key::Right => Some(vec![
                (0, 0), // Caps Shift
                (4, 2), // 8
            ]),
            
            // Backspace: Caps Shift + 0 (DELETE)
            Key::Backspace => Some(vec![
                (0, 0), // Caps Shift
                (4, 0), // 0
            ]),
            
            // Caps Lock: Caps Shift + 2 (CAPS LOCK)
            Key::CapsLock => Some(vec![
                (0, 0), // Caps Shift
                (3, 1), // 2
            ]),
            
            _ => None,
        }
    }

    /// Map PC key to ZX Spectrum matrix position (row, column)
    fn map_key(&self, key: Key) -> Option<(usize, usize)> {
        // ZX Spectrum keyboard layout matches port addresses:
        // Row 0 (0xFEFE, A8=0):  CAPS, Z, X, C, V
        // Row 1 (0xFDFE, A9=0):  A, S, D, F, G
        // Row 2 (0xFBFE, A10=0): Q, W, E, R, T
        // Row 3 (0xF7FE, A11=0): 1, 2, 3, 4, 5
        // Row 4 (0xEFFE, A12=0): 0, 9, 8, 7, 6
        // Row 5 (0xDFFE, A13=0): P, O, I, U, Y
        // Row 6 (0xBFFE, A14=0): Enter, L, K, J, H
        // Row 7 (0x7FFE, A15=0): Space, Sym, M, N, B

        match key {
            // Row 0: CAPS, Z, X, C, V
            Key::LeftShift | Key::RightShift => Some((0, 0)), // Caps Shift
            Key::Z => Some((0, 1)),
            Key::X => Some((0, 2)),
            Key::C => Some((0, 3)),
            Key::V => Some((0, 4)),

            // Row 1: A, S, D, F, G
            Key::A => Some((1, 0)),
            Key::S => Some((1, 1)),
            Key::D => Some((1, 2)),
            Key::F => Some((1, 3)),
            Key::G => Some((1, 4)),

            // Row 2: Q, W, E, R, T
            Key::Q => Some((2, 0)),
            Key::W => Some((2, 1)),
            Key::E => Some((2, 2)),
            Key::R => Some((2, 3)),
            Key::T => Some((2, 4)),

            // Row 3: 1, 2, 3, 4, 5
            Key::Key1 => Some((3, 0)),
            Key::Key2 => Some((3, 1)),
            Key::Key3 => Some((3, 2)),
            Key::Key4 => Some((3, 3)),
            Key::Key5 => Some((3, 4)),

            // Row 4: 0, 9, 8, 7, 6
            Key::Key0 => Some((4, 0)),
            Key::Key9 => Some((4, 1)),
            Key::Key8 => Some((4, 2)),
            Key::Key7 => Some((4, 3)),
            Key::Key6 => Some((4, 4)),

            // Row 5: P, O, I, U, Y
            Key::P => Some((5, 0)),
            Key::O => Some((5, 1)),
            Key::I => Some((5, 2)),
            Key::U => Some((5, 3)),
            Key::Y => Some((5, 4)),

            // Row 6: Enter, L, K, J, H
            Key::Enter => Some((6, 0)),
            Key::L => Some((6, 1)),
            Key::K => Some((6, 2)),
            Key::J => Some((6, 3)),
            Key::H => Some((6, 4)),

            // Row 7: Space, Symbol, M, N, B
            Key::Space => Some((7, 0)),
            Key::LeftCtrl | Key::RightCtrl => Some((7, 1)), // Symbol Shift
            Key::M => Some((7, 2)),
            Key::N => Some((7, 3)),
            Key::B => Some((7, 4)),

            _ => None,
        }
    }

    /// Check if a specific key is pressed
    pub fn is_key_pressed(&self, row: usize, col: usize) -> bool {
        if row < 8 && col < 5 {
            self.matrix[row] & (1 << col) == 0
        } else {
            false
        }
    }
}

impl Default for Keyboard {
    fn default() -> Self {
        Self::new()
    }
}
