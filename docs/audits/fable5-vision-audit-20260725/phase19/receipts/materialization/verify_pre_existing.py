#!/usr/bin/env python3
"""Rule-2 fence: the five pre-existing lane windows must not move. Ever.

Run after EVERY mutating step. Compares each pre-existing window's whole
registry entry -- not just its source-plan digest -- against a frozen baseline,
because an entry can drift in `pack_root` or `source_manifest_root_sha256`
while the plan digest stays put, and that is still corruption of the substrate.

Outcome-blind: reads registry JSON and manifest JSON only. No pack row, no
candidate, no ledger, no economic field is opened.

  python3 verify_pre_existing.py --freeze   # write the baseline (once)
  python3 verify_pre_existing.py            # check; exit 1 on any drift
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REGISTRY = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
    "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/LANE_INPUT_REGISTRY.json"
)
BASELINE = Path(__file__).with_name("PRE_EXISTING_WINDOW_BASELINE.json")
PRE_EXISTING = (
    "january_2026",
    "february_2026",
    "march_2026",
    "april_2026",
    "may_2026",
)
# The two digests the task statement pins by value. Checked literally, so a
# baseline written from an already-corrupted registry cannot launder them.
PINNED = {
    "january_2026": (
        "b44b433039bf7f5372fc067f62477cdb5c8b0d2caf4202755a922a7c198be954"
    ),
    "march_2026": (
        "8163172cbae28ae943ae940f3293bb2272671114e9e9bc0de3a7e04f79ffdf8e"
    ),
}


def snapshot() -> dict[str, dict]:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    windows = payload.get("windows") or {}
    out: dict[str, dict] = {}
    for window_id in PRE_EXISTING:
        entry = windows.get(window_id)
        if entry is None:
            raise SystemExit(f"FATAL missing pre-existing window: {window_id}")
        manifest_path = REGISTRY.parent / str(entry["source_manifest"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        out[window_id] = {
            "entry": entry,
            "manifest_root_sha256": manifest.get("manifest_root_sha256"),
            "manifest_bytes_sha256": __import__("hashlib")
            .sha256(manifest_path.read_bytes())
            .hexdigest(),
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--label", default="")
    ns = parser.parse_args()

    current = snapshot()
    for window_id, digest in PINNED.items():
        got = current[window_id]["entry"].get("canonical_source_plan_digest_sha256")
        if got != digest:
            print(f"FAIL pinned digest moved: {window_id} {got} != {digest}")
            return 1

    if ns.freeze:
        BASELINE.write_text(
            json.dumps(current, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"FROZEN {len(current)} pre-existing windows -> {BASELINE.name}")
        return 0

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    drift = [w for w in PRE_EXISTING if baseline.get(w) != current.get(w)]
    if drift:
        print(f"FAIL pre-existing windows drifted: {drift}")
        for w in drift:
            print("  baseline:", json.dumps(baseline.get(w), sort_keys=True))
            print("  current :", json.dumps(current.get(w), sort_keys=True))
        return 1
    label = f" [{ns.label}]" if ns.label else ""
    print(f"PASS 5/5 pre-existing windows byte-identical{label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
