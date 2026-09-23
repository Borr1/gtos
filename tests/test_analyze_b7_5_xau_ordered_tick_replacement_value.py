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
    "analyze_b7_5_xau_ordered_tick_replacement_value.py"
)
SPEC = importlib.util.spec_from_file_location(
    "analyze_b7_5_xau_ordered_tick_replacement_value", MODULE_PATH
)
assert SPEC and SPEC.loader
proof = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = proof
SPEC.loader.exec_module(proof)


BASELINE_PREFIX = "BROAD_LIVE_AS_IF_REPLAY_TEST_BASELINE"
TARGET_PREFIX = "BROAD_LIVE_AS_IF_REPLAY_TEST_XAU_TICK"
OUTPUT_PREFIX = "TEST_XAU_ORDERED_TICK_PROOF"
BASELINE_SHARED = "a" * 64
BASELINE_SOURCE = "b" * 64
TARGET_SHARED = "c" * 64
TARGET_SOURCE = "d" * 64
PROFILE_HASH = "e" * 64
SYMBOLS = [f"SYMBOL_{index:02d}" for index in range(23)] + ["XAUUSD"]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def early_trade(
    *,
    scoreable: bool,
    close_time: str = "2026-06-04T08:48:10.204000+00:00",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "canonical_replay_candidate_instance_key": proof.EARLY_IDENTITY,
        "candidate_id": proof.EARLY_IDENTITY.split("@@", 1)[0],
        "decision_time_utc": "2026-06-04T07:30:00+00:00",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "direction": "SHORT",
        "selector_action": "open-reduced-risk",
        "raw_selector_action": "open-reduced-risk",
        "effective_selector_action": "open-reduced-risk",
        "simulated_trade_id": "trade-early",
        "simulated_order_id": "order-early",
        "entry_time_utc": "2026-06-04T07:34:12.004000+00:00",
        "fill_time_utc": "2026-06-04T07:34:12.004000+00:00",
        "exit_time_utc": close_time,
        "terminal_r_scoreable": scoreable,
        "terminal_r_scoreability_status": (
            "ordered_tick_terminal_r_scoreable"
            if scoreable
            else "entry_fill_executable_terminal_r_ordered_tick_sequence_required"
        ),
        "headline_result_eligible": scoreable,
        "expected_cost_r": 0.1,
        "risk_cash": 625.0,
        "risk_pct": 0.625,
        "same_symbol_replay_exposure_context_status": "source_observed",
        "same_symbol_replay_exposure_context_synthesized_empty": False,
        "same_symbol_replay_exposure_context": {
            "symbol": "XAUUSD",
            "side": "SHORT",
            "same_side_open_count": 0,
            "same_side_open_ids": [],
            "same_side_open_risk_pct": 0.0,
        },
    }
    if scoreable:
        row.update(
            {
                "net_proxy_r": 1.0,
                "gross_r": 1.1,
                "final_r": 1.1,
                "pnl_cash": 625.0,
                "ordered_tick_final_r_authority": True,
                "ordered_tick_truth_satisfied": True,
                "ordered_tick_truth_satisfied_for_terminal_r": True,
                "ordered_tick_truth_source_satisfied": True,
                "ordered_tick_truth_oracle_satisfied": True,
                "ordered_tick_truth_authority": {
                    "source": "tick",
                    "source_timeframe": "TICK",
                    "query_row_count": 100,
                },
                "limit_first_ordered_tick_truth_satisfied": True,
                "limit_first_tick_window_covers_candidate": True,
                "limit_first_tick_query_rows_returned": 100,
                "limit_first_path_source": "tick",
                "limit_first_path_source_timeframe": "TICK",
                "limit_first_terminal_outcome": "target_reached_before_stop",
            }
        )
    return row


def late_missed(
    *,
    expose_early: bool,
    prior_cost_block: bool = False,
) -> dict[str, Any]:
    row = {
        "canonical_replay_candidate_instance_key": proof.LATE_IDENTITY,
        "candidate_id": proof.LATE_IDENTITY.split("@@", 1)[0],
        "decision_time_utc": "2026-06-04T07:45:00+00:00",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "direction": "SHORT",
        "selector_action": "trade",
        "raw_selector_action": "trade",
        "effective_selector_action": "trade",
        "effective_selector_reason": "synthetic_risk_bearing_lifecycle_candidate",
        "miss_reason": "synthetic_lifecycle_authority_block",
        "terminal_r_scoreable": True,
        "terminal_r_scoreability_status": "ordered_tick_terminal_r_scoreable",
        "missed_opportunity_r_scoreability_status": "diagnostic_opportunity_r_scoreable",
        "opportunity_net_proxy_r": 0.4,
        "same_symbol_lifecycle_action": "same_direction_scale_in",
        "same_symbol_replay_exposure_context_status": "source_observed",
        "same_symbol_replay_exposure_context_synthesized_empty": False,
        "same_symbol_replay_exposure_context": {
            "symbol": "XAUUSD",
            "side": "SHORT",
            "same_side_open_count": 1 if expose_early else 0,
            "same_side_open_ids": ["trade-early"] if expose_early else [],
            "same_side_open_risk_pct": 0.625 if expose_early else 0.0,
        },
        "package_replay_order_executable_final_blocker_class": "lifecycle_authority",
        "package_replay_order_executable_final_blocker_reason": (
            "same_symbol_lifecycle_authority_required"
        ),
    }
    if prior_cost_block:
        row.update(
            {
                "selector_action": "reject",
                "raw_selector_action": "reject",
                "effective_selector_action": "reject",
                "effective_selector_reason": "broker_net_pretrade_cost_packet_refused",
                "miss_reason": (
                    "scheduler_materialization_skipped_selector_not_risk_bearing_"
                    "cost_failed"
                ),
                "pretrade_cost_packet_status": "REFUSED",
                "cost_authority": "broker_calibrated_replay_cost",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "candidate_cost_r_fallback_is_authority": False,
                "broker_pretrade_cost_executable": False,
                "broker_pretrade_cost_executable_block_reason": (
                    "broker_cost_packet_refused:spread_r_exceeds_selected_cell_limit:"
                    "0.126612>0.100000|total_cost_r_exceeds_limit:0.151024>0.150000"
                ),
                "scheduler_materialization_skip_reason": (
                    "selector_not_risk_bearing_cost_failed"
                ),
                "scheduler_materialization_action_intent": (
                    "not_evaluated_selector_not_risk_bearing"
                ),
                "scheduler_selection_disposition": (
                    "candidate_materialization_skipped_before_scheduler"
                ),
                "same_symbol_lifecycle_action": "source_required_fail_closed",
                "package_replay_order_executable_final_blocker_class": (
                    "cost_authority"
                ),
                "package_replay_order_executable_final_blocker_reason": (
                    "broker_cost_authority_blocked_non_executable"
                ),
            }
        )
    return row


def late_trade() -> dict[str, Any]:
    return {
        "canonical_replay_candidate_instance_key": proof.LATE_IDENTITY,
        "candidate_id": proof.LATE_IDENTITY.split("@@", 1)[0],
        "decision_time_utc": "2026-06-04T07:45:00+00:00",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "direction": "SHORT",
        "selector_action": "trade",
        "raw_selector_action": "trade",
        "effective_selector_action": "trade",
        "simulated_trade_id": "trade-late",
        "simulated_order_id": "order-late",
        "entry_time_utc": "2026-06-04T07:46:00+00:00",
        "exit_time_utc": "2026-06-04T08:00:00+00:00",
        "terminal_r_scoreable": True,
        "terminal_r_scoreability_status": "ordered_tick_terminal_r_scoreable",
        "headline_result_eligible": True,
        "net_proxy_r": -1.0,
        "gross_r": -0.9,
        "final_r": -0.9,
        "pnl_cash": -500.0,
        "expected_cost_r": 0.1,
        "risk_cash": 500.0,
        "risk_pct": 0.5,
        "same_symbol_replay_exposure_context_status": "source_observed",
        "same_symbol_replay_exposure_context_synthesized_empty": False,
        "same_symbol_replay_exposure_context": {
            "symbol": "XAUUSD",
            "side": "SHORT",
            "same_side_open_count": 0,
            "same_side_open_ids": [],
            "same_side_open_risk_pct": 0.0,
        },
    }


def completed_summary(
    *,
    universe: list[str],
    shared_digest: str,
    source_digest: str,
    trades: list[dict[str, Any]],
    missed: list[dict[str, Any]],
    scorecard_rows: int,
    order_rows: int,
    oracle_rows: int,
    source_rows: int,
) -> dict[str, Any]:
    rollup = proof.trade_rollup(trades)
    stats = {"profile": proof.PROFILE, **rollup}
    stats["cash_pnl"] = stats["headline_cash_pnl"]
    return {
        "status": "broad_live_as_if_replay_materialized_broker_live_closed",
        "date_start": proof.DAY,
        "date_end": proof.DAY,
        "terminal_execution_materialized": True,
        "terminal_execution_materialization_status": (
            "terminal_execution_ledgers_materialized"
        ),
        "artifact_materialization_status": {
            "summary": "materialized",
            "trade": "materialized",
            "missed": "materialized_compact_missed_opportunity_ledger",
            "source": "materialized",
        },
        "broker_mutation_enabled": False,
        "live_broker_authority": False,
        "final_selection_claim": False,
        "active_replay_symbol_universe": universe,
        "configured_symbol_universe": universe,
        "candidate_rows": len(trades) + len(missed),
        "trade_rows": len(trades),
        "missed_opportunity_rows": len(missed),
        "scorecard_rows": scorecard_rows,
        "order_rows": order_rows,
        "oracle_rows": oracle_rows,
        "source_universe_rows": source_rows,
        "b7_5_contract_binding": {
            "required": True,
            "valid": True,
            "actual_shared_execution_contract_digest_sha256": shared_digest,
            "expected_shared_execution_contract_digest_sha256": shared_digest,
            "actual_source_plan_digests_sha256": [source_digest],
            "expected_source_plan_digest_sha256": source_digest,
        },
        "shared_execution_contract": {
            "shared_execution_contract_digest_sha256": shared_digest,
            "effective_profile_config_hashes": {proof.PROFILE: PROFILE_HASH},
        },
        "source_authority_chunk_invariance_contract": {
            "all_source_plans_valid": True,
            "all_chunk_source_plans_match_canonical": True,
        },
        "physical_trade_summary_serialized_ledger_parity_contract": {
            "serialized_trade_ledger_is_physical_summary_authority": True,
            "canonical_result_ledger_normalization_before_summary": True,
            "scoreable_unscoreable_cost_partition_required": True,
        },
        "split_profile_stats": [stats],
    }


def source_row(
    tick_path: Path,
    manifest_path: Path,
    tick_sha: str,
    tick_rows: int,
) -> dict[str, Any]:
    return {
        "row_type": "tick_symbol_source",
        "symbol": "XAUUSD",
        "timeframe": "TICK",
        "status": "selected_priority_tick_source",
        "selected_status": "selected_priority_tick_source",
        "path": str(tick_path),
        "source_path": str(tick_path),
        "manifest_path": str(manifest_path),
        "sha256": tick_sha,
        "source_sha256": tick_sha,
        "rows": tick_rows,
        "row_count": tick_rows,
        "start_utc": "2026-06-01T01:05:00+00:00",
        "end_utc": "2026-06-05T23:49:59+00:00",
        "ordered_tick_truth_satisfied": True,
        "source_broker": "FTMO",
        "source_role": "owner_authorized_path_override",
        "source_truth_scope": "ordered_price_path_only_not_broker_order_lifecycle_truth",
        "broker_lifecycle_truth_satisfied": False,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "not_redacted_account_native": True,
    }


class Scenario:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.tick_path = root / "ticks" / "XAUUSD" / "ticks.jsonl"
        self.tick_path.parent.mkdir(parents=True)
        self.tick_path.write_text('{"time":"a"}\n{"time":"b"}\n')
        self.tick_sha = proof.sha256_file(self.tick_path)
        self.tick_rows = 2
        self.manifest_path = root / "tick_manifest.json"
        write_json(
            self.manifest_path,
            {
                "schema_version": "mt5_research_tick_export_v1",
                "read_only": True,
                "errors": [],
                "source_provenance": {
                    "source_truth_scope": (
                        "ordered_price_path_only_not_broker_order_lifecycle_truth"
                    )
                },
                "files": {
                    "XAUUSD_TEST_TICK": {
                        "file_symbol": "XAUUSD",
                        "timeframe": "TICK",
                        "path": str(self.tick_path),
                        "sha256": self.tick_sha,
                        "rows": self.tick_rows,
                    }
                },
            },
        )

    def config(self, *, full_portfolio_mode: bool = False) -> proof.AnalyzerConfig:
        return proof.AnalyzerConfig(
            artifact_root=self.root,
            baseline_prefix=BASELINE_PREFIX,
            target_prefix=TARGET_PREFIX,
            output_prefix=OUTPUT_PREFIX,
            expected_baseline_shared_digest=BASELINE_SHARED,
            expected_baseline_source_digest=BASELINE_SOURCE,
            expected_target_shared_digest=TARGET_SHARED,
            expected_target_source_digest=TARGET_SOURCE,
            expected_profile_digest=PROFILE_HASH,
            expected_tick_sha256=self.tick_sha,
            expected_tick_rows=self.tick_rows,
            full_portfolio_mode=full_portfolio_mode,
        )

    def write_surface(
        self,
        prefix: str,
        *,
        universe: list[str],
        shared_digest: str,
        source_digest: str,
        trades: list[dict[str, Any]],
        missed: list[dict[str, Any]],
        sources: list[dict[str, Any]],
    ) -> None:
        scorecards = [
            {
                "canonical_replay_candidate_instance_key": trade[
                    "canonical_replay_candidate_instance_key"
                ]
            }
            for trade in trades
        ]
        orders = [
            {
                "canonical_replay_candidate_instance_key": trade[
                    "canonical_replay_candidate_instance_key"
                ],
                "simulated_order_id": trade["simulated_order_id"],
            }
            for trade in trades
        ]
        oracle = [
            {
                "canonical_replay_candidate_instance_key": trade[
                    "canonical_replay_candidate_instance_key"
                ]
            }
            for trade in trades
        ]
        summary = completed_summary(
            universe=universe,
            shared_digest=shared_digest,
            source_digest=source_digest,
            trades=trades,
            missed=missed,
            scorecard_rows=len(scorecards),
            order_rows=len(orders),
            oracle_rows=len(oracle),
            source_rows=len(sources),
        )
        write_json(self.root / f"{prefix}_SUMMARY.json", summary)
        write_jsonl(self.root / f"{prefix}_TRADE_LEDGER.jsonl", trades)
        write_jsonl(self.root / f"{prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl", missed)
        write_jsonl(self.root / f"{prefix}_SCORECARD_LEDGER.jsonl", scorecards)
        write_jsonl(self.root / f"{prefix}_ORDER_LEDGER.jsonl", orders)
        write_jsonl(self.root / f"{prefix}_ORDERED_PATH_ORACLE_LEDGER.jsonl", oracle)
        write_jsonl(self.root / f"{prefix}_SOURCE_UNIVERSE_LEDGER.jsonl", sources)

    def write_pair(
        self,
        *,
        expose_early: bool,
        early_close: str = "2026-06-04T08:48:10.204000+00:00",
        late_executes: bool = False,
        target_universe: list[str] | None = None,
        target_prior_cost_block: bool = False,
    ) -> None:
        baseline_early = early_trade(scoreable=False)
        baseline_late = late_missed(expose_early=True)
        self.write_surface(
            BASELINE_PREFIX,
            universe=SYMBOLS,
            shared_digest=BASELINE_SHARED,
            source_digest=BASELINE_SOURCE,
            trades=[baseline_early],
            missed=[baseline_late],
            sources=[{"symbol": "XAUUSD", "timeframe": "M1"}],
        )
        target_early = early_trade(scoreable=True, close_time=early_close)
        target_trades = [target_early]
        target_missed: list[dict[str, Any]] = []
        if late_executes:
            target_trades.append(late_trade())
        else:
            target_missed.append(
                late_missed(
                    expose_early=expose_early,
                    prior_cost_block=target_prior_cost_block,
                )
            )
        self.write_surface(
            TARGET_PREFIX,
            universe=target_universe or ["XAUUSD"],
            shared_digest=TARGET_SHARED,
            source_digest=TARGET_SOURCE,
            trades=target_trades,
            missed=target_missed,
            sources=[
                source_row(
                    self.tick_path,
                    self.manifest_path,
                    self.tick_sha,
                    self.tick_rows,
                )
            ],
        )


def test_incomplete_target_summary_cannot_mutate_outputs(tmp_path: Path) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_pair(expose_early=True)
    (tmp_path / f"{TARGET_PREFIX}_SUMMARY.json").unlink()
    stale_manifest = tmp_path / f"{OUTPUT_PREFIX}_COMPLETION_MANIFEST.json"
    stale_manifest.write_text("stale-but-untouched\n")

    with pytest.raises(proof.ArtifactError, match="target_summary_incomplete:missing"):
        proof.run(scenario.config())

    assert stale_manifest.read_text() == "stale-but-untouched\n"
    assert not (tmp_path / f"{OUTPUT_PREFIX}_SUMMARY.json").exists()


def test_cli_exposes_explicit_full_portfolio_mode() -> None:
    config = proof.parse_args(["--full-portfolio-mode"])

    assert config.full_portfolio_mode is True


def test_manifest_last_complete_open_exposure_proof(tmp_path: Path) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_pair(expose_early=True)

    result = proof.run(scenario.config())

    assert result["summary"]["decision"] == (
        "PROOF_COMPLETE_OPEN_EXPOSURE_AND_LATE_NON_EXECUTION_OBSERVED"
    )
    assert result["summary"]["analysis_valid"] is True
    assert result["summary"]["tick_source_integrity"]["valid"] is True
    assert result["summary"]["target_terminal_scoreability"]["valid"] is True
    assert result["summary"]["same_symbol_block_authority"]["consistent"] is True
    scope = result["summary"]["evidence_scope"]
    assert scope["full_portfolio_economic_claim_authorized"] is False
    assert scope["policy_change_authorized"] is False
    assert scope["policy_assumption_count"] == 0

    paths = {name: Path(path) for name, path in result["paths"].items()}
    assert all(path.is_file() for path in paths.values())
    manifest = json.loads(paths["completion_manifest"].read_text())
    assert manifest["status"] == "completion_manifest_written_last"
    assert manifest["artifact_count"] == 3
    assert manifest["row_ledger_rows"] == 12
    assert paths["completion_manifest"].stat().st_mtime_ns >= max(
        paths[name].stat().st_mtime_ns for name in ("summary", "row_ledger", "dossier")
    )
    for artifact in manifest["artifacts"]:
        assert proof.sha256_file(Path(artifact["path"])) == artifact["sha256"]


def test_open_trade_missing_from_source_observed_context_is_inconsistency(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_pair(expose_early=False)

    summary, rows = proof.build_analysis(scenario.config())

    assert summary["analysis_valid"] is True
    assert summary["target_chronology"]["early_trade_open_at_late_decision"] is True
    assert summary["same_symbol_block_authority"]["consistent"] is False
    assert summary["same_symbol_block_authority"]["status"] == (
        "early_trade_open_but_late_source_observed_context_missing_it"
    )
    assert summary["decision"] == "DEEPER_SAME_SYMBOL_AUTHORITY_INCONSISTENCY"
    assert summary["portfolio_disposition"] == "ESCALATE_FULL_PORTFOLIO"
    assert any(row["row_type"] == "same_symbol_block_authority" for row in rows)


def test_valid_cost_block_precedes_and_makes_lifecycle_context_non_authoritative(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_pair(
        expose_early=False,
        target_prior_cost_block=True,
    )

    summary, _rows = proof.build_analysis(scenario.config())

    authority = summary["same_symbol_block_authority"]
    assert summary["target_chronology"]["early_trade_open_at_late_decision"] is True
    assert authority["prior_cost_block_precedence"]["valid"] is True
    assert authority["status"] == "lifecycle_not_evaluated_due_prior_cost_block"
    assert authority["context_required_for_terminal_decision"] is False
    assert authority["context_decision_authoritative"] is False
    assert authority["raw_context_matches_chronology"] is False
    assert authority["consistent"] is True
    assert authority["provenance_label_caveat"] == (
        "serialized_source_observed_context_is_provenance_only_not_"
        "decision_authority_after_pre_lifecycle_cost_continue"
    )
    assert summary["causal_disposition"] == (
        "TERMINAL_TRUTH_GREEN_LIFECYCLE_NOT_EVALUATED_DUE_PRIOR_COST_BLOCK"
    )
    assert summary["decision"] == (
        "TERMINAL_TRUTH_GREEN_ESCALATE_FULL_PORTFOLIO"
    )
    assert summary["portfolio_disposition"] == "ESCALATE_FULL_PORTFOLIO"


def test_closed_early_trade_and_late_execution_is_descriptive_not_policy(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_pair(
        expose_early=False,
        early_close="2026-06-04T07:40:00+00:00",
        late_executes=True,
    )

    summary, _rows = proof.build_analysis(scenario.config())

    assert summary["decision"] == (
        "PROOF_COMPLETE_EARLY_TRADE_CLOSED_BEFORE_LATE_DECISION"
    )
    assert summary["target_chronology"]["early_trade_open_at_late_decision"] is False
    assert summary["same_symbol_block_authority"]["consistent"] is True
    assert summary["replacement_value_observation"][
        "arithmetic_netting_authorized"
    ] is False
    assert summary["evidence_scope"]["policy_preference_authorized"] is False


def test_physical_summary_mismatch_is_invalid_evidence(tmp_path: Path) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_pair(expose_early=True)
    path = tmp_path / f"{TARGET_PREFIX}_SUMMARY.json"
    payload = json.loads(path.read_text())
    payload["split_profile_stats"][0]["physical_net_r"] += 0.5
    write_json(path, payload)

    summary, _rows = proof.build_analysis(scenario.config())

    assert summary["physical_summary_parity"]["target"]["valid"] is False
    assert summary["decision"] == "INVALID_EVIDENCE"
    assert "target_physical_summary_parity_failed" in summary["structural_issues"]


def test_tick_file_hash_mismatch_is_invalid_evidence(tmp_path: Path) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_pair(expose_early=True)
    scenario.tick_path.write_text('{"tampered":true}\n')

    summary, _rows = proof.build_analysis(scenario.config())

    integrity = summary["tick_source_integrity"]
    assert integrity["valid"] is False
    assert integrity["checks"]["tick_file_sha_exact"] is False
    assert summary["decision"] == "INVALID_EVIDENCE"
    assert "target_tick_integrity_failed" in summary["structural_issues"]


def test_full_portfolio_mode_green_reconciles_same_day_r_cash_and_risk(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_pair(expose_early=True, target_universe=SYMBOLS)

    summary, _rows = proof.build_analysis(
        scenario.config(full_portfolio_mode=True)
    )

    assert summary["decision"] == "FULL_PORTFOLIO_RECONCILIATION_COMPLETE"
    assert summary["causal_disposition"] == (
        "PROOF_COMPLETE_OPEN_EXPOSURE_AND_LATE_NON_EXECUTION_OBSERVED"
    )
    assert summary["terminal_identity_partition_proof"]["valid"] is True
    partition = summary["terminal_identity_partition_proof"]
    assert partition["terminal_scoreability_enrichment_identities"] == [
        proof.EARLY_IDENTITY
    ]
    economics = summary["full_portfolio_economics"]
    assert economics["available"] is True
    assert economics["metrics"]["physical_net_r"]["delta"] == 1.0
    assert economics["metrics"]["physical_cash_pnl"]["delta"] == 625.0
    assert economics["metrics"]["physical_risk_pct"]["delta"] == 0.0
    scope = summary["evidence_scope"]
    assert scope["same_day_simulated_portfolio_reconciliation_authorized"] is True
    assert scope["full_portfolio_economic_claim_authorized"] is False
    assert scope["broad_generalization_claim_authorized"] is False
    assert scope["policy_change_authorized"] is False
    assert scope["broker_real_claim_authorized"] is False


def test_full_mode_does_not_require_lifecycle_context_after_valid_prior_cost_block(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_pair(
        expose_early=False,
        target_universe=SYMBOLS,
        target_prior_cost_block=True,
    )

    summary, _rows = proof.build_analysis(
        scenario.config(full_portfolio_mode=True)
    )

    authority = summary["same_symbol_block_authority"]
    assert authority["status"] == "lifecycle_not_evaluated_due_prior_cost_block"
    assert authority["context_required_for_terminal_decision"] is False
    assert "full_portfolio_same_symbol_context_drift" not in summary[
        "structural_issues"
    ]
    assert summary["decision"] == "FULL_PORTFOLIO_RECONCILIATION_COMPLETE"


def test_full_portfolio_mode_fails_closed_on_target_universe_drift(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_pair(expose_early=True)

    summary, _rows = proof.build_analysis(
        scenario.config(full_portfolio_mode=True)
    )

    assert summary["decision"] == "INVALID_EVIDENCE"
    assert summary["source_and_execution_contracts"]["target"]["checks"][
        "exact_24_symbol_target"
    ] is False
    assert "target_contract_invalid" in summary["structural_issues"]
    assert summary["evidence_scope"][
        "same_day_simulated_portfolio_reconciliation_authorized"
    ] is False


def test_full_portfolio_mode_fails_closed_on_identity_partition_drift(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_pair(expose_early=True, target_universe=SYMBOLS)
    missed_path = tmp_path / f"{TARGET_PREFIX}_MISSED_OPPORTUNITY_LEDGER.jsonl"
    rows = [json.loads(line) for line in missed_path.read_text().splitlines()]
    extra = dict(rows[0])
    extra["canonical_replay_candidate_instance_key"] = (
        "extra_candidate@@2026-06-04T08:00:00+00:00"
    )
    extra["candidate_id"] = "extra_candidate"
    extra["decision_time_utc"] = "2026-06-04T08:00:00+00:00"
    rows.append(extra)
    write_jsonl(missed_path, rows)
    summary_path = tmp_path / f"{TARGET_PREFIX}_SUMMARY.json"
    payload = json.loads(summary_path.read_text())
    payload["missed_opportunity_rows"] += 1
    payload["candidate_rows"] += 1
    write_json(summary_path, payload)

    summary, _rows = proof.build_analysis(
        scenario.config(full_portfolio_mode=True)
    )

    partition = summary["terminal_identity_partition_proof"]
    assert partition["valid"] is False
    assert partition["checks"]["candidate_identity_partition_exact"] is False
    assert summary["decision"] == "INVALID_EVIDENCE"
    assert "full_portfolio_terminal_identity_partition_drift" in summary[
        "structural_issues"
    ]


def test_full_portfolio_mode_fails_closed_on_same_symbol_context_drift(
    tmp_path: Path,
) -> None:
    scenario = Scenario(tmp_path)
    scenario.write_pair(expose_early=False, target_universe=SYMBOLS)

    summary, _rows = proof.build_analysis(
        scenario.config(full_portfolio_mode=True)
    )

    assert summary["same_symbol_block_authority"]["consistent"] is False
    assert summary["decision"] == "INVALID_EVIDENCE"
    assert "full_portfolio_same_symbol_context_drift" in summary[
        "structural_issues"
    ]
    assert summary["evidence_scope"][
        "same_day_simulated_portfolio_reconciliation_authorized"
    ] is False
