from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_SOURCE_KILL_SCOPE_REDESIGN_LEDGER_2026-05-17.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_AVOID_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_AVOID_MATERIALIZATION_SUMMARY_2026-05-17.json"
OUTPUT_MANIFEST = ROUTE_DIR / "MAIN_ORCH24_GBPJPY_LONG_ADVERSE_AVOID_OUTPUT_MANIFEST_2026-05-17.json"

OLD_BRANCH = "REDESIGN_GBPJPY_LONG_STRUCTURAL_FVG_OB_ADVERSE_CLUSTER_AVOID_FILTER_CANDIDATE"
IMPLEMENT_BRANCH = "IMPLEMENT_DEFAULT_OFF_GBPJPY_LONG_STRUCTURAL_FVG_OB_ADVERSE_AVOID_FILTER"
DUPLICATE_BRANCH = "MERGE_DUPLICATE_GBPJPY_LONG_ADVERSE_AVOID_EVIDENCE_TO_CANONICAL_OWNER"
SOURCE_BRANCH = "REDESIGN_GBPJPY_LONG_ADVERSE_AVOID_FILTER_SOURCE_REQUIRED"
TARGET_STATUS = "RECLASSIFIED_IMPLEMENT_TO_REDESIGN_AVOID_FILTER_CANDIDATE"
CANONICAL_STRATEGY = "V2_STRUCT_COMPOSITE_ANY"
STRATEGY_PRIORITY = {
    "V2_STRUCT_COMPOSITE_ANY": 0,
    "V2_STRUCT_SWING_PROTECTED": 1,
    "FVG_OB_CONFLUENCE_OB_AFTER_FVG": 2,
}
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
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


def target_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("gbpjpy_long_adverse_reclass_status") == TARGET_STATUS
        or row.get("branch_decision") == OLD_BRANCH
    ]


def choose_owners(rows: list[dict[str, Any]]) -> dict[str, str]:
    by_candidate: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        proxy = safe_float(row.get("after_proxy_r"))
        if proxy is None or proxy >= 0:
            continue
        by_candidate.setdefault(str(row.get("candidate_id") or ""), []).append(row)

    owners: dict[str, str] = {}
    for candidate_id, candidate_rows in by_candidate.items():
        selected = sorted(
            candidate_rows,
            key=lambda row: (
                STRATEGY_PRIORITY.get(str(row.get("strategy_id") or ""), 99),
                str(row.get("row_id") or ""),
            ),
        )[0]
        owners[candidate_id] = str(selected.get("row_id") or "")
    return owners


def ensure_audit(row: dict[str, Any], *, status: str, saved_proxy_r: float | None) -> None:
    audit = row.get("missed_opportunity_audit")
    if not isinstance(audit, dict):
        audit = {}
    audit.update(
        {
            "kill_scope": (
                "CURRENT_CLAIM_REDESIGNED_AS_DEFAULT_OFF_AVOID_FILTER"
                if saved_proxy_r is not None
                else "CURRENT_CLAIM_REDESIGNED_NOT_KILLED"
            ),
            "current_claim": "BROAD_GBPJPY_LONG_STRUCTURAL_OR_FVG_OB_DEFAULT_OFF_IMPLEMENTATION",
            "unsupported_reason": "CURRENT_GBPJPY_LONG_STRUCTURAL_FVG_OB_NUMERIC_PROXY_ROWS_ARE_ADVERSE",
            "what_was_tried": "DEDUPED_GBPJPY_LONG_STRUCTURAL_FVG_OB_ADVERSE_ROWS_BY_CANDIDATE_AND_CURRENT_PROXY_R",
            "what_could_make_it_work": (
                "USE_AS_DEFAULT_OFF_AVOID_FILTER_WITH_CANDIDATE_LEVEL_SAVED_R_ACCOUNTING"
                if saved_proxy_r is not None
                else "ACQUIRE_SOURCE_OR_MERGE_WITH_CANONICAL_AVOID_OWNER_BEFORE_COUNTING_SAVED_R"
            ),
            "preserve_as": "GBPJPY_LONG_AVOID_INVERSE_OR_CONTEXT_FILTER_CANDIDATE",
            "next_route": "IMPLEMENT_DEFAULT_OFF_GBPJPY_LONG_ADVERSE_AVOID_FILTER_AND_REPLAY_BY_SESSION_REGIME",
            "path_status": {
                "materialization_status": status,
                "current_claim_proxy_r_reference": row.get("after_proxy_r"),
                "avoid_saved_proxy_r": saved_proxy_r,
                "source_artifact": row.get("source_artifact"),
            },
        }
    )
    row["missed_opportunity_audit"] = audit


def annotate_row(row: dict[str, Any], owners: dict[str, str]) -> dict[str, Any]:
    out = dict(row)
    if out not in target_rows([out]):
        out.setdefault("gbpjpy_long_adverse_avoid_materialization_status", "NOT_TARGET_ROW")
        return out

    before = {
        "action_class": out.get("action_class"),
        "branch_decision": out.get("branch_decision"),
        "implementation_candidate": out.get("implementation_candidate"),
        "implementation_decision": out.get("implementation_decision"),
        "after_proxy_r": out.get("after_proxy_r"),
    }
    for key, value in before.items():
        out[f"before_gbpjpy_long_adverse_avoid_{key}"] = value

    candidate_id = str(out.get("candidate_id") or "")
    row_id = str(out.get("row_id") or "")
    proxy = safe_float(out.get("after_proxy_r"))
    owner_row_id = owners.get(candidate_id)
    is_owner = bool(owner_row_id and row_id == owner_row_id)
    saved_proxy_r = round(-proxy, 8) if is_owner and proxy is not None and proxy < 0 else None

    out["gbpjpy_long_adverse_current_claim_rejection_status"] = (
        "CURRENT_POSITIVE_GBPJPY_LONG_STRUCTURAL_FVG_OB_CLAIM_REJECTED_OR_REDESIGNED"
    )
    out["gbpjpy_long_adverse_current_claim_proxy_r_reference"] = proxy
    out["gbpjpy_long_adverse_current_claim_proxy_reference_status"] = (
        "REFERENCE_ONLY_NEGATIVE_CURRENT_CLAIM_PROXY"
        if proxy is not None
        else "NO_NUMERIC_PROXY_CURRENT_ROW_SOURCE_OR_LTF_REQUIRED"
    )
    out["gbpjpy_long_adverse_avoid_owner_candidate_id"] = candidate_id
    out["gbpjpy_long_adverse_avoid_owner_row_id"] = owner_row_id
    out["gbpjpy_long_adverse_avoid_duplicate_policy"] = (
        "COUNT_SAVED_R_ONCE_PER_CANDIDATE_USING_CANONICAL_STRUCTURAL_COMPOSITE_ROW"
    )
    out["gbpjpy_long_adverse_avoid_saved_proxy_r"] = saved_proxy_r
    out["gbpjpy_long_adverse_avoid_saved_proxy_counted"] = saved_proxy_r is not None

    if saved_proxy_r is not None:
        status = "CANONICAL_AVOID_FILTER_SAVED_R_OWNER"
        out["action_class"] = "IMPLEMENT_DEFAULT_OFF"
        out["branch_decision"] = IMPLEMENT_BRANCH
        out["current_action"] = IMPLEMENT_BRANCH
        out["implementation_candidate"] = IMPLEMENT_BRANCH
        out["implementation_decision"] = IMPLEMENT_BRANCH
        out["decision_evidence"] = (
            "DEDUPED_GBPJPY_LONG_CURRENT_ADVERSE_PROXY_REFERENCE_AS_DEFAULT_OFF_AVOID_FILTER_SAVED_R"
        )
        out["scoring_boundary"] = (
            "CURRENT_NEGATIVE_PROXY_REFERENCE_RETAINED_SAVED_R_COUNTED_SEPARATELY_ON_AVOID_OWNER"
        )
        out["coverage_status"] = "IMPLEMENTATION_CANDIDATE_AVOID_FILTER_WITH_CURRENT_PROXY_SAVED_R"
        out["data_requirement_state"] = "CURRENT_PROXY_R_NEGATIVE_CANONICAL_AVOID_OWNER_MATERIALIZED"
        out["next_action"] = (
            "IMPLEMENT_DEFAULT_OFF_GBPJPY_LONG_ADVERSE_AVOID_FILTER_AND_REPLAY_BY_SESSION_REGIME"
        )
    elif proxy is not None and proxy < 0:
        status = "DUPLICATE_AVOID_FILTER_PROXY_REFERENCE_NOT_COUNTED"
        out["action_class"] = "REDESIGN"
        out["branch_decision"] = DUPLICATE_BRANCH
        out["current_action"] = DUPLICATE_BRANCH
        out["implementation_candidate"] = DUPLICATE_BRANCH
        out["implementation_decision"] = DUPLICATE_BRANCH
        out["decision_evidence"] = "DUPLICATE_GBPJPY_LONG_ADVERSE_PROXY_REFERENCE_MERGED_TO_CANONICAL_AVOID_OWNER"
        out["scoring_boundary"] = "NO_DUPLICATE_SAVED_R_FOR_GBPJPY_LONG_ADVERSE_AVOID_FILTER"
        out["coverage_status"] = "DUPLICATE_AVOID_FILTER_EVIDENCE_MERGED_TO_CANONICAL_OWNER"
        out["data_requirement_state"] = "CURRENT_PROXY_R_NEGATIVE_DUPLICATE_REFERENCE_ONLY"
        out["next_action"] = "MERGE_DUPLICATE_GBPJPY_LONG_ADVERSE_AVOID_EVIDENCE_TO_CANONICAL_OWNER"
    else:
        status = "SOURCE_REQUIRED_BEFORE_AVOID_SAVED_R_COUNT"
        out["action_class"] = "REDESIGN"
        out["branch_decision"] = SOURCE_BRANCH
        out["current_action"] = SOURCE_BRANCH
        out["implementation_candidate"] = "REPAIR_GBPJPY_LONG_ADVERSE_AVOID_FILTER_LTF_OR_SOURCE_PROXY_BEFORE_COUNTING"
        out["implementation_decision"] = SOURCE_BRANCH
        out["decision_evidence"] = "GBPJPY_LONG_ADVERSE_CONTEXT_PRESENT_BUT_CURRENT_ROW_HAS_NO_NUMERIC_PROXY_R"
        out["scoring_boundary"] = "NO_AVOID_SAVED_R_WITHOUT_NUMERIC_CURRENT_CLAIM_PROXY_OR_LTF_REPAIR"
        out["coverage_status"] = "SOURCE_REQUIRED_FOR_AVOID_FILTER_SAVED_R_COUNT"
        out["data_requirement_state"] = "LTF_OR_SOURCE_PROXY_REQUIRED_FOR_GBPJPY_LONG_ADVERSE_AVOID_FILTER"
        out["next_action"] = "REPAIR_GBPJPY_LONG_ADVERSE_LTF_SOURCE_OR_KEEP_AS_CONTEXT_FEATURE"

    out["gbpjpy_long_adverse_avoid_materialization_status"] = status
    out["gbpjpy_long_adverse_avoid_candidate_decision"] = out["branch_decision"]
    out["underlying_intelligence_preserved"] = True
    out["opportunity_preservation_status"] = (
        "GBPJPY_LONG_ADVERSE_CURRENT_CLAIM_REDESIGNED_AS_AVOID_FILTER_OPPORTUNITY_PRESERVED"
    )
    out["opportunity_owner_row_id"] = owner_row_id or out.get("opportunity_owner_row_id") or row_id
    out["opportunity_owner_source_artifact"] = out.get("source_artifact") or out.get("opportunity_owner_source_artifact")
    out["opportunity_proxy_r_reference"] = proxy if proxy is not None else out.get("opportunity_proxy_r_reference")
    out["opportunity_proxy_reference_status"] = out["gbpjpy_long_adverse_current_claim_proxy_reference_status"]
    out["opportunity_not_independently_countable_reason"] = (
        "Current GBPJPY LONG structural/FVG positive claim is unsupported; saved-R is counted only once per candidate on the canonical avoid owner."
    )
    out["opportunity_useful_mechanism"] = (
        "The adverse GBPJPY LONG structural/FVG cluster remains useful as a default-off avoid/inverse/context filter."
    )
    out["opportunity_downstream_paths"] = ["avoid/inverse", "context feature", "redesign", "broader system component"]
    ensure_audit(out, status=status, saved_proxy_r=saved_proxy_r)
    return out


def missing_opportunity_preservation(rows: list[dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        branch = str(row.get("branch_decision") or "")
        required = (
            row.get("action_class") in {"KILL", "REDESIGN"}
            or branch == IMPLEMENT_BRANCH
            or row.get("gbpjpy_long_adverse_avoid_materialization_status")
            in {
                "CANONICAL_AVOID_FILTER_SAVED_R_OWNER",
                "DUPLICATE_AVOID_FILTER_PROXY_REFERENCE_NOT_COUNTED",
                "SOURCE_REQUIRED_BEFORE_AVOID_SAVED_R_COUNT",
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


def main() -> None:
    generated = utc_now()
    input_rows = read_jsonl(INPUT_LEDGER)
    targets = target_rows(input_rows)
    owners = choose_owners(targets)
    output_rows = [annotate_row(row, owners) for row in input_rows]

    before_counts = Counter(str(row.get("action_class") or "") for row in input_rows)
    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    before_proxy_rows, before_proxy_sum = proxy_summary(input_rows)
    after_proxy_rows, after_proxy_sum = proxy_summary(output_rows)
    target_after = target_rows(output_rows)
    saved_rows = [row for row in target_after if row.get("gbpjpy_long_adverse_avoid_saved_proxy_counted") is True]
    duplicate_rows = [
        row
        for row in target_after
        if row.get("gbpjpy_long_adverse_avoid_materialization_status")
        == "DUPLICATE_AVOID_FILTER_PROXY_REFERENCE_NOT_COUNTED"
    ]
    source_rows = [
        row
        for row in target_after
        if row.get("gbpjpy_long_adverse_avoid_materialization_status")
        == "SOURCE_REQUIRED_BEFORE_AVOID_SAVED_R_COUNT"
    ]
    numeric_targets = [row for row in targets if safe_float(row.get("after_proxy_r")) is not None]
    numeric_sum = round(sum(safe_float(row.get("after_proxy_r")) or 0.0 for row in numeric_targets), 8)
    saved_sum = round(sum(safe_float(row.get("gbpjpy_long_adverse_avoid_saved_proxy_r")) or 0.0 for row in saved_rows), 8)

    summary = {
        "route_id": "MAIN_ORCH24_GBPJPY_LONG_ADVERSE_AVOID_MATERIALIZATION",
        "date": DATE,
        "generated_utc": generated,
        "input_ledger": str(INPUT_LEDGER),
        "input_sha256": sha256_file(INPUT_LEDGER),
        "output_ledger": str(OUTPUT_LEDGER),
        "rows": len(output_rows),
        "row_identity_preserved": [row.get("row_id") for row in input_rows] == [row.get("row_id") for row in output_rows],
        "adverse_rows_materialized": len(target_after),
        "current_negative_proxy_reference_rows": len(numeric_targets),
        "current_negative_proxy_reference_sum": numeric_sum,
        "avoid_saved_r_owner_rows": len(saved_rows),
        "avoid_saved_proxy_r_sum": saved_sum,
        "duplicate_proxy_reference_rows": len(duplicate_rows),
        "source_required_rows": len(source_rows),
        "rows_moved_from_redesign_to_implement_default_off": sum(
            1
            for before, after in zip(input_rows, output_rows)
            if before.get("action_class") == "REDESIGN" and after.get("action_class") == "IMPLEMENT_DEFAULT_OFF"
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
        "terminal_decision": "IMPLEMENT_DEFAULT_OFF_GBPJPY_LONG_ADVERSE_AVOID_FILTER_WITH_REFERENCE_ONLY_CURRENT_PROXY_R",
        "safe_flags": SAFE_FLAGS,
    }

    manifest = {
        "generated_utc": generated,
        "outputs": {
            "ledger": {
                "path": str(OUTPUT_LEDGER),
                "rows": len(output_rows),
                "sha256": None,
            },
            "summary": {
                "path": str(OUTPUT_SUMMARY),
                "sha256": None,
            },
        },
        "inputs": {
            "source_kill_scope_ledger": {
                "path": str(INPUT_LEDGER),
                "exists": INPUT_LEDGER.exists(),
                "size_bytes": INPUT_LEDGER.stat().st_size if INPUT_LEDGER.exists() else 0,
                "sha256": sha256_file(INPUT_LEDGER),
            }
        },
        "safe_flags": SAFE_FLAGS,
    }

    write_jsonl(OUTPUT_LEDGER, output_rows)
    write_json(OUTPUT_SUMMARY, summary)
    manifest["outputs"]["ledger"]["sha256"] = sha256_file(OUTPUT_LEDGER)
    manifest["outputs"]["summary"]["sha256"] = sha256_file(OUTPUT_SUMMARY)
    write_json(OUTPUT_MANIFEST, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
