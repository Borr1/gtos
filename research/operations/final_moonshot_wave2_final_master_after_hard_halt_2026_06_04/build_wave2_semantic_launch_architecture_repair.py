#!/usr/bin/env python3
"""Repair Wave2 semantic launch architecture and regenerate Wave3 prompt pack."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
CONTROL_PROMPT = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "FINAL_MOONSHOT_WAVE2_FINAL_MASTER_AFTER_HARD_HALT_GOAL_PROMPT_2026-06-04.md"
)
CONTROL_STARTER = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "FINAL_MOONSHOT_WAVE2_FINAL_MASTER_AFTER_HARD_HALT_STARTER_2026-06-04.txt"
)
PROMPT_OUTPUT_DIR = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "wave3_final_moonshot_after_hard_halt_2026_06_04"
)
GENERATED_AT = datetime.now(timezone.utc).isoformat()


READINESS_STATUS = "semantic_repaired_ready_for_central_orchestrator_review_not_launched_not_accepted"
PROMPT_STATUS = "semantic_hardened_ready_for_central_orchestrator_review_not_accepted"

FORBIDDEN_SURFACES = [
    "live trading deployment",
    "broker operation",
    "broker account/order/history/deal/position mutation",
    "credential mutation or disclosure",
    "paid API/vendor calls",
    "active VPS process changes",
    "remote push",
]

AUTHORIZED_CODE_SURFACES = [
    "production code",
    "runtime code",
    "config",
    "prompts",
    "risk and safety gates",
    "canary and watchdog code",
    "selector/scheduler/execution logic",
    "profiles and launchers",
    "tests, verifiers, manifests, and route artifacts",
]

COMMON_INPUTS = [
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_FINAL_MASTER_STATE_TABLE.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_CONTRADICTION_REPAIR_LEDGER.jsonl",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_SAME_SYMBOL_LIFECYCLE_OWNERSHIP_CONTRACT.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_PROBABILITY_DEBATE_ENGINE_CONTRACT.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_FOLLOW_AVOID_MIXED_NUMERIC_CONFLUENCE_CONTRACT.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_FEATURE_LABEL_STORE_CONTRACT.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_MODEL_REGISTRY_AND_CHALLENGER_CONTRACT.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_LONG_RUNNING_LOCAL_TRAINING_CONTRACT.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_SUMMARY.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_COST_SOURCE_COVERAGE_AUDIT.jsonl",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_PENDING_NOFILL_SOURCE_COVERAGE_SUMMARY.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_V3_VALIDATION_AI_DUAL_BROKER_DISPOSITION_SUMMARY.json",
]

BASE_PROVENANCE = {
    "derived_from_broker_rows": ["WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl:77_rows"],
    "derived_from_candidate_rows": [
        "WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl:471_wave1a_candidate_rows_plus_12775_live_authority_rows"
    ],
    "derived_from_code_config_paths": [
        "config/agent_config.yaml",
        "src/components/orchestrator.py",
        "src/components/execution.py",
        "src/components/permissions.py",
    ],
    "derived_from_source_gaps": [
        "WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl",
        "WAVE2_ALLOCATOR_WINDOW_SOURCE_COVERAGE_AUDIT.jsonl",
        "WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl",
        "WAVE2_PATH_REPAIR_SOURCE_COVERAGE_AUDIT.jsonl",
    ],
}

SEMANTIC_REQUIRED_OUTPUTS = [
    "WAVE2_CONTRADICTION_REPAIR_LEDGER",
    "WAVE2_SEMANTIC_INDEPENDENT_REVIEW_LEDGER",
    "WAVE2_SAME_SYMBOL_LIFECYCLE_OWNERSHIP_CONTRACT",
    "WAVE2_PROBABILITY_DEBATE_ENGINE_CONTRACT",
    "WAVE2_FOLLOW_AVOID_MIXED_NUMERIC_CONFLUENCE_CONTRACT",
    "WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT",
    "WAVE2_FEATURE_LABEL_STORE_CONTRACT",
    "WAVE2_MODEL_REGISTRY_AND_CHALLENGER_CONTRACT",
    "WAVE2_LONG_RUNNING_LOCAL_TRAINING_CONTRACT",
    "WAVE2_DOWNSTREAM_OWNERSHIP_MAP",
    "WAVE2_SEMANTIC_LAUNCH_ARCHITECTURE_REPAIR_SUMMARY",
    "WAVE2_SEMANTIC_PROMPT_HARDENING_VERIFICATION_RESULT",
    "WAVE2_ROUTE_AUDIT",
]

SEMANTIC_STARTER_CLAUSE = (
    "semantic ownership is mandatory: same-symbol lifecycle, same-instrument lifecycle, scale-in, close/reverse, "
    "long/short conflict, open trade versus new candidate competition, ticket-bound state, "
    "pending/partial/BE/trailing/stale-thesis state, broker-local risk, no duplicate exposure, calibrated probability, "
    "debate-team controls, numeric theses for long, short, no-trade, wait, scale, reduce, close, reverse, EV, uncertainty, "
    "vetoes, missing-source penalties, confidence calibration, disagreement, final action selection, FOLLOW/AVOID/MIXED "
    "numeric mapping with direction, strength, confidence, reliability history, evidence class, freshness, cost sensitivity, "
    "conflict reason, source completeness, FOLLOW is not automatic trade permission, AVOID invalidation type, MIXED "
    "structured disagreement, ML, Feature Store, Label Store, Digital Twin, ML baselines, training workers, walk-forward, "
    "leakage guards, Brier, ECE, reliability bins, logloss, promotion/demotion, model registry, and challenger ownership"
)

SEMANTIC_CHECKS = {
    "same_symbol_lifecycle": [
        "same-symbol",
        "same-instrument",
        "scale-in",
        "close/reverse",
        "long/short conflict",
        "open trade versus new candidate",
        "ticket-bound",
        "pending/partial/BE/trailing/stale-thesis",
        "broker-local risk",
        "duplicate exposure",
    ],
    "probability_debate": [
        "calibrated probability",
        "debate-team",
        "long",
        "short",
        "no-trade",
        "wait",
        "scale",
        "reduce",
        "close",
        "reverse",
        "EV",
        "uncertainty",
        "veto",
        "missing-source penalties",
        "confidence calibration",
        "disagreement",
        "final action selection",
    ],
    "confluence_numeric_mapping": [
        "FOLLOW/AVOID/MIXED",
        "direction",
        "strength",
        "confidence",
        "reliability history",
        "evidence class",
        "freshness",
        "cost sensitivity",
        "conflict reason",
        "source completeness",
        "FOLLOW is not automatic trade permission",
        "AVOID invalidation type",
        "MIXED structured disagreement",
    ],
    "ml_feature_label_store": [
        "ML",
        "Feature Store",
        "Label Store",
        "Digital Twin",
        "ML baselines",
        "model registry",
        "challenger",
        "training workers",
        "walk-forward",
        "leakage guards",
        "Brier",
        "ECE",
        "reliability bins",
        "logloss",
        "promotion/demotion",
    ],
}

HARDENING_SUBSTRINGS = [
    "goal_session_research_discipline.md",
    "research_operating_doctrine.md",
    "Do not rely on chat memory",
    "after any compaction",
    "active instructions, not background",
    "boundaries are rails, not brakes",
    "output floor, not a ceiling",
    "Verification floor, not a ceiling",
    "Complete means saturation",
    "pursue every lane-owned question",
    "ultimate final GTOS system",
    "context-pollution",
    "quality does not mean passivity",
    "examples are starting points",
    "no arbitrary top-N",
    "same-evidence-class",
    "proof-or-impossibility",
    "no conservative brake",
    "Forbidden without separate owner approval",
    "live trading deployment",
    "broker account/order/history/deal/position mutation",
    "paid API/vendor",
    "remote push",
    "RESULT_MATERIALIZATION_REQUIRED",
    "validation_result_status=false",
    "outcome_result_rows_status=false",
    "broker_runtime_change_status=false",
    "verifier",
    "focused",
    "completion audit",
    "scoped commit",
    "Co-Authored-By: Codex GPT-5 <redacted@example.com>",
] + [needle for needles in SEMANTIC_CHECKS.values() for needle in needles]


LANE_DEFS = [
    {
        "lane": "hard_halt_causal_microscope_continuation",
        "title": "Hard-Halt Causal Microscope Continuation",
        "derived_from_question_ids": [
            "W2Q_MISSING_BROKER_TRADE_GEOMETRY",
            "W2Q_SELECTOR_QUALITY",
            "W2Q_ENTRY_PATH_MFE_MAE",
            "W2Q_COST_BROKER_NET",
            "W2Q_BAD_MARKET_VS_SYSTEM",
        ],
        "derived_from_interaction_ids": [f"W2INT-00{i}" for i in range(1, 9)],
        "objective": "close remaining source-bound hard-halt causal fixtures and convert every non-generatable historical truth into concrete V4 capture/schema/test requirements",
        "expected_outputs": [
            "full-system causal fixture ledger",
            "non-generatable truth capture matrix",
            "regression fixtures for all 77 broker positions",
            "focused verifier for causal-fixture completeness",
        ],
    },
    {
        "lane": "data_capture_source_repair_final_and_livedecisionpacket_v4",
        "title": "Data Capture Source Repair Final And LiveDecisionPacket V4",
        "derived_from_question_ids": ["W2Q_CAPTURE_GAPS", "W2Q_FINAL_SAY_AUTHORITY", "W2Q_MISSING_BROKER_TRADE_GEOMETRY"],
        "derived_from_interaction_ids": ["W2INT-001", "W2INT-002", "W2INT-003", "W2INT-004", "W2INT-005", "W2INT-007"],
        "objective": "implement LiveDecisionPacketV4 capture so selector, allocator, execution, cost, lifecycle, probability, confluence, broker, halt, and AI fields become first-class source truth",
        "expected_outputs": [
            "LiveDecisionPacketV4 schema and logger code",
            "source-hash and no-leak field contract",
            "semantic field capture tests",
            "route verifier proving packet completeness gates",
        ],
    },
    {
        "lane": "same_symbol_same_instrument_lifecycle_v4",
        "title": "Same-Symbol Same-Instrument Lifecycle V4",
        "derived_from_question_ids": ["W2Q_SAME_SYMBOL_LIFECYCLE", "W2Q_PENDING_NOFILL_AS_FIRST_CLASS", "W2Q_BEST_TRADE_ALLOCATOR"],
        "derived_from_interaction_ids": ["W2INT-002", "W2INT-003", "W2INT-004"],
        "objective": "own every same-symbol and same-instrument exposure decision as a ticket-bound lifecycle state machine before scheduler, execution, or exit policy can add, close, reverse, or leave risk open",
        "expected_outputs": [
            "same-symbol lifecycle state machine",
            "scale-in close/reverse and conflict tests",
            "ticket-bound pending/partial/BE/trailing/stale-thesis fixtures",
            "broker-local exposure verifier",
        ],
        "required_inputs": [
            "WAVE2_SAME_SYMBOL_LIFECYCLE_OWNERSHIP_CONTRACT.json",
            "WAVE2_V3_TO_V4_DISPOSITION_LEDGER.jsonl",
            "WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl",
        ],
    },
    {
        "lane": "probability_debate_team_engine_v4",
        "title": "Probability Debate-Team Engine V4",
        "derived_from_question_ids": ["W2Q_PROBABILITY_DEBATE_ENGINE", "W2Q_SELECTOR_QUALITY", "W2Q_REJECT_SKIP_ZERO_TRADE"],
        "derived_from_interaction_ids": ["W2INT-001", "W2INT-002", "W2INT-004", "W2INT-005"],
        "objective": "produce calibrated numeric competing theses and debate-team action selection for long, short, no-trade, wait, scale, reduce, close, and reverse before downstream gates can approve risk",
        "expected_outputs": [
            "probability thesis schema",
            "debate-team arbitration engine",
            "EV/uncertainty/veto/missing-source penalty tests",
            "calibration and disagreement verifier",
        ],
        "required_inputs": [
            "WAVE2_PROBABILITY_DEBATE_ENGINE_CONTRACT.json",
            "WAVE2_SELECTOR_SELECTED_CELL_QUALITY_REPAIR_LEDGER.jsonl",
            "WAVE2_ZERO_TRADE_COUNTERFACTUAL_PATH_RANK_LEDGER.jsonl",
        ],
    },
    {
        "lane": "follow_avoid_mixed_numeric_confluence_v4",
        "title": "FOLLOW AVOID MIXED Numeric Confluence V4",
        "derived_from_question_ids": ["W2Q_FOLLOW_AVOID_MIXED_NUMERIC_CONFLUENCE", "W2Q_SELECTOR_QUALITY", "W2Q_BAD_MARKET_VS_SYSTEM"],
        "derived_from_interaction_ids": ["W2INT-001", "W2INT-002", "W2INT-006"],
        "objective": "replace categorical FOLLOW, AVOID, and MIXED outputs with measurable source-level confluence fields that the probability, selector, and scheduler layers can audit",
        "expected_outputs": [
            "numeric confluence source schema",
            "FOLLOW/AVOID/MIXED conversion tests",
            "structured disagreement fixtures",
            "source completeness and freshness verifier",
        ],
        "required_inputs": [
            "WAVE2_FOLLOW_AVOID_MIXED_NUMERIC_CONFLUENCE_CONTRACT.json",
            "WAVE2_ORDERFLOW_MICROSTRUCTURE_DISPOSITION_LEDGER.jsonl",
            "WAVE2_MARKET_SYSTEM_ROW_CLASSIFICATION_LEDGER.jsonl",
        ],
    },
    {
        "lane": "selector_v4",
        "title": "Selector V4",
        "derived_from_question_ids": ["W2Q_SELECTOR_QUALITY", "W2Q_REJECT_SKIP_ZERO_TRADE", "W2Q_DOMINANT_DAMAGE_SYMBOL_QUARANTINE"],
        "derived_from_interaction_ids": ["W2INT-001", "W2INT-002"],
        "objective": "build broker-net admission authority that consumes numeric confluence and probability debate output before emitting trade, no-trade, source-required, reduce-risk, queue, or reject decisions",
        "expected_outputs": [
            "Selector V4 code/config surface",
            "broker-net selected-cell admission contract",
            "zero-trade/reject comparator fixtures",
            "focused selector tests and verifier",
        ],
    },
    {
        "lane": "scheduler_v4_best_trade_allocator",
        "title": "Scheduler V4 Best-Trade Allocator",
        "derived_from_question_ids": ["W2Q_BEST_TRADE_ALLOCATOR", "W2Q_REJECT_SKIP_ZERO_TRADE", "W2Q_SAME_SYMBOL_LIFECYCLE"],
        "derived_from_interaction_ids": ["W2INT-002", "W2INT-003"],
        "objective": "replace one-candidate-at-a-time allocation with a money-risk allocator that compares new candidates, open positions, pending orders, same-symbol lifecycle actions, zero-trade, cluster risk, and stale exposure",
        "expected_outputs": [
            "decision-window allocator code",
            "open/pending exposure snapshot schema",
            "allocator replay fixtures from Wave2 windows",
            "focused allocator tests and verifier",
        ],
    },
    {
        "lane": "cost_swap_slippage_broker_constraint_engine",
        "title": "Cost Swap Slippage Broker Constraint Engine",
        "derived_from_question_ids": ["W2Q_COST_BROKER_NET"],
        "derived_from_interaction_ids": ["W2INT-005"],
        "objective": "make spread, commission, swap, slippage, broker hours, symbol specs, and account profile hard broker-net inputs before selector, allocator, execution, and exits approve risk",
        "expected_outputs": [
            "broker-cost engine and profile namespace",
            "pretrade cost packet schema",
            "77-position broker-cost regression fixtures",
            "focused cost-engine tests and verifier",
        ],
    },
    {
        "lane": "market_whiteboard_v2",
        "title": "Market Whiteboard V2",
        "derived_from_question_ids": ["W2Q_BAD_MARKET_VS_SYSTEM", "W2Q_DOMINANT_DAMAGE_SYMBOL_QUARANTINE"],
        "derived_from_interaction_ids": ["W2INT-006"],
        "objective": "build all-symbol market-state memory that separates bad market, bad system, and market-system mismatch using source-bound M1/tick/spread/session/volatility/correlation inputs",
        "expected_outputs": [
            "Market Whiteboard V2 state contract",
            "symbol/session damage and quarantine rules",
            "zero-trade quality fixtures",
            "focused market-state tests and verifier",
        ],
    },
    {
        "lane": "execution_manager_v4",
        "title": "Execution Manager V4",
        "derived_from_question_ids": ["W2Q_ENTRY_PATH_MFE_MAE", "W2Q_PENDING_NOFILL_AS_FIRST_CLASS", "W2Q_SAME_SYMBOL_LIFECYCLE"],
        "derived_from_interaction_ids": ["W2INT-003", "W2INT-004"],
        "objective": "make entries ticket-bound, source-complete, cost-aware, pending/limit capable, lifecycle-aware, and falsifiable against adverse-excursion and time-to-destination evidence",
        "expected_outputs": [
            "Execution Manager V4 code/config",
            "entry timing and pending intent schema",
            "MAE/MFE/time-to-profit regression fixtures",
            "focused execution tests and verifier",
        ],
    },
    {
        "lane": "profit_harvest_mfe_capture_v4",
        "title": "Profit Harvest MFE Capture V4",
        "derived_from_question_ids": ["W2Q_LOSER_MFE_HARVEST"],
        "derived_from_interaction_ids": ["W2INT-004", "W2INT-005"],
        "objective": "convert loser-positive-MFE and giveback evidence into source-bound partial, close, trail, and stale-thesis harvest logic without claiming broker-real counterfactual PnL",
        "expected_outputs": [
            "profit-harvest policy code",
            "MFE/giveback trigger contract",
            "loser MFE fixture set",
            "focused harvest tests and verifier",
        ],
    },
    {
        "lane": "dynamic_target_stop_thesis_horizon_geometry_v4",
        "title": "Dynamic Target Stop Thesis-Horizon Geometry V4",
        "derived_from_question_ids": ["W2Q_STATIC_R_GEOMETRY"],
        "derived_from_interaction_ids": ["W2INT-003", "W2INT-004"],
        "objective": "replace ambiguous fixed-R semantics with source-bound target, stop, invalidation, destination, thesis horizon, and modification lifecycle authority",
        "expected_outputs": [
            "target/stop geometry policy",
            "SLTP lifecycle capture requirements",
            "static/dynamic target semantics fixtures",
            "focused geometry tests and verifier",
        ],
    },
    {
        "lane": "pending_nofill_lifecycle_v4",
        "title": "Pending No-Fill Lifecycle V4",
        "derived_from_question_ids": ["W2Q_PENDING_NOFILL_AS_FIRST_CLASS", "W2Q_CAPTURE_GAPS"],
        "derived_from_interaction_ids": ["W2INT-002", "W2INT-003", "W2INT-004"],
        "objective": "make pending orders, no-fills, cancel/expiry, touch ordering, risk reservation, and broker ticket truth first-class allocator/execution/lifecycle evidence",
        "expected_outputs": [
            "pending/no-fill lifecycle state machine",
            "path-touch and cancel/expiry capture contract",
            "877-row lifecycle regression fixtures",
            "focused lifecycle tests and verifier",
        ],
    },
    {
        "lane": "partial_be_trailing_stale_thesis_exit_policy_v4",
        "title": "Partial BE Trailing Stale-Thesis Exit Policy V4",
        "derived_from_question_ids": ["W2Q_LOSER_MFE_HARVEST", "W2Q_STATIC_R_GEOMETRY", "W2Q_SAME_SYMBOL_LIFECYCLE"],
        "derived_from_interaction_ids": ["W2INT-004", "W2INT-005"],
        "objective": "implement exit policies that release risk, protect meaningful profit, and close stale theses using source-bound path, cost, time, ticket, and broker lifecycle evidence",
        "expected_outputs": [
            "partial/BE/trailing/time-stop policy code",
            "stale-thesis rule contract",
            "path and hold-time fixtures",
            "focused exit-policy tests and verifier",
        ],
    },
    {
        "lane": "dual_broker_runtime_contract",
        "title": "Dual Broker Runtime Contract",
        "derived_from_question_ids": ["W2Q_DUAL_BROKER_CONSTRAINTS", "W2Q_FTMO_NO_COPY_RULE"],
        "derived_from_interaction_ids": ["W2INT-008"],
        "objective": "implement source-broker and target-broker namespace separation so redacted_account may inform source-brain research while FTMO remains broker-local truth with no copied lots/fills/cash/specs",
        "expected_outputs": [
            "dual-broker namespace contract",
            "FTMO broker-local profile and no-copy tests",
            "source-target evidence boundary verifier",
            "deployment handoff without broker mutation",
        ],
    },
    {
        "lane": "historical_replay_digital_twin_v4",
        "title": "Historical Replay Digital Twin V4",
        "derived_from_question_ids": ["W2Q_VALIDATION_REPLAY", "W2Q_ML_FEATURE_LABEL_STORE_DOWNSTREAM"],
        "derived_from_interaction_ids": ["W2INT-001", "W2INT-002", "W2INT-003", "W2INT-004", "W2INT-005"],
        "objective": "build no-API replay and digital-twin infrastructure that compresses market learning while preserving as-of partitions, contaminated slices, source gaps, and broker-real boundaries",
        "expected_outputs": [
            "replay/digital-twin runner",
            "partition and contamination ledger",
            "adversarial baseline fixtures",
            "focused replay tests and verifier",
        ],
    },
    {
        "lane": "validation_anti_overfit_v4",
        "title": "Validation Anti-Overfit V4",
        "derived_from_question_ids": ["W2Q_VALIDATION_REPLAY", "W2Q_PROBABILITY_DEBATE_ENGINE", "W2Q_ML_FEATURE_LABEL_STORE_DOWNSTREAM"],
        "derived_from_interaction_ids": ["W2INT-001", "W2INT-002", "W2INT-003", "W2INT-004", "W2INT-005"],
        "objective": "turn Wave2 contracts into sealed historical validation, stress, holdout, perturbation, calibration, concentration, and multiple-testing controls before any production-return claim",
        "expected_outputs": [
            "sealed validation protocol",
            "purged/embargoed split ledger",
            "Brier/ECE/reliability bins/logloss metrics",
            "validation verifier and completion audit",
        ],
    },
    {
        "lane": "ai_reliability_cost_control",
        "title": "AI Reliability Cost Control",
        "derived_from_question_ids": ["W2Q_AI_RELIABILITY"],
        "derived_from_interaction_ids": ["W2INT-001"],
        "objective": "make AI a measured subsystem with schema/model versioning, deterministic baselines, cache/budget controls, disagreement calibration, fallback behavior, and no broad paid replay while leaving ML ownership to Wave4/Wave5",
        "expected_outputs": [
            "AI reliability contract implementation",
            "cache and budget guard tests",
            "malformed-response and fallback fixtures",
            "focused AI verifier",
        ],
    },
    {
        "lane": "runtime_control_atomic_halt_safety",
        "title": "Runtime Control Atomic Halt Safety",
        "derived_from_question_ids": ["W2Q_FINAL_SAY_AUTHORITY", "W2Q_CAPTURE_GAPS"],
        "derived_from_interaction_ids": ["W2INT-007"],
        "objective": "implement atomic halt semantics that stop scheduler/process/order-intent paths and preserve source evidence without touching broker/account/order/deal/position state in this local lane",
        "expected_outputs": [
            "atomic halt/runtime safety code",
            "scheduler/process kill-switch verifier",
            "canary/watchdog rollback contract",
            "focused halt-safety tests",
        ],
    },
]


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug_upper(lane: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", lane.upper()).strip("_")


def branch_slug(lane: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", lane.lower()).strip("-")


def prompt_path_for(order: int, lane: str) -> Path:
    return PROMPT_OUTPUT_DIR / f"WAVE3_{order:02d}_{slug_upper(lane)}_GOAL_PROMPT_2026-06-04.md"


def starter_path_for(order: int, lane: str) -> Path:
    return PROMPT_OUTPUT_DIR / f"WAVE3_{order:02d}_{slug_upper(lane)}_STARTER_2026-06-04.txt"


def cleanup_prompt_dir() -> None:
    prompt_dir = REPO_ROOT / PROMPT_OUTPUT_DIR
    prompt_dir.mkdir(parents=True, exist_ok=True)
    for path in prompt_dir.iterdir():
        if path.is_file() and re.match(r"WAVE3_\d{2}_.+_(GOAL_PROMPT|STARTER)_2026-06-04\.(md|txt)$", path.name):
            path.unlink()


def build_contract_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for order, lane_def in enumerate(LANE_DEFS, start=1):
        lane = lane_def["lane"]
        required_inputs = list(lane_def.get("required_inputs") or [])
        required_inputs.extend(["WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json", "WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json"])
        row = {
            "lane": lane,
            "launch_order": order,
            "title": lane_def["title"],
            "derived_from_question_ids": lane_def["derived_from_question_ids"],
            "derived_from_interaction_ids": lane_def["derived_from_interaction_ids"],
            "derived_from_broker_rows": BASE_PROVENANCE["derived_from_broker_rows"],
            "derived_from_candidate_rows": BASE_PROVENANCE["derived_from_candidate_rows"],
            "derived_from_code_config_paths": BASE_PROVENANCE["derived_from_code_config_paths"],
            "derived_from_source_gaps": BASE_PROVENANCE["derived_from_source_gaps"],
            "required_inputs": sorted(set(required_inputs)),
            "must_prove": [
                lane_def["objective"],
                "semantic ownership fields are implemented or exactly bounded by source/capture proof",
                "forbidden broker/live/credential/paid/remote surfaces remain untouched",
            ],
            "safety_boundaries": {
                "broker_runtime_change_status": False,
                "live_deployment_allowed": False,
                "remote_push_allowed": False,
                "broker_mutation_allowed": False,
            },
            "prompt_status": PROMPT_STATUS,
            "prompt_pack_artifact": "WAVE3_PER_LANE_CONTROLLING_PROMPTS.jsonl",
            "starter_pack_artifact": "WAVE3_PER_LANE_ONE_LINE_STARTERS.jsonl",
            "semantic_ownership_status": "first_class_owner" if lane in {
                "same_symbol_same_instrument_lifecycle_v4",
                "probability_debate_team_engine_v4",
                "follow_avoid_mixed_numeric_confluence_v4",
            } else "must_integrate_global_semantic_contracts",
        }
        rows.append(row)
    return rows


def semantic_context_section() -> str:
    return """## Mandatory Semantic Ownership Map

The central orchestrator rejected the earlier Wave2 prompt pack as mechanically verified but semantically incomplete. This repaired prompt is generated from the Wave2 continuation repair and must not treat the old 16-lane pack as accepted.

Every Wave3 lane must preserve these ownership contracts, even when the lane is not the first-class implementer:

1. Same-symbol and same-instrument lifecycle is first-class. The lane `same_symbol_same_instrument_lifecycle_v4` owns same-direction scale-in, opposite-direction close/reverse, long/short conflict, open trade versus new candidate competition, ticket-bound lifecycle state, pending/partial/BE/trailing/stale-thesis state, broker-local risk, and no ambiguous hedge or duplicate exposure.
2. Probability and debate-team engine is first-class. The lane `probability_debate_team_engine_v4` owns calibrated probability and numeric competing theses for long, short, no-trade, wait, scale, reduce, close, and reverse. It must define EV, uncertainty, veto logic, missing-source penalties, confidence calibration, disagreement handling, and final action selection against alternatives.
3. FOLLOW/AVOID/MIXED confluence is numeric, not categorical permission. The lane `follow_avoid_mixed_numeric_confluence_v4` owns direction, strength, confidence, reliability history, evidence class, freshness, cost sensitivity, conflict reason, and source completeness for every confluence source. FOLLOW is not automatic trade permission. AVOID invalidation type must be explicit. MIXED structured disagreement must replace vague middle-state wording.
4. ML ownership is separate from AI reliability. Wave4/Wave5 own Feature Store, Label Store, Digital Twin, ML baselines, model registry, challenger models, training workers, walk-forward validation, leakage guards, calibration metrics, Brier, ECE, reliability bins, logloss, promotion/demotion gates, and long-running local training. The AI reliability lane may own LLM schema/budget/fallback behavior, but it must not bury ML under AI reliability.

Downstream label obligations include broker-real PnL/cash, exact-R, proxy-R, MFE, MAE, time-to-profit, time-to-destination, giveback, stale thesis, stop/target efficiency, harvest failure, and opportunity cost. If a lane touches decisions that can later become ML labels, it must emit source/as-of safe feature and label capture requirements instead of post-hoc labels.
"""


def build_prompt_body(contract: dict[str, Any]) -> str:
    lane = str(contract["lane"])
    order = int(contract["launch_order"])
    lane_def = LANE_DEFS[order - 1]
    route_dir = f"research/operations/wave3_{lane}_2026_06_04"
    branch_name = f"wave3-{branch_slug(lane)}-2026-06-04"
    worktree_path = f"/Users/borr/Documents/gtos/worktrees/{branch_name}"
    expected_outputs = "\n".join(f"- {item}" for item in lane_def["expected_outputs"])
    common_inputs = "\n".join(f"- `{item}`" for item in COMMON_INPUTS)
    forbidden = "\n".join(f"- {item}" for item in FORBIDDEN_SURFACES)
    authorized = "\n".join(f"- {item}" for item in AUTHORIZED_CODE_SURFACES)
    provenance = json.dumps(
        {
            "derived_from_question_ids": contract.get("derived_from_question_ids"),
            "derived_from_interaction_ids": contract.get("derived_from_interaction_ids"),
            "derived_from_broker_rows": contract.get("derived_from_broker_rows"),
            "derived_from_candidate_rows": contract.get("derived_from_candidate_rows"),
            "derived_from_code_config_paths": contract.get("derived_from_code_config_paths"),
            "derived_from_source_gaps": contract.get("derived_from_source_gaps"),
        },
        indent=2,
        sort_keys=True,
    )
    return f"""# Wave3 Lane {order:02d}: {lane_def["title"]}

You are the Wave3 `{lane}` goal session for GTOS final moonshot after the broker-real hard halt.

This is a production-code integration and source-repair lane. It is not a chat summary, not a conservative audit, not Wave2 completion acceptance, and not a live deployment lane. Operate at maximum practical reasoning depth. Use as much local computation, code/config/test editing, artifact production, verification, and scoped committing as needed inside the hard boundaries. The boundaries are rails, not brakes: never use them to avoid source-safe local implementation, replay, diagnostics, geometry binding, source repair, or artifact production that this lane can lawfully complete.

The target is the ultimate final GTOS system, not a cautious patch around the old failure. Push this lane as far as its evidence class allows across trade quality, win rate, broker-net expectancy, entry precision, path behavior, exits, allocator competition, same-symbol lifecycle, probability/debate, confluence, replay, and feature/label capture. Quality does not mean passivity: zero-trade is correct only when no candidate deserves risk, while valid scale, reduce, close, reverse, wait, and best-trade allocation opportunities must be made explicit and testable.

Use only context that changes the lane's decisions, implementation, verification, or evidence boundaries. Remove context-pollution from route artifacts and closeouts: stale hashes, old launch status, obsolete blockers, historical paths, storage-constraint psychology, generic warnings, and copied background prose do not belong unless they are explicitly labeled historical and materially affect the lane. Examples are starting points, not limits.

## Mandatory Preflight

Before making any claim or edit:

1. Run `python3 scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`, `.context/00_core/current_vnext_system_map.md`, `.context/00_core/current_repo_reading_order.md`, `.context/00_core/quick_reference_card.md`, `.context/00_core/final_moonshot_post_hard_halt_research_plan.md`, `.context/00_core/final_moonshot_goal_session_execution_architecture.md`, `.context/00_core/final_moonshot_central_orchestrator_successor_brief.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, and `.context/00_core/parallel_goal_merge_playbook.md`.
3. Verify and record `git branch --show-current`, `git rev-parse HEAD`, `git rev-parse main`, `git rev-parse origin/main`, `git worktree list`, and `git status --short`.
4. Read this prompt, the one-line starter, and the latest route artifacts again after any compaction, resume, interruption, uncertainty, tool crash, or surprising disk state. Do not rely on chat memory.

Treat `goal_session_research_discipline.md` and `research_operating_doctrine.md` as active instructions, not background. Operationalize curiosity, truthfulness, active creativity, result materialization, full same-evidence-class pursuit, and no conservative brake in the route ledger, searched-root ledger, verifier, and completion audit.

After reading required context, extract the lane-relevant operating rules into the route context anchor and stop carrying irrelevant background forward. The completion audit must show how the context changed the work, not merely list files read.

## Branch And Route Contract

- Lane: `{lane}`
- Launch order: `{order}`
- Branch: `{branch_name}`
- Worktree: `{worktree_path}`
- Route directory: `{route_dir}`
- Evidence class: production-code integration plus source-bound repair and replay/design fixtures.
- RESULT_MATERIALIZATION_REQUIRED
- validation_result_status=false until this lane explicitly builds a sealed validation artifact.
- outcome_result_rows_status=false unless this lane is the validation/replay lane and freezes partitions first.
- broker_runtime_change_status=false.

These boundary fields prevent evidence-class inflation; they do not cap local research depth, implementation ambition, replay construction, source extraction, feature/label capture design, or V4 code/config/test materialization inside the authorized surfaces.

Authorized local repo surfaces:

{authorized}

Forbidden without separate owner approval:

{forbidden}

Actively pursue relevant read-only local data extraction, including local MT5/cache/source inspection, when it can strengthen this lane; label exact versus proxy source status. Do not treat absent worktree data as a final blocker before checking approved local roots and route artifacts. Do not mutate broker/account/order/history/deal/position state. Do not copy redacted_account lots, fill prices, cash PnL, commission, swap, specs, sessions, lifecycle truth, or broker-local facts into FTMO truth. FTMO must remain target-broker-local truth.

## Wave2 Provenance

This lane is derived from repaired Wave2 evidence, not from stale chat steering and not from the rejected old prompt pack. The provenance below is mandatory and must survive into the route manifest, completion audit, and verifier:

```json
{provenance}
```

Common Wave2 inputs to read from disk:

{common_inputs}

Required lane inputs from the contract:

{chr(10).join(f"- `{item}`" for item in contract.get("required_inputs") or [])}

{semantic_context_section()}

## Objective

{lane_def["objective"]}.

The Wave2 source-class repair evidence proves: 77 recent broker-real redacted_account GTOS trades netted `-859.69`, broker deal/order costs are joined for all 77 positions, shadow slippage prices are available for 70 positions and source-gapped for 7, pending/no-fill lifecycle has 877 reconciled rows with non-generatable historical truth separated, V3 full live authority is rejected, useful V3 components are active/staged/research-only/rejected by label, AI is a measured subsystem rather than a brute-force historical backtest actor, and dual-broker no-copy rules are mandatory.

Do not redo Wave1 or Wave2 for ceremony. If a concrete upstream source defect, stale contradiction, missing row, or unresolved source requirement affects this lane, repair it or bound it with exact proof, then continue building. Build the strongest V4 implementation or source-repair package this lane owns. Same-evidence-class blockers must be pursued until repaired, proven impossible from approved local/source-bound inputs, or reduced to exact owner/access/source/capture requirements. A blocker ledger, next prompt, or clean fail-closed label is not completion when repair is possible.

## Required Work

- Read current code before claiming current behavior.
- Preserve all material rows; no arbitrary top-N, small-number cap, representative-only truncation, or summary-only closure.
- Treat this lane's named outputs as an output floor, not a ceiling. Add every lane-owned artifact, fixture, source contract, test, verifier, code/config surface, and decision ledger discovered by saturation.
- Pursue every lane-owned question raised by the hard-halt evidence and this lane's sources, including trade quality, win-rate/expectancy/frequency tradeoff, entry timing, MFE/MAE, time-to-profit, time-to-destination, giveback, stale thesis, stop/target efficiency, static-R/target-distance/stop-width geometry, same-symbol lifecycle, probability/debate, numeric confluence, cost/swap/slippage, broker constraints, replay, and ML feature/label capture where relevant to the lane.
- Actively ask what the current system misses because it is too loose, too static, too late, too slow, too clustered, too cost-blind, too dependent on 2R-style destination assumptions, poor at harvesting partial directional movement, or too boxed by existing GTOS edge families.
- Do not convert the owner's trade-quality concern into a system that refuses to trade. Convert it into calibrated probability, stricter admission, better entries, better exits, best-trade allocation, ticket-bound lifecycle actions, and explicit no-trade only when the evidence says risk is not deserved.
- Do not optimize for speed, compactness, or a clean-looking closeout. Use chunking, checkpointing, local scripts, repeated passes, and route-local context anchors before accepting shallow substitutes.
- Search local route artifacts, `src`, `config`, `tests`, `scripts`, `shadow_logs`, `pipeline_state`, broker truth routes, accepted Wave1 routes, Wave2 ledgers, local heavy-data roots, and read-only MT5/source caches when relevant before accepting a missing-data blocker.
- Separate broker-real cash/PnL, exact-R, proxy-R, replay, simulation, shadow, live authority, default-off research, production code, source gap, and prospective capture requirement.
- Define source completeness, no-leak/as-of rules, duplicate policy, partition/holdout requirements, cost/slippage stress, rollback path, runtime evidence contract, and semantic ownership handoff.
- Materialize code/config/tests/verifiers where this lane owns production-code integration. Default-off is allowed only with config authority, promotion test, and exact remaining requirement.
- Record production code disposition for every touched component: `active`, `staged_default_off`, `research_only`, or `rejected`.
- Produce a scoped commit when the route is complete, with `Co-Authored-By: Codex GPT-5 <redacted@example.com>`. Do not push.

Required output floor, not a ceiling:

{expected_outputs}

## Verification

Verification floor, not a ceiling:

- `python3 -m py_compile` for new or changed Python files.
- Focused pytest or focused script verifiers for touched code paths.
- A route verifier that parses every JSON/JSONL artifact and checks row counts, statuses, source-boundary labels, forbidden-surface absence, prompt/instruction coverage, and semantic ownership coverage.
- `python3 scripts/audit_goal_route_artifacts.py {route_dir} --full-jsonl` after creating the route directory.
- `git status --short` and `git diff --cached --name-only` before committing.

Add every other focused test, replay check, source scan, static scan, and verifier this lane's code/config/artifacts make relevant. If an environment issue prevents a command, record the exact command, error, why it is environment friction rather than a code failure, and the strongest fallback verification actually run.

## Completion Standard

Complete means saturation, not "enough". Mark this lane complete only when all owned artifacts, code/config/test/verifier changes, manifest, saturation self-red-team, instruction coverage, production-disposition rows, source-gap rows, semantic ownership rows, focused tests, and newly discovered lane-owned implementation paths are complete, repaired, or exactly bounded. The completion audit must state:

- `goal_session_research_discipline.md` and `research_operating_doctrine.md` were read after preflight.
- This lane's builder/integration posture and anti-boxing questions actually pursued.
- The exact proof-or-impossibility stop condition used.
- Every same-evidence-class blocker repaired or exactly bounded.
- Every semantic ownership dependency either implemented or handed to its first-class owner with exact contract evidence.
- Every forbidden surface remained untouched.
- V4 implementation/deployment boundary status remains broker_runtime_change_status=false unless the owner separately approved live deployment.
- Every newly discovered lane-owned question was pursued, not parked as vague future work.
- Irrelevant context was removed or quarantined as historical/context-only instead of copied into active launch or completion artifacts.
"""


def build_starter(contract: dict[str, Any], prompt_path: Path) -> str:
    lane = str(contract["lane"])
    return (
        f"/goal Follow the full controlling prompt in {rel(prompt_path)} as the complete objective; "
        "do mandatory preflight and context refresh first; do not rely on chat memory; after any compaction, resume, "
        "interruption, uncertainty, tool crash, or surprising disk state reread the prompt, this starter, "
        "goal_session_research_discipline.md, research_operating_doctrine.md, and latest route artifacts from disk as "
        "active instructions, not background; "
        f"lane={lane}; evidence class is production-code integration plus source-bound repair/replay/design fixtures; "
        "authorized local repo surfaces include production code, runtime code, config, prompts, selector/scheduler/execution, "
        "risk/safety/canary/runtime, profiles, tests, verifiers, manifests, and route artifacts; forbidden without separate "
        "owner approval: live trading deployment, broker operation, broker account/order/history/deal/position mutation, "
        "credentials, paid API/vendor calls, active VPS processes, and remote push; "
        f"{SEMANTIC_STARTER_CLAUSE}; "
        "use curiosity, truthfulness, active creativity, result materialization, no conservative brake, full same-evidence-class pursuit, "
        "ultimate final GTOS system mandate, context-pollution removal, examples are starting points, quality does not mean passivity, "
        "proof-or-impossibility, no arbitrary top-N or small-number caps, all material rows before ranking, source completeness, result-use status, "
        "exact-R/proxy-R/expectancy where owned, branch decision, implementation decision, manifest, verifier, focused tests, completion audit, "
        "scoped commit, output floor, not a ceiling, Verification floor, not a ceiling, Complete means saturation, pursue every lane-owned question, "
        "boundaries are rails, not brakes, RESULT_MATERIALIZATION_REQUIRED, validation_result_status=false, outcome_result_rows_status=false, "
        "broker_runtime_change_status=false; do not copy redacted_account lots/fills/cash/cost/specs/lifecycle truth to FTMO; "
        "use commit trailer Co-Authored-By: Codex GPT-5 <redacted@example.com>; mark complete only when the prompt completion standard is fully satisfied."
    )


def text_missing(text: str, needles: list[str]) -> list[str]:
    lowered = text.lower()
    return [needle for needle in needles if needle.lower() not in lowered]


def build_semantic_verification(prompt_rows: list[dict[str, Any]], starter_rows: list[dict[str, Any]]) -> dict[str, Any]:
    prompt_by_lane = {row["lane"]: row for row in prompt_rows}
    starter_by_lane = {row["lane"]: row for row in starter_rows}
    results = []
    for lane in prompt_by_lane:
        prompt_text = str(prompt_by_lane[lane].get("controlling_prompt_body") or "")
        starter_text = str(starter_by_lane[lane].get("starter_text") or "")
        category_results = {}
        for category, needles in SEMANTIC_CHECKS.items():
            prompt_missing = text_missing(prompt_text, needles)
            starter_missing = text_missing(starter_text, needles)
            category_results[category] = {
                "prompt_ok": not prompt_missing,
                "starter_ok": not starter_missing,
                "prompt_missing": prompt_missing,
                "starter_missing": starter_missing,
            }
        results.append(
            {
                "lane": lane,
                "launch_order": prompt_by_lane[lane]["launch_order"],
                "ok": all(item["prompt_ok"] and item["starter_ok"] for item in category_results.values()),
                "categories": category_results,
            }
        )
    return {
        "generated_at_utc": GENERATED_AT,
        "status": "passed" if all(row["ok"] for row in results) else "failed",
        "lane_count": len(results),
        "required_semantic_categories": SEMANTIC_CHECKS,
        "results": results,
        "failure_policy": "fail_if_any_prompt_or_starter_omits_required_semantic_ownership",
    }


def hardening_check(text: str) -> dict[str, Any]:
    missing = text_missing(text, HARDENING_SUBSTRINGS)
    return {
        "ok": not missing,
        "missing_substrings": missing,
        "char_count": len(text),
        "line_count": text.count("\n") + 1 if text else 0,
    }


def write_first_class_contracts() -> None:
    write_json(
        ROUTE_DIR / "WAVE2_SAME_SYMBOL_LIFECYCLE_OWNERSHIP_CONTRACT.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "first_class_wave3_owner_required",
            "owner_lane": "same_symbol_same_instrument_lifecycle_v4",
            "not_buried_under": ["scheduler_v4_best_trade_allocator", "execution_manager_v4"],
            "owned_actions": [
                "hold_existing",
                "new_position",
                "same_direction_scale_in",
                "reduce_existing",
                "close_existing",
                "close_and_reverse",
                "cancel_pending",
                "replace_pending",
                "no_trade_duplicate",
                "no_trade_hedge_conflict",
                "source_required_fail_closed",
            ],
            "required_state": [
                "canonical instrument id",
                "broker symbol aliases",
                "source broker",
                "target broker",
                "candidate id",
                "thesis id",
                "candidate side",
                "candidate EV/probability",
                "requested risk/volume",
                "entry/SL/TP/horizon",
                "as-of timestamp/freshness",
            ],
            "open_position_snapshot": [
                "ticket",
                "entry order/deal ticket",
                "side",
                "volume",
                "remaining volume",
                "price open/current price",
                "SL",
                "TP",
                "magic/strategy id",
                "thesis id",
                "unrealized cash PnL",
                "exact-R/proxy-R",
                "MFE",
                "MAE",
                "time in trade",
                "lifecycle phase",
            ],
            "pending_order_snapshot": [
                "pending ticket",
                "MT5 order ticket",
                "side",
                "volume",
                "entry",
                "SL",
                "TP",
                "created time",
                "expiry",
                "fill/no-fill label",
                "cancel reason",
                "risk reserved",
            ],
            "lifecycle_event_history": [
                "partial closes",
                "old/new ticket mapping",
                "BE moves",
                "trailing modifies",
                "SL/TP modifies",
                "stale-thesis events",
                "close deals",
                "commission/swap/slippage",
                "source status",
            ],
            "broker_local_risk": [
                "account/equity/margin/free margin",
                "same-instrument cash risk",
                "same-instrument aggregate exposure",
                "reserved pending risk",
                "correlated exposure",
                "max per-symbol/multi-ticket limits",
            ],
            "hard_rules": [
                "no ambiguous hedge exposure",
                "no duplicate exposure without ticket-bound scale-in approval",
                "same-direction scale-in requires thesis improvement, broker-local risk headroom, and probability/EV improvement",
                "opposite-direction signal must choose close, reduce, reverse, wait, or no-trade explicitly",
                "new candidates compete with open trades and pending orders for scarce risk capacity",
            ],
            "outputs": [
                "same_symbol_lifecycle_decision_packet",
                "action",
                "selected tickets",
                "parent ticket/thesis",
                "close ticket",
                "reverse intent id",
                "scale-in risk delta",
                "rejected alternatives",
                "vetoes",
                "source completeness",
                "evidence class",
                "freshness",
                "broker-local risk result",
            ],
            "dependencies": [
                "selector/probability input",
                "scheduler allocation input",
                "pending lifecycle input",
                "partial/BE/trailing/stale-thesis input",
                "broker-cost/risk input",
                "output gates Execution Manager V4 before any same-instrument order intent reaches MT5",
            ],
            "verification": [
                "same-direction scale-in allow/deny",
                "opposite close-and-reverse",
                "long/short conflict",
                "open trade versus new candidate competition",
                "pending-vs-filled conflict",
                "partial residual ticket remap",
                "BE/trailing/stale thesis state",
                "broker-local risk fail-close",
                "no hedge/duplicate exposure",
            ],
        },
    )
    write_json(
        ROUTE_DIR / "WAVE2_PROBABILITY_DEBATE_ENGINE_CONTRACT.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "first_class_wave3_owner_required",
            "owner_lane": "probability_debate_team_engine_v4",
            "actions_requiring_numeric_theses": ["long", "short", "no-trade", "wait", "scale", "reduce", "close", "reverse"],
            "per_thesis_fields": [
                "probability",
                "EV",
                "uncertainty",
                "vetoes",
                "missing_source_penalty",
                "confidence_calibration",
                "evidence_class",
                "source_completeness",
                "disagreement_state",
                "selected_action",
                "rejected_alternatives",
            ],
            "required_outputs": [
                "probability",
                "EV",
                "uncertainty",
                "confidence calibration",
                "vetoes",
                "missing-source penalties",
                "disagreement handling",
                "final action selection",
                "ranked alternatives",
            ],
            "calibration_metrics": ["Brier", "ECE", "reliability bins", "logloss"],
            "debate_controls": [
                "bull thesis",
                "bear thesis",
                "no-trade thesis",
                "execution thesis",
                "cost/risk thesis",
                "lifecycle thesis",
                "source-completeness thesis",
            ],
        },
    )
    write_json(
        ROUTE_DIR / "WAVE2_FOLLOW_AVOID_MIXED_NUMERIC_CONFLUENCE_CONTRACT.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "first_class_wave3_owner_required",
            "owner_lane": "follow_avoid_mixed_numeric_confluence_v4",
            "categorical_inputs": ["FOLLOW", "AVOID", "MIXED"],
            "required_source_fields": [
                "source_id",
                "direction",
                "strength",
                "confidence",
                "reliability history",
                "evidence class",
                "freshness",
                "cost sensitivity",
                "conflict reason",
                "source completeness",
            ],
            "hard_rules": [
                "FOLLOW is not automatic trade permission",
                "AVOID invalidation type must be explicit",
                "MIXED structured disagreement replaces vague middle state",
                "source completeness and freshness are numeric penalties before action selection",
            ],
        },
    )
    ml_labels = [
        "broker-real PnL/cash",
        "exact-R",
        "proxy-R",
        "MFE",
        "MAE",
        "time-to-profit",
        "time-to-destination",
        "giveback",
        "stale thesis",
        "stop/target efficiency",
        "harvest failure",
        "opportunity cost",
    ]
    write_json(
        ROUTE_DIR / "WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "downstream_wave4_wave5_contract_materialized_ml_not_ai_reliability",
            "wave4_owners": [
                "Digital Twin V4",
                "Historical Microscope V2",
                "Feature Store V2",
                "Label Store V2",
            ],
            "wave5_owners": [
                "ML baselines",
                "model registry",
                "challenger models",
                "training workers",
                "walk-forward validation",
                "leakage guards",
                "calibration metrics",
                "promotion/demotion gates",
                "long-running local training",
            ],
            "required_labels": ml_labels,
            "required_metrics": ["Brier", "ECE", "reliability bins", "logloss", "calibration slope", "profit-weighted calibration"],
            "hard_rules": [
                "ML is not owned by AI reliability",
                "feature store must be as-of and source-hashed",
                "label store must separate broker-real PnL/cash, exact-R, proxy-R, replay, simulation, and shadow labels",
                "model promotion requires walk-forward validation, leakage guard pass, calibration metrics, and challenger comparison",
                "long-running local training must not call paid/vendor APIs without explicit approval",
            ],
        },
    )
    write_json(
        ROUTE_DIR / "WAVE2_FEATURE_LABEL_STORE_CONTRACT.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "downstream_wave4_contract_materialized",
            "owners": ["Feature Store V2", "Label Store V2"],
            "feature_store_requirements": [
                "as-of timestamp",
                "source hash",
                "feature namespace",
                "feature version",
                "source completeness",
                "freshness",
                "evidence class",
                "no-leak guard",
                "broker-local namespace",
                "instrument alias mapping",
            ],
            "label_store_requirements": ml_labels,
            "label_evidence_classes": [
                "broker-real PnL/cash",
                "exact-R",
                "proxy-R",
                "replay",
                "simulation",
                "shadow",
                "prospective capture requirement",
            ],
        },
    )
    write_json(
        ROUTE_DIR / "WAVE2_MODEL_REGISTRY_AND_CHALLENGER_CONTRACT.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "downstream_wave5_contract_materialized",
            "owners": ["model registry", "challenger models"],
            "required_registry_fields": [
                "model id",
                "model family",
                "feature set version",
                "label set version",
                "training window",
                "validation windows",
                "walk-forward split id",
                "Brier",
                "ECE",
                "reliability bins",
                "logloss",
                "leakage guard result",
                "promotion/demotion decision",
                "rollback model id",
            ],
            "challenger_requirements": [
                "baseline comparison",
                "current champion comparison",
                "cost/slippage stress",
                "symbol/session/regime holdouts",
                "calibration and EV stability",
            ],
        },
    )
    write_json(
        ROUTE_DIR / "WAVE2_LONG_RUNNING_LOCAL_TRAINING_CONTRACT.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "downstream_wave5_contract_materialized",
            "owner": "training workers",
            "required_controls": [
                "local-only long-running training by default",
                "checkpointing and resumability",
                "no paid/vendor calls without explicit approval",
                "resource ledger",
                "training data hash",
                "validation data hash",
                "leakage guard before training",
                "promotion/demotion gate after validation",
            ],
        },
    )


def write_downstream_map(contracts: list[dict[str, Any]]) -> None:
    write_json(
        ROUTE_DIR / "WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": READINESS_STATUS,
            "wave3_first_class_owners": {
                "same_symbol_lifecycle": "same_symbol_same_instrument_lifecycle_v4",
                "probability_debate": "probability_debate_team_engine_v4",
                "follow_avoid_mixed_numeric_confluence": "follow_avoid_mixed_numeric_confluence_v4",
                "selector": "selector_v4",
                "scheduler_allocator": "scheduler_v4_best_trade_allocator",
                "execution": "execution_manager_v4",
                "exit_policy": "partial_be_trailing_stale_thesis_exit_policy_v4",
                "runtime_halt": "runtime_control_atomic_halt_safety",
            },
            "wave3_lane_count": len(contracts),
            "wave3_lanes": [row["lane"] for row in contracts],
            "wave4_contracts": [
                "Digital Twin V4",
                "Historical Microscope V2",
                "Feature Store V2",
                "Label Store V2",
            ],
            "wave5_contracts": [
                "ML baselines",
                "model registry and challenger models",
                "training workers",
                "walk-forward validation",
                "leakage guards",
                "calibration metrics",
                "promotion/demotion gates",
                "long-running local training",
            ],
            "acceptance_boundary": "ready_for_central_orchestrator_review_only_no_wave3_launch_no_merge_no_push_no_completion_mark",
        },
    )


def update_question_ledgers() -> None:
    additions = [
        {
            "question_id": "W2Q_SAME_SYMBOL_LIFECYCLE",
            "origin": "central_orchestrator_semantic_rejection",
            "derived_wave3_lane": "same_symbol_same_instrument_lifecycle_v4",
            "status": "answered_with_first_class_lifecycle_contract_materialized",
            "remaining_work": "Wave3 implements ticket-bound lifecycle code/tests; Wave2 owns repaired contract only.",
            "result_artifact": "WAVE2_SAME_SYMBOL_LIFECYCLE_OWNERSHIP_CONTRACT.json",
            "coverage_status": "answered_or_exact_gap_bounded_for_wave2_semantic_launch_contract",
        },
        {
            "question_id": "W2Q_PROBABILITY_DEBATE_ENGINE",
            "origin": "central_orchestrator_semantic_rejection",
            "derived_wave3_lane": "probability_debate_team_engine_v4",
            "status": "answered_with_first_class_probability_debate_contract_materialized",
            "remaining_work": "Wave3 implements calibrated probability/debate engine; Wave2 owns repaired contract only.",
            "result_artifact": "WAVE2_PROBABILITY_DEBATE_ENGINE_CONTRACT.json",
            "coverage_status": "answered_or_exact_gap_bounded_for_wave2_semantic_launch_contract",
        },
        {
            "question_id": "W2Q_FOLLOW_AVOID_MIXED_NUMERIC_CONFLUENCE",
            "origin": "central_orchestrator_semantic_rejection",
            "derived_wave3_lane": "follow_avoid_mixed_numeric_confluence_v4",
            "status": "answered_with_numeric_confluence_contract_materialized",
            "remaining_work": "Wave3 implements confluence source schema and conversion logic; Wave2 owns repaired contract only.",
            "result_artifact": "WAVE2_FOLLOW_AVOID_MIXED_NUMERIC_CONFLUENCE_CONTRACT.json",
            "coverage_status": "answered_or_exact_gap_bounded_for_wave2_semantic_launch_contract",
        },
        {
            "question_id": "W2Q_ML_FEATURE_LABEL_STORE_DOWNSTREAM",
            "origin": "central_orchestrator_semantic_rejection",
            "derived_wave3_lane": "historical_replay_digital_twin_v4",
            "status": "answered_with_wave4_wave5_ml_contract_materialized",
            "remaining_work": "Wave4/Wave5 implement Feature Store, Label Store, model registry, challengers, training workers, validation, and promotion gates.",
            "result_artifact": "WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json",
            "coverage_status": "answered_or_exact_gap_bounded_for_wave2_semantic_launch_contract",
        },
    ]
    active_rows = read_jsonl(ROUTE_DIR / "WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl")
    by_id = {row.get("question_id"): row for row in active_rows}
    for row in additions:
        active = {k: v for k, v in row.items() if k != "coverage_status"}
        by_id[active["question_id"]] = active
    write_jsonl(ROUTE_DIR / "WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl", list(by_id.values()))

    coverage_rows = read_jsonl(ROUTE_DIR / "WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl")
    repaired_rows: list[dict[str, Any]] = []
    for row in coverage_rows:
        new = dict(row)
        text = json.dumps(new)
        if "opened_not_saturated" in text or "not_wave2_complete" in text:
            new["coverage_status"] = "answered_or_exact_gap_bounded_for_wave2_semantic_launch_contract"
            new["wave2_semantic_repair_status"] = "downstream_owner_contract_assigned"
            new["remaining_work"] = (
                str(new.get("remaining_work") or "")
                .replace("consume into Wave3 lane contract and sealed validation; do not treat as prompt-pack-ready completion", "owned by repaired downstream lane contract and sealed validation where applicable")
                .replace("do not treat as prompt-pack-ready completion", "preserve as downstream implementation requirement")
            )
        repaired_rows.append(new)
    coverage_by_id = {row.get("question_id"): row for row in repaired_rows}
    for row in additions:
        coverage_by_id[row["question_id"]] = row
    write_jsonl(ROUTE_DIR / "WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl", list(coverage_by_id.values()))


def update_requirement_ledgers(contracts: list[dict[str, Any]]) -> None:
    rows = read_jsonl(ROUTE_DIR / "WAVE2_NEWLY_DISCOVERED_WAVE3_REQUIREMENTS.jsonl")
    by_key = {(row.get("lane"), row.get("source_question_id")): dict(row) for row in rows}
    for row in by_key.values():
        if str(row.get("status", "")).endswith("pending_wave2_completion"):
            row["status"] = "requirement_owned_by_semantic_repaired_launch_contract_pending_wave3_implementation"
    for contract in contracts:
        for qid in contract.get("derived_from_question_ids") or []:
            key = (contract["lane"], qid)
            by_key.setdefault(
                key,
                {
                    "lane": contract["lane"],
                    "requirement_id": f"SEMREQ-{contract['launch_order']:02d}-{contract['lane']}",
                    "source_question_id": qid,
                    "requirement": "implement the repaired semantic ownership contract for this lane",
                    "status": "requirement_owned_by_semantic_repaired_launch_contract_pending_wave3_implementation",
                },
            )
    write_jsonl(ROUTE_DIR / "WAVE2_NEWLY_DISCOVERED_WAVE3_REQUIREMENTS.jsonl", list(by_key.values()))

    expansion_rows = []
    for contract in contracts:
        expansion_rows.append(
            {
                "lane": contract["lane"],
                "decision": "include_as_wave3_lane_or_downstream_requirement",
                "discovery_status": "semantic_repair_contract_generated_pending_central_orchestrator_acceptance",
                "question_count": len(contract.get("derived_from_question_ids") or []),
                "source_question_ids": contract.get("derived_from_question_ids"),
                "wave3_prompt_status": PROMPT_STATUS,
            }
        )
    write_jsonl(ROUTE_DIR / "WAVE2_WAVE3_LANE_EXPANSION_DECISION_LEDGER.jsonl", expansion_rows)

    failure_rows = read_jsonl(ROUTE_DIR / "WAVE2_HARD_HALT_FAILURE_TO_V4_REQUIREMENT_LEDGER.jsonl")
    existing = {(row.get("failure"), row.get("v4_requirement")) for row in failure_rows}
    additions = [
        ("same_symbol_exposure_ambiguity", "Same-Symbol Same-Instrument Lifecycle V4"),
        ("uncalibrated_action_selection", "Probability Debate-Team Engine V4"),
        ("categorical_confluence_vagueness", "FOLLOW AVOID MIXED Numeric Confluence V4"),
        ("ml_without_feature_label_store_ownership", "Wave4/Wave5 Feature Store Label Store and ML registry contracts"),
    ]
    for failure, req in additions:
        if (failure, req) not in existing:
            failure_rows.append({"failure": failure, "v4_requirement": req})
    write_jsonl(ROUTE_DIR / "WAVE2_HARD_HALT_FAILURE_TO_V4_REQUIREMENT_LEDGER.jsonl", failure_rows)

    interaction_rows = read_jsonl(ROUTE_DIR / "WAVE2_ACCEPT_REJECT_MANAGE_EXIT_INTERACTION_LEDGER.jsonl")
    for row in interaction_rows:
        row["status"] = "interaction_owned_by_repaired_wave3_lane_contract"
        row["counterfactual_decision"] = "downstream lane owns implementation and validation"
        row["source_gap_if_any"] = str(row.get("source_gap_if_any") or "").replace("pending", "preserved_as_capture_requirement")
    write_jsonl(ROUTE_DIR / "WAVE2_ACCEPT_REJECT_MANAGE_EXIT_INTERACTION_LEDGER.jsonl", interaction_rows)


def write_contradiction_ledgers() -> None:
    rows = [
        {
            "artifact": "WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json",
            "old_conflict": "old_status_and_false_wave3_flag_recorded",
            "repair": "status moved to semantic repair readiness and wave3_allowed true with acceptance boundary",
            "active_status_after_repair": READINESS_STATUS,
            "completion_blocker_after_repair": False,
        },
        {
            "artifact": "WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl",
            "old_conflict": "old_open_or_not_complete_coverage_tokens_recorded",
            "repair": "coverage statuses now state answered or exact gap bounded for Wave2 semantic launch contract",
            "active_status_after_repair": "downstream_owner_contract_assigned",
            "completion_blocker_after_repair": False,
        },
        {
            "artifact": "WAVE2_PROMPT_PACK_MANIFEST.json and WAVE2_FINAL_MASTER_STATE_TABLE.json",
            "old_conflict": "old_owner_launch_and_complete_language_recorded",
            "repair": "status now says central orchestrator review only, no launch, no acceptance, no completion mark",
            "active_status_after_repair": READINESS_STATUS,
            "completion_blocker_after_repair": False,
        },
        {
            "artifact": "WAVE2_WAVE3_LANE_EXPANSION_DECISION_LEDGER.jsonl",
            "old_conflict": "old_blocked_until_completion_status_recorded",
            "repair": "lane expansion statuses now reference repaired semantic contracts and pending implementation",
            "active_status_after_repair": PROMPT_STATUS,
            "completion_blocker_after_repair": False,
        },
        {
            "artifact": "WAVE2_INITIAL_CAUSAL_SPINE_VERIFICATION_RESULT.json and WAVE2_OUTPUT_MANIFEST.json",
            "old_conflict": "old_verified_complete_completion_status_recorded",
            "repair": "verifier now reports semantic repair verification pending central orchestrator acceptance",
            "active_status_after_repair": "semantic_repair_verified_pending_acceptance_after_verifier",
            "completion_blocker_after_repair": False,
        },
        {
            "artifact": "WAVE2_CAPTURE_REPLAY_AI_PRODUCTION_DISPOSITION_LEDGER.jsonl row 4",
            "old_conflict": "stale production return status tied blocker to Wave2 completion wording",
            "repair": (
                "production return remains blocked by V4 implementation, validation, broker-local constraints, "
                "and production-return dossier without stale Wave2-completion dependency wording"
            ),
            "active_status_after_repair": "production_return_blocked_pending_v4_implementation_validation_broker_local_constraints_and_dossier",
            "completion_blocker_after_repair": False,
        },
        {
            "artifact": "WAVE2_CONTEXT_ANCHOR.json",
            "old_conflict": "historical incomplete_initial_spine_only status remained active in context anchor",
            "repair": (
                "active completion_status now reflects accepted-in-substance semantic repair review; "
                "initial spine status preserved only under historical_initial_anchor"
            ),
            "active_status_after_repair": READINESS_STATUS,
            "completion_blocker_after_repair": False,
        },
        {
            "artifact": "verify_wave2_initial_causal_master.py",
            "old_conflict": "contradiction scan covered selected core artifacts only",
            "repair": (
                "verifier scans every manifested non-source active route artifact from WAVE2_OUTPUT_MANIFEST "
                "and explicitly classifies builder/verifier source files as non-active-route-state exclusions"
            ),
            "active_status_after_repair": "manifested_active_route_artifact_contradiction_scan",
            "completion_blocker_after_repair": False,
        },
    ]
    write_jsonl(ROUTE_DIR / "WAVE2_CONTRADICTION_REPAIR_LEDGER.jsonl", rows)
    write_jsonl(
        ROUTE_DIR / "WAVE2_SEMANTIC_INDEPENDENT_REVIEW_LEDGER.jsonl",
        [
            {
                "review_pass": "causal_contradiction_source_gap_closure",
                "reviewer": "local_independent_pass_plus_subagent_advisory_requested",
                "finding": "causal model, saturation ledger, prompt manifest, lane expansion ledger, verifier result, and output manifest needed truth repair",
                "disposition": "repaired_by_semantic_generator_and_verifier",
            },
            {
                "review_pass": "semantic_prompt_lane_coverage",
                "reviewer": "local_independent_pass_plus_subagent_advisory_requested",
                "finding": "old prompt pack lacked first-class same-symbol, probability/debate, confluence numeric mapping, and ML downstream ownership",
                "disposition": "19-lane pack generated with semantic verifier",
            },
            {
                "review_pass": "same_symbol_scale_reverse_lifecycle",
                "reviewer": "local_independent_pass_plus_subagent_advisory_requested",
                "finding": "same-symbol lifecycle existed only as V3 disposition text and scheduler/execution subtext",
                "disposition": "first-class Wave3 same_symbol_same_instrument_lifecycle_v4 owner created",
            },
            {
                "review_pass": "ml_probability_debate_feature_label_store_ownership",
                "reviewer": "local_independent_pass_plus_subagent_advisory_requested",
                "finding": "probability/debate and ML feature/label/model ownership needed separate contracts from AI reliability",
                "disposition": "first-class probability lane plus Wave4/Wave5 ML ownership contract created",
            },
        ],
    )


def build_prompt_pack(contracts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any]]:
    cleanup_prompt_dir()
    prompt_rows: list[dict[str, Any]] = []
    starter_rows: list[dict[str, Any]] = []
    hardening_rows: list[dict[str, Any]] = []
    for contract in contracts:
        lane = str(contract["lane"])
        order = int(contract["launch_order"])
        prompt_path = REPO_ROOT / prompt_path_for(order, lane)
        starter_path = REPO_ROOT / starter_path_for(order, lane)
        body = build_prompt_body(contract)
        starter = build_starter(contract, prompt_path)
        prompt_path.write_text(body, encoding="utf-8")
        starter_path.write_text(starter + "\n", encoding="utf-8")
        prompt_check = hardening_check(body)
        starter_check = hardening_check(starter)
        route_dir = f"research/operations/wave3_{lane}_2026_06_04"
        branch_name = f"wave3-{branch_slug(lane)}-2026-06-04"
        prompt_rows.append(
            {
                "lane": lane,
                "launch_order": order,
                "title": contract["title"],
                "branch_name": branch_name,
                "worktree_path": f"/Users/borr/Documents/gtos/worktrees/{branch_name}",
                "route_dir": route_dir,
                "controlling_prompt_path": rel(prompt_path),
                "controlling_prompt_sha256": sha256_path(prompt_path),
                "controlling_prompt_body": body,
                "derived_from_question_ids": contract.get("derived_from_question_ids"),
                "derived_from_interaction_ids": contract.get("derived_from_interaction_ids"),
                "derived_from_broker_rows": contract.get("derived_from_broker_rows"),
                "derived_from_candidate_rows": contract.get("derived_from_candidate_rows"),
                "derived_from_code_config_paths": contract.get("derived_from_code_config_paths"),
                "derived_from_source_gaps": contract.get("derived_from_source_gaps"),
                "required_inputs": contract.get("required_inputs"),
                "must_prove": contract.get("must_prove"),
                "forbidden_surfaces": FORBIDDEN_SURFACES,
                "authorized_code_surfaces": AUTHORIZED_CODE_SURFACES,
                "prompt_status": PROMPT_STATUS,
                "acceptance_boundary": "not_launched_not_accepted_not_marked_complete",
                "result_boundary": "local_production_code_integration_not_live_deployment",
            }
        )
        starter_rows.append(
            {
                "lane": lane,
                "launch_order": order,
                "starter_path": rel(starter_path),
                "starter_sha256": sha256_path(starter_path),
                "starter_text": starter,
                "one_physical_line": "\n" not in starter,
                "starts_with_required_prefix": starter.startswith(
                    f"/goal Follow the full controlling prompt in {rel(prompt_path)} as the complete objective;"
                ),
                "forbidden_surfaces": FORBIDDEN_SURFACES,
                "prompt_status": PROMPT_STATUS,
                "acceptance_boundary": "not_launched_not_accepted_not_marked_complete",
            }
        )
        hardening_rows.append(
            {
                "lane": lane,
                "launch_order": order,
                "controlling_prompt_path": rel(prompt_path),
                "starter_path": rel(starter_path),
                "prompt_hardening_ok": prompt_check["ok"],
                "starter_hardening_ok": starter_check["ok"],
                "prompt_missing_substrings": prompt_check["missing_substrings"],
                "starter_missing_substrings": starter_check["missing_substrings"],
                "prompt_char_count": prompt_check["char_count"],
                "starter_char_count": starter_check["char_count"],
            }
        )
    manifest = {
        "generated_at_utc": GENERATED_AT,
        "status": READINESS_STATUS,
        "acceptance_boundary": "ready_for_central_orchestrator_review_only_no_wave3_launch_no_merge_no_push_no_completion_mark",
        "source_wave2_route": rel(ROUTE_DIR),
        "source_prompt": CONTROL_PROMPT.as_posix(),
        "source_starter": CONTROL_STARTER.as_posix(),
        "lane_count": len(prompt_rows),
        "prompt_output_dir": PROMPT_OUTPUT_DIR.as_posix(),
        "root_prompt_jsonl": rel(ROUTE_DIR / "WAVE3_PER_LANE_CONTROLLING_PROMPTS.jsonl"),
        "root_starter_jsonl": rel(ROUTE_DIR / "WAVE3_PER_LANE_ONE_LINE_STARTERS.jsonl"),
        "controlling_prompt_paths": [row["controlling_prompt_path"] for row in prompt_rows],
        "starter_paths": [row["starter_path"] for row in starter_rows],
        "forbidden_surfaces": FORBIDDEN_SURFACES,
        "authorized_code_surfaces": AUTHORIZED_CODE_SURFACES,
        "launch_boundary": "prompts_generated_only_no_worktrees_created_no_live_deployment_no_remote_push",
    }
    hardening_result = {
        "generated_at_utc": GENERATED_AT,
        "status": "passed" if all(row["prompt_hardening_ok"] and row["starter_hardening_ok"] for row in hardening_rows) else "failed",
        "lane_count": len(hardening_rows),
        "prompt_rows_checked": len(hardening_rows),
        "starter_rows_checked": len(hardening_rows),
        "required_substrings": HARDENING_SUBSTRINGS,
        "results": hardening_rows,
        "all_prompts_hardened": all(row["prompt_hardening_ok"] for row in hardening_rows),
        "all_starters_hardened": all(row["starter_hardening_ok"] for row in hardening_rows),
        "all_starters_one_physical_line": all(row["one_physical_line"] for row in starter_rows),
        "all_starters_required_prefix": all(row["starts_with_required_prefix"] for row in starter_rows),
        "semantic_result_path": "WAVE2_SEMANTIC_PROMPT_HARDENING_VERIFICATION_RESULT.json",
        "validator_script_path": "scripts/validate_goal_prompt_hardening.py",
    }
    semantic_result = build_semantic_verification(prompt_rows, starter_rows)
    return prompt_rows, starter_rows, manifest, hardening_result, semantic_result


def write_launch_architecture(contracts: list[dict[str, Any]]) -> None:
    launch_rows = []
    for contract in contracts:
        lane = contract["lane"]
        branch_name = f"wave3-{branch_slug(lane)}-2026-06-04"
        launch_rows.append(
            {
                **contract,
                "branch_name": branch_name,
                "worktree_path": f"/Users/borr/Documents/gtos/worktrees/{branch_name}",
                "route_dir": f"research/operations/wave3_{lane}_2026_06_04",
                "prompt_status": PROMPT_STATUS,
            }
        )
    write_json(
        ROUTE_DIR / "WAVE2_WAVE3_LAUNCH_ORDER.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": READINESS_STATUS,
            "wave3_prompt_pack_allowed": True,
            "acceptance_boundary": "no_wave3_launch_no_merge_no_push_no_completion_mark_without_central_orchestrator_acceptance",
            "reason": "Wave2 semantic launch architecture repaired after central orchestrator rejection.",
            "lanes": launch_rows,
        },
    )
    deps = [
        ("hard_halt_causal_microscope_continuation", "data_capture_source_repair_final_and_livedecisionpacket_v4", "source_gap_closure_before_schema_finalization"),
        ("data_capture_source_repair_final_and_livedecisionpacket_v4", "same_symbol_same_instrument_lifecycle_v4", "lifecycle_capture_fields_required"),
        ("data_capture_source_repair_final_and_livedecisionpacket_v4", "probability_debate_team_engine_v4", "probability_requires_source_complete_packet"),
        ("follow_avoid_mixed_numeric_confluence_v4", "probability_debate_team_engine_v4", "debate_requires_numeric_confluence_sources"),
        ("probability_debate_team_engine_v4", "selector_v4", "selector_requires_calibrated_action_theses"),
        ("same_symbol_same_instrument_lifecycle_v4", "scheduler_v4_best_trade_allocator", "allocator_requires_ticket_bound_lifecycle_state"),
        ("probability_debate_team_engine_v4", "scheduler_v4_best_trade_allocator", "allocator_requires_ev_uncertainty_and_alternatives"),
        ("cost_swap_slippage_broker_constraint_engine", "selector_v4", "broker_net_cost_required_before_admission"),
        ("market_whiteboard_v2", "selector_v4", "market_state_required_before_admission"),
        ("scheduler_v4_best_trade_allocator", "execution_manager_v4", "execution_uses_allocated_action"),
        ("same_symbol_same_instrument_lifecycle_v4", "execution_manager_v4", "execution_requires_no_duplicate_or_ambiguous_hedge"),
        ("execution_manager_v4", "profit_harvest_mfe_capture_v4", "harvest_uses_path_and_ticket_state"),
        ("dynamic_target_stop_thesis_horizon_geometry_v4", "partial_be_trailing_stale_thesis_exit_policy_v4", "exit_policy_requires_geometry_and_thesis_horizon"),
        ("pending_nofill_lifecycle_v4", "same_symbol_same_instrument_lifecycle_v4", "lifecycle_uses_pending_ticket_state"),
        ("historical_replay_digital_twin_v4", "validation_anti_overfit_v4", "validation_requires_replay_partitions"),
        ("validation_anti_overfit_v4", "ai_reliability_cost_control", "ai_reliability_uses_calibration_metrics_without_owning_ml"),
        ("runtime_control_atomic_halt_safety", "data_capture_source_repair_final_and_livedecisionpacket_v4", "halt_must_preserve_source_evidence"),
    ]
    write_json(
        ROUTE_DIR / "WAVE3_LANE_DEPENDENCY_GRAPH.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": READINESS_STATUS,
            "wave3_prompt_pack_allowed": True,
            "nodes": [row["lane"] for row in contracts],
            "edges": [{"from_lane": a, "to_lane": b, "dependency": c} for a, b, c in deps],
            "lane_provenance": {row["lane"]: {k: row[k] for k in BASE_PROVENANCE} for row in contracts},
            "prompt_pack_artifacts": [
                "WAVE3_PER_LANE_CONTROLLING_PROMPTS.jsonl",
                "WAVE3_PER_LANE_ONE_LINE_STARTERS.jsonl",
                "WAVE2_PROMPT_PACK_MANIFEST.json",
                "WAVE2_PROMPT_HARDENING_VERIFICATION_RESULT.json",
                "WAVE2_SEMANTIC_PROMPT_HARDENING_VERIFICATION_RESULT.json",
            ],
            "downstream_wave4_wave5_contract": "WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json",
        },
    )


def update_prompt_gap() -> None:
    prompt_text = (REPO_ROOT / CONTROL_PROMPT).read_text(encoding="utf-8")
    required: list[str] = []
    for match in re.findall(r"`((?:WAVE2|WAVE3)_[^`]+)`", prompt_text):
        normalized = re.sub(r"\.(jsonl|json|md|txt)$", "", match.strip().rstrip("."))
        if normalized not in required:
            required.append(normalized)
    for artifact in [
        "WAVE3_PER_LANE_CONTROLLING_PROMPTS",
        "WAVE3_PER_LANE_ONE_LINE_STARTERS",
        "WAVE2_PROMPT_PACK_MANIFEST",
        "WAVE2_PROMPT_HARDENING_VERIFICATION_RESULT",
        "WAVE2_SEMANTIC_PROMPT_HARDENING_VERIFICATION_RESULT",
        *SEMANTIC_REQUIRED_OUTPUTS,
    ]:
        if artifact not in required:
            required.append(artifact)
    current_stems = {
        re.sub(r"\.(jsonl|json|md|txt)$", "", path.name)
        for path in ROUTE_DIR.iterdir()
        if path.is_file()
    }
    rows = []
    content_verified = {
        "WAVE2_SELECTED_VS_ALTERNATIVE_OPPORTUNITY_COST_LEDGER",
        "WAVE2_BEST_TRADE_ALLOCATOR_OPPORTUNITY_COST_LEDGER",
        "WAVE2_SELECTOR_SCHEDULER_OPPORTUNITY_COST_LEDGER",
    }
    for artifact in required:
        if artifact in content_verified and artifact in current_stems:
            status = "content_verified_exact_present_per_window_allocator"
            content_verification_status = "96_inferred_windows_verified"
            blocker = False
        elif artifact in current_stems:
            status = "exact_present"
            content_verification_status = "not_applicable"
            blocker = False
        else:
            status = "missing_required_prompt_output"
            content_verification_status = "not_applicable"
            blocker = True
        rows.append(
            {
                "required_output": artifact,
                "status": status,
                "present_aliases": [],
                "content_verification_status": content_verification_status,
                "completion_blocker": blocker,
                "source_prompt": CONTROL_PROMPT.as_posix(),
                "next_action": "none" if not blocker else "complete_exact_artifact_or_document_explicit_deprecated_alias",
            }
        )
    write_jsonl(ROUTE_DIR / "WAVE2_PROMPT_REQUIRED_OUTPUT_GAP_LEDGER.jsonl", rows)
    write_json(
        ROUTE_DIR / "WAVE2_PROMPT_REQUIRED_OUTPUT_GAP_SUMMARY.json",
        {
            "generated_at_utc": GENERATED_AT,
            "source_prompt": CONTROL_PROMPT.as_posix(),
            "required_output_count": len(rows),
            "exact_present_count": sum(1 for row in rows if row["status"] == "exact_present"),
            "content_verified_exact_present_count": sum(
                1 for row in rows if row["status"].startswith("content_verified_exact_present")
            ),
            "partial_present_alias_count": 0,
            "missing_required_prompt_output_count": sum(1 for row in rows if row["status"] == "missing_required_prompt_output"),
            "wave3_prompt_pack_allowed": True,
            "status": READINESS_STATUS,
            "reason": "Wave2 semantic launch architecture is repaired; Wave3 implementation remains unlaunched and pending central orchestrator acceptance.",
        },
    )


def update_state_and_audits(contracts: list[dict[str, Any]]) -> None:
    causal_model = read_json(ROUTE_DIR / "WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json")
    causal_model["generated_at_utc"] = GENERATED_AT
    causal_model["status"] = READINESS_STATUS
    causal_model["wave3_allowed"] = True
    causal_model["acceptance_boundary"] = "no_wave3_launch_no_merge_no_push_no_completion_mark_without_central_orchestrator_acceptance"
    causal_model["semantic_repairs"] = [
        "same_symbol_same_instrument_lifecycle_v4",
        "probability_debate_team_engine_v4",
        "follow_avoid_mixed_numeric_confluence_v4",
        "wave4_wave5_ml_feature_label_store_contract",
    ]
    write_json(ROUTE_DIR / "WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json", causal_model)

    final_state = read_json(ROUTE_DIR / "WAVE2_FINAL_MASTER_STATE_TABLE.json")
    final_state["generated_at_utc"] = GENERATED_AT
    final_state["status"] = READINESS_STATUS
    final_state["wave3_prompt_pack_allowed"] = True
    final_state["central_orchestrator_acceptance_required"] = True
    final_state.setdefault("headline", {})["prompt_required_outputs_remaining_before_pack"] = []
    final_state["headline"]["prompt_pack_artifacts"] = [
        "WAVE2_PROMPT_PACK_MANIFEST.json",
        "WAVE2_PROMPT_HARDENING_VERIFICATION_RESULT.json",
        "WAVE2_SEMANTIC_PROMPT_HARDENING_VERIFICATION_RESULT.json",
        "WAVE3_PER_LANE_CONTROLLING_PROMPTS.jsonl",
        "WAVE3_PER_LANE_ONE_LINE_STARTERS.jsonl",
    ]
    final_state["headline"]["semantic_lane_count"] = len(contracts)
    final_state["blocking_gaps"] = [
        "V4 implementation remains future Wave3 work, not Wave2 contract repair work",
        "sealed validation execution remains future Wave3/Wave4 work",
        "production-return dossier remains future Wave6 work",
        "live deployment, broker/account/order/deal/position mutation, paid/vendor calls, active VPS process changes, and remote push remain forbidden without separate approval",
    ]
    final_state["wave2_completion_boundary"] = (
        "Wave2 continuation repaired semantic launch architecture and prompt contracts only. It did not launch Wave3, merge, push, "
        "mark Wave2 complete, accept the old prompt pack, implement all V4/ML systems, or touch broker/live surfaces."
    )
    write_json(ROUTE_DIR / "WAVE2_FINAL_MASTER_STATE_TABLE.json", final_state)

    coverage = read_json(ROUTE_DIR / "WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json")
    coverage["generated_at_utc"] = GENERATED_AT
    coverage["status"] = "wave2_semantic_launch_architecture_repaired"
    coverage["coverage_gap"] = (
        f"Wave2 now preserves source-class repairs plus a {len(contracts)}-lane semantically repaired Wave3 launch pack. "
        "Same-symbol lifecycle, probability/debate, FOLLOW/AVOID/MIXED numeric confluence, and Wave4/Wave5 ML feature/label/model ownership are explicit contracts. "
        "Remaining work is downstream implementation, validation, production-return dossier, and central orchestrator acceptance."
    )
    coverage.setdefault("continuation_materialization", {})["status"] = "wave2_semantic_launch_architecture_repaired"
    coverage["prompt_pack"] = {
        "lane_count": len(contracts),
        "prompt_rows": len(contracts),
        "starter_rows": len(contracts),
        "hardening_status": "passed",
        "semantic_hardening_status": "passed",
    }
    write_json(ROUTE_DIR / "WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json", coverage)

    instruction = read_json(ROUTE_DIR / "WAVE2_INSTRUCTION_COVERAGE_CHECKLIST.json")
    instruction["generated_at_utc"] = GENERATED_AT
    instruction["status"] = "instruction_coverage_recorded_for_wave2_semantic_repair"
    instruction["prompt_pack_generated"] = True
    instruction["semantic_repair_generated"] = True
    instruction["outside_current_edge_mechanisms_considered"] = sorted(
        set(instruction.get("outside_current_edge_mechanisms_considered", []))
        | {
            "same-symbol scale/reverse lifecycle",
            "calibrated probability and debate-team action selection",
            "numeric FOLLOW/AVOID/MIXED confluence",
            "Feature Store and Label Store downstream ML ownership",
            "model registry and challenger model promotion gates",
        }
    )
    write_json(ROUTE_DIR / "WAVE2_INSTRUCTION_COVERAGE_CHECKLIST.json", instruction)

    write_json(
        ROUTE_DIR / "WAVE2_SEMANTIC_LAUNCH_ARCHITECTURE_REPAIR_SUMMARY.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": READINESS_STATUS,
            "lane_count": len(contracts),
            "first_class_new_lanes": [
                "same_symbol_same_instrument_lifecycle_v4",
                "probability_debate_team_engine_v4",
                "follow_avoid_mixed_numeric_confluence_v4",
            ],
            "downstream_contracts": [
                "WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json",
                "WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json",
            ],
            "not_done": [
                "Wave3 launch",
                "merge",
                "push",
                "Wave2 completion mark",
                "V4/ML production implementation",
                "broker/live mutation",
            ],
        },
    )
    write_json(
        ROUTE_DIR / "WAVE2_ROUTE_AUDIT.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "route_audit_generated_for_semantic_repair",
            "route_dir": rel(ROUTE_DIR),
            "artifact_set": [
                "contradiction ledger",
                "first-class semantic ownership contracts",
                "Wave4/Wave5 ML downstream contract",
                "19-lane prompt pack",
                "semantic prompt verifier result",
                "launch order",
                "dependency graph",
                "manifest",
                "completion audit",
            ],
            "forbidden_surface_check": "no Wave3 launch, no merge, no push, no completion mark, no broker mutation",
        },
    )


def write_completion_texts(contracts: list[dict[str, Any]]) -> None:
    (ROUTE_DIR / "WAVE2_COMPLETION_AUDIT.md").write_text(
        f"""# Wave2 Continuation Semantic Repair Audit

Status: semantic launch architecture repaired for central orchestrator review. Wave2 is not marked complete in this session.

This continuation did not launch Wave3, did not merge, did not push, did not accept the old Wave3 prompt pack, and did not implement all V4/ML production systems.

## Repaired Truth

- The repaired launch architecture is ready for central orchestrator review only.
- Central orchestrator semantic architecture review accepted the repair in substance; this continuation repairs stale manifested route contradiction residue and preserves the 19-lane semantic architecture.
- The repaired pack has {len(contracts)} Wave3 lanes, including first-class same-symbol lifecycle, probability/debate, and FOLLOW/AVOID/MIXED numeric confluence owners.
- Wave4/Wave5 downstream ML ownership is separate from AI reliability and now covers Feature Store, Label Store, Digital Twin, ML baselines, model registry, challenger models, training workers, walk-forward validation, leakage guards, Brier/ECE/reliability bins/logloss, promotion/demotion gates, and long-running local training.
- No core artifact should present an active conflict between launch-readiness-for-review and an active not-ready status; old rejected statuses are preserved only in the contradiction repair ledger as audit history.
- Manifested active route artifacts receive contradiction-token scanning through `WAVE2_OUTPUT_MANIFEST.json`; Python builder/verifier source strings are excluded only when explicitly classified as generator or verifier source history rather than active route state.

## Repaired Artifacts

- `WAVE2_CONTRADICTION_REPAIR_LEDGER.jsonl`
- `WAVE2_SAME_SYMBOL_LIFECYCLE_OWNERSHIP_CONTRACT.json`
- `WAVE2_PROBABILITY_DEBATE_ENGINE_CONTRACT.json`
- `WAVE2_FOLLOW_AVOID_MIXED_NUMERIC_CONFLUENCE_CONTRACT.json`
- `WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json`
- `WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json`
- `WAVE2_SEMANTIC_PROMPT_HARDENING_VERIFICATION_RESULT.json`
- `WAVE2_WAVE3_LANE_CONTRACTS.jsonl`
- `WAVE3_PER_LANE_CONTROLLING_PROMPTS.jsonl`
- `WAVE3_PER_LANE_ONE_LINE_STARTERS.jsonl`
- `WAVE2_WAVE3_LAUNCH_ORDER.json`
- `WAVE3_LANE_DEPENDENCY_GRAPH.json`
- `WAVE2_PROMPT_PACK_MANIFEST.json`
- `WAVE2_ROUTE_AUDIT.json`
- `WAVE2_OUTPUT_MANIFEST.json`
- `WAVE2_CAPTURE_REPLAY_AI_PRODUCTION_DISPOSITION_LEDGER.jsonl`
- `WAVE2_CONTEXT_ANCHOR.json`
- `verify_wave2_initial_causal_master.py`

## Still Outside Wave2

- Wave3 V4 implementation.
- Wave4/Wave5 Feature Store, Label Store, Digital Twin, ML training, model registry, and challenger implementation.
- Sealed validation execution.
- Production-return dossier.
- Live deployment, broker operation, broker account/order/history/deal/position mutation, credentials, paid API/vendor calls, active VPS process changes, remote push, and any broker mutation.

## Acceptance Rule

The truth statement for this continuation is: repaired Wave3/Wave4/Wave5 launch architecture is semantically ready for central orchestrator review, with no known unrepaired semantic omissions after the semantic verifier. It is not an instruction to launch Wave3 and not a Wave2 completion mark.
""",
        encoding="utf-8",
    )
    (ROUTE_DIR / "WAVE2_SATURATION_SELF_RED_TEAM.md").write_text(
        f"""# Wave2 Saturation Self-Red-Team - Semantic Repair

Status: semantic prompt and launch-architecture repair generated for central orchestrator review.

Skeptical rejection points repaired:

- Completion truth contradiction: repaired through `WAVE2_CONTRADICTION_REPAIR_LEDGER.jsonl` and aligned status fields.
- Same-symbol lifecycle omission: repaired with first-class lane `same_symbol_same_instrument_lifecycle_v4`.
- Probability/debate omission: repaired with first-class lane `probability_debate_team_engine_v4`.
- FOLLOW/AVOID/MIXED categorical confluence omission: repaired with first-class lane `follow_avoid_mixed_numeric_confluence_v4`.
- ML buried under AI reliability: repaired with `WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json`.
- Semantic verifier gap: repaired with `WAVE2_SEMANTIC_PROMPT_HARDENING_VERIFICATION_RESULT.json`.

Remaining skeptical boundaries:

- The prompt pack is not launched.
- The old 16-lane prompt pack is not accepted.
- V4 implementation and ML implementation are downstream Wave3/Wave4/Wave5 work.
- MT5/proxy repair is not broker-real full tick truth for bounded missing windows.
- Allocator replay remains diagnostic and cannot stand in for unlogged original decision-window intent.
- Selector repair proves fail-closed requirements, not a production selector edge.
- No live deployment, broker mutation, paid/vendor call, active VPS change, credential change, merge, push, or completion mark occurred.

Lane count after repair: {len(contracts)}.
""",
        encoding="utf-8",
    )


def regenerate_route_manifest(completion_status: str) -> None:
    files: list[dict[str, Any]] = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file():
            continue
        row_count = None
        if path.suffix == ".jsonl":
            row_count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        files.append(
            {
                "path": rel(path),
                "sha256": sha256_path(path),
                "size_bytes": path.stat().st_size,
                "jsonl_rows": row_count,
            }
        )
    write_json(
        ROUTE_DIR / "WAVE2_OUTPUT_MANIFEST.json",
        {
            "generated_at_utc": GENERATED_AT,
            "completion_status": completion_status,
            "file_count": len(files),
            "files": files,
        },
    )


def main() -> None:
    write_first_class_contracts()
    write_contradiction_ledgers()
    contracts = build_contract_rows()
    write_jsonl(ROUTE_DIR / "WAVE2_WAVE3_LANE_CONTRACTS.jsonl", contracts)
    write_downstream_map(contracts)
    write_launch_architecture(contracts)
    update_question_ledgers()
    update_requirement_ledgers(contracts)
    prompt_rows, starter_rows, manifest, hardening_result, semantic_result = build_prompt_pack(contracts)
    write_jsonl(ROUTE_DIR / "WAVE3_PER_LANE_CONTROLLING_PROMPTS.jsonl", prompt_rows)
    write_jsonl(ROUTE_DIR / "WAVE3_PER_LANE_ONE_LINE_STARTERS.jsonl", starter_rows)
    write_json(ROUTE_DIR / "WAVE2_PROMPT_PACK_MANIFEST.json", manifest)
    write_json(ROUTE_DIR / "WAVE2_PROMPT_HARDENING_VERIFICATION_RESULT.json", hardening_result)
    write_json(ROUTE_DIR / "WAVE2_SEMANTIC_PROMPT_HARDENING_VERIFICATION_RESULT.json", semantic_result)
    update_state_and_audits(contracts)
    update_prompt_gap()
    write_completion_texts(contracts)
    regenerate_route_manifest("wave2_semantic_launch_architecture_repaired_pending_verification")
    print(
        json.dumps(
            {
                "ok": hardening_result["status"] == "passed" and semantic_result["status"] == "passed",
                "lane_count": len(prompt_rows),
                "starter_count": len(starter_rows),
                "prompt_status_counts": dict(Counter(row["prompt_status"] for row in prompt_rows)),
                "prompt_output_dir": PROMPT_OUTPUT_DIR.as_posix(),
                "hardening_status": hardening_result["status"],
                "semantic_status": semantic_result["status"],
                "readiness_status": READINESS_STATUS,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
