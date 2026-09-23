"""Verifier for the G0 NOFILL historical source-binding synthesis route."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.forward_capture import NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS


PREFIX = "G0_NOFILL_HIST_SYNTHESIS"
ROUTE_ID = "G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW"
TARGET_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "nofill_historical_sealed_validation_partition_and_source_binding"
)
G12_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_nofill_historical_sealed_validation_partition_source_binding_audit"
)

SAFE_FLAG_KEYS = ("validation_safe", "outcome_review_opened", "live_effect")
FORBIDDEN_TRUE_KEYS = (
    "opens_result_scoring",
    "opens_validation",
    "opens_promotion",
    "opens_registry_edit",
    "opens_paid_api_or_databento_route",
    "opens_remote_push",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_mt5_order_account_history_behavior",
    "changes_live_trading_behavior",
    "credentials_touched",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scan_forbidden(obj: Any, path: str = "$") -> list[str]:
    issues: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}"
            if key in SAFE_FLAG_KEYS and value is not False:
                issues.append(f"{child} must be false")
            if key in FORBIDDEN_TRUE_KEYS and value is True:
                issues.append(f"{child} opens a forbidden surface")
            if key == "promotion_verdict" and value != "NO_PROMOTION_VERDICT":
                issues.append(f"{child} must be NO_PROMOTION_VERDICT")
            issues.extend(scan_forbidden(value, child))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            issues.extend(scan_forbidden(value, f"{path}[{idx}]"))
    return issues


def parse_generated_artifacts() -> list[str]:
    issues: list[str] = []
    for path in ROUTE_DIR.glob("*.json"):
        try:
            obj = load_json(path)
        except Exception as exc:  # pragma: no cover
            issues.append(f"{path.name} JSON parse failed: {exc}")
            continue
        issues.extend(scan_forbidden(obj, path.name))
    for path in ROUTE_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if path.name != f"{PREFIX}_NEXT_PROMPT_PACK_2026-05-10.md" and "NO_PROMOTION_VERDICT" not in text:
            issues.append(f"{path.name} missing NO_PROMOTION_VERDICT")
        if "validation_safe=true" in text or "outcome_review_opened=true" in text or "live_effect=true" in text:
            issues.append(f"{path.name} contains true safe flag text")
    return issues


def verify() -> dict[str, Any]:
    issues = parse_generated_artifacts()
    manifest = load_json(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_2026-05-10.json")
    synthesis = load_json(ROUTE_DIR / f"{PREFIX}_ACCEPTED_G12_TARGET_ROUTE_SYNTHESIS_2026-05-10.json")
    zero = load_json(ROUTE_DIR / f"{PREFIX}_ZERO_SEALED_ROW_IMPLICATION_LEDGER_2026-05-10.json")
    reuse = load_json(ROUTE_DIR / f"{PREFIX}_CONTAMINATED_ROW_REUSE_CONSTRAINTS_2026-05-10.json")
    ranking = load_json(ROUTE_DIR / f"{PREFIX}_NEXT_SOURCE_EXPANSION_ROUTE_RANKING_2026-05-10.json")
    requirements = load_json(ROUTE_DIR / f"{PREFIX}_EXACT_SOURCE_EXPANSION_REQUIREMENTS_MATRIX_2026-05-10.json")
    fields = load_json(ROUTE_DIR / f"{PREFIX}_55_FIELD_EXPANSION_BINDING_CHECKLIST_2026-05-10.json")
    gates = load_json(ROUTE_DIR / f"{PREFIX}_VALIDATION_EXECUTION_CLOSED_GATE_LEDGER_2026-05-10.json")
    completion = load_json(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_2026-05-10.json")

    g12_verify = load_json(G12_DIR / "G12_NOFILL_HIST_AUDIT_VERIFICATION_RESULT_2026-05-10.json")
    g12_universe = load_json(
        G12_DIR / "G12_NOFILL_HIST_AUDIT_CAT_V3_UNIVERSE_ZERO_SEALED_RECOMPUTATION_AUDIT_2026-05-10.json"
    )
    target_matrix = load_json(TARGET_DIR / "NOFILL_HISTORICAL_SEALED_VALIDATION_55_FIELD_SOURCE_BINDING_MATRIX_2026-05-10.json")

    if g12_verify.get("ok") is not True:
        issues.append("accepted G12 verification result is not ok")
    if manifest.get("terminal_decision") != "ACCEPT_AS_G0_SOURCE_CONTROL_SYNTHESIS_FOR_NEXT_SEALED_SOURCE_EXPANSION":
        issues.append("manifest terminal decision mismatch")
    if synthesis["canonical_recomputed_facts"]["cat_v3_row_count"] != 298:
        issues.append("synthesis CAT V3 row count must be 298")
    if synthesis["canonical_recomputed_facts"]["sealed_validation_current_committed_nofill_rows"] != 0:
        issues.append("synthesis sealed row count must be 0")
    if zero.get("sealed_validation_current_committed_nofill_rows") != 0:
        issues.append("zero sealed ledger must report 0 sealed rows")
    if reuse.get("contaminated_row_count") != 298:
        issues.append("contaminated reuse ledger must constrain 298 rows")
    if ranking.get("recommended_next_route_id") != "NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET":
        issues.append("recommended next route must be local tick/shadow source expansion builder")
    if any(row.get("validation_execution_allowed") for row in requirements.get("matrix", [])):
        issues.append("requirements matrix opens validation execution")
    if any(row.get("result_or_cost_scoring_allowed") for row in requirements.get("matrix", [])):
        issues.append("requirements matrix opens result/cost scoring")
    if fields.get("field_count") != 55:
        issues.append("field checklist must have 55 fields")
    if set(row["field_name"] for row in fields.get("fields", [])) != set(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS):
        issues.append("field checklist does not match runtime NOFILL contract")
    if fields.get("binding_class_counts") != target_matrix.get("binding_class_counts"):
        issues.append("field binding counts do not match accepted target matrix")
    if manifest.get("future_requirement_count") != 20:
        issues.append("future requirement count must be 20")
    if g12_universe.get("target_family_counts") != {"accepted": 225, "reject": 65, "source_control": 4, "source_impossible": 4}:
        issues.append("G12 family counts changed unexpectedly")
    if any(item.get("opened") for item in gates.get("closed_gates", [])):
        issues.append("closed gate ledger opens a gate")
    if completion.get("completion_standard_satisfied") is not True:
        issues.append("completion audit does not satisfy completion standard")
    if completion.get("can_mark_goal_complete_after_scoped_commits_and_closeout_verification") is not True:
        issues.append("completion audit does not permit closeout after scoped commits")

    for key, path_text in manifest.get("outputs", {}).items():
        path = REPO_ROOT / path_text
        if not path.exists():
            issues.append(f"manifest output missing: {key} -> {path_text}")
    for key, path_text in manifest.get("static_files", {}).items():
        path = REPO_ROOT / path_text
        if not path.exists():
            issues.append(f"manifest static file missing: {key} -> {path_text}")

    for path in ROUTE_DIR.glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            issues.append(f"{path.name} syntax parse failed: {exc}")

    result = {
        "ok": not issues,
        "route_id": ROUTE_ID,
        "schema_version": "g0_nofill_historical_partition_source_binding_synthesis_control_review_verifier_v1",
        "failures": issues,
        "cat_v3_row_count": synthesis["canonical_recomputed_facts"]["cat_v3_row_count"],
        "sealed_validation_current_committed_nofill_rows": zero.get("sealed_validation_current_committed_nofill_rows"),
        "field_count": fields.get("field_count"),
        "future_requirement_count": manifest.get("future_requirement_count"),
        "exact_repair_source_blocker_count": manifest.get("exact_repair_source_blocker_count"),
        "recommended_next_route_id": ranking.get("recommended_next_route_id"),
        "terminal_decision": manifest.get("terminal_decision"),
        "can_mark_goal_complete": not issues,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    (ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_2026-05-10.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
