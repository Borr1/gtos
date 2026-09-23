"""Build G0 synthesis artifacts for the SCID additive forward-capture audit.

This route is G0 source/control synthesis only. It reconciles the accepted G12
audit of the additive runtime implementation, records the nonblocking activation
follow-up, and emits broad next-route prompt packs without opening validation,
result scoring, broker evidence, AI/API calls, paid/vendor access, raw market
blobs, live restarts, or trading-decision behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"

G12_AUDIT_DIR = OUTCOME_DIR / "g12_scid_forward_capture_additive_implementation_audit"
IMPLEMENTATION_DIR = OUTCOME_DIR / "scid_forward_capture_additive_implementation_from_parallel_g12_wave"

DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_FC_ADDITIVE_SYNTHESIS"
ROUTE_ID = "G0_SCID_FORWARD_CAPTURE_ADDITIVE_SYNTHESIS_CONTROL"
EVIDENCE_CLASS = "G0_SCID_FORWARD_CAPTURE_ADDITIVE_SYNTHESIS_CONTROL_ONLY"
TERMINAL_DECISION = (
    "ACCEPT_AS_G0_SCID_FORWARD_CAPTURE_ADDITIVE_SYNTHESIS_WITH_RANKED_NONBLOCKING_ROUTE_BUNDLE"
)
ACCEPTED_G12_DECISION = "ACCEPT_WITH_EXACT_NONBLOCKING_ACTIVATION_FOLLOWUPS"

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

FORBIDDEN_SURFACES = (
    "validation/result scoring/strategy edge/R/PnL/win-rate/expectancy/performance/"
    "promotion/AI/API/paid-vendor/credential/remote/broker-account-order-history-deal-position/"
    "raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision/canary-selector changes"
)

PROMPTS: dict[str, dict[str, Any]] = {
    "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN": {
        "rank": 1,
        "prompt_file": (
            "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_"
            "FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
        ),
        "starter_file": (
            "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_"
            "FROM_ADDITIVE_G0_SYNTHESIS_STARTER_2026-05-12.txt"
        ),
        "run_state": "RUN_NOW_NO_API_NO_OUTCOME_SCORING",
        "parallel_ready": True,
        "dependency_state": "not blocked by no-restart/no-live-row landing",
        "objective": (
            "Map the accepted 40 hypothesis cards across 8 science domains to additive SCID capture groups, "
            "freeze source fields, eligibility, denominator keys, duplicate policy, as-of rules, input-packet "
            "requirements, and no-API replay-input design without opening results."
        ),
        "required_outputs": [
            "40-card/8-domain source-field mapping matrix",
            "replay/input packet design ledger with eligibility and denominator contracts",
            "sealed historical partition or forward-capture dependency ledger",
            "negative-evidence and anti-boxing ledger covering non-OB/current-field alternatives",
            "completion audit with NO_PROMOTION_VERDICT and result scoring closed",
        ],
    },
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_VALIDITY_EXPANSION": {
        "rank": 2,
        "prompt_file": (
            "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_VALIDITY_EXPANSION_"
            "FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
        ),
        "starter_file": (
            "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_VALIDITY_EXPANSION_"
            "FROM_ADDITIVE_G0_SYNTHESIS_STARTER_2026-05-12.txt"
        ),
        "run_state": "RUN_NOW_SOURCE_STATUS_AND_VALIDITY_ONLY",
        "parallel_ready": True,
        "dependency_state": "can run against existing local/source-status artifacts before live rows land",
        "objective": (
            "Expand LTF/orderflow/proxy source-status validity around the accepted fail-closed SCID fields: "
            "search local-heavy roots and accepted source contracts, classify recoverable versus non-generatable "
            "fields, define as-of/hash/parser requirements, and identify proxy validity checks without paid pulls."
        ),
        "required_outputs": [
            "LTF source-status and as-of validity matrix",
            "orderflow/depth/proxy source-status and proxy-validity matrix",
            "recoverable-source versus non-generatable-source ledger",
            "future capture/parser/test contract list",
            "completion audit with no paid/vendor/API/raw-blob use",
        ],
    },
    "SCID_FORWARD_CAPTURE_MONITORING_HEALTH_GUARD": {
        "rank": 3,
        "prompt_file": (
            "SCID_FORWARD_CAPTURE_MONITORING_HEALTH_GUARD_FROM_ADDITIVE_G0_SYNTHESIS_"
            "GOAL_PROMPT_2026-05-12.md"
        ),
        "starter_file": (
            "SCID_FORWARD_CAPTURE_MONITORING_HEALTH_GUARD_FROM_ADDITIVE_G0_SYNTHESIS_"
            "STARTER_2026-05-12.txt"
        ),
        "run_state": "RUN_NOW_SOURCE_CONTROL_HEALTH_GUARD_ONLY",
        "parallel_ready": True,
        "dependency_state": "can build health checks now; strict non-empty live verification waits for expected rows",
        "objective": (
            "Build or specify a forward source-capture health guard for SCID rows: append-only schema checks, "
            "safe-flag checks, row freshness, missing-group status, fail-closed source-status summaries, and "
            "honest empty-path behavior without scoring any outcome."
        ),
        "required_outputs": [
            "monitoring/health guard design or implementation ticket",
            "schema/safe-flag/freshness check matrix",
            "empty-live-path honesty rule",
            "operator timing note for verifier without --allow-empty only when rows are expected",
            "completion audit with live_effect=false",
        ],
    },
    "SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION": {
        "rank": 4,
        "prompt_file": (
            "SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION_FROM_ADDITIVE_G0_SYNTHESIS_"
            "GOAL_PROMPT_2026-05-12.md"
        ),
        "starter_file": (
            "SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION_FROM_ADDITIVE_G0_SYNTHESIS_"
            "STARTER_2026-05-12.txt"
        ),
        "run_state": "OPERATIONAL_TIMING_REQUIRED_NOT_A_REPAIR_BLOCKER",
        "parallel_ready": False,
        "dependency_state": "requires normal orchestrator reload or owner-approved controlled reload plus expected eligible row",
        "objective": (
            "Verify additive SCID activation honesty after normal or owner-approved orchestrator reload: row landing, "
            "group counts, safe flags, append-only behavior, and default verifier without --allow-empty only when "
            "live candidate/lifecycle rows are expected."
        ),
        "required_outputs": [
            "activation readiness ledger distinguishing reload timing from repair",
            "post-reload row-landing verifier result when rows are expected",
            "missing-group interpretation if no eligible row arrives",
            "no trading/risk/safety/prompt-decision behavior changed statement",
            "completion audit preserving live_effect=false for the research route",
        ],
    },
    "SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION": {
        "rank": 5,
        "prompt_file": (
            "SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION_FROM_ADDITIVE_G0_SYNTHESIS_"
            "GOAL_PROMPT_2026-05-12.md"
        ),
        "starter_file": (
            "SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION_FROM_ADDITIVE_G0_SYNTHESIS_"
            "STARTER_2026-05-12.txt"
        ),
        "run_state": "DO_NOT_RUN_UNTIL_DEPENDENCY_VALID",
        "parallel_ready": False,
        "dependency_state": (
            "blocked until source/input activation evidence, preregistered hypothesis/input packet, duplicate policy, "
            "as-of proof, and G12/G0 gate approval exist"
        ),
        "objective": (
            "Prepare the later gate definition for a sealed result packet only after source/input prerequisites are "
            "valid. This prompt is dormant until dependencies prove the packet can be opened without leakage."
        ),
        "required_outputs": [
            "dependency-validity checklist before any result packet can open",
            "sealed packet schema and denominator gate plan",
            "explicit G12/G0 gate before scoring",
            "blocked-state ledger if any prerequisite is missing",
            "completion audit stating no result review opened in this preparatory lane",
        ],
    },
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_text(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "schema_version": "g0_scid_forward_capture_additive_synthesis_v1",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }


def write_json(stem: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def write_md(stem: str, title: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.md"
    path.write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                f"- **route_id:** `{ROUTE_ID}`",
                f"- **evidence_class:** `{EVIDENCE_CLASS}`",
                "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
                "- **validation_safe:** `false`",
                "- **outcome_review_opened:** `false`",
                "- **live_effect:** `false`",
                "",
                "```json",
                json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> list[Path]:
    return [write_json(stem, payload), write_md(stem, title, payload)]


def input_paths() -> dict[str, Path]:
    return {
        "controlling_prompt": G12_AUDIT_DIR / "NEXT_G0_SCID_FORWARD_CAPTURE_ADDITIVE_SYNTHESIS_PROMPT_2026-05-12.md",
        "g12_completion_audit": G12_AUDIT_DIR / "G12_SCID_FORWARD_CAPTURE_COMPLETION_AUDIT_2026-05-12.json",
        "g12_decision_ledger": G12_AUDIT_DIR / "G12_SCID_FORWARD_CAPTURE_ADDITIVE_IMPLEMENTATION_DECISION_LEDGER_2026-05-12.json",
        "g12_test_verifier_result": G12_AUDIT_DIR / "G12_SCID_FORWARD_CAPTURE_TEST_VERIFIER_REPRODUCTION_RESULT_2026-05-12.json",
        "g12_finding_ledger": G12_AUDIT_DIR / "G12_SCID_FORWARD_CAPTURE_FINDING_LEDGER_2026-05-12.json",
        "g12_downstream_compatibility": G12_AUDIT_DIR / "G12_SCID_FORWARD_CAPTURE_DOWNSTREAM_COMPATIBILITY_AUDIT_2026-05-12.json",
        "g12_live_restart_honesty": G12_AUDIT_DIR / "G12_SCID_FORWARD_CAPTURE_LIVE_ROW_RESTART_HONESTY_AUDIT_2026-05-12.json",
        "impl_hypothesis_compatibility": IMPLEMENTATION_DIR / "SCID_FC_ADDITIVE_IMPL_HYPOTHESIS_FACTORY_COMPATIBILITY_2026-05-12.json",
        "impl_ltf_orderflow_compatibility": IMPLEMENTATION_DIR / "SCID_FC_ADDITIVE_IMPL_LTF_ORDERFLOW_PROXY_COMPATIBILITY_2026-05-12.json",
        "impl_restart_ledger": IMPLEMENTATION_DIR / "SCID_FC_ADDITIVE_IMPL_RESTART_LEDGER_2026-05-12.json",
        "impl_default_verifier": IMPLEMENTATION_DIR / "SCID_FC_ADDITIVE_IMPL_VERIFIER_RESULT_DEFAULT_2026-05-12.json",
    }


def build_input_inventory(paths: dict[str, Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, path in sorted(paths.items()):
        rows.append(
            {
                "input_name": name,
                "path": repo_path(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "raw_market_blob": path.suffix.lower() in {".scid", ".depth", ".parquet", ".csv", ".dly", ".bin"},
            }
        )
    return rows


def route_scores(route_id: str) -> dict[str, int]:
    scores = {
        "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN": {
            "evidence_gain": 5,
            "dependency_readiness": 5,
            "edge_discovery_unlock": 5,
            "nonblocking_parallelism": 5,
            "source_noleak_cleanliness": 5,
            "activation_dependency": 0,
        },
        "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_VALIDITY_EXPANSION": {
            "evidence_gain": 5,
            "dependency_readiness": 4,
            "edge_discovery_unlock": 5,
            "nonblocking_parallelism": 5,
            "source_noleak_cleanliness": 4,
            "activation_dependency": 0,
        },
        "SCID_FORWARD_CAPTURE_MONITORING_HEALTH_GUARD": {
            "evidence_gain": 4,
            "dependency_readiness": 5,
            "edge_discovery_unlock": 3,
            "nonblocking_parallelism": 4,
            "source_noleak_cleanliness": 5,
            "activation_dependency": 1,
        },
        "SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION": {
            "evidence_gain": 4,
            "dependency_readiness": 2,
            "edge_discovery_unlock": 3,
            "nonblocking_parallelism": 2,
            "source_noleak_cleanliness": 5,
            "activation_dependency": 4,
        },
        "SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION": {
            "evidence_gain": 5,
            "dependency_readiness": 1,
            "edge_discovery_unlock": 5,
            "nonblocking_parallelism": 1,
            "source_noleak_cleanliness": 5,
            "activation_dependency": 5,
        },
    }
    return scores[route_id]


def prompt_text(route_id: str, route: dict[str, Any]) -> str:
    prompt_path = (
        f"research/science_program_2026_05/04_goal_prompts/{route['prompt_file']}"
    )
    requirements = "\n".join(f"- {item}" for item in route["required_outputs"])
    return f"""# {route_id} Goal Prompt

Evidence class: `{route_id}_ONLY`
Input G0 synthesis: `research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_additive_synthesis_control/`

Objective: {route['objective']}

Mandatory preflight:
1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/goal_session_research_discipline.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read the additive G0 synthesis decision ledger, accepted G12 synthesis, route ranking matrix, follow-up/blocker ledger, sequencing ledger, saturation/self-red-team ledger, not-in-a-loop ledger, and prompt-pack ledger.

Lane posture:
- Do not rely on chat memory or compacted summaries.
- Treat examples as starting points, not boundaries.
- Current GTOS OB/retest logic is not the research horizon.
- Current SCID fields are a substrate, not the outer boundary; define additional source-safe fields or exact blockers where useful.
- Be broad, curious, active, and non-lazy while preserving hard evidence-class boundaries.
- Source-safe means auditable, redacted, as-of-bound, duplicate-controlled, fail-closed where unavailable, and no-leak. It does not mean narrow or OB-only.

Forbidden surfaces:
- No validation/result scoring/strategy-edge/R/PnL/win-rate/expectancy/performance claim.
- No promotion dossier or live-trading recommendation.
- No AI/API calls, paid/vendor access, credential/remote action, broker account/order/history/deal/position evidence, or raw market-data blob commit.
- No trading, risk, safety, production prompt-decision, canary, selector, execution, order-behavior, or live-restart change.
- Do not convert the additive no-restart/no-live-row landing into a repair blocker.

Required outputs:
{requirements}

Completion Standard:
- Produce scoped artifacts and, where useful, a verifier/focused test or machine-checkable checklist.
- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Distinguish true blockers from nonblocking activation/source follow-ups.
- Include a saturation/self-red-team pass showing whether the lane accidentally became activation-only, OB-only, current-field-only, or passive live-row waiting.

One-line starter for this prompt:
`/goal Follow the full controlling prompt in {prompt_path} as the complete objective; run mandatory preflight/context refresh; do not rely on chat memory; stay {route_id}_ONLY with no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-behavior/trading-risk-safety-prompt-decision changes; pursue proof-or-impossibility broadly inside this evidence class, not OB-only/current-field-only/passive-waiting; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; emit scoped artifacts, saturation/self-red-team, blocker/follow-up, and completion-audit ledgers; mark complete only when the prompt file's completion standard is fully satisfied.`
"""


def one_line_starter(route_id: str, route: dict[str, Any]) -> str:
    prompt_path = f"research/science_program_2026_05/04_goal_prompts/{route['prompt_file']}"
    return (
        f"/goal Follow the full controlling prompt in {prompt_path} as the complete objective; "
        "run mandatory preflight/context refresh; do not rely on chat memory; "
        f"stay {route_id}_ONLY with no validation/results/R/PnL/win-rate/expectancy/performance/"
        "promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/"
        "live-behavior/trading-risk-safety-prompt-decision changes; pursue proof-or-impossibility "
        "broadly inside this evidence class, not OB-only/current-field-only/passive-waiting; "
        "preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; "
        "emit scoped artifacts, saturation/self-red-team, blocker/follow-up, and completion-audit ledgers; "
        "mark complete only when the prompt file's completion standard is fully satisfied."
    )


def write_prompt_packs() -> dict[str, dict[str, Any]]:
    prompt_pack: dict[str, dict[str, Any]] = {}
    for route_id, route in PROMPTS.items():
        prompt_path = PROMPT_DIR / route["prompt_file"]
        starter_path = ROUTE_DIR / route["starter_file"]
        text = prompt_text(route_id, route)
        starter = one_line_starter(route_id, route)
        prompt_path.write_text(text, encoding="utf-8")
        starter_path.write_text(starter + "\n", encoding="utf-8")
        prompt_pack[route_id] = {
            **route,
            "prompt_path": repo_path(prompt_path),
            "starter_path": repo_path(starter_path),
            "one_line_starter": starter,
            "prompt_sha256": sha256_file(prompt_path),
            "starter_sha256": sha256_file(starter_path),
        }
    return prompt_pack


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_additive_synthesis_control/",
        "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_VALIDITY_EXPANSION_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_MONITORING_HEALTH_GUARD_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
    raw_blob_suffixes = (".scid", ".depth", ".parquet", ".csv", ".dly", ".bin", ".jsonl.gz")
    entries: list[dict[str, Any]] = []
    for line in proc.stdout.strip().splitlines():
        if len(line) < 4:
            continue
        path = line[2:].strip().replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in allowed_prefixes)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(forbidden_live_prefixes),
                "scoped_raw_market_blob": scoped and path.endswith(raw_blob_suffixes),
            }
        )
    scoped_entries = [entry for entry in entries if entry["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "scoped_entries": scoped_entries,
        "unrelated_dirty_entry_count": len([entry for entry in entries if not entry["scoped"]]),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    paths = input_paths()
    loaded = {name: load_json(path) for name, path in paths.items() if path.suffix == ".json"}
    prompt_pack = write_prompt_packs()

    context_anchor = {
        **base_payload("context_anchor"),
        "current_head": git_text(["rev-parse", "--short", "HEAD"]),
        "current_head_subject": git_text(["log", "-1", "--pretty=%s"]),
        "controlling_prompt": repo_path(paths["controlling_prompt"]),
        "mandatory_context_read": [
            ".context/LIVE_STATE.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_READING_ORDER.md",
        ],
        "input_inventory": build_input_inventory(paths),
        "lane_application": {
            "lane": "G0 synthesis/control",
            "posture": "constructive route-generation with audit boundary preservation",
            "anti_boxing": [
                "activation/readiness is tracked but not allowed to consume the program",
                "OB/current-GTOS/current-field framing is explicitly not the horizon",
                "no-API and LTF/orderflow/proxy routes remain alive before live rows land",
            ],
        },
    }
    created += write_pair("CONTEXT_ANCHOR", "G0 SCID FC Additive Context Anchor", context_anchor)

    decision = loaded["g12_decision_ledger"]
    completion = loaded["g12_completion_audit"]
    tests = loaded["g12_test_verifier_result"]
    findings = loaded["g12_finding_ledger"]
    downstream = loaded["g12_downstream_compatibility"]
    live_honesty = loaded["g12_live_restart_honesty"]
    impl_restart = loaded["impl_restart_ledger"]
    impl_verifier = loaded["impl_default_verifier"]

    accepted_g12 = {
        **base_payload("accepted_g12_synthesis"),
        "accepted_g12_terminal_decision": decision["terminal_decision"],
        "expected_terminal_decision": ACCEPTED_G12_DECISION,
        "decision_matches_expected": decision["terminal_decision"] == ACCEPTED_G12_DECISION,
        "g12_decision_scope": decision["decision_scope"],
        "accepted_as_source_control_implementation_evidence_only": True,
        "g12_summary": decision["summary"],
        "accepted_evidence": decision["accepted_evidence"],
        "completion_can_mark_goal_complete": completion["can_mark_goal_complete"],
        "blocking_findings": decision["blocking_findings"],
        "nonblocking_findings": findings["nonblocking_findings"],
        "rejected_false_blockers": findings["rejected_findings"],
        "test_reproduction": tests,
        "safe_flags_from_g12": decision["safe_flags"],
        "preserved_safe_flags": {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    created += write_pair("ACCEPTED_G12_SYNTHESIS", "Accepted G12 Synthesis", accepted_g12)

    route_rows: list[dict[str, Any]] = []
    for route_id, route in sorted(PROMPTS.items(), key=lambda item: item[1]["rank"]):
        scores = route_scores(route_id)
        route_rows.append(
            {
                "rank": route["rank"],
                "route_id": route_id,
                "run_state": route["run_state"],
                "parallel_ready": route["parallel_ready"],
                "dependency_state": route["dependency_state"],
                "objective": route["objective"],
                "scores_0_to_5": scores,
                "total_score": sum(scores.values()),
                "prompt_path": prompt_pack[route_id]["prompt_path"],
                "starter_path": prompt_pack[route_id]["starter_path"],
                "why_not_boxed": [
                    "not selected because it is easy to explain",
                    "route advances evidence gain inside its own evidence class",
                    "does not assume OB/current GTOS field completeness",
                ],
            }
        )
    ranking = {
        **base_payload("route_ranking_matrix"),
        "rank_1_route": route_rows[0]["route_id"],
        "rank_1_reason": (
            "The no-API 40-card/8-domain preregistration and replay-input design has the highest evidence gain "
            "with no dependency on live row landing or owner-approved restart timing."
        ),
        "required_route_families_present": True,
        "routes": route_rows,
        "sealed_result_packet_route_dependency_blocked": True,
        "activation_route_is_nonblocking_followup_not_repair": True,
    }
    created += write_pair("ROUTE_RANKING_MATRIX", "Route Ranking Matrix", ranking)

    followups = {
        **base_payload("followup_blocker_ledger"),
        "nonblocking_activation_followups": decision["nonblocking_activation_followups"],
        "true_repair_blockers": [],
        "no_restart_no_live_row_classification": live_honesty["classification"],
        "default_verifier_row_count": impl_verifier["row_count"],
        "default_verifier_allow_empty": impl_verifier["allow_empty"],
        "controlled_restart_performed": impl_restart["controlled_restart_performed"],
        "live_row_landing_claimed": impl_restart["live_row_landing_claimed"],
        "why_not_repair_blocker": [
            "G12 explicitly accepted code-complete, fail-open, tested implementation with honest no-restart/no-live-row landing.",
            "Strict non-empty verification belongs after owner-approved/normal reload and an expected eligible live row.",
            "The G0 lane can advance no-API and source-status routes before live rows land.",
        ],
    }
    created += write_pair("FOLLOWUP_BLOCKER_LEDGER", "Followup And Blocker Ledger", followups)

    sequencing = {
        **base_payload("sequencing_parallelization_ledger"),
        "run_now_no_owner_live_approval": [
            "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN",
            "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_VALIDITY_EXPANSION",
            "SCID_FORWARD_CAPTURE_MONITORING_HEALTH_GUARD",
        ],
        "parallel_ready_nonconflicting": [
            "no-api hypothesis preregistration/replay-input design",
            "LTF/orderflow/proxy source-status validity expansion",
            "source-capture monitoring/health guard",
        ],
        "operational_timing_required_nonblocking": [
            "SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION",
        ],
        "later_dependency_valid_only": [
            "SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION",
        ],
        "dependency_rules": [
            "activation readiness requires normal or owner-approved orchestrator reload and expected eligible rows",
            "sealed result-packet gate requires frozen preregistration/input packet, source/as-of/duplicate proof, and later G12/G0 approval",
            "no-API and source-status routes do not wait for live row landing",
        ],
    }
    created += write_pair("SEQUENCING_PARALLELIZATION_LEDGER", "Sequencing And Parallelization Ledger", sequencing)

    saturation = {
        **base_payload("saturation_self_redteam_ledger"),
        "not_activation_only": True,
        "not_ob_only": True,
        "not_current_field_only": True,
        "not_live_forward_only": True,
        "not_passive_waiting": True,
        "self_red_team_questions": [
            {
                "question": "Did G0 turn no-restart/no-live-row landing into a repair blocker?",
                "answer": "No. It is tracked as G12-SCID-ACT-001 nonblocking activation follow-up.",
            },
            {
                "question": "Did route selection collapse into waiting for live rows?",
                "answer": "No. Three run-now routes are emitted before activation row landing.",
            },
            {
                "question": "Did route selection stay OB-only or current-framework-only?",
                "answer": "No. Rank 1 preserves all 40 cards and 8 science domains; rank 2 preserves LTF/orderflow/proxy source-status expansion.",
            },
            {
                "question": "Did G0 open result scoring or validation?",
                "answer": "No. Sealed result-packet design is dependency-blocked until source/input/G12/G0 gates exist.",
            },
            {
                "question": "Did any prompt authorize paid/API/vendor or broker result access?",
                "answer": "No. Prompt packs explicitly forbid those surfaces.",
            },
            {
                "question": "Could activation health be useful without becoming a loop?",
                "answer": "Yes. Monitoring health guard is source/control only and supports future evidence hygiene, while discovery routes proceed in parallel.",
            },
        ],
        "same_evidence_class_gaps_pursued": [
            "prompt packs emitted for every required route family instead of only rank 1",
            "sequencing separates run-now, operational-timing, and later dependency-valid lanes",
            "nonblocking follow-up ledger names exact next activation check without waiting loop",
        ],
    }
    created += write_pair("SATURATION_SELF_REDTEAM_LEDGER", "Saturation And Self-Red-Team Ledger", saturation)

    not_loop = {
        **base_payload("not_in_a_loop_ledger"),
        "terminal_statement": (
            "This G0 route advances from accepted source capture toward preregistered no-API input design, source-validity "
            "expansion, and health monitoring; it does not rebuild source infrastructure for its own sake."
        ),
        "loop_risks_and_controls": [
            {
                "risk": "activation-only waiting",
                "control": "rank 1 and rank 2 run before live rows land",
            },
            {
                "risk": "source-control loop without hypothesis path",
                "control": "rank 1 maps the accepted 40-card/8-domain factory into replay/input preregistration",
            },
            {
                "risk": "result packet opened too early",
                "control": "sealed packet route is emitted as dormant and dependency-blocked",
            },
            {
                "risk": "current-field tunnel vision",
                "control": "prompts require anti-boxing and exact future source/schema requirements for fields not yet captured",
            },
        ],
    }
    created += write_pair("NOT_IN_A_LOOP_LEDGER", "Not In A Loop Ledger", not_loop)

    prompt_pack_payload = {
        **base_payload("prompt_pack_ledger"),
        "prompt_pack_count": len(prompt_pack),
        "rank_1_next_prompt": prompt_pack["SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN"][
            "prompt_path"
        ],
        "rank_1_next_starter": prompt_pack["SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN"][
            "starter_path"
        ],
        "parallel_ready_prompt_packs": [
            route_id for route_id, route in prompt_pack.items() if route["parallel_ready"]
        ],
        "dependency_blocked_prompt_packs": [
            route_id
            for route_id, route in prompt_pack.items()
            if route["run_state"] == "DO_NOT_RUN_UNTIL_DEPENDENCY_VALID"
        ],
        "selected_route_prompt_packs": prompt_pack,
        "starter_lines_present_for_all_selected_routes": all(row["one_line_starter"] for row in prompt_pack.values()),
    }
    created += write_pair("PROMPT_PACK_LEDGER", "Prompt Pack Ledger", prompt_pack_payload)

    decision_payload = {
        **base_payload("decision_ledger"),
        "terminal_decision": TERMINAL_DECISION,
        "accepted_g12_terminal_decision": ACCEPTED_G12_DECISION,
        "g12_accepted_source_control_implementation_evidence_only": True,
        "rank_1_route": ranking["rank_1_route"],
        "true_repair_blocker_count": 0,
        "nonblocking_activation_followup_count": len(decision["nonblocking_activation_followups"]),
        "no_promotion_or_validation_opened": True,
        "no_live_behavior_change": True,
        "can_mark_goal_complete_after_verification": True,
    }
    created += write_pair("DECISION_LEDGER", "Decision Ledger", decision_payload)

    completion_audit = {
        **base_payload("completion_audit"),
        "objective_restatement": [
            "Run mandatory preflight/context refresh from disk.",
            "Synthesize the accepted G12 SCID additive implementation audit into G0 control state.",
            "Preserve ACCEPT_WITH_EXACT_NONBLOCKING_ACTIVATION_FOLLOWUPS and source/control-only scope.",
            "Keep NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
            "Do not score validation/results/R/PnL/win-rate/expectancy/performance or change live behavior.",
            "Rank and emit prompt packs/starters for activation/readiness, no-API 40-card/8-domain prereg/replay-input design, LTF/orderflow/proxy validity, monitoring/health guard, and later sealed result-packet gate if dependency-valid.",
            "Emit follow-up/blocker, sequencing/parallelization, saturation/self-red-team, and not-in-a-loop ledgers.",
            "Commit only scoped G0 synthesis/context artifacts.",
        ],
        "prompt_to_artifact_checklist": [
            {
                "requirement": "mandatory preflight/context refresh",
                "evidence": "python scripts/generate_live_state.py ran; LIVE_STATE, latest handoff, quick reference, research doctrine/current state, reading order, local heavy data, AI cost-control plan, and controlling prompt were read from disk.",
                "status": "PASS",
            },
            {
                "requirement": "record exact G12 terminal decision",
                "evidence": "G0_SCID_FC_ADDITIVE_SYNTHESIS_ACCEPTED_G12_SYNTHESIS_2026-05-12.json",
                "status": "PASS",
            },
            {
                "requirement": "source/control-only acceptance and safe flags",
                "evidence": "Decision, accepted-G12, and completion ledgers preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.",
                "status": "PASS",
            },
            {
                "requirement": "no validation/results/R/PnL/win-rate/expectancy/performance scoring",
                "evidence": "All emitted prompt packs forbid result scoring; sealed result packet is dependency-blocked.",
                "status": "PASS",
            },
            {
                "requirement": "no trading/risk/safety/prompt-decision/live behavior changes",
                "evidence": "Scoped route writes only G0 synthesis artifacts, prompt packs, and context refresh artifacts.",
                "status": "PASS",
            },
            {
                "requirement": "distinguish nonblocking activation follow-up from repair blockers",
                "evidence": "G0_SCID_FC_ADDITIVE_SYNTHESIS_FOLLOWUP_BLOCKER_LEDGER_2026-05-12.json",
                "status": "PASS",
            },
            {
                "requirement": "route-ranking matrix covers required routes",
                "evidence": "G0_SCID_FC_ADDITIVE_SYNTHESIS_ROUTE_RANKING_MATRIX_2026-05-12.json",
                "status": "PASS",
            },
            {
                "requirement": "rank-1 prompt and starter plus parallel-ready prompt packs",
                "evidence": "G0_SCID_FC_ADDITIVE_SYNTHESIS_PROMPT_PACK_LEDGER_2026-05-12.json",
                "status": "PASS",
            },
            {
                "requirement": "saturation/self-red-team, sequencing/parallelization, not-in-a-loop ledgers",
                "evidence": "SATURATION_SELF_REDTEAM, SEQUENCING_PARALLELIZATION, and NOT_IN_A_LOOP ledgers.",
                "status": "PASS",
            },
            {
                "requirement": "standalone verifier and focused tests",
                "evidence": "Verifier and pytest are provided in the route directory.",
                "status": "PENDING_VERIFIER_AND_FOCUSED_PYTEST",
            },
        ],
        "completion_standard_satisfied": False,
        "can_mark_goal_complete": False,
        "focused_tests_ok": False,
        "standalone_verifier_ok": False,
    }
    created += write_pair("COMPLETION_AUDIT", "Completion Audit", completion_audit)

    closeout = {
        **base_payload("closeout_verification"),
        "status": "BUILT_PENDING_STANDALONE_VERIFIER_AND_FOCUSED_PYTEST",
        "standalone_verifier": {"status": "PENDING"},
        "focused_pytest": {"status": "PENDING"},
        "scoped_git_status": scoped_git_status(),
    }
    created += write_pair("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout)

    manifest_entries = []
    for path in sorted(set(created)):
        manifest_entries.append(
            {
                "path": repo_path(path),
                "sha256": sha256_file(path),
                "artifact_type": path.suffix.lstrip("."),
            }
        )
    for route in prompt_pack.values():
        for key in ("prompt_path", "starter_path"):
            path = ROOT / route[key]
            manifest_entries.append(
                {
                    "path": repo_path(path),
                    "sha256": sha256_file(path),
                    "artifact_type": path.suffix.lstrip("."),
                }
            )

    manifest = {
        **base_payload("output_manifest"),
        "terminal_decision": TERMINAL_DECISION,
        "artifact_count_excluding_manifest": len(manifest_entries),
        "artifacts": manifest_entries,
        "scoped_git_status": scoped_git_status(),
    }
    created += write_pair("OUTPUT_MANIFEST", "Output Manifest", manifest)

    result = {
        "ok": True,
        "route_id": ROUTE_ID,
        "terminal_decision": TERMINAL_DECISION,
        "created_artifacts": [repo_path(path) for path in sorted(set(created))],
        "prompt_packs": prompt_pack,
    }
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return result


if __name__ == "__main__":
    build()
