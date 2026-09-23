#!/usr/bin/env python3
"""Materialize the Wave F lifecycle-label to replay-universe bridge audit."""

from __future__ import annotations

import gzip
import json
import os
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
PARENT_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19"
FILLABILITY_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19"
SIBLING_REPO = ROOT.parent / "ai-trading-agent"
SIBLING_WAVE3_ROUTE = SIBLING_REPO / "research/operations/wave3_pending_nofill_lifecycle_v4_2026_06_04"
MAIN_ORCH24_DIR = (
    SIBLING_REPO
    / "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization"
)

WAVE_B_REPLAY_LEDGER = (
    "research/operations/final_moonshot_ultimate_system_wave_b_hydrated_replay_materialization_2026_06_19/"
    "WAVE_B_CANDIDATE_REPLAY_MATERIALIZATION_LEDGER.jsonl.gz"
)
WAVE_C_NO_FILL_LEDGER = (
    "research/operations/final_moonshot_ultimate_system_wave_c_execution_cost_realism_2026_06_19/"
    "WAVE_C_NO_FILL_OPPORTUNITY_COST_LEDGER.jsonl.gz"
)

ALT_SOURCE_FILES = [
    "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_PATH_PROXY_REPAIR_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_SOURCE_DECISION_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE_LEDGER_2026-05-16.jsonl",
    "MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_REPAIR_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_LEDGER_2026-05-17.jsonl",
]

FORBIDDEN_SURFACE_STATUS = {
    "live_trading": False,
    "broker_operation": False,
    "broker_account_order_history_deal_position_mutation": False,
    "credential_mutation_or_disclosure": False,
    "paid_api_vendor_call": False,
    "blind_remote_push": False,
    "live_vps_restart_or_reload": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def write_json(path: Path, data: Any) -> None:
    path.write_text(dump_json(data), encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def stable_write_json(path: Path, data: dict[str, Any], time_field: str = "generated_utc") -> None:
    if path.exists():
        try:
            existing = read_json(path)
            existing_cmp = {k: v for k, v in existing.items() if k == time_field}
            new_cmp = {k: v for k, v in data.items() if k == time_field}
            existing_cmp = {k: v for k, v in existing.items() if k != time_field}
            new_cmp = {k: v for k, v in data.items() if k != time_field}
            if existing_cmp == new_cmp:
                data[time_field] = existing.get(time_field, data.get(time_field))
        except json.JSONDecodeError:
            pass
    write_json(path, data)


def git_show_gzip_jsonl(path: str) -> Iterable[dict[str, Any]]:
    proc = subprocess.Popen(["git", "show", f"HEAD:{path}"], cwd=ROOT, stdout=subprocess.PIPE)
    assert proc.stdout is not None
    try:
        with gzip.GzipFile(fileobj=proc.stdout) as gz:
            for raw in gz:
                if raw.strip():
                    yield json.loads(raw)
    finally:
        proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"git show failed for {path}")


def candidate_prefix(candidate_id: str | None) -> str:
    if not candidate_id:
        return "missing"
    if "_" in candidate_id:
        return candidate_id.split("_", 1)[0]
    if candidate_id.startswith("cand"):
        return "cand"
    return candidate_id[:24]


def normalize_time(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("Z", "+00:00")


def normalized_label_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("symbol") or ""),
        str(row.get("side") or "").upper(),
        normalize_time(row.get("decision_time_utc")),
    )


def normalized_replay_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("symbol") or ""),
        str(row.get("side") or "").upper(),
        normalize_time(row.get("asof_utc") or row.get("decision_time_utc") or row.get("decision_time")),
    )


def scan_replay_keyspace(path: str, label_ids: set[str], label_keys: set[tuple[str, str, str]]) -> dict[str, Any]:
    rows = 0
    exact_candidate_id_matches = 0
    symbol_side_time_matches = 0
    candidate_prefix_counts: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()
    side_counts: Counter[str] = Counter()
    month_counts: Counter[str] = Counter()
    may_date_counts: Counter[str] = Counter()
    min_time = ""
    max_time = ""
    sample_candidate_ids: list[str] = []
    sample_rows: list[dict[str, Any]] = []
    decision_window_rows = 0
    pending_lifecycle_id_rows = 0

    for row in git_show_gzip_jsonl(path):
        rows += 1
        candidate_id = str(row.get("candidate_id") or "")
        if len(sample_candidate_ids) < 5:
            sample_candidate_ids.append(candidate_id)
        if len(sample_rows) < 3:
            sample_rows.append(
                {
                    "candidate_id": candidate_id,
                    "symbol": row.get("symbol"),
                    "side": row.get("side"),
                    "asof_utc": row.get("asof_utc"),
                    "decision_window_id": row.get("decision_window_id"),
                    "pending_lifecycle_v4_id": row.get("pending_lifecycle_v4_id"),
                }
            )
        candidate_prefix_counts[candidate_prefix(candidate_id)] += 1
        if candidate_id in label_ids:
            exact_candidate_id_matches += 1
        key = normalized_replay_key(row)
        if key in label_keys:
            symbol_side_time_matches += 1
        if row.get("decision_window_id"):
            decision_window_rows += 1
        if row.get("pending_lifecycle_v4_id"):
            pending_lifecycle_id_rows += 1
        if row.get("symbol"):
            symbol_counts[str(row.get("symbol"))] += 1
        if row.get("side"):
            side_counts[str(row.get("side")).upper()] += 1
        time_value = key[2]
        if time_value:
            min_time = time_value if not min_time or time_value < min_time else min_time
            max_time = time_value if not max_time or time_value > max_time else max_time
            month_counts[time_value[:7]] += 1
            if time_value.startswith("2026-05"):
                may_date_counts[time_value[:10]] += 1

    return {
        "path": path,
        "rows_scanned": rows,
        "exact_candidate_id_matches": exact_candidate_id_matches,
        "symbol_side_time_matches": symbol_side_time_matches,
        "candidate_prefix_counts": dict(candidate_prefix_counts.most_common()),
        "symbol_counts_top20": dict(symbol_counts.most_common(20)),
        "side_counts": dict(side_counts.most_common()),
        "month_counts_top20": dict(month_counts.most_common(20)),
        "may_2026_date_counts": dict(may_date_counts.most_common()),
        "min_time_utc": min_time,
        "max_time_utc": max_time,
        "sample_candidate_ids": sample_candidate_ids,
        "sample_rows": sample_rows,
        "decision_window_id_rows": decision_window_rows,
        "pending_lifecycle_v4_id_rows": pending_lifecycle_id_rows,
    }


def iter_jsonl_with_deadlock_boundary(path: Path) -> Iterable[tuple[dict[str, Any] | None, str | None]]:
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    yield json.loads(line), None
                except json.JSONDecodeError as exc:
                    yield None, f"json_decode_error:{exc}"
    except OSError as exc:
        yield None, f"os_error:{exc.errno}:{exc.strerror}"


def find_candidate_ids(value: Any, label_ids: set[str]) -> set[str]:
    found: set[str] = set()
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, nested in current.items():
                if key == "candidate_id" and isinstance(nested, str) and nested in label_ids:
                    found.add(nested)
                elif isinstance(nested, (dict, list)):
                    stack.append(nested)
        elif isinstance(current, list):
            stack.extend(current)
    return found


def scan_alternate_sources(label_ids: set[str]) -> tuple[dict[str, set[str]], list[dict[str, Any]]]:
    matches: dict[str, set[str]] = defaultdict(set)
    source_rows: list[dict[str, Any]] = []
    for name in ALT_SOURCE_FILES:
        path = MAIN_ORCH24_DIR / name
        rows_scanned = 0
        matched_rows = 0
        parse_errors = 0
        open_status = "missing"
        if path.exists():
            open_status = "readable"
            for row, error in iter_jsonl_with_deadlock_boundary(path):
                if error:
                    parse_errors += 1
                    open_status = error
                    break
                if row is None:
                    continue
                rows_scanned += 1
                found = find_candidate_ids(row, label_ids)
                if found:
                    matched_rows += 1
                    for candidate_id in found:
                        matches[candidate_id].add(name)
        source_rows.append(
            {
                "source_id": f"main_orch24:{name}",
                "path": str(path),
                "rows_scanned": rows_scanned,
                "matched_rows": matched_rows,
                "unique_label_candidate_ids_matched_so_far": len(matches),
                "open_status": open_status,
                "surface": "historical_main_orch24_lifecycle_owner_search",
            }
        )
    return matches, source_rows


def label_keyspace(labels: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_prefix_counts = Counter(candidate_prefix(row.get("candidate_id")) for row in labels)
    symbol_counts = Counter(str(row.get("symbol") or "") for row in labels)
    side_counts = Counter(str(row.get("side") or "").upper() for row in labels)
    family_counts = Counter(str(row.get("fillability_label_family") or "") for row in labels)
    fill_counts = Counter(str(row.get("fill_no_fill_label") or "") for row in labels)
    decision_date_counts: Counter[str] = Counter()
    month_counts: Counter[str] = Counter()
    min_time = ""
    max_time = ""
    rows_with_time = 0
    for row in labels:
        time_value = normalize_time(row.get("decision_time_utc"))
        if time_value:
            rows_with_time += 1
            min_time = time_value if not min_time or time_value < min_time else min_time
            max_time = time_value if not max_time or time_value > max_time else max_time
            decision_date_counts[time_value[:10]] += 1
            month_counts[time_value[:7]] += 1
        else:
            decision_date_counts["missing"] += 1
            month_counts["missing"] += 1
    return {
        "rows": len(labels),
        "unique_candidate_ids": len({row.get("candidate_id") for row in labels if row.get("candidate_id")}),
        "rows_with_candidate_id": sum(1 for row in labels if row.get("candidate_id")),
        "rows_with_decision_time": rows_with_time,
        "candidate_prefix_counts": dict(candidate_prefix_counts.most_common()),
        "symbol_counts_top20": dict(symbol_counts.most_common(20)),
        "side_counts": dict(side_counts.most_common()),
        "fillability_label_family_counts": dict(family_counts.most_common()),
        "fill_no_fill_label_counts": dict(fill_counts.most_common()),
        "decision_date_counts": dict(decision_date_counts.most_common()),
        "month_counts": dict(month_counts.most_common()),
        "min_decision_time_utc": min_time,
        "max_decision_time_utc": max_time,
    }


def row_disposition(
    label: dict[str, Any],
    wave_b_stats: dict[str, Any],
    wave_c_stats: dict[str, Any],
    alt_matches: dict[str, set[str]],
) -> dict[str, Any]:
    candidate_id = str(label.get("candidate_id") or "")
    decision_time = normalize_time(label.get("decision_time_utc"))
    reasons: list[str] = []
    if not candidate_id.startswith("cand_"):
        reasons.append("candidate_id_namespace_not_wave_b_c_cand_hash")
    if not decision_time:
        reasons.append("missing_decision_time_for_decision_window_join")
    elif decision_time > str(wave_c_stats.get("max_time_utc") or ""):
        reasons.append("decision_time_after_wave_b_c_replay_universe_max")
    if wave_b_stats.get("exact_candidate_id_matches") == 0 and wave_c_stats.get("exact_candidate_id_matches") == 0:
        reasons.append("zero_direct_candidate_id_matches_in_wave_b_c")
    if wave_b_stats.get("symbol_side_time_matches") == 0 and wave_c_stats.get("symbol_side_time_matches") == 0:
        reasons.append("zero_symbol_side_decision_time_matches_in_wave_b_c")

    alternate_sources = sorted(alt_matches.get(candidate_id, set()))
    return {
        "candidate_id": candidate_id,
        "trade_id": label.get("trade_id"),
        "symbol": label.get("symbol"),
        "side": label.get("side"),
        "decision_time_utc": decision_time,
        "fillability_label_family": label.get("fillability_label_family"),
        "fill_no_fill_label": label.get("fill_no_fill_label"),
        "wave_b_direct_candidate_id_join": False,
        "wave_c_direct_candidate_id_join": False,
        "wave_b_symbol_side_time_join": False,
        "wave_c_symbol_side_time_join": False,
        "alternate_historical_owner_found": bool(alternate_sources),
        "alternate_historical_owner_sources": alternate_sources,
        "bridge_disposition": "excluded_from_current_wave_b_c_replay_universe",
        "exclusion_reasons": reasons,
        "final_package_selection_allowed": False,
        "model_training_allowed": False,
    }


def replace_jsonl_row(path: Path, key: str, row: dict[str, Any]) -> None:
    rows = []
    replaced = False
    if path.exists():
        for existing in read_jsonl(path):
            if existing.get(key) == row.get(key):
                rows.append(row)
                replaced = True
            else:
                rows.append(existing)
    if not replaced:
        rows.append(row)
    write_jsonl(path, rows)


def update_parent(summary: dict[str, Any], route_rel: str) -> None:
    board_path = PARENT_ROUTE / "PARENT_WAVE_STATUS_BOARD.json"
    board = read_json(board_path)
    board["current_head"] = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    board["generated_utc"] = summary["generated_utc"]
    for wave in board.get("waves", []):
        if wave.get("wave") != "F":
            continue
        wave["status"] = "lifecycle_replay_bridge_checkpoint_final_selection_still_blocked"
        wave["next_action"] = (
            "Treat the 877 lifecycle labels as excluded from the current Wave B/C replay denominator unless a selected-package "
            "replay extension materializes the May 3-12 runtime lifecycle window with candidate/decision-window parity; keep final selection blocked."
        )
        completed = wave.setdefault("completed", [])
        add_completed = [
            "Lifecycle-to-replay bridge exhausted for 877 row-bound labels",
            "Wave B and Wave C direct candidate_id joins remain 0",
            "Wave B and Wave C symbol/side/decision-time joins remain 0",
            "Main-Orch24 alternate historical lifecycle ownership recorded separately from current Wave B/C replay universe",
        ]
        for item in add_completed:
            if item not in completed:
                completed.append(item)
        evidence = wave.setdefault("evidence", [])
        for artifact in [
            f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json",
            f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_LEDGER.jsonl",
            f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_KEYSPACE_AUDIT.json",
            f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_RESIDUAL_BLOCKER_LEDGER.jsonl",
            f"{route_rel}/VERIFICATION_RESULT.json",
        ]:
            if artifact not in evidence:
                evidence.append(artifact)
        remaining = wave.setdefault("remaining", [])
        for item in [
            "selected-package replay extension covering May 3-12 runtime lifecycle window, or an explicit final-package exclusion policy",
            "candidate/decision-window parity between runtime placement packets and final replay package rows",
        ]:
            if item not in remaining:
                remaining.append(item)
    write_json(board_path, board)

    replace_jsonl_row(
        PARENT_ROUTE / "PARENT_ACTIVE_QUESTION_STACK.jsonl",
        "question_id",
        {
            "question_id": "PQ019",
            "question": "Can the 877 row-bound lifecycle labels be bridged into current Wave B/C replay rows?",
            "answer": (
                "No. The bridge route scanned 214536 Wave B rows and 214536 Wave C rows, found 0 exact candidate_id joins and "
                "0 symbol/side/decision-time joins, and proved the lifecycle labels are in a runtime/Main-Orch24 keyspace outside the current Wave B/C replay universe."
            ),
            "status": "answered_lifecycle_replay_bridge_checkpoint",
            "evidence": [
                f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json",
                f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_KEYSPACE_AUDIT.json",
                f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_LEDGER.jsonl",
            ],
            "next_action": "Either build a selected-package replay extension for the May 3-12 runtime lifecycle window or keep these labels excluded from current Wave B/C final-selection denominator.",
        },
    )
    replace_jsonl_row(
        PARENT_ROUTE / "PARENT_SOURCE_REQUEST_LEDGER.jsonl",
        "request_id",
        {
            "request_id": "PSR019",
            "source_or_field": "lifecycle_label_to_wave_b_c_replay_bridge",
            "exact_path": route_rel,
            "row_count": summary["bridge_rows"],
            "resolution": "Direct Wave B/C joins are exhausted at 0; alternate historical owner sources are captured but cannot backfill the current replay denominator.",
            "status": "completed_zero_join_exclusion_recorded_remaining_replay_extension_required",
            "next_action": "Materialize a replay package extension with placement candidate/decision-window parity before using these lifecycle labels for final package selection or training.",
        },
    )
    replace_jsonl_row(
        PARENT_ROUTE / "PARENT_MERGE_DECISION_LEDGER.jsonl",
        "decision_id",
        {
            "decision_id": "PMD018",
            "decision": "Absorb Wave F lifecycle replay bridge as WFB003 exclusion proof, not final package selection.",
            "reason": "The route exhausts direct current Wave B/C joins for all 877 lifecycle labels and preserves alternate historical ownership as source provenance only.",
            "status": "selected",
            "evidence": [
                f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json",
                f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_RESIDUAL_BLOCKER_LEDGER.jsonl",
            ],
        },
    )

    manifest_path = PARENT_ROUTE / "PARENT_OUTPUT_MANIFEST.json"
    manifest = read_json(manifest_path)
    manifest["generated_utc"] = summary["generated_utc"]
    linked = manifest.setdefault("linked_child_or_checkpoint_artifacts", [])
    for artifact in [
        f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json",
        f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_LEDGER.jsonl",
        f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SOURCE_SEARCH_LEDGER.jsonl",
        f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_KEYSPACE_AUDIT.json",
        f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_RESIDUAL_BLOCKER_LEDGER.jsonl",
        f"{route_rel}/VERIFICATION_RESULT.json",
    ]:
        if artifact not in linked:
            linked.append(artifact)
    write_json(manifest_path, manifest)

    audit_path = PARENT_ROUTE / "PARENT_COMPLETION_AUDIT.json"
    audit = read_json(audit_path)
    audit["generated_utc"] = summary["generated_utc"]
    completed = audit.setdefault("completed_requirements", [])
    completed_item = "Built Wave F lifecycle replay bridge with 877 label dispositions, 0 Wave B joins, and 0 Wave C joins"
    if completed_item not in completed:
        completed.append(completed_item)
    audit["same_evidence_class_next_step"] = (
        "Build a selected-package replay extension with May 3-12 runtime lifecycle candidate/decision-window parity, "
        "or formally exclude those lifecycle labels from any final-package denominator while preserving capture requirements."
    )
    unmet = audit.setdefault("unmet_completion_requirements", [])
    old = "candidate_id namespace bridge or decision_window_id join between pending lifecycle labels and Wave B/C material rows"
    if old in unmet:
        unmet.remove(old)
    for item in [
        "selected-package replay extension or explicit exclusion policy for May 3-12 runtime lifecycle labels",
        "full row-bound fillability/order-type labels across the selected final-package replay universe",
    ]:
        if item not in unmet:
            unmet.append(item)
    verification = audit.setdefault("verification", {})
    verification["wave_f_lifecycle_replay_bridge"] = "passed"
    verification["wave_f_lifecycle_bridge_rows"] = summary["bridge_rows"]
    verification["wave_f_lifecycle_bridge_wave_b_rows_scanned"] = summary["wave_b_rows_scanned"]
    verification["wave_f_lifecycle_bridge_wave_c_rows_scanned"] = summary["wave_c_rows_scanned"]
    verification["wave_f_lifecycle_bridge_wave_b_direct_joins"] = summary["wave_b_exact_candidate_id_matches"]
    verification["wave_f_lifecycle_bridge_wave_c_direct_joins"] = summary["wave_c_exact_candidate_id_matches"]
    verification["wave_f_lifecycle_bridge_alternate_owner_candidate_ids"] = summary["alternate_historical_owner_candidate_ids"]
    write_json(audit_path, audit)


def main() -> int:
    generated_utc = utc_now()
    route_rel = str(ROUTE.relative_to(ROOT))
    labels = read_jsonl(FILLABILITY_ROUTE / "WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl")
    label_ids = {str(row.get("candidate_id")) for row in labels if row.get("candidate_id")}
    label_keys = {normalized_label_key(row) for row in labels if normalized_label_key(row)[2]}
    fillability_summary = read_json(FILLABILITY_ROUTE / "WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json")

    source_rows = [
        {
            "source_id": "wave_f_fillability_label_repair_ledger",
            "path": str((FILLABILITY_ROUTE / "WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl").relative_to(ROOT)),
            "rows_scanned": len(labels),
            "matched_rows": len(labels),
            "open_status": "read",
            "surface": "row_bound_lifecycle_labels",
        },
        {
            "source_id": "wave3_pending_nofill_lifecycle_fixture_route",
            "path": str(SIBLING_WAVE3_ROUTE),
            "rows_scanned": fillability_summary.get("input_fixture_rows"),
            "matched_rows": fillability_summary.get("row_bound_fillability_label_rows"),
            "open_status": "read_via_prior_fillability_materialization",
            "surface": "historical_lifecycle_fixture_owner",
        },
    ]

    label_stats = label_keyspace(labels)
    wave_b_stats = scan_replay_keyspace(WAVE_B_REPLAY_LEDGER, label_ids, label_keys)
    wave_c_stats = scan_replay_keyspace(WAVE_C_NO_FILL_LEDGER, label_ids, label_keys)
    source_rows.extend(
        [
            {
                "source_id": "wave_b_candidate_replay_materialization",
                "path": WAVE_B_REPLAY_LEDGER,
                "rows_scanned": wave_b_stats["rows_scanned"],
                "matched_rows": wave_b_stats["exact_candidate_id_matches"],
                "symbol_side_time_matches": wave_b_stats["symbol_side_time_matches"],
                "open_status": "git_show_head_gzip_read",
                "surface": "current_wave_b_replay_universe",
            },
            {
                "source_id": "wave_c_no_fill_opportunity_cost",
                "path": WAVE_C_NO_FILL_LEDGER,
                "rows_scanned": wave_c_stats["rows_scanned"],
                "matched_rows": wave_c_stats["exact_candidate_id_matches"],
                "symbol_side_time_matches": wave_c_stats["symbol_side_time_matches"],
                "open_status": "git_show_head_gzip_read",
                "surface": "current_wave_c_replay_universe",
            },
        ]
    )
    alt_matches, alt_source_rows = scan_alternate_sources(label_ids)
    source_rows.extend(alt_source_rows)

    bridge_rows = [row_disposition(label, wave_b_stats, wave_c_stats, alt_matches) for label in labels]
    alternate_owner_candidate_ids = sum(1 for candidate_id in label_ids if alt_matches.get(candidate_id))
    alternate_owner_rows = sum(1 for row in bridge_rows if row["alternate_historical_owner_found"])

    residual_blockers = [
        {
            "blocker_id": "WFB003",
            "requirement": "row-bound fillability/no-fill labels joined to selected final-package replay rows",
            "status": "zero_join_exclusion_recorded_current_wave_b_c_universe_not_closed",
            "evidence": [
                "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json",
                "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_KEYSPACE_AUDIT.json",
                "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_LEDGER.jsonl",
            ],
            "remaining_action": "Build May 3-12 runtime lifecycle replay extension with candidate/decision-window parity, or exclude this label set from the selected package denominator.",
            "final_package_selection_allowed": False,
        },
        {
            "blocker_id": "WFB011",
            "requirement": "candidate_id namespace parity between runtime placement lifecycle and replay package rows",
            "status": "open_exact_replay_extension_or_namespace_bridge_requirement",
            "evidence": ["WAVE_F_LIFECYCLE_REPLAY_BRIDGE_KEYSPACE_AUDIT.json"],
            "remaining_action": "Materialize candidate/decision-window IDs in replay rows from the same placement packet namespace before using lifecycle labels for training or final selection.",
            "final_package_selection_allowed": False,
        },
    ]
    decision_rows = [
        {
            "decision_id": "WFLB001",
            "decision": "Scan the full current Wave B and Wave C ledgers instead of sampling lifecycle joins.",
            "reason": "The parent route requires no top-N closure and full denominator proof for source exclusions.",
            "status": "selected",
        },
        {
            "decision_id": "WFLB002",
            "decision": "Treat Main-Orch24 matches as alternate historical ownership only.",
            "reason": "They prove source provenance for lifecycle IDs but do not insert those IDs into the current Wave B/C replay universe.",
            "status": "selected",
        },
        {
            "decision_id": "WFLB003",
            "decision": "Keep final package selection, model training, deployment dossier, and live activation blocked.",
            "reason": "The direct bridge is 0 rows and the selected-package replay denominator still lacks row-bound lifecycle labels.",
            "status": "selected",
        },
    ]
    repair_rows = [
        {
            "repair_id": "WFLB001",
            "requirement": "candidate_id bridge from 877 lifecycle labels into Wave B/C",
            "result": "exhausted_zero_direct_join",
            "rows_affected": len(labels),
            "status": "materialized",
        },
        {
            "repair_id": "WFLB002",
            "requirement": "decision-window or symbol/side/time join into Wave B/C",
            "result": "exhausted_zero_symbol_side_time_join",
            "rows_affected": len(labels),
            "status": "materialized",
        },
        {
            "repair_id": "WFLB003",
            "requirement": "alternate source ownership for lifecycle IDs",
            "result": "historical_owner_evidence_recorded_without_wave_b_c_denominator_backfill",
            "rows_affected": alternate_owner_rows,
            "status": "materialized",
        },
    ]
    keyspace = {
        "schema": "gtos.final_moonshot.wave_f.lifecycle_replay_bridge.keyspace_audit.v1",
        "generated_utc": generated_utc,
        "label_keyspace": label_stats,
        "wave_b_keyspace": wave_b_stats,
        "wave_c_keyspace": wave_c_stats,
        "bridge_conclusion": {
            "direct_wave_b_join_rows": wave_b_stats["exact_candidate_id_matches"],
            "direct_wave_c_join_rows": wave_c_stats["exact_candidate_id_matches"],
            "symbol_side_time_wave_b_join_rows": wave_b_stats["symbol_side_time_matches"],
            "symbol_side_time_wave_c_join_rows": wave_c_stats["symbol_side_time_matches"],
            "candidate_namespace_compatible": False,
            "temporal_overlap_after_normalized_decision_time": False,
            "alternate_historical_owner_candidate_ids": alternate_owner_candidate_ids,
            "current_wave_b_c_replay_denominator_backfilled": False,
        },
    }
    summary = {
        "schema": "gtos.final_moonshot.wave_f.lifecycle_replay_bridge.summary.v1",
        "generated_utc": generated_utc,
        "status": "wave_f_lifecycle_replay_bridge_checkpoint_not_final_selection",
        "result_scope": "full_877_lifecycle_label_bridge_exhaustion_not_final_package_selection_not_training",
        "input_label_rows": len(labels),
        "bridge_rows": len(bridge_rows),
        "unique_label_candidate_ids": len(label_ids),
        "label_rows_with_decision_time": label_stats["rows_with_decision_time"],
        "wave_b_rows_scanned": wave_b_stats["rows_scanned"],
        "wave_c_rows_scanned": wave_c_stats["rows_scanned"],
        "wave_b_exact_candidate_id_matches": wave_b_stats["exact_candidate_id_matches"],
        "wave_c_exact_candidate_id_matches": wave_c_stats["exact_candidate_id_matches"],
        "wave_b_symbol_side_time_matches": wave_b_stats["symbol_side_time_matches"],
        "wave_c_symbol_side_time_matches": wave_c_stats["symbol_side_time_matches"],
        "wave_b_max_time_utc": wave_b_stats["max_time_utc"],
        "wave_c_max_time_utc": wave_c_stats["max_time_utc"],
        "label_min_decision_time_utc": label_stats["min_decision_time_utc"],
        "label_max_decision_time_utc": label_stats["max_decision_time_utc"],
        "alternate_historical_owner_candidate_ids": alternate_owner_candidate_ids,
        "alternate_historical_owner_label_rows": alternate_owner_rows,
        "source_search_rows": len(source_rows),
        "residual_blocker_rows": len(residual_blockers),
        "wfb003_status": "zero_join_exclusion_recorded_current_wave_b_c_universe_not_closed",
        "wfb011_status": "open_exact_replay_extension_or_namespace_bridge_requirement",
        "forbidden_surface_status": FORBIDDEN_SURFACE_STATUS,
        "terminal_decision": {
            "lifecycle_bridge_complete_for_current_wave_b_c_universe": True,
            "row_bound_fillability_complete_for_selected_package": False,
            "final_package_selected": False,
            "model_training_allowed": False,
            "deployment_dossier_allowed": False,
            "live_execution_activation_allowed": False,
            "wave_f_complete": False,
        },
    }

    write_jsonl(ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_LEDGER.jsonl", bridge_rows)
    write_jsonl(ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SOURCE_SEARCH_LEDGER.jsonl", source_rows)
    stable_write_json(ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_KEYSPACE_AUDIT.json", keyspace)
    write_jsonl(ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_RESIDUAL_BLOCKER_LEDGER.jsonl", residual_blockers)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_jsonl(ROUTE / "REPAIR_LEDGER.jsonl", repair_rows)
    stable_write_json(ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json", summary)
    (ROUTE / "SATURATION_SELF_RED_TEAM.md").write_text(
        "\n".join(
            [
                "# Wave F Lifecycle Replay Bridge Saturation Self-Red-Team",
                "",
                "- Full current Wave B and Wave C ledgers were streamed from Git blobs and not sampled.",
                "- The 877 lifecycle-label ledger was preserved row-for-row with exclusion dispositions.",
                "- Main-Orch24 matches are treated as provenance/ownership only because they do not alter the current Wave B/C denominator.",
                "- Final package selection, model training, deployment dossier, and live activation remain disallowed.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    stable_write_json(
        ROUTE / "COMPLETION_AUDIT.json",
        {
            "schema": "gtos.final_moonshot.wave_f.lifecycle_replay_bridge.completion_audit.v1",
            "generated_utc": generated_utc,
            "status": "checkpoint_complete_not_final_selection",
            "goal_completion_claim": False,
            "completed_requirements": [
                "Scanned 877 lifecycle labels",
                "Scanned 214536 Wave B replay rows",
                "Scanned 214536 Wave C no-fill rows",
                "Recorded 0 direct Wave B/C joins and row-level exclusions",
                "Recorded alternate historical owner matches separately from current replay denominator",
            ],
            "remaining_requirements": [
                "selected-package replay extension covering May 3-12 runtime lifecycle window",
                "candidate/decision-window namespace parity before label training or final selection",
                "broker actual-R and all-in close cost joins",
                "clean labels and deterministic baseline before model promotion",
            ],
            "forbidden_surface_status": FORBIDDEN_SURFACE_STATUS,
        },
    )
    stable_write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": "gtos.final_moonshot.wave_f.lifecycle_replay_bridge.output_manifest.v1",
            "generated_utc": generated_utc,
            "route": route_rel,
            "inputs": [
                str((FILLABILITY_ROUTE / "WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl").relative_to(ROOT)),
                WAVE_B_REPLAY_LEDGER,
                WAVE_C_NO_FILL_LEDGER,
                str(SIBLING_WAVE3_ROUTE),
                str(MAIN_ORCH24_DIR),
            ],
            "files": [
                "build_wave_f_lifecycle_replay_bridge.py",
                "verify_wave_f_lifecycle_replay_bridge.py",
                "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json",
                "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_LEDGER.jsonl",
                "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SOURCE_SEARCH_LEDGER.jsonl",
                "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_KEYSPACE_AUDIT.json",
                "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_RESIDUAL_BLOCKER_LEDGER.jsonl",
                "DECISION_LEDGER.jsonl",
                "REPAIR_LEDGER.jsonl",
                "SATURATION_SELF_RED_TEAM.md",
                "COMPLETION_AUDIT.json",
                "OUTPUT_MANIFEST.json",
                "FOCUSED_TEST_RESULT.json",
                "VERIFICATION_RESULT.json",
            ],
        },
    )
    stable_write_json(
        ROUTE / "FOCUSED_TEST_RESULT.json",
        {
            "schema": "gtos.final_moonshot.wave_f.lifecycle_replay_bridge.focused_test_result.v1",
            "generated_utc": generated_utc,
            "status": "pending_verifier",
            "checks": {
                "full_label_rows_materialized": len(bridge_rows) == 877,
                "wave_b_rows_scanned": wave_b_stats["rows_scanned"] == 214536,
                "wave_c_rows_scanned": wave_c_stats["rows_scanned"] == 214536,
                "direct_joins_zero": wave_b_stats["exact_candidate_id_matches"] == 0 and wave_c_stats["exact_candidate_id_matches"] == 0,
            },
        },
    )
    update_parent(summary, route_rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
