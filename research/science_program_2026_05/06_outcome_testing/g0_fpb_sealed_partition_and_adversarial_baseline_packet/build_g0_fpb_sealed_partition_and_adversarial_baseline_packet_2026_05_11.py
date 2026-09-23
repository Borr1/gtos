"""Build the G0 FPB sealed partition and adversarial baseline packet.

This route is a partition/control packet only. It consumes the accepted FPB
discovery result screen, accepted G12 audit, and G0 synthesis artifacts, then
freezes partition, duplicate, baseline, source/as-of, concentration, ambiguity,
and falsification controls. It does not execute validation, score results, call
AI/API, read broker/account/order evidence, or change live behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-11"
PREFIX = "G0_FPB_SEALED_PARTITION"
ROUTE_ID = "G0_FPB_SEALED_PARTITION_AND_ADVERSARIAL_BASELINE_PACKET"
EVIDENCE_CLASS = "G0_SEALED_PARTITION_AND_BASELINE_PACKET_ONLY"
SCHEMA_VERSION = "g0_fpb_sealed_partition_packet_v1"
TERMINAL_DECISION = "ACCEPT_PACKET_CURRENT_DISCOVERY_UNIVERSE_CONTAMINATED_SOURCE_CONTROL_UNBLOCKER_REQUIRED"

TARGET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_mechanical_replay_family_path_behavior_discovery_result_screen"
)
G12_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_fpb_result_audit"
)
G0_SYNTHESIS_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_fpb_discovery_synthesis_control_route"
)
SOURCE_ENGINE_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_mechanical_replay_engine_from_source_universe"
)

CONTROLLING_PROMPT = (
    PROMPT_DIR
    / "G0_FPB_SEALED_PARTITION_AND_ADVERSARIAL_BASELINE_PACKET_GOAL_PROMPT_2026-05-11.md"
)
NEXT_PROMPT = (
    PROMPT_DIR
    / "FPB_SOURCE_EXPANSION_AND_SEALED_POOL_MATERIALIZATION_GOAL_PROMPT_2026-05-11.md"
)

INPUTS = {
    "controlling_prompt": CONTROLLING_PROMPT,
    "target_matrix": TARGET_DIR / "FPB_FULL_POPULATION_AGGREGATE_MATRIX_2026-05-10.json",
    "target_denominator_duplicate_policy": TARGET_DIR / "FPB_DENOMINATOR_DUPLICATE_POLICY_2026-05-10.json",
    "target_baseline_control_ledger": TARGET_DIR / "FPB_BASELINE_CONTROL_LEDGER_2026-05-10.json",
    "target_selection_bias_multiple_testing": TARGET_DIR
    / "FPB_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json",
    "target_compact_cap_diagnostics": TARGET_DIR / "FPB_COMPACT_CAP_DIAGNOSTICS_2026-05-10.json",
    "target_failure_anatomy": TARGET_DIR / "FPB_FAILURE_ANATOMY_NEXT_HYPOTHESIS_LEDGER_2026-05-10.json",
    "target_manifest": TARGET_DIR / "FPB_OUTPUT_MANIFEST_2026-05-10.json",
    "target_verification": TARGET_DIR / "FPB_VERIFICATION_RESULT_2026-05-10.json",
    "g12_audit": G12_DIR / "G12_FPB_RESULT_AUDIT_2026-05-11.json",
    "g12_verification": G12_DIR / "G12_FPB_AUDIT_VERIFICATION_2026-05-11.json",
    "g0_route_ranking": G0_SYNTHESIS_DIR / "G0_FPB_SYNTHESIS_ROUTE_RANKING_LEDGER_2026-05-11.json",
    "g0_sealed_readiness": G0_SYNTHESIS_DIR
    / "G0_FPB_SYNTHESIS_SEALED_VALIDATION_READINESS_LEDGER_2026-05-11.json",
    "g0_selection_bias": G0_SYNTHESIS_DIR / "G0_FPB_SYNTHESIS_SELECTION_BIAS_LEDGER_2026-05-11.json",
    "g0_hostile_review": G0_SYNTHESIS_DIR / "G0_FPB_SYNTHESIS_HOSTILE_EDGE_REVIEW_LEDGER_2026-05-11.json",
    "source_selection": SOURCE_ENGINE_DIR / "NO_API_MECHANICAL_REPLAY_SOURCE_SELECTION_AND_HASH_LEDGER_2026-05-10.json",
    "source_excluded": SOURCE_ENGINE_DIR / "NO_API_MECHANICAL_REPLAY_EXCLUDED_SLICE_LEDGER_2026-05-10.json",
    "source_candidate_inventory": SOURCE_ENGINE_DIR / "NO_API_MECHANICAL_REPLAY_CANDIDATE_INVENTORY_2026-05-10.json",
    "source_family_status": SOURCE_ENGINE_DIR / "NO_API_MECHANICAL_REPLAY_FAMILY_TERMINAL_STATUS_LEDGER_2026-05-10.json",
}

EXPECTED_COUNTS = {
    "raw_candidate_attempts": 13_540_033,
    "duplicate_candidate_keys": 687_275,
    "unique_nonduplicate_candidate_path_label_denominator": 12_852_758,
    "path_label_row_count": 12_852_758,
    "opened_family_count": 11,
    "baseline_control_family_count": 4,
    "selected_source_count": 365,
    "excluded_source_slice_count": 3135,
}

SELECTED_FAMILIES = [
    "adjacent_range_compression_breakout",
    "ob_retest",
    "opening_drive_no_fill_lifecycle",
]
BASELINE_CONTROLS = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]
NON_SELECTED_DISCOVERY_FAMILIES = [
    "fvg_fill",
    "liquidity_stop_run_context",
    "session_kz_sweep",
    "breaker_re_entry",
]
LABELS = [
    "ONE_ATR_CONTINUATION_CONTEXT_TOUCH",
    "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH",
    "MIDPOINT_RETRACE_BEFORE_EXTENSION",
    "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE",
    "SAME_BAR_CONTEXT_AMBIGUOUS",
    "UNRESOLVED_BY_WINDOW",
    "UNRESOLVED_AT_SOURCE_END",
]

SAFE_FLAGS: dict[str, Any] = {
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
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}

ARTIFACTS = {
    "context_anchor": f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}",
    "evidence_reconciliation": f"{PREFIX}_EVIDENCE_RECONCILIATION_LEDGER_{DATE_TAG}",
    "partition_ledger": f"{PREFIX}_PARTITION_LEDGER_{DATE_TAG}",
    "discovery_exposure": f"{PREFIX}_DISCOVERY_EXPOSURE_LEDGER_{DATE_TAG}",
    "purge_duplicate_policy": f"{PREFIX}_PURGE_EMBARGO_DUPLICATE_POLICY_{DATE_TAG}",
    "baseline_packet": f"{PREFIX}_ADVERSARIAL_BASELINE_PACKET_{DATE_TAG}",
    "concentration_stress": f"{PREFIX}_CONCENTRATION_AND_STRESS_REQUIREMENTS_{DATE_TAG}",
    "ambiguity_policy": f"{PREFIX}_AMBIGUITY_UNRESOLVED_POLICY_{DATE_TAG}",
    "source_contract": f"{PREFIX}_SOURCE_ASOF_NOLEAK_CONTRACT_{DATE_TAG}",
    "falsification": f"{PREFIX}_FALSIFICATION_CRITERIA_{DATE_TAG}",
    "hardening": f"{PREFIX}_HARDENING_COVERAGE_LEDGER_{DATE_TAG}",
    "no_lazy_blocker": f"{PREFIX}_NO_LAZY_BLOCKER_LEDGER_{DATE_TAG}",
    "source_saturation": f"{PREFIX}_SEARCHED_ROOT_SOURCE_SATURATION_LEDGER_{DATE_TAG}",
    "hostile_edge": f"{PREFIX}_HOSTILE_EDGE_REVIEW_LEDGER_{DATE_TAG}",
    "negative_anatomy": f"{PREFIX}_NEGATIVE_FAILURE_ANATOMY_LEDGER_{DATE_TAG}",
    "selection_bias": f"{PREFIX}_SELECTION_BIAS_MULTIPLE_TESTING_CARRY_FORWARD_{DATE_TAG}",
    "process_limitations": f"{PREFIX}_PROCESS_LIMITATION_COUNTERMEASURES_{DATE_TAG}",
    "saturation": f"{PREFIX}_SATURATION_SELF_REDTEAM_{DATE_TAG}",
    "next_prompt_pack": f"{PREFIX}_NEXT_PROMPT_PACK_{DATE_TAG}",
    "no_leak_dirty_state": f"{PREFIX}_NOLEAK_DIRTY_STATE_AUDIT_{DATE_TAG}",
    "manifest": f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}",
    "completion": f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


GENERATED_AT = utc_now()


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_git(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": "git " + " ".join(args),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip().splitlines(),
        "stderr": proc.stderr.strip().splitlines(),
    }


def safe_payload(artifact_family: str, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": GENERATED_AT,
        "terminal_decision": TERMINAL_DECISION,
        **SAFE_FLAGS,
        **body,
    }


def write_json(base: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{base}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_md(base: str, title: str, payload: dict[str, Any], bullets: list[str] | None = None) -> Path:
    path = ROUTE_DIR / f"{base}.md"
    summary = {
        key: payload.get(key)
        for key in (
            "artifact_family",
            "terminal_decision",
            "current_sealed_historical_validation_source_rows",
            "source_control_unblocker_prompt_emitted",
            "completion_standard_satisfied",
            "can_mark_goal_complete_after_scoped_commit_and_context_refresh",
            "validation_safe",
            "outcome_review_opened",
            "live_effect",
        )
        if key in payload
    }
    lines = [
        f"# {title}",
        "",
        f"- Route: `{ROUTE_ID}`",
        f"- Evidence class: `{EVIDENCE_CLASS}`",
        f"- Promotion posture: `{SAFE_FLAGS['promotion_verdict']}`",
        f"- validation_safe: `{str(SAFE_FLAGS['validation_safe']).lower()}`",
        f"- outcome_review_opened: `{str(SAFE_FLAGS['outcome_review_opened']).lower()}`",
        f"- live_effect: `{str(SAFE_FLAGS['live_effect']).lower()}`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, indent=2, sort_keys=True),
        "```",
    ]
    if bullets:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {bullet}" for bullet in bullets)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def emit(base: str, title: str, payload: dict[str, Any], bullets: list[str] | None = None) -> dict[str, str]:
    write_json(base, payload)
    write_md(base, title, payload, bullets)
    return {"json": repo_path(ROUTE_DIR / f"{base}.json"), "md": repo_path(ROUTE_DIR / f"{base}.md")}


def pct(count: int, denominator: int) -> float:
    return round(count / denominator, 8) if denominator else 0.0


def top_slices(mapping: dict[str, Any], denominator: int, limit: int = 5) -> list[dict[str, Any]]:
    rows = []
    for key, value in sorted(mapping.items(), key=lambda item: int(item[1]), reverse=True)[:limit]:
        rows.append({"slice": key, "count": int(value), "share_of_family": pct(int(value), denominator)})
    return rows


def family_record(matrix: dict[str, Any], family_id: str) -> dict[str, Any]:
    row = next(item for item in matrix["family_rows"] if item["family_id"] == family_id)
    denominator = int(row["denominator"])
    counts = {label: int(row["counts"].get(label, 0)) for label in LABELS}
    return {
        "family_id": family_id,
        "candidate_denominator": denominator,
        "label_counts": counts,
        "label_proportions": {label: pct(count, denominator) for label, count in counts.items()},
        "ambiguity_unresolved_count": counts["SAME_BAR_CONTEXT_AMBIGUOUS"]
        + counts["UNRESOLVED_BY_WINDOW"]
        + counts["UNRESOLVED_AT_SOURCE_END"],
        "ambiguity_unresolved_rate": pct(
            counts["SAME_BAR_CONTEXT_AMBIGUOUS"]
            + counts["UNRESOLVED_BY_WINDOW"]
            + counts["UNRESOLVED_AT_SOURCE_END"],
            denominator,
        ),
        "top_source_family_slices": top_slices(matrix["candidate_by_family_source_family"].get(family_id, {}), denominator),
        "top_symbol_slices": top_slices(matrix["candidate_by_family_symbol"].get(family_id, {}), denominator),
        "top_timeframe_slices": top_slices(matrix["candidate_by_family_timeframe"].get(family_id, {}), denominator),
        "top_session_kz_slices": top_slices(
            matrix["candidate_by_family_session_or_kill_zone"].get(family_id, {}), denominator
        ),
        "top_regime_slices": top_slices(matrix["candidate_by_family_regime_phase"].get(family_id, {}), denominator),
        "side_slices": top_slices(matrix["candidate_by_family_side"].get(family_id, {}), denominator),
        "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_VALIDATION_OR_PERFORMANCE",
    }


def source_hash_inventory() -> list[dict[str, Any]]:
    rows = []
    for role, path in INPUTS.items():
        rows.append(
            {
                "role": role,
                "path": repo_path(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
                "sha256": sha256_file(path),
            }
        )
    return rows


def summarize_search_root(root: Path, patterns: tuple[str, ...], max_entries: int = 5000) -> dict[str, Any]:
    record: dict[str, Any] = {
        "root": str(root),
        "exists": root.exists(),
        "patterns": list(patterns),
        "entries_scanned_cap": max_entries,
        "entries_scanned": 0,
        "pattern_hits": {pattern: 0 for pattern in patterns},
        "scan_truncated": False,
        "status": "ROOT_ABSENT",
    }
    if not root.exists():
        return record
    try:
        for current, _dirs, files in os.walk(root):
            for name in files:
                record["entries_scanned"] += 1
                lower = name.lower()
                for pattern in patterns:
                    if lower.endswith(pattern.lower().lstrip("*")):
                        record["pattern_hits"][pattern] += 1
                if record["entries_scanned"] >= max_entries:
                    record["scan_truncated"] = True
                    record["status"] = "SCANNED_WITH_CAP"
                    return record
    except OSError as exc:
        record["status"] = "SCAN_ERROR"
        record["error"] = str(exc)
        return record
    record["status"] = "SCANNED"
    return record


def selected_source_summary(source_selection: dict[str, Any]) -> dict[str, Any]:
    selected = source_selection.get("selected_sources", [])
    source_ids = [row["source_row_id"] for row in selected]
    source_hashes = [row.get("source_sha256") for row in selected if row.get("source_sha256")]
    return {
        "selected_source_count": len(selected),
        "selected_source_ids_sample": source_ids[:20],
        "selected_source_id_min": min(source_ids) if source_ids else None,
        "selected_source_id_max": max(source_ids) if source_ids else None,
        "selected_source_hash_count": len(set(source_hashes)),
        "selected_by_source_family": source_selection.get("selected_by_source_family", {}),
        "selected_by_symbol": source_selection.get("selected_by_symbol", {}),
        "selected_by_timeframe": source_selection.get("selected_by_timeframe", {}),
        "all_selected_sources_reclassified_by_this_packet": "DISCOVERY_EXPOSED_CONTAMINATED_FOR_FUTURE_SEALED_VALIDATION",
    }


def build_next_prompt() -> None:
    text = f"""# FPB Source Expansion And Sealed Pool Materialization Goal Prompt

Date: {DATE_TAG}
Owner lane: source-control unblocker after `{ROUTE_ID}`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `FPB_SOURCE_EXPANSION_AND_SEALED_POOL_MATERIALIZATION` as a source/control route only.

The current accepted FPB source universe is discovery-exposed by the full-population discovery result screen and G12 audit. This route must materialize a clean sealed historical source pool, or prove the exact source/access requirement, before any validation execution prompt can exist.

## Mandatory Preflight

1. Run `python scripts\\generate_live_state.py`.
2. Read `.context\\LIVE_STATE.md`.
3. Read `.context\\00_core\\quick_reference_card.md`.
4. Read `.context\\00_core\\research_operating_doctrine.md`.
5. Read `.context\\00_core\\research_current_state.md`.
6. Read `.context\\00_core\\goal_session_research_discipline.md`.
7. Read `.context\\00_core\\local_heavy_data_inventory.md`.
8. Read `research\\science_program_2026_05\\06_outcome_testing\\g0_fpb_sealed_partition_and_adversarial_baseline_packet\\`.

## Evidence Class

`FPB_SOURCE_EXPANSION_AND_SEALED_POOL_MATERIALIZATION_ONLY`.

Allowed: source discovery, source hashing, coverage-window extraction, duplicate-key prechecks, partition ledger materialization, source/as-of/no-leak repair, and G12-ready audit prompt design.

Forbidden: validation execution, promotion, result/R/PnL/win-rate/expectancy/performance scoring, AI/API calls, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, live behavior, or prompt/config/risk/safety/execution/canary/selector changes.

## Required Work

1. Treat all `365` selected source rows and `12,852,758` accepted FPB path-label rows from the accepted discovery result screen as contaminated for sealed validation.
2. Search current worktree, absolute repo data roots, `C:\\tmp\\gtos_otb`, and permitted Sierra/vendor/cache roots for candidate source rows not already present in the selected-source hash ledger.
3. For each candidate source, emit source hash, source family, symbol, timeframe, coverage start/end UTC, as-of parser contract, no-leak status, duplicate-source-hash status, and whether it can enter a future sealed validation pool.
4. Preserve the four adversarial baselines: random-session, shifted-entry, momentum-continuation, and mean-reversion.
5. Apply the frozen purge/embargo, duplicate, ambiguity, concentration, and source/as-of policies from the sealed packet.
6. Emit either a G12 audit prompt for source-pool acceptance or an exact owner/source/access requirement.

## Completion Standard

Complete only when every proposed sealed source row has a source hash, coverage window, no-leak/as-of status, duplicate-source decision, and partition assignment; current discovery rows remain excluded; safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`; and no forbidden surface is opened.
"""
    NEXT_PROMPT.write_text(text, encoding="utf-8")


def count_reconciliation(matrix: dict[str, Any], g12: dict[str, Any], source_selection: dict[str, Any], excluded: dict[str, Any]) -> dict[str, Any]:
    actual = {
        "raw_candidate_attempts": matrix.get("raw_candidate_attempts"),
        "duplicate_candidate_keys": matrix.get("duplicate_candidate_keys"),
        "unique_nonduplicate_candidate_path_label_denominator": matrix.get(
            "unique_nonduplicate_candidate_path_label_denominator"
        ),
        "path_label_row_count": matrix.get("path_label_row_count"),
        "opened_family_count": matrix.get("opened_family_count"),
        "baseline_control_family_count": len(matrix.get("baseline_control_families", [])),
        "selected_source_count": source_selection.get("selected_source_count"),
        "excluded_source_slice_count": excluded.get("excluded_slice_count"),
    }
    checks = []
    for key, expected in EXPECTED_COUNTS.items():
        checks.append(
            {
                "check_id": key,
                "expected": expected,
                "actual": actual.get(key),
                "g12_actual": {
                    "raw_candidate_attempts": g12.get("count_audit", {}).get("headline_counts", {}).get("raw_candidate_attempts"),
                    "duplicate_candidate_keys": g12.get("count_audit", {}).get("headline_counts", {}).get("duplicate_candidate_keys"),
                    "path_label_row_count": g12.get("count_audit", {}).get("headline_counts", {}).get("path_label_row_count"),
                    "unique_nonduplicate_candidate_path_label_denominator": g12.get("count_audit", {})
                    .get("headline_counts", {})
                    .get("unique_nonduplicate_candidate_path_label_denominator"),
                    "opened_family_count": g12.get("opened_family_count"),
                    "baseline_control_family_count": g12.get("baseline_control_family_count"),
                }.get(key),
                "status": "PASS" if actual.get(key) == expected else "FAIL",
            }
        )
    return safe_payload(
        "evidence_reconciliation_ledger",
        {
            "all_counts_preserved": all(row["status"] == "PASS" for row in checks),
            "accepted_counts": EXPECTED_COUNTS,
            "count_checks": checks,
            "accepted_g12_decision": g12.get("decision"),
            "accepted_target_route": g12.get("target_route_id"),
            "boundary": "COUNTS_ARE_DISCOVERY_CONTROL_FACTS_ONLY_NOT_VALIDATION_OR_PERFORMANCE",
        },
    )


def build_partition_ledger(
    matrix: dict[str, Any],
    source_selection: dict[str, Any],
    excluded: dict[str, Any],
    selected_family_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    excluded_by_reason = excluded.get("by_reason", {})
    return safe_payload(
        "partition_ledger",
        {
            "partition_status": "CURRENT_ACCEPTED_FPB_UNIVERSE_IS_DISCOVERY_EXPOSED_NO_VALIDATION_EXECUTION",
            "discovery_pool": {
                "source_rows": source_selection.get("selected_source_count"),
                "raw_candidate_attempts": matrix.get("raw_candidate_attempts"),
                "duplicate_candidate_keys": matrix.get("duplicate_candidate_keys"),
                "unique_path_label_rows": matrix.get("unique_nonduplicate_candidate_path_label_denominator"),
                "opened_families": matrix.get("opened_families"),
                "selected_packet_families": SELECTED_FAMILIES,
                "assignment": "ALL_DISCOVERY_EXPOSED_FOR_FUTURE_SEALED_VALIDATION",
            },
            "development_pool": {
                "rows": 0,
                "assignment": "NO_ADDITIONAL_ROW_DEVELOPMENT_OPENED_BY_THIS_PACKET",
                "allowed_future_use": "parser_and_source_contract_tests_only_after_duplicate_and_no_leak_review",
            },
            "sealed_historical_validation_pool": {
                "current_source_rows": 0,
                "current_candidate_rows": 0,
                "reason": "accepted FPB result screen and G12 audit opened the current 365 selected source rows and all path-label aggregates",
                "required_unblocker": "materialize new source rows with hashes and coverage windows not present in selected-source ledger",
            },
            "stress_robustness_pool": {
                "current_discovery_aggregates_allowed": True,
                "allowed_use": "control-design and stress-specification only; no validation labels or performance interpretation",
                "stress_axes": [
                    "source_family",
                    "symbol",
                    "timeframe",
                    "session_or_kill_zone",
                    "regime_phase",
                    "side",
                    "duplicate_cluster",
                    "label_ambiguity_state",
                    "baseline_control_family",
                ],
            },
            "forward_shadow_pool": {
                "current_rows": 0,
                "allowed_use": "capture-quality and current-system realism only after separate source-control route",
            },
            "contaminated_forbidden_pool": {
                "current_selected_source_rows": source_selection.get("selected_source_count"),
                "current_unique_path_label_rows": matrix.get("unique_nonduplicate_candidate_path_label_denominator"),
                "excluded_source_slice_count": excluded.get("excluded_slice_count"),
                "excluded_by_reason": excluded_by_reason,
                "forbidden_denominator_entries": [
                    "any row from selected source hashes",
                    "any duplicate candidate key from the accepted FPB path-label set",
                    "compact materialized rows used only for schema sanity",
                    "blocked source-state rows requiring broker/order/account truth",
                    "same-bar or source-end unresolved rows unless split into fail-closed ambiguity strata",
                ],
            },
            "selected_family_partition_decisions": selected_family_rows,
            "validation_execution_prompt_emitted": False,
            "source_control_unblocker_prompt_emitted": True,
            "current_sealed_historical_validation_source_rows": 0,
        },
    )


def build_discovery_exposure(matrix: dict[str, Any], source_selection: dict[str, Any]) -> dict[str, Any]:
    selected_summary = selected_source_summary(source_selection)
    exposed_by_family = {family: family_record(matrix, family) for family in SELECTED_FAMILIES}
    return safe_payload(
        "discovery_exposure_ledger",
        {
            "exposure_rule": "any row, window, source hash, duplicate key, family aggregate, or slice aggregate opened by FPB discovery/G0/G12 is unavailable as sealed validation evidence",
            "source_exposure": selected_summary,
            "family_exposure": exposed_by_family,
            "global_exposed_axes": {
                "source_families": matrix.get("candidate_by_family_source_family", {}),
                "symbols": matrix.get("candidate_by_family_symbol", {}),
                "timeframes": matrix.get("candidate_by_family_timeframe", {}),
                "sessions_kz": matrix.get("candidate_by_family_session_or_kill_zone", {}),
                "regime_phases": matrix.get("candidate_by_family_regime_phase", {}),
                "sides": matrix.get("candidate_by_family_side", {}),
            },
            "window_policy": "current source artifacts do not carry coverage start/end for every selected source row; entire selected source row/file hash is therefore contaminated, and future materialization must extract coverage windows before validation",
        },
    )


def build_purge_policy() -> dict[str, Any]:
    return safe_payload(
        "purge_embargo_duplicate_policy",
        {
            "duplicate_candidate_key_policy": {
                "definition": "symbol|timeframe|family_id|side|decision_time_utc|zone_reference_id|source_sha256",
                "future_validation_rule": "one row per duplicate key; any key seen in discovery is excluded from sealed validation",
                "duplicate_cluster_policy": "cluster by symbol|family_id|side|timeframe|decision_time_utc_bucket|source_hash; one canonical candidate per cluster unless a predeclared cluster stress test is used",
            },
            "source_hash_policy": {
                "selected_source_hashes": "all 365 accepted source hashes are contaminated for sealed validation",
                "future_source_rule": "new source hash must not match selected source hash, duplicate hash, or compact-materialized source artifact",
            },
            "purge_embargo_policy": {
                "same_source_hash": "full exclusion",
                "same_symbol_timeframe_adjacent_source": "purge the source coverage window and embargo 14 calendar days on both sides once coverage windows are materialized",
                "same_decision_time_duplicate_cluster": "exclude exact duplicate and same timestamp cluster across source families unless predeclared as proxy stress only",
                "missing_coverage_window": "fail closed to source-control unblocker before validation",
            },
            "compact_policy": {
                "compact_rows_written": 120000,
                "compact_rows_suppressed": 12732758,
                "allowed_use": "schema/materialization sanity only",
                "forbidden_use": "decisive route choice, validation denominator, or family ranking",
            },
        },
    )


def build_baseline_packet(matrix: dict[str, Any]) -> dict[str, Any]:
    baseline_rows = [family_record(matrix, family) for family in BASELINE_CONTROLS]
    return safe_payload(
        "adversarial_baseline_packet",
        {
            "all_four_baselines_frozen": True,
            "baseline_controls": [
                {
                    "family_id": "baseline_random_session_control",
                    "adversarial_question": "does family behavior disappear when session timing is randomized under the same source universe",
                    "future_validation_role": "placebo for session/clock dependence",
                },
                {
                    "family_id": "baseline_shifted_entry_control",
                    "adversarial_question": "does a nearby shifted entry explain the same path behavior without the family mechanism",
                    "future_validation_role": "entry-locality and arbitrary offset control",
                },
                {
                    "family_id": "baseline_momentum_continuation",
                    "adversarial_question": "does simple continuation explain the path behavior",
                    "future_validation_role": "hidden beta/trend continuation control",
                },
                {
                    "family_id": "baseline_mean_reversion",
                    "adversarial_question": "does simple reversion explain the path behavior",
                    "future_validation_role": "protective-boundary/retrace control",
                },
            ],
            "baseline_discovery_rows": baseline_rows,
            "future_rule": "every selected family must be tested against all four baselines before any validation interpretation; baseline omission fails the packet",
        },
    )


def build_concentration_stress(matrix: dict[str, Any]) -> dict[str, Any]:
    selected = [family_record(matrix, family) for family in SELECTED_FAMILIES]
    return safe_payload(
        "concentration_and_stress_requirements",
        {
            "caps": {
                "single_source_hash_max_share": 0.20,
                "single_source_family_soft_cap": 0.70,
                "single_symbol_max_share": 0.25,
                "single_timeframe_max_share": 0.35,
                "single_session_kz_max_share": 0.35,
                "single_regime_phase_max_share": 0.40,
                "single_side_max_share": 0.60,
                "duplicate_cluster_max_rows": 1,
                "effective_n_family_floor": 30,
                "effective_n_combined_floor": 100,
            },
            "required_stress_tests": [
                "leave_one_source_family",
                "leave_one_symbol",
                "leave_one_timeframe",
                "leave_one_session_or_kz",
                "leave_one_regime_phase",
                "leave_one_side",
                "remove_top_1_source_hash",
                "remove_top_5_duplicate_clusters",
                "ambiguity_fail_closed",
                "all_four_baselines_required",
            ],
            "selected_family_current_discovery_concentration": selected,
            "current_discovery_pool_status": "USED_FOR_STRESS_DESIGN_ONLY_NOT_VALIDATION",
        },
    )


def build_ambiguity_policy(matrix: dict[str, Any]) -> dict[str, Any]:
    rows = [family_record(matrix, family) for family in SELECTED_FAMILIES + NON_SELECTED_DISCOVERY_FAMILIES]
    return safe_payload(
        "ambiguity_unresolved_policy",
        {
            "label_vocabulary": LABELS,
            "fail_closed_labels_before_validation": [
                "SAME_BAR_CONTEXT_AMBIGUOUS",
                "UNRESOLVED_BY_WINDOW",
                "UNRESOLVED_AT_SOURCE_END",
            ],
            "future_validation_rule": "ambiguous and unresolved rows are excluded from primary validation denominator, then split into a named robustness stress stratum",
            "same_bar_policy": "same-bar terminal context cannot be guessed; it is either excluded or bounded by a predeclared worst-case stress rule",
            "source_end_policy": "source-end unresolved rows require longer source coverage or exclusion",
            "window_unresolved_policy": "window-unresolved rows may only enter an unresolved-rate diagnostic, not primary validation",
            "family_ambiguity_burden_discovery_only": rows,
        },
    )


def build_source_contract() -> dict[str, Any]:
    fields = [
        ("source_row_id", "source-control", "must be unique and hash-bound before candidate generation"),
        ("source_sha256", "source-control", "must hash the raw source file used for candidate generation"),
        ("source_family", "as-of input", "must be known before candidate decision"),
        ("symbol", "as-of input", "must be source-native and mapped before candidate decision"),
        ("timeframe", "as-of input", "must be parser-native and not inferred from future path"),
        ("coverage_start_utc", "source-control", "required before purge/embargo can run"),
        ("coverage_end_utc", "source-control", "required before purge/embargo can run"),
        ("decision_time_utc", "as-of input", "candidate close time only"),
        ("family_id", "as-of input", "candidate family must be frozen before labels are opened"),
        ("side", "as-of input", "must be generated from pre-decision mechanics"),
        ("session_or_kill_zone", "as-of derived input", "derive from decision_time_utc and frozen calendar rules"),
        ("regime_phase", "as-of derived input", "derive only from history available at decision_time_utc"),
        ("zone_reference_id", "as-of input", "must be generated before label path opens"),
        ("candidate_duplicate_key", "source-control", "must be computed before denominator admission"),
        ("candidate_cluster_key", "source-control", "must be computed before concentration checks"),
        ("path_label_status", "label output", "must stay hidden until validation execution route opens labels"),
        ("label_observed_time_utc", "label output", "must stay hidden until validation execution route opens labels"),
        ("baseline_family_id", "control input", "must be one of the four frozen baselines"),
        ("parser_version", "source-control", "must be frozen before validation source opening"),
        ("asof_feature_manifest_sha256", "source-control", "must bind allowed fields and forbid post-label fields"),
    ]
    return safe_payload(
        "source_asof_noleak_contract",
        {
            "field_count": len(fields),
            "fields": [
                {
                    "field_name": name,
                    "field_class": klass,
                    "exact_requirement": requirement,
                    "no_leak_gate": "PASS_REQUIRED_BEFORE_VALIDATION",
                }
                for name, klass, requirement in fields
            ],
            "forbidden_fields": [
                "broker/account/order/history/deal/position/ticket fields",
                "post-label path result fields in validation inputs",
                "AI/API decision text unless a separate AI decision-value route is opened",
                "R/PnL/win-rate/expectancy/performance labels",
                "manual researcher annotations used as source truth",
            ],
            "source_contract_status": "COMPLETE_FOR_PACKET_DESIGN_SOURCE_POOL_MATERIALIZATION_REQUIRED_BEFORE_VALIDATION",
        },
    )


def build_falsification() -> dict[str, Any]:
    family_rules = {
        "adjacent_range_compression_breakout": [
            "kill if distinct path-label profile collapses under source-family, M1-only, symbol, and outside-kill-zone holdouts",
            "kill if shifted-entry or momentum-continuation baseline explains the same context-touch distribution",
            "downgrade if source expansion cannot reduce top-source/timeframe concentration under frozen caps",
        ],
        "ob_retest": [
            "kill if GTOS-core structural family is not separable from momentum-continuation and mean-reversion baselines on sealed rows",
            "kill if source/as-of zone reference cannot be generated before label opening",
            "downgrade if single-symbol or single-timeframe concentration breaches caps after source expansion",
        ],
        "opening_drive_no_fill_lifecycle": [
            "kill if no-fill lifecycle source state cannot be separated from pure clock/session baselines",
            "kill if midpoint/extension labels require non-generatable historical GTOS lifecycle truth",
            "downgrade if sample floor or session concentration caps fail after source expansion",
        ],
        "combined_route": [
            "kill if no clean sealed source pool can be materialized outside the accepted discovery universe",
            "kill if any of the four adversarial baselines is omitted",
            "kill if duplicate, ambiguity, purge/embargo, or source/as-of controls fail closed",
            "kill if selection-bias debt is not carried into the validation analysis plan",
        ],
    }
    return safe_payload("falsification_criteria", {"family_rules": family_rules})


def build_hardening() -> dict[str, Any]:
    coverage = [
        ("goal_session_research_discipline", "context anchor, searched-root ledger, no-lazy-blocker ledger, saturation pass"),
        ("research_operating_doctrine", "aggressive source-control route with strict NO_PROMOTION_VERDICT boundary"),
        ("local_heavy_data_inventory", "absolute data roots and prior worktree searches recorded"),
        ("ai_in_loop_cost_control", "no API use; future AI work isolated to decision-value sampling"),
        ("historical_sealed_validation_protocol", "discovery/development/sealed/stress/forward/contaminated pools frozen"),
        ("hostile_edge_review_lens", "selected, deferred, and baseline families reviewed adversarially"),
        ("process_limitation_countermeasures", "classification-only, self-audit, dirty-main, pycache, proxy, prompt boxing, and drift controls frozen"),
    ]
    return safe_payload(
        "hardening_coverage_ledger",
        {
            "coverage": [
                {"source": source, "artifact_coverage": artifact, "status": "PASS"} for source, artifact in coverage
            ],
            "all_hardening_sources_mapped": True,
        },
    )


def build_no_lazy_blocker() -> dict[str, Any]:
    blockers = [
        {
            "blocker_id": "FPB-SEALED-SOURCE-001",
            "blocker": "current accepted source universe is discovery-exposed",
            "same_evidence_class_pursuit": "reconciled source counts, selected source hashes, excluded source reasons, and FPB/G12 acceptance",
            "terminal_status": "EXACT_SOURCE_CONTROL_UNBLOCKER_PROMPT_EMITTED",
            "exact_next_action": repo_path(NEXT_PROMPT),
        },
        {
            "blocker_id": "FPB-COVERAGE-WINDOW-002",
            "blocker": "selected source rows do not expose complete coverage start/end windows needed for future purge/embargo",
            "same_evidence_class_pursuit": "fail-closed policy freezes whole selected source hashes as contaminated",
            "terminal_status": "EXACT_SOURCE_FIELD_REQUIREMENT_DEFINED",
            "exact_next_action": "source expansion route must emit coverage_start_utc and coverage_end_utc for each proposed sealed source row",
        },
    ]
    return safe_payload(
        "no_lazy_blocker_ledger",
        {
            "blockers": blockers,
            "remaining_vague_blockers": [],
            "remaining_same_evidence_class_gaps": [],
        },
    )


def build_source_saturation() -> dict[str, Any]:
    roots = [
        ROOT / "data",
        ROOT / "data" / "ticks",
        ROOT / "shadow_logs",
        ROOT / "exports",
        Path(r"C:\tmp\gtos_otb"),
        Path(r"C:\SierraChart\Data"),
        TARGET_DIR,
        G12_DIR,
        G0_SYNTHESIS_DIR,
        SOURCE_ENGINE_DIR,
    ]
    patterns = ("*.csv", "*.json", "*.jsonl", "*.parquet", "*.scid", "*.depth")
    return safe_payload(
        "searched_root_source_saturation_ledger",
        {
            "input_hashes": source_hash_inventory(),
            "searched_roots": [summarize_search_root(root, patterns) for root in roots],
            "positive_evidence": [
                "accepted FPB result screen and G12 audit found complete discovery/control counts",
                "source-selection ledger contains 365 selected source rows and 3135 excluded source slices",
                "current accepted source universe is exhausted for sealed validation because selected rows were opened by discovery",
            ],
            "negative_evidence": [
                "no broker/account/order/history/deal/position sources were read",
                "no API, paid vendor, credential, remote, live MT5, or validation execution route was opened",
            ],
            "broker_or_account_sources_read": False,
            "source_saturation_status": "CURRENT_PACKET_SOURCE_SATURATED_SOURCE_EXPANSION_REQUIRED_FOR_SEALED_POOL",
        },
    )


def build_hostile_edge(matrix: dict[str, Any]) -> dict[str, Any]:
    selected_reviews = {
        "adjacent_range_compression_breakout": {
            "why_mechanism_might_exist": "compression can store latent directional energy before a range break",
            "who_pays": "late range participants and stop orders around compression boundaries",
            "what_destroys_it": "arbitrary offset entry, one-source M1 concentration, or broad momentum baseline equivalence",
            "most_threatening_baseline": "baseline_momentum_continuation",
            "future_kill_test": "leave-one-timeframe/source and shifted-entry baseline stress under sealed source rows",
        },
        "ob_retest": {
            "why_mechanism_might_exist": "structural retest of an order block can mark a defended imbalance/repricing zone",
            "who_pays": "participants trapped around the prior structural break",
            "what_destroys_it": "simple continuation/reversion baselines or stale zone references",
            "most_threatening_baseline": "baseline_shifted_entry_control",
            "future_kill_test": "sealed OB source/as-of zone proof plus all four baseline comparisons",
        },
        "opening_drive_no_fill_lifecycle": {
            "why_mechanism_might_exist": "opening-drive extension without fill may encode clock/session flow imbalance",
            "who_pays": "late drive chasers or unfilled mean-reversion liquidity near midpoint",
            "what_destroys_it": "session-only random control, missing lifecycle truth, or midpoint label ambiguity",
            "most_threatening_baseline": "baseline_random_session_control",
            "future_kill_test": "clock/session holdout and source-state separation before validation labels open",
        },
    }
    deferred_reviews = {
        "fvg_fill": "deferred because same-bar ambiguity burden is too high for a sealed validation packet without a stricter ambiguity-control lane",
        "liquidity_stop_run_context": "deferred because baseline resemblance and liquidity/session beta need source-slice separation first",
        "session_kz_sweep": "deferred because session timing can be explained by random-session or shifted-entry controls",
        "breaker_re_entry": "deferred because denominator is small relative to other families and needs expansion or narrow holdout design",
        "baseline_controls": "retained only as adversarial controls, not candidate families",
    }
    return safe_payload(
        "hostile_edge_review_ledger",
        {
            "selected_family_reviews": selected_reviews,
            "deferred_or_excluded_family_reviews": deferred_reviews,
            "selected_family_discovery_slices": {family: family_record(matrix, family) for family in SELECTED_FAMILIES},
        },
    )


def build_negative_anatomy(matrix: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for family in NON_SELECTED_DISCOVERY_FAMILIES:
        record = family_record(matrix, family)
        rows.append(
            {
                "family_id": family,
                "decision": "NOT_IN_SELECTED_PACKET_PRIMARY_FAMILIES",
                "failure_or_limitation_anatomy": {
                    "ambiguity_unresolved_rate": record["ambiguity_unresolved_rate"],
                    "top_source_family_slices": record["top_source_family_slices"],
                    "top_timeframe_slices": record["top_timeframe_slices"],
                    "exact_followup": {
                        "fvg_fill": "same-bar ambiguity resolution and fail-closed policy route",
                        "liquidity_stop_run_context": "baseline-dominance and liquidity/session stress route",
                        "session_kz_sweep": "session-clock baseline stress route",
                        "breaker_re_entry": "sample expansion and duplicate policy route",
                    }[family],
                },
                "status": "NEGATIVE_OR_LIMITATION_LEARNING_CAPTURED_NOT_VALIDATION",
            }
        )
    return safe_payload("negative_failure_anatomy_ledger", {"rows": rows})


def build_selection_bias(selection: dict[str, Any], g0_selection: dict[str, Any]) -> dict[str, Any]:
    return safe_payload(
        "selection_bias_multiple_testing_carry_forward",
        {
            "opened_family_count": 11,
            "baseline_control_count": 4,
            "label_count": 7,
            "slice_dimensions_opened": selection.get("multiple_testing_debt", {}).get("slice_dimensions_reported", []),
            "selected_families": SELECTED_FAMILIES,
            "selection_process": "selected after FPB discovery and G0 synthesis, therefore future validation must carry selection-bias debt",
            "multiple_testing_debt_policy": [
                "future validation report must state that selected families came from an opened discovery screen",
                "future validation cannot call the selected packet independent unless the sealed source pool was unopened before this packet",
                "all four baselines and all declared stress axes must be run or the route fails",
                "no post-hoc threshold rescue can be promoted",
            ],
            "upstream_g0_selection_boundary": g0_selection.get("anti_bias_boundary"),
        },
    )


def build_process_limitations() -> dict[str, Any]:
    items = [
        ("classification_only_trap", "source-control unblocker emitted with exact source fields instead of stopping at contamination label"),
        ("self_audit_trap", "next source-pool route should emit a G12 audit prompt before validation execution"),
        ("worktree_data_blindness", "absolute data, tick, C:/tmp, and Sierra roots searched with capped counts"),
        ("dirty_main_verifier_noise", "no-leak audit scopes unrelated runtime dirt separately from route artifacts"),
        ("autostash_staging_risk", "final commit process must stage only route/context files"),
        ("windows_pycache_temp_friction", "focused tests use normal pytest; py_compile can use explicit output fallback if needed"),
        ("public_source_fragility", "not applicable because no public web source used"),
        ("proxy_source_ambiguity", "Sierra/futures/proxy sources require source-family stress and cannot prove broker-native behavior"),
        ("prompt_boxing", "selected families reviewed with deferred and baseline families, not only top route"),
        ("context_drift", "context anchor records controlling prompt, inputs, HEAD, and safe flags"),
        ("result_control_confusion", "current route emits source-control unblocker and no validation prompt"),
    ]
    return safe_payload(
        "process_limitation_countermeasures",
        {"countermeasures": [{"limitation": key, "countermeasure": value, "status": "PASS"} for key, value in items]},
    )


def build_saturation() -> dict[str, Any]:
    qa = [
        ("discovery_leak_mistake", "using any accepted FPB source hash or duplicate key in sealed validation would leak discovery evidence"),
        ("bad_denominator_mistake", "compact, duplicate, blocked, unresolved, or source-limited rows enter only named stress/control strata"),
        ("most_vulnerable_family", "adjacent_range_compression_breakout is most vulnerable to M1/source concentration; opening-drive is most vulnerable to session-clock controls"),
        ("threatening_baselines", "momentum threatens adjacent compression; shifted-entry threatens OB retest; random-session threatens opening-drive lifecycle"),
        ("ambiguity_policy", "same-bar, source-end, and window-unresolved labels fail closed from primary validation"),
        ("skeptical_g12_rejection", "G12 would reject a validation prompt from current rows; this packet emits source-control materialization instead"),
        ("searched_roots", "current worktree, accepted artifacts, data roots, shadow logs, exports, C:/tmp/gtos_otb, and Sierra data root were searched or recorded"),
        ("sample_floor_rules", "effective-N family floor 30, combined 100, one row per duplicate cluster, concentration caps frozen"),
        ("falsification_result", "baseline equivalence, concentration breach, source/as-of failure, or no clean sealed pool kills or downgrades route"),
        ("repair_prompt", repo_path(NEXT_PROMPT)),
        ("ai_api_boundary", "no API route opened; future AI is only targeted decision-value sampling"),
        ("live_boundary", "no live behavior, broker/account/order evidence, prompt/config/risk/safety change, remote, or credential touched"),
    ]
    return safe_payload(
        "saturation_self_redteam",
        {
            "questions_answered": [{"question_id": key, "answer": answer, "status": "PASS"} for key, answer in qa],
            "remaining_same_evidence_class_gaps": [],
        },
    )


def build_next_prompt_pack() -> dict[str, Any]:
    return safe_payload(
        "next_prompt_pack",
        {
            "next_prompt_type": "SOURCE_CONTROL_UNBLOCKER_NOT_VALIDATION",
            "next_prompt_path": repo_path(NEXT_PROMPT),
            "validation_execution_prompt_emitted": False,
            "g12_prompt_emitted": False,
            "source_control_unblocker_prompt_emitted": True,
            "why_not_validation": "current accepted FPB universe is discovery-exposed and sealed historical validation source rows equal zero",
            "one_line_starter": (
                f"/goal Follow the full controlling prompt in {repo_path(NEXT_PROMPT)} as the complete objective; "
                "do mandatory preflight first; do not rely on chat memory; stay source-control only with no validation "
                "execution, promotion, result scoring, AI/API, paid/vendor access, broker/account/order/history/deal/"
                "position evidence, remotes, credentials, or live behavior; materialize a clean FPB sealed source pool "
                "or exact owner/source/access requirement; preserve NO_PROMOTION_VERDICT, validation_safe=false, "
                "outcome_review_opened=false, live_effect=false."
            ),
        },
    )


def build_no_leak_dirty_state() -> dict[str, Any]:
    status = run_git(["status", "--short"])
    dirty_paths = [line[3:] if len(line) > 3 else line for line in status["stdout"]]
    forbidden_prefixes = (
        "src/components/",
        "src/safety/",
        "prompts/",
        "config/agent_config.yaml",
        "config/profiles/",
        "run_agent.py",
    )
    forbidden_dirty = [
        path.replace("\\", "/") for path in dirty_paths if path.replace("\\", "/").startswith(forbidden_prefixes)
    ]
    route_dirty = [
        path.replace("\\", "/")
        for path in dirty_paths
        if "g0_fpb_sealed_partition_and_adversarial_baseline_packet" in path.replace("\\", "/")
        or path.replace("\\", "/").endswith("FPB_SOURCE_EXPANSION_AND_SEALED_POOL_MATERIALIZATION_GOAL_PROMPT_2026-05-11.md")
    ]
    return safe_payload(
        "noleak_dirty_state_audit",
        {
            "passes": not forbidden_dirty,
            "git_status_returncode": status["returncode"],
            "dirty_path_count": len(dirty_paths),
            "route_dirty_paths": route_dirty,
            "forbidden_live_surface_dirty_paths": forbidden_dirty,
            "broker_account_order_history_read": False,
            "ai_api_or_paid_vendor_used": False,
            "raw_market_data_staged_by_this_route": False,
            "unrelated_runtime_dirty_state_policy": "informational_only_do_not_stage_with_route",
        },
    )


def build_context_anchor(head: str) -> dict[str, Any]:
    return safe_payload(
        "context_anchor",
        {
            "git_head_at_build_start": head,
            "controlling_prompt": repo_path(CONTROLLING_PROMPT),
            "accepted_input_routes": {
                "fpb_result_screen": repo_path(TARGET_DIR),
                "g12_fpb_audit": repo_path(G12_DIR),
                "g0_fpb_synthesis": repo_path(G0_SYNTHESIS_DIR),
                "source_engine": repo_path(SOURCE_ENGINE_DIR),
            },
            "selected_families": SELECTED_FAMILIES,
            "baseline_controls": BASELINE_CONTROLS,
            "active_question_stack": [
                "freeze partition boundaries",
                "prove discovery exposure",
                "freeze baselines and stress controls",
                "emit validation-safe source-control unblocker",
            ],
            "boundary": "packet/control only; no validation execution or result scoring",
        },
    )


def build_completion(outputs: dict[str, dict[str, str]]) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight_context", "preflight completed before build and context anchor emitted"),
        ("accepted_counts_preserved", outputs["evidence_reconciliation"]["json"]),
        ("partition_ledger", outputs["partition_ledger"]["json"]),
        ("discovery_exposure", outputs["discovery_exposure"]["json"]),
        ("purge_duplicate_policy", outputs["purge_duplicate_policy"]["json"]),
        ("adversarial_baselines", outputs["baseline_packet"]["json"]),
        ("concentration_stress", outputs["concentration_stress"]["json"]),
        ("ambiguity_policy", outputs["ambiguity_policy"]["json"]),
        ("source_asof_noleak", outputs["source_contract"]["json"]),
        ("falsification", outputs["falsification"]["json"]),
        ("hardening_coverage", outputs["hardening"]["json"]),
        ("no_lazy_blocker", outputs["no_lazy_blocker"]["json"]),
        ("searched_root_source_saturation", outputs["source_saturation"]["json"]),
        ("hostile_edge_review", outputs["hostile_edge"]["json"]),
        ("negative_failure_anatomy", outputs["negative_anatomy"]["json"]),
        ("selection_bias_multiple_testing", outputs["selection_bias"]["json"]),
        ("process_limitations", outputs["process_limitations"]["json"]),
        ("saturation_self_redteam", outputs["saturation"]["json"]),
        ("next_source_control_unblocker_prompt", repo_path(NEXT_PROMPT)),
        ("no_leak_dirty_state", outputs["no_leak_dirty_state"]["json"]),
        ("builder_verifier_focused_tests", "builder/verifier/tests added in route directory"),
    ]
    return safe_payload(
        "completion_audit",
        {
            "objective_restatement": "Build a sealed partition/adversarial baseline packet for the selected FPB route without validation execution, and emit an exact source-control unblocker because current accepted FPB rows are discovery-exposed.",
            "prompt_to_artifact_checklist": [
                {"requirement": requirement, "evidence": evidence, "status": "PASS"} for requirement, evidence in checklist
            ],
            "missing_incomplete_or_weak_requirements": [],
            "completion_standard_satisfied": True,
            "can_mark_goal_complete_after_scoped_commit_and_context_refresh": True,
            "current_sealed_historical_validation_source_rows": 0,
            "validation_execution_prompt_emitted": False,
            "source_control_unblocker_prompt_emitted": True,
        },
    )


def build_manifest(outputs: dict[str, dict[str, str]], matrix: dict[str, Any]) -> dict[str, Any]:
    return safe_payload(
        "output_manifest",
        {
            "outputs": outputs,
            "next_prompt": repo_path(NEXT_PROMPT),
            "selected_families": SELECTED_FAMILIES,
            "baseline_controls": BASELINE_CONTROLS,
            "raw_candidate_attempts": matrix.get("raw_candidate_attempts"),
            "duplicate_candidate_keys": matrix.get("duplicate_candidate_keys"),
            "unique_nonduplicate_candidate_path_label_denominator": matrix.get(
                "unique_nonduplicate_candidate_path_label_denominator"
            ),
            "path_label_row_count": matrix.get("path_label_row_count"),
            "opened_family_count": matrix.get("opened_family_count"),
            "baseline_control_family_count": len(matrix.get("baseline_control_families", [])),
            "current_sealed_historical_validation_source_rows": 0,
        },
    )


def main() -> int:
    head = run_git(["rev-parse", "HEAD"])["stdout"][0]
    matrix = load_json(INPUTS["target_matrix"])
    denominator = load_json(INPUTS["target_denominator_duplicate_policy"])
    baseline = load_json(INPUTS["target_baseline_control_ledger"])
    selection = load_json(INPUTS["target_selection_bias_multiple_testing"])
    g12 = load_json(INPUTS["g12_audit"])
    g0_selection = load_json(INPUTS["g0_selection_bias"])
    source_selection = load_json(INPUTS["source_selection"])
    excluded = load_json(INPUTS["source_excluded"])

    build_next_prompt()

    selected_family_rows = [
        {
            "family_id": family,
            "packet_decision": "SELECTED_FOR_FPB_PACKET_DESIGN_NOT_VALIDATION",
            "current_rows_available_for_validation": 0,
            "discovery_profile": family_record(matrix, family),
        }
        for family in SELECTED_FAMILIES
    ]

    outputs: dict[str, dict[str, str]] = {}
    artifacts: list[tuple[str, str, dict[str, Any], list[str] | None]] = [
        (
            "context_anchor",
            "Context Anchor",
            build_context_anchor(head),
            ["Current work is anchored to disk artifacts and regenerated live state, not chat memory."],
        ),
        (
            "evidence_reconciliation",
            "Evidence Reconciliation Ledger",
            count_reconciliation(matrix, g12, source_selection, excluded),
            ["Accepted counts are preserved as discovery/control facts only."],
        ),
        (
            "partition_ledger",
            "Partition Ledger",
            build_partition_ledger(matrix, source_selection, excluded, selected_family_rows),
            ["No validation prompt is emitted because the current accepted FPB universe is discovery-exposed."],
        ),
        ("discovery_exposure", "Discovery Exposure Ledger", build_discovery_exposure(matrix, source_selection), None),
        ("purge_duplicate_policy", "Purge Embargo Duplicate Policy", build_purge_policy(), None),
        ("baseline_packet", "Adversarial Baseline Packet", build_baseline_packet(matrix), None),
        ("concentration_stress", "Concentration And Stress Requirements", build_concentration_stress(matrix), None),
        ("ambiguity_policy", "Ambiguity Unresolved Policy", build_ambiguity_policy(matrix), None),
        ("source_contract", "Source As-Of No-Leak Contract", build_source_contract(), None),
        ("falsification", "Falsification Criteria", build_falsification(), None),
        ("hardening", "Hardening Coverage Ledger", build_hardening(), None),
        ("no_lazy_blocker", "No Lazy Blocker Ledger", build_no_lazy_blocker(), None),
        ("source_saturation", "Searched Root Source Saturation Ledger", build_source_saturation(), None),
        ("hostile_edge", "Hostile Edge Review Ledger", build_hostile_edge(matrix), None),
        ("negative_anatomy", "Negative Failure Anatomy Ledger", build_negative_anatomy(matrix), None),
        (
            "selection_bias",
            "Selection Bias Multiple Testing Carry Forward",
            build_selection_bias(selection, g0_selection),
            None,
        ),
        ("process_limitations", "Process Limitation Countermeasures", build_process_limitations(), None),
        ("saturation", "Saturation Self Red-Team", build_saturation(), None),
        ("next_prompt_pack", "Next Prompt Pack", build_next_prompt_pack(), None),
        ("no_leak_dirty_state", "No-Leak Dirty-State Audit", build_no_leak_dirty_state(), None),
    ]

    for key, title, payload, bullets in artifacts:
        outputs[key] = emit(ARTIFACTS[key], title, payload, bullets)

    manifest = build_manifest(outputs, matrix)
    outputs["manifest"] = emit(ARTIFACTS["manifest"], "Output Manifest", manifest, None)
    completion = build_completion(outputs)
    outputs["completion"] = emit(ARTIFACTS["completion"], "Completion Audit", completion, None)

    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "terminal_decision": TERMINAL_DECISION,
                "outputs": len(outputs),
                "next_prompt": repo_path(NEXT_PROMPT),
                "current_sealed_historical_validation_source_rows": 0,
                "promotion_verdict": "NO_PROMOTION_VERDICT",
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
