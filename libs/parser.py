import argparse

import config


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
    parser.add_argument(
        "-ar",
        "--autorun",
        action="store_true",
        help="Autorun * from disk",
        default=False,
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
        help="Display scale factor, default 2.0",
    )
    return parser
