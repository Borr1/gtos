from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from src.costs import build_post_lifecycle_component_cost
from src.research_infra import lane_rematerialization as lane_rm
from src.research_infra.train_engine import guard


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _manifest(tmp_path: Path, *, bars: list[dict] | None = None) -> tuple[Path, dict]:
    core = {
        "schema": lane_rm.SOURCE_SCHEMA,
        "campaign_sealed": False,
        "window_id": "january_2026",
        "bar_sources": bars or [],
        "tick_sources": [],
        "tick_gaps": [],
    }
    payload = {**core, "manifest_root_sha256": lane_rm._stable_sha256(core)}
    path = tmp_path / "manifests/january_2026.json"
    _write_json(path, payload)
    return path, payload


def _registry(tmp_path: Path, manifest: dict) -> Path:
    core = {
        "schema": lane_rm.REGISTRY_SCHEMA,
        "status": "LANE_TRUE_UTC_INPUT_REGISTRY_SOURCE_READY",
        "campaign_sealed": False,
        "march_window_registered": False,
        "windows": {
            "january_2026": {
                "window": ["2026-01-01", "2026-01-31"],
                "split": "development",
                "surface": "VAL",
                "source_manifest": "manifests/january_2026.json",
                "source_manifest_root_sha256": manifest["manifest_root_sha256"],
                "pack_root": "packs/january_2026",
                "pack_roots": {},
                "pack_status": "NOT_BUILT",
                "campaign_sealed": False,
            }
        },
    }
    payload = {**core, "registry_root_sha256": lane_rm._stable_sha256(core)}
    path = tmp_path / lane_rm.DEFAULT_REGISTRY_NAME
    _write_json(path, payload)
    return path


def _raw_campaign_registry_fixture(
    tmp_path: Path,
    *,
    time_column_basis: str = "true_utc",
    naive_csv_times: bool = False,
) -> tuple[Path, dict[str, Path]]:
    origin = tmp_path / "origin"
    relative_root = Path(".hermes/evidence/phase16/cj-rematerialization/LANE")
    lane_root = origin / relative_root
    component_paths: dict[str, Path] = {}
    bars: list[dict] = []
    definitions = (
        ("D1", "deep_universe_h4d1_2014_2026", "2025-09-01", 60, 86_400),
        ("H4", "deep_universe_h4d1_2014_2026", "2025-09-25", 210, 14_400),
        ("M15", "bridge_ftmo_m15_20250601_20260610", "2025-10-19", 960, 900),
        ("M1", "bridge_ftmo_m1_202510", "2025-10-28", 1_440, 60),
    )
    for timeframe, family, start_text, count, seconds in definitions:
        start = datetime.fromisoformat(start_text).replace(tzinfo=timezone.utc)
        step = timedelta(seconds=seconds)
        relative = relative_root / "bars" / f"EURUSD_{timeframe}.csv"
        path = origin / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=("time", "open", "high", "low", "close", "volume"),
            )
            writer.writeheader()
            writer.writerows(
                {
                    "time": (
                        (start + ordinal * step).replace(tzinfo=None).isoformat()
                        if naive_csv_times
                        else (start + ordinal * step).isoformat()
                    ),
                    "open": 1.0,
                    "high": 1.2,
                    "low": 0.8,
                    "close": 1.1,
                    "volume": ordinal + 1,
                }
                for ordinal in range(count)
            )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        component_paths[timeframe] = path
        bars.append(
            {
                "symbol": "EURUSD",
                "mapped_symbol": "EURUSD",
                "timeframe": timeframe,
                "source_family": family,
                "repo_relpath": relative.as_posix(),
                "row_count": count,
                "sha256": digest,
                "first_utc": start.isoformat(),
                "last_utc": (start + (count - 1) * step).isoformat(),
                "time_column_basis": time_column_basis,
                "broker_clock_rule": lane_rm.NEW_YORK_PLUS_7.name,
            }
        )
    tick_relative = relative_root / "ticks/EURUSD.jsonl"
    tick_path = origin / tick_relative
    tick_path.parent.mkdir(parents=True, exist_ok=True)
    tick_path.write_text(
        '{"time":"2025-10-28T12:00:00+00:00","bid":1.0,"ask":1.1}\n',
        encoding="utf-8",
    )
    tick_sha = hashlib.sha256(tick_path.read_bytes()).hexdigest()
    component_paths["TICK"] = tick_path
    manifest_core = {
        "schema": lane_rm.SOURCE_SCHEMA,
        "status": "LANE_TRUE_UTC_SOURCE_AUTHORITY_VALID",
        "campaign_sealed": False,
        "window_id": "october_2025",
        "window": ["2025-10-01", "2025-10-31"],
        "surface": "VAL",
        "lane_root_repo_relpath": relative_root.as_posix(),
        "bar_sources": bars,
        "tick_sources": [
            {
                "symbol": "EURUSD",
                "mapped_symbol": "EURUSD",
                "source_family": "ftmo_ordered_tick_fixture",
                "repo_relpath": tick_relative.as_posix(),
                "row_count": 1,
                "sha256": tick_sha,
                "first_utc": "2025-10-28T12:00:00+00:00",
                "last_utc": "2025-10-28T12:00:00+00:00",
                "source_server_redacted": "redacted:FT...r3",
                "source_server_hash": hashlib.sha256(b"FTMO-Server3").hexdigest(),
                "source_account_redacted": "redacted:53...16",
                "source_account_hash": hashlib.sha256(b"5316").hexdigest(),
                "time_column_basis": "true_utc",
                "broker_clock_rule": lane_rm.NEW_YORK_PLUS_7.name,
            }
        ],
        "tick_gaps": [],
        "economic_outcomes_read": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    manifest = {
        **manifest_core,
        "manifest_root_sha256": lane_rm._stable_sha256(manifest_core),
    }
    manifest_path = lane_root / "manifests/october_2025.json"
    _write_json(manifest_path, manifest)
    march_sentinel = lane_root / "manifests/MARCH_MUST_NOT_OPEN"
    march_sentinel.mkdir()
    component_paths["MARCH_SENTINEL"] = march_sentinel
    registry_core = {
        "schema": lane_rm.REGISTRY_SCHEMA,
        "status": "LANE_TRUE_UTC_INPUT_REGISTRY_COMPLETE",
        "campaign_sealed": False,
        "march_window_registered": True,
        "windows": {
            "october_2025": {
                "window": ["2025-10-01", "2025-10-31"],
                "split": "lane_validation",
                "surface": "VAL",
                "source_manifest": "manifests/october_2025.json",
                "source_manifest_root_sha256": manifest["manifest_root_sha256"],
                "canonical_source_plan_digest_sha256": "a" * 64,
                "pack_root": "packs/october_2025",
                "pack_roots": {},
                "pack_status": "NOT_BUILT",
            },
            "march_2026": {"source_manifest": "manifests/MARCH_MUST_NOT_OPEN"},
        },
    }
    registry = {
        **registry_core,
        "registry_root_sha256": lane_rm._stable_sha256(registry_core),
    }
    registry_path = lane_root / lane_rm.DEFAULT_REGISTRY_NAME
    _write_json(registry_path, registry)
    return registry_path, component_paths


def _raw_campaign_test_inputs(
    registry_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> lane_rm.LaneWindowInputs:
    def resolve_test_window(*, registry_path: Path, window_id: str):
        return lane_rm.LaneInputRegistry(
            registry_path,
            allow_registered_march_metadata=True,
        ).resolve(window_id=window_id, purpose=guard.PURPOSE_LANE_ITERATION)

    monkeypatch.setattr(
        lane_rm,
        "_validate_raw_campaign_frozen_authority",
        lambda _inputs: lane_rm.RAW_CAMPAIGN_APPROVED_DAYS,
    )
    monkeypatch.setattr(
        lane_rm,
        "resolve_registered_raw_campaign_window",
        resolve_test_window,
    )
    return resolve_test_window(
        registry_path=registry_path,
        window_id="october_2025",
    )


def _rebind_fixture_tick_component(
    registry_path: Path,
    tick_path: Path,
    payload: bytes,
    *,
    row_count: int,
    first_utc: str,
    last_utc: str,
) -> None:
    tick_path.write_bytes(payload)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    entry = registry["windows"]["october_2025"]
    manifest_path = registry_path.parent / entry["source_manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tick = manifest["tick_sources"][0]
    tick.update(
        {
            "row_count": row_count,
            "first_utc": first_utc,
            "last_utc": last_utc,
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    )
    manifest["manifest_root_sha256"] = lane_rm._manifest_root(
        manifest,
        "manifest_root_sha256",
    )
    _write_json(manifest_path, manifest)
    entry["source_manifest_root_sha256"] = manifest["manifest_root_sha256"]
    registry["registry_root_sha256"] = lane_rm._manifest_root(
        registry,
        "registry_root_sha256",
    )
    _write_json(registry_path, registry)


def test_broker_bar_label_is_repaired_via_us_clock() -> None:
    assert lane_rm._parse_broker_bar_time("2026-01-05 00:00:00") == datetime(
        2026, 1, 4, 22, 0, tzinfo=timezone.utc
    )
    assert lane_rm._parse_broker_bar_time("2026-04-06 00:00:00") == datetime(
        2026, 4, 5, 21, 0, tzinfo=timezone.utc
    )


def test_hour_table_states_direction_and_wraps_previous_day() -> None:
    receipt = lane_rm.hour_correction_table()
    assert receipt["direction"] == "true_utc = old_label - 2 hours"
    assert receipt["rows"][0] == {
        "sealed_january_old_label": "00:00",
        "true_utc_label": "22:00",
        "day_delta": -1,
        "old_label_minus_true_utc_hours": 2,
    }
    assert receipt["rows"][23]["true_utc_label"] == "21:00"
    assert receipt["estate_impact"]["aw_b_time"]["committed_map_cell_count"] == 83
    assert receipt["estate_impact"]["ah_entry_hour"]["correction"] == "none"
    assert receipt["receipt_root_sha256"] == lane_rm._manifest_root(
        receipt, "receipt_root_sha256"
    )


def test_tick_materialization_preserves_raw_epoch_and_only_relabels_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lane_rm, "REPO_ROOT", tmp_path)
    true_utc = datetime(2026, 1, 2, 10, 0, 0, 123000, tzinfo=timezone.utc)
    broker_msc = int((true_utc.timestamp() + 2 * 3600) * 1000)
    source = tmp_path / "input/ticks.jsonl"
    source.parent.mkdir()
    row = {
        "ask": 1.2,
        "bid": 1.1,
        "last": 0.0,
        "time": "2026-01-02T12:00:00.123000+00:00",
        "time_msc": broker_msc,
        "ts_utc": "2026-01-02T12:00:00.123000+00:00",
        "volume": 3.0,
    }
    source.write_text(json.dumps(row) + "\n", encoding="utf-8")
    lane_root = tmp_path / "lane"
    destination = lane_root / "sources/ticks/202601/EURUSD/ticks.jsonl"
    result = lane_rm._transform_tick_file(
        source=source,
        symbol="EURUSD",
        lane_root=lane_root,
        destination_by_window={"january_2026": destination},
        source_metadata={"sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
    )
    output = json.loads(destination.read_text())
    assert output["time_msc"] == broker_msc
    assert output["time"] == true_utc.isoformat()
    assert output["ts_utc"] == true_utc.isoformat()
    assert output["ask"] == row["ask"] and output["bid"] == row["bid"]
    assert result["january_2026"]["raw_broker_epoch_preserved"] is True


def test_tick_authority_persists_relative_paths_and_declares_runtime_root(
    tmp_path: Path,
) -> None:
    tick_path = tmp_path / "lane/ticks/EURUSD.jsonl"
    tick_path.parent.mkdir(parents=True)
    tick_path.write_text('{"time":"2026-01-02T10:00:00+00:00"}\n')
    tick_sha = hashlib.sha256(tick_path.read_bytes()).hexdigest()
    manifest_path = tmp_path / "lane/manifests/january.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("{}\n")
    manifest = {
        "manifest_root_sha256": "a" * 64,
        "tick_sources": [
            {
                "symbol": "EURUSD",
                "mapped_symbol": "EURUSD",
                "repo_relpath": "lane/ticks/EURUSD.jsonl",
                "source_family": "true_utc_ticks",
                "first_utc": "2026-01-02T10:00:00+00:00",
                "last_utc": "2026-01-02T10:00:00+00:00",
                "row_count": 1,
                "sha256": tick_sha,
            }
        ],
    }
    specs, contract = lane_rm._tick_authority(
        repo_root=tmp_path,
        manifest=manifest,
        manifest_path=manifest_path,
    )
    assert contract["logical_repo_root"] == str(tmp_path.resolve())
    assert specs["EURUSD"][0].path == Path("lane/ticks/EURUSD.jsonl")
    assert specs["EURUSD"][0].manifest_path == "lane/manifests/january.json"


def test_source_adapter_resolves_repo_relative_paths_and_bounds_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "lane/bars/EURUSD_M15.csv"
    csv_path.parent.mkdir(parents=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=("time", "open", "high", "low", "close", "volume")
        )
        writer.writeheader()
        writer.writerow(
            {
                "time": "2026-01-02T10:00:00+00:00",
                "open": 1,
                "high": 2,
                "low": 0.5,
                "close": 1.5,
                "volume": 7,
            }
        )
    entry = {
        "symbol": "EURUSD",
        "mapped_symbol": "EURUSD",
        "timeframe": "M15",
        "source_family": "bridge_ftmo_m15_20250601_20260610",
        "repo_relpath": "lane/bars/EURUSD_M15.csv",
        "row_count": 1,
        "sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
    }
    manifest_path, _payload = _manifest(tmp_path, bars=[entry])
    adapter = lane_rm.LaneReplaySourceAccelerator(
        repo_root=tmp_path, manifest_path=manifest_path
    )
    candidates = adapter.accepted_source_candidates(
        symbol="EURUSD",
        physical_timeframe="M15",
        source_family_order=("bridge_ftmo_m15_20250601_20260610",),
    )
    assert candidates[0].source_path == Path("lane/bars/EURUSD_M15.csv")
    rows, grouped, digest = adapter.load_file(
        candidates[0].source_path, symbol="EURUSD"
    )
    assert len(rows) == 1 and len(grouped["2026-01-02"]) == 1
    assert digest == entry["sha256"]
    assert not candidates[0].source_path.is_absolute()


def test_source_adapter_fails_closed_on_byte_drift(tmp_path: Path) -> None:
    csv_path = tmp_path / "lane/EURUSD_M1.csv"
    csv_path.parent.mkdir()
    csv_path.write_text("time,open,high,low,close,volume\n", encoding="utf-8")
    entry = {
        "symbol": "EURUSD",
        "mapped_symbol": "EURUSD",
        "timeframe": "M1",
        "source_family": "bridge_ftmo_m1_202601",
        "repo_relpath": "lane/EURUSD_M1.csv",
        "row_count": 1,
        "sha256": "0" * 64,
    }
    manifest_path, _payload = _manifest(tmp_path, bars=[entry])
    adapter = lane_rm.LaneReplaySourceAccelerator(
        repo_root=tmp_path, manifest_path=manifest_path
    )
    with pytest.raises(lane_rm.LaneRematerializationError, match="sha256_mismatch"):
        adapter.load_file(Path(entry["repo_relpath"]), symbol="EURUSD")


def test_raw_campaign_admission_rejects_synthetic_self_consistent_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path, _paths = _raw_campaign_registry_fixture(tmp_path)
    with pytest.raises(
        lane_rm.LaneRematerializationError,
        match="raw_campaign_registry_authority_mismatch",
    ):
        lane_rm.resolve_registered_raw_campaign_window(
            registry_path=registry_path,
            window_id="october_2025",
        )

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    manifest_path = registry_path.parent / registry["windows"]["october_2025"][
        "source_manifest"
    ]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["synthetic_rewrite"] = True
    manifest["manifest_root_sha256"] = lane_rm._manifest_root(
        manifest,
        "manifest_root_sha256",
    )
    _write_json(manifest_path, manifest)
    registry["windows"]["october_2025"]["source_manifest_root_sha256"] = (
        manifest["manifest_root_sha256"]
    )
    registry["registry_root_sha256"] = lane_rm._manifest_root(
        registry,
        "registry_root_sha256",
    )
    _write_json(registry_path, registry)
    monkeypatch.setattr(lane_rm, "RAW_CAMPAIGN_REGISTRY_PATH", registry_path)
    monkeypatch.setattr(
        lane_rm,
        "RAW_CAMPAIGN_REGISTRY_FILE_SHA256",
        hashlib.sha256(registry_path.read_bytes()).hexdigest(),
    )
    monkeypatch.setattr(
        lane_rm,
        "RAW_CAMPAIGN_REGISTRY_ROOT_SHA256",
        registry["registry_root_sha256"],
    )
    inputs = lane_rm.LaneInputRegistry(
        registry_path,
        allow_registered_march_metadata=True,
    ).resolve(
        window_id="october_2025",
        purpose=guard.PURPOSE_LANE_ITERATION,
    )
    with pytest.raises(
        lane_rm.LaneRematerializationError,
        match="raw_campaign_manifest_authority_mismatch",
    ):
        lane_rm._validate_raw_campaign_frozen_authority(inputs)


def test_raw_campaign_loader_reopens_exact_rows_and_does_not_open_march(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert lane_rm.RAW_CAMPAIGN_SYMBOLS == tuple(
        lane_rm.timewarp.GTOS_24_SYMBOL_SURFACE
    )
    assert len(lane_rm.RAW_CAMPAIGN_SYMBOLS) == 24
    assert len(lane_rm.TICK_SYMBOLS) == 4
    assert len(set(lane_rm.RAW_CAMPAIGN_SYMBOLS) - set(lane_rm.TICK_SYMBOLS)) == 20
    assert lane_rm.RAW_CAMPAIGN_WINDOW_IDS == {
        "october_2025",
        "november_2025",
    }
    registry_path, paths = _raw_campaign_registry_fixture(tmp_path)
    monkeypatch.setattr(lane_rm, "RAW_CAMPAIGN_SYMBOLS", ("EURUSD",))
    monkeypatch.setattr(lane_rm, "TICK_SYMBOLS", ("EURUSD",))
    inputs = _raw_campaign_test_inputs(registry_path, monkeypatch)
    sources = inputs.load_raw_campaign_sources(days=("2025-10-28",))
    assert set(sources) == {"EURUSD"}
    assert set(sources["EURUSD"]) == {
        "D1",
        "H4",
        "H1",
        "M15",
        "M1",
        "TICK",
    }
    for timeframe, source in sources["EURUSD"].items():
        authority = source.component_source_labels[0]
        assert authority["loader_component_file_sha256"] == hashlib.sha256(
            paths["M15" if timeframe == "H1" else timeframe].read_bytes()
        ).hexdigest()
        assert authority["loader_manifest_file_sha256"] == hashlib.sha256(
            inputs.source_manifest_path.read_bytes()
        ).hexdigest()
        assert authority["loader_registry_file_sha256"] == hashlib.sha256(
            registry_path.read_bytes()
        ).hexdigest()
        assert authority["loader_time_column_basis"] == "true_utc"
        assert authority["loader_naive_timestamp_interpretation_allowed"] is False
    h1_authority = sources["EURUSD"]["H1"].component_source_labels[0]
    assert h1_authority["authority_role"] == (
        "deterministic_h1_derived_from_manifest_bound_m15"
    )
    assert h1_authority["p1_packet_equivalence_claimed"] is False
    inputs.validate_raw_campaign_sources(
        days=("2025-10-28",),
        sources=sources,
    )
    assert paths["MARCH_SENTINEL"].is_dir()


def test_raw_campaign_loader_refuses_timebase_and_fresh_reopen_byte_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(lane_rm, "RAW_CAMPAIGN_SYMBOLS", ("EURUSD",))
    monkeypatch.setattr(lane_rm, "TICK_SYMBOLS", ("EURUSD",))
    invalid_registry, _paths = _raw_campaign_registry_fixture(
        tmp_path / "invalid",
        time_column_basis="broker_wall_clock",
    )
    invalid = _raw_campaign_test_inputs(invalid_registry, monkeypatch)
    with pytest.raises(
        lane_rm.LaneRematerializationError,
        match="raw_campaign_bar_authority_invalid",
    ):
        invalid.load_raw_campaign_sources(days=("2025-10-28",))

    naive_registry, _naive_paths = _raw_campaign_registry_fixture(
        tmp_path / "naive",
        naive_csv_times=True,
    )
    naive = _raw_campaign_test_inputs(naive_registry, monkeypatch)
    with pytest.raises(
        lane_rm.LaneRematerializationError,
        match="raw_campaign_timebase_invalid",
    ):
        naive.load_raw_campaign_sources(days=("2025-10-28",))

    registry_path, paths = _raw_campaign_registry_fixture(tmp_path / "valid")
    inputs = _raw_campaign_test_inputs(registry_path, monkeypatch)
    sources = inputs.load_raw_campaign_sources(days=("2025-10-28",))
    paths["M15"].write_text("tampered-after-first-parse\n", encoding="utf-8")
    with pytest.raises(
        lane_rm.LaneRematerializationError,
        match="sha256_mismatch",
    ):
        inputs.validate_raw_campaign_sources(
            days=("2025-10-28",),
            sources=sources,
        )


def test_a1_quote_resolver_issues_manifest_bound_entry_exit_receipts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path, paths = _raw_campaign_registry_fixture(tmp_path)
    entry_utc = "2025-10-28T12:00:00+00:00"
    exit_utc = "2025-10-28T14:00:00+00:00"
    rows = (
        {"time": entry_utc, "bid": 1.0, "ask": 1.1},
        {"time": exit_utc, "bid": 1.4, "ask": 1.5},
    )
    payload = b"".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        for row in rows
    )
    _rebind_fixture_tick_component(
        registry_path,
        paths["TICK"],
        payload,
        row_count=2,
        first_utc=entry_utc,
        last_utc=exit_utc,
    )
    monkeypatch.setattr(lane_rm, "RAW_CAMPAIGN_SYMBOLS", ("EURUSD",))
    monkeypatch.setattr(lane_rm, "TICK_SYMBOLS", ("EURUSD",))
    monkeypatch.setattr(lane_rm, "_QUOTE_OFFSET_STRIDE", 1)
    inputs = _raw_campaign_test_inputs(registry_path, monkeypatch)

    with inputs.quote_source_resolver(days=("2025-10-28",)) as resolver:
        geometry = resolver.resolve_geometry(
            trade_id="occurrence-1/order-1",
            account="FTMO",
            symbol="EURUSD",
            entry_physical_row_index=0,
            exit_physical_row_index=1,
        )
        assert geometry.entry_bid_price == 1.0
        assert geometry.entry_ask_price == 1.1
        assert geometry.exit_bid_price == 1.4
        assert geometry.row_index == 0
        assert geometry.exit_source.row_index == 1
        assert geometry.entry_row_sha256 == hashlib.sha256(
            payload.splitlines(keepends=True)[0]
        ).hexdigest()
        assert geometry.source_authority_root_sha256 == resolver.authority_root_sha256
        build_args = {
            "trade_id": "occurrence-1/order-1",
            "account": "FTMO",
            "symbol": "EURUSD",
            "side": "LONG",
            "entry_utc": datetime.fromisoformat(entry_utc),
            "exit_utc": datetime.fromisoformat(exit_utc),
            "entry_price": 1.1,
            "exit_price": 1.4,
            "sl_distance_price": 100.0,
            "lifecycle_provenance": "A1 manifest-bound selected quote rows",
            "geometry_spread_evidence": geometry,
            "verified_quote_geometry_resolver": resolver,
        }
        packet = build_post_lifecycle_component_cost(**build_args)
        assert packet["status"] == "NOT_EVALUABLE"
        assert "approved_order_geometry_authority_missing" in packet["failures"][0]

        repeated = resolver.resolve_geometry(
            trade_id="occurrence-1/order-1",
            account="FTMO",
            symbol="EURUSD",
            entry_physical_row_index=0,
            exit_physical_row_index=1,
        )
        repeated_packet = build_post_lifecycle_component_cost(
            **{
                **build_args,
                "geometry_spread_evidence": repeated,
            }
        )
        assert repeated_packet == packet

        forged = replace(geometry, exit_bid_price=1.8, exit_ask_price=1.9)
        refused = build_post_lifecycle_component_cost(
            **{
                **build_args,
                "exit_price": 1.8,
                "geometry_spread_evidence": forged,
            }
        )
        assert refused["status"] == "NOT_EVALUABLE"
        assert "not_issued_by_active_resolver" in refused["failures"][0]

    closed = build_post_lifecycle_component_cost(**build_args)
    assert closed["status"] == "NOT_EVALUABLE"
    assert "resolver_not_active" in closed["failures"][0]


def test_a1_quote_resolver_refuses_bad_ordinal_and_post_enter_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path, paths = _raw_campaign_registry_fixture(tmp_path)
    monkeypatch.setattr(lane_rm, "RAW_CAMPAIGN_SYMBOLS", ("EURUSD",))
    monkeypatch.setattr(lane_rm, "TICK_SYMBOLS", ("EURUSD",))
    inputs = _raw_campaign_test_inputs(registry_path, monkeypatch)
    with pytest.raises(
        lane_rm.LaneRematerializationError,
        match="lane_quote_source_component_drift",
    ):
        with inputs.quote_source_resolver(days=("2025-10-28",)) as resolver:
            with pytest.raises(
                lane_rm.LaneRematerializationError,
                match="physical_row_index_out_of_range",
            ):
                resolver.resolve_geometry(
                    trade_id="out-of-range",
                    account="FTMO",
                    symbol="EURUSD",
                    entry_physical_row_index=0,
                    exit_physical_row_index=1,
                )
            paths["TICK"].write_bytes(paths["TICK"].read_bytes() + b"{}\n")


def test_a1_quote_resolver_refuses_equal_time_reverse_source_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path, paths = _raw_campaign_registry_fixture(tmp_path)
    instant = "2025-10-28T12:00:00+00:00"
    payload = (
        b'{"time":"2025-10-28T12:00:00+00:00","bid":1.0,"ask":1.1}\n'
        b'{"time":"2025-10-28T12:00:00+00:00","bid":1.2,"ask":1.3}\n'
    )
    _rebind_fixture_tick_component(
        registry_path,
        paths["TICK"],
        payload,
        row_count=2,
        first_utc=instant,
        last_utc=instant,
    )
    monkeypatch.setattr(lane_rm, "RAW_CAMPAIGN_SYMBOLS", ("EURUSD",))
    monkeypatch.setattr(lane_rm, "TICK_SYMBOLS", ("EURUSD",))
    inputs = _raw_campaign_test_inputs(registry_path, monkeypatch)

    with inputs.quote_source_resolver(days=("2025-10-28",)) as resolver:
        with pytest.raises(
            lane_rm.LaneRematerializationError,
            match="exit_not_after_entry",
        ):
            resolver.resolve_geometry(
                trade_id="reverse-equal-time",
                account="FTMO",
                symbol="EURUSD",
                entry_physical_row_index=1,
                exit_physical_row_index=0,
            )


def test_a1_quote_resolver_refuses_rows_outside_approved_run_days(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path, paths = _raw_campaign_registry_fixture(tmp_path)
    entry_utc = "2025-10-28T12:00:00+00:00"
    held_utc = "2025-10-30T12:00:00+00:00"
    payload = (
        b'{"time":"2025-10-28T12:00:00+00:00","bid":1.0,"ask":1.1}\n'
        b'{"time":"2025-10-30T12:00:00+00:00","bid":1.2,"ask":1.3}\n'
    )
    _rebind_fixture_tick_component(
        registry_path,
        paths["TICK"],
        payload,
        row_count=2,
        first_utc=entry_utc,
        last_utc=held_utc,
    )
    monkeypatch.setattr(lane_rm, "RAW_CAMPAIGN_SYMBOLS", ("EURUSD",))
    monkeypatch.setattr(lane_rm, "TICK_SYMBOLS", ("EURUSD",))
    inputs = _raw_campaign_test_inputs(registry_path, monkeypatch)

    with inputs.quote_source_resolver(days=("2025-10-28",)) as resolver:
        with pytest.raises(
            lane_rm.LaneRematerializationError,
            match="outside_approved_run_days",
        ):
            resolver.resolve_geometry(
                trade_id="held-day-exit",
                account="FTMO",
                symbol="EURUSD",
                entry_physical_row_index=0,
                exit_physical_row_index=1,
            )


@pytest.mark.parametrize("link_parent", (False, True))
def test_a1_quote_resolver_refuses_logical_component_symlink_traversal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    link_parent: bool,
) -> None:
    registry_path, paths = _raw_campaign_registry_fixture(tmp_path)
    tick_path = paths["TICK"]
    if link_parent:
        real_parent = tick_path.parent.with_name("ticks-real")
        tick_path.parent.rename(real_parent)
        tick_path.parent.symlink_to(real_parent.name, target_is_directory=True)
    else:
        real_tick = tick_path.with_name("EURUSD-real.jsonl")
        real_tick.write_bytes(tick_path.read_bytes())
        tick_path.unlink()
        tick_path.symlink_to(real_tick.name)
    monkeypatch.setattr(lane_rm, "RAW_CAMPAIGN_SYMBOLS", ("EURUSD",))
    monkeypatch.setattr(lane_rm, "TICK_SYMBOLS", ("EURUSD",))
    inputs = _raw_campaign_test_inputs(registry_path, monkeypatch)

    with pytest.raises(
        lane_rm.LaneRematerializationError,
        match="component_symlink_refused",
    ):
        with inputs.quote_source_resolver(days=("2025-10-28",)):
            pass


def test_a1_quote_resolver_hashes_the_exact_opened_component_stream(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path, paths = _raw_campaign_registry_fixture(tmp_path)
    tick_path = paths["TICK"]
    original_path = tick_path.with_name("EURUSD-original.jsonl")
    forged_path = tick_path.with_name("EURUSD-forged.jsonl")
    forged_path.write_bytes(
        b'{"time":"2025-10-28T12:00:00+00:00","bid":9.0,"ask":9.1}\n'
    )
    original_tick_authority = lane_rm._tick_authority

    def swap_after_path_hash(**kwargs):
        result = original_tick_authority(**kwargs)
        tick_path.rename(original_path)
        forged_path.rename(tick_path)
        return result

    monkeypatch.setattr(lane_rm, "RAW_CAMPAIGN_SYMBOLS", ("EURUSD",))
    monkeypatch.setattr(lane_rm, "TICK_SYMBOLS", ("EURUSD",))
    monkeypatch.setattr(lane_rm, "_tick_authority", swap_after_path_hash)
    inputs = _raw_campaign_test_inputs(registry_path, monkeypatch)
    try:
        with pytest.raises(
            lane_rm.LaneRematerializationError,
            match="component_open_bytes_mismatch",
        ):
            with inputs.quote_source_resolver(days=("2025-10-28",)):
                pass
    finally:
        if tick_path.exists():
            tick_path.unlink()
        original_path.rename(tick_path)


@pytest.mark.parametrize(
    "payload, row_count",
    (
        (b"\xff\n", 1),
        (b"\n", 1),
        (
            b'{"time":"2025-10-28T12:00:00+00:00","bid":1.0,"bid":1.1,"ask":1.2}\n',
            1,
        ),
        (
            b'{"time":"2025-10-28T12:00:00+00:00","bid":1.0,"ask":1.1}',
            1,
        ),
    ),
)
def test_a1_quote_resolver_requires_strict_utf8_lf_closed_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: bytes,
    row_count: int,
) -> None:
    registry_path, paths = _raw_campaign_registry_fixture(tmp_path)
    _rebind_fixture_tick_component(
        registry_path,
        paths["TICK"],
        payload,
        row_count=row_count,
        first_utc="2025-10-28T12:00:00+00:00",
        last_utc="2025-10-28T12:00:00+00:00",
    )
    monkeypatch.setattr(lane_rm, "RAW_CAMPAIGN_SYMBOLS", ("EURUSD",))
    monkeypatch.setattr(lane_rm, "TICK_SYMBOLS", ("EURUSD",))
    inputs = _raw_campaign_test_inputs(registry_path, monkeypatch)
    with pytest.raises(lane_rm.LaneRematerializationError, match="lane_quote_source"):
        with inputs.quote_source_resolver(days=("2025-10-28",)):
            pass


def test_raw_campaign_admits_frozen_decision_day_but_refuses_reserve_before_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path, _paths = _raw_campaign_registry_fixture(tmp_path)
    monkeypatch.setattr(lane_rm, "RAW_CAMPAIGN_SYMBOLS", ("EURUSD",))
    monkeypatch.setattr(lane_rm, "TICK_SYMBOLS", ("EURUSD",))
    inputs = _raw_campaign_test_inputs(registry_path, monkeypatch)
    assert lane_rm._validate_raw_campaign_manifest(
        inputs,
        days=("2025-10-30",),
    ) == ("2025-10-30",)
    monkeypatch.setattr(
        lane_rm,
        "_resolver_for",
        lambda _inputs: pytest.fail("reserve day reached source resolver"),
    )
    for day in ("2025-10-31", "2025-11-05"):
        with pytest.raises(
            lane_rm.LaneRematerializationError,
            match="raw_campaign_day_not_approved",
        ):
            inputs.load_raw_campaign_sources(days=(day,))


def test_raw_campaign_call_through_attaches_causal_witness_before_generator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path, _paths = _raw_campaign_registry_fixture(tmp_path)
    monkeypatch.setattr(lane_rm, "RAW_CAMPAIGN_SYMBOLS", ("EURUSD",))
    monkeypatch.setattr(lane_rm, "TICK_SYMBOLS", ("EURUSD",))
    inputs = _raw_campaign_test_inputs(registry_path, monkeypatch)
    campaign = lane_rm.timewarp.CampaignConfig(
        name="bounded_raw_fixture",
        phase="engineering_comparator",
        days=("2025-10-28",),
        pending_expiry_minutes=60,
        use_repaired_pending_expiry=True,
        max_candidates_per_symbol_window=0,
        run_smoke_subset=False,
    )
    config = {
        "gtos_vnext_runtime": {
            "wave21_full_flow_truth_mode_enabled": True,
        }
    }
    native_result = {"native": "unchanged"}
    original_selector = lane_rm.timewarp.closed_bar_rows_until
    original_observed_selector = (
        lane_rm.timewarp.observed_successor_closed_bar_rows_until
    )
    original_cwd = Path.cwd()

    def fake_run_campaign(**kwargs):
        assert kwargs["prepared_day_pack"] is None
        assert Path.cwd() == inputs.logical_repo_root
        asof = datetime(2025, 10, 28, 12, 0, tzinfo=timezone.utc) - timedelta(
            microseconds=1
        )
        for timeframe in lane_rm.RAW_CAMPAIGN_DECISION_TIMEFRAMES:
            parent = kwargs["sources"]["EURUSD"][timeframe].rows
            selected = lane_rm.timewarp.closed_bar_rows_until(
                parent,
                timeframe=timeframe,
                asof=asof,
                max_rows=20,
            )
            assert selected
            assert all(
                datetime.fromisoformat(
                    row["wave21_completed_bar_witness"]["successor_open_utc"]
                )
                <= asof
                for row in selected
            )
            if timeframe == "M15":
                assert datetime.fromisoformat(
                    selected[-1]["wave21_completed_bar_witness"][
                        "successor_open_utc"
                    ]
                ) < asof + timedelta(microseconds=1)
                boundary = lane_rm.observed_successor_closed_bar_rows_until(
                    parent,
                    timeframe=timeframe,
                    asof=asof + timedelta(microseconds=1),
                    max_rows=20,
                    attach_witness=True,
                )
                assert datetime.fromisoformat(
                    boundary[-1]["wave21_completed_bar_witness"][
                        "successor_open_utc"
                    ]
                ) == asof + timedelta(microseconds=1)
        adapter = lane_rm.timewarp.HistoricalMT5Adapter(
            kwargs["sources"],
            require_successor_witness=True,
        )
        adapter.set_replay_context(symbol="EURUSD", asof=asof)
        for timeframe in lane_rm.RAW_CAMPAIGN_DECISION_TIMEFRAMES:
            selected = adapter.get_candles(
                "EURUSD",
                lane_rm.timewarp.LIVE_TF_MAP[timeframe],
                20,
            )
            assert selected
            assert all("wave21_completed_bar_witness" in row for row in selected)
        return native_result

    monkeypatch.setattr(lane_rm.timewarp, "run_campaign", fake_run_campaign)
    assert inputs.run_raw_campaign(campaign=campaign, config=config) is native_result
    assert lane_rm.timewarp.closed_bar_rows_until is original_selector
    assert (
        lane_rm.timewarp.observed_successor_closed_bar_rows_until
        is original_observed_selector
    )
    assert Path.cwd() == original_cwd

    with pytest.raises(
        lane_rm.LaneRematerializationError,
        match="truth_mode_required",
    ):
        inputs.run_raw_campaign(campaign=campaign, config={})
    with pytest.raises(
        lane_rm.LaneRematerializationError,
        match="candidate_cap_refused",
    ):
        inputs.run_raw_campaign(
            campaign=replace(
                campaign,
                max_candidates_per_symbol_window=1,
            ),
            config=config,
        )
    with pytest.raises(
        lane_rm.LaneRematerializationError,
        match="smoke_refused",
    ):
        inputs.run_raw_campaign(
            campaign=replace(campaign, run_smoke_subset=True),
            config=config,
        )


def test_registry_authorizes_val_lane_and_keeps_authority_paths_relative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lane_rm, "REPO_ROOT", tmp_path)
    _manifest_path, manifest = _manifest(tmp_path)
    registry_path = _registry(tmp_path, manifest)
    inputs = lane_rm.LaneInputRegistry(registry_path).resolve(
        window_id="january_2026", purpose=guard.PURPOSE_LANE_ITERATION
    )
    assert inputs.window_start == "2026-01-01"
    assert inputs.entry["surface"] == "VAL"
    assert not Path(inputs.entry["source_manifest"]).is_absolute()
    assert inputs.input_authority()["campaign_sealed"] is False


def test_registry_can_reference_a_foreign_worktree_read_only(
    tmp_path: Path,
) -> None:
    origin = tmp_path / "origin-worktree"
    lane_root = origin / ".hermes/evidence/phase16/cj-rematerialization/LANE"
    manifest_core = {
        "schema": lane_rm.SOURCE_SCHEMA,
        "campaign_sealed": False,
        "window_id": "january_2026",
        "lane_root_repo_relpath": lane_root.relative_to(origin).as_posix(),
        "bar_sources": [],
        "tick_sources": [],
        "tick_gaps": [],
    }
    manifest = {
        **manifest_core,
        "manifest_root_sha256": lane_rm._stable_sha256(manifest_core),
    }
    _write_json(lane_root / "manifests/january_2026.json", manifest)
    registry = _registry(lane_root, manifest)
    inputs = lane_rm.LaneInputRegistry(registry).resolve(
        window_id="january_2026", purpose=guard.PURPOSE_LANE_ITERATION
    )
    authority = inputs.input_authority()
    assert inputs.logical_repo_root == origin.resolve()
    assert authority["registry_access"] == "read_only"
    assert authority["registry_absolute_machine_local"] == str(registry.resolve())


def test_source_plan_override_is_in_memory_and_conflict_checked(tmp_path: Path) -> None:
    inputs = lane_rm.LaneWindowInputs(
        registry_path=tmp_path / "registry.json",
        registry={"registry_root_sha256": "c" * 64},
        window_id="february_2026",
        window=lane_rm.WINDOWS["february_2026"],
        entry={},
        source_manifest_path=tmp_path / "manifest.json",
        source_manifest={"manifest_root_sha256": "a" * 64},
        pack_root=tmp_path / "packs",
        pack_roots={},
        contract=tmp_path / "contract.json",
    )
    overridden = inputs.with_canonical_source_plan_digest("b" * 64)
    assert overridden.entry["canonical_source_plan_digest_sha256"] == "b" * 64
    assert "canonical_source_plan_digest_sha256" not in inputs.entry
    with pytest.raises(lane_rm.LaneRematerializationError, match="override_drift"):
        overridden.with_canonical_source_plan_digest("c" * 64)


def test_lane_prefix_is_read_only_filters_packs_and_requires_a_new_plan(
    tmp_path: Path,
) -> None:
    window = lane_rm.WINDOWS["may_2026"]
    roots = {
        (window.split, day, day): str(index).zfill(64)
        for index, day in enumerate(window.days, start=1)
    }
    inputs = lane_rm.LaneWindowInputs(
        registry_path=tmp_path / "registry.json",
        registry={"registry_root_sha256": "c" * 64},
        window_id=window.window_id,
        window=window,
        entry={
            "window": [window.start, window.end],
            "canonical_source_plan_digest_sha256": "a" * 64,
        },
        source_manifest_path=tmp_path / "manifest.json",
        source_manifest={"manifest_root_sha256": "b" * 64},
        pack_root=tmp_path / "packs",
        pack_roots=roots,
        contract=tmp_path / "contract.json",
        logical_repo_root=tmp_path,
    )
    bounded = inputs.for_prefix("2026-05-30")
    assert bounded.window_end == "2026-05-30"
    assert len(bounded.pack_roots) == 30
    assert "canonical_source_plan_digest_sha256" not in bounded.entry
    assert inputs.window_end == "2026-05-31"
    assert len(inputs.pack_roots) == 31
    assert inputs.entry["canonical_source_plan_digest_sha256"] == "a" * 64
    authority = bounded.input_authority()
    assert authority["window"] == ["2026-05-01", "2026-05-30"]
    assert authority["registered_window"] == ["2026-05-01", "2026-05-31"]
    assert authority["prefix_bounded"] is True
    with pytest.raises(lane_rm.LaneRematerializationError, match="out_of_range"):
        inputs.for_prefix("2026-06-01")


def test_empty_lane_tick_manifest_is_authoritative_without_repo_scan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_scan(*_args, **_kwargs):
        raise AssertionError("retired repo tick scan entered")

    monkeypatch.setattr(
        lane_rm.attempt5,
        "resolve_ftmo_tick_source",
        forbidden_scan,
    )
    resolver = lane_rm.LaneBroadSourceResolver(
        bound_tick_source_specs={},
        bound_tick_source_gaps={},
        bound_tick_logical_repo_root=tmp_path,
        sealed_tick_full_component_set=False,
    )
    assert resolver.sealed_tick_full_component_set is True
    assert resolver.resolve_tick(
        "EURUSD",
        source_authority_days=("2026-05-01", "2026-05-30"),
    ) is None


def test_prefix_pack_rebind_accepts_only_measured_source_root_delta() -> None:
    registered_root = "a" * 64
    effective_root = "b" * 64
    pack_root = "c" * 64
    manifest_root = "d" * 64
    plan_digest = "e" * 64
    core = {
        "schema": "gtos.lane.rematerialization.prefix_pack_source_rebind.v1",
        "status": "VERIFIED_PREFIX_PACK_SOURCE_IDENTITY_REBIND",
        "window_id": "may_2026",
        "registered_window": ["2026-05-01", "2026-05-31"],
        "effective_window": ["2026-05-01", "2026-05-30"],
        "registered_source_identity_root_sha256": registered_root,
        "effective_source_identity_root_sha256": effective_root,
        "source_manifest_root_sha256": manifest_root,
        "effective_source_plan_digest_sha256": plan_digest,
        "retained_pack_count": 30,
        "allowed_binding_difference": ["source_identity_root_sha256"],
        "source_manifest_unchanged": True,
        "retained_daily_pack_roots_are_exact_registry_subset": True,
        "pack_contents_remain_authenticated_per_reader_before_use": True,
        "economic_outcomes_read": False,
        "march_outcomes_read": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    proof = {**core, "authority_root_sha256": lane_rm._stable_sha256(core)}

    class Reader:
        bindings = {
            "days": ["2026-05-15"],
            "source_identity_root_sha256": registered_root,
        }
        external_root_authenticated = True
        pack_root_sha256 = pack_root

    differences = {
        "source_identity_root_sha256": {
            "pack": registered_root,
            "runtime": effective_root,
        }
    }
    assert lane_rm._prefix_pack_binding_rebind_allowed(
        differences=differences,
        proof=proof,
        reader=Reader(),
        days=["2026-05-15"],
        runtime_source_root=effective_root,
        expected_pack_root=pack_root,
        expected_window_id="may_2026",
        expected_effective_window=("2026-05-01", "2026-05-30"),
        expected_source_manifest_root=manifest_root,
        expected_source_plan_digest=plan_digest,
        expected_pack_count=30,
    )
    assert not lane_rm._prefix_pack_binding_rebind_allowed(
        differences={**differences, "symbols": {"pack": [], "runtime": ["x"]}},
        proof=proof,
        reader=Reader(),
        days=["2026-05-15"],
        runtime_source_root=effective_root,
        expected_pack_root=pack_root,
        expected_window_id="may_2026",
        expected_effective_window=("2026-05-01", "2026-05-30"),
        expected_source_manifest_root=manifest_root,
        expected_source_plan_digest=plan_digest,
        expected_pack_count=30,
    )
    tampered = {**proof, "effective_window": ["2026-05-01", "2026-05-31"]}
    assert not lane_rm._prefix_pack_binding_rebind_allowed(
        differences=differences,
        proof=tampered,
        reader=Reader(),
        days=["2026-05-15"],
        runtime_source_root=effective_root,
        expected_pack_root=pack_root,
        expected_window_id="may_2026",
        expected_effective_window=("2026-05-01", "2026-05-30"),
        expected_source_manifest_root=manifest_root,
        expected_source_plan_digest=plan_digest,
        expected_pack_count=30,
    )


def test_runtime_bindings_scope_relative_tick_paths_to_logical_repo_and_restore(
    tmp_path: Path,
) -> None:
    logical_root = tmp_path / "origin-worktree"
    logical_root.mkdir()
    inputs = lane_rm.LaneWindowInputs(
        registry_path=logical_root / "registry.json",
        registry={},
        window_id="february_2026",
        window=lane_rm.WINDOWS["february_2026"],
        entry={},
        source_manifest_path=logical_root / "manifest.json",
        source_manifest={"manifest_root_sha256": "a" * 64},
        pack_root=logical_root / "packs",
        pack_roots={},
        contract=logical_root / "contract.json",
        logical_repo_root=logical_root,
    )
    caller_cwd = Path.cwd()
    with inputs.runtime_bindings():
        assert Path.cwd() == logical_root.resolve()
    assert Path.cwd() == caller_cwd


def test_registry_refuses_non_lane_purpose_before_resolving_inputs(tmp_path: Path) -> None:
    _manifest_path, manifest = _manifest(tmp_path)
    registry_path = _registry(tmp_path, manifest)
    # January is SEALED on the fitting-role axis, so TRAINING must refuse even
    # though the independent surface axis labels it VAL.
    with pytest.raises(guard.WindowRefused):
        lane_rm.LaneInputRegistry(registry_path).resolve(
            window_id="january_2026", purpose=guard.PURPOSE_TRAINING
        )


def test_registry_binds_one_canonical_source_plan_without_sealed_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lane_rm, "REPO_ROOT", tmp_path)
    _manifest_path, manifest = _manifest(tmp_path)
    registry_path = _registry(tmp_path, manifest)
    digest = "a" * 64
    updated = lane_rm._register_source_plan_digest(
        registry_path, window_id="january_2026", digest=digest
    )
    assert updated["windows"]["january_2026"][
        "canonical_source_plan_digest_sha256"
    ] == digest
    inputs = lane_rm.LaneInputRegistry(registry_path).resolve(
        window_id="january_2026", purpose=guard.PURPOSE_LANE_ITERATION
    )
    assert inputs.accelerator().authority()["source_plan_digest_sha256"] == digest
    with pytest.raises(lane_rm.LaneRematerializationError, match="digest_drift"):
        lane_rm._register_source_plan_digest(
            registry_path, window_id="january_2026", digest="b" * 64
        )


def test_pack_successor_registration_repoints_only_to_repo_relative_root(
    tmp_path: Path,
) -> None:
    _manifest_path, manifest = _manifest(tmp_path)
    registry_path = _registry(tmp_path, manifest)
    successor = tmp_path / "packs/january_2026_authority_v2"
    updated = lane_rm._register_pack_roots(
        registry_path,
        window_id="january_2026",
        pack_roots={"development:2026-01-01:2026-01-01": "a" * 64},
        pack_root=successor,
    )
    assert updated["windows"]["january_2026"]["pack_root"] == (
        "packs/january_2026_authority_v2"
    )
    with pytest.raises(ValueError):
        lane_rm._register_pack_roots(
            registry_path,
            window_id="january_2026",
            pack_roots={},
            pack_root=tmp_path.parent / "escape",
        )


def test_safe_relative_refuses_absolute_and_parent_escape(tmp_path: Path) -> None:
    with pytest.raises(lane_rm.LaneRematerializationError, match="non_relocatable"):
        lane_rm._safe_relative(tmp_path, "/absolute/file")
    with pytest.raises(lane_rm.LaneRematerializationError, match="non_relocatable"):
        lane_rm._safe_relative(tmp_path, "../escape")


def test_lane_runtime_prefix_uses_b7_only_inside_argument_shell() -> None:
    assert (
        lane_rm._lane_argument_shell_prefix("CJ_RECLOCKED_S0R0", "S0R0")
        == "CJ_LANE_ARGUMENT_SHELL_B7_5_S0R0"
    )
    with pytest.raises(lane_rm.LaneRematerializationError, match="omit_historical"):
        lane_rm._lane_argument_shell_prefix("CJ_B7_5_FALSE_CLAIM", "S0R0")


def test_lane_fingerprint_args_do_not_require_runtime_prelude(tmp_path: Path) -> None:
    inputs = lane_rm.LaneWindowInputs(
        registry_path=tmp_path / "registry.json",
        registry={},
        window_id="january_2026",
        window=lane_rm.WINDOWS["january_2026"],
        entry={},
        source_manifest_path=tmp_path / "manifest.json",
        source_manifest={},
        pack_root=tmp_path / "packs",
        pack_roots={},
        contract=tmp_path / "R2.json",
    )
    args = inputs.fingerprint_args(arm_id="S0R0", stop_after_day=None)
    assert args.arm_id == "S0R0"
    assert args.engineering_stop_after_day is None
    assert args.expected_shared_execution_contract_sha256 is None
    assert args.decision_contract == tmp_path / "R2.json"


def test_true_utc_edge_fragment_rebind_requires_complete_enclosing_broker_day() -> None:
    def rows(stamp: str, count: int) -> tuple[dict, ...]:
        return tuple({"time": stamp, "close": 1.0} for _ in range(count))

    m1_jan1 = rows("2026-01-01T22:05:00+00:00", 90)
    m1_jan2 = rows("2026-01-02T10:00:00+00:00", 910)
    m15_jan1 = rows("2026-01-01T22:00:00+00:00", 8)
    m15_jan2 = rows("2026-01-02T10:00:00+00:00", 88)
    fragment_authority = lane_rm.timewarp.m1_symbol_day_source_authority(
        symbol="EURUSD",
        trading_day="2026-01-01",
        m1_row_count=len(m1_jan1),
        m15_row_count=len(m15_jan1),
    )
    assert fragment_authority["diagnostic_fallback_only"] is True
    spec = lane_rm.timewarp.SourceSpec(
        symbol="EURUSD",
        mapped_symbol="EURUSD",
        timeframe="M1",
        path=Path("lane/EURUSD_M1.csv"),
        source_family="bridge_ftmo_m1_202601",
        source_broker="FTMO",
        source_role="owner_authorized_research_hydration",
    )
    source = lane_rm.timewarp.ResolvedSource(
        spec=spec,
        rows=(*m1_jan1, *m1_jan2),
        rows_by_day={"2026-01-01": m1_jan1, "2026-01-02": m1_jan2},
        sha256="1" * 64,
        day_counts={"2026-01-01": 90, "2026-01-02": 910},
        selected_status="selected_composite_m1_days_with_symbol_day_scoped_gaps",
        min_required_rows_per_day=1000,
        day_source_authority={"2026-01-01": fragment_authority},
    )
    m15_source = lane_rm.timewarp.ResolvedSource(
        spec=replace(spec, timeframe="M15", path=Path("lane/EURUSD_M15.csv")),
        rows=(*m15_jan1, *m15_jan2),
        rows_by_day={"2026-01-01": m15_jan1, "2026-01-02": m15_jan2},
        sha256="2" * 64,
        day_counts={"2026-01-01": 8, "2026-01-02": 88},
        selected_status="selected_source_meets_floor",
        min_required_rows_per_day=0,
    )
    rebound, receipt_rows = lane_rm._rebind_complete_broker_day_fragments(
        source, m15_source=m15_source
    )
    authority = rebound.day_source_authority["2026-01-01"]
    assert authority["diagnostic_fallback_only"] is False
    assert authority["lane_enclosing_broker_day"] == "2026-01-02"
    assert authority["lane_enclosing_broker_day_m1_row_count"] == 1000
    assert authority["lane_enclosing_broker_day_m15_row_count"] == 96
    assert receipt_rows[0]["rows_added_or_synthesized"] == 0
    assert authority["source_day_authority_hash_sha256"] != fragment_authority[
        "source_day_authority_hash_sha256"
    ]

    incomplete = replace(source, rows=source.rows[:500])
    unchanged, no_receipt_rows = lane_rm._rebind_complete_broker_day_fragments(
        incomplete, m15_source=m15_source
    )
    assert unchanged.day_source_authority["2026-01-01"][
        "diagnostic_fallback_only"
    ] is True
    assert no_receipt_rows == ()


def test_true_utc_midwindow_sunday_fragment_uses_the_same_broker_day_proof() -> None:
    def rows(stamp: str, count: int) -> tuple[dict, ...]:
        return tuple({"time": stamp, "close": 1.0} for _ in range(count))

    m1_prior = rows("2026-05-15T10:00:00+00:00", 1000)
    m1_fragment = rows("2026-05-17T21:05:00+00:00", 90)
    m1_follow = rows("2026-05-18T10:00:00+00:00", 910)
    m15_prior = rows("2026-05-15T10:00:00+00:00", 96)
    m15_fragment = rows("2026-05-17T21:00:00+00:00", 8)
    m15_follow = rows("2026-05-18T10:00:00+00:00", 88)
    prior_authority = lane_rm.timewarp.m1_symbol_day_source_authority(
        symbol="USDCHF",
        trading_day="2026-05-15",
        m1_row_count=len(m1_prior),
        m15_row_count=len(m15_prior),
    )
    fragment_authority = lane_rm.timewarp.m1_symbol_day_source_authority(
        symbol="USDCHF",
        trading_day="2026-05-17",
        m1_row_count=len(m1_fragment),
        m15_row_count=len(m15_fragment),
    )
    assert prior_authority["diagnostic_fallback_only"] is False
    assert fragment_authority["diagnostic_fallback_only"] is True
    spec = lane_rm.timewarp.SourceSpec(
        symbol="USDCHF",
        mapped_symbol="USDCHF",
        timeframe="M1",
        path=Path("lane/USDCHF_M1.csv"),
        source_family="bridge_ftmo_m1_202601",
        source_broker="FTMO",
        source_role="owner_authorized_research_hydration",
    )
    source = lane_rm.timewarp.ResolvedSource(
        spec=spec,
        rows=(*m1_prior, *m1_fragment, *m1_follow),
        rows_by_day={
            "2026-05-15": m1_prior,
            "2026-05-17": m1_fragment,
            "2026-05-18": m1_follow,
        },
        sha256="3" * 64,
        day_counts={"2026-05-15": 1000, "2026-05-17": 90, "2026-05-18": 910},
        selected_status="selected_composite_m1_days_with_symbol_day_scoped_gaps",
        min_required_rows_per_day=1000,
        day_source_authority={
            "2026-05-15": prior_authority,
            "2026-05-17": fragment_authority,
        },
    )
    m15_source = lane_rm.timewarp.ResolvedSource(
        spec=replace(spec, timeframe="M15", path=Path("lane/USDCHF_M15.csv")),
        rows=(*m15_prior, *m15_fragment, *m15_follow),
        rows_by_day={
            "2026-05-15": m15_prior,
            "2026-05-17": m15_fragment,
            "2026-05-18": m15_follow,
        },
        sha256="4" * 64,
        day_counts={"2026-05-15": 96, "2026-05-17": 8, "2026-05-18": 88},
        selected_status="selected_source_meets_floor",
        min_required_rows_per_day=0,
    )
    rebound, receipt_rows = lane_rm._rebind_complete_broker_day_fragments(
        source, m15_source=m15_source
    )
    assert rebound.day_source_authority["2026-05-15"] == prior_authority
    repaired = rebound.day_source_authority["2026-05-17"]
    assert repaired["diagnostic_fallback_only"] is False
    assert repaired["lane_enclosing_broker_day"] == "2026-05-18"
    assert repaired["lane_enclosing_broker_day_m1_row_count"] == 1000
    assert repaired["lane_enclosing_broker_day_m15_row_count"] == 96
    assert receipt_rows[0]["utc_fragment_day"] == "2026-05-17"
    assert receipt_rows[0]["rows_added_or_synthesized"] == 0


def test_lane_chunk_resolver_uses_full_authority_scope_for_m1_invariance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[tuple[str, ...], tuple[str, ...]]] = []

    def fake_build(
        _self: object,
        days: tuple[str, ...],
        *,
        symbols: tuple[str, ...] | None = None,
        source_authority_days: tuple[str, ...] | None = None,
    ) -> dict:
        del symbols
        calls.append((days, tuple(source_authority_days or ())))
        return {}

    monkeypatch.setattr(
        lane_rm.attempt5.BroadSourceResolver,
        "build_sources_for_days",
        fake_build,
    )
    resolver = object.__new__(lane_rm.LaneBroadSourceResolver)
    authority_days = ("2026-01-01", "2026-01-02")
    resolver.build_sources_for_days(
        ("2026-01-01",),
        symbols=("EURUSD",),
        source_authority_days=authority_days,
    )
    assert calls == [(authority_days, authority_days)]


def test_clock_feature_census_and_hour_token_shift_are_physical() -> None:
    record = {
        "decision_time_utc": "2026-01-02T02:15:00+00:00",
        "symbols": [
            {
                "candidates": [
                    {
                        "candidate_instance_time_utc": "2026-01-02T02:15:00Z",
                        "utc_hour_bucket": "h02_03",
                        "session": "moonshot_h02_03",
                        "session_bucket": "tokyo",
                        "kill_zone": "tokyo",
                    }
                ]
            }
        ],
    }
    census = lane_rm._clock_feature_census(record)
    assert census["timestamps"] == [
        "2026-01-02T02:15:00+00:00",
        "2026-01-02T02:15:00Z",
    ]
    assert census["utc_hour_bucket"] == ["h02_03"]
    assert census["session"] == ["moonshot_h02_03"]
    assert lane_rm._shift_hour_token("h02_03") == "h00_01"
    assert lane_rm._shift_hour_token("moonshot_h00_01") == "moonshot_h22_23"
    assert lane_rm._shift_hour_token("tokyo") is None


def test_arm_invariance_receipt_declares_strict_and_material_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lane_rm, "REPO_ROOT", tmp_path)
    report = {
        "arm": "S0R0",
        "purpose": guard.PURPOSE_LANE_ITERATION,
        "stop_after_day": None,
        "error": None,
        "economics_counts": {"trade": 1, "order": 2, "scorecard": 3},
        "receipt_counts": {"candidate_rows": 10},
        "missed_digest": {"rows": 9},
        "lane_input_authority": {"campaign_sealed": False},
    }
    pool = {
        "diagnostic_scoreable_rows": 8,
        "net_r": -4.0,
        "mean_r_per_row": -0.5,
        "gross": {"mean_gross_r": -0.2},
        "cost": {
            "mean_cost_r": 0.3,
            "components_mean_r": {
                "commission_r": 0.05,
                "spread_r": 0.2,
                "expected_slippage_r": 0.02,
                "swap_cost_r": 0.03,
            },
        },
        "n_days_negative": 1,
        "n_days": 1,
    }
    paths = {
        "baseline_report": tmp_path / "baseline/report.json",
        "candidate_report": tmp_path / "candidate/report.json",
        "baseline_pool": tmp_path / "baseline/pool.json",
        "candidate_pool": tmp_path / "candidate/pool.json",
    }
    _write_json(paths["baseline_report"], report)
    _write_json(paths["candidate_report"], report)
    _write_json(paths["baseline_pool"], pool)
    _write_json(paths["candidate_pool"], pool)
    receipt = lane_rm.compare_january_arm_economics(
        candidate_report_path=paths["candidate_report"],
        candidate_pool_summary_path=paths["candidate_pool"],
        baseline_report_path=paths["baseline_report"],
        baseline_pool_summary_path=paths["baseline_pool"],
    )
    assert receipt["status"] == "JANUARY_RECLOCKED_ECONOMICS_INVARIANT"
    assert receipt["strict_invariant"] is True

    moved_report = dict(report)
    moved_report["economics_counts"] = {"trade": 2, "order": 2, "scorecard": 3}
    moved_pool = dict(pool)
    moved_pool["mean_r_per_row"] = -0.52
    _write_json(paths["candidate_report"], moved_report)
    _write_json(paths["candidate_pool"], moved_pool)
    moved = lane_rm.compare_january_arm_economics(
        candidate_report_path=paths["candidate_report"],
        candidate_pool_summary_path=paths["candidate_pool"],
        baseline_report_path=paths["baseline_report"],
        baseline_pool_summary_path=paths["baseline_pool"],
    )
    assert moved["status"] == "JANUARY_RECLOCKED_ECONOMICS_MOVED_MATERIALLY"
    assert "trade_count_changed" in moved["material_movement_reasons"]


def test_arm_invariance_receipt_compares_realized_physical_net_r(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lane_rm, "REPO_ROOT", tmp_path)
    report = {
        "arm": "S0R0",
        "purpose": guard.PURPOSE_LANE_ITERATION,
        "stop_after_day": None,
        "error": None,
        "economics_counts": {"trade": 1, "order": 2, "scorecard": 3},
        "receipt_counts": {"candidate_rows": 10},
        "missed_digest": {"rows": 9},
        "lane_input_authority": {"campaign_sealed": False},
    }
    pool = {
        "diagnostic_scoreable_rows": 8,
        "net_r": -4.0,
        "mean_r_per_row": -0.5,
        "gross": {"mean_gross_r": -0.2},
        "cost": {
            "mean_cost_r": 0.3,
            "components_mean_r": {
                "commission_r": 0.05,
                "spread_r": 0.2,
                "expected_slippage_r": 0.02,
                "swap_cost_r": 0.03,
            },
        },
        "n_days_negative": 1,
        "n_days": 1,
    }
    paths = {
        "baseline_report": tmp_path / "baseline/report.json",
        "candidate_report": tmp_path / "candidate/report.json",
        "baseline_pool": tmp_path / "baseline/pool.json",
        "candidate_pool": tmp_path / "candidate/pool.json",
        "baseline_economics": tmp_path / "baseline/economics.json",
        "candidate_economics": tmp_path / "candidate/economics.json",
    }
    for key in ("baseline_report", "candidate_report"):
        _write_json(paths[key], report)
    for key in ("baseline_pool", "candidate_pool"):
        _write_json(paths[key], pool)
    _write_json(
        paths["baseline_economics"],
        {
            "counts": report["economics_counts"],
            "summary_economics": {
                "split_profile_stats[0].physical_net_r": -2.0
            },
        },
    )
    _write_json(
        paths["candidate_economics"],
        {
            "counts": report["economics_counts"],
            "summary_economics": {
                "split_profile_stats[0].physical_net_r": -1.5
            },
        },
    )
    receipt = lane_rm.compare_january_arm_economics(
        candidate_report_path=paths["candidate_report"],
        candidate_pool_summary_path=paths["candidate_pool"],
        baseline_report_path=paths["baseline_report"],
        baseline_pool_summary_path=paths["baseline_pool"],
        baseline_economics_authority_path=paths["baseline_economics"],
        candidate_economics_authority_path=paths["candidate_economics"],
    )
    assert receipt["strict_invariant"] is False
    assert receipt["numeric_deltas"]["physical_net_r"] == 0.5
    assert receipt["status"] == "JANUARY_RECLOCKED_ECONOMICS_MOVED_BELOW_MATERIALITY"


def test_capture_baseline_economics_cross_checks_machine_local_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lane_rm, "REPO_ROOT", tmp_path)
    counts = {"trade": 2, "order": 4, "scorecard": 6, "missed": 8}
    missed = {"rows": 8, "diagnostic_scoreable_rows": 3}
    summary = {"split_profile_stats[0].physical_net_r": -1.25}
    fingerprint = {"arm_id": "S0R0", "window": ["2026-01-01", "2026-01-31"]}
    report = {
        "arm": "S0R0",
        "error": None,
        "stop_after_day": None,
        "output_prefix": "CD_BASELINE",
        "economics_counts": counts,
        "missed_digest": missed,
        "fingerprint": fingerprint,
    }
    lane_receipt = {
        "counts": counts,
        "missed_opportunity_pool": missed,
        "summary_economics": summary,
        "fingerprint": fingerprint,
    }
    full_economics = {
        "output_prefix": "CD_BASELINE",
        "counts": counts,
        "missed_digest": missed,
        "summary_economics": summary,
    }
    report_path = tmp_path / "report.json"
    lane_path = tmp_path / "lane.json"
    economics_path = tmp_path / "economics.json"
    _write_json(report_path, report)
    _write_json(lane_path, lane_receipt)
    _write_json(economics_path, full_economics)
    receipt = lane_rm.capture_baseline_economics_authority(
        committed_report_path=report_path,
        lane_receipt_path=lane_path,
        full_economics_path=economics_path,
    )
    assert receipt["status"] == "BASELINE_ECONOMICS_AUTHORITY_PRESERVED"
    assert receipt["summary_economics"] == summary
    assert receipt["cross_checks"]["fingerprint_matches_committed_report"] is True
