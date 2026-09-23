"""Behavioural tests for the three broad-origin generator repairs.

Every assertion here drives the real
``generate_live_broader_origin_candidates`` and reads its OUTPUT.  Nothing
greps the source.  The file also carries the blast-radius proof: the seven
at-market families are byte-identical across the repair, and the generator is
not on the live book's import path at all.

Population evidence behind the fixtures:
``docs/audits/fable5-vision-audit-20260725/phase20/receipts/``.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.components.broad_origin_emission_contract import (
    BIN_PAST_STOP,
    BIN_RESTING,
    BIN_TARGET_THROUGH,
    MAX_ADMISSION_GAP_R_KEY,
    MAX_SELECTED_BAR_AGE_PERIODS_KEY,
    MIN_ADMISSION_GAP_R_KEY,
    REASON_MAX_GAP_R,
    REASON_PAST_STOP,
    REFUSE_PAST_STOP_KEY,
    RUNTIME_SECTION,
    STALE_BAR_REASON,
    fill_gap_r,
)
from src.components.broader_origin_generators import (
    generate_live_broader_origin_candidates,
)

POI_FAMILIES = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}

LEGACY_RUNTIME = {
    REFUSE_PAST_STOP_KEY: False,
    MAX_ADMISSION_GAP_R_KEY: None,
    MIN_ADMISSION_GAP_R_KEY: None,
    MAX_SELECTED_BAR_AGE_PERIODS_KEY: None,
}


def _dt(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _flat_bars(*, latest_open: str, count: int = 60, close: float = 100.0,
               width: float = 1.0) -> list[dict]:
    latest = _dt(latest_open)
    start = latest - timedelta(minutes=15 * (count - 1))
    return [
        {
            "time": (start + timedelta(minutes=15 * i)).isoformat().replace("+00:00", "Z"),
            "open": close, "high": close + width / 2,
            "low": close - width / 2, "close": close,
        }
        for i in range(count)
    ]


def _raw(symbol: str, bars: list[dict], *, declare_bar: bool = True) -> dict:
    latest_open = _dt(bars[-1]["time"])
    payload: dict = {"symbol": symbol, "candles": {"M15": bars}}
    if declare_bar:
        payload["candle_open_utc"] = latest_open.isoformat()
        payload["candle_close_utc"] = (latest_open + timedelta(minutes=15)).isoformat()
    return payload


def _mso(*, atr_14: float = 1.0, order_blocks=(), breaker_blocks=(),
         fair_value_gaps=()) -> SimpleNamespace:
    return SimpleNamespace(
        timestamp_utc=None,
        timeframes={
            "M15": SimpleNamespace(atr_14=atr_14, fair_value_gaps=list(fair_value_gaps)),
            "H1": SimpleNamespace(
                order_blocks=list(order_blocks),
                breaker_blocks=list(breaker_blocks),
            ),
        },
    )


def _config(frameworks: list[str], *, runtime: dict | None = None) -> dict:
    config: dict = {
        "risk": {"min_rr": 1.5, "sl_buffer_atr_multiplier": 0.25},
        "gate1": {"ob_retest_sl_min_buffer_atr": 0.5},
        "model_a": {"enabled_frameworks": frameworks},
    }
    if runtime is not None:
        config[RUNTIME_SECTION] = dict(runtime)
    return config


def _run(raw_data, *, mso=None, config=None, now=None, symbol="US30_CASH",
         audit=None) -> list[dict]:
    return generate_live_broader_origin_candidates(
        raw_data=raw_data,
        mso=mso,
        config=config or {"risk": {"min_rr": 1.5}},
        symbol=symbol,
        kill_zone="ny",
        now_utc=now or _dt(raw_data["candle_close_utc"]),
        generation_audit=audit,
    )


def _families(candidates) -> set[str]:
    return {c["origin_family"] for c in candidates}


# ---------------------------------------------------------------------------
# A BREAKER ZONE PLACED SO THE MARKET IS ALREADY BEYOND THE CANDIDATE'S STOP.
#
# market 100.0, ATR 1.0, buffer 0.25 ATR.  Zone [100.5, 101.0] -> entry 100.75,
# stop 100.25, risk 0.5, so fill_gap_r = (100.0 - 100.75)/0.5 = -1.5.  The zone
# sits 0.5 % of price away, well inside the 1 % proximity scope that was the
# only admission test before the repair.
# ---------------------------------------------------------------------------
PAST_STOP_BREAKER = {
    "zone_low": 100.5, "zone_high": 101.0, "direction": "bullish",
    "is_retested": False, "formation_time": "2026-05-26T09:00:00Z",
    "mitigation_time": "2026-05-26T10:00:00Z", "causing_event": "bos",
    "original_ob_direction": "bearish",
}
# zone [99.5, 99.9] -> entry 99.70, stop 99.25, risk 0.45, gap_r = +0.667:
# the contract the family actually describes, a limit resting below the market.
RESTING_BREAKER = {**PAST_STOP_BREAKER, "zone_low": 99.5, "zone_high": 99.9}
# zone [99.0, 99.2] -> entry 99.10, stop 98.75, risk 0.35, gap_r = +2.571: the
# 1.5 R target is already behind the market, yet the 1 % proximity scope admits
# it (the zone is 0.8 % of price away).  This is the population the far-side
# radius cuts.
TARGET_THROUGH_BREAKER = {**PAST_STOP_BREAKER, "zone_low": 99.0, "zone_high": 99.2}


def _breaker_case(breaker: dict, *, runtime: dict | None = None, audit=None):
    bars = _flat_bars(latest_open="2026-05-26T10:00:00Z", close=100.0, width=0.2)
    raw = _raw("US30_CASH", bars)
    return _run(
        raw,
        mso=_mso(atr_14=1.0, breaker_blocks=[breaker]),
        config=_config(["breaker_re_entry"], runtime=runtime),
        audit=audit,
    )


def test_breaker_born_past_its_own_stop_is_refused_by_default() -> None:
    audit: dict = {}
    candidates = _breaker_case(PAST_STOP_BREAKER, audit=audit)
    assert "current_breaker_re_entry" not in _families(candidates)

    partition = audit["current_framework_admission"]["by_family"]["current_breaker_re_entry"]
    assert partition["considered"] == 1
    assert partition["admitted"] == 0
    assert partition["refused"] == 1
    assert partition["bins"] == {BIN_PAST_STOP: 1}
    assert partition["refusal_reasons"] == {REASON_PAST_STOP: 1}
    assert partition["partition_reconciled"] is True


def test_the_legacy_escape_hatch_emits_that_same_malformed_candidate() -> None:
    """...and its published geometry proves the malformation, not just the label.

    The emitted order's stop-loss sits ABOVE the market for a LONG, i.e. on the
    wrong side of the price the limit would actually fill at.
    """

    candidates = _breaker_case(PAST_STOP_BREAKER, runtime=LEGACY_RUNTIME)
    breaker = next(c for c in candidates if c["origin_family"] == "current_breaker_re_entry")
    assert breaker["side"] == "LONG"
    market = 100.0
    assert market < breaker["stop_loss"] < breaker["entry_price"]
    gap = fill_gap_r(side="LONG", entry_price=breaker["entry_price"],
                     stop_loss=breaker["stop_loss"], current_price=market)
    assert gap == pytest.approx(-1.5)


def test_an_admitted_poi_candidate_publishes_its_own_gap_in_R() -> None:
    audit: dict = {}
    candidates = _breaker_case(RESTING_BREAKER, audit=audit)
    breaker = next(c for c in candidates if c["origin_family"] == "current_breaker_re_entry")
    assert breaker["poi_admission_bin"] == BIN_RESTING
    recomputed = fill_gap_r(
        side=breaker["side"],
        entry_price=breaker["entry_price"],
        stop_loss=breaker["stop_loss"],
        current_price=breaker["source_fields"]["current_price"],
    )
    assert breaker["poi_fill_gap_r"] == pytest.approx(recomputed)
    assert audit["current_framework_admission"]["policy"][REFUSE_PAST_STOP_KEY] is True


def test_far_side_radius_refuses_a_candidate_whose_target_is_already_behind() -> None:
    audit: dict = {}
    kept = _breaker_case(TARGET_THROUGH_BREAKER, audit=audit)
    breaker = next(c for c in kept if c["origin_family"] == "current_breaker_re_entry")
    gap = breaker["poi_fill_gap_r"]
    assert gap >= 1.5, "fixture must sit beyond the 1.5 R target for this test"
    assert breaker["poi_admission_bin"] == BIN_TARGET_THROUGH
    # ...and the percent-of-price scope that was the ONLY gate before the repair
    # admits it comfortably: this is defect B, reproduced end to end.
    assert breaker["source_fields"]["proximity_gap_pct"] < 0.01

    refused_audit: dict = {}
    refused = _breaker_case(
        TARGET_THROUGH_BREAKER,
        runtime={MAX_ADMISSION_GAP_R_KEY: 1.5},
        audit=refused_audit,
    )
    assert "current_breaker_re_entry" not in _families(refused)
    partition = refused_audit["current_framework_admission"]["by_family"]
    assert partition["current_breaker_re_entry"]["refusal_reasons"] == {REASON_MAX_GAP_R: 1}


# ---------------------------------------------------------------------------
# ORDER BLOCKS take the same gate through a different code path.
# ---------------------------------------------------------------------------
def test_order_block_born_past_its_own_stop_is_refused_by_default() -> None:
    # buffer 0.5 ATR for ob_retest: zone [100.8, 101.2] -> entry 101.0,
    # stop 100.3, risk 0.7, gap_r = (100 - 101)/0.7 = -1.43
    ob = {"high": 101.2, "low": 100.8, "type": "bullish", "mitigated": False,
          "formation_time": "2026-05-26T09:00:00Z", "touch_count": 0,
          "causing_event_type": "bos"}
    bars = _flat_bars(latest_open="2026-05-26T10:00:00Z", close=100.0, width=0.2)
    raw = _raw("US30_CASH", bars)

    audit: dict = {}
    default = _run(raw, mso=_mso(atr_14=1.0, order_blocks=[ob]),
                   config=_config(["ob_retest"]), audit=audit)
    assert "current_ob_retest" not in _families(default)
    assert audit["current_framework_admission"]["by_family"]["current_ob_retest"][
        "refusal_reasons"] == {REASON_PAST_STOP: 1}

    legacy = _run(raw, mso=_mso(atr_14=1.0, order_blocks=[ob]),
                  config=_config(["ob_retest"], runtime=LEGACY_RUNTIME))
    assert "current_ob_retest" in _families(legacy)


# ---------------------------------------------------------------------------
# FAIR VALUE GAPS carry a disposition ledger that must still reconcile.
# ---------------------------------------------------------------------------
def _fvg(top: float, bottom: float) -> dict:
    return {
        "top": top, "bottom": bottom, "type": "bullish", "filled": False,
        "formation_time": "2026-05-26T09:00:00Z",
        "created_at_utc": "2026-05-26T09:00:00Z",
        "state_asof_utc": "2026-05-26T10:15:00Z",
        "source_candle_times": [
            "2026-05-26T08:30:00Z", "2026-05-26T08:45:00Z", "2026-05-26T09:00:00Z",
        ],
    }


def _fvg_case(fvg: dict, *, runtime: dict | None = None, audit=None):
    bars = _flat_bars(latest_open="2026-05-26T10:00:00Z", close=100.0, width=0.2)
    return _run(
        _raw("US30_CASH", bars),
        mso=_mso(atr_14=1.0, fair_value_gaps=[fvg]),
        config=_config(["fvg_fill"], runtime=runtime),
        audit=audit,
    )


def test_fvg_born_past_its_own_stop_is_refused_and_the_ledger_reconciles() -> None:
    audit: dict = {}
    candidates = _fvg_case(_fvg(101.0, 100.5), audit=audit)
    assert "current_fvg_fill" not in _families(candidates)

    partition = audit["current_fvg_poi_generation"]
    assert partition["considered_poi_count"] == 1
    assert partition["emitted_poi_count"] == 0
    assert partition["denied_poi_count"] == 1
    assert partition["partition_reconciled"] is True
    assert partition["rows"][0]["reason"] == REASON_PAST_STOP
    assert partition["rows"][0]["producer_disposition"] == "producer_denied_own_risk_envelope"
    assert partition["rows"][0]["uses_outcome_fields"] is False

    legacy = _fvg_case(_fvg(101.0, 100.5), runtime=LEGACY_RUNTIME)
    assert "current_fvg_fill" in _families(legacy)


def test_an_admitted_fvg_publishes_its_gap_and_keeps_the_ledger_whole() -> None:
    audit: dict = {}
    candidates = _fvg_case(_fvg(99.9, 99.5), audit=audit)
    fvg = next(c for c in candidates if c["origin_family"] == "current_fvg_fill")
    assert fvg["poi_admission_bin"] == BIN_RESTING
    assert fvg["poi_fill_gap_r"] == pytest.approx(
        fill_gap_r(side=fvg["side"], entry_price=fvg["entry_price"],
                   stop_loss=fvg["stop_loss"],
                   current_price=fvg["source_fields"]["current_price"])
    )
    partition = audit["current_fvg_poi_generation"]
    assert partition["emitted_poi_count"] == 1
    assert partition["denied_poi_count"] == 0
    assert partition["partition_reconciled"] is True


# ---------------------------------------------------------------------------
# STALE SELECTED BAR
# ---------------------------------------------------------------------------
def _stale_case(now: str, *, runtime: dict | None = None, audit=None,
                declare_bar: bool = False):
    bars = _flat_bars(latest_open="2026-05-26T10:00:00Z", close=100.0)
    bars[-1].update({"open": 100.0, "high": 100.8, "low": 99.2, "close": 100.6})
    raw = _raw("XAUUSD", bars, declare_bar=declare_bar)
    config = {"risk": {"min_rr": 1.5}}
    if runtime is not None:
        config[RUNTIME_SECTION] = dict(runtime)
    return generate_live_broader_origin_candidates(
        raw_data=raw, mso=None, config=config, symbol="XAUUSD",
        kill_zone="london", now_utc=_dt(now), generation_audit=audit,
    )


def test_a_fresh_bar_still_generates() -> None:
    audit: dict = {}
    candidates = _stale_case("2026-05-26T10:15:00Z", audit=audit)
    assert candidates
    assert audit["selected_closed_bar"]["selected_bar_age_periods"] == pytest.approx(0.0)
    assert audit["status"] == "candidate_generation_complete"


def test_one_missing_bar_already_refuses_the_whole_decision() -> None:
    audit: dict = {}
    candidates = _stale_case("2026-05-26T10:30:00Z", audit=audit)
    assert candidates == []
    assert audit["status"] == "stale_selected_closed_bar"
    assert audit["selected_closed_bar"]["reason"] == STALE_BAR_REASON
    assert audit["selected_closed_bar"]["selected_bar_age_periods"] == pytest.approx(1.0)
    assert audit["selected_closed_bar"]["admissible"] is False


def test_a_weekend_gap_refuses_and_the_escape_hatch_restores_the_old_entry() -> None:
    stale = _stale_case("2026-05-28T09:00:00Z")
    assert stale == []
    legacy = _stale_case("2026-05-28T09:00:00Z", runtime=LEGACY_RUNTIME)
    assert legacy, "legacy contract priced the decision off the stale close"
    # the old behaviour is exactly what makes the entry fiction: every at-market
    # candidate is still stamped at the bar that closed two days earlier.
    assert {c["candle_open_utc"] for c in legacy} == {"2026-05-26T10:00:00Z"}


def test_the_age_budget_is_a_dial_and_its_boundary_is_exact() -> None:
    two = {MAX_SELECTED_BAR_AGE_PERIODS_KEY: 2.0}
    assert _stale_case("2026-05-26T10:30:00Z", runtime=two)      # age 1 period
    assert _stale_case("2026-05-26T10:45:00Z", runtime=two) == []  # age 2 periods


def test_the_declared_bar_fast_path_is_gated_too() -> None:
    """``candle_open_utc``/``candle_close_utc`` short-circuit the walk-back; the
    age budget must not be bypassed by declaring a stale bar."""

    audit: dict = {}
    candidates = _stale_case("2026-05-26T10:45:00Z", declare_bar=True, audit=audit)
    assert candidates == []
    assert audit["status"] == "stale_selected_closed_bar"


# ---------------------------------------------------------------------------
# BLAST RADIUS
# ---------------------------------------------------------------------------
def test_the_seven_at_market_families_are_untouched_by_the_repair() -> None:
    """A fresh bar with no POI input must produce a byte-identical candidate set
    under the repaired and the legacy contract."""

    bars = _flat_bars(latest_open="2026-05-26T13:00:00Z", close=100.0)
    bars[-4].update({"open": 100.0, "high": 100.2, "low": 97.0, "close": 99.8})
    bars[-3].update({"open": 99.8, "high": 103.0, "low": 99.6, "close": 102.8})
    bars[-2].update({"open": 102.8, "high": 103.2, "low": 102.4, "close": 103.0})
    bars[-1].update({"open": 103.0, "high": 103.4, "low": 99.0, "close": 103.2})
    leader = _flat_bars(latest_open="2026-05-26T13:00:00Z", close=50.0)
    leader[-2].update({"open": 50.0, "high": 52.4, "low": 49.8, "close": 52.0})
    raw = _raw("XAUUSD", bars)
    cross = {"XAGUSD": _raw("XAGUSD", leader)}

    def run(runtime):
        config = {"risk": {"min_rr": 1.5}}
        if runtime is not None:
            config[RUNTIME_SECTION] = dict(runtime)
        return generate_live_broader_origin_candidates(
            raw_data=_raw("XAUUSD", [dict(b) for b in bars]),
            mso=None, config=config, symbol="XAUUSD", kill_zone="london",
            cross_asset_raw_data={"XAGUSD": _raw("XAGUSD", [dict(b) for b in leader])},
            now_utc=_dt(raw["candle_close_utc"]),
        )

    repaired = run(None)
    legacy = run(LEGACY_RUNTIME)
    assert repaired, "fixture must emit at-market candidates for this to mean anything"
    assert not (_families(repaired) & POI_FAMILIES)
    assert repaired == legacy


def test_the_repair_can_only_subtract_emissions_never_add_or_alter_one() -> None:
    bars = _flat_bars(latest_open="2026-05-26T10:00:00Z", close=100.0, width=0.2)
    raw = _raw("US30_CASH", bars)
    mso = _mso(atr_14=1.0, breaker_blocks=[PAST_STOP_BREAKER, RESTING_BREAKER])

    repaired = _run(raw, mso=mso, config=_config(["breaker_re_entry"]))
    legacy = _run(raw, mso=mso,
                  config=_config(["breaker_re_entry"], runtime=LEGACY_RUNTIME))

    repaired_ids = {c["candidate_id"] for c in repaired}
    legacy_ids = {c["candidate_id"] for c in legacy}
    assert repaired_ids < legacy_ids
    by_id = {c["candidate_id"]: c for c in legacy}
    for candidate in repaired:
        survivor = by_id[candidate["candidate_id"]]
        for key in ("entry_price", "stop_loss", "take_profit_1", "side",
                    "risk_reward_ratio", "candle_open_utc"):
            assert candidate[key] == survivor[key], key


# ---------------------------------------------------------------------------
# LIVE ISOLATION - the generator must not be reachable from the armed book.
# ---------------------------------------------------------------------------
#: The armed set is NOT written down here.  Three wave-20 artifacts wrote it down and all
#: three were wrong the same way (omitting `sub_mid_dn_revert`, which is armed on both
#: accounts; including `mx_btcusd_d1_donchian_20_breakout`, which the owner disarmed on
#: 2026-08-05).  `src/safety/armed_set.py` is the single source of truth: it reconciles
#: `config/live_armed_set.json` (the owner-decision declaration, with a receipt per change)
#: against `scripts/run_book_supervisor.ps1` (the mechanism that supplies `run_book.py
#: --tags`), and `tests/safety/test_armed_set_single_source.py` fails the build if they drift.
#:
#: The union across EVERY worker the launcher starts is the right set for an ISOLATION proof:
#: it is every sleeve that can generate an order on any book, whatever it is sized at.
#: `armed_sleeves()` defaults to `surface="production"` -- the armed book at the production
#: dial, which is what "armed" means everywhere else -- and that default became wrong for THIS
#: file on 2026-08-12, when the two F5 minimal-size experiment workers were declared with the
#: full 32-sleeve registry at a fixed $10 a trade. A $10 order is still an order, and a
#: generator that must not be reachable must not be reachable from those workers either, so
#: this one call passes `surface=None` deliberately.
from src.safety.armed_set import armed_sleeves as _armed_sleeves  # noqa: E402

ARMED_SLEEVES = tuple(sorted(_armed_sleeves(surface=None)))


def test_the_live_book_entrypoint_does_not_import_this_generator() -> None:
    """Behavioural, in a clean interpreter: import the live entrypoint and read
    ``sys.modules``.  The broad-origin family has never traded live and this
    repair must not be able to reach the armed book."""

    code = (
        "import sys, importlib;"
        "importlib.import_module('run_book');"
        "print('src.components.broader_origin_generators' in sys.modules);"
        "print('src.components.broad_origin_emission_contract' in sys.modules)"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True,
                          text=True, timeout=180)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.split() == ["False", "False"], proc.stdout


def test_no_armed_sleeve_is_produced_by_the_broad_origin_generator() -> None:
    from src.components.broader_origin_generators import (
        CURRENT_FRAMEWORK_ORIGIN_FAMILY,
        PRODUCTION_ORIGIN_FAMILIES,
    )

    emitted = set(PRODUCTION_ORIGIN_FAMILIES) | set(CURRENT_FRAMEWORK_ORIGIN_FAMILY.values())
    assert not emitted & set(ARMED_SLEEVES)


def test_armed_sleeves_matches_what_the_committed_launcher_actually_arms() -> None:
    """`ARMED_SLEEVES` is DERIVED from the launcher, not remembered.

    Three artifacts in this wave hard-coded a four-sleeve armed set and all three were
    wrong the same way.  The authority is `src/safety/armed_set.py`, which reconciles the
    owner-decision declaration in `config/live_armed_set.json` against the launcher that
    supplies `run_book.py --tags`.  Reading a launcher's argument list is reading
    configuration, not grepping an implementation for a substring: if the owner arms a
    sixth sleeve, this fails and the declaration gets fixed instead of quietly rotting.
    """

    from src.safety.armed_set import launcher_arming, reconcile

    problems = reconcile()
    assert problems == [], "\n".join(str(p) for p in problems)

    armed: set[str] = set()
    for row in launcher_arming().values():
        assert not row.is_fail_open, f"{row.namespace} passes no --tags: every BUILT sleeve is armed"
        armed |= row.armed
    assert armed == set(ARMED_SLEEVES), (
        f"the launcher arms {sorted(armed)} but this file declares "
        f"{sorted(ARMED_SLEEVES)}"
    )


def test_the_armed_sleeves_resolve_through_the_book_registry_not_this_module() -> None:
    """The armed tags resolve through the sleeve registry, whose generators
    are a disjoint set of callables from this module's families."""

    from src.components.ultimate_book.sleeves.registry import active_specs

    # Both opt-in books are asked for BY NAME. The two branches of `active_specs` are not
    # symmetric (`registry.py:128-141`): with `include_candidate_book=True` an empty
    # `candidate_book_sleeves` means ALL candidates, while with
    # `include_market_expansion_book=True` an empty `market_expansion_sleeves` means NONE --
    # `if allowed:` guards the whole update. So the old two-flag call silently resolved zero
    # market-expansion sleeves, which did not matter while the armed union was four
    # clean/candidate names and started mattering the moment it included `mx_*`.
    specs = active_specs(
        list(ARMED_SLEEVES),
        include_candidate_book=True,
        candidate_book_sleeves=list(ARMED_SLEEVES),
        include_market_expansion_book=True,
        market_expansion_sleeves=list(ARMED_SLEEVES),
    )
    tags = {spec.tag for spec in specs}
    assert tags == set(ARMED_SLEEVES)
    generators = {getattr(spec.generator, "__module__", "") for spec in specs}
    assert not any("broader_origin_generators" in m for m in generators)
    assert not any("broad_origin_emission_contract" in m for m in generators)


# ---------------------------------------------------------------------------
# TWO ATR DEFINITIONS, NAMED
# ---------------------------------------------------------------------------
def test_a_poi_candidate_names_the_atr_that_built_its_stop() -> None:
    """d4 section 7.2: the POI stop buffer uses the market-state Wilder true-range
    ATR while every `predecision_features` value normalises by the module's own
    high-low-mean ATR.  Measured over 611,854 M15 bar-instants the two disagree
    by more than 10 % on 48.30 % of bars, so the candidate must say which it used.
    The geometry is a strategy choice and is deliberately unchanged."""

    from src.components.broader_origin_generators import (
        ATR_SOURCE_MODULE_HIGH_LOW_MEAN,
        ATR_SOURCE_MSO_WILDER_TRUE_RANGE,
    )

    audit: dict = {}
    candidates = _breaker_case(RESTING_BREAKER, audit=audit)
    breaker = next(c for c in candidates
                   if c["origin_family"] == "current_breaker_re_entry")
    assert breaker["atr14_source"] == ATR_SOURCE_MSO_WILDER_TRUE_RANGE
    assert audit["current_framework_admission"]["atr14_source"] == (
        ATR_SOURCE_MSO_WILDER_TRUE_RANGE
    )

    # and the fallback path names itself honestly rather than lying about it
    bars = _flat_bars(latest_open="2026-05-26T10:00:00Z", close=100.0, width=0.2)
    fallback = _run(
        _raw("US30_CASH", bars),
        mso=SimpleNamespace(
            timestamp_utc=None,
            timeframes={
                "M15": SimpleNamespace(atr_14=0.0, fair_value_gaps=[]),
                "H1": SimpleNamespace(order_blocks=[],
                                      breaker_blocks=[RESTING_BREAKER]),
            },
        ),
        config=_config(["breaker_re_entry"]),
    )
    if fallback:
        assert fallback[0]["atr14_source"] == ATR_SOURCE_MODULE_HIGH_LOW_MEAN
