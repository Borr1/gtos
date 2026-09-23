#!/usr/bin/env python3
"""Print / write the all-instrument Challenge vs Jev data inventory.

Read-only. Never places, remints, flattens, or applies size.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.data_inventory import collect_inventory, render_markdown, write_markdown


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "judgment" / "astra" / "DATA_INVENTORY_ALL_INSTRUMENTS.md",
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        type=Path,
        default=ROOT / "judgment" / "astra" / "lab" / "wires" / "DATA_INVENTORY_ALL_INSTRUMENTS.json",
    )
    parser.add_argument("--print", action="store_true", help="Print markdown to stdout")
    parser.add_argument("--json-only", action="store_true", help="Print JSON to stdout; still write files unless --no-write")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    inv = collect_inventory()
    if not args.no_write:
        receipt = write_markdown(args.out, args.json_path, inv=inv)
        print(json.dumps(receipt, indent=2))
    if args.json_only:
        print(json.dumps(inv, indent=2, default=str))
    elif args.print:
        print(render_markdown(inv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
