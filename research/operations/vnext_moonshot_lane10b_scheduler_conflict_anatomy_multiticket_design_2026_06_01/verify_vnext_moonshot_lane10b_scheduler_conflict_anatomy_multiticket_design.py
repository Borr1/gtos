"""Verify Lane10b scheduler conflict anatomy route artifacts."""

from __future__ import annotations

import json

from build_vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design import (
    verify_outputs,
)


def main() -> int:
    result = verify_outputs(write=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
