from typing import Any, Dict, List, Optional

import cothread

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
        extra_config_files: Optional[List[str]] = None,
        additional_options: Optional[Dict[str, Any]] = None,
    ):
        self.save_location = setup_folders(method, folder_path)
        self.machine = Machine(extra_config_files, additional_options)
        self.components_pairs = get_component_pairs(self.machine, elements)
        self.algorithm: Algorithm = ALGORITHMS[method](self.machine)
        self.save_rawdata = self.machine.config["SAVE_RAWDATA"]
        self.save_results = self.machine.config["SAVE_RESULTS"]
        self.results_list: List[Results] = []
        self.beam_current_decay: Optional[BeamCurrentCheck] = None
        print("Worker init")

    def start(self):
        print("Start start")

        self.machine.zero_origins(self.save_location)
        self.beam_current_decay = BeamCurrentCheck(self.machine)
        print("Start end")

    def work(self):
        """Must return true if more work to be done."""
        # Select first pair and remove it from list.
        if not self.components_pairs:
            return False
        print("Work start")
        pair = self.components_pairs.pop(0)
        cothread.Sleep(1)

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

        print("Work end")
        return True

    def pause(self):
        print("Paused")

    def resume(self):
        print("Resumed")

    def finish(self):
        print("Finishing")
        self.algorithm.use_bba_offsets(self.results_list, self.save_location)
        cancel_all_oscillations(self.machine.config)
        self.machine.restore_origins(self.save_location)
        print("Finished")


def run_worker(worker):
    worker.start()
    while worker.work():
        pass
    worker.finish()
