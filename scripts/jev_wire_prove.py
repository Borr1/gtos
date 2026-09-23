#!/usr/bin/env python3
"""Score whether either named wire is PROVED_SHADOW. Never apply. Never invent a pass."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.process_lock import WIRE_COST, WIRE_FLOW
from src.judgment.wire_prove import prove_dual_file


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
        default=ROOT / "judgment/astra/lab/wires/W_DUAL_PROVE.json",
    )
    args = parser.parse_args()
    if not args.shadow.is_file():
        print(f"missing shadow pack: {args.shadow}", file=sys.stderr)
        return 2
    receipt = prove_dual_file(args.shadow, out=args.out)
    flow = receipt["candidates"][WIRE_FLOW]
    cost = receipt["candidates"][WIRE_COST]
    print(json.dumps({
        "clears_first_hint": receipt["clears_first_hint"],
        "wire_apply": False,
        "progress": receipt["progress"],
        WIRE_FLOW: {k: flow[k] for k in ("verdict", "n_xau_sufficient", "n_shadow_tilt_moved", "reasons") if k in flow},
        WIRE_COST: {k: cost[k] for k in ("verdict", "n_xau_cost_complete", "n_shadow_cost_tilt_moved", "reasons") if k in cost},
        "out": receipt.get("out"),
        "out_flow": receipt.get("out_flow"),
        "out_cost": receipt.get("out_cost"),
    }, indent=2))
    ok = flow["verdict"] in {"NOT_PROVED", "PROVED_SHADOW"} and cost["verdict"] in {"NOT_PROVED", "PROVED_SHADOW"}
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
