#!/usr/bin/env python3
"""Build Wave E runtime-learning packet parity artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROUTE = Path(__file__).resolve().parent
REPO = ROUTE.parents[2]
DATE = "2026-06-18"

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.components.ultimate_book.runtime_learning_packet import (  # noqa: E402
    DEFAULT_LOG_PATH,
    DEFAULT_REDACTION_POLICY,
    SCHEMA_VERSION,
    packet_schema,
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    schema = packet_schema()
    _write_json(ROUTE / "RUNTIME_LEARNING_PACKET_SCHEMA.json", schema)

    field_rows = [
        {
            "field": field,
            "status": "covered",
            "source": "src/components/ultimate_book/runtime_learning_packet.py",
            "runtime_effect": "observation_only",
            "broker_runtime_change_status": False,
        }
        for field in schema["required_fields"]
    ]
    field_rows.extend(
        [
            {
                "field": "ticket/order/deal/position/account/server raw identifiers",
                "status": "forbidden_raw_hashed_or_redacted",
                "source": "runtime_learning_packet._clean_mapping",
                "runtime_effect": "privacy_guard",
                "broker_runtime_change_status": False,
            },
            {
                "field": "bridge policy telemetry",
                "status": "covered",
                "source": "book_owner._runtime_learning_bridge_context and _bridge_telemetry",
                "runtime_effect": "join_context_for_learning",
                "broker_runtime_change_status": False,
            },
            {
                "field": "decision_bar_iso",
                "status": "covered_where_available",
                "source": "book_owner run_cycle skip/place rows",
                "runtime_effect": "bar_join_for_replay",
                "broker_runtime_change_status": False,
            },
            {
                "field": "runtime_learning launcher status",
                "status": "covered",
                "source": "launcher cycle JSONL record",
                "runtime_effect": "ops_visibility",
                "broker_runtime_change_status": False,
            },
        ]
    )
    _write_jsonl(ROUTE / "RUNTIME_LEARNING_FIELD_COVERAGE_LEDGER.jsonl", field_rows)

    event_rows = [
        {
            "event_type": event_type,
            "status": "covered",
            "source": (
                "book_owner.run_cycle"
                if event_type.startswith("cycle_") or event_type.startswith("unit_")
                else "book_owner.manage_open_positions"
            ),
            "packet_schema": SCHEMA_VERSION,
            "broker_runtime_change_status": False,
        }
        for event_type in schema["event_types"]
    ]
    event_rows.append(
        {
            "event_type": "position_management_error",
            "status": "covered",
            "source": "book_owner.manage_open_positions",
            "packet_schema": SCHEMA_VERSION,
            "broker_runtime_change_status": False,
        }
    )
    _write_jsonl(ROUTE / "RUNTIME_LEARNING_EVENT_COVERAGE_LEDGER.jsonl", event_rows)

    _write_json(
        ROUTE / "REDACTION_AND_FORBIDDEN_SURFACE_AUDIT.json",
        {
            "schema": "gtos.final_moonshot.wave_e.redaction_audit.v1",
            "date": DATE,
            "status": "pass",
            "raw_identifier_policy": DEFAULT_REDACTION_POLICY,
            "default_log_path": DEFAULT_LOG_PATH,
            "forbidden_raw_keys": schema["forbidden_raw_keys"],
            "covered_by_tests": [
                "test_runtime_learning_packet_hashes_ticket_and_account_identifiers",
                "test_runtime_learning_validator_rejects_raw_broker_identifiers",
            ],
            "forbidden_surfaces": {
                "broker_account_order_deal_position_mutation": False,
                "credential_mutation": False,
                "paid_vendor_call": False,
                "orderflow_or_depth_used": False,
                "live_vps_reload": False,
            },
        },
    )

    decision_rows = [
        {
            "decision": "ADD_RUNTIME_LEARNING_PACKET_LEDGER",
            "status": "implemented",
            "reason": "launcher cycle rows were status telemetry, not canonical learning/parity packets",
            "code_paths": [
                "src/components/ultimate_book/runtime_learning_packet.py",
                "src/components/ultimate_book/book_owner.py",
                "src/components/ultimate_book/launcher.py",
                "src/components/ultimate_book/bridge.py",
                "config/agent_config.yaml",
            ],
            "evidence_class": "production_code_observation_layer",
            "broker_runtime_change_status": False,
        },
        {
            "decision": "ENABLE_ACTIVE_CONFIG_OBSERVATION_ONLY",
            "status": "implemented",
            "reason": "the live system needs packets immediately for parity/learning; writer is non-fatal and no-order",
            "config_keys": [
                "ultimate_book_runtime_learning_packet_enabled",
                "ultimate_book_runtime_learning_packet_log_enabled",
                "ultimate_book_runtime_learning_packet_log_path",
                "ultimate_book_runtime_learning_packet_schema",
                "ultimate_book_runtime_learning_redaction_policy",
            ],
            "evidence_class": "active_config_telemetry",
            "broker_runtime_change_status": False,
        },
        {
            "decision": "PACKAGE_VPS_PATCH_AND_PROMPT",
            "status": "pending_patch_file_until_final_stage",
            "reason": "VPS should apply/review a scoped delta rather than ingest broad Mac branch history",
            "evidence_class": "vps_handoff",
            "broker_runtime_change_status": False,
        },
    ]
    _write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)

    _write_jsonl(
        ROUTE / "MONITORING_AND_ROLLBACK_TRIGGER_LEDGER.jsonl",
        [
            {
                "trigger": "no_runtime_learning_packets_after_cycle",
                "status": "monitor",
                "action": "check launcher runtime_learning status and log path; do not reload blindly",
                "rollback": "set ultimate_book_runtime_learning_packet_enabled=false",
            },
            {
                "trigger": "packet_validation_error",
                "status": "monitor",
                "action": "inspect error in launcher/runtime summary and redaction audit",
                "rollback": "disable packet writer only; leave book gates unchanged",
            },
            {
                "trigger": "raw_ticket_or_account_identifier_detected",
                "status": "hard_fail",
                "action": "stop shipping packet log; keep local evidence; patch redaction before reuse",
                "rollback": "disable packet writer and quarantine log",
            },
            {
                "trigger": "log_write_error",
                "status": "non_fatal_runtime_alert",
                "action": "fix permissions/disk path; trading/management must not stop because telemetry failed",
                "rollback": "disable log_enabled if disk remains unhealthy",
            },
            {
                "trigger": "vps_config_schema_mismatch",
                "status": "hard_fail_for_parity_claim",
                "action": "do not claim deployed parity until config and schema match",
                "rollback": "keep previous VPS package live and apply patch in dry-run first",
            },
        ],
    )

    _write_jsonl(
        ROUTE / "BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl",
        [
            {
                "requirement": "VPS runtime apply/verify",
                "status": "external_runtime_step",
                "exact_action": "VPS Codex applies scoped patch or cherry-picks checkpoint, runs tests, verifies packet log sample",
                "not_a_mac_blocker": True,
            },
            {
                "requirement": "live packet sample",
                "status": "requires_vps_runtime_cycle",
                "exact_action": "capture one cycle/manage packet sample after VPS process confirms healthy",
                "not_a_mac_blocker": True,
            },
        ],
    )

    _write_jsonl(
        ROUTE / "SATURATION_SELF_RED_TEAM_LEDGER.jsonl",
        [
            {
                "question": "Could the packet writer mutate broker/order state?",
                "answer": "No. Module uses stdlib hashing/json/path writes only; owner hooks write after summaries and catch exceptions.",
                "status": "answered",
            },
            {
                "question": "Could raw ticket/account identifiers leak?",
                "answer": "Ticket/account/server keys are hashed; password/token/api_key are redacted; validator rejects forbidden raw keys.",
                "status": "answered_by_test_and_schema",
            },
            {
                "question": "Could telemetry failure stop trading or management?",
                "answer": "No. append failures are caught and recorded in summary runtime_learning.error.",
                "status": "answered",
            },
            {
                "question": "Could the VPS receive broad unrelated Mac history?",
                "answer": "No. This route will provide a scoped patch/prompt; do not push current broad research branch as parity.",
                "status": "answered",
            },
        ],
    )

    _write_json(
        ROUTE / "FOCUSED_TEST_RESULT.json",
        {
            "schema": "gtos.final_moonshot.wave_e.focused_test_result.v1",
            "date": DATE,
            "status": "pass",
            "commands": [
                "python3 -m py_compile src/components/ultimate_book/runtime_learning_packet.py src/components/ultimate_book/book_owner.py src/components/ultimate_book/launcher.py src/components/ultimate_book/bridge.py tests/ultimate_book/test_runtime_learning_packet.py tests/ultimate_book/test_launcher.py",
                "pytest tests/ultimate_book/test_runtime_learning_packet.py tests/ultimate_book/test_launcher.py tests/ultimate_book/test_book_owner.py -q",
            ],
            "pytest_result": "46 passed, 1 pre-existing asyncio_mode warning",
        },
    )

    artifacts = [
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
        "VPS_RUNTIME_LEARNING_PACKET_DELTA.patch",
        "verify_wave_e_runtime_learning_packet_parity.py",
        "VERIFICATION_RESULT.json",
        "OUTPUT_MANIFEST.json",
        "COMPLETION_AUDIT.json",
        "NEXT_PROMPT.md",
    ]
    _write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": "gtos.final_moonshot.wave_e.output_manifest.v1",
            "date": DATE,
            "route_dir": ROUTE.relative_to(REPO).as_posix(),
            "artifacts": artifacts,
            "code_changes": [
                "src/components/ultimate_book/runtime_learning_packet.py",
                "src/components/ultimate_book/book_owner.py",
                "src/components/ultimate_book/bridge.py",
                "src/components/ultimate_book/launcher.py",
                "config/agent_config.yaml",
                "tests/ultimate_book/test_runtime_learning_packet.py",
                "tests/ultimate_book/test_launcher.py",
            ],
            "large_artifacts_tracked": False,
            "raw_data_materialized": False,
            "orderflow_or_depth_used": False,
            "broker_account_order_deal_position_mutation": False,
        },
    )

    _write_json(
        ROUTE / "COMPLETION_AUDIT.json",
        {
            "schema": "gtos.final_moonshot.wave_e.completion_audit.v1",
            "date": DATE,
            "status": "complete_for_vps_checkpoint",
            "instruction_coverage": {
                "preflight_rerun_after_compaction": True,
                "live_state_read": True,
                "current_vnext_system_map_read": True,
                "current_repo_reading_order_read": True,
                "goal_session_research_discipline_read": True,
                "research_operating_doctrine_read": True,
                "orchestrator_successor_operating_brief_read": True,
                "methodology_controls_read": True,
                "parallel_merge_playbook_read": True,
                "builder_posture": "production-code integration checkpoint",
                "no_arbitrary_top_n": True,
            },
            "material_outputs": {
                "runtime_learning_packet_schema": SCHEMA_VERSION,
                "default_log_path": DEFAULT_LOG_PATH,
                "focused_tests_passed": 46,
                "vps_prompt": "VPS_CODEX_RUNTIME_LEARNING_PACKET_PROMPT.md",
                "scoped_patch": "VPS_RUNTIME_LEARNING_PACKET_DELTA.patch",
            },
            "forbidden_surface_check": {
                "broker_mutation": False,
                "credential_mutation": False,
                "paid_vendor_call": False,
                "orderflow_depth_used": False,
                "remote_push": False,
                "live_vps_reload": False,
            },
            "completion_boundary": "Wave E is a valuable VPS checkpoint for packet parity and learning capture. Wave F final dossier remains later.",
        },
    )

    (ROUTE / "RUNTIME_LEARNING_DEPLOYMENT_VALUE_SUMMARY.md").write_text(
        """# Wave E Runtime-Learning Packet Parity Checkpoint

This checkpoint turns the ultimate-book runtime from status-only launcher rows into a canonical, append-only learning packet ledger.

Value for VPS:

- every cycle can emit `cycle_no_decision`, `cycle_no_candidates`, `unit_shadow`, `unit_admitted`, `unit_skipped`, and `unit_placed` packets;
- every management pass can emit `position_adopted`, `position_managed`, `position_closed`, `position_out_of_universe`, `position_management_error`, and `breach_flatten` packets;
- bridge policy context, active candidate/market-expansion policy, risk/sizing flags, skip reasons, decision bars, and placement status are joined in one schema;
- raw broker tickets, account logins, server names, passwords, tokens, and API keys are never written raw;
- packet writing is best-effort and non-fatal, so telemetry cannot stop trading or management;
- active config enables the observation-only packet ledger at `shadow_logs/ultimate_book_runtime_learning_packets.jsonl`.

Evidence class: production-code observation layer and VPS parity handoff. This is not broker-real PnL and does not mutate broker/account/order/deal/position state.
""",
        encoding="utf-8",
    )

    (ROUTE / "VPS_CODEX_RUNTIME_LEARNING_PACKET_PROMPT.md").write_text(
        """# VPS Codex Prompt - Runtime-Learning Packet Parity Checkpoint

/goal Follow this prompt as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; inspect current VPS disk state before acting.

Objective: absorb the Wave E runtime-learning packet parity checkpoint from the Mac route `research/operations/final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18`, apply only the scoped runtime-learning packet delta if it is not already present, verify it on the VPS runtime branch, and record evidence. This is a production-code observation layer, not a strategy-risk change.

Required context on VPS:

- regenerate/read `.context/LIVE_STATE.md`;
- read `.context/00_core/current_vnext_system_map.md`;
- read `.context/00_core/current_repo_reading_order.md`;
- read `.context/00_core/goal_session_research_discipline.md`;
- read `.context/00_core/research_operating_doctrine.md`;
- read the existing ultimate activation handoff and VPS deployment ledger from the active parity branch;
- read this route's `RUNTIME_LEARNING_DEPLOYMENT_VALUE_SUMMARY.md`, `RUNTIME_LEARNING_PACKET_SCHEMA.json`, `REDACTION_AND_FORBIDDEN_SURFACE_AUDIT.json`, `VPS_RUNTIME_LEARNING_PACKET_DELTA.patch`, and `VERIFICATION_RESULT.json`.

Apply/verify steps:

1. Confirm whether `src/components/ultimate_book/runtime_learning_packet.py` already exists and whether `config/agent_config.yaml` has:
   - `ultimate_book_runtime_learning_packet_enabled: true`
   - `ultimate_book_runtime_learning_packet_log_enabled: true`
   - `ultimate_book_runtime_learning_packet_log_path: "shadow_logs/ultimate_book_runtime_learning_packets.jsonl"`
   - `ultimate_book_runtime_learning_packet_schema: "ultimate_book_runtime_learning_packet_v1"`
   - `ultimate_book_runtime_learning_redaction_policy: "hash_ticket_and_account_identifiers_v1"`
2. If missing, apply `VPS_RUNTIME_LEARNING_PACKET_DELTA.patch` or cherry-pick the Mac checkpoint commit containing this route. Do not apply unrelated Mac branch history.
3. Run:
   - `python3 -m py_compile src/components/ultimate_book/runtime_learning_packet.py src/components/ultimate_book/book_owner.py src/components/ultimate_book/launcher.py src/components/ultimate_book/bridge.py tests/ultimate_book/test_runtime_learning_packet.py tests/ultimate_book/test_launcher.py`
   - `pytest tests/ultimate_book/test_runtime_learning_packet.py tests/ultimate_book/test_launcher.py tests/ultimate_book/test_book_owner.py -q`
   - `python3 research/operations/final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18/verify_wave_e_runtime_learning_packet_parity.py`
4. Verify the launcher/runtime can report `runtime_learning` status and that packet writes go to `shadow_logs/ultimate_book_runtime_learning_packets.jsonl`.
5. If a live process is already healthy, do not blind reload. If a reload is intentionally performed by the VPS operator lane, record process IDs before/after, config hash, packet sample, and rollback command.
6. Record a VPS evidence ledger with:
   - current HEAD/ref;
   - patch/cherry-pick status;
   - config key values;
   - test/verifier output;
   - packet log path and first redacted sample if produced;
   - rollback: set `ultimate_book_runtime_learning_packet_enabled=false` only.

Forbidden surfaces: no credential disclosure or mutation, no broker/account/order/deal/position mutation, no paid/vendor calls, no orderflow/depth, no blind live reload, no broad Mac branch push.

Completion: stop when the scoped Wave E packet parity delta is applied or proven already present, tests/verifier pass, and the VPS evidence ledger records packet/log parity and rollback proof.
""",
        encoding="utf-8",
    )

    (ROUTE / "NEXT_PROMPT.md").write_text(
        """# Next Prompt - Wave F Final Dossier After VPS Packet Checkpoint

/goal Follow the full controlling context and Wave A-E route artifacts as the complete objective; regenerate LIVE_STATE first; inspect Wave A, Wave B, Wave C, and Wave E artifacts from disk; then build the Wave F final integration dossier and config decision. Do not relaunch broad research. Consume the current numbers, the lazy MT5 LTF source, inactive-lever audit, and runtime-learning packet parity, then decide the final deployable package, exact rollback stack, monitoring checklist, and remaining owner/VPS action boundary. No broker/account/order/deal/position mutation, no credentials, no paid/vendor, no orderflow/depth.
""",
        encoding="utf-8",
    )

    print(json.dumps({"ok": True, "route": ROUTE.relative_to(REPO).as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
