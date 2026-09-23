from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.build_vnext_lane09_cross_lane_merge_dossier_production_package import verify_outputs


if __name__ == "__main__":
    result = verify_outputs(write=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result.get("ok") else 1)
