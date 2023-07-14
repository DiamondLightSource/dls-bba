import logging as log

from dls_bba.exceptions import LowCurrentError
from dls_bba.machine import Machine


class BeamCurrentCheck:
    def __init__(self, machine: Machine) -> None:
        self._machine = machine
        self._store_initial_current()

    def _store_initial_current(self) -> None:
        self._initial_current = self._machine.get_beam_current()
        msg = f"Stored Starting Beam Current: {self._initial_current}"
        log.debug(msg)

    def check_beam_decay(self) -> None:
        decay_current = self._machine.config["DECAY_CURRENT"]
        current_current = self._machine.get_beam_current()
        change_in_current = self._initial_current - current_current
        log.debug(f"Change in current: {change_in_current}")

        if change_in_current >= decay_current:
            self.topup_beam()

    def check_beam_drop(self) -> bool:
        warning_current_drop = self._machine.config["WARNING_CURRENT_DROP"]
        critical_current_drop = self._machine.config["CRITICAL_CURRENT_DROP"]
        current_current = self._machine.get_beam_current()
        change_in_current = self._initial_current - current_current
        log.debug(f"Change in current: {change_in_current}")

        if change_in_current > critical_current_drop:
            msg = f"Beam current drop by >{critical_current_drop} mA"
            log.critical(msg)
            raise LowCurrentError(msg)

        if change_in_current > warning_current_drop:
            self.topup_beam()
            return False

        return True

    def topup_beam(self) -> None:

        while True:
            msg = f"Please topup current to > {self._initial_current}mA."
            log.error(msg)
            msg = "Input y to continue after top-up, or n to cancel: "
            response = self._machine._ask_user(msg)

            if response == "n":
                msg = "User cancelled BBA: Due to beam current drop."
                log.critical(msg)
                raise LowCurrentError(msg)

            elif response == "y":
                current = self._machine.get_beam_current()
                if self._initial_current < current:
                    break
        self._machine.check_feedbacks()
