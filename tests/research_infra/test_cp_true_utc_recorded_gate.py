from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
TOOL_PATH = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase18/receipts"
    / "cp_true_utc_recorded_gate.py"
)
SPEC = importlib.util.spec_from_file_location("cp_true_utc_recorded_gate", TOOL_PATH)
assert SPEC and SPEC.loader
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


def _base_row() -> dict:
    return {
        "decision_time_utc": "2026-01-21T13:00:00+00:00",
        "route_session": "ny",
        "symbol": "XAUUSD",
        "side": "LONG",
        "counterfactual_order_fill_status": "filled",
        "counterfactual_order_fill_time_utc": "2026-01-21T13:01:00+00:00",
        "counterfactual_order_close_time_utc": "2026-01-21T16:00:00+00:00",
        "counterfactual_order_fill_price": 4400.0,
        "stop_loss": 4390.0,
        "opportunity_gross_r": 1.25,
        "opportunity_close_reason": "target",
        "terminal_outcome": "target_reached",
        "opportunity_path_scored": True,
        "path_index_source_sha256": "a" * 64,
        "candidate_id": "candidate",
    }


def test_source_preflight_constructs_only_exact_trade_records() -> None:
    records, report = tool.source_preflight([_base_row()])
    assert report["full_population_exact"] is True
    assert report["valid_trade_records"] == 1
    assert len(records) == 1
    assert records[0].holding_hours == 2 + 59 / 60
    assert records[0].r_gross == 1.25


def test_source_preflight_refuses_decision_time_and_net_proxy_substitution() -> None:
    row = _base_row()
    row.pop("counterfactual_order_fill_time_utc")
    row.pop("opportunity_gross_r")
    row["opportunity_net_proxy_r"] = 1.0
    records, report = tool.source_preflight([row])
    assert records == []
    assert report["full_population_exact"] is False
    assert report["filled_incomplete_rows"] == 1
    assert report["missing_field_counts"]["counterfactual_order_fill_time_utc"] == 1
    assert report["missing_field_counts"]["opportunity_gross_r"] == 1
    assert report["substitution_policy"]["net_proxy_as_gross_r"] == "FORBIDDEN"


def test_explicit_no_fill_is_not_a_trade_and_is_not_missing_evidence() -> None:
    row = _base_row()
    row["counterfactual_order_fill_status"] = "not_filled_no_trade"
    for field in tool.FILLED_TRADE_FIELDS:
        row.pop(field, None)
    records, report = tool.source_preflight([row])
    assert records == []
    assert report["full_population_exact"] is True
    assert report["explicit_no_trade_rows"] == 1
    assert report["fill_classification_missing_rows"] == 0


def test_missing_fill_classification_fails_the_whole_population_closed() -> None:
    exact = _base_row()
    unknown = _base_row()
    unknown.pop("counterfactual_order_fill_status")
    records, report = tool.source_preflight([exact, unknown])
    assert records == []
    assert report["full_population_exact"] is False
    assert report["valid_trade_records"] == 1
    assert report["fill_classification_missing_rows"] == 1
