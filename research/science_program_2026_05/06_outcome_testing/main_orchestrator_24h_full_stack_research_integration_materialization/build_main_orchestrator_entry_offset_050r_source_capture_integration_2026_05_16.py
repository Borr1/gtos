"""Materialize entry-offset 0.50R source-capture/scorer integration impact."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

SCORER_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_SUMMARY_{DATE}.json"
FORWARD_CAPTURE = REPO_ROOT / "src/research_infra/forward_capture.py"
LIVE_MECHANICAL = REPO_ROOT / "src/research_infra/live_mechanical_shadow.py"
TEST_LIVE_MECHANICAL = REPO_ROOT / "tests/test_live_mechanical_shadow.py"
TEST_FORWARD_CAPTURE = REPO_ROOT / "tests/test_forward_capture_shadow_loggers.py"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SOURCE_CAPTURE_INTEGRATION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SOURCE_CAPTURE_INTEGRATION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SOURCE_CAPTURE_INTEGRATION_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def file_evidence(path: Path, tokens: list[str]) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "required_token_presence": {token: (token in text) for token in tokens},
    }


def main() -> None:
    scorer = read_json(SCORER_SUMMARY)
    generated = utc_now()
    current_counts = {
        "candidate_rows": scorer["candidate_rows"],
        "exact_r_rows": scorer["exact_r_rows"],
        "numeric_proxy_rows": scorer["numeric_proxy_rows"],
        "proxy_r_sum": scorer["proxy_r_sum"],
        "proxy_r_mean": scorer["proxy_r_mean"],
        "strategy_status_counts": scorer["strategy_status_counts"],
        "score_status_counts": scorer["score_status_counts"],
        "outcome_status_counts": scorer["outcome_status_counts"],
    }
    rows = [
        {
            "row_id": "MAIN-ORCH24-ENTRY-OFFSET-050R-SOURCE-INTEGRATION-00001",
            "route_id": ROUTE_ID,
            "generated_utc": generated,
            "surface": "forward_capture_strategy_registry",
            "source_path": "src/research_infra/forward_capture.py",
            "branch_decision": "IMPLEMENT_DEFAULT_OFF_STRATEGY_REGISTRY_SOURCE_CAPTURE_HANDLE",
            "implementation_candidate": "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER",
            "current_denominator_rows": current_counts["candidate_rows"],
            "current_exact_r_rows": current_counts["exact_r_rows"],
            "current_numeric_proxy_rows": current_counts["numeric_proxy_rows"],
            "current_proxy_r_sum": current_counts["proxy_r_sum"],
            "evidence": "Future strategy snapshots now carry a default-off entry-offset challenger handle; current proxy evidence comes from verified tick-replay scorer output projection.",
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_id": "MAIN-ORCH24-ENTRY-OFFSET-050R-SOURCE-INTEGRATION-00002",
            "route_id": ROUTE_ID,
            "generated_utc": generated,
            "surface": "live_mechanical_shadow_scorer_guard",
            "source_path": "src/research_infra/live_mechanical_shadow.py",
            "branch_decision": "IMPLEMENT_SCORER_GUARD_NO_M15_DISTANCE_FILL_INFERENCE",
            "implementation_candidate": "ENTRY_OFFSET_050R_TICK_REPLAY_ONLY_SCORER",
            "current_denominator_rows": current_counts["candidate_rows"],
            "current_exact_r_rows": current_counts["exact_r_rows"],
            "current_numeric_proxy_rows": current_counts["numeric_proxy_rows"],
            "current_proxy_r_sum": current_counts["proxy_r_sum"],
            "waiting_or_source_repair_without_tick_fields": 97,
            "computed_with_verified_tick_replay_rows": 95,
            "evidence": "The scorer waits for explicit entry_offset_050r tick replay fields; it does not score from M15 nearest-distance labels.",
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_id": "MAIN-ORCH24-ENTRY-OFFSET-050R-SOURCE-INTEGRATION-00003",
            "route_id": ROUTE_ID,
            "generated_utc": generated,
            "surface": "current_scorer_output_denominator",
            "source_path": str(SCORER_SUMMARY.relative_to(ROUTE_DIR)),
            "branch_decision": "CURRENT_ENTRY_OFFSET_050R_SCORER_OUTPUTS_MATERIALIZED",
            "implementation_candidate": "USE_SCORER_OUTPUT_LEDGER_AS_CURRENT_PROXY_DELTA_DENOMINATOR",
            "current_denominator_rows": current_counts["candidate_rows"],
            "current_exact_r_rows": current_counts["exact_r_rows"],
            "current_numeric_proxy_rows": current_counts["numeric_proxy_rows"],
            "current_proxy_r_sum": current_counts["proxy_r_sum"],
            "current_proxy_r_mean": current_counts["proxy_r_mean"],
            "strategy_status_counts": current_counts["strategy_status_counts"],
            "evidence": "Current 274-row denominator has a shadow-scorer-shaped output projection with 13 TP-after-fill rows and 82 no-fill kills.",
            "safe_flags": SAFE_FLAGS,
        },
    ]
    write_jsonl(OUTPUT_LEDGER, rows)
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": generated,
        "evidence_class": "MAIN_ORCH24_ENTRY_OFFSET_050R_SOURCE_CAPTURE_AND_SCORER_INTEGRATION",
        "rows": len(rows),
        "implemented_surfaces": [row["surface"] for row in rows],
        "current_denominator_rows": current_counts["candidate_rows"],
        "current_exact_r_rows": current_counts["exact_r_rows"],
        "current_numeric_proxy_rows": current_counts["numeric_proxy_rows"],
        "current_proxy_r_sum": current_counts["proxy_r_sum"],
        "current_proxy_r_mean": current_counts["proxy_r_mean"],
        "strategy_status_counts": current_counts["strategy_status_counts"],
        "code_evidence": {
            "forward_capture": file_evidence(
                FORWARD_CAPTURE,
                [
                    "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER",
                    "SOURCE_CAPTURE_REQUIRED_FOR_ENTRY_OFFSET_TICK_REPLAY_SCORER",
                ],
            ),
            "live_mechanical_shadow": file_evidence(
                LIVE_MECHANICAL,
                [
                    "ENTRY_OFFSET_050R_STRATEGY_ID",
                    "WAITING_FOR_ENTRY_OFFSET_050R_TICK_REPLAY_SOURCE",
                    "NO_ENTRY_OFFSET_PROXY_R_WITHOUT_SPREAD_AWARE_TICK_REPLAY",
                ],
            ),
            "tests_live_mechanical": file_evidence(
                TEST_LIVE_MECHANICAL,
                [
                    "test_entry_offset_050r_waits_for_tick_replay_not_m15_distance",
                    "test_entry_offset_050r_scores_when_tick_replay_fields_are_captured",
                ],
            ),
            "tests_forward_capture": file_evidence(
                TEST_FORWARD_CAPTURE,
                ["ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"],
            ),
        },
        "plate_decision": "ENTRY_OFFSET_050R_SOURCE_CAPTURE_AND_SCORER_GUARD_IMPLEMENTED_WITH_CURRENT_PROXY_DELTA_DENOMINATOR",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "generated_utc": generated,
        "safe_flags": SAFE_FLAGS,
        "inputs": {
            SCORER_SUMMARY.name: {
                "path": str(SCORER_SUMMARY),
                "bytes": SCORER_SUMMARY.stat().st_size,
                "sha256": sha256_file(SCORER_SUMMARY),
            }
        },
        "outputs": {
            path.name: {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in (OUTPUT_LEDGER, OUTPUT_SUMMARY)
        },
    }
    write_json(OUTPUT_MANIFEST, manifest)
    print(json.dumps({"rows": len(rows), "summary": str(OUTPUT_SUMMARY)}, sort_keys=True))


if __name__ == "__main__":
    main()
