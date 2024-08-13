import argparse

import config
import hardware


def create_parser():
    parser = argparse.ArgumentParser(description="An educational C=64 emulator.")
    parser.add_argument(
        "-s",
        "--screen",
        action="store",
        help=f"Screen driver (default: {config.SCREEN})",
        default=config.SCREEN,
        choices=["raster", "virtual", "fast"],
    )
    parser.add_argument(
        "-d", "--disk", action="store", help="Disk (t64)", default="", type=str
    )
    parser.add_argument(
        "-c",
        "--console",
        action="store_true",
        help="Show screen in console (chars only)",
        default=False,
    )
    parser.add_argument(
        "-t", "--loadstate", action="store", help="Load state from file", default=False
    )
    parser.add_argument("-ar", "--autorun", action="store_true", help="Autorun * from disk", default=False)
    parser.add_argument("-at", "--autotype", action="store", help="Autotype command. Use | for return key")
    return parser


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
