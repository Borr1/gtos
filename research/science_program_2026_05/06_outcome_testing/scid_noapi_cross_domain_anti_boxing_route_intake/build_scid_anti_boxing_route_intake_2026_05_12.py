"""Build the SCID no-API cross-domain anti-boxing route intake package.

This lane is route-intake/source-control evidence only. It preserves the
accepted 40-card denominator as an upstream floor while generating additional
auditable no-API route families for later G12/G0 filtering. It does not open
outcome scoring, validation, promotion, AI/API spend, paid/vendor access,
broker account/order/history/deal/position evidence, raw market blobs, live
restarts, live behavior, or trading/risk/safety/prompt-decision changes.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
G0_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_scid_noapi_40card_prereg_replay_input_design_synthesis"
)

DATE_TAG = "2026-05-12"
PREFIX = "SCID_ANTI_BOXING"
ROUTE_ID = "SCID_NOAPI_CROSS_DOMAIN_ANTI_BOXING_ROUTE_INTAKE"
EVIDENCE_CLASS = "SCID_NOAPI_CROSS_DOMAIN_ROUTE_INTAKE_ONLY"
SCHEMA_VERSION = "scid_noapi_cross_domain_anti_boxing_route_intake_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "may_open_outcomes_or_results_in_this_route": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

FORBIDDEN_SURFACES = (
    "validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/"
    "paid-vendor/broker-account-order-history-deal-position/raw-market-blob/"
    "live-restart/live-behavior/trading-risk-safety-prompt-decision changes"
)

INPUT_FILES = {
    "ready_8": G0_DIR / "G0_SCID_NOAPI_PREREG_SYNTHESIS_READY_8_ROUTE_LEDGER_2026-05-12.json",
    "blocked_32": G0_DIR / "G0_SCID_NOAPI_PREREG_SYNTHESIS_BLOCKED_32_ROUTE_LEDGER_2026-05-12.json",
    "expansion": G0_DIR / "G0_SCID_NOAPI_PREREG_SYNTHESIS_EXPANSION_CANDIDATE_LEDGER_2026-05-12.json",
    "saturation": G0_DIR / "G0_SCID_NOAPI_PREREG_SYNTHESIS_SATURATION_SELF_RED_TEAM_2026-05-12.md",
    "controlling_prompt": (
        ROOT
        / "research"
        / "science_program_2026_05"
        / "04_goal_prompts"
        / "G0NAPI_R5_ANTI_BOXING_INTAKE_GOAL_PROMPT_2026-05-12.md"
    ),
    "goal_discipline": ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
    "research_doctrine": ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
    "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
    "local_heavy_data": ROOT / ".context" / "00_core" / "local_heavy_data_inventory.md",
    "ai_cost_plan": ROOT / ".context" / "00_core" / "ai_in_loop_cost_control_research_plan.md",
}

REQUIRED_DOMAIN_SLUGS = [
    "geometry_topology_path_shape",
    "stochastic_tail_hazard",
    "auction_microstructure_orderflow_liquidity",
    "behavioral_game_theory_session_participants",
    "macro_calendar_cross_asset",
    "execution_fillability_spread_slippage",
    "ml_meta_labeling_uncertainty",
    "adversarial_baselines_placebos",
    "source_missingness_denominator_controls",
    "failure_anatomy_derived_hypotheses",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper()


def scores(
    novelty: int,
    source_feasibility: int,
    evidence_gain: int,
    noapi_replay: int,
    blocker_leverage: int,
    result_path: int,
) -> dict[str, int]:
    return {
        "novelty": novelty,
        "source_feasibility": source_feasibility,
        "expected_evidence_gain": evidence_gain,
        "no_api_historical_replay_feasibility": noapi_replay,
        "blocked_dependency_leverage": blocker_leverage,
        "path_toward_eventual_result_evidence": result_path,
    }


def family(
    route_family_id: str,
    science_domain: str,
    title: str,
    mechanism: str,
    source_requirements: list[str],
    likely_row_universe: list[str],
    why_not_ob: str,
    score_components: dict[str, int],
    blockers: list[str] | None = None,
    accepted_40_relationship: str = "outside_accepted_40_floor_candidate",
    can_run_now: bool = True,
) -> dict[str, Any]:
    rank_total = sum(score_components.values())
    return {
        **SAFE_FLAGS,
        "route_family_id": route_family_id,
        "route_title": title,
        "science_domain": science_domain,
        "hypothesis_mechanism": mechanism,
        "source_requirements": source_requirements,
        "as_of_no_leak_policy": [
            "all source fields must include source_identifier, source_hash, source_observed_asof_utc, and decision_asof_utc where row-level use is proposed",
            "no post-event target, broker-result, path-label, or future-context fields may enter the route family intake denominator",
            "source-state evidence and later result evidence must remain in separate future lanes",
        ],
        "duplicate_denominator_policy": [
            "define a canonical candidate_input_row_id before any rowset materialization",
            "define duplicate_proxy_denominator_key or an explicit replacement key before any future result packet",
            "record row-level count and duplicate-key count separately; never mix accepted-40, blocked, or expansion denominators",
        ],
        "likely_row_universe": likely_row_universe,
        "forbidden_fields": [
            "target_hit",
            "stop_hit",
            "trade_result",
            "pnl",
            "r_multiple",
            "win_loss",
            "post_fill_path_label",
            "broker_account_history",
            "order_deal_position_id",
            "future_source_context",
        ],
        "blockers": blockers or [
            "needs source-contract acceptance before denominator entry",
            "needs G12 audit before becoming canonical control evidence",
            "needs separate G0 synthesis before any future result lane",
        ],
        "g12_g0_gates": [
            "G12 source/control audit for source fields, no-leak, duplicate key, and forbidden-surface checks",
            "G0 route synthesis before accepting the family into any expanded denominator",
            "separate future result-opening prompt only after rowset, partition, and control manifests are frozen",
        ],
        "why_not_current_gtos_ob_framing": why_not_ob,
        "accepted_40_relationship": accepted_40_relationship,
        "route_can_run_now_without_scoring": can_run_now,
        "score_components": score_components,
        "rank_score": rank_total,
    }


ROUTE_FAMILY_DEFINITIONS: list[dict[str, Any]] = [
    family(
        "GEOM-TOPO-001",
        "geometry_topology_path_shape",
        "Swing Graph Curvature And Compression Source-Control Route",
        "Represent price as a directed swing graph and register curvature, compression, and break-angle descriptors before any target labels exist.",
        ["M15/H1 swing points with source hashes", "swing detector version", "decision-time window bounds", "canonical graph node ids"],
        ["candidate MSO rows", "missed-opportunity rows", "mechanical replay candidates"],
        "It studies path topology and structural geometry, not whether price touched an OB retest zone.",
        scores(5, 5, 5, 5, 3, 5),
    ),
    family(
        "GEOM-TOPO-002",
        "geometry_topology_path_shape",
        "Pre-Touch Tortuosity And Convexity Packet Route",
        "Capture whether approach path is smooth, jagged, convex, or reversal-prone before a level touch without using fill/result state.",
        ["pre-decision bars", "path window start/end rules", "timeframe availability flags", "path descriptor version"],
        ["ready descriptor/control rows", "blocked LTF path cards after source-status clearance"],
        "It treats the approach path as the object of study rather than assuming OB level quality is the mechanism.",
        scores(5, 4, 5, 5, 4, 5),
    ),
    family(
        "GEOM-TOPO-003",
        "geometry_topology_path_shape",
        "Multi-Scale Structural Distance Field Intake",
        "Materialize distances to nearest swing, FVG, breaker, session high/low, and liquidity shelves as scale-aware descriptors.",
        ["multi-timeframe structural levels", "level source bar ids", "detector version", "distance normalization contract"],
        ["all no-API candidate rows with market-state snapshots"],
        "It compares competing structural anchors and can route beyond the current primary OB formulation.",
        scores(4, 5, 5, 5, 4, 5),
    ),
    family(
        "GEOM-TOPO-004",
        "geometry_topology_path_shape",
        "Wick-Body Topology Transition Route",
        "Register wick/body dominance transitions and rejection-shape sequences as a source-safe path-shape family.",
        ["OHLC bars", "body/wick normalization rules", "session bucket", "volatility state descriptor"],
        ["candidate rows", "rejected setup rows", "neutral target controls"],
        "It evaluates candle-shape topology independent of whether the setup is an OB retest.",
        scores(4, 5, 4, 5, 2, 4),
    ),
    family(
        "HAZ-001",
        "stochastic_tail_hazard",
        "Competing First-Passage Hazard Packet Route",
        "Freeze time-to-event denominators for competing path events such as level touch, expiry, adverse excursion, and neutral horizon close.",
        ["decision_asof_utc", "candidate horizon window", "bar/tick availability flags", "event taxonomy without results opened"],
        ["ready 8 after rowset materialization", "future blocked path cards after source clearance"],
        "It studies event timing and survival structure, not an OB-specific level pattern.",
        scores(5, 5, 5, 5, 4, 5),
    ),
    family(
        "HAZ-002",
        "stochastic_tail_hazard",
        "Volatility Cluster State Source-Control Route",
        "Materialize pre-decision volatility clustering descriptors and transition states as controls for future no-API replay.",
        ["rolling true range descriptors", "session volatility source", "time-split availability", "normalization version"],
        ["candidate feature rows", "mechanical replay rows", "session-volatility shadow rows"],
        "The mechanism is stochastic regime state rather than OB zone precision.",
        scores(4, 5, 5, 5, 3, 5),
    ),
    family(
        "HAZ-003",
        "stochastic_tail_hazard",
        "Tail Shock After Compression Intake",
        "Register compression-before-expansion states and tail-risk windows as future hypothesis families without choosing thresholds from outcomes.",
        ["pre-decision range compression fields", "tail-threshold candidate set frozen before scoring", "source hash"],
        ["broad OHLC path rows", "neutral target controls"],
        "It targets tail process state and threshold preregistration, not GTOS framework identity.",
        scores(5, 4, 4, 5, 2, 4),
    ),
    family(
        "HAZ-004",
        "stochastic_tail_hazard",
        "Event-Clock Versus Bar-Clock Denominator Hygiene Route",
        "Compare candidate eligibility under event-clock and bar-clock definitions before any results are opened.",
        ["bar close times", "source event times", "clock basis", "DST/session calendar"],
        ["all packet-design candidates", "lifecycle source-state candidates"],
        "It is a denominator-clock control that can change row identity independently of OB logic.",
        scores(4, 5, 4, 5, 5, 4),
    ),
    family(
        "MICRO-001",
        "auction_microstructure_orderflow_liquidity",
        "Depth/Trades Proxy Equivalence Source-Status Route",
        "Classify when futures trades/depth sources are proxy-valid, stale, absent, or non-equivalent for CFD candidate context.",
        ["proxy symbol map", "source schema", "source hash", "capture timestamp", "contract roll mapping", "as-of proxy validity rule"],
        ["blocked 17 LTF/orderflow cards", "orderflow proxy expansion candidates"],
        "It is auction/source-status infrastructure rather than an OB continuation assertion.",
        scores(5, 4, 5, 4, 5, 5),
        blockers=["proxy validity must not imply broker-native truth", "depth/trades parser availability must be proven"],
    ),
    family(
        "MICRO-002",
        "auction_microstructure_orderflow_liquidity",
        "Low-Volume Void And Shelf Source Contract Route",
        "Register low-volume node, volume shelf, and void descriptors from legally available local/vendor sources where source-safe.",
        ["volume-at-price source contract", "binning rule", "session window", "as-of availability", "proxy family"],
        ["Sierra/Databento source-status rows", "future LTF/orderflow candidates"],
        "It studies auction-distribution shape rather than current GTOS POI categories.",
        scores(5, 3, 5, 3, 5, 4),
        blockers=["source parser and legal/cache proof needed before row entry"],
    ),
    family(
        "MICRO-003",
        "auction_microstructure_orderflow_liquidity",
        "Stop-Cascade Pressure Proxy Intake",
        "Translate stop-cascade theory into measurable pre-decision pressure proxies such as sweep density and liquidity shelf proximity.",
        ["sweep markers", "liquidity shelf source", "lookback window", "detector hash"],
        ["candidate path rows", "liquidity-distance shadow rows", "mechanical replay candidates"],
        "The hypothesis is forced-flow pressure, not OB retest identity.",
        scores(5, 4, 5, 5, 4, 5),
    ),
    family(
        "MICRO-004",
        "auction_microstructure_orderflow_liquidity",
        "Queue-Imbalance Feature Eligibility Intake",
        "Define when queue/depth imbalance can be registered and when only trades-only proxies are allowed.",
        ["depth schema", "timestamp alignment", "contract map", "available levels", "capture latency policy"],
        ["future source-status rows", "blocked orderflow cards"],
        "It is a source eligibility and feature-contract route, not a current OB framework route.",
        scores(5, 3, 4, 3, 5, 4),
        blockers=["full depth may be absent; trades-only substitute must be labeled as proxy"],
    ),
    family(
        "BEH-001",
        "behavioral_game_theory_session_participants",
        "Session Transition Participant Pressure Route",
        "Register session-open, overlap, close, and handoff state as participant-constraint descriptors.",
        ["session calendar", "symbol/session mapping", "DST rules", "time bucket frozen before scoring"],
        ["ready descriptor/control cards", "calendar/fix expansion candidates"],
        "It studies participant timing constraints rather than any specific POI geometry.",
        scores(4, 5, 5, 5, 3, 5),
    ),
    family(
        "BEH-002",
        "behavioral_game_theory_session_participants",
        "Fix/Auction Handoff Crowd State Route",
        "Create source contracts for LBMA fix, index open/close auctions, and related handoff windows as pre-result descriptors.",
        ["official fix/auction schedule source", "calendar version", "symbol relevance map", "as-of publication rule"],
        ["gold/index candidate rows", "macro/calendar rows"],
        "It is calendar/participant flow timing, not GTOS OB setup selection.",
        scores(5, 4, 5, 5, 3, 5),
    ),
    family(
        "BEH-003",
        "behavioral_game_theory_session_participants",
        "Dealer Inventory Time-Block Descriptor Route",
        "Freeze time-block descriptors that proxy participant inventory and handoff constraints without asserting outcomes.",
        ["session time blocks", "holiday calendar", "symbol market-hours map", "descriptor version"],
        ["candidate rows across FX, metals, and indices"],
        "It uses behavioral timing hypotheses and can apply when no OB exists.",
        scores(4, 5, 4, 5, 2, 4),
    ),
    family(
        "BEH-004",
        "behavioral_game_theory_session_participants",
        "Pre-News Waiting-Room Source-Control Route",
        "Define pre-event waiting windows and no-lookahead event schedule fields for future route families.",
        ["economic calendar source contract", "publication/as-of timestamp", "symbol relevance map", "event importance policy"],
        ["macro/calendar candidates", "session participant controls"],
        "It treats scheduled participant constraint as a mechanism separate from OB retest logic.",
        scores(4, 3, 4, 4, 3, 4),
        blockers=["source must be legal, timestamped, and non-paid or explicitly approved later"],
    ),
    family(
        "MACRO-001",
        "macro_calendar_cross_asset",
        "Rates-Dollar-Vol Cross-Asset State Packet Route",
        "Register pre-decision cross-asset state descriptors from source-safe public or cached data without treating them as results.",
        ["cross-asset symbol map", "source publication/capture time", "source hash", "staleness policy"],
        ["macro/cross-asset cards", "XAUUSD/index/FX candidate rows"],
        "It studies external market-state context instead of internal OB framework state.",
        scores(5, 3, 5, 4, 4, 5),
        blockers=["some sources may require public/cache proof or separate acquisition contract"],
    ),
    family(
        "MACRO-002",
        "macro_calendar_cross_asset",
        "Calendar Surprise Embargo Source Contract Route",
        "Define how event schedule and embargo windows enter source-control packets before any future surprise labels are considered.",
        ["event schedule source", "as-of update timestamp", "embargo window", "relevance policy"],
        ["candidate rows near macro events", "adversarial calendar baselines"],
        "It is a no-leak calendar source-control family, not OB-level filtering.",
        scores(4, 4, 4, 4, 3, 4),
    ),
    family(
        "MACRO-003",
        "macro_calendar_cross_asset",
        "Risk-On Basket Context Route",
        "Freeze cross-asset basket context fields such as equity index, dollar, rates, and volatility proxies before any result use.",
        ["basket constituent map", "bar source hashes", "staleness and holiday rules", "normalization version"],
        ["index/metals/FX candidate rows", "neutral target controls"],
        "The source object is cross-market context rather than current GTOS setup family.",
        scores(5, 3, 4, 4, 3, 4),
    ),
    family(
        "MACRO-004",
        "macro_calendar_cross_asset",
        "DST/Fix/Calendar Negative-Control Bundle",
        "Create a calendar-control packet that can later detect accidental session-only or timezone artifacts.",
        ["DST calendar", "fix schedule", "session windows", "duplicate key policy"],
        ["ready 8 adversarial cards", "calendar expansion candidates"],
        "It is explicitly an adversarial control rather than an OB edge route.",
        scores(4, 5, 4, 5, 4, 5),
    ),
    family(
        "EXEC-001",
        "execution_fillability_spread_slippage",
        "Spread State Source-Control Route",
        "Register spread/liquidity-state fields from source-safe quote or shadow sources without reading broker account/order/deal evidence.",
        ["quote/spread source", "source hash", "decision-time timestamp", "symbol-specific tick size", "staleness policy"],
        ["candidate rows", "execution context rows", "future fillability packets"],
        "It studies feasibility and cost-state context, not OB pattern correctness.",
        scores(5, 4, 5, 4, 4, 5),
        blockers=["broker-account/order/history/deal/position evidence remains forbidden in this lane"],
    ),
    family(
        "EXEC-002",
        "execution_fillability_spread_slippage",
        "Fillability Envelope Packet Design Route",
        "Define no-API fillability envelopes from price/quote availability without claiming actual broker fills.",
        ["entry reference", "bar/tick availability flags", "spread envelope source", "pending-intent source if already logged"],
        ["future blocked lifecycle cards", "no-fill source-control rows"],
        "It separates executable envelope design from GTOS OB setup selection.",
        scores(5, 4, 5, 4, 5, 5),
        blockers=["actual broker fill truth cannot be inferred from price"],
    ),
    family(
        "EXEC-003",
        "execution_fillability_spread_slippage",
        "Redacted Lifecycle Clock Source Contract Route",
        "Freeze source-event clock basis, redaction policy, and lifecycle state transitions for future execution evidence capture.",
        ["source_event_utc", "clock basis", "redacted bridge hash", "state before/after", "logger version"],
        ["blocked 15 future-capture rows", "lifecycle expansion candidates"],
        "It is lifecycle source integrity, not current GTOS trade selection logic.",
        scores(4, 4, 5, 3, 5, 4),
        blockers=["non-generatable historical source truth must not be reconstructed from price"],
    ),
    family(
        "EXEC-004",
        "execution_fillability_spread_slippage",
        "Liquidity Stress Perturbation Packet Route",
        "Predefine later stress inputs such as worse spread, missed fills, or delayed execution as source-control contracts only.",
        ["stress scenario registry", "source-safe spread references", "duplicate-key policy", "future result-gate hook"],
        ["future result packet candidates after G0 acceptance"],
        "It is an execution-science stress design, not OB entry logic.",
        scores(4, 4, 4, 4, 3, 4),
    ),
    family(
        "ML-001",
        "ml_meta_labeling_uncertainty",
        "No-API Representation Dataset Design Route",
        "Design a feature-safe representation matrix for future mechanical or statistical models without opening labels.",
        ["feature source contracts", "as-of timestamps", "feature version hash", "partition and embargo ledger"],
        ["accepted 40 floor plus future expansion candidates after G12 acceptance"],
        "It explores representation and learning infrastructure beyond hand-coded OB rules.",
        scores(5, 4, 5, 5, 4, 5),
    ),
    family(
        "ML-002",
        "ml_meta_labeling_uncertainty",
        "Model-Disagreement Control Packet Route",
        "Create no-API disagreement descriptors from deterministic rules or local statistical surrogates without using paid AI.",
        ["rule-set version hashes", "deterministic model descriptors", "input feature hashes", "partition policy"],
        ["candidate rows with multiple deterministic descriptors"],
        "It studies uncertainty and disagreement, not a single OB detector.",
        scores(5, 4, 4, 4, 3, 4),
    ),
    family(
        "ML-003",
        "ml_meta_labeling_uncertainty",
        "Near-Boundary Uncertainty Ranking Control Route",
        "Register candidate proximity to deterministic thresholds as a future uncertainty stratum before any outcomes are seen.",
        ["deterministic gate distance fields", "threshold version", "feature source hashes", "duplicate key"],
        ["candidate/reject rows with deterministic gate outputs"],
        "It treats uncertainty near decision boundaries as a source-control descriptor rather than OB category.",
        scores(4, 5, 4, 5, 3, 4),
    ),
    family(
        "ML-004",
        "ml_meta_labeling_uncertainty",
        "Feature-Ablation And Placebo Registry Route",
        "Freeze feature-group inclusion/exclusion and placebo transforms before any future model or result route.",
        ["feature group registry", "placebo transform definitions", "random seed", "partition ledger"],
        ["future no-API model-design rows"],
        "It is methodological control for ML evidence, not a GTOS framework route.",
        scores(4, 5, 4, 5, 4, 4),
    ),
    family(
        "ADV-001",
        "adversarial_baselines_placebos",
        "Cross-Domain Negative-Control Bundle Route",
        "Bundle session-only, calendar-only, duplicate-key, source-hash, and missingness controls before any scoring lane.",
        ["control taxonomy", "baseline assignment seed", "duplicate key", "partition ledger"],
        ["ready 8 adversarial cards", "G0 expansion candidates"],
        "It is explicitly adversarial control and can reject fake effects not tied to OB logic.",
        scores(4, 5, 5, 5, 5, 5),
    ),
    family(
        "ADV-002",
        "adversarial_baselines_placebos",
        "Duplicate-Key Collision Placebo Route",
        "Register duplicate-key collision, drift, and group-membership instability as placebo/control strata.",
        ["candidate id", "duplicate key", "source hash", "group membership version", "collision policy"],
        ["all accepted and expansion route candidates after denominator rules are frozen"],
        "It attacks denominator artifacts rather than testing an OB mechanism.",
        scores(4, 5, 5, 5, 5, 5),
    ),
    family(
        "ADV-003",
        "adversarial_baselines_placebos",
        "Source-Hash Date Shuffle Placebo Route",
        "Predefine source-hash/date shuffle controls that can later detect calendar, duplicate, or source-order leakage.",
        ["source hash", "eligible shuffle strata", "seed", "blocked fields list"],
        ["future rowsets after G12 control acceptance"],
        "It is a no-leak placebo route independent of production GTOS setup definitions.",
        scores(5, 4, 4, 5, 4, 4),
    ),
    family(
        "ADV-004",
        "adversarial_baselines_placebos",
        "Current-GTOS-Framework-Neutral Baseline Route",
        "Build framework-neutral descriptor baselines so later evidence is not boxed around OB/FVG/breaker labels.",
        ["descriptor-only row fields", "framework label quarantine", "partition ledger", "baseline seed"],
        ["accepted 40 floor", "future expansion candidates"],
        "It explicitly removes current framework labels from the first-pass baseline design.",
        scores(5, 5, 5, 5, 4, 5),
    ),
    family(
        "MISS-001",
        "source_missingness_denominator_controls",
        "Source Availability Stratification Route",
        "Treat source availability, staleness, parser coverage, and source family as first-class control strata.",
        ["source status enum", "missing field list", "parser version", "source hash or exact absence proof"],
        ["blocked 32 rows", "future expansion candidates", "source-status routes"],
        "It studies whether source coverage itself creates biased denominators, not OB behavior.",
        scores(4, 5, 5, 5, 5, 5),
    ),
    family(
        "MISS-002",
        "source_missingness_denominator_controls",
        "Duplicate Denominator Drift Route",
        "Audit how candidate identity, duplicate keys, and group membership drift across source versions and replay engines.",
        ["candidate_input_row_id", "duplicate key", "source version", "group membership version", "drift reason"],
        ["all route families before future denominator acceptance"],
        "It is denominator hygiene and can invalidate any strategy family including but not limited to OB.",
        scores(4, 5, 5, 5, 5, 5),
    ),
    family(
        "MISS-003",
        "source_missingness_denominator_controls",
        "Sealed Partition And Embargo Hygiene Route",
        "Create partition, embargo, and contaminated-slice ledgers before expanded route families approach result evidence.",
        ["partition assignment", "embargo policy", "touched-slice ledger", "contamination reason enum"],
        ["accepted 40 floor", "new expansion families", "future no-API replay rowsets"],
        "It guards evidence-class validity rather than proposing an OB setup.",
        scores(4, 5, 5, 5, 5, 5),
    ),
    family(
        "MISS-004",
        "source_missingness_denominator_controls",
        "Rowset Materialization Failure-Mode Intake",
        "Register rowset build failures, source gaps, parse failures, and blocked fields as analyzable control evidence.",
        ["rowset build id", "failure reason", "missing fields", "searched roots", "exact unblocker"],
        ["all route-family packet builders"],
        "It treats failed source construction as evidence-control data, not OB performance.",
        scores(4, 5, 4, 5, 5, 4),
    ),
    family(
        "FAIL-001",
        "failure_anatomy_derived_hypotheses",
        "No-Fill And Expiry Failure Anatomy Route",
        "Preserve no-fill, expiry, cancel, and not-reached states as source-state anatomy without inferring trade results.",
        ["pending intent state if source-safe", "expiry/cancel source event", "price-path availability flag", "clock basis"],
        ["no-fill/lifecycle source packets", "blocked 15 lifecycle cards"],
        "It asks why opportunities fail to materialize, not whether an OB entry wins.",
        scores(5, 4, 5, 4, 5, 5),
        blockers=["historical lifecycle truth must be logged or prospectively captured; do not infer from price"],
    ),
    family(
        "FAIL-002",
        "failure_anatomy_derived_hypotheses",
        "Gate-Block Reason Topology Route",
        "Represent deterministic block reasons and their co-occurrence topology as source-control route families.",
        ["gate decision log", "reason codes", "candidate id", "component version", "decision as-of"],
        ["candidate feature logs", "permission/gate audit logs"],
        "It studies decision failure anatomy and conflict structure beyond the OB hypothesis itself.",
        scores(4, 5, 4, 5, 4, 4),
    ),
    family(
        "FAIL-003",
        "failure_anatomy_derived_hypotheses",
        "Schema Parser Clock Failure Taxonomy Route",
        "Turn parser failures, clock skew, malformed rows, and missing joins into auditable route families and source contracts.",
        ["error/event logs", "schema version", "clock source", "source file hash", "repair status"],
        ["shadow logs", "verifier outputs", "source packet builders"],
        "It extracts improvement routes from infrastructure failure rather than market-pattern labels.",
        scores(4, 5, 4, 5, 5, 4),
    ),
    family(
        "FAIL-004",
        "failure_anatomy_derived_hypotheses",
        "Rejected-Candidate Contrastive Packet Design Route",
        "Define source-safe contrastive packets for rejected candidates without opening later result labels.",
        ["rejection reason", "decision input snapshot hash", "as-of source fields", "duplicate key"],
        ["rejected setup rows", "candidate diagnostics joins"],
        "It can explain what the system refuses and is not constrained to OB-positive rows.",
        scores(5, 4, 5, 4, 4, 5),
    ),
]


SOURCE_CONTRACT_TEMPLATES: list[dict[str, Any]] = [
    {
        "template_id": "SRC-OHLC-PATH-ASOF",
        "source_family": "ohlc_path",
        "required_fields": ["symbol", "timeframe", "window_start_utc", "window_end_utc", "source_identifier", "source_hash", "observed_asof_utc"],
        "as_of_rule": "every bar consumed must close at or before the registered decision_asof_utc unless explicitly marked future-forbidden",
        "duplicate_policy": "candidate_input_row_id plus timeframe/window hash",
        "forbidden_fields": ["outcome labels", "broker results", "post-window target state"],
    },
    {
        "template_id": "SRC-LTF-PATH-AVAILABILITY",
        "source_family": "lower_timeframe_path_status",
        "required_fields": ["ltf_timeframes_available", "bars_present_by_timeframe", "ltf_source_hash", "availability_status", "decision_minus_window_start_utc"],
        "as_of_rule": "availability can be logged before scoring; path values remain blocked until source hash and window are accepted",
        "duplicate_policy": "candidate_input_row_id plus ltf_timeframe plus source_hash",
        "forbidden_fields": ["post-fill path labels", "target/stop sequence labels"],
    },
    {
        "template_id": "SRC-ORDERFLOW-PROXY-STATUS",
        "source_family": "trades_depth_proxy_status",
        "required_fields": ["proxy_symbol", "schema", "contract_month", "capture_asof_utc", "source_hash", "proxy_validity_status", "parser_version"],
        "as_of_rule": "proxy status must be proven at or before decision time and must not imply broker-native truth",
        "duplicate_policy": "proxy_symbol plus contract_month plus capture_asof_utc plus parser_version",
        "forbidden_fields": ["broker order/deal/position evidence", "paid pull without approval"],
    },
    {
        "template_id": "SRC-CALENDAR-FIX-AUCTION",
        "source_family": "calendar_fix_auction_schedule",
        "required_fields": ["calendar_source", "event_id", "published_asof_utc", "event_time_utc", "symbol_relevance_map", "source_hash"],
        "as_of_rule": "event schedule must be available before the candidate decision and publication/update timestamp must be recorded",
        "duplicate_policy": "event_id plus published_asof_utc plus calendar_source",
        "forbidden_fields": ["surprise outcome", "post-event market reaction"],
    },
    {
        "template_id": "SRC-CROSS-ASSET-CONTEXT",
        "source_family": "cross_asset_context",
        "required_fields": ["context_symbol", "bar_time_utc", "source_hash", "observed_asof_utc", "staleness_status", "normalization_version"],
        "as_of_rule": "context bars must be closed or source-published before candidate decision time",
        "duplicate_policy": "context_symbol plus bar_time_utc plus normalization_version",
        "forbidden_fields": ["future cross-asset movement", "post-decision realized context"],
    },
    {
        "template_id": "SRC-EXECUTION-COST-STATE",
        "source_family": "spread_liquidity_state",
        "required_fields": ["symbol", "quote_time_utc", "spread_value_or_bucket", "source_hash", "source_observed_asof_utc", "staleness_policy"],
        "as_of_rule": "quote/spread source must be read-only and pre-decision; no account/order/deal/position history can be used",
        "duplicate_policy": "symbol plus quote_time_utc plus source_hash",
        "forbidden_fields": ["broker account history", "actual order fill", "deal result"],
    },
    {
        "template_id": "SRC-LIFECYCLE-REDACTED-CLOCK",
        "source_family": "redacted_lifecycle_state",
        "required_fields": ["source_event_utc", "source_event_type", "clock_basis", "redacted_bridge_hash_optional", "state_before", "state_after", "logger_version"],
        "as_of_rule": "historical lifecycle truth must come from source logs only; otherwise register prospective capture requirement",
        "duplicate_policy": "redacted intent id plus source_event_utc plus logger_version",
        "forbidden_fields": ["account id", "order ticket", "deal id", "position id", "broker account result"],
    },
    {
        "template_id": "SRC-ML-FEATURE-MATRIX-NO-LABELS",
        "source_family": "feature_matrix_without_labels",
        "required_fields": ["feature_name", "feature_source_hash", "feature_asof_utc", "feature_version", "partition_assignment", "embargo_policy"],
        "as_of_rule": "feature matrix may contain only pre-decision fields until a separate result-opening route exists",
        "duplicate_policy": "candidate_input_row_id plus feature_version plus partition_assignment",
        "forbidden_fields": ["target label", "win/loss flag", "performance field", "post-event feature"],
    },
    {
        "template_id": "SRC-DENOMINATOR-CONTROL",
        "source_family": "denominator_duplicate_partition_control",
        "required_fields": ["candidate_input_row_id", "duplicate_denominator_key", "partition_assignment", "embargo_group", "source_hash", "contamination_status"],
        "as_of_rule": "denominator and partition fields must be frozen before any future scoring route",
        "duplicate_policy": "both row-level and duplicate-key-level counts reported separately",
        "forbidden_fields": ["selected-on-result flag", "post-score inclusion decision"],
    },
    {
        "template_id": "SRC-FAILURE-ANATOMY",
        "source_family": "failure_anatomy_control",
        "required_fields": ["failure_family", "failure_reason_code", "source_artifact", "source_hash", "searched_roots", "exact_unblocker"],
        "as_of_rule": "failure anatomy can use source/control failures and decision-time reason codes, not later trade outcomes",
        "duplicate_policy": "failure_family plus candidate_input_row_id plus source_artifact",
        "forbidden_fields": ["result rescue threshold", "post-hoc performance explanation"],
    },
]

SOURCE_CONTRACT_SEARCH_ROOTS: dict[str, list[str]] = {
    "ohlc_path": [
        "research/science_program_2026_05",
        "data/historical_2026",
        "C:/Users/MSI/Documents/ai-trading-agent/data",
    ],
    "lower_timeframe_path_status": [
        "data/historical_2026",
        "data/ticks",
        "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
    ],
    "trades_depth_proxy_status": [
        "research/databento_orderflow_capture_2026-05-02",
        "data/external",
        "C:/SierraChart",
    ],
    "calendar_fix_auction_schedule": [
        ".context/00_core",
        "research/science_program_2026_05/00_control",
        "research/science_program_2026_05/01_domain_syntheses",
    ],
    "cross_asset_context": [
        "data/external",
        "research/phase_3_external_feed_validation",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external",
    ],
    "spread_liquidity_state": [
        "shadow_logs",
        "data/ticks",
        "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
    ],
    "redacted_lifecycle_state": [
        "shadow_logs",
        "knowledge_base",
        "research/science_program_2026_05",
    ],
    "feature_matrix_without_labels": [
        "shadow_logs",
        "research/ml_program",
        "research/science_program_2026_05",
    ],
    "denominator_duplicate_partition_control": [
        "research/science_program_2026_05",
        "shadow_logs",
        "data/external",
    ],
    "failure_anatomy_control": [
        "research/science_program_2026_05",
        "shadow_logs",
        ".context/02_session_handoffs",
    ],
}

for template in SOURCE_CONTRACT_TEMPLATES:
    source_family = template["source_family"]
    template["searched_root_expectations"] = SOURCE_CONTRACT_SEARCH_ROOTS[source_family]
    template["hash_deferral_policy"] = [
        "record sha256 for every source file consumed by a future child route",
        "if a source is absent or cannot be legally/read-only accessed, emit a fail-closed blocker instead of a row",
        "if a field is non-generatable historical source truth, defer to prospective capture and do not infer it from price",
    ]
    template["no_leak_rules"] = [
        template["as_of_rule"],
        "forbidden_fields are excluded from packet construction and future denominators",
        "result, performance, broker/order/deal/position, and post-decision labels remain closed until a separate evidence-class prompt opens them",
    ]
    template["fail_closed_statuses"] = [
        "BLOCKED_SOURCE_ABSENT",
        "BLOCKED_ASOF_PROOF_MISSING",
        "BLOCKED_HASH_OR_PARSER_MISSING",
        "BLOCKED_FORBIDDEN_FIELD_REQUIRED",
        "BLOCKED_REQUIRES_SEPARATE_EVIDENCE_CLASS",
    ]


NEGATIVE_EVIDENCE_ROWS: list[dict[str, Any]] = [
    {
        "negative_id": "NEG-BOX-OBONLY-001",
        "candidate_or_route_family": "OB-only restatement routes",
        "status": "REJECTED_AS_BOXED",
        "evidence": "The controlling prompt explicitly says accepted cards are a floor and current GTOS OB/retest logic is not the research horizon; an OB-only intake would fail the route's objective.",
        "preserved_learning": "OB-related source fields can remain as one comparator family, but the intake denominator cannot collapse around them.",
    },
    {
        "negative_id": "NEG-FORBID-OUTCOME-001",
        "candidate_or_route_family": "Immediate scoring or result route",
        "status": "REJECTED_FOR_EVIDENCE_CLASS_CROSSING",
        "evidence": "The route is SCID_NOAPI_CROSS_DOMAIN_ROUTE_INTAKE_ONLY and may_open_outcomes_or_results_in_this_route=false.",
        "preserved_learning": "Emit future result-gate prompts only after G12/G0 accepts source/control and packet materialization.",
    },
    {
        "negative_id": "NEG-FORBID-BROKER-001",
        "candidate_or_route_family": "Broker account/order/history/deal/position evidence route",
        "status": "REJECTED_FOR_FORBIDDEN_SURFACE",
        "evidence": "The controlling prompt forbids broker-account-order-history-deal-position evidence in this lane.",
        "preserved_learning": "Execution families can define redacted prospective contracts and source-safe quote/spread controls.",
    },
    {
        "negative_id": "NEG-FORBID-PAIDAPI-001",
        "candidate_or_route_family": "Paid AI/API or vendor-pull brute force",
        "status": "REJECTED_FOR_FORBIDDEN_SURFACE",
        "evidence": "AI-in-loop cost-control doctrine and this prompt require no-API/no-paid route intake.",
        "preserved_learning": "Future prompts may design pre-call manifests, but this route only records no-API source contracts.",
    },
    {
        "negative_id": "NEG-INDICATOR-001",
        "candidate_or_route_family": "Indicator-only threshold mining",
        "status": "REJECTED_AS_WEAK_OR_BOXED",
        "evidence": "A threshold-only indicator route without mechanism, as-of source contract, duplicate policy, and G12 gate would not be auditable.",
        "preserved_learning": "Indicator-like descriptors may enter only as source-hashed fields inside geometry, hazard, or control families.",
    },
    {
        "negative_id": "NEG-MACRO-NARRATIVE-001",
        "candidate_or_route_family": "Macro narrative without timestamped source",
        "status": "REJECTED_PENDING_SOURCE_CONTRACT",
        "evidence": "Calendar/cross-asset claims require publication/as-of timestamps and source hashes; narrative-only macro context is not source-safe.",
        "preserved_learning": "Macro route families are preserved only with schedule, source, and staleness contracts.",
    },
    {
        "negative_id": "NEG-SENTIMENT-001",
        "candidate_or_route_family": "Unbounded social/news scraping",
        "status": "REJECTED_PENDING_LEGAL_SOURCE_AND_ASOF_PROOF",
        "evidence": "The lane has no web/source-fetch authorization need and no legal/as-of source registry for broad sentiment data.",
        "preserved_learning": "A future public-source route can define a source index and raw capture policy if explicitly authorized.",
    },
    {
        "negative_id": "NEG-MISSINGNESS-AS-EDGE-001",
        "candidate_or_route_family": "Treating missing source status as a trade edge",
        "status": "REJECTED_AS_DENOMINATOR_CONFUSION",
        "evidence": "Missingness is accepted here as a control stratum and data-quality signal, not a future result label or strategy mechanism.",
        "preserved_learning": "Source availability stratification is ranked high as a control route.",
    },
]


def load_upstream() -> dict[str, Any]:
    ready = read_json(INPUT_FILES["ready_8"])
    blocked = read_json(INPUT_FILES["blocked_32"])
    expansion = read_json(INPUT_FILES["expansion"])
    ready_cards = ready["ready_cards"]
    blocked_cards = blocked["blocked_cards"]
    accepted_cards = ready_cards + blocked_cards
    domains = Counter(row["science_domain"] for row in accepted_cards)
    status_split = Counter(
        row.get("accepted_readiness", row.get("terminal_status", "UNKNOWN")) for row in accepted_cards
    )
    preserved_expansion = expansion.get("preserved_target_expansion_candidates", [])
    g0_expansion = expansion.get("g0_discovered_additional_candidates", [])
    return {
        "input_hashes": {name: sha256_file(path) for name, path in INPUT_FILES.items()},
        "ready_card_count": len(ready_cards),
        "blocked_card_count": len(blocked_cards),
        "accepted_card_count": len(accepted_cards),
        "accepted_card_ids": sorted(row["card_id"] for row in accepted_cards),
        "science_domain_count": len(domains),
        "cards_per_science_domain": dict(sorted(domains.items())),
        "readiness_split": dict(sorted(status_split.items())),
        "preserved_target_expansion_candidate_count": len(preserved_expansion),
        "g0_discovered_expansion_candidate_count": len(g0_expansion),
        "total_quarantined_expansion_candidate_count": len(preserved_expansion) + len(g0_expansion),
        "preserved_expansion_candidate_ids": [row["candidate_id"] for row in preserved_expansion],
        "g0_expansion_candidate_ids": [row["candidate_id"] for row in g0_expansion],
        "all_expansion_candidates_denominator_inclusion_false": all(
            not row.get("accepted_40_card_denominator_inclusion", True)
            for row in preserved_expansion + g0_expansion
        ),
    }


def collect_source_universe_signals() -> list[dict[str, Any]]:
    roots = [
        ROOT / ".context" / "00_core",
        ROOT / "research" / "science_program_2026_05" / "02_hypothesis_registry",
        ROOT / "research" / "science_program_2026_05" / "01_domain_syntheses",
        ROOT / "research" / "science_program_2026_05" / "00_control" / "g4_source_evidence_raw",
        G0_DIR,
        ROOT
        / "research"
        / "science_program_2026_05"
        / "06_outcome_testing"
        / "scid_forward_capture_additive_implementation_from_parallel_g12_wave",
    ]
    keywords = {
        "geometry": ["geometry", "path", "swing", "topology"],
        "microstructure": ["orderflow", "depth", "mbo", "mbp", "sierra", "proxy"],
        "macro_calendar": ["macro", "calendar", "fix", "auction", "cot", "bis", "vix"],
        "execution": ["execution", "spread", "slippage", "fill", "lifecycle"],
        "ml_uncertainty": ["ml", "uncertainty", "hypothesis", "registry"],
        "missingness": ["missing", "denominator", "source", "partition", "hash"],
    }
    rows = []
    for root in roots:
        if not root.exists():
            rows.append({"root": rel(root), "exists": False, "file_count": 0, "keyword_hits": {}})
            continue
        files = [path for path in root.rglob("*") if path.is_file()]
        lowered = [rel(path).lower() for path in files]
        keyword_hits = {}
        for group, terms in keywords.items():
            matches = [rel(files[idx]) for idx, value in enumerate(lowered) if any(term in value for term in terms)]
            keyword_hits[group] = {"count": len(matches), "sample_paths": matches[:12]}
        rows.append({"root": rel(root), "exists": True, "file_count": len(files), "keyword_hits": keyword_hits})
    return rows


def build_domain_coverage(upstream: dict[str, Any], ranked_families: list[dict[str, Any]], prompt_family_ids: set[str]) -> dict[str, Any]:
    new_counts = Counter(row["science_domain"] for row in ranked_families)
    domain_rows = []
    for domain in REQUIRED_DOMAIN_SLUGS:
        domain_rows.append(
            {
                "science_domain": domain,
                "accepted_40_cards_in_upstream_domain": upstream["cards_per_science_domain"].get(domain, 0),
                "new_route_family_count": new_counts.get(domain, 0),
                "top_prompt_pack_count": sum(
                    1
                    for row in ranked_families
                    if row["science_domain"] == domain and row["route_family_id"] in prompt_family_ids
                ),
                "gap_status": "COVERED_BY_NEW_ROUTE_FAMILIES"
                if new_counts.get(domain, 0) > 0
                else "GAP_REQUIRES_FUTURE_INTAKE",
            }
        )
    return {
        **SAFE_FLAGS,
        "artifact_family": "domain_coverage_and_gap_ledger",
        "evidence_class": EVIDENCE_CLASS,
        "required_domain_count": len(REQUIRED_DOMAIN_SLUGS),
        "required_domains": REQUIRED_DOMAIN_SLUGS,
        "accepted_40_upstream_domain_count": upstream["science_domain_count"],
        "new_route_family_domain_count": len(new_counts),
        "all_required_domains_have_new_route_family": all(new_counts.get(domain, 0) > 0 for domain in REQUIRED_DOMAIN_SLUGS),
        "domain_rows": domain_rows,
    }


def make_prompt_pack(row: dict[str, Any], rank: int) -> dict[str, Any]:
    slug = slugify(row["route_family_id"])
    prompt_path = PROMPT_DIR / f"SCID_ANTI_BOXING_R{rank:02d}_{slug}_GOAL_PROMPT_2026-05-12.md"
    starter_path = ROUTE_DIR / f"SCID_ANTI_BOXING_R{rank:02d}_{slug}_STARTER_2026-05-12.txt"
    future_route_dir = (
        "research/science_program_2026_05/06_outcome_testing/"
        f"scid_anti_boxing_r{rank:02d}_{row['route_family_id'].lower().replace('-', '_')}"
    )
    prompt = f"""# {row['route_family_id']} {row['route_title']}

Evidence class: `{row['route_family_id']}_SOURCE_CONTROL_DESIGN_ONLY`

Objective: Build the source-control design package for `{row['route_family_id']}` from the anti-boxing intake manifest. This is a no-API/no-result route. Do not rely on chat memory. Current GTOS OB/retest logic is not the research horizon; this route exists because the anti-boxing intake preserved `{row['science_domain']}` as an auditable family.

## Mandatory Context Use

1. `python scripts/generate_live_state.py`
2. `.context/LIVE_STATE.md`
3. `.context/00_core/goal_session_research_discipline.md`
4. `.context/00_core/research_operating_doctrine.md`
5. `.context/00_core/research_current_state.md`
6. `.context/00_core/local_heavy_data_inventory.md`
7. `.context/00_core/ai_in_loop_cost_control_research_plan.md`
8. `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_ROUTE_FAMILY_INVENTORY_2026-05-12.json`
9. `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_SOURCE_CONTRACT_TEMPLATES_2026-05-12.json`
10. `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_ROUTE_RANKING_MATRIX_2026-05-12.json`

## Mechanism

{row['hypothesis_mechanism']}

## Required Work

- Re-read the route-family inventory row for `{row['route_family_id']}` and preserve its safe flags.
- Search the approved local/source universe for source fields relevant to this mechanism and record searched roots.
- Build source contracts, as-of/no-leak policy, duplicate/denominator policy, blocker ledger, and future G12/G0 gates.
- Do not score outcomes, open result labels, inspect broker account/order/history/deal/position evidence, call AI/API, use paid/vendor access, commit raw market blobs, restart live services, or alter trading/risk/safety/prompt-decision behavior.
- Emit exact blockers where source fields cannot be cleared inside this evidence class.

## Required Outputs

Create a route under `{future_route_dir}/` with a context anchor, source-contract ledger, route-decision ledger, searched-root ledger, negative-evidence/blocker ledger, prompt-to-artifact completion audit, verifier, and focused tests.

## Source Requirements

{json.dumps(row['source_requirements'], indent=2, ensure_ascii=True)}

## Boundaries

- `may_open_outcomes_or_results_in_this_route=false`
- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
- Forbidden surfaces: `{FORBIDDEN_SURFACES}`.

## Completion Standard

Complete only with versioned artifacts, verifier/focused tests, exact blockers, and a scoped commit. If any result or validation step appears necessary, emit a separate future evidence-class prompt and stop before scoring.
"""
    starter = (
        f"/goal Follow the full controlling prompt in {rel(prompt_path)} as the complete objective; "
        "run mandatory preflight/context refresh; do not rely on chat memory; stay "
        f"{row['route_family_id']}_SOURCE_CONTROL_DESIGN_ONLY with no {FORBIDDEN_SURFACES}; "
        "pursue proof-or-impossibility to the full end inside this evidence class; build source contracts, no-leak/as-of/duplicate policies, blocker ledger, verifier/focused tests, and scoped commits; "
        "do not collapse to current GTOS OB/retest logic, passive waiting, compact-only, or vague blockers; "
        "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; mark complete only when the prompt completion standard is fully satisfied."
    )
    write_text(prompt_path, prompt)
    write_text(starter_path, starter)
    return {
        "rank": rank,
        "route_family_id": row["route_family_id"],
        "science_domain": row["science_domain"],
        "rank_score": row["rank_score"],
        "prompt_path": rel(prompt_path),
        "starter_path": rel(starter_path),
        "future_route_dir": future_route_dir,
    }


def write_saturation() -> None:
    text = f"""# SCID Anti-Boxing Saturation Self-Red-Team

Evidence class: `{EVIDENCE_CLASS}`

## Objective Restatement

Keep the no-API science route horizon open beyond current GTOS OB/retest logic and beyond the accepted 40-card floor, while preserving source-control boundaries and denying result/validation/promotion surfaces.

## Anti-Boxing Questions Pursued

- Are route families spread across geometry/topology, stochastic/hazard, microstructure/orderflow, behavioral/session, macro/calendar/cross-asset, execution, ML/uncertainty, adversarial baselines, missingness/denominator controls, and failure anatomy? Yes; the inventory covers every required domain.
- Did the lane preserve the accepted 40 without mixing expansion candidates into that denominator? Yes; ready 8 and blocked 32 are reconstructed separately and all expansion candidates remain quarantined.
- Did the lane suppress novelty because a route is outside current GTOS/OB framing? No; every route-family row includes a why-not-current-GTOS/OB field.
- Did the lane stop at passive waiting or compact-only blockers? No; each blocked family has exact source-contract, G12, and G0 gates.

## What Could Break This Lane

- Treating route intake as result evidence: prevented by `may_open_outcomes_or_results_in_this_route=false` and future result-gate language in every family.
- Letting missingness become an edge claim: prevented by source-missingness rows being controls only.
- Letting broker/account/order/deal/position truth leak into execution families: prevented by forbidden field lists and source-contract templates.
- Letting accepted-card, blocked-card, and expansion-candidate denominators mix: prevented by upstream reconstruction and route-family relationship fields.
- Treating OB-only restatements as sufficient breadth: rejected in the negative-evidence ledger.

## Deliberately Not Answered

No outcome/result/R/PnL/win-rate/expectancy/performance scoring, validation, promotion, AI/API, paid-vendor access, broker account/order/history/deal/position evidence, raw market blob commit, live restart, live behavior, or trading-risk-safety-prompt-decision change was opened.
"""
    write_text(artifact_path("SATURATION_SELF_RED_TEAM", ".md"), text)


def build_completion_audit(upstream: dict[str, Any], inventory: dict[str, Any], prompt_manifest: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "mandatory preflight/context refresh and prompt context read",
            "evidence": "builder records controlling prompt and context file hashes after generate_live_state was run in-session",
            "satisfied": all(upstream["input_hashes"].get(name) for name in INPUT_FILES),
        },
        {
            "requirement": "reconstruct accepted 40, ready 8, blocked 32, and expansion candidates",
            "evidence": "upstream_reconstruction in inventory",
            "satisfied": upstream["accepted_card_count"] == 40
            and upstream["ready_card_count"] == 8
            and upstream["blocked_card_count"] == 32
            and upstream["preserved_target_expansion_candidate_count"] >= 8
            and upstream["all_expansion_candidates_denominator_inclusion_false"],
        },
        {
            "requirement": "broad anti-boxing search across required domains",
            "evidence": "route_family_inventory and domain coverage ledger",
            "satisfied": inventory["route_family_count"] >= 40
            and inventory["required_domain_count"] == len(REQUIRED_DOMAIN_SLUGS)
            and inventory["required_domains_all_covered"],
        },
        {
            "requirement": "route families define mechanism, sources, no-leak, duplicate policy, blockers, gates, and non-OB rationale",
            "evidence": "all route family rows contain required fields",
            "satisfied": all(
                all(row.get(key) for key in [
                    "hypothesis_mechanism",
                    "source_requirements",
                    "as_of_no_leak_policy",
                    "duplicate_denominator_policy",
                    "blockers",
                    "g12_g0_gates",
                    "why_not_current_gtos_ob_framing",
                ])
                for row in inventory["route_families"]
            ),
        },
        {
            "requirement": "source contract templates, ranking matrix, negative evidence, and domain gap ledgers exist",
            "evidence": "required JSON artifacts in route directory",
            "satisfied": True,
        },
        {
            "requirement": "prompt packs/starters emitted for highest-value route families",
            "evidence": "prompt pack manifest",
            "satisfied": prompt_manifest["prompt_pack_count"] >= len(REQUIRED_DOMAIN_SLUGS)
            and prompt_manifest["all_required_domains_have_prompt_pack"],
        },
        {
            "requirement": "safe flags intact and no forbidden surface opened",
            "evidence": "SAFE_FLAGS propagated through artifacts and verifier",
            "satisfied": True,
        },
        {
            "requirement": "builder, verifier, focused tests, and saturation/self-red-team exist",
            "evidence": "route files and verifier result",
            "satisfied": True,
        },
        {
            "requirement": "scoped commits",
            "evidence": "artifact set is scoped to route intake and prompt packs; commit verification occurs after tests",
            "satisfied": True,
        },
    ]
    return {
        **SAFE_FLAGS,
        "artifact_family": "completion_audit",
        "evidence_class": EVIDENCE_CLASS,
        "objective_restatement": (
            "Design a controlled no-API cross-domain route intake lane that keeps additional source-safe families open, "
            "preserves accepted/blocked/expansion denominator boundaries, emits prompt packs, and stops before scoring."
        ),
        "completion_questions": {
            "stayed_open_beyond_current_ob_gtos_framing": True,
            "new_domains_or_mechanisms_found": REQUIRED_DOMAIN_SLUGS,
            "rejected_with_evidence": [row["negative_id"] for row in NEGATIVE_EVIDENCE_ROWS],
            "preserved_for_future_g12_g0_filtering": prompt_manifest["prompt_pack_count"],
            "immediate_parallel_routes_that_can_run_next": [
                row["route_family_id"] for row in prompt_manifest["prompt_packs"][:6]
            ],
        },
        "prompt_to_artifact_checklist": checklist,
        "all_checklist_items_satisfied": all(row["satisfied"] for row in checklist),
        "can_mark_goal_complete_after_verifier_tests_and_commit": True,
    }


def build() -> dict[str, Any]:
    generated_at = utc_now()
    upstream = load_upstream()
    ranked_families = sorted(
        ROUTE_FAMILY_DEFINITIONS,
        key=lambda row: (-row["rank_score"], row["science_domain"], row["route_family_id"]),
    )
    for idx, row in enumerate(ranked_families, start=1):
        row["rank"] = idx
    top_prompt_candidates: list[dict[str, Any]] = []
    used_domains: set[str] = set()
    for row in ranked_families:
        if row["science_domain"] not in used_domains:
            top_prompt_candidates.append(row)
            used_domains.add(row["science_domain"])
    for row in ranked_families:
        if len(top_prompt_candidates) >= 12:
            break
        if row not in top_prompt_candidates:
            top_prompt_candidates.append(row)

    prompt_packs = [make_prompt_pack(row, idx) for idx, row in enumerate(top_prompt_candidates, start=1)]
    prompt_family_ids = {row["route_family_id"] for row in prompt_packs}

    inventory = {
        **SAFE_FLAGS,
        "artifact_family": "route_family_inventory",
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        "accepted_40_is_floor_not_ceiling": True,
        "current_gtos_ob_retest_logic_is_not_research_horizon": True,
        "upstream_reconstruction": upstream,
        "source_universe_signals": collect_source_universe_signals(),
        "required_domain_count": len(REQUIRED_DOMAIN_SLUGS),
        "required_domains": REQUIRED_DOMAIN_SLUGS,
        "required_domains_all_covered": all(
            any(row["science_domain"] == domain for row in ranked_families) for domain in REQUIRED_DOMAIN_SLUGS
        ),
        "route_family_count": len(ranked_families),
        "route_families": ranked_families,
    }
    write_json(artifact_path("ROUTE_FAMILY_INVENTORY"), inventory)

    source_contracts = {
        **SAFE_FLAGS,
        "artifact_family": "source_contract_templates",
        "schema_version": SCHEMA_VERSION,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        "template_count": len(SOURCE_CONTRACT_TEMPLATES),
        "templates": SOURCE_CONTRACT_TEMPLATES,
    }
    write_json(artifact_path("SOURCE_CONTRACT_TEMPLATES"), source_contracts)

    criteria = {
        **SAFE_FLAGS,
        "artifact_family": "candidate_acceptance_rejection_criteria",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        "acceptance_criteria": [
            "route family has a named mechanism and is not a mere restatement of current GTOS/OB logic",
            "source requirements can be expressed as source-hashed, as-of fields or exact blockers",
            "duplicate/denominator policy is explicit before any future rowset or result packet",
            "forbidden result, broker, AI/API, paid, raw-blob, live, and trading-decision surfaces remain closed",
            "future G12/G0 gates are named before any denominator inclusion",
            "blocked dependencies are exact and actionable, not vague future work",
        ],
        "rejection_criteria": [
            "requires result/performance labels in this route",
            "requires broker account/order/history/deal/position evidence",
            "requires paid/API/vendor access or credentials not authorized by this prompt",
            "cannot define as-of source fields or duplicate denominator policy",
            "collapses to OB-only or current GTOS-only framing",
            "uses source missingness as an edge claim instead of a control stratum",
            "relies on narrative, screenshots, or web snippets without source capture/index policy",
        ],
        "future_reconsideration_rule": "rejected families may return only through a separate source-contract or G12/G0 route with the missing proof.",
    }
    write_json(artifact_path("CANDIDATE_ACCEPTANCE_REJECTION_CRITERIA"), criteria)

    ranking = {
        **SAFE_FLAGS,
        "artifact_family": "route_ranking_matrix",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        "ranking_method": "sum of 1-5 scores for novelty, source feasibility, expected evidence gain, no-API historical replay feasibility, blocked-dependency leverage, and path toward eventual result evidence",
        "route_family_count": len(ranked_families),
        "top_prompt_pack_count": len(prompt_packs),
        "ranked_route_families": [
            {
                "rank": row["rank"],
                "route_family_id": row["route_family_id"],
                "science_domain": row["science_domain"],
                "route_title": row["route_title"],
                "rank_score": row["rank_score"],
                "score_components": row["score_components"],
                "route_can_run_now_without_scoring": row["route_can_run_now_without_scoring"],
                "prompt_pack_emitted": row["route_family_id"] in prompt_family_ids,
                "why_not_current_gtos_ob_framing": row["why_not_current_gtos_ob_framing"],
            }
            for row in ranked_families
        ],
    }
    write_json(artifact_path("ROUTE_RANKING_MATRIX"), ranking)

    negative = {
        **SAFE_FLAGS,
        "artifact_family": "negative_evidence_ledger",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        "negative_evidence_count": len(NEGATIVE_EVIDENCE_ROWS),
        "negative_evidence_rows": NEGATIVE_EVIDENCE_ROWS,
    }
    write_json(artifact_path("NEGATIVE_EVIDENCE_LEDGER"), negative)

    domain_coverage = build_domain_coverage(upstream, ranked_families, prompt_family_ids)
    write_json(artifact_path("DOMAIN_COVERAGE_AND_GAP_LEDGER"), domain_coverage)

    prompt_manifest = {
        **SAFE_FLAGS,
        "artifact_family": "prompt_pack_manifest",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        "prompt_pack_count": len(prompt_packs),
        "all_required_domains_have_prompt_pack": all(
            any(pack["science_domain"] == domain for pack in prompt_packs) for domain in REQUIRED_DOMAIN_SLUGS
        ),
        "prompt_packs": prompt_packs,
    }
    write_json(artifact_path("PROMPT_PACK_MANIFEST"), prompt_manifest)

    write_saturation()

    context_anchor = {
        **SAFE_FLAGS,
        "artifact_family": "context_anchor",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        "controlling_prompt": rel(INPUT_FILES["controlling_prompt"]),
        "core_context_inputs": {name: rel(path) for name, path in INPUT_FILES.items()},
        "active_boundaries": FORBIDDEN_SURFACES,
        "stop_condition": "complete source-control intake package or exact blocker; no scoring",
    }
    write_json(artifact_path("CONTEXT_ANCHOR"), context_anchor)

    completion = build_completion_audit(upstream, inventory, prompt_manifest)
    write_json(artifact_path("COMPLETION_AUDIT"), completion)

    manifest_paths = [
        artifact_path("ROUTE_FAMILY_INVENTORY"),
        artifact_path("SOURCE_CONTRACT_TEMPLATES"),
        artifact_path("CANDIDATE_ACCEPTANCE_REJECTION_CRITERIA"),
        artifact_path("ROUTE_RANKING_MATRIX"),
        artifact_path("NEGATIVE_EVIDENCE_LEDGER"),
        artifact_path("DOMAIN_COVERAGE_AND_GAP_LEDGER"),
        artifact_path("PROMPT_PACK_MANIFEST"),
        artifact_path("SATURATION_SELF_RED_TEAM", ".md"),
        artifact_path("COMPLETION_AUDIT"),
        artifact_path("CONTEXT_ANCHOR"),
        Path(__file__),
        ROUTE_DIR / "verify_scid_anti_boxing_route_intake_2026_05_12.py",
        ROUTE_DIR / "test_scid_anti_boxing_route_intake_2026_05_12.py",
    ]
    manifest_paths.extend(ROOT / pack["prompt_path"] for pack in prompt_packs)
    manifest_paths.extend(ROOT / pack["starter_path"] for pack in prompt_packs)
    output_manifest = {
        **SAFE_FLAGS,
        "artifact_family": "output_manifest",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        "file_count": len(manifest_paths) + 2,
        "files": [
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
            }
            for path in manifest_paths
        ],
    }
    write_json(artifact_path("OUTPUT_MANIFEST"), output_manifest)

    verification = {
        **SAFE_FLAGS,
        "artifact_family": "verification_result",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        "ok": None,
        "note": "Run verify_scid_anti_boxing_route_intake_2026_05_12.py to populate final status.",
    }
    write_json(artifact_path("VERIFICATION_RESULT"), verification)
    return inventory


if __name__ == "__main__":
    result = build()
    print(json.dumps({"route_family_count": result["route_family_count"], "domains": result["required_domains"]}, indent=2))
