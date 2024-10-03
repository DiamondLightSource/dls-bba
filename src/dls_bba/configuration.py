from __future__ import annotations

import sys
from copy import deepcopy
from json import load
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

if sys.version_info > (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files

DEFAULT_CONFIGS: Tuple[str, str] = (
    "I04-sim-settings.json",
    "defaults.json",
)
"""The default configuration files."""

LATTICE_SETTINGS: Tuple[str, ...] = (
    "RINGMODE",
    "UNITS",
    "DATASOURCE",
    "COTHREAD_CONTROL_SYSTEM_TIMEOUT",
    "COTHREAD_CONTROL_SYSTEM_WAIT_FLAG",
    "FOFB_EXECUTABLE_PATH",
    "FOFB_MAX_ORBIT_MICRONS",
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
"""The settings that require a lattice reload."""


class Configuration:
    """The Configuration class."""

    def __init__(self) -> None:
        """Initialise the Configuration class."""
        self._config: Dict[str, Any] = {}

    def __getitem__(self, key: str) -> Any:
        """Get an item from the configuration object.

        Args:
            key: The key to get from the configuration object.

        Returns:
            The value of the key.
        """
        return self._config[key]

    @classmethod
    def from_configuration_files(
        cls, paths: Optional[Union[List[Path], List[str]]] = None
    ) -> Configuration:
        """Construct a Configuration object using given config .json filepaths."""
        config = cls()
        config.apply_default_config()

        if paths is not None:
            config.apply_config_files(paths)

        return config

    def apply_default_config(self) -> None:
        """Apply the default configuration files."""
        default_config_resources = [
            Path(str(files("dls_bba").joinpath(resource)))
            for resource in DEFAULT_CONFIGS
        ]
        self.apply_config_files(default_config_resources)

    def update_config(self, new_dictionary: Dict[str, Any]) -> bool:
        """Update the configuration object with fields from the given dictionary.

        Args:
            new_dictionary: The dictionary to update the configuration object with.

        Returns:
            True if any of the keys in the given dictionary are in LATTICE_SETTINGS, False otherwise.
        """
        self._config.update(new_dictionary)
        return any(key in new_dictionary for key in LATTICE_SETTINGS)

    def apply_config_files(self, paths: Union[List[Path], List[str]]) -> bool:
        """Apply the configuration files at the given paths.

        Args:
            paths: The paths to the configuration files.

        Returns:
            True if any of the keys in the given dictionary are in LATTICE_SETTINGS, False otherwise.
        """
        reload_lattice = False
        for pth in paths:
            with open(pth) as f:
                reload_flag = self.update_config(load(f))
                if reload_flag:
                    reload_lattice = True
        return reload_lattice

    def get_settings(self) -> Dict[str, Any]:
        """Copy the configuration object.

        Returns:
            A copy of the configuration object.
        """
        return deepcopy(self._config)
