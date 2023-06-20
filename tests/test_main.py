import os
import subprocess
import sys

import pytest

from dls_bba import __version__
from dls_bba.lattice import Lattice


@pytest.fixture(scope="module")
def lattice_setup():
    lattice = Lattice()
    return lattice


def test_cli_version_module():
    cmd = [sys.executable, "-m", "dls_bba", "-v"]
    assert subprocess.check_output(cmd).decode().strip() == __version__


def test_cli_version():
    cmd = ["dls-bba", "-v"]
    assert subprocess.check_output(cmd).decode().strip() == __version__


def test_gui_version():
    cmd = ["dls-bba-gui", "-v"]
    assert subprocess.check_output(cmd).decode().strip() == __version__


def test_cli_show_bpm_options(lattice_setup):
    lattice = lattice_setup
    full_bpm_list = lattice.bpms_names
    cmd = [sys.executable, "-m", "dls_bba", "-e"]
    assert subprocess.check_output(cmd).decode().strip() == str(full_bpm_list)


def test_cli_show_cell_options(lattice_setup):
    lattice = lattice_setup
    full_bpm_list = lattice.cell_dictionary["01"]
    cmd = [sys.executable, "-m", "dls_bba", "-k", "01"]
    assert subprocess.check_output(cmd).decode().strip() == str(full_bpm_list)


def test_cli_show_cell_options_invalid_cell():
    cmd = [sys.executable, "-m", "dls_bba", "-k", "25"]
    expected_message = "Invalid cell selected. Try cells '00' to '24'"
    assert subprocess.check_output(cmd).decode().strip() == expected_message


def test_cli_algorithm_entry(tmp_path):
    cmd = [sys.executable, "-m", "dls_bba", "-a", "SlowBBA", "-s", tmp_path]
    subprocess.call(cmd)
    foldername = [name for name in os.listdir(tmp_path) if name.startswith("SlowBBA")][
        0
    ]
    assert any(
        file.endswith(".log") for file in os.listdir(os.path.join(tmp_path, foldername))
    )
