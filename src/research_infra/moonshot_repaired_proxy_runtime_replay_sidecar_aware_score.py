"""Score represented runtime replay comparison rows with sidecar-aware context."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


RUNTIME_REPLAY_SIDECAR_AWARE_SCORE_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_sidecar_aware_score.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"


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
    output["runtime_replay_sidecar_aware_score_surface"] = RUNTIME_REPLAY_SIDECAR_AWARE_SCORE_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def round_or_none(value: float | None, places: int = 10) -> float | None:
    return round(value, places) if value is not None else None


def scope_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("registry_family")),
    )


def signal_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("source_component")),
    )


def role_base_score(role: str) -> float:
    if role in {
        "DEFAULT_OFF_REPLAY_SIGNAL_COMPARISON_INPUT",
        "AVOID_REDESIGN_REPLAY_SIGNAL_COMPARISON_INPUT",
    }:
        return 1.0
    if role == "REPRESENTED_REPLAY_CONTEXT_COMPARISON_INPUT":
        return 0.5
    return 0.0


def scope_multiplier(scope_class: str) -> float:
    if scope_class in {
        "SCOPE_COMPARISON_DEFAULT_OFF_SIGNAL_ONLY",
        "SCOPE_COMPARISON_AVOID_REDESIGN_SIGNAL_ONLY",
    }:
        return 1.0
    if scope_class == "SCOPE_COMPARISON_MIXED_DEFAULT_OFF_AND_AVOID_SIGNALS":
        return 0.85
    if scope_class == "SCOPE_COMPARISON_REPRESENTED_CONTEXT_ONLY":
        return 0.55
    return 0.0


def sidecar_density(packet_count: int, sidecar_count: int) -> float:
    denominator = packet_count + sidecar_count
    if denominator <= 0:
        return 0.0
    return sidecar_count / denominator


def score_class(score: float, sidecar_count: int) -> str:
    if score >= 0.75 and sidecar_count == 0:
        return "COMPARISON_SCORE_HIGH_CLEAR"
    if score >= 0.55:
        return "COMPARISON_SCORE_USABLE_WITH_CONTEXT"
    if score > 0.0:
        return "COMPARISON_SCORE_CONTEXT_ONLY_OR_SIDECAR_DAMPED"
    return "COMPARISON_SCORE_REVIEW_ONLY"


def packet_score_rows(
    packet_rows: list[dict[str, Any]], scope_rows: list[dict[str, Any]], signal_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    scope_index = {scope_key(row): row for row in scope_rows}
    signal_index = {signal_key(row): row for row in signal_rows}
    output: list[dict[str, Any]] = []
    for row in packet_rows:
        scope = scope_index.get(scope_key(row), {})
        signal = signal_index.get(signal_key(row), {})
        packet_count = int(scope.get("comparison_packet_rows") or 0)
        sidecar_count = int(scope.get("review_sidecar_rows") or 0)
        density = sidecar_density(packet_count, sidecar_count)
        role = normalized(row.get("comparison_packet_role"))
        base = role_base_score(role)
        multiplier = scope_multiplier(normalized(scope.get("scope_comparison_class")))
        score = base * multiplier * (1.0 - min(0.5, density))
        output.append(
            boundary_row(
                {
                    "packet_score_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SIDECAR-SCORE-PACKET-{len(output) + 1:06d}"
                    ),
                    "input_comparison_packet_row_id": row.get("comparison_packet_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "comparison_packet_role": role,
                    "scope_comparison_class": scope.get("scope_comparison_class"),
                    "signal_count_balance": signal.get("signal_count_balance"),
                    "scope_comparison_packet_rows": packet_count,
                    "scope_review_sidecar_rows": sidecar_count,
                    "scope_sidecar_density": round(density, 10),
                    "comparison_role_base_score": base,
                    "scope_class_multiplier": multiplier,
                    "sidecar_aware_comparison_score": round(score, 10),
                    "sidecar_aware_score_class": score_class(score, sidecar_count),
                    "score_usage": "BRANCH_LOCAL_COMPARISON_PRIORITY_ONLY",
                    "packet_score_status": "SIDECAR_AWARE_PACKET_SCORE_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def scope_score_rows(packet_scores: list[dict[str, Any]], scope_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in packet_scores:
        grouped[scope_key(row)].append(row)
    output: list[dict[str, Any]] = []
    for scope in scope_rows:
        rows = grouped.get(scope_key(scope), [])
        scores = [float(row.get("sidecar_aware_comparison_score") or 0.0) for row in rows]
        output.append(
            boundary_row(
                {
                    "scope_score_row_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SIDECAR-SCORE-SCOPE-{len(output) + 1:05d}",
                    "symbol": scope.get("symbol"),
                    "route_session": scope.get("route_session"),
                    "horizon_id": scope.get("horizon_id"),
                    "registry_family": scope.get("registry_family"),
                    "scope_comparison_class": scope.get("scope_comparison_class"),
                    "comparison_packet_rows": int(scope.get("comparison_packet_rows") or 0),
                    "review_sidecar_rows": int(scope.get("review_sidecar_rows") or 0),
                    "packet_score_rows": len(rows),
                    "sidecar_aware_score_mean": round_or_none(mean(scores) if scores else None),
                    "sidecar_aware_score_min": min(scores) if scores else None,
                    "sidecar_aware_score_max": max(scores) if scores else None,
                    "scope_score_next_step": (
                        "SCORE_REPRESENTED_PACKET_ROWS_WITH_REVIEW_CONTEXT"
                        if rows
                        else "REVIEW_SIDECAR_ONLY_SCOPE_BEFORE_PACKET_SCORING"
                    ),
                    "scope_score_status": "SIDECAR_AWARE_SCOPE_SCORE_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def sidecar_score_impact_rows(
    attachment_rows: list[dict[str, Any]], scope_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    scope_index = {scope_key(row): row for row in scope_rows}
    output: list[dict[str, Any]] = []
    for row in attachment_rows:
        scope = scope_index.get(scope_key(row), {})
        sidecar_count = int(scope.get("review_sidecar_rows") or 0)
        packet_count = int(scope.get("comparison_packet_rows") or 0)
        density = sidecar_density(packet_count, sidecar_count)
        output.append(
            boundary_row(
                {
                    "sidecar_score_impact_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SIDECAR-SCORE-IMPACT-{len(output) + 1:06d}"
                    ),
                    "input_sidecar_attachment_row_id": row.get("sidecar_attachment_row_id"),
                    "input_comparison_review_sidecar_row_id": row.get("input_comparison_review_sidecar_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "review_sidecar_family": row.get("review_sidecar_family"),
                    "sidecar_attachment_class": row.get("sidecar_attachment_class"),
                    "scope_comparison_class": scope.get("scope_comparison_class"),
                    "scope_sidecar_density": round(density, 10),
                    "sidecar_score_impact_class": (
                        "SIDECAR_DAMPS_REPRESENTED_SCOPE_SCORE"
                        if row.get("sidecar_attachment_class") == "SIDECAR_ATTACHED_TO_REPRESENTED_SCOPE"
                        else "SIDECAR_HELD_FOR_SCOPE_REVIEW"
                    ),
                    "sidecar_score_impact_status": "SIDECAR_SCORE_IMPACT_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def system_score_rows(
    packet_scores: list[dict[str, Any]], scope_scores: list[dict[str, Any]], impact_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    score_classes = Counter(normalized(row.get("sidecar_aware_score_class")) for row in packet_scores)
    scope_classes = Counter(normalized(row.get("scope_comparison_class")) for row in scope_scores)
    impact_classes = Counter(normalized(row.get("sidecar_score_impact_class")) for row in impact_rows)
    scores = [float(row.get("sidecar_aware_comparison_score") or 0.0) for row in packet_scores]
    return [
        boundary_row(
            {
                "system_score_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SIDECAR-SCORE-SYSTEM-0001",
                "packet_score_rows": len(packet_scores),
                "scope_score_rows": len(scope_scores),
                "sidecar_score_impact_rows": len(impact_rows),
                "sidecar_aware_score_mean": round_or_none(mean(scores) if scores else None),
                "sidecar_aware_score_class_counts": dict(sorted(score_classes.items())),
                "scope_comparison_class_counts": dict(sorted(scope_classes.items())),
                "sidecar_score_impact_class_counts": dict(sorted(impact_classes.items())),
                "system_score": (
                    "Use sidecar-aware scores only as branch-local comparison priority, with review sidecars "
                    "preserved as dampers or sidecar-only review requirements."
                ),
                "system_score_status": "SIDECAR_AWARE_SYSTEM_SCORE_MATERIALIZED_BRANCH_LOCAL",
            }
        )
    ]


def sidecar_score_bucket_rows(
    packet_scores: list[dict[str, Any]],
    scope_scores: list[dict[str, Any]],
    impact_rows: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("sidecar_aware_score_class", packet_scores, "sidecar_aware_score_class"),
        ("packet_score_status", packet_scores, "packet_score_status"),
        ("scope_comparison_class", scope_scores, "scope_comparison_class"),
        ("scope_score_next_step", scope_scores, "scope_score_next_step"),
        ("sidecar_score_impact_class", impact_rows, "sidecar_score_impact_class"),
        ("system_score_status", system_rows, "system_score_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "sidecar_score_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SIDECAR-SCORE-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
