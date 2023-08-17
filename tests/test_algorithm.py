import os
from typing import Any, Dict, List
from unittest import mock

import pytest
from pytac.exceptions import FieldException

from dls_bba.algorithm import Algorithm
from dls_bba.datatypes import CalculatedOffset, Results
from dls_bba.machine import Machine

TEST_RESULTS_SINGLE: Dict[str, List[float]] = {"x1": [10.0, 2.0], "y1": [5.0, 1.0]}
TEST_PLOTTING_SINGLE: Dict[str, Dict[str, List[float]]] = {
    "Q1": {"x": [1, 2, 3], "y": [6, 5, 4]},
}
TEST_OFFSETS_SINGLE: Dict[str, CalculatedOffset] = {
    "x1": CalculatedOffset(1, 2, 3, 4),
    "y1": CalculatedOffset(9, 8, 7, 6),
}
TEST_RESULTS_DOUBLE: Dict[str, List[float]] = {
    "x1": [10.0, 2.0],
    "x2": [20.0, 2.0],
    "y1": [12.0, 6.0],
    "y2": [9.0, 3.0],
}
TEST_PLOTTING_DOUBLE: Dict[str, Dict[str, List[float]]] = {
    "Q1": {"x": [1, 2, 3], "y": [6, 5, 4]},
    "Q2": {"x": [9, 8, 7], "y": [4, 5, 6]},
}
TEST_OFFSETS_DOUBLE: Dict[str, CalculatedOffset] = {
    "x1": CalculatedOffset(1, 2, 3, 4),
    "y1": CalculatedOffset(9, 8, 7, 6),
    "x2": CalculatedOffset(11, 12, 13, 14),
    "y2": CalculatedOffset(19, 18, 17, 16),
}

TEST_METADATA: Dict[str, Any] = {"bpm_name": "TEST_BPM", "bpm_index": 1}
TEST_RESULTS_INVALID: Dict[str, List[float]] = {"z1": [1.0, 1.0]}
TEST_GET_BBA_OFFSETS: List[float] = [float(0) for _ in range(173)]
TEST_RESULTS: List[Results] = [
    Results(
        TEST_RESULTS_SINGLE, TEST_METADATA, TEST_PLOTTING_SINGLE, TEST_OFFSETS_SINGLE
    ),
    Results(
        TEST_RESULTS_DOUBLE, TEST_METADATA, TEST_PLOTTING_DOUBLE, TEST_OFFSETS_DOUBLE
    ),
]


class TEST_ALG(Algorithm):
    def __init__(self, machine: Machine):
        super().__init__(machine)

    def run(self, component_pair):
        pass

    def analyse(self, rawdata):
        pass


def test_algorithm_init(machine_setup):
    machine = machine_setup
    algorithm = TEST_ALG(machine)
    assert algorithm._machine is machine_setup
    assert algorithm.run
    assert algorithm.analyse


def test_algorithm_failed_init():
    with pytest.raises(TypeError):
        TEST_ALG()


@mock.patch("dls_bba.machine.Machine.get_quad_setpoint", return_value=10)
def test_calculate_quad_setpoints(mock_quad_setpoint, machine_setup):
    machine = machine_setup
    algorithm = TEST_ALG(machine)
    quad = machine.quads[0]
    qsh, qh, ql, qs, step = algorithm.calculate_quad_setpoints(quad)
    assert qh - step == qs
    assert qh + step == qsh
    assert ql + step == qs


def test_calculate_quad_setpoints_invalid_element(machine_setup):
    machine = machine_setup
    algorithm = TEST_ALG(machine)
    bpm = machine.bpms[0]
    with pytest.raises(FieldException):
        algorithm.calculate_quad_setpoints(bpm)


def test_calculate_new_offsets(machine_setup):
    machine = machine_setup
    algorithm = TEST_ALG(machine)
    offsets = algorithm.calculate_new_offsets(TEST_RESULTS_SINGLE, "x")
    assert offsets == TEST_RESULTS_SINGLE["x1"]
    offsets = algorithm.calculate_new_offsets(TEST_RESULTS_SINGLE, "y")
    assert offsets == TEST_RESULTS_SINGLE["y1"]
    offsets = algorithm.calculate_new_offsets(TEST_RESULTS_DOUBLE, "x")
    assert offsets == [15.0, 3.3541019662496847]
    offsets = algorithm.calculate_new_offsets(TEST_RESULTS_DOUBLE, "y")
    assert offsets == [10.5, 6.309714732061981]


def test_calculate_new_offsets_invalid_axis(machine_setup):
    machine = machine_setup
    algorithm = TEST_ALG(machine)
    with pytest.raises(RuntimeWarning):
        algorithm.calculate_new_offsets(TEST_RESULTS_INVALID, "x")


@mock.patch(
    "dls_bba.machine.Machine.get_bba_offsets",
    return_value=(TEST_GET_BBA_OFFSETS, TEST_GET_BBA_OFFSETS),
)
def test_create_offsets_dict(mock_get_bba_offsets, machine_setup):
    machine = machine_setup
    algorithm = TEST_ALG(machine)
    single_offsets = algorithm.create_offsets_dict(TEST_RESULTS_SINGLE, TEST_METADATA)
    for key, value in single_offsets.items():
        assert isinstance(key, str)
        assert isinstance(value, CalculatedOffset)
        assert value.old_value == TEST_GET_BBA_OFFSETS[0]
        assert value.new_value == value.diff_value

    double_offsets = algorithm.create_offsets_dict(TEST_RESULTS_DOUBLE, TEST_METADATA)
    for key, value in double_offsets.items():
        assert isinstance(key, str)
        assert isinstance(value, CalculatedOffset)
        assert value.old_value == TEST_GET_BBA_OFFSETS[0]
        assert value.new_value == value.diff_value


@mock.patch(
    "dls_bba.machine.Machine.get_bba_offsets",
    return_value=(TEST_GET_BBA_OFFSETS, TEST_GET_BBA_OFFSETS),
)
def test_save_bba_offsets(mock_get_bba_offsets, machine_setup, tmp_path):
    machine = machine_setup
    algorithm = TEST_ALG(machine)
    single_offsets = algorithm.create_offsets_dict(TEST_RESULTS_SINGLE, TEST_METADATA)
    algorithm._save_bba_offsets(single_offsets, tmp_path)
    assert os.path.exists(os.path.join(tmp_path, "results.txt"))


@mock.patch(
    "dls_bba.machine.Machine.get_bba_offsets",
    return_value=(TEST_GET_BBA_OFFSETS, TEST_GET_BBA_OFFSETS),
)
@mock.patch("dls_bba.algorithm.caput", return_value=None)
def test_apply_bba_offsets(mock_caput, mock_get_bba_offsets, machine_setup):
    machine = machine_setup
    algorithm = TEST_ALG(machine)
    single_offsets = algorithm.create_offsets_dict(TEST_RESULTS_SINGLE, TEST_METADATA)
    algorithm.apply_bba_offsets(single_offsets)


@mock.patch("dls_bba.algorithm.Algorithm._save_bba_offsets", return_value=None)
@mock.patch("dls_bba.algorithm.Algorithm.apply_bba_offsets", return_value=None)
@mock.patch("dls_bba.machine.Machine.apply_feedbacks", return_value=None)
@mock.patch("dls_bba.machine.Machine._ask_user", side_effect=["y"])
@mock.patch("dls_bba.algorithm.bba_offsets_plot", return_value=None)
def test_use_bba_offsets_yes_pass(
    mock_plot,
    mock_ask_user,
    mock_feedbacks,
    mock_apply,
    mock_save,
    machine_setup,
    tmp_path,
):
    machine = machine_setup
    algorithm = TEST_ALG(machine)
    algorithm.use_bba_offsets(TEST_RESULTS, tmp_path)


@mock.patch("dls_bba.algorithm.Algorithm._save_bba_offsets", return_value=None)
@mock.patch("dls_bba.algorithm.Algorithm.apply_bba_offsets", return_value=None)
@mock.patch("dls_bba.machine.Machine.apply_feedbacks", return_value=None)
@mock.patch("dls_bba.machine.Machine._ask_user", side_effect=["n"])
@mock.patch("dls_bba.algorithm.bba_offsets_plot", return_value=None)
def test_use_bba_offsets_no_pass(
    mock_plot,
    mock_ask_user,
    mock_feedbacks,
    mock_apply,
    mock_save,
    machine_setup,
    tmp_path,
):
    machine = machine_setup
    algorithm = TEST_ALG(machine)
    algorithm.use_bba_offsets(TEST_RESULTS, tmp_path)


@mock.patch("dls_bba.algorithm.Algorithm._save_bba_offsets", return_value=None)
@mock.patch("dls_bba.algorithm.Algorithm.apply_bba_offsets", return_value=None)
@mock.patch("dls_bba.machine.Machine.apply_feedbacks", return_value=None)
@mock.patch("dls_bba.machine.Machine._ask_user", side_effect=["z", "y"])
@mock.patch("dls_bba.algorithm.bba_offsets_plot", return_value=None)
def test_use_bba_offsets_invalid_then_yes_pass(
    mock_plot,
    mock_ask_user,
    mock_feedbacks,
    mock_apply,
    mock_save,
    machine_setup,
    tmp_path,
):
    machine = machine_setup
    algorithm = TEST_ALG(machine)
    algorithm.use_bba_offsets(TEST_RESULTS, tmp_path)


@mock.patch("dls_bba.algorithm.Algorithm._save_bba_offsets", return_value=None)
@mock.patch("dls_bba.algorithm.Algorithm.apply_bba_offsets", return_value=None)
@mock.patch("dls_bba.machine.Machine.apply_feedbacks", return_value=None)
@mock.patch("dls_bba.machine.Machine._ask_user", side_effect=["z", "n"])
@mock.patch("dls_bba.algorithm.bba_offsets_plot", return_value=None)
def test_use_bba_offsets_invalid_then_no_pass(
    mock_plot,
    mock_ask_user,
    mock_feedbacks,
    mock_apply,
    mock_save,
    machine_setup,
    tmp_path,
):
    machine = machine_setup
    algorithm = TEST_ALG(machine)
    algorithm.use_bba_offsets(TEST_RESULTS, tmp_path)
