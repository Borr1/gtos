#!/usr/bin/env python3
"""Prove the named CA size wire on the Challenge shadow pack. APPLY stays false."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.ca_size_prove import run_prove


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=None)
    parser.add_argument("--deals", type=Path, default=None)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    payload = run_prove(pack_path=args.pack, deals_path=args.deals, write=not args.no_write)
    target = payload.get("target") or {}
    print(
        json.dumps(
            {
                "schema": payload.get("schema"),
                "wire_candidate": payload.get("wire_candidate"),
                "verdict": payload.get("verdict"),
                "apply": payload.get("apply"),
                "named_new_fire": payload.get("named_new_fire"),
                "not_silent_ca_apply_flip": payload.get("not_silent_ca_apply_flip"),
                "ca_label_apply_any": payload.get("ca_label_apply_any"),
                "n_rows": payload.get("n_rows"),
                "target": {
                    k: target.get(k)
                    for k in (
                        "id",
                        "verdict",
                        "apply",
                        "n_decidable",
                        "n_moved",
                        "n_distinct",
                        "vals",
                        "component_assembled",
                        "component_moved",
                        "reasons",
                        "n_live_not_one",
                        "n_combined_flow_x_cost",
                    )
                },
                "physical_size": payload.get("physical_size"),
                "survey": payload.get("survey"),
                "never_place": payload.get("never_place"),
                "invented_news_protocol": payload.get("invented_news_protocol"),
                "prove_path": payload.get("prove_path"),
            },
            indent=2,
        )
    )
    if payload.get("apply") is True:
        return 3
    return 0 if payload.get("verdict") in {"PROVED_SHADOW", "NOT_PROVED"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
