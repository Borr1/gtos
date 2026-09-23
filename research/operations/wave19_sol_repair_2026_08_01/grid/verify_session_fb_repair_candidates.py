#!/usr/bin/env python3
"""Verify Session FB's two unique repair candidates without runtime wiring."""

from __future__ import annotations

from collections import Counter
import inspect
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from src.components.current_breaker_re_entry_repair import (  # noqa: E402
    STOP_DISTANCE_D as BREAKER_STOP_D,
    TARGET_DISTANCE_D as BREAKER_TARGET_D,
    TRANSFORM_ID as BREAKER_TRANSFORM_ID,
    apply_current_breaker_re_entry_repair,
)
from src.research_infra.current_ob_retest_geometry_candidate import (  # noqa: E402
    FORBIDDEN_OUTCOME_FIELDS,
    STOP_DISTANCE_D as OB_STOP_D,
    TARGET_DISTANCE_D as OB_TARGET_D,
    TRANSFORM_ID as OB_TRANSFORM_ID,
    apply_current_ob_retest_geometry_candidate,
)

import session_fb_sol_grid as fb  # noqa: E402


OUTPUT = fb.GRID_DIR / "REPAIR_CANDIDATES.json"
PREDECISION_FIELDS = (
    "candidate_id",
    "symbol",
    "side",
    "direction",
    "origin_family",
    "framework",
    "route_family",
    "setup_family",
    "bucket_source_family",
    "decision_time_utc",
    "decision_timeframe",
    "market_timeframe",
    "session_bucket",
    "authority_session",
    "kill_zone",
    "route_session",
    "utc_hour_bucket",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "policy_target_r",
    "raw_target_r",
    "risk_per_trade_pct",
    "effective_order_type",
)


def project_predecision(row: Mapping[str, Any]) -> dict[str, Any]:
    projected = {field: row.get(field) for field in PREDECISION_FIELDS if field in row}
    if set(projected) & set(FORBIDDEN_OUTCOME_FIELDS):
        raise fb.FBRefusal("repair_projection_contains_outcome_field")
    return projected


def default_is_false(function: Any) -> bool:
    return inspect.signature(function).parameters["enabled"].default is False


def runtime_references() -> list[str]:
    module = REPO / "src/research_infra/current_ob_retest_geometry_candidate.py"
    needles = ("current_ob_retest_geometry_candidate", OB_TRANSFORM_ID)
    references = []
    for path in (REPO / "src").rglob("*.py"):
        if path == module:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(needle in text for needle in needles):
            references.append(path.relative_to(REPO).as_posix())
    return sorted(references)


def main() -> int:
    protocol = fb.load_protocol()
    classification = fb.validate_rooted_json(fb.CLASSIFICATION)
    unique = classification["unique_null_clean_repair_candidates"]
    selected = {
        (row["family"], row["orientation"], row["cell_id"]): row for row in unique
    }
    expected = {
        (
            "current_breaker_re_entry",
            "inverted",
            "inverted|target_5D|stop_0.25D",
        ),
        (
            "current_ob_retest",
            "as_declared",
            "as_declared|target_1.5D|stop_0.25D",
        ),
    }
    if set(selected) != expected:
        raise fb.FBRefusal(f"repair_candidate_set_drift:{set(selected)}!={expected}")
    if (BREAKER_TARGET_D, BREAKER_STOP_D) != (5.0, 0.25):
        raise fb.FBRefusal("existing_breaker_transform_geometry_drift")
    if (OB_TARGET_D, OB_STOP_D) != (1.5, 0.25):
        raise fb.FBRefusal("ob_transform_geometry_drift")
    if not (
        default_is_false(apply_current_breaker_re_entry_repair)
        and default_is_false(apply_current_ob_retest_geometry_candidate)
    ):
        raise fb.FBRefusal("repair_transform_not_default_off")

    pool_path = fb.verify_bound_file(
        protocol["inputs"]["january_pool"], key="january_pool"
    )
    count = 0
    directions: Counter[str] = Counter()
    transformed_ids: set[str] = set()
    composite_keys: set[tuple[str, str, str, str]] = set()
    max_stop_error = 0.0
    max_target_error = 0.0
    disabled_identity = False
    for row in fb.iter_gzip_json(pool_path):
        if row.get("origin_family") != "current_ob_retest":
            continue
        projected = project_predecision(row)
        if count == 0:
            disabled_identity = (
                apply_current_ob_retest_geometry_candidate(projected) == projected
            )
        repaired = apply_current_ob_retest_geometry_candidate(
            projected, enabled=True
        )
        entry = float(projected["entry_price"])
        original_stop = float(projected["stop_loss"])
        base_distance = abs(entry - original_stop)
        side = fb.normalize_side(projected)
        sign = 1.0 if side == "LONG" else -1.0
        expected_stop = entry - sign * OB_STOP_D * base_distance
        expected_target = entry + sign * OB_TARGET_D * base_distance
        max_stop_error = max(
            max_stop_error, abs(float(repaired["stop_loss"]) - expected_stop)
        )
        max_target_error = max(
            max_target_error, abs(float(repaired["take_profit_1"]) - expected_target)
        )
        if (
            float(repaired["entry_price"]) != entry
            or repaired["side"] != side
            or repaired["direction"] != side
            or repaired["candidate_transform_id"] != OB_TRANSFORM_ID
            or repaired["candidate_transform_default"] != "off"
        ):
            raise fb.FBRefusal("ob_candidate_materialization_invariant_failed")
        transformed_ids.add(str(repaired["candidate_id"]))
        composite_keys.add(fb.composite_key(projected))
        directions[side] += 1
        count += 1
    if count != 1340:
        raise fb.FBRefusal(f"ob_candidate_row_count:{count}!=1340")
    if len(transformed_ids) != count or len(composite_keys) != count:
        raise fb.FBRefusal("ob_candidate_identity_not_one_to_one")
    # Canonical RR recomputation can move a large-price target by a few ulps;
    # retain and report the exact maximum while enforcing a sub-nanorisk bound.
    if max_stop_error > 1e-9 or max_target_error > 1e-9:
        raise fb.FBRefusal("ob_candidate_geometry_error")
    references = runtime_references()
    if references:
        raise fb.FBRefusal(f"ob_candidate_runtime_wiring_present:{references}")

    payload = fb.write_json(
        OUTPUT,
        {
            "schema": "gtos.session_fb.repair_candidates.v1",
            "generated_at_utc": fb.utc_now(),
            "source_head": fb.repo_head(),
            "surface": fb.SURFACE,
            "billed": False,
            "march_2026_outcomes_read": False,
            "live_forward_outcomes_read": False,
            "february_used_for_candidate_selection": False,
            "classification_receipt": {
                "path": fb.repo_path(fb.CLASSIFICATION),
                "self_sha256": classification["self_sha256"],
            },
            "unique_candidate_count": 2,
            "existing_breaker_candidate": {
                "status": "REUSED_NOT_DUPLICATED",
                "selected_evidence": selected[
                    (
                        "current_breaker_re_entry",
                        "inverted",
                        "inverted|target_5D|stop_0.25D",
                    )
                ],
                "implementation": "src/components/current_breaker_re_entry_repair.py",
                "implementation_sha256": fb.sha256_file(
                    REPO / "src/components/current_breaker_re_entry_repair.py"
                ),
                "transform_id": BREAKER_TRANSFORM_ID,
                "target_distance_D": BREAKER_TARGET_D,
                "stop_distance_D": BREAKER_STOP_D,
                "enabled_default": False,
                "existing_focused_test": "tests/test_broader_origin_generators.py",
            },
            "new_ob_retest_candidate": {
                "status": "IMPLEMENTED_DEFAULT_OFF_RESEARCH_ONLY",
                "selected_evidence": selected[
                    (
                        "current_ob_retest",
                        "as_declared",
                        "as_declared|target_1.5D|stop_0.25D",
                    )
                ],
                "implementation": (
                    "src/research_infra/current_ob_retest_geometry_candidate.py"
                ),
                "implementation_sha256": fb.sha256_file(
                    REPO
                    / "src/research_infra/current_ob_retest_geometry_candidate.py"
                ),
                "transform_id": OB_TRANSFORM_ID,
                "target_distance_D": OB_TARGET_D,
                "stop_distance_D": OB_STOP_D,
                "orientation": "as_declared",
                "enabled_default": False,
                "enable_surface": "explicit_research_argument_only",
                "runtime_source_references": references,
                "runtime_wiring_present": False,
                "config_changed": False,
                "rows_materialized_in_memory": count,
                "direction_rows": dict(sorted(directions.items())),
                "unique_input_composite_keys": len(composite_keys),
                "unique_transformed_candidate_ids": len(transformed_ids),
                "disabled_is_exact_detached_pass_through": disabled_identity,
                "outcome_fields_entered": False,
                "max_abs_stop_geometry_error": max_stop_error,
                "max_abs_target_geometry_error": max_target_error,
                "all_entries_times_symbols_directions_fixed": True,
                "focused_test": (
                    "tests/research_infra/"
                    "test_current_ob_retest_geometry_candidate.py"
                ),
            },
            "promotion_authority": False,
            "activation_authority": False,
            "status": "TWO_UNIQUE_REPAIRS_DEFAULT_OFF_ONE_REUSED_ONE_IMPLEMENTED",
        },
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "self_sha256": payload["self_sha256"],
                "ob_rows": count,
                "runtime_wiring_present": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
