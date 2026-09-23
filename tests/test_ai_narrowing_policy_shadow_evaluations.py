from __future__ import annotations

import json
from pathlib import Path

from scripts import backfill_ai_narrowing_policy_shadow_evaluations as mod


def _scope(**overrides):
    row = {
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny",
        "horizon_id": "live_candidate_decision",
        "source_component": "primary_analyzer_live_candidate",
        "selected_side": "LONG",
    }
    row.update(overrides)
    return row


def _policy(**overrides):
    row = {
        **_scope(),
        "ai_narrowing_policy_row_id": "POLICY-1",
        "ai_narrowing_policy_status": "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY",
        "ai_role_after_owner_approval": "MECHANICAL_SELECTOR_CAN_PRECEDE_AI_FOR_SCOPE_AFTER_REVIEW",
    }
    row.update(overrides)
    return row


def _candidate(**overrides):
    row = {
        **_scope(),
        "candidate_id": "XAUUSD_2026-05-18T13:30:00+00:00",
        "decision_time_utc": "2026-05-18T13:30:00+00:00",
        "schema_version": "strategy_follow_candidate_v1",
    }
    row.update(overrides)
    return row


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_shadow_evaluation_matches_policy_without_runtime_enablement(tmp_path):
    rows = mod.build_shadow_evaluations(
        candidate_rows=[(7, _candidate())],
        policy_rows=[_policy()],
        candidate_source_path=tmp_path / "candidates.jsonl",
        candidate_source_sha256="candidate-sha",
        policy_ledger_path=tmp_path / "policy.jsonl",
        policy_ledger_sha256="policy-sha",
        generated_at_utc="2026-05-18T00:00:00+00:00",
    )
    report = mod.build_report(
        rows=rows,
        appended_rows=rows,
        output_path=tmp_path / "out.jsonl",
        candidate_rows=1,
        policy_rows=1,
        candidate_source_sha256="candidate-sha",
        policy_ledger_sha256="policy-sha",
    )

    row = rows[0]
    assert row["event_adapter_status"] == "AI_NARROWING_EVENT_CONTRACT_COMPLETE"
    assert row["missing_required_fields"] == []
    assert row["ai_narrowing_registry_eval_status"] == "AI_NARROWING_REGISTRY_MATCH_PRE_AI_SELECTOR_REVIEW_READY"
    assert row["matched_policy_rows"] == 1
    assert row["ai_narrowing_review_ready"] is True
    assert row["ai_call_skip_allowed_now"] is False
    assert row["runtime_candidate_use_permitted"] is False
    assert row["live_ai_runtime_change_now"] is False
    assert row["paid_api_or_vendor_call"] is False
    assert report["ai_call_skip_allowed_now_rows"] == 0
    assert report["registry_eval_status_counts"] == {"AI_NARROWING_REGISTRY_MATCH_PRE_AI_SELECTOR_REVIEW_READY": 1}


def test_incomplete_candidate_contract_keeps_ai_gate(tmp_path):
    incomplete = _candidate(source_symbol=None, horizon_id=None)
    rows = mod.build_shadow_evaluations(
        candidate_rows=[(3, incomplete)],
        policy_rows=[_policy()],
        candidate_source_path=tmp_path / "candidates.jsonl",
        candidate_source_sha256="candidate-sha",
        policy_ledger_path=tmp_path / "policy.jsonl",
        policy_ledger_sha256="policy-sha",
        generated_at_utc="2026-05-18T00:00:00+00:00",
    )

    row = rows[0]
    assert row["event_adapter_status"] == "AI_NARROWING_EVENT_CONTRACT_INCOMPLETE"
    assert row["ai_narrowing_registry_eval_status"] == "AI_NARROWING_REGISTRY_NO_POLICY_MATCH_KEEP_AI"
    assert "source_symbol" in row["missing_required_fields"]
    assert "horizon_id" in row["missing_required_fields"]
    assert row["ai_narrowing_review_ready"] is False
    assert row["ai_call_skip_allowed_now"] is False
    assert row["production_change_opened_now"] is False


def test_cli_appends_shadow_rows_idempotently_and_writes_reports(tmp_path):
    candidate_path = tmp_path / "strategy_follow_candidates.jsonl"
    policy_path = tmp_path / "policy.jsonl"
    output_path = tmp_path / "ai_narrowing_policy_shadow_evaluations.jsonl"
    report_json = tmp_path / "report.json"
    report_md = tmp_path / "report.md"
    _write_jsonl(candidate_path, [_candidate()])
    _write_jsonl(policy_path, [_policy()])

    first_rc = mod.main(
        [
            "--candidates",
            str(candidate_path),
            "--policy-ledger",
            str(policy_path),
            "--output",
            str(output_path),
            "--report-json",
            str(report_json),
            "--report-md",
            str(report_md),
        ]
    )
    second_rc = mod.main(
        [
            "--candidates",
            str(candidate_path),
            "--policy-ledger",
            str(policy_path),
            "--output",
            str(output_path),
            "--report-json",
            str(report_json),
            "--report-md",
            str(report_md),
        ]
    )
    rows = _read_jsonl(output_path)
    report = json.loads(report_json.read_text(encoding="utf-8"))

    assert first_rc == 0
    assert second_rc == 0
    assert len(rows) == 1
    assert report["rows_computed"] == 1
    assert report["rows_appended_this_run"] == 0
    assert report["ai_call_skip_allowed_now_rows"] == 0
    assert "do not skip AI" in report_md.read_text(encoding="utf-8")
