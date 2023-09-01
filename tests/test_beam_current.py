from unittest import mock

import pytest

from dls_bba.beam_current import BeamCurrentCheck
from dls_bba.exceptions import LowCurrentError


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0])
@mock.patch("dls_bba.worker.ask_question", side_effect=[None])
def test_beam_current_is_stored_upon_object_creation(
    mock_ask_question, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    assert bcc._initial_current == 0


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[10, 10])
@mock.patch("dls_bba.worker.ask_question", side_effect=[None])
def test_return_true_when_beam_decay_is_ok(
    mock_ask_question, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    assert bcc.check_beam_decay()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[10, 9.9])
@mock.patch("dls_bba.beam_current.BeamCurrentCheck.topup_beam", return_value=None)
@mock.patch("dls_bba.worker.ask_question", side_effect=[None])
def test_return_false_when_beam_decay_is_bad(
    mock_ask_question, mock_topup, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    assert not bcc.check_beam_decay()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[15, 10])
@mock.patch("dls_bba.worker.ask_question", side_effect=[None])
def test_return_true_when_beam_drop_is_ok(
    mock_ask_question, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    assert bcc.check_beam_drop()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[15, 9.9])
@mock.patch("dls_bba.beam_current.BeamCurrentCheck.topup_beam", return_value=None)
@mock.patch("dls_bba.worker.ask_question", side_effect=[None])
def test_return_false_when_beam_drop_is_bad(
    mock_ask_question, mock_topup, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    assert not bcc.check_beam_drop()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0, 16])
@mock.patch("dls_bba.worker.ask_question", side_effect=[False])
@mock.patch("dls_bba.machine.Machine.check_feedbacks", return_value=None)
def test_user_returns_no_for_topup_prompt_and_check_feedbacks_is_not_called(
    mock_check_feedbacks, mock_ask_question, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    with pytest.raises(LowCurrentError):
        bcc.topup_beam(15)
        assert not mock_check_feedbacks.is_called


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0, 16, 17])
@mock.patch("dls_bba.worker.ask_question", side_effect=[True])
@mock.patch("dls_bba.machine.Machine.check_feedbacks", return_value=None)
def test_user_returns_yes_for_topup_prompt_and_check_feedbacks_is_called(
    mock_check_feedbacks, mock_ask_question, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    bcc.topup_beam(15)
    assert mock_check_feedbacks.is_called


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0, 15, 15, 16])
@mock.patch("dls_bba.worker.ask_question", side_effect=[True, True])
@mock.patch("dls_bba.machine.Machine.check_feedbacks", return_value=None)
def test_user_does_not_topup_sufficiently_first_time(
    mock_check_feedbacks, mock_ask_question, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    bcc.topup_beam(15)
    assert mock_check_feedbacks.is_called


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[0, 15, 15, 15])
@mock.patch("dls_bba.worker.ask_question", side_effect=[True, True, False])
@mock.patch("dls_bba.machine.Machine.check_feedbacks", return_value=None)
def test_user_does_not_topup_sufficiently_first_or_second_time_then_cancels(
    mock_check_feedbacks, mock_ask_question, mock_beam_current, machine_setup
):
    machine = machine_setup
    bcc = BeamCurrentCheck(machine, mock_ask_question)
    with pytest.raises(LowCurrentError):
        bcc.topup_beam(15)
        assert not mock_check_feedbacks.is_called
