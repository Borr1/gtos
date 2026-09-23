"""pbg_econ — the M1 tape, the walker and the broker-true cost model.

Conventions (the estate's, restated so they can be checked):

* An M1 bar stamped ``T`` covers ``[T, T+1min)`` and closes at ``T+1min``.
* A market order sent at instant ``D`` fills at the close of stamp ``D-1`` —
  the last print strictly before D.  (x3 §5b proved this equals the pool's own
  ``entry_price`` at 0.0 relative error on 14,911/14,911 at-market rows.)
* The forward path is stamps ``D+1 .. D+HORIZON`` by default (the sealed
  sidecar's convention).  ``include_fill_minute=True`` adds stamp ``D`` — x3
  §5a measured that omitting it flatters the shipped contract by 0.003 R.
* Tie rule: if the target and the stop are both reachable inside the same M1
  bar, the STOP wins (M1 OHLC carries no intrabar ordering).

Cost model: the h1 four-term broker-true basis (hour-aware tick spread +
broker-true commission + measured price-unit slippage + swap on broker-midnight
crossings), charged once, in price units, then divided by the arm's own risk
distance to give R.  Sources are the committed lane artifacts, named below.
"""

from __future__ import annotations

import gzip
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

import pbg_lib as L  # noqa: E402

DISC = HERE.parent / "discovery"
BROKER_TRUE = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase17"
    / "activation_carry_live_cost_truth/files/BROKER_TRUE_COSTS_V1.json"
)

HORIZON = 120


# ------------------------------------------------------------------ M1 tape


class Tape:
    """Minute-indexed OHLC arrays for one month-set, one symbol each."""

    def __init__(self, symbols, months):
        self.t0 = datetime.fromisoformat(
            f"{months[0][:4]}-{months[0][4:]}-01T00:00:00+00:00"
        )
        last = months[-1]
        y, m = int(last[:4]), int(last[4:])
        y2, m2 = (y + 1, 1) if m == 12 else (y, m + 1)
        self.t1 = datetime(y2, m2, 1, tzinfo=timezone.utc)
        self.n = int((self.t1 - self.t0).total_seconds() // 60)
        self.o, self.h, self.l, self.c = {}, {}, {}, {}
        for sym in symbols:
            o = np.full(self.n, np.nan)
            hi = np.full(self.n, np.nan)
            lo = np.full(self.n, np.nan)
            cl = np.full(self.n, np.nan)
            for mm in months:
                p = L.m1_dir(mm) / f"{sym}_M1.csv"
                if not p.is_file():
                    continue
                for row in L.read_csv_bars(p):
                    ts = datetime.fromisoformat(row["time_utc"])
                    i = int((ts - self.t0).total_seconds() // 60)
                    if 0 <= i < self.n:
                        o[i] = row["open"]
                        hi[i] = row["high"]
                        lo[i] = row["low"]
                        cl[i] = row["close"]
            self.o[sym], self.h[sym], self.l[sym], self.c[sym] = o, hi, lo, cl

    def idx(self, iso: str) -> int:
        return int(
            (datetime.fromisoformat(iso) - self.t0).total_seconds() // 60
        )

    def last_close_before(self, sym: str, i: int) -> float:
        """Close of stamp i-1 — the price a market order sent at stamp i gets."""
        c = self.c[sym]
        j = i - 1
        if j < 0:
            return math.nan
        v = c[j]
        return float(v)


def walk(
    tape: Tape,
    sym: str,
    i: int,
    *,
    entry: float,
    stop: float,
    long: bool,
    target_r: float = 2.0,
    horizon: int = HORIZON,
    include_fill_minute: bool = False,
):
    """Return (r, exit_reason, exit_bar, bars_used)."""
    d = abs(entry - stop)
    if not (d > 0):
        return None
    tgt = entry + target_r * d if long else entry - target_r * d
    a = i if include_fill_minute else i + 1
    b = min(a + horizon, tape.n)
    if a >= b:
        return None
    hi = tape.h[sym][a:b]
    lo = tape.l[sym][a:b]
    cl = tape.c[sym][a:b]
    ok = ~np.isnan(cl)
    if not ok.any():
        return None
    hi = hi[ok]
    lo = lo[ok]
    cl = cl[ok]
    if long:
        hit_t = hi >= tgt
        hit_s = lo <= stop
    else:
        hit_t = lo <= tgt
        hit_s = hi >= stop
    it = int(np.argmax(hit_t)) if hit_t.any() else None
    iss = int(np.argmax(hit_s)) if hit_s.any() else None
    if iss is not None and (it is None or iss <= it):
        return (-1.0, "stop", iss + 1, len(cl))
    if it is not None:
        return (float(target_r), "target", it + 1, len(cl))
    last = float(cl[-1])
    r = (last - entry) / d if long else (entry - last) / d
    return (r, "path_end", len(cl), len(cl))


def walk_limit(
    tape: Tape,
    sym: str,
    i: int,
    *,
    entry: float,
    stop: float,
    long: bool,
    target_r: float = 2.0,
    horizon: int = HORIZON,
):
    """Honest resting-limit contract for POI candidates.

    The order rests at ``entry`` from stamp i.  It fills on the first bar whose
    range contains ``entry``; the walk then starts at the NEXT bar (no same-bar
    credit).  Never filled inside the horizon -> ``no_fill``, booking 0.0 R,
    because you did not trade and you lost nothing.
    """
    d = abs(entry - stop)
    if not (d > 0):
        return None
    a = i
    b = min(a + horizon, tape.n)
    if a >= b:
        return None
    hi = tape.h[sym][a:b]
    lo = tape.l[sym][a:b]
    ok = ~np.isnan(hi)
    if not ok.any():
        return None
    idxs = np.nonzero(ok)[0]
    touched = (lo[idxs] <= entry) & (hi[idxs] >= entry)
    if not touched.any():
        return (0.0, "no_fill", None, int(ok.sum()))
    j = int(idxs[int(np.argmax(touched))])
    res = walk(
        tape, sym, a + j, entry=entry, stop=stop, long=long,
        target_r=target_r, horizon=horizon - j - 1,
    )
    if res is None:
        return (0.0, "no_fill", None, 0)
    return (res[0], res[1], res[2], res[3])


# ------------------------------------------------------------------- costs


class CostModel:
    """h1 four-term broker-true cost, in PRICE units, per (symbol, instant, side)."""

    def __init__(self):
        from src.utils.broker_clock import resolve_rule, utc_to_broker_naive

        self._resolve = resolve_rule
        self._to_broker = utc_to_broker_naive
        self.server = resolve_rule("FTMO-Server3")
        self.tick = json.load(open(DISC / "L10X_TICK_SPREAD_V1.json"))
        self.live = json.load(open(DISC / "L10X_LIVE_COST_PRICEUNITS_V1.json"))
        self.bt = json.load(open(BROKER_TRUE))["accounts"]["FTMO"]["instruments"]
        self.tmap = {
            "XAUUSD": "XAUUSD", "UK100": "UK100_cash", "SPX500": "US500_cash",
            "NAS100": "US100_cash", "US30_cash": "US30_cash", "GBPUSD": "GBPUSD",
            "GER40": "GER40_cash", "JP225": "JP225_cash", "USDCAD": "USDCAD",
            "BTCUSD": "BTCUSD", "EURJPY": "EURJPY", "ETHUSD": "ETHUSD",
            "XAGUSD": "XAGUSD", "USDCHF": "USDCHF", "USDJPY": "USDJPY",
            "EURGBP": "EURGBP", "NZDUSD": "NZDUSD", "EURUSD": "EURUSD",
            "UKOIL_cash": "UKOIL_cash", "GBPJPY": "GBPJPY", "AUDJPY": "AUDJPY",
            "USOIL_cash": "USOIL_cash", "AUDUSD": "AUDUSD", "CHFJPY": "CHFJPY",
        }
        self.bmap = {
            "XAUUSD": "XAUUSD", "SPX500": "US500.cash", "NAS100": "US100.cash",
            "US30_cash": "US30.cash", "UK100": "UK100.cash", "GER40": "GER40.cash",
            "JP225": "JP225.cash", "BTCUSD": "BTCUSD", "ETHUSD": "ETHUSD",
            "XAGUSD": "XAGUSD", "USDJPY": "USDJPY", "GBPUSD": "GBPUSD",
            "USDCAD": "USDCAD", "USDCHF": "USDCHF", "NZDUSD": "NZDUSD",
            "UKOIL_cash": "UKOIL.cash", "EURUSD": "EURUSD",
            "USOIL_cash": "USOIL.cash", "GBPJPY": "GBPJPY", "EURGBP": "EURGBP",
            "AUDJPY": "AUDJPY", "EURJPY": "EURJPY", "AUDUSD": "AUDUSD",
            "CHFJPY": "CHFJPY",
        }
        self.slipmap = {
            "XAUUSD": "ftmo:XAUUSD", "SPX500": "ftmo:US500.cash",
            "US30_cash": "ftmo:US30.cash", "UK100": "ftmo:UK100.cash",
            "GER40": "ftmo:GER40.cash", "JP225": "ftmo:JP225.cash",
            "BTCUSD": "ftmo:BTCUSD", "ETHUSD": "ftmo:ETHUSD",
            "EURUSD": "ftmo:EURUSD", "GBPUSD": "ftmo:GBPUSD",
            "USDJPY": "ftmo:USDJPY", "GBPJPY": "ftmo:GBPJPY",
        }
        self.slip_bps = self._build_slip()
        self._hour_cache = {}

    # -- slippage: measured price-unit bps where measured, class median else
    def _build_slip(self):
        """Exactly h1_01_cost_rows.build_slip_table: measured price-unit slippage
        over the broker's own mid_price_median, class median where unmeasured."""
        out, by_class = {}, defaultdict(list)
        for sym in self.tmap:
            rec = self.bt.get(self.bmap.get(sym, sym)) or {}
            klass = rec.get("instrument_class")
            key = self.slipmap.get(sym)
            px = (self.live.get(key) or {}).get("slip_px") if key else None
            mid = (rec.get("spread_price") or {}).get("mid_price_median")
            if px is not None and mid:
                bps = max(float(px), 0.0) / float(mid) * 1e4
                out[sym] = ("MEASURED_LIVE_DEALS", bps)
                by_class[klass].append(bps)
        med = {k: float(np.median(v)) for k, v in by_class.items() if v}
        glob = float(np.median([x for v in by_class.values() for x in v])) if by_class else 0.0
        for sym in self.tmap:
            if sym in out:
                continue
            klass = (self.bt.get(self.bmap.get(sym, sym)) or {}).get("instrument_class")
            out[sym] = ("MODELLED_CLASS_MEDIAN", med.get(klass, glob))
        return out

    def broker_hour(self, iso: str) -> int:
        u = datetime.fromisoformat(iso)
        if u.tzinfo is None:
            u = u.replace(tzinfo=timezone.utc)
        return self._to_broker(u, self.server).hour

    def spread_bps(self, sym: str, hour: int) -> float:
        tk = self.tick.get("ftmo:" + self.tmap.get(sym, sym))
        if not tk:
            return 0.0
        flat = tk.get("spread_bps_median") or 0.0
        byh = tk.get("spread_bps_median_by_broker_hour") or {}
        nby = tk.get("n_by_broker_hour") or {}
        v = byh.get(str(hour))
        if v is None or (nby.get(str(hour), 0) or 0) < 500:
            return float(flat)
        return float(v)

    def comm_px(self, sym: str, price: float) -> float:
        rec = self.bt.get(self.bmap.get(sym, sym))
        if rec is None:
            return 0.0
        blk = rec.get("commission") or {}
        upu = float(rec.get("usd_per_price_unit_per_lot") or 0.0)
        kind = blk.get("kind")
        if kind == "zero":
            return 0.0
        if not upu:
            return 0.0
        if kind == "per_lot":
            return float(blk["value"]) / upu
        if kind == "notional_bp":
            cs = float((rec.get("spec") or {}).get("trade_contract_size") or 0.0)
            if not cs:
                return 0.0
            return float(blk["value"]) / 1e4 * cs * float(price) / upu
        return 0.0

    def swap_px(self, sym: str, long: bool, price: float, iso: str, hold_min: int) -> float:
        rec = self.bt.get(self.bmap.get(sym, sym))
        if rec is None:
            return 0.0
        spec = rec.get("spec") or {}
        raw = spec.get("swap_long" if long else "swap_short")
        mode = spec.get("swap_mode")
        if raw is None or mode is None or float(raw) >= 0:
            return 0.0
        adv = abs(float(raw))
        if int(mode) == 1:
            pt = spec.get("point")
            per_night = adv * float(pt) if pt else 0.0
        elif int(mode) in (5, 6):
            per_night = float(price) * (adv / 100.0) / 360.0
        else:
            return 0.0
        u = datetime.fromisoformat(iso)
        if u.tzinfo is None:
            u = u.replace(tzinfo=timezone.utc)
        w0 = self._to_broker(u, self.server)
        w1 = w0 + timedelta(minutes=hold_min)
        nights, d = 0.0, w0.date()
        while True:
            d = d + timedelta(days=1)
            b = datetime(d.year, d.month, d.day)
            if b > w1:
                break
            nights += 3.0 if b.weekday() == 3 else 1.0
        return per_night * nights

    def cost_px(self, sym: str, iso: str, price: float, long: bool, hold_min: int = HORIZON):
        """(total price-unit cost, dict of terms)."""
        h = self.broker_hour(iso)
        sp = self.spread_bps(sym, h) / 1e4 * price
        cm = self.comm_px(sym, price)
        sl = self.slip_bps.get(sym, ("MODELLED", 0.0))[1] / 1e4 * price
        sw = self.swap_px(sym, long, price, iso, hold_min)
        tot = sp + cm + sl + sw
        return tot, {"spread": sp, "commission": cm, "slippage": sl, "swap": sw}
