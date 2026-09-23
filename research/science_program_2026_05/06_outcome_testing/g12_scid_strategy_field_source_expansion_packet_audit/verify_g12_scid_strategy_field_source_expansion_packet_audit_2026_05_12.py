from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
BUILD_PATH = ROUTE_DIR / "build_g12_scid_strategy_field_source_expansion_packet_audit_2026_05_12.py"
RESULT_PATH = ROUTE_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_VERIFICATION_RESULT_2026-05-12.json"


def load_builder() -> Any:
    spec = importlib.util.spec_from_file_location("g12_scid_strategy_field_audit_builder", BUILD_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load builder at {BUILD_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    builder = load_builder()
    audits, _ = builder.build_audits()
    decision = audits["decision"]["terminal_decision"]
    manifest_path = builder.output_paths()["manifest_json"]
    manifest = builder.read_json(manifest_path) if manifest_path.exists() else {}

    issues: list[dict[str, Any]] = []
    expected_ok_checks = {
        "prerequisite": audits["prerequisite"]["all_checks_passed"],
        "row_coverage": audits["row_coverage"]["row_coverage_ok"],
        "field_status": audits["field_status"]["field_status_audit_ok"],
        "fail_prospective_forbidden": audits["fail_prospective_forbidden"]["fail_prospective_forbidden_audit_ok"],
        "no_leak_surface": audits["noleak_surface"]["no_leak_surface_audit_ok"],
        "source_hash": audits["source_hash"]["source_hash_binding_ok"],
        "saturation": audits["saturation"]["saturation_complete"],
    }
    for name, ok in expected_ok_checks.items():
        if not ok:
            issues.append({"audit": name, "issue": "recomputed_check_failed"})

    if decision != builder.TERMINAL_ACCEPT:
        issues.append({"audit": "decision", "issue": "terminal_decision_not_accept", "observed": decision})

    required_manifest = {
        "context anchor",
        "prerequisite evidence-chain reconciliation audit",
        "row coverage and duplicate denominator recomputation audit",
        "field-status enum and closed-field recomputation audit",
        "fail-closed/prospective/forbidden status audit",
        "no-leak/forbidden-surface/raw-blob/trading-surface audit",
        "source hash/input binding audit",
        "saturation/self-red-team ledger",
        "decision ledger",
        "completion audit",
        "closeout verification",
        "standalone verifier",
        "focused tests",
        "next G0 synthesis/control prompt",
    }
    manifest_names = {item.get("artifact_name") for item in manifest.get("artifacts", [])}
    missing_manifest = sorted(required_manifest - manifest_names)
    if missing_manifest:
        issues.append({"audit": "manifest", "issue": "missing_required_artifacts", "missing": missing_manifest})

    next_prompt = builder.NEXT_G0_PROMPT
    if not next_prompt.exists():
        issues.append({"audit": "next_prompt", "issue": "next_g0_prompt_missing", "path": builder.rel(next_prompt)})
    else:
        text = next_prompt.read_text(encoding="utf-8")
        required_prompt_tokens = [
            "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "result-design readiness",
            "forward capture implementation",
            "broader source search",
            "negative learning",
        ]
        missing_tokens = [token for token in required_prompt_tokens if token not in text]
        if missing_tokens:
            issues.append({"audit": "next_prompt", "issue": "missing_required_tokens", "missing": missing_tokens})

    result = builder.safe_flag_payload(
        {
            "artifact_family": "verification_result",
            "ok": not issues,
            "issues": issues,
            "terminal_decision": decision,
            "candidate_rows_verified": audits["row_coverage"]["closure_rows"],
            "unique_candidate_ids_verified": audits["row_coverage"]["unique_closure_candidate_ids"],
            "row_hash_mismatch_count": audits["field_status"]["row_hash_mismatch_count"],
            "closed_source_value_mismatch_count": audits["field_status"]["closed_source_value_mismatch_count"],
            "forbidden_result_key_hit_count": audits["noleak_surface"]["closure_exact_forbidden_result_key_hit_count"],
            "forbidden_broker_key_hit_count": audits["noleak_surface"]["closure_exact_forbidden_broker_key_hit_count"],
            "raw_market_blob_paths_in_builder_diff": audits["noleak_surface"]["raw_market_blob_paths_in_builder_diff"],
            "trading_surface_paths_in_builder_diff": audits["noleak_surface"]["trading_surface_paths_in_builder_diff"],
            "safe_flags": {
                "NO_PROMOTION_VERDICT": True,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
        }
    )
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "issues": issues, "terminal_decision": decision}, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
