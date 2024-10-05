import argparse
import pathlib

import config


def create_parser():
    parser = argparse.ArgumentParser(
        description="An educational C=64 emulator.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "datafile",
        nargs="?",
        type=pathlib.Path,
        default=None,
        help="D64 image file or PRG (autodetect). Implies --autorun unless one of --autodir|--autoype|--no-autorun is set",
    )
    parser.add_argument(
        "-s",
        "--screen",
        action="store",
        help="Screen driver",
        default=config.SCREEN,
        choices=["raster", "virtual", "fast"],
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
        "-noar",
        "--no-autorun",
        action="store_true",
        default=False,
        help="Disable autorun when datafile is set",
    )

    parser.add_argument(
        "-ds",
        "--display-scale",
        type=float,
        action="store",
        default=2.0,
        help="Display scale factor",
    )
    parser.add_argument(
        "-ll",
        "--loglevel",
        type=int,
        action="store",
        default=config.LOGLEVEL,
        help="Log level ",
    )

    return parser


def is_d64_image(filepath: pathlib.Path) -> bool:
    """
    Trivial detection of D64 filetype
    """
    return filepath.stat().st_size == 174848
