from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_SOURCE_LEDGER = ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_SOURCE_LEDGER_2026-05-17.jsonl"
OUTPUT_SOURCE_LOG = Path("shadow_logs/pending_lifecycle_tick_spread_reconstruction.jsonl")
OUTPUT_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_PENDING_TICK_SPREAD_DEFAULT_SOURCE_MATERIALIZATION_SUMMARY_2026-05-17.json"
OUTPUT_MANIFEST = ROUTE_DIR / "MAIN_ORCH24_PENDING_TICK_SPREAD_DEFAULT_SOURCE_MATERIALIZATION_OUTPUT_MANIFEST_2026-05-17.json"
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
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    generated = utc_now()
    rows = read_jsonl(INPUT_SOURCE_LEDGER)
    status_counts = Counter(str(row.get("decision_spread_status") or "") for row in rows)
    safe_rows = [
        row
        for row in rows
        if row.get("decision_spread_status") == "TICK_PARQUET_AT_OR_BEFORE_DECISION_WITHIN_2S_SOURCE_SAFE"
    ]
    unsafe_rows = [
        row
        for row in rows
        if row.get("decision_spread_status") == "TICK_PARQUET_NO_PRIOR_TICK_WITHIN_2S_SOURCE_UNSAFE"
    ]
    write_jsonl(OUTPUT_SOURCE_LOG, rows)
    summary = {
        "route_id": "MAIN_ORCH24_PENDING_TICK_SPREAD_DEFAULT_SOURCE_MATERIALIZATION",
        "date": DATE,
        "generated_utc": generated,
        "input_source_ledger": str(INPUT_SOURCE_LEDGER),
        "input_source_ledger_sha256": sha256_file(INPUT_SOURCE_LEDGER),
        "output_source_log": str(OUTPUT_SOURCE_LOG),
        "rows": len(rows),
        "unique_candidates": len({str(row.get("candidate_id") or "") for row in rows}),
        "decision_spread_status_counts": dict(sorted(status_counts.items())),
        "tick_reconstruction_success_rows": len(safe_rows),
        "tick_reconstruction_unsafe_rows": len(unsafe_rows),
        "remaining_source_requirement_rows": len(unsafe_rows),
        "remaining_source_requirements": [
            {
                "candidate_id": row.get("candidate_id"),
                "decision_spread_status": row.get("decision_spread_status"),
                "source_requirement": row.get("source_requirement"),
                "tick_source_path": row.get("tick_source_path"),
            }
            for row in unsafe_rows
        ],
        "materialization_decision": (
            "INSTALL_VERIFIED_ROUTE_LOCAL_TICK_SPREAD_RECONSTRUCTION_AS_DEFAULT_SCORER_SOURCE_INPUT"
        ),
        "claim_boundary": (
            "This writes a source-capture shadow input consumed by live_mechanical_shadow dry-run/backfill. "
            "It does not append strategy outcomes, change trade logic, open exact R, or make a validation claim."
        ),
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    manifest = {
        "generated_utc": generated,
        "inputs": {
            "route_local_source_ledger": {
                "path": str(INPUT_SOURCE_LEDGER),
                "exists": INPUT_SOURCE_LEDGER.exists(),
                "size_bytes": INPUT_SOURCE_LEDGER.stat().st_size if INPUT_SOURCE_LEDGER.exists() else 0,
                "sha256": sha256_file(INPUT_SOURCE_LEDGER),
            }
        },
        "outputs": {
            "default_source_log": {
                "path": str(OUTPUT_SOURCE_LOG),
                "exists": OUTPUT_SOURCE_LOG.exists(),
                "rows": len(rows),
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
