from __future__ import annotations

import json
import sys

from build_vnext_moonshot_lane08_digital_twin_replay_engine import verify_outputs


def main() -> None:
    result = verify_outputs(write=True, count_large=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
