"""Default-off research candidate for Session FB's OB-retest geometry repair.

The transform is intentionally unreachable from runtime candidate generation.
It is an offline training-lane surface that must be called with ``enabled=True``.
Entry, decision time, symbol, and declared direction stay fixed; the stop becomes
0.25 of the source entry-to-stop distance and the target becomes 1.5 of that
distance.  No outcome field may enter an enabled transform.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from typing import Any, Mapping

from src.components.candidate_geometry import canonicalize_candidate_geometry


TRANSFORM_ID = "fb_current_ob_retest_as_declared_target_1p5d_stop_0p25d_v1"
ORIGIN_FAMILY = "current_ob_retest"
TARGET_DISTANCE_D = 1.5
STOP_DISTANCE_D = 0.25
REWARD_TO_RISK = TARGET_DISTANCE_D / STOP_DISTANCE_D
DEFAULT_ENABLED = False
ENABLE_SURFACE = "explicit_research_argument_only"

# Expected beliefs and predecision scores are deliberately not in this set.
# These names are realized/path labels and must be projected away before an
# enabled research transform can run.
FORBIDDEN_OUTCOME_FIELDS = frozenset(
    {
        "ambiguity_resolution",
        "counterfactual_order_close_time_utc",
        "exit_reason",
        "exit_utc",
        "final_r",
        "gross_r",
        "grid_net_r",
        "net_r",
        "opportunity_close_reason",
        "opportunity_gross_r",
        "opportunity_net_proxy_r",
        "outcome",
        "policy_gross_r",
        "raw_gross_r",
        "raw_net_proxy_r",
        "raw_opportunity_close_reason",
        "same_bar_ambiguity",
        "stop_first_touch_utc",
        "target_first_touch_utc",
        "terminal_outcome",
        "terminal_r_diagnostic_close_reason",
        "terminal_r_diagnostic_gross_r",
        "terminal_r_diagnostic_outcome",
        "terminal_r_diagnostic_target_r",
    }
)


class CurrentOBRetestGeometryCandidateError(ValueError):
    """The explicitly enabled research transform failed closed."""


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _candidate_id(original_id: str, identity: Mapping[str, Any]) -> str:
    material = {
        "original_candidate_id": original_id,
        "transform_id": TRANSFORM_ID,
        **dict(identity),
    }
    digest = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return f"broadorigin_{digest}"


def apply_current_ob_retest_geometry_candidate(
    candidate: Mapping[str, Any],
    *,
    enabled: bool = DEFAULT_ENABLED,
) -> dict[str, Any]:
    """Return a detached candidate and transform only explicit OB-retest calls.

    Disabled calls and other origin families are deep-copy pass-throughs.  An
    enabled OB-retest candidate containing a realized/path label is rejected,
    making the evidence boundary behavioral rather than documentary.
    """

    row = deepcopy(dict(candidate))
    if not enabled or str(row.get("origin_family") or "") != ORIGIN_FAMILY:
        return row

    entered_outcomes = sorted(
        field for field in FORBIDDEN_OUTCOME_FIELDS if row.get(field) is not None
    )
    if entered_outcomes:
        raise CurrentOBRetestGeometryCandidateError(
            "enabled current_ob_retest candidate forbids outcome fields:"
            + ",".join(entered_outcomes)
        )

    entry = _finite(row.get("entry_price"))
    original_stop = _finite(row.get("stop_loss"))
    side = str(row.get("side") or row.get("direction") or "").upper()
    original_id = str(row.get("candidate_id") or "")
    symbol = str(row.get("symbol") or "")
    decision_time_utc = str(row.get("decision_time_utc") or "")
    if (
        entry is None
        or original_stop is None
        or entry == original_stop
        or side not in {"LONG", "SHORT"}
        or not original_id
        or not symbol
        or not decision_time_utc
    ):
        raise CurrentOBRetestGeometryCandidateError(
            "enabled current_ob_retest candidate requires candidate_id, symbol, "
            "decision_time_utc, finite nonzero entry/stop geometry, and LONG or SHORT side"
        )

    base_distance = abs(entry - original_stop)
    sign = 1.0 if side == "LONG" else -1.0
    repaired_stop = entry - sign * STOP_DISTANCE_D * base_distance
    repaired_target = entry + sign * TARGET_DISTANCE_D * base_distance
    identity = {
        "symbol": symbol,
        "decision_time_utc": decision_time_utc,
        "side": side,
        "entry_price": entry,
        "original_stop_loss": original_stop,
        "original_base_distance": base_distance,
        "target_distance_D": TARGET_DISTANCE_D,
        "stop_distance_D": STOP_DISTANCE_D,
    }
    row.update(
        {
            "candidate_id": _candidate_id(original_id, identity),
            "side": side,
            "direction": side,
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
            "candidate_transform_enable_surface": ENABLE_SURFACE,
            "candidate_transform_source_boundary": (
                "predecision_candidate_geometry_only_outcome_fields_fail_closed"
            ),
            "candidate_transform_original": {
                "candidate_id": original_id,
                "side": side,
                "entry_price": entry,
                "stop_loss": original_stop,
                "take_profit_1": _finite(row.get("take_profit_1")),
                "risk_reward_ratio": _finite(row.get("risk_reward_ratio")),
            },
            "candidate_transform_spec": identity,
        }
    )
    predecision = row.get("predecision_features")
    if isinstance(predecision, dict):
        original_stop_atr = _finite(predecision.get("stop_distance_atr"))
        if original_stop_atr is not None:
            predecision["stop_distance_atr"] = original_stop_atr * STOP_DISTANCE_D
            predecision["target_distance_atr"] = original_stop_atr * TARGET_DISTANCE_D
    source_fields = row.get("source_fields")
    if isinstance(source_fields, dict):
        source_fields["candidate_transform_id"] = TRANSFORM_ID
        source_fields["candidate_transform_source_boundary"] = row[
            "candidate_transform_source_boundary"
        ]

    repaired = canonicalize_candidate_geometry(row, source=TRANSFORM_ID)
    if not (
        repaired["side"] == repaired["direction"] == side
        and math.isclose(float(repaired["entry_price"]), entry, abs_tol=1e-12)
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
        raise CurrentOBRetestGeometryCandidateError(
            "canonical current_ob_retest geometry did not reconcile"
        )
    return repaired


__all__ = [
    "DEFAULT_ENABLED",
    "ENABLE_SURFACE",
    "FORBIDDEN_OUTCOME_FIELDS",
    "ORIGIN_FAMILY",
    "REWARD_TO_RISK",
    "STOP_DISTANCE_D",
    "TARGET_DISTANCE_D",
    "TRANSFORM_ID",
    "CurrentOBRetestGeometryCandidateError",
    "apply_current_ob_retest_geometry_candidate",
]
