import sys
from pathlib import Path

import cothread
import matplotlib
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow

matplotlib.use("Qt5Agg")

# from dls_bba.lattice import Lattice

_qapp = cothread.iqt(argv=sys.argv)

if sys.version_info > (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files

UI_FILENAME: list[str] = ["fbba_gui.ui"]
# export QT_QPA_PLATFORM=minimal


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ui_file = [
            Path(files("dls_bba").joinpath(resource)) for resource in UI_FILENAME
        ][0]
        uic.loadUi(ui_file, self)

        # lattice = Lattice()


def start_gui():
    window = MainWindow()
    window.show()
    print("Open")
    cothread.WaitForQuit()
