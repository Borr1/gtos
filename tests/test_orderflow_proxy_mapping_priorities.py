from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts.audit_orderflow_proxy_mapping_priorities import (
    PROXY_CANDIDATES,
    build_payload,
    summarize_symbol_rows,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"orderflow_proxy_mapping_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _row(symbol: str, decision: str = "NO_TRADE", direction: str | None = None) -> dict:
    trade_parameters = {"direction": direction} if direction else None
    return {
        "timestamp_utc": "2026-04-17T00:15:00+00:00",
        "symbol": symbol,
        "decision": decision,
        "trade_parameters": trade_parameters,
        "session_tag": "tokyo",
        "m15_choch_detected": decision == "CANDIDATE",
        "mso_h1_unmitigated_ob_count": 1,
        "mso_h1_fvg_count": 0,
        "mso_m15_fvg_count": 0,
        "mso_detected_sweeps_count": 0,
    }


def test_symbol_summary_separates_supported_and_unsupported_candidates():
    rows = [
        _row("XAUUSD", "CANDIDATE", "LONG"),
        _row("NAS100", "CANDIDATE", "SHORT"),
        _row("XAGUSD", "CANDIDATE", "LONG"),
        _row("USDJPY", "CANDIDATE", "LONG"),
        _row("GBPUSD", "NO_TRADE"),
    ]

    payload = build_payload(rows, source_path="shadow_logs/candidate_features_log.jsonl")
    coverage = payload["current_coverage"]

    assert coverage["supported_candidate_counts"] == {"NAS100": 1, "XAGUSD": 1, "XAUUSD": 1}
    assert coverage["unsupported_candidate_counts"] == {"USDJPY": 1}
    assert coverage["unsupported_candidate_total"] == 1
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["registration_verdict"] == "NO_PROXY_MAPPING_ACTIVATED"


def test_priority_queue_freezes_proxy_order_and_transform_risk():
    payload = build_payload(
        [
            _row("XAGUSD", "CANDIDATE", "LONG"),
            _row("USDJPY", "CANDIDATE", "SHORT"),
            _row("GBPUSD", "CANDIDATE", "LONG"),
            _row("GBPJPY", "CANDIDATE", "SHORT"),
        ],
        source_path="shadow_logs/candidate_features_log.jsonl",
    )
    queue = payload["priority_queue"]

    assert [item["symbol"] for item in queue] == ["XAGUSD", "USDJPY", "GBPUSD", "GBPJPY"]
    by_symbol = {item["symbol"]: item for item in queue}
    assert by_symbol["XAGUSD"]["databento_symbols"] == ["SI.v.0"]
    assert by_symbol["XAGUSD"]["activation_status"] == "SUPPORTED_RESEARCH_PROXY_MAP"
    assert by_symbol["USDJPY"]["databento_symbols"] == ["6J.v.0"]
    assert by_symbol["USDJPY"]["activation_status"] == "NOT_IN_FUTURES_PROXY_MAP"
    assert by_symbol["USDJPY"]["transform_complexity"] == "medium"
    assert by_symbol["GBPUSD"]["activation_status"] == "SUPPORTED_RESEARCH_PROXY_MAP"
    assert by_symbol["GBPJPY"]["databento_symbols"] == ["6B.v.0", "6J.v.0"]
    assert by_symbol["GBPJPY"]["transform_complexity"] == "high"


def test_proxy_candidates_do_not_activate_research_manifest():
    assert set(PROXY_CANDIDATES) == {"XAGUSD", "USDJPY", "GBPUSD", "GBPJPY"}
    assert all(item["recommended_rank"] >= 1 for item in PROXY_CANDIDATES.values())
    assert PROXY_CANDIDATES["GBPJPY"]["transform_complexity"] == "high"
    assert PROXY_CANDIDATES["GBPUSD"]["operational_relevance"] == "observer_or_control_symbol"


def test_report_artifact_contains_required_research_sections_if_present():
    report = Path(
        "research/databento_orderflow_capture_2026-05-02/"
        "ORDERFLOW_PROXY_MAPPING_PRIORITY_AUDIT_2026-05-02.json"
    )
    if not report.exists():
        return

    payload = json.loads(report.read_text(encoding="utf-8"))
    synth = payload["synthesis"]

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert "ambiguity_ledger" in synth
    assert "opened_questions" in synth
    assert "next_steps" in synth
    assert payload["validation_protocol"]["explicitly_blocked"]
