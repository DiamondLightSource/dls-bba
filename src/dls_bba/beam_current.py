import logging as log
from typing import Callable

from dls_bba.exceptions import LowCurrentError
from dls_bba.machine import Machine


class BeamCurrentCheck:
    """A class to check the beam current and top-up if necessary."""

    def __init__(self, machine: Machine, question: Callable[[str], bool]) -> None:
        """Initialise the class and store the initial beam current.

        Args:
            machine: The machine object.
        """
        self._machine = machine
        self.question = question
        self._store_initial_current()

    def _store_initial_current(self) -> None:
        """Store the initial beam current."""
        self._initial_current = self._machine.get_beam_current()
        msg = f"Stored Starting Beam Current: {self._initial_current}"
        log.debug(msg)

    def check_beam_decay(self) -> bool:
        """Check if the beam current has decayed below the minimum current.

        Returns:
            True if beam has not dropped below the minimum current, False if it has.
        """
        min_current = self._machine.config["MIN_CURRENT"]
        current_current = self._machine.get_beam_current()
        log.debug(f"Current: {current_current}; Decay limit: {min_current}")

        if current_current < min_current:
            self.topup_beam(min_current)
            return False

        return True

    def check_beam_drop(self) -> bool:
        """Check if the beam current has dropped below the warning current drop.

        Returns:
            True if beam has not dropped below warning current drop, False if it has.
        """
        warning_current_drop = self._machine.config["WARNING_CURRENT_DROP"]
        current_current = self._machine.get_beam_current()
        change_in_current = self._initial_current - current_current
        log.debug(f"Change in current: {change_in_current}")

        if change_in_current > warning_current_drop:
            self.topup_beam(self._initial_current)
            return False

        return True

    def topup_beam(self, minimum_topup: float) -> None:
        """Prompt the user to topup the beam current.

        Args:
            minimum_topup: The minimum current (mA) to top-up to.
        """
        start_current = self._machine.get_beam_current()

        while True:
            msg = f"Please topup current to > {minimum_topup}mA."
            log.error(msg)
            msg = "Input y to continue after top-up, or n to cancel: "
            response = self.question(msg)

            if response:
                current = self._machine.get_beam_current()
                if current > start_current:
                    break

            else:
                msg = "User cancelled BBA: Due to beam current drop."
                log.critical(msg)
                raise LowCurrentError(msg)

        self._machine.check_feedbacks()
