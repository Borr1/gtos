from __future__ import annotations

import json

from build_vnext_moonshot_lane09_meta_selector_v2 import verify_outputs


def main() -> None:
    result = verify_outputs(write=True, require_focused_test=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
