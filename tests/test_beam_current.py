from unittest import mock

import pytest

from dls_bba.beam_current import BeamCurrentCheck
from dls_bba.exceptions import LowCurrentError


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0])
@mock.patch("dls_bba.worker.ask_question", side_effect=[None])
def test_beamcurrentcheck_init(mock_ask_question, mock_beam_current, machine_setup):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    assert bcc._initial_current == 0


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0, 14])
@mock.patch("dls_bba.worker.ask_question", side_effect=[None])
def test_beamcurrentcheck_check_beam_decay_valid(mock_ask_question, mock_beam_current, machine_setup):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    assert bcc.check_beam_decay()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0, 9])
@mock.patch("dls_bba.beam_current.BeamCurrentCheck.topup_beam", return_value=None)
@mock.patch("dls_bba.worker.ask_question", side_effect=[None])
def test_beamcurrentcheck_check_beam_decay_fail(
    mock_ask_question, mock_topup, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    assert not bcc.check_beam_decay()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0, 14])
@mock.patch("dls_bba.worker.ask_question", side_effect=[None])
def test_beamcurrentcheck_check_beam_drop_valid(mock_ask_question, mock_beam_current, machine_setup):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    assert bcc.check_beam_drop()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[15, 9])
@mock.patch("dls_bba.beam_current.BeamCurrentCheck.topup_beam", return_value=None)
@mock.patch("dls_bba.worker.ask_question", side_effect=[None])
def test_beamcurrentcheck_check_beam_drop_fail(
    mock_ask_question, mock_topup, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    assert not bcc.check_beam_drop()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0, 15])
@mock.patch("dls_bba.worker.ask_question", side_effect=[False])
def test_beamcurrentcheck_topup_user_returns_no(
    mock_ask_question, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    with pytest.raises(LowCurrentError):
        bcc.topup_beam(15)


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0, 16, 17])
@mock.patch("dls_bba.worker.ask_question", side_effect=[True])
@mock.patch("dls_bba.machine.Machine.check_feedbacks", return_value=None)
def test_beamcurrentcheck_topup_user_returns_yes(
    mock_check_feedbacks, mock_ask_question, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    bcc.topup_beam(15)


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0, 14, 16])
@mock.patch("dls_bba.worker.ask_question", side_effect=[True, True])
@mock.patch("dls_bba.machine.Machine.check_feedbacks", return_value=None)
def test_beamcurrentcheck_topup_user_returns_yes_then_yes_then_pass(
    mock_check_feedbacks, mock_ask_question, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    bcc.topup_beam(15)


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0, 15, 14, 14])
@mock.patch("dls_bba.worker.ask_question", side_effect=[True, True, False])
def test_beamcurrentcheck_topup_user_returns_yes_then_yes_then_no(
    mock_ask_question, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    with pytest.raises(LowCurrentError):
        bcc.topup_beam(15)
