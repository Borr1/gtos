from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = (
    ROOT
    / "src/research_infra/"
    "replay_acceleration_attempt5_typed_sparse_runner.py"
)
CONTRACT_PATH = (
    ROOT
    / "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_SELECTION_SIZING_DECISION_CONTRACT.json"
)
SHA = "a" * 64
SEALED_SEED = timewarp.B7_5_SELECTION_SIZING_FACTORIAL_SEALED_NEUTRAL_SEED_SHA256
PROTOCOL_DENOMINATOR = {
    "initial_equity_cash": (
        timewarp.B7_5_SELECTION_SIZING_FACTORIAL_INITIAL_EQUITY_CASH
    ),
    "fixed_account_risk_unit_pct": (
        timewarp.B7_5_SELECTION_SIZING_FACTORIAL_FIXED_ACCOUNT_RISK_UNIT_PCT
    ),
    "fixed_account_risk_unit_cash": (
        timewarp.B7_5_SELECTION_SIZING_FACTORIAL_FIXED_ACCOUNT_RISK_UNIT_CASH
    ),
    "fixed_denominator_portfolio_r_cash": (
        timewarp.B7_5_SELECTION_SIZING_FACTORIAL_FIXED_DENOMINATOR_PORTFOLIO_R_CASH
    ),
}
PROTOCOL_MATCHED_RISK = dict(
    timewarp.B7_5_SELECTION_SIZING_FACTORIAL_MATCHED_RISK
)
PROTOCOL_ECONOMICS = {
    "denominator": PROTOCOL_DENOMINATOR,
    "matched_risk": PROTOCOL_MATCHED_RISK,
}
PROTOCOL_ECONOMICS_DIGEST_SHA256 = timewarp.stable_sha256(PROTOCOL_ECONOMICS)


def load_harness():
    spec = importlib.util.spec_from_file_location(
        "b7_5_selection_sizing_factorial_harness_test",
        HARNESS_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def arm_binding(arm_id: str) -> dict:
    selection_factor = arm_id[:2]
    sizing_factor = arm_id[2:]
    identity = {
        "decision_contract_sha256": SHA,
        "common_execution_input_digest_sha256": SHA,
        "arm_id": arm_id,
        "arm_fingerprint_sha256": SHA,
        "selection_factor": selection_factor,
        "sizing_factor": sizing_factor,
        "selection_mode": (
            "neutral_hash_hard_eligible"
            if selection_factor == "S0"
            else "quality_ranked_current"
        ),
        "sizing_mode": (
            "fixed_equal_account_risk" if sizing_factor == "R0" else "dynamic_runtime"
        ),
        "neutral_selection_seed_sha256": SEALED_SEED,
        "fixed_account_risk_unit_pct": PROTOCOL_DENOMINATOR[
            "fixed_account_risk_unit_pct"
        ],
    }
    binding_payload = timewarp.b7_5_selection_sizing_factorial_binding_payload(
        **identity,
        protocol_economics=PROTOCOL_ECONOMICS,
        protocol_economics_digest_sha256=(
            PROTOCOL_ECONOMICS_DIGEST_SHA256
        ),
        denominator=PROTOCOL_DENOMINATOR,
        matched_risk=PROTOCOL_MATCHED_RISK,
        **{
            key: value
            for key, value in PROTOCOL_DENOMINATOR.items()
            if key != "fixed_account_risk_unit_pct"
        },
        **PROTOCOL_MATCHED_RISK,
    )
    return {
        "valid": True,
        "decision_contract_path": str(CONTRACT_PATH.relative_to(ROOT)),
        **identity,
        "binding_payload": binding_payload,
        "binding_payload_sha256": timewarp.stable_sha256(binding_payload),
        "protocol_economics": copy.deepcopy(PROTOCOL_ECONOMICS),
        "protocol_economics_digest_sha256": (
            PROTOCOL_ECONOMICS_DIGEST_SHA256
        ),
        "denominator": copy.deepcopy(PROTOCOL_DENOMINATOR),
        **PROTOCOL_DENOMINATOR,
        "matched_risk": copy.deepcopy(PROTOCOL_MATCHED_RISK),
        "uses_outcome_fields": False,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
    }


def runtime_config_for_arm(arm_id: str) -> dict:
    arm = arm_binding(arm_id)
    prefix = timewarp.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX
    runtime = {
        "prop_safe_selector_initial_balance": PROTOCOL_DENOMINATOR[
            "initial_equity_cash"
        ],
        "prop_safe_selector_external_daily_loss_limit_pct": PROTOCOL_MATCHED_RISK[
            "daily_accepted_risk_pct_cap"
        ],
        "scheduler_v4_best_trade_allocator_portfolio_ceiling_pct": (
            PROTOCOL_MATCHED_RISK["peak_open_plus_pending_risk_pct_cap"]
        ),
        "scheduler_v4_best_trade_allocator_correlation_cluster_ceiling_pct": (
            PROTOCOL_MATCHED_RISK["cluster_risk_pct_cap"]
        ),
        "scheduler_v4_best_trade_allocator_dynamic_budget_"
        "opening_window_max_total_risk_pct": PROTOCOL_MATCHED_RISK[
            "opening_window_risk_pct_cap"
        ],
        "scheduler_v4_best_trade_allocator_dynamic_budget_"
        "opening_window_reserve_enabled": True,
        f"{prefix}requested": True,
        f"{prefix}binding_valid": True,
        f"{prefix}binding_payload_sha256": arm["binding_payload_sha256"],
        f"{prefix}protocol_economics_digest_sha256": (
            arm["protocol_economics_digest_sha256"]
        ),
        f"{prefix}uses_outcome_fields": False,
        f"{prefix}live_broker_authority": False,
        f"{prefix}broker_mutation_enabled": False,
        f"{prefix}final_selection_claim": False,
    }
    for key in (
        "decision_contract_sha256",
        "common_execution_input_digest_sha256",
        "arm_id",
        "arm_fingerprint_sha256",
        "selection_factor",
        "sizing_factor",
        "selection_mode",
        "sizing_mode",
        "neutral_selection_seed_sha256",
    ):
        runtime[f"{prefix}{key}"] = arm[key]
    runtime.update(
        {f"{prefix}{key}": value for key, value in PROTOCOL_DENOMINATOR.items()}
    )
    runtime.update(
        {f"{prefix}{key}": value for key, value in PROTOCOL_MATCHED_RISK.items()}
    )
    return {
        "risk": {
            "risk_per_trade_pct": 0.5,
            "max_daily_loss_pct": 4.0,
        },
        "broad_live_as_if_replay_harness": {
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        },
        "gtos_vnext_runtime": runtime,
    }


def test_default_runtime_path_does_not_request_factorial() -> None:
    binding = timewarp.b7_5_selection_sizing_factorial_runtime_binding({})

    assert binding["valid"] is True
    assert binding["enabled"] is False
    assert binding["selection_factor"] == "S1"
    assert binding["sizing_factor"] == "R1"


@pytest.mark.parametrize("arm_id", ["S0R0", "S1R0", "S0R1", "S1R1"])
def test_runtime_binding_accepts_only_hash_bound_broker_closed_arms(arm_id: str) -> None:
    binding = timewarp.b7_5_selection_sizing_factorial_runtime_binding(
        runtime_config_for_arm(arm_id),
        fail_on_invalid=True,
    )

    assert binding["valid"] is True
    assert binding["arm_id"] == arm_id
    assert binding["neutral_selection_seed_sha256"] == SEALED_SEED
    assert binding["protocol_economics"] == PROTOCOL_ECONOMICS
    assert (
        binding["protocol_economics_digest_sha256"]
        == PROTOCOL_ECONOMICS_DIGEST_SHA256
    )
    assert binding["fixed_account_risk_unit_cash"] == 100.0
    assert binding["uses_outcome_fields"] is False


def test_runtime_binding_fails_closed_outside_no_broker_boundary() -> None:
    config = runtime_config_for_arm("S0R0")
    config["broad_live_as_if_replay_harness"]["broker_mutation_enabled"] = True

    with pytest.raises(
        ValueError,
        match="b7_5_selection_sizing_factorial_binding_invalid",
    ):
        timewarp.b7_5_selection_sizing_factorial_runtime_binding(
            config,
            fail_on_invalid=True,
        )


def test_any_partial_prefixed_runtime_binding_fails_closed() -> None:
    prefix = timewarp.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX
    config = {
        "broad_live_as_if_replay_harness": {
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        },
        "gtos_vnext_runtime": {f"{prefix}requested": True},
    }

    binding = timewarp.b7_5_selection_sizing_factorial_runtime_binding(config)

    assert binding["requested"] is True
    assert binding["enabled"] is False
    assert binding["valid"] is False
    assert "binding_not_valid" in binding["failures"]
    with pytest.raises(
        ValueError,
        match="b7_5_selection_sizing_factorial_binding_invalid",
    ):
        timewarp.b7_5_selection_sizing_factorial_runtime_binding(
            config,
            fail_on_invalid=True,
        )


@pytest.mark.parametrize(
    ("field", "value", "expected_failure"),
    [
        (
            "neutral_selection_seed_sha256",
            "f" * 64,
            "neutral_selection_seed_sha256_not_sealed_protocol_seed",
        ),
        (
            "protocol_economics_digest_sha256",
            "f" * 64,
            "protocol_economics_digest_sha256_mismatch",
        ),
        (
            "fixed_account_risk_unit_cash",
            99.0,
            "denominator_not_sealed_protocol_economics",
        ),
        (
            "binding_payload_sha256",
            "malformed",
            "binding_payload_sha256_mismatch",
        ),
    ],
)
def test_malformed_sealed_binding_fields_fail_closed(
    field: str,
    value: object,
    expected_failure: str,
) -> None:
    config = runtime_config_for_arm("S0R0")
    prefix = timewarp.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX
    config["gtos_vnext_runtime"][f"{prefix}{field}"] = value

    binding = timewarp.b7_5_selection_sizing_factorial_runtime_binding(config)

    assert binding["requested"] is True
    assert binding["enabled"] is False
    assert binding["valid"] is False
    assert expected_failure in binding["failures"]
    with pytest.raises(ValueError, match=expected_failure):
        timewarp.b7_5_selection_sizing_factorial_runtime_binding(
            config,
            fail_on_invalid=True,
        )


def test_neutral_rank_is_exact_seed_window_instance_hash() -> None:
    decision_window_id = "2026-06-04T07:30:00+00:00"
    candidate_instance_key = "candidate-a@@2026-06-04T07:30:00+00:00"
    expected = hashlib.sha256(
        f"{SEALED_SEED}|{decision_window_id}|{candidate_instance_key}".encode(
            "utf-8"
        )
    ).hexdigest()

    actual = timewarp.b7_5_selection_sizing_factorial_neutral_rank_sha256(
        seed_sha256=SEALED_SEED,
        decision_window_id=decision_window_id,
        candidate_instance_key=candidate_instance_key,
    )

    assert actual == expected


def test_harness_r0_keeps_base_and_global_risk_configuration_unchanged() -> None:
    harness = load_harness()
    baseline = harness.build_config(harness.PROFILE_REPAIRED)
    incumbent = harness.build_config(
        harness.PROFILE_REPAIRED,
        factorial_arm_binding=arm_binding("S1R1"),
    )
    fixed = harness.build_config(
        harness.PROFILE_REPAIRED,
        factorial_arm_binding=arm_binding("S0R0"),
    )

    assert "b7_5_selection_sizing_factorial_arm_binding" not in baseline[
        "broad_live_as_if_replay_harness"
    ]
    assert incumbent["risk"] == baseline["risk"]
    assert incumbent.get("timewarp_replay_symbol_risk_pct") == baseline.get(
        "timewarp_replay_symbol_risk_pct"
    )
    assert fixed["risk"] == baseline["risk"]
    assert fixed.get("timewarp_replay_symbol_risk_pct") == baseline.get(
        "timewarp_replay_symbol_risk_pct"
    )
    runtime = fixed["gtos_vnext_runtime"]
    prefix = timewarp.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX
    assert runtime[f"{prefix}fixed_account_risk_unit_pct"] == 0.1
    assert runtime[f"{prefix}fixed_account_risk_unit_cash"] == 100.0
    assert (
        runtime[f"{prefix}protocol_economics_digest_sha256"]
        == PROTOCOL_ECONOMICS_DIGEST_SHA256
    )
    assert runtime["scheduler_v4_best_trade_allocator_portfolio_ceiling_pct"] == 4.0
    assert (
        runtime["scheduler_v4_best_trade_allocator_correlation_cluster_ceiling_pct"]
        == 1.5
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_opening_window_max_total_risk_pct"
        ]
        == 1.0
    )
    assert runtime["scheduler_v4_best_trade_allocator_dynamic_daily_drawdown_budget_enabled"] is True


@pytest.mark.parametrize("balance", [90000.0, 100000.0, 110000.0])
def test_r0_final_risk_helper_preserves_fixed_100_cash_across_balances(
    balance: float,
) -> None:
    binding = timewarp.b7_5_selection_sizing_factorial_runtime_binding(
        runtime_config_for_arm("S0R0"),
        fail_on_invalid=True,
    )
    risk_authority = {
        "risk_decision": "trade",
        "risk_decision_reason": "focused_r0_fixed_cash_test",
        "b7_5_selection_sizing_factorial_binding": binding,
    }

    finalized = timewarp.bind_canonical_executable_final_risk_atom(
        risk_authority,
        final_risk_pct=0.1,
        authority_source="focused_r0_fixed_cash_test",
        balance=balance,
    )

    assert finalized["final_approved_risk_pct"] == 0.1
    assert finalized["runtime_final_risk_pct"] == 0.1
    assert finalized["approved_risk_pct"] == 0.1
    assert finalized["risk_cash"] == 100.0
    assert finalized["order_risk_cash"] == 100.0
    cash_detail = finalized["b7_5_selection_sizing_factorial_risk_cash"]
    assert cash_detail["fixed_equal_account_risk_cash_applied"] is True
    assert cash_detail["fixed_account_risk_current_balance_ignored"] == balance
    assert cash_detail["cash_basis_source"] == (
        "sealed_frozen_initial_equity_not_current_balance"
    )


def test_factorial_finalizer_hard_caps_accumulate_ranked_admissions() -> None:
    headroom = {
        "daily_accepted_risk": 0.15,
        "peak_open_plus_pending": 0.15,
        "cluster": 0.15,
        "prop_firm": 0.15,
        "configured_risk_per_trade": 2.0,
    }
    first = timewarp.b7_5_selection_sizing_factorial_finalizer_hard_cap_check(
        hard_headroom_pct=headroom,
        candidate_risk_pct=0.10,
        selected_total_risk_pct=0.0,
        selected_opening_risk_pct=0.0,
        selected_cluster_risk_pct={},
        candidate_cluster="metals",
    )
    second = timewarp.b7_5_selection_sizing_factorial_finalizer_hard_cap_check(
        hard_headroom_pct=headroom,
        candidate_risk_pct=0.10,
        selected_total_risk_pct=0.10,
        selected_opening_risk_pct=0.0,
        selected_cluster_risk_pct={"metals": 0.10},
        candidate_cluster="metals",
    )

    assert first["allowed"] is True
    assert first["failures"] == []
    assert second["allowed"] is False
    assert set(second["failures"]) == {
        "daily_accepted_risk",
        "peak_open_plus_pending",
        "cluster",
        "prop_firm",
    }


def test_factorial_r1_individual_allocator_cannot_override_sealed_hard_caps(
) -> None:
    headroom = {
        "daily_accepted_risk": 2.25,
        "peak_open_plus_pending": 3.75,
        "cluster": 1.5,
        "prop_firm": 4.0,
        "configured_risk_per_trade": 1.0,
        "opening_window": 0.125,
    }
    first = timewarp.b7_5_selection_sizing_factorial_finalizer_hard_cap_check(
        hard_headroom_pct=headroom,
        candidate_risk_pct=0.625,
        selected_total_risk_pct=0.0,
        selected_opening_risk_pct=0.0,
        selected_cluster_risk_pct={},
        candidate_cluster="us_index",
        candidate_individually_admitted_by_sizing_authority=True,
    )
    second = timewarp.b7_5_selection_sizing_factorial_finalizer_hard_cap_check(
        hard_headroom_pct=headroom,
        candidate_risk_pct=0.625,
        selected_total_risk_pct=0.625,
        selected_opening_risk_pct=0.625,
        selected_cluster_risk_pct={"us_index": 0.625},
        candidate_cluster="us_index",
        candidate_individually_admitted_by_sizing_authority=True,
    )

    assert first["allowed"] is False
    assert first["failures"] == ["opening_window"]
    assert first["hard_headroom_pct"]["opening_window"] == 0.125
    assert first["individual_sizing_authority_baseline_pct_by_scope"][
        "opening_window"
    ] == 0.125
    assert first["individual_sizing_authority_baseline_applied_scopes"] == []
    assert second["allowed"] is False
    assert "opening_window" in second["failures"]

    spare_headroom = {
        **headroom,
        "daily_accepted_risk": 0.15,
        "peak_open_plus_pending": 0.15,
        "cluster": 0.15,
        "prop_firm": 0.15,
        "opening_window": 0.15,
    }
    spare_first = timewarp.b7_5_selection_sizing_factorial_finalizer_hard_cap_check(
        hard_headroom_pct=spare_headroom,
        candidate_risk_pct=0.10,
        selected_total_risk_pct=0.0,
        selected_opening_risk_pct=0.0,
        selected_cluster_risk_pct={},
        candidate_cluster="metals",
        candidate_individually_admitted_by_sizing_authority=True,
    )
    spare_second = timewarp.b7_5_selection_sizing_factorial_finalizer_hard_cap_check(
        hard_headroom_pct=spare_headroom,
        candidate_risk_pct=0.10,
        selected_total_risk_pct=0.10,
        selected_opening_risk_pct=0.10,
        selected_cluster_risk_pct={"metals": 0.10},
        candidate_cluster="metals",
        candidate_individually_admitted_by_sizing_authority=True,
    )
    assert spare_first["allowed"] is True
    assert spare_first["individual_sizing_authority_baseline_applied_scopes"] == []
    assert spare_second["allowed"] is False
    assert set(spare_second["failures"]) == {
        "daily_accepted_risk",
        "peak_open_plus_pending",
        "cluster",
        "prop_firm",
        "opening_window",
    }


def test_factorial_r1_daily_cap_cannot_be_crossed_by_individual_admission() -> None:
    result = timewarp.b7_5_selection_sizing_factorial_finalizer_hard_cap_check(
        hard_headroom_pct={
            "daily_accepted_risk": 0.125,
            "peak_open_plus_pending": 4.0,
            "cluster": 1.5,
            "prop_firm": 4.0,
            "configured_risk_per_trade": 2.0,
        },
        candidate_risk_pct=0.50,
        selected_total_risk_pct=0.0,
        selected_opening_risk_pct=0.0,
        selected_cluster_risk_pct={},
        candidate_cluster="us_index",
        candidate_individually_admitted_by_sizing_authority=True,
    )

    assert result["allowed"] is False
    assert result["failures"] == ["daily_accepted_risk"]
    assert result["hard_headroom_pct"]["daily_accepted_risk"] == 0.125
    assert result["individual_sizing_authority_baseline_applied_scopes"] == []


@pytest.mark.parametrize(("arm_id", "risk_pct"), [("S0R0", 0.10), ("S1R1", 0.625)])
def test_factorial_filled_risk_releases_once_at_terminal_close(
    arm_id: str,
    risk_pct: float,
) -> None:
    account = timewarp.AccountState()
    day = "2026-06-04"
    session_key = "ny"
    decision_time_key = "2026-06-04T14:30:00+00:00"
    cluster_key = "us_index"
    side = "LONG"
    account.record_accepted_risk_order(
        day,
        risk_pct,
        session_key=session_key,
        decision_time_key=decision_time_key,
        decision_cluster_key=cluster_key,
        decision_side=side,
    )
    position = {
        "simulated_order_id": f"focused-{arm_id}-order",
        "accepted_risk_reservation_day": day,
        "trading_day": day,
        "risk_pct": risk_pct,
        "reserved_risk_pct": risk_pct,
        "accepted_risk_reservation_released": False,
        "risk_authority": {
            "b7_5_selection_sizing_factorial_binding": (
                timewarp.b7_5_selection_sizing_factorial_runtime_binding(
                    runtime_config_for_arm(arm_id),
                    fail_on_invalid=True,
                )
            ),
            "opening_window_session_counter_key": session_key,
            "decision_time_risk_order_counter_key": decision_time_key,
            "same_decision_cluster_side_risk_order_cluster": cluster_key,
            "same_decision_cluster_side_risk_order_side": side,
        },
    }

    release = account.release_factorial_filled_risk_on_close(
        day=day,
        position=position,
    )

    assert release["accepted_risk_close_release_required"] is True
    assert release["accepted_risk_reservation_released"] is True
    assert release["accepted_risk_released_pct"] == risk_pct
    assert account.accepted_risk_order_count(day) == 0
    assert account.accepted_risk_pct(day) == 0.0
    assert account.accepted_risk_order_count(day, session_key=session_key) == 0
    assert account.accepted_risk_pct(day, session_key=session_key) == 0.0
    assert (
        account.accepted_risk_order_count_for_decision_time(
            day,
            decision_time_key,
        )
        == 0
    )
    assert (
        account.accepted_risk_pct_for_decision_time(day, decision_time_key)
        == 0.0
    )
    assert (
        account.accepted_risk_order_count_for_decision_cluster_side(
            day,
            decision_time_key,
            cluster_key,
            side,
        )
        == 0
    )
    assert (
        account.accepted_risk_pct_for_decision_cluster_side(
            day,
            decision_time_key,
            cluster_key,
            side,
        )
        == 0.0
    )
    with pytest.raises(
        ValueError,
        match="b7_5_selection_sizing_factorial_filled_risk_double_release",
    ):
        account.release_factorial_filled_risk_on_close(
            day=day,
            position=position,
        )


def test_factorial_close_releases_original_day_across_midnight() -> None:
    account = timewarp.AccountState()
    reservation_day = "2026-06-04"
    processing_day = "2026-06-05"
    risk_pct = 0.625
    decision_time_key = "2026-06-04T23:45:00+00:00"
    account.record_accepted_risk_order(
        reservation_day,
        risk_pct,
        session_key="ny",
        decision_time_key=decision_time_key,
        decision_cluster_key="us_index",
        decision_side="LONG",
    )
    position = {
        "simulated_order_id": "cross-midnight-order",
        "accepted_risk_reservation_day": reservation_day,
        "trading_day": reservation_day,
        "risk_pct": risk_pct,
        "reserved_risk_pct": risk_pct,
        "accepted_risk_reservation_released": False,
        "risk_authority": {
            "b7_5_selection_sizing_factorial_binding": (
                timewarp.b7_5_selection_sizing_factorial_runtime_binding(
                    runtime_config_for_arm("S1R1"),
                    fail_on_invalid=True,
                )
            ),
            "opening_window_session_counter_key": "ny",
            "decision_time_risk_order_counter_key": decision_time_key,
            "same_decision_cluster_side_risk_order_cluster": "us_index",
            "same_decision_cluster_side_risk_order_side": "LONG",
        },
    }

    release = account.release_factorial_filled_risk_on_close(
        day=processing_day,
        position=position,
    )

    payload = release["accepted_risk_reservation_release"]
    assert payload["accepted_risk_reservation_day"] == reservation_day
    assert payload["accepted_risk_terminal_processing_day"] == processing_day
    assert payload["accepted_risk_release_day_matches_processing_day"] is False
    assert payload["accepted_risk_exact_release_required"] is True
    assert account.accepted_risk_pct(reservation_day) == 0.0
    assert account.accepted_risk_order_count(reservation_day) == 0
    assert account.accepted_risk_pct(processing_day) == 0.0
    assert account.accepted_risk_order_count(processing_day) == 0


def test_factorial_exact_release_underflow_preserves_reservation_state() -> None:
    account = timewarp.AccountState()
    reservation_day = "2026-06-04"
    account.record_accepted_risk_order(reservation_day, 0.625)
    position = {
        "accepted_risk_reservation_day": "2026-06-05",
        "risk_pct": 0.625,
        "reserved_risk_pct": 0.625,
        "accepted_risk_reservation_released": False,
        "risk_authority": {
            "b7_5_selection_sizing_factorial_binding": (
                timewarp.b7_5_selection_sizing_factorial_runtime_binding(
                    runtime_config_for_arm("S1R1"),
                    fail_on_invalid=True,
                )
            ),
        },
    }

    with pytest.raises(
        ValueError,
        match="accepted_risk_exact_release_day_count_underflow",
    ):
        account.release_factorial_filled_risk_on_close(
            day="2026-06-05",
            position=position,
        )

    assert position["accepted_risk_reservation_released"] is False
    assert account.accepted_risk_order_count(reservation_day) == 1
    assert account.accepted_risk_pct(reservation_day) == 0.625


def test_nonfactorial_filled_close_keeps_legacy_accepted_risk_behavior() -> None:
    account = timewarp.AccountState()
    day = "2026-06-04"
    account.record_accepted_risk_order(day, 0.50)
    position = {
        "simulated_order_id": "legacy-order",
        "risk_pct": 0.50,
        "reserved_risk_pct": 0.50,
        "accepted_risk_reservation_released": False,
        "risk_authority": {},
    }

    release = account.release_factorial_filled_risk_on_close(
        day=day,
        position=position,
    )

    assert release == {
        "accepted_risk_close_release_required": False,
        "accepted_risk_reservation_released": False,
    }
    assert account.accepted_risk_order_count(day) == 1
    assert account.accepted_risk_pct(day) == 0.50


def test_factorial_serialized_risk_lifecycle_audit_reconstructs_sequential_reuse(
    tmp_path: Path,
) -> None:
    harness = load_harness()
    binding = arm_binding("S1R1")
    order_rows = []
    trade_rows = []
    for index, (accept_time, fill_time, close_time) in enumerate(
        (
            (
                "2026-06-04T13:00:00+00:00",
                "2026-06-04T13:01:00+00:00",
                "2026-06-04T13:10:00+00:00",
            ),
            (
                "2026-06-04T13:15:00+00:00",
                "2026-06-04T13:16:00+00:00",
                "2026-06-04T13:25:00+00:00",
            ),
        ),
        start=1,
    ):
        order_id = f"order-{index}"
        risk_authority = {
            "opening_window_session_counter_key": "ny",
            "same_decision_cluster_side_risk_order_cluster": "usd_fx",
            "dynamic_daily_drawdown_budget_allocator": {
                "b7_5_selection_sizing_factorial_hard_cap_package_releases_suppressed": True,
                "opening_window_reserve": {"active": True}
            },
        }
        order_rows.extend(
            (
                {
                    "simulated_order_id": order_id,
                    "accepted_risk_reservation_day": "2026-06-04",
                    "trading_day": "2026-06-04",
                    "order_event_stage": "accepted_pending",
                    "is_terminal_order_event": False,
                    "created_time_utc": accept_time,
                    "reserved_risk_pct": 0.625,
                    "risk_pct": 0.625,
                    "daily_accepted_risk_pct_before": 0.0,
                    "daily_accepted_risk_pct_after": 0.625,
                    "same_decision_cluster_side_risk_order_cluster": "usd_fx",
                    "risk_authority": risk_authority,
                },
                {
                    "simulated_order_id": order_id,
                    "accepted_risk_reservation_day": "2026-06-04",
                    "trading_day": "2026-06-04",
                    "order_event_stage": "terminal_filled",
                    "is_terminal_order_event": True,
                    "order_status": "filled",
                    "event_time_utc": fill_time,
                    "accepted_risk_reservation_released": False,
                    "accepted_risk_reservation_transition": (
                        "pending_order_to_filled_position"
                    ),
                },
            )
        )
        trade_rows.append(
            {
                "simulated_order_id": order_id,
                "accepted_risk_reservation_day": "2026-06-04",
                "trading_day": "2026-06-04",
                "exit_time_utc": close_time,
                "accepted_risk_reservation_released": True,
                "accepted_risk_released_pct": 0.625,
                "accepted_risk_close_release_once_status": (
                    "released_exactly_once_at_terminal_close"
                ),
                "accepted_risk_reservation_release": {
                    "released_risk_pct": 0.625,
                    "accepted_risk_reservation_day": "2026-06-04",
                    "accepted_risk_exact_release_required": True,
                    "day_accepted_risk_pct_before_release": 0.625,
                    "day_accepted_risk_pct_after_release": 0.0,
                },
            }
        )
    order_path = tmp_path / "orders.jsonl"
    trade_path = tmp_path / "trades.jsonl"
    order_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in order_rows) + "\n",
        encoding="utf-8",
    )
    trade_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in trade_rows) + "\n",
        encoding="utf-8",
    )

    audit = harness.selection_sizing_factorial_risk_lifecycle_audit(
        order_path=order_path,
        trade_path=trade_path,
        factorial_arm_binding=binding,
    )

    assert audit["valid"] is True
    assert audit["accepted_order_count"] == 2
    assert audit["pending_to_open_transfer_count"] == 2
    assert audit["close_or_expiry_event_count"] == 2
    assert audit["close_or_expiry_release_count"] == 2
    assert audit["physical_accepted_risk_pct_sum"] == 1.25
    assert audit["peak_daily_accepted_risk_pct"] == 0.625
    assert audit["peak_open_plus_pending_risk_pct"] == 0.625
    assert audit["peak_opening_window_risk_pct"] == 0.625
    assert audit["terminal_daily_accepted_risk_pct"] == 0.0


def test_factorial_serialized_risk_lifecycle_audit_fails_cap_and_close_release(
    tmp_path: Path,
) -> None:
    harness = load_harness()
    order_path = tmp_path / "orders.jsonl"
    trade_path = tmp_path / "trades.jsonl"
    order_path.write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in (
                {
                    "simulated_order_id": "order-1",
                    "accepted_risk_reservation_day": "2026-06-04",
                    "trading_day": "2026-06-04",
                    "order_event_stage": "accepted_pending",
                    "is_terminal_order_event": False,
                    "created_time_utc": "2026-06-04T13:00:00+00:00",
                    "reserved_risk_pct": 1.25,
                    "risk_pct": 1.25,
                    "daily_accepted_risk_pct_before": 0.0,
                    "daily_accepted_risk_pct_after": 1.25,
                    "same_decision_cluster_side_risk_order_cluster": "",
                    "risk_authority": {
                        "opening_window_session_counter_key": "ny",
                        "same_decision_cluster_side_risk_order_cluster": "",
                        "dynamic_daily_drawdown_budget_allocator": {
                            "b7_5_selection_sizing_factorial_hard_cap_package_releases_suppressed": True,
                            "opening_window_reserve": {"active": True}
                        },
                    },
                },
                {
                    "simulated_order_id": "order-1",
                    "accepted_risk_reservation_day": "2026-06-04",
                    "trading_day": "2026-06-04",
                    "order_event_stage": "terminal_filled",
                    "is_terminal_order_event": True,
                    "order_status": "filled",
                    "event_time_utc": "2026-06-04T13:01:00+00:00",
                    "accepted_risk_reservation_released": False,
                    "accepted_risk_reservation_transition": (
                        "pending_order_to_filled_position"
                    ),
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )
    trade_path.write_text(
        json.dumps(
            {
                "simulated_order_id": "order-1",
                "accepted_risk_reservation_day": "2026-06-04",
                "trading_day": "2026-06-04",
                "exit_time_utc": "2026-06-04T13:10:00+00:00",
                "accepted_risk_reservation_released": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    audit = harness.selection_sizing_factorial_risk_lifecycle_audit(
        order_path=order_path,
        trade_path=trade_path,
        factorial_arm_binding=arm_binding("S1R1"),
    )

    assert audit["valid"] is False
    assert audit["close_or_expiry_event_count"] == 1
    assert audit["close_or_expiry_release_count"] == 0
    reasons = {row["reason"] for row in audit["failures"]}
    assert "accepted_risk_cluster_identity_missing" in reasons
    assert "opening_window_risk_cap_breached" in reasons
    assert "trade_close_release_flag_missing" in reasons
    assert "trade_close_release_payload_missing" in reasons


def test_factorial_serialized_risk_lifecycle_audit_proves_unfilled_release(
    tmp_path: Path,
) -> None:
    harness = load_harness()
    order_path = tmp_path / "orders.jsonl"
    trade_path = tmp_path / "trades.jsonl"
    order_path.write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in (
                {
                    "simulated_order_id": "order-expiry",
                    "accepted_risk_reservation_day": "2026-06-04",
                    "trading_day": "2026-06-04",
                    "order_event_stage": "accepted_pending",
                    "is_terminal_order_event": False,
                    "created_time_utc": "2026-06-04T13:00:00+00:00",
                    "reserved_risk_pct": 0.10,
                    "risk_pct": 0.10,
                    "daily_accepted_risk_pct_before": 0.0,
                    "daily_accepted_risk_pct_after": 0.10,
                    "same_decision_cluster_side_risk_order_cluster": "usd_fx",
                    "risk_authority": {
                        "opening_window_session_counter_key": "ny",
                        "same_decision_cluster_side_risk_order_cluster": "usd_fx",
                        "dynamic_daily_drawdown_budget_allocator": {
                            "b7_5_selection_sizing_factorial_hard_cap_package_releases_suppressed": True,
                            "opening_window_reserve": {
                                "active": False,
                                "counter_scope": "configured_session",
                            },
                        },
                    },
                },
                {
                    "simulated_order_id": "order-expiry",
                    "accepted_risk_reservation_day": "2026-06-04",
                    "trading_day": "2026-06-04",
                    "order_event_stage": "terminal_expired_unfilled",
                    "is_terminal_order_event": True,
                    "order_status": "expired_unfilled",
                    "event_time_utc": "2026-06-04T14:00:00+00:00",
                    "accepted_risk_reservation_released": True,
                    "released_risk_pct": 0.10,
                    "accepted_risk_reservation_release": {
                        "released_risk_pct": 0.10,
                        "accepted_risk_reservation_day": "2026-06-04",
                        "accepted_risk_exact_release_required": True,
                        "day_accepted_risk_pct_before_release": 0.10,
                        "day_accepted_risk_pct_after_release": 0.0,
                    },
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )
    trade_path.write_text("", encoding="utf-8")

    audit = harness.selection_sizing_factorial_risk_lifecycle_audit(
        order_path=order_path,
        trade_path=trade_path,
        factorial_arm_binding=arm_binding("S0R0"),
    )

    assert audit["valid"] is True
    assert audit["accepted_order_count"] == 1
    assert audit["pending_to_open_transfer_count"] == 0
    assert audit["close_or_expiry_event_count"] == 1
    assert audit["close_or_expiry_release_count"] == 1
    assert audit["terminal_daily_accepted_risk_pct"] == 0.0


def test_factorial_serialized_risk_lifecycle_audit_scopes_days_and_equal_times(
    tmp_path: Path,
) -> None:
    harness = load_harness()
    risk_pct = 0.625

    def risk_authority() -> dict[str, object]:
        return {
            "opening_window_session_counter_key": "ny",
            "same_decision_cluster_side_risk_order_cluster": "usd_fx",
            "dynamic_daily_drawdown_budget_allocator": {
                "b7_5_selection_sizing_factorial_hard_cap_package_releases_suppressed": True,
                "opening_window_reserve": {
                    "active": False,
                    "counter_scope": "configured_session",
                },
            },
        }

    def release_payload(day: str) -> dict[str, object]:
        return {
            "released_risk_pct": risk_pct,
            "accepted_risk_reservation_day": day,
            "accepted_risk_exact_release_required": True,
            "day_accepted_risk_pct_before_release": risk_pct,
            "day_accepted_risk_pct_after_release": 0.0,
        }

    order_rows = [
        {
            "profile": "profile-a",
            "campaign": "campaign-a",
            "simulated_order_id": "shared-order",
            "accepted_risk_reservation_day": "2026-06-04",
            "trading_day": "2026-06-04",
            "order_event_stage": "accepted_pending",
            "is_terminal_order_event": False,
            "created_time_utc": "2026-06-04T23:59:00+00:00",
            "reserved_risk_pct": risk_pct,
            "risk_pct": risk_pct,
            "daily_accepted_risk_pct_before": 0.0,
            "daily_accepted_risk_pct_after": risk_pct,
            "same_decision_cluster_side_risk_order_cluster": "usd_fx",
            "risk_authority": risk_authority(),
        },
        {
            "profile": "profile-a",
            "campaign": "campaign-a",
            "simulated_order_id": "shared-order",
            "accepted_risk_reservation_day": "2026-06-04",
            "trading_day": "2026-06-05",
            "order_event_stage": "terminal_filled",
            "is_terminal_order_event": True,
            "order_status": "filled",
            "event_time_utc": "2026-06-05T00:01:00+00:00",
            "accepted_risk_reservation_released": False,
            "accepted_risk_reservation_transition": (
                "pending_order_to_filled_position"
            ),
        },
        {
            "profile": "profile-b",
            "campaign": "campaign-b",
            "simulated_order_id": "old-order",
            "accepted_risk_reservation_day": "2026-06-05",
            "trading_day": "2026-06-05",
            "order_event_stage": "accepted_pending",
            "is_terminal_order_event": False,
            "created_time_utc": "2026-06-05T12:00:00+00:00",
            "reserved_risk_pct": risk_pct,
            "risk_pct": risk_pct,
            "daily_accepted_risk_pct_before": 0.0,
            "daily_accepted_risk_pct_after": risk_pct,
            "same_decision_cluster_side_risk_order_cluster": "usd_fx",
            "risk_authority": risk_authority(),
        },
        {
            "profile": "profile-b",
            "campaign": "campaign-b",
            "simulated_order_id": "old-order",
            "accepted_risk_reservation_day": "2026-06-05",
            "trading_day": "2026-06-05",
            "order_event_stage": "terminal_cancelled_replaced_by_scheduler_v4",
            "is_terminal_order_event": True,
            "order_status": "cancelled_replaced_by_scheduler_v4",
            "event_time_utc": "2026-06-05T13:00:00+00:00",
            "accepted_risk_reservation_released": True,
            "released_risk_pct": risk_pct,
            "accepted_risk_reservation_release": release_payload("2026-06-05"),
        },
        {
            "profile": "profile-b",
            "campaign": "campaign-b",
            "simulated_order_id": "shared-order",
            "accepted_risk_reservation_day": "2026-06-05",
            "trading_day": "2026-06-05",
            "order_event_stage": "accepted_pending",
            "is_terminal_order_event": False,
            "created_time_utc": "2026-06-05T13:00:00+00:00",
            "reserved_risk_pct": risk_pct,
            "risk_pct": risk_pct,
            "daily_accepted_risk_pct_before": 0.0,
            "daily_accepted_risk_pct_after": risk_pct,
            "same_decision_cluster_side_risk_order_cluster": "usd_fx",
            "risk_authority": risk_authority(),
        },
        {
            "profile": "profile-b",
            "campaign": "campaign-b",
            "simulated_order_id": "shared-order",
            "accepted_risk_reservation_day": "2026-06-05",
            "trading_day": "2026-06-05",
            "order_event_stage": "terminal_filled",
            "is_terminal_order_event": True,
            "order_status": "filled",
            "event_time_utc": "2026-06-05T13:01:00+00:00",
            "accepted_risk_reservation_released": False,
            "accepted_risk_reservation_transition": (
                "pending_order_to_filled_position"
            ),
        },
    ]
    trade_rows = [
        {
            "profile": "profile-a",
            "campaign": "campaign-a",
            "simulated_order_id": "shared-order",
            "accepted_risk_reservation_day": "2026-06-04",
            "trading_day": "2026-06-05",
            "exit_time_utc": "2026-06-05T00:01:00+00:00",
            "accepted_risk_reservation_released": True,
            "accepted_risk_released_pct": risk_pct,
            "accepted_risk_close_release_once_status": (
                "released_exactly_once_at_terminal_close"
            ),
            "accepted_risk_reservation_release": release_payload("2026-06-04"),
        },
        {
            "profile": "profile-b",
            "campaign": "campaign-b",
            "simulated_order_id": "shared-order",
            "accepted_risk_reservation_day": "2026-06-05",
            "trading_day": "2026-06-05",
            "exit_time_utc": "2026-06-05T13:01:00+00:00",
            "accepted_risk_reservation_released": True,
            "accepted_risk_released_pct": risk_pct,
            "accepted_risk_close_release_once_status": (
                "released_exactly_once_at_terminal_close"
            ),
            "accepted_risk_reservation_release": release_payload("2026-06-05"),
        },
    ]
    order_path = tmp_path / "orders.jsonl"
    trade_path = tmp_path / "trades.jsonl"
    order_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in order_rows) + "\n",
        encoding="utf-8",
    )
    trade_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in trade_rows) + "\n",
        encoding="utf-8",
    )

    audit = harness.selection_sizing_factorial_risk_lifecycle_audit(
        order_path=order_path,
        trade_path=trade_path,
        factorial_arm_binding=arm_binding("S1R1"),
    )

    assert audit["valid"] is True, audit["failures"]
    assert audit["accepted_order_count"] == 3
    assert audit["pending_to_open_transfer_count"] == 2
    assert audit["close_or_expiry_event_count"] == 3
    assert audit["close_or_expiry_release_count"] == 3
    assert audit["risk_scope_count"] == 2
    assert audit["reservation_day_scope_count"] == 2
    assert audit["peak_daily_accepted_risk_pct"] == risk_pct
    assert audit["terminal_daily_accepted_risk_pct"] == 0.0
    assert audit["terminal_pending_risk_pct"] == 0.0
    assert audit["terminal_open_risk_pct"] == 0.0


@pytest.mark.parametrize(
    ("scope", "remaining", "allowed"),
    [
        ("daily_accepted_risk", 0.10, True),
        ("daily_accepted_risk", 0.09, False),
        ("peak_open_plus_pending", 0.10, True),
        ("peak_open_plus_pending", 0.09, False),
        ("cluster", 0.10, True),
        ("cluster", 0.09, False),
        ("opening_window", 0.10, True),
        ("opening_window", 0.09, False),
    ],
)
def test_factorial_fixed_unit_cap_edges_never_fractionally_resize(
    scope: str,
    remaining: float,
    allowed: bool,
) -> None:
    headroom = {
        "daily_accepted_risk": 4.0,
        "peak_open_plus_pending": 4.0,
        "cluster": 1.5,
        "prop_firm": 4.0,
        "configured_risk_per_trade": 2.0,
    }
    headroom[scope] = remaining
    result = timewarp.b7_5_selection_sizing_factorial_finalizer_hard_cap_check(
        hard_headroom_pct=headroom,
        candidate_risk_pct=0.10,
        selected_total_risk_pct=0.0,
        selected_opening_risk_pct=0.0,
        selected_cluster_risk_pct={},
        candidate_cluster="metals",
    )

    assert result["candidate_risk_pct"] == 0.10
    assert result["allowed"] is allowed
    assert (scope in result["failures"]) is (not allowed)


def test_r0_package_signature_check_is_explicit_and_fail_closed() -> None:
    unsigned = timewarp.b7_5_factorial_package_authority_signature_check(
        signed_payload=None,
        authority_hash_before=None,
        authority_hash_after=None,
    )
    assert unsigned["status"] == "signature_not_applicable"
    assert unsigned["hash_invariant"] is None

    payload = {"schema": "focused-signed-payload", "candidate_id": "candidate-a"}
    payload_hash = timewarp.package_new_entry_authority_payload_hash_sha256(payload)
    signed = timewarp.b7_5_factorial_package_authority_signature_check(
        signed_payload=payload,
        authority_hash_before=payload_hash,
        authority_hash_after=payload_hash,
    )
    assert signed["status"] == "signed_payload_hash_valid"
    assert signed["payload_hash_valid"] is True

    with pytest.raises(ValueError, match="payload_hash_presence_mismatch"):
        timewarp.b7_5_factorial_package_authority_signature_check(
            signed_payload=payload,
            authority_hash_before=None,
            authority_hash_after=None,
        )
    with pytest.raises(ValueError, match="hash_changed_by_risk_stamp"):
        timewarp.b7_5_factorial_package_authority_signature_check(
            signed_payload=payload,
            authority_hash_before="f" * 64,
            authority_hash_after=payload_hash,
        )


def test_dynamic_package_cap_release_is_audit_only_under_all_factorial_arms() -> None:
    assert timewarp.b7_5_factorial_dynamic_package_cap_release_allowed(
        factorial_contract_bound=False,
        factorial_fixed_equal_risk_applied=False,
        configured_enabled=True,
        package_release_eligible=True,
    ) is True
    assert timewarp.b7_5_factorial_dynamic_package_cap_release_allowed(
        factorial_contract_bound=True,
        factorial_fixed_equal_risk_applied=True,
        configured_enabled=True,
        package_release_eligible=True,
    ) is False
    assert timewarp.b7_5_factorial_dynamic_package_cap_release_allowed(
        factorial_contract_bound=True,
        factorial_fixed_equal_risk_applied=False,
        configured_enabled=True,
        package_release_eligible=True,
    ) is False


def test_attempt5_decision_contract_loader_recomputes_s0r0_fingerprint() -> None:
    harness = load_harness()
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    arm = next(
        row
        for row in contract["factorial_contract"]["arms"]
        if row["arm_id"] == "S0R0"
    )
    args = argparse.Namespace(
        decision_contract=str(CONTRACT_PATH.relative_to(ROOT)),
        arm_id="S0R0",
        expected_arm_fingerprint_sha256=arm["arm_fingerprint_sha256"],
        runtime_evidence_root=Path("/Users/borr/GTOSActive/repo"),
    )

    binding = harness.selection_sizing_factorial_binding_from_args(args)

    assert binding is not None
    assert binding["valid"] is True
    assert binding["arm_id"] == "S0R0"
    assert binding["selection_factor"] == "S0"
    assert binding["sizing_factor"] == "R0"
    assert binding["neutral_selection_seed_sha256"] == SEALED_SEED
    assert binding["protocol_economics"] == PROTOCOL_ECONOMICS
    assert (
        binding["protocol_economics_digest_sha256"]
        == PROTOCOL_ECONOMICS_DIGEST_SHA256
    )
    assert binding["binding_payload_sha256"] == timewarp.stable_sha256(
        binding["binding_payload"]
    )
    assert binding["uses_outcome_fields"] is False
