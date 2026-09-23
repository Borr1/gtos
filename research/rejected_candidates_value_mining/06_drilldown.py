"""
Section 3+4: Deep drill into top miss-pattern buckets.

Focus on:
  - m15_choch_exists (L2 reject; +0.44 ExpR ⇒ over-rejection?)
  - entry_in_ob (L2 reject; +0.25 ExpR; small n)
  - blocked_limit (BLOCKED; +0.05 ExpR but huge n=1397 ⇒ +74R total)
  - sl_beyond_ob (L2 reject; +0.11 ExpR)
  - c1_failed (NO_TRADE; barely positive +0.04 ExpR — ambiguous)

Confirm correctness:
  - no_qualifying_h1_poi (-0.32 ExpR ⇒ correct rejection)
  - c2_m15_opposing (-0.05 ExpR; mixed)
  - h1_poi_exists (-0.10 ExpR)
"""
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

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


def main():
    resolved = []
    with open(OUT_DIR / "forward_resolution.jsonl", "r") as f:
        for line in f:
            r = json.loads(line)
            if r["_resolved"]:
                resolved.append(r)

    # Add month
    for r in resolved:
        r["month"] = (r.get("timestamp_utc") or "")[:7]

    target_buckets = ["m15_choch_exists", "entry_in_ob", "blocked_limit", "sl_beyond_ob",
                      "c1_failed", "c2_m15_opposing", "h1_poi_exists", "no_qualifying_h1_poi",
                      "c3_direction_mismatch"]

    for bucket in target_buckets:
        bucket_rows = [r for r in resolved if r["bucket_sub"] == bucket]
        if not bucket_rows:
            continue
        print(f"\n========== {bucket} (n={len(bucket_rows)}) ==========")
        rs = [r["fwd_r"] for r in bucket_rows if r.get("fwd_r") is not None]
        wins = sum(1 for x in rs if x >= 1.5 - 1e-9)
        n = len(rs)
        wr = wins / n if n > 0 else 0
        lo, hi = wilson_ci(wins, n)
        print(f"WR: {wr:.3f} CI[{lo:.3f}, {hi:.3f}]   ExpR: {sum(rs)/n:+.3f}   TotalR: {sum(rs):+.1f}")

        # By month
        print(f"  By month:")
        by_mo = defaultdict(list)
        for r in bucket_rows:
            by_mo[r["month"]].append(r)
        for mo in sorted(by_mo):
            mr = [r["fwd_r"] for r in by_mo[mo] if r.get("fwd_r") is not None]
            if not mr:
                continue
            n2 = len(mr)
            w = sum(1 for x in mr if x >= 1.5 - 1e-9)
            print(f"    {mo}: n={n2:3d}, WR={w/n2:.3f}, ExpR={sum(mr)/n2:+.3f}, TotalR={sum(mr):+.1f}")

        # By instrument
        print(f"  By instrument (n>=10):")
        by_inst = defaultdict(list)
        for r in bucket_rows:
            by_inst[r["_instrument"]].append(r)
        for inst, rs2 in sorted(by_inst.items()):
            mr = [r["fwd_r"] for r in rs2 if r.get("fwd_r") is not None]
            if len(mr) < 10:
                continue
            n2 = len(mr)
            w = sum(1 for x in mr if x >= 1.5 - 1e-9)
            print(f"    {inst:12s}: n={n2:3d}, WR={w/n2:.3f}, ExpR={sum(mr)/n2:+.3f}, TotalR={sum(mr):+.1f}")

        # By direction
        print(f"  By forward direction:")
        by_dir = defaultdict(list)
        for r in bucket_rows:
            d = r.get("fwd_direction") or "UNK"
            by_dir[d].append(r)
        for d, rs2 in sorted(by_dir.items()):
            mr = [r["fwd_r"] for r in rs2 if r.get("fwd_r") is not None]
            n2 = len(mr)
            if n2 == 0:
                continue
            w = sum(1 for x in mr if x >= 1.5 - 1e-9)
            print(f"    {d:6s}: n={n2:3d}, WR={w/n2:.3f}, ExpR={sum(mr)/n2:+.3f}")

        # By session
        print(f"  By kill_zone:")
        by_kz = defaultdict(list)
        for r in bucket_rows:
            kz = r.get("kill_zone") or "none"
            by_kz[kz].append(r)
        for kz, rs2 in sorted(by_kz.items()):
            mr = [r["fwd_r"] for r in rs2 if r.get("fwd_r") is not None]
            n2 = len(mr)
            if n2 == 0:
                continue
            w = sum(1 for x in mr if x >= 1.5 - 1e-9)
            print(f"    {kz:10s}: n={n2:3d}, WR={w/n2:.3f}, ExpR={sum(mr)/n2:+.3f}")


if __name__ == "__main__":
    main()
