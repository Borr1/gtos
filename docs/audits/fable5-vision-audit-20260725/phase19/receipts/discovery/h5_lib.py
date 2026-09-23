"""h5_lib — shared cell arithmetic for the edge/cost > 1 hunt.

THE CONTRACT IS FIXED AND IS NOT SEARCHED OVER in the primary hunt:
    entry  = market order at the close of path bar k=5 (5 minutes after the decision)
    exit   = TRAIL025 (no target, initial stop -1R, stop trails 0.25 R behind running MFE)
    cohort = born_at_limit (LIVE-EXPRESSIBLE: entry_price == the decision-instant market
             price, the only order type the live engine can place)
    cost   = broker-true (tick-truthed median spread + broker commission + measured
             live slippage), the same object l10 measured, ported in e_lib.real_cost_parts

TWO RATIOS, AND THEY ARE DIFFERENT BOOKS. Report both, always.
    ratio_R   = mean(gross_R) / mean(cost_R).  net R per trade > 0  <=>  ratio_R > 1.
                This is a CONSTANT-RISK book (fixed R per trade), which is how this
                estate sizes.  It is the money-relevant ratio.
    ratio_bps = mean(gross_R * rdp) / mean(cost_R * rdp), rdp = risk_distance/price.
                This is a CONSTANT-NOTIONAL book.  It is the price-space framing the
                swarm headline used (+0.231 vs 2.457 bps).
The two can disagree in sign of (ratio - 1) whenever stop width correlates with edge
inside the cell, so a cell is only called AFFORDABLE when ratio_R > 1.
"""
from __future__ import annotations

import math

GROSS = "K5_TRAIL025"
COST = "cost_true"


def _mean(v):
    return sum(v) / len(v) if v else None


def cell_stats(rs, gross_key=None, cost_key=None):
    """Every number h5 reports for one cell. `rs` is a list of substrate rows.
    Keys default to the module-level GROSS/COST so a caller can swap the whole hunt onto
    the hour-aware cost by setting h5_lib.COST = 'cost_true_hour'."""
    gross_key = gross_key or GROSS
    cost_key = cost_key or COST
    n = len(rs)
    if n == 0:
        return None
    g = [r[gross_key] for r in rs]
    c = [r[cost_key] for r in rs]
    net = [a - b for a, b in zip(g, c)]
    rdp = [r["rdp"] for r in rs]
    gb = [a * d * 1e4 for a, d in zip(g, rdp)]
    cb = [b * d * 1e4 for b, d in zip(c, rdp)]
    nb = [a - b for a, b in zip(gb, cb)]

    mg, mc, mn = _mean(g), _mean(c), _mean(net)
    mgb, mcb, mnb = _mean(gb), _mean(cb), _mean(nb)

    def _t(v):
        if len(v) < 3:
            return None
        m = _mean(v)
        s2 = sum((x - m) ** 2 for x in v) / (len(v) - 1)
        if s2 <= 0:
            return None
        return m / math.sqrt(s2 / len(v))

    # day-clustered t on net R: trades inside one day share the same market
    byday = {}
    for r, x in zip(rs, net):
        byday.setdefault(r["day"], []).append(x)
    t_net_day = None
    if len(byday) >= 3 and mn is not None:
        ss = sum((sum(x - mn for x in v)) ** 2 for v in byday.values())
        if ss > 0:
            G = len(byday)
            se = math.sqrt(ss) / n * math.sqrt(G / max(G - 1, 1))
            t_net_day = mn / se

    dpos = sum(1 for v in byday.values() if _mean(v) > 0)
    months = sorted({r["month"] for r in rs})

    out = {
        "n": n,
        "gross_R": round(mg, 6), "cost_R": round(mc, 6), "net_R": round(mn, 6),
        "ratio_R": (round(mg / mc, 4) if mc and mc > 0 else None),
        "edge_bps": round(mgb, 4), "toll_bps": round(mcb, 4), "net_bps": round(mnb, 4),
        "ratio_bps": (round(mgb / mcb, 4) if mcb and mcb > 0 else None),
        "t_gross": (round(_t(g), 3) if _t(g) is not None else None),
        "t_net": (round(_t(net), 3) if _t(net) is not None else None),
        "t_net_day": (round(t_net_day, 3) if t_net_day is not None else None),
        "days": len(byday), "days_net_pos": dpos,
        "n_symbols": len({r["symbol"] for r in rs}),
        "months": months,
    }
    for m in ("2026-01", "2026-02", "2026-03"):
        sub = [i for i, r in enumerate(rs) if r["month"] == m]
        if not sub:
            out["m_" + m] = None
            continue
        gm = _mean([g[i] for i in sub])
        cm = _mean([c[i] for i in sub])
        out["m_" + m] = {"n": len(sub), "gross_R": round(gm, 6), "cost_R": round(cm, 6),
                         "net_R": round(gm - cm, 6),
                         "ratio_R": (round(gm / cm, 4) if cm and cm > 0 else None)}
    return out


def rank_score(st):
    """(ratio - 1) * n — effect and evidence together, as the lane brief specifies."""
    if st is None or st.get("ratio_R") is None:
        return -1e18
    return (st["ratio_R"] - 1.0) * st["n"]
