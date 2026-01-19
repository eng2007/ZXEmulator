//! TRD disk image format support for TR-DOS
//!
//! TRD files are disk images for TR-DOS (Disk Operating System)
//! Standard format: 80 tracks × 2 sides × 16 sectors × 256 bytes = 655,360 bytes

use std::fs::File;
use std::io::{self, Read};

/// Standard TRD disk size (80 tracks, 2 sides, 16 sectors per track)
pub const TRD_SIZE: usize = 655_360;

/// Tracks per disk
pub const TRACKS: u8 = 80;

/// Sides per disk
pub const SIDES: u8 = 2;

/// Sectors per track
pub const SECTORS_PER_TRACK: u8 = 16;

/// Bytes per sector
pub const SECTOR_SIZE: usize = 256;

/// Catalog sector location (track 0, sector 8)
const CATALOG_TRACK: u8 = 0;
const CATALOG_SECTOR: u8 = 8;

/// Disk info sector location (track 0, sector 9)
const INFO_TRACK: u8 = 0;
const INFO_SECTOR: u8 = 9;

/// TRD disk image
#[derive(Clone)]
pub struct TrdDisk {
    /// Raw disk data
    data: Vec<u8>,
    
    /// Number of tracks (usually 80)
    tracks: u8,
    
    /// Number of sides (usually 2)
    sides: u8,
    
    /// Sectors per track (usually 16)
    sectors_per_track: u8,
}

impl TrdDisk {
    /// Create a new empty TRD disk
    pub fn new() -> Self {
        Self {
            data: vec![0; TRD_SIZE],
            tracks: TRACKS,
            sides: SIDES,
            sectors_per_track: SECTORS_PER_TRACK,
        }
    }

    /// Create TRD disk from raw data
    pub fn from_bytes(data: Vec<u8>) -> io::Result<Self> {
        if data.len() != TRD_SIZE {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                format!("Invalid TRD size: expected {}, got {}", TRD_SIZE, data.len()),
            ));
        }

        Ok(Self {
            data,
            tracks: TRACKS,
            sides: SIDES,
            sectors_per_track: SECTORS_PER_TRACK,
        })
    }

    /// Load TRD disk from file
    pub fn load(path: &str) -> io::Result<Self> {
        let mut file = File::open(path)?;
        let mut data = Vec::new();
        file.read_to_end(&mut data)?;
        
        Self::from_bytes(data)
    }

    /// Calculate physical offset in disk image
    /// 
    /// Physical sector layout:
    /// Track 0, Side 0: sectors 0-15
    /// Track 0, Side 1: sectors 16-31
    /// Track 1, Side 0: sectors 32-47
    /// etc.
    fn calculate_offset(&self, track: u8, side: u8, sector: u8) -> Option<usize> {
        if track >= self.tracks || side >= self.sides || sector >= self.sectors_per_track {
            return None;
        }

        let sectors_per_cyl = self.sectors_per_track as usize * self.sides as usize;
        let offset = (track as usize * sectors_per_cyl + side as usize * self.sectors_per_track as usize + sector as usize) * SECTOR_SIZE;
        
        Some(offset)
    }

    /// Read a sector from the disk
    pub fn read_sector(&self, track: u8, side: u8, sector: u8) -> Option<&[u8]> {
        let offset = self.calculate_offset(track, side, sector)?;
        Some(&self.data[offset..offset + SECTOR_SIZE])
    }

    /// Write a sector to the disk
    pub fn write_sector(&mut self, track: u8, side: u8, sector: u8, data: &[u8]) -> bool {
        if data.len() != SECTOR_SIZE {
            return false;
        }

        if let Some(offset) = self.calculate_offset(track, side, sector) {
            self.data[offset..offset + SECTOR_SIZE].copy_from_slice(data);
            true
        } else {
            false
        }
    }

    /// Get disk information from sector 9 of track 0
    pub fn get_disk_info(&self) -> Option<TrdDiskInfo> {
        let info_sector = self.read_sector(INFO_TRACK, 0, INFO_SECTOR)?;
        
        Some(TrdDiskInfo {
            first_free_sector: info_sector[0xe1],
            first_free_track: info_sector[0xe2],
            disk_type: info_sector[0xe3],
            num_files: info_sector[0xe4],
            free_sectors: u16::from_le_bytes([info_sector[0xe5], info_sector[0xe6]]),
            disk_id: info_sector[0xe7],
            // Disk password at 0xE9-0xF1
            // Deleted files at 0xF4
            disk_name: String::from_utf8_lossy(&info_sector[0xf5..=0xfc]).trim().to_string(),
        })
    }

    /// Get catalog entries (files on disk)
    pub fn get_catalog(&self) -> Vec<TrdCatalogEntry> {
        let mut entries = Vec::new();
        
        // Catalog occupies sectors 0-7 of track 0
        for sector in 0..8 {
            if let Some(catalog_data) = self.read_sector(CATALOG_TRACK, 0, sector) {
                // Each sector contains 16 file entries (16 bytes each)
                for i in 0..16 {
                    let offset = i * 16;
                    let entry_data = &catalog_data[offset..offset + 16];
                    
                    // Check if entry is valid (filename not empty)
                    if entry_data[0] != 0 {
                        let filename = String::from_utf8_lossy(&entry_data[0..8]).trim().to_string();
                        let extension = entry_data[8] as char;
                        
                        entries.push(TrdCatalogEntry {
                            filename,
                            extension,
                            start_sector: entry_data[0x0e],
                            start_track: entry_data[0x0f],
                            length_sectors: entry_data[0x0d],
                        });
                    }
                }
            }
        }
        
        entries
    }

    /// Get raw data (for debugging)
    pub fn get_data(&self) -> &[u8] {
        &self.data
    }
}

/// TR-DOS disk information (from sector 9)
#[derive(Debug, Clone)]
pub struct TrdDiskInfo {
    pub first_free_sector: u8,
    pub first_free_track: u8,
    pub disk_type: u8,
    pub num_files: u8,
    pub free_sectors: u16,
    pub disk_id: u8,
    pub disk_name: String,
}

/// TR-DOS catalog entry (file on disk)
#[derive(Debug, Clone)]
pub struct TrdCatalogEntry {
    pub filename: String,
    pub extension: char,  // 'B' = Basic, 'C' = Code, '#' = Array, 'D' = Data
    pub start_track: u8,
    pub start_sector: u8,
    pub length_sectors: u8,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_offset_calculation() {
        let disk = TrdDisk::new();
        
        // Track 0, Side 0, Sector 0 should be at offset 0
        assert_eq!(disk.calculate_offset(0, 0, 0), Some(0));
        
        // Track 0, Side 0, Sector 1 should be at offset 256
        assert_eq!(disk.calculate_offset(0, 0, 1), Some(256));
        
        // Track 0, Side 1, Sector 0 should be at offset 16*256 = 4096
        assert_eq!(disk.calculate_offset(0, 1, 0), Some(4096));
        
        // Track 1, Side 0, Sector 0 should be at offset 32*256 = 8192
        assert_eq!(disk.calculate_offset(1, 0, 0), Some(8192));
    }

    #[test]
    fn test_sector_read_write() {
        let mut disk = TrdDisk::new();
        let test_data = [0xAA; SECTOR_SIZE];
        
        // Write and read back
        assert!(disk.write_sector(0, 0, 0, &test_data));
        let read_data = disk.read_sector(0, 0, 0).unwrap();
        assert_eq!(read_data, &test_data);
    }
}
