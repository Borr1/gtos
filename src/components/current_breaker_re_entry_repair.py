"""Default-off candidate transform for CQ's breaker re-entry repair.

The transform is deliberately pure and predecision-only. It changes no config,
broker state, or admission authority. The original candidate entry stays fixed;
the declared side is inverted and geometry becomes target 5D / stop 0.25D,
where D is the candidate's original absolute entry-to-stop distance.

January true-UTC path evidence selected this exact predeclared cell. Selection is
not activation: callers must explicitly pass ``enabled=True``, and the candidate
still traverses every downstream selector, cost, risk, permission, and broker
authority gate.
"""

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from typing import Any, Mapping

from src.components.candidate_geometry import canonicalize_candidate_geometry


TRANSFORM_ID = "cq_current_breaker_inverted_target_5d_stop_0p25d_v1"
ENABLE_CONFIG_KEY = "phase18_current_breaker_re_entry_repair_enabled"
ORIGIN_FAMILY = "current_breaker_re_entry"
TARGET_DISTANCE_D = 5.0
STOP_DISTANCE_D = 0.25
REWARD_TO_RISK = TARGET_DISTANCE_D / STOP_DISTANCE_D


class CurrentBreakerRepairError(ValueError):
    """The enabled transform received geometry it cannot repair honestly."""


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _candidate_id(original_id: str, payload: Mapping[str, Any]) -> str:
    material = {
        "original_candidate_id": original_id,
        "transform_id": TRANSFORM_ID,
        **dict(payload),
    }
    digest = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return f"broadorigin_{digest}"


def apply_current_breaker_re_entry_repair(
    candidate: Mapping[str, Any],
    *,
    enabled: bool = False,
) -> dict[str, Any]:
    """Return a detached candidate, transformed only when explicitly enabled.

    Non-breaker candidates are always exact deep-copy pass-throughs. Disabled
    breaker candidates are too. Enabled malformed breaker geometry fails closed;
    it is never silently passed through as if the repair had applied.
    """

    row = deepcopy(dict(candidate))
    if not enabled or str(row.get("origin_family") or "") != ORIGIN_FAMILY:
        return row

    entry = _finite(row.get("entry_price"))
    original_stop = _finite(row.get("stop_loss"))
    original_side = str(row.get("side") or row.get("direction") or "").upper()
    original_id = str(row.get("candidate_id") or "")
    if (
        entry is None
        or original_stop is None
        or entry == original_stop
        or original_side not in {"LONG", "SHORT"}
        or not original_id
    ):
        raise CurrentBreakerRepairError(
            "enabled current_breaker repair requires candidate_id, finite nonzero "
            "entry/stop geometry, and LONG or SHORT side"
        )

    base_distance = abs(entry - original_stop)
    repaired_side = "SHORT" if original_side == "LONG" else "LONG"
    sign = 1.0 if repaired_side == "LONG" else -1.0
    repaired_stop = entry - sign * STOP_DISTANCE_D * base_distance
    repaired_target = entry + sign * TARGET_DISTANCE_D * base_distance
    identity = {
        "original_side": original_side,
        "repaired_side": repaired_side,
        "entry_price": entry,
        "original_stop_loss": original_stop,
        "original_base_distance": base_distance,
        "target_distance_D": TARGET_DISTANCE_D,
        "stop_distance_D": STOP_DISTANCE_D,
    }

    row.update(
        {
            "candidate_id": _candidate_id(original_id, identity),
            "side": repaired_side,
            "direction": repaired_side,
            "entry_reference": entry,
            "stop_loss": repaired_stop,
            "stop_or_invalidation": repaired_stop,
            "take_profit_1": repaired_target,
            "take_profit": repaired_target,
            "target_reference": repaired_target,
            "risk_reward_ratio": REWARD_TO_RISK,
            "rr": REWARD_TO_RISK,
            "candidate_transform_id": TRANSFORM_ID,
            "candidate_transform_enabled": True,
            "candidate_transform_default": "off",
            "candidate_transform_source_boundary": (
                "predecision_candidate_geometry_only_no_outcome_fields"
            ),
            "candidate_transform_original": {
                "candidate_id": original_id,
                "side": original_side,
                "entry_price": entry,
                "stop_loss": original_stop,
                "take_profit_1": _finite(row.get("take_profit_1")),
                "risk_reward_ratio": _finite(row.get("risk_reward_ratio")),
            },
            "candidate_transform_spec": identity,
        }
    )
    features = row.get("predecision_features")
    if isinstance(features, dict):
        old_stop_atr = _finite(features.get("stop_distance_atr"))
        if old_stop_atr is not None:
            features["stop_distance_atr"] = old_stop_atr * STOP_DISTANCE_D
            features["target_distance_atr"] = old_stop_atr * TARGET_DISTANCE_D
    source_fields = row.get("source_fields")
    if isinstance(source_fields, dict):
        source_fields["candidate_transform_id"] = TRANSFORM_ID
        source_fields["candidate_transform_source_boundary"] = row[
            "candidate_transform_source_boundary"
        ]
        source_fields["candidate_transform_original_side"] = original_side

    repaired = canonicalize_candidate_geometry(row, source=TRANSFORM_ID)
    if not (
        repaired["side"] == repaired_side
        and repaired["direction"] == repaired_side
        and math.isclose(
            float(repaired["stop_loss"]), repaired_stop, rel_tol=1e-12, abs_tol=1e-12
        )
        and math.isclose(
            float(repaired["take_profit_1"]),
            repaired_target,
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
        and math.isclose(
            float(repaired["risk_reward_ratio"]),
            REWARD_TO_RISK,
            rel_tol=0.0,
            abs_tol=1e-12,
        )
    ):
        raise CurrentBreakerRepairError("canonical repaired geometry did not reconcile")
    return repaired


__all__ = [
    "ENABLE_CONFIG_KEY",
    "ORIGIN_FAMILY",
    "REWARD_TO_RISK",
    "STOP_DISTANCE_D",
    "TARGET_DISTANCE_D",
    "TRANSFORM_ID",
    "CurrentBreakerRepairError",
    "apply_current_breaker_re_entry_repair",
]
