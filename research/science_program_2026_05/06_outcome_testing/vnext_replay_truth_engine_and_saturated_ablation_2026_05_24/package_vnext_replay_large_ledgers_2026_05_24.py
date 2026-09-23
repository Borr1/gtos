"""Package oversized vNext replay ledgers into push-safe JSONL chunks.

This is an artifact-packaging utility only. It does not call replay, ablation,
robustness, MIXED-resolution, or repair builders. The chunker preserves exact
JSONL row bytes and records reconstruction order in a machine-readable manifest.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
MAX_CHUNK_BYTES = 1_750_000_000
MAX_UNCOMPRESSED_BYTES_PER_CHUNK = 1_600_000_000
GITHUB_LFS_LIMIT_BYTES = 2_000_000_000
SOFT_LIMIT_BYTES = 1_800_000_000

CHUNK_MANIFEST_PATH = ROUTE_DIR / "VNEXT_REPLAY_LFS_CHUNK_MANIFEST_2026-05-24.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / "VNEXT_REPLAY_OUTPUT_MANIFEST_2026-05-24.json"
COMPLETION_AUDIT_PATH = ROUTE_DIR / "VNEXT_REPLAY_COMPLETION_AUDIT_2026-05-24.json"
FINAL_REPORT_PATH = ROUTE_DIR / "VNEXT_REPLAY_FINAL_REPORT_2026-05-24.md"
SESSION_STATE_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/gtos_vnext_replay_truth_engine"
    / "VNEXT_REPLAY_TRUTH_ENGINE_SESSION_STATE_2026-05-24.json"
)
PACKAGING_SCRIPT_PATH = Path(__file__).resolve()

LEDGER_SPECS = [
    {
        "ledger_id": "saturated_replay",
        "original_path": ROUTE_DIR / "VNEXT_REPLAY_SATURATED_REPLAY_LEDGER_2026-05-24.jsonl",
        "description": "Stage05 saturated replay ledger",
    },
    {
        "ledger_id": "ablation",
        "original_path": ROUTE_DIR / "VNEXT_REPLAY_ABLATION_LEDGER_2026-05-24.jsonl",
        "description": "Stage06 ablation ledger",
    },
]

METHODOLOGY_SCOPE = (
    "This completed package is a logged-event replay truth package, not the full "
    "historical all-market candidate-generation replay."
)
NEXT_PHASE_SCOPE = (
    "The next phase is full historical vNext candidate generation over all available "
    "OHLC/M1/M5/tick/Sierra data, with source repair/acquisition as needed and "
    "simulated R/path-ordering as the primary historical performance truth. "
    "Broker-realized execution fields are later live/demo calibration, not a blocker "
    "for historical simulated replay."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def run_git(args: list[str], *, allow_failure: bool = False) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8").strip()
    except Exception as exc:  # pragma: no cover - defensive metadata capture
        if allow_failure:
            return f"git {' '.join(args)} failed: {exc}"
        raise


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, allow_nan=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def iter_chunks_for_spec(original_path: Path) -> Iterable[Path]:
    yield from sorted(ROUTE_DIR.glob(f"{original_path.stem}.chunk-*.jsonl.gz"))


def artifact_record(path: Path, source_kind: str) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
        "lines": count_rows(path) if path.exists() else 0,
        "sha256": sha256_file(path) if path.exists() else None,
        "source_kind": source_kind,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_rows(path: Path) -> int:
    rows = 0
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rb") as handle:
        for _line in handle:
            rows += 1
    return rows


def file_metadata(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "byte_size": path.stat().st_size,
        "sha256": sha256_file(path),
        "row_count": count_rows(path),
    }


def remove_existing_chunks(original_path: Path) -> None:
    for chunk_path in iter_chunks_for_spec(original_path):
        chunk_path.unlink()
    for chunk_path in sorted(ROUTE_DIR.glob(f"{original_path.stem}.chunk-*.jsonl")):
        chunk_path.unlink()


def chunk_path_for(original_path: Path, index: int) -> Path:
    return ROUTE_DIR / f"{original_path.stem}.chunk-{index:04d}{original_path.suffix}.gz"


def chunk_ledger(spec: dict[str, Any]) -> dict[str, Any]:
    original_path = spec["original_path"]
    if not original_path.exists():
        raise FileNotFoundError(f"Required monolithic source file is missing: {original_path}")

    remove_existing_chunks(original_path)

    original_digest = hashlib.sha256()
    original_rows = 0
    original_bytes_seen = 0
    chunks: list[dict[str, Any]] = []

    current_handle = None
    current_raw_handle = None
    current_path: Path | None = None
    current_rows = 0
    current_uncompressed_bytes = 0
    chunk_index = 0

    def open_chunk() -> None:
        nonlocal current_handle, current_raw_handle, current_path, current_rows, current_uncompressed_bytes, chunk_index
        chunk_index += 1
        current_path = chunk_path_for(original_path, chunk_index)
        current_raw_handle = current_path.open("wb")
        current_handle = gzip.GzipFile(filename="", mode="wb", fileobj=current_raw_handle, mtime=0, compresslevel=6)
        current_rows = 0
        current_uncompressed_bytes = 0

    def close_chunk() -> None:
        nonlocal current_handle, current_raw_handle, current_path, current_rows, current_uncompressed_bytes
        if current_handle is None or current_path is None:
            return
        current_handle.close()
        if current_raw_handle is not None:
            current_raw_handle.close()
        compressed_size = current_path.stat().st_size
        compressed_sha = sha256_file(current_path)
        if compressed_size > MAX_CHUNK_BYTES or compressed_size >= SOFT_LIMIT_BYTES:
            raise AssertionError(f"Compressed chunk exceeds safe object size: {current_path} = {compressed_size}")
        chunks.append(
            {
                "chunk_index": len(chunks) + 1,
                "path": rel(current_path),
                "byte_size": compressed_size,
                "sha256": compressed_sha,
                "row_count": current_rows,
                "uncompressed_byte_size": current_uncompressed_bytes,
                "compression": "gzip_mtime0_compresslevel6",
            }
        )
        current_handle = None
        current_raw_handle = None
        current_path = None

    with original_path.open("rb") as source:
        for line in source:
            line_size = len(line)
            if line_size > MAX_UNCOMPRESSED_BYTES_PER_CHUNK:
                raise ValueError(
                    f"Single JSONL row in {original_path} is {line_size} bytes, "
                    f"larger than MAX_UNCOMPRESSED_BYTES_PER_CHUNK={MAX_UNCOMPRESSED_BYTES_PER_CHUNK}"
                )
            if current_handle is None:
                open_chunk()
            elif current_uncompressed_bytes > 0 and current_uncompressed_bytes + line_size > MAX_UNCOMPRESSED_BYTES_PER_CHUNK:
                close_chunk()
                open_chunk()

            assert current_handle is not None
            current_handle.write(line)
            current_rows += 1
            current_uncompressed_bytes += line_size
            original_digest.update(line)
            original_rows += 1
            original_bytes_seen += line_size

    close_chunk()

    original_size = original_path.stat().st_size
    if original_bytes_seen != original_size:
        raise AssertionError(f"Read byte count mismatch for {original_path}: {original_bytes_seen} != {original_size}")
    if not chunks:
        raise AssertionError(f"No chunks were written for {original_path}")

    return {
        "ledger_id": spec["ledger_id"],
        "description": spec["description"],
        "original_path": rel(original_path),
        "original_byte_size": original_size,
        "original_sha256": original_digest.hexdigest(),
        "original_row_count": original_rows,
        "max_chunk_bytes": MAX_CHUNK_BYTES,
        "max_uncompressed_bytes_per_chunk": MAX_UNCOMPRESSED_BYTES_PER_CHUNK,
        "chunk_compression": "gzip_mtime0_compresslevel6",
        "chunk_count": len(chunks),
        "chunks": chunks,
        "reconstruction_order": [chunk["path"] for chunk in chunks],
    }


def verify_package(manifest: dict[str, Any], *, require_references: bool = True) -> dict[str, Any]:
    verification: dict[str, Any] = {
        "schema_version": "vnext_replay_lfs_chunk_verification_v1",
        "generated_utc": utc_now(),
        "max_chunk_bytes": int(manifest["max_chunk_bytes"]),
        "ledgers": [],
        "pass": True,
    }
    for ledger in manifest["ledgers"]:
        concatenated_digest = hashlib.sha256()
        byte_total = 0
        row_total = 0
        uncompressed_byte_total = 0
        max_chunk_size = 0
        for chunk in ledger["chunks"]:
            path = REPO_ROOT / chunk["path"]
            if not path.exists():
                raise AssertionError(f"Missing chunk: {chunk['path']}")
            actual_size = path.stat().st_size
            actual_sha = sha256_file(path)
            actual_rows = 0
            actual_uncompressed_bytes = 0
            if actual_size != chunk["byte_size"]:
                raise AssertionError(f"Chunk byte mismatch for {chunk['path']}: {actual_size} != {chunk['byte_size']}")
            if actual_sha != chunk["sha256"]:
                raise AssertionError(f"Chunk sha mismatch for {chunk['path']}: {actual_sha} != {chunk['sha256']}")
            if actual_size > MAX_CHUNK_BYTES or actual_size >= SOFT_LIMIT_BYTES:
                raise AssertionError(f"Chunk exceeds safe object size: {chunk['path']} = {actual_size}")
            with gzip.open(path, "rb") as handle:
                for line in handle:
                    concatenated_digest.update(line)
                    actual_rows += 1
                    actual_uncompressed_bytes += len(line)
            if actual_rows != chunk["row_count"]:
                raise AssertionError(f"Chunk row mismatch for {chunk['path']}: {actual_rows} != {chunk['row_count']}")
            if actual_uncompressed_bytes != chunk["uncompressed_byte_size"]:
                raise AssertionError(
                    f"Chunk uncompressed byte mismatch for {chunk['path']}: "
                    f"{actual_uncompressed_bytes} != {chunk['uncompressed_byte_size']}"
                )
            byte_total += actual_size
            row_total += actual_rows
            uncompressed_byte_total += actual_uncompressed_bytes
            max_chunk_size = max(max_chunk_size, actual_size)

        if uncompressed_byte_total != ledger["original_byte_size"]:
            raise AssertionError(
                f"Uncompressed byte total mismatch for {ledger['ledger_id']}: "
                f"{uncompressed_byte_total} != {ledger['original_byte_size']}"
            )
        if row_total != ledger["original_row_count"]:
            raise AssertionError(f"Row total mismatch for {ledger['ledger_id']}: {row_total} != {ledger['original_row_count']}")
        reconstructed_sha = concatenated_digest.hexdigest()
        if reconstructed_sha != ledger["original_sha256"]:
            raise AssertionError(
                f"Reconstructed sha mismatch for {ledger['ledger_id']}: "
                f"{reconstructed_sha} != {ledger['original_sha256']}"
            )

        original_path = REPO_ROOT / ledger["original_path"]
        original_present = original_path.exists()
        if original_present:
            original = file_metadata(original_path)
            if original["byte_size"] != ledger["original_byte_size"]:
                raise AssertionError(f"Original byte mismatch for {ledger['original_path']}")
            if original["row_count"] != ledger["original_row_count"]:
                raise AssertionError(f"Original row mismatch for {ledger['original_path']}")
            if original["sha256"] != ledger["original_sha256"]:
                raise AssertionError(f"Original sha mismatch for {ledger['original_path']}")

        verification["ledgers"].append(
            {
                "ledger_id": ledger["ledger_id"],
                "original_path": ledger["original_path"],
                "original_file_present": original_present,
                "original_byte_size": ledger["original_byte_size"],
                "original_row_count": ledger["original_row_count"],
                "original_sha256": ledger["original_sha256"],
                "chunk_count": len(ledger["chunks"]),
                "chunk_compressed_byte_total": byte_total,
                "chunk_uncompressed_byte_total": uncompressed_byte_total,
                "chunk_row_total": row_total,
                "max_chunk_byte_size": max_chunk_size,
                "reconstructed_sha256": reconstructed_sha,
            }
        )

    if require_references:
        verify_references(manifest)
    return verification


def monolith_paths(manifest: dict[str, Any]) -> set[str]:
    return {ledger["original_path"] for ledger in manifest["ledgers"]}


def chunk_paths(manifest: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for ledger in manifest["ledgers"]:
        paths.extend(chunk["path"] for chunk in ledger["chunks"])
    return paths


def update_output_manifest(manifest: dict[str, Any]) -> None:
    existing = read_json(OUTPUT_MANIFEST_PATH)
    remove_paths = monolith_paths(manifest)
    records = {
        item["path"]: item
        for item in existing.get("outputs", [])
        if isinstance(item, dict) and item.get("path") not in remove_paths
    }
    records[rel(CHUNK_MANIFEST_PATH)] = artifact_record(CHUNK_MANIFEST_PATH, "generated_replay_chunk_manifest")
    records[rel(PACKAGING_SCRIPT_PATH)] = artifact_record(PACKAGING_SCRIPT_PATH, "generated_replay_packaging_verifier")
    records[rel(COMPLETION_AUDIT_PATH)] = artifact_record(COMPLETION_AUDIT_PATH, "generated_replay_output")
    records[rel(FINAL_REPORT_PATH)] = artifact_record(FINAL_REPORT_PATH, "generated_replay_report")
    for path in chunk_paths(manifest):
        records[path] = artifact_record(REPO_ROOT / path, "generated_replay_lfs_chunk")
    existing.update(
        {
            "generated_utc": utc_now(),
            "next_stage": "COMPLETE",
            "artifact_packaging": {
                "schema_version": "vnext_replay_lfs_chunk_packaging_v1",
                "chunk_manifest": rel(CHUNK_MANIFEST_PATH),
                "monolithic_paths_replaced": sorted(remove_paths),
                "max_chunk_bytes": MAX_CHUNK_BYTES,
                "max_uncompressed_bytes_per_chunk": MAX_UNCOMPRESSED_BYTES_PER_CHUNK,
                "github_lfs_single_object_limit_bytes": GITHUB_LFS_LIMIT_BYTES,
                "safe_object_limit_bytes": SOFT_LIMIT_BYTES,
                "no_replay_regenerated": True,
            },
            "outputs": [records[key] for key in sorted(records)],
        }
    )
    write_json(OUTPUT_MANIFEST_PATH, existing)


def update_completion_audit(manifest: dict[str, Any]) -> None:
    audit = read_json(COMPLETION_AUDIT_PATH)
    requirements = [req for req in audit.get("requirements", []) if req.get("requirement_id") != "lfs_chunk_packaging"]
    requirements.append(
        {
            "requirement_id": "lfs_chunk_packaging",
            "status": "complete",
            "evidence": rel(CHUNK_MANIFEST_PATH),
        }
    )
    audit.update(
        {
            "generated_utc": utc_now(),
            "requirements": requirements,
            "artifact_packaging": {
                "schema_version": "vnext_replay_lfs_chunk_packaging_v1",
                "chunk_manifest": rel(CHUNK_MANIFEST_PATH),
                "packaging_script": rel(PACKAGING_SCRIPT_PATH),
                "monolithic_paths_replaced": sorted(monolith_paths(manifest)),
                "chunk_paths": chunk_paths(manifest),
                "max_chunk_bytes": MAX_CHUNK_BYTES,
                "max_uncompressed_bytes_per_chunk": MAX_UNCOMPRESSED_BYTES_PER_CHUNK,
                "safe_object_limit_bytes": SOFT_LIMIT_BYTES,
                "verification": verify_package(manifest, require_references=False),
                "no_replay_regenerated": True,
            },
            "methodological_truth_scope": {
                "completed_package": METHODOLOGY_SCOPE,
                "next_phase": NEXT_PHASE_SCOPE,
            },
        }
    )
    write_json(COMPLETION_AUDIT_PATH, audit)


def update_final_report(manifest: dict[str, Any]) -> None:
    text = FINAL_REPORT_PATH.read_text(encoding="utf-8")
    marker = "\n## Artifact Packaging Addendum\n"
    if marker in text:
        text = text.split(marker, 1)[0]

    lines = [
        "## Artifact Packaging Addendum",
        "",
        METHODOLOGY_SCOPE,
        "",
        NEXT_PHASE_SCOPE,
        "",
        f"Chunk manifest: `{rel(CHUNK_MANIFEST_PATH)}`",
        "",
        "| Ledger | Original rows | Original bytes | Original sha256 | Chunk count | Max chunk bytes |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for ledger in manifest["ledgers"]:
        max_chunk = max(chunk["byte_size"] for chunk in ledger["chunks"])
        lines.append(
            f"| {ledger['ledger_id']} | {ledger['original_row_count']} | {ledger['original_byte_size']} | "
            f"`{ledger['original_sha256']}` | {ledger['chunk_count']} | {max_chunk} |"
        )
    lines.extend(
        [
            "",
            "The monolithic ledger paths are replaced for pushed history by the chunk files listed in the chunk manifest. "
            "Reconstruction order is the `reconstruction_order` array for each ledger.",
        ]
    )
    FINAL_REPORT_PATH.write_text(text.rstrip() + "\n\n" + "\n".join(lines).rstrip() + "\n", encoding="utf-8")


def update_session_state(manifest: dict[str, Any]) -> None:
    state = read_json(SESSION_STATE_PATH)
    remove_paths = monolith_paths(manifest)
    outputs = [path for path in state.get("current_output_artifacts", []) if path not in remove_paths]
    for path in [rel(CHUNK_MANIFEST_PATH), rel(PACKAGING_SCRIPT_PATH), *chunk_paths(manifest)]:
        if path not in outputs:
            outputs.append(path)
    tests = list(state.get("last_tests_or_verifiers") or [])
    verifier = (
        "python research/science_program_2026_05/06_outcome_testing/"
        "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/"
        "package_vnext_replay_large_ledgers_2026_05_24.py --check -> passed; "
        "oversized saturated/ablation ledgers replaced by chunk manifest"
    )
    if verifier not in tests:
        tests.append(verifier)
    state.update(
        {
            "updated_utc": utc_now(),
            "current_objective": "Final replay truth-freeze complete; push-safe LFS chunk packaging is materialized.",
            "current_output_artifacts": outputs,
            "last_tests_or_verifiers": tests,
            "artifact_packaging": {
                "schema_version": "vnext_replay_lfs_chunk_packaging_v1",
                "chunk_manifest": rel(CHUNK_MANIFEST_PATH),
                "monolithic_paths_replaced": sorted(remove_paths),
                "max_chunk_bytes": MAX_CHUNK_BYTES,
                "max_uncompressed_bytes_per_chunk": MAX_UNCOMPRESSED_BYTES_PER_CHUNK,
                "no_replay_regenerated": True,
            },
            "methodological_truth_scope": {
                "completed_package": METHODOLOGY_SCOPE,
                "next_phase": NEXT_PHASE_SCOPE,
            },
            "next_executable_action": (
                "Before any push, verify the unpushed LFS object set has no object over 2GB. "
                "Then push only after the oversized-object check is clean."
            ),
            "open_questions_remaining": [
                "Full historical all-market vNext candidate generation remains the next research phase; this package is logged-event replay truth.",
                "Broker-realized execution/fill fields remain a live/demo calibration input, not a blocker for historical simulated replay.",
            ],
        }
    )
    write_json(SESSION_STATE_PATH, state)


def verify_references(manifest: dict[str, Any]) -> None:
    output_manifest = read_json(OUTPUT_MANIFEST_PATH)
    output_paths = {item.get("path") for item in output_manifest.get("outputs", []) if isinstance(item, dict)}
    forbidden = monolith_paths(manifest)
    if output_paths.intersection(forbidden):
        raise AssertionError(f"Output manifest still references monolithic ledgers: {sorted(output_paths.intersection(forbidden))}")
    required_paths = {rel(CHUNK_MANIFEST_PATH), rel(PACKAGING_SCRIPT_PATH), *chunk_paths(manifest)}
    missing_output_paths = sorted(required_paths - output_paths)
    if missing_output_paths:
        raise AssertionError(f"Output manifest missing chunk package paths: {missing_output_paths}")

    audit = read_json(COMPLETION_AUDIT_PATH)
    if audit.get("artifact_packaging", {}).get("chunk_manifest") != rel(CHUNK_MANIFEST_PATH):
        raise AssertionError("Completion audit missing chunk packaging block")
    report = FINAL_REPORT_PATH.read_text(encoding="utf-8")
    for phrase in [METHODOLOGY_SCOPE, NEXT_PHASE_SCOPE, rel(CHUNK_MANIFEST_PATH)]:
        if phrase not in report:
            raise AssertionError(f"Final report missing packaging phrase: {phrase}")
    state = read_json(SESSION_STATE_PATH)
    state_outputs = set(state.get("current_output_artifacts") or [])
    if state_outputs.intersection(forbidden):
        raise AssertionError(f"Session state still references monolithic ledgers: {sorted(state_outputs.intersection(forbidden))}")
    missing_state_paths = sorted(required_paths - state_outputs)
    if missing_state_paths:
        raise AssertionError(f"Session state missing chunk package paths: {missing_state_paths}")


def build_package() -> dict[str, Any]:
    ledger_records = [chunk_ledger(spec) for spec in LEDGER_SPECS]
    manifest = {
        "schema_version": "vnext_replay_lfs_chunk_manifest_v1",
        "generated_utc": utc_now(),
        "max_chunk_bytes": MAX_CHUNK_BYTES,
        "max_uncompressed_bytes_per_chunk": MAX_UNCOMPRESSED_BYTES_PER_CHUNK,
        "safe_object_limit_bytes": SOFT_LIMIT_BYTES,
        "github_lfs_single_object_limit_bytes": GITHUB_LFS_LIMIT_BYTES,
        "no_replay_regenerated": True,
        "reconstruction_method": "Gunzip chunks in reconstruction_order for each ledger, then concatenate the uncompressed JSONL bytes.",
        "methodological_truth_scope": {
            "completed_package": METHODOLOGY_SCOPE,
            "next_phase": NEXT_PHASE_SCOPE,
        },
        "git": {
            "head": run_git(["rev-parse", "HEAD"], allow_failure=True),
            "commit": run_git(["log", "-1", "--oneline"], allow_failure=True),
        },
        "ledgers": ledger_records,
    }
    manifest["verification"] = verify_package(manifest, require_references=False)
    manifest["pass"] = bool(manifest["verification"]["pass"])
    write_json(CHUNK_MANIFEST_PATH, manifest)
    update_completion_audit(manifest)
    update_final_report(manifest)
    update_session_state(manifest)
    update_output_manifest(manifest)
    verify_package(manifest, require_references=True)
    return manifest


def check_package() -> dict[str, Any]:
    if not CHUNK_MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Chunk manifest missing: {CHUNK_MANIFEST_PATH}")
    manifest = read_json(CHUNK_MANIFEST_PATH)
    verification = verify_package(manifest, require_references=True)
    print(json.dumps(verification, indent=2, sort_keys=True))
    return verification


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_package()
        return
    manifest = build_package()
    print(json.dumps(manifest["verification"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
