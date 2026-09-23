from __future__ import annotations

import json
from pathlib import Path

from scripts import audit_sierra_proxy_registry as mod
from src.research_infra.sierra_proxy_registry import NO_REGISTERED_PROXY, SOURCE_DEFINITION_BLOCKED, VALIDATED_PROXY


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _candidate(candidate_id: str, symbol: str, broker_symbol: str | None = None) -> dict:
    return {
        "schema_version": "strategy_follow_candidate_v1",
        "row_key": f"candidate|{candidate_id}",
        "candidate_id": candidate_id,
        "symbol": symbol,
        "broker_symbol": broker_symbol or symbol,
        "decision_time_utc": "2026-05-04T16:30:00+00:00",
        "created_at_utc": "2026-05-04T16:30:20+00:00",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def test_build_report_classifies_candidate_registry_rows(tmp_path):
    rows = [
        _candidate("nas", "NAS100", "NDX100"),
        _candidate("silver", "XAGUSD"),
        _candidate("cross", "GBPJPY"),
    ]
    _write_jsonl(tmp_path / "shadow_logs/strategy_follow_candidates.jsonl", rows)

    report = mod.build_report(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")
    by_id = {row["candidate_id"]: row for row in report["candidate_status_rows"]}

    assert report["status"] == "OK_WITH_BLOCKED_PROXY_ROWS"
    assert by_id["nas"]["proxy_class"] == VALIDATED_PROXY
    assert by_id["nas"]["depth_interpretation_allowed"] is True
    assert by_id["silver"]["proxy_class"] == SOURCE_DEFINITION_BLOCKED
    assert by_id["cross"]["proxy_class"] == NO_REGISTERED_PROXY
    assert by_id["cross"]["paid_data_calls"] == 0
    assert by_id["cross"]["paid_fetch_attempted"] is False
    assert report["missing_required_proxy_classes"] == []


def test_append_status_rows_is_idempotent(tmp_path):
    _write_jsonl(tmp_path / "shadow_logs/strategy_follow_candidates.jsonl", [_candidate("nas", "NAS100", "NDX100")])
    report = mod.build_report(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")
    target = tmp_path / "shadow_logs/sierra_proxy_registry_status.jsonl"

    assert mod.append_status_rows_if_missing(report["candidate_status_rows"], target) == 1
    assert mod.append_status_rows_if_missing(report["candidate_status_rows"], target) == 0
    assert len(target.read_text(encoding="utf-8").splitlines()) == 1


def test_no_candidates_is_documented(tmp_path):
    report = mod.build_report(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")

    assert report["status"] == "NO_CANDIDATE_ROWS"
    assert report["current_counts"]["candidate_rows"] == 0
