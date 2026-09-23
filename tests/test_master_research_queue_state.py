from __future__ import annotations

import json

from scripts import build_master_research_queue_state as mod


def test_parse_backlog_mechanically_reads_status_rows(tmp_path):
    backlog = tmp_path / "MASTER_BACKLOG.md"
    backlog.write_text(
        "\n".join(
            [
                "## Section M -- METHODOLOGY corrections",
                "",
                "| ID | Tier | Status | Item |",
                "|---|---|---|---|",
                "| M-7 | T1 | PENDING | Replace Stouffer with weighted SE. |",
                "| M-8 | T1 | DONE | Null shuffles. |",
            ]
        ),
        encoding="utf-8",
    )

    rows = mod.parse_backlog(backlog)

    assert [row["id"] for row in rows] == ["M-7", "M-8"]
    assert rows[0]["section"].startswith("M")
    assert rows[0]["backlog_status"] == "PENDING"


def test_artifact_overlay_marks_d11_done_and_opens_followups(tmp_path):
    backlog = tmp_path / "MASTER_BACKLOG.md"
    backlog.write_text(
        "\n".join(
            [
                "## Section D -- DATA extraction needs",
                "",
                "| ID | Tier | Status | Item |",
                "|---|---|---|---|",
                "| D-11 | T1 | PENDING | 2022-2023 backfill data quality bias check. |",
            ]
        ),
        encoding="utf-8",
    )

    queue = mod.build_queue(backlog)
    d11 = next(row for row in queue if row["id"] == "D-11")

    assert d11["status"] == "DONE"
    assert d11["latest_artifact_path"].endswith("D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.md")
    assert "D11-REGENERATE-GBPJPY-US30CASH-OLD-LABELS" in d11["new_followups_opened"]


def test_build_payload_preserves_no_promotion_and_counts_generated_items(tmp_path):
    backlog = tmp_path / "MASTER_BACKLOG.md"
    backlog.write_text(
        "\n".join(
            [
                "## Section M -- METHODOLOGY corrections",
                "",
                "| ID | Tier | Status | Item |",
                "|---|---|---|---|",
                "| M-7 | T1 | PENDING | Replace Stouffer with weighted SE. |",
            ]
        ),
        encoding="utf-8",
    )

    payload = mod.build_payload(backlog_path=backlog)

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["summary"]["master_backlog_items"] == 1
    assert payload["summary"]["generated_followup_items"] >= 1
    assert payload["summary"]["promotion_allowed_items"] == []

    json.dumps(payload)
