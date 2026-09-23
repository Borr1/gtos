"""Emit the measured LP table straight from the receipts.

Transcribing eleven numbers per window by hand into a markdown table is how a
result document acquires a figure no artifact supports. This reads the arm
receipts and the pool receipts and prints the table, so every cell in
`LP_2025_POOLS_RESULT.md` has a file behind it.

Structural columns only -- row counts, digests, RSS, wall time. No economic
column is read or printed: three of these six windows are READ-RESTRICTED and
the other three are the next wave's to analyse, not LP's.
"""

from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ARMS = BASE / "arm_receipts"

WINDOWS = [
    ("june_2025", "LP_JUN_2025_S0R0", True),
    ("august_2025", "LP_AUG_2025_S0R0", True),
    ("september_2025", "LP_SEP_2025_S0R0", True),
    ("october_2025", "LP_OCT_2025_S0R0", False),
    ("november_2025", "LP_NOV_2025_S0R0", False),
    ("december_2025", "LP_DEC_2025_S0R0", False),
]


def _hms(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    seconds = int(seconds)
    return f"{seconds // 3600}h{(seconds % 3600) // 60:02d}m"


def main() -> int:
    print("### Arms as measured\n")
    print("| window | days | wall | max RSS | candidate rows | missed rows | orders | trades |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for window, prefix, _ in WINDOWS:
        path = ARMS / f"{prefix}_RECEIPT.json"
        if not path.is_file():
            print(f"| `{window}` | - | NOT BUILT | - | - | - | - | - |")
            continue
        r = json.loads(path.read_text())
        counts = r.get("receipt_counts") or {}
        rss = (r.get("rusage") or {}).get("maxrss_bytes")
        days = len(r.get("progress_rows") or [])
        print(
            f"| `{window}` | {days} | {_hms(r.get('wall_seconds'))} | "
            f"{(rss or 0) / 1e9:.2f} GB | {counts.get('candidate_rows', '-'):,} | "
            f"{counts.get('missed_opportunity_rows', '-'):,} | "
            f"{counts.get('order_rows', '-'):,} | {counts.get('trade_rows', '-'):,} |"
        )

    print("\n### Pools as built\n")
    print("| window | pool | rows | join keys | days | sha256 | read |")
    print("|---|---|---:|---:|---:|---|---|")
    for window, _, restricted in WINDOWS:
        path = BASE / f"{window}_S0R0_POOL_V1.json"
        if not path.is_file():
            print(f"| `{window}` | NOT BUILT | - | - | - | - | - |")
            continue
        r = json.loads(path.read_text())
        pool = r.get("compact_pool") or {}
        flag = "**RESTRICTED**" if restricted else "open"
        print(
            f"| `{window}` | `{pool.get('path')}` | {pool.get('rows', 0):,} | "
            f"{pool.get('unique_join_keys', 0):,} | {len(pool.get('dates') or [])} | "
            f"`{str(pool.get('sha256'))[:16]}…` | {flag} |"
        )

    print("\n### Receipt digests\n")
    for window, _, _ in WINDOWS:
        path = BASE / f"{window}_S0R0_POOL_V1.json"
        if path.is_file():
            r = json.loads(path.read_text())
            print(f"- `{window}` receipt `self_sha256` `{r.get('self_sha256')}`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
