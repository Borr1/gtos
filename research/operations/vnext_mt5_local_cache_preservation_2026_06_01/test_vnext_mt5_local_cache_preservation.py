from __future__ import annotations

import os
import sys
import tarfile
from pathlib import Path

ROUTE_DIR = Path(__file__).resolve().parent
if str(ROUTE_DIR) not in sys.path:
    sys.path.insert(0, str(ROUTE_DIR))

import build_vnext_mt5_local_cache_preservation as builder


def test_bases_market_history_tick_and_metadata_classification() -> None:
    base = builder.ACTIVE_TERMINAL_ROOT / "bases" / "redacted_account-Server 3"

    hcc = builder.classify_path(base / "history" / "XAUUSD" / "2024.hcc")
    assert hcc["evidence_role"] == "market_history"
    assert hcc["archive_decision"] == "include_archive"
    assert hcc["server_or_broker_folder"] == "redacted_account-Server 3"
    assert hcc["symbol"] == "XAUUSD"
    assert hcc["timeframe"] == "M1_PACKED_YEAR"
    assert hcc["first_date"] == "2024-01-01"
    assert hcc["last_date"] == "2024-12-31"

    hc = builder.classify_path(base / "history" / "XAUUSD" / "cache" / "M15.hc")
    assert hc["evidence_role"] == "bar_cache"
    assert hc["timeframe"] == "M15"

    tkc = builder.classify_path(base / "ticks" / "XAUUSD" / "202604.tkc")
    assert tkc["evidence_role"] == "tick_cache"
    assert tkc["first_date"] == "2026-04-01"
    assert tkc["last_date"] == "2026-04-30"

    welcome = builder.classify_path(base / "XAUUSD.welcome")
    assert welcome["evidence_role"] == "broker_server_metadata"

    trade_cache = builder.classify_path(base / "trades" / "33768217" / "deals_2026.04.dat")
    assert trade_cache["evidence_role"] == "broker_lifecycle_local_cache"


def test_secret_and_config_exclusion_records_path_hash_without_clear_path(tmp_path: Path) -> None:
    sensitive = tmp_path / "config" / "accounts.dat"
    sensitive.parent.mkdir()
    sensitive.write_bytes(b"do-not-copy")
    row = builder.file_row(sensitive, sensitive.stat(), [])
    assert row["archive_decision"] == "exclude_sensitive"
    assert row["path"] is None
    assert row["path_sha256"]
    assert row["redacted_path"].startswith("REDACTED_PATH_SHA256:")
    assert row["exclusion_reason"]


def test_binary_safe_date_extraction_uses_filename_only() -> None:
    # These paths do not need to exist; the inference must not open binary files.
    first_date, last_date, source = builder.infer_date_window(
        builder.ACTIVE_TERMINAL_ROOT / "bases" / "redacted_account-Server 3" / "ticks" / "US30" / "202604.tkc"
    )
    assert (first_date, last_date, source) == ("2026-04-01", "2026-04-30", "filename_year_month")

    first_date, last_date, source = builder.infer_date_window(
        builder.ACTIVE_TERMINAL_ROOT / "bases" / "redacted_account-Server 3" / "history" / "GBPJPY" / "2025.hcc"
    )
    assert (first_date, last_date, source) == ("2025-01-01", "2025-12-31", "filename_year")


def test_manifest_archive_listing_parser(tmp_path: Path) -> None:
    source = tmp_path / "source.log"
    source.write_text("runtime evidence\n", encoding="utf-8")
    archive_path = tmp_path / "proof.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(source, arcname="terminal_roaming/logs/source.log", recursive=False)

    listing = builder.list_archive(archive_path)
    assert len(listing) == 1
    assert listing[0]["archive_member_path"] == "terminal_roaming/logs/source.log"
    assert listing[0]["size_bytes"] == os.path.getsize(source)
    assert builder.sha256_file(archive_path)


def test_mql5_files_and_program_install_are_archived() -> None:
    mql5_file = builder.classify_path(builder.ACTIVE_TERMINAL_ROOT / "MQL5" / "Files" / "agent_signals_XAUUSD.jsonl")
    assert mql5_file["evidence_role"] == "mql5_files_evidence"
    assert mql5_file["archive_decision"] == "include_archive"
    assert mql5_file["symbol"] == "XAUUSD"

    program_file = builder.classify_path(builder.PROGRAM_FILES_ROOT / "terminal64.exe")
    assert program_file["evidence_role"] == "program_install_reproducibility"
    assert program_file["archive_decision"] == "include_archive"
