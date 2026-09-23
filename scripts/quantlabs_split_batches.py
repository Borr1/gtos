"""Split the tagged blog manifest into extraction batches.

Reads urls_blog.txt, selects PRIORITY + top-N-recent KEEP URLs,
splits into equal-ish batches, writes batch_NN.txt files.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: split_batches.py <manifest> <out_dir> <num_batches> [keep_cap]", file=sys.stderr)
        return 2
    manifest = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    n = int(sys.argv[3])
    keep_cap = int(sys.argv[4]) if len(sys.argv) > 4 else 168
    out_dir.mkdir(parents=True, exist_ok=True)

    priority: list[str] = []
    keep: list[str] = []
    with manifest.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3:
                continue
            url, mod, tag = parts[0], parts[1], parts[2]
            if tag == "PRIORITY":
                priority.append(f"{url} | {mod} | {tag}")
            elif tag == "KEEP":
                keep.append(f"{url} | {mod} | {tag}")

    selected = priority + keep[:keep_cap]
    total = len(selected)

    # Round-robin into n batches so each gets a mix of priority + keep
    batches: list[list[str]] = [[] for _ in range(n)]
    for i, row in enumerate(selected):
        batches[i % n].append(row)

    for i, batch in enumerate(batches, 1):
        path = out_dir / f"batch_{i:02d}.txt"
        with path.open("w", encoding="utf-8") as f:
            f.write(f"# Batch {i:02d} — {len(batch)} URLs (mix of PRIORITY + KEEP)\n")
            for row in batch:
                f.write(row + "\n")

    print(f"Split {total} URLs ({len(priority)} PRIORITY + {min(keep_cap, len(keep))} KEEP) into {n} batches in {out_dir}")
    for i, batch in enumerate(batches, 1):
        print(f"  batch_{i:02d}.txt: {len(batch)} URLs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
