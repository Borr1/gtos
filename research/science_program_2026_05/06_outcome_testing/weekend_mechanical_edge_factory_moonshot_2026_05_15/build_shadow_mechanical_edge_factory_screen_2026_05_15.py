#!/usr/bin/env python3
"""Build the first parent-side no-API shadow mechanical edge factory screen.

Evidence class:
    Forward shadow/path-follow research only. This script summarizes existing
    no-API logs and emits descriptor/hypothesis/control artifacts. It does not
    call AI, MT5, broker, paid data, or vendor APIs, and it does not make
    validation, R/PnL, win-rate, expectancy, live-readiness, or promotion claims.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SHADOW_DIR = REPO / "shadow_logs"
UTC_NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

SOURCE_FILES = {
    "strategy_outcomes": SHADOW_DIR / "live_mechanical_strategy_shadow_outcomes.jsonl",
    "candidate_path_follow": SHADOW_DIR / "candidate_path_follow.jsonl",
    "candidate_rollups": SHADOW_DIR / "live_candidate_strategy_rollups.jsonl",
    "candidate_ltf_path_order": SHADOW_DIR / "candidate_ltf_path_order.jsonl",
    "strategy_follow_evaluations": SHADOW_DIR / "strategy_follow_evaluations.jsonl",
}

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no, "_raw": line[:500]}
                continue
            yield obj


def sort_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("asof_latest_candle_utc") or ""),
        str(row.get("created_at_utc") or row.get("backfilled_at_utc") or row.get("timestamp_utc") or ""),
        str(row.get("row_key") or ""),
    )


def latest_by(rows: Iterable[dict[str, Any]], key_fields: tuple[str, ...]) -> dict[tuple[Any, ...], dict[str, Any]]:
    latest: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        if row.get("_parse_error"):
            continue
        key = tuple(row.get(field) for field in key_fields)
        if any(value is None for value in key):
            continue
        current = latest.get(key)
        if current is None or sort_key(row) >= sort_key(current):
            latest[key] = row
    return latest


def pct(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def mean(values: list[float]) -> float | None:
    values = [value for value in values if value is not None and math.isfinite(value)]
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def get_nested(row: dict[str, Any], path: list[str], default: Any = None) -> Any:
    cur: Any = row
    for part in path:
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def classify_terminal(row: dict[str, Any]) -> str:
    outcome_status = str(row.get("outcome_status") or "")
    path_label = str(row.get("path_label") or "")
    status_text = " ".join(
        str(row.get(field) or "")
        for field in ("strategy_status", "score_status", "outcome_status")
    ).upper()
    if (
        "NOT_COMPUTABLE" in status_text
        or "NOT_SCORED" in status_text
        or "MISSING_REQUIRED_LIVE_METADATA" in status_text
        or "SCORER_NOT_IMPLEMENTED" in status_text
    ):
        return "not_computable_or_not_scored"
    if row.get("hit_tp1") is True and row.get("hit_sl") is True:
        return "ambiguous_tp1_and_sl"
    if row.get("hit_tp1") is True:
        return "terminal_tp1"
    if row.get("hit_sl") is True:
        return "terminal_sl"
    if "NO_FILL_PRICE_REACHED_TP" in outcome_status or "continued_without_entry_touch_to_tp_area" in path_label:
        return "no_fill_reached_tp_area"
    if row.get("touched_entry") is True:
        return "entry_touched_unresolved_or_partial"
    if "NOT_SCORED" in outcome_status:
        return "not_scored"
    if "NOT_APPLICABLE" in outcome_status:
        return "not_applicable"
    if "UNRESOLVED" in outcome_status:
        return "unresolved"
    return "other"


def is_entry_strategy(row: dict[str, Any]) -> bool:
    if row.get("strategy_applicability") != "candidate_relevant":
        return False
    status_text = " ".join(
        str(row.get(field) or "")
        for field in ("strategy_status", "score_status", "outcome_status")
    ).upper()
    if "NOT_AN_ENTRY_STRATEGY" in status_text or "CONTEXT_ONLY" in status_text:
        return False
    if "NOT_COMPUTABLE" in status_text or "NOT_SCORED" in status_text:
        return False
    if "MISSING_REQUIRED_LIVE_METADATA" in status_text or "SCORER_NOT_IMPLEMENTED" in status_text:
        return False
    return True


def summarize_strategy_outcomes(latest_outcomes: dict[tuple[Any, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in latest_outcomes.values():
        key = (
            str(row.get("strategy_id") or "<missing>"),
            str(row.get("strategy_family") or "<missing>"),
            str(row.get("symbol") or "<missing>"),
            str(row.get("side") or "<missing>"),
        )
        groups[key].append(row)

    output: list[dict[str, Any]] = []
    for (strategy_id, family, symbol, side), rows in sorted(groups.items()):
        terminal_counts = Counter(classify_terminal(row) for row in rows)
        score_counts = Counter(str(row.get("score_status") or "<missing>") for row in rows)
        status_counts = Counter(str(row.get("strategy_status") or "<missing>") for row in rows)
        outcome_counts = Counter(str(row.get("outcome_status") or "<missing>") for row in rows)
        entry_rows = [row for row in rows if is_entry_strategy(row)]
        terminal_event_count = terminal_counts["terminal_tp1"] + terminal_counts["terminal_sl"]
        output.append(
            {
                "strategy_id": strategy_id,
                "strategy_family": family,
                "symbol": symbol,
                "side": side,
                "latest_rows": len(rows),
                "unique_candidates": len({row.get("candidate_id") for row in rows}),
                "entry_strategy_rows": len(entry_rows),
                "terminal_event_count": terminal_event_count,
                "terminal_tp1_count": terminal_counts["terminal_tp1"],
                "terminal_sl_count": terminal_counts["terminal_sl"],
                "observed_terminal_tp1_share_research_only": pct(
                    terminal_counts["terminal_tp1"], terminal_event_count
                ),
                "no_fill_reached_tp_area_count": terminal_counts["no_fill_reached_tp_area"],
                "entry_touched_unresolved_or_partial_count": terminal_counts[
                    "entry_touched_unresolved_or_partial"
                ],
                "unresolved_count": terminal_counts["unresolved"],
                "not_scored_count": terminal_counts["not_scored"],
                "not_computable_or_not_scored_count": terminal_counts[
                    "not_computable_or_not_scored"
                ],
                "ambiguous_tp1_and_sl_count": terminal_counts["ambiguous_tp1_and_sl"],
                "not_applicable_count": terminal_counts["not_applicable"],
                "other_count": terminal_counts["other"],
                "score_status_counts": dict(sorted(score_counts.items())),
                "strategy_status_counts": dict(sorted(status_counts.items())),
                "outcome_status_counts": dict(sorted(outcome_counts.items())),
                "evidence_class": "FORWARD_SHADOW_PATH_FOLLOW_RESEARCH_ONLY",
                "claim_boundary": "Counts are duplicate-collapsed latest forward shadow path observations, not validation or realized performance.",
            }
        )
    return output


def summarize_candidate_paths(latest_paths: dict[tuple[Any, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in latest_paths.values():
        key = (
            str(row.get("symbol") or "<missing>"),
            str(row.get("side") or "<missing>"),
            str(row.get("framework") or "<missing>"),
            str(row.get("path_label") or "<missing>"),
        )
        groups[key].append(row)

    output: list[dict[str, Any]] = []
    for (symbol, side, framework, path_label), rows in sorted(groups.items()):
        depth_thin = [
            get_nested(row, ["external_confluence", "sierra", "features", "event15_thin_depth10_rate"])
            for row in rows
        ]
        total_depth = [
            get_nested(row, ["external_confluence", "sierra", "features", "event15_median_total_depth10"])
            for row in rows
        ]
        mid_change = [
            get_nested(row, ["external_confluence", "sierra", "features", "event15_mid_change_ticks"])
            for row in rows
        ]
        nearest = [row.get("nearest_distance_to_entry") for row in rows]
        output.append(
            {
                "symbol": symbol,
                "side": side,
                "framework": framework,
                "path_label": path_label,
                "candidate_count": len(rows),
                "touched_entry_count": sum(1 for row in rows if row.get("touched_entry") is True),
                "hit_tp1_count": sum(1 for row in rows if row.get("hit_tp1") is True),
                "hit_sl_count": sum(1 for row in rows if row.get("hit_sl") is True),
                "sierra_feature_rows": sum(
                    1
                    for row in rows
                    if get_nested(row, ["external_confluence", "sierra", "status"]) == "FEATURES_EXTRACTED"
                ),
                "avg_event15_thin_depth10_rate": mean(depth_thin),
                "avg_event15_total_depth10": mean(total_depth),
                "avg_event15_mid_change_ticks": mean(mid_change),
                "avg_nearest_distance_to_entry": mean(nearest),
                "evidence_class": "FORWARD_SHADOW_PATH_FOLLOW_RESEARCH_ONLY",
            }
        )
    return output


def summarize_rollup_blockers(latest_rollups: dict[tuple[Any, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    blockers: Counter[tuple[str, str, str]] = Counter()
    examples: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in latest_rollups.values():
        unresolved = row.get("unresolved_strategies") or {}
        if not isinstance(unresolved, dict):
            continue
        for strategy_id, data in unresolved.items():
            if not isinstance(data, dict):
                continue
            key = (
                str(strategy_id),
                str(data.get("strategy_status") or "<missing>"),
                str(data.get("score_status") or "<missing>"),
            )
            blockers[key] += 1
            examples.setdefault(
                key,
                {
                    "candidate_id": row.get("candidate_id"),
                    "symbol": row.get("symbol"),
                    "reason": data.get("reason"),
                },
            )

    output = []
    for (strategy_id, strategy_status, score_status), count in sorted(
        blockers.items(), key=lambda item: (-item[1], item[0])
    ):
        output.append(
            {
                "strategy_id": strategy_id,
                "strategy_status": strategy_status,
                "score_status": score_status,
                "candidate_count": count,
                "example": examples[(strategy_id, strategy_status, score_status)],
                "failure_family": "data/source/capture gap",
                "next_useful_action": "Add or repair forward capture for the missing lock/entry metadata, then rerun the scorer; do not synthesize historical lock truth from price alone.",
            }
        )
    return output


def build_hypotheses(
    strategy_rollups: list[dict[str, Any]],
    path_rollups: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    hypotheses: list[dict[str, Any]] = []

    no_fill_tp = [row for row in path_rollups if row["path_label"] == "continued_without_entry_touch_to_tp_area"]
    if no_fill_tp:
        hypotheses.append(
            {
                "hypothesis_id": "PARENT-SHADOW-HYP-001",
                "family": "execution_fillability_and_entry_geometry",
                "mechanical_translation": "For candidate contexts where price travels to TP area before touching the limit entry, test an as-of market/shallower-limit/entry-offset challenger and a no-fill avoid/route-to-different-entry rule.",
                "source_evidence": "candidate_path_follow latest duplicate-collapsed rows with path_label=continued_without_entry_touch_to_tp_area",
                "supporting_row_groups": no_fill_tp,
                "required_controls": [
                    "same candidate denominator",
                    "entry-touch order disambiguation",
                    "spread/slippage/fillability stress",
                    "neighbor-window continuation control",
                    "no broker-realized performance claim",
                ],
                "claim_boundary": "Hypothesis only; current evidence is forward shadow path behavior, not validated expectancy.",
            }
        )

    depth_rows = [
        row
        for row in path_rollups
        if row.get("sierra_feature_rows", 0) > 0 and row.get("avg_event15_thin_depth10_rate") is not None
    ]
    if depth_rows:
        hypotheses.append(
            {
                "hypothesis_id": "PARENT-SHADOW-HYP-002",
                "family": "orderflow_depth_proxy_context",
                "mechanical_translation": "Use Sierra event15 depth-thinness, total depth, and mid-change descriptors as context features for path-label routing, especially no-fill continuation and adverse-touch categories.",
                "source_evidence": "candidate_path_follow external_confluence.sierra.features",
                "supporting_row_groups": depth_rows,
                "required_controls": [
                    "symbol-specific futures-to-CFD proxy validity",
                    "source-file byte-range/hash contracts",
                    "pre/post decision timing separation",
                    "leave-symbol/session out",
                    "control for generic volatility expansion",
                ],
                "claim_boundary": "Descriptor candidate only; no depth feature is promoted as an edge.",
            }
        )

    computable_strategies = [
        row
        for row in strategy_rollups
        if row["entry_strategy_rows"] > 0
        and (row["terminal_event_count"] > 0 or row["no_fill_reached_tp_area_count"] > 0)
    ]
    if computable_strategies:
        hypotheses.append(
            {
                "hypothesis_id": "PARENT-SHADOW-HYP-003",
                "family": "strategy_challenger_comparison",
                "mechanical_translation": "Build same-denominator challenger comparison for strategies already scored from shared candidate paths, separating terminal TP/SL events from no-fill/entry-touch unresolved states.",
                "source_evidence": "live_mechanical_strategy_shadow_outcomes latest candidate-strategy rows",
                "supporting_row_groups": computable_strategies,
                "required_controls": [
                    "duplicate candidate collapse",
                    "terminal-only vs unresolved separated",
                    "strategy applicability filter",
                    "candidate final outcome stratification",
                    "do not call neutral/path outcomes realized R",
                ],
                "claim_boundary": "Comparison design candidate, not a performance claim.",
            }
        )

    if blockers:
        hypotheses.append(
            {
                "hypothesis_id": "PARENT-SHADOW-HYP-004",
                "family": "forward_capture_repair",
                "mechanical_translation": "Prioritize structural-lock and FVG-lock metadata capture because many V2/V3/FVG challenger rows are not computable in live forward logs.",
                "source_evidence": "live_candidate_strategy_rollups unresolved_strategies",
                "supporting_row_groups": blockers,
                "required_controls": [
                    "capture as-of at decision time",
                    "no retroactive synthesis from later price",
                    "schema/test/verifier before scorer consumption",
                ],
                "claim_boundary": "Infrastructure implication, not edge evidence.",
            }
        )

    return hypotheses


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = sorted({key for row in rows for key in row.keys() if not isinstance(row.get(key), (dict, list))})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in columns})


def main() -> int:
    source_manifest = {
        name: {
            "path": str(path),
            "exists": path.exists(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size if path.exists() else None,
        }
        for name, path in SOURCE_FILES.items()
    }

    latest_outcomes = latest_by(
        read_jsonl(SOURCE_FILES["strategy_outcomes"]), ("candidate_id", "strategy_id")
    )
    latest_paths = latest_by(read_jsonl(SOURCE_FILES["candidate_path_follow"]), ("candidate_id",))
    latest_rollups = latest_by(read_jsonl(SOURCE_FILES["candidate_rollups"]), ("candidate_id",))

    strategy_rollups = summarize_strategy_outcomes(latest_outcomes)
    path_rollups = summarize_candidate_paths(latest_paths)
    blockers = summarize_rollup_blockers(latest_rollups)
    hypotheses = build_hypotheses(strategy_rollups, path_rollups, blockers)

    summary = {
        "schema": "weekend_mechanical_edge_factory_shadow_screen_v1",
        "generated_utc": UTC_NOW,
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "FORWARD_SHADOW_PATH_FOLLOW_RESEARCH_ONLY",
        "claim_boundary": "This screen is descriptor, source, and challenger-design intelligence only. It is not validation, promotion, R/PnL, win-rate, expectancy, live-readiness, or live behavior.",
        "source_manifest": source_manifest,
        "duplicate_policy": {
            "strategy_outcomes": "latest row per candidate_id + strategy_id by asof_latest_candle_utc/created_at_utc/row_key",
            "candidate_path_follow": "latest row per candidate_id by asof_latest_candle_utc/created_at_utc/row_key",
            "candidate_rollups": "latest row per candidate_id by asof_latest_candle_utc/created_at_utc/row_key",
        },
        "counts": {
            "latest_strategy_candidate_rows": len(latest_outcomes),
            "latest_candidate_path_rows": len(latest_paths),
            "latest_candidate_rollup_rows": len(latest_rollups),
            "strategy_rollup_rows": len(strategy_rollups),
            "path_descriptor_rows": len(path_rollups),
            "failure_intelligence_rows": len(blockers),
            "hypothesis_rows": len(hypotheses),
        },
        "top_path_labels_by_count": dict(
            Counter(row["path_label"] for row in path_rollups for _ in range(int(row["candidate_count"]))).most_common()
        ),
        "immediate_implications": [
            "No-fill-to-TP-area path labels are first-class execution/entry-geometry intelligence, not merely failed fills.",
            "Sierra depth descriptors are already present in candidate_path_follow for selected symbols and should be routed into descriptor controls before any edge claim.",
            "Many V2/V3/FVG challenger scorers remain blocked by missing live structural/FVG lock metadata; this is a forward-capture repair route.",
            "Strategy outcome rows need duplicate-collapsed, terminal/unresolved-separated comparison before old-vs-new claims.",
        ],
    }

    write_json(ROUTE_DIR / "PARENT_SHADOW_MECHANICAL_EDGE_FACTORY_RESULT_2026-05-15.json", summary)
    write_jsonl(
        ROUTE_DIR / "PARENT_SHADOW_MECHANICAL_STRATEGY_ROLLUP_2026-05-15.jsonl",
        strategy_rollups,
    )
    write_csv(
        ROUTE_DIR / "PARENT_SHADOW_MECHANICAL_STRATEGY_ROLLUP_2026-05-15.csv",
        strategy_rollups,
    )
    write_jsonl(
        ROUTE_DIR / "PARENT_MARKET_BEHAVIOR_DESCRIPTOR_LEDGER_2026-05-15.jsonl",
        path_rollups,
    )
    write_jsonl(
        ROUTE_DIR / "PARENT_FAILURE_INTELLIGENCE_LEDGER_2026-05-15.jsonl",
        blockers,
    )
    write_jsonl(
        ROUTE_DIR / "PARENT_CHALLENGER_HYPOTHESIS_LEDGER_2026-05-15.jsonl",
        hypotheses,
    )

    md_lines = [
        "# Parent Shadow Mechanical Edge Factory Screen",
        "",
        f"Generated UTC: `{UTC_NOW}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: `FORWARD_SHADOW_PATH_FOLLOW_RESEARCH_ONLY`",
        "",
        "This is descriptor and challenger-design intelligence only. It is not validation, promotion, R/PnL, win-rate, expectancy, live-readiness, or live behavior.",
        "",
        "## Counts",
        "",
    ]
    for key, value in summary["counts"].items():
        md_lines.append(f"- `{key}`: `{value}`")
    md_lines.extend(["", "## Immediate Implications", ""])
    for item in summary["immediate_implications"]:
        md_lines.append(f"- {item}")
    md_lines.extend(["", "## Output Files", ""])
    for filename in [
        "PARENT_SHADOW_MECHANICAL_EDGE_FACTORY_RESULT_2026-05-15.json",
        "PARENT_SHADOW_MECHANICAL_STRATEGY_ROLLUP_2026-05-15.jsonl",
        "PARENT_SHADOW_MECHANICAL_STRATEGY_ROLLUP_2026-05-15.csv",
        "PARENT_MARKET_BEHAVIOR_DESCRIPTOR_LEDGER_2026-05-15.jsonl",
        "PARENT_FAILURE_INTELLIGENCE_LEDGER_2026-05-15.jsonl",
        "PARENT_CHALLENGER_HYPOTHESIS_LEDGER_2026-05-15.jsonl",
    ]:
        md_lines.append(f"- `{filename}`")
    (ROUTE_DIR / "PARENT_SHADOW_MECHANICAL_EDGE_FACTORY_SUMMARY_2026-05-15.md").write_text(
        "\n".join(md_lines) + "\n", encoding="utf-8"
    )

    print(json.dumps({"ok": True, "generated_utc": UTC_NOW, "counts": summary["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
