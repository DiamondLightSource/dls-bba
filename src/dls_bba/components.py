from __future__ import annotations

import logging as log
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Union

import numpy as np
import pytac

from dls_bba.exceptions import ComponentConstructionError, ElementDisabledError

if TYPE_CHECKING:
    from dls_bba.lattice import Lattice


@dataclass
class Components:
    """The components class stores both the names and EpicsElements for the
    paired components, including additional information such as the axis, kick
    and indices."""

    bpm_name: str
    quadrupoles_names: list[str]
    corrector_name: str
    axis: str
    kick: str
    bpm: pytac.element.EpicsElement
    quadrupoles: list[pytac.element.EpicsElement]
    corrector: pytac.element.EpicsElement
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
        """Components constructor using the names of the components.

        Args:
            lattice: The Lattice object for the accelerator.
            bpm_name: The name of the BPM required.
            quadrupoles_names: The names of quadrupoles required in a list.
            corrector_name: The name of the corrector required.
            axis: The axis of interest. eg. 'x' or 'y'
            kick: The corrector kick of interest. eg. 'x_kick' or 'y_kick'

        Returns:
            The constructed Components object.
        """
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
    def from_dict(cls, lattice: Lattice, dct: dict[str, str]):
        """Components constructor using a dictionary.

        Args:
            lattice: The Lattice object for the accelerator.
            dct: A dictionary that contains information for construction.

        Returns:
            The constructed Components object.
        """
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
    ) -> tuple[
        pytac.element.EpicsElement,
        list[pytac.element.EpicsElement],
        pytac.element.EpicsElement,
    ]:
        """A function that converts component names to EpicsElements.

        Args:
            lattice: The Lattice object for the accelerator.
            bpm_name: The name of the BPM required.
            quadrupoles_names: The names of quadrupoles required in a list.
            corrector_name: The name of the corrector required.

        Returns:
            The EpicsElement object for the BPM.
            A list of EpicsElements for the quadrupoles.
            The EpicsElement object for the corrector.
        """
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

    def as_dict(self) -> dict[str, Union[str, list[str]]]:
        """A function that converts the component names into a dictionary.

        Returns:
            A dictionary of all names and string values in the object.
        """
        dct: dict[str, Union[str, list[str]]] = {}
        for k, v in asdict(self).items():
            if isinstance(v, str):
                dct[k] = v
            if isinstance(v, list) and isinstance(v[0], str):
                dct[k] = v
        return dct


def generate_component_pairings(
    lattice: Lattice, element_name: str
) -> list[Components]:
    """A function that generates the component pairings when given a valid
    quadrupole or bpm name.

    Args:
        lattice: The Lattice object for the accelerator.
        element_name: The name of the element.

    Returns:
        The component for the horizontal direction.
        The component for the vertical direction.

    Raises:
        ComponentConstructionError: If an invalid element name is given.
    """
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
        raise ComponentConstructionError(message)

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
    """This function returns valid component pairings given the current machine state.
    Elements that are disabled will be valid upon component object construction, this
    function removes those elements and provides warnings where appropriate.

    Args:
        lattice: The Lattice object for the accelerator.
        component_pairings: The list of component pair lists.

    Returns:
        The verified list of component pair lists.
    """
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
