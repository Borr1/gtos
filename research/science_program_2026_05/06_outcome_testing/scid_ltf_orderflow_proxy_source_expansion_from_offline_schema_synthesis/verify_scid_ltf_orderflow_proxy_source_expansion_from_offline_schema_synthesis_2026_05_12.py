"""Verifier for the SCID LTF/orderflow/proxy source-expansion route."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-12"
PREFIX = "SCID_LTF_OF_PROXY_EXPANSION"
ROUTE_ID = "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS"
EVIDENCE_CLASS = "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY"
TERMINAL_DECISION = "BUILT_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_G12_AUDIT_REQUIRED"
VERIFICATION_RESULT = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
NEXT_G12_PROMPT = (
    PROMPT_DIR
    / "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md"
)

REQUIRED_STEMS = [
    "CONTEXT_ANCHOR",
    "ACCEPTED_AUDIT_RECONCILIATION",
    "ACQUISITION_LADDER",
    "SOURCE_INVENTORY_HASH_MANIFEST",
    "LTF_SOURCE_MATRIX",
    "ORDERFLOW_PROXY_MATRIX",
    "CANDIDATE_COVERAGE_MATRIX",
    "PROXY_VALIDITY_LEDGER",
    "ASOF_NOLEAK_DUPLICATE_POLICY",
    "APPROVAL_GATE_LEDGER",
    "SATURATION_REDTEAM_LEDGER",
    "DECISION_LEDGER",
    "OUTPUT_MANIFEST",
    "COMPLETION_AUDIT",
    "CLOSEOUT_VERIFICATION",
]

REQUIRED_CATEGORIES = {
    "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE",
    "SIERRA_DEPTH_MARKET_DEPTH_SOURCE",
    "SIERRA_CONVERTED_LTF_OHLCV_SOURCE",
    "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE",
    "PATH_CONTEXT_SHADOW_SOURCE",
    "SESSION_VOLATILITY_CONTEXT_SOURCE",
    "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL",
    "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL",
}

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
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "credentials_touched",
    "changes_live_trading_behavior",
]


def repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def route_json(stem: str) -> dict[str, Any]:
    return load_json(ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json")


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{repo_path(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/",
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
    raw_blob_suffixes = (".scid", ".depth", ".parquet", ".csv", ".dly", ".bin", ".jsonl.gz")
    entries = []
    for line in proc.stdout.strip().splitlines():
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
    scoped_entries = [entry for entry in entries if entry["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "scoped_entries": scoped_entries,
        "unrelated_dirty_entry_count": len([entry for entry in entries if not entry["scoped"]]),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def verify() -> dict[str, Any]:
    failures: list[str] = []
    required_paths = []
    for stem in REQUIRED_STEMS:
        for suffix in (".json", ".md"):
            path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"
            required_paths.append(repo_path(path))
            if not path.exists():
                failures.append(f"missing required artifact: {repo_path(path)}")
    py_files = [
        ROUTE_DIR / "build_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py",
        ROUTE_DIR / "verify_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py",
        ROUTE_DIR / "test_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py",
    ]
    for path in py_files:
        if not path.exists():
            failures.append(f"missing python artifact: {repo_path(path)}")
    if not NEXT_G12_PROMPT.exists():
        failures.append(f"missing G12 prompt: {repo_path(NEXT_G12_PROMPT)}")

    syntax = syntax_parse([path for path in py_files if path.exists()])
    failures.extend(syntax["failures"])

    loaded: dict[str, dict[str, Any]] = {}
    for stem in REQUIRED_STEMS:
        path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
        if path.exists():
            loaded[stem] = load_json(path)

    for stem, payload in loaded.items():
        if payload.get("route_id") != ROUTE_ID:
            failures.append(f"{stem}: route_id mismatch")
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append(f"{stem}: evidence_class mismatch")
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{stem}: promotion verdict mismatch")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{stem}: {flag} must be false")

    recon = loaded.get("ACCEPTED_AUDIT_RECONCILIATION", {})
    candidate = recon.get("candidate_boundary", {})
    if candidate.get("candidate_rows") != 3014:
        failures.append("candidate row boundary is not 3014")
    if candidate.get("unique_candidate_input_row_ids") != 3014:
        failures.append("unique candidate id boundary is not 3014")
    if candidate.get("unique_duplicate_proxy_denominator_keys") != 3014:
        failures.append("unique duplicate key boundary is not 3014")
    if len(recon.get("ten_capture_groups", [])) != 10:
        failures.append("ten capture groups not preserved")

    acquisition = loaded.get("ACQUISITION_LADDER", {})
    if acquisition.get("searched_beyond_current_worktree") is not True:
        failures.append("acquisition ladder did not search beyond current worktree")
    if acquisition.get("searched_root_count", 0) < 10:
        failures.append("acquisition ladder is too shallow")

    inventory = loaded.get("SOURCE_INVENTORY_HASH_MANIFEST", {})
    categories = set(inventory.get("source_category_counts", {}))
    missing_categories = sorted(REQUIRED_CATEGORIES - categories)
    if missing_categories:
        failures.append(f"source inventory missing categories: {missing_categories}")
    for row in inventory.get("inventory_rows", []):
        if not row.get("sha256") and not row.get("hash_deferral_reason"):
            failures.append(f"inventory row lacks hash or deferral: {row.get('path')}")
    if inventory.get("raw_market_blob_commits_added") != 0:
        failures.append("raw market blob commit count must be zero")
    if inventory.get("forbidden_broker_account_order_history_deal_position_sources_consumed") != 0:
        failures.append("forbidden broker/account/order evidence consumed")

    ltf = loaded.get("LTF_SOURCE_MATRIX", {})
    if len(ltf.get("rows", [])) < 6:
        failures.append("LTF matrix missing required source families")
    orderflow = loaded.get("ORDERFLOW_PROXY_MATRIX", {})
    if len(orderflow.get("rows", [])) < 4:
        failures.append("orderflow matrix missing required source families")

    coverage = loaded.get("CANDIDATE_COVERAGE_MATRIX", {})
    if coverage.get("coverage_row_count") != 7:
        failures.append("candidate coverage matrix must cover seven canonical economic groups")
    if coverage.get("all_candidate_groups_covered") is not True:
        failures.append("candidate coverage matrix missing a group")
    for row in coverage.get("rows", []):
        if row.get("candidate_rows") not in {48, 421, 509}:
            failures.append(f"unexpected candidate group count: {row}")
        if "SOURCE_CONTROL" not in row.get("candidate_boundary", ""):
            failures.append(f"coverage row boundary missing source/control label: {row.get('canonical_economic_group')}")

    proxy = loaded.get("PROXY_VALIDITY_LEDGER", {})
    if proxy.get("all_proxy_rows_context_only") is not True:
        failures.append("proxy validity ledger must mark all rows context-only")
    for row in proxy.get("proxy_rows", []):
        if row.get("validity_status") != "CONTEXT_ONLY_NOT_BROKER_NATIVE_CFD_TRUTH":
            failures.append(f"proxy row not context-only: {row.get('canonical_economic_group')}")

    gates = loaded.get("APPROVAL_GATE_LEDGER", {})
    gate_ids = {row.get("gate_id") for row in gates.get("approval_gates", [])}
    for gate in {
        "GATE_RAW_SIERRA_HASH_OR_WINDOW_EXTRACT",
        "GATE_PRIOR_WORKTREE_TICK_PARQUET_CONSUMPTION",
        "GATE_DATABENTO_NEW_PULL",
        "GATE_LIVE_WIRING",
        "GATE_BROKER_ACCOUNT_ORDER_HISTORY_DEAL_POSITION",
    }:
        if gate not in gate_ids:
            failures.append(f"approval gate missing: {gate}")

    decision = loaded.get("DECISION_LEDGER", {})
    if decision.get("terminal_decision") != TERMINAL_DECISION:
        failures.append("terminal decision mismatch")
    if decision.get("ready_for_g12_audit") is not True:
        failures.append("decision must be ready for G12 audit")
    if decision.get("terminal_blockers") != []:
        failures.append("terminal blockers should be empty after exact gates are emitted")

    prompt_text = NEXT_G12_PROMPT.read_text(encoding="utf-8") if NEXT_G12_PROMPT.exists() else ""
    for phrase in [
        "3,014",
        "ten capture groups",
        "source inventory",
        "hash/hash-deferral",
        "proxy-validity",
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
        "Completion Standard",
    ]:
        if phrase not in prompt_text:
            failures.append(f"G12 prompt missing phrase: {phrase}")

    status = scoped_git_status()
    if not status["no_scoped_forbidden_live_surface"]:
        failures.append("scoped git status includes forbidden live surface")
    if not status["no_scoped_raw_market_blob"]:
        failures.append("scoped git status includes raw market blob")

    result = {
        "ok": not failures,
        "failures": failures,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "terminal_decision": TERMINAL_DECISION,
        "required_artifacts_checked": required_paths,
        "syntax": syntax,
        "candidate_rows_verified": candidate.get("candidate_rows"),
        "source_inventory_count": inventory.get("source_inventory_count"),
        "source_category_count": len(categories),
        "scoped_git_status": status,
        "can_mark_goal_complete": not failures,
        "verification_note": "Focused pytest must also pass; this verifier does not open validation or raw/live surfaces.",
    }
    VERIFICATION_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
