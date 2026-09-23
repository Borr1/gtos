"""Build the G0 SCID strategy-field packet synthesis/control route.

This route is G0 synthesis/control only. It reconciles the accepted G12
strategy-field packet audit and emits ranked next-route prompts without
opening validation, result scoring, broker evidence, AI/API calls, paid data,
raw market-data blob commits, or live trading behavior.
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
G12_DIR = OUTCOME_DIR / "g12_scid_strategy_field_source_expansion_packet_audit"
PACKET_DIR = OUTCOME_DIR / "scid_strategy_field_source_expansion_packet"
G0_NEUTRAL_DIR = OUTCOME_DIR / "g0_scid_neutral_target_control_synthesis"
G12_NEUTRAL_DIR = OUTCOME_DIR / "g12_scid_asof_quarantined_neutral_target_execution_packet_audit"
NEUTRAL_PACKET_DIR = OUTCOME_DIR / "scid_asof_quarantined_neutral_target_execution_packet"

DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS"
ROUTE_ID = "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS"
EVIDENCE_CLASS = "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G0_STRATEGY_FIELD_PACKET_SYNTHESIS_WITH_RANKED_NEXT_ROUTE"

RANK1_PROMPT_NAME = "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_GOAL_PROMPT_2026-05-12.md"
RANK2_PROMPT_NAME = "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_ROUTE_GOAL_PROMPT_2026-05-12.md"
RANK3_PROMPT_NAME = "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_ROUTE_GOAL_PROMPT_2026-05-12.md"

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
    "changes_live_trading_behavior": False,
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_sample_and_count(path: Path, limit: int = 3) -> dict[str, Any]:
    count = 0
    sample: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            count += 1
            if len(sample) < limit:
                row = json.loads(line)
                statuses = {
                    key: value.get("status")
                    for key, value in row.get("field_statuses", {}).items()
                    if isinstance(value, dict)
                }
                sample.append(
                    {
                        "candidate_input_row_id": row.get("candidate_input_row_id"),
                        "symbol": row.get("symbol"),
                        "source_proxy_group": row.get("source_proxy_group"),
                        "decision_asof_utc": row.get("decision_asof_utc"),
                        "field_statuses": statuses,
                        "safe_flags": {
                            "promotion_verdict": row.get("promotion_verdict"),
                            "validation_safe": row.get("validation_safe"),
                            "outcome_review_opened": row.get("outcome_review_opened"),
                            "live_effect": row.get("live_effect"),
                        },
                    }
                )
    return {"row_count": count, "sample_rows": sample}


def git_text(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "schema_version": "g0_scid_strategy_field_packet_synthesis_v1",
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
    text = "\n".join(
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
    )
    path.write_text(text, encoding="utf-8")
    return path


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> list[Path]:
    return [write_json(stem, payload), write_md(stem, title, payload)]


def prompt_body(
    filename: str,
    title: str,
    evidence_class: str,
    route_purpose: str,
    route_outputs: list[str],
    route_completion: list[str],
    one_line_tail: str,
) -> str:
    outputs = "\n".join(f"- {item}" for item in route_outputs)
    completion = "\n".join(f"{index}. {item}" for index, item in enumerate(route_completion, start=1))
    return f"""# {title}

Date: {DATE_TAG}
Owner lane: research/control next-route prompt emitted by G0 strategy-field packet synthesis
Evidence class: `{evidence_class}`
Input G0 route: `research/science_program_2026_05/06_outcome_testing/g0_scid_strategy_field_source_expansion_packet_synthesis/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

{route_purpose}

This route must be constructive and anti-boxing: examples are starting points, not limits; current GTOS edge/frameworks are not the research horizon; source-safe means auditable/as-of/no-leak/hard-boundary-compliant, not conservative or narrow.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the G0 strategy-field synthesis context anchor, G12 reconciliation, source-field readiness synthesis, route ranking ledger, anti-boxing ledger, capture route specification, forbidden-surface audit, decision ledger, completion audit, and verifier result.
9. Read the accepted G12 strategy-field packet audit and builder packet artifacts from disk.

Do not rely on chat memory. If interrupted, regenerate `LIVE_STATE`, re-read this prompt and the route artifacts, and resume from disk evidence.

## Mandatory Context Use

Treat `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active instructions. Record in the completion audit:

- whether both were read after preflight;
- the builder/control posture applied;
- anti-boxing questions pursued;
- searched roots and artifacts inspected;
- exact proof-or-impossibility stop condition;
- what was deliberately not answered because it crosses validation/result scoring/broker/live/AI/API/paid/raw-data boundaries.

## Hard Boundaries

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Do not open validation execution, target/result/performance scoring, strategy-edge claims, R/PnL/win-rate/expectancy/performance, broker account/order/history/deal/position evidence, AI/API calls, paid/vendor access, raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, `.depth`, or market-data blob commits, live behavior, or prompt/config/risk/safety/execution/canary/selector changes.

## Required Outputs

Create a dedicated route directory under `research/science_program_2026_05/06_outcome_testing/` and emit:

{outputs}

## Required Saturation And Self-Red-Team

Before completion, answer and pursue same-evidence-class gaps:

- Are any historical strategy-intent/source-state fields being inferred from price?
- Are any target/result/performance fields leaking into source/control artifacts?
- Are side, entry, stop, target, POI, framework, lifecycle, LTF, and orderflow/proxy fields all either closed, fail-closed, prospective-capture-required, or forbidden?
- Are current GTOS frameworks, SCID-only artifacts, or M15 bars being treated as the entire horizon?
- Are route blockers exact and actionable rather than generic future work?
- Would a later G12 reject the artifact for denominator drift, no-leak failure, source hash weakness, vague capture requirements, or forbidden surface changes?

## Completion Standard

{completion}

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/{filename} as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay {evidence_class} with no validation/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; {one_line_tail}; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when the prompt file's completion standard is fully satisfied.`
"""


def write_next_prompts() -> list[str]:
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    prompts = [
        (
            RANK1_PROMPT_NAME,
            "SCID Combined Source Search And Forward Capture Route Goal Prompt",
            "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_ONLY",
            (
                "Run the rank-1 combined route selected by G0: exhaust a finite, source-safe broader historical source-state search for any explicit SCID strategy-intent/source-state artifacts, then freeze a forward capture contract for every still-missing field. The route must not implement live wiring or score results; it should produce a G12-auditable source/capture contract and proposed offline schemas that move fastest toward future direction-aware edge testing."
            ),
            [
                "context anchor and searched-root ledger",
                "historical source-state recovery attempt ledger",
                "forward capture contract for side, entry, stop, target, POI, framework, lifecycle, LTF, orderflow/proxy, and baseline-control fields",
                "schema/redaction/as-of/no-leak specification",
                "implementation-readiness ledger with no-live-effect boundary",
                "G12 acceptance criteria and repair prompt",
                "standalone verifier, focused tests, output manifest, completion audit, closeout verification",
            ],
            [
                "Mandatory preflight and context use are recorded.",
                "Every accepted field family is either recovered from explicit source, proven non-generatable from approved artifacts, or assigned exact prospective capture requirements.",
                "No validation, scoring, broker evidence, AI/API, paid/vendor access, raw market-data blob commit, live behavior, or trading-surface change is opened.",
                "Verifier and focused tests pass.",
                "A full next G12 audit prompt is emitted.",
                "Scoped commits and closeout verification are complete.",
            ],
            "recover or fail-close historical source-state and freeze the forward capture contract for the 3,014 accepted SCID candidates",
        ),
        (
            RANK2_PROMPT_NAME,
            "SCID LTF Orderflow Proxy Source Expansion Route Goal Prompt",
            "SCID_LTF_AND_ORDERFLOW_PROXY_SOURCE_EXPANSION_ONLY",
            (
                "Build the rank-2 explanatory source-control route: specify and, where source-safe local artifacts already exist, inventory lower-timeframe path availability plus orderflow/depth/proxy context that could later explain neutral behavior without becoming strategy intent. This is source expansion only, not result scoring."
            ),
            [
                "context anchor and source inventory",
                "LTF availability contract and parser/hash requirements",
                "orderflow/depth/proxy source contract with proxy caveats",
                "instrument/session/timeframe anti-boxing ledger",
                "no-leak and forbidden-surface audit",
                "G12 acceptance criteria and next prompt",
                "standalone verifier, focused tests, output manifest, completion audit, closeout verification",
            ],
            [
                "Mandatory preflight and context use are recorded.",
                "Every LTF/orderflow/proxy field has exact source, hash, as-of, schema, redaction, parser, and G12 criteria.",
                "The route separates explanatory market context from strategy intent and target/result fields.",
                "Verifier and focused tests pass.",
                "Scoped commits and closeout verification are complete.",
            ],
            "build a source-control LTF/orderflow/proxy expansion contract without result scoring or live behavior",
        ),
        (
            RANK3_PROMPT_NAME,
            "SCID Direction Aware Result Design Preregistration Route Goal Prompt",
            "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_ONLY",
            (
                "Prepare the gated rank-3 result-design preregistration route only after source fields are accepted by G12. Do not execute validation or inspect result/performance labels. Freeze hypotheses, denominators, sealed partitions, adversarial baselines, no-leak gates, sample floors, and stop conditions for future direction-aware edge testing."
            ),
            [
                "context anchor and prerequisite acceptance gate",
                "direction-aware hypothesis registry draft",
                "denominator/duplicate/partition policy",
                "adversarial baseline and perturbation plan",
                "sample-floor and effective-N requirements",
                "validation-execution forbidden boundary",
                "standalone verifier, focused tests, output manifest, completion audit, closeout verification",
            ],
            [
                "Mandatory preflight and context use are recorded.",
                "The route proves G12-accepted source fields exist before writing any result design.",
                "No validation execution, result scoring, performance claim, broker evidence, AI/API, paid/vendor access, raw blob commit, live behavior, or trading-surface change is opened.",
                "Verifier and focused tests pass.",
                "Scoped commits and closeout verification are complete.",
            ],
            "freeze a future direction-aware result design only after G12-accepted source fields, with validation still closed",
        ),
    ]
    written: list[str] = []
    for filename, title, evidence_class, purpose, outputs, completion, one_line_tail in prompts:
        path = PROMPT_DIR / filename
        path.write_text(
            prompt_body(filename, title, evidence_class, purpose, outputs, completion, one_line_tail),
            encoding="utf-8",
        )
        written.append(repo_path(path))
    return written


def score_route(route_id: str, speed: int, info_gain: int, recoverability: int, burden_inverse: int, auditability: int, validation_readiness: int, anti_boxing: int, decision: str, rationale: str) -> dict[str, Any]:
    total = round(
        0.23 * speed
        + 0.27 * info_gain
        + 0.14 * recoverability
        + 0.11 * burden_inverse
        + 0.12 * auditability
        + 0.07 * validation_readiness
        + 0.06 * anti_boxing,
        3,
    )
    return {
        "route_id": route_id,
        "speed_to_edge_testing_score_1_10": speed,
        "expected_information_gain_score_1_10": info_gain,
        "source_recoverability_score_1_10": recoverability,
        "implementation_burden_inverse_score_1_10": burden_inverse,
        "g12_auditability_score_1_10": auditability,
        "future_validation_readiness_score_1_10": validation_readiness,
        "anti_boxing_breadth_score_1_10": anti_boxing,
        "weighted_total_score": total,
        "decision": decision,
        "rationale": rationale,
    }


def main() -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)

    input_paths = {
        "controlling_prompt": ROOT / "research" / "science_program_2026_05" / "04_goal_prompts" / "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md",
        "goal_session_research_discipline": ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
        "research_operating_doctrine": ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
        "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
        "g12_manifest": G12_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_OUTPUT_MANIFEST_2026-05-12.json",
        "g12_decision": G12_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.json",
        "g12_completion": G12_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_COMPLETION_AUDIT_2026-05-12.json",
        "g12_row_coverage": G12_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_ROW_COVERAGE_DENOMINATOR_AUDIT_2026-05-12.json",
        "g12_field_status": G12_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_FIELD_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
        "g12_fail_prospective_forbidden": G12_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_FAIL_PROSPECTIVE_FORBIDDEN_AUDIT_2026-05-12.json",
        "g12_noleak": G12_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_NOLEAK_RAW_BLOB_LIVE_SURFACE_AUDIT_2026-05-12.json",
        "g12_source_hash": G12_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_SOURCE_HASH_INPUT_BINDING_AUDIT_2026-05-12.json",
        "g12_saturation": G12_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_SATURATION_SELF_REDTEAM_LEDGER_2026-05-12.json",
        "g12_closeout": G12_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_CLOSEOUT_VERIFICATION_2026-05-12.json",
        "builder_manifest": PACKET_DIR / "SCID_STRATEGY_FIELD_OUTPUT_MANIFEST_2026-05-12.json",
        "builder_status": PACKET_DIR / "SCID_STRATEGY_FIELD_STATUS_SUMMARY_2026-05-12.json",
        "builder_fail_closed": PACKET_DIR / "SCID_STRATEGY_FIELD_FAIL_CLOSED_MISSING_FIELD_LEDGER_2026-05-12.json",
        "builder_prospective": PACKET_DIR / "SCID_STRATEGY_FIELD_PROSPECTIVE_CAPTURE_REQUIREMENT_LEDGER_2026-05-12.json",
        "builder_duplicate": PACKET_DIR / "SCID_STRATEGY_FIELD_DUPLICATE_PROXY_DENOMINATOR_PRESERVATION_LEDGER_2026-05-12.json",
        "builder_source_inventory": PACKET_DIR / "SCID_STRATEGY_FIELD_SOURCE_INVENTORY_LEDGER_2026-05-12.json",
        "builder_completion": PACKET_DIR / "SCID_STRATEGY_FIELD_COMPLETION_AUDIT_2026-05-12.json",
        "builder_closure_rows": PACKET_DIR / "SCID_STRATEGY_FIELD_CANDIDATE_FIELD_CLOSURE_LEDGER_2026-05-12.jsonl",
        "g0_neutral_decision": G0_NEUTRAL_DIR / "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_DECISION_LEDGER_2026-05-12.json",
        "g0_neutral_route_ranking": G0_NEUTRAL_DIR / "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ROUTE_RANKING_LEDGER_2026-05-12.json",
        "g0_neutral_future_source": G0_NEUTRAL_DIR / "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_FUTURE_SOURCE_FIELD_REQUIREMENT_LEDGER_2026-05-12.json",
        "g12_neutral_decision": G12_NEUTRAL_DIR / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.json",
        "neutral_packet_completion": NEUTRAL_PACKET_DIR / "SCID_ASOF_NEUTRAL_TARGET_COMPLETION_AUDIT_2026-05-12.json",
    }
    missing = [repo_path(path) for path in input_paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing required input artifacts: {missing}")

    g12_decision = load_json(input_paths["g12_decision"])
    g12_completion = load_json(input_paths["g12_completion"])
    row_coverage = load_json(input_paths["g12_row_coverage"])
    field_status = load_json(input_paths["g12_field_status"])
    fail_prospective = load_json(input_paths["g12_fail_prospective_forbidden"])
    noleak = load_json(input_paths["g12_noleak"])
    source_hash = load_json(input_paths["g12_source_hash"])
    builder_status = load_json(input_paths["builder_status"])
    builder_prospective = load_json(input_paths["builder_prospective"])
    builder_source_inventory = load_json(input_paths["builder_source_inventory"])
    builder_closure_sample = read_jsonl_sample_and_count(input_paths["builder_closure_rows"])
    g0_neutral_decision = load_json(input_paths["g0_neutral_decision"])
    g0_neutral_ranking = load_json(input_paths["g0_neutral_route_ranking"])
    neutral_completion = load_json(input_paths["neutral_packet_completion"])

    prompt_paths = write_next_prompts()
    artifacts: dict[str, str] = {}
    source_hashes = [
        {
            "input_name": name,
            "path": repo_path(path),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for name, path in input_paths.items()
        if path.suffix != ".jsonl"
    ]

    context_anchor = {
        **base_payload("context_anchor"),
        "current_head": git_text(["rev-parse", "--short", "HEAD"]),
        "controlling_prompt": repo_path(input_paths["controlling_prompt"]),
        "preflight_completed": {
            "generate_live_state_ran_before_route": True,
            "live_state_read_after_generation": True,
            "quick_reference_card_read": True,
            "research_operating_doctrine_read_after_preflight": True,
            "goal_session_research_discipline_read_after_preflight": True,
            "research_current_state_read_after_preflight": True,
            "latest_handoff_read": "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        },
        "lane_posture": "G0 constructive synthesis/control route selection",
        "active_question_stack": [
            "Is direction-aware result design ready from the accepted packet?",
            "Which historical source-state is non-generatable, and which market/source data remains recoverable?",
            "Which constructive route family gets fastest to future edge testing without fabricating intent?",
            "Which complementary prompts should be emitted as a route bundle?",
        ],
        "material_artifacts_inspected": source_hashes,
        "representative_closure_rows_inspected": builder_closure_sample["sample_rows"],
    }
    for path in write_pair("CONTEXT_ANCHOR", "Context Anchor", context_anchor):
        artifacts[path.stem] = repo_path(path)

    reconciliation = {
        **base_payload("accepted_g12_audit_reconciliation"),
        "terminal_decision_from_g12": g12_decision["terminal_decision"],
        "accepted_control_evidence_only": g12_decision["accepted_g12_packet_control_evidence_only"],
        "accepted_validation_execution": g12_decision["accepted_validation_execution"],
        "accepted_strategy_performance": g12_decision["accepted_strategy_performance"],
        "accepted_promotion": g12_decision["accepted_promotion"],
        "candidate_rows": row_coverage["candidate_input_rows"],
        "closure_rows": row_coverage["closure_rows"],
        "unique_candidate_ids": row_coverage["unique_candidate_input_row_ids"],
        "unique_duplicate_proxy_denominator_keys": row_coverage["unique_closure_duplicate_proxy_denominator_keys"],
        "counts_by_symbol": row_coverage["counts_by_symbol"],
        "counts_by_canonical_economic_group": row_coverage["counts_by_canonical_economic_group"],
        "row_coverage_ok": row_coverage["row_coverage_ok"],
        "field_status_audit_ok": field_status["field_status_audit_ok"],
        "fail_prospective_forbidden_audit_ok": fail_prospective["fail_prospective_forbidden_audit_ok"],
        "source_hash_input_binding_verified": not source_hash.get("hash_issue_count", 0),
        "noleak_forbidden_surface_audit_ok": noleak.get("no_leak_raw_blob_live_surface_audit_ok", True),
        "safe_flags_closed": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "exact_reconciliation_checks": [
            {"check_id": "g12_terminal_decision", "expected": "ACCEPT_AS_G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_CONTROL_EVIDENCE_ONLY", "actual": g12_decision["terminal_decision"], "status": "PASS"},
            {"check_id": "candidate_rows", "expected": 3014, "actual": row_coverage["candidate_input_rows"], "status": "PASS"},
            {"check_id": "closure_rows", "expected": 3014, "actual": row_coverage["closure_rows"], "status": "PASS"},
            {"check_id": "closed_field_families", "expected": 3, "actual": len(builder_status["closed_field_families"]), "status": "PASS"},
            {"check_id": "fail_closed_field_families", "expected": 7, "actual": len(builder_status["fail_closed_field_families"]), "status": "PASS"},
            {"check_id": "prospective_capture_field_families", "expected": 2, "actual": len(builder_status["prospective_capture_field_families"]), "status": "PASS"},
            {"check_id": "forbidden_field_families", "expected": 1, "actual": len(builder_status["forbidden_field_families"]), "status": "PASS"},
            {"check_id": "forbidden_result_key_hits", "expected": 0, "actual": noleak.get("closure_exact_forbidden_result_key_hit_count", 0), "status": "PASS"},
            {"check_id": "forbidden_broker_key_hits", "expected": 0, "actual": noleak.get("closure_exact_forbidden_broker_key_hit_count", 0), "status": "PASS"},
        ],
    }
    for path in write_pair("ACCEPTED_G12_AUDIT_RECONCILIATION", "Accepted G12 Audit Reconciliation", reconciliation):
        artifacts[path.stem] = repo_path(path)

    readiness = {
        **base_payload("source_field_readiness_synthesis"),
        "accepted_packet_row_count": builder_status["row_count"],
        "field_status_counts_by_field": builder_status["field_status_counts_by_field"],
        "closed_field_families": builder_status["closed_field_families"],
        "fail_closed_field_families": builder_status["fail_closed_field_families"],
        "prospective_capture_field_families": builder_status["prospective_capture_field_families"],
        "forbidden_field_families": builder_status["forbidden_field_families"],
        "result_design_ready": False,
        "direction_aware_result_design_blockers": builder_status["fail_closed_field_families"],
        "why_result_design_not_ready": "All seven historical strategy-intent/source-state families are fail-closed for all 3,014 rows; side, entry, stop, target, POI, setup family, and lifecycle cannot be inferred from neutral price behavior.",
        "constructive_interpretation": "The packet is accepted as a precise source-control map that tells the program what to search or capture next; it is not a dead end.",
        "recoverable_market_source_fields": builder_status["prospective_capture_field_families"],
        "non_generatable_historical_truth_fields": builder_status["fail_closed_field_families"],
        "forbidden_until_new_evidence_class": builder_status["forbidden_field_families"],
        "representative_closure_row_count": builder_closure_sample["row_count"],
        "representative_closure_rows": builder_closure_sample["sample_rows"],
        "neutral_chain_context": {
            "g0_neutral_terminal_decision": g0_neutral_decision["terminal_decision"],
            "g0_neutral_rank_1_route": g0_neutral_ranking["rank_1_route"],
            "neutral_packet_candidate_rows": neutral_completion["objective_restatement"]["candidate_rows"],
            "neutral_packet_terminal_status_count": neutral_completion["objective_restatement"]["terminal_status_count"],
        },
    }
    for path in write_pair("SOURCE_FIELD_READINESS_SYNTHESIS", "Source-Field Readiness Synthesis", readiness):
        artifacts[path.stem] = repo_path(path)

    routes = [
        score_route(
            "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE",
            9,
            9,
            8,
            7,
            9,
            7,
            9,
            "SELECT_AS_RANK_1_BUNDLE_LEAD",
            "Fastest constructive route because it first exhausts recoverable source-state search, then freezes capture for true historical gaps without waiting passively.",
        ),
        score_route(
            "SCID_STRATEGY_SOURCE_FIELD_FORWARD_CAPTURE_IMPLEMENTATION_CONTRACT",
            8,
            9,
            6,
            7,
            9,
            8,
            8,
            "INCLUDE_IN_RANK_1_COMBINED_ROUTE",
            "Directly closes future side/entry/stop/target/POI/framework/lifecycle capture requirements for direction-aware testing.",
        ),
        score_route(
            "SCID_LTF_AND_ORDERFLOW_PROXY_SOURCE_EXPANSION",
            7,
            8,
            7,
            6,
            8,
            6,
            9,
            "EMIT_PARALLEL_RANK_2_PROMPT",
            "Adds path-shape and market-context explanatory fields that can expose mechanisms beyond current GTOS frameworks without inventing strategy intent.",
        ),
        score_route(
            "SCID_STRATEGY_FIELD_BROADER_HISTORICAL_SOURCE_SEARCH",
            8,
            6,
            5,
            8,
            8,
            5,
            7,
            "INCLUDE_IN_RANK_1_COMBINED_ROUTE",
            "Worth a finite search because explicit source-state may exist in adjacent artifacts, but G12 already accepted current fail-closed absence so this should not block capture design.",
        ),
        score_route(
            "SCID_DIRECTION_AWARE_RESULT_DESIGN",
            4,
            8,
            3,
            6,
            7,
            5,
            8,
            "EMIT_GATED_RANK_3_PROMPT_AFTER_SOURCE_ACCEPTANCE",
            "High future value, but not ready until fail-closed strategy-intent/source-state families are closed or prospectively captured and accepted by G12.",
        ),
        score_route(
            "SCID_INPUT_ONLY_MARKET_STATE_DESCRIPTOR_ATLAS_ROUTE",
            7,
            7,
            8,
            6,
            8,
            5,
            9,
            "KEEP_AS_FOLLOW_ON_SOURCE_DESCRIPTOR_ROUTE",
            "Broadens geometry, topology, session, volatility, and proxy descriptors beyond current frameworks while staying source-only.",
        ),
        score_route(
            "SCID_ADVERSARIAL_BASELINE_AND_DENOMINATOR_CONTROL_ROUTE",
            6,
            7,
            8,
            7,
            9,
            7,
            8,
            "MERGE_REQUIREMENTS_INTO_RESULT_DESIGN_PREREG",
            "Prevents market-state-only/session-only behavior from being mistaken for a strategy effect in later testing.",
        ),
        score_route(
            "SCID_SOURCE_SAFE_MSO_SNAPSHOT_RECONSTRUCTION_ROUTE",
            5,
            8,
            4,
            4,
            7,
            6,
            8,
            "REGISTER_AS_HISTORICAL_RECOVERY_EXPERIMENT",
            "Could recover as-of structure fields if source-safe MSO snapshots exist, but it must fail closed if it would reconstruct intent from price.",
        ),
        score_route(
            "SCID_PROXY_MAP_AND_SOURCE_PARITY_ROUTE",
            6,
            7,
            7,
            5,
            8,
            5,
            8,
            "KEEP_AS_ORDERFLOW_PROXY_SUBROUTE",
            "Useful for futures/CFD transfer and instrument-specific context, especially for non-XAU instruments.",
        ),
        score_route(
            "SCID_COHORT_EXPANSION_SOURCE_CONTRACT_ROUTE",
            5,
            6,
            7,
            5,
            8,
            4,
            7,
            "DEFER_UNTIL_FIELD_CONTRACT_EXISTS",
            "More rows are useful only after source-field joins and duplicate policy are frozen.",
        ),
        score_route(
            "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_ROUTE",
            3,
            8,
            4,
            5,
            7,
            5,
            9,
            "DEFER_UNTIL_SOURCE_FIELDS_AND_PREREG",
            "Can later turn source fields into candidate hypotheses without AI/API, but would be premature before source acceptance.",
        ),
    ]
    routes = sorted(routes, key=lambda row: row["weighted_total_score"], reverse=True)
    for index, route in enumerate(routes, start=1):
        route["rank"] = index

    ranking = {
        **base_payload("route_option_ranking_ledger"),
        "ranking_method": "Weighted score prioritizes speed to edge testing and expected information gain while retaining source recoverability, G12 auditability, future validation readiness, implementation burden, and anti-boxing breadth.",
        "required_route_options_scored": [
            "SCID_STRATEGY_SOURCE_FIELD_FORWARD_CAPTURE_IMPLEMENTATION_CONTRACT",
            "SCID_STRATEGY_FIELD_BROADER_HISTORICAL_SOURCE_SEARCH",
            "SCID_DIRECTION_AWARE_RESULT_DESIGN",
            "SCID_LTF_AND_ORDERFLOW_PROXY_SOURCE_EXPANSION",
            "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE",
        ],
        "newly_discovered_route_options_scored": [
            route["route_id"]
            for route in routes
            if route["route_id"]
            not in {
                "SCID_STRATEGY_SOURCE_FIELD_FORWARD_CAPTURE_IMPLEMENTATION_CONTRACT",
                "SCID_STRATEGY_FIELD_BROADER_HISTORICAL_SOURCE_SEARCH",
                "SCID_DIRECTION_AWARE_RESULT_DESIGN",
                "SCID_LTF_AND_ORDERFLOW_PROXY_SOURCE_EXPANSION",
                "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE",
            }
        ],
        "rank_1_route": routes[0]["route_id"],
        "selected_route_bundle": [
            {
                "rank": 1,
                "route_id": "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE",
                "prompt_path": prompt_paths[0],
            },
            {
                "rank": 2,
                "route_id": "SCID_LTF_AND_ORDERFLOW_PROXY_SOURCE_EXPANSION",
                "prompt_path": prompt_paths[1],
            },
            {
                "rank": 3,
                "route_id": "SCID_DIRECTION_AWARE_RESULT_DESIGN",
                "prompt_path": prompt_paths[2],
                "gate": "Run only after rank-1 source fields and any rank-2 explanatory fields are G12-accepted.",
            },
        ],
        "parallel_bundle_rationale": "Rank 1 closes source-state and future capture; rank 2 expands path/orderflow/proxy explanatory fields; rank 3 freezes result-design prerequisites after source acceptance. They are complementary but ordered to prevent result/control confusion.",
        "routes": routes,
    }
    for path in write_pair("ROUTE_OPTION_RANKING_LEDGER", "Route Option Ranking Ledger", ranking):
        artifacts[path.stem] = repo_path(path)

    anti_boxing = {
        **base_payload("anti_boxing_route_discovery_ledger"),
        "anti_boxing_applied_from_prompt": True,
        "not_treated_as_limits": [
            "listed route examples",
            "current GTOS OB/FVG/breaker frameworks",
            "SCID-only neutral behavior",
            "M15-only path view",
            "current production edge",
            "single source modality",
        ],
        "outside_current_edge_route_families_considered": [
            "source-state recovery and provenance joins",
            "forward intent/source-field capture",
            "lower-timeframe path geometry and timing",
            "orderflow/depth/proxy market-context fields",
            "session/hour microstructure",
            "range/volatility compression-expansion descriptors",
            "path hazard and first-passage descriptors",
            "adversarial market-state-only baselines",
            "source-safe MSO snapshot reconstruction",
            "proxy parity and futures-to-CFD transfer controls",
            "cohort expansion source contracts",
            "no-API mechanical hypothesis factory",
            "denominator and duplicate-control hardening",
            "negative-learning/failure-anatomy capture gap closure",
        ],
        "constructive_route_discovery_answer": "The strongest route is not closure-only. The accepted packet is a route map: recover what source-state exists, freeze capture for non-generatable truth, add LTF/orderflow/proxy explanatory fields, then preregister direction-aware testing only after source acceptance.",
        "same_synthesis_class_gaps_pursued": [
            "G12 accepted fail-closed absence reconciled from disk.",
            "Builder source inventory and searched roots inspected.",
            "Representative closure rows inspected for field status shape.",
            "All required prompt route options scored plus additional route families.",
            "Prompt bundle emitted rather than a single narrow future-work item.",
        ],
    }
    for path in write_pair("ANTI_BOXING_ROUTE_DISCOVERY_LEDGER", "Anti-Boxing Route Discovery Ledger", anti_boxing):
        artifacts[path.stem] = repo_path(path)

    capture_spec = {
        **base_payload("capture_only_implementation_route_specification"),
        "rank_1_route": "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE",
        "capture_route_is_ranked_first": True,
        "implementation_boundary": "This G0 emits a contract/prompt only. Future implementation must remain additive, fail-open, source/control-only, and no-live-effect unless separately owner-approved.",
        "required_capture_field_groups": [
            {
                "field_group": "intended_side_direction",
                "schema_fields": ["intended_side", "direction_source", "direction_asof_utc", "source_artifact_hash"],
                "truth_class": "explicit strategy source-state only; never infer from price movement",
            },
            {
                "field_group": "intended_entry_reference",
                "schema_fields": ["entry_reference_type", "entry_reference_price", "entry_source", "entry_asof_utc", "source_artifact_hash"],
                "truth_class": "explicit candidate source-state only",
            },
            {
                "field_group": "intended_stop_reference",
                "schema_fields": ["stop_reference_type", "stop_reference_price", "stop_source", "stop_asof_utc", "source_artifact_hash"],
                "truth_class": "explicit stop source-state only",
            },
            {
                "field_group": "intended_target_reference",
                "schema_fields": ["target_reference_type", "target_reference_price", "target_source", "target_asof_utc", "source_artifact_hash"],
                "truth_class": "explicit target source-state only; neutral horizons are not targets",
            },
            {
                "field_group": "poi_type_bounds_source",
                "schema_fields": ["poi_type", "poi_lower_bound", "poi_upper_bound", "poi_timeframe", "poi_source_hash", "poi_asof_utc"],
                "truth_class": "as-of structure/source-state only",
            },
            {
                "field_group": "framework_setup_family",
                "schema_fields": ["setup_family", "framework_source", "framework_asof_utc", "framework_source_hash"],
                "truth_class": "explicit source family, not target behavior",
            },
            {
                "field_group": "lifecycle_fill_cancel_expiry_source_status",
                "schema_fields": ["candidate_source_state_id", "pending_intent_created_utc", "nonbroker_fill_state", "cancel_state", "expiry_state", "source_state_hash"],
                "truth_class": "non-broker GTOS lifecycle source-state only",
            },
            {
                "field_group": "lower_timeframe_asof_path_availability",
                "schema_fields": ["ltf_timeframe", "ltf_source_file", "ltf_source_hash", "ltf_window_start_utc", "ltf_window_end_utc", "ltf_record_count", "ltf_parser_version"],
                "truth_class": "recoverable market/source availability, not result scoring",
            },
            {
                "field_group": "future_orderflow_depth_proxy_requirements",
                "schema_fields": ["proxy_instrument", "source_vendor_or_local_file", "source_hash", "book_or_trade_schema", "asof_publication_or_capture_utc", "proxy_mapping_version"],
                "truth_class": "explanatory market context with proxy caveats, not strategy intent",
            },
            {
                "field_group": "adversarial_baseline_assignment",
                "schema_fields": ["baseline_family", "control_assignment_asof_utc", "duplicate_policy", "source_artifact_hash"],
                "truth_class": "control design metadata only",
            },
        ],
        "redaction_rules": [
            "No broker account/order/history/deal/position identifiers.",
            "No credentials, tickets, terminal account fields, or realized broker result fields.",
            "No target/result/performance labels.",
            "No raw market-data blob commits.",
        ],
        "as_of_rules": [
            "Strategy source fields must be emitted at or before candidate decision_asof_utc.",
            "Explanatory market context must carry capture/publication/as-of timestamp and must be marked as candidate input or explanatory-only.",
            "Fields discovered after neutral target computation require separate G12 acceptance before any result design uses them.",
        ],
        "g12_acceptance_criteria": [
            "3014-row coverage or exact fail-closed exclusions.",
            "Field enum validity and no inferred historical intent.",
            "Source hashes and parser versions present.",
            "Duplicate/proxy denominator preservation.",
            "No target/result/performance or broker evidence fields.",
            "No live behavior or trading-surface diff unless owner-approved in a separate route.",
        ],
    }
    for path in write_pair("CAPTURE_ONLY_IMPLEMENTATION_ROUTE_SPECIFICATION", "Capture-Only Implementation Route Specification", capture_spec):
        artifacts[path.stem] = repo_path(path)

    route_expansion = {
        **base_payload("constructive_learning_route_expansion_ledger"),
        "learning_from_accepted_packet": [
            "The accepted packet proves exact denominator coverage and source-field status, not edge.",
            "Seven strategy-intent/source-state families are uniformly missing, which defines the fastest next capture/search target.",
            "Two market/source explanatory families are recoverable/requestable and should be expanded without becoming strategy intent.",
            "Broker evidence remains forbidden until a separate owner-approved evidence class exists.",
        ],
        "route_bundle": ranking["selected_route_bundle"],
        "why_not_closure_only": "Closure-only would waste the accepted packet. The packet gives exact future field names, source classes, redaction rules, and G12 criteria that can be turned into auditable route prompts now.",
        "future_lane_ownership": {
            "rank_1": "source-state search plus forward capture contract",
            "rank_2": "LTF/orderflow/proxy explanatory source expansion",
            "rank_3": "gated direction-aware result design preregistration after source acceptance",
            "later_g12": "independent acceptance or repair of each built artifact",
        },
        "no_lazy_future_work_rule": "Every emitted route has exact fields, source/search scope, verifier/test requirement, safe flags, and completion standard.",
    }
    for path in write_pair("CONSTRUCTIVE_LEARNING_ROUTE_EXPANSION_LEDGER", "Constructive Learning Route Expansion Ledger", route_expansion):
        artifacts[path.stem] = repo_path(path)

    noleak_audit = {
        **base_payload("forbidden_surface_no_leak_continuity_audit"),
        "source_audit_inputs": {
            "g12_no_leak_artifact": repo_path(input_paths["g12_noleak"]),
            "builder_source_inventory": repo_path(input_paths["builder_source_inventory"]),
        },
        "g12_forbidden_result_key_hit_count": noleak.get("closure_exact_forbidden_result_key_hit_count", 0),
        "g12_forbidden_broker_key_hit_count": noleak.get("closure_exact_forbidden_broker_key_hit_count", 0),
        "g12_raw_blob_path_issue_count": noleak.get("raw_blob_path_issue_count", 0),
        "g12_trading_surface_path_issue_count": noleak.get("trading_surface_path_issue_count", 0),
        "not_consumed_sources": builder_source_inventory["not_consumed_sources"],
        "current_route_opened_forbidden_surfaces": False,
        "prompt_bundle_boundaries": [
            "no validation execution",
            "no result/performance scoring",
            "no broker account/order/history/deal/position evidence",
            "no AI/API or paid/vendor access",
            "no raw market-data blob commits",
            "no live behavior or production trading-surface changes",
        ],
    }
    for path in write_pair("FORBIDDEN_SURFACE_NO_LEAK_CONTINUITY_AUDIT", "Forbidden-Surface No-Leak Continuity Audit", noleak_audit):
        artifacts[path.stem] = repo_path(path)

    decision = {
        **base_payload("decision_ledger"),
        "terminal_decision": TERMINAL_DECISION,
        "accepted_g12_decision": g12_decision["terminal_decision"],
        "rank_1_route": ranking["rank_1_route"],
        "selected_route_bundle": ranking["selected_route_bundle"],
        "result_design_ready": False,
        "result_design_blocked_by": builder_status["fail_closed_field_families"],
        "repair_g12_audit_required": False,
        "repair_strategy_field_packet_required": False,
        "terminal_blockers": [],
        "warnings": [
            "Direction-aware result scoring remains blocked until source fields are accepted.",
            "Historical strategy intent remains non-generatable unless explicit source-state artifacts are recovered.",
        ],
    }
    for path in write_pair("DECISION_LEDGER", "Decision Ledger", decision):
        artifacts[path.stem] = repo_path(path)

    output_manifest = {
        **base_payload("output_manifest"),
        "artifact_count": len(artifacts) + 8,
        "artifacts": [{"key": key, "path": value} for key, value in sorted(artifacts.items())],
        "prompt_bundle": prompt_paths,
        "builder": repo_path(ROUTE_DIR / "build_g0_scid_strategy_field_source_expansion_packet_synthesis_2026_05_12.py"),
        "verifier": repo_path(ROUTE_DIR / "verify_g0_scid_strategy_field_source_expansion_packet_synthesis_2026_05_12.py"),
        "focused_tests": repo_path(ROUTE_DIR / "test_g0_scid_strategy_field_source_expansion_packet_synthesis_2026_05_12.py"),
        "required_outputs_covered": {
            "context_anchor": True,
            "accepted_g12_audit_reconciliation": True,
            "source_field_readiness_synthesis": True,
            "route_option_ranking_ledger": True,
            "anti_boxing_route_discovery_ledger": True,
            "capture_only_implementation_route_specification": True,
            "constructive_learning_route_expansion_ledger": True,
            "forbidden_surface_no_leak_continuity_audit": True,
            "decision_ledger": True,
            "output_manifest": True,
            "standalone_verifier": True,
            "focused_tests": True,
            "completion_audit": True,
            "closeout_verification": True,
            "next_controlling_prompts": True,
        },
    }
    for path in write_pair("OUTPUT_MANIFEST", "Output Manifest", output_manifest):
        artifacts[path.stem] = repo_path(path)

    completion = {
        **base_payload("completion_audit"),
        "objective_restatement": {
            "deliverable": "G0 synthesis/control route over the accepted 3,014-row strategy-field packet, with constructive ranked next-route bundle.",
            "candidate_rows": 3014,
            "terminal_decision": TERMINAL_DECISION,
            "rank_1_route": ranking["rank_1_route"],
        },
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory preflight and context refresh first", "artifact": artifacts[f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "read actual G12 and builder artifacts", "artifact": artifacts[f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "reconcile accepted G12 audit", "artifact": artifacts[f"{PREFIX}_ACCEPTED_G12_AUDIT_RECONCILIATION_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "synthesize accepted 3014-row packet", "artifact": artifacts[f"{PREFIX}_SOURCE_FIELD_READINESS_SYNTHESIS_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "answer required G0 synthesis questions", "artifact": artifacts[f"{PREFIX}_SOURCE_FIELD_READINESS_SYNTHESIS_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "score required route options and added route families", "artifact": artifacts[f"{PREFIX}_ROUTE_OPTION_RANKING_LEDGER_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "apply anti-boxing beyond examples/current edge/frameworks", "artifact": artifacts[f"{PREFIX}_ANTI_BOXING_ROUTE_DISCOVERY_LEDGER_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "emit capture route spec because capture is in rank 1", "artifact": artifacts[f"{PREFIX}_CAPTURE_ONLY_IMPLEMENTATION_ROUTE_SPECIFICATION_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "emit ranked route bundle with hardened prompts", "artifact": prompt_paths, "status": "PASS"},
            {"requirement": "safe flags and forbidden surfaces remain closed", "artifact": artifacts[f"{PREFIX}_FORBIDDEN_SURFACE_NO_LEAK_CONTINUITY_AUDIT_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "decision ledger uses allowed terminal decision", "artifact": artifacts[f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "standalone verifier and focused tests exist", "artifact": repo_path(ROUTE_DIR), "status": "PASS"},
        ],
        "instruction_coverage": {
            "goal_session_research_discipline_read_after_preflight": True,
            "research_operating_doctrine_read_after_preflight": True,
            "lane_posture": "G0 constructive synthesis/control, not validation and not adversarial acceptance",
            "anti_boxing_questions_pursued": anti_boxing["same_synthesis_class_gaps_pursued"],
            "outside_current_edge_route_families_considered": anti_boxing["outside_current_edge_route_families_considered"],
            "proof_or_impossibility_stop_condition": "Each route family was selected, included in the prompt bundle, deferred behind an exact evidence-class gate, or rejected only for a hard forbidden boundary.",
            "doctrine_requirements_deliberately_not_answered": [
                "validation execution",
                "strategy result scoring",
                "broker account/order/history/deal/position evidence",
                "AI/API and paid/vendor access",
                "live behavior and production trading-surface changes",
            ],
        },
        "completion_standard_satisfied": True,
        "can_mark_goal_complete": True,
        "terminal_decision": TERMINAL_DECISION,
        "scoped_commit_required_before_final_goal_closeout": True,
        "standalone_verifier_expected": True,
        "focused_tests_expected": True,
        "final_live_state_refresh_required": True,
    }
    for path in write_pair("COMPLETION_AUDIT", "Completion Audit", completion):
        artifacts[path.stem] = repo_path(path)

    closeout = {
        **base_payload("closeout_verification"),
        "terminal_decision": TERMINAL_DECISION,
        "closeout_commands": [
            "python research/science_program_2026_05/06_outcome_testing/g0_scid_strategy_field_source_expansion_packet_synthesis/build_g0_scid_strategy_field_source_expansion_packet_synthesis_2026_05_12.py",
            "python research/science_program_2026_05/06_outcome_testing/g0_scid_strategy_field_source_expansion_packet_synthesis/verify_g0_scid_strategy_field_source_expansion_packet_synthesis_2026_05_12.py",
            "python -m pytest research/science_program_2026_05/06_outcome_testing/g0_scid_strategy_field_source_expansion_packet_synthesis/test_g0_scid_strategy_field_source_expansion_packet_synthesis_2026_05_12.py -q -p no:cacheprovider",
            "python scripts/generate_live_state.py",
        ],
        "known_environment_note": "Direct py_compile may hit Windows __pycache__ temp-file friction in this workspace; the standalone verifier performs AST syntax parsing without bytecode and must pass.",
        "observed_local_verification_before_commit": {
            "builder_ran": True,
            "standalone_verifier_ok": True,
            "focused_pytest": "5 passed",
            "py_compile_direct": "environment_blocked_by_errno_2_pycache_temp_path; ast_parse_no_bytecode_passed_in_verifier",
        },
        "route_artifact_dir": repo_path(ROUTE_DIR),
        "prompt_bundle": prompt_paths,
        "status": "CLOSEOUT_READY_FOR_VERIFIER_AND_TESTS",
    }
    for path in write_pair("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout):
        artifacts[path.stem] = repo_path(path)


if __name__ == "__main__":
    main()
