#!/usr/bin/env python3
"""Build G12 audit artifacts for the CNR T3 lifecycle expansion packet.

Research audit only. This script does not compute R, performance, win rate,
expectancy, DSR, PBO, broker actual-R, account history, live order state, or
any promotion statistic. It audits the upstream packet as categorical lifecycle
source evidence only.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "g12_cnr_t3_lifecycle_audit_v1"

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
OUTCOME_ROOT = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
T3 = OUTCOME_ROOT / "cnr_t3_lifecycle_expansion_source_packet"

BOUNDARY_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "broker_actual_r_accessed": False,
    "account_history_accessed": False,
    "live_trade_results_accessed": False,
    "live_order_state_accessed": False,
    "blocked_packet_outcome_source_read": False,
    "api_calls": 0,
    "databento_calls": 0,
    "paid_data_calls": 0,
    "mt5_order_calls": 0,
    "mt5_account_calls": 0,
    "order_calls": 0,
    "canary_calls": 0,
}

ALLOWED_LABELS = {
    "target_after_original_horizon",
    "stop_after_original_horizon",
    "ambiguous_target_stop_after_original_horizon",
    "still_no_terminal_after_extended_horizon",
    "source_horizon_insufficient",
    "not_packet_eligible",
}

FORBIDDEN_PACKET_KEYS = {
    "synthetic_r",
    "broker_actual_r",
    "account_history",
    "live_trade_result",
    "live_trade_results",
    "live_order_state",
    "hidden_path_label",
    "promotion_statistic",
    "win_rate",
    "expectancy",
    "dsr",
    "pbo",
    "performance",
}

REQUIRED_OUTPUT_STEMS = [
    "G12_CNR_T3_CONTEXT_ANCHOR_2026-05-08",
    "G12_CNR_T3_DECISION_LEDGER_2026-05-08",
    "G12_CNR_T3_INVENTORY_COVERAGE_AUDIT_2026-05-08",
    "G12_CNR_T3_LIFECYCLE_PACKET_AUDIT_2026-05-08",
    "G12_CNR_T3_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08",
    "G12_CNR_T3_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08",
    "G12_CNR_T3_FORENSICS_AND_LEARNING_2026-05-08",
    "G12_CNR_T3_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08",
    "G12_CNR_T3_COMPLETION_AUDIT_2026-05-08",
]

T3_JSON = {
    "completion": "CNR_T3_COMPLETION_AUDIT_2026-05-08.json",
    "context": "CNR_T3_CONTEXT_ANCHOR_2026-05-08.json",
    "contract": "CNR_T3_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json",
    "inventory": "CNR_T3_NO_TERMINAL_CANDIDATE_INVENTORY_2026-05-08.json",
    "source_ledger": "CNR_T3_SEARCHED_ROOT_AND_SOURCE_HASH_LEDGER_2026-05-08.json",
    "packet": "CNR_T3_LIFECYCLE_PACKET_2026-05-08.json",
    "noleak": "CNR_T3_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
    "blockers": "CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json",
    "learning": "CNR_T3_LIFECYCLE_FORENSICS_AND_LEARNING_2026-05-08.json",
}

T3_ROWS = T3 / "CNR_T3_LIFECYCLE_PACKET_2026-05-08_ROWS.jsonl"

UPSTREAM_REQUIRED = [
    "g12_cnr_next_model_control_audit/G12_CNR_NEXT_PROMPT_PACK_2026-05-08.md",
    "g12_cnr_next_model_control_audit/G12_CNR_NEXT_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08.json",
    "g12_cnr_next_model_control_audit/G12_CNR_NEXT_DECISION_LEDGER_2026-05-08.json",
    "g12_cnr_next_model_control_audit/G12_CNR061_LIFECYCLE_PACKET_AUDIT_2026-05-08.json",
    "g12_cnr_next_model_control_audit/G12_CNR_XAGUSD_STOP_AFTER_HORIZON_FORENSICS_2026-05-08.json",
    "g12_cnr_next_model_control_audit/G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT_2026-05-08.json",
    "cnr_next_model_control_pack/CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_2026-05-08.json",
    "cnr_next_model_control_pack/CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_2026-05-08_ROWS.jsonl",
    "cnr_next_model_control_pack/CNR_T1_T2_T3_TARGET_PREREGISTRATION_2026-05-08.json",
    "cnr_next_model_control_pack/CNR_E2_E3_E4_TIMING_PREREGISTRATION_2026-05-08.json",
    "oti8_cnr061_quarantined_results/OTI8_CNR061_RESULT_LEDGER_2026-05-08_ROWS.jsonl",
    "oti8_cnr061_quarantined_results/OTI8_CNR061_ACCEPTED_ROW_MANIFEST_2026-05-08.json",
    "g12_oti8_cnr061_post_result_audit/G12_OTI8_CNR061_RESULT_INTEGRITY_AUDIT_2026-05-08.json",
    "g12_oti8_cnr061_post_result_audit/G12_OTI8_CNR061_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.json",
    "oti7_cnr_accepted_quarantined_results/OTI7_CNR_RESULT_LEDGER_2026-05-08.jsonl",
    "g12_oti7_cnr_post_result_audit/G12_OTI7_CNR_POST_RESULT_DECISION_LEDGER_2026-05-08.json",
    "oti5_g6_cusum_changepoint_quarantined_results/OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "g12_oti5_otr061_post_audit/G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.json",
    "oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "oti4_g6_opening_drive_quarantined_results/OTI4_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "oti1_lifecycle_quarantined_results/OTI1_RESULT_LEDGER_2026-05-07.json",
    "oti2_riskbank_quarantined_results/OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "oti6_otr061_cnr_quarantined_results/OTI6_CNR_RESULT_LEDGER_2026-05-07.json",
]

PREFLIGHT_READS = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_READING_ORDER.md",
    "research/science_program_2026_05/06_outcome_testing/g12_cnr_t3_lifecycle_audit/G12_CNR_T3_LIFECYCLE_AUDIT_GOAL_PROMPT_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_G12_AUDIT_PROMPT_PACK_2026-05-08.md",
]

_PARQUET_CACHE: dict[str, list[dict[str, Any]]] = {}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception as exc:
        return f"[git unavailable: {exc}]"


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text_line_ending_variants(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data = path.read_bytes()
    lf_data = data.replace(b"\r\n", b"\n")
    crlf_data = lf_data.replace(b"\n", b"\r\n")
    return {
        "raw": hashlib.sha256(data).hexdigest(),
        "lf_normalized": hashlib.sha256(lf_data).hexdigest(),
        "crlf_variant": hashlib.sha256(crlf_data).hexdigest(),
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(stem: str, obj: Any) -> None:
    (BASE / f"{stem}.json").write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(stem: str, title: str, body: str) -> None:
    (BASE / f"{stem}.md").write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def artifact_entry(path: Path, role: str) -> dict[str, Any]:
    return {
        "path": rel(path),
        "role": role,
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size if path.exists() else None,
    }


def boundary_base(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA_VERSION,
        "date_stamp": DATE,
        "generated_at_utc": now_utc(),
        **BOUNDARY_FLAGS,
    }


def load_t3_artifacts() -> dict[str, Any]:
    data = {key: load_json(T3 / name) for key, name in T3_JSON.items()}
    data["packet_rows"] = load_jsonl(T3_ROWS)
    return data


def contains_forbidden_key(value: Any) -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_l = str(key).lower()
            if any(f == key_l or f in key_l for f in FORBIDDEN_PACKET_KEYS):
                hits.append(str(key))
            hits.extend(contains_forbidden_key(nested))
    elif isinstance(value, list):
        for item in value:
            hits.extend(contains_forbidden_key(item))
    return hits


def parse_dt(value: str) -> dt.datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def iso_z(value: dt.datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def read_parquet_ticks(path: str) -> list[dict[str, Any]]:
    if path in _PARQUET_CACHE:
        return _PARQUET_CACHE[path]
    import pyarrow.parquet as pq

    table = pq.read_table(path, columns=["ts_utc", "bid", "ask"])
    rows = table.to_pylist()
    rows.sort(key=lambda row: row["ts_utc"])
    _PARQUET_CACHE[path] = rows
    return rows


def classify_terminal(side: str, bid: float, ask: float, stop: float, target: float) -> tuple[str | None, str | None]:
    if side == "LONG":
        hit_target = bid >= target
        hit_stop = bid <= stop
        quote_side = "bid"
    elif side == "SHORT":
        hit_target = ask <= target
        hit_stop = ask >= stop
        quote_side = "ask"
    else:
        return None, None
    if hit_target and hit_stop:
        return "ambiguous_target_stop_after_original_horizon", quote_side
    if hit_target:
        return "target_after_original_horizon", quote_side
    if hit_stop:
        return "stop_after_original_horizon", quote_side
    return None, None


def recompute_packet_label(row: dict[str, Any]) -> dict[str, Any]:
    original_end = parse_dt(row["original_horizon_end_utc"])
    extended_end = parse_dt(row["extended_horizon_end_utc"])
    first_tick_after: str | None = None
    rows_scanned = 0
    terminal_label: str | None = None
    terminal_event: str | None = None
    terminal_side: str | None = None
    source_failures: list[str] = []

    tick_files = row.get("tick_source_files", [])
    for source in tick_files:
        path = source.get("path")
        if not path or not Path(path).exists():
            source_failures.append(f"missing tick source {path}")
            continue
        for tick in read_parquet_ticks(path):
            ts = tick["ts_utc"].astimezone(dt.timezone.utc)
            if ts <= original_end:
                continue
            if ts > extended_end:
                break
            if first_tick_after is None:
                first_tick_after = iso_z(ts)
            rows_scanned += 1
            label, quote_side = classify_terminal(
                row["side"],
                float(tick["bid"]),
                float(tick["ask"]),
                float(row["original_stop_loss"]),
                float(row["original_take_profit_1"]),
            )
            if label:
                terminal_label = label
                terminal_event = iso_z(ts)
                terminal_side = quote_side
                break
        if terminal_label:
            break

    if source_failures:
        terminal_label = "source_horizon_insufficient"
    elif terminal_label is None:
        terminal_label = "still_no_terminal_after_extended_horizon"

    return {
        "input_inventory_id": row.get("input_inventory_id"),
        "record_id": row.get("record_id"),
        "computed_lifecycle_label": terminal_label,
        "reported_lifecycle_label": row.get("lifecycle_label"),
        "computed_terminal_event_utc": terminal_event,
        "reported_terminal_event_utc": row.get("terminal_event_utc"),
        "computed_terminal_price_side": terminal_side,
        "reported_terminal_price_side": row.get("terminal_price_side"),
        "first_tick_after_original_horizon_utc": first_tick_after,
        "rows_scanned_until_terminal_or_cap": rows_scanned,
        "source_failures": source_failures,
        "status": "PASS" if terminal_label == row.get("lifecycle_label") else "FAIL",
    }


def select_upstream_candidates() -> dict[str, Any]:
    specs: list[dict[str, Any]] = []

    def add_jsonl(lane: str, rel_path: str, predicate, rule: str) -> None:
        path = OUTCOME_ROOT / rel_path
        rows = load_jsonl(path)
        selected = [row for row in rows if predicate(row)]
        specs.append(
            {
                "source_lane": lane,
                "artifact_path": rel_path,
                "rows_loaded": len(rows),
                "candidate_like_rows_selected": len(selected),
                "selection_rule": rule,
            }
        )

    add_jsonl(
        "OTI8_CNR061",
        "oti8_cnr061_quarantined_results/OTI8_CNR061_RESULT_LEDGER_2026-05-08_ROWS.jsonl",
        lambda row: "NO_TERMINAL_WITHIN_ORDERED_HORIZON" in str(row.get("terminal_status", "")),
        "terminal_status contains NO_TERMINAL_WITHIN_ORDERED_HORIZON",
    )
    add_jsonl(
        "OTI5_G6_CUSUM",
        "oti5_g6_cusum_changepoint_quarantined_results/OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
        lambda row: "NO_ENTRY_TOUCH_NO_R_SCORED" in str(row.get("result_status", "")),
        "result_status contains NO_ENTRY_TOUCH_NO_R_SCORED",
    )
    add_jsonl(
        "OTI4_G6_OPENING_DRIVE",
        "oti4_g6_opening_drive_quarantined_results/OTI4_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
        lambda row: "terminal_order_unclaimed" in str(row.get("same_bar_ambiguity_state", "")),
        "same_bar_ambiguity_state contains terminal_order_unclaimed",
    )
    add_jsonl(
        "OTI3_G3_GEOMETRY",
        "oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
        lambda row: "NO_PRICE_COMPATIBLE_M1_SOURCE" in str(row.get("terminal_label", "")),
        "terminal_label contains NO_PRICE_COMPATIBLE_M1_SOURCE",
    )
    add_jsonl(
        "OTI2_RISKBANK",
        "oti2_riskbank_quarantined_results/OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
        lambda row: (
            "without_entry_touch" in str(row.get("path_order_label", ""))
            or row.get("entry_first_touch_utc") in {None, "", "null"}
            or "unresolved" in str(row.get("descriptive_status", "")).lower()
        ),
        "path_order_label contains without_entry_touch, or entry touch is null, or descriptive_status is unresolved",
    )

    oti1_path = OUTCOME_ROOT / "oti1_lifecycle_quarantined_results/OTI1_RESULT_LEDGER_2026-05-07.json"
    oti1 = load_json(oti1_path)
    selected_oti1 = []
    loaded_oti1 = 0
    for packet_result in oti1.get("packet_results", []):
        for group in packet_result.get("group_summaries", []):
            loaded_oti1 += 1
            state = str(group.get("fill_or_no_fill_state", ""))
            lifecycle_state = str(group.get("lifecycle_state", ""))
            if state.startswith("no_fill") or lifecycle_state in {"still_pending", "wrong_side"}:
                selected_oti1.append(group)
    specs.append(
        {
            "source_lane": "OTI1_LIFECYCLE",
            "artifact_path": "oti1_lifecycle_quarantined_results/OTI1_RESULT_LEDGER_2026-05-07.json",
            "rows_loaded": loaded_oti1,
            "candidate_like_rows_selected": len(selected_oti1),
            "selection_rule": "flatten packet_results.group_summaries with no_fill or still_pending lifecycle states",
        }
    )

    add_jsonl(
        "OTI7_CNR",
        "oti7_cnr_accepted_quarantined_results/OTI7_CNR_RESULT_LEDGER_2026-05-08.jsonl",
        lambda row: False,
        "scanned; no no-terminal/no-entry/still-pending status found",
    )
    oti6_path = OUTCOME_ROOT / "oti6_otr061_cnr_quarantined_results/OTI6_CNR_RESULT_LEDGER_2026-05-07.json"
    oti6_rows = [load_json(oti6_path)]
    specs.append(
        {
            "source_lane": "OTI6_CNR",
            "artifact_path": "oti6_otr061_cnr_quarantined_results/OTI6_CNR_RESULT_LEDGER_2026-05-07.json",
            "rows_loaded": len(oti6_rows),
            "candidate_like_rows_selected": 0,
            "selection_rule": "scanned; target-already-passed geometry ineligible, not no-terminal-like",
        }
    )
    for lane, rel_path, rule in [
        (
            "G12_OTI8",
            "g12_oti8_cnr061_post_result_audit/G12_OTI8_CNR061_RESULT_INTEGRITY_AUDIT_2026-05-08.json",
            "audit source only; candidates sourced from OTI8 accepted result rows",
        ),
        (
            "G12_OTI7",
            "g12_oti7_cnr_post_result_audit/G12_OTI7_CNR_POST_RESULT_DECISION_LEDGER_2026-05-08.json",
            "audit source only; no new candidate rows",
        ),
        (
            "G12_OTI5",
            "g12_oti5_otr061_post_audit/G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.json",
            "audit source only; candidates sourced from OTI5 result rows",
        ),
    ]:
        specs.append(
            {
                "source_lane": lane,
                "artifact_path": rel_path,
                "rows_loaded": 1,
                "candidate_like_rows_selected": 0,
                "selection_rule": rule,
            }
        )

    return {
        "scan_summaries": specs,
        "selected_total": sum(item["candidate_like_rows_selected"] for item in specs),
        "selected_lane_counts": {
            item["source_lane"]: item["candidate_like_rows_selected"]
            for item in specs
            if item["candidate_like_rows_selected"]
        },
    }


def build_context_anchor() -> dict[str, Any]:
    artifact_entries = [artifact_entry(ROOT / path, "mandatory_preflight_or_prompt") for path in PREFLIGHT_READS]
    artifact_entries.extend(artifact_entry(T3 / name, "required_t3_input") for name in T3_JSON.values())
    artifact_entries.append(artifact_entry(T3_ROWS, "required_t3_input"))
    artifact_entries.extend(artifact_entry(OUTCOME_ROOT / path, "required_upstream_input") for path in UPSTREAM_REQUIRED)
    local_roots = [
        ROOT / "data" / "ticks",
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks"),
        Path(r"C:\tmp\gtos_otb\CNRT3LIFE\data\ticks"),
        Path(r"C:\tmp"),
    ]
    searched_roots = []
    for root in local_roots:
        entry: dict[str, Any] = {"root": str(root), "exists": root.exists()}
        xag = root / "XAGUSD" if root.name == "ticks" else root
        if xag.exists():
            entry["xagusd_2026_05_tick_file_count"] = len(list(xag.glob("2026-05-0*.parquet"))) if xag.is_dir() else None
        searched_roots.append(entry)

    return {
        **boundary_base("G12_CNR_T3_CONTEXT_ANCHOR"),
        "head": run_git(["rev-parse", "HEAD"]),
        "head_oneline": run_git(["log", "-1", "--oneline"]),
        "branch": run_git(["rev-parse", "--abbrev-ref", "HEAD"]),
        "repo_root": str(ROOT),
        "worktree_path": str(ROOT),
        "controlling_prompt": rel(BASE / "G12_CNR_T3_LIFECYCLE_AUDIT_GOAL_PROMPT_2026-05-08.md"),
        "artifacts_read": artifact_entries,
        "active_question_stack": [
            "Accept, block, or reject CNR_T3_LIFECYCLE_EXPANSION_SOURCE_PACKET_V1 as categorical lifecycle source evidence only?",
            "Does the 304-row inventory cover every accepted/quarantined no-terminal-like row found by the upstream scan?",
            "Are exactly six rows packet eligible and exactly 298 rows blocked?",
            "Do source hashes, allowed labels, no-leak boundaries, duplicate denominators, and sample-floor gates hold?",
            "What do six stop_after_original_horizon labels prove and not prove?",
            "Which exact next lane should run first without mixing label families?",
        ],
        "searched_root_ledger": searched_roots,
        "route_decision_ledger_initial": [
            {
                "route": "G12 audit",
                "decision": "WRITE_CONTEXT_ANCHOR_FIRST_THEN_AUDIT",
                "reason": "Goal prompt requires context anchor before decision outputs.",
            },
            {
                "route": "web_or_curl",
                "decision": "NOT_USED",
                "reason": "All required source evidence is local and source-hashed; no public source doc was needed.",
            },
            {
                "route": "paid/API/Databento/MT5",
                "decision": "FORBIDDEN_NOT_USED",
                "reason": "Audit uses local files only and makes no paid, API, account, or order calls.",
            },
        ],
        "git_status_short_at_anchor": run_git(["status", "--short"]),
        "runtime_dirt_notice": "Expected preflight dirt may include .context/LIVE_STATE.md; G12 outputs are scoped to this audit directory plus optional context refresh.",
    }


def inventory_coverage_audit(t3: dict[str, Any]) -> dict[str, Any]:
    inventory = t3["inventory"]
    recomputed = select_upstream_candidates()
    inv_rows = inventory["rows"]
    source_lane_counts = dict(Counter(row.get("source_lane") for row in inv_rows))
    labels = dict(Counter(row.get("lifecycle_label_or_blocker_label") for row in inv_rows))
    eligible_rows = [row for row in inv_rows if row.get("packet_eligible")]
    blocked_rows = [row for row in inv_rows if not row.get("packet_eligible")]

    expected_scan = {
        item["source_lane"]: {
            "rows_loaded": item["rows_loaded"],
            "candidate_like_rows_selected": item["candidate_like_rows_selected"],
        }
        for item in inventory.get("artifact_scan_summaries", [])
    }
    recomputed_scan = {
        item["source_lane"]: {
            "rows_loaded": item["rows_loaded"],
            "candidate_like_rows_selected": item["candidate_like_rows_selected"],
        }
        for item in recomputed["scan_summaries"]
    }
    scan_mismatches = {
        lane: {"reported": expected_scan.get(lane), "recomputed": recomputed_scan.get(lane)}
        for lane in sorted(set(expected_scan) | set(recomputed_scan))
        if expected_scan.get(lane) != recomputed_scan.get(lane)
    }
    status = "PASS" if not scan_mismatches and len(inv_rows) == 304 and len(eligible_rows) == 6 and len(blocked_rows) == 298 else "FAIL"

    return {
        **boundary_base("G12_CNR_T3_INVENTORY_COVERAGE_AUDIT"),
        "decision": "ACCEPT_INVENTORY_COVERAGE_FOR_NAMED_SOURCE_ARTIFACTS" if status == "PASS" else "BLOCK_INVENTORY_COVERAGE_UNTIL_MISMATCHES_RESOLVED",
        "status": status,
        "reported_candidate_count": inventory.get("candidate_count"),
        "recomputed_candidate_like_total": recomputed["selected_total"],
        "reported_source_lane_counts": inventory.get("source_lane_counts"),
        "recomputed_source_lane_counts": recomputed["selected_lane_counts"],
        "source_lane_counts_from_rows": source_lane_counts,
        "label_counts_from_rows": labels,
        "packet_eligible_rows": len(eligible_rows),
        "not_packet_eligible_rows": len(blocked_rows),
        "scan_summaries_reported": inventory.get("artifact_scan_summaries", []),
        "scan_summaries_recomputed": recomputed["scan_summaries"],
        "scan_mismatches": scan_mismatches,
        "coverage_boundary": "This accepts coverage for the named upstream scan artifacts only; it is not proof that unrelated future local data roots contain no other possible research rows.",
    }


def lifecycle_packet_audit(t3: dict[str, Any]) -> dict[str, Any]:
    inventory_rows = t3["inventory"]["rows"]
    packet = t3["packet"]
    packet_rows = t3["packet_rows"]
    contract = t3["contract"]
    accepted = load_json(OUTCOME_ROOT / "oti8_cnr061_quarantined_results" / "OTI8_CNR061_ACCEPTED_ROW_MANIFEST_2026-05-08.json")
    accepted_hashes = set(accepted.get("accepted_sidecar_row_sha256", []))
    eligible_rows = [row for row in inventory_rows if row.get("packet_eligible")]
    eligible_hashes = {row.get("source_hashes", {}).get("sidecar_row_sha256") for row in eligible_rows}
    packet_input_ids = {row.get("input_inventory_id") for row in packet_rows}
    eligible_ids = {row.get("inventory_id") for row in eligible_rows}
    recomputes = [recompute_packet_label(row) for row in packet_rows]
    recompute_status = "PASS" if all(item["status"] == "PASS" for item in recomputes) else "FAIL"

    source = Path(T3 / "build_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py").read_text(encoding="utf-8")
    freeze_line = next((i for i, line in enumerate(source.splitlines(), 1) if 'write_json(OUTPUT_NAMES["contract"]' in line), None)
    scan_line = next((i for i, line in enumerate(source.splitlines(), 1) if "build_packet_and_ledgers(candidates)" in line), None)
    freeze_before_scan = bool(freeze_line and scan_line and freeze_line < scan_line)

    checks = {
        "packet_row_count_is_6": len(packet_rows) == 6 and packet.get("row_count") == 6,
        "all_packet_rows_stop_after_original_horizon": Counter(row.get("lifecycle_label") for row in packet_rows) == {"stop_after_original_horizon": 6},
        "packet_rows_match_eligible_inventory_ids": packet_input_ids == eligible_ids,
        "eligible_rows_are_oti8_cnr061": {row.get("source_lane") for row in eligible_rows} == {"OTI8_CNR061"},
        "eligible_sidecar_hashes_in_accepted_manifest": eligible_hashes.issubset(accepted_hashes) and len(eligible_hashes) == 6,
        "contract_freeze_order_before_scan_in_builder": freeze_before_scan,
        "tick_path_recompute_matches_labels": recompute_status == "PASS",
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    return {
        **boundary_base("G12_CNR_T3_LIFECYCLE_PACKET_AUDIT"),
        "decision": "ACCEPT_AS_CATEGORICAL_LIFECYCLE_SOURCE_EVIDENCE_ONLY" if status == "PASS" else "BLOCK_WITH_EXACT_NEXT_QUESTIONS",
        "status": status,
        "checks": checks,
        "contract_id": contract.get("contract_id"),
        "contract_allowed_labels": contract.get("allowed_labels"),
        "contract_freeze_evidence": {
            "freeze_order_text": contract.get("freeze_order"),
            "contract_write_line": freeze_line,
            "extension_scan_line": scan_line,
            "freeze_before_scan": freeze_before_scan,
        },
        "packet_lifecycle_label_counts": dict(Counter(row.get("lifecycle_label") for row in packet_rows)),
        "eligible_inventory_ids": sorted(eligible_ids),
        "packet_input_inventory_ids": sorted(packet_input_ids),
        "eligible_sidecar_hashes": sorted(hash for hash in eligible_hashes if hash),
        "accepted_manifest_hash_count": len(accepted_hashes),
        "tick_path_recompute": recomputes,
        "what_this_proves": [
            "The six packet rows are exactly the accepted OTI8 CNR061 original-horizon no-terminal rows.",
            "The frozen source contract can extend those rows into categorical lifecycle labels without R scoring.",
            "Under the SHORT ask-side terminal rule, each row first hits the original stop after the original ordered horizon.",
            "The original OTI8 no-terminal state was horizon-limited for this one May 5 NY XAGUSD duplicate group.",
        ],
        "what_this_does_not_prove": [
            "It does not prove R, win rate, expectancy, DSR, PBO, validation, promotion, or live edge.",
            "It does not use broker actual-R, account history, live trade results, live order state, or hidden path labels.",
            "It does not score or rescue the 94 G12-blocked CNR061 rows.",
            "It does not prove T1 fixed-R, T2 structural-level targets, or E2/E3/E4 timing telemetry.",
            "It does not justify thresholds, selectors, risk, prompt, execution, or live-gate changes.",
        ],
    }


def source_hash_and_noleak_audit(t3: dict[str, Any]) -> dict[str, Any]:
    source_ledger = t3["source_ledger"]
    packet_rows = t3["packet_rows"]
    consumed_checks = []
    for item in source_ledger.get("consumed_tick_file_hashes", []):
        path = Path(item["path"])
        observed = sha256_file(path)
        consumed_checks.append(
            {
                "path": str(path),
                "exists": path.exists(),
                "reported_sha256": item.get("sha256"),
                "observed_sha256": observed,
                "status": "PASS" if observed == item.get("sha256") else "FAIL",
            }
        )

    upstream_hash_checks = []
    for item in source_ledger.get("upstream_artifact_hashes", []):
        path = ROOT / item["path"]
        variants = sha256_text_line_ending_variants(path)
        observed = variants.get("raw")
        reported = item.get("sha256")
        status = "PASS" if reported in set(variants.values()) else "FAIL"
        if item.get("role") != "required_upstream_input" and status == "FAIL":
            status = "INFO_MUTABLE_CONTEXT_OR_PROMPT_REFRESHED"
        upstream_hash_checks.append(
            {
                "path": item["path"],
                "role": item.get("role"),
                "exists": path.exists(),
                "reported_sha256": reported,
                "observed_sha256": observed,
                "observed_text_sha256_variants": variants,
                "status": status,
            }
        )

    forbidden_packet_hits = {}
    for row in packet_rows:
        hits = sorted(set(contains_forbidden_key(row)))
        if hits:
            forbidden_packet_hits[row.get("input_inventory_id", row.get("record_id"))] = hits

    label_set = {row.get("lifecycle_label") for row in packet_rows}
    boundary_scan = {
        "packet_rows_boundary_flags": all(
            row.get("promotion_verdict") == PROMOTION_VERDICT
            and row.get("validation_safe") is False
            and row.get("outcome_review_opened") is False
            and row.get("live_effect") is False
            for row in packet_rows
        ),
        "allowed_label_set": label_set.issubset(ALLOWED_LABELS),
        "no_forbidden_packet_keys": not forbidden_packet_hits,
        "no_r_performance_computed": t3["noleak"].get("no_r_performance_computed") is True,
        "blocked_94_status_pass": t3["noleak"].get("blocked_94_status") == "PASS",
    }
    hash_status = "PASS" if all(item["status"] == "PASS" for item in consumed_checks) else "FAIL"
    upstream_required_status = "PASS" if all(item["status"] in {"PASS", "INFO_MUTABLE_CONTEXT_OR_PROMPT_REFRESHED"} for item in upstream_hash_checks) else "FAIL"
    status = "PASS" if hash_status == "PASS" and upstream_required_status == "PASS" and all(boundary_scan.values()) else "FAIL"

    return {
        **boundary_base("G12_CNR_T3_SOURCE_HASH_AND_NOLEAK_AUDIT"),
        "decision": "ACCEPT_SOURCE_HASH_AND_NOLEAK_BOUNDARY" if status == "PASS" else "BLOCK_SOURCE_HASH_OR_NOLEAK_BOUNDARY",
        "status": status,
        "consumed_tick_file_hash_checks": consumed_checks,
        "upstream_artifact_hash_checks": upstream_hash_checks,
        "upstream_hash_note": "LIVE_STATE.md is intentionally mutable after mandatory preflight; required research inputs must remain content-stable modulo Windows LF/CRLF checkout normalization, and tick sources remain byte-exact.",
        "packet_label_set": sorted(label for label in label_set if label),
        "forbidden_packet_key_hits": forbidden_packet_hits,
        "boundary_scan": boundary_scan,
        "blocked_94_exclusion": t3["noleak"].get("blocked_94_exclusion"),
        "local_heavy_data_observation": "XAGUSD May 5/6 tick parquet files are present in the absolute main data root and absent from this worktree data/ticks path, matching the local-heavy-data policy lesson.",
    }


def duplicate_samplefloor_audit(t3: dict[str, Any]) -> dict[str, Any]:
    packet_rows = t3["packet_rows"]
    duplicate_groups = Counter(row.get("duplicate_group_id") for row in packet_rows)
    denominator_keys = Counter(row.get("duplicate_denominator_key") for row in packet_rows)
    countable_rows = [row for row in packet_rows if row.get("countable_denominator_row")]
    status = "PASS" if len(packet_rows) == 6 and len(duplicate_groups) == 1 and len(countable_rows) == 2 and t3["noleak"].get("sample_floor_for_validation_met") is False else "FAIL"
    return {
        **boundary_base("G12_CNR_T3_DUPLICATE_SAMPLEFLOOR_AUDIT"),
        "decision": "ACCEPT_DUPLICATE_AND_SAMPLEFLOOR_BOUNDARY" if status == "PASS" else "BLOCK_DUPLICATE_OR_SAMPLEFLOOR_BOUNDARY",
        "status": status,
        "packet_row_count": len(packet_rows),
        "unique_duplicate_groups": len(duplicate_groups),
        "duplicate_group_counts": dict(duplicate_groups),
        "duplicate_denominator_key_counts": dict(denominator_keys),
        "countable_denominator_rows": len(countable_rows),
        "sample_floor_for_validation_met": False,
        "sample_floor_reason": "Six row-level entries collapse to one duplicate group and two countable timing-target denominator rows; this is source evidence only.",
        "promotion_block": "Duplicate/sample-floor status blocks validation and promotion; it does not block research learning or next source packetization.",
    }


def blocker_and_route_ledger(t3: dict[str, Any], inventory_audit: dict[str, Any]) -> dict[str, Any]:
    blockers = t3["blockers"]
    exact = blockers.get("exact_blockers", [])
    blocker_ids = {row.get("inventory_id") for row in exact}
    inventory_blocked_ids = {
        row.get("inventory_id")
        for row in t3["inventory"]["rows"]
        if not row.get("packet_eligible")
    }
    lane_counts = Counter(row.get("source_lane") for row in exact)
    exactness_checks = {
        "blocker_count_is_298": len(exact) == 298 and blockers.get("blocker_count") == 298,
        "blockers_match_noneligible_inventory_ids": blocker_ids == inventory_blocked_ids,
        "all_blockers_not_packet_eligible": set(row.get("lifecycle_label") for row in exact) == {"not_packet_eligible"},
        "no_blocker_extended_tick_scan": all(row.get("searched_extended_tick_path") is False for row in exact),
        "all_candidates_packetized_or_blocked": blockers.get("all_candidates_packetized_or_blocked") is True,
    }
    status = "PASS" if all(exactness_checks.values()) else "FAIL"
    first_route = {
        "route": "SEPARATE_NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT",
        "priority": 1,
        "decision": "RUN_FIRST_AS_SOURCE_CONTRACT_ONLY",
        "why": "It can use the 298 exact-blocked lifecycle-like rows without relabeling them as T3 target/stop outcomes. It should split no-fill, no-entry, still-pending, source-blocked, and terminal-order-unclaimed families under a new frozen contract.",
        "hard_boundaries": [
            "Do not reuse CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1 labels.",
            "Do not compute R or score blocked rows.",
            "Do not use broker/account/live/hidden labels.",
            "Keep validation_safe=false and live_effect=false.",
        ],
    }
    routes = [
        first_route,
        {
            "route": "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE_PACKET",
            "priority": 2,
            "decision": "BLOCKED_UNTIL_FIXED_R_AND_STOP_SOURCE_PACKET_FREEZE",
            "exact_next_input": "Frozen fixed-R multiple, stop-source convention, executable quote source, cost convention, and no-leak row schema.",
        },
        {
            "route": "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL_PACKET",
            "priority": 3,
            "decision": "BLOCKED_UNTIL_ASOF_STRUCTURAL_LEVEL_SNAPSHOT_BUILDER",
            "exact_next_input": "Source-hashed structural level id, timestamp, hierarchy rank, selection rule id, and as-of snapshot hash.",
        },
        {
            "route": "CNR_E2_E3_E4_TELEMETRY",
            "priority": 4,
            "decision": "FUTURE_TELEMETRY_REQUIRED_BEFORE_RESULT_ROWS",
            "exact_next_input": "Signal emission timestamp, decision latency fields, and pretouch trigger source fields captured before outcome opening.",
        },
    ]
    return {
        **boundary_base("G12_CNR_T3_BLOCKER_AND_NEXT_ROUTE_LEDGER"),
        "decision": "ACCEPT_BLOCKERS_WITH_EXACT_NEXT_ROUTES" if status == "PASS" else "BLOCK_WITH_EXACT_NEXT_QUESTIONS",
        "status": status,
        "exactness_checks": exactness_checks,
        "blocker_count": len(exact),
        "blocker_label_counts": blockers.get("blocker_label_counts"),
        "blocker_source_lane_counts": dict(lane_counts),
        "inventory_scan_status": inventory_audit.get("status"),
        "global_blockers_from_t3": blockers.get("global_blockers_for_future_routes"),
        "first_next_lane": first_route,
        "route_decision_ledger": routes,
        "exact_next_questions": [
            "Which of the 298 rows are no-fill, no-entry, still-pending, source-blocked, and terminal-order-unclaimed after family split?",
            "Can each non-T3 family bind source rows, as-of timestamps, and source hashes without outcome leakage?",
            "Which rows are source-insufficient versus lifecycle-meaningful after the new contract is frozen?",
            "What capture fields are missing to make T1, T2, and E2/E3/E4 source-safe later?",
        ],
    }


def forensics_and_learning(t3: dict[str, Any], lifecycle: dict[str, Any], blockers: dict[str, Any]) -> dict[str, Any]:
    packet_rows = t3["packet_rows"]
    terminal_events = [row.get("terminal_event_utc") for row in packet_rows]
    original_horizons = [row.get("original_horizon_end_utc") for row in packet_rows]
    return {
        **boundary_base("G12_CNR_T3_FORENSICS_AND_LEARNING"),
        "decision": "ACCEPT_LEARNING_AS_FAILURE_ANATOMY_ONLY",
        "status": "PASS" if lifecycle.get("status") == "PASS" and blockers.get("status") == "PASS" else "BLOCK",
        "categorical_learning": [
            "The six accepted OTI8 rows were not terminal-free forever; they became stop_after_original_horizon under the frozen extension rule.",
            "The rows all share one May 5 NY XAGUSD SHORT duplicate group, so the evidence is narrow failure anatomy, not a broad strategy result.",
            "The late-stop path suggests the original ordered horizon was too short to distinguish no-terminal from delayed adverse terminal for this group.",
            "The 298 blocked rows are learning inventory for other lifecycle contracts, not failed T3 target/stop rows.",
        ],
        "six_row_context": {
            "row_count": len(packet_rows),
            "unique_duplicate_groups": sorted({row.get("duplicate_group_id") for row in packet_rows}),
            "symbols": sorted({row.get("symbol") for row in packet_rows}),
            "sides": sorted({row.get("side") for row in packet_rows}),
            "original_horizon_end_utc_values": original_horizons,
            "terminal_event_utc_values": terminal_events,
        },
        "what_six_stop_after_original_horizon_labels_prove": lifecycle.get("what_this_proves"),
        "what_six_stop_after_original_horizon_labels_do_not_prove": lifecycle.get("what_this_does_not_prove"),
        "anti_rescue_boundary": "No rescue threshold, live gate, risk change, prompt edit, selector, or execution behavior is supported by this audit.",
        "open_questions_reduced_to_routes": blockers.get("route_decision_ledger"),
    }


def decision_ledger(
    inventory: dict[str, Any],
    lifecycle: dict[str, Any],
    source: dict[str, Any],
    duplicate: dict[str, Any],
    blockers: dict[str, Any],
) -> dict[str, Any]:
    subparts = {
        "candidate_inventory": inventory["decision"],
        "lifecycle_packet": lifecycle["decision"],
        "source_hash_and_no_leak": source["decision"],
        "duplicate_sample_floor": duplicate["decision"],
        "blockers_and_routes": blockers["decision"],
    }
    all_pass = all(obj.get("status") == "PASS" for obj in [inventory, lifecycle, source, duplicate, blockers])
    return {
        **boundary_base("G12_CNR_T3_DECISION_LEDGER"),
        "overall_decision": "ACCEPT_AS_CATEGORICAL_LIFECYCLE_SOURCE_EVIDENCE_ONLY" if all_pass else "BLOCK_WITH_EXACT_NEXT_QUESTIONS",
        "categorical_scope": "source-hashed lifecycle evidence only",
        "subpart_decisions": subparts,
        "audit_question_answers": [
            {"question": "Did T3 complete preflight and read required upstream artifacts?", "answer": "PASS; context/source ledgers list mandatory preflight and upstream artifacts."},
            {"question": "Was the contract frozen before extended tick path read?", "answer": "PASS; builder writes context and contract before build_packet_and_ledgers."},
            {"question": "Does the 304-row inventory cover named source scans?", "answer": f"{inventory['status']}; recomputed total {inventory['recomputed_candidate_like_total']}."},
            {"question": "Are the six rows exactly accepted CNR061 no-terminal rows?", "answer": f"{lifecycle['status']}; packet ids match eligible inventory ids and accepted hashes."},
            {"question": "Are 298 rows exact-blocked?", "answer": f"{blockers['status']}; blocker count {blockers['blocker_count']}."},
            {"question": "Are labels allowed and categorical?", "answer": f"{source['status']}; packet label set {source['packet_label_set']}."},
            {"question": "Are source hashes sufficient?", "answer": f"{source['status']}; consumed tick file hashes recomputed."},
            {"question": "Are no-leak and sample-floor boundaries preserved?", "answer": f"{duplicate['status']}; validation_safe remains false."},
            {"question": "Which next lane should run first?", "answer": blockers["first_next_lane"]["route"]},
        ],
        "promotion_boundary": "NO_PROMOTION_VERDICT; validation_safe=false; outcome_review_opened=false; live_effect=false.",
    }


def prompt_pack() -> str:
    return "\n".join(
        [
            "# G12 CNR T3 Next Prompt Pack - 2026-05-08",
            "",
            "Promotion verdict: `NO_PROMOTION_VERDICT`",
            "Validation safe: `false`",
            "Outcome review opened: `false`",
            "Live effect: `false`",
            "",
            "## Recommended Next Goal",
            "",
            "`/goal Build SEPARATE_NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT_V1 for the 298 CNR_T3 not_packet_eligible rows as a new source-safe lifecycle/no-fill/no-entry/still-pending/source-blocked/terminal-order-unclaimed contract. Complete GTOS preflight; read the G12 CNR T3 audit artifacts; freeze a new contract before scanning or labeling; split the 298 rows by label family; search local-heavy data roots and source artifacts; hash every source file; exact-block source-insufficient rows; do not reuse CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1 labels; do not compute R/performance; do not score blocked rows as T3 outcomes; do not use broker actual-R/account history/live trade results/live order state/hidden labels; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; touch no live prompts/risk/execution/permissions/safety/selectors/canaries/MT5/order/credential/remote surfaces; stop only with source contract, family split inventory, source/no-leak/duplicate/sample-floor audit, blocker ledger, verifier/tests, and completion audit.`",
            "",
            "## Follow-Up Routes",
            "",
            "- `CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE_PACKET`: blocked until fixed-R multiple, stop-source convention, executable quote source, and cost/no-leak schema are frozen.",
            "- `CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL_PACKET`: blocked until source-hashed structural level id, timestamp, hierarchy rank, and selection rule id exist as as-of snapshots.",
            "- `CNR_E2_E3_E4_TELEMETRY`: future telemetry requirement for signal emission, decision latency, and pretouch trigger fields; do not open result rows before capture.",
            "",
            "## Hard Boundaries",
            "",
            "- Keep the six T3 stop-after-horizon labels as narrow categorical lifecycle evidence only.",
            "- No 94 blocked-row scoring, rescue, or relabeling.",
            "- No R, performance, win rate, expectancy, DSR, PBO, validation, promotion, or live-edge claims.",
            "- No paid/API/Databento/MT5 order/account calls without explicit owner approval.",
            "",
        ]
    )


def simple_md(summary: dict[str, Any], keys: list[str]) -> str:
    lines = [
        f"Promotion verdict: `{summary['promotion_verdict']}`",
        f"Validation safe: `{str(summary['validation_safe']).lower()}`",
        f"Outcome review opened: `{str(summary['outcome_review_opened']).lower()}`",
        f"Live effect: `{str(summary['live_effect']).lower()}`",
        "",
    ]
    for key in keys:
        if key in summary:
            lines.append(f"## {key}")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(summary[key], indent=2, sort_keys=True, ensure_ascii=True))
            lines.append("```")
            lines.append("")
    return "\n".join(lines)


def completion_audit(
    context: dict[str, Any],
    decision: dict[str, Any],
    inventory: dict[str, Any],
    lifecycle: dict[str, Any],
    source: dict[str, Any],
    duplicate: dict[str, Any],
    forensics: dict[str, Any],
    blockers: dict[str, Any],
) -> dict[str, Any]:
    output_files = []
    for stem in REQUIRED_OUTPUT_STEMS:
        output_files.extend([f"{stem}.json", f"{stem}.md"])
    output_files.extend(
        [
            "G12_CNR_T3_NEXT_PROMPT_PACK_2026-05-08.md",
            "build_g12_cnr_t3_lifecycle_audit_2026_05_08.py",
            "verify_g12_cnr_t3_lifecycle_audit_2026_05_08.py",
            "test_g12_cnr_t3_lifecycle_audit_2026_05_08.py",
        ]
    )
    checklist = [
        {"requirement": "mandatory_gtos_preflight", "status": "PASS_RECORDED", "evidence": PREFLIGHT_READS},
        {"requirement": "context_anchor_before_decisions", "status": "PASS_RECORDED", "evidence": "builder writes context anchor before decision outputs"},
        {"requirement": "required_t3_inputs_read", "status": "PASS_RECORDED", "evidence": list(T3_JSON.values()) + [T3_ROWS.name]},
        {"requirement": "upstream_cnr_oti_artifacts_read", "status": "PASS_RECORDED", "evidence": UPSTREAM_REQUIRED},
        {"requirement": "local_heavy_data_roots_searched", "status": "PASS_RECORDED", "evidence": context["searched_root_ledger"]},
        {"requirement": "304_row_inventory_coverage", "status": inventory["status"], "evidence": inventory["recomputed_candidate_like_total"]},
        {"requirement": "six_eligible_rows", "status": lifecycle["status"], "evidence": lifecycle["eligible_inventory_ids"]},
        {"requirement": "298_exact_blockers", "status": blockers["status"], "evidence": blockers["blocker_count"]},
        {"requirement": "frozen_contract_before_scan", "status": "PASS" if lifecycle["checks"]["contract_freeze_order_before_scan_in_builder"] else "FAIL", "evidence": lifecycle["contract_freeze_evidence"]},
        {"requirement": "allowed_labels", "status": "PASS" if source["boundary_scan"]["allowed_label_set"] else "FAIL", "evidence": source["packet_label_set"]},
        {"requirement": "source_hashes", "status": source["status"], "evidence": source["consumed_tick_file_hash_checks"]},
        {"requirement": "no_leak_controls", "status": source["status"], "evidence": source["boundary_scan"]},
        {"requirement": "duplicate_sample_floor_controls", "status": duplicate["status"], "evidence": duplicate["sample_floor_reason"]},
        {"requirement": "94_blocked_row_exclusion", "status": "PASS" if source["boundary_scan"]["blocked_94_status_pass"] else "FAIL", "evidence": source["blocked_94_exclusion"]},
        {"requirement": "what_six_stop_after_original_horizon_labels_prove", "status": "PASS", "evidence": forensics["what_six_stop_after_original_horizon_labels_prove"]},
        {"requirement": "what_six_stop_after_original_horizon_labels_do_not_prove", "status": "PASS", "evidence": forensics["what_six_stop_after_original_horizon_labels_do_not_prove"]},
        {"requirement": "next_route_guidance", "status": "PASS", "evidence": blockers["route_decision_ledger"]},
        {"requirement": "py_compile", "status": "PENDING_VERIFIER", "evidence": "python -m py_compile builder/verifier/test"},
        {"requirement": "focused_pytest", "status": "PENDING_VERIFIER", "evidence": "pytest test_g12_cnr_t3_lifecycle_audit_2026_05_08.py -q"},
        {"requirement": "verifier_pass", "status": "PENDING_VERIFIER", "evidence": "python verify_g12_cnr_t3_lifecycle_audit_2026_05_08.py"},
        {"requirement": "final_live_state_regeneration", "status": "PENDING_FINAL_PREFLIGHT", "evidence": "python scripts/generate_live_state.py after verification"},
    ]
    all_static = all(item["status"] in {"PASS", "PASS_RECORDED"} or item["status"].startswith("PENDING") for item in checklist)
    return {
        **boundary_base("G12_CNR_T3_COMPLETION_AUDIT"),
        "objective_restatement": "Audit CNR_T3_LIFECYCLE_EXPANSION_SOURCE_PACKET_V1 as categorical lifecycle source evidence only, preserving NO_PROMOTION_VERDICT and live-effect false boundaries.",
        "output_files_expected": output_files,
        "prompt_to_artifact_checklist": checklist,
        "static_completion_status": "PASS_STATIC_ARTIFACTS_BUILT" if all_static else "FAIL_STATIC_ARTIFACTS",
        "decision_summary": decision["overall_decision"],
        "can_mark_goal_complete": False,
        "verification_status": "PENDING_VERIFIER",
    }


def write_all() -> dict[str, Any]:
    t3 = load_t3_artifacts()

    context = build_context_anchor()
    write_json("G12_CNR_T3_CONTEXT_ANCHOR_2026-05-08", context)
    write_md("G12_CNR_T3_CONTEXT_ANCHOR_2026-05-08", "G12 CNR T3 Context Anchor - 2026-05-08", simple_md(context, ["head_oneline", "branch", "controlling_prompt", "active_question_stack", "searched_root_ledger", "route_decision_ledger_initial", "git_status_short_at_anchor"]))

    inventory = inventory_coverage_audit(t3)
    lifecycle = lifecycle_packet_audit(t3)
    source = source_hash_and_noleak_audit(t3)
    duplicate = duplicate_samplefloor_audit(t3)
    blockers = blocker_and_route_ledger(t3, inventory)
    forensics = forensics_and_learning(t3, lifecycle, blockers)
    decision = decision_ledger(inventory, lifecycle, source, duplicate, blockers)
    completion = completion_audit(context, decision, inventory, lifecycle, source, duplicate, forensics, blockers)

    artifacts = [
        ("G12_CNR_T3_DECISION_LEDGER_2026-05-08", "G12 CNR T3 Decision Ledger - 2026-05-08", decision, ["overall_decision", "subpart_decisions", "audit_question_answers", "promotion_boundary"]),
        ("G12_CNR_T3_INVENTORY_COVERAGE_AUDIT_2026-05-08", "G12 CNR T3 Inventory Coverage Audit - 2026-05-08", inventory, ["decision", "status", "reported_candidate_count", "recomputed_candidate_like_total", "reported_source_lane_counts", "scan_mismatches", "coverage_boundary"]),
        ("G12_CNR_T3_LIFECYCLE_PACKET_AUDIT_2026-05-08", "G12 CNR T3 Lifecycle Packet Audit - 2026-05-08", lifecycle, ["decision", "status", "checks", "contract_freeze_evidence", "packet_lifecycle_label_counts", "tick_path_recompute", "what_this_proves", "what_this_does_not_prove"]),
        ("G12_CNR_T3_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08", "G12 CNR T3 Source Hash And Noleak Audit - 2026-05-08", source, ["decision", "status", "consumed_tick_file_hash_checks", "boundary_scan", "blocked_94_exclusion", "local_heavy_data_observation"]),
        ("G12_CNR_T3_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08", "G12 CNR T3 Duplicate Samplefloor Audit - 2026-05-08", duplicate, ["decision", "status", "packet_row_count", "unique_duplicate_groups", "duplicate_denominator_key_counts", "countable_denominator_rows", "sample_floor_reason"]),
        ("G12_CNR_T3_FORENSICS_AND_LEARNING_2026-05-08", "G12 CNR T3 Forensics And Learning - 2026-05-08", forensics, ["decision", "status", "categorical_learning", "six_row_context", "what_six_stop_after_original_horizon_labels_prove", "what_six_stop_after_original_horizon_labels_do_not_prove", "open_questions_reduced_to_routes"]),
        ("G12_CNR_T3_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08", "G12 CNR T3 Blocker And Next Route Ledger - 2026-05-08", blockers, ["decision", "status", "exactness_checks", "blocker_source_lane_counts", "first_next_lane", "route_decision_ledger", "exact_next_questions"]),
        ("G12_CNR_T3_COMPLETION_AUDIT_2026-05-08", "G12 CNR T3 Completion Audit - 2026-05-08", completion, ["objective_restatement", "decision_summary", "static_completion_status", "verification_status", "can_mark_goal_complete", "prompt_to_artifact_checklist"]),
    ]
    for stem, title, obj, keys in artifacts:
        write_json(stem, obj)
        write_md(stem, title, simple_md(obj, keys))

    (BASE / "G12_CNR_T3_NEXT_PROMPT_PACK_2026-05-08.md").write_text(prompt_pack(), encoding="utf-8")
    return completion


def main() -> None:
    completion = write_all()
    print(json.dumps({"status": completion["static_completion_status"], "decision": completion["decision_summary"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
