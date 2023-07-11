from argparse import ArgumentParser

from dls_bba.cli import (
    cli_entrypoint,
    cli_multi_test,
    cli_quadcenter_plot,
    cli_show_bpm_options,
    cli_show_cell_options,
)
from dls_bba.common import ALGORITHMS
from dls_bba.gui import start_gui

from . import __version__

__all__ = ["main"]


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument("--version", "-v", action="version", version=__version__)
    parser.add_argument(
        "--algorithm",
        "-a",
        default=None,
        type=str,
        choices=ALGORITHMS.keys(),
        help="The BBA algorithm to use.",
    )
    parser.add_argument(
        "--bpm",
        "-b",
        type=str,
        help="The single BPM name that BBA should be performed on.",
    )
    parser.add_argument(
        "--save_location",
        "-s",
        type=str,
        default=None,
        help="The location to save files to.",
    )
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        type=list[str],
        help="Additional configuration filepaths.",
    )
    parser.add_argument(
        "--individual",
        "-i",
        default=None,
        type=dict,
        help="Additional individual configuration options",
    )
    parser.add_argument(
        "--quadcenter",
        "-q",
        default=None,
        type=str,
        help="The full filepath of the xxx-results.mat file to plot.",
    )
    parser.add_argument(
        "--element_names",
        "-e",
        action="store_true",
        help="Display possible BPM values.",
    )
    parser.add_argument(
        "--cell",
        "-k",
        default=None,
        type=str,
        help="Display the BPM values in the cell if given the identifier. Eg: '04'",
    )
    parser.add_argument(
        "--multi",
        "-m",
        action="store_true",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    if args.element_names:
        cli_show_bpm_options(args.config, args.individual)
    if args.cell is not None and not args.multi:
        cli_show_cell_options(args.cell, args.config, args.individual)
    if args.quadcenter is not None:
        cli_quadcenter_plot(args.quadcenter)
    if args.algorithm is not None and not args.multi:
        cli_entrypoint(
            args.algorithm, args.bpm, args.save_location, args.config, args.individual
        )
    if args.algorithm is not None and args.multi:
        cli_multi_test(
            args.algorithm, args.cell, args.save_location, args.config, args.individual
        )


def parse_gui_arguments(args=None):
    parser = ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version=__version__)
    args = parser.parse_args(args)


def gui_main():
    parse_gui_arguments()
    start_gui()


# test with: python -m dls_bba
if __name__ == "__main__":
    main()
