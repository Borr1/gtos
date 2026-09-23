"""Audit whether research follow-up items have live/forward capture coverage.

This is a research/operations verifier. It does not call AI, Databento, MT5,
or Sierra. It only inspects local files and records whether each follow-up item
has one of:

- a live-flow append-only row source,
- a monitor-script row source,
- an explicit event-triggered collector, or
- a documented blocker/approval trigger.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


FOLLOWUP_MATRIX: tuple[dict[str, Any], ...] = (
    {
        "id": "LIVE-FOLLOW-001",
        "research_item": "AI-independent mechanical/MSO evaluation anchor",
        "source": "Owner 2026-05-04; FCI-ACTION-018 gap audit",
        "coverage_type": "LIVE_FLOW_APPEND_ONLY",
        "row_paths": ["shadow_logs/strategy_follow_evaluations.jsonl"],
        "expected_schemas": ["strategy_follow_evaluation_v1"],
        "implementation": "src/components/orchestrator.py -> record_live_mso_forward_shadow",
        "monitor": "scripts/_live_monitor_iter.py shadow freshness",
        "required_next_state": "row per MSO/live evaluation after orchestrator reload",
    },
    {
        "id": "LIVE-FOLLOW-002",
        "research_item": "AI CANDIDATE terminal strategy registry and external confluence",
        "source": "V2/V2b/V3/J46/S79 follow-data discussion",
        "coverage_type": "LIVE_FLOW_APPEND_ONLY",
        "row_paths": ["shadow_logs/strategy_follow_candidates.jsonl"],
        "expected_schemas": ["strategy_follow_candidate_v1"],
        "implementation": "src/components/orchestrator.py -> record_live_candidate_forward_shadow",
        "monitor": "scripts/_live_monitor_iter.py shadow freshness",
        "required_next_state": "row per AI CANDIDATE terminal path",
    },
    {
        "id": "LIVE-FOLLOW-003",
        "research_item": "Candidate path follow: close/touch/fill/pass-through/continue/return",
        "source": "Owner 2026-05-04 candidate monitoring requirement",
        "coverage_type": "MONITOR_SCRIPT_APPEND_ONLY",
        "row_paths": ["shadow_logs/candidate_path_follow.jsonl"],
        "expected_schemas": ["candidate_path_follow_v1"],
        "implementation": "scripts/follow_live_candidate_paths.py",
        "monitor": "run during live monitoring cadence",
        "required_next_state": "append path state for every strategy_follow_candidates row",
    },
    {
        "id": "LIVE-FOLLOW-003B",
        "research_item": "Opportunity-level duplicate protection for consecutive same setup detections",
        "source": "Owner 2026-05-04 same-candidate duplicate concern",
        "coverage_type": "MONITOR_SCRIPT_APPEND_ONLY",
        "row_paths": ["shadow_logs/live_candidate_opportunity_clusters.jsonl"],
        "expected_schemas": ["live_candidate_opportunity_cluster_v1"],
        "implementation": "src/research_infra/live_opportunity_dedupe.py via scripts/follow_live_candidate_paths.py gap closure",
        "monitor": "scripts/verify_shadow_log_integrity.py and opportunity rollup rows",
        "required_next_state": "raw rows preserved; count COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY only for trade-opportunity comparisons",
    },
    {
        "id": "LIVE-FOLLOW-004",
        "research_item": "Pending-limit lifecycle truth",
        "source": "FCI-ACTION-002; O8 pending LIMIT_PLACED gap",
        "coverage_type": "LIVE_FLOW_APPEND_ONLY",
        "row_paths": ["shadow_logs/pending_limit_lifecycle.jsonl"],
        "expected_schemas": ["pending_limit_lifecycle_v1"],
        "implementation": "src/components/pending_limit_lifecycle_logger.py + execution/orchestrator hooks",
        "monitor": "scripts/_live_monitor_iter.py shadow freshness; forward runbook",
        "required_next_state": "state coverage across pending/fill/cancel/expiry events",
    },
    {
        "id": "LIVE-FOLLOW-005",
        "research_item": "V2b OB-boundary/J46/fixed-R/FVG forward pairs",
        "source": "FCI-ACTION-004; C-9 blocker; V2b forward rows",
        "coverage_type": "LIVE_FLOW_APPEND_ONLY",
        "row_paths": ["shadow_logs/v2b_forward_pairs.jsonl"],
        "expected_schemas": ["v2b_forward_pair_v1"],
        "implementation": "src/research_infra/forward_capture.py",
        "monitor": "scripts/_live_monitor_iter.py shadow freshness; readiness verifier",
        "required_next_state": "resolved post-cutoff pairs plus broker/synthetic lane separation",
    },
    {
        "id": "LIVE-FOLLOW-006",
        "research_item": "V3/pre-fill delivery path and reversal-leg taxonomy",
        "source": "FCI-ACTION-005; P1-C-V3-FVG-ONLY-RESCUE blocker",
        "coverage_type": "LIVE_FLOW_APPEND_ONLY",
        "row_paths": ["shadow_logs/prefill_delivery_path.jsonl"],
        "expected_schemas": ["prefill_delivery_path_v1"],
        "implementation": "src/research_infra/forward_capture.py",
        "monitor": "scripts/_live_monitor_iter.py shadow freshness; forward runbook",
        "required_next_state": "arm/fill/cancel and path-order fields before V3 scoring",
    },
    {
        "id": "LIVE-FOLLOW-007",
        "research_item": "FVG/OB confluence and disagreement ledger",
        "source": "FCI-ACTION-006; FVG-only/OB-only/both-fire follow-up",
        "coverage_type": "LIVE_FLOW_APPEND_ONLY",
        "row_paths": ["shadow_logs/fvg_ob_confluence.jsonl"],
        "expected_schemas": ["fvg_ob_confluence_forward_v1"],
        "implementation": "src/research_infra/forward_capture.py",
        "monitor": "scripts/_live_monitor_iter.py shadow freshness; readiness verifier",
        "required_next_state": "forward-only confluence rows with no post-outcome leakage",
    },
    {
        "id": "LIVE-FOLLOW-008",
        "research_item": "CL/ZN/VIX/VXM context/control ledger",
        "source": "FCI-ACTION-015",
        "coverage_type": "LIVE_FLOW_APPEND_ONLY",
        "row_paths": [
            "shadow_logs/context_control_ledger.jsonl",
            "shadow_logs/shadow_observer_hardening_status.jsonl",
        ],
        "expected_schemas": [
            "context_control_forward_v1",
            "shadow_observer_hardening_status_v1",
        ],
        "implementation": "src/research_infra/forward_capture.py plus LTO-035 observer source registry/status",
        "monitor": "scripts/_live_monitor_iter.py shadow freshness; readiness verifier; LTO-035 observer hardening",
        "required_next_state": "context/control rows only; never direct strategy validation",
    },
    {
        "id": "LIVE-FOLLOW-009",
        "research_item": "Databento targeted live confluence/orderflow",
        "source": "FCI-ACTION-007/008; owner cost guard",
        "coverage_type": "EXPLICIT_EVENT_TRIGGERED_COLLECTOR",
        "row_paths": ["shadow_logs/databento_live_confluence.jsonl"],
        "expected_schemas": ["databento_live_confluence_v1"],
        "implementation": "scripts/databento_live_shadow_collector.py",
        "monitor": "scripts/_live_monitor_iter.py shadow freshness; Databento request ledger",
        "required_next_state": "run only on registered strategy/orderflow triggers, not every candle",
    },
    {
        "id": "LIVE-FOLLOW-010",
        "research_item": "Sierra local depth confluence",
        "source": "FCI-ACTION-009; Sierra depth parity work",
        "coverage_type": "EMBEDDED_LOCAL_CONFLUENCE",
        "row_paths": [
            "shadow_logs/strategy_follow_candidates.jsonl",
            "shadow_logs/candidate_path_follow.jsonl",
        ],
        "expected_schemas": [
            "strategy_follow_candidate_v1",
            "candidate_path_follow_v1",
        ],
        "implementation": "src/research_infra/forward_capture.py external_confluence.sierra; scripts/extract_sierra_depth_features.py",
        "monitor": "Sierra inventory + candidate/path follow rows",
        "required_next_state": "delayed/local Sierra snapshots attached where proxy mapping exists",
    },
    {
        "id": "LIVE-FOLLOW-011",
        "research_item": "NAS100/NQ orderflow adverse-selection diagnostic",
        "source": "OF-NAS100-DEPTH-ADVERSE-SELECTION-V1",
        "coverage_type": "EVENT_TRIGGERED_PLUS_EMBEDDED_CONFLUENCE",
        "row_paths": [
            "shadow_logs/databento_live_confluence.jsonl",
            "shadow_logs/strategy_follow_candidates.jsonl",
        ],
        "expected_schemas": [
            "databento_live_confluence_v1",
            "strategy_follow_candidate_v1",
        ],
        "implementation": "Databento live collector + Sierra confluence + request ledger",
        "monitor": "forward runbook and readiness verifier",
        "required_next_state": "track broker_actual_r>=20 and MBP10 candidate rows>=30",
    },
    {
        "id": "LIVE-FOLLOW-012",
        "research_item": "Broker actual-R, slippage, cost, and exit accounting",
        "source": "FCI-ACTION-003/017; O8 account truth gap",
        "coverage_type": "PARTIAL_EXIT_FLOW_PLUS_BLOCKER",
        "row_paths": [
            "shadow_logs/slippage.jsonl",
            "shadow_logs/j46_j49_shadow_outcomes.jsonl",
            "shadow_logs/time_in_trade.jsonl",
        ],
        "expected_schemas": [],
        "implementation": "src/components/execution.py and orchestrator exit hooks",
        "monitor": "scripts/build_broker_r_reconciliation_coverage.py; scripts/build_cost_slippage_exit_coverage.py",
        "required_next_state": "canonical MT5 deal-history export for full broker actual-R joins",
    },
    {
        "id": "LIVE-FOLLOW-013",
        "research_item": "J46-J49 exit policy comparator",
        "source": "J46-J49 30d shadow validation requirement",
        "coverage_type": "EXIT_FLOW_APPEND_ONLY",
        "row_paths": ["shadow_logs/j46_j49_shadow_outcomes.jsonl"],
        "expected_schemas": [],
        "implementation": "src/components/j46_j49_shadow_logger.py",
        "monitor": "scripts/week1_j46_j49_verification.py",
        "required_next_state": "accumulate fill rows; compare actual vs old-policy hypothetical",
    },
    {
        "id": "LIVE-FOLLOW-014",
        "research_item": "S79/side-aware compounding context",
        "source": "S79 and H-PM03/side-aware live tracking",
        "coverage_type": "CONFIG_PRESENT_WAITING_FOR_FORWARD_STRATEGY_ROWS",
        "row_paths": [
            "shadow_logs/strategy_follow_candidates.jsonl",
            "shadow_logs/daily_pnl_history.jsonl",
            "pipeline_state/side_aware_sprt_state.json",
        ],
        "expected_schemas": ["strategy_follow_candidate_v1"],
        "implementation": "strategy registry snapshot + existing PnL/SPRT monitoring",
        "monitor": "scripts/week1_j46_j49_verification.py",
        "required_next_state": "candidate/fill rows preserve S79/side-aware context without changing risk",
    },
    {
        "id": "LIVE-FOLLOW-015",
        "research_item": "Regime classifier and monthly decay/OB continuation",
        "source": "Regime classifier promotion gate; S1 monthly decay",
        "coverage_type": "LIVE_FLOW_AND_WATCHDOG_MONITOR",
        "row_paths": [
            "shadow_logs/regime_classifications.jsonl",
            "shadow_logs/ob_continuation_daily.csv",
        ],
        "expected_schemas": [],
        "implementation": "src/components/regime_shadow_logger.py; scripts/monthly_decay_monitor.py; scripts/ob_continuation_monitor.py",
        "monitor": "watchdog.ps1 and live monitor",
        "required_next_state": ">=14d regime shadow plus realized-outcome comparison; monthly decay report cadence",
    },
    {
        "id": "LIVE-FOLLOW-016",
        "research_item": "Decision-layer diagnostics: candidate features, D1 lag, direction, SL/touch/correlation gates",
        "source": "A.1/A.2/ADR-005/T5.24 shadow decisions",
        "coverage_type": "LIVE_FLOW_APPEND_ONLY",
        "row_paths": [
            "shadow_logs/candidate_features_log.jsonl",
            "shadow_logs/d1_bias_lag.jsonl",
            "shadow_logs/direction_emission_xau_audit.jsonl",
            "shadow_logs/sl_beyond_ob_decisions.jsonl",
            "shadow_logs/touch_count_gate_decisions.jsonl",
            "shadow_logs/cross_instrument_correlation_decisions.jsonl",
        ],
        "expected_schemas": [],
        "implementation": "component shadow loggers wired from orchestrator/permissions",
        "monitor": "scripts/_live_monitor_iter.py shadow freshness",
        "required_next_state": "continue freshness checks and per-candidate joins",
    },
    {
        "id": "LIVE-FOLLOW-017",
        "research_item": "Mechanical/dumb baseline, proximity, liquidity, displacement, structure divergence",
        "source": "A6, proximity, liquidity distance, displacement, v2 detector follow-up",
        "coverage_type": "LIVE_FLOW_AND_DAEMON_APPEND_ONLY",
        "row_paths": [
            "shadow_logs/dumb_baseline_hypotheticals.jsonl",
            "shadow_logs/proximity_shadow_log.jsonl",
            "shadow_logs/liquidity_distance_log.jsonl",
            "shadow_logs/displacement_events.jsonl",
            "shadow_logs/structure_detector_divergences.jsonl",
        ],
        "expected_schemas": [],
        "implementation": "orchestrator loggers plus displacement daemon",
        "monitor": "scripts/_live_monitor_iter.py shadow freshness; daemon heartbeat",
        "required_next_state": "keep per-candle freshness and join to candidate/fill outcomes",
    },
    {
        "id": "LIVE-FOLLOW-018",
        "research_item": "Exit-management shadows: BE, partial close Variant C, time in trade",
        "source": "WF2 R011/R013/R052; exit-management follow-up",
        "coverage_type": "EXIT_TRIGGER_APPEND_ONLY",
        "row_paths": [
            "shadow_logs/be_shadow_log.jsonl",
            "shadow_logs/partial_close_shadow_log.jsonl",
            "shadow_logs/time_in_trade.jsonl",
        ],
        "expected_schemas": [],
        "implementation": "orchestrator exit hooks",
        "monitor": "cost/slippage coverage report; future n>=30 trigger counts",
        "required_next_state": "rows appear only when fills reach trigger/close states",
    },
    {
        "id": "LIVE-FOLLOW-019",
        "research_item": "Session volatility and US30 sweep divergence",
        "source": "Podcast research deployments H25/H16",
        "coverage_type": "WATCHDOG_SCRIPT_OUTPUT",
        "row_paths": [
            "shadow_logs/session_volatility_log.csv",
            "shadow_logs/sweep_divergence_log.csv",
        ],
        "expected_schemas": [],
        "implementation": "scripts/session_volatility_monitor.py; scripts/sweep_divergence_monitor.py",
        "monitor": "watchdog/generate_live_state daemon inventory",
        "required_next_state": "verify watchdog cadence or run manually if stale",
    },
    {
        "id": "LIVE-FOLLOW-020",
        "research_item": "K55 shadow / ML specialist paired AI+ML labels",
        "source": "K55 S-1..S-5 work; owner approved read-only shadow path on 2026-05-05",
        "coverage_type": "READONLY_ML_SHADOW_FEATURE_BUNDLE_STATUS",
        "row_paths": ["shadow_logs/ml_shadow_predictions.jsonl"],
        "expected_schemas": ["ml_shadow_prediction_v1"],
        "implementation": "src/research_infra/k55_ml_shadow.py + scripts/backfill_k55_ml_shadow_predictions.py",
        "monitor": "daily checklist/verifier; prediction remains disabled unless a registered model artifact matches target and feature bundle",
        "required_next_state": "collect paired AI/K55 feature rows; train or register a matching model artifact only after enough clean labels exist",
    },
    {
        "id": "LIVE-FOLLOW-021",
        "research_item": "Component 3B debate / AI tool grounding / Reflexion behavior changes",
        "source": "N62/L-4/L-1/L-2/B-5 approval-gated work",
        "coverage_type": "EXPLICIT_OWNER_APPROVAL_BLOCKED",
        "row_paths": [],
        "expected_schemas": [],
        "implementation": "code/scaffolding exists in places; not wired by design",
        "monitor": "N/A until explicit owner reopen with budget cap",
        "required_next_state": "do not run or spend API unless owner reopens explicitly",
    },
    {
        "id": "LIVE-FOLLOW-022",
        "research_item": "GBPJPY Sierra/orderflow proxy gap",
        "source": "Live GBPJPY candidate question; Sierra/Databento mapping audit",
        "coverage_type": "BLOCKED_WITH_EVIDENCE_AND_TRIGGER",
        "row_paths": [],
        "expected_schemas": [],
        "implementation": "no direct CME GBPJPY futures proxy registered",
        "monitor": "strategy rows log NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
        "required_next_state": "separate 6B/6J cross proxy design before using Sierra/Databento confluence",
    },
    {
        "id": "LIVE-FOLLOW-023",
        "research_item": "Account/PnL truth and R-vs-dollar evidence separation",
        "source": "Follow-up plan 2026-05-03 section 1; owner MT5 screenshot correction",
        "coverage_type": "VERIFIER_REQUIRED_WITH_LOCAL_ROWS",
        "row_paths": [
            "shadow_logs/daily_pnl.json",
            "shadow_logs/daily_pnl_history.jsonl",
            "shadow_logs/equity_read_anomalies.jsonl",
        ],
        "expected_schemas": [],
        "implementation": "local PnL rows exist; account-history verifier/report still required",
        "monitor": "daily PnL/account-history reconciliation before CEO-facing dollar claims",
        "required_next_state": "build/read read-only MT5 account-history reconciliation: ACCOUNT_HISTORY_REALIZED vs LIVE_R_ARTIFACT vs RESEARCH_MEASURED",
    },
    {
        "id": "LIVE-FOLLOW-024",
        "research_item": "O1 trade-index staleness and O8 lifecycle completeness verifiers",
        "source": "Follow-up plan 2026-05-03 O1/O8; research_current_state operations telemetry",
        "coverage_type": "VERIFIER_REQUIRED_WITH_KNOWN_GAP",
        "row_paths": [
            "knowledge_base/trade_records/_trade_index.json",
            "shadow_logs/pending_limit_lifecycle.jsonl",
        ],
        "expected_schemas": ["", "pending_limit_lifecycle_v1"],
        "implementation": "O1/O8 verifier artifacts exist historically; fresh live rows still need join coverage",
        "monitor": "index-staleness verifier and lifecycle-completeness verifier after new LIMIT_PLACED rows",
        "required_next_state": "rebuild/migrate stale trade index and verify each LIMIT_PLACED has execution or pending_lifecycle state",
    },
    {
        "id": "LIVE-FOLLOW-025",
        "research_item": "V2 structural oracle/as-of selector remains shadow/discovery only",
        "source": "Follow-up plan held items; V2/V2b path-scaling current state",
        "coverage_type": "LIVE_SNAPSHOT_PLUS_DISCOVERY_ONLY_BLOCKER",
        "row_paths": [
            "shadow_logs/strategy_follow_evaluations.jsonl",
            "shadow_logs/v2b_forward_pairs.jsonl",
        ],
        "expected_schemas": [
            "strategy_follow_evaluation_v1",
            "v2b_forward_pair_v1",
        ],
        "implementation": "strategy snapshots preserve V2 variants; no selector changes live behavior",
        "monitor": "V2b forward-pair rows and candidate path rows",
        "required_next_state": "do not wire a structural selector until resolved unseen V2b rows, lifecycle, cost, and preregistered gates exist",
    },
    {
        "id": "LIVE-FOLLOW-026",
        "research_item": "XAUUSD same-market structural path extension and frozen-slice guard",
        "source": "Deep-dive priority 6; research_current_state evidence-class boundaries",
        "coverage_type": "SOURCE_STATUS_REQUIRED_WITH_FORWARD_SNAPSHOT",
        "row_paths": [
            "shadow_logs/strategy_follow_evaluations.jsonl",
            "shadow_logs/strategy_follow_candidates.jsonl",
            "shadow_logs/xauusd_same_market_extension_status.jsonl",
        ],
        "expected_schemas": [
            "strategy_follow_evaluation_v1",
            "strategy_follow_candidate_v1",
            "xauusd_same_market_extension_status_v1",
        ],
        "implementation": "current snapshots capture XAUUSD live context; LTO-028 status row preregisters the frozen same-market/source-transfer slice with outcomes closed",
        "monitor": "xauusd_same_market_extension_status plus claim ledger and source-period/evidence-class fields",
        "required_next_state": "register same-market source-transfer slice before opening outcomes; keep live rows separate from replay evidence",
    },
    {
        "id": "LIVE-FOLLOW-027",
        "research_item": "ES/MES strategy-cohort pre-registration",
        "source": "Deep-dive priority 7; research_current_state required move 4",
        "coverage_type": "PRE_REGISTRATION_REQUIRED",
        "row_paths": [
            "shadow_logs/es_mes_preregistration_status.jsonl",
        ],
        "expected_schemas": [
            "es_mes_preregistration_status_v1",
        ],
        "implementation": "LTO-029 status row preregisters ES/MES source mapping, session windows, evidence classes, and no-lookahead rules with outcomes closed",
        "monitor": "es_mes_preregistration_status plus ES/MES registry/report artifacts",
        "required_next_state": "keep outcomes closed until a separate event-id/source-hash/scoring dossier is frozen",
    },
    {
        "id": "LIVE-FOLLOW-028",
        "research_item": "6B sampling alignment and SI source/depth-definition blockers",
        "source": "Deep-dive priorities 4/5; Sierra batch/audit status",
        "coverage_type": "SOURCE_STATUS_BLOCKED_WITH_TRIGGER",
        "row_paths": [
            "shadow_logs/strategy_follow_candidates.jsonl",
            "shadow_logs/candidate_path_follow.jsonl",
        ],
        "expected_schemas": [
            "strategy_follow_candidate_v1",
            "candidate_path_follow_v1",
        ],
        "implementation": "Sierra/Databento confluence reports availability, but 6B/SI interpretation is source-status gated",
        "monitor": "Sierra readiness inventory and source-status section in research_current_state",
        "required_next_state": "use common-second policy for 6B and keep SI blocked until source/depth definition resolves",
    },
    {
        "id": "LIVE-FOLLOW-029",
        "research_item": "External feed blockers: pre-2024 tick, pre-2022 OHLCV, FX COT, KMW fix, H-K-M, BIS, Fed research feed",
        "source": "Follow-up plan data/source blocks D-2/D-4/D-5/D-7/D-8/D-9/D-12",
        "coverage_type": "DOCUMENTED_SOURCE_BLOCKERS",
        "row_paths": [],
        "expected_schemas": [],
        "implementation": "not live-captured because legal/source/cadence/cache contracts are not registered",
        "monitor": "research_current_state Required Next Research Moves 24-28",
        "required_next_state": "reopen only after source/access path, cache schema, publication-time/no-lookahead convention, and budget approval exist",
    },
    {
        "id": "LIVE-FOLLOW-030",
        "research_item": "Options/gamma and volatility-risk-premium blockers plus FlashAlpha Basic GEX forward context",
        "source": "research_current_state options/gamma proxy; follow-up A-2/A-3/D-3",
        "coverage_type": "PARTIAL_FORWARD_CONTEXT_PLUS_SOURCE_BLOCKERS",
        "row_paths": [],
        "expected_schemas": [],
        "implementation": "FlashAlpha Basic forward context is wired outside these strategy rows; historical/aggregate gamma and VRP validation remain source-blocked",
        "monitor": "FlashAlpha forward context reports and source-blocker ledger",
        "required_next_state": "accumulate legal forward rows or register legal historical GEX/VRP/VIX1D/VIX9D sources before validation",
    },
    {
        "id": "LIVE-FOLLOW-031",
        "research_item": "X-1/X-2/X-3 imbalance/meta-order-flow primitives",
        "source": "Follow-up plan external source blockers; orderflow category-specific open work",
        "coverage_type": "DOCUMENTED_SOURCE_BLOCKERS",
        "row_paths": [
            "shadow_logs/databento_live_confluence.jsonl",
            "shadow_logs/strategy_follow_candidates.jsonl",
        ],
        "expected_schemas": [
            "databento_live_confluence_v1",
            "strategy_follow_candidate_v1",
        ],
        "implementation": "only targeted Databento/Sierra confluence is available; no broad primitive promoted",
        "monitor": "Databento request ledger, Sierra depth confluence, and NAS100 feature contract",
        "required_next_state": "define primitive-specific extractor, label plan, cost cap, and candidate trigger before broader collection",
    },
    {
        "id": "LIVE-FOLLOW-032",
        "research_item": "Live monitoring goal/runbook persistence for all shadow rows",
        "source": "Owner 2026-05-04 keep-in-context requirement",
        "coverage_type": "RUNBOOK_AND_MONITORING_CADENCE",
        "row_paths": [
            ".context/05_operations/FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md",
            "scripts/_live_monitor_iter.py",
        ],
        "expected_schemas": [],
        "implementation": "runbook plus live monitor freshness list",
        "monitor": "active monitoring goal prompt and periodic live monitor iterations",
        "required_next_state": "after orchestrator restart, monitor row freshness and path outcomes during each active session",
    },
    {
        "id": "LIVE-FOLLOW-033",
        "research_item": "Separate no-AI MSO shadow observer for tested non-orchestrator instruments",
        "source": "Owner 2026-05-04 instrument-expansion live-follow question",
        "coverage_type": "SEPARATE_NO_AI_OBSERVER_APPEND_ONLY",
        "row_paths": [
            "shadow_logs/shadow_observer_status.jsonl",
            "shadow_logs/strategy_follow_evaluations.jsonl",
            "shadow_logs/shadow_observer_hardening_status.jsonl",
        ],
        "expected_schemas": [
            "shadow_observer_status_v1",
            "strategy_follow_evaluation_v1",
            "shadow_observer_hardening_status_v1",
        ],
        "implementation": "config/shadow_observer_registry.yaml + src/research_infra/shadow_observer.py + scripts/run_shadow_observer.py + LTO-035 hardening audit",
        "monitor": "scripts/_live_monitor_iter.py shadow freshness; SHADOW_OBSERVER_RUNBOOK_2026-05-04.md; scripts/audit_shadow_observer_hardening.py",
        "required_next_state": "run active EURUSD/GER40/UK100 MSO-only observers; keep ES/MES prereg-blocked and CL/ZN/VIX control-only; audit stale detection and final closeout",
    },
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _latest_jsonl(path: Path) -> tuple[int, dict[str, Any] | None, str | None]:
    if not path.exists() or path.is_dir():
        return 0, None, "missing"
    lines = [line for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
    if not lines:
        return 0, None, "empty"
    try:
        return len(lines), json.loads(lines[-1]), None
    except json.JSONDecodeError as exc:
        return len(lines), None, f"invalid_json:{exc}"


def _file_info(root: Path, rel_path: str) -> dict[str, Any]:
    path = root / rel_path
    suffix = path.suffix.lower()
    info: dict[str, Any] = {
        "path": rel_path,
        "exists": path.exists(),
        "line_count": 0,
        "latest_schema": None,
        "promotion_verdict": None,
        "mtime_utc": None,
        "error": None,
    }
    if path.exists():
        info["mtime_utc"] = datetime.fromtimestamp(
            path.stat().st_mtime, timezone.utc
        ).isoformat()
    if suffix == ".jsonl":
        count, latest, error = _latest_jsonl(path)
        info["line_count"] = count
        info["error"] = error
        if latest:
            info["latest_schema"] = latest.get("schema_version")
            info["promotion_verdict"] = latest.get("promotion_verdict")
    elif path.exists() and not path.is_dir():
        try:
            info["line_count"] = sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore"))
        except Exception as exc:  # noqa: BLE001
            info["error"] = str(exc)
    return info


def _coverage_status(item: dict[str, Any], files: list[dict[str, Any]]) -> str:
    coverage_type = str(item.get("coverage_type") or "")
    if "EXPLICIT_OWNER_APPROVAL_BLOCKED" in coverage_type:
        return coverage_type
    if "APPROVAL_OR_TARGET_REFRESH_BLOCKED" in coverage_type:
        return coverage_type
    if "TARGET_REFRESH_APPROVED_PENDING_IMPLEMENTATION" in coverage_type:
        return coverage_type
    if any(
        marker in coverage_type
        for marker in (
            "BLOCKED",
            "BLOCKER",
            "PARTIAL",
            "PRE_REGISTRATION_REQUIRED",
            "VERIFIER_REQUIRED",
            "SOURCE_STATUS_REQUIRED",
            "DOCUMENTED_SOURCE_BLOCKERS",
            "WAITING_FOR_FORWARD",
        )
    ):
        return coverage_type
    if not item.get("row_paths"):
        return "NO_ROW_SOURCE_BY_DESIGN"
    if "SEPARATE_NO_AI_OBSERVER" in coverage_type:
        if any(f["line_count"] for f in files):
            return "ROWS_PRESENT"
        return "SEPARATE_OBSERVER_READY_WAITING_FOR_KZ_ROW"
    if any(f["line_count"] for f in files):
        return "ROWS_PRESENT"
    if "EXPLICIT_EVENT_TRIGGERED" in coverage_type:
        return "COLLECTOR_READY_WAITING_FOR_EXPLICIT_TRIGGER"
    if "EXIT_TRIGGER" in coverage_type:
        return "LIVE_HOOK_READY_WAITING_FOR_EXIT_TRIGGER_ROWS"
    if "WATCHDOG_SCRIPT" in coverage_type:
        return "SCRIPT_OUTPUT_WAITING_OR_STALE_CHECK_REQUIRED"
    if "MONITOR_SCRIPT" in coverage_type:
        return "MONITOR_SCRIPT_READY_WAITING_FOR_CANDIDATE_ROWS"
    return "LIVE_HOOK_READY_WAITING_FOR_NEXT_RESTART_OR_EVENT"


def build_report(root: Path) -> dict[str, Any]:
    rows = []
    counts: dict[str, int] = {}
    for item in FOLLOWUP_MATRIX:
        files = [_file_info(root, rel) for rel in item.get("row_paths", [])]
        status = _coverage_status(item, files)
        counts[status] = counts.get(status, 0) + 1
        schemas = item.get("expected_schemas") or []
        schema_attention = []
        for idx, expected in enumerate(schemas):
            if not expected:
                continue
            if idx >= len(files):
                schema_attention.append(f"{expected}:missing_file_slot")
                continue
            latest = files[idx].get("latest_schema")
            if latest and latest != expected:
                schema_attention.append(f"{files[idx]['path']} latest={latest} expected={expected}")
        rows.append(
            {
                **item,
                "files": files,
                "coverage_status": status,
                "schema_attention": schema_attention,
            }
        )
    return {
        "schema_version": "live_shadow_followup_coverage_audit_v1",
        "created_at_utc": utc_now_iso(),
        "promotion_verdict": PROMOTION_VERDICT,
        "root": str(root),
        "status_counts": counts,
        "rows": rows,
    }


def render_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Live Shadow Follow-Up Coverage Audit - 2026-05-04",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(payload["status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "## Coverage Matrix",
            "",
            "| ID | Research item | Coverage status | Row sources | Required next state |",
            "|---|---|---|---|---|",
        ]
    )
    for row in payload["rows"]:
        paths = "<br>".join(f"`{f['path']}` ({f['line_count']} rows)" for f in row["files"]) or "n/a"
        lines.append(
            "| {id} | {item} | `{status}` | {paths} | {next_state} |".format(
                id=row["id"],
                item=row["research_item"].replace("|", "/"),
                status=row["coverage_status"],
                paths=paths,
                next_state=row["required_next_state"].replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## Hard Boundaries",
            "",
            "- This audit does not promote any strategy, risk setting, prompt, or execution behavior.",
            "- Databento Live is event-triggered and explicitly enabled only; no blind every-candle subscription is allowed.",
            "- Sierra depth is local/delayed confluence and is embedded only where a registered proxy mapping exists.",
            "- GBPJPY has no registered direct Sierra/Databento proxy in this audit; strategy rows must show that blocker instead of guessing.",
            "- K55/ML shadow target refresh and read-only feature/status rows are implemented; prediction remains disabled until a matching registered model artifact exists. Component 3B/debate/tool-grounding remains approval-blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args(argv)

    payload = build_report(Path(args.root))
    if args.output_json:
        target = Path(args.output_json)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if args.output_md:
        target = Path(args.output_md)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_md(payload), encoding="utf-8")
    if not args.output_json and not args.output_md:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
