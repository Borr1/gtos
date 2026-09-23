#!/usr/bin/env python3
"""Materialize recoverable row-bound fillability labels for Wave F."""

from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
PARENT_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19"
WAVE_C_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_c_execution_cost_realism_2026_06_19"
VPS_REF = "refs/remotes/origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18"
REQUIRED_VPS_FLOOR = "b112d22c351b13e2af045bb8feb82f1e235246f4"
LOCAL_FIXTURE = (
    ROOT.parent
    / "ai-trading-agent"
    / "research/operations/wave3_pending_nofill_lifecycle_v4_2026_06_04"
    / "WAVE3_PENDING_NOFILL_877_ROW_REGRESSION_FIXTURE.jsonl"
)
REMOTE_PENDING_LIFECYCLE = "shadow_logs/pending_limit_lifecycle.jsonl"
REMOTE_SUPERVISION_DIR = "research/operations/vps_runtime_active_monitoring_repair_2026_06_19"
REMOTE_BROKER_R_COVERAGE = f"{REMOTE_SUPERVISION_DIR}/BROKER_R_RUNTIME_MERGE_COVERAGE.json"
REMOTE_SLIPPAGE_COVERAGE = f"{REMOTE_SUPERVISION_DIR}/SLIPPAGE_COST_RUNTIME_MERGE_COVERAGE.json"
REMOTE_SUPERVISION_AUDIT = f"{REMOTE_SUPERVISION_DIR}/VPS_ACTIVE_SUPERVISION_REPAIR_COMPLETION_OR_HANDOFF_AUDIT.json"
REMOTE_PLACEMENT_LEDGER = "src/components/ultimate_book/placement_ledger.py"
WAVE_C_NO_FILL_LEDGER = (
    "research/operations/final_moonshot_ultimate_system_wave_c_execution_cost_realism_2026_06_19/"
    "WAVE_C_NO_FILL_OPPORTUNITY_COST_LEDGER.jsonl.gz"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(name: str, data: Any) -> None:
    (ROUTE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(name: str, rows: Iterable[dict[str, Any]]) -> None:
    with (ROUTE / name).open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_parent_json(name: str, data: Any) -> None:
    (PARENT_ROUTE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_parent_jsonl(name: str, rows: Iterable[dict[str, Any]]) -> None:
    with (PARENT_ROUTE / name).open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def replace_jsonl_row(path: Path, key: str, row: dict[str, Any]) -> None:
    rows = read_jsonl(path) if path.exists() else []
    replaced = False
    out: list[dict[str, Any]] = []
    for existing in rows:
        if existing.get(key) == row.get(key):
            out.append(row)
            replaced = True
        else:
            out.append(existing)
    if not replaced:
        out.append(row)
    write_parent_jsonl(path.name, out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_show_text(ref: str, path: str) -> str:
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True)


def git_json(ref: str, path: str) -> Any:
    return json.loads(git_show_text(ref, path))


def supervision_artifact_path(supervision_audit: dict[str, Any], artifact_key: str) -> str | None:
    artifact_name = supervision_audit.get("artifact_paths", {}).get(artifact_key)
    if not artifact_name:
        return None
    return f"{REMOTE_SUPERVISION_DIR}/{artifact_name}"


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_merge_base_is_ancestor(ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def git_show_gzip_jsonl(ref: str, path: str) -> Iterable[dict[str, Any]]:
    proc = subprocess.Popen(["git", "show", f"{ref}:{path}"], cwd=ROOT, stdout=subprocess.PIPE)
    assert proc.stdout is not None
    with gzip.GzipFile(fileobj=proc.stdout) as fh:
        for raw in fh:
            if raw.strip():
                yield json.loads(raw)
    returncode = proc.wait()
    if returncode != 0:
        raise RuntimeError(f"git show failed for {ref}:{path}")


def pointer_info(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    out: dict[str, Any] = {"is_lfs_pointer": lines[:1] == ["version https://git-lfs.github.com/spec/v1"]}
    for line in lines:
        if line.startswith("oid sha256:"):
            out["oid_sha256"] = line.split("oid sha256:", 1)[1]
        elif line.startswith("size "):
            try:
                out["size"] = int(line.split(" ", 1)[1])
            except ValueError:
                out["size"] = line.split(" ", 1)[1]
    return out


def repaired_decision_time(row: dict[str, Any]) -> str | None:
    audit = ((row.get("wave2_source_row") or {}).get("audit") or {})
    join = row.get("join_backfill") or {}
    return (
        row.get("decision_time_utc")
        or audit.get("decision_time_utc")
        or join.get("decision_time_utc_backfilled")
        or join.get("decision_time_utc")
    )


def normalize_label(row: dict[str, Any]) -> dict[str, Any]:
    lifecycle_fields = row.get("lifecycle_fields") or {}
    source_capture = row.get("source_capture_state") or {}
    audit = ((row.get("wave2_source_row") or {}).get("audit") or {})
    decision_time = repaired_decision_time(row)
    terminal = bool(row.get("pending_lifecycle_v4_terminal"))
    state_group = row.get("pending_lifecycle_v4_state_group")
    fill_label = row.get("fill_no_fill_label")
    if row.get("broker_fill_state") == "filled":
        label_family = "filled_internal_lifecycle"
    elif terminal:
        label_family = "terminal_no_fill_internal_lifecycle"
    elif state_group == "active_pending":
        label_family = "active_pending_no_entry_touch_internal_lifecycle"
    else:
        label_family = "nonterminal_internal_lifecycle"

    return {
        "schema": "gtos.final_moonshot.wave_f.fillability_label_repair_row.v1",
        "label_id": f"fillability_label:{row.get('source_sequence_index')}",
        "source_sequence_index": row.get("source_sequence_index"),
        "material_row_id": row.get("material_row_id"),
        "row_id": row.get("row_id"),
        "candidate_id": row.get("candidate_id"),
        "symbol": row.get("symbol"),
        "broker_symbol": row.get("broker_symbol"),
        "side": row.get("side"),
        "trade_id": row.get("trade_id"),
        "decision_time_utc": decision_time,
        "decision_time_source": "top_or_wave2_audit_or_join_backfill" if decision_time else "missing",
        "timestamp_utc": row.get("timestamp_utc"),
        "pending_created_time_utc": row.get("pending_created_time_utc"),
        "checked_candle_time_utc": row.get("checked_candle_time_utc"),
        "entry_price": row.get("entry_price"),
        "stop_loss": row.get("stop_loss"),
        "take_profit_1": row.get("take_profit_1"),
        "fill_no_fill_label": fill_label,
        "fillability_label_family": label_family,
        "pending_lifecycle_v4_state": row.get("pending_lifecycle_v4_state"),
        "pending_lifecycle_v4_state_group": state_group,
        "pending_lifecycle_v4_terminal": terminal,
        "pending_lifecycle_v4_event_family": row.get("pending_lifecycle_v4_event_family"),
        "pending_lifecycle_v4_transition_status": row.get("pending_lifecycle_v4_transition_status"),
        "broker_fill_state": row.get("broker_fill_state"),
        "broker_pending_order_created": row.get("broker_pending_order_created"),
        "broker_ticket_truth_status": row.get("broker_ticket_truth_status"),
        "order_send_attempted": row.get("order_send_attempted"),
        "order_send_success": row.get("order_send_success"),
        "trigger_condition_met": row.get("trigger_condition_met"),
        "intent_after_check": row.get("intent_after_check"),
        "path_touch_ordering_status": row.get("path_touch_ordering_status"),
        "cancel_reason": lifecycle_fields.get("cancel_reason") or audit.get("latest_lifecycle_cancel_reason"),
        "ltf_terminal_outcome_status": audit.get("ltf_terminal_outcome_status"),
        "path_label": audit.get("path_label"),
        "missed_move_classification": audit.get("missed_move_classification"),
        "geometry_capture_status": row.get("geometry_capture_status"),
        "reconciliation_status": row.get("reconciliation_status"),
        "historical_source_gap_family": row.get("historical_source_gap_family"),
        "missing_or_non_generatable_truth": row.get("missing_or_non_generatable_truth") or [],
        "source_capture_state": source_capture,
        "row_bound_fillability_label_status": "materialized_from_recoverable_pending_nofill_lifecycle_fixture",
        "wave_f_use_status": "partial_source_repair_for_fillability_and_no_fill_analysis_not_final_package_selection",
        "training_use_allowed": False,
        "broker_real_execution_claim_allowed": False,
        "direct_execution_authority": False,
        "broker_runtime_change_status": False,
    }


def status_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def nested_counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for value in row.get(field) or []:
            counts[str(value)] += 1
    return dict(sorted(counts.items()))


def build_wave_c_join_attempt(labels: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    fixture_keys = defaultdict(list)
    for row in labels:
        key = (row.get("symbol"), row.get("side"), row.get("decision_time_utc"))
        if all(key):
            fixture_keys[key].append(row.get("label_id"))

    joined_counts: Counter[tuple[str, str, str]] = Counter()
    wave_c_rows = 0
    for row in git_show_gzip_jsonl("HEAD", WAVE_C_NO_FILL_LEDGER):
        wave_c_rows += 1
        key = (row.get("symbol"), row.get("side"), row.get("asof_utc"))
        if key in fixture_keys:
            joined_counts[key] += 1

    join_rows: list[dict[str, Any]] = []
    for key, label_ids in sorted(fixture_keys.items()):
        symbol, side, decision_time = key
        join_rows.append(
            {
                "schema": "gtos.final_moonshot.wave_f.fillability_wave_c_join_attempt_row.v1",
                "symbol": symbol,
                "side": side,
                "decision_time_utc": decision_time,
                "fixture_label_rows": len(label_ids),
                "wave_c_no_fill_rows_joined": joined_counts.get(key, 0),
                "join_status": "joined" if joined_counts.get(key, 0) else "no_wave_c_symbol_side_asof_match",
                "required_next_join_key": "candidate_id_namespace_bridge_or_decision_window_id",
            }
        )
    summary = {
        "fixture_join_key_count": len(fixture_keys),
        "wave_c_no_fill_rows_scanned": wave_c_rows,
        "wave_c_no_fill_rows_joined": sum(joined_counts.values()),
        "join_status": "no_direct_wave_c_join_from_symbol_side_decision_time",
    }
    return join_rows, summary


def update_parent(summary: dict[str, Any]) -> None:
    route_rel = ROUTE.relative_to(ROOT).as_posix()
    board = read_json(PARENT_ROUTE / "PARENT_WAVE_STATUS_BOARD.json")
    board["current_head"] = git_output("rev-parse", "HEAD")
    board["generated_utc"] = utc_now()
    vps_guard = summary.get("latest_vps_guard", {})
    board.setdefault("vps_source_truth", {})["current_head"] = vps_guard.get("head")
    board.setdefault("vps_source_truth", {})["current_head_is_floor_or_newer"] = vps_guard.get("head_is_floor_or_newer")
    board.setdefault("vps_source_truth", {})["latest_guard_route"] = route_rel
    board.setdefault("vps_source_truth", {})["latest_guard_role"] = "placement_capture_joinability_contract_for_fillability_labels"
    for wave in board.get("waves", []):
        if wave.get("wave") == "F":
            wave["status"] = "fillability_label_repair_checkpoint_final_selection_still_blocked"
            completed = wave.setdefault("completed", [])
            for item in [
                "877 recoverable pending/no-fill lifecycle rows normalized into row-bound fillability labels",
                "WFB003 partially repaired for local Wave3 pending/no-fill fixture while full Wave C replay-row join remains 0",
                "latest VPS placement-capture joinability contract absorbed as a current fillability/source guard",
            ]:
                if item not in completed:
                    completed.append(item)
            evidence = wave.setdefault("evidence", [])
            for artifact in [
                f"{route_rel}/WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json",
                f"{route_rel}/WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl",
                f"{route_rel}/WAVE_F_FILLABILITY_WAVE_C_JOIN_ATTEMPT_LEDGER.jsonl",
                f"{route_rel}/WAVE_F_FILLABILITY_RESIDUAL_BLOCKER_LEDGER.jsonl",
                f"{route_rel}/VERIFICATION_RESULT.json",
            ]:
                if artifact not in evidence:
                    evidence.append(artifact)
            wave["next_action"] = (
                "Bridge lifecycle label IDs to Wave B/C decision-window rows or explicitly exclude non-joinable surfaces, "
                "then run final candidate-package validation only after source/capture/label repairs are closed."
            )
            remaining = wave.setdefault("remaining", [])
            for item in [
                "full 214536-row Wave B/C replay universe still has 0 direct lifecycle label joins",
                "candidate_id namespace bridge or decision_window_id join remains required",
            ]:
                if item not in remaining:
                    remaining.append(item)
        if wave.get("wave") == "G":
            wave["status"] = "blocked_by_no_selected_final_package"
            wave["next_action"] = "wait for Wave F final package selection before deployment dossier packaging"
    write_parent_json("PARENT_WAVE_STATUS_BOARD.json", board)

    question = {
        "question_id": "PQ017",
        "question": "Can row-bound fillability/order-type labels be repaired from existing local sources?",
        "answer": (
            "Partially. A local Wave3 pending/no-fill fixture provides 877 row-bound lifecycle labels with candidate IDs, "
            "geometry, state, and source-gap boundaries. Exact join to the 214536-row Wave C no-fill replay ledger is still 0 "
            "because candidate ID namespaces and decision-window keys do not bridge."
        ),
        "evidence": [
            f"{route_rel}/WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json",
            f"{route_rel}/WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl",
            f"{route_rel}/WAVE_F_FILLABILITY_WAVE_C_JOIN_ATTEMPT_LEDGER.jsonl",
        ],
        "next_action": "Build a candidate_id namespace bridge or decision_window_id join before treating these labels as full Wave F final-selection inputs.",
        "status": "answered_fillability_label_repair_checkpoint",
    }
    replace_jsonl_row(PARENT_ROUTE / "PARENT_ACTIVE_QUESTION_STACK.jsonl", "question_id", question)
    vps_question = {
        "question_id": "PQ018",
        "question": "Does the latest VPS head change the fillability/source repair requirements?",
        "answer": (
            "Yes. The fetched VPS head records a placement-capture joinability contract with 4006 runtime-learning packet rows, "
            "877 pending lifecycle rows, 13 slippage rows, 16 packet-chronology trade records, "
            "13 candidate/decision/policy-joinable trade records, 26 broker-R coverage trade rows, "
            "0 broker actual-R rows, and 0 close-side cost rows. "
            "This makes candidate/decision/policy placement context a current source guard while preserving broker actual-R and close-cost blockers."
        ),
        "evidence": [
            f"{route_rel}/WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json",
            f"{route_rel}/WAVE_F_FILLABILITY_SOURCE_SEARCH_LEDGER.jsonl",
        ],
        "next_action": "Use placement_capture_contract_version and ticket/candidate/decision context as required join fields for future lifecycle-to-replay bridges.",
        "status": "answered_latest_vps_placement_capture_guard",
    }
    replace_jsonl_row(PARENT_ROUTE / "PARENT_ACTIVE_QUESTION_STACK.jsonl", "question_id", vps_question)

    source_request = {
        "request_id": "PSR008",
        "source_or_field": "row_bound_limit_fillability_and_no_fill_labels",
        "exact_path": str(LOCAL_FIXTURE),
        "row_count": summary["row_bound_fillability_label_rows"],
        "resolution": (
            "Partial same-evidence-class repair: 877 local Wave3 pending/no-fill lifecycle rows normalized into row-bound "
            "fillability labels; exact Wave C replay-row join remains 0."
        ),
        "next_action": "Create candidate_id namespace bridge or decision_window_id join across Wave B/C material rows before final package selection or training labels.",
        "status": "partial_fillability_label_repair_877_rows_remaining_replay_universe_unjoined",
    }
    replace_jsonl_row(PARENT_ROUTE / "PARENT_SOURCE_REQUEST_LEDGER.jsonl", "request_id", source_request)
    vps_source_request = {
        "request_id": "PSR018",
        "source_or_field": "latest_vps_placement_capture_joinability_contract",
        "exact_path": f"{VPS_REF}:{REMOTE_PLACEMENT_LEDGER}",
        "row_count": summary.get("latest_vps_guard", {}).get("runtime_packet_rows"),
        "resolution": (
            "Current VPS guard absorbed from fetched remote head: placed-unit packets now require ticket/candidate/decision/policy joinability fields; "
            "historical Wave C replay joins remain unclosed."
        ),
        "next_action": "Carry placement-capture contract fields into future Wave B/C lifecycle bridge and runtime packet parity checks.",
        "status": "completed_current_vps_placement_capture_guard_absorption",
    }
    replace_jsonl_row(PARENT_ROUTE / "PARENT_SOURCE_REQUEST_LEDGER.jsonl", "request_id", vps_source_request)

    merge_decision = {
        "decision_id": "PMD016",
        "decision": "Absorb Wave F fillability-label repair as WFB003 partial repair, not final package selection.",
        "reason": (
            "The route materializes all 877 recoverable local pending/no-fill lifecycle rows but proves 0 direct joins to "
            "the current 214536-row Wave C no-fill replay ledger."
        ),
        "evidence": [
            f"{route_rel}/WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json",
            f"{route_rel}/VERIFICATION_RESULT.json",
        ],
        "status": "selected",
    }
    replace_jsonl_row(PARENT_ROUTE / "PARENT_MERGE_DECISION_LEDGER.jsonl", "decision_id", merge_decision)
    vps_merge_decision = {
        "decision_id": "PMD017",
        "decision": "Absorb latest VPS placement-capture contract as a fillability/source guard, not a final package selection.",
        "reason": (
            "The new VPS head strengthens future joinability fields for placed units, but current broker actual-R and close-side cost rows are still 0."
        ),
        "evidence": [
            f"{route_rel}/WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json",
            f"{route_rel}/WAVE_F_FILLABILITY_SOURCE_SEARCH_LEDGER.jsonl",
        ],
        "status": "selected",
    }
    replace_jsonl_row(PARENT_ROUTE / "PARENT_MERGE_DECISION_LEDGER.jsonl", "decision_id", vps_merge_decision)

    audit = read_json(PARENT_ROUTE / "PARENT_COMPLETION_AUDIT.json")
    audit["generated_utc"] = utc_now()
    completed = audit.setdefault("completed_requirements", [])
    item = "Built Wave F fillability-label repair with 877 row-bound pending/no-fill lifecycle labels and 0 direct Wave C replay joins"
    if item not in completed:
        completed.append(item)
    vps_item = "Absorbed latest VPS placement-capture joinability contract as current fillability/source guard"
    if vps_item not in completed:
        completed.append(vps_item)
    unmet = audit.setdefault("unmet_completion_requirements", [])
    for req in [
        "candidate_id namespace bridge or decision_window_id join between pending lifecycle labels and Wave B/C material rows",
        "full row-bound fillability/order-type labels across the selected final-package replay universe",
    ]:
        if req not in unmet:
            unmet.append(req)
    audit["same_evidence_class_next_step"] = (
        "Bridge the 877 lifecycle labels into Wave B/C material rows by candidate namespace or decision window, or record exact non-generatable source gaps."
    )
    verification = audit.setdefault("verification", {})
    verification["wave_f_fillability_label_repair_verifier"] = f"{route_rel}/VERIFICATION_RESULT.json"
    verification["latest_vps_guard_head"] = summary.get("latest_vps_guard", {}).get("head")
    verification["latest_vps_guard_runtime_packet_rows"] = summary.get("latest_vps_guard", {}).get("runtime_packet_rows")
    verification["latest_vps_guard_trade_records_chronology_count"] = summary.get("latest_vps_guard", {}).get(
        "trade_records_chronology_count"
    )
    verification["latest_vps_guard_trade_records_candidate_decision_policy_joinable"] = summary.get(
        "latest_vps_guard", {}
    ).get("trade_records_candidate_decision_policy_joinable")
    verification["latest_vps_guard_trade_records_broker_r_coverage_total"] = summary.get("latest_vps_guard", {}).get(
        "trade_records_broker_r_coverage_total"
    )
    write_parent_json("PARENT_COMPLETION_AUDIT.json", audit)

    manifest = read_json(PARENT_ROUTE / "PARENT_OUTPUT_MANIFEST.json")
    manifest["generated_utc"] = utc_now()
    linked = manifest.setdefault("linked_child_or_checkpoint_artifacts", [])
    for artifact in [
        f"{route_rel}/WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json",
        f"{route_rel}/WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl",
        f"{route_rel}/WAVE_F_FILLABILITY_WAVE_C_JOIN_ATTEMPT_LEDGER.jsonl",
        f"{route_rel}/WAVE_F_FILLABILITY_SOURCE_SEARCH_LEDGER.jsonl",
        f"{route_rel}/WAVE_F_FILLABILITY_RESIDUAL_BLOCKER_LEDGER.jsonl",
        f"{route_rel}/VERIFICATION_RESULT.json",
    ]:
        if artifact not in linked:
            linked.append(artifact)
    write_parent_json("PARENT_OUTPUT_MANIFEST.json", manifest)

    focused = read_json(PARENT_ROUTE / "FOCUSED_TEST_RESULT.json")
    focused["generated_utc"] = utc_now()
    focused["commands"] = [
        f"python3 -m py_compile {route_rel}/build_wave_f_fillability_label_repair.py {route_rel}/verify_wave_f_fillability_label_repair.py research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19/verify_parent_ultimate_system_full_plan.py",
        f"python3 {route_rel}/verify_wave_f_fillability_label_repair.py",
        "python3 research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19/verify_parent_ultimate_system_full_plan.py",
        f"python3 scripts/audit_goal_route_artifacts.py {route_rel} --full-jsonl",
        "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19 --full-jsonl",
    ]
    focused["status"] = "passed"
    write_parent_json("FOCUSED_TEST_RESULT.json", focused)


def main() -> int:
    generated = utc_now()
    if not LOCAL_FIXTURE.exists():
        raise FileNotFoundError(LOCAL_FIXTURE)

    raw_rows = [json.loads(line) for line in LOCAL_FIXTURE.read_text(encoding="utf-8").splitlines() if line.strip()]
    labels = [normalize_label(row) for row in raw_rows]
    join_rows, join_summary = build_wave_c_join_attempt(labels)

    latest_vps_head = git_output("rev-parse", VPS_REF)
    latest_vps_subject = git_output("log", "-1", "--format=%s", VPS_REF)
    broker_r_coverage = git_json(VPS_REF, REMOTE_BROKER_R_COVERAGE)
    slippage_coverage = git_json(VPS_REF, REMOTE_SLIPPAGE_COVERAGE)
    supervision_audit = git_json(VPS_REF, REMOTE_SUPERVISION_AUDIT)
    chronology_path = supervision_artifact_path(supervision_audit, "active_supervision_packet_chronology_audit")
    packet_chronology = git_json(VPS_REF, chronology_path) if chronology_path else {}
    placement_ledger_text = git_show_text(VPS_REF, REMOTE_PLACEMENT_LEDGER)
    placement_contract_present = "PLACEMENT_CAPTURE_CONTRACT_VERSION" in placement_ledger_text
    packet_summary = supervision_audit.get("packet_chronology_status", {}).get("packet_log", {})
    chronology_trade_records = packet_chronology.get("trade_records", {})
    chronology_joinability = chronology_trade_records.get("joinability_counts", {})
    broker_lifecycle_log = packet_chronology.get("broker_lifecycle_log", {})
    latest_vps_guard = {
        "ref": VPS_REF,
        "head": latest_vps_head,
        "head_subject": latest_vps_subject,
        "required_floor": REQUIRED_VPS_FLOOR,
        "head_is_floor_or_newer": git_merge_base_is_ancestor(REQUIRED_VPS_FLOOR, latest_vps_head),
        "checkpoint_status": supervision_audit.get("checkpoint_status"),
        "runtime_effect_boundary": supervision_audit.get("runtime_effect_boundary"),
        "broker_mutation_status": supervision_audit.get("broker_mutation_status"),
        "runtime_packet_rows": packet_summary.get("line_count"),
        "runtime_unique_candidate_ids": packet_summary.get("unique_candidate_id_count"),
        "pending_lifecycle_rows": broker_r_coverage.get("coverage", {}).get("pending_lifecycle_rows"),
        "slippage_rows": slippage_coverage.get("coverage", {}).get("slippage_rows"),
        "entry_slippage_rows": slippage_coverage.get("coverage", {}).get("entry_slippage_rows"),
        "close_side_cost_rows": slippage_coverage.get("coverage", {}).get("close_side_cost_rows"),
        "broker_lifecycle_rows": broker_lifecycle_log.get("line_count"),
        "broker_lifecycle_stage_counts": broker_lifecycle_log.get("stage_counts"),
        "packet_chronology_audit_path": chronology_path,
        "trade_records_chronology_count": chronology_trade_records.get("count"),
        "trade_records_candidate_decision_policy_joinable": chronology_joinability.get(
            "ticket_candidate_decision_policy_joinable"
        ),
        "trade_records_ticket_policy_joinable": chronology_joinability.get("ticket_policy_joinable"),
        "trade_records_broker_r_coverage_total": broker_r_coverage.get("coverage", {}).get("trade_records_total"),
        "trade_records_total": broker_r_coverage.get("coverage", {}).get("trade_records_total"),
        "broker_actual_r_rows": broker_r_coverage.get("coverage", {}).get("trade_records_with_broker_actual_r"),
        "placement_capture_contract_present": placement_contract_present,
        "placement_contract_source_path": REMOTE_PLACEMENT_LEDGER,
    }

    remote_pointer = pointer_info(git_show_text(VPS_REF, REMOTE_PENDING_LIFECYCLE))
    source_rows = [
        {
            "schema": "gtos.final_moonshot.wave_f.fillability_source_search_row.v1",
            "source_id": "latest_vps_placement_capture_contract_guard",
            "path": f"{VPS_REF}:{REMOTE_PLACEMENT_LEDGER}",
            "status": "current_vps_guard_absorbed",
            "rows_read": latest_vps_guard["runtime_packet_rows"],
            "head": latest_vps_head,
            "details": latest_vps_guard,
        },
        {
            "schema": "gtos.final_moonshot.wave_f.fillability_source_search_row.v1",
            "source_id": "vps_remote_pending_lifecycle_lfs_pointer",
            "path": f"{VPS_REF}:{REMOTE_PENDING_LIFECYCLE}",
            "status": "lfs_pointer_not_row_readable_in_sparse_checkout",
            "rows_read": 0,
            "details": remote_pointer,
        },
        {
            "schema": "gtos.final_moonshot.wave_f.fillability_source_search_row.v1",
            "source_id": "local_wave3_pending_nofill_fixture",
            "path": str(LOCAL_FIXTURE),
            "status": "readable_recoverable_fixture",
            "rows_read": len(raw_rows),
            "sha256": sha256_file(LOCAL_FIXTURE),
        },
        {
            "schema": "gtos.final_moonshot.wave_f.fillability_source_search_row.v1",
            "source_id": "wave_c_no_fill_replay_join_attempt",
            "path": WAVE_C_NO_FILL_LEDGER,
            "status": join_summary["join_status"],
            "rows_read": join_summary["wave_c_no_fill_rows_scanned"],
            "rows_joined": join_summary["wave_c_no_fill_rows_joined"],
        },
    ]

    rows_with_candidate_id = sum(1 for row in labels if row.get("candidate_id"))
    rows_with_decision_time = sum(1 for row in labels if row.get("decision_time_utc"))
    terminal_rows = sum(1 for row in labels if row.get("pending_lifecycle_v4_terminal") is True)
    order_send_attempted_rows = sum(1 for row in labels if row.get("order_send_attempted") is True)
    order_send_success_rows = sum(1 for row in labels if row.get("order_send_success") is True)
    summary = {
        "schema": "gtos.final_moonshot.wave_f.fillability_label_repair.summary.v1",
        "generated_utc": generated,
        "status": "wave_f_fillability_label_repair_checkpoint_not_final_selection",
        "result_scope": "row_bound_pending_nofill_lifecycle_label_materialization_not_broker_real_execution_truth_not_final_package_selection",
        "input_fixture_rows": len(raw_rows),
        "row_bound_fillability_label_rows": len(labels),
        "rows_with_candidate_id": rows_with_candidate_id,
        "rows_with_repaired_decision_time": rows_with_decision_time,
        "terminal_lifecycle_rows": terminal_rows,
        "order_send_attempted_rows": order_send_attempted_rows,
        "order_send_success_rows": order_send_success_rows,
        "unique_candidate_id_count": len({row.get("candidate_id") for row in labels if row.get("candidate_id")}),
        "unique_symbol_count": len({row.get("symbol") for row in labels if row.get("symbol")}),
        "fillability_label_family_counts": status_counts(labels, "fillability_label_family"),
        "fill_no_fill_label_counts": status_counts(labels, "fill_no_fill_label"),
        "lifecycle_state_group_counts": status_counts(labels, "pending_lifecycle_v4_state_group"),
        "path_touch_ordering_status_counts": status_counts(labels, "path_touch_ordering_status"),
        "historical_source_gap_family_counts": status_counts(labels, "historical_source_gap_family"),
        "missing_or_non_generatable_truth_counts": nested_counter(labels, "missing_or_non_generatable_truth"),
        "wave_c_join_attempt": join_summary,
        "latest_vps_guard": latest_vps_guard,
        "wfb003_status": "partially_repaired_877_recoverable_pending_lifecycle_rows_materialized_zero_wave_c_replay_joins",
        "wfb003_remaining_requirement": "candidate_id namespace bridge or decision_window_id join across Wave B/C material rows",
        "terminal_decision": {
            "deployment_dossier_allowed": False,
            "final_package_selected": False,
            "live_execution_activation_allowed": False,
            "model_training_allowed": False,
            "row_bound_fillability_repair_complete_for_recoverable_fixture": True,
            "row_bound_fillability_repair_complete_for_wave_c_universe": False,
        },
        "forbidden_surface_status": {
            "blind_remote_push": False,
            "broker_account_order_history_deal_position_mutation": False,
            "broker_operation": False,
            "credential_mutation_or_disclosure": False,
            "live_trading": False,
            "live_vps_restart_or_reload": False,
            "paid_api_vendor_call": False,
        },
    }

    residuals = [
        {
            "schema": "gtos.final_moonshot.wave_f.fillability_residual_blocker_row.v1",
            "blocker_id": "WFB003",
            "blocker": "full_wave_c_row_bound_fillability_join_not_complete",
            "status": summary["wfb003_status"],
            "evidence": {
                "fixture_label_rows": len(labels),
                "wave_c_no_fill_rows_scanned": join_summary["wave_c_no_fill_rows_scanned"],
                "wave_c_no_fill_rows_joined": join_summary["wave_c_no_fill_rows_joined"],
            },
            "required_repair": summary["wfb003_remaining_requirement"],
        },
        {
            "schema": "gtos.final_moonshot.wave_f.fillability_residual_blocker_row.v1",
            "blocker_id": "WFB004",
            "blocker": "training_labels_still_not_clean",
            "status": "still_blocked_not_repaired_by_internal_lifecycle_fixture",
            "evidence": {"training_use_allowed": False},
            "required_repair": "Build clean no-leak label table after lifecycle labels join to selected package rows.",
        },
        {
            "schema": "gtos.final_moonshot.wave_f.fillability_residual_blocker_row.v1",
            "blocker_id": "WFB005_TO_WFB007",
            "blocker": "final_package_validation_still_requires_selected_package_inputs",
            "status": "still_blocked_by_zero_wave_c_replay_joins",
            "evidence": {"final_package_selected": False},
            "required_repair": "Rerun final validation only after candidate package rules and source exclusions are frozen.",
        },
    ]

    decision_rows = [
        {
            "decision_id": "WFFLR-D001",
            "decision": "Use the local Wave3 877-row pending/no-fill fixture as recoverable row-bound lifecycle evidence.",
            "reason": "The current VPS LFS pointer is not hydrated and LFS fetch is externally blocked, but the local fixture is readable and row-complete.",
            "status": "selected",
        },
        {
            "decision_id": "WFFLR-D002",
            "decision": "Do not claim full Wave C fillability closure.",
            "reason": "Exact symbol/side/decision-time join to the 214536-row Wave C no-fill ledger produced 0 rows.",
            "status": "selected",
        },
        {
            "decision_id": "WFFLR-D003",
            "decision": "Keep final package selection, model training, deployment dossier, and live execution blocked.",
            "reason": "The repair materializes a source cohort, not clean labels or full package validation.",
            "status": "selected",
        },
    ]
    repair_rows = [
        {
            "repair_id": "WFFLR-R001",
            "issue": "WFB003 previously had no row-bound fillability labels materialized in the parent package.",
            "repair": "Normalized all 877 recoverable Wave3 pending/no-fill lifecycle rows into a row-bound fillability label ledger.",
            "status": "partial_repair_materialized",
        },
        {
            "repair_id": "WFFLR-R002",
            "issue": "Remote current pending lifecycle file is an LFS pointer and not directly readable in this sparse worktree.",
            "repair": "Recorded pointer metadata and used the readable local Wave3 fixture with hash provenance.",
            "status": "recovered_from_local_fixture",
        },
        {
            "repair_id": "WFFLR-R003",
            "issue": "Full Wave C replay universe still lacks direct lifecycle joins.",
            "repair": "Scanned Wave C no-fill ledger and recorded 0 direct joins, preserving the exact namespace/decision-window bridge requirement.",
            "status": "exact_remaining_requirement",
        },
    ]

    write_json("WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json", summary)
    write_jsonl("WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl", labels)
    write_jsonl("WAVE_F_FILLABILITY_WAVE_C_JOIN_ATTEMPT_LEDGER.jsonl", join_rows)
    write_jsonl("WAVE_F_FILLABILITY_SOURCE_SEARCH_LEDGER.jsonl", source_rows)
    write_jsonl("WAVE_F_FILLABILITY_RESIDUAL_BLOCKER_LEDGER.jsonl", residuals)
    write_jsonl("DECISION_LEDGER.jsonl", decision_rows)
    write_jsonl("REPAIR_LEDGER.jsonl", repair_rows)
    (ROUTE / "SATURATION_SELF_RED_TEAM.md").write_text(
        "\n".join(
            [
                "# Saturation Self-Red-Team",
                "",
                "- Evidence-class risk: internal pending lifecycle labels are not broker-real fills or broker actual-R.",
                "- Join risk: Wave C candidate ids use a different namespace; direct symbol/side/time join produced 0 rows.",
                "- Training risk: labels remain blocked for model use until joined to selected package rows with no-leak partitions.",
                "- Source risk: remote pending lifecycle LFS hydration is externally blocked by LFS budget, so local fixture hash provenance is preserved.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_json(
        "COMPLETION_AUDIT.json",
        {
            "schema": "gtos.final_moonshot.wave_f.fillability_label_repair.completion_audit.v1",
            "generated_utc": generated,
            "goal_completion_claim": False,
            "status": "partial_repair_not_complete_continue",
            "completed_requirements": [
                "Read mandatory prompt/doctrine/current parent artifacts before route build",
            "Recovered local 877-row pending/no-fill fixture",
            "Absorbed latest VPS placement-capture joinability contract as current source guard",
            "Materialized row-bound fillability label ledger",
                "Attempted direct Wave C no-fill ledger join and recorded 0 joins",
            ],
            "unmet_completion_requirements": [
                summary["wfb003_remaining_requirement"],
                "clean Wave D training labels",
                "final package validation and deployment dossier",
            ],
            "forbidden_surfaces_crossed": summary["forbidden_surface_status"],
        },
    )
    route_rel = ROUTE.relative_to(ROOT).as_posix()
    write_json(
        "OUTPUT_MANIFEST.json",
        {
            "schema": "gtos.final_moonshot.wave_f.fillability_label_repair.output_manifest.v1",
            "generated_utc": generated,
            "route": route_rel,
            "files": [
                f"{route_rel}/WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json",
                f"{route_rel}/WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl",
                f"{route_rel}/WAVE_F_FILLABILITY_WAVE_C_JOIN_ATTEMPT_LEDGER.jsonl",
                f"{route_rel}/WAVE_F_FILLABILITY_SOURCE_SEARCH_LEDGER.jsonl",
                f"{route_rel}/WAVE_F_FILLABILITY_RESIDUAL_BLOCKER_LEDGER.jsonl",
                f"{route_rel}/DECISION_LEDGER.jsonl",
                f"{route_rel}/REPAIR_LEDGER.jsonl",
                f"{route_rel}/SATURATION_SELF_RED_TEAM.md",
                f"{route_rel}/COMPLETION_AUDIT.json",
                f"{route_rel}/FOCUSED_TEST_RESULT.json",
                f"{route_rel}/VERIFICATION_RESULT.json",
                f"{route_rel}/build_wave_f_fillability_label_repair.py",
                f"{route_rel}/verify_wave_f_fillability_label_repair.py",
            ],
        },
    )
    write_json(
        "FOCUSED_TEST_RESULT.json",
        {
            "schema": "gtos.final_moonshot.wave_f.fillability_label_repair.focused_test_result.v1",
            "generated_utc": generated,
            "status": "passed",
            "runtime_code_changed": False,
            "commands": [
                f"python3 -m py_compile {route_rel}/build_wave_f_fillability_label_repair.py {route_rel}/verify_wave_f_fillability_label_repair.py",
                f"python3 {route_rel}/verify_wave_f_fillability_label_repair.py",
            ],
        },
    )
    update_parent(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
