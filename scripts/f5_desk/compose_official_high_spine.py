"""Compose the Warsh-class official HIGH spine the F5 writer actually reads.

Merges intel-layer news_brief (live speakers) + news_calendar.json (FOMC/CPI/NFP
history and scheduled decisions). Does not read news_tape. Does not flip
news_filter YAML. Does not place or restart.

Usage:
    python scripts/f5_desk/compose_official_high_spine.py
    python scripts/f5_desk/compose_official_high_spine.py --write
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.components.ultimate_book.minimal_size import f5_compose_official_high_spine

INTEL_SPINE = Path(r"C:\Users\trader\intel-layer\calendar\official_high_spine.json")
REPO_SPINE = _REPO / "data" / "official_high_spine.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="compose_official_high_spine")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--repo", type=Path, default=_REPO)
    args = parser.parse_args(argv)
    now = datetime.now(timezone.utc)
    spine = f5_compose_official_high_spine(args.repo, now=now)
    names = [e.get("name") for e in spine.get("events") or []]
    print(json.dumps({
        "events": len(names),
        "extracted_utc": spine.get("extracted_utc"),
        "has_warsh": any("warsh" in str(n).lower() for n in names),
        "has_nfp": any("nfp" in str(n).lower() or "non-farm" in str(n).lower() or "nonfarm" in str(n).lower() for n in names),
        "first": names[:8],
    }, indent=2))
    if args.write:
        payload = json.dumps(spine, indent=2) + "\n"
        for dest in (REPO_SPINE, INTEL_SPINE):
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(payload, encoding="utf-8")
            print("wrote", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
