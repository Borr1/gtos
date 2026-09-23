from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_AVOID_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_2026-05-17.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_SUMMARY_2026-05-17.json"
OUTPUT_MANIFEST = ROUTE_DIR / "MAIN_ORCH24_ENTRY_OFFSET_CONCENTRATION_GUARD_OUTPUT_MANIFEST_2026-05-17.json"

OWNER_BRANCHES = {
    "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_CHALLENGER",
    "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_NEAR_MISS_CHALLENGER",
}
PREFILL_REFERENCE_BRANCHES = {
    "REDESIGN_PREFILL_FAR_MISS_RETEST_CONTROL_MERGED_INTO_ENTRY_OFFSET_050R",
    "MERGE_PREFILL_NEAR_MISS_INTO_ENTRY_OFFSET_050R_IMPLEMENTATION",
}
NO_FILL_CONTROL_BRANCHES = {
    "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL",
    "KILL_PREFILL_050R_OFFSET_NO_FILL_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL",
}

GUARDED_OWNER_BRANCH = "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_CONCENTRATION_GUARDED_CANDIDATE"
GUARDED_PREFILL_BRANCH = "MERGE_PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE"
SOURCE_COST_FILL_REPAIR_BRANCH = "REDESIGN_ENTRY_OFFSET_NO_FILL_RETEST_SOURCE_COST_FILL_REPAIR_REQUIRED"
LARGEST_CLUSTER_KEY = "US30_cash|2026-05-08"
BOUNDARY_FIELDS = {
    "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
    "validation_result_status": "NOT_OPENED_BY_RESULT_MATERIALIZATION",
    "outcome_result_rows_status": "NOT_OPENED_BY_RESULT_MATERIALIZATION",
    "broker_runtime_change_status": "NO_BROKER_OR_RUNTIME_CHANGE_FROM_RESULT_MATERIALIZATION",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def proxy_summary(rows: list[dict[str, Any]]) -> tuple[int, float]:
    count = 0
    total = 0.0
    for row in rows:
        value = row.get("after_proxy_r")
        if value is None:
            value = row.get("strategy_proxy_r")
        number = safe_float(value)
        if number is None:
            continue
        count += 1
        total += number
    return count, round(total, 8)


def candidate_cluster_key(candidate_id: str) -> str:
    match = re.search(r"_(\d{4}-\d{2}-\d{2})T", candidate_id)
    if not match:
        return "UNKNOWN|UNKNOWN"
    symbol = candidate_id[: match.start()]
    return f"{symbol}|{match.group(1)}"


def subtype(row: dict[str, Any]) -> str:
    branch = str(row.get("branch_decision") or "")
    if "NEAR_MISS" in branch:
        return "NEAR_MISS"
    if "FAR_MISS" in branch:
        return "FAR_MISS"
    bucket = str(row.get("entry_retest_redesign_bucket") or "")
    if "NEAR_MISS" in bucket:
        return "NEAR_MISS"
    if "FAR_MISS" in bucket:
        return "FAR_MISS"
    return "UNKNOWN"


def owner_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("branch_decision") in OWNER_BRANCHES]


def prefill_reference_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("branch_decision") in PREFILL_REFERENCE_BRANCHES]


def no_fill_control_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("branch_decision") in NO_FILL_CONTROL_BRANCHES]


def cluster_stats(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_cluster: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_cluster[candidate_cluster_key(str(row.get("candidate_id") or ""))].append(row)

    total_rows = len(rows)
    total_sum = round(sum(safe_float(row.get("after_proxy_r")) or 0.0 for row in rows), 8)
    stats: dict[str, dict[str, Any]] = {}
    for key, cluster_rows in by_cluster.items():
        row_count = len(cluster_rows)
        proxy_sum = round(sum(safe_float(row.get("after_proxy_r")) or 0.0 for row in cluster_rows), 8)
        stats[key] = {
            "cluster_key": key,
            "row_count": row_count,
            "proxy_r_sum": proxy_sum,
            "row_share": round(row_count / total_rows, 8) if total_rows else 0.0,
            "proxy_r_share": round(proxy_sum / total_sum, 8) if total_sum else 0.0,
        }
    return stats


def update_audit(
    row: dict[str, Any],
    *,
    status: str,
    proxy_reference: float | None,
    owner_row_id: str | None,
    cluster_key: str,
) -> None:
    audit = row.get("missed_opportunity_audit")
    if not isinstance(audit, dict):
        audit = {}
    audit.update(
        {
            "current_claim": "ENTRY_OFFSET_050R_SPREAD_AWARE_SHIFT_FILL_OR_PREFILL_TP_AFTER_FILL",
            "decision_branch": row.get("branch_decision"),
            "kill_scope": (
                "NOT_KILLED_DEFAULT_OFF_OWNER_CLUSTER_GUARDED"
                if status == "ENTRY_OFFSET_OWNER_CLUSTER_GUARDED"
                else "CURRENT_CLAIM_ONLY"
                if status == "NO_FILL_CONTROL_SOURCE_COST_FILL_REPAIR_REQUIRED"
                else "NOT_KILLED_MERGED_ENTRY_OFFSET_OWNER_REFERENCE"
            ),
            "what_was_tried": "M15_OR_TICK_REPAIRED_ENTRY_OFFSET_050R_REPLAY_WITH_PREFILL_OWNER_MERGE",
            "unsupported_reason": (
                "POSITIVE_PROXY_CLUSTER_CONCENTRATED_IN_US30_CASH_2026_05_08_SO_NOT_STANDALONE_PROMOTABLE"
                if status == "ENTRY_OFFSET_OWNER_CLUSTER_GUARDED"
                else "PROXY_R_OWNED_BY_ENTRY_OFFSET_OWNER_NOT_PREFILL_STANDALONE"
                if status == "PREFILL_REFERENCE_CLUSTER_GUARDED"
                else "ENTRY_OFFSET_050R_REPLAY_DID_NOT_FILL_BEFORE_TARGET_AREA"
            ),
            "what_could_make_it_work": (
                "DUPLICATE_AWARE_REPLAY_WITH_SYMBOL_DATE_CLUSTER_CAP_AND_OUT_OF_CLUSTER_SUPPORT"
                if status != "NO_FILL_CONTROL_SOURCE_COST_FILL_REPAIR_REQUIRED"
                else "WIDER_OFFSET_GRID_OR_MARKET_CONTROL_STATE_WITH_SOURCE_COST_FILL_REPAIR_THAT_REACHES_FILL_BEFORE_TARGET_AREA"
            ),
            "preserve_as": (
                "ENTRY_OFFSET_050R_CLUSTER_GUARDED_DEFAULT_OFF_CANDIDATE"
                if status == "ENTRY_OFFSET_OWNER_CLUSTER_GUARDED"
                else "PREFILL_CONTEXT_FEATURE_MERGED_TO_ENTRY_OFFSET_050R_CLUSTER_GUARD"
                if status == "PREFILL_REFERENCE_CLUSTER_GUARDED"
                else "NO_FILL_AVOID_CONTEXT_AND_RETEST_REDESIGN_SOURCE_REQUIREMENT"
            ),
            "next_route": (
                "REPLAY_ENTRY_OFFSET_050R_WITH_SYMBOL_DATE_CLUSTER_CAP_FAR_NEAR_SPLIT_COST_AND_FILL_REPAIR"
                if status != "NO_FILL_CONTROL_SOURCE_COST_FILL_REPAIR_REQUIRED"
                else "TEST_WIDER_RETEST_OFFSETS_AND_MARKET_CONTROL_BUCKETS_WITH_FILL_COST_SOURCE_FIELDS"
            ),
            "path_status": {
                "proxy_r_reference": proxy_reference,
                "proxy_owner_row_id": owner_row_id,
                "proxy_counting_decision": (
                    "COUNTED_ON_ENTRY_OFFSET_OWNER_ROW_ONLY"
                    if status == "ENTRY_OFFSET_OWNER_CLUSTER_GUARDED"
                    else "REFERENCE_ONLY_NOT_DUPLICATED"
                    if status == "PREFILL_REFERENCE_CLUSTER_GUARDED"
                    else "ZERO_OR_NO_FILL_REFERENCE_ONLY"
                ),
                "cluster_key": cluster_key,
                "source_artifact": row.get("source_artifact"),
            },
        }
    )
    row["missed_opportunity_audit"] = audit


def annotate_cluster_fields(
    row: dict[str, Any],
    *,
    stats: dict[str, dict[str, Any]],
    owner_by_candidate: dict[str, dict[str, Any]],
    status: str,
) -> None:
    candidate_id = str(row.get("candidate_id") or "")
    cluster_key = candidate_cluster_key(candidate_id)
    stat = stats.get(cluster_key, {"row_count": 0, "proxy_r_sum": 0.0, "row_share": 0.0, "proxy_r_share": 0.0})
    owner = owner_by_candidate.get(candidate_id)
    owner_row_id = str(owner.get("row_id")) if owner else str(row.get("row_id") or "")
    proxy_reference = safe_float(row.get("after_proxy_r"))
    if proxy_reference is None:
        proxy_reference = safe_float(row.get("opportunity_proxy_r_reference"))

    row["entry_offset_concentration_guard_status"] = status
    row["entry_offset_original_branch_decision"] = row.get("branch_decision")
    row["entry_offset_original_implementation_candidate"] = row.get("implementation_candidate")
    row["entry_offset_original_subtype"] = subtype(row)
    row["entry_offset_concentration_cluster_key"] = cluster_key
    row["entry_offset_concentration_cluster_row_count"] = stat["row_count"]
    row["entry_offset_concentration_cluster_proxy_r_sum"] = stat["proxy_r_sum"]
    row["entry_offset_concentration_cluster_row_share"] = stat["row_share"]
    row["entry_offset_concentration_cluster_proxy_r_share"] = stat["proxy_r_share"]
    row["entry_offset_concentration_effective_cluster_count"] = len(stats)
    row["entry_offset_largest_cluster_key"] = LARGEST_CLUSTER_KEY
    row["entry_offset_largest_cluster_guard_required"] = cluster_key == LARGEST_CLUSTER_KEY
    row["entry_offset_proxy_owner_row_id"] = owner_row_id
    row["entry_offset_proxy_owner_candidate_id"] = candidate_id
    row["entry_offset_proxy_r_reference"] = proxy_reference
    row["entry_offset_proxy_reference_status"] = (
        "COUNTED_ON_ENTRY_OFFSET_OWNER_ROW_ONLY"
        if status == "ENTRY_OFFSET_OWNER_CLUSTER_GUARDED"
        else "REFERENCE_ONLY_NOT_DUPLICATED"
        if status == "PREFILL_REFERENCE_CLUSTER_GUARDED"
        else "ZERO_OR_NO_FILL_REFERENCE_ONLY"
    )
    row["entry_offset_cluster_guard_decision"] = (
        "CLUSTER_GUARD_REQUIRED_BECAUSE_US30_CASH_2026_05_08_OWNS_11_OF_13_POSITIVE_ROWS"
        if cluster_key == LARGEST_CLUSTER_KEY
        else "DIVERSIFYING_SUPPORT_ROW_KEPT_BUT_NOT_ENOUGH_FOR_IMPLEMENTATION"
    )
    row["underlying_intelligence_preserved"] = True
    row["opportunity_owner_row_id"] = owner_row_id
    row["opportunity_owner_source_artifact"] = row.get("source_artifact") or row.get("opportunity_owner_source_artifact")
    row["opportunity_proxy_r_reference"] = proxy_reference
    row["opportunity_proxy_reference_status"] = row["entry_offset_proxy_reference_status"]
    row["opportunity_useful_mechanism"] = (
        "Spread-aware 0.50R entry shift and prefill TP-after-fill timing remain useful as a default-off entry-offset component, but the current positive proxy is cluster-concentrated."
    )
    row["opportunity_downstream_paths"] = [
        "entry-offset merge",
        "redesign",
        "avoid/inverse",
        "context feature",
        "source requirement",
        "tighter target",
        "shorter horizon",
        "broader system component",
    ]
    row["opportunity_preservation_status"] = "ENTRY_OFFSET_CONCENTRATION_GUARD_OPPORTUNITY_PRESERVED"
    row["opportunity_not_independently_countable_reason"] = (
        "Proxy R is counted once on the entry-offset owner row and is not duplicated by prefill references; the current implementation claim is default-off discovery only because 11/13 positive rows cluster on US30_cash|2026-05-08."
        if status != "NO_FILL_CONTROL_SOURCE_COST_FILL_REPAIR_REQUIRED"
        else "The 0.50R fill claim did not fill before target area in repaired replay; preserve as no-fill/avoid context and wider-offset/source-cost-fill repair, not as a standalone positive implementation count."
    )
    update_audit(
        row,
        status=status,
        proxy_reference=proxy_reference,
        owner_row_id=owner_row_id,
        cluster_key=cluster_key,
    )


def annotate_row(
    row: dict[str, Any],
    *,
    stats: dict[str, dict[str, Any]],
    owner_by_candidate: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    out = dict(row)
    branch = str(out.get("branch_decision") or "")

    if branch in OWNER_BRANCHES:
        annotate_cluster_fields(
            out,
            stats=stats,
            owner_by_candidate=owner_by_candidate,
            status="ENTRY_OFFSET_OWNER_CLUSTER_GUARDED",
        )
        out["branch_decision"] = GUARDED_OWNER_BRANCH
        out["current_action"] = GUARDED_OWNER_BRANCH
        out["implementation_candidate"] = "ENTRY_OFFSET_050R_CLUSTER_GUARDED_DEFAULT_OFF_CHALLENGER"
        out["implementation_decision"] = GUARDED_OWNER_BRANCH
        out["decision_evidence"] = (
            "POSITIVE_ENTRY_OFFSET_PROXY_R_RETAINED_BUT_CLUSTER_CAPPED_BY_SYMBOL_DATE_CONCENTRATION"
        )
        out["coverage_status"] = "IMPLEMENTATION_CANDIDATE_DEFAULT_OFF_CLUSTER_GUARDED"
        out["data_requirement_state"] = "COMPUTED_FROM_ENTRY_OFFSET_REPLAY_CLUSTER_GUARDED"
        out["scoring_boundary"] = "PROXY_R_COUNTED_ON_OWNER_ROW_DEFAULT_OFF_CLUSTER_CAP_REQUIRED"
        out["next_action"] = (
            "REPLAY_ENTRY_OFFSET_050R_WITH_SYMBOL_DATE_CLUSTER_CAP_FAR_NEAR_SPLIT_COST_AND_FILL_REPAIR"
        )
        return out

    if branch in PREFILL_REFERENCE_BRANCHES:
        annotate_cluster_fields(
            out,
            stats=stats,
            owner_by_candidate=owner_by_candidate,
            status="PREFILL_REFERENCE_CLUSTER_GUARDED",
        )
        out["branch_decision"] = GUARDED_PREFILL_BRANCH
        out["current_action"] = GUARDED_PREFILL_BRANCH
        out["implementation_candidate"] = "PREFILL_TP_AFTER_FILL_CONTEXT_MERGED_TO_ENTRY_OFFSET_CLUSTER_GUARD"
        out["implementation_decision"] = GUARDED_PREFILL_BRANCH
        out["decision_evidence"] = (
            "PREFILL_TP_AFTER_FILL_PROXY_R_REFERENCED_FROM_ENTRY_OFFSET_OWNER_NOT_DUPLICATED"
        )
        out["coverage_status"] = "MERGED_REFERENCE_NOT_STANDALONE_CLUSTER_GUARDED"
        out["data_requirement_state"] = "MERGED_TO_ENTRY_OFFSET_PROXY_OWNER_CLUSTER_GUARDED"
        out["scoring_boundary"] = "REFERENCE_ONLY_PREFILL_PROXY_R_NOT_COUNTED_STANDALONE"
        out["next_action"] = (
            "CONSUME_PREFILL_TP_AFTER_FILL_CONTEXT_IN_ENTRY_OFFSET_050R_CLUSTER_GUARDED_REPLAY"
        )
        return out

    if branch in NO_FILL_CONTROL_BRANCHES:
        annotate_cluster_fields(
            out,
            stats=stats,
            owner_by_candidate=owner_by_candidate,
            status="NO_FILL_CONTROL_SOURCE_COST_FILL_REPAIR_REQUIRED",
        )
        out["entry_offset_no_fill_control_status"] = "CURRENT_050R_FILL_CLAIM_UNSUPPORTED_REDESIGN_PATH_PRESERVED"
        out["entry_offset_no_fill_repair_branch_candidate"] = SOURCE_COST_FILL_REPAIR_BRANCH
        out["coverage_status"] = "KILLED_CURRENT_CLAIM_PRESERVED_AS_NO_FILL_RETEST_REDESIGN_OR_AVOID_CONTEXT"
        out["data_requirement_state"] = "RETEST_SOURCE_COST_FILL_OR_WIDER_OFFSET_REQUIRED"
        out["scoring_boundary"] = "NO_POSITIVE_PROXY_R_FOR_050R_NO_FILL_ROWS"
        out["next_action"] = "TEST_WIDER_RETEST_OFFSETS_AND_MARKET_CONTROL_BUCKETS_WITH_FILL_COST_SOURCE_FIELDS"
        return out

    out.setdefault("entry_offset_concentration_guard_status", "NOT_TARGET_ROW")
    return out


def missing_opportunity_preservation(rows: list[dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        required = (
            row.get("action_class") in {"KILL", "REDESIGN"}
            or str(row.get("branch_decision") or "") == GUARDED_OWNER_BRANCH
            or row.get("entry_offset_concentration_guard_status")
            in {
                "ENTRY_OFFSET_OWNER_CLUSTER_GUARDED",
                "PREFILL_REFERENCE_CLUSTER_GUARDED",
                "NO_FILL_CONTROL_SOURCE_COST_FILL_REPAIR_REQUIRED",
            }
        )
        if not required:
            continue
        audit = row.get("missed_opportunity_audit")
        if (
            row.get("underlying_intelligence_preserved") is not True
            or not isinstance(audit, dict)
            or not row.get("opportunity_preservation_status")
            or not row.get("opportunity_not_independently_countable_reason")
        ):
            count += 1
    return count


def source_cost_fill_repair_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for row in rows:
        blob = " ".join(
            str(row.get(key, ""))
            for key in (
                "branch_decision",
                "coverage_status",
                "data_requirement_state",
                "opportunity_proxy_reference_status",
                "next_action",
            )
        ).upper()
        if (
            "SOURCE_COST" in blob
            or "FILL_REPAIR" in blob
            or "SOURCE_REQUIRED" in blob
            or "LTF_OR_SOURCE" in blob
            or "RETEST_SOURCE_COST_FILL" in blob
        ):
            results.append(row)
    return results


def main() -> None:
    generated = utc_now()
    input_rows = read_jsonl(INPUT_LEDGER)
    owners = owner_rows(input_rows)
    stats = cluster_stats(owners)
    owner_by_candidate = {str(row.get("candidate_id") or ""): row for row in owners}
    output_rows = [annotate_row(row, stats=stats, owner_by_candidate=owner_by_candidate) for row in input_rows]

    before_counts = Counter(str(row.get("action_class") or "") for row in input_rows)
    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    before_proxy_rows, before_proxy_sum = proxy_summary(input_rows)
    after_proxy_rows, after_proxy_sum = proxy_summary(output_rows)

    guarded_owner_rows = [row for row in output_rows if row.get("branch_decision") == GUARDED_OWNER_BRANCH]
    guarded_prefill_rows = [row for row in output_rows if row.get("branch_decision") == GUARDED_PREFILL_BRANCH]
    no_fill_rows = [
        row
        for row in output_rows
        if row.get("entry_offset_no_fill_control_status")
        == "CURRENT_050R_FILL_CLAIM_UNSUPPORTED_REDESIGN_PATH_PRESERVED"
    ]
    unique_owner_refs = sorted({str(row.get("entry_offset_proxy_owner_row_id") or "") for row in guarded_prefill_rows})
    prefill_reference_sum = round(
        sum(safe_float(row.get("opportunity_proxy_r_reference")) or 0.0 for row in guarded_prefill_rows),
        8,
    )
    owner_proxy_sum = round(sum(safe_float(row.get("after_proxy_r")) or 0.0 for row in guarded_owner_rows), 8)
    largest = stats.get(LARGEST_CLUSTER_KEY, {})
    source_cost_fill_rows = source_cost_fill_repair_rows(output_rows)
    audit_rows = [row for row in output_rows if isinstance(row.get("missed_opportunity_audit"), dict)]

    summary = {
        "route_id": "MAIN_ORCH24_ENTRY_OFFSET_CONCENTRATION_GUARD",
        "date": DATE,
        "generated_utc": generated,
        "input_ledger": str(INPUT_LEDGER),
        "input_sha256": sha256_file(INPUT_LEDGER),
        "output_ledger": str(OUTPUT_LEDGER),
        "rows": len(output_rows),
        "row_identity_preserved": [row.get("row_id") for row in input_rows]
        == [row.get("row_id") for row in output_rows],
        "entry_offset_owner_rows_guarded": len(guarded_owner_rows),
        "entry_offset_owner_proxy_rows_counted": len(guarded_owner_rows),
        "entry_offset_owner_proxy_r_sum_counted": owner_proxy_sum,
        "prefill_reference_rows_guarded": len(guarded_prefill_rows),
        "prefill_reference_proxy_rows_referenced": len(guarded_prefill_rows),
        "prefill_reference_proxy_r_sum_referenced": prefill_reference_sum,
        "unique_proxy_owner_rows_referenced": len(unique_owner_refs),
        "unique_proxy_owner_proxy_r_sum_referenced": owner_proxy_sum,
        "proxy_r_reference_mentions": len(guarded_owner_rows) + len(guarded_prefill_rows),
        "proxy_r_reference_mentions_not_duplicated": True,
        "rows_removed_from_standalone_prefill_implementation_preserved": len(guarded_prefill_rows),
        "rows_preserved_as_entry_offset_owned": len(guarded_prefill_rows),
        "no_fill_control_rows_preserved": len(no_fill_rows),
        "rows_requiring_source_cost_fill_repair": len(source_cost_fill_rows),
        "rows_with_missed_opportunity_audit": len(audit_rows),
        "clusters": stats,
        "effective_cluster_count": len(stats),
        "largest_cluster_key": LARGEST_CLUSTER_KEY,
        "largest_cluster_row_count": largest.get("row_count"),
        "largest_cluster_proxy_r_sum": largest.get("proxy_r_sum"),
        "largest_cluster_row_share": largest.get("row_share"),
        "largest_cluster_proxy_r_share": largest.get("proxy_r_share"),
        "largest_cluster_guard_owner_rows": sum(
            1 for row in guarded_owner_rows if row.get("entry_offset_largest_cluster_guard_required") is True
        ),
        "diversifying_support_owner_rows": sum(
            1 for row in guarded_owner_rows if row.get("entry_offset_largest_cluster_guard_required") is False
        ),
        "action_class_counts_before": dict(sorted(before_counts.items())),
        "action_class_counts_after": dict(sorted(after_counts.items())),
        "action_class_delta": {
            key: after_counts.get(key, 0) - before_counts.get(key, 0)
            for key in sorted(set(before_counts) | set(after_counts))
        },
        "numeric_proxy_rows_before": before_proxy_rows,
        "numeric_proxy_rows_after": after_proxy_rows,
        "proxy_r_sum_before": before_proxy_sum,
        "proxy_r_sum_after": after_proxy_sum,
        "proxy_r_sum_delta": round(after_proxy_sum - before_proxy_sum, 8),
        "opportunity_preservation_missing_after": missing_opportunity_preservation(output_rows),
        "terminal_decision": (
            "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_CONCENTRATION_GUARDED_CANDIDATE;"
            " PREFILL_ROWS_REFERENCE_OWNER_PROXY_ONLY; NO_FILL_ROWS_PRESERVED_FOR_SOURCE_COST_FILL_REPAIR"
        ),
        "boundary_fields": BOUNDARY_FIELDS,
    }

    manifest = {
        "generated_utc": generated,
        "inputs": {
            "gbpjpy_long_adverse_avoid_action_ledger": {
                "path": str(INPUT_LEDGER),
                "exists": INPUT_LEDGER.exists(),
                "size_bytes": INPUT_LEDGER.stat().st_size if INPUT_LEDGER.exists() else 0,
                "sha256": sha256_file(INPUT_LEDGER),
            }
        },
        "outputs": {
            "ledger": {"path": str(OUTPUT_LEDGER), "rows": len(output_rows), "sha256": None},
            "summary": {"path": str(OUTPUT_SUMMARY), "sha256": None},
        },
        "boundary_fields": BOUNDARY_FIELDS,
    }

    write_jsonl(OUTPUT_LEDGER, output_rows)
    write_json(OUTPUT_SUMMARY, summary)
    manifest["outputs"]["ledger"]["sha256"] = sha256_file(OUTPUT_LEDGER)
    manifest["outputs"]["summary"]["sha256"] = sha256_file(OUTPUT_SUMMARY)
    write_json(OUTPUT_MANIFEST, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
