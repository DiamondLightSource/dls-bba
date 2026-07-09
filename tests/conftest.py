import os
from pathlib import Path

os.environ.setdefault("EPICS_CA_SERVER_PORT", "8064")

TEST_DATA_DIR = Path.cwd() / "tests/test_data/"
