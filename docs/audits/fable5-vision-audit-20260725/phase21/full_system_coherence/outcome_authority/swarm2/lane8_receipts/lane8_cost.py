"""LANE 8 — charge broker-true cost to every walked row of every expansion arm.

`src/costs/cost_r` is the only cost authority (Session J's broker-truth layer). Where it raises,
the trade is recorded UNPRICED and coverage falls; it is NEVER back-filled with a plausible
number (`walkforward/panel.py` module docstring — F38 is the defect this rule exists downstream
of). Coverage is published per arm.

R_net = R_gross - cost_r, exact rather than approximate: `primitives.simulate` subtracts cost as
a scalar in R at the END of the trade and never uses it to decide a fill (`primitives.py:33-73`),
so the path is cost-independent.
"""
from __future__ import annotations
import collections, datetime as dt, gzip, json, math, random, statistics as stat, sys
from pathlib import Path

REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
sys.path.insert(0, str(REPO))
from src.costs import load_broker_true_costs, cost_r                      # noqa: E402

OUT = Path(__file__).resolve().parent
BT = load_broker_true_costs()
_f = lambda x: None if x is None else (float(x) if not hasattr(x, "value") else float(x.value))


def price(rows, account="FTMO"):
    priced, unpriced = [], collections.Counter()
    for r in rows:
        try:
            b = cost_r(r["symbol"], account, max(0.25, r["hold_hours"]),
                       sl_distance_price=r["sl_distance_price"], entry_price=r["entry_price"],
                       side="LONG" if r["direction"] > 0 else "SHORT",
                       entry_utc=dt.datetime.fromisoformat(r["entry_utc"]), costs=BT)
        except Exception as e:
            unpriced[f'{r["symbol"]}:{type(e).__name__}'] += 1
            continue
        c = _f(b.total_r)
        priced.append({**r, "cost_r": c, "r_net": r["r_gross"] - c,
                       "swap_r": _f(b.swap_r), "spread_r": _f(b.spread_r),
                       "comm_r": _f(b.commission_r), "slip_r": _f(b.slippage_r)})
    return priced, unpriced


def boot(v, reps=3000, seed=7):
    rng = random.Random(seed); n = len(v)
    if n < 2:
        return None
    ms = sorted(stat.fmean([v[rng.randrange(n)] for _ in range(n)]) for _ in range(reps))
    return [round(ms[int(.025 * reps)], 5), round(ms[int(.975 * reps)], 5)]


def stats(priced, unpriced, n_all, label):
    if not priced:
        return {"arm": label, "n_walked": n_all, "n_priced": 0,
                "coverage": 0.0, "unpriced": dict(unpriced)}
    g = [x["r_gross"] for x in priced]; net = [x["r_net"] for x in priced]
    c = [x["cost_r"] for x in priced]
    fwd = [x["r_net"] for x in priced if x["entry_utc"][:4] >= "2025"]
    pre = [x["r_net"] for x in priced if x["entry_utc"][:4] < "2025"]
    days = sorted({x["entry_utc"][:10] for x in priced})
    byday = collections.defaultdict(float)
    for x in priced:
        byday[x["entry_utc"][:10]] += x["r_net"]
    span = (dt.date.fromisoformat(days[-1]) - dt.date.fromisoformat(days[0])).days / 365.25
    m = stat.fmean(net); se = stat.stdev(net) / math.sqrt(len(net)) if len(net) > 1 else float("nan")
    return {
        "arm": label, "n_walked": n_all, "n_priced": len(priced),
        "coverage": round(len(priced) / n_all, 4), "unpriced": dict(unpriced.most_common(8)),
        "gross_r": round(stat.fmean(g), 5), "cost_r": round(stat.fmean(c), 5),
        "net_r": round(m, 5), "se": round(se, 5),
        "t_net": round(m / se, 3) if se and not math.isnan(se) else None,
        "ci95_boot_net": boot(net),
        "swap_share_of_cost": round(stat.fmean([x["swap_r"] or 0 for x in priced]) / stat.fmean(c), 4) if stat.fmean(c) else None,
        "median_hold_h": round(stat.median([x["hold_hours"] for x in priced]), 1),
        "n_days": len(days), "years": round(span, 2),
        "days_per_month": round(len(days) / (span * 12), 3),
        "total_net_R": round(sum(net), 2),
        "net_R_per_month": round(sum(net) / (span * 12), 4),
        "sum_R_per_signal_day": round(stat.fmean(list(byday.values())), 5),
        "pre2025_n": len(pre), "pre2025_net_r": round(stat.fmean(pre), 5) if pre else None,
        "fwd2025_n": len(fwd), "fwd2025_net_r": round(stat.fmean(fwd), 5) if fwd else None,
        "n_symbols": len({x["symbol"] for x in priced}),
    }


if __name__ == "__main__":
    src = json.load(gzip.open(OUT / "LANE8_EXPANSION_V1.json.gz"))
    res = {"generated": dt.datetime.now(dt.UTC).isoformat(),
           "cost_authority": "src/costs/cost_r (BROKER_TRUE_COSTS_V1.json)", "account": "FTMO",
           "arms": {}}
    for key, rows in src["rows"].items():
        p, u = price(rows)
        res["arms"][key] = stats(p, u, len(rows), key)
        s = res["arms"][key]
        print(f"{key:44s} n={s['n_walked']:5d} cov={s['coverage']:.2f} "
              f"gross={s.get('gross_r')} cost={s.get('cost_r')} net={s.get('net_r')} "
              f"t={s.get('t_net')} R/mo={s.get('net_R_per_month')}", flush=True)
    json.dump(res, open(OUT / "LANE8_COST_CHARGED_V1.json", "w"), indent=1)
