"""Verify Lane10 Portfolio Scheduler V2 route artifacts."""

from __future__ import annotations

import json

from build_vnext_moonshot_lane10_portfolio_scheduler_v2 import verify_outputs


def main() -> int:
    result = verify_outputs(write=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
