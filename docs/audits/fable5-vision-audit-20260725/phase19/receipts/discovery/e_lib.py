"""e_lib -- shared machinery for lane e-stack (do the levers ADD UP?).

Two things live here so January / February / March are scored by IDENTICAL code:

  1. CONTRACTS -- the exit menu, walked honestly on an R path with a given fill start.
  2. real_cost_r -- the broker-true cost model, ported verbatim from l10's
     l10x_06_recost.py so the cost basis is the same object l10 measured.

SIGN CONVENTION (inherited from w0_ws): every *_r is signed for the trade's own side.
fav = best excursion in the bar, adv = worst. The stop sits at -1.0R by construction.

FILL HONESTY: a trade only exists from the first bar where price traded at/through
entry_price (adv <= 0). Everything before that bar is unreachable by a resting limit.

TIE RULE: if stop and target are both reachable inside one M1 bar, the STOP is taken.

TRAIL HONESTY (l11 S5): a stop armed or tightened at bar i is only CHECKED from bar
i+1. Booking the trail level on the same bar that set it manufactures ~0.36 R/trade.
"""
from __future__ import annotations

# --------------------------------------------------------------- exit menu
# name -> (target_r, stop_r, trail_r, max_bars, has_defined_risk)
# max_bars is an ABSOLUTE 1-based path-bar index (bars are minutes from the decision).
CONTRACTS = {
    "INC":        (2.0,  -1.0, None, None, True),   # the shipped 2R / -1R contract
    "T3S1":       (3.0,  -1.0, None, None, True),
    "T5S2":       (5.0,  -2.0, None, None, True),
    "STOPONLY":   (None, -1.0, None, None, True),
    "T2S1M90":    (2.0,  -1.0, None, 90,   True),
    "TRAIL025":   (None, -1.0, 0.25, None, True),
    "TRAIL050":   (None, -1.0, 0.50, None, True),
    "TS30S1":     (None, -1.0, None, 30,   True),
    "TS60S1":     (None, -1.0, None, 60,   True),
    "TS90S1":     (None, -1.0, None, 90,   True),
    "TS90S2":     (None, -2.0, None, 90,   True),
    "TS90S3":     (None, -3.0, None, 90,   True),
    "TS90":       (None, None, None, 90,   False),  # no stop -- risk undefined
    "TS60":       (None, None, None, 60,   False),
    "HOLD":       (None, None, None, None, False),
}
STOPBEARING = [k for k, v in CONTRACTS.items() if v[4]]


def first_touch(adv, min_bar0=0):
    """0-based index of the first bar at/after min_bar0 where price traded at/through
    entry (adv <= 0). None if the limit is never touched."""
    for i in range(min_bar0, len(adv)):
        if adv[i] <= 1e-12:
            return i
    return None


def walk(fav, adv, cls, start, target_r, stop_r, trail_r, max_bars):
    """Honest first-touch walk from 0-based bar `start`. Returns (r, reason, exit_bar1)."""
    n = len(fav)
    last = min(n, max_bars) if max_bars else n
    if start is None or last <= start:
        return (0.0, "no_fill", None)
    stop = stop_r
    peak = -1e18
    for i in range(start, last):
        f, a = fav[i], adv[i]
        if stop is not None and a <= stop + 1e-12:
            return (stop, "stop", i + 1)
        if target_r is not None and f >= target_r - 1e-12:
            return (target_r, "target", i + 1)
        if f > peak:
            peak = f
        if trail_r is not None and peak >= trail_r:
            ns = peak - trail_r
            stop = ns if stop is None else max(stop, ns)
    j = last - 1
    return (cls[j], ("time_stop" if max_bars and n > last else "path_end"), last)


# --------------------------------------------------------- broker-true cost
# Ported verbatim from l10_scripts/l10x_06_recost.py (lane l10-broker-truth, X5/X6).
JPYCOMM = 0.00808905
USDCOMM = 5.00048e-05
_COMM = {
    "EURUSD": USDCOMM, "GBPUSD": USDCOMM, "AUDUSD": USDCOMM, "NZDUSD": USDCOMM,
    "USDJPY": JPYCOMM, "GBPJPY": JPYCOMM, "EURJPY": JPYCOMM, "AUDJPY": JPYCOMM,
    "CHFJPY": JPYCOMM, "XAUUSD": 0.0576, "XAGUSD": 0.001,
    "UK100": 0.0, "SPX500": 0.0, "NAS100": 0.0, "US30_cash": 0.0, "GER40": 0.0,
    "JP225": 0.0, "UKOIL_cash": 0.0, "USOIL_cash": 0.0,
}
_CRYPTO_BPS = {"BTCUSD": 39.2778 / 88599.74 * 1e4}
TMAP = {"XAUUSD": "XAUUSD", "UK100": "UK100_cash", "SPX500": "US500_cash",
        "NAS100": "US100_cash", "US30_cash": "US30_cash", "GBPUSD": "GBPUSD",
        "GER40": "GER40_cash", "JP225": "JP225_cash", "USDCAD": "USDCAD",
        "BTCUSD": "BTCUSD", "EURJPY": "EURJPY", "ETHUSD": "ETHUSD", "XAGUSD": "XAGUSD",
        "USDCHF": "USDCHF", "USDJPY": "USDJPY", "EURGBP": "EURGBP", "NZDUSD": "NZDUSD",
        "EURUSD": "EURUSD", "UKOIL_cash": "UKOIL_cash", "GBPJPY": "GBPJPY",
        "AUDJPY": "AUDJPY", "USOIL_cash": "USOIL_cash", "AUDUSD": "AUDUSD",
        "CHFJPY": "CHFJPY"}
SLIPMAP = {"XAUUSD": "ftmo:XAUUSD", "SPX500": "ftmo:US500.cash", "US30_cash": "ftmo:US30.cash",
           "UK100": "ftmo:UK100.cash", "GER40": "ftmo:GER40.cash", "JP225": "ftmo:JP225.cash",
           "BTCUSD": "ftmo:BTCUSD", "ETHUSD": "ftmo:ETHUSD", "EURUSD": "ftmo:EURUSD",
           "GBPUSD": "ftmo:GBPUSD", "USDJPY": "ftmo:USDJPY", "GBPJPY": "ftmo:GBPJPY"}


def real_cost_parts(sym, entry_price, risk_distance, tick, live):
    """(real_spread_r, real_comm_r, real_slip_r) or None if the symbol has no tick truth."""
    tk = tick.get("ftmo:" + TMAP.get(sym, sym))
    if not tk or not tk.get("spread_bps_median"):
        return None
    sp_px = tk["spread_bps_median"] * entry_price / 1e4
    if sym in _CRYPTO_BPS:
        cm = _CRYPTO_BPS[sym] * entry_price / 1e4
    elif sym == "ETHUSD":
        cm = 1.09905
    elif sym in ("USDCHF", "USDCAD"):
        cm = USDCOMM * entry_price
    elif sym == "EURGBP":
        cm = USDCOMM * 0.74
    else:
        cm = _COMM.get(sym, 0.0)
    sl_px = live.get(SLIPMAP.get(sym, ""), {}).get("slip_px")
    sl_px = max(sl_px, 0.0) if sl_px is not None else 0.0
    d = risk_distance
    return (sp_px / d, cm / d, sl_px / d)


# ------------------------------------------------------------------- stats
def mean(v):
    return sum(v) / len(v) if v else None


def q(v, p):
    if not v:
        return None
    s = sorted(v)
    i = max(0, min(len(s) - 1, int(round(p * (len(s) - 1)))))
    return s[i]


def se(v):
    n = len(v)
    if n < 2:
        return None
    m = sum(v) / n
    return (sum((x - m) ** 2 for x in v) / (n - 1) / n) ** 0.5
