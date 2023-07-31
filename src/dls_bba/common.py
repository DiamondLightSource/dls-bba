import os
from typing import Optional

from dls_bba.algorithm import Algorithm
from dls_bba.fbba import FastBBA
from dls_bba.isotime import get_isotime
from dls_bba.logger import get_new_logger
from dls_bba.sbba import SlowBBA
from dls_bba.simfbba import SimFastBBA

ALGORITHMS: dict[str, type[Algorithm]] = {
    "SlowBBA": SlowBBA,
    "FastBBA": FastBBA,
    "SimFastBBA": SimFastBBA,
}


def setup_folders_and_logger(
    method: str, folder_path: Optional[str] = None, gui=None
) -> str:
    """"""
    foldername = f"{method}-{get_isotime()}"
    file = os.getcwd() if folder_path is None else folder_path
    bba_folderpath = os.path.join(file, foldername)
    os.makedirs(bba_folderpath)
    get_new_logger(bba_folderpath, gui)
    return bba_folderpath
