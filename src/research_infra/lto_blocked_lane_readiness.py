"""Blocked-lane readiness artifacts for LTO-024, LTO-031, and LTO-032.

This module produces research/control evidence only. It does not call AI,
Databento, MT5, Sierra, canaries, orders, or execution code.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
STATUS_SCHEMA_VERSION = "lto_blocked_lane_status_v1"
LTO024_SCHEMA_VERSION = "lto024_component3b_approval_dossier_v1"
LTO031_SCHEMA_VERSION = "lto031_external_feed_source_readiness_v1"
LTO032_SCHEMA_VERSION = "lto032_options_gamma_source_readiness_v1"

NO_ACTION_COUNTERS = {
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "paid_data_calls": 0,
    "paid_fetch_attempted": False,
}

DEFAULT_SOURCE_ARTIFACTS = {
    "lto024": [
        "research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md",
        "research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md",
        "research/program_control/LIMITATIONS_TO_OPPORTUNITIES_QUEUE_STATE_2026-05-05.md",
    ],
    "lto031": [
        "research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md",
        "research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md",
        "research/program_control/MASTER_RESEARCH_QUEUE_STATE_2026-05-03.md",
    ],
    "lto032": [
        "research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md",
        "research/program_control/MASTER_RESEARCH_QUEUE_STATE_2026-05-03.md",
        "src/components/external_feeds.py",
    ],
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(*parts: Any) -> str:
    payload = "|".join(json.dumps(part, sort_keys=True, default=str) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def read_text(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def artifact_presence(root: Path, rel_paths: list[str]) -> list[dict[str, Any]]:
    rows = []
    for rel_path in rel_paths:
        path = root / rel_path
        rows.append(
            {
                "path": rel_path,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
            }
        )
    return rows


def _has_import(text: str, module_pattern: str) -> bool:
    pattern = rf"^\s*(?:from\s+{module_pattern}\s+import|import\s+{module_pattern}\b)"
    return bool(re.search(pattern, text, flags=re.MULTILINE))


def scan_lto024_activation(root: Path) -> dict[str, Any]:
    orchestrator = read_text(root / "src/components/orchestrator.py")
    primary = read_text(root / "src/components/primary_analyzer.py")
    run_agent = read_text(root / "run_agent.py")

    findings = {
        "orchestrator_imports_debate": _has_import(
            orchestrator,
            r"(?:src\.components\.debate|components\.debate|debate)",
        ),
        "run_agent_imports_debate": _has_import(
            run_agent,
            r"(?:src\.components\.debate|components\.debate|debate)",
        ),
        "primary_analyzer_imports_ai_tools": _has_import(
            primary,
            r"(?:src\.components\.ai_tools|components\.ai_tools|ai_tools)",
        ),
        "orchestrator_imports_ai_tools": _has_import(
            orchestrator,
            r"(?:src\.components\.ai_tools|components\.ai_tools|ai_tools)",
        ),
        "orchestrator_imports_adaptive_review": _has_import(
            orchestrator,
            r"(?:src\.components\.adaptive_review|components\.adaptive_review|adaptive_review)",
        ),
    }
    activation_detected = any(findings.values())
    return {
        "activation_detected": activation_detected,
        "findings": findings,
        "source_files": {
            "orchestrator_exists": bool(orchestrator),
            "primary_analyzer_exists": bool(primary),
            "run_agent_exists": bool(run_agent),
            "debate_code_exists": (root / "src/components/debate.py").exists(),
            "ai_tools_exists": (root / "src/components/ai_tools").exists(),
            "adaptive_review_exists": (root / "src/components/adaptive_review.py").exists(),
            "debate_tests_exist": (root / "tests/test_debate.py").exists(),
        },
    }


def lto024_payload(root: Path, generated_at_utc: str | None = None) -> dict[str, Any]:
    generated_at = generated_at_utc or utc_now_iso()
    activation = scan_lto024_activation(root)
    action_required = []
    if activation["activation_detected"]:
        action_required.append("LIVE_AI_OR_DEBATE_ACTIVATION_DETECTED")
    status = "APPROVAL_BLOCKED_DOSSIER_READY" if not action_required else "ACTION_REQUIRED"
    payload = {
        "schema_version": LTO024_SCHEMA_VERSION,
        "created_at_utc": generated_at,
        "lto_id": "LTO-024",
        "follow_ids": ["LIVE-FOLLOW-021"],
        "status": status,
        "promotion_verdict": PROMOTION_VERDICT,
        "scope": "approval dossier and static no-activation check only",
        "summary": (
            "Component 3B, tool grounding, and Reflexion remain parked. "
            "The current artifact is a dossier template plus static check, not implementation."
        ),
        "current_cost_usd": 0.0,
        "future_cost_status": "OWNER_BUDGET_AND_TOKEN_PROFILE_REQUIRED_BEFORE_ANY_AI_CALL",
        "shadow_only_mode_required_if_reopened": {
            "decision_impact": "ZERO_LIVE_DECISION_IMPACT",
            "execution_impact": "ZERO_ORDER_OR_RISK_IMPACT",
            "allowed_rows": "append-only shadow comparison/status rows only",
            "required_gate": "separate owner approval with model, symbol scope, trigger policy, budget cap, cooldown, and stop conditions",
        },
        "prompts_or_modules_affected_if_reopened": [
            "src/prompts/bull_agent_prompt.py",
            "src/prompts/bear_agent_prompt.py",
            "src/prompts/judge_prompt.py",
            "src/components/debate.py",
            "src/components/ai_tools/",
            "src/components/adaptive_review.py",
            "src/components/primary_analyzer.py only if tool grounding changes primary-analysis behavior",
            "src/components/orchestrator.py only if a shadow-only caller is explicitly approved",
        ],
        "evaluation_metrics_if_reopened": [
            "paired 3A vs 3B/tool/reflexion disagreement rate",
            "broker actual-R after account-history join",
            "synthetic path-R clearly separated from broker actual-R",
            "candidate rate and false-veto rate",
            "latency per candidate",
            "AI refusal/malformed rate",
            "token and dollar cost per candidate",
            "source-grounding coverage and missing-source rate",
            "no-action safety counters",
        ],
        "stop_conditions_if_reopened": [
            "monthly or daily cost cap exceeded",
            "any row reports nonzero order/risk/execution action",
            "malformed/refusal rate exceeds preregistered threshold",
            "latency exceeds preregistered live-shadow budget",
            "feature/source leakage detected",
            "unapproved prompt, risk, safety-gate, or execution edit detected",
        ],
        "owner_decisions_required": [
            "DELETE/WIRE/LEAVE decision for Component 3B",
            "tool-grounding scope and allowed tools",
            "Reflexion memory scope and retention policy",
            "model, symbols, kill zones, budget cap, cooldown, and duration",
        ],
        "static_activation_check": activation,
        "source_artifacts": artifact_presence(root, DEFAULT_SOURCE_ARTIFACTS["lto024"]),
        "action_required_codes": action_required,
        **NO_ACTION_COUNTERS,
    }
    return payload


def lto031_sources() -> list[dict[str, Any]]:
    return [
        {
            "source_key": "pre_2024_tick_lob",
            "status": "BLOCKED",
            "url_or_vendor": "ALTERNATE_BROKER_PROVIDER_ARCHIVE_OR_PAID_HISTORICAL_TICK_LOB_SOURCE_REQUIRED",
            "legal_access_path": "NOT_REGISTERED",
            "cache_schema": "tick_lob_history_v1_required_before_ingest",
            "publication_time_no_lookahead_convention": "event timestamps must be exchange/source timestamps; ingestion time must be separately stored",
            "cost_status": "UNKNOWN_UNTIL_PROVIDER_SELECTED",
            "expected_use": "older tick/depth coverage for source-period expansion and decay checks",
            "local_evidence": "MT5 tick probes and local tick capture do not provide pre-2024 tick history",
        },
        {
            "source_key": "pre_2022_ohlcv",
            "status": "BLOCKED",
            "url_or_vendor": "ALTERNATE_BROKER_PROVIDER_OR_ARCHIVE_REQUIRED",
            "legal_access_path": "NOT_REGISTERED",
            "cache_schema": "ohlcv_history_v1_required_before_replay",
            "publication_time_no_lookahead_convention": "bar close time only; source-period flag required",
            "cost_status": "UNKNOWN_UNTIL_PROVIDER_SELECTED",
            "expected_use": "older all-symbol OHLCV expansion with source-period bias flags",
            "local_evidence": "current redacted_account MT5 history does not provide full all-symbol pre-2022 M15 coverage",
        },
        {
            "source_key": "fx_cot",
            "status": "BLOCKED_SOURCE_MAPPING_REQUIRED",
            "url_or_vendor": "CFTC_OFFICIAL_COT_WITH_FX_CONTRACT_MAPPING_REQUIRED",
            "legal_access_path": "OFFICIAL_PUBLIC_SOURCE_EXPECTED_BUT_FX_MAPPING_NOT_REGISTERED",
            "cache_schema": "cftc_fx_cot_v1_required",
            "publication_time_no_lookahead_convention": "use CFTC publication timestamp, not report-period end, for as-of joins",
            "cost_status": "EXPECTED_FREE_PUBLIC_SOURCE_VERIFY_BEFORE_FETCH",
            "expected_use": "FX positioning context for USDJPY/GBPJPY/GBPUSD regimes",
            "local_evidence": "CFTC fetcher and XAUUSD gold cache exist, but no local FX COT contract mappings/rows exist",
        },
        {
            "source_key": "kmw_fx_fix",
            "status": "BLOCKED",
            "url_or_vendor": "KROHN_MUELLER_WHELAN_FX_FIX_SOURCE_OR_LEGAL_PROXY_REQUIRED",
            "legal_access_path": "NOT_REGISTERED",
            "cache_schema": "fx_fix_calendar_and_window_v1_required",
            "publication_time_no_lookahead_convention": "calendar/fix windows must be known before session; no outcome-derived fix tags",
            "cost_status": "UNKNOWN_UNTIL_SOURCE_SELECTED",
            "expected_use": "FX fix-window W-shape context for USDJPY/GBPJPY/GBPUSD",
            "local_evidence": "LBMA metals calendar exists, but no local KMW FX-fix source/cache exists",
        },
        {
            "source_key": "hkm_intermediary_capital",
            "status": "BLOCKED",
            "url_or_vendor": "HE_KELLY_MANELA_INTERMEDIARY_CAPITAL_SOURCE_REQUIRED",
            "legal_access_path": "NOT_REGISTERED",
            "cache_schema": "hkm_intermediary_capital_v1_required",
            "publication_time_no_lookahead_convention": "monthly/quarterly release timestamp required before as-of join",
            "cost_status": "UNKNOWN_UNTIL_SOURCE_SELECTED",
            "expected_use": "cross-asset intermediary-capital regime feature",
            "local_evidence": "no local H-K-M/intermediary-capital source, status file, normalized cache, or registered spec exists",
        },
        {
            "source_key": "bis_macro",
            "status": "BLOCKED",
            "url_or_vendor": "BIS_PUBLIC_TABLES_OR_SELECTED_BIS_SOURCE_REQUIRED",
            "legal_access_path": "NOT_REGISTERED",
            "cache_schema": "bis_macro_tables_v1_required",
            "publication_time_no_lookahead_convention": "BIS release/publication timestamp required; revisions must be versioned",
            "cost_status": "EXPECTED_PUBLIC_SOURCE_VERIFY_BEFORE_FETCH",
            "expected_use": "JPY carry, macro, and cross-asset risk context",
            "local_evidence": "FRED macro cache exists, but no BIS source/cache/spec exists locally",
        },
        {
            "source_key": "fed_research_feed",
            "status": "BLOCKED_SOURCE_UNSPECIFIED",
            "url_or_vendor": "SPECIFIC_FED_RESEARCH_FEED_REQUIRED",
            "legal_access_path": "NOT_REGISTERED",
            "cache_schema": "fed_research_feed_v1_required",
            "publication_time_no_lookahead_convention": "publication timestamp and source document version required",
            "cost_status": "EXPECTED_PUBLIC_SOURCE_VERIFY_BEFORE_FETCH",
            "expected_use": "research/event context only after source is specified",
            "local_evidence": "no distinct Fed research-feed contract/parser/cache exists beyond FRED macro feed",
        },
    ]


def lto031_payload(root: Path, generated_at_utc: str | None = None) -> dict[str, Any]:
    sources = lto031_sources()
    return {
        "schema_version": LTO031_SCHEMA_VERSION,
        "created_at_utc": generated_at_utc or utc_now_iso(),
        "lto_id": "LTO-031",
        "follow_ids": ["LIVE-FOLLOW-029"],
        "status": "SOURCE_BLOCKED_READINESS_REGISTERED",
        "promotion_verdict": PROMOTION_VERDICT,
        "summary": "External feed blockers are now explicit source-readiness rows; none are validated from unavailable sources.",
        "source_count": len(sources),
        "status_counts": _status_counts(sources),
        "sources": sources,
        "source_artifacts": artifact_presence(root, DEFAULT_SOURCE_ARTIFACTS["lto031"]),
        "validation_boundary": "No unavailable source is used for validation, replay, ML labels, or live decisions.",
        **NO_ACTION_COUNTERS,
    }


def lto032_sources() -> list[dict[str, Any]]:
    return [
        {
            "source_key": "flashalpha_basic_gex_forward_proxy",
            "status": "READY_FORWARD_CONTEXT_ONLY",
            "url_or_vendor": "FlashAlpha Basic GEX proxy path already integrated locally",
            "legal_access_path": "LOCAL_FORWARD_PROXY_INTEGRATION_PRESENT",
            "delay_or_publication_timestamp": "snapshot ingestion timestamp; not historical official aggregate GEX",
            "instrument_mapping": "QQQ->NAS100, DIA->US30, SPY->SPX context, GLD->XAUUSD, SLV->XAGUSD",
            "cache_schema": "flashalpha_gex normalized snapshots already present",
            "no_lookahead_convention": "forward snapshots only; never backfill historical alpha from later snapshots",
            "expected_use": "context-only forward gamma proxy until enough point-in-time rows accumulate",
            "local_evidence": "15 normalized rows across QQQ/DIA/SPY/GLD/SLV in Lane 4 triage",
        },
        {
            "source_key": "official_or_historical_aggregate_gex",
            "status": "BLOCKED",
            "url_or_vendor": "OFFICIAL_CBOE_OR_LEGAL_HISTORICAL_GEX_PROVIDER_REQUIRED",
            "legal_access_path": "NOT_REGISTERED",
            "delay_or_publication_timestamp": "required before use",
            "instrument_mapping": "NAS100/US30/SPX/XAUUSD/XAGUSD mapping must be registered before validation",
            "cache_schema": "historical_gex_v1_required",
            "no_lookahead_convention": "use provider publication timestamp; no reconstructed history without timestamps",
            "expected_use": "historical gamma-sign validation and regime features",
            "local_evidence": "FlashAlpha Basic is single-expiry forward proxy only, not official aggregate/historical GEX",
        },
        {
            "source_key": "vix1d_vix9d_spread",
            "status": "BLOCKED",
            "url_or_vendor": "LEGAL_VIX1D_AND_VIX9D_SOURCE_REQUIRED",
            "legal_access_path": "NOT_REGISTERED",
            "delay_or_publication_timestamp": "required before use",
            "instrument_mapping": "index volatility context for NAS100/US30/SPX only unless separately mapped",
            "cache_schema": "vix1d_vix9d_term_structure_v1_required",
            "no_lookahead_convention": "publication/as-of timestamp required for each value",
            "expected_use": "dealer-gamma/short-vol context proxy",
            "local_evidence": "local feed inventory has VIXCLS/GVZCLS but no VIX1D or VIX9D",
        },
        {
            "source_key": "vrp_delta",
            "status": "BLOCKED_CONSTRUCTION_REQUIRED",
            "url_or_vendor": "IMPLIED_VARIANCE_SOURCE_PLUS_REALIZED_VOL_ESTIMATOR_REQUIRED",
            "legal_access_path": "NOT_REGISTERED",
            "delay_or_publication_timestamp": "required for implied-vol source and realized-vol estimator inputs",
            "instrument_mapping": "per-instrument VRP mapping must be preregistered before collection",
            "cache_schema": "vrp_construction_v1_required",
            "no_lookahead_convention": "realized-vol lookback must end before decision time; implied source uses as-of timestamp",
            "expected_use": "volatility-risk-premium regime/context feature",
            "local_evidence": "no local VRP, VIX futures, implied-variance term-structure, or registered realized-vol estimator source exists",
        },
    ]


def lto032_payload(root: Path, generated_at_utc: str | None = None) -> dict[str, Any]:
    sources = lto032_sources()
    return {
        "schema_version": LTO032_SCHEMA_VERSION,
        "created_at_utc": generated_at_utc or utc_now_iso(),
        "lto_id": "LTO-032",
        "follow_ids": ["LIVE-FOLLOW-030"],
        "status": "PARTIAL_FORWARD_CONTEXT_WITH_SOURCE_BLOCKERS_REGISTERED",
        "promotion_verdict": PROMOTION_VERDICT,
        "summary": "FlashAlpha Basic is usable as forward context only; historical/aggregate gamma, VIX1D/VIX9D, and VRP remain source-blocked.",
        "source_count": len(sources),
        "status_counts": _status_counts(sources),
        "sources": sources,
        "source_artifacts": artifact_presence(root, DEFAULT_SOURCE_ARTIFACTS["lto032"]),
        "validation_boundary": "No historical gamma/VRP validation claim is allowed until legal timestamped sources and schemas exist.",
        **NO_ACTION_COUNTERS,
    }


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status") or "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def status_rows(
    *,
    lto024: dict[str, Any],
    lto031: dict[str, Any],
    lto032: dict[str, Any],
    generated_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    generated_at = generated_at_utc or utc_now_iso()
    payloads = [lto024, lto031, lto032]
    rows = []
    for payload in payloads:
        lto_id = str(payload["lto_id"])
        row = {
            "schema_version": STATUS_SCHEMA_VERSION,
            "created_at_utc": generated_at,
            "row_key": stable_hash(lto_id, payload["status"], "2026-05-05"),
            "lto_id": lto_id,
            "follow_ids": payload.get("follow_ids", []),
            "blocked_lane_status": payload["status"],
            "blocker_type": "APPROVAL_BLOCKED" if lto_id == "LTO-024" else "SOURCE_BLOCKED",
            "summary": payload["summary"],
            "source_count": payload.get("source_count", 0),
            "status_counts": payload.get("status_counts", {}),
            "action_required_codes": payload.get("action_required_codes", []),
            "promotion_verdict": PROMOTION_VERDICT,
            **NO_ACTION_COUNTERS,
        }
        rows.append(row)
    return rows


def build_all_payloads(root: Path, generated_at_utc: str | None = None) -> dict[str, Any]:
    generated_at = generated_at_utc or utc_now_iso()
    lto024 = lto024_payload(root, generated_at)
    lto031 = lto031_payload(root, generated_at)
    lto032 = lto032_payload(root, generated_at)
    rows = status_rows(lto024=lto024, lto031=lto031, lto032=lto032, generated_at_utc=generated_at)
    return {
        "created_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "reports": {
            "lto024": lto024,
            "lto031": lto031,
            "lto032": lto032,
        },
        "status_rows": rows,
    }


def render_lto024_markdown(payload: dict[str, Any]) -> str:
    lines = _header("LTO024 Component 3B / Tool Grounding / Reflexion Approval Dossier", payload)
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            f"- Current cost: `${payload['current_cost_usd']:.2f}`",
            f"- Future cost status: `{payload['future_cost_status']}`",
            f"- Status: `{payload['status']}`",
            "",
            "## Static Activation Check",
            "",
        ]
    )
    for key, value in payload["static_activation_check"]["findings"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## If Reopened, Must Define", ""])
    for decision in payload["owner_decisions_required"]:
        lines.append(f"- {decision}")
    lines.extend(["", "## Metrics", ""])
    for metric in payload["evaluation_metrics_if_reopened"]:
        lines.append(f"- {metric}")
    lines.extend(["", "## Stop Conditions", ""])
    for condition in payload["stop_conditions_if_reopened"]:
        lines.append(f"- {condition}")
    lines.extend(_footer())
    return "\n".join(lines) + "\n"


def render_source_readiness_markdown(title: str, payload: dict[str, Any]) -> str:
    lines = _header(title, payload)
    lines.extend(
        [
            "",
            "## Source Status",
            "",
            "| Source | Status | Legal/access path | Cache/schema | Expected use |",
            "|---|---|---|---|---|",
        ]
    )
    for source in payload["sources"]:
        lines.append(
            "| `{source}` | `{status}` | {access} | {schema} | {use} |".format(
                source=source["source_key"],
                status=source["status"],
                access=str(source.get("legal_access_path") or "").replace("|", "/"),
                schema=str(source.get("cache_schema") or "").replace("|", "/"),
                use=str(source.get("expected_use") or "").replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            f"- {payload['validation_boundary']}",
        ]
    )
    lines.extend(_footer())
    return "\n".join(lines) + "\n"


def _header(title: str, payload: dict[str, Any]) -> list[str]:
    return [
        f"# {title} - 2026-05-05",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Created:** `{payload['created_at_utc']}`",
        f"**LTO:** `{payload['lto_id']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        payload["summary"],
    ]


def _footer() -> list[str]:
    return [
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "This artifact is blocker/readiness evidence only. It does not validate, promote, wire, or alter live trading behavior.",
    ]
