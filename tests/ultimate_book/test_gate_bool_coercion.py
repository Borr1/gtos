"""The ultimate_book authority gates must not fail open on string config values.

Before this was fixed, `bridge._bool` was a bare `bool(...)`, so every textual form
of "off" -- "false", "no", "off", "0", "disabled" -- evaluated **True**. It resolves
19 gates in bridge.py, including the three authority gates
(`bridge.py:275-277`, which were `:254-256` before the fix added its helper):
ultimate_book_enabled, ultimate_book_apply_to_execution and
ultimate_book_live_activation_allowed, the last of which is the live order-authority
gate. A single quoted YAML value or a supervisor/env overlay could therefore grant
live authority while the config file still read `false` to a human auditor.

The VPS live-hardening branch fixed this with `config_bool_value`; mainline never
received it. These tests pin the corrected behaviour through the real gate path.
"""

from __future__ import annotations

import pytest

from src.components.ultimate_book.admission import GovernorState
from src.components.ultimate_book.bridge import (
    config_bool_value,
    evaluate_vnext_ultimate_book_admission,
)

FALSEY_TEXT = ["false", "False", "FALSE", " false ", "no", "n", "off", "0", "disabled"]
TRUTHY_TEXT = ["true", "True", "yes", "y", "on", "1", "enabled"]


@pytest.mark.parametrize("value", FALSEY_TEXT)
def test_config_bool_value_parses_textual_false(value):
    # The bare bool() this replaced returned True for every one of these.
    assert config_bool_value(value, False) is False
    assert config_bool_value(value, True) is False


@pytest.mark.parametrize("value", TRUTHY_TEXT)
def test_config_bool_value_parses_textual_true(value):
    assert config_bool_value(value, False) is True


def test_config_bool_value_falls_back_to_default_on_unknown():
    # An unrecognised value must not be coerced to True by truthiness; it takes the
    # supplied default, which for every authority gate is False.
    assert config_bool_value("maybe", False) is False
    assert config_bool_value("maybe", True) is True
    assert config_bool_value(None, False) is False
    assert config_bool_value(None, True) is True


def test_config_bool_value_preserves_native_and_numeric():
    assert config_bool_value(True, False) is True
    assert config_bool_value(False, True) is False
    assert config_bool_value(1, False) is True
    assert config_bool_value(0, True) is False


def _governor_state() -> GovernorState:
    return GovernorState(
        equity=100000,
        high_water=100000,
        realized_today_pct=0.0,
        open_risk_pct=0.0,
        max_dd_reference_equity=100000,
    )


@pytest.mark.parametrize("value", FALSEY_TEXT)
def test_string_false_does_not_grant_live_activation(value):
    """The end-to-end assertion: a stringly-typed 'off' must stay off.

    Both other gates are armed so the only thing standing between this config and
    live order authority is the coercion under test.
    """
    config = {
        "gtos_vnext_runtime": {
            "ultimate_book_enabled": True,
            "ultimate_book_apply_to_execution": True,
            "ultimate_book_live_activation_allowed": value,
        }
    }
    decision = evaluate_vnext_ultimate_book_admission(
        config=config, intents=[], governor_state=_governor_state()
    )
    assert decision.live_activation_allowed_by_config is False
    assert decision.runtime_effect_now is False
    assert decision.candidate_use_allowed_now is False
    assert decision.realized_units == []


@pytest.mark.parametrize("value", TRUTHY_TEXT)
def test_string_true_is_still_read_as_armed(value):
    """The fix must not make the gate unconditionally False.

    Only the config-gate read is asserted here: runtime_effect_now additionally
    depends on the broad-selector replacement invariant, which is a separate guard.
    """
    config = {
        "gtos_vnext_runtime": {
            "ultimate_book_enabled": True,
            "ultimate_book_apply_to_execution": True,
            "ultimate_book_live_activation_allowed": value,
        }
    }
    decision = evaluate_vnext_ultimate_book_admission(
        config=config, intents=[], governor_state=_governor_state()
    )
    assert decision.live_activation_allowed_by_config is True


def test_missing_gate_key_still_fails_closed():
    decision = evaluate_vnext_ultimate_book_admission(
        config={"gtos_vnext_runtime": {}}, intents=[], governor_state=_governor_state()
    )
    assert decision.live_activation_allowed_by_config is False
    assert decision.runtime_effect_now is False
    assert decision.realized_units == []
