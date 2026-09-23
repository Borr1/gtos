from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.research_infra import replay_prepared_day_pack as prepared_pack
from src.research_infra import (
    v4_timewarp_simulated_live_research_loop as timewarp,
)


class _Clock:
    def __init__(self, days, sources):
        del days, sources

    def decision_times_for_day(self, day, *, smoke_subset=False):
        del day, smoke_subset
        return [datetime(2026, 1, 2, 0, 15, tzinfo=timezone.utc)]


class _LiveReplay:
    def __init__(self, sources, config, *, campaign_exact_cache=None):
        del sources, config, campaign_exact_cache

    def contract_row(self):
        return {
            "live_replay_mode": True,
            "raw_data_construction_mode": "unit_no_session",
        }


class _DecisionCore:
    def __init__(self, **kwargs):
        del kwargs


class _PreparedReader:
    def __init__(self, record):
        self.record = record
        self.compatibility = None
        self.consumed = []
        self.finished = False

    def assert_compatible(self, **kwargs):
        self.compatibility = kwargs

    def next_window(self, **kwargs):
        self.consumed.append(kwargs)
        return self.record

    def finish(self):
        self.finished = True


def test_no_event_day_pack_consumption_matches_direct_reducer(monkeypatch) -> None:
    symbols = ("EURUSD", "XAUUSD")
    guard = {"active": True, "reason": "unit_verified_no_session"}
    monkeypatch.setattr(timewarp, "INCLUDED_SYMBOLS", symbols)
    monkeypatch.setattr(timewarp, "ReplayClock", _Clock)
    monkeypatch.setattr(timewarp, "LiveReplayMode", _LiveReplay)
    monkeypatch.setattr(timewarp, "V4DecisionCycleCore", _DecisionCore)
    monkeypatch.setattr(
        timewarp,
        "calendar_no_session_breadth_guard",
        lambda **kwargs: guard,
    )
    monkeypatch.setattr(
        prepared_pack,
        "source_identity_root",
        lambda sources: "b" * 64,
    )
    campaign = timewarp.CampaignConfig(
        name="unit_no_event",
        phase="unit",
        profile="S0R0",
        days=("2026-01-02",),
        pending_expiry_minutes=60,
        use_repaired_pending_expiry=True,
    )
    config = {}
    sources = {symbol: {} for symbol in symbols}
    timestamp = "2026-01-02T00:15:00+00:00"
    record = {
        "schema": "gtos.replay_acceleration.prepared_window.v1",
        "trading_day": "2026-01-02",
        "window_ordinal": 0,
        "decision_time_utc": timestamp,
        "calendar_no_session_breadth_guard": guard,
        "symbols": [
            {
                "symbol": symbol,
                "status": "source_skipped",
                "asof_row": {},
                "mso_payload": None,
                "candidates": [],
            }
            for symbol in symbols
        ],
    }
    reader = _PreparedReader(record)

    direct = timewarp.run_campaign(
        campaign=campaign,
        config=config,
        sources=sources,
    )
    packed = timewarp.run_campaign(
        campaign=campaign,
        config=config,
        sources=sources,
        prepared_day_pack=reader,
    )

    assert timewarp.stable_sha256(direct["ledgers"]) == timewarp.stable_sha256(
        packed["ledgers"]
    )
    assert reader.compatibility == {
        "days": ["2026-01-02"],
        "symbols": list(symbols),
        "factor_neutral_config_root_sha256": (
            prepared_pack.factor_neutral_config_root(config)
        ),
        "source_identity_root_sha256": "b" * 64,
        "max_candidates_per_symbol_window": 0,
    }
    assert reader.consumed == [
        {
            "trading_day": "2026-01-02",
            "decision_time_utc": timestamp,
            "window_ordinal": 0,
        }
    ]
    assert reader.finished is True
    assert packed["broker"].order_send_attempts == 0


def test_real_pack_requires_external_root_before_reducer(
    tmp_path, monkeypatch
) -> None:
    symbol = "XAUUSD"
    timestamp = "2026-01-02T00:15:00+00:00"
    monkeypatch.setattr(timewarp, "INCLUDED_SYMBOLS", (symbol,))
    root = tmp_path / "pack"
    prepared_pack.seal_prepared_day_pack(
        output_dir=root,
        records=[
            {
                "schema": prepared_pack.WINDOW_SCHEMA,
                "trading_day": "2026-01-02",
                "window_ordinal": 0,
                "decision_time_utc": timestamp,
                "calendar_no_session_breadth_guard": {"active": True},
                "symbols": [
                    {
                        "symbol": symbol,
                        "status": "source_skipped",
                        "asof_row": {
                            "raw_data_status": (
                                "calendar_no_session_breadth_guard_day_skipped"
                            ),
                            "candidate_count": 0,
                            "decision_time_utc": timestamp,
                        },
                        "mso_payload": None,
                        "candidates": [],
                    }
                ],
            }
        ],
        bindings={
            "days": ["2026-01-02"],
            "symbols": [symbol],
            "factor_neutral_config_root_sha256": "a" * 64,
            "source_identity_root_sha256": "b" * 64,
            "max_candidates_per_symbol_window": 0,
        },
    )
    reader = prepared_pack.PreparedDayPackReader(root)
    campaign = timewarp.CampaignConfig(
        name="unit_external_root",
        phase="unit",
        profile="S0R0",
        days=("2026-01-02",),
        pending_expiry_minutes=60,
        use_repaired_pending_expiry=True,
    )
    with pytest.raises(
        ValueError,
        match="prepared_day_pack_external_root_not_authenticated",
    ):
        timewarp.run_campaign(
            campaign=campaign,
            config={},
            sources={symbol: {}},
            prepared_day_pack=reader,
        )
