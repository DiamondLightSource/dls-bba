import ast
import subprocess
import sys
from argparse import Namespace
from unittest import mock

import pytest

from dls_bba import __version__
from dls_bba.__main__ import main, sort_elements
from dls_bba.machine import Machine

TEST_NAMESPACE_BPM = Namespace(
    wholemachine=False,
    config_files=None,
    additional_config=None,
    psps=False,
    cell=None,
    bpm=5,
    quad=None,
)
TEST_NAMESPACE_BPM_F = Namespace(
    wholemachine=False,
    config_files=None,
    additional_config=None,
    psps=False,
    cell=None,
    bpm=0,
    quad=None,
)
TEST_NAMESPACE_QUAD = Namespace(
    wholemachine=False,
    config_files=None,
    additional_config=None,
    psps=False,
    cell=None,
    bpm=None,
    quad=5,
)
TEST_NAMESPACE_QUAD_F = Namespace(
    wholemachine=False,
    config_files=None,
    additional_config=None,
    psps=False,
    cell=None,
    bpm=None,
    quad=0,
)
TEST_NAMESPACE_CELL = Namespace(
    wholemachine=False,
    config_files=None,
    additional_config=None,
    psps=False,
    cell="01",
    bpm=None,
    quad=None,
)
TEST_NAMESPACE_CELL_F = Namespace(
    wholemachine=False,
    config_files=None,
    additional_config=None,
    psps=False,
    cell="00",
    bpm=None,
    quad=None,
)
TEST_NAMESPACE_WHOLEMACHINE = Namespace(
    wholemachine=True,
    config_files=None,
    additional_config=None,
    psps=False,
    cell=None,
    bpm=None,
    quad=None,
)
TEST_NAMESPACE_PSPS = Namespace(
    wholemachine=False,
    config_files=None,
    additional_config=None,
    psps=True,
    cell=None,
    bpm=None,
    quad=None,
)
TEST_NAMESPACE_INFO_BPM = Namespace(
    command="info",
    wholemachine=False,
    config_files=None,
    additional_config=None,
    psps=False,
    cell=None,
    bpm=5,
    quad=None,
)
TEST_NAMESPACE_RUN_BPM = Namespace(
    command="run",
    algorithm="SimFastBBA",
    save_location="",
    wholemachine=False,
    config_files=None,
    additional_config=None,
    psps=False,
    cell=None,
    bpm=5,
    quad=None,
)
TEST_NAMESPACE_PLOT_BOWTIE = Namespace(
    command="plot",
    save_location="",
    config_files=None,
    additional_config=None,
    quadcenter=True,
    difference=False,
)
TEST_NAMESPACE_PLOT_DIFF = Namespace(
    command="plot",
    save_location="",
    config_files=None,
    additional_config=None,
    difference=True,
    quadcenter=False,
)


@pytest.fixture(scope="module", autouse=True)
@mock.patch("pytac.lattice.EpicsLattice.get_element_values", return_value=[0])
@mock.patch("dls_bba.machine.Machine._get_effective_corrector", return_value=None)
@mock.patch("dls_bba.machine.Machine.get_enabled_bpms", return_value=[0])
def machine_setup(
    mock_get_element_values, mock_get_effective_corrector, mock_get_enabled_bpms
) -> Machine:
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


@mock.patch("dls_bba.machine.Machine", return_value=machine_setup)
def test_sort_elements(mock_machine):
    assert "SR01C-DI-EBPM-05" in sort_elements(TEST_NAMESPACE_BPM)
    assert "SR01A-PC-Q1AD-05" in sort_elements(TEST_NAMESPACE_QUAD)
    assert len(sort_elements(TEST_NAMESPACE_CELL)) == 7
    assert len(sort_elements(TEST_NAMESPACE_WHOLEMACHINE)) == 173
    assert len(sort_elements(TEST_NAMESPACE_PSPS)) == 74


@mock.patch("dls_bba.machine.Machine", return_value=machine_setup)
def test_sort_elements_failure(mock_machine):
    assert not sort_elements(TEST_NAMESPACE_BPM_F)
    assert not sort_elements(TEST_NAMESPACE_QUAD_F)
    assert not sort_elements(TEST_NAMESPACE_CELL_F)


@mock.patch("dls_bba.machine.Machine", return_value=machine_setup)
@mock.patch("dls_bba.__main__.parse_arguments", return_value=TEST_NAMESPACE_INFO_BPM)
def test_main_info(mock_machine, mock_parse_args):
    main()


# TODO: Patching isnt working?
# @mock.patch("dls_bba.cli.cli_entrypoint", return_value=None)
# @mock.patch("dls_bba.__main__.parse_arguments", return_value=TEST_NAMESPACE_RUN_BPM)
# def test_main_run(mock_cli_entrypoint, mock_parse_args):

#     def cli_entrypoint(**kwargs):
#         pass

#     from dls_bba import cli

#     cli.cli_entrypoint = cli_entrypoint

#     main()


# @mock.patch(
#     "dls_bba.__main__.parse_arguments",
#     side_effect=[TEST_NAMESPACE_PLOT_BOWTIE, TEST_NAMESPACE_PLOT_DIFF],
# )
# @mock.patch("dls_bba.plotting.bowtie_plot", return_value=None)
# @mock.patch("dls_bba.plotting.bba_offsets_folder", return_value=None)
# def test_main_plot(mock_bba_offsets, mock_bba_bowtie, mock_parse_args):
#     main()
#     main()
