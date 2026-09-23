from __future__ import annotations

import json
from argparse import Namespace
from datetime import datetime, timezone

import pytest

import scripts.export_mt5_research_ticks as tick_export
from scripts.export_mt5_research_ticks import _read_existing_ticks_jsonl_stats
from scripts.export_mt5_research_ohlcv import (
    default_symbol_specs_for_args,
    parse_symbol_specs,
)


def test_ftmo_default_symbol_specs_match_replay_resolver_aliases() -> None:
    specs = parse_symbol_specs(
        default_symbol_specs_for_args(Namespace(source_broker="FTMO"))
    )
    mapping = {spec.file_symbol: spec.mt5_symbol for spec in specs}

    assert mapping["GER40"] == "GER40.cash"
    assert mapping["NAS100"] == "US100.cash"
    assert mapping["US30_cash"] == "US30.cash"
    assert mapping["SPX500"] == "US500.cash"
    assert mapping["USOIL_cash"] == "USOIL.cash"
    assert mapping["UKOIL_cash"] == "UKOIL.cash"
    assert len(mapping) == 24


def test_non_ftmo_default_symbol_specs_preserve_legacy_aliases() -> None:
    specs = parse_symbol_specs(
        default_symbol_specs_for_args(Namespace(source_broker="redacted_account"))
    )
    mapping = {spec.file_symbol: spec.mt5_symbol for spec in specs}

    assert mapping["NAS100"] == "NDX100"
    assert mapping["US30_cash"] == "US30"


def test_tick_export_reuse_existing_stats_filters_requested_window(tmp_path) -> None:
    path = tmp_path / "ticks.jsonl"
    rows = [
        {"ts_utc": "2026-05-12T23:59:59+00:00", "bid": 1.0},
        {"ts_utc": "2026-05-13T00:00:00+00:00", "bid": 1.1},
        {"ts_utc": "2026-05-13T00:00:01+00:00", "bid": 1.2},
        {"ts_utc": "2026-05-14T00:00:00+00:00", "bid": 1.3},
    ]
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    stats = _read_existing_ticks_jsonl_stats(
        path,
        start=datetime(2026, 5, 13, tzinfo=timezone.utc),
        end=datetime(2026, 5, 14, tzinfo=timezone.utc),
    )

    assert stats == {
        "rows": 2,
        "first": "2026-05-13T00:00:00+00:00",
        "last": "2026-05-13T00:00:01+00:00",
    }


def test_tick_export_owner_override_scope_rejects_before_mt5_initialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_initialized(_args: Namespace) -> object:
        raise AssertionError("MT5 initialized before provenance validation")

    monkeypatch.setattr(tick_export, "initialize_mt5_client", fail_if_initialized)

    with pytest.raises(RuntimeError, match="ordered_price_path_only_not_broker"):
        tick_export.main(
            [
                "--window",
                "hostile5d:2026-05-13T00:00:00+00:00,2026-05-18T02:00:00+00:00",
                "--source-broker",
                "FTMO",
                "--source-role",
                "owner_authorized_path_override",
                "--replaces-missing-frozen-path-source",
                "--not-redacted_account-native",
                "--source-truth-scope",
                "ordered_price_path_ticks_not_broker_lifecycle_truth",
                "--require-owner-authorized-path-override",
            ]
        )
