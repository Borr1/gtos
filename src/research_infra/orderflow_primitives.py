"""LTO-033 orderflow primitive registry and cached-feature readiness audit.

This module is research/tooling only. It defines measurable orderflow
primitives and summarizes whether current cached/local artifacts can support
them. It does not call Databento, Sierra, MT5, AI, canaries, or order code.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research_infra.databento_live_shadow import (
    COOLDOWN_SECONDS,
    DAILY_SPEND_CAP_USD,
    MAX_COST_PER_TRIGGER_USD,
    MAX_RECORDS_PER_TRIGGER,
    POLICY_ID as DATABENTO_POLICY_ID,
)

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "orderflow_primitives_status_v1"
REPORT_SCHEMA_VERSION = "lto033_orderflow_primitives_v1"
REGISTRY_VERSION = "orderflow_primitive_registry_v1"
LTO_ID = "LTO-033"
FOLLOW_ID = "LIVE-FOLLOW-031"

DEFAULT_CACHED_TRADES = Path(
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_AGGRESSIVE_SURGICAL_TRADES_FEATURES_2026-05-02.json"
)
DEFAULT_CACHED_MBP10 = Path(
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_AGGRESSIVE_PROXY_EXPANDED_MBP10_FEATURES_2026-05-02.json"
)
DEFAULT_CACHED_MBO = Path(
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_MBO_FEATURE_DIAGNOSTIC_2026-05-02.json"
)
DEFAULT_NAS100_FORENSICS = Path(
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.json"
)
DEFAULT_LTO010 = Path("research/program_control/LTO010_DATABENTO_LIVE_CONFLUENCE_POLICY_2026-05-05.json")
DEFAULT_LTO011 = Path("research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.json")
DEFAULT_LTO012 = Path("research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.json")
DEFAULT_LTO030 = Path("research/program_control/LTO030_6B_SI_DEPTH_POLICY_2026-05-05.json")

ALLOWED_DECISION_PREFIXES = ("pre60_", "event15_", "profile_")
FORBIDDEN_DECISION_PREFIXES = ("post15_", "post60_")

NO_DECISION_COUNTERS = {
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "paid_data_calls": 0,
    "paid_fetch_attempted": False,
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path | str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _file_hash(path: Path) -> str:
    if not path.exists():
        return "missing"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_signature(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: str(item)):
        digest.update(str(path).replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(path.exists()).encode("ascii"))
        digest.update(b"\0")
        digest.update(_file_hash(path).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()[:32]


def _row_key(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:32]


def primitive_registry() -> list[dict[str, Any]]:
    """Return the frozen LTO-033 primitive design registry."""
    common_trigger = {
        "trigger_type": "GTOS_STRUCTURAL_CANDIDATE_WINDOW",
        "required_join_keys": ["candidate_id", "decision_time_utc", "symbol", "framework", "side"],
        "decision_cutoff": "decision_time_utc",
        "windows": ["pre60", "event15"],
        "forensic_only_windows": ["post15", "post60"],
    }
    return [
        {
            "primitive_id": "X1_FOOTPRINT_DELTA_ABSORPTION_V1",
            "x_lane": "X-1",
            "family": "footprint_delta_absorption",
            "definition": "Aggressive trade delta and absorption around the POI before the decision cutoff.",
            "source_priority": [
                "Sierra .scid bid/ask volume when footprint conversion is registered",
                "Databento trades schema for normalized futures proxy replay/live collection",
            ],
            "schemas": ["trades", "sierra_scid"],
            "decision_feature_fields": [
                "pre60_signed_volume",
                "pre60_buy_fraction",
                "pre60_absorption_volume_per_tick",
                "pre60_delta_price_divergence",
                "event15_signed_volume",
                "event15_buy_fraction",
                "event15_absorption_volume_per_tick",
                "event15_delta_price_divergence",
            ],
            "continuous_measures_first": [
                "signed delta",
                "buy volume fraction",
                "absorption volume per tick",
                "delta-price divergence flag",
            ],
            "threshold_policy": "continuous_first_no_threshold_until_forward_rows",
            "candidate_trigger": common_trigger,
            "roles_to_evaluate": [
                "entry_timing",
                "bad_condition_veto",
                "stop_invalidation_efficiency",
            ],
            "current_status": "CACHED_TRADES_EXTRACTOR_READY_SIERRA_FOOTPRINT_PARTIAL",
            "blocker_codes": ["SIERRA_SCID_FOOTPRINT_CONVERTER_NOT_FULLY_REGISTERED"],
        },
        {
            "primitive_id": "X1_STACKED_IMBALANCE_FOOTPRINT_V1",
            "x_lane": "X-1",
            "family": "stacked_imbalance",
            "definition": "Consecutive bid/ask volume imbalance by price level inside footprint bars.",
            "source_priority": [
                "Sierra footprint/.scid bid/ask-volume by price level",
                "Databento trades only as a weak approximation; not enough for true stacked footprint imbalance",
            ],
            "schemas": ["sierra_scid", "trades"],
            "decision_feature_fields": [
                "pre60_stacked_imbalance_run_count",
                "event15_stacked_imbalance_run_count",
                "event15_max_bid_ask_volume_ratio_by_price",
                "event15_imbalance_price_level_count",
            ],
            "continuous_measures_first": [
                "run length of same-side imbalance",
                "max bid/ask volume ratio by price level",
                "imbalance price-level density",
            ],
            "threshold_policy": "registered_feature_names_only_no_ratio_threshold_selected",
            "candidate_trigger": common_trigger,
            "roles_to_evaluate": [
                "entry_timing",
                "bad_condition_veto",
            ],
            "current_status": "SOURCE_NOT_CAPTURED_REGISTERED_PRIMITIVE",
            "blocker_codes": ["FOOTPRINT_PRICE_LEVEL_BID_ASK_VOLUME_NOT_CAPTURED"],
        },
        {
            "primitive_id": "X2_DEPTH_THINNESS_WALL_CONCENTRATION_V1",
            "x_lane": "X-2",
            "family": "depth_thinness_wall_concentration",
            "definition": "Top-of-book depth, thinness, imbalance, near/far concentration, and bid/ask walls before entry.",
            "source_priority": [
                "Sierra .depth when source/parity policy allows interpretation",
                "Databento mbp-10 for canonical proxy replay/live collection",
            ],
            "schemas": ["mbp-10", "sierra_depth"],
            "decision_feature_fields": [
                "pre60_median_total_depth10",
                "pre60_median_depth10_imbalance",
                "event15_median_total_depth10",
                "event15_thin_depth10_rate",
                "event15_median_depth10_imbalance",
                "event15_median_near_far_ratio",
                "event15_median_max_bid_wall",
                "event15_median_max_ask_wall",
            ],
            "continuous_measures_first": [
                "depth10 total depth",
                "depth10 imbalance",
                "thin-depth rate",
                "near/far depth ratio",
                "bid/ask max wall size",
            ],
            "threshold_policy": "continuous_first_no_wall_or_thinness_threshold_selected",
            "candidate_trigger": common_trigger,
            "roles_to_evaluate": [
                "bad_condition_veto",
                "entry_timing",
                "stop_invalidation_efficiency",
            ],
            "current_status": "CACHED_MBP10_AND_SIERRA_DEPTH_AVAILABLE_WITH_PROXY_POLICIES",
            "blocker_codes": ["DATABENTO_LIVE_LICENSE_BLOCKED", "SYMBOL_SPECIFIC_SIERRA_PARITY_REQUIRED"],
        },
        {
            "primitive_id": "X2_LIQUIDITY_PULL_DEPLETION_V1",
            "x_lane": "X-2",
            "family": "liquidity_pull_depletion",
            "definition": "Near-touch adds, pulls, and net-liquidity depletion before the decision cutoff.",
            "source_priority": [
                "Databento MBO for add/remove events",
                "Sierra depth snapshots for coarser pull/depletion approximations only after a parity policy",
            ],
            "schemas": ["mbo", "sierra_depth"],
            "decision_feature_fields": [
                "pre60_near10_pull_pressure",
                "pre60_near10_net_liquidity",
                "event15_near10_add_size",
                "event15_near10_remove_size",
                "event15_near10_pull_pressure",
                "event15_near10_net_liquidity",
            ],
            "continuous_measures_first": [
                "near-touch pull pressure",
                "near-touch add/remove size",
                "near-touch net liquidity",
            ],
            "threshold_policy": "continuous_first_no_pull_threshold_selected",
            "candidate_trigger": common_trigger,
            "roles_to_evaluate": [
                "bad_condition_veto",
                "entry_timing",
            ],
            "current_status": "NAS100_CACHED_MBO_DIAGNOSTIC_ONLY_LIVE_LICENSE_BLOCKED",
            "blocker_codes": ["DATABENTO_LIVE_LICENSE_BLOCKED", "MBO_COST_AND_STORAGE_CAP_REQUIRED"],
        },
        {
            "primitive_id": "X3_META_ORDER_FLOW_QUEUE_BEHAVIOR_V1",
            "x_lane": "X-3",
            "family": "meta_order_flow_queue_behavior",
            "definition": "Order-level add/cancel/fill intensity, queue churn, and book resets as meta-order-flow context.",
            "source_priority": ["Databento MBO order-level events"],
            "schemas": ["mbo"],
            "decision_feature_fields": [
                "pre60_action_count",
                "event15_action_count",
                "mbo_book_clear_count",
                "event15_near10_add_bid_size",
                "event15_near10_add_ask_size",
                "event15_near10_remove_bid_size",
                "event15_near10_remove_ask_size",
            ],
            "continuous_measures_first": [
                "action count intensity",
                "bid/ask add-remove asymmetry",
                "book clear/reset count",
            ],
            "threshold_policy": "diagnostic_only_until_mbo_forward_cost_value_is_proven",
            "candidate_trigger": {
                **common_trigger,
                "activation_scope": "targeted NAS100/NQ forensic windows first",
            },
            "roles_to_evaluate": [
                "bad_condition_veto",
                "target_rr_expansion",
            ],
            "current_status": "MBO_SOURCE_BLOCKED_FOR_LIVE_LICENSE_AND_COST_VALUE",
            "blocker_codes": ["DATABENTO_LIVE_LICENSE_BLOCKED", "MBO_NOT_DEFAULT_COLLECTION_SCHEMA"],
        },
        {
            "primitive_id": "VP_VOLUME_PROFILE_CONTEXT_V1",
            "x_lane": "X-1",
            "family": "volume_profile_context",
            "definition": "Decision-time relation to POC, VAH, VAL, HVN, and LVN context around the GTOS POI.",
            "source_priority": [
                "Sierra .scid/session profile and footprint chart state",
                "Databento trades-derived event-window profile for normalized replay",
            ],
            "schemas": ["trades", "sierra_scid"],
            "decision_feature_fields": [
                "profile_poc_price",
                "profile_event_price_volume_percentile",
                "profile_nearest_hvn_distance_ticks",
                "profile_nearest_lvn_distance_ticks",
                "profile_levels",
                "profile_vah_price",
                "profile_val_price",
            ],
            "continuous_measures_first": [
                "distance to POC",
                "event price volume percentile",
                "nearest HVN/LVN distance",
                "distance to VAH/VAL once captured",
            ],
            "threshold_policy": "POC_HVN_LVN_PARTIAL_NO_VAH_VAL_THRESHOLD",
            "candidate_trigger": common_trigger,
            "roles_to_evaluate": [
                "target_rr_expansion",
                "stop_invalidation_efficiency",
                "entry_timing",
            ],
            "current_status": "EXTRACTOR_PARTIAL_POC_HVN_LVN_READY_VAH_VAL_NOT_CAPTURED",
            "blocker_codes": ["VAH_VAL_NOT_CAPTURED", "SESSION_PROFILE_DEFINITION_NOT_FROZEN"],
        },
    ]


def no_lookahead_check(registry: list[dict[str, Any]]) -> dict[str, Any]:
    bad_fields: dict[str, list[str]] = {}
    fields_checked = 0
    for primitive in registry:
        primitive_bad: list[str] = []
        for field in primitive.get("decision_feature_fields") or []:
            fields_checked += 1
            text = str(field)
            if text.startswith(FORBIDDEN_DECISION_PREFIXES):
                primitive_bad.append(text)
        if primitive_bad:
            bad_fields[str(primitive["primitive_id"])] = primitive_bad
    return {
        "status": "PASS" if not bad_fields else "FAIL",
        "fields_checked": fields_checked,
        "forbidden_decision_prefixes": list(FORBIDDEN_DECISION_PREFIXES),
        "allowed_decision_prefixes": list(ALLOWED_DECISION_PREFIXES),
        "bad_fields": bad_fields,
        "post_event_policy": "post15/post60 fields are forensic-only and are not in primitive decision_feature_fields",
    }


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def summarize_feature_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in (payload.get("feature_rows") or []) if isinstance(row, dict)]
    ok_rows = [row for row in rows if row.get("data_status") == "ok"]
    candidate_rows = [row for row in ok_rows if row.get("event_class") == "candidate"]
    field_counts: dict[str, int] = {}
    for row in ok_rows:
        for key, value in row.items():
            if value is not None:
                field_counts[key] = field_counts.get(key, 0) + 1
    return {
        "schema_version": payload.get("schema_version"),
        "feature_row_count": len(rows),
        "ok_row_count": len(ok_rows),
        "candidate_row_count": len(candidate_rows),
        "data_status_counts": dict(payload.get("synthesis", {}).get("data_status_counts") or {}),
        "non_null_field_counts": field_counts,
    }


def _artifact_feature_fields(summaries: dict[str, dict[str, Any]]) -> set[str]:
    fields: set[str] = set()
    for summary in summaries.values():
        fields.update((summary.get("non_null_field_counts") or {}).keys())
    return fields


def field_coverage(registry: list[dict[str, Any]], summaries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    available = _artifact_feature_fields(summaries)
    out: dict[str, Any] = {}
    for primitive in registry:
        fields = [str(field) for field in primitive.get("decision_feature_fields") or []]
        present = [field for field in fields if field in available]
        missing = [field for field in fields if field not in available]
        out[str(primitive["primitive_id"])] = {
            "decision_field_count": len(fields),
            "available_decision_fields": present,
            "missing_decision_fields": missing,
            "coverage_ratio": round(len(present) / len(fields), 6) if fields else None,
            "current_status": primitive.get("current_status"),
            "blocker_codes": primitive.get("blocker_codes", []),
        }
    return out


def cached_stability_summary(forensics: dict[str, Any]) -> dict[str, Any]:
    feeds = forensics.get("feeds") or {}
    if not feeds:
        return {
            "status": "NO_CACHED_FORENSICS_PAYLOAD",
            "feeds": {},
            "claim_boundary": "feature registry only; no stability evidence loaded",
        }
    out: dict[str, Any] = {}
    for feed, row in feeds.items():
        coverage = row.get("coverage") or {}
        labels = row.get("label_coverage") or {}
        concentration = row.get("concentration") or {}
        stability = row.get("stability") or {}
        depth = ((stability.get("event15_total_depth") or {}).get("leave_one_date") or {})
        thin = ((stability.get("event15_thin_rate") or {}).get("leave_one_date") or {})
        imbalance = ((stability.get("event15_imbalance") or {}).get("leave_one_date") or {})
        out[str(feed)] = {
            "candidate_rows": coverage.get("candidate_rows"),
            "context_rows": coverage.get("context_rows"),
            "actual_r_rows": labels.get("actual_r_n"),
            "synthetic_label_rows": labels.get("synthetic_label_n"),
            "top_candidate_date_share": (concentration.get("candidate_by_date") or {}).get("top_share"),
            "event15_total_depth_leave_one_date_sign_flips": depth.get("sign_flip_count"),
            "event15_thin_rate_leave_one_date_sign_flips": thin.get("sign_flip_count"),
            "event15_imbalance_leave_one_date_sign_flips": imbalance.get("sign_flip_count"),
        }
    return {
        "status": "DIAGNOSTIC_ONLY_LABEL_LIMITED",
        "feeds": out,
        "claim_boundary": (
            "Cached feature stability supports forward field selection only. It does not validate a live filter "
            "because actual broker-R coverage is sparse and date concentration is high."
        ),
    }


def _path_status(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def source_readiness(paths: dict[str, Path], payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    lto011 = payloads.get("lto011") or {}
    lto012 = payloads.get("lto012") or {}
    lto030 = payloads.get("lto030") or {}
    return {
        "cached_artifacts": {name: _path_status(path) for name, path in paths.items()},
        "databento_live": {
            "status": lto011.get("status") or "UNKNOWN",
            "license_blocker": bool(
                ((lto011.get("status_row") or {}).get("databento_live_status") or {}).get("license_blocker")
            ),
            "policy_id": DATABENTO_POLICY_ID,
        },
        "sierra_depth": {
            "status": lto012.get("status") or "UNKNOWN",
            "candidate_rows": ((lto012.get("status_row") or {}).get("current_counts") or {}).get("latest_candidate_rows"),
            "features_extracted": ((lto012.get("status_row") or {}).get("current_counts") or {}).get("features_extracted"),
        },
        "sierra_6b_si_policy": {
            "status": lto030.get("status") or "UNKNOWN",
            "common_second_alignment_policy_registered_for_6b": (
                (lto030.get("completion_evidence") or {}).get("common_second_alignment_policy_registered_for_6b")
            ),
            "si_depth_definition_remains_blocked": (
                (lto030.get("completion_evidence") or {}).get("si_depth_definition_remains_blocked")
            ),
        },
    }


def role_matrix(registry: list[dict[str, Any]]) -> dict[str, list[str]]:
    matrix: dict[str, list[str]] = {
        "entry_timing": [],
        "bad_condition_veto": [],
        "stop_invalidation_efficiency": [],
        "target_rr_expansion": [],
    }
    for primitive in registry:
        primitive_id = str(primitive["primitive_id"])
        for role in primitive.get("roles_to_evaluate") or []:
            if role in matrix:
                matrix[role].append(primitive_id)
    return matrix


def cost_policy() -> dict[str, Any]:
    return {
        "policy_id": DATABENTO_POLICY_ID,
        "max_cost_per_trigger_usd": MAX_COST_PER_TRIGGER_USD,
        "daily_spend_cap_usd": DAILY_SPEND_CAP_USD,
        "cooldown_seconds": COOLDOWN_SECONDS,
        "max_records_per_trigger": MAX_RECORDS_PER_TRIGGER,
        "schema_tiers": {
            "trades": "default lowest-cost normalized trade/footprint proxy when live license is available",
            "mbp-10": "targeted depth windows for registered candidates and source/parity-tested symbols",
            "mbo": "surgical NAS100/NQ forensic windows only until cost/value is proven",
            "sierra": "local file-based capture; no Databento paid call",
        },
        "this_audit_paid_data_calls": 0,
    }


def build_status_row(
    *,
    generated_at_utc: str,
    source_dependency_signature: str,
    registry: list[dict[str, Any]],
    feature_coverage: dict[str, Any],
    no_lookahead: dict[str, Any],
    stability: dict[str, Any],
    readiness: dict[str, Any],
) -> dict[str, Any]:
    blocker_codes = sorted(
        {
            code
            for primitive in registry
            for code in (primitive.get("blocker_codes") or [])
        }
    )
    status = (
        "OK_PRIMITIVES_REGISTERED_WITH_SOURCE_BLOCKERS"
        if no_lookahead.get("status") == "PASS"
        else "ACTION_REQUIRED_NO_LOOKAHEAD_FAILURE"
    )
    primitive_ids = [str(primitive["primitive_id"]) for primitive in registry]
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _row_key(SCHEMA_VERSION, REGISTRY_VERSION, source_dependency_signature, ",".join(primitive_ids)),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "lto_id": LTO_ID,
        "follow_id": FOLLOW_ID,
        "status": status,
        "registry_version": REGISTRY_VERSION,
        "primitive_count": len(registry),
        "primitive_ids": primitive_ids,
        "feature_families": sorted({str(primitive["family"]) for primitive in registry}),
        "roles_evaluated_separately": role_matrix(registry),
        "candidate_trigger_policy": {
            "trigger_type": "GTOS_STRUCTURAL_CANDIDATE_WINDOW",
            "required_join_keys": ["candidate_id", "decision_time_utc", "symbol", "framework", "side"],
            "decision_cutoff": "decision_time_utc",
            "default_windows": ["pre60", "event15"],
            "post_event_policy": "post-event fields are forensic-only unless a pre-decision window exists",
        },
        "cost_policy": cost_policy(),
        "no_lookahead_check": no_lookahead,
        "field_coverage": feature_coverage,
        "cached_feature_stability": stability,
        "source_readiness": readiness,
        "blocker_codes": blocker_codes,
        "claim_boundary": (
            "Primitive registration and cached feature design only. No live filter, signal, risk modifier, "
            "entry rule, target rule, or promotion claim is authorized."
        ),
        "no_leak_status": "PRIMITIVE_REGISTRY_AND_CACHED_ASOF_FEATURES_ONLY",
        "promotion_verdict": PROMOTION_VERDICT,
        **NO_DECISION_COUNTERS,
    }


def build_report_payload(
    *,
    root: Path,
    generated_at_utc: str | None = None,
    cached_trades_path: Path = DEFAULT_CACHED_TRADES,
    cached_mbp10_path: Path = DEFAULT_CACHED_MBP10,
    cached_mbo_path: Path = DEFAULT_CACHED_MBO,
    nas100_forensics_path: Path = DEFAULT_NAS100_FORENSICS,
    lto010_path: Path = DEFAULT_LTO010,
    lto011_path: Path = DEFAULT_LTO011,
    lto012_path: Path = DEFAULT_LTO012,
    lto030_path: Path = DEFAULT_LTO030,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    registry = primitive_registry()
    relative_paths = {
        "cached_trades": cached_trades_path,
        "cached_mbp10": cached_mbp10_path,
        "cached_mbo": cached_mbo_path,
        "nas100_cached_forensics": nas100_forensics_path,
        "lto010": lto010_path,
        "lto011": lto011_path,
        "lto012": lto012_path,
        "lto030": lto030_path,
    }
    full_paths = {name: root / path for name, path in relative_paths.items()}
    payloads = {name: read_json(path) for name, path in full_paths.items()}
    summaries = {
        "cached_trades": summarize_feature_payload(payloads["cached_trades"]),
        "cached_mbp10": summarize_feature_payload(payloads["cached_mbp10"]),
        "cached_mbo": summarize_feature_payload(payloads["cached_mbo"]),
    }
    signature = source_signature(list(full_paths.values()))
    no_lookahead = no_lookahead_check(registry)
    coverage = field_coverage(registry, summaries)
    stability = cached_stability_summary(payloads["nas100_cached_forensics"])
    readiness = source_readiness(full_paths, payloads)
    status_row = build_status_row(
        generated_at_utc=generated,
        source_dependency_signature=signature,
        registry=registry,
        feature_coverage=coverage,
        no_lookahead=no_lookahead,
        stability=stability,
        readiness=readiness,
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": generated,
        "lto_id": LTO_ID,
        "follow_id": FOLLOW_ID,
        "status": status_row["status"],
        "promotion_verdict": PROMOTION_VERDICT,
        "source_dependency_signature": signature,
        "source_paths": {name: str(path) for name, path in relative_paths.items()},
        "primitive_registry": registry,
        "cached_feature_summaries": summaries,
        "status_row": status_row,
        "completion_evidence": {
            "primitive_count": len(registry),
            "required_families_present": required_families_present(registry),
            "no_lookahead_pass": no_lookahead.get("status") == "PASS",
            "roles_are_separate": all(role_matrix(registry).values()),
            "cost_policy_declared": True,
            "status_log_schema": SCHEMA_VERSION,
            "new_paid_data_calls": 0,
            "live_trading_behavior_changed": False,
        },
        "synthesis": {
            "summary": (
                "LTO-033 is now registered as measurable orderflow primitives instead of broad opinions. "
                "Current cached/local data supports trades-level delta/absorption, MBP-10 depth, NAS100 MBO "
                "diagnostics, and partial volume-profile context; stacked footprint imbalance and VAH/VAL remain "
                "source-not-captured; Databento live remains license-blocked."
            ),
            "next_actions": [
                "Use these primitive IDs in future Sierra/Databento candidate-window rows.",
                "Keep post15/post60 fields forensic only and score only pre60/event15/profile decision fields.",
                "Prioritize Sierra .scid footprint conversion for stacked imbalance and VAH/VAL semantics.",
                "Use MBO only in surgical NAS100/NQ windows until live license/cost/value evidence is stronger.",
            ],
            "non_claims": [
                "No orderflow primitive is promoted.",
                "No threshold is selected.",
                "No live filter, target, stop, risk, prompt, execution, or order behavior changed.",
            ],
        },
    }


def required_families_present(registry: list[dict[str, Any]]) -> dict[str, bool]:
    families = {str(primitive.get("family")) for primitive in registry}
    return {
        "footprint_delta_absorption": "footprint_delta_absorption" in families,
        "stacked_imbalance": "stacked_imbalance" in families,
        "depth_thinness": "depth_thinness_wall_concentration" in families,
        "liquidity_pulls": "liquidity_pull_depletion" in families,
        "wall_concentration": "depth_thinness_wall_concentration" in families,
        "volume_profile_context": "volume_profile_context" in families,
        "meta_order_flow": "meta_order_flow_queue_behavior" in families,
    }
