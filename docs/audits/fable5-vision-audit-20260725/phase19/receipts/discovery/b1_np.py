"""b1_np — numpy substrate + fast scorer shared by every b1 step.

Loads the five-month at-market substrate once, attaches
  * h1's four-term broker-true cost   (3 hunt months, 43,755/43,755 joined)
  * the broker hour (NEW_YORK_PLUS_7, the measured live convention)
  * h2's ex-ante cash-session flag    (exchange-local, DST-correct)
and exposes every (delay k x exit contract) gross vector as a numpy array.

COST BASES (all round-trip, all in R; multiply by bpsfac for price space)
  flat   cost_true            swarm basis            0.181834 R / 2.4571 bps
  hour   cost_true_hour       b1 five-month basis    0.220328 R / 2.6692 bps
  h1     cost_h1_r            STRICTEST, 3 months    0.245214 R / 2.9744 bps
"""
from __future__ import annotations

import gzip
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
KS = (0, 1, 2, 3, 5, 10, 15, 20, 30, 45, 60)
CONTRACTS = ("STOPONLY", "INC", "T3S1", "TS90S1", "TS60S1", "TRAIL025")
# TRAIL025 is carried for reference ONLY: the estate's ratified honest-trail bound
# (B613 / AD; h6-F8) shows it manufactures +0.084 R/trade of bar-resolution premium.
TRAIL_FREE = ("STOPONLY", "INC", "T3S1", "TS90S1", "TS60S1")

BERLIN, LONDON, NY, TOKYO = (ZoneInfo("Europe/Berlin"), ZoneInfo("Europe/London"),
                             ZoneInfo("America/New_York"), ZoneInfo("Asia/Tokyo"))
CASH = {"GER40": (BERLIN, 9.0, 17.5), "UK100": (LONDON, 8.0, 16.5),
        "US30_cash": (NY, 9.5, 16.0), "NAS100": (NY, 9.5, 16.0),
        "SPX500": (NY, 9.5, 16.0), "JP225": (TOKYO, 9.0, 15.0),
        "USOIL_cash": (NY, 9.0, 14.5), "UKOIL_cash": (LONDON, 8.0, 17.5),
        "XAUUSD": (LONDON, 8.0, 21.0), "XAGUSD": (LONDON, 8.0, 21.0)}
FX = {"EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
      "EURJPY", "GBPJPY", "AUDJPY", "CHFJPY", "EURGBP"}
FX_WIN = (LONDON, 8.0, 17.0)
CRYPTO = {"BTCUSD", "ETHUSD"}

_c = {}


def _in_cash(sym, dt):
    if sym in CRYPTO:
        return True
    spec = CASH.get(sym) or (FX_WIN if sym in FX else None)
    if spec is None:
        return False
    tz, o, c = spec
    lt = dt.astimezone(tz)
    if lt.weekday() >= 5:
        return False
    h = lt.hour + lt.minute / 60.0
    return o <= h < c


def load():
    if "d" in _c:
        return _c["d"]
    rows = [json.loads(x) for x in gzip.open(f"{D}/h5_SUBSTRATE_5M.jsonl.gz", "rt") if x.strip()]
    h1 = {}
    for ln in gzip.open(f"{D}/b1_COST_JOIN_V1.jsonl.gz", "rt"):
        o = json.loads(ln)
        h1[(o["cid"], o["dt"])] = o
    n = len(rows)
    M = {
        "symbol": np.array([r["symbol"] for r in rows]),
        "day": np.array([r["day"] for r in rows]),
        "month": np.array([r["month"] for r in rows]),
        "family": np.array([r["family"] or "" for r in rows]),
        "session": np.array([r["session"] or "" for r in rows]),
        "side": np.array([r["side"] for r in rows]),
        "dow": np.array([r["dow"] for r in rows]),
        "rdp": np.array([r["rdp"] for r in rows], dtype=np.float64),
        "cost_flat": np.array([r["cost_true"] for r in rows], dtype=np.float64),
        "cost_hour": np.array([r["cost_true_hour"] for r in rows], dtype=np.float64),
        "prob": np.array([r["prob"] if r["prob"] is not None else np.nan for r in rows]),
        "rv_rel": np.array([r["rv_rel"] if r["rv_rel"] is not None else np.nan for r in rows]),
        "rdp_rel": np.array([r["rdp_rel"] if r["rdp_rel"] is not None else np.nan for r in rows]),
        "utc_hour": np.array([r["utc_hour"] for r in rows], dtype=np.int32),
        "ny_hour": np.array([r["ny_hour"] for r in rows], dtype=np.int32),
    }
    M["bpsfac"] = M["rdp"] * 1e4
    M["broker_hour"] = (M["ny_hour"] + 7) % 24
    ch1 = np.full(n, np.nan)
    ch1ns = np.full(n, np.nan)
    swp = np.full(n, np.nan)
    era = np.full(n, np.nan)
    for i, r in enumerate(rows):
        o = h1.get((r["cid"], r["dt"]))
        if o is not None:
            ch1[i] = o["cost_h1_r"]
            ch1ns[i] = o["cost_h1_noswap_r"]
            swp[i] = o["swap_r"]
            era[i] = o["cost_h1_era_r"]
    M["cost_h1"] = ch1
    M["cost_h1_noswap"] = ch1ns
    M["swap_r"] = swp
    M["cost_h1_era"] = era
    cash = np.zeros(n, dtype=bool)
    for i, r in enumerate(rows):
        cash[i] = _in_cash(r["symbol"], datetime.fromisoformat(r["dt"]))
    M["cash"] = cash

    G = {}
    for k in KS:
        for cx in CONTRACTS:
            key = f"K{k}_{cx}"
            G[(k, cx)] = np.array([r[key] if r.get(key) is not None else np.nan
                                   for r in rows], dtype=np.float64)
    _c["d"] = (M, G, rows)
    return _c["d"]


# ------------------------------------------------------------------ fast scorer
def score(g, c, M, sel, want_equity=False):
    """Scores one book. g = gross R vector, c = cost R vector, sel = bool mask."""
    s = sel & np.isfinite(g) & np.isfinite(c)
    n = int(s.sum())
    if n == 0:
        return {"n": 0}
    gg, cc = g[s], c[s]
    net = gg - cc
    bf = M["bpsfac"][s]
    gb, cb = gg * bf, cc * bf
    nb = gb - cb
    day = M["day"][s]
    mg, mc, mn = gg.mean(), cc.mean(), net.mean()
    mgb, mcb = gb.mean(), cb.mean()
    ud, inv = np.unique(day, return_inverse=True)
    G_ = len(ud)
    dsum = np.bincount(inv, weights=net, minlength=G_)
    dcnt = np.bincount(inv, minlength=G_)
    dmean = dsum / dcnt
    t_day = None
    if G_ >= 3:
        resid = dsum - mn * dcnt
        ss = float((resid ** 2).sum())
        if ss > 0:
            se = np.sqrt(ss) / n * np.sqrt(G_ / max(G_ - 1, 1))
            t_day = float(mn / se)
    sd = net.std(ddof=1) if n > 2 else np.nan
    out = {"n": n,
           "gross_R": float(mg), "cost_R": float(mc), "net_R": float(mn),
           "ratio_R": float(mg / mc) if mc else None,
           "gross_bps": float(mgb), "cost_bps": float(mcb), "net_bps": float(mgb - mcb),
           "ratio_bps": float(mgb / mcb) if mcb else None,
           "t_net": float(mn / (sd / np.sqrt(n))) if sd and np.isfinite(sd) and sd > 0 else None,
           "t_gross": (float(gg.mean() / (gg.std(ddof=1) / np.sqrt(n)))
                       if n > 2 and gg.std(ddof=1) > 0 else None),
           "t_net_day": t_day,
           "win_rate_net": float((net > 0).mean()),
           "win_rate_gross": float((gg > 0).mean()),
           "n_days": G_, "n_days_net_pos": int((dmean > 0).sum()),
           "n_symbols": int(len(np.unique(M["symbol"][s]))),
           "total_net_R": float(net.sum()),
           "mean_rdp_bps": float(bf.mean()),
           "months": sorted(set(M["month"][s].tolist()))}
    cum = np.cumsum(dsum)
    peak = np.maximum.accumulate(cum)
    out["max_dd_R"] = float((cum - peak).min()) if G_ else 0.0
    out["ret_over_dd"] = (float(cum[-1] / -out["max_dd_R"])
                          if out["max_dd_R"] < 0 else None)
    for m in ("2026-01", "2026-02", "2026-03", "2026-04", "2026-05"):
        ms = M["month"][s] == m
        if not ms.any():
            out["m_" + m] = None
            continue
        out["m_" + m] = {"n": int(ms.sum()), "gross_R": float(gg[ms].mean()),
                         "cost_R": float(cc[ms].mean()), "net_R": float(net[ms].mean()),
                         "ratio_R": (float(gg[ms].mean() / cc[ms].mean())
                                     if cc[ms].mean() else None),
                         "net_bps": float(nb[ms].mean())}
    if want_equity:
        out["equity_days"] = ud.tolist()
        out["equity_net_R"] = [round(float(x), 4) for x in cum]
        out["day_net_R"] = [round(float(x), 5) for x in dmean]
    return out


def slim(s, nd=6):
    def rr(v):
        return round(v, nd) if isinstance(v, float) else v
    return {k: (rr(v) if not isinstance(v, dict) else {a: rr(b) for a, b in v.items()})
            for k, v in s.items() if k not in ("equity_days", "equity_net_R", "day_net_R")}
