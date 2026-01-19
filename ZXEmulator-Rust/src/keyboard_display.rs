//! Keyboard display visualization with realistic ZX Spectrum styling

use crate::keyboard::Keyboard;

/// Keyboard display dimensions
pub const KB_WIDTH: usize = 900;
pub const KB_HEIGHT: usize = 320;

/// Key dimensions
const KEY_WIDTH: usize = 82;
const KEY_HEIGHT: usize = 66;
const KEY_GAP: usize = 6;
const MARGIN_X: usize = 12;
const MARGIN_Y: usize = 20; // Extra top margin for labels

/// Colors (ARGB)
const COLOR_BG: u32 = 0xFF000000;          // Black background
const COLOR_TEXT_WHITE: u32 = 0xFFFFFFFF;
const COLOR_TEXT_BLACK: u32 = 0xFF000000;
const COLOR_TEXT_RED: u32 = 0xFFCC0000;
const COLOR_TEXT_GREEN: u32 = 0xFF00CC00;
const COLOR_HIGHLIGHT: u32 = 0xFFDDDDDD;   // Pressed overlay

/// Key Colors
const KC_BLUE: u32 = 0xFF0000CC;
const KC_RED: u32 = 0xFFCC0000;
const KC_MAGENTA: u32 = 0xFFCC00CC;
const KC_GREEN: u32 = 0xFF00CC00;
const KC_CYAN: u32 = 0xFF00CCCC;
const KC_YELLOW: u32 = 0xFFCCCC00;
const KC_WHITE: u32 = 0xFFDDDDDD;
const KC_BLACK: u32 = 0xFF202020;
const KC_TAN: u32 = 0xFFCC8844;  // For main letter keys (orange/brownish)

/// Key styling configuration
struct KeyStyle<'a> {
    color: u32,
    main: &'a str,
    top: &'a str,         // Text above key / Top label
    tl: &'a str,          // Top-Left (E-mode red/green)
    tr: &'a str,          // Top-Right (Symbol red)
    bl: &'a str,          // Bottom-Left (Extended)
    br: &'a str,          // Bottom-Right (Keyword)
    main_color: u32,      // Color of main char
}

const EMPTY_KEY: KeyStyle = KeyStyle {
    color: KC_BLACK, main: "", top: "", tl: "", tr: "", bl: "", br: "", main_color: COLOR_TEXT_WHITE 
};

/// Row 1 Data (Numbers)
const ROW1_DATA: [KeyStyle; 10] = [
    KeyStyle { color: KC_BLUE,    main: "1", top: "BLUE",       tl: "EDIT",      tr: "!",  bl: "DEF FN",    br: "",      main_color: COLOR_TEXT_WHITE },
    KeyStyle { color: KC_RED,     main: "2", top: "RED",        tl: "CAPS LOCK", tr: "@",  bl: "FN",        br: "",      main_color: COLOR_TEXT_WHITE },
    KeyStyle { color: KC_MAGENTA, main: "3", top: "MAGENTA",    tl: "TRUE VID",  tr: "#",  bl: "LINE",      br: "",      main_color: COLOR_TEXT_WHITE },
    KeyStyle { color: KC_GREEN,   main: "4", top: "GREEN",      tl: "INV VID",   tr: "$",  bl: "OPEN #",    br: "",      main_color: COLOR_TEXT_WHITE },
    KeyStyle { color: KC_CYAN,    main: "5", top: "CYAN",       tl: "<-",        tr: "%",  bl: "CLOSE #",   br: "",      main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_YELLOW,  main: "6", top: "YELLOW",     tl: "v",         tr: "&",  bl: "MOVE",      br: "",      main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_WHITE,   main: "7", top: "WHITE",      tl: "^",         tr: "'",  bl: "ERASE",     br: "",      main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN,   main: "8", top: "",           tl: "->",        tr: "(",  bl: "POINT",     br: "",      main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN,   main: "9", top: "GRAPHICS",   tl: "",          tr: ")",  bl: "CAT",       br: "",      main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_BLACK,   main: "0", top: "BLACK",      tl: "DELETE",    tr: "_",  bl: "FORMAT",    br: "",      main_color: COLOR_TEXT_WHITE },
];

/// Row 2 Data (QWERTY)
const ROW2_DATA: [KeyStyle; 10] = [
    KeyStyle { color: KC_TAN, main: "Q", top: "SIN",     tl: "",    tr: "<=", bl: "ASN",    br: "PLOT",   main_color: COLOR_TEXT_BLACK }, // Correction: TL is usually redundant if on top. Following image style: TL on key
    KeyStyle { color: KC_TAN, main: "W", top: "COS",     tl: "",    tr: "<>", bl: "ACS",    br: "DRAW",   main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "E", top: "TAN",     tl: "",    tr: ">=", bl: "ATN",    br: "REM",    main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "R", top: "INT",     tl: "",    tr: "<",  bl: "VERIFY", br: "RUN",    main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "T", top: "RND",     tl: "",    tr: ">",  bl: "MERGE",  br: "RAND",   main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "Y", top: "STR$",    tl: "",    tr: "AND",bl: "[",      br: "RETURN", main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "U", top: "CHR$",    tl: "",    tr: "OR", bl: "]",      br: "IF",     main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "I", top: "CODE",    tl: "",    tr: "AT", bl: "IN",     br: "INPUT",  main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "O", top: "PEEK",    tl: "",    tr: ";",  bl: "OUT",    br: "POKE",   main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "P", top: "TAB",     tl: "",    tr: "\"", bl: "(c)",    br: "PRINT",  main_color: COLOR_TEXT_BLACK },
];

/// Row 3 Data (ASDF)
const ROW3_DATA: [KeyStyle; 10] = [
    KeyStyle { color: KC_TAN, main: "A", top: "READ",    tl: "STOP",tr: "~",  bl: "NEW",    br: "",       main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "S", top: "RESTORE", tl: "NOT", tr: "|",  bl: "SAVE",   br: "",       main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "D", top: "DATA",    tl: "STEP",tr: "\\", bl: "DIM",    br: "",       main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "F", top: "SGN",     tl: "TO",  tr: "{",  bl: "FOR",    br: "",       main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "G", top: "ABS",     tl: "THEN",tr: "}",  bl: "GOTO",   br: "",       main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "H", top: "SQR",     tl: "",   tr: "^",  bl: "CIRCLE", br: "GOSUB",  main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "J", top: "VAL",     tl: "",   tr: "-",  bl: "VAL$",   br: "LOAD",   main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "K", top: "LEN",     tl: "",   tr: "+",  bl: "SCRN$",  br: "LIST",   main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN, main: "L", top: "USR",     tl: "",   tr: "=",  bl: "ATTR",   br: "LET",    main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_RED, main: "ENTER", top: "",    tl: "",    tr: "",   bl: "",       br: "",       main_color: COLOR_TEXT_BLACK },
];

/// Row 4 Data (ZXCV)
const ROW4_DATA: [KeyStyle; 10] = [
    KeyStyle { color: KC_RED,     main: "CAPS", top: "",      tl: "",    tr: "",   bl: "",   br: "SHIFT",  main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN,   main: "Z",    top: "LN",      tl: "",   tr: ":",  bl: "BEEP",   br: "COPY",   main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN,   main: "X",    top: "EXP",     tl: "",   tr: "L",  bl: "INK",    br: "CLEAR",  main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN,   main: "C",    top: "LPRINT",  tl: "",   tr: "?",  bl: "PAPER",  br: "CONT",   main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN,   main: "V",    top: "LLIST",   tl: "",   tr: "/",  bl: "FLASH",  br: "CLS",    main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN,   main: "B",    top: "BIN",     tl: "",   tr: "*",  bl: "BRIGHT", br: "BORDER", main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN,   main: "N",    top: "INKEY$",  tl: "",   tr: ",",  bl: "OVER",   br: "NEXT",   main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_TAN,   main: "M",    top: "PI",      tl: "",   tr: ".",  bl: "INV",    br: "PAUSE",  main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_YELLOW,  main: "SYMBOL", top: "",    tl: "",    tr: "",   bl: "",       br: "SHIFT",  main_color: COLOR_TEXT_BLACK },
    KeyStyle { color: KC_BLUE,    main: "SPACE",  top: "",    tl: "",    tr: "",   bl: "",       br: "BREAK",  main_color: COLOR_TEXT_WHITE },
];

const ALL_ROWS: [&[KeyStyle; 10]; 4] = [&ROW1_DATA, &ROW2_DATA, &ROW3_DATA, &ROW4_DATA];

/// Key matrix positions (Hardware mapping)
const KEY_MATRIX: [[(usize, usize); 10]; 4] = [
    [(3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (4, 4), (4, 3), (4, 2), (4, 1), (4, 0)], // 1..0
    [(2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (5, 4), (5, 3), (5, 2), (5, 1), (5, 0)], // Q..P
    [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (6, 4), (6, 3), (6, 2), (6, 1), (6, 0)], // A..Enter
    [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (7, 4), (7, 3), (7, 2), (7, 1), (7, 0)], // Caps..Space
];

/// 5x7 Font Bitmap (Basic ASCII + some block graphics)
const FONT_5X7: [(char, [u8; 7]); 60] = [
    ('0', [0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E]),
    ('1', [0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E]),
    ('2', [0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F]),
    ('3', [0x0E, 0x11, 0x01, 0x06, 0x01, 0x11, 0x0E]),
    ('4', [0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02]),
    ('5', [0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E]),
    ('6', [0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E]),
    ('7', [0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08]),
    ('8', [0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E]),
    ('9', [0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C]),
    ('A', [0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11]),
    ('B', [0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E]),
    ('C', [0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E]),
    ('D', [0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E]),
    ('E', [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F]),
    ('F', [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10]),
    ('G', [0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0E]),
    ('H', [0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11]),
    ('I', [0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E]),
    ('J', [0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C]),
    ('K', [0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11]),
    ('L', [0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F]),
    ('M', [0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11]),
    ('N', [0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11]),
    ('O', [0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E]),
    ('P', [0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10]),
    ('Q', [0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D]),
    ('R', [0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11]),
    ('S', [0x0E, 0x11, 0x10, 0x0E, 0x01, 0x11, 0x0E]),
    ('T', [0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04]),
    ('U', [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E]),
    ('V', [0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04]),
    ('W', [0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11]),
    ('X', [0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11]),
    ('Y', [0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04]),
    ('Z', [0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F]),
    ('!', [0x04, 0x04, 0x04, 0x04, 0x00, 0x00, 0x04]),
    ('@', [0x0E, 0x11, 0x11, 0x19, 0x15, 0x15, 0x0E]),
    ('#', [0x0A, 0x1F, 0x0A, 0x0A, 0x1F, 0x0A, 0x00]),
    ('$', [0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04]),
    ('%', [0x11, 0x02, 0x04, 0x08, 0x10, 0x20, 0x22]),
    ('&', [0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D]),
    ('\'', [0x0C, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00]),
    ('(', [0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02]),
    (')', [0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08]),
    ('_', [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F]),
    ('<', [0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02]),
    ('>', [0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08]),
    ('^', [0x04, 0x0A, 0x11, 0x00, 0x00, 0x00, 0x00]), // Used for up arrow
    ('-', [0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00]),
    ('+', [0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00]),
    ('=', [0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00]),
    (':', [0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00]),
    (';', [0x00, 0x0C, 0x0C, 0x00, 0x04, 0x08, 0x00]),
    ('"', [0x0A, 0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00]),
    (',', [0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08]),
    ('.', [0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C]),
    ('/', [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x00]),
    ('*', [0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00]),
    ('?', [0x0E, 0x11, 0x01, 0x02, 0x00, 0x00, 0x02]),
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

        for (row_idx, row_data) in ALL_ROWS.iter().enumerate() {
            for (col_idx, key_style) in row_data.iter().enumerate() {
                let (matrix_row, matrix_col) = KEY_MATRIX[row_idx][col_idx];
                let pressed = keyboard.is_key_pressed(matrix_row, matrix_col);
                
                let x = MARGIN_X + col_idx * (KEY_WIDTH + KEY_GAP);
                let y = MARGIN_Y + row_idx * (KEY_HEIGHT + KEY_GAP);
                
                self.draw_key(x, y, key_style, pressed);
            }
        }
    }

    /// Draw a styled key
    fn draw_key(&mut self, x: usize, y: usize, style: &KeyStyle, pressed: bool) {
        // Draw top label (above the key) if exists
        if !style.top.is_empty() {
             // For row 1, color matches key cap. For others, typically white/grey
             let top_color = if style.main.parse::<u8>().is_ok() && style.main.len() == 1 { style.color } else { COLOR_TEXT_WHITE };
             self.draw_text_tiny(x + KEY_WIDTH/2, y - 4, style.top, top_color);
        }

        // Draw key body
        let mut key_color = style.color;
        if pressed {
            // Simple highlight blending
            let r = ((key_color >> 16) & 0xFF) + 40;
            let g = ((key_color >> 8) & 0xFF) + 40;
            let b = (key_color & 0xFF) + 40;
            key_color = (r.min(255) << 16) | (g.min(255) << 8) | b.min(255);
        }
        
        // Draw rectangle
        self.fill_rect(x, y, KEY_WIDTH, KEY_HEIGHT, key_color);
        
        // Main Label (Center or slightly left)
        // Check if double height label (CAPS SHIFT etc)
        if style.main.contains(" ") || style.main.len() > 2 {
             // Split words
             let parts: Vec<&str> = style.main.split(' ').collect();
             for (i, part) in parts.iter().enumerate() {
                 self.draw_text(x + 4, y + 10 + i*10, part, style.main_color);
             }
        } else {
             self.draw_text(x + 6, y + 6, style.main, style.main_color);
        }
        
        // Top Left (E-mode) - Red usually, or Green 
        if !style.tl.is_empty() {
            self.draw_text_tiny(x + KEY_WIDTH - (style.tl.len()*4) - 4, y + 4, style.tl, COLOR_TEXT_RED);
        }
        
        // Top Right (Symbol) - Red
        if !style.tr.is_empty() {
             self.draw_text_tiny(x + KEY_WIDTH - (style.tr.len()*4) - 4, y + 16, style.tr, COLOR_TEXT_RED);
        }
        
        // Bottom Right (Keyword K-Mode) - White/Black
        if !style.br.is_empty() {
             self.draw_text_tiny(x + KEY_WIDTH - (style.br.len()*4) - 4, y + KEY_HEIGHT - 10, style.br, style.main_color);
        }
        
         // Bottom Left (Extended/Other)
        if !style.bl.is_empty() {
             self.draw_text_tiny(x + 4, y + KEY_HEIGHT - 10, style.bl, style.main_color);
        }
    }

    fn fill_rect(&mut self, x: usize, y: usize, w: usize, h: usize, color: u32) {
        for dy in 0..h {
            for dx in 0..w {
                let px = x + dx;
                let py = y + dy;
                if px < KB_WIDTH && py < KB_HEIGHT {
                    self.buffer[py * KB_WIDTH + px] = color;
                }
            }
        }
    }

    /// Draw text using 5x7 font
    fn draw_text(&mut self, cx: usize, cy: usize, text: &str, color: u32) {
        let char_spacing = 6;
        for (i, ch) in text.chars().enumerate() {
             self.draw_char(cx + i * char_spacing, cy, ch, color);
        }
    }
    
    /// Draw smaller text (using same font but maybe we could scale down? 
    /// For now just using same font but carefully placed)
    fn draw_text_tiny(&mut self, cx: usize, cy: usize, text: &str, color: u32) {
        // Centered anchor logic
        let width = text.len() * 6;
        let start_x = cx.saturating_sub(width/2); 
        self.draw_text(start_x, cy, text, color);
    }

    fn draw_char(&mut self, x: usize, y: usize, ch: char, color: u32) {
        if let Some((_, pattern)) = FONT_5X7.iter().find(|(c, _)| *c == ch.to_ascii_uppercase()) {
            for (row, &bits) in pattern.iter().enumerate() {
                for col in 0..5 {
                    if (bits >> (4 - col)) & 1 == 1 {
                        let px = x + col;
                        let py = y + row;
                         if px < KB_WIDTH && py < KB_HEIGHT {
                            self.buffer[py * KB_WIDTH + px] = color;
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
