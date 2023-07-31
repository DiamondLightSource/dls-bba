import logging as log
import os
import sys

CONSOLE_LOG_FORMAT = "%(levelname)-7s: [%(filename)s:%(lineno)d] — %(message)s"
GUI_LOG_FORMAT = "%(levelname)-7s: %(message)s"
FILE_LOG_FORMAT = (
    "%(levelname)-7s: %(asctime)s — [%(filename)s:%(lineno)d] — %(message)s"
)


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ""

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass


def get_new_logger(folder_path, gui_handler=None):
    """"""
    logger = log.getLogger()
    logger.setLevel(log.NOTSET)
    logger.handlers.clear()
    filename = "log.log"

    console_handler = log.StreamHandler()
    console_handler.setLevel(log.DEBUG)
    console_handler.setFormatter(log.Formatter(CONSOLE_LOG_FORMAT))
    logger.addHandler(console_handler)

    if gui_handler is not None:
        sys.stderr = StreamToLogger(logger, log.CRITICAL)
        gui_handler.setLevel(log.INFO)
        gui_handler.setFormatter(log.Formatter(GUI_LOG_FORMAT))
        logger.addHandler(gui_handler)

    file_handler = log.FileHandler(os.path.join(folder_path, filename))
    file_handler.setLevel(log.DEBUG)
    file_handler.setFormatter(log.Formatter(FILE_LOG_FORMAT))
    logger.addHandler(file_handler)
