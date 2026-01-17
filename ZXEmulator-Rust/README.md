# ZX Spectrum Emulator (Rust)

A ZX Spectrum emulator written in Rust, ported from the Python version.

## Features

- Complete Z80 CPU emulation with all instruction sets
- 48K and 128K Spectrum models support
- Full screen rendering with pixel-perfect accuracy
- Keyboard emulation with Spectrum key matrix
- Snapshot loading (.z80, .sna formats)
- ROM loading for different Spectrum models

## Building

```bash
cargo build --release
```

## Running

```bash
# Run with a ROM file
cargo run --release -- path/to/48.rom

# Or run the built executable
./target/release/zx-emulator path/to/48.rom
```

## Controls

- **ESC** - Exit emulator
- **F2** - Reset
- Standard keyboard maps to ZX Spectrum keys

## Dependencies

- `minifb` - Cross-platform windowing and graphics
- `bitflags` - Efficient CPU flag handling
