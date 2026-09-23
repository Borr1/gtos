from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_full_historical_candidate_generation_replay_2026_05_24/"
    "build_vnext_full_replay_stage01_source_universe_2026_05_24.py"
)


def load_stage01_module():
    spec = importlib.util.spec_from_file_location("vnext_full_stage01", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_session_bucket_uses_broad_replay_windows():
    stage01 = load_stage01_module()

    assert stage01.session_bucket("2026-05-01 00:00:00") == "tokyo_broad"
    assert stage01.session_bucket("2026-05-01 07:15:00") == "london_broad"
    assert stage01.session_bucket("2026-05-01 13:45:00") == "ny_broad"
    assert stage01.session_bucket("2026-05-01 18:00:00") == "off_kz_broad"


def test_path_r_contract_separates_ltf_and_proxy_modes():
    stage01 = load_stage01_module()
    contract = stage01.path_r_scoring_contract()

    assert contract["source_mode_priority"] == [
        "tick_or_sierra_path_aware",
        "m1_path_aware",
        "m5_path_aware",
        "bar_close_m15",
        "ohlc_only_proxy",
        "missing_source",
    ]
    assert contract["source_repair_link_required_for_missing_modes"] is True
    assert "current_config_shadow" in contract["mode_rows_required"]
    assert "hypothetical_activated_vnext" in contract["mode_rows_required"]


def test_read_csv_metadata_writes_market_bar_denominator_rows(tmp_path):
    stage01 = load_stage01_module()
    source = tmp_path / "XAUUSD_M15.csv"
    with source.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time", "open", "high", "low", "close", "volume"])
        writer.writerow(["2026-05-01 07:00:00", "1", "2", "0.5", "1.5", "10"])
        writer.writerow(["2026-05-01 13:15:00", "1.5", "2.5", "1.0", "2.0", "11"])

    metadata, rows = stage01.read_csv_metadata_and_m15_rows(
        tmp_path,
        source,
        "XAUUSD",
        "M15",
        "abc123",
    )

    assert metadata["data_rows"] == 2
    assert metadata["first_time_utc"] == "2026-05-01 07:00:00"
    assert metadata["last_time_utc"] == "2026-05-01 13:15:00"
    assert len(rows) == 2
    assert {row["source_origin"] for row in rows} == {"market_bar_enumeration"}
    assert {row["candidate_generation_disposition"] for row in rows} == {
        "pending_candidate_generation"
    }
    assert rows[0]["session_bucket"] == "london_broad"
    assert rows[1]["session_bucket"] == "ny_broad"
