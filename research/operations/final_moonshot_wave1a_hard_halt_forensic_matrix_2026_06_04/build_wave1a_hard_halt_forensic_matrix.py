#!/usr/bin/env python3
"""Build Wave 1A hard-halt broker/candidate forensic artifacts."""

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
    from src.research_infra.wave1a_hard_halt_forensics import ROUTE_REL, build_route

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-dir", default=str(repo_root / ROUTE_REL))
    args = parser.parse_args()
    result = build_route(repo_root, Path(args.route_dir))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

