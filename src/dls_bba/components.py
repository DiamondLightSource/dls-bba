from __future__ import annotations

import logging as log
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Dict, List, Tuple, Union

from pytac.element import EpicsElement

from dls_bba.exceptions import ComponentConstructionError, ElementDisabledError

if TYPE_CHECKING:
    from dls_bba.machine import Machine


@dataclass
class Components:
    bpm_name: str
    quadrupoles_names: List[str]
    corrector_name: str
    axis: str
    kick: str
    bpm: EpicsElement
    quadrupoles: List[EpicsElement]
    corrector: EpicsElement
    bpm_index: int

    @classmethod
    def from_name(
        cls,
        machine: Machine,
        bpm_name: str,
        quadrupoles_names: List[str],
        corrector_name: str,
        axis: str,
        kick: str,
    ) -> Components:
        """The Components class constructor using the string names of the elements.

        Args:
            machine: The machine object.
            bpm_name: The name of the BPM.
            quadrupoles_names: The names of the quadrupoles.
            corrector_name: The name of the corrector.
            axis: The axis string of the measurement.
            kick: The pytac kick string of the measurement.

        Returns:
            The Components object.
        """
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
    def from_dict(
        cls, machine: Machine, dct: Dict[str, Union[str, List[str]]]
    ) -> Components:
        """The Components class constructor using a dictionary.

        Args:
            machine: The machine object.
            dct: The dictionary containing the names of the elements.

        Returns:
            The Components object.
        """
        bpm_name = str(dct["bpm_name"])
        quadrupoles_names = List(dct["quadrupoles_names"])
        corrector_name = str(dct["corrector_name"])
        axis = str(dct["axis"])
        kick = str(dct["kick"])

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
    ) -> Tuple[EpicsElement, List[EpicsElement], EpicsElement]:
        """Converts the string names of the elements to the pytac elements.

        Args:
            machine: The machine object.
            bpm_name: The name of the BPM.
            quadrupoles_names: The names of the quadrupoles.
            corrector_name: The name of the corrector.

        Returns:
            A tuple containing the pytac elements of the BPM, quadrupoles and corrector.
        """
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

    def as_dict(self) -> Dict[str, Union[str, List[str]]]:
        """Converts the Components object to a dictionary.

        Returns:
            The dictionary containing the names of the elements.
        """
        a: Dict[str, Union[str, List[str]]] = {}
        for k, v in asdict(self).items():
            if isinstance(v, str):
                a[k] = v
            if isinstance(v, List) and isinstance(v[0], str):
                a[k] = v
        return a


def get_component_pairs(
    machine: Machine, element_names: List[str], verify: bool = True
) -> List[List[Components]]:
    """Constructs a list of component pairs from the given elements.

    Args:
        machine: The machine object.
        element_names: The names of the elements.
        verify: Whether to verify the component pairings.

    Returns:
        The list of component pairs.
    """
    component_pairs: List[List[Components]] = []

    for element_name in element_names:
        component_pairs.append(construct_component_pair(machine, element_name))

    if verify:
        component_pairs = verify_component_pairing(machine, component_pairs)

    return component_pairs


def construct_component_pair(machine: Machine, element: str) -> List[Components]:
    """Constructs a component pair from the given element.

    A component pair is the x, y pair of component objects for a single BPM.

    Args:
        machine: The machine object.
        element: The name of the element.

    Returns:
        The component pair.
    """
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
    """Returns valid component pairings given the current machine state.

    Elements that are disabled will be valid upon component object construction, this
    function removes those elements and provides warnings where appropriate.

    Args:
        machine: The machine object.
        component_pairings: The list of component pairings.

    Returns:
        The list of component pairings with disabled elements removed.
    """
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
    """Checks that individual components are not invalid.

    Disabled BPMs cannot perform BBA, and are removed from the lists.
    Feedback disabled BPMs can perform BBA, but the results may be invalid.

    Args:
        machine: The machine object.
        component_pair: The component pair.

    Raises:
        ElementDisabledError: If the component pair uses disabled elements.
    """
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
