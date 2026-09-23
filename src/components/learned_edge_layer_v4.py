"""Learned Edge Layer V4 — pure-Python frozen-artifact scorer.

Deterministic runtime scorer for the learned mechanical edge model. Loads a
frozen JSON artifact (``ultimate_learned_edge_layer_v1`` schema, produced
offline by ``src/research_infra/learned_edge_trainer.py``) and scores one
candidate's predecision feature mapping into:

- ``fill_probability``        calibrated P(fill)
- ``probability``             calibrated P(target-before-stop | fill)
- ``expected_net_r``          P(fill) * E[net_r | fill]

No sklearn / numpy / file writes / broker calls at runtime — inference is
plain arithmetic over the artifact payload, so the trainer can use this exact
module for out-of-fold parity checks (train/runtime parity by construction).

Fail-closed: scoring refuses (returns ``status != "scored"``) on schema or
generator-sha mismatch, stale artifact, or missing required features. The
caller (selector_v4 learned mode) must fall back to static floors with an
explicit reason — never silently.
"""

from __future__ import annotations

from src.components.executable_value_semantics import (
    EXPECTED_VALUE_ALREADY_FILL_ADJUSTED,
)

import json
import math
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ARTIFACT_SCHEMA_VERSION = "ultimate_learned_edge_layer_v1"
EVIDENCE_CLASS = "production_code_integration_frozen_learned_artifact_inference"

REQUIRED_HEADS = ("fill", "outcome")

# Runtime mirror of learned_edge_dataset_builder.ASSET_CLASS_BY_SYMBOL. Kept
# local so the runtime scorer stays research-infra-free; parity is enforced by
# tests/test_selector_v4_learned_mode.py against the builder map.
ASSET_CLASS_BY_SYMBOL = {
    "XAUUSD": "metals",
    "XAGUSD": "metals",
    "BTCUSD": "crypto",
    "ETHUSD": "crypto",
    "GER40": "index",
    "JP225": "index",
    "NAS100": "index",
    "SPX500": "index",
    "UK100": "index",
    "US30_cash": "index",
    "UKOIL_cash": "energy",
    "USOIL_cash": "energy",
    "AUDJPY": "jpy_fx",
    "CHFJPY": "jpy_fx",
    "EURJPY": "jpy_fx",
    "GBPJPY": "jpy_fx",
    "USDJPY": "jpy_fx",
    "AUDUSD": "fx",
    "EURGBP": "fx",
    "EURUSD": "fx",
    "GBPUSD": "fx",
    "NZDUSD": "fx",
    "USDCAD": "fx",
    "USDCHF": "fx",
    # 2026-06-11 universe expansion (22 symbols; mirror in builder/scorer).
    "XAUEUR": "metals",
    "XAUAUD": "metals",
    "XAGAUD": "metals",
    "XAGEUR": "metals",
    "XCUUSD": "metals",
    "AUS200_cash": "index",
    "EU50_cash": "index",
    "FRA40_cash": "index",
    "US2000_cash": "index",
    "N25_cash": "index",
    "DXY_cash": "index",
    "NATGAS_cash": "energy",
    "HEATOIL_c": "energy",
    "COTTON_c": "agri",
    "CORN_c": "agri",
    "USDSGD": "fx",
    "USDCNH": "fx",
    "LTCUSD": "crypto",
    "DOTUSD": "crypto",
    "ADAUSD": "crypto",
    "DASHUSD": "crypto",
    "XTZUSD": "crypto",
}


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def _clip01(value: float, *, eps: float = 1e-6) -> float:
    return min(1.0 - eps, max(eps, value))


def load_learned_edge_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("learned edge artifact must be a JSON object")
    return payload


_ARTIFACT_CACHE: dict[tuple[str, int, int], dict[str, Any]] = {}


def load_learned_edge_artifact_cached(path: str | Path) -> dict[str, Any]:
    """Load a frozen artifact through a module-level cache.

    Cache key is ``(resolved path, mtime_ns, size)`` so a rewritten artifact
    file is re-read while repeated scoring of the same frozen file pays the
    JSON parse cost once. Missing/invalid paths raise (fail-closed; the caller
    must record an explicit fallback, never a silent one).
    """

    resolved = Path(path).resolve(strict=True)
    stat = resolved.stat()
    key = (str(resolved), stat.st_mtime_ns, stat.st_size)
    cached = _ARTIFACT_CACHE.get(key)
    if cached is not None:
        return cached
    artifact = load_learned_edge_artifact(resolved)
    for stale_key in [k for k in _ARTIFACT_CACHE if k[0] == key[0]]:
        del _ARTIFACT_CACHE[stale_key]
    _ARTIFACT_CACHE[key] = artifact
    return artifact


def _as_float(value: Any) -> float | None:
    """Builder-parity numeric coercion (bool -> None; non-finite -> None)."""

    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        result = float(value)
        return result if math.isfinite(result) else None
    if isinstance(value, str):
        try:
            result = float(value)
        except ValueError:
            return None
        return result if math.isfinite(result) else None
    return None


def _runtime_selected_thesis(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    probability_packet = packet.get("probability_packet")
    if isinstance(probability_packet, Mapping):
        thesis = probability_packet.get("selected_thesis")
        if isinstance(thesis, Mapping):
            return thesis
    return {}


def _runtime_day_of_week(packet: Mapping[str, Any]) -> str | None:
    for token in (
        str(packet.get("trading_day") or ""),
        str(packet.get("decision_time_utc") or "")[:10],
    ):
        if not token:
            continue
        try:
            return datetime.strptime(token, "%Y-%m-%d").strftime("%a").lower()
        except ValueError:
            continue
    return None


def extract_runtime_features(candidate_packet: Mapping[str, Any]) -> dict[str, Any]:
    """Build the predecision ``f_*`` feature mapping from a runtime packet.

    Mirrors ``learned_edge_dataset_builder.extract_features`` name-for-name
    (train/runtime feature parity is pinned by test) while accepting the union
    of candidate-microscope and selector candidate-packet field shapes:
    top-level candidate fields plus ``probability_packet.selected_thesis``.
    ``f_n_competing_in_group`` comes from ``n_competing_in_group`` when present
    (else 1); day-of-week falls back from ``trading_day`` to the
    ``decision_time_utc`` date. Predecision-only by construction: no outcome,
    fill-status, or hindsight field is read.
    """

    packet: Mapping[str, Any] = (
        candidate_packet if isinstance(candidate_packet, Mapping) else {}
    )
    thesis = _runtime_selected_thesis(packet)
    symbol = str(packet.get("symbol") or "")

    entry = _as_float(packet.get("entry_price"))
    reference = _as_float(packet.get("entry_reference"))
    stop = _as_float(packet.get("stop_loss"))
    limit_offset_r: float | None = None
    if entry is not None and stop is not None and reference is not None:
        risk_distance = abs(entry - stop)
        if risk_distance > 0:
            limit_offset_r = abs(reference - entry) / risk_distance
    stop_distance_rel: float | None = None
    if entry is not None and stop is not None and entry != 0:
        stop_distance_rel = abs(entry - stop) / abs(entry)

    n_competing = _as_float(packet.get("n_competing_in_group"))
    if n_competing is None or n_competing <= 0:
        n_competing = 1.0

    result = {
        "f_origin_family": packet.get("origin_family")
        or packet.get("candidate_origin_family"),
        "f_framework": packet.get("framework"),
        "f_symbol": symbol or None,
        "f_asset_class": ASSET_CLASS_BY_SYMBOL.get(symbol),
        "f_side": (str(packet.get("side") or "").upper() or None),
        "f_route_session": packet.get("route_session"),
        "f_session_bucket": packet.get("session_bucket"),
        "f_utc_hour_bucket": packet.get("utc_hour_bucket"),
        "f_kill_zone": packet.get("kill_zone"),
        "f_day_of_week": _runtime_day_of_week(packet),
        "f_dynamic_geometry_policy": packet.get("dynamic_geometry_policy"),
        "f_dynamic_execution_policy_id": packet.get("dynamic_execution_policy_id"),
        "f_disagreement_state": thesis.get("disagreement_state"),
        "f_heuristic_probability": _as_float(packet.get("candidate_probability")),
        "f_heuristic_ev_r": _as_float(packet.get("candidate_ev_r")),
        "f_thesis_probability": _as_float(thesis.get("probability")),
        "f_thesis_uncalibrated_probability": _as_float(
            thesis.get("uncalibrated_probability")
        ),
        "f_thesis_uncertainty": _as_float(thesis.get("uncertainty")),
        "f_thesis_missing_source_penalty": _as_float(
            thesis.get("missing_source_penalty")
        ),
        "f_thesis_source_completeness": _as_float(thesis.get("source_completeness")),
        "f_expected_cost_r": _as_float(packet.get("expected_cost_r")),
        "f_risk_reward_ratio": _as_float(
            packet.get("risk_reward_ratio") or packet.get("rr")
        ),
        "f_limit_offset_r": limit_offset_r,
        "f_stop_distance_rel": stop_distance_rel,
        "f_n_competing_in_group": float(n_competing),
        "f_open_positions_seen": _as_float(packet.get("simulated_open_positions_seen")),
        "f_pending_orders_seen": _as_float(packet.get("simulated_pending_orders_seen")),
    }
    pd_block = packet.get("predecision_features")
    pd_block = pd_block if isinstance(pd_block, Mapping) else {}
    for pd_name in (
        "atr14_over_atr50",
        "bars_since_session_open",
        "close_position_in_lookback_range",
        "close_to_close_vol_8_over_48",
        "compression_ratio_prior_bar",
        "dist_to_prior_high20_atr",
        "dist_to_prior_low20_atr",
        "session_open_range_width_atr",
        "stop_distance_atr",
        "sweep_depth_atr",
        "target_distance_atr",
        "trigger_bar_body_atr",
        "trigger_bar_range_atr",
    ):
        result[f"f_pd_{pd_name}"] = _as_float(pd_block.get(pd_name))
    trend_state = pd_block.get("trend_state_m15")
    result["f_pd_trend_state_m15"] = str(trend_state) if trend_state is not None else None
    transition = pd_block.get("trend_transition_flag")
    result["f_pd_trend_transition_flag"] = (
        str(bool(transition)).lower() if transition is not None else None
    )
    return result


def artifact_validation_errors(
    artifact: Mapping[str, Any],
    *,
    expected_generator_sha: str | None = None,
    now_utc: datetime | None = None,
) -> list[str]:
    errors: list[str] = []
    if artifact.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        errors.append(
            f"schema_version_mismatch_expected_{ARTIFACT_SCHEMA_VERSION}_got_{artifact.get('schema_version')}"
        )
    heads = artifact.get("heads")
    if not isinstance(heads, Mapping):
        errors.append("heads_missing")
    else:
        for head in REQUIRED_HEADS:
            if head not in heads:
                errors.append(f"head_missing:{head}")
    if not isinstance(artifact.get("numeric_features"), list):
        errors.append("numeric_features_missing")
    if not isinstance(artifact.get("categorical_features"), list):
        errors.append("categorical_features_missing")
    sha = str(artifact.get("generator_code_sha") or "")
    if expected_generator_sha and sha and sha != expected_generator_sha:
        errors.append(f"generator_code_sha_mismatch_artifact_{sha[:12]}_runtime_{expected_generator_sha[:12]}")
    valid_through = str(artifact.get("valid_through_utc") or "")
    if valid_through:
        try:
            cutoff = datetime.fromisoformat(valid_through.replace("Z", "+00:00"))
            if cutoff.tzinfo is None:
                cutoff = cutoff.replace(tzinfo=timezone.utc)
            now = now_utc or datetime.now(timezone.utc)
            if now > cutoff:
                errors.append(f"artifact_stale_valid_through_{valid_through}")
        except ValueError:
            errors.append("valid_through_utc_unparseable")
    return errors


def _numeric_value(
    features: Mapping[str, Any], spec: Mapping[str, Any]
) -> tuple[float, bool]:
    """Return (standardized value, was_missing)."""

    name = str(spec.get("name"))
    raw = features.get(name)
    value: float | None
    if isinstance(raw, bool) or raw is None:
        value = None
    else:
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = None
        if value is not None and not math.isfinite(value):
            value = None
    missing = value is None
    if value is None:
        value = float(spec.get("median") or 0.0)
    lo = spec.get("clip_low")
    hi = spec.get("clip_high")
    if lo is not None:
        value = max(float(lo), value)
    if hi is not None:
        value = min(float(hi), value)
    mean = float(spec.get("mean") or 0.0)
    std = float(spec.get("std") or 1.0)
    if std <= 0:
        std = 1.0
    return (value - mean) / std, missing


def _categorical_value(
    features: Mapping[str, Any], spec: Mapping[str, Any], *, head: str
) -> float:
    name = str(spec.get("name"))
    encodings = spec.get("encodings") or {}
    head_map = encodings.get(head) or {}
    level = features.get(name)
    level_key = str(level) if level is not None else "__missing__"
    if level_key in head_map:
        return float(head_map[level_key])
    return float(head_map.get("__prior__", 0.0))


def _linear_score(
    features: Mapping[str, Any], artifact: Mapping[str, Any], *, head: str
) -> tuple[float, list[str]]:
    head_spec = (artifact.get("heads") or {}).get(head) or {}
    coefficients = head_spec.get("coefficients") or {}
    intercept = float(head_spec.get("intercept") or 0.0)
    missing_required: list[str] = []
    total = intercept
    for spec in artifact.get("numeric_features") or []:
        name = str(spec.get("name"))
        coef = float(coefficients.get(name, 0.0))
        value, missing = _numeric_value(features, spec)
        if missing and spec.get("required") is True:
            missing_required.append(name)
        total += coef * value
    for spec in artifact.get("categorical_features") or []:
        name = str(spec.get("name"))
        coef = float(coefficients.get(name, 0.0))
        total += coef * _categorical_value(features, spec, head=head)
    return total, missing_required


def _beta_calibrate(probability: float, calibration: Mapping[str, Any] | None) -> float:
    if not calibration:
        return probability
    p = _clip01(probability)
    a = float(calibration.get("a") or 1.0)
    b = float(calibration.get("b") or 1.0)
    c = float(calibration.get("c") or 0.0)
    return _sigmoid(a * math.log(p) - b * math.log(1.0 - p) + c)


def _segment_shrinkage(
    features: Mapping[str, Any],
    artifact: Mapping[str, Any],
    probability: float,
    *,
    head: str,
) -> tuple[float, float]:
    """Reliability-weighted shrinkage to segment base rate. Returns (p, w)."""

    spec = artifact.get("segment_shrinkage") or {}
    head_spec = spec.get(head) or {}
    segments = head_spec.get("segments") or {}
    key_fields = spec.get("key_fields") or []
    key = "|".join(str(features.get(field) or "unknown") for field in key_fields)
    entry = segments.get(key) or {}
    base_rate = entry.get("base_rate", head_spec.get("global_base_rate"))
    n = float(entry.get("n") or 0.0)
    k = float(spec.get("k") or 0.0)
    if base_rate is None or k <= 0:
        return probability, 1.0
    weight = n / (n + k) if (n + k) > 0 else 0.0
    weight = max(float(spec.get("min_weight") or 0.0), weight)
    return weight * probability + (1.0 - weight) * float(base_rate), weight


def score_learned_edge(
    features: Mapping[str, Any],
    artifact: Mapping[str, Any],
    *,
    expected_generator_sha: str | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Score one candidate feature mapping with a frozen artifact."""

    errors = artifact_validation_errors(
        artifact, expected_generator_sha=expected_generator_sha, now_utc=now_utc
    )
    if errors:
        return {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "status": "refused_artifact_invalid",
            "errors": errors,
            "evidence_class": EVIDENCE_CLASS,
        }

    fill_logit, fill_missing = _linear_score(features, artifact, head="fill")
    outcome_logit, outcome_missing = _linear_score(features, artifact, head="outcome")
    missing_required = sorted(set(fill_missing + outcome_missing))
    if missing_required:
        return {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "status": "refused_missing_required_features",
            "missing_required_features": missing_required,
            "evidence_class": EVIDENCE_CLASS,
        }

    heads = artifact.get("heads") or {}
    p_fill_raw = _sigmoid(fill_logit)
    p_outcome_raw = _sigmoid(outcome_logit)
    p_fill = _beta_calibrate(p_fill_raw, (heads.get("fill") or {}).get("calibration"))
    p_outcome = _beta_calibrate(p_outcome_raw, (heads.get("outcome") or {}).get("calibration"))
    p_fill, fill_weight = _segment_shrinkage(features, artifact, p_fill, head="fill")
    p_outcome, outcome_weight = _segment_shrinkage(features, artifact, p_outcome, head="outcome")

    net_r_head = heads.get("net_r") or {}
    if net_r_head:
        net_r_value, _ = _linear_score(features, artifact, head="net_r")
        clip = net_r_head.get("clip") or {}
        lo, hi = clip.get("low"), clip.get("high")
        if lo is not None:
            net_r_value = max(float(lo), net_r_value)
        if hi is not None:
            net_r_value = min(float(hi), net_r_value)
    else:
        net_r_value = None

    expected_net_r = (p_fill * net_r_value) if net_r_value is not None else None

    return {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "status": "scored",
        "fill_probability_raw": round(p_fill_raw, 8),
        "fill_probability": round(p_fill, 8),
        "probability_raw": round(p_outcome_raw, 8),
        "probability": round(p_outcome, 8),
        "expected_net_r_conditional": round(net_r_value, 8) if net_r_value is not None else None,
        "expected_net_r": round(expected_net_r, 8) if expected_net_r is not None else None,
        "expected_net_r_semantics": EXPECTED_VALUE_ALREADY_FILL_ADJUSTED,
        "expected_net_r_semantics_source": "learned_edge_layer_v4_contract",
        "segment_shrinkage_weights": {
            "fill": round(fill_weight, 8),
            "outcome": round(outcome_weight, 8),
        },
        "artifact_hash_sha256": artifact.get("artifact_hash_sha256"),
        "training_manifest_sha256": artifact.get("training_manifest_sha256"),
        "evidence_class": EVIDENCE_CLASS,
    }
