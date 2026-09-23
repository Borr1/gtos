#!/usr/bin/env python3
"""Verify Wave 1A hard-halt forensic route artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def main() -> int:
    repo_root = _repo_root()
    sys.path.insert(0, str(repo_root))
    from src.research_infra.wave1a_hard_halt_forensics import ROUTE_REL, verify_route

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-dir", default=str(repo_root / ROUTE_REL))
    parser.add_argument("--write-result", action="store_true")
    args = parser.parse_args()
    route_dir = Path(args.route_dir)
    result = verify_route(route_dir)
    if args.write_result:
        (route_dir / "WAVE1A_VERIFICATION_RESULT.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

