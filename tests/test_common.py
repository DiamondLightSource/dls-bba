import os
from unittest import mock

from conftest import _get_effective_corrector, get_element_values

from dls_bba.common import apply_golden, setup_folders_and_logger


def test_setup_folders_creates_folder_in_correct_location(tmp_path):
    folder_path = setup_folders_and_logger("METHOD", tmp_path, None)
    assert os.path.isfile(os.path.join(folder_path, "log.log"))


@mock.patch("dls_bba.machine.Machine.restore_origins", return_value=None)
def test_apply_golden_orbit_when_provided_machine(
    mock_restore_origins, machine_setup, tmp_path
):
    machine = machine_setup
    apply_golden(tmp_path, machine)
    assert mock_restore_origins.is_called


@mock.patch("dls_bba.machine.Machine.restore_origins", return_value=None)
@mock.patch(
    "pytac.lattice.EpicsLattice.get_element_values",
    side_effect=get_element_values,
)
@mock.patch(
    "dls_bba.machine.Machine._get_effective_corrector",
    side_effect=_get_effective_corrector,
)
def test_apply_golden_orbit_when_not_provided_machine(
    mock_get_effective_corrector,
    mock_get_element_values,
    mock_restore_origins,
    tmp_path,
):
    apply_golden(tmp_path)
    assert mock_restore_origins.is_called
