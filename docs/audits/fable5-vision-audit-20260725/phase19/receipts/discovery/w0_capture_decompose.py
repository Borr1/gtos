"""w0-capture step 2: WHERE the 0.258 R/trade exit-layer gap lives.

Consumes the rowdump written by w0_capture_horizon.py --rowdump and the pool,
and decomposes the walk-vs-recorded discrepancy by family / policy / blocker /
symbol / timeframe, plus the sub-target-winner MFE timing split.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[6]
POOL = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools"
    / "CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
)
EXTRA = (
    "symbol",
    "decision_timeframe",
    "direction",
    "side",
    "route_family",
    "framework",
    "session_bucket",
    "selected_policy_for_expected_net_r",
    "candidate_probability",
    "expected_net_r",
    "policy_target_r",
    "raw_target_r",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "selector_reason",
    "effective_selector_reason",
    "miss_reason",
    "candidate_lifecycle_action",
    "fill_realism_class",
    "effective_order_type",
    "limit_marketable_at_decision",
)


def group_table(mask, labels, gross_rec, walk120, walk_full, cost, top=40):
    idx = collections.defaultdict(list)
    for i, lab in enumerate(labels):
        idx[lab].append(i)
    rows = []
    for lab, ii in idx.items():
        ii = np.asarray(ii)
        m = mask[ii]
        tot = len(ii)
        if tot == 0:
            continue
        d = walk120[ii] - gross_rec[ii]
        rows.append(
            {
                "group": str(lab),
                "n": int(tot),
                "n_discrepant": int(m.sum()),
                "share_discrepant": float(m.sum() / tot),
                "recorded_gross_mean_R": float(np.nanmean(gross_rec[ii])),
                "pure120_gross_mean_R": float(np.nanmean(walk120[ii])),
                "pure_full_gross_mean_R": float(np.nanmean(walk_full[ii])),
                "gap_pure120_minus_recorded_R": float(np.nanmean(d)),
                "R_total_lost_to_exit_layer": float(np.nansum(d)),
                "mean_cost_R": float(np.nanmean(cost[ii])),
                "pure120_net_after_frozen_cost_R": float(
                    np.nanmean(walk120[ii]) - np.nanmean(cost[ii])
                ),
            }
        )
    rows.sort(key=lambda r: -abs(r["R_total_lost_to_exit_layer"]))
    return rows[:top]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rowdump", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path(__file__).with_name("W0_CAPTURE_DECOMPOSE_V1.json"))
    args = ap.parse_args()

    z = np.load(args.rowdump, allow_pickle=True)
    gross_rec = z["gross_rec"]
    walk = z["walk_gross"]
    out = z["walk_out"]
    mfe = z["mfe"]
    hz = list(z["horizons"])
    fam = z["family"]
    cost = z["cost_r"]
    cid = z["cid"]
    target_r = z["target_r"]
    j120 = hz.index(120)
    j1d = hz.index(1440)
    jfull = len(hz) - 1
    walk120 = walk[:, j120]
    walkfull = walk[:, jfull]

    extra = {k: [] for k in EXTRA}
    with gzip.open(POOL, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            for k in EXTRA:
                extra[k].append(r.get(k))

    ok = np.isfinite(gross_rec) & np.isfinite(walk120)
    d = walk120 - gross_rec
    disc = ok & (d > 0.02)          # engine recorded WORSE than plain geometry
    disc_up = ok & (d < -0.02)      # engine recorded BETTER than plain geometry

    res = {
        "schema": "gtos-w0-capture-decompose-v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "billed": False,
        "n": int(len(gross_rec)),
        "n_discrepant_engine_worse": int(disc.sum()),
        "n_discrepant_engine_better": int(disc_up.sum()),
        "R_total_engine_worse": float(np.nansum(d[disc])),
        "R_total_engine_better": float(np.nansum(d[disc_up])),
    }

    for key, labels in [
        ("origin_family", fam),
        ("dynamic_geometry_policy", z["policy"]),
        ("final_blocker_class", z["blocker"]),
        ("symbol", np.asarray(extra["symbol"], dtype=object)),
        ("decision_timeframe", np.asarray(extra["decision_timeframe"], dtype=object)),
        ("route_family", np.asarray(extra["route_family"], dtype=object)),
        ("framework", np.asarray(extra["framework"], dtype=object)),
        ("selected_policy_for_expected_net_r", np.asarray(extra["selected_policy_for_expected_net_r"], dtype=object)),
        ("effective_order_type", np.asarray(extra["effective_order_type"], dtype=object)),
        ("fill_realism_class", np.asarray(extra["fill_realism_class"], dtype=object)),
    ]:
        res[f"by_{key}"] = group_table(disc, labels, gross_rec, walk120, walkfull, cost)

    # cross: family x policy for the top offender
    xs = collections.Counter()
    for i in np.nonzero(disc)[0]:
        xs[(str(fam[i]), str(z["policy"][i]), str(extra["decision_timeframe"][i]))] += 1
    res["discrepant_cross_family_policy_tf_top"] = [
        {"family": k[0], "policy": k[1], "tf": k[2], "n": v} for k, v in xs.most_common(25)
    ]

    # what does the engine record on discrepant rows, and what does geometry say?
    rec_hist = collections.Counter()
    for i in np.nonzero(disc)[0]:
        g = gross_rec[i]
        w = walk120[i]
        rb = "stop" if g <= -0.98 else ("target" if g >= target_r[i] - 0.02 else ("pos" if g > 0.02 else ("neg" if g < -0.02 else "flat")))
        wb = {1: "target", 2: "stop", 3: "mark"}.get(int(out[i, j120]), "none")
        rec_hist[(rb, wb)] += 1
    res["discrepant_recorded_vs_geometry_transitions"] = [
        {"recorded": k[0], "pure_geometry": k[1], "n": v} for k, v in rec_hist.most_common(20)
    ]

    # direction/side agreement audit on discrepant rows
    dirside = collections.Counter()
    for i in np.nonzero(ok)[0]:
        dirside[(str(extra["direction"][i]), str(extra["side"][i]), bool(disc[i]))] += 1
    res["direction_side_audit"] = [
        {"direction": k[0], "side": k[1], "discrepant": k[2], "n": v} for k, v in dirside.most_common(20)
    ]

    # geometry sanity: is take_profit exactly 2R from entry?
    tr = target_r[np.isfinite(target_r)]
    res["target_distance_R_distribution"] = {
        "n": int(len(tr)),
        "mean": float(tr.mean()),
        "min": float(tr.min()),
        "p1": float(np.percentile(tr, 1)),
        "p50": float(np.percentile(tr, 50)),
        "p99": float(np.percentile(tr, 99)),
        "max": float(tr.max()),
        "share_exactly_2R_within_0p01": float(np.mean(np.abs(tr - 2.0) <= 0.01)),
    }

    # ---- the mission's timing split on sub-target winners
    sub = ok & (gross_rec > 0.02) & (gross_rec < target_r - 0.02)
    reach120 = mfe[:, j120] >= target_r - 1e-9
    reach1d = mfe[:, j1d] >= target_r - 1e-9
    reachfull = mfe[:, jfull] >= target_r - 1e-9
    nsub = int(sub.sum())
    res["sub_target_winner_target_timing"] = {
        "n": nsub,
        "recorded_gross_mean_R": float(np.nanmean(gross_rec[sub])),
        "reached_2R_within_recorded_120m_window": [int((sub & reach120).sum()), float((sub & reach120).sum() / nsub)],
        "reached_2R_after_120m_within_1d": [int((sub & reach1d & ~reach120).sum()), float((sub & reach1d & ~reach120).sum() / nsub)],
        "reached_2R_after_1d_within_10d": [int((sub & reachfull & ~reach1d).sum()), float((sub & reachfull & ~reach1d).sum() / nsub)],
        "never_reached_2R_within_10d": [int((sub & ~reachfull).sum()), float((sub & ~reachfull).sum() / nsub)],
    }

    # full stops: money on the table BEFORE the stop (target touched first under geometry)
    st = ok & (gross_rec <= -0.98)
    nst = int(st.sum())
    res["full_stop_forensics"] = {
        "n": nst,
        "pure_geometry_says_target_first_within_120m": [int((st & (out[:, j120] == 1)).sum()), float((st & (out[:, j120] == 1)).sum() / nst)],
        "pure_geometry_says_stop_first_within_120m": [int((st & (out[:, j120] == 2)).sum()), float((st & (out[:, j120] == 2)).sum() / nst)],
        "pure_geometry_says_mark_within_120m": [int((st & (out[:, j120] == 3)).sum()), float((st & (out[:, j120] == 3)).sum() / nst)],
        "R_recoverable_if_geometry_governed": float(np.nansum(walk120[st] - gross_rec[st])),
        "R_per_pool_trade": float(np.nansum(walk120[st] - gross_rec[st]) / len(gross_rec)),
    }

    # ---- counterfactual books
    def book(mask, arr, label):
        g = arr[mask]
        c = cost[mask]
        return {
            "label": label,
            "n": int(mask.sum()),
            "gross_mean_R": float(np.nanmean(g)),
            "net_frozen_cost_mean_R": float(np.nanmean(g - c)),
            "win_rate": float(np.mean(g > 0)),
        }

    res["books"] = [
        book(ok, gross_rec, "recorded_engine_exit"),
        book(ok, walk120, "pure_2R_1R_bracket_120m_horizon"),
        book(ok, walk[:, j1d], "pure_2R_1R_bracket_24h_horizon"),
        book(ok, walkfull, "pure_2R_1R_bracket_10d_horizon"),
    ]

    # exclude the breaker family (already known inverted) and re-run the books
    nb = ok & np.asarray([f != "current_breaker_re_entry" for f in fam])
    res["books_excluding_current_breaker_re_entry"] = [
        book(nb, gross_rec, "recorded_engine_exit"),
        book(nb, walk120, "pure_2R_1R_bracket_120m_horizon"),
        book(nb, walk[:, j1d], "pure_2R_1R_bracket_24h_horizon"),
        book(nb, walkfull, "pure_2R_1R_bracket_10d_horizon"),
    ]

    # worst 15 individual discrepancies for spot-checking
    order = np.argsort(-np.where(disc, d, -np.inf))[:15]
    res["worst_discrepancies"] = [
        {
            "candidate_id": str(cid[i]),
            "symbol": str(extra["symbol"][i]),
            "side": str(extra["side"][i]),
            "family": str(fam[i]),
            "policy": str(z["policy"][i]),
            "recorded_gross_R": float(gross_rec[i]),
            "pure_geometry_120m_gross_R": float(walk120[i]),
            "gap_R": float(d[i]),
            "target_R": float(target_r[i]),
            "mfe_120m_R": float(mfe[i, j120]),
            "entry": extra["entry_price"][i],
            "stop": extra["stop_loss"][i],
            "tp": extra["take_profit_1"][i],
            "selector_reason": extra["selector_reason"][i],
            "miss_reason": extra["miss_reason"][i],
        }
        for i in order
    ]

    args.out.write_text(json.dumps(res, indent=1, sort_keys=True))
    for k in (
        "n_discrepant_engine_worse",
        "n_discrepant_engine_better",
        "R_total_engine_worse",
        "R_total_engine_better",
    ):
        print(k, res[k])
    print("\n-- by origin_family --")
    for r in res["by_origin_family"]:
        print(
            f"{r['group']:<32} n={r['n']:>6} disc={r['n_discrepant']:>5} ({r['share_discrepant']:.3f}) "
            f"rec={r['recorded_gross_mean_R']:+.4f} pure120={r['pure120_gross_mean_R']:+.4f} "
            f"pureFull={r['pure_full_gross_mean_R']:+.4f} gap={r['gap_pure120_minus_recorded_R']:+.4f} "
            f"Rlost={r['R_total_lost_to_exit_layer']:+.1f}"
        )
    print("\n-- by dynamic_geometry_policy --")
    for r in res["by_dynamic_geometry_policy"]:
        print(
            f"{r['group']:<32} n={r['n']:>6} disc={r['n_discrepant']:>5} ({r['share_discrepant']:.3f}) "
            f"rec={r['recorded_gross_mean_R']:+.4f} pure120={r['pure120_gross_mean_R']:+.4f} gap={r['gap_pure120_minus_recorded_R']:+.4f} Rlost={r['R_total_lost_to_exit_layer']:+.1f}"
        )
    print("\n-- by decision_timeframe --")
    for r in res["by_decision_timeframe"]:
        print(f"{r['group']:<10} n={r['n']:>6} disc={r['n_discrepant']:>5} rec={r['recorded_gross_mean_R']:+.4f} pure120={r['pure120_gross_mean_R']:+.4f} gap={r['gap_pure120_minus_recorded_R']:+.4f}")
    print("\n-- transitions on discrepant rows --")
    for r in res["discrepant_recorded_vs_geometry_transitions"]:
        print(f"  recorded={r['recorded']:<7} geometry={r['pure_geometry']:<7} n={r['n']}")
    print("\n-- books --")
    for b in res["books"]:
        print(f"  {b['label']:<38} n={b['n']} gross={b['gross_mean_R']:+.4f} netFrozen={b['net_frozen_cost_mean_R']:+.4f} win={b['win_rate']:.3f}")
    print("\n-- books ex-breaker --")
    for b in res["books_excluding_current_breaker_re_entry"]:
        print(f"  {b['label']:<38} n={b['n']} gross={b['gross_mean_R']:+.4f} netFrozen={b['net_frozen_cost_mean_R']:+.4f} win={b['win_rate']:.3f}")
    print("\n-- sub-target timing --")
    print(json.dumps(res["sub_target_winner_target_timing"], indent=1))
    print("\n-- full stops --")
    print(json.dumps(res["full_stop_forensics"], indent=1))
    print("\n-- target distance --")
    print(json.dumps(res["target_distance_R_distribution"], indent=1))
    print("\n-- direction/side --")
    for r in res["direction_side_audit"]:
        print("  ", r)
    print("\n-- worst --")
    for r in res["worst_discrepancies"][:6]:
        print("  ", json.dumps(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
