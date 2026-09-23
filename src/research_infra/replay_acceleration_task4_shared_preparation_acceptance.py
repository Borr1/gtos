#!/usr/bin/env python3
"""Verify Task 4 exact shared closed-timeframe preparation.

The verifier reuses the accepted Task 3 semantic comparator, but independently
checks the new D1/H4/H1 cache accounting.  M15 remains outside the cache.  The
Jan 1 no-event day must perform no market-state builds; the 96-window Jan 2
dense day must account for every one of the 2,304 symbol windows exactly.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research_infra import (
    replay_acceleration_task2_semantic_acceptance as semantic,
)
from src.research_infra import (
    replay_acceleration_task3_exact_cache_acceptance as task3,
)


SCHEMA = "gtos.replay_acceleration.task4_shared_preparation_acceptance.v1"
STATUS = "TASK4_SHARED_EXACT_PREPARATION_SEMANTIC_AND_PERFORMANCE_VERIFIED"
TASK_NAME = "Replay-Acceleration Task 4"
MARKET_STATE_CACHE_KEY = "shared_market_state_cache"
DENSE_SYMBOL_WINDOWS = 24 * 96
EXPECTED_MARKET_STATE_CACHE = {
    "d1_hits": 2256,
    "d1_misses": 48,
    "d1_builds": 48,
    "d1_evictions": 24,
    "d1_entries": 24,
    "h4_hits": 2136,
    "h4_misses": 168,
    "h4_builds": 168,
    "h4_evictions": 144,
    "h4_entries": 24,
    "h1_hits": 1721,
    "h1_misses": 583,
    "h1_builds": 583,
    "h1_evictions": 559,
    "h1_entries": 24,
}


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise task3.Task3ExactCacheRejected(code)


def validate_task4_cache_audits(
    summary: Mapping[str, Any],
    *,
    expected_market_state_cache: Mapping[str, int] = (
        EXPECTED_MARKET_STATE_CACHE
    ),
    expected_counts_source: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate base Task 3 cache bindings plus exact Task 4 hit accounting."""

    progress = summary.get("progress_rows")
    _require(
        isinstance(progress, list) and len(progress) == 2,
        "task4_cache_progress_invalid",
    )
    stripped_summary = copy.deepcopy(dict(summary))
    stripped_progress = stripped_summary.get("progress_rows")
    _require(isinstance(stripped_progress, list), "task4_cache_progress_invalid")
    original_audits: list[dict[str, Any]] = []
    for index, (original_row, stripped_row) in enumerate(
        zip(progress, stripped_progress)
    ):
        _require(
            isinstance(original_row, Mapping)
            and isinstance(stripped_row, Mapping),
            "task4_cache_progress_invalid",
        )
        original_audit = original_row.get("campaign_exact_cache")
        stripped_audit = stripped_row.get("campaign_exact_cache")
        _require(
            isinstance(original_audit, Mapping)
            and isinstance(stripped_audit, dict),
            "task4_cache_audit_invalid",
        )
        original_audits.append(copy.deepcopy(dict(original_audit)))
        market_state = stripped_audit.pop(MARKET_STATE_CACHE_KEY, None)
        if index == 0:
            _require(
                market_state is None
                and set(original_audit) == task3._CACHE_KEYS,
                "task4_no_event_cache_audit_invalid",
            )
        else:
            _require(
                isinstance(market_state, Mapping)
                and set(original_audit)
                == (task3._CACHE_KEYS | {MARKET_STATE_CACHE_KEY})
                and dict(market_state) == dict(expected_market_state_cache),
                "task4_dense_cache_audit_invalid",
            )

    base = task3.validate_cache_audits(stripped_summary)
    dense = original_audits[1][MARKET_STATE_CACHE_KEY]
    per_timeframe = {}
    for timeframe in ("d1", "h4", "h1"):
        hits = int(dense[f"{timeframe}_hits"])
        misses = int(dense[f"{timeframe}_misses"])
        builds = int(dense[f"{timeframe}_builds"])
        evictions = int(dense[f"{timeframe}_evictions"])
        entries = int(dense[f"{timeframe}_entries"])
        _require(
            hits + misses == DENSE_SYMBOL_WINDOWS
            and builds == misses
            and evictions == builds - entries,
            f"task4_{timeframe}_cache_reconciliation_invalid",
        )
        per_timeframe[timeframe.upper()] = {
            "symbol_window_requests": hits + misses,
            "exact_cache_hits": hits,
            "exact_state_builds": builds,
            "avoided_rebuild_ratio": hits / (hits + misses),
        }
    return {
        **base,
        "status": "TASK4_SHARED_MARKET_STATE_CACHE_BOUNDED_AND_EXACT",
        "daily_audits": original_audits,
        "audit_root_sha256": semantic.canonical_sha256(original_audits),
        "m15_cache_enabled": False,
        "dense_symbol_window_count": DENSE_SYMBOL_WINDOWS,
        "closed_timeframe_request_count": DENSE_SYMBOL_WINDOWS * 3,
        "closed_timeframe_build_count": sum(
            row["exact_state_builds"] for row in per_timeframe.values()
        ),
        "closed_timeframe_cache_hit_count": sum(
            row["exact_cache_hits"] for row in per_timeframe.values()
        ),
        "per_timeframe": per_timeframe,
        "expected_counts_source": copy.deepcopy(expected_counts_source),
    }


def derive_expected_market_state_cache(
    reference_root: Path,
) -> tuple[dict[str, int], dict[str, Any]]:
    """Recompute cache requests and endpoint changes from reference rows."""

    decision_path = semantic._role_path(Path(reference_root), "decision")
    digest = hashlib.sha256()
    last_identity: dict[tuple[str, str], tuple[Any, ...]] = {}
    requests: dict[str, int] = defaultdict(int)
    builds: dict[str, int] = defaultdict(int)
    symbols: dict[str, set[str]] = defaultdict(set)
    successful_rows = 0
    with decision_path.open("rb") as handle:
        for raw in handle:
            digest.update(raw)
            row = json.loads(raw)
            if (
                row.get("raw_data_status")
                != "live_equivalent_raw_data_built_and_mso_computed"
            ):
                continue
            successful_rows += 1
            symbol = str(row.get("symbol") or "")
            endpoints = row.get(
                "decision_max_source_time_utc_by_timeframe"
            )
            hashes = row.get("source_hashes_by_timeframe")
            paths = row.get("source_paths_by_timeframe")
            counts = row.get("decision_rows_used_by_timeframe")
            _require(
                symbol
                and isinstance(endpoints, Mapping)
                and isinstance(hashes, Mapping)
                and isinstance(paths, Mapping)
                and isinstance(counts, Mapping),
                "task4_reference_source_identity_missing",
            )
            for timeframe in ("D1", "H4", "H1"):
                requests[timeframe] += 1
                symbols[timeframe].add(symbol)
                identity = (
                    paths.get(timeframe),
                    hashes.get(timeframe),
                    counts.get(timeframe),
                    endpoints.get(timeframe),
                )
                key = (symbol, timeframe)
                if last_identity.get(key) != identity:
                    builds[timeframe] += 1
                    last_identity[key] = identity
    _require(
        successful_rows == DENSE_SYMBOL_WINDOWS,
        "task4_reference_dense_symbol_window_count_invalid",
    )
    expected: dict[str, int] = {}
    for timeframe in ("D1", "H4", "H1"):
        prefix = timeframe.lower()
        entry_count = len(symbols[timeframe])
        expected[f"{prefix}_hits"] = requests[timeframe] - builds[timeframe]
        expected[f"{prefix}_misses"] = builds[timeframe]
        expected[f"{prefix}_builds"] = builds[timeframe]
        expected[f"{prefix}_evictions"] = builds[timeframe] - entry_count
        expected[f"{prefix}_entries"] = entry_count
    _require(
        expected == EXPECTED_MARKET_STATE_CACHE,
        "task4_reference_cache_projection_changed",
    )
    return expected, {
        "schema": "gtos.replay_acceleration.task4_cache_count_source.v1",
        "role": "decision",
        "path": str(decision_path.resolve()),
        "sha256": digest.hexdigest(),
        "successful_symbol_window_rows": successful_rows,
        "causal_or_economic_fields_read": False,
        "fields_read": [
            "raw_data_status",
            "symbol",
            "decision_max_source_time_utc_by_timeframe",
            "source_hashes_by_timeframe",
            "source_paths_by_timeframe",
            "decision_rows_used_by_timeframe",
        ],
    }


def run_acceptance(reference_root: Path, accelerated_root: Path) -> dict[str, Any]:
    expected, source = derive_expected_market_state_cache(reference_root)

    def validate(summary: Mapping[str, Any]) -> dict[str, Any]:
        return validate_task4_cache_audits(
            summary,
            expected_market_state_cache=expected,
            expected_counts_source=source,
        )

    return task3.run_acceptance(
        reference_root,
        accelerated_root,
        cache_validator=validate,
        reference_cache_validator=task3.validate_cache_audits,
        receipt_schema=SCHEMA,
        receipt_status=STATUS,
        task_name=TASK_NAME,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--accelerated-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    receipt = run_acceptance(args.reference_root, args.accelerated_root)
    task3.atomic_write_json(args.output, receipt)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
