"""Interface for ``python -m dls_bba``."""

import json
import sys
from argparse import ArgumentParser, Namespace

from dls_bba.common import ALGORITHMS, apply_folder, apply_offset_files, apply_single
from dls_bba.gui import start_gui
from dls_bba.machine import Machine
from dls_bba.plotting import bba_offsets_folder, bowtie_plot
from dls_bba.worker import Worker, ask_question, run_worker

from . import __version__

__all__ = ["main"]


def add_common_arguments(parser: ArgumentParser) -> None:
    """Add common argument parsing."""
    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument(
        "-c",
        "--config_files",
        default=None,
        type=str,
        help="additional configuration .json filepaths",
    )
    parser.add_argument(
        "-o",
        "--additional_config",
        default=None,
        type=json.loads,
        help="additional individual configuration options (stringified dict)",
    )


def add_action_arguments(info_parser, run_parser, plot_parser, apply_parser):
    """Add argument parsing for the action sub-commands"""
    run_parser.add_argument(
        "-a",
        "--algorithm",
        default=None,
        type=str,
        choices=ALGORITHMS.keys(),
        required=True,
        help="the algorithm to use",
    )
    group = plot_parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-Q",
        "--quadcenter",
        action="store_true",
        help="plot the quadcentre for an individual BPM",
    )
    group.add_argument(
        "-d",
        "--difference",
        action="store_true",
        help="plot the relative differences across an entire BBA run",
    )

    apply_parser.add_argument(
        "-l", "--load", type=str, default=None, help="The location to load from."
    )
    group = apply_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-g", "--golden", action="store_true", help="")
    group.add_argument("-s", "--single", action="store_true", help="")
    group.add_argument("-m", "--multiple", action="store_true", help="")

    for subparser in [info_parser, run_parser]:
        group = subparser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "-w", "--wholemachine", action="store_true", help="run BBA on all BPMs"
        )
        group.add_argument(
            "-p",
            "--psps",
            action="store_true",
            help="run BBA on all Primaries and Source Points",
        )
        group.add_argument(
            "-k", "--cell", type=str, default=None, help="run BBA on a specified cell"
        )
        group.add_argument(
            "-b", "--bpm", type=int, default=None, help="run BBA on a specified BPM"
        )
        group.add_argument(
            "-q",
            "--quad",
            type=int,
            default=None,
            help="run BBA on a specified quadrupole",
        )

    for subparser in [run_parser, plot_parser]:
        subparser.add_argument(
            "-f",
            "--filepath",
            type=str,
            default=None,
            help="the location to save files to",
        )


def setup_parser():
    parent_parser = ArgumentParser(description="The options for using dls-bba module")
    subparsers = parent_parser.add_subparsers(title="actions")

    info_parser = subparsers.add_parser(
        "info",
        add_help=False,
        description="Get information on BBA",
    )
    run_parser = subparsers.add_parser(
        "run",
        add_help=False,
        description="Run BBA",
        help="Run BBA",
    )
    plot_parser = subparsers.add_parser(
        "plot",
        add_help=False,
        description="Plot BBA results",
        help="Plot BBA results",
    )
    apply_parser = subparsers.add_parser(
        "apply",
        add_help=False,
        description="Apply BBA results",
        help="Apply BBA results",
    )

    info_parser.set_defaults(command="info")
    run_parser.set_defaults(command="run")
    plot_parser.set_defaults(command="plot")
    apply_parser.set_defaults(command="apply")

    add_common_arguments(parent_parser)
    add_action_arguments(info_parser, run_parser, plot_parser, apply_parser)

    return parent_parser


def parse_arguments(argv: list[str] | None = None) -> Namespace:
    """Parse the command line arguments."""
    parent_parser = setup_parser()
    if argv is None:
        argv = sys.argv[1:]

    args = parent_parser.parse_args(argv)
    return args


def sort_elements(args) -> list[str]:
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
    elements: list[str] = []

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


def main(args: Namespace | None = None) -> None:
    """The main CLI entrypoint for the BBA package."""
    args = parse_arguments()
    if args.command == "info":
        elements = sort_elements(args)
        print(elements)

    elif args.command == "run":
        if args.algorithm is None:
            sys.exit("No algorithm selected please specify one using -a or --algorithm")
        elif args.algorithm not in ALGORITHMS.keys():
            sys.exit(
                f"Invalid algorithm '{args.algorithm}' please try one of "
                f"{ALGORITHMS.keys()}"
            )
        elements = sort_elements(args)
        worker = Worker(
            args.algorithm,
            elements,
            ask_question,
            folder_path=args.filepath,
            extra_config_files=args.config_files,
            additional_options=args.additional_config,
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
            apply_offset_files(
                args.load, None, args.config_files, args.additional_config
            )
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


if __name__ == "__main__":
    main()
