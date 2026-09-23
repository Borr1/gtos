"""Session CF (CF-2) — what a broker rename does to a position that is ALREADY OPEN.

The commission asked whether the canonical->broker alias should also cover position adoption and
exit management, on the theory that "a position opened under an old name is still managed after a
rename mid-hold — that gap is worse than the generation gap and today it is untested."

Measured here, and the answer has two halves that point opposite ways:

  * the gap is REAL. `_open_book_positions_by_canonical` (`book_owner.py:3063-3071`) builds its
    broker->canonical map from the CURRENT profile, so a position still carrying the old broker
    name matches no canonical symbol, reaches neither the per-pair route nor the leftover safety
    net at `:2290`, and is therefore not adopted and not exit-managed;

  * but it is NOT silent, which is the half the premise got backwards. `_alert_out_of_universe`
    (`:2353-2385`) exists for exactly this shape — a W7-magic position whose broker symbol is not
    in the currently-resolved manageable set — and it fires a log warning, an operator card and a
    `summary["out_of_universe"]` row, once per ticket. So the adoption path already had the
    detection the GENERATION path lacked entirely, which is the reverse of the assumed asymmetry.

Consequence for the design (stated, not silently implemented): the alias must NOT be extended to
adoption. Making an old broker name resolve again would have the book manage a position on a
symbol the terminal no longer serves — every `get_tick(old_name)` fails, so trail/BE/TP edits and
the time stop would run against absent prices. Per CLAUDE.md H8 the broker-side SL/TP set at entry
(`execution.py:3488`) survives regardless, so such a position rides its hard stop rather than
being naked. The correct response is the operator ceremony the alert exists to trigger.
"""
from datetime import datetime, timezone

from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.mt5.mt5_interface import MAGIC_NUMBER

OLD_BROKER_NAME = "US500.old"      # what the position was opened under, pre-rename
NEW_BROKER_NAME = "US500.cash"     # what the profile resolves SPX500 to now
SLEEVE = "sub_xvol_pullback"


class _Pos:
    def __init__(self, ticket, symbol, comment):
        self.ticket = ticket
        self.symbol = symbol
        self.comment = comment
        self.magic = MAGIC_NUMBER
        self.volume = 0.1
        self.type = 0
        self.price_open = 5000.0
        self.sl = 4900.0
        self.tp = 5200.0
        self.profit = 0.0
        self.swap = 0.0


class _MT5:
    def __init__(self, positions):
        self._positions = positions

    def get_open_positions(self):
        return list(self._positions)

    def broker_link_connected(self):
        return True

    def get_tick(self, symbol):
        raise RuntimeError(f"{symbol} is not served by this terminal")

    def get_candles(self, symbol, tf, count):
        return []

    def get_account_balance(self):
        return 100000.0

    def get_account_equity(self):
        return 100000.0


def _cfg():
    return {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "instruments": {
            "SPX500": {"market": {"mt5_symbol": NEW_BROKER_NAME}},
            "XAUUSD": {"market": {"mt5_symbol": "XAUUSD"}},
        },
        "gtos_vnext_runtime": {
            "ultimate_book_enabled": True,
            "ultimate_book_apply_to_execution": True,
            "ultimate_book_live_activation_allowed": True,
            "ultimate_book_live_broker_authority": True,
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


def _run(tmp_path, symbol):
    owner = UltimateBookOwner(_cfg(), _MT5([_Pos(4242, symbol, f"W7:{SLEEVE}"[:16])]),
                              str(tmp_path), namespace="operator_profile")
    owner._send_card = lambda *_a, **_k: None
    return owner.manage_open_positions(now_utc=datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc))


def test_position_under_the_OLD_broker_name_is_not_adopted_but_IS_alarmed(tmp_path):
    summary = _run(tmp_path, OLD_BROKER_NAME)

    oou = summary.get("out_of_universe") or []
    assert [r["ticket"] for r in oou] == [4242], (
        "a W7 position on a symbol no active sleeve resolves to must raise the out-of-universe "
        "alert — this is the detection the generation path does not have")
    assert oou[0]["symbol"] == OLD_BROKER_NAME

    assert not any(r.get("ticket") == 4242 for r in (summary.get("adopted") or [])), (
        "the gap is real: the old broker name matches no canonical symbol, so the position is "
        "never adopted into an engine and gets no time stop, scale-out, trail or breach-flatten")


def test_the_same_position_under_the_CURRENT_broker_name_raises_no_alarm(tmp_path):
    """Control — the alert keys on resolution, not on the ticket being unusual."""
    summary = _run(tmp_path, NEW_BROKER_NAME)
    assert not (summary.get("out_of_universe") or [])


def test_reverse_map_is_built_from_the_current_profile_only(tmp_path):
    """The mechanism, isolated: broker->canonical carries no memory of previous broker names."""
    owner = UltimateBookOwner(_cfg(), _MT5([]), str(tmp_path),
                              namespace="operator_profile")
    stale = _Pos(1, OLD_BROKER_NAME, f"W7:{SLEEVE}"[:16])
    fresh = _Pos(2, NEW_BROKER_NAME, f"W7:{SLEEVE}"[:16])

    by_canon = owner._open_book_positions_by_canonical(
        ["SPX500"], open_positions_snapshot=[stale, fresh])

    assert [p.ticket for p in by_canon.get("SPX500", [])] == [2]
    assert all(stale not in v for v in by_canon.values())
