# READY.

READY. is an educational & fun Commodore 64 emulator, written for learning and rebuilding after
decades.

A special thank to the numberless sources of information found on the web.

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

Then download basic, kernal and chargen into `roms/` folder.

## Usage

### Running the emulator

```shell
python READY..py```
```

### Options

```shell
> python READY..py --help
```
```
usage: READY..py [-h] [-s {raster,simple,text,virtual,numpy}] [-d DISK] [-c]

An educational C=64 emulator.

options:
  -h, --help            show this help message and exit
  -s {raster,simple,text,virtual,numpy}, --screen {raster,simple,text,virtual,numpy}
                        Screen driver
  -d DISK, --disk DISK  Disk (t64)
  -c, --console         Show screen in console (chars only)
```

### Keyboard mapping

```
- \ : <LEFT ARROW>
- ESC: <RUN/STOP>
- BACKSPACE: <DEL>
- INS: <INS> (<SHIFT+DEL>)
- HOME: <HOME>
- PAGE_UP: <RESTORE>
- LEFT_ALT: <C=>
```

Special keys

```
- F10 paste (text)
- F11 enter monitor
- F12 reset
- RIGHT_ALT + P: PLAY on datassette
- RIGHT_ALT + S: STOP on datassette
```

### Monitor

Enter monitor pressing F11
```
$e5f5> help
Documented commands (type help <topic>):
========================================
convert  disass  go  help  i  mem  next  reset  step  trace  x
```
