import logging as log
from typing import Any, Dict, List, Optional

from dls_bba.algorithm import Algorithm
from dls_bba.beam_current import BeamCurrentCheck
from dls_bba.common import ALGORITHMS, setup_folders
from dls_bba.components import get_component_pairs
from dls_bba.datatypes import Results
from dls_bba.excite import cancel_all_oscillations
from dls_bba.machine import Machine


class Worker:
    def __init__(
        self,
        method: str,
        elements: str,
        folder_path: str,
        logger: Optional[log.Handler],
        extra_config_files: Optional[List[str]] = None,
        additional_options: Optional[Dict[str, Any]] = None,
    ):
        self.save_location = setup_folders(method, folder_path, logger)
        self.machine = Machine(extra_config_files, additional_options)
        self.components_pairs = get_component_pairs(self.machine, elements)
        self.algorithm: Algorithm = ALGORITHMS[method](self.machine)
        self.save_rawdata = self.machine.config["SAVE_RAWDATA"]
        self.save_results = self.machine.config["SAVE_RESULTS"]
        self.results_list: List[Results] = []
        self.beam_current_decay: Optional[BeamCurrentCheck] = None
        log.debug("Worker initialised")

    def start(self):
        log.debug("Worker Start Started.")
        self.machine.zero_origins(self.save_location)
        self.beam_current_decay = BeamCurrentCheck(self.machine)
        log.debug("Worker Start Finished.")

    def work(self):
        """Must return true if more work to be done."""
        # Select first pair and remove it from list.
        if not self.components_pairs:
            return False
        log.debug("Work start")
        pair = self.components_pairs.pop(0)

        beam_current_drop = BeamCurrentCheck(self.machine)

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
        return True

    def pause(self):
        log.debug("Paused")

    def resume(self):
        log.debug("Resumed")

    def finish(self):
        log.debug("Finishing")
        self.algorithm.use_bba_offsets(self.results_list, self.save_location)
        cancel_all_oscillations(self.machine.config)
        self.machine.restore_origins(self.save_location)
        log.debug("Finished")


def run_worker(worker):
    worker.start()
    while worker.work():
        pass
    worker.finish()
