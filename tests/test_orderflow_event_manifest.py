from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from src.research_infra import orderflow_event_manifest as mod


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"orderflow_event_manifest_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_floor_to_m15_uses_prior_boundary():
    ts = mod.parse_utc("2026-04-17T00:16:10.123456+00:00")
    assert mod.floor_to_m15(ts).isoformat() == "2026-04-17T00:15:00+00:00"


def test_build_events_maps_supported_candidate_to_futures_window():
    rows = [
        {
            "timestamp_utc": "2026-04-17T13:16:05+00:00",
            "symbol": "XAUUSD",
            "decision": "CANDIDATE",
            "framework": "ob_retest",
            "setup_grade": "A+",
            "m15_choch_detected": True,
            "h4_aligned": True,
            "mso_h1_unmitigated_ob_count": 1,
            "mso_h1_fvg_count": 2,
            "mso_m15_fvg_count": 3,
            "mso_detected_sweeps_count": 4,
            "trade_parameters": {"direction": "LONG"},
        }
    ]
    events = mod.build_events(
        rows,
        source_path="shadow.jsonl",
        pre_minutes=30,
        post_minutes=45,
    )
    assert len(events) == 1
    event = events[0]
    assert event["databento_symbols"] == ["GC.v.0"]
    assert event["canonical_m15_close_utc"] == "2026-04-17T13:15:00+00:00"
    assert event["window_start_utc"] == "2026-04-17T12:45:00+00:00"
    assert event["window_end_utc"] == "2026-04-17T14:00:00+00:00"
    assert event["event_class"] == "candidate"
    assert "framework_ob_retest" in event["tags"]


def test_build_events_maps_new_research_only_proxy_symbols():
    rows = [
        {
            "timestamp_utc": "2026-04-17T13:16:05+00:00",
            "symbol": "XAGUSD",
            "decision": "CANDIDATE",
        },
        {
            "timestamp_utc": "2026-04-17T13:31:05+00:00",
            "symbol": "GBPUSD",
            "decision": "CANDIDATE",
        },
    ]

    events = mod.build_events(
        rows,
        source_path="shadow.jsonl",
        pre_minutes=30,
        post_minutes=45,
    )

    by_symbol = {event["symbol"]: event["databento_symbols"] for event in events}
    assert by_symbol["XAGUSD"] == ["SI.v.0"]
    assert by_symbol["GBPUSD"] == ["6B.v.0"]


def test_available_end_cap_truncates_and_excludes_unavailable_events():
    rows = [
        {
            "timestamp_utc": "2026-05-01T15:45:05+00:00",
            "symbol": "XAUUSD",
            "decision": "CANDIDATE",
        },
        {
            "timestamp_utc": "2026-05-01T16:00:05+00:00",
            "symbol": "XAUUSD",
            "decision": "CANDIDATE",
        },
    ]
    events = mod.build_events(
        rows,
        source_path="shadow.jsonl",
        pre_minutes=60,
        post_minutes=60,
        available_end_utc="2026-05-01T16:00:00+00:00",
    )
    assert len(events) == 1
    assert events[0]["window_end_utc"] == "2026-05-01T16:00:00+00:00"
    assert events[0]["window_truncated_at_available_end"] is True


def test_merge_fetch_groups_merges_overlapping_same_symbol_windows():
    events = [
        {
            "event_id": "a",
            "databento_symbols": ["NQ.v.0"],
            "window_start_utc": "2026-04-17T13:00:00+00:00",
            "window_end_utc": "2026-04-17T14:00:00+00:00",
            "symbol": "NAS100",
            "event_class": "candidate",
        },
        {
            "event_id": "b",
            "databento_symbols": ["NQ.v.0"],
            "window_start_utc": "2026-04-17T14:10:00+00:00",
            "window_end_utc": "2026-04-17T15:00:00+00:00",
            "symbol": "NAS100",
            "event_class": "m15_choch_context",
        },
    ]
    groups = mod.merge_fetch_groups(events, merge_gap_minutes=15)
    assert len(groups) == 1
    assert groups[0]["event_count"] == 2
    assert groups[0]["start_utc"] == "2026-04-17T13:00:00+00:00"
    assert groups[0]["end_utc"] == "2026-04-17T15:00:00+00:00"


def test_build_payload_keeps_no_promotion_and_ambiguities():
    payload = mod.build_payload(
        [
            {
                "timestamp_utc": "2026-04-17T13:16:05+00:00",
                "symbol": "NAS100",
                "decision": "NO_TRADE",
                "m15_choch_detected": True,
            }
        ],
        source_path="shadow.jsonl",
        pre_minutes=60,
        post_minutes=60,
        merge_gap_minutes=15,
        available_end_utc=None,
    )
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["synthesis"]["event_count"] == 1
    assert payload["synthesis"]["ambiguities"]
