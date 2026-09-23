from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"


def test_stage05_registry_is_non_boxed_and_default_off() -> None:
    rows = [
        json.loads(line)
        for line in (ROUTE_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_{DATE_ID}.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    names = {row["name"] for row in rows}
    assert {"ob_retest", "fvg_fill", "breaker_re_entry"} <= names
    assert "orderflow_depth_imbalance_proxy" in names
    assert "cross_asset_lead_lag" in names
    assert "path_hazard_early_failure" in names
    assert all(row["default_off"] is True for row in rows)


def test_stage05_summary_advances_to_market_awareness() -> None:
    summary = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_SUMMARY_{DATE_ID}.json").read_text(
            encoding="utf-8"
        )
    )
    state = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json").read_text(encoding="utf-8")
    )
    assert summary["current_framework_candidate_rows"] == 253234
    assert summary["non_current_origin_family_rows"] > 10
    assert summary["first_incomplete_invariant_after_stage05"] == "STAGE_06_MARKET_AWARENESS_ENRICHMENT"
    assert state["first_incomplete_invariant"] == "STAGE_06_MARKET_AWARENESS_ENRICHMENT"
