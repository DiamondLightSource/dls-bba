from typing import Any, Dict, List, Optional
from unittest import mock

import pytest

from dls_bba.machine import Machine

OVERRIDES = {"MIN_CURRENT": 10, "WARNING_CURRENT_DROP": 5}


def get_element_values(family, field, *args, **kwargs) -> List[int]:
    if family == "BPM":
        if field == "x_fofb_disabled":
            return [0 for _ in range(173)]
        elif field == "y_fofb_disabled":
            return [0 for _ in range(173)]
        elif field == "enabled":
            return [1 for _ in range(173)]
    return [1 for _ in range(173)]


@mock.patch.object(Machine, "_get_effective_corrector")
def _get_effective_corrector(self) -> None:
    for bpm_name, hstr_name, vstr_name in zip(
        self.bpms_names, self.hstrs_names, self.vstrs_names
    ):
        self._effective_corrector[bpm_name] = [hstr_name, vstr_name]


@pytest.fixture(scope="session")
@mock.patch(
    "pytac.lattice.EpicsLattice.get_element_values",
    side_effect=get_element_values,
)
@mock.patch(
    "dls_bba.machine.Machine._get_effective_corrector",
    side_effect=_get_effective_corrector,
)
def machine_setup(
    mock_element_values,
    mock_effected_corrector,
    extra_config_files: Optional[List[Any]] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> Machine:
    if overrides is None:
        overrides = {}
    overrides.update(OVERRIDES)
    machine = Machine(extra_config_files, overrides)
    return machine
