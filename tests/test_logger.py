import os

from dls_bba.logger import get_new_logger


def test_get_new_logger_no_gui_creates_log_file_in_expected_location(tmp_path):
    get_new_logger(tmp_path)
    assert os.path.isfile(os.path.join(tmp_path, "log.log"))
