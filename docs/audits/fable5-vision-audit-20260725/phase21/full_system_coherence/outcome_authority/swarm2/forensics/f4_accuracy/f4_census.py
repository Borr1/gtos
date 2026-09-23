#!/usr/bin/env python3
"""F4 task 1 — the accuracy decomposition.

Joins the frozen five-month candidate cache to Lane 2's M1 horizon walk (which
carries per-trade MFE/MAE in gross R at the sealed horizon h1) and attributes
every losing filled trade to a failure mode.

Validation gate: the walk's h1 arm must reproduce the sealed corpus label.
Anything that does not reproduce is reported, not silently dropped.

Read-only. Writes receipts under receipts/.
"""
from __future__ import annotations

import gzip
import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from f4_common import MONTHS, dollars, enrich, jdump, load_month  # noqa: E402

WALK = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane2")
OUT = Path(__file__).parent / "receipts"

# Prereg thresholds — frozen in F4_PREREG_V1.json before this ran.
T_WRONG = 0.3     # MFE below this => never went anywhere
T_RIGHT = 1.0     # MFE at or above this => was genuinely winning


def load_walk(month: str) -> dict:
    with gzip.open(WALK / f"walk_{month}.pkl.gz", "rb") as f:
        recs = pickle.load(f)
    return {r["k"]: r for r in recs}


def main() -> None:
    per_month = {}
    rows_all = []
    val = {"checked": 0, "kind_match": 0, "gross_close": 0, "max_abs_gross_err": 0.0}

    for m in MONTHS:
        rows = enrich(load_month(m))
        w = load_walk(m)
        n_join = 0
        for r in rows:
            g = w.get(r["candidate_occurrence_key"])
            r["_w"] = g
            if g is not None:
                n_join += 1
        per_month[m] = {"rows": len(rows), "walk_joined": n_join}
        rows_all += rows
        print(f"{m}: rows={len(rows)} joined={n_join}", flush=True)

    # ---- validation: does h1 reproduce the sealed label? --------------------
    fil = [r for r in rows_all if r["is_filled"] and r["_w"] is not None]
    mism = Counter()
    for r in fil:
        h1 = r["_w"].get("h1")
        if not h1:
            mism["no_h1"] += 1
            continue
        val["checked"] += 1
        want = r["lifecycle_label_status"].replace("RESOLVED_FILLED_", "")
        if h1["kind"] == want:
            val["kind_match"] += 1
        else:
            mism[f"{want}->{h1['kind']}"] += 1
        if h1.get("gross") is not None and r["terminal_gross_r"] == r["terminal_gross_r"]:
            err = abs(float(h1["gross"]) - r["terminal_gross_r"])
            val["max_abs_gross_err"] = max(val["max_abs_gross_err"], err)
            if err < 1e-6:
                val["gross_close"] += 1
    val["kind_match_rate"] = val["kind_match"] / max(1, val["checked"])
    val["gross_match_rate"] = val["gross_close"] / max(1, val["checked"])
    val["mismatches"] = dict(mism.most_common(12))
    print("VALIDATION", val, flush=True)

    # ---- the decomposition --------------------------------------------------
    # Universe: filled rows whose h1 walk reproduces the sealed kind exactly.
    use = []
    for r in fil:
        h1 = r["_w"].get("h1")
        if not h1:
            continue
        if h1["kind"] != r["lifecycle_label_status"].replace("RESOLVED_FILLED_", ""):
            continue
        r["mfe"] = float(h1["mfe"])
        r["mae"] = float(h1["mae"])
        r["gapped"] = bool(h1["gapped"])
        use.append(r)
    print(f"decomposition universe n={len(use)} of filled {len(fil)}", flush=True)

    def classify(r):
        """Path mode. Disjoint by construction."""
        if r["terminal_net_r"] > 0:
            return "WON"
        if r["mfe"] < T_WRONG:
            return "M1_WRONG_DIRECTION"
        if r["mfe"] >= T_RIGHT:
            return "M2_RIGHT_THEN_REVERSED"
        return "M5_MIDDLE"

    for r in use:
        r["mode"] = classify(r)
        # cost / clock re-cuts (may overlap the path modes)
        r["killed_by_cost"] = bool(r["terminal_gross_r"] > 0 and r["terminal_net_r"] <= 0)
        r["killed_by_clock"] = bool(
            r["lifecycle_label_status"] == "RESOLVED_FILLED_TIME_STOP"
            and r["terminal_gross_r"] > 0
        )
        # clock cost: was it winning at the bell and cut before target?
        r["clock_cut_while_up"] = bool(
            r["lifecycle_label_status"] == "RESOLVED_FILLED_TIME_STOP" and r["mfe"] >= T_RIGHT
        )

    def block(rs, label):
        n = len(rs)
        if n == 0:
            return {"n": 0}
        net = np.array([r["terminal_net_r"] for r in rs])
        gro = np.array([r["terminal_gross_r"] for r in rs])
        mfe = np.array([r["mfe"] for r in rs])
        mae = np.array([r["mae"] for r in rs])
        return {
            "n": n, "share": n / len(use),
            "net_mean": float(net.mean()), "net_sum": float(net.sum()),
            "gross_mean": float(gro.mean()),
            "mfe_mean": float(mfe.mean()), "mfe_med": float(np.median(mfe)),
            "mae_mean": float(mae.mean()), "mae_med": float(np.median(mae)),
            "usd_sum_at_500_per_R": round(float(net.sum()) * 500.0),
        }

    modes = defaultdict(list)
    for r in use:
        modes[r["mode"]].append(r)
    dec = {k: block(v, k) for k, v in modes.items()}

    losers = [r for r in use if r["terminal_net_r"] <= 0]
    lose_modes = defaultdict(list)
    for r in losers:
        lose_modes[r["mode"]].append(r)
    dec_losers = {k: dict(block(v, k), share_of_losers=len(v) / len(losers))
                  for k, v in lose_modes.items()}

    recut = {
        "killed_by_cost": block([r for r in use if r["killed_by_cost"]], "cost"),
        "killed_by_clock_positive_gross": block([r for r in use if r["killed_by_clock"]], "clock"),
        "clock_cut_while_mfe_ge_1R": block([r for r in use if r["clock_cut_while_up"]], "clockup"),
    }

    # overlap matrix: path mode x (cost / clock)
    overlap = {}
    for mode in sorted(modes):
        overlap[mode] = {
            "n": len(modes[mode]),
            "also_killed_by_cost": sum(1 for r in modes[mode] if r["killed_by_cost"]),
            "also_clock_positive": sum(1 for r in modes[mode] if r["killed_by_clock"]),
        }

    # per-month stability of the three-way split among losers
    bymonth = {}
    for m in MONTHS:
        L = [r for r in losers if r["month"] == m]
        if not L:
            continue
        c = Counter(r["mode"] for r in L)
        bymonth[m] = {k: c[k] / len(L) for k in sorted(c)} | {"n": len(L)}

    # exit-reason x mode cross tab
    cross = defaultdict(Counter)
    for r in use:
        cross[r["lifecycle_label_status"]][r["mode"]] += 1

    # MFE / MAE distribution of the whole filled universe
    mfe = np.array([r["mfe"] for r in use])
    mae = np.array([r["mae"] for r in use])
    qs = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
    dist = {
        "mfe_quantiles": {str(q): float(np.quantile(mfe, q)) for q in qs},
        "mae_quantiles": {str(q): float(np.quantile(mae, q)) for q in qs},
        "mfe_mean": float(mfe.mean()), "mae_mean": float(mae.mean()),
        "frac_mfe_ge": {str(t): float((mfe >= t).mean())
                        for t in (0.3, 0.5, 1.0, 1.5, 2.0, 3.0)},
        "frac_mae_le": {str(t): float((mae <= t).mean())
                        for t in (-0.25, -0.5, -0.75, -1.0)},
        "gapped_share": float(np.mean([r["gapped"] for r in use])),
    }

    res = {
        "prereg_sha256": "bfe7c722c2f22d45dd8de072fb4e906352b254696a9eb61896ff53a303d68054",
        "thresholds": {"T_WRONG_MFE_R": T_WRONG, "T_RIGHT_MFE_R": T_RIGHT},
        "per_month_join": per_month,
        "validation_h1_vs_sealed": val,
        "universe_n": len(use),
        "filled_n": len(fil),
        "decomposition_all_filled": dec,
        "decomposition_losers_only": dec_losers,
        "loser_n": len(losers),
        "cost_clock_recut": recut,
        "overlap_matrix": overlap,
        "losers_mode_share_by_month": bymonth,
        "exit_reason_x_mode": {k: dict(v) for k, v in cross.items()},
        "excursion_distribution": dist,
        "note_mfe_is_raw_high_low": (
            "MFE/MAE are measured from the quote-adjusted fill price against RAW bar "
            "high/low, so MFE overstates the exit-achievable favourable excursion by "
            "roughly one spread. Treated as an upper bound throughout."
        ),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    jdump(res, OUT / "F4_DECOMPOSITION_V1.json")

    # cache the joined universe for downstream tasks
    keep = ("candidate_occurrence_key", "mfe", "mae", "mode", "gapped",
            "killed_by_cost", "killed_by_clock", "clock_cut_while_up")
    slim = [{k: r[k] for k in keep} for r in use]
    with gzip.open(OUT.parent / "f4_excursion_join.pkl.gz", "wb") as f:
        pickle.dump(slim, f, protocol=5)

    print("\n=== THREE-WAY DECOMPOSITION OF LOSERS (n=%d) ===" % len(losers))
    for k in sorted(dec_losers, key=lambda x: -dec_losers[x]["n"]):
        d = dec_losers[k]
        print(f"  {k:26s} n={d['n']:7d} {d['share_of_losers']*100:5.1f}%  "
              f"netR={d['net_sum']:+10.1f} ({dollars(d['net_sum'])})  "
              f"mfe_med={d['mfe_med']:+.3f} mae_med={d['mae_med']:+.3f}")
    print("\n=== COST / CLOCK RE-CUT ===")
    for k, d in recut.items():
        if d.get("n"):
            print(f"  {k:34s} n={d['n']:7d} netR={d['net_sum']:+9.1f} ({dollars(d['net_sum'])})")
    print("\n=== MFE distribution (all filled) ===")
    print("  ", dist["frac_mfe_ge"])


if __name__ == "__main__":
    main()
