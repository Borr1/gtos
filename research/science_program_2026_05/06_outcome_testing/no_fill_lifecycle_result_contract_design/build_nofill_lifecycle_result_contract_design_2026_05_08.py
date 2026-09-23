from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE_STAMP = "2026-05-08"
CONTRACT_ID = "NOFILL_LIFECYCLE_CLOSURE_RESULT_CONTRACT_V1"
DESIGN_LANE_ID = "NOFILL_LIFECYCLE_CLOSURE_RESULT_CONTRACT_DESIGN_V1"
SCHEMA_VERSION = "nofill_lifecycle_result_contract_design_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]

G12_CORR_DIR = Path("research/science_program_2026_05/06_outcome_testing/g12_no_fill_correction_reaudit")
CLOSE_PACKET_DIR = Path("research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet")
CLOSE_CORR_DIR = Path("research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction")
G12_CLOSE_DIR = Path("research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit")
G12_NOFILL_DIR = Path("research/science_program_2026_05/06_outcome_testing/g12_no_fill_lifecycle_audit")
NOFILL_PENDING_DIR = Path("research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract")
G12_T3_DIR = Path("research/science_program_2026_05/06_outcome_testing/g12_cnr_t3_lifecycle_audit")
OTR061_DIR = Path("research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery")

ROW_0127_EXPECTED_SHA256 = "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
ROW_0127_FIRST_TOUCH = "2026-05-06T07:15:00.634000Z"
ROW_0127_SOURCE = OTR061_DIR / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"

RESULT_JSON_NAMES = [
    f"NOFILL_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_UNIVERSE_AND_EXCLUSION_LEDGER_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_POLICY_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_BLOCKER_LEDGER_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.json",
]

BASE_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

FORBIDDEN_PACKET_FIELDS = [
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
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


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


def write_json(name: str, payload: dict[str, Any]) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def write_md(name: str, title: str, body: str) -> None:
    text = f"# {title}\n\n{body.rstrip()}\n"
    (OUT_DIR / name).write_text(text, encoding="utf-8")


def counter_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda kv: kv[0]))


def load_upstream() -> dict[str, Any]:
    closure_rows = load_jsonl(CLOSE_PACKET_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl")
    return {
        "g12_corr_decision": load_json(G12_CORR_DIR / "G12_NOFILL_CORR_DECISION_LEDGER_2026-05-08.json"),
        "g12_corr_source": load_json(G12_CORR_DIR / "G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.json"),
        "g12_corr_row_0127": load_json(G12_CORR_DIR / "G12_NOFILL_CORR_ROW_0127_AUDIT_2026-05-08.json"),
        "g12_corr_noleak": load_json(G12_CORR_DIR / "G12_NOFILL_CORR_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json"),
        "close_packet_contract": load_json(CLOSE_PACKET_DIR / "NOFILL_CLOSE_FROZEN_SOURCE_CONTRACT_2026-05-08.json"),
        "close_packet_summary": load_json(CLOSE_PACKET_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08.json"),
        "close_packet_duplicate": load_json(CLOSE_PACKET_DIR / "NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json"),
        "close_packet_blockers": load_json(CLOSE_PACKET_DIR / "NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json"),
        "close_corr_resolution": load_json(CLOSE_CORR_DIR / "NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.json"),
        "g12_close_decision": load_json(G12_CLOSE_DIR / "G12_NOFILL_CLOSE_DECISION_LEDGER_2026-05-08.json"),
        "g12_nofill_decision": load_json(G12_NOFILL_DIR / "G12_NOFILL_DECISION_LEDGER_2026-05-08.json"),
        "g12_nofill_universe": load_json(G12_NOFILL_DIR / "G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json"),
        "g12_nofill_label": load_json(G12_NOFILL_DIR / "G12_NOFILL_LABEL_FAMILY_AUDIT_2026-05-08.json"),
        "nofill_pending_contract": load_json(NOFILL_PENDING_DIR / "NOFILL_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json"),
        "nofill_pending_packet": load_json(NOFILL_PENDING_DIR / "NOFILL_INPUT_ONLY_PACKET_2026-05-08.json"),
        "g12_t3_decision": load_json(G12_T3_DIR / "G12_CNR_T3_DECISION_LEDGER_2026-05-08.json"),
        "closure_rows": closure_rows,
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
        OUT_DIR / "NOFILL_LIFECYCLE_RESULT_CONTRACT_DESIGN_GOAL_PROMPT_2026-05-08.md",
        G12_CORR_DIR / "G12_NOFILL_CORR_NEXT_PROMPT_PACK_2026-05-08.md",
        G12_CORR_DIR / "G12_NOFILL_CORR_DECISION_LEDGER_2026-05-08.json",
        G12_CORR_DIR / "G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.json",
        G12_CORR_DIR / "G12_NOFILL_CORR_ROW_0127_AUDIT_2026-05-08.json",
        G12_CORR_DIR / "G12_NOFILL_CORR_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
        CLOSE_PACKET_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08.json",
        CLOSE_PACKET_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl",
        CLOSE_PACKET_DIR / "NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json",
        CLOSE_CORR_DIR / "NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.json",
        G12_CLOSE_DIR / "G12_NOFILL_CLOSE_DECISION_LEDGER_2026-05-08.json",
        G12_NOFILL_DIR / "G12_NOFILL_DECISION_LEDGER_2026-05-08.json",
        G12_NOFILL_DIR / "G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json",
        NOFILL_PENDING_DIR / "NOFILL_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json",
        NOFILL_PENDING_DIR / "NOFILL_INPUT_ONLY_PACKET_2026-05-08.json",
        G12_T3_DIR / "G12_CNR_T3_DECISION_LEDGER_2026-05-08.json",
        ROW_0127_SOURCE,
    ]
    for path in sorted((REPO_ROOT / G12_CORR_DIR).glob("G12_NOFILL_CORR_*")):
        if path.is_file():
            rel_path = path.relative_to(REPO_ROOT)
            if rel_path not in paths:
                paths.append(rel_path)
    records = []
    seen: set[str] = set()
    for path in paths:
        record = hash_record(path)
        if record["path"] not in seen:
            seen.add(record["path"])
            records.append(record)
    return records


def build_rulebook(up: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        "artifact_family": "NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "design_lane_id": DESIGN_LANE_ID,
        "generated_at_utc": generated_at,
        "contract_frozen_at_utc": generated_at,
        "contract_status": "FROZEN_DESIGN_ONLY_RESULT_LANE_NOT_OPEN",
        **BASE_FLAGS,
        "starting_evidence_locked": {
            "g12_decision": up["g12_corr_decision"]["decision"],
            "packet_rows": up["g12_corr_decision"]["counts_summary"]["packet_json_count"],
            "source_closed": up["g12_corr_decision"]["counts_summary"]["blocker_ledger_source_closed_rows"],
            "source_blocked_exact": up["g12_corr_decision"]["counts_summary"]["blocker_ledger_source_blocked_exact_rows"],
            "row_0127_source_sha256": ROW_0127_EXPECTED_SHA256,
            "row_0127_first_terminal_area_touch_utc": ROW_0127_FIRST_TOUCH,
            "six_t3_rows_excluded": True,
            "blocked_94_cnr061_rows_excluded": True,
        },
        "scope_boundary": {
            "what_this_contract_allows_next": (
                "A future G12-accepted result lane may categorize lifecycle closure states from "
                "source-hashed evidence under these rules."
            ),
            "what_this_contract_does_not_allow": [
                "No R/performance/win-rate/expectancy scoring.",
                "No broker/account/live/order/hidden labels.",
                "No blocked CNR061 rows and no six T3 stop_after_original_horizon rows.",
                "No promotion, validation, or live-effect claim.",
                "No live trading surface, registry, credential, remote, paid/API/Databento, or MT5 order/account call.",
            ],
            "current_lane_outputs_are_design_only": True,
        },
        "eligible_universe": {
            "source_packet": "NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1 after correction/G12 reaudit",
            "row_count": 298,
            "row_status_required": "source_closed",
            "result_rows_opened_by_this_lane": 0,
            "excluded_universes": {
                "six_cnr_t3_stop_after_original_horizon_rows": [
                    "CNR-T3-CAND-0001",
                    "CNR-T3-CAND-0002",
                    "CNR-T3-CAND-0003",
                    "CNR-T3-CAND-0004",
                    "CNR-T3-CAND-0005",
                    "CNR-T3-CAND-0006",
                ],
                "blocked_94_cnr061_rows": "exactly excluded by G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT",
                "any_row_with_source_status_other_than_source_closed": "blocked",
                "any_row_needing broker/account/live/order source": "blocked",
            },
        },
        "result_label_families": {
            "categorical_lifecycle_only": {
                "nofill_terminal_before_entry": {
                    "source_closure_inputs": [
                        "entry_not_touched_before_terminal_area_source_confirmed",
                        "terminal_sequence_tick_source_projected_no_score when first event is terminal_area",
                    ],
                    "required_proof": "side-aware terminal touch before side-aware entry touch while pending intent is active or input row is an accepted source-only no-entry family",
                    "r_performance_allowed": False,
                },
                "nofill_no_entry_through_frozen_horizon": {
                    "source_closure_inputs": ["entry_not_touched_through_tick_horizon_source_confirmed"],
                    "required_proof": "source-hashed quote/tick path covers path_start through frozen horizon with no side-aware entry touch",
                    "r_performance_allowed": False,
                },
                "nofill_cancelled_wrong_side_before_fill": {
                    "source_closure_inputs": ["pending_cancelled_wrong_side_before_fill_source_confirmed"],
                    "required_proof": "source-hashed pending-intent cancellation reason and no earlier side-aware fill touch",
                    "r_performance_allowed": False,
                },
                "nofill_cancelled_system_or_new_day_before_fill": {
                    "source_closure_inputs": ["pending_cancelled_system_or_new_day_before_fill_source_confirmed"],
                    "required_proof": "source-hashed pending-intent system/new-day cancel or expiry event and no earlier side-aware fill touch",
                    "r_performance_allowed": False,
                },
                "nofill_still_pending_at_frozen_horizon": {
                    "source_closure_inputs": ["pending_still_open_at_frozen_horizon_source_confirmed"],
                    "required_proof": "frozen observation horizon and source-hashed pending-intent state at horizon",
                    "r_performance_allowed": False,
                },
            },
            "result_blocked_or_separate_family": {
                "entry_touched_terminal_sequence_unclaimed": {
                    "source_closure_inputs": ["entry_touched_terminal_sequence_unclaimed_source_confirmed"],
                    "reason": "entry touch moves the row out of no-fill closure unless a separate fill/result contract proves active fill and terminal order",
                },
                "price_compatible_m1_source_recovered": {
                    "source_closure_inputs": ["price_compatible_m1_source_recovered"],
                    "reason": "price-compatible M1 source is source availability only; it is not side-aware quote/fill/terminal ordering proof",
                },
                "terminal_order_unclaimed_due_same_bar_or_ltf_gap": {
                    "source_closure_inputs": ["terminal_order_unclaimed_due_same_bar_or_ltf_gap"],
                    "reason": "same-bar or lower-timeframe gap must remain ambiguous until tick/quote path evidence resolves ordering",
                },
                "source_blocked_missing_required_field": {
                    "source_closure_inputs": [
                        "source_blocked_missing_price_compatible_path",
                        "source_blocked_missing_pending_lifecycle_fields",
                        "source_blocked_missing_top_level_symbol_session_side",
                    ],
                    "reason": "exact source blocker must be carried; no result label can be inferred",
                },
            },
            "forbidden_label_families": [
                "R/performance labels",
                "broker actual-R labels",
                "account-history labels",
                "live order/deal/position labels",
                "hidden labels",
                "stop_after_original_horizon T3 labels",
            ],
        },
        "entry_fill_cancel_expiry_semantics": {
            "entry_touch": "A side-aware quote touch of the frozen entry price under the parser rules; quote touch alone is not broker fill.",
            "fill": "May be claimed only when an active pending intent exists, the source-hashed side-aware entry touch occurs before cancel/expiry, and no forbidden broker/live/account source is used.",
            "no_fill": "A categorical lifecycle state proving no source-authorized fill occurred before terminal/cancel/expiry/horizon under this contract.",
            "wrong_side_cancel": "Pending-intent source says wrong_side/no_fill_cancelled_wrong_side before any source-hashed fill touch.",
            "system_cancel": "Pending-intent source says system cancel before any source-hashed fill touch.",
            "new_day_expiry": "Source-hashed pending-intent expiry or frozen policy expiry at the next-day boundary before fill.",
            "still_pending_at_horizon": "Frozen horizon reached with no fill/cancel/expiry source; not converted into a terminal performance outcome.",
            "entry_touched_sequence_unclaimed": "Entry touch exists but later terminal/protective ordering is not claimable; route to a separate fill/path contract.",
        },
        "side_aware_touch_parser": {
            "parser_id": "bid_ask_side_aware_touch_times_v1",
            "long": {
                "entry_fill_touch": "ask <= entry_price",
                "terminal_area_touch": "bid >= terminal_area_price",
                "protective_touch": "bid <= protective_level_price",
            },
            "short": {
                "entry_fill_touch": "bid >= entry_price",
                "terminal_area_touch": "ask <= terminal_area_price",
                "protective_touch": "ask >= protective_level_price",
            },
            "ordering": "Sort by source timestamp ascending; simultaneous conflicting events are ambiguous unless a later contract has source row sequence proof.",
        },
        "source_hierarchy": {
            "tier_1_tick_quote_path": "Source-hashed tick parquet/CSV with UTC timestamp, bid, and ask. Required for side-aware touch ordering.",
            "tier_2_lower_timeframe_ohlc": "Source-hashed M1/M5 OHLC can support price-compatible path context but cannot by itself prove bid/ask fill or terminal/protective ordering.",
            "tier_3_pending_intent_logs": "Source-hashed pending lifecycle projection/log rows can prove cancel, expiry, and still-pending state only if the required closure fields are present.",
            "tier_4_packet_projection_rows": "Accepted packet rows provide identity, frozen geometry, and input labels; they cannot become result labels without tier 1/2/3 source sufficiency.",
            "insufficient_sources": [
                "Unhashed local files",
                "Broker/account/live order state",
                "Hidden labels",
                "Search snippets or chat memory",
                "Lower-timeframe OHLC for side-aware fill proof without a conservative quote contract",
            ],
        },
        "same_bar_and_terminal_order_policy": {
            "same_timestamp_entry_and_terminal": "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS",
            "same_timestamp_terminal_and_protective": "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS",
            "ohlc_same_bar_without_tick_path": "BLOCK_RESULT_LTF_GAP",
            "row_0127_terminal_first_boundary": "The OTR061 first terminal-area event is sufficient for terminal-before-entry categorical closure; it is not R/performance.",
        },
        "duplicate_denominator_policy": {
            "row_identity": "source_inventory_id remains unique source inventory identity.",
            "primary_denominator_key": "nofill_duplicate_key",
            "secondary_denominator_key": "duplicate_group_id",
            "counting_rule": "Future result reports must show row-level counts and collapsed unique nofill_duplicate_key counts; validation/promotion cannot use row-level repeats.",
            "canonical_duplicate_selection": "For any scored categorical family, keep earliest decision_asof_utc within nofill_duplicate_key, then lexicographic source_inventory_id; retain other rows as duplicate metadata.",
            "duplicate_conflict": "If duplicate rows disagree on categorical label or source geometry, block the whole duplicate group pending source audit.",
        },
        "sample_floor_policy": {
            "design_lane": "No sample floor applies because no outcomes are opened.",
            "future_discovery_report": "May report categorical counts at any n, but must label under_sample_floor until >=30 unique nofill_duplicate_key rows per label family and >=10 unique duplicate_group_id rows.",
            "future_validation_report": "Requires >=100 unique nofill_duplicate_key rows overall, >=30 per reported primary family, no single duplicate_group_id >10%, no single symbol/session/side bucket >35%, and predeclared denominator before label scan.",
            "promotion": "Blocked regardless of n until a separate promotion dossier exists; then GTOS methodology gates also require DSR-corrected p < 0.01, PBO < 0.4, and effective_N >= 3 where applicable.",
        },
        "no_leak_asof_schema": {
            "decision_time_fields": "Frozen geometry and candidate metadata known at decision_asof_utc only.",
            "label_time_fields": "Post-asof quote/path/pending lifecycle events used only to assign categorical labels, never as decision features.",
            "source_time_fields": "source_path, source_sha256, source_first_ts_utc, source_last_ts_utc, parser version, and hash ledger timestamps.",
            "forbidden_fields": FORBIDDEN_PACKET_FIELDS,
            "asof_rule": "No field generated after a closure event may be used to modify the frozen entry, side, terminal area, protective level, session, or duplicate key.",
        },
        "source_hash_and_cache_policy": {
            "all_consumed_files_hashed": True,
            "required_hash_algorithm": "sha256",
            "raw_source_ledger_required": True,
            "hash_mismatch_policy": "BLOCK_RESULT_SOURCE_HASH_MISMATCH",
            "missing_source_policy": "BLOCK_RESULT_MISSING_SOURCE_WITH_EXACT_REQUEST",
            "mutable_context_policy": "Context docs may drift but must be re-read and re-hashed at lane start; row source evidence cannot drift.",
        },
        "dsr_pbo_effective_n_policy": {
            "current_contract_design": "not_computable_no_result_values_opened",
            "future_categorical_result_lane": "effective_N and duplicate/concentration diagnostics required; DSR/PBO only if numeric selection/performance comparisons are introduced by a separate approved lane.",
            "future_performance_lane": "Out of scope here and requires a new frozen result contract plus promotion dossier.",
        },
        "exact_next_lane_gates": [
            "G12 must audit and accept this frozen result contract before any result packet is built.",
            "A future result packet builder must emit row-level eligibility/blocker decisions before assigning labels.",
            "The future lane must re-run source hashes, no-leak/as-of checks, duplicate/sample-floor checks, and excluded-universe checks.",
            "Any missing pending-intent closure field must remain a blocker, not an inferred label.",
            "Any R/performance/broker/account/live/hidden label request must stop and open a separate owner-approved contract.",
        ],
    }


def build_universe(up: dict[str, Any], generated_at: str) -> dict[str, Any]:
    rows = up["closure_rows"]
    closure_counts = Counter(row["closure_label"] for row in rows)
    lane_counts = Counter(row["source_lane"] for row in rows)
    status_counts = Counter(row["closure_status"] for row in rows)
    source_inventory_ids = {row["source_inventory_id"] for row in rows}
    duplicate_keys = {row.get("nofill_duplicate_key") for row in rows if row.get("nofill_duplicate_key")}
    duplicate_group_ids = {row.get("duplicate_group_id") for row in rows if row.get("duplicate_group_id")}
    return {
        "artifact_family": "NOFILL_RESULT_CONTRACT_UNIVERSE_AND_EXCLUSION_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": generated_at,
        **BASE_FLAGS,
        "universe_status": "SOURCE_CLOSED_INPUT_UNIVERSE_ONLY_RESULT_ROWS_NOT_OPENED",
        "source_packet": {
            "packet_id": "NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1",
            "packet_rows": len(rows),
            "closure_status_counts": counter_dict(status_counts),
            "closure_label_counts": counter_dict(closure_counts),
            "source_lane_counts": counter_dict(lane_counts),
            "source_inventory_id_unique": len(source_inventory_ids),
            "nofill_duplicate_key_unique": len(duplicate_keys),
            "duplicate_group_id_unique": len(duplicate_group_ids),
            "rows_with_exact_blockers": up["close_packet_blockers"]["rows_with_exact_blockers"],
            "source_blocked_exact_rows": up["close_packet_blockers"]["source_blocked_exact_rows"],
            "source_closed_rows": up["close_packet_blockers"]["source_closed_rows"],
        },
        "accepted_starting_facts": {
            "g12_decision": up["g12_corr_decision"]["decision"],
            "g12_packet_count_pass": up["g12_corr_decision"]["counts_summary"]["packet_count_pass"],
            "g12_source_closed_pass": up["g12_corr_decision"]["counts_summary"]["source_closed_pass"],
            "g12_source_blocked_exact_pass": up["g12_corr_decision"]["counts_summary"]["source_blocked_exact_pass"],
        },
        "exclusions": {
            "six_t3_rows": up["g12_corr_source"]["exclusion_status"]["six_t3_rows"],
            "blocked_94_cnr061": up["g12_corr_source"]["exclusion_status"]["blocked_94_cnr061"],
            "packet_t3_or_oti8_leaks": up["g12_corr_source"]["exclusion_status"]["packet_t3_or_oti8_leaks"],
            "packet_oti8_cnr061_row_count": up["g12_corr_source"]["exclusion_status"]["packet_oti8_cnr061_row_count"],
        },
        "current_result_opening_status": {
            "result_rows_opened": 0,
            "r_or_performance_rows_scored": 0,
            "broker_account_live_hidden_rows_inspected": 0,
            "blocked_cnr061_rows_scored": 0,
        },
        "current_family_route_map": {
            "entry_not_touched_before_terminal_area_source_confirmed": "future categorical nofill_terminal_before_entry candidate, requires G12 accepted result contract",
            "entry_not_touched_through_tick_horizon_source_confirmed": "future categorical nofill_no_entry_through_frozen_horizon candidate, requires full source-hashed quote/tick horizon",
            "pending_cancelled_wrong_side_before_fill_source_confirmed": "future categorical nofill_cancelled_wrong_side_before_fill candidate, requires pending-intent closure fields",
            "pending_cancelled_system_or_new_day_before_fill_source_confirmed": "future categorical nofill_cancelled_system_or_new_day_before_fill candidate, requires pending-intent closure fields",
            "pending_still_open_at_frozen_horizon_source_confirmed": "future categorical still_pending_at_horizon candidate, not performance",
            "entry_touched_terminal_sequence_unclaimed_source_confirmed": "blocked from no-fill result; requires separate fill/path contract",
            "price_compatible_m1_source_recovered": "source availability only; blocked for side-aware result until quote/tick or conservative lower-TF contract",
            "terminal_sequence_tick_source_projected_no_score": "source closure only; future categorical label depends on row-level first-event proof",
        },
    }


def build_field_requirements(up: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        "artifact_family": "NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": generated_at,
        **BASE_FLAGS,
        "required_row_identity_fields": [
            "packet_row_id",
            "source_inventory_id",
            "source_lane",
            "source_packet_id",
            "source_row_id",
            "source_artifact_path",
            "source_artifact_sha256",
            "schema_version",
        ],
        "required_frozen_decision_fields": [
            "projected_symbol or source_symbol",
            "projected_session or session",
            "projected_side or side",
            "decision_asof_utc",
            "entry_price",
            "terminal_area_price",
            "protective_level_price",
            "duplicate_group_id",
            "nofill_duplicate_key",
        ],
        "required_pending_intent_closure_fields": [
            "pending_intent_id or deterministic source pending key",
            "pending_created_at_utc",
            "pending_active_from_utc",
            "pending_active_until_utc",
            "entry_touched_at_utc",
            "filled_at_utc",
            "cancelled_at_utc",
            "cancel_reason",
            "expired_at_utc",
            "expiry_policy_id",
            "frozen_horizon_start_utc",
            "frozen_horizon_end_utc",
            "last_observed_pending_state_at_utc",
            "source_path",
            "source_sha256",
        ],
        "required_quote_tick_path_fields": [
            "path_start_utc",
            "path_end_utc",
            "source_files",
            "source_sha256",
            "source_first_ts_utc",
            "source_last_ts_utc",
            "timestamp_utc",
            "bid",
            "ask",
            "entry_touch_time_utc",
            "terminal_area_touch_time_utc",
            "protective_level_touch_time_utc",
            "ordered_source_events",
            "same_timestamp_ambiguity",
            "parser_contract",
        ],
        "lower_timeframe_path_fields": [
            "timeframe",
            "source_path",
            "source_sha256",
            "path_start_utc",
            "path_end_utc",
            "open",
            "high",
            "low",
            "close",
            "timezone",
            "price_scale_contract",
            "path_order_label",
            "ambiguity_flags",
        ],
        "source_sufficiency_matrix": {
            "tick_bid_ask_path": {
                "entry_fill_touch": "sufficient_quote_touch_not_broker_fill",
                "terminal_area_touch": "sufficient",
                "protective_touch": "sufficient",
                "ordering": "sufficient unless same timestamp ambiguity",
            },
            "lower_timeframe_ohlc": {
                "entry_fill_touch": "insufficient_for_bid_ask_fill_without_quote_contract",
                "terminal_area_touch": "price_compatible_context_only",
                "protective_touch": "price_compatible_context_only",
                "ordering": "insufficient_for_terminal_order_if same bar or no tick order",
            },
            "pending_intent_projection": {
                "cancel_expiry_still_pending": "sufficient only if required fields and source hash are present",
                "fill": "insufficient without side-aware quote/tick entry touch or explicit source fill field in non-live log",
            },
        },
        "current_exact_missing_field_counts": up["close_packet_blockers"]["blocker_counts"],
        "row_0127_source_requirement_status": {
            "source_hash": ROW_0127_EXPECTED_SHA256,
            "first_terminal_area_touch_utc": ROW_0127_FIRST_TOUCH,
            "full_path_end_coverage": "not required for terminal-first categorical source closure; exact read-only request remains if future lane demands independent full-horizon proof",
        },
    }


def build_touch_parser(generated_at: str) -> dict[str, Any]:
    return {
        "artifact_family": "NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": generated_at,
        **BASE_FLAGS,
        "parser_id": "bid_ask_side_aware_touch_times_v1",
        "input_requirements": {
            "timestamp": "UTC timestamp with stable row order from source file",
            "bid": "numeric broker/source bid quote",
            "ask": "numeric broker/source ask quote",
            "entry_price": "frozen at decision_asof_utc",
            "terminal_area_price": "frozen at decision_asof_utc",
            "protective_level_price": "frozen at decision_asof_utc",
            "side": "LONG or SHORT frozen at decision_asof_utc",
        },
        "side_rules": {
            "LONG": {
                "entry_touch": "ask <= entry_price",
                "terminal_area_touch": "bid >= terminal_area_price",
                "protective_touch": "bid <= protective_level_price",
                "wrong_side_before_fill": "terminal_area_touch before entry_touch may support terminal-before-entry lifecycle closure; pending-intent cancel reason still required for wrong-side-cancel label",
            },
            "SHORT": {
                "entry_touch": "bid >= entry_price",
                "terminal_area_touch": "ask <= terminal_area_price",
                "protective_touch": "ask >= protective_level_price",
                "wrong_side_before_fill": "terminal_area_touch before entry_touch may support terminal-before-entry lifecycle closure; pending-intent cancel reason still required for wrong-side-cancel label",
            },
        },
        "ordered_event_algorithm": [
            "Filter source rows to path_start_utc <= timestamp <= path_end_utc.",
            "Evaluate entry, terminal, and protective touch predicates on each row using the frozen side.",
            "Record the first timestamp for each event type and the quote values that triggered it.",
            "Sort first events by timestamp.",
            "If two or more conflicting first events have the same timestamp, emit BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS unless source row sequence proof is separately hashed.",
            "If terminal event is strictly before entry event and protective event, categorical nofill_terminal_before_entry can be assigned by a future accepted result lane.",
            "If entry event is strictly before terminal/protective, route out of no-fill closure into separate fill/path contract.",
            "If no entry event exists through a fully covered frozen horizon, categorical nofill_no_entry_through_frozen_horizon can be assigned by a future accepted result lane.",
        ],
        "same_bar_policy": {
            "tick_same_timestamp_conflict": "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS",
            "m1_same_bar_terminal_and_entry": "BLOCK_RESULT_LTF_GAP",
            "ohlc_no_intrabar_order": "cannot claim order; keep categorical source-control or exact blocker",
        },
        "lower_timeframe_policy": {
            "m1_ohlc_price_compatible": "May prove a source window exists and price scale is compatible.",
            "m1_ohlc_no_touch": "May support no-touch context only if the future contract defines a conservative bid/ask spread bound and hashes that source.",
            "m1_ohlc_terminal_order": "Not sufficient for side-aware terminal/protective/entry ordering without tick path or explicit path-order source accepted by G12.",
        },
    }


def build_noleak_schema(generated_at: str) -> dict[str, Any]:
    return {
        "artifact_family": "NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": generated_at,
        **BASE_FLAGS,
        "asof_model": {
            "decision_asof_utc": "Freezes symbol/session/side/entry/terminal/protective geometry and duplicate keys.",
            "path_start_utc": "Must be >= decision_asof_utc unless source explicitly records pending creation before decision.",
            "label_event_utc": "First source event used only as categorical label evidence, never as decision feature.",
            "hash_asof": "All source files must be hashed before result labels are emitted in the future lane.",
        },
        "allowed_decision_time_fields": [
            "source_inventory_id",
            "source_lane",
            "source_packet_id",
            "source_row_id",
            "symbol",
            "session",
            "side",
            "decision_asof_utc",
            "entry_price",
            "terminal_area_price",
            "protective_level_price",
            "duplicate_group_id",
            "nofill_duplicate_key",
        ],
        "allowed_label_time_fields": [
            "entry_touch_time_utc",
            "terminal_area_touch_time_utc",
            "protective_level_touch_time_utc",
            "cancelled_at_utc",
            "cancel_reason",
            "expired_at_utc",
            "frozen_horizon_end_utc",
            "ordered_source_events",
            "same_timestamp_ambiguity",
        ],
        "allowed_source_control_fields": [
            "source_path",
            "source_sha256",
            "source_first_ts_utc",
            "source_last_ts_utc",
            "source_row_count",
            "parser_contract",
            "schema_version",
            "builder_version",
            "verification_status",
        ],
        "forbidden_fields": FORBIDDEN_PACKET_FIELDS,
        "label_family_separation": {
            "source_control_labels": "Input-only closure packet labels remain source-control evidence.",
            "categorical_lifecycle_labels": "Future result lane may emit categorical lifecycle labels only after G12 accepts this contract.",
            "synthetic_path_labels": "Out of scope unless a separate synthetic path contract is frozen.",
            "broker_account_labels": "Forbidden in this contract.",
            "performance_labels": "Forbidden in this contract.",
        },
        "leakage_blocker_rules": [
            "If a row contains any forbidden field as row data, block it.",
            "If label-time fields modify decision-time geometry, block it.",
            "If source hash or source path is missing for a label-time event, block it.",
            "If account, broker, live, MT5 order/account, or hidden fields are needed, stop and request a separate owner-approved contract.",
        ],
    }


def build_duplicate_samplefloor(up: dict[str, Any], generated_at: str) -> dict[str, Any]:
    duplicate = up["close_packet_duplicate"]
    g12_dup = up["g12_corr_noleak"]
    return {
        "artifact_family": "NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_POLICY",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": generated_at,
        **BASE_FLAGS,
        "current_duplicate_state": {
            "packet_rows": duplicate["packet_rows"],
            "source_inventory_id_unique": duplicate["source_inventory_id_unique"],
            "nofill_duplicate_key_unique": duplicate["nofill_duplicate_key_unique"],
            "duplicate_group_id_unique": duplicate["duplicate_group_id_unique"],
            "nofill_duplicate_key_max_repeat": duplicate["nofill_duplicate_key_max_repeat"],
            "duplicate_group_id_max_repeat": duplicate["duplicate_group_id_max_repeat"],
            "validation_sample_floor_status": duplicate["validation_sample_floor_status"],
            "g12_unique_source_inventory_ids": g12_dup["unique_source_inventory_ids"],
            "g12_unique_nofill_duplicate_keys": g12_dup["unique_nofill_duplicate_keys"],
            "g12_unique_duplicate_group_ids": g12_dup["unique_duplicate_group_ids"],
        },
        "denominator_policy": {
            "source_inventory_id": "identity only, never validation denominator",
            "nofill_duplicate_key": "primary unique opportunity denominator",
            "duplicate_group_id": "secondary concentration and conflict denominator",
            "row_level_counts": "allowed as source inventory only",
            "conflict_policy": "block duplicate key if duplicate rows disagree on family label, geometry, or source ordering",
        },
        "sample_floor_policy": {
            "current_design_lane": {
                "status": "NOT_APPLICABLE_NO_RESULT_ROWS_OPENED",
                "can_claim_validation": False,
            },
            "future_result_discovery": {
                "minimum_unique_nofill_duplicate_key_per_family": 30,
                "minimum_unique_duplicate_group_id_per_family": 10,
                "label_if_below_floor": "DISCOVERY_UNDER_SAMPLE_FLOOR",
            },
            "future_result_validation": {
                "minimum_unique_nofill_duplicate_key_overall": 100,
                "minimum_unique_nofill_duplicate_key_per_primary_family": 30,
                "max_single_duplicate_group_share": 0.10,
                "max_single_symbol_session_side_share": 0.35,
                "requires_predeclared_denominator": True,
                "can_claim_promotion": False,
            },
            "promotion": {
                "status": "BLOCKED_BY_POLICY",
                "requires_separate_promotion_dossier": True,
                "methodology_gate": "DSR_p<0.01, PBO<0.4, effective_N>=3 where applicable",
            },
        },
    }


def build_blocker_ledger(up: dict[str, Any], generated_at: str) -> dict[str, Any]:
    blocker_counts = up["close_packet_blockers"]["blocker_counts"]
    return {
        "artifact_family": "NOFILL_RESULT_CONTRACT_BLOCKER_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": generated_at,
        **BASE_FLAGS,
        "current_exact_blocker_counts_from_source_closure_packet": blocker_counts,
        "current_rows_with_exact_blockers": up["close_packet_blockers"]["rows_with_exact_blockers"],
        "result_contract_blocker_rules": {
            "BLOCK_RESULT_EXCLUDED_T3_ROW": "source_inventory_id is one of CNR-T3-CAND-0001..0006 or stop_after_original_horizon label appears",
            "BLOCK_RESULT_EXCLUDED_CNR061_BLOCKED_ROW": "row is in the 94 G12-blocked CNR061 set or source_lane=OTI8_CNR061 from the blocked packet",
            "BLOCK_RESULT_SOURCE_HASH_MISMATCH": "any row source hash differs from the frozen ledger",
            "BLOCK_RESULT_MISSING_SOURCE": "required tick/lower-timeframe/pending-intent source file is absent or unhashed",
            "BLOCK_RESULT_FORBIDDEN_FIELD": "row carries broker/account/live/order/hidden/performance field",
            "BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD": "pending lifecycle family lacks entry_touched_at_utc/fill/cancel/expiry/horizon fields",
            "BLOCK_RESULT_LTF_PRICE_ONLY": "row has price-compatible M1/OHLC source only but no side-aware quote/tick parser proof",
            "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": "entry, terminal, or protective event order is same-timestamp or same-bar unresolved",
            "BLOCK_RESULT_DUPLICATE_CONFLICT": "duplicate key rows disagree on geometry, family label, or source ordering",
            "BLOCK_RESULT_ASOF_LEAK": "post-label evidence modifies decision-time geometry or duplicate keys",
            "BLOCK_RESULT_BROKER_OR_LIVE_SOURCE_REQUIRED": "classification requires broker/account/live/order source",
        },
        "row_0127_status": {
            "source_closed": True,
            "source_sha256": ROW_0127_EXPECTED_SHA256,
            "first_terminal_area_touch_utc": ROW_0127_FIRST_TOUCH,
            "blocked_now": False,
            "future_exact_request_if_full_horizon_needed": "NOFILL-CLOSE-ROW-0127_XAUUSD_2026-05-06_ticks_READONLY_REQUEST.json",
        },
        "next_unblockers": [
            {
                "blocker": "entry_touched_at_utc is not materialized in pending lifecycle source",
                "exact_unblocker": "Add source-hashed pending intent closure fields for entry_touched_at_utc, filled_at_utc, cancelled_at_utc, cancel_reason, expired_at_utc, and frozen_horizon_end_utc.",
            },
            {
                "blocker": "missing_prereg_opening_drive_field_*",
                "exact_unblocker": "Freeze and source-hash opening-drive range_high/range_low/breakout_side/breakout_close_time in the prereg source packet before result classification.",
            },
            {
                "blocker": "post_entry_terminal_touch_time is not claimable from the M1 path-order row",
                "exact_unblocker": "Provide tick/quote source or accepted lower-timeframe ordering contract for post-entry terminal/protective events.",
            },
            {
                "blocker": "terminal touch replay remains unopened",
                "exact_unblocker": "Build a separate terminal replay source packet with source-hashed M1/tick path and parser/scale contract.",
            },
        ],
    }


def build_context_anchor(generated_at: str, hashes: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "artifact_family": "NOFILL_RESULT_CONTRACT_CONTEXT_ANCHOR",
        "schema_version": SCHEMA_VERSION,
        "lane": DESIGN_LANE_ID,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": generated_at,
        "git_head": git_head(),
        **BASE_FLAGS,
        "research_lane_type": "contract_design_only",
        "controlling_prompt": rel(OUT_DIR / "NOFILL_LIFECYCLE_RESULT_CONTRACT_DESIGN_GOAL_PROMPT_2026-05-08.md"),
        "controlling_inputs": [
            rel(G12_CORR_DIR / "G12_NOFILL_CORR_NEXT_PROMPT_PACK_2026-05-08.md"),
            rel(G12_CORR_DIR),
            rel(CLOSE_PACKET_DIR),
            rel(CLOSE_CORR_DIR),
            rel(G12_CLOSE_DIR),
            rel(G12_NOFILL_DIR),
            rel(NOFILL_PENDING_DIR),
            rel(G12_T3_DIR),
            rel(OTR061_DIR),
        ],
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
        },
        "searched_roots": [
            "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery",
            "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
            "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery",
            "C:/tmp/gtos_otb",
        ],
        "active_question_stack": [
            "Which 298 rows may a future no-fill lifecycle result lane consider?",
            "Which labels are categorical lifecycle only and which are result-blocked?",
            "Which source class proves entry/fill/cancel/expiry/touch ordering?",
            "Which duplicate and sample-floor rules prevent row-repeat inflation?",
            "Which exact blockers stop a future row from receiving a label?",
            "What must G12 audit before any result lane opens?",
        ],
        "route_decisions": [
            "Use corrected G12 source packet as input-only source closure evidence.",
            "Do not parse or score rows for R/performance.",
            "Use existing upstream counts and row-level source hashes as controls.",
            "Treat lower-timeframe OHLC as price-compatible context unless a separate quote-side contract is accepted.",
            "Keep row 0127 source-closed from OTR061 terminal-first evidence but not performance-scored.",
        ],
        "source_files_read_or_hashed": hashes,
        "instruction_coverage": {
            "entry_fill_cancel_expiry_semantics": "covered in frozen rulebook",
            "quote_tick_ltf_path_evidence": "covered in field requirements and parser",
            "pending_intent_closure_fields": "covered in field requirements and blocker ledger",
            "side_aware_touch_parser": "covered in parser artifact",
            "duplicate_policy": "covered in duplicate/sample-floor policy",
            "sample_floor": "covered in duplicate/sample-floor policy",
            "source_hash_rules": "covered in rulebook and context anchor",
            "no_leak_asof_schema": "covered in noleak/asof schema",
            "label_family_separation": "covered in rulebook and noleak/asof schema",
            "exact_blocker_rules": "covered in blocker ledger",
            "no_scoring_or_live_effect": "all flags false and result rows opened = 0",
        },
    }


def build_completion_audit(generated_at: str) -> dict[str, Any]:
    expected = [
        f"NOFILL_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE_STAMP}.md/json",
        f"NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE_STAMP}.md/json",
        f"NOFILL_RESULT_CONTRACT_UNIVERSE_AND_EXCLUSION_LEDGER_{DATE_STAMP}.md/json",
        f"NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS_{DATE_STAMP}.md/json",
        f"NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_{DATE_STAMP}.md/json",
        f"NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA_{DATE_STAMP}.md/json",
        f"NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_POLICY_{DATE_STAMP}.md/json",
        f"NOFILL_RESULT_CONTRACT_BLOCKER_LEDGER_{DATE_STAMP}.md/json",
        f"NOFILL_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE_STAMP}.md",
        f"NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.md/json",
        "build_nofill_lifecycle_result_contract_design_2026_05_08.py",
        "verify_nofill_lifecycle_result_contract_design_2026_05_08.py",
        "test_nofill_lifecycle_result_contract_design_2026_05_08.py",
    ]
    checklist = [
        ("Mandatory GTOS preflight and controlling artifacts read", "context anchor records preflight and controlling inputs"),
        ("G12 corrected packet accepted as input-only source closure evidence", "rulebook starting_evidence_locked.g12_decision"),
        ("298 source_closed / 0 source_blocked_exact preserved", "universe ledger and rulebook starting evidence"),
        ("Row 0127 OTR061 hash and first terminal-area touch preserved", "rulebook, field requirements, and blocker ledger"),
        ("Six T3 rows and 94 blocked CNR061 rows excluded", "universe ledger exclusions"),
        ("Entry/fill/cancel/expiry semantics frozen", "frozen rulebook"),
        ("Quote/tick/lower-timeframe path evidence hierarchy frozen", "field requirements and parser"),
        ("Pending-intent closure fields frozen", "field requirements and blocker ledger"),
        ("Side-aware touch parser frozen", "touch/path parser"),
        ("Duplicate and sample-floor policy frozen", "duplicate/sample-floor policy"),
        ("Source-hash and no-leak/as-of schema frozen", "rulebook and noleak/asof schema"),
        ("Label-family separation preserved", "rulebook and noleak/asof schema"),
        ("Exact blocker rules written", "blocker ledger"),
        ("No result rows opened and no R/performance scored", "flags and current_result_opening_status"),
        ("Next-lane guidance written", "next prompt pack"),
    ]
    return {
        "artifact_family": "NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": generated_at,
        **BASE_FLAGS,
        "objective_restatement": (
            "Design and freeze the no-fill lifecycle closure result contract before any future outcome lane opens; "
            "do not score R/performance, do not inspect forbidden labels, preserve exclusions and safety flags, "
            "and produce machine-checkable artifacts plus next-lane guidance."
        ),
        "expected_artifacts": expected,
        "prompt_to_artifact_checklist": [
            {"requirement": req, "evidence": evidence, "status": "PENDING_VERIFIER"} for req, evidence in checklist
        ],
        "verification_results": {
            "status": "PENDING_RUN_VERIFY_SCRIPT",
            "can_mark_goal_complete": False,
        },
        "missing_or_weak_requirements": ["Verification has not yet been run for this generated audit."],
        "can_mark_goal_complete": False,
    }


def md_for_context(anchor: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Lane: `{anchor['lane']}`",
            f"Contract: `{anchor['contract_id']}`",
            f"Generated: `{anchor['generated_at_utc']}`",
            "",
            "## Boundaries",
            "",
            "- `NO_PROMOTION_VERDICT`",
            "- `validation_safe=false`",
            "- `outcome_review_opened=false`",
            "- `live_effect=false`",
            "- Result rows opened: `0`",
            "",
            "## Active Questions",
            "",
            bullet_lines(anchor["active_question_stack"]),
            "",
            "## Searched Roots",
            "",
            bullet_lines(anchor["searched_roots"]),
        ]
    )


def md_for_rulebook(rulebook: dict[str, Any]) -> str:
    facts = rulebook["starting_evidence_locked"]
    return "\n".join(
        [
            f"Contract: `{CONTRACT_ID}`",
            f"Status: `{rulebook['contract_status']}`",
            "",
            "## Locked Starting Evidence",
            "",
            f"- G12 decision: `{facts['g12_decision']}`",
            f"- Packet rows: `{facts['packet_rows']}`",
            f"- Source closed/source blocked exact: `{facts['source_closed']}` / `{facts['source_blocked_exact']}`",
            f"- Row 0127 OTR061 SHA256: `{facts['row_0127_source_sha256']}`",
            f"- Row 0127 first terminal-area touch: `{facts['row_0127_first_terminal_area_touch_utc']}`",
            "",
            "## Contract Boundary",
            "",
            rulebook["scope_boundary"]["what_this_contract_allows_next"],
            "",
            "This lane opens no result rows and forbids R/performance, broker/account/live/order/hidden labels, validation, promotion, and live effect.",
            "",
            "## Side-Aware Parser",
            "",
            "- LONG entry: `ask <= entry_price`; terminal: `bid >= terminal_area_price`; protective: `bid <= protective_level_price`.",
            "- SHORT entry: `bid >= entry_price`; terminal: `ask <= terminal_area_price`; protective: `ask >= protective_level_price`.",
            "- Same-timestamp conflicts are ambiguous.",
        ]
    )


def write_artifact_markdown(payloads: dict[str, dict[str, Any]]) -> None:
    write_md(
        f"NOFILL_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE_STAMP}.md",
        "NOFILL Result Contract Context Anchor",
        md_for_context(payloads["context_anchor"]),
    )
    write_md(
        f"NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE_STAMP}.md",
        "NOFILL Result Contract Frozen Rulebook",
        md_for_rulebook(payloads["rulebook"]),
    )
    universe = payloads["universe"]
    write_md(
        f"NOFILL_RESULT_CONTRACT_UNIVERSE_AND_EXCLUSION_LEDGER_{DATE_STAMP}.md",
        "NOFILL Result Contract Universe And Exclusion Ledger",
        "\n".join(
            [
                f"Packet rows: `{universe['source_packet']['packet_rows']}`",
                f"Source closed rows: `{universe['source_packet']['source_closed_rows']}`",
                f"Source blocked exact rows: `{universe['source_packet']['source_blocked_exact_rows']}`",
                f"Unique nofill duplicate keys: `{universe['source_packet']['nofill_duplicate_key_unique']}`",
                f"Unique duplicate groups: `{universe['source_packet']['duplicate_group_id_unique']}`",
                "",
                "Exclusions remain active: six CNR T3 rows and the 94 G12-blocked CNR061 rows.",
            ]
        ),
    )
    write_md(
        f"NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS_{DATE_STAMP}.md",
        "NOFILL Result Contract Field Source Requirements",
        "The JSON artifact is the machine-checkable source of truth for required identity, frozen decision, pending-intent, quote/tick, and lower-timeframe fields. Tick bid/ask path is required for side-aware touch ordering; M1/M5 OHLC remains price-compatible context unless a later quote-side contract is accepted.",
    )
    write_md(
        f"NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_{DATE_STAMP}.md",
        "NOFILL Result Contract Touch And Path Parser",
        "The parser is `bid_ask_side_aware_touch_times_v1`. LONG uses ask for entry and bid for terminal/protective. SHORT uses bid for entry and ask for terminal/protective. Same-timestamp or same-bar unresolved ordering blocks result labels.",
    )
    write_md(
        f"NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA_{DATE_STAMP}.md",
        "NOFILL Result Contract No-Leak Asof Schema",
        "Decision-time geometry is frozen at `decision_asof_utc`. Post-asof path and pending lifecycle events may be categorical labels only, never decision features. Broker/account/live/order/hidden/performance fields are forbidden.",
    )
    duplicate = payloads["duplicate_samplefloor"]
    write_md(
        f"NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_POLICY_{DATE_STAMP}.md",
        "NOFILL Result Contract Duplicate Sample-Floor Policy",
        "\n".join(
            [
                f"Current packet rows: `{duplicate['current_duplicate_state']['packet_rows']}`",
                f"Unique `nofill_duplicate_key`: `{duplicate['current_duplicate_state']['nofill_duplicate_key_unique']}`",
                f"Unique `duplicate_group_id`: `{duplicate['current_duplicate_state']['duplicate_group_id_unique']}`",
                "",
                "Row-level counts are source inventory only. Future validation must collapse duplicates and satisfy the frozen sample-floor rules in the JSON artifact.",
            ]
        ),
    )
    write_md(
        f"NOFILL_RESULT_CONTRACT_BLOCKER_LEDGER_{DATE_STAMP}.md",
        "NOFILL Result Contract Blocker Ledger",
        "The JSON artifact freezes exact blocker rules. Current upstream blockers remain blocker evidence; no row is rescued by performance, broker/account/live, hidden, or blocked CNR061 data.",
    )


def write_next_prompt_pack() -> None:
    body = f"""Run the next lane only after G12 accepts `{CONTRACT_ID}`.

Recommended next lane: `G12_NOFILL_LIFECYCLE_RESULT_CONTRACT_AUDIT_V1`.

Objective: audit the frozen no-fill lifecycle closure result contract under `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_result_contract_design/`. Decide accept/block/reject for the eligible universe, label-family separation, entry/fill/cancel/expiry semantics, side-aware parser, source hierarchy, pending-intent closure fields, duplicate/sample-floor policy, no-leak/as-of schema, source-hash policy, exact blockers, and next result-lane gates.

Starting facts to preserve:
- G12 corrected packet decision: `ACCEPT_CORRECTED_SOURCE_PACKET_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE`.
- Corrected source packet: `298 source_closed / 0 source_blocked_exact`.
- `NOFILL-CLOSE-ROW-0127` OTR061 SHA256: `{ROW_0127_EXPECTED_SHA256}`.
- `NOFILL-CLOSE-ROW-0127` first side-aware terminal-area touch: `{ROW_0127_FIRST_TOUCH}`.
- Six T3 rows and the 94 G12-blocked CNR061 rows remain excluded.

Hard boundaries: do not score R/performance; do not inspect broker/account/live/order/hidden labels; do not score blocked CNR061 rows or six T3 rows; do not use paid/API/Databento or MT5 order/account calls; do not edit registries, remotes, credentials, or live trading surfaces; do not claim validation, promotion, or live effect.

If G12 accepts this contract, the later result packet lane may categorize lifecycle closure states only. It must still emit row-level eligibility/blocker decisions before labels, re-run source hashes, verify duplicate/sample-floor status, and preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""
    write_md(
        f"NOFILL_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE_STAMP}.md",
        "NOFILL Result Contract Next Prompt Pack",
        body,
    )


def build_artifacts() -> dict[str, dict[str, Any]]:
    generated_at = now_utc()
    up = load_upstream()
    hashes = controlling_hashes()

    payloads = {
        "context_anchor": build_context_anchor(generated_at, hashes),
        "rulebook": build_rulebook(up, generated_at),
        "universe": build_universe(up, generated_at),
        "field_requirements": build_field_requirements(up, generated_at),
        "touch_parser": build_touch_parser(generated_at),
        "noleak_schema": build_noleak_schema(generated_at),
        "duplicate_samplefloor": build_duplicate_samplefloor(up, generated_at),
        "blocker_ledger": build_blocker_ledger(up, generated_at),
        "completion_audit": build_completion_audit(generated_at),
    }

    write_json(f"NOFILL_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE_STAMP}.json", payloads["context_anchor"])
    write_json(f"NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE_STAMP}.json", payloads["rulebook"])
    write_json(f"NOFILL_RESULT_CONTRACT_UNIVERSE_AND_EXCLUSION_LEDGER_{DATE_STAMP}.json", payloads["universe"])
    write_json(f"NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS_{DATE_STAMP}.json", payloads["field_requirements"])
    write_json(f"NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_{DATE_STAMP}.json", payloads["touch_parser"])
    write_json(f"NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA_{DATE_STAMP}.json", payloads["noleak_schema"])
    write_json(f"NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_POLICY_{DATE_STAMP}.json", payloads["duplicate_samplefloor"])
    write_json(f"NOFILL_RESULT_CONTRACT_BLOCKER_LEDGER_{DATE_STAMP}.json", payloads["blocker_ledger"])
    write_json(f"NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.json", payloads["completion_audit"])
    write_artifact_markdown(payloads)
    write_next_prompt_pack()
    write_md(
        f"NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.md",
        "NOFILL Result Contract Completion Audit",
        "Generated completion audit is pending verifier finalization. Run `verify_nofill_lifecycle_result_contract_design_2026_05_08.py`.",
    )
    return payloads


def main() -> None:
    payloads = build_artifacts()
    print(
        json.dumps(
            {
                "status": "BUILT",
                "contract_id": CONTRACT_ID,
                "generated_artifacts": len(RESULT_JSON_NAMES) + 9,
                "packet_rows": payloads["universe"]["source_packet"]["packet_rows"],
                "result_rows_opened": 0,
                **BASE_FLAGS,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
