import os
import signal
import sys
from pathlib import Path

# isort: off
import matplotlib
from cothread.cothread import Callback, _QuitEvent

matplotlib.use("Qt5Agg")  # noqa: E402
# isort: on

import cothread  # noqa: E402
from PyQt6 import QtCore, uic  # noqa: E402
from PyQt6.QtWidgets import (  # noqa: E402
    QApplication,
    QFileDialog,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from dls_bba.common import ALGORITHMS  # noqa: E402
from dls_bba.datatypes import Results  # noqa: E402
from dls_bba.machine import Machine  # noqa: E402
from dls_bba.plotting import bba_offsets_folder, bowtie_plot

_qapp = cothread.iqt()

if sys.version_info > (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files

UI_FILENAME: list[str] = ["fbba_gui.ui"]
# DEFAULT_SAVE_LOCATION: str = "/dls/ops-physics/diamonddata/fastBBA"
DEFAULT_SAVE_LOCATION = "/dls/physics/owr68555/11July2023"


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ui_file = [
            Path(files("dls_bba").joinpath(resource)) for resource in UI_FILENAME
        ][0]
        uic.loadUi(ui_file, self)

        self.machine = Machine()
        self.setup_machine_args()
        self.setup_main_window()

    def setup_machine_args(self):
        self.modes = {  # Mode name: [selection_strings, arguments]
            "Whole Machine": [["Whole Machine"], self.machine.bpms_names],
            "Cells": [
                list(self.machine.cell_dictionary.keys()),
                self.machine.cell_dictionary,
            ],
            "BPMs": [self.machine.bpms_names, self.machine.bpms_names],
            "Quadrupoles": [self.machine.quads_names, self.machine.quads_names],
            "PSPs": [["All PSPs"], self.machine.psps],
        }

    def setup_main_window(self):
        # Methods
        self.method_dropdown.addItems(ALGORITHMS.keys())
        self.method_dropdown.setCurrentText(list(ALGORITHMS.keys())[0])
        # Mode
        self.display_on_screen("Please select a mode.", clear=True)

        # Mode Selection
        self.options = None
        self.display = None
        self.selected = None
        self.whole_machine.clicked.connect(lambda: self.select_mode("Whole Machine"))
        self.cell.clicked.connect(lambda: self.select_mode("Cells"))
        self.bpms.clicked.connect(lambda: self.select_mode("BPMs"))
        self.quadrupoles.clicked.connect(lambda: self.select_mode("Quadrupoles"))
        self.psps.clicked.connect(lambda: self.select_mode("PSPs"))

        self.selected_toggle = 0
        self.lock_unlock_pv.clicked.connect(lambda: self.lock_unlock_selection())

        # File / Folder selection, plotting and applying.
        self.button_save_loc.clicked.connect(lambda: self.select_save_location_folder())
        self.display_save_loc.setPlainText(DEFAULT_SAVE_LOCATION)
        self.button_bba_folder.clicked.connect(lambda: self.select_bba_folder())
        self.display_bba_folder.setPlainText("Not Selected")
        self.button_single_bba.clicked.connect(lambda: self.select_bba_file())
        self.display_single_bba.setPlainText("Not Selected")

        self.plot_bba.clicked.connect(lambda: self.plot_bba_folder())
        #self.apply_bba.clicked.connect()

        self.plot_single_bba.clicked.connect(lambda: self.plot_bba_file())

        self.tabWidget.setCurrentIndex(0)
        # Quitting
        self.force_close = False

    def plot_bba_file(self):
        if self.loadfile is None:
            self.display_bba_folder.clear()
            self.display_bba_folder.setPlainText("Please select a file to load.")

        bowtie_plot(self.loadfile, os.path.dirname(self.loadfile), True)

    def plot_bba_folder(self):

        if self.loadfolder is None:
            self.display_bba_folder.clear()
            self.display_bba_folder.setPlainText("Please select a folder to load.")

        good_files = []
        for file in os.listdir(self.loadfolder):
            if file.endswith("-results.mat"):
                good_files.append(os.path.join(self.loadfolder, file))

        load_folder_results = [Results.from_file(file) for file in good_files]

        bba_offsets_folder(self.machine, load_folder_results, self.loadfolder, False)

    def select_save_location_folder(self):
        folderpath = QFileDialog.getExistingDirectory(
            self, "Select Folder to Save to", DEFAULT_SAVE_LOCATION
        )
        self.display_save_loc.setPlainText(folderpath)
        self.savepath = folderpath

    def select_bba_folder(self):
        folderpath = QFileDialog.getExistingDirectory(
            self, "Select Folder to load", DEFAULT_SAVE_LOCATION
        )
        self.display_bba_folder.setPlainText(folderpath)
        self.loadfolder = folderpath
        self.load_folder_results = None

    def select_bba_file(self):
        filepath = QFileDialog.getOpenFileName(
            self,
            "Select a Results.mat File to load",
            DEFAULT_SAVE_LOCATION,
            "Results MATLAB Files (*-results.mat)",
        )
        self.display_single_bba.setPlainText(filepath[0])
        self.loadfile = filepath[0]

    def select_mode(self, key):
        values = self.modes[key]
        selection_strings, options = values[0], values[1]
        # Clear and redraw selection
        self.pv_selection.clear()
        self.pv_selection.addItems(selection_strings)
        self.last_list = selection_strings
        self.selection_strings = selection_strings
        self.options = options

    def lock_unlock_selection(self) -> None:
        if self.selected_toggle == 0:
            if self.select_options():
                self.disable_mode_selection()
                self.selected_toggle = 1
                return

        if self.selected_toggle == 1:
            self.options = None
            self.display = None
            self.selected = None
            self.enable_mode_selection()
            self.selected_toggle = 0
            return

    def enable_mode_selection(self):
        self.whole_machine.setEnabled(True)
        self.cell.setEnabled(True)
        self.bpms.setEnabled(True)
        self.quadrupoles.setEnabled(True)
        self.psps.setEnabled(True)
        self.lock_unlock_pv.setText("Select")
        # Set the list to full previously selected list.
        self.pv_selection.clear()
        self.pv_selection.addItems(self.last_list)
        for i in range(self.pv_selection.count()):
            it = self.pv_selection.item(i)
            it.setFlags(it.flags() | QtCore.Qt.ItemFlag.ItemIsEnabled)

    def disable_mode_selection(self):
        self.whole_machine.setEnabled(False)
        self.cell.setEnabled(False)
        self.bpms.setEnabled(False)
        self.quadrupoles.setEnabled(False)
        self.psps.setEnabled(False)
        self.lock_unlock_pv.setText("Unselect")
        # Set the list to only selected items.
        temp_selected = [item.text() for item in self.pv_selection.selectedItems()]
        self.pv_selection.clear()
        self.pv_selection.addItems(temp_selected)
        for i in range(self.pv_selection.count()):
            it = self.pv_selection.item(i)
            it.setFlags(it.flags() & ~QtCore.Qt.ItemFlag.ItemIsEnabled)

    def select_options(self) -> bool:
        selected = self.pv_selection.selectedItems()

        if len(selected) == 0:
            msg = "Please select a mode."
            self.display_on_screen(msg, clear=True)
            self.selected = None
            return False

        elif len(selected) == 1 and any(
            True for x in ["Whole Machine", "All PSPs"] if x in self.selection_strings
        ):
            msg = f"{self.selection_strings[0]} selected."
            self.display_on_screen(msg, clear=True)
            self.selected = self.options
            return True

        elif len(selected) == 1 and not any(
            True for x in ["Whole Machine", "All PSPs"] if x in self.selection_strings
        ):
            if len(selected[0].text()) == 2:
                cell_number = selected[0].text()
                elements = self.machine.cell_dictionary[cell_number]
                msg = f"Cell {cell_number} selected."
                self.display_on_screen(msg, clear=True)
                self.selected = elements
                return True

            else:
                element = selected[0].text()
                msg = f"{element} selected."
                self.display_on_screen(msg, clear=True)
                self.selected = element
                return True

        else:
            if len(selected[0].text()) == 2:
                cells = [element.text() for element in selected]
                elements = []
                for cell in cells:
                    elements.extend(self.machine.cell_dictionary[cell])
                msg = f"Cells {cells} selected."
                self.display_on_screen(msg, clear=True)
                self.selected = elements
                return True

            else:
                elements = [element.text() for element in selected]
                msg = f"{len(elements)} elements selected."
                self.display_on_screen(msg, clear=True)
                self.selected = elements
                return True

    def display_on_screen(self, text, clear=False):
        if clear:
            self.screen.clear()
            QApplication.processEvents()
        self.screen.appendPlainText(text)
        QApplication.processEvents()

    def closeEvent(self, event=None):
        if self.force_close:
            print("Force Closed.")
            # if mid_oscillation:
            #     prime all IOCs
            # reset all golden offsets and reset quad posisitons.
        else:
            print("Closed Gracefully.")
        # In every scenario -> Reset all IOCs.
        # set all start times to 0's, then prime.
        print("Exited.")


def start_gui():
    window = MainWindow()
    window.show()
    # cothread.WaitForQuit()

    def graceful_exit():
        window.closeEvent()
        _QuitEvent.Signal()

    signal.signal(signal.SIGINT, lambda signum, frame: Callback(graceful_exit))
    _QuitEvent.Wait()
