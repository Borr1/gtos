"""Chair behaviours encoded 2026-08-25 (owner-directed): auto-breakeven + duplicate-stack
dedup, plus the two fill-truth fixes that shipped with them.

Contracts under test:
- `_f5_auto_breakeven`: a fast-family position whose favourable excursion touches
  +F5_AUTO_BE_TRIGGER_R (1.5R of its own initial stop) gets its stop moved to entry through
  the engine's own `_modify_sl`. NULL-RULE runner sleeves (crypto, energy_agri,
  sub_xvol_pullback, metals_softband, vol_compression, mx_*) are NEVER touched. Tighten-only
  by construction; H8-honest under authority-false; namespace-gated.
- `_f5_duplicate_stack_dedup`: same symbol+direction+entry+stop across two engines is one
  bet wearing two tickets — the later ticket closes, the first stays. STRICT equality only.
- `_f5_fill_truth_fields`: direction absent from trade_params (frozen-commit path, measured
  on 178414870) no longer suppresses `f5_fill_deviation_r` — the sign derives from geometry.
- `_f5_on_open(source=...)`: adoption re-emits are labelled `adoption_rehydrate` with
  broker_mutation False so fill counters keyed naively cannot double-count a restart.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.minimal_size import MinimalSizeConfig

F5_NS = "operator"
NOW = datetime(2026, 8, 25, 5, 0, 0, tzinfo=timezone.utc)


class _MT5:
    def __init__(self, bid=100.0, ask=100.02):
        self.bid, self.ask = bid, ask

    def get_tick(self, _symbol):
        return SimpleNamespace(bid=self.bid, ask=self.ask, time=datetime.now(timezone.utc))

    def get_account_balance(self):
        return 100_000.0

    def get_account_equity(self):
        return 100_000.0


class _EE:
    def __init__(self, ticket, direction="LONG", entry=100.0, stop_loss=99.0):
        self.active_trade = SimpleNamespace(
            ticket=ticket, direction=direction, stop_loss=stop_loss,
            entry_price=entry, current_volume=1.0,
        )
        self.closes = []
        self.modifies = []

    def close_position(self, reason):
        self.closes.append(reason)
        self.active_trade = None
        return True

    def _modify_sl(self, ticket, new_sl, *, trade=None, modify_reason=""):
        self.modifies.append((ticket, new_sl, modify_reason))
        return True


def _config(authority=True):
    return {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "gtos_vnext_runtime": {
            "ultimate_book_enabled": True,
            "ultimate_book_apply_to_execution": True,
            "ultimate_book_live_activation_allowed": True,
            "ultimate_book_live_broker_authority": authority,
            "ultimate_book_disable_broad_selector": True,
            "ultimate_book_profile": "clean3_w7_measured_nom1p25",
            "ultimate_book_include_clean3": True,
            "ultimate_book_derisk_mode": "band",
            "ultimate_book_include_candidate_book": False,
            "ultimate_book_include_market_expansion_book": False,
            "ultimate_book_stress_derisk": False,
            "ultimate_book_kelly_lite": True,
            "ultimate_book_kelly_conservative": True,
            "ultimate_book_drop_w7_symbols": True,
            "selector_v4_enabled": True,
            "selector_v4_apply_to_execution": False,
        },
    }


def _owner(tmp_path, namespace=F5_NS, authority=True, mt5=None):
    return UltimateBookOwner(
        _config(authority=authority),
        mt5 or _MT5(),
        str(tmp_path),
        namespace=namespace,
        engine_factory=lambda _symbol: _EE(1),
        minimal_size=MinimalSizeConfig(
            enabled=True, target_risk_usd=250.0, notional_initial_usd=100_000.0,
        ),
    )


def _events(tmp_path, event=None, namespace=F5_NS):
    p = Path(tmp_path) / "shadow_logs" / "f5_minimal" / namespace / "events.jsonl"
    if not p.is_file():
        return []
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    return [r for r in rows if event is None or r["event"] == event]


# ---------------------------------------------------------------------------
# auto-breakeven
# ---------------------------------------------------------------------------
def test_auto_be_locks_fast_family_at_trigger(tmp_path):
    # entry 100, stop 99 (1R = 1.0); bid 101.6 = +1.6R favourable -> stop to entry
    owner = _owner(tmp_path, mt5=_MT5(bid=101.6, ask=101.62))
    ee = _EE(ticket=7, direction="LONG", entry=100.0, stop_loss=99.0)
    owner._exec_engines[("EURUSD", "dsp_walked_high_accepted_through")] = ee
    summary = {}
    owner._f5_auto_breakeven(summary, NOW)
    assert ee.modifies == [(7, 100.0, "f5_auto_breakeven")]
    assert summary.get("f5_auto_breakeven") == 1
    rows = _events(tmp_path, "f5_auto_breakeven")
    assert len(rows) == 1 and rows[0]["status"] == "applied"
    assert rows[0]["broker_mutation"] is True
    # memo: second pass does nothing even at higher excursion
    owner._f5_auto_breakeven({}, NOW)
    assert len(ee.modifies) == 1


def test_auto_be_below_trigger_does_nothing(tmp_path):
    owner = _owner(tmp_path, mt5=_MT5(bid=101.4, ask=101.42))   # +1.4R < 1.5R
    ee = _EE(ticket=8, direction="LONG", entry=100.0, stop_loss=99.0)
    owner._exec_engines[("EURUSD", "dsp_walked_high_accepted_through")] = ee
    owner._f5_auto_breakeven({}, NOW)
    assert ee.modifies == []


def test_auto_be_never_touches_null_rule_sleeves(tmp_path):
    owner = _owner(tmp_path, mt5=_MT5(bid=103.0, ask=103.02))   # +3R, way past trigger
    for sleeve in ("crypto", "energy_agri", "sub_xvol_pullback", "metals_softband",
                   "vol_compression", "mx_btcusd_d1_donchian_20_breakout"):
        ee = _EE(ticket=hash(sleeve) % 10_000 + 10, direction="LONG",
                 entry=100.0, stop_loss=99.0)
        owner._exec_engines[(f"SYM_{sleeve}", sleeve)] = ee
    owner._f5_auto_breakeven({}, NOW)
    for (_, _sleeve), ee in owner._exec_engines.items():
        assert ee.modifies == [], f"null-rule sleeve {_sleeve} was managed"


def test_auto_be_short_uses_ask_and_moves_down(tmp_path):
    # SHORT entry 100, stop 101 (1R = 1.0); ask 98.4 = +1.6R -> stop down to entry
    owner = _owner(tmp_path, mt5=_MT5(bid=98.38, ask=98.4))
    ee = _EE(ticket=9, direction="SHORT", entry=100.0, stop_loss=101.0)
    owner._exec_engines[("GBPUSD", "dsp_walked_high_accepted_through")] = ee
    owner._f5_auto_breakeven({}, NOW)
    assert ee.modifies == [(9, 100.0, "f5_auto_breakeven")]


def test_auto_be_skips_already_risk_free(tmp_path):
    owner = _owner(tmp_path, mt5=_MT5(bid=103.0, ask=103.02))
    ee = _EE(ticket=10, direction="LONG", entry=100.0, stop_loss=100.0)  # at entry already
    owner._exec_engines[("EURUSD", "asian_fade")] = ee
    owner._f5_auto_breakeven({}, NOW)
    assert ee.modifies == []


def test_auto_be_authority_false_suppresses_and_says_so(tmp_path):
    owner = _owner(tmp_path, authority=False, mt5=_MT5(bid=101.6, ask=101.62))
    ee = _EE(ticket=11, direction="LONG", entry=100.0, stop_loss=99.0)
    owner._exec_engines[("EURUSD", "idxrev")] = ee
    owner._f5_auto_breakeven({}, NOW)
    assert ee.modifies == []
    rows = _events(tmp_path, "f5_auto_breakeven")
    assert len(rows) == 1
    assert rows[0]["status"] == "suppressed_live_broker_authority_false"
    assert rows[0]["broker_mutation"] is False


def test_auto_be_is_namespace_gated(tmp_path):
    owner = _owner(tmp_path, namespace="operator_profile",
                   mt5=_MT5(bid=101.6, ask=101.62))
    ee = _EE(ticket=12, direction="LONG", entry=100.0, stop_loss=99.0)
    owner._exec_engines[("EURUSD", "idxrev")] = ee
    owner._f5_auto_breakeven({}, NOW)
    assert ee.modifies == []


# ---------------------------------------------------------------------------
# duplicate-stack dedup
# ---------------------------------------------------------------------------
def test_dup_stack_closes_later_ticket_keeps_first(tmp_path):
    owner = _owner(tmp_path)
    first = _EE(ticket=178425997, direction="LONG", entry=1.16556, stop_loss=1.16505)
    second = _EE(ticket=178427810, direction="LONG", entry=1.16556, stop_loss=1.16505)
    owner._exec_engines[("EURUSD", "dsp_bleed_accept_fresh_20low_second_push")] = first
    owner._exec_engines[("EURUSD", "dsp_close_on_20low_not_a_cascade_then_up")] = second
    summary = {}
    owner._f5_duplicate_stack_dedup(summary)
    assert second.closes == ["f5_duplicate_stack_dedup"]
    assert first.closes == []
    assert summary.get("f5_duplicate_stack_dedup") == 1
    rows = _events(tmp_path, "f5_duplicate_stack_dedup")
    assert len(rows) == 1
    assert rows[0]["ticket"] == 178427810 and rows[0]["kept_ticket"] == 178425997
    assert rows[0]["status"] == "closed" and rows[0]["broker_mutation"] is True


def test_dup_stack_different_stops_are_different_bets(tmp_path):
    owner = _owner(tmp_path)
    a = _EE(ticket=1, direction="LONG", entry=1.16556, stop_loss=1.16505)
    b = _EE(ticket=2, direction="LONG", entry=1.16556, stop_loss=1.16480)
    owner._exec_engines[("EURUSD", "s1")] = a
    owner._exec_engines[("EURUSD", "s2")] = b
    owner._f5_duplicate_stack_dedup({})
    assert a.closes == [] and b.closes == []


def test_dup_stack_opposite_directions_untouched(tmp_path):
    owner = _owner(tmp_path)
    a = _EE(ticket=1, direction="LONG", entry=1.16556, stop_loss=1.16505)
    b = _EE(ticket=2, direction="SHORT", entry=1.16556, stop_loss=1.16607)
    owner._exec_engines[("EURUSD", "s1")] = a
    owner._exec_engines[("EURUSD", "s2")] = b
    owner._f5_duplicate_stack_dedup({})
    assert a.closes == [] and b.closes == []


def test_dup_stack_authority_false_suppresses(tmp_path):
    owner = _owner(tmp_path, authority=False)
    a = _EE(ticket=1, direction="LONG", entry=1.16556, stop_loss=1.16505)
    b = _EE(ticket=2, direction="LONG", entry=1.16556, stop_loss=1.16505)
    owner._exec_engines[("EURUSD", "s1")] = a
    owner._exec_engines[("EURUSD", "s2")] = b
    owner._f5_duplicate_stack_dedup({})
    assert a.closes == [] and b.closes == []
    rows = _events(tmp_path, "f5_duplicate_stack_dedup")
    assert len(rows) == 1
    assert rows[0]["status"] == "suppressed_live_broker_authority_false"


def test_dup_stack_is_namespace_gated(tmp_path):
    owner = _owner(tmp_path, namespace="operator_profile")
    a = _EE(ticket=1, direction="LONG", entry=1.16556, stop_loss=1.16505)
    b = _EE(ticket=2, direction="LONG", entry=1.16556, stop_loss=1.16505)
    owner._exec_engines[("EURUSD", "s1")] = a
    owner._exec_engines[("EURUSD", "s2")] = b
    owner._f5_duplicate_stack_dedup({})
    assert a.closes == [] and b.closes == []


# ---------------------------------------------------------------------------
# fill-truth: sign fallback + adoption emit labelling
# ---------------------------------------------------------------------------
def test_fill_truth_deviation_stamps_without_direction_key(tmp_path):
    """Frozen-commit trade_params carry no 'direction' (178414870): geometry decides."""
    owner = _owner(tmp_path)
    ts = SimpleNamespace(entry_price=4646.9, sl_distance=0.0,
                         stop_loss=4616.39, initial_volume=0.05, current_volume=0.05)
    tp = {"entry_price": 4630.89, "stop_loss": 4616.39, "f5_actual_risk_usd": 72.4}
    owner._f5_fill_truth_fields(tp, {"trade_state": ts})
    # LONG (stop below entry): deviation = (4646.9 - 4630.89) / 14.5 = +1.104 adverse
    assert "f5_fill_deviation_r" in tp
    assert abs(tp["f5_fill_deviation_r"] - (4646.9 - 4630.89) / (4630.89 - 4616.39)) < 1e-9
    assert "f5_actual_risk_at_fill_usd" in tp


def test_adoption_reemit_is_labelled_not_counted_as_fill(tmp_path):
    owner = _owner(tmp_path)
    base = dict(f5_nominal_risk_usd=200.0, f5_intended_risk_usd=250.0,
                f5_actual_risk_usd=250.0)
    owner._f5_on_open(ticket=99, sleeve="idxrev", symbol="JP225",
                      trade_params=dict(base), candidate_id="c1",
                      decision_day="2026-08-25", decision_bar_iso="2026-08-25T04:45:00Z")
    owner._f5_on_open(ticket=99, sleeve="idxrev", symbol="JP225",
                      trade_params=dict(base), candidate_id="c1",
                      decision_day="2026-08-25", decision_bar_iso="2026-08-25T04:45:00Z",
                      source="adoption_rehydrate")
    rows = _events(tmp_path, "f5_fill")
    assert len(rows) == 2
    assert rows[0]["f5_fill_source"] == "fill" and rows[0]["broker_mutation"] is True
    assert rows[1]["f5_fill_source"] == "adoption_rehydrate"
    assert rows[1]["broker_mutation"] is False
