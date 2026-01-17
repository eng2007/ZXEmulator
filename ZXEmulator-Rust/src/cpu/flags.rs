//! CPU flags

use bitflags::bitflags;

bitflags! {
    /// Z80 CPU status flags
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    pub struct Flags: u8 {
        /// Carry flag
        const C = 0b0000_0001;
        /// Add/Subtract flag
        const N = 0b0000_0010;
        /// Parity/Overflow flag
        const PV = 0b0000_0100;
        /// Undocumented flag (copy of bit 3)
        const F3 = 0b0000_1000;
        /// Half-carry flag
        const H = 0b0001_0000;
        /// Undocumented flag (copy of bit 5)
        const F5 = 0b0010_0000;
        /// Zero flag
        const Z = 0b0100_0000;
        /// Sign flag
        const S = 0b1000_0000;
    }
}

impl Flags {
    /// Calculate parity of a byte (true if even number of 1 bits)
    pub fn parity(value: u8) -> bool {
        value.count_ones() % 2 == 0
    }

    /// Calculate sign flag
    pub fn sign(value: u8) -> bool {
        value & 0x80 != 0
    }

    /// Calculate zero flag
    pub fn zero(value: u8) -> bool {
        value == 0
    }

    /// Get undocumented flags (bits 3 and 5) from value
    pub fn undoc(value: u8) -> Flags {
        Flags::from_bits_truncate(value & (Flags::F3.bits() | Flags::F5.bits()))
    }
}

/// Helper to build flags for 8-bit operations
pub fn sz53_flags(result: u8) -> Flags {
    let mut flags = Flags::empty();
    if result == 0 { flags |= Flags::Z; }
    if result & 0x80 != 0 { flags |= Flags::S; }
    flags |= Flags::undoc(result);
    flags
}

/// Helper for parity flag
pub fn parity_flag(value: u8) -> Flags {
    if Flags::parity(value) { Flags::PV } else { Flags::empty() }
}

/// Calculate flags for INC operation
pub fn inc_flags(value: u8, result: u8) -> Flags {
    let mut flags = sz53_flags(result);
    if value == 0x7F { flags |= Flags::PV; } // Overflow
    if (value & 0x0F) == 0x0F { flags |= Flags::H; } // Half-carry
    flags
}

/// Calculate flags for DEC operation
pub fn dec_flags(value: u8, result: u8) -> Flags {
    let mut flags = sz53_flags(result) | Flags::N;
    if value == 0x80 { flags |= Flags::PV; } // Overflow
    if (value & 0x0F) == 0x00 { flags |= Flags::H; } // Half-borrow
    flags
}

/// Calculate flags for ADD operation
pub fn add_flags(a: u8, b: u8, result: u8, carry: bool) -> Flags {
    let mut flags = sz53_flags(result);
    
    // Carry
    let sum = (a as u16) + (b as u16) + (carry as u16);
    if sum > 0xFF { flags |= Flags::C; }
    
    // Half-carry
    if ((a & 0x0F) + (b & 0x0F) + (carry as u8)) > 0x0F { flags |= Flags::H; }
    
    // Overflow
    let sa = (a as i8) as i16;
    let sb = (b as i8) as i16;
    let sum_signed = sa + sb + (carry as i16);
    if sum_signed < -128 || sum_signed > 127 { flags |= Flags::PV; }
    
    flags
}

/// Calculate flags for SUB operation
pub fn sub_flags(a: u8, b: u8, result: u8, carry: bool) -> Flags {
    let mut flags = sz53_flags(result) | Flags::N;
    
    // Carry (borrow)
    let diff = (a as i16) - (b as i16) - (carry as i16);
    if diff < 0 { flags |= Flags::C; }
    
    // Half-carry (half-borrow)
    if (a & 0x0F) < (b & 0x0F) + (carry as u8) { flags |= Flags::H; }
    
    // Overflow
    let sa = (a as i8) as i16;
    let sb = (b as i8) as i16;
    let diff_signed = sa - sb - (carry as i16);
    if diff_signed < -128 || diff_signed > 127 { flags |= Flags::PV; }
    
    flags
}

/// Calculate flags for logical AND
pub fn and_flags(result: u8) -> Flags {
    sz53_flags(result) | Flags::H | parity_flag(result)
}

/// Calculate flags for logical OR/XOR
pub fn or_xor_flags(result: u8) -> Flags {
    sz53_flags(result) | parity_flag(result)
}

/// Calculate flags for CP (compare) operation
pub fn cp_flags(a: u8, b: u8) -> Flags {
    let result = a.wrapping_sub(b);
    let mut flags = sub_flags(a, b, result, false);
    // Undocumented flags come from operand, not result
    flags &= !(Flags::F3 | Flags::F5);
    flags |= Flags::undoc(b);
    flags
}
