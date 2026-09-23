#!/usr/bin/env python3
"""B2 step 2: score every declared arm and comparator on the five sealed months.

Frozen spec: B2_SPEC_V1.json (sha256 6d4ebdea…).  The funnel below is adapted
from lane3_receipts/funnel_lib.py (Lane 3's exact reproduction of the frozen
`select()`); the ONLY change is that the score is supplied from an external
{occurrence_key: value} map instead of being read off the row, so every arm runs
through byte-identical gates.

Usage:  b2_score.py <step>
  step=validate   reproduce the three sealed reads with the shipped score
  step=arms       run every arm + comparator, per month and pooled
  step=pickrate   the ceiling-capture / reversal test for every ranker
  step=crux       the MARKET-top-abstain re-decision under composition
Each step checkpoints its own JSON and can be re-run independently.
"""
from __future__ import annotations

import gzip
import json
import math
import pickle
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

CACHE = Path("/private/tmp/w21-puzzle-cache")
HERE = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/b2")
LANE3 = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane3/out")
OUT = Path(
    "/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725/"
    "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/"
    "outcome_authority/swarm2/breakthrough/b2_composed_rule"
)
OUT.mkdir(parents=True, exist_ok=True)

MONTHS = ("feb", "apr", "may", "jun", "jul")
MAX_COST_R = 0.20
MIN_EXPECTED_NET_R = 0.10
RESOLVED_STATUS_TO_STATE = {
    "RESOLVED_NO_FILL": "NO_FILL",
    "RESOLVED_FILLED_TARGET": "TARGET",
    "RESOLVED_FILLED_STOP": "STOP",
    "RESOLVED_FILLED_TIME_STOP": "TIME_STOP",
}
KEEP = (
    "candidate_occurrence_key", "decision_window_id", "trading_day",
    "label_span_start_utc", "label_span_end_utc", "expiry_utc",
    "symbol", "origin_family", "proposed_order_type",
    "cost_r", "deductible_cost_r", "terminal_net_r",
    "lifecycle_label_status", "predecision_geometry_valid", "month",
)
RNG = np.random.default_rng(20260812)

# sealed values, for the instrument check (Lane 3 §1, from the sealed results)
SEALED = {
    "feb": {"top_below_0p10": 1164, "top_limit_abstain": 601, "trade": 106,
            "actual": 14.168399},
    "apr": {"top_below_0p10": 1447, "top_limit_abstain": 344, "trade": 50,
            "actual": -7.742114},
    "may": {"top_below_0p10": 1265, "top_limit_abstain": 374, "trade": 17,
            "actual": 5.130257},
    "jun": {"top_below_0p10": 1575, "top_limit_abstain": 414, "trade": 49,
            "actual": 3.963843},
    "jul": {"top_below_0p10": 1537, "top_limit_abstain": 226, "trade": 68,
            "actual": -14.566020},
}


# ------------------------------------------------------------------ primitives
def at(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def state_of(row):
    status = str(row.get("lifecycle_label_status") or "")
    if status in RESOLVED_STATUS_TO_STATE:
        return RESOLVED_STATUS_TO_STATE[status]
    if status.startswith("CENSORED_"):
        return None
    raise ValueError(f"unknown lifecycle status: {status!r}")


def load_rows():
    out = []
    for month in MONTHS:
        with gzip.open(CACHE / f"rows_{month}.pkl.gz", "rb") as fh:
            raw = pickle.load(fh)
        for src in raw:
            row = {k: src.get(k) for k in KEEP}
            row["month"] = month
            row["state"] = state_of(src)
            row["resolved"] = row["state"] is not None
            out.append(row)
        del raw
    return out


def net_actual(row):
    return float(row.get("terminal_net_r") or 0.0) if row["resolved"] else None


def net_wc(row):
    if row["resolved"]:
        return float(row.get("terminal_net_r") or 0.0)
    try:
        dc = float(row.get("deductible_cost_r"))
    except (TypeError, ValueError):
        dc = 0.0
    return -1.0 - dc


def is_eligible(row):
    if not row["predecision_geometry_valid"]:
        return False
    try:
        cost = float(row["cost_r"])
    except (TypeError, ValueError):
        return False
    return math.isfinite(cost) and cost <= MAX_COST_R


# ------------------------------------------------------------------ the funnel
def run_funnel(rows, score, *, abstain=True, min_pred=MIN_EXPECTED_NET_R,
               market_only=False, random_pick=False, rng=None, diagnose=False):
    """Adapted from lane3_receipts/funnel_lib.run_funnel.

    `score` maps candidate_occurrence_key -> float (or None -> row is dropped
    from ranking, counted).  Gates G0..G5 are otherwise byte-identical.
    """
    eligible, no_score = [], 0
    for row in rows:
        if not is_eligible(row):
            continue
        if not random_pick:
            value = score.get(row["candidate_occurrence_key"])
            if value is None:
                no_score += 1
                continue
            row = dict(row, _score=float(value))
        else:
            row = dict(row, _score=0.0)
        eligible.append(row)

    by_window = defaultdict(list)
    for row in eligible:
        by_window[row["decision_window_id"]].append(row)
    ordered = sorted(
        by_window.values(),
        key=lambda vals: (min(at(r["label_span_start_utc"]) for r in vals),
                          vals[0]["decision_window_id"]),
    )

    active, selected, disp, windows = {}, [], Counter(), []
    for candidates in ordered:
        decision_at = min(at(r["label_span_start_utc"]) for r in candidates)
        active = {s: e for s, e in active.items() if e > decision_at}
        available = [r for r in candidates if r["symbol"] not in active]
        if market_only:
            available = [r for r in available if r["proposed_order_type"] == "MARKET"]
        if not available:
            disp["no_available_candidate"] += 1
            continue
        if random_pick:
            top = available[rng.integers(0, len(available))]
        else:
            top = max(available, key=lambda r: (r["_score"], -float(r["cost_r"]),
                                                r["candidate_occurrence_key"]))
        if diagnose:
            windows.append(_window_record(available, top))
        if not random_pick and top["_score"] < min_pred:
            disp["top_below_0p10"] += 1
            if diagnose:
                windows[-1]["outcome_gate"] = "G4_top_below_min_pred"
            continue
        if abstain and top["proposed_order_type"] != "MARKET":
            disp["top_limit_abstain"] += 1
            if diagnose:
                windows[-1]["outcome_gate"] = "G5_market_top_abstain"
            continue
        disp["trade"] += 1
        if diagnose:
            windows[-1]["outcome_gate"] = "TRADED"
        selected.append(top)
        active[top["symbol"]] = at(top["label_span_end_utc"] or top["expiry_utc"])
    result = (selected, dict(sorted(disp.items())), no_score)
    return result + (windows,) if diagnose else result


def _window_record(available, top):
    act = [net_actual(r) for r in available]
    res = [a for a in act if a is not None]
    order = sorted(available, key=lambda r: (r["_score"], -float(r["cost_r"]),
                                             r["candidate_occurrence_key"]),
                   reverse=True)
    return {
        "trading_day": top["trading_day"],
        "month": top["month"],
        "decision_hour": at(top["label_span_start_utc"]).hour,
        "n_available": len(available),
        "n_resolved": len(res),
        "top_score": top["_score"],
        "top_order_type": top["proposed_order_type"],
        "top_family": top["origin_family"],
        "pick_actual": net_actual(top),
        "pick_wc": net_wc(top),
        "rank2_actual": net_actual(order[1]) if len(order) > 1 else None,
        "oracle_max_actual": max(res) if res else None,
        "mean_actual": (sum(res) / len(res)) if res else None,
        "mean_wc": float(np.mean([net_wc(r) for r in available])),
        "n_positive_available": sum(1 for a in res if a > 0),
        "pick_is_window_best": bool(res and net_actual(top) is not None
                                    and net_actual(top) >= max(res) - 1e-12),
        "outcome_gate": None,
    }


# ------------------------------------------------------------------ evaluation
def portfolio(selected, *, all_days):
    resolved = [r for r in selected if r["resolved"]]
    censored = [r for r in selected if not r["resolved"]]
    actual = sum(float(r.get("terminal_net_r") or 0.0) for r in resolved)
    worst = actual + sum(-1.0 - float(r["deductible_cost_r"] or 0.0) for r in censored)
    by_day = defaultdict(float)
    for r in resolved:
        by_day[r["trading_day"]] += float(r.get("terminal_net_r") or 0.0)
    pos = sum(1 for v in by_day.values() if v > 0)
    neg = sum(1 for v in by_day.values() if v < 0)
    return {
        "trades": len(selected),
        "resolved": len(resolved),
        "censored": len(censored),
        "actual_net_r": round(actual, 6),
        "worst_case_net_r": round(worst, 6),
        "outcomes": dict(sorted(Counter(r["state"] or "CENSORED" for r in selected).items())),
        "positive_days": pos,
        "negative_days": neg,
        "gate_1_min_20_resolved_trades": bool(len(resolved) >= 20),
        "gate_2_pooled_worst_case_strictly_positive": bool(worst > 0),
        "gate_3_positive_days_exceed_negative": bool(pos > neg),
        "all_three_gates": bool(len(resolved) >= 20 and worst > 0 and pos > neg),
        "net_by_day": {d: round(v, 6) for d, v in sorted(by_day.items())},
    }


def boot(vals, days, nboot=2000):
    """Day-clustered bootstrap, identical to lane3_receipts/step6_geometry.boot."""
    if not len(vals):
        return None
    by = defaultdict(list)
    for v, d in zip(vals, days):
        by[d].append(v)
    arrs = [np.asarray(by[k], dtype=float) for k in sorted(by)]
    n = len(arrs)
    o = np.asarray([np.concatenate([arrs[i] for i in RNG.integers(0, n, n)]).mean()
                    for _ in range(nboot)])
    return {"point": float(np.mean(vals)), "n": int(len(vals)),
            "ci95_lo": float(np.percentile(o, 2.5)),
            "ci95_hi": float(np.percentile(o, 97.5)),
            "p_two_sided_sign": float(2 * min((o <= 0).mean(), (o >= 0).mean()))}


def write(name, payload):
    path = OUT / name
    path.write_text(json.dumps(payload, indent=1, sort_keys=True, default=float) + "\n")
    print("WROTE", path, flush=True)


# ------------------------------------------------------------------ score maps
def load_scores():
    with gzip.open(LANE3 / "preds_daily.pkl.gz", "rb") as fh:
        shipped = pickle.load(fh)
    composed = None
    path = HERE / "scores_daily.pkl.gz"
    if path.exists():
        with gzip.open(path, "rb") as fh:
            composed = pickle.load(fh)
    return shipped, composed


def score_map(composed, field):
    return {k: v[field] for k, v in composed.items()}


# ------------------------------------------------------------------ steps
def step_validate(rows, shipped):
    report = {"schema": "gtos.swarm2.b2.instrument_validation.v1",
              "purpose": "reproduce the three sealed reads with the shipped score "
                         "before any composed number is reported (spec commitment)",
              "months": {}}
    ok = True
    for month in MONTHS:
        sub = [r for r in rows if r["month"] == month]
        sel, disp, _ = run_funnel(sub, shipped)
        pf = portfolio(sel, all_days=None)
        exp = SEALED[month]
        match = (disp.get("top_below_0p10") == exp["top_below_0p10"]
                 and disp.get("top_limit_abstain") == exp["top_limit_abstain"]
                 and disp.get("trade") == exp["trade"]
                 and abs(pf["actual_net_r"] - exp["actual"]) < 1e-3)
        ok = ok and match
        report["months"][month] = {
            "sealed": exp, "reproduced_dispositions": disp,
            "reproduced_actual_net_r": pf["actual_net_r"], "exact_match": match}
    report["all_five_months_reproduce"] = ok
    write("instrument_validation.json", report)
    return ok


ARMS = [
    ("A1_PRIMARY_composed_floor0p10_abstain", "composed", 0.10, True),
    ("A2_composed_floor0p00_abstain", "composed", 0.0, True),
    ("A3_composed_floor0p10_no_abstain", "composed", 0.10, False),
    ("A4_composed_floor0p00_no_abstain", "composed", 0.0, False),
    ("A5_e_net_given_fill_only_floor0p10_abstain", "e_net_given_fill", 0.10, True),
    ("A6_jeffreys_composed_floor0p10_abstain", "composed_jeffreys", 0.10, True),
    ("A7_p_fill_only_abstain", "p_fill", -1e9, True),
]


def step_arms(rows, shipped, composed):
    days_all = sorted({r["trading_day"] for r in rows})
    report = {"schema": "gtos.swarm2.b2.arms.v1",
              "spec_sha256": "6d4ebdea10fd1b8249e9d94c62504d2e2ff80ff5eee98efe041d908dae82e62e",
              "n_trading_days": len(days_all), "arms": {}, "comparators": {}}

    def run_and_record(bucket, name, smap, *, abstain, min_pred,
                       market_only=False):
        entry = {"pooled": None, "by_month": {}}
        sel, disp, ns = run_funnel(rows, smap, abstain=abstain, min_pred=min_pred,
                                   market_only=market_only)
        entry["pooled"] = portfolio(sel, all_days=days_all)
        entry["pooled"]["dispositions"] = disp
        entry["pooled"]["rows_without_a_score"] = ns
        for month in MONTHS:
            sub = [r for r in rows if r["month"] == month]
            s, d, _ = run_funnel(sub, smap, abstain=abstain, min_pred=min_pred,
                                 market_only=market_only)
            entry["by_month"][month] = portfolio(s, all_days=None)
            entry["by_month"][month]["dispositions"] = d
        entry["config"] = {"abstain": abstain, "min_pred": min_pred,
                           "market_only": market_only}
        bucket[name] = entry
        print(f"  {name}: trades={entry['pooled']['trades']} "
              f"actual={entry['pooled']['actual_net_r']} "
              f"wc={entry['pooled']['worst_case_net_r']}", flush=True)
        return entry

    # comparators first — C1 is the +0.954 R book of record
    run_and_record(report["comparators"], "C1_shipped_market_top_abstain", shipped,
                   abstain=True, min_pred=0.10)
    run_and_record(report["comparators"], "C2_shipped_naive_mixed", shipped,
                   abstain=False, min_pred=0.10)
    run_and_record(report["comparators"], "C3_shipped_market_rerank", shipped,
                   abstain=True, min_pred=0.10, market_only=True)

    # C4 random: 200 seeded replicates, uniform within the eligible post-occupancy set
    reps = []
    for seed in range(200):
        rng = np.random.default_rng(20260812 + seed)
        sel, _, _ = run_funnel(rows, {}, abstain=False, min_pred=-1e9,
                               random_pick=True, rng=rng)
        pf = portfolio(sel, all_days=days_all)
        reps.append((pf["trades"], pf["actual_net_r"], pf["worst_case_net_r"]))
    arr = np.asarray(reps, dtype=float)
    report["comparators"]["C4_random_within_eligible"] = {
        "replicates": 200,
        "mean_trades": float(arr[:, 0].mean()),
        "mean_actual_net_r": float(arr[:, 1].mean()),
        "actual_p05": float(np.percentile(arr[:, 1], 5)),
        "actual_p95": float(np.percentile(arr[:, 1], 95)),
        "mean_worst_case_net_r": float(arr[:, 2].mean()),
    }
    print("  C4_random:", report["comparators"]["C4_random_within_eligible"], flush=True)

    if composed is not None:
        for name, field, floor, abstain in ARMS:
            run_and_record(report["arms"], name, score_map(composed, field),
                           abstain=abstain, min_pred=floor)

    write("arms.json", report)
    return report


def step_pickrate(rows, shipped, composed):
    """Ceiling-capture / reversal test, method identical to Lane 3 step6."""
    report = {"schema": "gtos.swarm2.b2.pickrate.v1",
              "baselines": {"pick_positive_uniform": 0.0862,
                            "pick_best_uniform": 0.0264},
              "shipped_published": {"pick_positive": 0.0722, "pick_best": 0.0184},
              "rankers": {}}
    maps = {"shipped": shipped}
    if composed is not None:
        maps["composed"] = score_map(composed, "composed")
        maps["e_net_given_fill"] = score_map(composed, "e_net_given_fill")
        maps["p_fill"] = score_map(composed, "p_fill")
        maps["composed_jeffreys"] = score_map(composed, "composed_jeffreys")

    # `basis` controls the occupancy path the window records are cut from.
    #   open  : abstain=False, min_pred=-inf  -> every window reaching G3, but the
    #           symbol is occupied on every window, so the available sets differ
    #           from the shipped run.
    #   policy: abstain=True, min_pred=0.10   -> each ranker measured inside the
    #           funnel it would actually run; reproduces Lane 3's published
    #           shipped values 0.0722 / 0.0184.
    basis = report.setdefault("bases", {})
    for basis_name, kwargs in (("open", {"abstain": False, "min_pred": -1e9}),
                               ("policy", {"abstain": True, "min_pred": 0.10})):
        basis[basis_name] = _pickrate_basis(rows, maps, **kwargs)
        for name, entry in basis[basis_name].items():
            print(f"  [{basis_name}] {name}: "
                  f"pick+={entry['pick_positive_rate']['ranker']['point']:.4f} "
                  f"best={entry['pick_best_rate_strict']['ranker']['point']:.4f} "
                  f"meanR={entry['mean_realized_r_of_pick']['point']:.5f}", flush=True)
    report["rankers"] = basis["open"]
    write("pickrate.json", report)
    return report


def _pickrate_basis(rows, maps, **kwargs):
    out = {}
    for name, smap in maps.items():
        _, _, _, wins = run_funnel(rows, smap, diagnose=True, **kwargs)
        strict = [w for w in wins if w["oracle_max_actual"] is not None
                  and w["pick_actual"] is not None]
        hit = [1.0 if (w["pick_actual"] or 0) > 0 else 0.0 for w in strict]
        base = [w["n_positive_available"] / w["n_available"] for w in strict]
        hd = [w["trading_day"] for w in strict]
        bestw = [w for w in wins if w["oracle_max_actual"] is not None
                 and w["oracle_max_actual"] > 0]
        bh = [1.0 if w["pick_is_window_best"] else 0.0 for w in bestw]
        bb = [1.0 / w["n_available"] for w in bestw]
        bd = [w["trading_day"] for w in bestw]
        scored = [w for w in wins if w["pick_actual"] is not None]
        out[name] = {
            "n_windows": len(wins),
            "pick_positive_rate": {
                "windows": len(hit),
                "ranker": boot(hit, hd),
                "uniform_baseline": float(np.mean(base)) if base else None,
                "ranker_minus_uniform": boot([h - b for h, b in zip(hit, base)], hd),
            },
            "pick_best_rate_strict": {
                "windows": len(bestw),
                "ranker": boot(bh, bd),
                "uniform_baseline": float(np.mean(bb)) if bb else None,
                "ranker_minus_uniform": boot([a - b for a, b in zip(bh, bb)], bd),
            },
            "mean_realized_r_of_pick": boot([w["pick_actual"] for w in scored],
                                            [w["trading_day"] for w in scored]),
            "vs_uniform_mean_r": boot(
                [w["pick_actual"] - w["mean_actual"] for w in scored
                 if w["mean_actual"] is not None],
                [w["trading_day"] for w in scored if w["mean_actual"] is not None]),
            "top_order_type_mix": dict(Counter(w["top_order_type"] for w in wins)),
            "top_no_fill_share": float(np.mean(
                [1.0 if (w["pick_actual"] == 0.0) else 0.0 for w in scored])),
            "top_censor_rate": float(np.mean(
                [0.0 if w["pick_actual"] is not None else 1.0 for w in wins])),
            "oracle_ceiling_r_per_window": float(np.mean(
                [w["oracle_max_actual"] for w in wins
                 if w["oracle_max_actual"] is not None])),
        }
    return out


def step_crux(rows, shipped, composed):
    """The MARKET-top-abstain re-decision under composition.

    Under the shipped score, abstaining avoided -73.63 R (p 0.038).  The
    question: under a statistic that explicitly prices non-fill, does the set of
    windows the rule abstains from become profitable to take?
    """
    report = {"schema": "gtos.swarm2.b2.abstain_crux.v1", "scores": {}}
    maps = {"shipped": shipped}
    if composed is not None:
        maps["composed"] = score_map(composed, "composed")
        maps["e_net_given_fill"] = score_map(composed, "e_net_given_fill")

    for name, smap in maps.items():
        _, _, _, wins = run_funnel(rows, smap, abstain=True,
                                   min_pred=MIN_EXPECTED_NET_R, diagnose=True)
        ab = [w for w in wins if w["outcome_gate"] == "G5_market_top_abstain"]
        res = [w for w in ab if w["pick_actual"] is not None]
        entry = {
            "windows_abstained": len(ab),
            "resolved_of_those": len(res),
            "take_the_limit_top_instead": {
                "total_actual_r": float(np.sum([w["pick_actual"] for w in res])),
                "per_window": boot([w["pick_actual"] for w in res],
                                   [w["trading_day"] for w in res]),
            },
            "abstain_books_exactly": 0.0,
            "value_of_abstaining_r": -float(np.sum([w["pick_actual"] for w in res])),
        }
        # the conditional that reverses it (Lane 3 §4.3): E[net | LIMIT top fills]
        filled = [w["pick_actual"] for w in res if w["pick_actual"] != 0.0]
        entry["e_net_given_limit_top_fills"] = {
            "n": len(filled),
            "mean": float(np.mean(filled)) if filled else None,
            "boot": boot(filled, [w["trading_day"] for w in res
                                  if w["pick_actual"] != 0.0]) if filled else None,
        }
        entry["no_fill_share_of_abstained_tops"] = (
            float(np.mean([1.0 if w["pick_actual"] == 0.0 else 0.0 for w in res]))
            if res else None)
        report["scores"][name] = entry
        print(f"  {name}: abstained={len(ab)} take-instead="
              f"{entry['take_the_limit_top_instead']['total_actual_r']:.2f} R "
              f"E[net|fills]={entry['e_net_given_limit_top_fills']['mean']}", flush=True)
    write("abstain_crux.json", report)
    return report


def run_funnel_veto(rows, score, veto, *, abstain=True, min_pred=MIN_EXPECTED_NET_R,
                    limit_rescue=None):
    """Shipped ranker + a composed-statistic condition applied to the CHOSEN top.

    `veto(key) -> bool` must be True for the trade to be taken (applied after
    G4 and, when `abstain`, after G5).  `limit_rescue(key) -> bool`, when given,
    REPLACES G5: a LIMIT top is taken iff limit_rescue says so.
    This is the constructive direction implied by A1's failure: composition is
    used to VETO the shipped selection, not to replace the ranker, so the
    shipped argmax's low fill rate is preserved.
    """
    eligible = []
    for row in rows:
        if not is_eligible(row):
            continue
        value = score.get(row["candidate_occurrence_key"])
        if value is None:
            continue
        eligible.append(dict(row, _score=float(value)))

    by_window = defaultdict(list)
    for row in eligible:
        by_window[row["decision_window_id"]].append(row)
    ordered = sorted(
        by_window.values(),
        key=lambda vals: (min(at(r["label_span_start_utc"]) for r in vals),
                          vals[0]["decision_window_id"]),
    )
    active, selected, disp = {}, [], Counter()
    for candidates in ordered:
        decision_at = min(at(r["label_span_start_utc"]) for r in candidates)
        active = {s: e for s, e in active.items() if e > decision_at}
        available = [r for r in candidates if r["symbol"] not in active]
        if not available:
            disp["no_available_candidate"] += 1
            continue
        top = max(available, key=lambda r: (r["_score"], -float(r["cost_r"]),
                                            r["candidate_occurrence_key"]))
        if top["_score"] < min_pred:
            disp["top_below_0p10"] += 1
            continue
        key = top["candidate_occurrence_key"]
        if top["proposed_order_type"] != "MARKET":
            if limit_rescue is not None:
                if not limit_rescue(key):
                    disp["limit_top_not_rescued"] += 1
                    continue
            elif abstain:
                disp["top_limit_abstain"] += 1
                continue
        if veto is not None and not veto(key):
            disp["composed_veto"] += 1
            continue
        disp["trade"] += 1
        selected.append(top)
        active[top["symbol"]] = at(top["label_span_end_utc"] or top["expiry_utc"])
    return selected, dict(sorted(disp.items()))


def step_constructive(rows, shipped, composed):
    """B-arms: POST-HOC, IN-SAMPLE constructive variants.

    Declared as such: these were chosen AFTER seeing A1 fail, so they are
    hypothesis-generating only and are counted in the multiplicity bill.
    """
    days_all = sorted({r["trading_day"] for r in rows})
    enf = score_map(composed, "e_net_given_fill")
    cmp_ = score_map(composed, "composed")
    report = {
        "schema": "gtos.swarm2.b2.constructive.v1",
        "status": "POST_HOC_IN_SAMPLE_HYPOTHESIS_ONLY_NOT_AN_ADMISSION",
        "declared": "chosen after A1 failed; counted in the multiplicity bill; "
                    "pre-registration-pending on data this lane must not touch",
        "arms": {},
    }
    specs = {
        "B1_shipped_rank_plus_e_net_given_fill_positive_veto":
            dict(veto=lambda k: enf.get(k, -1.0) > 0.0),
        "B2_shipped_rank_plus_composed_ge_0p10_veto":
            dict(veto=lambda k: cmp_.get(k, -1.0) >= 0.10),
        "B3_shipped_rank_composed_limit_rescue_ge_0p10":
            dict(veto=None, limit_rescue=lambda k: cmp_.get(k, -1.0) >= 0.10),
        "B4_shipped_rank_composed_limit_rescue_e_net_positive":
            dict(veto=None, limit_rescue=lambda k: enf.get(k, -1.0) > 0.0),
    }
    for name, kw in specs.items():
        sel, disp = run_funnel_veto(rows, shipped, **kw)
        entry = {"pooled": portfolio(sel, all_days=days_all), "by_month": {}}
        entry["pooled"]["dispositions"] = disp
        for month in MONTHS:
            sub = [r for r in rows if r["month"] == month]
            s, d = run_funnel_veto(sub, shipped, **kw)
            entry["by_month"][month] = portfolio(s, all_days=None)
        report["arms"][name] = entry
        print(f"  {name}: trades={entry['pooled']['trades']} "
              f"actual={entry['pooled']['actual_net_r']} "
              f"wc={entry['pooled']['worst_case_net_r']} "
              f"gates={entry['pooled']['all_three_gates']}", flush=True)
    write("constructive.json", report)
    return report


def step_headtohead(rows, shipped, composed):
    """Day-clustered bootstrap of each arm's per-day R against the shipped book."""
    days_all = sorted({r["trading_day"] for r in rows})
    enf = score_map(composed, "e_net_given_fill")
    cmp_ = score_map(composed, "composed")

    runs = {}
    sel, _, _ = run_funnel(rows, shipped, abstain=True, min_pred=0.10)
    runs["C1_shipped"] = portfolio(sel, all_days=days_all)["net_by_day"]
    for name, field, floor, abstain in ARMS:
        sel, _, _ = run_funnel(rows, score_map(composed, field), abstain=abstain,
                               min_pred=floor)
        runs[name] = portfolio(sel, all_days=days_all)["net_by_day"]
    for name, kw in (
        ("B1_shipped_rank_plus_e_net_given_fill_positive_veto",
         dict(veto=lambda k: enf.get(k, -1.0) > 0.0)),
        ("B2_shipped_rank_plus_composed_ge_0p10_veto",
         dict(veto=lambda k: cmp_.get(k, -1.0) >= 0.10)),
        ("B3_shipped_rank_composed_limit_rescue_ge_0p10",
         dict(veto=None, limit_rescue=lambda k: cmp_.get(k, -1.0) >= 0.10)),
        ("B4_shipped_rank_composed_limit_rescue_e_net_positive",
         dict(veto=None, limit_rescue=lambda k: enf.get(k, -1.0) > 0.0)),
    ):
        sel, _ = run_funnel_veto(rows, shipped, **kw)
        runs[name] = portfolio(sel, all_days=days_all)["net_by_day"]

    base = runs["C1_shipped"]
    report = {"schema": "gtos.swarm2.b2.headtohead.v1",
              "cluster_unit": "trading_day", "n_days": len(days_all),
              "reference": "C1_shipped (+0.954 R five-month book of record)",
              "arms": {}}
    for name, byday in runs.items():
        if name == "C1_shipped":
            continue
        diff = [byday.get(d, 0.0) - base.get(d, 0.0) for d in days_all]
        report["arms"][name] = {
            "arm_total_r": round(sum(byday.values()), 6),
            "shipped_total_r": round(sum(base.values()), 6),
            "total_difference_r": round(sum(diff), 6),
            "per_day_difference": boot(diff, days_all),
        }
        b = report["arms"][name]["per_day_difference"]
        print(f"  {name}: total {report['arms'][name]['total_difference_r']:+.3f} R  "
              f"per-day {b['point']:+.5f} CI[{b['ci95_lo']:+.5f},{b['ci95_hi']:+.5f}] "
              f"p={b['p_two_sided_sign']:.3f}", flush=True)
    write("headtohead.json", report)
    return report


def step_leaktest(rows, shipped, composed):
    """Temporal-leak controls, run after a sibling lane killed a finding as lookahead.

    The sibling's leak was a SAME-DAY AGGREGATE feature (a median over every
    eligible candidate on the trading day, including candidates generated after
    the scored trade).  This build's feature basis contains no aggregate of any
    kind, so that specific defect has no target here -- but the frozen chain does
    carry one real temporal weakness, and it is tested rather than argued:
    `resolved_eligible` absorbs a day's rows wholesale the moment the day is
    scored, so a label whose span ends after the next day begins is in training
    before its outcome could be known.  Measured: 5.0 % of rows, horizon capped
    at exactly 1.0 day.  Two independent controls therefore fully remove it.
    """
    days_all = sorted({r["trading_day"] for r in rows})
    enf_base = score_map(composed, "e_net_given_fill")
    report = {"schema": "gtos.swarm2.b2.leaktest.v1", "variants": {}}

    variants = {"baseline": composed}
    for tag, fname in (("embargo1", "scores_embargo1.pkl.gz"),
                       ("strict_label_availability", "scores_avail.pkl.gz")):
        path = HERE / fname
        if path.exists():
            with gzip.open(path, "rb") as fh:
                variants[tag] = pickle.load(fh)

    for tag, sc in variants.items():
        cmp_ = score_map(sc, "composed")
        enf = score_map(sc, "e_net_given_fill")
        entry = {"n_scores": len(sc)}
        sel, _, _ = run_funnel(rows, cmp_, abstain=True, min_pred=0.10)
        entry["A1_composed"] = portfolio(sel, all_days=days_all)
        sel, _, _ = run_funnel(rows, enf, abstain=True, min_pred=0.10)
        entry["A5_e_net_given_fill"] = portfolio(sel, all_days=days_all)
        sel, _ = run_funnel_veto(rows, shipped,
                                 veto=lambda k, c=cmp_: c.get(k, -1.0) >= 0.10)
        entry["B2_composed_veto"] = portfolio(sel, all_days=days_all)

        # the one positive this lane found: E[net|fill]'s within-window term
        for nm, smap in (("composed", cmp_), ("e_net_given_fill", enf)):
            _, _, _, wins = run_funnel(rows, smap, abstain=True, min_pred=0.10,
                                       diagnose=True)
            sc_w = [w for w in wins if w["pick_actual"] is not None
                    and w["mean_actual"] is not None]
            entry[f"{nm}_selection_vs_uniform"] = boot(
                [w["pick_actual"] - w["mean_actual"] for w in sc_w],
                [w["trading_day"] for w in sc_w])
        report["variants"][tag] = entry
        a1, a5, b2 = (entry["A1_composed"]["actual_net_r"],
                      entry["A5_e_net_given_fill"]["actual_net_r"],
                      entry["B2_composed_veto"]["actual_net_r"])
        s = entry["e_net_given_fill_selection_vs_uniform"]
        print(f"  [{tag}] A1={a1:+.3f} A5={a5:+.3f} B2={b2:+.3f} "
              f"| E[net|fill] selection {s['point']:+.5f} "
              f"CI[{s['ci95_lo']:+.5f},{s['ci95_hi']:+.5f}] p={s['p_two_sided_sign']:.3f}",
              flush=True)

    # past/future split of the EVALUATION: a same-day contamination signature
    # would concentrate the selection term in the later windows.
    report["past_future_split"] = _hour_split(rows, composed)
    write("leaktest.json", report)
    return report


def _hour_split(rows, composed):  # noqa
    """Selection term by decision hour half, for both statistics."""
    out = {}
    hour_of = {}
    for r in rows:
        hour_of[r["decision_window_id"]] = at(r["label_span_start_utc"]).hour
    for nm in ("composed", "e_net_given_fill"):
        _, _, _, wins = run_funnel(rows, score_map(composed, nm), abstain=True,
                                   min_pred=0.10, diagnose=True)
        entry = {}
        for half, keep in (("decision_hour_lt_12", lambda h: h < 12),
                           ("decision_hour_ge_12", lambda h: h >= 12)):
            sub = [w for w in wins
                   if w["pick_actual"] is not None and w["mean_actual"] is not None
                   and keep(w["decision_hour"])]
            entry[half] = boot([w["pick_actual"] - w["mean_actual"] for w in sub],
                               [w["trading_day"] for w in sub])
        out[nm] = entry
        print(f"  [hour split] {nm}: "
              f"<12 {entry['decision_hour_lt_12']['point']:+.5f} "
              f"(n={entry['decision_hour_lt_12']['n']}) | "
              f">=12 {entry['decision_hour_ge_12']['point']:+.5f} "
              f"(n={entry['decision_hour_ge_12']['n']})", flush=True)
    return out


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    rows = load_rows()
    print(f"loaded {len(rows)} rows", flush=True)
    shipped, composed = load_scores()
    print(f"shipped preds {len(shipped)}; composed "
          f"{len(composed) if composed else 'ABSENT'}", flush=True)
    if step in ("validate", "all"):
        step_validate(rows, shipped)
    if step in ("arms", "all"):
        step_arms(rows, shipped, composed)
    if step in ("pickrate", "all"):
        step_pickrate(rows, shipped, composed)
    if step in ("crux", "all"):
        step_crux(rows, shipped, composed)
    if step in ("constructive", "all"):
        step_constructive(rows, shipped, composed)
    if step in ("headtohead", "all"):
        step_headtohead(rows, shipped, composed)
    if step in ("leaktest", "all"):
        step_leaktest(rows, shipped, composed)


if __name__ == "__main__":
    main()
