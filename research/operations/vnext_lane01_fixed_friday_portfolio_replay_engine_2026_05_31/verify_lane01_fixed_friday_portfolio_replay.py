"""Route-owned verifier for Lane 01 fixed-Friday portfolio replay."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "build_vnext_lane01_fixed_friday_portfolio_replay.py"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_vnext_lane01_fixed_friday_portfolio_replay import verify_outputs


def main() -> int:
    result = verify_outputs(write=False)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
