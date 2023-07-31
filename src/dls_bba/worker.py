import logging as log
import traceback
from typing import Any, Callable, Dict, List, Optional

from dls_bba.algorithm import Algorithm
from dls_bba.beam_current import BeamCurrentCheck
from dls_bba.common import ALGORITHMS, setup_folders_and_logger
from dls_bba.components import get_component_pairs
from dls_bba.datatypes import Results
from dls_bba.excite import cancel_all_oscillations
from dls_bba.machine import Machine


class Worker:
    def __init__(
        self,
        method: str,
        elements: List[str],
        question: Callable[[str], bool],
        folder_path: Optional[str],
        logger: Optional[log.Handler],
        extra_config_files: Optional[List[str]] = None,
        additional_options: Optional[Dict[str, Any]] = None,
    ):
        self.machine = Machine(extra_config_files, additional_options)
        folder_path = (
            folder_path
            if folder_path is not None
            else self.machine.config["SAVE_LOCATION"]
        )
        self.save_location = setup_folders_and_logger(method, folder_path, logger)
        self.components_pairs = get_component_pairs(self.machine, elements)
        self.starting_length = len(self.components_pairs)
        self.algorithm: Algorithm = ALGORITHMS[method](self.machine)
        self.question = question
        self.save_rawdata = self.machine.config["SAVE_RAWDATA"]
        self.save_results = self.machine.config["SAVE_RESULTS"]
        self.results_list: List[Results] = []
        self.beam_current_decay: Optional[BeamCurrentCheck] = None
        log.debug("Worker initialised")

    def start(self):
        log.debug("Worker Start Started.")
        self.machine.check_feedbacks()
        self.machine.zero_origins(self.save_location)
        self.beam_current_decay = BeamCurrentCheck(self.machine, self.question)
        log.debug("Worker Start Finished.")

    def work(self):
        """Must return true if more work to be done."""
        # Select first pair and remove it from list.
        if not self.components_pairs:
            return 0
        log.debug("Work start")
        pair = self.components_pairs.pop(0)

        beam_current_drop = BeamCurrentCheck(self.machine, self.question)

        while True:
            self.machine.check_feedbacks()
            rawdata = self.algorithm.run(pair)

            if beam_current_drop.check_beam_drop():
                break

        if self.save_rawdata:
            rawdata.save(self.save_location)

        results = self.algorithm.analyse(rawdata)
        if self.save_results:
            results.save(self.save_location)

        assert self.beam_current_decay is not None
        self.beam_current_decay.check_beam_decay()

        log.debug("Work end")
        return len(self.components_pairs) / self.starting_length

    def pause(self):
        log.debug("Paused")

    def resume(self):
        log.debug("Resumed")

    def finish(self):
        log.debug("Finishing")
        self.algorithm.use_bba_offsets(self.results_list, self.save_location, self.question)
        cancel_all_oscillations(self.machine.config)
        self.machine.restore_origins(self.save_location)
        log.debug("Finished")

    def forced_finish(self):
        log.debug("Forced finish")
        self.algorithm.reformat_and_save_offsets(self.results_list, self.save_location)
        cancel_all_oscillations(self.machine.config)
        self.machine.restore_origins(self.save_location)
        log.debug("Forced finish finished")


def show_progress(left):
    percent = "%.2f" % (100 * left)
    log.info(f"{percent}% left")


def run_worker(worker):
    try:
        worker.start()
        fraction = 1
        while fraction > 0:
            fraction = worker.work()
            show_progress(fraction)
        worker.finish()
    except Exception:
        traceback.print_exc()
        worker.forced_finish()


def ask_question(msg: str) -> bool:
    while True:
        log.debug(f"Question: {msg}")
        response = input(msg).lower().strip()
        log.debug(f"User Response: {response}")
        if response in "yn":
            return response == "y"
        else:
            print("Please answer y or n")
