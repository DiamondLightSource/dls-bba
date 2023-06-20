from dls_bba.isotime import get_isotime


def test_get_isotime():
    isotime = get_isotime()
    assert len(isotime) == 15
    assert type(isotime) == str
    assert isotime[8] == "T"
