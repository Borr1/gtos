"""Frozen segment-book admission table from the relabeled frame.

Selection (TRAIN + TRAIN_DEVELOPMENT_GRADE only): every segment cell
(asset_class x origin_family x session_bucket, where session buckets include
hourly moonshot windows) with n >= MIN_N gets a one-sided t-statistic for
mean relabeled net R > 0; Benjamini-Hochberg control at Q across ALL tested
cells; surviving cells form the book with their shrunk expected R.

Evaluation: the VALIDATION rows of the SAME frozen frame, evaluated ONCE —
book membership decided purely from TRAIN statistics. Boundary: replay/proxy
evidence; not a broker-real claim; sealed days untouched.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

MIN_N = 150
BH_Q = 0.10
SHRINK_K = 200.0

BOUNDARY = {
    "broker_operation": False,
    "paid_api_or_vendor_call": False,
    "broker_runtime_change_status": False,
    "validation_result_status": False,
    "outcome_result_rows_status": False,
}


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    train = defaultdict(list)
    val = defaultdict(list)
    val_days = defaultdict(set)
    with open(args.frame, encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            row = json.loads(line)
            if row.get("label_relabel_source") != "segment_winner_replay":
                continue
            net = row.get("label_net_r_raw")
            if net is None:
                continue
            seg = (
                str(row.get("f_asset_class")),
                str(row.get("f_origin_family")),
                str(row.get("f_session_bucket")),
            )
            role = row.get("partition_role")
            if role in ("TRAIN", "TRAIN_DEVELOPMENT_GRADE"):
                train[seg].append(float(net))
            elif role == "VALIDATION":
                val[seg].append(float(net))
                val_days[seg].add(str(row.get("trading_day")))

    tested = []
    global_pool = [x for nets in train.values() for x in nets]
    global_mean = statistics.fmean(global_pool) if global_pool else 0.0
    for seg, nets in train.items():
        if len(nets) < MIN_N:
            continue
        mean = statistics.fmean(nets)
        sd = statistics.pstdev(nets)
        if sd <= 0:
            continue
        t = (mean - 0.0) / (sd / math.sqrt(len(nets)))
        p = 1.0 - _norm_cdf(t)  # one-sided H1: mean > 0
        tested.append({"segment": seg, "n": len(nets), "mean": mean, "sd": sd, "t": t, "p": p})

    # Benjamini-Hochberg at Q across all tested cells.
    tested.sort(key=lambda r: r["p"])
    m = len(tested)
    survivors = []
    max_k = 0
    for k, row in enumerate(tested, start=1):
        if row["p"] <= BH_Q * k / m:
            max_k = k
    survivors = tested[:max_k]

    book = []
    val_book_net, val_book_n = 0.0, 0
    val_day_set = set()
    for row in survivors:
        seg = row["segment"]
        nets_val = val.get(seg, [])
        shrink = row["n"] / (row["n"] + SHRINK_K)
        expected_r = shrink * row["mean"] + (1 - shrink) * min(0.0, global_mean)
        entry = {
            "asset_class": seg[0],
            "origin_family": seg[1],
            "session_bucket": seg[2],
            "train_n": row["n"],
            "train_mean_net_r": round(row["mean"], 5),
            "train_t": round(row["t"], 3),
            "train_p_one_sided": row["p"],
            "expected_r_shrunk": round(expected_r, 5),
            "validation_n": len(nets_val),
            "validation_mean_net_r": round(statistics.fmean(nets_val), 5) if nets_val else None,
            "validation_net_r_sum": round(sum(nets_val), 4) if nets_val else 0.0,
        }
        book.append(entry)
        val_book_net += sum(nets_val)
        val_book_n += len(nets_val)
        val_day_set |= val_days.get(seg, set())

    holds = sum(
        1 for e in book if e["validation_n"] >= 15 and (e["validation_mean_net_r"] or 0) > 0
    )
    evaluable = sum(1 for e in book if e["validation_n"] >= 15)
    report = {
        "schema_version": "ultimate_segment_book_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "frame": str(args.frame),
        "selection": {
            "roles": ["TRAIN", "TRAIN_DEVELOPMENT_GRADE"],
            "min_n": MIN_N,
            "test": "one_sided_t_mean_net_gt_zero_normal_approx",
            "multiple_testing": f"benjamini_hochberg_q_{BH_Q}",
            "cells_tested": m,
            "cells_surviving": len(book),
        },
        "book": sorted(book, key=lambda e: -e["train_mean_net_r"]),
        "validation_once": {
            "book_net_r_sum": round(val_book_net, 4),
            "book_trades": val_book_n,
            "book_r_per_trade": round(val_book_net / val_book_n, 5) if val_book_n else None,
            "book_validation_days": len(val_day_set),
            "r_per_validation_day": round(val_book_net / max(1, len(val_day_set)), 4),
            "segments_holding_out_of_time": f"{holds}/{evaluable} (n>=15)",
        },
        "claim_boundary": (
            "replay_proxy_evidence_under_segment_winner_exits_corrected_costs_"
            "not_broker_real_not_sealed_validated"
        ),
        **BOUNDARY,
    }
    Path(args.out).write_text(json.dumps(report, indent=1, sort_keys=True, default=str))
    print(json.dumps({k: report[k] for k in ("selection", "validation_once")}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
