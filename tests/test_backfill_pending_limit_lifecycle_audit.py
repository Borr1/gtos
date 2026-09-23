from __future__ import annotations

from scripts.backfill_pending_limit_lifecycle_audit import build_report, read_jsonl_with_lines


def test_read_jsonl_with_lines_reports_bad_rows_and_continues(tmp_path):
    path = tmp_path / "source.jsonl"
    path.write_text('{"ok":1}\nnot-json\n{"ok":2}\n', encoding="utf-8")

    issues = []
    rows = read_jsonl_with_lines(path, issues)

    assert rows == [(1, {"ok": 1}), (3, {"ok": 2})]
    assert len(issues) == 1
    assert issues[0]["line_no"] == 2
    assert issues[0]["path"] == str(path)
    assert issues[0]["snippet"] == "not-json"


def test_build_report_marks_source_jsonl_issues_action_required(tmp_path):
    report = build_report(
        [],
        [],
        tmp_path / "pending_limit_lifecycle_audit.jsonl",
        audit_rows_available=0,
        source_jsonl_issues=[
            {
                "path": "shadow_logs/pending_limit_lifecycle.jsonl",
                "line_no": 367,
                "error": "Expecting value",
                "snippet": 'ort": false}',
            }
        ],
    )

    assert report["status"] == "ACTION_REQUIRED"
    assert report["counts"]["source_jsonl_issue_count"] == 1
    assert report["source_jsonl_issues"][0]["line_no"] == 367
