"""Side proof for bar and quote Choices. Does not call the network or the writer."""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

os.environ["GTOS_PIPELINE_CHOICES_RECORD"] = str(Path(tempfile.gettempdir()) / "pipeline_choices_test.jsonl")

from src.components import data_ingestion as di  # noqa: E402
from src.components.ultimate_book.bar_provider import candles_to_bars  # noqa: E402
from src.judgment import pipeline_choices as pc  # noqa: E402

NS = "operator"
NOW = datetime(2026, 9, 21, 10, 20, tzinfo=timezone.utc)


def _bar(iso: str, *, high: float = 2.0, low: float = 0.5) -> dict:
    return {
        "time": iso,
        "open": 1.0,
        "high": high,
        "low": low,
        "close": 1.5,
        "volume": 1,
    }


CANDLES = [
    _bar("2026-09-21T10:00:00+00:00"),
    _bar("2026-09-21T10:15:00+00:00"),
]


def _bind(choice: str | None, probs: dict | None = None):
    def ask(state, **_kwargs):
        if choice is None:
            return {"decision_emitted": False, "choice": None, "probabilities": probs or {}}
        return {
            "decision_emitted": True,
            "choice": choice,
            "probability": 0.8,
            "probabilities": probs or {choice: 0.8},
            "model": "jev-1.13.0",
        }

    pc.bind_ask(ask)
    pc.clear_cache()


def _n_bars(**kwargs) -> int:
    bars, _times = candles_to_bars(
        CANDLES,
        now=NOW,
        interval_minutes=15,
        symbol="XAUUSD",
        timeframe=15,
        **kwargs,
    )
    return len(bars)


def test_last_bar():
    assert _n_bars() == 1
    _bind("forming_bar_stays_out")
    assert _n_bars(namespace=NS) == 1
    _bind("closed_bar_reaches")
    assert _n_bars(namespace=NS) == 2
    _bind(None)
    assert _n_bars(namespace=NS) == 2


def test_unclosed_tail():
    kept = di.filter_closed_candles(CANDLES, "M15", now_utc=NOW)
    assert len(kept) == 1
    _bind("unclosed_stays_out")
    assert len(di.filter_closed_candles(CANDLES, "M15", now_utc=NOW, namespace=NS)) == 1
    _bind("unclosed_reaches")
    assert len(di.filter_closed_candles(CANDLES, "M15", now_utc=NOW, namespace=NS)) == 2
    _bind(None)
    assert len(di.filter_closed_candles(CANDLES, "M15", now_utc=NOW, namespace=NS)) == 2


def test_decision_m15():
    stamped = di.infer_latest_closed_m15_timestamp(CANDLES, now_utc=NOW)
    assert stamped["candle_open_utc"] == "2026-09-21T10:00:00+00:00"
    _bind("this_m15_is_the_close")
    chosen = di.infer_latest_closed_m15_timestamp(CANDLES, now_utc=NOW, namespace=NS)
    assert chosen["candle_timestamp_source"] == "latest_closed_m15_bar"
    _bind("not_this_m15")
    refused = di.infer_latest_closed_m15_timestamp(CANDLES, now_utc=NOW, namespace=NS)
    assert refused["candle_open_utc"] is None
    _bind(None)
    empty = di.infer_latest_closed_m15_timestamp(CANDLES, now_utc=NOW, namespace=NS)
    assert empty["candle_open_utc"] is None


def test_series_and_levels_and_quote():
    class _Mt5:
        def get_candles(self, *_args):
            return CANDLES[:1]

    try:
        di.pull_m5_candles(_Mt5(), 36, "XAUUSD")
        raised = False
    except Exception:
        raised = True
    assert raised is False
    short = di.pull_m5_candles(_Mt5(), 36, "XAUUSD")
    assert short is None
    _bind("m5_reaches")
    assert di.pull_m5_candles(_Mt5(), 36, "XAUUSD", namespace=NS) is not None
    _bind(None)
    assert di.pull_m5_candles(_Mt5(), 36, "XAUUSD", namespace=NS) is not None
    _bind("m5_short")
    assert di.pull_m5_candles(_Mt5(), 36, "XAUUSD", namespace=NS) is None

    day = datetime(2026, 9, 21, tzinfo=timezone.utc).date()
    levels = di.compute_session_levels(
        [_bar("2026-09-18T12:00:00+00:00", high=9.0, low=3.0)],
        day,
    )
    assert levels["pdh"] == 9.0
    _bind(None)
    hidden = di.compute_session_levels(
        [_bar("2026-09-18T12:00:00+00:00", high=9.0, low=3.0)],
        day,
        namespace=NS,
    )
    assert hidden["pdh"] == 0.0
    _bind("prev_day_bars_reach")
    shown = di.compute_session_levels(
        [_bar("2026-09-18T12:00:00+00:00", high=9.0, low=3.0)],
        day,
        namespace=NS,
    )
    assert shown["pdh"] == 9.0

    class _Bid:
        empty = False

        def dropna(self):
            return self

        def __gt__(self, _other):
            return self

        def __getitem__(self, _item):
            return self

        @property
        def iloc(self):
            return self

        def __getitem_iloc(self, idx):
            return 10.0 if idx == 0 else 12.0

        def max(self):
            return 13.0

        def min(self):
            return 9.0

        def __len__(self):
            return 4

    class _Iloc:
        def __getitem__(self, idx):
            return 10.0 if idx == 0 else 12.0

    class _Bid2:
        empty = False
        iloc = _Iloc()

        def dropna(self):
            return self

        def __gt__(self, _other):
            return self

        def __getitem__(self, _item):
            return self

        def max(self):
            return 13.0

        def min(self):
            return 9.0

        def __len__(self):
            return 4

    class _Ticks:
        empty = False
        columns = ["bid"]
        bid = _Bid2()

        def __getitem__(self, key):
            return self.bid

    di._tick_read_ticks_for_bar = lambda *args, **kwargs: _Ticks()
    di._TICKS_ROOT = "ticks"
    bad = _bar("2026-09-21T10:00:00+00:00", high=1.0, low=2.0)
    _bind("candle_print_stands")
    repaired, _report = di.repair_malformed_ohlc_from_ticks(
        [bad], "XAUUSD", "M15", namespace=NS,
    )
    assert repaired[0]["close"] == 1.5
    _bind("tick_quote_reaches")
    replaced, report = di.repair_malformed_ohlc_from_ticks(
        [bad], "XAUUSD", "M15", namespace=NS,
    )
    assert replaced[0]["close"] == 12.0
    assert report["repaired_count"] == 1
    _bind(None)
    stood, report2 = di.repair_malformed_ohlc_from_ticks(
        [bad], "XAUUSD", "M15", namespace=NS,
    )
    assert stood[0]["close"] == 1.5
    assert report2["repaired_count"] == 0


def main() -> None:
    test_last_bar()
    test_unclosed_tail()
    test_decision_m15()
    test_series_and_levels_and_quote()
    print("PIPELINE_CHOICE_PROVE_OK")


if __name__ == "__main__":
    main()
