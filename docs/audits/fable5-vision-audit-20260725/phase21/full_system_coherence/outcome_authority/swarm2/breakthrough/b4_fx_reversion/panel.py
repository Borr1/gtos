"""B4 panel loader.

Facts this module encodes, each verified against source before use:

* The deep archive's ``time`` column is BROKER WALL CLOCK, not UTC. Manifest
  evidence: ``AAPL_M15.first == "2014-01-02 16:30:00"`` and the NYSE cash open is
  09:30 New York, so broker == NY + 7 (``src/utils/broker_clock.py``).  Every
  exporter in the archive carries defect F7.
* Broker midnight == 17:00 New York == the FX rollover == the swap charge ==
  the D1 bar boundary.  In UTC that instant is 21:00 (NY on EDT) or 22:00 (NY on
  EST), so a *UTC*-hour session filter smears the rollover across two buckets and
  a *broker*-hour filter isolates it to exactly one.  We work in broker hours and
  convert to UTC only for reporting.
* D1 bar close is therefore the last print before the rollover instant, which is
  the widest-spread minute of the day (Lane 5: 17.6x; ticks: 41x on EURUSD).
  Any close-to-close signal inherits that contamination.  See ``anchor.py``.

Nothing here reaches a broker, the VPS, or any config file.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports"
D1H4 = f"{ROOT}/deep_universe_h4d1_2014_2026"
M15D = f"{ROOT}/deep_universe_m15_2014_2026"
CACHE = "/Users/borr/.claude/jobs/adb9e69b/tmp/b4cache"
os.makedirs(CACHE, exist_ok=True)

REPO = "/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725"
if REPO not in sys.path:
    sys.path.insert(0, REPO)


# --------------------------------------------------------------------------
# broker <-> UTC, US DST calendar (mirrors src/utils/broker_clock.py exactly;
# reimplemented on vectors because the shipped helper is scalar-per-call and we
# convert ~10^7 stamps).
# --------------------------------------------------------------------------
def _nth_weekday(year, month, weekday, n):
    d = date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(days=7 * (n - 1))


def _us_dst_bounds(year):
    """(start, end) of US EDT as *broker-naive* datetimes.

    US DST starts 02:00 local NY on the 2nd Sunday of March, ends 02:00 local NY
    (=01:00 EST) on the 1st Sunday of November.  In broker wall clock (NY+7)
    those are 09:00 and 08:00 respectively.
    """
    s = _nth_weekday(year, 3, 6, 2)   # Sunday == weekday 6
    e = _nth_weekday(year, 11, 6, 1)
    return (datetime(s.year, s.month, s.day, 9, 0),
            datetime(e.year, e.month, e.day, 8, 0))


def broker_offset_hours(idx: pd.DatetimeIndex) -> np.ndarray:
    """+3 while NY is on EDT, +2 while on EST.  Vectorised, no tzdata needed."""
    out = np.full(len(idx), 2, dtype=np.int8)
    yrs = idx.year.values
    for y in np.unique(yrs):
        s, e = _us_dst_bounds(int(y))
        m = (yrs == y) & (idx.values >= np.datetime64(s)) & (idx.values < np.datetime64(e))
        out[m] = 3
    return out


def to_utc(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return idx - pd.to_timedelta(broker_offset_hours(idx), unit="h")


# --------------------------------------------------------------------------
# symbol classification
# --------------------------------------------------------------------------
FX_MAJ = ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "USD",
          "CZK", "DKK", "HUF", "ILS", "MXN", "NOK", "PLN", "SEK", "SGD",
          "TRY", "ZAR", "CNH", "HKD", "THB"]


def classify(sym: str) -> str:
    s = sym.upper()
    if len(s) == 6 and s[:3] in FX_MAJ and s[3:] in FX_MAJ:
        return "fx"
    if s.endswith("USD") and len(s) in (6, 7) and s[:-3] in (
            "BTC", "ETH", "XRP", "LTC", "BCH", "ADA", "DOT", "LNK", "SOL", "DOG",
            "AAV", "ALG", "ATM", "AVA", "AXS", "BAT", "CHZ", "COM", "EOS", "FIL",
            "GRT", "ICP", "MAT", "MKR", "NEA", "SAN", "SHB", "SUS", "THT", "TRX",
            "UNI", "VET", "XLM", "XMR", "XTZ", "ZEC", "ENJ", "MAN", "OMG", "QTM",
            "DSH", "IOT", "NEO", "ETC", "BNB", "APE", "GAL", "LDO", "OPT", "ARB"):
        return "crypto"
    if s in ("XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD") or s.startswith("XAU") or s.startswith("XAG"):
        return "metal"
    if "OIL" in s or s in ("NGAS", "NGAS_cash".upper()) or s.upper().startswith("NG"):
        return "energy"
    if s.endswith("_CASH") or s in ("GER40", "UK100", "JP225", "NAS100", "SPX500", "US30",
                                    "FRA40", "EU50", "AUS200", "HK50", "SUI20", "ESP35",
                                    "NETH25", "US2000", "CHINA50", "SA40", "IT40"):
        return "index"
    return "equity"


def _fx_pair(sym):
    s = sym.upper()
    return (s[:3], s[3:]) if len(s) == 6 else (None, None)


# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------
def list_symbols(tf="D1"):
    d = D1H4 if tf in ("D1", "H4") else M15D
    return sorted(f[: -len(f"_{tf}.csv")] for f in os.listdir(d) if f.endswith(f"_{tf}.csv"))


def load_one(sym, tf="D1"):
    d = D1H4 if tf in ("D1", "H4") else M15D
    p = f"{d}/{sym}_{tf}.csv"
    if not os.path.exists(p):
        return None
    df = pd.read_csv(p, parse_dates=["time"])
    df = df.rename(columns={"time": "bt"})           # bt == broker-naive time
    df = df.drop_duplicates(subset="bt").sort_values("bt").reset_index(drop=True)
    return df


def d1_panel(force=False):
    """Wide close panel on the broker DATE index, plus open/high/low.

    Broker D1 bars are stamped at broker midnight, so the stamp *is* the broker
    trading date and no conversion is needed for alignment.  All FX symbols share
    the same boundary instant, which is precisely why the FX cell is the clean one
    (Lane 5 §2.1 iii) - and precisely why they share the same rollover
    contamination (this lane's §2).
    """
    cp = f"{CACHE}/d1_panel.parquet"
    if os.path.exists(cp) and not force:
        st = pd.read_parquet(cp)
        return st
    frames = []
    for s in list_symbols("D1"):
        df = load_one(s, "D1")
        if df is None or len(df) < 200:
            continue
        df["sym"] = s
        frames.append(df[["bt", "sym", "open", "high", "low", "close", "volume"]])
    st = pd.concat(frames, ignore_index=True)
    st.to_parquet(cp, index=False)
    return st


def m15_syms(symbols, force=False):
    """Long M15 frame for a symbol list, broker time + UTC + broker hour."""
    key = "_".join(sorted(symbols))[:80]
    cp = f"{CACHE}/m15_{abs(hash(key)) % (10**10)}.parquet"
    if os.path.exists(cp) and not force:
        return pd.read_parquet(cp)
    frames = []
    for s in symbols:
        df = load_one(s, "M15")
        if df is None or len(df) < 1000:
            continue
        idx = pd.DatetimeIndex(df["bt"])
        df["off"] = broker_offset_hours(idx)
        df["ut"] = idx - pd.to_timedelta(df["off"].values, unit="h")
        df["bh"] = idx.hour
        df["bmin"] = idx.hour * 60 + idx.minute
        df["bdate"] = idx.normalize()
        df["sym"] = s
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out.to_parquet(cp, index=False)
    return out


# --------------------------------------------------------------------------
# tick-measured spreads (the only tape-true cost instrument on this machine)
# --------------------------------------------------------------------------
TICKROOT = "/Users/borr/GTOSActive/vps-ticks-20260726"


def tick_spread_by_broker_hour(force=False):
    """Median + mean relative spread per (symbol, broker hour) from the tick archive.

    Lane 1 measured this by UTC *session*; the rollover then hides inside a
    seven-hour median.  Per broker hour it is isolable.
    """
    cp = f"{CACHE}/tick_spread_bh.parquet"
    if os.path.exists(cp) and not force:
        return pd.read_parquet(cp)
    import glob
    rows = []
    files = sorted(glob.glob(f"{TICKROOT}/FTMO_*_ticks_*.csv.gz"))
    if not files:
        files = sorted(glob.glob(f"{TICKROOT}/*.csv.gz"))
    for f in files:
        base = os.path.basename(f)
        try:
            d = pd.read_csv(f, compression="gzip", usecols=["time", "bid", "ask"])
        except Exception:
            continue
        sym = base.split("_ticks")[0].replace("FTMO_", "").replace("redacted_account_", "")
        bt = pd.to_datetime(d["time"], unit="s")     # broker wall clock, per .timebase.json
        mid = (d.bid.values + d.ask.values) / 2.0
        sp = (d.ask.values - d.bid.values) / np.where(mid > 0, mid, np.nan)
        g = pd.DataFrame({"bh": bt.dt.hour.values, "sp": sp}).dropna()
        agg = g.groupby("bh")["sp"].agg(["median", "mean", "count", lambda x: x.quantile(0.9)])
        agg.columns = ["med", "mean", "n", "p90"]
        agg["sym"] = sym
        agg["src"] = "FTMO" if base.startswith("FTMO") else "FN"
        rows.append(agg.reset_index())
    out = pd.concat(rows, ignore_index=True)
    out = out.groupby(["sym", "src", "bh"], as_index=False).apply(
        lambda d: pd.Series({"med": np.average(d["med"], weights=d["n"]),
                             "mean": np.average(d["mean"], weights=d["n"]),
                             "p90": np.average(d["p90"], weights=d["n"]),
                             "n": d["n"].sum()}), include_groups=False)
    out.to_parquet(cp, index=False)
    return out


if __name__ == "__main__":
    st = d1_panel()
    print("D1 panel rows", len(st), "symbols", st.sym.nunique(),
          "dates", st.bt.min(), "->", st.bt.max())
