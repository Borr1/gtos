"""e_score -- the ONE combined offline scorer for lane e-stack.

Six levers, each ON/OFF, applied to a month base table. Every arm is scored on the
SAME candidate-opportunity denominator: a declined candidate books exactly 0.0 R, so
a rule that trades 300 times and a rule that trades 24,000 times are comparable.

LEVERS
  A1 STOPVALID  decline candidates whose stop price was already breached at the
                decision instant                              [w0-capture]
  A2 NOMKT      decline candidates whose limit was already through the market
                (but stop intact)                             [l6-F4]
  A3 DELAY      decline candidates whose entry level is traded inside the first
                minute after the decision                     [l8-F1]
  B1 EXIT       replace the shipped 2R/-1R contract with the chosen one [l11/l1/l2]
  C1 GATE       apply the shipped cost gate (spread<=0.10 AND total<=0.15) with
                BROKER-TRUE costs instead of the frozen model  [l5/l10]
  C2 DEPTH      require the limit to rest at least `depth_r` R away from the
                decision-instant market                       [l6-F8/l4]

ACCOUNTING
  gross     = R booked by the exit walk, honest fill, 0.0 if the limit never fills
  net_true  = gross - broker-true cost, charged only on trades that happened
  net_c73   = gross - (frozen spread / 7.3 + commission + slippage + swap)
  net_froz  = gross - the frozen cost model (the shipped one)
"""
from __future__ import annotations
import gzip, json, math, os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e_lib  # noqa: E402

LEVERS = ["A1_STOPVALID", "A2_NOMKT", "A3_DELAY", "B1_EXIT", "C1_GATE", "C2_DEPTH"]
GATE_SPREAD, GATE_TOTAL = 0.10, 0.15


def load(path):
    return [json.loads(x) for x in gzip.open(path, "rt") if x.strip()]


def eligible(r, arm, depth_r):
    if arm.get("A1_STOPVALID") and r["born"] == "born_past_stop":
        return False
    if arm.get("A2_NOMKT") and r["born"] == "born_marketable":
        return False
    if arm.get("A3_DELAY") and r["t_first"] == 1:
        return False
    if arm.get("C1_GATE"):
        if r["cost_true"] is None:
            return False
        if r["real_spread_r"] > GATE_SPREAD + 1e-12 or r["cost_true"] > GATE_TOTAL + 1e-12:
            return False
    if arm.get("C2_DEPTH"):
        if r["mkt_r"] is None or r["mkt_r"] < depth_r - 1e-12:
            return False
    return True


def score(rows, arm, contract="TS90S1", depth_r=1.0, dedup=False, days=None):
    """Return the book for one arm over one candidate population."""
    c = contract if arm.get("B1_EXIT") else "INC"
    pop = [r for r in rows if (not dedup or r["is_first"])]
    if days is not None:
        pop = [r for r in pop if r["day"] in days]
    n_opp = len(pop)
    per_day = {}
    tr = []           # gross R of trades actually taken
    ct, cc, cf = [], [], []
    n_decl = n_nofill = 0
    for r in pop:
        d = r["day"]
        if d not in per_day:
            per_day[d] = [0.0, 0.0, 0.0, 0, 0]   # gross, net_true, net_c73, n_opp, n_tr
        per_day[d][3] += 1
        if not eligible(r, arm, depth_r):
            n_decl += 1
            continue
        if r["X_" + c] == "no_fill":
            n_nofill += 1
            continue
        g = r["R_" + c]
        kt = r["cost_true"] if r["cost_true"] is not None else r["cost_corr73"]
        tr.append(g); ct.append(g - kt)
        cc.append(g - r["cost_corr73"]); cf.append(g - r["cost_frozen"])
        per_day[d][0] += g
        per_day[d][1] += g - kt
        per_day[d][2] += g - r["cost_corr73"]
        per_day[d][4] += 1
    n_tr = len(tr)
    wins = [x for x in tr if x > 0]
    loss = [x for x in tr if x <= 0]
    dseq = sorted(per_day)
    dg = [per_day[d][0] for d in dseq]
    dn = [per_day[d][1] for d in dseq]
    res = {
        "arm": {k: bool(arm.get(k)) for k in LEVERS}, "contract": c,
        "n_opportunity": n_opp, "n_declined": n_decl, "n_no_fill": n_nofill,
        "n_trades": n_tr, "trade_rate": round(n_tr / n_opp, 6) if n_opp else None,
        "gross_per_opportunity": round(sum(tr) / n_opp, 6) if n_opp else None,
        "net_true_per_opportunity": round(sum(ct) / n_opp, 6) if n_opp else None,
        "net_c73_per_opportunity": round(sum(cc) / n_opp, 6) if n_opp else None,
        "gross_per_trade": round(sum(tr) / n_tr, 6) if n_tr else None,
        "net_true_per_trade": round(sum(ct) / n_tr, 6) if n_tr else None,
        "net_c73_per_trade": round(sum(cc) / n_tr, 6) if n_tr else None,
        "net_frozen_per_trade": round(sum(cf) / n_tr, 6) if n_tr else None,
        "total_gross_R": round(sum(tr), 3), "total_net_true_R": round(sum(ct), 3),
        "total_net_c73_R": round(sum(cc), 3),
        "win_rate": round(len(wins) / n_tr, 6) if n_tr else None,
        "mean_winner": round(sum(wins) / len(wins), 6) if wins else None,
        "mean_loser": round(sum(loss) / len(loss), 6) if loss else None,
        "payoff": (round((sum(wins) / len(wins)) / abs(sum(loss) / len(loss)), 4)
                   if wins and loss and sum(loss) else None),
        "se_gross_per_trade": (round(e_lib.se(tr), 6) if n_tr > 1 else None),
        "se_net_true_per_trade": (round(e_lib.se(ct), 6) if n_tr > 1 else None),
        "t_net_true": (round((sum(ct) / n_tr) / e_lib.se(ct), 3)
                       if n_tr > 1 and e_lib.se(ct) else None),
        "n_days": len(dseq),
        "days_gross_positive": sum(1 for x in dg if x > 0),
        "days_net_true_positive": sum(1 for x in dn if x > 0),
        "mean_cost_true_charged": (round(sum(t - n for t, n in zip(tr, ct)) / n_tr, 6)
                                   if n_tr else None),
        "equity_net_true": [round(x, 4) for x in _cum(dn)],
        "day_index": dseq,
        "max_drawdown_net_true_R": round(_mdd(_cum(dn)), 4),
    }
    return res


def _cum(v):
    out, s = [], 0.0
    for x in v:
        s += x
        out.append(s)
    return out


def _mdd(eq):
    peak, mdd = 0.0, 0.0
    for x in eq:
        peak = max(peak, x)
        mdd = min(mdd, x - peak)
    return mdd


def allarms(rows, contract="TS90S1", depth_r=1.0, dedup=False, days=None):
    out = []
    for mask in range(64):
        arm = {LEVERS[i]: bool(mask >> i & 1) for i in range(6)}
        out.append(score(rows, arm, contract, depth_r, dedup, days))
    return out


def bootstrap_day(rows, arm, contract, depth_r, nboot=400, seed=20260806, dedup=False):
    """Day-block bootstrap on net-true R PER OPPORTUNITY."""
    import random
    rnd = random.Random(seed)
    pop = [r for r in rows if (not dedup or r["is_first"])]
    byday = {}
    for r in pop:
        byday.setdefault(r["day"], []).append(r)
    days = sorted(byday)
    per = {}
    for d in days:
        s = 0.0
        n = len(byday[d])
        for r in byday[d]:
            if not eligible(r, arm, depth_r):
                continue
            c = contract if arm.get("B1_EXIT") else "INC"
            if r["X_" + c] == "no_fill":
                continue
            kt = r["cost_true"] if r["cost_true"] is not None else r["cost_corr73"]
            s += r["R_" + c] - kt
        per[d] = (s, n)
    obs = sum(per[d][0] for d in days) / sum(per[d][1] for d in days)
    samp = []
    for _ in range(nboot):
        pick = [rnd.choice(days) for _ in days]
        num = sum(per[d][0] for d in pick)
        den = sum(per[d][1] for d in pick)
        samp.append(num / den if den else 0.0)
    samp.sort()
    return {"observed": round(obs, 6),
            "ci95": [round(samp[int(0.025 * nboot)], 6), round(samp[int(0.975 * nboot)], 6)],
            "p_le_zero": round(sum(1 for x in samp if x <= 0) / nboot, 5),
            "n_days": len(days), "nboot": nboot}
