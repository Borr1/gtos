#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_final_moonshot_wave1c_dual_broker_architecture import main


if __name__ == "__main__":
    raise SystemExit(main())
