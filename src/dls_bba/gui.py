import logging as log
import os
import signal
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

# isort: off
import matplotlib
from cothread.cothread import Callback, _QuitEvent

from dls_bba.datatypes import Results

matplotlib.use("Qt5Agg")  # noqa: E402
# isort: on

import cothread  # noqa: E402
from cothread.catools import FORMAT_CTRL, caget  # noqa: E402
from PyQt6 import QtCore, uic  # noqa: E402
from PyQt6.QtWidgets import (  # noqa: E402
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
)
from pytac.load_csv import available_ringmodes

from dls_bba.common import (  # noqa: E402
    ALGORITHMS,
    apply_folder,
    apply_golden,
    apply_single,
)
from dls_bba.excite import cancel_all_oscillations  # noqa E402
from dls_bba.isotime import get_isotime  # noqa: E402
from dls_bba.machine import DATASOURCE, ORIGIN_SUFFIXES, UNITS, Machine  # noqa: E402
from dls_bba.plotting import bba_offsets_folder, bowtie_plot  # noqa: E402
from dls_bba.worker import Worker  # noqa: E402

if sys.version_info > (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files

UI_FILENAME: List[str] = ["fbba_gui.ui"]
"""The name of the .ui file."""
# DEFAULT_SAVE_LOCATION: str = "/dls/ops-physics/diamonddata/fastBBA"
RAD_TO_URAD_CONV: float = 1e6
"""Conversion value from radians to microradians."""


class Ticker:
    """The Ticker controls how the state changes of the process get returned to the GUI."""

    def __init__(
        self, on_update: Callable[[str, str], None], progress: Callable[[float], None]
    ) -> None:
        """Initialise the Ticker.

        Args:
            on_update: A function that handles state changes.
            progress: A function that handles the progress fraction.
        """
        self.__action = cothread.Event()
        self.__on_update = on_update
        self.__progress = progress
        self.__state = "Idle"
        cothread.Spawn(self.__ticker)

    def __do_tick(self, worker: Worker) -> None:
        """Complete ticks for the duration of the process.

        Args:
            worker: The worker that controls the process.
        """
        self.__set_state("Running")
        worker.start()
        fraction: Union[float, int] = 1
        self.__progress(fraction)

        action = "run"
        while action == "run" and fraction > 0:
            if self.__action:
                action, _ = self.__action.Wait()

            if action == "run":
                fraction = worker.work()
                self.__progress(fraction)
            elif action == "stop":
                self.__set_state("Complete")
                worker.forced_finish()
                self.__set_state("Idle")
            elif action == "pause":
                worker.pause()
                self.__set_state("Paused")
                action, _ = self.__action.Wait()
                worker.resume()
                self.__set_state("Running")

        self.__set_state("Complete")
        worker.finish()
        self.__set_state("Idle")

    def __ticker(self) -> None:
        """The individual ticks for the BBA process."""
        while True:
            action = ""
            while action != "run":
                action, worker = self.__action.Wait()

            try:
                self.__do_tick(worker)
            except Exception:
                traceback.print_exc()
                self.__set_state("Complete")
                worker.forced_finish()
                self.__set_state("Idle")

    def __set_state(self, state: str) -> None:
        """Set the new state."""
        old_state = self.__state
        self.__state = state
        self.__on_update(old_state, state)

    def start_ticker(self, worker: Worker) -> None:
        """Start the ticker."""
        self.__action.Signal(("run", worker))

    def pause_ticker(self) -> None:
        """Pause the ticker."""
        self.__action.Signal(("pause", None))

    def stop_ticker(self) -> None:
        """Stop the ticker."""
        self.__action.Signal(("stop", None))

    def resume_ticker(self) -> None:
        """Resume the ticker."""
        self.__action.Signal(("run", None))

    def pause_resume_ticker(self) -> None:
        """Pause or Resume the ticker."""
        if self.__state == "Running":
            self.pause_ticker()
        elif self.__state == "Paused":
            self.resume_ticker()
        else:
            log.error(f"Don't know what to do with state: {self.__state}")

    @property
    def state(self) -> str:
        """Return the current state of the ticker."""
        return self.__state


class GuiLogger(log.Handler):
    """The GUI Logging Handler."""

    def __init__(self, main_screen: QPlainTextEdit) -> None:
        super().__init__()
        self._main_screen = main_screen

    def emit(self, record: log.LogRecord) -> None:
        """Emit/update the screen with the logging output.

        Args:
            record: The logging record.
        """
        self._main_screen.appendPlainText(self.format(record))


class MainWindow(QMainWindow):
    """The GUI MainWindow."""

    tabWidget: QTabWidget

    # Main page widgets:
    # Method Selection
    method_dropdown: QComboBox
    whole_machine: QPushButton
    cell: QPushButton
    bpms: QPushButton
    quadrupoles: QPushButton
    psps: QPushButton
    pv_selection: QListWidget
    lock_unlock_pv: QPushButton
    # Screen
    main_screen: QPlainTextEdit
    # Button Array
    button_start: QPushButton
    button_pause: QPushButton
    button_stop: QPushButton
    button_reset: QPushButton
    progressBar: QProgressBar
    # Config
    config_use_feedbacks: QCheckBox
    config_use_fofb: QCheckBox
    config_max_orbit: QDoubleSpinBox
    config_current_limit: QDoubleSpinBox
    # Most Recent Data
    button_plot_recent: QPushButton
    button_apply_recent: QPushButton
    display_most_recent: QTextEdit

    # Configuration option widgets:
    # Options
    config_corr_kick: QDoubleSpinBox
    config_quad_step: QDoubleSpinBox
    config_warning_current: QDoubleSpinBox
    config_sofb_run_time: QDoubleSpinBox
    config_run_time: QDoubleSpinBox
    config_wait_time: QDoubleSpinBox
    config_sbba_min_frac: QDoubleSpinBox
    config_sbba_stdev: QDoubleSpinBox
    config_use_decimation: QCheckBox
    config_x_cycles: QSpinBox
    config_x_freq: QSpinBox
    config_y_cycles: QSpinBox
    config_y_freq: QSpinBox
    save_rawdata: QCheckBox
    save_results: QCheckBox
    save_plots: QCheckBox
    config_reselection: QDoubleSpinBox

    # Advanced Options
    config_ringmode: QComboBox
    config_units: QComboBox
    config_datasource: QComboBox
    config_ccs_timeout: QDoubleSpinBox
    config_ccs_wait: QCheckBox
    config_fofb_executable_path: QTextEdit
    config_fofb_max_orbit: QDoubleSpinBox
    config_orm_path: QTextEdit
    config_corrector_txt_path: QTextEdit

    # Save Location and Config
    button_save_loc: QPushButton
    display_save_loc: QTextEdit
    config_load_apply: QPushButton
    display_config_load: QTextEdit
    button_golden: QPushButton
    display_golden: QTextEdit
    button_bba_folder: QPushButton
    display_bba_folder: QTextEdit
    plot_bba: QPushButton
    apply_bba: QPushButton
    button_single_bba: QPushButton
    display_single_bba: QTextEdit
    plot_single_bba: QPushButton
    apply_single_bba: QPushButton

    def __init__(self, *args, **kwargs) -> None:
        """Setup the GUI."""
        super().__init__(*args, **kwargs)
        ui_file = [
            Path(files("dls_bba").joinpath(resource))  # type: ignore
            for resource in UI_FILENAME
        ][0]
        uic.loadUi(ui_file, self)

        self.machine = Machine()
        self.modes: Dict[str, List[Union[List[str], Dict[str, List[str]]]]] = {
            "Whole Machine": [["Whole Machine"], self.machine.bpms_names],
            "Cells": [
                list(self.machine.cell_dictionary.keys()),
                self.machine.cell_dictionary,
            ],
            "BPMs": [self.machine.bpms_names, self.machine.bpms_names],
            "Quadrupoles": [self.machine.quads_names, self.machine.quads_names],
            "PSPs": [["All PSPs"], self.machine.psps],
        }
        self.recent_folder: Optional[str] = None
        self.last_list: Optional[List[str]] = None
        self.selection_strings: Optional[List[str]] = None
        self.selected: Optional[Union[List[str], str]] = None
        self.loadfolder: Optional[str] = None
        self.savepath: Optional[str] = None
        self.loadfile: Optional[str] = None
        self.selected_toggle: int = 0
        self.tmp_single_filepath: Optional[str] = None
        self.setup_main_window()
        self.show_config()
        self.logger = GuiLogger(self.main_screen)
        self.ticker = Ticker(self.ticker_update, self.progress)
        self.reset_progressbar()
        self.tabWidget.setCurrentIndex(0)

        # Mode Selection
        self.options: Optional[Union[Dict[str, List[str]], List[str]]] = None

    def question(self, msg: str) -> bool:
        """Prompt the GUI with a question.

        Args:
            msg: The question to be asked.

        Returns:
            A bool as the answer.
        """
        button = QMessageBox.question(self, "BBA User Prompt", msg)
        return button == QMessageBox.StandardButton.Yes

    def setup_main_window(self) -> None:
        """Setup the mainwindow and the button interactions."""
        # Methods
        self.method_dropdown.addItems(ALGORITHMS.keys())
        self.method_dropdown.setCurrentText(list(ALGORITHMS.keys())[0])
        # Mode
        self.display_on_screen("Please select a mode.", clear=True)

        # Mode Selection
        self.whole_machine.clicked.connect(lambda: self.select_mode("Whole Machine"))
        self.cell.clicked.connect(lambda: self.select_mode("Cells"))
        self.bpms.clicked.connect(lambda: self.select_mode("BPMs"))
        self.quadrupoles.clicked.connect(lambda: self.select_mode("Quadrupoles"))
        self.psps.clicked.connect(lambda: self.select_mode("PSPs"))
        self.lock_unlock_pv.clicked.connect(self.lock_unlock_selection)

        # File / Folder selection, plotting and applying.
        self.config_units.addItems(["Engineering", "Physics"])
        self.config_units.setCurrentText("Engineering")
        self.config_datasource.addItems(DATASOURCE.keys())
        self.config_datasource.setCurrentText(list(DATASOURCE.keys())[0])

        self.button_save_loc.clicked.connect(self.select_save_location_folder)
        self.display_save_loc.setPlainText(self.machine.config["SAVE_LOCATION"])
        self.button_bba_folder.clicked.connect(self.select_bba_folder)
        self.display_bba_folder.setPlainText("Not Selected")
        self.button_single_bba.clicked.connect(self.select_bba_file)
        self.display_single_bba.setPlainText("Not Selected")
        self.plot_bba.clicked.connect(self.plot_bba_folder)
        self.apply_bba.clicked.connect(self.apply_bba_folder)
        self.plot_single_bba.clicked.connect(self.plot_bba_file)
        self.apply_single_bba.clicked.connect(self.apply_bba_file)

        # Front page buttons
        self.button_start.clicked.connect(self.start_ticker)
        self.button_pause.clicked.connect(self.pause_resume_ticker)
        self.button_stop.clicked.connect(self.stop_ticker)
        self.button_reset.clicked.connect(self.reset_iocs)
        self.button_plot_recent.clicked.connect(self.plot_recent)
        self.button_apply_recent.clicked.connect(self.apply_recent)

        # Configuration options
        self.config_use_feedbacks.clicked.connect(self.use_slow_feedbacks)
        self.config_use_fofb.clicked.connect(self.use_fofb)
        self.config_ringmode.addItems(self.get_ringmode_options())
        self.config_load_apply.clicked.connect(self.load_config_file)
        self.button_golden.clicked.connect(self.reapply_golden_orbits)

    def start_ticker(self) -> None:
        """Start Ticker"""
        log.info("GUI Start Pressed")
        if not self.selected:
            self.display_on_screen("No elements selected.")
            return
        self.button_start.setEnabled(False)
        #self.button_pause.setEnabled(True)
        self.button_pause.setText("Pause")
        #self.button_stop.setEnabled(True)
        self.lock_unlock_pv.setEnabled(False)
        self.ticker.start_ticker(self.create_worker())

    def pause_resume_ticker(self) -> None:
        """Pause / Resume Ticker."""
        log.info("GUI Pause/Resume Pressed")
        self.ticker.pause_resume_ticker()
        log.debug(f"State: {self.ticker.state}")
        if self.ticker.state == "Running":
            self.button_pause.setText("Resume")
        elif self.ticker.state == "Paused":
            self.button_pause.setText("Pause")

    def stop_ticker(self, manual_stop=None) -> None:
        """Stop Ticker."""
        log.info(f"ms {manual_stop}")
        if manual_stop:
            log.info("GUI Stop Pressed")
        self.ticker.stop_ticker()
        self.button_pause.setEnabled(False)
        self.button_pause.setText("Pause")
        self.button_stop.setEnabled(False)
        self.lock_unlock_pv.setEnabled(True)

        directory = self.machine.config["SAVE_LOCATION"]
        newest_folder: str = max(
            [os.path.join(directory, d) for d in os.listdir(directory)],
            key=os.path.getmtime,
        )
        self.display_most_recent.setText(newest_folder)
        self.recent_folder = newest_folder
        self.reselect_elements()

    def reselect_elements(self) -> None:
        """Reselect any elements that have a change in offset larger than the limit."""
        reselect_limit = self.machine.config["RESELECTION_LIMIT"]

        good_files = []
        assert isinstance(self.recent_folder, str)
        for file in os.listdir(self.recent_folder):
            if file.endswith("-results.mat"):
                good_files.append(os.path.join(self.recent_folder, file))

        load_folder_results = [Results.from_file(file) for file in good_files]
        reselect = []
        for result in load_folder_results:
            bpm_name = result.metadata["bpm_name"].replace("-", "_")
            x_key = str(
                bpm_name + ORIGIN_SUFFIXES["BBA"].format(axis="X").replace(":", "__")
            )
            y_key = str(
                bpm_name + ORIGIN_SUFFIXES["BBA"].format(axis="Y").replace(":", "__")
            )
            if (
                abs(result.offsets[x_key].diff_value) >= reselect_limit
                or abs(result.offsets[y_key].diff_value) >= reselect_limit
            ):
                reselect.append(bpm_name)

        self.display_on_screen(
            f"Reselected {len(reselect)} elements with > {reselect_limit}um change."
        )
        self.pv_selection.clear()
        self.pv_selection.addItems(reselect)
        self.last_list = reselect
        self.selection_strings = reselect
        self.selected = reselect

    def ticker_update(self, old_state: str, new_state: str) -> None:
        """Update the ticker and handle when the process is finished.

        Args:
            old_state: The old state string.
            new_state:  The new state string.
        """
        log.debug(f"Ticker state: {old_state} => {new_state}")

        if old_state == "Complete" and new_state == "Idle":
            self.stop_ticker(False)

    def progress(self, fraction_left: float) -> None:
        """Update the progress bar.

        Args:
            fraction_left: The fraction left of the run.
        """
        percent_completed = (1 - fraction_left) * 100
        log.info(f"Percent Completed: {percent_completed}%")
        self.progressBar.setValue(round(percent_completed))  # type: ignore

    def reset_progressbar(self) -> None:
        """Reset the progressbar to 0."""
        self.progressBar.setValue(0)

    def create_worker(self) -> Worker:
        """Create the worker to perform BBA.

        Returns:
            An initialised Worker.
        """
        method = self.method_dropdown.currentText()
        if isinstance(self.selected, str):
            self.selected = [self.selected]
        assert isinstance(self.selected, list) and isinstance(self.selected[0], str)
        return Worker(
            method,
            self.selected,
            self.question,
            machine=self.machine,
            folder_path=self.machine.config["SAVE_LOCATION"],
            logger=self.logger,
            additional_options=self.get_config_from_gui(),
        )

    def reset_iocs(self) -> None:
        """Reset all Corrector IOCS."""
        cancel_all_oscillations(self.machine.config)

    def use_slow_feedbacks(self) -> None:
        """Maintain valid configuration between both feedback buttons."""
        if self.config_use_feedbacks.isChecked:
            self.config_use_fofb.setChecked(False)

    def use_fofb(self) -> None:
        """Maintain valid configuration between both feedback buttons."""
        self.config_use_feedbacks.setChecked(True)

    def plot_recent(self) -> None:
        """Plot the recent data."""
        if self.recent_folder is None:
            self.display_most_recent.clear()
            self.display_most_recent.setText("Cannot plot recent until BBA has run.")
            return

        bba_offsets_folder(
            self.machine,
            self.recent_folder,
            self.machine.config["SAVE_PLOTS"],
        )

    def apply_recent(self) -> None:
        """Apply the recent data."""
        if self.recent_folder is None:
            self.display_most_recent.clear()
            self.display_most_recent.setText("Cannot apply recent until BBA has run.")
            return

        apply_folder(self.recent_folder, self.machine)

    def reapply_golden_orbits(self) -> None:
        """Reapply the golden orbits from the provided file."""
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
        apply_golden(file[0], self.machine)
        self.display_golden.setText(f"Golden Orbits restored at {get_isotime()}")

    def load_config_file(self) -> None:
        """Load and apply the config file to the GUI."""
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
        self.machine.update_config(extra_config_files=list_file)
        self.show_config()
        # Allow for lattice reload.
        cothread.Yield()  # TODO: Why does this need to yield?
        self.display_config_load.setText(f"Config File Applied at {get_isotime()}")

    def get_ringmode_options(self) -> List[str]:
        """Get the current ringmode options from the machine.

        Returns:
            A list of the current ringmodes.
        """
        file_ringmodes = available_ringmodes()
        pv_ringmodes = set(caget("SR-CS-RING-01:MODE", format=FORMAT_CTRL).enums)
        return file_ringmodes & pv_ringmodes

    def get_config_from_gui(self) -> Dict[str, Any]:
        """Get the current config in the GUI.

        Returns:
            A dictionary of the new config.
        """
        config_override_dict = {
            "SAVE_LOCATION": self.display_save_loc.toPlainText(),
            "USE_FEEDBACKS": self.config_use_feedbacks.isChecked(),
            "FOFB_FEEDBACKS": self.config_use_fofb.isChecked(),
            "MAX_ORBIT_CORRECTION_MICRONS": self.config_max_orbit.value(),
            "MIN_CURRENT": self.config_current_limit.value(),
            "CORRECTOR_KICK_RADIANS": self.config_corr_kick.value() / RAD_TO_URAD_CONV,
            "QUADRUPOLE_STEP_PERCENT": self.config_quad_step.value(),
            "WARNING_CURRENT_DROP": self.config_warning_current.value(),
            "FEEDBACK_WAIT_TIME": self.config_wait_time.value(),
            "FEEDBACK_RUN_TIME": self.config_run_time.value(),
            "SOFB_RUN_TIME": self.config_sofb_run_time.value(),
            "MIN_SLOPE_FRACTION": self.config_sbba_min_frac.value(),
            "CENTER_OUTLIER_FACTOR": self.config_sbba_stdev.value(),
            "OUTLIER_FACTOR": self.config_sbba_stdev.value(),
            "DECIMATED": self.config_use_decimation.isChecked(),
            "X_CYCLES": self.config_x_cycles.value(),
            "X_FREQUENCY": self.config_x_freq.value(),
            "Y_CYCLES": self.config_y_cycles.value(),
            "Y_FREQUENCY": self.config_y_freq.value(),
            "SAVE_RAWDATA": self.save_rawdata.isChecked(),
            "SAVE_RESULTS": self.save_results.isChecked(),
            "SAVE_PLOTS": self.save_plots.isChecked(),
            "RESELECTION_LIMIT": self.config_reselection.value(),
            "RINGMODE": self.config_ringmode.currentText(),
            "UNITS": self.config_units.currentText().lower(),
            "DATASOURCE": self.config_datasource.currentText(),
            "COTHREAD_CONTROL_SYSTEM_TIMEOUT": self.config_ccs_timeout.value(),
            "COTHREAD_CONTROL_SYSTEM_WAIT_FLAG": self.config_ccs_wait.isChecked(),
            "FOFB_EXECUTABLE_PATH": self.config_fofb_executable_path.toPlainText(),
            "FOFB_MAX_ORBIT_MICRONS": self.config_fofb_max_orbit.value(),
            "ORBIT_RESPONSE_MATRIX_PATH": self.config_orm_path.toPlainText(),
            "CORRECTORS_TXT_PATH": self.config_corrector_txt_path.toPlainText(),
        }
        return config_override_dict

    def update_config(self) -> None:
        """Update the machine config with the current config in the GUI.
        """
        config_override_dict = self.get_config_from_gui()
        self.machine.update_config(config_override_dict=config_override_dict)
        self.show_config()
        cothread.Yield()

    def show_config(self) -> None:
        """Load the config from the config object to the GUI."""
        config = self.machine.config

        self.config_use_feedbacks.setChecked(config["USE_FEEDBACKS"])
        self.config_use_fofb.setChecked(config["FOFB_FEEDBACKS"])
        self.config_max_orbit.setValue(config["MAX_ORBIT_CORRECTION_MICRONS"])
        self.config_current_limit.setValue(config["MIN_CURRENT"])

        self.config_corr_kick.setValue(
            config["CORRECTOR_KICK_RADIANS"] * RAD_TO_URAD_CONV
        )
        self.config_quad_step.setValue(config["QUADRUPOLE_STEP_PERCENT"])
        self.config_warning_current.setValue(config["WARNING_CURRENT_DROP"])
        self.config_wait_time.setValue(config["FEEDBACK_WAIT_TIME"])
        self.config_run_time.setValue(config["FEEDBACK_RUN_TIME"])
        self.config_sofb_run_time.setValue(config["SOFB_RUN_TIME"])
        self.config_sbba_min_frac.setValue(config["MIN_SLOPE_FRACTION"])
        self.config_sbba_stdev.setValue(config["CENTER_OUTLIER_FACTOR"])
        self.config_sbba_stdev.setValue(config["OUTLIER_FACTOR"])
        self.config_use_decimation.setChecked(config["DECIMATED"])
        self.config_x_cycles.setValue(config["X_CYCLES"])
        self.config_x_freq.setValue(config["X_FREQUENCY"])
        self.config_y_cycles.setValue(config["Y_CYCLES"])
        self.config_y_freq.setValue(config["Y_FREQUENCY"])
        self.save_rawdata.setChecked(config["SAVE_RAWDATA"])
        self.save_results.setChecked(config["SAVE_RESULTS"])
        self.save_plots.setChecked(config["SAVE_PLOTS"])
        self.config_reselection.setValue(config["RESELECTION_LIMIT"])

        self.config_ringmode.setCurrentText(config["RINGMODE"])
        self.config_units.setCurrentText(UNITS[config["UNITS"].lower()].capitalize())
        self.config_datasource.setCurrentText(config["DATASOURCE"])
        self.config_ccs_timeout.setValue(config["COTHREAD_CONTROL_SYSTEM_TIMEOUT"])
        self.config_ccs_wait.setChecked(config["COTHREAD_CONTROL_SYSTEM_WAIT_FLAG"])
        self.config_fofb_executable_path.setText(config["FOFB_EXECUTABLE_PATH"])
        self.config_fofb_max_orbit.setValue(config["FOFB_MAX_ORBIT_MICRONS"])
        self.config_orm_path.setText(config["ORBIT_RESPONSE_MATRIX_PATH"])
        self.config_corrector_txt_path.setText(config["CORRECTORS_TXT_PATH"])

        self.display_save_loc.setPlainText(config["SAVE_LOCATION"])

    def apply_bba_folder(self) -> None:
        """Apply all results files in the given folder."""
        if self.loadfolder is None:
            self.display_bba_folder.clear()
            self.display_bba_folder.setPlainText("Please select a folder to apply.")
            return

        apply_folder(self.loadfolder, self.machine)

    def apply_bba_file(self) -> None:
        """Apply the individual BBA results file selected."""
        if self.loadfile is None:
            self.display_single_bba.clear()
            self.display_single_bba.setPlainText("Please select a file to apply.")
            return

        apply_single(self.loadfile, self.machine)

    def plot_bba_file(self) -> None:
        """Plot the individual BBA results file selected."""
        if self.loadfile is None:
            self.display_single_bba.clear()
            self.display_single_bba.setPlainText("Please select a file to plot.")
            return

        bowtie_plot(
            self.loadfile,
            self.machine.config["SAVE_PLOTS"],
        )

    def plot_bba_folder(self) -> None:
        """Plot all results files in the given folder."""
        if self.loadfolder is None:
            self.display_bba_folder.clear()
            self.display_bba_folder.setPlainText("Please select a folder to plot.")
            return

        bba_offsets_folder(
            self.machine,
            self.loadfolder,
            self.machine.config["SAVE_PLOTS"],
        )

    def select_save_location_folder(self) -> None:
        """Select the save location."""
        folderpath = QFileDialog.getExistingDirectory(
            self, "Select Folder to Save to", self.machine.config["SAVE_LOCATION"]
        )
        if folderpath == "":
            self.display_save_loc.clear()
            self.display_save_loc.setPlainText(self.machine.config["SAVE_LOCATION"])
        else:
            self.display_save_loc.setPlainText(folderpath)
            self.savepath = folderpath

    def select_bba_folder(self) -> None:
        """Select a folder of old data to load."""
        folderpath = QFileDialog.getExistingDirectory(
            self, "Select Folder to load", self.machine.config["SAVE_LOCATION"]
        )
        if folderpath == "":
            self.display_bba_folder.clear()
            self.display_bba_folder.setPlainText("No folder selected.")
            return
        self.display_bba_folder.setPlainText(folderpath)
        self.loadfolder = folderpath

    def select_bba_file(self) -> None:
        """Select an individual results file to load."""
        if self.tmp_single_filepath is None:
            self.tmp_single_filepath = self.machine.config["SAVE_LOCATION"]
        filepath = QFileDialog.getOpenFileName(
            self,
            "Select a Results.mat File to load",
            self.tmp_single_filepath,
            "Results MATLAB Files (*-results.mat)",
        )
        if filepath[0] == "":
            self.display_single_bba.clear()
            self.display_single_bba.setPlainText("No folder selected.")
            return
        self.display_single_bba.setPlainText(filepath[0])
        self.tmp_single_filepath = os.path.dirname(filepath[0])
        self.loadfile = filepath[0]

    def select_mode(self, key):
        """Display the correct PV options for the mode selected."""
        values = self.modes[key]
        selection_strings, options = values[0], values[1]
        # Clear and redraw selection
        self.pv_selection.clear()
        self.pv_selection.addItems(selection_strings)
        self.last_list = selection_strings
        self.selection_strings = selection_strings
        self.options = options

    def lock_unlock_selection(self) -> None:
        """Toggle locking and unlocking the PV selection."""
        if self.selected_toggle == 0:
            if self.select_options():
                self.disable_mode_selection()
                self.selected_toggle = 1
                return

        if self.selected_toggle == 1:
            self.enable_mode_selection()
            self.options = None
            self.selected = None
            self.selected_toggle = 0
            return

    def enable_mode_selection(self):
        """Enable selection of options."""
        self.button_start.setEnabled(False)
        self.whole_machine.setEnabled(True)
        self.cell.setEnabled(True)
        self.bpms.setEnabled(True)
        self.quadrupoles.setEnabled(True)
        self.psps.setEnabled(True)
        self.lock_unlock_pv.setText("Select")
        self.display_on_screen("Please select a mode", True)
        self.reset_progressbar()
        # Set the list to full previously selected list.
        self.pv_selection.clear()
        self.pv_selection.addItems(self.last_list)
        for i in range(self.pv_selection.count()):
            it = self.pv_selection.item(i)
            it.setFlags(it.flags() | QtCore.Qt.ItemFlag.ItemIsEnabled)
            if it.text() in self.selected:
                it.setSelected(True)

    def disable_mode_selection(self):
        """Disable selection of options."""
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
        """Select options and find the correct element names where needed.

        Returns:
            True if elements are selected, False if nothing selected.
        """
        selected = self.pv_selection.selectedItems()  # type: ignore
        assert isinstance(self.selection_strings, list)
        if len(selected) == 0:
            self.display_on_screen("Please select a mode.", clear=True)
            self.selected = None
            return False

        elif len(selected) == 1 and any(
            True for x in ["Whole Machine", "All PSPs"] if x in self.selection_strings
        ):
            self.display_on_screen(f"{self.selection_strings[0]} selected.", clear=True)
            assert isinstance(self.options, list) and isinstance(self.options[0], str)
            self.selected = self.options
            return True

        elif len(selected) == 1 and not any(
            True for x in ["Whole Machine", "All PSPs"] if x in self.selection_strings
        ):
            if len(selected[0].text()) == 2:
                cell_number = selected[0].text()
                elements = self.machine.cell_dictionary[cell_number]
                self.display_on_screen(f"Cell {cell_number} selected.", clear=True)
                self.selected = elements
                return True

            else:
                element = selected[0].text()
                self.display_on_screen(f"{element} selected.", clear=True)
                self.selected = element
                return True

        else:
            if len(selected[0].text()) == 2:
                cells = [element.text() for element in selected]
                elements = []
                for cell in cells:
                    elements.extend(self.machine.cell_dictionary[cell])
                self.display_on_screen(f"Cells {cells} selected.", clear=True)
                self.selected = elements
                return True

            else:
                elements = [element.text() for element in selected]
                self.display_on_screen(
                    f"{len(elements)} elements selected.", clear=True
                )
                self.selected = elements
                return True

    def display_on_screen(self, text: str, clear=False) -> None:
        """Display a message on the GUI Screen.

        Args:
            text: The message to display
            clear: If to clear the screen beforehand.
        """
        if clear:
            self.main_screen.clear()
            QApplication.processEvents()
        self.main_screen.appendPlainText(text)
        QApplication.processEvents()

    def closeEvent(self, event=None) -> None:
        """Signal the close event."""
        if self.ticker.state != "Idle":
            log.critical("Force Closed.")
            cancel_all_oscillations(self.machine.config)
            log.critical("Golden Orbit not reapplied to BPMs. Please reapply.")
        else:
            log.info("Closed Gracefully.")
        log.info("Exited.")


def start_gui() -> None:
    """Start the GUI."""
    _qapp = cothread.iqt()  # noqa
    window = MainWindow()
    window.show()
    # cothread.WaitForQuit()

    def graceful_exit() -> None:
        """When closed, trigger a close event."""
        window.closeEvent()
        _QuitEvent.Signal()

    signal.signal(signal.SIGINT, lambda signum, frame: Callback(graceful_exit))
    _QuitEvent.Wait()
