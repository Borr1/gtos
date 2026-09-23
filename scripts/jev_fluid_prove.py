#!/usr/bin/env python3
"""Prove remaining fluid gates on the Challenge-true pack. APPLY preauthorized.

Never places. SEL-V4-002 cannot APPLY. Envelope walls stay integers.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.fluid_prove import prove_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--shadow",
        type=Path,
        default=ROOT / "judgment/astra/lab/challenge_shadow_20260917/shadow.jsonl",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "judgment/astra/lab/wires/FLUID_PROVE_LEDGER.json",
    )
    parser.add_argument("--no-apply", action="store_true")
    args = parser.parse_args()
    if not args.shadow.is_file():
        print(f"missing shadow pack: {args.shadow}", file=sys.stderr)
        return 2
    receipt = prove_file(args.shadow, out=args.out, apply=not args.no_apply)
    print(
        json.dumps(
            {
                "n_rows": receipt.get("n_rows"),
                "n_proved_shadow": receipt.get("n_proved_shadow"),
                "n_not_proved": receipt.get("n_not_proved"),
                "n_inherited": receipt.get("n_inherited"),
                "applied_this_wave": receipt.get("applied_this_wave"),
                "held_research_or_ritual": receipt.get("held_research_or_ritual"),
                "proved": receipt.get("proved"),
                "not_proved": receipt.get("not_proved"),
                "out": receipt.get("out"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
