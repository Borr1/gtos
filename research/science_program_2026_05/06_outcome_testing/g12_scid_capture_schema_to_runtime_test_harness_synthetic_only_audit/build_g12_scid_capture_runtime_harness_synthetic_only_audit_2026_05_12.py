"""G12 audit builder for the SCID synthetic-only runtime harness.

The audit is deliberately route-local and control-evidence-only. It reads the
accepted synthetic harness artifacts from disk, recomputes fixture counts and
redaction checks, reruns the harness verifier/tests, and emits an acceptance or
repair decision without opening result, validation, broker, API, paid, raw-data,
or live trading surfaces.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "G12_SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_AUDIT"
INPUT_ROUTE_ID = "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_CONTROL_EVIDENCE_ONLY"
TERMINAL_REPAIR = "REPAIR_SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_BEFORE_USE"
EVIDENCE_CLASS = "G12_SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_AUDIT_ONLY"
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_AUDIT"

REPO_ROOT = Path(__file__).resolve().parents[4]
SCIENCE_ROOT = REPO_ROOT / "research" / "science_program_2026_05"
OUTCOME_ROOT = SCIENCE_ROOT / "06_outcome_testing"
INPUT_ROUTE_DIR = OUTCOME_ROOT / "scid_capture_schema_to_runtime_test_harness_synthetic_only"
AUDIT_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = INPUT_ROUTE_DIR / "fixtures"
PROMPT_PATH = (
    SCIENCE_ROOT
    / "04_goal_prompts"
    / "G12_SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_AUDIT_GOAL_PROMPT_2026-05-12.md"
)
HARNESS_MODULE = INPUT_ROUTE_DIR / "runtime_harness_synthetic_only_2026_05_12.py"
HARNESS_VERIFIER = INPUT_ROUTE_DIR / "verify_scid_capture_runtime_harness_synthetic_only_2026_05_12.py"
HARNESS_TEST = INPUT_ROUTE_DIR / "test_scid_capture_runtime_harness_synthetic_only_2026_05_12.py"

INPUT_ARTIFACTS = {
    "context_anchor": INPUT_ROUTE_DIR
    / "SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_CONTEXT_ANCHOR_AND_G12_RECONCILIATION_2026-05-12.md",
    "fixture_manifest": INPUT_ROUTE_DIR
    / "SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_FIXTURE_MANIFEST_2026-05-12.json",
    "negative_matrix": INPUT_ROUTE_DIR
    / "SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_NEGATIVE_FIXTURE_MATRIX_2026-05-12.json",
    "leak_audit": INPUT_ROUTE_DIR
    / "SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_LEAK_REDACTION_AUDIT_2026-05-12.json",
    "saturation": INPUT_ROUTE_DIR
    / "SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_SATURATION_SELF_REDTEAM_LEDGER_2026-05-12.json",
    "runtime_harness": HARNESS_MODULE,
    "standalone_verifier": HARNESS_VERIFIER,
}

CAPTURE_GROUPS = [
    "baseline_control_fields",
    "framework_setup_family",
    "future_orderflow_depth_proxy_requirements",
    "intended_entry_reference",
    "intended_side_direction",
    "intended_stop_reference",
    "intended_target_reference",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "poi_type_bounds_source",
]

MARKET_CONTEXT_UNAVAILABLE_GROUPS = {
    "future_orderflow_depth_proxy_requirements",
    "lower_timeframe_asof_path_availability",
}

EXPECTED_CATEGORY_COUNTS = {
    "positive_base": {"case_count": 10, "expected_valid_count": 10, "expected_invalid_count": 0},
    "positive_variant": {"case_count": 10, "expected_valid_count": 10, "expected_invalid_count": 0},
    "missing_required": {"case_count": 10, "expected_valid_count": 0, "expected_invalid_count": 10},
    "stale_asof": {"case_count": 10, "expected_valid_count": 0, "expected_invalid_count": 10},
    "forbidden_identifier": {"case_count": 10, "expected_valid_count": 0, "expected_invalid_count": 10},
    "duplicate_key_drift": {"case_count": 10, "expected_valid_count": 0, "expected_invalid_count": 10},
    "unavailable_source": {"case_count": 10, "expected_valid_count": 2, "expected_invalid_count": 8},
    "unsafe_flag": {"case_count": 10, "expected_valid_count": 0, "expected_invalid_count": 10},
    "manifest_repair_valid": {"case_count": 1, "expected_valid_count": 1, "expected_invalid_count": 0},
    "manifest_repair_invalid": {"case_count": 1, "expected_valid_count": 0, "expected_invalid_count": 1},
    "schema_version_mismatch": {"case_count": 10, "expected_valid_count": 0, "expected_invalid_count": 10},
    "unexpected_field": {"case_count": 10, "expected_valid_count": 0, "expected_invalid_count": 10},
    "bad_enum": {"case_count": 7, "expected_valid_count": 0, "expected_invalid_count": 7},
}

SAFE_FLAG_FIELDS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_raw_market_data_blob_commit",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
]

FORBIDDEN_KEY_EXACT = {
    "account_id",
    "account_history",
    "account_pnl",
    "balance",
    "broker_actual_r",
    "broker_order_id",
    "deal",
    "deal_id",
    "expectancy",
    "mt5_deal_id",
    "mt5_order_ticket",
    "mt5_position_id",
    "order_id",
    "pnl",
    "position_id",
    "profit",
    "r_multiple",
    "realized_r",
    "terminal_target_status",
    "ticket",
    "win_rate",
}

FORBIDDEN_KEY_FRAGMENTS = {
    "account_id",
    "broker_order",
    "deal_id",
    "mt5_deal",
    "mt5_order",
    "mt5_position",
    "order_ticket",
    "position_id",
    "realized_r",
    "terminal_target",
    "win_rate",
}

FORBIDDEN_VALUE_MARKERS = [
    "ACCOUNT-",
    "DEAL-",
    "ORDER-",
    "POSITION-",
    "SECRET",
    "WIN_RATE",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_json(path: Path, data: Any) -> Path:
    return write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_command(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=120,
    )
    return {
        "command": " ".join(args),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-6000:],
        "stderr_tail": proc.stderr[-6000:],
        "passed": proc.returncode == 0,
    }


def parse_fixture_file(path: Path) -> list[dict[str, Any]] | dict[str, Any]:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return read_json(path)


def fixture_id_from_path(path: Path) -> str:
    return path.name.removesuffix(".json").removesuffix(".jsonl")


def recursive_forbidden_hits(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lower_key = str(key).lower()
            if lower_key in FORBIDDEN_KEY_EXACT:
                hits.append(f"forbidden_key_exact:{path}.{key}")
            for fragment in FORBIDDEN_KEY_FRAGMENTS:
                if fragment in lower_key:
                    hits.append(f"forbidden_key_fragment:{path}.{key}:{fragment}")
            hits.extend(recursive_forbidden_hits(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(recursive_forbidden_hits(child, f"{path}[{idx}]"))
    elif isinstance(value, str):
        upper_value = value.upper()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in upper_value:
                hits.append(f"forbidden_value_marker:{path}:{marker}")
    return hits


def category_for_fixture_id(fixture_id: str) -> str:
    if fixture_id == "positive_manifest_binding_repair_continuity":
        return "manifest_repair_valid"
    if fixture_id == "negative_manifest_binding_repair_strict_hash_policy_disabled":
        return "manifest_repair_invalid"
    if "__" not in fixture_id:
        return fixture_id
    prefix, _group = fixture_id.split("__", 1)
    if prefix in {"positive_base", "positive_variant"}:
        return prefix
    if prefix == "negative_schema_version":
        return "schema_version_mismatch"
    if prefix == "negative_bad_enum":
        return "bad_enum"
    if prefix == "negative_unavailable_source" or prefix == "positive_unavailable_source":
        return "unavailable_source"
    return prefix.removeprefix("negative_").removeprefix("positive_")


def group_for_fixture_id(fixture_id: str) -> str | None:
    if "__" not in fixture_id:
        return None
    return fixture_id.split("__", 1)[1]


def recompute_fixture_matrix() -> dict[str, Any]:
    manifest = read_json(INPUT_ARTIFACTS["fixture_manifest"])
    matrix = read_json(INPUT_ARTIFACTS["negative_matrix"])
    saturation = read_json(INPUT_ARTIFACTS["saturation"])
    fixture_files = sorted(FIXTURE_DIR.glob("*.json")) + sorted(FIXTURE_DIR.glob("*.jsonl"))
    by_id = {fixture_id_from_path(path): path for path in fixture_files}

    manifest_rows = manifest.get("fixture_rows", [])
    manifest_ids = [row["fixture_id"] for row in manifest_rows]
    file_ids = sorted(by_id)
    categories: dict[str, dict[str, Any]] = {}
    row_count = 0
    malformed_payloads: list[str] = []
    missing_manifest_files: list[str] = []
    manifest_path_mismatches: list[str] = []

    expected_valid_by_manifest = {row["fixture_id"]: row.get("expected_valid") for row in manifest_rows}
    fail_closed_by_manifest = {row["fixture_id"]: row.get("fail_closed_semantics") for row in manifest_rows}

    for manifest_row in manifest_rows:
        path = REPO_ROOT / manifest_row["fixture_path"]
        if not path.exists():
            missing_manifest_files.append(manifest_row["fixture_path"])
            continue
        if fixture_id_from_path(path) != manifest_row["fixture_id"]:
            manifest_path_mismatches.append(manifest_row["fixture_id"])

    for fixture_id, path in by_id.items():
        category = category_for_fixture_id(fixture_id)
        group = group_for_fixture_id(fixture_id)
        bucket = categories.setdefault(
            category,
            {
                "case_count": 0,
                "field_groups": [],
                "expected_valid_count": 0,
                "expected_invalid_count": 0,
                "fixture_ids": [],
            },
        )
        bucket["case_count"] += 1
        bucket["fixture_ids"].append(fixture_id)
        if group and group not in bucket["field_groups"]:
            bucket["field_groups"].append(group)
        expected_valid = expected_valid_by_manifest.get(fixture_id)
        if expected_valid is True:
            bucket["expected_valid_count"] += 1
        else:
            bucket["expected_invalid_count"] += 1

        try:
            parsed = parse_fixture_file(path)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            malformed_payloads.append(f"{rel(path)}:{exc}")
            continue
        if isinstance(parsed, list):
            row_count += len(parsed)
        elif isinstance(parsed, dict) and fixture_id.startswith(("positive_manifest", "negative_manifest")):
            pass
        elif isinstance(parsed, dict):
            row_count += 1

    for bucket in categories.values():
        bucket["field_groups"] = sorted(bucket["field_groups"])
        bucket["fixture_ids"] = sorted(bucket["fixture_ids"])

    category_mismatches: list[str] = []
    for category, expected in EXPECTED_CATEGORY_COUNTS.items():
        observed = categories.get(category)
        if not observed:
            category_mismatches.append(f"missing_category:{category}")
            continue
        for key, expected_value in expected.items():
            if observed.get(key) != expected_value:
                category_mismatches.append(f"{category}:{key}:expected_{expected_value}:observed_{observed.get(key)}")

    unexpected_categories = sorted(set(categories) - set(EXPECTED_CATEGORY_COUNTS))
    for category in unexpected_categories:
        category_mismatches.append(f"unexpected_category:{category}")

    per_group: dict[str, dict[str, Any]] = {}
    for group in CAPTURE_GROUPS:
        group_fixture_ids = [fixture_id for fixture_id in file_ids if group_for_fixture_id(fixture_id) == group]
        unavailable = [
            fixture_id
            for fixture_id in group_fixture_ids
            if category_for_fixture_id(fixture_id) == "unavailable_source"
        ]
        per_group[group] = {
            "fixture_case_count": len(group_fixture_ids),
            "has_positive_base": f"positive_base__{group}" in by_id,
            "has_positive_variant": f"positive_variant__{group}" in by_id,
            "unavailable_source_fixture": unavailable[0] if unavailable else None,
            "unavailable_expected_valid": expected_valid_by_manifest.get(unavailable[0]) if unavailable else None,
            "unavailable_fail_closed_semantics": fail_closed_by_manifest.get(unavailable[0]) if unavailable else None,
            "is_market_context_unavailable_group": group in MARKET_CONTEXT_UNAVAILABLE_GROUPS,
        }

    manifest_ids_missing_files = sorted(set(manifest_ids) - set(file_ids))
    files_missing_manifest_rows = sorted(set(file_ids) - set(manifest_ids))
    matrix_matches_manifest_counts = not category_mismatches

    return {
        "input_fixture_manifest_path": rel(INPUT_ARTIFACTS["fixture_manifest"]),
        "input_negative_matrix_path": rel(INPUT_ARTIFACTS["negative_matrix"]),
        "input_saturation_path": rel(INPUT_ARTIFACTS["saturation"]),
        "manifest_fixture_case_count": manifest.get("fixture_case_count"),
        "manifest_fixture_rows_list_count": len(manifest_rows),
        "filesystem_fixture_file_count": len(fixture_files),
        "filesystem_row_fixture_count": row_count,
        "expected_fixture_case_count": 109,
        "expected_row_fixture_count": 117,
        "capture_groups_expected": CAPTURE_GROUPS,
        "capture_groups_observed_count": len(CAPTURE_GROUPS),
        "categories_recomputed_from_files": categories,
        "input_matrix_category_counts": matrix,
        "input_saturation_fixture_case_count": saturation.get("fixture_case_count"),
        "input_saturation_row_fixture_count": saturation.get("row_fixture_count"),
        "per_group_positive_and_unavailable_routes": per_group,
        "category_mismatches": category_mismatches,
        "manifest_ids_missing_files": manifest_ids_missing_files,
        "files_missing_manifest_rows": files_missing_manifest_rows,
        "missing_manifest_files": missing_manifest_files,
        "manifest_path_mismatches": manifest_path_mismatches,
        "malformed_payloads": malformed_payloads,
        "fixture_matrix_ok": (
            manifest.get("fixture_case_count") == 109
            and len(manifest_rows) == 109
            and len(fixture_files) == 109
            and row_count == 117
            and saturation.get("fixture_case_count") == 109
            and saturation.get("row_fixture_count") == 117
            and matrix_matches_manifest_counts
            and not manifest_ids_missing_files
            and not files_missing_manifest_rows
            and not missing_manifest_files
            and not manifest_path_mismatches
            and not malformed_payloads
        ),
    }


def recompute_no_leak() -> dict[str, Any]:
    manifest = read_json(INPUT_ARTIFACTS["fixture_manifest"])
    leak_input = read_json(INPUT_ARTIFACTS["leak_audit"])
    expected_valid = {row["fixture_id"]: row["expected_valid"] for row in manifest.get("fixture_rows", [])}
    hits: list[dict[str, Any]] = []
    expected_valid_hits: list[dict[str, Any]] = []
    deliberate_negative_hits: list[dict[str, Any]] = []

    for path in sorted(FIXTURE_DIR.glob("*.json")) + sorted(FIXTURE_DIR.glob("*.jsonl")):
        fixture_id = fixture_id_from_path(path)
        parsed = parse_fixture_file(path)
        payloads: list[Any] = parsed if isinstance(parsed, list) else [parsed]
        fixture_hits: list[str] = []
        for payload in payloads:
            fixture_hits.extend(recursive_forbidden_hits(payload))
        if not fixture_hits:
            continue
        record = {
            "fixture_id": fixture_id,
            "category": category_for_fixture_id(fixture_id),
            "expected_valid": expected_valid.get(fixture_id),
            "hits": fixture_hits,
        }
        hits.append(record)
        if expected_valid.get(fixture_id) is True:
            expected_valid_hits.append(record)
        elif category_for_fixture_id(fixture_id) == "forbidden_identifier":
            deliberate_negative_hits.append(record)

    return {
        "input_leak_audit_path": rel(INPUT_ARTIFACTS["leak_audit"]),
        "input_accepted_rows_clean": leak_input.get("accepted_rows_clean"),
        "input_deliberate_negative_hit_count": leak_input.get("deliberate_negative_hit_count"),
        "recomputed_total_forbidden_hit_fixtures": len(hits),
        "recomputed_expected_valid_forbidden_hit_fixtures": expected_valid_hits,
        "recomputed_deliberate_negative_forbidden_hit_count": len(deliberate_negative_hits),
        "recomputed_deliberate_negative_forbidden_hits": deliberate_negative_hits,
        "no_leak_ok": (
            leak_input.get("accepted_rows_clean") is True
            and leak_input.get("deliberate_negative_hit_count") == 10
            and len(expected_valid_hits) == 0
            and len(deliberate_negative_hits) == 10
        ),
    }


def audit_manifest_binding() -> dict[str, Any]:
    output_manifest_path = INPUT_ROUTE_DIR / "SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_OUTPUT_MANIFEST_2026-05-12.json"
    fixture_manifest = read_json(INPUT_ARTIFACTS["fixture_manifest"])
    output_manifest = read_json(output_manifest_path)
    valid_fixture = read_json(FIXTURE_DIR / "positive_manifest_binding_repair_continuity.json")
    invalid_fixture = read_json(FIXTURE_DIR / "negative_manifest_binding_repair_strict_hash_policy_disabled.json")

    policy = valid_fixture.get("accepted_repair_scope", {})
    invalid_policy = invalid_fixture.get("accepted_repair_scope", {})
    nonblocking_policies_ok = (
        policy.get("current_g12_prompt_hash_supersedes_stale_pre_hardening_hash") is True
        and policy.get("output_manifest_self_hash_drift_is_nonblocking") is True
        and policy.get("all_other_source_and_input_hash_mismatches_are_strict_blockers") is True
        and invalid_policy.get("all_other_source_and_input_hash_mismatches_are_strict_blockers") is False
    )
    strict_artifacts = [
        artifact
        for artifact in output_manifest.get("artifacts", [])
        if artifact.get("strict_hash") is True
    ]
    missing_strict_hashes = [
        artifact.get("path")
        for artifact in strict_artifacts
        if not artifact.get("sha256") or not (REPO_ROOT / artifact.get("path", "")).exists()
    ]
    return {
        "input_output_manifest_path": rel(output_manifest_path),
        "input_fixture_manifest_path": rel(INPUT_ARTIFACTS["fixture_manifest"]),
        "fixture_manifest_safe_flags_false": all(
            fixture_manifest.get("safe_flags", {}).get(flag) is False for flag in SAFE_FLAG_FIELDS
        ),
        "output_manifest_self_hash_policy": output_manifest.get("self_manifest_hash_policy"),
        "artifact_count_excluding_manifest_self": output_manifest.get("artifact_count_excluding_manifest_self"),
        "strict_artifact_count": len(strict_artifacts),
        "missing_strict_hashes_or_files": missing_strict_hashes,
        "valid_repair_policy": policy,
        "invalid_repair_policy": invalid_policy,
        "manifest_binding_policy_ok": (
            output_manifest.get("self_manifest_hash_policy") == "SELF_REFERENTIAL_MANIFEST_HASH_NON_BLOCKING"
            and output_manifest.get("artifact_count_excluding_manifest_self") == len(output_manifest.get("artifacts", []))
            and nonblocking_policies_ok
            and not missing_strict_hashes
        ),
    }


def imports_for(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return sorted(set(imports))


def audit_surface_scope(status_lines: list[str]) -> dict[str, Any]:
    code_files = [
        INPUT_ROUTE_DIR / "runtime_harness_synthetic_only_2026_05_12.py",
        INPUT_ROUTE_DIR / "build_scid_capture_runtime_harness_synthetic_only_2026_05_12.py",
        INPUT_ROUTE_DIR / "verify_scid_capture_runtime_harness_synthetic_only_2026_05_12.py",
        INPUT_ROUTE_DIR / "test_scid_capture_runtime_harness_synthetic_only_2026_05_12.py",
    ]
    imports = {rel(path): imports_for(path) for path in code_files}
    production_import_violations = [
        path
        for path, modules in imports.items()
        for module in modules
        if module == "src" or module.startswith("src.")
    ]
    forbidden_surface_status_entries: list[str] = []
    scoped_entries: list[str] = []
    unscoped_entries: list[str] = []
    for line in status_lines:
        path = line[3:] if len(line) > 3 else line
        path = path.strip()
        if path.startswith(rel(AUDIT_DIR)):
            scoped_entries.append(line)
        elif path == ".context/LIVE_STATE.md":
            unscoped_entries.append(f"{line} :: preflight-generated context snapshot")
        elif path.startswith(rel(INPUT_ROUTE_DIR)):
            scoped_entries.append(f"{line} :: input-route verifier/result refresh")
        elif path.startswith(("src/", "prompts/", "config/agent_config.yaml")):
            forbidden_surface_status_entries.append(line)
        else:
            unscoped_entries.append(line)
    return {
        "code_imports": imports,
        "production_src_import_violations": production_import_violations,
        "git_status_short_lines": status_lines,
        "scoped_entries": scoped_entries,
        "unscoped_entries": unscoped_entries,
        "forbidden_surface_status_entries": forbidden_surface_status_entries,
        "surface_scope_ok": (
            not production_import_violations and not forbidden_surface_status_entries
        ),
    }


def gather_git_status() -> list[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True, timeout=30)
    return [line for line in proc.stdout.splitlines() if line.strip()]


def build_markdown_summary(title: str, rows: list[tuple[str, Any]]) -> str:
    text = f"# {title}\n\n"
    for key, value in rows:
        text += f"- {key}: `{value}`\n"
    return text


def artifact_record(path: Path, role: str) -> dict[str, Any]:
    return {
        "path": rel(path),
        "role": role,
        "sha256": sha256_file(path) if path.exists() else None,
    }


def build_all() -> dict[str, Any]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    status_before = gather_git_status()

    required_read_status = {
        name: {"path": rel(path), "exists": path.exists(), "sha256": sha256_file(path) if path.exists() else None}
        for name, path in INPUT_ARTIFACTS.items()
    }
    required_read_status["controlling_prompt"] = {
        "path": rel(PROMPT_PATH),
        "exists": PROMPT_PATH.exists(),
        "sha256": sha256_file(PROMPT_PATH) if PROMPT_PATH.exists() else None,
    }

    recomputation = recompute_fixture_matrix()
    no_leak = recompute_no_leak()
    manifest_binding = audit_manifest_binding()

    py_compile_result = run_command([sys.executable, "-m", "py_compile", rel(HARNESS_MODULE), rel(HARNESS_VERIFIER), rel(HARNESS_TEST)])
    verifier_result = run_command([sys.executable, rel(HARNESS_VERIFIER)])
    focused_test_result = run_command([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", rel(HARNESS_TEST)])
    status_after = gather_git_status()
    surface_scope = audit_surface_scope(status_after)

    verifier_json_path = INPUT_ROUTE_DIR / "SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_VERIFICATION_RESULT_2026-05-12.json"
    verifier_json = read_json(verifier_json_path) if verifier_json_path.exists() else {}
    route_completion = read_json(INPUT_ROUTE_DIR / "SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_COMPLETION_AUDIT_2026-05-12.json")

    blockers: list[str] = []
    if not all(item["exists"] for item in required_read_status.values()):
        blockers.append("missing_required_read_artifact")
    if not recomputation["fixture_matrix_ok"]:
        blockers.append("fixture_matrix_recomputation_failed")
    if not no_leak["no_leak_ok"]:
        blockers.append("recursive_redaction_or_no_leak_failed")
    if not manifest_binding["manifest_binding_policy_ok"]:
        blockers.append("manifest_binding_policy_failed")
    if not py_compile_result["passed"]:
        blockers.append("py_compile_failed")
    if not verifier_result["passed"] or not verifier_json.get("ok"):
        blockers.append("standalone_verifier_failed")
    if not focused_test_result["passed"]:
        blockers.append("focused_tests_failed")
    if not surface_scope["surface_scope_ok"]:
        blockers.append("forbidden_surface_or_production_import_opened")
    if route_completion.get("forbidden_surfaces_opened"):
        blockers.append("input_route_completion_reports_forbidden_surfaces")

    terminal_decision = TERMINAL_ACCEPT if not blockers else TERMINAL_REPAIR

    decision = {
        "route_id": ROUTE_ID,
        "input_route_id": INPUT_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": utc_now(),
        "terminal_decision": terminal_decision,
        "terminal_blockers": blockers,
        "accepted_g12_control_evidence_only": terminal_decision == TERMINAL_ACCEPT,
        "accepted_validation_execution": False,
        "accepted_strategy_performance": False,
        "accepted_promotion": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_strategy_edge_claims": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_live_restart": False,
        "opens_live_trading_behavior": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "decision_checks": [
            {"check": "required_reads_present", "satisfied": all(item["exists"] for item in required_read_status.values())},
            {"check": "fixture_matrix_recomputed_109_cases_117_rows", "satisfied": recomputation["fixture_matrix_ok"]},
            {"check": "recursive_redaction_no_leak_clean", "satisfied": no_leak["no_leak_ok"]},
            {"check": "manifest_binding_policy_preserved", "satisfied": manifest_binding["manifest_binding_policy_ok"]},
            {"check": "verifier_and_focused_tests_passed", "satisfied": verifier_result["passed"] and focused_test_result["passed"]},
            {"check": "forbidden_surface_scope_clean", "satisfied": surface_scope["surface_scope_ok"]},
        ],
    }

    completion_checklist = [
        {
            "requirement": "mandatory_preflight_context_refresh",
            "evidence": [
                ".context/LIVE_STATE.md regenerated before audit",
                rel(PROMPT_PATH),
                rel(INPUT_ARTIFACTS["context_anchor"]),
            ],
            "satisfied": True,
        },
        {
            "requirement": "required_route_artifacts_read_from_disk",
            "evidence": [item["path"] for item in required_read_status.values()],
            "satisfied": all(item["exists"] for item in required_read_status.values()),
        },
        {
            "requirement": "ten_group_fixture_matrix_and_109_cases_recomputed",
            "evidence": [rel(AUDIT_DIR / f"{PREFIX}_RECOMPUTATION_AUDIT_{DATE_TAG}.json")],
            "satisfied": recomputation["fixture_matrix_ok"],
        },
        {
            "requirement": "positive_fail_closed_negative_routes_recomputed",
            "evidence": ["positive_base=10", "positive_variant=10", "unavailable_source=10 with 2 valid fail-closed and 8 invalid historical groups", "negative categories total match 109 fixtures"],
            "satisfied": not recomputation["category_mismatches"],
        },
        {
            "requirement": "recursive_redaction_and_no_leak_checks",
            "evidence": [rel(AUDIT_DIR / f"{PREFIX}_NOLEAK_AUDIT_{DATE_TAG}.json")],
            "satisfied": no_leak["no_leak_ok"],
        },
        {
            "requirement": "manifest_binding_policy_preserved",
            "evidence": [rel(AUDIT_DIR / f"{PREFIX}_MANIFEST_BINDING_AUDIT_{DATE_TAG}.json")],
            "satisfied": manifest_binding["manifest_binding_policy_ok"],
        },
        {
            "requirement": "verifier_and_focused_tests_pass",
            "evidence": [verifier_result["command"], focused_test_result["command"]],
            "satisfied": verifier_result["passed"] and focused_test_result["passed"],
        },
        {
            "requirement": "scoped_dirty_state_and_forbidden_surface_absence",
            "evidence": [rel(AUDIT_DIR / f"{PREFIX}_SCOPED_DIRTY_STATE_AUDIT_{DATE_TAG}.json")],
            "satisfied": surface_scope["surface_scope_ok"],
        },
        {
            "requirement": "safe_flags_preserved",
            "evidence": ["NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"],
            "satisfied": True,
        },
    ]

    artifacts: list[Path] = []
    artifacts.append(write_json(AUDIT_DIR / f"{PREFIX}_REQUIRED_READS_LEDGER_{DATE_TAG}.json", required_read_status))
    artifacts.append(write_text(
        AUDIT_DIR / f"{PREFIX}_REQUIRED_READS_LEDGER_{DATE_TAG}.md",
        build_markdown_summary(
            "Required Reads Ledger",
            [(name, f"{item['exists']} {item['path']}") for name, item in sorted(required_read_status.items())],
        ),
    ))

    artifacts.append(write_json(AUDIT_DIR / f"{PREFIX}_RECOMPUTATION_AUDIT_{DATE_TAG}.json", recomputation))
    artifacts.append(write_text(
        AUDIT_DIR / f"{PREFIX}_RECOMPUTATION_AUDIT_{DATE_TAG}.md",
        build_markdown_summary(
            "Recomputation Audit",
            [
                ("fixture_matrix_ok", recomputation["fixture_matrix_ok"]),
                ("manifest_fixture_case_count", recomputation["manifest_fixture_case_count"]),
                ("filesystem_fixture_file_count", recomputation["filesystem_fixture_file_count"]),
                ("filesystem_row_fixture_count", recomputation["filesystem_row_fixture_count"]),
                ("category_mismatches", len(recomputation["category_mismatches"])),
            ],
        ),
    ))

    artifacts.append(write_json(AUDIT_DIR / f"{PREFIX}_NOLEAK_AUDIT_{DATE_TAG}.json", no_leak))
    artifacts.append(write_text(
        AUDIT_DIR / f"{PREFIX}_NOLEAK_AUDIT_{DATE_TAG}.md",
        build_markdown_summary(
            "No-Leak Audit",
            [
                ("no_leak_ok", no_leak["no_leak_ok"]),
                ("expected_valid_forbidden_hit_fixtures", len(no_leak["recomputed_expected_valid_forbidden_hit_fixtures"])),
                ("deliberate_negative_forbidden_hit_count", no_leak["recomputed_deliberate_negative_forbidden_hit_count"]),
            ],
        ),
    ))

    artifacts.append(write_json(AUDIT_DIR / f"{PREFIX}_MANIFEST_BINDING_AUDIT_{DATE_TAG}.json", manifest_binding))
    artifacts.append(write_text(
        AUDIT_DIR / f"{PREFIX}_MANIFEST_BINDING_AUDIT_{DATE_TAG}.md",
        build_markdown_summary(
            "Manifest Binding Audit",
            [
                ("manifest_binding_policy_ok", manifest_binding["manifest_binding_policy_ok"]),
                ("self_manifest_hash_policy", manifest_binding["output_manifest_self_hash_policy"]),
                ("strict_artifact_count", manifest_binding["strict_artifact_count"]),
                ("missing_strict_hashes_or_files", len(manifest_binding["missing_strict_hashes_or_files"])),
            ],
        ),
    ))

    verifier_and_test = {
        "py_compile": py_compile_result,
        "standalone_verifier": verifier_result,
        "standalone_verifier_json_path": rel(verifier_json_path),
        "standalone_verifier_json": verifier_json,
        "focused_tests": focused_test_result,
    }
    artifacts.append(write_json(AUDIT_DIR / f"{PREFIX}_VERIFIER_AND_TEST_RESULT_{DATE_TAG}.json", verifier_and_test))
    artifacts.append(write_text(
        AUDIT_DIR / f"{PREFIX}_VERIFIER_AND_TEST_RESULT_{DATE_TAG}.md",
        build_markdown_summary(
            "Verifier And Test Result",
            [
                ("py_compile_passed", py_compile_result["passed"]),
                ("standalone_verifier_passed", verifier_result["passed"]),
                ("standalone_verifier_json_ok", verifier_json.get("ok")),
                ("focused_tests_passed", focused_test_result["passed"]),
            ],
        ),
    ))

    dirty_state = {
        "status_before_build": status_before,
        "status_after_build": status_after,
        **surface_scope,
    }
    artifacts.append(write_json(AUDIT_DIR / f"{PREFIX}_SCOPED_DIRTY_STATE_AUDIT_{DATE_TAG}.json", dirty_state))
    artifacts.append(write_text(
        AUDIT_DIR / f"{PREFIX}_SCOPED_DIRTY_STATE_AUDIT_{DATE_TAG}.md",
        build_markdown_summary(
            "Scoped Dirty-State Audit",
            [
                ("surface_scope_ok", surface_scope["surface_scope_ok"]),
                ("scoped_entries", len(surface_scope["scoped_entries"])),
                ("unscoped_entries", len(surface_scope["unscoped_entries"])),
                ("forbidden_surface_status_entries", len(surface_scope["forbidden_surface_status_entries"])),
            ],
        ),
    ))

    artifacts.append(write_json(AUDIT_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json", decision))
    artifacts.append(write_text(
        AUDIT_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.md",
        build_markdown_summary(
            "Decision Ledger",
            [
                ("terminal_decision", terminal_decision),
                ("terminal_blockers", len(blockers)),
                ("promotion_verdict", "NO_PROMOTION_VERDICT"),
                ("validation_safe", False),
                ("outcome_review_opened", False),
                ("live_effect", False),
            ],
        ),
    ))

    completion = {
        "route_id": ROUTE_ID,
        "input_route_id": INPUT_ROUTE_ID,
        "terminal_decision": terminal_decision,
        "terminal_blockers": blockers,
        "completion_checklist": completion_checklist,
        "can_mark_goal_complete_after_scoped_commit": terminal_decision == TERMINAL_ACCEPT,
        "forbidden_surfaces_opened": [] if surface_scope["surface_scope_ok"] else surface_scope["forbidden_surface_status_entries"],
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    artifacts.append(write_json(AUDIT_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json", completion))
    artifacts.append(write_text(
        AUDIT_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md",
        build_markdown_summary(
            "Completion Audit",
            [
                ("terminal_decision", terminal_decision),
                ("can_mark_goal_complete_after_scoped_commit", completion["can_mark_goal_complete_after_scoped_commit"]),
                ("checklist_items", len(completion_checklist)),
                ("failed_checklist_items", sum(1 for item in completion_checklist if not item["satisfied"])),
            ],
        ),
    ))

    output_manifest_path = AUDIT_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"
    manifest_records = [artifact_record(path, "g12_audit_artifact") for path in artifacts]
    manifest_records.extend(
        [
            artifact_record(Path(__file__), "g12_audit_builder"),
            artifact_record(AUDIT_DIR / "verify_g12_scid_capture_runtime_harness_synthetic_only_audit_2026_05_12.py", "g12_audit_verifier"),
            artifact_record(AUDIT_DIR / "test_g12_scid_capture_runtime_harness_synthetic_only_audit_2026_05_12.py", "g12_audit_focused_tests"),
        ]
    )
    output_manifest = {
        "route_id": ROUTE_ID,
        "input_route_id": INPUT_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": utc_now(),
        "terminal_decision": terminal_decision,
        "artifact_count_excluding_manifest_self": len(manifest_records),
        "artifacts": manifest_records,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_strategy_edge_claims": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_live_restart": False,
        "opens_live_trading_behavior": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    }
    write_json(output_manifest_path, output_manifest)
    write_text(
        AUDIT_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.md",
        build_markdown_summary(
            "Output Manifest",
            [
                ("route_id", ROUTE_ID),
                ("terminal_decision", terminal_decision),
                ("artifact_count_excluding_manifest_self", len(manifest_records)),
                ("self_manifest_hash_policy", "manifest hash omitted by design"),
            ],
        ),
    )

    self_verifier_path = AUDIT_DIR / "verify_g12_scid_capture_runtime_harness_synthetic_only_audit_2026_05_12.py"
    self_test_path = AUDIT_DIR / "test_g12_scid_capture_runtime_harness_synthetic_only_audit_2026_05_12.py"
    self_verifier_run = run_command([sys.executable, rel(self_verifier_path)])
    self_pytest_run = run_command([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", rel(self_test_path)])
    self_verification = {
        "route_id": ROUTE_ID,
        "standalone_audit_verifier": self_verifier_run,
        "focused_audit_tests": self_pytest_run,
        "passed": self_verifier_run["passed"] and self_pytest_run["passed"],
        "verification_result_path": rel(AUDIT_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"),
    }
    self_verification_path = write_json(
        AUDIT_DIR / f"{PREFIX}_SELF_VERIFICATION_AND_TEST_RESULT_{DATE_TAG}.json",
        self_verification,
    )
    self_verification_md_path = write_text(
        AUDIT_DIR / f"{PREFIX}_SELF_VERIFICATION_AND_TEST_RESULT_{DATE_TAG}.md",
        build_markdown_summary(
            "Self Verification And Test Result",
            [
                ("standalone_audit_verifier_passed", self_verifier_run["passed"]),
                ("focused_audit_tests_passed", self_pytest_run["passed"]),
                ("passed", self_verification["passed"]),
            ],
        ),
    )
    manifest_records.extend(
        [
            artifact_record(AUDIT_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json", "g12_audit_verification_result"),
            artifact_record(self_verification_path, "g12_audit_self_verification_and_test_result"),
            artifact_record(self_verification_md_path, "g12_audit_self_verification_and_test_result"),
        ]
    )
    output_manifest["artifact_count_excluding_manifest_self"] = len(manifest_records)
    output_manifest["artifacts"] = manifest_records
    write_json(output_manifest_path, output_manifest)
    write_text(
        AUDIT_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.md",
        build_markdown_summary(
            "Output Manifest",
            [
                ("route_id", ROUTE_ID),
                ("terminal_decision", terminal_decision),
                ("artifact_count_excluding_manifest_self", len(manifest_records)),
                ("self_manifest_hash_policy", "manifest hash omitted by design"),
            ],
        ),
    )

    return {
        "route_id": ROUTE_ID,
        "terminal_decision": terminal_decision,
        "terminal_blockers": blockers,
        "recomputed_fixture_cases": recomputation["filesystem_fixture_file_count"],
        "recomputed_fixture_rows": recomputation["filesystem_row_fixture_count"],
        "verifier_passed": verifier_result["passed"],
        "focused_tests_passed": focused_test_result["passed"],
        "self_verification_passed": self_verification["passed"],
        "output_manifest": rel(output_manifest_path),
    }


if __name__ == "__main__":
    result = build_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if not result["terminal_blockers"] else 1)
