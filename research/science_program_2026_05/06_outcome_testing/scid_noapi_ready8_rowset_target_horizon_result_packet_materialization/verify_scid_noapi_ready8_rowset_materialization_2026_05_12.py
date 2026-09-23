"""Verifier for the SCID no-API ready-8 materialization packet."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"

DATE_TAG = "2026-05-12"
PREFIX = "SCID_NOAPI_READY8"
ROUTE_ID = "SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION"
EVIDENCE_CLASS = "SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION_ONLY"
TERMINAL_DECISION = "MATERIALIZED_READY8_SOURCE_CONTROL_PACKET_G12_AUDIT_REQUIRED"
EXPECTED_READY_CARDS = {
    "ADV-001",
    "ADV-003",
    "BEH-001",
    "HAZ-001",
    "HAZ-005",
    "MAC-001",
    "MAC-004",
    "UNC-004",
}
EXPECTED_SOURCE_CANDIDATES = 3014
EXPECTED_ROWSET_ROWS = EXPECTED_SOURCE_CANDIDATES * len(EXPECTED_READY_CARDS)

REQUIRED_JSON_STEMS = [
    "ROWSET_MANIFEST",
    "TARGET_HORIZON_CONTRACT",
    "DUPLICATE_DENOMINATOR_MANIFEST",
    "PARTITION_CONTROL_MANIFEST",
    "BASELINE_CONTROL_ASSIGNMENT_MANIFEST",
    "RESULT_OPENING_GATE_DECISION",
    "BLOCKER_OR_DEPENDENCY_LEDGER",
    "EXPANSION_OBSERVATION_LEDGER",
    "NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT",
    "SOURCE_HASH_AND_ASOF_AUDIT",
    "COMPLETION_AUDIT",
    "VERIFICATION_RESULT",
    "OUTPUT_MANIFEST",
]
REQUIRED_JSONL_STEMS = ["ROWSET_ROWS"]
REQUIRED_MD_STEMS = ["SATURATION_SELF_RED_TEAM"]
REQUIRED_PY = [
    "build_scid_noapi_ready8_rowset_materialization_2026_05_12.py",
    "verify_scid_noapi_ready8_rowset_materialization_2026_05_12.py",
    "test_scid_noapi_ready8_rowset_materialization_2026_05_12.py",
]
PROMPT_FILES = [
    "G12_SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md",
    "G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_GOAL_PROMPT_2026-05-12.md",
]
STARTER_FILES = [
    "G12_SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_PACKET_AUDIT_STARTER_2026-05-12.txt",
    "G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_STARTER_2026-05-12.txt",
]
SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "credentials_touched",
    "changes_trading_risk_safety_prompt_decision_behavior",
]
FORBIDDEN_EXACT_KEYS = {
    "target_hit",
    "stop_hit",
    "outcome",
    "outcome_status",
    "actual_r",
    "broker_actual_r",
    "synthetic_path_r",
    "realized_r",
    "r",
    "pnl",
    "profit",
    "loss",
    "win_rate",
    "expectancy",
    "performance",
    "performance_metric",
    "validated_edge",
    "order_ticket",
    "deal_id",
    "position_id",
    "account_id",
    "broker_account",
}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{rel(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def recursive_key_hits(value: Any, forbidden: set[str] = FORBIDDEN_EXACT_KEYS) -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, subvalue in value.items():
            if key in forbidden:
                hits.append(key)
            hits.extend(recursive_key_hits(subvalue, forbidden))
    elif isinstance(value, list):
        for item in value:
            hits.extend(recursive_key_hits(item, forbidden))
    return hits


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/",
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_GOAL_PROMPT_2026-05-12.md",
        ".context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "run_agent.py", "scripts/canary")
    raw_blob_suffixes = (".scid", ".depth", ".parquet", ".zip", ".bin", ".jsonl.gz")
    entries = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in allowed_prefixes)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(forbidden_live_prefixes),
                "scoped_raw_market_blob": scoped and path.endswith(raw_blob_suffixes),
            }
        )
    scoped_entries = [row for row in entries if row["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "scoped_entries": scoped_entries,
        "unscoped_entry_count": len(entries) - len(scoped_entries),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def refresh_completion(result: dict[str, Any], mark_focused_tests_ok: bool) -> None:
    path = artifact_path("COMPLETION_AUDIT")
    if not path.exists():
        return
    completion = read_json(path)
    completion["standalone_verifier_ok"] = result["ok"]
    completion["standalone_verifier_failures"] = result["failures"]
    if mark_focused_tests_ok:
        completion["focused_tests_ok"] = True
    for row in completion.get("prompt_to_artifact_checklist", []):
        if row.get("requirement") == "standalone verifier and focused tests pass":
            row["satisfied"] = result["ok"] and bool(mark_focused_tests_ok)
            row["evidence"] = rel(artifact_path("VERIFICATION_RESULT"))
    non_commit_rows = [
        row
        for row in completion.get("prompt_to_artifact_checklist", [])
        if row.get("requirement") != "scoped artifacts and context refresh committed"
    ]
    completion["completion_standard_satisfied_before_commit"] = all(
        row.get("satisfied") is True for row in non_commit_rows
    )
    completion["completion_standard_satisfied"] = all(
        row.get("satisfied") is True for row in completion.get("prompt_to_artifact_checklist", [])
    )
    completion["can_mark_goal_complete"] = completion["completion_standard_satisfied_before_commit"]
    write_json(path, completion)


def refresh_output_manifest(result: dict[str, Any]) -> None:
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    if not manifest_path.exists():
        return
    excluded = {manifest_path.resolve()}
    paths = set()
    for path in ROUTE_DIR.iterdir():
        if path.is_file() and path.resolve() not in excluded:
            paths.add(path)
    for name in PROMPT_FILES:
        path = PROMPT_DIR / name
        if path.exists():
            paths.add(path)
    manifest = read_json(manifest_path)
    manifest["artifact_count"] = len(paths)
    manifest["artifacts"] = [
        {"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in sorted(paths)
    ]
    manifest["verification_result"] = {
        "path": rel(artifact_path("VERIFICATION_RESULT")),
        "ok": result["ok"],
        "failure_count": result["failure_count"],
        "can_mark_goal_complete": result["can_mark_goal_complete"],
    }
    write_json(manifest_path, manifest)


def write_focused_test_result(result: dict[str, Any]) -> None:
    payload = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "focused_tests_ok": True,
        "focused_pytest_command": (
            "python -m pytest "
            "research/science_program_2026_05/06_outcome_testing/"
            "scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/"
            "test_scid_noapi_ready8_rowset_materialization_2026_05_12.py -q"
        ),
        "standalone_verifier_ok": result["ok"],
    }
    write_json(artifact_path("FOCUSED_TEST_RESULT"), payload)


def verify(mark_focused_tests_ok: bool = False, write_result: bool = True) -> dict[str, Any]:
    failures: list[str] = []
    loaded: dict[str, Any] = {}

    for stem in REQUIRED_JSON_STEMS:
        path = artifact_path(stem)
        if not path.exists():
            failures.append(f"missing json artifact: {rel(path)}")
            continue
        loaded[stem] = read_json(path)
    for stem in REQUIRED_JSONL_STEMS:
        path = artifact_path(stem, ".jsonl")
        if not path.exists():
            failures.append(f"missing jsonl artifact: {rel(path)}")
    for stem in REQUIRED_MD_STEMS:
        path = artifact_path(stem, ".md")
        if not path.exists():
            failures.append(f"missing markdown artifact: {rel(path)}")
    for name in REQUIRED_PY:
        if not (ROUTE_DIR / name).exists():
            failures.append(f"missing python artifact: {name}")
    for name in PROMPT_FILES:
        if not (PROMPT_DIR / name).exists():
            failures.append(f"missing prompt artifact: {name}")
    for name in STARTER_FILES:
        if not (ROUTE_DIR / name).exists():
            failures.append(f"missing starter artifact: {name}")

    syntax = syntax_parse([ROUTE_DIR / name for name in REQUIRED_PY if (ROUTE_DIR / name).exists()])
    failures.extend(syntax["failures"])

    for stem, payload in loaded.items():
        if not isinstance(payload, dict):
            failures.append(f"{stem}: payload is not object")
            continue
        if payload.get("route_id") != ROUTE_ID:
            failures.append(f"{stem}: route_id mismatch")
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append(f"{stem}: evidence_class mismatch")
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{stem}: promotion verdict mismatch")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{stem}: expected {flag}=false, got {payload.get(flag)!r}")

    rows = []
    row_path = artifact_path("ROWSET_ROWS", ".jsonl")
    if row_path.exists():
        rows = iter_jsonl(row_path)
    if len(rows) != EXPECTED_ROWSET_ROWS:
        failures.append(f"rowset row count {len(rows)} != {EXPECTED_ROWSET_ROWS}")

    card_ids = {row.get("card_id") for row in rows}
    if card_ids != EXPECTED_READY_CARDS:
        failures.append(f"rowset card ids mismatch: {sorted(card_ids)}")
    candidate_ids = {row.get("candidate_input_row_id") for row in rows}
    duplicate_keys = {row.get("duplicate_proxy_denominator_key") for row in rows}
    if len(candidate_ids) != EXPECTED_SOURCE_CANDIDATES:
        failures.append(f"candidate id count {len(candidate_ids)} != {EXPECTED_SOURCE_CANDIDATES}")
    if len(duplicate_keys) != EXPECTED_SOURCE_CANDIDATES:
        failures.append(f"duplicate key count {len(duplicate_keys)} != {EXPECTED_SOURCE_CANDIDATES}")

    per_card = {}
    forbidden_row_hits = []
    asof_violations = []
    missing_hash = []
    row_hashes = set()
    for row in rows:
        per_card[row["card_id"]] = per_card.get(row["card_id"], 0) + 1
        hits = [key for key in row if key in FORBIDDEN_EXACT_KEYS]
        if hits:
            forbidden_row_hits.append((row.get("rowset_row_id"), hits))
        if not row.get("source_hash") or not row.get("row_hash"):
            missing_hash.append(row.get("rowset_row_id"))
        if row.get("source_observed_asof_utc") > row.get("decision_asof_utc"):
            asof_violations.append(row.get("rowset_row_id"))
        row_hashes.add(row.get("row_hash"))
    if set(per_card.values()) != {EXPECTED_SOURCE_CANDIDATES}:
        failures.append(f"per-card row counts mismatch: {per_card}")
    if forbidden_row_hits:
        failures.append(f"forbidden row keys present: {forbidden_row_hits[:5]}")
    if asof_violations:
        failures.append(f"as-of violations present: {asof_violations[:5]}")
    if missing_hash:
        failures.append(f"missing source/row hash: {missing_hash[:5]}")
    if len(row_hashes) != len(rows):
        failures.append("row_hash values are not unique per rowset row")

    manifest = loaded.get("ROWSET_MANIFEST", {})
    if manifest.get("rowset_row_count") != EXPECTED_ROWSET_ROWS:
        failures.append("rowset manifest count mismatch")
    if manifest.get("accepted_card_denominator_count") != 40:
        failures.append("accepted card denominator count must remain 40")
    if manifest.get("ready_card_denominator_count") != 8:
        failures.append("ready card denominator count must remain 8")
    if manifest.get("blocked_dependency_row_count_preserved") != 32:
        failures.append("blocked dependency count must remain 32")
    if manifest.get("row_level_exclusion_count") != 0:
        failures.append("unexpected row-level exclusions")
    if manifest.get("rowset_rows_sha256") != sha256_file(row_path):
        failures.append("rowset rows sha mismatch in manifest")

    target_contract = loaded.get("TARGET_HORIZON_CONTRACT", {})
    target_hits = recursive_key_hits(target_contract)
    if target_hits:
        failures.append(f"target horizon contract has forbidden keys: {sorted(set(target_hits))}")
    if target_contract.get("target_or_hazard_hits_computed") is not False:
        failures.append("target horizon contract computed hits")
    if target_contract.get("performance_or_result_fields_present") is not False:
        failures.append("target horizon contract reports result/performance fields")

    duplicate = loaded.get("DUPLICATE_DENOMINATOR_MANIFEST", {})
    if duplicate.get("duplicate_key_collision_count") != 0:
        failures.append("duplicate key collisions detected")
    if duplicate.get("incomplete_card_expansion_count") != 0:
        failures.append("incomplete card expansion detected")
    if duplicate.get("primary_candidate_row_denominator_count") != EXPECTED_SOURCE_CANDIDATES:
        failures.append("duplicate manifest primary denominator mismatch")
    if duplicate.get("ready_card_row_denominator_count") != EXPECTED_ROWSET_ROWS:
        failures.append("duplicate manifest ready-row denominator mismatch")

    partition = loaded.get("PARTITION_CONTROL_MANIFEST", {})
    if partition.get("source_candidate_partition_count") != EXPECTED_SOURCE_CANDIDATES:
        failures.append("partition manifest source candidate count mismatch")
    if partition.get("discovery_development_status", {}).get("CONTAMINATED_OR_FORBIDDEN_POOL", {}).get("candidate_count") != 0:
        failures.append("contaminated/forbidden pool is not empty")

    baseline = loaded.get("BASELINE_CONTROL_ASSIGNMENT_MANIFEST", {})
    if baseline.get("deterministic_assignments_only") is not True:
        failures.append("baseline assignments are not marked deterministic")
    if baseline.get("result_or_performance_lookup_used") is not False:
        failures.append("baseline assignments used result/performance lookup")
    if baseline.get("row_assignment_count") != EXPECTED_ROWSET_ROWS:
        failures.append("baseline assignment row count mismatch")

    gate = loaded.get("RESULT_OPENING_GATE_DECISION", {})
    if gate.get("terminal_decision") != TERMINAL_DECISION:
        failures.append("result gate terminal decision mismatch")
    if gate.get("may_score_results_now") is not False:
        failures.append("result gate allows scoring now")
    if gate.get("g12_audit_required_before_any_result_opening") is not True:
        failures.append("result gate does not require G12 audit")

    blocker = loaded.get("BLOCKER_OR_DEPENDENCY_LEDGER", {})
    if blocker.get("ready8_source_control_blocker_count") != 0:
        failures.append("ready8 source-control blocker count is not zero")
    if blocker.get("blocked_32_dependency_row_count") != 32:
        failures.append("blocked 32 count mismatch")

    expansion = loaded.get("EXPANSION_OBSERVATION_LEDGER", {})
    if expansion.get("all_expansion_observations_remain_outside_accepted_denominator") is not True:
        failures.append("expansion observations are not quarantined from accepted denominator")
    if expansion.get("accepted_40_is_floor_not_ceiling") is not True:
        failures.append("accepted 40 floor-not-ceiling flag missing")

    no_leak = loaded.get("NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT", {})
    if no_leak.get("forbidden_row_field_hit_count") != 0:
        failures.append("no-leak audit reports forbidden row fields")
    if no_leak.get("asof_violation_count") != 0:
        failures.append("no-leak audit reports as-of violations")

    source_hash = loaded.get("SOURCE_HASH_AND_ASOF_AUDIT", {})
    if source_hash.get("source_hash_missing_count") != 0:
        failures.append("source hash audit reports missing hashes")
    if source_hash.get("source_observed_asof_lte_decision_asof_count") != EXPECTED_ROWSET_ROWS:
        failures.append("source hash/as-of audit count mismatch")

    saturation_path = artifact_path("SATURATION_SELF_RED_TEAM", ".md")
    if saturation_path.exists():
        saturation = saturation_path.read_text(encoding="utf-8")
        for phrase in [
            "3014 * 8 = 24112",
            "OB-only",
            "passively",
            "No validation",
            "accepted 40-card denominator",
        ]:
            if phrase not in saturation:
                failures.append(f"saturation missing phrase: {phrase}")

    for name in PROMPT_FILES:
        text = (PROMPT_DIR / name).read_text(encoding="utf-8") if (PROMPT_DIR / name).exists() else ""
        for phrase in ["NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"]:
            if phrase not in text:
                failures.append(f"prompt {name} missing phrase {phrase}")
    for name in STARTER_FILES:
        text = (ROUTE_DIR / name).read_text(encoding="utf-8").strip() if (ROUTE_DIR / name).exists() else ""
        if not text.startswith("/goal Follow the full controlling prompt"):
            failures.append(f"starter {name} missing /goal prefix")
        if "\n" in text:
            failures.append(f"starter {name} is not one physical line")

    git_status = scoped_git_status()
    if not git_status["no_scoped_forbidden_live_surface"]:
        failures.append("scoped git status includes forbidden live surface")
    if not git_status["no_scoped_raw_market_blob"]:
        failures.append("scoped git status includes raw market blob")

    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "terminal_decision": TERMINAL_DECISION,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_strategy_edge_claims": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "credentials_touched": False,
        "changes_trading_risk_safety_prompt_decision_behavior": False,
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "can_mark_goal_complete": not failures,
        "ready_card_count_verified": len(card_ids),
        "source_candidate_count_verified": len(candidate_ids),
        "rowset_row_count_verified": len(rows),
        "duplicate_key_count_verified": len(duplicate_keys),
        "syntax_parse": syntax,
        "scoped_git_status": git_status,
    }
    if write_result:
        write_json(artifact_path("VERIFICATION_RESULT"), result)
        refresh_completion(result, mark_focused_tests_ok=mark_focused_tests_ok)
        if mark_focused_tests_ok and result["ok"]:
            write_focused_test_result(result)
        refresh_output_manifest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
