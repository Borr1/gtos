#!/usr/bin/env python3
"""SHADOW-prove harvest P0-1 / P0-2 / P0-5 on Challenge 0. Never places."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.harvest_prove import DEFAULT_RECEIPT, run_harvest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    receipt = run_harvest(out=args.out)
    p02 = receipt.get("p0_2") or {}
    p05 = receipt.get("p0_5") or {}
    print(
        json.dumps(
            {
                "p0_1": {
                    "verdict": receipt.get("verdict"),
                    "n": receipt.get("n"),
                    "n_decidable": receipt.get("n_decidable"),
                    "n_moved": receipt.get("n_moved"),
                    "n_invented_high": receipt.get("n_invented_high"),
                    "symbols": receipt.get("symbols"),
                    "landed_books": receipt.get("landed_books"),
                    "out": receipt.get("out"),
                },
                "p0_2": {
                    "verdict": p02.get("verdict"),
                    "n_decidable": p02.get("n_decidable"),
                    "n_moved": p02.get("n_moved"),
                    "n_non_xau_tf_attached": p02.get("n_non_xau_tf_attached"),
                    "n_non_xau_route_class_unknown": p02.get("n_non_xau_route_class_unknown"),
                    "n_unknown_until_landed": p02.get("n_unknown_until_landed"),
                    "n_us30_house_hard_off": p02.get("n_us30_house_hard_off"),
                    "n_invented_route_class": p02.get("n_invented_route_class"),
                    "n_invented_route_class_non_xau": p02.get("n_invented_route_class_non_xau"),
                    "tf_routes": p02.get("tf_routes"),
                    "route_classes": p02.get("route_classes"),
                    "chair_named_atom": p02.get("chair_named_atom"),
                    "ready_to_apply": p02.get("ready_to_apply"),
                    "out": receipt.get("out_p0_2"),
                    "reasons": p02.get("reasons"),
                },
                "p0_5": {
                    "verdict": p05.get("verdict"),
                    "n_decidable": p05.get("n_decidable"),
                    "n_moved": p05.get("n_moved"),
                    "fill_models": p05.get("fill_models"),
                    "ready_to_apply": p05.get("ready_to_apply"),
                    "out": receipt.get("out_p0_5"),
                    "reasons": p05.get("reasons"),
                },
            },
            indent=2,
        )
    )
    verdicts = {receipt.get("verdict"), p02.get("verdict"), p05.get("verdict")}
    return 0 if verdicts <= {"PROVED_SHADOW", "NOT_PROVED", None} else 3


if __name__ == "__main__":
    raise SystemExit(main())
