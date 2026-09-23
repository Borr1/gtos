from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage00_inventory_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage00", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


if __name__ == "__main__":
    raise SystemExit(module.main(["--check", *sys.argv[1:]]))
