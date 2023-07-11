from __future__ import annotations

import logging as log
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Dict, List, Tuple, Union

import numpy as np
import pytac

from dls_bba.exceptions import ComponentConstructionError, ElementDisabledError

if TYPE_CHECKING:
    from dls_bba.machine import Machine


@dataclass
class Components:
    """The components class stores both the names and EpicsElements for the
    paired components, including additional information such as the axis, kick
    and indices.
    """

    bpm_name: str
    quadrupoles_names: List[str]
    corrector_name: str
    axis: str
    kick: str
    bpm: pytac.element.EpicsElement
    quadrupoles: List[pytac.element.EpicsElement]
    corrector: pytac.element.EpicsElement
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
        """Components constructor using the names of the components.

        Args:
            machine: The Machine object for the accelerator.
            bpm_name: The name of the BPM required.
            quadrupoles_names: The names of quadrupoles required in a list.
            corrector_name: The name of the corrector required.
            axis: The axis of interest. eg. 'x' or 'y'
            kick: The corrector kick of interest. eg. 'x_kick' or 'y_kick'

        Returns:
            The constructed Components object.
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
    def from_dict(cls, machine: Machine, dct: Dict) -> Components:
        """Components constructor using a dictionary.

        Args:
            machine: The Machine object for the accelerator.
            dct: A dictionary that contains information for construction.

        Returns:
            The constructed Components object.
        """
        bpm_name = dct["bpm_name"]
        quadrupoles_names = List(dct["quadrupoles_names"])
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
    ) -> Tuple[
        pytac.element.EpicsElement,
        List[pytac.element.EpicsElement],
        pytac.element.EpicsElement,
    ]:
        """A function that converts component names to EpicsElements.

        Args:
            machine: The Machine object for the accelerator.
            bpm_name: The name of the BPM required.
            quadrupoles_names: The names of quadrupoles required in a list.
            corrector_name: The name of the corrector required.

        Returns:
            The EpicsElement object for the BPM.
            A list of EpicsElements for the quadrupoles.
            The EpicsElement object for the corrector.
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
        """A function that converts the component names into a dictionary.

        This will only store attributes that are str or List[str].

        Returns:
            A dictionary of all names and string values in the object.
        """
        a: Dict[str, Union[str, List[str]]] = {}
        for k, v in asdict(self).items():
            is_list_str = isinstance(v, List) and isinstance(v[0], str)
            if isinstance(v, str) or is_list_str:
                a[k] = v
        return a


def generate_component_pairings(
    machine: Machine, element_name: str
) -> list[Components]:
    """A function that generates the component pairings when given a valid
    quadrupole or bpm name.

    Args:
        machine: The Machine object for the accelerator.
        element_name: The name of the element.

    Returns:
        The component for the horizontal direction.
        The component for the vertical direction.

    Raises:
        ComponentConstructionError: If an invalid element name is given.
    """
    if element_name in machine.bpms_names:
        bpm = element_name
        quads = machine.bpm2quad(bpm)
    elif element_name in machine.quads_names:
        quad = element_name
        bpm = machine.quad2bpm(quad)
        quads = [quad]
    else:
        message = f"Element {element_name} does not correspond to quadrupole or BPM"
        log.critical(message)
        raise ComponentConstructionError(message)

    hor_corr, ver_corr = machine.effective_correctors(bpm)
    horizontal_components = Components.from_name(
        machine, bpm, quads, hor_corr, "x", "x_kick"
    )
    vertical_components = Components.from_name(
        machine, bpm, quads, ver_corr, "y", "y_kick"
    )
    return [horizontal_components, vertical_components]


def verify_component_pairing(
    machine: Machine, component_pairings: list[list[Components]]
) -> list[list[Components]]:
    """This function returns valid component pairings given the current machine state.
    Elements that are disabled will be valid upon component object construction, this
    function removes those elements and provides warnings where appropriate.

    Args:
        machine: The Machine object for the accelerator.
        component_pairings: The list of component pair lists.

    Returns:
        The verified list of component pair lists.
    """
    checked_pairings = []

    disabled_bpms_indices = np.nonzero(np.logical_not(machine.get_enabled_bpms()))[
        0
    ].tolist()
    disabled_fofb_bpm_indices_x = np.nonzero(machine.fofb_disabled["x"])[0].tolist()
    disabled_fofb_bpm_indices_y = np.nonzero(machine.fofb_disabled["y"])[0].tolist()
    disabled_fofb_indices = disabled_fofb_bpm_indices_x + disabled_fofb_bpm_indices_y

    for component_pair in component_pairings:
        try:
            check_component(
                component_pair, disabled_bpms_indices, disabled_fofb_indices
            )
        except ElementDisabledError:
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
    """This function checks the individual components that they are not invalid.
    Disabled BPMs cannot perform BBA, whereas FOFB Disabled BPMs can, but the
    result must be treated with caution.

    Args:
        component_pair: A pair of horizontal and vertical component objects.
        disabled_bpm_indices: The indices of the disabled BPMs.
        disabled_fofb_bpm_indices: The indicies of FOFB disabled BPMs.

    Raises:
        ElementDisabledError: If a disabled BPM is selected.
    """
    horizontal_component = component_pair[0]

    if horizontal_component.bpm_index in disabled_bpm_indices:
        msg = f"Cannot run BBA on disabled BPM: {horizontal_component.bpm_name}"
        log.error(msg)
        raise ElementDisabledError(msg)

    if horizontal_component.bpm_index in disabled_fofb_bpm_indices:
        msg = f"BPM: {horizontal_component.bpm_name} is feedback disabled. Results may be invalid."
        log.warning(msg)
