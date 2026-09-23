"""Branch-local implementation candidates from expanded-market priority rows."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_IMPL_CANDIDATES = "src/research_infra/moonshot_expanded_market_impl_candidates.py"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
CANDIDATE_CLASS = "implementation-priority-positive-alternate-source-repair"

EXACT_SCOPE_FIELDS = (
    "expanded_market_implementation_priority_row_id",
    "symbol_family",
    "symbol",
    "source_symbol",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
    "source_path",
    "source_file_sha256",
    "source_component",
    "source_record_selector",
    "entry_reference",
    "entry_reference_time",
)

NUMERIC_SCOPE_FIELDS = (
    "proxy_entry_price",
    "proxy_denominator_price",
    "proxy_target_price",
    "proxy_stop_price",
)


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "artifact_scope": "branch_local_research",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["expanded_market_impl_candidates_surface"] = EXPANDED_MARKET_IMPL_CANDIDATES
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def digest(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    return [value for value in (as_float(row.get(field)) for row in rows) if value is not None]


def implementation_candidate_input(row: dict[str, Any]) -> bool:
    return row.get("implementation_priority_class") == CANDIDATE_CLASS


def candidate_scope(row: dict[str, Any]) -> dict[str, Any]:
    exact = {field: row.get(field) for field in EXACT_SCOPE_FIELDS}
    numeric_exact = {field: row.get(field) for field in NUMERIC_SCOPE_FIELDS}
    thresholds = {
        "alternate_source_proxy_cost_adjusted_simulated_r": row.get(
            "alternate_source_proxy_cost_adjusted_simulated_r"
        ),
        "implementation_priority_score": row.get("implementation_priority_score"),
    }
    return {
        "scope_type": "row_level_positive_alternate_source_repair",
        "exact": exact,
        "numeric_exact": numeric_exact,
        "minimum_thresholds": thresholds,
    }


def matches_candidate_scope(candidate: dict[str, Any], row: dict[str, Any]) -> bool:
    scope = candidate.get("branch_local_candidate_scope") or {}
    for field, expected in (scope.get("exact") or {}).items():
        if normalized(row.get(field)) != normalized(expected):
            return False
    for field, expected in (scope.get("numeric_exact") or {}).items():
        expected_float = as_float(expected)
        actual_float = as_float(row.get(field))
        if expected_float is None and actual_float is None:
            continue
        if expected_float is None or actual_float is None:
            return False
        if abs(actual_float - expected_float) > 1e-9:
            return False
    for field, threshold in (scope.get("minimum_thresholds") or {}).items():
        threshold_float = as_float(threshold)
        actual_float = as_float(row.get(field))
        if threshold_float is None or actual_float is None:
            return False
        if actual_float + 1e-12 < threshold_float:
            return False
    return True


def candidate_code_expression(scope_sha256: str, row: dict[str, Any]) -> str:
    return (
        f"scope_sha256={scope_sha256}; "
        f"symbol_family={row.get('symbol_family')}; "
        f"timeframe={row.get('market_timeframe')}; "
        f"session={row.get('route_session')}; "
        f"horizon={row.get('horizon_id')}; "
        f"side={row.get('side')}; "
        f"source_sha256={row.get('source_file_sha256')}; "
        f"alternate_proxy_r_min={row.get('alternate_source_proxy_cost_adjusted_simulated_r')}"
    )


def implementation_candidate_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    scope = candidate_scope(row)
    scope_sha = digest(scope)
    payload = dict(row)
    payload.update(
        {
            "expanded_market_impl_candidate_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-IMPL-CANDIDATE-{sequence:07d}"
            ),
            "input_implementation_priority_row_id": row.get(
                "expanded_market_implementation_priority_row_id"
            ),
            "candidate_family": "expanded_market_positive_alternate_source_repair",
            "candidate_action": "FOLLOW_POSITIVE_ALTERNATE_SOURCE_REPAIR_IN_BRANCH_LOCAL_REPLAY",
            "candidate_status": "BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_READY",
            "branch_local_candidate_scope": scope,
            "branch_local_candidate_scope_sha256": scope_sha,
            "candidate_function_name": f"score_expanded_market_alt_source_repair_{scope_sha[:16]}",
            "branch_local_code_expression": candidate_code_expression(scope_sha, row),
            "candidate_source_path": row.get("source_path"),
            "candidate_source_file_sha256": row.get("source_file_sha256"),
            "candidate_cost_adjusted_simulated_r": row.get(
                "alternate_source_proxy_cost_adjusted_simulated_r"
            ),
            "candidate_stress_simulated_r": row.get("observed_deconcentrated_stress_simulated_r"),
            "candidate_effective_n": row.get("deconcentrated_effective_n"),
            "follow_inverse_default_off_avoid_class": "follow",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_CANDIDATE"
            ),
        }
    )
    return boundary_row(payload)


def evidence_preservation_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    payload = dict(row)
    row_class = normalized(row.get("implementation_priority_class"))
    payload.update(
        {
            "expanded_market_impl_candidate_evidence_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-IMPL-EVIDENCE-{sequence:07d}"
            ),
            "input_implementation_priority_row_id": row.get(
                "expanded_market_implementation_priority_row_id"
            ),
            "evidence_preservation_class": row_class,
            "evidence_status": "PRESERVED_NONCANDIDATE_IMPLEMENTATION_PRIORITY_ROW",
            "candidate_status": "NOT_A_NEW_IMPLEMENTATION_CANDIDATE",
            "follow_inverse_default_off_avoid_class": row.get("follow_inverse_default_off_avoid_class"),
            "keep_kill_redesign_implement_decision": row.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )
    return boundary_row(payload)


def self_test_row(candidate: dict[str, Any], source_row: dict[str, Any], sequence: int) -> dict[str, Any]:
    side_mismatch = dict(source_row)
    side_mismatch["side"] = "SHORT" if source_row.get("side") == "LONG" else "LONG"
    hash_mismatch = dict(source_row)
    hash_mismatch["source_file_sha256"] = f"{source_row.get('source_file_sha256')}:mismatch"
    threshold_mismatch = dict(source_row)
    threshold = as_float(source_row.get("alternate_source_proxy_cost_adjusted_simulated_r"))
    if threshold is not None:
        threshold_mismatch["alternate_source_proxy_cost_adjusted_simulated_r"] = threshold - 0.000001

    positive_match = matches_candidate_scope(candidate, source_row)
    side_rejected = not matches_candidate_scope(candidate, side_mismatch)
    hash_rejected = not matches_candidate_scope(candidate, hash_mismatch)
    threshold_rejected = not matches_candidate_scope(candidate, threshold_mismatch)
    passed = positive_match and side_rejected and hash_rejected and threshold_rejected
    return boundary_row(
        {
            "expanded_market_impl_candidate_self_test_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-IMPL-SELFTEST-{sequence:07d}"
            ),
            "input_impl_candidate_row_id": candidate.get("expanded_market_impl_candidate_row_id"),
            "input_implementation_priority_row_id": candidate.get("input_implementation_priority_row_id"),
            "branch_local_candidate_scope_sha256": candidate.get("branch_local_candidate_scope_sha256"),
            "positive_scope_match": positive_match,
            "negative_side_mismatch_rejected": side_rejected,
            "negative_source_hash_mismatch_rejected": hash_rejected,
            "negative_threshold_underflow_rejected": threshold_rejected,
            "self_test_status": "EXPANDED_MARKET_IMPL_CANDIDATE_SELF_TEST_PASS"
            if passed
            else "EXPANDED_MARKET_IMPL_CANDIDATE_SELF_TEST_FAIL",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_CANDIDATE_SELF_TEST"
                if passed
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_CANDIDATE_SELF_TEST"
            ),
        }
    )


def issue_rows(candidates: list[dict[str, Any]], self_tests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in candidates:
        if not row.get("source_path") or not row.get("source_file_sha256"):
            issues.append(
                boundary_row(
                    {
                        "expanded_market_impl_candidate_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-IMPL-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_impl_candidate_row_id": row.get("expanded_market_impl_candidate_row_id"),
                        "issue_status": "MISSING_SOURCE_PATH_OR_HASH",
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_CANDIDATE"
                        ),
                    }
                )
            )
        if as_float(row.get("candidate_cost_adjusted_simulated_r")) is None:
            issues.append(
                boundary_row(
                    {
                        "expanded_market_impl_candidate_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-IMPL-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_impl_candidate_row_id": row.get("expanded_market_impl_candidate_row_id"),
                        "issue_status": "MISSING_CANDIDATE_SIMULATED_R",
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_CANDIDATE"
                        ),
                    }
                )
            )
    for row in self_tests:
        if row.get("self_test_status") != "EXPANDED_MARKET_IMPL_CANDIDATE_SELF_TEST_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_impl_candidate_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-IMPL-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_impl_candidate_row_id": row.get("input_impl_candidate_row_id"),
                        "issue_status": row.get("self_test_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_CANDIDATE"
                        ),
                    }
                )
            )
    return issues


def implementation_candidate_rows(
    priority_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    self_tests: list[dict[str, Any]] = []
    for row in priority_rows:
        if implementation_candidate_input(row):
            candidate = implementation_candidate_row(row, len(candidates) + 1)
            candidates.append(candidate)
            self_tests.append(self_test_row(candidate, row, len(self_tests) + 1))
        else:
            evidence.append(evidence_preservation_row(row, len(evidence) + 1))
    issues = issue_rows(candidates, self_tests)
    return candidates, evidence, self_tests, issues


def aggregate_key(row: dict[str, Any], row_kind: str) -> tuple[str, ...]:
    row_class = (
        normalized(row.get("implementation_priority_class"))
        if row_kind == "candidate"
        else normalized(row.get("evidence_preservation_class"))
    )
    tier = normalized(row.get("implementation_priority_tier"))
    return (
        row_kind,
        row_class,
        tier,
        normalized(row.get("symbol_family")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
    )


def empty_bucket() -> dict[str, Any]:
    return {
        "row_count": 0,
        "candidate_rows": 0,
        "evidence_rows": 0,
        "priority_sum": 0.0,
        "priority_count": 0,
        "alternate_sum": 0.0,
        "alternate_count": 0,
        "observed_cost_sum": 0.0,
        "observed_cost_count": 0,
        "effective_n_sum": 0,
        "deconcentrated_effective_n_sum": 0.0,
        "win_count": 0,
        "loss_count": 0,
        "zero_count": 0,
        "target_first_count": 0,
        "stop_first_count": 0,
        "neither_count": 0,
        "ambiguous_count": 0,
        "source_paths": set(),
        "decisions": Counter(),
    }


def update_bucket(bucket: dict[str, Any], row: dict[str, Any], row_kind: str) -> None:
    bucket["row_count"] += 1
    if row_kind == "candidate":
        bucket["candidate_rows"] += 1
    else:
        bucket["evidence_rows"] += 1
    priority = as_float(row.get("implementation_priority_score"))
    if priority is not None:
        bucket["priority_sum"] += priority
        bucket["priority_count"] += 1
    alternate = as_float(row.get("alternate_source_proxy_cost_adjusted_simulated_r"))
    if alternate is not None:
        bucket["alternate_sum"] += alternate
        bucket["alternate_count"] += 1
    observed = as_float(row.get("observed_cost_adjusted_simulated_r"))
    if observed is not None:
        bucket["observed_cost_sum"] += observed
        bucket["observed_cost_count"] += 1
    bucket["effective_n_sum"] += int(row.get("effective_n") or 0)
    bucket["deconcentrated_effective_n_sum"] += float(row.get("deconcentrated_effective_n") or 0.0)
    for field in (
        "win_count",
        "loss_count",
        "zero_count",
        "target_first_count",
        "stop_first_count",
        "neither_count",
        "ambiguous_count",
    ):
        bucket[field] += int(row.get(field) or 0)
    bucket["source_paths"].add(str(row.get("source_path") or ""))
    bucket["decisions"][row.get("keep_kill_redesign_implement_decision")] += 1


def aggregate_rows_from_buckets(buckets: dict[tuple[str, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(buckets):
        bucket = buckets[key]
        rows.append(
            boundary_row(
                {
                    "expanded_market_impl_candidate_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-IMPL-AGG-{len(rows) + 1:07d}"
                    ),
                    "row_kind": key[0],
                    "implementation_priority_class": key[1],
                    "implementation_priority_tier": key[2],
                    "symbol_family": key[3],
                    "market_timeframe": key[4],
                    "route_session": key[5],
                    "horizon_id": key[6],
                    "side": key[7],
                    "row_count": bucket["row_count"],
                    "candidate_rows": bucket["candidate_rows"],
                    "evidence_rows": bucket["evidence_rows"],
                    "average_implementation_priority_score": rounded(
                        bucket["priority_sum"] / bucket["priority_count"]
                        if bucket["priority_count"]
                        else None
                    ),
                    "average_alternate_source_proxy_cost_adjusted_simulated_r": rounded(
                        bucket["alternate_sum"] / bucket["alternate_count"]
                        if bucket["alternate_count"]
                        else None
                    ),
                    "average_observed_cost_adjusted_simulated_r": rounded(
                        bucket["observed_cost_sum"] / bucket["observed_cost_count"]
                        if bucket["observed_cost_count"]
                        else None
                    ),
                    "effective_n_sum": bucket["effective_n_sum"],
                    "deconcentrated_effective_n_sum": rounded(bucket["deconcentrated_effective_n_sum"]),
                    "win_count": bucket["win_count"],
                    "loss_count": bucket["loss_count"],
                    "zero_count": bucket["zero_count"],
                    "target_first_count": bucket["target_first_count"],
                    "stop_first_count": bucket["stop_first_count"],
                    "neither_count": bucket["neither_count"],
                    "ambiguous_count": bucket["ambiguous_count"],
                    "source_path_count": len(bucket["source_paths"]),
                    "decision_counts": dict(sorted(bucket["decisions"].items())),
                    "keep_kill_redesign_implement_decision": bucket["decisions"].most_common(1)[0][0],
                }
            )
        )
    return rows


def aggregate_impl_candidate_rows(
    candidates: list[dict[str, Any]], evidence: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    for row in candidates:
        update_bucket(buckets[aggregate_key(row, "candidate")], row, "candidate")
    for row in evidence:
        update_bucket(buckets[aggregate_key(row, "evidence")], row, "evidence")
    return aggregate_rows_from_buckets(buckets)


def system_impl_candidate_rows(
    candidates: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    self_tests: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "expanded_market_impl_candidate_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-IMPL-SYSTEM-0001"
                ),
                "implementation_candidate_rows": len(candidates),
                "preserved_evidence_rows": len(evidence),
                "self_test_rows": len(self_tests),
                "self_test_pass_rows": sum(
                    1
                    for row in self_tests
                    if row.get("self_test_status") == "EXPANDED_MARKET_IMPL_CANDIDATE_SELF_TEST_PASS"
                ),
                "aggregate_rows": len(aggregates),
                "issue_rows": len(issues),
                "candidate_class_counts": dict(
                    sorted(Counter(row.get("implementation_priority_class") for row in candidates).items())
                ),
                "evidence_class_counts": dict(
                    sorted(Counter(row.get("evidence_preservation_class") for row in evidence).items())
                ),
                "priority_tier_counts": dict(
                    sorted(
                        Counter(
                            [row.get("implementation_priority_tier") for row in candidates]
                            + [row.get("implementation_priority_tier") for row in evidence]
                        ).items()
                    )
                ),
                "candidate_source_path_count": len({row.get("source_path") for row in candidates}),
                "evidence_source_path_count": len({row.get("source_path") for row in evidence}),
                "symbol_family_count": len(
                    {row.get("symbol_family") for row in candidates}
                    | {row.get("symbol_family") for row in evidence}
                ),
                "metadata": metadata,
            }
        )
    ]
