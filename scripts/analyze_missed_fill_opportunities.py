#!/usr/bin/env python3
"""Build the preregistered missed-fill entry-geometry study."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.missed_fill_opportunity_study import build_study, write_markdown


DEFAULT_OUTPUT_JSON = Path("research/program_control/MISSED_FILL_ENTRY_GEOMETRY_STUDY_2026-05-12.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/MISSED_FILL_ENTRY_GEOMETRY_STUDY_2026-05-12.md")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()

    study = build_study(args.root)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(study, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(study, args.output_md)
    print(json.dumps(study, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
