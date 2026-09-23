"""Compare runtime replay packet rows by scope and attach review sidecars."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


RUNTIME_REPLAY_COMPARISON_SUMMARY_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_comparison_summary.py"
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
    output["runtime_replay_comparison_summary_surface"] = RUNTIME_REPLAY_COMPARISON_SUMMARY_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


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


def scope_comparison_class(role_counts: Counter[str], sidecar_count: int) -> str:
    default_count = role_counts.get("DEFAULT_OFF_REPLAY_SIGNAL_COMPARISON_INPUT", 0)
    avoid_count = role_counts.get("AVOID_REDESIGN_REPLAY_SIGNAL_COMPARISON_INPUT", 0)
    context_count = role_counts.get("REPRESENTED_REPLAY_CONTEXT_COMPARISON_INPUT", 0)
    if default_count and avoid_count:
        return "SCOPE_COMPARISON_MIXED_DEFAULT_OFF_AND_AVOID_SIGNALS"
    if default_count:
        return "SCOPE_COMPARISON_DEFAULT_OFF_SIGNAL_ONLY"
    if avoid_count:
        return "SCOPE_COMPARISON_AVOID_REDESIGN_SIGNAL_ONLY"
    if context_count:
        return "SCOPE_COMPARISON_REPRESENTED_CONTEXT_ONLY"
    if sidecar_count:
        return "SCOPE_COMPARISON_SIDECAR_ONLY_REVIEW"
    return "SCOPE_COMPARISON_EMPTY"


def scope_next_step(comparison_class: str, sidecar_count: int) -> str:
    suffix = "_WITH_REVIEW_SIDECARS" if sidecar_count else ""
    if comparison_class == "SCOPE_COMPARISON_MIXED_DEFAULT_OFF_AND_AVOID_SIGNALS":
        return "COMPARE_DEFAULT_OFF_AND_AVOID_REDESIGN_SIGNALS" + suffix
    if comparison_class == "SCOPE_COMPARISON_DEFAULT_OFF_SIGNAL_ONLY":
        return "COMPARE_DEFAULT_OFF_SIGNAL_AGAINST_CONTEXT" + suffix
    if comparison_class == "SCOPE_COMPARISON_AVOID_REDESIGN_SIGNAL_ONLY":
        return "COMPARE_AVOID_REDESIGN_SIGNAL_AGAINST_CONTEXT" + suffix
    if comparison_class == "SCOPE_COMPARISON_REPRESENTED_CONTEXT_ONLY":
        return "RETAIN_REPRESENTED_CONTEXT_FOR_PACKET_COMPARISON" + suffix
    return "REVIEW_SIDECAR_SCOPE_BEFORE_COMPARISON"


def scope_comparison_rows(
    packet_rows: list[dict[str, Any]], sidecar_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    packet_groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    sidecar_groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in packet_rows:
        packet_groups[scope_key(row)].append(row)
    for row in sidecar_rows:
        sidecar_groups[scope_key(row)].append(row)

    output: list[dict[str, Any]] = []
    for symbol, route_session, horizon_id, registry_family in sorted(set(packet_groups) | set(sidecar_groups)):
        packets = packet_groups.get((symbol, route_session, horizon_id, registry_family), [])
        sidecars = sidecar_groups.get((symbol, route_session, horizon_id, registry_family), [])
        role_counts = Counter(normalized(row.get("comparison_packet_role")) for row in packets)
        sidecar_counts = Counter(normalized(row.get("review_sidecar_family")) for row in sidecars)
        comparison_class = scope_comparison_class(role_counts, len(sidecars))
        output.append(
            boundary_row(
                {
                    "scope_comparison_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-COMPARISON-SUMMARY-SCOPE-{len(output) + 1:05d}"
                    ),
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "registry_family": registry_family,
                    "comparison_packet_rows": len(packets),
                    "review_sidecar_rows": len(sidecars),
                    "comparison_packet_role_counts": dict(sorted(role_counts.items())),
                    "review_sidecar_family_counts": dict(sorted(sidecar_counts.items())),
                    "scope_comparison_class": comparison_class,
                    "scope_comparison_next_step": scope_next_step(comparison_class, len(sidecars)),
                    "scope_comparison_status": "RUNTIME_REPLAY_SCOPE_COMPARISON_SUMMARY_MATERIALIZED",
                }
            )
        )
    return output


def signal_comparison_rows(
    packet_rows: list[dict[str, Any]], sidecar_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    packet_groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    sidecar_groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in packet_rows:
        packet_groups[signal_key(row)].append(row)
    for row in sidecar_rows:
        sidecar_groups[signal_key(row)].append(row)

    output: list[dict[str, Any]] = []
    for symbol, route_session, horizon_id, source_component in sorted(set(packet_groups) | set(sidecar_groups)):
        packets = packet_groups.get((symbol, route_session, horizon_id, source_component), [])
        sidecars = sidecar_groups.get((symbol, route_session, horizon_id, source_component), [])
        role_counts = Counter(normalized(row.get("comparison_packet_role")) for row in packets)
        default_count = role_counts.get("DEFAULT_OFF_REPLAY_SIGNAL_COMPARISON_INPUT", 0)
        avoid_count = role_counts.get("AVOID_REDESIGN_REPLAY_SIGNAL_COMPARISON_INPUT", 0)
        context_count = role_counts.get("REPRESENTED_REPLAY_CONTEXT_COMPARISON_INPUT", 0)
        if default_count > avoid_count:
            balance = "DEFAULT_OFF_REPRESENTED_COUNT_DOMINANT"
        elif avoid_count > default_count:
            balance = "AVOID_REDESIGN_REPRESENTED_COUNT_DOMINANT"
        elif default_count or avoid_count:
            balance = "DEFAULT_OFF_AND_AVOID_REPRESENTED_COUNTS_TIED"
        elif context_count:
            balance = "REPRESENTED_CONTEXT_ONLY"
        else:
            balance = "SIDECAR_ONLY"
        output.append(
            boundary_row(
                {
                    "signal_comparison_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-COMPARISON-SUMMARY-SIGNAL-{len(output) + 1:05d}"
                    ),
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "source_component": source_component,
                    "comparison_packet_rows": len(packets),
                    "review_sidecar_rows": len(sidecars),
                    "default_off_comparison_packet_rows": default_count,
                    "avoid_redesign_comparison_packet_rows": avoid_count,
                    "represented_context_comparison_packet_rows": context_count,
                    "signal_count_balance": balance,
                    "signal_comparison_status": "RUNTIME_REPLAY_SIGNAL_COMPARISON_SUMMARY_MATERIALIZED",
                }
            )
        )
    return output


def sidecar_attachment_rows(
    packet_rows: list[dict[str, Any]], sidecar_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    represented_scope_keys = {scope_key(row) for row in packet_rows}
    output: list[dict[str, Any]] = []
    for row in sidecar_rows:
        attachment = (
            "SIDECAR_ATTACHED_TO_REPRESENTED_SCOPE"
            if scope_key(row) in represented_scope_keys
            else "SIDECAR_ONLY_SCOPE_REVIEW"
        )
        output.append(
            boundary_row(
                {
                    "sidecar_attachment_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-COMPARISON-SUMMARY-SIDECAR-{len(output) + 1:06d}"
                    ),
                    "input_comparison_review_sidecar_row_id": row.get("comparison_review_sidecar_row_id"),
                    "input_advancement_decision_row_id": row.get("input_advancement_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "review_sidecar_family": row.get("review_sidecar_family"),
                    "inventory_alignment_class": row.get("inventory_alignment_class"),
                    "sidecar_attachment_class": attachment,
                    "sidecar_attachment_status": "RUNTIME_REPLAY_SIDECAR_ATTACHMENT_MATERIALIZED",
                }
            )
        )
    return output


def system_summary_rows(
    scope_rows: list[dict[str, Any]], signal_rows: list[dict[str, Any]], attachment_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    scope_classes = Counter(normalized(row.get("scope_comparison_class")) for row in scope_rows)
    signal_balances = Counter(normalized(row.get("signal_count_balance")) for row in signal_rows)
    attachment_classes = Counter(normalized(row.get("sidecar_attachment_class")) for row in attachment_rows)
    return [
        boundary_row(
            {
                "system_comparison_summary_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-COMPARISON-SUMMARY-SYSTEM-0001",
                "scope_comparison_rows": len(scope_rows),
                "signal_comparison_rows": len(signal_rows),
                "sidecar_attachment_rows": len(attachment_rows),
                "scope_comparison_class_counts": dict(sorted(scope_classes.items())),
                "signal_count_balance_counts": dict(sorted(signal_balances.items())),
                "sidecar_attachment_class_counts": dict(sorted(attachment_classes.items())),
                "system_comparison_summary": (
                    "Compare represented replay packet roles by scope, retain sidecar attachment state, and send "
                    "sidecar-only scopes to review before downstream packet scoring."
                ),
                "system_comparison_summary_status": "RUNTIME_REPLAY_COMPARISON_SUMMARY_MATERIALIZED_BRANCH_LOCAL",
            }
        )
    ]


def comparison_summary_bucket_rows(
    scope_rows: list[dict[str, Any]],
    signal_rows: list[dict[str, Any]],
    attachment_rows: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("scope_comparison_class", scope_rows, "scope_comparison_class"),
        ("scope_comparison_next_step", scope_rows, "scope_comparison_next_step"),
        ("signal_count_balance", signal_rows, "signal_count_balance"),
        ("sidecar_attachment_class", attachment_rows, "sidecar_attachment_class"),
        ("system_comparison_summary_status", system_rows, "system_comparison_summary_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "comparison_summary_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-COMPARISON-SUMMARY-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
