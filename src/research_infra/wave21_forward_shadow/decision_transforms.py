"""Post-generation candidate transforms the frozen funnel rows were built on.

The sealed funnel population is NOT the raw generator output: between
generation and the ledger row, the research timewarp applies (in truth mode)
the dynamic execution-policy router and the V4 target/stop geometry contract —
which retargets ``take_profit_1``/``risk_reward_ratio`` to the routed policy's
``final_target_r`` — then canonicalizes geometry and mints the candidate's
occurrence identity.  (Verbatim source:
``v4_timewarp_simulated_live_research_loop.evaluate_candidate_v4``,
the block ending at ``candidate_after_geometry``.)

The shadow must run the same chain or its candidate surface diverges from the
rule's — the generation-probe harness measures exactly that against sealed
February windows.  Everything here calls the production functions; only the
glue is local, and the glue mirrors the timewarp lines it cites.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.components.broader_origin_generators import (
    CANDIDATE_OCCURRENCE_KEY_FIELD,
    CANDIDATE_SOURCE_SAFE_FINGERPRINT_FIELD,
    candidate_occurrence_key_from_fields,
)
from src.components.candidate_geometry import canonicalize_candidate_geometry
from src.components.dynamic_target_stop_geometry_v4 import (
    build_target_stop_geometry_v4_contract,
)
from src.research_infra import v4_timewarp_simulated_live_research_loop as _tw

TRUTH_MODE_ECONOMIC_RISK_PCT = 0.0


def apply_dynamic_target_geometry(
    candidate: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Route the execution policy and retarget the candidate (timewarp-exact).

    Mirrors ``evaluate_candidate_v4`` lines 69233-69359 under truth mode
    (probability economics stripped, economic risk 0.0): router record ->
    geometry contract -> ``risk_reward_ratio``/``take_profit_1`` retarget ->
    ``canonicalize_candidate_geometry``.
    """

    candidate = dict(candidate)
    policy_router_record = _tw.dynamic_policy_router_record(
        candidate=candidate,
        config=config,
        risk_pct=TRUTH_MODE_ECONOMIC_RISK_PCT,
    )
    selected_policy = str(
        policy_router_record.get("selected_policy") or "momentum_exhaustion"
    )
    execution_policy_id = policy_router_record.get("execution_policy_id")
    selected_policy_params = _tw.selected_policy_params_from_router_record(
        policy_router_record
    )
    dynamic_geometry_trade_params = {
        "entry_price": candidate.get("entry_price"),
        "stop_loss": candidate.get("stop_loss"),
        "direction": candidate.get("side"),
        **_tw.dynamic_geometry_trade_params_from_policy_params(selected_policy_params),
    }
    geometry_contract = build_target_stop_geometry_v4_contract(
        config=config,
        selected_policy=selected_policy,
        execution_policy_id=execution_policy_id,
        source_event={
            "source_path_feature_status": "computed_from_source_ohlc_asof_timewarp_replay",
            "source_window_complete": True,
            "ordered_path_status": "pending_post_asof_replay",
            "selected_policy_ordered_path_status": "ordered_path_pending_postdecision_replay",
            "selected_policy_same_bar_ambiguous": False,
            "moonshot_dynamic_execution_router_v4": policy_router_record,
            "selected_policy_params": selected_policy_params or None,
        },
        trade_params=dynamic_geometry_trade_params,
        entry_price=candidate.get("entry_price"),
        stop_loss=candidate.get("stop_loss"),
        direction=candidate.get("side"),
        final_target_r=selected_policy_params.get("final_target_r")
        if selected_policy_params
        else None,
        stage="timewarp_asof_candidate_decision",
    )
    geometry_destination = geometry_contract.get("target_destination")
    geometry_destination = (
        geometry_destination if isinstance(geometry_destination, Mapping) else {}
    )
    final_target_r = _tw.safe_float(
        _tw.first_present(
            geometry_contract.get("final_target_r"),
            geometry_destination.get("final_target_r"),
            candidate.get("risk_reward_ratio"),
        ),
        _tw.safe_float(candidate.get("risk_reward_ratio"), 1.5),
    )
    risk_distance = abs(
        _tw.safe_float(candidate.get("entry_price"))
        - _tw.safe_float(candidate.get("stop_loss"))
    )
    dynamic_target = None
    if risk_distance > 0:
        if str(candidate.get("side") or "").upper() == "LONG":
            dynamic_target = (
                _tw.safe_float(candidate.get("entry_price"))
                + final_target_r * risk_distance
            )
        else:
            dynamic_target = (
                _tw.safe_float(candidate.get("entry_price"))
                - final_target_r * risk_distance
            )
    candidate = {
        **candidate,
        "risk_reward_ratio": final_target_r,
        "rr": final_target_r,
        "take_profit_1": dynamic_target
        if dynamic_target is not None
        else candidate.get("take_profit_1"),
        "dynamic_geometry_applied": True,
        "dynamic_geometry_policy": geometry_contract.get("selected_policy"),
        "dynamic_execution_policy_id": geometry_contract.get("execution_policy_id"),
        "moonshot_dynamic_execution_router_v4": policy_router_record,
    }
    return canonicalize_candidate_geometry(
        candidate,
        source="timewarp_dynamic_target_stop_geometry_v4",
    )


def apply_ledger_session_aliases(
    candidate: Mapping[str, Any],
    *,
    decision_time_utc: str,
) -> dict[str, Any]:
    """Rewrite session fields exactly as the ledger alias pass does.

    Mirrors ``ledger_namespace_alias_fields`` lines 70547-70576: the executable
    session namespace resolves through ``authority_execution_session_fields``
    (kill zone -> session bucket -> ... -> utc hour bucket -> derived session)
    and, when the route session is ``off_configured_session`` but the UTC hour
    bucket exists, becomes ``moonshot_hHH_HH`` — the value the sealed funnel
    rows carry and the model's ``utc_session`` categories were fitted on.
    ``route_session`` keeps the raw provenance value, exactly as the ledger
    rows do.
    """

    row = dict(candidate)
    authority_session_fields = _tw.authority_execution_session_fields(
        row,
        decision_time_utc=decision_time_utc,
    )
    raw_route_session = str(
        authority_session_fields.get("route_session_raw") or ""
    ).strip()
    applied_route_session = str(
        _tw.first_present(
            authority_session_fields.get("authority_session"), raw_route_session
        )
        or ""
    ).strip()
    raw_session_bucket = _tw.configured_execution_session_token(
        row.get("session_bucket")
    )
    raw_kill_zone = _tw.configured_execution_session_token(row.get("kill_zone"))
    session_bucket = str(
        _tw.first_present(raw_session_bucket, applied_route_session, raw_route_session)
        or ""
    ).strip()
    kill_zone = str(
        _tw.first_present(
            raw_kill_zone, raw_session_bucket, applied_route_session, raw_route_session
        )
        or ""
    ).strip()
    if session_bucket:
        row["session_bucket"] = session_bucket
        row["session"] = session_bucket
    if kill_zone:
        row["kill_zone"] = kill_zone
    if raw_route_session:
        row["route_session"] = raw_route_session
    row["authority_session"] = authority_session_fields.get("authority_session")
    row["authority_session_source"] = authority_session_fields.get(
        "authority_session_source"
    )
    row["authority_session_tokens"] = list(
        authority_session_fields.get("authority_session_tokens") or []
    )
    if authority_session_fields.get("utc_hour_bucket"):
        row["utc_hour_bucket"] = authority_session_fields["utc_hour_bucket"]
    return row


def stamp_preselector_admission(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Validate + stamp the occurrence BEFORE any decision transform.

    Verbatim semantics of ``evaluate_candidate_v4``'s pre-selector block: the
    declared occurrence key must re-derive from the untransformed candidate;
    the admission stamp then lets the post-transform derivation accept the
    declared fingerprint (``allow_validated_post_source_safe_transform``) —
    which is exactly how the sealed funnel rows kept their generation-time
    occurrence keys through the dynamic-geometry retarget.
    """

    candidate = dict(candidate)
    declared = str(candidate.get(CANDIDATE_OCCURRENCE_KEY_FIELD) or "").strip()
    verified = candidate_occurrence_key_from_fields(candidate)
    if not declared or not verified or verified != declared:
        raise ValueError("candidate_source_safe_occurrence_invalid_before_selector")
    candidate["candidate_source_safe_admission_status"] = (
        "validated_immediately_preselector"
    )
    candidate["candidate_source_safe_admission_fingerprint_sha256"] = candidate.get(
        CANDIDATE_SOURCE_SAFE_FINGERPRINT_FIELD
    )
    return candidate


def mint_occurrence_identity(
    candidate: Mapping[str, Any],
    *,
    decision_time_utc: str,
) -> dict[str, Any]:
    """Finalize the canonical occurrence identity on the POST-transform row.

    Mirrors the candidate-ledger identity stamp: derivation runs with
    ``allow_validated_post_source_safe_transform=True`` against the admission
    stamp set by :func:`stamp_preselector_admission`, so the occurrence key is
    the generation-time key — identical to the sealed replay's behavior.  On
    identity failure the candidate comes back with an explicit unmintable
    status; the runner excludes it (the funnel's ``_occurrence`` contract
    would refuse it anyway) and logs the reason.
    """

    candidate = dict(candidate)
    candidate.setdefault("candidate_instance_time_utc", decision_time_utc)
    identity = _tw.canonical_replay_candidate_instance_fields(
        candidate, decision_time_utc=decision_time_utc
    )
    key = identity.get("canonical_replay_candidate_instance_key")
    status = identity.get("candidate_instance_identity_status")
    if not key:
        derived = candidate_occurrence_key_from_fields(
            candidate, allow_validated_post_source_safe_transform=True
        )
        key = derived or None
        if key and not status:
            status = "materialized"
    candidate["canonical_replay_candidate_instance_key"] = key
    candidate["candidate_instance_identity_status"] = status or (
        "forward_shadow_identity_unmintable" if not key else "materialized"
    )
    return candidate
