"""pbg_analyze — reproduction proof, paired earliness table and economics.

    python3 pbg_analyze.py --in /tmp/pbg_full_jan --month 202601 \
        --sealed /tmp/pbg_ref/CJ_SEALED_CANDIDATE_KEYS_202601.tsv.gz \
        --out ../pbg/PBG_JAN_V1.json

Every arm is priced on the same M1 tape, with the same walker, the same
conservative tie rule and the same broker-true cost model.  Nothing is sampled.
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[5]))

import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402

AT_MARKET = (
    "displacement_continuation",
    "liquidity_sweep_reclaim",
    "structural_distance_extreme",
    "volatility_compression_expansion",
    "session_open_range_break",
    "regime_transition_break",
    "cross_asset_lead_lag",
)
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")
# the five at-market families whose PAIRED partial-vs-close delta is positive in
# January (measured, PBG_JAN_V1 -> by_family); carried as a named cohort so the
# selective book can be priced with its own phantom leg charged.
EARLY5 = (
    "displacement_continuation",
    "liquidity_sweep_reclaim",
    "session_open_range_break",
    "regime_transition_break",
    "volatility_compression_expansion",
)
CONTINUATION5 = (
    "displacement_continuation",
    "regime_transition_break",
    "volatility_compression_expansion",
    "session_open_range_break",
    "cross_asset_lead_lag",
)


def setup_key(r):
    """One setup per (symbol, family, side, bar).  POI families additionally key
    on the candidate id, which for them is stable across the bar (it hashes
    poi_id + zone-midpoint entry, and the zone comes from the bar-open MSO)."""
    if r["f"].startswith("current_"):
        return (r["s"], r["f"], r["d"], r["b"], r["cid"])
    return (r["s"], r["f"], r["d"], r["b"])


def load_rows(indir):
    for p in sorted(glob.glob(os.path.join(indir, "pbg_*.jsonl.gz"))):
        with gzip.open(p, "rt") as fh:
            for line in fh:
                yield json.loads(line)


def bootstrap_days(by_day, n=2000, seed=20260806):
    """Day-block bootstrap of the mean of a per-day (sum, count) table."""
    days = sorted(by_day)
    if not days:
        return None
    s = np.array([by_day[d][0] for d in days], dtype=float)
    c = np.array([by_day[d][1] for d in days], dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(days), size=(n, len(days)))
    num = s[idx].sum(axis=1)
    den = c[idx].sum(axis=1)
    den[den == 0] = np.nan
    m = num / den
    m = m[~np.isnan(m)]
    return {
        "mean": float(s.sum() / c.sum()) if c.sum() else None,
        "ci95_lo": float(np.percentile(m, 2.5)),
        "ci95_hi": float(np.percentile(m, 97.5)),
        "p_le_0": float((m <= 0).mean()),
        "n_days": len(days),
        "days_positive": int(sum(1 for d in days if by_day[d][0] > 0)),
    }


def summarise(trades, label):
    """trades: list of dicts with gross, net, bps_gross, bps_net, day, exit."""
    if not trades:
        return {"label": label, "n": 0}
    g = np.array([t["gross"] for t in trades])
    c = np.array([t["cost_r"] for t in trades])
    n = g - c
    bg = np.array([t["bps_gross"] for t in trades])
    bn = np.array([t["bps_net"] for t in trades])
    by_day_g, by_day_n = defaultdict(lambda: [0.0, 0]), defaultdict(lambda: [0.0, 0])
    for t in trades:
        by_day_g[t["day"]][0] += t["gross"]
        by_day_g[t["day"]][1] += 1
        by_day_n[t["day"]][0] += t["gross"] - t["cost_r"]
        by_day_n[t["day"]][1] += 1
    ex = Counter(t["exit"] for t in trades)
    return {
        "label": label,
        "n": int(len(g)),
        "gross_r_per_trade": float(g.mean()),
        "cost_r_per_trade": float(c.mean()),
        "net_r_per_trade": float(n.mean()),
        "gross_bps": float(bg.mean()),
        "net_bps": float(bn.mean()),
        "total_gross_r": float(g.sum()),
        "total_net_r": float(n.sum()),
        "win_rate_gross": float((g > 0).mean()),
        "win_rate_net": float((n > 0).mean()),
        "exit_mix": {k: v / len(g) for k, v in ex.items()},
        "truncation_share": ex.get("path_end", 0) / len(g),
        "days_net_positive": sum(1 for d in by_day_n if by_day_n[d][0] > 0),
        "n_days": len(by_day_n),
        "boot_net": bootstrap_days(by_day_n),
        "boot_gross": bootstrap_days(by_day_g),
    }


def paired_bootstrap(pairs, seed=20260806, n=2000):
    """pairs: list of (day, delta).  Day-block bootstrap of the mean delta."""
    by_day = defaultdict(lambda: [0.0, 0])
    for d, x in pairs:
        by_day[d][0] += x
        by_day[d][1] += 1
    return bootstrap_days(by_day, n=n, seed=seed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--month", default="202601")
    ap.add_argument("--sealed", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--target-r", type=float, default=2.0)
    args = ap.parse_args()

    out = {"month": args.month, "generated_utc": datetime.now(timezone.utc).isoformat()}

    rows = list(load_rows(args.indir))
    out["rows_emitted_total"] = len(rows)
    out["rows_by_k"] = {str(k): v for k, v in sorted(Counter(r["k"] for r in rows).items())}

    # ---------------------------------------------------------------- 1. repro
    close = [r for r in rows if r["k"] == 15]
    mk = {(r["cid"], r["t"]) for r in close}
    repro = {"my_close_only_rows": len(close), "my_distinct_keys": len(mk)}
    if args.sealed and os.path.isfile(args.sealed):
        sealed = set()
        with gzip.open(args.sealed, "rt") as fh:
            for line in fh:
                a, b = line.rstrip("\n").split("\t")
                sealed.add((a, b))
        repro.update(
            {
                "sealed_keys": len(sealed),
                "matched": len(mk & sealed),
                "sealed_only": len(sealed - mk),
                "mine_only": len(mk - sealed),
                "coverage_of_sealed": len(mk & sealed) / len(sealed) if sealed else None,
                "exact_reproduction": len(mk) == len(sealed) == len(mk & sealed),
                "sealed_only_by_time": dict(
                    Counter(t[11:16] for _, t in (sealed - mk)).most_common(5)
                ),
                "mine_only_by_day": dict(
                    Counter(t[:10] for _, t in (mk - sealed)).most_common(5)
                ),
            }
        )
    out["reproduction"] = repro
    out["close_only_family_counts"] = dict(Counter(r["f"] for r in close))

    # -------------------------------------------------------------- 2. substrate
    months = [args.month]
    tape = E.Tape(L.SYMBOLS, months)
    cm = E.CostModel()

    # every at-market emission's entry MUST equal the last M1 close before its
    # own decision instant — the no-look-ahead proof, on the whole population.
    anchor_ok = anchor_n = 0
    worst = 0.0
    for r in rows:
        if r["f"] not in AT_MARKET:
            continue
        i = tape.idx(r["t"])
        p = tape.last_close_before(r["s"], i)
        if p != p:  # nan
            continue
        anchor_n += 1
        rel = abs(p - r["e"]) / max(abs(r["e"]), 1e-12)
        worst = max(worst, rel)
        if rel <= 1e-9:
            anchor_ok += 1
    out["anchor_check"] = {
        "population": "every at-market emission, all k",
        "n": anchor_n,
        "exact": anchor_ok,
        "share_exact": anchor_ok / anchor_n if anchor_n else None,
        "worst_relative_error": worst,
    }

    # ------------------------------------------------------------- 3. arms
    by_key = defaultdict(dict)  # key -> {k: row}
    for r in rows:
        by_key[setup_key(r)][r["k"]] = r

    def price(r, *, d0=None, entry_override=None):
        i = tape.idx(r["t"])
        entry = entry_override if entry_override is not None else r["e"]
        stop = r["sl"]
        d = abs(entry - stop) if d0 is None else d0
        if not (d > 0):
            return None
        stop_eff = entry - d if r["d"] == "L" else entry + d
        limit = r["f"].startswith("current_")
        fn = E.walk_limit if limit else E.walk
        w = fn(
            tape,
            r["s"],
            i,
            entry=entry,
            stop=stop_eff,
            long=(r["d"] == "L"),
            target_r=args.target_r,
        )
        if w is None:
            return None
        gross, exit_reason, exit_bar, bars = w
        cpx, _terms = cm.cost_px(r["s"], r["t"], entry, r["d"] == "L")
        # an order that never filled pays nothing
        cost_r = 0.0 if exit_reason == "no_fill" else cpx / d
        return {
            "gross": gross,
            "cost_r": cost_r,
            "bps_gross": gross * d / entry * 1e4,
            "bps_net": (gross - cost_r) * d / entry * 1e4,
            "day": r["t"][:10],
            "exit": exit_reason,
            "exit_bar": exit_bar,
            "risk": d,
            "k": r["k"],
            "sym": r["s"],
            "fam": r["f"],
        }

    cohorts = {
        "AT_MARKET": set(AT_MARKET),
        "POI": set(POI),
        "CONTINUATION5": set(CONTINUATION5),
        "EARLY5": set(EARLY5),
    }

    result = {}
    for cname, fams in cohorts.items():
        keys = [k for k in by_key if k[1] in fams]
        close_arm, part_arm, paired, phantom, closeonly_only = [], [], [], [], []
        d0pres = []
        clockctl = []
        ear_hist = Counter()
        for k in keys:
            per = by_key[k]
            ck = per.get(15)
            pk_min = min((kk for kk in per if kk < 15), default=None)
            pk = per.get(pk_min) if pk_min is not None else None
            tc = price(ck) if ck is not None else None
            tp = price(pk) if pk is not None else None
            if tc is not None:
                close_arm.append(tc)
            if tp is not None:
                part_arm.append(tp)
            if ck is not None and pk is not None:
                ear_hist[15 - pk_min] += 1
                if tc is not None and tp is not None:
                    paired.append((tc, tp, 15 - pk_min))
                    tdp = price(pk, d0=tc["risk"])
                    if tdp is not None:
                        d0pres.append((tc, tdp, 15 - pk_min))
                    # CLOCK CONTROL (x5 §5.2 shape): the CLOSE-ONLY setup — its
                    # side and its risk distance — entered at the partial arm's
                    # own minute, at the market price then.  It is look-ahead by
                    # construction (the setup is not knowable at that minute), so
                    # it is a control, never a strategy.  partial - control = the
                    # value of DETECTING on the forming bar rather than the clock.
                    mp = tape.last_close_before(pk["s"], tape.idx(pk["t"]))
                    if mp == mp:
                        tcc = price(pk, d0=tc["risk"], entry_override=mp)
                        if tcc is not None:
                            clockctl.append((tcc, tp, 15 - pk_min))
            elif pk is not None and ck is None:
                if tp is not None:
                    phantom.append(tp)
            elif ck is not None and pk is None:
                if tc is not None:
                    closeonly_only.append(tc)

        r = {
            "n_setup_keys": len(keys),
            "close_arm": summarise(close_arm, "close_only_k15"),
            "partial_arm_firstk": summarise(part_arm, "partial_first_k"),
            "paired_n": len(paired),
            "earliness_hist": {str(a): b for a, b in sorted(ear_hist.items())},
            "earliness_mean_minutes": (
                float(np.mean([e for _, _, e in paired])) if paired else None
            ),
            "earliness_median_minutes": (
                float(np.median([e for _, _, e in paired])) if paired else None
            ),
            "paired_close": summarise([a for a, _, _ in paired], "paired_close"),
            "paired_partial": summarise([b for _, b, _ in paired], "paired_partial"),
            "paired_delta_net": paired_bootstrap(
                [(a["day"], (b["gross"] - b["cost_r"]) - (a["gross"] - a["cost_r"]))
                 for a, b, _ in paired]
            ),
            "paired_delta_gross": paired_bootstrap(
                [(a["day"], b["gross"] - a["gross"]) for a, b, _ in paired]
            ),
            "d0_preserved_close": summarise([a for a, _, _ in d0pres], "d0_close"),
            "d0_preserved_partial": summarise([b for _, b, _ in d0pres], "d0_partial"),
            "d0_preserved_delta_net": paired_bootstrap(
                [(a["day"], (b["gross"] - b["cost_r"]) - (a["gross"] - a["cost_r"]))
                 for a, b, _ in d0pres]
            ),
            "clock_control": summarise([a for a, _, _ in clockctl], "clock_control_lookahead"),
            "clock_control_partial": summarise([b for _, b, _ in clockctl], "partial_same_rows"),
            "partial_minus_clock_control_net": paired_bootstrap(
                [(a["day"], (b["gross"] - b["cost_r"]) - (a["gross"] - a["cost_r"]))
                 for a, b, _ in clockctl]
            ),
            "phantom": summarise(phantom, "partial_only_setup_never_completed"),
            "close_only_only": summarise(closeonly_only, "close_only_never_early"),
        }
        # the honest books
        r["BOOK_close_only"] = summarise(close_arm + closeonly_only, "BOOK_close")
        r["BOOK_partial"] = summarise(part_arm + phantom, "BOOK_partial")
        result[cname] = r

    out["cohorts"] = result

    # ------------------------------------------------- 4. fixed-minute ablation
    abl = {}
    for cname, fams in cohorts.items():
        per_k = {}
        for kk in list(range(1, 15)) + [15]:
            tr = [price(r) for r in rows if r["f"] in fams and r["k"] == kk]
            tr = [t for t in tr if t is not None]
            per_k[str(kk)] = summarise(tr, f"all_emissions_k{kk}")
        abl[cname] = per_k
    out["fixed_minute_ablation"] = abl

    # ------------------------------------------- 4b. common-support minute curve
    # Setups emitted at EVERY minute 1..15 of their own bar: the same rows at
    # every rung, so the curve is a property of the clock and the geometry, not
    # of a changing population.
    common = {}
    for cname, fams in cohorts.items():
        keys = [
            k for k in by_key
            if k[1] in fams and all(kk in by_key[k] for kk in range(1, 16))
        ]
        per_k = {}
        for kk in range(1, 16):
            tr = [price(by_key[k][kk]) for k in keys]
            tr = [x for x in tr if x is not None]
            per_k[str(kk)] = summarise(tr, f"common_support_k{kk}")
        deltas = {}
        for kk in range(1, 15):
            d = []
            for k in keys:
                a = price(by_key[k][15])
                b = price(by_key[k][kk])
                if a and b:
                    d.append((a["day"], (b["gross"] - b["cost_r"]) - (a["gross"] - a["cost_r"])))
            deltas[str(kk)] = paired_bootstrap(d) if d else None
        common[cname] = {"n_keys": len(keys), "by_k": per_k, "delta_vs_close": deltas}
    out["common_support_minute_curve"] = common

    # ----------------------------------------------------------- 5. per-family
    fam_tab = {}
    for fam in AT_MARKET + POI:
        keys = [k for k in by_key if k[1] == fam]
        cl, pa, ph = [], [], []
        deltas, d0d, grd = [], [], []
        for k in keys:
            per = by_key[k]
            ck = per.get(15)
            pkm = min((x for x in per if x < 15), default=None)
            tc = price(ck) if ck is not None else None
            tp = price(per[pkm]) if pkm is not None else None
            if tc:
                cl.append(tc)
            if tp:
                (pa if ck is not None else ph).append(tp)
            if tc and tp and ck is not None:
                deltas.append((tc["day"], (tp["gross"] - tp["cost_r"]) - (tc["gross"] - tc["cost_r"])))
                td = price(per[pkm], d0=tc["risk"])
                if td:
                    d0d.append((tc["day"], (td["gross"] - td["cost_r"]) - (tc["gross"] - tc["cost_r"])))
                    grd.append((tc["day"], td["gross"] - tc["gross"]))
        fam_tab[fam] = {
            "close": summarise(cl, "close"),
            "partial_paired": summarise(pa, "partial"),
            "phantom": summarise(ph, "phantom"),
            "delta_net_paired": paired_bootstrap(deltas) if deltas else None,
            "delta_net_paired_d0_preserved": paired_bootstrap(d0d) if d0d else None,
            "delta_gross_paired_d0_preserved": paired_bootstrap(grd) if grd else None,
        }
    out["by_family"] = fam_tab

    Path(args.out).write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: out[k] for k in ("reproduction", "anchor_check")}, indent=1))
    for c in ("AT_MARKET", "CONTINUATION5", "EARLY5", "POI"):
        r = out["cohorts"][c]
        print(
            c,
            "close net %.5f (n=%d) | partial net %.5f (n=%d) | phantom net %.5f (n=%d) | "
            "BOOK close %.5f -> partial %.5f"
            % (
                r["close_arm"].get("net_r_per_trade", float("nan")),
                r["close_arm"].get("n", 0),
                r["partial_arm_firstk"].get("net_r_per_trade", float("nan")),
                r["partial_arm_firstk"].get("n", 0),
                r["phantom"].get("net_r_per_trade", float("nan")),
                r["phantom"].get("n", 0),
                r["BOOK_close_only"].get("net_r_per_trade", float("nan")),
                r["BOOK_partial"].get("net_r_per_trade", float("nan")),
            ),
        )


if __name__ == "__main__":
    main()
