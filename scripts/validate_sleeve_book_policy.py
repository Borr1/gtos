#!/usr/bin/env python3
"""Replay ``SleeveBookPolicy`` against the live book's own runtime-learning packets.

Reproduces the Phase-2 B90-B99 validation receipt.  Reads only; touches no broker
and writes nothing outside ``--out``.

Usage
-----
  python3 scripts/validate_sleeve_book_policy.py \
      --packets /Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/ultimate_book_runtime_learning_packets.jsonl.gz \
      --out docs/audits/fable5-vision-audit-20260725/phase2/receipts

Emits, into ``--out``:
  SLEEVE_BOOK_POLICY_VALIDATION.json       both n_active modes, disagreements enumerated
  SLEEVE_BOOK_POLICY_HARNESS_REPORT.json   replay_differential_harness verdicts + null control

Exit code is 0 when every comparable cycle agreed under supplied-count mode and
the null control was EQUIVALENT; 1 otherwise.  A non-zero exit means read the
enumerated disagreements, not that the run failed.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

from src.research_infra.replay_differential_harness import compare_arms  # noqa: E402
from src.research_infra.replay_policy import packet_validation as V  # noqa: E402

DEFAULT_PACKETS = (
    "/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/"
    "ultimate_book_runtime_learning_packets.jsonl.gz"
)


def _live_config() -> dict:
    with open(REPO / "config" / "agent_config.yaml", encoding="utf-8") as handle:
        return yaml.safe_load(handle)["gtos_vnext_runtime"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", default=DEFAULT_PACKETS)
    parser.add_argument("--out", required=True)
    parser.add_argument("--namespace", action="append", default=None)
    parser.add_argument("--day", action="append", default=None)
    parser.add_argument(
        "--arms",
        default=None,
        help="directory for the arm-shaped ledgers (default: a sibling of --out)",
    )
    args = parser.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = _live_config()

    reports = {}
    for mode, derive in (("supplied", False), ("derived", True)):
        reports[mode] = V.validate(
            args.packets,
            base_config=base,
            namespaces=args.namespace,
            days=args.day,
            derive_n_active=derive,
        )
        totals = reports[mode]["totals"]
        print(f"[{mode}] {json.dumps(totals)}", flush=True)

    # Arm-shaped ledgers, and the real differential harness over them.
    cycles = V.group_cycles(V.iter_packets(args.packets))
    if args.namespace:
        cycles = [c for c in cycles if c.namespace in set(args.namespace)]
    if args.day:
        cycles = [c for c in cycles if set(c.decision_days) & set(args.day)]
    results = [V.reconstruct_cycle(c, base_config=base) for c in cycles]
    comparable = [
        r
        for r in results
        if r.status in (V.MATCH, V.PARTIAL_MATCH, V.PORT_OR_LIVE_DEFECT)
    ]
    arms = Path(args.arms) if args.arms else out.parent / "_sleeve_book_policy_arms"
    if arms.exists():
        shutil.rmtree(arms)
    dirs = V.ledger_pair(comparable, arms)
    identity = {V.LEDGER_ROLE: (V.IDENTITY_FIELD,)}
    harness = {
        "null_control": compare_arms(
            dirs["policy"], dirs["null_control"], roles=[V.LEDGER_ROLE],
            alignment="identity", identity_keys=identity, expose_values=True,
        ),
        "policy_vs_live": compare_arms(
            dirs["policy"], dirs["live"], roles=[V.LEDGER_ROLE],
            alignment="identity", identity_keys=identity, expose_values=True,
        ),
    }
    for name, report in harness.items():
        role = report["roles"][V.LEDGER_ROLE]
        print(
            f"[harness:{name}] verdict={report['verdict']} "
            f"matched={role.get('matched_row_count')} "
            f"rows_with_differences={role.get('rows_with_differences')} "
            f"left_only={role.get('left_only_row_count')} "
            f"right_only={role.get('right_only_row_count')} "
            f"unknown={role.get('unknown_difference_count')}",
            flush=True,
        )

    (out / "SLEEVE_BOOK_POLICY_VALIDATION.json").write_text(
        json.dumps(reports, indent=1, default=str) + "\n", encoding="utf-8"
    )
    (out / "SLEEVE_BOOK_POLICY_HARNESS_REPORT.json").write_text(
        json.dumps(harness, indent=1, default=str) + "\n", encoding="utf-8"
    )
    shutil.rmtree(arms, ignore_errors=True)

    clean = (
        reports["supplied"]["totals"]["cycles_disagreeing"] == 0
        and harness["null_control"]["verdict"] == "EQUIVALENT"
    )
    return 0 if clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
