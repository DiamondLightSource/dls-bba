import os
import subprocess
import sys

import pytest
from tests.ioc_helper import BBAIoc

from dls_bba import __version__
from dls_bba.machine import Machine


@pytest.fixture(scope="module", autouse=True)
def test_ioc():
    ioc = BBAIoc()
    yield ioc.start_ioc()
    ioc.exit_ioc()


@pytest.fixture(scope="module")
def machine_setup():
    machine = Machine()
    return machine


def test_cli_module_entrypoint_can_provide_version():
    cmd = [sys.executable, "-m", "dls_bba", "-v"]
    assert subprocess.check_output(cmd).decode().strip() == __version__


def test_cli_entrypoint_can_provide_version():
    cmd = ["dls-bba", "-v"]
    assert subprocess.check_output(cmd).decode().strip() == __version__


def test_gui_entrypoint_can_provide_version():
    cmd = ["dls-bba-gui", "-v"]
    assert subprocess.check_output(cmd).decode().strip() == __version__


def test_cli_argument_shows_all_bpm_names(machine_setup):
    machine = machine_setup
    full_bpm_list = machine.bpms_names
    cmd = [sys.executable, "-m", "dls_bba", "info", "-w"]
    assert subprocess.check_output(cmd).decode().strip() == str(full_bpm_list)


def test_cli_argument_shows_full_cell_dictionary(machine_setup):
    machine = machine_setup
    full_bpm_list = machine.cell_dictionary["06"]
    cmd = [sys.executable, "-m", "dls_bba", "info", "-k", "06"]
    assert subprocess.check_output(cmd).decode().strip() == str(full_bpm_list)


def test_cli_argument_fails_when_given_invalid_cell():
    cmd = [sys.executable, "-m", "dls_bba", "info", "-k", "25"]
    expected_message = "Invalid cell selected. Try cells '01' to '24'"

    with pytest.raises(subprocess.CalledProcessError) as err:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)

    assert expected_message in err.value.output.decode()


def test_cli_algorithm_selection_creates_correctly_named_folder(tmp_path):
    cmd = [
        sys.executable,
        "-m",
        "dls_bba",
        "run",
        "-a",
        "SlowBBA",
        "-w",
        "-f",
        tmp_path,
    ]
    subprocess.call(cmd)
    foldername = [name for name in os.listdir(tmp_path) if name.startswith("SlowBBA")][
        0
    ]
    assert any(
        file.endswith(".log") for file in os.listdir(os.path.join(tmp_path, foldername))
    )
