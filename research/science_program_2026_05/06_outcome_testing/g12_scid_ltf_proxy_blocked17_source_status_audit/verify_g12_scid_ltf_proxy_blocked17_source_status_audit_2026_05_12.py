"""Verifier for the blocked-17 LTF/orderflow/proxy G12 audit."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


ROUTE_ID = "G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT"
EVIDENCE_CLASS = "G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT_ONLY"
SCHEMA_VERSION = "g12_scid_ltf_proxy_blocked17_source_status_audit_v1"
DATE = "2026-05-12"

TARGET_VERIFIER_RESULT = "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_VERIFICATION_RESULT_2026-05-12.json"

SAFE_FLAGS: dict[str, Any] = {
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
    "opens_raw_market_data_blob_commit": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}

REQUIRED_AUDIT_FILES = {
    "context": f"G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_CONTEXT_ANCHOR_{DATE}.json",
    "denominator": f"G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DENOMINATOR_RECOMPUTATION_{DATE}.json",
    "artifacts": f"G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_ARTIFACT_AND_SAFE_FLAGS_AUDIT_{DATE}.json",
    "status": f"G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SOURCE_STATUS_RECOMPUTATION_AUDIT_{DATE}.json",
    "inventory": f"G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SEARCH_ROOT_SOURCE_INVENTORY_AUDIT_{DATE}.json",
    "proxy": f"G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_PROXY_HASH_ASOF_AUDIT_{DATE}.json",
    "noleak": f"G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_NOLEAK_FORBIDDEN_SURFACE_AUDIT_{DATE}.json",
    "decision": f"G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DECISION_LEDGER_{DATE}.json",
    "completion": f"G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_COMPLETION_AUDIT_{DATE}.json",
    "manifest": f"G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_OUTPUT_MANIFEST_{DATE}.json",
}


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repo root")


REPO_ROOT = find_repo_root()
ROUTE_DIR = Path(__file__).resolve().parent
RESULT_PATH = ROUTE_DIR / f"G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_VERIFICATION_RESULT_{DATE}.json"
NEXT_G0_PROMPT_PATH = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts/G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
NEXT_G0_STARTER_PATH = ROUTE_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_NEXT_G0_STARTER_2026-05-12.txt"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_flag_errors(name: str, payload: dict[str, Any]) -> list[str]:
    errors = []
    for key, expected in SAFE_FLAGS.items():
        if payload.get(key) != expected:
            errors.append(f"{name}: {key} expected {expected!r}, got {payload.get(key)!r}")
    if payload.get("route_id") != ROUTE_ID:
        errors.append(f"{name}: route_id mismatch")
    if payload.get("evidence_class") != EVIDENCE_CLASS:
        errors.append(f"{name}: evidence_class mismatch")
    return errors


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True)
    entries = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:] if len(line) > 3 else line
        norm = path.replace("\\", "/")
        scoped = (
            norm.startswith("research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/")
            or norm == "research/science_program_2026_05/04_goal_prompts/G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
            or norm == TARGET_VERIFIER_RESULT
            or norm == ".context/LIVE_STATE.md"
            or norm == ".context/00_core/research_current_state.md"
        )
        forbidden_live_surface = norm.startswith(("src/", "prompts/", "config/", "run_agent.py", "start_all.bat"))
        raw_blob = Path(norm).suffix.lower() in {".parquet", ".scid", ".depth", ".zst", ".dbn", ".csv"}
        entries.append(
            {
                "raw": line,
                "path": norm,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and forbidden_live_surface,
                "scoped_raw_market_blob": scoped and raw_blob,
            }
        )
    scoped_entries = [entry for entry in entries if entry["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.splitlines(),
        "entries": entries,
        "scoped_entries": scoped_entries,
        "unrelated_dirty_entry_count": len([entry for entry in entries if not entry["scoped"]]),
        "no_scoped_forbidden_live_surface": not any(entry["scoped_forbidden_live_surface"] for entry in scoped_entries),
        "no_scoped_raw_market_blob": not any(entry["scoped_raw_market_blob"] for entry in scoped_entries),
    }


def verify(*, source_route_focused_tests_ok: bool = False, g12_audit_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    payloads: dict[str, Any] = {}
    for key, filename in REQUIRED_AUDIT_FILES.items():
        path = ROUTE_DIR / filename
        if not path.exists():
            failures.append(f"missing audit artifact {filename}")
            continue
        try:
            payload = read_json(path)
        except Exception as exc:  # pragma: no cover - defensive verifier path
            failures.append(f"{filename}: parse error {exc}")
            continue
        payloads[key] = payload
        failures.extend(safe_flag_errors(key, payload))

    for key in ["denominator", "artifacts", "status", "inventory", "proxy", "noleak"]:
        if payloads.get(key, {}).get("ok") is not True:
            failures.append(f"{key} audit did not pass")

    decision = payloads.get("decision", {})
    if decision.get("terminal_decision") != "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY":
        failures.append("decision ledger did not accept source-status control evidence")
    if decision.get("terminal_blockers"):
        failures.append(f"decision ledger has blockers: {decision.get('terminal_blockers')}")

    completion = payloads.get("completion", {})
    if completion.get("completion_standard_satisfied") is not True:
        failures.append("completion audit standard not satisfied")
    if completion.get("missing_incomplete_or_weakly_verified_requirements"):
        failures.append("completion audit has missing requirements")

    if not NEXT_G0_PROMPT_PATH.exists():
        failures.append("missing next G0 prompt")
    if not NEXT_G0_STARTER_PATH.exists():
        failures.append("missing next G0 starter")
    elif "\n\n" in NEXT_G0_STARTER_PATH.read_text(encoding="utf-8"):
        failures.append("next G0 starter must be one physical line")

    target_verifier = read_json(REPO_ROOT / TARGET_VERIFIER_RESULT)
    if target_verifier.get("ok") is not True:
        failures.append("target R2 route verifier result is not ok")
    if target_verifier.get("summary", {}).get("included_card_count") != 17:
        failures.append("target R2 verifier did not confirm 17 included cards")

    if not source_route_focused_tests_ok:
        failures.append("source route focused pytest not marked ok; rerun focused tests then verify with --mark-source-route-tests-ok")
    if not g12_audit_focused_tests_ok:
        failures.append("G12 audit focused pytest not marked ok; rerun focused tests then verify with --mark-g12-tests-ok")

    git_status = scoped_git_status()
    if not git_status["no_scoped_forbidden_live_surface"]:
        failures.append("scoped diff touches forbidden live surface")
    if not git_status["no_scoped_raw_market_blob"]:
        failures.append("scoped diff adds raw market blob")

    result = {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "VERIFICATION_RESULT",
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "can_mark_goal_complete": not failures,
        "source_route_verifier_ok": target_verifier.get("ok") is True,
        "source_route_focused_tests_ok": source_route_focused_tests_ok,
        "g12_audit_focused_tests_ok": g12_audit_focused_tests_ok,
        "terminal_decision": decision.get("terminal_decision"),
        "included_card_count_verified": payloads.get("denominator", {}).get("included_card_ids") and len(payloads["denominator"]["included_card_ids"]),
        "status_counts": payloads.get("status", {}).get("status_counts", {}),
        "source_inventory_count": payloads.get("inventory", {}).get("source_inventory_count"),
        "proxy_rows_context_only": payloads.get("proxy", {}).get("proxy_rows_context_only"),
        "scoped_git_status": git_status,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-source-route-tests-ok", action="store_true")
    parser.add_argument("--mark-g12-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(
        source_route_focused_tests_ok=args.mark_source_route_tests_ok,
        g12_audit_focused_tests_ok=args.mark_g12_tests_ok,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
