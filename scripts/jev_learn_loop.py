#!/usr/bin/env python3
"""Shadow-score Challenge closes into LEARN_LOOP_V0. Log only. No place."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Harness never POSTs. Local fluid instruments are enough.
os.environ.setdefault("GTOS_JEV_A1_CALL", "0")

from src.judgment.learn_loop import (  # noqa: E402
    DEFAULT_FIXTURES,
    LearnLoopStore,
    load_close_fixtures,
    run_close_harness,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument(
        "--store",
        type=Path,
        default=ROOT / "judgment/astra/lab/learn_loop_v0/last_run.jsonl",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "judgment/astra/lab/learn_loop_v0/last_run.summary.json",
    )
    args = parser.parse_args()
    deals = load_close_fixtures(args.fixtures)
    if not deals:
        print(f"no fixtures at {args.fixtures}", file=sys.stderr)
        return 2
    store = LearnLoopStore(args.store)
    pack = run_close_harness(deals, store=store)
    compact = {
        "schema": pack["schema"],
        "close_loop": pack.get("close_loop"),
        "never_place": True,
        "apply": False,
        "silent_apply": False,
        "april_historical_used": pack["april_historical_used"],
        "news_protocol_invented": False,
        "n_rows": pack["n_rows"],
        "scoreboard": pack["scoreboard"],
        "promotion": pack["promotion"],
        "asset_class_prove": pack.get("asset_class_prove"),
        "tickets": [r.get("ticket") for r in pack["rows"]],
        "exit_classes": {str(r.get("ticket")): r.get("exit_class") for r in pack["rows"]},
        "miss_types": {str(r.get("ticket")): r.get("miss_type") for r in pack["rows"]},
        "store": str(args.store),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(compact, indent=2) + "\n", encoding="utf-8")
    board = pack["scoreboard"]
    print(
        f"login {board['account']} sample_n {board.get('sample_n')} "
        f"by_exit {board['by_exit_class']} never_place {pack['never_place']}"
    )
    for rec in pack["rows"]:
        print(
            f"  {rec.get('ticket')} {rec.get('symbol')} {rec.get('asset_class')} "
            f"{rec.get('exit_class')} {rec.get('miss_type')} R={rec.get('R')} "
            f"src={rec.get('r_source')} prove={rec.get('prove_next')}"
        )
    batch = board.get("batch") or {}
    print(
        f"batch n={batch.get('n')} sum_R={batch.get('sum_R')} "
        f"mean_R={batch.get('mean_R')} exits={batch.get('exit_class')} "
        f"miss={batch.get('miss_type')} tickets_invented={batch.get('tickets_invented')}"
    )
    assets = batch.get("by_asset_class") or {}
    for name in ("XAU", "INDEX", "FX", "CRYPTO"):
        block = assets.get(name) or {}
        print(
            f"  asset {name} n={block.get('n')} mean_R={block.get('mean_R')} "
            f"wins={block.get('wins')}"
        )
    prove = pack.get("asset_class_prove") or {}
    print(
        f"asset_class_prove apply={prove.get('apply')} "
        f"identity_ok={prove.get('batch_identity_ok')} "
        f"n_candidates={prove.get('n_candidates')}"
    )
    for cand in prove.get("candidates") or []:
        print(
            f"  {cand.get('pattern')} n={cand.get('n')} "
            f"status={cand.get('status')} apply={cand.get('apply')} "
            f"q={cand.get('proposed_question')}"
        )
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
