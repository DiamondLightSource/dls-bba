from __future__ import annotations

import logging as log
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, List

from pytac.element import EpicsElement

from dls_bba.exceptions import ComponentConstructionError, ElementDisabledError

if TYPE_CHECKING:
    from dls_bba.machine import Machine


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
        machine: Machine,
        bpm_name: str,
        quadrupoles_names: list[str],
        corrector_name: str,
        axis: str,
        kick: str,
    ):
        bpm, quadrupoles, corrector = Components.name_to_element(
            machine, bpm_name, quadrupoles_names, corrector_name
        )
        bpm_index = machine.bpms_names.index(bpm_name)

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
    def from_dict(cls, machine: Machine, dct: dict):
        # recreate the object from the dict, with elements and names
        bpm_name = dct["bpm_name"]
        quadrupoles_names = list(dct["quadrupoles_names"])
        corrector_name = dct["corrector_name"]
        axis = dct["axis"]
        kick = dct["kick"]

        return cls.from_name(
            machine,
            bpm_name,
            quadrupoles_names,
            corrector_name,
            axis,
            kick,
        )

    @staticmethod
    def name_to_element(
        machine: Machine,
        bpm_name: str,
        quadrupoles_names: List[str],
        corrector_name: str,
    ):
        bpm = machine.bpms[machine.bpms_names.index(bpm_name)]
        quadrupoles = [
            machine.quads[machine.quads_names.index(quad_name)]
            for quad_name in quadrupoles_names
        ]
        if "-PC-H" in corrector_name:
            corrector = machine.hstrs[machine.hstrs_names.index(corrector_name)]
        else:
            corrector = machine.vstrs[machine.vstrs_names.index(corrector_name)]
        return bpm, quadrupoles, corrector

    def as_dict(self):
        a = {}
        for k, v in asdict(self).items():
            if isinstance(v, str):
                a[k] = v
            if isinstance(v, list) and isinstance(v[0], str):
                a[k] = v
        return a


def get_component_pairs(
    machine: Machine, element_names: str, verify: bool = True
) -> List[List[Components]]:
    """"""
    component_pairs: List[List[Components]] = []

    for element_name in element_names:
        component_pairs.append(construct_component_pair(machine, element_name))

    if verify:
        component_pairs = verify_component_pairing(machine, component_pairs)

    return component_pairs


def construct_component_pair(machine: Machine, element: str) -> List[Components]:
    if element in machine.bpms_names:
        bpm = element
        quads = machine.bpm2quad(bpm)
    elif element in machine.quads_names:
        quad = element
        bpm = machine.quad2bpm(quad)
        quads = [quad]
    else:
        msg = f"Element {element} does not correspond to quadrupole or BPM"
        log.critical(msg)
        raise ComponentConstructionError(msg)
    hor_corr, ver_corr = machine.effective_correctors(bpm)
    horizontal_components = Components.from_name(
        machine, bpm, quads, hor_corr, "x", "x_kick"
    )
    vertical_components = Components.from_name(
        machine, bpm, quads, ver_corr, "y", "y_kick"
    )
    return [horizontal_components, vertical_components]


def verify_component_pairing(
    machine: Machine, component_pairings: List[List[Components]]
) -> List[List[Components]]:
    checked_pairings: List[List[Components]] = []

    for component_pair in component_pairings:
        try:
            check_component(machine, component_pair)
        except ElementDisabledError:
            bpm_name = component_pair[0].bpm_name
            msg = f"BPM {bpm_name} skipped."
            log.warning(msg)
        else:
            checked_pairings.append(component_pair)
    return checked_pairings


def check_component(machine: Machine, component_pair: List[Components]) -> None:
    disabled_fofb_bpm_indices = (
        machine.fofb_disabled_indices["x"] + machine.fofb_disabled_indices["y"]
    )
    horizontal_component = component_pair[0]

    if horizontal_component.bpm_index in machine.disabled_bpm_indices:
        msg = f"Cannot run BBA on disabled BPM: {horizontal_component.bpm_name}"
        log.error(msg)
        raise ElementDisabledError(msg)

    if horizontal_component.bpm_index in disabled_fofb_bpm_indices:
        msg = f"BPM: {horizontal_component.bpm_name} is feedback disabled. Results may be invalid."
        log.warning(msg)
