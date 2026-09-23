from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CROSS_INSTRUMENT_CORR_LOGGER_ACTIVATION"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
CONFIG_PATH = REPO / "config/agent_config.yaml"
LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"
EXPECTED_ROWS = 4
EXPECTED_MANIFEST_OUTPUT_COUNT = 2


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def config_logger_enabled() -> bool:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    logger_cfg = ((config.get("shadow_loggers") or {}).get("cross_instrument_correlation_decisions_logger") or {})
    return bool(logger_cfg.get("enabled"))


def verify() -> dict[str, Any]:
    issues: list[str] = []
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != EXPECTED_ROWS:
        issues.append(f"activation_rows_unexpected:{len(rows)}")
    if summary.get("activation_rows") != len(rows):
        issues.append(f"summary_rows_mismatch:{summary.get('activation_rows')}:{len(rows)}")
    if config_logger_enabled() is not True:
        issues.append("config_logger_not_enabled")
    if summary.get("config_cross_instrument_correlation_decisions_logger_enabled") is not True:
        issues.append("summary_config_logger_not_enabled")

    for key in (
        "gate_calls_logger",
        "logger_config_gated",
        "logger_failure_isolated",
        "permissions_context_present",
        "orchestrator_context_present",
        "tests_cover_enabled_write",
        "tests_cover_disabled_no_write",
        "runtime_halt_active",
    ):
        if summary.get(key) is not True:
            issues.append(f"{key}_not_true:{summary.get(key)}")

    effect = summary.get("implementation_effect") or {}
    if effect.get("config_shadow_logger_enabled") is not True:
        issues.append("effect_config_shadow_logger_not_enabled")
    if effect.get("future_observation_only_capture_when_runtime_reenabled") is not True:
        issues.append("effect_future_capture_not_enabled")
    for key in (
        "current_runtime_restart_now",
        "runtime_decision_effect",
        "prompt_risk_execution_effect",
        "broker_operation",
        "paid_api_or_vendor_call",
    ):
        if effect.get(key) is not False:
            issues.append(f"effect_{key}_unexpected:{effect.get(key)}")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (LEDGER, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
            break
    if len(output_by_name) != EXPECTED_MANIFEST_OUTPUT_COUNT:
        issues.append(f"manifest_output_count_unexpected:{len(output_by_name)}")

    for row in rows:
        row_id = row.get("activation_row_id")
        for key in ("broker_operation", "paid_api_or_vendor_call"):
            if row.get(key):
                issues.append(f"{key}_claimed:{row_id}")
                break
        if row.get("runtime_decision_effect"):
            issues.append(f"runtime_decision_effect_claimed:{row_id}")
            break
        if row.get("prompt_risk_execution_effect"):
            issues.append(f"prompt_risk_execution_effect_claimed:{row_id}")
            break

    result = {
        "route_id": ROUTE_ID,
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "activation_rows": len(rows),
        "config_cross_instrument_correlation_decisions_logger_enabled": summary.get(
            "config_cross_instrument_correlation_decisions_logger_enabled"
        ),
        "runtime_halt_active": summary.get("runtime_halt_active"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
