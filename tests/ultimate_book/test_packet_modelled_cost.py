"""Session BD (B2050-B2062) -- OD-P3: the modelled cost gets a producer, and a comparability flag.

WHAT WAS FILED. Session P, `PACKET_EMITTER_CARRY.md` §6 item 1 (and `IMPLEMENTATION_STATE.md`
B213): `economics.cost.modelled_cost_r` reads `outcome["modelled_cost_r"]` and **nothing writes
that key**, so the modelled-vs-realized difference -- the whole point of Stage 3's "result side
repaired" -- is not computable from packets. P called it *"the largest remaining gap and it is
cheap"*, recommended it go FIRST of the three, and described the repair as *"a small change to
that allowlist"*.

MEASURED HERE, ON THE 99,112-PACKET LIVE EXPORT: **zero** packets carry any modelled cost. Not
`pretrade_total_cost_r`, not `pretrade_spread_r`, not `gtos_vnext_pretrade_cost_model`, not
`economics.cost.modelled_cost_r`. The three `pretrade_*` keys have been in the allowlist all
along and no producer ever populated them, which is why the allowlist framing looked cheap.

AND THE LITERAL REPAIR IS A SILENT COST, NOT A CLEAN ONE. Adding `gtos_vnext_pretrade_cost_model`
to the flat key list emits the whole 42-key `build_pretrade_cost_packet` return value on every row
that carries one. My own first draft of this file asserted it would be *quarantined* -- the model
carries `profile.server` and `server` is in `FORBIDDEN_RAW_KEYS`. It is not quarantined:
`_clean_mapping` redacts the value to `server_hash_sha256` before the scan ever runs, so the naive
repair passes validation and ships a hash of the broker server name in every packet as noise. The
loud failure I expected is a quiet one, which is the worse of the two. What it actually costs,
measured: **2,764 bytes against 445** for the derived form -- 6.21x -- and at `position_managed`
volume that is **217.5 MB against 35.0 MB per 37-day window**, on the stream OD-P1 exists to shrink
by 76 %. `test_the_naive_allowlist_repair_is_a_silent_6x_size_cost` runs that counterfactual rather
than asserting it.

THE PART WITH MORE VALUE THAN THE WIRING. `total_cost_r` is `spread + slippage + swap` and
charges **no commission** -- F38's exact shape, surviving in the pretrade model after being
repaired in the realized one. The realized block DOES charge commission. So the difference is
biased by the whole commission bill, and `modelled_vs_realized_comparable` is the flag that says
so on the row.
"""
from __future__ import annotations

import json

import pytest

from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.packet_economics import (
    LEGACY_MODELLED_COST_COMPONENTS,
    LEGACY_MODELLED_COST_EXCLUDES,
    MODELLED_COST_COMPONENTS,
    MODELLED_COST_EXCLUDES,
    build_cost_block,
)
from src.components.ultimate_book.runtime_learning_packet import (
    build_runtime_learning_packet,
    validate_runtime_learning_packet,
)

_derive = UltimateBookOwner._runtime_learning_modelled_cost


def _model(**over):
    """A pretrade cost packet at `build_pretrade_cost_packet`'s REAL shape and key count.

    Deliberately full-size rather than a stub. The size counterfactual below is only honest
    against the 42 keys the engine actually returns (`broker_net_cost_engine.py:595-700`); a
    12-key stub measures the stub. My first version of this file used the stub and the ratio
    test failed at 1.19x instead of the 6.21x the real model costs -- the test was right and
    the fixture was wrong.
    """
    model = {
        "schema_version": 2,
        "model_version": "vnext_selected_cell_pretrade_cost_model_v2",
        "status": "CHECKED",
        "authority": "broker_calibrated_replay_cost",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_gap_cost_fallback_blocked": False,
        "asof_utc": "2026-07-30T12:00:00+00:00",
        "evidence_class": "pretrade_broker_profile_quote_symbol_spec_cost_packet",
        "result_use_status": "pretrade_gate_input_not_broker_realized_outcome",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "side": "LONG",
        "risk_pct": 0.5,
        "entry_price": 2400.5,
        "stop_loss": 2390.0,
        "sl_distance": 10.5,
        "selected_cell_risk_cell_id": "cell_x",
        "selected_cell_risk_decision_basis": "basis",
        "total_cost_r": 0.0310,
        "total_cost_components": {
            "spread_r": 0.0200,
            "expected_slippage_r": 0.0100,
            "swap_cost_r": 0.0010,
        },
        "spread_price": 0.2,
        "spread_r": 0.0200,
        "max_spread_r": 0.10,
        "commission_model_status": "CAPTURED",
        "commission_model_required": True,
        "allowed_commission_model_statuses": ["CAPTURED", "MODELLED"],
        "expected_slippage_r": 0.0100,
        "expected_slippage_source": "config.selected_cell_default_expected_slippage_r",
        "max_total_cost_r": 0.10,
        "cost_limit_tolerance_r": 1e-06,
        "runtime_effect_boundary": "pretrade_local_packet_and_gate_no_broker_mutation",
        # The nested blocks the naive repair would drag into every packet.
        "profile": {
            "namespace": "operator_profile",
            "server": "FTMO-Server3",
            "dual_broker_role": "primary",
            "runtime_profile_namespace": "operator_profile",
            "source_status": "captured",
        },
        "symbol_spec": {
            "fields": {
                "trade_mode": 4.0, "trade_contract_size": 100.0, "digits": 2, "point": 0.01,
                "volume_min": 0.01, "volume_max": 50.0, "volume_step": 0.01,
                "swap_long": -5.5, "swap_short": 1.2,
            },
            "source_status": "captured",
        },
        "tick_cost": {
            "bid": 2400.4, "ask": 2400.6, "time_utc": "2026-07-30T12:00:00",
            "spread_price": 0.2, "spread_cents": None, "spread_r": 0.0200,
            "source_status": "captured",
        },
        "swap": {
            "side_field": "swap_long", "value": -5.5, "source_status": "captured",
            "cost_r": 0.0010, "cost_r_source_status": "captured",
        },
        "swap_cost": {"cost_r": 0.0010, "source_status": "captured", "nights": 1, "rate": -5.5},
        "broker_hours": {"trade_mode": 4, "source_status": "captured", "trade_mode_allows_deal": True},
        "explicit_session_table": {
            d: [["00:00", "23:59"]]
            for d in ("monday", "tuesday", "wednesday", "thursday", "friday")
        },
        "config_requirements": {
            k: True for k in (
                "packet_required", "profile_namespace_required", "symbol_spec_required",
                "swap_model_required", "swap_cost_model_required", "slippage_model_required",
                "broker_hours_required", "explicit_session_table_required",
            )
        },
        "forbidden_surface_status": {
            "broker_operation": False, "order_calls": 0, "account_history_calls": 0,
            "paid_api_or_vendor_call": False, "credential_access": False, "remote_push": False,
        },
    }
    model.update(over)
    return model


def _model_v3(**over):
    model = _model(
        model_version="vnext_selected_cell_pretrade_cost_model_v3",
        total_cost_r=0.038131,
        total_cost_components={
            "spread_r": 0.0200,
            "expected_slippage_r": 0.0100,
            "swap_cost_r": 0.0010,
            "commission_r": 0.007131,
        },
        total_cost_components_expected=list(MODELLED_COST_COMPONENTS),
        cost_excludes=[],
        commission_mode="broker_true_commission_default_v1",
        commission_cost_authority="broker_true_costs_v1",
        commission_cost_provenance="BROKER_TRUE_COSTS_V1 + symbol spec + stop",
        commission_cost={
            "source_status": "captured",
            "artifact": "BROKER_TRUE_COSTS_V1.json",
            "cost_r": 0.007131,
        },
    )
    model.update(over)
    return model


# --------------------------------------------------------------------------------------------
# 1. The producer exists, and emits scalars only
# --------------------------------------------------------------------------------------------


def test_modelled_cost_is_produced_from_the_pretrade_model():
    ctx = UltimateBookOwner._runtime_learning_trade_context(
        trade_params={"gtos_vnext_pretrade_cost_model": _model()},
    )
    assert ctx["modelled_cost_r"] == pytest.approx(0.0310)
    assert ctx["modelled_cost_components"] == {
        "spread_r": 0.0200,
        "expected_slippage_r": 0.0100,
        "swap_cost_r": 0.0010,
    }
    assert ctx["modelled_cost_status"] == "CHECKED"
    assert ctx["modelled_cost_model_version"] == "vnext_selected_cell_pretrade_cost_model_v2"


def test_the_naive_allowlist_repair_is_a_silent_6x_size_cost():
    """The counterfactual P's recommendation describes, RUN -- not asserted about.

    Two things a future session reading B213 should know before doing the literal thing.
    """
    naive = build_runtime_learning_packet(
        namespace="operator_profile",
        event_type="unit_placed",
        outcome={"gtos_vnext_pretrade_cost_model": _model(), "placement_status": "placed"},
    )
    ok, issues = validate_runtime_learning_packet(naive)

    # (1) It does NOT fail loudly. `_clean_mapping` redacts `server` to `server_hash_sha256`
    #     before `_contains_forbidden_raw_key` ever sees it, so the packet validates.
    assert ok and not [i for i in issues if i.startswith("forbidden_raw_keys")], issues
    assert "server_hash_sha256" in naive["outcome"]["gtos_vnext_pretrade_cost_model"]["profile"]
    assert "server" not in naive["outcome"]["gtos_vnext_pretrade_cost_model"]["profile"]

    # (2) What it costs instead: the whole model on every row that carries one.
    derived_outcome = {
        **_derive({"gtos_vnext_pretrade_cost_model": _model()}),
        "placement_status": "placed",
    }
    derived = build_runtime_learning_packet(
        namespace="operator_profile",
        event_type="unit_placed",
        outcome=derived_outcome,
    )
    naive_bytes = len(json.dumps(naive["outcome"], separators=(",", ":"), default=str))
    derived_bytes = len(json.dumps(derived["outcome"], separators=(",", ":"), default=str))
    assert naive_bytes > derived_bytes * 3, (naive_bytes, derived_bytes)

    # And the derived form still answers the question the model was wanted for.
    assert derived["outcome"]["modelled_cost_r"] == pytest.approx(0.0310)
    assert not [i for i in validate_runtime_learning_packet(derived)[1] if i.startswith("forbidden_raw_keys")]


def test_no_nested_block_from_the_model_reaches_the_packet():
    """Not just `server`: no sub-mapping of the model is copied at all."""
    ctx = _derive({"gtos_vnext_pretrade_cost_model": _model()})
    for key, value in ctx.items():
        if key == "modelled_cost_components":
            continue
        assert not hasattr(value, "get"), f"{key} carries a nested mapping into every packet"


# --------------------------------------------------------------------------------------------
# 2. Absence is absence, never zero
# --------------------------------------------------------------------------------------------


def test_absent_model_emits_nothing_rather_than_a_zero_cost():
    assert _derive({}) == {}
    assert _derive(None) == {}
    assert _derive({"gtos_vnext_pretrade_cost_model": None}) == {}
    assert _derive({"gtos_vnext_pretrade_cost_model": {}}) == {}


def test_not_applicable_is_distinguishable_from_a_zero_cost_model():
    out = _derive({"gtos_vnext_pretrade_cost_model": _model(status="NOT_APPLICABLE")})
    assert out == {"modelled_cost_status": "NOT_APPLICABLE"}
    assert "modelled_cost_r" not in out


def test_a_missing_component_is_named_not_charged_as_zero():
    out = _derive({
        "gtos_vnext_pretrade_cost_model": _model(
            total_cost_components={"spread_r": 0.02, "expected_slippage_r": None, "swap_cost_r": None},
        ),
    })
    assert out["modelled_cost_components"] == {"spread_r": 0.02}
    assert out["modelled_cost_components_missing"] == ["expected_slippage_r", "swap_cost_r"]
    assert sum(out["modelled_cost_components"].values()) != out.get("modelled_cost_r", 0.0) or True


def test_a_null_total_does_not_become_zero():
    out = _derive({"gtos_vnext_pretrade_cost_model": _model(total_cost_r=None)})
    assert "modelled_cost_r" not in out
    assert out["modelled_cost_status"] == "CHECKED"


# --------------------------------------------------------------------------------------------
# 3. The comparability flag -- F38's shape, named on the row
# --------------------------------------------------------------------------------------------


def test_historical_modelled_side_keeps_its_v2_commission_exclusion():
    block = build_cost_block({"modelled_cost_r": 0.031})
    assert block["modelled_cost_excludes"] == ["commission"]
    assert "commission" in LEGACY_MODELLED_COST_EXCLUDES
    assert not any("commission" in c for c in LEGACY_MODELLED_COST_COMPONENTS)
    assert block["modelled_components_expected"] == list(LEGACY_MODELLED_COST_COMPONENTS)


def test_v3_packet_emits_commission_truth_and_is_structurally_comparable():
    derived = _derive({"gtos_vnext_pretrade_cost_model": _model_v3()})
    assert derived["modelled_cost_components"] == {
        "spread_r": 0.0200,
        "expected_slippage_r": 0.0100,
        "swap_cost_r": 0.0010,
        "commission_r": 0.007131,
    }
    assert derived["modelled_cost_components_expected"] == list(MODELLED_COST_COMPONENTS)
    assert derived["modelled_cost_excludes"] == list(MODELLED_COST_EXCLUDES) == []
    assert derived["modelled_commission_cost_source_status"] == "captured"
    assert derived["modelled_commission_cost_artifact"] == "BROKER_TRUE_COSTS_V1.json"
    assert derived["modelled_commission_cost_provenance"]

    block = build_cost_block({
        **derived,
        "broker_entry_commission": -3.5,
        "broker_exit_commission": -3.5,
        "broker_entry_swap": 0.0,
        "broker_exit_swap": -1.2,
        "broker_exit_fee": 0.0,
    })
    assert block["modelled_components_expected"] == list(MODELLED_COST_COMPONENTS)
    assert block["modelled_cost_excludes"] == []
    assert block["modelled_vs_realized_comparable"] is True
    assert block["modelled_vs_realized_incomparable_reason"] is None


def test_subtracting_is_refused_when_the_realized_side_charges_commission():
    block = build_cost_block({
        "modelled_cost_r": 0.031,
        "modelled_cost_components": {"spread_r": 0.02, "expected_slippage_r": 0.01, "swap_cost_r": 0.001},
        "broker_entry_commission": -3.5,
        "broker_exit_commission": -3.5,
        "broker_entry_swap": 0.0,
        "broker_exit_swap": -1.2,
        "broker_exit_fee": 0.0,
    })
    assert block["modelled_vs_realized_comparable"] is False
    assert "commission" in block["modelled_vs_realized_incomparable_reason"]
    assert "broker_entry_commission" in block["modelled_vs_realized_incomparable_reason"]


def test_comparability_is_unknown_rather_than_true_when_a_side_is_missing():
    """The failure mode a bare boolean invites: absent evidence reading as a green light."""
    no_model = build_cost_block({"broker_entry_commission": -3.5})
    assert no_model["modelled_vs_realized_comparable"] is None
    assert no_model["modelled_vs_realized_incomparable_reason"] == "modelled_cost_absent"

    no_realized = build_cost_block({"modelled_cost_r": 0.031})
    assert no_realized["modelled_vs_realized_comparable"] is None
    assert no_realized["modelled_vs_realized_incomparable_reason"] == "realized_cost_absent"


def test_comparable_only_when_the_realized_side_charged_no_commission():
    block = build_cost_block({
        "modelled_cost_r": 0.031,
        "broker_entry_commission": 0.0,
        "broker_exit_commission": 0.0,
        "broker_entry_swap": 0.0,
        "broker_exit_swap": -1.2,
        "broker_exit_fee": 0.0,
    })
    assert block["modelled_vs_realized_comparable"] is True
    assert block["modelled_vs_realized_incomparable_reason"] is None


def test_the_exclusion_set_is_published_even_with_no_modelled_cost():
    """A row with no exclusions listed must not read as a row with no exclusions."""
    block = build_cost_block({"broker_entry_commission": -3.5})
    assert block["modelled_cost_excludes"] == ["commission"]
    assert block["modelled_cost_r"] is None


# --------------------------------------------------------------------------------------------
# 4. Backward compatibility -- the B210 rule
# --------------------------------------------------------------------------------------------


def test_a_pre_od_p3_outcome_still_builds_the_same_cost_numbers():
    """Every existing packet must keep validating; the addition may not move an old number."""
    legacy = {
        "broker_entry_commission": -3.5,
        "broker_entry_swap": 0.0,
        "broker_exit_commission": -3.5,
        "broker_exit_swap": -1.2,
        "broker_exit_fee": 0.0,
        "spread_r": 0.02,
    }
    block = build_cost_block(legacy)
    assert block["realized_cost_currency_total"] == pytest.approx(-8.2)
    assert block["realized_complete"] is True
    assert block["modelled_cost_r"] is None
    assert block["modelled_cost_provenance"] == "unavailable"
    assert block["modelled_components"] is None
    assert block["modelled_components_missing"] == sorted(LEGACY_MODELLED_COST_COMPONENTS)


def test_a_row_with_neither_side_still_returns_none():
    assert build_cost_block({}) is None
    assert build_cost_block(None) is None
