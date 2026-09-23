"""Build vNext READY8 failure-context adjustment rules.

This converts READY8 adversarial-control, underpower, and concentration rows
into compact runtime adjustment rules for contextual side-risk sizing. The
rules do not reopen the old research order; they collapse the row-bearing
READY8 family by the runtime match surface that side_aware_sizing already
consumes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder"
RULES_PATH = OUT_DIR / "GTOS_VNEXT_READY8_FAILURE_CONTEXT_ADJUSTMENT_RULES_2026-05-18.json"
SUMMARY_PATH = OUT_DIR / "GTOS_VNEXT_READY8_FAILURE_CONTEXT_ADJUSTMENT_SUMMARY_2026-05-18.json"
MASTER_LEDGER_PATH = OUT_DIR / "GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_LEDGER_2026-05-18.jsonl"

READY8_ADV_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit"
HAZ001_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/haz001_density_waiting_time_concentration_expansion_and_sealed_retest"
READY8_DECISION_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/decide_ready8_scid_and_related_geometry_research_direction"

CONTROL_LEDGER = READY8_ADV_DIR / "READY8_CONTROLS_FULLY_EXPLAIN_OR_WEAKEN_FINDINGS_LEDGER_2026-05-15.jsonl"
UNDERPOWER_LEDGER = READY8_ADV_DIR / "READY8_BRANCH_UNDERPOWER_EFFECTIVE_N_LEDGER_2026-05-15.jsonl"
CONCENTRATION_LEDGER = READY8_ADV_DIR / "READY8_CONCENTRATION_ADJUSTED_INTERPRETATION_LEDGER_2026-05-15.jsonl"
DOWNSTREAM_RULES = READY8_ADV_DIR / "READY8_DOWNSTREAM_ADJUSTMENT_RULES_2026-05-15.json"
GENERATED_AT_UTC = "2026-05-18T00:00:00Z"

MATCH_FIELDS = (
    "card_id",
    "horizon_m15_bars",
    "target_family_id",
    "partition_assignment",
    "descriptor_name",
    "descriptor_value",
    "wait_gap_bucket",
    "prior_24h_count_bucket",
    "source_window",
    "source_segment_sha256",
    "canonical_economic_group",
    "symbol",
    "symbol_family",
    "side",
    "session",
    "framework",
    "route_family",
)


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
    return rows


def nonempty_line_count(path: Path) -> int:
    if path.suffix.lower() == ".json":
        return 1 if path.stat().st_size else 0
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        return sum(1 for line in handle if line.strip())


def source_artifact_stats(paths: list[Path]) -> list[dict[str, Any]]:
    stats = []
    for path in sorted({p for p in paths if p.exists()}, key=lambda item: rel(item)):
        stats.append(
            {
                "path": rel(path),
                "sha256": sha256_path(path),
                "row_count": nonempty_line_count(path),
                "suffix": path.suffix.lower(),
            }
        )
    return stats


def selected_open_ready8_units() -> dict[str, Any]:
    def empty_selection() -> dict[str, Any]:
        return {
            "selected_unit_count": 0,
            "selected_row_bearing_or_structured_units": 0,
            "selected_support_or_wrapper_units": 0,
            "selected_counted_rows_or_lines": 0,
        }

    def summarize_selected(selected: list[dict[str, Any]]) -> dict[str, Any]:
        rowish_suffixes = {".jsonl", ".json", ".csv", ".tsv", ".ndjson"}
        counted = 0
        rowish = 0
        for row in selected:
            source_path = ROOT / str(row.get("source_artifact_path") or "")
            if source_path.suffix.lower() in rowish_suffixes:
                rowish += 1
            if (
                source_path.exists()
                and source_path.is_file()
                and source_path.suffix.lower()
                in {".jsonl", ".json", ".csv", ".txt", ".md", ".py"}
            ):
                counted += nonempty_line_count(source_path)

        return {
            "selected_unit_count": len(selected),
            "selected_row_bearing_or_structured_units": rowish,
            "selected_support_or_wrapper_units": len(selected) - rowish,
            "selected_counted_rows_or_lines": counted,
        }

    if not MASTER_LEDGER_PATH.exists():
        return empty_selection()

    selected = []
    closed_runtime_selection: dict[str, Any] | None = None
    for line in MASTER_LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if (
            row.get("batch_wave_id") == "WAVE_READY8_FAILURE_CONTEXT_ADJUSTMENT_RULES"
            and row.get("runtime_selected_open_unit_count")
        ):
            closed_runtime_selection = {
                "selected_unit_count": row.get("runtime_selected_open_unit_count", 0),
                "selected_row_bearing_or_structured_units": row.get(
                    "runtime_selected_row_bearing_or_structured_units", 0
                ),
                "selected_support_or_wrapper_units": row.get(
                    "runtime_selected_support_or_wrapper_units", 0
                ),
                "selected_counted_rows_or_lines": row.get(
                    "runtime_selected_counted_rows_or_lines", 0
                ),
            }
        if row.get("conversion_state") != "NOT_STARTED":
            continue
        if row.get("evidence_family") != "ready8_tags_failure_intelligence":
            continue
        path = str(row.get("source_artifact_path") or "")
        lower = path.casefold().replace("\\", "/")
        if not (
            "2026-05-15" in lower
            or "2026_05_15" in lower
            or "2026-05-16" in lower
            or "2026_05_16" in lower
            or "weekend" in lower
            or "moonshot" in lower
        ):
            continue
        selected.append(row)

    if selected:
        return summarize_selected(selected)
    if closed_runtime_selection:
        return closed_runtime_selection
    return empty_selection()


def scoped_key(row: dict[str, Any]) -> dict[str, str]:
    branch_key = row.get("branch_key") if isinstance(row.get("branch_key"), dict) else {}
    result: dict[str, str] = {}
    for field in MATCH_FIELDS:
        value = row.get(field)
        if value in (None, ""):
            value = branch_key.get(field)
        if value in (None, ""):
            continue
        result[field] = str(value)
    return result


def add_aggregate(
    aggregates: dict[tuple[tuple[str, str], ...], dict[str, Any]],
    *,
    scope: dict[str, str],
    source_path: Path,
    source_row_index: int,
    action: str,
    score_multiplier: float,
    reason: str,
    evidence_class: str,
    extra: dict[str, Any] | None = None,
) -> None:
    if not scope.get("card_id"):
        return
    key = tuple(sorted(scope.items()))
    item = aggregates.setdefault(
        key,
        {
            **scope,
            "ready8_adjustment_rule_id": hashlib.sha1(json.dumps(scope, sort_keys=True).encode()).hexdigest()[:16],
            "score_multiplier": 1.0,
            "positive_score_multiplier": 1.0,
            "negative_score_multiplier": 1.0,
            "adjustment_action_counts": Counter(),
            "source_row_count": 0,
            "source_paths": set(),
            "source_examples": [],
            "reasons": Counter(),
            "evidence_classes": Counter(),
            "min_unique_duplicate_denominator_count": None,
            "max_control_envelope_abs": None,
        },
    )
    item["score_multiplier"] = min(float(item["score_multiplier"]), score_multiplier)
    item["positive_score_multiplier"] = min(float(item["positive_score_multiplier"]), score_multiplier)
    item["negative_score_multiplier"] = min(float(item["negative_score_multiplier"]), score_multiplier)
    item["adjustment_action_counts"][action] += 1
    item["source_row_count"] += 1
    item["source_paths"].add(rel(source_path))
    item["reasons"][reason] += 1
    item["evidence_classes"][evidence_class] += 1
    if len(item["source_examples"]) < 5:
        item["source_examples"].append(
            {
                "path": rel(source_path),
                "line_index": source_row_index,
                "action": action,
                "reason": reason,
            }
        )
    extra = extra or {}
    unique_count = extra.get("unique_duplicate_denominator_count")
    if isinstance(unique_count, (int, float)):
        current = item["min_unique_duplicate_denominator_count"]
        item["min_unique_duplicate_denominator_count"] = (
            unique_count if current is None else min(current, unique_count)
        )
    envelope = extra.get("matched_control_envelope_abs")
    if isinstance(envelope, (int, float)):
        current = item["max_control_envelope_abs"]
        item["max_control_envelope_abs"] = envelope if current is None else max(current, envelope)


def build_rules() -> tuple[dict[str, Any], dict[str, Any]]:
    aggregates: dict[tuple[tuple[str, str], ...], dict[str, Any]] = {}
    source_paths = [
        CONTROL_LEDGER,
        UNDERPOWER_LEDGER,
        CONCENTRATION_LEDGER,
        DOWNSTREAM_RULES,
    ]
    source_paths.extend(path for path in READY8_ADV_DIR.iterdir() if path.suffix.lower() in {".json", ".jsonl", ".md", ".py", ".txt"})
    source_paths.extend(path for path in HAZ001_DIR.iterdir() if path.suffix.lower() in {".json", ".jsonl", ".md", ".py", ".txt"})
    source_paths.extend(path for path in READY8_DECISION_DIR.iterdir() if path.suffix.lower() in {".json", ".jsonl", ".md", ".py", ".txt"})

    for index, row in enumerate(read_jsonl(CONTROL_LEDGER), start=1):
        classification = str(row.get("adjustment_classification") or "")
        if classification == "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT":
            multiplier = 0.0
            action = "zero_ready8_context_score_control_explained"
        elif classification == "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT":
            multiplier = 0.5
            action = "halve_ready8_context_score_control_weakened"
        else:
            continue
        add_aggregate(
            aggregates,
            scope=scoped_key(row),
            source_path=CONTROL_LEDGER,
            source_row_index=index,
            action=action,
            score_multiplier=multiplier,
            reason=classification,
            evidence_class=str(row.get("evidence_class") or ""),
            extra=row,
        )

    for index, row in enumerate(read_jsonl(UNDERPOWER_LEDGER), start=1):
        if row.get("underpowered_unique_duplicate_floor_lt_30") is not True:
            continue
        add_aggregate(
            aggregates,
            scope=scoped_key(row),
            source_path=UNDERPOWER_LEDGER,
            source_row_index=index,
            action="zero_ready8_context_score_underpowered",
            score_multiplier=0.0,
            reason="underpowered_unique_duplicate_floor_lt_30",
            evidence_class=str(row.get("evidence_class") or ""),
            extra=row,
        )

    for index, row in enumerate(read_jsonl(CONCENTRATION_LEDGER), start=1):
        adjusted = str(row.get("adjusted_interpretation") or "")
        if adjusted not in {
            "CONCENTRATION_ADJUSTMENT_REQUIRED_BEFORE_INTERPRETATION",
            "UNDERPOWERED_RETAINED_NOT_KILL_OR_PROMOTE",
        }:
            continue
        add_aggregate(
            aggregates,
            scope=scoped_key(row),
            source_path=CONCENTRATION_LEDGER,
            source_row_index=index,
            action="zero_ready8_context_score_concentrated_or_underpowered",
            score_multiplier=0.0,
            reason=adjusted,
            evidence_class=str(row.get("evidence_class") or ""),
            extra=row,
        )

    rules = []
    for item in sorted(aggregates.values(), key=lambda row: (row.get("card_id", ""), row.get("target_family_id", ""), row.get("horizon_m15_bars", ""), row.get("partition_assignment", ""), row.get("ready8_adjustment_rule_id", ""))):
        source_paths_sorted = sorted(item.pop("source_paths"))
        actions = dict(sorted(item.pop("adjustment_action_counts").items()))
        reasons = dict(sorted(item.pop("reasons").items()))
        evidence_classes = dict(sorted(item.pop("evidence_classes").items()))
        rule = {
            **item,
            "row_type": "gtos_vnext_ready8_failure_context_adjustment_rule",
            "source_component": "ready8_failure_context_adjustment",
            "evidence_family": "ready8_tags_failure_intelligence",
            "reason": "ready8_failure_context_adjustment",
            "adjustment_action_counts": actions,
            "reason_counts": reasons,
            "evidence_class_counts": evidence_classes,
            "source_paths": source_paths_sorted,
        }
        rules.append({key: value for key, value in rule.items() if value not in (None, {}, [], "")})

    downstream = read_json(DOWNSTREAM_RULES)
    source_stats = source_artifact_stats(source_paths)
    selected = selected_open_ready8_units()
    card_counts = Counter(rule.get("card_id") for rule in rules if rule.get("card_id"))
    horizon_counts = Counter(rule.get("horizon_m15_bars") for rule in rules if rule.get("horizon_m15_bars"))
    target_counts = Counter(rule.get("target_family_id") for rule in rules if rule.get("target_family_id"))
    partition_counts = Counter(rule.get("partition_assignment") for rule in rules if rule.get("partition_assignment"))
    multiplier_counts = Counter(str(rule.get("score_multiplier")) for rule in rules)
    blank_anchor_counts = Counter(
        field
        for rule in rules
        for field in ("horizon_m15_bars", "target_family_id", "partition_assignment")
        if not rule.get(field)
    )

    payload = {
        "schema_version": "gtos_vnext_ready8_failure_context_adjustment_rules_v1",
        "generated_at_utc": GENERATED_AT_UTC,
        "source_evidence_class": downstream.get("evidence_class"),
        "runtime_adjustment_rule_count": len(rules),
        "rules": rules,
    }
    summary = {
        "schema_version": "gtos_vnext_ready8_failure_context_adjustment_summary_v1",
        "generated_at_utc": payload["generated_at_utc"],
        "rules_path": rel(RULES_PATH),
        "summary_path": rel(SUMMARY_PATH),
        "runtime_adjustment_rule_count": len(rules),
        "source_artifact_count": len(source_stats),
        "source_rows_counted": sum(int(item.get("row_count") or 0) for item in source_stats),
        "source_artifacts": source_stats,
        "selected_open_ready8_family": selected,
        "card_counts": dict(sorted(card_counts.items())),
        "horizon_counts": dict(sorted(horizon_counts.items(), key=lambda item: str(item[0]))),
        "target_family_counts": dict(sorted(target_counts.items())),
        "partition_counts": dict(sorted(partition_counts.items())),
        "score_multiplier_counts": dict(sorted(multiplier_counts.items())),
        "blank_anchor_counts": dict(sorted(blank_anchor_counts.items())),
        "downstream_comparison_summary_counts": downstream.get("comparison_summary_counts", {}),
        "downstream_branch_summary_counts": downstream.get("branch_summary_counts", {}),
        "adjustment_action_counts": dict(
            sorted(
                Counter(
                    action
                    for rule in rules
                    for action, count in rule.get("adjustment_action_counts", {}).items()
                    for _ in range(int(count))
                ).items()
            )
        ),
        "expected_runtime_effect": (
            "READY8 tag-derived context support is adjusted before side-risk "
            "scoring: control-explained, underpowered, and concentration-blocked "
            "card/horizon/target/partition scopes zero matching READY8 context "
            "score, while materially weakened scopes halve it."
        ),
    }
    return payload, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload, summary = build_rules()
    if args.check:
        expected_rules = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
        if RULES_PATH.exists() and RULES_PATH.read_text(encoding="utf-8") != expected_rules:
            raise SystemExit(f"{RULES_PATH} is stale")
        if SUMMARY_PATH.exists() and SUMMARY_PATH.read_text(encoding="utf-8") != expected_summary:
            raise SystemExit(f"{SUMMARY_PATH} is stale")
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        RULES_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "rules_path": rel(RULES_PATH),
                "summary_path": rel(SUMMARY_PATH),
                "runtime_adjustment_rule_count": summary["runtime_adjustment_rule_count"],
                "source_rows_counted": summary["source_rows_counted"],
                "selected_unit_count": summary["selected_open_ready8_family"]["selected_unit_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
