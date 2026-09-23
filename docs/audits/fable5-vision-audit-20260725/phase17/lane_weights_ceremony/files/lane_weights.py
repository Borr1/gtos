"""Signed, day-latched live carrier for learning-lane sleeve multipliers.

The carrier is deliberately outside ``agent_config.yaml`` and profile YAML: those
bytes are activation-token inputs.  A weight file is useful only when all of its
claims verify as one unit.  Any missing, stale, malformed, wrongly scoped, or
badly signed file therefore produces a complete neutral vector (x1.00), never a
partially applied one.

The first observation in a UTC decision day is persisted beneath the book's
namespace.  Every later observation -- including after a process restart --
reuses that latch.  A previously unseen non-neutral vector may only be admitted
inside the first five minutes of its effective day; operators stage the signed
file before the boundary and the running worker picks it up after midnight.
This is the B365-class guard against an intraday sizing jump.

This module has no broker imports and cannot place or manage an order.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import math
import os
import stat
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "gtos.lane_weights.v1"
SNAPSHOT_SCHEMA_VERSION = "gtos.lane_weights.snapshot.v1"
LATCH_SCHEMA_VERSION = "gtos.lane_weights.latch.v1"
DECLARED_MIN_WEIGHT = 0.50
DECLARED_MAX_WEIGHT = 1.15
ACTIVATION_GRACE_SECONDS = 5 * 60
MIN_KEY_BYTES = 32
MAX_KEY_BYTES = 4096


class LaneWeightsConfigurationError(ValueError):
    """The launch arguments themselves are unsafe or internally inconsistent."""


class LaneWeightsValidationError(ValueError):
    """A signed source or persisted latch failed its contract."""


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _payload(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {str(k): v for k, v in envelope.items() if k != "signature_hmac_sha256"}


def envelope_digest(envelope: Mapping[str, Any]) -> str:
    """Digest the complete signed envelope for packet provenance."""
    return hashlib.sha256(_canonical_json(dict(envelope))).hexdigest()


def sign_envelope(payload: Mapping[str, Any], key: bytes) -> dict[str, Any]:
    """Return a canonical HMAC-SHA256 envelope.  ``key`` is never serialized."""
    if len(key) < MIN_KEY_BYTES:
        raise LaneWeightsConfigurationError(f"signing key must be at least {MIN_KEY_BYTES} bytes")
    clean = _payload(payload)
    signature = hmac.new(key, _canonical_json(clean), hashlib.sha256).hexdigest()
    return {**clean, "signature_hmac_sha256": signature}


def load_signing_key(path: str | os.PathLike[str]) -> bytes:
    """Read a secret key with a strict POSIX permission check.

    Windows does not expose useful POSIX mode bits; ACL validation belongs in the
    deployment preflight there.  Symlinks are refused on every platform so a
    supervisor cannot be redirected to a different secret after inspection.
    """
    key_path = Path(path)
    if key_path.is_symlink():
        raise LaneWeightsValidationError("signing_key_is_symlink")
    try:
        info = key_path.stat()
    except OSError as exc:
        raise LaneWeightsValidationError(f"signing_key_unreadable:{exc.__class__.__name__}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise LaneWeightsValidationError("signing_key_not_regular_file")
    if os.name != "nt" and (stat.S_IMODE(info.st_mode) & 0o077):
        raise LaneWeightsValidationError("signing_key_permissions_not_private")
    try:
        key = key_path.read_bytes()
    except OSError as exc:
        raise LaneWeightsValidationError(f"signing_key_unreadable:{exc.__class__.__name__}") from exc
    if not (MIN_KEY_BYTES <= len(key) <= MAX_KEY_BYTES):
        raise LaneWeightsValidationError("signing_key_length_out_of_bounds")
    return key


def _iso_day(value: Any, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise LaneWeightsValidationError(f"{field}_not_iso_date") from exc


def _iso_instant(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LaneWeightsValidationError(f"{field}_not_iso_datetime") from exc
    if parsed.tzinfo is None:
        raise LaneWeightsValidationError(f"{field}_timezone_missing")
    return parsed.astimezone(timezone.utc)


def _sha256_hex(value: Any, field: str) -> str:
    text = str(value or "")
    if len(text) != 64 or any(c not in "009abcdef" for c in text):
        raise LaneWeightsValidationError(f"{field}_not_sha256")
    return text


def _scope(expected_sleeves: Sequence[str]) -> tuple[str, ...]:
    scope = tuple(sorted(str(v).strip() for v in expected_sleeves if str(v).strip()))
    if len(scope) != len(set(scope)):
        raise LaneWeightsConfigurationError("expected_sleeves_contains_duplicates")
    return scope


def verify_envelope(
    envelope: Mapping[str, Any],
    *,
    key: bytes,
    namespace: str,
    expected_sleeves: Sequence[str],
) -> dict[str, Any]:
    """Verify signature, scope, band, types, and provenance fields as one contract."""
    if not isinstance(envelope, Mapping):
        raise LaneWeightsValidationError("weights_file_not_mapping")
    if envelope.get("schema_version") != SCHEMA_VERSION:
        raise LaneWeightsValidationError("schema_version_mismatch")
    if str(envelope.get("namespace") or "") != str(namespace):
        raise LaneWeightsValidationError("namespace_mismatch")

    signature = str(envelope.get("signature_hmac_sha256") or "")
    if len(signature) != 64 or any(c not in "009abcdef" for c in signature):
        raise LaneWeightsValidationError("signature_not_sha256")
    expected_signature = hmac.new(key, _canonical_json(_payload(envelope)), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise LaneWeightsValidationError("signature_mismatch")

    scope = _scope(expected_sleeves)
    declared_scope = envelope.get("scope_sleeves")
    if not isinstance(declared_scope, list) or tuple(sorted(str(v) for v in declared_scope)) != scope:
        raise LaneWeightsValidationError("scope_mismatch")
    if len(declared_scope) != len(set(str(v) for v in declared_scope)):
        raise LaneWeightsValidationError("scope_contains_duplicates")

    band = envelope.get("declared_band")
    if not isinstance(band, Mapping):
        raise LaneWeightsValidationError("declared_band_missing")
    try:
        lower = float(band.get("min"))
        upper = float(band.get("max"))
    except (TypeError, ValueError) as exc:
        raise LaneWeightsValidationError("declared_band_non_numeric") from exc
    if lower != DECLARED_MIN_WEIGHT or upper != DECLARED_MAX_WEIGHT:
        raise LaneWeightsValidationError("declared_band_mismatch")

    raw_weights = envelope.get("weights")
    if not isinstance(raw_weights, Mapping) or set(map(str, raw_weights)) != set(scope):
        raise LaneWeightsValidationError("weights_scope_mismatch")
    weights: dict[str, float] = {}
    for sleeve in scope:
        raw = raw_weights.get(sleeve)
        if isinstance(raw, bool):
            raise LaneWeightsValidationError(f"weight_non_numeric:{sleeve}")
        try:
            value = float(raw)
        except (TypeError, ValueError) as exc:
            raise LaneWeightsValidationError(f"weight_non_numeric:{sleeve}") from exc
        if not math.isfinite(value) or not lower <= value <= upper:
            raise LaneWeightsValidationError(f"weight_out_of_band:{sleeve}")
        weights[sleeve] = value

    effective = _iso_day(envelope.get("effective_decision_day"), "effective_decision_day")
    expires = _iso_day(envelope.get("expires_after_decision_day"), "expires_after_decision_day")
    if expires < effective:
        raise LaneWeightsValidationError("expiry_before_effective_day")
    issued = _iso_instant(envelope.get("issued_at_utc"), "issued_at_utc")
    effective_boundary = datetime.combine(effective, time.min, tzinfo=timezone.utc)
    if issued > effective_boundary:
        raise LaneWeightsValidationError("issued_after_effective_day_boundary")

    evidence_digest = _sha256_hex(envelope.get("evidence_digest_sha256"), "evidence_digest_sha256")
    return {
        "weights": weights,
        "scope_sleeves": list(scope),
        "declared_band": {"min": lower, "max": upper},
        "effective_decision_day": effective.isoformat(),
        "expires_after_decision_day": expires.isoformat(),
        "issued_at_utc": issued.isoformat(),
        "evidence_digest_sha256": evidence_digest,
        "signature_verified": True,
        "source_digest_sha256": envelope_digest(envelope),
    }


def build_unsigned_payload(
    *,
    namespace: str,
    weights: Mapping[str, float],
    effective_decision_day: str,
    expires_after_decision_day: str,
    evidence_digest_sha256: str,
    issued_at_utc: str,
) -> dict[str, Any]:
    """Build the only payload shape accepted by :func:`verify_envelope`."""
    scope = tuple(sorted(str(k) for k in weights))
    return {
        "schema_version": SCHEMA_VERSION,
        "namespace": str(namespace),
        "scope_sleeves": list(scope),
        "weights": {s: float(weights[s]) for s in scope},
        "declared_band": {"min": DECLARED_MIN_WEIGHT, "max": DECLARED_MAX_WEIGHT},
        "effective_decision_day": str(effective_decision_day),
        "expires_after_decision_day": str(expires_after_decision_day),
        "issued_at_utc": str(issued_at_utc),
        "evidence_digest_sha256": str(evidence_digest_sha256),
    }


def neutral_snapshot(
    namespace: str,
    decision_day: str,
    scope_sleeves: Sequence[str],
    reason: str,
    *,
    status: str = "neutral",
) -> dict[str, Any]:
    scope = _scope(scope_sleeves)
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "namespace": str(namespace),
        "decision_day": str(decision_day),
        "status": status,
        "reason": str(reason),
        "weights": {s: 1.0 for s in scope},
        "scope_sleeves": list(scope),
        "declared_band": {"min": DECLARED_MIN_WEIGHT, "max": DECLARED_MAX_WEIGHT},
        "signature_verified": False,
        "source_digest_sha256": None,
        "evidence_digest_sha256": None,
        "effective_decision_day": None,
        "expires_after_decision_day": None,
        "issued_at_utc": None,
    }


class LaneWeightController:
    """Resolve one all-or-neutral sleeve vector and latch it for each UTC day."""

    def __init__(
        self,
        *,
        namespace: str,
        expected_sleeves: Sequence[str],
        repo_root: str | os.PathLike[str],
        weights_path: str | os.PathLike[str] | None = None,
        key_path: str | os.PathLike[str] | None = None,
        logger: logging.Logger | None = None,
    ):
        if bool(weights_path) != bool(key_path):
            raise LaneWeightsConfigurationError("lane_weights_and_key_must_be_supplied_together")
        self.namespace = str(namespace)
        self.expected_sleeves = _scope(expected_sleeves)
        if weights_path and not self.expected_sleeves:
            raise LaneWeightsConfigurationError("lane_weights_requires_nonempty_tags_scope")
        self.weights_path = Path(weights_path) if weights_path else None
        self.key_path = Path(key_path) if key_path else None
        self.enabled = self.weights_path is not None
        self._log = logger or logging.getLogger(__name__)
        self._state_path = (
            Path(repo_root) / "pipeline_state" / "ultimate_book" / self.namespace / "lane_weights_latch.json"
        )
        self._cache: dict[str, dict[str, Any]] = {}

    @property
    def state_path(self) -> Path:
        return self._state_path

    def _read_source(self) -> Mapping[str, Any]:
        if self.weights_path is None or self.key_path is None:
            raise LaneWeightsValidationError("carrier_disabled")
        try:
            raw = json.loads(self.weights_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise LaneWeightsValidationError("weights_file_missing") from exc
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise LaneWeightsValidationError(f"weights_file_unreadable:{exc.__class__.__name__}") from exc
        key = load_signing_key(self.key_path)
        return {"envelope": raw, "verified": verify_envelope(
            raw,
            key=key,
            namespace=self.namespace,
            expected_sleeves=self.expected_sleeves,
        )}

    def _active_snapshot(self, verified: Mapping[str, Any], day: str) -> dict[str, Any]:
        return {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "namespace": self.namespace,
            "decision_day": day,
            "status": "active",
            "reason": "signed_weights_active",
            **dict(verified),
        }

    def _persist(self, snapshot: Mapping[str, Any], envelope: Mapping[str, Any] | None) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        wrapper = {
            "schema_version": LATCH_SCHEMA_VERSION,
            "namespace": self.namespace,
            "decision_day": snapshot.get("decision_day"),
            "status": snapshot.get("status"),
            "reason": snapshot.get("reason"),
            "source_envelope": dict(envelope) if envelope is not None else None,
            "written_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        tmp = self._state_path.with_name(f".{self._state_path.name}.{os.getpid()}.tmp")
        try:
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(wrapper, fh, sort_keys=True, separators=(",", ":"))
                fh.write("\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self._state_path)
        finally:
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass

    def _from_latch(self, day: str) -> dict[str, Any] | None:
        if not self._state_path.exists():
            return None
        try:
            state = json.loads(self._state_path.read_text(encoding="utf-8"))
            if state.get("schema_version") != LATCH_SCHEMA_VERSION:
                raise LaneWeightsValidationError("latch_schema_mismatch")
            if state.get("namespace") != self.namespace:
                raise LaneWeightsValidationError("latch_namespace_mismatch")
            if state.get("decision_day") != day:
                return None
            if state.get("status") != "active":
                return neutral_snapshot(
                    self.namespace,
                    day,
                    self.expected_sleeves,
                    str(state.get("reason") or "persisted_neutral"),
                )
            envelope = state.get("source_envelope")
            key = load_signing_key(self.key_path) if self.key_path else b""
            verified = verify_envelope(
                envelope,
                key=key,
                namespace=self.namespace,
                expected_sleeves=self.expected_sleeves,
            )
            effective = _iso_day(verified["effective_decision_day"], "effective_decision_day")
            expires = _iso_day(verified["expires_after_decision_day"], "expires_after_decision_day")
            current = _iso_day(day, "decision_day")
            if not effective <= current <= expires:
                raise LaneWeightsValidationError("latched_source_not_active_for_day")
            return self._active_snapshot(verified, day)
        except Exception as exc:  # fail-neutral even when the state itself is corrupt
            reason = f"latch_invalid:{exc}"
            self._log.error("book[%s]: LANE WEIGHTS NEUTRAL: %s", self.namespace, reason)
            snapshot = neutral_snapshot(self.namespace, day, self.expected_sleeves, reason)
            try:
                self._persist(snapshot, None)
            except OSError:
                pass
            return snapshot

    def snapshot_for_day(
        self,
        decision_day: str | date,
        *,
        observed_at_utc: datetime | None = None,
    ) -> dict[str, Any]:
        if isinstance(decision_day, datetime):
            day_obj = decision_day.date()
        else:
            day_obj = decision_day if isinstance(decision_day, date) else _iso_day(decision_day, "decision_day")
        day = day_obj.isoformat()
        if day in self._cache:
            return dict(self._cache[day])
        # A live worker may run for months; only today's immutable latch needs to
        # stay in memory.  The persisted file is the restart contract.
        self._cache.clear()
        if not self.enabled:
            snapshot = neutral_snapshot(
                self.namespace, day, self.expected_sleeves, "lane_weights_not_configured", status="disabled"
            )
            self._cache[day] = snapshot
            return dict(snapshot)

        latched = self._from_latch(day)
        if latched is not None:
            self._cache[day] = latched
            if latched.get("status") == "active":
                self._log.warning("%s", format_active_log(latched))
            return dict(latched)

        envelope: Mapping[str, Any] | None = None
        try:
            source = self._read_source()
            envelope = source["envelope"]
            verified = source["verified"]
            effective = _iso_day(verified["effective_decision_day"], "effective_decision_day")
            expires = _iso_day(verified["expires_after_decision_day"], "expires_after_decision_day")
            if day_obj < effective:
                raise LaneWeightsValidationError("weights_file_not_yet_effective")
            if day_obj > expires:
                raise LaneWeightsValidationError("weights_file_stale")
            observed = observed_at_utc or datetime.now(timezone.utc)
            if observed.tzinfo is None:
                observed = observed.replace(tzinfo=timezone.utc)
            observed = observed.astimezone(timezone.utc)
            boundary = datetime.combine(day_obj, time.min, tzinfo=timezone.utc)
            seconds_after_boundary = (observed - boundary).total_seconds()
            if not 0 <= seconds_after_boundary <= ACTIVATION_GRACE_SECONDS:
                raise LaneWeightsValidationError("missed_decision_day_activation_boundary")
            snapshot = self._active_snapshot(verified, day)
        except Exception as exc:
            reason = str(exc) or exc.__class__.__name__
            snapshot = neutral_snapshot(self.namespace, day, self.expected_sleeves, reason)
            envelope = None
            self._log.error(
                "book[%s]: LANE WEIGHTS NEUTRAL for %s: %s; all scoped sleeves x1.00",
                self.namespace,
                day,
                reason,
            )

        try:
            self._persist(snapshot, envelope if snapshot["status"] == "active" else None)
        except OSError as exc:
            reason = f"latch_persist_failed:{exc.__class__.__name__}"
            self._log.error(
                "book[%s]: LANE WEIGHTS NEUTRAL for %s: %s; non-neutral state cannot be restart-stable",
                self.namespace,
                day,
                reason,
            )
            snapshot = neutral_snapshot(self.namespace, day, self.expected_sleeves, reason)
        self._cache[day] = snapshot
        if snapshot.get("status") == "active":
            self._log.warning("%s", format_active_log(snapshot))
        return dict(snapshot)

    def snapshot(self, now_utc: datetime | None = None) -> dict[str, Any]:
        now = now_utc or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        now = now.astimezone(timezone.utc)
        return self.snapshot_for_day(now.date(), observed_at_utc=now)


def format_active_log(snapshot: Mapping[str, Any]) -> str:
    weights = snapshot.get("weights") if isinstance(snapshot.get("weights"), Mapping) else {}
    rendered = " ".join(f"{s}={float(weights[s]):.2f}" for s in sorted(weights))
    return f"LANE WEIGHTS ACTIVE: {rendered}"
