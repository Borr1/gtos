"""Summarize live shadow candidates at opportunity level.

Raw shadow logs keep every candidate/path/mechanical row. This read-only
summary collapses consecutive duplicate active setups and active same-symbol
overlaps using ``live_candidate_opportunity_clusters.jsonl`` so monitoring
does not over-count repeated detections as separate winning trades.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.evidence_selection import (
    evidence_selection_key,
    latest_by_candidate as latest_evidence_by_candidate,
)


DEFAULT_ROOT = Path(".")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LIVE_SHADOW_OPPORTUNITY_SUMMARY_2026-05-04.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LIVE_SHADOW_OPPORTUNITY_SUMMARY_2026-05-04.md")


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
    return rows


def latest_by_candidate_asof(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for line_no, row in enumerate(rows, start=1):
        cid = str(row.get("candidate_id") or "")
        asof = str(row.get("asof_latest_candle_utc") or "")
        if not cid or not asof:
            continue
        key = (cid, asof)
        current = evidence_selection_key(row, line_no)
        previous = evidence_selection_key(latest.get(key) or {}, int((latest.get(key) or {}).get("_line_no") or 0))
        if current >= previous:
            latest[key] = {**row, "_line_no": line_no}
    return latest


def latest_mechanical_by_candidate_strategy_asof(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    latest: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        strategy = str(row.get("strategy_id") or "")
        asof = str(row.get("asof_latest_candle_utc") or "")
        if not cid or not strategy or not asof:
            continue
        key = (cid, strategy, asof)
        current = parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        previous = parse_utc((latest.get(key) or {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        if current >= previous:
            latest[key] = row
    return latest


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return latest_evidence_by_candidate(rows)


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _strategy_r(row: dict[str, Any]) -> float | None:
    explicit = _safe_float(row.get("strategy_proxy_r"))
    if explicit is not None:
        return explicit
    outcome_status = str(row.get("outcome_status") or "")
    if outcome_status == "ENTRY_TOUCHED_THEN_TP1":
        return 1.5
    if outcome_status == "ENTRY_TOUCHED_THEN_SL":
        return -1.0
    if outcome_status.startswith("NO_FILL_"):
        return 0.0
    if outcome_status == "NO_ENTRY_TOUCH_BY_ASOF":
        return 0.0
    return None


def _counts_for_proxy_r(row: dict[str, Any]) -> bool:
    return row.get("score_status") in {
        "COMPUTED_FROM_CANDIDATE_PATH",
        "COMPUTED_FROM_PENDING_LIFECYCLE",
        "COMPUTED_FROM_LTF_PATH_ORDER",
    }


def build_summary(root: Path) -> dict[str, Any]:
    shadow = root / "shadow_logs"
    cluster_rows = read_jsonl(shadow / "live_candidate_opportunity_clusters.jsonl")
    path_rows = read_jsonl(shadow / "candidate_path_follow.jsonl")
    mechanical_rows = read_jsonl(shadow / "live_mechanical_strategy_shadow_outcomes.jsonl")
    latest_clusters = latest_by_candidate(cluster_rows)
    latest_paths = latest_by_candidate(path_rows)
    latest_mech_by_key = latest_mechanical_by_candidate_strategy_asof(mechanical_rows)

    candidates = sorted(latest_clusters)
    opportunity_ids = {row.get("opportunity_id") for row in latest_clusters.values() if row.get("opportunity_id")}
    countable_candidates = [
        cid
        for cid, row in latest_clusters.items()
        if row.get("opportunity_counting_status") == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
    ]
    not_countable = Counter(
        str(row.get("opportunity_counting_status") or "UNKNOWN") for row in latest_clusters.values()
        if row.get("opportunity_counting_status") != "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
    )
    algorithm_versions = Counter(
        str(row.get("opportunity_assignment_algorithm_version") or "UNVERSIONED")
        for row in latest_clusters.values()
    )
    path_statuses = Counter(str((latest_paths.get(cid) or {}).get("path_label") or "MISSING_PATH") for cid in candidates)
    countable_path_statuses = Counter(
        str((latest_paths.get(cid) or {}).get("path_label") or "MISSING_PATH") for cid in countable_candidates
    )

    by_strategy: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "countable_rows": 0,
            "r_counted_rows": 0,
            "proxy_r": 0.0,
            "outcomes": Counter(),
            "r_counting_statuses": Counter(),
        }
    )
    for cid in countable_candidates:
        path = latest_paths.get(cid) or {}
        asof = str(path.get("asof_latest_candle_utc") or "")
        if not asof:
            continue
        for (candidate_id, strategy_id, row_asof), row in latest_mech_by_key.items():
            if candidate_id != cid or row_asof != asof:
                continue
            outcome = str(row.get("outcome_status") or "UNKNOWN")
            by_strategy[str(strategy_id)]["countable_rows"] += 1
            by_strategy[str(strategy_id)]["outcomes"][outcome] += 1
            if _counts_for_proxy_r(row):
                r_value = _strategy_r(row)
                if r_value is None:
                    by_strategy[str(strategy_id)]["r_counting_statuses"]["R_WAITING_FOR_EXIT_OR_RETRY"] += 1
                    continue
                by_strategy[str(strategy_id)]["r_counted_rows"] += 1
                by_strategy[str(strategy_id)]["proxy_r"] += r_value
                by_strategy[str(strategy_id)]["r_counting_statuses"][str(row.get("score_status"))] += 1
            else:
                by_strategy[str(strategy_id)]["r_counting_statuses"]["NOT_ENTRY_MODEL_R"] += 1

    strategy_summary = {
        strategy: {
            "countable_rows": values["countable_rows"],
            "r_counted_rows": values["r_counted_rows"],
            "proxy_r": round(values["proxy_r"], 4),
            "outcomes": dict(values["outcomes"]),
            "r_counting_statuses": dict(values["r_counting_statuses"]),
        }
        for strategy, values in sorted(by_strategy.items())
    }

    return {
        "schema_version": "live_shadow_opportunity_summary_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "raw_candidate_count_with_latest_cluster": len(candidates),
        "unique_opportunity_ids_latest": len(opportunity_ids),
        "countable_primary_opportunities": len(countable_candidates),
        "not_countable_by_reason": dict(not_countable),
        "opportunity_assignment_algorithm_versions": dict(algorithm_versions),
        "latest_path_labels_raw_candidates": dict(path_statuses),
        "latest_path_labels_countable_opportunities": dict(countable_path_statuses),
        "strategy_summary_countable_only": strategy_summary,
        "counting_rule": (
            "Count only rows whose latest opportunity_counting_status is "
            "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY. Consecutive duplicate active setups and "
            "active same-symbol overlaps are retained as raw evidence but not counted as "
            "separate trades."
        ),
        "r_counting_rule": (
            "Proxy R is computed only for mechanical rows with score_status="
            "COMPUTED_FROM_CANDIDATE_PATH, COMPUTED_FROM_LTF_PATH_ORDER, "
            "or COMPUTED_FROM_PENDING_LIFECYCLE. "
            "Pending lifecycle rows use internal fill/no-fill telemetry when a real limit "
            "intent existed; no-fill lifecycle outcomes contribute 0R. Same-M1 TP/SL "
            "ambiguity is retained as evidence but does not contribute R without tick-order "
            "proof. Context-only, diagnostic, not-applicable, waiting, and not-scored rows "
            "retain outcome labels but do not contribute R."
        ),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }


def write_markdown(summary: dict[str, Any], output: Path) -> None:
    lines = [
        "# Live Shadow Opportunity Summary - 2026-05-04",
        "",
        f"**Schema:** `{summary['schema_version']}`",
        f"**Generated:** `{summary['generated_at_utc']}`",
        f"**Promotion verdict:** `{summary['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- Raw candidates with latest cluster rows: `{summary['raw_candidate_count_with_latest_cluster']}`",
        f"- Unique opportunity IDs: `{summary['unique_opportunity_ids_latest']}`",
        f"- Countable primary opportunities: `{summary['countable_primary_opportunities']}`",
        f"- Not countable by reason: `{summary['not_countable_by_reason']}`",
        f"- Opportunity assignment algorithm versions: `{summary['opportunity_assignment_algorithm_versions']}`",
        "",
        "## Path Labels",
        "",
        f"- Raw candidates: `{summary['latest_path_labels_raw_candidates']}`",
        f"- Countable opportunities: `{summary['latest_path_labels_countable_opportunities']}`",
        "",
        "## Strategy Summary",
        "",
        "| Strategy | Countable rows | R-counted rows | Proxy R | Outcomes | R status |",
        "|---|---:|---:|---:|---|---|",
    ]
    for strategy, row in summary["strategy_summary_countable_only"].items():
        lines.append(
            f"| `{strategy}` | {row['countable_rows']} | {row['r_counted_rows']} | "
            f"{row['proxy_r']} | `{row['outcomes']}` | `{row['r_counting_statuses']}` |"
        )
    lines.extend(
        [
            "",
            "## Counting Rule",
            "",
            summary["counting_rule"],
            "",
            "## R Counting Rule",
            "",
            summary["r_counting_rule"],
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()

    summary = build_summary(args.root)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(summary, args.output_md)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
