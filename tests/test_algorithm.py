from unittest import mock

import pytest

from dls_bba.algorithm import Algorithm
from dls_bba.machine import Machine


class TEST_ALG(Algorithm):
    def __init__(self, machine: Machine):
        super().__init__(machine)

    def run(self, component_pair):
        pass

    def analyse(self, rawdata):
        pass


@pytest.fixture(scope="module", autouse=True)
@mock.patch("pytac.lattice.EpicsLattice.get_element_values", return_value=[0])
@mock.patch("dls_bba.machine.Machine._get_effective_corrector", return_value=None)
@mock.patch("dls_bba.machine.Machine.get_enabled_bpms", return_value=[0])
def machine_setup(
    mock_get_element_values, mock_get_effective_corrector, mock_get_enabled_bpms
) -> Machine:
    machine = Machine()
    return machine


@mock.patch("dls_bba.machine.Machine", return_value=machine_setup)
def test_algorithm_init(machine_setup):
    algorithm = TEST_ALG(machine_setup)
    assert algorithm._machine is machine_setup


def test_algorithm_failed_init():
    with pytest.raises(TypeError):
        TEST_ALG()


# @mock.patch("dls_bba.machine.Machine", return_value=machine_setup)
# def test_calculate_setpoints(machine_setup):
#     machine = machine_setup
#     algorithm = TEST_ALG(machine)
#     a, b, c, d, e = algorithm.calculate_quad_setpoints(machine.quads_names[0])
#     print(a, b, c, d, e)
#     assert False


# @mock.patch("dls_bba.machine.Machine", return_value=machine_setup)
# def test_calculate_setpoints_invalid_element(machine_setup):
#     machine = machine_setup
#     algorithm = TEST_ALG(machine)
#     a, b, c, d, e = algorithm.calculate_quad_setpoints(machine.bpms_names[0])
#     print(a, b, c, d, e)
#     assert False
