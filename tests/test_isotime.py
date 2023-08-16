from dls_bba.isotime import get_isotime


def test_get_isotime_returns_valid_isotime():
    isotime = get_isotime()
    assert len(isotime) == 15
    assert isinstance(isotime, str)
    assert isotime[8] == "T"
