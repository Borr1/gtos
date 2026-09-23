#!/usr/bin/env python3
"""Complete-judge historical prove — Challenge 0 tape.

No live bars. No host-mesh. No order_send. No invented NEWS_PROTOCOL.

    python3 scripts/run_complete_judge_historical_prove.py --score-out /tmp/cj-prove.json

SHADOW labels only. Does not APPLY fire rate or size_ceiling.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.judgment.complete_judge_prove import prove_complete_judge  # noqa: E402
from src.judgment.fluid_gates import EXPECTED_FLUID  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score-out", default=None, help="Write prove scorecard JSON")
    args = parser.parse_args(argv)

    card = prove_complete_judge()
    slim = {k: v for k, v in card.items() if k != "rows"}
    slim["n_fluid_lock"] = EXPECTED_FLUID
    text = json.dumps(slim, indent=2, sort_keys=True)
    print(text)
    if args.score_out:
        path = Path(args.score_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    return 0 if card.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
