"""Materialize FVG/structural forward-registry alignment decisions.

The current scorer can now make row-level default-off/kill/source-repair
decisions for standalone FVG, swing-protected stop, and structural metadata
surfaces. This plate ties the static forward-capture strategy registry to that
implemented scorer output so future candidate rows do not keep stale global
"source blocked" labels where row-level gates exist.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.forward_capture import FOLLOW_STRATEGY_REGISTRY  # noqa: E402


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

SOURCE_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_SCORER_CANDIDATE_RECOMPUTE_LEDGER_{DATE}.jsonl"
SOURCE_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_SCORER_CANDIDATE_RECOMPUTE_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_FORWARD_REGISTRY_ALIGNMENT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_FORWARD_REGISTRY_ALIGNMENT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_FORWARD_REGISTRY_ALIGNMENT_OUTPUT_MANIFEST_{DATE}.json"

ALIGNMENT_STRATEGIES = {
    "V2_STRUCT_FVG_MID_EDGE": "SOURCE_CAPTURE_REQUIRED_SCORER_BLOCKED",
    "V3_FVG_ONLY_RESCUE_RISK_BANK": "SOURCE_CAPTURE_REQUIRED_SCORER_BLOCKED",
    "V2_STRUCT_SWING_PROTECTED": "SOURCE_CAPTURE_REQUIRED_SCORER_BLOCKED",
    "V2_STRUCT_COMPOSITE_ANY": "SOURCE_CAPTURE_REQUIRED_SCORER_BLOCKED",
    "V3_FVG_THEN_OB_TAIL_RISK_BANK": "SOURCE_CAPTURE_REQUIRED_SCORER_BLOCKED",
    "V3_OB_LOCK_PULLBACK_RISK_BANK": "SOURCE_CAPTURE_REQUIRED_SCORER_BLOCKED",
    "V3_OB_LOCK_COST_AWARE_MIN_R": "SOURCE_CAPTURE_REQUIRED_SCORER_BLOCKED",
    "FVG_OB_CONFLUENCE_OB_AFTER_FVG": "IMPLEMENT_SHADOW_SCORER_CAPTURED_METADATA_DEFAULT_OFF",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def registry_by_id() -> dict[str, dict[str, Any]]:
    return {item["strategy_id"]: dict(item) for item in FOLLOW_STRATEGY_REGISTRY}


def strategy_rows(rows: list[dict[str, Any]], strategy_id: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("strategy_id") == strategy_id]


def proxy_sum(rows: list[dict[str, Any]], field: str) -> float:
    return sum(value for row in rows if (value := safe_float(row.get(field))) is not None)


def numeric_count(rows: list[dict[str, Any]], field: str) -> int:
    return sum(1 for row in rows if safe_float(row.get(field)) is not None)


def decision_for_registry(
    strategy_id: str,
    registry_item: dict[str, Any],
    source_rows: list[dict[str, Any]],
) -> str:
    previous_branch = ALIGNMENT_STRATEGIES[strategy_id]
    branch = registry_item.get("branch_decision")
    if branch == previous_branch:
        return "REGISTRY_ALREADY_ALIGNED_OR_PRESERVED"
    if any(row.get("after_proxy_r") is not None for row in source_rows):
        return "ALIGN_REGISTRY_TO_ROW_LEVEL_DEFAULT_OFF_SCORER"
    return "ALIGN_REGISTRY_TO_ROW_LEVEL_SOURCE_REPAIR_GATED_SCORER"


def build_rows() -> list[dict[str, Any]]:
    registry = registry_by_id()
    source_rows = read_jsonl(SOURCE_LEDGER)
    generated = utc_now()
    out: list[dict[str, Any]] = []
    for strategy_id in sorted(ALIGNMENT_STRATEGIES):
        rows = strategy_rows(source_rows, strategy_id)
        registry_item = registry[strategy_id]
        before_values = [value for row in rows if (value := safe_float(row.get("before_proxy_r"))) is not None]
        after_values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
        out.append(
            {
                "row_id": f"MAIN-ORCH24-FVG-STRUCT-REGISTRY-ALIGN-{len(out) + 1:05d}",
                "route_id": ROUTE_ID,
                "generated_utc": generated,
                "strategy_id": strategy_id,
                "family": registry_item.get("family"),
                "previous_registry_branch_decision": ALIGNMENT_STRATEGIES[strategy_id],
                "current_registry_branch_decision": registry_item.get("branch_decision"),
                "current_registry_decision_evidence": registry_item.get("decision_evidence"),
                "implementation_candidate": registry_item.get("implementation_candidate"),
                "source_rows": len(rows),
                "candidate_rows": len({row.get("candidate_id") for row in rows}),
                "exact_r_rows": 0,
                "before_numeric_proxy_rows": len(before_values),
                "after_numeric_proxy_rows": len(after_values),
                "numeric_proxy_row_delta": len(after_values) - len(before_values),
                "before_proxy_r_sum": sum(before_values),
                "after_proxy_r_sum": sum(after_values),
                "proxy_r_sum_delta": sum(after_values) - sum(before_values),
                "after_branch_decision_counts": dict(
                    Counter(str(row.get("after_branch_decision")) for row in rows)
                ),
                "implementation_decision_counts": dict(
                    Counter(str(row.get("implementation_decision")) for row in rows)
                ),
                "proxy_delta_class_counts": dict(
                    Counter(str(row.get("proxy_r_delta_class")) for row in rows)
                ),
                "alignment_decision": decision_for_registry(strategy_id, registry_item, rows),
                "safe_flags": SAFE_FLAGS,
                "no_live_behavior": True,
                "no_shadow_log_append": True,
            }
        )
    return out


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_summary = read_json(SOURCE_SUMMARY)
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_FVG_STRUCTURAL_FORWARD_REGISTRY_ALIGNMENT",
        "claim_boundary": (
            "Forward-capture registry metadata alignment with already-materialized row-level "
            "FVG/structural scorer decisions. No shadow append, live behavior, exact broker R, "
            "or promotion claim is opened."
        ),
        "registry_rows": len(rows),
        "source_rows": sum(row["source_rows"] for row in rows),
        "aligned_strategy_after_numeric_proxy_rows": sum(
            row["after_numeric_proxy_rows"] for row in rows
        ),
        "aligned_strategy_after_proxy_r_sum": sum(row["after_proxy_r_sum"] for row in rows),
        "aligned_strategy_proxy_r_sum_delta": sum(row["proxy_r_sum_delta"] for row in rows),
        "candidate_rows": source_summary.get("candidate_rows"),
        "exact_r_rows": 0,
        "source_summary_rows": source_summary.get("rows"),
        "source_summary_after_numeric_proxy_rows": source_summary.get("after_numeric_proxy_rows"),
        "source_summary_after_proxy_r_sum": source_summary.get("after_proxy_r_sum"),
        "source_summary_numeric_proxy_row_delta": source_summary.get("numeric_proxy_row_delta"),
        "source_summary_proxy_r_sum_delta": source_summary.get("proxy_r_sum_delta"),
        "registry_alignment_decision_counts": dict(
            Counter(row.get("alignment_decision") for row in rows)
        ),
        "current_registry_branch_decision_counts": dict(
            Counter(row.get("current_registry_branch_decision") for row in rows)
        ),
        "per_strategy_proxy_delta": {
            row["strategy_id"]: {
                "source_rows": row["source_rows"],
                "after_numeric_proxy_rows": row["after_numeric_proxy_rows"],
                "after_proxy_r_sum": row["after_proxy_r_sum"],
                "proxy_r_sum_delta": row["proxy_r_sum_delta"],
            }
            for row in rows
        },
        "surface_summary": source_summary.get("surface_summary"),
        "plate_decision": "FVG_STRUCTURAL_FORWARD_REGISTRY_ALIGNED_TO_ROW_LEVEL_SCORER_DECISIONS",
        "safe_flags": SAFE_FLAGS,
    }


def build_manifest() -> dict[str, Any]:
    inputs = {
        "source_ledger": SOURCE_LEDGER,
        "source_summary": SOURCE_SUMMARY,
        "forward_capture_source": Path("src/research_infra/forward_capture.py"),
        "forward_capture_tests": Path("tests/test_forward_capture_shadow_loggers.py"),
    }
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            str(path): {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in inputs.values()
        },
        "output_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in [OUTPUT_LEDGER, OUTPUT_SUMMARY]
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    rows = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summarize(rows))
    write_json(OUTPUT_MANIFEST, build_manifest())
    print(json.dumps({"rows": len(rows), "summary": str(OUTPUT_SUMMARY)}, sort_keys=True))


if __name__ == "__main__":
    main()
