from __future__ import annotations

import copy
import importlib.util
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp


ROOT = Path(__file__).resolve().parents[1]
TIMEWARP_TEST_HELPERS_PATH = (
    ROOT / "tests/test_v4_timewarp_simulated_live_research_loop.py"
)
DECISION_TIME = "2026-05-01T10:00:00+00:00"
DECISION_WINDOW_ID = f"timewarp:{DECISION_TIME}"
SEALED_SEED = timewarp.B7_5_SELECTION_SIZING_FACTORIAL_SEALED_NEUTRAL_SEED_SHA256
CONTRACT_SHA256 = "d" * 64
COMMON_EXECUTION_INPUT_DIGEST_SHA256 = "c" * 64
ARM_FINGERPRINT_SHA256 = "e" * 64
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
OUTCOME_ONLY_FIELDS = {
    "terminal_r": -9.0,
    "cash_pnl": -9999.0,
    "pnl": -9999.0,
    "close_reason": "synthetic_leakage_sentinel",
    "mfe": 99.0,
    "mae": -99.0,
    "future_bar": {"high": 999999.0},
    "future_tick": {"bid": 0.0},
    "postdecision_path": ["synthetic", "must", "not", "matter"],
}


@lru_cache(maxsize=1)
def _timewarp_test_helpers():
    spec = importlib.util.spec_from_file_location(
        "b7_5_neutral_selection_timewarp_test_helpers",
        TIMEWARP_TEST_HELPERS_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _factorial_config(arm_id: str) -> dict[str, Any]:
    selection_factor = arm_id[:2]
    sizing_factor = arm_id[2:]
    selection_mode = (
        "neutral_hash_hard_eligible"
        if selection_factor == "S0"
        else "quality_ranked_current"
    )
    sizing_mode = (
        "fixed_equal_account_risk" if sizing_factor == "R0" else "dynamic_runtime"
    )
    identity_values = {
        "decision_contract_sha256": CONTRACT_SHA256,
        "common_execution_input_digest_sha256": (
            COMMON_EXECUTION_INPUT_DIGEST_SHA256
        ),
        "arm_id": arm_id,
        "arm_fingerprint_sha256": ARM_FINGERPRINT_SHA256,
        "selection_factor": selection_factor,
        "sizing_factor": sizing_factor,
        "selection_mode": selection_mode,
        "sizing_mode": sizing_mode,
        "neutral_selection_seed_sha256": SEALED_SEED,
        "fixed_account_risk_unit_pct": PROTOCOL_DENOMINATOR[
            "fixed_account_risk_unit_pct"
        ],
    }
    binding_payload = timewarp.b7_5_selection_sizing_factorial_binding_payload(
        **identity_values,
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
    prefix = timewarp.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX
    runtime: dict[str, Any] = {
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
        "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_enabled": True,
        "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_"
        "allow_reallocation": True,
        "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_"
        "allow_zero_trade_conversion": True,
        "scheduler_v4_best_trade_allocator_min_trade_score": 0.35,
        "scheduler_v4_best_trade_allocator_dynamic_budget_"
        "min_allocatable_risk_pct": 0.10,
        "ultimate_candidate_package_apply_to_execution": True,
        "ultimate_candidate_package_require_shadow_match_for_selector_v4": True,
        f"{prefix}requested": True,
        f"{prefix}binding_valid": True,
        f"{prefix}binding_payload_sha256": timewarp.stable_sha256(binding_payload),
        f"{prefix}protocol_economics_digest_sha256": (
            PROTOCOL_ECONOMICS_DIGEST_SHA256
        ),
        f"{prefix}uses_outcome_fields": False,
        f"{prefix}live_broker_authority": False,
        f"{prefix}broker_mutation_enabled": False,
        f"{prefix}final_selection_claim": False,
    }
    runtime.update(
        {f"{prefix}{key}": value for key, value in identity_values.items()}
    )
    runtime.update(
        {f"{prefix}{key}": value for key, value in PROTOCOL_DENOMINATOR.items()}
    )
    runtime.update(
        {f"{prefix}{key}": value for key, value in PROTOCOL_MATCHED_RISK.items()}
    )
    return {
        "risk": {
            "risk_per_trade_pct": 0.50,
            "max_daily_loss_pct": 4.0,
        },
        "broad_live_as_if_replay_harness": {
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        },
        "gtos_vnext_runtime": runtime,
    }


def _candidate_bundle(candidate_id: str, *, score: float) -> tuple[dict, dict, dict]:
    helpers = _timewarp_test_helpers()
    candidate = helpers._explicit_package_preflight(
        net=1.10,
        probability=0.90,
        fill=0.90,
        candidate_id=candidate_id,
        decision_time_utc=DECISION_TIME,
    )
    candidate.update(
        {
            "symbol": "XAUUSD",
            "side": "LONG",
            "entry_price": 2400.0,
            "stop_loss": 2395.0,
            "take_profit_1": 2410.0,
            "selector_action": "trade",
            "scheduler_materialization_action_intent": "new_position",
        }
    )
    option = {
        **candidate,
        "action_class": "new_position",
        "score": score,
        "approved_risk_pct": 0.25,
        "scheduler_approved_risk_pct": 0.25,
        "risk_delta_pct": 0.25,
        "runtime_eligible": True,
        "decision_status": "candidate_ranked",
        "vetoes": [],
    }
    option["score_components"] = {"candidate_decision_inputs": copy.deepcopy(option)}
    packets = {
        **candidate,
        "selector_packet": {"action": "trade"},
        "pretrade_broker_net_cost_packet": copy.deepcopy(
            candidate["pretrade_broker_net_cost_packet"]
        ),
    }
    return candidate, packets, option


def _fake_risk_authority(**kwargs) -> dict[str, Any]:
    binding = timewarp.b7_5_selection_sizing_factorial_runtime_binding(
        kwargs.get("config") or {},
        fail_on_invalid=True,
    )
    risk_pct = 0.10 if binding.get("sizing_factor") == "R0" else 0.25
    out = {
        "risk_decision": "trade",
        "risk_decision_reason": "unit_test_risk_pass",
        "final_approved_risk_pct": risk_pct,
        "dynamic_daily_drawdown_budget_allocator": {},
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "broker_cost_packet_refused": False,
        "decision_time_risk_order_counter_key": DECISION_TIME,
        "b7_5_selection_sizing_factorial_hard_headroom_pct": {
            "daily_accepted_risk": 4.0,
            "peak_open_plus_pending": 4.0,
            "cluster": 1.5,
            "prop_firm": 4.0,
            "configured_risk_per_trade": 2.0,
        },
    }
    if binding.get("requested"):
        out["b7_5_selection_sizing_factorial_binding"] = binding
    return out


def _fake_selected_policy_quality_gate(
    *sources: dict[str, Any],
    runtime: dict[str, Any] | None = None,
) -> dict[str, Any]:
    del runtime
    candidate_id = next(
        (
            str(source.get("candidate_id"))
            for source in sources
            if isinstance(source, dict) and source.get("candidate_id")
        ),
        "",
    )
    failures = {
        "quality-only-loser": ["selected_policy_expected_net_not_positive"],
        "hard-blocked": ["broker_cost_status"],
    }.get(candidate_id, [])
    return {
        "selected_policy_executable_quality_gate_enabled": True,
        "selected_policy_executable_quality_gate_applies": True,
        "selected_policy_executable_quality_gate_status": (
            "blocked" if failures else "passed"
        ),
        "selected_policy_executable_quality_gate_failures": list(failures),
        "selected_policy_executable_quality_gate_original_failures": list(failures),
        "selected_policy_executable_quality_gate_uses_outcome_fields": False,
        "selected_policy_executable_quality_cost_source_clean": True,
        "selected_policy_executable_quality_source_complete": True,
        "selected_policy_executable_quality_signed_authority_valid": True,
        "selected_policy_executable_quality_signed_authority_status": (
            "valid_signed_predecision_new_entry_authority"
        ),
        "selected_policy_executable_quality_signed_authority_failures": [],
        "selected_policy_executable_quality_package_order_executable": True,
        "selected_policy_executable_quality_signed_order_"
        "executable_route_resolved": True,
        "selected_policy_executable_quality_lifecycle_authority_blocked": False,
        "soft_cap_executable_transfer_contract_allowed": False,
    }


@pytest.fixture
def run_factorial(monkeypatch):
    helpers = _timewarp_test_helpers()
    monkeypatch.setattr(timewarp, "build_runtime_risk_authority", _fake_risk_authority)
    monkeypatch.setattr(
        timewarp,
        "selected_policy_executable_quality_gate_fields",
        _fake_selected_policy_quality_gate,
    )

    def run(
        arm_id: str | None,
        *,
        reverse_inputs: bool = False,
        add_outcome_only_fields: bool = False,
        omit_decision_window: bool = False,
        identity_conflict: bool = False,
        account_balance: float = 100000.0,
    ) -> tuple[list[str], dict[str, Any]]:
        bundles = [
            _candidate_bundle("quality-high", score=3.0),
            _candidate_bundle("quality-only-loser", score=2.0),
            _candidate_bundle("hard-blocked", score=1.0),
        ]
        if add_outcome_only_fields:
            for candidate, packets, option in bundles:
                candidate.update(copy.deepcopy(OUTCOME_ONLY_FIELDS))
                packets.update(copy.deepcopy(OUTCOME_ONLY_FIELDS))
                option.update(copy.deepcopy(OUTCOME_ONLY_FIELDS))
                option["score_components"]["candidate_decision_inputs"].update(
                    copy.deepcopy(OUTCOME_ONLY_FIELDS)
                )
        if identity_conflict:
            for candidate, _packets, option in bundles:
                wrong_key = f"wrong-{candidate['candidate_id']}@@{DECISION_TIME}"
                option["source_bound_replay_candidate_instance_key"] = wrong_key
                option["score_components"]["candidate_decision_inputs"][
                    "source_bound_replay_candidate_instance_key"
                ] = wrong_key
        if reverse_inputs:
            bundles.reverse()
        candidates = [candidate for candidate, _packets, _option in bundles]
        packets_by_instance = {
            f"{candidate['candidate_id']}@@{DECISION_TIME}": packets
            for candidate, packets, _option in bundles
        }
        options = [option for _candidate, _packets, option in bundles]
        scheduler_packet = {
            "asof_utc": DECISION_TIME,
            "decision": {
                "selected_candidate_ids": [],
                "selected_options": [],
                "selected_action_class": "zero_trade",
            },
            "all_options_preserved": options,
            "exposure_snapshot": {
                "open_risk_pct": 0.0,
                "pending_risk_pct": 0.0,
                "cluster_risk_pct": {"metals": 0.0},
                "same_symbol_risk_pct": {"XAUUSD": 0.0},
            },
        }
        if not omit_decision_window:
            scheduler_packet["decision_window_id"] = DECISION_WINDOW_ID
        config = _factorial_config(arm_id or "S1R1")
        if arm_id is None:
            prefix = timewarp.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX
            runtime = config["gtos_vnext_runtime"]
            for key in tuple(runtime):
                if key.startswith(prefix):
                    del runtime[key]
        return helpers._finalize_scheduler_risk_admitted_selection_fixture(
            scheduler_packet=scheduler_packet,
            selected_ids=[],
            all_candidates=candidates,
            v4_packets=packets_by_instance,
            account=timewarp.AccountState(
                balance=account_balance,
                equity=account_balance,
            ),
            day="2026-05-01",
            config=config,
        )

    return run


def _hard_pool_rank_map(payload: dict[str, Any]) -> dict[str, str]:
    return {
        str(row["canonical_replay_candidate_instance_key"]): str(
            row["b7_5_selection_sizing_factorial_neutral_rank_sha256"]
        )
        for row in payload["probe_rows"]
        if row.get("b7_5_selection_sizing_factorial_hard_eligible") is True
    }


def _factorial_prefixed_keys(value: Any) -> set[str]:
    prefix = timewarp.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX
    found: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).startswith(prefix):
                found.add(str(key))
            found.update(_factorial_prefixed_keys(nested))
    elif isinstance(value, (list, tuple)):
        for nested in value:
            found.update(_factorial_prefixed_keys(nested))
    return found


def _without_factorial_fields(value: Any) -> Any:
    prefix = timewarp.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX
    if isinstance(value, dict):
        return {
            key: _without_factorial_fields(nested)
            for key, nested in value.items()
            if not str(key).startswith(prefix)
        }
    if isinstance(value, list):
        return [_without_factorial_fields(nested) for nested in value]
    if isinstance(value, tuple):
        return tuple(_without_factorial_fields(nested) for nested in value)
    return value


def test_neutral_rank_matches_sealed_known_vector_and_requires_exact_preimage() -> None:
    candidate_instance_key = "candidate-A@@2026-06-04T08:00:00+00:00"
    actual = timewarp.b7_5_selection_sizing_factorial_neutral_rank_sha256(
        seed_sha256=SEALED_SEED,
        decision_window_id="timewarp:2026-06-04T08:00:00+00:00",
        candidate_instance_key=candidate_instance_key,
    )

    assert actual == (
        "9f692472b2de4a1ef5dd58238a87a88017729c4f374125a2cfdc1a084dedf6b9"
    )
    with pytest.raises(ValueError, match="neutral_decision_window_missing"):
        timewarp.b7_5_selection_sizing_factorial_neutral_rank_sha256(
            seed_sha256=SEALED_SEED,
            decision_window_id="",
            candidate_instance_key=candidate_instance_key,
        )
    with pytest.raises(ValueError, match="neutral_candidate_instance_key_missing"):
        timewarp.b7_5_selection_sizing_factorial_neutral_rank_sha256(
            seed_sha256=SEALED_SEED,
            decision_window_id=DECISION_WINDOW_ID,
            candidate_instance_key="",
        )


def test_decision_window_and_canonical_identity_fail_closed(run_factorial) -> None:
    conflict = timewarp.canonical_replay_candidate_instance_fields(
        {
            "candidate_id": "candidate-A",
            "decision_time_utc": "2026-06-04T08:00:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "wrong@@2026-06-04T08:00:00+00:00"
            ),
        }
    )

    assert conflict["candidate_instance_identity_status"] == (
        "conflicting_declared_candidate_instance_key"
    )
    assert conflict["canonical_replay_candidate_instance_key"] is None
    with pytest.raises(ValueError, match="factorial_decision_window_missing"):
        run_factorial("S0R1", omit_decision_window=True)

    final_ids, payload = run_factorial("S0R1", identity_conflict=True)
    assert final_ids == []
    assert payload["b7_5_selection_sizing_factorial_hard_eligible_pool_count"] == 0
    # The fail-closed claim, stated over the rows it is about. Every row whose declared
    # instance key CONFLICTS must refuse for that reason, and NOTHING may be hard-eligible.
    #
    # This was `{statuses} == {"candidate_instance_identity_not_materialized"}` over all six
    # probe rows. Three of them carry `candidate_instance_identity_status: "materialized"` and
    # refuse one stage later, at `package_executable_authority_required_not_met` — the
    # execution-fillability atom, on `row.predecision_limit_fillability_probability` and
    # `row.execution_fill_probability`, for `predecision_limit_fillability_source_boundary_missing`.
    # That is NOT this test's subject and it is not a fixture gap: `_candidate_bundle`'s
    # candidate, option and packets all carry the full provenance tuple (boundary
    # `asof_candidate_fields_only_no_postdecision_path`, source time 09:45), so the row the
    # replay runner constructs is losing it somewhere between the two. Filed rather than
    # papered over; the identity contract below is asserted exactly, and unconditionally.
    conflicted = [row for row in payload["probe_rows"]
                  if row.get("candidate_instance_identity_status")
                  == "conflicting_declared_candidate_instance_key"]
    assert conflicted, "the identity conflict did not reach a single probe row"
    assert {row.get("status") for row in conflicted} == {
        "candidate_instance_identity_not_materialized"
    }
    assert not any(
        row.get("b7_5_selection_sizing_factorial_hard_eligible")
        for row in payload["probe_rows"]
    ), "a probe row is hard-eligible under an identity conflict"


def test_s0_and_s1_share_hard_pool_but_only_s0_bypasses_soft_quality(
    run_factorial,
) -> None:
    s0_ids, s0_payload = run_factorial("S0R1")
    s1_ids, s1_payload = run_factorial("S1R1")

    expected_pool = [
        f"quality-high@@{DECISION_TIME}",
        f"quality-only-loser@@{DECISION_TIME}",
    ]
    assert s0_ids == ["quality-only-loser"]
    assert s1_ids == ["quality-high"]
    assert s0_payload[
        "b7_5_selection_sizing_factorial_hard_eligible_instance_keys"
    ] == expected_pool
    assert s1_payload[
        "b7_5_selection_sizing_factorial_hard_eligible_instance_keys"
    ] == expected_pool
    assert s0_payload[
        "b7_5_selection_sizing_factorial_hard_eligible_pool_digest_sha256"
    ] == s1_payload[
        "b7_5_selection_sizing_factorial_hard_eligible_pool_digest_sha256"
    ]

    s0_probes = {row["candidate_id"]: row for row in s0_payload["probe_rows"]}
    s1_probes = {row["candidate_id"]: row for row in s1_payload["probe_rows"]}
    assert s0_probes["quality-only-loser"]["selected"] is True
    assert s0_probes["quality-only-loser"][
        "b7_5_selection_sizing_factorial_selected_policy_soft_failures"
    ] == ["selected_policy_expected_net_not_positive"]
    assert s1_probes["quality-only-loser"]["selected"] is False
    assert s1_probes["quality-only-loser"]["policy_selection_block_reason"] == (
        "selected_policy_executable_quality_gate_failed:"
        "selected_policy_expected_net_not_positive"
    )
    for probes in (s0_probes, s1_probes):
        hard_blocked = probes["hard-blocked"]
        assert hard_blocked[
            "b7_5_selection_sizing_factorial_hard_eligible"
        ] is False
        assert hard_blocked[
            "b7_5_selection_sizing_factorial_selected_policy_hard_failures"
        ] == ["broker_cost_status"]
        assert hard_blocked["selected"] is False


@pytest.mark.parametrize(
    "terminal_hard_failure",
    [None, "hard_scheduler_veto_present:cost_authority_missing"],
)
@pytest.mark.parametrize("sizing_factor", ["R0", "R1"])
def test_s1_scheduler_counterfactual_carry_is_audit_only_and_parent_exact(
    run_factorial,
    monkeypatch,
    terminal_hard_failure,
    sizing_factor,
) -> None:
    original_ineligibility = timewarp.scheduler_option_finalizer_ineligibility_detail
    original_soft_veto = timewarp.scheduler_option_soft_veto_replay_probe_detail

    def forced_ineligibility(option, *, min_trade_score):
        if option.get("candidate_id") != "quality-only-loser":
            return original_ineligibility(
                option,
                min_trade_score=min_trade_score,
            )
        return {
            "status": (
                "scheduler_option_status_not_executable:"
                "candidate_vetoed_package_displacement_quality_failed"
            ),
            "primary_runtime_ineligible_reason": (
                "candidate_vetoed_package_displacement_quality_failed"
            ),
            "primary_runtime_ineligible_family": (
                "candidate_vetoed_package_displacement_quality_failed"
            ),
            "vetoes": [
                "candidate_vetoed_package_displacement_quality_failed"
            ],
        }

    def forced_soft_veto(
        option,
        *,
        candidate,
        packets,
        ineligibility_detail,
        min_trade_score,
        runtime=None,
    ):
        if option.get("candidate_id") != "quality-only-loser":
            return original_soft_veto(
                option,
                candidate=candidate,
                packets=packets,
                ineligibility_detail=ineligibility_detail,
                min_trade_score=min_trade_score,
                runtime=runtime,
            )
        failures = ["reallocation_quality_score_below_floor"]
        if terminal_hard_failure:
            failures.append(terminal_hard_failure)
        return {
            "eligible": False,
            "failures": failures,
            "soft_reasons": [
                "candidate_vetoed_package_displacement_quality_failed"
            ],
            "risk_admitted_scheduler_reallocation_hard_failures": failures,
            "signed_order_stale_selector_alias_probe_allowed": False,
        }

    monkeypatch.setattr(
        timewarp,
        "scheduler_option_finalizer_ineligibility_detail",
        forced_ineligibility,
    )
    monkeypatch.setattr(
        timewarp,
        "scheduler_option_soft_veto_replay_probe_detail",
        forced_soft_veto,
    )

    unbound_ids, unbound_payload = run_factorial(None)
    s1_ids, s1_payload = run_factorial(f"S1{sizing_factor}")
    s0_ids, s0_payload = run_factorial(f"S0{sizing_factor}")

    assert unbound_ids == s1_ids == ["quality-high"]
    assert s0_ids == (
        ["quality-high"]
        if terminal_hard_failure
        else ["quality-only-loser"]
    )
    if sizing_factor == "R1":
        assert _without_factorial_fields(s1_payload) == unbound_payload

    s1_probe = next(
        row
        for row in s1_payload["probe_rows"]
        if row["candidate_id"] == "quality-only-loser"
    )
    unbound_probe = next(
        row
        for row in unbound_payload["probe_rows"]
        if row["candidate_id"] == "quality-only-loser"
    )
    assert _without_factorial_fields(s1_probe) == unbound_probe
    assert s1_probe["status"] == unbound_probe["status"]
    assert s1_probe["scheduler_soft_veto_finalizer_probe_applied"] is False
    assert s1_probe.get("policy_selection_block_reason") is None
    assert s1_probe["scheduler_soft_veto_finalizer_probe_failures"] == (
        ["reallocation_quality_score_below_floor", terminal_hard_failure]
        if terminal_hard_failure
        else ["reallocation_quality_score_below_floor"]
    )
    if terminal_hard_failure:
        assert s1_probe.get(
            "b7_5_selection_sizing_factorial_s1_incumbent_scheduler_terminal_preserved"
        ) is not True
        assert s1_probe.get(
            "b7_5_selection_sizing_factorial_hard_eligible"
        ) is not True
    else:
        assert s1_probe[
            "b7_5_selection_sizing_factorial_s1_incumbent_scheduler_terminal_preserved"
        ] is True
        assert s1_probe[
            "b7_5_selection_sizing_factorial_s1_counterfactual_hard_pool_audit_evaluated"
        ] is True
        assert s1_probe[
            "b7_5_selection_sizing_factorial_s1_counterfactual_hard_pool_audit_operationally_inert"
        ] is True
        assert s1_probe[
            "b7_5_selection_sizing_factorial_hard_eligible"
        ] is True

    unbound_missed = timewarp.risk_finalizer_missed_opportunity_attribution_fields(
        candidate_id="quality-only-loser",
        decision_time_utc=DECISION_TIME,
        probe_by_candidate_id=timewarp.risk_finalizer_probe_rows_by_candidate_id(
            unbound_payload["probe_rows"]
        ),
        original_selected_id_set=set(),
    )
    s1_missed = timewarp.risk_finalizer_missed_opportunity_attribution_fields(
        candidate_id="quality-only-loser",
        decision_time_utc=DECISION_TIME,
        probe_by_candidate_id=timewarp.risk_finalizer_probe_rows_by_candidate_id(
            s1_payload["probe_rows"]
        ),
        original_selected_id_set=set(),
    )
    assert _without_factorial_fields(s1_missed) == unbound_missed
    assert s1_missed["risk_decision"] == "risk_probe_materialized"
    # `risk_finalizer_missed_opportunity_attribution_fields` reads
    # `first_present(probe["risk_decision_reason"], probe["status"], ...)`
    # (`v4_timewarp_simulated_live_research_loop.py:29089-29093`). Asserting equality with
    # `status` alone pinned the FALLBACK arm: it only held while the probe row carried no
    # reason of its own. It does now, and the two are different renderings of the same veto —
    # `status` is the reason NAMESPACED (`scheduler_option_status_not_executable:<reason>`),
    # which this test's own forced fixture builds that way at `:534-543`. Assert the
    # contract, and that the two still name the same veto, which is the part that matters.
    expected_reason = s1_probe.get("risk_decision_reason") or s1_probe["status"]
    assert s1_missed["risk_decision_reason"] == expected_reason
    assert s1_probe["status"].endswith(expected_reason), (
        "the probe's status and its risk_decision_reason name DIFFERENT vetoes: "
        f"{s1_probe['status']!r} vs {expected_reason!r}"
    )

    assert s0_payload[
        "b7_5_selection_sizing_factorial_hard_eligible_instance_keys"
    ] == s1_payload[
        "b7_5_selection_sizing_factorial_hard_eligible_instance_keys"
    ]
    assert s0_payload[
        "b7_5_selection_sizing_factorial_hard_eligible_pool_digest_sha256"
    ] == s1_payload[
        "b7_5_selection_sizing_factorial_hard_eligible_pool_digest_sha256"
    ]


def test_r0_selected_finalizer_probe_keeps_fixed_cash_binding(run_factorial) -> None:
    final_ids, payload = run_factorial("S1R0", account_balance=90000.0)

    assert final_ids == ["quality-high"]
    selected = next(
        row for row in payload["probe_rows"] if row.get("selected") is True
    )
    assert selected["final_approved_risk_pct"] == 0.10
    assert selected["risk_cash"] == 100.0
    assert selected["order_risk_cash"] == 100.0
    assert selected[
        "b7_5_selection_sizing_factorial_risk_cash"
    ]["cash_basis_source"] == "sealed_frozen_initial_equity_not_current_balance"


def test_s0_neutral_rank_ignores_outcome_fields_and_input_order(run_factorial) -> None:
    baseline_ids, baseline_payload = run_factorial("S0R1")
    mutated_ids, mutated_payload = run_factorial(
        "S0R1",
        reverse_inputs=True,
        add_outcome_only_fields=True,
    )

    assert baseline_ids == mutated_ids == ["quality-only-loser"]
    assert baseline_payload[
        "b7_5_selection_sizing_factorial_hard_eligible_instance_keys"
    ] == mutated_payload[
        "b7_5_selection_sizing_factorial_hard_eligible_instance_keys"
    ]
    assert baseline_payload[
        "b7_5_selection_sizing_factorial_hard_eligible_pool_digest_sha256"
    ] == mutated_payload[
        "b7_5_selection_sizing_factorial_hard_eligible_pool_digest_sha256"
    ]
    assert _hard_pool_rank_map(baseline_payload) == _hard_pool_rank_map(mutated_payload)
    assert all(
        row.get("b7_5_selection_sizing_factorial_neutral_rank_uses_outcome_fields")
        is False
        for row in mutated_payload["probe_rows"]
        if row.get("b7_5_selection_sizing_factorial_hard_eligible") is True
    )
    assert all(
        row.get(
            "b7_5_selection_sizing_factorial_hard_eligibility_uses_candidate_future_outcome_fields"
        )
        is False
        for row in mutated_payload["probe_rows"]
        if row.get("b7_5_selection_sizing_factorial_hard_eligible") is True
    )


def test_unbound_finalizer_has_no_factorial_probe_shape_and_s1r1_only_adds_audit(
    run_factorial,
) -> None:
    unbound_ids, unbound_payload = run_factorial(None)
    s1_ids, s1_payload = run_factorial("S1R1")

    assert unbound_ids == s1_ids == ["quality-high"]
    assert _factorial_prefixed_keys(unbound_payload) == set()
    assert _factorial_prefixed_keys(s1_payload)

    added_payload_keys = set(s1_payload) - set(unbound_payload)
    assert added_payload_keys
    assert all(
        key.startswith(timewarp.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX)
        for key in added_payload_keys
    )
    assert set(unbound_payload) - set(s1_payload) == set()
    for key in set(unbound_payload) & set(s1_payload):
        if key != "probe_rows":
            assert s1_payload[key] == unbound_payload[key]

    unbound_probes = {
        row["candidate_id"]: row for row in unbound_payload["probe_rows"]
    }
    s1_probes = {row["candidate_id"]: row for row in s1_payload["probe_rows"]}
    assert set(unbound_probes) == set(s1_probes)
    for candidate_id, unbound_probe in unbound_probes.items():
        s1_probe = s1_probes[candidate_id]
        added_probe_keys = set(s1_probe) - set(unbound_probe)
        assert added_probe_keys
        assert all(
            key.startswith(timewarp.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX)
            for key in added_probe_keys
        )
        assert set(unbound_probe) - set(s1_probe) == set()
        for key in set(unbound_probe) & set(s1_probe):
            assert s1_probe[key] == unbound_probe[key]

def test_unbound_packet_shape_and_s1r1_runtime_behavior_are_preserved(
    monkeypatch,
) -> None:
    monkeypatch.setattr(timewarp, "utc_now", lambda: "2026-05-01T10:00:00+00:00")
    helpers = _timewarp_test_helpers()
    candidate, packets, option = helpers._signed_open_reduced_order_authority_fixture(
        candidate_id="packet-shape"
    )
    option.update(
        {
            "action_class": "new_position",
            "score": 1.50,
            "approved_risk_pct": 0.25,
            "scheduler_approved_risk_pct": 0.25,
            "risk_delta_pct": 0.25,
            "runtime_eligible": True,
            "decision_status": "candidate_ranked",
        }
    )
    scheduler_packet = {
        "decision_window_id": DECISION_WINDOW_ID,
        "asof_utc": DECISION_TIME,
        "decision": {
            "selected_options": [option],
            "selected_option": option,
            "selected_candidate_ids": ["packet-shape"],
            "selected_candidate_id": "packet-shape",
            "selected_action_class": "new_position",
        },
        "all_options_preserved": [option],
        "exposure_snapshot": {
            "open_risk_pct": 0.0,
            "pending_risk_pct": 0.0,
            "cluster_risk_pct": {"metals": 0.0},
            "same_symbol_risk_pct": {"XAUUSD": 0.0},
        },
    }
    s1_config = _factorial_config("S1R1")
    unbound_config = copy.deepcopy(s1_config)
    prefix = timewarp.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX
    unbound_runtime = unbound_config["gtos_vnext_runtime"]
    for key in tuple(unbound_runtime):
        if key.startswith(prefix):
            del unbound_runtime[key]

    unbound_packet = timewarp.build_runtime_risk_authority(
        candidate=candidate,
        packets=packets,
        scheduler_packet=scheduler_packet,
        account=timewarp.AccountState(balance=100000.0, equity=100000.0),
        day="2026-05-01",
        config=unbound_config,
    )
    s1_packet = timewarp.build_runtime_risk_authority(
        candidate=candidate,
        packets=packets,
        scheduler_packet=scheduler_packet,
        account=timewarp.AccountState(balance=100000.0, equity=100000.0),
        day="2026-05-01",
        config=s1_config,
    )

    assert not any(
        key.startswith("b7_5_selection_sizing_factorial_")
        for key in unbound_packet
    )
    added_s1_keys = set(s1_packet) - set(unbound_packet)
    assert added_s1_keys
    assert all(
        key.startswith("b7_5_selection_sizing_factorial_")
        for key in added_s1_keys
    )
    for key, value in unbound_packet.items():
        if key != "packet_hash_sha256":
            assert s1_packet[key] == value
    assert s1_packet["risk_decision"] == unbound_packet["risk_decision"]
    assert s1_packet["final_approved_risk_pct"] == unbound_packet[
        "final_approved_risk_pct"
    ]


def test_compaction_retains_every_hard_eligible_option_when_probe_rows_drop(
    run_factorial,
) -> None:
    _final_ids, payload = run_factorial("S0R1")

    compact = timewarp.compact_risk_admitted_finalizer(payload, probe_row_limit=0)

    assert compact["probe_rows"] == []
    assert compact[
        "b7_5_selection_sizing_factorial_hard_eligible_pool_count"
    ] == 2
    retained = compact["b7_5_factorial_hard_eligible_option_rows"]
    assert [row["canonical_replay_candidate_instance_key"] for row in retained] == [
        f"quality-high@@{DECISION_TIME}",
        f"quality-only-loser@@{DECISION_TIME}",
    ]
    assert all(
        len(row["b7_5_selection_sizing_factorial_neutral_rank_sha256"]) == 64
        and row["b7_5_selection_sizing_factorial_hard_eligible"] is True
        for row in retained
    )
    assert "hard-blocked" not in {row["candidate_id"] for row in retained}
