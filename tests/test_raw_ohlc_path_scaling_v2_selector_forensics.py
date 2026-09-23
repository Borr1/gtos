from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts import analyze_raw_ohlc_path_scaling_v2_selector_forensics as mod


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"v2_selector_forensics_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _event(event_key: str, variant: str, net_r: float, *, cohort: str, role: str) -> dict:
    return {
        "event_key": event_key,
        "candle_close_utc": "2026-01-01T13:00:00+00:00",
        "variant_id": variant,
        "symbol": cohort.split("|")[0],
        "session": cohort.split("|")[1],
        "selected_timeframe": "M1",
        "mechanical_side": "LONG",
        "raw_cohort_key": cohort,
        "role": role,
        "net_r_by_cost": {"0.05": net_r},
    }


def _write(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def test_forensics_recommends_ob_when_fvg_headline_is_less_clean(tmp_path):
    event_log = tmp_path / "events.jsonl"
    rows = []
    cases = [
        ("target", "USDJPY|tokyo|bearish|D1", "primary_controlled_child", 0.0, -0.5, 0.2),
        ("blocked", "NAS100|ny|bullish|D1", "dominance_watchlist", 0.0, 1.0, 0.1),
        ("negative", "GBPUSD|london|bearish|H4", "negative_control", 0.0, 0.2, 0.1),
    ]
    for key, cohort, role, baseline_r, fvg_r, ob_r in cases:
        rows.append(_event(key, mod.BASELINE_VARIANT, baseline_r, cohort=cohort, role=role))
        rows.append(_event(key, "STRUCT_FVG_MID_EDGE_V2", fvg_r, cohort=cohort, role=role))
        rows.append(_event(key, "STRUCT_OB_BOUNDARY_V2", ob_r, cohort=cohort, role=role))
        rows.append(_event(key, "STRUCT_SWING_PROTECTED_V2", ob_r, cohort=cohort, role=role))
        rows.append(_event(key, "STRUCT_COMPOSITE_ANY_V2", ob_r, cohort=cohort, role=role))
    _write(event_log, rows)

    payload = mod.build_payload(event_log_path=event_log)
    fvg = payload["variants"]["STRUCT_FVG_MID_EDGE_V2"]
    ob = payload["variants"]["STRUCT_OB_BOUNDARY_V2"]

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["decision_readout"]["recommended_v2b_candidate"] == "STRUCT_OB_BOUNDARY_V2"
    assert fvg["pairwise_vs_j46"]["mean_delta_candidate_minus_baseline"] > ob["pairwise_vs_j46"]["mean_delta_candidate_minus_baseline"]
    assert fvg["cleanliness"]["all_major_groups_nonnegative"] is False
    assert ob["cleanliness"]["all_major_groups_nonnegative"] is True
