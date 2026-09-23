from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts import audit_xauusd_same_market_extension as script
from src.research_infra.xauusd_same_market_extension import (
    ACTION_REQUIRED,
    PROMOTION_VERDICT,
    STATUS_OK,
    build_report_payload,
    build_status_row,
    render_markdown,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _registry(**overrides) -> dict:
    row = {
        "schema_version": "xauusd_source_transfer_frozen_slice_registry_v1",
        "status": "RESEARCH_ARTIFACT_DONE",
        "promotion_verdict": PROMOTION_VERDICT,
        "live_trading_behavior_changed": False,
        "families": ["XAUUSD.scid same-market", "GC/MGC futures proxy"],
        "evidence_classes": ["SAME_MARKET_SOURCE_TRANSFER", "FUTURES_PROXY_TRANSFER"],
        "frozen_question": "Do registered XAUUSD slices transfer without same-slice tuning?",
        "target_resolved_rows_before_validation_discussion": 30,
        "holdout_policy": "Open no outcomes before slice fields are frozen.",
    }
    row.update(overrides)
    return row


def _source_map(**overrides) -> dict:
    row = {
        "schema_version": "forward_capture_source_map_v1",
        "status": "RESEARCH_ARTIFACT_DONE",
        "promotion_verdict": PROMOTION_VERDICT,
        "live_trading_behavior_changed": False,
        "opened_outcome_slices": [],
    }
    row.update(overrides)
    return row


def _inventory() -> dict:
    return {
        "schema_version": "sierra_forward_capture_inventory_v1",
        "status": "RESEARCH_ARTIFACT_DONE",
        "promotion_verdict": PROMOTION_VERDICT,
        "symbols": [
            {
                "symbol_root": "XAUUSD",
                "status": "CAUTION_SCID_PRESENT_DEPTH_MISSING",
                "scid_file_count": 1,
                "depth_file_count": 0,
                "latest_scid_utc": "2026-05-02T15:50:48+00:00",
                "latest_depth_utc": None,
            },
            {
                "symbol_root": "GC",
                "status": "READY_SCID_AND_DEPTH_PRESENT",
                "scid_file_count": 1,
                "depth_file_count": 2,
                "latest_scid_utc": "2026-05-04T19:06:28+00:00",
                "latest_depth_utc": "2026-05-04T19:06:29+00:00",
            },
            {
                "symbol_root": "MGC",
                "status": "READY_SCID_AND_DEPTH_PRESENT",
                "scid_file_count": 1,
                "depth_file_count": 2,
                "latest_scid_utc": "2026-05-04T19:06:28+00:00",
                "latest_depth_utc": "2026-05-04T19:06:29+00:00",
            },
        ],
    }


def _candidate() -> dict:
    return {
        "candidate_id": "XAUUSD_2026-05-04T13:15:00+00:00",
        "symbol": "XAUUSD",
        "created_at_utc": "2026-05-04T13:15:05+00:00",
        "decision_time_utc": "2026-05-04T13:15:00+00:00",
        "promotion_verdict": PROMOTION_VERDICT,
    }


def test_status_row_preregisters_source_status_without_opening_outcomes():
    row = build_status_row(
        registry=_registry(),
        source_map=_source_map(),
        sierra_inventory=_inventory(),
        candidate_rows=[_candidate()],
        evaluation_rows=[{**_candidate(), "candidate_id": "XAUUSD_2026-05-04T13:15:00+00:00_pre_ai"}],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["status"] == STATUS_OK
    assert row["promotion_verdict"] == PROMOTION_VERDICT
    assert row["opened_outcome_slices_at_registration"] == 0
    assert row["forward_snapshot"]["xauusd_live_candidate_rows"] == 1
    assert row["forward_snapshot"]["live_rows_are_not_replay_outcomes"] is True
    assert "XAUUSD_SAME_MARKET_DEPTH_MISSING_SCID_ONLY" in row["documented_limitation_codes"]
    assert row["order_calls"] == 0


def test_opened_outcomes_are_action_required():
    row = build_status_row(
        registry=_registry(),
        source_map=_source_map(opened_outcome_slices=[{"slice_id": "bad"}]),
        sierra_inventory=_inventory(),
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["status"] == ACTION_REQUIRED
    assert "OPENED_OUTCOMES_PRESENT_AT_REGISTRATION" in row["action_required_codes"]


def test_report_markdown_keeps_live_rows_separate_from_replay():
    payload = build_report_payload(
        registry=_registry(),
        source_map=_source_map(),
        sierra_inventory=_inventory(),
        candidate_rows=[_candidate()],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    rendered = render_markdown(payload)

    assert "Opened outcome slices at registration: `0`" in rendered
    assert "Live rows are not replay outcomes: `True`" in rendered
    assert "NO_PROMOTION_VERDICT" in rendered


def test_script_appends_status_row_idempotently(tmp_path, monkeypatch, capsys):
    registry = tmp_path / "registry.json"
    source_map = tmp_path / "source_map.json"
    inventory = tmp_path / "sierra.json"
    candidates = tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl"
    status_log = tmp_path / "shadow_logs" / "xauusd_same_market_extension_status.jsonl"
    output_json = tmp_path / "research" / "program_control" / "report.json"
    output_md = tmp_path / "research" / "program_control" / "report.md"
    _write_json(registry, _registry())
    _write_json(source_map, _source_map())
    _write_json(inventory, _inventory())
    _write_jsonl(candidates, [_candidate()])
    args = [
        "audit_xauusd_same_market_extension.py",
        "--registry",
        str(registry),
        "--source-map",
        str(source_map),
        "--sierra-inventory",
        str(inventory),
        "--candidates",
        str(candidates),
        "--status-log",
        str(status_log),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
    ]
    monkeypatch.setattr(sys, "argv", args)

    assert script.main() == 0
    first = json.loads(capsys.readouterr().out)
    assert first["rows_appended"] == 1

    monkeypatch.setattr(sys, "argv", args)
    assert script.main() == 0
    second = json.loads(capsys.readouterr().out)

    assert second["rows_appended"] == 0
    assert output_json.exists()
    assert output_md.exists()
    assert len(status_log.read_text(encoding="utf-8").splitlines()) == 1
