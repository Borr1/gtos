#!/usr/bin/env python3
"""Atomically migrate terminal replay rows to the exact candidate-cost alias contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.v4_timewarp_simulated_live_research_loop import (  # noqa: E402
    normalize_candidate_cost_alias_fields,
)


TERMINAL_LEDGER_SUFFIXES = (
    "MISSED_OPPORTUNITY_LEDGER.jsonl",
    "ORDER_LEDGER.jsonl",
    "TRADE_LEDGER.jsonl",
)
ALLOWED_MUTATED_FIELDS = {
    "candidate_cost_alias_conflict",
    "candidate_cost_alias_status",
    "cost_r",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def numeric_or_none(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def candidate_cost_alias_mismatch(row: Mapping[str, Any]) -> bool:
    expected_cost_r = numeric_or_none(row.get("expected_cost_r"))
    cost_r = numeric_or_none(row.get("cost_r"))
    return bool(
        expected_cost_r is not None
        and cost_r is not None
        and not math.isclose(
            expected_cost_r,
            cost_r,
            rel_tol=0.0,
            abs_tol=1e-12,
        )
    )


def semantic_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in row.items()
        if key not in ALLOWED_MUTATED_FIELDS
    }


def staged_repair(path: Path) -> tuple[Path | None, dict[str, Any]]:
    """Stage one JSONL repair while preserving every unchanged line byte-for-byte."""

    if not path.exists():
        raise FileNotFoundError(path)
    staged_path = path.with_suffix(path.suffix + ".cost-alias-repair.tmp")
    staged_path.unlink(missing_ok=True)
    before_sha = hashlib.sha256()
    after_sha = hashlib.sha256()
    row_count = 0
    changed_rows = 0
    changed_samples: list[dict[str, Any]] = []

    try:
        with path.open("rb") as source, staged_path.open("wb") as target:
            for line_number, raw_line in enumerate(source, start=1):
                row_count += 1
                before_sha.update(raw_line)
                output_line = raw_line
                try:
                    row = json.loads(raw_line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
                if not isinstance(row, dict):
                    raise ValueError(f"non-object JSONL row at {path}:{line_number}")
                if candidate_cost_alias_mismatch(row):
                    before_semantic = semantic_projection(row)
                    prior_expected_cost_r = row.get("expected_cost_r")
                    prior_cost_r = row.get("cost_r")
                    normalize_candidate_cost_alias_fields(row)
                    if semantic_projection(row) != before_semantic:
                        raise AssertionError(
                            f"non-alias semantic drift at {path}:{line_number}"
                        )
                    output_line = (
                        json.dumps(row, sort_keys=True, default=str) + "\n"
                    ).encode("utf-8")
                    changed_rows += 1
                    if len(changed_samples) < 12:
                        changed_samples.append(
                            {
                                "line_number": line_number,
                                "candidate_id": row.get("candidate_id"),
                                "decision_time_utc": row.get("decision_time_utc"),
                                "symbol": row.get("symbol"),
                                "side": row.get("side"),
                                "expected_cost_r": prior_expected_cost_r,
                                "prior_cost_r": prior_cost_r,
                                "canonical_cost_r": row.get("cost_r"),
                                "miss_reason": row.get("miss_reason"),
                            }
                        )
                target.write(output_line)
                after_sha.update(output_line)
    except BaseException:
        staged_path.unlink(missing_ok=True)
        raise

    result = {
        "path": str(path),
        "row_count": row_count,
        "changed_rows": changed_rows,
        "before_sha256": before_sha.hexdigest(),
        "after_sha256": after_sha.hexdigest(),
        "unchanged_rows_byte_preserved": row_count - changed_rows,
        "changed_samples": changed_samples,
    }
    if changed_rows == 0:
        staged_path.unlink(missing_ok=True)
        return None, result
    return staged_path, result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broad-prefix", required=True)
    parser.add_argument("--expected-changes", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prefix = str(args.broad_prefix).strip()
    paths = [ROUTE / f"{prefix}_{suffix}" for suffix in TERMINAL_LEDGER_SUFFIXES]
    staged: list[tuple[Path, Path]] = []
    results: list[dict[str, Any]] = []
    try:
        for path in paths:
            staged_path, result = staged_repair(path)
            results.append(result)
            if staged_path is not None:
                staged.append((path, staged_path))
        changed_rows = sum(int(row["changed_rows"]) for row in results)
        if args.expected_changes is not None and changed_rows != args.expected_changes:
            raise ValueError(
                "terminal cost alias repair count mismatch: "
                f"expected={args.expected_changes} actual={changed_rows}"
            )
        for path, staged_path in staged:
            staged_path.replace(path)
    finally:
        for _path, staged_path in staged:
            staged_path.unlink(missing_ok=True)

    summary = {
        "schema": "gtos.final_moonshot.broad_replay.terminal_candidate_cost_alias_repair.v1",
        "generated_utc": utc_now(),
        "broad_replay_prefix": prefix,
        "status": "terminal_candidate_cost_aliases_repaired",
        "changed_rows": sum(int(row["changed_rows"]) for row in results),
        "row_count": sum(int(row["row_count"]) for row in results),
        "allowed_mutated_fields": sorted(ALLOWED_MUTATED_FIELDS),
        "behavior_fields_changed": False,
        "broker_live_authority": False,
        "final_selection_claim": False,
        "files": results,
    }
    summary_path = ROUTE / f"{prefix}_TERMINAL_CANDIDATE_COST_ALIAS_REPAIR_SUMMARY.json"
    tmp = summary_path.with_suffix(summary_path.suffix + ".tmp")
    tmp.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(summary_path)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
