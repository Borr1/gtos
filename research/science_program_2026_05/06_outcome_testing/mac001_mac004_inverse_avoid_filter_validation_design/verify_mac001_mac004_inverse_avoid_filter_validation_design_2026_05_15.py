from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("build_mac001_mac004_inverse_avoid_filter_validation_design_2026_05_15.py")


def _load_builder():
    spec = importlib.util.spec_from_file_location("mac_inverse_builder", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load builder script: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify() -> dict:
    builder = _load_builder()
    return builder.verify_outputs()


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
