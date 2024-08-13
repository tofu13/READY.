import argparse

import config
from libs import hardware
from libs.parser import create_parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    autotype = 'load "*",8,1|run:|' if args.autorun else args.autotype or ""
    autotype = autotype.replace("|", "\n")

    if args.loadstate:
        c64 = hardware.machine.Machine.from_file(args.loadstate)
        c64.run()
    else:
        roms = hardware.roms.ROMS(config.ROMS_FOLDER)
        memory = hardware.memory.Memory(roms=roms)
        cpu = hardware.cpu.CPU(memory)
        if args.screen == "raster":
            screen = hardware.screen.RasterScreen(memory)
        elif args.screen == "virtual":
            screen = hardware.screen.VirtualScreen(memory)
        elif args.screen == "fast":
            screen = hardware.screen.FastScreen(memory)
        else:
            raise argparse.ArgumentError(None, f"Invalid screen driver {args.screen}")

        cia_a = hardware.cia.CIA_A(memory)

        diskdrive = hardware.disk_drive.Drive()
        if disk := args.disk:
            diskdrive.set_imagefile(disk)

        c64 = hardware.machine.Machine(
            memory=memory,
            cpu=cpu,
            screen=screen,
            ciaA=cia_a,
            diskdrive=diskdrive,
            console=args.console,
            autorun=autotype,
        )

        if args.console:
            # Pre-clear screen for quicker runtime updates
            print("\033[H\033[2J", end="")

        if config.QUICK_BOOT:
            # Skip most lookup for ram start -> fast cold start
            c64.memory.roms["kernal"][0x1D69] = 159
        c64.run(0xFCE2)


if __name__ == "__main__":
    main()
