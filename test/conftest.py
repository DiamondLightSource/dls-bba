import pytest
# Cothread can get in the way of coverage measurements, presumably
# because of the stack switching.
# If you import catools at the start of a test run then the imports
# in the code don't interfere with the coverage measurements.
from cothread import catools  # noqa

import pytac


@pytest.fixture
def lattice():
    return pytac.load_csv.load("DIAD")
