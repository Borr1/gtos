from __future__ import annotations

import json

from build_vnext_absolute_moonshot_execution_policy_v3 import verify_outputs


def main() -> None:
    result = verify_outputs(write=True, count_large=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
