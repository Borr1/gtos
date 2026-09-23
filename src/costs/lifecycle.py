"""Separate pretrade estimates from post-lifecycle simulated component cost.

Final offline economics may consume only the packet built here.  Its holding horizon is
derived from actual simulated entry/exit instants; there is no forecast-holding argument
and no path that can reuse a pretrade swap number.  The claim is intentionally narrower
than broker-realized cost because slippage remains a source-bound expectation unless
broker deal evidence exists.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from datetime import datetime, timezone
from numbers import Real
from typing import TYPE_CHECKING, Any

from src.costs.artifact_authority import DEFAULT_COST_INPUTS_MANIFEST
from src.costs.completeness import (
    PRETRADE_EXPECTED_COST_ROLE,
    CostPacketCompleteness,
    CostPacketIncompleteError,
)
from src.costs.coverage import Coverage, weakest
from src.costs.model import (
    CostTruthError,
    SpreadAccounting,
    SpreadGeometryEvidence,
    _resolve_geometry_authority,
    component_sum_r,
    cost_r,
    elapsed_holding_hours,
    load_broker_true_costs,
)

if TYPE_CHECKING:
    from src.costs.fx_conversion import HistoricalFxRates
    from src.costs.model import BrokerTrueCosts
    from src.costs.slippage_model import SlippageModel
    from src.costs.spread_model import SpreadModel

__all__ = [
    "POST_LIFECYCLE_COMPONENT_COST_ROLE",
    "POST_LIFECYCLE_COMPONENT_COST_SCHEMA",
    "PRETRADE_EXPECTED_COST_ROLE",
    "assess_post_lifecycle_component_cost",
    "build_post_lifecycle_component_cost",
    "post_lifecycle_component_cost_is_complete",
    "require_complete_post_lifecycle_component_cost",
]

POST_LIFECYCLE_COMPONENT_COST_ROLE = "post_lifecycle_component_cost"
POST_LIFECYCLE_COMPONENT_COST_SCHEMA = (
    "gtos.costs.post_lifecycle_component_cost.v1"
)
_FIELDS = ("spread_r", "expected_slippage_r", "swap_cost_r", "commission_r")
_SOURCE_ROLES = {
    "spread_r": "observed_quote_spread_attributed_in_fill_anchored_gross",
    "expected_slippage_r": "source_bound_expected_slippage_not_broker_realized",
    "swap_cost_r": "actual_elapsed_broker_rollover_component",
    "commission_r": "broker_schedule_component",
}


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    number = float(value)
    return number if math.isfinite(number) and number >= 0 else None


def _sha(value: object) -> str | None:
    if not isinstance(value, str) or len(value) != 64:
        return None
    return value if all(c in "009abcdef" for c in value) else None


def _utc(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if instant.tzinfo is None:
        return None
    return instant.astimezone(timezone.utc)


def _revalidate_quote_geometry(
    lifecycle: Mapping[str, Any], geometry: Mapping[str, Any]
) -> str | None:
    """Re-read the bound row and cross-check every lifecycle geometry input."""

    account = lifecycle.get("account")
    symbol = lifecycle.get("symbol")
    side = lifecycle.get("side")
    entry_utc = _utc(lifecycle.get("entry_utc"))
    entry_price = _number(lifecycle.get("entry_price"))
    sl_distance = _number(lifecycle.get("sl_distance_price"))
    if (
        not isinstance(account, str)
        or not account
        or not isinstance(symbol, str)
        or not symbol
        or not isinstance(side, str)
        or not side
        or entry_utc is None
        or entry_price is None
        or entry_price <= 0
        or sl_distance is None
        or sl_distance <= 0
    ):
        return "quote_geometry_lifecycle_binding_invalid"
    try:
        evidence = SpreadGeometryEvidence(
            source_path=geometry.get("source_path"),
            source_sha256=geometry.get("source_sha256"),
            row_index=geometry.get("row_index"),
            trade_id=geometry.get("trade_id"),
        )
        resolved_symbol, _ = load_broker_true_costs().resolve_instrument(
            account, symbol
        )
        _, _, _, _, resolved_detail = _resolve_geometry_authority(
            evidence,
            account=account,
            resolved_symbol=resolved_symbol,
            entry_utc=entry_utc,
            entry_price=entry_price,
            side=side,
            sl_distance_price=sl_distance,
        )
    except (AttributeError, CostTruthError, TypeError, ValueError):
        return "quote_geometry_authority_revalidation_failed"
    if dict(geometry) != resolved_detail:
        return "quote_geometry_authority_receipt_mismatch"
    return None


def _base_packet(
    *,
    trade_id: str,
    symbol: str,
    account: str,
    side: str,
    entry_utc: datetime,
    exit_utc: datetime,
    entry_price: float,
    exit_price: float,
    sl_distance_price: float,
    pretrade_expected_cost_ref: str | None,
    lifecycle_provenance: str,
) -> dict[str, Any]:
    elapsed = elapsed_holding_hours(entry_utc, exit_utc)
    return {
        "schema": POST_LIFECYCLE_COMPONENT_COST_SCHEMA,
        "cost_role": POST_LIFECYCLE_COMPONENT_COST_ROLE,
        "result_use_scope": "SIMULATED_POST_LIFECYCLE_COST_NOT_BROKER_REALIZED",
        "broker_realized_status": "NOT_EVALUABLE_NO_BROKER_DEAL_COMPONENTS",
        "trade_id": trade_id,
        "predecessor": {
            "cost_role": PRETRADE_EXPECTED_COST_ROLE,
            "packet_ref": pretrade_expected_cost_ref,
            "components_reused": [],
        },
        "lifecycle": {
            "entry_utc": entry_utc.astimezone(timezone.utc).isoformat(),
            "exit_utc": exit_utc.astimezone(timezone.utc).isoformat(),
            "symbol": symbol,
            "account": account,
            "side": side.upper(),
            "elapsed_holding_hours": elapsed,
            "holding_source_status": "actual_simulated_entry_exit_elapsed",
            "source_status": "actual_simulated_lifecycle",
            "provenance": lifecycle_provenance,
            "entry_price": float(entry_price),
            "exit_price": float(exit_price),
            "sl_distance_price": float(sl_distance_price),
        },
        "component_sum_order": list(_FIELDS),
    }


def build_post_lifecycle_component_cost(
    *,
    trade_id: str,
    symbol: str,
    account: str,
    entry_utc: datetime,
    exit_utc: datetime,
    entry_price: float,
    exit_price: float,
    sl_distance_price: float,
    geometry_spread_evidence: SpreadGeometryEvidence,
    verified_quote_geometry_resolver: object | None = None,
    lifecycle_provenance: str,
    side: str = "LONG",
    pretrade_expected_cost_ref: str | None = None,
    spread_percentile: str = "p50",
    spread_session: str | None = None,
    spread_band: str | None = None,
    spread_vol_state: int | None = None,
    spread_composition: str | None = None,
    spread_era_exponent: float | None = None,
    spread_require_decidable: bool = False,
    spread_model: "SpreadModel | None" = None,
    historical_fx: "HistoricalFxRates | None" = None,
    slippage_model: "SlippageModel | None" = None,
    costs: "BrokerTrueCosts | None" = None,
) -> dict[str, Any]:
    """Build a final-simulation cost packet from actual lifecycle geometry.

    Failure is returned as ``NOT_EVALUABLE`` with ``total_cost_r=None``.  The caller can
    retain that row in its denominator, but cannot obtain a numeric default from it.
    """

    if not isinstance(trade_id, str) or not trade_id.strip() or trade_id != trade_id.strip():
        raise CostTruthError("post-lifecycle trade_id must be non-empty and trimmed")
    if pretrade_expected_cost_ref is not None and (
        not isinstance(pretrade_expected_cost_ref, str)
        or not pretrade_expected_cost_ref.strip()
        or pretrade_expected_cost_ref != pretrade_expected_cost_ref.strip()
    ):
        raise CostTruthError("pretrade_expected_cost_ref must be non-empty and trimmed")
    if (
        not isinstance(lifecycle_provenance, str)
        or not lifecycle_provenance.strip()
        or lifecycle_provenance != lifecycle_provenance.strip()
    ):
        raise CostTruthError("lifecycle_provenance must be non-empty and trimmed")
    for name, value in (
        ("entry_price", entry_price),
        ("exit_price", exit_price),
        ("sl_distance_price", sl_distance_price),
    ):
        if _number(value) is None or float(value) <= 0:
            raise CostTruthError(f"post-lifecycle {name} must be finite and > 0")

    packet = _base_packet(
        trade_id=trade_id,
        symbol=symbol,
        account=account,
        side=side,
        entry_utc=entry_utc,
        exit_utc=exit_utc,
        entry_price=entry_price,
        exit_price=exit_price,
        sl_distance_price=sl_distance_price,
        pretrade_expected_cost_ref=pretrade_expected_cost_ref,
        lifecycle_provenance=lifecycle_provenance,
    )
    elapsed = packet["lifecycle"]["elapsed_holding_hours"]
    try:
        breakdown = cost_r(
            symbol,
            account,
            elapsed,
            sl_distance_price=sl_distance_price,
            entry_price=entry_price,
            side=side,
            entry_utc=entry_utc,
            spread_percentile=spread_percentile,
            spread_session=spread_session,
            spread_band=spread_band,
            spread_vol_state=spread_vol_state,
            spread_composition=spread_composition,
            spread_era_exponent=spread_era_exponent,
            spread_require_decidable=spread_require_decidable,
            spread_accounting=SpreadAccounting.QUOTE_GEOMETRY,
            geometry_spread_evidence=geometry_spread_evidence,
            verified_quote_geometry_resolver=verified_quote_geometry_resolver,
            spread_model=spread_model,
            historical_fx=historical_fx,
            slippage_model=slippage_model,
            costs=costs,
        )
    except CostTruthError as exc:
        packet.update({
            "status": "NOT_EVALUABLE",
            "components": {},
            "total_cost_r": None,
            "coverage": None,
            "failures": [f"component_build_failed:{exc}"],
        })
        return packet

    measures = {
        "spread_r": breakdown.spread_r,
        "expected_slippage_r": breakdown.slippage_r,
        "swap_cost_r": breakdown.swap_r,
        "commission_r": breakdown.commission_r,
    }
    manifest_sha = breakdown.detail["slippage"].get(
        "cost_inputs_manifest_sha256"
    )
    fx_manifest_sha = (breakdown.detail.get("fx_conversion") or {}).get(
        "cost_inputs_manifest_sha256"
    )
    if fx_manifest_sha is not None and fx_manifest_sha != manifest_sha:
        packet.update({
            "status": "NOT_EVALUABLE",
            "components": {},
            "total_cost_r": None,
            "coverage": None,
            "failures": ["cost_input_manifest_authority_disagreement"],
        })
        return packet

    components: dict[str, dict[str, Any]] = {}
    for field, measure in measures.items():
        component = measure.as_dict()
        component["source_role"] = _SOURCE_ROLES[field]
        if field in {"swap_cost_r", "commission_r"}:
            component["broker_true_costs_artifact_sha256"] = breakdown.detail.get(
                "broker_true_costs_artifact_sha256"
            )
        if field == "expected_slippage_r" or (
            field == "commission_r" and fx_manifest_sha is not None
        ):
            component["cost_inputs_manifest_sha256"] = manifest_sha
        components[field] = component
    components["spread_r"].update({
        "accounting": "included_in_fill_anchored_gross_no_additional_deduction",
        "attributed_physical_spread_r": (
            breakdown.attributed_spread_r.value
            if breakdown.attributed_spread_r is not None
            else None
        ),
    })
    packet["lifecycle"]["quote_geometry"] = breakdown.detail["spread"][
        "geometry_authority"
    ]
    lifecycle_integrity = {
        key: packet["lifecycle"][key]
        for key in (
            "entry_utc",
            "exit_utc",
            "symbol",
            "account",
            "side",
            "elapsed_holding_hours",
            "entry_price",
            "exit_price",
            "sl_distance_price",
            "holding_source_status",
            "source_status",
            "provenance",
        )
    }
    lifecycle_integrity["quote_geometry"] = packet["lifecycle"]["quote_geometry"]
    packet["lifecycle"]["record_sha256"] = hashlib.sha256(
        json.dumps(
            lifecycle_integrity, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    packet["cost_input_authority"] = {
        "root_kind": "git_versioned_manifest_bytes",
        "manifest_path": str(DEFAULT_COST_INPUTS_MANIFEST),
        "manifest_sha256": manifest_sha,
        "broker_true_costs_artifact_sha256": breakdown.detail.get(
            "broker_true_costs_artifact_sha256"
        ),
    }
    packet.update({
        "status": "COMPLETE",
        "components": components,
        "total_cost_r": breakdown.total_r.value,
        "coverage": breakdown.total_r.coverage.value,
        "total_provenance": breakdown.total_r.provenance,
        "failures": [],
    })
    return packet


def assess_post_lifecycle_component_cost(
    packet: Mapping[str, Any],
) -> CostPacketCompleteness:
    """Validate the post-lifecycle packet for final simulated economics."""

    failures: list[str] = []
    if packet.get("schema") != POST_LIFECYCLE_COMPONENT_COST_SCHEMA:
        failures.append("wrong_post_lifecycle_schema")
    if packet.get("cost_role") != POST_LIFECYCLE_COMPONENT_COST_ROLE:
        failures.append("wrong_cost_role_not_post_lifecycle")
    if packet.get("status") != "COMPLETE":
        failures.append("post_lifecycle_status_not_complete")
    if packet.get("broker_realized_status") != "NOT_EVALUABLE_NO_BROKER_DEAL_COMPONENTS":
        failures.append("broker_realized_claim_scope_invalid")

    predecessor = packet.get("predecessor")
    if not isinstance(predecessor, Mapping):
        failures.append("predecessor_missing")
    else:
        if predecessor.get("cost_role") != PRETRADE_EXPECTED_COST_ROLE:
            failures.append("predecessor_role_invalid")
        if predecessor.get("components_reused") != []:
            failures.append("pretrade_components_reused")

    lifecycle = packet.get("lifecycle")
    if not isinstance(lifecycle, Mapping):
        lifecycle = {}
        failures.append("lifecycle_missing")
    entry = _utc(lifecycle.get("entry_utc"))
    exit_ = _utc(lifecycle.get("exit_utc"))
    elapsed = _number(lifecycle.get("elapsed_holding_hours"))
    if entry is None or exit_ is None or exit_ < entry:
        failures.append("actual_entry_exit_invalid")
    elif elapsed is None or elapsed != elapsed_holding_hours(entry, exit_):
        failures.append("actual_elapsed_holding_mismatch")
    if lifecycle.get("holding_source_status") != "actual_simulated_entry_exit_elapsed":
        failures.append("holding_source_is_not_actual_lifecycle")
    if lifecycle.get("source_status") != "actual_simulated_lifecycle":
        failures.append("lifecycle_source_status_invalid")
    if not isinstance(lifecycle.get("provenance"), str) or not lifecycle[
        "provenance"
    ].strip():
        failures.append("lifecycle_provenance_missing")
    for field in ("entry_price", "exit_price", "sl_distance_price"):
        value = _number(lifecycle.get(field))
        if value is None or value <= 0:
            failures.append(f"invalid_lifecycle_geometry:{field}")
    geometry = lifecycle.get("quote_geometry")
    if not isinstance(geometry, Mapping):
        failures.append("quote_geometry_missing")
    else:
        if geometry.get("gross_basis") != "fill_anchored_quote_geometry":
            failures.append("quote_geometry_gross_basis_invalid")
        if geometry.get("gross_includes_spread") is not True:
            failures.append("quote_geometry_spread_inclusion_missing")
        if _sha(geometry.get("source_sha256")) is None:
            failures.append("quote_geometry_source_hash_invalid")
        if geometry.get("trade_id") != packet.get("trade_id"):
            failures.append("quote_geometry_trade_mismatch")
        revalidation_failure = _revalidate_quote_geometry(lifecycle, geometry)
        if revalidation_failure is not None:
            failures.append(revalidation_failure)
    integrity_keys = (
        "entry_utc",
        "exit_utc",
        "symbol",
        "account",
        "side",
        "elapsed_holding_hours",
        "entry_price",
        "exit_price",
        "sl_distance_price",
        "holding_source_status",
        "source_status",
        "provenance",
    )
    lifecycle_integrity = {key: lifecycle.get(key) for key in integrity_keys}
    lifecycle_integrity["quote_geometry"] = geometry
    try:
        expected_lifecycle_sha = hashlib.sha256(
            json.dumps(
                lifecycle_integrity, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
    except (TypeError, ValueError):
        expected_lifecycle_sha = None
    if expected_lifecycle_sha is None or lifecycle.get(
        "record_sha256"
    ) != expected_lifecycle_sha:
        failures.append("lifecycle_record_hash_mismatch")

    authority = packet.get("cost_input_authority")
    manifest_sha = None
    broker_truth_sha = None
    if not isinstance(authority, Mapping):
        failures.append("cost_input_authority_missing")
    else:
        if authority.get("root_kind") != "git_versioned_manifest_bytes":
            failures.append("cost_input_authority_root_invalid")
        manifest_sha = _sha(authority.get("manifest_sha256"))
        if manifest_sha is None:
            failures.append("cost_input_manifest_hash_invalid")
        if not isinstance(authority.get("manifest_path"), str):
            failures.append("cost_input_manifest_path_missing")
        broker_truth_sha = _sha(
            authority.get("broker_true_costs_artifact_sha256")
        )
        if broker_truth_sha is None:
            failures.append("broker_true_costs_artifact_hash_invalid")

    components = packet.get("components")
    if not isinstance(components, Mapping):
        components = {}
        failures.append("post_lifecycle_components_missing")
    values: dict[str, float] = {}
    coverages: list[Coverage] = []
    for field in _FIELDS:
        component = components.get(field)
        if not isinstance(component, Mapping):
            failures.append(f"missing_post_lifecycle_component:{field}")
            continue
        value = _number(component.get("value"))
        if value is None:
            failures.append(f"invalid_post_lifecycle_component:{field}")
        else:
            values[field] = value
        try:
            coverage = Coverage(component.get("coverage"))
        except (TypeError, ValueError):
            failures.append(f"invalid_component_coverage:{field}")
        else:
            coverages.append(coverage)
        if not isinstance(component.get("provenance"), str) or not component[
            "provenance"
        ].strip():
            failures.append(f"component_provenance_missing:{field}")
        if component.get("source_role") != _SOURCE_ROLES[field]:
            failures.append(f"component_source_role_invalid:{field}")
        if field in {"swap_cost_r", "commission_r"} and component.get(
            "broker_true_costs_artifact_sha256"
        ) != broker_truth_sha:
            failures.append(f"broker_truth_authority_mismatch:{field}")
    slippage = components.get("expected_slippage_r")
    if isinstance(slippage, Mapping) and slippage.get(
        "cost_inputs_manifest_sha256"
    ) != manifest_sha:
        failures.append("slippage_manifest_authority_mismatch")
    spread = components.get("spread_r")
    if isinstance(spread, Mapping):
        if spread.get("accounting") != (
            "included_in_fill_anchored_gross_no_additional_deduction"
        ):
            failures.append("spread_accounting_not_exactly_once")
        # The validated quote-geometry contract above says the transacted
        # bid/ask spread is already present in gross P&L.  Keep that physical
        # spread as attribution, but never permit it (or a model spread) to
        # re-enter the component deduction.  Checking the numeric slot matters:
        # an internally re-summed packet would otherwise pass every identity
        # check below and charge the same spread twice.
        if _number(spread.get("value")) != 0.0:
            failures.append("spread_already_in_gross_must_not_be_deducted")
        if _number(spread.get("attributed_physical_spread_r")) is None:
            failures.append("attributed_physical_spread_missing")

    exact_sum = None
    if len(values) == len(_FIELDS):
        exact_sum = component_sum_r(*(values[field] for field in _FIELDS))
    total = _number(packet.get("total_cost_r"))
    if total is None:
        failures.append("post_lifecycle_total_invalid")
    elif exact_sum is None or total != exact_sum:
        failures.append("post_lifecycle_component_identity_mismatch")
    if packet.get("component_sum_order") != list(_FIELDS):
        failures.append("component_sum_order_invalid")
    if coverages:
        expected_coverage = weakest(*coverages).value
        if len(coverages) != len(_FIELDS) or packet.get("coverage") != expected_coverage:
            failures.append("post_lifecycle_weakest_coverage_mismatch")

    failures = list(dict.fromkeys(failures))
    complete = not failures
    return CostPacketCompleteness(
        status="COMPLETE" if complete else "NOT_EVALUABLE",
        complete=complete,
        component_values=values,
        component_sum_r=exact_sum if complete else None,
        failures=tuple(failures),
    )


def post_lifecycle_component_cost_is_complete(packet: Mapping[str, Any]) -> bool:
    return assess_post_lifecycle_component_cost(packet).complete


def require_complete_post_lifecycle_component_cost(
    packet: Mapping[str, Any],
) -> CostPacketCompleteness:
    assessment = assess_post_lifecycle_component_cost(packet)
    if not assessment.complete:
        raise CostPacketIncompleteError(assessment)
    return assessment
