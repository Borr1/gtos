#!/usr/bin/env python3
"""Offline operator utility for signed ultimate-book learning-lane weights.

No command in this file imports MT5 or a broker adapter.  It creates/verifies the
external carrier and audits the applied-weight telemetry written by run_book.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Direct ``python scripts/gtos_lane_weights.py`` starts with ``scripts/`` on
# sys.path, not the repository root.  Resolve the local package explicitly; the
# operator command must work in exactly the form printed by the ceremony page.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.ultimate_book.lane_weights import (
    DECLARED_MAX_WEIGHT,
    DECLARED_MIN_WEIGHT,
    LaneWeightsConfigurationError,
    LaneWeightsValidationError,
    build_unsigned_payload,
    envelope_digest,
    load_signing_key,
    sign_envelope,
    verify_envelope,
)


def _write_json_atomic(path: Path, value: Any, *, refuse_existing: bool = False) -> None:
    if refuse_existing and path.exists():
        raise LaneWeightsConfigurationError(f"output_exists:{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(value, fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass


def _parse_tags(value: str) -> tuple[str, ...]:
    tags = tuple(sorted(v.strip() for v in str(value).split(",") if v.strip()))
    if not tags or len(tags) != len(set(tags)):
        raise LaneWeightsConfigurationError("tags_must_be_nonempty_and_unique")
    return tags


def _parse_weights(items: list[str]) -> dict[str, float]:
    weights: dict[str, float] = {}
    for item in items:
        if "=" not in item:
            raise LaneWeightsConfigurationError(f"weight_must_be_sleeve_equals_number:{item}")
        sleeve, raw = item.split("=", 1)
        sleeve = sleeve.strip()
        if not sleeve or sleeve in weights:
            raise LaneWeightsConfigurationError(f"weight_name_empty_or_duplicate:{sleeve}")
        try:
            value = float(raw)
        except ValueError as exc:
            raise LaneWeightsConfigurationError(f"weight_not_numeric:{sleeve}") from exc
        if not DECLARED_MIN_WEIGHT <= value <= DECLARED_MAX_WEIGHT:
            raise LaneWeightsConfigurationError(f"weight_out_of_band:{sleeve}")
        weights[sleeve] = value
    if not weights:
        raise LaneWeightsConfigurationError("at_least_one_weight_required")
    return weights


def _evidence_digest(value: str) -> str:
    candidate = Path(value)
    if candidate.is_file():
        return hashlib.sha256(candidate.read_bytes()).hexdigest()
    text = str(value).strip()
    if len(text) == 64 and all(c in "009abcdef" for c in text):
        return text
    raise LaneWeightsConfigurationError("evidence_must_be_a_file_or_lowercase_sha256")


def _cmd_keygen(args: argparse.Namespace) -> int:
    path = Path(args.output)
    if path.exists():
        raise LaneWeightsConfigurationError(f"key_output_exists:{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        os.write(descriptor, secrets.token_bytes(32))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    if os.name != "nt":
        os.chmod(path, 0o600)
    print(json.dumps({"ok": True, "key_path": str(path), "secret_printed": False}, sort_keys=True))
    return 0


def _cmd_sign(args: argparse.Namespace) -> int:
    weights = _parse_weights(args.weight)
    key = load_signing_key(args.key)
    issued = args.issued_at or datetime.now(timezone.utc).isoformat()
    payload = build_unsigned_payload(
        namespace=args.namespace,
        weights=weights,
        effective_decision_day=args.effective_day,
        expires_after_decision_day=args.expires_day,
        evidence_digest_sha256=_evidence_digest(args.evidence),
        issued_at_utc=issued,
    )
    envelope = sign_envelope(payload, key)
    verified = verify_envelope(
        envelope,
        key=key,
        namespace=args.namespace,
        expected_sleeves=tuple(weights),
    )
    _write_json_atomic(Path(args.output), envelope, refuse_existing=not args.force)
    print(json.dumps({
        "ok": True,
        "output": args.output,
        "namespace": args.namespace,
        "scope_sleeves": verified["scope_sleeves"],
        "weights": verified["weights"],
        "declared_band": verified["declared_band"],
        "effective_decision_day": verified["effective_decision_day"],
        "expires_after_decision_day": verified["expires_after_decision_day"],
        "source_digest_sha256": verified["source_digest_sha256"],
        "signature_verified": True,
        "secret_printed": False,
    }, sort_keys=True))
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    envelope = json.loads(Path(args.input).read_text(encoding="utf-8"))
    key = load_signing_key(args.key)
    verified = verify_envelope(
        envelope,
        key=key,
        namespace=args.namespace,
        expected_sleeves=_parse_tags(args.tags),
    )
    print(json.dumps({
        "ok": True,
        **verified,
        "secret_printed": False,
    }, sort_keys=True))
    return 0


def _cmd_telemetry(args: argparse.Namespace) -> int:
    if not 1 <= int(args.days) <= 31:
        raise LaneWeightsConfigurationError("days_must_be_between_1_and_31")
    expected_scope = _parse_tags(args.tags)
    envelope = json.loads(Path(args.weights).read_text(encoding="utf-8"))
    verified = verify_envelope(
        envelope,
        key=load_signing_key(args.key),
        namespace=args.namespace,
        expected_sleeves=expected_scope,
    )
    start = date.fromisoformat(args.start_day)
    days = [start + timedelta(days=i) for i in range(args.days)]
    expected_days = {d.isoformat() for d in days}
    expected_digest = envelope_digest(envelope)
    observations = {day: 0 for day in sorted(expected_days)}
    mismatches: list[dict[str, Any]] = []
    packet_count = 0
    path = Path(args.input)
    with path.open("r", encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                packet = json.loads(line)
            except json.JSONDecodeError:
                mismatches.append({"line": line_number, "reason": "invalid_json"})
                continue
            if packet.get("namespace") != args.namespace:
                continue
            provenance = packet.get("lane_weight_provenance")
            if not isinstance(provenance, dict):
                created_day = str(packet.get("created_at_utc") or "")[:10]
                if created_day in expected_days:
                    mismatches.append({
                        "line": line_number,
                        "day": created_day,
                        "reason": "lane_weight_provenance_missing",
                    })
                continue
            controller_day = str(provenance.get("controller_decision_day") or "")
            if controller_day not in expected_days:
                continue
            packet_count += 1
            observations[controller_day] += 1
            bridge_lane = ((packet.get("bridge") or {}).get("lane_weights") or {})
            checks = {
                "status": provenance.get("status") == "active",
                "signature_verified": provenance.get("signature_verified") is True,
                "source_digest": provenance.get("source_digest_sha256") == expected_digest,
                "bridge_weights": bridge_lane.get("weights") == verified["weights"],
                "bridge_day": bridge_lane.get("decision_day") == controller_day,
            }
            bad = sorted(k for k, ok in checks.items() if not ok)
            for sleeve, applied in (packet.get("lane_weights_by_sleeve") or {}).items():
                if float(applied) != float(verified["weights"].get(sleeve, 1.0)):
                    bad.append(f"applied_weight:{sleeve}")
            if bad:
                mismatches.append({"line": line_number, "day": controller_day, "failed": bad})

    missing_days = [day for day, count in observations.items() if count == 0]
    ok = not mismatches and not missing_days
    report = {
        "schema_version": "gtos.lane_weights.telemetry.v1",
        "ok": ok,
        "namespace": args.namespace,
        "source_digest_sha256": expected_digest,
        "expected_weights": verified["weights"],
        "start_day": args.start_day,
        "days": args.days,
        "packet_count": packet_count,
        "observations_by_controller_day": observations,
        "missing_days": missing_days,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:100],
    }
    if args.output:
        _write_json_atomic(Path(args.output), report)
    print(json.dumps(report, sort_keys=True))
    return 0 if ok else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    keygen = sub.add_parser("keygen", help="Create a new 256-bit external key without printing it")
    keygen.add_argument("--output", required=True)
    keygen.set_defaults(func=_cmd_keygen)

    sign = sub.add_parser("sign", help="Create a signed gtos.lane_weights.v1 file")
    sign.add_argument("--namespace", required=True)
    sign.add_argument("--weight", action="append", required=True, help="sleeve=multiplier; repeat per sleeve")
    sign.add_argument("--effective-day", required=True)
    sign.add_argument("--expires-day", required=True)
    sign.add_argument("--evidence", required=True, help="Evidence file path or lowercase SHA-256")
    sign.add_argument("--issued-at", default=None, help="UTC ISO timestamp; defaults to now")
    sign.add_argument("--key", required=True)
    sign.add_argument("--output", required=True)
    sign.add_argument("--force", action="store_true")
    sign.set_defaults(func=_cmd_sign)

    verify = sub.add_parser("verify", help="Verify signature, namespace, scope, band, and dates")
    verify.add_argument("--input", required=True)
    verify.add_argument("--key", required=True)
    verify.add_argument("--namespace", required=True)
    verify.add_argument("--tags", required=True)
    verify.set_defaults(func=_cmd_verify)

    telemetry = sub.add_parser("telemetry", help="Audit per-day runtime packets against a declaration")
    telemetry.add_argument("--input", required=True, help="Runtime-learning JSONL")
    telemetry.add_argument("--weights", required=True)
    telemetry.add_argument("--key", required=True)
    telemetry.add_argument("--namespace", required=True)
    telemetry.add_argument("--tags", required=True)
    telemetry.add_argument("--start-day", required=True)
    telemetry.add_argument("--days", type=int, default=7)
    telemetry.add_argument("--output", default=None)
    telemetry.set_defaults(func=_cmd_telemetry)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (LaneWeightsConfigurationError, LaneWeightsValidationError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc), "secret_printed": False}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
