# READY.
READY. is a Commodore 64 emulator written in python 3.

Target is not perfect emulation, but rather learning how that computer works and rebuilding it after 35 years using technologies that are orders of magnitude more powerful.

## Credits
Credits for inspiration, information and tools go to:
- https://github.com/fotcorn/Python-C64-Emulator
- https://github.com/andrewsg/python-c64
- https://github.com/meonwax/acme
- https://www.floodgap.com/retrotech/xa

- http://6502.cdot.systems (https://github.com/ctyler/6502js)
- https://www.masswerk.at/6502/
- https://everything2.com/title/Commodore+64
- https://www.c64-wiki.com

## Status
Code is organized in modules corresponding to single hardware components.

- Memory (working)
- CPU (working/testing)
- Video (TBD)
- ROM (TDB)
- Keyboard (TBD)
- Storage (TBD)
- Audio (TDB)

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

## Usage
```python READY. [filename]```

where ```[filename]``` is a binary object. It will be loaded at $0801 and run (no "cbm format" with address at first two bytes of binary file).

You can use [acme](https://github.com/meonwax/acme) or [xa](https://www.floodgap.com/retrotech/xa) to compile an assembler file, see the [programs](https://github.com/tofu13/READY./tree/master/programs) folder for some example.
