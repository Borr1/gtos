"""Broker-inert, default-off P1 complete-path adapter.

This module is deliberately an in-memory projection.  It has no CLI, writer,
network client, broker handle, configuration loader, or runtime discovery.  A
caller must explicitly enable it and supply the four exact in-module,
source-bound stage callables.  Historical P1 execution remains blocked by
source conformance.

The market preimage mirrors the request field names at reference SHA-256
``afb81e734e2d...``.  The limit preimage mirrors the internal pending-intent
fields at that same reference.  The live-capable reference module is never
imported; values that depend on an account profile are injected as inert,
hash-bound research facts.  Volume is never derived in this lane.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
import datetime as dt
import hashlib
import json
import math
from typing import Any

from src.components.current_breaker_re_entry_repair import (
    TRANSFORM_ID as BREAKER_TRANSFORM_ID,
    CurrentBreakerRepairError,
    apply_current_breaker_re_entry_repair,
)
from src.research_infra.exit_overlay import (
    ExitOverlaySpec,
    ExitPathPoint,
    SignedM1Bar,
    replay_m1_conservative,
    replay_signed_path,
)
from src.research_infra.train_engine.decision_semantics import (
    COST_COMPONENT_TOLERANCE_R,
    normalize_evidence_row,
)


SCHEMA = "gtos-wave20-p1-complete-path-shadow-v1"
DEFAULT_ENABLED = False
EXECUTION_AUTHORITY = False
ACTIVATION_AUTHORITY = False
RESULT_BEARING_SCIENCE_EXECUTED = False

FIXED_BREAKER_MEMBER = "cq_current_breaker_re_entry_inverted_5d_stop_0p25d"
FIXED_BREAKER_MEMBER_RECORD = {
    "basis": "Session CQ's predeclared S0R0 true-UTC January path grid: inverted current-breaker re-entry, fixed entry, target 5D, stop 0.25D.",
    "declared_at": "2026-08-01",
    "graduated_by": "Session CQ (wave 18)",
    "graduation_candidate_id": "eca3498b7579f9fc",
    "graduation_spec_digest": "b6c3953771cb5bd6feb38ab4db902db96a6c9453688da285705bdf9c03f7e4ec",
    "look_taken": True,
    "name": FIXED_BREAKER_MEMBER,
    "source": "docs/audits/fable5-vision-audit-20260725/phase18/receipts/CQ_CURRENT_BREAKER_REPAIR_V1.json",
    "status": "declared",
}
FIXED_BREAKER_MEMBER_CANONICAL_SHA256 = (
    "0de66ebe5b67e7b3352d98624acb50c69ab116b1c46d58c422b887e5583a650f"
)
FROZEN_GATE_DISPOSITION = "RATIFIED_GATE_ADMIT_DOSSIER_REQUIRED_NOT_ARMED"
VOLUME_STATUS = "NOT_EVALUABLE_OWNER_INPUT_REQUIRED"

STAGES = (
    "source_opportunity",
    "candidate_generation",
    "fixed_breaker_transform",
    "permission",
    "dynamic_router",
    "scheduler_capture_only",
    "order_preimage",
    "fill_or_no_fill",
    "hde_cost",
    "hdf_exit_or_terminal",
    "unchanged_frozen_gate_disposition",
)

IDENTITY_FIELDS = (
    "source_window_id",
    "source_opportunity_id",
    "candidate_id",
    "symbol",
    "side",
    "decision_time_utc",
    "account_scope",
)

ALLOWED_SOURCE_WINDOWS = frozenset({"january_2026", "april_2026", "may_2026"})
COMMISSIONED_SOURCE_WINDOWS = {
    "january_2026": ("2026-01-01", "2026-01-30"),
    "april_2026": ("2026-04-01", "2026-04-30"),
    "may_2026": ("2026-05-01", "2026-05-30"),
}
FEBRUARY_WINDOW = "february_2026"
FEBRUARY_ATTRIBUTION_PURPOSE = "attribution_only_metadata"


class ShadowRefusal(ValueError):
    """A fail-closed, non-executing P1 refusal."""


class K1StaleRefusal(ShadowRefusal):
    """A learned path would invalidate K1 and must stop the whole run."""


@dataclass(frozen=True)
class CompositeIdentity:
    source_window_id: str
    source_opportunity_id: str
    candidate_id: str
    symbol: str
    side: str
    decision_time_utc: str
    account_scope: str

    @classmethod
    def from_opportunity(cls, row: Mapping[str, Any]) -> "CompositeIdentity":
        missing = [field for field in IDENTITY_FIELDS if not str(row.get(field) or "").strip()]
        if missing:
            raise ShadowRefusal("composite_identity_missing:" + ",".join(missing))
        side = str(row["side"]).upper()
        if side not in {"LONG", "SHORT"}:
            raise ShadowRefusal(f"composite_identity_side_invalid:{side}")
        return cls(
            source_window_id=str(row["source_window_id"]),
            source_opportunity_id=str(row["source_opportunity_id"]),
            candidate_id=str(row["candidate_id"]),
            symbol=str(row["symbol"]),
            side=side,
            decision_time_utc=str(row["decision_time_utc"]),
            account_scope=str(row["account_scope"]),
        )

    def as_dict(self) -> dict[str, str]:
        return asdict(self)

    def key(self) -> tuple[str, ...]:
        values = self.as_dict()
        return tuple(values[field] for field in IDENTITY_FIELDS)


@dataclass(frozen=True)
class ShadowDependencies:
    """The four route surfaces, all identity-bound by the runner before use."""

    generate_candidate: Callable[[Mapping[str, Any]], Iterable[Mapping[str, Any]]]
    dynamic_router: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]
    scheduler_capture: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]
    fill_or_no_fill: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]
    broker_inert: bool = True


def _jsonable(value: Any, active: set[int] | None = None) -> Any:
    active = set() if active is None else active
    is_container = is_dataclass(value) or isinstance(
        value, (Mapping, list, tuple, set)
    )
    marker = id(value)
    if is_container:
        if marker in active:
            raise ShadowRefusal("canonical_payload_cycle")
        active.add(marker)
    try:
        if is_dataclass(value):
            return _jsonable(asdict(value), active)
        if isinstance(value, Mapping):
            return {
                str(key): _jsonable(item, active) for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [_jsonable(item, active) for item in value]
        if isinstance(value, set):
            return sorted(_jsonable(item, active) for item in value)
        if isinstance(value, float) and not math.isfinite(value):
            raise ShadowRefusal("canonical_payload_nonfinite")
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        raise ShadowRefusal(f"canonical_payload_unsupported:{type(value).__name__}")
    finally:
        if is_container:
            active.remove(marker)


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(
        _jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


if canonical_sha256(FIXED_BREAKER_MEMBER_RECORD) != FIXED_BREAKER_MEMBER_CANONICAL_SHA256:
    raise RuntimeError("fixed_breaker_member_record_canonical_hash_mismatch")


def refuse_external_operation(operation: str) -> None:
    """Refuse any operation outside deterministic in-memory projection."""

    normalized = str(operation or "").strip().lower().replace("-", "_")
    allowed = {"in_memory_projection", "synthetic_known_answer"}
    if normalized not in allowed:
        raise ShadowRefusal(f"forbidden_external_operation:{normalized}")


def _source_scope_refusal(*, path: str, window_id: str, purpose: str) -> str | None:
    path_text = str(path).lower().replace("\\", "/")
    for encoded, decoded in (
        ("%2e", "."),
        ("%2f", "/"),
        ("%5c", "/"),
        ("%2d", "-"),
        ("%5f", "_"),
    ):
        path_text = path_text.replace(encoded, decoded)
    path_parts = path_text.split("/")
    path_tokens = "".join(
        character if character.isalnum() else "_" for character in path_text
    )
    while "__" in path_tokens:
        path_tokens = path_tokens.replace("__", "_")
    combined = " ".join((path_tokens, str(window_id), str(purpose))).lower()
    normalized_window = str(window_id).strip().lower()
    normalized_purpose = str(purpose).strip().lower()

    if any(token in path_tokens for token in ("march", "2026_03", "202603")):
        return "march_2026_read_forbidden"
    if "live_forward" in path_tokens:
        return "live_forward_read_forbidden"
    if any(
        token in path_tokens for token in ("february", "2026_02", "202602")
    ) and normalized_window != FEBRUARY_WINDOW:
        return "february_window_alias_forbidden"
    if ".." in path_parts:
        return "source_path_alias_forbidden"

    if normalized_window == FEBRUARY_WINDOW:
        if normalized_purpose != FEBRUARY_ATTRIBUTION_PURPOSE:
            return "february_economics_or_selection_forbidden"
        return None
    if normalized_window not in ALLOWED_SOURCE_WINDOWS:
        if "march" in combined:
            return "march_2026_read_forbidden"
        if "live_forward" in combined or "live-forward" in combined:
            return "live_forward_read_forbidden"
        return f"source_window_not_admitted:{normalized_window}"

    forbidden_scopes = {
        "candidate_breadth": "candidate_breadth_forbidden",
        "breadth_expansion": "candidate_breadth_forbidden",
        "alternate_family": "alternate_family_forbidden",
        "post_hoc_drop": "post_hoc_drop_forbidden",
        "o1": "o1_scope_forbidden",
        "c0": "c0_scope_forbidden",
        "n1": "n1_scope_forbidden",
        "fc2": "fc2_scope_forbidden",
    }
    for token, reason in forbidden_scopes.items():
        if token in combined:
            return reason
    return None


def guarded_source_read(
    path: str,
    *,
    window_id: str,
    purpose: str,
    reader: Callable[[str], Any],
) -> Any:
    """Validate source scope before invoking an injected read function."""

    reason = _source_scope_refusal(path=path, window_id=window_id, purpose=purpose)
    if reason is not None:
        raise ShadowRefusal(reason)
    return reader(path)


_LEARNED_AUTHORITY_KEYS = frozenset(
    {
        "candidate_probability",
        "learned_probability",
        "model_probability",
        "predicted_value",
        "learned_value",
        "value_model_score",
    }
)


def _normalized_field_name(value: Any) -> str:
    text = str(value)
    normalized: list[str] = []
    for index, character in enumerate(text):
        if (
            character.isupper()
            and index
            and text[index - 1].isalnum()
            and text[index - 1].islower()
        ):
            normalized.append("_")
        normalized.append(character.lower() if character.isalnum() else "_")
    collapsed = "".join(normalized)
    while "__" in collapsed:
        collapsed = collapsed.replace("__", "_")
    return collapsed.strip("_")


def _assert_no_learned_authority(
    value: Any, prefix: str = "", active: set[int] | None = None
) -> None:
    active = set() if active is None else active
    if isinstance(value, (Mapping, list, tuple)):
        marker = id(value)
        if marker in active:
            raise ShadowRefusal("canonical_payload_cycle")
        active.add(marker)
        try:
            if isinstance(value, Mapping):
                for key, item in value.items():
                    key_text = str(key)
                    path = f"{prefix}.{key_text}" if prefix else key_text
                    if _normalized_field_name(key_text) in _LEARNED_AUTHORITY_KEYS:
                        raise K1StaleRefusal(
                            f"k1_learned_authority_forbidden:{path}"
                        )
                    _assert_no_learned_authority(item, path, active)
            else:
                for index, item in enumerate(value):
                    _assert_no_learned_authority(
                        item, f"{prefix}[{index}]", active
                    )
        finally:
            active.remove(marker)


_PERMISSION_REQUIRED = {
    "session_state": ("asof_utc", "session_open", "daily_loss_blocked"),
    "account_headroom": (
        "snapshot_status",
        "daily_headroom_pct",
        "overall_headroom_pct",
    ),
    "symbol_state": ("symbol", "trade_mode", "position_conflict"),
    "mt5_interface_response": ("interface_status", "symbol_visible"),
}


def evaluate_inert_permission(inputs: Any) -> dict[str, Any]:
    """Evaluate deterministic, in-memory permission facts and fail closed."""

    if not isinstance(inputs, Mapping):
        return {
            "status": "REFUSED",
            "reason": "permission_inputs_not_mapping",
            "missing_fields": [],
        }
    missing: list[str] = []
    for group, fields in _PERMISSION_REQUIRED.items():
        block = inputs.get(group)
        if not isinstance(block, Mapping):
            missing.append(group)
            continue
        for field in fields:
            if field not in block or block[field] is None:
                missing.append(f"{group}.{field}")
    if missing:
        return {
            "status": "REFUSED",
            "reason": "permission_missing_required_field:" + ",".join(missing),
            "missing_fields": missing,
        }

    session = inputs["session_state"]
    account = inputs["account_headroom"]
    symbol = inputs["symbol_state"]
    interface = inputs["mt5_interface_response"]
    headroom: dict[str, float] = {}
    for field in ("daily_headroom_pct", "overall_headroom_pct"):
        value = account[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return {
                "status": "REFUSED",
                "reason": f"permission_invalid_numeric:account_headroom.{field}",
                "missing_fields": [],
            }
        number = float(value)
        if not math.isfinite(number):
            return {
                "status": "REFUSED",
                "reason": f"permission_invalid_numeric:account_headroom.{field}",
                "missing_fields": [],
            }
        headroom[field] = number
    checks = (
        (session["session_open"] is True, "permission_session_closed"),
        (session["daily_loss_blocked"] is False, "permission_daily_loss_blocked"),
        (account["snapshot_status"] == "VALID", "permission_account_snapshot_invalid"),
        (headroom["daily_headroom_pct"] >= 0.0, "permission_daily_headroom_negative"),
        (headroom["overall_headroom_pct"] >= 0.0, "permission_overall_headroom_negative"),
        (symbol["trade_mode"] == "ENABLED", "permission_symbol_trade_mode_blocked"),
        (symbol["position_conflict"] is False, "permission_position_conflict"),
        (interface["interface_status"] == "INERT_OK", "permission_interface_not_inert_ok"),
        (interface["symbol_visible"] is True, "permission_symbol_not_visible"),
    )
    for passed, reason in checks:
        if not passed:
            return {"status": "REFUSED", "reason": reason, "missing_fields": []}
    return {
        "status": "PERMITTED",
        "reason": "deterministic_in_memory_permission_pass",
        "missing_fields": [],
    }


def _required_finite(row: Mapping[str, Any], field: str) -> float:
    value = row.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ShadowRefusal(f"order_preimage_invalid_numeric:{field}")
    number = float(value)
    if not math.isfinite(number):
        raise ShadowRefusal(f"order_preimage_invalid_numeric:{field}")
    return number


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value
    return len(text) == 64 and all(character in "009abcdef" for character in text)


def project_order_preimage(
    candidate: Mapping[str, Any],
    *,
    order_kind: str,
    account_snapshot: Mapping[str, Any],
    account_scope: str,
) -> dict[str, Any]:
    """Project market-request or internal-limit-intent fields without execution."""

    if not isinstance(candidate, Mapping):
        raise ShadowRefusal("order_preimage_candidate_not_mapping")
    if not isinstance(account_snapshot, Mapping):
        raise ShadowRefusal("order_preimage_account_snapshot_not_mapping")
    declared_side = str(candidate.get("side") or "").upper()
    declared_direction = str(candidate.get("direction") or "").upper()
    if (
        declared_side
        and declared_direction
        and declared_side != declared_direction
    ):
        raise ShadowRefusal("order_preimage_side_direction_conflict")
    side = declared_side or declared_direction
    if side not in {"LONG", "SHORT"}:
        raise ShadowRefusal(f"order_preimage_side_invalid:{side}")
    candidate_id = str(candidate.get("candidate_id") or "").strip()
    symbol = str(candidate.get("symbol") or "").strip()
    decision_time = str(candidate.get("decision_time_utc") or "").strip()
    if not candidate_id or not symbol or not decision_time:
        raise ShadowRefusal("order_preimage_identity_incomplete")
    entry = _required_finite(candidate, "entry_price")
    stop = _required_finite(candidate, "stop_loss")
    target = _required_finite(candidate, "take_profit_1")
    for field, value in (
        ("entry_price", entry),
        ("stop_loss", stop),
        ("take_profit_1", target),
    ):
        if value <= 0.0:
            raise ShadowRefusal(f"order_preimage_nonpositive:{field}")
    geometry_valid = (
        stop < entry < target if side == "LONG" else target < entry < stop
    )
    if not geometry_valid:
        raise ShadowRefusal("order_preimage_geometry_invalid")

    declared_scope = str(account_snapshot.get("account_scope") or "")
    if declared_scope != account_scope:
        raise ShadowRefusal(
            f"order_preimage_account_scope_mismatch:{declared_scope}:{account_scope}"
        )
    missing_authority = []
    for field in ("profile_snapshot_sha256", "symbol_snapshot_sha256"):
        value = account_snapshot.get(field)
        if not str(value or "").strip():
            missing_authority.append(field)
        elif not _is_sha256(value):
            missing_authority.append(f"invalid_sha256:{field}")
    authority_status = (
        "INJECTED_RESEARCH_SNAPSHOT_BOUND"
        if not missing_authority
        else "NOT_EVALUABLE_INERT_SNAPSHOT_AUTHORITY_REQUIRED"
    )
    common = {
        "schema": "gtos-wave20-p1-order-preimage-v1",
        "executable": False,
        "account_scope": account_scope,
        "account_profile": account_snapshot.get("profile_id"),
        "account_authority_status": authority_status,
        "missing_account_authority": missing_authority,
        "symbol": account_snapshot.get("broker_symbol") or symbol,
        "source_symbol": symbol,
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "volume": None,
        "volume_status": VOLUME_STATUS,
    }
    kind = str(order_kind).strip().lower()
    if kind == "market":
        return {
            **common,
            "request_kind": "market",
            "action": "TRADE_ACTION_DEAL",
            "type": "ORDER_TYPE_BUY" if side == "LONG" else "ORDER_TYPE_SELL",
            "price": entry,
            "sl": stop,
            "tp": target,
            "deviation": account_snapshot.get("deviation_points"),
            "magic": account_snapshot.get("magic"),
            "comment": account_snapshot.get("comment"),
            "type_time": "ORDER_TIME_GTC",
            "type_filling": account_snapshot.get("filling_mode"),
            "reference_field_mapping": {
                "price": "candidate.entry_price",
                "sl": "candidate.stop_loss",
                "tp": "candidate.take_profit_1",
                "type": "candidate.side",
                "symbol": "injected_snapshot.broker_symbol",
                "deviation": "injected_snapshot.deviation_points",
                "magic": "injected_snapshot.magic",
                "comment": "injected_snapshot.comment",
                "type_filling": "injected_snapshot.filling_mode",
            },
        }
    if kind == "limit":
        return {
            **common,
            "request_kind": "limit",
            "action": "STORE_INTERNAL_PENDING_LIMIT_INTENT",
            "direction": side,
            "limit_price": entry,
            "stop_loss": stop,
            "take_profit_1": target,
            "pending_order_mode": "internal_software_limit",
            "broker_pending_order_created": False,
            "native_pending_order_type": None,
            "reference_field_mapping": {
                "direction": "candidate.side",
                "limit_price": "candidate.entry_price",
                "stop_loss": "candidate.stop_loss",
                "take_profit_1": "candidate.take_profit_1",
                "candidate_id": "candidate.candidate_id",
                "decision_time_utc": "candidate.decision_time_utc",
            },
        }
    raise ShadowRefusal(f"order_preimage_kind_unsupported:{kind}")


def scheduler_capture_only(
    packet: Mapping[str, Any], *, incoming_disposition: str
) -> dict[str, Any]:
    """Capture scheduler telemetry while preserving the incoming disposition."""

    if not isinstance(packet, Mapping):
        raise ShadowRefusal("scheduler_capture_packet_not_mapping")
    _assert_no_learned_authority(packet)
    return {
        "mode": "CAPTURE_ONLY",
        "effect": "NONE",
        "captured_packet": dict(packet),
        "input_disposition": incoming_disposition,
        "output_disposition": incoming_disposition,
        "selection_authority": False,
        "ranking_authority": False,
        "suppression_authority": False,
        "sizing_authority": False,
    }


def project_hde_cost(row: Mapping[str, Any]) -> dict[str, Any]:
    """Project HDE's unchanged complete/incomplete/refused cost authority."""

    normalized = normalize_evidence_row(row)
    return {
        "state": normalized.get("cost_component_state"),
        "candidate_sum_r": normalized.get("cost_component_candidate_sum_r"),
        "authoritative_cost_r": normalized.get("authoritative_cost_r"),
        "refusal_reasons": list(normalized.get("cost_decision_refusal_reasons") or ()),
        "tolerance_r": COST_COMPONENT_TOLERANCE_R,
    }


def project_hdf_exit(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Replay one synthetic ordered path through the integrated HDF authority."""

    spec = ExitOverlaySpec.from_protocol_cell(payload.get("cell") or {})
    points = tuple(ExitPathPoint(**dict(row)) for row in payload.get("points") or ())
    result = replay_signed_path(
        spec,
        points,
        decision_time_us=int(payload["decision_time_us"]),
        cost_r=float(payload["cost_r"]),
        source_mode=str(payload.get("source_mode") or "SYNTHETIC"),
    )
    return asdict(result)


def project_hdf_m1_exit(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Replay synthetic M1 bars through HDF's conservative two-ordering rule."""

    spec = ExitOverlaySpec.from_protocol_cell(payload.get("cell") or {})
    bars = tuple(SignedM1Bar(**dict(row)) for row in payload.get("bars") or ())
    result = replay_m1_conservative(
        spec,
        bars,
        decision_time_us=int(payload["decision_time_us"]),
        cost_r=float(payload["cost_r"]),
    )
    return asdict(result)


def account_claim_scope(account_scope: str) -> dict[str, Any]:
    normalized = str(account_scope).strip().lower()
    if normalized == "operator_profile":
        return {
            "account_scope": normalized,
            "scope": "SOLE_FUTURE_ECONOMIC_SCOPE",
            "economic_verdict_emitted": False,
            "mechanical_compatibility_allowed": True,
        }
    if normalized == "redacted_account":
        return {
            "account_scope": normalized,
            "scope": "MECHANICAL_ONLY",
            "economic_gate_allowed": False,
            "promotion_or_veto_allowed": False,
            "economic_verdict_emitted": False,
            "mechanical_compatibility_allowed": True,
        }
    raise ShadowRefusal(f"account_scope_unrecognized:{normalized}")


def _stage_row(
    identity: CompositeIdentity,
    *,
    stage: str,
    disposition: str,
    reason: str,
    input_payload: Any,
    output_payload: Any,
) -> dict[str, Any]:
    return {
        "composite_identity": identity.as_dict(),
        "stage": stage,
        "disposition": disposition,
        "reason": reason,
        "asof_utc": identity.decision_time_utc,
        "input_sha256": canonical_sha256(input_payload),
        "output_sha256": canonical_sha256(output_payload),
    }


def _detached_mapping(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ShadowRefusal(f"{label}_not_mapping")
    detached = _jsonable(value)
    if not isinstance(detached, dict):
        raise ShadowRefusal(f"{label}_not_mapping")
    return detached


def inert_admit_unchanged_router(
    candidate: Mapping[str, Any], source: Mapping[str, Any]
) -> dict[str, Any]:
    """The only admitted P1 router: pure, outcome-blind, and geometry-preserving."""

    del source
    routed_candidate = _detached_mapping(candidate, label="inert_router_candidate")
    _assert_no_learned_authority(routed_candidate)
    return {
        "candidate": routed_candidate,
        "disposition": "ADMIT",
        "reason": "fixed_preregistered_member_admit_unchanged",
    }


def source_bound_candidate_generator(
    source: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Project only the candidate row embedded in the hash-bound source record."""

    value = source.get("synthetic_candidate")
    if value is None:
        return []
    return [_detached_mapping(value, label="source_bound_candidate")]


def inert_scheduler_capture(
    candidate: Mapping[str, Any], source: Mapping[str, Any]
) -> dict[str, Any]:
    """Create deterministic capture telemetry without selection or sizing authority."""

    return {
        "capture_id": str(source.get("source_opportunity_id") or ""),
        "candidate_sha256": canonical_sha256(candidate),
        "would_disposition": "OBSERVE_ONLY",
        "would_rank": None,
        "would_size": None,
    }


def source_bound_fill_projection(
    preimage: Mapping[str, Any], source: Mapping[str, Any]
) -> dict[str, Any]:
    """Read the future result lane's explicit inert fill projection only."""

    del preimage
    return _detached_mapping(
        source.get("synthetic_fill") or {}, label="source_bound_fill_projection"
    )


def _dependency_exception_reason(exc: Exception) -> str:
    return f"dependency_exception:{type(exc).__name__}"


def _validate_source_identity_scope(identity: CompositeIdentity) -> None:
    bounds = COMMISSIONED_SOURCE_WINDOWS.get(identity.source_window_id)
    if bounds is None:
        raise ShadowRefusal(
            f"source_window_not_admitted:{identity.source_window_id}"
        )
    text = identity.decision_time_utc.strip()
    parse_text = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = dt.datetime.fromisoformat(parse_text)
    except ValueError as exc:
        raise ShadowRefusal("source_decision_time_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise ShadowRefusal("source_decision_time_not_true_utc")
    observed_date = parsed.astimezone(dt.timezone.utc).date().isoformat()
    if not bounds[0] <= observed_date <= bounds[1]:
        raise ShadowRefusal(
            "source_decision_outside_commissioned_window:"
            f"{identity.source_window_id}:{observed_date}"
        )


def _candidate_identity_mismatch(
    candidate: Mapping[str, Any], identity: CompositeIdentity
) -> str | None:
    declared_side = str(candidate.get("side") or "").upper()
    declared_direction = str(candidate.get("direction") or "").upper()
    if (
        declared_side
        and declared_direction
        and declared_side != declared_direction
    ):
        return "side_direction"
    candidate_side = declared_side or declared_direction
    expected = {
        "candidate_id": identity.candidate_id,
        "symbol": identity.symbol,
        "side": identity.side,
        "decision_time_utc": identity.decision_time_utc,
    }
    observed = {
        "candidate_id": str(candidate.get("candidate_id") or ""),
        "symbol": str(candidate.get("symbol") or ""),
        "side": candidate_side,
        "decision_time_utc": str(candidate.get("decision_time_utc") or ""),
    }
    for field in ("candidate_id", "symbol", "side", "decision_time_utc"):
        if observed[field] != expected[field]:
            return field
    if str(candidate.get("origin_family") or "") != "current_breaker_re_entry":
        return "origin_family"
    return None


def _routed_candidate_identity_mismatch(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> str | None:
    for field in ("candidate_id", "symbol", "side", "decision_time_utc"):
        before_value = str(before.get(field) or "")
        after_value = str(after.get(field) or "")
        if field == "side":
            before_value = before_value.upper()
            after_value = after_value.upper()
        if before_value != after_value:
            return field
    return None


def run_complete_path_shadow(
    source_opportunities: Iterable[Mapping[str, Any]],
    *,
    enabled: bool = DEFAULT_ENABLED,
    dependencies: ShadowDependencies | None = None,
) -> dict[str, Any]:
    """Run an explicitly enabled, synthetic complete-path disposition audit."""

    explicitly_enabled = enabled is True
    base = {
        "schema": SCHEMA,
        "enabled": explicitly_enabled,
        "execution_authority": EXECUTION_AUTHORITY,
        "activation_authority": ACTIVATION_AUTHORITY,
        "result_bearing_science_executed": RESULT_BEARING_SCIENCE_EXECUTED,
        "fixed_breaker_member": FIXED_BREAKER_MEMBER,
        "fixed_breaker_member_canonical_sha256": FIXED_BREAKER_MEMBER_CANONICAL_SHA256,
        "frozen_gate_disposition": FROZEN_GATE_DISPOSITION,
    }
    if not explicitly_enabled:
        return {
            **base,
            "status": "DEFAULT_OFF",
            "source_opportunity_count": 0,
            "stage_row_count": 0,
            "stage_ledger": [],
            "missed_opportunity_ledger": [],
        }
    if dependencies is None:
        raise ShadowRefusal("enabled_shadow_dependencies_required")
    if dependencies.broker_inert is not True:
        raise ShadowRefusal("dependency_contract_not_broker_inert")

    sources = [
        _detached_mapping(row, label="source_opportunity")
        for row in source_opportunities
    ]
    identities = [CompositeIdentity.from_opportunity(row) for row in sources]
    for identity in identities:
        _validate_source_identity_scope(identity)
        account_claim_scope(identity.account_scope)
    keys = [identity.key() for identity in identities]
    if len(set(keys)) != len(keys):
        raise ShadowRefusal("duplicate_source_composite_identity")

    stage_ledger: list[dict[str, Any]] = []
    missed: list[dict[str, Any]] = []

    for source, identity in zip(sources, identities):
        first_miss: tuple[str, str] | None = None
        current: Any = source
        router_disposition = "UNSET"
        fill_status = "UNSET"
        authoritative_cost: float | None = None

        def record(stage: str, disposition: str, reason: str, output: Any) -> None:
            nonlocal current
            stage_ledger.append(
                _stage_row(
                    identity,
                    stage=stage,
                    disposition=disposition,
                    reason=reason,
                    input_payload=current,
                    output_payload=output,
                )
            )
            current = output

        def refuse(stage: str, reason: str, output: Any | None = None) -> None:
            nonlocal first_miss
            refused_output = output if output is not None else {"status": "REFUSED", "reason": reason}
            record(stage, "REFUSED", reason, refused_output)
            first_miss = (stage, reason)
            missed.append(
                {
                    "composite_identity": identity.as_dict(),
                    "first_missing_stage": stage,
                    "reason": reason,
                    "asof_utc": identity.decision_time_utc,
                    "input_sha256": stage_ledger[-1]["input_sha256"],
                }
            )

        def skip(stage: str) -> None:
            assert first_miss is not None
            miss_stage, miss_reason = first_miss
            record(
                stage,
                "NOT_REACHED_PRIOR_STAGE_MISS",
                f"prior_stage_miss:{miss_stage}:{miss_reason}",
                current,
            )

        record(
            "source_opportunity",
            "OBSERVED",
            "source_opportunity_identity_bound",
            source,
        )

        try:
            if dependencies.generate_candidate is not source_bound_candidate_generator:
                raise ShadowRefusal("candidate_generator_dependency_not_bound")
            generated_raw = dependencies.generate_candidate(
                _detached_mapping(source, label="candidate_generation_source")
            )
            if isinstance(generated_raw, Mapping):
                raise ShadowRefusal("candidate_generation_result_must_be_iterable_of_rows")
            generated: list[dict[str, Any]] = []
            for row in generated_raw:
                generated.append(
                    _detached_mapping(row, label="candidate_generation_row")
                )
            if len(generated) != 1:
                raise ShadowRefusal(f"candidate_generation_candidate_count_not_one:{len(generated)}")
            candidate = generated[0]
            _assert_no_learned_authority(candidate)
            mismatch = _candidate_identity_mismatch(candidate, identity)
            if mismatch is not None:
                raise ShadowRefusal(
                    f"candidate_generation_identity_mismatch:{mismatch}"
                )
            record(
                "candidate_generation",
                "GENERATED_ONE",
                "exactly_one_source_candidate_generated",
                candidate,
            )
        except K1StaleRefusal:
            raise
        except ShadowRefusal as exc:
            refuse("candidate_generation", str(exc))
            candidate = {}
        except Exception as exc:
            refuse("candidate_generation", _dependency_exception_reason(exc))
            candidate = {}

        if first_miss is not None:
            skip("fixed_breaker_transform")
        else:
            try:
                transformed = apply_current_breaker_re_entry_repair(candidate, enabled=True)
                if transformed.get("candidate_transform_id") != BREAKER_TRANSFORM_ID:
                    raise ShadowRefusal("fixed_breaker_transform_not_applied")
                transformed["decision_time_utc"] = identity.decision_time_utc
                record(
                    "fixed_breaker_transform",
                    "APPLIED",
                    FIXED_BREAKER_MEMBER,
                    transformed,
                )
                candidate = transformed
            except K1StaleRefusal:
                raise
            except (ShadowRefusal, CurrentBreakerRepairError) as exc:
                refuse("fixed_breaker_transform", str(exc))
            except Exception as exc:
                refuse(
                    "fixed_breaker_transform", _dependency_exception_reason(exc)
                )

        if first_miss is not None:
            skip("permission")
        else:
            permission = evaluate_inert_permission(source.get("permission_inputs") or {})
            if permission["status"] != "PERMITTED":
                refuse("permission", str(permission["reason"]), permission)
            else:
                record("permission", "PERMITTED", str(permission["reason"]), permission)

        if first_miss is not None:
            skip("dynamic_router")
        else:
            try:
                if dependencies.dynamic_router is not inert_admit_unchanged_router:
                    raise ShadowRefusal("dynamic_router_dependency_not_bound")
                candidate_before_router = canonical_sha256(candidate)
                routed_raw = dependencies.dynamic_router(
                    _detached_mapping(candidate, label="dynamic_router_candidate"),
                    _detached_mapping(source, label="dynamic_router_source"),
                )
                routed = _detached_mapping(
                    routed_raw, label="dynamic_router_result"
                )
                _assert_no_learned_authority(routed)
                router_disposition = str(routed.get("disposition") or "").upper()
                route_reason = str(routed.get("reason") or "dynamic_router_reason_missing")
                if router_disposition not in {"ADMIT", "PASS"}:
                    raise ShadowRefusal(
                        f"dynamic_router_refused:{router_disposition}:{route_reason}"
                    )
                routed_candidate = routed.get("candidate")
                if isinstance(routed_candidate, Mapping):
                    routed_candidate = _detached_mapping(
                        routed_candidate,
                        label="dynamic_router_candidate_result",
                    )
                    mismatch = _routed_candidate_identity_mismatch(
                        candidate, routed_candidate
                    )
                    if mismatch is not None:
                        raise ShadowRefusal(
                            f"dynamic_router_candidate_identity_mismatch:{mismatch}"
                        )
                    if canonical_sha256(routed_candidate) != candidate_before_router:
                        raise ShadowRefusal(
                            "dynamic_router_candidate_mutation_forbidden"
                        )
                    candidate = routed_candidate
                record("dynamic_router", router_disposition, route_reason, routed)
            except K1StaleRefusal:
                raise
            except ShadowRefusal as exc:
                refuse("dynamic_router", str(exc))
            except Exception as exc:
                refuse("dynamic_router", _dependency_exception_reason(exc))

        if first_miss is not None:
            skip("scheduler_capture_only")
        else:
            try:
                if dependencies.scheduler_capture is not inert_scheduler_capture:
                    raise ShadowRefusal("scheduler_capture_dependency_not_bound")
                scheduler_candidate = _detached_mapping(
                    candidate, label="scheduler_candidate"
                )
                scheduler_source = _detached_mapping(
                    source, label="scheduler_source"
                )
                candidate_before = canonical_sha256(scheduler_candidate)
                source_before = canonical_sha256(scheduler_source)
                packet = dependencies.scheduler_capture(
                    scheduler_candidate, scheduler_source
                )
                if (
                    canonical_sha256(scheduler_candidate) != candidate_before
                    or canonical_sha256(scheduler_source) != source_before
                ):
                    raise ShadowRefusal(
                        "scheduler_capture_input_mutation_forbidden"
                    )
                capture = scheduler_capture_only(
                    packet,
                    incoming_disposition=router_disposition,
                )
                if capture["output_disposition"] != router_disposition:
                    raise ShadowRefusal("scheduler_capture_changed_disposition")
                record(
                    "scheduler_capture_only",
                    "CAPTURED_NO_EFFECT",
                    "scheduler_telemetry_captured_without_route_effect",
                    capture,
                )
            except K1StaleRefusal:
                raise
            except ShadowRefusal as exc:
                refuse("scheduler_capture_only", str(exc))
            except Exception as exc:
                refuse(
                    "scheduler_capture_only", _dependency_exception_reason(exc)
                )

        if first_miss is not None:
            skip("order_preimage")
            preimage = {}
        else:
            try:
                preimage = project_order_preimage(
                    candidate,
                    order_kind=str(source.get("order_kind") or ""),
                    account_snapshot=source.get("account_snapshot") or {},
                    account_scope=identity.account_scope,
                )
                if preimage["missing_account_authority"]:
                    raise ShadowRefusal(
                        "order_preimage_account_authority_missing:"
                        + ",".join(preimage["missing_account_authority"])
                    )
                record(
                    "order_preimage",
                    "PROJECTED_INERT",
                    "non_executable_order_preimage_projected",
                    preimage,
                )
            except ShadowRefusal as exc:
                refuse("order_preimage", str(exc))
                preimage = {}

        if first_miss is not None:
            skip("fill_or_no_fill")
        else:
            try:
                if dependencies.fill_or_no_fill is not source_bound_fill_projection:
                    raise ShadowRefusal("fill_projection_dependency_not_bound")
                fill_raw = dependencies.fill_or_no_fill(
                    _detached_mapping(preimage, label="fill_preimage"),
                    _detached_mapping(source, label="fill_source"),
                )
                fill = _detached_mapping(fill_raw, label="fill_result")
                fill_status = str(fill.get("status") or "").upper()
                fill_reason = str(fill.get("reason") or "")
                if fill_status not in {"FILLED", "NO_FILL"}:
                    raise ShadowRefusal(f"fill_or_no_fill_status_invalid:{fill_status}")
                if not fill_reason:
                    raise ShadowRefusal("fill_or_no_fill_reason_missing")
                record("fill_or_no_fill", fill_status, fill_reason, fill)
            except ShadowRefusal as exc:
                refuse("fill_or_no_fill", str(exc))
            except Exception as exc:
                refuse("fill_or_no_fill", _dependency_exception_reason(exc))

        if first_miss is not None:
            skip("hde_cost")
        elif fill_status == "NO_FILL":
            record(
                "hde_cost",
                "NOT_APPLICABLE_NO_FILL",
                "no_fill_has_no_realized_cost_authority",
                {"state": "not_applicable_no_fill", "authoritative_cost_r": None},
            )
        else:
            try:
                cost = project_hde_cost(source.get("hde_cost_input") or {})
                if cost["state"] != "complete":
                    reasons = cost["refusal_reasons"] or [
                        "component_authority_unavailable"
                    ]
                    refuse(
                        "hde_cost",
                        f"hde_cost_{cost['state']}:{reasons[0]}",
                        cost,
                    )
                else:
                    authoritative_cost = float(cost["authoritative_cost_r"])
                    record(
                        "hde_cost",
                        "COMPLETE",
                        "hde_complete_component_sum",
                        cost,
                    )
            except ShadowRefusal as exc:
                refuse("hde_cost", str(exc))
            except Exception as exc:
                refuse("hde_cost", _dependency_exception_reason(exc))

        if first_miss is not None:
            skip("hdf_exit_or_terminal")
        elif fill_status == "NO_FILL":
            record(
                "hdf_exit_or_terminal",
                "NO_FILL_TERMINAL",
                "explicit_no_fill_terminal",
                {"status": "NO_FILL_TERMINAL", "exit_reason": "not_filled"},
            )
        else:
            try:
                hdf_input = _detached_mapping(
                    source.get("hdf_exit_input") or {},
                    label="hdf_exit_input",
                )
                hdf_input["cost_r"] = authoritative_cost
                exit_result = project_hdf_exit(hdf_input)
                if exit_result["status"] != "REPLAYED":
                    refuse(
                        "hdf_exit_or_terminal",
                        f"hdf_exit_source_refused:{exit_result['exit_reason']}",
                        exit_result,
                    )
                else:
                    record(
                        "hdf_exit_or_terminal",
                        "TERMINAL_CAPTURED",
                        str(exit_result["exit_reason"]),
                        exit_result,
                    )
            except ShadowRefusal as exc:
                refuse("hdf_exit_or_terminal", str(exc))
            except Exception as exc:
                refuse(
                    "hdf_exit_or_terminal", _dependency_exception_reason(exc)
                )

        record(
            "unchanged_frozen_gate_disposition",
            "UNCHANGED",
            FROZEN_GATE_DISPOSITION,
            {
                "fixed_breaker_member": FIXED_BREAKER_MEMBER,
                "disposition": FROZEN_GATE_DISPOSITION,
                "armed": False,
            },
        )

    stage_keys = [
        (
            tuple(row["composite_identity"][field] for field in IDENTITY_FIELDS),
            row["stage"],
        )
        for row in stage_ledger
    ]
    expected_rows = len(sources) * len(STAGES)
    if len(stage_ledger) != expected_rows or len(set(stage_keys)) != expected_rows:
        raise ShadowRefusal("stage_ledger_denominator_or_duplicate_invariant_failed")

    return {
        **base,
        "status": (
            "COMPLETE_SYNTHETIC_NO_MISSES"
            if not missed
            else "COMPLETE_SYNTHETIC_WITH_EXPLICIT_MISSES"
        ),
        "source_opportunity_count": len(sources),
        "stage_row_count": len(stage_ledger),
        "stage_ledger": stage_ledger,
        "missed_opportunity_ledger": missed,
    }


__all__ = [
    "ACTIVATION_AUTHORITY",
    "CompositeIdentity",
    "DEFAULT_ENABLED",
    "EXECUTION_AUTHORITY",
    "FIXED_BREAKER_MEMBER",
    "FIXED_BREAKER_MEMBER_RECORD",
    "FIXED_BREAKER_MEMBER_CANONICAL_SHA256",
    "FROZEN_GATE_DISPOSITION",
    "IDENTITY_FIELDS",
    "K1StaleRefusal",
    "RESULT_BEARING_SCIENCE_EXECUTED",
    "STAGES",
    "ShadowDependencies",
    "ShadowRefusal",
    "VOLUME_STATUS",
    "account_claim_scope",
    "canonical_sha256",
    "source_bound_candidate_generator",
    "inert_admit_unchanged_router",
    "inert_scheduler_capture",
    "source_bound_fill_projection",
    "evaluate_inert_permission",
    "guarded_source_read",
    "project_hde_cost",
    "project_hdf_exit",
    "project_hdf_m1_exit",
    "project_order_preimage",
    "refuse_external_operation",
    "run_complete_path_shadow",
    "scheduler_capture_only",
]
