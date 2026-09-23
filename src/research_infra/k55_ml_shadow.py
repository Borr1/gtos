"""K55 read-only ML shadow feature and prediction substrate.

This module builds candidate-scoped ML shadow rows from already-written
decision-time/as-of shadow logs. It does not call AI, canaries, MT5 order APIs,
Databento, or Sierra. A prediction is computed only when an explicit JSON model
artifact matches the registered target and feature-bundle versions; otherwise
the row records a feature bundle with inference disabled.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "ml_shadow_prediction_v1"
REGISTRY_SCHEMA_VERSION = "k55_target_feature_registry_v1"
TARGET_VERSION = "k55_target_v1_account_history_realized_primary_synthetic_path_context_2026_05_05"
FEATURE_BUNDLE_VERSION = "k55_feature_bundle_v1_lto001_020_orderflow_asof_2026_05_05"
INFERENCE_VERSION = "k55_shadow_inference_v1_json_linear_or_disabled"
CLASSIFIER_VERSION = "k55_ml_shadow_builder_v1"

PREDICTION_COMPUTED = "ML_SHADOW_PREDICTION_COMPUTED"
FEATURE_READY_MODEL_PENDING = "ML_SHADOW_FEATURE_BUNDLE_READY_MODEL_ARTIFACT_PENDING"
FEATURE_PARTIAL_MODEL_PENDING = "ML_SHADOW_FEATURE_BUNDLE_PARTIAL_MODEL_ARTIFACT_PENDING"
MODEL_INVALID = "ML_SHADOW_MODEL_ARTIFACT_INVALID_INFERENCE_DISABLED"
ACTION_REQUIRED = "ML_SHADOW_ACTION_REQUIRED"

DEFAULT_MODEL_REGISTRY_PATH = Path("research/ml_program/shadow/k55_shadow_registry_2026-05-05.json")

MODEL_SCHEMA_VERSION = "k55_shadow_linear_json_model_v1"
FORBIDDEN_FEATURE_KEY_PARTS = (
    "actual_r",
    "broker_actual",
    "hit_sl",
    "hit_tp",
    "label",
    "outcome",
    "path_",
    "pnl",
    "profit",
    "realized",
    "winner",
    "loser",
)

KNOWN_SYMBOLS = ("XAUUSD", "US30", "NAS100", "USDJPY", "GBPJPY", "GBPUSD", "XAGUSD")
KNOWN_FRAMEWORKS = ("ob_retest", "fvg_fill", "breaker_re_entry")
KNOWN_SESSIONS = ("london", "ny", "tokyo")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _rows_with_lines(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> list[tuple[int, dict[str, Any]]]:
    if not rows:
        return []
    first = rows[0]
    if isinstance(first, tuple):
        return [(int(line_no), row) for line_no, row in rows if isinstance(row, dict)]  # type: ignore[misc]
    return [(index, row) for index, row in enumerate(rows, start=1) if isinstance(row, dict)]  # type: ignore[arg-type]


def _jsonish(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _stable_hash(*parts: Any) -> str:
    return hashlib.sha256("|".join(_jsonish(part) for part in parts).encode("utf-8")).hexdigest()[:32]


def _clock(row: dict[str, Any]) -> datetime:
    return (
        parse_utc(row.get("backfilled_at_utc"))
        or parse_utc(row.get("created_at_utc"))
        or parse_utc(row.get("decision_time_utc"))
        or parse_utc(row.get("asof_cutoff_utc"))
        or parse_utc(row.get("asof_latest_candle_utc"))
        or parse_utc(row.get("timestamp_utc"))
        or parse_utc(row.get("ts"))
        or datetime.min.replace(tzinfo=timezone.utc)
    )


def _latest_by_candidate(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    return latest_evidence_by_candidate(_rows_with_lines(rows))


def _latest_global(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> dict[str, Any] | None:
    best: tuple[datetime, int, dict[str, Any]] | None = None
    for line_no, row in _rows_with_lines(rows):
        item = dict(row)
        item["_line_no"] = line_no
        key = (_clock(item), line_no)
        if best is None or key >= (best[0], best[1]):
            best = (key[0], key[1], item)
    return best[2] if best else None


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool_num(value: Any) -> float:
    return 1.0 if value is True else 0.0


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalized_symbol(value: Any) -> str:
    text = _safe_text(value).upper()
    if text in {"NDX100"}:
        return "NAS100"
    if text in {"US30_CASH"}:
        return "US30"
    return text


def _normalized_side(value: Any) -> str:
    text = _safe_text(value).upper()
    if text in {"BUY", "BULLISH"}:
        return "LONG"
    if text in {"SELL", "BEARISH"}:
        return "SHORT"
    return text


def _trade_params(candidate: dict[str, Any]) -> dict[str, Any]:
    params = candidate.get("trade_parameters")
    return params if isinstance(params, dict) else {}


def _planned_rr(candidate: dict[str, Any]) -> float | None:
    params = _trade_params(candidate)
    entry = _float_or_none(params.get("entry_price"))
    sl = _float_or_none(params.get("stop_loss"))
    tp = _float_or_none(params.get("take_profit_1"))
    side = _normalized_side(candidate.get("side") or params.get("direction"))
    if entry is None or sl is None or tp is None:
        return None
    risk = abs(entry - sl)
    if risk <= 0:
        return None
    if side == "LONG":
        return (tp - entry) / risk
    if side == "SHORT":
        return (entry - tp) / risk
    return abs(tp - entry) / risk


def _tf_from_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    summary = candidate.get("mso_summary") if isinstance(candidate.get("mso_summary"), dict) else {}
    timeframes = summary.get("timeframes") if isinstance(summary.get("timeframes"), dict) else {}
    return timeframes


def _tf_from_mso_join(mso_row: dict[str, Any] | None) -> dict[str, Any]:
    if not mso_row:
        return {}
    snapshot = mso_row.get("mso_snapshot") if isinstance(mso_row.get("mso_snapshot"), dict) else {}
    structural = snapshot.get("structural_state") if isinstance(snapshot.get("structural_state"), dict) else {}
    return structural


def _feature_value(target: dict[str, float], key: str, value: Any) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        target[key] = _bool_num(value)
        return
    number = _float_or_none(value)
    if number is None or math.isnan(number) or math.isinf(number):
        return
    target[key] = float(number)


def _one_hot(target: dict[str, float], prefix: str, value: Any, known_values: tuple[str, ...]) -> None:
    normalized = _safe_text(value)
    for item in known_values:
        target[f"{prefix}__{item}"] = 1.0 if normalized == item else 0.0


def _source_ref(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {"joined": False, "row_key": None, "source_line": None}
    return {
        "joined": True,
        "row_key": row.get("row_key"),
        "schema_version": row.get("schema_version"),
        "created_at_utc": row.get("created_at_utc"),
        "backfilled_at_utc": row.get("backfilled_at_utc"),
        "source_line": row.get("_line_no"),
    }


def target_registry_payload(*, generated_at_utc: str | None = None) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "generated_at_utc": generated,
        "promotion_verdict": PROMOTION_VERDICT,
        "target_version": TARGET_VERSION,
        "feature_bundle_version": FEATURE_BUNDLE_VERSION,
        "inference_version": INFERENCE_VERSION,
        "model_registry_path": str(DEFAULT_MODEL_REGISTRY_PATH),
        "target_contract": {
            "primary_label": "broker_actual_r",
            "primary_label_required_evidence_class": "ACCOUNT_HISTORY_REALIZED",
            "secondary_context_label": "synthetic_path_r",
            "secondary_context_claim_boundary": (
                "Synthetic path labels are allowed for context, QA, and pretraining research only. "
                "They are not account-realized labels and cannot validate promotion."
            ),
            "sample_eligibility_order": [
                "PRIMARY_ACCOUNT_HISTORY_REALIZED_R_LABEL",
                "SYNTHETIC_PATH_CONTEXT_ONLY",
                "UNLABELED_FORWARD_CANDIDATE",
            ],
        },
        "feature_bundle_contract": {
            "allowed_feature_timing": "decision_time_or_asof_only",
            "excluded_from_feature_vector": [
                "broker_actual_r",
                "actual_r",
                "path_label",
                "hit_tp1",
                "hit_sl",
                "pnl",
                "profit",
                "realized_r",
            ],
            "feature_groups": [
                "candidate_context",
                "mso_context",
                "decision_diagnostics_asof",
                "mechanical_asof_context",
                "regime_decay_asof",
                "orderflow_source_asof",
                "risk_policy_context",
            ],
        },
        "model_artifact_policy": {
            "default_status": "MODEL_ARTIFACT_MISSING_INFERENCE_DISABLED",
            "accepted_artifact_schema": MODEL_SCHEMA_VERSION,
            "minimum_checks": [
                "target_version_matches",
                "feature_bundle_version_matches",
                "weights_are_numeric",
                "threshold_is_numeric",
                "feature_keys_pass_no_leak_filter",
            ],
            "stale_k54_policy": (
                "Do not wire stale K54 v3/v4 artifacts directly. K54 v3/v4 failed global gates and "
                "their offline feature catalog is not replicated in live MSO. They remain audit context."
            ),
        },
        "claim_boundary": (
            "K55 shadow rows are research-only and read-only. They cannot change AI prompts, safety gates, "
            "risk, execution, order placement, or live promotion without a separate promotion dossier."
        ),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def _display_path(path: Path) -> str:
    """Return stable repo-relative paths when possible for reproducible rows."""
    try:
        resolved = path.resolve(strict=False)
        cwd = Path.cwd().resolve(strict=False)
        return resolved.relative_to(cwd).as_posix()
    except (OSError, ValueError):
        return path.as_posix() if not path.is_absolute() else str(path)


def load_model_artifact(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "status": "MODEL_ARTIFACT_MISSING_INFERENCE_DISABLED",
            "model": None,
            "model_path": None,
            "errors": [],
        }
    model_path = Path(path)
    model_path_display = _display_path(model_path)
    if not model_path.exists():
        return {
            "status": "MODEL_ARTIFACT_MISSING_INFERENCE_DISABLED",
            "model": None,
            "model_path": model_path_display,
            "errors": [],
        }
    errors: list[str] = []
    try:
        raw = json.loads(model_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "MODEL_ARTIFACT_INVALID_INFERENCE_DISABLED",
            "model": None,
            "model_path": model_path_display,
            "errors": [f"MODEL_JSON_UNREADABLE:{exc}"],
        }
    if not isinstance(raw, dict):
        errors.append("MODEL_JSON_NOT_OBJECT")
    if raw.get("schema_version") != MODEL_SCHEMA_VERSION:
        errors.append("MODEL_SCHEMA_VERSION_MISMATCH")
    if raw.get("target_version") != TARGET_VERSION:
        errors.append("TARGET_VERSION_MISMATCH")
    if raw.get("feature_bundle_version") != FEATURE_BUNDLE_VERSION:
        errors.append("FEATURE_BUNDLE_VERSION_MISMATCH")
    weights = raw.get("weights")
    if not isinstance(weights, dict):
        errors.append("WEIGHTS_NOT_OBJECT")
    else:
        for key, value in weights.items():
            if key != "bias" and feature_key_forbidden(str(key)):
                errors.append(f"FORBIDDEN_WEIGHT_KEY:{key}")
            if _float_or_none(value) is None:
                errors.append(f"NON_NUMERIC_WEIGHT:{key}")
    if _float_or_none(raw.get("threshold")) is None:
        errors.append("THRESHOLD_NOT_NUMERIC")
    if errors:
        return {
            "status": "MODEL_ARTIFACT_INVALID_INFERENCE_DISABLED",
            "model": None,
            "model_path": model_path_display,
            "errors": errors,
        }
    return {
        "status": "MODEL_ARTIFACT_READY",
        "model": raw,
        "model_path": model_path_display,
        "errors": [],
    }


def feature_key_forbidden(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in FORBIDDEN_FEATURE_KEY_PARTS)


def forbidden_feature_keys(feature_vector: dict[str, float]) -> list[str]:
    return sorted(key for key in feature_vector if feature_key_forbidden(key))


def _candidate_context(candidate: dict[str, Any]) -> dict[str, Any]:
    params = _trade_params(candidate)
    entry = _float_or_none(params.get("entry_price"))
    sl = _float_or_none(params.get("stop_loss"))
    tp = _float_or_none(params.get("take_profit_1"))
    return {
        "symbol": _normalized_symbol(candidate.get("symbol") or candidate.get("broker_symbol")),
        "broker_symbol": candidate.get("broker_symbol"),
        "side": _normalized_side(candidate.get("side") or params.get("direction")),
        "framework": candidate.get("framework"),
        "session": candidate.get("session") or candidate.get("kill_zone"),
        "analysis_decision": candidate.get("analysis_decision"),
        "trade_parameters": {
            "direction": _normalized_side(params.get("direction") or candidate.get("side")),
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit_1": tp,
            "risk_reward_ratio": _float_or_none(params.get("risk_reward_ratio")) or _planned_rr(candidate),
            "sl_buffer_applied": _float_or_none(params.get("sl_buffer_applied")),
        },
    }


def _mso_context(candidate: dict[str, Any], mso_row: dict[str, Any] | None) -> dict[str, Any]:
    timeframes = _tf_from_mso_join(mso_row) or _tf_from_candidate(candidate)
    tf_context: dict[str, Any] = {}
    for tf in ("D1", "H4", "H1", "M15"):
        raw = timeframes.get(tf) if isinstance(timeframes, dict) else None
        item = raw if isinstance(raw, dict) else {}
        tf_context[tf] = {
            "structure_direction": item.get("structure_direction"),
            "order_block_count": item.get("order_block_count"),
            "unmitigated_order_block_count": item.get("unmitigated_order_block_count"),
            "fvg_count": item.get("fvg_count"),
            "breaker_block_count": item.get("breaker_block_count"),
        }
    return {
        "join_status": "MSO_JOINED" if mso_row else "MSO_JOIN_MISSING_USING_CANDIDATE_SUMMARY" if timeframes else "MSO_CONTEXT_MISSING",
        "timeframes": tf_context,
        "source": _source_ref(mso_row),
    }


def _decision_diagnostics_features(decision_row: dict[str, Any] | None) -> dict[str, Any]:
    if not decision_row:
        return {"join_status": "DECISION_DIAGNOSTICS_MISSING"}
    candidate_features = decision_row.get("candidate_features_context") if isinstance(decision_row.get("candidate_features_context"), dict) else {}
    mso = candidate_features.get("mso") if isinstance(candidate_features.get("mso"), dict) else {}
    verification = decision_row.get("verification_context") if isinstance(decision_row.get("verification_context"), dict) else {}
    l2_summary = verification.get("l2_check_summary") if isinstance(verification.get("l2_check_summary"), dict) else {}
    return {
        "join_status": decision_row.get("decision_diagnostics_status"),
        "source": _source_ref(decision_row),
        "candidate_features_join_status": decision_row.get("candidate_features_join_status"),
        "candidate_feature_mso": {
            "m15_bvc_buy_fraction": _float_or_none(mso.get("m15_bvc_buy_fraction")),
            "m15_clv_current": _float_or_none(mso.get("m15_clv_current")),
            "m15_clv_avg_5": _float_or_none(mso.get("m15_clv_avg_5")),
            "m15_session_vol_ratio": _float_or_none(mso.get("m15_session_vol_ratio")),
            "m15_net_flow_5": _float_or_none(mso.get("m15_net_flow_5")),
            "h1_nearest_ob_distance_atr": _float_or_none(mso.get("h1_nearest_ob_distance_atr")),
            "pd_equilibrium_50": _float_or_none(mso.get("pd_equilibrium_50")),
        },
        "c_gate": candidate_features.get("c_gate_result") if isinstance(candidate_features.get("c_gate_result"), dict) else {},
        "verification_passed": decision_row.get("verification_passed"),
        "l2_check_summary": l2_summary,
        "verification_blocked_by": decision_row.get("verification_blocked_by"),
    }


def _mechanical_asof_features(mechanical_row: dict[str, Any] | None) -> dict[str, Any]:
    if not mechanical_row:
        return {"join_status": "MECHANICAL_CONTEXT_MISSING"}
    proximity = mechanical_row.get("proximity_context") if isinstance(mechanical_row.get("proximity_context"), dict) else {}
    liquidity = mechanical_row.get("liquidity_distance_context") if isinstance(mechanical_row.get("liquidity_distance_context"), dict) else {}
    pool_summary = liquidity.get("pool_summary") if isinstance(liquidity.get("pool_summary"), dict) else {}
    displacement = mechanical_row.get("displacement_context") if isinstance(mechanical_row.get("displacement_context"), dict) else {}
    structure = mechanical_row.get("structure_divergence_context") if isinstance(mechanical_row.get("structure_divergence_context"), dict) else {}
    timeframes = structure.get("timeframes") if isinstance(structure.get("timeframes"), dict) else {}
    return {
        "join_status": mechanical_row.get("mechanical_context_status"),
        "source": _source_ref(mechanical_row),
        "proximity": {
            "join_status": proximity.get("join_status"),
            "distance_atr_ratio": _float_or_none(proximity.get("distance_atr_ratio")),
            "h1_ob_count": _float_or_none(proximity.get("h1_ob_count")),
            "m15_ob_count": _float_or_none(proximity.get("m15_ob_count")),
            "relevant_ob_count": _float_or_none(proximity.get("relevant_ob_count")),
        },
        "liquidity_distance": {
            "join_status": liquidity.get("join_status"),
            "violating_pool_count": _float_or_none(pool_summary.get("violating_pool_count")),
            "nearest_pool_distance_to_sl": _float_or_none(pool_summary.get("nearest_pool_distance_to_sl")),
            "nearest_violating_distance_to_sl": _float_or_none(pool_summary.get("nearest_violating_distance_to_sl")),
        },
        "displacement": {
            "join_status": displacement.get("join_status"),
            "displacement_ratio": _float_or_none(displacement.get("displacement_ratio")),
            "body_to_atr": _float_or_none(displacement.get("body_to_atr")),
        },
        "structure_divergence": {
            "join_status": structure.get("join_status"),
            "h1_v2_score": _float_or_none((timeframes.get("H1") or {}).get("v2_score")) if isinstance(timeframes.get("H1"), dict) else None,
            "m15_v2_score": _float_or_none((timeframes.get("M15") or {}).get("v2_score")) if isinstance(timeframes.get("M15"), dict) else None,
        },
    }


def _regime_decay_features(regime_row: dict[str, Any] | None) -> dict[str, Any]:
    if not regime_row:
        return {"join_status": "REGIME_DECAY_CONTEXT_MISSING"}
    regime = regime_row.get("regime_context") if isinstance(regime_row.get("regime_context"), dict) else {}
    ob = regime_row.get("ob_continuation_context") if isinstance(regime_row.get("ob_continuation_context"), dict) else {}
    portfolio = ob.get("portfolio_scope_snapshot") if isinstance(ob.get("portfolio_scope_snapshot"), dict) else {}
    symbol_scope = ob.get("symbol_scope_snapshot") if isinstance(ob.get("symbol_scope_snapshot"), dict) else {}
    return {
        "join_status": regime_row.get("regime_decay_context_status"),
        "source": _source_ref(regime_row),
        "regime": regime.get("regime"),
        "regime_age_seconds": _float_or_none(regime.get("regime_age_seconds")),
        "portfolio_ob_continuation_rate_pct": _float_or_none(portfolio.get("rate_pct")),
        "symbol_ob_continuation_rate_pct": _float_or_none(symbol_scope.get("rate_pct")),
        "symbol_ob_insufficient_sample": symbol_scope.get("insufficient_sample"),
    }


def _risk_policy_features(s79_row: dict[str, Any] | None) -> dict[str, Any]:
    if not s79_row:
        return {"join_status": "S79_RISK_CONTEXT_MISSING"}
    context = s79_row.get("risk_context") if isinstance(s79_row.get("risk_context"), dict) else {}
    return {
        "join_status": s79_row.get("s79_side_aware_context_status"),
        "source": _source_ref(s79_row),
        "side_aware_enabled": context.get("side_aware_enabled"),
        "side_multiplier_for_row": _float_or_none(context.get("side_multiplier_for_row")),
        "symbol_risk_per_trade_pct": _float_or_none(context.get("symbol_risk_per_trade_pct")),
    }


def _orderflow_source_features(
    candidate: dict[str, Any],
    databento_row: dict[str, Any] | None,
    sierra_proxy_row: dict[str, Any] | None,
    sierra_depth_row: dict[str, Any] | None,
    orderflow_status_row: dict[str, Any] | None,
    sierra_status_row: dict[str, Any] | None,
) -> dict[str, Any]:
    external = candidate.get("external_confluence") if isinstance(candidate.get("external_confluence"), dict) else {}
    candidate_sierra = external.get("sierra") if isinstance(external.get("sierra"), dict) else {}
    candidate_databento = external.get("databento") if isinstance(external.get("databento"), dict) else {}
    depth_features = sierra_depth_row.get("features") if isinstance((sierra_depth_row or {}).get("features"), dict) else {}
    orderflow_readiness = orderflow_status_row.get("source_readiness") if isinstance((orderflow_status_row or {}).get("source_readiness"), dict) else {}
    databento_live = orderflow_readiness.get("databento_live") if isinstance(orderflow_readiness.get("databento_live"), dict) else {}
    sierra_depth = orderflow_readiness.get("sierra_depth") if isinstance(orderflow_readiness.get("sierra_depth"), dict) else {}
    return {
        "candidate_sierra_status": candidate_sierra.get("status"),
        "candidate_sierra_source_status": candidate_sierra.get("source_status"),
        "candidate_sierra_interpretation_status": candidate_sierra.get("interpretation_status"),
        "candidate_databento_status": candidate_databento.get("status"),
        "candidate_databento_trigger_status": (
            (candidate_databento.get("trigger_policy") or {}).get("trigger_status")
            if isinstance(candidate_databento.get("trigger_policy"), dict)
            else None
        ),
        "databento_trigger": {
            "join_status": "DATABENTO_TRIGGER_ROW_JOINED" if databento_row else "DATABENTO_TRIGGER_ROW_MISSING",
            "source": _source_ref(databento_row),
            "trigger_status": (databento_row or {}).get("trigger_status"),
            "decision": (databento_row or {}).get("decision"),
        },
        "sierra_proxy": {
            "join_status": "SIERRA_PROXY_ROW_JOINED" if sierra_proxy_row else "SIERRA_PROXY_ROW_MISSING",
            "source": _source_ref(sierra_proxy_row),
            "source_status": (sierra_proxy_row or {}).get("source_status"),
            "proxy_class": (sierra_proxy_row or {}).get("proxy_class"),
            "depth_interpretation_allowed": (sierra_proxy_row or {}).get("depth_interpretation_allowed"),
            "scid_interpretation_allowed": (sierra_proxy_row or {}).get("scid_interpretation_allowed"),
        },
        "sierra_depth_features": {
            "join_status": "SIERRA_DEPTH_FEATURES_JOINED" if sierra_depth_row else "SIERRA_DEPTH_FEATURES_MISSING",
            "source": _source_ref(sierra_depth_row),
            "feature_status": (sierra_depth_row or {}).get("feature_status"),
            "features_present": (sierra_depth_row or {}).get("features_present"),
            "depth_interpretation_allowed": (sierra_depth_row or {}).get("depth_interpretation_allowed"),
            "pre60_median_total_depth10": _float_or_none(depth_features.get("pre60_median_total_depth10")),
            "pre60_median_depth10_imbalance": _float_or_none(depth_features.get("pre60_median_depth10_imbalance")),
            "event15_median_total_depth10": _float_or_none(depth_features.get("event15_median_total_depth10")),
            "event15_thin_depth10_rate": _float_or_none(depth_features.get("event15_thin_depth10_rate")),
            "event15_median_depth10_imbalance": _float_or_none(depth_features.get("event15_median_depth10_imbalance")),
            "event15_median_near_far_ratio": _float_or_none(depth_features.get("event15_median_near_far_ratio")),
        },
        "orderflow_primitives": {
            "join_status": "ORDERFLOW_PRIMITIVES_STATUS_JOINED" if orderflow_status_row else "ORDERFLOW_PRIMITIVES_STATUS_MISSING",
            "source": _source_ref(orderflow_status_row),
            "status": (orderflow_status_row or {}).get("status"),
            "primitive_count": _float_or_none((orderflow_status_row or {}).get("primitive_count")),
            "blocker_count": len((orderflow_status_row or {}).get("blocker_codes") or []),
            "databento_live_status": databento_live.get("status"),
            "sierra_depth_candidate_rows": _float_or_none(sierra_depth.get("candidate_rows")),
            "sierra_depth_features_extracted": _float_or_none(sierra_depth.get("features_extracted")),
        },
        "sierra_depth_status": {
            "join_status": "SIERRA_DEPTH_STATUS_JOINED" if sierra_status_row else "SIERRA_DEPTH_STATUS_MISSING",
            "source": _source_ref(sierra_status_row),
            "status": (sierra_status_row or {}).get("status"),
        },
    }


def _label_contract(
    broker_row: dict[str, Any] | None,
    mechanical_row: dict[str, Any] | None,
    j46_row: dict[str, Any] | None,
    account_truth_row: dict[str, Any] | None,
) -> dict[str, Any]:
    broker_allowed = bool(broker_row and broker_row.get("actual_r_claim_allowed") is True and broker_row.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED")
    broker_r = _float_or_none((broker_row or {}).get("broker_actual_r"))
    path_context = mechanical_row.get("path_context") if isinstance((mechanical_row or {}).get("path_context"), dict) else {}
    synthetic_path_available = bool(j46_row and j46_row.get("synthetic_path_available") is True) or bool(path_context.get("path_label"))
    if broker_allowed:
        eligibility = "PRIMARY_ACCOUNT_HISTORY_REALIZED_R_LABEL"
    elif synthetic_path_available:
        eligibility = "SYNTHETIC_PATH_CONTEXT_ONLY"
    else:
        eligibility = "UNLABELED_FORWARD_CANDIDATE"
    return {
        "target_version": TARGET_VERSION,
        "sample_eligibility": eligibility,
        "primary_label_status": "ACCOUNT_HISTORY_REALIZED_R_AVAILABLE" if broker_allowed else "ACCOUNT_HISTORY_REALIZED_R_MISSING",
        "primary_label_r": broker_r if broker_allowed else None,
        "primary_label_source": _source_ref(broker_row),
        "synthetic_path_context_status": "SYNTHETIC_PATH_CONTEXT_AVAILABLE" if synthetic_path_available else "SYNTHETIC_PATH_CONTEXT_MISSING",
        "synthetic_path_label": path_context.get("path_label"),
        "synthetic_path_touched_entry": path_context.get("touched_entry"),
        "synthetic_path_hit_tp1": path_context.get("hit_tp1"),
        "synthetic_path_hit_sl": path_context.get("hit_sl"),
        "j46_context_status": (j46_row or {}).get("j46_j49_exit_comparator_status"),
        "account_truth_status": (account_truth_row or {}).get("account_truth_status"),
        "actual_r_claim_allowed": broker_allowed,
        "no_leak_boundary": "labels are stored outside feature_vector and must not be read by live inference features",
    }


def _flatten_feature_vector(groups: dict[str, Any]) -> dict[str, float]:
    vector: dict[str, float] = {}
    candidate = groups.get("candidate_context") if isinstance(groups.get("candidate_context"), dict) else {}
    params = candidate.get("trade_parameters") if isinstance(candidate.get("trade_parameters"), dict) else {}
    symbol = _normalized_symbol(candidate.get("symbol"))
    framework = _safe_text(candidate.get("framework"))
    session = _safe_text(candidate.get("session"))
    side = _normalized_side(candidate.get("side"))
    _one_hot(vector, "symbol", symbol, KNOWN_SYMBOLS)
    _one_hot(vector, "framework", framework, KNOWN_FRAMEWORKS)
    _one_hot(vector, "session", session, KNOWN_SESSIONS)
    vector["side__LONG"] = 1.0 if side == "LONG" else 0.0
    vector["side__SHORT"] = 1.0 if side == "SHORT" else 0.0
    _feature_value(vector, "planned_risk_reward_ratio", params.get("risk_reward_ratio"))
    _feature_value(vector, "sl_buffer_applied", params.get("sl_buffer_applied"))

    mso = groups.get("mso_context") if isinstance(groups.get("mso_context"), dict) else {}
    timeframes = mso.get("timeframes") if isinstance(mso.get("timeframes"), dict) else {}
    for tf in ("D1", "H4", "H1", "M15"):
        item = timeframes.get(tf) if isinstance(timeframes.get(tf), dict) else {}
        prefix = f"mso_{tf.lower()}"
        _feature_value(vector, f"{prefix}_order_block_count", item.get("order_block_count"))
        _feature_value(vector, f"{prefix}_unmitigated_order_block_count", item.get("unmitigated_order_block_count"))
        _feature_value(vector, f"{prefix}_fvg_count", item.get("fvg_count"))
        _feature_value(vector, f"{prefix}_breaker_block_count", item.get("breaker_block_count"))

    decision = groups.get("decision_diagnostics_asof") if isinstance(groups.get("decision_diagnostics_asof"), dict) else {}
    candidate_mso = decision.get("candidate_feature_mso") if isinstance(decision.get("candidate_feature_mso"), dict) else {}
    for key, value in candidate_mso.items():
        _feature_value(vector, f"decision_{key}", value)
    c_gate = decision.get("c_gate") if isinstance(decision.get("c_gate"), dict) else {}
    _feature_value(vector, "decision_c1_h1_bias_present", c_gate.get("c1_h1_bias_present"))
    _feature_value(vector, "decision_c2_m15_choch_detected", c_gate.get("c2_m15_choch_detected"))
    _feature_value(vector, "decision_c3_direction_matches", c_gate.get("c3_direction_matches"))
    _feature_value(vector, "decision_verification_passed", decision.get("verification_passed"))
    l2 = decision.get("l2_check_summary") if isinstance(decision.get("l2_check_summary"), dict) else {}
    vector["decision_l2_pass_count"] = float(sum(1 for value in l2.values() if value == "PASS"))
    vector["decision_l2_fail_count"] = float(sum(1 for value in l2.values() if value == "FAIL"))
    vector["decision_l2_skip_count"] = float(sum(1 for value in l2.values() if value == "SKIP"))

    mechanical = groups.get("mechanical_asof_context") if isinstance(groups.get("mechanical_asof_context"), dict) else {}
    proximity = mechanical.get("proximity") if isinstance(mechanical.get("proximity"), dict) else {}
    liquidity = mechanical.get("liquidity_distance") if isinstance(mechanical.get("liquidity_distance"), dict) else {}
    displacement = mechanical.get("displacement") if isinstance(mechanical.get("displacement"), dict) else {}
    structure = mechanical.get("structure_divergence") if isinstance(mechanical.get("structure_divergence"), dict) else {}
    for key, value in proximity.items():
        if key != "join_status":
            _feature_value(vector, f"mechanical_proximity_{key}", value)
    for key, value in liquidity.items():
        if key != "join_status":
            _feature_value(vector, f"mechanical_liquidity_{key}", value)
    for key, value in displacement.items():
        if key != "join_status":
            _feature_value(vector, f"mechanical_displacement_{key}", value)
    for key, value in structure.items():
        if key != "join_status":
            _feature_value(vector, f"mechanical_structure_{key}", value)

    regime = groups.get("regime_decay_asof") if isinstance(groups.get("regime_decay_asof"), dict) else {}
    _feature_value(vector, "regime_age_seconds", regime.get("regime_age_seconds"))
    _feature_value(vector, "regime_portfolio_ob_continuation_rate_pct", regime.get("portfolio_ob_continuation_rate_pct"))
    _feature_value(vector, "regime_symbol_ob_continuation_rate_pct", regime.get("symbol_ob_continuation_rate_pct"))
    _feature_value(vector, "regime_symbol_ob_insufficient_sample", regime.get("symbol_ob_insufficient_sample"))

    risk = groups.get("risk_policy_context") if isinstance(groups.get("risk_policy_context"), dict) else {}
    _feature_value(vector, "risk_side_aware_enabled", risk.get("side_aware_enabled"))
    _feature_value(vector, "risk_side_multiplier_for_row", risk.get("side_multiplier_for_row"))
    _feature_value(vector, "risk_symbol_risk_per_trade_pct", risk.get("symbol_risk_per_trade_pct"))

    orderflow = groups.get("orderflow_source_asof") if isinstance(groups.get("orderflow_source_asof"), dict) else {}
    sierra_proxy = orderflow.get("sierra_proxy") if isinstance(orderflow.get("sierra_proxy"), dict) else {}
    sierra_depth = orderflow.get("sierra_depth_features") if isinstance(orderflow.get("sierra_depth_features"), dict) else {}
    primitives = orderflow.get("orderflow_primitives") if isinstance(orderflow.get("orderflow_primitives"), dict) else {}
    _feature_value(vector, "orderflow_sierra_depth_interpretation_allowed", sierra_proxy.get("depth_interpretation_allowed"))
    _feature_value(vector, "orderflow_sierra_scid_interpretation_allowed", sierra_proxy.get("scid_interpretation_allowed"))
    _feature_value(vector, "orderflow_sierra_features_present", sierra_depth.get("features_present"))
    for key in (
        "pre60_median_total_depth10",
        "pre60_median_depth10_imbalance",
        "event15_median_total_depth10",
        "event15_thin_depth10_rate",
        "event15_median_depth10_imbalance",
        "event15_median_near_far_ratio",
    ):
        _feature_value(vector, f"orderflow_sierra_{key}", sierra_depth.get(key))
    _feature_value(vector, "orderflow_primitive_count", primitives.get("primitive_count"))
    _feature_value(vector, "orderflow_blocker_count", primitives.get("blocker_count"))
    _feature_value(vector, "orderflow_sierra_depth_candidate_rows", primitives.get("sierra_depth_candidate_rows"))
    _feature_value(vector, "orderflow_sierra_depth_features_extracted", primitives.get("sierra_depth_features_extracted"))

    return vector


def _score_model(model: dict[str, Any], feature_vector: dict[str, float]) -> dict[str, Any]:
    weights = model.get("weights") if isinstance(model.get("weights"), dict) else {}
    threshold = _float_or_none(model.get("threshold")) or 0.5
    raw = _float_or_none(weights.get("bias")) or 0.0
    contributions: dict[str, float] = {}
    for key, value in feature_vector.items():
        weight = _float_or_none(weights.get(key))
        if weight is None:
            continue
        contribution = weight * value
        raw += contribution
        contributions[key] = contribution
    score = 1.0 / (1.0 + math.exp(-raw))
    return {
        "ml_score": score,
        "ml_raw_score": raw,
        "ml_threshold": threshold,
        "ml_signal": "ML_SHADOW_WOULD_TAKE" if score >= threshold else "ML_SHADOW_WOULD_SKIP",
        "model_contribution_count": len(contributions),
        "model_top_contributions": dict(sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)[:20]),
    }


def build_ml_shadow_rows(
    candidate_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    *,
    mso_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    account_truth_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    broker_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    j46_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    s79_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    regime_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    decision_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    mechanical_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    databento_trigger_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    sierra_proxy_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    sierra_depth_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    orderflow_status_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    sierra_status_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    model_artifact_path: str | Path | None = None,
    generated_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    generated = generated_at_utc or utc_now_iso()
    model_state = load_model_artifact(model_artifact_path)
    model = model_state.get("model") if isinstance(model_state.get("model"), dict) else None
    mso_by_candidate = _latest_by_candidate(mso_rows)
    account_by_candidate = _latest_by_candidate(account_truth_rows)
    broker_by_candidate = _latest_by_candidate(broker_rows)
    j46_by_candidate = _latest_by_candidate(j46_rows)
    s79_by_candidate = _latest_by_candidate(s79_rows)
    regime_by_candidate = _latest_by_candidate(regime_rows)
    decision_by_candidate = _latest_by_candidate(decision_rows)
    mechanical_by_candidate = _latest_by_candidate(mechanical_rows)
    databento_by_candidate = _latest_by_candidate(databento_trigger_rows)
    sierra_proxy_by_candidate = _latest_by_candidate(sierra_proxy_rows)
    sierra_depth_by_candidate = _latest_by_candidate(sierra_depth_rows)
    orderflow_status = _latest_global(orderflow_status_rows)
    sierra_status = _latest_global(sierra_status_rows)

    rows: list[dict[str, Any]] = []
    for candidate_line, candidate in _rows_with_lines(candidate_rows):
        candidate_id = str(candidate.get("candidate_id") or "").strip()
        if not candidate_id:
            continue
        mso_row = mso_by_candidate.get(candidate_id)
        account_row = account_by_candidate.get(candidate_id)
        broker_row = broker_by_candidate.get(candidate_id)
        j46_row = j46_by_candidate.get(candidate_id)
        s79_row = s79_by_candidate.get(candidate_id)
        regime_row = regime_by_candidate.get(candidate_id)
        decision_row = decision_by_candidate.get(candidate_id)
        mechanical_row = mechanical_by_candidate.get(candidate_id)
        databento_row = databento_by_candidate.get(candidate_id)
        sierra_proxy_row = sierra_proxy_by_candidate.get(candidate_id)
        sierra_depth_row = sierra_depth_by_candidate.get(candidate_id)

        feature_groups = {
            "candidate_context": _candidate_context(candidate),
            "mso_context": _mso_context(candidate, mso_row),
            "decision_diagnostics_asof": _decision_diagnostics_features(decision_row),
            "mechanical_asof_context": _mechanical_asof_features(mechanical_row),
            "regime_decay_asof": _regime_decay_features(regime_row),
            "orderflow_source_asof": _orderflow_source_features(
                candidate,
                databento_row,
                sierra_proxy_row,
                sierra_depth_row,
                orderflow_status,
                sierra_status,
            ),
            "risk_policy_context": _risk_policy_features(s79_row),
        }
        feature_vector = _flatten_feature_vector(feature_groups)
        forbidden = forbidden_feature_keys(feature_vector)
        label = _label_contract(broker_row, mechanical_row, j46_row, account_row)

        source_refs = {
            "candidate_line": candidate_line,
            "mso": _source_ref(mso_row),
            "account_truth": _source_ref(account_row),
            "broker_actual_r_audit": _source_ref(broker_row),
            "j46_j49": _source_ref(j46_row),
            "s79": _source_ref(s79_row),
            "regime_decay": _source_ref(regime_row),
            "decision_diagnostics": _source_ref(decision_row),
            "mechanical_context": _source_ref(mechanical_row),
            "databento_trigger": _source_ref(databento_row),
            "sierra_proxy": _source_ref(sierra_proxy_row),
            "sierra_depth": _source_ref(sierra_depth_row),
            "orderflow_status": _source_ref(orderflow_status),
            "sierra_status": _source_ref(sierra_status),
        }
        missing_sources = [
            name
            for name, ref in source_refs.items()
            if isinstance(ref, dict) and not ref.get("joined")
        ]
        feature_bundle_complete = all(
            name not in missing_sources
            for name in ("mso", "decision_diagnostics", "mechanical_context")
        )
        documented_limitations: list[str] = []
        if missing_sources:
            documented_limitations.append("OPTIONAL_OR_RECOVERABLE_SOURCE_ROWS_MISSING")
        if model_state["status"] == "MODEL_ARTIFACT_MISSING_INFERENCE_DISABLED":
            documented_limitations.append("MODEL_ARTIFACT_MISSING_INFERENCE_DISABLED")
        action_required: list[str] = []
        if model_state["status"] == "MODEL_ARTIFACT_INVALID_INFERENCE_DISABLED":
            action_required.extend(model_state.get("errors") or ["MODEL_ARTIFACT_INVALID"])
        if forbidden:
            action_required.append("FEATURE_VECTOR_FORBIDDEN_POST_OUTCOME_KEY")

        prediction = {
            "inference_enabled": False,
            "prediction_status": "INFERENCE_DISABLED",
            "model_version": None,
            "model_artifact_status": model_state["status"],
            "model_artifact_path": model_state.get("model_path"),
            "ml_score": None,
            "ml_raw_score": None,
            "ml_threshold": None,
            "ml_signal": None,
            "model_contribution_count": 0,
            "model_top_contributions": {},
        }
        if model is not None and not forbidden:
            scored = _score_model(model, feature_vector)
            prediction.update(
                {
                    "inference_enabled": True,
                    "prediction_status": PREDICTION_COMPUTED,
                    "model_version": model.get("model_version"),
                    "model_artifact_status": model_state["status"],
                    **scored,
                }
            )

        if action_required:
            status = ACTION_REQUIRED
        elif prediction["inference_enabled"]:
            status = PREDICTION_COMPUTED
        elif feature_bundle_complete:
            status = FEATURE_READY_MODEL_PENDING
        else:
            status = FEATURE_PARTIAL_MODEL_PENDING
        if model_state["status"] == "MODEL_ARTIFACT_INVALID_INFERENCE_DISABLED":
            status = MODEL_INVALID

        source_dependency_signature = _stable_hash(
            SCHEMA_VERSION,
            CLASSIFIER_VERSION,
            TARGET_VERSION,
            FEATURE_BUNDLE_VERSION,
            INFERENCE_VERSION,
            candidate_id,
            candidate.get("decision_time_utc"),
            candidate.get("created_at_utc"),
            candidate.get("symbol"),
            candidate.get("broker_symbol"),
            candidate.get("side"),
            candidate.get("framework"),
            feature_vector,
            source_refs,
            prediction.get("model_version") or "NO_MODEL",
            model_state["status"],
        )
        row = {
            "schema_version": SCHEMA_VERSION,
            "row_key": _stable_hash("ml_shadow_prediction", source_dependency_signature),
            "source_dependency_signature": source_dependency_signature,
            "created_at_utc": generated,
            "backfilled_at_utc": generated,
            "classifier_version": CLASSIFIER_VERSION,
            "lto_id": "LTO-023",
            "follow_id": "LIVE-FOLLOW-020",
            "row_type": "candidate_ml_shadow_prediction",
            "promotion_verdict": PROMOTION_VERDICT,
            "evidence_class": "ML_SHADOW_FEATURE_BUNDLE_STATUS",
            "ml_shadow_status": status,
            "target_version": TARGET_VERSION,
            "feature_bundle_version": FEATURE_BUNDLE_VERSION,
            "inference_version": INFERENCE_VERSION,
            "candidate_id": candidate_id,
            "trade_id": candidate.get("trade_id"),
            "symbol": _normalized_symbol(candidate.get("symbol") or candidate.get("broker_symbol")),
            "broker_symbol": candidate.get("broker_symbol"),
            "side": _normalized_side(candidate.get("side") or _trade_params(candidate).get("direction")),
            "framework": candidate.get("framework"),
            "session": candidate.get("session") or candidate.get("kill_zone"),
            "decision_time_utc": candidate.get("decision_time_utc"),
            "asof_latest_candle_utc": candidate.get("asof_cutoff_utc") or candidate.get("decision_time_utc"),
            "analysis_decision": candidate.get("analysis_decision"),
            "trade_parameters": _candidate_context(candidate)["trade_parameters"],
            "prediction": prediction,
            "feature_bundle_status": "FEATURE_BUNDLE_COMPLETE" if feature_bundle_complete else "FEATURE_BUNDLE_PARTIAL_DOCUMENTED",
            "feature_availability": {
                "feature_count": len(feature_vector),
                "missing_sources": missing_sources,
                "source_refs": source_refs,
            },
            "source_freshness": {
                "candidate_created_at_utc": candidate.get("created_at_utc"),
                "decision_time_utc": candidate.get("decision_time_utc"),
                "source_rows_joined": len(source_refs) - len(missing_sources),
                "source_rows_missing": len(missing_sources),
            },
            "feature_groups": feature_groups,
            "feature_vector": feature_vector,
            "forbidden_feature_keys": forbidden,
            "label_contract": label,
            "ml_label_eligibility": label["sample_eligibility"],
            "no_leak_status": "K55_FEATURE_VECTOR_ASOF_ONLY_LABELS_SEPARATE",
            "claim_boundary": (
                "This row is read-only K55 shadow substrate. Prediction fields are observational only and "
                "cannot alter live AI decisions, prompts, safety gates, risk, execution, or order placement."
            ),
            "documented_limitation_codes": documented_limitations,
            "action_required_codes": action_required,
            "no_ai_calls": True,
            "no_canary_required": True,
            "no_execution": True,
            "ai_calls": 0,
            "canary_calls": 0,
            "order_calls": 0,
            "paid_data_calls": 0,
            "paid_fetch_attempted": False,
        }
        rows.append(row)
    return rows


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("ml_shadow_status") or "UNKNOWN") for row in rows)
    model_status_counts = Counter(str((row.get("prediction") or {}).get("model_artifact_status") or "UNKNOWN") for row in rows)
    eligibility_counts = Counter(str(row.get("ml_label_eligibility") or "UNKNOWN") for row in rows)
    symbol_counts = Counter(str(row.get("symbol") or "UNKNOWN") for row in rows)
    feature_counts = [len(row.get("feature_vector") or {}) for row in rows]
    missing_source_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    limitation_counts: Counter[str] = Counter()
    for row in rows:
        availability = row.get("feature_availability") if isinstance(row.get("feature_availability"), dict) else {}
        for source in availability.get("missing_sources") or []:
            missing_source_counts[str(source)] += 1
        for code in row.get("action_required_codes") or []:
            action_counts[str(code)] += 1
        for code in row.get("documented_limitation_codes") or []:
            limitation_counts[str(code)] += 1
    return {
        "status_counts": dict(status_counts),
        "model_artifact_status_counts": dict(model_status_counts),
        "ml_label_eligibility_counts": dict(eligibility_counts),
        "symbol_counts": dict(symbol_counts),
        "missing_source_counts": dict(missing_source_counts),
        "action_required_code_counts": dict(action_counts),
        "documented_limitation_code_counts": dict(limitation_counts),
        "prediction_computed_rows": status_counts.get(PREDICTION_COMPUTED, 0),
        "inference_enabled_rows": sum(1 for row in rows if (row.get("prediction") or {}).get("inference_enabled") is True),
        "feature_count_min": min(feature_counts) if feature_counts else 0,
        "feature_count_max": max(feature_counts) if feature_counts else 0,
        "feature_count_avg": round(sum(feature_counts) / len(feature_counts), 4) if feature_counts else 0.0,
    }


def report_payload(
    rows: list[dict[str, Any]],
    appended_rows: list[dict[str, Any]],
    output_path: str | Path,
    *,
    source_counts: dict[str, int],
    model_artifact_path: str | Path | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    rolling = build_rolling_status(rows)
    action_rows = [
        {
            "row_key": row.get("row_key"),
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "decision_time_utc": row.get("decision_time_utc"),
            "action_required_codes": row.get("action_required_codes") or [],
        }
        for row in rows
        if row.get("action_required_codes")
    ]
    model_state = load_model_artifact(model_artifact_path)
    status = "ACTION_REQUIRED" if action_rows or model_state["status"] == "MODEL_ARTIFACT_INVALID_INFERENCE_DISABLED" else "OK_K55_ML_SHADOW_FEATURE_BUNDLE_REGISTERED"
    return {
        "schema_version": "lto023_k55_ml_shadow_report_v1",
        "generated_at_utc": generated,
        "promotion_verdict": PROMOTION_VERDICT,
        "status": status,
        "status_log_path": str(output_path),
        "status_log_schema": SCHEMA_VERSION,
        "target_registry": target_registry_payload(generated_at_utc=generated),
        "counts": {
            "rows_computed": len(rows),
            "status_rows_appended_this_run": len(appended_rows),
            "prediction_computed_rows": rolling["prediction_computed_rows"],
            "inference_enabled_rows": rolling["inference_enabled_rows"],
            "action_required": len(action_rows),
        },
        "source_counts": source_counts,
        "rolling_status": rolling,
        "model_artifact": {
            "path": str(model_artifact_path) if model_artifact_path else None,
            "status": model_state["status"],
            "errors": model_state.get("errors") or [],
        },
        "action_required_examples": action_rows[:25],
        "claim_boundary": (
            "LTO-023 refreshes the K55 target and feature bundle and implements a read-only scoring path. "
            "Rows remain shadow-only. Missing production model artifact is a documented blocker, not a "
            "reason to reuse stale K54 v3/v4 artifacts blindly."
        ),
        "ml_goal_contribution": (
            "This lane turns the LTO-001..020 capture work, Sierra/Databento/orderflow source status, "
            "decision diagnostics, mechanical context, regime decay, and label-quality metadata into one "
            "K55-ready feature bundle with a gated inference interface."
        ),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def write_registry_markdown(payload: dict[str, Any], path: str | Path) -> None:
    lines = [
        "# K55 Target And Feature Registry - 2026-05-05",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Generated:** `{payload['generated_at_utc']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        f"**Target version:** `{payload['target_version']}`",
        f"**Feature bundle version:** `{payload['feature_bundle_version']}`",
        f"**Inference version:** `{payload['inference_version']}`",
        "",
        "## Target Contract",
        "",
        f"`{payload['target_contract']}`",
        "",
        "## Feature Bundle Contract",
        "",
        f"`{payload['feature_bundle_contract']}`",
        "",
        "## Model Artifact Policy",
        "",
        f"`{payload['model_artifact_policy']}`",
        "",
        "## Boundary",
        "",
        payload["claim_boundary"],
    ]
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report_markdown(report: dict[str, Any], path: str | Path) -> None:
    counts = report["counts"]
    rolling = report["rolling_status"]
    lines = [
        "# LTO-023 K55 ML Shadow - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- Rows computed: `{counts['rows_computed']}`",
        f"- Rows appended this run: `{counts['status_rows_appended_this_run']}`",
        f"- Prediction-computed rows: `{counts['prediction_computed_rows']}`",
        f"- Inference-enabled rows: `{counts['inference_enabled_rows']}`",
        f"- Action required: `{counts['action_required']}`",
        "",
        "## Model Artifact",
        "",
        f"`{report['model_artifact']}`",
        "",
        "## Source Counts",
        "",
        f"`{report['source_counts']}`",
        "",
        "## Rolling Status",
        "",
        f"- Status counts: `{rolling['status_counts']}`",
        f"- Model artifact status counts: `{rolling['model_artifact_status_counts']}`",
        f"- Label eligibility counts: `{rolling['ml_label_eligibility_counts']}`",
        f"- Missing source counts: `{rolling['missing_source_counts']}`",
        f"- Feature count min/max/avg: `{rolling['feature_count_min']}` / `{rolling['feature_count_max']}` / `{rolling['feature_count_avg']}`",
        f"- Documented limitations: `{rolling['documented_limitation_code_counts']}`",
        f"- Action-required codes: `{rolling['action_required_code_counts']}`",
        "",
        "## Target Registry",
        "",
        f"- Target version: `{report['target_registry']['target_version']}`",
        f"- Feature bundle version: `{report['target_registry']['feature_bundle_version']}`",
        f"- Inference version: `{report['target_registry']['inference_version']}`",
        "",
        "## Boundary",
        "",
        report["claim_boundary"],
        "",
        "## ML Goal Contribution",
        "",
        report["ml_goal_contribution"],
        "",
        "## Safety Counters",
        "",
        f"- ai_calls: `{report['ai_calls']}`",
        f"- canary_calls: `{report['canary_calls']}`",
        f"- order_calls: `{report['order_calls']}`",
        f"- paid_data_calls: `{report['paid_data_calls']}`",
    ]
    if report["action_required_examples"]:
        lines.extend(["", "## Action Required Examples", "", "```json", json.dumps(report["action_required_examples"], indent=2, sort_keys=True), "```"])
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
