#!/usr/bin/env python3
"""Chair entrypoint: Challenge fluid-gate shadow cycle.

Default is a no-op unless ``GTOS_JEV_FLUID_GATES_SHADOW=1`` (or ``--force``
for a local dry-run). Never places, remints, flattens, or mints tokens.

    GTOS_JEV_FLUID_GATES_SHADOW=1 python3 scripts/run_jev_fluid_gates_shadow.py

See ``judgment/CHAIR_ENABLE_SHADOW_CHALLENGE.md``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.judgment.challenge import CHALLENGE_LOGIN  # noqa: E402
from src.judgment.cycle import run_fluid_gate_cycle  # noqa: E402
from src.judgment.flags import APPLY_ENV, SHADOW_ENV  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--log-dir",
        default=None,
        help="Override judgment/live/jev_sidecar (also GTOS_JEV_FLUID_GATES_LOG_DIR)",
    )
    parser.add_argument(
        "--prove-dir",
        default=None,
        help="Directory of named prove receipts (A1/A2/A3/W_named)",
    )
    parser.add_argument("--prove-site", default=None, help="Prove receipt site_id")
    parser.add_argument(
        "--stake",
        default="sleeve_admit",
        help="Gate stake (label_assist|sleeve_admit|corr_hold). place/remint/flatten VETO.",
    )
    parser.add_argument(
        "--login",
        default=CHALLENGE_LOGIN,
        help="Must stay 0 (Challenge sole payout writer)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run one cycle even if GTOS_JEV_FLUID_GATES_SHADOW is unset (still shadow-only)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=None,
        help="Inject a Choice confidence for a dry-run (no TypeSafe call)",
    )
    args = parser.parse_args(argv)

    answers = None
    if args.confidence is not None:
        answers = {
            "next_gate": {
                "choice": "HOLD",
                "confidence": args.confidence,
                "probabilities": {"HOLD": args.confidence, "ABSTAIN": 1.0 - args.confidence},
            }
        }

    result = run_fluid_gate_cycle(
        login=args.login,
        stake=args.stake,
        log_dir=args.log_dir,
        prove_dir=args.prove_dir,
        prove_site_id=args.prove_site,
        answers=answers,
        force=args.force,
    )
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    if result.skipped:
        print(
            f"\nShadow is off. Chair enable: export {SHADOW_ENV}=1 "
            f"(APPLY stays off until {APPLY_ENV}=1 + prove receipt).",
            file=sys.stderr,
        )
        return 2
    return 0 if result.verify.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
