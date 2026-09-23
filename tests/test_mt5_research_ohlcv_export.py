from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.utils.broker_clock import fixed_offset_rule
from scripts.export_mt5_research_ohlcv import (
    ORDERED_PATH_OVERRIDE_SCOPE,
    SymbolSpec,
    _copy_rates_range_chunked,
    enrich_export_result_for_manifest,
    export_research_ohlcv,
)
from scripts.export_mt5_research_ticks import (
    enrich_tick_export_result_for_manifest,
    export_research_ticks,
)
from scripts.inspect_mt5_tick_availability import parse_windows


def test_export_manifest_enrichment_adds_v4u_source_capture_fields(tmp_path: Path) -> None:
    output_dir = tmp_path / "data" / "mt5_research_exports" / "v4u_ftmo_ltf_req"
    start = datetime(2026, 6, 2, 13, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 2, 13, 3, tzinfo=timezone.utc)
    export_result = export_research_ohlcv(
        mt5_module=FakeMT5(),
        specs=[SymbolSpec(file_symbol="NAS100", mt5_symbol="NDX100")],
        timeframe_names=["M1"],
        start=start,
        end=end,
        output_dir=output_dir,
        clock=fixed_offset_rule(0, evidence="test fixture: bars are already true UTC, so a declared zero-offset clock keeps this test about chunking/manifest rather than the clock"),
    )
    provenance = {
        "source_broker": "FTMO",
        "source_role": "owner_authorized_path_override",
        "replaces_missing_frozen_path_source": True,
        "not_redacted_account_native": True,
        "source_truth_scope": ORDERED_PATH_OVERRIDE_SCOPE,
        "handoff_requirement_id": "v4u_ltf_req",
        "broker_lifecycle_truth_satisfied": False,
        "asof_decision_truth_satisfied": False,
    }
    manifest_path = output_dir / "manifest.json"

    enriched = enrich_export_result_for_manifest(
        export_result=export_result,
        account=FakeAccount(),
        provenance=provenance,
        start=start,
        end=end,
        manifest_path=manifest_path,
        clock=fixed_offset_rule(0, evidence="test fixture: bars are already true UTC, so a declared zero-offset clock keeps this test about chunking/manifest rather than the clock"),
    )

    file_payload = enriched["files"]["NAS100_M1"]
    assert file_payload["row_count"] == 3
    assert len(file_payload["sha256"]) == 64
    assert file_payload["source_server_redacted"] == "redacted:FT...mo"
    assert len(file_payload["source_server_hash"]) == 64
    assert file_payload["source_account_redacted"] == "redacted:12...56"
    assert len(file_payload["source_account_hash"]) == 64
    assert "source_server" not in file_payload
    assert "source_account_login" not in file_payload
    assert file_payload["source_broker"] == "FTMO"
    assert file_payload["source_role"] == "owner_authorized_path_override"
    assert file_payload["source_truth_scope"] == ORDERED_PATH_OVERRIDE_SCOPE
    assert file_payload["replaces_missing_frozen_path_source"] is True
    assert file_payload["not_redacted_account_native"] is True
    assert file_payload["broker_lifecycle_truth_satisfied"] is False
    assert file_payload["asof_decision_truth_satisfied"] is False
    assert file_payload["export_tool"] == "scripts/export_mt5_research_ohlcv.py"
    assert file_payload["manifest_path"] == str(manifest_path)


def test_ohlcv_final_window_refresh_prefers_newer_complete_history() -> None:
    class RefreshingMT5:
        def __init__(self) -> None:
            self.calls = 0

        def copy_rates_range(self, _symbol, _timeframe, _start, _end):
            self.calls += 1
            rows = [
                _rate("2026-06-18T00:00:00+00:00", 100.0, 101.0, 99.0, 100.5)
            ]
            if self.calls >= 2:
                rows.append(
                    _rate("2026-06-19T00:00:00+00:00", 100.5, 102.0, 100.0, 101.5)
                )
            return rows

        def last_error(self):
            return (1, "Success")

    mt5 = RefreshingMT5()
    rows, stats = _copy_rates_range_chunked(
        mt5_module=mt5,
        symbol="XAUUSD",
        timeframe=1,
        start=datetime(2026, 6, 18, tzinfo=timezone.utc),
        end=datetime(2026, 6, 20, tzinfo=timezone.utc),
        chunk=None,
        history_refresh_retries=2,
        history_refresh_delay_seconds=0.0,
    )

    assert rows is not None
    assert len(rows) == 2
    assert stats["history_refresh_attempts"] == 2
    assert stats["history_refresh_improvements"] == 1
    assert stats["raw_rows_returned"] == 2


def test_tick_export_manifest_enrichment_adds_v4u_source_capture_fields(tmp_path: Path) -> None:
    output_dir = tmp_path / "data" / "mt5_research_exports" / "v4u_ftmo_ltf_req"
    windows = parse_windows(["v4u_ltf_req:2026-06-02T13:00:00Z,2026-06-02T13:02:00Z"])
    export_result = export_research_ticks(
        mt5_module=FakeTickMT5(),
        specs=[SymbolSpec(file_symbol="NAS100", mt5_symbol="NDX100")],
        windows=windows,
        output_dir=output_dir,
        copy_ticks_flag=FakeTickMT5.COPY_TICKS_ALL,
    )
    provenance = {
        "source_broker": "FTMO",
        "source_role": "owner_authorized_path_override",
        "replaces_missing_frozen_path_source": True,
        "not_redacted_account_native": True,
        "source_truth_scope": ORDERED_PATH_OVERRIDE_SCOPE,
        "handoff_requirement_id": "v4u_ltf_req",
        "broker_lifecycle_truth_satisfied": False,
        "asof_decision_truth_satisfied": False,
    }
    manifest_path = output_dir / "manifest.json"

    enriched = enrich_tick_export_result_for_manifest(
        export_result=export_result,
        account=FakeAccount(),
        provenance=provenance,
        manifest_path=manifest_path,
    )

    file_payload = enriched["files"]["NAS100_v4u_ltf_req_TICK"]
    assert file_payload["row_count"] == 2
    assert len(file_payload["sha256"]) == 64
    assert file_payload["timeframe"] == "TICK"
    assert file_payload["source_server_redacted"] == "redacted:FT...mo"
    assert len(file_payload["source_server_hash"]) == 64
    assert file_payload["source_account_redacted"] == "redacted:12...56"
    assert len(file_payload["source_account_hash"]) == 64
    assert "source_server" not in file_payload
    assert "source_account_login" not in file_payload
    assert file_payload["source_broker"] == "FTMO"
    assert file_payload["not_redacted_account_native"] is True
    assert file_payload["broker_lifecycle_truth_satisfied"] is False
    assert file_payload["asof_decision_truth_satisfied"] is False
    assert file_payload["export_tool"] == "scripts/export_mt5_research_ticks.py"


class FakeMT5:
    TIMEFRAME_M1 = 1

    def symbol_select(self, _symbol: str, _enabled: bool) -> bool:
        return True

    def copy_rates_range(self, _symbol, _timeframe, _start, _end):
        return [
            _rate("2026-06-02T13:00:00+00:00", 100.0, 100.2, 99.9, 100.1),
            _rate("2026-06-02T13:01:00+00:00", 100.1, 100.5, 100.0, 100.3),
            _rate("2026-06-02T13:02:00+00:00", 100.3, 100.8, 100.2, 100.7),
        ]

    def last_error(self):
        return (1, "Success")


class FakeTickMT5:
    COPY_TICKS_ALL = 1

    def symbol_select(self, _symbol: str, _enabled: bool) -> bool:
        return True

    def copy_ticks_range(self, _symbol, _start, _end, _flag):
        return [
            {
                "time_msc": 1780405200123,
                "bid": 99.9,
                "ask": 100.0,
                "last": 99.95,
                "volume": 1,
                "flags": 0,
            },
            {
                "time_msc": 1780405201456,
                "bid": 102.1,
                "ask": 102.2,
                "last": 102.15,
                "volume": 1,
                "flags": 0,
            },
        ]

    def last_error(self):
        return (1, "Success")


@dataclass
class FakeAccount:
    login: int = 123456
    server: str = "FTMO-Demo"


def _rate(ts: str, open_: float, high: float, low: float, close: float) -> dict:
    return {
        "time": int(datetime.fromisoformat(ts).timestamp()),
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "tick_volume": 10,
    }
