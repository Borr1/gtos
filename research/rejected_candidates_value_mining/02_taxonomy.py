"""
Section 1: Build rejection taxonomy.

Bucket every NO_TRADE / REJECTED_L2 / BLOCKED_LIMIT / PARSE_ERROR row by reason category.
Quantify by instrument, month, kill-zone, AI-direction-evaluated.

Output:
  taxonomy.json - structured counts
  taxonomy_summary.csv - flat table for inspection
"""
import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
OUT_DIR = ROOT / "research/rejected_candidates_value_mining"

# Read rejected rows
rejected = []
with open(OUT_DIR / "rejected_rows.jsonl", "r") as f:
    for line in f:
        rejected.append(json.loads(line))


def categorize_reason(row):
    """Return a coarse bucket for the rejection reason."""
    decision = row["decision"]
    reason = (row.get("no_trade_reason") or "").lower()
    l2_reason = (row.get("l2_reason") or "").lower()

    if decision == "PARSE_ERROR":
        return ("PARSE_ERROR", "parse_error")

    if decision == "BLOCKED_LIMIT":
        return ("BLOCKED_LIMIT", "blocked_limit")

    if decision == "REJECTED_L2":
        # L2 reason categories
        if l2_reason.startswith("entry_in_ob"):
            return ("L2_REJECT", "entry_in_ob")
        if l2_reason.startswith("h1_poi_exists"):
            return ("L2_REJECT", "h1_poi_exists")
        if l2_reason.startswith("m15_choch_exists"):
            return ("L2_REJECT", "m15_choch_exists")
        if l2_reason.startswith("sl_beyond_ob"):
            return ("L2_REJECT", "sl_beyond_ob")
        # Fallback if l2_reason is missing in source
        return ("L2_REJECT", "other_or_unknown")

    # NO_TRADE
    if reason.startswith("c1_failed"):
        return ("NO_TRADE", "c1_failed")
    if reason.startswith("c2_m15_opposing"):
        return ("NO_TRADE", "c2_m15_opposing")
    if reason.startswith("c3_direction_mismatch"):
        return ("NO_TRADE", "c3_direction_mismatch")
    if reason.startswith("no_qualifying_h1_poi"):
        return ("NO_TRADE", "no_qualifying_h1_poi")
    if reason.startswith("ob_proximity"):
        return ("NO_TRADE", "ob_proximity_no_unmitigated")
    if reason.startswith("prescreen") or "l1_no_direction" in reason:
        return ("NO_TRADE", "prescreen_no_direction")
    if reason == "" or reason == "none":
        return ("NO_TRADE", "no_reason_logged")
    # capture other unique buckets
    short = reason.split(":")[0][:60]
    return ("NO_TRADE", f"other:{short}")


# Categorize each row
for r in rejected:
    bucket_top, bucket_sub = categorize_reason(r)
    r["bucket_top"] = bucket_top
    r["bucket_sub"] = bucket_sub


# Counts
top_counter = Counter(r["bucket_top"] for r in rejected)
sub_counter = Counter(r["bucket_sub"] for r in rejected)

# Per instrument breakdown
inst_sub = defaultdict(Counter)
for r in rejected:
    inst_sub[r["_instrument"]][r["bucket_sub"]] += 1

# Per month
def month(ts):
    if not ts:
        return "unknown"
    try:
        return ts[:7]
    except Exception:
        return "unknown"


month_sub = defaultdict(Counter)
for r in rejected:
    month_sub[month(r.get("timestamp_utc"))][r["bucket_sub"]] += 1

# Per session / kill_zone
kz_sub = defaultdict(Counter)
for r in rejected:
    kz_sub[r.get("kill_zone") or "none"][r["bucket_sub"]] += 1

# Print summary
print("===== Rejection Taxonomy =====")
print(f"Total rejected rows: {len(rejected)}")
print()
print("Top bucket counts:")
for k, v in top_counter.most_common():
    pct = 100.0 * v / len(rejected)
    print(f"  {k}: {v} ({pct:.1f}%)")
print()
print("Sub-bucket counts:")
for k, v in sub_counter.most_common():
    pct = 100.0 * v / len(rejected)
    print(f"  {k}: {v} ({pct:.1f}%)")
print()
print("Per-instrument top sub-buckets:")
for inst, sc in sorted(inst_sub.items()):
    total = sum(sc.values())
    print(f"  {inst} (total {total}):")
    for sub, cnt in sc.most_common(8):
        pct = 100.0 * cnt / total
        print(f"    {sub}: {cnt} ({pct:.1f}%)")
print()
print("Per-month top sub-buckets:")
for m, sc in sorted(month_sub.items()):
    if m == "unknown":
        continue
    total = sum(sc.values())
    print(f"  {m} (total {total}):")
    for sub, cnt in sc.most_common(5):
        pct = 100.0 * cnt / total
        print(f"    {sub}: {cnt} ({pct:.1f}%)")

# Persist
out = {
    "total_rejected": len(rejected),
    "top_bucket_counts": dict(top_counter),
    "sub_bucket_counts": dict(sub_counter),
    "per_instrument": {k: dict(v) for k, v in inst_sub.items()},
    "per_month": {k: dict(v) for k, v in month_sub.items()},
    "per_kill_zone": {k: dict(v) for k, v in kz_sub.items()},
}
with open(OUT_DIR / "taxonomy.json", "w") as f:
    json.dump(out, f, indent=2, default=str)

# Re-write rejected_rows.jsonl with bucket info
with open(OUT_DIR / "rejected_rows_bucketed.jsonl", "w") as f:
    for r in rejected:
        f.write(json.dumps(r, default=str) + "\n")
print()
print(f"Wrote {OUT_DIR / 'taxonomy.json'}")
print(f"Wrote {OUT_DIR / 'rejected_rows_bucketed.jsonl'}")
