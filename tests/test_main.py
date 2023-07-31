import subprocess
import sys
import ast
from unittest import mock
import pytest

from dls_bba import __version__
from dls_bba.machine import Machine


@pytest.fixture(scope="module")
def machine_setup():
    machine = Machine()
    return machine


def test_cli_can_provide_version_as_module():
    cmd = [sys.executable, "-m", "dls_bba", "-v"]
    assert subprocess.check_output(cmd).decode().strip() == __version__


def test_cli_can_provide_version():
    cmd = ["dls-bba", "-v"]
    assert subprocess.check_output(cmd).decode().strip() == __version__


def test_gui_can_provide_version():
    cmd = ["dls-bba-gui", "-v"]
    assert subprocess.check_output(cmd).decode().strip() == __version__


def test_cli_info_valid():
    cmd = ["dls-bba", "info", "-w"]
    assert len(ast.literal_eval(subprocess.check_output(cmd).decode().strip())) == 173
    cmd = ["dls-bba", "info", "-p"]
    assert len(ast.literal_eval(subprocess.check_output(cmd).decode().strip())) == 74
    cmd = ["dls-bba", "info", "-k", "01"]
    assert len(ast.literal_eval(subprocess.check_output(cmd).decode().strip())) == 7
    cmd = ["dls-bba", "info", "-b", "5"]
    assert "SR01C-DI-EBPM-05" in subprocess.check_output(cmd).decode().strip()
    cmd = ["dls-bba", "info", "-q", "5"]
    assert "SR01A-PC-Q1AD-05" in subprocess.check_output(cmd).decode().strip()


def test_cli_info_invalid():
    cmd = ["dls-bba", "info", "-k", "00"]
    assert "Invalid cell selected" in subprocess.check_output(cmd).decode().strip()
    cmd = ["dls-bba", "info", "-k", "25"]
    assert "Invalid cell selected" in subprocess.check_output(cmd).decode().strip()
    cmd = ["dls-bba", "info", "-b", "0"]
    assert "Invalid BPM selected" in subprocess.check_output(cmd).decode().strip()
    cmd = ["dls-bba", "info", "-b", "174"]
    assert "Invalid BPM selected" in subprocess.check_output(cmd).decode().strip()
    cmd = ["dls-bba", "info", "-q", "0"]
    assert "Invalid Quad selected" in subprocess.check_output(cmd).decode().strip()
    cmd = ["dls-bba", "info", "-q", "249"]
    assert "Invalid Quad selected" in subprocess.check_output(cmd).decode().strip()


def test_cli_elements_are_mutually_exclusive():
    pass


@mock.patch("Worker", return_value=None)
@mock.patch("run_worker", return_value=None)
def test_run(mock_worker, mock_run_worker):
    pass


# def test_cli_algorithm_selection_creates_correctly_named_folder(tmp_path):
#     cmd = [sys.executable, "-m", "dls_bba", "-a", "SlowBBA", "-s", tmp_path]
#     subprocess.call(cmd)
#     foldername = [name for name in os.listdir(tmp_path) if name.startswith("SlowBBA")][
#         0
#     ]
#     assert any(
#         file.endswith(".log") for file in os.listdir(os.path.join(tmp_path, foldername))
#     )
