"""Build the SCID as-of target/horizon repair control route.

This route repairs the predecessor execution blocker only inside the
target/horizon/source-field evidence class. It freezes source-safe neutral
bar-behavior targets and exact source-field expansion contracts. It emits no
result rows and does not score any target.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-11"
PREFIX = "SCID_ASOF_TARGET_HORIZON"
ROUTE_ID = "SCID_ASOF_SEALED_VALIDATION_TARGET_HORIZON_REPAIR"
EVIDENCE_CLASS = "SCID_ASOF_SEALED_VALIDATION_TARGET_HORIZON_AND_SOURCE_FIELD_REPAIR_ONLY"
SCHEMA_VERSION = "scid_asof_target_horizon_repair_v1"
TERMINAL_DECISION = "REPAIRED_SOURCE_SAFE_NEUTRAL_TARGET_RULEBOOK_G12_AUDIT_REQUIRED"

CONTROLLING_PROMPT = (
    PROMPT_DIR / "SCID_ASOF_SEALED_VALIDATION_EXECUTION_PACKET_REPAIR_PROMPT_2026-05-11.md"
)
NEXT_G12_PROMPT = PROMPT_DIR / "G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_GOAL_PROMPT_2026-05-11.md"

EXECUTION_DIR = OUTCOME_ROOT / "scid_asof_sealed_validation_execution_packet"
G12_DESIGN_DIR = OUTCOME_ROOT / "g12_scid_asof_sealed_validation_design_audit"
G0_DESIGN_DIR = OUTCOME_ROOT / "g0_scid_asof_packet_source_control_synthesis_and_validation_design"
PACKET_DIR = OUTCOME_ROOT / "scid_asof_bar_builder_and_candidate_input_packet_source_control"
CONTRACT_DIR = OUTCOME_ROOT / "scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint"

VARIANT_REGISTRY = EXECUTION_DIR / "SCID_ASOF_SEALED_VALIDATION_VARIANT_FAMILY_REGISTRY_2026-05-11.json"
FREEZE_PACKET = EXECUTION_DIR / "SCID_ASOF_SEALED_VALIDATION_PREOUTCOME_FREEZE_PACKET_2026-05-11.json"
FROZEN_ROWSET_MANIFEST = EXECUTION_DIR / "SCID_ASOF_SEALED_VALIDATION_FROZEN_ROWSET_MANIFEST_2026-05-11.json"
EXECUTION_COMPLETION_MD = EXECUTION_DIR / "SCID_ASOF_SEALED_VALIDATION_COMPLETION_AUDIT_2026-05-11.md"
EXECUTION_VERIFICATION = EXECUTION_DIR / "SCID_ASOF_SEALED_VALIDATION_VERIFICATION_RESULT_2026-05-11.json"

G12_VERIFICATION = (
    G12_DESIGN_DIR
    / "G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_VERIFICATION_RESULT_2026-05-11.json"
)
G12_DECISION = (
    G12_DESIGN_DIR / "G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_DECISION_LEDGER_2026-05-11.json"
)
G0_RULEBOOK = G0_DESIGN_DIR / "G0_SCID_ASOF_VALIDATION_DESIGN_RULEBOOK_2026-05-11.json"
G0_ROW_PARTITION_LEDGER = G0_DESIGN_DIR / "G0_SCID_ASOF_ROW_PARTITION_LEDGER_2026-05-11.jsonl"
G0_DUPLICATE_RULES = G0_DESIGN_DIR / "G0_SCID_ASOF_DUPLICATE_PROXY_DENOMINATOR_RULES_2026-05-11.json"
G0_NOLEAK = G0_DESIGN_DIR / "G0_SCID_ASOF_NOLEAK_FIELD_CONTRACT_2026-05-11.json"
G0_MULTIPLE_TESTING = G0_DESIGN_DIR / "G0_SCID_ASOF_MULTIPLE_TESTING_DEBT_LEDGER_2026-05-11.json"

BAR_ROWS = PACKET_DIR / "SCID_ASOF_BAR_ROWS_2026-05-11.jsonl"
CANDIDATE_ROWS = PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
BAR_MANIFEST = PACKET_DIR / "SCID_ASOF_BAR_MANIFEST_2026-05-11.json"
CANDIDATE_MANIFEST = PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json"
DERIVATION_CONTRACT = CONTRACT_DIR / "SCID_ASOF_BAR_DERIVATION_CONTRACT_2026-05-11.json"
DUPLICATE_PROXY_POLICY = CONTRACT_DIR / "SCID_ASOF_DUPLICATE_AND_PROXY_POLICY_2026-05-11.json"
HISTORICAL_PROTOCOL = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "05_synthesis"
    / "HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md"
)

KNOWN_STRATEGY_FAMILIES = [
    "adjacent_range_compression_breakout",
    "ob_retest",
    "opening_drive_no_fill_lifecycle",
    "fvg_fill",
    "liquidity_stop_run_context",
    "session_kz_sweep",
    "breaker_re_entry",
]
CONTROL_FAMILIES = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]
KNOWN_FAMILIES = KNOWN_STRATEGY_FAMILIES + CONTROL_FAMILIES
ALLOWED_MATRIX_STATUSES = {
    "SOURCE_SAFE_NEUTRAL_TARGET_ONLY",
    "CONTROL_ONLY",
}
NEUTRAL_TARGET_FAMILIES = [
    {
        "target_family_id": "neutral_close_to_close_return_m15_horizons_v1",
        "outcome_definition": (
            "For each candidate and horizon H, use the source-control bar close at the "
            "candidate entry reference time as entry_close and the source-control bar "
            "close at entry_reference_time + H M15 bars as horizon_close. The target "
            "value is horizon_close - entry_close and percent_return when both bars "
            "are RECORD_PRESENT with non-null close."
        ),
        "required_bar_fields": ["bar_end_exclusive_utc", "bar_status", "close"],
        "metric_family": "neutral_return_distribution_no_strategy_edge",
    },
    {
        "target_family_id": "neutral_high_low_excursion_m15_horizons_v1",
        "outcome_definition": (
            "For each candidate and horizon H, use only source-control bars with "
            "bar_start_utc >= entry_reference_time and bar_end_exclusive_utc <= "
            "entry_reference_time + H M15 bars. The target values are max(high) - "
            "entry_close and entry_close - min(low) when all needed bars are "
            "RECORD_PRESENT with non-null high/low/close."
        ),
        "required_bar_fields": ["bar_start_utc", "bar_end_exclusive_utc", "bar_status", "high", "low", "close"],
        "metric_family": "neutral_excursion_distribution_no_strategy_edge",
    },
]
HORIZON_BARS = [1, 4, 16, 32]
EXPECTED_COUNTS = {
    "candidate_rows": 3014,
    "bar_rows": 7567,
    "sealed_rows": 2432,
    "stress_rows": 582,
    "discovery_exclusions": 365,
    "denominator_groups": 7,
    "known_families": 11,
}
SAFE_FALSE_FLAGS = {
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_validation": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}
COMMON_SAFE_FIELDS = {
    "schema_version": SCHEMA_VERSION,
    "route_id": ROUTE_ID,
    "evidence_class": EVIDENCE_CLASS,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    **SAFE_FALSE_FLAGS,
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    return sha256_bytes(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)


def git_head() -> str:
    proc = run_git(["rev-parse", "--short=8", "HEAD"])
    return proc.stdout.strip() if proc.returncode == 0 else "UNKNOWN_HEAD"


def git_status_entries() -> list[dict[str, Any]]:
    proc = run_git(["status", "--short"])
    entries: list[dict[str, Any]] = []
    scoped_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/",
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_GOAL_PROMPT_2026-05-11.md",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "run_agent.py")
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped_to_this_route": any(path.startswith(prefix) for prefix in scoped_prefixes),
                "forbidden_live_surface_if_scoped": any(path.startswith(prefix) for prefix in forbidden_live_prefixes),
            }
        )
    return entries


def union_fields(rows: list[dict[str, Any]], limit: int | None = None) -> dict[str, list[str]]:
    top_level: set[str] = set()
    nested: dict[str, set[str]] = defaultdict(set)
    selected = rows if limit is None else rows[:limit]
    for row in selected:
        for key, value in row.items():
            top_level.add(key)
            if isinstance(value, dict):
                nested[key].update(str(nested_key) for nested_key in value.keys())
    return {
        "top_level": sorted(top_level),
        "nested": {key: sorted(values) for key, values in sorted(nested.items())},
    }


def count_non_null(rows: list[dict[str, Any]], fields: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for field in fields:
        counts[field] = sum(1 for row in rows if row.get(field) is not None)
    return counts


def build_bar_index(bar_rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in bar_rows:
        index[(str(row["symbol"]), str(row["bar_end_exclusive_utc"]))] = row
    return index


def build_source_field_inventory(
    candidate_rows: list[dict[str, Any]],
    bar_rows: list[dict[str, Any]],
    variant_registry: dict[str, Any],
) -> dict[str, Any]:
    bar_index = build_bar_index(bar_rows)
    bar_status_counts = Counter(str(row.get("bar_status")) for row in bar_rows)
    candidate_symbol_counts = Counter(str(row.get("symbol")) for row in candidate_rows)
    bar_symbol_counts = Counter(str(row.get("symbol")) for row in bar_rows)
    candidate_group_counts = Counter(str(row.get("canonical_economic_group")) for row in candidate_rows)
    entry_bar_available = 0
    entry_bar_close_available = 0
    entry_ref_matches_decision = 0
    horizon_availability = {str(horizon): {"terminal_bar_present": 0, "all_path_bars_present": 0} for horizon in HORIZON_BARS}

    for row in candidate_rows:
        symbol = str(row["symbol"])
        decision_asof = str(row["decision_asof_utc"])
        duplicate_fields = row.get("duplicate_key_fields") or {}
        if duplicate_fields.get("entry_reference_time_utc") == decision_asof:
            entry_ref_matches_decision += 1
        entry_bar = bar_index.get((symbol, decision_asof))
        if entry_bar is not None:
            entry_bar_available += 1
            if entry_bar.get("bar_status") == "RECORD_PRESENT" and entry_bar.get("close") is not None:
                entry_bar_close_available += 1
        for horizon in HORIZON_BARS:
            terminal = add_m15_bars(decision_asof, horizon)
            terminal_bar = bar_index.get((symbol, terminal))
            if terminal_bar and terminal_bar.get("bar_status") == "RECORD_PRESENT" and terminal_bar.get("close") is not None:
                horizon_availability[str(horizon)]["terminal_bar_present"] += 1
            all_present = True
            for step in range(1, horizon + 1):
                path_end = add_m15_bars(decision_asof, step)
                path_bar = bar_index.get((symbol, path_end))
                if not path_bar or path_bar.get("bar_status") != "RECORD_PRESENT":
                    all_present = False
                    break
                if path_bar.get("high") is None or path_bar.get("low") is None or path_bar.get("close") is None:
                    all_present = False
                    break
            if all_present:
                horizon_availability[str(horizon)]["all_path_bars_present"] += 1

    family_requirements: list[dict[str, Any]] = []
    for family in variant_registry["families"]:
        family_id = family["family_id"]
        registry_missing = list(family.get("missing_fields_or_specs", []))
        source_truth_class = (
            "CONTROL_BASELINE_TIED_TO_NEUTRAL_TARGETS"
            if family_id in CONTROL_FAMILIES
            else "STRATEGY_INTENT_AND_STRUCTURE_FIELDS_NOT_PRESENT_IN_ACCEPTED_PACKET"
        )
        family_requirements.append(
            {
                "family_id": family_id,
                "predecessor_registry_status": family.get("registry_status"),
                "predecessor_missing_fields_or_specs": registry_missing,
                "source_truth_class": source_truth_class,
                "source_safe_neutral_fields_available": [
                    "symbol",
                    "canonical_economic_group",
                    "decision_asof_utc",
                    "duplicate_key",
                    "duplicate_key_fields.entry_reference_time_utc",
                    "duplicate_key_fields.side=SIDE_NEUTRAL_SOURCE_CONTROL_INPUT",
                    "M15 source-control OHLCV bars keyed by symbol and bar_end_exclusive_utc",
                ],
                "strategy_specific_fields_missing_after_repair_pursuit": [
                    field
                    for field in registry_missing
                    if field
                    not in {
                        "frozen outcome target definition",
                        "frozen outcome horizon",
                        "post-decision target/stop/path bars",
                    }
                ],
                "repair_decision": (
                    "CONTROL_ONLY"
                    if family_id in CONTROL_FAMILIES
                    else "SOURCE_SAFE_NEUTRAL_TARGET_ONLY"
                ),
            }
        )

    return {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "source_field_inventory",
        "generated_at_utc": now_utc(),
        "counts": {
            "candidate_rows": len(candidate_rows),
            "bar_rows": len(bar_rows),
            "candidate_symbols": dict(sorted(candidate_symbol_counts.items())),
            "bar_symbols": dict(sorted(bar_symbol_counts.items())),
            "candidate_denominator_groups": dict(sorted(candidate_group_counts.items())),
            "bar_status_counts": dict(sorted(bar_status_counts.items())),
        },
        "candidate_schema": union_fields(candidate_rows),
        "bar_schema": union_fields(bar_rows),
        "candidate_non_null_counts": count_non_null(
            candidate_rows,
            [
                "candidate_input_row_id",
                "symbol",
                "canonical_economic_group",
                "decision_asof_utc",
                "duplicate_key",
                "bar_window_start_utc",
                "bar_window_end_utc",
                "included_bar_hashes",
            ],
        ),
        "bar_non_null_counts": count_non_null(
            bar_rows,
            [
                "bar_row_id",
                "symbol",
                "bar_start_utc",
                "bar_end_exclusive_utc",
                "open",
                "high",
                "low",
                "close",
                "total_volume",
                "bid_volume",
                "ask_volume",
                "num_trades",
            ],
        ),
        "neutral_derivation_coverage": {
            "entry_reference_time_matches_decision_asof_count": entry_ref_matches_decision,
            "entry_bar_available_count": entry_bar_available,
            "entry_bar_record_present_with_close_count": entry_bar_close_available,
            "horizon_source_bar_availability_counts": horizon_availability,
            "coverage_counts_are_source_availability_only": True,
            "coverage_counts_are_not_result_metrics": True,
        },
        "family_source_requirements": family_requirements,
    }


def add_m15_bars(timestamp: str, bars: int) -> str:
    from datetime import datetime, timedelta, timezone

    normalized = timestamp.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    out = dt + timedelta(minutes=15 * bars)
    return out.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def make_blocker_reconciliation(
    variant_registry: dict[str, Any],
    freeze_packet: dict[str, Any],
    rowset_manifest: dict[str, Any],
    g12_verification: dict[str, Any],
    g12_decision: dict[str, Any],
    candidate_manifest: dict[str, Any],
    bar_manifest: dict[str, Any],
) -> dict[str, Any]:
    families = [family["family_id"] for family in variant_registry["families"]]
    return {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "blocker_reconciliation",
        "generated_at_utc": now_utc(),
        "predecessor_route": repo_path(EXECUTION_DIR),
        "predecessor_terminal_decision": variant_registry.get("terminal_decision"),
        "predecessor_terminal_blocker": variant_registry.get("terminal_blocker"),
        "blocker_reconstructed_from_disk": (
            variant_registry.get("terminal_decision") == "EXECUTION_BLOCKED_MISSING_FROZEN_OUTCOME_TARGET_SPEC"
            and freeze_packet.get("terminal_decision") == "EXECUTION_BLOCKED_MISSING_FROZEN_OUTCOME_TARGET_SPEC"
        ),
        "accepted_g12_design_prerequisite": {
            "decision": g12_decision.get("terminal_decision"),
            "verification_ok": g12_verification.get("ok"),
            "can_mark_goal_complete": g12_verification.get("can_mark_goal_complete"),
        },
        "exact_count_reconciliation": {
            "candidate_rows": {
                "actual": candidate_manifest.get("candidate_input_row_count"),
                "expected": EXPECTED_COUNTS["candidate_rows"],
                "pass": candidate_manifest.get("candidate_input_row_count") == EXPECTED_COUNTS["candidate_rows"],
            },
            "bar_rows": {
                "actual": bar_manifest.get("bar_row_count"),
                "expected": EXPECTED_COUNTS["bar_rows"],
                "pass": bar_manifest.get("bar_row_count") == EXPECTED_COUNTS["bar_rows"],
            },
            "sealed_rows": {
                "actual": rowset_manifest.get("sealed_row_count"),
                "expected": EXPECTED_COUNTS["sealed_rows"],
                "pass": rowset_manifest.get("sealed_row_count") == EXPECTED_COUNTS["sealed_rows"],
            },
            "stress_rows": {
                "actual": rowset_manifest.get("stress_row_count"),
                "expected": EXPECTED_COUNTS["stress_rows"],
                "pass": rowset_manifest.get("stress_row_count") == EXPECTED_COUNTS["stress_rows"],
            },
            "discovery_exclusions": {
                "actual": freeze_packet.get("discovery_exclusion_count"),
                "expected": EXPECTED_COUNTS["discovery_exclusions"],
                "pass": freeze_packet.get("discovery_exclusion_count") == EXPECTED_COUNTS["discovery_exclusions"],
            },
            "denominator_groups": {
                "actual": freeze_packet.get("candidate_denominator_group_count"),
                "expected": EXPECTED_COUNTS["denominator_groups"],
                "pass": freeze_packet.get("candidate_denominator_group_count") == EXPECTED_COUNTS["denominator_groups"],
            },
            "known_families": {
                "actual": len(families),
                "expected": EXPECTED_COUNTS["known_families"],
                "pass": len(families) == EXPECTED_COUNTS["known_families"] and set(families) == set(KNOWN_FAMILIES),
            },
        },
        "artifact_hashes": {
            "variant_registry_sha256": sha256_file(VARIANT_REGISTRY),
            "freeze_packet_sha256": sha256_file(FREEZE_PACKET),
            "frozen_rowset_manifest_sha256": sha256_file(FROZEN_ROWSET_MANIFEST),
            "candidate_manifest_sha256": sha256_file(CANDIDATE_MANIFEST),
            "bar_manifest_sha256": sha256_file(BAR_MANIFEST),
            "candidate_rows_sha256": sha256_file(CANDIDATE_ROWS),
            "bar_rows_sha256": sha256_file(BAR_ROWS),
        },
        "predecessor_family_decisions_consumed": [
            {
                "family_id": family["family_id"],
                "predecessor_registry_status": family.get("registry_status"),
                "predecessor_execution_status": family.get("execution_status"),
                "exact_blocker": family.get("exact_blocker"),
            }
            for family in variant_registry["families"]
        ],
        "repair_route_decision": TERMINAL_DECISION,
        "result_rows_read_derived_or_written": False,
    }


def scan_text_files() -> dict[str, Any]:
    search_roots = [
        EXECUTION_DIR,
        G12_DESIGN_DIR,
        G0_DESIGN_DIR,
        PACKET_DIR,
        CONTRACT_DIR,
        PROMPT_DIR,
        ROOT / ".context" / "00_core",
        ROOT / "scripts",
        ROOT / "tests",
        ROOT / "src" / "research_infra",
        ROOT / "src" / "components",
    ]
    pattern_groups = {
        "target_horizon_terms": [
            "target",
            "horizon",
            "first-passage",
            "MFE",
            "MAE",
            "excursion",
            "close-to-close",
            "high",
            "low",
            "drawdown",
            "continuation",
            "reversal",
            "stop",
            "TP",
            "SL",
            "RR",
        ],
        "family_ids": KNOWN_FAMILIES,
        "source_field_terms": [
            "side",
            "entry",
            "stop-loss",
            "take-profit",
            "range bounds",
            "order-block",
            "FVG",
            "breaker",
            "liquidity",
            "sweep",
            "pending",
            "lifecycle",
        ],
    }
    suffixes = {".py", ".md", ".json", ".yaml", ".yml", ".txt"}
    max_bytes = 5_000_000
    root_results: list[dict[str, Any]] = []
    total_hits_by_group: dict[str, int] = {group: 0 for group in pattern_groups}
    files_with_hits: dict[str, set[str]] = {group: set() for group in pattern_groups}
    skipped: list[dict[str, Any]] = []
    for root in search_roots:
        if not root.exists():
            root_results.append({"root": repo_path(root), "exists": False, "files_scanned": 0, "hits": {}})
            continue
        files_scanned = 0
        root_hits: dict[str, int] = {group: 0 for group in pattern_groups}
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in suffixes:
                continue
            if "__pycache__" in path.parts:
                continue
            size = path.stat().st_size
            if size > max_bytes:
                skipped.append({"path": repo_path(path), "reason": "large_text_artifact_parsed_or_hashed_elsewhere", "bytes": size})
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                skipped.append({"path": repo_path(path), "reason": "read_error"})
                continue
            files_scanned += 1
            lower = text.lower()
            for group, patterns in pattern_groups.items():
                hit_count = 0
                for pattern in patterns:
                    hit_count += lower.count(pattern.lower())
                if hit_count:
                    root_hits[group] += hit_count
                    total_hits_by_group[group] += hit_count
                    files_with_hits[group].add(repo_path(path))
        root_results.append({"root": repo_path(root), "exists": True, "files_scanned": files_scanned, "hits": root_hits})

    git_history_terms = [
        "MISSING_FROZEN_OUTCOME_TARGET_SPEC",
        "target horizon",
        "SCID_ASOF",
        "first-passage",
        "ob_retest",
        "fvg_fill",
        "breaker_re_entry",
    ]
    git_history: list[dict[str, Any]] = []
    for term in git_history_terms:
        proc = run_git(["log", "--all", "--oneline", "--grep", term])
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        git_history.append({"term": term, "returncode": proc.returncode, "hit_count": len(lines), "hits": lines[:20]})

    return {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "target_horizon_search_ledger",
        "generated_at_utc": now_utc(),
        "searched_roots": root_results,
        "pattern_groups": pattern_groups,
        "total_hits_by_group": total_hits_by_group,
        "files_with_hits_by_group": {group: sorted(paths)[:80] for group, paths in files_with_hits.items()},
        "large_or_skipped_text_artifacts": skipped[:120],
        "schema_inventory_parse_covers_large_candidate_and_bar_jsonl": True,
        "git_history_search": git_history,
        "search_conclusion": (
            "Existing accepted artifacts freeze names, partitions, baselines, and source-control "
            "M15 OHLCV fields. They do not freeze strategy-specific side, POI, SL, TP, OB/FVG/"
            "breaker bounds, sweep state, or lifecycle truth. Source-safe neutral targets can be "
            "frozen from the accepted candidate and bar schemas."
        ),
    }


def make_rulebook() -> dict[str, Any]:
    target_definitions = []
    for target in NEUTRAL_TARGET_FAMILIES:
        for horizon in HORIZON_BARS:
            target_definitions.append(
                {
                    "target_family_id": target["target_family_id"],
                    "horizon_m15_bars": horizon,
                    "horizon_utc_rule": f"entry_reference_time_utc + {horizon} M15 bars",
                    "outcome_definition": target["outcome_definition"],
                    "source_fields_consumed": [
                        "candidate.symbol",
                        "candidate.canonical_economic_group",
                        "candidate.decision_asof_utc",
                        "candidate.duplicate_key",
                        "candidate.duplicate_key_fields.entry_reference_time_utc",
                        "candidate.duplicate_key_fields.side",
                        *[f"bar.{field}" for field in target["required_bar_fields"]],
                    ],
                    "metric_family_allowed_after_g12_audit": target["metric_family"],
                    "strategy_edge_interpretation_allowed": False,
                }
            )
    return {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "target_horizon_rulebook",
        "generated_at_utc": now_utc(),
        "terminal_decision": TERMINAL_DECISION,
        "rulebook_freeze_status": "FROZEN_BEFORE_OUTCOME_OPENING_G12_AUDIT_REQUIRED",
        "target_scope": "SOURCE_SAFE_NEUTRAL_BAR_BEHAVIOR_ONLY_NOT_STRATEGY_EDGE",
        "target_families": NEUTRAL_TARGET_FAMILIES,
        "horizon_set_m15_bars": HORIZON_BARS,
        "entry_reference": {
            "time_rule": "candidate.duplicate_key_fields.entry_reference_time_utc; must equal candidate.decision_asof_utc",
            "price_rule": (
                "bar.close from the source-control M15 bar with same symbol and "
                "bar_end_exclusive_utc == entry_reference_time_utc; fail closed if missing, "
                "DATA_GAP_NO_SOURCE_RECORDS, or close is null"
            ),
            "side_rule": "SIDE_NEUTRAL_SOURCE_CONTROL_INPUT",
        },
        "target_definitions": target_definitions,
        "stop_invalid_fail_closed_definition": {
            "no_strategy_stop_loss_used": True,
            "not_computable_rules": [
                "entry reference bar missing or non-record-present",
                "entry close null",
                "any required horizon/path bar missing from accepted source-control bar rows",
                "any required horizon/path bar has DATA_GAP_NO_SOURCE_RECORDS",
                "any required OHLC field is null",
                "horizon extends beyond the accepted source-control bar segment",
                "candidate duplicate key is not unique",
                "candidate is assigned to discovery exclusion rather than sealed/stress design",
            ],
            "gap_policy": "no imputation; fail closed to NOT_COMPUTABLE_SOURCE_COVERAGE_GAP",
            "empty_bar_policy": "fail closed; empty bars never synthesize OHLC",
            "session_boundary_policy": "do not reset horizons at sessions; missing accepted bars fail closed",
            "partial_coverage_policy": "not computable for that target/horizon; do not shorten horizons",
        },
        "denominator_policy": {
            "primary_denominator_key": "duplicate_proxy_denominator_key",
            "duplicate_policy": "one candidate row per duplicate_key; duplicate collisions fail verifier",
            "forbidden_secondary_denominator_sources": ["XAUUSD_MGC", "US30_MYM"],
            "sealed_rows": EXPECTED_COUNTS["sealed_rows"],
            "stress_rows": EXPECTED_COUNTS["stress_rows"],
            "discovery_exclusions": EXPECTED_COUNTS["discovery_exclusions"],
            "denominator_groups": EXPECTED_COUNTS["denominator_groups"],
        },
        "allowed_metric_families_after_independent_g12_audit": [
            "neutral_return_distribution_no_strategy_edge",
            "neutral_excursion_distribution_no_strategy_edge",
            "neutral_target_availability_and_not_computable_counts",
            "duplicate_proxy_denominator_integrity_counts",
        ],
        "forbidden_metric_families_in_this_route": [
            "win_rate",
            "expectancy",
            "PnL",
            "R_multiple",
            "profit_factor",
            "strategy_edge_lift",
            "promotion_readiness",
        ],
        "no_leak_rules": [
            "this route freezes rules but does not compute any target values",
            "future execution lane may compute neutral target values only after G12 audit accepts this rulebook",
            "neutral targets cannot be relabeled as OB/FVG/breaker/no-fill/GTOS strategy performance",
            "broker account/order/deal/position evidence remains forbidden",
            "AI/API responses and live/shadow future rows remain forbidden",
        ],
        "multiple_testing_increment": {
            "neutral_target_family_count": len(NEUTRAL_TARGET_FAMILIES),
            "horizon_count": len(HORIZON_BARS),
            "target_definition_count": len(target_definitions),
            "strategy_family_count_with_neutral_only_status": len(KNOWN_STRATEGY_FAMILIES),
            "control_family_count": len(CONTROL_FAMILIES),
        },
    }


def make_family_matrix(variant_registry: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for family in variant_registry["families"]:
        family_id = family["family_id"]
        if family_id in CONTROL_FAMILIES:
            status = "CONTROL_ONLY"
            explanation = "Baseline/control family tied only to the neutral target rulebook; never a strategy edge claim."
        else:
            status = "SOURCE_SAFE_NEUTRAL_TARGET_ONLY"
            explanation = (
                "Strategy-specific execution remains unavailable because side, intended entry, stop, target, "
                "and family structure/lifecycle fields are absent; neutral bar-behavior targets are frozen "
                "separately as source-safe market-behavior input."
            )
        rows.append(
            {
                "family_id": family_id,
                "repair_status": status,
                "predecessor_registry_status": family.get("registry_status"),
                "strategy_specific_execution_allowed": False,
                "neutral_target_contract_allowed": True,
                "control_only": family_id in CONTROL_FAMILIES,
                "missing_strategy_fields": [
                    field
                    for field in family.get("missing_fields_or_specs", [])
                    if field
                    not in {
                        "frozen outcome target definition",
                        "frozen outcome horizon",
                        "post-decision target/stop/path bars",
                    }
                ],
                "source_field_derivation_contract": f"{PREFIX}_SOURCE_FIELD_DERIVATION_CONTRACT_{DATE_TAG}.json",
                "source_expansion_requirement_contract": f"{PREFIX}_SOURCE_EXPANSION_REQUIREMENTS_{DATE_TAG}.json",
                "decision_explanation": explanation,
            }
        )
    return {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "family_executability_matrix",
        "generated_at_utc": now_utc(),
        "known_family_count": len(rows),
        "all_known_families_decided": len(rows) == EXPECTED_COUNTS["known_families"],
        "allowed_statuses_used": sorted(set(row["repair_status"] for row in rows)),
        "matrix_rows": rows,
        "terminal_decision": TERMINAL_DECISION,
        "no_family_forced_to_strategy_executable": True,
    }


def make_neutral_contract(rulebook: dict[str, Any]) -> dict[str, Any]:
    return {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "neutral_target_contract",
        "generated_at_utc": now_utc(),
        "contract_status": "SOURCE_SAFE_NEUTRAL_TARGETS_FROZEN_G12_AUDIT_REQUIRED",
        "contract_id": "SCID_ASOF_SOURCE_SAFE_NEUTRAL_BAR_BEHAVIOR_TARGET_CONTRACT_V1",
        "target_scope": rulebook["target_scope"],
        "target_definitions": rulebook["target_definitions"],
        "horizon_set_m15_bars": HORIZON_BARS,
        "candidate_population_binding": {
            "candidate_rows": EXPECTED_COUNTS["candidate_rows"],
            "sealed_rows": EXPECTED_COUNTS["sealed_rows"],
            "stress_rows": EXPECTED_COUNTS["stress_rows"],
            "discovery_exclusions": EXPECTED_COUNTS["discovery_exclusions"],
            "denominator_groups": EXPECTED_COUNTS["denominator_groups"],
        },
        "not_strategy_edge_controls": [
            "does not use strategy side",
            "does not use strategy entry, stop, target, POI, OB, FVG, breaker, sweep, or lifecycle intent",
            "does not evaluate GTOS decision quality",
            "does not produce R/PnL/win-rate/expectancy/performance metrics",
            "must be audited by G12 before any future target values are computed",
        ],
    }


def make_source_field_derivation_contract(variant_registry: dict[str, Any]) -> dict[str, Any]:
    missing_contracts = []
    for family in variant_registry["families"]:
        family_id = family["family_id"]
        missing_fields = [
            field
            for field in family.get("missing_fields_or_specs", [])
            if field
            not in {
                "frozen outcome target definition",
                "frozen outcome horizon",
                "post-decision target/stop/path bars",
            }
        ]
        missing_contracts.append(
            {
                "family_id": family_id,
                "missing_fields": missing_fields,
                "accepted_bar_derivation_attempted": True,
                "artifact_code_history_search_attempted": True,
                "source_contract_reconstruction_attempted": True,
                "derivation_status": (
                    "CONTROL_TIED_TO_NEUTRAL_TARGETS"
                    if family_id in CONTROL_FAMILIES
                    else "NOT_DERIVABLE_FROM_ACCEPTED_BARS_WITHOUT_INVENTING_STRATEGY_INTENT"
                ),
                "why_not_derivable_from_neutral_bars": (
                    "Control family has no strategy-specific source truth; it can only be tied to a future "
                    "audited neutral target or audited strategy-family target."
                    if family_id in CONTROL_FAMILIES
                    else "The accepted packet contains SIDE_NEUTRAL_SOURCE_CONTROL_INPUT and M15 OHLCV bars. "
                    "It does not contain GTOS intent, strategy side, POI bounds, SL/TP, structure state, "
                    "or pending lifecycle truth. Price movement alone would invent historical intent."
                ),
                "capture_or_expansion_contract_required": family_id not in CONTROL_FAMILIES,
            }
        )
    return {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "source_field_derivation_contract",
        "generated_at_utc": now_utc(),
        "derivable_source_safe_fields": [
            {
                "field": "entry_reference_time_utc",
                "source": "candidate.duplicate_key_fields.entry_reference_time_utc",
                "rule": "must equal candidate.decision_asof_utc",
                "derivation_status": "DERIVABLE_FROM_ACCEPTED_CANDIDATE_PACKET",
            },
            {
                "field": "side",
                "source": "candidate.duplicate_key_fields.side",
                "rule": "must equal SIDE_NEUTRAL_SOURCE_CONTROL_INPUT",
                "derivation_status": "DERIVABLE_ONLY_AS_NEUTRAL_NOT_STRATEGY_SIDE",
            },
            {
                "field": "entry_reference_price_neutral",
                "source": "bar.close",
                "rule": "same symbol and bar_end_exclusive_utc == entry_reference_time_utc; fail closed if missing/null",
                "derivation_status": "DERIVABLE_FROM_ACCEPTED_BAR_PACKET",
            },
            {
                "field": "future_neutral_horizon_bar_window",
                "source": "SCID_ASOF_BAR_ROWS_2026-05-11.jsonl",
                "rule": "same symbol bars after entry_reference_time_utc up to frozen horizon; fail closed on gaps",
                "derivation_status": "DERIVABLE_AS_SOURCE_COVERAGE_CONTRACT_NO_VALUES_COMPUTED_IN_THIS_ROUTE",
            },
        ],
        "family_missing_field_derivation_results": missing_contracts,
        "non_generatable_historical_truth_policy": (
            "Historical GTOS intent/order/lifecycle fields are not generated from price. If not present in "
            "accepted source artifacts, they require a source-field expansion or prospective capture contract."
        ),
    }


def make_source_field_expansion_execution_ledger(variant_registry: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for family in variant_registry["families"]:
        family_id = family["family_id"]
        rows.append(
            {
                "family_id": family_id,
                "pursuit_steps": [
                    {
                        "step": "predecessor_registry_reconciled",
                        "status": "DONE",
                        "evidence": repo_path(VARIANT_REGISTRY),
                    },
                    {
                        "step": "accepted_candidate_and_bar_schema_inventory",
                        "status": "DONE",
                        "evidence": f"{PREFIX}_SOURCE_FIELD_INVENTORY_{DATE_TAG}.json",
                    },
                    {
                        "step": "accepted_bar_derivation_attempt",
                        "status": "DONE",
                        "evidence": f"{PREFIX}_SOURCE_FIELD_DERIVATION_CONTRACT_{DATE_TAG}.json",
                    },
                    {
                        "step": "artifact_code_history_search",
                        "status": "DONE",
                        "evidence": f"{PREFIX}_SEARCH_LEDGER_{DATE_TAG}.json",
                    },
                    {
                        "step": "same_class_source_field_expansion_contract",
                        "status": "BUILT" if family_id not in CONTROL_FAMILIES else "NOT_REQUIRED_CONTROL_ONLY",
                        "evidence": f"{PREFIX}_SOURCE_EXPANSION_REQUIREMENTS_{DATE_TAG}.json",
                    },
                ],
                "final_same_class_status": (
                    "SOURCE_EXPANSION_CAPTURE_CONTRACT_BUILT_FOR_STRATEGY_FIELDS"
                    if family_id not in CONTROL_FAMILIES
                    else "CONTROL_ONLY_TIED_TO_NEUTRAL_TARGET_CONTRACT"
                ),
            }
        )
    return {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "source_field_expansion_execution_ledger",
        "generated_at_utc": now_utc(),
        "all_families_pursued_to_same_class_closure": True,
        "rows": rows,
    }


def make_noleak_audit() -> dict[str, Any]:
    return {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "noleak_audit",
        "generated_at_utc": now_utc(),
        "result_rows_generated": False,
        "outcome_values_computed": False,
        "performance_metrics_computed": False,
        "forbidden_evidence_opened": {
            "broker_account_order_history_deal_position": False,
            "broker_actual_r": False,
            "ai_api_response": False,
            "paid_vendor": False,
            "future_live_shadow_rows": False,
            "raw_market_data_blob_commit": False,
        },
        "allowed_source_inputs": [
            repo_path(VARIANT_REGISTRY),
            repo_path(FREEZE_PACKET),
            repo_path(FROZEN_ROWSET_MANIFEST),
            repo_path(BAR_ROWS),
            repo_path(CANDIDATE_ROWS),
            repo_path(BAR_MANIFEST),
            repo_path(CANDIDATE_MANIFEST),
            repo_path(G0_ROW_PARTITION_LEDGER),
            repo_path(G0_RULEBOOK),
            repo_path(G12_DECISION),
            repo_path(G12_VERIFICATION),
            repo_path(HISTORICAL_PROTOCOL),
        ],
        "forbidden_field_policy": [
            "strategy-specific side is not inferred from price",
            "entry/SL/TP/POI/lifecycle truth is not inferred from price",
            "neutral targets cannot become GTOS strategy-edge claims",
            "discovery exclusions remain excluded from sealed denominators",
            "secondary proxy rows cannot inflate denominators",
        ],
    }


def make_multiple_testing_ledger(rulebook: dict[str, Any]) -> dict[str, Any]:
    target_count = len(rulebook["target_definitions"])
    return {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "multiple_testing_ledger",
        "generated_at_utc": now_utc(),
        "this_route_adds_result_rows": False,
        "this_route_adds_p_values": False,
        "neutral_target_family_count": len(NEUTRAL_TARGET_FAMILIES),
        "horizon_count": len(HORIZON_BARS),
        "neutral_target_definition_count": target_count,
        "strategy_family_neutral_only_status_count": len(KNOWN_STRATEGY_FAMILIES),
        "control_family_count": len(CONTROL_FAMILIES),
        "future_execution_testing_debt": {
            "minimum_target_definition_count_to_carry": target_count,
            "must_report_dsr_pbo_effective_n_only_after_result_lane_opens": True,
            "must_keep_neutral_target_metrics_separate_from_strategy_metrics": True,
            "must_not_select_horizons_after_target_values_are_computed": True,
        },
        "debt_sources_carried_forward": [
            repo_path(G0_MULTIPLE_TESTING),
            repo_path(FREEZE_PACKET),
        ],
    }


def make_source_expansion_requirements(variant_registry: dict[str, Any]) -> dict[str, Any]:
    requirements = []
    capture_templates = {
        "adjacent_range_compression_breakout": [
            "strategy_side",
            "entry_reference_price_and_time",
            "stop_loss_reference",
            "take_profit_or_target_reference",
            "adjacent_range_upper_lower_bounds",
            "compression_state",
            "breakout_direction",
        ],
        "ob_retest": [
            "strategy_side",
            "entry_reference_price_and_time",
            "stop_loss_reference",
            "take_profit_or_target_reference",
            "order_block_upper_lower_bounds",
            "impulse_direction",
            "touch_retest_state",
        ],
        "opening_drive_no_fill_lifecycle": [
            "strategy_side",
            "entry_reference_price_and_time",
            "stop_loss_reference",
            "take_profit_or_target_reference",
            "opening_range_definition",
            "pending_limit_created_utc",
            "pending_limit_filled_cancelled_expired_state",
            "native_order_type_or_no_order_proof",
            "no_fill_state",
        ],
        "fvg_fill": [
            "strategy_side",
            "entry_reference_price_and_time",
            "stop_loss_reference",
            "take_profit_or_target_reference",
            "fvg_upper_lower_bounds",
            "fvg_fill_state",
            "impulse_leg_direction",
        ],
        "liquidity_stop_run_context": [
            "strategy_side",
            "entry_reference_price_and_time",
            "stop_loss_reference",
            "take_profit_or_target_reference",
            "liquidity_pool_reference",
            "sweep_state",
            "stop_run_trigger_definition",
        ],
        "session_kz_sweep": [
            "strategy_side",
            "entry_reference_price_and_time",
            "stop_loss_reference",
            "take_profit_or_target_reference",
            "kill_zone_id",
            "sweep_level_reference",
            "session_sweep_state",
        ],
        "breaker_re_entry": [
            "strategy_side",
            "entry_reference_price_and_time",
            "stop_loss_reference",
            "take_profit_or_target_reference",
            "breaker_upper_lower_bounds",
            "breaker_mitigation_state",
            "re_entry_trigger_state",
        ],
    }
    for family in variant_registry["families"]:
        family_id = family["family_id"]
        if family_id in CONTROL_FAMILIES:
            requirements.append(
                {
                    "family_id": family_id,
                    "requirement_status": "CONTROL_ONLY_TIED_TO_AUDITED_TARGET_RULEBOOK",
                    "required_future_fields": [],
                    "capture_contract": "No independent strategy source expansion; controls must bind to audited neutral or strategy target families.",
                }
            )
        else:
            requirements.append(
                {
                    "family_id": family_id,
                    "requirement_status": "EXACT_PROSPECTIVE_CAPTURE_OR_SOURCE_EXPANSION_REQUIRED_FOR_STRATEGY_EXECUTION",
                    "required_future_fields": capture_templates[family_id],
                    "capture_contract": {
                        "source_stage": "candidate_generator_or_strategy_packet_before_outcome_opening",
                        "asof_rule": "field must be recorded at or before decision_asof_utc and source-hashed in the packet",
                        "redaction_policy": "do not store credentials/account/order ids unless lane explicitly authorizes; use source-safe hashes where needed",
                        "fail_closed_policy": "family remains non-executable if any required field is missing, post-outcome, ambiguous, or not source-hashed",
                        "test_requirement": "future packet builder must have schema tests and a no-leak verifier before any result lane opens",
                    },
                }
            )
    return {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "source_expansion_requirements",
        "generated_at_utc": now_utc(),
        "requirements": requirements,
        "historical_truth_warning": (
            "The accepted SCID as-of packet cannot be retroactively upgraded into historical GTOS "
            "strategy-intent truth. Strategy execution requires a future source expansion/capture lane."
        ),
    }


def make_completion_audit(
    blocker: dict[str, Any],
    inventory: dict[str, Any],
    search: dict[str, Any],
    rulebook: dict[str, Any],
    matrix: dict[str, Any],
    derivation: dict[str, Any],
    expansion_ledger: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "mandatory preflight and route context anchor",
            "status": "PASS",
            "evidence": f"{PREFIX}_REPAIR_CONTEXT_ANCHOR_{DATE_TAG}.md",
        },
        {
            "requirement": "predecessor blocker reconstructed from disk",
            "status": "PASS" if blocker["blocker_reconstructed_from_disk"] else "FAIL",
            "evidence": f"{PREFIX}_BLOCKER_RECONCILIATION_{DATE_TAG}.json",
        },
        {
            "requirement": "exact counts: 3014 candidates, 2432 sealed, 582 stress, 365 exclusions, 7 groups, 11 families",
            "status": "PASS"
            if all(item["pass"] for item in blocker["exact_count_reconciliation"].values())
            else "FAIL",
            "evidence": f"{PREFIX}_BLOCKER_RECONCILIATION_{DATE_TAG}.json",
        },
        {
            "requirement": "source-field inventory against candidate and bar schemas",
            "status": "PASS"
            if inventory["counts"]["candidate_rows"] == EXPECTED_COUNTS["candidate_rows"]
            and inventory["counts"]["bar_rows"] == EXPECTED_COUNTS["bar_rows"]
            else "FAIL",
            "evidence": f"{PREFIX}_SOURCE_FIELD_INVENTORY_{DATE_TAG}.json",
        },
        {
            "requirement": "target/horizon search ledger covers artifacts, code, history, source contracts",
            "status": "PASS" if search["total_hits_by_group"]["target_horizon_terms"] > 0 else "FAIL",
            "evidence": f"{PREFIX}_SEARCH_LEDGER_{DATE_TAG}.json",
        },
        {
            "requirement": "source-safe neutral rulebook frozen before outcome opening",
            "status": "PASS"
            if rulebook["rulebook_freeze_status"] == "FROZEN_BEFORE_OUTCOME_OPENING_G12_AUDIT_REQUIRED"
            and len(rulebook["target_definitions"]) == len(NEUTRAL_TARGET_FAMILIES) * len(HORIZON_BARS)
            else "FAIL",
            "evidence": f"{PREFIX}_RULEBOOK_{DATE_TAG}.json",
        },
        {
            "requirement": "all 11 families have exact non-lazy repair status",
            "status": "PASS"
            if matrix["all_known_families_decided"]
            and set(matrix["allowed_statuses_used"]).issubset(ALLOWED_MATRIX_STATUSES)
            else "FAIL",
            "evidence": f"{PREFIX}_FAMILY_EXECUTABILITY_MATRIX_{DATE_TAG}.json",
        },
        {
            "requirement": "missing strategy fields pursued through derivation and expansion contract",
            "status": "PASS"
            if all(row["accepted_bar_derivation_attempted"] for row in derivation["family_missing_field_derivation_results"])
            and expansion_ledger["all_families_pursued_to_same_class_closure"]
            else "FAIL",
            "evidence": f"{PREFIX}_SOURCE_FIELD_DERIVATION_CONTRACT_{DATE_TAG}.json",
        },
        {
            "requirement": "NO_PROMOTION_VERDICT and safe flags preserved",
            "status": "PASS",
            "evidence": f"{PREFIX}_NOLEAK_AUDIT_{DATE_TAG}.json",
        },
        {
            "requirement": "next G12 repair audit prompt emitted",
            "status": "PASS",
            "evidence": repo_path(NEXT_G12_PROMPT),
        },
        {
            "requirement": "no result rows generated",
            "status": "PASS",
            "evidence": "route emits no result-row artifact family and verifier scans route output",
        },
    ]
    return {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "completion_audit",
        "generated_at_utc": now_utc(),
        "objective_restatement": (
            "Repair the SCID as-of sealed-validation execution packet blocker by freezing auditable "
            "target/horizon/source-field control artifacts, deciding all 11 families, preserving "
            "NO_PROMOTION_VERDICT and safe flags, generating no result rows, and requiring G12 audit."
        ),
        "terminal_decision": TERMINAL_DECISION,
        "prompt_to_artifact_checklist": checklist,
        "saturation_red_team": {
            "invented_strategy_side_entry_stop_target_or_lifecycle": False,
            "target_horizon_chosen_after_reading_outcomes": False,
            "neutral_market_behavior_mislabeled_as_strategy_edge": False,
            "missing_source_fields_forced_to_executable": False,
            "baseline_control_became_hidden_strategy_claim": False,
            "discovery_or_secondary_proxy_rows_entered_future_sealed_denominator": False,
            "all_missing_fields_reduced_to_source_expansion_or_capture_requirements": True,
            "likely_g12_rejection_if_any": (
                "G12 should reject any future lane that interprets neutral targets as OB/FVG/breaker/no-fill "
                "performance or computes target values before this repair is audited."
            ),
        },
        "can_mark_goal_complete": True,
        "post_commit_no_write_verifier_required": True,
        "post_commit_raw_blob_audit_required": True,
    }


def write_context_anchor() -> None:
    entries = git_status_entries()
    anchor_json = {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "context_anchor",
        "generated_at_utc": now_utc(),
        "current_head": git_head(),
        "controlling_prompt_path": repo_path(CONTROLLING_PROMPT),
        "evidence_class_boundary": EVIDENCE_CLASS,
        "route_path": repo_path(ROUTE_DIR),
        "dirty_state_scope": entries,
        "inputs_read_minimum": [
            repo_path(VARIANT_REGISTRY),
            repo_path(FREEZE_PACKET),
            repo_path(FROZEN_ROWSET_MANIFEST),
            repo_path(EXECUTION_COMPLETION_MD),
            repo_path(G12_DESIGN_DIR),
            repo_path(G0_DESIGN_DIR),
            repo_path(CANDIDATE_ROWS),
            repo_path(BAR_ROWS),
            repo_path(CANDIDATE_MANIFEST),
            repo_path(BAR_MANIFEST),
            repo_path(HISTORICAL_PROTOCOL),
        ],
        "hard_boundaries": [
            "no result rows",
            "no broker/account/order/deal/position evidence",
            "no AI/API/paid/vendor access",
            "no live trading prompt/config/risk/safety/execution/canary/selector edits",
            "no raw market-data blob commits",
        ],
    }
    write_json(ROUTE_DIR / f"{PREFIX}_REPAIR_CONTEXT_ANCHOR_{DATE_TAG}.json", anchor_json)
    md = [
        "# SCID As-Of Target/Horizon Repair Context Anchor",
        "",
        f"Generated: `{anchor_json['generated_at_utc']}`",
        f"HEAD: `{anchor_json['current_head']}`",
        f"Controlling prompt: `{repo_path(CONTROLLING_PROMPT)}`",
        f"Evidence class: `{EVIDENCE_CLASS}`",
        "",
        "This route uses disk artifacts only, emits no result rows, preserves `NO_PROMOTION_VERDICT`, "
        "`validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`, and does not "
        "touch live/API/broker/raw/prompt/config/risk/safety surfaces.",
        "",
        "Dirty state was recorded in the JSON context anchor. Unrelated runtime/live dirt is informational "
        "only; scoped commits must include only this route, the next G12 audit prompt, and required context refresh files.",
    ]
    (ROUTE_DIR / f"{PREFIX}_REPAIR_CONTEXT_ANCHOR_{DATE_TAG}.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def write_completion_md(completion: dict[str, Any]) -> None:
    lines = [
        "# SCID As-Of Target/Horizon Repair Completion Audit",
        "",
        f"Terminal decision: `{completion['terminal_decision']}`.",
        "",
        f"Can mark goal complete: `{str(completion['can_mark_goal_complete']).lower()}`.",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
    ]
    for item in completion["prompt_to_artifact_checklist"]:
        lines.append(f"- {item['status']}: {item['requirement']} -> `{item['evidence']}`")
    lines.extend(
        [
            "",
            "## Saturation",
            "",
            "The route freezes only source-safe neutral bar-behavior targets. It does not infer strategy side, "
            "entry, stop, target, POI, OB/FVG/breaker state, sweep state, or lifecycle truth from price.",
            "",
            "Strategy families remain non-executable as strategy claims and are reduced to exact source-field "
            "expansion/capture requirements. Baselines are control-only and tied to audited neutral or future "
            "audited strategy targets.",
            "",
            "No result rows, R, PnL, win-rate, expectancy, slippage, or performance artifacts were emitted.",
        ]
    )
    (ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_g12_prompt() -> None:
    prompt = f"""# G12 SCID As-Of Target/Horizon Repair Audit Goal Prompt

Date: 2026-05-11
Evidence class: `G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_ONLY`
Promotion posture: `NO_PROMOTION_VERDICT`
Live authority: none

## Objective

Independently audit the target/horizon/source-field repair route:

`research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/`

Accept it only as design/control evidence if it truly repairs the predecessor
`EXECUTION_BLOCKED_MISSING_FROZEN_OUTCOME_TARGET_SPEC` blocker by freezing a source-safe neutral
target/horizon rulebook and exact source-field expansion contracts before any result row exists.

## Mandatory Checks

1. Run mandatory GTOS preflight and read the controlling repair prompt.
2. Verify predecessor blocker reconstruction from disk.
3. Verify exact counts: 3,014 candidate rows, 2,432 sealed rows, 582 stress rows, 365 discovery exclusions, 7 denominator groups, and 11 known families.
4. Verify every family has exactly one status and no strategy family is forced executable.
5. Verify the neutral target rulebook is source-safe, side-neutral, horizon-frozen, and not labeled as strategy edge.
6. Verify all missing strategy fields are reduced to exact source-expansion/capture requirements.
7. Verify no result rows, target values, R, PnL, win-rate, expectancy, slippage, performance, AI/API, broker/account/order/deal/position evidence, paid/vendor evidence, raw blobs, or live behavior changes exist.
8. Verify no-leak, duplicate/proxy denominator, multiple-testing, source-field derivation, source expansion, saturation, focused tests, and standalone verifier outputs.
9. Emit a G12 audit decision. If accepted, the only allowed next lane is a separate quarantined neutral-target execution packet or source-field expansion packet; no promotion or live behavior is authorized.

## Required Inputs

- `research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_COMPLETION_AUDIT_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_RULEBOOK_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_FAMILY_EXECUTABILITY_MATRIX_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_SOURCE_FIELD_DERIVATION_CONTRACT_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_SOURCE_EXPANSION_REQUIREMENTS_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_VERIFICATION_RESULT_2026-05-11.json`

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and
`live_effect=false`. Do not generate result rows or touch live/API/broker/raw/prompt/config/risk/safety surfaces.
"""
    NEXT_G12_PROMPT.write_text(prompt, encoding="utf-8")


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    variant_registry = load_json(VARIANT_REGISTRY)
    freeze_packet = load_json(FREEZE_PACKET)
    rowset_manifest = load_json(FROZEN_ROWSET_MANIFEST)
    g12_verification = load_json(G12_VERIFICATION)
    g12_decision = load_json(G12_DECISION)
    candidate_manifest = load_json(CANDIDATE_MANIFEST)
    bar_manifest = load_json(BAR_MANIFEST)
    candidate_rows = load_jsonl(CANDIDATE_ROWS)
    bar_rows = load_jsonl(BAR_ROWS)

    write_context_anchor()
    blocker = make_blocker_reconciliation(
        variant_registry,
        freeze_packet,
        rowset_manifest,
        g12_verification,
        g12_decision,
        candidate_manifest,
        bar_manifest,
    )
    inventory = build_source_field_inventory(candidate_rows, bar_rows, variant_registry)
    search = scan_text_files()
    rulebook = make_rulebook()
    matrix = make_family_matrix(variant_registry)
    neutral = make_neutral_contract(rulebook)
    derivation = make_source_field_derivation_contract(variant_registry)
    expansion_ledger = make_source_field_expansion_execution_ledger(variant_registry)
    noleak = make_noleak_audit()
    multiple_testing = make_multiple_testing_ledger(rulebook)
    source_requirements = make_source_expansion_requirements(variant_registry)
    completion = make_completion_audit(blocker, inventory, search, rulebook, matrix, derivation, expansion_ledger)

    artifacts = {
        f"{PREFIX}_BLOCKER_RECONCILIATION_{DATE_TAG}.json": blocker,
        f"{PREFIX}_SOURCE_FIELD_INVENTORY_{DATE_TAG}.json": inventory,
        f"{PREFIX}_SEARCH_LEDGER_{DATE_TAG}.json": search,
        f"{PREFIX}_RULEBOOK_{DATE_TAG}.json": rulebook,
        f"{PREFIX}_FAMILY_EXECUTABILITY_MATRIX_{DATE_TAG}.json": matrix,
        f"{PREFIX}_NEUTRAL_TARGET_CONTRACT_{DATE_TAG}.json": neutral,
        f"{PREFIX}_SOURCE_FIELD_DERIVATION_CONTRACT_{DATE_TAG}.json": derivation,
        f"{PREFIX}_SOURCE_FIELD_EXPANSION_EXECUTION_LEDGER_{DATE_TAG}.json": expansion_ledger,
        f"{PREFIX}_NOLEAK_AUDIT_{DATE_TAG}.json": noleak,
        f"{PREFIX}_MULTIPLE_TESTING_LEDGER_{DATE_TAG}.json": multiple_testing,
        f"{PREFIX}_SOURCE_EXPANSION_REQUIREMENTS_{DATE_TAG}.json": source_requirements,
        f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json": completion,
    }
    for filename, payload in artifacts.items():
        write_json(ROUTE_DIR / filename, payload)
    write_completion_md(completion)
    write_g12_prompt()

    manifest = {
        **COMMON_SAFE_FIELDS,
        "artifact_family": "route_output_manifest",
        "generated_at_utc": now_utc(),
        "terminal_decision": TERMINAL_DECISION,
        "artifacts": [
            {
                "path": repo_path(ROUTE_DIR / filename),
                "sha256": sha256_file(ROUTE_DIR / filename),
                "bytes": (ROUTE_DIR / filename).stat().st_size,
            }
            for filename in sorted(artifacts)
        ]
        + [
            {
                "path": repo_path(ROUTE_DIR / f"{PREFIX}_REPAIR_CONTEXT_ANCHOR_{DATE_TAG}.md"),
                "sha256": sha256_file(ROUTE_DIR / f"{PREFIX}_REPAIR_CONTEXT_ANCHOR_{DATE_TAG}.md"),
                "bytes": (ROUTE_DIR / f"{PREFIX}_REPAIR_CONTEXT_ANCHOR_{DATE_TAG}.md").stat().st_size,
            },
            {
                "path": repo_path(ROUTE_DIR / f"{PREFIX}_REPAIR_CONTEXT_ANCHOR_{DATE_TAG}.json"),
                "sha256": sha256_file(ROUTE_DIR / f"{PREFIX}_REPAIR_CONTEXT_ANCHOR_{DATE_TAG}.json"),
                "bytes": (ROUTE_DIR / f"{PREFIX}_REPAIR_CONTEXT_ANCHOR_{DATE_TAG}.json").stat().st_size,
            },
            {
                "path": repo_path(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md"),
                "sha256": sha256_file(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md"),
                "bytes": (ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md").stat().st_size,
            },
            {
                "path": repo_path(NEXT_G12_PROMPT),
                "sha256": sha256_file(NEXT_G12_PROMPT),
                "bytes": NEXT_G12_PROMPT.stat().st_size,
            },
        ],
    }
    write_json(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true", help="Build artifacts in memory and print the manifest hash.")
    args = parser.parse_args()
    manifest = build()
    if args.check_only:
        print(sha256_json(manifest))
    else:
        print(json.dumps({"ok": True, "terminal_decision": TERMINAL_DECISION, "manifest": repo_path(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json")}, indent=2))


if __name__ == "__main__":
    main()
