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
from cothread.catools import FORMAT_CTRL, caget  # noqa: E402
from PyQt6 import QtCore, uic  # noqa: E402
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow  # noqa: E402

from dls_bba.common import ALGORITHMS  # noqa: E402
from dls_bba.datatypes import Results  # noqa: E402
from dls_bba.excite import cancel_all_oscillations  # noqa E402
from dls_bba.fbba import FastBBA  # noqa: E402
from dls_bba.isotime import get_isotime  # noqa: E402
from dls_bba.machine import Machine  # noqa: E402
from dls_bba.plotting import bba_offsets_folder, bowtie_plot  # noqa: E402
from dls_bba.worker import Worker  # noqa: E402

_qapp = cothread.iqt()

if sys.version_info > (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files

UI_FILENAME: list[str] = ["fbba_gui.ui"]
# DEFAULT_SAVE_LOCATION: str = "/dls/ops-physics/diamonddata/fastBBA"
delay = 1


class Ticker:
    #    def __init__(self, worker, on_update):
    def __init__(self, on_update):
        self.__action = cothread.Event()
        self.__on_update = on_update
        self.__state = "Idle"
        cothread.Spawn(self.__ticker)

    def __ticker(self):
        while True:
            action = ""
            while action != "run":
                action, worker = self.__action.Wait()
            self.__set_state("Running")

            worker.start()
            running = True
            while action == "run" and running:
                if self.__action:
                    action, _ = self.__action.Wait()

                if action == "run":
                    running = worker.work()

                elif action == "pause":
                    worker.pause()
                    self.__set_state("Paused")
                    action = self.__action.Wait()
                    worker.resume()
                    self.__set_state("Running")

            self.__set_state("Complete")
            worker.finish()
            self.__set_state("Idle")

    def __set_state(self, state):
        old_state = self.__state
        self.__state = state
        self.__on_update(old_state, state)

    def start_ticker(self, worker):
        self.__action.Signal(("run", worker))

    def pause_ticker(self):
        self.__action.Signal(("pause", None))

    def stop_ticker(self):
        self.__action.Signal(("stop", None))

    def resume_ticker(self):
        self.__action.Signal(("run", None))

    def pause_resume_ticker(self):
        if self.__state == "Running":
            self.pause_ticker()
        elif self.__state == "Paused":
            self.resume_ticker()
        else:
            print("Don't know what to do with", self.__state)

    @property
    def state(self):
        return self.__state


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
        self.show_config()

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
        self.method_dropdown.setCurrentText(list(ALGORITHMS.keys())[2])
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
        self.display_save_loc.setPlainText(self.machine.config["SAVE_LOCATION"])
        self.button_bba_folder.clicked.connect(lambda: self.select_bba_folder())
        self.display_bba_folder.setPlainText("Not Selected")
        self.button_single_bba.clicked.connect(lambda: self.select_bba_file())
        self.display_single_bba.setPlainText("Not Selected")

        self.plot_bba.clicked.connect(lambda: self.plot_bba_folder())
        self.apply_bba.clicked.connect(lambda: self.apply_bba_folder())

        self.plot_single_bba.clicked.connect(lambda: self.plot_bba_file())
        self.apply_single_bba.clicked.connect(lambda: self.apply_bba_file())

        # Front page buttons
        self.ticker = Ticker(self.ticker_update)
        self.pause_counter = 0
        self.button_start.clicked.connect(self.start_ticker)
        self.button_pause.clicked.connect(self.pause_resume_ticker)
        self.button_stop.clicked.connect(self.stop_ticker)

        self.button_reset.clicked.connect(lambda: self.reset_iocs())

        # Configuration options
        self.tmp_single_filepath = None
        self.config_ringmode.addItems(self.get_ringmode_options())
        self.config_load_apply.clicked.connect(lambda: self.load_config_file())
        self.button_golden.clicked.connect(lambda: self.reapply_golden_orbits())

        self.tabWidget.setCurrentIndex(0)

    def start_ticker(self):
        self.update_config()
        self.button_start.setEnabled(False)
        self.button_pause.setEnabled(True)
        self.button_stop.setEnabled(True)
        print("gui start")
        self.ticker.start_ticker(self.get_worker())

    def pause_resume_ticker(self):
        print("gui pause/resume")
        self.ticker.pause_resume_ticker()
        print(f"State: {self.ticker.state}")
        if self.ticker.state == "Running":
            self.button_pause.setText("Resume")
        elif self.ticker.state == "Paused":
            self.button_pause.setText("Pause")

    def stop_ticker(self):
        print("gui stop")
        self.ticker.stop_ticker()
        self.button_start.setEnabled(True)
        self.button_pause.setEnabled(False)
        self.button_stop.setEnabled(False)

    def ticker_update(self, old_state, new_state):
        print("Ticker state:", old_state, "=>", new_state)

    def get_worker(self):
        method = self.method_dropdown.currentText()
        folder_path = self.machine.config["SAVE_LOCATION"]
        print(method)
        print(self.selected, type(self.selected), type(self.selected[0]))
        print(folder_path)
        return Worker(method, self.selected, folder_path)

    def reset_iocs(self):
        cancel_all_oscillations(self.machine.config)

    def reapply_golden_orbits(self):
        self.display_golden.clear()
        file = QFileDialog.getOpenFileName(
            self,
            "Select a golden .json File to load",
            self.machine.config["SAVE_LOCATION"],
            "JSON files (*.json)",
        )
        if file == ("", ""):
            self.display_golden.setText("No file selected.")
            return
        selected_file = file[0]
        self.machine.restore_origins(selected_file)
        self.display_golden.setText(f"Golden Orbits restored at {get_isotime()}")

    def load_config_file(self):
        self.display_config_load.clear()
        file = QFileDialog.getOpenFileName(
            self,
            "Select a config .json File to load",
            self.machine.config["SAVE_LOCATION"],
            "JSON files (*.json)",
        )
        if file == ("", ""):
            self.display_config_load.setText("No file selected.")
            return
        list_file = [file[0]]
        self.machine._update_config(extra_config_files=list_file)
        self.show_config()
        # Allow for lattice reload.
        cothread.Yield()
        self.display_config_load.setText(f"Config File Applied at {get_isotime()}")

    def get_ringmode_options(self):
        ringmodes = caget("SR-CS-RING-01:MODE", format=FORMAT_CTRL).enums
        return ringmodes

    def update_config(self):
        dct = {
            "FEEDBACKS": self.config_use_feedbacks.isChecked(),
            "MAX_ORBIT_CORRECTION_MICRONS": self.config_max_orbit.value(),
            "MIN_CURRENT": self.config_current_limit.value(),
            "CORRECTOR_KICK_RADIANS": self.config_corr_kick.value() * 1e-6,
            "QUADRUPOLE_STEP_PERCENT": self.config_quad_step.value(),
            "WARNING_CURRENT_DROP": self.config_warning_current.value(),
            "CRITICAL_CURRENT_DROP": self.config_critical_current.value(),
            "FEEDBACK_WAITTIME": self.config_waittime.value(),
            "FEEDBACK_RUNTIME": self.config_runtime.value(),
            "MIN_SLOPE_FRACTION": self.config_sbba_min_frac.value(),
            "CENTER_OUTLIER_FACTOR": self.confifg_sbba_stdev.value(),
            "DECIMATED": self.config_use_decimation.isChecked(),
            "X_CYCLES": self.config_x_cycles.value(),
            "X_FREQUENCY": self.config_x_freq.value(),
            "Y_CYCLES": self.config_y_cycles.value(),
            "Y_FREQUENCY": self.config_y_freq.value(),
            "SAVE_RAWDATA": self.save_rawdata.isChecked(),
            "SAVE_RESULTS": self.save_results.isChecked(),
            "SAVE_PLOTS": self.save_plots.isChecked(),
            "RINGMODE": self.config_ringmode.currentText(),
            "UNITS": self.config_units.currentText(),
            "DATASOURCE": self.config_datasource.currentText(),
            "COTHREAD_CONTROL_SYSTEM_TIMEOUT": self.config_ccs_timeout.value(),
            "COTHREAD_CONTROL_SYSTEM_WAIT_FLAG": self.config_ccs_wait.isChecked(),
            "FOFB_NOGUI_PATH": self.config_fofb_nogui_path.toPlainText(),
            "FOFB_MAX_ORBIT_MICRONS": self.config_fofb_max_orbit.value(),
            "ORBIT_RESPONSE_MATRIX_PATH": self.config_orm_path.toPlainText(),
            "CORRECTORS_TXT_PATH": self.config_corrector_txt_path.toPlainText(),
        }
        self.machine._update_config(dct=dct)
        self.show_config()
        cothread.Yield()

    def show_config(self):
        config = self.machine.config

        self.config_use_feedbacks.setChecked(config["FEEDBACKS"])
        self.config_max_orbit.setValue(config["MAX_ORBIT_CORRECTION_MICRONS"])
        self.config_current_limit.setValue(config["MIN_CURRENT"])

        self.config_corr_kick.setValue(config["CORRECTOR_KICK_RADIANS"] * 1e6)
        self.config_quad_step.setValue(config["QUADRUPOLE_STEP_PERCENT"])
        self.config_warning_current.setValue(config["WARNING_CURRENT_DROP"])
        self.config_critical_current.setValue(config["CRITICAL_CURRENT_DROP"])
        self.config_waittime.setValue(config["FEEDBACK_WAITTIME"])
        self.config_runtime.setValue(config["FEEDBACK_RUNTIME"])
        self.config_sbba_min_frac.setValue(config["MIN_SLOPE_FRACTION"])
        self.confifg_sbba_stdev.setValue(config["CENTER_OUTLIER_FACTOR"])
        self.config_use_decimation.setChecked(config["DECIMATED"])
        self.config_x_cycles.setValue(config["X_CYCLES"])
        self.config_x_freq.setValue(config["X_FREQUENCY"])
        self.config_y_cycles.setValue(config["Y_CYCLES"])
        self.config_y_freq.setValue(config["Y_FREQUENCY"])
        self.save_rawdata.setChecked(config["SAVE_RAWDATA"])
        self.save_results.setChecked(config["SAVE_RESULTS"])
        self.save_plots.setChecked(config["SAVE_PLOTS"])

        self.config_ringmode.setCurrentText(config["RINGMODE"])
        self.config_units.setCurrentText(config["UNITS"])
        self.config_datasource.setCurrentText(config["DATASOURCE"])
        self.config_ccs_timeout.setValue(config["COTHREAD_CONTROL_SYSTEM_TIMEOUT"])
        self.config_ccs_wait.setChecked(config["COTHREAD_CONTROL_SYSTEM_WAIT_FLAG"])
        self.config_fofb_nogui_path.setText(config["FOFB_NOGUI_PATH"])
        self.config_fofb_max_orbit.setValue(config["FOFB_MAX_ORBIT_MICRONS"])
        self.config_orm_path.setText(config["ORBIT_RESPONSE_MATRIX_PATH"])
        self.config_corrector_txt_path.setText(config["CORRECTORS_TXT_PATH"])

    def apply_bba_folder(self):
        if self.loadfolder is None:
            self.display_bba_folder.clear()
            self.display_bba_folder.setPlainText("Please select a folder to apply.")

        good_files = []
        for file in os.listdir(self.loadfolder):
            if file.endswith("-results.mat"):
                good_files.append(os.path.join(self.loadfolder, file))

        load_folder_results = [Results.from_file(file) for file in good_files]

        offsets_dict = {}
        for results in load_folder_results:
            offsets_dict.update(results.offsets.items())

        algorithm = FastBBA(self.machine)
        algorithm.apply_bba_offsets(offsets_dict)

    def apply_bba_file(self):
        if self.loadfile is None:
            self.display_bba_folder.clear()
            self.display_bba_folder.setPlainText("Please select a file to apply.")

        results_file = Results.from_file(self.loadfile)
        algorithm = FastBBA(self.machine)
        algorithm.apply_bba_offsets(results_file.offsets)

    def plot_bba_file(self):
        if self.loadfile is None:
            self.display_bba_folder.clear()
            self.display_bba_folder.setPlainText("Please select a file to plot.")

        bowtie_plot(
            self.loadfile,
            os.path.dirname(self.loadfile),
            self.machine.config["SAVE_PLOTS"],
        )

    def plot_bba_folder(self):
        if self.loadfolder is None:
            self.display_bba_folder.clear()
            self.display_bba_folder.setPlainText("Please select a folder to plot.")

        good_files = []
        for file in os.listdir(self.loadfolder):
            if file.endswith("-results.mat"):
                good_files.append(os.path.join(self.loadfolder, file))

        load_folder_results = [Results.from_file(file) for file in good_files]

        bba_offsets_folder(
            self.machine,
            load_folder_results,
            self.loadfolder,
            self.machine.config["SAVE_PLOTS"],
        )

    def select_save_location_folder(self):
        folderpath = QFileDialog.getExistingDirectory(
            self, "Select Folder to Save to", self.machine.config["SAVE_LOCATION"]
        )
        self.display_save_loc.setPlainText(folderpath)
        self.savepath = folderpath

    def select_bba_folder(self):
        folderpath = QFileDialog.getExistingDirectory(
            self, "Select Folder to load", self.machine.config["SAVE_LOCATION"]
        )
        self.display_bba_folder.setPlainText(folderpath)
        self.loadfolder = folderpath
        self.load_folder_results = None

    def select_bba_file(self):
        if self.tmp_single_filepath is None:
            self.tmp_single_filepath = self.machine.config["SAVE_LOCATION"]
        filepath = QFileDialog.getOpenFileName(
            self,
            "Select a Results.mat File to load",
            self.tmp_single_filepath,
            "Results MATLAB Files (*-results.mat)",
        )
        self.display_single_bba.setPlainText(filepath[0])
        self.tmp_single_filepath = os.path.dirname(filepath[0])
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
            self.enable_mode_selection()
            self.options = None
            self.display = None
            self.selected = None
            self.selected_toggle = 0
            return

    def enable_mode_selection(self):
        self.button_start.setEnabled(False)
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
            if it.text() in self.selected:
                it.setSelected(True)

    def disable_mode_selection(self):
        self.button_start.setEnabled(True)
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
        if self.ticker.state != "Idle":
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
