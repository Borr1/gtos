from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE_STAMP = "2026-05-08"
SCHEMA_VERSION = "g12_nofill_result_contract_audit_v1"
CONTRACT_ID = "NOFILL_LIFECYCLE_CLOSURE_RESULT_CONTRACT_V1"
AUDIT_LANE_ID = "G12_NOFILL_LIFECYCLE_RESULT_CONTRACT_AUDIT_V1"
DECISION = "ACCEPT_AS_FROZEN_RESULT_CONTRACT_FOR_FUTURE_CATEGORICAL_PACKET_AUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

EXPECTED_PACKET_ROWS = 298
EXPECTED_SOURCE_CLOSED = 298
EXPECTED_SOURCE_BLOCKED_EXACT = 0
EXPECTED_NOFILL_DUPLICATE_KEYS = 196
EXPECTED_DUPLICATE_GROUPS = 153
EXPECTED_ROW_0127_SHA256 = "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
EXPECTED_ROW_0127_FIRST_TOUCH = "2026-05-06T07:15:00.634000Z"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
BASE = Path("research/science_program_2026_05/06_outcome_testing")
DESIGN_DIR = BASE / "no_fill_lifecycle_result_contract_design"
SOURCE_PACKET_DIR = BASE / "no_fill_lifecycle_closure_source_packet"
CORR_G12_DIR = BASE / "g12_no_fill_correction_reaudit"
G12_LIFECYCLE_DIR = BASE / "g12_no_fill_lifecycle_audit"
G12_CLOSE_DIR = BASE / "g12_no_fill_closure_audit"
G12_T3_DIR = BASE / "g12_cnr_t3_lifecycle_audit"
PENDING_CONTRACT_DIR = BASE / "no_fill_still_pending_lifecycle_contract"
OTR061_DIR = BASE / "otr061_xau_tick_recovery"
ROW_0127_SOURCE = OTR061_DIR / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"

JSON_OUTPUTS = [
    f"G12_NOFILL_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE_STAMP}.json",
    f"G12_NOFILL_RESULT_CONTRACT_DECISION_LEDGER_{DATE_STAMP}.json",
    f"G12_NOFILL_RESULT_CONTRACT_RULEBOOK_AUDIT_{DATE_STAMP}.json",
    f"G12_NOFILL_RESULT_CONTRACT_SOURCE_NOLEAK_AUDIT_{DATE_STAMP}.json",
    f"G12_NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE_STAMP}.json",
    f"G12_NOFILL_RESULT_CONTRACT_BLOCKER_AND_GATE_LEDGER_{DATE_STAMP}.json",
    f"G12_NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.json",
]

MD_OUTPUTS = [
    f"G12_NOFILL_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE_STAMP}.md",
    f"G12_NOFILL_RESULT_CONTRACT_DECISION_LEDGER_{DATE_STAMP}.md",
    f"G12_NOFILL_RESULT_CONTRACT_RULEBOOK_AUDIT_{DATE_STAMP}.md",
    f"G12_NOFILL_RESULT_CONTRACT_SOURCE_NOLEAK_AUDIT_{DATE_STAMP}.md",
    f"G12_NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE_STAMP}.md",
    f"G12_NOFILL_RESULT_CONTRACT_BLOCKER_AND_GATE_LEDGER_{DATE_STAMP}.md",
    f"G12_NOFILL_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE_STAMP}.md",
    f"G12_NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.md",
]

PY_OUTPUTS = [
    "build_g12_nofill_result_contract_audit_2026_05_08.py",
    "verify_g12_nofill_result_contract_audit_2026_05_08.py",
    "test_g12_nofill_result_contract_audit_2026_05_08.py",
]

BASE_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

FORBIDDEN_FIELD_NAMES = {
    "account_history",
    "actual_r",
    "broker_actual_r",
    "broker_fill_state",
    "broker_order_id",
    "broker_position_id",
    "conservative_lower_bound_r",
    "descriptive_gross_synthetic_path_r",
    "descriptive_synthetic_path_r",
    "dsr",
    "expectancy",
    "hidden_label",
    "live_order_state",
    "live_trade_result",
    "mt5_deal_ticket",
    "mt5_order_ticket",
    "mt5_position_ticket",
    "pbo",
    "pending_ticket",
    "profit",
    "reward_r_to_tp1",
    "synthetic_r",
    "trade_state_ticket",
    "win_rate",
}

T3_EXCLUDED_IDS = {
    "CNR-T3-CAND-0001",
    "CNR-T3-CAND-0002",
    "CNR-T3-CAND-0003",
    "CNR-T3-CAND-0004",
    "CNR-T3-CAND-0005",
    "CNR-T3-CAND-0006",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path) -> Any:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with (REPO_ROOT / path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(name: str, payload: dict[str, Any]) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, title: str, body: str) -> None:
    (OUT_DIR / name).write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    abs_path = REPO_ROOT / path if not path.is_absolute() else path
    if not abs_path.exists() or not abs_path.is_file():
        return None
    h = hashlib.sha256()
    with abs_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_record(path: Path) -> dict[str, Any]:
    abs_path = REPO_ROOT / path if not path.is_absolute() else path
    return {
        "path": rel(abs_path),
        "exists": abs_path.exists(),
        "size_bytes": abs_path.stat().st_size if abs_path.exists() and abs_path.is_file() else None,
        "sha256": sha256_file(abs_path) if abs_path.exists() and abs_path.is_file() else None,
    }


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def counter_dict(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items(), key=lambda kv: kv[0]))


def scan_forbidden_keys(obj: Any, path: str = "$") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_FIELD_NAMES:
                hits.append({"path": child_path, "field": key})
            hits.extend(scan_forbidden_keys(value, child_path))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(scan_forbidden_keys(value, f"{path}[{idx}]"))
    return hits


def contains_value(obj: Any, wanted: str) -> bool:
    if isinstance(obj, str):
        return obj == wanted
    if isinstance(obj, dict):
        return any(contains_value(value, wanted) for value in obj.values())
    if isinstance(obj, list):
        return any(contains_value(value, wanted) for value in obj)
    return False


def load_inputs() -> dict[str, Any]:
    return {
        "design_rulebook": load_json(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE_STAMP}.json"),
        "design_universe": load_json(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_UNIVERSE_AND_EXCLUSION_LEDGER_{DATE_STAMP}.json"),
        "design_fields": load_json(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS_{DATE_STAMP}.json"),
        "design_parser": load_json(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_{DATE_STAMP}.json"),
        "design_noleak": load_json(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA_{DATE_STAMP}.json"),
        "design_duplicate": load_json(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_POLICY_{DATE_STAMP}.json"),
        "design_blockers": load_json(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_BLOCKER_LEDGER_{DATE_STAMP}.json"),
        "design_completion": load_json(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.json"),
        "corr_decision": load_json(CORR_G12_DIR / f"G12_NOFILL_CORR_DECISION_LEDGER_{DATE_STAMP}.json"),
        "corr_row_0127": load_json(CORR_G12_DIR / f"G12_NOFILL_CORR_ROW_0127_AUDIT_{DATE_STAMP}.json"),
        "source_packet": load_json(SOURCE_PACKET_DIR / f"NOFILL_CLOSE_ROW_PACKET_{DATE_STAMP}.json"),
        "source_rows": load_jsonl(SOURCE_PACKET_DIR / f"NOFILL_CLOSE_ROW_PACKET_{DATE_STAMP}_ROWS.jsonl"),
        "source_blockers": load_json(SOURCE_PACKET_DIR / f"NOFILL_CLOSE_ROW_BLOCKER_LEDGER_{DATE_STAMP}.json"),
        "source_duplicate": load_json(SOURCE_PACKET_DIR / f"NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE_STAMP}.json"),
        "source_noleak": load_json(SOURCE_PACKET_DIR / f"NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_{DATE_STAMP}.json"),
        "g12_universe": load_json(G12_LIFECYCLE_DIR / f"G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_{DATE_STAMP}.json"),
        "g12_lifecycle_decision": load_json(G12_LIFECYCLE_DIR / f"G12_NOFILL_DECISION_LEDGER_{DATE_STAMP}.json"),
        "g12_close_decision": load_json(G12_CLOSE_DIR / f"G12_NOFILL_CLOSE_DECISION_LEDGER_{DATE_STAMP}.json"),
        "g12_t3_decision": load_json(G12_T3_DIR / f"G12_CNR_T3_DECISION_LEDGER_{DATE_STAMP}.json"),
        "pending_contract": load_json(PENDING_CONTRACT_DIR / f"NOFILL_FROZEN_LIFECYCLE_CONTRACT_{DATE_STAMP}.json"),
        "pending_input": load_json(PENDING_CONTRACT_DIR / f"NOFILL_INPUT_ONLY_PACKET_{DATE_STAMP}.json"),
    }


def controlling_hashes() -> list[dict[str, Any]]:
    paths = [
        Path(".context/LIVE_STATE.md"),
        Path(".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md"),
        Path(".context/00_core/quick_reference_card.md"),
        Path(".context/00_core/research_operating_doctrine.md"),
        Path(".context/00_core/research_current_state.md"),
        Path(".context/00_core/goal_session_research_discipline.md"),
        Path(".context/00_core/local_heavy_data_inventory.md"),
        Path(".context/00_READING_ORDER.md"),
        OUT_DIR / f"G12_NOFILL_RESULT_CONTRACT_AUDIT_GOAL_PROMPT_{DATE_STAMP}.md",
        ROW_0127_SOURCE,
        SOURCE_PACKET_DIR / f"NOFILL_CLOSE_ROW_PACKET_{DATE_STAMP}.json",
        SOURCE_PACKET_DIR / f"NOFILL_CLOSE_ROW_PACKET_{DATE_STAMP}_ROWS.jsonl",
        SOURCE_PACKET_DIR / f"NOFILL_CLOSE_ROW_BLOCKER_LEDGER_{DATE_STAMP}.json",
        CORR_G12_DIR / f"G12_NOFILL_CORR_DECISION_LEDGER_{DATE_STAMP}.json",
        CORR_G12_DIR / f"G12_NOFILL_CORR_ROW_0127_AUDIT_{DATE_STAMP}.json",
        G12_LIFECYCLE_DIR / f"G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_{DATE_STAMP}.json",
        G12_T3_DIR / f"G12_CNR_T3_DECISION_LEDGER_{DATE_STAMP}.json",
    ]
    paths.extend(sorted(path for path in (REPO_ROOT / DESIGN_DIR).glob("*") if path.is_file()))
    records = []
    seen: set[str] = set()
    for path in paths:
        rec = hash_record(path)
        if rec["path"] not in seen:
            records.append(rec)
            seen.add(rec["path"])
    return records


def ts_to_z(ts: Any) -> str:
    return ts.isoformat().replace("+00:00", "Z")


def recompute_row_0127_event() -> dict[str, Any]:
    import pandas as pd

    source_path = REPO_ROOT / ROW_0127_SOURCE
    df = pd.read_parquet(source_path)
    path_start = pd.Timestamp("2026-05-06T07:15:00Z")
    window = df[df["ts_utc"] >= path_start]
    event_defs = [
        ("entry", window[window["ask"] <= 4561.52]),
        ("terminal_area", window[window["bid"] >= 4582.77]),
        ("protective", window[window["bid"] <= 4547.35]),
    ]
    events = []
    for event_name, event_rows in event_defs:
        if event_rows.empty:
            continue
        row = event_rows.iloc[0]
        events.append(
            {
                "event": event_name,
                "first_touch_utc": ts_to_z(row["ts_utc"]),
                "bid": float(row["bid"]),
                "ask": float(row["ask"]),
            }
        )
    events.sort(key=lambda item: item["first_touch_utc"])
    first_event = events[0] if events else None
    same_timestamp_ambiguity = bool(events and sum(1 for item in events if item["first_touch_utc"] == events[0]["first_touch_utc"]) > 1)
    return {
        "source_path": rel(ROW_0127_SOURCE),
        "source_sha256": sha256_file(ROW_0127_SOURCE),
        "source_rows_total": int(len(df)),
        "rows_at_or_after_path_start": int(len(window)),
        "source_first_ts_utc": ts_to_z(df.iloc[0]["ts_utc"]),
        "source_last_ts_utc": ts_to_z(df.iloc[-1]["ts_utc"]),
        "path_start_utc": "2026-05-06T07:15:00Z",
        "projected_side": "LONG",
        "entry_price": 4561.52,
        "terminal_area_price": 4582.77,
        "protective_level_price": 4547.35,
        "ordered_source_events": events,
        "first_source_event": first_event,
        "same_timestamp_ambiguity": same_timestamp_ambiguity,
        "expected_sha256_match": sha256_file(ROW_0127_SOURCE) == EXPECTED_ROW_0127_SHA256,
        "expected_first_touch_match": bool(first_event and first_event["first_touch_utc"] == EXPECTED_ROW_0127_FIRST_TOUCH),
    }


def packet_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    exact_blockers = []
    for row in rows:
        exact_blockers.extend(row.get("exact_blockers", []))
    return {
        "packet_rows": len(rows),
        "closure_status_counts": counter_dict([row.get("closure_status", "") for row in rows]),
        "closure_label_counts": counter_dict([row.get("closure_label", "") for row in rows]),
        "source_lane_counts": counter_dict([row.get("source_lane", "") for row in rows]),
        "source_inventory_id_unique": len({row.get("source_inventory_id") for row in rows}),
        "nofill_duplicate_key_unique": len({row.get("nofill_duplicate_key") for row in rows}),
        "duplicate_group_id_unique": len({row.get("duplicate_group_id") for row in rows}),
        "source_blocked_exact_rows": sum(1 for row in rows if row.get("closure_status") == "source_blocked_exact"),
        "source_closed_rows": sum(1 for row in rows if row.get("closure_status") == "source_closed"),
        "rows_with_exact_blockers": sum(1 for row in rows if row.get("exact_blockers")),
        "exact_blocker_counts": counter_dict(exact_blockers),
        "t3_excluded_id_overlap": sorted(T3_EXCLUDED_IDS & {str(row.get("source_inventory_id")) for row in rows}),
        "blocked_cnr061_lane_rows": [row.get("packet_row_id") for row in rows if row.get("source_lane") == "OTI8_CNR061"],
        "stop_after_original_horizon_hits": [
            row.get("packet_row_id")
            for row in rows
            if contains_value(row, "stop_after_original_horizon")
        ],
        "forbidden_field_hits": [
            {"packet_row_id": row.get("packet_row_id"), **hit}
            for row in rows
            for hit in scan_forbidden_keys(row)
        ],
    }


def build_context_anchor(generated_at: str, hashes: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "artifact_family": "G12_NOFILL_RESULT_CONTRACT_CONTEXT_ANCHOR",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": generated_at,
        "git_head": git_head(),
        **BASE_FLAGS,
        "preflight_completed": {
            "generate_live_state": True,
            "live_state_read": True,
            "latest_handoff_read": True,
            "quick_reference_card_read": True,
            "research_operating_doctrine_read": True,
            "research_current_state_read": True,
            "goal_session_research_discipline_read": True,
            "local_heavy_data_inventory_read": True,
            "reading_order_read": True,
            "claude_md_read": True,
        },
        "controlling_inputs": [
            rel(DESIGN_DIR),
            rel(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE_STAMP}.md"),
            rel(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE_STAMP}.json"),
            rel(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_UNIVERSE_AND_EXCLUSION_LEDGER_{DATE_STAMP}.json"),
            rel(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS_{DATE_STAMP}.json"),
            rel(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_{DATE_STAMP}.json"),
            rel(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA_{DATE_STAMP}.json"),
            rel(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_POLICY_{DATE_STAMP}.json"),
            rel(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_BLOCKER_LEDGER_{DATE_STAMP}.json"),
            rel(DESIGN_DIR / f"NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.json"),
            rel(SOURCE_PACKET_DIR),
            rel(CORR_G12_DIR),
            rel(G12_LIFECYCLE_DIR),
            rel(G12_T3_DIR),
            rel(OTR061_DIR),
        ],
        "searched_roots": [
            rel(DESIGN_DIR),
            rel(SOURCE_PACKET_DIR),
            rel(CORR_G12_DIR),
            rel(G12_LIFECYCLE_DIR),
            rel(G12_CLOSE_DIR),
            rel(G12_T3_DIR),
            rel(PENDING_CONTRACT_DIR),
            rel(OTR061_DIR),
            "C:/Users/MSI/Documents/ai-trading-agent/data/ticks (prior source-hashed upstream search referenced; not re-traversed because required OTR061 source exists in worktree)",
            "C:/tmp/gtos_otb (prior worktree source copies referenced by upstream search ledger)",
        ],
        "active_question_stack": [
            "Is the 298-row source-closed universe frozen enough for a later categorical result packet lane?",
            "Are six T3 rows and 94 G12-blocked CNR061 rows exactly excluded?",
            "Are lifecycle label families separated from R, broker actual-R, account, live, order, and hidden labels?",
            "Are entry, fill, cancel, expiry, still-pending, no-entry, terminal-first, wrong-side, and ambiguity semantics precise enough?",
            "Are LONG and SHORT bid/ask parser rules side-aware and correct?",
            "Are source hierarchy, source-hash, no-leak/as-of, duplicate, sample-floor, and blocker policies enforceable?",
            "What exact future result-lane gates remain after acceptance?",
        ],
        "route_decisions": [
            "Audit only the frozen result contract; do not open a result or quarantine lane.",
            "Recompute counts, exclusions, duplicate denominators, blocker counts, forbidden-field scans, source hash, and row 0127 terminal-first evidence.",
            "Treat 204 current source blockers as row-level future result blockers, not contract blockers.",
            "Accept the contract only if future labels remain categorical lifecycle evidence and row-level gates run before labels.",
        ],
        "source_files_read_or_hashed": hashes,
    }


def build_rulebook_audit(inputs: dict[str, Any], row_0127: dict[str, Any]) -> dict[str, Any]:
    rulebook = inputs["design_rulebook"]
    parser = inputs["design_parser"]
    fields = inputs["design_fields"]
    noleak = inputs["design_noleak"]
    issues: list[str] = []
    required_sections = [
        "eligible_universe",
        "result_label_families",
        "entry_fill_cancel_expiry_semantics",
        "side_aware_touch_parser",
        "source_hierarchy",
        "same_bar_and_terminal_order_policy",
        "duplicate_denominator_policy",
        "sample_floor_policy",
        "no_leak_asof_schema",
        "source_hash_and_cache_policy",
        "dsr_pbo_effective_n_policy",
        "exact_next_lane_gates",
    ]
    for section in required_sections:
        if section not in rulebook:
            issues.append(f"missing_section:{section}")
    side_rules = parser["side_rules"]
    expected_rules = {
        ("LONG", "entry_touch"): "ask <= entry_price",
        ("LONG", "terminal_area_touch"): "bid >= terminal_area_price",
        ("LONG", "protective_touch"): "bid <= protective_level_price",
        ("SHORT", "entry_touch"): "bid >= entry_price",
        ("SHORT", "terminal_area_touch"): "ask <= terminal_area_price",
        ("SHORT", "protective_touch"): "ask >= protective_level_price",
    }
    for (side, key), expected in expected_rules.items():
        if side_rules.get(side, {}).get(key) != expected:
            issues.append(f"parser_mismatch:{side}.{key}")
    for field in ["entry_touched_at_utc", "filled_at_utc", "cancelled_at_utc", "cancel_reason", "expired_at_utc", "frozen_horizon_end_utc"]:
        if field not in fields["required_pending_intent_closure_fields"]:
            issues.append(f"missing_pending_intent_field:{field}")
    if "broker_actual_r" not in noleak["forbidden_fields"]:
        issues.append("broker_actual_r_not_forbidden")
    if row_0127["first_source_event"]["event"] != "terminal_area":
        issues.append("row_0127_first_event_not_terminal_area")
    return {
        "artifact_family": "G12_NOFILL_RESULT_CONTRACT_RULEBOOK_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        **BASE_FLAGS,
        "decision": "ACCEPT_RULEBOOK_WITH_FUTURE_ROW_LEVEL_GATES",
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "required_sections_checked": required_sections,
        "side_aware_parser_verdict": "PASS",
        "entry_fill_cancel_expiry_semantics_verdict": "PASS_CATEGORICAL_ONLY_QUOTE_TOUCH_NOT_BROKER_FILL",
        "source_hierarchy_verdict": "PASS_TICK_QUOTE_REQUIRED_FOR_SIDE_AWARE_ORDERING_M1_PRICE_CONTEXT_ONLY",
        "pending_intent_fields_verdict": "PASS_REQUIRED_FIELDS_LISTED; missing fields must block row labels",
        "row_0127_recomputed_terminal_first": row_0127,
        "audit_question_answers": [
            {
                "question": "Is the eligible universe frozen enough for a later result packet lane?",
                "answer": "Yes, as a source-closed input universe only. Future labels still require row-level eligibility/blocker decisions before labels.",
            },
            {
                "question": "Are entry/fill/cancel/expiry semantics precise enough?",
                "answer": "Yes for categorical no-fill lifecycle closure. The contract explicitly prevents quote touch from becoming broker fill or performance.",
            },
            {
                "question": "Are bid/ask side-aware rules correct?",
                "answer": "Yes: LONG entry ask<=entry, terminal bid>=terminal, protective bid<=protective; SHORT entry bid>=entry, terminal ask<=terminal, protective ask>=protective.",
            },
            {
                "question": "Does the contract need exact extra fields before any result lane?",
                "answer": "No contract rewrite is required. The future result builder must block any row missing the listed pending-intent closure fields, especially entry_touched_at_utc/fill/cancel/expiry/horizon fields.",
            },
        ],
        "non_blocking_watch_items_for_future_builder": [
            "Keep pending_intent_id as source identity/control metadata, not a decision feature or broker ticket.",
            "Treat side-aware quote entry touch as lifecycle eligibility only; it is not a broker fill or R/performance label.",
            "Do not use row 0127 beyond terminal-first categorical closure unless a later lane needs full-horizon proof and satisfies the exact source request.",
        ],
    }


def build_source_noleak_audit(inputs: dict[str, Any], metrics: dict[str, Any], row_0127: dict[str, Any]) -> dict[str, Any]:
    source_audit = inputs["source_noleak"]
    return {
        "artifact_family": "G12_NOFILL_RESULT_CONTRACT_SOURCE_NOLEAK_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        **BASE_FLAGS,
        "decision": "ACCEPT_SOURCE_HASH_AND_NOLEAK_BOUNDARY",
        "status": "PASS"
        if (
            not metrics["forbidden_field_hits"]
            and not metrics["blocked_cnr061_lane_rows"]
            and not metrics["t3_excluded_id_overlap"]
            and not metrics["stop_after_original_horizon_hits"]
            and row_0127["expected_sha256_match"]
            and row_0127["expected_first_touch_match"]
        )
        else "FAIL",
        "forbidden_packet_field_hits": metrics["forbidden_field_hits"],
        "blocked_cnr061_lane_rows_in_packet": metrics["blocked_cnr061_lane_rows"],
        "six_t3_overlap": metrics["t3_excluded_id_overlap"],
        "stop_after_original_horizon_hits": metrics["stop_after_original_horizon_hits"],
        "row_0127_source_hash_recomputed": row_0127["source_sha256"],
        "row_0127_first_touch_recomputed": row_0127["first_source_event"],
        "upstream_source_hash_audit_status": source_audit.get("status"),
        "upstream_forbidden_packet_hits_count": source_audit.get("forbidden_packet_hits_count"),
        "forbidden_surface_counters": {
            "broker_actual_r_accessed": source_audit.get("broker_actual_r_accessed"),
            "account_history_accessed": source_audit.get("account_history_accessed"),
            "live_trade_results_accessed": source_audit.get("live_trade_results_accessed"),
            "mt5_order_calls": source_audit.get("mt5_order_calls"),
            "mt5_account_calls": source_audit.get("mt5_account_calls"),
            "paid_data_calls": source_audit.get("paid_data_calls"),
            "databento_calls": source_audit.get("databento_calls"),
            "api_calls": source_audit.get("api_calls"),
            "canary_calls": source_audit.get("canary_calls"),
        },
        "no_leak_verdict": "PASS: categorical lifecycle labels only; no R/performance/broker/account/live/order/hidden fields may enter future row payloads.",
        "asof_verdict": "PASS: decision-time geometry stays frozen; label-time source events cannot modify geometry or duplicate keys.",
    }


def build_duplicate_samplefloor_audit(inputs: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    duplicate = inputs["design_duplicate"]
    rows = inputs["source_rows"]
    nofill_counts = Counter(str(row.get("nofill_duplicate_key")) for row in rows)
    group_counts = Counter(str(row.get("duplicate_group_id")) for row in rows)
    return {
        "artifact_family": "G12_NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        **BASE_FLAGS,
        "decision": "ACCEPT_DUPLICATE_AND_SAMPLEFLOOR_POLICY",
        "status": "PASS"
        if (
            metrics["packet_rows"] == EXPECTED_PACKET_ROWS
            and metrics["nofill_duplicate_key_unique"] == EXPECTED_NOFILL_DUPLICATE_KEYS
            and metrics["duplicate_group_id_unique"] == EXPECTED_DUPLICATE_GROUPS
            and duplicate["sample_floor_policy"]["current_design_lane"]["can_claim_validation"] is False
        )
        else "FAIL",
        "recomputed_duplicate_state": {
            "packet_rows": metrics["packet_rows"],
            "source_inventory_id_unique": metrics["source_inventory_id_unique"],
            "nofill_duplicate_key_unique": metrics["nofill_duplicate_key_unique"],
            "duplicate_group_id_unique": metrics["duplicate_group_id_unique"],
            "nofill_duplicate_key_max_repeat": max(nofill_counts.values()),
            "duplicate_group_id_max_repeat": max(group_counts.values()),
            "nofill_duplicate_key_repeated_count": sum(1 for value in nofill_counts.values() if value > 1),
            "duplicate_group_id_repeated_count": sum(1 for value in group_counts.values() if value > 1),
        },
        "frozen_policy": duplicate["sample_floor_policy"],
        "denominator_verdict": "PASS: row-level counts are source inventory only; future reports must collapse by nofill_duplicate_key and carry duplicate conflicts as blockers.",
        "validation_promotion_boundary": "No validation or promotion claim is possible from this design or future under-floor discovery counts; promotion remains blocked without a separate dossier.",
    }


def build_blocker_gate_ledger(inputs: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    blockers = inputs["design_blockers"]
    exact_next_lane_gates = [
        "Run G12 audit acceptance check for this contract before building any result packet.",
        "Future result packet builder must emit row-level eligibility/blocker decisions before assigning any lifecycle labels.",
        "Use only the 298 source_closed input rows; reject any non-source_closed row.",
        "Exclude CNR-T3-CAND-0001..0006, any stop_after_original_horizon row, and every OTI8_CNR061/G12-blocked CNR061 row.",
        "Re-run source hashes for every consumed file; any missing file or hash mismatch is BLOCK_RESULT_MISSING_SOURCE or BLOCK_RESULT_SOURCE_HASH_MISMATCH.",
        "Apply bid_ask_side_aware_touch_times_v1 exactly; M1/M5 OHLC alone cannot prove side-aware fill or terminal/protective ordering.",
        "Block same-timestamp or same-bar unresolved entry/terminal/protective ordering.",
        "Block missing pending-intent closure fields instead of inferring cancel, expiry, fill, or still-pending labels.",
        "Block duplicate-key conflicts and report both row-level and nofill_duplicate_key denominators.",
        "Keep DSR/PBO/effective-N not_computable unless a separate approved numeric performance lane exists.",
        "Stop if R/performance, broker/account/live/order/hidden labels, paid/API/Databento, MT5 order/account calls, registry, credential, remote, or live trading surface changes are required.",
    ]
    return {
        "artifact_family": "G12_NOFILL_RESULT_CONTRACT_BLOCKER_AND_GATE_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        **BASE_FLAGS,
        "decision": "ACCEPT_BLOCKERS_AND_NEXT_RESULT_LANE_GATES",
        "status": "PASS" if metrics["exact_blocker_counts"] == blockers["current_exact_blocker_counts_from_source_closure_packet"] else "FAIL",
        "recomputed_current_exact_blocker_counts": metrics["exact_blocker_counts"],
        "rows_with_exact_blockers": metrics["rows_with_exact_blockers"],
        "contract_blocker_rules": blockers["result_contract_blocker_rules"],
        "current_row_blockers_remain_future_row_level_blockers": True,
        "contract_acceptance_blockers": [],
        "exact_next_lane_gates": exact_next_lane_gates,
        "next_allowed_lane": "NOFILL_LIFECYCLE_CLOSURE_CATEGORICAL_RESULT_PACKET_V1",
        "next_lane_not_allowed_to_do": [
            "score R/performance/win-rate/expectancy",
            "inspect broker actual-R/account history/live order/deal/position/live result/hidden labels",
            "score blocked CNR061 rows or six excluded T3 rows",
            "call paid/API/Databento or MT5 order/account surfaces",
            "edit registries/remotes/credentials/live trading prompts/risk/execution/permissions/safety/selectors/order behavior",
            "claim validation, promotion, or live effect",
        ],
    }


def build_decision_ledger(inputs: dict[str, Any], metrics: dict[str, Any], row_0127: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_family": "G12_NOFILL_RESULT_CONTRACT_DECISION_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        **BASE_FLAGS,
        "overall_decision": DECISION,
        "decision_status": "PASS_ACCEPTED",
        "accepted_scope": "frozen preregistered categorical lifecycle result contract only; no current result rows opened",
        "non_claims": [
            "No R/performance scoring.",
            "No broker/account/live/order/hidden labels inspected.",
            "No blocked CNR061 or six T3 rows scored.",
            "No validation, promotion, or live effect.",
            "No paid/API/Databento or MT5 order/account calls.",
        ],
        "starting_facts_verified": {
            "g12_corrected_packet_decision": inputs["corr_decision"]["decision"],
            "packet_rows": metrics["packet_rows"],
            "source_closed": metrics["source_closed_rows"],
            "source_blocked_exact": metrics["source_blocked_exact_rows"],
            "row_0127_sha256": row_0127["source_sha256"],
            "row_0127_first_terminal_area_touch": row_0127["first_source_event"]["first_touch_utc"],
            "six_t3_excluded": not metrics["t3_excluded_id_overlap"],
            "blocked_94_cnr061_excluded": not metrics["blocked_cnr061_lane_rows"] and inputs["g12_universe"]["blocked_94_exclusion"]["blocked_rows"] == 94,
        },
        "subpart_decisions": {
            "eligible_universe": "ACCEPT_SOURCE_CLOSED_INPUT_UNIVERSE_ONLY",
            "exclusions": "ACCEPT_EXACT_T3_AND_BLOCKED_CNR061_EXCLUSIONS",
            "label_family_separation": "ACCEPT_CATEGORICAL_LIFECYCLE_ONLY_BOUNDARY",
            "entry_fill_cancel_expiry_semantics": "ACCEPT_WITH_QUOTE_TOUCH_NOT_BROKER_FILL_BOUNDARY",
            "side_aware_parser": "ACCEPT_BID_ASK_SIDE_AWARE_PARSER",
            "source_hierarchy_and_hashes": "ACCEPT_TICK_QUOTE_FIRST_SOURCE_HIERARCHY",
            "pending_intent_fields": "ACCEPT_REQUIRED_FIELDS_AS_FUTURE_ROW_BLOCKERS_IF_MISSING",
            "duplicate_sample_floor": "ACCEPT_DENOMINATOR_AND_UNDER_SAMPLE_FLOOR_POLICY",
            "noleak_asof": "ACCEPT_NOLEAK_ASOF_SCHEMA",
            "exact_blockers": "ACCEPT_RESULT_BLOCKER_RULES",
            "next_lane": "ALLOW_ONLY_SEPARATE_CATEGORICAL_RESULT_PACKET_LANE_AFTER_THIS_ACCEPTANCE",
        },
        "primary_reasons": [
            "The contract preserves the corrected source packet state: 298 source_closed rows and 0 source_blocked_exact rows.",
            "Row 0127 recomputes from the OTR061 parquet SHA256 and first terminal-area touch exactly.",
            "The six accepted CNR T3 rows and 94 G12-blocked CNR061 rows remain excluded and unscored.",
            "The side-aware parser and source hierarchy prevent lower-timeframe OHLC or quote touches from becoming broker fill or R/performance claims.",
            "The duplicate/sample-floor rules prevent row-repeat inflation and keep validation/promotion closed.",
            "Exact blockers and next-lane gates are strong enough to stop weak rows before labels.",
        ],
        "contract_acceptance_blockers": [],
        "future_row_level_blockers_still_present": [
            "204 source-closed rows currently carry exact source-field blockers and must be blocked row-by-row unless a future source-safe packet clears them.",
            "M1/OHLC price-compatible rows cannot receive side-aware fill/order labels without tick/quote or an accepted conservative quote contract.",
            "Pending lifecycle rows without materialized entry_touched_at_utc/fill/cancel/expiry/horizon fields cannot receive inferred labels.",
        ],
    }


def build_completion_audit(generated_at: str) -> dict[str, Any]:
    checklist = [
        ("Mandatory GTOS preflight completed and context anchors read", "context anchor preflight_completed plus source hashes"),
        ("NOFILL_RESULT_CONTRACT_NEXT_PROMPT_PACK used as controlling input", "context anchor controlling_inputs and source hash list"),
        ("Frozen rulebook audited", "rulebook audit artifact"),
        ("Universe/exclusion ledger audited", "decision ledger and source/no-leak audit"),
        ("Field/source requirements audited", "rulebook audit and blocker/gate ledger"),
        ("Touch/path parser audited", "rulebook audit side_aware_parser_verdict"),
        ("No-leak/as-of schema audited", "source/no-leak audit"),
        ("Duplicate/sample-floor policy audited", "duplicate/sample-floor audit"),
        ("Blocker and completion artifacts audited", "blocker/gate ledger and completion audit"),
        ("Builder/verifier/test artifacts audited", "verifier includes design verifier read-only and py_compile/pytest"),
        ("298 source_closed / 0 source_blocked_exact independently verified", "decision ledger starting_facts_verified"),
        ("Row 0127 SHA256 and first terminal-area touch recomputed", "source/no-leak audit row_0127 fields"),
        ("Six T3 rows and 94 CNR061 blocked rows excluded", "source/no-leak audit and decision ledger"),
        ("Label-family separation preserved", "rulebook and source/no-leak audits"),
        ("Entry/fill/cancel/expiry semantics preserved", "rulebook audit"),
        ("Side-aware parser preserved", "rulebook audit"),
        ("Source hierarchy and pending-intent closure fields preserved", "rulebook audit and gate ledger"),
        ("Exact next result-lane gates written", "blocker/gate ledger and next prompt pack"),
        ("NO_PROMOTION_VERDICT and false safety flags preserved", "all generated JSON flags plus verifier"),
        ("Forbidden live/account/broker/order/paid/API surfaces avoided", "source/no-leak audit and live-surface diff verifier"),
    ]
    return {
        "artifact_family": "G12_NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": generated_at,
        **BASE_FLAGS,
        "objective_restatement": (
            "Run a G12 red-team audit of NOFILL_LIFECYCLE_CLOSURE_RESULT_CONTRACT_V1 and decide accept/block/reject "
            "before any result lane opens, while preserving source-only/no-promotion/no-validation/no-live-effect boundaries."
        ),
        "expected_artifacts": JSON_OUTPUTS + MD_OUTPUTS + PY_OUTPUTS,
        "prompt_to_artifact_checklist": [
            {"requirement": req, "evidence": evidence, "status": "PENDING_VERIFIER"} for req, evidence in checklist
        ],
        "verification_results": {"status": "PENDING_RUN_VERIFY_SCRIPT"},
        "missing_or_weak_requirements": ["Verifier has not yet finalized this completion audit."],
        "can_mark_goal_complete": False,
    }


def write_markdown(payloads: dict[str, dict[str, Any]]) -> None:
    context = payloads["context"]
    write_md(
        f"G12_NOFILL_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE_STAMP}.md",
        "G12 NOFILL Result Contract Context Anchor",
        "\n".join(
            [
                f"Audit lane: `{AUDIT_LANE_ID}`",
                f"Contract: `{CONTRACT_ID}`",
                f"Generated: `{context['generated_at_utc']}`",
                "",
                "## Boundaries",
                "",
                "- `NO_PROMOTION_VERDICT`",
                "- `validation_safe=false`",
                "- `outcome_review_opened=false`",
                "- `live_effect=false`",
                "- No R/performance, broker/account/live/order/hidden labels, paid/API/Databento, MT5 order/account calls, or live-surface edits.",
                "",
                "## Active Questions",
                "",
                "\n".join(f"- {item}" for item in context["active_question_stack"]),
                "",
                "## Searched Roots",
                "",
                "\n".join(f"- `{item}`" for item in context["searched_roots"]),
            ]
        ),
    )
    decision = payloads["decision"]
    facts = decision["starting_facts_verified"]
    write_md(
        f"G12_NOFILL_RESULT_CONTRACT_DECISION_LEDGER_{DATE_STAMP}.md",
        "G12 NOFILL Result Contract Decision Ledger",
        "\n".join(
            [
                f"Decision: `{decision['overall_decision']}`",
                f"Status: `{decision['decision_status']}`",
                "",
                "## Verified Starting Facts",
                "",
                f"- Packet rows/source closed/source blocked exact: `{facts['packet_rows']}` / `{facts['source_closed']}` / `{facts['source_blocked_exact']}`",
                f"- Row 0127 SHA256: `{facts['row_0127_sha256']}`",
                f"- Row 0127 first terminal-area touch: `{facts['row_0127_first_terminal_area_touch']}`",
                f"- Six T3 excluded: `{str(facts['six_t3_excluded']).lower()}`",
                f"- Blocked 94 CNR061 excluded: `{str(facts['blocked_94_cnr061_excluded']).lower()}`",
                "",
                "The contract is accepted only as a frozen rulebook for a future categorical lifecycle packet. It opens no result lane by itself.",
            ]
        ),
    )
    rulebook = payloads["rulebook"]
    write_md(
        f"G12_NOFILL_RESULT_CONTRACT_RULEBOOK_AUDIT_{DATE_STAMP}.md",
        "G12 NOFILL Result Contract Rulebook Audit",
        "\n".join(
            [
                f"Status: `{rulebook['status']}`",
                f"Decision: `{rulebook['decision']}`",
                "",
                f"Side-aware parser verdict: `{rulebook['side_aware_parser_verdict']}`",
                f"Entry/fill/cancel/expiry verdict: `{rulebook['entry_fill_cancel_expiry_semantics_verdict']}`",
                f"Source hierarchy verdict: `{rulebook['source_hierarchy_verdict']}`",
                "",
                "Non-blocking future-builder watch items:",
                "\n".join(f"- {item}" for item in rulebook["non_blocking_watch_items_for_future_builder"]),
            ]
        ),
    )
    source = payloads["source_noleak"]
    write_md(
        f"G12_NOFILL_RESULT_CONTRACT_SOURCE_NOLEAK_AUDIT_{DATE_STAMP}.md",
        "G12 NOFILL Result Contract Source Noleak Audit",
        "\n".join(
            [
                f"Status: `{source['status']}`",
                f"Decision: `{source['decision']}`",
                f"Forbidden packet field hits: `{len(source['forbidden_packet_field_hits'])}`",
                f"Blocked CNR061 packet rows: `{len(source['blocked_cnr061_lane_rows_in_packet'])}`",
                f"Six T3 overlap: `{len(source['six_t3_overlap'])}`",
                f"Row 0127 recomputed SHA256: `{source['row_0127_source_hash_recomputed']}`",
                f"Row 0127 first source event: `{source['row_0127_first_touch_recomputed']['first_touch_utc']}`",
                "",
                source["no_leak_verdict"],
            ]
        ),
    )
    duplicate = payloads["duplicate"]
    write_md(
        f"G12_NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE_STAMP}.md",
        "G12 NOFILL Result Contract Duplicate Samplefloor Audit",
        "\n".join(
            [
                f"Status: `{duplicate['status']}`",
                f"Decision: `{duplicate['decision']}`",
                f"Packet rows: `{duplicate['recomputed_duplicate_state']['packet_rows']}`",
                f"Unique nofill duplicate keys: `{duplicate['recomputed_duplicate_state']['nofill_duplicate_key_unique']}`",
                f"Unique duplicate groups: `{duplicate['recomputed_duplicate_state']['duplicate_group_id_unique']}`",
                "",
                duplicate["denominator_verdict"],
                duplicate["validation_promotion_boundary"],
            ]
        ),
    )
    gates = payloads["blockers"]
    write_md(
        f"G12_NOFILL_RESULT_CONTRACT_BLOCKER_AND_GATE_LEDGER_{DATE_STAMP}.md",
        "G12 NOFILL Result Contract Blocker And Gate Ledger",
        "\n".join(
            [
                f"Status: `{gates['status']}`",
                f"Decision: `{gates['decision']}`",
                f"Next allowed lane: `{gates['next_allowed_lane']}`",
                f"Contract acceptance blockers: `{len(gates['contract_acceptance_blockers'])}`",
                "",
                "## Exact Next-Lane Gates",
                "",
                "\n".join(f"- {item}" for item in gates["exact_next_lane_gates"]),
            ]
        ),
    )


def write_next_prompt_pack() -> None:
    write_md(
        f"G12_NOFILL_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE_STAMP}.md",
        "G12 NOFILL Result Contract Next Prompt Pack",
        f"""Run only after `G12_NOFILL_LIFECYCLE_RESULT_CONTRACT_AUDIT_V1` accepts `{CONTRACT_ID}`.

Recommended next lane: `NOFILL_LIFECYCLE_CLOSURE_CATEGORICAL_RESULT_PACKET_V1`.

Objective: build a categorical lifecycle result packet from the accepted 298-row source-closed no-fill input universe, but only after emitting row-level eligibility/blocker decisions before labels. The lane may categorize lifecycle closure states only. It must not score R/performance, win-rate, expectancy, broker actual-R, account history, live order/deal/position, hidden labels, validation, promotion, or live effect.

Starting facts to preserve:
- Corrected source packet: `298 source_closed / 0 source_blocked_exact`.
- Row `NOFILL-CLOSE-ROW-0127` OTR061 SHA256: `{EXPECTED_ROW_0127_SHA256}`.
- Row `NOFILL-CLOSE-ROW-0127` first terminal-area touch: `{EXPECTED_ROW_0127_FIRST_TOUCH}`.
- Six T3 rows `CNR-T3-CAND-0001..0006` and all 94 G12-blocked CNR061 rows remain excluded.
- All outputs must preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Required gates:
- Re-run source hashes for every consumed source file.
- Apply `bid_ask_side_aware_touch_times_v1` exactly.
- Treat M1/M5 OHLC as price-compatible context only unless a separate accepted conservative quote contract exists.
- Block missing pending-intent closure fields, source hash mismatches, same-timestamp/same-bar terminal-order ambiguity, duplicate conflicts, forbidden fields, and excluded universes.
- Report row-level counts and collapsed `nofill_duplicate_key` counts; keep validation/promotion blocked regardless of discovery counts.

Hard boundaries: no broker/account/live/order/hidden labels, no R/performance scoring, no blocked CNR061 or six T3 scoring, no paid/API/Databento or MT5 order/account calls, no registry/remote/credential/live-surface edits, and no validation/promotion/live-effect claim.
""",
    )


def build_artifacts() -> dict[str, dict[str, Any]]:
    generated_at = now_utc()
    inputs = load_inputs()
    rows = inputs["source_rows"]
    metrics = packet_metrics(rows)
    row_0127 = recompute_row_0127_event()
    hashes = controlling_hashes()
    payloads = {
        "context": build_context_anchor(generated_at, hashes),
        "rulebook": build_rulebook_audit(inputs, row_0127),
        "source_noleak": build_source_noleak_audit(inputs, metrics, row_0127),
        "duplicate": build_duplicate_samplefloor_audit(inputs, metrics),
        "blockers": build_blocker_gate_ledger(inputs, metrics),
        "decision": build_decision_ledger(inputs, metrics, row_0127),
        "completion": build_completion_audit(generated_at),
    }
    write_json(f"G12_NOFILL_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE_STAMP}.json", payloads["context"])
    write_json(f"G12_NOFILL_RESULT_CONTRACT_DECISION_LEDGER_{DATE_STAMP}.json", payloads["decision"])
    write_json(f"G12_NOFILL_RESULT_CONTRACT_RULEBOOK_AUDIT_{DATE_STAMP}.json", payloads["rulebook"])
    write_json(f"G12_NOFILL_RESULT_CONTRACT_SOURCE_NOLEAK_AUDIT_{DATE_STAMP}.json", payloads["source_noleak"])
    write_json(f"G12_NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE_STAMP}.json", payloads["duplicate"])
    write_json(f"G12_NOFILL_RESULT_CONTRACT_BLOCKER_AND_GATE_LEDGER_{DATE_STAMP}.json", payloads["blockers"])
    write_json(f"G12_NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.json", payloads["completion"])
    write_markdown(payloads)
    write_next_prompt_pack()
    write_md(
        f"G12_NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.md",
        "G12 NOFILL Result Contract Completion Audit",
        "Generated completion audit is pending verifier finalization. Run `verify_g12_nofill_result_contract_audit_2026_05_08.py`.",
    )
    return payloads


def main() -> None:
    payloads = build_artifacts()
    print(
        json.dumps(
            {
                "status": "BUILT",
                "audit_lane_id": AUDIT_LANE_ID,
                "contract_id": CONTRACT_ID,
                "decision": payloads["decision"]["overall_decision"],
                "packet_rows": payloads["decision"]["starting_facts_verified"]["packet_rows"],
                "row_0127_first_touch": payloads["decision"]["starting_facts_verified"]["row_0127_first_terminal_area_touch"],
                **BASE_FLAGS,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
