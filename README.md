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

ROMS are not included here: download basic, kernal and chargen into `roms/` folder.

## Usage

### Running the emulator

```shell
python READY..py
```

### Options

```shell
python READY..py --help
```
```
usage: READY..py [-h] [-s {raster,virtual,fast}] [-d DISK] [-c] [-t LOADSTATE]

An educational C=64 emulator.

options:
  -h, --help            show this help message and exit
  -s {raster,virtual,fast}, --screen {raster,virtual,fast}
                        Screen driver
  -d DISK, --disk DISK  Disk (t64)
  -c, --console         Show screen in console (chars only)
  -t LOADSTATE, --loadstate LOADSTATE
                        Load state from file
```

### Configuration

See [config.py](config.py) for available parameters:

### Keyboard mapping

#### Default keys
```
- PAGE_DOWN: <RESTORE>
- PAGE_UP: <UP_ARROW>
- ESC: <RUN/STOP>
- BACKSPACE, CANC: <INS/DEL>
- HOME: <HOME>
- LEFT_ALT: <C=>
- LEFT_CTRL: <CTRL>
```

#### Bonus keys

```
- LEFT: <SHIFT+CRSR_LR>
- UP: <SHIFT+CRSR_UD>
- INS: <INS> (<SHIFT+INS/DEL>)
```

#### Special keys

```
- F10 paste
- F11 enter monitor
- F12 reset
- RIGHT_ALT + P: PLAY on datassette
- RIGHT_ALT + S: STOP on datassette
```

#### Keymaps

Available keymaps: it, en.

(Definitions in `constants.py`, contributions welcome)

### Monitor

Enter monitor pressing F11
```
$e5f5> help
Documented commands (type help <topic>):
========================================
convert  disass  go  help  i  mem  next  reset  step  trace  x
```
