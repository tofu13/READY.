import argparse
import logging
import pathlib

import d64

import config
from libs import hardware
from libs.parser import create_parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    logging.basicConfig(
        filename=config.LOGFILE, filemode="w", format="%(message)s", level=args.loglevel
    )

    autotype = (
        'load "*",8,1|run:|'
        if args.autorun
        else 'load "$",8|list:|'
        if args.autodir
        else args.autotype or ""
    )
    autotype = autotype.replace("|", "\n")

    if args.loadstate:
        c64 = hardware.machine.Machine.from_file(args.loadstate)
        c64.run()
    else:
        roms = hardware.roms.ROMS(config.ROMS_FOLDER)
        memory = hardware.memory.Memory(roms=roms)
        bus = hardware.bus.Bus()
        cpu = hardware.cpu.CPU(memory, bus)
        if args.screen == "raster":
            screen = hardware.screen.RasterScreen(memory, bus)
        elif args.screen == "virtual":
            screen = hardware.screen.VirtualScreen(memory, bus)
        elif args.screen == "fast":
            screen = hardware.screen.FastScreen(memory, bus)
        else:
            raise argparse.ArgumentError(None, f"Invalid screen driver {args.screen}")

        cia_a = hardware.cia.CIA_A(memory, bus)
        cia_b = hardware.cia.CIA_B(memory, bus)

        diskdrive = hardware.disk_drive.Drive()
        if program := args.program:
            d64.DiskImage.create("d64", pathlib.Path("tempdisk.d64"), b"TEMP", b"00")
            with (
                d64.DiskImage("tempdisk.d64", "w") as image,
                image.path(b"RUNME.PRG").open("w", "PRG") as f_out,
                open(program, "rb") as f_in,
            ):
                f_out.write(f_in.read())
            diskdrive.set_imagefile("tempdisk.d64")

        elif disk := args.disk:
            diskdrive.set_imagefile(disk)

        c64 = hardware.machine.Machine(
            memory=memory,
            bus=bus,
            cpu=cpu,
            screen=screen,
            ciaA=cia_a,
            ciaB=cia_b,
            diskdrive=diskdrive,
            console=args.console,
            autotype=autotype,
            display_scale=args.display_scale,
        )

        if args.console:
            # Pre-clear screen for quicker runtime updates
            print("\033[H\033[2J", end="")

        if config.QUICK_BOOT:
            # Skip most lookup for ram start -> fast cold start
            c64.memory.rom_kernal[0x1D69] = 159
        c64.run(0xFCE2)


if __name__ == "__main__":
    main()
