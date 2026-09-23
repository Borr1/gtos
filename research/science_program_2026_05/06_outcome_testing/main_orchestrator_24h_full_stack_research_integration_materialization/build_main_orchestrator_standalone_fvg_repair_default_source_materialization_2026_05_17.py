from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_ACTION_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_2026-05-17.jsonl"
)
OUTPUT_SOURCE_LOG = Path("shadow_logs/standalone_fvg_poi_current_claim_repair_decisions.jsonl")
OUTPUT_SUMMARY = (
    ROUTE_DIR / "MAIN_ORCH24_STANDALONE_FVG_REPAIR_DEFAULT_SOURCE_MATERIALIZATION_SUMMARY_2026-05-17.json"
)
OUTPUT_MANIFEST = (
    ROUTE_DIR
    / "MAIN_ORCH24_STANDALONE_FVG_REPAIR_DEFAULT_SOURCE_MATERIALIZATION_OUTPUT_MANIFEST_2026-05-17.json"
)
TARGET_BRANCH = "REDESIGN_STANDALONE_FVG_POI_SCORER_CURRENT_PROXY_NEGATIVE_SMALL_N"
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_no"] = line_no
                rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def source_row(row: dict[str, Any], *, generated: str, ledger_sha: str | None) -> dict[str, Any]:
    proxy_ref = safe_float(row.get("after_proxy_r"))
    if proxy_ref is None:
        proxy_ref = safe_float(row.get("opportunity_proxy_r_reference"))
    audit = row.get("missed_opportunity_audit")
    return {
        "schema_version": "standalone_fvg_poi_current_claim_repair_decision_v1",
        "created_at_utc": generated,
        "generated_utc": generated,
        "source_decision_status": "ACTION_LEDGER_REPAIRED_CURRENT_CLAIM_DECISION",
        "candidate_id": row.get("candidate_id"),
        "strategy_id": row.get("strategy_id"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "decision_time_utc": row.get("decision_time_utc"),
        "action_class": row.get("action_class"),
        "branch_decision": row.get("branch_decision"),
        "implementation_decision": row.get("implementation_decision"),
        "current_action": row.get("current_action"),
        "next_action": row.get("next_action"),
        "decision_evidence": row.get("decision_evidence"),
        "scoring_boundary": row.get("scoring_boundary"),
        "implementation_candidate": row.get("implementation_candidate"),
        "coverage_status": row.get("coverage_status"),
        "data_requirement_state": row.get("data_requirement_state"),
        "source_capture_surface": row.get("source_capture_surface"),
        "row_id": row.get("row_id"),
        "source_row_id": row.get("row_id"),
        "source_line_no": row.get("_source_line_no"),
        "source_ledger": str(INPUT_ACTION_LEDGER),
        "source_ledger_sha256": ledger_sha,
        "source_artifact": row.get("source_artifact") or str(INPUT_ACTION_LEDGER),
        "standalone_fvg_poi_type": row.get("standalone_fvg_poi_type"),
        "standalone_fvg_poi_type_repair_status": row.get("standalone_fvg_poi_type_repair_status"),
        "standalone_fvg_poi_type_repair_source": row.get("standalone_fvg_poi_type_repair_source"),
        "standalone_fvg_trade_record_bounds_repair_status": row.get(
            "standalone_fvg_trade_record_bounds_repair_status"
        ),
        "fvg_exact_bounds": row.get("fvg_exact_bounds"),
        "after_proxy_r": proxy_ref,
        "opportunity_proxy_r_reference": proxy_ref,
        "opportunity_proxy_reference_status": "REFERENCE_ONLY_CURRENT_STANDALONE_FVG_CLAIM_NOT_COUNTED",
        "opportunity_not_independently_countable_reason": row.get(
            "opportunity_not_independently_countable_reason"
        ),
        "opportunity_useful_mechanism": row.get("opportunity_useful_mechanism"),
        "opportunity_downstream_paths": row.get("opportunity_downstream_paths"),
        "opportunity_preservation_status": row.get("opportunity_preservation_status"),
        "underlying_intelligence_preserved": row.get("underlying_intelligence_preserved"),
        "missed_opportunity_audit": audit if isinstance(audit, dict) else None,
        "safe_flags": SAFE_FLAGS,
        "no_live_behavior": True,
        "no_shadow_log_append": True,
        "no_ai_calls": True,
        "claim_boundary": (
            "Reference-only current-claim repair consumed by research shadow scorer; no trade logic, "
            "prompt, risk, selector, broker operation, exact-R, or validation claim is opened."
        ),
    }


def main() -> None:
    generated = utc_now()
    ledger_sha = sha256_file(INPUT_ACTION_LEDGER)
    action_rows = read_jsonl(INPUT_ACTION_LEDGER)
    target_rows = [row for row in action_rows if row.get("branch_decision") == TARGET_BRANCH]
    source_rows = [source_row(row, generated=generated, ledger_sha=ledger_sha) for row in target_rows]
    proxy_refs = [
        value
        for row in source_rows
        if (value := safe_float(row.get("opportunity_proxy_r_reference"))) is not None
    ]
    write_jsonl(OUTPUT_SOURCE_LOG, source_rows)
    status_counts = Counter(str(row.get("source_decision_status") or "") for row in source_rows)
    strategy_counts = Counter(str(row.get("strategy_id") or "") for row in source_rows)
    summary = {
        "route_id": "MAIN_ORCH24_STANDALONE_FVG_REPAIR_DEFAULT_SOURCE_MATERIALIZATION",
        "date": DATE,
        "generated_utc": generated,
        "input_action_ledger": str(INPUT_ACTION_LEDGER),
        "input_action_ledger_sha256": ledger_sha,
        "output_source_log": str(OUTPUT_SOURCE_LOG),
        "rows": len(source_rows),
        "unique_candidate_strategy_keys": len(
            {(row.get("candidate_id"), row.get("strategy_id")) for row in source_rows}
        ),
        "unique_candidates": len({str(row.get("candidate_id") or "") for row in source_rows}),
        "source_decision_status_counts": dict(sorted(status_counts.items())),
        "strategy_id_counts": dict(sorted(strategy_counts.items())),
        "proxy_r_rows_referenced_not_counted": len(proxy_refs),
        "proxy_r_sum_referenced_not_counted": round(sum(proxy_refs), 8),
        "missed_opportunity_audit_rows": sum(
            1 for row in source_rows if isinstance(row.get("missed_opportunity_audit"), dict)
        ),
        "underlying_intelligence_preserved_rows": sum(
            1 for row in source_rows if row.get("underlying_intelligence_preserved") is True
        ),
        "materialization_decision": (
            "INSTALL_REPAIRED_STANDALONE_FVG_CURRENT_CLAIM_DECISIONS_AS_DEFAULT_SCORER_SOURCE_INPUT"
        ),
        "claim_boundary": (
            "This writes a research shadow source input consumed by live_mechanical_shadow dry-run/backfill. "
            "It does not append strategy outcomes, alter live trading, duplicate proxy R, or promote the claim."
        ),
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    manifest = {
        "generated_utc": generated,
        "inputs": {
            "action_ledger": {
                "path": str(INPUT_ACTION_LEDGER),
                "exists": INPUT_ACTION_LEDGER.exists(),
                "size_bytes": INPUT_ACTION_LEDGER.stat().st_size if INPUT_ACTION_LEDGER.exists() else 0,
                "sha256": ledger_sha,
            }
        },
        "outputs": {
            "default_source_log": {
                "path": str(OUTPUT_SOURCE_LOG),
                "exists": OUTPUT_SOURCE_LOG.exists(),
                "rows": len(source_rows),
                "size_bytes": OUTPUT_SOURCE_LOG.stat().st_size,
                "sha256": sha256_file(OUTPUT_SOURCE_LOG),
            },
            "summary": {
                "path": str(OUTPUT_SUMMARY),
                "sha256": sha256_file(OUTPUT_SUMMARY),
            },
        },
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_MANIFEST, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
