from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import build_g12_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_audit_2026_05_10 as builder


def _us(value: datetime) -> int:
    return int((value - builder.SIERRA_EPOCH).total_seconds() * 1_000_000)


def _write_scid(path: Path, records: list[tuple]) -> None:
    with path.open("wb") as handle:
        handle.write(builder.HEADER_STRUCT.pack(b"SCID", 56, 40, 1, 0, 0, b"\0" * 36))
        for record in records:
            handle.write(builder.RECORD_STRUCT.pack(*record))


def _record(ts: datetime, close: float, bid_volume: int = 3, ask_volume: int = 7) -> tuple:
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


def test_synthetic_scid_independent_day_and_nearest_window(tmp_path: Path):
    scid = tmp_path / "XAUUSD.scid"
    records = [
        _record(datetime(2026, 4, 15, 14, 15, 4, 900000, tzinfo=timezone.utc), 2400.0),
        _record(datetime(2026, 4, 15, 14, 15, 5, 20000, tzinfo=timezone.utc), 2401.0),
        _record(datetime(2026, 4, 15, 14, 16, 0, tzinfo=timezone.utc), 2402.0),
        _record(datetime(2026, 4, 16, 9, 30, 5, 30000, tzinfo=timezone.utc), 2410.0),
    ]
    _write_scid(scid, records)
    header = builder.parse_scid_header(scid)

    assert header.record_count == 4
    day = builder.day_summary(scid, header, "2026-04-15")
    assert day["row_count"] == 3
    assert day["volume_totals"]["total_volume"] == 30
    assert day["timestamp_resolution"]["min_positive_delta_us"] == 120000

    candidate = {
        "candidate_id": "XAUUSD_2026-04-15T14:15:05.007998+00:00",
        "candidate_utc": "2026-04-15T14:15:05.007998Z",
        "source_date": "2026-04-15",
        "owner_request_id": "OWNER-TICK-TEST",
        "target_mt5_tick_path": "data/ticks/XAUUSD/2026-04-15.parquet",
        "contamination_or_embargo_excluded": False,
    }
    summary = builder.candidate_summary(scid, header, candidate)
    assert summary["rows_plus_minus_60_seconds"] == 3
    assert summary["nearest_records"]["strict_preceding_record"]["timestamp_utc"] == "2026-04-15T14:15:04.900000Z"
    assert summary["nearest_records"]["at_or_following_record"]["timestamp_utc"] == "2026-04-15T14:15:05.020000Z"
    assert summary["candidate_coverage_status"] == "SCID_RECORDS_PRESENT_AROUND_CANDIDATE"


def test_mt5_field_blockers_do_not_allow_scid_quote_substitution():
    field_rows = builder.build_field_rows()
    fields = {row["field"]: row for row in field_rows}
    hard_absent = [row["field"] for row in field_rows if row["blocker_class"] == "HARD_FIELD_ABSENT"]
    proxy_only = [row["field"] for row in field_rows if row["blocker_class"] == "PROXY_ONLY_NON_EQUIVALENT"]

    assert hard_absent == ["bid", "ask", "flags"]
    assert proxy_only == ["time_msc", "last", "volume", "broker_symbol"]
    assert fields["bid"]["satisfies_mt5_tick_contract_field"] is False
    assert fields["ask"]["satisfies_mt5_tick_contract_field"] is False
    assert fields["flags"]["presence_status"] == "ABSENT"


def test_generated_g12_artifacts_close_context_only_with_open_mt5_blockers():
    source = json.loads(
        (builder.ROUTE_DIR / f"{builder.PREFIX}_SOURCE_HASH_HEADER_COVERAGE_REAUDIT_{builder.DATE}.json").read_text(
            encoding="utf-8"
        )
    )
    candidates = json.loads(
        (builder.ROUTE_DIR / f"{builder.PREFIX}_CANDIDATE_WINDOW_REPRODUCIBILITY_AUDIT_{builder.DATE}.json").read_text(
            encoding="utf-8"
        )
    )
    decision = json.loads(
        (builder.ROUTE_DIR / f"{builder.PREFIX}_DECISION_LEDGER_{builder.DATE}.json").read_text(encoding="utf-8")
    )
    next_step = json.loads(
        (builder.ROUTE_DIR / f"{builder.PREFIX}_NEXT_STEP_RECOMMENDATION_{builder.DATE}.json").read_text(
            encoding="utf-8"
        )
    )

    assert source["raw_source"]["source_sha256"] == builder.EXPECTED_SCID_SHA256
    assert {row["source_date"]: row["row_count"] for row in source["day_coverage"]} == builder.EXPECTED_DAY_COUNTS
    assert len(candidates["candidate_coverage"]) == 3
    assert candidates["april16_candidate_rows_remain_contamination_embargo_excluded"] is True
    assert decision["terminal_decision"] == "ACCEPT_TARGET_ROUTE_AS_SOURCE_HASHED_SCID_CONTEXT_ONLY_WITH_MT5_TICK_BLOCKERS_OPEN"
    assert decision["mt5_tick_recovery_equivalent"] is False
    assert decision["closes_owner_tick_requests"] is False
    assert decision["owner_manual_mt5_export_still_required"] is True
    assert next_step["no_more_same_evidence_class_work_needed_for_these_dates"] is True
