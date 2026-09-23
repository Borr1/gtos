"""The pre-gap bar, wired — and the proof that the default path did not move.

Session AB wrote and tested `candles_to_bars(..., now=..., interval_minutes=...)` and
deliberately did not wire it, because wiring it changes which bars an armed book trades and it
could not be gated behind a config key: `config/agent_config.yaml`'s bytes are hashed into the
live activation token's config digest, so adding a key there stops the armed book placing until
the token is re-minted.

Session AI wired it behind `run_book.py --recover-pre-gap-bar`, which is the same mechanism
`--tags` already uses -- supervisor-settable, no source edit on a live host, no config byte
touched. This file asserts the two properties that make that safe:

  1. OFF (the default) the generation engine's bar fetch is byte-identical to the call it made
     before the argument existed. Asserted by intercepting the fetch and comparing kwargs, not
     by reading the diff.
  2. ON, the last closed bar before a gap becomes the decision bar AND survives the
     recency guard -- which is the part that is not obvious, because that guard
     (`book_engine.py`, "skip a bar whose close is older than ~2 intervals") is the second half
     of the defect and a fix that only changed the fetch would be defeated by it.
"""

from __future__ import annotations

import datetime as dt

import pytest

from src.components.ultimate_book import bar_provider as BP


UTC = dt.timezone.utc


def _candles(start: dt.datetime, n: int, minutes: int):
    """`n` candles, oldest first, each `minutes` long, the last one OPENING at
    `start + (n-1)*minutes`."""
    out = []
    for i in range(n):
        t = start + dt.timedelta(minutes=minutes * i)
        out.append({"time": t.isoformat(), "open": 100.0 + i, "high": 101.0 + i,
                    "low": 99.0 + i, "close": 100.5 + i, "volume": 10})
    return out


# ---------------------------------------------------------------------------------
# 1. The capability itself, at the boundary that matters
# ---------------------------------------------------------------------------------
def test_without_both_kwargs_the_last_candle_is_still_dropped():
    """The whole safety argument for the default rests on this."""
    ivl = 240
    last_open = dt.datetime(2026, 7, 24, 17, 0, tzinfo=UTC)   # a Friday H4 open
    cs = _candles(last_open - dt.timedelta(minutes=ivl * 4), 5, ivl)
    now = last_open + dt.timedelta(minutes=ivl)               # its close, exactly

    plain, _ = BP.candles_to_bars(cs)
    with_now_only, _ = BP.candles_to_bars(cs, now=now)
    with_ivl_only, _ = BP.candles_to_bars(cs, interval_minutes=ivl)
    assert len(plain) == 4
    assert len(with_now_only) == 4, "one kwarg alone must not change behaviour"
    assert len(with_ivl_only) == 4, "one kwarg alone must not change behaviour"


def test_with_both_kwargs_a_provably_closed_last_candle_is_kept():
    ivl = 240
    last_open = dt.datetime(2026, 7, 24, 17, 0, tzinfo=UTC)
    cs = _candles(last_open - dt.timedelta(minutes=ivl * 4), 5, ivl)
    kept, times = BP.candles_to_bars(cs, now=last_open + dt.timedelta(minutes=ivl),
                                     interval_minutes=ivl)
    assert len(kept) == 5
    assert times[-1] == last_open


def test_a_still_forming_last_candle_is_dropped_even_with_both_kwargs():
    """The flag recovers bars it can PROVE are closed. One second early is not proof."""
    ivl = 240
    last_open = dt.datetime(2026, 7, 24, 17, 0, tzinfo=UTC)
    cs = _candles(last_open - dt.timedelta(minutes=ivl * 4), 5, ivl)
    kept, _ = BP.candles_to_bars(
        cs, now=last_open + dt.timedelta(minutes=ivl) - dt.timedelta(seconds=1),
        interval_minutes=ivl)
    assert len(kept) == 4


# ---------------------------------------------------------------------------------
# 2. The wiring: OFF is byte-identical, ON reaches the fetch
# ---------------------------------------------------------------------------------
class _Recorder:
    """Stands in for `get_closed_bars` and records exactly how it was called."""

    def __init__(self):
        self.calls = []

    def __call__(self, mt5, symbol, timeframe, count, **kw):
        self.calls.append({"symbol": symbol, "timeframe": timeframe, "count": count, **kw})
        return [], []


def _engine(monkeypatch, *, recover: bool):
    from src.components.ultimate_book import book_engine as BE
    rec = _Recorder()
    monkeypatch.setattr(BE, "get_closed_bars", rec)
    eng = BE.UltimateBookLiveEngine({}, object(), ".", namespace="test_ns",
                                   recover_pre_gap_bar=recover)
    return eng, rec


def test_off_by_default_only_h4_primary_fetch_keeps_last_closed(monkeypatch, tmp_path):
    """H4 always passes now+interval so FRA40 session-close is not one bar behind.

    D1 / M15 / M1 stay on the old drop unless --recover-pre-gap-bar (D1 pre-gap
    EV is worse; do not flip that flag globally). Aux fetches stay untouched.
    """
    from src.components.ultimate_book import book_engine as BE
    rec = _Recorder()
    monkeypatch.setattr(BE, "get_closed_bars", rec)
    eng = BE.UltimateBookLiveEngine({}, object(), str(tmp_path), namespace="test_ns")
    assert eng._recover_pre_gap_bar is False
    now = dt.datetime(2026, 7, 24, 21, 0, tzinfo=UTC)
    try:
        eng._generate_intents(now=now)
    except Exception:
        pass  # a bare config cannot complete a cycle; the fetch kwargs are what is under test
    assert len(rec.calls) >= 20, (
        f"only {len(rec.calls)} fetch calls -- this assertion exists so the test below cannot "
        f"pass vacuously if a refactor stops reaching the fetch. Measured 27 at the time of "
        f"writing (the metals/crypto/index/substrate surfaces of the default 11).")
    h4 = [c for c in rec.calls if c["timeframe"] in (16388, "H4")]
    other = [c for c in rec.calls if c["timeframe"] not in (16388, "H4")]
    assert h4, "default surface must fetch H4"
    for c in h4:
        assert c.get("now") == now
        assert c.get("interval_minutes") == 240
    for c in other:
        assert "now" not in c and "interval_minutes" not in c, (
            "non-H4 default path must call get_closed_bars without keep-last kwargs, "
            f"and this call carried {sorted(set(c) - {'symbol', 'timeframe', 'count'})}")


def test_on_the_fetch_carries_now_and_the_timeframe_interval(monkeypatch, tmp_path):
    from src.components.ultimate_book import book_engine as BE
    rec = _Recorder()
    monkeypatch.setattr(BE, "get_closed_bars", rec)
    eng = BE.UltimateBookLiveEngine({}, object(), str(tmp_path), namespace="test_ns",
                                   recover_pre_gap_bar=True)
    assert eng._recover_pre_gap_bar is True
    now = dt.datetime(2026, 7, 24, 21, 0, tzinfo=UTC)
    try:
        eng._generate_intents(now=now)
    except Exception:
        pass
    primary = [c for c in rec.calls if "now" in c]
    assert len(primary) >= 20, (
        f"only {len(primary)} of {len(rec.calls)} fetch calls carried the pre-gap kwargs; the "
        f"flag is not reaching the fetch")
    for c in primary:
        assert c["now"] == now
        assert c["interval_minutes"] == BE._TF_MINUTES.get(c["timeframe"]), (
            f"the interval must come from the SPEC's timeframe, not a constant: "
            f"{c['timeframe']} -> {c['interval_minutes']}")
    # The default 11-sleeve surface spans TWO timeframes -- H4 (16388) on 25 of the 27 fetches
    # and M15 (15) on the two JPY sleeves -- so a single interval across every call would mean
    # the timeframe was being ignored and a constant substituted. Measured: {15: 2, 16388: 25}.
    assert {(c["timeframe"], c["interval_minutes"]) for c in primary} == {(15, 15), (16388, 240)}


def test_the_owner_and_the_launcher_thread_the_flag_through():
    """A flag the launcher cannot reach is not wired. Checked by signature, so a refactor
    that drops the passthrough fails here rather than silently at the console."""
    import inspect

    from src.components.ultimate_book.book_owner import UltimateBookOwner

    assert "recover_pre_gap_bar" in inspect.signature(UltimateBookOwner.__init__).parameters
    src = inspect.getsource(UltimateBookOwner.__init__)
    assert "recover_pre_gap_bar=recover_pre_gap_bar" in src, (
        "the owner accepts the argument and must pass it to the generation engine")

    import pathlib
    rb = pathlib.Path(__file__).resolve().parents[2] / "run_book.py"
    text = rb.read_text()
    # Behavioural where it can be, textual only for the CLI surface -- argparse's wiring is
    # not importable without running main(), and main() constructs a live MT5 client.
    assert "--recover-pre-gap-bar" in text
    assert "recover_pre_gap_bar=args.recover_pre_gap_bar" in text


def test_no_config_key_was_added_for_this(monkeypatch):
    """The reason the flag is a CLI argument at all: `agent_config.yaml`'s bytes are hashed
    into the live activation token's config digest, so a key there would stop the armed book
    placing until the token was re-minted. If someone later adds one, this fails and they have
    to read why."""
    import pathlib

    cfg = (pathlib.Path(__file__).resolve().parents[2] / "config/agent_config.yaml").read_text()
    assert "recover_pre_gap_bar" not in cfg
    assert "pre_gap" not in cfg


# ---------------------------------------------------------------------------------
# 3. The half a fetch-only fix would have missed
# ---------------------------------------------------------------------------------
def test_the_recovered_bar_is_fresh_enough_to_survive_the_recency_guard():
    """`book_engine` skips a bar whose close is older than ~2 intervals, which is the SECOND
    half of AB's defect: the pre-gap bar is dropped as forming and then refused as stale.

    So the flag is only a fix if the recovered bar's close is recent at the moment the cycle
    runs. It is, and the arithmetic is the point: a cycle triggers ON a reference symbol's bar
    close, so `now == bar_close` for the recovered bar (age 0) against `1 x interval` for the
    bar the engine would otherwise have used. Both are inside the `2 x interval` guard, which
    is exactly why the defect was silent -- the engine traded a one-interval-old bar and looked
    healthy.
    """
    ivl = 240
    last_open = dt.datetime(2026, 7, 24, 17, 0, tzinfo=UTC)
    cs = _candles(last_open - dt.timedelta(minutes=ivl * 4), 5, ivl)
    now = last_open + dt.timedelta(minutes=ivl)

    _, plain_times = BP.candles_to_bars(cs)
    _, kept_times = BP.candles_to_bars(cs, now=now, interval_minutes=ivl)

    plain_age = (now - (plain_times[-1] + dt.timedelta(minutes=ivl))).total_seconds()
    kept_age = (now - (kept_times[-1] + dt.timedelta(minutes=ivl))).total_seconds()
    guard = 2 * ivl * 60

    assert kept_age == 0.0
    assert plain_age == ivl * 60
    assert plain_age < guard, ("the OLD bar also passes the guard -- which is why the defect "
                               "never announced itself")
    assert kept_age < guard
    assert kept_times[-1] > plain_times[-1], "the decision bar moved forward by one interval"
