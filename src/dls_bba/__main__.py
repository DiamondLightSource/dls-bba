from argparse import ArgumentParser
from typing import List

from dls_bba.cli import cli_entrypoint
from dls_bba.common import ALGORITHMS
from dls_bba.gui import start_gui
from dls_bba.machine import Machine
from dls_bba.plotting import bba_offsets_folder, bowtie_plot

from . import __version__

__all__ = ["main"]


def parse_arguments():
    parent_parser = ArgumentParser(description="The parent parser")
    subparsers = parent_parser.add_subparsers(title="actions")

    parent_parser.add_argument("--version", "-v", action="version", version=__version__)
    parent_parser.add_argument(
        "--config",
        "-c",
        default=None,
        type=str,
        help="Additional configuration filepaths.",
    )
    parent_parser.add_argument(
        "--individual",
        "-i",
        default=None,
        type=dict,
        help="Additional individual configuration options",
    )

    parser_info = subparsers.add_parser(
        "info", parents=[parent_parser], add_help=False, description="Get information"
    )
    parser_info.set_defaults(which="info")

    parser_run = subparsers.add_parser(
        "run", parents=[parent_parser], add_help=False, description="Run BBA"
    )
    parser_run.set_defaults(which="run")
    parser_run.add_argument(
        "--method",
        "-m",
        default=None,
        type=str,
        choices=ALGORITHMS.keys(),
        help="The algorithm to use.",
    )

    parser_plot = subparsers.add_parser(
        "plot", parents=[parent_parser], add_help=False, description="Plot results"
    )
    parser_plot.set_defaults(which="plot")
    group = parser_plot.add_mutually_exclusive_group(required=True)
    group.add_argument("--quadcenter", "-Q", action="store_true", help="")
    group.add_argument("--difference", "-d", action="store_true", help="")

    for subparser in [parser_info, parser_run]:
        group = subparser.add_mutually_exclusive_group(required=True)
        group.add_argument("--wholemachine", "-w", action="store_true", help="")
        group.add_argument("--psps", "-p", action="store_true", help="")
        group.add_argument("--cell", "-k", type=str, default=None, help="")
        group.add_argument("--bpm", "-b", type=int, default=None, help="")
        group.add_argument("--quad", "-q", type=int, default=None, help="")

    for subparser in [parser_run, parser_plot]:
        subparser.add_argument(
            "--save_location",
            "-s",
            type=str,
            default=None,
            help="The location to save files to.",
        )

    return parent_parser.parse_args()


def sort_elements(args) -> List[str]:
    machine = Machine(args.config, args.individual)
    elements = []

    if args.wholemachine:
        elements = machine.bpms_names
    if args.psps:
        elements = machine.psps
    if args.cell is not None:
        if args.cell not in machine.cell_dictionary.keys():
            print("Invalid cell selected. Try cells '00' to '24'")
        else:
            elements = machine.cell_dictionary[args.cell]
    if args.bpm is not None:
        if (args.bpm > len(machine.bpms_names)) and (args.bpm >= 1):
            print(f"Invalid BPM selected. Try:  1 <= BPMs <= {len(machine.bpms_names)}")
        else:
            elements = [machine.bpms_names[args.bpm - 1]]
    if args.quad is not None:
        if args.quad > len(machine.quads_names) and (args.quad >= 1):
            print(
                f"Invalid Quad selected. Try:  1 <= Quads <= {len(machine.quads_names)}"
            )
        else:
            elements = [machine.quads_names[args.quad - 1]]
    return elements


def main():
    args = parse_arguments()
    if args.which == "info":
        elements = sort_elements(args)
        print(elements)

    elif args.which == "run":
        elements = sort_elements(args)
        cli_entrypoint(
            args.method, elements, args.save_location, args.config, args.individual
        )

    elif args.which == "plot":
        if args.quadcenter:
            machine = Machine(args.config, args.individual)
            bowtie_plot(args.save_location, machine.config["SAVE_PLOTS"])
        if args.difference:
            machine = Machine(args.config, args.individual)
            bba_offsets_folder(machine, args.difference, machine.config["SAVE_PLOTS"])


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
