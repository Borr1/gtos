from __future__ import annotations

import json

from scripts import audit_limitations_to_opportunities_completion as mod


def test_completion_audit_current_repo_can_mark_complete():
    payload = mod.build_payload(root=mod.ROOT)

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["completion_status"] == "ACHIEVED_WITH_DOCUMENTED_EXTERNAL_BLOCKERS"
    assert payload["can_mark_goal_complete"] is True
    assert payload["queue_status_counts"] == {
        "APPROVAL_BLOCKED": 1,
        "DONE": 37,
        "SOURCE_BLOCKED": 2,
    }
    assert not [check for check in payload["checks"] if check["status"] != "PASS"]
    assert {row["lto_id"] for row in payload["artifact_rows"]} >= {"LTO-024", "LTO-031", "LTO-032"}


def test_completion_audit_markdown_reports_external_blockers():
    payload = mod.build_payload(root=mod.ROOT)
    rendered = mod.render_markdown(payload)

    assert "`LTO-024`: approval-blocked" in rendered
    assert "`LTO-031`: source-blocked" in rendered
    assert "`LTO-032`: source-blocked/partial" in rendered
    assert "`ACHIEVED_WITH_DOCUMENTED_EXTERNAL_BLOCKERS`" in rendered
    json.dumps(payload)
