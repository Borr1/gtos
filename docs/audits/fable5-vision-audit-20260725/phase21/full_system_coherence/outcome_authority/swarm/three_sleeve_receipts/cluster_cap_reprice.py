#!/usr/bin/env python3
"""Re-price `ultimate_book_one_unit_per_cluster_per_day` on the THREE-sleeve book.

Measurement only.  No live path, no config, no broker, no VPS.

WHY.  `LIVE_BOOK_INTEGRITY_V1.md` §2.3 priced the restored cluster envelope at
**-36.0 % R/day** against `p_fail_daily -> 0.0000` and `p_pass +4.7…+10.7 pp`, and the owner
turned it on for that trade.  That pricing was computed on the FOUR-sleeve armed book, where
`sub_xvol_pullback` and `sub_mid_dn_revert` BOTH sat in the `substrate` cluster -- 38 of 42
armed symbol slots in one cluster.  Four hours later `sub_mid_dn_revert` was disarmed, so
`substrate` is now a single sleeve and the cap's binding rate necessarily changed.  The cap is
reversible in two minutes (`LIVE_BOOK_INTEGRITY_V1.md` §3.3), so if it is now materially less
useful or materially more costly the owner should be told.

METHOD.  `live_book_integrity_receipts/cluster_envelope_impact.py`'s instrument, unchanged,
parameterised by sleeve set so the three- and four-sleeve books are measured in ONE run under
ONE code path -- a within-corpus A/B/A/B.  The instrument is the correlated UNIT, not the
trade: `admission.size_correlated_units` buckets by `(decision_day, cluster)` and splits
`unit_risk / n` across members (`admission.py:1171-1177`, `:1253`), so a bar-group's return in
unit-risk terms is the MEAN of its members' R.  `book_owner.py:2066` compares `dbar`, so
same-bar members always place and only a LATER-BAR same-cluster fire is blocked.

  cap OFF : every (cluster, day, bar) group is a full fresh unit
  cap ON  : only the day's FIRST bar-group per cluster is a unit; `jpy` is exempt

POPULATION.  `phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz` -- the corrected-armed-set
archive re-walk (22,354 trades, per-trade symbol + `entry_utc` + banded net R).  This is the
ARCHIVE population, NOT the W7 recost cache, so every number here is a WITHIN-CORPUS A/B and
is not comparable to any published `p_pass`.  That is the only claim it needs to support, and
it is the same population `LIVE_BOOK_INTEGRITY_V1.md` §2.3 used -- so the three-sleeve and
four-sleeve numbers here are directly comparable to each other AND to that document.

Usage: python3 cluster_cap_reprice.py [out.json]
"""
from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import math
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[8]
for p in (REPO, REPO / "scripts"):
    sys.path.insert(0, str(p))

from src.components.ultimate_book import admission as A     # noqa: E402
from src.safety.armed_set import armed_sleeves              # noqa: E402
import mc_firm_rules as Q                                   # noqa: E402

ROWS = (REPO / "docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts"
        / "R1_ESTATE_ROWS_V2.json.gz")
EXEMPT = {"jpy"}          # config/agent_config.yaml ultimate_book_cluster_cap_exempt_clusters
PATHS = 40000
N_BOOT = 20000

mx, _err = A.resolve_market_expansion_sleeves(
    policy="positive_weighted12_after_swap", explicit_sleeves=())
REG = A.effective_registry(include_clean3=True, include_candidate_book=True,
                           include_market_expansion_book=True, market_expansion_sleeves=mx)
CONF = {k: float(v.confidence) for k, v in REG.items()}

THREE = sorted(armed_sleeves())                             # the live set today
FOUR = sorted(set(THREE) | {"sub_mid_dn_revert"})           # the set §2.3 priced

D = json.load(gzip.open(ROWS))


def unit_series(rows, rkey="r_new_mid", conf_weight=True, shift_h=0):
    """(days, cap_off_day_R, cap_on_day_R, stats) -- verbatim from cluster_envelope_impact."""
    byday: dict = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        t = dt.datetime.fromisoformat(r["entry_utc"]) + dt.timedelta(hours=shift_h)
        cl = A.cluster_of(r["sleeve"], REG) or "__unknown__"
        byday[(cl, t.date().isoformat())][t.isoformat()].append(r)
    off, on = collections.defaultdict(float), collections.defaultdict(float)
    n_off = n_on = bound = first_bar_multi = 0
    blocked_new_symbol = blocked_repeat_symbol = 0
    per_cluster_blocked: dict = collections.Counter()
    per_cluster_buckets: dict = collections.Counter()
    per_cluster_bound: dict = collections.Counter()
    gaps: list[float] = []
    for (cl, day), bars in byday.items():
        per_cluster_buckets[cl] += 1
        order = sorted(bars)
        if len(bars[order[0]]) > 1 and len({x["symbol"] for x in bars[order[0]]}) > 1:
            first_bar_multi += 1
        if len(order) > 1 and cl not in EXEMPT:
            bound += 1
            per_cluster_bound[cl] += 1
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
            else:
                per_cluster_blocked[cl] += 1
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
        "blocked_repeat_share_pct": (
            round(100.0 * blocked_repeat_symbol
                  / max(1, blocked_repeat_symbol + blocked_new_symbol), 2)),
        "buckets_whose_FIRST_bar_is_multi_symbol_never_blocked": first_bar_multi,
        "blocked_bar_gap_hours_median": round(statistics.median(gaps), 2) if gaps else None,
        "per_cluster_buckets": dict(per_cluster_buckets),
        "per_cluster_buckets_where_cap_binds": dict(per_cluster_bound),
        "per_cluster_units_blocked": dict(per_cluster_blocked),
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
                   for _ in range(N_BOOT))
    mu_off, mu_on = statistics.fmean(so), statistics.fmean(sn)
    sd = statistics.stdev(diff) if n > 1 else 0.0
    return {
        "n_days": n,
        "r_per_day_cap_off": round(mu_off, 5),
        "r_per_day_cap_on": round(mu_on, 5),
        "r_per_day_pct_change": round(100.0 * (mu_on - mu_off) / abs(mu_off), 2) if mu_off else None,
        "paired_delta_r_per_day": round(statistics.fmean(diff), 5),
        "paired_delta_ci95": [round(boots[int(0.025 * N_BOOT)], 5),
                              round(boots[int(0.975 * N_BOOT) - 1], 5)],
        "paired_delta_t": round(statistics.fmean(diff) / (sd / math.sqrt(n)), 3) if sd else None,
        "sd_day_cap_off": round(statistics.pstdev(so), 5),
        "sd_day_cap_on": round(statistics.pstdev(sn), 5),
        "worst_day_cap_off": round(min(so), 4),
        "worst_day_cap_on": round(min(sn), 4),
        "max_drawdown_r_cap_off": round(maxdd(so), 3),
        "max_drawdown_r_cap_on": round(maxdd(sn), 3),
    }


out = {
    "schema": "gtos.wave21.cluster_cap_reprice.v1",
    "measurement_only": True,
    "population": ("ARCHIVE (R1_ESTATE_ROWS_V2) -- within-corpus A/B ONLY, not comparable to "
                   "the W7-cache p_pass figures; same population and instrument as "
                   "LIVE_BOOK_INTEGRITY_V1 §2.3, so the two are comparable to each other"),
    "books": {"THREE_SLEEVE_ARMED": THREE, "FOUR_SLEEVE_PRIOR": FOUR},
    "confidences": {s: CONF.get(s) for s in FOUR},
    "clusters": {s: A.cluster_of(s, REG) for s in FOUR},
    "exempt_clusters": sorted(EXEMPT),
    "mc_paths": PATHS,
    "arms": {},
}

for bname, book in (("THREE_SLEEVE_ARMED", THREE), ("FOUR_SLEEVE_PRIOR", FOUR)):
    armed_rows = [r for r in D if r["sleeve"] in book]
    fwd_rows = [r for r in armed_rows if r["entry_utc"] >= "2025-01-01"]
    blk = {"n_trades_all_years": len(armed_rows), "n_trades_forward": len(fwd_rows),
           "robustness": {}, "decision": {}}

    for band in ("r_new_low", "r_new_mid", "r_new_high", "r_old"):
        for cw in (True, False):
            d, so, sn, stt = unit_series(armed_rows, rkey=band, conf_weight=cw)
            blk["robustness"][f"{band}|conf_weighted={cw}"] = {**stt, **econ(d, so, sn)}
    for sh in (-2, 2):
        d, so, sn, stt = unit_series(armed_rows, shift_h=sh)
        blk["robustness"][f"r_new_mid|day_boundary_shift={sh:+d}h"] = {**stt, **econ(d, so, sn)}

    for wlabel, rws in (("all_years", armed_rows), ("forward_2025_plus", fwd_rows)):
        d, so, sn, stt = unit_series(rws)
        blk["decision"][wlabel] = {"stats": stt, "econ": econ(d, so, sn), "mc": {}}
        for acct in ("FTMO", "redacted_account"):
            rule = [r for r in Q.rule_sets(acct)[0] if r.label == "P2_BOTH_PHASES"][0]
            for risk, rlabel in ((0.020, "dial_2.000pct"),
                                 (0.011968, "measured_live_1.1968pct")):
                a = Q.mc(so, risk, rule, PATHS, seed_base=1)
                b = Q.mc(sn, risk, rule, PATHS, seed_base=1)
                blk["decision"][wlabel]["mc"][f"{acct}|{rlabel}"] = {
                    "cap_off": {"p_pass": round(a["p_pass"], 6), "se": round(a["se_p_pass"], 6),
                                "p_fail_daily": round(a["p_fail_daily"], 6),
                                "p_fail_dd": round(a["p_fail_dd"], 6)},
                    "cap_on": {"p_pass": round(b["p_pass"], 6), "se": round(b["se_p_pass"], 6),
                               "p_fail_daily": round(b["p_fail_daily"], 6),
                               "p_fail_dd": round(b["p_fail_dd"], 6)},
                    "delta_p_pass": round(b["p_pass"] - a["p_pass"], 6),
                    "delta_p_fail_daily": round(b["p_fail_daily"] - a["p_fail_daily"], 6),
                }
    out["arms"][bname] = blk

# ---- the head-to-head the owner needs ------------------------------------------------
h2h = {}
for wlabel in ("all_years", "forward_2025_plus"):
    row = {}
    for bname in ("FOUR_SLEEVE_PRIOR", "THREE_SLEEVE_ARMED"):
        e = out["arms"][bname]["decision"][wlabel]["econ"]
        s = out["arms"][bname]["decision"][wlabel]["stats"]
        row[bname] = {"bind_rate_pct": s["bind_rate_pct"],
                      "units_blocked": s["units_blocked"],
                      "units_blocked_pct": s["units_blocked_pct"],
                      "blocked_repeat_share_pct": s["blocked_repeat_share_pct"],
                      "r_per_day_cap_off": e["r_per_day_cap_off"],
                      "r_per_day_cap_on": e["r_per_day_cap_on"],
                      "r_per_day_pct_change": e["r_per_day_pct_change"],
                      "paired_delta_r_per_day": e["paired_delta_r_per_day"],
                      "paired_delta_ci95": e["paired_delta_ci95"],
                      "worst_day_cap_off": e["worst_day_cap_off"],
                      "worst_day_cap_on": e["worst_day_cap_on"],
                      "mc": {k: {"delta_p_pass": v["delta_p_pass"],
                                 "p_fail_daily_off": v["cap_off"]["p_fail_daily"],
                                 "p_fail_daily_on": v["cap_on"]["p_fail_daily"],
                                 "p_pass_off": v["cap_off"]["p_pass"],
                                 "p_pass_on": v["cap_on"]["p_pass"]}
                             for k, v in out["arms"][bname]["decision"][wlabel]["mc"].items()}}
    h2h[wlabel] = row
out["head_to_head"] = h2h

DEST = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "CLUSTER_CAP_REPRICE_V1.json"
DEST.write_text(json.dumps(out, indent=1))
print("WROTE", DEST)
for w, row in h2h.items():
    print(f"\n=== {w} ===")
    for bname, v in row.items():
        print(f"{bname:19s} bind {v['bind_rate_pct']:5.2f}%  blocked {v['units_blocked']:4d} "
              f"({v['units_blocked_pct']:5.2f}%)  repeat {v['blocked_repeat_share_pct']:5.1f}%  "
              f"R/day {v['r_per_day_cap_off']:+.5f} -> {v['r_per_day_cap_on']:+.5f} "
              f"({v['r_per_day_pct_change']:+.1f}%)  worst {v['worst_day_cap_off']:+.3f} -> "
              f"{v['worst_day_cap_on']:+.3f}")
        for k, m in v["mc"].items():
            print(f"    {k:38s} p_pass {m['p_pass_off']:.4f} -> {m['p_pass_on']:.4f} "
                  f"({m['delta_p_pass']:+.4f})  p_fail_daily {m['p_fail_daily_off']:.4f} -> "
                  f"{m['p_fail_daily_on']:.4f}")
