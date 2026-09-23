from __future__ import annotations

from pathlib import Path

import build_vnext_absolute_moonshot_post_lane18_source_capture_repair as builder


def test_classify_market_bar_gap_from_local_source(tmp_path, monkeypatch):
    csv_path = tmp_path / "data" / "historical_2022_2023" / "XAGUSD_H4.csv"
    csv_path.parent.mkdir(parents=True)
    csv_path.write_text(
        "time,open,high,low,close,volume\n"
        "2022-01-03T00:00:00Z,1,2,0,1,10\n"
        "2022-01-04T00:00:00Z,1,2,0,1,10\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(builder, "REPO_ROOT", tmp_path)
    index = builder.build_source_index()
    row = {
        "symbol": "XAGUSD",
        "date": "2022-01-03",
        "field_family": "h4_coverage_or_structure",
        "source_path": "data/historical_2026/XAGUSD_H4.csv",
    }

    disposition = builder.classify_field(row, "h4_coverage_or_structure", index)

    assert disposition["disposition"] == "filled_now"
    assert disposition["repair_source_paths"] == ["data/historical_2022_2023/XAGUSD_H4.csv"]
    assert disposition["no_leak_status"] == "decision_asof_market_bar_source_only"


def test_classify_historical_intent_as_non_generatable():
    index = builder.SourceIndex()
    row = {
        "symbol": "XAUUSD",
        "date": "2022-01-03",
        "field_family": "historical_broker_intent_or_order_truth",
    }

    disposition = builder.classify_field(row, "historical_broker_intent_or_order_truth", index)

    assert disposition["disposition"] == "non_generatable_historical_truth"
    assert "cannot be generated from price movement" in disposition["classification_reason"]


def test_field_families_uses_gap_reason_code_without_unspecified_fallback():
    row = {
        "gap_reason_code": "NO_JOINED_LABEL_SOURCE_CURRENT_INPUTS",
        "repair_requirement_code": "RUN_OR_JOIN_MICROSCOPE_REPLAY_OR_READONLY_BROKER_LIFECYCLE_COST_SOURCE",
    }

    families = builder.field_families(row)

    assert "NO_JOINED_LABEL_SOURCE_CURRENT_INPUTS" in families
    assert "RUN_OR_JOIN_MICROSCOPE_REPLAY_OR_READONLY_BROKER_LIFECYCLE_COST_SOURCE" in families
    assert "unspecified_source_gap" not in families


def test_classify_realized_r_as_proxy_bound_when_cost_calibration_exists():
    index = builder.SourceIndex(cost_symbols={"XAUUSD"})
    row = {
        "symbol": "XAUUSD",
        "date": "2026-03-06",
        "field_family": "net_r",
    }

    disposition = builder.classify_field(row, "net_r", index)

    assert disposition["disposition"] == "proxy_bound_now"
    assert disposition["source_class"] == "source_bound_proxy_r_or_cost_calibration"


def test_downstream_contract_mapping_for_policy_tick_gap():
    consumers = builder.downstream_for_family("ordered_bid_ask_tick_timeline")

    assert "Execution Policy V3" in consumers
    assert "Digital Twin V2" in consumers
    assert "Production Change Dossier" in consumers
