import os
from pathlib import Path

TEST_DATA_DIR = Path.cwd() / "tests/test_data/"
EPICS_SERVER_PORT = "8064"
EPICS_REPEATER_PORT = "8065"
os.environ.setdefault("EPICS_CA_SERVER_PORT", EPICS_SERVER_PORT)
os.environ.setdefault("EPICS_CA_REPEATER_PORT", EPICS_REPEATER_PORT)
