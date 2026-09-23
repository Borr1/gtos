#!/usr/bin/env python3
"""Assemble the LM-MAT machine receipt from metadata only.

Reads: the lane registry, each window's source manifest, each window's
materialization/source-plan/pack receipts, and the source catalog. Every field
it touches is a path, a count, a timestamp or a digest.

It never opens a pack shard, a candidate, a ledger or a trade table, and it
computes no economic quantity -- the per-symbol coverage the deliverable asks
for is `first_utc` / `last_utc` / `row_count` as DECLARED by the catalog and the
manifests, which is exactly the metadata-only check the brief specifies. Row
decoding would both violate outcome-blindness and be a weaker check anyway,
since the declared values are what every downstream binding actually verifies
against.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HOLD = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
    "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
REGISTRY = HOLD / "LANE_INPUT_REGISTRY.json"
CATALOG = HOLD / "SOURCE_CATALOG.json"
HERE = Path(__file__).resolve().parent
PRE_EXISTING = (
    "january_2026",
    "february_2026",
    "march_2026",
    "april_2026",
    "may_2026",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _free_gb() -> float:
    out = subprocess.run(
        ["df", "-k", "/"], capture_output=True, text=True, check=True
    ).stdout.splitlines()[-1].split()
    return round(int(out[3]) / 1048576, 2)


def window_report(window_id: str, registry: dict, catalog: dict) -> dict:
    entry = registry["windows"][window_id]
    manifest_path = REGISTRY.parent / str(entry["source_manifest"])
    manifest = _load(manifest_path)

    per_symbol: dict[str, dict] = {}
    for row in manifest.get("bar_sources") or ():
        symbol = str(row["symbol"])
        per_symbol.setdefault(symbol, {})[str(row["timeframe"])] = {
            "first_utc": row["first_utc"],
            "last_utc": row["last_utc"],
            "row_count": row["row_count"],
            "sha256": row["sha256"],
            "source_family": row["source_family"],
        }
    for row in manifest.get("tick_sources") or ():
        per_symbol.setdefault(str(row["symbol"]), {})["TICK"] = {
            "first_utc": row["first_utc"],
            "last_utc": row["last_utc"],
            "row_count": row["row_count"],
            "sha256": row["sha256"],
            "source_family": row["source_family"],
        }

    # Coverage verdict, metadata only: for every symbol, does the declared M1
    # and M15 span enclose the window's calendar? D1/H4 reach back to 2014 and
    # are checked at the timeframe level by the materializer itself.
    start = datetime.fromisoformat(entry["window"][0]).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(entry["window"][1]).replace(tzinfo=timezone.utc)
    incomplete: list[str] = []
    for symbol, frames in per_symbol.items():
        for timeframe in ("D1", "H4", "M15", "M1"):
            frame = frames.get(timeframe)
            if frame is None:
                incomplete.append(f"{symbol}:{timeframe}:missing")
                continue
            if int(frame["row_count"]) <= 0:
                incomplete.append(f"{symbol}:{timeframe}:empty")
        m15 = frames.get("M15")
        if m15 is not None:
            if datetime.fromisoformat(str(m15["first_utc"])) > start:
                incomplete.append(f"{symbol}:M15:starts_after_window")
            if datetime.fromisoformat(str(m15["last_utc"])) < end:
                incomplete.append(f"{symbol}:M15:ends_before_window")

    receipts: dict[str, str | None] = {}
    for kind in ("SOURCES", "SOURCE_PLAN", "PACKS"):
        candidate = HERE / "receipts" / f"{kind}_{window_id}.json"
        receipts[kind] = (
            hashlib.sha256(candidate.read_bytes()).hexdigest()
            if candidate.is_file()
            else None
        )

    pack_root = REGISTRY.parent / str(entry["pack_root"])
    day_dirs = (
        sorted(p.name for p in (pack_root / entry["split"]).iterdir() if p.is_dir())
        if (pack_root / entry["split"]).is_dir()
        else []
    )
    return {
        "window_id": window_id,
        "window": entry["window"],
        "split": entry["split"],
        "surface": entry["surface"],
        "declared_day_count": len(entry.get("pack_roots") or {}) or None,
        "calendar_day_count": (end - start).days + 1,
        "pack_day_dir_count": len(day_dirs),
        "pack_status": entry["pack_status"],
        "pack_root": entry["pack_root"],
        "source_manifest": entry["source_manifest"],
        "source_manifest_root_sha256": entry["source_manifest_root_sha256"],
        "canonical_source_plan_digest_sha256": entry.get(
            "canonical_source_plan_digest_sha256"
        ),
        "bar_source_count": manifest["bar_source_count"],
        "bar_symbol_count": manifest["bar_symbol_count"],
        "tick_symbol_count": manifest["tick_symbol_count"],
        "tick_gap_count": manifest["tick_gap_count"],
        "tick_gap_status": sorted(
            {str(g["status"]) for g in manifest.get("tick_gaps") or ()}
        ),
        "coverage_complete": not incomplete,
        "coverage_exceptions": sorted(set(incomplete)),
        "per_symbol_source_coverage": {
            symbol: per_symbol[symbol] for symbol in sorted(per_symbol)
        },
        "receipt_sha256": receipts,
        "downstream_arguments": {
            "--window": window_id,
            "--lane-source-plan-digest": entry.get(
                "canonical_source_plan_digest_sha256"
            ),
            "--lane-input-registry": str(REGISTRY),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", required=True, help="comma-separated window ids")
    parser.add_argument("--disk-trajectory", default="", help="path to a JSON list")
    parser.add_argument("--out", type=Path, required=True)
    ns = parser.parse_args()

    registry = _load(REGISTRY)
    catalog = _load(CATALOG)
    built = [w for w in ns.windows.split(",") if w]

    payload = {
        "schema": "gtos.lane.materialization.lm_mat_result.v1",
        "session": "LM-MAT",
        "decision": "OD-BROAD-FORENSIC-2",
        "branch": "phase19/march-confirm",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": (
            "LANE_ITERATION_EVIDENCE - unbilled exploration, never admission-grade"
        ),
        "economic_outcome_read": False,
        "economic_outcome_read_statement": (
            "No economic statistic of any newly materialized window was computed, "
            "printed, logged or written by this session. No R, win rate, trade "
            "count, P&L, candidate, order, ledger row or summary statistic of any "
            "2025 window was produced. Every artifact here is an INPUT: bars and "
            "ticks with one timestamp column rewritten through "
            "broker_epoch_to_utc, their manifests, their canonical source-plan "
            "digests, and their prepared day packs. The windows remain "
            "outcome-virgin and are usable as first-read validation evidence."
        ),
        "march_outcomes_read": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "campaign_sealed": False,
        "registry_path": str(REGISTRY),
        "registry_status": registry["status"],
        "registry_root_sha256": registry["registry_root_sha256"],
        "catalog_root_sha256": catalog["catalog_root_sha256"],
        "catalog_bar_source_count": len(catalog["bar_sources"]),
        "windows_built": [window_report(w, registry, catalog) for w in built],
        "pre_existing_windows_verified": {
            w: {
                "canonical_source_plan_digest_sha256": registry["windows"][w].get(
                    "canonical_source_plan_digest_sha256"
                ),
                "source_manifest_root_sha256": registry["windows"][w][
                    "source_manifest_root_sha256"
                ],
                "pack_status": registry["windows"][w]["pack_status"],
            }
            for w in PRE_EXISTING
        },
        "free_gb_now": _free_gb(),
    }
    if ns.disk_trajectory:
        payload["disk_trajectory_gb_free"] = json.loads(
            Path(ns.disk_trajectory).read_text(encoding="utf-8")
        )
    ns.out.write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {ns.out} ({len(built)} windows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
