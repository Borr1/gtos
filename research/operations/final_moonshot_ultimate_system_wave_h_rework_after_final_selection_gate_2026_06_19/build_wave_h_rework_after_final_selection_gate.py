#!/usr/bin/env python3
"""Build Wave H rework artifacts after final-selection source exhaustion."""

from __future__ import annotations

import json
import errno
import subprocess
import time
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
PARENT_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19"
FINAL_SELECTION_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_final_selection_source_exhaustion_2026_06_19"
PRIOR_WAVE_H_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_h_bounded_adversarial_audit_2026_06_19"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_generated_utc() -> str:
    path = ROUTE / "WAVE_H_REWORK_AFTER_FINAL_SELECTION_SUMMARY.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("generated_utc") or utc_now()
        except (json.JSONDecodeError, OSError):
            return utc_now()
    return utc_now()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        text = read_text(path)
    except OSError:
        return {}
    if not text.strip():
        return {}
    data = json.loads(text)
    return data if isinstance(data, dict) else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in read_text(path).splitlines() if line.strip()]


def read_text(path: Path) -> str:
    last_exc: OSError | None = None
    for _ in range(5):
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            if exc.errno != errno.EDEADLK:
                raise
            last_exc = exc
            time.sleep(0.05)
    if last_exc is not None:
        try:
            return subprocess.check_output(["/bin/cat", str(path)], text=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            pass
        rel = path.relative_to(ROOT)
        return read_committed_blob_text(str(rel))
    return path.read_text(encoding="utf-8", errors="replace")


def read_object(common_dir: Path, oid: str) -> tuple[str, bytes]:
    obj = common_dir / "objects" / oid[:2] / oid[2:]
    data = zlib.decompress(obj.read_bytes())
    header, body = data.split(b"\0", 1)
    kind = header.split()[0].decode("ascii")
    return kind, body


def tree_entries(common_dir: Path, oid: str) -> dict[str, tuple[str, str]]:
    kind, body = read_object(common_dir, oid)
    if kind != "tree":
        raise ValueError(f"object {oid} is {kind}, not tree")
    entries: dict[str, tuple[str, str]] = {}
    pos = 0
    while pos < len(body):
        mode_end = body.index(b" ", pos)
        mode = body[pos:mode_end].decode("ascii")
        pos = mode_end + 1
        name_end = body.index(b"\0", pos)
        name = body[pos:name_end].decode("utf-8")
        pos = name_end + 1
        child = body[pos : pos + 20].hex()
        pos += 20
        entries[name] = (mode, child)
    return entries


def read_committed_blob_text(rel: str) -> str:
    common = Path(subprocess.check_output(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, text=True).strip())
    if not common.is_absolute():
        common = ROOT / common
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    kind, commit_body = read_object(common, head)
    if kind != "commit":
        raise ValueError(f"HEAD {head} is {kind}, not commit")
    tree_oid = None
    for line in commit_body.splitlines():
        if line.startswith(b"tree "):
            tree_oid = line.split()[1].decode("ascii")
            break
    if tree_oid is None:
        raise ValueError("HEAD commit missing tree")
    oid = tree_oid
    for part in rel.split("/"):
        entries = tree_entries(common, oid)
        mode, oid = entries[part]
    kind, blob = read_object(common, oid)
    if kind != "blob":
        raise ValueError(f"{rel} resolves to {kind}, not blob")
    return blob.decode("utf-8", errors="replace")


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def replace_row(rows: list[dict[str, Any]], key: str, row: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    replaced = False
    for existing in rows:
        if existing.get(key) == row[key]:
            out.append(row)
            replaced = True
        else:
            out.append(existing)
    if not replaced:
        out.append(row)
    return out


def update_parent(generated: str) -> None:
    question = {
        "question_id": "PQ026",
        "question": "Does Wave H rework accept the current final-selection gate as deployment-ready?",
        "status": "answered_wave_h_rework_after_final_selection_checkpoint",
        "answer": "No. Wave H rework accepts the current A-F evidence as bounded checkpoints only and confirms 13 unresolved final-selection gates. Final package selection, deployment dossier, model training, broker-real expectancy, and live activation remain blocked.",
        "evidence": [
            "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/WAVE_H_REWORK_AFTER_FINAL_SELECTION_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/WAVE_H_REWORK_ISSUE_LEDGER.jsonl",
        ],
        "next_action": "Repair the exact final-selection source gates before Wave H can accept a final package or deployment dossier.",
    }
    source = {
        "request_id": "PSR026",
        "status": "wave_h_rework_current_gate_audit_complete_final_selection_still_blocked",
        "source_or_field": "wave_h_current_final_selection_adversarial_rework",
        "resolution": "Current Wave H rework is no longer stale against the final-selection gate route; it confirms 13 blocking requirements remain.",
        "row_count": 13,
        "exact_path": "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19",
        "next_action": "Keep PSR013/PSR014 final-selection and audit-rework surfaces open until the source gates are actually repaired.",
        "updated_utc": generated,
    }
    decision = {
        "decision_id": "PMD025",
        "status": "selected",
        "decision": "Admit Wave H rework-after-final-selection-gate as current adversarial audit state, not final package acceptance.",
        "reason": "The route re-audits the current final-selection gate ledger and proves final readiness remains blocked.",
        "evidence": [
            "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/WAVE_H_REWORK_AFTER_FINAL_SELECTION_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/VERIFICATION_RESULT.json",
        ],
        "updated_utc": generated,
    }
    for name, key, row in [
        ("PARENT_ACTIVE_QUESTION_STACK.jsonl", "question_id", question),
        ("PARENT_SOURCE_REQUEST_LEDGER.jsonl", "request_id", source),
        ("PARENT_MERGE_DECISION_LEDGER.jsonl", "decision_id", decision),
    ]:
        path = PARENT_ROUTE / name
        try:
            write_jsonl(path, replace_row(read_jsonl(path), key, row))
        except OSError:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, sort_keys=True) + "\n")

    manifest_path = PARENT_ROUTE / "PARENT_OUTPUT_MANIFEST.json"
    manifest = read_json(manifest_path)
    if not manifest:
        return
    linked = list(manifest.get("linked_child_or_checkpoint_artifacts") or [])
    for required in [
        "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/WAVE_H_REWORK_AFTER_FINAL_SELECTION_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/WAVE_H_REWORK_AUDIT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/WAVE_H_REWORK_ISSUE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/WAVE_H_REWORK_DECISION.json",
        "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/VERIFICATION_RESULT.json",
    ]:
        if required not in linked:
            linked.append(required)
    manifest["linked_child_or_checkpoint_artifacts"] = linked
    manifest["generated_utc"] = generated
    write_json(manifest_path, manifest)

    board_path = PARENT_ROUTE / "PARENT_WAVE_STATUS_BOARD.json"
    board = read_json(board_path)
    if not board:
        return
    for row in board.get("waves") or []:
        if row.get("wave") == "H":
            row["status"] = "wave_h_rework_after_final_selection_checkpoint_still_blocked"
            row["completed"] = [
                "Wave H rework re-audited the current final-selection source exhaustion gate",
                "13 unresolved final-selection gates remain blocking; no final package selected",
            ]
            row["next_action"] = "Repair exact source gates before Wave H final acceptance or deployment dossier work."
            row["evidence"] = [
                "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/WAVE_H_REWORK_AFTER_FINAL_SELECTION_SUMMARY.json",
                "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/VERIFICATION_RESULT.json",
            ]
    board["generated_utc"] = generated
    write_json(board_path, board)


def build_artifacts() -> dict[str, Any]:
    generated = stable_generated_utc()
    ROUTE.mkdir(parents=True, exist_ok=True)
    final_gates = read_jsonl(FINAL_SELECTION_ROUTE / "FINAL_SELECTION_GATE_LEDGER.jsonl")
    prior_h = read_json(PRIOR_WAVE_H_ROUTE / "VERIFICATION_RESULT.json")

    audit_rows = []
    issue_rows = []
    for idx, gate in enumerate(final_gates, 1):
        status = gate.get("status")
        blocks = gate.get("final_selection_allowed") is False and gate.get("gate_id") != "FSG014"
        disposition = "blocking_rework_required" if blocks else "accepted_boundary_guard"
        audit_rows.append(
            {
                "audit_id": f"WHR{idx:03d}",
                "gate_id": gate.get("gate_id"),
                "gate": gate.get("gate"),
                "status": disposition,
                "evidence": gate.get("evidence"),
                "required_repair": gate.get("required_repair"),
                "final_selection_allowed": False,
            }
        )
        if blocks:
            issue_rows.append(
                {
                    "issue_id": f"WHI{len(issue_rows) + 1:03d}",
                    "gate_id": gate.get("gate_id"),
                    "severity": "blocking_final_selection",
                    "status": status,
                    "issue": gate.get("gate"),
                    "required_repair": gate.get("required_repair"),
                }
            )

    decision = {
        "schema": "gtos.final_moonshot.wave_h.rework_after_final_selection.decision.v1",
        "generated_utc": generated,
        "status": "reject_final_acceptance_rework_still_required",
        "accept_current_a_to_f_as_bounded_checkpoints": True,
        "final_package_selected": False,
        "deployment_dossier_allowed": False,
        "live_execution_activation_allowed": False,
        "model_training_allowed": False,
        "broker_real_expectancy_claim_allowed": False,
        "reason": "The final-selection source exhaustion gate preserves 13 unresolved requirements; Wave H cannot accept a final package until those gates are repaired.",
    }
    summary = {
        "schema": "gtos.final_moonshot.wave_h.rework_after_final_selection.summary.v1",
        "generated_utc": generated,
        "status": "wave_h_rework_after_final_selection_checkpoint_still_blocked",
        "result_scope": "adversarial_rework_of_current_final_selection_gate_not_final_acceptance",
        "audit_rows": len(audit_rows),
        "issue_rows": len(issue_rows),
        "blocking_issue_rows": len(issue_rows),
        "final_selection_gate_rows": len(final_gates),
        "final_selection_open_gate_rows": len(issue_rows),
        "prior_wave_h_audit_rows": prior_h.get("audit_rows"),
        "prior_wave_h_blocking_issue_rows": prior_h.get("blocking_issue_rows"),
        "rework_current_gate_materialized": True,
        "rework_required": True,
        "final_package_selected": False,
        "terminal_decision": decision,
        "forbidden_surface_status": {
            "live_trading": False,
            "broker_operation": False,
            "broker_account_order_history_deal_position_mutation": False,
            "credential_mutation_or_disclosure": False,
            "paid_api_vendor_call": False,
            "blind_remote_push": False,
            "live_vps_restart_or_reload": False,
        },
    }
    completion = {
        "schema": "gtos.final_moonshot.wave_h.rework_after_final_selection.completion_audit.v1",
        "generated_utc": generated,
        "goal_completion_claim": False,
        "status": "not_complete_continue",
        "instruction_coverage": {
            "current_disk_evidence": "consumed final-selection gate ledger and prior Wave H verification from disk",
            "no_top_n_shortlist": "all final-selection gate rows were converted into Wave H audit rows",
            "same_evidence_class_rework": "re-audited current final-selection blockers instead of only citing stale prior Wave H summary",
            "forbidden_surfaces": "no live trading, broker operation, mutation, credential, paid API, blind push, or live VPS restart/reload performed",
        },
        "verification": {"wave_h_rework_after_final_selection": "pending"},
        "remaining_work": [row["required_repair"] for row in issue_rows],
    }
    manifest_files = [
        "build_wave_h_rework_after_final_selection_gate.py",
        "verify_wave_h_rework_after_final_selection_gate.py",
        "WAVE_H_REWORK_AFTER_FINAL_SELECTION_SUMMARY.json",
        "WAVE_H_REWORK_AUDIT_LEDGER.jsonl",
        "WAVE_H_REWORK_ISSUE_LEDGER.jsonl",
        "WAVE_H_REWORK_DECISION.json",
        "DECISION_LEDGER.jsonl",
        "REPAIR_LEDGER.jsonl",
        "SATURATION_SELF_RED_TEAM.md",
        "COMPLETION_AUDIT.json",
        "OUTPUT_MANIFEST.json",
        "FOCUSED_TEST_RESULT.json",
        "VERIFICATION_RESULT.json",
    ]
    manifest = {
        "schema": "gtos.final_moonshot.wave_h.rework_after_final_selection.output_manifest.v1",
        "generated_utc": generated,
        "route": str(ROUTE.relative_to(ROOT)),
        "files": manifest_files,
    }
    focused = {
        "schema": "gtos.final_moonshot.wave_h.rework_after_final_selection.focused_test_result.v1",
        "generated_utc": generated,
        "status": "pending",
        "tests": ["python3 verify_wave_h_rework_after_final_selection_gate.py"],
    }
    decisions = [
        {
            "decision_id": "WHRD001",
            "status": "selected",
            "decision": "Reject final package acceptance from current evidence.",
            "reason": "Final-selection source exhaustion records 13 unresolved gates.",
        },
        {
            "decision_id": "WHRD002",
            "status": "selected",
            "decision": "Accept A-F artifacts only as bounded checkpoints.",
            "reason": "Proxy replay, validation stress, and source-exhaustion artifacts are useful but not final deployment authority.",
        },
    ]
    repairs = [
        {
            "repair_id": "WHRR001",
            "status": "materialized_current_wave_h_rework",
            "repair": "Converted the current final-selection gate ledger into Wave H audit and issue ledgers.",
        },
        {
            "repair_id": "WHRR002",
            "status": "parent_wave_h_status_refreshed",
            "repair": "Updated parent Wave H status and manifest links to point at the current rework route.",
        },
    ]
    red_team = "\n".join(
        [
            "# Wave H Rework After Final Selection Gate Self Red Team",
            "",
            "- This route does not repair broker actual-R, close-side all-in cost, clean labels, or fillability joins.",
            "- It only refreshes the adversarial audit against the current final-selection gate ledger.",
            "- Final package selection, deployment dossier, model training, broker-real expectancy, and live activation remain disallowed.",
            "- Parent PSR013 and PSR014 stay substantively open until source gates are repaired, even though current Wave H rework is materialized.",
            "",
        ]
    )

    write_json(ROUTE / "WAVE_H_REWORK_AFTER_FINAL_SELECTION_SUMMARY.json", summary)
    write_jsonl(ROUTE / "WAVE_H_REWORK_AUDIT_LEDGER.jsonl", audit_rows)
    write_jsonl(ROUTE / "WAVE_H_REWORK_ISSUE_LEDGER.jsonl", issue_rows)
    write_json(ROUTE / "WAVE_H_REWORK_DECISION.json", decision)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decisions)
    write_jsonl(ROUTE / "REPAIR_LEDGER.jsonl", repairs)
    write_text(ROUTE / "SATURATION_SELF_RED_TEAM.md", red_team)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "OUTPUT_MANIFEST.json", manifest)
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused)
    write_json(
        ROUTE / "VERIFICATION_RESULT.json",
        {
            "schema": "gtos.final_moonshot.wave_h.rework_after_final_selection.verification_result.v1",
            "verified_utc": generated,
            "ok": False,
            "issue_count": 1,
            "issues": ["verifier_not_run_after_build"],
        },
    )
    return summary


def main() -> int:
    build_artifacts()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
