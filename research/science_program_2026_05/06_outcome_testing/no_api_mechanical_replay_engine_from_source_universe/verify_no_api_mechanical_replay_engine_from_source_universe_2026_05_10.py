#!/usr/bin/env python3
"""Verify the no-API mechanical replay source-universe route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


ROUTE_ID = "NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE"
SCHEMA_VERSION = "no_api_mechanical_replay_engine_from_source_universe_v1"
DATE = "2026-05-10"
ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
OUTPUT_PREFIX = "NO_API_MECHANICAL_REPLAY"

REQUIRED_OPENED_FAMILIES = {
    "ob_retest",
    "fvg_fill",
    "breaker_re_entry",
    "opening_drive_no_fill_lifecycle",
    "session_kz_sweep",
    "liquidity_stop_run_context",
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
    "adjacent_range_compression_breakout",
}

FORBIDDEN_TRUE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_promotion",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_paid_api_or_databento_route",
    "opens_mt5_order_account_history_behavior",
    "opens_remote_push",
    "opens_registry_edit",
    "credentials_touched",
    "changes_live_trading_behavior",
]

FORBIDDEN_ROW_FIELDS = {
    "pnl",
    "broker_actual_r",
    "actual_r",
    "win_rate",
    "expectancy",
    "account_history",
    "deal",
    "position",
}

PLACEHOLDER_TERMS = ["TBD", "TODO", "unknown", "maybe", "later", "future work"]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_path(name: str) -> Path:
    return ROUTE_DIR / f"{OUTPUT_PREFIX}_{name}_{DATE}.json"


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if stripped:
                yield line_number, json.loads(stripped)


def artifact_path(value: Any) -> Path:
    path = Path(str(value))
    if path.is_absolute():
        return path
    return ROOT / path


def flag_failures(payload: Mapping[str, Any], label: str) -> list[str]:
    failures = []
    for flag in FORBIDDEN_TRUE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(f"{label}: {flag} is not false")
    if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        failures.append(f"{label}: promotion_verdict is not NO_PROMOTION_VERDICT")
    return failures


def verify(route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    global ROUTE_DIR
    ROUTE_DIR = route_dir
    failures: list[str] = []
    completion = read_json(json_path("COMPLETION_AUDIT"))
    manifest = read_json(json_path("OUTPUT_MANIFEST"))
    family = read_json(json_path("FAMILY_TERMINAL_STATUS_LEDGER"))
    registry = read_json(json_path("MECHANICAL_FAMILY_REGISTRY"))
    source_selection = read_json(json_path("SOURCE_SELECTION_AND_HASH_LEDGER"))
    candidates = read_json(json_path("CANDIDATE_INVENTORY"))
    path_labels = read_json(json_path("DISCOVERY_PATH_LABEL_INVENTORY"))
    noleak = read_json(json_path("NOLEAK_AUDIT"))
    saturation = read_json(json_path("SATURATION_SELF_REDTEAM_PASS"))
    excluded = read_json(json_path("EXCLUDED_SLICE_LEDGER"))
    continuation = read_json(json_path("SAME_EVIDENCE_CLASS_CONTINUATION_LEDGER"))
    next_prompt = read_json(json_path("NEXT_PROMPT_PACK"))

    for label, payload in [
        ("completion", completion),
        ("manifest", manifest),
        ("family", family),
        ("registry", registry),
        ("source_selection", source_selection),
        ("candidates", candidates),
        ("path_labels", path_labels),
        ("noleak", noleak),
        ("saturation", saturation),
        ("excluded", excluded),
        ("continuation", continuation),
        ("next_prompt", next_prompt),
    ]:
        failures.extend(flag_failures(payload, label))

    if completion.get("completion_standard_satisfied") is not True:
        failures.append("completion audit does not mark completion_standard_satisfied=true")
    if completion.get("can_mark_goal_complete") is not True:
        failures.append("completion audit does not mark can_mark_goal_complete=true")
    if completion.get("missing_incomplete_or_weak_requirements"):
        failures.append("completion audit has missing/incomplete/weak requirements")

    opened = {row.get("family_id") for row in family.get("opened_families") or []}
    missing_families = sorted(REQUIRED_OPENED_FAMILIES - opened)
    if missing_families:
        failures.append(f"missing required opened family ids: {missing_families}")
    for row in family.get("opened_families") or []:
        if row.get("prototype_only") is not False:
            failures.append(f"family {row.get('family_id')} is marked prototype-only")
        if row.get("opened_to_terminal_status") is not True:
            failures.append(f"family {row.get('family_id')} did not reach terminal status")

    if not source_selection.get("selected_source_count"):
        failures.append("no selected sources")
    if not candidates.get("candidate_row_count"):
        failures.append("no candidate inventory rows")
    if not path_labels.get("path_label_row_count"):
        failures.append("no path-label rows")
    if noleak.get("status") != "PASS":
        failures.append("noleak audit status is not PASS")
    if saturation.get("terminal_status") != "SATURATION_PASS_COMPLETE":
        failures.append("saturation terminal status is not complete")
    if not excluded.get("excluded_slice_count"):
        failures.append("excluded-slice ledger is empty; route likely did not audit skipped source slices")
    if not continuation.get("continuation_rows"):
        failures.append("same-evidence-class continuation ledger is empty")
    prompt_path_value = next_prompt.get("prompt_path") or next_prompt.get("prompt_path_to_create")
    if not prompt_path_value:
        failures.append("next prompt pack does not record a prompt path")
    else:
        prompt_path = artifact_path(prompt_path_value)
        if not prompt_path.exists():
            failures.append(f"next full prompt file missing: {prompt_path}")
    if not next_prompt.get("one_line_starter"):
        failures.append("next prompt pack is missing one_line_starter")

    candidate_rows_path = artifact_path(candidates.get("candidate_rows_path"))
    path_label_rows_path = artifact_path(path_labels.get("path_label_rows_path"))
    if not candidate_rows_path.exists():
        failures.append(f"candidate rows path missing: {candidate_rows_path}")
    if not path_label_rows_path.exists():
        failures.append(f"path-label rows path missing: {path_label_rows_path}")

    sample_candidate_count = 0
    if candidate_rows_path.exists():
        for line_number, row in iter_jsonl(candidate_rows_path):
            sample_candidate_count += 1
            failures.extend(flag_failures(row, f"candidate row {line_number}"))
            keys = {str(key).lower() for key in row.keys()}
            bad = sorted(keys & FORBIDDEN_ROW_FIELDS)
            if bad:
                failures.append(f"candidate row {line_number} contains forbidden fields {bad}")
            if row.get("projection_only") is not True:
                failures.append(f"candidate row {line_number} is not projection_only=true")
            if row.get("no_ai_calls") is not True or row.get("no_execution") is not True:
                failures.append(f"candidate row {line_number} violates no-AI/no-execution flags")
            if sample_candidate_count >= 500:
                break
    sample_path_count = 0
    if path_label_rows_path.exists():
        for line_number, row in iter_jsonl(path_label_rows_path):
            sample_path_count += 1
            failures.extend(flag_failures(row, f"path-label row {line_number}"))
            keys = {str(key).lower() for key in row.keys()}
            bad = sorted(keys & FORBIDDEN_ROW_FIELDS)
            if bad:
                failures.append(f"path-label row {line_number} contains forbidden fields {bad}")
            if row.get("label_family") != "DISCOVERY_PATH_LABEL_ONLY":
                failures.append(f"path-label row {line_number} is not discovery-only")
            if sample_path_count >= 500:
                break

    placeholder_hits = []
    for path in route_dir.glob(f"{OUTPUT_PREFIX}_*.json"):
        if path.name.endswith("_ROWS_2026-05-10.jsonl"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        for term in PLACEHOLDER_TERMS:
            if term.lower() in lower:
                placeholder_hits.append({"path": str(path.relative_to(ROOT)), "term": term})
    for path in route_dir.glob(f"{OUTPUT_PREFIX}_*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        for term in PLACEHOLDER_TERMS:
            if term.lower() in lower:
                placeholder_hits.append({"path": str(path.relative_to(ROOT)), "term": term})
    if placeholder_hits:
        failures.append(f"placeholder scan hits: {placeholder_hits[:20]}")

    result = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "verification_result",
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "failures": failures,
        "candidate_row_count": candidates.get("candidate_row_count"),
        "path_label_row_count": path_labels.get("path_label_row_count"),
        "selected_source_count": source_selection.get("selected_source_count"),
        "opened_family_count": family.get("opened_family_count"),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_promotion": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_paid_api_or_databento_route": False,
        "opens_mt5_order_account_history_behavior": False,
        "opens_remote_push": False,
        "opens_registry_edit": False,
        "credentials_touched": False,
        "changes_live_trading_behavior": False,
    }
    output_path = route_dir / f"{OUTPUT_PREFIX}_VERIFICATION_RESULT_{DATE}.json"
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-dir", type=Path, default=ROUTE_DIR)
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = verify(args.route_dir)
    if args.quiet:
        print(
            json.dumps(
                {
                    "ok": result["ok"],
                    "can_mark_goal_complete": result["can_mark_goal_complete"],
                    "failures": result["failures"],
                    "candidate_row_count": result["candidate_row_count"],
                    "path_label_row_count": result["path_label_row_count"],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
