"""h3_lib -- shared machinery for lane h3 (how much of the 2.457 bps toll is removable).

SUBSTRATE. The LIVE-EXPRESSIBLE cohort built by e_build_atmkt.py: at-market entries only
(entry_price == the decision-instant close), three months, 43,755 rows.
    e_JAN_ATMKT_V1.jsonl.gz  14,905
    e_FEB_ATMKT_V1.jsonl.gz  13,966
    e_MAR_ATMKT_V1.jsonl.gz  14,884

PRICE SPACE. Every R quantity converts to basis points of the entry price through the
row's own stop width:
    rdp      = risk_distance / entry_price            (fraction of price carried by 1R)
    bps(x_R) = x_R * rdp * 1e4
This conversion is what makes an edge on a 0.03 %-stop FX pair comparable with an edge on
a 0.34 %-stop oil CFD. Every "bps" number in this lane is a per-trade quantity averaged
over trades, never a ratio of averages.

TOLL. `cost_true` = real_spread_r + real_comm_r + real_slip_r, the broker-true cost object
l10 measured from 263.9 M ticks and e_lib ported verbatim. There is NO swap term in it --
see h3-F5 for why that is correct on a 2 h horizon and what it means.

HOUR-AWARE SPREAD. `L10X_TICK_SPREAD_V1.json` carries `spread_bps_median_by_broker_hour`
per symbol. The tick capture ran 2026-06-18..07-24, i.e. US EDT, where the broker clock
(= America/New_York + 7 h, CLAUDE.md §4) sits at UTC+3. The pool runs 2026-01..03, i.e.
EST (UTC+2) until 2026-03-08 and EDT after. The session shape is a property of the NEW YORK
wall clock, not of UTC, so the profile is transferred through NY local hour:
    ny_hour(tick_broker_hour) = (broker_hour - 7) % 24
    ny_hour(pool_row)         = decision_time_utc converted to America/New_York
`h3_hour_spread_bps(sym, ny_hour)` does this. `--naive-utc` in the scripts uses the
uncorrected (broker_hour - 3) mapping for every month as a robustness arm.
"""
from __future__ import annotations

import gzip
import json
import math
import os
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
except Exception:                                          # pragma: no cover
    NY = None

D = os.path.dirname(os.path.abspath(__file__))
MONTHS = {"2026-01": "e_JAN_ATMKT_V1.jsonl.gz",
          "2026-02": "e_FEB_ATMKT_V1.jsonl.gz",
          "2026-03": "e_MAR_ATMKT_V1.jsonl.gz"}
BASES = {"2026-01": "e_JAN_BASE_V1.jsonl.gz",
         "2026-02": "e_FEB_BASE_V1.jsonl.gz",
         "2026-03": "e_MAR_BASE_V1.jsonl.gz"}

TICK = json.load(open(f"{D}/L10X_TICK_SPREAD_V1.json"))

# imported so the hour model uses the SAME symbol->tick-key map the cost object uses
import e_lib  # noqa: E402

KS = [0, 1, 2, 3, 5, 10, 15, 20, 30, 45, 60]
CS = ["INC", "TRAIL025", "TS90S1", "STOPONLY", "T3S1", "TS60S1"]
HEADLINE = ("K5_TRAIL025", "the synthesis contract: at-market, +5 min, 0.25R trail")


# ------------------------------------------------------------------ loading
def load_atmkt(months=None, require_cost=True):
    """The live-expressible cohort. Adds ny_hour, utc_hour, month, and price-space fields."""
    out = []
    for m in (months or sorted(MONTHS)):
        for line in gzip.open(os.path.join(D, MONTHS[m]), "rt"):
            if not line.strip():
                continue
            r = json.loads(line)
            if require_cost and r.get("cost_true") is None:
                continue
            r["month"] = m
            dt = datetime.fromisoformat(r["dt"])
            r["utc_hour"] = dt.hour
            r["ny_hour"] = dt.astimezone(NY).hour if NY else (dt.hour - 5) % 24
            r["dow"] = dt.weekday()
            r["rdp_bps"] = r["rdp"] * 1e4
            out.append(r)
    return out


def load_base(months=None):
    out = []
    for m in (months or sorted(BASES)):
        for line in gzip.open(os.path.join(D, BASES[m]), "rt"):
            if not line.strip():
                continue
            r = json.loads(line)
            r["month"] = m
            out.append(r)
    return out


# ------------------------------------------------------- hour-aware spread
_HOURMAP = {}


def _profile(sym):
    """{ny_hour: spread_bps} for a pool symbol, or None."""
    if sym in _HOURMAP:
        return _HOURMAP[sym]
    tk = TICK.get("ftmo:" + e_lib.TMAP.get(sym, sym))
    prof = None
    if tk and tk.get("spread_bps_median_by_broker_hour"):
        byh = tk["spread_bps_median_by_broker_hour"]
        nh = tk.get("n_by_broker_hour", {})
        prof = {}
        for bh, v in byh.items():
            prof[(int(bh) - 7) % 24] = {"bps": float(v), "n": int(nh.get(bh, 0))}
    _HOURMAP[sym] = prof
    return prof


def hour_spread_bps(sym, ny_hour, naive_utc_hour=None):
    """Tick-measured median quoted spread in bps for this symbol at this NY hour.
    Falls back to the flat median when the hour is unmeasured."""
    p = _profile(sym)
    tk = TICK.get("ftmo:" + e_lib.TMAP.get(sym, sym))
    flat = tk.get("spread_bps_median") if tk else None
    if p is None:
        return flat
    if naive_utc_hour is not None:                 # robustness arm: broker_hour-3 mapping
        h = (naive_utc_hour + 3 - 7) % 24
    else:
        h = ny_hour
    e = p.get(h)
    return e["bps"] if e else flat


def add_hour_cost(rows, naive=False):
    """Attach hour-conditioned spread and the resulting hour-aware toll, in R and bps."""
    for r in rows:
        sb = hour_spread_bps(r["symbol"], r["ny_hour"],
                             naive_utc_hour=(r["utc_hour"] if naive else None))
        if sb is None:
            r["spread_bps_hour"] = None
            r["cost_true_hour"] = None
            continue
        sp_r = (sb * r["entry_price"] / 1e4) / r["risk_distance"]
        r["spread_bps_hour"] = sb
        r["real_spread_r_hour"] = sp_r
        r["cost_true_hour"] = sp_r + r["real_comm_r"] + r["real_slip_r"]
    return rows


# ------------------------------------------------------------- price space
def bps(x_r, row):
    return x_r * row["rdp"] * 1e4


def gross_r(row, col=None):
    return row[col or HEADLINE[0]]


def scored(rows, col=None, cost_key="cost_true"):
    """Per-trade (gross_bps, toll_bps, net_bps) lists for rows with a defined contract value."""
    g, t, n, keep = [], [], [], []
    c = col or HEADLINE[0]
    for r in rows:
        v = r.get(c)
        ct = r.get(cost_key)
        if v is None or ct is None:
            continue
        gb = v * r["rdp"] * 1e4
        tb = ct * r["rdp"] * 1e4
        g.append(gb); t.append(tb); n.append(gb - tb); keep.append(r)
    return g, t, n, keep


# ------------------------------------------------------------------- stats
def mean(v):
    return sum(v) / len(v) if v else None


def se(v):
    n = len(v)
    if n < 2:
        return None
    m = sum(v) / n
    return math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1) / n)


def q(v, p):
    if not v:
        return None
    s = sorted(v)
    i = max(0, min(len(s) - 1, int(round(p * (len(s) - 1)))))
    return s[i]


def tstat(v):
    m, s = mean(v), se(v)
    return None if not s else m / s


def daily_t(rows, vals, daykey="day"):
    """Cluster-robust-ish: mean of daily means and its t. Guards against within-day
    correlation inflating a per-trade t."""
    acc = {}
    for r, v in zip(rows, vals):
        acc.setdefault(r[daykey], []).append(v)
    dm = [sum(x) / len(x) for x in acc.values()]
    return {"n_days": len(dm), "mean_of_daily": mean(dm), "t_daily": tstat(dm),
            "days_positive": sum(1 for x in dm if x > 0)}


def summarize(rows, col=None, cost_key="cost_true", label=""):
    g, t, n, keep = scored(rows, col, cost_key)
    if not g:
        return {"label": label, "n": 0}
    d = daily_t(keep, n)
    dg = daily_t(keep, g)
    return {
        "label": label, "n": len(g),
        "gross_r": mean([r.get(col or HEADLINE[0]) for r in keep]),
        "cost_r": mean([r[cost_key] for r in keep]),
        "net_r": mean([r.get(col or HEADLINE[0]) - r[cost_key] for r in keep]),
        "edge_bps": mean(g), "toll_bps": mean(t), "net_bps": mean(n),
        "edge_over_toll": (mean(g) / mean(t)) if mean(t) else None,
        "t_gross_trade": tstat(g), "t_net_trade": tstat(n),
        "t_net_daily": d["t_daily"], "days": d["n_days"],
        "days_net_positive": d["days_positive"],
        "days_gross_positive": dg["days_positive"],
    }


def dump(obj, name):
    p = os.path.join(D, name)
    with open(p, "w") as fh:
        json.dump(obj, fh, indent=1, default=str)
    return p
