//! Snapshot loading for ZX Spectrum (.sna and .z80 formats)

use crate::memory::Memory;
use crate::cpu::Z80;
use std::fs::File;
use std::io::{self, Read};

/// Load a snapshot file (auto-detect format)
pub fn load_snapshot(path: &str, cpu: &mut Z80, memory: &mut Memory) -> io::Result<()> {
    let path_lower = path.to_lowercase();
    
    if path_lower.ends_with(".sna") {
        load_sna(path, cpu, memory)
    } else if path_lower.ends_with(".z80") {
        load_z80(path, cpu, memory)
    } else {
        Err(io::Error::new(io::ErrorKind::InvalidInput, "Unknown snapshot format"))
    }
}

/// Load SNA snapshot (48K only)
pub fn load_sna(path: &str, cpu: &mut Z80, memory: &mut Memory) -> io::Result<()> {
    let mut file = File::open(path)?;
    let mut data = Vec::new();
    file.read_to_end(&mut data)?;

    if data.len() < 27 + 49152 {
        return Err(io::Error::new(io::ErrorKind::InvalidData, "SNA file too small"));
    }

    memory.reset();

    // If we are in 128K mode, we need to switch to 48K mode (ROM 1) and lock paging
    if memory.is_128k_mode() {
        memory.write_7ffd(0x30); // ROM 1, Disable Paging, Bank 0, Screen 5
    }

    // Load registers from header
    cpu.i = data[0];
    cpu.hl_prime = u16::from_le_bytes([data[1], data[2]]);
    cpu.de_prime = u16::from_le_bytes([data[3], data[4]]);
    cpu.bc_prime = u16::from_le_bytes([data[5], data[6]]);
    cpu.af_prime = u16::from_le_bytes([data[7], data[8]]);

    cpu.hl = u16::from_le_bytes([data[9], data[10]]);
    cpu.de = u16::from_le_bytes([data[11], data[12]]);
    cpu.bc = u16::from_le_bytes([data[13], data[14]]);
    cpu.iy = u16::from_le_bytes([data[15], data[16]]);
    cpu.ix = u16::from_le_bytes([data[17], data[18]]);

    // Interrupt status
    let iff2 = data[19] & 0x04 != 0;
    cpu.iff1 = iff2;
    cpu.iff2 = iff2;

    cpu.r = data[20];
    cpu.af = u16::from_le_bytes([data[21], data[22]]);
    cpu.sp = u16::from_le_bytes([data[23], data[24]]);
    cpu.im = data[25] & 0x03;

    // Border color is at offset 26 (we ignore it for now)
    // let border = data[26];

    // Load RAM (48K from 0x4000)
    let ram = memory.get_ram_mut();
    for i in 0..49152 {
        // SNA data goes to addresses 0x4000-0xFFFF (banks 5, 2, 0)
        let addr = 0x4000 + i;
        memory.write(addr as u16, data[27 + i]);
    }

    // SNA stores PC on stack, so we pop it
    cpu.pc = memory.read_word(cpu.sp);
    cpu.sp = cpu.sp.wrapping_add(2);

    cpu.halted = false;

    Ok(())}

/// Load Z80 snapshot (48K/128K)
pub fn load_z80(path: &str, cpu: &mut Z80, memory: &mut Memory) -> io::Result<()> {
    let mut file = File::open(path)?;
    let mut data = Vec::new();
    file.read_to_end(&mut data)?;

    if data.len() < 30 {
        return Err(io::Error::new(io::ErrorKind::InvalidData, "Z80 file too small"));
    }

    // Z80 v1 header
    cpu.af = u16::from_le_bytes([data[1], data[0]]); // Note: swapped
    cpu.bc = u16::from_le_bytes([data[2], data[3]]);
    cpu.hl = u16::from_le_bytes([data[4], data[5]]);
    cpu.pc = u16::from_le_bytes([data[6], data[7]]);
    cpu.sp = u16::from_le_bytes([data[8], data[9]]);
    cpu.i = data[10];
    cpu.r = (data[11] & 0x7F) | ((data[12] & 0x01) << 7);

    let flags = data[12];
    // let border = (flags >> 1) & 0x07;
    let compressed = flags & 0x20 != 0;

    cpu.de = u16::from_le_bytes([data[13], data[14]]);
    cpu.bc_prime = u16::from_le_bytes([data[15], data[16]]);
    cpu.de_prime = u16::from_le_bytes([data[17], data[18]]);
    cpu.hl_prime = u16::from_le_bytes([data[19], data[20]]);
    cpu.af_prime = u16::from_le_bytes([data[22], data[21]]); // Swapped

    cpu.iy = u16::from_le_bytes([data[23], data[24]]);
    cpu.ix = u16::from_le_bytes([data[25], data[26]]);

    cpu.iff1 = data[27] != 0;
    cpu.iff2 = data[28] != 0;
    cpu.im = data[29] & 0x03;

    // Check if v1 (PC != 0) or v2/v3 (PC == 0)
    if cpu.pc != 0 {
        // Version 1 format - 48K only
        let mem_data = &data[30..];
        if compressed {
            decompress_block(mem_data, memory, 0x4000, 49152)?;
        } else {
            for (i, &byte) in mem_data.iter().take(49152).enumerate() {
                memory.write((0x4000 + i) as u16, byte);
            }
        }
    } else {
        // Version 2/3 format
        let extra_len = u16::from_le_bytes([data[30], data[31]]) as usize;
        cpu.pc = u16::from_le_bytes([data[32], data[33]]);

        let hw_mode = data[34];
        let is_128k = hw_mode >= 3;

        // Skip to memory blocks
        let mut offset = 32 + extra_len;

        while offset + 3 <= data.len() {
            let block_len = u16::from_le_bytes([data[offset], data[offset + 1]]) as usize;
            let page = data[offset + 2];
            offset += 3;

            if offset + block_len > data.len() {
                break;
            }

            let (addr, len) = if is_128k {
                match page {
                    3 => (0x0000, 16384), // ROM or bank 0
                    4 => (0x8000, 16384), // Bank 2
                    5 => (0x4000, 16384), // Bank 5
                    p if p >= 6 => (0xC000, 16384), // Other banks
                    _ => { offset += block_len; continue; }
                }
            } else {
                match page {
                    4 => (0x8000, 16384),
                    5 => (0xC000, 16384),
                    8 => (0x4000, 16384),
                    _ => { offset += block_len; continue; }
                }
            };

            let block_data = &data[offset..offset + block_len];
            if block_len == 0xFFFF {
                // Uncompressed block
                for (i, &byte) in data[offset..offset + len].iter().enumerate() {
                    memory.write((addr + i) as u16, byte);
                }
            } else {
                decompress_block(block_data, memory, addr as u16, len)?;
            }

            offset += block_len;
        }
    }

    cpu.halted = false;

    Ok(())
}

/// Decompress RLE-encoded block
fn decompress_block(data: &[u8], memory: &mut Memory, start: u16, max_len: usize) -> io::Result<()> {
    let mut src = 0;
    let mut dst = 0;

    while src < data.len() && dst < max_len {
        if src + 3 < data.len() && data[src] == 0xED && data[src + 1] == 0xED {
            // RLE sequence: ED ED count byte
            let count = data[src + 2] as usize;
            let byte = data[src + 3];
            for _ in 0..count {
                if dst < max_len {
                    memory.write(start.wrapping_add(dst as u16), byte);
                    dst += 1;
                }
            }
            src += 4;
        } else {
            memory.write(start.wrapping_add(dst as u16), data[src]);
            src += 1;
            dst += 1;
        }
    }

    Ok(())
}

/// Load ROM file
pub fn load_rom(path: &str, memory: &mut Memory) -> io::Result<()> {
    let mut file = File::open(path)?;
    let mut data = Vec::new();
    file.read_to_end(&mut data)?;

    if data.len() >= 32768 {
        // 128K ROM
        memory.load_rom_128k(&data);
    } else {
        // 48K ROM
        memory.load_rom(&data, 0);
    }

    Ok(())
}
