#!/usr/bin/env python3
"""Verify the FTMO local profile and VPS dual-production prep route.

This verifier is offline. It checks route artifacts, generated profile geometry,
account redaction, alias/spec completeness, and manifest hashes. It does not
connect to MT5 and cannot mutate broker state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = Path(__file__).resolve().parent

if str(REPO_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT))

from scripts.verify_broker_profile import VNEXT_24_SYMBOLS, verify_profile  # noqa: E402


EXPECTED_FTMO_ALIASES = {
    "GER40": "GER40.cash",
    "JP225": "JP225.cash",
    "NAS100": "US100.cash",
    "SPX500": "US500.cash",
    "UK100": "UK100.cash",
    "UKOIL_cash": "UKOIL.cash",
    "US30_cash": "US30.cash",
    "USOIL_cash": "USOIL.cash",
}

REQUIRED_ROUTE_FILES = (
    "FTMO_MT5_RAW_CAPTURE_LEDGER.json",
    "FTMO_ACCOUNT_IDENTITY_PROOF.json",
    "OFFICIAL_FTMO_SOURCE_INDEX.json",
    "FTMO_SYMBOL_INVENTORY_LEDGER.jsonl",
    "VNEXT_FTMO_ALIAS_RESOLUTION_LEDGER.jsonl",
    "FTMO_SYMBOL_SPEC_LEDGER.jsonl",
    "FTMO_SESSION_SPREAD_COST_HISTORY_DEPTH_LEDGER.jsonl",
    "FTMO_YAML_STALE_COMPARISON_LEDGER.jsonl",
    "PROFILE_VERIFIER_RESULT.json",
    "LOCAL_RUNTIME_DUAL_BROKER_READINESS_AUDIT_LEDGER.jsonl",
    "LOCAL_IMPLEMENTATION_CHANGE_LEDGER.jsonl",
    "VPS_DUAL_PRODUCTION_IMPLEMENTATION_CONTRACT.md",
    "VPS_SESSION_STARTER_INSTRUCTION.txt",
    "UNRESOLVED_OWNER_VPS_EXPORT_REQUIREMENT_LEDGER.jsonl",
    "SATURATION_SELF_RED_TEAM_LEDGER.md",
    "OUTPUT_MANIFEST.json",
    "COMPLETION_AUDIT.json",
    "ROUTE_CONTEXT_ANCHOR.json",
    "build_vnext_ftmo_local_profile_and_vps_dual_prod_prep.py",
    "verify_vnext_ftmo_local_profile_and_vps_dual_prod_prep.py",
    "templates/ftmo_readonly_preflight.ps1",
    "templates/vps_dual_process_groups.ps1",
    "templates/rollback_stop_by_namespace.ps1",
)

REQUIRED_SPEC_FIELDS = (
    "trade_tick_size",
    "trade_tick_value",
    "trade_contract_size",
    "volume_min",
    "volume_max",
    "volume_step",
    "trade_stops_level",
    "trade_freeze_level",
    "spread",
    "spread_float",
)

SKIP_MANIFEST_NAMES = {"builder_stdout.log", "builder_stderr.log", "builder.pid"}


def is_manifest_excluded(path: Path) -> bool:
    return "__pycache__" in path.parts or path.suffix == ".pyc" or path.name in SKIP_MANIFEST_NAMES


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _as_number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _append_manifest_artifact(
    artifacts: list[dict[str, Any]],
    seen_paths: set[str],
    path: Path,
    repo_root: Path,
    *,
    source_class: str,
    validation_state: str,
) -> None:
    if not path.exists() or not path.is_file() or is_manifest_excluded(path):
        return
    key = str(path.resolve()).lower()
    if key in seen_paths:
        return
    seen_paths.add(key)
    artifacts.append(
        {
            "path": _rel(path, repo_root),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "source_class": source_class,
            "validation_state": validation_state,
        }
    )


def write_manifest(route_dir: Path, repo_root: Path) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for path in sorted(route_dir.rglob("*")):
        if path.is_file():
            _append_manifest_artifact(
                artifacts,
                seen_paths,
                path,
                repo_root,
                source_class="route_output",
                validation_state=(
                    "route_verifier_output"
                    if path.name == "VERIFICATION_RESULT.json"
                    else "verified_by_route_verifier"
                ),
            )
    for row in read_jsonl(route_dir / "LOCAL_IMPLEMENTATION_CHANGE_LEDGER.jsonl"):
        rel_path = row.get("path")
        if not rel_path:
            continue
        _append_manifest_artifact(
            artifacts,
            seen_paths,
            repo_root / rel_path,
            repo_root,
            source_class="local_implementation_or_profile_output",
            validation_state="verified_by_route_verifier",
        )
    manifest = {
        "schema_version": "ftmo_route_output_manifest_v1",
        "route_id": route_dir.name,
        "generated_at_utc": utc_now(),
        "artifact_count": len(artifacts),
        "self_hash_status": "OUTPUT_MANIFEST.json is self-referential; verifier excludes it from hash validation.",
        "artifacts": artifacts,
    }
    write_json(route_dir / "OUTPUT_MANIFEST.json", manifest)
    return manifest


def verify_route(
    route_dir: Path = ROUTE_DIR,
    repo_root: Path = REPO_ROOT,
    *,
    write_result: bool = True,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for rel in REQUIRED_ROUTE_FILES:
        if not (route_dir / rel).exists():
            issues.append({"code": "missing_required_route_file", "path": rel})

    context_path = route_dir / "ROUTE_CONTEXT_ANCHOR.json"
    context = read_json(context_path) if context_path.exists() else {}
    canonical_profile_name = context.get("canonical_profile_name")
    profile_path = repo_root / "config" / "profiles" / f"{canonical_profile_name}.yaml"
    ftmo_profile_path = repo_root / "config" / "profiles" / "ftmo.yaml"
    if not canonical_profile_name:
        issues.append({"code": "missing_canonical_profile_name"})
    if canonical_profile_name and not profile_path.exists():
        issues.append({"code": "missing_generated_profile", "path": _rel(profile_path, repo_root)})

    raw_capture = read_json(route_dir / "FTMO_MT5_RAW_CAPTURE_LEDGER.json") if (route_dir / "FTMO_MT5_RAW_CAPTURE_LEDGER.json").exists() else {}
    if raw_capture.get("status") != "captured":
        issues.append({"code": "mt5_capture_not_captured", "status": raw_capture.get("status")})
    account = raw_capture.get("account") if isinstance(raw_capture.get("account"), dict) else {}
    if account.get("login") not in {None, "<redacted>"}:
        issues.append({"code": "raw_account_login_not_redacted", "value": account.get("login")})
    for field in ("login_sha256", "server", "company", "currency"):
        if not account.get(field):
            issues.append({"code": "missing_redacted_account_identity_field", "field": field})

    official_rows = read_json(route_dir / "OFFICIAL_FTMO_SOURCE_INDEX.json") if (route_dir / "OFFICIAL_FTMO_SOURCE_INDEX.json").exists() else []
    if official_rows:
        failed_sources = [row for row in official_rows if row.get("fetch_status") != "captured"]
        if failed_sources:
            issues.append({"code": "official_ftmo_source_not_captured", "count": len(failed_sources)})
    else:
        issues.append({"code": "official_source_index_empty_or_missing"})

    alias_rows = read_jsonl(route_dir / "VNEXT_FTMO_ALIAS_RESOLUTION_LEDGER.jsonl")
    alias_by_symbol = {row.get("symbol"): row for row in alias_rows}
    if len(alias_rows) != len(VNEXT_24_SYMBOLS):
        issues.append({"code": "alias_ledger_wrong_count", "count": len(alias_rows)})
    missing_alias_symbols = [symbol for symbol in VNEXT_24_SYMBOLS if symbol not in alias_by_symbol]
    if missing_alias_symbols:
        issues.append({"code": "alias_ledger_missing_active_symbols", "symbols": missing_alias_symbols})
    unresolved = [
        row for row in alias_rows
        if row.get("alias_status") != "resolved" or not row.get("mt5_symbol")
    ]
    if unresolved:
        issues.append({"code": "unresolved_active_aliases", "count": len(unresolved), "symbols": [row.get("symbol") for row in unresolved]})
    alias_counts = Counter(str(row.get("mt5_symbol")).upper() for row in alias_rows if row.get("mt5_symbol"))
    duplicated = {alias: count for alias, count in alias_counts.items() if count > 1}
    if duplicated:
        issues.append({"code": "duplicate_ftmo_aliases", "aliases": duplicated})
    for symbol, expected_alias in EXPECTED_FTMO_ALIASES.items():
        actual = alias_by_symbol.get(symbol, {}).get("mt5_symbol")
        if actual != expected_alias:
            issues.append({"code": "known_ftmo_alias_mismatch", "symbol": symbol, "expected": expected_alias, "actual": actual})

    spec_rows = read_jsonl(route_dir / "FTMO_SYMBOL_SPEC_LEDGER.jsonl")
    specs_by_symbol = {row.get("symbol"): row for row in spec_rows}
    if len(spec_rows) != len(VNEXT_24_SYMBOLS):
        issues.append({"code": "spec_ledger_wrong_count", "count": len(spec_rows)})
    for symbol in VNEXT_24_SYMBOLS:
        spec = specs_by_symbol.get(symbol)
        if not spec:
            issues.append({"code": "missing_symbol_spec", "symbol": symbol})
            continue
        for field in REQUIRED_SPEC_FIELDS:
            if field not in spec:
                issues.append({"code": "missing_symbol_spec_field", "symbol": symbol, "field": field})
        for field in ("trade_tick_size", "trade_tick_value", "trade_contract_size", "volume_min", "volume_max", "volume_step"):
            number = _as_number(spec.get(field))
            if number is None or number <= 0:
                issues.append({"code": "non_positive_symbol_spec_field", "symbol": symbol, "field": field, "value": spec.get(field)})

    session_rows = read_jsonl(route_dir / "FTMO_SESSION_SPREAD_COST_HISTORY_DEPTH_LEDGER.jsonl")
    if len(session_rows) != len(VNEXT_24_SYMBOLS):
        issues.append({"code": "session_history_ledger_wrong_count", "count": len(session_rows)})
    for row in session_rows:
        hist = row.get("history_depth") if isinstance(row.get("history_depth"), dict) else {}
        if not hist.get("bars"):
            issues.append({"code": "missing_history_depth_bars", "symbol": row.get("symbol")})
        if not hist.get("ticks"):
            warnings.append({"code": "missing_or_empty_tick_depth", "symbol": row.get("symbol")})

    comparison_rows = read_jsonl(route_dir / "FTMO_YAML_STALE_COMPARISON_LEDGER.jsonl")
    if len(comparison_rows) != len(VNEXT_24_SYMBOLS):
        issues.append({"code": "ftmo_yaml_comparison_wrong_count", "count": len(comparison_rows)})

    profile_result = verify_profile(profile_path) if profile_path.exists() else {"ok": False, "issues": [{"code": "missing_generated_profile"}]}
    stored_profile_result = read_json(route_dir / "PROFILE_VERIFIER_RESULT.json") if (route_dir / "PROFILE_VERIFIER_RESULT.json").exists() else {}
    if profile_result.get("ok") is not True:
        issues.append({"code": "generated_profile_verifier_failed", "issues": profile_result.get("issues", [])})
    if stored_profile_result.get("ok") != profile_result.get("ok"):
        issues.append({"code": "stored_profile_verifier_result_stale", "stored_ok": stored_profile_result.get("ok"), "current_ok": profile_result.get("ok")})

    if ftmo_profile_path.exists() and canonical_profile_name:
        ftmo_profile = yaml.safe_load(ftmo_profile_path.read_text(encoding="utf-8")) or {}
        if ftmo_profile.get("profile_alias_for") != canonical_profile_name:
            issues.append(
                {
                    "code": "ftmo_yaml_not_demoted_to_account_profile_pointer",
                    "profile_alias_for": ftmo_profile.get("profile_alias_for"),
                }
            )

    runtime_rows = read_jsonl(route_dir / "LOCAL_RUNTIME_DUAL_BROKER_READINESS_AUDIT_LEDGER.jsonl")
    if not runtime_rows:
        issues.append({"code": "runtime_dual_broker_audit_empty"})
    for row in runtime_rows:
        if not row.get("required_local_change") or row.get("required_local_change") == "none":
            warnings.append({"code": "runtime_audit_no_local_change_required", "file_path": row.get("file_path")})
        if not row.get("required_vps_change"):
            issues.append({"code": "runtime_audit_missing_vps_change", "file_path": row.get("file_path")})

    implementation_rows = read_jsonl(route_dir / "LOCAL_IMPLEMENTATION_CHANGE_LEDGER.jsonl")
    implementation_paths = {row.get("path") for row in implementation_rows}
    for required_path in (
        "src/utils/broker_profile.py",
        "scripts/verify_broker_profile.py",
        _rel(route_dir / "verify_vnext_ftmo_local_profile_and_vps_dual_prod_prep.py", repo_root),
        "tests/test_vnext_ftmo_local_profile_and_vps_dual_prod_prep.py",
    ):
        if required_path not in implementation_paths:
            issues.append({"code": "implementation_ledger_missing_path", "path": required_path})

    manifest_path = route_dir / "OUTPUT_MANIFEST.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        for artifact in manifest.get("artifacts", []):
            artifact_rel = artifact.get("path")
            if not artifact_rel:
                continue
            path = repo_root / artifact_rel
            if is_manifest_excluded(path):
                continue
            if not path.exists():
                issues.append({"code": "manifest_artifact_missing", "path": artifact_rel})
                continue
            if path.name in {"OUTPUT_MANIFEST.json", "VERIFICATION_RESULT.json"}:
                continue
            current_hash = sha256_file(path)
            if artifact.get("sha256") != current_hash:
                issues.append({"code": "manifest_hash_mismatch", "path": artifact_rel})

    completion_path = route_dir / "COMPLETION_AUDIT.json"
    completion = read_json(completion_path) if completion_path.exists() else {}
    if completion.get("mt5_capture_status") != "captured":
        issues.append({"code": "completion_audit_capture_not_captured"})
    if completion.get("profile_verifier_ok") is not True:
        issues.append({"code": "completion_audit_profile_verifier_not_ok"})

    result = {
        "schema_version": "ftmo_route_verification_result_v1",
        "route_id": route_dir.name,
        "generated_at_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "warning_count": len(warnings),
        "issues": issues,
        "warnings": warnings,
        "counts": {
            "alias_rows": len(alias_rows),
            "resolved_aliases": sum(1 for row in alias_rows if row.get("alias_status") == "resolved"),
            "symbol_specs": len(spec_rows),
            "session_history_rows": len(session_rows),
            "runtime_audit_rows": len(runtime_rows),
            "implementation_rows": len(implementation_rows),
        },
        "canonical_profile_name": canonical_profile_name,
        "profile_verifier_ok": profile_result.get("ok"),
    }

    if write_result:
        write_json(route_dir / "VERIFICATION_RESULT.json", result)
        manifest = write_manifest(route_dir, repo_root)
        if completion_path.exists():
            completion["route_verifier_ok"] = result["ok"]
            completion["route_verifier_result"] = _rel(route_dir / "VERIFICATION_RESULT.json", repo_root)
            completion["manifest_artifact_count"] = manifest.get("artifact_count")
            completion["can_mark_goal_complete"] = bool(
                result["ok"]
                and completion.get("mt5_capture_status") == "captured"
                and completion.get("profile_verifier_ok") is True
            )
            write_json(completion_path, completion)
        write_manifest(route_dir, repo_root)

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-dir", type=Path, default=ROUTE_DIR)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    result = verify_route(args.route_dir, args.repo_root, write_result=not args.no_write)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
