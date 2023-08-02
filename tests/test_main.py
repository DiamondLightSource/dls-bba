import ast
import subprocess
import sys
from argparse import Namespace
from unittest import mock

import pytest

from dls_bba import __version__
from dls_bba.__main__ import sort_elements
from dls_bba.machine import Machine

TEST_NAMESPACE = Namespace(wholemachine=False, config_files=None, additional_config=None, psps=False, cell=None, bpm=5, quad=None)


@pytest.fixture(scope="module", autouse=True)
@mock.patch("pytac.lattice.EpicsLattice.get_element_values", return_value=[0])
@mock.patch("dls_bba.machine.Machine._get_effective_corrector", return_value=None)
@mock.patch("dls_bba.machine.Machine.get_enabled_bpms", return_value=[0])
def machine_setup(mock_get_element_values, mock_get_effective_corrector, mock_get_enabled_bpms):
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


@mock.patch("dls_bba.machine.Machine", return_value=machine_setup)
def test_cli_info_valid(mock_machine):
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


@mock.patch("dls_bba.machine.Machine", return_value=machine_setup)
def test_cli_info_invalid(mock_machine):
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


def test_sort_elements():
    assert "SR01C-DI-EBPM-05" in sort_elements(TEST_NAMESPACE)
