"""Measured resource and retention architecture for bounded replay acceleration."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import resource
import subprocess
import sys
import time
import zlib
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA = "gtos.replay_acceleration.resource_architecture_result.v1"
GIB = 1024**3
DISK_WARNING_BYTES = 34 * GIB
DISK_HARD_FLOOR_BYTES = 28 * GIB
SCRATCH_QUOTA_BYTES = 1 * GIB
LEGACY_PID = 34389

SOURCE_DIR = Path(
    "research/operations/replay_acceleration_bounded_slice_2026_07_19"
)
NORMALIZED_DIR = Path(
    "research/operations/replay_acceleration_normalized_slice_2026_07_19"
)
CANDIDATE_DIR = Path(
    "research/operations/replay_acceleration_candidate_boundary_2026_07_19"
)
REDUCER_DIR = Path(
    "research/operations/replay_acceleration_isolated_reducers_2026_07_19"
)
TYPED_DIR = Path(
    "research/operations/replay_acceleration_typed_proofs_2026_07_19"
)
RESUME_DIR = Path(
    "research/operations/replay_acceleration_resume_2026_07_19"
)

RESULT_PATHS = {
    "source": SOURCE_DIR / "BOUNDED_EQUIVALENCE_RESULT.json",
    "normalization": NORMALIZED_DIR / "NORMALIZATION_EQUIVALENCE_RESULT.json",
    "candidate_boundary": CANDIDATE_DIR / "CANDIDATE_BOUNDARY_RESULT.json",
    "isolated_reducers": REDUCER_DIR / "ISOLATED_REDUCER_RESULT.json",
    "typed_proofs": TYPED_DIR / "TYPED_PROOF_RESULT.json",
    "resume": RESUME_DIR / "RESUME_RESULT.json",
}


class ResourceError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_usage(path: Path) -> dict[str, int]:
    allocated = 0
    logical = 0
    files = 0
    for candidate in path.rglob("*"):
        if not candidate.is_file():
            continue
        stat = candidate.stat()
        logical += stat.st_size
        allocated += stat.st_blocks * 512
        files += 1
    return {
        "allocated_bytes": allocated,
        "logical_bytes": logical,
        "file_count": files,
    }


def enforce_resource_gate(
    *, available_bytes: int, bounded_slice_allocated_bytes: Iterable[int]
) -> None:
    if available_bytes < DISK_HARD_FLOOR_BYTES:
        raise ResourceError("disk_hard_floor_threatened")
    if any(value >= SCRATCH_QUOTA_BYTES for value in bounded_slice_allocated_bytes):
        raise ResourceError("bounded_slice_quota_not_strictly_below_limit")


def _disk() -> dict[str, Any]:
    stat = os.statvfs(Path.cwd())
    available = stat.f_bavail * stat.f_frsize
    return {
        "available_bytes": available,
        "warning_bytes": DISK_WARNING_BYTES,
        "hard_floor_bytes": DISK_HARD_FLOOR_BYTES,
        "above_warning": available >= DISK_WARNING_BYTES,
        "hard_floor_respected": available >= DISK_HARD_FLOOR_BYTES,
        "margin_above_hard_floor_bytes": available - DISK_HARD_FLOOR_BYTES,
    }


def _swap() -> dict[str, Any]:
    completed = subprocess.run(
        ["sysctl", "-n", "vm.swapusage"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return {"available": False}
    values = {
        key.lower(): float(value)
        for key, value in re.findall(r"(total|used|free) = ([0-9.]+)M", completed.stdout)
    }
    return {
        "available": len(values) == 3,
        "total_bytes": int(values.get("total", 0.0) * 1024**2),
        "used_bytes": int(values.get("used", 0.0) * 1024**2),
        "free_bytes": int(values.get("free", 0.0) * 1024**2),
    }


def _legacy_process() -> dict[str, Any]:
    completed = subprocess.run(
        ["ps", "-o", "pid=,state=", "-p", str(LEGACY_PID)],
        check=False,
        capture_output=True,
        text=True,
    )
    fields = completed.stdout.strip().split()
    return {
        "pid": LEGACY_PID,
        "observed": bool(fields),
        "state": fields[1] if len(fields) > 1 else None,
        "modified_or_signaled": False,
    }


def _bounded_slice_inventory() -> list[dict[str, Any]]:
    source = json.loads(RESULT_PATHS["source"].read_bytes())
    normalized = json.loads(RESULT_PATHS["normalization"].read_bytes())
    rows = [
        {
            "name": "source_equivalence_scratch",
            "path": (SOURCE_DIR / "scratch").as_posix(),
            **source["combined_retained_scratch"],
        },
        {
            "name": "normalization_scratch",
            "path": (NORMALIZED_DIR / "scratch").as_posix(),
            **normalized["combined_retained_scratch"],
        },
    ]
    for name, path in (
        ("candidate_boundary_evidence", CANDIDATE_DIR),
        ("isolated_reducer_evidence", REDUCER_DIR),
        ("typed_proof_evidence", TYPED_DIR),
        ("resume_evidence", RESUME_DIR),
    ):
        rows.append({"name": name, "path": path.as_posix(), **tree_usage(path)})
    for row in rows:
        row["quota_bytes"] = SCRATCH_QUOTA_BYTES
        row["strictly_below_quota"] = row["allocated_bytes"] < SCRATCH_QUOTA_BYTES
    return rows


def _proof_files() -> list[Path]:
    files: list[Path] = []
    for directory in (CANDIDATE_DIR, REDUCER_DIR, TYPED_DIR, RESUME_DIR):
        files.extend(path for path in directory.rglob("*") if path.is_file())
    for directory in (SOURCE_DIR, NORMALIZED_DIR):
        files.extend(
            path
            for path in directory.iterdir()
            if path.is_file()
        )
    return sorted(set(files), key=lambda path: path.as_posix())


def _hash_probe() -> dict[str, Any]:
    start = time.perf_counter_ns()
    rows = [
        {
            "path": path.as_posix(),
            "logical_bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        }
        for path in _proof_files()
    ]
    elapsed = time.perf_counter_ns() - start
    return {
        "scope": "proof_and_contract_files_excluding_large_accepted_cache_payloads",
        "files": rows,
        "file_count": len(rows),
        "bytes_hashed": sum(row["logical_bytes"] for row in rows),
        "wall_ns": elapsed,
        "inventory_root_sha256": stable_sha256(rows),
    }


def _compression_probe() -> dict[str, Any]:
    paths = sorted((TYPED_DIR / "shards").glob("*.gtp"))
    payload = b"".join(path.read_bytes() for path in paths)
    start = time.perf_counter_ns()
    compressed = zlib.compress(payload, level=6)
    elapsed = time.perf_counter_ns() - start
    if zlib.decompress(compressed) != payload:
        raise ResourceError("compression_probe_roundtrip_mismatch")
    return {
        "scope": "typed_structural_shards_in_memory_only",
        "algorithm": "zlib_level_6_probe_not_route_authority",
        "input_bytes": len(payload),
        "compressed_bytes": len(compressed),
        "ratio": round(len(compressed) / len(payload), 9),
        "wall_ns": elapsed,
        "persistent_compressed_artifact_created": False,
    }


VERIFIER_COMMANDS = (
    (
        "candidate_boundary",
        [
            sys.executable,
            "-m",
            "src.research_infra.replay_acceleration_candidate_boundary_verifier",
            RESULT_PATHS["candidate_boundary"].as_posix(),
        ],
    ),
    (
        "isolated_reducers",
        [
            sys.executable,
            "-m",
            "src.research_infra.replay_acceleration_isolated_reducers_verifier",
            RESULT_PATHS["isolated_reducers"].as_posix(),
        ],
    ),
    (
        "typed_proofs",
        [
            sys.executable,
            "-m",
            "src.research_infra.replay_acceleration_typed_proofs_verifier",
            RESULT_PATHS["typed_proofs"].as_posix(),
        ],
    ),
    (
        "resume",
        [
            sys.executable,
            "-m",
            "src.research_infra.replay_acceleration_resume_verifier",
            RESULT_PATHS["resume"].as_posix(),
        ],
    ),
)


def _verification_probes() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, command in VERIFIER_COMMANDS:
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.perf_counter_ns()
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        wall_ns = time.perf_counter_ns() - start
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        if completed.returncode != 0:
            raise ResourceError(f"verification_probe_failed:{label}")
        try:
            receipt = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ResourceError(f"verification_probe_receipt_invalid:{label}") from exc
        if receipt.get("status") != "VERIFIED":
            raise ResourceError(f"verification_probe_not_verified:{label}")
        rows.append(
            {
                "label": label,
                "status": "VERIFIED",
                "command": command,
                "receipt_sha256": hashlib.sha256(
                    completed.stdout.encode("utf-8")
                ).hexdigest(),
                "wall_ns": wall_ns,
                "user_ns": int((after.ru_utime - before.ru_utime) * 1_000_000_000),
                "system_ns": int((after.ru_stime - before.ru_stime) * 1_000_000_000),
                "peak_rss_native_upper_bound": int(after.ru_maxrss),
                "peak_rss_unit": "bytes_on_darwin_kib_elsewhere",
                "minor_page_faults": int(after.ru_minflt - before.ru_minflt),
                "major_page_faults": int(after.ru_majflt - before.ru_majflt),
                "blocks_read": int(after.ru_inblock - before.ru_inblock),
                "blocks_written": int(after.ru_oublock - before.ru_oublock),
            }
        )
    return rows


def _accepted_stage_measurements() -> dict[str, Any]:
    source = json.loads(RESULT_PATHS["source"].read_bytes())
    normalization = json.loads(RESULT_PATHS["normalization"].read_bytes())
    candidate = json.loads(RESULT_PATHS["candidate_boundary"].read_bytes())
    reducer = json.loads(RESULT_PATHS["isolated_reducers"].read_bytes())
    typed = json.loads(RESULT_PATHS["typed_proofs"].read_bytes())
    resume = json.loads(RESULT_PATHS["resume"].read_bytes())
    return {
        "source": {
            "label": "bounded_all_symbol_source_stage_not_whole_replay",
            "runs": source["resource_measurements"],
        },
        "normalization": {
            "label": "bounded_all_symbol_normalization_stage_not_whole_replay",
            "runs": normalization["resource_measurements"],
        },
        "candidate_boundary": candidate["measurement"],
        "isolated_reducers": reducer["measurement"],
        "typed_proofs": typed["measurement"],
        "resume": resume["measurement"],
    }


def build_resource_result() -> dict[str, Any]:
    disk = _disk()
    slices = _bounded_slice_inventory()
    enforce_resource_gate(
        available_bytes=disk["available_bytes"],
        bounded_slice_allocated_bytes=[row["allocated_bytes"] for row in slices],
    )
    aggregate = sum(row["allocated_bytes"] for row in slices)
    hash_probe = _hash_probe()
    compression_probe = _compression_probe()
    verification = _verification_probes()
    writer_path = Path(__file__).resolve()
    verifier_path = writer_path.with_name(
        "replay_acceleration_resource_architecture_verifier.py"
    )
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "ACCEPTED",
        "gate": "RESOURCE_STORAGE_ARCHITECTURE_ACCEPTED",
        "disk": disk,
        "swap": _swap(),
        "legacy_process": _legacy_process(),
        "retention": {
            "bounded_slices": slices,
            "aggregate_retained_allocated_bytes": aggregate,
            "aggregate_exceeds_single_slice_quota": aggregate >= SCRATCH_QUOTA_BYTES,
            "quota_semantics": "strict_per_bounded_slice_not_aggregate_retention",
            "reclaim_candidates": [
                {
                    "path": (SOURCE_DIR / "scratch" / "cold_repeat").as_posix(),
                    "status": "retained_requires_explicit_reclaim_authorization",
                },
                {
                    "path": (NORMALIZED_DIR / "scratch" / "cold_repeat").as_posix(),
                    "status": "retained_requires_explicit_reclaim_authorization",
                },
            ],
            "files_deleted": 0,
            "bytes_reclaimed": 0,
            "unique_proof_evidence_preserved": True,
            "broad_lfs_hydration_performed": False,
            "lfs_prune_performed": False,
        },
        "accepted_stage_measurements": _accepted_stage_measurements(),
        "verification_probes": verification,
        "hash_probe": hash_probe,
        "compression_probe": compression_probe,
        "measurements": {
            "whole_replay_speed_claim": False,
            "source_stage_only_labels_preserved": True,
            "bytes_read_written_where_available": True,
            "page_faults_recorded": True,
            "peak_rss_recorded": True,
            "scratch_recorded": True,
        },
        "code_identity": {
            "writer_path": writer_path.relative_to(Path.cwd()).as_posix(),
            "writer_sha256": file_sha256(writer_path),
            "independent_verifier_path": verifier_path.relative_to(Path.cwd()).as_posix(),
            "independent_verifier_sha256": file_sha256(verifier_path),
        },
        "execution": {
            "policy_callbacks_invoked": False,
            "successor_arm_execution_launched": False,
            "production_action": False,
        },
    }
    result["result_root_sha256"] = stable_sha256(result)
    return result


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(canonical_bytes(payload) + b"\n")
    os.replace(temporary, path)


def write_resource_result(output_dir: Path) -> Path:
    result = build_resource_result()
    result["exact_command_receipt"] = [
        sys.executable,
        "-m",
        __name__,
        "--output-dir",
        output_dir.as_posix(),
    ]
    result.pop("result_root_sha256", None)
    result["result_root_sha256"] = stable_sha256(result)
    path = output_dir / "RESOURCE_ARCHITECTURE_RESULT.json"
    _atomic_json(path, result)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    path = write_resource_result(args.output_dir)
    payload = json.loads(path.read_bytes())
    print(
        json.dumps(
            {
                "gate": payload["gate"],
                "available_bytes": payload["disk"]["available_bytes"],
                "result_root_sha256": payload["result_root_sha256"],
                "output": path.as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
