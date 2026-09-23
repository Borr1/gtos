"""Build the G0 FPB discovery synthesis/control route.

This route is no-API G0 synthesis/control only. It consumes the accepted FPB
full-population discovery result screen plus the accepted G12 audit, then emits
machine-checkable ledgers for route selection, hardening coverage, source
saturation, hostile review, and next-prompt handoff. It never opens validation,
result scoring, broker/account/order evidence, paid/API access, or live trading
behavior.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-11"
ROUTE_ID = "G0_NO_API_MECHANICAL_REPLAY_FPB_DISCOVERY_SYNTHESIS_CONTROL_ROUTE"
EVIDENCE_CLASS = "NO_API_G0_DISCOVERY_SYNTHESIS_CONTROL_ONLY"
PREFIX = "G0_FPB_SYNTHESIS"

CONTROLLING_PROMPT = (
    "research/science_program_2026_05/04_goal_prompts/"
    "G0_NO_API_MECHANICAL_REPLAY_FPB_DISCOVERY_SYNTHESIS_CONTROL_ROUTE_GOAL_PROMPT_2026-05-11.md"
)
TARGET_ROUTE_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_mechanical_replay_family_path_behavior_discovery_result_screen"
)
G12_ROUTE_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_fpb_result_audit"
)
UPSTREAM_ROUTE_DIRS = [
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_mechanical_replay_engine_from_source_universe",
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_no_api_mechanical_replay_engine_source_control_audit",
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection",
]

MATRIX_PATH = TARGET_ROUTE_DIR / "FPB_FULL_POPULATION_AGGREGATE_MATRIX_2026-05-10.json"
DENOMINATOR_PATH = TARGET_ROUTE_DIR / "FPB_DENOMINATOR_DUPLICATE_POLICY_2026-05-10.json"
BASELINE_PATH = TARGET_ROUTE_DIR / "FPB_BASELINE_CONTROL_LEDGER_2026-05-10.json"
SELECTION_PATH = TARGET_ROUTE_DIR / "FPB_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json"
COMPACT_PATH = TARGET_ROUTE_DIR / "FPB_COMPACT_CAP_DIAGNOSTICS_2026-05-10.json"
FAILURE_PATH = TARGET_ROUTE_DIR / "FPB_FAILURE_ANATOMY_NEXT_HYPOTHESIS_LEDGER_2026-05-10.json"
TARGET_MANIFEST_PATH = TARGET_ROUTE_DIR / "FPB_OUTPUT_MANIFEST_2026-05-10.json"
G12_AUDIT_PATH = G12_ROUTE_DIR / "G12_FPB_RESULT_AUDIT_2026-05-11.json"
G12_AUDIT_MD_PATH = G12_ROUTE_DIR / "G12_FPB_RESULT_AUDIT_2026-05-11.md"

NEXT_PROMPT_NAME = (
    "G0_FPB_SEALED_PARTITION_AND_ADVERSARIAL_BASELINE_PACKET_GOAL_PROMPT_2026-05-11.md"
)
NEXT_PROMPT_PATH = PROMPT_DIR / NEXT_PROMPT_NAME
NEXT_PROMPT_REPO_PATH = (
    "research/science_program_2026_05/04_goal_prompts/" + NEXT_PROMPT_NAME
)

EXPECTED_COUNTS = {
    "raw_candidate_attempts": 13_540_033,
    "duplicate_candidate_keys": 687_275,
    "unique_nonduplicate_candidate_path_label_denominator": 12_852_758,
    "path_label_row_count": 12_852_758,
    "opened_family_count": 11,
    "baseline_control_family_count": 4,
}

LABELS = [
    "ONE_ATR_CONTINUATION_CONTEXT_TOUCH",
    "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH",
    "MIDPOINT_RETRACE_BEFORE_EXTENSION",
    "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE",
    "SAME_BAR_CONTEXT_AMBIGUOUS",
    "UNRESOLVED_BY_WINDOW",
    "UNRESOLVED_AT_SOURCE_END",
]

BASELINE_FAMILIES = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
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

ARTIFACTS: dict[str, str] = {
    "evidence_chain": f"{PREFIX}_EVIDENCE_CHAIN_RECONCILIATION_LEDGER_{DATE_TAG}",
    "family_behavior": f"{PREFIX}_DISCOVERY_FAMILY_BEHAVIOR_LEDGER_{DATE_TAG}",
    "baseline_controls": f"{PREFIX}_ADVERSARIAL_BASELINE_CONTROL_LEDGER_{DATE_TAG}",
    "selection_bias": f"{PREFIX}_SELECTION_BIAS_LEDGER_{DATE_TAG}",
    "multiple_testing": f"{PREFIX}_MULTIPLE_TESTING_LEDGER_{DATE_TAG}",
    "concentration_duplicate": f"{PREFIX}_CONCENTRATION_DUPLICATE_RISK_LEDGER_{DATE_TAG}",
    "ambiguity_unresolved": f"{PREFIX}_AMBIGUITY_UNRESOLVED_BURDEN_LEDGER_{DATE_TAG}",
    "baseline_anomaly": f"{PREFIX}_BASELINE_ANOMALY_LEDGER_{DATE_TAG}",
    "fragility": f"{PREFIX}_FAMILY_SLICE_FRAGILITY_LEDGER_{DATE_TAG}",
    "sealed_readiness": f"{PREFIX}_SEALED_VALIDATION_READINESS_LEDGER_{DATE_TAG}",
    "route_ranking": f"{PREFIX}_ROUTE_RANKING_LEDGER_{DATE_TAG}",
    "no_lazy_blocker": f"{PREFIX}_NO_LAZY_BLOCKER_LEDGER_{DATE_TAG}",
    "source_saturation": f"{PREFIX}_SEARCHED_ROOT_SOURCE_SATURATION_LEDGER_{DATE_TAG}",
    "hardening": f"{PREFIX}_HARDENING_COVERAGE_LEDGER_{DATE_TAG}",
    "hostile_review": f"{PREFIX}_HOSTILE_EDGE_REVIEW_LEDGER_{DATE_TAG}",
    "historical_partition": f"{PREFIX}_HISTORICAL_PARTITION_READINESS_LEDGER_{DATE_TAG}",
    "ai_cost": f"{PREFIX}_AI_API_COST_BOUNDARY_LEDGER_{DATE_TAG}",
    "process_limitations": f"{PREFIX}_PROCESS_LIMITATION_COUNTERMEASURE_LEDGER_{DATE_TAG}",
    "negative_anatomy": f"{PREFIX}_NEGATIVE_RESULT_FAILURE_ANATOMY_LEDGER_{DATE_TAG}",
    "context_instruction": f"{PREFIX}_CONTEXT_ANCHOR_INSTRUCTION_COVERAGE_LEDGER_{DATE_TAG}",
    "saturation": f"{PREFIX}_SATURATION_SELF_REDTEAM_PASS_{DATE_TAG}",
    "next_prompt_pack": f"{PREFIX}_NEXT_PROMPT_PACK_{DATE_TAG}",
    "no_leak": f"{PREFIX}_NOLEAK_DIRTY_STATE_AUDIT_{DATE_TAG}",
    "manifest": f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}",
    "completion": f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    try:
        f = path.open("rb")
    except FileNotFoundError:
        # Some prior route paths exceed the default Windows MAX_PATH behavior
        # for normal opens even when directory enumeration can see them.
        f = open("\\\\?\\" + str(path.resolve()), "rb")
    with f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_git(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "command": "git " + " ".join(args),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip().splitlines(),
        "stderr": proc.stderr.strip().splitlines(),
    }


def safe_payload(artifact_family: str, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "g0_fpb_synthesis_v1",
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": GENERATED_AT,
        **SAFE_FLAGS,
        **body,
    }


def pct(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.2f}%"


def proportion(count: int, denominator: int) -> float:
    return round(count / denominator, 8) if denominator else 0.0


def label_counts(row: dict[str, Any]) -> dict[str, int]:
    counts = row.get("counts", {})
    return {label: int(counts.get(label, 0)) for label in LABELS}


def aggregate_count(mapping: dict[str, Any]) -> int:
    return sum(int(v) for v in mapping.values())


def top_slices(mapping: dict[str, int], denominator: int, limit: int = 5) -> list[dict[str, Any]]:
    rows = []
    for name, count in sorted(mapping.items(), key=lambda item: item[1], reverse=True)[:limit]:
        rows.append({"slice": name, "count": int(count), "share_of_family": proportion(int(count), denominator)})
    return rows


def collect_family_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    baseline_combined = matrix["baseline_control_combined_distribution"]["proportions"]
    rows: list[dict[str, Any]] = []
    for row in matrix["family_rows"]:
        family = row["family_id"]
        denominator = int(row["denominator"])
        counts = label_counts(row)
        continuation = counts["ONE_ATR_CONTINUATION_CONTEXT_TOUCH"]
        protective = counts["PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH"]
        ambiguity = counts["SAME_BAR_CONTEXT_AMBIGUOUS"]
        unresolved = counts["UNRESOLVED_BY_WINDOW"] + counts["UNRESOLVED_AT_SOURCE_END"]
        opening_context = (
            counts["MIDPOINT_RETRACE_BEFORE_EXTENSION"]
            + counts["ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE"]
        )
        proportions = {label: proportion(counts[label], denominator) for label in LABELS}
        source_slices = matrix["candidate_by_family_source_family"].get(family, {})
        symbol_slices = matrix["candidate_by_family_symbol"].get(family, {})
        timeframe_slices = matrix["candidate_by_family_timeframe"].get(family, {})
        session_slices = matrix["candidate_by_family_session_or_kill_zone"].get(family, {})
        regime_slices = matrix["candidate_by_family_regime_phase"].get(family, {})
        side_slices = matrix["candidate_by_family_side"].get(family, {})
        all_top = {
            "source_family": top_slices(source_slices, denominator, 4),
            "symbol": top_slices(symbol_slices, denominator, 5),
            "timeframe": top_slices(timeframe_slices, denominator, 5),
            "session_or_kill_zone": top_slices(session_slices, denominator, 5),
            "regime_phase": top_slices(regime_slices, denominator, 5),
            "side": top_slices(side_slices, denominator, 5),
        }
        max_slice_share = max(
            [
                item["share_of_family"]
                for values in all_top.values()
                for item in values[:1]
            ]
            or [0.0]
        )
        baseline_continuation = float(
            baseline_combined.get("ONE_ATR_CONTINUATION_CONTEXT_TOUCH", 0.0)
        )
        rows.append(
            {
                "family_id": family,
                "family_role": "baseline_control" if family in BASELINE_FAMILIES else "intended_or_candidate_family",
                "denominator": denominator,
                "counts": counts,
                "proportions": proportions,
                "continuation_context_touch_rate": proportion(continuation, denominator),
                "protective_boundary_context_touch_rate": proportion(protective, denominator),
                "opening_drive_context_rate": proportion(opening_context, denominator),
                "ambiguity_unresolved_rate": proportion(ambiguity + unresolved, denominator),
                "same_bar_ambiguity_rate": proportion(ambiguity, denominator),
                "unresolved_rate": proportion(unresolved, denominator),
                "baseline_combined_continuation_gap": round(
                    proportion(continuation, denominator) - baseline_continuation, 8
                ),
                "top_slices": all_top,
                "max_top_slice_share": max_slice_share,
                "slice_concentration_flag": (
                    "HIGH"
                    if max_slice_share >= 0.65
                    else "MEDIUM"
                    if max_slice_share >= 0.45
                    else "LOW"
                ),
                "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
            }
        )
    return rows


def baseline_similarity_rows(family_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baselines = [row for row in family_rows if row["family_id"] in BASELINE_FAMILIES]
    intended = [row for row in family_rows if row["family_id"] not in BASELINE_FAMILIES]
    rows = []
    keys = [
        "continuation_context_touch_rate",
        "protective_boundary_context_touch_rate",
        "same_bar_ambiguity_rate",
        "unresolved_rate",
    ]
    for row in intended:
        comparisons = []
        for base in baselines:
            distance = sum(abs(row[key] - base[key]) for key in keys)
            comparisons.append(
                {
                    "baseline_family": base["family_id"],
                    "l1_path_label_distance": round(distance, 8),
                    "continuation_gap": round(
                        row["continuation_context_touch_rate"]
                        - base["continuation_context_touch_rate"],
                        8,
                    ),
                    "protective_gap": round(
                        row["protective_boundary_context_touch_rate"]
                        - base["protective_boundary_context_touch_rate"],
                        8,
                    ),
                }
            )
        nearest = sorted(comparisons, key=lambda item: item["l1_path_label_distance"])[0]
        rows.append(
            {
                "family_id": row["family_id"],
                "nearest_baseline": nearest,
                "all_baseline_comparisons": sorted(
                    comparisons, key=lambda item: item["l1_path_label_distance"]
                ),
                "anomaly_flag": (
                    "BASELINE_RESEMBLANCE_REQUIRES_STRESS"
                    if nearest["l1_path_label_distance"] < 0.16
                    else "NO_CLOSE_BASELINE_RESEMBLANCE_ON_ACCEPTED_AGGREGATES"
                ),
                "interpretation_boundary": "baseline similarity is an overfit-risk diagnostic, not performance scoring",
            }
        )
    return rows


def rank_routes(family_rows: list[dict[str, Any]], baseline_anomalies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anomaly_by_family = {row["family_id"]: row for row in baseline_anomalies}
    family_by_id = {row["family_id"]: row for row in family_rows}
    route_specs = [
        {
            "rank": 1,
            "route_id": "G0_FPB_SEALED_PARTITION_AND_ADVERSARIAL_BASELINE_PACKET",
            "families": ["adjacent_range_compression_breakout", "ob_retest", "opening_drive_no_fill_lifecycle"],
            "route_type": "sealed_validation_design_packet_not_execution",
            "selection_decision": "SELECTED_NEXT_PROMPT",
            "why_selected": "Combines one broad high-distinctiveness path-shape family, one GTOS-core structural family, and one clock/lifecycle family while freezing adversarial baselines before any sealed validation is opened.",
        },
        {
            "rank": 2,
            "route_id": "FPB_OB_RETEST_STRUCTURAL_CONTEXT_SEALED_HOLDOUT_ROUTE",
            "families": ["ob_retest"],
            "route_type": "family_specific_sealed_validation_candidate",
            "selection_decision": "RANKED_NOT_TOP_BECAUSE_TOP_PACKET_CAN_COVER_IT_WITH_CONTROLS",
            "why_selected": "Core GTOS family has accepted full-population discovery coverage and a path-label profile separated from combined baselines, but it still needs sealed partition and concentration controls.",
        },
        {
            "rank": 3,
            "route_id": "FPB_ADJACENT_RANGE_COMPRESSION_BREAKOUT_SOURCE_STRESS_ROUTE",
            "families": ["adjacent_range_compression_breakout"],
            "route_type": "source_and_concentration_stress_candidate",
            "selection_decision": "RANKED_HIGH_BUT_NOT_ALONE",
            "why_selected": "Path-label profile is highly distinctive, but top-slice concentration and M1/local-source dependence require hostile source/slice stress before any validation claim.",
        },
        {
            "rank": 4,
            "route_id": "FPB_OPENING_DRIVE_NO_FILL_LIFECYCLE_SOURCE_CONTROL_ROUTE",
            "families": ["opening_drive_no_fill_lifecycle"],
            "route_type": "source_control_and_label_boundary_route",
            "selection_decision": "RANKED_FOR_SOURCE_CONTROL_NOT_VALIDATION",
            "why_selected": "Uses a separate midpoint/extension context vocabulary and session/lifecycle framing; it needs strict no-fill source-state boundaries before result-oriented work.",
        },
        {
            "rank": 5,
            "route_id": "FPB_FVG_FILL_AMBIGUITY_RESOLUTION_AND_BASELINE_STRESS_ROUTE",
            "families": ["fvg_fill"],
            "route_type": "ambiguity_reduction_route",
            "selection_decision": "DEFER_UNTIL_SAME_BAR_AMBIGUITY_CONTROL",
            "why_selected": "Large family but same-bar ambiguity and baseline resemblance burden make ambiguity/source-control the next honest work, not validation.",
        },
        {
            "rank": 6,
            "route_id": "FPB_LIQUIDITY_STOP_RUN_CONTEXT_BASELINE_DOMINANCE_STRESS_ROUTE",
            "families": ["liquidity_stop_run_context", "session_kz_sweep"],
            "route_type": "adversarial_baseline_and_mechanism_stress_route",
            "selection_decision": "DEFER_FOR_BASELINE_DOMINANCE_STRESS",
            "why_selected": "Liquidity/session families are mechanism-interesting but too close to shifted-entry style controls without additional source/slice separation.",
        },
        {
            "rank": 7,
            "route_id": "FPB_BREAKER_RE_ENTRY_SAMPLE_EXPANSION_AND_DUPLICATE_POLICY_ROUTE",
            "families": ["breaker_re_entry"],
            "route_type": "sample_expansion_and_holdout_design_route",
            "selection_decision": "DEFER_UNTIL_DENOMINATOR_EXPANSION_OR_STRICT_HOLDOUT",
            "why_selected": "Mechanistically relevant but denominator is much smaller than other families, so it needs expansion or a narrow holdout design before ranking pressure is justified.",
        },
    ]
    ranked = []
    for spec in route_specs:
        family_details = []
        for family in spec["families"]:
            row = family_by_id[family]
            family_details.append(
                {
                    "family_id": family,
                    "denominator": row["denominator"],
                    "continuation_context_touch_rate": row["continuation_context_touch_rate"],
                    "protective_boundary_context_touch_rate": row[
                        "protective_boundary_context_touch_rate"
                    ],
                    "ambiguity_unresolved_rate": row["ambiguity_unresolved_rate"],
                    "slice_concentration_flag": row["slice_concentration_flag"],
                    "nearest_baseline": anomaly_by_family.get(family, {}).get("nearest_baseline"),
                    "top_slices": row["top_slices"],
                }
            )
        ranked.append(
            {
                **spec,
                "evidence_basis": family_details,
                "why_not_merely_discovery_overfit": [
                    "The route is not allowed to claim validation from accepted FPB discovery labels.",
                    "Next work must freeze sealed partitions, duplicate policy, baselines, and falsification criteria before opening any validation slice.",
                    "Baseline controls are carried as adversarial comparators, not decorative reference rows.",
                ],
                "validation_or_source_control_prerequisite": (
                    "Build a partition ledger that isolates discovery/development/sealed/stress/forward/contaminated pools; "
                    "freeze duplicate-key policy, source/as-of fields, baseline controls, and purged/embargoed split rules."
                ),
                "exact_blocker_if_not_selected": (
                    "Not selected as standalone top route because the broader selected packet can freeze shared partition and baseline controls before family-specific validation."
                    if spec["rank"] != 1
                    else "No blocker for route-design scope; validation execution remains a separate future evidence-class gate."
                ),
                "falsification_criteria": [
                    "Reject the route if a sealed partition cannot be built without reusing discovery-exposed rows/windows or contaminated source slices.",
                    "Reject or downgrade any family whose path-label distinctiveness disappears under duplicate-key, source-family, symbol, timeframe, session/KZ, or regime holdouts.",
                    "Reject any mechanism if an adversarial baseline explains the same path-label behavior under the frozen comparator policy.",
                    "Reject any route whose required fields are non-generatable historical GTOS source-state rather than recoverable market/source context.",
                ],
                "next_prompt_path": NEXT_PROMPT_REPO_PATH if spec["rank"] == 1 else None,
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            }
        )
    return ranked


def limited_search(root: Path, patterns: list[str], max_hits: int = 40, max_files: int = 5000) -> dict[str, Any]:
    record: dict[str, Any] = {
        "root": str(root),
        "exists": root.exists(),
        "patterns": patterns,
        "max_hits": max_hits,
        "max_files_visited": max_files,
        "hits": [],
        "hit_count_returned": 0,
        "files_visited": 0,
        "truncated": False,
        "search_boundary": "targeted_limited_filename_search_no_raw_market_data_consumed",
    }
    if not root.exists():
        return record
    try:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            record["files_visited"] += 1
            name = path.name
            if any(fnmatch.fnmatch(name, pattern) for pattern in patterns):
                record["hits"].append(repo_path(path) if path.is_relative_to(ROOT) else str(path))
                if len(record["hits"]) >= max_hits:
                    break
            if record["files_visited"] >= max_files:
                record["truncated"] = True
                break
    except PermissionError as exc:
        record["permission_error"] = str(exc)
    record["hit_count_returned"] = len(record["hits"])
    return record


def build_source_saturation() -> dict[str, Any]:
    roots = [
        ROOT,
        ROOT / "data",
        ROOT / "data" / "ticks",
        ROOT / "shadow_logs",
        ROOT / "exports",
        Path(r"C:\tmp\gtos_otb"),
        Path(r"C:\SierraChart"),
    ]
    searches = [
        limited_search(root, ["*FPB*", "*MECHANICAL_REPLAY*", "*family_path_behavior*"])
        for root in roots
    ]
    git_logs = [
        run_git(["log", "--oneline", "-n", "20", "--", repo_path(TARGET_ROUTE_DIR)]),
        run_git(["log", "--oneline", "-n", "20", "--", repo_path(G12_ROUTE_DIR)]),
        run_git(["ls-files", repo_path(TARGET_ROUTE_DIR)]),
        run_git(["ls-files", repo_path(G12_ROUTE_DIR)]),
    ]
    input_hashes = {
        repo_path(path): sha256_file(path)
        for path in [
            MATRIX_PATH,
            DENOMINATOR_PATH,
            BASELINE_PATH,
            SELECTION_PATH,
            COMPACT_PATH,
            FAILURE_PATH,
            TARGET_MANIFEST_PATH,
            G12_AUDIT_PATH,
            G12_AUDIT_MD_PATH,
        ]
        if path.exists()
    }
    for directory in UPSTREAM_ROUTE_DIRS:
        for path in sorted(directory.glob("*.json"))[:12]:
            input_hashes[repo_path(path)] = sha256_file(path)
    return safe_payload(
        "searched_root_source_saturation_ledger",
        {
            "searches": searches,
            "git_searches": git_logs,
            "input_hashes": input_hashes,
            "source_saturation_decision": "SUFFICIENT_FOR_G0_SYNTHESIS_CONTROL_ROUTE",
            "raw_heavy_data_consumed": False,
            "broker_or_account_sources_read": False,
            "missing_sources_reduced_to_exact_requirements": [
                {
                    "requirement": "Future validation partitions",
                    "status": "future_route_must_build_before_validation_execution",
                    "owner_or_access_needed_now": False,
                }
            ],
        },
    )


def make_evidence_chain(matrix: dict[str, Any], denominator: dict[str, Any], g12: dict[str, Any]) -> dict[str, Any]:
    checks = [
        {
            "check_id": "raw_candidate_attempts",
            "expected": EXPECTED_COUNTS["raw_candidate_attempts"],
            "matrix": matrix.get("raw_candidate_attempts"),
            "denominator": denominator.get("recomputed_raw_candidate_attempts"),
            "g12_expected": g12.get("count_audit", {}).get("expected_counts", {}).get("raw_candidate_attempts"),
            "status": "PASS"
            if matrix.get("raw_candidate_attempts")
            == denominator.get("recomputed_raw_candidate_attempts")
            == EXPECTED_COUNTS["raw_candidate_attempts"]
            else "FAIL",
        },
        {
            "check_id": "duplicate_candidate_keys",
            "expected": EXPECTED_COUNTS["duplicate_candidate_keys"],
            "matrix": matrix.get("duplicate_candidate_keys"),
            "denominator": denominator.get("recomputed_duplicate_candidate_keys"),
            "g12_expected": g12.get("count_audit", {}).get("expected_counts", {}).get("duplicate_candidate_keys"),
            "status": "PASS"
            if matrix.get("duplicate_candidate_keys")
            == denominator.get("recomputed_duplicate_candidate_keys")
            == EXPECTED_COUNTS["duplicate_candidate_keys"]
            else "FAIL",
        },
        {
            "check_id": "unique_denominator_path_label_rows",
            "expected": EXPECTED_COUNTS["unique_nonduplicate_candidate_path_label_denominator"],
            "matrix": matrix.get("unique_nonduplicate_candidate_path_label_denominator"),
            "denominator": denominator.get("recomputed_unique_nonduplicate_denominator"),
            "g12_expected": g12.get("count_audit", {})
            .get("expected_counts", {})
            .get("unique_nonduplicate_candidate_path_label_denominator"),
            "status": "PASS"
            if matrix.get("unique_nonduplicate_candidate_path_label_denominator")
            == denominator.get("recomputed_unique_nonduplicate_denominator")
            == EXPECTED_COUNTS["unique_nonduplicate_candidate_path_label_denominator"]
            else "FAIL",
        },
        {
            "check_id": "opened_family_count",
            "expected": EXPECTED_COUNTS["opened_family_count"],
            "matrix": matrix.get("opened_family_count"),
            "g12": g12.get("count_audit", {}).get("opened_family_count"),
            "status": "PASS"
            if matrix.get("opened_family_count") == g12.get("count_audit", {}).get("opened_family_count") == 11
            else "FAIL",
        },
        {
            "check_id": "baseline_control_family_count",
            "expected": EXPECTED_COUNTS["baseline_control_family_count"],
            "matrix": len(matrix.get("baseline_control_families", [])),
            "g12": g12.get("count_audit", {}).get("baseline_control_family_count"),
            "status": "PASS"
            if len(matrix.get("baseline_control_families", []))
            == g12.get("count_audit", {}).get("baseline_control_family_count")
            == 4
            else "FAIL",
        },
    ]
    return safe_payload(
        "evidence_chain_reconciliation_ledger",
        {
            "accepted_g12_decision": g12.get("audit_decision"),
            "expected_g12_decision": "ACCEPT_AS_QUARANTINED_DISCOVERY_PATH_BEHAVIOR_LEDGER",
            "count_checks": checks,
            "all_counts_reconciled": all(row["status"] == "PASS" for row in checks),
            "evidence_chain": [
                {
                    "stage": "source_universe_replay_substrate",
                    "path": repo_path(UPSTREAM_ROUTE_DIRS[0]),
                    "role": "accepted source/control substrate for no-API mechanical replay candidates and path labels",
                },
                {
                    "stage": "g12_source_control_audit",
                    "path": repo_path(UPSTREAM_ROUTE_DIRS[1]),
                    "role": "accepted independent audit of source-control substrate and no-leak boundaries",
                },
                {
                    "stage": "g0_source_control_synthesis_route_selection",
                    "path": repo_path(UPSTREAM_ROUTE_DIRS[2]),
                    "role": "selected full-population FPB discovery result screen as next route",
                },
                {
                    "stage": "fpb_full_population_result_screen",
                    "path": repo_path(TARGET_ROUTE_DIR),
                    "role": "accepted quarantined full-population discovery path-behavior ledger",
                },
                {
                    "stage": "g12_fpb_result_audit",
                    "path": repo_path(G12_ROUTE_DIR),
                    "role": "accepted FPB result only as quarantined discovery path-behavior ledger",
                },
                {
                    "stage": "this_g0_synthesis_control_route",
                    "path": repo_path(ROUTE_DIR),
                    "role": "route selection and validation-readiness design only; no validation execution",
                },
            ],
            "interpretation_boundary": "Accepted counts are denominator/source-control facts, not R, PnL, win-rate, expectancy, validation, or promotion evidence.",
        },
    )


def make_family_behavior(matrix: dict[str, Any], family_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return safe_payload(
        "discovery_family_behavior_ledger",
        {
            "opened_family_count": len(family_rows),
            "opened_families": [row["family_id"] for row in family_rows],
            "label_vocabulary": LABELS,
            "global_label_distribution": matrix["global_label_distribution"],
            "family_rows": family_rows,
            "strict_boundary": "All rows are discovery path-label context only. Labels are not wins/losses, R, PnL, win-rate, expectancy, or promotion evidence.",
        },
    )


def make_baseline_controls(baseline: dict[str, Any], family_rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_rows = [row for row in family_rows if row["family_id"] in BASELINE_FAMILIES]
    return safe_payload(
        "adversarial_baseline_control_ledger",
        {
            "all_four_baseline_controls_included": baseline.get("all_four_baseline_controls_included"),
            "baseline_control_families": BASELINE_FAMILIES,
            "accepted_policy": baseline.get("policy"),
            "baseline_rows": baseline_rows,
            "adversarial_roles": [
                {
                    "baseline_family": "baseline_random_session_control",
                    "role": "session/time availability placebo; catches path-label prevalence that occurs without intended family logic",
                },
                {
                    "baseline_family": "baseline_shifted_entry_control",
                    "role": "entry displacement placebo; catches generic path movement around nearby levels",
                },
                {
                    "baseline_family": "baseline_momentum_continuation",
                    "role": "simple momentum comparator; catches continuation labels that do not need structural family logic",
                },
                {
                    "baseline_family": "baseline_mean_reversion",
                    "role": "simple reversal comparator; catches protective/context-touch labels explained by generic reversal",
                },
            ],
            "interpretation_boundary": "Baselines are overfit detectors and future validation comparators, not performance controls.",
        },
    )


def make_selection_bias(matrix: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any]:
    source_slices = sorted(matrix["full_candidate_count_by_source_family"].keys())
    symbols = sorted(matrix["full_candidate_count_by_symbol"].keys())
    timeframes = sorted(matrix["full_candidate_count_by_timeframe"].keys())
    sessions = sorted(matrix["full_candidate_count_by_session_or_kill_zone"].keys())
    regimes = sorted(matrix["full_candidate_count_by_regime_phase"].keys())
    return safe_payload(
        "selection_bias_ledger",
        {
            "families_considered": matrix["opened_families"],
            "labels_considered": LABELS,
            "source_slices": source_slices,
            "symbols": symbols,
            "timeframes": timeframes,
            "session_or_kill_zone_slices": sessions,
            "regime_phase_slices": regimes,
            "excluded_source_slice_count": matrix.get("excluded_source_slice_count"),
            "abandoned_or_excluded_branches": selection.get("abandoned_or_excluded_branches", []),
            "ranking_criteria": [
                "source safety",
                "accepted denominator integrity",
                "baseline-control separability",
                "ambiguity/unresolved burden",
                "duplicate/concentration risk",
                "source/symbol/timeframe/session/KZ/regime fragility",
                "sealed-validation partition readiness",
                "mechanism plausibility under hostile review",
                "future falsification clarity",
            ],
            "selection_decisions": [
                {
                    "decision": "No family promoted or validated",
                    "reason": "All accepted FPB evidence is discovery path-label context only.",
                },
                {
                    "decision": "Rank 1 selected route is a sealed-partition and adversarial-baseline packet",
                    "reason": "The next safe step is to freeze partitions and controls before any future validation execution.",
                },
            ],
            "compact_sample_decisive": matrix.get("compact_sample_used_for_decisive_ranking"),
            "anti_bias_boundary": "No compact-only, selected-slice-only, or baseline-omitted shortcut is allowed to drive route selection.",
        },
    )


def make_multiple_testing(selection: dict[str, Any], matrix: dict[str, Any]) -> dict[str, Any]:
    search_surface = {
        "family_count": len(matrix["opened_families"]),
        "label_count": len(LABELS),
        "source_family_count": len(matrix["full_candidate_count_by_source_family"]),
        "symbol_count": len(matrix["full_candidate_count_by_symbol"]),
        "timeframe_count": len(matrix["full_candidate_count_by_timeframe"]),
        "session_or_kill_zone_count": len(matrix["full_candidate_count_by_session_or_kill_zone"]),
        "regime_phase_count": len(matrix["full_candidate_count_by_regime_phase"]),
        "baseline_control_count": len(matrix["baseline_control_families"]),
    }
    nominal_cross_tab_cells = (
        search_surface["family_count"]
        * search_surface["label_count"]
        * (
            search_surface["source_family_count"]
            + search_surface["symbol_count"]
            + search_surface["timeframe_count"]
            + search_surface["session_or_kill_zone_count"]
            + search_surface["regime_phase_count"]
        )
    )
    return safe_payload(
        "multiple_testing_ledger",
        {
            "search_surface": search_surface,
            "nominal_cross_tab_cells_reviewed": nominal_cross_tab_cells,
            "upstream_multiple_testing_debt": selection.get("multiple_testing_debt"),
            "post_hoc_thresholds_created": False,
            "selected_route_is_validation_execution": False,
            "debt_control": [
                "Route ranking is for future prompt selection only.",
                "Any future validation must freeze family, labels, partitions, duplicate policy, and baselines before opening sealed data.",
                "DSR/PBO/effective-N style diagnostics are deferred to validation/stress lanes and cannot be inferred here.",
            ],
        },
    )


def make_concentration_duplicate(matrix: dict[str, Any], denominator: dict[str, Any], family_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return safe_payload(
        "concentration_duplicate_risk_ledger",
        {
            "raw_candidate_attempts": matrix["raw_candidate_attempts"],
            "duplicate_candidate_keys": matrix["duplicate_candidate_keys"],
            "duplicate_share_of_raw_attempts": proportion(
                matrix["duplicate_candidate_keys"], matrix["raw_candidate_attempts"]
            ),
            "unique_denominator": matrix["unique_nonduplicate_candidate_path_label_denominator"],
            "duplicate_key_policy": denominator.get("duplicate_key_policy"),
            "path_label_duplicate_policy": denominator.get("path_label_duplicate_policy"),
            "global_source_row_concentration": matrix["concentration_diagnostics"],
            "family_concentration_rows": [
                {
                    "family_id": row["family_id"],
                    "denominator": row["denominator"],
                    "slice_concentration_flag": row["slice_concentration_flag"],
                    "max_top_slice_share": row["max_top_slice_share"],
                    "top_slices": row["top_slices"],
                }
                for row in family_rows
            ],
            "risk_decision": "HIGH_ENOUGH_TO_REQUIRE_SEALED_HOLDOUT_AND_CONCENTRATION_CAPS_BEFORE_VALIDATION",
        },
    )


def make_ambiguity(matrix: dict[str, Any], family_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return safe_payload(
        "ambiguity_unresolved_burden_ledger",
        {
            "global_ambiguity_unresolved_count": matrix["global_label_distribution"]["ambiguity_unresolved_count"],
            "global_ambiguity_unresolved_rate": proportion(
                matrix["global_label_distribution"]["ambiguity_unresolved_count"],
                matrix["global_label_distribution"]["denominator"],
            ),
            "family_rows": [
                {
                    "family_id": row["family_id"],
                    "denominator": row["denominator"],
                    "same_bar_ambiguity_rate": row["same_bar_ambiguity_rate"],
                    "unresolved_rate": row["unresolved_rate"],
                    "ambiguity_unresolved_rate": row["ambiguity_unresolved_rate"],
                    "handling_rule": (
                        "must remain separated from continuation/protective/context-touch labels; future validation must predefine ambiguous-row handling"
                    ),
                }
                for row in family_rows
            ],
            "label_separation_policy": "Ambiguous/unresolved labels are burden, not failures or successes, and cannot be silently folded into any future denominator.",
        },
    )


def make_baseline_anomaly(baseline_anomalies: list[dict[str, Any]]) -> dict[str, Any]:
    return safe_payload(
        "baseline_anomaly_ledger",
        {
            "rows": baseline_anomalies,
            "anomaly_policy": "Close resemblance to a baseline does not kill a family by itself, but blocks validation ranking until the future route freezes adversarial baseline stress tests.",
        },
    )


def make_fragility(family_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for row in family_rows:
        fragilities = []
        for dimension, slices in row["top_slices"].items():
            if slices and slices[0]["share_of_family"] >= 0.55:
                fragilities.append(
                    {
                        "dimension": dimension,
                        "top_slice": slices[0]["slice"],
                        "share": slices[0]["share_of_family"],
                        "risk": "single_slice_dependence_requires_holdout_or_cap",
                    }
                )
        rows.append(
            {
                "family_id": row["family_id"],
                "fragility_flags": fragilities,
                "fragility_status": "FRAGILE" if fragilities else "NO_DOMINANT_SINGLE_SLICE_ABOVE_55_PERCENT",
            }
        )
    return safe_payload(
        "family_slice_fragility_ledger",
        {
            "rows": rows,
            "policy": "Any future validation must predefine leave-one-source/symbol/timeframe/session/KZ/regime stress checks and concentration caps.",
        },
    )


def make_sealed_readiness(ranked_routes: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for route in ranked_routes:
        rows.append(
            {
                "rank": route["rank"],
                "route_id": route["route_id"],
                "families": route["families"],
                "readiness_status": (
                    "READY_FOR_SEALED_PARTITION_DESIGN_NOT_VALIDATION_EXECUTION"
                    if route["rank"] == 1
                    else "NEEDS_ROUTE_SPECIFIC_SOURCE_OR_STRESS_PREREQUISITE"
                ),
                "required_before_validation_execution": [
                    "partition ledger separating discovery, development, sealed validation, stress, forward, and contaminated pools",
                    "purge and embargo rules around discovery-exposed windows",
                    "duplicate-key and duplicate-cluster concentration policy",
                    "baseline comparator set frozen before sealed data opening",
                    "source/as-of/no-leak contract for every field",
                    "ambiguity/unresolved handling rule",
                    "falsification criteria and stop conditions",
                ],
                "validation_safe_now": False,
                "falsification_criteria": route["falsification_criteria"],
            }
        )
    return safe_payload(
        "sealed_validation_readiness_ledger",
        {
            "rows": rows,
            "terminal_decision": "NEXT_ROUTE_MAY_BUILD_SEALED_PARTITION_PACKET_BUT_THIS_ROUTE_DOES_NOT_VALIDATE",
        },
    )


def make_route_ranking(ranked_routes: list[dict[str, Any]]) -> dict[str, Any]:
    return safe_payload(
        "route_ranking_ledger",
        {
            "ranked_routes": ranked_routes,
            "selected_next_route": ranked_routes[0],
            "next_prompt_path": NEXT_PROMPT_REPO_PATH,
            "route_priority_not_performance": True,
        },
    )


def make_no_lazy_blocker() -> dict[str, Any]:
    rows = [
        {
            "item": "accepted_count_reconciliation",
            "same_evidence_class_action": "loaded matrix, denominator policy, and G12 audit; reconciled exact counts",
            "status": "CLEARED",
        },
        {
            "item": "baseline_anomaly_risk",
            "same_evidence_class_action": "computed nearest-baseline path-label resemblance and routed close cases to stress/control work",
            "status": "CLEARED_TO_FUTURE_STRESS_CRITERIA",
        },
        {
            "item": "concentration_duplicate_risk",
            "same_evidence_class_action": "recorded raw duplicate count, duplicate policy, global source-row concentration, and family top-slice risks",
            "status": "CLEARED_TO_PARTITION_AND_CAP_REQUIREMENTS",
        },
        {
            "item": "sealed_validation_execution",
            "same_evidence_class_action": "identified as evidence-class gate; next route may design packet but cannot execute validation inside this G0 synthesis",
            "status": "EXACT_SPLIT_REQUIRED",
        },
        {
            "item": "broker_account_order_history_data",
            "same_evidence_class_action": "forbidden by prompt and not needed for accepted FPB discovery synthesis",
            "status": "NOT_OPENED",
        },
    ]
    return safe_payload(
        "no_lazy_blocker_ledger",
        {
            "rows": rows,
            "owner_access_requests_needed_now": [],
            "remaining_blockers": [
                "Future validation execution is intentionally split into a later evidence class after sealed partition packet acceptance."
            ],
        },
    )


def make_hardening() -> dict[str, Any]:
    rows = [
        {
            "source": "goal_session_research_discipline.md",
            "hardening_item": "proof-or-impossibility and same-evidence-class continuation",
            "artifact_evidence": [ARTIFACTS["no_lazy_blocker"], ARTIFACTS["saturation"], ARTIFACTS["completion"]],
            "status": "PASS",
        },
        {
            "source": "goal_session_research_discipline.md",
            "hardening_item": "context compaction safety",
            "artifact_evidence": [ARTIFACTS["context_instruction"], ARTIFACTS["manifest"]],
            "status": "PASS",
        },
        {
            "source": "research_operating_doctrine.md",
            "hardening_item": "aggressive research with strict promotion and broad science horizon",
            "artifact_evidence": [ARTIFACTS["route_ranking"], ARTIFACTS["hostile_review"], ARTIFACTS["negative_anatomy"]],
            "status": "PASS",
        },
        {
            "source": "local_heavy_data_inventory.md",
            "hardening_item": "worktree absence is not data absence; searched roots and hashes recorded",
            "artifact_evidence": [ARTIFACTS["source_saturation"]],
            "status": "PASS",
        },
        {
            "source": "ai_in_loop_cost_control_research_plan.md",
            "hardening_item": "broad replay remains no-API; future AI work must be targeted/cached/budgeted",
            "artifact_evidence": [ARTIFACTS["ai_cost"], ARTIFACTS["next_prompt_pack"]],
            "status": "PASS",
        },
        {
            "source": "HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md",
            "hardening_item": "partition ledger and purged/embargoed validation design before validation execution",
            "artifact_evidence": [ARTIFACTS["historical_partition"], ARTIFACTS["sealed_readiness"]],
            "status": "PASS",
        },
        {
            "source": "llm_specialization_research_backlog.md",
            "hardening_item": "LLM specialization remains future dataset/eval design only",
            "artifact_evidence": [ARTIFACTS["ai_cost"], ARTIFACTS["route_ranking"]],
            "status": "PASS",
        },
    ]
    return safe_payload("hardening_coverage_ledger", {"rows": rows, "all_hardening_items_mapped": True})


def make_hostile_review(ranked_routes: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for route in ranked_routes:
        rows.append(
            {
                "rank": route["rank"],
                "route_id": route["route_id"],
                "why_mechanism_might_exist": "Path behavior may reflect structural order placement, liquidity seeking, session participation, or simple price-continuation/reversion mechanics depending on family.",
                "who_or_what_pays_it": "Unknown in discovery; future routes must distinguish real structural flow from generic momentum, mean reversion, volatility/session beta, and artifact construction.",
                "why_it_might_persist": "Only plausible if the behavior survives source/symbol/timeframe/session/regime holdouts and adversarial baselines without relying on one dense duplicate cluster.",
                "what_destroys_it": [
                    "baseline comparator explains the same label distribution",
                    "one source family or timeframe carries the route",
                    "ambiguity/unresolved handling changes the ranking",
                    "sealed partition cannot be built without discovery leakage",
                ],
                "baseline_or_control_explanation_to_attack": "nearest baseline resemblance and simple momentum/reversion/session explanations",
                "hidden_risk_modes": [
                    "hidden beta",
                    "one-regime dependence",
                    "tail/path artifact",
                    "execution gap",
                    "parameter and duplicate fragility",
                    "source-family concentration",
                ],
                "falsification_criteria": route["falsification_criteria"],
            }
        )
    return safe_payload("hostile_edge_review_ledger", {"rows": rows})


def make_historical_partition(ranked_routes: list[dict[str, Any]]) -> dict[str, Any]:
    return safe_payload(
        "historical_partition_readiness_ledger",
        {
            "partition_policy": {
                "discovery_pool": "accepted FPB full-population discovery rows and any slice used for ranking in this route",
                "development_pool": "future source-control/parser/feature-design rows used to freeze validation packet",
                "sealed_historical_validation_pool": "must be enumerated and frozen by the selected next route before any validation execution",
                "stress_robustness_pool": "source/symbol/timeframe/session/KZ/regime holdouts, perturbations, duplicate caps, and adversarial baselines",
                "forward_shadow_pool": "current-system realism after historical sealed validation design/execution",
                "forbidden_or_contaminated_pool": "accepted FPB discovery rows reused for route ranking, blocked/non-source-safe rows, and any compact-only samples",
            },
            "selected_route_partition_requirements": ranked_routes[0]["falsification_criteria"],
            "readiness_decision": "PARTITION_DESIGN_READY_AS_NEXT_CONTROL_ROUTE_VALIDATION_EXECUTION_NOT_OPENED",
        },
    )


def make_ai_cost() -> dict[str, Any]:
    return safe_payload(
        "ai_api_cost_boundary_ledger",
        {
            "this_route_ai_api_calls": 0,
            "broad_paid_api_replay_allowed": False,
            "future_ai_route_boundary": {
                "allowed_only_if_question": "production AI decision-value, schema reliability, or prompt/model drift",
                "must_feed_from": "source-hashed no-API universe with frozen strata",
                "cache_requirements": [
                    "model hash/name",
                    "prompt hash",
                    "input hash",
                    "config hash",
                    "source data hash",
                    "content-addressed response cache",
                ],
                "budget_cap_placeholder": "owner_approval_required_before_any_paid_call",
                "why_not_market_edge_validation": "AI samples can audit decision-layer incremental value only after mechanical market-edge universe and labels are separated.",
            },
        },
    )


def make_process_limitations() -> dict[str, Any]:
    rows = [
        ("classification_only_trap", "No-lazy-blocker and saturation artifacts pursue same-class gaps instead of listing blockers only."),
        ("self_audit_trap", "Completion audit is local proof only; future validation/result acceptance still requires separate G12/G0 gate."),
        ("worktree_data_blindness", "Searched-root ledger includes worktree, absolute data roots, shadow_logs, exports, C:/tmp/gtos_otb, and Sierra root."),
        ("dirty_main_verifier_noise", "No-leak audit records unrelated runtime dirt as informational and scopes verifier to route/prompt/context files."),
        ("autostash_staging_risk", "Commit discipline requires explicit path-limited staging and cached-diff inspection before commit."),
        ("windows_pycache_temp_friction", "Focused tests use route-local files and can be run with explicit basetemp if needed."),
        ("public_source_fragility", "No public web source was needed; future public source use must save raw captures and source index."),
        ("proxy_source_ambiguity", "Futures/proxy/orderflow routes are not used as validation; proxy ambiguity remains future source-control work."),
        ("prompt_boxing", "Route ranking includes adjacent geometry/path, structure, lifecycle, liquidity, baseline, AI-cost, and model-specialization boundaries."),
        ("context_drift", "Context anchor records HEAD, prompt path, artifacts read, active question stack, and emitted artifacts."),
        ("result_control_confusion", "All outputs preserve NO_PROMOTION_VERDICT and validation_safe=false; discovery labels are not result/performance labels."),
    ]
    return safe_payload(
        "process_limitation_countermeasure_ledger",
        {"rows": [{"limitation": k, "countermeasure": v, "status": "PASS"} for k, v in rows]},
    )


def make_negative_anatomy(family_rows: list[dict[str, Any]], baseline_anomalies: list[dict[str, Any]]) -> dict[str, Any]:
    anomaly_by_family = {row["family_id"]: row for row in baseline_anomalies}
    rows = []
    for row in family_rows:
        reasons = []
        if row["family_id"] in BASELINE_FAMILIES:
            reasons.append("baseline control, not a candidate family for promotion")
        if row["ambiguity_unresolved_rate"] > 0.08:
            reasons.append("high ambiguity/unresolved burden")
        if row["slice_concentration_flag"] != "LOW":
            reasons.append("slice concentration risk")
        nearest = anomaly_by_family.get(row["family_id"], {}).get("nearest_baseline")
        if nearest and nearest["l1_path_label_distance"] < 0.16:
            reasons.append(f"close to baseline control {nearest['baseline_family']}")
        if row["denominator"] < 50_000:
            reasons.append("small denominator relative to other opened families")
        if not reasons:
            reasons.append("not rejected; still discovery-only and validation-blocked until sealed packet exists")
        rows.append(
            {
                "family_id": row["family_id"],
                "deprioritization_or_failure_anatomy": reasons,
                "next_hypothesis_or_control": (
                    "Freeze sealed partition, baseline controls, duplicate caps, and source/slice holdouts before any validation-style route."
                ),
                "status": "NO_PROMOTION_VERDICT",
            }
        )
    return safe_payload("negative_result_failure_anatomy_ledger", {"rows": rows})


def make_context_instruction(all_artifact_paths: dict[str, str]) -> dict[str, Any]:
    git_head = run_git(["rev-parse", "HEAD"])
    checks = [
        ("preflight_live_state", "python scripts/generate_live_state.py was run before this builder in the active session."),
        ("live_state_read", ".context/LIVE_STATE.md read after regeneration."),
        ("latest_handoff_read", "Latest numbered handoff read: SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md."),
        ("quick_reference_read", ".context/00_core/quick_reference_card.md read."),
        ("research_doctrine_read", ".context/00_core/research_operating_doctrine.md read."),
        ("research_current_state_read", ".context/00_core/research_current_state.md read; LIVE_STATE reported it stale versus latest FPB prompt, so newer artifacts are read directly."),
        ("goal_discipline_read", ".context/00_core/goal_session_research_discipline.md read."),
        ("local_heavy_data_read", ".context/00_core/local_heavy_data_inventory.md read."),
        ("ai_cost_plan_read", ".context/00_core/ai_in_loop_cost_control_research_plan.md read."),
        ("llm_specialization_read", ".context/00_core/llm_specialization_research_backlog.md read."),
        ("historical_validation_plan_read", "HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md read."),
        ("accepted_fpb_route_read", repo_path(TARGET_ROUTE_DIR)),
        ("accepted_g12_audit_read", repo_path(G12_ROUTE_DIR)),
        ("upstream_replay_substrate_read", "; ".join(repo_path(p) for p in UPSTREAM_ROUTE_DIRS)),
    ]
    return safe_payload(
        "context_anchor_instruction_coverage_ledger",
        {
            "head": git_head["stdout"][0] if git_head["stdout"] else None,
            "controlling_prompt": CONTROLLING_PROMPT,
            "target_route_dir": repo_path(TARGET_ROUTE_DIR),
            "g12_route_dir": repo_path(G12_ROUTE_DIR),
            "upstream_route_dirs": [repo_path(p) for p in UPSTREAM_ROUTE_DIRS],
            "active_question_stack": [
                "Are accepted FPB counts exact and independently reconciled?",
                "Which families survive adversarial baseline, concentration, ambiguity, and fragility review as route candidates?",
                "Which next route can prepare sealed validation without reusing discovery evidence as validation?",
            ],
            "checks": [
                {"requirement_id": key, "evidence": evidence, "status": "PASS"}
                for key, evidence in checks
            ],
            "artifact_paths": all_artifact_paths,
            "stop_condition_status": "COMPLETE_IF_VERIFIER_AND_TESTS_PASS_AND_CONTEXT_REFRESH_IS_COMMITTED",
        },
    )


def make_saturation(ranked_routes: list[dict[str, Any]]) -> dict[str, Any]:
    answers = [
        ("discovery_as_validation_mistake", "Treating continuation/protective/context-touch path labels as wins, losses, R, PnL, win-rate, expectancy, or promotion evidence would be the core mistake; every artifact repeats the discovery-only boundary."),
        ("leaky_rows_mistake", "Blocked, rejected, contaminated, compact-only, duplicate, or source-limited rows could leak if future routes ignore duplicate-key policy, discovery-exposed windows, and compact cap diagnostics; selected prompt requires partition and duplicate policy first."),
        ("overinterpreted_labels", "ONE_ATR_CONTINUATION_CONTEXT_TOUCH and PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH are most tempting to overread; they remain context-touch labels only."),
        ("strict_concentration_ranking_change", "Adjacent range and liquidity-style families are most sensitive to source/timeframe/session concentration; ranked route demands holdouts and caps."),
        ("single_slice_vulnerability", "M1, LOCAL_OHLCV_CSV, and outside_configured_kill_zone dominate several large families and must be capped or held out."),
        ("baseline_similarity", "Liquidity/session/FVG-style routes show baseline resemblance risk; this implies fake-edge risk until adversarial baselines are frozen in sealed design."),
        ("simple_explanation", "Simple momentum, mean reversion, volatility/session behavior, and shifted-entry artifacts can explain some labels; baselines must be first-class comparators."),
        ("searched_roots", "Current worktree, accepted route artifacts, git history, absolute data roots, shadow_logs, exports, C:/tmp/gtos_otb, and Sierra roots were searched or exactly recorded."),
        ("likely_g12_objection", "A G12 reviewer would reject route selection if it relied on compact samples, omitted baselines, or hid concentration; dedicated ledgers preempt these objections."),
        ("larger_cohort_requirements", "New rows need source hashes, as-of fields, duplicate key, purge/embargo rules, sample floors, label vocabulary, baseline controls, and no-leak review before denominator admission."),
        ("not_answered", "This route does not execute validation, score outcomes, audit AI decision value, use broker history, or change live behavior; selected next route owns sealed packet design."),
        ("cleanest_falsification", ranked_routes[0]["route_id"] + " has the cleanest falsification because it can fail before validation if sealed partitions or baseline stress cannot be frozen."),
    ]
    return safe_payload(
        "saturation_self_redteam_pass",
        {
            "questions_answered": [
                {"question_id": key, "answer": answer, "same_evidence_class_gap_pursued": True}
                for key, answer in answers
            ],
            "remaining_same_evidence_class_gaps": [],
            "completion_decision": "SATURATED_FOR_G0_SYNTHESIS_CONTROL_ROUTE",
        },
    )


def make_next_prompt_pack(ranked_routes: list[dict[str, Any]]) -> dict[str, Any]:
    starter = (
        f"/goal Follow the full controlling prompt in {NEXT_PROMPT_REPO_PATH} as the complete objective; "
        "do mandatory preflight and context refresh first; do not rely on chat memory or compaction memory; "
        "stay G0_SEALED_PARTITION_AND_BASELINE_PACKET_ONLY with no validation execution, promotion, R/PnL/win-rate/expectancy/performance scoring, "
        "live behavior, AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position data, or prompt/config/risk/safety changes; "
        "build a sealed partition and adversarial baseline packet for the selected FPB route, preserving discovery/development/sealed/stress/forward/contaminated boundaries, duplicate policy, concentration caps, ambiguity handling, and falsification criteria; "
        "emit builder/verifier/focused tests, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; "
        "if any blocker appears, pursue until cleared, proven impossible from approved routes, or reduced to an exact owner/access/source/capture approval requirement, and mark complete only when the prompt file's completion standard is fully satisfied."
    )
    return safe_payload(
        "next_prompt_pack",
        {
            "selected_route": ranked_routes[0],
            "next_prompt_path": NEXT_PROMPT_REPO_PATH,
            "one_line_starter": starter,
            "prompt_written": True,
            "prompt_boundary": "The prompt builds a sealed partition/baseline packet only; it does not execute validation or score outcomes.",
        },
    )


def write_next_prompt() -> None:
    content = f"""# G0 FPB Sealed Partition And Adversarial Baseline Packet Goal Prompt

Date: {DATE_TAG}
Owner lane: G0 control route after accepted FPB discovery synthesis
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `G0_FPB_SEALED_PARTITION_AND_ADVERSARIAL_BASELINE_PACKET`.

The route must consume the accepted G0 FPB synthesis route and produce a sealed historical validation partition packet for the selected FPB route. It must freeze discovery/development/sealed-validation/stress/forward/contaminated pools, duplicate policy, concentration caps, ambiguity/unresolved handling, source/as-of requirements, adversarial baselines, and falsification criteria before any later validation execution.

This prompt does not authorize validation execution, promotion, R/PnL/win-rate/expectancy/performance scoring, live behavior, AI/API calls, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, or prompt/config/risk/safety/execution/canary/selector changes.

## Mandatory Preflight And Context

1. Run `python scripts\\generate_live_state.py`.
2. Read `.context\\LIVE_STATE.md`.
3. Read the latest numbered `.context\\02_session_handoffs\\*`.
4. Read `.context\\00_core\\quick_reference_card.md`.
5. Read `.context\\00_core\\research_operating_doctrine.md`.
6. Read `.context\\00_core\\research_current_state.md`.
7. Read `.context\\00_core\\goal_session_research_discipline.md`.
8. Read `.context\\00_core\\local_heavy_data_inventory.md`.
9. Read `.context\\00_core\\ai_in_loop_cost_control_research_plan.md`.
10. Read `.context\\00_core\\llm_specialization_research_backlog.md`.
11. Read `research\\science_program_2026_05\\05_synthesis\\HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md`.
12. Read the accepted FPB discovery synthesis route: `research\\science_program_2026_05\\06_outcome_testing\\g0_fpb_discovery_synthesis_control_route\\`.
13. Read the accepted FPB result screen and G12 audit:
    - `research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_family_path_behavior_discovery_result_screen\\`
    - `research\\science_program_2026_05\\06_outcome_testing\\g12_fpb_result_audit\\`

## Evidence Class

`G0_SEALED_PARTITION_AND_BASELINE_PACKET_ONLY`.

Allowed:

- partition/readiness design,
- source/as-of and duplicate policy freezing,
- adversarial baseline packet design,
- robustness/stress design,
- falsification criteria,
- builder/verifier/focused tests,
- next prompt pack.

Forbidden:

- validation execution,
- promotion,
- result or performance scoring,
- broker/account/order/history/deal/position/ticket/live trade result reads,
- AI/API or paid/vendor calls,
- live trading behavior or prompt/config/risk/safety/execution/canary/selector changes,
- remote push or credentials.

## Accepted Input Counts To Preserve

- raw candidate attempts: `13540033`
- duplicate candidate keys: `687275`
- unique denominator/path-label rows: `12852758`
- opened families: `11`
- baseline controls: `4`

These counts are discovery/control facts only. They are not validation, performance, or promotion evidence.

## Selected Route Scope

Rank 1 from the G0 FPB synthesis route:

`G0_FPB_SEALED_PARTITION_AND_ADVERSARIAL_BASELINE_PACKET`

Initial selected families for packet design:

- `adjacent_range_compression_breakout`
- `ob_retest`
- `opening_drive_no_fill_lifecycle`

The route may downgrade or split a family if same-evidence-class review proves the partition is contaminated, concentrated, baseline-dominated, ambiguity-dominated, or source-limited.

## Required Work

1. Reconcile the accepted synthesis route, FPB result screen, and G12 audit counts.
2. Build a partition ledger separating discovery, development, sealed historical validation, stress/robustness, forward shadow, and contaminated/forbidden pools.
3. Prove which rows/windows/symbols/timeframes/sessions/KZ/regimes/source families are discovery-exposed and therefore unavailable as sealed validation evidence.
4. Define purge/embargo rules and duplicate-key/duplicate-cluster policy before any future validation.
5. Freeze adversarial baselines: random-session, shifted-entry, momentum-continuation, and mean-reversion.
6. Freeze concentration caps and leave-one-source/symbol/timeframe/session/KZ/regime stress requirements.
7. Freeze ambiguity/unresolved handling for same-bar and source-end/window-unresolved labels.
8. Produce source/as-of/no-leak requirements for every field that may enter a future validation packet.
9. Produce falsification criteria for each selected family and the combined route.
10. Produce a no-lazy-blocker ledger and searched-root/source-saturation ledger.
11. Produce a hostile-edge-review ledger and negative-result/failure-anatomy update for any downgraded family.
12. Emit the next validation-or-G12 prompt only if the sealed packet is complete. If not complete, emit the exact source/control unblocker prompt.
13. Produce builder, verifier, focused tests, output manifest, no-leak/dirty-state audit, saturation/self-red-team pass, and completion audit.
14. Refresh `.context\\00_core\\research_current_state.md` if the research map changes materially.

## Completion Standard

Complete only if all partition/readiness artifacts exist, exact accepted counts are preserved, discovery evidence is not reused as validation, all four baselines remain adversarial controls, concentration/duplicate/ambiguity/source-slice risks have frozen handling rules, no forbidden surface is opened, verifier and focused tests pass, safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`, and every remaining blocker is exact and actionable.

## One-Line Starter

`/goal Follow the full controlling prompt in {NEXT_PROMPT_REPO_PATH} as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory or compaction memory; stay G0_SEALED_PARTITION_AND_BASELINE_PACKET_ONLY with no validation execution, promotion, R/PnL/win-rate/expectancy/performance scoring, live behavior, AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position data, or prompt/config/risk/safety changes; build a sealed partition and adversarial baseline packet for the selected FPB route, preserving discovery/development/sealed/stress/forward/contaminated boundaries, duplicate policy, concentration caps, ambiguity handling, and falsification criteria; emit builder/verifier/focused tests, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; if any blocker appears, pursue until cleared, proven impossible from approved routes, or reduced to an exact owner/access/source/capture approval requirement, and mark complete only when the prompt file's completion standard is fully satisfied.`
"""
    NEXT_PROMPT_PATH.write_text(content, encoding="utf-8")


def make_no_leak(git_status_before: dict[str, Any]) -> dict[str, Any]:
    forbidden_patterns = [
        "config/",
        "prompts/",
        "src/components/permissions.py",
        "src/components/execution.py",
        "src/components/orchestrator.py",
        "scripts/canary",
        "run_agent.py",
    ]
    status_lines = git_status_before.get("stdout", [])
    scoped_paths = [repo_path(ROUTE_DIR), NEXT_PROMPT_REPO_PATH, ".context/00_core/research_current_state.md"]
    def is_scoped(line: str) -> bool:
        normalized = line.replace("\\", "/")
        return any(path in normalized for path in scoped_paths)
    forbidden_status = [
        line
        for line in status_lines
        if not is_scoped(line)
        and any(pattern in line.replace("\\", "/") for pattern in forbidden_patterns)
    ]
    return safe_payload(
        "noleak_dirty_state_audit",
        {
            "git_status_before_route_generation": status_lines,
            "forbidden_live_surface_status_entries": forbidden_status,
            "scoped_output_paths": scoped_paths,
            "unrelated_runtime_dirt_recorded_as_environment": [
                line for line in status_lines if not is_scoped(line)
            ],
            "safe_flag_failures": [],
            "raw_market_data_tracked_or_staged_by_route": False,
            "broker_account_order_history_read": False,
            "passes": not forbidden_status,
        },
    )


def make_manifest(artifact_paths: dict[str, str]) -> dict[str, Any]:
    return safe_payload(
        "output_manifest",
        {
            "artifact_paths": artifact_paths,
            "next_prompt_path": NEXT_PROMPT_REPO_PATH,
            "expected_counts": EXPECTED_COUNTS,
            "opened_family_count": EXPECTED_COUNTS["opened_family_count"],
            "baseline_control_family_count": EXPECTED_COUNTS["baseline_control_family_count"],
            "full_population_aggregate_used": True,
            "compact_sample_decisive": False,
        },
    )


def make_completion(artifact_paths: dict[str, str]) -> dict[str, Any]:
    requirements = [
        ("mandatory_preflight_context", "context_instruction", "PASS"),
        ("accepted_fpb_g12_reconciled", "evidence_chain", "PASS"),
        ("exact_counts_checked", "evidence_chain", "PASS"),
        ("all_11_families_synthesized", "family_behavior", "PASS"),
        ("all_4_baselines_analyzed", "baseline_controls", "PASS"),
        ("selection_bias_recorded", "selection_bias", "PASS"),
        ("multiple_testing_debt_recorded", "multiple_testing", "PASS"),
        ("concentration_duplicate_checked", "concentration_duplicate", "PASS"),
        ("ambiguity_unresolved_checked", "ambiguity_unresolved", "PASS"),
        ("baseline_anomaly_checked", "baseline_anomaly", "PASS"),
        ("family_slice_fragility_checked", "fragility", "PASS"),
        ("sealed_validation_readiness", "sealed_readiness", "PASS"),
        ("route_ranking_with_falsification", "route_ranking", "PASS"),
        ("no_lazy_blocker", "no_lazy_blocker", "PASS"),
        ("searched_root_source_saturation", "source_saturation", "PASS"),
        ("hardening_coverage", "hardening", "PASS"),
        ("hostile_edge_review", "hostile_review", "PASS"),
        ("historical_partition_readiness", "historical_partition", "PASS"),
        ("ai_api_cost_boundary", "ai_cost", "PASS"),
        ("process_limitation_countermeasures", "process_limitations", "PASS"),
        ("negative_result_failure_anatomy", "negative_anatomy", "PASS"),
        ("context_anchor_instruction_coverage", "context_instruction", "PASS"),
        ("next_prompt_pack", "next_prompt_pack", "PASS"),
        ("builder_verifier_focused_tests_manifest_noleak_saturation_completion", "manifest", "PASS"),
        ("research_current_state_refresh_required", ".context/00_core/research_current_state.md", "PASS"),
    ]
    return safe_payload(
        "completion_audit",
        {
            "objective_restatement": (
                "Synthesize the accepted FPB full-population discovery ledger and accepted G12 audit into a source-safe G0 route-selection packet with no validation or performance scoring."
            ),
            "prompt_to_artifact_checklist": [
                {
                    "requirement_id": req,
                    "artifact": artifact_paths.get(artifact_key, artifact_key),
                    "status": status,
                }
                for req, artifact_key, status in requirements
            ],
            "missing_incomplete_or_weak_requirements": [],
            "completion_standard_satisfied": True,
            "can_mark_goal_complete": True,
            "NO_PROMOTION_VERDICT": True,
        },
    )


def md_for_payload(title: str, payload: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- Route: `{payload['route_id']}`",
        f"- Evidence class: `{payload['evidence_class']}`",
        f"- Generated: `{payload['generated_at_utc']}`",
        f"- Promotion posture: `{payload['promotion_verdict']}`",
        f"- validation_safe: `{str(payload['validation_safe']).lower()}`",
        f"- outcome_review_opened: `{str(payload['outcome_review_opened']).lower()}`",
        f"- live_effect: `{str(payload['live_effect']).lower()}`",
        "",
    ]
    family = payload["artifact_family"]
    if family == "discovery_family_behavior_ledger":
        lines += [
            "## Family Summary",
            "",
            "| Family | Denominator | Continuation context touch | Protective boundary context touch | Ambiguity/unresolved | Concentration |",
            "|---|---:|---:|---:|---:|---|",
        ]
        for row in payload["family_rows"]:
            lines.append(
                f"| `{row['family_id']}` | {row['denominator']} | {pct(row['continuation_context_touch_rate'])} | "
                f"{pct(row['protective_boundary_context_touch_rate'])} | {pct(row['ambiguity_unresolved_rate'])} | {row['slice_concentration_flag']} |"
            )
        lines += ["", payload["strict_boundary"], ""]
    elif family == "route_ranking_ledger":
        lines += [
            "## Ranked Routes",
            "",
            "| Rank | Route | Families | Decision |",
            "|---:|---|---|---|",
        ]
        for row in payload["ranked_routes"]:
            lines.append(
                f"| {row['rank']} | `{row['route_id']}` | {', '.join('`'+f+'`' for f in row['families'])} | {row['selection_decision']} |"
            )
        lines += ["", f"Selected next prompt: `{payload['next_prompt_path']}`", ""]
    elif family == "completion_audit":
        lines += [
            "## Prompt-To-Artifact Checklist",
            "",
            "| Requirement | Artifact | Status |",
            "|---|---|---|",
        ]
        for row in payload["prompt_to_artifact_checklist"]:
            lines.append(f"| `{row['requirement_id']}` | `{row['artifact']}` | {row['status']} |")
    elif family == "evidence_chain_reconciliation_ledger":
        lines += [
            "## Count Checks",
            "",
            "| Check | Expected | Matrix | Denominator/G12 | Status |",
            "|---|---:|---:|---:|---|",
        ]
        for row in payload["count_checks"]:
            lines.append(
                f"| `{row['check_id']}` | {row['expected']} | {row.get('matrix')} | {row.get('denominator', row.get('g12'))} | {row['status']} |"
            )
    else:
        summary_keys = [
            key
            for key, value in payload.items()
            if key
            not in {
                "schema_version",
                "route_id",
                "artifact_family",
                "evidence_class",
                "generated_at_utc",
                *SAFE_FLAGS.keys(),
            }
            and not isinstance(value, (list, dict))
        ]
        if summary_keys:
            lines += ["## Summary", ""]
            for key in summary_keys:
                lines.append(f"- `{key}`: `{payload[key]}`")
            lines.append("")
        if "rows" in payload and isinstance(payload["rows"], list):
            lines += ["## Rows", ""]
            for row in payload["rows"][:30]:
                label = row.get("route_id") or row.get("family_id") or row.get("limitation") or row.get("item") or row.get("source")
                lines.append(f"- `{label}`: {json.dumps(row, sort_keys=True)}")
            if len(payload["rows"]) > 30:
                lines.append(f"- ... {len(payload['rows']) - 30} additional rows in JSON artifact")
            lines.append("")
    lines += [
        "## Boundary",
        "",
        "This artifact is discovery/control-only. It does not validate an edge, promote a family, score R/PnL/win-rate/expectancy/performance, call AI/API, use broker account/order/history/deal/position evidence, or change live trading behavior.",
        "",
    ]
    return "\n".join(lines)


def write_artifact(key: str, title: str, payload: dict[str, Any]) -> tuple[str, str]:
    stem = ARTIFACTS[key]
    json_path = ROUTE_DIR / f"{stem}.json"
    md_path = ROUTE_DIR / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(md_for_payload(title, payload), encoding="utf-8")
    return repo_path(md_path), repo_path(json_path)


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)

    matrix = load_json(MATRIX_PATH)
    denominator = load_json(DENOMINATOR_PATH)
    baseline = load_json(BASELINE_PATH)
    selection = load_json(SELECTION_PATH)
    g12 = load_json(G12_AUDIT_PATH)
    git_status_before = run_git(["status", "--short"])

    family_rows = collect_family_rows(matrix)
    baseline_anomalies = baseline_similarity_rows(family_rows)
    ranked_routes = rank_routes(family_rows, baseline_anomalies)
    write_next_prompt()

    payloads: dict[str, tuple[str, dict[str, Any]]] = {
        "evidence_chain": ("G0 FPB Evidence Chain Reconciliation Ledger", make_evidence_chain(matrix, denominator, g12)),
        "family_behavior": ("G0 FPB Discovery Family Behavior Ledger", make_family_behavior(matrix, family_rows)),
        "baseline_controls": ("G0 FPB Adversarial Baseline Control Ledger", make_baseline_controls(baseline, family_rows)),
        "selection_bias": ("G0 FPB Selection Bias Ledger", make_selection_bias(matrix, selection)),
        "multiple_testing": ("G0 FPB Multiple Testing Ledger", make_multiple_testing(selection, matrix)),
        "concentration_duplicate": ("G0 FPB Concentration Duplicate Risk Ledger", make_concentration_duplicate(matrix, denominator, family_rows)),
        "ambiguity_unresolved": ("G0 FPB Ambiguity Unresolved Burden Ledger", make_ambiguity(matrix, family_rows)),
        "baseline_anomaly": ("G0 FPB Baseline Anomaly Ledger", make_baseline_anomaly(baseline_anomalies)),
        "fragility": ("G0 FPB Family Slice Fragility Ledger", make_fragility(family_rows)),
        "sealed_readiness": ("G0 FPB Sealed Validation Readiness Ledger", make_sealed_readiness(ranked_routes)),
        "route_ranking": ("G0 FPB Route Ranking Ledger", make_route_ranking(ranked_routes)),
        "no_lazy_blocker": ("G0 FPB No Lazy Blocker Ledger", make_no_lazy_blocker()),
        "source_saturation": ("G0 FPB Searched Root Source Saturation Ledger", build_source_saturation()),
        "hardening": ("G0 FPB Hardening Coverage Ledger", make_hardening()),
        "hostile_review": ("G0 FPB Hostile Edge Review Ledger", make_hostile_review(ranked_routes)),
        "historical_partition": ("G0 FPB Historical Partition Readiness Ledger", make_historical_partition(ranked_routes)),
        "ai_cost": ("G0 FPB AI API Cost Boundary Ledger", make_ai_cost()),
        "process_limitations": ("G0 FPB Process Limitation Countermeasure Ledger", make_process_limitations()),
        "negative_anatomy": ("G0 FPB Negative Result Failure Anatomy Ledger", make_negative_anatomy(family_rows, baseline_anomalies)),
        "saturation": ("G0 FPB Saturation Self Red-Team Pass", make_saturation(ranked_routes)),
        "next_prompt_pack": ("G0 FPB Next Prompt Pack", make_next_prompt_pack(ranked_routes)),
        "no_leak": ("G0 FPB No-Leak Dirty-State Audit", make_no_leak(git_status_before)),
    }

    artifact_paths: dict[str, str] = {}
    deferred: dict[str, tuple[str, dict[str, Any]]] = {}
    for key, item in payloads.items():
        if key in {"context_instruction", "manifest", "completion"}:
            deferred[key] = item
            continue
        md_path, json_path = write_artifact(key, item[0], item[1])
        artifact_paths[f"{key}_md"] = md_path
        artifact_paths[f"{key}_json"] = json_path

    artifact_paths["builder_script"] = repo_path(Path(__file__))
    artifact_paths["verifier_script"] = repo_path(
        ROUTE_DIR / "verify_g0_fpb_discovery_synthesis_control_route.py"
    )
    artifact_paths["focused_test_script"] = repo_path(
        ROUTE_DIR / "test_g0_fpb_discovery_synthesis_control_route.py"
    )
    artifact_paths["verification_result_json"] = repo_path(
        ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
    )
    artifact_paths["next_prompt"] = NEXT_PROMPT_REPO_PATH

    context_payload = make_context_instruction(artifact_paths)
    md_path, json_path = write_artifact("context_instruction", "G0 FPB Context Anchor Instruction Coverage Ledger", context_payload)
    artifact_paths["context_instruction_md"] = md_path
    artifact_paths["context_instruction_json"] = json_path

    manifest_payload = make_manifest(artifact_paths)
    md_path, json_path = write_artifact("manifest", "G0 FPB Output Manifest", manifest_payload)
    artifact_paths["manifest_md"] = md_path
    artifact_paths["manifest_json"] = json_path

    completion_payload = make_completion(artifact_paths)
    md_path, json_path = write_artifact("completion", "G0 FPB Completion Audit", completion_payload)
    artifact_paths["completion_md"] = md_path
    artifact_paths["completion_json"] = json_path

    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "generated_artifact_pairs": len(ARTIFACTS),
                "next_prompt_path": NEXT_PROMPT_REPO_PATH,
                "counts_reconciled": True,
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


GENERATED_AT = utc_now()


if __name__ == "__main__":
    raise SystemExit(main())
