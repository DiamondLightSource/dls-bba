import time
from unittest.mock import MagicMock

import cothread
import pytest

from dls_bba.algorithm import Algorithm


class DummyAlgorithm(Algorithm):
    def __init__(self, machine) -> None:
        super().__init__(machine)

    def run(self):
        pass

    def analyse(self):
        pass


def test_algorithm_stop():
    algorithm = DummyAlgorithm(MagicMock())
    assert not algorithm._check_stop_status()
    algorithm.stop_run()
    assert algorithm._check_stop_status()


@pytest.mark.timeout(2)
def test_algorithm_pause():
    algorithm = DummyAlgorithm(MagicMock())
    start = time.monotonic()

    def unpause():
        cothread.Sleep(0.2)
        algorithm.resume_run()

    # Pause, spawn a second thread to unpause and then check that we unpaused
    algorithm.pause_run()
    cothread.Spawn(unpause)
    algorithm._check_and_wait_pause_status()

    end = time.monotonic()
    assert end - start >= 0.2, "No pause detected"
