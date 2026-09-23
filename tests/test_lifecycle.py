"""Tests for trade lifecycle state machine transitions."""

import pytest

from src.models.trade_models import (
    TERMINAL_STATES,
    VALID_TRANSITIONS,
    InvalidTransitionError,
    transition,
)


def _make_record(state: str = "EVALUATING") -> dict:
    """Create a minimal trade record dict for lifecycle testing."""
    return {
        "lifecycle_state": state,
        "state_transitions": [],
    }


# -------------------------------------------------------------------
# Happy-path: every valid transition succeeds
# -------------------------------------------------------------------

class TestValidTransitions:

    @pytest.mark.parametrize(
        "from_state, to_state",
        [
            ("EVALUATING", "NO_TRADE"),
            ("EVALUATING", "CANDIDATE"),
            ("CANDIDATE", "DEBATED"),
            ("DEBATED", "REJECTED"),
            ("DEBATED", "APPROVED"),
            ("APPROVED", "EXECUTING"),
            ("EXECUTING", "ACTIVE"),
            ("EXECUTING", "FAILED_EXECUTION"),
            ("ACTIVE", "CLOSED"),
        ],
    )
    def test_valid_transition(self, from_state, to_state):
        record = _make_record(from_state)
        transition(record, from_state, to_state, f"test_{from_state}_to_{to_state}")
        assert record["lifecycle_state"] == to_state

    def test_full_happy_path(self):
        """Walk the complete EVALUATING → … → CLOSED path."""
        record = _make_record("EVALUATING")
        steps = [
            ("EVALUATING", "CANDIDATE", "primary_candidate"),
            ("CANDIDATE", "DEBATED", "debate_completed"),
            ("DEBATED", "APPROVED", "verdict_approve"),
            ("APPROVED", "EXECUTING", "order_sent"),
            ("EXECUTING", "ACTIVE", "order_filled"),
            ("ACTIVE", "CLOSED", "tp1_hit"),
        ]
        for from_s, to_s, event in steps:
            transition(record, from_s, to_s, event)

        assert record["lifecycle_state"] == "CLOSED"
        assert len(record["state_transitions"]) == 6

    def test_rejection_path(self):
        """EVALUATING → CANDIDATE → DEBATED → REJECTED."""
        record = _make_record("EVALUATING")
        transition(record, "EVALUATING", "CANDIDATE", "primary_candidate")
        transition(record, "CANDIDATE", "DEBATED", "debate_completed")
        transition(record, "DEBATED", "REJECTED", "verdict_reject")
        assert record["lifecycle_state"] == "REJECTED"


# -------------------------------------------------------------------
# Invalid transitions
# -------------------------------------------------------------------

class TestInvalidTransitions:

    @pytest.mark.parametrize(
        "from_state, to_state",
        [
            # Skip states
            ("EVALUATING", "DEBATED"),
            ("EVALUATING", "APPROVED"),
            ("EVALUATING", "EXECUTING"),
            ("EVALUATING", "ACTIVE"),
            ("EVALUATING", "CLOSED"),
            ("EVALUATING", "REJECTED"),
            ("EVALUATING", "FAILED_EXECUTION"),
            # Backward transitions
            ("CANDIDATE", "EVALUATING"),
            ("DEBATED", "CANDIDATE"),
            ("DEBATED", "EVALUATING"),
            ("APPROVED", "DEBATED"),
            ("EXECUTING", "APPROVED"),
            ("ACTIVE", "EXECUTING"),
            # Cross-branch transitions
            ("CANDIDATE", "APPROVED"),
            ("CANDIDATE", "ACTIVE"),
            ("APPROVED", "ACTIVE"),
            ("APPROVED", "CLOSED"),
            # Self-transitions
            ("EVALUATING", "EVALUATING"),
            ("ACTIVE", "ACTIVE"),
        ],
    )
    def test_invalid_transition_raises(self, from_state, to_state):
        record = _make_record(from_state)
        with pytest.raises(InvalidTransitionError):
            transition(record, from_state, to_state, "bad_event")

    def test_wrong_from_state_raises(self):
        """Record is in CANDIDATE but caller says from_state=EVALUATING."""
        record = _make_record("CANDIDATE")
        with pytest.raises(InvalidTransitionError, match="Record is in CANDIDATE, not EVALUATING"):
            transition(record, "EVALUATING", "CANDIDATE", "wrong_from")

    def test_nonexistent_state_raises(self):
        record = _make_record("EVALUATING")
        with pytest.raises(InvalidTransitionError):
            transition(record, "EVALUATING", "INVENTED_STATE", "bad")


# -------------------------------------------------------------------
# Terminal states reject all transitions
# -------------------------------------------------------------------

class TestTerminalStates:

    @pytest.mark.parametrize("terminal_state", list(TERMINAL_STATES))
    def test_terminal_state_rejects_all(self, terminal_state):
        record = _make_record(terminal_state)
        # Try transitioning to every possible state
        all_states = set()
        for targets in VALID_TRANSITIONS.values():
            all_states |= targets
        all_states |= set(VALID_TRANSITIONS.keys())

        for target in all_states:
            with pytest.raises(InvalidTransitionError, match="terminal state"):
                transition(record, terminal_state, target, "should_fail")


# -------------------------------------------------------------------
# Transition logging
# -------------------------------------------------------------------

class TestTransitionLogging:

    def test_transition_appends_to_state_transitions(self):
        record = _make_record("EVALUATING")
        transition(record, "EVALUATING", "CANDIDATE", "primary_candidate")

        assert len(record["state_transitions"]) == 1
        entry = record["state_transitions"][0]
        assert entry["from"] == "EVALUATING"
        assert entry["to"] == "CANDIDATE"
        assert entry["event"] == "primary_candidate"
        assert "time" in entry

    def test_multiple_transitions_append_in_order(self):
        record = _make_record("EVALUATING")
        transition(record, "EVALUATING", "CANDIDATE", "ev1")
        transition(record, "CANDIDATE", "DEBATED", "ev2")
        transition(record, "DEBATED", "APPROVED", "ev3")

        assert len(record["state_transitions"]) == 3
        assert [t["event"] for t in record["state_transitions"]] == ["ev1", "ev2", "ev3"]

    def test_transition_does_not_mutate_on_failure(self):
        record = _make_record("EVALUATING")
        original_transitions = list(record["state_transitions"])
        with pytest.raises(InvalidTransitionError):
            transition(record, "EVALUATING", "CLOSED", "bad")
        # State and transitions unchanged
        assert record["lifecycle_state"] == "EVALUATING"
        assert record["state_transitions"] == original_transitions

    def test_time_is_iso_format(self):
        record = _make_record("EVALUATING")
        transition(record, "EVALUATING", "CANDIDATE", "test")
        time_str = record["state_transitions"][0]["time"]
        # Should be parseable as ISO datetime
        from datetime import datetime
        dt = datetime.fromisoformat(time_str)
        assert dt.year >= 2026
