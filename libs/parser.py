import argparse

import config


def create_parser():
    parser = argparse.ArgumentParser(
        description="An educational C=64 emulator.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-s",
        "--screen",
        action="store",
        help="Screen driver",
        default=config.SCREEN,
        choices=["raster", "virtual", "fast"],
    )
    parser.add_argument("-d", "--disk", action="store", help="Disk (t64)", type=str)
    parser.add_argument(
        "-p",
        "--program",
        action="store",
        help="(PRG) file to store on a temporary disk image. Useful with --autorun",
        type=str,
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
    parser.add_argument(
        "-ar",
        "--autorun",
        action="store_true",
        help="Autorun * from disk",
        default=False,
    )
    parser.add_argument(
        "-ad",
        "--autodir",
        action="store_true",
        help="Autodir",
    )
    parser.add_argument(
        "-at",
        "--autotype",
        action="store",
        help="Autotype command. Use | for return key",
    )
    parser.add_argument(
        "-ds",
        "--display-scale",
        type=float,
        action="store",
        default=2.0,
        help="Display scale factor",
    )
    return parser
