from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import pytest


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO
    / "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "compare_b7_5_causal_risk_pair.py"
)
SPEC = importlib.util.spec_from_file_location("compare_b7_5_causal_risk_pair", MODULE_PATH)
assert SPEC and SPEC.loader
pair = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pair
SPEC.loader.exec_module(pair)


SHARED = "a" * 64
PROFILE_HASH = "b" * 64
HOSTILE_SOURCE = "c" * 64
NON_HOSTILE_SOURCE = "d" * 64
HOSTILE_DAY = "2026-05-15"
NON_HOSTILE_DAY = "2026-06-04"
SYMBOLS = [f"SYMBOL_{index:02d}" for index in range(24)]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    )


def candidate_key(label: str, day: str) -> str:
    return f"candidate_{label}@@{day}T12:00:00+00:00"


def make_trade(
    label: str,
    day: str,
    *,
    net_r: float,
    cash_pnl: float,
    cap: bool,
    requires_base_fragility: bool,
    base_fragile: bool = False,
    headline: bool = True,
) -> dict[str, Any]:
    expected_cost_r = 0.1
    final_r = net_r + expected_cost_r
    risk_pct = 0.1 if cap else 0.5
    return {
        "canonical_replay_candidate_instance_key": candidate_key(label, day),
        "candidate_id": f"candidate_{label}",
        "decision_time_utc": f"{day}T12:00:00+00:00",
        "symbol": "XAUUSD",
        "direction": "LONG",
        "terminal_r_scoreable": True,
        "net_proxy_r": net_r,
        "gross_r": final_r,
        "final_r": final_r,
        "expected_cost_r": expected_cost_r,
        "total_execution_cost_r": expected_cost_r,
        "pnl_cash": cash_pnl,
        "risk_cash": 100.0,
        "risk_pct": risk_pct,
        "headline_result_eligible": headline,
        "risk_expression_ladder_tier": "reduced" if cap else "full",
        "broker_pretrade_cost_executable": True,
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "predecision_stop_hazard_guard_status": "capped" if cap else "passed",
        "predecision_stop_hazard_guard_configured_action": "cap" if cap else "no_block",
        "predecision_stop_hazard_guard_effective_action": "cap" if cap else "no_block",
        "predecision_stop_hazard_guard_effective_cap": cap,
        "predecision_stop_hazard_guard_risk_cap_applied": cap,
        "predecision_stop_hazard_guard_risk_cap_pct": 0.1 if cap else None,
        "predecision_stop_hazard_guard_pressure_triggered": cap,
        "predecision_stop_hazard_guard_pressure_requires_base_fragility": (
            requires_base_fragility
        ),
        "predecision_stop_hazard_guard_unit_risk_atr": 0.2 if base_fragile else 0.4,
        "predecision_stop_hazard_guard_min_unit_risk_atr": 0.35,
        "simulated_trade_id": f"trade_{label}",
        "simulated_order_id": f"order_{label}",
        "order_status": "filled",
        "fill_status": "filled",
    }


def make_unscoreable_trade(label: str, day: str) -> dict[str, Any]:
    row = make_trade(
        label,
        day,
        net_r=0.0,
        cash_pnl=0.0,
        cap=False,
        requires_base_fragility=True,
        headline=False,
    )
    row.update(
        {
            "terminal_r_scoreable": False,
            "net_proxy_r": None,
            "gross_r": None,
            "final_r": None,
            "terminal_r_unscoreable_reason": "ordered_tick_source_gap",
        }
    )
    return row


def make_projection(
    label: str,
    day: str,
    *,
    trade: bool,
    missed: bool,
    scorecard: bool = True,
    scheduler: bool = True,
    order: bool = True,
    decision_time: str | None = None,
) -> dict[str, Any]:
    timestamp = decision_time or f"{day}T12:00:00+00:00"
    key_day = timestamp[:10]
    return {
        "candidate_instance_parity_key": candidate_key(label, key_day),
        "candidate_id": f"candidate_{label}",
        "decision_time_utc": timestamp,
        "symbol": "XAUUSD",
        "side": "LONG",
        "candidate_present": True,
        "scorecard_present": scorecard,
        "scheduler_selected": scheduler,
        "order_present": order,
        "trade_present": trade,
        "missed_present": missed,
        "effective_selector_action": "trade",
        "effective_selector_reason": "synthetic_test_authority",
        "risk_behavior": "full" if trade else "hold",
        "risk_finalizer_action": "trade" if trade else "hold",
        "order_status": "filled" if trade else "expired",
        "terminal_fill_status": "filled" if trade else "not_filled",
        "terminal_outcome": "target" if trade else None,
        "miss_reason": "synthetic_miss" if missed else None,
    }


def make_missed(
    label: str,
    day: str,
    *,
    scope: str,
    net_r: float | None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "canonical_replay_candidate_instance_key": candidate_key(label, day),
        "candidate_id": f"candidate_{label}",
        "decision_time_utc": f"{day}T12:00:00+00:00",
        "symbol": "XAUUSD",
        "direction": "LONG",
        "miss_reason": "synthetic_miss",
    }
    if scope == "executable":
        row["missed_opportunity_r_scoreability_status"] = "headline_r_scoreable"
        row["net_proxy_r"] = net_r
    elif scope == "diagnostic":
        row[
            "missed_opportunity_r_scoreability_status"
        ] = "diagnostic_opportunity_r_scoreable"
        row["opportunity_net_proxy_r"] = net_r
    else:
        row[
            "missed_opportunity_r_scoreability_status"
        ] = "ordered_tick_source_gap_unscoreable"
    return row


def target_summary(
    day: str,
    *,
    source_digest: str,
    trades: list[dict[str, Any]],
    projections: list[dict[str, Any]],
    missed: list[dict[str, Any]],
) -> dict[str, Any]:
    rollup = pair.trade_rollup(trades)
    split_stats = dict(rollup)
    # Canonical split stats name headline cash simply `cash_pnl`; physical cash
    # remains separately serialized as `physical_cash_pnl`.
    split_stats["cash_pnl"] = split_stats.pop("headline_cash_pnl")
    return {
        "status": "broad_live_as_if_replay_materialized_broker_live_closed",
        "date_start": day,
        "date_end": day,
        "selected_day_count": 1,
        "max_candidates_per_symbol_window": 0,
        "candidate_generation_authority": "uncapped_full_authority",
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
        "candidate_rows": len(projections),
        "scorecard_rows": sum(bool(row.get("scorecard_present")) for row in projections),
        "missed_opportunity_rows": len(missed),
        "trade_rows": len(trades),
        "b7_5_contract_binding": {
            "valid": True,
            "actual_shared_execution_contract_digest_sha256": SHARED,
            "actual_source_plan_digests_sha256": [source_digest],
        },
        "shared_execution_contract": {
            "shared_execution_contract_digest_sha256": SHARED,
            "effective_profile_config_hashes": {
                pair.PROFILE: PROFILE_HASH,
            },
            "active_replay_symbol_universe": SYMBOLS,
            "execution_options": {"max_candidates_per_symbol_window": 0},
        },
        "source_authority_chunk_invariance_contract": {
            "all_chunk_source_plans_match_canonical": True,
            "all_source_plans_valid": True,
        },
        "physical_trade_summary_serialized_ledger_parity_contract": {
            "canonical_result_ledger_normalization_before_summary": True,
            "scoreable_unscoreable_cost_partition_required": True,
            "serialized_trade_ledger_is_physical_summary_authority": True,
        },
        "split_profile_stats": [{"profile": pair.PROFILE, **split_stats}],
    }


def write_surface(
    root: Path,
    prefix: str,
    day: str,
    *,
    source_digest: str,
    trades: list[dict[str, Any]],
    projections: list[dict[str, Any]],
    missed: list[dict[str, Any]],
    extra_projection_rows: list[dict[str, Any]] | None = None,
    write_projection: bool = True,
    write_missed: bool = True,
) -> None:
    write_json(
        root / f"{prefix}_SUMMARY.json",
        target_summary(
            day,
            source_digest=source_digest,
            trades=trades,
            projections=projections,
            missed=missed,
        ),
    )
    write_jsonl(root / f"{prefix}_TRADE_LEDGER.jsonl", trades)
    write_jsonl(root / f"{prefix}_ORDER_LEDGER.jsonl", trades)
    if write_projection:
        write_jsonl(
            pair.projection_path(root, prefix),
            [*projections, *(extra_projection_rows or [])],
        )
    if write_missed:
        write_jsonl(root / f"{prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl", missed)


class Scenario:
    hostile_baseline = "BROAD_LIVE_AS_IF_REPLAY_HOSTILE_BASELINE"
    hostile_candidate = "BROAD_LIVE_AS_IF_REPLAY_HOSTILE_CANDIDATE"
    non_hostile_baseline = "BROAD_LIVE_AS_IF_REPLAY_NON_HOSTILE_BASELINE"
    non_hostile_candidate = "BROAD_LIVE_AS_IF_REPLAY_NON_HOSTILE_CANDIDATE"

    def __init__(self, root: Path) -> None:
        self.root = root

    def config(self, **overrides: Any) -> Any:
        values = {
            "artifact_root": self.root,
            "hostile_prefix": self.hostile_candidate,
            "hostile_baseline_prefix": self.hostile_baseline,
            "hostile_day": HOSTILE_DAY,
            "non_hostile_prefix": self.non_hostile_candidate,
            "non_hostile_baseline_prefix": self.non_hostile_baseline,
            "non_hostile_day": NON_HOSTILE_DAY,
            "expected_shared_execution_contract_sha256": SHARED,
            "expected_profile_config_sha256": PROFILE_HASH,
            "expected_hostile_source_plan_sha256": HOSTILE_SOURCE,
            "expected_non_hostile_source_plan_sha256": NON_HOSTILE_SOURCE,
            "expected_hostile_pressure_cohort_count": 1,
            "expected_non_hostile_pressure_cohort_count": 1,
            "require_hostile_projection": True,
            "output_prefix": "TEST_B7_5_PAIR",
        }
        values.update(overrides)
        return pair.AnalyzerConfig(**values)

    def write_pair(
        self,
        *,
        day: str,
        source_digest: str,
        baseline_prefix: str,
        candidate_prefix: str,
        baseline_net: float = 1.0,
        baseline_cash: float = 100.0,
        candidate_net: float = 2.0,
        candidate_cash: float = 200.0,
        candidate_filled: bool = True,
        candidate_present: bool = True,
        candidate_cap: bool = False,
        candidate_requires_base: bool = True,
        candidate_base_fragile: bool = False,
        candidate_missed_scope: str = "executable",
        candidate_missed_r: float = 1.0,
        baseline_extra_projection: list[dict[str, Any]] | None = None,
        candidate_extra_projection: list[dict[str, Any]] | None = None,
    ) -> None:
        label = "hostile" if day == HOSTILE_DAY else "non_hostile"
        baseline_trade = make_trade(
            label,
            day,
            net_r=baseline_net,
            cash_pnl=baseline_cash,
            cap=True,
            requires_base_fragility=False,
        )
        baseline_projection = make_projection(
            label, day, trade=True, missed=False
        )
        write_surface(
            self.root,
            baseline_prefix,
            day,
            source_digest=source_digest,
            trades=[baseline_trade],
            projections=[baseline_projection],
            missed=[],
            extra_projection_rows=baseline_extra_projection,
        )

        candidate_trades: list[dict[str, Any]] = []
        candidate_missed: list[dict[str, Any]] = []
        candidate_projections: list[dict[str, Any]] = []
        if candidate_present:
            candidate_projections.append(
                make_projection(
                    label,
                    day,
                    trade=candidate_filled,
                    missed=not candidate_filled,
                )
            )
        if candidate_filled:
            candidate_trades.append(
                make_trade(
                    label,
                    day,
                    net_r=candidate_net,
                    cash_pnl=candidate_cash,
                    cap=candidate_cap,
                    requires_base_fragility=candidate_requires_base,
                    base_fragile=candidate_base_fragile,
                )
            )
        elif candidate_present:
            candidate_missed.append(
                make_missed(
                    label,
                    day,
                    scope=candidate_missed_scope,
                    net_r=candidate_missed_r,
                )
            )
        write_surface(
            self.root,
            candidate_prefix,
            day,
            source_digest=source_digest,
            trades=candidate_trades,
            projections=candidate_projections,
            missed=candidate_missed,
            extra_projection_rows=candidate_extra_projection,
        )

    def write_standard(self, **non_hostile_overrides: Any) -> None:
        self.write_pair(
            day=HOSTILE_DAY,
            source_digest=HOSTILE_SOURCE,
            baseline_prefix=self.hostile_baseline,
            candidate_prefix=self.hostile_candidate,
        )
        self.write_pair(
            day=NON_HOSTILE_DAY,
            source_digest=NON_HOSTILE_SOURCE,
            baseline_prefix=self.non_hostile_baseline,
            candidate_prefix=self.non_hostile_candidate,
            **non_hostile_overrides,
        )


@pytest.mark.parametrize("configured_action", ["cap", "block"])
def test_passed_nested_gate_does_not_activate_configured_cap_or_block(
    configured_action: str,
) -> None:
    state = pair.cap_state(
        {
            "predecision_stop_hazard_guard_configured_action": configured_action,
            "predecision_stop_hazard_guard": {
                "status": "passed",
                "action": configured_action,
                "risk_cap_applied": False,
                "effective_cap": False,
                "effective_block": False,
                "unit_risk_atr": 0.4,
                "min_unit_risk_atr": 0.35,
            },
            "risk_pct": 0.5,
        }
    )

    assert state["status"] == "passed"
    assert state["configured_action"] == configured_action
    assert state["resolved_action"] == "no_block"
    assert state["raw_cap_applied"] is False
    assert state["effective_cap"] is False
    assert state["cap_applied"] is False


def test_row_day_uses_harness_window_before_cross_midnight_identity_time() -> None:
    assert pair.row_day(
        {
            "canonical_replay_candidate_instance_key": (
                "midnight-open@@2026-06-04T00:00:00+00:00"
            ),
            "decision_time_utc": "2026-06-04T00:00:00+00:00",
            "trading_day": "2026-06-03",
        }
    ) == "2026-06-03"
    assert pair.row_day(
        {
            "candidate_instance_parity_key": (
                "next-midnight@@2026-06-05T00:00:00+00:00"
            ),
            "decision_time_utc": "2026-06-05T00:00:00+00:00",
            "trading_day": "2026-06-04",
            "projection_source_window_date": "2026-06-04",
        }
    ) == "2026-06-04"
    # Explicit projection-window authority prevents an identity timestamp from
    # leaking into a different harness day even when trading_day is stale.
    assert pair.row_day(
        {
            "candidate_instance_parity_key": (
                "explicit-next-window@@2026-06-04T23:59:00+00:00"
            ),
            "decision_time": "2026-06-04T23:59:00+00:00",
            "trading_day": "2026-06-04",
            "projection_source_window_date": "2026-06-05",
        }
    ) == "2026-06-05"
    # Identity time remains the deterministic fallback when no harness-window
    # or trading-day authority was serialized.
    assert pair.row_day(
        {
            "canonical_replay_candidate_instance_key": (
                "identity-fallback@@2026-06-04T00:00:00+00:00"
            ),
            "decision_time_utc": "2026-06-05T00:00:00+00:00",
        }
    ) == "2026-06-04"


def test_projection_loader_keeps_only_exact_harness_window_across_midnight(
    tmp_path: Path,
) -> None:
    path = tmp_path / "projection.jsonl"
    keep = make_projection(
        "keep-next-midnight",
        "2026-06-05",
        trade=False,
        missed=True,
        decision_time="2026-06-05T00:00:00+00:00",
    )
    keep.update(
        {
            "projection_source_window_date": "2026-06-04",
            "trading_day": "2026-06-04",
        }
    )
    exclude = make_projection(
        "exclude-prior-clock",
        "2026-06-04",
        trade=False,
        missed=True,
        decision_time="2026-06-04T23:59:00+00:00",
    )
    exclude.update(
        {
            "projection_source_window_date": "2026-06-05",
            "trading_day": "2026-06-04",
        }
    )
    write_jsonl(path, [keep, exclude])

    loaded = pair.load_projection(path, "2026-06-04")

    assert set(loaded.rows) == {keep["candidate_instance_parity_key"]}
    assert loaded.scan["selected_day_rows"] == 1
    assert loaded.scan["outside_day_rows"] == 1


def test_summary_trade_parity_aliases_canonical_cash_pnl_to_headline_cash() -> None:
    trade = make_trade(
        "cash-alias",
        NON_HOSTILE_DAY,
        net_r=1.5,
        cash_pnl=175.0,
        cap=False,
        requires_base_fragility=True,
    )
    projection = make_projection(
        "cash-alias", NON_HOSTILE_DAY, trade=True, missed=False
    )
    summary = target_summary(
        NON_HOSTILE_DAY,
        source_digest=NON_HOSTILE_SOURCE,
        trades=[trade],
        projections=[projection],
        missed=[],
    )
    stats = summary["split_profile_stats"][0]
    assert "headline_cash_pnl" not in stats
    assert stats["cash_pnl"] == 175.0

    parity = pair.summary_trade_parity(summary, pair.trade_rollup([trade]))

    assert parity == {"status": "exact", "bad_counts": {}, "mismatches": []}


def test_positive_pair_filters_exact_days_and_traces_pressure_cohorts(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    other_day = make_projection(
        "outside",
        "2026-06-05",
        trade=False,
        missed=True,
        decision_time="2026-06-05T12:00:00+00:00",
    )
    scenario.write_standard(baseline_extra_projection=[other_day])

    bundle = pair.analyze(scenario.config())

    assert bundle.summary["decision_status"] == "STRUCTURAL_ACCEPT_ECONOMIC_POSITIVE"
    assert bundle.summary["evidence_status"] == "ACCEPT"
    assert bundle.summary["structural_status"] == "ACCEPT"
    assert bundle.summary["economic_status"] == "POSITIVE"
    assert bundle.summary["downstream_status"] == "CLEAR"
    non_hostile = bundle.summary["comparisons"]["non_hostile"]
    assert non_hostile["candidate_identity_counts"] == {
        "baseline": 1,
        "candidate": 1,
        "added": 0,
        "removed": 0,
        "shared": 1,
    }
    assert non_hostile["pressure_cohort_disposition_counts"] == {
        "filled_cap_cleared": 1
    }
    assert (
        bundle.comparisons[1].baseline.projection.scan["outside_day_rows"] == 1
    )
    identity_rows = list(bundle.iter_identity_rows())
    assert len(identity_rows) == 2
    assert all(row["identity_class"] == "shared" for row in identity_rows)


def test_projection_parity_uses_exact_terminal_union_not_summary_counts(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_standard()
    summary_path = tmp_path / f"{scenario.non_hostile_baseline}_SUMMARY.json"
    summary = json.loads(summary_path.read_text())
    summary.update(
        {
            "date_start": "2026-06-01",
            "date_end": "2026-06-19",
            "candidate_rows": 999_999,
            "scorecard_rows": 888_888,
            "missed_opportunity_rows": 777_777,
        }
    )
    write_json(summary_path, summary)

    bundle = pair.analyze(scenario.config())

    parity = bundle.summary["comparisons"]["non_hostile"][
        "baseline_projection_parity"
    ]
    assert parity["status"] == "exact"
    assert parity["candidate_projection_rows"] == 1
    assert parity["terminal_candidate_union_rows"] == 1
    assert bundle.summary["decision_status"] == "STRUCTURAL_ACCEPT_ECONOMIC_POSITIVE"


def test_projection_row_outside_terminal_trade_missed_union_fails_closed(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    orphan = make_projection(
        "orphan", NON_HOSTILE_DAY, trade=False, missed=False
    )
    scenario.write_standard(
        baseline_extra_projection=[orphan],
        candidate_extra_projection=[orphan],
    )

    bundle = pair.analyze(scenario.config())

    comparison = bundle.summary["comparisons"]["non_hostile"]
    assert bundle.summary["decision_status"] == "INSUFFICIENT_EVIDENCE"
    assert comparison["baseline_projection_parity"]["status"] == "mismatch"
    assert comparison["candidate_projection_parity"]["status"] == "mismatch"
    assert (
        "projection_terminal_candidate_union_identity_mismatch"
        in comparison["candidate_projection_parity"]["failures"]
    )
    assert comparison["candidate_projection_parity"]["projection_only_sample"] == [
        candidate_key("orphan", NON_HOSTILE_DAY)
    ]


def test_missed_metrics_keep_executable_diagnostic_and_unscoreable_separate(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_standard()
    prefix = scenario.non_hostile_candidate
    trade = make_trade(
        "non_hostile",
        NON_HOSTILE_DAY,
        net_r=2.0,
        cash_pnl=200.0,
        cap=False,
        requires_base_fragility=True,
    )
    projections = [
        make_projection("non_hostile", NON_HOSTILE_DAY, trade=True, missed=False),
        make_projection("exec", NON_HOSTILE_DAY, trade=False, missed=True),
        make_projection("diag", NON_HOSTILE_DAY, trade=False, missed=True),
        make_projection("unscore", NON_HOSTILE_DAY, trade=False, missed=True),
    ]
    missed = [
        make_missed("exec", NON_HOSTILE_DAY, scope="executable", net_r=1.25),
        make_missed("diag", NON_HOSTILE_DAY, scope="diagnostic", net_r=-2.5),
        make_missed("unscore", NON_HOSTILE_DAY, scope="unscoreable", net_r=None),
    ]
    write_surface(
        tmp_path,
        prefix,
        NON_HOSTILE_DAY,
        source_digest=NON_HOSTILE_SOURCE,
        trades=[trade],
        projections=projections,
        missed=missed,
    )
    # Keep the same candidate denominator in the baseline so the test isolates
    # scoreability classes rather than triggering candidate-identity drift.
    baseline_trade = make_trade(
        "non_hostile",
        NON_HOSTILE_DAY,
        net_r=1.0,
        cash_pnl=100.0,
        cap=True,
        requires_base_fragility=False,
    )
    baseline_missed = [
        make_missed("exec", NON_HOSTILE_DAY, scope="executable", net_r=0.0),
        make_missed("diag", NON_HOSTILE_DAY, scope="diagnostic", net_r=0.0),
        make_missed("unscore", NON_HOSTILE_DAY, scope="unscoreable", net_r=None),
    ]
    write_surface(
        tmp_path,
        scenario.non_hostile_baseline,
        NON_HOSTILE_DAY,
        source_digest=NON_HOSTILE_SOURCE,
        trades=[baseline_trade],
        projections=[
            make_projection("non_hostile", NON_HOSTILE_DAY, trade=True, missed=False),
            make_projection("exec", NON_HOSTILE_DAY, trade=False, missed=True),
            make_projection("diag", NON_HOSTILE_DAY, trade=False, missed=True),
            make_projection("unscore", NON_HOSTILE_DAY, trade=False, missed=True),
        ],
        missed=baseline_missed,
    )

    bundle = pair.analyze(scenario.config())
    metrics = bundle.summary["comparisons"]["non_hostile"][
        "candidate_missed_metrics"
    ]
    assert metrics["rows"] == 3
    assert metrics["executable_scoreable_rows"] == 1
    assert metrics["executable_positive_net_r"] == 1.25
    assert metrics["diagnostic_scoreable_rows"] == 1
    assert metrics["diagnostic_negative_net_r"] == -2.5
    assert metrics["unscoreable_rows"] == 1


def test_positive_executable_displacement_exposes_unresolved_authority_gap(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_standard(
        candidate_filled=False,
        candidate_present=True,
        candidate_missed_scope="executable",
        candidate_missed_r=1.5,
    )

    bundle = pair.analyze(scenario.config())

    assert bundle.summary["decision_status"] == "DEEPER_AUTHORITY_GAP_EXPOSED"
    assert bundle.summary["structural_status"] == "ACCEPT"
    assert bundle.summary["economic_status"] == "MIXED_UNRESOLVED"
    assert bundle.summary["downstream_status"] == "DEEPER_AUTHORITY_GAP_EXPOSED"
    cohort = bundle.comparisons[1].cohort_rows[0]
    assert cohort["disposition"] == "order_or_scheduler_transfer_missed"
    assert cohort["outcome_assessment"] == {
        "status": "UNRESOLVED_POSITIVE_EXECUTABLE_DISPLACEMENT",
        "scope": "executable",
        "net_r": 1.5,
        "economic_direction": "positive_displaced",
        "downstream_authority_gap": True,
        "interpretation": (
            "candidate missed a positive executable opportunity; replacement value "
            "and downstream authority require causal proof"
        ),
    }
    assert any(
        reason.startswith("pressure_cohort_outcome_unresolved")
        for reason in bundle.summary["downstream_reasons"]
    )


def test_negative_diagnostic_displacement_is_beneficial_not_a_gap(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_standard(
        candidate_filled=False,
        candidate_present=True,
        candidate_missed_scope="diagnostic",
        candidate_missed_r=-1.5,
    )

    bundle = pair.analyze(scenario.config())

    assert bundle.summary["decision_status"] == "STRUCTURAL_ACCEPT_ECONOMIC_MIXED"
    assert bundle.summary["structural_status"] == "ACCEPT"
    assert bundle.summary["economic_status"] == "MIXED"
    assert bundle.summary["downstream_status"] == "CLEAR"
    cohort = bundle.comparisons[1].cohort_rows[0]
    assert cohort["outcome_assessment"]["status"] == (
        "BENEFICIAL_NEGATIVE_DISPLACEMENT"
    )
    assert cohort["outcome_assessment"]["economic_direction"] == (
        "beneficial_rejection"
    )
    assert cohort["outcome_assessment"]["downstream_authority_gap"] is False
    assert not bundle.summary["downstream_reasons"]


def test_unscoreable_cohort_displacement_is_unresolved_not_proven_flaw(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_standard(
        candidate_filled=False,
        candidate_present=True,
        candidate_missed_scope="unscoreable",
        candidate_missed_r=0.0,
    )

    bundle = pair.analyze(scenario.config())

    assert bundle.summary["decision_status"] == "DEEPER_AUTHORITY_GAP_EXPOSED"
    assert bundle.summary["structural_status"] == "ACCEPT"
    assert bundle.summary["economic_status"] == "MIXED_UNRESOLVED"
    assert bundle.summary["downstream_status"] == "DEEPER_AUTHORITY_GAP_EXPOSED"
    assessment = bundle.comparisons[1].cohort_rows[0]["outcome_assessment"]
    assert assessment["status"] == "UNRESOLVED_UNSCOREABLE_DISPLACEMENT"
    assert "not automatically" not in assessment["interpretation"]
    assert assessment["downstream_authority_gap"] is True


def test_two_new_unscoreable_replacement_fills_keep_economics_unresolved(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_pair(
        day=HOSTILE_DAY,
        source_digest=HOSTILE_SOURCE,
        baseline_prefix=scenario.hostile_baseline,
        candidate_prefix=scenario.hostile_candidate,
    )

    baseline_trade = make_trade(
        "non_hostile",
        NON_HOSTILE_DAY,
        net_r=1.0,
        cash_pnl=100.0,
        cap=True,
        requires_base_fragility=False,
    )
    candidate_trade = make_trade(
        "non_hostile",
        NON_HOSTILE_DAY,
        net_r=2.0,
        cash_pnl=200.0,
        cap=False,
        requires_base_fragility=True,
    )
    labels = ("replacement_a", "replacement_b")
    baseline_projections = [
        make_projection("non_hostile", NON_HOSTILE_DAY, trade=True, missed=False),
        *(
            make_projection(label, NON_HOSTILE_DAY, trade=False, missed=True)
            for label in labels
        ),
    ]
    candidate_projections = [
        make_projection("non_hostile", NON_HOSTILE_DAY, trade=True, missed=False),
        *(
            make_projection(label, NON_HOSTILE_DAY, trade=True, missed=False)
            for label in labels
        ),
    ]
    write_surface(
        tmp_path,
        scenario.non_hostile_baseline,
        NON_HOSTILE_DAY,
        source_digest=NON_HOSTILE_SOURCE,
        trades=[baseline_trade],
        projections=baseline_projections,
        missed=[
            make_missed(label, NON_HOSTILE_DAY, scope="unscoreable", net_r=None)
            for label in labels
        ],
    )
    write_surface(
        tmp_path,
        scenario.non_hostile_candidate,
        NON_HOSTILE_DAY,
        source_digest=NON_HOSTILE_SOURCE,
        trades=[candidate_trade, *(make_unscoreable_trade(label, NON_HOSTILE_DAY) for label in labels)],
        projections=candidate_projections,
        missed=[],
    )

    bundle = pair.analyze(scenario.config())

    comparison = bundle.summary["comparisons"]["non_hostile"]
    assert bundle.summary["decision_status"] == "DEEPER_AUTHORITY_GAP_EXPOSED"
    assert bundle.summary["structural_status"] == "ACCEPT"
    assert bundle.summary["economic_status"] == "MIXED_UNRESOLVED"
    assert bundle.summary["downstream_status"] == "DEEPER_AUTHORITY_GAP_EXPOSED"
    assert comparison["unscoreable_replacement_trade_count"] == 2
    assert any(
        reason == (
            "unscoreable_replacement_trades_require_terminal_outcomes:"
            "non_hostile:count=2"
        )
        for reason in bundle.summary["downstream_reasons"]
    )


def test_candidate_suppression_is_a_batch_failure(tmp_path: Path) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_standard(candidate_filled=False, candidate_present=False)

    bundle = pair.analyze(scenario.config())

    assert bundle.summary["decision_status"] == "BATCH_FAIL"
    assert bundle.summary["structural_status"] == "FAIL"
    assert bundle.summary["economic_status"] == "NOT_ASSESSED"
    assert bundle.summary["downstream_status"] == "NOT_ASSESSED"
    assert "candidate_identity_drift" in bundle.summary["decision_reasons"]
    assert (
        bundle.comparisons[1].cohort_rows[0]["disposition"]
        == "candidate_generation_suppressed"
    )


def test_duplicate_projection_identity_fails_closed_as_insufficient_evidence(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    duplicate = make_projection(
        "non_hostile", NON_HOSTILE_DAY, trade=True, missed=False
    )
    scenario.write_standard(candidate_extra_projection=[duplicate])

    bundle = pair.analyze(scenario.config())

    assert bundle.summary["decision_status"] == "INSUFFICIENT_EVIDENCE"
    assert bundle.summary["evidence_status"] == "INSUFFICIENT_EVIDENCE"
    assert bundle.summary["structural_status"] == "NOT_ASSESSED"
    assert (
        "candidate_projection_duplicate_identity_keys"
        in bundle.summary["decision_reasons"]
    )


def test_nonfragile_cap_remaining_is_a_batch_failure(tmp_path: Path) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_standard(
        candidate_cap=True,
        candidate_requires_base=False,
        candidate_base_fragile=False,
    )

    bundle = pair.analyze(scenario.config())

    assert bundle.summary["decision_status"] == "BATCH_FAIL"
    assert bundle.summary["structural_status"] == "FAIL"
    assert "candidate_stop_hazard_cap_execution_authority_leak" in bundle.summary[
        "decision_reasons"
    ]
    assert "pressure_only_nonfragile_cap_remains" in bundle.summary[
        "decision_reasons"
    ]


def test_suppressed_pressure_rematerialized_as_final_block_is_batch_failure(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_standard(candidate_filled=False, candidate_present=True)
    path = (
        tmp_path
        / f"{scenario.non_hostile_candidate}_MISSED_OPPORTUNITY_LEDGER.jsonl"
    )
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    rows[0].update(
        {
            "stop_hazard_materialization_pressure_score_materialized": True,
            "stop_hazard_materialization_pressure_suppressed_reason": (
                "stop_hazard_pressure_requires_base_fragility"
            ),
            "stop_hazard_materialization_requires_reallocation_dominance": True,
            "stop_hazard_materialization_blocked": True,
            "package_replay_order_executable_final_blocker_reason": (
                "stop_hazard_materialization_requires_reallocation_dominance"
            ),
        }
    )
    write_jsonl(path, rows)

    bundle = pair.analyze(scenario.config())

    assert bundle.summary["decision_status"] == "BATCH_FAIL"
    assert bundle.summary["structural_status"] == "FAIL"
    assert (
        "candidate_suppressed_pressure_rematerialized_as_final_block"
        in bundle.summary["decision_reasons"]
    )
    metrics = bundle.summary["comparisons"]["non_hostile"][
        "candidate_missed_metrics"
    ]
    assert metrics["suppressed_pressure_materialization_blocked_rows"] == 1


def test_structural_green_with_mixed_cash_translation_is_economic_mixed(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_standard(candidate_net=2.0, candidate_cash=50.0)

    bundle = pair.analyze(scenario.config())

    assert bundle.summary["decision_status"] == "STRUCTURAL_ACCEPT_ECONOMIC_MIXED"
    assert bundle.summary["structural_status"] == "ACCEPT"
    assert bundle.summary["economic_status"] == "MIXED"
    assert bundle.summary["downstream_status"] == "CLEAR"
    assert not bundle.summary["comparisons"]["non_hostile"]["structural_issues"]


def test_atomic_outputs_manifest_hashes_and_row_parity_detect_tampering(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_standard()
    bundle = pair.analyze(scenario.config())

    published = pair.publish(bundle)

    manifest_path = Path(published["manifest_path"])
    verification = pair.verify_manifest(manifest_path)
    assert verification == {"valid": True, "issues": []}
    manifest = json.loads(manifest_path.read_text())
    identity = next(
        row
        for row in manifest["output_artifacts"]
        if row["kind"] == "identity_transition_ledger"
    )
    assert identity["row_count"] == 2
    assert manifest["row_parity"]["identity_transition_ledger"] == 2
    identity_path = Path(identity["path"])
    identity_path.write_text(identity_path.read_text() + "{}\n")

    verification = pair.verify_manifest(manifest_path)

    assert verification["valid"] is False
    assert "output_sha256_mismatch:identity_transition_ledger" in verification["issues"]
    assert "output_row_count_mismatch:identity_transition_ledger" in verification[
        "issues"
    ]


def test_historical_hostile_projection_gap_is_explicit_but_not_silently_upgraded(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_standard()
    pair.projection_path(tmp_path, scenario.hostile_baseline).unlink()
    pair.projection_path(tmp_path, scenario.hostile_candidate).unlink()
    (tmp_path / f"{scenario.hostile_baseline}_MISSED_OPPORTUNITY_LEDGER.jsonl").unlink()

    bundle = pair.analyze(scenario.config(require_hostile_projection=False))

    hostile = bundle.summary["comparisons"]["hostile"]
    assert hostile["projection_identity_status"] == "unavailable_trade_identity_only"
    assert "historical_candidate_stage_identity_unavailable_trade_identity_only" in hostile[
        "warnings"
    ]
    assert "historical_baseline_missed_ledger_unavailable" in hostile["warnings"]
    assert bundle.summary["decision_status"] == "STRUCTURAL_ACCEPT_ECONOMIC_POSITIVE"
