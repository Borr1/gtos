#!/usr/bin/env python3
"""Default-off helpers for future compliant VPS migration checks.

The commands here are local/read-only by default. They do not import MT5 unless
future code adds an explicit execute-readonly path; this route only ships dry
plans and verifiers for already-exported files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]

RESTRICTED_COUNTRIES = {
    "bangladesh",
    "myanmar",
    "belarus",
    "north korea",
    "syria",
    "grenada",
    "chad",
    "malaysia",
    "belize",
    "antigua and barbuda",
    "cape verde",
    "tuvalu",
    "vietnam",
    "bouvet island",
    "burundi",
    "cook islands",
    "eritrea",
    "comoros",
    "sri lanka",
    "fiji",
}

ACTIVE_SYMBOLS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_result(value: dict[str, Any], *, as_json: bool) -> int:
    if as_json:
        print(json.dumps(value, indent=2, sort_keys=True))
    else:
        print(value)
    return 0 if value.get("ok", True) else 1


def sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def classify_network_origin(origin: dict[str, Any]) -> dict[str, Any]:
    country = str(origin.get("country") or origin.get("country_name") or "").strip()
    country_code = str(origin.get("country_code") or "").strip().upper()
    country_key = country.lower()
    is_us = country_key in {"united states", "usa", "us"} or country_code == "US"
    restricted = country_key in RESTRICTED_COUNTRIES
    issues = []
    if restricted:
        issues.append("network_origin_restricted_country")
    if is_us:
        issues.append("network_origin_united_states_not_allowed_for_mt5")
    if not country and not country_code:
        issues.append("network_origin_country_missing")
    return {
        "country": country,
        "country_code": country_code,
        "restricted_country": restricted,
        "united_states_for_mt5": is_us,
        "ok_for_redacted_account_mt5": not issues,
        "issues": issues,
    }


def command_source_inventory(args: argparse.Namespace) -> int:
    root = Path(args.repo_root).resolve()
    roots = ["data", "shadow_logs", "pipeline_state", "knowledge_base", "config", "src", "tests"]
    rows = []
    for rel_root in roots:
        path = root / rel_root
        files = 0
        bytes_total = 0
        if path.exists():
            for item in path.rglob("*"):
                if item.is_file():
                    files += 1
                    try:
                        bytes_total += item.stat().st_size
                    except OSError:
                        pass
        rows.append({"root": rel_root, "exists": path.exists(), "files": files, "bytes": bytes_total})
    return write_result(
        {
            "schema_version": "default_off_source_inventory_v1",
            "generated_at_utc": now_iso(),
            "ok": all(row["exists"] for row in rows if row["root"] in {"config", "src", "tests"}),
            "rows": rows,
            "no_broker_access": True,
        },
        as_json=args.json,
    )


def command_mt5_readiness_plan(args: argparse.Namespace) -> int:
    return write_result(
        {
            "schema_version": "default_off_mt5_readiness_plan_v1",
            "generated_at_utc": now_iso(),
            "ok": True,
            "default_off": True,
            "requires_before_execute_readonly": [
                "network_origin_json_ok_for_redacted_account_mt5",
                "dedicated_private_vps_proof",
                "redacted_account VPS/EA add-on or fee proof where applicable",
                "secrets_present_without_printing_values",
            ],
            "symbols": ACTIVE_SYMBOLS,
            "read_only_exports": [
                "symbol_info all fields",
                "history_orders_get",
                "history_deals_get",
                "orders_get snapshot",
                "positions_get snapshot",
                "bars and tick coverage",
            ],
            "forbidden_calls": ["order_send", "order_modify", "order_cancel", "position_close"],
        },
        as_json=args.json,
    )


def command_broker_history_verify(args: argparse.Namespace) -> int:
    path = Path(args.input)
    issues = []
    rows = 0
    required_any = {"ticket", "order", "position_id", "symbol"}
    seen_keys: set[str] = set()
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                rows += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    issues.append(f"line_{line_no}_invalid_json")
                    continue
                if not isinstance(row, dict):
                    issues.append(f"line_{line_no}_not_object")
                    continue
                seen_keys.update(row)
    except OSError as exc:
        issues.append(f"cannot_read_input:{exc}")
    if rows == 0:
        issues.append("no_export_rows")
    if not (required_any & seen_keys):
        issues.append("missing_broker_history_identifier_fields")
    return write_result(
        {
            "schema_version": "default_off_broker_history_export_verification_v1",
            "generated_at_utc": now_iso(),
            "ok": not issues,
            "issues": issues,
            "rows": rows,
            "seen_keys": sorted(seen_keys),
            "no_broker_access": True,
        },
        as_json=args.json,
    )


def _csv_has_rows(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            next(reader, None)
            return next(reader, None) is not None
    except OSError:
        return False


def command_capture_health(args: argparse.Namespace) -> int:
    root = Path(args.repo_root).resolve()
    missing = []
    symbol_rows = []
    for symbol in ACTIVE_SYMBOLS:
        tick_dir = root / "data" / "ticks" / symbol
        m1_dir = root / "data" / "m1" / symbol
        tick_files = list(tick_dir.glob("*")) if tick_dir.exists() else []
        m1_files = list(m1_dir.glob("*.csv")) if m1_dir.exists() else []
        if not tick_files:
            missing.append(f"{symbol}:tick")
        if not m1_files or not any(_csv_has_rows(path) for path in m1_files[:3]):
            missing.append(f"{symbol}:m1")
        symbol_rows.append(
            {
                "symbol": symbol,
                "tick_files": len(tick_files),
                "m1_csv_files": len(m1_files),
            }
        )
    return write_result(
        {
            "schema_version": "default_off_capture_health_v1",
            "generated_at_utc": now_iso(),
            "ok": not missing,
            "missing": missing,
            "symbols": symbol_rows,
            "no_broker_access": True,
        },
        as_json=args.json,
    )


def command_hash_verify(args: argparse.Namespace) -> int:
    manifest = read_json(Path(args.manifest), {})
    issues = []
    artifacts = manifest.get("artifacts") or []
    for artifact in artifacts:
        path = REPO_ROOT / str(artifact.get("path", "")).replace("\\", "/")
        expected = artifact.get("sha256")
        if not path.exists():
            issues.append(f"missing_artifact:{artifact.get('path')}")
            continue
        if expected and sha256_file(path) != expected:
            issues.append(f"hash_mismatch:{artifact.get('path')}")
    return write_result(
        {
            "schema_version": "default_off_hash_verify_v1",
            "generated_at_utc": now_iso(),
            "ok": not issues,
            "issues": issues,
            "checked": len(artifacts),
            "no_broker_access": True,
        },
        as_json=args.json,
    )


def command_startup_preflight(args: argparse.Namespace) -> int:
    origin = read_json(Path(args.network_origin_json), {})
    classification = classify_network_origin(origin)
    issues = list(classification["issues"])
    if not args.dedicated_private_vps_proof:
        issues.append("dedicated_private_vps_proof_missing")
    if not args.vps_ea_addon_proof:
        issues.append("vps_ea_addon_or_fee_proof_missing")
    return write_result(
        {
            "schema_version": "default_off_startup_preflight_v1",
            "generated_at_utc": now_iso(),
            "ok": not issues,
            "issues": issues,
            "network_origin": classification,
            "live_runtime_start_allowed": False,
            "next_step": "read_only_exports_only_after_all_issues_clear",
        },
        as_json=args.json,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("source-inventory")
    p.add_argument("--repo-root", default=str(REPO_ROOT))
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_source_inventory)

    p = sub.add_parser("mt5-readiness-plan")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_mt5_readiness_plan)

    p = sub.add_parser("broker-history-export-verify")
    p.add_argument("--input", required=True)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_broker_history_verify)

    p = sub.add_parser("capture-health")
    p.add_argument("--repo-root", default=str(REPO_ROOT))
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_capture_health)

    p = sub.add_parser("hash-verify")
    p.add_argument("--manifest", required=True)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_hash_verify)

    p = sub.add_parser("startup-preflight")
    p.add_argument("--network-origin-json", required=True)
    p.add_argument("--dedicated-private-vps-proof", default="")
    p.add_argument("--vps-ea-addon-proof", default="")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_startup_preflight)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
