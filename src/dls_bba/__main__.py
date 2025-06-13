import json
import sys
from argparse import ArgumentParser, Namespace
from typing import List

from dls_bba.common import ALGORITHMS, apply_folder, apply_golden, apply_single
from dls_bba.gui import start_gui
from dls_bba.machine import Machine
from dls_bba.plotting import bba_offsets_folder, bowtie_plot
from dls_bba.worker import Worker, ask_question, run_worker

from . import __version__

__all__ = ["main"]


def parse_arguments() -> Namespace:
    """Parse the command line arguments."""
    parent_parser = ArgumentParser(description="The options for using dls-bba module")
    subparsers = parent_parser.add_subparsers(title="actions")

    parent_parser.add_argument("--version", "-v", action="version", version=__version__)
    parent_parser.add_argument(
        "--config_files",
        "-c",
        default=None,
        type=str,
        help="additional configuration .json filepaths",
    )
    parent_parser.add_argument(
        "--additional_config",
        "-o",
        default=None,
        type=json.loads,
        help="additional individual configuration options (stringified dict)",
    )

    parser_info = subparsers.add_parser(
        "info",
        parents=[parent_parser],
        add_help=False,
        description="Get information on BBA",
    )
    parser_info.set_defaults(command="info")

    parser_run = subparsers.add_parser(
        "run",
        parents=[parent_parser],
        add_help=False,
        description="Run BBA",
        help="Run BBA",
    )
    parser_run.set_defaults(command="run")
    parser_run.add_argument(
        "--algorithm",
        "-a",
        default=None,
        type=str,
        choices=ALGORITHMS.keys(),
        required=True,
        help="the algorithm to use",
    )

    parser_plot = subparsers.add_parser(
        "plot",
        parents=[parent_parser],
        add_help=False,
        description="Plot BBA results",
        help="Plot BBA results",
    )
    parser_plot.set_defaults(command="plot")
    group = parser_plot.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--quadcenter",
        "-Q",
        action="store_true",
        help="plot the quadcentre for an individual BPM",
    )
    group.add_argument(
        "--difference",
        "-d",
        action="store_true",
        help="plot the relative differences across an entire BBA run",
    )

    parser_apply = subparsers.add_parser(
        "apply",
        parents=[parent_parser],
        add_help=False,
        description="Apply BBA results",
        help="Apply BBA results",
    )
    parser_apply.set_defaults(command="apply")
    parser_apply.add_argument(
        "--load", "-l", type=str, default=None, help="The location to load from."
    )
    group = parser_apply.add_mutually_exclusive_group(required=True)
    group.add_argument("--golden", "-g", action="store_true", help="")
    group.add_argument("--single", "-s", action="store_true", help="")
    group.add_argument("--multiple", "-m", action="store_true", help="")

    for subparser in [parser_info, parser_run]:
        group = subparser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--wholemachine", "-w", action="store_true", help="run BBA on all BPMs"
        )
        group.add_argument(
            "--psps",
            "-p",
            action="store_true",
            help="run BBA on all Primaries and Source Points",
        )
        group.add_argument(
            "--cell", "-k", type=str, default=None, help="run BBA on a specified cell"
        )
        group.add_argument(
            "--bpm", "-b", type=int, default=None, help="run BBA on a specified BPM"
        )
        group.add_argument(
            "--quad",
            "-q",
            type=int,
            default=None,
            help="run BBA on a specified quadrupole",
        )

    for subparser in [parser_run, parser_plot]:
        subparser.add_argument(
            "--filepath",
            "-f",
            type=str,
            default=None,
            help="the location to save files to",
        )

    return parent_parser.parse_args()


def sort_elements(args) -> List[str]:
    """Return the elements selected from the argparser.

    Args:
        args: The parsed arguments from the argparser.

    Returns:
        A list of elements.
    """
    # Additional config must be in the correct format Dict[str, Any]
    if args.additional_config is not None:
        assert all(isinstance(key, str) for key in args.additional_config.keys())

    machine = Machine(args.config_files, args.additional_config)
    elements: List[str] = []

    if args.wholemachine:
        elements = machine.bpms_names
    if args.psps:
        elements = machine.psps
    if args.cell is not None:
        cell = args.cell.zfill(2)
        if cell not in machine.cell_dictionary.keys():
            sys.exit("Invalid cell selected. Try cells '01' to '24'")
        else:
            elements = machine.cell_dictionary[cell]
    if args.bpm is not None:
        if (args.bpm > len(machine.bpms_names)) or (args.bpm <= 0):
            sys.exit(
                f"Invalid BPM selected. Try:  1 <= BPMs <= {len(machine.bpms_names)}"
            )
        else:
            elements = [machine.bpms_names[args.bpm - 1]]
    if args.quad is not None:
        if args.quad > len(machine.quads_names) or (args.quad <= 0):
            sys.exit(
                f"Invalid Quad selected. Try:  1 <= Quads <= {len(machine.quads_names)}"
            )
        else:
            elements = [machine.quads_names[args.quad - 1]]

    if not elements:
        sys.exit("Provided arguments resulted in 0 elements selected, exiting.")

    return elements


def main() -> None:
    """The main CLI entrypoint for the BBA package."""
    args = parse_arguments()
    if args.command == "info":
        elements = sort_elements(args)
        print(elements)

    elif args.command == "run":
        elements = sort_elements(args)
        worker = Worker(
            args.algorithm,
            elements,
            ask_question,
            args.filepath,
            None,
            args.config_files,
            args.additional_config,
        )
        run_worker(worker)

    elif args.command == "plot":
        if args.quadcenter:
            machine = Machine(args.config_files, args.additional_config)
            bowtie_plot(args.filepath, True)
        if args.difference:
            machine = Machine(args.config_files, args.additional_config)
            bba_offsets_folder(machine, args.filepath, True)

    elif args.command == "apply":
        if args.golden:
            apply_golden(args.load, None, args.config_files, args.additional_config)
        if args.single:
            apply_single(args.load, None, args.config_files, args.additional_config)
        if args.folder:
            apply_folder(args.load, None, args.config_files, args.additional_config)


def parse_gui_arguments(args=None) -> None:
    """Allow the GUI to accept -v and --version arguments."""
    parser = ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version=__version__)
    args = parser.parse_args(args)


def gui_main() -> None:
    """The main GUI entrypoint for the BBA package."""
    parse_gui_arguments()
    start_gui()


# test with: python -m dls_bba
if __name__ == "__main__":
    main()
