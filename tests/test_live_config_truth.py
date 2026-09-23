"""Which gates are ACTUALLY live — pinned by CI instead of rediscovered by archaeology.

Why this file exists
--------------------
Both independent audits had to re-derive the live decision surface by reading
config and tracing gate resolvers, and both got parts of it wrong on the first
pass (SECOND_AUDIT.md E1c). Nothing in the suite asserted the shipped
configuration's actual authority state, so every audit paid the archaeology cost
again.

This file states that state once, as executable assertions over the **shipped**
`config/agent_config.yaml` and the real gate resolvers.

`config/agent_config.yaml` is SHA-bound by the R2 decision contract
(`CLAUDE.md` H1). These tests **read** it and never write it.

The F8 asymmetry, which is the reason this file is not merely a config snapshot
---------------------------------------------------------------------------
One flag name, `live_activation_allowed`, carries two contradictory meanings:

* **Scheduler-V4 path** — `false` *disables a rejection gate*.
  `permissions._scheduler_v4_required` (`permissions.py:655-664`) short-circuits
  on the flag, so `_reject_if_scheduler_v4_not_selected_authority`
  (`permissions.py:930-938`) returns `None`: **no denial is produced at all**.
  Arming the flag is what makes the gate fire.

* **Book path** — `false` *suppresses placement*.
  `bridge.evaluate_vnext_ultimate_book_admission` (`bridge.py:487-490`) returns
  `shadow_live_activation_not_allowed` with `runtime_effect_now=False`.

Same flag name, opposite polarity. Both meanings are pinned below so a future
reader cannot assume one from the other.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.components import permissions as P
from src.components.ultimate_book.admission import GovernorState
from src.components.ultimate_book.bridge import evaluate_vnext_ultimate_book_admission


ROOT = Path(__file__).resolve().parents[1]
AGENT_CONFIG = ROOT / "config" / "agent_config.yaml"
PROFILE_DIR = ROOT / "config" / "profiles"


@pytest.fixture(scope="module")
def shipped_config() -> dict:
    return yaml.safe_load(AGENT_CONFIG.read_text())


@pytest.fixture(scope="module")
def runtime(shipped_config) -> dict:
    return shipped_config["gtos_vnext_runtime"]


def _governor_state() -> GovernorState:
    return GovernorState(
        equity=100000.0,
        high_water=100000.0,
        realized_today_pct=0.0,
        open_risk_pct=0.0,
        max_dd_reference_equity=100000.0,
    )


class _GovernedVNextTrade:
    """The four attributes `_vnext_risk_budget_governed_trade` requires.

    permissions.py:1105-1127 — context active, a selected policy, an execution
    policy id, and a positive selected-cell risk pct.
    """
    gtos_vnext_production_execution_path = True
    gtos_vnext_dynamic_policy_selected = "test_policy"
    gtos_vnext_execution_policy_id = "test_execution_policy"
    gtos_vnext_selected_cell_risk_pct = 0.4


class _UngovernedTrade:
    """Carries none of them."""


# ---------------------------------------------------------------------------
# 1. The shipped configuration's authority state, key by key
# ---------------------------------------------------------------------------

class TestShippedGateValues:
    """E1c, as assertions. If any of these changes, this test is where you find out."""

    @pytest.mark.parametrize("key,expected", [
        # --- V3: fully off, both halves ---------------------------------
        ("selector_v3_enabled", False),
        ("selector_v3_apply_to_execution", False),
        ("scheduler_v3_enabled", False),
        ("scheduler_v3_apply_to_execution", False),

        # --- Selector V4: exists, exercised in replay, no live authority --
        ("selector_v4_enabled", True),
        ("selector_v4_apply_to_execution", False),
        ("selector_v4_live_activation_allowed", False),

        # --- Scheduler V4: enabled AND apply_to_execution, but no live ----
        #     activation. This combination is the one that surprises readers:
        #     apply_to_execution is TRUE here and FALSE for selector V4.
        ("scheduler_v4_best_trade_allocator_enabled", True),
        ("scheduler_v4_best_trade_allocator_apply_to_execution", True),
        ("scheduler_v4_best_trade_allocator_live_activation_allowed", False),

        # --- The ultimate_book: the declared live decision surface --------
        ("ultimate_book_enabled", True),
        ("ultimate_book_apply_to_execution", True),
        ("ultimate_book_live_activation_allowed", False),

        # --- The candidate package ---------------------------------------
        ("ultimate_candidate_package_live_activation_allowed", False),
    ])
    def test_gate_value(self, runtime, key, expected):
        assert key in runtime, f"{key} vanished from config/agent_config.yaml"
        assert runtime[key] is expected, (
            f"{key} is {runtime[key]!r}, expected {expected!r}. "
            "If this change is intended, update this test and say why in the commit."
        )

    def test_every_gate_value_is_a_native_bool(self, runtime):
        """A quoted YAML bool would once have failed open (F29, fixed in 1a1eeba50).

        `config_bool_value` now parses textual forms correctly, but a native bool
        is still the only form that reads unambiguously to a human auditor.
        """
        for key, value in runtime.items():
            if key.endswith(("_enabled", "_apply_to_execution", "_live_activation_allowed",
                             "_live_broker_authority")):
                assert isinstance(value, bool), (
                    f"{key} = {value!r} is {type(value).__name__}, not a native bool"
                )

    def test_live_broker_authority_is_absent_from_yaml_and_defaults_closed(self, runtime):
        """The 4th gate landed as code, not as an explicit YAML key (B19).

        `bridge.DEFAULT_CONFIG` carries `ultimate_book_live_broker_authority: False`
        (`bridge.py:70`), so the gate is fail-closed today. The explicit YAML key
        is queued to a contract re-seal batch. This test states the current truth
        rather than the intended end state — when the key does land, flip it here.
        """
        assert "ultimate_book_live_broker_authority" not in runtime

        decision = evaluate_vnext_ultimate_book_admission(
            config={"gtos_vnext_runtime": dict(runtime)},
            intents=[],
            governor_state=_governor_state(),
        )
        assert decision.live_broker_authority is False

    def test_book_profile_and_derisk_mode_are_the_declared_live_pair(self, runtime):
        """live_system_of_record.md: clean3_w7_ceiling_nom2p00 with mandatory smooth derisk."""
        assert runtime["ultimate_book_profile"] == "clean3_w7_ceiling_nom2p00"
        assert runtime["ultimate_book_derisk_mode"] == "smooth"


# ---------------------------------------------------------------------------
# 2. F8 — one flag name, two contradictory meanings
# ---------------------------------------------------------------------------

class TestF8FlagPolarityOnTheSchedulerV4Path:
    """`live_activation_allowed=false` DISABLES the rejection gate here."""

    def test_shipped_config_produces_no_denial_for_a_governed_trade(self, shipped_config):
        """The gate is a no-op at shipped config — not armed, absent.

        This is the counter-intuitive half. A reader who assumes "activation not
        allowed" means "the trade is rejected" has it exactly backwards on this
        path: nothing is rejected, because the gate never runs.
        """
        denial = P._reject_if_scheduler_v4_not_selected_authority(
            None, "XAUUSD", shipped_config, _GovernedVNextTrade()
        )
        assert denial is None

    def test_the_flag_is_what_short_circuits_it(self, shipped_config):
        """Off -> refused before the trade is even examined; on -> the trade decides.

        The two `reason` strings are the proof: with the flag off the predicate
        never reaches the governed-trade check, so a governed and an ungoverned
        trade produce the SAME config-level reason.
        """
        required_off, proof_off = P._scheduler_v4_required(
            shipped_config, _GovernedVNextTrade()
        )
        assert required_off is False
        assert proof_off["reason"] == "scheduler_v4_not_terminal_by_config"

        # Same reason for an ungoverned trade: the flag short-circuits first.
        _, proof_off_ungoverned = P._scheduler_v4_required(
            shipped_config, _UngovernedTrade()
        )
        assert proof_off_ungoverned["reason"] == "scheduler_v4_not_terminal_by_config"

        armed = {"gtos_vnext_runtime": dict(shipped_config["gtos_vnext_runtime"])}
        armed["gtos_vnext_runtime"][
            "scheduler_v4_best_trade_allocator_live_activation_allowed"
        ] = True

        required_on, _ = P._scheduler_v4_required(armed, _GovernedVNextTrade())
        assert required_on is True, (
            "arming live_activation_allowed must make the gate live; if this "
            "fails the flag is no longer the enabling condition"
        )

        # With the flag armed the trade's own properties become the deciding
        # factor, and the reason changes accordingly.
        required_on_ungoverned, proof_on_ungoverned = P._scheduler_v4_required(
            armed, _UngovernedTrade()
        )
        assert required_on_ungoverned is False
        assert proof_on_ungoverned["reason"] == "trade_not_vnext_risk_budget_governed"


class TestF8FlagPolarityOnTheBookPath:
    """`live_activation_allowed=false` SUPPRESSES placement here — the opposite."""

    def test_shipped_config_is_shadow_only_with_the_activation_reason(self, shipped_config):
        decision = evaluate_vnext_ultimate_book_admission(
            config=shipped_config, intents=[], governor_state=_governor_state()
        )
        assert decision.enabled is True
        assert decision.apply_to_execution is True
        assert decision.live_activation_allowed_by_config is False
        assert decision.runtime_effect_now is False
        assert decision.candidate_use_allowed_now is False
        assert decision.decision_status == "shadow_live_activation_not_allowed"
        assert decision.reason == "ultimate_book_live_activation_allowed_false"
        assert decision.realized_units == []

    def test_arming_only_this_flag_advances_to_the_broker_authority_gate(self, shipped_config):
        """Proves the gate ordering: activation is gate 3, broker authority gate 4.

        Arming activation alone does NOT reach live — the next gate catches it.
        A regression that collapsed the two would show up here as a
        `runtime_effect_now=True`.
        """
        armed = {"gtos_vnext_runtime": dict(shipped_config["gtos_vnext_runtime"])}
        armed["gtos_vnext_runtime"]["ultimate_book_live_activation_allowed"] = True

        decision = evaluate_vnext_ultimate_book_admission(
            config=armed, intents=[], governor_state=_governor_state()
        )
        assert decision.live_activation_allowed_by_config is True
        assert decision.decision_status == "shadow_live_broker_authority_false"
        assert decision.reason == "ultimate_book_live_broker_authority_false"
        assert decision.runtime_effect_now is False
        assert decision.realized_units == []


class TestF8IsStatedRatherThanAssumed:
    """The asymmetry itself, as one assertion, so it cannot be read off by accident."""

    def test_the_same_flag_value_means_no_denial_on_one_path_and_no_placement_on_the_other(
        self, shipped_config
    ):
        scheduler_denial = P._reject_if_scheduler_v4_not_selected_authority(
            None, "XAUUSD", shipped_config, _GovernedVNextTrade()
        )
        book_decision = evaluate_vnext_ultimate_book_admission(
            config=shipped_config, intents=[], governor_state=_governor_state()
        )

        rt = shipped_config["gtos_vnext_runtime"]
        assert rt["scheduler_v4_best_trade_allocator_live_activation_allowed"] is False
        assert rt["ultimate_book_live_activation_allowed"] is False

        # Same value, opposite consequence.
        assert scheduler_denial is None            # gate disabled: nothing rejected
        assert book_decision.runtime_effect_now is False   # placement suppressed


# ---------------------------------------------------------------------------
# 3. Profile overlays must not flip an authority gate
# ---------------------------------------------------------------------------

class TestProfileOverlaysDoNotGrantAuthority:
    """`.context/LIVE_STATE.md` renders base config only, with no profile overlay
    (`scripts/generate_live_state.py:394-399`). So an authority gate flipped in a
    profile would be invisible to the document operators read. Assert none is.
    """

    @pytest.mark.parametrize("profile_path", sorted(PROFILE_DIR.glob("*.yaml")))
    def test_no_profile_arms_a_live_authority_gate(self, profile_path):
        data = yaml.safe_load(profile_path.read_text()) or {}
        runtime = (data.get("gtos_vnext_runtime") or {}) if isinstance(data, dict) else {}

        for key, value in runtime.items():
            if key.endswith(("_live_activation_allowed", "_live_broker_authority")):
                assert value is False, (
                    f"{profile_path.name} sets {key} = {value!r}. A profile overlay "
                    "must never grant live authority — LIVE_STATE.md does not render "
                    "profile overlays, so this would be invisible to an operator."
                )

    def test_at_least_one_profile_was_actually_scanned(self):
        """Guards against the parametrize silently collecting nothing."""
        assert len(list(PROFILE_DIR.glob("*.yaml"))) >= 3
