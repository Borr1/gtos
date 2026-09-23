from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.research_infra.v4u_ordered_path_hydration import (
    build_rolling_hydration_oracle,
)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_proxy_m15_sources_are_rejected_for_ordered_path_truth(tmp_path: Path) -> None:
    ordered = tmp_path / "ordered.jsonl"
    candidates = tmp_path / "candidates.jsonl"
    write_jsonl(
        ordered,
        [
            {
                "candidate_id": "c2",
                "symbol": "EURUSD",
                "asof_utc": "2022-01-03T08:15:00+00:00",
                "ordered_path_source_status": "ordered_touch_times_missing",
                "configured_target_r": 2.0,
            }
        ],
    )
    write_jsonl(
        candidates,
        [
            {
                "candidate_id": "c2",
                "symbol": "EURUSD",
                "asof_utc": "2022-01-03T08:15:00+00:00",
                "session": "LONDON_BROAD",
                "side": "SHORT",
                "entry_reference": 1.2,
                "stop_or_invalidation": 1.201,
                "source_status": "source_window_incomplete",
                "source_completeness": 0.45,
            }
        ],
    )
    proxy = tmp_path / "data" / "mt5_research_exports" / "phase" / "EURUSD_M15.csv"
    proxy.parent.mkdir(parents=True)
    proxy.write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2022-01-03T08:15:00+00:00,1.2,1.201,1.199,1.2,1",
                "2022-01-03T08:30:00+00:00,1.2,1.202,1.198,1.199,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report, rows = build_rolling_hydration_oracle(
        ordered_path_ledger=ordered,
        candidate_ledger=candidates,
        source_roots=(tmp_path / "data",),
        scratch_root=tmp_path / "scratch",
        run_id="test_proxy",
    )

    assert report["source_index_summary"]["source_kind_counts"] == {"m15_proxy": 1}
    assert report["verdict"]["proxy_sources_used_as_broker_native_truth"] == 0
    assert rows[0]["coverage_status"] == "eligible_ltf_missing"
    assert rows[0]["matched_sources"] == []
    assert rows[0]["rejected_sources"][0]["source_label"] == (
        "proxy_m15_context_not_ordered_path_truth"
    )
    assert "broker_native" not in json.dumps(rows[0]["rejected_sources"])
    assert rows[0]["oracle_status"] == "not_run_no_eligible_ltf_source"


def test_unlabeled_mt5_research_export_m1_is_rejected_for_ordered_path_truth(tmp_path: Path) -> None:
    ordered = tmp_path / "ordered.jsonl"
    candidates = tmp_path / "candidates.jsonl"
    write_jsonl(
        ordered,
        [
            {
                "candidate_id": "c_unlabeled",
                "symbol": "NAS100",
                "asof_utc": "2026-06-02T13:00:00+00:00",
                "ordered_path_source_status": "ordered_touch_times_missing",
                "configured_target_r": 2.0,
            }
        ],
    )
    write_jsonl(
        candidates,
        [
            {
                "candidate_id": "c_unlabeled",
                "symbol": "NAS100",
                "asof_utc": "2026-06-02T13:00:00+00:00",
                "session": "NY_BROAD",
                "side": "LONG",
                "entry_reference": 100.0,
                "stop_or_invalidation": 99.0,
            }
        ],
    )
    export = tmp_path / "data" / "mt5_research_exports" / "unlabeled" / "NAS100_M1.csv"
    export.parent.mkdir(parents=True)
    export.write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-06-02T13:00:00+00:00,100,100,100,100,1",
                "2026-06-02T13:01:00+00:00,100,102.2,100,102,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report, rows = build_rolling_hydration_oracle(
        ordered_path_ledger=ordered,
        candidate_ledger=candidates,
        source_roots=(tmp_path / "data",),
        scratch_root=tmp_path / "scratch",
        run_id="test_unlabeled_mt5_export",
    )

    assert rows[0]["coverage_status"] == "eligible_ltf_missing"
    assert rows[0]["matched_sources"] == []
    rejected = rows[0]["rejected_sources"][0]
    assert rejected["source_kind"] == "mt5_research_export_m1"
    assert rejected["source_label"] == (
        "mt5_research_export_m1_missing_or_invalid_path_override_provenance"
    )
    assert rejected["source_provenance_status"] == "invalid_mt5_export_manifest_missing"
    assert report["verdict"]["proxy_sources_used_as_broker_native_truth"] == 0


def test_ftmo_owner_authorized_mt5_export_m1_can_be_ordered_path_truth(tmp_path: Path) -> None:
    ordered = tmp_path / "ordered.jsonl"
    candidates = tmp_path / "candidates.jsonl"
    requirement_id = "v4u_ltf_testreq123"
    write_jsonl(
        ordered,
        [
            {
                "candidate_id": "c_ftmo",
                "symbol": "NAS100",
                "asof_utc": "2026-06-02T13:00:00+00:00",
                "ordered_path_source_status": "ordered_touch_times_missing",
                "configured_target_r": 2.0,
            }
        ],
    )
    write_jsonl(
        candidates,
        [
            {
                "candidate_id": "c_ftmo",
                "symbol": "NAS100",
                "asof_utc": "2026-06-02T13:00:00+00:00",
                "session": "NY_BROAD",
                "side": "LONG",
                "entry_reference": 100.0,
                "stop_or_invalidation": 99.0,
            }
        ],
    )
    export = (
        tmp_path
        / "data"
        / "mt5_research_exports"
        / f"v4u_ftmo_ltf_{requirement_id}"
        / "NAS100_M1.csv"
    )
    export.parent.mkdir(parents=True)
    export.write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-06-02T13:00:00+00:00,100,100,100,100,1",
                "2026-06-02T13:01:00+00:00,100,102.2,100,102,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "mt5_research_ohlcv_export_v1",
        "account": {"login": 123456, "server": "FTMO-Demo"},
        "source_provenance": {
            "source_broker": "FTMO",
            "source_role": "owner_authorized_path_override",
            "replaces_missing_frozen_path_source": True,
            "not_redacted_account_native": True,
            "source_truth_scope": "ordered_price_path_only_not_broker_order_lifecycle_truth",
            "handoff_requirement_id": requirement_id,
            "broker_lifecycle_truth_satisfied": False,
            "asof_decision_truth_satisfied": False,
        },
        "files": {
            "NAS100_M1": {
                "path": str(export),
                "file_symbol": "NAS100",
                "mt5_symbol": "NDX100",
                "timeframe": "M1",
                "rows": 2,
                "row_count": 2,
                "sha256": _sha256(export),
                "source_server": "FTMO-Demo",
                "source_account_login": 123456,
                "export_tool": "scripts/export_mt5_research_ohlcv.py",
            }
        },
    }
    (export.parent / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    report, rows = build_rolling_hydration_oracle(
        ordered_path_ledger=ordered,
        candidate_ledger=candidates,
        source_roots=(tmp_path / "data",),
        scratch_root=tmp_path / "scratch",
        run_id="test_ftmo_mt5_export",
    )

    row = rows[0]
    assert row["coverage_status"] == "eligible_ltf_available"
    assert row["oracle_status"] == "resolved"
    assert row["oracle_result"]["terminal_outcome"] == "target_reached_before_stop"
    source = row["matched_sources"][0]
    assert source["source_label"] == "ftmo_owner_authorized_m1_ltf_path_override"
    assert source["source_broker"] == "FTMO"
    assert source["source_role"] == "owner_authorized_path_override"
    assert source["not_redacted_account_native"] is True
    assert source["source_provenance_status"] == "valid_owner_authorized_path_override"
    assert source["handoff_requirement_id"] == requirement_id
    assert report["source_index_summary"]["source_provenance_status_counts"][
        "valid_owner_authorized_path_override"
    ] == 1


def test_ftmo_owner_authorized_mt5_tick_export_can_be_ordered_path_truth(tmp_path: Path) -> None:
    ordered = tmp_path / "ordered.jsonl"
    candidates = tmp_path / "candidates.jsonl"
    requirement_id = "v4u_ltf_tickreq123"
    write_jsonl(
        ordered,
        [
            {
                "candidate_id": "c_tick",
                "symbol": "NAS100",
                "asof_utc": "2026-06-02T13:00:00+00:00",
                "ordered_path_source_status": "ordered_touch_times_missing",
                "configured_target_r": 2.0,
            }
        ],
    )
    write_jsonl(
        candidates,
        [
            {
                "candidate_id": "c_tick",
                "symbol": "NAS100",
                "asof_utc": "2026-06-02T13:00:00+00:00",
                "session": "NY_BROAD",
                "side": "LONG",
                "entry_reference": 100.0,
                "stop_or_invalidation": 99.0,
            }
        ],
    )
    export = (
        tmp_path
        / "data"
        / "mt5_research_exports"
        / f"v4u_ftmo_ltf_{requirement_id}"
        / "ticks"
        / "NAS100"
        / "window_ticks.jsonl"
    )
    export.parent.mkdir(parents=True)
    write_jsonl(
        export,
        [
            {
                "ts_utc": "2026-06-02T13:00:01+00:00",
                "bid": 99.9,
                "ask": 100.0,
                "last": 99.95,
            },
            {
                "ts_utc": "2026-06-02T13:00:02+00:00",
                "bid": 102.1,
                "ask": 102.2,
                "last": 102.15,
            },
        ],
    )
    manifest = {
        "schema_version": "mt5_research_tick_export_v1",
        "account": {"login": 123456, "server": "FTMO-Demo"},
        "source_provenance": {
            "source_broker": "FTMO",
            "source_role": "owner_authorized_path_override",
            "replaces_missing_frozen_path_source": True,
            "not_redacted_account_native": True,
            "source_truth_scope": "ordered_price_path_only_not_broker_order_lifecycle_truth",
            "handoff_requirement_id": requirement_id,
            "broker_lifecycle_truth_satisfied": False,
            "asof_decision_truth_satisfied": False,
        },
        "files": {
            "NAS100_window_TICK": {
                "path": str(export),
                "file_symbol": "NAS100",
                "mt5_symbol": "NDX100",
                "timeframe": "TICK",
                "rows": 2,
                "row_count": 2,
                "sha256": _sha256(export),
                "source_server": "FTMO-Demo",
                "source_account_login": 123456,
                "export_tool": "scripts/export_mt5_research_ticks.py",
            }
        },
    }
    (export.parents[2] / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    report, rows = build_rolling_hydration_oracle(
        ordered_path_ledger=ordered,
        candidate_ledger=candidates,
        source_roots=(tmp_path / "data",),
        scratch_root=tmp_path / "scratch",
        run_id="test_ftmo_mt5_tick_export",
    )

    row = rows[0]
    assert row["coverage_status"] == "eligible_ltf_available"
    assert row["oracle_status"] == "resolved"
    assert row["oracle_result"]["source"] == "tick"
    assert row["oracle_result"]["terminal_outcome"] == "target_reached_before_stop"
    source = row["matched_sources"][0]
    assert source["source_kind"] == "mt5_research_export_tick"
    assert source["source_label"] == "ftmo_owner_authorized_tick_ltf_path_override"
    assert source["source_broker"] == "FTMO"
    assert source["source_provenance_status"] == "valid_owner_authorized_path_override"
    assert report["source_index_summary"]["source_provenance_status_counts"][
        "valid_owner_authorized_path_override"
    ] == 1


def test_mt5_hcc_cache_is_recoverable_candidate_not_ordered_path_truth(tmp_path: Path) -> None:
    ordered = tmp_path / "ordered.jsonl"
    candidates = tmp_path / "candidates.jsonl"
    write_jsonl(
        ordered,
        [
            {
                "candidate_id": "c3",
                "symbol": "XAUUSD",
                "asof_utc": "2025-04-02T09:00:00+00:00",
                "ordered_path_source_status": "ordered_touch_times_missing",
                "configured_target_r": 2.0,
            }
        ],
    )
    write_jsonl(
        candidates,
        [
            {
                "candidate_id": "c3",
                "symbol": "XAUUSD",
                "asof_utc": "2025-04-02T09:00:00+00:00",
                "session": "LONDON_BROAD",
                "side": "LONG",
                "entry_reference": 100.0,
                "stop_or_invalidation": 99.0,
            }
        ],
    )
    hcc = tmp_path / "Bases" / "redacted_account-Server 2" / "history" / "XAUUSD" / "2025.hcc"
    hcc.parent.mkdir(parents=True)
    hcc.write_bytes(b"binary mt5 hcc fixture")

    report, rows = build_rolling_hydration_oracle(
        ordered_path_ledger=ordered,
        candidate_ledger=candidates,
        source_roots=(tmp_path / "Bases",),
        scratch_root=tmp_path / "scratch",
        run_id="test_hcc",
    )

    row = rows[0]
    assert row["coverage_status"] == "eligible_ltf_missing"
    assert row["oracle_status"] == "not_run_no_eligible_ltf_source"
    assert row["mt5_binary_cache_status"] == (
        "cache_candidate_requires_parser_or_readonly_export"
    )
    assert row["mt5_binary_cache_candidates"][0]["source_label"] == (
        "mt5_hcc_m1_packed_year_cache_candidate"
    )
    assert row["mt5_binary_cache_candidates"][0]["row_count_status"] == (
        "binary_cache_not_parsed_requires_parser_or_readonly_export"
    )
    assert report["metrics"]["rolling_windows_with_mt5_binary_cache_candidate"] == 1
    assert report["verdict"]["rows_with_mt5_binary_cache_candidate_requiring_parser_or_export"] == 1
    assert report["verdict"]["local_or_package_ltf_rows_converted_to_ordered_path_truth"] == 0
    requirement = report["exact_source_requirements"][0]
    assert requirement["mt5_binary_cache_candidate_labels"] == [
        "mt5_hcc_m1_packed_year_cache_candidate"
    ]
    assert requirement["cache_command_templates"][0]["read_only"] is True


def test_mt5_cache_alias_match_is_fail_closed_until_exported(tmp_path: Path) -> None:
    ordered = tmp_path / "ordered.jsonl"
    candidates = tmp_path / "candidates.jsonl"
    write_jsonl(
        ordered,
        [
            {
                "candidate_id": "c4",
                "symbol": "NAS100",
                "asof_utc": "2026-01-14T14:00:00+00:00",
                "ordered_path_source_status": "ordered_touch_times_missing",
                "configured_target_r": 2.0,
            }
        ],
    )
    write_jsonl(
        candidates,
        [
            {
                "candidate_id": "c4",
                "symbol": "NAS100",
                "asof_utc": "2026-01-14T14:00:00+00:00",
                "session": "NY_BROAD",
                "side": "SHORT",
                "entry_reference": 15000.0,
                "stop_or_invalidation": 15010.0,
            }
        ],
    )
    hcc = tmp_path / "Bases" / "redacted_account-Server 2" / "history" / "NDX100" / "2026.hcc"
    hcc.parent.mkdir(parents=True)
    hcc.write_bytes(b"binary mt5 hcc alias fixture")

    report, rows = build_rolling_hydration_oracle(
        ordered_path_ledger=ordered,
        candidate_ledger=candidates,
        source_roots=(tmp_path / "Bases",),
        scratch_root=tmp_path / "scratch",
        run_id="test_alias_hcc",
    )

    assert rows[0]["mt5_binary_cache_status"] == (
        "cache_candidate_requires_parser_or_readonly_export"
    )
    assert rows[0]["mt5_binary_cache_candidates"][0]["symbol"] == "NDX100"
    assert rows[0]["coverage_status"] == "eligible_ltf_missing"
    assert report["verdict"]["proxy_sources_used_as_broker_native_truth"] == 0


def test_mt5_ticks_dat_symbol_cache_is_recoverable_but_date_unproven(tmp_path: Path) -> None:
    ordered = tmp_path / "ordered.jsonl"
    candidates = tmp_path / "candidates.jsonl"
    write_jsonl(
        ordered,
        [
            {
                "candidate_id": "c5",
                "symbol": "GBPUSD",
                "asof_utc": "2023-05-10T08:00:00+00:00",
                "ordered_path_source_status": "ordered_touch_times_missing",
                "configured_target_r": 2.0,
            }
        ],
    )
    write_jsonl(
        candidates,
        [
            {
                "candidate_id": "c5",
                "symbol": "GBPUSD",
                "asof_utc": "2023-05-10T08:00:00+00:00",
                "session": "LONDON_BROAD",
                "side": "LONG",
                "entry_reference": 1.25,
                "stop_or_invalidation": 1.249,
            }
        ],
    )
    ticks = tmp_path / "Bases" / "FTMO-Server3" / "ticks" / "GBPUSD" / "ticks.dat"
    ticks.parent.mkdir(parents=True)
    ticks.write_bytes(b"binary mt5 tick fixture")

    report, rows = build_rolling_hydration_oracle(
        ordered_path_ledger=ordered,
        candidate_ledger=candidates,
        source_roots=(tmp_path / "Bases",),
        scratch_root=tmp_path / "scratch",
        run_id="test_ticks_dat",
    )

    row = rows[0]
    assert row["coverage_status"] == "eligible_ltf_missing"
    assert row["mt5_binary_cache_status"] == (
        "cache_candidate_requires_parser_or_readonly_export"
    )
    assert row["mt5_binary_cache_candidates"][0]["source_label"] == (
        "mt5_tick_binary_cache_candidate"
    )
    assert row["mt5_binary_cache_candidates"][0]["date_min"] is None
    assert report["metrics"]["rolling_windows_with_mt5_binary_cache_candidate"] == 1
    assert report["verdict"]["local_or_package_ltf_rows_converted_to_ordered_path_truth"] == 0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
