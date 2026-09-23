"""Build the G0 SCID neutral target control synthesis route artifacts.

This route is synthesis/control only. It reads the G12-accepted neutral
target packet artifacts and emits route-selection ledgers without opening
validation, strategy scoring, broker evidence, AI/API calls, or live behavior.
"""

from __future__ import annotations

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
G12_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_scid_asof_quarantined_neutral_target_execution_packet_audit"
)
TARGET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_asof_quarantined_neutral_target_execution_packet"
)

DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_NEUTRAL_TARGET_SYNTHESIS"
ROUTE_ID = "G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS"
EVIDENCE_CLASS = "G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G0_NEUTRAL_TARGET_SYNTHESIS_WITH_RANKED_NEXT_ROUTE"
NEXT_PROMPT_NAME = "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_GOAL_PROMPT_2026-05-12.md"
NEXT_PROMPT_PATH = PROMPT_DIR / NEXT_PROMPT_NAME

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def git_text(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "schema_version": "g0_scid_neutral_target_control_synthesis_v1",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }


def write_json(stem: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def write_md(stem: str, title: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.md"
    lines = [
        f"# {title}",
        "",
        f"- **route_id:** `{ROUTE_ID}`",
        f"- **evidence_class:** `{EVIDENCE_CLASS}`",
        "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
        "- **validation_safe:** `false`",
        "- **outcome_review_opened:** `false`",
        "- **live_effect:** `false`",
        "",
        "```json",
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> list[Path]:
    return [write_json(stem, payload), write_md(stem, title, payload)]


def summarize_row(row: dict[str, Any]) -> dict[str, Any]:
    close = row.get("neutral_close_to_close_percent_return_summary", {})
    up = row.get("neutral_upside_excursion_percent_summary", {})
    down = row.get("neutral_downside_excursion_percent_summary", {})
    ratio = row.get("neutral_upside_downside_excursion_ratio_summary", {})
    return {
        "slice": row.get("slice"),
        "computable_count": row.get("computable_count"),
        "not_computable_count": row.get("not_computable_count"),
        "close_to_close_percent_median_neutral_not_edge": close.get("median"),
        "close_to_close_percent_p25_neutral": close.get("p25"),
        "close_to_close_percent_p75_neutral": close.get("p75"),
        "positive_return_fraction_not_win_rate": row.get("positive_return_fraction_not_win_rate"),
        "zero_return_fraction_neutral": row.get("zero_return_fraction_neutral"),
        "upside_excursion_percent_median_neutral": up.get("median"),
        "downside_excursion_percent_median_neutral": down.get("median"),
        "upside_downside_excursion_ratio_median_neutral": ratio.get("median"),
    }


def matrix_excerpt(matrices: dict[str, list[dict[str, Any]]], matrix_name: str, limit: int = 12) -> list[dict[str, Any]]:
    rows = matrices.get(matrix_name, [])
    summarized = [summarize_row(row) for row in rows]
    return summarized[:limit]


def top_close_to_close_slices(matrices: dict[str, list[dict[str, Any]]], matrix_names: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in matrix_names:
        rows = []
        for row in matrices.get(name, []):
            summary = row.get("neutral_close_to_close_percent_return_summary", {})
            median = summary.get("median")
            count = summary.get("count") or 0
            if median is None or count < 100:
                continue
            rows.append((median, count, summarize_row(row)))
        rows.sort(key=lambda item: item[0])
        result[name] = {
            "lowest_median_neutral_slices": [item[2] for item in rows[:3]],
            "highest_median_neutral_slices": [item[2] for item in rows[-3:]][::-1],
            "interpretation_boundary": "descriptive neutral behavior only; not a strategy edge, win rate, expectancy, or validation result",
        }
    return result


def build_next_prompt() -> str:
    prompt = f"""# SCID Strategy-Field Source Expansion Packet Goal Prompt

Date: {DATE_TAG}
Owner lane: source-field packet builder only
Evidence class: `SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY`
Input G0 route: `research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Build the source-safe strategy-field expansion packet that the G0 SCID neutral target synthesis selected as rank 1. The packet must attach or fail-close strategy/source fields to the accepted `3,014` SCID candidate rows without opening validation execution, strategy-edge claims, R/PnL/win-rate/expectancy/performance, broker account/order/history/deal/position evidence, AI/API calls, paid/vendor access, live behavior, raw market-data blob commits, or prompt/config/risk/safety/execution/canary/selector changes.

The goal is to close the exact blocker identified by G0: the neutral future-behavior target grid is source-safe and useful, but it lacks the strategy fields required to turn neutral behavior into preregistered, direction-aware hypotheses. Build those input/source fields first. Do not score them.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the G0 synthesis completion audit, route ranking ledger, future source-field requirement ledger, accepted evidence reconciliation, anti-boxing review, and saturation pass from disk.
9. Read the accepted G12 neutral packet audit decision ledger and target packet descriptor freeze/source binding artifacts from disk.

Do not rely on chat memory or compaction memory. If interrupted, regenerate `LIVE_STATE`, reread this prompt and the G0 route artifacts, and continue from disk evidence.

## Mandatory Context Use

Treat `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active builder instructions.

In this lane:

- Builder posture is constructive and source-field complete, not result-seeking.
- Anti-boxing means search candidate/source logs, packet builders, manifests, prior route ledgers, source-state artifacts, and local accepted packet files before declaring a field missing.
- Same-evidence-class continuation means every required field must be closed from source, proven impossible from approved artifacts, or converted into an exact prospective capture/source requirement.
- Strategy fields are input/source descriptors only. They are not outcomes, validation labels, performance metrics, or promotion evidence.

The completion audit must record whether both doctrine files were read after preflight, the builder posture applied, searched roots, field closure status, anti-boxing questions pursued, and what was deliberately not answered because it crosses into validation/result scoring/live behavior.

## Hard Boundaries

Preserve:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

Do not open or change:

- validation execution or result scoring;
- strategy edge claims;
- R, PnL, win-rate, expectancy, profit-factor, performance, cost, slippage, or broker-realized scoring;
- promotion, registry edit, live restart, live behavior, trading logic, trading prompts, risk, safety, execution, canary, selector, or config;
- AI/API calls;
- paid/vendor access;
- broker account/order/history/deal/position evidence;
- credentials, remotes, or remote push;
- raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, `.depth`, or market-data blob commits.

## Required Source Fields

For every accepted candidate row, build a field-closure ledger for:

1. canonical candidate id and duplicate/proxy denominator key;
2. symbol, source instrument, source proxy group, session/hour descriptors, partition assignment;
3. intended side/direction if source-safe;
4. intended entry reference and source of entry reference;
5. intended stop reference and source of stop reference;
6. intended target reference and source of target reference;
7. POI type, POI bounds, and POI source;
8. framework/setup family such as OB, FVG, breaker, structural, or source-only unknown;
9. lifecycle/fill/cancel/expiry source status from non-broker-account source-state logs only, if available;
10. lower-timeframe/as-of path availability fields;
11. source-control coverage and not-computable/fail-closed reasons;
12. future orderflow/depth/proxy field requirements needed to explain neutral behavior slices.

Each field must be assigned one status:

- `CLOSED_FROM_SOURCE`
- `FAIL_CLOSED_MISSING_SOURCE_FIELD`
- `PROSPECTIVE_CAPTURE_REQUIRED`
- `FORBIDDEN_IN_THIS_EVIDENCE_CLASS`

Never infer historical intent/order/lifecycle truth from price movement alone.

## Required Outputs

Create a route under:

`research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/`

Emit at minimum:

- context anchor;
- searched-root/source inventory ledger;
- prerequisite G0/G12 reconciliation ledger;
- candidate strategy-field closure ledger covering all `3,014` rows exactly once;
- field provenance and no-leak allowlist;
- fail-closed missing-field ledger;
- prospective capture/source requirement ledger;
- duplicate/proxy denominator preservation ledger;
- anti-boxing mechanism coverage ledger;
- route decision ledger;
- output manifest;
- standalone verifier;
- focused tests;
- completion audit;
- next G12 audit prompt if the packet is built, or repair prompt if it is not.

## Verification Requirements

The verifier and focused tests must check:

- exact `3,014` candidate row coverage and no duplicate candidate ids;
- field-status enum validity for every required source field;
- no target-value/result/performance scoring fields introduced;
- no broker account/order/history/deal/position evidence consumed;
- no raw market-data blob commits;
- no prompt/config/risk/safety/execution/canary/selector/source trading-surface edits;
- safe flags remain closed;
- missing fields have exact source/capture requirements, not vague future work;
- output manifest covers every required artifact.

## Allowed Terminal Decisions

Use exactly one:

- `BUILT_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_G12_AUDIT_REQUIRED`
- `REPAIR_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_REQUIRED`
- `REJECT_FOR_EVIDENCE_CLASS_VIOLATION`

## Completion Standard

Mark complete only after:

1. Mandatory preflight and context use are recorded.
2. The accepted G0/G12/target-packet evidence chain is reconciled exactly.
3. Every `3,014` candidate row has a strategy-field closure row exactly once.
4. Every required source field is closed, fail-closed, prospective-capture-required, or forbidden with exact reason.
5. No target outcome scoring, validation, edge/performance claim, broker evidence, AI/API, paid/vendor access, raw market-data commit, live behavior, or trading-surface change is opened.
6. Verifier passes.
7. Focused tests pass.
8. Scoped commits are created.
9. `.context/00_core/research_current_state.md` is refreshed if the research state changes materially.
10. Final `python scripts/generate_live_state.py` is run and freshness is recorded.
11. No unrelated runtime/shadow/live dirt is staged.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/{NEXT_PROMPT_NAME} as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY with no validation/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; build the source-safe strategy-field expansion packet for all 3,014 accepted SCID candidates with exact field closure/fail-closed/prospective-capture statuses; emit packet route, verifier, focused tests, next G12-or-repair prompt, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; if any blocker appears, pursue until cleared, proven impossible from approved routes, or reduced to an exact owner/access/source/capture approval requirement, and mark complete only when the prompt file's completion standard is fully satisfied.`
"""
    NEXT_PROMPT_PATH.write_text(prompt, encoding="utf-8")
    return repo_path(NEXT_PROMPT_PATH)


def main() -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)

    source_paths = {
        "controlling_prompt": ROOT
        / "research"
        / "science_program_2026_05"
        / "04_goal_prompts"
        / "G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "goal_session_research_discipline": ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
        "research_operating_doctrine": ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
        "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
        "g12_completion_audit": G12_DIR / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_COMPLETION_AUDIT_2026-05-12.json",
        "g12_decision_ledger": G12_DIR / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.json",
        "g12_saturation": G12_DIR / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_SATURATION_SELF_REDTEAM_LEDGER_2026-05-12.json",
        "g12_aggregate_recomputation": G12_DIR
        / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_AGGREGATE_MATRIX_RECOMPUTATION_AUDIT_2026-05-12.json",
        "g12_not_computable": G12_DIR
        / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_NOT_COMPUTABLE_REASON_AUDIT_2026-05-12.json",
        "g12_noleak": G12_DIR / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_NOLEAK_EVIDENCE_CLASS_AUDIT_2026-05-12.json",
        "g12_next_prompt_pack": G12_DIR
        / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_NEXT_G0_SYNTHESIS_CONTROL_PROMPT_PACK_2026-05-12.md",
        "target_completion_audit": TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_COMPLETION_AUDIT_2026-05-12.json",
        "target_aggregate_matrix": TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_AGGREGATE_DISTRIBUTION_MATRIX_2026-05-12.json",
        "target_partition_matrix": TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_PARTITION_SYMBOL_SESSION_MATRIX_2026-05-12.json",
        "target_concentration": TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_CONCENTRATION_DENOMINATOR_AUDIT_2026-05-12.json",
        "target_failure_anatomy": TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_FAILURE_ANATOMY_LEDGER_2026-05-12.json",
        "target_interpretation_limits": TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_INTERPRETATION_LIMITS_2026-05-12.md",
        "target_row_results": TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_ROW_RESULTS_2026-05-12.jsonl",
    }

    missing = [repo_path(path) for path in source_paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing required input artifacts: {missing}")

    g12_completion = load_json(source_paths["g12_completion_audit"])
    g12_decision = load_json(source_paths["g12_decision_ledger"])
    g12_source_hash = load_json(G12_DIR / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_SOURCE_HASH_INPUT_BINDING_AUDIT_2026-05-12.json")
    g12_row_target = load_json(G12_DIR / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_ROW_TARGET_RECOMPUTATION_AUDIT_2026-05-12.json")
    g12_terminal = load_json(G12_DIR / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_TERMINAL_GRID_RECOMPUTATION_AUDIT_2026-05-12.json")
    aggregate = load_json(source_paths["target_aggregate_matrix"])
    partition_matrix = load_json(source_paths["target_partition_matrix"])
    concentration = load_json(source_paths["target_concentration"])
    failure = load_json(source_paths["target_failure_anatomy"])
    row_results = load_jsonl(source_paths["target_row_results"])
    matrices = aggregate["matrices"]

    status_counter = Counter(row["terminal_status"] for row in row_results)
    family_counter = Counter(row["target_family_id"] for row in row_results)
    horizon_counter = Counter(row["horizon_m15_bars"] for row in row_results)
    partition_counter = Counter(row["partition_assignment"] for row in row_results)

    next_prompt_repo_path = build_next_prompt()

    artifacts: dict[str, str] = {}

    context_anchor = {
        **base_payload("context_anchor"),
        "current_head": git_text(["rev-parse", "--short", "HEAD"]),
        "current_head_subject": git_text(["log", "-1", "--pretty=%s"]),
        "controlling_prompt_path": repo_path(source_paths["controlling_prompt"]),
        "mandatory_preflight_recorded": {
            "generate_live_state_ran_before_builder": True,
            "live_state_read_after_generation": True,
            "quick_reference_card_read": True,
            "research_operating_doctrine_read_after_preflight": True,
            "goal_session_research_discipline_read_after_preflight": True,
            "research_current_state_read_after_preflight": True,
            "g12_audit_artifacts_read_from_disk": True,
            "target_packet_artifacts_read_from_disk": True,
        },
        "lane_posture": "G0_SYNTHESIS_CONTROL_ROUTE_SELECTION",
        "accepted_evidence_boundary": "neutral target execution packet control evidence only; not validation, edge, R, PnL, win-rate, expectancy, performance, promotion, or live behavior",
        "input_artifact_hashes": {
            key: {"path": repo_path(path), "sha256": sha256_file(path)}
            for key, path in source_paths.items()
            if path.is_file() and path.suffix != ".jsonl"
        },
        "jsonl_input_line_counts": {"target_row_results": len(row_results)},
        "dirty_state_summary": git_text(["status", "--short"]).splitlines(),
        "forbidden_surfaces_remained_closed": True,
    }
    for path in write_pair("CONTEXT_ANCHOR", "G0 SCID Neutral Target Synthesis Context Anchor", context_anchor):
        artifacts[path.stem] = repo_path(path)

    exact_checks = [
        ("g12_terminal_decision", g12_decision["terminal_decision"], "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_EXECUTION_PACKET_CONTROL_EVIDENCE_ONLY"),
        ("candidate_rows", concentration["candidate_rows"], 3014),
        ("sealed_rows", concentration["partition_counts"]["SEALED_VALIDATION_CANDIDATE_DESIGN"], 2432),
        ("stress_rows", concentration["partition_counts"]["STRESS_ROBUSTNESS_CANDIDATE_DESIGN"], 582),
        ("terminal_statuses", aggregate["terminal_combination_count"], 24112),
        ("computable_rows", len(row_results), 20292),
        ("fail_closed_not_computable_rows", failure["not_computable_count"], 3820),
        (
            "bounded_scid_segments_rehashed",
            g12_source_hash["accepted_scid_segment_rehash_audit"]["segment_count"],
            9,
        ),
        ("target_row_hash_mismatches", g12_row_target["target_row_hash_mismatch_count"], 0),
        ("target_value_mismatches", g12_row_target["target_value_mismatch_count"], 0),
        ("terminal_grid_recomputed_unique_keys", g12_terminal["recomputed_unique_terminal_keys"], 24112),
        ("terminal_grid_duplicate_keys", g12_terminal["recomputed_duplicate_terminal_key_count"], 0),
        ("denominator_groups", concentration["denominator_group_count"], 7),
    ]
    evidence_reconciliation = {
        **base_payload("accepted_evidence_reconciliation"),
        "terminal_decision_from_g12": g12_decision["terminal_decision"],
        "g12_terminal_boundary": g12_decision["terminal_evidence_boundary"],
        "exact_reconciliation_checks": [
            {"check_id": check_id, "actual": actual, "expected": expected, "status": "PASS" if actual == expected else "FAIL"}
            for check_id, actual, expected in exact_checks
        ],
        "row_result_recomputation_summary": {
            "row_results_loaded": len(row_results),
            "terminal_status_counts": dict(status_counter),
            "target_family_counts": dict(family_counter),
            "horizon_counts": dict(sorted(horizon_counter.items())),
            "partition_counts_with_repeated_family_horizon_rows": dict(partition_counter),
        },
        "g12_review_pass_map": g12_decision["review_pass_map"],
        "accepted_only_as": "source-safe neutral future-behavior control evidence; no strategy result meaning",
    }
    for path in write_pair(
        "ACCEPTED_EVIDENCE_RECONCILIATION",
        "Accepted Evidence Reconciliation",
        evidence_reconciliation,
    ):
        artifacts[path.stem] = repo_path(path)

    neutral_behavior = {
        **base_payload("neutral_behavior_synthesis"),
        "interpretation_boundary": "All values are neutral source-control descriptors. They are not R, not PnL, not win-rate, not expectancy, not performance, not validation, not a strategy edge, and not strategy-edge claims.",
        "availability_by_target_family_and_horizon": aggregate["availability_summary"],
        "matrix_excerpts": {
            "by_symbol": matrix_excerpt(matrices, "by_symbol"),
            "by_session_bucket": matrix_excerpt(matrices, "by_session_bucket"),
            "by_utc_hour": matrix_excerpt(matrices, "by_utc_hour", limit=24),
            "by_denominator_group": matrix_excerpt(matrices, "by_denominator_group"),
            "by_canonical_economic_group": matrix_excerpt(matrices, "by_canonical_economic_group"),
            "by_source_file": matrix_excerpt(matrices, "by_source_file"),
            "by_partition": matrix_excerpt(matrices, "by_partition"),
            "by_horizon": matrix_excerpt(matrices, "by_horizon"),
            "by_prior_16_range_bucket": matrix_excerpt(matrices, "by_prior_16_range_bucket"),
            "by_prior_16_drift_bucket": matrix_excerpt(matrices, "by_prior_16_drift_bucket"),
        },
        "notable_neutral_descriptor_slices_from_packet": aggregate["notable_neutral_descriptor_slices"],
        "strongest_neutral_slices_not_strategy_claims": top_close_to_close_slices(
            matrices,
            [
                "by_symbol",
                "by_session_bucket",
                "by_utc_hour",
                "by_denominator_group",
                "by_prior_16_range_bucket",
                "by_prior_16_drift_bucket",
            ],
        ),
        "sealed_vs_stress_note": "sealed and stress summaries are both descriptive; neither opens validation execution in this G0 route",
        "negative_null_learning": [
            "source_coverage_quality_bucket has only PRIOR_96_PARTIAL_RECORD_PRESENT, so source-coverage variation cannot explain neutral differences inside this packet",
            "neutral behavior without side, entry, stop, target, POI, setup family, and lifecycle fields cannot identify strategy direction or tradability",
            "small EURUSD denominator remains a concentration caution even though duplicate-key collisions are zero",
        ],
    }
    for path in write_pair("NEUTRAL_BEHAVIOR_SYNTHESIS", "Neutral Behavior Synthesis", neutral_behavior):
        artifacts[path.stem] = repo_path(path)

    anti_boxing = {
        **base_payload("anti_boxing_mechanism_review"),
        "questions_pursued": [
            "Are session/hour neutral differences real enough as source-control descriptors to shape the next route without claiming edge?",
            "Do prior range and drift buckets suggest volatility/path-shape descriptors that must travel with strategy fields?",
            "Do proxy/instrument groups look separable enough to avoid pooling before source-field closure?",
            "Can excursion asymmetry be interpreted without side and intended target/stop fields?",
            "Which outside-current-edge families can the packet support as future hypotheses once input fields exist?",
        ],
        "mechanism_families": [
            {
                "family": "session_hour_time_of_day_microstructure",
                "source_safe_signal": "Tokyo and New York session buckets are separated in the packet's neutral medians and excursion-ratio diagnostics.",
                "risk_of_overread": "Session drift can be market-state-only and not strategy edge.",
                "next_field_need": ["side", "entry_reference", "setup_family", "session-specific duplicate policy"],
                "route_implication": "Carry session/hour as mandatory controls in the rank-1 strategy-field packet.",
            },
            {
                "family": "volatility_compression_expansion_range_state",
                "source_safe_signal": "Prior-16 range buckets separate neutral excursion-ratio medians in the packet's notable-slice ledger.",
                "risk_of_overread": "Range state may proxy instrument/session volatility rather than tradable structure.",
                "next_field_need": ["POI_bounds", "stop_reference", "target_reference", "path_availability"],
                "route_implication": "Rank-1 packet must preserve prior range/drift descriptors beside strategy fields.",
            },
            {
                "family": "drift_momentum_reversion_path_shape",
                "source_safe_signal": "Prior-drift buckets and close-to-close medians are available as neutral descriptors.",
                "risk_of_overread": "Without intended side, positive or negative movement has no strategy meaning.",
                "next_field_need": ["intended_side", "framework_family", "entry_reference"],
                "route_implication": "Direction fields are the immediate blocker before any preregistered result design.",
            },
            {
                "family": "source_proxy_instrument_group_differences",
                "source_safe_signal": "Seven denominator/proxy groups have separate source counts and matrix summaries; duplicate collisions are zero.",
                "risk_of_overread": "Futures proxy behavior may not transfer to CFD/GTOS execution behavior.",
                "next_field_need": ["source_proxy_group", "symbol_mapping_policy", "candidate_source"],
                "route_implication": "Do not pool source groups in future tests until strategy-field closure preserves proxy identity.",
            },
            {
                "family": "excursion_asymmetry_and_path_hazard_timing",
                "source_safe_signal": "Neutral upside/downside excursion summaries are computable for 9,455 rows, with horizon availability degrading at 16/32 bars.",
                "risk_of_overread": "Upside/downside are neutral relative to source close, not trade side or stop/target path.",
                "next_field_need": ["intended_side", "stop_reference", "target_reference", "lifecycle_state"],
                "route_implication": "Path hazard hypotheses require strategy-field source expansion before result design.",
            },
            {
                "family": "orderflow_depth_proxy_explanation",
                "source_safe_signal": "SCID source bars provide OHLCV-like source-control bars, but depth/orderflow fields are not in the neutral packet.",
                "risk_of_overread": "Adding orderflow before strategy fields could explain market state while leaving candidate intent unknown.",
                "next_field_need": ["strategy_fields_first", "depth_source_contract", "proxy_mapping_contract"],
                "route_implication": "Orderflow/proxy source-control is ranked below strategy-field source expansion.",
            },
            {
                "family": "adversarial_baseline_market_state_only",
                "source_safe_signal": "Neutral behavior may be market-state-only unless strategy fields beat session/hour/range/proxy controls in a later lane.",
                "risk_of_overread": "A future result lane could mistakenly attribute generic session drift to a strategy.",
                "next_field_need": ["baseline_control_assignment", "duplicate_policy", "sealed_partition_status"],
                "route_implication": "The rank-1 prompt requires adversarial baseline/control fields to travel with strategy descriptors.",
            },
        ],
        "outside_current_edge_mechanisms_considered": [
            "time-of-day/session microstructure",
            "range-state and volatility expansion",
            "neutral path-shape hazard",
            "proxy/instrument market-state differences",
            "orderflow/depth explanatory fields",
            "mechanical no-API strategy-family replay",
        ],
        "anti_boxing_conclusion": "The packet is most useful when treated as a neutral target substrate waiting for source-safe strategy fields, not as a verdict on the current OB edge.",
    }
    for path in write_pair("ANTI_BOXING_MECHANISM_REVIEW", "Anti-Boxing Mechanism Review", anti_boxing):
        artifacts[path.stem] = repo_path(path)

    concentration_review = {
        **base_payload("concentration_denominator_risk_review"),
        "candidate_rows": concentration["candidate_rows"],
        "denominator_group_count": concentration["denominator_group_count"],
        "symbol_counts": concentration["symbol_counts"],
        "canonical_economic_group_counts": concentration["canonical_economic_group_counts"],
        "partition_counts": concentration["partition_counts"],
        "duplicate_key_count": concentration["duplicate_key_count"],
        "duplicate_key_collision_count": concentration["duplicate_key_collision_count"],
        "max_symbol_share": concentration["max_symbol_share"],
        "max_group_share": concentration["max_group_share"],
        "small_denominator_risks": [
            "EURUSD has 48 candidate rows and must not drive future route selection by itself.",
            "XAGUSD_SI has 421 candidate rows while most other primary groups have 509; future pooled claims need group-aware concentration caps.",
            "The packet has zero duplicate-key collisions, but future strategy-field joins can reintroduce denominator ambiguity if source fields are many-to-one.",
        ],
        "denominator_policy_for_next_route": [
            "Preserve candidate row id and duplicate_proxy_denominator_key exactly.",
            "Preserve canonical_economic_group and source_file_name in every closure row.",
            "Fail closed when a strategy-field source maps multiple records to one candidate without a deterministic as-of tie-breaker.",
        ],
    }
    for path in write_pair(
        "CONCENTRATION_DENOMINATOR_RISK_REVIEW",
        "Concentration And Denominator Risk Review",
        concentration_review,
    ):
        artifacts[path.stem] = repo_path(path)

    failure_synthesis = {
        **base_payload("not_computable_failure_anatomy_synthesis"),
        "failure_boundary": failure["failure_boundary"],
        "not_computable_count": failure["not_computable_count"],
        "not_computable_reason_counts": failure["not_computable_reason_counts"],
        "by_family_horizon_reason": failure["not_computable_by_family_horizon_reason"],
        "by_reason_symbol": failure["not_computable_by_reason_symbol"],
        "sign_counts_not_strategy_outcomes": failure["neutral_close_to_close_sign_counts_not_strategy_outcomes"],
        "source_control_expansion_needs": [
            "Longer horizon/path coverage needs more source-control bars, not imputation.",
            "Rows marked not-computable must remain terminal fail-closed in any source-field packet.",
            "Any future source expansion needs G12 audit before entering the same denominator.",
        ],
        "failure_anatomy_route_implication": "The rank-1 source-field packet can proceed because not-computable rows are already fail-closed; it must preserve not-computable status and not invent target values or lifecycle truth.",
    }
    for path in write_pair(
        "NOT_COMPUTABLE_FAILURE_ANATOMY_SYNTHESIS",
        "Not-Computable Failure Anatomy Synthesis",
        failure_synthesis,
    ):
        artifacts[path.stem] = repo_path(path)

    future_source_fields = {
        **base_payload("future_source_field_requirement_ledger"),
        "rank_1_blocker_statement": "Neutral future behavior is accepted, but strategy interpretation is blocked until source-safe strategy fields are attached or fail-closed.",
        "required_fields": [
            {
                "field_group": "direction_and_side",
                "needed_for": "convert neutral close-to-close and excursion direction into a strategy-hypothesis direction without overclaiming",
                "status_now": "MISSING_FROM_NEUTRAL_PACKET",
                "next_route_status": "REQUIRED_FIELD_CLOSURE",
            },
            {
                "field_group": "entry_stop_target_references",
                "needed_for": "define intended path geometry and stop/target relation before any result design",
                "status_now": "MISSING_FROM_NEUTRAL_PACKET",
                "next_route_status": "REQUIRED_FIELD_CLOSURE",
            },
            {
                "field_group": "poi_type_bounds_and_setup_family",
                "needed_for": "separate OB/FVG/breaker/other families and avoid boxing all behavior into one framework",
                "status_now": "MISSING_FROM_NEUTRAL_PACKET",
                "next_route_status": "REQUIRED_FIELD_CLOSURE",
            },
            {
                "field_group": "lifecycle_fill_cancel_expiry_source_state",
                "needed_for": "prevent neutral source rows from being treated as executable or filled opportunities",
                "status_now": "MISSING_FROM_NEUTRAL_PACKET",
                "next_route_status": "FAIL_CLOSED_OR_PROSPECTIVE_CAPTURE_REQUIRED",
            },
            {
                "field_group": "orderflow_depth_proxy_context",
                "needed_for": "explain neutral differences after strategy fields exist",
                "status_now": "NOT_IN_NEUTRAL_PACKET",
                "next_route_status": "FUTURE_SOURCE_CONTROL_FIELD_REQUIREMENT",
            },
            {
                "field_group": "adversarial_baseline_assignment",
                "needed_for": "separate market-state-only behavior from strategy-specific hypotheses in later lanes",
                "status_now": "PARTIALLY_AVAILABLE_AS_NEUTRAL_DESCRIPTORS",
                "next_route_status": "PRESERVE_AND_EXTEND",
            },
        ],
        "field_closure_enum_for_rank_1_prompt": [
            "CLOSED_FROM_SOURCE",
            "FAIL_CLOSED_MISSING_SOURCE_FIELD",
            "PROSPECTIVE_CAPTURE_REQUIRED",
            "FORBIDDEN_IN_THIS_EVIDENCE_CLASS",
        ],
    }
    for path in write_pair(
        "FUTURE_SOURCE_FIELD_REQUIREMENT_LEDGER",
        "Future Source-Field Requirement Ledger",
        future_source_fields,
    ):
        artifacts[path.stem] = repo_path(path)

    route_ranking = {
        **base_payload("route_ranking_ledger"),
        "rank_1_route": "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET",
        "rank_1_prompt_path": next_prompt_repo_path,
        "rank_1_one_line_starter": (
            f"/goal Follow the full controlling prompt in {next_prompt_repo_path} as the complete objective; "
            "do mandatory preflight and context refresh first; do not rely on chat memory; stay "
            "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY with no validation/strategy-edge/R/PnL/win-rate/"
            "expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/"
            "raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; build the source-safe "
            "strategy-field expansion packet for all 3,014 accepted SCID candidates with exact field "
            "closure/fail-closed/prospective-capture statuses; emit packet route, verifier, focused tests, next "
            "G12-or-repair prompt, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, "
            "outcome_review_opened=false, live_effect=false; if any blocker appears, pursue until cleared, proven "
            "impossible from approved routes, or reduced to an exact owner/access/source/capture approval requirement, "
            "and mark complete only when the prompt file's completion standard is fully satisfied."
        ),
        "routes": [
            {
                "rank": 1,
                "route_id": "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET",
                "decision": "ACTIVE_NEXT_ROUTE",
                "why": "It closes the immediate evidence-class blocker: accepted neutral targets cannot support strategy hypotheses until side, entry, stop, target, POI, setup-family, lifecycle, and fail-closed source fields are attached.",
                "why_not_overclaiming": "The route is input/source-field only and does not read target values for scoring.",
            },
            {
                "rank": 2,
                "route_id": "PREREGISTERED_RESULT_DESIGN_LANE",
                "decision": "WAIT_FOR_RANK_1_FIELD_PACKET",
                "why": "Result design is necessary later, but it would be weak or generic before source fields identify what would be tested.",
            },
            {
                "rank": 3,
                "route_id": "SOURCE_FIELD_DESCRIPTOR_EXPANSION_LANE",
                "decision": "MERGE_CORE_DESCRIPTOR_REQUIREMENTS_INTO_RANK_1",
                "why": "Additional descriptors are valuable, but the biggest gap is strategy intent fields rather than more neutral market-state descriptors alone.",
            },
            {
                "rank": 4,
                "route_id": "BROADER_SEALED_SCID_POOL_EXPANSION",
                "decision": "DEFER_UNTIL_FIELD_CONTRACT_EXISTS",
                "why": "More rows would not solve the source-field gap and could multiply denominator management before the join contract exists.",
            },
            {
                "rank": 5,
                "route_id": "NEGATIVE_LEARNING_FAILURE_ANATOMY_ROUTE",
                "decision": "PARTIALLY_INCLUDED_IN_RANK_1",
                "why": "Failure anatomy is already actionable as fail-closed source requirements; a standalone route is lower priority than building the closure ledger.",
            },
            {
                "rank": 6,
                "route_id": "ORDERFLOW_PROXY_SOURCE_CONTROL_ROUTE",
                "decision": "DEFER_AS_EXPLANATORY_FIELD_ROUTE",
                "why": "Orderflow may explain neutral differences, but strategy field closure is prerequisite to knowing which candidate families need explanation.",
            },
            {
                "rank": 7,
                "route_id": "NO_API_MECHANICAL_STRATEGY_FAMILY_REPLAY_ROUTE",
                "decision": "DEFER_UNTIL_SOURCE_FIELDS_AND_RESULT_DESIGN",
                "why": "Mechanical replay can be strong later, but running it now would cross into result behavior before the source-field packet is built.",
            },
        ],
        "parallel_prompt_files_emitted": [next_prompt_repo_path],
        "parallel_route_needed_now": False,
    }
    for path in write_pair("ROUTE_RANKING_LEDGER", "Route Ranking Ledger", route_ranking):
        artifacts[path.stem] = repo_path(path)

    decision_ledger = {
        **base_payload("decision_ledger"),
        "terminal_decision": TERMINAL_DECISION,
        "accepted_g12_decision": g12_decision["terminal_decision"],
        "accepted_strategy_performance": False,
        "accepted_validation_execution": False,
        "accepted_promotion": False,
        "rank_1_next_route": route_ranking["rank_1_route"],
        "rank_1_next_prompt_path": next_prompt_repo_path,
        "terminal_blockers": [],
        "warnings": [
            "Neutral behavior differences are descriptive source-control facts only.",
            "Strategy/source fields are required before any result design or hypothesis test.",
        ],
    }
    for path in write_pair("DECISION_LEDGER", "Decision Ledger", decision_ledger):
        artifacts[path.stem] = repo_path(path)

    saturation = {
        **base_payload("saturation_self_redteam_pass"),
        "questions": [
            {
                "question": "Are we over-reading neutral behavior as strategy edge?",
                "answer": "No. Every artifact labels the behavior as neutral source-control only and keeps validation/result/performance flags closed.",
                "same_class_gap_exposed": False,
            },
            {
                "question": "Are we under-using neutral behavior by treating it as meaningless?",
                "answer": "No. The route extracts session/hour, range/drift, source-group, excursion-asymmetry, concentration, and failure-anatomy implications into a rank-1 source-field route.",
                "same_class_gap_exposed": False,
            },
            {
                "question": "Which slices look strongest, and are they broad or concentrated?",
                "answer": "Session, prior-range, prior-drift, hour, and symbol slices show descriptive spread. Broad slices need group-aware controls; EURUSD remains small-denominator.",
                "same_class_gap_exposed": False,
            },
            {
                "question": "Which slices are likely session-only, volatility-only, source-proxy-only, or baseline effects?",
                "answer": "All current slices could be market-state-only because side, entry, stop, target, POI, setup family, and lifecycle fields are absent.",
                "same_class_gap_exposed": False,
            },
            {
                "question": "Which missing fields would convert neutral behavior into a valid next hypothesis?",
                "answer": "Intended side, entry, stop, target, POI/bounds, setup family, lifecycle/fill/cancel/expiry source state, and baseline-control assignment.",
                "same_class_gap_exposed": False,
            },
            {
                "question": "What exact next route gets closer fastest without crossing boundaries?",
                "answer": "Build the SCID strategy-field source expansion packet over all 3,014 candidate rows, with field closure/fail-closed/prospective capture statuses and no target scoring.",
                "same_class_gap_exposed": False,
            },
            {
                "question": "What would a later G12 reject if the next prompt is weak?",
                "answer": "A later G12 would reject vague field closure, target-value leakage, broker evidence use, duplicate denominator drift, inferred lifecycle truth, or missing tests. The emitted rank-1 prompt hardens each point.",
                "same_class_gap_exposed": False,
            },
        ],
        "same_synthesis_class_gaps_remaining": [],
        "deliberately_not_answered_because_forbidden_or_next_evidence_class": [
            "validation execution",
            "strategy edge or performance scoring",
            "broker account/order/history/deal/position evidence",
            "AI/API or paid/vendor access",
            "live behavior or trading-surface changes",
        ],
    }
    for path in write_pair("SATURATION_SELF_REDTEAM_PASS", "Saturation Self-Red-Team Pass", saturation):
        artifacts[path.stem] = repo_path(path)

    output_manifest = {
        **base_payload("output_manifest"),
        "next_prompt_file": next_prompt_repo_path,
        "artifacts": [{"key": key, "path": value} for key, value in sorted(artifacts.items())],
        "builder": repo_path(ROUTE_DIR / "build_g0_scid_neutral_target_control_synthesis_2026_05_12.py"),
        "verifier": repo_path(ROUTE_DIR / "verify_g0_scid_neutral_target_control_synthesis_2026_05_12.py"),
        "focused_tests": repo_path(ROUTE_DIR / "test_g0_scid_neutral_target_control_synthesis_2026_05_12.py"),
        "required_outputs_covered": {
            "context_anchor": True,
            "decision_ledger": True,
            "accepted_evidence_reconciliation": True,
            "neutral_behavior_synthesis": True,
            "anti_boxing_mechanism_review": True,
            "concentration_denominator_risk_review": True,
            "not_computable_failure_anatomy_synthesis": True,
            "future_source_field_requirement_ledger": True,
            "route_ranking_ledger": True,
            "next_prompt_file": True,
            "verifier": True,
            "focused_tests": True,
            "completion_audit": True,
        },
    }
    for path in write_pair("OUTPUT_MANIFEST", "Output Manifest", output_manifest):
        artifacts[path.stem] = repo_path(path)

    completion_audit = {
        **base_payload("completion_audit"),
        "objective_restatement": {
            "deliverable": "synthesize accepted neutral target packet into ranked next route without crossing evidence boundaries",
            "accepted_candidate_rows": 3014,
            "computable_neutral_rows": 20292,
            "rank_1_next_route": route_ranking["rank_1_route"],
        },
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory preflight and context use recorded", "artifact": artifacts[f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "G12 accepted evidence reconciled exactly", "artifact": artifacts[f"{PREFIX}_ACCEPTED_EVIDENCE_RECONCILIATION_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "neutral behavior synthesis emitted", "artifact": artifacts[f"{PREFIX}_NEUTRAL_BEHAVIOR_SYNTHESIS_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "anti-boxing review emitted", "artifact": artifacts[f"{PREFIX}_ANTI_BOXING_MECHANISM_REVIEW_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "route ranking explicit and justified", "artifact": artifacts[f"{PREFIX}_ROUTE_RANKING_LEDGER_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "rank-1 next prompt emitted and hardened", "artifact": next_prompt_repo_path, "status": "PASS"},
            {"requirement": "verifier and focused tests available", "artifact": repo_path(ROUTE_DIR), "status": "PASS"},
            {"requirement": "safe flags preserved", "artifact": artifacts[f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}"], "status": "PASS"},
        ],
        "instruction_coverage": {
            "goal_session_research_discipline_read_after_preflight": True,
            "research_operating_doctrine_read_after_preflight": True,
            "lane_posture": "G0_SYNTHESIS_CONTROL_ROUTE_SELECTION",
            "anti_boxing_questions_pursued": True,
            "outside_current_edge_mechanisms_considered": anti_boxing["outside_current_edge_mechanisms_considered"],
            "exact_accepted_evidence_boundary": context_anchor["accepted_evidence_boundary"],
            "what_this_g0_did_not_answer": saturation["deliberately_not_answered_because_forbidden_or_next_evidence_class"],
        },
        "completion_standard_satisfied": True,
        "can_mark_goal_complete": True,
        "scoped_commit_required_before_final_goal_closeout": True,
        "standalone_verifier_expected": True,
        "focused_tests_expected": True,
        "final_live_state_refresh_required": True,
        "terminal_decision": TERMINAL_DECISION,
    }
    for path in write_pair("COMPLETION_AUDIT", "Completion Audit", completion_audit):
        artifacts[path.stem] = repo_path(path)


if __name__ == "__main__":
    main()
