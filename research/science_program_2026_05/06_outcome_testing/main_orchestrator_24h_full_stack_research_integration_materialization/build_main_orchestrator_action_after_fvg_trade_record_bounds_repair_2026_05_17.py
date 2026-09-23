"""Repair the remaining FVG/OB exact-bounds source requirement from trade record proof.

The current action ledger has one FVG/OB bucket row left as a generic exact-bounds
source requirement. Its owner trade record contains an L2 ``entry_in_fvg`` PASS
with exact FVG bounds, while the OB checks were skipped because the live path was
really fvg_fill. This builder consumes that source evidence into the action
ledger without promoting the unsupported FVG/OB confluence claim.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_SUMMARY_{DATE}.json"
TRADE_RECORD = REPO_ROOT / "knowledge_base" / "trade_records" / "GBPJPY" / "2026-05-04_tokyo_0300.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

TARGET_CANDIDATE_ID = "GBPJPY_2026-05-04T03:00:00+00:00"
TARGET_ROW_ID = "MAIN-ORCH24-ACTION-SRCM15-00021"
TARGET_BRANCH = "PRESERVE_FVG_OB_BUCKET_BOTH_FIRE_EXACT_BOUNDS_REQUIRED"
REPAIRED_BRANCH = "REDESIGN_FVG_OB_BUCKET_REPAIRED_AS_FVG_ONLY_NO_OB_CONFLUENCE"
RELATED_STANDALONE_STRATEGIES = {"V2_STRUCT_FVG_MID_EDGE", "V3_FVG_ONLY_RESCUE_RISK_BANK"}

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_no"] = line_no
                rows.append(row)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "positive_rows": sum(value > 0 for value in values),
        "zero_rows": sum(value == 0 for value in values),
        "negative_rows": sum(value < 0 for value in values),
    }


def action_delta(before: Counter[str], after: Counter[str]) -> dict[str, int]:
    keys = sorted(set(before) | set(after))
    return {
        key: int(after.get(key, 0)) - int(before.get(key, 0))
        for key in keys
        if int(after.get(key, 0)) != int(before.get(key, 0))
    }


def checks_by_name(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    checks = (
        record.get("decision_pipeline", {})
        .get("level2_verification", {})
        .get("checks", [])
    )
    return {
        str(check.get("name")): check
        for check in checks
        if isinstance(check, dict) and check.get("name")
    }


def fvg_repair_payload(record: dict[str, Any]) -> dict[str, Any]:
    checks = checks_by_name(record)
    entry_check = checks.get("entry_in_fvg") or {}
    mso = entry_check.get("mso_value") or {}
    required = {
        "fvg_bottom": safe_float(mso.get("fvg_bottom")),
        "fvg_top": safe_float(mso.get("fvg_top")),
        "fvg_midpoint": safe_float(mso.get("fvg_midpoint")),
        "fvg_type": mso.get("fvg_type"),
        "formation_time": mso.get("formation_time"),
    }
    if entry_check.get("status") != "PASS" or any(value is None for key, value in required.items() if key != "fvg_type"):
        raise ValueError("Trade record does not contain a usable entry_in_fvg PASS with exact bounds")
    ob_check_statuses = {
        name: (checks.get(name) or {}).get("status")
        for name in ("h1_poi_exists", "ob_zone", "entry_in_ob", "sl_beyond_ob")
    }
    return {
        "source_file": str(TRADE_RECORD.relative_to(REPO_ROOT)),
        "source_sha256": sha256_file(TRADE_RECORD),
        "entry_in_fvg_check_status": entry_check.get("status"),
        "entry_in_fvg_detail": entry_check.get("detail"),
        "fvg_bounds": {
            "low": min(required["fvg_bottom"], required["fvg_top"]),  # type: ignore[arg-type]
            "high": max(required["fvg_bottom"], required["fvg_top"]),  # type: ignore[arg-type]
            "bottom": required["fvg_bottom"],
            "top": required["fvg_top"],
            "midpoint": required["fvg_midpoint"],
            "type": required["fvg_type"],
            "formation_time": required["formation_time"],
            "source_status": "MATCHED_M15_FVG_FROM_TRADE_RECORD_L2_ENTRY_IN_FVG",
        },
        "ob_check_statuses": ob_check_statuses,
        "ob_leg_status": (
            "NO_OB_BOUNDS_IN_TRADE_RECORD_L2_OB_CHECKS_SKIPPED_FVG_FILL_PATH"
            if all(status == "SKIP" for status in ob_check_statuses.values())
            else "OB_STATUS_REQUIRES_MANUAL_REVIEW"
        ),
    }


def repair_fvg_ob_row(row: dict[str, Any], repair: dict[str, Any], *, generated: str) -> None:
    proxy_ref = safe_float(row.get("selected_shift_proxy_r"))
    row["before_fvg_trade_record_bounds_repair_action_class"] = row.get("action_class")
    row["before_fvg_trade_record_bounds_repair_branch_decision"] = row.get("branch_decision")
    row["before_fvg_trade_record_bounds_repair_after_proxy_r"] = row.get("after_proxy_r")
    row["fvg_trade_record_bounds_repair_status"] = (
        "FVG_EXACT_BOUNDS_CAPTURED_OB_LEG_NOT_PRESENT_CURRENT_FVG_OB_CLAIM_REDESIGNED"
    )
    row["fvg_trade_record_bounds_repair_generated_utc"] = generated
    row["fvg_trade_record_bounds_repair_source"] = repair
    row["fvg_exact_bounds"] = repair["fvg_bounds"]
    row["ob_bounds_repair_status"] = repair["ob_leg_status"]
    row["action_class"] = "REDESIGN"
    row["branch_decision"] = REPAIRED_BRANCH
    row["implementation_decision"] = REPAIRED_BRANCH
    row["current_action"] = REPAIRED_BRANCH
    row["next_action"] = (
        "MERGE_EXACT_FVG_BOUNDS_INTO_STANDALONE_FVG_ENTRY_LOCK_REDESIGN_OR_CAPTURE_OB_BOUNDS_BEFORE_FVG_OB_CONFLUENCE"
    )
    row["after_score_status"] = "NOT_COUNTED_FVG_ONLY_SOURCE_REPAIR_NOT_FVG_OB_CONFLUENCE"
    row["after_strategy_status"] = "REDESIGN_FVG_OB_CONFLUENCE_AS_FVG_ONLY_OR_CAPTURE_OB_LEG"
    row["after_outcome_status"] = "ENTRY_THEN_SL_REFERENCE_ONLY"
    row["after_proxy_r"] = None
    row["proxy_r_delta"] = None
    row["data_requirement_state"] = "FVG_BOUNDS_REPAIRED_OB_BOUNDS_ABSENT_CURRENT_CLAIM_NOT_INDEPENDENT"
    row["decision_evidence"] = "TRADE_RECORD_L2_ENTRY_IN_FVG_PASS_WITH_OB_CHECKS_SKIPPED"
    row["scoring_boundary"] = "FVG_ONLY_EXACT_BOUNDS_REPAIRED_NOT_FVG_OB_OB_AFTER_FVG_IMPLEMENTATION"
    row["implementation_candidate"] = "REDESIGN_AS_FVG_ONLY_ENTRY_LOCK_OR_REQUIRE_OB_BOUNDS"
    row["opportunity_preservation_status"] = "OPPORTUNITY_PRESERVED_AS_FVG_ONLY_REDESIGN_SOURCE_INTELLIGENCE"
    row["opportunity_proxy_r_reference"] = proxy_ref
    row["opportunity_proxy_reference_status"] = "REFERENCE_ONLY_SHARED_PATH_PROXY_NOT_FVG_OB_IMPLEMENTATION"
    row["opportunity_not_independently_countable_reason"] = (
        "The trade record repairs exact FVG bounds but proves the current both-fire FVG/OB claim lacks an OB leg; "
        "the shared path proxy is referenced only and cannot count as independent FVG/OB confluence performance."
    )
    row["opportunity_useful_mechanism"] = (
        "Exact FVG entry geometry remains useful for standalone FVG entry-lock redesign, FVG/OB source-capture "
        "requirements, and GBPJPY LONG adverse-context analysis."
    )
    row["opportunity_downstream_paths"] = [
        "redesign",
        "source requirement",
        "context feature",
        "broader system component",
    ]
    row["underlying_intelligence_preserved"] = True
    row["missed_opportunity_audit"] = {
        "kill_scope": "NOT_KILLED_CURRENT_FVG_OB_CLAIM_REDESIGNED_ONLY",
        "current_claim": TARGET_BRANCH,
        "unsupported_reason": "EXACT_FVG_BOUNDS_REPAIRED_BUT_OB_LEG_NOT_PRESENT_FOR_FVG_OB_CONFLUENCE",
        "what_was_tried": "Parsed owner trade record L2 verification entry_in_fvg PASS and OB-related SKIP checks.",
        "what_could_make_it_work": (
            "A decision-time OB bounds source plus FVG/OB sequence/overlap arbitration, or redesign as standalone "
            "FVG entry-lock scorer with exact post-lock/reentry source."
        ),
        "preserve_as": "FVG_ONLY_EXACT_BOUNDS_REDESIGN_AND_SOURCE_CAPTURE_REQUIREMENT",
        "next_route": (
            "MERGE_INTO_STANDALONE_FVG_ENTRY_LOCK_REDESIGN_OR_CAPTURE_OB_BOUNDS_BEFORE_FVG_OB_CONFLUENCE"
        ),
        "path_status": {
            "proxy_r_reference": proxy_ref,
            "proxy_reference_status": "REFERENCE_ONLY_NOT_IMPLEMENTATION",
            "source_artifact": str(TRADE_RECORD.relative_to(REPO_ROOT)),
            "fvg_bounds": repair["fvg_bounds"],
            "ob_leg_status": repair["ob_leg_status"],
        },
    }
    row["safe_flags"] = SAFE_FLAGS
    row["no_live_behavior"] = True
    row["no_shadow_log_append"] = True


def enrich_related_standalone_row(row: dict[str, Any], repair: dict[str, Any], *, generated: str) -> None:
    row["standalone_fvg_trade_record_bounds_repair_status"] = (
        "EXACT_FVG_BOUNDS_CAPTURED_REDESIGN_STILL_NEEDS_ENTRY_LOCK_REENTRY_OR_CONDITION_SPLIT"
    )
    row["standalone_fvg_trade_record_bounds_repair_generated_utc"] = generated
    row["standalone_fvg_trade_record_bounds_repair_source"] = repair
    row["fvg_exact_bounds"] = repair["fvg_bounds"]
    row["underlying_intelligence_preserved"] = True
    audit = row.get("missed_opportunity_audit")
    if isinstance(audit, dict):
        audit = dict(audit)
        audit["trade_record_fvg_bounds_repair"] = {
            "source_artifact": str(TRADE_RECORD.relative_to(REPO_ROOT)),
            "fvg_bounds": repair["fvg_bounds"],
            "status": "EXACT_FVG_BOUNDS_REPAIRED_BUT_CURRENT_STANDALONE_SMALL_N_NEGATIVE_CLAIM_REMAINS_REDESIGN",
        }
        row["missed_opportunity_audit"] = audit
    row["safe_flags"] = SAFE_FLAGS
    row["no_live_behavior"] = True
    row["no_shadow_log_append"] = True


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    source_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    repair = fvg_repair_payload(read_json(TRADE_RECORD))
    before_counts = Counter(str(row.get("action_class") or "") for row in source_rows)
    before_proxy = proxy_summary(source_rows)
    output_rows: list[dict[str, Any]] = []
    repaired_target_rows: list[dict[str, Any]] = []
    enriched_related_rows: list[dict[str, Any]] = []

    for row in source_rows:
        new = dict(row)
        new.pop("_source_line_no", None)
        if new.get("row_id") == TARGET_ROW_ID and new.get("branch_decision") == TARGET_BRANCH:
            repair_fvg_ob_row(new, repair, generated=generated)
            repaired_target_rows.append(new)
        elif (
            new.get("candidate_id") == TARGET_CANDIDATE_ID
            and new.get("strategy_id") in RELATED_STANDALONE_STRATEGIES
            and new.get("branch_decision") == "REDESIGN_STANDALONE_FVG_POI_SCORER_CURRENT_PROXY_NEGATIVE_SMALL_N"
        ):
            enrich_related_standalone_row(new, repair, generated=generated)
            enriched_related_rows.append(new)
        else:
            new["fvg_trade_record_bounds_repair_status"] = "NOT_TARGET_ROW"
        output_rows.append(new)

    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    after_proxy = proxy_summary(output_rows)
    missing_audit = sum(
        1
        for row in output_rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and not row.get("missed_opportunity_audit")
    )
    proxy_refs = [safe_float(row.get("opportunity_proxy_r_reference")) for row in repaired_target_rows]
    proxy_refs = [value for value in proxy_refs if value is not None]

    summary = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated,
        "input_ledger": str(INPUT_LEDGER),
        "input_summary": str(INPUT_SUMMARY),
        "input_rows": input_summary.get("rows"),
        "rows": len(output_rows),
        "exact_r_rows": sum(1 for row in output_rows if safe_float(row.get("exact_r")) is not None),
        "action_class_counts_before": dict(sorted(before_counts.items())),
        "action_class_counts_after": dict(sorted(after_counts.items())),
        "action_class_delta_vs_previous": action_delta(before_counts, after_counts),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "target_fvg_ob_requirement_rows_repaired": len(repaired_target_rows),
        "related_standalone_fvg_rows_enriched": len(enriched_related_rows),
        "proxy_r_rows_referenced_not_counted": len(proxy_refs),
        "proxy_r_sum_referenced_not_counted": round(sum(proxy_refs), 8),
        "remaining_fvg_ob_exact_bounds_requirement_rows": sum(
            1 for row in output_rows if row.get("branch_decision") == TARGET_BRANCH
        ),
        "rows_requiring_source_cost_fill_repair_after": sum(
            1 for row in output_rows if row.get("action_class") == "PRESERVE_REQUIREMENT"
        ),
        "redesign_preserve_kill_missing_audit_after": missing_audit,
        "repair_source": repair,
        "safe_flags": SAFE_FLAGS,
        "research_safety": {
            "changes_live_behavior": False,
            "changes_shadow_log_history": False,
            "changes_prompt_risk_selector_execution": False,
            "opens_exact_r": False,
        },
    }
    return output_rows, summary


def build_manifest(summary: dict[str, Any], outputs: list[Path]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": summary["generated_utc"],
        "inputs": {
            str(INPUT_LEDGER): sha256_file(INPUT_LEDGER),
            str(INPUT_SUMMARY): sha256_file(INPUT_SUMMARY),
            str(TRADE_RECORD): sha256_file(TRADE_RECORD),
        },
        "outputs": {str(path): sha256_file(path) for path in outputs if path.exists()},
        "safe_flags": SAFE_FLAGS,
        "summary": summary,
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary, [OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    write_json(OUTPUT_MANIFEST, build_manifest(summary, [OUTPUT_LEDGER, OUTPUT_SUMMARY, OUTPUT_MANIFEST]))
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
