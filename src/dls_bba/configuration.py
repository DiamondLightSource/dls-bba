import sys
from dataclasses import dataclass, field
from json import load
from pathlib import Path
from typing import Any, List, Optional, Union

if sys.version_info > (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files

DEFAULT_CONFIGS = (
    "I04-20230524-settings.json",  # Ring mode settings -> Must be first in list.
    "defaults.json",  # UI defaults.
)

LATTICE_SETTINGS = (  # Requires update to lattice and associated components
    "RINGMODE",
    "UNITS",
    "DATASOURCE",
    "COTHREAD_CONTROL_SYSTEM_TIMEOUT",
    "COTHREAD_CONTROL_SYSTEM_WAIT_FLAG",
    "FOFB_NOGUI_PATH",
    "FEEDBACK_PVS",
    "DIAGNOSTICS",
    "ORBIT_RESPONSE_MATRIX_PATH",
    "CORRECTORS_TXT_PATH",
    "CORRECTOR_IOCS",
    "BPM2QUAD_SPECIAL_CASES",
    "BPM2QUAD_EXCEPTIONS",
    "QUAD2BPM_SPECIAL_CASES",
    "QUAD2BPM_EXCEPTIONS",
    "PSPS",
)


@dataclass
class Configuration:
    config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_configuration_files(cls, paths: Optional[List[Union[Path, str]]] = None):
        config = cls()
        config.apply_default_config()

        if paths is not None:
            config.apply_config_files(paths)

        return config

    def apply_default_config(self):
        default_config_resources = [
            Path(files("dls_bba").joinpath(resource)) for resource in DEFAULT_CONFIGS
        ]
        self.apply_config_files(default_config_resources)

    def update_config(self, new_dictionary: dict) -> bool:
        self.config.update(new_dictionary)
        return any(key in new_dictionary for key in LATTICE_SETTINGS)

    def apply_config_files(self, paths: List[Union[Path, str]]) -> bool:
        reload_lattice = False
        for pth in paths:
            with open(pth) as f:
                reload_flag = self.update_config(load(f))
                if reload_flag:
                    reload_lattice = True
        return reload_lattice
