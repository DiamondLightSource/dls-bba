from dls_bba.logger import get_new_logger


def test_get_new_logger_no_gui(tmp_path):
    get_new_logger(tmp_path)
