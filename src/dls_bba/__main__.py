from argparse import ArgumentParser
from typing import List

from dls_bba.cli import (
    cli_entrypoint,
    cli_quadcenter_plot,
    cli_show_bpm_options,
    cli_show_cell_options,
)
from dls_bba.common import ALGORITHMS
from dls_bba.machine import Machine
from dls_bba.gui import start_gui

from . import __version__

__all__ = ["main"]


def parse_arguments():
    parent_parser = ArgumentParser(description="The parent parser")
    subparsers = parent_parser.add_subparsers(title="actions")

    parent_parser.add_argument("--version", "-v", action="version", version=__version__)

    parser_info = subparsers.add_parser("info", parents=[parent_parser], add_help=False, description="Get information")
    parser_info.set_defaults(which="info")

    parser_run = subparsers.add_parser("run", parents=[parent_parser], add_help=False, description="Run BBA")
    parser_run.set_defaults(which="run")
    parser_run.add_argument("--method", "-m", default=None, type=str, choices=ALGORITHMS.keys(), help="The algorithm to use.")

    parser_plot = subparsers.add_parser("plot", parents=[parent_parser], add_help=False, description="Plot results")
    parser_plot.set_defaults(which="plot")
    group = parser_plot.add_mutually_exclusive_group(required=True)
    group.add_argument("--quadcenter", "-Q", action='store_true', help="")
    group.add_argument("--difference", "-d", action='store_true', help="")

    for subparser in [parser_info, parser_run]:
        subparser.add_argument("--config", "-c", default=None, type=str, help="Additional configuration filepaths.")
        subparser.add_argument("--individual", "-i", default=None, type=dict, help="Additional individual configuration options")

        group = subparser.add_mutually_exclusive_group(required=True)
        group.add_argument("--wholemachine", "-w", action='store_true', help="")
        group.add_argument("--psps", "-p", action='store_true', help="")
        group.add_argument("--cell", "-k", type=str, default=None,  help="")
        group.add_argument("--bpm", "-b", type=int, default=None, help="")
        group.add_argument("--quad", "-q", type=int, default=None, help="")

    for subparser in [parser_run, parser_plot]:
        subparser.add_argument("--save_location", "-s", type=str, default=None, help="The location to save files to.")

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
        if args.bpm > len(machine.bpms_names):
            print(f"Invalid BPM selected. Try BPMs < {len(machine.bpms_names)}")
        else:
            elements = [machine.bpms_names[args.bpm]]
    if args.quad is not None:
        if args.quad > len(machine.quads_names):
            print(f"Invalid Quad selected. Try Quads < {len(machine.quads_names)}")
        else:
            elements = [machine.quads_names[args.quad]]
    return elements


def main():
    args = parse_arguments()
    if args.which == "info":
        elements = sort_elements(args)
        print(elements)

    elif args.which == "run":
        elements = sort_elements(args)
        cli_entrypoint(args.method, elements, args.save_location, args.config, args.individual)

    elif args.which == "plot":
        if args.quadcenter:
            cli_quadcenter_plot(args.save_location)
        if args.difference:
            pass


    # if args.element_names:
    #     cli_show_bpm_options(args.config, args.individual)
    # if args.cell is not None:
    #     cli_show_cell_options(args.cell, args.config, args.individual)
    # if args.quadcenter is not None:
    #     cli_quadcenter_plot(args.quadcenter)
    # if args.algorithm is not None:
    #     cli_entrypoint(
    #         args.algorithm, args.bpm, args.save_location, args.config, args.individual
    #     )


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
