import gzip
import json
from pathlib import Path

from scripts.audit_goal_route_artifacts import audit_route


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_audit_goal_route_artifacts_detects_required_files_and_jsonl(tmp_path: Path) -> None:
    route = tmp_path / "route"
    _write(route / "ROUTE_COMPLETION_AUDIT_2026-05-15.json", json.dumps({"ok": True}))
    _write(
        route / "ROUTE_DECISION_LEDGER_2026-05-15.json",
        json.dumps(
            {
                "terminal_decision": "ACCEPT",
                "result_boundary": "RESEARCH_RESULT_BOUNDARY",
                "source_use_state": "BLOCKED_UNTIL_SOURCE_CONTRACT_PASSES",
                "outcome_window_state": "FROZEN_NOT_OPENED",
                "runtime_effect_boundary": "NO_LIVE_RUNTIME_EFFECT",
            }
        ),
    )
    _write(route / "ROUTE_VERIFICATION_RESULT_2026-05-15.json", json.dumps({"ok": True}))
    _write(route / "ROUTE_OUTPUT_MANIFEST_2026-05-15.json", json.dumps({"artifacts": []}))
    _write(route / "verify_route_2026_05_15.py", "def verify(): return True\n")
    _write(route / "test_route_2026_05_15.py", "def test_ok(): assert True\n")
    _write(
        route / "ROWS_2026-05-15.jsonl",
        json.dumps({"row_id": "1", "status": "PASS", "role": "pass"}) + "\n",
    )

    result = audit_route(route, max_jsonl_rows=None)

    assert result["ok"] is True
    assert result["missing_required"] == []
    assert result["json_parse_error_count"] == 0
    assert result["jsonl_count"] == 1
    assert result["jsonl_scans"][0]["rows_scanned"] == 1
    assert ("status=PASS", 1) in result["jsonl_scans"][0]["top_statuses"]


def test_full_jsonl_respects_byte_cap_unless_giant_scan_is_explicit(
    tmp_path: Path,
) -> None:
    route = tmp_path / "route"
    _write(route / "ROUTE_COMPLETION_AUDIT_2026-05-15.json", json.dumps({"ok": True}))
    _write(
        route / "ROUTE_DECISION_LEDGER_2026-05-15.json",
        json.dumps(
            {
                "terminal_decision": "ACCEPT",
                "result_boundary": "RESEARCH_RESULT_BOUNDARY",
                "source_use_state": "BLOCKED_UNTIL_SOURCE_CONTRACT_PASSES",
                "outcome_window_state": "FROZEN_NOT_OPENED",
                "runtime_effect_boundary": "NO_LIVE_RUNTIME_EFFECT",
            }
        ),
    )
    _write(route / "ROUTE_VERIFICATION_RESULT_2026-05-15.json", json.dumps({"ok": True}))
    _write(route / "ROUTE_OUTPUT_MANIFEST_2026-05-15.json", json.dumps({"artifacts": []}))
    _write(route / "verify_route_2026_05_15.py", "def verify(): return True\n")
    _write(route / "test_route_2026_05_15.py", "def test_ok(): assert True\n")
    _write(
        route / "BIG_ROWS_2026-05-15.jsonl",
        json.dumps({"row_id": "1", "status": "PASS", "payload": "x" * 64}) + "\n",
    )

    capped = audit_route(route, max_jsonl_rows=None, max_jsonl_file_bytes=10)

    assert capped["ok"] is False
    assert capped["jsonl_files_scanned"] == 0
    assert capped["jsonl_files_skipped_large_count"] == 1
    assert capped["jsonl_files_unscanned"] == 1
    assert capped["jsonl_full_scan_incomplete"] is True

    explicit = audit_route(
        route,
        max_jsonl_rows=None,
        max_jsonl_file_bytes=10,
        allow_giant_jsonl=True,
    )

    assert explicit["ok"] is True
    assert explicit["jsonl_files_scanned"] == 1
    assert explicit["jsonl_files_skipped_large_count"] == 0
    assert explicit["jsonl_full_scan_incomplete"] is False
    assert explicit["jsonl_scans"][0]["rows_scanned"] == 1


def test_full_giant_scan_streams_large_retired_label_text(tmp_path: Path) -> None:
    route = tmp_path / "route"
    _write(route / "ROUTE_COMPLETION_AUDIT_2026-05-15.json", json.dumps({"ok": True}))
    _write(route / "ROUTE_DECISION_LEDGER_2026-05-15.json", json.dumps({"decision": "ACCEPT"}))
    _write(route / "ROUTE_VERIFICATION_RESULT_2026-05-15.json", json.dumps({"ok": True}))
    _write(route / "ROUTE_OUTPUT_MANIFEST_2026-05-15.json", json.dumps({"artifacts": []}))
    _write(route / "verify_route_2026_05_15.py", "def verify(): return True\n")
    _write(route / "test_route_2026_05_15.py", "def test_ok(): assert True\n")
    _write(route / "ROWS_2026-05-15.jsonl", json.dumps({"row_id": "1"}) + "\n")
    _write(route / "LARGE_RETIRED_LABEL_SCAN.py", ("x" * 1_000_001) + "\n")

    capped = audit_route(route, max_jsonl_rows=None)

    assert capped["retired_label_status"]["skipped_large_file_count"] == 1

    explicit = audit_route(route, max_jsonl_rows=None, allow_giant_jsonl=True)

    assert explicit["ok"] is True
    assert explicit["retired_label_status"]["skipped_large_file_count"] == 0
    assert explicit["retired_label_status"]["scanned_bytes"] >= 1_000_001


def test_audit_goal_route_artifacts_rejects_zero_byte_json(tmp_path: Path) -> None:
    route = tmp_path / "route"
    _write(route / "ROUTE_COMPLETION_AUDIT_2026-05-15.json", json.dumps({"ok": True}))
    _write(
        route / "ROUTE_DECISION_LEDGER_2026-05-15.json",
        json.dumps(
            {
                "terminal_decision": "ACCEPT",
                "result_boundary": "RESEARCH_RESULT_BOUNDARY",
                "source_use_state": "BLOCKED_UNTIL_SOURCE_CONTRACT_PASSES",
                "outcome_window_state": "FROZEN_NOT_OPENED",
                "runtime_effect_boundary": "NO_LIVE_RUNTIME_EFFECT",
            }
        ),
    )
    _write(route / "ROUTE_VERIFICATION_RESULT_2026-05-15.json", json.dumps({"ok": True}))
    _write(route / "ROUTE_OUTPUT_MANIFEST_2026-05-15.json", json.dumps({"artifacts": []}))
    _write(route / "verify_route_2026_05_15.py", "def verify(): return True\n")
    _write(route / "test_route_2026_05_15.py", "def test_ok(): assert True\n")
    (route / "ZERO_SUMMARY.json").write_text("", encoding="utf-8")

    result = audit_route(route, max_jsonl_rows=10)

    assert result["ok"] is False
    assert result["json_zero_byte_error_count"] == 1
    assert result["json_zero_byte_errors"][0]["path"] == "ZERO_SUMMARY.json"


def test_audit_goal_route_artifacts_reads_gzip_payload_with_jsonl_suffix(tmp_path: Path) -> None:
    route = tmp_path / "route"
    _write(route / "ROUTE_COMPLETION_AUDIT_2026-05-15.json", json.dumps({"ok": True}))
    _write(route / "ROUTE_DECISION_LEDGER_2026-05-15.json", json.dumps({"decision": "ACCEPT"}))
    _write(route / "ROUTE_VERIFICATION_RESULT_2026-05-15.json", json.dumps({"ok": True}))
    _write(route / "ROUTE_OUTPUT_MANIFEST_2026-05-15.json", json.dumps({"artifacts": []}))
    _write(route / "verify_route_2026_05_15.py", "def verify(): return True\n")
    _write(route / "test_route_2026_05_15.py", "def test_ok(): assert True\n")
    with gzip.open(route / "COMPRESSED_ROWS_2026-05-15.jsonl", "wt", encoding="utf-8") as handle:
        handle.write(json.dumps({"row_id": "gz-1", "status": "PASS"}) + "\n")

    result = audit_route(route, max_jsonl_rows=None)

    assert result["ok"] is True
    assert result["jsonl_parse_error_count"] == 0
    assert result["jsonl_scans"][0]["rows_scanned"] == 1
    assert ("status=PASS", 1) in result["jsonl_scans"][0]["top_statuses"]


def test_audit_goal_route_artifacts_reports_missing_required_files(tmp_path: Path) -> None:
    route = tmp_path / "route"
    route.mkdir()
    _write(route / "ONLY_NOTE.md", "no verifier here")

    result = audit_route(route, max_jsonl_rows=10)

    assert result["ok"] is False
    assert "completion_audit" in result["missing_required"]
    assert "verification_result" in result["missing_required"]


def test_audit_goal_route_artifacts_rejects_parse_errors_and_cache_false_positives(
    tmp_path: Path,
) -> None:
    route = tmp_path / "route"
    _write(
        route / "ROUTE_COMPLETION_AUDIT_2026-05-15.json",
        json.dumps({"ok": True}),
    )
    _write(
        route / "ROUTE_DECISION_LEDGER_2026-05-15.json",
        json.dumps(
            {
                "terminal_decision": "ACCEPT",
                "result_boundary": "RESEARCH_RESULT_BOUNDARY",
                "source_use_state": "BLOCKED_UNTIL_SOURCE_CONTRACT_PASSES",
                "outcome_window_state": "FROZEN_NOT_OPENED",
                "runtime_effect_boundary": "NO_LIVE_RUNTIME_EFFECT",
            }
        ),
    )
    _write(route / "ROUTE_VERIFICATION_RESULT_2026-05-15.json", json.dumps({"ok": True}))
    _write(route / "ROUTE_OUTPUT_MANIFEST_2026-05-15.json", json.dumps({"artifacts": []}))
    _write(route / "__pycache__" / "verify_fake.py", "def verify(): return True\n")
    _write(route / "test_route_2026_05_15.py", "def test_ok(): assert True\n")
    _write(route / "bad.json", "{")
    _write(route / "bad_rows.jsonl", "{bad\n")

    result = audit_route(route, max_jsonl_rows=None)

    assert result["ok"] is False
    assert "verifier_script" in result["missing_required"]
    assert result["json_parse_error_count"] == 1
    assert result["jsonl_parse_error_count"] == 1


def test_launch_pack_profile_accepts_starters_without_builder_artifacts(tmp_path: Path) -> None:
    route = tmp_path / "launch"
    _write(
        route / "LAUNCH_COMPLETION_AUDIT_2026-05-15.json",
        json.dumps(
            {
                "result_boundary": "RESEARCH_RESULT_BOUNDARY",
                "source_use_state": "BLOCKED_UNTIL_SOURCE_CONTRACT_PASSES",
                "outcome_window_state": "FROZEN_NOT_OPENED",
                "runtime_effect_boundary": "NO_LIVE_RUNTIME_EFFECT",
            }
        ),
    )
    _write(route / "LAUNCH_DECISION_LEDGER_2026-05-15.json", json.dumps({"decision": "OPEN"}))
    _write(route / "ROUTE_STARTER_2026-05-15.txt", "starter")

    result = audit_route(route, max_jsonl_rows=None, profile="launch-pack")

    assert result["ok"] is True
    assert result["missing_required"] == []
