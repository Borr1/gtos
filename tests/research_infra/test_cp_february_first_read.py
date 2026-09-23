"""Behavioral tests for Session CP's pre-outcome February evaluator."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
TOOL = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase18/receipts"
    / "cp_february_first_read.py"
)
PROTOCOL = TOOL.with_name("CP_FEBRUARY_FIRST_READ_PROTOCOL_V1.json")
SPEC = importlib.util.spec_from_file_location("cp_february_first_read", TOOL)
assert SPEC and SPEC.loader
CP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CP)


def _protocol() -> dict:
    return json.loads(PROTOCOL.read_text())


def _lane_receipt(*, physical: float = 1.0, trades: int = 40) -> dict:
    return {
        "evidence_class": CP.EXPECTED_EVIDENCE,
        "spec": {"arm": "S0R0", "lane_window_id": "february_2026"},
        "partition_authorization": {
            "window": ["2026-02-01", "2026-02-28"],
            "dominant_surface": "VAL",
            "may_emit_iteration_evidence": True,
            "disclosures": ["VAL is used once by survivor selection"],
        },
        "counts": {"trade": trades},
        "summary_economics": {
            "split_profile_stats[0].physical_net_r": physical,
        },
    }


def _pool(
    *,
    gross: float,
    net: float,
    positive_days: int,
    negative_days: int,
    base_rate: float,
    breakeven: float,
    rows: int = 20000,
) -> dict:
    days = {
        f"2026-02-{index + 1:02d}": {"mean_net_r": 1.0}
        for index in range(positive_days)
    }
    days.update({
        f"2026-02-{positive_days + index + 1:02d}": {"mean_net_r": -1.0}
        for index in range(negative_days)
    })
    return {
        "source": "regenerated_ledger",
        "row_limit_applied": None,
        "diagnostic_scoreable_rows": rows,
        "unreadable_proxy_rows": 0,
        "gross": {"mean_gross_r": gross},
        "mean_r_per_row": net,
        "base_rate_positive": base_rate,
        "breakeven_precision": breakeven,
        "by_day": days,
    }


def test_positive_on_every_committed_surface_is_the_only_s1r1_authorization() -> None:
    result = CP.evaluate(
        _protocol(),
        _pool(
            gross=0.02,
            net=0.01,
            positive_days=12,
            negative_days=8,
            base_rate=0.55,
            breakeven=0.50,
        ),
        _lane_receipt(physical=0.01),
    )
    assert result["disposition"] == "PROMOTE_TO_S1R1_PROBE"
    assert result["s1r1_authorized_by_protocol"] is True
    assert result["admission_or_graduation_claim"] is False


def test_materially_negative_broad_surface_stops_the_second_arm() -> None:
    result = CP.evaluate(
        _protocol(),
        _pool(
            gross=-0.10,
            net=-0.40,
            positive_days=4,
            negative_days=16,
            base_rate=0.30,
            breakeven=0.60,
        ),
        _lane_receipt(physical=0.0),
    )
    assert result["disposition"] == "REJECT_S1R1_AS_NOT_JUSTIFIED"
    assert result["s1r1_authorized_by_protocol"] is False


def test_mixed_signs_are_inconclusive_not_posthoc_resolved() -> None:
    result = CP.evaluate(
        _protocol(),
        _pool(
            gross=0.01,
            net=-0.01,
            positive_days=11,
            negative_days=9,
            base_rate=0.49,
            breakeven=0.50,
        ),
        _lane_receipt(physical=1.0),
    )
    assert result["disposition"] == "INCONCLUSIVE_HOLD_S1R1"
    assert result["s1r1_authorized_by_protocol"] is False


def test_a_thin_window_cannot_reach_either_directional_verdict() -> None:
    result = CP.evaluate(
        _protocol(),
        _pool(
            gross=1.0,
            net=1.0,
            positive_days=10,
            negative_days=0,
            base_rate=0.80,
            breakeven=0.20,
            rows=100,
        ),
        _lane_receipt(physical=10.0, trades=2),
    )
    assert result["disposition"] == "INCONCLUSIVE_INSUFFICIENT_DENOMINATOR"


def test_a_non_february_receipt_refuses_before_metrics_are_interpreted() -> None:
    receipt = _lane_receipt()
    receipt["spec"]["lane_window_id"] = "january_2026"
    with pytest.raises(CP.FirstReadRefusal, match="not_february"):
        CP.evaluate(
            _protocol(),
            _pool(
                gross=1.0,
                net=1.0,
                positive_days=20,
                negative_days=0,
                base_rate=0.80,
                breakeven=0.20,
            ),
            receipt,
        )
