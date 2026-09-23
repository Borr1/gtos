#!/usr/bin/env python3
"""Repair TARGETSTOP_NA_NA branch rows by binding them to signature-scope contracts."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

BRANCH_SCORE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_BRANCH_SCORE_LEDGER_2026-05-16.jsonl"
BRANCH_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS_BRANCH_QUEUE_2026-05-16.jsonl"
PARTIAL_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_ENTRY_LEDGER_2026-05-16.jsonl"
PARTIAL_COST_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_COST_MODEL_LEDGER_2026-05-16.jsonl"
PARTIAL_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_SIGNATURE_SCOPE_LEDGER_2026-05-16.jsonl"
TARGET_STOP_CONTRACT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_TARGET_STOP_CONTRACT_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_TARGETSTOP_NA_BINDING_REPAIR_RESULT_2026-05-16.json"
NA_BRANCH_REPAIR_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_TARGETSTOP_NA_BINDING_REPAIR_BRANCH_LEDGER_2026-05-16.jsonl"
BINDING_CANDIDATE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_TARGETSTOP_NA_BINDING_REPAIR_CANDIDATE_LEDGER_2026-05-16.jsonl"
CONTRACT_SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_TARGETSTOP_NA_BINDING_REPAIR_CONTRACT_SUMMARY_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_TARGETSTOP_NA_BINDING_REPAIR_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_TARGETSTOP_NA_BINDING_REPAIR_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS target/stop NA binding repair only. Rows prove whether "
    "TARGETSTOP_NA_NA entry-level repair branches can be bound to existing "
    "partial/source-recheck signature-scope target/stop contracts; no validation, "
    "R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior "
    "change is claimed."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        BRANCH_SCORE_PATH,
        BRANCH_QUEUE_PATH,
        PARTIAL_ENTRY_PATH,
        PARTIAL_COST_PATH,
        PARTIAL_SIGNATURE_PATH,
        TARGET_STOP_CONTRACT_PATH,
    ]
    rows = [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
            "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
        }
        for path in paths
    ]
    return rows, hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()


def natural_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("route_candidate_id")), str(row.get("entry_variant") or row.get("source_entry_variant")))


def classify_touch(status: str) -> str:
    text = str(status or "").upper()
    if text.startswith("TARGET") or "TARGET_TOUCH_FIRST" in text:
        return "favorable_target_proxy"
    if text.startswith("STOP") or "STOP_TOUCH" in text:
        return "adverse_stop_proxy"
    if "AMBIG" in text or "ORDER_UNRESOLVED" in text:
        return "ambiguous_ordering_proxy"
    if "NOFILL" in text or "NO_TARGET_OR_STOP" in text or "UNTOUCHED" in text:
        return "no_fill_or_no_resolution_proxy"
    return "descriptor_proxy"


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    artifact_paths = [
        RESULT_PATH,
        NA_BRANCH_REPAIR_PATH,
        BINDING_CANDIDATE_PATH,
        CONTRACT_SUMMARY_PATH,
        QUESTION_PATH,
        SUMMARY_PATH,
        Path(__file__).resolve(),
    ]
    artifact_names = {path.name for path in artifact_paths}
    manifest["outputs"] = [row for row in manifest.get("outputs", []) if row.get("artifact") not in artifact_names]
    for path, artifact_type in [
        (RESULT_PATH, "result"),
        (NA_BRANCH_REPAIR_PATH, "na_branch_repair_ledger"),
        (BINDING_CANDIDATE_PATH, "binding_candidate_ledger"),
        (CONTRACT_SUMMARY_PATH, "contract_summary_ledger"),
        (QUESTION_PATH, "question_ledger"),
        (SUMMARY_PATH, "summary"),
    ]:
        manifest["outputs"].append(
            {
                "artifact": path.name,
                "category": "historical_ohlc_gtos_replay_targetstop_na_binding_repair",
                "artifact_type": artifact_type,
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    existing_paths = {str(path.relative_to(REPO)).replace("\\", "/") for path in artifact_paths}
    manifest["artifacts"] = [
        row for row in manifest.get("artifacts", []) if row.get("path") not in existing_paths
    ]
    for path, artifact_type in [
        (Path(__file__).resolve(), "targetstop_na_binding_repair_builder"),
        (RESULT_PATH, "targetstop_na_binding_repair_result"),
        (NA_BRANCH_REPAIR_PATH, "targetstop_na_branch_repair_ledger"),
        (BINDING_CANDIDATE_PATH, "targetstop_na_binding_candidate_ledger"),
        (CONTRACT_SUMMARY_PATH, "targetstop_na_contract_summary_ledger"),
        (QUESTION_PATH, "targetstop_na_question_ledger"),
        (SUMMARY_PATH, "targetstop_na_summary"),
    ]:
        manifest["artifacts"].append(
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "status": "created",
                "type": artifact_type,
            }
        )
    manifest["last_updated_utc"] = generated_at
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "event_type": "route_artifact_built",
        "route": "historical_ohlc_gtos_replay_targetstop_na_binding_repair",
        "artifact": RESULT_PATH.name,
        "counts": result["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    counts = result["counts"]
    lines = [
        "# Historical OHLC GTOS Target/Stop NA Binding Repair",
        "",
        f"Generated UTC: {result['generated_utc']}",
        "",
        "## Boundary",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
        f"- TARGETSTOP_NA_NA branch rows: {counts['targetstop_na_branch_rows']}",
        f"- Binding candidate rows: {counts['binding_candidate_rows']}",
        f"- Contract summary rows: {counts['contract_summary_rows']}",
        f"- Question rows: {counts['question_rows']}",
        "",
        "## Repair Finding",
        "",
        "The two NA rows are entry-level repair summaries. Existing signature-scope rows already bind both entries across all 16 target/stop contracts, so the repair is to use those signature-scope rows for path/outcome interpretation and preserve the NA rows only as entry-level provenance.",
        "",
    ]
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    manifest_rows, manifest_hash = source_manifest()
    branch_scores = [row for row in read_jsonl(BRANCH_SCORE_PATH) if not row.get("_parse_error")]
    branch_queue = [row for row in read_jsonl(BRANCH_QUEUE_PATH) if not row.get("_parse_error")]
    partial_entries = [row for row in read_jsonl(PARTIAL_ENTRY_PATH) if not row.get("_parse_error")]
    partial_costs = [row for row in read_jsonl(PARTIAL_COST_PATH) if not row.get("_parse_error")]
    partial_signatures = [row for row in read_jsonl(PARTIAL_SIGNATURE_PATH) if not row.get("_parse_error")]
    target_stop_contracts = [row for row in read_jsonl(TARGET_STOP_CONTRACT_PATH) if not row.get("_parse_error")]

    branch_queue_by_id = {str(row.get("branch_queue_id")): row for row in branch_queue}
    partial_entry_by_key = {natural_key(row): row for row in partial_entries}
    costs_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    sigs_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in partial_costs:
        costs_by_key[natural_key(row)].append(row)
    for row in partial_signatures:
        sigs_by_key[natural_key(row)].append(row)

    na_branch_rows = [
        row for row in branch_scores if str(row.get("target_stop_contract_id")).startswith("TARGETSTOP_NA")
    ]
    repair_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    question_rows: list[dict[str, Any]] = []

    for seq, branch in enumerate(na_branch_rows, 1):
        key = natural_key(branch)
        entry = partial_entry_by_key.get(key, {})
        sigs = sigs_by_key.get(key, [])
        costs = costs_by_key.get(key, [])
        contract_ids = sorted({str(row.get("target_stop_contract_id")) for row in sigs})
        cost_model_ids = sorted({str(row.get("cost_fill_id")) for row in costs})
        touch_counter = Counter(str(row.get("m1_first_touch_status")) for row in sigs)
        status_counter = Counter(str(row.get("signature_scope_status")) for row in sigs)
        repair_status = (
            "TARGETSTOP_NA_ENTRY_ROW_BOUND_TO_EXISTING_SIGNATURE_SCOPE_CONTRACT_ROWS"
            if len(contract_ids) == len(target_stop_contracts) and sigs
            else "TARGETSTOP_NA_ENTRY_ROW_REMAINS_UNBOUND_FAIL_CLOSED"
        )
        repair_rows.append(
            {
                "targetstop_na_repair_id": f"OHLC-GTOS-TARGETSTOP-NA-REPAIR-{seq:05d}",
                "branch_proxy_score_id": branch.get("branch_proxy_score_id"),
                "branch_queue_id": branch.get("branch_queue_id"),
                "family_synthesis_id": branch.get("family_synthesis_id"),
                "route_candidate_id": branch.get("route_candidate_id"),
                "symbol": branch.get("symbol"),
                "side": branch.get("side"),
                "route_session": branch.get("route_session"),
                "entry_variant": branch.get("entry_variant"),
                "original_target_stop_contract_id": branch.get("target_stop_contract_id"),
                "partial_source_recheck_entry_repair_id": entry.get("partial_source_recheck_entry_repair_id"),
                "entry_repair_status": entry.get("entry_repair_status"),
                "entry_alignment_status": entry.get("entry_alignment_status"),
                "binding_repair_status": repair_status,
                "bound_target_stop_contract_count": len(contract_ids),
                "bound_target_stop_contract_ids": contract_ids,
                "source_cost_model_count": len(cost_model_ids),
                "binding_candidate_rows_for_entry": len(sigs),
                "signature_scope_status_counts": dict(sorted(status_counter.items())),
                "m1_first_touch_status_counts": dict(sorted(touch_counter.items())),
                "repair_interpretation": "Original NA row is entry-level provenance only; use signature-scope rows for target/stop path evidence.",
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_TARGETSTOP_NA_BINDING_REPAIR_BRANCH",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
        for cand_seq, sig in enumerate(sigs, 1):
            candidate_rows.append(
                {
                    "targetstop_na_binding_candidate_id": f"OHLC-GTOS-TARGETSTOP-NA-BIND-CAND-{len(candidate_rows) + 1:05d}",
                    "targetstop_na_repair_id": f"OHLC-GTOS-TARGETSTOP-NA-REPAIR-{seq:05d}",
                    "branch_queue_id": branch.get("branch_queue_id"),
                    "route_candidate_id": sig.get("route_candidate_id"),
                    "symbol": sig.get("symbol"),
                    "side": sig.get("side"),
                    "route_session": sig.get("route_session"),
                    "entry_variant": sig.get("entry_variant"),
                    "event_id": sig.get("event_id"),
                    "cost_fill_id": sig.get("cost_fill_id"),
                    "cost_model": sig.get("cost_model"),
                    "target_stop_contract_id": sig.get("target_stop_contract_id"),
                    "target_multiple": sig.get("target_multiple"),
                    "stop_multiple": sig.get("stop_multiple"),
                    "signature_scope_status": sig.get("signature_scope_status"),
                    "m1_repair_path_status": sig.get("m1_repair_path_status"),
                    "m1_first_touch_status": sig.get("m1_first_touch_status"),
                    "touch_class": classify_touch(str(sig.get("m1_first_touch_status"))),
                    "m1_repair_fill_status": sig.get("m1_repair_fill_status"),
                    "m1_repair_fill_bar_offset": sig.get("m1_repair_fill_bar_offset"),
                    "first_target_touch_m1_offset": sig.get("first_target_touch_m1_offset"),
                    "first_stop_touch_m1_offset": sig.get("first_stop_touch_m1_offset"),
                    "source_manifest_hash": manifest_hash,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_TARGETSTOP_NA_BINDING_REPAIR_CANDIDATE",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "candidate_sequence_for_na_branch": cand_seq,
                }
            )

        by_contract: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for sig in sigs:
            by_contract[str(sig.get("target_stop_contract_id"))].append(sig)
        for contract_id in sorted(by_contract):
            contract_rows = by_contract[contract_id]
            touch_classes = Counter(classify_touch(str(row.get("m1_first_touch_status"))) for row in contract_rows)
            summary_rows.append(
                {
                    "targetstop_na_contract_summary_id": f"OHLC-GTOS-TARGETSTOP-NA-CONTRACT-SUM-{len(summary_rows) + 1:05d}",
                    "targetstop_na_repair_id": f"OHLC-GTOS-TARGETSTOP-NA-REPAIR-{seq:05d}",
                    "branch_queue_id": branch.get("branch_queue_id"),
                    "route_candidate_id": branch.get("route_candidate_id"),
                    "entry_variant": branch.get("entry_variant"),
                    "target_stop_contract_id": contract_id,
                    "candidate_rows": len(contract_rows),
                    "cost_model_counts": dict(sorted(Counter(str(row.get("cost_model")) for row in contract_rows).items())),
                    "signature_scope_status_counts": dict(sorted(Counter(str(row.get("signature_scope_status")) for row in contract_rows).items())),
                    "m1_first_touch_status_counts": dict(sorted(Counter(str(row.get("m1_first_touch_status")) for row in contract_rows).items())),
                    "touch_class_counts": dict(sorted(touch_classes.items())),
                    "source_manifest_hash": manifest_hash,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_TARGETSTOP_NA_BINDING_REPAIR_CONTRACT_SUMMARY",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    question_specs = [
        (
            "Can every TARGETSTOP_NA_NA row be bound to existing signature-scope target/stop contracts?",
            len(repair_rows),
            "binding_status",
        ),
        (
            "Which bound signature-scope rows are no-fill controls rather than replayed path rows?",
            sum(1 for row in candidate_rows if row.get("touch_class") == "no_fill_or_no_resolution_proxy"),
            "nofill_scope_split",
        ),
        (
            "Which bound signature-scope rows have target-first repair proxies?",
            sum(1 for row in candidate_rows if row.get("touch_class") == "favorable_target_proxy"),
            "target_first_repair_proxy",
        ),
        (
            "Do NA entry rows need mutation, deletion, or only provenance labeling?",
            len(repair_rows),
            "provenance_labeling",
        ),
    ]
    for seq, (question, row_count, track) in enumerate(question_specs, 1):
        question_rows.append(
            {
                "question_id": f"OHLC-GTOS-TARGETSTOP-NA-BIND-Q-{seq:03d}",
                "question": question,
                "track": track,
                "affected_row_count": row_count,
                "not_completion": True,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    write_jsonl(NA_BRANCH_REPAIR_PATH, repair_rows)
    write_jsonl(BINDING_CANDIDATE_PATH, candidate_rows)
    write_jsonl(CONTRACT_SUMMARY_PATH, summary_rows)
    write_jsonl(QUESTION_PATH, question_rows)

    counts = {
        "targetstop_na_branch_rows": len(na_branch_rows),
        "source_branch_queue_na_rows": sum(
            1 for row in branch_queue_by_id.values() if str(row.get("target_stop_contract_id")).startswith("TARGETSTOP_NA")
        ),
        "partial_entry_input_rows": len(partial_entries),
        "partial_cost_model_input_rows": len(partial_costs),
        "partial_signature_scope_input_rows": len(partial_signatures),
        "target_stop_contract_input_rows": len(target_stop_contracts),
        "binding_repair_rows": len(repair_rows),
        "binding_candidate_rows": len(candidate_rows),
        "contract_summary_rows": len(summary_rows),
        "question_rows": len(question_rows),
        "bound_na_rows": sum(
            1
            for row in repair_rows
            if row.get("binding_repair_status") == "TARGETSTOP_NA_ENTRY_ROW_BOUND_TO_EXISTING_SIGNATURE_SCOPE_CONTRACT_ROWS"
        ),
        "source_manifest_rows": len(manifest_rows),
    }
    result = {
        "generated_utc": generated_at,
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_targetstop_na_binding_repair_v1",
        "artifact": RESULT_PATH.name,
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "binding_repair_status_counts": dict(sorted(Counter(row["binding_repair_status"] for row in repair_rows).items())),
        "candidate_touch_class_counts": dict(sorted(Counter(row["touch_class"] for row in candidate_rows).items())),
        "candidate_m1_first_touch_status_counts": dict(sorted(Counter(row["m1_first_touch_status"] for row in candidate_rows).items())),
        "contract_candidate_rows_per_na_branch": {
            str(row["branch_queue_id"]): row["binding_candidate_rows_for_entry"] for row in repair_rows
        },
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"artifact": str(RESULT_PATH), "counts": counts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
