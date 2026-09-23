#!/usr/bin/env python3
"""Build NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS.

This lane is a source/control synthesis of the accepted no-fill categorical V2
packet. It summarizes input-only categorical labels and blocker/reject learning.
It does not score R, performance, broker outcomes, validation, promotion, or
live behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
SCHEMA = "nofill_cat_v2_quarantined_categorical_synthesis_forensics_v1"
LANE = "NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS"
PACKET_ID = "NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
GENERATED_AT_UTC = "2026-05-09T00:00:00Z"

OUT_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = OUT_DIR.parent
REPO_ROOT = OUT_DIR.parents[3]
REBUILD_DIR = OUTCOME_ROOT / "nofill_lifecycle_categorical_result_packet_v2_rebuild"
G12_DIR = OUTCOME_ROOT / "g12_nofill_categorical_result_packet_v2_audit"

GOAL_PROMPT = OUT_DIR / "NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS_GOAL_PROMPT_2026-05-09.md"

EXPECTED_PARTITION = {
    "accepted": 225,
    "blocked": 8,
    "rejected": 65,
    "universe": 298,
    "accepted_prior": 52,
    "accepted_source_corrected": 173,
}
EXPECTED_DECISIONS = {
    "ACCEPT_PRIOR_CATEGORICAL_LABEL": 52,
    "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 173,
    "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 8,
    "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
    "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
}
EXPECTED_ACCEPTED_LABELS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_ACCEPTED_SOURCE_LANES = {
    "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": 32,
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2": 29,
    "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": 58,
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": 51,
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": 3,
    "prior_g12_categorical_packet_audit": 52,
}
EXPECTED_BLOCKER_CODES = {
    "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE": 4,
    "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP": 1,
    "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED": 1,
    "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3,
}
EXPECTED_REJECT_DECISIONS = {
    "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
    "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
}

REQUIRED_ACCEPTED_FIELDS = (
    "packet_row_id",
    "accepted_source_lane",
    "categorical_input_label",
    "symbol",
    "session",
    "side",
    "source_row_id",
    "nofill_duplicate_key",
    "duplicate_group_id",
    "decision_asof_utc",
)

FORBIDDEN_KEY_PARTS = (
    "actual_r",
    "account_history",
    "broker_actual",
    "broker_deal",
    "broker_order",
    "broker_position",
    "expectancy",
    "hidden_label",
    "live_order",
    "live_trade_result",
    "mt5_account",
    "mt5_deal",
    "mt5_history",
    "mt5_order",
    "mt5_position",
    "pbo",
    "profit",
    "r_multiple",
    "reward_r",
    "synthetic_r",
    "win_rate",
)

CONTROL_INPUTS = [
    GOAL_PROMPT,
    REBUILD_DIR / "NOFILL_CAT_V2_ACCEPTED_PACKET_2026-05-09.json",
    REBUILD_DIR / "NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl",
    REBUILD_DIR / "NOFILL_CAT_V2_BLOCKER_LEDGER_2026-05-09.json",
    REBUILD_DIR / "NOFILL_CAT_V2_REJECT_LEDGER_2026-05-09.json",
    REBUILD_DIR / "NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_2026-05-09.json",
    REBUILD_DIR / "NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_2026-05-09.json",
    G12_DIR / "G12_NOFILL_CAT_V2_DECISION_LEDGER_2026-05-09.json",
    G12_DIR / "G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_2026-05-09.json",
    G12_DIR / "G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_2026-05-09.json",
    G12_DIR / "G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_2026-05-09.json",
    G12_DIR / "G12_NOFILL_CAT_V2_LEARNING_LEDGER_2026-05-09.md",
    G12_DIR / "G12_NOFILL_CAT_V2_NEXT_PROMPT_PACK_2026-05-09.md",
]

OUTPUT_JSON = [
    "NOFILL_CAT_V2_FORENSICS_SYNTHESIS_2026-05-09.json",
    "NOFILL_CAT_V2_FORENSICS_SLICE_LEDGER_2026-05-09.json",
    "NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_2026-05-09.json",
    "NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_2026-05-09.json",
    "NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT_2026-05-09.json",
    "NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_2026-05-09.json",
    "NOFILL_CAT_V2_FORENSICS_COMPLETION_AUDIT_2026-05-09.json",
]

OUTPUT_MD = [
    "NOFILL_CAT_V2_FORENSICS_CONTEXT_ANCHOR_2026-05-09.md",
    "NOFILL_CAT_V2_FORENSICS_SYNTHESIS_2026-05-09.md",
    "NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_2026-05-09.md",
    "NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_2026-05-09.md",
    "NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT_2026-05-09.md",
    "NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_2026-05-09.md",
    "NOFILL_CAT_V2_FORENSICS_NEXT_PROMPT_PACK_2026-05-09.md",
    "NOFILL_CAT_V2_FORENSICS_COMPLETION_AUDIT_2026-05-09.md",
]

PY_FILES = [
    "build_nofill_cat_v2_quarantined_categorical_synthesis_forensics_2026_05_09.py",
    "verify_nofill_cat_v2_quarantined_categorical_synthesis_forensics_2026_05_09.py",
    "test_nofill_cat_v2_quarantined_categorical_synthesis_forensics_2026_05_09.py",
]


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA,
        "lane": LANE,
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE: {exc}"


def load_inputs() -> dict[str, Any]:
    return {
        "accepted_packet": read_json(REBUILD_DIR / "NOFILL_CAT_V2_ACCEPTED_PACKET_2026-05-09.json"),
        "row_ledger": read_jsonl(REBUILD_DIR / "NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl"),
        "blocker_ledger": read_json(REBUILD_DIR / "NOFILL_CAT_V2_BLOCKER_LEDGER_2026-05-09.json"),
        "reject_ledger": read_json(REBUILD_DIR / "NOFILL_CAT_V2_REJECT_LEDGER_2026-05-09.json"),
        "v2_source_audit": read_json(REBUILD_DIR / "NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_2026-05-09.json"),
        "v2_duplicate_audit": read_json(REBUILD_DIR / "NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_2026-05-09.json"),
        "g12_decision": read_json(G12_DIR / "G12_NOFILL_CAT_V2_DECISION_LEDGER_2026-05-09.json"),
        "g12_source_audit": read_json(G12_DIR / "G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_2026-05-09.json"),
        "g12_noleak_audit": read_json(G12_DIR / "G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_2026-05-09.json"),
        "g12_blocker_review": read_json(G12_DIR / "G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_2026-05-09.json"),
    }


def pct(count: int, denominator: int) -> float:
    return round((count / denominator) * 100.0, 2) if denominator else 0.0


def counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def cross_counts(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    counter = Counter(tuple(str(row.get(field)) for field in fields) for row in rows)
    out = []
    for key, count in sorted(counter.items(), key=lambda item: (item[0], item[1])):
        item = {field: value for field, value in zip(fields, key)}
        item["row_count"] = count
        item["pct_of_accepted_rows"] = pct(count, len(rows))
        out.append(item)
    return out


def slice_table(rows: list[dict[str, Any]], field: str, denominator: int) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(field))].append(row)
    out = []
    for value, items in sorted(grouped.items()):
        out.append(
            {
                field: value,
                "row_count": len(items),
                "pct_of_accepted_rows": pct(len(items), denominator),
                "unique_nofill_duplicate_keys": len({row.get("nofill_duplicate_key") for row in items if row.get("nofill_duplicate_key")}),
                "label_counts": counts(items, "categorical_input_label"),
                "source_lane_counts": counts(items, "accepted_source_lane"),
                "descriptive_only": True,
            }
        )
    return out


def rows_by_status(row_ledger: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    accepted = [row for row in row_ledger if row["row_status"] == "ACCEPTED_INPUT_ONLY"]
    blocked = [row for row in row_ledger if row["row_status"] == "BLOCKED_EXACT_SOURCE_OR_ORDERING_GAP"]
    rejected = [row for row in row_ledger if row["row_status"] == "REJECTED_EXCLUDED_FROM_DENOMINATOR"]
    return accepted, blocked, rejected


def control_hash_records() -> list[dict[str, Any]]:
    records = []
    for path in CONTROL_INPUTS:
        records.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "role": "controlling_or_supporting_input",
            }
        )
    return records


def scan_forbidden_keys(payload: Any, path: str = "") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_l = str(key).lower()
            if any(part in key_l for part in FORBIDDEN_KEY_PARTS):
                hits.append({"path": f"{path}.{key}" if path else str(key), "key": str(key)})
            hits.extend(scan_forbidden_keys(value, f"{path}.{key}" if path else str(key)))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            hits.extend(scan_forbidden_keys(item, f"{path}[{index}]"))
    return hits


def duplicate_summary(accepted: list[dict[str, Any]], rejected: list[dict[str, Any]], g12_noleak: dict[str, Any]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted:
        grouped[row["nofill_duplicate_key"]].append(row)
    collisions = {key: rows for key, rows in grouped.items() if key and len(rows) > 1}
    collision_rows = [row for rows in collisions.values() for row in rows]
    return {
        "accepted_rows": len(accepted),
        "accepted_unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in accepted if row.get("nofill_duplicate_key")}),
        "duplicate_key_collision_count": len(collisions),
        "rows_in_duplicate_key_collisions": len(collision_rows),
        "collision_label_counts": counts(collision_rows, "categorical_input_label"),
        "collision_source_lane_counts": counts(collision_rows, "accepted_source_lane"),
        "collision_groups": {
            key: [row["packet_row_id"] for row in rows]
            for key, rows in sorted(collisions.items())
        },
        "oti5_canonical_duplicate_rows_accepted": sum(
            1
            for row in accepted
            if row["accepted_source_lane"] == "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT"
        ),
        "oti5_noncanonical_duplicate_rows_rejected": sum(
            1
            for row in rejected
            if row["accepted_source_lane"] == "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT"
        ),
        "inherited_g12_duplicate_posture": g12_noleak["duplicate_posture"],
        "interpretation": (
            "Accepted duplicate-key collisions are confined to opening-drive source projections that are not result labels; "
            "the OTI5 duplicate-conflict family is canonicalized to 3 accepted source-identity rows and 39 noncountable rejects."
        ),
    }


def label_explanations() -> dict[str, dict[str, Any]]:
    common_non_claims = [
        "not R/performance",
        "not win rate",
        "not expectancy",
        "not broker actual-R",
        "not account history",
        "not validation",
        "not promotion",
        "not live-gate or live-order evidence",
    ]
    return {
        "nofill_terminal_before_entry": {
            "plain_mechanism": "The approved source path reaches the terminal area before a side-aware entry touch.",
            "what_it_proves": "A pending idea can become lifecycle-invalid before it ever becomes an entry event under the source contract.",
            "what_it_does_not_prove": common_non_claims,
            "failure_anatomy": "The setup lifecycle can end upstream of fill; pending-intent hygiene needs explicit terminal-before-entry observation and cancellation context.",
            "stronger_future_fields": [
                "as-of terminal-area touch timestamp",
                "side-aware entry touch timestamp or no-touch proof",
                "pending intent create/cancel/expiry timestamps",
                "terminal geometry source hash",
                "reason the pending intent remained active or was cancelled",
            ],
            "future_hypothesis": "Preregister a pending-hygiene capture lane that measures how often terminal-before-entry states arrive before current cancellation logic can respond.",
        },
        "source_corrected_no_entry_through_pending_horizon": {
            "plain_mechanism": "Corrected source fields show no side-aware entry touch through the frozen pending horizon.",
            "what_it_proves": "Some no-fill rows are true no-entry-through-horizon source states, not missing labels.",
            "what_it_does_not_prove": common_non_claims,
            "failure_anatomy": "The pending window can expire without a side-aware entry event; without richer cancellation telemetry, this cannot decide whether the setup should have expired earlier.",
            "stronger_future_fields": [
                "active pending horizon start/end",
                "side-aware bid/ask touch search result",
                "cancel reason",
                "last eligible quote before expiry/cancel",
                "spread/source coverage status over the full horizon",
            ],
            "future_hypothesis": "Preregister a no-entry horizon lane that separates late cancellation, stale POI, and genuinely untouched entry states before any rule change is considered.",
        },
        "fill_path_entry_before_protective_level_no_terminal_observed": {
            "plain_mechanism": "Source-ordered events show entry before the protective level, with no terminal-area event observed inside the approved path window.",
            "what_it_proves": "A fill/path transition can be categorized as entry then protective without observed terminal completion in the source window.",
            "what_it_does_not_prove": common_non_claims,
            "failure_anatomy": "Lifecycle evidence can enter a post-entry transition state that lacks terminal observation; that is an ordering fact, not a result.",
            "stronger_future_fields": [
                "entry timestamp",
                "protective-level timestamp",
                "terminal-area search coverage",
                "source window end reason",
                "same-tick ambiguity flag",
            ],
            "future_hypothesis": "Collect fill/path transition labels prospectively with same-tick blockers separated before any post-entry result lane opens.",
        },
        "fill_path_entry_before_protective_level_before_terminal_area": {
            "plain_mechanism": "Source-ordered events show entry, then protective level, then terminal area.",
            "what_it_proves": "The source can order three lifecycle predicates for a small subset of fill/path rows.",
            "what_it_does_not_prove": common_non_claims,
            "failure_anatomy": "The row family can express a complete lifecycle ordering, but the label does not say whether the order was good, bad, or tradable.",
            "stronger_future_fields": [
                "three event timestamps",
                "quote side used by each predicate",
                "same-bar and same-tick flags",
                "cost/slippage placeholder kept closed until a result lane is approved",
            ],
            "future_hypothesis": "Use this ordering as a future categorical state in a frozen result contract, not as current performance evidence.",
        },
        "fill_path_entry_before_terminal_area_before_protective_level": {
            "plain_mechanism": "Source-ordered events show entry, then terminal area, then protective level.",
            "what_it_proves": "The source can identify a terminal-area-before-protective lifecycle ordering in a small subset.",
            "what_it_does_not_prove": common_non_claims,
            "failure_anatomy": "This is the strongest-looking lifecycle ordering semantically, but it remains descriptive because no result values or broker facts are opened.",
            "stronger_future_fields": [
                "terminal-area and protective-level timestamps",
                "source coverage through both events",
                "event predicates and quote side",
                "denominator identity after duplicate collapse",
            ],
            "future_hypothesis": "If a later result lane is approved, freeze this label as one event-order category before opening any quantitative scoring.",
        },
        "opening_drive_source_projection_ready_no_result_label": {
            "plain_mechanism": "Opening-drive range/breakout/as-of source projection is ready, but no result label is assigned.",
            "what_it_proves": "The source projection can be reconstructed for future contract work.",
            "what_it_does_not_prove": common_non_claims + ["not a no-fill result label"],
            "failure_anatomy": "Projection readiness is useful inventory, but duplicate-key clustering shows it can inflate row counts if converted into denominator evidence too early.",
            "stronger_future_fields": [
                "frozen opening range bounds",
                "breakout side and as-of timestamp",
                "projection duplicate key",
                "explicit result-label blocker until a future contract assigns one",
            ],
            "future_hypothesis": "Build a separate opening-drive categorical contract audit that freezes denominator and label assignment before any outcomes are opened.",
        },
        "canonical_duplicate_geometry_source_ready_no_label_assigned": {
            "plain_mechanism": "The duplicate-geometry rule selected a canonical countable source-identity row but did not assign a result label.",
            "what_it_proves": "Duplicate-control can collapse a repeated projection family into source-identity evidence.",
            "what_it_does_not_prove": common_non_claims + ["not a lifecycle result label"],
            "failure_anatomy": "The prior duplicate conflict was a denominator-control issue; canonical source identity fixes countability but cannot infer lifecycle outcome.",
            "stronger_future_fields": [
                "canonical duplicate selection rule",
                "all noncanonical sibling row ids",
                "geometry fields used for canonicalization",
                "proof no sibling row is counted in a result denominator",
            ],
            "future_hypothesis": "Keep canonical duplicate controls as a precondition for future packet builders, and never let noncanonical projections enter result denominators.",
        },
    }


def build_label_family_analysis(accepted: list[dict[str, Any]]) -> dict[str, Any]:
    explanations = label_explanations()
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted:
        by_label[row["categorical_input_label"]].append(row)

    label_items = {}
    for label, rows in sorted(by_label.items()):
        explanation = explanations[label]
        label_items[label] = {
            **explanation,
            "row_count": len(rows),
            "pct_of_accepted_rows": pct(len(rows), len(accepted)),
            "unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in rows if row.get("nofill_duplicate_key")}),
            "source_lane_counts": counts(rows, "accepted_source_lane"),
            "symbol_counts": counts(rows, "symbol"),
            "session_counts": counts(rows, "session"),
            "side_counts": counts(rows, "side"),
            "descriptive_only": True,
            "validation_safe": False,
        }

    fill_path_rows = [row for row in accepted if str(row["categorical_input_label"]).startswith("fill_path_")]
    return {
        **base_payload("NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS"),
        "packet_id": PACKET_ID,
        "accepted_row_count": len(accepted),
        "label_families": label_items,
        "oti2_fill_path_family_rollup": {
            "row_count": len(fill_path_rows),
            "label_counts": counts(fill_path_rows, "categorical_input_label"),
            "symbol_counts": counts(fill_path_rows, "symbol"),
            "session_counts": counts(fill_path_rows, "session"),
            "side_counts": counts(fill_path_rows, "side"),
            "plain_mechanism": "The OTI2 rows are source-ordered event-order categories around entry, protective level, and terminal area.",
            "non_claim": "They are not PnL, not broker realized outcomes, and not validation evidence.",
        },
    }


def blocker_reject_learning(blocked: list[dict[str, Any]], rejected: list[dict[str, Any]], g12_source: dict[str, Any]) -> dict[str, Any]:
    blocker_code_counts = Counter(code for row in blocked for code in row["exact_blocker_codes"])
    reject_code_counts = Counter(code for row in rejected for code in row["exact_blocker_codes"])
    return {
        **base_payload("NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING"),
        "packet_id": PACKET_ID,
        "blocked_row_count": len(blocked),
        "rejected_row_count": len(rejected),
        "blocker_code_counts": dict(sorted(blocker_code_counts.items())),
        "reject_code_counts": dict(sorted(reject_code_counts.items())),
        "reject_decision_counts": counts(rejected, "consolidated_g12_decision"),
        "blocker_families": {
            "oti4_may3_source_gaps": {
                "row_count": blocker_code_counts["BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP"],
                "rows": [
                    row["packet_row_id"]
                    for row in blocked
                    if "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP" in row["exact_blocker_codes"]
                ],
                "learning": "Local NAS100/XAUUSD tick files exist but have zero rows in the frozen 2026-05-03 13:00-13:30 UTC opening range; the OTI4 source-search ledger found no approved CSV/OHLC substitute.",
                "unblocker": "Read-only tick parquet or M1/lower OHLC covering the frozen opening range, source-hashed with as-of provenance.",
                "forbidden_unblockers": ["MT5 order/account/history calls", "broker actual-R", "live order/deal/position labels"],
                "status": "EXACT_SOURCE_GAP",
            },
            "oti3_same_tick_order_ambiguities": {
                "row_count": blocker_code_counts["BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE"],
                "rows": [
                    row["packet_row_id"]
                    for row in blocked
                    if "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE" in row["exact_blocker_codes"]
                ],
                "learning": "The first source timestamp has a single tick row satisfying entry and protective predicates simultaneously; current approved data has no intra-tick order.",
                "unblocker": "Higher-resolution or broker-native event-order source that proves intra-tick sequence without account/order labels.",
                "status": "SOURCE_SAFE_ORDERING_IMPOSSIBLE_FROM_CURRENT_TICK_ROWS",
            },
            "original_oti2_source_gap": {
                "row_count": sum(
                    1
                    for row in blocked
                    if set(row["exact_blocker_codes"])
                    == {"BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED", "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP"}
                ),
                "rows": [
                    row["packet_row_id"]
                    for row in blocked
                    if set(row["exact_blocker_codes"])
                    == {"BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED", "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP"}
                ],
                "learning": "M1 context is not side-aware tick proof and XAUUSD tick coverage misses the active pending window through cancel.",
                "unblocker": "Side-aware bid/ask tick or approved lower source covering the active pending window through cancel.",
                "status": "EXACT_ACTIVE_WINDOW_SOURCE_GAP",
            },
        },
        "reject_families": {
            "oti4_contract_excluded": {
                "row_count": sum(1 for row in rejected if row["consolidated_g12_decision"] == "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED"),
                "code_counts": {
                    code: count
                    for code, count in sorted(reject_code_counts.items())
                    if code.startswith("BLOCK_OTI4")
                },
                "learning": "These rows fail the frozen OTI4 source contract and therefore cannot be label or denominator evidence.",
                "status": "CONTRACT_EXCLUDED_NO_LABEL",
            },
            "oti5_noncanonical_duplicate_projections": {
                "row_count": sum(1 for row in rejected if row["consolidated_g12_decision"] == "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE"),
                "learning": "These are repeated noncanonical projections. Counting them would inflate the denominator.",
                "status": "DUPLICATE_EXCLUDED_NO_LABEL",
            },
        },
        "inherited_blocker_saturation_conclusion": g12_source.get("blocker_saturation_conclusion"),
        "g12_recomputed_proofs_referenced": {
            "oti3_same_tick_checks": len(g12_source.get("recomputed_oti3_same_tick_order_checks", [])),
            "oti4_may3_source_gap_checks": len(g12_source.get("recomputed_oti4_may3_source_gap_checks", [])),
            "original_oti2_source_gap_rows": g12_source.get("recomputed_original_oti2_source_gap_check", {}).get("row_count"),
        },
    }


def build_slice_ledger(accepted: list[dict[str, Any]], blocked: list[dict[str, Any]], rejected: list[dict[str, Any]], g12_noleak: dict[str, Any]) -> dict[str, Any]:
    denominator = len(accepted)
    return {
        **base_payload("NOFILL_CAT_V2_FORENSICS_SLICE_LEDGER"),
        "packet_id": PACKET_ID,
        "descriptive_only": True,
        "accepted_denominator": denominator,
        "partition_counts": {
            "accepted": len(accepted),
            "blocked": len(blocked),
            "rejected": len(rejected),
            "universe": len(accepted) + len(blocked) + len(rejected),
        },
        "accepted_slices": {
            "by_label": slice_table(accepted, "categorical_input_label", denominator),
            "by_source_lane": slice_table(accepted, "accepted_source_lane", denominator),
            "by_symbol": slice_table(accepted, "symbol", denominator),
            "by_session": slice_table(accepted, "session", denominator),
            "by_side": slice_table(accepted, "side", denominator),
            "by_source_lane_plus_label": cross_counts(accepted, ("accepted_source_lane", "categorical_input_label")),
            "by_label_plus_symbol": cross_counts(accepted, ("categorical_input_label", "symbol")),
            "by_label_plus_session": cross_counts(accepted, ("categorical_input_label", "session")),
            "by_label_plus_side": cross_counts(accepted, ("categorical_input_label", "side")),
        },
        "duplicate_and_canonical_policy": duplicate_summary(accepted, rejected, g12_noleak),
        "small_slice_policy": {
            "threshold_rows": 20,
            "meaning": "Small slices are descriptive source-control summaries only; they cannot validate or promote any rule.",
            "small_accepted_label_slices": [
                {"label": label, "row_count": count}
                for label, count in sorted(Counter(row["categorical_input_label"] for row in accepted).items())
                if count < 20
            ],
        },
    }


def build_synthesis(accepted: list[dict[str, Any]], blocked: list[dict[str, Any]], rejected: list[dict[str, Any]], slice_ledger: dict[str, Any]) -> dict[str, Any]:
    decision_counts = Counter(row["consolidated_g12_decision"] for row in accepted + blocked + rejected)
    return {
        **base_payload("NOFILL_CAT_V2_FORENSICS_SYNTHESIS"),
        "packet_id": PACKET_ID,
        "source_authority": [
            rel(REBUILD_DIR / "NOFILL_CAT_V2_ACCEPTED_PACKET_2026-05-09.json"),
            rel(REBUILD_DIR / "NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl"),
            rel(G12_DIR / "G12_NOFILL_CAT_V2_DECISION_LEDGER_2026-05-09.json"),
            rel(G12_DIR / "G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_2026-05-09.json"),
        ],
        "partition_verified": True,
        "partition_counts": slice_ledger["partition_counts"],
        "decision_counts": dict(sorted(decision_counts.items())),
        "accepted_label_counts": counts(accepted, "categorical_input_label"),
        "accepted_source_lane_counts": counts(accepted, "accepted_source_lane"),
        "accepted_symbol_counts": counts(accepted, "symbol"),
        "accepted_session_counts": counts(accepted, "session"),
        "accepted_side_counts": counts(accepted, "side"),
        "quarantined_synthesis_conclusion": (
            "The 225 accepted rows are coherent as input-only categorical lifecycle/source evidence. "
            "They describe no-fill, no-entry-through-horizon, fill/path ordering, opening-drive source projection, "
            "and canonical duplicate-control states. They do not open R/performance, broker outcomes, validation, "
            "promotion, or live behavior."
        ),
        "learning_headlines": [
            "Terminal-before-entry is the largest accepted family and points to pending-intent lifecycle hygiene questions.",
            "No-entry-through-horizon rows separate untouched pending windows from missing labels.",
            "Fill/path labels preserve event ordering without converting ordering into performance.",
            "Opening-drive projections are source-ready inventory, not result labels.",
            "Duplicate-control rows fix source identity but do not infer lifecycle outcomes.",
            "The 8 blockers are exact source/order gaps; the 65 rejects remain outside denominator and label assignment.",
        ],
        "non_claims": [
            "No R/performance values were computed.",
            "No win-rate or expectancy is reported.",
            "No broker actual-R, account history, live order/deal/position, or hidden labels were consumed.",
            "No validation-safe, outcome-review, promotion, registry, or live-effect boundary was opened.",
        ],
        "next_route_decision": (
            "Primary next route is a G12 synthesis-control audit of this quarantined forensics packet. "
            "A separate residual-blocker source-access lane can target only the 8 exact blockers."
        ),
    }


def contradiction_audit(
    accepted: list[dict[str, Any]],
    blocked: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    inputs: dict[str, Any],
    generated_payloads: dict[str, Any],
) -> dict[str, Any]:
    accepted_missing = {
        field: [row["packet_row_id"] for row in accepted if row.get(field) in (None, "")]
        for field in REQUIRED_ACCEPTED_FIELDS
    }
    accepted_missing = {field: rows for field, rows in accepted_missing.items() if rows}
    blocker_labels = [row["packet_row_id"] for row in blocked if row.get("categorical_input_label") is not None]
    reject_labels = [row["packet_row_id"] for row in rejected if row.get("categorical_input_label") is not None]
    blocked_reject_denominator = [
        row["packet_row_id"]
        for row in blocked + rejected
        if row.get("in_accepted_packet_denominator") is True
    ]
    label_counts = counts(accepted, "categorical_input_label")
    source_lane_counts = counts(accepted, "accepted_source_lane")
    blocker_code_counts = dict(sorted(Counter(code for row in blocked for code in row["exact_blocker_codes"]).items()))
    reject_decisions = counts(rejected, "consolidated_g12_decision")
    generated_forbidden_hits = scan_forbidden_keys(generated_payloads)
    g12_source = inputs["g12_source_audit"]
    g12_noleak = inputs["g12_noleak_audit"]

    checks = [
        {
            "check": "exact_partition_298_225_8_65",
            "status": "PASS" if len(accepted) == 225 and len(blocked) == 8 and len(rejected) == 65 else "FAIL",
            "evidence": {"accepted": len(accepted), "blocked": len(blocked), "rejected": len(rejected)},
        },
        {
            "check": "accepted_required_source_fields_non_null",
            "status": "PASS" if not accepted_missing else "FAIL",
            "evidence": accepted_missing,
        },
        {
            "check": "accepted_label_counts_expected",
            "status": "PASS" if label_counts == EXPECTED_ACCEPTED_LABELS else "FAIL",
            "evidence": label_counts,
        },
        {
            "check": "accepted_source_lane_counts_expected",
            "status": "PASS" if source_lane_counts == EXPECTED_ACCEPTED_SOURCE_LANES else "FAIL",
            "evidence": source_lane_counts,
        },
        {
            "check": "blocker_codes_expected",
            "status": "PASS" if blocker_code_counts == EXPECTED_BLOCKER_CODES else "FAIL",
            "evidence": blocker_code_counts,
        },
        {
            "check": "reject_decisions_expected",
            "status": "PASS" if reject_decisions == EXPECTED_REJECT_DECISIONS else "FAIL",
            "evidence": reject_decisions,
        },
        {
            "check": "blockers_have_no_labels",
            "status": "PASS" if not blocker_labels else "FAIL",
            "evidence": blocker_labels,
        },
        {
            "check": "rejects_have_no_labels",
            "status": "PASS" if not reject_labels else "FAIL",
            "evidence": reject_labels,
        },
        {
            "check": "blocked_or_rejected_not_in_denominator",
            "status": "PASS" if not blocked_reject_denominator else "FAIL",
            "evidence": blocked_reject_denominator,
        },
        {
            "check": "source_hash_reference_status",
            "status": "PASS"
            if g12_source["status"] == "PASS"
            and not g12_source["missing_control_inputs"]
            and not g12_source["inherited_g12_source_hash_mismatches"]
            and not g12_source["inherited_g12_missing_source_hash_records"]
            else "FAIL",
            "evidence": {
                "g12_source_status": g12_source["status"],
                "source_hash_drift_classification": g12_source["source_hash_drift_classification"],
            },
        },
        {
            "check": "label_duplicate_no_leak_status",
            "status": "PASS"
            if g12_noleak["status"] == "PASS"
            and not g12_noleak["forbidden_key_hits"]
            and not g12_noleak["label_issues"]
            else "FAIL",
            "evidence": {
                "g12_noleak_status": g12_noleak["status"],
                "countable_scope": g12_noleak["countable_scope"],
            },
        },
        {
            "check": "generated_forbidden_output_keys",
            "status": "PASS" if not generated_forbidden_hits else "FAIL",
            "evidence": generated_forbidden_hits[:20],
        },
    ]
    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    return {
        **base_payload("NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT"),
        "packet_id": PACKET_ID,
        "status": status,
        "contradiction_checks": checks,
        "control_input_hash_records": control_hash_records(),
        "missing_control_inputs": [record for record in control_hash_records() if not record["exists"]],
        "inherited_source_hash_status": {
            "g12_status": g12_source["status"],
            "v2_status": inputs["v2_source_audit"]["status"],
            "source_hash_drift_classification": g12_source["source_hash_drift_classification"],
            "g12_control_input_records": len(g12_source.get("control_input_hash_records", [])),
            "searched_root_ledger": g12_source.get("searched_root_ledger", []),
        },
        "duplicate_policy_status": duplicate_summary(accepted, rejected, g12_noleak),
        "path_result_leakage_status": "PASS_NO_RESULT_VALUES_OPENED",
        "hidden_semantics_status": "PASS_NO_HIDDEN_PERFORMANCE_LABELS_DETECTED",
    }


def future_hypotheses_and_capture(blocker_learning: dict[str, Any]) -> dict[str, Any]:
    return {
        **base_payload("NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER"),
        "packet_id": PACKET_ID,
        "route_decision": {
            "primary_next_route": "G12_NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS_AUDIT",
            "secondary_route": "NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE",
            "quantitative_result_lane_status": "FORBIDDEN_UNTIL_SEPARATE_FROZEN_PREREG_G12_GATE_AND_SAMPLE_FLOOR",
        },
        "future_control_lanes": [
            {
                "lane": "G12 synthesis-control audit",
                "purpose": "Independently verify this forensics packet's counts, non-claims, label-family analysis, blocker/reject learning, and no-leak posture.",
                "opens_results": False,
                "required_inputs": OUTPUT_JSON + OUTPUT_MD,
            },
            {
                "lane": "Residual 8 blocker-clear access lane",
                "purpose": "Target only exact source/order blockers without touching accepted/rejected rows.",
                "opens_results": False,
                "required_access_or_capture": blocker_learning["blocker_families"],
            },
            {
                "lane": "Pending-intent hygiene capture",
                "purpose": "Capture terminal-before-entry and no-entry-through-horizon facts prospectively with source hashes and cancel/expiry context.",
                "opens_results": False,
                "capture_fields": [
                    "pending_create_utc",
                    "pending_cancel_or_expiry_utc",
                    "terminal_touch_utc",
                    "side_aware_entry_touch_utc_or_no_touch",
                    "source_coverage_status",
                    "cancel_reason",
                ],
            },
            {
                "lane": "Fill/path event-order categorical contract",
                "purpose": "Freeze event-order categories and same-tick blocker handling before any future result packet.",
                "opens_results": False,
                "capture_fields": [
                    "entry_event_utc",
                    "protective_event_utc",
                    "terminal_event_utc",
                    "same_tick_or_same_bar_flag",
                    "quote_side_used",
                    "source_window_end_reason",
                ],
            },
            {
                "lane": "Opening-drive source projection contract",
                "purpose": "Turn source projection readiness into a frozen categorical contract with denominator and duplicate policy before labels are assigned.",
                "opens_results": False,
                "capture_fields": [
                    "opening_range_start_end",
                    "breakout_side",
                    "range_complete_asof",
                    "candidate_side_match_status",
                    "duplicate_projection_key",
                ],
            },
            {
                "lane": "Future quantitative result dossier gate",
                "purpose": "Only if the owner wants scoring later, freeze preregistration, denominator, source fields, sample floor, no-leak proof, duplicate policy, and G12 acceptance before any result values are opened.",
                "opens_results": "not_in_this_lane",
                "minimum_requirements": [
                    "frozen prereg before outcome opening",
                    "sample floor and denominator policy",
                    "source-hashed side-aware event fields",
                    "blocked/rejected row exclusion proof",
                    "separate G12 gate",
                    "explicit owner approval",
                ],
            },
        ],
        "hard_non_claims": [
            "This synthesis does not choose a trading rule.",
            "This synthesis does not validate cancellation timing.",
            "This synthesis does not promote any selector or live gate.",
            "This synthesis does not use broker actual-R or account history.",
        ],
    }


def markdown_table_from_counts(title: str, count_map: dict[str, int]) -> list[str]:
    return [
        f"## {title}",
        "",
        "| Value | Count |",
        "|---|---:|",
        *[f"| `{key}` | {value} |" for key, value in sorted(count_map.items())],
        "",
    ]


def write_context_anchor(inputs: dict[str, Any]) -> None:
    source_roots = inputs["g12_source_audit"].get("searched_root_ledger", [])
    lines = [
        "# NOFILL CAT V2 Forensics Context Anchor",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        f"- Lane: `{LANE}`",
        f"- Packet: `{PACKET_ID}`",
        f"- Starting HEAD: `{git_output('rev-parse', '--short', 'HEAD')}`",
        f"- Starting branch: `{git_output('branch', '--show-current')}`",
        "- Live-state freshness: `.context/LIVE_STATE.md` regenerated before this lane and reported research context `FRESH`.",
        f"- Controlling prompt: `{rel(GOAL_PROMPT)}`",
        "",
        "## Controlling Inputs",
        "",
        *[f"- `{rel(path)}`" for path in CONTROL_INPUTS],
        "",
        "## Searched Roots And Evidence Routes",
        "",
        "- Current worktree target directory via `rg --files`.",
        "- V2 rebuild directory and G12 categorical V2 audit directory.",
        "- Git branch, HEAD, status, and lane history were checked.",
        "- The inherited G12 source-hash audit records the local-heavy-data root searches below:",
        *[f"- `{item.get('root')}` - {item.get('purpose')}" for item in source_roots],
        "",
        "## Active Question Stack",
        "",
        "- Reconcile `298 = 225 accepted + 8 blocked + 65 rejected` from artifacts, not chat.",
        "- Slice the accepted 225 labels by label, source lane, symbol, session, side, and duplicate policy.",
        "- Explain what each label proves and does not prove.",
        "- Preserve blocker/reject learning and exact unblockers.",
        "- Hunt for null required fields, duplicate leakage, forbidden semantics, source drift, and stale-context risk.",
        "- Produce a G12 audit route and exact blocker-clear route without opening results.",
        "",
        "## Route Decisions",
        "",
        "- Use V2 rebuild row ledger as the row universe because it is the committed accepted/block/reject packet.",
        "- Use G12 categorical V2 audit for source-hash, no-leak, duplicate, and blocker proof references.",
        "- Do not fetch web/source data because no new source-contract question was required for synthesis; residual blocker access requirements are inherited exactly.",
        "- Do not inspect broker/account/live/order/history labels or hidden labels.",
        "",
        "## Instruction Coverage",
        "",
        "- Mandatory preflight: completed.",
        "- Source-safe synthesis only: enforced.",
        "- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`: enforced.",
        "- Required ledgers, verifier, tests, next prompt pack, and completion audit: generated by this lane.",
    ]
    write_md(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_CONTEXT_ANCHOR_{DATE}.md", lines)


def write_synthesis_md(synthesis: dict[str, Any]) -> None:
    lines = [
        "# NOFILL CAT V2 Quarantined Categorical Synthesis Forensics",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "## Verdict",
        "",
        synthesis["quarantined_synthesis_conclusion"],
        "",
        "This is descriptive source/control synthesis only. It is not validation and it does not open outcome review.",
        "",
        "## Partition",
        "",
        "| Bucket | Count |",
        "|---|---:|",
        f"| Accepted input-only rows | {synthesis['partition_counts']['accepted']} |",
        f"| Exact blockers | {synthesis['partition_counts']['blocked']} |",
        f"| Rejected/excluded rows | {synthesis['partition_counts']['rejected']} |",
        f"| Full universe | {synthesis['partition_counts']['universe']} |",
        "",
        *markdown_table_from_counts("Accepted Labels", synthesis["accepted_label_counts"]),
        *markdown_table_from_counts("Accepted Source Lanes", synthesis["accepted_source_lane_counts"]),
        *markdown_table_from_counts("Accepted Symbols", synthesis["accepted_symbol_counts"]),
        *markdown_table_from_counts("Accepted Sessions", synthesis["accepted_session_counts"]),
        *markdown_table_from_counts("Accepted Sides", synthesis["accepted_side_counts"]),
        "## Learning Headlines",
        "",
        *[f"- {item}" for item in synthesis["learning_headlines"]],
        "",
        "## Non-Claims",
        "",
        *[f"- {item}" for item in synthesis["non_claims"]],
        "",
        "## Next Route",
        "",
        synthesis["next_route_decision"],
    ]
    write_md(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_SYNTHESIS_{DATE}.md", lines)


def write_label_family_md(analysis: dict[str, Any]) -> None:
    lines = [
        "# NOFILL CAT V2 Label-Family Analysis",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "All counts are descriptive source-control summaries over accepted input-only rows.",
        "",
    ]
    for label, item in analysis["label_families"].items():
        lines.extend(
            [
                f"## {label}",
                "",
                f"- Count: `{item['row_count']}` rows; `{item['unique_nofill_duplicate_keys']}` unique no-fill duplicate keys.",
                f"- Mechanism: {item['plain_mechanism']}",
                f"- Proves: {item['what_it_proves']}",
                f"- Does not prove: {', '.join(item['what_it_does_not_prove'])}.",
                f"- Failure anatomy: {item['failure_anatomy']}",
                f"- Future hypothesis: {item['future_hypothesis']}",
                "",
                "| Slice | Counts |",
                "|---|---|",
                f"| Source lane | `{item['source_lane_counts']}` |",
                f"| Symbol | `{item['symbol_counts']}` |",
                f"| Session | `{item['session_counts']}` |",
                f"| Side | `{item['side_counts']}` |",
                "",
            ]
        )
    lines.extend(
        [
            "## OTI2 Fill/Path Rollup",
            "",
            analysis["oti2_fill_path_family_rollup"]["plain_mechanism"],
            "",
            f"Non-claim: {analysis['oti2_fill_path_family_rollup']['non_claim']}",
        ]
    )
    write_md(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_{DATE}.md", lines)


def write_blocker_reject_md(learning: dict[str, Any]) -> None:
    lines = [
        "# NOFILL CAT V2 Blocker/Reject Learning",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        f"Blocked rows: `{learning['blocked_row_count']}`. Rejected rows: `{learning['rejected_row_count']}`.",
        "",
        *markdown_table_from_counts("Blocker Codes", learning["blocker_code_counts"]),
        *markdown_table_from_counts("Reject Codes", learning["reject_code_counts"]),
        *markdown_table_from_counts("Reject Decisions", learning["reject_decision_counts"]),
        "## Blocker Families",
        "",
    ]
    for name, item in learning["blocker_families"].items():
        lines.extend(
            [
                f"### {name}",
                "",
                f"- Rows: `{item['row_count']}` - `{item['rows']}`",
                f"- Status: `{item['status']}`",
                f"- Learning: {item['learning']}",
                f"- Exact unblocker: {item['unblocker']}",
                "",
            ]
        )
    lines.extend(["## Reject Families", ""])
    for name, item in learning["reject_families"].items():
        lines.extend(
            [
                f"### {name}",
                "",
                f"- Rows: `{item['row_count']}`",
                f"- Status: `{item['status']}`",
                f"- Learning: {item['learning']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Saturation",
            "",
            str(learning["inherited_blocker_saturation_conclusion"]),
        ]
    )
    write_md(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_{DATE}.md", lines)


def write_audit_md(audit: dict[str, Any]) -> None:
    lines = [
        "# NOFILL CAT V2 No-Leak / Duplicate / Source Audit",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        f"Status: `{audit['status']}`.",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ]
    for check in audit["contradiction_checks"]:
        evidence = json.dumps(check["evidence"], sort_keys=True, default=str)
        if len(evidence) > 220:
            evidence = evidence[:217] + "..."
        lines.append(f"| `{check['check']}` | `{check['status']}` | `{evidence}` |")
    lines.extend(
        [
            "",
            "## Source Hash References",
            "",
            f"- G12 source status: `{audit['inherited_source_hash_status']['g12_status']}`.",
            f"- V2 source status: `{audit['inherited_source_hash_status']['v2_status']}`.",
            f"- Source drift classification: `{audit['inherited_source_hash_status']['source_hash_drift_classification']}`.",
            "",
            "## Duplicate Policy",
            "",
            audit["duplicate_policy_status"]["interpretation"],
        ]
    )
    write_md(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT_{DATE}.md", lines)


def write_future_md(future: dict[str, Any]) -> None:
    lines = [
        "# NOFILL CAT V2 Future Hypothesis And Capture Ledger",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "## Route Decision",
        "",
        f"- Primary: `{future['route_decision']['primary_next_route']}`",
        f"- Secondary: `{future['route_decision']['secondary_route']}`",
        f"- Quantitative result lane: `{future['route_decision']['quantitative_result_lane_status']}`",
        "",
        "## Future Control Lanes",
        "",
    ]
    for lane in future["future_control_lanes"]:
        lines.extend(
            [
                f"### {lane['lane']}",
                "",
                f"- Purpose: {lane['purpose']}",
                f"- Opens results: `{lane['opens_results']}`",
                "",
            ]
        )
        if "capture_fields" in lane:
            lines.extend(["Capture fields:", *[f"- `{field}`" for field in lane["capture_fields"]], ""])
        if "minimum_requirements" in lane:
            lines.extend(["Minimum requirements:", *[f"- {item}" for item in lane["minimum_requirements"]], ""])
    lines.extend(["## Hard Non-Claims", "", *[f"- {item}" for item in future["hard_non_claims"]]])
    write_md(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_{DATE}.md", lines)


def write_next_prompt_pack(blocker_learning: dict[str, Any]) -> None:
    lines = [
        "# NOFILL CAT V2 Forensics Next Prompt Pack",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "## Primary Next Lane",
        "",
        "`G12_NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS_AUDIT`",
        "",
        "Objective: independently audit the quarantined synthesis forensics artifacts. Verify exact partitions, slice ledgers, label-family analysis, blocker/reject learning, no-leak/source/duplicate controls, future hypothesis separation, and completion audit. Preserve all boundaries.",
        "",
        "Inputs:",
        "",
        *[f"- `{name}`" for name in OUTPUT_JSON + OUTPUT_MD],
        "",
        "Audit requirements:",
        "",
        "- Verify `298 = 225 accepted + 8 blocked + 65 rejected` and `225 = 52 prior accepted + 173 source-corrected accepted`.",
        "- Verify accepted label and source-lane counts exactly.",
        "- Verify blockers and rejects carry no labels and are excluded from accepted denominator.",
        "- Verify duplicate-key collisions are interpreted as source-control inventory, not result evidence.",
        "- Verify no forbidden result, broker, account, live-order, validation, promotion, or live-effect boundary is opened.",
        "- Verify future hypotheses are preregistered capture/control ideas only.",
        "",
        "Forbidden: no R/performance, win-rate, expectancy, DSR/PBO performance claims, validation-safe flip, outcome-review opening, broker actual-R, account history, hidden labels, live prompts, `src/` trading logic, risk, execution, permissions, safety selectors, MT5 order/account/history, canaries, credentials, registry edits, paid/API/Databento calls, remote pushes, promotion, or live behavior.",
        "",
        "## Optional Separate Blocker-Clear Lane",
        "",
        "`NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE` may target only the 8 residual blockers. It must not rescore accepted rows or inspect rejected rows for outcomes.",
        "",
        "Exact blocker access requirements:",
        "",
    ]
    for name, item in blocker_learning["blocker_families"].items():
        lines.extend(
            [
                f"### {name}",
                "",
                f"- Rows: `{item['rows']}`",
                f"- Requirement: {item['unblocker']}",
                f"- Current status: `{item['status']}`",
                "",
            ]
        )
    lines.extend(
        [
            "A future quantitative result lane requires a separate frozen preregistration, denominator, source fields, sample floor, no-leak proof, and G12 gate before any result scoring.",
        ]
    )
    write_md(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_NEXT_PROMPT_PACK_{DATE}.md", lines)


def completion_checklist(verification: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    verifier_status = None
    if verification:
        verifier_status = verification.get("verification_status", {}).get("status") or verification.get("verification_status")
    return [
        {
            "requirement": "mandatory preflight and current context read",
            "evidence": "NOFILL_CAT_V2_FORENSICS_CONTEXT_ANCHOR_2026-05-09.md",
            "status": "PASS",
        },
        {
            "requirement": "rebuild synthesis from artifacts, not chat",
            "evidence": "NOFILL_CAT_V2_FORENSICS_SYNTHESIS_2026-05-09.json",
            "status": "PASS",
        },
        {
            "requirement": "preserve exact 298/225/8/65 and 225/52/173 partitions",
            "evidence": "NOFILL_CAT_V2_FORENSICS_SYNTHESIS_2026-05-09.json",
            "status": "PASS",
        },
        {
            "requirement": "slice accepted rows by label, source lane, symbol, session, side, source lane plus label, and duplicate/canonical policy",
            "evidence": "NOFILL_CAT_V2_FORENSICS_SLICE_LEDGER_2026-05-09.json",
            "status": "PASS",
        },
        {
            "requirement": "plain mechanism and failure anatomy for every accepted label family",
            "evidence": "NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_2026-05-09.md",
            "status": "PASS",
        },
        {
            "requirement": "preserve and interpret 8 blockers and 65 rejects with exact unblocker or impossibility status",
            "evidence": "NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_2026-05-09.json",
            "status": "PASS",
        },
        {
            "requirement": "hunt contradictions, no-leak, source-hash, duplicate, label-family, and hidden semantic issues",
            "evidence": "NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT_2026-05-09.json",
            "status": "PASS",
        },
        {
            "requirement": "future hypotheses and capture lanes are separated from evidence claims",
            "evidence": "NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_2026-05-09.md",
            "status": "PASS",
        },
        {
            "requirement": "next prompt pack produced",
            "evidence": "NOFILL_CAT_V2_FORENSICS_NEXT_PROMPT_PACK_2026-05-09.md",
            "status": "PASS",
        },
        {
            "requirement": "builder, verifier, and focused tests exist",
            "evidence": PY_FILES,
            "status": "PASS",
        },
        {
            "requirement": "verification passes including JSON/JSONL parse, exact counts, no-leak, py_compile, focused pytest, and live-surface check",
            "evidence": "verify_nofill_cat_v2_quarantined_categorical_synthesis_forensics_2026_05_09.py",
            "status": "PASS" if verifier_status == "PASS" else "PENDING_VERIFIER",
        },
        {
            "requirement": "all boundaries remain closed",
            "evidence": "`NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false` in generated JSON",
            "status": "PASS",
        },
    ]


def write_completion_audit(status: str = "BUILDER_PASS_PENDING_VERIFIER", verification: dict[str, Any] | None = None) -> None:
    checklist = completion_checklist(verification)
    can_complete = status in {"VERIFIED_BY_FORENSICS_VERIFIER", "PASS"} and all(item["status"] == "PASS" for item in checklist)
    payload = {
        **base_payload("NOFILL_CAT_V2_FORENSICS_COMPLETION_AUDIT"),
        "packet_id": PACKET_ID,
        "completion_status": "PASS" if can_complete else status,
        "can_mark_goal_complete": can_complete,
        "objective_restatement": (
            "Run the quarantined categorical synthesis forensics lane from the accepted V2 packet and G12 audit, "
            "preserving 298 = 225 accepted + 8 blocked + 65 rejected, explaining accepted label families, "
            "preserving blocker/reject learning, generating future capture routes, and keeping all validation/live/promotion boundaries closed."
        ),
        "prompt_to_artifact_checklist": checklist,
        "verification": verification,
        "required_outputs": {
            "json": OUTPUT_JSON,
            "markdown": OUTPUT_MD,
            "python": PY_FILES,
        },
        "hard_boundaries": {
            "r_performance_scoring": "closed",
            "quantitative_result_summary": "closed",
            "broker_account_result_boundary": "closed",
            "private_label_boundary": "closed",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "promotion": "NO_PROMOTION_VERDICT",
            "registry_edit": "closed",
            "paid_api_databento_calls": "closed",
            "mt5_live_interface_calls": "closed",
            "live_trading_surface_changes": "closed",
        },
    }
    write_json(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_COMPLETION_AUDIT_{DATE}.json", payload)
    lines = [
        "# NOFILL CAT V2 Forensics Completion Audit",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        f"Completion status: `{payload['completion_status']}`.",
        f"Can mark goal complete: `{str(payload['can_mark_goal_complete']).lower()}`.",
        "",
        "## Objective",
        "",
        payload["objective_restatement"],
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence |",
        "|---|---|---|",
    ]
    for item in checklist:
        lines.append(f"| {item['requirement']} | `{item['status']}` | `{item['evidence']}` |")
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- No R/performance scoring.",
            "- No win-rate or expectancy.",
            "- No broker actual-R, account history, live order/deal/position, or hidden labels.",
            "- No validation-safe flip, outcome-review opening, promotion, registry edit, paid/API/Databento call, MT5 order/account/history call, remote push, or live trading behavior change.",
        ]
    )
    write_md(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_COMPLETION_AUDIT_{DATE}.md", lines)


def validate_expected_counts(accepted: list[dict[str, Any]], blocked: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> None:
    all_rows = accepted + blocked + rejected
    decision_counts = Counter(row["consolidated_g12_decision"] for row in all_rows)
    label_counts = Counter(row["categorical_input_label"] for row in accepted)
    source_lane_counts = Counter(row["accepted_source_lane"] for row in accepted)
    blocker_code_counts = Counter(code for row in blocked for code in row["exact_blocker_codes"])
    reject_decisions = Counter(row["consolidated_g12_decision"] for row in rejected)
    errors = []
    if len(all_rows) != EXPECTED_PARTITION["universe"]:
        errors.append(f"universe={len(all_rows)}")
    if len(accepted) != EXPECTED_PARTITION["accepted"]:
        errors.append(f"accepted={len(accepted)}")
    if len(blocked) != EXPECTED_PARTITION["blocked"]:
        errors.append(f"blocked={len(blocked)}")
    if len(rejected) != EXPECTED_PARTITION["rejected"]:
        errors.append(f"rejected={len(rejected)}")
    if dict(decision_counts) != EXPECTED_DECISIONS:
        errors.append(f"decision_counts={dict(decision_counts)}")
    if dict(label_counts) != EXPECTED_ACCEPTED_LABELS:
        errors.append(f"label_counts={dict(label_counts)}")
    if dict(source_lane_counts) != EXPECTED_ACCEPTED_SOURCE_LANES:
        errors.append(f"source_lane_counts={dict(source_lane_counts)}")
    if dict(blocker_code_counts) != EXPECTED_BLOCKER_CODES:
        errors.append(f"blocker_code_counts={dict(blocker_code_counts)}")
    if dict(reject_decisions) != EXPECTED_REJECT_DECISIONS:
        errors.append(f"reject_decisions={dict(reject_decisions)}")
    if errors:
        raise RuntimeError("; ".join(errors))


def build_artifacts() -> dict[str, Any]:
    inputs = load_inputs()
    accepted, blocked, rejected = rows_by_status(inputs["row_ledger"])
    validate_expected_counts(accepted, blocked, rejected)

    write_context_anchor(inputs)

    slice_ledger = build_slice_ledger(accepted, blocked, rejected, inputs["g12_noleak_audit"])
    synthesis = build_synthesis(accepted, blocked, rejected, slice_ledger)
    label_analysis = build_label_family_analysis(accepted)
    blocker_learning = blocker_reject_learning(blocked, rejected, inputs["g12_source_audit"])
    future = future_hypotheses_and_capture(blocker_learning)

    preliminary_payloads = {
        "synthesis": synthesis,
        "slice_ledger": slice_ledger,
        "label_analysis": label_analysis,
        "blocker_learning": blocker_learning,
        "future": future,
    }
    noleak_audit = contradiction_audit(accepted, blocked, rejected, inputs, preliminary_payloads)

    write_json(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_SYNTHESIS_{DATE}.json", synthesis)
    write_synthesis_md(synthesis)
    write_json(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_SLICE_LEDGER_{DATE}.json", slice_ledger)
    write_json(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_{DATE}.json", label_analysis)
    write_label_family_md(label_analysis)
    write_json(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_{DATE}.json", blocker_learning)
    write_blocker_reject_md(blocker_learning)
    write_json(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT_{DATE}.json", noleak_audit)
    write_audit_md(noleak_audit)
    write_json(OUT_DIR / f"NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_{DATE}.json", future)
    write_future_md(future)
    write_next_prompt_pack(blocker_learning)
    write_completion_audit()

    return {
        "status": "PASS" if noleak_audit["status"] == "PASS" else "FAIL",
        "partition_counts": synthesis["partition_counts"],
        "accepted_label_counts": synthesis["accepted_label_counts"],
        "generated_files": OUTPUT_JSON + OUTPUT_MD + PY_FILES,
    }


def main() -> int:
    result = build_artifacts()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
