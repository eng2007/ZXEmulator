//! Keyboard display visualization with ZX Spectrum BASIC commands

use crate::keyboard::Keyboard;

/// Keyboard display dimensions
pub const KB_WIDTH: usize = 640;
pub const KB_HEIGHT: usize = 280;

/// Key dimensions
const KEY_WIDTH: usize = 58;
const KEY_HEIGHT: usize = 60;
const KEY_GAP: usize = 6;
const MARGIN: usize = 10;

/// Colors (ARGB)
const COLOR_BG: u32 = 0xFF1A1A2E;
const COLOR_KEY: u32 = 0xFF16213E;
const COLOR_KEY_PRESSED: u32 = 0xFFE94560;
const COLOR_KEY_BORDER: u32 = 0xFF0F3460;
const COLOR_TEXT_MAIN: u32 = 0xFFFFFFFF;
const COLOR_TEXT_CMD: u32 = 0xFF00DD00;  // Green for main command
const COLOR_TEXT_EXT: u32 = 0xFFDD0000;  // Red for extended

/// Key data: main label, basic command, extended mode
const KEY_DATA: [[[&str; 3]; 10]; 4] = [
    // Row 1: numbers
    [
        ["1", "EDIT", "DEF FN"],
        ["2", "CAPS", "FN"],
        ["3", "TRUE", "LINE"],
        ["4", "INV", "OPEN#"],
        ["5", "<-", "CLOSE"],
        ["6", "v", "MOVE"],
        ["7", "^", "ERASE"],
        ["8", "->", "POINT"],
        ["9", "GRPH", "CAT"],
        ["0", "DEL", "FRMT"],
    ],
    // Row 2: QWERTY
    [
        ["Q", "PLOT", "ASN"],
        ["W", "DRAW", "ACS"],
        ["E", "REM", "ATN"],
        ["R", "RUN", "VRFY"],
        ["T", "RAND", "MRGE"],
        ["Y", "RET", "STR$"],
        ["U", "IF", "CHR$"],
        ["I", "INPT", "CODE"],
        ["O", "POKE", "PEEK"],
        ["P", "PRNT", "TAB"],
    ],
    // Row 3: ASDF
    [
        ["A", "NEW", "READ"],
        ["S", "SAVE", "REST"],
        ["D", "DIM", "DATA"],
        ["F", "FOR", "SGN"],
        ["G", "GOTO", "ABS"],
        ["H", "GSUB", "SQR"],
        ["J", "LOAD", "VAL"],
        ["K", "LIST", "LEN"],
        ["L", "LET", "USR"],
        ["En", "", ""],
    ],
    // Row 4: ZXCV
    [
        ["Cs", "", ""],
        ["Z", "COPY", "LN"],
        ["X", "CLR", "EXP"],
        ["C", "CONT", "LPRT"],
        ["V", "CLS", "LLST"],
        ["B", "BRDR", "BIN"],
        ["N", "NEXT", "INKY"],
        ["M", "PAUS", "PI"],
        ["Ss", "", ""],
        ["Sp", "BRK", ""],
    ],
];

/// Key matrix positions
const KEY_MATRIX: [[(usize, usize); 10]; 4] = [
    [(3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (4, 4), (4, 3), (4, 2), (4, 1), (4, 0)],
    [(2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (5, 4), (5, 3), (5, 2), (5, 1), (5, 0)],
    [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (6, 4), (6, 3), (6, 2), (6, 1), (6, 0)],
    [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (7, 4), (7, 3), (7, 2), (7, 1), (7, 0)],
];

/// 5x7 font bitmaps
const FONT_5X7: [(char, [u8; 7]); 50] = [
    ('0', [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110]),
    ('1', [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110]),
    ('2', [0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111]),
    ('3', [0b01110, 0b10001, 0b00001, 0b00110, 0b00001, 0b10001, 0b01110]),
    ('4', [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010]),
    ('5', [0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110]),
    ('6', [0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110]),
    ('7', [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000]),
    ('8', [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110]),
    ('9', [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100]),
    ('A', [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001]),
    ('B', [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110]),
    ('C', [0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110]),
    ('D', [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110]),
    ('E', [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111]),
    ('F', [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000]),
    ('G', [0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01110]),
    ('H', [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001]),
    ('I', [0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110]),
    ('J', [0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100]),
    ('K', [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001]),
    ('L', [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111]),
    ('M', [0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001]),
    ('N', [0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001]),
    ('O', [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110]),
    ('P', [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000]),
    ('Q', [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101]),
    ('R', [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001]),
    ('S', [0b01110, 0b10001, 0b10000, 0b01110, 0b00001, 0b10001, 0b01110]),
    ('T', [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100]),
    ('U', [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110]),
    ('V', [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100]),
    ('W', [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001]),
    ('X', [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001]),
    ('Y', [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100]),
    ('Z', [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111]),
    // Lowercase for commands
    ('n', [0b00000, 0b00000, 0b10110, 0b11001, 0b10001, 0b10001, 0b10001]),
    ('s', [0b00000, 0b00000, 0b01110, 0b10000, 0b01110, 0b00001, 0b11110]),
    ('p', [0b00000, 0b00000, 0b11110, 0b10001, 0b11110, 0b10000, 0b10000]),
    ('#', [0b01010, 0b11111, 0b01010, 0b01010, 0b11111, 0b01010, 0b00000]),
    ('$', [0b00100, 0b01111, 0b10100, 0b01110, 0b00101, 0b11110, 0b00100]),
    ('-', [0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000]),
    ('>', [0b01000, 0b00100, 0b00010, 0b00001, 0b00010, 0b00100, 0b01000]),
    ('<', [0b00010, 0b00100, 0b01000, 0b10000, 0b01000, 0b00100, 0b00010]),
    ('^', [0b00100, 0b01010, 0b10001, 0b00000, 0b00000, 0b00000, 0b00000]),
    ('v', [0b00000, 0b00000, 0b00000, 0b10001, 0b01010, 0b00100, 0b00000]),
    (' ', [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000]),
    ('*', [0b00000, 0b00100, 0b10101, 0b01110, 0b10101, 0b00100, 0b00000]),
    ('/', [0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b00000, 0b00000]),
    ('.', [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b01100, 0b01100]),
];

/// Keyboard display renderer
pub struct KeyboardDisplay {
    pub buffer: Vec<u32>,
}

impl KeyboardDisplay {
    pub fn new() -> Self {
        Self {
            buffer: vec![COLOR_BG; KB_WIDTH * KB_HEIGHT],
        }
    }

    /// Render keyboard with pressed keys highlighted
    pub fn render(&mut self, keyboard: &Keyboard) {
        self.buffer.fill(COLOR_BG);

        for (row_idx, row) in KEY_DATA.iter().enumerate() {
            for (col_idx, key_info) in row.iter().enumerate() {
                let (matrix_row, matrix_col) = KEY_MATRIX[row_idx][col_idx];
                let pressed = keyboard.is_key_pressed(matrix_row, matrix_col);
                
                let x = MARGIN + col_idx * (KEY_WIDTH + KEY_GAP);
                let y = MARGIN + row_idx * (KEY_HEIGHT + KEY_GAP);
                
                self.draw_key(x, y, key_info, pressed);
            }
        }
    }

    /// Draw a single key with main label and commands
    fn draw_key(&mut self, x: usize, y: usize, key_info: &[&str; 3], pressed: bool) {
        let bg_color = if pressed { COLOR_KEY_PRESSED } else { COLOR_KEY };
        
        // Draw key background
        for dy in 0..KEY_HEIGHT {
            for dx in 0..KEY_WIDTH {
                let px = x + dx;
                let py = y + dy;
                if px < KB_WIDTH && py < KB_HEIGHT {
                    let idx = py * KB_WIDTH + px;
                    let is_border = dx < 2 || dx >= KEY_WIDTH - 2 || dy < 2 || dy >= KEY_HEIGHT - 2;
                    self.buffer[idx] = if is_border { COLOR_KEY_BORDER } else { bg_color };
                }
            }
        }

        let main_label = key_info[0];
        let basic_cmd = key_info[1];
        let ext_cmd = key_info[2];

        // Main key label (center, large)
        self.draw_text(x + KEY_WIDTH / 2, y + 14, main_label, COLOR_TEXT_MAIN);

        // BASIC command (green, below main)
        if !basic_cmd.is_empty() {
            self.draw_text_small(x + KEY_WIDTH / 2, y + 32, basic_cmd, COLOR_TEXT_CMD);
        }

        // Extended command (red, bottom)
        if !ext_cmd.is_empty() {
            self.draw_text_small(x + KEY_WIDTH / 2, y + 48, ext_cmd, COLOR_TEXT_EXT);
        }
    }

    /// Draw text centered at position (5x7 font)
    fn draw_text(&mut self, cx: usize, cy: usize, text: &str, color: u32) {
        let char_width = 6;
        let text_width = text.len() * char_width;
        let start_x = cx.saturating_sub(text_width / 2);
        let start_y = cy.saturating_sub(3);

        for (char_idx, ch) in text.to_uppercase().chars().enumerate() {
            if let Some((_, pattern)) = FONT_5X7.iter().find(|(c, _)| *c == ch) {
                let char_x = start_x + char_idx * char_width;
                for (row, &bits) in pattern.iter().enumerate() {
                    for col in 0..5 {
                        if bits & (1 << (4 - col)) != 0 {
                            let px = char_x + col;
                            let py = start_y + row;
                            if px < KB_WIDTH && py < KB_HEIGHT {
                                self.buffer[py * KB_WIDTH + px] = color;
                            }
                        }
                    }
                }
            }
        }
    }

    /// Draw smaller text (4x6 effective, spaced tighter)
    fn draw_text_small(&mut self, cx: usize, cy: usize, text: &str, color: u32) {
        let char_width = 5;
        let text_width = text.len() * char_width;
        let start_x = cx.saturating_sub(text_width / 2);
        let start_y = cy.saturating_sub(3);

        for (char_idx, ch) in text.to_uppercase().chars().enumerate() {
            if let Some((_, pattern)) = FONT_5X7.iter().find(|(c, _)| *c == ch) {
                let char_x = start_x + char_idx * char_width;
                for (row, &bits) in pattern.iter().enumerate() {
                    for col in 0..5 {
                        if bits & (1 << (4 - col)) != 0 {
                            let px = char_x + col;
                            let py = start_y + row;
                            if px < KB_WIDTH && py < KB_HEIGHT {
                                self.buffer[py * KB_WIDTH + px] = color;
                            }
                        }
                    }
                }
            }
        }
    }

    pub fn get_buffer(&self) -> &[u32] {
        &self.buffer
    }
}

impl Default for KeyboardDisplay {
    fn default() -> Self {
        Self::new()
    }
}
