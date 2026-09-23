#!/usr/bin/env python3
"""Verify a hash-bound *offline export* of live host state against local truth.

The verifier has no network, broker, token-mint or host-read code.  It consumes a
JSON observation prepared elsewhere, rejects stale or unhashed observations, and
compares only non-secret digests plus the running ``run_book.py`` argument vectors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "config/live_armed_set.json").is_file():
            return parent
    raise RuntimeError("cannot locate repository root")


REPO = _repo_root()
DECLARATION = REPO / "config/live_armed_set.json"
LAUNCHER = REPO / "scripts/run_book_supervisor.ps1"
BASE_CONFIG = REPO / "config/agent_config.yaml"
SCHEMA = "gtos.host_observation.v1"
OUTPUT_SCHEMA = "gtos.wave21.host_parity_verification.v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ROW_RE = re.compile(r"@\{\s*ns\s*=\s*\"(?P<ns>[^\"]+)\"(?P<body>.*?)\}", re.S)


@dataclass(frozen=True)
class Arming:
    namespace: str
    profile: str
    tags: tuple[str, ...] | None
    frontier_exits: tuple[str, ...]
    spread_geometry_floor: tuple[str, ...]


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def payload_sha256(receipt: dict[str, Any]) -> str:
    """Digest convention for the receipt: canonical JSON without this field."""

    return _sha256(_canonical_bytes({k: v for k, v in receipt.items() if k != "payload_sha256"}))


def argv_sha256(argv: list[str]) -> str:
    """Bind argument boundaries as well as bytes."""

    return _sha256(_canonical_bytes(argv))


def _parse_time(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"{field}_missing_or_not_string")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field}_invalid_iso8601")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field}_timezone_missing")
        return None
    return parsed.astimezone(timezone.utc)


def _csv(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(part.strip() for part in str(value).split(",") if part.strip())


def _row_field(body: str, *keys: str) -> str | None:
    for key in keys:
        match = re.search(
            rf"(?:^|;)\s*{re.escape(key)}\s*=\s*(?:\"(?P<value>[^\"]*)\"|\$null)", body
        )
        if match:
            return match.group("value")
    return None


def parse_local_launcher(path: Path = LAUNCHER) -> dict[str, Arming]:
    rows = {}
    for match in ROW_RE.finditer(path.read_text(encoding="utf-8")):
        body = match.group("body")
        namespace = match.group("ns")
        raw_tags = _row_field(body, "tags")
        rows[namespace] = Arming(
            namespace=namespace,
            profile=_row_field(body, "profile") or "",
            # No/empty --tags is fail-open (all built sleeves), never an empty set.
            tags=_csv(raw_tags) if raw_tags else None,
            frontier_exits=_csv(_row_field(body, "frontier")),
            spread_geometry_floor=_csv(_row_field(body, "spreadFloor", "floor")),
        )
    return rows


def parse_declaration(path: Path = DECLARATION) -> dict[str, Arming]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    rows = {}
    for namespace, row in doc.get("accounts", {}).items():
        tags = tuple(row.get("armed_sleeves") or ())
        rows[namespace] = Arming(
            namespace=namespace,
            profile=str(row.get("profile") or ""),
            tags=tags if tags else None,
            frontier_exits=tuple(row.get("frontier_exits") or ()),
            spread_geometry_floor=tuple(row.get("spread_geometry_floor") or ()),
        )
    return rows


def _flag(argv: list[str], name: str, errors: list[str]) -> str | None:
    indexes = [index for index, value in enumerate(argv) if value == name]
    if len(indexes) != 1:
        errors.append(f"argv_{name[2:].replace('-', '_')}_count_{len(indexes)}")
        return None
    index = indexes[0]
    if index + 1 >= len(argv) or argv[index + 1].startswith("--"):
        errors.append(f"argv_{name[2:].replace('-', '_')}_value_missing")
        return None
    return argv[index + 1]


def parse_worker(worker: dict[str, Any], errors: list[str]) -> Arming | None:
    argv = worker.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(value, str) for value in argv):
        errors.append("worker_argv_missing_or_invalid")
        return None
    observed_hash = worker.get("argv_sha256")
    computed_hash = argv_sha256(argv)
    if observed_hash != computed_hash:
        errors.append("worker_argv_sha256_mismatch")
    namespace = _flag(argv, "--namespace", errors)
    profile = _flag(argv, "--profile", errors)
    tags = _flag(argv, "--tags", errors)
    floor = _flag(argv, "--spread-geometry-floor", errors)
    # Frontier is the one optional argument.  Repetition or a valueless flag is invalid.
    frontier_indexes = [index for index, value in enumerate(argv) if value == "--frontier-exits"]
    if len(frontier_indexes) > 1:
        errors.append(f"argv_frontier_exits_count_{len(frontier_indexes)}")
        frontier = None
    elif frontier_indexes:
        index = frontier_indexes[0]
        if index + 1 >= len(argv) or argv[index + 1].startswith("--"):
            errors.append("argv_frontier_exits_value_missing")
            frontier = None
        else:
            frontier = argv[index + 1]
    else:
        frontier = None
    if not namespace or not profile:
        return None
    return Arming(
        namespace=namespace,
        profile=profile,
        tags=_csv(tags) if tags else None,
        frontier_exits=_csv(frontier),
        spread_geometry_floor=_csv(floor),
    )


def _config_digest(base_bytes: bytes, profile_name: str, profile_bytes: bytes) -> str:
    parts = [
        f"agent_config.yaml:{_sha256(base_bytes)}",
        f"{profile_name}.yaml:{_sha256(profile_bytes)}",
    ]
    return _sha256("|".join(parts).encode())


def _local_config_digest(profile: str) -> str | None:
    profile_path = REPO / "config/profiles" / f"{profile}.yaml"
    try:
        return _config_digest(BASE_CONFIG.read_bytes(), profile, profile_path.read_bytes())
    except OSError:
        return None


def _git(*args: str, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=text)


def _resolve_ref(ref: str) -> str | None:
    proc = _git("rev-parse", "--verify", f"{ref}^{{commit}}")
    return proc.stdout.strip() if proc.returncode == 0 else None


def _ref_blob(ref: str, path: str) -> bytes | None:
    proc = _git("cat-file", "blob", f"{ref}:{path}", text=False)
    return proc.stdout if proc.returncode == 0 else None


def _preserved_config_digest(ref: str, profile: str) -> str | None:
    base = _ref_blob(ref, "config/agent_config.yaml")
    overlay = _ref_blob(ref, f"config/profiles/{profile}.yaml")
    if base is None or overlay is None:
        return None
    return _config_digest(base, profile, overlay)


def _issue(
    issues: list[dict[str, Any]], kind: str, namespace: str, field: str,
    expected: Any, observed: Any, *, severity: str = "CRITICAL",
) -> None:
    issues.append({
        "kind": kind,
        "namespace": namespace,
        "field": field,
        "expected": expected,
        "observed": observed,
        "severity": severity,
    })


def _compare_arming(
    issues: list[dict[str, Any]], observed: dict[str, Arming], expected: dict[str, Arming],
    observed_name: str, expected_name: str,
) -> None:
    for namespace in sorted(set(observed) | set(expected)):
        if namespace not in observed:
            _issue(issues, f"{observed_name}_account_missing", namespace, "account", True, False)
            continue
        if namespace not in expected:
            _issue(issues, f"{observed_name}_account_undeclared", namespace, "account", False, True)
            continue
        left, right = observed[namespace], expected[namespace]
        for field in ("profile", "tags", "frontier_exits", "spread_geometry_floor"):
            actual = getattr(left, field)
            wanted = getattr(right, field)
            if field != "profile":
                actual = None if actual is None else sorted(actual)
                wanted = None if wanted is None else sorted(wanted)
            if actual != wanted:
                _issue(
                    issues, f"{observed_name}_vs_{expected_name}_mismatch",
                    namespace, field, wanted, actual,
                )


def verify_receipt(
    receipt: dict[str, Any], *, now: datetime, max_validity_seconds: int,
    declaration_path: Path = DECLARATION, launcher_path: Path = LAUNCHER,
) -> tuple[dict[str, Any], int]:
    errors: list[str] = []
    if receipt.get("schema") != SCHEMA:
        errors.append("schema_unknown")
    observation_id = receipt.get("observation_id")
    if not isinstance(observation_id, str) or not observation_id.strip():
        errors.append("observation_id_missing_or_invalid")
    claimed_payload = receipt.get("payload_sha256")
    computed_payload = payload_sha256(receipt)
    if claimed_payload != computed_payload:
        errors.append("payload_sha256_mismatch")

    captured = _parse_time(receipt.get("captured_at_utc"), "captured_at_utc", errors)
    expires = _parse_time(receipt.get("expires_at_utc"), "expires_at_utc", errors)
    current = False
    age_seconds = None
    if captured and expires:
        validity = (expires - captured).total_seconds()
        if validity <= 0:
            errors.append("expiry_not_after_capture")
        if validity > max_validity_seconds:
            errors.append("validity_window_exceeds_policy")
        if captured > now:
            errors.append("capture_is_in_the_future")
        age_seconds = (now - captured).total_seconds()
        current = captured <= now <= expires and 0 < validity <= max_validity_seconds

    preservation = receipt.get("preservation")
    if not isinstance(preservation, dict):
        preservation = {}
        errors.append("preservation_missing")
    preservation_ref = preservation.get("ref")
    preserved_commit = _resolve_ref(preservation_ref) if isinstance(preservation_ref, str) else None
    if not preserved_commit:
        errors.append("preservation_ref_unresolvable")
    elif preservation.get("commit") != preserved_commit:
        errors.append("preservation_commit_mismatch")

    workers_raw = receipt.get("workers")
    if not isinstance(workers_raw, list) or not workers_raw:
        errors.append("workers_missing")
        workers_raw = []
    host: dict[str, Arming] = {}
    worker_by_namespace: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(workers_raw):
        if not isinstance(raw, dict):
            errors.append(f"worker_{index}_not_object")
            continue
        worker_errors: list[str] = []
        parsed = parse_worker(raw, worker_errors)
        errors.extend(f"worker_{index}_{error}" for error in worker_errors)
        if parsed:
            if parsed.namespace in host:
                errors.append(f"duplicate_worker_namespace_{parsed.namespace}")
            host[parsed.namespace] = parsed
            worker_by_namespace[parsed.namespace] = raw

    local_declaration = parse_declaration(declaration_path)
    local_launcher = parse_local_launcher(launcher_path)
    issues: list[dict[str, Any]] = []
    _compare_arming(issues, local_launcher, local_declaration, "local_launcher", "declaration")
    _compare_arming(issues, host, local_declaration, "host", "declaration")
    _compare_arming(issues, host, local_launcher, "host", "local_launcher")

    host_files = receipt.get("host_files")
    if not isinstance(host_files, dict):
        host_files = {}
        errors.append("host_files_missing")
    for field in ("armed_set_module_present", "armed_set_manifest_present"):
        value = host_files.get(field)
        if not isinstance(value, bool):
            errors.append(f"host_files_{field}_missing")
        elif not value:
            _issue(
                issues, "host_armed_set_mechanism_absent", "host", field,
                True, False,
            )

    local_head = _resolve_ref("HEAD")
    host_head = host_files.get("head")
    if not isinstance(host_head, str) or not re.fullmatch(r"[0-9a-f]{40}", host_head):
        errors.append("host_head_missing_or_invalid")
    else:
        if preserved_commit and host_head != preserved_commit:
            _issue(issues, "host_head_vs_preservation_mismatch", "host", "head",
                   preserved_commit, host_head)
        if local_head and host_head != local_head:
            _issue(issues, "host_head_vs_local_mismatch", "host", "head", local_head, host_head,
                   severity="HIGH")

    local_launcher_hash = _sha256(launcher_path.read_bytes())
    host_launcher_hash = host_files.get("launcher_sha256")
    if not isinstance(host_launcher_hash, str) or not SHA256_RE.fullmatch(host_launcher_hash):
        errors.append("host_launcher_sha256_missing_or_invalid")
    else:
        if host_launcher_hash != local_launcher_hash:
            _issue(issues, "host_launcher_vs_local_mismatch", "host", "launcher_sha256",
                   local_launcher_hash, host_launcher_hash, severity="HIGH")
        if preserved_commit:
            preserved_launcher = _ref_blob(preserved_commit, "scripts/run_book_supervisor.ps1")
            if preserved_launcher is None:
                errors.append("preservation_launcher_missing")
            else:
                preserved_launcher_hash = _sha256(preserved_launcher)
                if host_launcher_hash != preserved_launcher_hash:
                    _issue(issues, "host_launcher_vs_preservation_mismatch", "host",
                           "launcher_sha256", preserved_launcher_hash, host_launcher_hash)

    for namespace, arming in host.items():
        raw = worker_by_namespace[namespace]
        runtime_digest = raw.get("config_digest_sha256")
        token_digest = raw.get("token_config_digest_sha256")
        if not isinstance(runtime_digest, str) or not SHA256_RE.fullmatch(runtime_digest):
            errors.append(f"{namespace}_config_digest_missing_or_invalid")
            continue
        if not isinstance(token_digest, str) or not SHA256_RE.fullmatch(token_digest):
            errors.append(f"{namespace}_token_config_digest_missing_or_invalid")
            continue
        local_digest = _local_config_digest(arming.profile)
        preserved_digest = (
            _preserved_config_digest(preserved_commit, arming.profile) if preserved_commit else None
        )
        if token_digest != runtime_digest:
            _issue(issues, "token_vs_runtime_config_digest_mismatch", namespace, "config_digest",
                   runtime_digest, token_digest)
        if local_digest is None:
            errors.append(f"{namespace}_local_config_digest_unavailable")
        elif runtime_digest != local_digest:
            _issue(issues, "host_vs_local_config_digest_mismatch", namespace, "config_digest",
                   local_digest, runtime_digest)
        if preserved_digest is None:
            errors.append(f"{namespace}_preserved_config_digest_unavailable")
        elif runtime_digest != preserved_digest:
            _issue(issues, "host_vs_preserved_config_digest_mismatch", namespace, "config_digest",
                   preserved_digest, runtime_digest)

    if errors:
        status = "INVALID_RECEIPT"
        code = 2
    elif not current:
        status = "STALE_NOT_CURRENT"
        code = 2
    elif issues:
        status = "CURRENT_MISMATCH"
        code = 1
    else:
        status = "CURRENT_MATCH"
        code = 0
    result = {
        "schema": OUTPUT_SCHEMA,
        "status": status,
        "observation_current": current and not errors,
        "parity_established": status == "CURRENT_MATCH",
        "claim_current_allowed": status in {"CURRENT_MATCH", "CURRENT_MISMATCH"},
        "checked_at_utc": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "observation_id": observation_id,
        "captured_at_utc": receipt.get("captured_at_utc"),
        "expires_at_utc": receipt.get("expires_at_utc"),
        "observation_age_seconds": age_seconds,
        "payload_sha256_claimed": claimed_payload,
        "payload_sha256_computed": computed_payload,
        "preservation_ref": preservation_ref,
        "preservation_commit_resolved": preserved_commit,
        "local_head": local_head,
        "validation_errors": sorted(set(errors)),
        "issues": sorted(issues, key=lambda row: (
            row["namespace"], row["field"], row["kind"], json.dumps(row["observed"], sort_keys=True)
        )),
        "host_workers": {namespace: asdict(row) for namespace, row in sorted(host.items())},
        "local_declaration": {
            namespace: asdict(row) for namespace, row in sorted(local_declaration.items())
        },
        "local_launcher": {
            namespace: asdict(row) for namespace, row in sorted(local_launcher.items())
        },
        "authority": {
            "offline_receipt_only": True,
            "host_contacted": False,
            "broker_contacted": False,
            "token_material_read": False,
            "mutation_performed": False,
            "activation_authority": False,
        },
    }
    result["deterministic_payload_sha256"] = _sha256(_canonical_bytes({
        key: value for key, value in result.items() if key != "checked_at_utc"
    }))
    return result, code


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--max-validity-seconds", type=int, default=3600)
    parser.add_argument("--now", help="test/replay clock; ISO-8601. Defaults to real UTC now.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    errors: list[str] = []
    now = _parse_time(args.now, "now", errors) if args.now else datetime.now(timezone.utc)
    if not now or errors:
        raise SystemExit("invalid --now: " + ", ".join(errors))
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    result, code = verify_receipt(
        receipt, now=now, max_validity_seconds=args.max_validity_seconds,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{result['status']} issues={len(result['issues'])} errors="
          f"{len(result['validation_errors'])} -> {args.output}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
