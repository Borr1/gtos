from __future__ import annotations

import json

from scripts import build_limitations_to_opportunities_queue_state as mod


def test_lto_sections_and_followup_map_cover_active_plan():
    sections = mod.parse_lto_sections()
    follow_to_lto, lto_to_follow = mod.parse_followup_mapping()

    assert len(sections) == 40
    assert sections["LTO-040"]["title"] == "Research Queue / Master Backlog Integration"
    assert follow_to_lto["LIVE-FOLLOW-032"] == ["LTO-034", "LTO-040"]
    assert "LIVE-FOLLOW-001" in lto_to_follow["LTO-039"]
    assert "Implementation Order" not in sections["LTO-040"]["validation"]


def test_queue_payload_maps_every_live_follow_row_and_preserves_no_promotion():
    payload = mod.build_payload()

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["summary"]["lto_item_count"] == 40
    assert payload["summary"]["live_follow_row_count"] == 34
    assert payload["summary"]["unmapped_live_follow_ids"] == []
    assert payload["summary"]["mapped_lto_ids_without_plan_section"] == []
    assert payload["summary"]["promotion_allowed_items"] == []

    by_id = {item["id"]: item for item in payload["items"]}
    assert by_id["LTO-040"]["status"] == "DONE"
    assert by_id["LTO-034"]["status"] == "DONE"
    assert by_id["LTO-039"]["status"] == "DONE"
    assert by_id["LTO-006"]["status"] == "DONE"
    assert by_id["LTO-007"]["status"] == "DONE"
    assert by_id["LTO-008"]["status"] == "DONE"
    assert by_id["LTO-009"]["status"] == "DONE"
    assert by_id["LTO-015"]["status"] == "DONE"
    assert by_id["LTO-016"]["status"] == "DONE"
    assert by_id["LTO-017"]["status"] == "DONE"
    assert by_id["LTO-018"]["status"] == "DONE"
    assert by_id["LTO-019"]["status"] == "DONE"
    assert by_id["LTO-020"]["status"] == "DONE"
    assert by_id["LTO-025"]["status"] == "DONE"
    assert by_id["LTO-026"]["status"] == "DONE"
    assert by_id["LTO-011"]["status"] == "DONE"
    assert by_id["LTO-012"]["status"] == "DONE"
    assert by_id["LTO-013"]["status"] == "DONE"
    assert by_id["LTO-014"]["status"] == "DONE"
    assert by_id["LTO-030"]["status"] == "DONE"
    assert by_id["LTO-033"]["status"] == "DONE"
    assert by_id["LTO-021"]["status"] == "DONE"
    assert by_id["LTO-022"]["status"] == "DONE"
    assert by_id["LTO-036"]["status"] == "DONE"
    assert by_id["LTO-037"]["status"] == "DONE"
    assert by_id["LTO-038"]["status"] == "DONE"
    assert by_id["LTO-023"]["status"] == "DONE"
    assert "Owner-approved read-only ML shadow path" in by_id["LTO-023"]["blocked_by"]
    assert by_id["LTO-027"]["status"] == "DONE"
    assert "MT5 account history is used for filled broker outcomes" in by_id["LTO-027"]["blocked_by"]
    assert by_id["LTO-028"]["status"] == "DONE"
    assert "outcomes closed at registration" in by_id["LTO-028"]["blocked_by"]
    assert by_id["LTO-029"]["status"] == "DONE"
    assert "no-lookahead rules" in by_id["LTO-029"]["blocked_by"]
    assert by_id["LTO-035"]["status"] == "DONE"
    assert "No-AI/no-execution observer hardening is implemented" in by_id["LTO-035"]["blocked_by"]
    assert by_id["LTO-024"]["status"] == "APPROVAL_BLOCKED"
    assert any("LTO024_COMPONENT3B" in path for path in by_id["LTO-024"]["blocker_artifact_paths"])
    assert by_id["LTO-031"]["status"] == "SOURCE_BLOCKED"
    assert any("LTO031_EXTERNAL_FEED" in path for path in by_id["LTO-031"]["blocker_artifact_paths"])
    assert by_id["LTO-032"]["status"] == "SOURCE_BLOCKED"
    assert any("LTO032_OPTIONS_GAMMA" in path for path in by_id["LTO-032"]["blocker_artifact_paths"])
    assert by_id["LTO-010"]["status"] == "DONE"
    assert "no longer owner-approval-blocked" in by_id["LTO-010"]["blocked_by"]
    assert by_id["LTO-001"]["follow_ids"] == ["LIVE-FOLLOW-001"]
    assert all(item["implementation_order"] is not None for item in payload["items"])
    assert by_id["LTO-009"]["implementation_order"] < by_id["LTO-015"]["implementation_order"]

    json.dumps(payload)


def test_render_markdown_reports_zero_unmapped_rows():
    payload = mod.build_payload()
    rendered = mod.render_markdown(payload)

    assert "Unmapped LIVE-FOLLOW rows: `none`" in rendered
    assert "| `LTO-040` Research Queue / Master Backlog Integration | `DONE` |" in rendered
    assert "`NO_PROMOTION_VERDICT`" in rendered
