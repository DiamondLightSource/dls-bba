from dataclasses import asdict, dataclass

from pytac.element import EpicsElement

from dls_bba.lattice import Lattice


@dataclass
class Components:
    bpm_pv_prefix: str
    quadrupoles_pvs_prefixes: list[str]
    corrector_pv_prefix: str
    axis: str
    kick: str
    bpm: EpicsElement
    quadrupoles: list[EpicsElement]
    corrector: EpicsElement

    @classmethod
    def from_pv_prefixes(
        cls,
        lattice: Lattice,
        bpm_pv_prefix: str,
        quadrupoles_pvs_prefixes: list[str],
        corrector_pv_prefix: str,
        axis: str,
        kick: str,
    ):
        bpm, quadrupoles, corrector = Components.pv_to_element(
            lattice, bpm_pv_prefix, quadrupoles_pvs_prefixes, corrector_pv_prefix
        )

        return cls(
            bpm_pv_prefix,
            quadrupoles_pvs_prefixes,
            corrector_pv_prefix,
            axis,
            kick,
            bpm,
            quadrupoles,
            corrector,
        )

    @classmethod
    def from_dict(cls, lattice: Lattice, dct: dict):
        # recreate the object from the dict, with elements and pvs
        bpm_pv_prefix = dct["bpm_pv_prefix"]
        quadrupoles_pvs_prefixes = dct["quadrupoles_pvs_prefixes"]
        corrector_pv_prefix = dct["corrector_pv_prefix"]
        axis = dct["axis"]
        kick = dct["kick"]

        return cls.from_pv_prefixes(
            lattice,
            bpm_pv_prefix,
            quadrupoles_pvs_prefixes,
            corrector_pv_prefix,
            axis,
            kick,
        )

    @staticmethod
    def pv_to_element(
        lattice: Lattice,
        bpm_pv_prefix: str,
        quadrupoles_pvs_prefixes: list[str],
        corrector_pv_prefix: str,
    ):
        bpm = lattice.bpms[lattice.bpms_pvs.index(bpm_pv_prefix)]
        quadrupoles = [
            lattice.quads[lattice.quads_pvs.index(quad_pv_prefix)]
            for quad_pv_prefix in quadrupoles_pvs_prefixes
        ]
        if "-PC-H" in corrector_pv_prefix:
            corrector = lattice.hstrs[lattice.hstrs_pvs.index(corrector_pv_prefix)]
        else:
            corrector = lattice.vstrs[lattice.vstrs_pvs.index(corrector_pv_prefix)]
        return bpm, quadrupoles, corrector

    def as_dict(self):
        return {
            k: v for k, v in asdict(self).items() if isinstance(k, (str, list(str)))
        }
