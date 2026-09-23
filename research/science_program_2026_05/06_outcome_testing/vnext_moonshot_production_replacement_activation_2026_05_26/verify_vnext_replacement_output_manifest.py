from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"

MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
RESULT_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_VERIFIER_{DATE}.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _resolve(path_text: str, route_dir: Path = ROUTE_DIR) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    repo_path = REPO_ROOT / path
    if repo_path.exists():
        return repo_path
    return route_dir / path


def _load_manifest(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _is_manifest_self(path: Path, manifest_path: Path = MANIFEST_PATH) -> bool:
    try:
        return path.resolve() == manifest_path.resolve()
    except FileNotFoundError:
        return False


def _verify_entries(
    manifest: dict[str, Any],
    *,
    manifest_path: Path = MANIFEST_PATH,
    route_dir: Path = ROUTE_DIR,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    outputs = manifest.get("outputs")
    if not isinstance(outputs, list):
        return [{"issue": "manifest_outputs_not_list"}]
    for index, entry in enumerate(outputs):
        path_text = entry.get("path")
        if not path_text:
            issues.append({"entry_index": index, "issue": "missing_path"})
            continue
        path = _resolve(str(path_text), route_dir)
        if not path.exists():
            issues.append(
                {
                    "entry_index": index,
                    "issue": "listed_artifact_missing",
                    "path": str(path_text),
                }
            )
            continue
        if path.is_dir():
            if entry.get("directory_entry_policy") != "directory_exists_files_hashed_by_child_manifest_or_shards":
                issues.append(
                    {
                        "entry_index": index,
                        "issue": "directory_entry_missing_policy",
                        "path": str(path_text),
                    }
                )
            continue
        if _is_manifest_self(path, manifest_path):
            if entry.get("sha256"):
                issues.append(
                    {
                        "entry_index": index,
                        "issue": "manifest_self_entry_must_not_claim_fixed_hash",
                        "path": str(path_text),
                    }
                )
            continue
        actual_hash = _sha256(path)
        if entry.get("sha256") != actual_hash:
            issues.append(
                {
                    "actual_sha256": actual_hash,
                    "entry_index": index,
                    "expected_sha256": entry.get("sha256"),
                    "issue": "sha256_mismatch",
                    "path": str(path_text),
                }
            )
        actual_size = path.stat().st_size
        if entry.get("size_bytes") != actual_size:
            issues.append(
                {
                    "actual_size_bytes": actual_size,
                    "entry_index": index,
                    "expected_size_bytes": entry.get("size_bytes"),
                    "issue": "size_bytes_mismatch",
                    "path": str(path_text),
                }
            )
    return issues


def _repair_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    repaired = dict(manifest)
    repaired_outputs: list[dict[str, Any]] = []
    for entry in manifest.get("outputs", []):
        repaired_entry = dict(entry)
        path_text = repaired_entry.get("path")
        if path_text:
            path = _resolve(str(path_text))
            if path.exists() and path.is_dir():
                repaired_entry.pop("sha256", None)
                repaired_entry.pop("size_bytes", None)
                repaired_entry["directory_entry_policy"] = (
                    "directory_exists_files_hashed_by_child_manifest_or_shards"
                )
            elif path.exists() and path.is_file():
                if _is_manifest_self(path):
                    repaired_entry.pop("sha256", None)
                    repaired_entry.pop("size_bytes", None)
                    repaired_entry["self_hash_policy"] = (
                        "verified_by_manifest_verifier_result_not_fixed_inside_self"
                    )
                else:
                    repaired_entry["sha256"] = _sha256(path)
                    repaired_entry["size_bytes"] = path.stat().st_size
        repaired_outputs.append(repaired_entry)
    repaired["outputs"] = repaired_outputs
    repaired["last_updated_utc"] = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    repaired["manifest_hash_policy"] = {
        "all_listed_file_outputs_except_manifest_self_have_sha256_and_size": True,
        "manifest_self_entry_policy": (
            "self hash is non-fixed because writing the hash changes the manifest; "
            "the verifier result records the post-write manifest hash"
        ),
    }
    return repaired


def run(*, write: bool) -> tuple[dict[str, Any], int]:
    manifest = _load_manifest()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if write:
        manifest = _repair_manifest(manifest)
        MANIFEST_PATH.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest = _load_manifest()
    issues = _verify_entries(manifest)
    manifest_hash = _sha256(MANIFEST_PATH)
    result = {
        "generated_at_utc": generated_at,
        "issue_count": len(issues),
        "issues": issues[:200],
        "manifest_path": _rel(MANIFEST_PATH),
        "manifest_sha256": manifest_hash,
        "mode": "write" if write else "check",
        "output_count": len(manifest.get("outputs", [])),
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_output_manifest_verifier_v1",
        "status": "passed" if not issues else "failed",
    }
    if write:
        RESULT_PATH.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return result, 0 if not issues else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify without mutating files")
    mode.add_argument("--write", action="store_true", help="repair manifest hashes and write result")
    args = parser.parse_args()
    result, exit_code = run(write=args.write)
    print(json.dumps({k: result[k] for k in ["status", "issue_count", "mode", "output_count"]}, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
