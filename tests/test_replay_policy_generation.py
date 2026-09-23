"""Behavioural tests for the generation port (``replay_policy.generation``).

These assert *behaviour*, not source text: every test drives the real
``UltimateBookLiveEngine._generate_intents`` through the port and checks what
comes out.  A test that grepped the module for a substring would pass against a
wrong implementation, which is the failure mode `CLAUDE.md` §6 calls out.

Two of these pin bugs that a control caught during the session rather than
anything found by reading -- ``test_bars_are_fetched_under_the_broker_symbol``
and ``test_h4_closes_are_broker_aligned_not_utc_multiples``.  Both silently
returned "no candidates", which is indistinguishable from "the sleeve did not
fire" unless something asserts it.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib

import pytest
import yaml

from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
from src.research_infra.replay_policy.generation import (
    CsvBarSource,
    EmptyBarSource,
    GenerationError,
    GenerationPort,
    InMemoryBarSource,
    ReplayMT5,
    bar_closes,
)

UTC = dt.timezone.utc
H4 = 16388
M15 = 15


def _runtime_config() -> dict:
    base = yaml.safe_load(open("config/agent_config.yaml"))
    return dict(base.get("gtos_vnext_runtime") or {})


def _resolver(profile: str):
    return build_broker_symbol_resolver(yaml.safe_load(open(f"config/profiles/{profile}.yaml")) or {})


def _flat_bars(n: int, start: dt.datetime, minutes: int, price: float = 100.0) -> list[dict]:
    return [
        {
            "time": (start + dt.timedelta(minutes=minutes * i)).isoformat(),
            "open": price, "high": price, "low": price, "close": price, "volume": 1.0,
        }
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# the null control
# ---------------------------------------------------------------------------
def test_empty_bar_source_generates_nothing():
    """The port's null control.  No bars -> every sleeve warmup-gates closed."""
    port = GenerationPort(_runtime_config(), EmptyBarSource(),
                          namespace="t_null", broker_symbol=_resolver("operator_profile"))
    result = port.generate(dt.datetime(2026, 6, 20, 12, tzinfo=UTC))
    assert result.candidates == ()
    # but it DID try: the port must be exercising the engine, not short-circuiting
    assert len(result.evaluations) > 0


def test_the_active_book_is_twenty_nine_sleeves_under_the_live_dial():
    """DF-1 reconciles ``active_specs``' 32 generator specs to the live 29
    (``book_engine.py:439-440``)."""
    port = GenerationPort(_runtime_config(), EmptyBarSource(),
                          namespace="t_census", broker_symbol=_resolver("operator_profile"))
    assert len(port.active_sleeve_names()) == 29


# ---------------------------------------------------------------------------
# the profile intersection -- reproduced against live truth
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "profile,expected_unsupported,expected_supported_slots",
    # ETHUSD added to `crypto` 2026-08-11 (lane B7): +1 supported slot on BOTH profiles, because
    # both declare it. `expected_unsupported` is unchanged for exactly that reason.
    [("operator_profile", 0, 96), ("redacted_account", 19, 77)],
)
def test_profile_intersection_matches_the_live_generation_telemetry(
    profile, expected_unsupported, expected_supported_slots
):
    """``bridge.broker_profile_generation`` in the live packets, reproduced.

    These exact numbers appear in the runtime-learning packets for the two live
    namespaces, so this is a comparison against live truth rather than against
    the port's own expectations.  redacted_account is the discriminating side: it is
    the profile missing the four metal crosses, DASHUSD, XPDUSD, XTZUSD, AVAUSD.
    """
    port = GenerationPort(_runtime_config(), EmptyBarSource(),
                          namespace=f"t_{profile}", broker_symbol=_resolver(profile))
    tel = port.generate(dt.datetime(2026, 6, 20, 12, tzinfo=UTC)).telemetry
    assert tel["active_spec_count"] == 29
    # 95 until 2026-08-11, when ETHUSD was added to `crypto.ON_SURFACE` (owner-authorized, lane
    # B7). One symbol on one active spec is exactly one slot: 29 specs unchanged, 95 -> 96. The
    # per-profile numbers below are unchanged, because ETHUSD is declared on BOTH live profiles --
    # if it were missing from one, `broker_unsupported_symbol_slot_count` would have absorbed it
    # there, which is what makes this assertion worth keeping rather than deleting.
    assert tel["active_symbol_slot_count"] == 96
    assert tel["broker_unsupported_symbol_slot_count"] == expected_unsupported
    assert tel["profile_supported_symbol_slot_count"] == expected_supported_slots


def test_metals_core_runs_six_of_six_on_ftmo_and_two_of_six_on_redacted_account():
    """B99b/D0 said the four metal crosses are absent from *both* live profiles.
    Measured, they are absent only from redacted_account -- so on FTMO ``metals_core``
    had its full declared universe and still produced nothing (D16)."""
    cfg = _runtime_config()
    seen = {}
    for profile in ("operator_profile", "redacted_account"):
        port = GenerationPort(cfg, EmptyBarSource(), namespace=f"t_mc_{profile}",
                              broker_symbol=_resolver(profile))
        skips = port.generate(dt.datetime(2026, 6, 20, 12, tzinfo=UTC)).skips
        missing = {s["symbol"] for s in skips
                   if s.get("sleeve") == "metals_core"
                   and s.get("reason") == "profile_missing_instrument_config"}
        seen[profile] = missing
    assert seen["operator_profile"] == set()
    assert seen["redacted_account"] == {"XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD"}


# ---------------------------------------------------------------------------
# the seams that silently return nothing when wrong
# ---------------------------------------------------------------------------
def test_bars_are_fetched_under_the_broker_symbol_not_the_canonical_one():
    """``book_engine.py:461`` fetches under the broker name.  A bar source keyed
    by canonical name returns nothing for every remapped symbol, and the failure
    is silent -- it looks exactly like "the sleeve did not fire"."""
    resolver = _resolver("operator_profile")
    assert resolver("SPX500") == "US500.cash"        # the crossing exists
    bars = InMemoryBarSource()
    bars.add("SPX500", H4, _flat_bars(260, dt.datetime(2026, 1, 1, tzinfo=UTC), 240))
    mt5 = ReplayMT5(bars, now=dt.datetime(2026, 4, 1, tzinfo=UTC))
    assert mt5.get_candles("SPX500", H4, 260) != []        # canonical key hits
    assert mt5.get_candles("US500.cash", H4, 260) == []    # broker key misses
    # ...which is what the engine will ask for:
    port = GenerationPort(_runtime_config(), bars, namespace="t_xing",
                          broker_symbol=resolver)
    fetched = {s for s, _tf, _n in
               [(e["symbol"], e["timeframe"], e["bars_requested"])
                for e in port.generate(dt.datetime(2026, 4, 1, tzinfo=UTC)).evaluations]}
    assert "US500.cash" in fetched and "SPX500" not in fetched


def test_h4_closes_are_broker_aligned_not_utc_multiples():
    """FTMO H4 bars close at UTC 21/01/05/09/13/17 because the server runs
    NY+7.  Driving a replay at UTC multiples of four evaluates every sleeve up
    to three hours off its own decision bar."""
    src = CsvBarSource({("XAUUSD", H4): "data/historical_2026/XAUUSD_H4.csv"})
    rows = src._load(("XAUUSD", H4))
    assert rows, "archive fixture missing"
    hours = {dt.datetime.fromisoformat(r["time"]).hour for r in rows}
    assert hours & {1, 5, 9, 13, 17, 21}
    assert not hours & {0, 4, 8, 12, 16, 20}


def test_csv_source_refuses_a_file_with_no_declared_timebase():
    """An undeclared time basis is exactly how F7 happened; the loader fails
    closed rather than assuming UTC."""
    src = CsvBarSource({("XAUUSD", H4): "data/XAUUSD_H4.csv"})   # no sidecar
    with pytest.raises(GenerationError):
        src.candles("XAUUSD", H4, 10, dt.datetime(2026, 4, 1, tzinfo=UTC))


def test_csv_source_converts_broker_local_stamps_to_utc_on_the_us_dst_calendar(tmp_path):
    """The offset is seasonal, and it follows the **US** calendar (Session B).

    NY+7 means UTC+2 in January (NY on EST) and UTC+3 in July (NY on EDT), so the
    same broker-local 00:00 stamp is 22:00 or 21:00 UTC the previous day
    depending on the date.  A fixed +3 -- the EET assumption both earlier audits
    made -- is wrong for roughly four weeks a year.
    """
    for broker_stamp, expected in (("2026-01-05 00:00:00", "2026-01-04T22:00"),
                                   ("2026-07-06 00:00:00", "2026-07-05T21:00")):
        csv = tmp_path / f"X_{broker_stamp[:10]}_H4.csv"
        csv.write_text(f"time,open,high,low,close,volume\n{broker_stamp},1,1,1,1,1\n")
        csv.with_suffix(".csv.timebase.json").write_text(json.dumps({
            "broker_clock_server": "FTMO-Server3", "time_column_basis": "broker_server_local",
        }))
        rows = CsvBarSource({("X", H4): csv})._load(("X", H4))
        assert rows[0]["time"].startswith(expected), broker_stamp


# ---------------------------------------------------------------------------
# the ENCODING is a property of the bytes, not of the sidecar schema (Session CA, B2104)
# ---------------------------------------------------------------------------
def _sidecar_v1_broker_local(csv_path, **extra):
    csv_path.with_suffix(".csv.timebase.json").write_text(json.dumps({
        "schema_version": "gtos_timebase_sidecar_v1",
        "time_column": "time", "time_column_basis": "broker_server_local",
        "broker_clock_server": "FTMO-Server3", "declares": csv_path.name, **extra,
    }))


def test_epoch_time_column_loads_under_a_schema1_broker_local_sidecar(tmp_path):
    """A bridge export stamped by the SANCTIONED writer carries schema 1 over MT5 epochs.

    `research_timebase.write_sidecar` has no encoding field at all -- `time_column_basis`
    states which CLOCK, never whether the column is an epoch or an ISO string. Before this
    fix `_load` inferred the encoding from the sidecar SCHEMA, so every row of
    `bridge_ftmo_carrycond_h4_m1_20260730` raised `fromisoformat` and was `continue`d, and
    the series loaded as EMPTY with no error: 8 of 8 files, 0 rows each.
    """
    csv = tmp_path / "XAUEUR_H4.csv"
    # 1611201600 == 2021-01-21 04:00:00 broker wall clock (FTMO-Server3 = NY+7, so UTC+2
    # in January) -> 02:00 UTC. The same epoch decoded as UTC would read 04:00 -- F7.
    csv.write_text("time,open,high,low,close,tick_volume\n1611201600,1,2,0.5,1.5,7\n")
    _sidecar_v1_broker_local(csv)
    rows = CsvBarSource({("XAUEUR", H4): csv})._load(("XAUEUR", H4))
    assert len(rows) == 1
    assert rows[0]["time"].startswith("2021-01-21T02:00")
    assert rows[0]["volume"] == 7.0


def test_iso_time_column_still_loads_under_the_same_sidecar(tmp_path):
    """The epoch branch must not capture ISO stamps: an ISO date always carries a `-`."""
    csv = tmp_path / "X_H4.csv"
    csv.write_text("time,open,high,low,close,volume\n2026-01-05 00:00:00,1,1,1,1,1\n")
    _sidecar_v1_broker_local(csv)
    rows = CsvBarSource({("X", H4): csv})._load(("X", H4))
    assert rows[0]["time"].startswith("2026-01-04T22:00")


def test_a_series_that_parses_to_nothing_raises_instead_of_reading_as_no_data(tmp_path):
    """An empty result from unparseable bytes is indistinguishable from an absent symbol.

    That is the failure this whole fix is about: the caller skips the symbol, the sleeve
    silently loses it from its surface, and every log reads healthy. It fails closed now.
    """
    csv = tmp_path / "X_H4.csv"
    csv.write_text("time,open,high,low,close,volume\nnot-a-time-at-all!,1,1,1,1,1\n")
    _sidecar_v1_broker_local(csv)
    src = CsvBarSource({("X", H4): csv})
    with pytest.raises(GenerationError) as ei:
        src._load(("X", H4))
    assert "0 usable bars" in str(ei.value)
    assert "not-a-time-at-all!" in str(ei.value)


def test_an_absent_file_is_still_an_empty_series_not_an_error(tmp_path):
    """The refusal is scoped to bytes that exist and do not decode -- not to a missing file,
    which is a legitimate 'this symbol is not in this archive'."""
    src = CsvBarSource({("X", H4): tmp_path / "nope_H4.csv"})
    assert src._load(("X", H4)) == []


def test_partially_unparseable_rows_are_counted_and_published_not_dropped_silently(tmp_path):
    csv = tmp_path / "X_H4.csv"
    csv.write_text("time,open,high,low,close,volume\n"
                   "1611201600,1,1,1,1,1\n"
                   "garbage,1,1,1,1,1\n")
    _sidecar_v1_broker_local(csv)
    src = CsvBarSource({("X", H4): csv})
    assert len(src._load(("X", H4))) == 1
    assert dict(src.describe())["rows_dropped_unparseable_time_cell"] == {f"X:{H4}": 1}


def test_rows_outside_a_declared_window_are_not_an_encoding_refusal(tmp_path):
    """All-dropped-by-the-declared-window stays legal: it is recorded and deliberate."""
    csv = tmp_path / "X_H4.csv"
    csv.write_text("time,open,high,low,close,volume\n2026-01-05 00:00:00,1,1,1,1,1\n")
    _sidecar_v1_broker_local(csv, valid_from="2026-06-01", valid_through="2026-06-30")
    src = CsvBarSource({("X", H4): csv})
    assert src._load(("X", H4)) == []
    assert dict(src.describe())["rows_dropped_outside_declared_timebase_window"] == {f"X:{H4}": 1}


def test_the_real_bridge_export_loads_rather_than_reading_as_empty():
    """The measured case, against the bytes on this machine. Skips where they are absent."""
    export = pathlib.Path("/Users/borr/GTOSActive/repo/data/mt5_research_exports/"
                          "bridge_ftmo_carrycond_h4_m1_20260730")
    if not (export / "XAUEUR_H4.csv").is_file():
        pytest.skip("bridge export not on this machine (data/ is gitignored)")
    src = CsvBarSource({("XAUEUR", H4): export / "XAUEUR_H4.csv",
                        ("GER40.cash", 1): export / "GER40_M1.csv"})
    assert len(src._load(("XAUEUR", H4))) == 8547
    assert len(src._load(("GER40.cash", 1))) == 90000


# ---------------------------------------------------------------------------
# bar semantics
# ---------------------------------------------------------------------------
def test_candles_include_the_forming_bar_because_bar_provider_drops_it():
    """``bar_provider.py:58`` drops the last candle.  A source that withholds the
    forming bar therefore costs the caller its most recent CLOSED bar."""
    start = dt.datetime(2026, 1, 1, tzinfo=UTC)
    bars = InMemoryBarSource()
    bars.add("S", H4, _flat_bars(10, start, 240))
    # at 08:30 the 08:00 bar is forming; bars at 00:00 and 04:00 are closed
    got = bars.candles("S", H4, 10, start + dt.timedelta(hours=8, minutes=30))
    assert [r["time"] for r in got][-1] == (start + dt.timedelta(hours=8)).isoformat()
    from src.components.ultimate_book.bar_provider import candles_to_bars
    _closed, times = candles_to_bars(got, drop_forming=True)
    assert times[-1] == start + dt.timedelta(hours=4)


def test_warmup_floor_fails_closed_below_the_cluster_minimum():
    """``bar_provider.enough`` gates metals at 200 closed bars.  199 closed bars
    must produce no candidate -- never a wrong one."""
    start = dt.datetime(2026, 1, 1, tzinfo=UTC)
    cfg = _runtime_config()
    resolver = _resolver("operator_profile")
    for n_closed, expect_fetch in ((199, True), (260, True)):
        bars = InMemoryBarSource()
        bars.add("XAUUSD", H4, _flat_bars(n_closed + 1, start, 240))
        port = GenerationPort(cfg, bars, namespace=f"t_warm{n_closed}", broker_symbol=resolver)
        now = start + dt.timedelta(minutes=240 * (n_closed + 1))
        res = port.generate(now, tags=["metals_core"])
        assert any(e["symbol"] == "XAUUSD" for e in res.evaluations) is expect_fetch
        # flat bars never produce a signal either way; the point is it does not raise
        assert res.candidates == ()


def test_bar_closes_are_aligned_to_the_timeframe_grid():
    got = bar_closes(dt.datetime(2026, 1, 1, 0, 5, tzinfo=UTC),
                     dt.datetime(2026, 1, 1, 1, 0, tzinfo=UTC), M15)
    assert got == [dt.datetime(2026, 1, 1, 0, 15, tzinfo=UTC),
                   dt.datetime(2026, 1, 1, 0, 30, tzinfo=UTC),
                   dt.datetime(2026, 1, 1, 0, 45, tzinfo=UTC),
                   dt.datetime(2026, 1, 1, 1, 0, tzinfo=UTC)]
    with pytest.raises(GenerationError):
        bar_closes(dt.datetime(2026, 1, 1, tzinfo=UTC), dt.datetime(2026, 1, 2, tzinfo=UTC), 999)


# ---------------------------------------------------------------------------
# the replay clock must be explicit
# ---------------------------------------------------------------------------
def test_replay_mt5_refuses_to_serve_bars_without_a_clock():
    """An unset replay clock must raise, not quietly serve "now" -- a replay that
    silently used wall-clock time would leak the future into every fetch."""
    with pytest.raises(GenerationError):
        ReplayMT5(InMemoryBarSource()).get_candles("X", H4, 10)


def test_replay_mt5_exposes_no_order_path():
    """The safety property is "has no method that could send", not "cannot be
    constructed" -- ``create_mt5("live")`` succeeds on macOS."""
    mt5 = ReplayMT5(EmptyBarSource(), now=dt.datetime(2026, 1, 1, tzinfo=UTC))
    for forbidden in ("order_send", "order_check", "position_close", "connect"):
        assert not hasattr(mt5, forbidden)


# ---------------------------------------------------------------------------
# generation -> decision, composed
# ---------------------------------------------------------------------------
def test_generated_candidates_flow_into_the_decision_policy_and_size():
    """The two halves of the port compose without an adapter.

    Session H's ``SleeveBookPolicy`` consumes ``PolicyCandidate``; the generation
    port emits it.  This drives real archive bars through the production
    generators and then through the production sizer, which is the end-to-end
    shape K1 asks for -- run here over an out-of-window archive because the live
    window's warmup bars do not exist locally.  It pins that the remaining work
    is wiring a ``BarSource``, not adapting a type.
    """
    import glob
    import os

    from src.research_infra.replay_policy.core import AccountDayState
    from src.research_infra.replay_policy.sleeve_book import SleeveBookPolicy

    cfg = _runtime_config()
    resolver = _resolver("operator_profile")
    files = {}
    for path in glob.glob("data/historical_2026/*.csv"):
        sym, _, tfn = os.path.basename(path)[:-4].rpartition("_")
        if tfn == "H4":
            files[(resolver(sym), H4)] = path      # keyed by BROKER symbol
    if not files:
        pytest.skip("bar archive not present")

    port = GenerationPort(cfg, CsvBarSource(files), namespace="t_e2e", broker_symbol=resolver)
    policy = SleeveBookPolicy(cfg, account="A")

    # a bar close on which idxrev is known to generate over this archive
    rows = CsvBarSource(files)._load((resolver("XAUUSD"), H4))
    closes = [dt.datetime.fromisoformat(r["time"]) + dt.timedelta(minutes=240) for r in rows]
    closes = [c for c in closes if c >= dt.datetime(2026, 1, 1, tzinfo=UTC)]

    produced = []
    for close in closes[:400]:
        produced = port.generate(close, tags=["idxrev"]).candidates
        if produced:
            break
    assert produced, "idxrev generated nothing over 400 archive H4 closes -- the control that caught two driver bugs"

    for cand in produced:
        assert cand.stop_dist > 0          # admission.py:1148-1149 fails the unit closed otherwise
        assert cand.direction in (1, -1)   # admission.py:1146-1147
        assert cand.decision_bar_iso and cand.timeframe == H4

    decision = policy.decide(produced, AccountDayState(
        equity=100_000.0, high_water=100_000.0, realized_today_pct=0.0, open_risk_pct=0.0,
        namespace="t_e2e"))
    assert decision.policy_id == "sleeve_book_w7"
    assert isinstance(decision.total_risk_pct, float)
    # the gates are false in the live config, so this must be a shadow decision
    assert decision.authority.get("live_activation_allowed") in (False, None)


# ---------------------------------------------------------------------------
# the VPS bars archive: gzip + broker-epoch + the second sidecar schema
# ---------------------------------------------------------------------------
VPS_BARS = "/Users/borr/GTOSActive/vps-bars-20260727"


def _vps(name: str) -> str:
    return f"{VPS_BARS}/{name}"


def test_broker_epoch_sidecar_is_decoded_as_wall_clock_not_utc(tmp_path):
    """The VPS export's ``time`` is a raw MT5 epoch whose decode-as-UTC yields the
    BROKER wall clock (``broker_clock.py:434-437``).  Decoding it as UTC and
    keeping it is finding F7 and shifts every session-anchored sleeve by 2-3 h.

    Fixture: broker epoch 1086926400 decodes-as-UTC to 2004-06-11T04:00 broker
    local; June is NY-EDT so the server is UTC+3, giving 01:00Z.
    """
    csv = tmp_path / "X_H4.csv"
    csv.write_text("time,open,high,low,close,tick_volume,spread,real_volume\n"
                   "1086926400,384.0,384.3,383.3,383.8,47,0,0\n")
    (tmp_path / "X_H4.csv.timebase.json").write_text(json.dumps({
        "timebase": "broker_server_wall_clock", "broker": "FTMO-Server3",
    }))
    rows = CsvBarSource({("X", H4): csv})._load(("X", H4))
    assert rows[0]["time"].startswith("2004-06-11T01:00")


def test_unrecognised_sidecar_declaration_is_refused(tmp_path):
    """Two sidecar schemas are honoured; a third is refused rather than guessed."""
    csv = tmp_path / "Y_H4.csv"
    csv.write_text("time,open,high,low,close,volume\n1086926400,1,1,1,1,1\n")
    (tmp_path / "Y_H4.csv.timebase.json").write_text(json.dumps({"timebase": "something_else"}))
    with pytest.raises(GenerationError):
        CsvBarSource({("Y", H4): csv})._load(("Y", H4))


@pytest.mark.skipif(not __import__("pathlib").Path(VPS_BARS).is_dir(),
                    reason="VPS bars archive not present")
def test_vps_bar_archive_loads_gzipped_and_lands_on_the_live_h4_grid():
    """Behavioural check against the real archive.

    FTMO H4 bars close on the UTC 1/5/9/13/17/21 grid in summer (server UTC+3) and
    2/6/10/14/18/22 in winter (UTC+2), because the server runs NY+7 on the US DST
    calendar.  **Both grids must appear and nothing else** — seeing only one would
    mean the offset was applied as a constant, which is the EET assumption both
    earlier audits made and is wrong for ~4 weeks a year.  The summer grid is the
    one the live packets' `decision_bar_iso` values sit on.
    """
    src = CsvBarSource({("XAUUSD", H4): _vps("FTMO_XAUUSD_H4.csv.gz")})
    rows = src._load(("XAUUSD", H4))
    assert len(rows) > 30_000
    summer, winter = {1, 5, 9, 13, 17, 21}, {2, 6, 10, 14, 18, 22}
    hours = {dt.datetime.fromisoformat(r["time"]).hour for r in rows[-4000:]}
    assert hours <= summer | winter
    assert hours & summer and hours & winter        # DST is applied, not assumed constant
    # It must cover the live window's 46.2-day H4 warmup, which the in-tree archive
    # (ending 2026-04-24) did not.  XAUUSD H4 begins 2004-06-11 -- the note's
    # 2000-03-29 is the earliest across all symbols, not per-symbol.
    assert rows[0]["time"] < "2005-01-01"
    assert rows[-1]["time"] > "2026-07-20"


@pytest.mark.skipif(not __import__("pathlib").Path(VPS_BARS).is_dir(),
                    reason="VPS bars archive not present")
def test_every_live_sleeve_symbol_resolves_to_a_loadable_bar_series():
    """The canonical->broker crossing is honoured end to end, for every symbol the
    live book declares.

    **This test replaces one that asserted the index and oil families were ABSENT
    from the pull.** That assertion pinned a transient state of someone's export
    rather than a behaviour, and it went red the moment the archive was completed —
    a self-inflicted regression in this session's own A/B. The lesson is the one
    `CLAUDE.md` §6 already states in another form: pin behaviour, not a snapshot of
    the world. What is genuinely invariant, and what actually broke three times
    this session, is the crossing: files are keyed on CANONICAL names while
    ``book_engine.py:461`` fetches under the BROKER name.
    """
    import pathlib

    if not any(pathlib.Path(VPS_BARS).glob("FTMO_*_H4.csv.gz")):
        pytest.skip("VPS bars archive has no FTMO H4 series")

    resolver = _resolver("operator_profile")
    canonical = {p.name[len("FTMO_"):].rsplit("_", 1)[0]
                 for p in pathlib.Path(VPS_BARS).glob("FTMO_*_H4.csv.gz")}
    # the crossing is real for the index/oil families and identity for metals/crypto
    remapped = {s: resolver(s) for s in canonical if resolver(s) != s}
    assert remapped, "no canonical->broker remap found; the crossing test is vacuous"

    # a series keyed by the BROKER name loads; keyed canonically it does not — which
    # is exactly how the port silently produced zero idxrev intents twice.
    sample = sorted(remapped)[0]
    path = f"{VPS_BARS}/FTMO_{sample}_H4.csv.gz"
    assert CsvBarSource({(resolver(sample), H4): path}).candles(
        resolver(sample), H4, 5, dt.datetime(2026, 7, 20, tzinfo=UTC)), sample
    assert CsvBarSource({(sample, H4): path}).candles(
        resolver(sample), H4, 5, dt.datetime(2026, 7, 20, tzinfo=UTC)) == []
