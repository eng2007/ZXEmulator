use std::fs::File;
use std::io::{BufRead, BufReader, Write};
use std::path::Path;

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum PortDecoding {
    Full,    // Strict decoding: port == 0x7FFD
    Partial, // Pentagon decoding: (port & 0x8002) == 0 imply bits A1 and A15 are 0
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum MemorySize {
    K128,
    K512,
}

#[derive(Debug, Clone)]
pub struct Config {
    pub port_decoding: PortDecoding,
    pub memory_size: MemorySize,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            port_decoding: PortDecoding::Partial, // Default to Pentagon behavior
            memory_size: MemorySize::K128,        // Default to standard 128K
        }
    }
}

pub fn load_config(path: &str) -> Config {
    let mut config = Config::default();

    if !Path::new(path).exists() {
        println!("Config file not found, creating default: {}", path);
        if let Ok(mut file) = File::create(path) {
            writeln!(file, "[Settings]").unwrap();
            writeln!(file, "PortDecoding=Partial ; Full or Partial").unwrap();
            writeln!(file, "MemorySize=128      ; 128 or 512").unwrap();
        }
        return config;
    }

    if let Ok(file) = File::open(path) {
        let reader = BufReader::new(file);
        for line in reader.lines() {
            if let Ok(line) = line {
                let line = line.trim();
                if line.starts_with(';') || line.starts_with('[') || line.is_empty() {
                    continue;
                }

                if let Some((key, value)) = line.split_once('=') {
                    let key = key.trim();
                    let value = value.split(';').next().unwrap_or("").trim(); // Remove comments

                    match key {
                        "PortDecoding" => {
                            if value.eq_ignore_ascii_case("Full") {
                                config.port_decoding = PortDecoding::Full;
                            } else if value.eq_ignore_ascii_case("Partial") {
                                config.port_decoding = PortDecoding::Partial;
                            }
                        }
                        "MemorySize" => {
                            if value == "512" {
                                config.memory_size = MemorySize::K512;
                            } else {
                                config.memory_size = MemorySize::K128;
                            }
                        }
                        _ => {}
                    }
                }
            }
        }
    }

    config
}
