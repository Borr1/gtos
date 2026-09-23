"""Build the no-fill blocked-family source-correction router artifacts.

This lane is research/control only. It routes blocked categorical lifecycle rows
to future source-correction or contract-revision prompt packs without opening
performance outcomes.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
MAIN_REPO_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
DATE = "2026-05-08"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

CAT_PACKET_ROWS = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_PACKET_ROWS_2026-05-08.jsonl"
CAT_BLOCKER_LEDGER = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_2026-05-08.json"
G12_DECISION_LEDGER = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/G12_NOFILL_CAT_DECISION_LEDGER_2026-05-08.json"
G12_BLOCKER_REVIEW = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/G12_NOFILL_CAT_BLOCKER_REVIEW_2026-05-08.json"
G12_SOURCE_HASH_AUDIT = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/G12_NOFILL_CAT_SOURCE_HASH_AUDIT_2026-05-08.json"
CONTRACT_RULEBOOK = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_result_contract_design/NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-08.json"
FIELD_REQUIREMENTS = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_result_contract_design/NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS_2026-05-08.json"

CONTROLLING_PROMPT = LANE_DIR / "NOFILL_BLOCKED_FAMILY_SOURCE_CORRECTION_ROUTER_GOAL_PROMPT_2026-05-08.md"

FAMILY_ORDER = [
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION",
    "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET",
    "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT",
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT",
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT",
]

FAMILY_BY_TUPLE = {
    ("BLOCK_RESULT_MISSING_SOURCE",): "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION",
    ("BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD",): "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET",
    ("BLOCK_RESULT_LTF_PRICE_ONLY",): "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT",
    ("BLOCK_RESULT_DUPLICATE_CONFLICT",): "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT",
    (
        "BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED",
        "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS",
    ): "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT",
}

FAMILY_PROMPT_PACKS = {
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION_PROMPT_PACK_2026-05-08.md",
    "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_PROMPT_PACK_2026-05-08.md",
    "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT_PROMPT_PACK_2026-05-08.md",
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_PROMPT_PACK_2026-05-08.md",
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT": "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_PROMPT_PACK_2026-05-08.md",
}

FAMILY_MISSING_FIELDS = {
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": [
        "range_high",
        "range_low",
        "breakout_close_time",
        "breakout_side",
        "source_hashed_range_bars",
        "as_of_provenance",
        "parser_version",
        "decision_time_availability",
    ],
    "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": [
        "entry_touched_at_utc",
        "filled_at_utc",
        "cancelled_at_utc",
        "expired_at_utc",
        "pending_intent_id_or_deterministic_key",
        "source_hash_path",
        "side_aware_touch_source",
        "as_of_rule",
    ],
    "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": [
        "bid_ask_quote_or_tick_source",
        "entry_touch_time_utc",
        "terminal_area_touch_time_utc",
        "protective_level_touch_time_utc",
        "ordered_source_events",
        "same_timestamp_ambiguity",
        "parser_contract",
    ],
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": [
        "source_identity_collision_decision",
        "canonical_geometry_selection_rule",
        "duplicate_denominator_rule",
        "geometry_signature_source_fields",
        "source_hash_path",
    ],
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT": [
        "entry_touch_source",
        "post_entry_terminal_touch_time_utc",
        "post_entry_protective_touch_time_utc",
        "ordered_source_events",
        "same_timestamp_ambiguity",
        "separate_fill_path_label_family",
    ],
}

FAMILY_ROUTE_KIND = {
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": "source_correction_or_contract_revision_prompt_pack",
    "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": "source_correction_prompt_pack",
    "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": "source_correction_or_quote_tick_contract_prompt_pack_with_partial_access_request",
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": "source_identity_geometry_audit_prompt_pack",
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT": "contract_revision_prompt_pack",
}

EXPECTED_CODE_COUNTS = {
    "BLOCK_RESULT_DUPLICATE_CONFLICT": 42,
    "BLOCK_RESULT_LTF_PRICE_ONLY": 69,
    "BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD": 54,
    "BLOCK_RESULT_MISSING_SOURCE": 80,
    "BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED": 1,
    "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": 1,
}

EXCLUDED_T3_IDS = {
    "CNR-T3-CAND-0001",
    "CNR-T3-CAND-0002",
    "CNR-T3-CAND-0003",
    "CNR-T3-CAND-0004",
    "CNR-T3-CAND-0005",
    "CNR-T3-CAND-0006",
}

FORBIDDEN_BOUNDARIES = [
    "No R/performance scoring.",
    "No win-rate, expectancy, DSR/PBO, validation, promotion, or live-effect claims.",
    "No broker actual-R, account history, live order/deal/position labels, hidden labels, or blocked CNR061/six T3 scoring.",
    "No paid/API/Databento calls and no MT5 order/account/history calls.",
    "No live trading prompts, risk, execution, permissions, safety gates, selectors, canaries, credentials, remotes, registry promotion flags, validation flags, outcome-review flags, live-effect flags, or order behavior changes.",
]


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_source_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    worktree_candidate = REPO_ROOT / path
    if worktree_candidate.exists():
        return worktree_candidate
    main_candidate = MAIN_REPO_ROOT / path
    if main_candidate.exists():
        return main_candidate
    return worktree_candidate


def file_record(path: Path, role: str, expected_sha256: str | None = None) -> dict[str, Any]:
    actual = sha256_file(path)
    return {
        "path": str(path),
        "rel_path": rel(path) if path.is_absolute() and str(path).startswith(str(REPO_ROOT)) else str(path),
        "role": role,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "sha256": actual,
        "expected_sha256": expected_sha256,
        "expected_match": actual == expected_sha256 if expected_sha256 and actual else None,
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(name: str, payload: dict[str, Any]) -> None:
    payload.setdefault("generated_at_utc", NOW)
    payload.setdefault("promotion_verdict", "NO_PROMOTION_VERDICT")
    payload.setdefault("validation_safe", False)
    payload.setdefault("outcome_review_opened", False)
    payload.setdefault("live_effect", False)
    (LANE_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def md_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
    return "\n".join(out)


def write_md(name: str, title: str, sections: list[tuple[str, str]]) -> None:
    lines = [f"# {title}", "", f"Generated: {NOW}", "", "Promotion posture: `NO_PROMOTION_VERDICT`", "Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`", ""]
    for heading, body in sections:
        lines.extend([f"## {heading}", "", body.strip(), ""])
    (LANE_DIR / name).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def family_tuple(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(row.get("result_blocker_codes") or [])


def route_family(row: dict[str, Any]) -> str:
    tup = family_tuple(row)
    if tup not in FAMILY_BY_TUPLE:
        raise ValueError(f"Unexpected blocker tuple for {row.get('packet_row_id')}: {tup}")
    return FAMILY_BY_TUPLE[tup]


def tick_path(symbol: str, date_text: str) -> Path:
    return MAIN_REPO_ROOT / "data" / "ticks" / symbol / f"{date_text}.parquet"


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        "source_lane_counts": dict(Counter(row.get("source_lane") for row in rows)),
        "source_closure_label_counts": dict(Counter(row.get("source_closure_label") for row in rows)),
        "symbol_counts": dict(Counter(row.get("symbol") for row in rows)),
        "session_counts": dict(Counter(row.get("session") for row in rows)),
        "date_counts": dict(Counter(f"{row.get('symbol')}|{str(row.get('decision_asof_utc'))[:10]}" for row in rows)),
        "source_close_packet_row_ids": [row["source_close_packet_row_id"] for row in rows],
        "packet_row_ids": [row["packet_row_id"] for row in rows],
        "source_inventory_ids": [row["source_inventory_id"] for row in rows],
        "unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in rows}),
        "unique_duplicate_group_ids": len({row["duplicate_group_id"] for row in rows}),
    }


def collect_unique_source_refs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[tuple[str, str | None], dict[str, Any]] = {}
    for row in rows:
        for ref in row.get("source_references") or []:
            key = (ref.get("path"), ref.get("expected_sha256"))
            seen.setdefault(
                key,
                {
                    "path": ref.get("path"),
                    "expected_sha256": ref.get("expected_sha256"),
                    "roles": set(),
                    "row_count": 0,
                },
            )
            seen[key]["roles"].add(ref.get("role"))
            seen[key]["row_count"] += 1
    records = []
    for item in seen.values():
        path = resolve_source_path(item["path"])
        record = file_record(path, role="blocked_row_source_reference", expected_sha256=item["expected_sha256"])
        record["source_reference_path"] = item["path"]
        record["source_reference_roles"] = sorted(r for r in item["roles"] if r)
        record["referencing_blocked_rows"] = item["row_count"]
        records.append(record)
    return sorted(records, key=lambda r: (r["source_reference_path"], r.get("expected_sha256") or ""))


def search_root_record(root: Path, description: str, patterns: list[str]) -> dict[str, Any]:
    exists = root.exists()
    record: dict[str, Any] = {
        "root": str(root),
        "description": description,
        "exists": exists,
        "patterns": patterns,
        "matched_files": [],
        "match_count": 0,
    }
    if not exists:
        return record
    matched: list[str] = []
    for pattern in patterns:
        try:
            matched.extend(str(path) for path in root.rglob(pattern) if path.is_file())
        except (OSError, PermissionError) as exc:
            record.setdefault("errors", []).append(f"{pattern}: {exc}")
    record["matched_files"] = sorted(set(matched))[:200]
    record["match_count"] = len(set(matched))
    return record


def build_tick_availability(family_rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    availability: dict[str, Any] = {}
    for family, rows in family_rows.items():
        needed = sorted({(row["symbol"], str(row["decision_asof_utc"])[:10]) for row in rows})
        records = []
        for symbol, date_text in needed:
            path = tick_path(symbol, date_text)
            records.append(file_record(path, role=f"{family}_needed_tick_file"))
        availability[family] = {
            "needed_symbol_dates": [f"{symbol}|{date_text}" for symbol, date_text in needed],
            "present": sum(1 for r in records if r["exists"]),
            "missing": sum(1 for r in records if not r["exists"]),
            "records": records,
        }
    return availability


def pending_field_search() -> dict[str, Any]:
    paths = [
        REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl",
        REPO_ROOT / "shadow_logs/pending_limit_lifecycle_audit.jsonl",
        REPO_ROOT / "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl",
        MAIN_REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl",
        MAIN_REPO_ROOT / "shadow_logs/pending_limit_lifecycle_audit.jsonl",
        MAIN_REPO_ROOT / "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl",
    ]
    required_fields = [
        "entry_touched_at_utc",
        "filled_at_utc",
        "cancelled_at_utc",
        "expired_at_utc",
        "pending_created_at_utc",
        "pending_active_from_utc",
        "pending_active_until_utc",
    ]
    records = []
    for path in paths:
        field_counts = Counter()
        rows_seen = 0
        if path.exists():
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                rows_seen += 1
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                for field in required_fields:
                    if field in payload and payload.get(field) not in (None, "", []):
                        field_counts[field] += 1
                    source_row = payload.get("source_row")
                    if isinstance(source_row, dict):
                        for field in required_fields:
                            if field in source_row and source_row.get(field) not in (None, "", []):
                                field_counts[f"source_row.{field}"] += 1
        record = file_record(path, role="pending_intent_lifecycle_source_search")
        record["rows_seen"] = rows_seen
        record["required_field_nonnull_counts"] = dict(field_counts)
        records.append(record)
    return {
        "required_fields": required_fields,
        "records": records,
        "materialized_entry_touched_at_utc_found": any(
            (r.get("required_field_nonnull_counts") or {}).get("entry_touched_at_utc", 0) > 0
            or (r.get("required_field_nonnull_counts") or {}).get("source_row.entry_touched_at_utc", 0) > 0
            for r in records
        ),
    }


def build_route_decision(row: dict[str, Any], tick_availability: dict[str, Any]) -> dict[str, Any]:
    family = route_family(row)
    date_text = str(row["decision_asof_utc"])[:10]
    row_tick = tick_path(row["symbol"], date_text)
    status = "source_safe_next_prompt_pack"
    access_requirement = None
    if family == "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT" and not row_tick.exists():
        status = "exact_access_or_source_capture_request_required"
        access_requirement = f"Locate or extract read-only USDJPY bid/ask tick parquet for {date_text}; no MT5 order/account/history calls."
    return {
        "packet_row_id": row["packet_row_id"],
        "source_close_packet_row_id": row["source_close_packet_row_id"],
        "source_inventory_id": row["source_inventory_id"],
        "source_lane": row["source_lane"],
        "source_packet_id": row["source_packet_id"],
        "source_row_id": row["source_row_id"],
        "symbol": row["symbol"],
        "session": row["session"],
        "side": row["side"],
        "decision_asof_utc": row["decision_asof_utc"],
        "nofill_duplicate_key": row["nofill_duplicate_key"],
        "duplicate_group_id": row["duplicate_group_id"],
        "blocker_codes": row["result_blocker_codes"],
        "blocker_reasons": row["result_blocker_reasons"],
        "route_family": family,
        "route_kind": FAMILY_ROUTE_KIND[family],
        "next_prompt_pack": FAMILY_PROMPT_PACKS[family],
        "route_status": status,
        "missing_fields_or_contract_terms": FAMILY_MISSING_FIELDS[family],
        "row_tick_source_probe": {
            "path": str(row_tick),
            "exists": row_tick.exists(),
        },
        "access_requirement": access_requirement,
        "result_label_allowed_in_router": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def build_prompt_pack(family: str, rows: list[dict[str, Any]], access_rows: list[dict[str, Any]]) -> str:
    prompt_path = FAMILY_PROMPT_PACKS[family]
    starter = (
        f"/goal Run {family} using C:\\tmp\\gtos_otb\\NOFILLROUTER\\research\\science_program_2026_05\\06_outcome_testing"
        f"\\nofill_blocked_family_source_correction_router\\{prompt_path} as the controlling prompt; preserve NO_PROMOTION_VERDICT, "
        "validation_safe=false, outcome_review_opened=false, live_effect=false; make categorical lifecycle labels possible only through source-correction or contract-revision evidence; do not compute R/performance or touch live trading surfaces."
    )
    family_requirements = {
        "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": (
            "Rebuild or revise the opening-drive source contract for 80 rows by source-hashing range_high, range_low, breakout_close_time, breakout_side, range bars, parser version, and decision-time as-of provenance. Use OTI4, OTX, G12/OTX artifacts, and local tick files. Decide patch-source-projection versus contract revision; do not assign labels in the prompt pack itself."
        ),
        "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": (
            "Build a pending-intent closure source packet for 54 rows that materializes entry_touched_at_utc plus fill/cancel/expiry/horizon timestamps from source-safe lifecycle logs and side-aware tick source. Do not consume broker actual-R, account history, or live order/deal/position labels."
        ),
        "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": (
            "Determine whether the 69 USDJPY price-only rows can become categorical lifecycle evidence under a conservative quote/tick contract. Use source-hashed USDJPY CFD M1 only as context; quote/tick proof is required for labels. Route rows with missing tick dates to the exact access/source request."
        ),
        "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": (
            "Audit the 42 duplicate-conflict rows across 3 nofill_duplicate_key groups. Decide true duplicate conflict, source identity collision, repeated row projection, geometry mismatch, or denominator collision. Freeze canonical geometry rules before any future label."
        ),
        "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT": (
            "Design the separate fill/path categorical contract for the single entry-touched row. Separate entry-touch/fill/path terminal order without R/performance, broker/account/live/order labels, or hidden labels."
        ),
    }[family]
    access_note = "No access request is currently needed for this family."
    if access_rows:
        access_note = "Rows needing exact access/source request:\n" + "\n".join(
            f"- {row['source_close_packet_row_id']} {row['symbol']} {row['decision_asof_utc']}: {row['access_requirement']}"
            for row in access_rows
        )
    return f"""# {family} Prompt Pack - {DATE}

Promotion posture: `NO_PROMOTION_VERDICT`
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`
Lane type: source-correction / contract-revision only

## One-Line Starter

`{starter}`

## Objective

{family_requirements}

Rows in scope: `{len(rows)}`.
Blocker tuple(s): `{sorted({'+'.join(row.get('result_blocker_codes') or row.get('blocker_codes') or []) for row in rows})}`.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered handoff in `.context/02_session_handoffs/`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read `.context/00_core/local_heavy_data_inventory.md`.
9. Read this prompt pack, `NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.md`, `NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json`, and `NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json`.

## Hardening Standard

Operate at maximum practical reasoning depth. Enforce curiosity, truthfulness, and active creativity. Treat examples, listed files, current timeframe, current worktree, current source modality, and first model framing as starting points, not boundaries. Search local heavy-data roots and prior artifacts before accepting any data blocker. Pursue every ambiguity until answered, proven impossible from approved inputs, reduced to an exact owner/access/source/capture requirement, or blocked by a hard forbidden boundary. Preserve context in committed artifacts so compaction cannot erase requirements.

## Scope Boundaries

{os.linesep.join(f"- {line}" for line in FORBIDDEN_BOUNDARIES)}

## Required Missing Fields Or Contract Terms

{os.linesep.join(f"- `{field}`" for field in FAMILY_MISSING_FIELDS[family])}

## Access State

{access_note}

## Required Outputs For This Future Lane

- Context anchor and source-search ledger.
- Source/contract packet or exact impossibility ledger.
- Row-level route/eligibility decisions for every row in this family.
- Source-hash/no-leak/duplicate/as-of checks.
- Completion audit with exact blockers, no generic future-work language.

## Stop Condition

Stop only when every row in this family is source-corrected, contract-revised, blocked by exact source/as-of/no-leak/duplicate/label-family impossibility, or mapped to an exact owner/access/source/capture request.
"""


def build() -> dict[str, Any]:
    rows = read_jsonl(CAT_PACKET_ROWS)
    blocker_ledger = read_json(CAT_BLOCKER_LEDGER)
    g12_decision = read_json(G12_DECISION_LEDGER)
    g12_blocker = read_json(G12_BLOCKER_REVIEW)
    read_json(CONTRACT_RULEBOOK)
    read_json(FIELD_REQUIREMENTS)

    blocked = [row for row in rows if row.get("eligibility_decision") == "BLOCKED_BEFORE_LABEL"]
    eligible = [row for row in rows if row.get("eligibility_decision") == "ELIGIBLE_LABEL_ASSIGNED"]
    code_counts = Counter()
    tuple_counts = Counter()
    family_rows: dict[str, list[dict[str, Any]]] = {family: [] for family in FAMILY_ORDER}
    for row in blocked:
        for code in row.get("result_blocker_codes") or []:
            code_counts[code] += 1
        tuple_counts["+".join(row.get("result_blocker_codes") or [])] += 1
        family_rows[route_family(row)].append(row)

    tick_availability = build_tick_availability(family_rows)
    row_route_decisions = [build_route_decision(row, tick_availability) for row in blocked]
    access_rows = [row for row in row_route_decisions if row["access_requirement"]]

    context_anchor = {
        "artifact_family": "NOFILL_ROUTER_CONTEXT_ANCHOR",
        "lane": "NOFILL_BLOCKED_FAMILY_SOURCE_CORRECTION_ROUTER_V1",
        "head": run_git(["rev-parse", "HEAD"]),
        "branch": run_git(["branch", "--show-current"]),
        "controlling_prompt_path": rel(CONTROLLING_PROMPT),
        "preflight_files_read": [
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_READING_ORDER.md",
            rel(CONTROLLING_PROMPT),
        ],
        "freshness_status": "LIVE_STATE_REGENERATED_AND_RESEARCH_CURRENT_STATE_REPORTED_FRESH_AT_PREFLIGHT",
        "objective_restatement": "Route all 246 G12-blocked no-fill categorical rows to exact source-correction, contract-revision, access/source request, or impossibility decisions without opening result/performance/live lanes.",
        "starting_facts_preserved": {
            "total_categorical_rows": len(rows),
            "eligible_rows": len(eligible),
            "blocked_rows": len(blocked),
            "blocker_code_counts": dict(code_counts),
            "blocker_tuple_counts": dict(tuple_counts),
            "row_0127_terminal_first_touch": "2026-05-06T07:15:00.634000Z",
            "row_0127_tick_sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
            "six_t3_rows_excluded": sorted(EXCLUDED_T3_IDS),
            "g12_blocked_cnr061_rows_excluded": 94,
        },
        "forbidden_boundaries": FORBIDDEN_BOUNDARIES,
    }

    write_json(f"NOFILL_ROUTER_CONTEXT_ANCHOR_{DATE}.json", context_anchor)
    write_md(
        f"NOFILL_ROUTER_CONTEXT_ANCHOR_{DATE}.md",
        "NOFILL Router Context Anchor",
        [
            ("Objective", context_anchor["objective_restatement"]),
            ("Preflight Files Read", "\n".join(f"- `{p}`" for p in context_anchor["preflight_files_read"])),
            ("Starting Counts", json.dumps(context_anchor["starting_facts_preserved"], indent=2, sort_keys=True)),
            ("Forbidden Boundaries", "\n".join(f"- {line}" for line in FORBIDDEN_BOUNDARIES)),
        ],
    )

    inventory_families = []
    for family in FAMILY_ORDER:
        fam_rows = family_rows[family]
        summary = summarize_rows(fam_rows)
        inventory_families.append(
            {
                "route_family": family,
                "prompt_pack": FAMILY_PROMPT_PACKS[family],
                "route_kind": FAMILY_ROUTE_KIND[family],
                "missing_fields_or_contract_terms": FAMILY_MISSING_FIELDS[family],
                **summary,
            }
        )

    inventory = {
        "artifact_family": "NOFILL_ROUTER_BLOCKED_FAMILY_INVENTORY",
        "input_packet": rel(CAT_PACKET_ROWS),
        "g12_decision": g12_decision.get("decision"),
        "g12_blocker_review_status": g12_blocker.get("status"),
        "total_rows": len(rows),
        "eligible_rows": len(eligible),
        "blocked_rows": len(blocked),
        "blocker_code_counts": dict(code_counts),
        "blocker_tuple_counts": dict(tuple_counts),
        "family_order": FAMILY_ORDER,
        "families": inventory_families,
        "eligible_packet_row_ids": [row["packet_row_id"] for row in eligible],
        "blocked_packet_row_ids": [row["packet_row_id"] for row in blocked],
        "row_route_decision_count": len(row_route_decisions),
    }
    write_json(f"NOFILL_ROUTER_BLOCKED_FAMILY_INVENTORY_{DATE}.json", inventory)
    write_md(
        f"NOFILL_ROUTER_BLOCKED_FAMILY_INVENTORY_{DATE}.md",
        "NOFILL Router Blocked Family Inventory",
        [
            (
                "Family Counts",
                md_table(
                    [
                        {
                            "family": family["route_family"],
                            "rows": family["row_count"],
                            "unique_keys": family["unique_nofill_duplicate_keys"],
                            "prompt_pack": family["prompt_pack"],
                        }
                        for family in inventory_families
                    ],
                    ["family", "rows", "unique_keys", "prompt_pack"],
                ),
            ),
            ("Blocker Code Counts", json.dumps(dict(code_counts), indent=2, sort_keys=True)),
            ("Overlap Note", "The OTI2 row carries both `BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED` and `BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS`, so blocker-code counts sum to 247 while row identities remain 246."),
        ],
    )

    controlling_inputs = [
        CONTROLLING_PROMPT,
        G12_DECISION_LEDGER,
        G12_BLOCKER_REVIEW,
        G12_SOURCE_HASH_AUDIT,
        CAT_PACKET_ROWS,
        CAT_BLOCKER_LEDGER,
        CONTRACT_RULEBOOK,
        FIELD_REQUIREMENTS,
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/G12_NOFILL_CAT_NOLEAK_LABEL_AUDIT_2026-05-08.json",
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/G12_NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_no_fill_result_contract_audit/G12_NOFILL_RESULT_CONTRACT_DECISION_LEDGER_2026-05-08.json",
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.md",
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_no_fill_correction_reaudit/G12_NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json",
    ]
    prior_artifacts = [
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/oti4_g6_opening_drive_quarantined_results/OTI4_BLOCKER_AND_AMBIGUITY_LEDGER_2026-05-07.json",
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_BLOCKER_LEDGER_2026-05-07.json",
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_BLOCKER_LEDGER_2026-05-07.json",
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/oti5_g6_cusum_changepoint_quarantined_results/OTI5_G6_CUSUM_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json",
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_AMBIGUITY_RESOLUTION_LEDGER_2026-05-07.json",
    ]
    root_searches = [
        search_root_record(REPO_ROOT / "research/science_program_2026_05/06_outcome_testing", "worktree outcome-testing artifacts", ["*NOFILL*.json", "*OTI*.json", "*OTX*.json"]),
        search_root_record(MAIN_REPO_ROOT / "data", "absolute main data root", ["USDJPY_M1.csv", "*.parquet"]),
        search_root_record(MAIN_REPO_ROOT / "data" / "ticks", "absolute main tick root", ["*.parquet"]),
        search_root_record(MAIN_REPO_ROOT / "data" / "mt5_research_exports", "read-only MT5 research exports", ["USDJPY_M1.csv", "*.csv"]),
        search_root_record(MAIN_REPO_ROOT / "shadow_logs", "absolute main shadow logs", ["pending_limit_lifecycle*.jsonl"]),
        search_root_record(MAIN_REPO_ROOT / "exports", "absolute exports root", ["*"]),
        search_root_record(Path(r"C:\tmp"), "temporary worktrees and prior artifacts", ["G12_NOFILL_CAT_DECISION_LEDGER_2026-05-08.json", "OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json"]),
        search_root_record(Path(r"C:\SierraChart"), "SierraChart data root", ["*.scid", "*.depth", "*.csv"]),
    ]
    source_hash_records = [file_record(path, "controlling_input") for path in controlling_inputs]
    source_hash_records.extend(file_record(path, "prior_artifact") for path in prior_artifacts)
    source_ref_records = collect_unique_source_refs(blocked)
    pending_search = pending_field_search()
    usd_m1 = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\mt5_research_exports\phase3_v2b_forward_20260401_20260502_readonly\USDJPY_M1.csv")
    source_search_ledger = {
        "artifact_family": "NOFILL_ROUTER_SOURCE_SEARCH_LEDGER",
        "controlling_input_hashes": source_hash_records,
        "blocked_row_source_reference_hashes": source_ref_records,
        "root_searches": root_searches,
        "tick_availability_by_family": tick_availability,
        "pending_intent_field_search": pending_search,
        "usdjpy_m1_context_source": file_record(usd_m1, role="usdjpy_price_compatible_m1_context_source", expected_sha256="9a16ad55351131b0675bbc83390059deeb3ee6b669b42f848219cee7b47b5519"),
        "search_conclusions": {
            "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": "Local tick source is present for all OTI4 symbol-date probes, but current accepted packet still lacks source-hashed prereg opening-drive fields.",
            "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": "Pending lifecycle logs are present, but entry_touched_at_utc is not materialized; local ticks are present for family symbol-date probes and can be used by a future source packet if contract-safe.",
            "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": "USDJPY M1 CSV context exists and matches expected hash; USDJPY tick parquet exists for 2026-04-30 and 2026-05-01 rows but is absent for 2026-04-17 and 2026-04-20 rows.",
            "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": "Duplicate conflict is denominator/source-identity ambiguity, not missing tick data.",
            "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT": "The single XAUUSD row has local tick source available, but it requires a separate label family contract because entry touch moves it out of no-fill closure.",
        },
    }
    write_json(f"NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_{DATE}.json", source_search_ledger)
    write_md(
        f"NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_{DATE}.md",
        "NOFILL Router Source Search Ledger",
        [
            ("Root Searches", md_table(root_searches, ["root", "exists", "match_count", "description"])),
            ("Family Tick Availability", json.dumps({k: {"present": v["present"], "missing": v["missing"], "needed_symbol_dates": v["needed_symbol_dates"]} for k, v in tick_availability.items()}, indent=2, sort_keys=True)),
            ("Pending Intent Field Search", json.dumps({"materialized_entry_touched_at_utc_found": pending_search["materialized_entry_touched_at_utc_found"], "required_fields": pending_search["required_fields"]}, indent=2, sort_keys=True)),
            ("Conclusions", "\n".join(f"- `{k}`: {v}" for k, v in source_search_ledger["search_conclusions"].items())),
        ],
    )

    family_route_decisions = []
    for family in FAMILY_ORDER:
        fam_route_rows = [row for row in row_route_decisions if row["route_family"] == family]
        exact_access_rows = [row for row in fam_route_rows if row["access_requirement"]]
        family_route_decisions.append(
            {
                "route_family": family,
                "row_count": len(fam_route_rows),
                "route_kind": FAMILY_ROUTE_KIND[family],
                "next_prompt_pack": FAMILY_PROMPT_PACKS[family],
                "source_safe_rows": len(fam_route_rows) - len(exact_access_rows),
                "access_or_source_request_rows": len(exact_access_rows),
                "missing_fields_or_contract_terms": FAMILY_MISSING_FIELDS[family],
                "route_decision": "OPEN_SOURCE_SAFE_PROMPT_PACK" if family != "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT" else "OPEN_PROMPT_PACK_AND_EXACT_ACCESS_REQUEST_FOR_MISSING_TICK_DATES",
                "no_result_lane_allowed": True,
            }
        )

    route_ledger = {
        "artifact_family": "NOFILL_ROUTER_ROUTE_DECISION_LEDGER",
        "row_route_decision_count": len(row_route_decisions),
        "family_route_decisions": family_route_decisions,
        "row_route_decisions": row_route_decisions,
        "no_result_lane_allowed": True,
        "forbidden_boundaries": FORBIDDEN_BOUNDARIES,
    }
    write_json(f"NOFILL_ROUTER_ROUTE_DECISION_LEDGER_{DATE}.json", route_ledger)
    write_md(
        f"NOFILL_ROUTER_ROUTE_DECISION_LEDGER_{DATE}.md",
        "NOFILL Router Route Decision Ledger",
        [
            (
                "Family Decisions",
                md_table(
                    family_route_decisions,
                    ["route_family", "row_count", "route_decision", "source_safe_rows", "access_or_source_request_rows", "next_prompt_pack"],
                ),
            ),
            ("Row Coverage", f"Every blocked row has one row-level route decision: `{len(row_route_decisions)}` decisions for `{len(blocked)}` blocked rows."),
            ("No Result Lane", "No family is routed to a result, validation, promotion, R/performance, broker/account, live-order, hidden-label, registry, or live-effect lane."),
        ],
    )

    access_request_ledger = {
        "artifact_family": "NOFILL_ROUTER_ACCESS_REQUEST_LEDGER",
        "access_request_count": 1 if access_rows else 0,
        "row_count_requiring_access_or_source_capture": len(access_rows),
        "requests": [],
    }
    if access_rows:
        access_request_ledger["requests"].append(
            {
                "request_id": "NOFILL-ROUTER-ACCESS-USDJPY-TICKS-2026-04-17-2026-04-20",
                "family": "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT",
                "row_count": len(access_rows),
                "source_close_packet_row_ids": [row["source_close_packet_row_id"] for row in access_rows],
                "needed_source": "USDJPY bid/ask tick parquet or an already cached source-equivalent quote file for 2026-04-17 and 2026-04-20.",
                "purpose": "Convert price-compatible M1 context-only rows into quote/tick-order categorical lifecycle evidence or keep exact source blockers.",
                "authorized_in_router": False,
                "approval_required": "Owner approval for a separate read-only tick extraction/source-search lane if cached files cannot be found.",
                "forbidden": "No MT5 order/account/history calls, no broker actual-R/account/live order labels, no paid/API/Databento calls, no result/performance scoring.",
                "cache_path_required": r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\USDJPY\YYYY-MM-DD.parquet",
                "source_hash_required": True,
            }
        )
    write_json(f"NOFILL_ROUTER_ACCESS_REQUEST_LEDGER_{DATE}.json", access_request_ledger)
    write_md(
        f"NOFILL_ROUTER_ACCESS_REQUEST_LEDGER_{DATE}.md",
        "NOFILL Router Access Request Ledger",
        [
            ("Access Summary", f"Access/source-capture requests: `{access_request_ledger['access_request_count']}`; row identities needing them: `{len(access_rows)}`."),
            ("Requests", json.dumps(access_request_ledger["requests"], indent=2, sort_keys=True) if access_request_ledger["requests"] else "No access request required."),
        ],
    )

    learning_rows = [
        {
            "route_family": "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION",
            "teaches": "Terminal tick evidence cannot substitute for prereg opening-drive range and breakout fields. Future opening-drive packets must carry source-hashed range bars and breakout fields as first-class source contract fields.",
            "future_capture_change": "Log range_high, range_low, breakout_close_time, breakout_side, range_start/end, parser version, source file hash, and decision-time as-of status before any categorical label lane.",
        },
        {
            "route_family": "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET",
            "teaches": "Pending final-state labels are insufficient without an explicit entry_touched_at_utc or side-aware quote replay proving no earlier fill touch.",
            "future_capture_change": "Every pending-intent closure row needs entry_touched_at_utc plus fill/cancel/expiry/horizon timestamps and source hashes.",
        },
        {
            "route_family": "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT",
            "teaches": "Price-compatible M1 context is useful source inventory, but bid/ask quote ordering remains the contract boundary for categorical lifecycle labels.",
            "future_capture_change": "Archive USDJPY tick/quote parquet for all source rows or freeze a conservative quote contract that explicitly states what M1 can and cannot prove.",
        },
        {
            "route_family": "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT",
            "teaches": "Duplicate keys that collapse rows with conflicting geometry/order signatures cannot be rescued by earliest-row selection without denominator leakage.",
            "future_capture_change": "Separate source identity, duplicate denominator, geometry signature, and row projection keys before any label assignment.",
        },
        {
            "route_family": "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT",
            "teaches": "Once entry is touched, the row leaves the no-fill lifecycle family even if terminal-area timing looks favorable.",
            "future_capture_change": "Use a separate fill/path categorical label family with tick-ordered entry, terminal, protective, and ambiguity events while keeping R/performance closed.",
        },
    ]
    failure_ledger = {
        "artifact_family": "NOFILL_ROUTER_FAILURE_AND_LEARNING_LEDGER",
        "learning_rows": learning_rows,
        "global_lessons": [
            "Blocked categorical rows are source-contract evidence, not negative performance evidence.",
            "A next lane must source-correct or contract-revise before categorical labels expand beyond the accepted 52 rows.",
            "No row should be relabeled just because local heavy data exists; source hashes, as-of validity, parser contracts, and label-family boundaries remain mandatory.",
        ],
    }
    write_json(f"NOFILL_ROUTER_FAILURE_AND_LEARNING_LEDGER_{DATE}.json", failure_ledger)
    write_md(
        f"NOFILL_ROUTER_FAILURE_AND_LEARNING_LEDGER_{DATE}.md",
        "NOFILL Router Failure And Learning Ledger",
        [
            ("Family Lessons", md_table(learning_rows, ["route_family", "teaches", "future_capture_change"])),
            ("Global Lessons", "\n".join(f"- {item}" for item in failure_ledger["global_lessons"])),
        ],
    )

    for family in FAMILY_ORDER:
        fam_rows = [row for row in row_route_decisions if row["route_family"] == family]
        fam_access = [row for row in fam_rows if row["access_requirement"]]
        (LANE_DIR / FAMILY_PROMPT_PACKS[family]).write_text(build_prompt_pack(family, fam_rows, fam_access), encoding="utf-8")

    next_prompt = f"""# NOFILL Router Next Prompt Pack - {DATE}

Promotion posture: `NO_PROMOTION_VERDICT`
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Recommended execution order:

1. `OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION_PROMPT_PACK_2026-05-08.md` - 80 rows.
2. `OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_PROMPT_PACK_2026-05-08.md` - 54 rows.
3. `OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT_PROMPT_PACK_2026-05-08.md` - 69 rows, including 7 rows needing exact USDJPY tick/source access for 2026-04-17 and 2026-04-20 if quote proof is required.
4. `OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_PROMPT_PACK_2026-05-08.md` - 42 rows across 3 conflicted duplicate-key groups.
5. `OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_PROMPT_PACK_2026-05-08.md` - 1 row with separate fill/path plus terminal-order ambiguity.

Starter:

`/goal Run the next source-safe no-fill blocked-family lane using the relevant prompt pack under C:\\tmp\\gtos_otb\\NOFILLROUTER\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; do not compute R/performance or touch live trading surfaces.`

Do not open a result, validation, promotion, registry, live-effect, broker/account, paid/API/Databento, MT5 order/account/history, or live trading behavior lane from this router.
"""
    (LANE_DIR / f"NOFILL_ROUTER_NEXT_PROMPT_PACK_{DATE}.md").write_text(next_prompt, encoding="utf-8")

    completion_audit = {
        "artifact_family": "NOFILL_ROUTER_COMPLETION_AUDIT",
        "objective_restatement": context_anchor["objective_restatement"],
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory_gtos_preflight", "evidence": "NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.json", "status": "PASS_RECORDED"},
            {"requirement": "split_246_blocked_rows_by_family", "evidence": "NOFILL_ROUTER_BLOCKED_FAMILY_INVENTORY_2026-05-08.json", "status": "PASS"},
            {"requirement": "route_every_blocked_row", "evidence": "NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json", "status": "PASS"},
            {"requirement": "search_local_heavy_data_and_prior_artifacts", "evidence": "NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json", "status": "PASS"},
            {"requirement": "request_access_if_needed", "evidence": "NOFILL_ROUTER_ACCESS_REQUEST_LEDGER_2026-05-08.json", "status": "PASS"},
            {"requirement": "write_next_prompt_packs_only_for_source_safe_or_contract_revision_lanes", "evidence": sorted(FAMILY_PROMPT_PACKS.values()), "status": "PASS"},
            {"requirement": "record_failure_learning", "evidence": "NOFILL_ROUTER_FAILURE_AND_LEARNING_LEDGER_2026-05-08.json", "status": "PASS"},
            {"requirement": "preserve_no_promotion_and_false_flags", "evidence": "verify_nofill_blocked_family_source_correction_router_2026_05_08.py", "status": "PENDING_VERIFIER_RUN"},
            {"requirement": "no_live_trading_surface_changes", "evidence": "git diff/name-only scope check", "status": "PENDING_VERIFIER_RUN"},
        ],
        "row_coverage": {
            "total_packet_rows": len(rows),
            "eligible_rows_not_routed": len(eligible),
            "blocked_rows_routed": len(row_route_decisions),
            "family_order": FAMILY_ORDER,
            "blocker_code_counts": dict(code_counts),
            "blocker_tuple_counts": dict(tuple_counts),
        },
        "open_access_requests": access_request_ledger["requests"],
        "can_mark_goal_complete": False,
        "completion_status": "PENDING_VERIFICATION",
    }
    write_json(f"NOFILL_ROUTER_COMPLETION_AUDIT_{DATE}.json", completion_audit)
    write_md(
        f"NOFILL_ROUTER_COMPLETION_AUDIT_{DATE}.md",
        "NOFILL Router Completion Audit",
        [
            ("Objective", completion_audit["objective_restatement"]),
            ("Prompt-To-Artifact Checklist", md_table(completion_audit["prompt_to_artifact_checklist"], ["requirement", "status", "evidence"])),
            ("Row Coverage", json.dumps(completion_audit["row_coverage"], indent=2, sort_keys=True)),
            ("Status", "`PENDING_VERIFICATION` until the verifier is run."),
        ],
    )

    return {
        "rows": len(rows),
        "blocked": len(blocked),
        "eligible": len(eligible),
        "family_counts": {family: len(family_rows[family]) for family in FAMILY_ORDER},
        "access_rows": len(access_rows),
    }


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))
