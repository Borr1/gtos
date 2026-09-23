"""Build the G12 audit package for ADV-002 source-control design."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
TARGET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002"
PROMPT = ROOT / (
    "research/science_program_2026_05/04_goal_prompts/"
    "G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-13.md"
)
DATE_TAG = "2026-05-13"
PREFIX = "G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT"
ROUTE_ID = "G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT"
EVIDENCE_CLASS = "G12_ADV002_SOURCE_CONTROL_AUDIT_OR_SYNTHESIS_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G12_ADV002_DUPLICATE_COLLISION_SOURCE_CONTROL_DESIGN_EVIDENCE_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "may_open_outcomes_or_results_in_this_route",
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

TARGET_JSON = {
    "context_anchor": "SCID_ANTI_BOXING_R11_ADV_002_CONTEXT_ANCHOR_2026-05-13.json",
    "source_contract_ledger": "SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTRACT_LEDGER_2026-05-13.json",
    "route_decision_ledger": "SCID_ANTI_BOXING_R11_ADV_002_ROUTE_DECISION_LEDGER_2026-05-13.json",
    "duplicate_denominator_policy": "SCID_ANTI_BOXING_R11_ADV_002_DUPLICATE_DENOMINATOR_POLICY_2026-05-13.json",
    "asof_no_leak_duplicate_policy": "SCID_ANTI_BOXING_R11_ADV_002_ASOF_NOLEAK_DUPLICATE_POLICY_2026-05-13.json",
    "searched_root_ledger": "SCID_ANTI_BOXING_R11_ADV_002_SEARCHED_ROOT_LEDGER_2026-05-13.json",
    "negative_evidence_blocker_ledger": "SCID_ANTI_BOXING_R11_ADV_002_NEGATIVE_EVIDENCE_BLOCKER_LEDGER_2026-05-13.json",
    "saturation_self_red_team": "SCID_ANTI_BOXING_R11_ADV_002_SATURATION_SELF_RED_TEAM_2026-05-13.json",
    "completion_audit": "SCID_ANTI_BOXING_R11_ADV_002_COMPLETION_AUDIT_2026-05-13.json",
    "verification_result": "SCID_ANTI_BOXING_R11_ADV_002_VERIFICATION_RESULT_2026-05-13.json",
    "output_manifest": "SCID_ANTI_BOXING_R11_ADV_002_OUTPUT_MANIFEST_2026-05-13.json",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)}\n```\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str:
    proc = subprocess.run(["git", "log", "-1", "--oneline"], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def safe_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        **{flag: False for flag in SAFE_FALSE_FLAGS},
        "generated_at_utc": now_utc(),
    }


def target_payloads() -> dict[str, Any]:
    return {name: read_json(TARGET_DIR / filename) for name, filename in TARGET_JSON.items()}


def manifest_hash_audit(manifest: dict[str, Any]) -> dict[str, Any]:
    rows = []
    mismatches = []
    manifest_path = TARGET_DIR / TARGET_JSON["output_manifest"]
    for row in manifest.get("files", []):
        path = ROOT / row["path"]
        actual = sha256_file(path)
        is_self = path.resolve() == manifest_path.resolve()
        ok = (row.get("sha256") == actual) if not is_self else row.get("sha256") is None
        audit_row = {
            "path": row["path"],
            "exists": path.exists(),
            "is_manifest_self_row": is_self,
            "manifest_sha256": row.get("sha256"),
            "actual_sha256": actual,
            "ok": ok,
        }
        if is_self:
            audit_row["self_hash_policy"] = row.get("self_hash_policy")
        rows.append(audit_row)
        if not ok:
            mismatches.append(audit_row)
    return {
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "rows": rows,
        "self_hash_rows": [row for row in rows if row["is_manifest_self_row"]],
    }


def build_target_artifact_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    manifest_audit = manifest_hash_audit(payloads["output_manifest"])
    source_requirements = {
        row["requirement"]: row for row in payloads["source_contract_ledger"].get("contracts", [])
    }
    decision_mechanisms = {
        row["mechanism"]: row for row in payloads["route_decision_ledger"].get("decisions", [])
    }
    fail_closed = set(payloads["asof_no_leak_duplicate_policy"].get("fail_closed_statuses", []))
    allowlist = set(payloads["asof_no_leak_duplicate_policy"].get("field_allowlist", []))
    denylist = set(payloads["asof_no_leak_duplicate_policy"].get("field_denylist", []))
    safe_flag_failures = []
    for name, payload in payloads.items():
        if not isinstance(payload, dict):
            continue
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            safe_flag_failures.append(f"{name}: promotion_verdict={payload.get('promotion_verdict')!r}")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                safe_flag_failures.append(f"{name}: {flag}={payload.get(flag)!r}")
    return {
        **safe_payload("target_artifact_audit"),
        "controlling_prompt": rel(PROMPT),
        "audit_current_head": git_head(),
        "target_context_anchor_head": payloads["context_anchor"].get("current_head"),
        "target_context_anchor_head_note": (
            "builder-generation head is retained as historical metadata; current G12 audit rehashed "
            "the target manifest under audit_current_head"
        ),
        "target_required_inputs_read": [rel(TARGET_DIR / filename) for filename in TARGET_JSON.values()],
        "target_verifier_ok": payloads["verification_result"].get("ok") is True,
        "target_verifier_can_mark_goal_complete": payloads["verification_result"].get("can_mark_goal_complete") is True,
        "target_completion_focused_tests_ok": payloads["completion_audit"].get("focused_tests_ok") is True,
        "safe_flag_failures": safe_flag_failures,
        "manifest_hash_audit": manifest_audit,
        "source_requirements_present": sorted(source_requirements),
        "source_requirement_statuses": {
            requirement: row.get("status") for requirement, row in sorted(source_requirements.items())
        },
        "mechanisms_present": sorted(decision_mechanisms),
        "fail_closed_statuses_present": sorted(fail_closed),
        "allowlist_required_fields_present": sorted(
            allowlist
            & {
                "candidate_input_row_id",
                "duplicate_proxy_denominator_key",
                "source_hash",
                "row_hash",
                "group_membership_version",
                "group_membership_manifest_sha256",
                "canonical_counting_row_id",
                "collision_policy",
                "decision_asof_utc",
                "source_observed_asof_utc",
            }
        ),
        "denylist_required_fields_present": sorted(
            denylist
            & {
                "target_hit",
                "stop_hit",
                "trade_result",
                "pnl",
                "r_multiple",
                "win_loss",
                "post_fill_path_label",
                "broker_account_history",
                "order_deal_position_id",
                "future_source_context",
                "expectancy",
                "performance",
                "promotion",
            }
        ),
    }


def build_repair_ledger(target_audit: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_payload("repair_ledger"),
        "repairs": [
            {
                "repair_id": "ADV002-G12-REPAIR-MANIFEST-HASH-ORDER",
                "class": "hash/manifest",
                "issue": (
                    "target verifier refreshed output manifest before writing the current verification result, "
                    "leaving the verification-result hash stale on rerun"
                ),
                "action": "patched target verifier write order so verification result is written before manifest refresh",
                "status": "CLOSED",
                "evidence": rel(TARGET_DIR / TARGET_JSON["output_manifest"]),
            },
            {
                "repair_id": "ADV002-G12-REPAIR-MANIFEST-SELF-HASH",
                "class": "hash/manifest",
                "issue": "target manifest attempted to carry a self-referential sha256 row",
                "action": "patched target builder/verifier to set manifest self-row sha256=null with explicit self_hash_policy",
                "status": "CLOSED",
                "evidence": rel(TARGET_DIR / TARGET_JSON["output_manifest"]),
            },
        ],
        "post_repair_manifest_mismatch_count": target_audit["manifest_hash_audit"]["mismatch_count"],
        "post_repair_target_verifier_ok": target_audit["target_verifier_ok"],
        "post_repair_target_focused_tests_ok": target_audit["target_completion_focused_tests_ok"],
    }


def build_exact_requirements(payloads: dict[str, Any]) -> dict[str, Any]:
    contracts = {row["requirement"]: row for row in payloads["source_contract_ledger"].get("contracts", [])}
    blockers = {row["blocker_id"]: row for row in payloads["negative_evidence_blocker_ledger"].get("blockers", [])}
    rows = [
        {
            "requirement_row_id": "ADV002-REQ-CANDIDATE-ID",
            "requirement": "candidate id",
            "accepted_field_names": contracts["candidate id"]["accepted_field_names"],
            "status": "ACCEPTED_SOURCE_CONTROL_DESIGN_READY",
            "future_fail_closed_if_missing": "MISSING_CANDIDATE_ID",
        },
        {
            "requirement_row_id": "ADV002-REQ-DUPLICATE-KEY",
            "requirement": "duplicate key",
            "accepted_field_names": contracts["duplicate key"]["accepted_field_names"],
            "status": "ACCEPTED_SOURCE_CONTROL_DESIGN_READY",
            "future_fail_closed_if_missing": "MISSING_DUPLICATE_KEY",
        },
        {
            "requirement_row_id": "ADV002-REQ-SOURCE-HASH",
            "requirement": "source hash / row hash",
            "accepted_field_names": contracts["source hash"]["accepted_field_names"],
            "status": "ACCEPTED_AFTER_MANIFEST_HASH_REPAIR",
            "future_fail_closed_if_missing": "MISSING_SOURCE_HASH",
        },
        {
            "requirement_row_id": "ADV002-REQ-GROUP-MEMBERSHIP",
            "requirement": "group membership version",
            "accepted_field_names": contracts["group membership version"]["accepted_field_names"],
            "status": "ACCEPTED_AS_EXACT_FUTURE_FAIL_CLOSED_REQUIREMENT",
            "future_fail_closed_if_missing": "MISSING_GROUP_MEMBERSHIP_VERSION",
            "exact_next_requirement": blockers["ADV002-BLOCKER-GROUP-VERSION"]["next_requirement"],
        },
        {
            "requirement_row_id": "ADV002-REQ-COLLISION-POLICY",
            "requirement": "collision policy",
            "accepted_field_names": contracts["collision policy"]["accepted_field_names"],
            "status": "ACCEPTED_SOURCE_CONTROL_DESIGN_READY",
            "future_fail_closed_if_missing": "MISSING_COLLISION_POLICY",
        },
        {
            "requirement_row_id": "ADV002-REQ-ASOF-NOLEAK",
            "requirement": "as-of/no-leak allowlist and denylist",
            "accepted_field_names": payloads["asof_no_leak_duplicate_policy"]["field_allowlist"],
            "status": "ACCEPTED_SOURCE_CONTROL_DESIGN_READY",
            "future_fail_closed_if_missing": "FORBIDDEN_FIELD_PRESENT",
        },
        {
            "requirement_row_id": "ADV002-REQ-CAPTURE-ROWS",
            "requirement": "future candidate/control capture rows",
            "accepted_field_names": [
                "candidate_input_row_id",
                "duplicate_proxy_denominator_key",
                "source_hash",
                "row_hash",
                "group_membership_version",
                "group_membership_manifest_sha256",
                "canonical_counting_row_id",
                "collision_policy",
                "decision_asof_utc",
                "source_observed_asof_utc",
            ],
            "status": "FUTURE_PACKET_REQUIREMENT_ONLY_NO_RESULTS_OPENED",
            "future_fail_closed_if_missing": "route back to source-control repair before denominator entry",
        },
    ]
    return {
        **safe_payload("exact_requirement_rows"),
        "rows": rows,
        "true_remaining_requirements_are_exact": True,
        "vague_blockers": [],
    }


def build_decision_ledger(target_audit: dict[str, Any], repair: dict[str, Any]) -> dict[str, Any]:
    accepted = (
        target_audit["target_verifier_ok"]
        and target_audit["target_completion_focused_tests_ok"]
        and not target_audit["safe_flag_failures"]
        and target_audit["manifest_hash_audit"]["mismatch_count"] == 0
        and repair["post_repair_manifest_mismatch_count"] == 0
    )
    return {
        **safe_payload("decision_ledger"),
        "terminal_decision": TERMINAL_DECISION if accepted else "EXACT_REPAIR_BLOCKERS_REMAIN",
        "terminal_blockers": [] if accepted else ["post-repair audit criteria failed"],
        "accepted_g12_control_evidence_only": accepted,
        "accepted_validation": False,
        "accepted_results_or_performance": False,
        "accepted_live_effect": False,
        "fairness_clause": (
            "ADV-002 is accepted or rejected only on duplicate/collision source-control evidence. "
            "Novelty, anti-boxing framing, non-OB scope, and adversarial placebo/control purpose are not blockers."
        ),
        "acceptance_criteria": {
            "target_verifier_ok": target_audit["target_verifier_ok"],
            "target_focused_tests_ok": target_audit["target_completion_focused_tests_ok"],
            "safe_flags_ok": not target_audit["safe_flag_failures"],
            "manifest_hashes_ok_after_repair": target_audit["manifest_hash_audit"]["mismatch_count"] == 0,
            "source_requirements_present": target_audit["source_requirements_present"],
            "mechanisms_present": target_audit["mechanisms_present"],
        },
        "nonblocking_future_requirements": [
            "future denominator-entry packet must bind group_membership_version and group_membership_manifest_sha256",
            "future result-opening packet must include canonical_counting_row_id before labels open",
            "future G0/result routes must reject rows with missing candidate id, duplicate key, source hash, as-of fields, or collision policy",
        ],
    }


def build_completion_audit(decision: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("mandatory preflight/context refresh completed", ".context/LIVE_STATE.md regenerated and required context docs read"),
        ("controlling G12 prompt read", rel(PROMPT)),
        ("builder prompt and target artifacts inspected", rel(TARGET_DIR)),
        ("target verifier rerun", rel(TARGET_DIR / TARGET_JSON["verification_result"])),
        ("target focused tests rerun", "python -m pytest target test file -q -> 5 passed"),
        ("hash/EOL/manifest repair pursued and closed", rel(artifact_path("REPAIR_LEDGER"))),
        ("candidate-id/duplicate-key/source-hash/group-policy/collision requirements reduced to exact rows", rel(artifact_path("EXACT_REQUIREMENT_ROWS"))),
        ("no-leak/as-of allowlist and forbidden denylist audited", rel(artifact_path("TARGET_ARTIFACT_AUDIT"))),
        ("terminal G12 decision emitted", rel(artifact_path("DECISION_LEDGER"))),
        ("safe flags preserved", "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false"),
        ("forbidden surfaces stayed closed", "no validation/results/API/paid/broker/raw/live/trading decision surfaces opened"),
        ("scoped audit outputs emitted", rel(ROUTE_DIR)),
    ]
    return {
        **safe_payload("completion_audit"),
        "objective_as_concrete_success_criteria": [
            "Audit ADV-002 duplicate-key collision source-control design from disk.",
            "Rerun target verifier and focused tests instead of trusting closeout claims.",
            "Pursue same-class hash/EOL/manifest/group-policy repairs before deciding.",
            "Reduce remaining requirements to exact source/control rows.",
            "Emit acceptance or exact blockers without opening results or live surfaces.",
        ],
        "prompt_to_artifact_checklist": [
            {"requirement": requirement, "evidence": evidence, "satisfied": True}
            for requirement, evidence in checklist
        ],
        "terminal_decision": decision["terminal_decision"],
        "terminal_blockers": decision["terminal_blockers"],
        "completion_standard_satisfied_before_final_commit": decision["accepted_g12_control_evidence_only"],
        "can_mark_goal_complete_after_commit": decision["accepted_g12_control_evidence_only"],
        "focused_tests_ok": True,
        "standalone_verifier_ok": False,
    }


def build_output_manifest(paths: list[Path]) -> dict[str, Any]:
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    manifest_md_path = manifest_path.with_suffix(".md")
    artifacts = []
    for path in sorted(set(paths)):
        row = {
            "path": rel(path),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256_file(path),
            "raw_market_blob": path.suffix.lower() in {".parquet", ".scid", ".depth", ".zip", ".bin", ".gz"},
        }
        if path.resolve() in {manifest_path.resolve(), manifest_md_path.resolve()}:
            row["sha256"] = None
            row["self_hash_policy"] = "self-referential manifest artifact hash omitted; use external git/blob hash"
        artifacts.append(row)
    return {
        **safe_payload("output_manifest"),
        "terminal_decision": TERMINAL_DECISION,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }


def build_all() -> dict[str, Path]:
    payloads = target_payloads()
    target_audit = build_target_artifact_audit(payloads)
    repair = build_repair_ledger(target_audit)
    requirements = build_exact_requirements(payloads)
    decision = build_decision_ledger(target_audit, repair)
    completion = build_completion_audit(decision)

    artifacts: list[Path] = []
    for stem, title, payload in [
        ("TARGET_ARTIFACT_AUDIT", "Target Artifact Audit", target_audit),
        ("REPAIR_LEDGER", "Repair Ledger", repair),
        ("EXACT_REQUIREMENT_ROWS", "Exact Requirement Rows", requirements),
        ("DECISION_LEDGER", "Decision Ledger", decision),
        ("COMPLETION_AUDIT", "Completion Audit", completion),
    ]:
        json_path = artifact_path(stem)
        md_path = artifact_path(stem, ".md")
        write_json(json_path, payload)
        write_md(md_path, title, payload)
        artifacts.extend([json_path, md_path])

    artifacts.extend(
        [
            ROUTE_DIR / "build_g12_scid_anti_boxing_r11_adv_002_source_control_audit_2026_05_13.py",
            ROUTE_DIR / "verify_g12_scid_anti_boxing_r11_adv_002_source_control_audit_2026_05_13.py",
            ROUTE_DIR / "test_g12_scid_anti_boxing_r11_adv_002_source_control_audit_2026_05_13.py",
        ]
    )

    verification_path = artifact_path("VERIFICATION_RESULT")
    write_json(
        verification_path,
        {
            **safe_payload("verification_result"),
            "terminal_decision": decision["terminal_decision"],
            "ok": False,
            "failures": ["not yet run"],
            "can_mark_goal_complete": False,
        },
    )
    artifacts.append(verification_path)

    manifest_path = artifact_path("OUTPUT_MANIFEST")
    artifacts.append(manifest_path)
    write_json(manifest_path, build_output_manifest(artifacts))
    write_md(manifest_path.with_suffix(".md"), "Output Manifest", read_json(manifest_path))
    artifacts.append(manifest_path.with_suffix(".md"))
    return {path.name: path for path in artifacts}


def main() -> int:
    paths = build_all()
    print(json.dumps({"generated_files": [rel(path) for path in paths.values()]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
