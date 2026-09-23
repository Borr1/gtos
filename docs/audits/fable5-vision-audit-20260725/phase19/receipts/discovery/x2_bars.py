"""x2 shared bar loading: M15 and M1 (true-UTC lane hold), January 2026."""
import csv, os, datetime as dt, bisect

BARROOT = "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars"
M15DIR = os.path.join(BARROOT, "bridge_ftmo_m15_20250601_20260610")

def _parse(ts):
    return dt.datetime.fromisoformat(ts)

def load_m15(symbol):
    p = os.path.join(M15DIR, f"{symbol}_M15.csv")
    out = []
    with open(p, newline="") as fh:
        for r in csv.reader(fh):
            if r[0] == "time":
                continue
            out.append((_parse(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])))
    out.sort(key=lambda x: x[0])
    return out

def load_m1(symbol, months=("202512", "202601", "202602")):
    out = []
    for m in months:
        p = os.path.join(BARROOT, f"bridge_ftmo_m1_{m}", f"{symbol}_M1.csv")
        if not os.path.isfile(p):
            continue
        with open(p, newline="") as fh:
            for r in csv.reader(fh):
                if r[0] == "time":
                    continue
                out.append((_parse(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])))
    out.sort(key=lambda x: x[0])
    return out

def index_by_time(bars):
    return {b[0]: i for i, b in enumerate(bars)}

SYMBOLS = ["AUDJPY","AUDUSD","BTCUSD","CHFJPY","ETHUSD","EURGBP","EURJPY","EURUSD","GBPJPY","GBPUSD",
           "GER40","JP225","NAS100","NZDUSD","SPX500","UK100","UKOIL_cash","US30_cash","USDCAD",
           "USDCHF","USDJPY","USOIL_cash","XAGUSD","XAUUSD"]


# --------------------------------------------------------------------------------------
# Compatibility API for the earlier x2 attempt's scripts (x2_earliness.py,
# x2_early_entry_walk.py).  Their x2_bars.py was overwritten by this file during the
# second x2 session; these four functions restore the exact surface they call.
# Shapes: bars are (datetime, o, h, l, c, v) tuples; `times` is the parallel list of
# datetimes for bisect.
# --------------------------------------------------------------------------------------
from bisect import bisect_left as _bl

_M15_CACHE: dict = {}
_M1_CACHE: dict = {}


def m15(symbol):
    """(bars, times) for the symbol's whole M15 history."""
    if symbol not in _M15_CACHE:
        b = load_m15(symbol)
        _M15_CACHE[symbol] = (b, [x[0] for x in b])
    return _M15_CACHE[symbol]


def m1(symbol, months=("202512", "202601", "202602")):
    """(bars, times) for the symbol's M1 history over `months`."""
    key = (symbol, months)
    if key not in _M1_CACHE:
        b = load_m1(symbol, months)
        _M1_CACHE[key] = (b, [x[0] for x in b])
    return _M1_CACHE[key]


def m15_index_for_decision(symbol, decision_utc):
    """Index of the M15 bar that PRODUCED a decision at `decision_utc`
    (its open is decision_utc - 15 min).  None when absent."""
    if isinstance(decision_utc, str):
        decision_utc = _parse(decision_utc)
    bars, times = m15(symbol)
    want = decision_utc - dt.timedelta(minutes=15)
    k = _bl(times, want)
    return k if k < len(times) and times[k] == want else None


def m1_slice(symbol, start, end):
    """M1 bars with start <= time < end."""
    if isinstance(start, str):
        start = _parse(start)
    if isinstance(end, str):
        end = _parse(end)
    bars, times = m1(symbol)
    a = _bl(times, start)
    b = _bl(times, end)
    return bars[a:b]
