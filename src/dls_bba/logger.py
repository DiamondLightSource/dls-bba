import logging as log
import os

CONSOLE_LOG_FORMAT = "%(levelname)-7s: [%(filename)s:%(lineno)d] — %(message)s"
"""The format for console log output."""
FILE_LOG_FORMAT = (
    "%(levelname)-7s: %(asctime)s — [%(filename)s:%(lineno)d] — %(message)s"
)
"""The format for file log output."""


def get_new_logger(folder_path):
    """This function sets up the logger.

    Args:
        folder_path: This is the folder path to put the logging file into.
    """
    logger = log.getLogger()
    logger.setLevel(log.NOTSET)
    filename = "log.log"
    # Console handler
    console_handler = log.StreamHandler()
    console_handler.setLevel(log.INFO)
    console_handler.setFormatter(log.Formatter(CONSOLE_LOG_FORMAT))
    logger.addHandler(console_handler)
    # File handler
    file_handler = log.FileHandler(os.path.join(folder_path, filename))
    file_handler.setLevel(log.DEBUG)
    file_handler.setFormatter(log.Formatter(FILE_LOG_FORMAT))
    logger.addHandler(file_handler)
