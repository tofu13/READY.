import argparse

import config
import hardware


def main():
    parser = argparse.ArgumentParser(
        description="An educational C=64 emulator."
    )
    parser.add_argument("-s", "--screen", action='store',
                        help="Screen driver", default=config.SCREEN, choices=["raster", "simple"])
    args = parser.parse_args()

    roms = hardware.roms.ROMS(config.ROMS_FOLDER)
    memory = hardware.memory.BytearrayMemory(65536, roms)
    cpu = hardware.cpu.CPU(memory)
    if args.screen == "raster":
        screen = hardware.screen.RasterScreen(memory)
    elif args.screen == "simple":
        screen = hardware.screen.LazyScreen(memory)
    else:
        raise argparse.ArgumentError(f"Invalid screen driver {args.screen}")
    cia_a = hardware.cia.CIA_A(memory)

    c64 = hardware.machine.Machine(
        memory=memory,
        cpu=cpu,
        screen=screen,
        ciaA=cia_a,
    )

    # Entry point
    c64.run(0xFCE2)


if __name__ == '__main__':
    main()
