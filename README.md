# READY.

READY. is an educational Commodore 64 emulator written in python 3.

Target is not perfect emulation or performance, but rather learning how that computer works and rebuilding it after
decades.

A special thanks to the numberless sources of information found on the web.

## Installation

Python >= 3.8 is required.
On GNU/Linux `xsel` or `xclip` packages are required in order to paste text.

```shell
git clone https://github.com/tofu13/READY..git
cd READY.
```

For a standalone environment it is suggested to:

```shell
virtualenv venv -p python3
. venv/bin/activate
pip install -r requirements.txt
```

Then download basic, kernal and chargen into roms/ folder.

## Usage

### Running the emulator

```shell
python READY..py```
```

### Options

```shell
usage: READY..py [-h] [-s {raster,simple}]
```

```
An educational C=64 emulator.

options:
  -h, --help            show this help message and exit
  -s {raster,simple}, --screen {raster,simple}
                        Screen driver
```

### Keyboard mapping

- \ : <left arrow>
- INS: £
- ESC: <RUN/STOP>
- CANC: <DEL>
- HOME: <HOME>
- PAGE_UP: <RESTORE>
- LEFT_ALT: <C=>

Numeric keypad is mapped

- F10 paste (text)
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
s|step -- execute next instruction
del [address] -- delete breakpoint at address
q|quit -- exit monitor and resume
reset -- reset machine
```
