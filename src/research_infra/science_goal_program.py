"""Research-control scaffolding for the primitive-science goal program.

The program is planning and coordination only. It writes schemas, prompt
contracts, empty registries, and launch maps; it does not call AI services,
fetch paid data, touch MT5, or alter live trading behavior.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RESULT_BOUNDARY = "RESEARCH_RESULT_BOUNDARY"
PROGRAM_DATE = "2026-05-06"
PROGRAM_ROOT = Path("research/science_program_2026_05")
EXTERNAL_WORKTREE_ROOT = r"C:\tmp\gtosg"
SCHEMA_VERSION = "science_goal_program_control_v1"
STATUS_READY = "SCIENCE_GOAL_PROGRAM_READY_RESEARCH_ONLY"
ACCESS_REQUEST_POLICY = (
    "If the goal session is blocked by sandbox, filesystem ACL, pytest temp-dir, local Git ref/write, "
    "network, `curl.exe`, web-fetch/search tooling, or public link/sitemap crawling needed for this "
    "research program, request access instead of stopping; the owner has stated access requests for this "
    "program will be granted. If web search is insufficient, use direct public fetches, links, and sitemaps "
    "to understand source content, save raw responses/source-index evidence before making claims, and cite "
    "the saved evidence. This does not authorize paid external spend, paywall/credential bypass, MT5/order/"
    "live-trading actions, credential changes, remote pushes, or changes to forbidden live trading areas."
)
DEEP_RESEARCH_POLICY = (
    "Use maximum deliberate reasoning before and during search. Start by writing what mechanisms would be "
    "worth finding, what evidence would distinguish them from noise, which GTOS components they could affect, "
    "and where the strongest evidence is likely to live. Do not perform one shallow web search and summarize it. "
    "Iterate through local context, papers, books, PDFs, exchange/vendor/regulator/platform docs, datasets, "
    "source-code references, and credible public sources when relevant. Hunt for counter-evidence, decay modes, "
    "duplicate routes, hidden leakage, implementation blockers, and non-obvious market behaviors most traders "
    "would miss. Every new ambiguity must become an answered question, a sharper hypothesis, or an explicit "
    "blocked item with the next evidence needed."
)
CONTEXT_LEDGER_POLICY = (
    "Maintain a lane context ledger as you work. Record each important artifact/source read, the claim or "
    "mechanism it changed, the next question it created, and the next source or repo check to pursue. If live "
    "state or research context may be stale, regenerate/read it again before relying on it. If lost, formulate "
    "the exact question, search locally and publicly for the answer, and ask the owner only when the answer "
    "requires a preference, credential, paid-source decision, or live-system approval."
)

NO_ACTION_COUNTERS = {
    "ai_calls": 0,
    "canary_calls": 0,
    "mt5_calls": 0,
    "order_calls": 0,
    "paid_data_calls": 0,
    "paid_fetch_attempted": False,
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
    "no_live_trading_behavior_change": True,
}

SCHEMA_REQUIRED_FIELDS: dict[str, list[str]] = {
    "science_mechanism_v1": [
        "mechanism_id",
        "science_domain",
        "market_behavior",
        "expected_signature",
        "required_data",
        "known_decay_mode",
        "existing_gtos_overlap",
        "killed_route_check",
        "result_boundary",
    ],
    "science_hypothesis_v1": [
        "hypothesis_id",
        "mechanism_id",
        "null",
        "alternative",
        "symbols",
        "timeframes",
        "entry_or_filter_or_exit_role",
        "label_class",
        "no_leak_fields",
        "sample_floor",
        "test_method",
        "live_change_blockers",
        "result_boundary",
    ],
    "experiment_prereg_v1": [
        "experiment_id",
        "hypothesis_id",
        "frozen_at_utc",
        "outcome_window_state",
        "metric",
        "cohort",
        "exclusions",
        "duplicate_policy",
        "cost_slippage_assumptions",
        "dsr_pbo_effective_n_policy",
        "label_separation_policy",
        "reproducibility_key",
        "result_boundary",
    ],
    "source_contract_v2": [
        "source_id",
        "url_or_vendor",
        "access_legal_state",
        "cost_rule",
        "publication_asof_timestamp_rule",
        "cache_path",
        "allowed_feature_role",
        "source_use_state",
        "source_use_blockers",
        "result_boundary",
    ],
    "goal_status_v1": [
        "lane_id",
        "lane_status",
        "files_written",
        "tests_run",
        "blockers",
        "next_questions",
        "commit_sha",
        "result_boundary",
    ],
}

SCHEMA_FIELD_NOTES: dict[str, dict[str, str]] = {
    "science_mechanism_v1": {
        "mechanism_id": "Stable ID, e.g. SCI-MICRO-OFI-001.",
        "science_domain": "Primitive science source family, not a public trading-strategy label.",
        "market_behavior": "Observable GTOS-relevant behavior the mechanism should create.",
        "expected_signature": "Point-in-time signature expected before the decision/outcome.",
        "required_data": "Exact source rows required to observe it.",
        "known_decay_mode": "Why the effect may vanish, crowd, reverse, or become regime-specific.",
        "existing_gtos_overlap": "Active, shadow, killed, blocked, or untested GTOS route.",
        "killed_route_check": "Artifact/grep/handoff check proving this is not reopening a killed route.",
    },
    "science_hypothesis_v1": {
        "null": "Concrete null that can fail without subjective interpretation.",
        "alternative": "Expected direction and cohort where the mechanism should help.",
        "label_class": "One of broker_actual_r, synthetic_path_r, lifecycle_no_fill, observation_only, or context_only.",
        "no_leak_fields": "Feature names that are decision-time/as-of only.",
        "sample_floor": "Minimum n/effective-N before any result can be accepted.",
        "live_change_blockers": "Reasons this cannot leave research/shadow status.",
    },
    "experiment_prereg_v1": {
        "frozen_at_utc": "Must be present before outcome review.",
        "outcome_window_state": "Must be frozen and not opened at registration time.",
        "duplicate_policy": "How repeated setup/path rows are deduped.",
        "dsr_pbo_effective_n_policy": "DSR/PBO/effective-N calculation or not_computable reason.",
        "label_separation_policy": "Prevents broker actual-R, synthetic path-R, lifecycle, and observation labels from mixing.",
    },
    "source_contract_v2": {
        "publication_asof_timestamp_rule": "Exact publication/as-of convention; report date alone is not enough for macro sources.",
        "allowed_feature_role": "Decision-time feature, context-only, forensic-only, or blocked.",
        "source_use_state": "Blocked until source legality, timestamp, cache, parser, and no-lookahead tests pass.",
    },
    "goal_status_v1": {
        "commit_sha": "Set after scoped commit in the lane worktree; null while not run.",
        "result_boundary": "Always RESEARCH_RESULT_BOUNDARY unless a separate owner-approved production-change dossier exists.",
    },
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def lane_specs() -> list[dict[str, Any]]:
    """Return all coordinator, science, and red-team lane definitions."""

    return [
        {
            "lane_id": "G0",
            "lane_name": "Program Governor",
            "worktree_slug": "G0_program_governor",
            "branch": "science-goals/g0-program-governor",
            "role": "coordinator",
            "science_domain": "research governance",
            "objective": (
                "Own worktree map, master registry, source/budget ledger, merge discipline, "
                "stale-route checks, lane reconciliation, and final synthesis."
            ),
            "primary_outputs": [
                "00_control/WORKTREE_MAP_2026-05-06.md",
                "00_control/SOURCE_BUDGET_LEDGER_2026-05-06.md",
                "05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md",
            ],
            "neighbor_lanes": ["G1", "G4", "G9"],
        },
        {
            "lane_id": "G1",
            "lane_name": "Validation Probability Statistics Causality",
            "worktree_slug": "G1_validation_statistics",
            "branch": "science-goals/g1-validation-statistics",
            "role": "science_lane",
            "science_domain": "validation, probability, statistics, causality",
            "objective": (
                "Extract mechanisms from DSR/PBO/effective-N, CPCV, causal inference, leakage control, "
                "multiple testing, power analysis, and sample-floor policy."
            ),
            "primary_outputs": ["01_domain_syntheses/G1_VALIDATION_STATISTICS_SYNTHESIS.md"],
            "neighbor_lanes": ["G2", "G9", "G10"],
        },
        {
            "lane_id": "G2",
            "lane_name": "Stochastic Processes Time Series Tails",
            "worktree_slug": "G2_stochastic_tails",
            "branch": "science-goals/g2-stochastic-tails",
            "role": "science_lane",
            "science_domain": "stochastic processes, time series, tails",
            "objective": (
                "Extract mechanisms from SDEs, Markov/HMM state models, GARCH/EVT, rough volatility, "
                "drawdown/tail risk, hazard models, and survival timing."
            ),
            "primary_outputs": ["01_domain_syntheses/G2_STOCHASTIC_TAILS_SYNTHESIS.md"],
            "neighbor_lanes": ["G1", "G3", "G10"],
        },
        {
            "lane_id": "G3",
            "lane_name": "Geometry Fractals Signal Processing",
            "worktree_slug": "G3_geometry_signal",
            "branch": "science-goals/g3-geometry-signal",
            "role": "science_lane",
            "science_domain": "geometry, fractals, signal processing",
            "objective": (
                "Translate swings, directional change, wavelets, Fourier/spectral coherence, Hurst, "
                "multifractal, and measurable topology ideas into GTOS hypotheses."
            ),
            "primary_outputs": ["01_domain_syntheses/G3_GEOMETRY_SIGNAL_SYNTHESIS.md"],
            "neighbor_lanes": ["G2", "G4", "G6"],
        },
        {
            "lane_id": "G4",
            "lane_name": "Market Microstructure Order Book Auction",
            "worktree_slug": "G4_microstructure_auction",
            "branch": "science-goals/g4-microstructure-auction",
            "role": "science_lane",
            "science_domain": "market microstructure, order book, auction",
            "objective": (
                "Extract mechanisms from OFI, queueing, liquidity, footprint, volume profile, VWAP, "
                "opening/closing auctions, stop cascades, and futures-proxy transfer."
            ),
            "primary_outputs": ["01_domain_syntheses/G4_MICROSTRUCTURE_AUCTION_SYNTHESIS.md"],
            "neighbor_lanes": ["G3", "G6", "G11"],
        },
        {
            "lane_id": "G5",
            "lane_name": "Behavioral Finance Psychology Game Theory",
            "worktree_slug": "G5_behavioral_game",
            "branch": "science-goals/g5-behavioral-game",
            "role": "science_lane",
            "science_domain": "behavioral finance, psychology, game theory",
            "objective": (
                "Translate herding, crowded trendline/ICT behavior, adaptive markets, predatory trading, "
                "forced flow, and reactions to news/AI into measurable mechanisms."
            ),
            "primary_outputs": ["01_domain_syntheses/G5_BEHAVIORAL_GAME_SYNTHESIS.md"],
            "neighbor_lanes": ["G4", "G6", "G7"],
        },
        {
            "lane_id": "G6",
            "lane_name": "Momentum Continuation Breakout Mean Reversion",
            "worktree_slug": "G6_momentum_reversion",
            "branch": "science-goals/g6-momentum-reversion",
            "role": "science_lane",
            "science_domain": "momentum, continuation, breakout, mean reversion",
            "objective": (
                "Study continuation/no-retrace, opening ranges, impulse-pullback, trend persistence, "
                "reversal exhaustion, and stat-arb analogues as primitive mechanisms."
            ),
            "primary_outputs": ["01_domain_syntheses/G6_MOMENTUM_REVERSION_SYNTHESIS.md"],
            "neighbor_lanes": ["G3", "G5", "G10"],
        },
        {
            "lane_id": "G7",
            "lane_name": "Macro Cross Asset Rates FX Gold",
            "worktree_slug": "G7_macro_cross_asset",
            "branch": "science-goals/g7-macro-cross-asset",
            "role": "science_lane",
            "science_domain": "macro, cross-asset, rates, FX, gold",
            "objective": (
                "Translate DXY, yields, real rates, COT, BIS/FRED/Fed, LBMA/fix effects, "
                "gold/silver/index/JPY/GBP context into source-aware hypotheses."
            ),
            "primary_outputs": ["01_domain_syntheses/G7_MACRO_CROSS_ASSET_SYNTHESIS.md"],
            "neighbor_lanes": ["G5", "G8", "G11"],
        },
        {
            "lane_id": "G8",
            "lane_name": "Options Gamma Volatility Risk Premium",
            "worktree_slug": "G8_options_vol",
            "branch": "science-goals/g8-options-vol",
            "role": "science_lane",
            "science_domain": "options, gamma, volatility risk premium",
            "objective": (
                "Translate GEX, dealer hedging, VIX1D/VIX9D, GVZ/VVIX, VRP construction, "
                "and OPEX regimes into source-contracted shadow hypotheses."
            ),
            "primary_outputs": ["01_domain_syntheses/G8_OPTIONS_VOL_SYNTHESIS.md"],
            "neighbor_lanes": ["G2", "G7", "G10"],
        },
        {
            "lane_id": "G9",
            "lane_name": "AI ML RL LLM Trading Systems",
            "worktree_slug": "G9_ai_ml_systems",
            "branch": "science-goals/g9-ai-ml-systems",
            "role": "science_lane",
            "science_domain": "AI, ML, RL, LLM trading systems",
            "objective": (
                "Map K55 target/model paths, no-leak feature bundles, classical-vs-LLM comparisons, "
                "tool grounding, debate, and Reflexion into shadow-only experiments."
            ),
            "primary_outputs": ["01_domain_syntheses/G9_AI_ML_SYSTEMS_SYNTHESIS.md"],
            "neighbor_lanes": ["G1", "G4", "G10"],
        },
        {
            "lane_id": "G10",
            "lane_name": "Execution Entries Exits Risk Portfolio",
            "worktree_slug": "G10_execution_risk",
            "branch": "science-goals/g10-execution-risk",
            "role": "science_lane",
            "science_domain": "execution, entries, exits, risk, portfolio",
            "objective": (
                "Translate internal pending vs native pending, slippage, path timing, J46/J49 successors, "
                "re-entry/trailing, and prop-firm constraints into preregistered shadow lanes."
            ),
            "primary_outputs": ["01_domain_syntheses/G10_EXECUTION_RISK_SYNTHESIS.md"],
            "neighbor_lanes": ["G1", "G6", "G9"],
        },
        {
            "lane_id": "G11",
            "lane_name": "Data Sources And Market Expansion",
            "worktree_slug": "G11_data_sources_expansion",
            "branch": "science-goals/g11-data-sources-expansion",
            "role": "science_lane",
            "science_domain": "data sources and market expansion",
            "objective": (
                "Govern Sierra/Databento/source contracts, new instruments, observer lanes, data-quality bias, "
                "legality, cost, and freshness without turning expansion into a production-change claim."
            ),
            "primary_outputs": ["01_domain_syntheses/G11_DATA_SOURCES_EXPANSION_SYNTHESIS.md"],
            "neighbor_lanes": ["G4", "G7", "G8"],
        },
        {
            "lane_id": "G12",
            "lane_name": "Red Team Leakage Source Validity",
            "worktree_slug": "G12_red_team",
            "branch": "science-goals/g12-red-team",
            "role": "red_team",
            "science_domain": "methodology red team",
            "objective": (
                "Review top hypotheses for leakage, post-hoc selection, duplicate counting, "
                "synthetic-vs-actual label confusion, source invalidity, and live-change drift."
            ),
            "primary_outputs": ["05_synthesis/G12_RED_TEAM_REVIEW.md"],
            "neighbor_lanes": ["G1", "G9", "G11"],
        },
    ]


def schema_contracts() -> dict[str, dict[str, Any]]:
    return {
        name: {
            "schema_name": name,
            "required_fields": fields,
            "field_notes": SCHEMA_FIELD_NOTES.get(name, {}),
            "result_boundary": RESULT_BOUNDARY,
        }
        for name, fields in SCHEMA_REQUIRED_FIELDS.items()
    }


def required_lane_stop_outputs(lane_id: str) -> list[str]:
    if lane_id == "G0":
        return [
            "worktree map",
            "source/budget ledger",
            "master mechanism registry",
            "master hypothesis registry",
            "master preregistry",
            "lane status registry",
            "governor context and ambiguity ledger",
            "cross-agent synthesis",
        ]
    if lane_id == "G12":
        return [
            "red-team review",
            "red-team context and ambiguity ledger",
            "leakage ledger",
            "duplicate-counting review",
            "label-separation review",
            "source-validity review",
            "survivor/blocker decisions",
        ]
    return [
        "domain synthesis",
        "lane context ledger with search plan, sources read, evolving questions, and stale-context refreshes",
        "ambiguity ledger with pursued answers, blockers, sharper hypotheses, and owner questions if needed",
        "counter-evidence and decay-mode review",
        "mechanism rows",
        "hypothesis rows",
        "killed-route notes",
        "experiment prereg specs",
        "source/budget blockers",
        "neighbor-lane cross-domain hypotheses after first synthesis pass",
    ]


def validate_schema_row(schema_name: str, row: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    required = set(SCHEMA_REQUIRED_FIELDS[schema_name])
    missing = sorted(required - set(row))
    if missing:
        issues.append(f"{schema_name}:MISSING_FIELDS:{','.join(missing)}")
    if row.get("result_boundary") != RESULT_BOUNDARY:
        issues.append(f"{schema_name}:RESULT_BOUNDARY_MISMATCH")

    if schema_name == "source_contract_v2":
        ready = str(row.get("source_use_state") or "").upper() == "READY_FOR_VALIDATION_USE"
        blockers = row.get("source_use_blockers") or []
        legal = str(row.get("access_legal_state") or "").upper()
        cost = str(row.get("cost_rule") or "").upper()
        role = str(row.get("allowed_feature_role") or "").upper()
        if ready and blockers:
            issues.append("source_contract_v2:SOURCE_USE_READY_WITH_BLOCKERS")
        if ready and any(token in legal for token in ("BLOCKED", "REQUIRED", "UNKNOWN", "PAID")):
            issues.append("source_contract_v2:BLOCKED_OR_INCOMPLETE_SOURCE_MARKED_READY_FOR_USE")
        if ready and ("PAID" in cost or "APPROVAL_REQUIRED" in cost):
            issues.append("source_contract_v2:PAID_SOURCE_MARKED_READY_WITHOUT_APPROVAL")
        if ready and ("FORWARD_CONTEXT_ONLY" in role or "FORENSIC_ONLY" in role):
            issues.append("source_contract_v2:NON_VALIDATION_ROLE_MARKED_READY_FOR_USE")

    if schema_name == "experiment_prereg_v1":
        if row.get("outcome_window_state") != "FROZEN_NOT_OPENED":
            issues.append("experiment_prereg_v1:OUTCOME_WINDOW_MUST_BE_CLOSED_AT_REGISTRATION")
        if not row.get("frozen_at_utc"):
            issues.append("experiment_prereg_v1:MISSING_FREEZE_TIMESTAMP")
        label_policy = str(row.get("label_separation_policy") or "")
        for token in ("broker_actual_r", "synthetic_path_r", "lifecycle", "observation"):
            if token not in label_policy:
                issues.append(f"experiment_prereg_v1:LABEL_POLICY_MISSING_{token.upper()}")

    if schema_name == "science_hypothesis_v1":
        no_leak_fields = row.get("no_leak_fields") or []
        if not isinstance(no_leak_fields, list) or not no_leak_fields:
            issues.append("science_hypothesis_v1:NO_LEAK_FIELDS_REQUIRED")
        label_class = row.get("label_class")
        allowed = {"broker_actual_r", "synthetic_path_r", "lifecycle_no_fill", "observation_only", "context_only"}
        if label_class not in allowed:
            issues.append("science_hypothesis_v1:LABEL_CLASS_NOT_ALLOWED")

    return issues


def initial_registries() -> dict[str, Any]:
    return {
        "mechanism_registry": {
            "schema": "science_mechanism_v1",
            "rows": [],
            "result_boundary": RESULT_BOUNDARY,
            "status": "EMPTY_PENDING_LANE_OUTPUTS",
        },
        "hypothesis_registry": {
            "schema": "science_hypothesis_v1",
            "rows": [],
            "result_boundary": RESULT_BOUNDARY,
            "status": "EMPTY_PENDING_LANE_OUTPUTS",
        },
        "experiment_preregistry": {
            "schema": "experiment_prereg_v1",
            "rows": [],
            "result_boundary": RESULT_BOUNDARY,
            "status": "EMPTY_PENDING_LANE_OUTPUTS",
        },
    }


def worktree_rows(lanes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "lane_id": lane["lane_id"],
            "lane_name": lane["lane_name"],
            "role": lane["role"],
            "branch": lane["branch"],
            "worktree_path": f"{EXTERNAL_WORKTREE_ROOT}\\{lane['lane_id']}",
            "base_ref": "main",
            "prompt_path": str(PROGRAM_ROOT / "04_goal_prompts" / f"{lane['lane_id']}_{lane['worktree_slug'].upper()}_GOAL_PROMPT_{PROGRAM_DATE}.md"),
            "created_by_this_builder": False,
            "creation_command": (
                f"git -C C:\\Users\\MSI\\Documents\\ai-trading-agent worktree add "
                f"-b {lane['branch']} \"{EXTERNAL_WORKTREE_ROOT}\\{lane['lane_id']}\" main"
            ),
        }
        for lane in lanes
    ]


def source_budget_ledger() -> dict[str, Any]:
    return {
        "schema": "science_source_budget_ledger_v1",
        "result_boundary": RESULT_BOUNDARY,
        "budget_posture": "ZERO_NEW_EXTERNAL_CASH_UNTIL_NUMERIC_CAP_AND_PER_SOURCE_LIMIT_ARE_OWNER_APPROVED",
        "current_external_cash_spend_cap_usd": 0.0,
        "per_source_limit_usd": None,
        "spend_allowed": False,
        "allowed_now": [
            "local repo artifacts",
            "existing local data",
            "existing Sierra files/access",
            "existing Databento credits only after manifest/cost estimate/cap ledger",
            "public web only when fetched, cached, and source-indexed under the research lane",
        ],
        "disallowed_until_owner_approval": [
            "new subscriptions",
            "paid trials",
            "account top-ups",
            "vendor purchases",
            "broad paid data pulls",
            "any source marked ready for validation use before source_contract_v2 tests pass",
        ],
        "ledger_rows": [],
    }


def goal_status_rows(lanes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "lane_id": lane["lane_id"],
            "lane_status": "READY_TO_LAUNCH_NOT_RUN",
            "files_written": [],
            "tests_run": [],
            "blockers": [],
            "next_questions": [
                "Launch lane in its own worktree.",
                "Produce required stop-condition artifacts before marking complete.",
            ],
            "commit_sha": None,
            "result_boundary": RESULT_BOUNDARY,
        }
        for lane in lanes
    ]


def orchestration_plan() -> dict[str, Any]:
    return {
        "launch_order": [
            {"phase": "coordinator_first", "lanes": ["G0"]},
            {"phase": "parallel_wave_1_max_6", "lanes": ["G1", "G2", "G3", "G4", "G5", "G6"]},
            {"phase": "parallel_wave_2_max_5", "lanes": ["G7", "G8", "G9", "G10", "G11"]},
            {"phase": "cross_domain_second_pass", "lanes": ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11"]},
            {"phase": "red_team_after_first_synthesis", "lanes": ["G12"]},
        ],
        "max_parallel_lanes": 8,
        "merge_owner": "G0",
        "merge_rule": "Lane outputs are reviewed and merged by G0 into master registries; science lanes write only their own files.",
        "result_boundary": RESULT_BOUNDARY,
    }


def build_payload(generated_at_utc: str | None = None) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    lanes = lane_specs()
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated,
        "status": STATUS_READY,
        "result_boundary": RESULT_BOUNDARY,
        "program_root": str(PROGRAM_ROOT),
        "external_worktree_root": EXTERNAL_WORKTREE_ROOT,
        "objective": (
            "Turn primitive sciences into GTOS mechanisms, preregistered hypotheses, "
            "shadow-only evidence lanes, and later production-change dossiers only if evidence survives."
        ),
        "first_wave_priority": "primitive_sciences_not_missed_move_only_or_market_expansion_only",
        "lanes": lanes,
        "lane_count": len(lanes),
        "science_lane_count": len([lane for lane in lanes if lane["role"] == "science_lane"]),
        "schema_contracts": schema_contracts(),
        "registries": initial_registries(),
        "worktree_map": worktree_rows(lanes),
        "source_budget_ledger": source_budget_ledger(),
        "goal_status_rows": goal_status_rows(lanes),
        "orchestration_plan": orchestration_plan(),
        "required_acceptance_tests": [
            "registry schema tests for mechanism, hypothesis, source, and prereg rows",
            "no-leak tests proving post-outcome fields are excluded from decision-time features",
            "duplicate active setup tests so repeated rows do not inflate opportunity counts",
            "label separation tests for broker actual-R, synthetic path-R, lifecycle/no-fill, and observation-only labels",
            "source contract tests blocking forward-context or paid/incomplete sources from ready source-use state",
            "reproducibility tests for frozen cohort plus prereg spec regeneration",
            "methodology report with DSR/PBO/effective-N or explicit not_computable reason",
        ],
        **NO_ACTION_COUNTERS,
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value).replace("|", "/")
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True).replace("|", "/")
    return str(value).replace("|", "/")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(item) for item in row) + " |")
    return out


def render_control_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# GTOS Primitive-Science Goal Program - 2026-05-06",
        "",
        f"**Status:** `{payload['status']}`",
        f"**Result boundary:** `{payload['result_boundary']}`",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Generated:** `{payload['generated_at_utc']}`",
        "",
        "## Purpose",
        "",
        payload["objective"],
        "",
        "This is a research-control scaffold. It does not launch trades, change prompts, alter risk, "
        "modify execution, call canaries, call MT5, fetch paid data, or produce a production-change assertion.",
        "",
        "## Launch Order",
        "",
    ]
    for phase in payload["orchestration_plan"]["launch_order"]:
        lines.append(f"- `{phase['phase']}`: {', '.join(phase['lanes'])}")
    lines.extend(
        [
            "",
            f"Maximum parallel science lanes: `{payload['orchestration_plan']['max_parallel_lanes']}`",
            "",
            "## Lanes",
            "",
            *_table(
                ["Lane", "Role", "Domain", "Worktree", "Neighbors"],
                [
                    [
                        lane["lane_id"],
                        lane["role"],
                        lane["science_domain"],
                        f"{EXTERNAL_WORKTREE_ROOT}\\{lane['lane_id']}",
                        lane["neighbor_lanes"],
                    ]
                    for lane in payload["lanes"]
                ],
            ),
            "",
            "## Required Acceptance Tests",
            "",
            *[f"- {item}" for item in payload["required_acceptance_tests"]],
            "",
            "## Safety Counters",
            "",
            f"- AI calls: `{payload['ai_calls']}`",
            f"- Canary calls: `{payload['canary_calls']}`",
            f"- MT5 calls: `{payload['mt5_calls']}`",
            f"- Order calls: `{payload['order_calls']}`",
            f"- Paid data calls: `{payload['paid_data_calls']}`",
            f"- Live behavior changed: `{not payload['no_live_trading_behavior_change']}`",
            "",
            "## Result Boundary",
            "",
            "All outputs from this program remain research/shadow-only until a separate owner-approved production-change dossier exists.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_schema_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Science Program Schema Contracts - 2026-05-06",
        "",
        f"**Result boundary:** `{payload['result_boundary']}`",
        "",
    ]
    for schema_name, contract in payload["schema_contracts"].items():
        lines.extend(
            [
                f"## {schema_name}",
                "",
                "Required fields:",
                "",
                *[f"- `{field}`" for field in contract["required_fields"]],
                "",
            ]
        )
        notes = contract.get("field_notes") or {}
        if notes:
            lines.extend(["Field notes:", ""])
            lines.extend(f"- `{field}`: {note}" for field, note in notes.items())
            lines.append("")
    lines.extend(
        [
            "## Enforcement Notes",
            "",
            "- `source_contract_v2.source_use_state` must remain blocked while access/legal state is blocked, paid approval is missing, or blockers remain.",
            "- `experiment_prereg_v1.outcome_window_state` must remain frozen and not opened at registration.",
            "- `science_hypothesis_v1.label_class` must keep broker actual-R, synthetic path-R, lifecycle/no-fill, observation-only, and context-only labels separated.",
            f"- Every row carries `{RESULT_BOUNDARY}`.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_worktree_markdown(payload: dict[str, Any]) -> str:
    rows = payload["worktree_map"]
    lines = [
        "# Science Program Worktree Map - 2026-05-06",
        "",
        f"**External root:** `{payload['external_worktree_root']}`",
        f"**Result boundary:** `{payload['result_boundary']}`",
        "",
        "This file records the intended isolated worktrees. The builder does not create external directories; run the generated PowerShell script only when ready to launch lanes.",
        "",
        *_table(
            ["Lane", "Branch", "Worktree", "Prompt"],
            [[row["lane_id"], row["branch"], row["worktree_path"], row["prompt_path"]] for row in rows],
        ),
        "",
        "## Creation Commands",
        "",
        "```powershell",
        'New-Item -ItemType Directory -Path "C:\\tmp\\gtosg" -Force | Out-Null',
        *[row["creation_command"] for row in rows],
        "```",
        "",
        "Do not stage runtime dirt from `main`; each lane commits only its scoped research files.",
    ]
    return "\n".join(lines) + "\n"


def render_source_budget_markdown(payload: dict[str, Any]) -> str:
    ledger = payload["source_budget_ledger"]
    lines = [
        "# Science Program Source And Budget Ledger - 2026-05-06",
        "",
        f"**Result boundary:** `{ledger['result_boundary']}`",
        f"**Budget posture:** `{ledger['budget_posture']}`",
        f"**Current external cash spend cap:** `${ledger['current_external_cash_spend_cap_usd']:.0f}`",
        f"**Per-source limit:** `{ledger['per_source_limit_usd']}`",
        f"**Spend allowed:** `{ledger['spend_allowed']}`",
        "",
        "## Allowed Now",
        "",
        *[f"- {item}" for item in ledger["allowed_now"]],
        "",
        "## Disallowed Until Owner Approval",
        "",
        *[f"- {item}" for item in ledger["disallowed_until_owner_approval"]],
        "",
        "## Ledger Rows",
        "",
        "`[]`",
        "",
        "No lane may spend cash or mark a source ready for validation use until this ledger has a numeric cap, per-source limit, source contract, and owner approval.",
    ]
    return "\n".join(lines) + "\n"


def render_master_registry_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Science Program Master Registry - 2026-05-06",
        "",
        f"**Status:** `{payload['status']}`",
        f"**Result boundary:** `{payload['result_boundary']}`",
        "",
        "## Initial Registry State",
        "",
        "- Mechanisms: `0`",
        "- Hypotheses: `0`",
        "- Experiment preregs: `0`",
        "- Goal status rows: `{}`".format(len(payload["goal_status_rows"])),
        "",
        "## Merge Rule",
        "",
        payload["orchestration_plan"]["merge_rule"],
        "",
        "## Survivor Backlog",
        "",
        "No survivor hypotheses exist yet. Survivors can enter a later experiment backlog only after lane outputs, cross-domain pass, and red-team review.",
        "",
        "## Ranking Criteria For Future Survivors",
        "",
        "- expected value",
        "- independence from OB-retest",
        "- feasibility",
        "- evidence strength",
        "- decay-defense value",
        "",
        "## Result Boundary",
        "",
        "This registry is empty by design until science lanes write evidence. Empty does not mean promoted, killed, or validated.",
    ]
    return "\n".join(lines) + "\n"


def render_domain_readme(payload: dict[str, Any]) -> str:
    lines = [
        "# Domain Syntheses",
        "",
        "Each science lane writes one domain synthesis here, then appends mechanism rows, hypothesis rows, killed-route notes, experiment specs, and blockers to its lane-owned files.",
        "",
        "Required lane outputs before completion:",
        "",
        "- domain synthesis",
        "- lane context ledger with search plan, sources read, evolving questions, and stale-context refreshes",
        "- ambiguity ledger with pursued answers, blockers, sharper hypotheses, and owner questions if needed",
        "- counter-evidence and decay-mode review",
        "- mechanism rows using `science_mechanism_v1`",
        "- hypothesis rows using `science_hypothesis_v1`",
        "- killed-route notes with file/line or artifact evidence",
        "- experiment prereg specs using `experiment_prereg_v1`",
        "- source/budget blockers using `source_contract_v2` where applicable",
        "- `goal_status_v1` update with files, tests, blockers, next questions, and commit SHA",
        "",
        f"`{RESULT_BOUNDARY}` applies to every row and report.",
    ]
    return "\n".join(lines) + "\n"


def render_goal_prompt_template() -> str:
    return """# Canonical Science Lane Goal Prompt Template - 2026-05-06

Use this template for every primitive-science lane.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered file in `.context/02_session_handoffs/`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_READING_ORDER.md` and the relevant Tier 2-4 artifacts.

## Worktree Boundary

Do not touch `main`. Work only inside the lane worktree. Do not stage runtime dirt. Commit only scoped lane files.

## Access Request Policy

If the goal session is blocked by sandbox, filesystem ACL, pytest temp-dir, local Git ref/write, network, `curl.exe`, web-fetch/search tooling, or public link/sitemap crawling needed for this research program, request access instead of stopping; the owner has stated access requests for this program will be granted. If web search is insufficient, use direct public fetches, links, and sitemaps to understand source content, save raw responses/source-index evidence before making claims, and cite the saved evidence. This does not authorize paid external spend, paywall/credential bypass, MT5/order/live-trading actions, credential changes, remote pushes, or changes to forbidden live trading areas.

## Objective

Extract mechanisms from primitive science, not public trading strategies. Every useful idea becomes measurable, preregistered, source-aware, and shadow-only.

## Deep Research Mode

Use maximum deliberate reasoning before and during search. Start by writing what mechanisms would be worth finding, what evidence would distinguish them from noise, which GTOS components they could affect, and where the strongest evidence is likely to live. Do not perform one shallow web search and summarize it. Iterate through local context, papers, books, PDFs, exchange/vendor/regulator/platform docs, datasets, source-code references, and credible public sources when relevant. Hunt for counter-evidence, decay modes, duplicate routes, hidden leakage, implementation blockers, and non-obvious market behaviors most traders would miss. Every new ambiguity must become an answered question, a sharper hypothesis, or an explicit blocked item with the next evidence needed.

## Context And Ambiguity Discipline

Maintain a lane context ledger as you work. Record each important artifact/source read, the claim or mechanism it changed, the next question it created, and the next source or repo check to pursue. If live state or research context may be stale, regenerate/read it again before relying on it. If lost, formulate the exact question, search locally and publicly for the answer, and ask the owner only when the answer requires a preference, credential, paid-source decision, or live-system approval.

## Repo Cross-Check

Before keeping any idea, verify whether GTOS already tested, killed, blocked, or activated it. Cite file paths and line evidence or mark the check incomplete with the exact blocker.

## Hypothesis Translation

Translate surviving mechanisms into `science_mechanism_v1`, `science_hypothesis_v1`, `experiment_prereg_v1`, and `source_contract_v2` rows where applicable.

## Stop Condition

The lane is not complete until it has produced domain synthesis, context ledger, ambiguity ledger, counter-evidence review, mechanism rows, hypothesis rows, killed-route notes, experiment specs, blockers, tests/verification notes, and a `goal_status_v1` row. Preserve explicit result-boundary fields.
"""


def render_lane_prompt(lane: dict[str, Any]) -> str:
    output_list = required_lane_stop_outputs(lane["lane_id"])
    lines = [
        f"# {lane['lane_id']} {lane['lane_name']} Goal Prompt - 2026-05-06",
        "",
        f"**Role:** `{lane['role']}`",
        f"**Domain:** `{lane['science_domain']}`",
        f"**Result boundary:** `{RESULT_BOUNDARY}`",
        f"**Worktree:** `{EXTERNAL_WORKTREE_ROOT}\\{lane['lane_id']}`",
        f"**Branch:** `{lane['branch']}`",
        "",
        "## Objective",
        "",
        lane["objective"],
        "",
        "## Mandatory Preflight",
        "",
        "1. Run `python scripts/generate_live_state.py`.",
        "2. Read `.context/LIVE_STATE.md`.",
        "3. Read the latest numbered file in `.context/02_session_handoffs/`.",
        "4. Read `.context/00_core/quick_reference_card.md`.",
        "5. Read `.context/00_core/research_operating_doctrine.md`.",
        "6. Read `.context/00_core/research_current_state.md`.",
        "7. Read `.context/00_READING_ORDER.md` and relevant Tier 2-4 artifacts.",
        "",
        "## Worktree Boundary",
        "",
        "Do not touch `main`. Work only inside this lane worktree. Do not stage runtime dirt. Commit only scoped lane files.",
        "",
        "## Access Request Policy",
        "",
        ACCESS_REQUEST_POLICY,
        "",
        "## Deep Research Mode",
        "",
        DEEP_RESEARCH_POLICY,
        "",
        "## Context And Ambiguity Discipline",
        "",
        CONTEXT_LEDGER_POLICY,
        "",
        "## Science-First Requirement",
        "",
        "Extract primitive mechanisms from the domain. Do not start from public trading strategies, missed-move lists, or market-expansion wishes.",
        "",
        "## Repo Cross-Check",
        "",
        "For each idea, verify whether it is already active, shadowed, blocked, killed, duplicated, or stale in GTOS. Cite paths and line evidence where possible.",
        "",
        "## Hypothesis Translation",
        "",
        "Every useful idea must become measurable, preregistered, source-aware, and label-safe. Use `science_mechanism_v1`, `science_hypothesis_v1`, `experiment_prereg_v1`, `source_contract_v2`, and `goal_status_v1`.",
        "",
        "## Required Stop Outputs",
        "",
        *[f"- {item}" for item in output_list],
        "",
        "## Neighbor Pass",
        "",
        f"After the first synthesis pass, read outputs from neighboring lanes: {', '.join(lane['neighbor_lanes'])}. Add only cross-domain hypotheses that survive source, leakage, and killed-route checks.",
        "",
        "## Forbidden",
        "",
        "- No live trading prompt changes.",
        "- No risk, execution, permissions, selector, or safety-gate changes.",
        "- No spending without source/budget ledger approval.",
        "- No live-scale or production-change claim.",
        "- No same-dataset discovery result labeled as validation.",
        "",
        "## Done Standard",
        "",
        f"Do not mark `{lane['lane_id']}` complete until files exist, focused checks are recorded, blockers are explicit, and every row/report carries `{RESULT_BOUNDARY}`.",
    ]
    return "\n".join(lines) + "\n"


def render_create_worktrees_script(payload: dict[str, Any]) -> str:
    lines = [
        "# Generated by scripts/build_science_goal_program.py",
        "$ErrorActionPreference = 'Stop'",
        '$Repo = "C:\\Users\\MSI\\Documents\\ai-trading-agent"',
        f'$Root = "{EXTERNAL_WORKTREE_ROOT}"',
        "New-Item -ItemType Directory -Path $Root -Force | Out-Null",
        "",
    ]
    for row in payload["worktree_map"]:
        lines.extend(
            [
                f'# {row["lane_id"]} {row["lane_name"] if "lane_name" in row else row["branch"]}',
                f'git -C $Repo worktree add -b {row["branch"]} "{row["worktree_path"]}" main',
            ]
        )
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_outputs(payload: dict[str, Any], *, root: Path = Path(".")) -> list[Path]:
    base = root / PROGRAM_ROOT
    outputs: list[Path] = []

    files: list[tuple[Path, Any, str]] = [
        (base / "00_control" / f"PROGRAM_GOVERNOR_{PROGRAM_DATE}.json", payload, "json"),
        (base / "00_control" / f"PROGRAM_GOVERNOR_{PROGRAM_DATE}.md", render_control_markdown(payload), "text"),
        (base / "00_control" / f"SCHEMA_CONTRACTS_{PROGRAM_DATE}.json", payload["schema_contracts"], "json"),
        (base / "00_control" / f"SCHEMA_CONTRACTS_{PROGRAM_DATE}.md", render_schema_markdown(payload), "text"),
        (base / "00_control" / f"WORKTREE_MAP_{PROGRAM_DATE}.json", payload["worktree_map"], "json"),
        (base / "00_control" / f"WORKTREE_MAP_{PROGRAM_DATE}.md", render_worktree_markdown(payload), "text"),
        (base / "00_control" / f"SOURCE_BUDGET_LEDGER_{PROGRAM_DATE}.json", payload["source_budget_ledger"], "json"),
        (base / "00_control" / f"SOURCE_BUDGET_LEDGER_{PROGRAM_DATE}.md", render_source_budget_markdown(payload), "text"),
        (base / "00_control" / f"GOAL_STATUS_REGISTRY_{PROGRAM_DATE}.json", payload["goal_status_rows"], "json"),
        (base / "00_control" / f"CREATE_WORKTREES_{PROGRAM_DATE}.ps1", render_create_worktrees_script(payload), "text"),
        (base / "01_domain_syntheses" / "README.md", render_domain_readme(payload), "text"),
        (base / "02_hypothesis_registry" / f"MECHANISM_REGISTRY_{PROGRAM_DATE}.json", payload["registries"]["mechanism_registry"], "json"),
        (base / "02_hypothesis_registry" / f"HYPOTHESIS_REGISTRY_{PROGRAM_DATE}.json", payload["registries"]["hypothesis_registry"], "json"),
        (base / "03_experiment_specs" / f"EXPERIMENT_PREREGISTRY_{PROGRAM_DATE}.json", payload["registries"]["experiment_preregistry"], "json"),
        (base / "04_goal_prompts" / f"CANONICAL_LANE_GOAL_PROMPT_TEMPLATE_{PROGRAM_DATE}.md", render_goal_prompt_template(), "text"),
        (base / "05_synthesis" / f"SCIENCE_PROGRAM_MASTER_REGISTRY_{PROGRAM_DATE}.json", {
            "schema_version": SCHEMA_VERSION,
            "result_boundary": RESULT_BOUNDARY,
            "registries": payload["registries"],
            "goal_status_rows": payload["goal_status_rows"],
            "survivor_backlog": [],
        }, "json"),
        (base / "05_synthesis" / f"SCIENCE_PROGRAM_MASTER_REGISTRY_{PROGRAM_DATE}.md", render_master_registry_markdown(payload), "text"),
    ]

    for lane in payload["lanes"]:
        prompt_name = f"{lane['lane_id']}_{lane['worktree_slug'].upper()}_GOAL_PROMPT_{PROGRAM_DATE}.md"
        files.append((base / "04_goal_prompts" / prompt_name, render_lane_prompt(lane), "text"))

    for path, content, kind in files:
        if kind == "json":
            _write_json(path, content)
        else:
            _write_text(path, str(content))
        outputs.append(path)

    return outputs
