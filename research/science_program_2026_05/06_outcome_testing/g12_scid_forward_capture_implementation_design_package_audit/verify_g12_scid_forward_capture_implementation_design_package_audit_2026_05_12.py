"""Verifier for the G12 SCID implementation-design package audit."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


DATE = "2026-05-12"
ROUTE_ID = "G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_AUDIT"
EVIDENCE_CLASS = "G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_AUDIT_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_CONTROL_EVIDENCE_ONLY"
ROOT = Path(__file__).resolve().parent
FORBIDDEN_BLOB_SUFFIXES = (".scid", ".depth", ".parquet", ".zip")


def find_repo_root() -> Path:
    cur = ROOT
    for parent in [cur, *cur.parents]:
        if (parent / ".git").exists() and (parent / "scripts" / "generate_live_state.py").exists():
            return parent
    raise RuntimeError("repository root not found")


REPO_ROOT = find_repo_root()


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def stable_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest() -> None:
    artifacts = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel_path = path.relative_to(ROOT).as_posix()
        if rel_path in {
            f"G12_SCID_FC_IMPL_DESIGN_AUDIT_OUTPUT_MANIFEST_{DATE}.json",
            f"G12_SCID_FC_IMPL_DESIGN_AUDIT_OUTPUT_MANIFEST_{DATE}.md",
        }:
            continue
        artifacts.append(
            {
                "path": rel_path,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "raw_market_blob": path.suffix in FORBIDDEN_BLOB_SUFFIXES,
            }
        )
    payload = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "safe_flags": {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "generated_by": "verifier",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "artifact_type": "output_manifest",
        "artifact_count_excluding_manifest": len(artifacts),
        "manifest_self_hash_policy": "self_hash_excluded",
        "artifacts": artifacts,
    }
    (ROOT / f"G12_SCID_FC_IMPL_DESIGN_AUDIT_OUTPUT_MANIFEST_{DATE}.json").write_text(
        stable_json(payload), encoding="utf-8"
    )
    (ROOT / f"G12_SCID_FC_IMPL_DESIGN_AUDIT_OUTPUT_MANIFEST_{DATE}.md").write_text(
        "# G12 SCID FC Impl Design Audit Output Manifest\n\n```json\n"
        + stable_json(payload).rstrip()
        + "\n```\n",
        encoding="utf-8",
    )


def parse_python_files() -> dict[str, Any]:
    failures = []
    for path in sorted(ROOT.glob("*.py")):
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            failures.append({"path": path.name, "error": str(exc)})
    return {"ok": not failures, "method": "ast_parse_no_bytecode", "failures": failures}


def git_scope() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    route_prefix = ROOT.relative_to(REPO_ROOT).as_posix() + "/"
    rows = []
    disallowed = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().replace("\\", "/")
        row = {
            "status": line[:2],
            "path": path,
            "scoped": path.startswith(route_prefix)
            or path in {".context/LIVE_STATE.md", ".context/00_core/research_current_state.md"}
            or path.startswith(
                "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/"
            ),
        }
        rows.append(row)
        if not row["scoped"]:
            disallowed.append(row)
    return {"returncode": proc.returncode, "rows": rows, "disallowed": disallowed}


def check_safe(payload: dict[str, Any], failures: list[str], name: str) -> None:
    if payload.get("route_id") != ROUTE_ID:
        failures.append(f"{name}: route_id mismatch")
    if payload.get("evidence_class") != EVIDENCE_CLASS:
        failures.append(f"{name}: evidence_class mismatch")
    flags = payload.get("safe_flags") or payload
    if flags.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        failures.append(f"{name}: promotion verdict mismatch")
    for key, value in flags.items():
        if key != "promotion_verdict" and value is not False:
            failures.append(f"{name}: safe flag {key} is not false")


def verify() -> dict[str, Any]:
    failures: list[str] = []
    required = [
        f"G12_SCID_FC_IMPL_DESIGN_AUDIT_CONTEXT_ANCHOR_{DATE}.json",
        f"G12_SCID_FC_IMPL_DESIGN_AUDIT_SOURCE_HASH_MANIFEST_BINDING_{DATE}.json",
        f"G12_SCID_FC_IMPL_DESIGN_AUDIT_CANDIDATE_BOUNDARY_AND_UPSTREAM_RECONCILIATION_{DATE}.json",
        f"G12_SCID_FC_IMPL_DESIGN_AUDIT_CAPTURE_GROUP_RECOMPUTATION_{DATE}.json",
        f"G12_SCID_FC_IMPL_DESIGN_AUDIT_PROPOSED_PATCH_OWNER_GATE_RECOMPUTATION_{DATE}.json",
        f"G12_SCID_FC_IMPL_DESIGN_AUDIT_SCOPED_DIFF_NOLEAK_DIRTY_STATE_{DATE}.json",
        f"G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_VERIFIER_AND_FOCUSED_TESTS_{DATE}.json",
        f"G12_SCID_FC_IMPL_DESIGN_AUDIT_DECISION_LEDGER_{DATE}.json",
        f"G12_SCID_FC_IMPL_DESIGN_AUDIT_COMPLETION_AUDIT_{DATE}.json",
        f"G12_SCID_FC_IMPL_DESIGN_AUDIT_OUTPUT_MANIFEST_{DATE}.json",
        f"G12_SCID_FC_IMPL_DESIGN_ACCEPTED_NEXT_OWNER_GATED_ROUTE_PROMPT_{DATE}.md",
    ]
    for name in required:
        if not (ROOT / name).exists():
            failures.append(f"missing required artifact: {name}")

    for path in sorted(ROOT.glob("G12_SCID_FC_IMPL_DESIGN_AUDIT_*.json")):
        if (
            "_TARGET_VERIFIER_STDOUT_" in path.name
            or "_OUTPUT_MANIFEST_" in path.name
            or "_VERIFICATION_RESULT_" in path.name
        ):
            continue
        check_safe(load_json(path.name), failures, path.name)

    candidate = load_json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_CANDIDATE_BOUNDARY_AND_UPSTREAM_RECONCILIATION_{DATE}.json")
    if candidate.get("candidate_boundary_status") != "PASS":
        failures.append("candidate boundary status is not PASS")

    groups = load_json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_CAPTURE_GROUP_RECOMPUTATION_{DATE}.json")
    if groups.get("exact_ten_capture_groups_status") != "PASS":
        failures.append("capture group status is not PASS")
    if groups.get("target_capture_group_count") != 10:
        failures.append("capture group count is not 10")
    if not groups.get("all_group_contracts_complete"):
        failures.append("capture group contracts incomplete")

    patch = load_json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_PROPOSED_PATCH_OWNER_GATE_RECOMPUTATION_{DATE}.json")
    if not patch.get("all_patch_rows_owner_and_g12_gated"):
        failures.append("patch rows are not all owner/G12 gated")
    if not all(patch.get("lifecycle_ltf_orderflow_fail_closed_status", {}).values()):
        failures.append("lifecycle/LTF/orderflow fail-closed status incomplete")

    source_hash = load_json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_SOURCE_HASH_MANIFEST_BINDING_{DATE}.json")
    if source_hash.get("missing_manifest_artifacts"):
        failures.append("target manifest has missing artifacts")
    if source_hash.get("blocking_unrepaired_hash_mismatches"):
        failures.append("target manifest has blocking hash mismatches")

    scoped = load_json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_SCOPED_DIFF_NOLEAK_DIRTY_STATE_{DATE}.json")
    if not scoped.get("no_production_surface_changed"):
        failures.append("scoped diff/no-leak audit found production surface changes")

    runs = load_json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_VERIFIER_AND_FOCUSED_TESTS_{DATE}.json")
    if runs.get("target_verifier_status", {}).get("status") != "passed":
        failures.append("target verifier did not pass")
    if runs.get("target_pytest_status", {}).get("status") != "passed":
        failures.append("target focused tests did not pass")

    decision = load_json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_DECISION_LEDGER_{DATE}.json")
    if decision.get("terminal_decision") != TERMINAL_DECISION:
        failures.append("terminal decision is not accepted")
    if decision.get("blocking_reasons"):
        failures.append("decision ledger has blocking reasons")

    completion = load_json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_COMPLETION_AUDIT_{DATE}.json")
    if not completion.get("completion_standard_satisfied"):
        failures.append("completion standard not satisfied")
    if not completion.get("can_mark_goal_complete"):
        failures.append("completion audit says goal cannot be marked complete")

    manifest = load_json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_OUTPUT_MANIFEST_{DATE}.json")
    for row in manifest.get("artifacts", []):
        if row.get("raw_market_blob"):
            failures.append(f"manifest contains raw market blob: {row['path']}")

    syntax = parse_python_files()
    if not syntax["ok"]:
        failures.append("audit Python syntax parse failed")
    scope = git_scope()
    if scope["disallowed"]:
        failures.append(f"disallowed dirty state: {scope['disallowed']}")

    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "safe_flags": {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "ok": not failures,
        "failures": failures,
        "can_mark_goal_complete": not failures,
        "syntax_parse": syntax,
        "git_scope": scope,
    }
    (ROOT / f"G12_SCID_FC_IMPL_DESIGN_AUDIT_VERIFICATION_RESULT_{DATE}.json").write_text(
        stable_json(result), encoding="utf-8"
    )
    (ROOT / f"G12_SCID_FC_IMPL_DESIGN_AUDIT_VERIFICATION_RESULT_{DATE}.md").write_text(
        "# G12 SCID FC Impl Design Audit Verification Result\n\n```json\n"
        + stable_json(result).rstrip()
        + "\n```\n",
        encoding="utf-8",
    )
    write_manifest()
    return result


if __name__ == "__main__":
    verification = verify()
    print(stable_json(verification).rstrip())
    raise SystemExit(0 if verification["ok"] else 1)
