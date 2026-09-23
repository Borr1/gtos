#!/usr/bin/env python3
"""Build Wave3 hard-halt causal microscope continuation route artifacts."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research_infra.wave3_hard_halt_causal_microscope import build_route


if __name__ == "__main__":
    result = build_route(ROOT)
    raise SystemExit(0 if result.get("ok") else 1)
