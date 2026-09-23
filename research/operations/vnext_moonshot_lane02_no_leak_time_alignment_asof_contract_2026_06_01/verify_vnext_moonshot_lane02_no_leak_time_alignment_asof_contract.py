"""Verifier for vNext Moonshot Lane02 no-leak/as-of contract artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROUTE_DIR = Path(__file__).resolve().parent
if str(ROUTE_DIR) not in sys.path:
    sys.path.insert(0, str(ROUTE_DIR))

import build_vnext_moonshot_lane02_no_leak_time_alignment_asof_contract as builder  # noqa: E402


def main() -> int:
    result = builder.verify_outputs(write=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
