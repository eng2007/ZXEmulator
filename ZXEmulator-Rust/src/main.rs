//! ZX Spectrum Emulator - Main entry point

use minifb::{Key, Window, WindowOptions, Scale};
use rfd::FileDialog;
use std::env;
use std::time::Duration;

mod cpu;
mod memory;
mod graphics;
mod keyboard;
mod keyboard_display;
mod io;
mod snapshot;
mod debug_display;
mod config;

use cpu::Z80;
use memory::Memory;
use graphics::{Graphics, WINDOW_WIDTH, WINDOW_HEIGHT};
use keyboard::Keyboard;
use keyboard_display::{KeyboardDisplay, KB_WIDTH, KB_HEIGHT};
use debug_display::{DebugDisplay, DBG_WIDTH, DBG_HEIGHT};
use io::IoController;

/// Cycles per frame (3.5MHz / 50Hz)
const CYCLES_PER_FRAME: u64 = 69888;

/// Maximum instructions per frame (safety limit)
const MAX_INSTRUCTIONS_PER_FRAME: u32 = 100000;

/// Frame duration for 50Hz
const FRAME_DURATION: Duration = Duration::from_millis(20);

fn main() {
    let args: Vec<String> = env::args().collect();

    // Create emulator components
    // Load configuration
    let config = config::load_config("zx_emu.ini");
    println!("Configuration loaded: {:?}", config);

    // Create emulator components
    let mut memory = Memory::new(config.clone());
    let mut keyboard = Keyboard::new();
    let mut io = IoController::new(&mut keyboard, &mut memory, config.clone());
    let mut cpu = Z80::new(&mut memory, &mut io);
    let mut graphics = Graphics::new();
    let mut kb_display = KeyboardDisplay::new();
    let mut debug_display = DebugDisplay::new();

    let mut current_filename = String::from("None");

    // Load ROM if provided
    if args.len() > 1 {
        let rom_path = &args[1];
        match snapshot::load_rom(rom_path, &mut memory) {
            Ok(_) => {
                println!("Loaded ROM: {}", rom_path);
                current_filename = std::path::Path::new(rom_path)
                    .file_name()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .to_string();
            }
            Err(e) => {
                eprintln!("Failed to load ROM: {}", e);
                println!("Continuing with empty memory...");
            }
        }
    } else {
        println!("Usage: {} <rom_file> [snapshot_file]", args[0]);
        println!("No ROM file specified, starting with empty memory (test mode)");
    }

    // Load snapshot if provided
    if args.len() > 2 {
        let snapshot_path = &args[2];
        match snapshot::load_snapshot(snapshot_path, &mut cpu, &mut memory) {
            Ok(_) => {
                println!("Loaded snapshot: {}", snapshot_path);
                current_filename = std::path::Path::new(snapshot_path)
                    .file_name()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .to_string();
            }
            Err(e) => eprintln!("Failed to load snapshot: {}", e),
        }
    }

    // Create main emulator window
    let mut window = Window::new(
        "ZX Spectrum Emulator (Rust)",
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        WindowOptions {
            scale: Scale::X2,
            resize: true,
            ..WindowOptions::default()
        },
    )
    .expect("Failed to create window");

    // Create keyboard display window
    let mut kb_window = Window::new(
        "ZX Spectrum Keyboard",
        KB_WIDTH,
        KB_HEIGHT,
        WindowOptions {
            scale: Scale::X1,
            resize: false,
            ..WindowOptions::default()
        },
    )
    .expect("Failed to create keyboard window");

    // Create debug window
    let mut dbg_window = Window::new(
        "ZX Debugger",
        DBG_WIDTH,
        DBG_HEIGHT,
        WindowOptions {
            scale: Scale::X1,
            resize: false,
            ..WindowOptions::default()
        },
    )
    .expect("Failed to create debug window");

    // Limit update rate to ~50 FPS
    window.limit_update_rate(Some(FRAME_DURATION));
    kb_window.limit_update_rate(Some(FRAME_DURATION));
    dbg_window.limit_update_rate(Some(FRAME_DURATION));

    println!("ZX Spectrum Emulator started");
    println!("Controls: ESC = Exit, F2 = Reset, F3 = Load Snapshot");

    // Main loop - continue while main window is open
    while window.is_open() && !window.is_key_down(Key::Escape) {
        // Handle special keys
        if window.is_key_pressed(Key::F2, minifb::KeyRepeat::No) {
            cpu.reset();
            memory.reset();
            io.reset();
            println!("Emulator reset");
        }

        if window.is_key_pressed(Key::F3, minifb::KeyRepeat::No) {
            if let Some(path) = FileDialog::new()
                .add_filter("Snapshots", &["z80", "sna", "zip"])
                .add_filter("All Files", &["*"])
                .pick_file() 
            {
                if let Some(path_str) = path.to_str() {
                     match snapshot::load_snapshot(path_str, &mut cpu, &mut memory) {
                        Ok(_) => {
                            println!("Loaded snapshot: {}", path_str);
                            current_filename = path.file_name()
                                .unwrap_or_default()
                                .to_string_lossy()
                                .to_string();
                        }
                        Err(e) => eprintln!("Failed to load snapshot: {}", e),
                    }
                }
            }
        }

        // F4: Load ROM
        if window.is_key_pressed(Key::F4, minifb::KeyRepeat::No) {
             if let Some(path) = FileDialog::new()
                .add_filter("ROMs", &["rom", "bin"])
                .add_filter("All Files", &["*"])
                .pick_file() 
            {
                if let Some(path_str) = path.to_str() {
                    match snapshot::load_rom(path_str, &mut memory) {
                        Ok(_) => {
                            println!("Loaded ROM: {}", path_str);
                            current_filename = path.file_name()
                                .unwrap_or_default()
                                .to_string_lossy()
                                .to_string();
                            
                            // Reset emulator after loading new ROM
                            cpu.reset();
                            memory.reset();
                            io.reset();
                            println!("Emulator reset with new ROM");
                        }
                        Err(e) => eprintln!("Failed to load ROM: {}", e),
                    }
                }
            }
        }

        // Update keyboard state from main window
        let keys: Vec<Key> = window.get_keys();
        keyboard.update(&keys);

        // Run CPU for one frame with safety limit
        let start_cycles = cpu.cycles;
        let mut instruction_count = 0u32;
        
        while cpu.cycles - start_cycles < CYCLES_PER_FRAME 
              && instruction_count < MAX_INSTRUCTIONS_PER_FRAME 
        {
            let cycles_before = cpu.cycles;
            cpu.execute();
            instruction_count += 1;
            
            // If CPU is halted, just add remaining cycles and break
            if cpu.halted {
                let remaining = CYCLES_PER_FRAME - (cpu.cycles - start_cycles);
                cpu.cycles += remaining;
                break;
            }
            
            // Safety: if execute() didn't advance cycles, force advancement
            if cpu.cycles == cycles_before {
                cpu.cycles += 4;
            }
        }

        // Trigger frame interrupt
        cpu.handle_interrupt();

        // Update border color from I/O
        graphics.set_border(io.get_border_color());

        // Render main screen
        graphics.render(&memory);

        // Render keyboard display
        kb_display.render(&keyboard);

        // Render debug display
        debug_display.render(&cpu, &memory, &current_filename);

        // Update main window
        window
            .update_with_buffer(graphics.get_buffer(), WINDOW_WIDTH, WINDOW_HEIGHT)
            .expect("Failed to update window");

        // Update keyboard window (if still open)
        if kb_window.is_open() {
            kb_window
                .update_with_buffer(kb_display.get_buffer(), KB_WIDTH, KB_HEIGHT)
                .expect("Failed to update keyboard window");
        }

        // Update debug window (if still open)
        if dbg_window.is_open() {
            dbg_window
                .update_with_buffer(debug_display.get_buffer(), DBG_WIDTH, DBG_HEIGHT)
                .expect("Failed to update debug window");
        }
    }

    println!("Emulator stopped");
}
