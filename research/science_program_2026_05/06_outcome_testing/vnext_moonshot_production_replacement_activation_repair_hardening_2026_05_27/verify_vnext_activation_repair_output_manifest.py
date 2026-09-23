from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-27"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
MANIFEST = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def write_manifest(payload: dict[str, Any]) -> None:
    MANIFEST.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stage_for(path: Path) -> str:
    text = path.as_posix().lower()
    for stage in ("stage00", "stage01", "stage02", "stage03", "stage04", "stage05", "stage06", "stage07"):
        if stage in text:
            return stage.replace("stage", "stage_")
    if "stage_spine" in text:
        return "route_state"
    return "route_local"


def route_files() -> list[Path]:
    return sorted(
        path
        for path in ROUTE_DIR.rglob("*")
        if path.is_file()
        and path.name not in {".DS_Store"}
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    )


def build_outputs(files: list[Path], *, manifest_size_bytes: int | None = None) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for path in sorted(files, key=lambda item: rel(item)):
        self_entry = path == MANIFEST
        outputs.append(
            {
                "path": rel(path),
                "sha256": None if self_entry else sha256_file(path),
                "self_hash_policy": (
                    "excluded_self_referential_manifest_hash" if self_entry else None
                ),
                "size_bytes": (
                    manifest_size_bytes
                    if self_entry and manifest_size_bytes is not None
                    else path.stat().st_size
                ),
                "stage": stage_for(path),
                "status": "current",
            }
        )
    return outputs


def rebuild_manifest() -> dict[str, Any]:
    files = route_files()
    outputs = build_outputs(files)
    payload = {
        "schema_version": "vnext_activation_repair_manifest_v2",
        "route_id": ROUTE_ID,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "stage05_manifest_synchronized",
        "self_hash_policy": "manifest self-entry is present but sha256 is null to avoid self-reference",
        "self_size_policy": "manifest self-entry size_bytes must equal current manifest file size",
        "non_self_size_policy": "every non-self entry must match current disk size_bytes and sha256",
        "current_disk_file_count": len(files),
        "output_count": len(files),
        "outputs": outputs,
    }
    for _ in range(8):
        write_manifest(payload)
        observed_size = MANIFEST.stat().st_size
        for row in outputs:
            if row.get("path") == rel(MANIFEST):
                row["size_bytes"] = observed_size
                row["sha256"] = None
                row["self_hash_policy"] = "excluded_self_referential_manifest_hash"
                break
        payload["outputs"] = outputs
        payload["current_manifest_size_bytes"] = observed_size
        payload["output_count"] = len(payload["outputs"])
        payload["current_disk_file_count"] = len(route_files())
        write_manifest(payload)
        if MANIFEST.stat().st_size == observed_size:
            break
    return payload


def check_manifest(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    paths_seen: set[str] = set()
    current_paths = {rel(path) for path in route_files()}
    for row in payload.get("outputs") or []:
        rpath = row.get("path")
        if not rpath:
            issues.append("entry_missing_path")
            continue
        if rpath in paths_seen:
            issues.append(f"duplicate_path:{rpath}")
        paths_seen.add(rpath)
        path = REPO_ROOT / rpath
        if not path.exists():
            issues.append(f"missing_path:{rpath}")
            continue
        if row.get("sha256") is None:
            if path != MANIFEST:
                issues.append(f"missing_sha256_non_self:{rpath}")
            elif row.get("self_hash_policy") != "excluded_self_referential_manifest_hash":
                issues.append("manifest_self_hash_policy_missing")
            elif row.get("size_bytes") != MANIFEST.stat().st_size:
                issues.append("manifest_self_size_bytes_mismatch")
            continue
        if row.get("size_bytes") != path.stat().st_size:
            issues.append(f"size_mismatch:{rpath}")
        observed = sha256_file(path)
        if observed != row.get("sha256"):
            issues.append(f"hash_mismatch:{rpath}")
    missing_from_manifest = sorted(current_paths - paths_seen)
    extra_in_manifest = sorted(paths_seen - current_paths)
    for rpath in missing_from_manifest:
        issues.append(f"current_route_file_missing_from_manifest:{rpath}")
    for rpath in extra_in_manifest:
        issues.append(f"manifest_entry_not_on_disk:{rpath}")
    if payload.get("output_count") != len(payload.get("outputs") or []):
        issues.append("top_level_output_count_mismatch")
    if payload.get("current_disk_file_count") != len(current_paths):
        issues.append("top_level_current_disk_file_count_mismatch")
    if payload.get("non_self_size_policy") != "every non-self entry must match current disk size_bytes and sha256":
        issues.append("non_self_size_policy_missing_or_stale")
    required_names = {
        f"VNEXT_ACTIVATION_REPAIR_EXECUTION_ROUTER_LAUNCH_DOSSIER_{DATE}.json",
        f"VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_FREQUENCY_TRADE_R_SUMMARY_{DATE}.json",
        f"VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_SELECTED_TRADE_SHARD_MANIFEST_{DATE}.jsonl",
        f"VNEXT_ACTIVATION_REPAIR_STAGE04_MEMBERSHIP_AUDIT_SHARD_MANIFEST_{DATE}.jsonl",
        f"VNEXT_ACTIVATION_REPAIR_STAGE04_PRIOR_INTELLIGENCE_CONSUMPTION_LEDGER_{DATE}.jsonl",
        "final_dynamic_router_replay.manifest.jsonl",
        "final_dynamic_router_replay_summary.json",
        "momentum_policy_promotion.manifest.jsonl",
        "momentum_policy_promotion_summary.json",
        "momentum_exception_decision_ledger.jsonl",
        "selected_policy_risk_proof_summary.json",
        "momentum_policy_lifecycle_propagation_proof.json",
        f"momentum_policy_promotion_verifier_result_{DATE}.json",
        "build_execution_intelligence_dynamic_router_replay.py",
        "build_execution_policy_momentum_promotion.py",
        "build_execution_intelligence_static_15r_ceiling_repair.py",
        "build_launch_execution_router_dossier.py",
        "build_stage04_canonical_frequency_trade_r_ledger.py",
        "test_execution_intelligence_static_15r_ceiling_repair.py",
        "verify_execution_intelligence_dynamic_router_replay.py",
        "verify_execution_policy_momentum_promotion.py",
        "verify_execution_intelligence_static_15r_ceiling_repair.py",
        "verify_stage04_canonical_frequency_trade_r_ledger.py",
        "verify_stage03_mt5_aliases_readonly.py",
        "verify_stage03_production_extraction_readonly.py",
    }
    present_names = {Path(path).name for path in paths_seen}
    for name in sorted(required_names - present_names):
        issues.append(f"required_manifest_entry_missing:{name}")
    if rel(MANIFEST) not in paths_seen:
        issues.append("manifest_self_entry_missing")
    stale_abandoned = [
        path for path in paths_seen if "/execution_intelligence_static_15r_ceiling_repair/" in path
    ]
    for rpath in stale_abandoned:
        issues.append(f"stale_abandoned_ei15r_path_referenced:{rpath}")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync", action="store_true")
    args = parser.parse_args(argv)
    if args.sync:
        payload = rebuild_manifest()
    else:
        payload = load_manifest()
    issues = check_manifest(payload)
    result = {
        "mode": "sync" if args.sync else "check",
        "status": "passed" if not issues else "failed",
        "issue_count": len(issues),
        "issues": issues,
        "output_count": len(payload.get("outputs") or []),
        "current_disk_file_count": len(route_files()),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
