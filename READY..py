import argparse

import hardware
from hardware.constants import *

from config import *


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("-1", "--cbm-format", action='store_true',
                        help="First two bytes of file are little endian load address (like in LOAD\"*\",8,1)")
    #parser.add_argument("-a", "--assembly", action='store_true',
    #                    help=f"Compile and run an assembler file using compiler specified with"
    #                         f" -c (default: {DEFAULT_COMPILER}). See config.")
    parser.add_argument("-c", "--compiler", action='store', default=f"{DEFAULT_COMPILER}",
                        help=f"Use this compiler. Available: {', '.join(COMPILERS.keys()) or 'none :( '}. See config.")
    parser.add_argument("-s", "--load-address", action='store',
                        help=f"Load binary file at address (if not specified: ${DEFAULT_LOAD_ADDRESS:04X}). "
                             f"Use (escaped)$ or 0x for hex value.")
    parser.add_argument("-n","--no-roms", action='store_true', default=False,
                        help="Do not load roms")
    args = parser.parse_args()

    print(args)
    if args.cbm_format and args.load_address:
        raise parser.error("-1/--cbmformat and -s/--load-addres conflicts. Choose one.")

    if args.load_address:
        try:
            if args.load_address.startswith("0x"):
                base = int(args.load_address[2:], 16)
            elif args.load_address.startswith("$"):
                base = int(args.load_address[1:], 16)
            else:
                base = int(args.load_address)
        except ValueError as err:
            raise parser.error(f"Invalid load address {args.load_address}")
        if not 0 <= base <= 0xFFFF:
            raise parser.error(f"Invalid load address {args.load_address}")

    base = None
    roms = None if args.no_roms else hardware.roms.ROMS(ROMS_FOLDER)

    c64 = hardware.machine.Machine(
        hardware.memory.BytearrayMemory(65536),
        hardware.cpu.CPU(),
        hardware.screen.Screen(),
        roms,
    )

    if True:
        base = c64.load(args.filename, base or DEFAULT_LOAD_ADDRESS, args.cbm_format)
        c64.cpu.run(base)

        pass