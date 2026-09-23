"""Independent verifier for the prospective real accelerated S0R0 route."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "gtos.replay_acceleration.real_s0r0_execution_contract.v1"
STATUS = "PROSPECTIVE_REAL_ACCELERATED_S0R0_ROUTE_SEALED"
PREFIX = (
    "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_SELECTION_SIZING_"
    "S0R0_SOURCE_REPAIRED_R3_CAP_R2"
)
EXPECTED_VARIANTS = {"cold_bounded": 1, "warm_continuation": 4}
FORBIDDEN_OUTCOME_KEYS = frozenset(
    {
        "pnl",
        "pnl_total",
        "r_total",
        "win_count",
        "loss_count",
        "win_loss",
        "march_outcome",
        "comparative_economic_outcome",
        "treatment_economics",
    }
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def root(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def self_root(value: Mapping[str, Any], field: str) -> str:
    projection = dict(value)
    projection.pop(field, None)
    return root(projection)


def newline_self_root(value: Mapping[str, Any], field: str) -> str:
    projection = dict(value)
    projection.pop(field, None)
    return hashlib.sha256(canonical_bytes(projection) + b"\n").hexdigest()


def load_canonical(path: Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    value = json.loads(raw)
    if type(value) is not dict or raw != canonical_bytes(value) + b"\n":
        raise ValueError("execution_contract_artifact_not_canonical")
    return value


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_outcome_blind(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_OUTCOME_KEYS:
                raise ValueError("execution_contract_forbidden_outcome_key")
            _assert_outcome_blind(item)
    elif isinstance(value, list):
        for item in value:
            _assert_outcome_blind(item)


def _argument_value(argv: list[str], name: str) -> str:
    try:
        index = argv.index(name)
        return argv[index + 1]
    except (ValueError, IndexError):
        raise ValueError(f"execution_contract_command_argument_missing:{name}") from None


def _verify_command(
    variant: Mapping[str, Any],
    *,
    name: str,
    expected_workers: int,
) -> None:
    argv = variant.get("argv")
    if not isinstance(argv, list) or not argv or not all(
        type(item) is str and item for item in argv
    ):
        raise ValueError("execution_contract_command_invalid")
    if _argument_value(argv, "--arm-id") != "S0R0":
        raise ValueError("execution_contract_arm_invalid")
    if any(token in {"S1R0", "S0R1", "S1R1"} for token in argv):
        raise ValueError("execution_contract_other_arm_forbidden")
    if (
        _argument_value(argv, "--start") != "2026-01-01"
        or _argument_value(argv, "--end") != "2026-01-31"
        or _argument_value(argv, "--chunk-size") != "1"
        or _argument_value(argv, "--output-prefix") != PREFIX
        or _argument_value(argv, "--profiles")
        != "repaired_package_conversion_v3"
        or _argument_value(argv, "--source-prewarm-workers")
        != str(expected_workers)
        or _argument_value(argv, "--parity-gate-after-day")
        != "2026-01-07"
    ):
        raise ValueError("execution_contract_command_scope_invalid")
    required_flags = {
        "--omit-candidate-ledger",
        "--omit-candidate-index-ledger",
        "--omit-packet-sidecar-ledger",
        "--compact-missed-ledger",
        "--compact-decision-ledger",
        "--compact-scorecard-ledger",
    }
    if not required_flags.issubset(argv):
        raise ValueError("execution_contract_compact_proof_flags_missing")
    if "--streaming-proof-archive-root" not in argv:
        raise ValueError("execution_contract_streaming_archive_missing")
    if name == "cold_bounded" and "--stop-after-parity-gate" not in argv:
        raise ValueError("execution_contract_cold_stop_missing")
    if name == "warm_continuation" and "--stop-after-parity-gate" in argv:
        raise ValueError("execution_contract_continuation_disabled")
    digest = str(variant.get("shared_execution_contract_digest_sha256") or "")
    if len(digest) != 64 or _argument_value(
        argv, "--expected-shared-execution-contract-sha256"
    ) != digest:
        raise ValueError("execution_contract_shared_digest_binding_invalid")


def verify_execution_contract(
    artifact_path: Path,
    *,
    git_root: Path,
) -> dict[str, Any]:
    artifact = load_canonical(artifact_path)
    _assert_outcome_blind(artifact)
    if (
        artifact.get("schema") != SCHEMA
        or artifact.get("status") != STATUS
        or artifact.get("valid") is not True
        or artifact.get("economic_values_exposed") is not False
        or artifact.get("contract_self_root_sha256")
        != self_root(artifact, "contract_self_root_sha256")
    ):
        raise ValueError("execution_contract_identity_invalid")
    git_root = Path(git_root).resolve()
    sealing_commit = str(artifact.get("sealing_code_commit") or "")
    if len(sealing_commit) != 40:
        raise ValueError("execution_contract_sealing_commit_invalid")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", sealing_commit, "HEAD"],
        cwd=git_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    code_rows = artifact.get("code_authority")
    if not isinstance(code_rows, list) or not code_rows:
        raise ValueError("execution_contract_code_authority_missing")
    paths = []
    for row in code_rows:
        if not isinstance(row, Mapping):
            raise ValueError("execution_contract_code_row_invalid")
        relative = Path(str(row.get("path") or ""))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("execution_contract_code_path_invalid")
        path = (git_root / relative).resolve()
        try:
            path.relative_to(git_root)
        except ValueError:
            raise ValueError("execution_contract_code_path_invalid") from None
        if (
            not path.is_file()
            or path.is_symlink()
            or file_sha256(path) != row.get("sha256")
        ):
            raise ValueError(f"execution_contract_code_drift:{relative}")
        paths.append(str(relative))
    if paths != sorted(set(paths)):
        raise ValueError("execution_contract_code_inventory_invalid")

    for binding_name, self_field in (
        ("partial_golden", "manifest_self_root_sha256"),
        ("partial_golden_amendment", "amendment_self_root_sha256"),
    ):
        binding = artifact.get(binding_name)
        if not isinstance(binding, Mapping):
            raise ValueError(f"execution_contract_{binding_name}_missing")
        bound_path = Path(str(binding.get("path") or ""))
        if not bound_path.is_absolute():
            bound_path = git_root / bound_path
        bound = load_canonical(bound_path)
        if (
            bound.get(self_field) != binding.get(self_field)
            or bound.get(self_field) != newline_self_root(bound, self_field)
            or file_sha256(bound_path) != binding.get("file_sha256")
        ):
            raise ValueError(f"execution_contract_{binding_name}_drift")

    variants = artifact.get("execution_variants")
    if not isinstance(variants, Mapping) or set(variants) != set(EXPECTED_VARIANTS):
        raise ValueError("execution_contract_variant_inventory_invalid")
    for name, workers in EXPECTED_VARIANTS.items():
        variant = variants[name]
        if not isinstance(variant, Mapping):
            raise ValueError("execution_contract_variant_invalid")
        _verify_command(variant, name=name, expected_workers=workers)
    permissions = artifact.get("permissions")
    if not isinstance(permissions, Mapping) or any(
        (
            permissions.get("other_arms") is not False,
            permissions.get("broker_live_vps_deployment") is not False,
            permissions.get("legacy_evidence_mutation") is not False,
            permissions.get("jan_8_31_continuation")
            != "CONDITIONAL_ON_INDEPENDENT_EXACT_FULL_RESULT_PARITY",
        )
    ):
        raise ValueError("execution_contract_permissions_invalid")
    report_core = {
        "schema": "gtos.replay_acceleration.real_s0r0_execution_contract_verification.v1",
        "valid": True,
        "status": "PROSPECTIVE_REAL_ACCELERATED_S0R0_ROUTE_VERIFIED",
        "contract_self_root_sha256": artifact["contract_self_root_sha256"],
        "sealing_code_commit": sealing_commit,
        "code_authority_count": len(code_rows),
        "variant_count": len(variants),
        "economic_values_exposed": False,
        "writer_imported": False,
        "runner_imported": False,
    }
    return {**report_core, "verification_root_sha256": root(report_core)}


def atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise ValueError("execution_contract_verification_output_exists")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(canonical_bytes(value) + b"\n")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify_execution_contract(args.artifact, git_root=args.git_root)
    atomic_write(args.output, report)
    print(
        canonical_bytes(
            {
                "valid": True,
                "verification_root_sha256": report[
                    "verification_root_sha256"
                ],
                "economic_values_exposed": False,
            }
        ).decode("ascii")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
