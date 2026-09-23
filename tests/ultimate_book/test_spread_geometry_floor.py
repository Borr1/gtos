"""The generation-side spread-geometry floor (Session AY, B1810) — default-inert, fail-closed.

WHAT HAS TO BE TRUE FOR THIS TO BE SAFE TO SHIP TO A HOST RUNNING REAL MONEY

  1. OFF (the default) nothing moves. Asserted by running the SAME engine fixture with and
     without the argument and comparing the produced intents field-by-field, not by reading
     the diff.
  2. A malformed selection stops the WORKER, at launch, rather than degrading in silence at
     every tick. `--tags ""` means ALL sleeves (`run_book.py:340`) and `registry.py:144`
     drops an unknown tag with no error; both are fail-OPEN shapes this estate has already
     been bitten by, so both are refused here.
  3. ON, an intent whose live spread exceeds the limit never appears in `intents` — which is
     the whole point, because `book_engine.evaluate` hands `intents` to
     `_running_conviction_override` and `admission.py:1188` carries that count MONOTONE
     UPWARD into every other sleeve's size that day.
  4. An unreadable quote REFUSES. The authoritative pre-trade gate answers the identical
     question with `missing_current_quote_spread_or_sl_distance`, a refusal reason; a
     generation floor that failed open would be the only one of the three layers that let
     an unpriceable leg through.
  5. A bug inside the floor refuses and says so, rather than standing the whole book down
     (`evaluate`'s catch-all would turn it into `engine_exception` and zero units on every
     sleeve) or silently passing.
"""

from __future__ import annotations

import json
import pathlib
import tempfile

import pytest

from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
from src.components.ultimate_book.spread_geometry import (
    MAX_PLAUSIBLE_LIMIT,
    SPREAD_GEOMETRY_FLOOR_DEFAULT_LIMIT,
    SpreadGeometryFloorError,
    evaluate_intent,
    parse_spread_geometry_floor,
    resolve_floor_limit,
)

from tests.ultimate_book.test_book_engine import _FakeMT5, _cfg, _fixture_now


class _Tick:
    def __init__(self, bid, ask):
        self.bid = bid
        self.ask = ask


class _MT5WithTick(_FakeMT5):
    """The engine fixture plus a quote, so the floor has something to read."""

    def __init__(self, spread=1.0, mid=60000.0, **kw):
        super().__init__(**kw)
        self._spread = spread
        self._mid = mid

    def get_tick(self, symbol):
        half = self._spread / 2.0
        return _Tick(self._mid - half, self._mid + half)


class _Intent:
    def __init__(self, stop_dist):
        self.stop_dist = stop_dist
        self.sleeve = "crypto"


# ---------------------------------------------------------------------------------
# 1. parse — every refusal is a refusal, not a degradation
# ---------------------------------------------------------------------------------
def test_absent_selection_is_off():
    assert parse_spread_geometry_floor(None) == {}


def test_empty_string_is_refused_not_read_as_all_or_none():
    with pytest.raises(SpreadGeometryFloorError) as e:
        parse_spread_geometry_floor("")
    assert "EMPTY" in str(e.value)
    with pytest.raises(SpreadGeometryFloorError):
        parse_spread_geometry_floor("   ")


def test_sleeve_without_a_limit_inherits_and_with_one_is_explicit():
    assert parse_spread_geometry_floor("crypto") == {"crypto": None}
    assert parse_spread_geometry_floor("crypto:0.075") == {"crypto": 0.075}
    assert parse_spread_geometry_floor(" a , b:0.2 ",
                                       known_sleeves=("a", "b")) == {"a": None, "b": 0.2}


def test_unknown_sleeve_is_refused_when_a_known_set_is_supplied():
    with pytest.raises(SpreadGeometryFloorError) as e:
        parse_spread_geometry_floor("crpyto", known_sleeves=("crypto",))
    assert "unknown sleeve" in str(e.value)


def test_the_launcher_validates_against_every_registered_generator_not_just_BUILT():
    """`BUILT` is 11 sleeves; the candidate book adds 9 and market expansion 12. AY-1's
    largest measured repair is `asia_pdl_fade`, which is in CANDIDATE_BUILT — validating
    against `BUILT` alone refused the flag's best use as a typo, which is what the first
    draft of `run_book.py` did."""
    from src.components.ultimate_book.sleeves.registry import (
        BUILT, CANDIDATE_BUILT, MARKET_EXPANSION_BUILT,
    )

    known = set(BUILT) | set(CANDIDATE_BUILT) | set(MARKET_EXPANSION_BUILT)
    for name in ("asia_pdl_fade", "sub_mid_dn_revert", "sub_xvol_pullback",
                 "mx_btcusd_d1_donchian_20_breakout", "orb_crypto_london"):
        assert parse_spread_geometry_floor(name, known_sleeves=known) == {name: None}
    assert "asia_pdl_fade" not in BUILT, "the point of the test"
    assert len(known) >= 32


def test_stray_comma_and_duplicate_are_refused():
    with pytest.raises(SpreadGeometryFloorError):
        parse_spread_geometry_floor("crypto,")
    with pytest.raises(SpreadGeometryFloorError) as e:
        parse_spread_geometry_floor("crypto:0.1,crypto:0.2")
    assert "twice" in str(e.value)


@pytest.mark.parametrize("bad", ["crypto:abc", "crypto:0", "crypto:-0.1", "crypto:"])
def test_implausible_limits_are_refused(bad):
    with pytest.raises(SpreadGeometryFloorError):
        parse_spread_geometry_floor(bad)


def test_a_limit_at_or_above_one_is_refused_because_it_permits_the_defect():
    """A `spread_r` limit >= 1 lets the stop be narrower than the round-trip spread — the
    exact pathology. Refused rather than honoured, because it would read as protection."""
    with pytest.raises(SpreadGeometryFloorError) as e:
        parse_spread_geometry_floor(f"crypto:{MAX_PLAUSIBLE_LIMIT}")
    assert "read as protection" in str(e.value)
    with pytest.raises(SpreadGeometryFloorError):
        parse_spread_geometry_floor("crypto:2.0")


# ---------------------------------------------------------------------------------
# 2. resolve — the two layers agree by construction, not by a copied constant
# ---------------------------------------------------------------------------------
def test_a_sleeve_not_in_the_selection_has_no_limit():
    assert resolve_floor_limit({}, "crypto", {"energy_agri": None}) is None
    assert resolve_floor_limit({}, "crypto", {}) is None
    assert resolve_floor_limit({}, "crypto", None) is None


def test_inherited_limit_is_the_send_gates_own_including_its_per_sleeve_override():
    cfg = {
        "selected_cell_pretrade_max_spread_r": 0.10,
        "selected_cell_pretrade_max_spread_r_by_sleeve": {"fx_jpy": 0.35},
    }
    assert resolve_floor_limit(cfg, "crypto", {"crypto": None}) == 0.10
    assert resolve_floor_limit(cfg, "fx_jpy", {"fx_jpy": None}) == 0.35
    # an explicit selection always wins over the inherited one
    assert resolve_floor_limit(cfg, "fx_jpy", {"fx_jpy": 0.2}) == 0.2


def test_inherited_limit_falls_back_to_the_send_gates_own_literal():
    """`broker_net_cost_engine:574` falls back to 0.10 when the key is absent. If the two
    layers disagreed there, generation would admit exactly what the send gate refuses."""
    assert resolve_floor_limit({}, "crypto", {"crypto": None}) == \
        SPREAD_GEOMETRY_FLOOR_DEFAULT_LIMIT
    assert SPREAD_GEOMETRY_FLOOR_DEFAULT_LIMIT == 0.10


def test_a_malformed_config_value_does_not_raise_into_the_live_path():
    cfg = {"selected_cell_pretrade_max_spread_r": "not a number",
           "selected_cell_pretrade_max_spread_r_by_sleeve": {"crypto": "also not"}}
    assert resolve_floor_limit(cfg, "crypto", {"crypto": None}) == \
        SPREAD_GEOMETRY_FLOOR_DEFAULT_LIMIT


# ---------------------------------------------------------------------------------
# 3. evaluate — the arithmetic, and both fail-closed branches
# ---------------------------------------------------------------------------------
def test_a_wide_stop_passes_and_a_narrow_one_is_refused_at_the_boundary():
    tick = _Tick(99.95, 100.05)          # spread 0.10
    # spread_r = 0.10 / stop
    ok, obs = evaluate_intent(_Intent(2.0), tick, 0.10)      # 0.05 <= 0.10
    assert ok is None
    assert obs["spread_r"] == pytest.approx(0.05)
    exact, _ = evaluate_intent(_Intent(1.0), tick, 0.10)     # 0.10, NOT > 0.10
    assert exact is None, "the limit is inclusive, matching the send gate's `>` comparison"
    bad, obs = evaluate_intent(_Intent(0.5), tick, 0.10)     # 0.20 > 0.10
    assert bad is not None and bad.startswith("spread_geometry_floor:")
    assert obs["spread_r"] == pytest.approx(0.20)


def test_no_limit_means_no_opinion():
    assert evaluate_intent(_Intent(0.0001), _Tick(99.0, 101.0), None)[0] is None


@pytest.mark.parametrize("tick", [None, _Tick(0.0, 0.0), _Tick(101.0, 100.0), _Tick(None, 1.0)])
def test_an_unreadable_or_crossed_quote_is_refused_not_admitted(tick):
    reason, _ = evaluate_intent(_Intent(1.0), tick, 0.10)
    assert reason is not None and "quote_unavailable" in reason


@pytest.mark.parametrize("stop", [0.0, -1.0, None, "wat"])
def test_a_nonpositive_or_unreadable_stop_is_refused(stop):
    reason, _ = evaluate_intent(_Intent(stop), _Tick(99.95, 100.05), 0.10)
    assert reason is not None and "nonpositive_stop" in reason


def test_the_observation_is_recorded_for_a_passing_leg_too():
    """Building the spread record out of a refusal log is the derive-don't-accumulate trap;
    the passing legs are most of the distribution."""
    _, obs = evaluate_intent(_Intent(2.0), _Tick(99.95, 100.05), 0.10)
    assert obs["spread_r"] == pytest.approx(0.05)
    assert obs["spread_price"] == pytest.approx(0.10)
    assert obs["limit"] == 0.10


# ---------------------------------------------------------------------------------
# 4. the engine — default-inert, and ON it removes the intent BEFORE the count
# ---------------------------------------------------------------------------------
def _intent_fields(intents):
    return [(i.sleeve, i.symbol, i.direction, round(float(i.stop_dist), 10)) for i in intents]


def test_default_off_is_byte_identical_to_before_the_argument_existed():
    mt5 = _MT5WithTick(spread=1.0)
    now = _fixture_now(mt5)
    control = UltimateBookLiveEngine(_cfg(True), mt5, tempfile.mkdtemp()).evaluate(
        tags=("crypto",), now_utc=now)
    for absent in ({}, None):
        got = UltimateBookLiveEngine(
            _cfg(True), mt5, tempfile.mkdtemp(),
            spread_geometry_floor=absent).evaluate(tags=("crypto",), now_utc=now)
        assert _intent_fields(got["intents"]) == _intent_fields(control["intents"])
        assert got["n_intents"] == control["n_intents"] >= 1
        assert "spread_geometry_floor" not in (got["generation"] or {})


def test_a_sleeve_not_named_is_untouched_even_with_the_floor_on():
    mt5 = _MT5WithTick(spread=5000.0)     # would refuse anything it evaluated
    now = _fixture_now(mt5)
    control = UltimateBookLiveEngine(_cfg(True), mt5, tempfile.mkdtemp()).evaluate(
        tags=("crypto",), now_utc=now)
    got = UltimateBookLiveEngine(
        _cfg(True), mt5, tempfile.mkdtemp(),
        spread_geometry_floor={"energy_agri": None}).evaluate(tags=("crypto",), now_utc=now)
    assert _intent_fields(got["intents"]) == _intent_fields(control["intents"])


def test_on_a_pathological_spread_removes_the_intent_and_says_why(monkeypatch):
    monkeypatch.setattr("src.judgment.cost_choices.withholds", lambda *args, **kwargs: True)
    # Wide enough that spread_r >> 0.10 on any plausible BTC stop, and still a VALID
    # quote: a spread big enough to drive `bid` negative is refused by the
    # unreadable-quote branch instead, which would test the wrong thing.
    mt5 = _MT5WithTick(spread=5000.0)
    now = _fixture_now(mt5)
    control = UltimateBookLiveEngine(_cfg(True), mt5, tempfile.mkdtemp()).evaluate(
        tags=("crypto",), now_utc=now)
    assert control["n_intents"] >= 1, "the fixture must fire, or this asserts nothing"
    got = UltimateBookLiveEngine(
        _cfg(True), mt5, tempfile.mkdtemp(),
        spread_geometry_floor={"crypto": None}).evaluate(tags=("crypto",), now_utc=now)
    assert got["n_intents"] == 0
    skips = [s for s in got["generation_skips"]
             if str(s.get("reason", "")).startswith("spread_geometry_floor:")]
    assert skips, got["generation_skips"]
    assert skips[0]["sleeve"] == "crypto"
    assert skips[0]["spread_geometry"]["spread_r"] > 0.10
    assert got["generation"]["spread_geometry_floor"]["refused"] == len(skips)


def test_a_tight_spread_leaves_the_intent_alone_with_the_floor_on():
    mt5 = _MT5WithTick(spread=0.01)       # a hair's width on a 60k instrument
    now = _fixture_now(mt5)
    control = UltimateBookLiveEngine(_cfg(True), mt5, tempfile.mkdtemp()).evaluate(
        tags=("crypto",), now_utc=now)
    got = UltimateBookLiveEngine(
        _cfg(True), mt5, tempfile.mkdtemp(),
        spread_geometry_floor={"crypto": None}).evaluate(tags=("crypto",), now_utc=now)
    assert _intent_fields(got["intents"]) == _intent_fields(control["intents"])
    assert got["generation"]["spread_geometry_floor"] == {
        "evaluated": control["n_intents"], "refused": 0, "sleeves": []}


def test_a_broker_with_no_quote_at_all_refuses_rather_than_admits():
    """`_FakeMT5` has no `get_tick`. The floor must treat that as a refusal, matching
    `pretrade_cost_refusal_reasons`' `missing_current_quote_spread_or_sl_distance`."""
    mt5 = _FakeMT5()
    now = _fixture_now(mt5)
    got = UltimateBookLiveEngine(
        _cfg(True), mt5, tempfile.mkdtemp(),
        spread_geometry_floor={"crypto": None}).evaluate(tags=("crypto",), now_utc=now)
    assert got["n_intents"] == 0
    assert any("quote_unavailable" in str(s.get("reason", ""))
               for s in got["generation_skips"]), got["generation_skips"]


def test_a_bug_inside_the_floor_refuses_loudly_and_does_not_stand_the_book_down(monkeypatch):
    """`evaluate` catches everything as `engine_exception` and returns zero units for EVERY
    sleeve. An internal fault in a default-off, one-sleeve filter must not do that — and it
    must not silently pass, either."""
    import src.components.ultimate_book.spread_geometry as SG

    def boom(*a, **k):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(SG, "evaluate_intent", boom)
    mt5 = _MT5WithTick(spread=0.01)
    now = _fixture_now(mt5)
    got = UltimateBookLiveEngine(
        _cfg(True), mt5, tempfile.mkdtemp(),
        spread_geometry_floor={"crypto": None}).evaluate(tags=("crypto",), now_utc=now)
    assert got["ok"] is True, "the cycle survives"
    assert got["reason"] != "engine_exception"
    assert got["n_intents"] == 0, "fail-closed: the intent is refused, not admitted"
    assert any("spread_geometry_floor_error:RuntimeError" in str(s.get("reason", ""))
               for s in got["generation_skips"]), got["generation_skips"]


# ---------------------------------------------------------------------------------
# 5. Evaluation previews never become durable running-conviction truth
# ---------------------------------------------------------------------------------
def test_evaluation_preview_does_not_enter_the_days_accepted_sleeve_union():
    """Generation may preview a candidate for its own sizing, but evaluation never persists it.

    The placement owner now commits running conviction only after broker acceptance. Therefore both
    the geometry-refused arm and the unfiltered evaluation-only arm leave no accepted-sleeve state.
    """
    cfg = dict(_cfg(True), ultimate_book_kelly_running_count=True, ultimate_book_kelly_lite=True)
    mt5 = _MT5WithTick(spread=5000.0)     # a valid quote, refused on GEOMETRY
    now = _fixture_now(mt5)

    on_dir = tempfile.mkdtemp()
    off_dir = tempfile.mkdtemp()
    UltimateBookLiveEngine(cfg, mt5, off_dir).evaluate(tags=("crypto",), now_utc=now)
    UltimateBookLiveEngine(cfg, mt5, on_dir, spread_geometry_floor={"crypto": None}).evaluate(
        tags=("crypto",), now_utc=now)

    def _union(root):
        """Read the persisted accepted-placement union, if any."""
        path = pathlib.Path(root) / "pipeline_state/ultimate_book/ftmo_primary/firing_sleeves.json"
        if not path.is_file():
            return {}
        return json.loads(path.read_text()).get("days") or {}

    off_union, on_union = _union(off_dir), _union(on_dir)
    assert not any("crypto" in v for v in off_union.values()), off_union
    assert not any("crypto" in v for v in on_union.values()), on_union
