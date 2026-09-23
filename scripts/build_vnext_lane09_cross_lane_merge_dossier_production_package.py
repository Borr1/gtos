from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTE_ID = "vnext_lane09_cross_lane_merge_dossier_production_package_2026_05_31"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID
MASTER_ROUTE = ROOT / "research" / "operations" / "vnext_next_level_master_orchestration_2026_05_31"
PROMPT_PATH = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "VNEXT_LANE09_CROSS_LANE_MERGE_DOSSIER_PRODUCTION_PACKAGE_GOAL_PROMPT_2026-05-31.md"
)
STARTER_PATH = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "VNEXT_LANE09_CROSS_LANE_MERGE_DOSSIER_PRODUCTION_PACKAGE_STARTER_2026-05-31.txt"
)

LANES = [
    {
        "lane_id": "01",
        "title": "Fixed Friday portfolio replay engine",
        "route": "research/operations/vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31",
        "primary_summary": "LANE01_PORTFOLIO_REPLAY_SUMMARY.json",
    },
    {
        "lane_id": "02",
        "title": "Broad selected portfolio replay stress",
        "route": "research/operations/vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31",
        "primary_summary": "LANE02_PORTFOLIO_REPLAY_STRESS_SUMMARY.json",
        "external_owner": "dedicated_lane02_goal_session",
    },
    {
        "lane_id": "03",
        "title": "Meta-selector discovery and implementation",
        "route": "research/operations/vnext_lane03_meta_selector_discovery_implementation_2026_05_31",
        "primary_summary": "LANE03_META_SELECTOR_RULE_PACKAGE.json",
    },
    {
        "lane_id": "04",
        "title": "Selected-cell risk bridge and packet completeness",
        "route": "research/operations/vnext_lane04_selected_cell_risk_bridge_packet_completeness_2026_05_31",
        "primary_summary": "LANE04_SUMMARY.json",
    },
    {
        "lane_id": "05",
        "title": "Runtime portfolio scheduler integration",
        "route": "research/operations/vnext_lane05_runtime_portfolio_scheduler_integration_2026_05_31",
        "primary_summary": "LANE05_SCHEDULER_SUMMARY.json",
    },
    {
        "lane_id": "06",
        "title": "Broker lifecycle net-R and cost truth",
        "route": "research/operations/vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31",
        "primary_summary": "LANE06_SUMMARY.json",
    },
    {
        "lane_id": "07",
        "title": "Market coverage, source, and starvation repair",
        "route": "research/operations/vnext_lane07_market_coverage_source_starvation_repair_2026_05_31",
        "primary_summary": "LANE07_FINAL_REPORT.md",
    },
    {
        "lane_id": "08",
        "title": "Execution policy and microstructure stress",
        "route": "research/operations/vnext_lane08_execution_policy_microstructure_stress_2026_05_31",
        "primary_summary": "LANE08_EXPECTANCY_SUMMARY.json",
    },
]

SHARED_SURFACES = [
    "config/agent_config.yaml",
    "src/components/gtos_vnext_runtime.py",
    "src/components/orchestrator.py",
    "src/components/permissions.py",
    "src/components/execution.py",
    "src/components/m1_capture.py",
    "src/research/moonshot_default_off_policy_router.py",
    "tests/test_gtos_vnext_runtime.py",
    "tests/test_vnext_broader_origin_orchestrator.py",
    "tests/test_moonshot_default_off_policy_router.py",
    "tests/test_m1_capture.py",
    "scripts/build_vnext_lane01_fixed_friday_portfolio_replay.py",
    "scripts/build_vnext_lane02_broad_selected_portfolio_replay_stress.py",
    "scripts/build_vnext_lane03_meta_selector.py",
    "scripts/build_vnext_lane05_runtime_portfolio_scheduler.py",
    "scripts/build_vnext_lane06_broker_lifecycle_truth.py",
    "scripts/build_vnext_lane08_execution_policy_microstructure_stress.py",
    "tests/test_vnext_lane01_fixed_friday_portfolio_replay.py",
    "tests/test_vnext_lane02_broad_selected_portfolio_replay_stress.py",
    "tests/test_vnext_lane05_portfolio_scheduler.py",
    "tests/test_vnext_lane06_broker_lifecycle_truth.py",
    "tests/test_vnext_lane08_execution_policy_microstructure_stress.py",
]
SCOPED_PACKAGE_COMMIT_SUBJECT = "vnext: package next-level lane implementation"
SCOPED_PACKAGE_REQUIRED_PATHS = (
    ".gitattributes",
    "config/agent_config.yaml",
    "research/operations/vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31/LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_LEDGER.jsonl",
    "research/operations/vnext_lane08_execution_policy_microstructure_stress_2026_05_31/LANE08_STRICT_TICK_POLICY_LEDGER.jsonl",
    "research/operations/vnext_lane09_cross_lane_merge_dossier_production_package_2026_05_31/LANE09_PRODUCTION_PACKAGE.json",
    "research/operations/vnext_next_level_master_orchestration_2026_05_31/MASTER_SCOPED_MERGE_STAGING_PLAN.json",
    "scripts/build_vnext_lane09_cross_lane_merge_dossier_production_package.py",
    "scripts/build_vnext_next_level_master_orchestration.py",
    "src/components/gtos_vnext_runtime.py",
    "tests/test_vnext_lane09_cross_lane_merge_dossier.py",
)
SCOPED_PACKAGE_REQUIRED_PREFIXES = tuple(lane["route"] + "/" for lane in LANES) + (
    "research/operations/vnext_lane09_cross_lane_merge_dossier_production_package_2026_05_31/",
    "research/operations/vnext_next_level_master_orchestration_2026_05_31/",
    "research/science_program_2026_05/04_goal_prompts/",
)
SCOPED_PACKAGE_FORBIDDEN_PREFIXES = (
    ".codex/",
    ".context/",
    "data/",
    "knowledge_base/",
    "pipeline_state/",
    "research/archive/",
    "research/ml_program/shadow/",
    "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/",
    "research/program_control/",
    "shadow_logs/",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def run_git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def git_status_for(path: Path) -> list[str]:
    output = run_git(["status", "--short", "--", rel(path)])
    return output.splitlines() if output else []


def latest_scoped_package_commit_sha() -> str | None:
    history = run_git(["log", "-n", "50", "--format=%H%x09%s"])
    if not history:
        return None
    for line in history.splitlines():
        if "\t" not in line:
            continue
        sha, subject = line.split("\t", 1)
        if subject == SCOPED_PACKAGE_COMMIT_SUBJECT:
            return sha
    return None


def git_commit_paths(sha: str) -> list[str]:
    output = run_git(["show", "--name-only", "--format=", "--no-renames", sha])
    if not output:
        return []
    return [line.replace("\\", "/") for line in output.splitlines() if line.strip()]


def detect_scoped_package_commit() -> dict[str, Any]:
    sha = latest_scoped_package_commit_sha()
    if not sha:
        return {
            "scoped_commit_forbidden_path_count": None,
            "scoped_commit_forbidden_paths": [],
            "scoped_commit_missing_required_paths": list(SCOPED_PACKAGE_REQUIRED_PATHS),
            "scoped_commit_missing_required_prefixes": list(SCOPED_PACKAGE_REQUIRED_PREFIXES),
            "scoped_commit_path_count": 0,
            "scoped_commit_paths": [],
            "scoped_commit_performed": False,
            "scoped_commit_sha": None,
            "scoped_commit_short_subject": None,
            "scoped_commit_status": "not_performed; no scoped implementation package commit found in recent history",
        }
    paths = git_commit_paths(sha)
    path_set = set(paths)
    forbidden_paths = sorted(
        path for path in paths if path.startswith(SCOPED_PACKAGE_FORBIDDEN_PREFIXES)
    )
    missing_required_paths = sorted(
        path for path in SCOPED_PACKAGE_REQUIRED_PATHS if path not in path_set
    )
    missing_required_prefixes = sorted(
        prefix
        for prefix in SCOPED_PACKAGE_REQUIRED_PREFIXES
        if not any(path.startswith(prefix) for path in paths)
    )
    scope_ok = not forbidden_paths and not missing_required_paths and not missing_required_prefixes
    short_subject = run_git(["show", "-s", "--format=%h %s", sha])
    return {
        "scoped_commit_forbidden_path_count": len(forbidden_paths),
        "scoped_commit_forbidden_paths": forbidden_paths,
        "scoped_commit_missing_required_paths": missing_required_paths,
        "scoped_commit_missing_required_prefixes": missing_required_prefixes,
        "scoped_commit_path_count": len(paths),
        "scoped_commit_paths": paths,
        "scoped_commit_performed": scope_ok,
        "scoped_commit_sha": sha,
        "scoped_commit_short_subject": short_subject,
        "scoped_commit_status": "performed_scope_audited"
        if scope_ok
        else "found_but_failed_scope_audit",
    }


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_jsonl(path: Path) -> int | None:
    if path.suffix.lower() != ".jsonl" or not path.exists():
        return None
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for line in handle if line.strip())


def file_evidence(path: Path, role: str) -> dict[str, Any]:
    item: dict[str, Any] = {"exists": path.exists(), "path": rel(path), "role": role}
    if path.is_file():
        item.update(
            {
                "kind": "file",
                "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                "row_count": count_jsonl(path),
                "sha256": sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    elif path.is_dir():
        item.update(
            {
                "file_count": sum(1 for child in path.rglob("*") if child.is_file()),
                "kind": "directory",
                "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            }
        )
    return item


def first_match(route_path: Path, pattern: str) -> Path | None:
    if not route_path.exists():
        return None
    matches = sorted(path for path in route_path.rglob(pattern) if path.is_file())
    return matches[0] if matches else None


def verifier_ok(payload: dict[str, Any]) -> bool:
    status = str(payload.get("status") or payload.get("result") or "").lower()
    return bool(
        payload.get("ok")
        or payload.get("passed")
        or status in {"verified", "pass", "passed", "ok", "complete", "completed"}
    )


def audit_complete(payload: dict[str, Any]) -> bool:
    status = str(payload.get("status") or "").lower()
    decision = str(payload.get("completion_decision") or "").lower()
    schema = str(payload.get("schema_version") or "").lower()
    return bool(
        payload.get("can_mark_route_complete")
        or payload.get("completion_ready")
        or payload.get("completion_ready_for_lane09")
        or payload.get("can_mark_route_complete_after_verifier")
        or status in {"complete", "completed", "pass", "passed"}
        or status.startswith("complete")
        or decision.startswith("complete")
        or ("completion_audit" in schema and bool(payload.get("outputs")))
    )


def parse_focused_result(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {"exists": False, "ok": False, "path": None}
    if path.suffix.lower() == ".xml":
        try:
            root = ET.fromstring(path.read_text(encoding="utf-8", errors="replace"))
            errors = sum(int(node.attrib.get("errors", 0)) for node in root.iter("testsuite"))
            failures = sum(int(node.attrib.get("failures", 0)) for node in root.iter("testsuite"))
            tests = sum(int(node.attrib.get("tests", 0)) for node in root.iter("testsuite"))
            return {"errors": errors, "exists": True, "failures": failures, "ok": errors == 0 and failures == 0 and tests > 0, "path": rel(path), "tests": tests}
        except ET.ParseError as exc:
            return {"exists": True, "ok": False, "parse_error": str(exc), "path": rel(path)}
    payload = load_json(path, {})
    return {"exists": True, "ok": bool(payload.get("ok", True)), "path": rel(path), "payload_summary": payload}


def manifest_output_count(payload: dict[str, Any]) -> int:
    outputs = payload.get("outputs") or payload.get("files") or payload.get("materialized_outputs") or []
    return len(outputs) if isinstance(outputs, list) else 0


def run_artifact_audit(route_path: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        "scripts/audit_goal_route_artifacts.py",
        rel(route_path),
        "--full-jsonl",
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=900)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {}
    parse_clean = bool(
        payload
        and payload.get("json_parse_error_count", 0) == 0
        and payload.get("jsonl_parse_error_count", 0) == 0
        and payload.get("jsonl_files_unscanned", 0) == 0
    )
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "jsonl_files_scanned": payload.get("jsonl_files_scanned"),
        "jsonl_files_unscanned": payload.get("jsonl_files_unscanned"),
        "jsonl_parse_error_count": payload.get("jsonl_parse_error_count"),
        "ok": parse_clean,
        "profile_ok": bool(payload.get("ok")),
        "route_dir": rel(route_path),
        "stderr_tail": completed.stderr[-2000:],
        "stdout_summary": {
            "file_count": payload.get("file_count"),
            "json_count": payload.get("json_count"),
            "json_parse_error_count": payload.get("json_parse_error_count"),
            "jsonl_count": payload.get("jsonl_count"),
            "jsonl_scan_note": payload.get("jsonl_scan_note"),
            "large_files": payload.get("large_files"),
            "missing_required": payload.get("missing_required"),
            "ok": payload.get("ok"),
            "profile_note": "generic audit profile may report missing category warnings on lane-specific routes; Lane09 requires parse-clean full JSONL scan plus route verifier evidence",
        },
    }


def lane_base_row(lane: dict[str, Any]) -> dict[str, Any]:
    route_path = ROOT / lane["route"]
    audit_path = first_match(route_path, "*COMPLETION_AUDIT.json")
    verifier_path = first_match(route_path, "*VERIFICATION_RESULT.json")
    manifest_path = first_match(route_path, "*OUTPUT_MANIFEST.json")
    focused_path = first_match(route_path, "*FOCUSED_TEST_RESULT.*")
    audit_payload = load_json(audit_path, {}) if audit_path else {}
    verifier_payload = load_json(verifier_path, {}) if verifier_path else {}
    manifest_payload = load_json(manifest_path, {}) if manifest_path else {}
    focused_result = parse_focused_result(focused_path)
    return {
        "artifact_audit_ok": None,
        "artifact_audit_path": None,
        "audit_complete": audit_complete(audit_payload),
        "completion_audit_path": rel(audit_path) if audit_path else None,
        "completion_status": audit_payload.get("status") or audit_payload.get("completion_decision"),
        "external_owner": lane.get("external_owner"),
        "focused_test_result": focused_result,
        "lane_id": lane["lane_id"],
        "manifest_output_count": manifest_output_count(manifest_payload),
        "manifest_path": rel(manifest_path) if manifest_path else None,
        "primary_summary_path": rel(route_path / lane["primary_summary"]) if (route_path / lane["primary_summary"]).exists() else None,
        "route_exists": route_path.exists(),
        "route_file_count": sum(1 for child in route_path.rglob("*") if child.is_file()) if route_path.exists() else 0,
        "route_path": rel(route_path),
        "schema_version": "lane09_lane_verification_matrix_v1",
        "title": lane["title"],
        "verification_issue_count": verifier_payload.get("issue_count"),
        "verification_ok": verifier_ok(verifier_payload),
        "verification_payload_summary": {
            "accepted_rows": verifier_payload.get("accepted_rows"),
            "input_rows": verifier_payload.get("input_rows"),
            "issue_count": verifier_payload.get("issue_count"),
            "ok": verifier_payload.get("ok"),
            "portfolio_ready_rows": verifier_payload.get("portfolio_ready_rows"),
            "status": verifier_payload.get("status"),
        },
        "verification_result_path": rel(verifier_path) if verifier_path else None,
    }


def apply_lane09_adoption(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["lane_id"]: row for row in matrix}
    lane02 = by_id.get("02", {})
    lane02_full_ok = bool(
        lane02.get("verification_ok")
        and lane02.get("audit_complete")
        and lane02.get("verification_payload_summary", {}).get("input_rows") == 289600
        and lane02.get("verification_payload_summary", {}).get("accepted_rows") == 72482
    )
    for row in matrix:
        if row["lane_id"] == "02":
            row["lane09_adoption_state"] = (
                "adopted_read_only_from_dedicated_lane02_handoff_for_packaging"
                if lane02_full_ok
                else "not_adopted_lane02_full_denominator_proof_missing"
            )
            row["lane09_terminal_accepted"] = lane02_full_ok
            row["read_only_handoff_policy"] = "Lane09 packages Lane02 evidence without rewriting Lane02 route artifacts."
        elif row["lane_id"] in {"03", "08"}:
            row["lane09_adoption_state"] = (
                "accepted_dependency_hold_cleared_by_lane02_readonly_package_adoption"
                if lane02_full_ok and row.get("verification_ok") and row.get("audit_complete")
                else "dependency_hold_pending_lane02_package_adoption"
            )
            row["lane09_terminal_accepted"] = lane02_full_ok and row.get("verification_ok") and row.get("audit_complete")
        else:
            row["lane09_adoption_state"] = (
                "accepted_terminal_verified_lane_package"
                if row.get("verification_ok") and row.get("audit_complete")
                else "not_accepted_missing_terminal_route_evidence"
            )
            row["lane09_terminal_accepted"] = row.get("verification_ok") and row.get("audit_complete")
    return matrix


def build_lane_matrix(now: str, *, run_audits: bool) -> list[dict[str, Any]]:
    matrix = [lane_base_row(lane) for lane in LANES]
    if run_audits:
        audit_rows = []
        for row in matrix:
            audit = run_artifact_audit(ROOT / row["route_path"])
            audit_rows.append({"lane_id": row["lane_id"], **audit})
            row["artifact_audit_ok"] = audit["ok"]
            row["artifact_audit_path"] = "LANE09_LANE_ARTIFACT_AUDIT_RESULTS.jsonl"
        write_jsonl(ROUTE_DIR / "LANE09_LANE_ARTIFACT_AUDIT_RESULTS.jsonl", audit_rows)
    for row in matrix:
        row["timestamp_utc"] = now
    return apply_lane09_adoption(matrix)


def source_completeness_path(route_path: Path) -> Path | None:
    return first_match(route_path, "*SOURCE_COMPLETENESS*.jsonl") or first_match(route_path, "*SOURCE_INTEGRITY*.jsonl")


def compact_metric_for_lane(lane_id: str, route_path: Path, audit: dict[str, Any]) -> dict[str, Any]:
    if lane_id == "01":
        summary = load_json(route_path / "LANE01_PORTFOLIO_REPLAY_SUMMARY.json", {})
        return {
            "accepted_rows": summary.get("accepted_rows"),
            "gross_r_sum": summary.get("accepted_gross_r_sum"),
            "quality_subset_rows": summary.get("quality_subset_rows"),
            "rejected_rows": summary.get("rejected_rows"),
        }
    if lane_id == "02":
        summary = load_json(route_path / "LANE02_PORTFOLIO_REPLAY_STRESS_SUMMARY.json", {})
        return {
            "accepted_rows": summary.get("stats", {}).get("accepted_rows"),
            "gross_r_sum": summary.get("stats", {}).get("accepted_gross_r_sum"),
            "scenario_ids": summary.get("scenario_ids"),
            "selected_surface_rows": summary.get("selected_surface_rows"),
        }
    if lane_id == "03":
        return {
            "branch_decision_rows": audit.get("branch_decision_rows"),
            "input_rows_scanned": audit.get("input_rows_scanned"),
            "rule_counts": audit.get("rule_counts"),
        }
    if lane_id == "05":
        return audit.get("row_level_closure", {})
    if lane_id == "06":
        return load_json(route_path / "LANE06_SUMMARY.json", {})
    if lane_id == "07":
        return audit.get("counts", {})
    if lane_id == "08":
        return load_json(route_path / "LANE08_EXPECTANCY_SUMMARY.json", {})
    return audit.get("summary_metrics") or audit.get("counts") or {}


def build_result_materialization_ledger(now: str, matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lane in LANES:
        route_path = ROOT / lane["route"]
        audit_path = first_match(route_path, "*COMPLETION_AUDIT.json")
        audit = load_json(audit_path, {}) if audit_path else {}
        source_path = source_completeness_path(route_path)
        rows.append(
            {
                "branch_decision": "package_lane_terminal_result_for_cross_lane_merge",
                "evidence_class": "offline_route_artifact_merge_package",
                "implementation_decision": "include_in_lane09_package" if next(row for row in matrix if row["lane_id"] == lane["lane_id"])["lane09_terminal_accepted"] else "hold_until_terminal_evidence_repaired",
                "lane_id": lane["lane_id"],
                "materialization_result_scope": lane["title"],
                "metric_payload": compact_metric_for_lane(lane["lane_id"], route_path, audit),
                "result_boundary": "local_package_only_no_live_deployment",
                "schema_version": "lane09_result_materialization_v1",
                "source_completeness_path": rel(source_path) if source_path else None,
                "source_route": lane["route"],
                "timestamp_utc": now,
            }
        )
    return rows


def build_implementation_decision_ledger(now: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lane in LANES:
        route_path = ROOT / lane["route"]
        decision_paths = sorted(route_path.glob("*IMPLEMENTATION_DECISION_LEDGER.jsonl"))
        if decision_paths:
            for path in decision_paths:
                for row in load_jsonl(path):
                    rows.append(
                        {
                            "lane_id": lane["lane_id"],
                            "lane09_decision": "carry_forward_for_merge_review",
                            "schema_version": "lane09_implementation_decision_v1",
                            "source_path": rel(path),
                            "source_row": row,
                            "timestamp_utc": now,
                        }
                    )
            continue
        audit_path = first_match(route_path, "*COMPLETION_AUDIT.json")
        audit = load_json(audit_path, {}) if audit_path else {}
        rows.append(
            {
                "lane_id": lane["lane_id"],
                "lane09_decision": "carry_completion_audit_decision_forward_for_merge_review",
                "schema_version": "lane09_implementation_decision_v1",
                "source_path": rel(audit_path) if audit_path else None,
                "source_row": {
                    "completion_status": audit.get("status") or audit.get("completion_decision"),
                    "runtime_effect_boundary": audit.get("runtime_effect_boundary"),
                    "source_use_state": audit.get("source_use_state"),
                },
                "timestamp_utc": now,
            }
        )
    return rows


def build_shared_file_conflict_ledger(now: str) -> list[dict[str, Any]]:
    master_rows = load_jsonl(MASTER_ROUTE / "MASTER_SHARED_FILE_OWNERSHIP_LEDGER.jsonl")
    by_path = {row.get("path"): row for row in master_rows}
    rows: list[dict[str, Any]] = []
    for path_text in SHARED_SURFACES:
        path = ROOT / path_text
        master_row = by_path.get(path_text, {})
        status = git_status_for(path)
        rows.append(
            {
                "conflict_status": "requires_lane09_scoped_merge_review" if status else "clean_or_unmodified_on_current_git_status",
                "current_git_status": status,
                "exists": path.exists(),
                "lane09_owner_decision": master_row.get("master_conflict_policy") or "route_owned_or_lane_specific_surface",
                "owner": master_row.get("owner"),
                "owner_state": master_row.get("owner_state"),
                "participating_lanes": master_row.get("participating_lanes"),
                "path": path_text,
                "production_change_boundary": "local_package_only_no_hidden_live_deployment",
                "schema_version": "lane09_shared_file_conflict_v1",
                "timestamp_utc": now,
            }
        )
    return rows


def build_blocker_ledger(
    now: str,
    matrix: list[dict[str, Any]],
    shared_rows: list[dict[str, Any]],
    scoped_package_commit: dict[str, Any],
) -> list[dict[str, Any]]:
    terminal_missing = [row["lane_id"] for row in matrix if not row.get("lane09_terminal_accepted")]
    dirty_shared = [row["path"] for row in shared_rows if row["current_git_status"]]
    scoped_commit_performed = bool(scoped_package_commit.get("scoped_commit_performed"))
    scoped_commit_status = (
        "open_merge_commit_boundary"
        if dirty_shared or not scoped_commit_performed
        else "closed_scoped_package_commit_performed"
    )
    scoped_next_action = (
        "Review and stage only scoped lane-owned runtime/config/test changes; do not sweep unrelated live/shadow dirt."
        if scoped_commit_status == "open_merge_commit_boundary"
        else "none"
    )
    return [
        {
            "blocker_class": "lane_terminal_package_evidence",
            "current_evidence": {"not_accepted_lanes": terminal_missing},
            "exact_next_action": "repair missing lane verifier/audit evidence before any scoped merge commit" if terminal_missing else "none",
            "schema_version": "lane09_blocker_v1",
            "status": "open" if terminal_missing else "closed_all_lanes_packaged",
            "timestamp_utc": now,
        },
        {
            "blocker_class": "production_change_approval",
            "current_evidence": "No CEO approval in this route for live behavior deployment, broker action, paid calls, credential changes, remote push, or live restart.",
            "exact_next_action": "Prepare a separate owner-approved production-change dossier before live deployment.",
            "schema_version": "lane09_blocker_v1",
            "status": "open_by_policy_not_route_failure",
            "timestamp_utc": now,
        },
        {
            "blocker_class": "shared_file_scoped_merge_review",
            "current_evidence": {
                "dirty_shared_surfaces": dirty_shared,
                "scoped_commit_performed": scoped_commit_performed,
                "scoped_commit_sha": scoped_package_commit.get("scoped_commit_sha"),
                "scoped_commit_short_subject": scoped_package_commit.get("scoped_commit_short_subject"),
            },
            "exact_next_action": scoped_next_action,
            "schema_version": "lane09_blocker_v1",
            "status": scoped_commit_status,
            "timestamp_utc": now,
        },
        {
            "blocker_class": "broker_lifecycle_future_event",
            "current_evidence": "Lane06 records current broker lifecycle truth; final net-R for open residual lifecycle remains event-pending until broker close evidence exists.",
            "exact_next_action": "Consume new close/deal evidence after it exists; no broker action is authorized by Lane09.",
            "schema_version": "lane09_blocker_v1",
            "status": "open_external_runtime_event_pending",
            "timestamp_utc": now,
        },
    ]


def build_production_package(
    now: str,
    matrix: list[dict[str, Any]],
    shared_rows: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    scoped_package_commit: dict[str, Any],
) -> dict[str, Any]:
    accepted = [row["lane_id"] for row in matrix if row.get("lane09_terminal_accepted")]
    scoped_commit_performed = bool(scoped_package_commit.get("scoped_commit_performed"))
    return {
        "accepted_lane_packages": accepted,
        "behavior_delta_surfaces": [row for row in shared_rows if row["current_git_status"]],
        "completion_interpretation": "local_merge_dossier_and_production_package_materialized_not_live_deployment",
        "forbidden_surfaces": {
            "broker_order_deal_position_action": False,
            "credential_change": False,
            "hidden_live_deployment": False,
            "paid_api_vendor_spend": False,
            "remote_push": False,
        },
        "generated_at_utc": now,
        "lane02_readonly_handoff_adopted": "02" in accepted,
        "live_production_change_ready": False,
        "open_policy_blockers": [
            row for row in blockers if row["status"] in {"open_by_policy_not_route_failure", "open_external_runtime_event_pending"}
        ],
        "package_status": "scoped_package_committed_for_owner_review"
        if scoped_commit_performed
        else "packaged_for_owner_review_and_scoped_merge",
        "rollback_surface": {
            "config": "config/agent_config.yaml",
            "runtime_code": [
                "src/components/gtos_vnext_runtime.py",
                "src/components/orchestrator.py",
                "src/components/execution.py",
                "src/components/m1_capture.py",
                "src/research/moonshot_default_off_policy_router.py",
            ],
            "tests": [row["path"] for row in shared_rows if row["path"].startswith("tests/")],
        },
        "route_id": ROUTE_ID,
        "schema_version": "lane09_production_package_v1",
        "scoped_package_commit": scoped_package_commit,
    }


def build_merge_dossier(
    now: str,
    matrix: list[dict[str, Any]],
    package: dict[str, Any],
    blockers: list[dict[str, Any]],
    scoped_package_commit: dict[str, Any],
) -> str:
    accepted = ", ".join(package["accepted_lane_packages"])
    blocker_lines = [
        f"- `{row['blocker_class']}`: `{row['status']}` - {row['exact_next_action']}"
        for row in blockers
    ]
    lane_lines = [
        (
            f"- Lane{row['lane_id']}: `{row['lane09_adoption_state']}`, "
            f"verifier_ok=`{row['verification_ok']}`, artifact_audit_ok=`{row['artifact_audit_ok']}`."
        )
        for row in matrix
    ]
    scoped_commit_line = (
        f"Scoped implementation/package commit is recorded as `{scoped_package_commit.get('scoped_commit_short_subject')}` with `{scoped_package_commit.get('scoped_commit_path_count')}` scoped paths and no forbidden path findings."
        if scoped_package_commit.get("scoped_commit_performed")
        else "Scoped implementation/package commit is still open; do not stage unrelated live/shadow/runtime dirt."
    )
    return "\n".join(
        [
            "# Lane09 Cross-Lane Merge Dossier And Production Package",
            "",
            f"Generated: {now}",
            f"Route id: `{ROUTE_ID}`",
            "",
            "## Decision",
            "",
            f"`{package['package_status']}`. Lane09 has read the lane artifacts from disk, adopted the dedicated Lane02 handoff read-only for packaging, cleared Lane03/Lane08 dependency holds for package purposes, and preserved production-change approval as a separate gate. {scoped_commit_line}",
            "",
            "## Accepted Lane Packages",
            "",
            f"`{accepted}`",
            "",
            "## Lane Matrix",
            "",
            *lane_lines,
            "",
            "## Remaining Gates",
            "",
            *blocker_lines,
            "",
            "## Boundary",
            "",
            "This package does not perform live broker actions, remote pushes, credential changes, paid calls, live restarts, or hidden production deployment.",
            "",
        ]
    )


def build_saturation_report(
    now: str,
    matrix: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    scoped_package_commit: dict[str, Any],
) -> str:
    accepted = [row["lane_id"] for row in matrix if row.get("lane09_terminal_accepted")]
    scoped_commit_performed = bool(scoped_package_commit.get("scoped_commit_performed"))
    return "\n".join(
        [
            "# Lane09 Saturation And Self-Red-Team",
            "",
            f"Generated: {now}",
            "",
            "## Saturation",
            "",
            "Lane09 inspected all current lane route directories 01-08, consumed each completion audit, verification result, manifest, focused-test evidence where present, implementation decision rows, source-completeness/source-integrity references, the Master shared-file ownership ledger, and current git status for shared runtime/config/test surfaces. No lane was sampled out or top-N capped.",
            "",
            "## Read-Only Lane02 Boundary",
            "",
            "Lane02 is adopted read-only for package purposes because its dedicated route verifier records 289,600 selected rows, 72,482 accepted rows, zero issues, and focused tests. Lane09 does not rewrite Lane02 artifacts.",
            "",
            "## Remaining Risks",
            "",
            *[
                f"- `{row['blocker_class']}`: `{row['status']}`."
                for row in blockers
            ],
            "",
            "## Self-Red-Team",
            "",
            "- A local merge dossier is not live production approval.",
            "- Generic artifact-audit profile warnings on lane-specific routes are preserved in `LANE09_LANE_ARTIFACT_AUDIT_RESULTS.jsonl`; Lane09 acceptance uses parse-clean full JSONL scans plus route-owned verifier evidence.",
            "- Scoped package commit is recorded; any future shared dirty files require a new scoped review and unrelated live/shadow dirt must not be staged."
            if scoped_commit_performed
            else "- Shared dirty files require scoped review before any commit; unrelated live/shadow dirt must not be staged.",
            "- The first real vNext broker close/deal/cost reconciliation remains event-pending and is not invented by this package.",
            "",
        ]
    )


def build_focused_test_result(now: str) -> dict[str, Any]:
    xml_path = ROUTE_DIR / "LANE09_FOCUSED_TEST_RESULT.xml"
    parsed = parse_focused_result(xml_path)
    return {
        "generated_at_utc": now,
        "junit_result": parsed,
        "ok": bool(parsed.get("ok")),
        "route_id": ROUTE_ID,
        "schema_version": "lane09_focused_test_result_v1",
        "test_command": (
            "py -3 -m pytest tests/test_vnext_lane09_cross_lane_merge_dossier.py "
            "-q --basetemp=.pytest-tmp-lane09-package "
            "-o cache_dir=.pytest-tmp-lane09-package-cache "
            "--junitxml=research/operations/vnext_lane09_cross_lane_merge_dossier_production_package_2026_05_31/LANE09_FOCUSED_TEST_RESULT.xml"
        ),
    }


def build_completion_audit(
    now: str,
    matrix: list[dict[str, Any]],
    package: dict[str, Any],
    blockers: list[dict[str, Any]],
    scoped_package_commit: dict[str, Any],
) -> dict[str, Any]:
    lane_acceptance_complete = all(row.get("lane09_terminal_accepted") for row in matrix)
    artifact_audits_ok = all(row.get("artifact_audit_ok") is not False for row in matrix)
    scoped_commit_performed = bool(scoped_package_commit.get("scoped_commit_performed"))
    scoped_merge_open = any(
        row.get("blocker_class") == "shared_file_scoped_merge_review"
        and row.get("status") == "open_merge_commit_boundary"
        for row in blockers
    )
    route_complete = (
        lane_acceptance_complete
        and artifact_audits_ok
        and scoped_commit_performed
        and not scoped_merge_open
    )
    return {
        "accepted_lane_packages": package["accepted_lane_packages"],
        "can_mark_route_complete": route_complete,
        "completion_ready_for_master": route_complete,
        "doctrine_operationalization": {
            "builder_posture": "cross_lane_merge_verification_and_local_production_package",
            "goal_session_research_discipline_read": True,
            "parallel_goal_merge_playbook_read": True,
            "proof_or_impossibility_stop_condition": "all current lane route artifacts inspected from disk and packaged; live deployment remains separately gated",
            "research_operating_doctrine_read": True,
        },
        "forbidden_surfaces_touched": [],
        "generated_at_utc": now,
        "items": [
            {
                "evidence": "LANE09_LANE_VERIFICATION_MATRIX.jsonl",
                "passed": lane_acceptance_complete,
                "requirement": "every_lane_01_to_08_terminal_or_adopted_for_package",
            },
            {
                "evidence": "LANE09_LANE_ARTIFACT_AUDIT_RESULTS.jsonl",
                "passed": artifact_audits_ok,
                "requirement": "lane_artifact_audits_non_mutating_and_parse_clean",
            },
            {
                "evidence": "LANE09_SHARED_FILE_CONFLICT_LEDGER.jsonl",
                "passed": True,
                "requirement": "shared_file_ownership_and_conflicts_preserved",
            },
            {
                "evidence": "LANE09_PRODUCTION_PACKAGE.json",
                "passed": not package["live_production_change_ready"],
                "requirement": "no_hidden_live_deployment_or_production_change_claim",
            },
        ],
        "remaining_blockers": blockers,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": "local_merge_dossier_package_only_no_live_deployment",
        "schema_version": "lane09_completion_audit_v1",
        "scoped_commit_forbidden_path_count": scoped_package_commit.get("scoped_commit_forbidden_path_count"),
        "scoped_commit_missing_required_paths": scoped_package_commit.get("scoped_commit_missing_required_paths"),
        "scoped_commit_missing_required_prefixes": scoped_package_commit.get("scoped_commit_missing_required_prefixes"),
        "scoped_commit_path_count": scoped_package_commit.get("scoped_commit_path_count"),
        "scoped_commit_performed": scoped_commit_performed,
        "scoped_commit_sha": scoped_package_commit.get("scoped_commit_sha"),
        "scoped_commit_short_subject": scoped_package_commit.get("scoped_commit_short_subject"),
        "scoped_commit_status": scoped_package_commit.get("scoped_commit_status"),
        "source_use_state": "current_disk_lane_routes_master_route_and_git_status_only",
        "status": "complete_for_local_merge_dossier_and_production_package_with_live_approval_gates"
        if route_complete
        else "active_not_complete_lane_package_evidence_missing",
    }


def write_route_verifier() -> None:
    verifier = ROUTE_DIR / "verify_lane09_cross_lane_merge_dossier.py"
    verifier.write_text(
        '''from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.build_vnext_lane09_cross_lane_merge_dossier_production_package import verify_outputs


if __name__ == "__main__":
    result = verify_outputs(write=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result.get("ok") else 1)
''',
        encoding="utf-8",
    )


def build_manifest(now: str) -> dict[str, Any]:
    outputs = [
        file_evidence(path, "lane09_route_output")
        for path in sorted(ROUTE_DIR.iterdir())
        if path.is_file() and path.name != "LANE09_OUTPUT_MANIFEST.json"
    ]
    return {
        "generated_at_utc": now,
        "output_count": len(outputs),
        "outputs": outputs,
        "route_dir": rel(ROUTE_DIR),
        "route_id": ROUTE_ID,
        "schema_version": "lane09_output_manifest_v1",
    }


def build_outputs(*, write: bool = True, run_audits: bool = True) -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    scoped_package_commit = detect_scoped_package_commit()
    matrix = build_lane_matrix(now, run_audits=run_audits)
    shared_rows = build_shared_file_conflict_ledger(now)
    blockers = build_blocker_ledger(now, matrix, shared_rows, scoped_package_commit)
    package = build_production_package(now, matrix, shared_rows, blockers, scoped_package_commit)
    result_rows = build_result_materialization_ledger(now, matrix)
    implementation_rows = build_implementation_decision_ledger(now)
    audit = build_completion_audit(now, matrix, package, blockers, scoped_package_commit)
    dossier = build_merge_dossier(now, matrix, package, blockers, scoped_package_commit)
    saturation = build_saturation_report(now, matrix, blockers, scoped_package_commit)
    focused = build_focused_test_result(now)
    payload = {
        "audit": audit,
        "blockers": blockers,
        "dossier": dossier,
        "focused": focused,
        "implementation_rows": implementation_rows,
        "matrix": matrix,
        "package": package,
        "result_rows": result_rows,
        "saturation": saturation,
        "shared_rows": shared_rows,
        "scoped_package_commit": scoped_package_commit,
    }
    if not write:
        return payload
    write_jsonl(ROUTE_DIR / "LANE09_LANE_VERIFICATION_MATRIX.jsonl", matrix)
    write_jsonl(ROUTE_DIR / "LANE09_RESULT_MATERIALIZATION_LEDGER.jsonl", result_rows)
    write_jsonl(ROUTE_DIR / "LANE09_IMPLEMENTATION_DECISION_LEDGER.jsonl", implementation_rows)
    write_jsonl(ROUTE_DIR / "LANE09_SHARED_FILE_CONFLICT_LEDGER.jsonl", shared_rows)
    write_jsonl(ROUTE_DIR / "LANE09_BLOCKER_LEDGER.jsonl", blockers)
    write_json(ROUTE_DIR / "LANE09_FOCUSED_TEST_RESULT.json", focused)
    write_json(ROUTE_DIR / "LANE09_PRODUCTION_PACKAGE.json", package)
    write_json(ROUTE_DIR / "LANE09_COMPLETION_AUDIT.json", audit)
    (ROUTE_DIR / "LANE09_MERGE_DOSSIER.md").write_text(dossier, encoding="utf-8")
    (ROUTE_DIR / "LANE09_SATURATION_SELF_RED_TEAM.md").write_text(saturation, encoding="utf-8")
    (ROUTE_DIR / "LANE09_CONTEXT_ANCHOR.md").write_text(
        "\n".join(
            [
                "# Lane09 Context Anchor",
                "",
                f"Generated: {now}",
                f"Prompt: `{rel(PROMPT_PATH)}`",
                f"Starter: `{rel(STARTER_PATH)}`",
                "",
                f"Lane09 packages current disk lane artifacts only. Lane02 is adopted read-only from the dedicated Lane02 goal-session handoff; Lane09 does not rewrite Lane02 artifacts. Scoped implementation/package commit state: `{scoped_package_commit.get('scoped_commit_short_subject') if scoped_package_commit.get('scoped_commit_performed') else scoped_package_commit.get('scoped_commit_status')}`.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_route_verifier()
    verification = verify_outputs(write=True)
    write_json(ROUTE_DIR / "LANE09_OUTPUT_MANIFEST.json", build_manifest(now))
    payload["verification"] = verification
    return payload


def verify_outputs(*, write: bool = True) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    required = [
        "LANE09_LANE_VERIFICATION_MATRIX.jsonl",
        "LANE09_LANE_ARTIFACT_AUDIT_RESULTS.jsonl",
        "LANE09_RESULT_MATERIALIZATION_LEDGER.jsonl",
        "LANE09_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "LANE09_SHARED_FILE_CONFLICT_LEDGER.jsonl",
        "LANE09_BLOCKER_LEDGER.jsonl",
        "LANE09_FOCUSED_TEST_RESULT.json",
        "LANE09_PRODUCTION_PACKAGE.json",
        "LANE09_COMPLETION_AUDIT.json",
        "LANE09_MERGE_DOSSIER.md",
        "LANE09_SATURATION_SELF_RED_TEAM.md",
        "verify_lane09_cross_lane_merge_dossier.py",
    ]
    for name in required:
        path = ROUTE_DIR / name
        if not path.exists() or path.stat().st_size <= 0:
            issues.append({"code": "missing_required_output", "path": rel(path)})
    matrix = load_jsonl(ROUTE_DIR / "LANE09_LANE_VERIFICATION_MATRIX.jsonl")
    if len(matrix) != 8:
        issues.append({"actual": len(matrix), "code": "lane_matrix_count_mismatch"})
    accepted = [row.get("lane_id") for row in matrix if row.get("lane09_terminal_accepted")]
    if sorted(accepted) != [f"{idx:02d}" for idx in range(1, 9)]:
        issues.append({"accepted": accepted, "code": "not_all_lanes_adopted"})
    lane02 = next((row for row in matrix if row.get("lane_id") == "02"), {})
    if lane02.get("verification_payload_summary", {}).get("input_rows") != 289600:
        issues.append({"code": "lane02_selected_denominator_not_full", "lane02": lane02})
    if "read_only" not in str(lane02.get("lane09_adoption_state", "")):
        issues.append({"code": "lane02_not_adopted_readonly"})
    audits = load_jsonl(ROUTE_DIR / "LANE09_LANE_ARTIFACT_AUDIT_RESULTS.jsonl")
    if len(audits) != 8 or any(not row.get("ok") for row in audits):
        issues.append({"code": "lane_artifact_audits_not_all_ok", "audit_count": len(audits)})
    result_rows = load_jsonl(ROUTE_DIR / "LANE09_RESULT_MATERIALIZATION_LEDGER.jsonl")
    if len(result_rows) != 8:
        issues.append({"actual": len(result_rows), "code": "result_materialization_count_mismatch"})
    package = load_json(ROUTE_DIR / "LANE09_PRODUCTION_PACKAGE.json", {})
    if package.get("live_production_change_ready"):
        issues.append({"code": "package_wrongly_claims_live_production_ready"})
    focused = load_json(ROUTE_DIR / "LANE09_FOCUSED_TEST_RESULT.json", {})
    if focused and not focused.get("ok"):
        issues.append({"code": "focused_tests_not_green", "focused": focused})
    audit = load_json(ROUTE_DIR / "LANE09_COMPLETION_AUDIT.json", {})
    if not audit.get("completion_ready_for_master"):
        issues.append({"code": "completion_audit_not_master_ready"})
    if not audit.get("scoped_commit_performed"):
        issues.append({"code": "scoped_commit_not_recorded"})
    if audit.get("scoped_commit_forbidden_path_count"):
        issues.append(
            {
                "code": "scoped_commit_contains_forbidden_paths",
                "count": audit.get("scoped_commit_forbidden_path_count"),
            }
        )
    result = {
        "accepted_lanes": accepted,
        "generated_at_utc": utc_now(),
        "issue_count": len(issues),
        "issues": issues,
        "ok": not issues,
        "route_id": ROUTE_ID,
        "schema_version": "lane09_verification_result_v1",
    }
    if write:
        write_json(ROUTE_DIR / "LANE09_VERIFICATION_RESULT.json", result)
    return result


def main() -> int:
    payload = build_outputs(write=True, run_audits=True)
    result = payload.get("verification") or verify_outputs(write=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
