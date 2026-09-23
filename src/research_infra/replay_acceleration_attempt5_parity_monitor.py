"""Opaque Jan 1-7 parity monitor for the sealed attempt-5 S0R0 runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping

from src.research_infra.replay_acceleration_fixed_verifier_authority import (
    FixedVerifierAuthorityError,
    assert_fixed_verifier_code_identity,
    validate_fixed_verifier_code_authority,
)
from src.research_infra.replay_acceleration_immutable_evidence import (
    RegularFileIdentity,
)
from src.research_infra.replay_acceleration_partial_golden_successor_authority import (
    SuccessorAuthorityError,
    verify_successor_authority,
)


SCHEMA = "gtos.replay_acceleration.attempt5_parity_monitor.v2"
VERIFIER_MODULE = "src.research_infra.replay_acceleration_real_parity_verifier"
PROSPECTIVE_GOLDEN_AUTHORITY_KEYS = frozenset(
    {
        "golden_manifest_path",
        "golden_manifest_file_sha256",
        "golden_manifest_self_root_sha256",
        "golden_root_sha256",
        "opaque_result_surface_root_sha256",
        "golden_amendment_path",
        "golden_amendment_file_sha256",
        "golden_amendment_self_root_sha256",
        "fixed_verifier_module",
        "fixed_verifier_path",
        "fixed_verifier_file_sha256",
    }
)
PROSPECTIVE_GOLDEN_AUTHORITY_V2_KEYS = PROSPECTIVE_GOLDEN_AUTHORITY_KEYS | {
    "successor_authority_path",
    "successor_authority_file_sha256",
    "successor_authority_root_sha256",
    "successor_authority_verification_root_sha256",
    "economic_execution_contract_digest_sha256",
    "fixed_verifier_code_authority",
    "fixed_verifier_code_authority_root_sha256",
}


class MonitorRejected(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def root(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(
        character in "009abcdef" for character in text
    )


def _lexical_path(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _path_has_symlink_component(path: Path) -> bool:
    lexical = _lexical_path(path)
    current = Path(lexical.anchor)
    for component in lexical.parts[1:]:
        current /= component
        if current.is_symlink():
            return True
    return False


def _open_regular_nofollow(path: Path, *, code: str) -> int:
    lexical = _lexical_path(path)
    if _path_has_symlink_component(lexical):
        raise MonitorRejected("monitor_symlink_component_forbidden")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    parent_descriptor = -1
    try:
        parent_descriptor = os.open(lexical.anchor, directory_flags)
        for component in lexical.parts[1:-1]:
            next_descriptor = os.open(
                component,
                directory_flags | nofollow,
                dir_fd=parent_descriptor,
            )
            os.close(parent_descriptor)
            parent_descriptor = next_descriptor
        descriptor = os.open(
            lexical.name,
            os.O_RDONLY | nofollow,
            dir_fd=parent_descriptor,
        )
    except OSError:
        raise MonitorRejected(code) from None
    finally:
        if parent_descriptor >= 0:
            os.close(parent_descriptor)
    opened = os.fstat(descriptor)
    if not stat.S_ISREG(opened.st_mode):
        os.close(descriptor)
        raise MonitorRejected(code)
    return descriptor


def _read_regular_file_nofollow(path: Path, *, code: str) -> bytes:
    descriptor = _open_regular_nofollow(path, code=code)
    try:
        opened = os.fstat(descriptor)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        completed = os.fstat(descriptor)
        if (
            opened.st_dev != completed.st_dev
            or opened.st_ino != completed.st_ino
            or opened.st_size != completed.st_size
            or opened.st_mtime_ns != completed.st_mtime_ns
            or opened.st_ctime_ns != completed.st_ctime_ns
        ):
            raise MonitorRejected("monitor_evidence_changed_during_read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def file_sha256(path: Path) -> str:
    raw = _read_regular_file_nofollow(
        path,
        code="monitor_evidence_file_invalid",
    )
    return hashlib.sha256(raw).hexdigest()


def _load_canonical_json(raw: bytes, *, code: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        raise MonitorRejected(code) from None
    if type(value) is not dict or raw != canonical_bytes(value) + b"\n":
        raise MonitorRejected(code)
    return value


def atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path = _lexical_path(path)
    if _path_has_symlink_component(path):
        raise MonitorRejected("monitor_symlink_component_forbidden")
    if path.exists() or path.is_symlink():
        raise MonitorRejected("monitor_output_must_be_new")
    if not path.parent.is_dir():
        raise MonitorRejected("monitor_output_parent_invalid")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        payload = canonical_bytes(value) + b"\n"
        view = memoryview(payload)
        offset = 0
        while offset < len(view):
            written = os.write(descriptor, view[offset:])
            if written <= 0:
                raise MonitorRejected("monitor_output_write_failed")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        os.link(temporary, path, follow_symlinks=False)
    except OSError:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise MonitorRejected("monitor_output_must_be_new") from None
    temporary.unlink()


def _inside(path: Path, root_path: Path, *, code: str) -> Path:
    lexical_root = _lexical_path(root_path)
    lexical_path = _lexical_path(path)
    if _path_has_symlink_component(lexical_root) or _path_has_symlink_component(
        lexical_path
    ):
        raise MonitorRejected("monitor_symlink_component_forbidden")
    try:
        lexical_path.relative_to(lexical_root)
    except ValueError:
        raise MonitorRejected(code) from None
    return lexical_path


def _reject_path_collisions(paths: Mapping[str, Path]) -> None:
    items = list(paths.items())
    for index, (left_name, left_path) in enumerate(items):
        for right_name, right_path in items[index + 1 :]:
            if (
                left_path == right_path
                or left_path in right_path.parents
                or right_path in left_path.parents
            ):
                raise MonitorRejected(
                    "monitor_evidence_path_collision:"
                    f"{left_name}:{right_name}"
                )


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _validated_request_authority(
    *,
    request: Mapping[str, Any],
    namespace: Path,
    golden_manifest: Path,
) -> tuple[
    dict[str, Any],
    bytes,
    bytes,
    bytes,
    dict[str, RegularFileIdentity] | None,
]:
    request_projection = dict(request)
    request_root = request_projection.pop("gate_request_root_sha256", None)
    authority = request.get("prospective_golden_authority")
    is_successor = (
        type(authority) is dict
        and set(authority) == PROSPECTIVE_GOLDEN_AUTHORITY_V2_KEYS
    )
    if (
        not _is_sha256(request_root)
        or request_root != root(request_projection)
        or request.get("accelerated_namespace_path") != str(namespace)
        or type(authority) is not dict
        or set(authority)
        not in {
            PROSPECTIVE_GOLDEN_AUTHORITY_KEYS,
            PROSPECTIVE_GOLDEN_AUTHORITY_V2_KEYS,
        }
        or authority.get("fixed_verifier_module") != VERIFIER_MODULE
    ):
        raise MonitorRejected("monitor_gate_request_authority_invalid")
    hash_fields = (
        "golden_manifest_file_sha256",
        "golden_manifest_self_root_sha256",
        "golden_root_sha256",
        "opaque_result_surface_root_sha256",
        "golden_amendment_file_sha256",
        "golden_amendment_self_root_sha256",
        "fixed_verifier_file_sha256",
        *(
            (
                "successor_authority_file_sha256",
                "successor_authority_root_sha256",
                "successor_authority_verification_root_sha256",
                "economic_execution_contract_digest_sha256",
                "fixed_verifier_code_authority_root_sha256",
            )
            if is_successor
            else ()
        ),
    )
    if any(not _is_sha256(authority.get(field)) for field in hash_fields):
        raise MonitorRejected("monitor_gate_request_authority_invalid")
    path_fields = (
        "golden_manifest_path",
        "golden_amendment_path",
        "fixed_verifier_path",
        *(("successor_authority_path",) if is_successor else ()),
    )
    if any(
        type(authority.get(field)) is not str
        or not Path(str(authority[field])).is_absolute()
        or str(_lexical_path(Path(str(authority[field]))))
        != str(authority[field])
        for field in path_fields
    ):
        raise MonitorRejected("monitor_gate_request_authority_invalid")
    amendment_path = _lexical_path(
        Path(str(authority["golden_amendment_path"]))
    )
    verifier_path = _lexical_path(
        Path(str(authority["fixed_verifier_path"]))
    )
    successor_authority_path = (
        _lexical_path(Path(str(authority["successor_authority_path"])))
        if is_successor
        else None
    )
    expected_verifier_path = _lexical_path(
        Path(__file__).with_name(
            "replay_acceleration_real_parity_verifier.py"
        )
    )
    if (
        authority["golden_manifest_path"] != str(golden_manifest)
        or verifier_path != expected_verifier_path
    ):
        raise MonitorRejected("monitor_gate_request_authority_mismatch")
    authority_paths = {
        "golden_manifest": golden_manifest,
        "golden_amendment": amendment_path,
        "fixed_verifier": verifier_path,
    }
    if successor_authority_path is not None:
        authority_paths["successor_authority"] = successor_authority_path
    _reject_path_collisions(authority_paths)
    manifest_raw = _read_regular_file_nofollow(
        golden_manifest,
        code="monitor_golden_manifest_invalid",
    )
    amendment_raw = _read_regular_file_nofollow(
        amendment_path,
        code="monitor_golden_amendment_invalid",
    )
    verifier_raw = _read_regular_file_nofollow(
        verifier_path,
        code="monitor_fixed_verifier_invalid",
    )
    if (
        hashlib.sha256(manifest_raw).hexdigest()
        != authority["golden_manifest_file_sha256"]
        or hashlib.sha256(amendment_raw).hexdigest()
        != authority["golden_amendment_file_sha256"]
        or hashlib.sha256(verifier_raw).hexdigest()
        != authority["fixed_verifier_file_sha256"]
    ):
        raise MonitorRejected("monitor_gate_request_authority_mismatch")
    code_identities = None
    if is_successor:
        try:
            successor_verification = verify_successor_authority(
                Path(str(authority["successor_authority_path"]))
            )
            code_identities = validate_fixed_verifier_code_authority(
                authority["fixed_verifier_code_authority"],
                module_directory=Path(__file__).parent,
            )
        except (SuccessorAuthorityError, FixedVerifierAuthorityError):
            raise MonitorRejected(
                "monitor_gate_request_authority_mismatch"
            ) from None
        if (
            successor_verification.get("authority_file_sha256")
            != authority["successor_authority_file_sha256"]
            or successor_verification.get("authority_root_sha256")
            != authority["successor_authority_root_sha256"]
            or successor_verification.get("verification_root_sha256")
            != authority["successor_authority_verification_root_sha256"]
            or authority["fixed_verifier_code_authority"].get(
                "authority_root_sha256"
            )
            != authority["fixed_verifier_code_authority_root_sha256"]
        ):
            raise MonitorRejected("monitor_gate_request_authority_mismatch")
    return dict(authority), manifest_raw, amendment_raw, verifier_raw, code_identities


def run_monitor(args: argparse.Namespace) -> dict[str, Any]:
    namespace = _lexical_path(Path(args.namespace))
    git_root = _lexical_path(Path(args.git_root))
    golden_manifest = _lexical_path(Path(args.golden_manifest))
    if any(
        _path_has_symlink_component(path)
        for path in (namespace, git_root, golden_manifest)
    ):
        raise MonitorRejected("monitor_symlink_component_forbidden")
    if (
        not namespace.is_dir()
        or not git_root.is_dir()
        or int(args.timeout_seconds) < 1
        or int(args.timeout_seconds) > 604800
        or float(args.poll_seconds) <= 0.0
    ):
        raise MonitorRejected("monitor_authority_invalid")
    gate_request = _inside(
        args.gate_request,
        namespace,
        code="monitor_gate_request_outside_namespace",
    )
    report_output = _inside(
        args.report_output,
        namespace,
        code="monitor_report_outside_namespace",
    )
    receipt_output = _inside(
        args.receipt_output,
        namespace,
        code="monitor_receipt_outside_namespace",
    )
    monitor_receipt = _inside(
        args.monitor_receipt,
        namespace,
        code="monitor_evidence_outside_namespace",
    )
    evidence_paths = {
        "gate_request": gate_request,
        "parity_report": report_output,
        "parity_receipt": receipt_output,
        "monitor_receipt": monitor_receipt,
    }
    _reject_path_collisions(evidence_paths)
    if any(
        path.exists() or path.is_symlink()
        for path in (report_output, receipt_output, monitor_receipt)
    ):
        raise MonitorRejected("monitor_output_must_be_new")

    deadline = time.monotonic() + int(args.timeout_seconds)
    gate_raw: bytes | None = None
    while time.monotonic() < deadline:
        if gate_request.is_symlink() or _path_has_symlink_component(gate_request):
            raise MonitorRejected("monitor_symlink_component_forbidden")
        if gate_request.exists():
            gate_raw = _read_regular_file_nofollow(
                gate_request,
                code="monitor_gate_request_invalid",
            )
            break
        if not _pid_alive(int(args.runner_pid)):
            raise MonitorRejected("monitor_runner_exited_before_gate_request")
        time.sleep(float(args.poll_seconds))
    else:
        raise MonitorRejected("monitor_gate_request_timeout")
    if gate_raw is None:
        raise MonitorRejected("monitor_gate_request_invalid")
    request = _load_canonical_json(
        gate_raw,
        code="monitor_gate_request_invalid",
    )
    authority, manifest_raw, amendment_raw, verifier_raw, code_identities = (
        _validated_request_authority(
            request=request,
            namespace=namespace,
            golden_manifest=golden_manifest,
        )
    )
    authority_paths = {
        "golden_manifest": golden_manifest,
        "golden_amendment": Path(authority["golden_amendment_path"]),
        "fixed_verifier": Path(authority["fixed_verifier_path"]),
    }
    if "successor_authority_path" in authority:
        authority_paths["successor_authority"] = Path(
            authority["successor_authority_path"]
        )
    _reject_path_collisions({**evidence_paths, **authority_paths})

    command = [
        sys.executable,
        "-m",
        VERIFIER_MODULE,
        "--golden-manifest",
        str(golden_manifest),
        "--accelerated-namespace",
        str(namespace),
        "--gate-request",
        str(gate_request),
        "--report-output",
        str(report_output),
        "--receipt-output",
        str(receipt_output),
    ]
    if code_identities is not None:
        try:
            assert_fixed_verifier_code_identity(code_identities)
        except FixedVerifierAuthorityError:
            raise MonitorRejected("monitor_fixed_verifier_changed") from None
    completed = subprocess.run(command, cwd=git_root, check=False)
    if code_identities is not None:
        try:
            assert_fixed_verifier_code_identity(code_identities)
            validate_fixed_verifier_code_authority(
                authority["fixed_verifier_code_authority"],
                module_directory=Path(__file__).parent,
            )
        except FixedVerifierAuthorityError:
            raise MonitorRejected("monitor_fixed_verifier_changed") from None
    if completed.returncode != 0:
        raise MonitorRejected(
            f"monitor_parity_verifier_failed:{completed.returncode}"
        )
    report_raw = _read_regular_file_nofollow(
        report_output,
        code="monitor_parity_report_invalid",
    )
    receipt_raw = _read_regular_file_nofollow(
        receipt_output,
        code="monitor_parity_receipt_invalid",
    )
    _load_canonical_json(report_raw, code="monitor_parity_report_invalid")
    _load_canonical_json(receipt_raw, code="monitor_parity_receipt_invalid")
    evidence_core = {
        "schema": SCHEMA,
        "status": "EXACT_PARITY_VERIFIER_COMPLETED_RECEIPT_PUBLISHED",
        "runner_pid": int(args.runner_pid),
        "namespace": str(namespace),
        "gate_request_sha256": hashlib.sha256(gate_raw).hexdigest(),
        "gate_request_root_sha256": request["gate_request_root_sha256"],
        "prospective_golden_authority_root_sha256": root(authority),
        "golden_manifest_path": str(golden_manifest),
        "golden_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "golden_amendment_path": authority["golden_amendment_path"],
        "golden_amendment_sha256": hashlib.sha256(amendment_raw).hexdigest(),
        "fixed_verifier_path": authority["fixed_verifier_path"],
        "fixed_verifier_file_sha256": hashlib.sha256(verifier_raw).hexdigest(),
        "parity_report_sha256": hashlib.sha256(report_raw).hexdigest(),
        "parity_receipt_sha256": hashlib.sha256(receipt_raw).hexdigest(),
        "verifier_module": VERIFIER_MODULE,
        "verifier_returncode": int(completed.returncode),
        "economic_values_exposed": False,
        "other_arms_launched": False,
        "broker_live_authority": False,
    }
    evidence = {
        **evidence_core,
        "monitor_receipt_root_sha256": root(evidence_core),
    }
    atomic_write(monitor_receipt, evidence)
    return evidence


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-pid", type=int, required=True)
    parser.add_argument("--namespace", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, required=True)
    parser.add_argument("--golden-manifest", type=Path, required=True)
    parser.add_argument("--gate-request", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--monitor-receipt", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=604800)
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    evidence = run_monitor(args)
    print(
        canonical_bytes(
            {
                "status": evidence["status"],
                "monitor_receipt_root_sha256": evidence[
                    "monitor_receipt_root_sha256"
                ],
                "economic_values_exposed": False,
            }
        ).decode("ascii")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
