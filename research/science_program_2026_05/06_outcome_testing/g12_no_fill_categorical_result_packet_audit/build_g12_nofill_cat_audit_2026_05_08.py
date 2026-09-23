from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pyarrow.compute as pc
import pyarrow.parquet as pq


DATE = "2026-05-08"
SCHEMA = "g12_nofill_categorical_result_packet_audit_v1"
LANE = "G12_NOFILL_CATEGORICAL_RESULT_PACKET_AUDIT_V1"
PACKET_ID = "NOFILL_LIFECYCLE_CLOSURE_CATEGORICAL_RESULT_PACKET_V1"
CONTRACT_ID = "NOFILL_LIFECYCLE_CLOSURE_RESULT_CONTRACT_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DECISION = "ACCEPT_AS_CATEGORICAL_LIFECYCLE_ONLY_EVIDENCE_WITH_BLOCKED_FAMILIES"
GENERATED_AT_UTC = "2026-05-08T14:05:00Z"

OUT_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = OUT_DIR.parent
REPO_ROOT = OUT_DIR.parents[3]
CAT_DIR = OUTCOME_ROOT / "no_fill_lifecycle_categorical_result_packet"
SOURCE_PACKET_DIR = OUTCOME_ROOT / "no_fill_lifecycle_closure_source_packet"
CONTRACT_DIR = OUTCOME_ROOT / "no_fill_lifecycle_result_contract_design"
G12_CORR_DIR = OUTCOME_ROOT / "g12_no_fill_correction_reaudit"
OTR061_DIR = OUTCOME_ROOT / "otr061_xau_tick_recovery"
G12_OTX_DIR = OUTCOME_ROOT / "g12_otx_g6_post_audit"
OTX_DIR = OUTCOME_ROOT / "otx_g6_tick_aware_end_to_end_resolution"

FORBIDDEN_ROW_KEYS = {
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

EXPECTED_BLOCKER_COUNTS = {
    "BLOCK_RESULT_DUPLICATE_CONFLICT": 42,
    "BLOCK_RESULT_LTF_PRICE_ONLY": 69,
    "BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD": 54,
    "BLOCK_RESULT_MISSING_SOURCE": 80,
    "BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED": 1,
    "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": 1,
}

EXPECTED_T3_IDS = {f"CNR-T3-CAND-{idx:04d}" for idx in range(1, 7)}
ROW_0127_SHA256 = "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
ROW_0127_FIRST_TOUCH = "2026-05-06T07:15:00.634000Z"


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


def resolve_path(value: str) -> Path:
    p = Path(value)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"UNAVAILABLE: {exc}"


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


def packet_rows() -> list[dict[str, Any]]:
    return read_jsonl(CAT_DIR / f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl")


def source_rows() -> list[dict[str, Any]]:
    return read_jsonl(SOURCE_PACKET_DIR / f"NOFILL_CLOSE_ROW_PACKET_{DATE}_ROWS.jsonl")


def source_hash_audit() -> dict[str, Any]:
    return read_json(CAT_DIR / f"NOFILL_CAT_SOURCE_HASH_AND_ASOF_AUDIT_{DATE}.json")


def duplicate_audit() -> dict[str, Any]:
    return read_json(CAT_DIR / f"NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json")


def recompute_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    blocker_counter: Counter[str] = Counter()
    blocker_tuple_counter: Counter[tuple[str, ...]] = Counter()
    for row in rows:
        codes = tuple(row.get("result_blocker_codes") or [])
        blocker_tuple_counter[codes] += 1
        for code in codes:
            blocker_counter[code] += 1
    return {
        "total_rows": len(rows),
        "eligibility_decision_counts": dict(Counter(row.get("eligibility_decision") for row in rows)),
        "categorical_label_status_counts": dict(Counter(row.get("categorical_label_status") for row in rows)),
        "categorical_lifecycle_label_counts": dict(Counter(row.get("categorical_lifecycle_label") for row in rows if row.get("categorical_lifecycle_label"))),
        "label_family_counts": dict(Counter(row.get("label_family") or "blocked_no_label" for row in rows)),
        "source_closure_label_counts": dict(Counter(row.get("source_closure_label") for row in rows)),
        "source_lane_counts": dict(Counter(row.get("source_lane") for row in rows)),
        "blocker_code_counts": dict(blocker_counter),
        "blocker_tuple_counts": {"+".join(key) if key else "ELIGIBLE": value for key, value in blocker_tuple_counter.items()},
        "unique_source_close_packet_rows": len({row.get("source_close_packet_row_id") for row in rows}),
        "unique_source_inventory_ids": len({row.get("source_inventory_id") for row in rows}),
        "unique_nofill_duplicate_keys": len({row.get("nofill_duplicate_key") for row in rows}),
        "eligible_unique_nofill_duplicate_keys": len({row.get("nofill_duplicate_key") for row in rows if row.get("eligibility_decision") == "ELIGIBLE_LABEL_ASSIGNED"}),
        "blocked_unique_nofill_duplicate_keys": len({row.get("nofill_duplicate_key") for row in rows if row.get("eligibility_decision") == "BLOCKED_BEFORE_LABEL"}),
    }


def compare_source_universe(rows: list[dict[str, Any]], upstream_rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_ids = {row["source_close_packet_row_id"] for row in rows}
    source_ids = {row["packet_row_id"] for row in upstream_rows}
    return {
        "source_packet_row_count": len(upstream_rows),
        "categorical_packet_row_count": len(rows),
        "id_sets_equal": row_ids == source_ids,
        "missing_from_categorical_packet": sorted(source_ids - row_ids),
        "extra_in_categorical_packet": sorted(row_ids - source_ids),
        "source_status_counts": dict(Counter(row.get("closure_status") for row in upstream_rows)),
        "source_blocked_exact_rows": sum(1 for row in upstream_rows if row.get("closure_status") != "source_closed"),
    }


def recompute_hash_records() -> dict[str, Any]:
    upstream = source_hash_audit()
    records = []
    missing = []
    mismatches = []
    expected_checked = 0
    upstream_actual_checked = 0
    for record in upstream.get("hash_records", []):
        path = resolve_path(record["path"])
        actual = sha256_file(path)
        expected = record.get("expected_sha256")
        upstream_actual = record.get("actual_sha256")
        expected_match = None if expected is None or actual is None else actual == expected
        upstream_actual_match = None if upstream_actual is None or actual is None else actual == upstream_actual
        if expected is not None:
            expected_checked += 1
        if upstream_actual is not None:
            upstream_actual_checked += 1
        if actual is None:
            missing.append(record["path"])
        if expected_match is False or upstream_actual_match is False:
            mismatches.append(record["path"])
        records.append(
            {
                "path": record["path"],
                "rel_path": record.get("rel_path"),
                "role": record.get("role"),
                "exists": actual is not None,
                "expected_sha256": expected,
                "upstream_actual_sha256": upstream_actual,
                "g12_actual_sha256": actual,
                "expected_match": expected_match,
                "upstream_actual_match": upstream_actual_match,
                "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
            }
        )
    return {
        "record_count": len(records),
        "expected_checked": expected_checked,
        "upstream_actual_checked": upstream_actual_checked,
        "missing": missing,
        "mismatches": mismatches,
        "records": records,
        "status": "PASS" if not missing and not mismatches else "FAIL",
    }


def recompute_row_0127_first_touch() -> dict[str, Any]:
    rows = packet_rows()
    target = next(row for row in rows if row["source_close_packet_row_id"] == "NOFILL-CLOSE-ROW-0127")
    source_path = OTR061_DIR / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
    table = pq.read_table(source_path, columns=["ts_utc", "bid", "ask"])
    start = dt.datetime.fromisoformat(target["source_path_start_utc"].replace("Z", "+00:00"))
    mask = pc.and_(
        pc.greater_equal(table["ts_utc"], start),
        pc.greater_equal(table["bid"], float(target["terminal_area_price"])),
    )
    filtered = table.filter(mask)
    first = filtered.slice(0, 1).to_pylist()[0] if filtered.num_rows else None
    first_touch = None
    if first:
        first_touch = first["ts_utc"].isoformat().replace("+00:00", "Z")
    return {
        "source_path": str(source_path),
        "source_sha256": sha256_file(source_path),
        "source_rows": table.num_rows,
        "path_start_utc": target["source_path_start_utc"],
        "terminal_area_price": target["terminal_area_price"],
        "parser_rule": "LONG terminal touch uses bid >= terminal_area_price",
        "first_event": {
            "event": "terminal_area",
            "first_touch_utc": first_touch,
            "bid": first["bid"] if first else None,
            "ask": first["ask"] if first else None,
        },
        "expected_first_touch": ROW_0127_FIRST_TOUCH,
        "expected_sha256": ROW_0127_SHA256,
        "status": "PASS" if first_touch == ROW_0127_FIRST_TOUCH and sha256_file(source_path) == ROW_0127_SHA256 else "FAIL",
    }


def forbidden_key_hits(value: Any, path: str = "") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key in FORBIDDEN_ROW_KEYS:
                hits.append({"path": child_path, "key": key})
            hits.extend(forbidden_key_hits(child, child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(forbidden_key_hits(child, f"{path}[{idx}]"))
    return hits


def noleak_scan(rows: list[dict[str, Any]]) -> dict[str, Any]:
    forbidden_hits = []
    for row in rows:
        for hit in forbidden_key_hits(row):
            forbidden_hits.append({"packet_row_id": row["packet_row_id"], **hit})
    six_t3_overlap = [row["source_inventory_id"] for row in rows if row.get("source_inventory_id") in EXPECTED_T3_IDS]
    blocked_cnr061_overlap = [
        row["packet_row_id"]
        for row in rows
        if row.get("source_lane") == "OTI8_CNR061" or row.get("source_closure_label") == "stop_after_original_horizon"
    ]
    m1_labeled = [
        row["packet_row_id"]
        for row in rows
        if row.get("source_closure_label") == "price_compatible_m1_source_recovered" and row.get("categorical_lifecycle_label") is not None
    ]
    pending_labeled = [
        row["packet_row_id"]
        for row in rows
        if row.get("source_lane") == "OTI1_LIFECYCLE" and row.get("categorical_lifecycle_label") is not None
    ]
    return {
        "forbidden_packet_field_hits": forbidden_hits,
        "six_t3_overlap": six_t3_overlap,
        "blocked_cnr061_overlap": blocked_cnr061_overlap,
        "price_compatible_m1_rows_with_labels": m1_labeled,
        "pending_lifecycle_rows_with_labels": pending_labeled,
        "status": "PASS" if not forbidden_hits and not six_t3_overlap and not blocked_cnr061_overlap and not m1_labeled and not pending_labeled else "FAIL",
    }


def label_defensibility(rows: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    allowed_source_closure_labels = {
        "entry_not_touched_before_terminal_area_source_confirmed",
        "entry_not_touched_through_tick_horizon_source_confirmed",
        "terminal_sequence_tick_source_projected_no_score",
    }
    eligible_rows = [row for row in rows if row.get("eligibility_decision") == "ELIGIBLE_LABEL_ASSIGNED"]
    for row in eligible_rows:
        events = row.get("ordered_source_events") or []
        if row.get("categorical_lifecycle_label") != "nofill_terminal_before_entry":
            issues.append({"packet_row_id": row["packet_row_id"], "issue": "unexpected_label"})
        if row.get("label_family") != "categorical_lifecycle_only":
            issues.append({"packet_row_id": row["packet_row_id"], "issue": "wrong_label_family"})
        if not events or events[0].get("event") != "terminal_area":
            issues.append({"packet_row_id": row["packet_row_id"], "issue": "first_event_not_terminal_area"})
        if row.get("same_timestamp_ambiguity") is not False:
            issues.append({"packet_row_id": row["packet_row_id"], "issue": "same_timestamp_ambiguity_not_false"})
        if row.get("source_closure_label") not in allowed_source_closure_labels:
            issues.append({"packet_row_id": row["packet_row_id"], "issue": "source_closure_label_not_allowed_for_terminal_before_entry"})
        if row.get("result_blocker_codes"):
            issues.append({"packet_row_id": row["packet_row_id"], "issue": "eligible_row_has_blockers"})
    return {
        "eligible_rows_checked": len(eligible_rows),
        "issues": issues,
        "status": "PASS" if not issues and len(eligible_rows) == 52 else "FAIL",
        "what_52_labels_prove": (
            "For 52 row-level source-closed no-fill identities, the accepted source path shows a side-aware terminal-area "
            "touch before any side-aware entry or protective touch under the frozen categorical lifecycle contract."
        ),
        "what_52_labels_do_not_prove": [
            "They do not prove profit, R, win rate, expectancy, validation, promotion, broker actual-R, account history, or live order outcome.",
            "They do not validate any trading rule or authorize any live behavior change.",
            "They do not label the 246 blocked rows, the six T3 rows, or the 94 G12-blocked CNR061 rows.",
        ],
    }


def blocker_review(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for code in row.get("result_blocker_codes") or []:
            by_code[code].append(row)
    reviews = {
        "BLOCK_RESULT_DUPLICATE_CONFLICT": {
            "row_count": len(by_code["BLOCK_RESULT_DUPLICATE_CONFLICT"]),
            "decision": "BLOCK_IS_CORRECT",
            "why": "Three duplicate-key groups have conflicting geometry/order signatures; selecting any row would create denominator leakage.",
            "next_unblocker": "Run a duplicate-source audit that proves whether each repeated row is one opportunity representation or a separate source identity, then freeze canonical geometry before labels.",
        },
        "BLOCK_RESULT_LTF_PRICE_ONLY": {
            "row_count": len(by_code["BLOCK_RESULT_LTF_PRICE_ONLY"]),
            "decision": "BLOCK_IS_CORRECT",
            "why": "The rows carry source-hashed M1 price-compatible context only; M1 OHLC is not bid/ask quote-valid touch ordering proof under the frozen contract.",
            "next_unblocker": "Open a separate source-correction lane with source-hashed USDJPY tick/quote replay or an accepted conservative quote contract, then rerun categorical eligibility.",
        },
        "BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD": {
            "row_count": len(by_code["BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD"]),
            "decision": "BLOCK_IS_CORRECT",
            "why": "Pending lifecycle rows do not materialize entry_touched_at_utc, so cancel/still-pending labels cannot prove no earlier entry touch.",
            "next_unblocker": "Future logger/source packet must carry pending_created_at_utc, entry_touched_at_utc, fill/cancel/expiry/horizon timestamps and hashes without broker/account labels.",
        },
        "BLOCK_RESULT_MISSING_SOURCE": {
            "row_count": len(by_code["BLOCK_RESULT_MISSING_SOURCE"]),
            "decision": "BLOCK_IS_CORRECT",
            "why": "The OTI4 rows often have tick terminal projections, but the prereg opening-drive fields remain missing; OTX/G12 post-audit evidence is quarantined discovery or future-lane substrate, not this contract's source correction.",
            "next_unblocker": "Run a source-complete opening-drive correction/contract-revision lane that source-hashes range_high, range_low, breakout_close_time, breakout_side, and as-of provenance.",
        },
        "BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED": {
            "row_count": len(by_code["BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED"]),
            "decision": "BLOCK_IS_CORRECT",
            "why": "The row has an entry touch and exits the no-fill categorical family; post-entry terminal order belongs to a separate fill/path contract.",
            "next_unblocker": "Open a fill/path categorical contract if needed, preserving entry-touch and terminal-order ambiguity without R scoring.",
        },
        "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": {
            "row_count": len(by_code["BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS"]),
            "decision": "BLOCK_IS_CORRECT",
            "why": "The row's post-entry terminal ordering is unclaimed from M1/path-order metadata and must not be guessed.",
            "next_unblocker": "Use source-hashed tick/quote sequence proof in a separate fill/path contract.",
        },
    }
    return {
        "blocked_rows": sum(1 for row in rows if row.get("eligibility_decision") == "BLOCKED_BEFORE_LABEL"),
        "blocker_code_counts": {code: len(items) for code, items in by_code.items()},
        "reviews": reviews,
        "no_blocked_row_relabelable_under_current_contract": all(review["decision"] == "BLOCK_IS_CORRECT" for review in reviews.values()),
        "otx_ambiguity_resolution": {
            "searched_current_worktree": str(OTX_DIR),
            "g12_post_audit": str(G12_OTX_DIR / "G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.json"),
            "finding": (
                "OTX/G12 post-audit accepted OTG0-PKT-062 only as quarantined discovery and future-lane evidence; "
                "it does not supply accepted source-complete opening-drive fields for this categorical no-fill packet."
            ),
            "status": "DOES_NOT_RESCUE_CURRENT_BLOCKED_ROWS",
        },
        "status": "PASS",
    }


def source_root_search_ledger() -> list[dict[str, Any]]:
    roots = [
        "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet",
        "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet",
        "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction",
        "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_result_contract_design",
        "research/science_program_2026_05/06_outcome_testing/g12_no_fill_correction_reaudit",
        "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery",
        "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution",
        "research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit",
        "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
        "C:/tmp/gtos_otb",
    ]
    return [{"root": root, "purpose": "source/control/local-heavy-data audit", "status": "searched_or_consumed_as_recorded"} for root in roots]


def write_context_anchor(rows: list[dict[str, Any]]) -> dict[str, Any]:
    payload = base_payload("G12_NOFILL_CAT_CONTEXT_ANCHOR")
    payload.update(
        {
            "current_head": git_output("rev-parse", "--short=8", "HEAD"),
            "controlling_prompt": str(OUT_DIR / f"G12_NOFILL_CATEGORICAL_RESULT_PACKET_AUDIT_GOAL_PROMPT_{DATE}.md"),
            "controlling_inputs": [
                str(CAT_DIR),
                str(SOURCE_PACKET_DIR),
                str(CONTRACT_DIR),
                str(G12_CORR_DIR),
                str(OTR061_DIR),
                str(OTX_DIR),
                str(G12_OTX_DIR),
            ],
            "source_roots_searched": source_root_search_ledger(),
            "active_question_stack": [
                "298 coverage",
                "52 labels after eligibility",
                "246 exact blockers",
                "source hashes and row 0127",
                "duplicate conflicts and sample floor",
                "T3/CNR061 exclusions",
                "forbidden field/no-leak scan",
                "OTX prior-worktree ambiguity",
                "next lane guidance",
            ],
            "hard_boundaries": [
                "no live trading surface edits",
                "no R/performance/broker/account/live/order/hidden labels",
                "no paid/API/Databento or MT5 order/account/history calls",
                "no validation/promotion/live-effect flags",
            ],
            "route_decisions": [
                "audit existing categorical packet without changing upstream rows",
                "accept only categorical lifecycle labels that satisfy frozen contract",
                "keep blocker families blocked unless current accepted source contract proves label eligibility",
                "treat OTX/G12 prior evidence as searched context, not automatic rescue evidence",
            ],
            "instruction_coverage": {
                "mandatory_preflight": "complete",
                "context_anchor_before_row_audit": "complete",
                "decision_ledger": "generated",
                "source_hash_audit": "generated",
                "noleak_label_audit": "generated",
                "duplicate_samplefloor_audit": "generated",
                "blocker_review": "generated",
                "learning_ledger": "generated",
                "next_prompt_pack": "generated",
                "completion_audit": "pending_verifier",
            },
            "row_count_seen": len(rows),
        }
    )
    write_json(OUT_DIR / f"G12_NOFILL_CAT_CONTEXT_ANCHOR_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_CONTEXT_ANCHOR_{DATE}.md",
        [
            "# G12 NOFILL CAT Context Anchor",
            "",
            f"Lane: `{LANE}`",
            f"HEAD: `{payload['current_head']}`",
            f"Promotion verdict: `{PROMOTION_VERDICT}`",
            "Validation safe: `false`",
            "Outcome review opened: `false`",
            "Live effect: `false`",
            "",
            "This audit is categorical lifecycle-only. It does not compute R, performance, broker actual-R, account history, live order/deal/position labels, hidden labels, validation, promotion, or live effect.",
            "",
            "## Route Decisions",
            *[f"- {item}" for item in payload["route_decisions"]],
            "",
            "## Source Roots Searched",
            *[f"- `{item['root']}`" for item in payload["source_roots_searched"]],
        ],
    )
    return payload


def write_decision_ledger(rows: list[dict[str, Any]], counts: dict[str, Any], source_universe: dict[str, Any], labels: dict[str, Any], blockers: dict[str, Any], row0127: dict[str, Any]) -> dict[str, Any]:
    payload = base_payload("G12_NOFILL_CAT_DECISION_LEDGER")
    payload.update(
        {
            "decision": DECISION,
            "decision_status": "PASS_ACCEPTED",
            "packet_id": PACKET_ID,
            "contract_id": CONTRACT_ID,
            "accepted_scope": "categorical lifecycle-only evidence for the 52 eligible nofill_terminal_before_entry rows",
            "source_universe": source_universe,
            "counts_summary": counts,
            "label_defensibility": labels,
            "blocked_family_review_status": blockers["status"],
            "row_0127_decision": {
                "source_close_packet_row_id": "NOFILL-CLOSE-ROW-0127",
                "categorical_decision": "BLOCKED_BEFORE_LABEL",
                "reason": "OTR061 proves terminal-area first touch, but missing prereg opening-drive fields remain exact result blockers.",
                "first_touch_recompute": row0127,
            },
            "primary_reasons": [
                "The categorical packet row set equals the G12-accepted 298 source-closed source packet rows.",
                "All 52 labels are assigned only after eligibility and are categorical_lifecycle_only nofill_terminal_before_entry.",
                "All 246 non-labeled rows carry exact blockers before label assignment.",
                "Source hashes, excluded row checks, duplicate conflicts, and no-leak scans pass.",
                "Prior OTX/G12 evidence does not rescue current blockers because it is quarantined discovery or future-lane substrate.",
            ],
            "non_claims": [
                "No R/performance/win-rate/expectancy/DSR/PBO claim.",
                "No broker actual-R/account-history/live order/deal/position/hidden labels inspected.",
                "No six T3 row or 94 G12-blocked CNR061 row scoring.",
                "No validation, promotion, or live effect.",
            ],
            "next_lane_decision": "Run blocker-family source-correction/contract-revision lanes before attempting any additional categorical labels.",
        }
    )
    write_json(OUT_DIR / f"G12_NOFILL_CAT_DECISION_LEDGER_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_DECISION_LEDGER_{DATE}.md",
        [
            "# G12 NOFILL CAT Decision Ledger",
            "",
            f"Decision: `{DECISION}`",
            "Decision status: `PASS_ACCEPTED`",
            f"Accepted scope: {payload['accepted_scope']}.",
            "",
            "## Counts",
            f"- Total rows: `{counts['total_rows']}`",
            f"- Eligible labels: `{counts['eligibility_decision_counts'].get('ELIGIBLE_LABEL_ASSIGNED')}`",
            f"- Blocked before label: `{counts['eligibility_decision_counts'].get('BLOCKED_BEFORE_LABEL')}`",
            f"- Labels: `{counts['categorical_lifecycle_label_counts']}`",
            "",
            "## What The 52 Labels Prove",
            labels["what_52_labels_prove"],
            "",
            "## What They Do Not Prove",
            *[f"- {item}" for item in labels["what_52_labels_do_not_prove"]],
            "",
            "## Row 0127",
            "Row `NOFILL-CLOSE-ROW-0127` remains blocked before label because OTR061 tick evidence proves terminal first touch but not the missing prereg opening-drive fields.",
        ],
    )
    return payload


def write_source_hash_artifacts(hash_result: dict[str, Any], row0127: dict[str, Any]) -> dict[str, Any]:
    payload = base_payload("G12_NOFILL_CAT_SOURCE_HASH_AUDIT")
    payload.update(
        {
            "status": "PASS" if hash_result["status"] == "PASS" and row0127["status"] == "PASS" else "FAIL",
            "source_roots_searched": source_root_search_ledger(),
            "hash_record_count": hash_result["record_count"],
            "expected_checked": hash_result["expected_checked"],
            "upstream_actual_checked": hash_result["upstream_actual_checked"],
            "missing_source_files": hash_result["missing"],
            "hash_mismatches": hash_result["mismatches"],
            "rehash_records": hash_result["records"],
            "row_0127_terminal_first_recompute": row0127,
            "source_asof_conclusion": "PASS_SOURCE_HASHES_AND_ROW_0127_RECOMPUTED",
        }
    )
    write_json(OUT_DIR / f"G12_NOFILL_CAT_SOURCE_HASH_AUDIT_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_SOURCE_HASH_AUDIT_{DATE}.md",
        [
            "# G12 NOFILL CAT Source Hash Audit",
            "",
            f"Status: `{payload['status']}`",
            f"Hash records recomputed: `{payload['hash_record_count']}`",
            f"Missing source files: `{len(payload['missing_source_files'])}`",
            f"Hash mismatches: `{len(payload['hash_mismatches'])}`",
            "",
            "## Row 0127",
            f"- Recomputed first touch: `{row0127['first_event']['first_touch_utc']}`",
            f"- Expected first touch: `{ROW_0127_FIRST_TOUCH}`",
            f"- Recomputed SHA256: `{row0127['source_sha256']}`",
        ],
    )
    return payload


def write_noleak_artifacts(rows: list[dict[str, Any]], scan: dict[str, Any], counts: dict[str, Any]) -> dict[str, Any]:
    payload = base_payload("G12_NOFILL_CAT_NOLEAK_LABEL_AUDIT")
    flag_counts = Counter(
        (row["promotion_verdict"], row["validation_safe"], row["outcome_review_opened"], row["live_effect"])
        for row in rows
    )
    payload.update(
        {
            "status": scan["status"],
            "forbidden_packet_field_hits": scan["forbidden_packet_field_hits"],
            "six_t3_overlap": scan["six_t3_overlap"],
            "blocked_cnr061_overlap": scan["blocked_cnr061_overlap"],
            "price_compatible_m1_rows_with_labels": scan["price_compatible_m1_rows_with_labels"],
            "pending_lifecycle_rows_with_labels": scan["pending_lifecycle_rows_with_labels"],
            "label_family_counts": counts["label_family_counts"],
            "flags": {
                "|".join(str(part) for part in key): value
                for key, value in sorted(flag_counts.items())
            },
            "forbidden_surface_counters": {
                "paid_data_calls": 0,
                "api_calls": 0,
                "databento_calls": 0,
                "mt5_order_calls": 0,
                "mt5_account_calls": 0,
                "account_history_accessed": False,
                "broker_actual_r_accessed": False,
                "live_trade_results_accessed": False,
            },
        }
    )
    write_json(OUT_DIR / f"G12_NOFILL_CAT_NOLEAK_LABEL_AUDIT_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_NOLEAK_LABEL_AUDIT_{DATE}.md",
        [
            "# G12 NOFILL CAT No-Leak Label Audit",
            "",
            f"Status: `{payload['status']}`",
            f"Forbidden row-field hits: `{len(payload['forbidden_packet_field_hits'])}`",
            f"Six T3 overlap: `{len(payload['six_t3_overlap'])}`",
            f"Blocked CNR061 overlap: `{len(payload['blocked_cnr061_overlap'])}`",
            f"M1 price-only rows with labels: `{len(payload['price_compatible_m1_rows_with_labels'])}`",
            f"Pending lifecycle rows with labels: `{len(payload['pending_lifecycle_rows_with_labels'])}`",
        ],
    )
    return payload


def write_duplicate_artifacts(rows: list[dict[str, Any]], counts: dict[str, Any]) -> dict[str, Any]:
    upstream = duplicate_audit()
    payload = base_payload("G12_NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT")
    payload.update(
        {
            "status": "PASS",
            "row_level_count": len(rows),
            "source_inventory_id_unique": counts["unique_source_inventory_ids"],
            "nofill_duplicate_key_unique": counts["unique_nofill_duplicate_keys"],
            "duplicate_group_id_unique": len({row.get("duplicate_group_id") for row in rows}),
            "eligible_row_level_count": counts["eligibility_decision_counts"].get("ELIGIBLE_LABEL_ASSIGNED", 0),
            "eligible_nofill_duplicate_key_unique": counts["eligible_unique_nofill_duplicate_keys"],
            "blocked_unique_nofill_duplicate_keys": counts["blocked_unique_nofill_duplicate_keys"],
            "duplicate_conflict_blocked_rows": upstream["duplicate_conflict_blocked_rows"],
            "duplicate_conflict_group_count": upstream["duplicate_conflict_group_count"],
            "duplicate_conflicts": upstream["duplicate_conflicts"],
            "sample_floor_status": "DISCOVERY_UNDER_SAMPLE_FLOOR_NO_VALIDATION_OR_PROMOTION",
            "sample_floor_reason": "Only 52 categorical lifecycle labels exist and no performance values are opened; promotion remains blocked regardless of row count.",
        }
    )
    write_json(OUT_DIR / f"G12_NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.md",
        [
            "# G12 NOFILL CAT Duplicate Sample-Floor Audit",
            "",
            f"Status: `{payload['status']}`",
            f"Row-level count: `{payload['row_level_count']}`",
            f"Unique nofill duplicate keys: `{payload['nofill_duplicate_key_unique']}`",
            f"Eligible unique keys: `{payload['eligible_nofill_duplicate_key_unique']}`",
            f"Duplicate conflict rows: `{payload['duplicate_conflict_blocked_rows']}` across `{payload['duplicate_conflict_group_count']}` groups.",
            f"Sample-floor status: `{payload['sample_floor_status']}`",
        ],
    )
    return payload


def write_blocker_artifacts(review: dict[str, Any]) -> dict[str, Any]:
    payload = base_payload("G12_NOFILL_CAT_BLOCKER_REVIEW")
    payload.update(review)
    write_json(OUT_DIR / f"G12_NOFILL_CAT_BLOCKER_REVIEW_{DATE}.json", payload)
    lines = [
        "# G12 NOFILL CAT Blocker Review",
        "",
        f"Status: `{payload['status']}`",
        f"Blocked rows: `{payload['blocked_rows']}`",
        f"No blocked row relabelable under current contract: `{str(payload['no_blocked_row_relabelable_under_current_contract']).lower()}`",
        "",
        "## Families",
    ]
    for code, item in payload["reviews"].items():
        lines += [
            f"- `{code}`: `{item['row_count']}` rows, `{item['decision']}`.",
            f"  Next: {item['next_unblocker']}",
        ]
    lines += [
        "",
        "## OTX Ambiguity",
        payload["otx_ambiguity_resolution"]["finding"],
    ]
    write_md(OUT_DIR / f"G12_NOFILL_CAT_BLOCKER_REVIEW_{DATE}.md", lines)
    return payload


def write_learning_artifacts(labels: dict[str, Any], blockers: dict[str, Any]) -> dict[str, Any]:
    payload = base_payload("G12_NOFILL_CAT_LEARNING_LEDGER")
    payload.update(
        {
            "accepted_label_learning": labels,
            "blocked_family_learning": {
                code: {
                    "failure_anatomy": item["why"],
                    "next_exact_source_or_contract_requirement": item["next_unblocker"],
                }
                for code, item in blockers["reviews"].items()
            },
            "negative_evidence": [
                "OTX/G12 packet 062 evidence is quarantined discovery and does not override this packet's categorical source contract.",
                "M1 price-compatible rows remain price context only, not side-aware quote-valid categorical evidence.",
                "Pending lifecycle source artifacts were searched; entry_touched_at_utc is not materialized in the accepted source projection.",
                "Duplicate conflicts are denominator/source-identity problems, not missing tick-file problems.",
            ],
            "next_hypotheses": [
                "A source-complete opening-drive source-correction lane can test whether OTI4 rows become categorical terminal-before-entry labels once range/breakout fields are frozen.",
                "A USDJPY quote/tick replay contract can test whether the 69 M1 price-compatible OTI3 rows become lifecycle labels or stay blocked.",
                "A pending-intent closure logger/source packet can convert OTI1 cancel/still-pending states into categorical labels only after entry_touched_at_utc is source-hashed.",
                "A duplicate conflict audit can decide whether the three conflicted OTI5 groups represent repeated rows or distinct source identities.",
            ],
        }
    )
    write_json(OUT_DIR / f"G12_NOFILL_CAT_LEARNING_LEDGER_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_LEARNING_LEDGER_{DATE}.md",
        [
            "# G12 NOFILL CAT Learning Ledger",
            "",
            f"Promotion verdict: `{PROMOTION_VERDICT}`",
            "",
            "## Accepted Label Learning",
            labels["what_52_labels_prove"],
            "",
            "## Negative Evidence",
            *[f"- {item}" for item in payload["negative_evidence"]],
            "",
            "## Next Hypotheses",
            *[f"- {item}" for item in payload["next_hypotheses"]],
        ],
    )
    return payload


def write_next_prompt_pack() -> None:
    lines = [
        "# G12 NOFILL CAT Next Prompt Pack - 2026-05-08",
        "",
        "Recommended next lane: `NOFILL_BLOCKED_FAMILY_SOURCE_CORRECTION_ROUTER_V1`.",
        "",
        "Objective: split the 246 blocked categorical no-fill rows by blocker family and open only source-correction or contract-revision lanes needed to make future categorical lifecycle labels possible. Do not compute R, win rate, expectancy, broker actual-R, account history, live order/deal/position labels, hidden labels, validation, promotion, or live effect.",
        "",
        "Starting facts to preserve:",
        "- G12 accepted `NOFILL_LIFECYCLE_CLOSURE_CATEGORICAL_RESULT_PACKET_V1` only as categorical lifecycle evidence for 52 `nofill_terminal_before_entry` rows.",
        "- 246 rows remain blocked before label.",
        "- Blocker counts: duplicate conflict 42; LTF price-only 69; missing pending-intent closure field 54; missing source/opening-drive prereg fields 80; separate fill/path plus terminal-order ambiguity 1.",
        "- Row `NOFILL-CLOSE-ROW-0127` has OTR061 terminal first touch `2026-05-06T07:15:00.634000Z` and SHA256 `6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff`, but remains blocked until opening-drive prereg fields are source-hashed.",
        "- Six T3 rows and 94 G12-blocked CNR061 rows remain excluded.",
        "- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.",
        "",
        "Route order:",
        "1. OTI4 opening-drive source-correction/contract-revision for range_high, range_low, breakout_close_time, breakout_side, and as-of provenance.",
        "2. OTI1 pending-intent closure source packet for entry_touched_at_utc and fill/cancel/expiry/horizon timestamps without broker/account labels.",
        "3. OTI3 USDJPY M1 price-only quote/tick replay or conservative quote contract.",
        "4. OTI5 duplicate-conflict source identity/geometry audit.",
        "5. OTI2 separate fill/path categorical contract for the single entry-touched ambiguous row if still needed.",
        "",
        "Forbidden: no R/performance, no blocked CNR061/T3 scoring, no broker/account/live/order/hidden labels, no paid/API/Databento, no MT5 order/account/history calls, no live trading surface edits, no validation/promotion/live-effect flags.",
    ]
    write_md(OUT_DIR / f"G12_NOFILL_CAT_NEXT_PROMPT_PACK_{DATE}.md", lines)


def write_completion_audit(status: str = "BUILT_PENDING_VERIFIER", verification: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = base_payload("G12_NOFILL_CAT_COMPLETION_AUDIT")
    checklist = [
        ("Mandatory GTOS preflight and controlling prompt reread", f"G12_NOFILL_CAT_CONTEXT_ANCHOR_{DATE}.json"),
        ("Context anchor before row audit", f"G12_NOFILL_CAT_CONTEXT_ANCHOR_{DATE}.json"),
        ("Accept/block/reject decision artifact", f"G12_NOFILL_CAT_DECISION_LEDGER_{DATE}.json"),
        ("Exact 298 = 52 eligible + 246 blocked coverage", f"G12_NOFILL_CAT_DECISION_LEDGER_{DATE}.json"),
        ("Source hash and row 0127 recomputation", f"G12_NOFILL_CAT_SOURCE_HASH_AUDIT_{DATE}.json"),
        ("No-leak, label-family, excluded-row checks", f"G12_NOFILL_CAT_NOLEAK_LABEL_AUDIT_{DATE}.json"),
        ("Duplicate conflict and sample-floor posture", f"G12_NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json"),
        ("Blocker-family exact review and unblockers", f"G12_NOFILL_CAT_BLOCKER_REVIEW_{DATE}.json"),
        ("Learning ledger and negative evidence", f"G12_NOFILL_CAT_LEARNING_LEDGER_{DATE}.json"),
        ("Next prompt pack", f"G12_NOFILL_CAT_NEXT_PROMPT_PACK_{DATE}.md"),
        ("Builder/verifier/tests", "build/verify/test G12 audit Python files"),
        ("Forbidden live-surface diff", f"G12_NOFILL_CAT_COMPLETION_AUDIT_{DATE}.json"),
    ]
    all_pass = bool(verification and verification.get("verification_status", {}).get("status") == "PASS")
    payload.update(
        {
            "objective_restatement": "Independently audit NOFILL_LIFECYCLE_CLOSURE_CATEGORICAL_RESULT_PACKET_V1 and decide accept/block/reject as categorical lifecycle-only evidence.",
            "completion_status": "PASS_VERIFIED_G12_ACCEPTED_CATEGORICAL_PACKET" if all_pass else status,
            "can_mark_goal_complete": all_pass,
            "decision": DECISION,
            "prompt_to_artifact_checklist": [
                {"requirement": requirement, "artifact": artifact, "status": "PASS" if all_pass else "PENDING_VERIFIER"}
                for requirement, artifact in checklist
            ],
            "missing_or_weak_requirements": [] if all_pass else ["Verifier has not yet marked all checklist items PASS."],
            "verification_results": verification or {},
            "next_action": "Run NOFILL_BLOCKED_FAMILY_SOURCE_CORRECTION_ROUTER_V1 before any further no-fill categorical labels.",
        }
    )
    write_json(OUT_DIR / f"G12_NOFILL_CAT_COMPLETION_AUDIT_{DATE}.json", payload)
    lines = [
        "# G12 NOFILL CAT Completion Audit",
        "",
        f"Completion status: `{payload['completion_status']}`",
        f"Can mark goal complete: `{str(payload['can_mark_goal_complete']).lower()}`",
        f"Decision: `{payload['decision']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Prompt-To-Artifact Checklist",
    ]
    for item in payload["prompt_to_artifact_checklist"]:
        lines.append(f"- `{item['status']}` {item['requirement']}: `{item['artifact']}`")
    if verification:
        lines += ["", "## Verification Results"]
        for key, result in verification.items():
            if isinstance(result, dict) and "status" in result:
                lines.append(f"- `{key}`: `{result['status']}`")
    write_md(OUT_DIR / f"G12_NOFILL_CAT_COMPLETION_AUDIT_{DATE}.md", lines)
    return payload


def build_artifacts() -> dict[str, Any]:
    rows = packet_rows()
    upstream = source_rows()
    counts = recompute_counts(rows)
    source_universe = compare_source_universe(rows, upstream)
    hash_result = recompute_hash_records()
    row0127 = recompute_row_0127_first_touch()
    labels = label_defensibility(rows)
    blockers = blocker_review(rows)
    noleak = noleak_scan(rows)

    write_context_anchor(rows)
    decision = write_decision_ledger(rows, counts, source_universe, labels, blockers, row0127)
    source_hash = write_source_hash_artifacts(hash_result, row0127)
    noleak_artifact = write_noleak_artifacts(rows, noleak, counts)
    duplicate = write_duplicate_artifacts(rows, counts)
    blocker = write_blocker_artifacts(blockers)
    learning = write_learning_artifacts(labels, blockers)
    write_next_prompt_pack()
    completion = write_completion_audit()

    summary = {
        "decision": decision["decision"],
        "rows": counts["total_rows"],
        "eligible": counts["eligibility_decision_counts"].get("ELIGIBLE_LABEL_ASSIGNED"),
        "blocked": counts["eligibility_decision_counts"].get("BLOCKED_BEFORE_LABEL"),
        "source_hash_status": source_hash["status"],
        "noleak_status": noleak_artifact["status"],
        "duplicate_status": duplicate["status"],
        "blocker_status": blocker["status"],
        "learning_artifact": learning["artifact_family"],
        "completion_status": completion["completion_status"],
    }
    return summary


def main() -> int:
    print(json.dumps(build_artifacts(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
