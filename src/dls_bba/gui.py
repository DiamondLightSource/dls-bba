import sys
from pathlib import Path

# isort: off
import matplotlib

matplotlib.use("Qt5Agg")  # noqa: E402
# isort: on

import cothread  # noqa: E402
from PyQt6 import uic  # noqa: E402
from PyQt6.QtWidgets import QMainWindow  # noqa: E402

from dls_bba.common import ALGORITHMS  # noqa: E402
from dls_bba.machine import Machine  # noqa: E402

_qapp = cothread.iqt()

if sys.version_info > (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files

UI_FILENAME: list[str] = ["fbba_gui.ui"]


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ui_file = [
            Path(files("dls_bba").joinpath(resource)) for resource in UI_FILENAME
        ][0]
        uic.loadUi(ui_file, self)

        machine = Machine()
        self.setup_main_window(machine)

    def setup_main_window(self, machine):
        # Methods
        self.box_method.addItems(ALGORITHMS.keys())
        self.box_method.setCurrentText(list(ALGORITHMS.keys())[0])
        # Mode

        # Mode Selection


def start_gui():
    window = MainWindow()
    window.show()
    cothread.WaitForQuit()
