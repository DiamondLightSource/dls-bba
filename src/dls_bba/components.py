from __future__ import annotations

import logging as log
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from pytac.element import EpicsElement

from dls_bba.exceptions import BBAComponentException

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
        message = "Neither a quadrupole nor BPM was given."
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
