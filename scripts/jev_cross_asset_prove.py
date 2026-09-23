#!/usr/bin/env python3
"""Survey + offline CROSS_ASSET prove on the Challenge shadow pack. Log only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.cross_asset_prove import run_prove


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=None)
    parser.add_argument("--deals", type=Path, default=None)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    payload = run_prove(pack_path=args.pack, deals_path=args.deals, write=not args.no_write)
    print(json.dumps({k: payload[k] for k in (
        "schema",
        "n_rows",
        "n_proved_shadow",
        "n_not_proved",
        "survey",
        "targets",
        "hydrate",
        "hydrate_event",
        "flips_vs_prior",
        "apply_any",
        "no_ca_apply_flip",
        "physical_size",
        "next_prove_targets",
        "never_place",
    ) if k in payload}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
