from __future__ import annotations

import json

from build_vnext_absolute_moonshot_lane17_market_awareness_whiteboard import verify_outputs


def main() -> int:
    result = verify_outputs(write=True, count_large=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
