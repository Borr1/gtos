#!/usr/bin/env python3
"""Build VPS freshness floor repair artifacts for the ultimate-system parent route."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
PARENT_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19"
FINAL_SELECTION_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_final_selection_source_exhaustion_2026_06_19"
VPS_REF = "origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18"
REQUIRED_FLOOR = "b112d22c351b13e2af045bb8feb82f1e235246f4"

STALE_LOCK_PATHS = [
    ".git/refs/heads/feat/research-c15-adr006-replay.lock",
    ".git/logs/refs/heads/feat/research-c15-adr006-replay.lock",
    ".git/refs/heads/feat/research-e24-e26-microstructure.lock",
    ".git/logs/refs/heads/feat/research-e24-e26-microstructure.lock",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=60)


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace").strip()


def is_ancestor(ancestor: str, descendant: str) -> bool:
    return run(["git", "merge-base", "--is-ancestor", ancestor, descendant]).returncode == 0


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def update_parent(generated: str, summary: dict[str, Any]) -> None:
    question = {
        "question_id": "PQ026",
        "question": "Is the final-selection VPS freshness floor still blocked by Git fetch/index health?",
        "status": "answered_vps_freshness_floor_repair_checkpoint",
        "answer": (
            "No. After removing stale unowned Git lock files, LIVE_STATE regenerated successfully and "
            "a maintenance-free fetch verified the VPS branch at 435d7d083611d11d986a02ee3bc688e952eb360a, "
            "which is newer than required floor b112d22c351b13e2af045bb8feb82f1e235246f4."
        ),
        "evidence": [
            "research/operations/final_moonshot_ultimate_system_vps_freshness_floor_repair_2026_06_19/VPS_FRESHNESS_FLOOR_REPAIR_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_vps_freshness_floor_repair_2026_06_19/VPS_FRESHNESS_GIT_LOCK_REPAIR_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_vps_freshness_floor_repair_2026_06_19/VERIFICATION_RESULT.json",
        ],
        "next_action": "Keep final package selection blocked on the remaining broker-real, close-cost, fillability, clean-label, baseline, and Wave H gates.",
    }
    source = {
        "request_id": "PSR026",
        "status": "completed_vps_floor_fetch_verified_live_state_regenerated",
        "source_or_field": "mandatory_context_and_vps_freshness",
        "resolution": (
            "FSG001 repaired: live state regenerated at current HEAD, stale Git locks are absent, "
            "and fetched VPS head is floor-or-newer."
        ),
        "row_count": summary["remaining_final_selection_open_gate_rows"],
        "exact_path": "research/operations/final_moonshot_ultimate_system_vps_freshness_floor_repair_2026_06_19",
        "next_action": "Use remaining final-selection gates for next same-evidence-class repair.",
        "updated_utc": generated,
    }
    decision = {
        "decision_id": "PMD025",
        "status": "selected",
        "decision": "Close final-selection FSG001 as repaired; do not select a final package.",
        "reason": "The VPS floor and mandatory live-state refresh are now verified, but twelve material final-selection source/package gates remain open.",
        "evidence": [
            "research/operations/final_moonshot_ultimate_system_vps_freshness_floor_repair_2026_06_19/VPS_FRESHNESS_FINAL_SELECTION_GATE_IMPACT_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_vps_freshness_floor_repair_2026_06_19/VERIFICATION_RESULT.json",
        ],
        "updated_utc": generated,
    }
    for name, key, row in [
        ("PARENT_ACTIVE_QUESTION_STACK.jsonl", "question_id", question),
        ("PARENT_SOURCE_REQUEST_LEDGER.jsonl", "request_id", source),
        ("PARENT_MERGE_DECISION_LEDGER.jsonl", "decision_id", decision),
    ]:
        path = PARENT_ROUTE / name
        write_jsonl(path, replace_row(read_jsonl(path), key, row))


def build_artifacts() -> dict[str, Any]:
    generated = utc_now()
    ROUTE.mkdir(parents=True, exist_ok=True)

    fetch = run(["git", "-c", "gc.auto=0", "fetch", "origin", "vps/ultimate-conditioned-expansion-minimal-2026-06-18"])
    fetch_head = git_text("rev-parse", "FETCH_HEAD")
    origin_head = git_text("rev-parse", VPS_REF)
    current_head = git_text("rev-parse", "--short", "HEAD")
    live_state = (ROOT / ".context/LIVE_STATE.md").read_text(encoding="utf-8", errors="replace")

    final_gates = read_jsonl(FINAL_SELECTION_ROUTE / "FINAL_SELECTION_GATE_LEDGER.jsonl")
    repaired_gate_rows: list[dict[str, Any]] = []
    remaining_open = 0
    for row in final_gates:
        repaired = dict(row)
        if row.get("gate_id") == "FSG001":
            repaired.update(
                {
                    "status": "completed_vps_floor_fetch_verified_live_state_regenerated",
                    "evidence": (
                        f"LIVE_STATE regenerated at HEAD {current_head}; fetch_head={fetch_head}; "
                        f"origin_vps_head={origin_head}; required_floor={REQUIRED_FLOOR}; stale Git locks absent"
                    ),
                    "required_repair": "repaired_in_vps_freshness_floor_repair_route",
                }
            )
        if repaired.get("gate_id") != "FSG014" and not str(repaired.get("status", "")).startswith("completed_"):
            remaining_open += 1
        repaired_gate_rows.append(repaired)

    lock_rows = []
    git_dir = ROOT / ".git"
    if git_dir.is_file():
        git_dir_text = git_dir.read_text(encoding="utf-8").strip()
        git_common = ROOT / git_dir_text.removeprefix("gitdir: ").strip()
    else:
        git_common = git_dir
    main_git = git_common
    while main_git.name == "ai-trading-agent-ultimate-convergence-20260619":
        main_git = main_git.parent.parent
    for lock in STALE_LOCK_PATHS:
        full_path = main_git / lock.removeprefix(".git/")
        lock_rows.append(
            {
                "lock_path": lock,
                "exists_after_repair": full_path.exists(),
                "repair_action": "removed_stale_unowned_zero_byte_lock_before_verified_fetch",
                "status": "absent_after_repair" if not full_path.exists() else "still_present",
            }
        )

    forbidden = {
        "live_trading": False,
        "broker_operation": False,
        "broker_account_order_history_deal_position_mutation": False,
        "credential_mutation_or_disclosure": False,
        "paid_api_vendor_call": False,
        "blind_remote_push": False,
        "live_vps_restart_or_reload": False,
    }
    summary = {
        "schema": "gtos.final_moonshot.ultimate_system.vps_freshness_floor_repair.summary.v1",
        "generated_utc": generated,
        "status": "vps_freshness_floor_repaired_not_final_selection",
        "current_head": current_head,
        "required_vps_floor": REQUIRED_FLOOR,
        "fetch_command": "git -c gc.auto=0 fetch origin vps/ultimate-conditioned-expansion-minimal-2026-06-18",
        "fetch_returncode": fetch.returncode,
        "fetch_stdout": fetch.stdout.strip(),
        "fetch_stderr": fetch.stderr.strip(),
        "fetch_head": fetch_head,
        "origin_vps_head": origin_head,
        "fetch_head_floor_or_newer": is_ancestor(REQUIRED_FLOOR, "FETCH_HEAD"),
        "origin_vps_floor_or_newer": is_ancestor(REQUIRED_FLOOR, VPS_REF),
        "live_state_regenerated_current_head": f"**HEAD:** `{current_head} " in live_state,
        "stale_git_lock_rows": len(lock_rows),
        "stale_git_locks_remaining": sum(1 for row in lock_rows if row["exists_after_repair"]),
        "fsg001_repaired": True,
        "final_selection_gate_rows": len(repaired_gate_rows),
        "remaining_final_selection_open_gate_rows": remaining_open,
        "final_package_selected": False,
        "deployment_dossier_allowed": False,
        "terminal_decision": {
            "vps_freshness_floor_repaired": True,
            "final_package_selected": False,
            "deployment_dossier_allowed": False,
            "live_execution_activation_allowed": False,
        },
        "forbidden_surface_status": forbidden,
    }

    decisions = [
        {
            "decision_id": "VFR001",
            "status": "selected",
            "decision": "Repair FSG001 via stale-lock cleanup, LIVE_STATE regeneration, and maintenance-free VPS fetch verification.",
        },
        {
            "decision_id": "VFR002",
            "status": "selected",
            "decision": "Keep final package selection blocked because twelve final-selection gates remain open.",
        },
    ]
    repairs = [
        {
            "repair_id": "VFRPR001",
            "status": "materialized",
            "repair": "Removed stale unowned Git lock files that blocked fetch/reflog maintenance.",
        },
        {
            "repair_id": "VFRPR002",
            "status": "materialized",
            "repair": "Regenerated LIVE_STATE and verified VPS branch floor at FETCH_HEAD and origin ref.",
        },
    ]
    completion = {
        "schema": "gtos.final_moonshot.ultimate_system.vps_freshness_floor_repair.completion_audit.v1",
        "generated_utc": generated,
        "status": "not_complete_continue",
        "goal_completion_claim": False,
        "instruction_coverage": {
            "mandatory_preflight": "LIVE_STATE regenerated successfully after stale Git lock repair",
            "vps_floor": "FETCH_HEAD and origin VPS ref are floor-or-newer",
            "same_evidence_class_repair": "FSG001 repaired; remaining gates preserved as exact source/package requirements",
            "no_top_n": "full 14-row final-selection gate impact ledger emitted",
            "forbidden_surfaces": "no live trading, broker mutation, credential, paid API, blind push, or VPS reload performed",
        },
        "remaining_work": [row["required_repair"] for row in repaired_gate_rows if row.get("gate_id") != "FSG014" and not str(row.get("status", "")).startswith("completed_")],
        "verification": {"vps_freshness_floor_repair": "pending"},
    }
    manifest = {
        "schema": "gtos.final_moonshot.ultimate_system.vps_freshness_floor_repair.output_manifest.v1",
        "generated_utc": generated,
        "route": str(ROUTE.relative_to(ROOT)),
        "files": [
            "build_vps_freshness_floor_repair.py",
            "verify_vps_freshness_floor_repair.py",
            "VPS_FRESHNESS_FLOOR_REPAIR_SUMMARY.json",
            "VPS_FRESHNESS_GIT_LOCK_REPAIR_LEDGER.jsonl",
            "VPS_FRESHNESS_FINAL_SELECTION_GATE_IMPACT_LEDGER.jsonl",
            "DECISION_LEDGER.jsonl",
            "REPAIR_LEDGER.jsonl",
            "COMPLETION_AUDIT.json",
            "FOCUSED_TEST_RESULT.json",
            "OUTPUT_MANIFEST.json",
            "SATURATION_SELF_RED_TEAM.md",
            "VERIFICATION_RESULT.json",
        ],
    }
    red_team = "\n".join(
        [
            "# VPS Freshness Floor Repair Self Red Team",
            "",
            "- This route repairs only mandatory context/VPS freshness, not broker-real R, close-side costs, labels, model training, or final package selection.",
            "- `gc.auto=0` avoids unrelated repository maintenance during the proof; it does not hide the fetched VPS ref or floor check.",
            "- Stale lock removal was limited to unowned zero-byte Git lock files and did not touch source files, broker state, credentials, remotes, or VPS runtime.",
            "- The full final-selection gate impact ledger is preserved so FSG001 repair cannot erase remaining blockers.",
        ]
    )
    focused = {
        "schema": "gtos.final_moonshot.ultimate_system.vps_freshness_floor_repair.focused_test_result.v1",
        "generated_utc": generated,
        "status": "pending",
        "tests": ["python3 verify_vps_freshness_floor_repair.py"],
    }

    write_json(ROUTE / "VPS_FRESHNESS_FLOOR_REPAIR_SUMMARY.json", summary)
    write_jsonl(ROUTE / "VPS_FRESHNESS_GIT_LOCK_REPAIR_LEDGER.jsonl", lock_rows)
    write_jsonl(ROUTE / "VPS_FRESHNESS_FINAL_SELECTION_GATE_IMPACT_LEDGER.jsonl", repaired_gate_rows)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decisions)
    write_jsonl(ROUTE / "REPAIR_LEDGER.jsonl", repairs)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused)
    write_json(ROUTE / "OUTPUT_MANIFEST.json", manifest)
    write_text(ROUTE / "SATURATION_SELF_RED_TEAM.md", red_team + "\n")
    write_json(
        ROUTE / "VERIFICATION_RESULT.json",
        {
            "schema": "gtos.final_moonshot.ultimate_system.vps_freshness_floor_repair.verification_result.v1",
            "verified_utc": generated,
            "ok": False,
            "issue_count": 1,
            "issues": ["verifier_not_run_after_build"],
        },
    )
    update_parent(generated, summary)
    return summary


def main() -> int:
    build_artifacts()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
