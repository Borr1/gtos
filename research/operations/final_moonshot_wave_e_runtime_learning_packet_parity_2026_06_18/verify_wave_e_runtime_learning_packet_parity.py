#!/usr/bin/env python3
"""Verify Wave E runtime-learning packet parity artifacts and code wiring."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROUTE = Path(__file__).resolve().parent
REPO = ROUTE.parents[2]
RESULT = ROUTE / "VERIFICATION_RESULT.json"

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.components.ultimate_book.runtime_learning_packet import (  # noqa: E402
    DEFAULT_LOG_PATH,
    DEFAULT_REDACTION_POLICY,
    SCHEMA_VERSION,
    build_runtime_learning_packet,
    packet_schema,
    validate_runtime_learning_packet,
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    issues: list[str] = []
    required = [
        "RUNTIME_LEARNING_PACKET_SCHEMA.json",
        "RUNTIME_LEARNING_FIELD_COVERAGE_LEDGER.jsonl",
        "RUNTIME_LEARNING_EVENT_COVERAGE_LEDGER.jsonl",
        "REDACTION_AND_FORBIDDEN_SURFACE_AUDIT.json",
        "DECISION_LEDGER.jsonl",
        "MONITORING_AND_ROLLBACK_TRIGGER_LEDGER.jsonl",
        "BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl",
        "SATURATION_SELF_RED_TEAM_LEDGER.jsonl",
        "FOCUSED_TEST_RESULT.json",
        "RUNTIME_LEARNING_DEPLOYMENT_VALUE_SUMMARY.md",
        "VPS_CODEX_RUNTIME_LEARNING_PACKET_PROMPT.md",
        "OUTPUT_MANIFEST.json",
        "COMPLETION_AUDIT.json",
        "NEXT_PROMPT.md",
    ]
    for name in required:
        if not (ROUTE / name).exists():
            issues.append(f"missing_artifact:{name}")

    if (ROUTE / "RUNTIME_LEARNING_PACKET_SCHEMA.json").exists():
        schema = _read_json(ROUTE / "RUNTIME_LEARNING_PACKET_SCHEMA.json")
        expected = packet_schema()
        if schema.get("schema_version") != SCHEMA_VERSION:
            issues.append("schema_version_mismatch")
        if schema.get("log_path_default") != DEFAULT_LOG_PATH:
            issues.append("default_log_path_mismatch")
        if schema.get("redaction_policy") != DEFAULT_REDACTION_POLICY:
            issues.append("redaction_policy_mismatch")
        for field in expected["required_fields"]:
            if field not in schema.get("required_fields", []):
                issues.append(f"schema_missing_required_field:{field}")

    sample = build_runtime_learning_packet(
        namespace="verify",
        event_type="unit_placed",
        bridge={"runtime_effect_now": True, "market_expansion_policy": "positive_weighted12_after_swap"},
        unit={"sleeve_members": ["ny_crypto_momentum"], "unit_risk_pct": 0.001},
        outcome={
            "ticket": 111,
            "account_login": "222",
            "server": "broker-live",
            "symbol": "BTCUSD",
            "sleeve": "ny_crypto_momentum",
            "placement_status": "placed",
        },
    )
    ok, packet_issues = validate_runtime_learning_packet(sample)
    if not ok:
        issues.append("sample_packet_invalid:" + ",".join(packet_issues))
    text = json.dumps(sample, sort_keys=True)
    for forbidden in ['"ticket":', '"account_login":', '"server":']:
        if forbidden in text:
            issues.append(f"raw_identifier_leak:{forbidden}")

    config_text = (REPO / "config/agent_config.yaml").read_text(encoding="utf-8")
    config_required = {
        "ultimate_book_runtime_learning_packet_enabled: true": "config_packet_enabled_missing",
        "ultimate_book_runtime_learning_packet_log_enabled: true": "config_packet_log_enabled_missing",
        f'ultimate_book_runtime_learning_packet_log_path: "{DEFAULT_LOG_PATH}"': "config_log_path_missing",
        f'ultimate_book_runtime_learning_packet_schema: "{SCHEMA_VERSION}"': "config_schema_missing",
        f'ultimate_book_runtime_learning_redaction_policy: "{DEFAULT_REDACTION_POLICY}"': "config_redaction_missing",
    }
    for needle, issue in config_required.items():
        if needle not in config_text:
            issues.append(issue)

    code_checks = {
        "src/components/ultimate_book/runtime_learning_packet.py": [
            "RuntimeLearningPacketWriter",
            "validate_runtime_learning_packet",
            "FORBIDDEN_RAW_KEYS",
        ],
        "src/components/ultimate_book/book_owner.py": [
            "_emit_cycle_runtime_learning",
            "_emit_management_runtime_learning",
            "build_runtime_learning_packet",
        ],
        "src/components/ultimate_book/launcher.py": ["runtime_learning"],
        "src/components/ultimate_book/bridge.py": [
            "ultimate_book_runtime_learning_packet_enabled",
            "RUNTIME_LEARNING_PACKET_SCHEMA_VERSION",
        ],
        "tests/ultimate_book/test_runtime_learning_packet.py": [
            "test_runtime_learning_packet_hashes_ticket_and_account_identifiers",
            "test_book_owner_shadow_cycle_writes_runtime_learning_packet",
        ],
        "tests/ultimate_book/test_launcher.py": ["runtime_learning"],
    }
    for rel, needles in code_checks.items():
        path = REPO / rel
        if not path.exists():
            issues.append(f"missing_code_file:{rel}")
            continue
        content = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in content:
                issues.append(f"missing_code_string:{rel}:{needle}")

    if (ROUTE / "FOCUSED_TEST_RESULT.json").exists():
        focused = _read_json(ROUTE / "FOCUSED_TEST_RESULT.json")
        if focused.get("status") != "pass":
            issues.append("focused_tests_not_pass")
        if "46 passed" not in focused.get("pytest_result", ""):
            issues.append("focused_pytest_count_missing")

    if (ROUTE / "RUNTIME_LEARNING_FIELD_COVERAGE_LEDGER.jsonl").exists():
        fields = _read_jsonl(ROUTE / "RUNTIME_LEARNING_FIELD_COVERAGE_LEDGER.jsonl")
        if len(fields) < len(packet_schema()["required_fields"]):
            issues.append("field_coverage_too_small")
        if not any("raw identifiers" in row.get("field", "") for row in fields):
            issues.append("field_coverage_missing_identifier_policy")

    if (ROUTE / "RUNTIME_LEARNING_EVENT_COVERAGE_LEDGER.jsonl").exists():
        events = _read_jsonl(ROUTE / "RUNTIME_LEARNING_EVENT_COVERAGE_LEDGER.jsonl")
        event_names = {row.get("event_type") for row in events}
        for event_type in packet_schema()["event_types"]:
            if event_type not in event_names:
                issues.append(f"event_coverage_missing:{event_type}")

    prompt = ROUTE / "VPS_CODEX_RUNTIME_LEARNING_PACKET_PROMPT.md"
    if prompt.exists():
        prompt_text = prompt.read_text(encoding="utf-8")
        for needle in [
            "Do not apply unrelated Mac branch history",
            "no broker/account/order/deal/position mutation",
            "VPS_RUNTIME_LEARNING_PACKET_DELTA.patch",
            "ultimate_book_runtime_learning_packet_enabled",
        ]:
            if needle not in prompt_text:
                issues.append(f"vps_prompt_missing:{needle}")

    patch = ROUTE / "VPS_RUNTIME_LEARNING_PACKET_DELTA.patch"
    patch_required = patch.exists()
    if patch_required:
        if patch.stat().st_size <= 0:
            issues.append("patch_file_empty")
        patch_text = patch.read_text(encoding="utf-8", errors="replace")
        for needle in [
            "src/components/ultimate_book/runtime_learning_packet.py",
            "ultimate_book_runtime_learning_packet_enabled",
            "tests/ultimate_book/test_runtime_learning_packet.py",
        ]:
            if needle not in patch_text:
                issues.append(f"patch_missing:{needle}")
    else:
        issues.append("missing_artifact:VPS_RUNTIME_LEARNING_PACKET_DELTA.patch")

    result = {
        "schema": "gtos.final_moonshot.wave_e.verification_result.v1",
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "route": ROUTE.relative_to(REPO).as_posix(),
        "packet_schema": SCHEMA_VERSION,
        "default_log_path": DEFAULT_LOG_PATH,
        "patch_present": patch.exists(),
        "evidence_class": "production_code_observation_layer_vps_checkpoint",
        "broker_runtime_change_status": False,
        "orderflow_or_depth_used": False,
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
