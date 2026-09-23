#!/usr/bin/env python3
"""Measure remaining SHADOW fluid axes. Never invent. Never place. Never APPLY."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.shadow_unlock import measure_shadow_unlock, write_receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--shadow",
        type=Path,
        default=ROOT / "judgment/astra/lab/challenge_shadow_20260917/shadow.jsonl",
    )
    parser.add_argument(
        "--deals",
        type=Path,
        default=ROOT / "judgment/astra/lab/challenge_shadow_20260917/deals_since_20260909.jsonl",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "judgment/astra/lab/wires/SHADOW_UNLOCK_RECEIPT.json",
    )
    args = parser.parse_args()
    receipt = measure_shadow_unlock(pack_path=args.shadow, deals_path=args.deals)
    write_receipt(receipt, dest=args.out)
    shadow = receipt.get("shadow_axes") or {}
    print(
        json.dumps(
            {
                "n_fluid": (receipt.get("inventory") or {}).get("n_fluid"),
                "by_status": (receipt.get("inventory") or {}).get("by_status"),
                "shadow": (receipt.get("inventory") or {}).get("shadow"),
                "research_only": (receipt.get("inventory") or {}).get("research_only"),
                "any_honest_fill": receipt.get("any_honest_fill"),
                "filled_this_pass": receipt.get("filled_this_pass"),
                "landed_symbols": (receipt.get("multi_instrument") or {}).get("landed_symbols"),
                "n_non_xau_sufficient": (receipt.get("pack") or {}).get("n_non_xau_sufficient"),
                "shadow_blocked": {
                    gid: {
                        "missing_field": row.get("missing_field"),
                        "can_honestly_fill": row.get("can_honestly_fill_from_existing_challenge_state"),
                        "reasons": row.get("reasons"),
                    }
                    for gid, row in shadow.items()
                },
                "out": str(args.out),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
