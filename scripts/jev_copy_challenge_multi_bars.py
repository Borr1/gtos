#!/usr/bin/env python3
"""Copy Challenge multi-symbol CSVs from box/VPS paths into the lab landing dir.

Does not invent bars. Does not use April data/historical. Missing src → n_copied=0.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.bars import copy_multi_csvs_if_present, landed_challenge_symbols


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=None)
    args = parser.parse_args()
    result = copy_multi_csvs_if_present(args.src)
    result["landed_after"] = landed_challenge_symbols()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
