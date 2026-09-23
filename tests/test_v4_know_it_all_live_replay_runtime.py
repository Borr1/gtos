from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.research_infra.v4_know_it_all_live_replay_runtime as kia
from src.research_infra.v4_timewarp_simulated_live_research_loop import (
    ROUTE_ID as TIMEWARP_ROUTE_ID,
    SOURCE_TRUTH_SCOPE,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def zero_row_tick_payload(*, symbol: str, mapped_symbol: str, manifest_path: Path) -> dict:
    return {
        "asof_decision_truth_satisfied": False,
        "broker_lifecycle_truth_satisfied": False,
        "chunks_requested": 1,
        "chunks_with_rows": 0,
        "empty_chunks": 1,
        "export_tool": "scripts/export_mt5_research_ticks.py",
        "file_symbol": symbol,
        "first": None,
        "last": None,
        "last_empty_chunk_error": "(1, 'Success')",
        "manifest_path": str(manifest_path),
        "mt5_symbol": mapped_symbol,
        "not_redacted_account_native": True,
        "path": f"fixture/ticks/{symbol}/sel_002_20260420T2359_20260421T0001_ticks.jsonl",
        "raw_rows_returned": 0,
        "replaces_missing_frozen_path_source": False,
        "request_end_utc": "2026-04-21T00:01:00+00:00",
        "request_start_utc": "2026-04-20T23:59:00+00:00",
        "row_count": 0,
        "rows": 0,
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "source_account_hash": "c" * 64,
        "source_account_redacted": "redacted",
        "source_broker": "FTMO",
        "source_role": "owner_authorized_research_hydration",
        "source_server_hash": "b" * 64,
        "source_server_redacted": "redacted",
        "source_truth_scope": SOURCE_TRUTH_SCOPE,
        "timeframe": "TICK",
        "window": "sel_002_20260420T2359_20260421T0001",
    }


def minimal_previous_timewarp_route(tmp_path: Path) -> Path:
    (tmp_path / "src/components").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src/components/orchestrator.py").write_text(
        "\n".join(
            [
                "from src.components.v4_live_replay_decision_core import V4DecisionCycleCore",
                "class SessionOrchestrator:",
                "    def __init__(self):",
                "        self._v4_decision_cycle_core = V4DecisionCycleCore(config={})",
                "    def _process_vnext_broader_origin_candidates(self):",
                "        self._v4_decision_cycle_core.generate_candidates(raw_data={}, mso=None, symbol='XAUUSD', kill_zone='fixture')",
                "        self._v4_decision_cycle_core.decision_window_candidate_summaries([])",
                "        ingest_live_data = True",
                "        generate_live_broader_origin_candidates = True",
                "        evaluate_execution_manager_v4 = True",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "src/research_infra").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src/research_infra/v4_timewarp_simulated_live_research_loop.py").write_text(
        "\n".join(
            [
                "from src.components.v4_live_replay_decision_core import V4DecisionCycleCore",
                "decision_core = V4DecisionCycleCore(",
                "    config={},",
                "    sources={},",
                "    candidate_evaluator=evaluate_candidate_v4,",
                "    scheduler_allocator=materialize_scheduler_window,",
                ")",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    route = tmp_path / "previous_timewarp"
    route.mkdir()
    write_json(
        route / "TIMEWARP_VERIFICATION_RESULT.json",
        {
            "route_id": TIMEWARP_ROUTE_ID,
            "status": "passed",
            "failure_count": 0,
        },
    )
    write_json(
        route / "TIMEWARP_LIVE_REPLAY_PARITY_CHECKLIST.json",
        {
            "route_id": TIMEWARP_ROUTE_ID,
            "full_live_replay_parity_status": "failed",
            "checks": [
                {
                    "check": "direct_production_orchestrator_instantiation",
                    "status": "failed",
                    "details": "fixture boot path is live-side-effectful",
                }
            ],
        },
    )
    write_json(
        route / "TIMEWARP_REPAIR_BEFORE_AFTER_SUMMARY.json",
        {
            "baseline": {"total_r": -1.0, "filled_trades": 2},
            "repaired": {"total_r": -2.0, "filled_trades": 3},
            "delta": {"total_r": -1.0},
            "repair_count": 1,
            "production_change_claim": False,
        },
    )
    write_json(
        route / "TIMEWARP_HOLDOUT_RESULT_SUMMARY.json",
        {
            "phase": "holdout",
            "total_r": -3.0,
            "filled_trades": 1,
            "winners": 0,
            "losses": 1,
        },
    )
    write_json(
        route / "TIMEWARP_SELECTED_ORDER_TICK_EXPORT_RUN_SUMMARY.json",
        {
            "exports": [
                {"symbol": "GBPUSD", "row_count_total": 0, "errors": 1},
                {"symbol": "US30_cash", "row_count_total": 0, "errors": 1},
                {"symbol": "XAUUSD", "row_count_total": 10, "errors": 0},
            ]
        },
    )
    gap_manifest_specs = [
        (
            "GBPUSD",
            "GBPUSD",
            "GBPUSD_sel_002_20260420T2359_20260421T0001_TICK",
            route
            / "ftmo_research_exports"
            / "timewarp_ftmo_selected_order_ticks_GBPUSD_20260607"
            / "manifest.json",
        ),
        (
            "US30_cash",
            "US30.cash",
            "US30_cash_sel_002_20260420T2359_20260421T0001_TICK",
            route
            / "ftmo_research_exports"
            / "timewarp_ftmo_selected_order_ticks_US30_cash_20260607"
            / "manifest.json",
        ),
    ]
    for symbol, mapped_symbol, key, manifest_path in gap_manifest_specs:
        payload = zero_row_tick_payload(
            symbol=symbol,
            mapped_symbol=mapped_symbol,
            manifest_path=manifest_path,
        )
        write_json(
            manifest_path,
            {
                "schema_version": "mt5_research_tick_export_v1",
                "read_only": True,
                "label": f"fixture_{symbol}_selected_ticks",
                "mt5_client_kind": "siliconmetatrader5_bridge",
                "source_provenance": {
                    "source_broker": "FTMO",
                    "source_role": "owner_authorized_research_hydration",
                    "source_truth_scope": SOURCE_TRUTH_SCOPE,
                    "not_redacted_account_native": True,
                    "broker_lifecycle_truth_satisfied": False,
                    "asof_decision_truth_satisfied": False,
                    "replaces_missing_frozen_path_source": False,
                },
                "errors": [
                    {
                        "error": "no_ticks:(1, 'Success')",
                        "file_symbol": symbol,
                        "mt5_symbol": mapped_symbol,
                        "window": "sel_002_20260420T2359_20260421T0001",
                    }
                ],
                "files": {key: payload},
            },
        )
    write_json(
        route / "TIMEWARP_SOURCE_MANIFEST.json",
        {
            "ftmo_primary_hydration_complete": True,
            "sources": [
                {
                    "symbol": "XAUUSD",
                    "mapped_symbol": "XAUUSD",
                    "timeframe": "M1",
                    "source_broker": "FTMO",
                    "source_role": "owner_authorized_research_hydration",
                    "source_truth_scope": SOURCE_TRUTH_SCOPE,
                    "not_redacted_account_native": True,
                    "broker_lifecycle_truth_satisfied": False,
                    "ordered_tick_truth_satisfied": False,
                    "row_count": 1440,
                    "sha256": "a" * 64,
                    "path": "fixture/XAUUSD_M1.csv",
                    "manifest_path": "fixture/manifest.json",
                    "export_tool": "fixture_export.py",
                    "selected_status": "selected_source_meets_day_floor",
                },
                {
                    "symbol": "XAUUSD",
                    "mapped_symbol": "XAUUSD",
                    "timeframe": "TICK",
                    "source_broker": "FTMO",
                    "source_role": "owner_authorized_research_hydration",
                    "source_truth_scope": SOURCE_TRUTH_SCOPE,
                    "not_redacted_account_native": True,
                    "broker_lifecycle_truth_satisfied": False,
                    "ordered_tick_truth_satisfied": True,
                    "row_count": 10,
                    "sha256": "b" * 64,
                    "path": "fixture/XAUUSD_ticks.jsonl",
                    "manifest_path": "fixture/tick_manifest.json",
                    "export_tool": "fixture_tick_export.py",
                    "selected_status": "selected_priority_tick_source",
                },
            ],
        },
    )
    write_jsonl(route / "TIMEWARP_CANDIDATE_MICROSCOPE_LEDGER.jsonl", [{"candidate_id": "c1"}])
    write_jsonl(
        route / "TIMEWARP_SIMULATED_TRADE_LEDGER.jsonl",
        [
            {
                "phase": "baseline",
                "campaign": "baseline",
                "trade_id": "t1",
                "candidate_id": "c1",
                "symbol": "XAUUSD",
                "net_proxy_r": -1.18,
                "gross_r": -1.0,
                "expected_cost_r": 0.18,
                "mfe_r": 0.2,
                "production_change_claim": False,
                "broker_runtime_change_status": False,
            }
        ],
    )
    write_jsonl(
        route / "TIMEWARP_SIMULATED_ORDER_LEDGER.jsonl",
        [
            {
                "phase": "baseline",
                "campaign": "baseline",
                "candidate_id": "c2",
                "symbol": "GBPUSD",
                "order_status": "risk_rejected",
                "risk_decision_reason": "risk_headroom_zero",
                "production_change_claim": False,
                "broker_runtime_change_status": False,
            }
        ],
    )
    write_jsonl(
        route / "TIMEWARP_MISSED_OPPORTUNITY_LEDGER.jsonl",
        [
            {
                "phase": "baseline",
                "campaign": "baseline",
                "candidate_id": "c3",
                "symbol": "AUDUSD",
                "miss_reason": "scheduler_selected_competing_candidate",
                "net_proxy_r": 2.82,
                "gross_r": 3.0,
                "expected_cost_r": 0.18,
                "production_change_claim": False,
                "broker_runtime_change_status": False,
            },
            {
                "phase": "baseline",
                "campaign": "baseline",
                "candidate_id": "c4",
                "symbol": "EURUSD",
                "miss_reason": "scheduler_selected_competing_candidate",
                "net_proxy_r": -0.02,
                "gross_r": 0.16,
                "expected_cost_r": 0.18,
                "production_change_claim": False,
                "broker_runtime_change_status": False,
            },
        ],
    )
    write_jsonl(
        route / "TIMEWARP_SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP.jsonl",
        [
            {
                "phase": "baseline",
                "campaign": "baseline",
                "symbol": "XAUUSD",
                "session": "london",
                "framework": "fixture",
                "policy": "partial_be_runner",
                "filled_trade_count": 1,
                "winner_count": 0,
                "loser_count": 1,
                "net_proxy_r": -1.18,
                "expected_cost_r": 0.18,
                "production_change_claim": False,
                "broker_runtime_change_status": False,
            }
        ],
    )
    return route


def focused_passed_payload() -> dict:
    return {
        "command": ["pytest", "fixture"],
        "returncode": 0,
        "stdout": "fixture passed",
        "stderr": "",
        "status": "passed",
    }


def write_minimal_smoke_replay(route: Path) -> dict:
    row_counts: dict[str, int] = {}
    for key, filename in kia.KIA_SMOKE_LEDGER_FILES.items():
        row = {
            "fixture_smoke_key": key,
            "kia_route_id": kia.ROUTE_ID,
            "kia_smoke_replay": True,
            "simulated_broker_adapter": "SimulatedBroker",
            "broker_mutation_enabled": False,
            "broker_history_truth_satisfied": False,
            "broker_account_order_history_deal_position_mutation": False,
        }
        if key in {"candidate", "order", "oracle"}:
            row["path_truth_index"] = "PathTruthIndex"
        if key == "oracle":
            row["path_index_lookup_mode"] = "day_time_bisect_index"
            row["ordered_tick_truth_satisfied"] = True
        write_jsonl(route / filename, [row])
        row_counts[key] = 1
    summary = {
        "route_id": kia.ROUTE_ID,
        "status": "completed",
        "smoke_day": "fixture-day",
        "source_primary_hydration_complete": True,
        "row_counts": row_counts,
        "campaign_summary": {"candidate_rows": 1, "simulated_orders": 1, "filled_trades": 1},
        "no_live_broker_mutation": True,
        "no_paid_api": True,
        "no_remote_push": True,
        "production_change_claim": False,
    }
    write_json(route / "KIA_SMOKE_REPLAY_SUMMARY.json", summary)
    return summary


def write_minimal_repair_rerun(route: Path) -> dict:
    for files in (kia.KIA_REPAIR_LEDGER_FILES, kia.KIA_HOLDOUT_LEDGER_FILES):
        for key, filename in files.items():
            row = {
                "campaign": "fixture_repair",
                "phase": "repair_development" if "REPAIR_RERUN" in filename else "holdout_rolling",
                "fixture_repair_key": key,
                "kia_repair_policy_id": kia.KIA_REPAIR_POLICY_ID,
                "kia_decision_tape_replay": True,
                "production_change_claim": False,
                "broker_runtime_change_status": False,
                "paid_api_or_vendor_call": False,
                "remote_push": False,
            }
            if key == "daily":
                row.update(
                    {
                        "trading_day": "2026-04-20",
                        "candidate_rows": 1,
                        "simulated_orders": 1,
                        "filled_trades": 1,
                        "risk_rejected_orders": 0,
                        "expired_unfilled_orders": 0,
                        "not_filled_orders": 0,
                        "gross_r": 0.5,
                        "expected_cost_r": 0.1,
                        "net_proxy_r": 0.4,
                        "total_r": 0.4,
                    }
                )
            write_jsonl(route / filename, [row])
    repair_summary = {
        "route_id": kia.ROUTE_ID,
        "status": "completed",
        "phase": "repair_development",
        "decision_tape_replay": True,
        "total_r": 0.4,
        "filled_trades": 1,
        "risk_rejected_orders": 0,
        "production_change_claim": False,
        "broker_runtime_change_status": False,
    }
    holdout_summary = {
        "route_id": kia.ROUTE_ID,
        "status": "completed",
        "phase": "holdout_rolling",
        "decision_tape_replay": True,
        "total_r": 0.4,
        "filled_trades": 1,
        "risk_rejected_orders": 0,
        "production_change_claim": False,
        "broker_runtime_change_status": False,
    }
    before_after = {
        "route_id": kia.ROUTE_ID,
        "status": "completed",
        "repair_policy_id": kia.KIA_REPAIR_POLICY_ID,
        "repair_counts_as_replay_system_repair": True,
        "deltas": {
            "repair_vs_baseline_total_r": 1.4,
            "holdout_vs_previous_holdout_total_r": 3.4,
        },
        "kia_repair_development_summary": repair_summary,
        "kia_holdout_rolling_summary": holdout_summary,
        "production_change_claim": False,
        "broker_runtime_change_status": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
    }
    write_json(route / "KIA_SYSTEM_REPAIR_RERUN_SUMMARY.json", repair_summary)
    write_json(route / "KIA_SYSTEM_REPAIR_HOLDOUT_SUMMARY.json", holdout_summary)
    write_json(route / "KIA_SYSTEM_REPAIR_BEFORE_AFTER_SUMMARY.json", before_after)
    return before_after


@pytest.fixture(autouse=True)
def patch_smoke_replay(monkeypatch: pytest.MonkeyPatch):
    def fake_smoke(*, repo_root: Path, route_dir: Path) -> dict:
        return write_minimal_smoke_replay(route_dir)

    def fake_repair(*, route_dir: Path, previous_route_dir: Path, previous_summary: dict) -> dict:
        return write_minimal_repair_rerun(route_dir)

    monkeypatch.setattr(kia, "_write_kia_smoke_replay", fake_smoke)
    monkeypatch.setattr(kia, "_write_system_repair_rerun", fake_repair)


def test_build_route_writes_required_kia_checkpoint_artifacts(tmp_path: Path) -> None:
    previous = minimal_previous_timewarp_route(tmp_path)
    route = tmp_path / "kia_route"
    result = kia.build_route(
        repo_root=tmp_path,
        route_dir=route,
        previous_route_dir=previous,
        run_tests=False,
        focused_test_result=focused_passed_payload(),
    )

    assert result["verification"]["status"] == "passed"
    assert result["smoke_summary"]["status"] == "completed"
    for name in kia.REQUIRED_ARTIFACTS:
        assert (route / name).exists(), name
    assert not (route / "_scratch").exists()

    source_rows = [
        json.loads(line)
        for line in (route / "KIA_SOURCE_HYDRATION_LEDGER.jsonl").read_text().splitlines()
    ]
    assert len(source_rows) == 2
    assert {row["source_broker"] for row in source_rows} == {"FTMO"}

    artifact_audit = json.loads((route / "KIA_ROUTE_ARTIFACT_AUDIT_RESULT.json").read_text())
    assert artifact_audit["ok"] is True
    assert artifact_audit["missing_required"] == []
    action_queue = (route / "KIA_ACTION_QUEUE.md").read_text(encoding="utf-8")
    assert "[x] Rerun a KIA smoke slice" in action_queue
    assert "[x] Extract or verify a shared live/replay V4 decision-cycle core" in action_queue
    assert "[x] Retry or exactly source-bound the two zero-row selected-order FTMO tick windows" in action_queue
    assert "[x] Run development tranche failure anatomy" in action_queue
    tick_gap_rows = [
        json.loads(line)
        for line in (route / "KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(tick_gap_rows) == 2
    assert {row["source_bound_status"] for row in tick_gap_rows} == {
        "exact_zero_row_manifest_window_previous_route_only"
    }
    assert all(row["ordered_tick_truth_satisfied"] is False for row in tick_gap_rows)
    checkpoints = [
        json.loads(line)
        for line in (route / "KIA_CHECKPOINT_LEDGER.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [row["checkpoint_id"] for row in checkpoints] == [
        "kia_cp001_runtime_adapter_and_route_state",
        "kia_cp002_smoke_replay_materialized",
        "kia_cp003_shared_decision_cycle_core_verified",
        "kia_cp004_tick_gaps_source_bound",
        "kia_cp005_development_failure_anatomy_materialized",
        "kia_cp006_scheduler_single_select_repair_rerun_and_holdout",
    ]
    development_summary = json.loads((route / "KIA_DEVELOPMENT_FAILURE_ANATOMY_SUMMARY.json").read_text())
    assert development_summary["status"] == "completed"
    assert development_summary["family_counts"]["weak_accepted_trades"] == 1
    assert development_summary["family_counts"]["partial_be_runner"] == 1
    assert development_summary["family_counts"]["scheduler_regret"] == 1
    assert development_summary["family_counts"]["cost_flips"] == 1
    assert development_summary["family_counts"]["risk_headroom_lockout"] == 1
    repair_summary = json.loads((route / "KIA_SYSTEM_REPAIR_BEFORE_AFTER_SUMMARY.json").read_text())
    assert repair_summary["status"] == "completed"
    assert repair_summary["production_change_claim"] is False
    assert "[x] Implement only repeated system repairs" in action_queue
    next_starter = (route / kia.KIA_NEXT_STARTER_FILE).read_text(encoding="utf-8")
    saturation = (route / kia.KIA_SATURATION_SELF_RED_TEAM_FILE).read_text(encoding="utf-8")
    completion_audit = (route / "COMPLETION_AUDIT.md").read_text(encoding="utf-8")
    assert next_starter.startswith("/goal Continue from ")
    assert "do not claim production readiness" in next_starter
    assert "Saturation status: completed" in saturation
    assert "The repair did not earn production-change readiness." in saturation
    assert f"Completion status: {kia.KIA_COMPLETION_STATUS}" in completion_audit
    assert "Production-change readiness: false" in completion_audit


def test_verify_route_rejects_action_queue_without_resume_requirements(tmp_path: Path) -> None:
    previous = minimal_previous_timewarp_route(tmp_path)
    route = tmp_path / "kia_route"
    kia.build_route(
        repo_root=tmp_path,
        route_dir=route,
        previous_route_dir=previous,
        run_tests=False,
        focused_test_result=focused_passed_payload(),
    )
    (route / "KIA_ACTION_QUEUE.md").write_text("# KIA Action Queue\n", encoding="utf-8")

    result = kia.verify_route(repo_root=tmp_path, route_dir=route, write_result=False)
    assert result["status"] == "failed"
    assert any(
        check["check"] == "action_queue_followable_after_resume"
        for check in result["checks"]
        if check["status"] == "failed"
    )


def test_verify_route_rejects_completion_overclaim(tmp_path: Path) -> None:
    previous = minimal_previous_timewarp_route(tmp_path)
    route = tmp_path / "kia_route"
    kia.build_route(
        repo_root=tmp_path,
        route_dir=route,
        previous_route_dir=previous,
        run_tests=False,
        focused_test_result=focused_passed_payload(),
    )
    (route / "COMPLETION_AUDIT.md").write_text(
        "# KIA Completion\n\nCompletion status: COMPLETE\n",
        encoding="utf-8",
    )

    result = kia.verify_route(repo_root=tmp_path, route_dir=route, write_result=False)
    assert result["status"] == "failed"
    assert any(
        check["check"] == "completion_audit_not_overclaiming"
        for check in result["checks"]
        if check["status"] == "failed"
    )


def test_verify_route_rejects_smoke_oracle_without_path_index_metadata(tmp_path: Path) -> None:
    previous = minimal_previous_timewarp_route(tmp_path)
    route = tmp_path / "kia_route"
    kia.build_route(
        repo_root=tmp_path,
        route_dir=route,
        previous_route_dir=previous,
        run_tests=False,
        focused_test_result=focused_passed_payload(),
    )
    oracle_rows = [
        json.loads(line)
        for line in (route / "KIA_SMOKE_ORDERED_PATH_ORACLE_LEDGER.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    oracle_rows[0]["path_index_lookup_mode"] = "linear_scan"
    write_jsonl(route / "KIA_SMOKE_ORDERED_PATH_ORACLE_LEDGER.jsonl", oracle_rows)

    result = kia.verify_route(repo_root=tmp_path, route_dir=route, write_result=False)
    assert result["status"] == "failed"
    assert any(
        check["check"] == "kia_smoke_required_metadata"
        for check in result["checks"]
        if check["status"] == "failed"
    )


def test_verify_route_rejects_tick_gap_promoted_to_tick_truth(tmp_path: Path) -> None:
    previous = minimal_previous_timewarp_route(tmp_path)
    route = tmp_path / "kia_route"
    kia.build_route(
        repo_root=tmp_path,
        route_dir=route,
        previous_route_dir=previous,
        run_tests=False,
        focused_test_result=focused_passed_payload(),
    )
    rows = [
        json.loads(line)
        for line in (route / "KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    rows[0]["ordered_tick_truth_satisfied"] = True
    write_jsonl(route / "KIA_TICK_GAP_SOURCE_BOUND_LEDGER.jsonl", rows)

    result = kia.verify_route(repo_root=tmp_path, route_dir=route, write_result=False)
    assert result["status"] == "failed"
    assert any(
        check["check"] == "tick_gap_source_bound_ledger"
        for check in result["checks"]
        if check["status"] == "failed"
    )
