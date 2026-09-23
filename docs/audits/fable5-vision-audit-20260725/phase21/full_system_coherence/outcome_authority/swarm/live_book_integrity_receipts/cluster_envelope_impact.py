#!/usr/bin/env python3
"""Cluster-envelope impact: what `ultimate_book_one_unit_per_cluster_per_day` is worth.

The instrument is the CORRELATED UNIT, not the trade. `admission.size_correlated_units`
buckets by ``(decision_day, cluster)`` and splits one unit's risk across its members
(``per_trade = unit_risk / n``), so a bar-group's return in unit-risk terms is the MEAN of
its members' R. `book_owner.py:2066` skips a LATER-BAR same-cluster fire and never touches
same-bar members, so the two regimes are:

  cap OFF (live before 2026-08-12): every (cluster, day, bar) group is a full fresh unit
  cap ON                          : only the day's FIRST bar-group per cluster is a unit

Population: `phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz` (the corrected-armed-set
re-walk, 22,354 trades, per-trade symbol + entry_utc + banded net R). This is the ARCHIVE
population, NOT the W7 recost cache -- so every number here is a WITHIN-CORPUS A/B and is
not comparable to a published `p_pass`. That is the only claim it needs to support.

Usage: python3 cluster_envelope_impact.py [out.json]
"""
from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[7] if len(Path(__file__).resolve().parents) > 7 else Path.cwd()
for p in (REPO, REPO / "scripts"):
    sys.path.insert(0, str(p))

from src.components.ultimate_book import admission as A          # noqa: E402
from src.safety.armed_set import armed_sleeves                   # noqa: E402
import mc_firm_rules as Q                                        # noqa: E402

ROWS = (REPO / "docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts"
        / "R1_ESTATE_ROWS_V2.json.gz")
EXEMPT = {"jpy"}          # config/agent_config.yaml ultimate_book_cluster_cap_exempt_clusters
PATHS = 40000

mx, _err = A.resolve_market_expansion_sleeves(
    policy="positive_weighted12_after_swap", explicit_sleeves=())
REG = A.effective_registry(include_clean3=True, include_candidate_book=True,
                           include_market_expansion_book=True, market_expansion_sleeves=mx)
CONF = {k: float(v.confidence) for k, v in REG.items()}
ARMED = sorted(armed_sleeves())

D = json.load(gzip.open(ROWS))


def unit_series(rows, rkey="r_new_mid", conf_weight=True, shift_h=0):
    """(days, cap_off_day_R, cap_on_day_R, stats)."""
    byday: dict = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        t = dt.datetime.fromisoformat(r["entry_utc"]) + dt.timedelta(hours=shift_h)
        cl = A.cluster_of(r["sleeve"], REG) or "__unknown__"
        byday[(cl, t.date().isoformat())][t.isoformat()].append(r)
    off, on = collections.defaultdict(float), collections.defaultdict(float)
    n_off = n_on = bound = first_bar_multi = 0
    blocked_new_symbol = blocked_repeat_symbol = 0
    gaps: list[float] = []
    for (cl, day), bars in byday.items():
        order = sorted(bars)
        if len(bars[order[0]]) > 1 and len({x["symbol"] for x in bars[order[0]]}) > 1:
            first_bar_multi += 1
        if len(order) > 1 and cl not in EXEMPT:
            bound += 1
            first_syms = {x["symbol"] for x in bars[order[0]]}
            t0 = dt.datetime.fromisoformat(order[0])
            for b in order[1:]:
                gaps.append((dt.datetime.fromisoformat(b) - t0).total_seconds() / 3600.0)
                if {x["symbol"] for x in bars[b]} & first_syms:
                    blocked_repeat_symbol += 1
                else:
                    blocked_new_symbol += 1
        for i, b in enumerate(order):
            g = bars[b]
            u = statistics.fmean([x[rkey] for x in g])
            if conf_weight:
                u *= max(CONF.get(x["sleeve"], 0.0) for x in g)
            off[day] += u
            n_off += 1
            if i == 0 or cl in EXEMPT:
                on[day] += u
                n_on += 1
    days = sorted(set(off) | set(on))
    so = [off.get(d, 0.0) for d in days]
    sn = [on.get(d, 0.0) for d in days]
    return days, so, sn, {
        "cluster_day_buckets": len(byday), "buckets_where_cap_binds": bound,
        "bind_rate_pct": round(100.0 * bound / max(1, len(byday)), 2),
        "units_cap_off": n_off, "units_cap_on": n_on,
        "units_blocked": n_off - n_on,
        "units_blocked_pct": round(100.0 * (n_off - n_on) / max(1, n_off), 2),
        "blocked_is_repeat_of_symbol_already_on": blocked_repeat_symbol,
        "blocked_is_a_new_symbol": blocked_new_symbol,
        "buckets_whose_FIRST_bar_is_multi_symbol_never_blocked": first_bar_multi,
        "blocked_bar_gap_hours_median": round(statistics.median(gaps), 2) if gaps else None,
    }


def maxdd(series):
    eq = peak = 0.0
    dd = 0.0
    for v in series:
        eq += v
        peak = max(peak, eq)
        dd = min(dd, eq - peak)
    return dd


def econ(days, so, sn):
    rnd = random.Random(1)
    diff = [b - a for a, b in zip(so, sn)]
    n = len(diff)
    boots = sorted(statistics.fmean([diff[rnd.randrange(n)] for _ in range(n)])
                   for _ in range(20000))
    return {
        "n_days": n,
        "r_per_day_cap_off": round(statistics.fmean(so), 5),
        "r_per_day_cap_on": round(statistics.fmean(sn), 5),
        "r_per_day_pct_change": round(100.0 * (statistics.fmean(sn) - statistics.fmean(so))
                                      / abs(statistics.fmean(so)), 2) if statistics.fmean(so) else None,
        "paired_delta_r_per_day": round(statistics.fmean(diff), 5),
        "paired_delta_ci95": [round(boots[500], 5), round(boots[19499], 5)],
        "sd_day_cap_off": round(statistics.pstdev(so), 5),
        "sd_day_cap_on": round(statistics.pstdev(sn), 5),
        "worst_day_cap_off": round(min(so), 4),
        "worst_day_cap_on": round(min(sn), 4),
        "max_drawdown_r_cap_off": round(maxdd(so), 3),
        "max_drawdown_r_cap_on": round(maxdd(sn), 3),
    }


out = {
    "schema": "gtos.live_book_integrity.cluster_envelope_impact.v1",
    "population": "ARCHIVE (R1_ESTATE_ROWS_V2) -- within-corpus A/B ONLY, not comparable to "
                  "the W7-cache p_pass figures",
    "armed_sleeves": ARMED,
    "confidences": {s: CONF.get(s) for s in ARMED},
    "clusters": {s: A.cluster_of(s, REG) for s in ARMED},
    "exempt_clusters": sorted(EXEMPT),
    "mc_paths": PATHS,
    "arms": {},
}

armed_rows = [r for r in D if r["sleeve"] in ARMED]
fwd_rows = [r for r in armed_rows if r["entry_utc"] >= "2025-01-01"]

# 1. robustness: every cost band, both weightings, +/- 2 h clock sensitivity
rob = {}
for band in ("r_new_low", "r_new_mid", "r_new_high", "r_old"):
    for cw in (True, False):
        d, so, sn, st = unit_series(armed_rows, rkey=band, conf_weight=cw)
        rob[f"{band}|conf_weighted={cw}"] = {**st, **econ(d, so, sn)}
for sh in (-2, 2):
    d, so, sn, st = unit_series(armed_rows, shift_h=sh)
    rob[f"r_new_mid|day_boundary_shift={sh:+d}h"] = {**st, **econ(d, so, sn)}
out["arms"]["robustness"] = rob

# 2. the decision instrument: p_pass at the firm-true 2-phase rules
mcres = {}
for wlabel, rows in (("all_years", armed_rows), ("forward_2025_plus", fwd_rows)):
    d, so, sn, st = unit_series(rows)
    mcres[wlabel] = {"stats": st, "econ": econ(d, so, sn), "mc": {}}
    for acct in ("FTMO", "redacted_account"):
        rule = [r for r in Q.rule_sets(acct)[0] if r.label == "P2_BOTH_PHASES"][0]
        for risk, rlabel in ((0.020, "dial_2.000pct"), (0.011968, "measured_live_1.1968pct")):
            a = Q.mc(so, risk, rule, PATHS, seed_base=1)
            b = Q.mc(sn, risk, rule, PATHS, seed_base=1)
            mcres[wlabel]["mc"][f"{acct}|{rlabel}"] = {
                "cap_off": {"p_pass": round(a["p_pass"], 6), "se": round(a["se_p_pass"], 6),
                            "p_fail_daily": round(a["p_fail_daily"], 6),
                            "p_fail_dd": round(a["p_fail_dd"], 6)},
                "cap_on": {"p_pass": round(b["p_pass"], 6), "se": round(b["se_p_pass"], 6),
                           "p_fail_daily": round(b["p_fail_daily"], 6),
                           "p_fail_dd": round(b["p_fail_dd"], 6)},
                "delta_p_pass": round(b["p_pass"] - a["p_pass"], 6),
            }
out["arms"]["decision"] = mcres

dest = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("CLUSTER_ENVELOPE_IMPACT_V1.json")
dest.write_text(json.dumps(out, indent=1))
print("WROTE", dest)
print(json.dumps(out["arms"]["decision"]["all_years"]["stats"], indent=1))
for w, blk in out["arms"]["decision"].items():
    for k, v in blk["mc"].items():
        print(f"{w:18s} {k:38s} OFF {v['cap_off']['p_pass']:.4f} -> ON {v['cap_on']['p_pass']:.4f} "
              f"({v['delta_p_pass']:+.4f})  pDaily {v['cap_off']['p_fail_daily']:.4f} -> "
              f"{v['cap_on']['p_fail_daily']:.4f}")
