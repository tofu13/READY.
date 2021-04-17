# READY.
READY. is an educational Commodore 64 emulator written in python 3.

Target is not perfect emulation, but rather learning how that computer works and rebuilding it after 35 years using technologies that are orders of magnitude more powerful.

## Credits
Inspiration:
- https://github.com/fotcorn/Python-C64-Emulator
- https://github.com/andrewsg/python-c64
- https://github.com/irmen/pyc64

Tools:
- https://github.com/meonwax/acme
- https://www.floodgap.com/retrotech/xa
- https://github.com/ctyler/6502js

Libraries:
- https://www.pygame.org

A special thanks to the numberless source of information found on the web.

## Status
Code is organized in modules corresponding to single hardware components.

- Memory (working)
- CPU (working/testing)
- Video (testing)
- ROM (working)
- Keyboard (working)
- Storage (TBD)
- Audio (TBD)


## Installation (on GNU/Linux)
Python >= 3.7 is required.

```
git clone https://github.com/tofu13/READY..git
cd READY.
```

For a standalone environment it is suggested to: 
```
virtualenv venv -p python3
. venv/bin/activate
pip install -r requirements.txt
```

Then download basic, kernal and chargen into roms/ folder.

## Usage

### Running the emulator
```python READY. [filename]```

where ```[filename]``` is a binary object ("cbm format" with address at first two bytes of binary file). It will be loaded at $0801 and run. Just omit it for a regular boot.

Complete usage:
```
usage: READY..py [-h] [-1] [-s LOAD_ADDRESS] [filename]

An educational C=64 emulator.

positional arguments:
  filename              Binary object to be run. If missing boots normally.

optional arguments:
  -h, --help            show this help message and exit
  -1, --cbm-format      First two bytes of file are little endian load address (like in LOAD"*",8,1)
  -s LOAD_ADDRESS, --load-address LOAD_ADDRESS
                        Load binary file at address (if not specified: $0801). Use (escaped)$ or 0x for hex value.
```

You can use [acme](https://github.com/meonwax/acme) or [xa](https://www.floodgap.com/retrotech/xa) to compile an assembler file, see the [programs](https://github.com/tofu13/READY./tree/master/programs) folder for some example.

### Special keys
- F11 enter monitor
- F12 reset

### Monitor
The command line monitor understands the following commands:

```
READY. monitor. Commands list:
d|disass [start] [end] -- disassemble
m|mem [start] [end] -- show memory as hex and text
i [start] [end] -- show memory as text
bk [addres] -- show breakpoints. If address specifies, set one at address 
s|setp -- execute next instruction
del [address] -- delete breakpoint at address
q|quit -- exit monitor and resume
reset -- reset machine
```
