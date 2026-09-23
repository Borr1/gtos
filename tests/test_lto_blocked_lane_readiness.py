from __future__ import annotations

import json
from pathlib import Path

from scripts import audit_lto_blocked_lane_readiness as script
from src.research_infra import lto_blocked_lane_readiness as mod


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_lto024_static_scan_passes_when_live_imports_absent(tmp_path):
    _write(tmp_path / "src/components/orchestrator.py", "# no debate import\n")
    _write(tmp_path / "src/components/primary_analyzer.py", "# no tool import\n")
    _write(tmp_path / "run_agent.py", "# no debate import\n")
    _write(tmp_path / "src/components/debate.py", "# paused code exists\n")
    _write(tmp_path / "src/components/adaptive_review.py", "# not wired\n")
    (tmp_path / "src/components/ai_tools").mkdir(parents=True)
    _write(tmp_path / "tests/test_debate.py", "# tests exist\n")

    payload = mod.lto024_payload(tmp_path, "2026-05-05T00:00:00+00:00")

    assert payload["status"] == "APPROVAL_BLOCKED_DOSSIER_READY"
    assert payload["current_cost_usd"] == 0.0
    assert payload["action_required_codes"] == []
    assert payload["static_activation_check"]["activation_detected"] is False
    assert payload["ai_calls"] == 0
    assert payload["order_calls"] == 0


def test_lto024_static_scan_flags_live_debate_import(tmp_path):
    _write(tmp_path / "src/components/orchestrator.py", "from src.components.debate import BullBearDebate\n")
    _write(tmp_path / "src/components/primary_analyzer.py", "# no tool import\n")
    _write(tmp_path / "run_agent.py", "# no debate import\n")

    payload = mod.lto024_payload(tmp_path, "2026-05-05T00:00:00+00:00")

    assert payload["status"] == "ACTION_REQUIRED"
    assert payload["action_required_codes"] == ["LIVE_AI_OR_DEBATE_ACTIVATION_DETECTED"]
    assert payload["static_activation_check"]["findings"]["orchestrator_imports_debate"] is True


def test_lto031_and_lto032_source_readiness_explain_blockers(tmp_path):
    lto031 = mod.lto031_payload(tmp_path, "2026-05-05T00:00:00+00:00")
    lto032 = mod.lto032_payload(tmp_path, "2026-05-05T00:00:00+00:00")

    assert lto031["status"] == "SOURCE_BLOCKED_READINESS_REGISTERED"
    assert lto031["source_count"] == 7
    assert {row["source_key"] for row in lto031["sources"]} >= {
        "pre_2024_tick_lob",
        "fx_cot",
        "bis_macro",
    }
    assert all(row["promotion_verdict"] == mod.PROMOTION_VERDICT for row in [lto031, lto032])
    assert lto032["status"] == "PARTIAL_FORWARD_CONTEXT_WITH_SOURCE_BLOCKERS_REGISTERED"
    assert lto032["status_counts"]["READY_FORWARD_CONTEXT_ONLY"] == 1
    assert lto032["status_counts"]["BLOCKED"] == 2
    assert lto032["status_counts"]["BLOCKED_CONSTRUCTION_REQUIRED"] == 1


def test_status_rows_are_no_action_and_idempotent(tmp_path):
    payloads = mod.build_all_payloads(tmp_path, "2026-05-05T00:00:00+00:00")
    rows = payloads["status_rows"]

    assert [row["lto_id"] for row in rows] == ["LTO-024", "LTO-031", "LTO-032"]
    assert all(row["schema_version"] == mod.STATUS_SCHEMA_VERSION for row in rows)
    assert all(row["promotion_verdict"] == mod.PROMOTION_VERDICT for row in rows)
    assert all(row["ai_calls"] == 0 and row["paid_data_calls"] == 0 for row in rows)

    log_path = tmp_path / "shadow_logs/lto_blocked_lane_status.jsonl"
    assert script.append_missing_rows(log_path, rows) == 3
    assert script.append_missing_rows(log_path, rows) == 0
    written = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(written) == 3
