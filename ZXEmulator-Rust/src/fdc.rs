//! WD1793 Floppy Disk Controller (FDC) emulation
//!
//! Emulates the WD1793 controller used in Beta Disk and Pentagon interfaces

use crate::trd::TrdDisk;

/// WD1793 FDC status register flags
const STATUS_BUSY: u8 = 0x01;
const STATUS_DRQ: u8 = 0x02;       // Data Request
const STATUS_TRACK_0: u8 = 0x04;   // Head at track 0
const STATUS_CRC: u8 = 0x08;       // CRC error
const STATUS_SEEK_ERROR: u8 = 0x10;
const STATUS_RECORD_NOT_FOUND: u8 = 0x10;
const STATUS_HEAD_LOADED: u8 = 0x20;
const STATUS_WRITE_PROTECT: u8 = 0x40;
const STATUS_NOT_READY: u8 = 0x80;

/// WD1793 command types
const CMD_RESTORE: u8 = 0x00;
const CMD_SEEK: u8 = 0x10;
const CMD_STEP: u8 = 0x20;
const CMD_READ_SECTOR: u8 = 0x80;
const CMD_WRITE_SECTOR: u8 = 0xA0;
const CMD_READ_ADDRESS: u8 = 0xC0;
const CMD_FORCE_INTERRUPT: u8 = 0xD0;

/// FDC state machine states
#[derive(Debug, Clone, Copy, PartialEq)]
enum FdcState {
    Idle,
    Seeking,
    ReadingSector,
    WritingSector,
    ReadingAddress,
}

/// WD1793 Floppy Disk Controller
pub struct FDC {
    /// Command/Status register (port 0x1F)
    status: u8,
    
    /// Track register (port 0x3F)
    track: u8,
    
    /// Sector register (port 0x5F)
    sector: u8,
    
    /// Data register (port 0x7F)
    data: u8,
    
    /// System register (port 0xFF)
    /// Bit 0: Drive select bit 0
    /// Bit 1: Drive select bit 1
    /// Bit 2: Side select (0 = side A, 1 = side B)
    /// Bit 3: Reset (active low)
    /// Bit 4: Motor on/off
    system: u8,
    
    /// Current state
    state: FdcState,
    
    /// Current head position
    head_track: u8,
    
    /// Current side (0 or 1)
    side: u8,
    
    /// Current drive (0-3)
    drive: u8,
    
    /// Mounted disks (4 drives)
    disks: [Option<TrdDisk>; 4],
    
    /// Sector buffer for read/write operations
    sector_buffer: Vec<u8>,
    
    /// Buffer position for DRQ operations
    buffer_pos: usize,
    
    /// Motor on flag
    motor_on: bool,
    
    /// DRQ (Data Request) flag
    drq: bool,
    
    /// INTRQ (Interrupt Request) flag
    intrq: bool,
}

impl FDC {
    /// Create new FDC
    pub fn new() -> Self {
        Self {
            status: STATUS_TRACK_0,
            track: 0,
            sector: 1,
            data: 0,
            system: 0,
            state: FdcState::Idle,
            head_track: 0,
            side: 0,
            drive: 0,
            disks: [None, None, None, None],
            sector_buffer: Vec::new(),
            buffer_pos: 0,
            motor_on: false,
            drq: false,
            intrq: false,
        }
    }

    /// Load disk into drive
    pub fn load_disk(&mut self, drive: usize, disk: TrdDisk) {
        if drive < 4 {
            self.disks[drive] = Some(disk);
        }
    }

    /// Unload disk from drive
    pub fn unload_disk(&mut self, drive: usize) {
        if drive < 4 {
            self.disks[drive] = None;
        }
    }

    /// Read command/status register (port 0x1F)
    pub fn read_status(&mut self) -> u8 {
        // Clear INTRQ on status read
        self.intrq = false;
        
        let mut status = self.status;
        
        // Update status flags
        if self.drq {
            status |= STATUS_DRQ;
        }
        
        if self.head_track == 0 {
            status |= STATUS_TRACK_0;
        }
        
        // Check if disk is ready
        if self.disks[self.drive as usize].is_none() || !self.motor_on {
            status |= STATUS_NOT_READY;
        }
        
        println!("[FDC] Read status: 0x{:02X} (BUSY={} DRQ={} NOT_READY={} TRACK0={})", 
            status,
            (status & STATUS_BUSY) != 0,
            (status & STATUS_DRQ) != 0,
            (status & STATUS_NOT_READY) != 0,
            (status & STATUS_TRACK_0) != 0
        );
        
        status
    }

    /// Write command register (port 0x1F)
    pub fn write_command(&mut self, cmd: u8) {
        // Determine command type
        let cmd_type = cmd & 0xF0;
        
        println!("[FDC] Command 0x{:02X}, type 0x{:02X}", cmd, cmd_type);
        
        match cmd_type {
            CMD_RESTORE => {
                println!("[FDC] -> RESTORE");
                self.cmd_restore();
            }
            CMD_SEEK => {
                println!("[FDC] -> SEEK");
                self.cmd_seek();
            }
            CMD_STEP => {
                println!("[FDC] -> STEP");
                self.cmd_step(cmd);
            }
            CMD_READ_SECTOR => {
                println!("[FDC] -> READ_SECTOR");
                self.cmd_read_sector(cmd);
            }
            CMD_WRITE_SECTOR => {
                println!("[FDC] -> WRITE_SECTOR");
                self.cmd_write_sector(cmd);
            }
            CMD_READ_ADDRESS => {
                println!("[FDC] -> READ_ADDRESS");
                self.cmd_read_address();
            }
            CMD_FORCE_INTERRUPT => {
                println!("[FDC] -> FORCE_INTERRUPT");
                self.cmd_force_interrupt();
            }
            _ => {
                // For commands like 0x30, 0x40, 0x50 (step variants)
                if cmd_type >= 0x20 && cmd_type < 0x80 {
                    println!("[FDC] -> STEP variant");
                    self.cmd_step(cmd);
                } else {
                    println!("[FDC] -> UNKNOWN COMMAND!");
                }
            }
        }
    }

    /// Read track register (port 0x3F)
    pub fn read_track(&self) -> u8 {
        self.track
    }

    /// Write track register (port 0x3F)
    pub fn write_track(&mut self, value: u8) {
        self.track = value;
    }

    /// Read sector register (port 0x5F)
    pub fn read_sector(&self) -> u8 {
        self.sector
    }

    /// Write sector register (port 0x5F)
    pub fn write_sector(&mut self, value: u8) {
        self.sector = value;
    }

    /// Read data register (port 0x7F)
    pub fn read_data(&mut self) -> u8 {
        self.drq = false;
        
        if self.buffer_pos < self.sector_buffer.len() {
            let data = self.sector_buffer[self.buffer_pos];
            self.buffer_pos += 1;
            
            // If buffer finished, end operation
            if self.buffer_pos >= self.sector_buffer.len() {
                self.status &= !STATUS_BUSY;
                self.state = FdcState::Idle;
                self.intrq = true;
            } else {
                // Set DRQ for next byte
                self.drq = true;
            }
            
            data
        } else {
            0xFF
        }
    }

    /// Write data register (port 0x7F)
    pub fn write_data(&mut self, value: u8) {
        self.drq = false;
        
        if self.buffer_pos < self.sector_buffer.len() {
            self.sector_buffer[self.buffer_pos] = value;
            self.buffer_pos += 1;
            
            // If buffer finished, write to disk
            if self.buffer_pos >= self.sector_buffer.len() {
                self.execute_write_sector();
                self.status &= !STATUS_BUSY;
                self.state = FdcState::Idle;
                self.intrq = true;
            } else {
                // Set DRQ for next byte
                self.drq = true;
            }
        }
    }

    /// Read system register (port 0xFF)
    /// In Beta Disk interface, reading port 0xFF returns:
    /// Bit 6: INTRQ - Interrupt Request from FDC
    /// Bit 7: DRQ - Data Request from FDC
    /// Bits 0-5: Usually return 0x3F (all high)
    /// NOTE: Reading this port does NOT clear INTRQ (only reading 0x1F does)
    pub fn read_system(&mut self) -> u8 {
        let mut result = 0x3F; // Bits 0-5 typically high
        
        if self.intrq {
            result |= 0x40; // Bit 6: INTRQ
        }
        
        if self.drq {
            result |= 0x80; // Bit 7: DRQ
        }
        
        static mut LOG_COUNT_FDC: u32 = 0;
        unsafe {
            if LOG_COUNT_FDC < 100 {
                println!("[FDC] read_system() -> 0x{:02X} (INTRQ={} DRQ={})", 
                    result, self.intrq, self.drq);
                LOG_COUNT_FDC += 1;
            }
        }
        
        // NOTE: Do NOT clear INTRQ here! Only reading status (0x1F) clears it
        
        result
    }

    /// Write system register (port 0xFF)
    pub fn write_system(&mut self, value: u8) {
        self.system = value;
        
        // Extract drive select (bits 0-1)
        self.drive = value & 0x03;
        
        // Extract side select (bit 2)
        self.side = (value >> 2) & 0x01;
        
        // Motor control (bit 4)
        self.motor_on = (value & 0x10) != 0;
        
        // Reset (bit 3, active low)
        if (value & 0x08) == 0 {
            self.reset();
        }
    }

    /// Reset FDC
    pub fn reset(&mut self) {
        self.status = STATUS_TRACK_0;
        self.track = 0;
        self.sector = 1;
        self.data = 0;
        self.state = FdcState::Idle;
        self.head_track = 0;
        self.drq = false;
        self.intrq = false;
        self.buffer_pos = 0;
        self.sector_buffer.clear();
    }

    // === Command implementations ===

    /// CMD I: Restore (seek to track 0)
    fn cmd_restore(&mut self) {
        self.status = STATUS_BUSY;
        self.head_track = 0;
        self.track = 0;
        // Clear BUSY and set TRACK_0
        self.status &= !STATUS_BUSY;
        self.status |= STATUS_TRACK_0;
        self.intrq = true;
        self.state = FdcState::Idle;
        
        println!("[FDC] ====== RESTORE COMPLETED ====== status=0x{:02X}, INTRQ={}", self.status, self.intrq);
    }

    /// CMD I: Seek
    fn cmd_seek(&mut self) {
        self.status = STATUS_BUSY;
        self.head_track = self.track;
        // Clear BUSY and other flags
        self.status = 0;
        if self.head_track == 0 {
            self.status |= STATUS_TRACK_0;
        }
        self.intrq = true;
        self.state = FdcState::Idle;
    }

    /// CMD I: Step
    fn cmd_step(&mut self, cmd: u8) {
        self.status = STATUS_BUSY;
        
        // Determine step direction from previous operation
        // For now, just stay in place
        let update_track = (cmd & 0x10) != 0;
        
        if update_track {
            self.track = self.head_track;
        }
        
        // Clear BUSY and other flags
        self.status = 0;
        if self.head_track == 0 {
            self.status |= STATUS_TRACK_0;
        }
        self.intrq = true;
        self.state = FdcState::Idle;
    }

    /// CMD II: Read Sector
    fn cmd_read_sector(&mut self, _cmd: u8) {
        self.status = STATUS_BUSY;
        self.state = FdcState::ReadingSector;
        
        if let Some(disk) = &self.disks[self.drive as usize] {
            // Sector numbering in TR-DOS is 1-based, but we use 0-based internally
            let sector_num = if self.sector > 0 { self.sector - 1 } else { 0 };
            
            if let Some(sector_data) = disk.read_sector(self.head_track, self.side, sector_num) {
                self.sector_buffer = sector_data.to_vec();
                self.buffer_pos = 0;
                self.drq = true;
                self.status &= !STATUS_RECORD_NOT_FOUND;
            } else {
                self.status |= STATUS_RECORD_NOT_FOUND;
                self.status &= !STATUS_BUSY;
                self.state = FdcState::Idle;
                self.intrq = true;
            }
        } else {
            self.status |= STATUS_RECORD_NOT_FOUND;
            self.status &= !STATUS_BUSY;
            self.state = FdcState::Idle;
            self.intrq = true;
        }
    }

    /// CMD II: Write Sector
    fn cmd_write_sector(&mut self, _cmd: u8) {
        self.status = STATUS_BUSY;
        self.state = FdcState::WritingSector;
        
        // Prepare buffer for writing
        self.sector_buffer = vec![0; 256];
        self.buffer_pos = 0;
        self.drq = true;
    }

    /// Execute write sector (after buffer is filled)
    fn execute_write_sector(&mut self) {
        if let Some(disk) = &mut self.disks[self.drive as usize] {
            let sector_num = if self.sector > 0 { self.sector - 1 } else { 0 };
            
            if !disk.write_sector(self.head_track, self.side, sector_num, &self.sector_buffer) {
                self.status |= STATUS_RECORD_NOT_FOUND;
            }
        } else {
            self.status |= STATUS_RECORD_NOT_FOUND;
        }
    }

    /// CMD III: Read Address
    fn cmd_read_address(&mut self) {
        self.status = STATUS_BUSY;
        self.state = FdcState::ReadingAddress;
        
        // Return current address
        self.sector_buffer = vec![
            self.head_track,  // Track
            self.side,        // Side
            1,                // Sector (always 1 for simplicity)
            1,                // Sector length (256 bytes = code 1)
            0,                // CRC1
            0,                // CRC2
        ];
        self.buffer_pos = 0;
        self.drq = true;
    }

    /// CMD IV: Force Interrupt
    fn cmd_force_interrupt(&mut self) {
        self.status &= !STATUS_BUSY;
        self.state = FdcState::Idle;
        self.drq = false;
        // NOTE: FORCE_INTERRUPT (0xD0) does NOT generate INTRQ
        // INTRQ is only generated if interrupt condition bits (0-3) are set
        self.intrq = false;
    }

    /// Check if DRQ is active
    pub fn is_drq(&self) -> bool {
        self.drq
    }

    /// Check if INTRQ is active
    pub fn is_intrq(&self) -> bool {
        self.intrq
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fdc_creation() {
        let fdc = FDC::new();
        assert_eq!(fdc.track, 0);
        assert_eq!(fdc.sector, 1);
        assert_eq!(fdc.head_track, 0);
    }

    #[test]
    fn test_restore_command() {
        let mut fdc = FDC::new();
        fdc.head_track = 10;
        fdc.write_command(CMD_RESTORE);
        assert_eq!(fdc.head_track, 0);
        assert_eq!(fdc.track, 0);
    }
}
