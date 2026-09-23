from __future__ import annotations

import json
from pathlib import Path

import src.research_infra.v4_kia_parity_tick_first_runtime_repair as kiap
from src.components.v4_live_replay_decision_core import PRODUCTION_CORE_IMPORT_PATH
from src.research_infra.v4_timewarp_simulated_live_research_loop import SOURCE_TRUTH_SCOPE


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def minimal_repo_source(tmp_path: Path) -> None:
    replay = tmp_path / "src/research_infra/v4_timewarp_simulated_live_research_loop.py"
    replay.parent.mkdir(parents=True, exist_ok=True)
    replay.write_text(
        "\n".join(
            [
                "from src.components.v4_live_replay_decision_core import V4DecisionCycleCore",
                "decision_core = V4DecisionCycleCore(",
                "    config={},",
                "    sources={},",
                "    candidate_evaluator=evaluate_candidate_v4,",
                "    scheduler_allocator=materialize_scheduler_window,",
                ")",
                "decision_core.generate_candidates(raw_data={}, mso=None, symbol='XAUUSD', kill_zone='fixture')",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def proof_payload() -> dict:
    refs = {
        "production_core_imported": True,
        "production_core_instantiated": True,
        "production_core_generate_candidates_called": True,
        "production_core_window_summaries_called": True,
        "replay_core_imported_from_production": True,
        "replay_core_generate_candidates_called": True,
        "replay_core_candidate_evaluator_bound": True,
        "replay_core_scheduler_allocator_bound": True,
    }
    return {
        "production_import_path": PRODUCTION_CORE_IMPORT_PATH,
        "shared_core_status": kiap.KIA_PRODUCTION_SHARED_CORE_STATUS,
        "live_orchestrator_source_refs": refs,
    }


def write_minimal_route(
    tmp_path: Path,
    *,
    m1_violation: bool = False,
    close_development_gate: bool = False,
    close_item8_gate: bool = False,
    include_development: bool = False,
) -> Path:
    route = tmp_path / "route"
    route.mkdir()
    write_json(
        route / "KIAP_CONTEXT_ANCHOR.json",
        {"route_status": "IN_PROGRESS", "completion_claim": False},
    )
    (route / "KIAP_ACTION_QUEUE.md").write_text(
        "\n".join(
            [
                "4. [x]",
                "5. [x]",
                "6. [x]",
                "7. [x]" if close_development_gate else "7. [ ]",
                "8. [x]" if close_item8_gate else ("8. [ ]" if close_development_gate else ""),
                "9. [ ]" if close_item8_gate else "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (route / "COMPLETION_AUDIT.md").write_text(
        "Completion status: `IN_PROGRESS`\n",
        encoding="utf-8",
    )
    write_jsonl(route / "KIAP_ACTIVE_QUESTION_STACK.jsonl", [{"status": "answered"}])
    write_jsonl(route / "KIAP_CHECKPOINT_LEDGER.jsonl", [{"checkpoint_id": "cp"}])
    write_jsonl(route / "KIAP_LIMITATION_BACKLOG.jsonl", [{"status": "open"}])
    write_json(route / "KIAP_RUNTIME_PARITY_PROOF.json", proof_payload())
    write_json(route / "KIAP_RUNTIME_PARITY_CHECKLIST.json", {"checklist_status": "passed"})
    write_json(route / "KIAP_ROLLING_RUN_STATE.json", {"completion_claim": False})
    write_json(route / "KIAP_FOCUSED_TEST_RESULT.json", {"status": "passed"})
    write_json(route / "KIAP_VERIFICATION_RESULT.json", {"status": "pending"})
    write_json(route / "KIAP_ROUTE_ARTIFACT_AUDIT_RESULT.json", {"ok": True})
    write_json(
        route / "KIAP_OUTPUT_MANIFEST.json",
        {
            "raw_export_scratch_committed": False,
            "prior_kia_duplicate_ledgers_included": False,
            "artifacts": [],
        },
    )
    write_json(
        route / "KIAP_SCRATCH_CLEANUP_PROOF.json",
        {"raw_export_scratch_committed": False},
    )
    (route / "KIAP_SATURATION_SELF_RED_TEAM.md").write_text("Saturation status\n", encoding="utf-8")
    (route / "verify_kiap_route.py").write_text("# fixture\n", encoding="utf-8")

    order = {
        "simulated_order_id": "order-1",
        "candidate_id": "candidate-1",
        "order_status": "filled",
        "symbol": "XAUUSD",
        "decision_time_utc": "2026-04-20T07:15:00+00:00",
        "expiry_utc": "2026-04-20T11:15:00+00:00",
        "phase": "smoke",
    }
    oracle = {
        "candidate_id": "candidate-1",
        "source": "m1" if m1_violation else "tick",
        "ordered_tick_truth_satisfied": not m1_violation,
    }
    trade = {"simulated_order_id": "order-1", "candidate_id": "candidate-1"}
    rollup = {"selected_order_count": 1, "filled_trade_count": 1}
    smoke_summary = {
        "status": "completed",
        "source_primary_hydration_complete": True,
        "no_live_broker_mutation": True,
        "row_counts": {
            "candidate": 1,
            "order": 1,
            "oracle": 1,
            "account": 1,
            "daily": 1,
        },
        "rollup_reconciliation": {"status": "passed"},
    }
    write_json(route / "KIAP_SMOKE_REPLAY_SUMMARY.json", smoke_summary)
    for key, filename in kiap.KIAP_SMOKE_LEDGER_FILES.items():
        rows = []
        if key == "order":
            rows = [order]
        elif key == "oracle":
            rows = [oracle]
        elif key == "trade":
            rows = [trade]
        elif key == "rollup":
            rows = [rollup]
        elif key in {"candidate", "account", "daily"}:
            rows = [{"fixture": key}]
        write_jsonl(route / filename, rows)
    write_jsonl(route / "KIAP_RISK_LOCKOUT_CAUSAL_CHAIN_LEDGER.jsonl", [])
    write_jsonl(route / "KIAP_WEEKLY_MICROSCOPE_SUMMARY.jsonl", [{"fixture": True}])

    requirement = {
        "simulated_order_id": "order-1",
        "source_requirement_id": "sr-1",
        "required_source_type": "TICK",
        "source_broker": "FTMO",
        "source_truth_scope": SOURCE_TRUTH_SCOPE,
        "not_redacted_account_native": True,
        "broker_lifecycle_truth_satisfied": False,
    }
    selected_truth = {
        **requirement,
        "path_source": "m1" if m1_violation else "tick",
        "ordered_tick_truth_satisfied": not m1_violation,
        "selected_tick_truth_verification_status": (
            "failed_unlabeled_m1_or_missing_tick_truth" if m1_violation else "passed_tick_truth"
        ),
        "m1_fallback_violation": m1_violation,
    }
    requirements = [requirement]
    selected_truth_rows = [selected_truth]
    if include_development:
        dev_order = {
            **order,
            "simulated_order_id": "dev-order-1",
            "candidate_id": "dev-candidate-1",
            "decision_time_utc": "2026-04-21T07:15:00+00:00",
            "expiry_utc": "2026-04-21T11:15:00+00:00",
            "phase": "development",
        }
        dev_oracle = {
            **oracle,
            "candidate_id": "dev-candidate-1",
            "source": "tick",
            "ordered_tick_truth_satisfied": True,
        }
        for key, filename in kiap.KIAP_DEVELOPMENT_LEDGER_FILES.items():
            rows = []
            if key == "asof":
                rows = [
                    {
                        "raw_data_status": "live_equivalent_raw_data_built_and_mso_computed",
                        "symbol": "XAUUSD",
                        "decision_time_utc": "2026-04-21T07:15:00+00:00",
                        "no_future_decision_rows": True,
                        "m1_or_tick_attached_to_decision": False,
                        "source_broker": "FTMO",
                        "source_truth_scope": SOURCE_TRUTH_SCOPE,
                    }
                ]
            elif key == "order":
                rows = [dev_order]
            elif key == "oracle":
                rows = [dev_oracle]
            elif key == "trade":
                rows = [{"simulated_order_id": "dev-order-1", "candidate_id": "dev-candidate-1"}]
            elif key == "rollup":
                rows = [{"selected_order_count": 1, "filled_trade_count": 1}]
            elif key in {"candidate", "account", "daily"}:
                rows = [{"fixture": key}]
            write_jsonl(route / filename, rows)
        write_jsonl(route / "KIAP_DEVELOPMENT_RISK_LOCKOUT_CAUSAL_CHAIN_LEDGER.jsonl", [])
        write_jsonl(route / "KIAP_DEVELOPMENT_WEEKLY_MICROSCOPE_SUMMARY.jsonl", [{"fixture": True}])
        write_json(
            route / "KIAP_DEVELOPMENT_REPLAY_SUMMARY.json",
            {
                "status": "completed",
                "full_development_tranche_claim": False,
                "no_live_broker_mutation": True,
                "row_counts": {"candidate": 1, "order": 1, "oracle": 1, "daily": 1},
                "rollup_reconciliation": {"status": "passed"},
            },
        )
        dev_requirement = {
            **requirement,
            "simulated_order_id": "dev-order-1",
            "candidate_id": "dev-candidate-1",
            "phase": "development",
        }
        dev_selected_truth = {
            **selected_truth,
            "simulated_order_id": "dev-order-1",
            "candidate_id": "dev-candidate-1",
            "phase": "development",
            "path_source": "tick",
            "ordered_tick_truth_satisfied": True,
            "selected_tick_truth_verification_status": "passed_tick_truth",
            "m1_fallback_violation": False,
        }
        requirements.append(dev_requirement)
        selected_truth_rows.append(dev_selected_truth)
    write_jsonl(route / "KIAP_SOURCE_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(route / "KIAP_SELECTED_TICK_TRUTH_VERIFICATION_LEDGER.jsonl", selected_truth_rows)
    write_jsonl(route / "KIAP_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl", [])
    write_jsonl(
        route / "KIAP_SOURCE_HYDRATION_LEDGER.jsonl",
        [
            {
                "kiap_source_row_id": "source-1",
                "source_broker": "FTMO",
                "source_truth_scope": SOURCE_TRUTH_SCOPE,
                "not_redacted_account_native": True,
                "broker_lifecycle_truth_satisfied": False,
            }
        ],
    )
    return route


def test_kiap_verifier_accepts_minimal_tick_truth_route(tmp_path: Path) -> None:
    minimal_repo_source(tmp_path)
    route = write_minimal_route(tmp_path)

    result = kiap.verify_route(repo_root=tmp_path, route_dir=route, write_result=False)

    assert result["status"] == "passed"


def test_kiap_verifier_rejects_unlabeled_selected_m1_fallback(tmp_path: Path) -> None:
    minimal_repo_source(tmp_path)
    route = write_minimal_route(tmp_path, m1_violation=True)

    result = kiap.verify_route(repo_root=tmp_path, route_dir=route, write_result=False)

    assert result["status"] == "failed"
    failed_checks = {check["check"] for check in result["checks"] if check["status"] == "failed"}
    assert "selected_tick_truth_no_unlabeled_m1" in failed_checks


def test_kiap_verifier_requires_development_ledgers_when_gate_7_closes(tmp_path: Path) -> None:
    minimal_repo_source(tmp_path)
    route = write_minimal_route(tmp_path, close_development_gate=True)

    result = kiap.verify_route(repo_root=tmp_path, route_dir=route, write_result=False)

    assert result["status"] == "failed"
    failed_checks = {check["check"] for check in result["checks"] if check["status"] == "failed"}
    assert "kiap_development_checkpoint_materialized" in failed_checks


def test_kiap_verifier_accepts_minimal_development_checkpoint(tmp_path: Path) -> None:
    minimal_repo_source(tmp_path)
    route = write_minimal_route(
        tmp_path,
        close_development_gate=True,
        include_development=True,
    )

    result = kiap.verify_route(repo_root=tmp_path, route_dir=route, write_result=False)

    assert result["status"] == "passed"


def test_kiap_verifier_requires_item8_tranches_when_gate_8_closes(tmp_path: Path) -> None:
    minimal_repo_source(tmp_path)
    route = write_minimal_route(
        tmp_path,
        close_development_gate=True,
        close_item8_gate=True,
        include_development=True,
    )

    result = kiap.verify_route(repo_root=tmp_path, route_dir=route, write_result=False)

    assert result["status"] == "failed"
    failed_checks = {check["check"] for check in result["checks"] if check["status"] == "failed"}
    assert "kiap_item8_tranches_materialized" in failed_checks


def test_source_requirement_rows_split_exact_zero_tick_gaps() -> None:
    requirements, selected_truth, current_gaps = kiap._requirement_rows(
        order_rows=[
            {
                "simulated_order_id": "order-1",
                "candidate_id": "candidate-1",
                "symbol": "GBPUSD",
                "decision_time_utc": "2026-04-20T23:59:00+00:00",
                "expiry_utc": "2026-04-21T00:01:00+00:00",
            }
        ],
        oracle_rows=[
            {
                "candidate_id": "candidate-1",
                "source": "m1",
                "ordered_tick_truth_satisfied": False,
            }
        ],
        prior_gap_rows=[
            {
                "gap_id": "gap-1",
                "symbol": "GBPUSD",
                "request_start_utc": "2026-04-20T23:59:00+00:00",
                "request_end_utc": "2026-04-21T00:01:00+00:00",
                "source_bound_status": "exact_zero_row_manifest_window_retry_confirmed",
            }
        ],
    )

    assert requirements[0]["requirement_status"] == "unresolved_exact_zero_row_ftmo_tick_source_bound"
    assert selected_truth[0]["selected_tick_truth_verification_status"] == "unresolved_exact_zero_row_source_requirement_split"
    assert current_gaps[0]["final_performance_inclusion_status"] == "excluded_unresolved_source_requirement"


def test_source_requirement_rows_use_order_window_not_repeated_candidate_fallback() -> None:
    requirements, selected_truth, current_gaps = kiap._requirement_rows(
        order_rows=[
            {
                "campaign": "kiap_holdout_rolling_20260430",
                "phase": "holdout_rolling",
                "simulated_order_id": "order-1",
                "candidate_id": "candidate-repeat",
                "symbol": "UKOIL_cash",
                "decision_time_utc": "2026-04-30T00:15:00+00:00",
                "expiry_utc": "2026-04-30T02:15:00+00:00",
            },
            {
                "campaign": "kiap_holdout_rolling_20260430",
                "phase": "holdout_rolling",
                "simulated_order_id": "order-2",
                "candidate_id": "candidate-repeat",
                "symbol": "UKOIL_cash",
                "decision_time_utc": "2026-04-30T02:15:00+00:00",
                "expiry_utc": "2026-04-30T04:15:00+00:00",
            },
        ],
        oracle_rows=[
            {
                "campaign": "kiap_holdout_rolling_20260430",
                "phase": "holdout_rolling",
                "candidate_id": "candidate-repeat",
                "asof_utc": "2026-04-30T00:15:00+00:00",
                "expiry_utc": "2026-04-30T02:15:00+00:00",
                "source": "m1",
                "ordered_tick_truth_satisfied": False,
                "source_path": "combined_ftmo_day_sources/UKOIL_cash_M1",
            },
            {
                "campaign": "kiap_holdout_rolling_20260430",
                "phase": "holdout_rolling",
                "candidate_id": "candidate-repeat",
                "asof_utc": "2026-04-30T02:15:00+00:00",
                "expiry_utc": "2026-04-30T04:15:00+00:00",
                "source": "tick",
                "ordered_tick_truth_satisfied": True,
                "path_row_count": 3643,
                "source_path": "combined_ftmo_tick_sources/UKOIL_cash_TICK",
            },
        ],
        prior_gap_rows=[],
    )

    assert current_gaps == []
    by_order = {row["simulated_order_id"]: row for row in selected_truth}
    assert by_order["order-1"]["selected_tick_truth_verification_status"] == "failed_unlabeled_m1_or_missing_tick_truth"
    assert by_order["order-2"]["selected_tick_truth_verification_status"] == "passed_tick_truth"
    assert by_order["order-2"]["path_source"] == "tick"
    assert by_order["order-2"]["path_row_count"] == 3643
    assert {row["simulated_order_id"] for row in requirements} == {"order-1", "order-2"}


def test_item9_classifies_all_repair_families_without_topn() -> None:
    ledger_files = {
        "trade": "trades.jsonl",
        "rollup": "rollups.jsonl",
        "missed": "missed.jsonl",
        "order": "orders.jsonl",
    }
    families = kiap._item9_classify_phase_rows(
        phase="full_development",
        ledger_files=ledger_files,
        trades=[
            {
                "simulated_order_id": "trade-weak",
                "symbol": "XAUUSD",
                "gross_r": -1.0,
                "net_proxy_r": -1.18,
            },
            {
                "simulated_order_id": "trade-cost-flip",
                "symbol": "EURUSD",
                "gross_r": 0.05,
                "expected_cost_r": 0.18,
                "net_proxy_r": -0.13,
            },
        ],
        rollups=[
            {
                "symbol": "XAUUSD",
                "policy": "partial_be_runner",
                "candidate_count": 3,
                "filled_trade_count": 1,
                "net_proxy_r": -0.5,
            }
        ],
        missed=[
            {
                "candidate_id": "missed-1",
                "symbol": "GBPUSD",
                "miss_reason": "scheduler_selected_competing_candidate",
                "net_proxy_r": 1.25,
            },
            {
                "candidate_id": "missed-negative",
                "symbol": "GBPUSD",
                "miss_reason": "scheduler_selected_competing_candidate",
                "net_proxy_r": -0.2,
            },
        ],
        orders=[
            {
                "simulated_order_id": "order-risk",
                "symbol": "NAS100",
                "order_status": "risk_rejected",
                "risk_decision_reason": "risk_headroom_zero",
            }
        ],
    )

    assert len(families["weak_accepted_trades"]) == 2
    assert len(families["cost_flips"]) == 1
    assert len(families["partial_be_runner"]) == 1
    assert len(families["scheduler_regret"]) == 1
    assert len(families["risk_headroom_lockout"]) == 1
    assert families["scheduler_regret"][0]["kiap_item9_source_ledger"] == "missed.jsonl"


def test_item10_selected_candidate_attribution_uses_order_decision_window(tmp_path: Path) -> None:
    minimal_repo_source(tmp_path)
    route = write_minimal_route(tmp_path)

    missing = kiap._item10_selected_candidate_attribution_diagnostics(route, ["smoke"])

    assert missing["status"] == "failed"
    assert "missing_candidate_row_for_selected_order_window" in missing["failures"][0]

    write_jsonl(
        route / kiap.KIAP_SMOKE_LEDGER_FILES["candidate"],
        [
            {
                "phase": "smoke",
                "candidate_id": "candidate-1",
                "decision_time_utc": "2026-04-20T07:15:00+00:00",
                "selected_candidate_execution_attribution_status": "not_selected_yet",
            }
        ],
    )
    unattributed = kiap._item10_selected_candidate_attribution_diagnostics(route, ["smoke"])

    assert unattributed["status"] == "failed"
    assert "candidate_not_attributed_by_selected_candidate_id" in unattributed["failures"][0]

    write_jsonl(
        route / kiap.KIAP_SMOKE_LEDGER_FILES["candidate"],
        [
            {
                "phase": "smoke",
                "candidate_id": "candidate-1",
                "decision_time_utc": "2026-04-20T07:15:00+00:00",
                "selected_candidate_execution_attribution_status": "attributed_by_selected_candidate_id",
            }
        ],
    )
    attributed = kiap._item10_selected_candidate_attribution_diagnostics(route, ["smoke"])

    assert attributed["status"] == "passed"
    assert attributed["latest_selected_order_rows"] == 1


def test_item10_order_oracle_source_attribution_requires_exact_window(tmp_path: Path) -> None:
    minimal_repo_source(tmp_path)
    route = write_minimal_route(tmp_path)
    write_jsonl(
        route / kiap.KIAP_SMOKE_LEDGER_FILES["oracle"],
        [
            {
                "phase": "smoke",
                "candidate_id": "candidate-1",
                "asof_utc": "2026-04-20T07:15:00+00:00",
                "expiry_utc": "2026-04-20T11:15:00+00:00",
                "source": "tick",
                "ordered_tick_truth_satisfied": True,
            }
        ],
    )
    requirement = {
        "phase": "smoke",
        "simulated_order_id": "order-1",
        "candidate_id": "candidate-1",
        "decision_time_utc": "2026-04-20T07:15:00+00:00",
        "expiry_utc": "2026-04-20T11:15:00+00:00",
        "required_source_type": "TICK",
        "local_indexed_tick_lookup_attempted": True,
        "source_truth_scope": SOURCE_TRUTH_SCOPE,
    }
    selected_truth = {
        **requirement,
        "path_source": "tick",
        "ordered_tick_truth_satisfied": True,
        "selected_tick_truth_verification_status": "passed_tick_truth",
        "m1_fallback_violation": False,
    }
    write_jsonl(route / "KIAP_SOURCE_REQUIREMENT_LEDGER.jsonl", [requirement])
    write_jsonl(route / "KIAP_SELECTED_TICK_TRUTH_VERIFICATION_LEDGER.jsonl", [selected_truth])

    passed = kiap._item10_order_oracle_source_diagnostics(route, ["smoke"])

    assert passed["status"] == "passed"
    assert passed["passed_tick_truth_rows"] == 1

    write_jsonl(
        route / "KIAP_SELECTED_TICK_TRUTH_VERIFICATION_LEDGER.jsonl",
        [{**selected_truth, "expiry_utc": "2026-04-20T12:15:00+00:00"}],
    )
    failed = kiap._item10_order_oracle_source_diagnostics(route, ["smoke"])

    assert failed["status"] == "failed"
    assert "selected_truth_window_key_mismatch" in failed["failures"][0]
