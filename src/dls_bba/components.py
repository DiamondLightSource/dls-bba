from __future__ import annotations

import logging as log
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING
import numpy as np

from pytac.element import EpicsElement

from dls_bba.exceptions import BBAComponentException, DisabledBPMException

if TYPE_CHECKING:
    from dls_bba.lattice import Lattice


@dataclass
class Components:
    bpm_name: str
    quadrupoles_names: list[str]
    corrector_name: str
    axis: str
    kick: str
    bpm: EpicsElement
    quadrupoles: list[EpicsElement]
    corrector: EpicsElement
    bpm_index: int

    @classmethod
    def from_name(
        cls,
        lattice: Lattice,
        bpm_name: str,
        quadrupoles_names: list[str],
        corrector_name: str,
        axis: str,
        kick: str,
    ):
        bpm, quadrupoles, corrector = Components.name_to_element(
            lattice, bpm_name, quadrupoles_names, corrector_name
        )
        bpm_index = lattice.bpms_names.index(bpm_name)

        return cls(
            bpm_name,
            quadrupoles_names,
            corrector_name,
            axis,
            kick,
            bpm,
            quadrupoles,
            corrector,
            bpm_index,
        )

    @classmethod
    def from_dict(cls, lattice: Lattice, dct: dict):
        # recreate the object from the dict, with elements and names
        bpm_name = dct["bpm_name"]
        quadrupoles_names = list(dct["quadrupoles_names"])
        corrector_name = dct["corrector_name"]
        axis = dct["axis"]
        kick = dct["kick"]

        return cls.from_name(
            lattice,
            bpm_name,
            quadrupoles_names,
            corrector_name,
            axis,
            kick,
        )

    @staticmethod
    def name_to_element(
        lattice: Lattice,
        bpm_name: str,
        quadrupoles_names: list[str],
        corrector_name: str,
    ):
        bpm = lattice.bpms[lattice.bpms_names.index(bpm_name)]
        quadrupoles = [
            lattice.quads[lattice.quads_names.index(quad_name)]
            for quad_name in quadrupoles_names
        ]
        if "-PC-H" in corrector_name:
            corrector = lattice.hstrs[lattice.hstrs_names.index(corrector_name)]
        else:
            corrector = lattice.vstrs[lattice.vstrs_names.index(corrector_name)]
        return bpm, quadrupoles, corrector

    def as_dict(self):
        a = {}
        for k, v in asdict(self).items():
            if isinstance(v, str):
                a[k] = v
            if isinstance(v, list) and isinstance(v[0], str):
                a[k] = v
        return a


def generate_component_pairings(
    lattice: Lattice, element_name: str
) -> list[Components]:
    """Can accept either bpm or quad name."""
    if element_name in lattice.bpms_names:
        bpm = element_name
        quads = lattice.bpm2quad(bpm)
    elif element_name in lattice.quads_names:
        quad = element_name
        bpm = lattice.quad2bpm(quad)
        quads = [quad]
    else:
        message = f"Element {element_name} does not correspond to quadrupole or BPM"
        log.critical(message)
        raise BBAComponentException(message)

    hor_corr, ver_corr = lattice.effective_correctors(bpm)
    horizontal_components = Components.from_name(
        lattice, bpm, quads, hor_corr, "x", "x_kick"
    )
    vertical_components = Components.from_name(
        lattice, bpm, quads, ver_corr, "y", "y_kick"
    )
    return [horizontal_components, vertical_components]


def verify_component_pairing(
    lattice: Lattice, component_pairings: list[list[Components]]
) -> list[list[Components]]:
    checked_pairings = []

    disabled_bpms_indices = np.nonzero(np.logical_not(lattice.get_enabled_bpms()))[
        0
    ].tolist()
    disabled_fofb_bpm_indices_x = np.nonzero(lattice.fofb_disabled["x"])[0].tolist()
    disabled_fofb_bpm_indices_y = np.nonzero(lattice.fofb_disabled["y"])[0].tolist()
    disabled_fofb_indices = disabled_fofb_bpm_indices_x + disabled_fofb_bpm_indices_y

    for component_pair in component_pairings:
        try:
            check_component(
                component_pair, disabled_bpms_indices, disabled_fofb_indices
            )
        except DisabledBPMException:
            bpm_name = component_pair[0].bpm_name
            msg = f"BPM {bpm_name} skipped."
            log.warning(msg)
        else:
            checked_pairings.append(component_pair)
    return checked_pairings


def check_component(
    component_pair: list[Components],
    disabled_bpm_indices: list[int],
    disabled_fofb_bpm_indices: list[int],
):
    horizontal_component = component_pair[0]

    if horizontal_component.bpm_index in disabled_bpm_indices:
        msg = f"Cannot run BBA on disabled BPM: {horizontal_component.bpm_name}"
        log.error(msg)
        raise DisabledBPMException(msg)

    if horizontal_component.bpm_index in disabled_fofb_bpm_indices:
        msg = f"BPM: {horizontal_component.bpm_name} is feedback disabled. Results may be invalid."
        log.warning(msg)
