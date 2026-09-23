from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import build_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_2026_05_10 as builder


def _us(value: datetime) -> int:
    return int((value - builder.SIERRA_EPOCH).total_seconds() * 1_000_000)


def _write_scid(path: Path, records: list[tuple]) -> None:
    with path.open("wb") as handle:
        handle.write(builder.HEADER_STRUCT.pack(b"SCID", 56, 40, 1, 0, 0, b"\0" * 36))
        for record in records:
            handle.write(builder.RECORD_STRUCT.pack(*record))


def _record(ts: datetime, close: float, bid_volume: int = 4, ask_volume: int = 6) -> tuple:
    total_volume = bid_volume + ask_volume
    return (
        _us(ts),
        close - 0.1,
        close + 0.2,
        close - 0.3,
        close,
        2,
        total_volume,
        bid_volume,
        ask_volume,
    )


def test_synthetic_scid_day_and_candidate_coverage(tmp_path: Path):
    scid = tmp_path / "XAUUSD.scid"
    records = [
        _record(datetime(2026, 4, 15, 14, 15, 4, 900000, tzinfo=timezone.utc), 2401.0),
        _record(datetime(2026, 4, 15, 14, 15, 5, 20000, tzinfo=timezone.utc), 2401.5),
        _record(datetime(2026, 4, 15, 14, 15, 6, tzinfo=timezone.utc), 2402.0),
        _record(datetime(2026, 4, 16, 9, 30, 5, 10000, tzinfo=timezone.utc), 2410.0),
    ]
    _write_scid(scid, records)
    header = builder.parse_scid_header(scid)

    day = builder.day_summary(scid, header, "2026-04-15")
    assert day["row_count"] == 3
    assert day["timestamp_resolution"]["min_positive_delta_us"] == 120000
    assert day["volume_totals"]["total_volume"] == 30
    assert day["record_status_anomaly_counts"] == {}

    candidate = {
        "candidate_id": "XAUUSD_2026-04-15T14:15:05.007998+00:00",
        "candidate_utc": "2026-04-15T14:15:05.007998Z",
        "contamination_or_embargo_excluded": False,
    }
    summary = builder.candidate_summary(scid, header, candidate)
    assert summary["rows_plus_minus_60_seconds"] == 3
    assert summary["nearest_records"]["strict_preceding_record"]["timestamp_utc"] == "2026-04-15T14:15:04.900000Z"
    assert summary["nearest_records"]["at_or_following_record"]["timestamp_utc"] == "2026-04-15T14:15:05.020000Z"
    assert summary["candidate_coverage_status"] == "SCID_RECORDS_PRESENT_AROUND_CANDIDATE"


def test_mt5_field_comparison_preserves_hard_blockers():
    audit = builder.build_field_comparison_audit()
    fields = {row["field"]: row for row in audit["field_rows"]}

    assert audit["mt5_tick_contract_satisfied"] is False
    assert audit["hard_absent_fields"] == ["bid", "ask", "flags"]
    assert fields["bid"]["presence_status"] == "ABSENT"
    assert fields["ask"]["presence_status"] == "ABSENT"
    assert fields["flags"]["presence_status"] == "ABSENT"
    assert fields["last"]["presence_status"] == "DERIVABLE_ONLY_AS_PROXY"


def test_generated_artifacts_keep_context_only_packet_and_manual_export_blockers():
    source = json.loads(
        (builder.ROUTE_DIR / f"{builder.PREFIX}_SCID_SOURCE_HASH_HEADER_AUDIT_{builder.DATE}.json").read_text(
            encoding="utf-8"
        )
    )
    coverage = json.loads(
        (builder.ROUTE_DIR / f"{builder.PREFIX}_SCID_DAY_CANDIDATE_COVERAGE_LEDGER_{builder.DATE}.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(
        (builder.ROUTE_DIR / f"{builder.PREFIX}_SOURCE_HASHED_ALTERNATE_PACKET_{builder.DATE}.json").read_text(
            encoding="utf-8"
        )
    )
    blockers = json.loads(
        (builder.ROUTE_DIR / f"{builder.PREFIX}_FIELD_MISMATCH_BLOCKER_LEDGER_{builder.DATE}.json").read_text(
            encoding="utf-8"
        )
    )
    owner = json.loads(
        (builder.ROUTE_DIR / f"{builder.PREFIX}_OWNER_MANUAL_EXPORT_FALLBACK_MANIFEST_{builder.DATE}.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(source["raw_source"]["source_sha256"]) == 64
    assert {row["source_date"]: row["row_count"] for row in coverage["day_coverage"]} == {
        "2026-04-15": 72119,
        "2026-04-16": 70048,
    }
    assert len(coverage["candidate_coverage"]) == 3
    assert packet["packet_admissibility_status"] == "ADMISSIBLE_AS_SCID_MARKET_ACTIVITY_CONTEXT_ONLY"
    assert packet["mt5_tick_recovery_equivalent"] is False
    assert packet["closes_owner_tick_requests"] is False
    assert blockers["terminal_blocker_status"] == "MT5_BID_ASK_TICK_CONTRACT_NOT_SATISFIED_BY_SCID"
    assert blockers["owner_tick_requests_remain_open"] is True
    assert owner["remaining_market_data_export_request_count"] == 2
