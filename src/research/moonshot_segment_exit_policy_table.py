"""Frozen segment exit-policy table loader and resolver (default-off).

Pure consumer of the ``exit_policy_segment_table_v1`` artifact produced by
``src/research_infra/ultimate_exit_policy_segment_tournament.py``. No files
are written, no broker/MT5/paid-API calls are made, and nothing here changes
runtime behavior on its own: the router only consumes a resolution when the
caller explicitly attaches it to the event under ``segment_policy_resolution``
(see ``moonshot_default_off_policy_router``).

Fail-closed contract: ``load_segment_policy_table`` raises on schema or
sha256-pin mismatch — a corrupt or substituted table never resolves.
Resolution walks the segment hierarchy deterministically:

    leaf (asset_class x origin_family x session_bucket)
    -> asset_class x session_bucket
    -> asset_class
    -> global
    -> default_policy (incumbent) with fallback_level ``global_default``

Only ``promoted: true`` rows participate in the walk; promoted=false rows are
recorded evidence, never routing authority.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

SEGMENT_TABLE_SCHEMA_VERSION = "exit_policy_segment_table_v1"
SEGMENT_LEVEL_ORDER = ("leaf", "asset_class_session", "asset_class", "global")
GLOBAL_DEFAULT_FALLBACK_LEVEL = "global_default"
SESSION_VOCABULARY_UNMAPPED_FALLBACK_LEVEL = "session_vocabulary_unmapped"

# Single canonical session-vocabulary map. The frozen table's keys use raw
# ledger vocabulary ('london', 'ny', 'tokyo', 'off_kz', 'moonshot_hNN_MM'
# hourly buckets); callers may pass config kill-zone vocabulary
# ('london_core', 'new_york', 'tokyo_kz', 'off_configured_session', ...).
# Both sides are normalized through this one map — table match keys at load
# time and query inputs at resolve time — so vocabulary drift can never
# silently fall through to the global default.
_CANONICAL_SESSION_BY_ALIAS = {
    "london": "london",
    "london_core": "london",
    "ny": "ny",
    "ny_core": "ny",
    "new_york": "ny",
    "tokyo": "tokyo",
    "tokyo_kz": "tokyo",
    "asia": "tokyo",
    "off_kz": "off_kz",
    "off_core_session": "off_kz",
    "off_configured_session": "off_kz",
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _norm_origin_family(value: Any) -> str:
    return _norm(value).removeprefix("origin_").removeprefix("current_")


def normalize_session_vocabulary(value: Any) -> Optional[str]:
    """Map raw-ledger or config kill-zone session vocabulary to the canonical
    table vocabulary ('london' | 'ny' | 'tokyo' | 'off_kz').

    ``moonshot_hNN_MM`` hourly buckets pass through unchanged. Unknown or
    empty vocabulary returns ``None`` (fail-visible — the resolver surfaces
    it as ``session_vocabulary_unmapped`` instead of silently defaulting).
    """

    token = _norm(value).replace("-", "_").replace(" ", "_")
    if not token:
        return None
    canonical = _CANONICAL_SESSION_BY_ALIAS.get(token)
    if canonical is not None:
        return canonical
    if token.startswith("moonshot_h"):
        hour_parts = token.removeprefix("moonshot_h").split("_")
        if len(hour_parts) == 2 and all(part.isdigit() for part in hour_parts):
            return token
    return None


def _normalize_segment_session(segment: Any) -> Any:
    """Return ``segment`` with its match session key canonicalized.

    Wildcard (None/empty) session keys stay wildcard. A table key in unknown
    vocabulary is left as-is; it can never equal a canonical query key, so
    such rows are inert rather than silently rerouted.
    """

    if not isinstance(segment, Mapping):
        return segment
    match = segment.get("match")
    if not isinstance(match, Mapping):
        return segment
    raw_session = match.get("session_bucket")
    if _norm(raw_session) == "":
        return segment
    canonical = normalize_session_vocabulary(raw_session)
    if canonical is None or canonical == raw_session:
        return segment
    normalized_match = dict(match)
    normalized_match["session_bucket"] = canonical
    normalized_segment = dict(segment)
    normalized_segment["match"] = normalized_match
    return normalized_segment


def segment_table_validation_errors(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, Mapping):
        return ["table_payload_not_a_mapping"]
    if payload.get("schema_version") != SEGMENT_TABLE_SCHEMA_VERSION:
        errors.append(
            f"schema_version_mismatch_expected_{SEGMENT_TABLE_SCHEMA_VERSION}"
            f"_got_{payload.get('schema_version')}"
        )
    default_policy = payload.get("default_policy")
    if (
        not isinstance(default_policy, Mapping)
        or not default_policy.get("policy_id")
        or not isinstance(default_policy.get("params"), Mapping)
    ):
        errors.append("default_policy_missing_policy_id_or_params")
    segments = payload.get("segments")
    if not isinstance(segments, list):
        errors.append("segments_not_a_list")
        return errors
    for index, segment in enumerate(segments):
        if not isinstance(segment, Mapping):
            errors.append(f"segment_{index}_not_a_mapping")
            continue
        if not segment.get("segment_id"):
            errors.append(f"segment_{index}_missing_segment_id")
        if not isinstance(segment.get("match"), Mapping):
            errors.append(f"segment_{index}_match_not_a_mapping")
        if not segment.get("policy_id"):
            errors.append(f"segment_{index}_missing_policy_id")
        if not isinstance(segment.get("params"), Mapping):
            errors.append(f"segment_{index}_params_not_a_mapping")
        if segment.get("fallback_level") not in SEGMENT_LEVEL_ORDER:
            errors.append(f"segment_{index}_unknown_fallback_level")
        if not isinstance(segment.get("promoted"), bool):
            errors.append(f"segment_{index}_promoted_not_boolean")
    return errors


def load_segment_policy_table(
    path: str | Path,
    expected_sha256: Optional[str] = None,
) -> dict[str, Any]:
    """Load + validate a frozen segment table; optionally pin its sha256.

    Fail-closed: raises ``ValueError`` on sha mismatch or schema violations.
    The returned dict carries ``table_sha256`` (sha256 of the raw file bytes)
    for downstream provenance stamping.
    """

    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and digest != str(expected_sha256).strip().lower():
        raise ValueError(
            "segment_policy_table_sha256_mismatch"
            f"_expected_{str(expected_sha256).strip().lower()}_actual_{digest}"
        )
    payload = json.loads(raw.decode("utf-8"))
    errors = segment_table_validation_errors(payload)
    if errors:
        raise ValueError("segment_policy_table_invalid:" + ";".join(errors))
    table = dict(payload)
    segments = payload.get("segments")
    if isinstance(segments, list):
        table["segments"] = [
            _normalize_segment_session(segment) for segment in segments
        ]
    table["table_sha256"] = digest
    return table


def _match_key(segment: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
    match = segment.get("match")
    match = match if isinstance(match, Mapping) else {}
    raw_session = _norm(match.get("session_bucket")) or None
    session_key: str | None = None
    if raw_session is not None:
        # Canonicalize here too so tables that bypassed the loader still match
        # on canonical vocabulary; unknown table vocabulary stays raw (inert —
        # it can never equal a canonical query key).
        session_key = normalize_session_vocabulary(raw_session) or raw_session
    return (
        _norm(match.get("asset_class")) or None,
        _norm_origin_family(match.get("origin_family")) or None,
        session_key,
    )


def _default_policy_resolution(
    table: Mapping[str, Any],
    *,
    fallback_level: str,
    reason: Optional[str],
) -> dict[str, Any]:
    default_policy = table.get("default_policy")
    default_policy = default_policy if isinstance(default_policy, Mapping) else {}
    default_params = default_policy.get("params")
    return {
        "policy_id": default_policy.get("policy_id"),
        "family": default_policy.get("family"),
        "params": dict(default_params) if isinstance(default_params, Mapping) else {},
        "params_fidelity": None,
        "segment_id": fallback_level,
        "fallback_level": fallback_level,
        "promoted": False,
        "reason": reason,
        "table_sha256": table.get("table_sha256"),
    }


def resolve_segment_policy(
    table: Mapping[str, Any],
    *,
    asset_class: Any,
    origin_family: Any,
    session_bucket: Any,
) -> dict[str, Any]:
    """Resolve one candidate's segment keys to its frozen exit policy.

    Walks the hierarchy deterministically over promoted rows only; ties at a
    level break by sorted ``segment_id``. Unmatched keys fall through to the
    table's ``default_policy`` with fallback_level ``global_default``.

    Session vocabulary is canonicalized through
    ``normalize_session_vocabulary``. An input session that does not
    normalize (unknown vocabulary or empty) never silently falls through:
    it returns the default policy with fallback_level
    ``session_vocabulary_unmapped`` and an explicit ``reason`` so forensic
    joins can count every unmapped event.
    """

    normalized_asset_class = _norm(asset_class) or None
    normalized_origin_family = _norm_origin_family(origin_family) or None
    raw_session_bucket = _norm(session_bucket) or None
    normalized_session_bucket = normalize_session_vocabulary(session_bucket)
    if normalized_session_bucket is None:
        reason = (
            "session_vocabulary_unmapped_empty_input"
            if raw_session_bucket is None
            else f"session_vocabulary_unmapped_unknown_token_{raw_session_bucket}"
        )
        return _default_policy_resolution(
            table,
            fallback_level=SESSION_VOCABULARY_UNMAPPED_FALLBACK_LEVEL,
            reason=reason,
        )

    wanted_by_level = {
        "leaf": (
            normalized_asset_class,
            normalized_origin_family,
            normalized_session_bucket,
        ),
        "asset_class_session": (normalized_asset_class, None, normalized_session_bucket),
        "asset_class": (normalized_asset_class, None, None),
        "global": (None, None, None),
    }

    segments = table.get("segments")
    segments = segments if isinstance(segments, list) else []
    for level in SEGMENT_LEVEL_ORDER:
        # Missing candidate keys leave None in ``wanted``; a leaf row always
        # carries three non-None match keys, so such rows simply never match
        # and resolution falls through to the coarser levels.
        wanted = wanted_by_level[level]
        matches = [
            segment
            for segment in segments
            if isinstance(segment, Mapping)
            and segment.get("fallback_level") == level
            and bool(segment.get("promoted"))
            and _match_key(segment) == wanted
        ]
        if matches:
            chosen = sorted(matches, key=lambda segment: str(segment.get("segment_id")))[0]
            params = chosen.get("params")
            return {
                "policy_id": chosen.get("policy_id"),
                "family": chosen.get("family"),
                "params": dict(params) if isinstance(params, Mapping) else {},
                "params_fidelity": chosen.get("params_fidelity"),
                "segment_id": chosen.get("segment_id"),
                "fallback_level": level,
                "promoted": True,
                "reason": None,
                "table_sha256": table.get("table_sha256"),
            }

    return _default_policy_resolution(
        table,
        fallback_level=GLOBAL_DEFAULT_FALLBACK_LEVEL,
        reason=None,
    )


__all__ = [
    "GLOBAL_DEFAULT_FALLBACK_LEVEL",
    "SEGMENT_LEVEL_ORDER",
    "SEGMENT_TABLE_SCHEMA_VERSION",
    "SESSION_VOCABULARY_UNMAPPED_FALLBACK_LEVEL",
    "load_segment_policy_table",
    "normalize_session_vocabulary",
    "resolve_segment_policy",
    "segment_table_validation_errors",
]
