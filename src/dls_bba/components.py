from dataclasses import asdict, dataclass

from pytac.element import EpicsElement

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
    def from_pv_prefixes(
        cls,
        lattice: Lattice,
        bpm_name: str,
        quadrupoles_names: list[str],
        corrector_name: str,
        axis: str,
        kick: str,
    ):
        bpm, quadrupoles, corrector = Components.pv_to_element(
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
        # recreate the object from the dict, with elements and pvs
        bpm_name = dct["bpm_name"]
        quadrupoles_names = dct["quadrupoles_names"]
        corrector_name = dct["corrector_name"]
        axis = dct["axis"]
        kick = dct["kick"]

        return cls.from_pv_prefixes(
            lattice,
            bpm_name,
            quadrupoles_names,
            corrector_name,
            axis,
            kick,
        )

    @staticmethod
    def pv_to_element(
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
        return {
            k: v for k, v in asdict(self).items() if isinstance(k, (str, list(str)))
        }
