#!/usr/bin/env python3
"""Join recovered-unfilled, exact-spread, and no-fill geometry controls."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

RECOVERED_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_PATH_CONTROL_RESULT_2026-05-16.json"
RECOVERED_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_ENTRY_PATH_LEDGER_2026-05-16.jsonl"
RECOVERED_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_SIGNATURE_PATH_LEDGER_2026-05-16.jsonl"
EXACT_DELTA_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_DESCRIPTOR_DELTA_LEDGER_2026-05-16.jsonl"
EXACT_UNAVAILABLE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_UNAVAILABLE_STRESS_LEDGER_2026-05-16.jsonl"
NOFILL_REPAIR_BRANCH_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_BRANCH_LEDGER_2026-05-16.jsonl"
NOFILL_AMBIGUITY_BRANCH_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_BRANCH_STATUS_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_RESULT_2026-05-16.json"
SIGNATURE_JOIN_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_SIGNATURE_JOIN_LEDGER_2026-05-16.jsonl"
EXACT_CONTEXT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_EXACT_SPREAD_CONTEXT_LEDGER_2026-05-16.jsonl"
NOFILL_CONTEXT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_NOFILL_GEOMETRY_CONTEXT_LEDGER_2026-05-16.jsonl"
FAMILY_JOIN_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_FAMILY_JOIN_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC recovered-unfilled cross-control join only. Rows join "
    "recovered fill paths, exact-spread/stress controls, and no-fill geometry "
    "branch context for mechanism splitting; no validation, R/PnL, expectancy, "
    "win-rate, live-readiness, promotion, or live behavior change is claimed."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        RECOVERED_RESULT_PATH,
        RECOVERED_ENTRY_PATH,
        RECOVERED_SIGNATURE_PATH,
        EXACT_DELTA_PATH,
        EXACT_UNAVAILABLE_PATH,
        NOFILL_REPAIR_BRANCH_PATH,
        NOFILL_AMBIGUITY_BRANCH_PATH,
    ]
    rows = [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
            "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
        }
        for path in paths
    ]
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def family_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("route_candidate_id")),
            str(row.get("entry_variant")),
            str(row.get("target_stop_contract_id")),
        ]
    )


def symbol_side_key(row: dict[str, Any]) -> str:
    return f"{row.get('symbol')}|{row.get('side')}"


def status_set(rows: list[dict[str, Any]], field: str) -> list[str]:
    return sorted({str(row.get(field)) for row in rows if row.get(field) is not None})


def exact_family_status(delta_rows: list[dict[str, Any]], unavailable_rows: list[dict[str, Any]]) -> str:
    if delta_rows and unavailable_rows:
        return "FAMILY_HAS_EXACT_SPREAD_DELTA_AND_UNAVAILABLE_STRESS_CONTEXT"
    if delta_rows:
        return "FAMILY_HAS_EXACT_SPREAD_DELTA_CONTEXT"
    if unavailable_rows:
        return "FAMILY_HAS_EXACT_SPREAD_UNAVAILABLE_STRESS_CONTEXT"
    return "FAMILY_HAS_NO_GRADIENT_EXACT_SPREAD_CONTEXT"


def nofill_symbol_side_status(count: int) -> str:
    if count > 0:
        return "HAS_NOFILL_GEOMETRY_SYMBOL_SIDE_CONTEXT"
    return "NO_NOFILL_GEOMETRY_SYMBOL_SIDE_CONTEXT"


def signature_cross_status(
    row: dict[str, Any],
    delta_rows: list[dict[str, Any]],
    unavailable_rows: list[dict[str, Any]],
    nofill_count: int,
) -> str:
    fill = row.get("recovered_fill_source")
    path_status = str(row.get("recovered_path_status"))
    exact_status = exact_family_status(delta_rows, unavailable_rows)
    nofill_status = nofill_symbol_side_status(nofill_count)
    if fill == "EXACT_TICK_FILL_SIDE_TOUCH" and "FILL_BAR_ORDER_AMBIGUITY" in path_status:
        prefix = "EXACT_TICK_RECOVERED_FILL_BAR_AMBIGUITY"
    elif fill == "EXACT_TICK_FILL_SIDE_TOUCH":
        prefix = "EXACT_TICK_RECOVERED_ORDERED_AFTER_FILL_BAR"
    elif "FILL_BAR_ORDER_AMBIGUITY" in path_status:
        prefix = "M1_PROXY_FILL_SIDE_UNRESOLVED_FILL_BAR_AMBIGUITY"
    else:
        prefix = "M1_PROXY_FILL_SIDE_UNRESOLVED_STRESS"
    return f"{prefix}__{exact_status}__{nofill_status}"


def family_cross_status(
    recovered_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    unavailable_rows: list[dict[str, Any]],
) -> str:
    has_recovered = bool(recovered_rows)
    has_delta = bool(delta_rows)
    has_unavailable = bool(unavailable_rows)
    if has_recovered and has_delta and has_unavailable:
        return "RECOVERED_WITH_EXACT_DELTA_AND_UNAVAILABLE_STRESS_FAMILY"
    if has_recovered and has_delta:
        return "RECOVERED_WITH_EXACT_DELTA_FAMILY"
    if has_recovered and has_unavailable:
        return "RECOVERED_WITH_UNAVAILABLE_STRESS_FAMILY"
    if has_recovered:
        return "RECOVERED_ONLY_FAMILY"
    if has_delta and has_unavailable:
        return "EXACT_DELTA_AND_UNAVAILABLE_STRESS_ONLY_FAMILY"
    if has_delta:
        return "EXACT_DELTA_ONLY_FAMILY"
    return "UNAVAILABLE_STRESS_ONLY_FAMILY"


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "historical_ohlc_gtos_replay_recovered_unfilled_cross_control_join",
            "generated_utc": generated_at,
            "counts": outputs["counts"],
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    )
    manifest["outputs"] = existing
    manifest["last_updated_utc"] = generated_at
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(outputs: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "event_type": "route_artifact_built",
        "route": "historical_ohlc_gtos_replay_recovered_unfilled_cross_control_join",
        "artifact": RESULT_PATH.name,
        "counts": outputs["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    manifest_rows, manifest_hash = source_manifest()
    recovered_result = read_json(RECOVERED_RESULT_PATH)
    recovered_entries = [row for row in read_jsonl(RECOVERED_ENTRY_PATH) if not row.get("_parse_error")]
    recovered_signatures = [row for row in read_jsonl(RECOVERED_SIGNATURE_PATH) if not row.get("_parse_error")]
    exact_delta_rows = [row for row in read_jsonl(EXACT_DELTA_PATH) if not row.get("_parse_error")]
    exact_unavailable_rows = [row for row in read_jsonl(EXACT_UNAVAILABLE_PATH) if not row.get("_parse_error")]
    nofill_repair_rows = [row for row in read_jsonl(NOFILL_REPAIR_BRANCH_PATH) if not row.get("_parse_error")]
    nofill_ambiguity_rows = [row for row in read_jsonl(NOFILL_AMBIGUITY_BRANCH_PATH) if not row.get("_parse_error")]

    recovered_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    delta_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unavailable_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    recovered_by_symbol_side: dict[str, list[dict[str, Any]]] = defaultdict(list)
    delta_by_symbol_side: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unavailable_by_symbol_side: dict[str, list[dict[str, Any]]] = defaultdict(list)
    nofill_by_symbol_side: dict[str, list[dict[str, Any]]] = defaultdict(list)
    nofill_ambiguity_by_branch = {row["branch_id"]: row for row in nofill_ambiguity_rows}

    for row in recovered_signatures:
        recovered_by_family[family_key(row)].append(row)
        recovered_by_symbol_side[symbol_side_key(row)].append(row)
    for row in exact_delta_rows:
        delta_by_family[family_key(row)].append(row)
        delta_by_symbol_side[symbol_side_key(row)].append(row)
    for row in exact_unavailable_rows:
        unavailable_by_family[family_key(row)].append(row)
        unavailable_by_symbol_side[symbol_side_key(row)].append(row)
    for row in nofill_repair_rows:
        nofill_by_symbol_side[symbol_side_key(row)].append(row)

    signature_join_rows: list[dict[str, Any]] = []
    signature_status_counter: Counter[str] = Counter()
    for seq, row in enumerate(recovered_signatures, 1):
        key = family_key(row)
        ss_key = symbol_side_key(row)
        delta_context = delta_by_family.get(key, [])
        unavailable_context = unavailable_by_family.get(key, [])
        nofill_context = nofill_by_symbol_side.get(ss_key, [])
        status = signature_cross_status(row, delta_context, unavailable_context, len(nofill_context))
        signature_status_counter[status] += 1
        signature_join_rows.append(
            {
                "cross_control_signature_join_id": f"OHLC-GTOS-RECOVERED-CROSS-SIG-{seq:05d}",
                "recovered_signature_path_id": row["recovered_signature_path_id"],
                "cost_sensitivity_signature_id": row["cost_sensitivity_signature_id"],
                "entry_variant_id": row["entry_variant_id"],
                "event_id": row["event_id"],
                "route_candidate_id": row["route_candidate_id"],
                "symbol": row["symbol"],
                "side": row["side"],
                "entry_variant": row["entry_variant"],
                "target_stop_contract_id": row["target_stop_contract_id"],
                "target_multiple": row["target_multiple"],
                "stop_multiple": row["stop_multiple"],
                "recovered_fill_source": row["recovered_fill_source"],
                "recovered_path_status": row["recovered_path_status"],
                "recovered_first_touch_status": row["recovered_first_touch_status"],
                "family_key": key,
                "symbol_side_key": ss_key,
                "family_exact_descriptor_delta_rows": len(delta_context),
                "family_exact_unavailable_stress_rows": len(unavailable_context),
                "family_exact_descriptor_delta_statuses": status_set(delta_context, "descriptor_delta_status"),
                "family_exact_first_touch_statuses": status_set(delta_context, "exact_first_touch_status"),
                "family_exact_unavailable_stress_statuses": status_set(unavailable_context, "stress_bound_status"),
                "family_exact_spread_context_status": exact_family_status(delta_context, unavailable_context),
                "symbol_side_nofill_geometry_rows": len(nofill_context),
                "symbol_side_nofill_proxy_projection_statuses": status_set(nofill_context, "proxy_projection_status"),
                "symbol_side_nofill_geometry_statuses": status_set(nofill_context, "geometry_status"),
                "cross_control_join_status": status,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_SIGNATURE_JOIN",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    exact_context_rows: list[dict[str, Any]] = []
    exact_context_counter: Counter[str] = Counter()
    combined_exact_rows = [("EXACT_DESCRIPTOR_DELTA", row) for row in exact_delta_rows] + [
        ("EXACT_UNAVAILABLE_STRESS", row) for row in exact_unavailable_rows
    ]
    for seq, (kind, row) in enumerate(combined_exact_rows, 1):
        key = family_key(row)
        ss_key = symbol_side_key(row)
        recovered_context = recovered_by_family.get(key, [])
        nofill_context = nofill_by_symbol_side.get(ss_key, [])
        if recovered_context and nofill_context:
            context_status = f"{kind}_WITH_RECOVERED_FAMILY_AND_NOFILL_SYMBOL_SIDE_CONTEXT"
        elif recovered_context:
            context_status = f"{kind}_WITH_RECOVERED_FAMILY_CONTEXT"
        elif nofill_context:
            context_status = f"{kind}_WITH_NOFILL_SYMBOL_SIDE_CONTEXT"
        else:
            context_status = f"{kind}_WITHOUT_RECOVERED_OR_NOFILL_CONTEXT"
        exact_context_counter[context_status] += 1
        exact_context_rows.append(
            {
                "cross_control_exact_context_id": f"OHLC-GTOS-RECOVERED-CROSS-EXACT-{seq:05d}",
                "exact_context_kind": kind,
                "cost_sensitivity_signature_id": row.get("cost_sensitivity_signature_id"),
                "entry_variant_id": row.get("entry_variant_id"),
                "event_id": row.get("event_id"),
                "route_candidate_id": row.get("route_candidate_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "entry_variant": row.get("entry_variant"),
                "target_stop_contract_id": row.get("target_stop_contract_id"),
                "target_multiple": row.get("target_multiple"),
                "stop_multiple": row.get("stop_multiple"),
                "descriptor_delta_status": row.get("descriptor_delta_status"),
                "exact_first_touch_status": row.get("exact_first_touch_status"),
                "exact_spread_value": row.get("exact_spread_value"),
                "exact_spread_proxy_bucket": row.get("exact_spread_proxy_bucket"),
                "stress_bound_status": row.get("stress_bound_status"),
                "low_spread_descriptor_status": row.get("low_spread_descriptor_status"),
                "high_spread_descriptor_status": row.get("high_spread_descriptor_status"),
                "family_key": key,
                "symbol_side_key": ss_key,
                "family_recovered_signature_rows": len(recovered_context),
                "family_recovered_fill_sources": status_set(recovered_context, "recovered_fill_source"),
                "family_recovered_path_statuses": status_set(recovered_context, "recovered_path_status"),
                "symbol_side_nofill_geometry_rows": len(nofill_context),
                "symbol_side_nofill_proxy_projection_statuses": status_set(nofill_context, "proxy_projection_status"),
                "cross_control_exact_context_status": context_status,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_EXACT_SPREAD_CONTEXT",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    nofill_context_rows: list[dict[str, Any]] = []
    nofill_context_counter: Counter[str] = Counter()
    for seq, row in enumerate(nofill_repair_rows, 1):
        ss_key = symbol_side_key(row)
        ambiguity = nofill_ambiguity_by_branch.get(row["branch_id"], {})
        recovered_context = recovered_by_symbol_side.get(ss_key, [])
        delta_context = delta_by_symbol_side.get(ss_key, [])
        unavailable_context = unavailable_by_symbol_side.get(ss_key, [])
        if recovered_context and (delta_context or unavailable_context):
            context_status = "NOFILL_GEOMETRY_WITH_RECOVERED_AND_EXACT_SPREAD_SYMBOL_SIDE_CONTEXT"
        elif recovered_context:
            context_status = "NOFILL_GEOMETRY_WITH_RECOVERED_SYMBOL_SIDE_CONTEXT"
        elif delta_context or unavailable_context:
            context_status = "NOFILL_GEOMETRY_WITH_EXACT_SPREAD_SYMBOL_SIDE_CONTEXT"
        else:
            context_status = "NOFILL_GEOMETRY_WITHOUT_OHLC_REPLAY_SYMBOL_SIDE_CONTEXT"
        nofill_context_counter[context_status] += 1
        nofill_context_rows.append(
            {
                "cross_control_nofill_context_id": f"OHLC-GTOS-RECOVERED-CROSS-NOFILL-{seq:05d}",
                "branch_id": row["branch_id"],
                "candidate_id": row["candidate_id"],
                "branch_type": row["branch_type"],
                "symbol": row["symbol"],
                "side": row["side"],
                "framework": row.get("framework"),
                "geometry_status": row.get("geometry_status"),
                "path_proxy_status": row.get("path_proxy_status"),
                "proxy_projection_status": row.get("proxy_projection_status"),
                "ambiguity_split_geometry_status": ambiguity.get("geometry_status"),
                "ambiguity_split_path_proxy_status": ambiguity.get("path_proxy_status"),
                "ambiguity_split_proxy_projection_status": ambiguity.get("proxy_projection_status"),
                "decision_spread_status_after_proxy": row.get("decision_spread_status_after_proxy"),
                "symbol_side_key": ss_key,
                "symbol_side_recovered_signature_rows": len(recovered_context),
                "symbol_side_recovered_fill_sources": status_set(recovered_context, "recovered_fill_source"),
                "symbol_side_recovered_path_statuses": status_set(recovered_context, "recovered_path_status"),
                "symbol_side_exact_descriptor_delta_rows": len(delta_context),
                "symbol_side_exact_unavailable_stress_rows": len(unavailable_context),
                "symbol_side_exact_descriptor_delta_statuses": status_set(delta_context, "descriptor_delta_status"),
                "symbol_side_exact_unavailable_stress_statuses": status_set(unavailable_context, "stress_bound_status"),
                "cross_control_nofill_context_status": context_status,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_NOFILL_GEOMETRY_CONTEXT",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    family_join_rows: list[dict[str, Any]] = []
    family_status_counter: Counter[str] = Counter()
    all_family_keys = sorted(set(recovered_by_family) | set(delta_by_family) | set(unavailable_by_family))
    for seq, key in enumerate(all_family_keys, 1):
        recovered_context = recovered_by_family.get(key, [])
        delta_context = delta_by_family.get(key, [])
        unavailable_context = unavailable_by_family.get(key, [])
        exemplar = (recovered_context or delta_context or unavailable_context)[0]
        status = family_cross_status(recovered_context, delta_context, unavailable_context)
        family_status_counter[status] += 1
        family_join_rows.append(
            {
                "cross_control_family_join_id": f"OHLC-GTOS-RECOVERED-CROSS-FAMILY-{seq:05d}",
                "family_key": key,
                "route_candidate_id": exemplar.get("route_candidate_id"),
                "symbol": exemplar.get("symbol"),
                "side": exemplar.get("side"),
                "entry_variant": exemplar.get("entry_variant"),
                "target_stop_contract_id": exemplar.get("target_stop_contract_id"),
                "target_multiple": exemplar.get("target_multiple"),
                "stop_multiple": exemplar.get("stop_multiple"),
                "recovered_signature_rows": len(recovered_context),
                "exact_descriptor_delta_rows": len(delta_context),
                "exact_unavailable_stress_rows": len(unavailable_context),
                "recovered_fill_sources": status_set(recovered_context, "recovered_fill_source"),
                "recovered_path_statuses": status_set(recovered_context, "recovered_path_status"),
                "exact_descriptor_delta_statuses": status_set(delta_context, "descriptor_delta_status"),
                "exact_first_touch_statuses": status_set(delta_context, "exact_first_touch_status"),
                "exact_unavailable_stress_statuses": status_set(unavailable_context, "stress_bound_status"),
                "cross_control_family_status": status,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_FAMILY_JOIN",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    bucket_rows: list[dict[str, Any]] = []

    def add_bucket(axis: str, counter: Counter[Any]) -> None:
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_axis": axis,
                    "bucket": "|".join(str(part) for part in bucket) if isinstance(bucket, tuple) else str(bucket),
                    "count": count,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_BUCKET",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    add_bucket("signature_cross_control_join_status", signature_status_counter)
    add_bucket("exact_cross_control_context_status", exact_context_counter)
    add_bucket("nofill_cross_control_context_status", nofill_context_counter)
    add_bucket("family_cross_control_status", family_status_counter)
    add_bucket("recovered_fill_source__family_exact_context", Counter((row["recovered_fill_source"], row["family_exact_spread_context_status"]) for row in signature_join_rows))
    add_bucket("recovered_path_status__nofill_context", Counter((row["recovered_path_status"], nofill_symbol_side_status(row["symbol_side_nofill_geometry_rows"])) for row in signature_join_rows))
    add_bucket("nofill_proxy_projection_status__cross_context", Counter((row["proxy_projection_status"], row["cross_control_nofill_context_status"]) for row in nofill_context_rows))

    exact_differs_rows = [row for row in exact_context_rows if row.get("descriptor_delta_status") == "EXACT_DIFFERS_FROM_LOW_AND_HIGH_PROXY_DESCRIPTOR"]
    recovered_exact_overlap = [row for row in signature_join_rows if row["family_exact_descriptor_delta_rows"] > 0]
    recovered_unavailable_overlap = [row for row in signature_join_rows if row["family_exact_unavailable_stress_rows"] > 0]
    fill_bar_rows = [
        row
        for row in signature_join_rows
        if str(row.get("recovered_first_touch_status", "")).startswith("FILL_BAR_")
    ]
    nofill_overlap_rows = [
        row
        for row in nofill_context_rows
        if row["cross_control_nofill_context_status"]
        in {
            "NOFILL_GEOMETRY_WITH_RECOVERED_AND_EXACT_SPREAD_SYMBOL_SIDE_CONTEXT",
            "NOFILL_GEOMETRY_WITH_RECOVERED_SYMBOL_SIDE_CONTEXT",
            "NOFILL_GEOMETRY_WITH_EXACT_SPREAD_SYMBOL_SIDE_CONTEXT",
        }
    ]
    question_rows = [
        {
            "question_id": "OHLC-GTOS-RECOVERED-CROSS-CONTROL-QUESTION-001",
            "question": "Which recovered signatures share route/entry/target-stop family context with exact-spread descriptor deltas?",
            "row_count": len(recovered_exact_overlap),
            "next_same_resource_action": "split recovered rows with exact-spread family context by descriptor delta status and fill source",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-RECOVERED-CROSS-CONTROL-QUESTION-002",
            "question": "Which recovered signatures only have unavailable exact-spread stress context at family level?",
            "row_count": len(recovered_unavailable_overlap),
            "next_same_resource_action": "route unavailable-overlap families into low/high spread interval stress and broader tick-history acquisition/proxy search",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-RECOVERED-CROSS-CONTROL-QUESTION-003",
            "question": "Which exact-spread rows differ from both low and high proxy descriptors and therefore need supra-static friction split?",
            "row_count": len(exact_differs_rows),
            "next_same_resource_action": "split exact-differs rows by route/entry/target-stop and spread value versus tested proxy interval",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-RECOVERED-CROSS-CONTROL-QUESTION-004",
            "question": "Which recovered rows remain fill-bar target/stop order unresolved after cross-control joining?",
            "row_count": len(fill_bar_rows),
            "next_same_resource_action": "route fill-bar rows to M1/tick ordering stress and conservative target/stop interval bounds",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-RECOVERED-CROSS-CONTROL-QUESTION-005",
            "question": "Which no-fill geometry branches have matching symbol/side context in recovered or exact-spread OHLC controls?",
            "row_count": len(nofill_overlap_rows),
            "next_same_resource_action": "split no-fill geometry branches by proxy projection, geometry status, and OHLC symbol/side context",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]

    counts = {
        "bucket_rows": len(bucket_rows),
        "exact_context_rows": len(exact_context_rows),
        "exact_descriptor_delta_input_rows": len(exact_delta_rows),
        "exact_unavailable_stress_input_rows": len(exact_unavailable_rows),
        "family_join_rows": len(family_join_rows),
        "nofill_ambiguity_branch_input_rows": len(nofill_ambiguity_rows),
        "nofill_context_rows": len(nofill_context_rows),
        "nofill_repair_branch_input_rows": len(nofill_repair_rows),
        "question_rows": len(question_rows),
        "recovered_entry_input_rows": len(recovered_entries),
        "recovered_signature_input_rows": len(recovered_signatures),
        "signature_join_rows": len(signature_join_rows),
        "source_manifest_rows": len(manifest_rows),
    }
    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_recovered_unfilled_cross_control_join_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_JOIN_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This cross-control join packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "signature_cross_control_join_status_counts": dict(sorted(signature_status_counter.items())),
        "exact_cross_control_context_status_counts": dict(sorted(exact_context_counter.items())),
        "nofill_cross_control_context_status_counts": dict(sorted(nofill_context_counter.items())),
        "family_cross_control_status_counts": dict(sorted(family_status_counter.items())),
        "recovered_upstream_counts": recovered_result.get("counts", {}),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "next_same_resource_work": [
            "split exact-differs rows by route/entry/target-stop and spread interval mechanics",
            "stress recovered fill-bar order-unresolved rows with M1/tick ordering where available",
            "convert confirmed no-fill signatures into execution-friction/fillability branch controls",
            "build cost/fill/path family synthesis preserving all family rows",
        ],
    }

    write_jsonl(SIGNATURE_JOIN_PATH, signature_join_rows)
    write_jsonl(EXACT_CONTEXT_PATH, exact_context_rows)
    write_jsonl(NOFILL_CONTEXT_PATH, nofill_context_rows)
    write_jsonl(FAMILY_JOIN_PATH, family_join_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Recovered-Unfilled Cross-Control Join",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet joins recovered unfilled path controls with exact-spread/stress controls and no-fill geometry branch context.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Family Status",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(family_status_counter.items())),
                "",
                "## Immediate Work",
                "",
                "- Split exact-differs rows by route/entry/target-stop and spread interval mechanics.",
                "- Stress recovered fill-bar order-unresolved rows with M1/tick ordering where available.",
                "- Convert confirmed no-fill signatures into execution-friction/fillability branch controls.",
                "- Build cost/fill/path family synthesis preserving all family rows.",
                "",
                "No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    update_manifest(output, generated_at)
    append_sprint_ledger(output, generated_at)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
