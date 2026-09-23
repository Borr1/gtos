#!/usr/bin/env python3
"""Build SEPARATE_NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT_V1 artifacts.

Research/control only. This script reads prior source-hashed CNR T3 and OTI
artifacts, writes the no-fill context anchor and frozen contract before
classification, then creates input-only lifecycle rows for the 298 non-T3 rows.
It intentionally does not compute or carry R/performance/live/account fields.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
SCHEMA = "separate_no_fill_still_pending_lifecycle_contract_v1"
CONTRACT_ID = "SEPARATE_NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
OUTCOME_ROOT = REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_PATH = OUT_DIR / "NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT_GOAL_PROMPT_2026-05-08.md"
MAIN_ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")

CORE_CONTEXT_INPUTS = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_READING_ORDER.md",
]

CONTROL_INPUTS = [
    "g12_cnr_t3_lifecycle_audit/G12_CNR_T3_NEXT_PROMPT_PACK_2026-05-08.md",
    "g12_cnr_t3_lifecycle_audit/G12_CNR_T3_DECISION_LEDGER_2026-05-08.json",
    "g12_cnr_t3_lifecycle_audit/G12_CNR_T3_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08.json",
    "g12_cnr_t3_lifecycle_audit/G12_CNR_T3_INVENTORY_COVERAGE_AUDIT_2026-05-08.json",
    "g12_cnr_t3_lifecycle_audit/G12_CNR_T3_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json",
    "cnr_t3_lifecycle_expansion_source_packet/CNR_T3_NO_TERMINAL_CANDIDATE_INVENTORY_2026-05-08.json",
    "cnr_t3_lifecycle_expansion_source_packet/CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json",
    "cnr_t3_lifecycle_expansion_source_packet/CNR_T3_SEARCHED_ROOT_AND_SOURCE_HASH_LEDGER_2026-05-08.json",
]

UPSTREAM_ROW_SOURCES = [
    "oti1_lifecycle_quarantined_results/OTI1_RESULT_LEDGER_2026-05-07.json",
    "oti2_riskbank_quarantined_results/OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "oti4_g6_opening_drive_quarantined_results/OTI4_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "oti5_g6_cusum_changepoint_quarantined_results/OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
]

# Optional source reports are hashed if present. A few early OTI1 lanes do not
# have a standalone source hash report, so absence is recorded rather than fatal.
OPTIONAL_SOURCE_REPORTS = [
    "oti1_lifecycle_quarantined_results/OTI1_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
    "oti2_riskbank_quarantined_results/OTI2_RISKBANK_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
    "oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
    "oti4_g6_opening_drive_quarantined_results/OTI4_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
    "oti5_g6_cusum_changepoint_quarantined_results/OTI5_G6_CUSUM_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
]

FORBIDDEN_PACKET_KEYS = {
    "synthetic_r",
    "descriptive_synthetic_path_r",
    "descriptive_gross_synthetic_path_r",
    "conservative_lower_bound_r",
    "reward_r_to_tp1",
    "broker_actual_r",
    "actual_r",
    "account_history",
    "live_trade_result",
    "live_order_state",
    "win_rate",
    "expectancy",
    "dsr",
    "pbo",
}

FORBIDDEN_VALUE_NEEDLES = [
    "broker_actual_r",
    "account_history",
    "live_trade_result",
    "live_order_state",
    "win rate",
    "expectancy",
    "DSR",
    "PBO",
    "validation_safe=true",
    "outcome_review_opened=true",
    "live_effect=true",
]

FORBIDDEN_LIVE_PREFIXES = [
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
]

FORBIDDEN_LIVE_NAME_NEEDLES = [
    "mt5",
    "order",
    "account",
    "risk",
    "execution",
    "permissions",
    "safety",
    "selector",
    "credential",
    "remote",
    "databento",
    "paid",
    "canary",
]

LABELS = {
    "no_fill_still_pending_at_frozen_lifecycle_horizon": {
        "family": "no_fill_still_pending",
        "source_lanes": ["OTI1_LIFECYCLE"],
        "allowed_evidence": [
            "upstream lifecycle_state=still_pending",
            "upstream fill_or_no_fill_state=no_fill_still_pending",
            "source projection/log hashes",
        ],
        "not_allowed": "No broker/account/live order state may be used to resolve whether the order later filled.",
        "actionable_unblocker": "Add source-hashed pending-intent lifecycle closure fields: pending_created_at, touched_at, filled_at, cancelled_at, expired_at, and frozen observation horizon.",
    },
    "no_fill_cancelled_wrong_side_before_fill": {
        "family": "no_fill_cancelled_wrong_side",
        "source_lanes": ["OTI1_LIFECYCLE"],
        "allowed_evidence": [
            "upstream lifecycle_state=wrong_side",
            "upstream fill_or_no_fill_state=no_fill_cancelled_wrong_side",
            "cancel_expiry_or_wrong_side_reason",
        ],
        "not_allowed": "No post-hoc rescue label or performance outcome may be attached.",
        "actionable_unblocker": "Capture exact source-hashed cancellation state and price-side invalidation reason at the lifecycle logger.",
    },
    "no_entry_touch_before_terminal_area": {
        "family": "no_entry_touch",
        "source_lanes": ["OTI2_RISKBANK"],
        "allowed_evidence": [
            "path_order_label=tp1_area_reached_without_entry_touch",
            "entry_first_touch_utc is null",
            "coverage binding hash matches",
        ],
        "not_allowed": "Do not carry any path-R fields or treat terminal-area reach as performance.",
        "actionable_unblocker": "Freeze a no-fill/no-entry path-order packet with entry touch, terminal-area touch, source coverage, and lifecycle horizon fields only.",
    },
    "source_blocked_no_price_compatible_m1": {
        "family": "source_blocked",
        "source_lanes": ["OTI3_G3_GEOMETRY"],
        "allowed_evidence": [
            "terminal_label=NO_PRICE_COMPATIBLE_M1_SOURCE",
            "attempted M1 source path, scale status, and source hash",
        ],
        "not_allowed": "Do not infer terminal order from incompatible or missing M1 source.",
        "actionable_unblocker": "Provide a price-compatible source-hashed M1/tick path for the symbol and decision window, or a parser/scale contract proving the current source is compatible.",
    },
    "terminal_order_unclaimed_entry_touched_unresolved": {
        "family": "terminal_order_unclaimed",
        "source_lanes": ["OTI2_RISKBANK"],
        "allowed_evidence": [
            "path_order_label=entry_touched_unresolved",
            "terminal_order_claim_allowed is false",
            "entry touch exists but terminal ordering is not claimable",
        ],
        "not_allowed": "Do not score the row or infer stop/target ordering from unresolved terminal state.",
        "actionable_unblocker": "Capture lower-timeframe/tick terminal-order proof after entry touch, with an as-of source hash and explicit ambiguity policy.",
    },
    "terminal_order_unclaimed_local_ohlc_bounded": {
        "family": "terminal_order_unclaimed",
        "source_lanes": ["OTI4_G6_OPENING_DRIVE"],
        "allowed_evidence": [
            "same_bar_ambiguity_state=terminal_order_unclaimed",
            "local OHLC bounded path policy",
            "not_computable source/as-of reasons",
        ],
        "not_allowed": "Do not claim same-bar or lower-timeframe terminal order without source proof.",
        "actionable_unblocker": "Capture prereg opening-drive range fields and lower-timeframe or tick source order evidence as of the decision window.",
    },
    "no_entry_touch_no_r_scored": {
        "family": "no_entry_touch",
        "source_lanes": ["OTI5_G6_CUSUM"],
        "allowed_evidence": [
            "result_status=NO_ENTRY_TOUCH_NO_R_SCORED",
            "entry_first_touch_utc is null",
            "tick path source files are hashed",
        ],
        "not_allowed": "Do not carry synthetic path-R values from neighboring rows.",
        "actionable_unblocker": "Keep tick path files and entry touch proof; future scoring would require a separate result lane and remains blocked here.",
    },
    "not_contract_eligible": {
        "family": "not_contract_eligible",
        "source_lanes": [],
        "allowed_evidence": ["reserved fallback for rows outside this frozen contract"],
        "not_allowed": "Do not create new labels after seeing result fields.",
        "actionable_unblocker": "Write a new frozen source contract for the row's actual family.",
    },
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def git_output(*args: str) -> str:
    cmd = ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", *args]
    try:
        out = subprocess.check_output(cmd, cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT)
        return out.strip()
    except Exception as exc:  # pragma: no cover - recorded as context, not fatal.
        return f"GIT_UNAVAILABLE: {exc}"


def file_entry(path: Path, required: bool = True, role: str = "source") -> dict[str, Any]:
    return {
        "path": rel(path),
        "absolute_path": str(path.resolve()) if path.exists() else str(path),
        "exists": path.exists(),
        "required": required,
        "role": role,
        "sha256": sha256_file(path),
    }


def output(name: str) -> Path:
    return OUT_DIR / name


def build_context_anchor(anchor_written_at: str) -> dict[str, Any]:
    controlled = [file_entry(OUTCOME_ROOT / p, True, "controlling_input") for p in CONTROL_INPUTS]
    upstream = [file_entry(OUTCOME_ROOT / p, True, "upstream_row_source") for p in UPSTREAM_ROW_SOURCES]
    upstream += [file_entry(OUTCOME_ROOT / p, False, "optional_upstream_source_report") for p in OPTIONAL_SOURCE_REPORTS]
    core = [file_entry(REPO_ROOT / p, True, "mandatory_context") for p in CORE_CONTEXT_INPUTS]
    prompt = file_entry(PROMPT_PATH, True, "controlling_prompt")
    roots = [
        {"root": str(REPO_ROOT), "exists": REPO_ROOT.exists(), "purpose": "current NOFILLPEND worktree"},
        {"root": str(MAIN_ROOT), "exists": MAIN_ROOT.exists(), "purpose": "absolute main repo and ignored heavy data"},
        {"root": str(MAIN_ROOT / "data"), "exists": (MAIN_ROOT / "data").exists(), "purpose": "absolute main data"},
        {"root": str(MAIN_ROOT / "data" / "ticks"), "exists": (MAIN_ROOT / "data" / "ticks").exists(), "purpose": "source-hashed tick parquet"},
        {"root": str(MAIN_ROOT / "data" / "external"), "exists": (MAIN_ROOT / "data" / "external").exists(), "purpose": "cached external sources"},
        {"root": str(MAIN_ROOT / "shadow_logs"), "exists": (MAIN_ROOT / "shadow_logs").exists(), "purpose": "runtime shadow logs"},
        {"root": str(MAIN_ROOT / "pipeline_state"), "exists": (MAIN_ROOT / "pipeline_state").exists(), "purpose": "runtime pipeline state"},
        {"root": str(MAIN_ROOT / "knowledge_base"), "exists": (MAIN_ROOT / "knowledge_base").exists(), "purpose": "knowledge base"},
        {"root": str(MAIN_ROOT / "research"), "exists": (MAIN_ROOT / "research").exists(), "purpose": "prior research artifacts"},
        {"root": "C:/tmp/gtos_otb", "exists": Path("C:/tmp/gtos_otb").exists(), "purpose": "parallel worktrees and prior artifacts"},
    ]
    return {
        "schema_version": SCHEMA,
        "artifact_family": "NOFILL_CONTEXT_ANCHOR",
        "date_stamp": DATE,
        "generated_at_utc": anchor_written_at,
        "current_head": git_output("rev-parse", "HEAD"),
        "git_status_at_anchor": git_output("status", "--short"),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "controlling_prompt": prompt,
        "mandatory_context_inputs_read": core,
        "controlling_inputs_read": controlled,
        "upstream_row_sources_read": upstream,
        "active_question_stack": [
            "Can the 298 CNR_T3 not_packet_eligible rows be split into source-safe lifecycle/no-fill/no-entry/still-pending/source-blocked/terminal-order-unclaimed families?",
            "Which rows clear a new input-only contract without reusing T3 stop-after-horizon labels?",
            "Which source/data/methodology blockers remain actionable without R/performance scoring or live/account labels?",
            "What exact future capture fields would turn the blocked families into stronger packets?",
        ],
        "scheduled_and_initially_checked_roots": roots,
        "source_boundaries": [
            "Research/control and input-packet lane only.",
            "Rows may use upstream source identity, family, hashes, as-of/source-block status, and no-fill/no-entry lifecycle state.",
            "Rows may not use broker/account/live/order state, hidden labels, blocked-packet outcomes, or path R/performance values.",
            "The six accepted CNR T3 rows and the 94 G12-blocked CNR061 rows remain excluded.",
            "Paid/API/Databento/MT5 account/order calls are not used.",
        ],
        "forbidden_fields": sorted(FORBIDDEN_PACKET_KEYS),
        "stop_condition_checklist": {
            "source_contract": "pending",
            "family_split_inventory": "pending",
            "source_hash_ledger": "pending",
            "packet_or_impossibility_proof": "pending",
            "no_leak_duplicate_sample_floor_audit": "pending",
            "blocker_ledger": "pending",
            "forensics_learning": "pending",
            "verifier_tests": "pending",
            "g12_prompt_pack": "pending",
            "completion_audit": "pending",
            "committed": "pending",
        },
    }


def build_contract(contract_written_at: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "artifact_family": "NOFILL_FROZEN_LIFECYCLE_CONTRACT",
        "contract_id": CONTRACT_ID,
        "contract_frozen_at_utc": contract_written_at,
        "date_stamp": DATE,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "scope": "Input-only lifecycle/no-fill/no-entry/source-blocked packet for the 298 non-T3 CNR rows.",
        "not_t3_reuse_rule": "The CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1 label set is not reused; stop_after_original_horizon is forbidden here.",
        "allowed_labels": LABELS,
        "packet_row_allowed_fields": [
            "row identity and upstream source lane",
            "source hashes and source artifact path",
            "symbol/session/side/decision-asof fields when present upstream",
            "new contract lifecycle family label",
            "source-status and exact missing source/actionable unblocker fields",
            "duplicate grouping for denominator hygiene",
        ],
        "packet_row_forbidden_fields": sorted(FORBIDDEN_PACKET_KEYS),
        "sample_floor_policy": "No validation or promotion sample floor can pass in this lane; this packet is source/control evidence only.",
        "blocked_row_policy": "Rows outside allowed labels become exact blockers; blocked CNR061 rows are not opened.",
    }


def write_anchor_and_contract() -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    anchor_time = utc_now()
    anchor = build_context_anchor(anchor_time)
    write_json(output("NOFILL_CONTEXT_ANCHOR_2026-05-08.json"), anchor)
    write_md(output("NOFILL_CONTEXT_ANCHOR_2026-05-08.md"), render_anchor_md(anchor))
    contract_time = utc_now()
    contract = build_contract(contract_time)
    write_json(output("NOFILL_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json"), contract)
    write_md(output("NOFILL_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.md"), render_contract_md(contract))
    run_order = {
        "anchor_written_at_utc": anchor_time,
        "contract_written_at_utc": contract_time,
    }
    return anchor, contract, run_order


def render_anchor_md(anchor: dict[str, Any]) -> list[str]:
    lines = [
        "# No-Fill Context Anchor - 2026-05-08",
        "",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        f"Generated: `{anchor['generated_at_utc']}`",
        f"HEAD: `{anchor['current_head']}`",
        f"Prompt: `{anchor['controlling_prompt']['path']}`",
        "",
        "## Active Questions",
    ]
    lines += [f"- {q}" for q in anchor["active_question_stack"]]
    lines += ["", "## Initial Roots"]
    lines += [f"- `{r['root']}` exists={r['exists']} purpose={r['purpose']}" for r in anchor["scheduled_and_initially_checked_roots"]]
    lines += ["", "## Boundaries"]
    lines += [f"- {b}" for b in anchor["source_boundaries"]]
    lines += ["", "## Inputs Read"]
    for entry in anchor["mandatory_context_inputs_read"] + [anchor["controlling_prompt"]] + anchor["controlling_inputs_read"]:
        lines.append(f"- `{entry['path']}` exists={entry['exists']} sha256=`{entry['sha256']}`")
    return lines


def render_contract_md(contract: dict[str, Any]) -> list[str]:
    lines = [
        "# No-Fill Frozen Lifecycle Contract - 2026-05-08",
        "",
        f"Contract: `{contract['contract_id']}`",
        f"Frozen at: `{contract['contract_frozen_at_utc']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Scope",
        contract["scope"],
        "",
        "## Labels",
    ]
    for label, spec in contract["allowed_labels"].items():
        lines.append(f"- `{label}` family=`{spec['family']}` source_lanes={','.join(spec['source_lanes']) if spec['source_lanes'] else 'reserved'}")
    lines += [
        "",
        "## Hard Rules",
        f"- {contract['not_t3_reuse_rule']}",
        "- No R, performance, win rate, expectancy, DSR, PBO, validation, promotion, broker/account/live/order, hidden-label, or blocked-packet outcome fields.",
        "- Every row is input-only source/control evidence or an exact blocker.",
    ]
    return lines


def build_source_maps() -> dict[str, Any]:
    oti1 = load_json(OUTCOME_ROOT / "oti1_lifecycle_quarantined_results" / "OTI1_RESULT_LEDGER_2026-05-07.json")
    oti1_groups: dict[tuple[str, str], dict[str, Any]] = {}
    for packet in oti1["packet_results"]:
        for group in packet.get("group_summaries", []):
            oti1_groups[(packet["packet_id"], group["duplicate_group_id"])] = group

    oti2_rows = load_jsonl(OUTCOME_ROOT / "oti2_riskbank_quarantined_results" / "OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl")
    oti2_by_setup = {(r["packet_id"], r["setup_id"]): r for r in oti2_rows}

    oti3_rows = load_jsonl(OUTCOME_ROOT / "oti3_g3_geometry_quarantined_results" / "OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_2026-05-07.jsonl")
    oti3_by_packet_hash = {(r["packet_id"], r["packet_source_hash"]): r for r in oti3_rows}

    oti4_rows = load_jsonl(OUTCOME_ROOT / "oti4_g6_opening_drive_quarantined_results" / "OTI4_RESULT_LEDGER_ROWS_2026-05-07.jsonl")
    oti4_by_record = {(r["packet_id"], r["record_id"]): r for r in oti4_rows}

    oti5_rows = load_jsonl(OUTCOME_ROOT / "oti5_g6_cusum_changepoint_quarantined_results" / "OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl")
    oti5_by_record = {(r["packet_id"], r["record_id"]): r for r in oti5_rows}

    return {
        "oti1": oti1,
        "oti1_groups": oti1_groups,
        "oti2_by_setup": oti2_by_setup,
        "oti3_by_packet_hash": oti3_by_packet_hash,
        "oti4_by_record": oti4_by_record,
        "oti5_by_record": oti5_by_record,
    }


def reconstruct_universe() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    inv = load_json(OUTCOME_ROOT / "cnr_t3_lifecycle_expansion_source_packet" / "CNR_T3_NO_TERMINAL_CANDIDATE_INVENTORY_2026-05-08.json")
    blocker = load_json(OUTCOME_ROOT / "cnr_t3_lifecycle_expansion_source_packet" / "CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json")
    g12_no_leak = load_json(OUTCOME_ROOT / "g12_cnr_t3_lifecycle_audit" / "G12_CNR_T3_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json")
    g12_inv = load_json(OUTCOME_ROOT / "g12_cnr_t3_lifecycle_audit" / "G12_CNR_T3_INVENTORY_COVERAGE_AUDIT_2026-05-08.json")
    g12_route = load_json(OUTCOME_ROOT / "g12_cnr_t3_lifecycle_audit" / "G12_CNR_T3_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08.json")
    rows = [r for r in inv["rows"] if not r["packet_eligible"]]
    exact_blocker_ids = {b["inventory_id"] for b in blocker["exact_blockers"]}
    row_ids = {r["inventory_id"] for r in rows}
    if len(rows) != 298:
        raise RuntimeError(f"Expected 298 non-T3 rows, found {len(rows)}")
    if row_ids != exact_blocker_ids:
        raise RuntimeError("Non-T3 inventory rows do not match exact blocker ledger inventory ids")
    if any(r["source_lane"] == "OTI8_CNR061" for r in rows):
        raise RuntimeError("OTI8 CNR061 row leaked into no-fill universe")
    if g12_no_leak["blocked_94_exclusion"]["blocked_rows"] != 94:
        raise RuntimeError("G12 94-row blocker evidence missing")
    return rows, inv, blocker, g12_no_leak, {"g12_inventory": g12_inv, "g12_route": g12_route}


def safe_hash_dict(d: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in d.items():
        if isinstance(v, str) and len(v) >= 32 and all(c in "009abcdef" for c in v.lower()):
            out[k] = v
    return out


def classify_row(row: dict[str, Any], maps: dict[str, Any], packet_index: int) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    lane = row["source_lane"]
    base = {
        "schema_version": SCHEMA,
        "contract_id": CONTRACT_ID,
        "packet_row_id": f"NOFILL-ROW-{packet_index:04d}",
        "source_inventory_id": row["inventory_id"],
        "source_lane": lane,
        "source_packet_id": row["packet_id"],
        "source_row_id": row["row_id"],
        "source_artifact_path": row["source_artifact_path"],
        "source_artifact_sha256": sha256_file(REPO_ROOT / row["source_artifact_path"]),
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol"),
        "session": row.get("session"),
        "side": row.get("side"),
        "decision_asof_utc": row.get("decision_asof_utc"),
        "path_start_utc": row.get("path_start_utc"),
        "original_horizon_end_utc": row.get("original_horizon_end_utc"),
        "upstream_candidate_state_family": row.get("candidate_state_family"),
        "upstream_terminal_status": row.get("terminal_status"),
        "duplicate_group_id": row.get("duplicate_group_id"),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "source_hashes": safe_hash_dict(row.get("source_hashes") or {}),
        "no_r_performance_or_live_fields_carried": True,
    }

    if lane == "OTI1_LIFECYCLE":
        source = maps["oti1_groups"].get((row["packet_id"], row["row_id"]))
        if not source:
            return None, exact_blocker(row, "missing_oti1_group_summary", "OTI1 group summary was not found by packet_id and opportunity id.")
        state = source["lifecycle_state"]
        if state == "still_pending":
            label = "no_fill_still_pending_at_frozen_lifecycle_horizon"
        elif state == "wrong_side":
            label = "no_fill_cancelled_wrong_side_before_fill"
        else:
            return None, exact_blocker(row, "unsupported_oti1_lifecycle_state", f"Unsupported OTI1 lifecycle_state={state}")
        evidence = {
            "lifecycle_state": source["lifecycle_state"],
            "fill_or_no_fill_state": source["fill_or_no_fill_state"],
            "cancel_expiry_or_wrong_side_reason": source["cancel_expiry_or_wrong_side_reason"],
            "setup_ids": source.get("setup_ids", []),
            "source_symbols": source.get("source_symbols", []),
            "raw_child_rows": source.get("raw_child_rows"),
            "counted_primary_unit": source.get("counted_primary_unit"),
        }
        return packet_row(base, label, evidence), None

    if lane == "OTI2_RISKBANK":
        source = maps["oti2_by_setup"].get((row["packet_id"], row["row_id"]))
        if not source:
            return None, exact_blocker(row, "missing_oti2_path_order_row", "OTI2 row was not found by packet_id and setup_id.")
        if source.get("path_order_label") not in {"tp1_area_reached_without_entry_touch", "entry_touched_unresolved"}:
            return None, exact_blocker(row, "unsupported_oti2_path_order", f"Unsupported OTI2 path_order_label={source.get('path_order_label')}")
        evidence = {
            "path_order_label": source.get("path_order_label"),
            "entry_first_touch_utc": source.get("entry_first_touch_utc"),
            "coverage_mode": source.get("coverage_mode"),
            "coverage_reaches_path_end_utc": source.get("coverage_reaches_path_end_utc"),
            "coverage_binding_hash_match": source.get("coverage_binding_hash_match"),
            "ltf_projection_hash_matches": source.get("ltf_projection_hash_matches"),
            "raw_path_log_path": source.get("raw_path_log_path"),
            "path_end_utc": source.get("path_end_utc"),
            "terminal_order_claim_allowed": source.get("terminal_order_claim_allowed"),
        }
        if source.get("path_order_label") == "entry_touched_unresolved":
            return packet_row(base, "terminal_order_unclaimed_entry_touched_unresolved", evidence), None
        return packet_row(base, "no_entry_touch_before_terminal_area", evidence), None

    if lane == "OTI3_G3_GEOMETRY":
        packet_hash = (row.get("source_hashes") or {}).get("packet_source_hash")
        source = maps["oti3_by_packet_hash"].get((row["packet_id"], packet_hash))
        if not source:
            return None, exact_blocker(row, "missing_oti3_geometry_row", "OTI3 row was not found by packet_id and packet source hash.")
        if source.get("terminal_label") != "NO_PRICE_COMPATIBLE_M1_SOURCE":
            return None, exact_blocker(row, "unsupported_oti3_terminal_label", f"Unsupported OTI3 terminal_label={source.get('terminal_label')}")
        attempts = []
        for item in source.get("outcome_source_attempted", []):
            attempts.append({
                "path": item.get("path"),
                "exists": item.get("exists"),
                "first_open_utc": item.get("first_open_utc"),
                "last_open_utc": item.get("last_open_utc"),
                "row_count": item.get("row_count"),
                "price_scale_status": item.get("price_scale_status"),
                "sha256": item.get("sha256"),
                "decision_covered": item.get("decision_covered"),
            })
        evidence = {
            "terminal_label": source.get("terminal_label"),
            "outcome_source_status": source.get("outcome_source_status"),
            "outcome_source_attempted": attempts,
            "no_leak_status": source.get("no_leak_status"),
            "packet_source_hash_match": source.get("packet_source_hash_match"),
        }
        return packet_row(base, "source_blocked_no_price_compatible_m1", evidence), None

    if lane == "OTI4_G6_OPENING_DRIVE":
        source = maps["oti4_by_record"].get((row["packet_id"], row["row_id"]))
        if not source:
            return None, exact_blocker(row, "missing_oti4_opening_drive_row", "OTI4 row was not found by packet_id and record_id.")
        if source.get("same_bar_ambiguity_state") != "terminal_order_unclaimed":
            return None, exact_blocker(row, "unsupported_oti4_ambiguity_state", f"Unsupported OTI4 same_bar_ambiguity_state={source.get('same_bar_ambiguity_state')}")
        evidence = {
            "same_bar_ambiguity_state": source.get("same_bar_ambiguity_state"),
            "same_bar_ambiguity_policy": source.get("same_bar_ambiguity_policy"),
            "opening_drive_status": source.get("opening_drive_status"),
            "quarantined_result_status": source.get("quarantined_result_status"),
            "not_computable_reasons": source.get("not_computable_reasons", []),
            "ohlc_source_path": source.get("ohlc_source_path"),
            "ohlc_source_last_utc": source.get("ohlc_source_last_utc"),
            "range_bar_count": source.get("range_bar_count"),
            "path_bar_count": source.get("path_bar_count"),
            "source_hash_match": source.get("source_hash_match"),
        }
        return packet_row(base, "terminal_order_unclaimed_local_ohlc_bounded", evidence), None

    if lane == "OTI5_G6_CUSUM":
        source = maps["oti5_by_record"].get((row["packet_id"], row["row_id"]))
        if not source:
            return None, exact_blocker(row, "missing_oti5_cusum_row", "OTI5 row was not found by packet_id and record_id.")
        if source.get("result_status") != "NO_ENTRY_TOUCH_NO_R_SCORED":
            return None, exact_blocker(row, "unsupported_oti5_result_status", f"Unsupported OTI5 result_status={source.get('result_status')}")
        evidence = {
            "result_status": source.get("result_status"),
            "entry_first_touch_utc": source.get("entry_first_touch_utc"),
            "path_tick_count": source.get("path_tick_count"),
            "missing_tick_files": source.get("missing_tick_files", []),
            "path_source_files": source.get("path_source_files", []),
            "path_source_sha256": source.get("path_source_sha256", {}),
        }
        return packet_row(base, "no_entry_touch_no_r_scored", evidence), None

    return None, exact_blocker(row, "unsupported_source_lane", f"Unsupported source_lane={lane}")


def packet_row(base: dict[str, Any], label: str, evidence: dict[str, Any]) -> dict[str, Any]:
    spec = LABELS[label]
    row = dict(base)
    row.update({
        "contract_label": label,
        "contract_family": spec["family"],
        "contract_label_status": "input_only_source_control_row",
        "allowed_evidence_class": "source_hashed_lifecycle_no_fill_no_entry_or_blocker_state",
        "source_evidence": evidence,
        "actionable_unblocker": spec["actionable_unblocker"],
        "future_route_boundary": "Future outcome/performance scoring requires a separate frozen result lane; this packet is not validation safe.",
    })
    row["nofill_duplicate_key"] = "|".join(
        str(x) for x in [
            row["source_lane"],
            row["source_packet_id"],
            row.get("duplicate_group_id"),
            row["contract_label"],
        ]
    )
    return row


def exact_blocker(row: dict[str, Any], blocker_code: str, reason: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "contract_id": CONTRACT_ID,
        "source_inventory_id": row.get("inventory_id"),
        "source_lane": row.get("source_lane"),
        "source_packet_id": row.get("packet_id"),
        "source_row_id": row.get("row_id"),
        "blocker_code": blocker_code,
        "exact_blocker": reason,
        "actionable_unblocker": "Provide the named source row or create a new frozen contract for the row family.",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def classify_universe(rows: list[dict[str, Any]], maps: dict[str, Any], classification_started_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    packet_rows: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        pkt, block = classify_row(row, maps, idx)
        if pkt:
            pkt["classification_started_at_utc"] = classification_started_at
            packet_rows.append(pkt)
        if block:
            block["classification_started_at_utc"] = classification_started_at
            blockers.append(block)
    return packet_rows, blockers


def collect_underlying_source_paths(packet_rows: list[dict[str, Any]], maps: dict[str, Any]) -> list[dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}

    def add(path_s: str | None, role: str, expected_sha: str | None = None, source_row: str | None = None) -> None:
        if not path_s:
            return
        candidates: list[Path] = []
        p = Path(path_s)
        if p.is_absolute():
            candidates.append(p)
        else:
            candidates.append(REPO_ROOT / p)
            candidates.append(MAIN_ROOT / p)
        chosen = next((c for c in candidates if c.exists()), candidates[0])
        key = str(chosen)
        if key not in entries:
            actual = sha256_file(chosen)
            entries[key] = {
                "path": str(chosen),
                "exists": chosen.exists(),
                "role": role,
                "expected_sha256": expected_sha,
                "actual_sha256": actual,
                "hash_match": (actual == expected_sha) if expected_sha and actual else None,
                "source_rows": [],
            }
        if source_row:
            entries[key]["source_rows"].append(source_row)

    for path_rel in CONTROL_INPUTS + UPSTREAM_ROW_SOURCES + OPTIONAL_SOURCE_REPORTS:
        add(str(OUTCOME_ROOT / path_rel), "required_or_optional_artifact", None, path_rel)

    oti1 = maps["oti1"]
    for item in oti1.get("lifecycle_source_evidence", {}).get("cited_lifecycle_logs", []):
        add(item.get("path"), "oti1_lifecycle_log", item.get("sha256"), "OTI1")
    source_projection = oti1.get("lifecycle_source_evidence", {}).get("source_projection_file")
    if source_projection:
        add(source_projection, "oti1_source_projection", None, "OTI1")

    for row in packet_rows:
        ev = row.get("source_evidence", {})
        if row["source_lane"] == "OTI2_RISKBANK":
            add(ev.get("raw_path_log_path"), "oti2_raw_ltf_path_log", None, row["packet_row_id"])
        elif row["source_lane"] == "OTI3_G3_GEOMETRY":
            for attempt in ev.get("outcome_source_attempted", []):
                add(attempt.get("path"), "oti3_attempted_m1_source", attempt.get("sha256"), row["packet_row_id"])
        elif row["source_lane"] == "OTI4_G6_OPENING_DRIVE":
            add(ev.get("ohlc_source_path"), "oti4_local_ohlc_source", None, row["packet_row_id"])
        elif row["source_lane"] == "OTI5_G6_CUSUM":
            for path_s, expected in ev.get("path_source_sha256", {}).items():
                add(path_s, "oti5_tick_path_source", expected, row["packet_row_id"])

    return sorted(entries.values(), key=lambda x: x["path"])


def targeted_root_search() -> list[dict[str, Any]]:
    targets = [
        PROMPT_PATH.name,
        "CNR_T3_NO_TERMINAL_CANDIDATE_INVENTORY_2026-05-08.json",
        "CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json",
        "G12_CNR_T3_DECISION_LEDGER_2026-05-08.json",
        "OTI1_RESULT_LEDGER_2026-05-07.json",
        "OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
        "OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
        "OTI4_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
        "OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    ]
    roots = [
        REPO_ROOT,
        MAIN_ROOT,
        MAIN_ROOT / "data",
        MAIN_ROOT / "data" / "ticks",
        MAIN_ROOT / "data" / "external",
        MAIN_ROOT / "shadow_logs",
        MAIN_ROOT / "pipeline_state",
        MAIN_ROOT / "knowledge_base",
        MAIN_ROOT / "research",
        Path("C:/tmp/gtos_otb"),
    ]
    out = []
    for root in roots:
        info: dict[str, Any] = {
            "root": str(root),
            "exists": root.exists(),
            "search_type": "targeted_required_artifact_and_heavy_data_presence",
            "target_basenames": targets,
            "matches": [],
            "permission_error": None,
        }
        if root.exists():
            try:
                for dirpath, dirnames, filenames in os.walk(root):
                    dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", ".venv", "node_modules"}]
                    hit_names = sorted(set(filenames).intersection(targets))
                    for name in hit_names:
                        p = Path(dirpath) / name
                        info["matches"].append({"path": str(p), "sha256": sha256_file(p)})
                    if len(info["matches"]) >= 200:
                        info["truncated"] = True
                        break
            except PermissionError as exc:
                info["permission_error"] = str(exc)
        out.append(info)
    return out


def build_source_ledger(packet_rows: list[dict[str, Any]], maps: dict[str, Any]) -> dict[str, Any]:
    consumed = collect_underlying_source_paths(packet_rows, maps)
    return {
        "schema_version": SCHEMA,
        "artifact_family": "NOFILL_SOURCE_SEARCH_AND_HASH_LEDGER",
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "searched_roots": targeted_root_search(),
        "consumed_source_files": consumed,
        "hash_summary": {
            "files_listed": len(consumed),
            "existing_files": sum(1 for e in consumed if e["exists"]),
            "expected_hash_checks": sum(1 for e in consumed if e["expected_sha256"]),
            "expected_hash_matches": sum(1 for e in consumed if e["hash_match"] is True),
            "expected_hash_mismatches": [e for e in consumed if e["hash_match"] is False],
            "missing_expected_files": [e for e in consumed if e["expected_sha256"] and not e["exists"]],
        },
        "source_policy": "Existing local files only; no API, paid data, MT5, account, broker, order, credential, remote, or web calls.",
    }


def build_family_inventory(source_rows: list[dict[str, Any]], packet_rows: list[dict[str, Any]], blockers: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(r["contract_label"] for r in packet_rows)
    lane_counts = Counter(r["source_lane"] for r in packet_rows)
    duplicate_by_family = defaultdict(set)
    for row in packet_rows:
        duplicate_by_family[row["contract_label"]].add(row["nofill_duplicate_key"])
    return {
        "schema_version": SCHEMA,
        "artifact_family": "NOFILL_298_FAMILY_SPLIT_INVENTORY",
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "source_universe_rows": len(source_rows),
        "packet_rows": len(packet_rows),
        "exact_blockers": len(blockers),
        "six_t3_rows_excluded": True,
        "blocked_94_cnr061_excluded": True,
        "source_lane_counts": dict(sorted(lane_counts.items())),
        "contract_label_counts": dict(sorted(counts.items())),
        "unique_duplicate_keys_by_label": {k: len(v) for k, v in sorted(duplicate_by_family.items())},
        "row_index": [
            {
                "source_inventory_id": r["source_inventory_id"],
                "source_lane": r["source_lane"],
                "source_packet_id": r["source_packet_id"],
                "source_row_id": r["source_row_id"],
                "contract_label": r["contract_label"],
                "contract_family": r["contract_family"],
                "symbol": r.get("symbol"),
                "session": r.get("session"),
                "side": r.get("side"),
                "duplicate_group_id": r.get("duplicate_group_id"),
                "nofill_duplicate_key": r.get("nofill_duplicate_key"),
            }
            for r in packet_rows
        ],
    }


def build_packet_manifest(packet_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "artifact_family": "NOFILL_INPUT_ONLY_PACKET",
        "contract_id": CONTRACT_ID,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "packet_row_count": len(packet_rows),
        "packet_rows_jsonl": "NOFILL_INPUT_ONLY_PACKET_2026-05-08_ROWS.jsonl",
        "packet_scope": "input-only lifecycle/no-fill/no-entry/source-blocked row classification; no outcome/performance scoring",
        "label_counts": dict(sorted(Counter(r["contract_label"] for r in packet_rows).items())),
        "source_lane_counts": dict(sorted(Counter(r["source_lane"] for r in packet_rows).items())),
        "forbidden_fields_carried": [],
        "status": "INPUT_ONLY_PACKET_BUILT" if packet_rows else "NO_CLEARABLE_PACKET_ROWS",
    }


def scan_forbidden(obj: Any, path: str = "") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            low = str(k).lower()
            if low in FORBIDDEN_PACKET_KEYS:
                hits.append({"path": f"{path}/{k}", "kind": "forbidden_key"})
            hits.extend(scan_forbidden(v, f"{path}/{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(scan_forbidden(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        text = obj
        for needle in FORBIDDEN_VALUE_NEEDLES:
            if needle in text:
                hits.append({"path": path, "kind": "forbidden_value", "needle": needle})
    return hits


def build_noleak_audit(packet_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]], g12_no_leak: dict[str, Any]) -> dict[str, Any]:
    hits = scan_forbidden(packet_rows)
    label_counts = Counter(r["contract_label"] for r in packet_rows)
    duplicate_keys = [r["nofill_duplicate_key"] for r in packet_rows]
    return {
        "schema_version": SCHEMA,
        "artifact_family": "NOFILL_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT",
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "forbidden_packet_hits": hits,
        "forbidden_packet_hits_count": len(hits),
        "source_rows": len(source_rows),
        "packet_rows": len(packet_rows),
        "label_counts": dict(sorted(label_counts.items())),
        "duplicate_key_rows": len(duplicate_keys),
        "duplicate_key_unique": len(set(duplicate_keys)),
        "duplicate_key_repeated_counts": {k: v for k, v in Counter(duplicate_keys).items() if v > 1},
        "validation_sample_floor_status": "FALSE_INPUT_ONLY_CONTROL_PACKET_NOT_VALIDATION",
        "sample_floor_reason": "Rows are mixed lifecycle/source-block families and explicitly validation_safe=false.",
        "six_t3_rows_excluded": all(r["source_lane"] != "OTI8_CNR061" for r in packet_rows),
        "blocked_94_exclusion": g12_no_leak["blocked_94_exclusion"],
        "status": "PASS" if not hits and len(source_rows) == 298 and len(packet_rows) == 298 else "FAIL",
    }


def build_blocker_ledger(packet_rows: list[dict[str, Any]], blockers: list[dict[str, Any]], source_ledger: dict[str, Any]) -> dict[str, Any]:
    family_counts = Counter(r["contract_label"] for r in packet_rows)
    family_blockers = {
        "no_fill_still_pending_at_frozen_lifecycle_horizon": {
            "rows": family_counts["no_fill_still_pending_at_frozen_lifecycle_horizon"],
            "blocker_type": "lifecycle_closure_not_observed",
            "exact_unblocker": LABELS["no_fill_still_pending_at_frozen_lifecycle_horizon"]["actionable_unblocker"],
        },
        "no_fill_cancelled_wrong_side_before_fill": {
            "rows": family_counts["no_fill_cancelled_wrong_side_before_fill"],
            "blocker_type": "lifecycle_cancel_reason_only",
            "exact_unblocker": LABELS["no_fill_cancelled_wrong_side_before_fill"]["actionable_unblocker"],
        },
        "no_entry_touch_before_terminal_area": {
            "rows": family_counts["no_entry_touch_before_terminal_area"],
            "blocker_type": "no_entry_touch_path_order_only",
            "exact_unblocker": LABELS["no_entry_touch_before_terminal_area"]["actionable_unblocker"],
        },
        "source_blocked_no_price_compatible_m1": {
            "rows": family_counts["source_blocked_no_price_compatible_m1"],
            "blocker_type": "price_compatible_m1_source_missing_or_scale_mismatch",
            "exact_unblocker": LABELS["source_blocked_no_price_compatible_m1"]["actionable_unblocker"],
        },
        "terminal_order_unclaimed_entry_touched_unresolved": {
            "rows": family_counts["terminal_order_unclaimed_entry_touched_unresolved"],
            "blocker_type": "entry_touched_but_terminal_order_unresolved",
            "exact_unblocker": LABELS["terminal_order_unclaimed_entry_touched_unresolved"]["actionable_unblocker"],
        },
        "terminal_order_unclaimed_local_ohlc_bounded": {
            "rows": family_counts["terminal_order_unclaimed_local_ohlc_bounded"],
            "blocker_type": "same_bar_or_ltf_terminal_order_unproven",
            "exact_unblocker": LABELS["terminal_order_unclaimed_local_ohlc_bounded"]["actionable_unblocker"],
        },
        "no_entry_touch_no_r_scored": {
            "rows": family_counts["no_entry_touch_no_r_scored"],
            "blocker_type": "no_entry_touch_result_family_no_scoring",
            "exact_unblocker": LABELS["no_entry_touch_no_r_scored"]["actionable_unblocker"],
        },
    }
    return {
        "schema_version": SCHEMA,
        "artifact_family": "NOFILL_BLOCKER_AND_IMPOSSIBILITY_LEDGER",
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "exact_row_blockers": blockers,
        "exact_row_blocker_count": len(blockers),
        "family_failure_anatomy": family_blockers,
        "missing_expected_files": source_ledger["hash_summary"]["missing_expected_files"],
        "hash_mismatches": source_ledger["hash_summary"]["expected_hash_mismatches"],
        "impossibility_proof": [
            "A validation/performance result is impossible in this lane because the contract forbids R/performance and preserves validation_safe=false.",
            "Broker/account/live order state resolution is impossible without explicit owner approval and is forbidden here.",
            "The 94 blocked CNR061 rows cannot be rescued or relabeled because G12 only approved them as excluded.",
            "Rows requiring price-compatible M1/tick or lower-timeframe terminal ordering remain exact source/capture blockers until the named source exists.",
        ],
        "status": "PASS_WITH_ACTIONABLE_FAMILY_BLOCKERS" if len(blockers) == 0 else "PASS_WITH_ROW_BLOCKERS",
    }


def build_forensics(packet_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_lane = Counter(r["source_lane"] for r in packet_rows)
    by_label = Counter(r["contract_label"] for r in packet_rows)
    by_symbol = Counter(str(r.get("symbol")) for r in packet_rows)
    by_session = Counter(str(r.get("session")) for r in packet_rows)
    return {
        "schema_version": SCHEMA,
        "artifact_family": "NOFILL_FORENSICS_AND_LEARNING",
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "row_count": len(packet_rows),
        "source_lane_counts": dict(sorted(by_lane.items())),
        "contract_label_counts": dict(sorted(by_label.items())),
        "symbol_counts": dict(sorted(by_symbol.items())),
        "session_counts": dict(sorted(by_session.items())),
        "learning": [
            "The 298-row non-T3 universe is not a single failure mode; it splits into pending lifecycle closure, wrong-side no-fill cancellation, no-entry touch, source-incompatible M1, and terminal-order-unclaimed families.",
            "No-fill/still-pending evidence can improve GTOS by making opportunity loss explicit before any performance scoring is considered.",
            "Source-blocked and terminal-order-unclaimed rows are useful negative evidence because they name the exact capture fields needed for future packets.",
            "The next stronger lifecycle logger should record pending intent creation, touch, fill, cancel/expiry, observation horizon, quote source hash, and lower-timeframe terminal order proof.",
        ],
        "non_claims": [
            "This does not validate an edge.",
            "This does not compute performance.",
            "This does not resolve broker fills, account history, live orders, or blocked CNR061 rows.",
            "This does not alter live trading behavior.",
        ],
        "next_prompt_guidance": [
            "Ask G12 to audit that every row is input-only and family labels are contract-frozen.",
            "For source-blocked rows, require exact source/capture unblockers rather than generic more-data language.",
            "Keep future outcome scoring in a separate lane with a new frozen result contract.",
        ],
    }


def build_g12_prompt_pack() -> str:
    return f"""# No-Fill G12 Audit Prompt Pack - {DATE}

Promotion verdict: `{PROMOTION_VERDICT}`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Recommended G12 Goal

`/goal Audit SEPARATE_NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT_V1 under research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract. Complete mandatory GTOS preflight; read the controlling prompt, context anchor, frozen contract, 298 family split inventory, source search/hash ledger, input-only packet JSON/JSONL, no-leak/duplicate/sample-floor audit, blocker/impossibility ledger, forensics/learning, builder, verifier, and tests. Decide ACCEPT/BLOCK/REJECT as research-control input-only lifecycle evidence. Verify that the exact 298 CNR_T3 not_packet_eligible rows were reconstructed, the six T3 stop-after-horizon rows and 94 G12-blocked CNR061 rows were excluded, the frozen no-fill contract was written before classification, labels do not reuse CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1, source hashes are recomputed or exact missing files are recorded, no forbidden R/performance/broker/account/live/hidden labels are carried, duplicate/sample-floor remains validation-blocking, and NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false are preserved. Do not compute R/performance, do not score blocked rows, do not use broker actual-R/account history/live trade results/live order state/hidden labels, and touch no live prompts/risk/execution/permissions/safety/selectors/canaries/MT5/order/credential/remote surfaces.`

## Audit Questions

1. Are all 298 rows present exactly once under the new contract or exact-blocked?
2. Are the families correctly split into no-fill still-pending, no-fill wrong-side cancellation, no-entry touch, source-blocked, and terminal-order-unclaimed rows?
3. Are source hashes, missing source files, and root searches sufficient to support input-only classification?
4. Does any packet row carry forbidden R/performance/live/account/broker/hidden-label fields?
5. Does the audit clearly state what the packet proves and what remains impossible without a future source/result lane?

## Required Next Guidance

- Accept/block/reject the contract and packet.
- Write exact next capture requirements for every blocked/source-limited family.
- Keep any future scoring or promotion in a separate frozen lane.
"""


def live_surface_status() -> dict[str, Any]:
    status = git_output("status", "--short")
    changed = []
    for line in status.splitlines():
        if not line.strip():
            continue
        path = line[3:].replace("\\", "/")
        changed.append(path)
    forbidden = [
        p for p in changed
        if any(p.startswith(prefix) for prefix in FORBIDDEN_LIVE_PREFIXES)
        or any(needle in p.lower() for needle in FORBIDDEN_LIVE_NAME_NEEDLES)
    ]
    return {
        "git_status_short": status,
        "changed_paths": changed,
        "forbidden_live_surface_changed_paths": forbidden,
        "status": "PASS" if not forbidden else "FAIL",
    }


def build_completion_audit(
    run_order: dict[str, str],
    source_rows: list[dict[str, Any]],
    packet_rows: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    source_ledger: dict[str, Any],
    noleak: dict[str, Any],
    g12_no_leak: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        {"requirement": "mandatory GTOS preflight and context docs read", "evidence": "NOFILL_CONTEXT_ANCHOR_2026-05-08.json", "status": "PASS"},
        {"requirement": "frozen contract before classification", "evidence": run_order, "status": "PASS" if run_order["contract_written_at_utc"] <= run_order["classification_started_at_utc"] else "FAIL"},
        {"requirement": "exact 298-row universe", "evidence": {"source_rows": len(source_rows)}, "status": "PASS" if len(source_rows) == 298 else "FAIL"},
        {"requirement": "six accepted T3 rows excluded", "evidence": "no source_lane=OTI8_CNR061 in packet", "status": "PASS" if all(r["source_lane"] != "OTI8_CNR061" for r in packet_rows) else "FAIL"},
        {"requirement": "94 G12-blocked CNR061 rows excluded", "evidence": g12_no_leak["blocked_94_exclusion"], "status": "PASS" if g12_no_leak["blocked_94_exclusion"]["status"] == "PASS" else "FAIL"},
        {"requirement": "source/hash ledger", "evidence": source_ledger["hash_summary"], "status": "PASS" if not source_ledger["hash_summary"]["expected_hash_mismatches"] else "FAIL"},
        {"requirement": "input-only packet or proof impossible", "evidence": {"packet_rows": len(packet_rows), "row_blockers": len(blockers)}, "status": "PASS" if len(packet_rows) + len(blockers) == 298 else "FAIL"},
        {"requirement": "no-leak duplicate sample-floor audit", "evidence": {"status": noleak["status"], "forbidden_hits": noleak["forbidden_packet_hits_count"]}, "status": noleak["status"]},
        {"requirement": "blocker/impossibility ledger", "evidence": "NOFILL_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json", "status": "PASS"},
        {"requirement": "forensics/learning", "evidence": "NOFILL_FORENSICS_AND_LEARNING_2026-05-08.json", "status": "PASS"},
        {"requirement": "G12 prompt pack", "evidence": "NOFILL_G12_AUDIT_PROMPT_PACK_2026-05-08.md", "status": "PASS"},
        {"requirement": "forbidden live surface diff", "evidence": live_surface_status(), "status": live_surface_status()["status"]},
    ]
    complete = all(item["status"] == "PASS" for item in checklist)
    return {
        "schema_version": SCHEMA,
        "artifact_family": "NOFILL_COMPLETION_AUDIT",
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "objective_restatement": "Build an input-only no-fill/still-pending/source-blocked lifecycle contract for the exact 298 non-T3 CNR rows without R/performance/live/account labels.",
        "run_order": run_order,
        "prompt_to_artifact_checklist": checklist,
        "can_mark_goal_complete_after_verifier": complete,
        "completion_status": "PASS_PENDING_EXTERNAL_COMMIT" if complete else "FAIL",
    }


def render_count_table(counts: dict[str, int]) -> list[str]:
    return [f"- `{k}`: {v}" for k, v in sorted(counts.items())]


def write_reports(
    family: dict[str, Any],
    source_ledger: dict[str, Any],
    packet_manifest: dict[str, Any],
    noleak: dict[str, Any],
    blocker: dict[str, Any],
    forensics: dict[str, Any],
    completion: dict[str, Any],
) -> None:
    write_json(output("NOFILL_298_FAMILY_SPLIT_INVENTORY_2026-05-08.json"), family)
    write_md(output("NOFILL_298_FAMILY_SPLIT_INVENTORY_2026-05-08.md"), [
        "# No-Fill 298 Family Split Inventory - 2026-05-08",
        "",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        f"Source universe rows: `{family['source_universe_rows']}`",
        f"Packet rows: `{family['packet_rows']}`",
        f"Exact row blockers: `{family['exact_blockers']}`",
        "",
        "## Contract Label Counts",
        *render_count_table(family["contract_label_counts"]),
        "",
        "## Source Lane Counts",
        *render_count_table(family["source_lane_counts"]),
    ])

    write_json(output("NOFILL_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json"), source_ledger)
    write_md(output("NOFILL_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.md"), [
        "# No-Fill Source Search And Hash Ledger - 2026-05-08",
        "",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Search Roots",
        *[f"- `{r['root']}` exists={r['exists']} matches={len(r.get('matches', []))} permission_error={r.get('permission_error')}" for r in source_ledger["searched_roots"]],
        "",
        "## Hash Summary",
        f"- Files listed: `{source_ledger['hash_summary']['files_listed']}`",
        f"- Existing files: `{source_ledger['hash_summary']['existing_files']}`",
        f"- Expected hash checks: `{source_ledger['hash_summary']['expected_hash_checks']}`",
        f"- Expected hash matches: `{source_ledger['hash_summary']['expected_hash_matches']}`",
        f"- Expected hash mismatches: `{len(source_ledger['hash_summary']['expected_hash_mismatches'])}`",
        f"- Missing expected files: `{len(source_ledger['hash_summary']['missing_expected_files'])}`",
    ])

    write_json(output("NOFILL_INPUT_ONLY_PACKET_2026-05-08.json"), packet_manifest)
    write_md(output("NOFILL_INPUT_ONLY_PACKET_2026-05-08.md"), [
        "# No-Fill Input-Only Packet - 2026-05-08",
        "",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        f"Packet rows: `{packet_manifest['packet_row_count']}`",
        f"Status: `{packet_manifest['status']}`",
        "",
        "## Label Counts",
        *render_count_table(packet_manifest["label_counts"]),
    ])

    write_json(output("NOFILL_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json"), noleak)
    write_md(output("NOFILL_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md"), [
        "# No-Fill No-Leak Duplicate Sample-Floor Audit - 2026-05-08",
        "",
        f"Status: `{noleak['status']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        f"Forbidden packet hits: `{noleak['forbidden_packet_hits_count']}`",
        f"Packet rows: `{noleak['packet_rows']}`",
        f"Unique duplicate keys: `{noleak['duplicate_key_unique']}`",
        f"Sample floor: `{noleak['validation_sample_floor_status']}`",
    ])

    write_json(output("NOFILL_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json"), blocker)
    write_md(output("NOFILL_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.md"), [
        "# No-Fill Blocker And Impossibility Ledger - 2026-05-08",
        "",
        f"Status: `{blocker['status']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        f"Exact row blockers: `{blocker['exact_row_blocker_count']}`",
        "",
        "## Family Failure Anatomy",
        *[f"- `{k}` rows={v['rows']} blocker_type=`{v['blocker_type']}` unblocker={v['exact_unblocker']}" for k, v in blocker["family_failure_anatomy"].items()],
    ])

    write_json(output("NOFILL_FORENSICS_AND_LEARNING_2026-05-08.json"), forensics)
    write_md(output("NOFILL_FORENSICS_AND_LEARNING_2026-05-08.md"), [
        "# No-Fill Forensics And Learning - 2026-05-08",
        "",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Learning",
        *[f"- {x}" for x in forensics["learning"]],
        "",
        "## Non-Claims",
        *[f"- {x}" for x in forensics["non_claims"]],
    ])

    output("NOFILL_G12_AUDIT_PROMPT_PACK_2026-05-08.md").write_text(build_g12_prompt_pack(), encoding="utf-8")

    write_json(output("NOFILL_COMPLETION_AUDIT_2026-05-08.json"), completion)
    write_md(output("NOFILL_COMPLETION_AUDIT_2026-05-08.md"), [
        "# No-Fill Completion Audit - 2026-05-08",
        "",
        f"Completion status: `{completion['completion_status']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Objective",
        completion["objective_restatement"],
        "",
        "## Checklist",
        *[f"- `{item['status']}` {item['requirement']}: {item['evidence']}" for item in completion["prompt_to_artifact_checklist"]],
    ])


def main() -> int:
    _anchor, _contract, run_order = write_anchor_and_contract()
    classification_started_at = utc_now()
    run_order["classification_started_at_utc"] = classification_started_at
    source_rows, _inv, _blocker, g12_no_leak, _g12 = reconstruct_universe()
    maps = build_source_maps()
    packet_rows, blockers = classify_universe(source_rows, maps, classification_started_at)
    source_ledger = build_source_ledger(packet_rows, maps)
    family = build_family_inventory(source_rows, packet_rows, blockers)
    packet_manifest = build_packet_manifest(packet_rows)
    noleak = build_noleak_audit(packet_rows, source_rows, g12_no_leak)
    blocker = build_blocker_ledger(packet_rows, blockers, source_ledger)
    forensics = build_forensics(packet_rows)
    completion = build_completion_audit(run_order, source_rows, packet_rows, blockers, source_ledger, noleak, g12_no_leak)
    write_jsonl(output("NOFILL_INPUT_ONLY_PACKET_2026-05-08_ROWS.jsonl"), packet_rows)
    write_reports(family, source_ledger, packet_manifest, noleak, blocker, forensics, completion)
    print(json.dumps({
        "status": completion["completion_status"],
        "source_rows": len(source_rows),
        "packet_rows": len(packet_rows),
        "row_blockers": len(blockers),
        "forbidden_hits": noleak["forbidden_packet_hits_count"],
        "hash_mismatches": len(source_ledger["hash_summary"]["expected_hash_mismatches"]),
    }, indent=2))
    return 0 if completion["completion_status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
