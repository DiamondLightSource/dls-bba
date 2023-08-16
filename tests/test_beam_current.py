from unittest import mock

import pytest

from dls_bba.beam_current import BeamCurrentCheck
from dls_bba.exceptions import LowCurrentError


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0])
def test_beamcurrentcheck_init(mock_beam_current, machine_setup):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine)
    assert bcc._initial_current == 0


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[15, 14])
def test_beamcurrentcheck_check_beam_decay_valid(mock_beam_current, machine_setup):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine)
    assert bcc.check_beam_decay()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[15, 9])
@mock.patch("dls_bba.beam_current.BeamCurrentCheck.topup_beam", return_value=None)
def test_beamcurrentcheck_check_beam_decay_fail(
    mock_topup, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine)
    assert not bcc.check_beam_decay()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[15, 14])
def test_beamcurrentcheck_check_beam_drop_valid(mock_beam_current, machine_setup):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine)
    assert bcc.check_beam_drop()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[15, 9])
@mock.patch("dls_bba.beam_current.BeamCurrentCheck.topup_beam", return_value=None)
def test_beamcurrentcheck_check_beam_drop_fail(
    mock_topup, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine)
    assert not bcc.check_beam_drop()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[15])
@mock.patch("dls_bba.machine.Machine._ask_user", side_effect=["n"])
def test_beamcurrentcheck_topup_user_returns_no(
    mock_ask_user, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine)
    with pytest.raises(LowCurrentError):
        bcc.topup_beam(15)


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[15, 16])
@mock.patch("dls_bba.machine.Machine._ask_user", side_effect=["y"])
@mock.patch("dls_bba.machine.Machine.check_feedbacks", return_value=None)
def test_beamcurrentcheck_topup_user_returns_yes(
    mock_check_feedbacks, mock_ask_user, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine)
    bcc.topup_beam(15)


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[15, 14, 16])
@mock.patch("dls_bba.machine.Machine._ask_user", side_effect=["y", "y"])
@mock.patch("dls_bba.machine.Machine.check_feedbacks", return_value=None)
def test_beamcurrentcheck_topup_user_returns_yes_then_yes_then_pass(
    mock_check_feedbacks, mock_ask_user, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine)
    bcc.topup_beam(15)


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[15, 14, 16])
@mock.patch("dls_bba.machine.Machine._ask_user", side_effect=["y", "n"])
def test_beamcurrentcheck_topup_user_returns_yes_then_yes_then_no(
    mock_ask_user, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine)
    with pytest.raises(LowCurrentError):
        bcc.topup_beam(15)
