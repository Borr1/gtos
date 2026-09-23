"""Consume moonshot source-provenance evidence for remaining no-scalar rows.

After the NAS100 tick-order repair, the action ledger has nine pure
PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR rows. The moonshot unified
replay/acquisition ledger has branch-level provenance decisions for those same
source branch IDs. It also marks them as excluded from scalar implementation
ranking. This plate therefore preserves the R-style proxy as reference-only
evidence, replaces the generic no-scalar branch with explicit provenance
requirements, and keeps the counted proxy denominator unchanged.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_SUMMARY_{DATE}.json"

MOONSHOT_ROOT = Path(r"")
MOONSHOT_SOURCE_DIR = (
    MOONSHOT_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
MOONSHOT_LEDGER_GLOB = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_VARIANT_REPLAY_ACQUISITION_"
    "BRANCH_KEEP_KILL_REDESIGN_IMPLEMENT_LEDGER_2026-05-17.jsonl"
)

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

GENERIC_BRANCH = "PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR"
POSITIVE_BRANCH = "PRESERVE_SOURCE_PROVENANCE_EXCLUDE_SCALAR_POSITIVE_RSTYLE_REFERENCE"
NEGATIVE_BRANCH = "PRESERVE_SOURCE_PROVENANCE_EXCLUDE_SCALAR_NEGATIVE_RSTYLE_REFERENCE_AVOID_CONTEXT"

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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_no"] = line_no
                rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def long_path(path: Path) -> str:
    resolved = str(path.resolve())
    if resolved.startswith("\\\\?\\"):
        return resolved
    return "\\\\?\\" + resolved


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(long_path(path), "rb") as handle:
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


def git_snapshot() -> dict[str, Any]:
    if not MOONSHOT_ROOT.exists():
        return {"path": str(MOONSHOT_ROOT), "exists": False, "status": "MISSING"}
    command_base = [
        "git",
        "-c",
        "core.excludesfile=",
        "-c",
        "safe.directory=C:/tmp/",
        "-C",
        str(MOONSHOT_ROOT),
    ]
    head = subprocess.run(
        [*command_base, "rev-parse", "--short", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    status = subprocess.run(
        [*command_base, "status", "--short"],
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "path": str(MOONSHOT_ROOT),
        "exists": True,
        "head_short": head.stdout.strip() if head.returncode == 0 else None,
        "head_error": head.stderr.strip() if head.returncode != 0 else None,
        "status_short": [line for line in status.stdout.splitlines() if line.strip()] if status.returncode == 0 else None,
        "status_error": status.stderr.strip() if status.returncode != 0 else None,
        "is_dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
    }


def moonshot_ledger_path() -> Path:
    matches = [
        MOONSHOT_SOURCE_DIR / name
        for name in os.listdir(long_path(MOONSHOT_SOURCE_DIR))
        if name == MOONSHOT_LEDGER_GLOB
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one moonshot source ledger, got {len(matches)}")
    return matches[0]


def read_moonshot_rows(path: Path) -> dict[str, dict[str, Any]]:
    by_branch: dict[str, dict[str, Any]] = {}
    with open(long_path(path), "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            branch_id = row.get("branch_queue_id")
            if isinstance(branch_id, str):
                row["_source_line_no"] = line_no
                by_branch[branch_id] = row
    return by_branch


def target_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("action_class") == "PRESERVE_REQUIREMENT"
        and row.get("branch_decision") == GENERIC_BRANCH
    ]


def source_branch_id(row: dict[str, Any]) -> str:
    for key in ("source_branch_queue_id", "branch_queue_id"):
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    audit = row.get("missed_opportunity_audit") or {}
    path_status = audit.get("path_status") if isinstance(audit, dict) else {}
    value = path_status.get("source_branch_queue_id") if isinstance(path_status, dict) else None
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"row lacks source branch id: {row.get('row_id')}")


def moonshot_reference_payload(source: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "branch_queue_id",
        "branch_keep_kill_redesign_implement_id",
        "branch_action_execution_id",
        "route_candidate_id",
        "route_session",
        "symbol",
        "side",
        "horizon_id",
        "entry_variant",
        "target_stop_contract_id",
        "target_stop_result",
        "primary_export_family",
        "action_execution_class",
        "keep_kill_redesign_implement_replay_decision",
        "unified_execution_decision",
        "candidate_score_class",
        "candidate_score_proxy",
        "rstyle_lower_mean",
        "rstyle_midpoint_mean",
        "rstyle_upper_mean",
        "rstyle_proxy_signal_class",
        "sealed_or_proxy_outcome_status",
        "implementation_implication",
        "exact_failure_cause",
        "exact_missing_geometry_or_source_reason",
        "source_confidence_status",
        "ambiguity_status",
    ]
    return {key: source.get(key) for key in keys}


def repair_target_row(row: dict[str, Any], *, source: dict[str, Any], source_path: Path, generated: str) -> None:
    midpoint = safe_float(source.get("rstyle_midpoint_mean"))
    if midpoint is None:
        raise ValueError(f"moonshot source row lacks rstyle_midpoint_mean: {source.get('branch_queue_id')}")
    candidate_score_proxy = safe_float(source.get("candidate_score_proxy"))
    branch = POSITIVE_BRANCH if midpoint >= 0 else NEGATIVE_BRANCH
    downstream_paths = ["source requirement", "context feature", "broader system component"]
    if midpoint < 0 or "AVOID" in str(source.get("exact_failure_cause") or ""):
        downstream_paths.insert(1, "avoid/inverse")
    if "RETEST" in str(source.get("exact_failure_cause") or ""):
        downstream_paths.insert(1, "redesign")

    row["before_source_provenance_reference_action_class"] = row.get("action_class")
    row["before_source_provenance_reference_branch_decision"] = row.get("branch_decision")
    row["source_provenance_reference_repair_generated_utc"] = generated
    row["source_provenance_reference_repair_status"] = "MOONSHOT_UNIFIED_SOURCE_PROVENANCE_CONSUMED_REFERENCE_ONLY"
    row["action_class"] = "PRESERVE_REQUIREMENT"
    row["branch_decision"] = branch
    row["implementation_decision"] = branch
    row["current_action"] = branch
    row["next_action"] = "PRESERVE_SOURCE_PROVENANCE_FOR_CONTEXT_FEATURE_OR_SOURCE_ACQUISITION_NOT_SCALAR_IMPLEMENTATION"
    row["after_strategy_status"] = "PRESERVE_SOURCE_PROVENANCE_REFERENCE_ONLY_EXCLUDED_FROM_SCALAR_IMPLEMENTATION"
    row["after_score_status"] = "REFERENCE_ONLY_MOONSHOT_RSTYLE_EXCLUDED_FROM_SCALAR_SCORER"
    row["after_proxy_r"] = None
    row["proxy_r_delta"] = 0.0
    row["current_claim_proxy_counted"] = False
    row["exact_r"] = None
    row["data_requirement_state"] = "SOURCE_PROVENANCE_REQUIREMENT_WITH_MOONSHOT_RSTYLE_REFERENCE_ONLY"
    row["decision_evidence"] = "MOONSHOT_UNIFIED_REPLAY_SOURCE_PROVENANCE_EXCLUDES_SCALAR_IMPLEMENTATION"
    row["scoring_boundary"] = "RSTYLE_REFERENCE_NOT_COUNTED_BECAUSE_SOURCE_PROVENANCE_BRANCH_EXCLUDED_FROM_SCALAR_RANKING"
    row["implementation_candidate"] = "SOURCE_PROVENANCE_CONTEXT_FEATURE_OR_SOURCE_ACQUISITION_REQUIREMENT"
    row["source_requirement_preserved"] = True
    row["source_requirement_next_action"] = (
        "USE_AS_SOURCE_PROVENANCE_CONTEXT_FEATURE_OR_ACQUIRE_EXACT_SOURCE_BEFORE_ANY_SCALAR_IMPLEMENTATION"
    )
    row["source_provenance_reference_owner_artifact"] = str(source_path)
    row["source_provenance_reference_owner_line"] = source.get("_source_line_no")
    row["source_provenance_reference_branch_queue_id"] = source.get("branch_queue_id")
    row["source_provenance_reference_payload"] = moonshot_reference_payload(source)
    row["source_provenance_rstyle_lower_reference"] = safe_float(source.get("rstyle_lower_mean"))
    row["source_provenance_rstyle_midpoint_reference"] = midpoint
    row["source_provenance_rstyle_upper_reference"] = safe_float(source.get("rstyle_upper_mean"))
    row["source_provenance_candidate_score_proxy_reference"] = candidate_score_proxy
    row["source_provenance_reference_status"] = "REFERENCE_ONLY_NOT_COUNTED_EXCLUDED_FROM_SCALAR_IMPLEMENTATION"
    row["opportunity_preservation_status"] = "SOURCE_PROVENANCE_RSTYLE_REFERENCE_PRESERVED_WITHOUT_COUNTING_IMPLEMENTATION_R"
    row["opportunity_proxy_r_reference"] = midpoint
    row["opportunity_proxy_reference_status"] = "RSTYLE_REFERENCE_ONLY_NOT_COUNTED_SOURCE_PROVENANCE_EXCLUDED_FROM_SCALAR_SCORER"
    row["opportunity_owner_row_id"] = row.get("source_row_id")
    row["opportunity_owner_source_artifact"] = row.get("source_artifact")
    row["opportunity_not_independently_countable_reason"] = (
        "The moonshot unified replay row explicitly classifies this branch as provenance-preserve and excluded from "
        "scalar implementation ranking; exact broker R, executed fill geometry, slippage, and source-proofed scalar "
        "ownership remain absent. The R-style midpoint is therefore reference intelligence, not counted implementation R."
    )
    row["opportunity_useful_mechanism"] = (
        "Source provenance, target/stop result, fillability friction, source-stress, and R-style interval evidence remain "
        "useful as context features, avoid/inverse or retest-redesign cues where adverse, source-acquisition requirements, "
        "and broader system/source-quality components."
    )
    row["opportunity_downstream_paths"] = downstream_paths
    row["underlying_intelligence_preserved"] = True
    row["missed_opportunity_audit"] = {
        "kill_scope": "NOT_KILLED_SOURCE_PROVENANCE_CURRENT_SCALAR_IMPLEMENTATION_CLAIM_REJECTED_ONLY",
        "current_claim": GENERIC_BRANCH,
        "unsupported_reason": "MOONSHOT_UNIFIED_LEDGER_EXCLUDES_BRANCH_FROM_SCALAR_IMPLEMENTATION_RANKING",
        "what_was_tried": (
            "The remaining no-scalar action rows were joined by source branch ID to the moonshot unified replay/acquisition "
            "ledger, including R-style interval references, source confidence, target/stop result, fillability friction, "
            "and unified keep/redesign/implement decision fields."
        ),
        "what_could_make_it_work": (
            "Exact source acquisition, broker-realized fills, executed risk/slippage, or a redesigned context/avoid/retest "
            "component with its own non-duplicated denominator could make this intelligence implementable."
        ),
        "preserve_as": "SOURCE_PROVENANCE_CONTEXT_FEATURE_OR_SOURCE_REQUIREMENT_REFERENCE",
        "next_route": "SOURCE_PROVENANCE_FEATURE_JOIN_OR_EXACT_SOURCE_ACQUISITION_BEFORE_SCALAR_IMPLEMENTATION",
        "path_status": moonshot_reference_payload(source),
    }
    row["safe_flags"] = SAFE_FLAGS
    row["no_live_behavior"] = True
    row["no_shadow_log_append"] = True


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    source_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    moonshot_path = moonshot_ledger_path()
    moonshot_rows = read_moonshot_rows(moonshot_path)
    moonshot_snapshot = git_snapshot()

    before_counts = Counter(str(row.get("action_class") or "") for row in source_rows)
    before_branch_counts = Counter(str(row.get("branch_decision") or "") for row in source_rows)
    before_proxy = proxy_summary(source_rows)
    targets = target_rows(source_rows)
    output_rows: list[dict[str, Any]] = []
    touched: list[dict[str, Any]] = []

    target_branch_ids = {source_branch_id(row) for row in targets}
    missing = sorted(branch_id for branch_id in target_branch_ids if branch_id not in moonshot_rows)
    if missing:
        raise ValueError(f"missing moonshot source branch IDs: {missing}")

    for row in source_rows:
        new = dict(row)
        new.pop("_source_line_no", None)
        if row in targets:
            source = moonshot_rows[source_branch_id(row)]
            repair_target_row(new, source=source, source_path=moonshot_path, generated=generated)
            touched.append(new)
        else:
            new["source_provenance_reference_repair_status"] = "NOT_TARGET_ROW"
        output_rows.append(new)

    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    after_branch_counts = Counter(str(row.get("branch_decision") or "") for row in output_rows)
    after_proxy = proxy_summary(output_rows)
    rstyle_midpoints = [
        float(row["source_provenance_rstyle_midpoint_reference"])
        for row in touched
        if safe_float(row.get("source_provenance_rstyle_midpoint_reference")) is not None
    ]
    candidate_scores = [
        float(row["source_provenance_candidate_score_proxy_reference"])
        for row in touched
        if safe_float(row.get("source_provenance_candidate_score_proxy_reference")) is not None
    ]
    missing_audit = sum(
        1
        for row in output_rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and not row.get("missed_opportunity_audit")
    )
    missing_intel = sum(
        1
        for row in output_rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and row.get("underlying_intelligence_preserved") is not True
    )

    moonshot_stat = os.stat(long_path(moonshot_path))
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
        "generic_no_scalar_preserve_rows_before": before_branch_counts.get(GENERIC_BRANCH, 0),
        "generic_no_scalar_preserve_rows_after": after_branch_counts.get(GENERIC_BRANCH, 0),
        "source_provenance_reference_rows": len(touched),
        "source_provenance_reference_rows_positive_rstyle": sum(value >= 0 for value in rstyle_midpoints),
        "source_provenance_reference_rows_negative_rstyle": sum(value < 0 for value in rstyle_midpoints),
        "source_provenance_rstyle_midpoint_sum_referenced_not_counted": round(sum(rstyle_midpoints), 8),
        "source_provenance_candidate_score_proxy_sum_referenced_not_counted": round(sum(candidate_scores), 8),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "remaining_preserve_requirement_rows": after_counts.get("PRESERVE_REQUIREMENT", 0),
        "remaining_preserve_requirement_branch_counts": dict(
            sorted(
                Counter(
                    str(row.get("branch_decision"))
                    for row in output_rows
                    if row.get("action_class") == "PRESERVE_REQUIREMENT"
                ).items()
            )
        ),
        "remaining_numeric_preserve_requirement_rows": sum(
            1
            for row in output_rows
            if row.get("action_class") == "PRESERVE_REQUIREMENT" and safe_float(row.get("after_proxy_r")) is not None
        ),
        "redesign_preserve_kill_missing_audit_after": missing_audit,
        "redesign_preserve_kill_missing_underlying_intel_after": missing_intel,
        "rows_with_missed_opportunity_audit_after": sum(1 for row in output_rows if row.get("missed_opportunity_audit")),
        "rows_with_underlying_intelligence_preserved_after": sum(
            1 for row in output_rows if row.get("underlying_intelligence_preserved") is True
        ),
        "moonshot_snapshot": {
            **moonshot_snapshot,
            "source_ledger_path": str(moonshot_path),
            "source_ledger_size_bytes": int(moonshot_stat.st_size),
            "source_ledger_sha256": sha256_file(moonshot_path),
            "source_ledger_rows_indexed": len(moonshot_rows),
        },
        "safe_flags": SAFE_FLAGS,
        "research_safety": {
            "changes_live_behavior": False,
            "changes_shadow_log_history": False,
            "changes_prompt_risk_selector_execution": False,
            "opens_exact_r": False,
            "opens_counted_proxy_r": False,
        },
    }
    return output_rows, summary


def build_manifest(summary: dict[str, Any], outputs: list[Path]) -> dict[str, Any]:
    moonshot = summary["moonshot_snapshot"]
    return {
        "route_id": ROUTE_ID,
        "date": DATE,
        "description": "Remaining no-scalar source requirements enriched with moonshot provenance reference evidence.",
        "generated_utc": summary["generated_utc"],
        "inputs": {
            "ledger": {"path": str(INPUT_LEDGER), "sha256": sha256_file(INPUT_LEDGER)},
            "summary": {"path": str(INPUT_SUMMARY), "sha256": sha256_file(INPUT_SUMMARY)},
            "moonshot_source_ledger": {
                "path": moonshot["source_ledger_path"],
                "sha256": moonshot["source_ledger_sha256"],
                "size_bytes": moonshot["source_ledger_size_bytes"],
                "moonshot_head_short": moonshot.get("head_short"),
                "moonshot_dirty": moonshot.get("is_dirty"),
            },
        },
        "outputs": {
            path.name: {"path": str(path), "sha256": sha256_file(path)}
            for path in outputs
            if path.exists()
        },
        "key_counts": {
            "rows": summary["rows"],
            "source_provenance_reference_rows": summary["source_provenance_reference_rows"],
            "generic_no_scalar_preserve_rows_after": summary["generic_no_scalar_preserve_rows_after"],
            "source_provenance_rstyle_midpoint_sum_referenced_not_counted": summary[
                "source_provenance_rstyle_midpoint_sum_referenced_not_counted"
            ],
            "numeric_proxy_rows_after": summary["numeric_proxy_rows_after"],
            "proxy_r_sum_after": summary["proxy_r_sum_after"],
            "remaining_preserve_requirement_rows": summary["remaining_preserve_requirement_rows"],
        },
        "safe_flags": SAFE_FLAGS,
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
