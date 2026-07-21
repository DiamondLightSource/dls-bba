import logging
import os
import subprocess
import sys
import time
import typing
from dataclasses import dataclass, field
from tempfile import NamedTemporaryFile
from typing import IO

import cothread
import pytac
from cothread import catools
from epicsdbbuilder import (
    InitialiseDbd,
    ResetRecords,
    WriteRecords,
    records,
)
from pytac import load_csv
from pytac.element import EpicsElement

from tests.conftest import EPICS_REPEATER_PORT, EPICS_SERVER_PORT

os.environ.setdefault("EPICS_CA_SERVER_PORT", EPICS_SERVER_PORT)
os.environ.setdefault("EPICS_CA_REPEATER_PORT", EPICS_REPEATER_PORT)

InitialiseDbd()


@dataclass
class Record:
    """Represents a single record for use in an IOC.

    There is no ability to link records to each other.
    """

    typ: str
    name: str
    fields: dict[str, typing.Any] = field(default_factory=dict)


class BBAIoc:
    def __init__(self) -> None:
        """Create new instance of BasicIoc.

        IOC will start using defined EPICS environment variables.
        """
        self.record_list: list[Record] = []
        self.db_file: IO = NamedTemporaryFile("w+t")
        self.process: subprocess.Popen | None = None
        self.create_bba_records()

    def create_bba_records(self) -> None:
        lattice = load_csv.load("I04")
        bpms: list[EpicsElement] = lattice.get_elements("BPM")

        for bpm in bpms:
            self.add_bo_record(bpm.get_pv_name("x_fofb_disabled", pytac.RB))
            self.add_bo_record(bpm.get_pv_name("y_fofb_disabled", pytac.RB))
            self.add_bo_record(bpm.get_pv_name("enabled", pytac.RB), initial_value=1)

    def _add_record(self, typ: str, pv_name: str, **fields: int) -> None:
        assert not self.is_started(), (
            f"Cannot add {typ} record to running IOC ({pv_name})"
        )

        if pv_name in (record.name for record in self.record_list):
            return

        self.record_list.append(Record(typ, pv_name, fields))

    def _generate_db_file(self) -> None:
        """Convert the list of records into the equivalent db file.

        Note that epicsdbbuilder is currently unable to handle multiple independent
        record sets. As a result, we keep all of that code in this function, and reset
        before and after use.
        """
        ResetRecords()

        for record in self.record_list:
            getattr(records, record.typ)(record.name, **record.fields)

        WriteRecords(self.db_file.name)
        ResetRecords()

    def start_ioc(self) -> None:
        """Launch IOC."""
        self._generate_db_file()
        with open(self.db_file.name) as f:
            logging.debug(f.read())

        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "epicscorelibs.ioc",
                "-d",
                self.db_file.name,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env={
                "EPICS_CA_SERVER_PORT": EPICS_SERVER_PORT,
                "EPICS_CA_REPEATER_PORT": EPICS_REPEATER_PORT,
            },
        )
        self.wait_for_ioc()

    def exit_ioc(self) -> None:
        """Close the soft IOC."""
        if self.process is not None:
            self.process.communicate("exit")
            self.process = None

        # Ensure that any cached connections are cleared in case
        # they appear in a new IOC later.
        # This is not cothread API.
        catools._channel_cache.purge()

    def is_started(self) -> bool:
        return self.process is not None

    def wait_for_ioc(self, timeout: float = 5) -> None:
        start = time.time()
        while True:
            assert self.process is not None
            assert self.process.stdout is not None
            assert time.time() - start < timeout
            line = self.process.stdout.readline()
            if line:
                logging.info(f">>> {line.strip()}")
            cothread.Yield()
            if "complete" in line:
                return

    def add_bo_record(
        self,
        pv_name: str,
        initial_value: int = 0,
        **fields: int,
    ) -> None:
        """Add a new binary-valued bo PV record."""
        final_fields = {"VAL": initial_value}
        final_fields.update(fields)

        self._add_record("bo", pv_name, **final_fields)
