from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CONFIDENCE_ACTIVE_GUARD"
SCHEMA_VERSION = "main_orch48_confidence_active_guard_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.components.confidence_scorer import resolve_confidence_filter_mode  # noqa: E402


CONFIG_SOURCE = REPO / "config/agent_config.yaml"
CONFIDENCE_SCORER = REPO / "src/components/confidence_scorer.py"
ORCHESTRATOR = REPO / "src/components/orchestrator.py"
CONFIDENCE_TEST = REPO / "tests/test_confidence_scorer.py"
AI_AUDIT_TEST = REPO / "tests/research_infra/test_ai_decision_architecture_audit.py"
QUARANTINE_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_CONFIDENCE_FILTER_QUARANTINE_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

EXPECTED_TEST_NAMES = [
    "test_active_mode_requires_validated_promotion_flag",
    "test_active_mode_allowed_when_validation_flag_present",
    "test_unknown_mode_fails_closed_to_shadow",
    "test_confidence_filter_quarantine_row_blocks_active_promotion_without_runtime_use",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_config(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def boundary(*, runtime_behavior_effect_if_unvalidated_active_requested: bool = False) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "research_runtime_halt_active": (REPO / "pipeline_state/RESEARCH_RUNTIME_HALT.flag").exists(),
        "production_import_path_hardened": runtime_behavior_effect_if_unvalidated_active_requested,
        "runtime_behavior_effect_if_unvalidated_active_requested": runtime_behavior_effect_if_unvalidated_active_requested,
        "current_runtime_behavior_changed": False,
        "runtime_trading_or_live_broker_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
    }


def code_surface(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "bytes": path.stat().st_size,
        "lines": count_lines(path),
        "sha256": sha256_path(path),
    }


def mode_guard_row(config: dict[str, Any]) -> dict[str, Any]:
    current = resolve_confidence_filter_mode(config)
    active_unvalidated = resolve_confidence_filter_mode({"confidence_filter_mode": "active"})
    active_validated = resolve_confidence_filter_mode(
        {
            "confidence_filter_mode": "active",
            "confidence_filter_active_promotion": {"validated": True},
        }
    )
    unknown = resolve_confidence_filter_mode({"confidence_filter_mode": "invalid"})
    return {
        "confidence_active_guard_row_id": "MAIN-ORCH48-CONFIDENCE-ACTIVE-GUARD-00000001",
        "audit_surface": "confidence_filter_mode_guard_behavior",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(CONFIG_SOURCE),
        "source_sha256": sha256_path(CONFIG_SOURCE),
        "current_requested_mode": current.requested_mode,
        "current_effective_mode": current.effective_mode,
        "current_blocked_reason": current.blocked_reason,
        "active_unvalidated_effective_mode": active_unvalidated.effective_mode,
        "active_unvalidated_blocked_reason": active_unvalidated.blocked_reason,
        "active_validated_effective_mode": active_validated.effective_mode,
        "unknown_mode_effective_mode": unknown.effective_mode,
        "unknown_mode_blocked_reason": unknown.blocked_reason,
        "current_runtime_behavior_changed": False,
        "implementation_decision": "KEEP_CONFIDENCE_FILTER_SHADOW_AND_BLOCK_UNVALIDATED_ACTIVE_MODE",
        "research_boundary": boundary(runtime_behavior_effect_if_unvalidated_active_requested=True),
    }


def runtime_patch_row(confidence_text: str, orchestrator_text: str) -> dict[str, Any]:
    return {
        "confidence_active_guard_row_id": "MAIN-ORCH48-CONFIDENCE-ACTIVE-GUARD-00000002",
        "audit_surface": "confidence_filter_runtime_guard_patch",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": f"{display_path(CONFIDENCE_SCORER)}, {display_path(ORCHESTRATOR)}",
        "source_sha256": {
            display_path(CONFIDENCE_SCORER): sha256_path(CONFIDENCE_SCORER),
            display_path(ORCHESTRATOR): sha256_path(ORCHESTRATOR),
        },
        "resolver_helper_present": "def resolve_confidence_filter_mode" in confidence_text,
        "active_validation_flag_checked": "confidence_filter_active_promotion" in confidence_text,
        "orchestrator_uses_resolver": "resolve_confidence_filter_mode(self.config)" in orchestrator_text,
        "unvalidated_active_warning_present": "blocked_reason" in orchestrator_text,
        "repo_runtime_guard_code_changed": True,
        "implementation_decision": "WIRE_CONFIDENCE_FILTER_MODE_RESOLVER_BEFORE_LOW_CONFIDENCE_SKIP_BRANCH",
        "research_boundary": boundary(runtime_behavior_effect_if_unvalidated_active_requested=True),
    }


def test_coverage_row(test_texts: dict[str, str]) -> dict[str, Any]:
    combined = "\n".join(test_texts.values())
    covered = {name: name in combined for name in EXPECTED_TEST_NAMES}
    return {
        "confidence_active_guard_row_id": "MAIN-ORCH48-CONFIDENCE-ACTIVE-GUARD-00000003",
        "audit_surface": "confidence_filter_active_guard_test_coverage",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": ", ".join(display_path(path) for path in (CONFIDENCE_TEST, AI_AUDIT_TEST)),
        "source_sha256": {
            display_path(CONFIDENCE_TEST): sha256_path(CONFIDENCE_TEST),
            display_path(AI_AUDIT_TEST): sha256_path(AI_AUDIT_TEST),
        },
        "expected_test_names": EXPECTED_TEST_NAMES,
        "expected_test_name_coverage": covered,
        "expected_test_names_covered_rows": sum(covered.values()),
        "implementation_decision": "TEST_ACTIVE_MODE_QUARANTINE_AND_B12_AUDIT_INHERITANCE",
        "research_boundary": boundary(),
    }


def inherited_quarantine_row(quarantine_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "confidence_active_guard_row_id": "MAIN-ORCH48-CONFIDENCE-ACTIVE-GUARD-00000004",
        "audit_surface": "confidence_filter_quarantine_inheritance",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(QUARANTINE_SUMMARY),
        "source_sha256": sha256_path(QUARANTINE_SUMMARY),
        "inherited_confidence_filter_mode": quarantine_summary.get("confidence_filter_mode"),
        "inherited_b12_confidence_trades_evaluated": int(quarantine_summary.get("b12_confidence_trades_evaluated") or 0),
        "inherited_b12_confidence_predictive_strata": int(quarantine_summary.get("b12_confidence_predictive_strata") or 0),
        "inherited_confidence_filter_quarantine_rows": int(quarantine_summary.get("confidence_filter_quarantine_rows") or 0),
        "implementation_decision": "CONSUME_CONFIDENCE_QUARANTINE_EVIDENCE_INTO_ACTIVE_MODE_GUARD",
        "research_boundary": boundary(),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "audit_surface_counts": dict(sorted(Counter(row["audit_surface"] for row in rows).items())),
        "current_shadow_effective_rows": sum(row.get("current_effective_mode") == "shadow" for row in rows),
        "active_unvalidated_blocked_rows": sum(
            row.get("active_unvalidated_blocked_reason") == "active_confidence_filter_requires_validated_promotion"
            for row in rows
        ),
        "active_validated_allowed_rows": sum(row.get("active_validated_effective_mode") == "active" for row in rows),
        "unknown_mode_shadow_rows": sum(row.get("unknown_mode_effective_mode") == "shadow" for row in rows),
        "resolver_helper_present_rows": sum(bool(row.get("resolver_helper_present")) for row in rows),
        "orchestrator_uses_resolver_rows": sum(bool(row.get("orchestrator_uses_resolver")) for row in rows),
        "repo_runtime_guard_code_changed_rows": sum(bool(row.get("repo_runtime_guard_code_changed")) for row in rows),
        "expected_test_names_covered_rows": sum(int(row.get("expected_test_names_covered_rows") or 0) for row in rows),
        "inherited_b12_confidence_predictive_strata": sum(
            int(row.get("inherited_b12_confidence_predictive_strata") or 0) for row in rows
        ),
        "runtime_behavior_effect_if_unvalidated_active_requested_rows": sum(
            bool((row.get("research_boundary") or {}).get("runtime_behavior_effect_if_unvalidated_active_requested"))
            for row in rows
        ),
        "current_runtime_behavior_changed_rows": sum(
            bool((row.get("research_boundary") or {}).get("current_runtime_behavior_changed")) for row in rows
        ),
        "paid_api_or_vendor_call_rows": sum(
            bool((row.get("research_boundary") or {}).get("paid_api_or_vendor_call")) for row in rows
        ),
        "broker_operation_rows": sum(bool((row.get("research_boundary") or {}).get("broker_operation")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(
            bool((row.get("research_boundary") or {}).get("runtime_candidate_use_permitted")) for row in rows
        ),
    }


def build() -> dict[str, Any]:
    config = read_config(CONFIG_SOURCE)
    confidence_text = CONFIDENCE_SCORER.read_text(encoding="utf-8")
    orchestrator_text = ORCHESTRATOR.read_text(encoding="utf-8")
    test_texts = {
        display_path(CONFIDENCE_TEST): CONFIDENCE_TEST.read_text(encoding="utf-8"),
        display_path(AI_AUDIT_TEST): AI_AUDIT_TEST.read_text(encoding="utf-8"),
    }
    quarantine_summary = read_json(QUARANTINE_SUMMARY)
    rows = [
        mode_guard_row(config),
        runtime_patch_row(confidence_text, orchestrator_text),
        test_coverage_row(test_texts),
        inherited_quarantine_row(quarantine_summary),
    ]
    write_jsonl(OUTPUT_LEDGER, rows)
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_sources": [
            code_surface(CONFIG_SOURCE),
            code_surface(QUARANTINE_SUMMARY),
        ],
        "code_surfaces": [
            code_surface(CONFIDENCE_SCORER),
            code_surface(ORCHESTRATOR),
            code_surface(CONFIDENCE_TEST),
            code_surface(AI_AUDIT_TEST),
            code_surface(Path(__file__)),
        ],
        **summarize(rows),
        "implementation_effect": {
            "confidence_filter_active_mode_guarded": True,
            "current_confidence_filter_mode_remains_shadow": True,
            "current_runtime_behavior_changed": False,
            "research_runtime_halt_active": boundary()["research_runtime_halt_active"],
            "paid_api_or_vendor_call": False,
            "broker_operation": False,
            "runtime_trading_or_live_broker_effect": False,
            "runtime_candidate_use_permitted": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)
    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "lines": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return {
        "ok": True,
        "route_id": ROUTE_ID,
        "rows": summary["rows"],
        "active_unvalidated_blocked_rows": summary["active_unvalidated_blocked_rows"],
        "current_runtime_behavior_changed_rows": summary["current_runtime_behavior_changed_rows"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
