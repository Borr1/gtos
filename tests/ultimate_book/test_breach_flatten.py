"""MACRO-EMRG-03 open-position breach FLATTEN + adopt-by-ledger orphan recovery.

The governor's soft/hard daily stops and DD de-risk band are ENTRY-side only. This covers the missing
LAST-RESORT tier: flatten OPEN positions + latch new entries off near the prop-fatal daily-loss / static
max-DD floor, with hysteresis and fail-safe-on-uncertain-data. Plus the adopt-by-ledger fix so the book
manages its OWN ledger-recorded positions even when a legacy comment blocks comment-routing.
"""
import tempfile
from datetime import datetime, timezone

from src.components.ultimate_book.admission import GovernorState
from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.placement_ledger import PlacementLedger


def _gs(realized_pct=0.0, equity=100000.0, ref=100000.0):
    return GovernorState(equity=equity, high_water=equity, realized_today_pct=realized_pct,
                         open_risk_pct=0.0, operator_circuit_breaker=False, max_dd_reference_equity=ref)


class _FakeMT5:
    def get_account_equity(self):
        return 100000.0

    def get_account_balance(self):
        return 100000.0


def _runtime(**over):
    rt = {"ultimate_book_enabled": True, "ultimate_book_apply_to_execution": True,
          "ultimate_book_live_activation_allowed": True,
          # Fourth authority gate, merged from the VPS live-hardening lineage
          # 2026-07-26. It defaults False, and with it false the book observes a
          # breach and refuses ANY broker mutation -- including the flatten itself --
          # logging "no broker mutation; new entries OFF". These tests exercise what
          # flatten DOES once authorised, so they must arm it; the gate's own
          # fail-closed behaviour is covered separately.
          "ultimate_book_live_broker_authority": True,
          "ultimate_book_flatten_on_breach": True,
          "ultimate_book_flatten_daily_loss_pct": 0.04, "ultimate_book_flatten_maxdd_pct": 0.09,
          "ultimate_book_flatten_confirm_ticks": 2}
    rt.update(over)
    return {"gtos_vnext_runtime": rt}


def _owner(**over):
    return UltimateBookOwner(_runtime(**over), _FakeMT5(), tempfile.mkdtemp())


def _verdict(owner, gs):
    owner.engine.compute_governor_state = lambda now_utc=None: gs
    return owner.engine.breach_flatten_check()


# ---------------- engine.breach_flatten_check verdict logic ----------------
def test_disabled_returns_none():
    assert _verdict(_owner(ultimate_book_flatten_on_breach=False), _gs(realized_pct=-0.10)) is None


def test_unassessable_returns_none():
    assert _verdict(_owner(), None) is None        # gs None (bad data) -> never flatten


def test_daily_loss_triggers():
    v = _verdict(_owner(), _gs(realized_pct=-0.045))
    assert v["flatten"] and v["block_entries"] and "daily" in v["reason"]


def test_daily_within_threshold_no_flatten():
    assert _verdict(_owner(), _gs(realized_pct=-0.03))["flatten"] is False   # soft-stop zone, not flatten


def test_maxdd_triggers():
    v = _verdict(_owner(), _gs(equity=90500.0, ref=100000.0))   # dd = 9.5% >= 9%
    assert v["flatten"] and "maxDD" in v["reason"]


def test_maxdd_within_threshold_no_flatten():
    assert _verdict(_owner(), _gs(equity=92000.0, ref=100000.0))["flatten"] is False   # dd 8% < 9%


# ---------------- owner _apply_breach_flatten: hysteresis + flatten + latch ----------------
class _FakeEE:
    def __init__(self):
        self.active_trade = object()
        self.closed = None

    def close_position(self, reason):
        self.closed = reason
        self.active_trade = None
        return True


def test_hysteresis_then_flatten_and_latch():
    owner = _owner()
    ee = _FakeEE()
    owner._exec_engines = {("GER40", "idxrev"): ee}
    owner.engine.breach_flatten_check = lambda now_utc=None: {
        "flatten": True, "block_entries": True, "reason": "daily -4.50% <= -4.0%",
        "metrics": {"equity": 96000.0}}
    summary = {"closed": [], "errors": []}
    owner._apply_breach_flatten(None, summary)            # tick 1 -> confirm=2 not reached
    assert ee.active_trade is not None and owner._breach_block is False and owner._breach_ticks == 1
    owner._apply_breach_flatten(None, summary)            # tick 2 -> FLATTEN + latch
    assert ee.active_trade is None and ee.closed == "vnext_breach_flatten"
    assert owner._breach_block is True
    assert any(c.get("action") == "breach_flatten" for c in summary["closed"])


def test_operator_flatten_flag():
    import os
    owner = _owner()
    ee = _FakeEE()
    owner._exec_engines = {("GER40", "idxrev"): ee}
    base = os.path.join(owner._repo_root, "pipeline_state")
    os.makedirs(base, exist_ok=True)
    flag = os.path.join(base, "ULTIMATE_BOOK_FLATTEN.flag")
    with open(flag, "w") as f:
        f.write("flatten")
    summary = {"closed": [], "errors": []}
    owner._apply_breach_flatten(None, summary)         # immediate, no hysteresis
    assert ee.active_trade is None and ee.closed == "vnext_operator_flatten"
    assert owner._breach_block is True
    assert any(c.get("action") == "operator_flatten" for c in summary["closed"])
    # remove the flag + no governor breach -> placement resumes
    os.remove(flag)
    owner.engine.breach_flatten_check = lambda now_utc=None: {"flatten": False, "block_entries": False,
                                                              "reason": None, "metrics": {}}
    owner._apply_breach_flatten(None, {"closed": [], "errors": []})
    assert owner._breach_block is False


def test_latch_clears_when_breach_resolves():
    owner = _owner()
    owner._breach_block = True
    owner._breach_alerted = True
    owner._breach_ticks = 5
    owner.engine.breach_flatten_check = lambda now_utc=None: {
        "flatten": False, "block_entries": False, "reason": None, "metrics": {}}
    owner._apply_breach_flatten(None, {"closed": [], "errors": []})
    assert owner._breach_block is False and owner._breach_ticks == 0


def test_unassessable_leaves_latch_untouched():
    owner = _owner()
    owner._breach_block = True
    owner.engine.breach_flatten_check = lambda now_utc=None: None
    owner._apply_breach_flatten(None, {"closed": [], "errors": []})
    assert owner._breach_block is True       # FAIL-SAFE: never unblock on uncertain data


def test_run_cycle_observe_only_when_breached():
    owner = _owner()
    owner._breach_block = True

    class _D:
        would_units = []
        realized_units = []

    owner.engine.evaluate = lambda **kw: {"ok": True, "decision": _D(), "intents": [], "meta": [],
                                          "governor_state": None, "n_intents": 0,
                                          "runtime_effect_now": True, "reason": "admitted"}
    s = owner.run_cycle(place=True)
    assert "breach_flatten_block" in s["skipped"] and s["placed"] == []


# ---------------- adopt-by-ledger ticket index ----------------
def test_ledger_ticket_index_recovers_book_placed():
    d = tempfile.mkdtemp()
    led = PlacementLedger(d, "ns_test")
    led.record("vp_euidx_pocgrav", "GER40", "2026-06-14T21:00:00+00:00", ticket=158716676, ts="t")
    assert led.sleeve_symbol_for_ticket(158716676) == ("vp_euidx_pocgrav", "GER40")
    assert led.sleeve_symbol_for_ticket(999999) is None          # a foreign ticket stays foreign
    # durable: a fresh ledger (post-restart) rebuilds the index from disk
    assert PlacementLedger(d, "ns_test").sleeve_symbol_for_ticket(158716676) == ("vp_euidx_pocgrav", "GER40")


# ---------------- bar-age gate: no restart-late chase entries ----------------
def test_entry_too_late_gate():
    O = UltimateBookOwner._entry_too_late
    H4, M15 = 16388, 15   # _TF_MINUTES: 240 / 15
    h4_open = datetime(2026, 6, 15, 8, 0, tzinfo=timezone.utc)        # H4 bar closes 12:00
    h4_iso = h4_open.isoformat()
    assert O(datetime(2026, 6, 15, 12, 2, tzinfo=timezone.utc), h4_iso, H4, 0.5) is False   # 2m late -> timely
    assert O(datetime(2026, 6, 15, 14, 30, tzinfo=timezone.utc), h4_iso, H4, 0.5) is True    # 150m > 120m -> chase
    m15_open = datetime(2026, 6, 16, 2, 0, tzinfo=timezone.utc)       # M15 bar closes 02:15
    assert O(datetime(2026, 6, 16, 2, 18, tzinfo=timezone.utc), m15_open.isoformat(), M15, 0.5) is False  # 3m
    assert O(datetime(2026, 6, 16, 2, 25, tzinfo=timezone.utc), m15_open.isoformat(), M15, 0.5) is True   # 10m>7.5
    # FAIL-OPEN: unknown timeframe / missing bar must never block a live entry
    assert O(datetime(2026, 6, 15, 14, 30, tzinfo=timezone.utc), h4_iso, 99999, 0.5) is False
    assert O(datetime(2026, 6, 15, 14, 30, tzinfo=timezone.utc), None, H4, 0.5) is False
