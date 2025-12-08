# ZXEmulator

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A full-featured ZX Spectrum emulator written in Python, featuring complete Z80 CPU emulation, graphics, sound, and I/O subsystems.

![ZX Spectrum Emulator](https://via.placeholder.com/800x400/000000/FFFFFF?text=ZX+Emulator+Screenshot)

## Features

### 🎮 Core Emulation
- **Complete Z80 CPU emulation** with all instruction sets (base, extended, IX/IY registers)
- **48K and 128K Spectrum models** support
- **Accurate timing** and interrupt handling
- **Memory banking** for 128K models

### 🎨 Graphics & Display
- **Full screen rendering** with pixel-perfect accuracy
- **Color palette emulation** (15 colors + bright variants)
- **Border effects** and screen attributes
- **SCR file loading** for screen snapshots
- **Real-time screen updates**

### ⌨️ Input/Output
- **Full keyboard emulation** with Spectrum key matrix
- **I/O port handling** for peripherals
- **Snapshot loading** (.z80, .sna formats)
- **ROM loading** for different Spectrum models

### 🛠️ Development Tools
- **Built-in debugger** with register and memory inspection
- **Test suite** with Z80 instruction verification
- **Multiple CPU implementations** for comparison and optimization
- **Logging and tracing** capabilities

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Setup
```bash
# Clone the repository
git clone https://github.com/eng2007/ZXEmulator.git
cd ZXEmulator

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
# Run the emulator
python emulator.py
```

### Available Scripts
- `start_emul.bat` - Launch the main emulator
- `start_draw_keyboard.bat` - Keyboard visualization demo
- `start_screen.bat` - Screen loading demo
- `start_test.bat` - Run test suite

### ROM Files
Place your ZX Spectrum ROM files in the `roms/` directory:
- `48.rom` - 48K Spectrum ROM
- `128k.rom` - 128K Spectrum ROM

### Supported File Formats
- **ROM files**: `.rom`, `.bin`
- **Snapshots**: `.z80`, `.sna`
- **Screen files**: `.scr`
- **Archives**: `.zip` (automatically extracted)

## Controls

### Emulator Controls
- **F1** - Open ROM selection menu
- **F2** - Reset emulator
- **ESC** - Exit emulator

### ZX Spectrum Keyboard
The emulator maps PC keyboard to ZX Spectrum keys:
- Standard QWERTY layout maps to Spectrum keyboard matrix
- Special keys (Symbol Shift, Caps Shift) are mapped appropriately

## Project Structure

```
ZXEmulator/
├── emulator.py          # Main emulator class and GUI
├── new_cpu.py           # Z80 CPU implementation (main)
├── cpu.py               # Alternative Z80 CPU implementation
├── base_cpu.py          # Base CPU functionality
├── ext_cpu.py           # Extended CPU instructions
├── memory.py            # Memory management and banking
├── graphics.py          # Screen rendering and graphics
├── keyboard.py          # Keyboard input handling
├── io_controller.py     # I/O port management
├── interrupt_controller.py # Interrupt handling
├── const.py             # Constants and definitions
├── tests.py             # Test suite
├── tests_new.py         # Additional tests
├── requirements.txt     # Python dependencies
├── roms/                # ZX Spectrum ROM files
├── demos/               # Demo programs and games
├── snapshots/           # Game snapshots (.z80, .sna)
├── screens/             # Screen captures (.scr)
└── z80-master/          # Z80 reference implementation
```

## Technical Details

### Z80 CPU Emulation
- **Complete instruction set** including undocumented opcodes
- **Accurate flag handling** and register operations
- **Interrupt modes** (IM 0, IM 1, IM 2)
- **Multiple CPU cores** for testing and compatibility

### Memory System
- **64KB base memory** for 48K model
- **128KB extended memory** with proper banking
- **ROM/RAM switching** and memory paging
- **Snapshot loading** with memory state restoration

### Graphics System
- **256x192 pixel resolution** with color attributes
- **8x8 character cells** with ink/paper colors
- **Border rendering** with 8 possible colors
- **Real-time screen updates** at 50Hz

## Testing

Run the test suite to verify Z80 instruction accuracy:
```bash
python tests_new.py
```

The emulator includes comprehensive tests against known Z80 test suites and maintains compatibility with existing ZX Spectrum software.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Compatibility

- **Python 3.7+** required
- **Windows, Linux, macOS** supported
- **Pygame 2.0+** for graphics and input
- **NumPy** for performance optimizations

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Based on the original ZX Spectrum architecture
- Z80 CPU emulation inspired by various open-source projects
- Special thanks to the ZX Spectrum preservation community

## Screenshots

![Emulator Interface](https://via.placeholder.com/400x300/000000/FFFFFF?text=Emulator+Interface)
![Game Loading](https://via.placeholder.com/400x300/000000/FFFFFF?text=Game+Loading)

---

*ZX Spectrum is a trademark of Sinclair Research Ltd.*
