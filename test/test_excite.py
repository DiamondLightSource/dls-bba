import pytac
import pytest

from bba.pml import excite
from bba.pml.definitions import X, Y


@pytest.fixture
def lattice():
    return pytac.load_csv.load("DIAD")


def test_get_fofb_corrector(lattice):
    h1 = lattice.get_elements("HSTR")[10]
    fofb_corrector = excite.get_fofb_corrector(h1, X)
    assert fofb_corrector.corr == 3
    v1 = lattice.get_elements("VSTR")[10]
    fofb_corrector = excite.get_fofb_corrector(v1, Y)
    assert fofb_corrector.corr == 12
