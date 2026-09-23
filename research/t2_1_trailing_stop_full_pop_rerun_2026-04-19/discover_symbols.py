"""Map each batch_api batch-id to the instrument symbol mentioned inside
its full_prompts.json. Writes batch_symbol_map.json next to this script.
"""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path
from collections import Counter


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "batch_symbol_map.json"

SYMBOLS = (
    "XAUUSD",
    "US30_cash",
    "US30",
    "USDJPY",
    "GBPJPY",
    "GBPUSD",
    "EURUSD",
    "NAS100",
    "XAGUSD",
)


def _prompt_text(prompt) -> str:
    if isinstance(prompt, str):
        return prompt
    if isinstance(prompt, list):
        parts = []
        for b in prompt:
            if isinstance(b, dict):
                parts.append(str(b.get("text", "")))
            else:
                parts.append(str(b))
        return " ".join(parts)
    return str(prompt)


def main() -> None:
    hits: dict[str, str] = {}
    counts: Counter[str] = Counter()
    for p in sorted(
        glob.glob(str(ROOT / "knowledge_base_backtest" / "batch_api" / "msgbatch_*_full_prompts.json"))
    ):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        if not d:
            continue
        text = _prompt_text(d[0].get("prompt", ""))
        found = "UNKNOWN"
        for s in SYMBOLS:
            if s in text:
                found = s
                break
        bid = os.path.basename(p).replace("_full_prompts.json", "")
        hits[bid] = found
        counts[found] += 1

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(hits, f, indent=2)
    print(f"batches scanned: {len(hits)}")
    print("symbol distribution:", dict(counts))
    print(f"map written: {OUT}")


if __name__ == "__main__":
    main()
