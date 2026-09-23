"""
Section 2/3: Per-bucket forward-resolved analysis.

For each rejection bucket compute:
  - n
  - WR (TP-hits / resolved-trades)
  - Exp R
  - Median R
  - Total R
  - Wilson 95% CI on WR
  - Per-instrument breakdown
  - Per-month breakdown
  - Per-session breakdown

Output:
  bucket_metrics.json
  bucket_per_instrument.csv
  bucket_per_month.csv
  bucket_per_session.csv
"""
import json
import math
import statistics
import csv
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
OUT_DIR = ROOT / "research/rejected_candidates_value_mining"


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    lo = (centre - spread) / denom
    hi = (centre + spread) / denom
    return (lo, hi)


def fmt_ci(k, n):
    if n == 0:
        return "n=0"
    p = k / n
    lo, hi = wilson_ci(k, n)
    return f"{p:.3f} (n={n}, CI [{lo:.3f}, {hi:.3f}])"


def stats_for_rows(rows, r_field="fwd_r"):
    """Given a list of resolved rows, compute summary stats."""
    n = len(rows)
    if n == 0:
        return {"n": 0}
    rs = [r[r_field] for r in rows if r.get(r_field) is not None]
    if not rs:
        return {"n": n, "n_resolved": 0}
    n = len(rs)
    wins = sum(1 for x in rs if x >= 1.5 - 1e-9)
    losses = sum(1 for x in rs if x <= -1.0 + 1e-9)
    expiries = n - wins - losses
    wr = wins / n
    exp_r = sum(rs) / n
    median_r = statistics.median(rs)
    total_r = sum(rs)
    lo, hi = wilson_ci(wins, n)
    return {
        "n": n,
        "wins": wins,
        "losses": losses,
        "expiries": expiries,
        "wr": wr,
        "wr_ci_lo": lo,
        "wr_ci_hi": hi,
        "exp_r": exp_r,
        "median_r": median_r,
        "total_r": total_r,
    }


def main():
    # Load forward resolution
    resolved = []
    with open(OUT_DIR / "forward_resolution.jsonl", "r") as f:
        for line in f:
            r = json.loads(line)
            if r["_resolved"]:
                resolved.append(r)
    print(f"Resolved (single-direction) rows: {len(resolved)}")

    # Per-bucket overall
    by_bucket = defaultdict(list)
    for r in resolved:
        by_bucket[r["bucket_sub"]].append(r)

    print()
    print("===== Per-bucket overall =====")
    bucket_metrics = {}
    for bucket, rows in sorted(by_bucket.items()):
        s = stats_for_rows(rows)
        bucket_metrics[bucket] = s
        if s["n"] > 0:
            print(f"  {bucket:30s} n={s['n']:4d}  WR={s['wr']:.3f} CI[{s['wr_ci_lo']:.3f},{s['wr_ci_hi']:.3f}]  ExpR={s['exp_r']:+.3f}  totalR={s['total_r']:+.1f}")

    # Per-bucket × instrument
    by_inst_bucket = defaultdict(lambda: defaultdict(list))
    for r in resolved:
        by_inst_bucket[r["bucket_sub"]][r["_instrument"]].append(r)
    print()
    print("===== Per-bucket × instrument =====")
    inst_rows = []
    for bucket, by_inst in sorted(by_inst_bucket.items()):
        print(f"  {bucket}:")
        for inst, rows in sorted(by_inst.items()):
            s = stats_for_rows(rows)
            inst_rows.append({"bucket": bucket, "instrument": inst, **s})
            if s["n"] > 0:
                print(f"    {inst:10s} n={s['n']:4d}  WR={s['wr']:.3f} CI[{s['wr_ci_lo']:.3f},{s['wr_ci_hi']:.3f}]  ExpR={s['exp_r']:+.3f}  totalR={s['total_r']:+.1f}")

    # Per-bucket × month
    by_month_bucket = defaultdict(lambda: defaultdict(list))
    for r in resolved:
        ts = r.get("timestamp_utc") or ""
        m = ts[:7] if ts else "unknown"
        by_month_bucket[r["bucket_sub"]][m].append(r)
    print()
    print("===== Per-bucket × month =====")
    month_rows = []
    for bucket, by_mo in sorted(by_month_bucket.items()):
        for mo, rows in sorted(by_mo.items()):
            s = stats_for_rows(rows)
            month_rows.append({"bucket": bucket, "month": mo, **s})

    # Per-bucket × session
    by_session_bucket = defaultdict(lambda: defaultdict(list))
    for r in resolved:
        kz = r.get("kill_zone") or "none"
        by_session_bucket[r["bucket_sub"]][kz].append(r)
    print()
    print("===== Per-bucket × session =====")
    sess_rows = []
    for bucket, by_kz in sorted(by_session_bucket.items()):
        for kz, rows in sorted(by_kz.items()):
            s = stats_for_rows(rows)
            sess_rows.append({"bucket": bucket, "session": kz, **s})
            if s["n"] >= 5:
                print(f"  {bucket:30s} {kz:10s} n={s['n']:4d}  WR={s['wr']:.3f} ExpR={s['exp_r']:+.3f}")

    # Save
    with open(OUT_DIR / "bucket_metrics.json", "w") as f:
        json.dump(bucket_metrics, f, indent=2)
    with open(OUT_DIR / "bucket_per_instrument.csv", "w", newline="") as f:
        if inst_rows:
            w = csv.DictWriter(f, fieldnames=list(inst_rows[0].keys()))
            w.writeheader()
            for row in inst_rows:
                w.writerow(row)
    with open(OUT_DIR / "bucket_per_month.csv", "w", newline="") as f:
        if month_rows:
            w = csv.DictWriter(f, fieldnames=list(month_rows[0].keys()))
            w.writeheader()
            for row in month_rows:
                w.writerow(row)
    with open(OUT_DIR / "bucket_per_session.csv", "w", newline="") as f:
        if sess_rows:
            w = csv.DictWriter(f, fieldnames=list(sess_rows[0].keys()))
            w.writeheader()
            for row in sess_rows:
                w.writerow(row)

    # Headline numbers
    print()
    print("===== HEADLINES =====")
    total_resolved = len(resolved)
    rs = [r["fwd_r"] for r in resolved if r.get("fwd_r") is not None]
    overall_total = sum(rs)
    print(f"Resolved rejected candles total R if all traded blindly: {overall_total:+.1f} R")
    n_months = 4  # 2026-01..2026-04
    print(f"  Per month: {overall_total/n_months:+.2f} R")
    print(f"  Mean per row: {overall_total/total_resolved:+.3f} R")

    # Per bucket — total R left on table
    print()
    print("===== Total R per bucket =====")
    bucket_total = []
    for bucket, rows in by_bucket.items():
        rs2 = [r["fwd_r"] for r in rows if r.get("fwd_r") is not None]
        total = sum(rs2)
        bucket_total.append((bucket, len(rs2), total))
    for bucket, n, total in sorted(bucket_total, key=lambda x: -x[2]):
        print(f"  {bucket:30s}  n={n:4d}  total_R={total:+.1f}  per_month={total/4:+.2f}")


if __name__ == "__main__":
    main()
