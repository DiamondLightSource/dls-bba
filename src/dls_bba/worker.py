import logging as log
import traceback
from collections.abc import Callable
from typing import Any

from cothread import cothread

from dls_bba.algorithm import Algorithm
from dls_bba.beam_current import BeamCurrentCheck
from dls_bba.common import ALGORITHMS, setup_folders_and_logger
from dls_bba.components import get_component_pairs
from dls_bba.datatypes import FullResults
from dls_bba.excite import cancel_all_oscillations
from dls_bba.machine import Machine


class Worker:
    def __init__(
        self,
        method: str,
        elements: list[str],
        question_callback: Callable[[str], bool],
        machine: Machine | None = None,
        folder_path: str | None = None,
        logger: log.Handler | None = None,
        extra_config_files: list[str] | None = None,
        additional_options: dict[str, Any] | None = None,
    ) -> None:
        """Initialise the worker and setup for performing a BBA.

        Args:
            method: The BBA method.
            elements: The elements to perform a BBA on.
            question_callback: The question function dependant on using the GUI or CLI.
            machine: A machine instance.
            folder_path: The save location folder path.
            logger: The GUI logger handler.
            extra_config_files: List of extra configuration files to load.
            additional_options: Dictionary of configuration overrides.
        """
        if machine is not None:
            machine.update_config(extra_config_files, additional_options)
            self.machine = machine
        else:
            self.machine = Machine(extra_config_files, additional_options)
        folder_path = (
            folder_path
            if folder_path is not None
            else self.machine.config["SAVE_LOCATION"]
        )
        self.save_location = setup_folders_and_logger(method, folder_path, logger)
        log.debug(f"Running {method} against {elements} results saved to {folder_path}")
        self.components_pairs = get_component_pairs(self.machine, elements)
        self.starting_length = len(self.components_pairs)
        if method not in ALGORITHMS:
            raise KeyError(
                f"Invalid BBA algorithm '{method}', please select one of: "
                f"{list(ALGORITHMS.keys())}"
            )
        else:
            self.algorithm: Algorithm = ALGORITHMS[method](self.machine)
        self.question_callback = question_callback
        self.save_rawdata = self.machine.config["SAVE_RAWDATA"]
        self.save_results = self.machine.config["SAVE_RESULTS"]
        self.results_list: list[FullResults] = []
        self.beam_current_decay: BeamCurrentCheck | None = None
        log.debug("Worker initialised")

    def start(self) -> None:
        """Start the BBA process."""
        log.debug("Worker Start Started.")
        self.machine.check_feedbacks()
        self.machine.zero_origins(self.save_location)
        self.beam_current_decay = BeamCurrentCheck(self.machine, self.question_callback)
        log.debug("Worker Start Finished.")

    def work(
        self,
        stop_event: cothread.Event | None = None,
        pause_event: cothread.Event | None = None,
    ) -> float:
        """Complete an iteration of the BBA process.

        Args:
            stop_event: Cothread event which is triggered when the GUI stop button
                        is pressed.
            pause_event: Cothread event which is triggered when the GUI pause/resume
                        button is pressed. Acts as both a pause and unpause event.

        Returns:
            A fraction of the remaining BBA pairs over the total number of pairs.
        """
        # Select first pair and remove it from list.
        if not self.components_pairs:
            return 0.0
        log.debug("Work start")
        pair = self.components_pairs.pop(0)

        beam_current_drop = BeamCurrentCheck(self.machine, self.question_callback)

        while True:
            self.machine.check_feedbacks()
            rawdata = self.algorithm.run(pair, stop_event, pause_event)

            if beam_current_drop.check_beam_not_dropped():
                break

        if not bool(stop_event) and rawdata is not None:
            if self.save_rawdata is not None:
                rawdata.save(self.save_location)

            results = self.algorithm.analyse(rawdata)
            if self.save_results:
                results.save(self.save_location)
            self.results_list.append(results)

        assert self.beam_current_decay is not None
        self.beam_current_decay.check_beam_not_decayed()

        log.debug("Work end")
        return len(self.components_pairs) / self.starting_length

    def finish(self, stop_event: cothread.Event | None = None) -> None:
        """The process is finished.

        Args:
            stop_event: Cothread event which is triggered when the GUI stop button
                        is pressed.
        """

        log.debug("Finishing")
        if not bool(stop_event):
            self.algorithm.use_bba_offsets(
                self.results_list, self.save_location, self.question_callback
            )
        cancel_all_oscillations(self.machine.config)
        self.machine.restore_origins(self.save_location)
        log.debug("Finished")

    def forced_finish(self) -> None:
        """The process is finished (forced/unexpected)."""
        log.debug("Forced finish")
        self.algorithm.reformat_and_save_offsets(self.results_list, self.save_location)
        cancel_all_oscillations(self.machine.config)
        self.machine.restore_origins(self.save_location)
        log.debug("Forced finish finished")


def show_progress(left: float) -> None:
    """Log the percentage progress of the BBA.

    args:
        left: The fraction of work remaining.
    """
    log.info(f"{100 * left:.2f}% left")


def run_worker(worker: Worker) -> None:
    """Run the BBA.

    args:
        worker: The worker to run BBA from.
    """
    try:
        worker.start()
        fraction: float = 1.0
        while fraction > 0:
            fraction = worker.work()
            show_progress(fraction)
        worker.finish()
    except Exception:
        traceback.print_exc()
        worker.forced_finish()


def ask_question(msg: str) -> bool:
    """The CLI callable for asking a question.

    Args:
        msg: The message you want to ask.

    Returns:
        A bool response.
    """
    while True:
        log.debug(f"Question: {msg}")
        response = input(msg).lower().strip()
        log.debug(f"User Response: {response}")
        if response in "yn":
            return response == "y"
        else:
            print("Please answer y or n")
