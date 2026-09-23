from __future__ import annotations

import gzip
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"
ROUTE_ID = "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"

STAGE06_FEATURES = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_FEATURE_LEDGER_{DATE_ID}.jsonl"
STAGE06_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_SUMMARY_{DATE_ID}.json"
STAGE07_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_{DATE_ID}.json"
STAGE07_PROP_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_PROP_EV_ATTEMPT_LEDGER_{DATE_ID}.jsonl"
STAGE07_BRANCH_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_CORRECTED_BRANCH_METRICS_LEDGER_{DATE_ID}.jsonl"
NOFILL_INDEX = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "vnext_full_historical_candidate_generation_replay_2026_05_24"
    / "VNEXT_FULL_REPLAY_NOFILL_PENDING_LIFECYCLE_LEDGER_2026-05-24.jsonl"
)
CONFIG_PATH = REPO_ROOT / "config" / "agent_config.yaml"
PROFILE_PATH = REPO_ROOT / "config" / "profiles" / "redacted_account.yaml"
PROMPT_PATH = REPO_ROOT / "src" / "prompts" / "primary_analyzer_prompt.py"
STATE_PATH = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"

OUTPUT_ROLE_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_AI_ROLE_DECISION_LEDGER_{DATE_ID}.jsonl"
OUTPUT_MANIFEST = ROUTE_DIR / f"VNEXT_MOONSHOT_AI_VALIDATION_BUDGET_MANIFEST_{DATE_ID}.jsonl"
OUTPUT_REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_AI_VALIDATION_BUDGET_REPORT_{DATE_ID}.md"
OUTPUT_PACKET_SPEC = ROUTE_DIR / f"VNEXT_MOONSHOT_AI_PROMPT_PACKET_SPEC_{DATE_ID}.md"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_AI_ROLE_BUDGET_SUMMARY_{DATE_ID}.json"

MODEL_ID = "claude-sonnet-4-6"
MODEL_EFFORT = "max"
MAX_SELECTED_ROWS_PER_STRATUM = 32
MAX_PROP_STREAM_ROWS = 32
MAX_NOFILL_ROWS = 32

BUDGET_TIERS = [
    {
        "tier": "zero_call_design",
        "max_calls": 0,
        "max_spend_usd": 0.0,
        "can_support": "manifest/cache/prompt review only",
        "cannot_support": "AI incremental value, schema reliability, or production-role decision",
    },
    {
        "tier": "smoke_plumbing",
        "max_calls": 32,
        "max_spend_usd": 5.0,
        "can_support": "cache-key plumbing, prompt packet schema, malformed-response handling smoke",
        "cannot_support": "edge or branch-level AI-value claims",
    },
    {
        "tier": "decisive_low_budget",
        "max_calls": 128,
        "max_spend_usd": 15.0,
        "can_support": "directional false-positive/false-negative read across mandatory strata",
        "cannot_support": "production activation or model replacement",
    },
    {
        "tier": "strong_validation",
        "max_calls": 320,
        "max_spend_usd": 35.0,
        "can_support": "role decision between production gate, validator, MIXED resolver, and monitoring-only for selected strata",
        "cannot_support": "full historical AI backtest or live activation",
    },
    {
        "tier": "extended_validation",
        "max_calls": 512,
        "max_spend_usd": 50.0,
        "can_support": "broad selected-strata AI role decision under monthly cap if owner approves spend",
        "cannot_support": "removing production AI without separate sealed validation and owner approval",
    },
]

MANDATORY_STRATA = [
    "high_ev_opportunity_branch",
    "fixed_vs_dynamic_live_lost",
    "fixed_vs_dynamic_live_rescued",
    "same_bar_ambiguous",
    "high_quality_live_winner",
    "high_quality_live_loser",
    "costly_live_loser",
    "ai_required_context_rich",
    "no_paid_mechanical_control",
    "source_sensitive_window_incomplete",
    "market_awareness_edge_case",
    "prop_ev_optimized_candidate",
    "mixed_or_policy_disagreement_proxy",
    "nofill_pending_lifecycle",
    "prop_near_boundary_ev_stream",
]

OUTCOME_FIELDS_EXCLUDED_FROM_PACKET = [
    "legacy_final_r",
    "live_current_j46_j49_final_r",
    "be_after_trigger_final_r",
    "trailing_runner_final_r",
    "live_vs_legacy_delta_r",
    "policy_reversal_bucket",
    "mfe_r",
    "mae_r",
    "mfe_mae_ratio",
    "live_exit_reason",
    "live_exit_progress_fraction",
    "terminal_outcome",
    "pending_lifecycle_state",
    "post_trade_equity",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_payload(payload: Any) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_in_kill_zone(row: dict[str, Any]) -> bool:
    return str(row.get("kill_zone_position") or "").startswith("in_")


def source_computed(row: dict[str, Any]) -> bool:
    return row.get("source_path_feature_status") == "computed_from_source_ohlc_asof"


def feature_complete(row: dict[str, Any]) -> bool:
    return (
        source_computed(row)
        and row.get("trend_state_20") != "insufficient_lookback"
        and row.get("volatility_state_14_vs_50") != "insufficient_lookback"
    )


def no_high_news(row: dict[str, Any]) -> bool:
    return row.get("news_high_impact_within_120m") is not True


def side_aligned(row: dict[str, Any]) -> bool:
    side = str(row.get("side") or "").upper()
    trend = str(row.get("trend_state_20") or "")
    if trend == "flat":
        return True
    if side == "LONG":
        return trend in {"up", "strong_up"}
    if side == "SHORT":
        return trend in {"down", "strong_down"}
    return False


def high_quality(row: dict[str, Any]) -> bool:
    return is_in_kill_zone(row) and feature_complete(row) and no_high_news(row)


def context_rich(row: dict[str, Any]) -> bool:
    volatility = str(row.get("volatility_state_14_vs_50") or "")
    trend = str(row.get("trend_state_20") or "")
    displacement = safe_float(row.get("current_bar_displacement_atr14"))
    return (
        row.get("news_high_impact_within_120m") is True
        or volatility in {"high_recent_vs_baseline", "elevated_recent_vs_baseline"}
        or str(row.get("compression_expansion_state") or "") == "expansion"
        or trend in {"strong_up", "strong_down"}
        or (displacement is not None and displacement >= 1.5)
        or not is_in_kill_zone(row)
        or not bool(row.get("source_window_complete"))
    )


def no_paid_mechanical(row: dict[str, Any]) -> bool:
    volatility = str(row.get("volatility_state_14_vs_50") or "")
    trend = str(row.get("trend_state_20") or "")
    displacement = safe_float(row.get("current_bar_displacement_atr14"))
    return (
        high_quality(row)
        and volatility in {"normal_recent_vs_baseline", "low_recent_vs_baseline", "very_low_recent_vs_baseline"}
        and trend in {"flat", "up", "down"}
        and (displacement is None or displacement < 1.5)
    )


def market_awareness_edge(row: dict[str, Any]) -> bool:
    displacement = safe_float(row.get("current_bar_displacement_atr14"))
    return (
        row.get("news_high_impact_within_120m") is True
        or row.get("compression_expansion_state") == "expansion"
        or row.get("trend_state_20") in {"strong_up", "strong_down"}
        or row.get("liquidity_sweep_proxy_state") in {"swept_both_prior_20_extremes", "swept_prior_20_high", "swept_prior_20_low"}
        or (displacement is not None and displacement >= 2.0)
    )


def branch_match(row: dict[str, Any], branch_id: str) -> bool:
    if branch_id == "origin_current_fvg_fill":
        return row.get("framework") == "fvg_fill"
    if branch_id == "origin_current_ob_retest":
        return row.get("framework") == "ob_retest"
    if branch_id == "origin_current_breaker_re_entry":
        return row.get("framework") == "breaker_re_entry"
    if branch_id == "high_quality_asof_kz":
        return high_quality(row)
    if branch_id == "prop_ev_optimized_side_aligned_kz":
        return high_quality(row) and side_aligned(row)
    if branch_id == "ai_required_context_rich":
        return feature_complete(row) and context_rich(row)
    if branch_id == "no_paid_mechanical_diagnostic":
        return no_paid_mechanical(row)
    if branch_id == "raw_repaired_all_replayable":
        return True
    return False


def policy_value(row: dict[str, Any], policy_name: str) -> float | None:
    if policy_name == "legacy_fixed_1.5r":
        return safe_float(row.get("legacy_final_r"))
    if policy_name == "live_current_j46_j49":
        return safe_float(row.get("live_current_j46_j49_final_r"))
    if policy_name == "be_after_trigger":
        return safe_float(row.get("be_after_trigger_final_r"))
    if policy_name == "trailing_runner":
        return safe_float(row.get("trailing_runner_final_r"))
    return safe_float(row.get("live_current_j46_j49_final_r"))


def packet_for_feature_row(row: dict[str, Any], stratum_alias: str) -> dict[str, Any]:
    return {
        "packet_schema_version": "vnext_moonshot_ai_candidate_packet_v1",
        "packet_stratum_alias": stratum_alias,
        "candidate_id": row.get("candidate_id"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "framework": row.get("framework"),
        "candle_time_utc": row.get("candle_time_utc"),
        "entry_first_touch_utc": row.get("entry_first_touch_utc"),
        "session_bucket": row.get("session_bucket"),
        "session_subwindow": row.get("session_subwindow"),
        "kill_zone_position": row.get("kill_zone_position"),
        "weekday": row.get("weekday"),
        "month": row.get("month"),
        "quarter": row.get("quarter"),
        "source_mode": row.get("source_mode"),
        "source_timeframe": row.get("source_timeframe"),
        "source_window_complete": row.get("source_window_complete"),
        "source_path_hash": row.get("source_sha256"),
        "trend_state_20": row.get("trend_state_20"),
        "volatility_state_14_vs_50": row.get("volatility_state_14_vs_50"),
        "compression_expansion_state": row.get("compression_expansion_state"),
        "current_bar_displacement_atr14": row.get("current_bar_displacement_atr14"),
        "current_bar_speed_atr14": row.get("current_bar_speed_atr14"),
        "current_bar_direction": row.get("current_bar_direction"),
        "lookback50_position": row.get("lookback50_position"),
        "liquidity_sweep_proxy_state": row.get("liquidity_sweep_proxy_state"),
        "news_calendar_coverage_status": row.get("news_calendar_coverage_status"),
        "news_min_abs_minutes": row.get("news_min_abs_minutes"),
        "news_high_impact_within_120m": row.get("news_high_impact_within_120m"),
        "orderflow_depth_proxy_status": row.get("orderflow_depth_proxy_status"),
        "cross_asset_lead_lag_status": row.get("cross_asset_lead_lag_status"),
        "spread_slippage_cost_status": row.get("spread_slippage_cost_status"),
    }


def label_hash_for_feature_row(row: dict[str, Any]) -> str:
    label_payload = {
        "candidate_id": row.get("candidate_id"),
        "legacy_final_r": row.get("legacy_final_r"),
        "live_current_j46_j49_final_r": row.get("live_current_j46_j49_final_r"),
        "be_after_trigger_final_r": row.get("be_after_trigger_final_r"),
        "trailing_runner_final_r": row.get("trailing_runner_final_r"),
        "policy_reversal_bucket": row.get("policy_reversal_bucket"),
        "mfe_r": row.get("mfe_r"),
        "mae_r": row.get("mae_r"),
        "live_exit_reason": row.get("live_exit_reason"),
    }
    return hash_payload(label_payload)


def candidate_strata(row: dict[str, Any], best_branch: str, best_policy: str) -> list[str]:
    strata = []
    live_r = safe_float(row.get("live_current_j46_j49_final_r"))
    if branch_match(row, best_branch) and (policy_value(row, best_policy) or 0.0) > 0:
        strata.append("high_ev_opportunity_branch")
    if row.get("policy_reversal_bucket") == "dynamic_nonpositive_from_legacy_winner":
        strata.append("fixed_vs_dynamic_live_lost")
    if row.get("policy_reversal_bucket") == "dynamic_winner_from_legacy_nonpositive":
        strata.append("fixed_vs_dynamic_live_rescued")
    if row.get("same_bar_ambiguity"):
        strata.append("same_bar_ambiguous")
    if high_quality(row) and live_r is not None and live_r > 0:
        strata.append("high_quality_live_winner")
    if high_quality(row) and live_r is not None and live_r < 0:
        strata.append("high_quality_live_loser")
    if live_r is not None and live_r <= -1.0:
        strata.append("costly_live_loser")
    if feature_complete(row) and context_rich(row):
        strata.append("ai_required_context_rich")
    if no_paid_mechanical(row):
        strata.append("no_paid_mechanical_control")
    if not bool(row.get("source_window_complete")) or row.get("orderflow_depth_proxy_status") != "not_joined_stage06_source_limited":
        strata.append("source_sensitive_window_incomplete")
    if market_awareness_edge(row):
        strata.append("market_awareness_edge_case")
    if high_quality(row) and side_aligned(row):
        strata.append("prop_ev_optimized_candidate")
    if row.get("policy_reversal_bucket") not in {None, "same_result"} or row.get("same_bar_ambiguity"):
        strata.append("mixed_or_policy_disagreement_proxy")
    return strata


def keep_sample(samples: dict[str, list[tuple[str, dict[str, Any]]]], stratum: str, row: dict[str, Any]) -> None:
    key = sha256(f"{stratum}|{row.get('candidate_id')}|{row.get('source_sha256')}".encode("utf-8")).hexdigest()
    samples[stratum].append((key, row))
    if len(samples[stratum]) > MAX_SELECTED_ROWS_PER_STRATUM:
        samples[stratum] = sorted(samples[stratum], key=lambda item: item[0])[:MAX_SELECTED_ROWS_PER_STRATUM]


def read_candidate_samples(best_branch: str, best_policy: str) -> tuple[Counter[str], dict[str, list[tuple[str, dict[str, Any]]]]]:
    counts: Counter[str] = Counter()
    samples: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for row in iter_jsonl(STAGE06_FEATURES):
        for stratum in candidate_strata(row, best_branch, best_policy):
            counts[stratum] += 1
            keep_sample(samples, stratum, row)
    return counts, samples


def iter_nofill_rows() -> Iterable[dict[str, Any]]:
    for index_row in iter_jsonl(NOFILL_INDEX):
        chunk_path = REPO_ROOT / index_row["chunk_path"]
        with gzip.open(chunk_path, "rt", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def read_nofill_samples() -> tuple[int, list[tuple[str, dict[str, Any]]]]:
    count = 0
    samples: list[tuple[str, dict[str, Any]]] = []
    for row in iter_nofill_rows():
        if not row.get("no_fill"):
            continue
        count += 1
        key = sha256(f"nofill|{row.get('candidate_id')}|{row.get('source_path')}".encode("utf-8")).hexdigest()
        samples.append((key, row))
        if len(samples) > MAX_NOFILL_ROWS:
            samples = sorted(samples, key=lambda item: item[0])[:MAX_NOFILL_ROWS]
    return count, samples


def read_prop_stream_samples() -> tuple[int, list[tuple[str, dict[str, Any]]]]:
    count = 0
    samples: list[tuple[str, dict[str, Any]]] = []
    for row in iter_jsonl(STAGE07_PROP_LEDGER):
        near_boundary_actions = row.get("reduced_risk_trades", 0) + row.get("deferred_trades", 0) + row.get("abandon_restarts", 0)
        if near_boundary_actions <= 0:
            continue
        count += 1
        key = sha256(
            f"prop|{row.get('branch_id')}|{row.get('policy_name')}|{row.get('prop_policy')}".encode("utf-8")
        ).hexdigest()
        samples.append((key, row))
        if len(samples) > MAX_PROP_STREAM_ROWS:
            samples = sorted(samples, key=lambda item: item[0])[:MAX_PROP_STREAM_ROWS]
    return count, samples


def tier_for_rank(rank: int) -> str:
    for tier in BUDGET_TIERS:
        if rank <= tier["max_calls"]:
            return tier["tier"]
    return BUDGET_TIERS[-1]["tier"]


def build_manifest_rows(
    *,
    candidate_counts: Counter[str],
    candidate_samples: dict[str, list[tuple[str, dict[str, Any]]]],
    nofill_count: int,
    nofill_samples: list[tuple[str, dict[str, Any]]],
    prop_count: int,
    prop_samples: list[tuple[str, dict[str, Any]]],
    prompt_hash: str,
    config_hash: str,
    profile_hash: str,
    packet_spec_hash_seed: str,
) -> list[dict[str, Any]]:
    rows = []
    global_rank = 0
    stratum_alias = {name: f"S{index:02d}" for index, name in enumerate(MANDATORY_STRATA, start=1)}

    for stratum in MANDATORY_STRATA:
        if stratum == "nofill_pending_lifecycle":
            source_rows = nofill_samples
            eligible_count = nofill_count
        elif stratum == "prop_near_boundary_ev_stream":
            source_rows = prop_samples
            eligible_count = prop_count
        else:
            source_rows = candidate_samples.get(stratum, [])
            eligible_count = candidate_counts[stratum]
        for _, source_row in sorted(source_rows, key=lambda item: item[0]):
            global_rank += 1
            alias = stratum_alias[stratum]
            if stratum == "nofill_pending_lifecycle":
                packet = {
                    "packet_schema_version": "vnext_moonshot_ai_nofill_packet_v1",
                    "packet_stratum_alias": alias,
                    "candidate_id": source_row.get("candidate_id"),
                    "symbol": source_row.get("symbol"),
                    "side": source_row.get("side"),
                    "framework": source_row.get("framework"),
                    "candle_time_utc": source_row.get("candle_time_utc"),
                    "source_path": source_row.get("source_path"),
                    "best_available_replay_mode": source_row.get("best_available_replay_mode"),
                    "pending_horizon_policy": source_row.get("pending_horizon_policy"),
                }
                label_hash = hash_payload(
                    {
                        "candidate_id": source_row.get("candidate_id"),
                        "no_fill": source_row.get("no_fill"),
                        "terminal_outcome": source_row.get("terminal_outcome"),
                        "pending_lifecycle_state": source_row.get("pending_lifecycle_state"),
                    }
                )
                packet_type = "nofill_pending_lifecycle_candidate"
                source_refs = [source_row.get("source_path")]
            elif stratum == "prop_near_boundary_ev_stream":
                packet = {
                    "packet_schema_version": "vnext_moonshot_ai_prop_stream_packet_v1",
                    "packet_stratum_alias": alias,
                    "branch_id": source_row.get("branch_id"),
                    "dynamic_policy": source_row.get("policy_name"),
                    "prop_policy": source_row.get("prop_policy"),
                    "input_rows": source_row.get("input_rows"),
                    "segmented_account_attempts_modelled": source_row.get("segmented_account_attempts_modelled"),
                    "action_counts": source_row.get("action_counts"),
                    "redacted_account_rules_modelled": source_row.get("redacted_account_rules_modelled"),
                }
                label_hash = hash_payload(
                    {
                        "branch_id": source_row.get("branch_id"),
                        "policy_name": source_row.get("policy_name"),
                        "prop_policy": source_row.get("prop_policy"),
                        "expected_payout_proxy_usd_fee599_payout8000": source_row.get("expected_payout_proxy_usd_fee599_payout8000"),
                        "trade_opportunity_cost_r": source_row.get("trade_opportunity_cost_r"),
                    }
                )
                packet_type = "prop_near_boundary_stream"
                source_refs = [rel(STAGE07_PROP_LEDGER)]
            else:
                packet = packet_for_feature_row(source_row, alias)
                label_hash = label_hash_for_feature_row(source_row)
                packet_type = "corrected_dynamic_candidate"
                source_refs = [source_row.get("source_path"), rel(STAGE06_FEATURES)]
            packet_hash = hash_payload(packet)
            cache_key = hash_payload(
                {
                    "model_id": MODEL_ID,
                    "model_effort": MODEL_EFFORT,
                    "prompt_hash": prompt_hash,
                    "config_hash": config_hash,
                    "profile_hash": profile_hash,
                    "packet_spec_hash_seed": packet_spec_hash_seed,
                    "packet_hash": packet_hash,
                }
            )
            rows.append(
                {
                    "schema_version": "vnext_moonshot_ai_validation_budget_manifest_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": "STAGE_08_AI_ROLE_AND_BUDGET_DESIGN",
                    "manifest_row_id": f"STAGE08-AI-MANIFEST-{global_rank:04d}",
                    "global_budget_rank": global_rank,
                    "budget_tier_inclusion": tier_for_rank(global_rank),
                    "validation_stratum": stratum,
                    "validation_stratum_alias_for_prompt": alias,
                    "eligible_rows_in_stratum": eligible_count,
                    "selected_by": "deterministic_sha256_spread_sample_not_performance_top_n",
                    "packet_type": packet_type,
                    "candidate_id": packet.get("candidate_id") or f"{packet_type}:{global_rank:04d}",
                    "outcome_hidden_from_ai_packet": True,
                    "packet_payload": packet,
                    "packet_sha256": packet_hash,
                    "offline_scoring_label_sha256": label_hash,
                    "outcome_fields_excluded_from_packet": OUTCOME_FIELDS_EXCLUDED_FROM_PACKET,
                    "source_references": [ref for ref in source_refs if ref],
                    "cache_key_sha256": cache_key,
                    "cache_key_policy": "sha256(model_id, model_effort, prompt_hash, config_hash, profile_hash, packet_spec_hash_seed, packet_hash)",
                    "model_id": MODEL_ID,
                    "model_effort": MODEL_EFFORT,
                    "prompt_hash": prompt_hash,
                    "config_hash": config_hash,
                    "profile_hash": profile_hash,
                    "paid_api_or_vendor_call_made": False,
                }
            )
    return rows


def role_decision_rows(stage07_summary: dict[str, Any], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best = stage07_summary["best_overall_reference_fee599_payout8000"]
    manifest_count = len(manifest_rows)
    rows = [
        {
            "role": "production_decision_gate",
            "decision": "retain_pending_budgeted_ai_delta_validation",
            "production_api_role": True,
            "monitoring_agent_role": False,
            "rationale": "Corrected no-API replay proves mechanical and dynamic execution substrate, but does not measure production prompt incremental value or schema reliability.",
            "evidence": {"manifest_rows": manifest_count, "best_branch": best["branch_id"], "best_policy": best["policy_name"]},
        },
        {
            "role": "validator",
            "decision": "recommended_primary_stage08_paid_validation_role",
            "production_api_role": True,
            "monitoring_agent_role": False,
            "rationale": "AI should validate high-EV, disagreement, source-sensitive, and context-rich rows instead of brute-forcing every candidate.",
            "evidence": {"mandatory_strata": MANDATORY_STRATA},
        },
        {
            "role": "mixed_resolver",
            "decision": "recommended_for_policy_disagreement_and_ambiguous_rows",
            "production_api_role": True,
            "monitoring_agent_role": False,
            "rationale": "Fixed-vs-dynamic reversals and same-bar/MIXED proxies are where deterministic rules most need semantic adjudication.",
            "evidence": {"strata": ["fixed_vs_dynamic_live_lost", "fixed_vs_dynamic_live_rescued", "same_bar_ambiguous", "mixed_or_policy_disagreement_proxy"]},
        },
        {
            "role": "structural_critic",
            "decision": "recommended_for_context_rich_rows",
            "production_api_role": True,
            "monitoring_agent_role": False,
            "rationale": "Market-awareness edge cases and source-sensitive rows need critique of structure/context, not hidden outcome labels.",
            "evidence": {"strata": ["ai_required_context_rich", "market_awareness_edge_case", "source_sensitive_window_incomplete"]},
        },
        {
            "role": "malformed_response_repairer",
            "decision": "monitoring_agent_allowed_but_not_decision_replacement",
            "production_api_role": False,
            "monitoring_agent_role": True,
            "rationale": "A monitoring/supervisor agent may repair operations and malformed packets under bounds; it is not proven to replace the production decision API.",
            "evidence": {"boundary": "repair schema/ops only unless separate AI replacement validation passes"},
        },
        {
            "role": "supervisor_monitoring_assistant",
            "decision": "recommended_default_off_monitoring_role",
            "production_api_role": False,
            "monitoring_agent_role": True,
            "rationale": "Monitoring can watch cache misses, malformed responses, source gaps, and budget stops without choosing trades.",
            "evidence": {"budget_tiers": [tier["tier"] for tier in BUDGET_TIERS]},
        },
        {
            "role": "removable_component",
            "decision": "rejected_for_now",
            "production_api_role": False,
            "monitoring_agent_role": False,
            "rationale": "No corrected paid-AI delta evidence exists in this no-call route, so AI removal would be an unsupported production change.",
            "evidence": {"paid_api_calls_made": 0, "required_separate_evidence": "cached stratified AI delta audit"},
        },
    ]
    return [
        {
            "schema_version": "vnext_moonshot_ai_role_decision_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_08_AI_ROLE_AND_BUDGET_DESIGN",
            "role_decision_id": f"STAGE08-AI-ROLE-{index:03d}",
            **row,
            "no_paid_api_or_vendor_call": True,
        }
        for index, row in enumerate(rows, start=1)
    ]


def write_packet_spec(prompt_hash: str, config_hash: str, profile_hash: str) -> None:
    lines = [
        "# vNext Moonshot AI Prompt Packet Spec",
        "",
        "## Purpose",
        "",
        "Budgeted validation packets test the production AI decision layer after corrected no-API replay. They are not activation approval and they do not expose outcome labels to the AI packet.",
        "",
        "## Required Model Binding",
        "",
        f"- Model: `{MODEL_ID}`",
        f"- Effort: `{MODEL_EFFORT}`",
        f"- Prompt hash: `{prompt_hash}`",
        f"- Config hash: `{config_hash}`",
        f"- redacted_account profile hash: `{profile_hash}`",
        "",
        "## Allowed Packet Fields",
        "",
        "Only as-of candidate identity, symbol/session/side/framework, source hashes, source-completeness status, market-awareness fields, and prop-rule context are allowed.",
        "",
        "## Forbidden Packet Fields",
        "",
        "The packet must exclude final R, MFE/MAE, policy outcome, terminal outcome, lifecycle result, post-trade equity, and any future touch/order result. These are referenced only by offline scoring hashes.",
        "",
        "## Cache Key",
        "",
        "`sha256(model_id, model_effort, prompt_hash, config_hash, profile_hash, packet_spec_hash_seed, packet_hash)`",
        "",
        "## Malformed Handling",
        "",
        "Malformed, refusal, schema-missing, or hallucinated-field responses stop the current tier if the tier malformed rate exceeds 5% or if three consecutive responses fail. Monitoring agents may repair packet transport/schema only; they may not rewrite the trading decision.",
        "",
        "## Expected Output Schema",
        "",
        "The AI response must return `decision`, `confidence`, `required_context_fields_used`, `disallowed_fields_used=false`, `reason_codes`, `risk_notes`, and `schema_version`.",
        "",
    ]
    OUTPUT_PACKET_SPEC.write_text("\n".join(lines), encoding="utf-8")


def write_report(summary: dict[str, Any]) -> None:
    lines = [
        "# vNext Moonshot Stage08 AI Role And Budget Design",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Result",
        "",
        f"- Role decision rows: `{summary['role_decision_rows']}`",
        f"- Validation manifest rows: `{summary['manifest_rows']}`",
        f"- Mandatory strata covered: `{summary['mandatory_strata_covered']}` / `{len(MANDATORY_STRATA)}`",
        "- Paid API/vendor calls made: `0`",
        "",
        "## Role Decision",
        "",
        "- Keep production AI as a budgeted validator/gate pending cached delta validation.",
        "- Use AI most heavily on high-EV, disagreement, source-sensitive, context-rich, no-fill, and prop-near-boundary strata.",
        "- Treat monitoring/supervisor agents as operational repairers, not production decision replacements.",
        "- Do not remove AI from trade selection until a separate cached AI-delta audit proves replacement safety.",
        "",
        "## Budget Tiers",
        "",
    ]
    for tier in BUDGET_TIERS:
        lines.append(f"- `{tier['tier']}`: max_calls={tier['max_calls']} max_spend_usd={tier['max_spend_usd']} supports {tier['can_support']}.")
    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def update_state(summary: dict[str, Any]) -> None:
    if not STATE_PATH.exists():
        return
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = git_head()
    state["current_stage"] = "STAGE_08_AI_ROLE_AND_BUDGET_DESIGN"
    state["first_incomplete_invariant"] = "STAGE_09_ML_AND_SURROGATE_FEASIBILITY"
    state["exact_next_action"] = "Run Stage09 ML and surrogate feasibility from corrected labels and as-of features."
    state["completion_gate_status"] = "not_complete_first_incomplete_stage09"
    state["stage_status_table"]["STAGE_08_AI_ROLE_AND_BUDGET_DESIGN"] = "complete_no_paid_calls"
    state["stage_status_table"]["STAGE_09_ML_AND_SURROGATE_FEASIBILITY"] = "pending"
    state["row_counts_scanned"]["stage08_ai_role_decision_rows"] = summary["role_decision_rows"]
    state["row_counts_scanned"]["stage08_ai_validation_manifest_rows"] = summary["manifest_rows"]
    state["output_artifact_manifest"]["ai_role_decision_ledger"] = rel(OUTPUT_ROLE_LEDGER)
    state["output_artifact_manifest"]["ai_validation_budget_manifest"] = rel(OUTPUT_MANIFEST)
    state["output_artifact_manifest"]["ai_validation_budget_report"] = rel(OUTPUT_REPORT)
    state["output_artifact_manifest"]["ai_prompt_packet_spec"] = rel(OUTPUT_PACKET_SPEC)
    state["output_artifact_manifest"]["ai_role_budget_summary"] = rel(OUTPUT_SUMMARY)
    state.setdefault("verifiers_tests_run", []).append(
        {
            "command": (
                "py -3 research/science_program_2026_05/06_outcome_testing/"
                "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
                "build_vnext_moonshot_stage08_ai_role_budget_design_2026_05_26.py"
            ),
            "status": "passed",
            "result": (
                f"manifest_rows={summary['manifest_rows']}; "
                f"role_rows={summary['role_decision_rows']}; "
                "first_incomplete=STAGE_09_ML_AND_SURROGATE_FEASIBILITY"
            ),
        }
    )
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build() -> dict[str, Any]:
    stage06_summary = json.loads(STAGE06_SUMMARY.read_text(encoding="utf-8"))
    stage07_summary = json.loads(STAGE07_SUMMARY.read_text(encoding="utf-8"))
    prompt_hash = hash_file(PROMPT_PATH)
    config_hash = hash_file(CONFIG_PATH)
    profile_hash = hash_file(PROFILE_PATH)
    packet_spec_hash_seed = hash_payload({"route": ROUTE_ID, "stage": "STAGE_08_AI_ROLE_AND_BUDGET_DESIGN", "date": DATE_ID})
    best = stage07_summary["best_overall_reference_fee599_payout8000"]
    candidate_counts, candidate_samples = read_candidate_samples(best["branch_id"], best["policy_name"])
    nofill_count, nofill_samples = read_nofill_samples()
    prop_count, prop_samples = read_prop_stream_samples()
    write_packet_spec(prompt_hash, config_hash, profile_hash)
    manifest_rows = build_manifest_rows(
        candidate_counts=candidate_counts,
        candidate_samples=candidate_samples,
        nofill_count=nofill_count,
        nofill_samples=nofill_samples,
        prop_count=prop_count,
        prop_samples=prop_samples,
        prompt_hash=prompt_hash,
        config_hash=config_hash,
        profile_hash=profile_hash,
        packet_spec_hash_seed=packet_spec_hash_seed,
    )
    role_rows = role_decision_rows(stage07_summary, manifest_rows)
    with OUTPUT_MANIFEST.open("w", encoding="utf-8", newline="\n") as handle:
        for row in manifest_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    with OUTPUT_ROLE_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for row in role_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    stratum_counts = Counter(row["validation_stratum"] for row in manifest_rows)
    summary = {
        "schema_version": "vnext_moonshot_ai_role_budget_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_08_AI_ROLE_AND_BUDGET_DESIGN",
        "generated_at_utc": utc_now(),
        "current_git_head": git_head(),
        "role_decision_ledger_path": rel(OUTPUT_ROLE_LEDGER),
        "ai_validation_budget_manifest_path": rel(OUTPUT_MANIFEST),
        "ai_validation_budget_report_path": rel(OUTPUT_REPORT),
        "ai_prompt_packet_spec_path": rel(OUTPUT_PACKET_SPEC),
        "role_decision_rows": len(role_rows),
        "manifest_rows": len(manifest_rows),
        "manifest_stratum_counts": dict(sorted(stratum_counts.items())),
        "mandatory_strata": MANDATORY_STRATA,
        "mandatory_strata_covered": sum(1 for stratum in MANDATORY_STRATA if stratum_counts[stratum] > 0),
        "candidate_eligible_stratum_counts": dict(sorted(candidate_counts.items())),
        "nofill_eligible_rows": nofill_count,
        "prop_near_boundary_eligible_streams": prop_count,
        "budget_tiers": BUDGET_TIERS,
        "packet_outcome_hidden": True,
        "outcome_fields_excluded_from_packet": OUTCOME_FIELDS_EXCLUDED_FROM_PACKET,
        "cache_key_policy": "sha256(model_id, model_effort, prompt_hash, config_hash, profile_hash, packet_spec_hash_seed, packet_hash)",
        "prompt_hash": prompt_hash,
        "config_hash": config_hash,
        "profile_hash": profile_hash,
        "stage06_feature_rows": stage06_summary.get("feature_rows"),
        "stage07_best_reference_stream": best,
        "paid_api_or_vendor_calls_made": 0,
        "forbidden_boundaries_crossed": False,
        "production_ai_api_distinct_from_monitoring_agent": True,
        "first_incomplete_invariant_after_stage08": "STAGE_09_ML_AND_SURROGATE_FEASIBILITY",
    }
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(summary)
    update_state(summary)
    return summary


def main() -> None:
    summary = build()
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "stage": "STAGE_08_AI_ROLE_AND_BUDGET_DESIGN",
                "manifest_rows": summary["manifest_rows"],
                "role_decision_rows": summary["role_decision_rows"],
                "mandatory_strata_covered": summary["mandatory_strata_covered"],
                "first_incomplete_invariant": summary["first_incomplete_invariant_after_stage08"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
