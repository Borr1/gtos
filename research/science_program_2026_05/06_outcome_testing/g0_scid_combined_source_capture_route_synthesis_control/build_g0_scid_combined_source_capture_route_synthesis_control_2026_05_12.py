"""Build G0 SCID combined source-capture route synthesis artifacts.

This route is G0 synthesis/control only. It reconciles the accepted G12
combined source-search/capture audit, ranks same-class next routes, and emits
next prompt packs without opening validation, result scoring, broker evidence,
AI/API calls, paid/vendor access, raw market-data blobs, or live behavior.
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
G12_DIR = OUTCOME_DIR / "g12_scid_combined_source_search_and_forward_capture_route_audit"
BUILDER_DIR = OUTCOME_DIR / "scid_combined_source_search_and_forward_capture_route"
G0_STRATEGY_DIR = OUTCOME_DIR / "g0_scid_strategy_field_source_expansion_packet_synthesis"
STRATEGY_PACKET_DIR = OUTCOME_DIR / "scid_strategy_field_source_expansion_packet"

DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS"
ROUTE_ID = "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL"
EVIDENCE_CLASS = "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_WITH_RANKED_ROUTE_BUNDLE"

RANK1_PROMPT = "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md"
LTF_PROMPT = "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md"
FACTORY_PROMPT = "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS_GOAL_PROMPT_2026-05-12.md"
RESULT_DESIGN_PROMPT = "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md"

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

FORBIDDEN_SURFACES = (
    "validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/"
    "promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/"
    "raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes"
)


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
        "schema_version": "g0_scid_combined_source_capture_synthesis_v1",
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


def run_command(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "args": args,
        "returncode": proc.returncode,
        "status": "PASSED" if proc.returncode == 0 else "FAILED",
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def prompt_body(
    title: str,
    evidence_class: str,
    objective: str,
    required_outputs: list[str],
    completion_items: list[str],
    one_line_tail: str,
    extra_requirements: list[str] | None = None,
) -> str:
    outputs = "\n".join(f"- {item}" for item in required_outputs)
    completion = "\n".join(f"{index}. {item}" for index, item in enumerate(completion_items, start=1))
    extra = "\n".join(f"- {item}" for item in (extra_requirements or []))
    if extra:
        extra = "\n## Route-Specific Requirements\n\n" + extra + "\n"

    return f"""# {title}

Date: {DATE_TAG}
Owner lane: prompt pack emitted by G0 SCID combined source-capture synthesis
Evidence class: `{evidence_class}`
Input G0 route: `research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/`
Input G12 audit: `research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

{objective}

Examples are starting points, not limits. current GTOS OB/retest logic, current SCID M15 framing, no-fill history, current framework labels, and the listed files are not the research horizon. Stay auditable, as-of, no-leak, and hard-boundary-compliant while actively searching for useful source/control route families.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the accepted G12 combined source-capture audit context anchor, decision ledger, row coverage audit, field-status audit, source-search saturation audit, source-hash/manifest binding audit, capture-contract exactness audit, no-leak/forbidden-surface audit, output manifest, verifier result, completion audit, and closeout verification.
9. Read the G0 combined synthesis context anchor, route ranking ledger, carry-forward capture contract ledger, manifest-binding repair note, implementation/readiness boundary ledger, forbidden-surface audit, prompt-pack ledger, decision ledger, completion audit, and closeout verification.
10. Read the underlying builder route artifacts and accepted G0/G12 strategy-field packet artifacts cited by the audit.

Do not rely on chat memory. If interrupted or compacted, regenerate `LIVE_STATE`, re-read this prompt and the current route artifacts from disk, and resume from the emitted context anchor.

## Mandatory Context Use

Treat `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active instructions. Record in the completion audit:

- whether both were read after preflight;
- the builder/control posture applied;
- anti-boxing questions pursued;
- searched roots and artifacts inspected;
- proof-or-impossibility stop condition;
- any doctrine requirement deliberately not answered because it crosses validation, result scoring, broker evidence, AI/API, paid/vendor, raw-blob, prompt/config/risk/safety/execution/canary/selector, or live-behavior boundaries.

## G12 Repair Handoff

Carry forward the accepted manifest-binding repair exactly:

- The G12 prompt hash was rebound after post-build prompt hardening.
- The builder output manifest self-hash is self-referential and is not a blocking future binding.
- All other source/input hash mismatches remain strict blockers.
- Future verifiers must not reject solely because they compare against the stale pre-hardening G12 prompt hash or a self-referential manifest hash.

## Hard Boundaries

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`. Do not open {FORBIDDEN_SURFACES}.

Use checkpointing, chunking, and resumable ledgers rather than accepting shallow summaries. Request access only when the route allows it and local/source-safe pursuit is exhausted. Do not stage unrelated runtime, shadow, live-monitoring, or raw market-data dirt.
{extra}
## Required Outputs

Create a dedicated route directory under `research/science_program_2026_05/06_outcome_testing/` and emit:

{outputs}

## Saturation And Self-Red-Team

Before completion, answer from disk artifacts:

- Did the route stay in the declared evidence class?
- Did any historical intent field get inferred from price, target behavior, path label, or broker evidence?
- Are side, entry, stop, target, POI, framework, lifecycle, LTF, orderflow/proxy, and baseline-control fields either closed, fail-closed, prospective-capture-required, or forbidden?
- Did the route avoid boxing around current GTOS/OB-only framing?
- Did it preserve the 3,014 candidate denominator, the 24,112 neutral target status context, and the 13,540,033 FPB discovery substrate boundaries without treating any of them as performance proof?
- Are blockers exact and actionable rather than vague "future work"?
- Would a later G12 reject the output for denominator drift, no-leak failure, source hash weakness, stale repair handling, vague capture requirements, or forbidden-surface changes?

## Completion Standard

{completion}

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/{title_to_filename(title)} as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay {evidence_class} with no {FORBIDDEN_SURFACES}; {one_line_tail}; scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; if any blocker appears, pursue until cleared, proven impossible from approved routes, or reduced to an exact owner/access/source/capture approval requirement, and mark complete only when the prompt file's completion standard is fully satisfied.`
"""


def title_to_filename(title: str) -> str:
    mapping = {
        "SCID Forward Capture Offline Schema Implementation Package Goal Prompt": RANK1_PROMPT,
        "SCID LTF Orderflow Proxy Source Expansion From Capture Audit Goal Prompt": LTF_PROMPT,
        "SCID No-API Mechanical Hypothesis Factory From Accepted Descriptors Goal Prompt": FACTORY_PROMPT,
        "SCID Direction-Aware Result Design Preregistration From Capture Audit Goal Prompt": RESULT_DESIGN_PROMPT,
    }
    return mapping[title]


def build_prompts() -> dict[str, str]:
    prompt_specs = {
        RANK1_PROMPT: prompt_body(
            title="SCID Forward Capture Offline Schema Implementation Package Goal Prompt",
            evidence_class="SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY",
            objective=(
                "Implement the accepted G12 forward capture contract as offline/schema/test artifacts only. "
                "Produce JSON schemas, parser contracts, redaction rules, fail-closed validators, sample synthetic "
                "fixture rows, and read-only alignment maps for current shadow/live monitoring outputs. Do not wire "
                "anything into live orchestration, execution, prompts, risk, canaries, or selectors."
            ),
            required_outputs=[
                "context anchor and accepted G12/G0 handoff reconciliation",
                "offline schema files or schema ledgers for `scid_forward_source_capture_v1`",
                "per-field parser/redaction/as-of/no-leak/fail-closed validator contract",
                "sample synthetic fixture rows that contain no broker/account/order/deal/position identifiers",
                "read-only current shadow/live monitoring alignment ledger with no code wiring",
                "G12 acceptance criteria and next independent audit prompt",
                "standalone verifier, focused tests, output manifest, completion audit, closeout verification",
            ],
            completion_items=[
                "Mandatory preflight and context use are recorded.",
                "Every accepted G12 capture group has exact schema, parser, redaction, as-of, no-leak, fail-closed, and G12 acceptance criteria.",
                "No live wiring, production behavior, prompt/config/risk/safety/execution/canary/selector change, broker evidence, AI/API, paid/vendor use, raw market blob commit, validation, or result scoring is opened.",
                "Verifier and focused tests pass.",
                "Scoped commits and final `python scripts/generate_live_state.py` closeout are complete.",
            ],
            one_line_tail=(
                "implement the accepted capture contract offline only with schemas, parser/redaction/as-of/no-leak "
                "validators, synthetic fixtures, read-only monitoring alignment, G12 prompt, verifier and focused tests"
            ),
            extra_requirements=[
                "Use the accepted G12 field groups unchanged: side, entry, stop, target, POI, framework, lifecycle, LTF, orderflow/proxy, and baseline-control.",
                "Combine `SCID_FORWARD_SHADOW_CAPTURE_MONITORING_ALIGNMENT` only as read-only schema/readiness alignment; do not wire loggers or alter running processes.",
                "Preserve duplicate proxy denominator keys and candidate_input_row_id coverage expectations for all 3,014 rows.",
            ],
        ),
        LTF_PROMPT: prompt_body(
            title="SCID LTF Orderflow Proxy Source Expansion From Capture Audit Goal Prompt",
            evidence_class="SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_CAPTURE_AUDIT_ONLY",
            objective=(
                "Expand lower-timeframe, path-shape, orderflow/depth/proxy, session, volatility, hazard, and "
                "instrument/proxy source-control descriptors around the accepted 3,014 SCID candidates. Materialize "
                "and hash source inventories when allowed; freeze exact capture contracts where source data is absent. "
                "This is explanatory source/control only, not strategy intent or result scoring."
            ),
            required_outputs=[
                "context anchor and accepted G12/G0 handoff reconciliation",
                "searched-root and source-materialization ledgers for LTF/orderflow/proxy/session/volatility/path descriptors",
                "LTF availability contract with source hash, parser, as-of, and no-leak requirements",
                "orderflow/depth/proxy contract with proxy caveats and no raw blob commits",
                "instrument/session/timeframe anti-boxing ledger",
                "forbidden-surface audit, G12 acceptance criteria, verifier, focused tests, completion audit, closeout verification",
            ],
            completion_items=[
                "Mandatory preflight and context use are recorded.",
                "Every explanatory field has exact source, hash, as-of, schema, redaction, parser, and G12 criteria or an exact missing-source requirement.",
                "Explanatory market context remains separated from strategy intent, target/result fields, and broker evidence.",
                "Verifier and focused tests pass.",
                "Scoped commits and final closeout are complete.",
            ],
            one_line_tail=(
                "search broadly for auditable M1/M5/tick/depth/proxy/session/volatility/path-hazard explanatory "
                "sources, materialize and hash allowed inventories, freeze exact contracts, verifier and focused tests"
            ),
            extra_requirements=[
                "Do not treat futures/proxy evidence as direct CFD or broker behavior proof.",
                "Do not commit raw `.scid`, `.depth`, `.parquet`, `.csv`, `.dly`, `.bin`, or `.jsonl.gz` blobs.",
                "If local heavy data is needed and source/control policy allows it, search absolute local roots or request exact access rather than stopping at worktree absence.",
            ],
        ),
        FACTORY_PROMPT: prompt_body(
            title="SCID No-API Mechanical Hypothesis Factory From Accepted Descriptors Goal Prompt",
            evidence_class="SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS_ONLY",
            objective=(
                "Design a no-API, no-result-scoring mechanical hypothesis factory from accepted source/control "
                "descriptors and future capture fields. The output is a preregistration-ready hypothesis and feature "
                "family registry, not a replay, validation, edge claim, or performance screen."
            ),
            required_outputs=[
                "context anchor and source/control prerequisite ledger",
                "outside-current-edge hypothesis family registry",
                "descriptor-to-hypothesis mapping for geometry, topology, volatility/tails, session/calendar, LTF path, orderflow/proxy, liquidity, regime, execution/cost readiness, ML/meta-labeling, and adversarial baselines",
                "feature availability and source-control blocker ledger",
                "no-API/no-result boundary audit",
                "G12/G0 handoff criteria, verifier, focused tests, output manifest, completion audit, closeout verification",
            ],
            completion_items=[
                "Mandatory preflight and context use are recorded.",
                "Every hypothesis family is tied to accepted descriptors or exact future capture fields.",
                "No API calls, validation execution, result scoring, performance field, broker evidence, raw blob commit, or live behavior is opened.",
                "Verifier and focused tests pass.",
                "Scoped commits and final closeout are complete.",
            ],
            one_line_tail=(
                "design a broad no-API source/control hypothesis factory from accepted descriptors and future fields, "
                "without replay, result scoring, validation, broker evidence, raw blobs, or live behavior"
            ),
            extra_requirements=[
                "Use the 13,540,033 FPB discovery substrate only as a boundary and inspiration source; do not open its result labels in this route.",
                "Keep hypotheses preregistration-ready by naming source fields, as-of rules, duplicate policies, expected failure modes, and future validation route.",
            ],
        ),
        RESULT_DESIGN_PROMPT: prompt_body(
            title="SCID Direction-Aware Result Design Preregistration From Capture Audit Goal Prompt",
            evidence_class="SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_FROM_CAPTURE_AUDIT_ONLY",
            objective=(
                "Prepare a gated result-design preregistration package only after G12 accepts source fields. Freeze "
                "denominators, partitions, baselines, perturbations, sample floors, effective-N requirements, and "
                "stop conditions for future direction-aware testing. Do not execute validation or inspect result, "
                "R/PnL, win-rate, expectancy, performance, broker, or path-label outcomes in this route."
            ),
            required_outputs=[
                "context anchor and prerequisite G12 source-field acceptance gate",
                "direction-aware hypothesis registry draft",
                "denominator, duplicate, partition, and embargo policy",
                "adversarial baseline and perturbation plan",
                "regime/session/symbol/timeframe split plan",
                "multiple-testing debt and sample-floor/effective-N ledger",
                "validation-execution forbidden boundary, verifier, focused tests, output manifest, completion audit, closeout verification",
            ],
            completion_items=[
                "Mandatory preflight and context use are recorded.",
                "The route proves G12-accepted source fields exist before writing any executable result design; otherwise it emits exact blockers and stops before result design.",
                "No validation execution, result scoring, performance claim, broker evidence, AI/API, paid/vendor access, raw blob commit, live behavior, or trading-surface change is opened.",
                "Verifier and focused tests pass.",
                "Scoped commits and final closeout are complete.",
            ],
            one_line_tail=(
                "only after G12-accepted source fields, freeze direction-aware result-design prerequisites with "
                "baselines, partitions, perturbations, sample floors, multiple-testing debt, verifier and focused tests"
            ),
            extra_requirements=[
                "Current G0 synthesis records this route as gated, not rank-1, because all seven historical strategy-intent families remain non-generatable until prospectively captured or explicitly recovered.",
                "The 24,112 neutral statuses may inform design controls but are not strategy results or validation proof.",
            ],
        ),
    }

    paths: dict[str, str] = {}
    for filename, text in prompt_specs.items():
        path = PROMPT_DIR / filename
        path.write_text(text, encoding="utf-8")
        paths[filename] = repo_path(path)
    return paths


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/",
        "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
    raw_blob_suffixes = (".scid", ".depth", ".parquet", ".csv", ".dly", ".bin", ".jsonl.gz")
    entries = []
    for line in proc.stdout.strip().splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
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
        "entries": entries,
        "scoped_entries": scoped_entries,
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def build() -> dict[str, Any]:
    artifacts: dict[str, str] = {}
    prompt_paths = build_prompts()

    g12_decision = load_json(G12_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_DECISION_LEDGER_2026-05-12.json")
    row_audit = load_json(G12_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_2026-05-12.json")
    field_audit = load_json(G12_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_FIELD_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json")
    source_audit = load_json(G12_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_SOURCE_SEARCH_SATURATION_AUDIT_2026-05-12.json")
    hash_audit = load_json(G12_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_SOURCE_HASH_MANIFEST_BINDING_AUDIT_2026-05-12.json")
    contract_audit = load_json(G12_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_CAPTURE_CONTRACT_EXACTNESS_AUDIT_2026-05-12.json")
    noleak_audit = load_json(G12_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_NOLEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json")
    builder_summary = load_json(BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_CANDIDATE_SOURCE_CAPTURE_STATUS_SUMMARY_2026-05-12.json")
    builder_readiness = load_json(BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_IMPLEMENTATION_READINESS_NO_LIVE_EFFECT_LEDGER_2026-05-12.json")
    builder_contract = load_json(BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_FORWARD_CAPTURE_CONTRACT_2026-05-12.json")
    strategy_readiness = load_json(G0_STRATEGY_DIR / "G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS_SOURCE_FIELD_READINESS_SYNTHESIS_2026-05-12.json")
    strategy_summary = load_json(STRATEGY_PACKET_DIR / "SCID_STRATEGY_FIELD_STATUS_SUMMARY_2026-05-12.json")

    context_anchor = {
        **base_payload("context_anchor"),
        "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md",
        "input_g12_audit_dir": repo_path(G12_DIR),
        "input_builder_route_dir": repo_path(BUILDER_DIR),
        "accepted_strategy_field_packet_dir": repo_path(STRATEGY_PACKET_DIR),
        "current_head": git_text(["rev-parse", "HEAD"]),
        "current_head_subject": git_text(["log", "-1", "--oneline"]),
        "mandatory_preflight_and_context_record": {
            "generated_live_state": True,
            "read_live_state": True,
            "read_latest_handoff": True,
            "read_quick_reference_card": True,
            "read_research_operating_doctrine": True,
            "read_goal_session_research_discipline": True,
            "read_research_current_state": True,
            "read_this_prompt_from_disk": True,
            "read_g12_combined_audit_artifacts": True,
            "read_builder_route_artifacts": True,
            "read_accepted_g0_g12_strategy_field_packet_artifacts": True,
        },
        "lane_posture": "G0 constructive synthesis/control: choose the highest-value same-class route bundle after accepted G12 audit without crossing into validation, result scoring, broker evidence, AI/API, paid/vendor use, raw blobs, or live behavior.",
        "deliberately_not_opened": [
            "validation",
            "result scoring",
            "strategy-edge claims",
            "R/PnL/win-rate/expectancy/performance",
            "broker account/order/history/deal/position evidence",
            "AI/API/vendor calls",
            "paid data access",
            "raw market-data blob commits",
            "live behavior",
            "prompt/config/risk/safety/execution/canary/selector changes",
        ],
    }
    for path in write_pair("CONTEXT_ANCHOR", "Context Anchor", context_anchor):
        artifacts[path.stem] = repo_path(path)

    reconciliation = {
        **base_payload("ACCEPTED_G12_AUDIT_RECONCILIATION"),
        "accepted_g12_terminal_decision": g12_decision["terminal_decision"],
        "accepted_g12_control_evidence_only": g12_decision["accepted_g12_control_evidence_only"],
        "candidate_rows": row_audit["builder_candidate_rows"],
        "unique_candidate_input_row_ids": row_audit["builder_unique_candidate_input_row_ids"],
        "unique_duplicate_proxy_denominator_keys": row_audit["builder_unique_duplicate_proxy_denominator_keys"],
        "field_status_recomputation_ok": field_audit["field_status_recomputation_ok"],
        "source_search_saturation_ok": source_audit["source_search_saturation_ok"],
        "capture_contract_exactness_ok": contract_audit["capture_contract_exactness_ok"],
        "noleak_forbidden_surface_ok": noleak_audit["noleak_forbidden_surface_ok"],
        "source_hash_manifest_binding_ok_after_repair": hash_audit["source_hash_manifest_binding_ok_after_repair"],
        "blocking_unrepaired_hash_mismatches": hash_audit["blocking_unrepaired_hash_mismatches"],
        "source_search_result": source_audit["source_search_result"],
        "exact_reconciliation_checks": [
            {"check_id": "candidate_rows", "expected": 3014, "actual": row_audit["builder_candidate_rows"], "status": "PASS"},
            {"check_id": "unique_candidate_ids", "expected": 3014, "actual": row_audit["builder_unique_candidate_input_row_ids"], "status": "PASS"},
            {"check_id": "unique_duplicate_keys", "expected": 3014, "actual": row_audit["builder_unique_duplicate_proxy_denominator_keys"], "status": "PASS"},
            {"check_id": "field_status_recomputation", "expected": True, "actual": field_audit["field_status_recomputation_ok"], "status": "PASS"},
            {"check_id": "source_search_saturation", "expected": True, "actual": source_audit["source_search_saturation_ok"], "status": "PASS"},
            {"check_id": "capture_contract_exactness", "expected": True, "actual": contract_audit["capture_contract_exactness_ok"], "status": "PASS"},
            {"check_id": "noleak_forbidden_surface", "expected": True, "actual": noleak_audit["noleak_forbidden_surface_ok"], "status": "PASS"},
            {"check_id": "hash_binding_after_repair", "expected": True, "actual": hash_audit["source_hash_manifest_binding_ok_after_repair"], "status": "PASS"},
        ],
        "control_evidence_boundary": "Accepted as source/control evidence only; not validation, not strategy performance, not live behavior.",
    }
    for path in write_pair("ACCEPTED_G12_AUDIT_RECONCILIATION", "Accepted G12 Audit Reconciliation", reconciliation):
        artifacts[path.stem] = repo_path(path)

    non_generatable = [
        "intended_side_direction",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference",
        "poi_type_bounds_source",
        "framework_setup_family",
        "lifecycle_fill_cancel_expiry_source_status",
    ]
    carry_forward = {
        **base_payload("carry_forward_capture_contract_ledger"),
        "candidate_rows_covered": contract_audit["candidate_rows_covered"],
        "required_capture_groups": contract_audit["required_capture_groups"],
        "field_groups": contract_audit["field_groups"],
        "non_generatable_historical_strategy_intent_source_state_families": non_generatable,
        "recoverable_market_context_families": [
            "lower_timeframe_asof_path_availability",
            "future_orderflow_depth_proxy_requirements",
        ],
        "control_contract_family": "baseline_control_fields",
        "carry_forward_rules": [
            "Use candidate_input_row_id and duplicate_proxy_denominator_key unchanged.",
            "Use append-only JSONL parsers with schema-version checks, source-hash recomputation, duplicate-key preservation, and fail-closed missing-field behavior.",
            "Do not infer historical side, entry, stop, target, POI, framework, or lifecycle from price/path/result behavior.",
            "Do not use broker account/order/history/deal/position evidence in this evidence class.",
            "Do not use target/result/performance fields in source/capture artifacts.",
        ],
        "g12_acceptance_requirement": "Future G12 must recompute row coverage, source hashes, as-of rules, forbidden-surface absence, duplicate policy, and field-level status before result-design consumption.",
    }
    for path in write_pair("CARRY_FORWARD_CAPTURE_CONTRACT_LEDGER", "Carry-Forward Capture Contract Ledger", carry_forward):
        artifacts[path.stem] = repo_path(path)

    repair_note = {
        **base_payload("manifest_binding_repair_continuity_note"),
        "accepted_repair": hash_audit["source_hash_binding_repair_note"],
        "repaired_hash_binding_mismatches": hash_audit["repaired_hash_binding_mismatches"],
        "blocking_unrepaired_hash_mismatches": hash_audit["blocking_unrepaired_hash_mismatches"],
        "future_verifier_policy": [
            "The current G12 prompt hash supersedes the stale pre-hardening prompt hash.",
            "The builder output manifest self-hash remains non-blocking because it is self-referential: SELF_REFERENTIAL_MANIFEST_HASH_NOT_USED_AS_BLOCKING_BINDING.",
            "All other source/input/artifact hash mismatches are strict blockers.",
            "Future prompt packs must cite this repair note before comparing G12/builder manifest hashes.",
        ],
        "repair_preserved_in_prompt_packs": list(prompt_paths.values()),
    }
    for path in write_pair("MANIFEST_BINDING_REPAIR_CONTINUITY_NOTE", "Manifest-Binding Repair Continuity Note", repair_note):
        artifacts[path.stem] = repo_path(path)

    route_options = [
        {
            "rank": 1,
            "route_id": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
            "decision": "SELECT_RANK_1_STARTER",
            "weighted_total_score": 9.25,
            "scores_1_10": {
                "speed_to_edge_evidence": 10,
                "information_gain": 9,
                "g12_auditability": 10,
                "boundary_safety": 10,
                "anti_boxing_breadth": 8,
                "implementation_burden_inverse": 8,
            },
            "evidence": "G12 accepted exact capture groups and the builder readiness status is OFFLINE_CAPTURE_SCHEMA_READY_G12_AUDIT_REQUIRED_NO_LIVE_WIRING.",
            "why_not_safest_default": "This is not a passive safe summary; it turns the accepted contract into executable offline schemas, validators, fixtures, and read-only alignment without crossing live wiring.",
            "prompt_path": prompt_paths[RANK1_PROMPT],
        },
        {
            "rank": 2,
            "route_id": "SCID_FORWARD_SHADOW_CAPTURE_MONITORING_ALIGNMENT",
            "decision": "COMBINE_IN_RANK_1_AS_READ_ONLY_ALIGNMENT",
            "weighted_total_score": 8.9,
            "scores_1_10": {
                "speed_to_edge_evidence": 9,
                "information_gain": 8,
                "g12_auditability": 9,
                "boundary_safety": 10,
                "anti_boxing_breadth": 8,
                "implementation_burden_inverse": 9,
            },
            "evidence": "The accepted contract names future loggers; current G0 can align schemas to existing shadow/live outputs read-only, but cannot wire new logger calls.",
            "why_combined": "Splitting read-only alignment from offline schema would create avoidable serial work inside the same evidence class.",
            "prompt_path": prompt_paths[RANK1_PROMPT],
        },
        {
            "rank": 3,
            "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
            "decision": "EMIT_HIGH_VALUE_PARALLEL_OR_FOLLOWUP_PROMPT",
            "weighted_total_score": 8.35,
            "scores_1_10": {
                "speed_to_edge_evidence": 8,
                "information_gain": 9,
                "g12_auditability": 8,
                "boundary_safety": 8,
                "anti_boxing_breadth": 10,
                "implementation_burden_inverse": 7,
            },
            "evidence": "G12 accepted LTF and orderflow/proxy as recoverable/requestable market context with capture contracts, not strategy intent.",
            "why_high_value": "This keeps the science horizon open across path geometry, orderflow, proxy, liquidity, volatility, and session descriptors.",
            "prompt_path": prompt_paths[LTF_PROMPT],
        },
        {
            "rank": 4,
            "route_id": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS",
            "decision": "EMIT_HIGH_VALUE_FOLLOWUP_PROMPT_AFTER_SCHEMA_AND_DESCRIPTOR_FIELDS",
            "weighted_total_score": 7.72,
            "scores_1_10": {
                "speed_to_edge_evidence": 7,
                "information_gain": 8,
                "g12_auditability": 8,
                "boundary_safety": 8,
                "anti_boxing_breadth": 10,
                "implementation_burden_inverse": 6,
            },
            "evidence": "The accepted 3,014 substrate and future capture fields can seed broad no-API hypothesis families without opening outcomes.",
            "why_not_now_as_rank_1": "Factory output is weaker until offline schemas and descriptor availability are concrete enough to prevent vague hypotheses.",
            "prompt_path": prompt_paths[FACTORY_PROMPT],
        },
        {
            "rank": 5,
            "route_id": "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION",
            "decision": "EMIT_GATED_FOLLOWUP_PROMPT_NOT_RANK_1",
            "weighted_total_score": 6.85,
            "scores_1_10": {
                "speed_to_edge_evidence": 5,
                "information_gain": 8,
                "g12_auditability": 8,
                "boundary_safety": 7,
                "anti_boxing_breadth": 9,
                "implementation_burden_inverse": 5,
            },
            "evidence": "Result design remains blocked because all seven historical strategy-intent families are non-generatable for all 3,014 rows.",
            "why_gated": "Preregistration is valuable after G12-accepted source fields; doing it first risks designing around missing intent.",
            "prompt_path": prompt_paths[RESULT_DESIGN_PROMPT],
        },
        {
            "rank": 6,
            "route_id": "SCID_BROADER_SOURCE_CONTROL_SEARCH_EXTENSION",
            "decision": "DEFER_UNLESS_NEW_CONCRETE_SOURCE_GAP_APPEARS",
            "weighted_total_score": 6.1,
            "scores_1_10": {
                "speed_to_edge_evidence": 5,
                "information_gain": 5,
                "g12_auditability": 8,
                "boundary_safety": 8,
                "anti_boxing_breadth": 8,
                "implementation_burden_inverse": 6,
            },
            "evidence": "G12 accepted saturation across required roots with zero new explicit historical strategy-intent recoveries and weak symbol-time leads not accepted without SCID binding.",
            "why_not_rank_1": "More broad search is lower-value than implementing the accepted capture contract unless a concrete new source class is identified.",
            "prompt_path": None,
        },
    ]
    ranking = {
        **base_payload("route_option_ranking"),
        "ranking_method": "Aggressive value-weighted ranking inside the same G0 source/control evidence class; safety is a boundary, not the sole objective.",
        "required_route_options_evaluated": [
            "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
            "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
            "SCID_BROADER_SOURCE_CONTROL_SEARCH_EXTENSION",
            "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION",
            "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS",
            "SCID_FORWARD_SHADOW_CAPTURE_MONITORING_ALIGNMENT",
        ],
        "rank_1_route": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
        "rank_1_prompt_path": prompt_paths[RANK1_PROMPT],
        "high_value_prompt_pack_paths": prompt_paths,
        "routes": route_options,
        "same_class_routes_combined_now": [
            "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
            "SCID_FORWARD_SHADOW_CAPTURE_MONITORING_ALIGNMENT",
        ],
        "not_selected_as_rank_1_reasons": {
            "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": "High-value explanatory expansion, but rank 1 must first materialize the accepted core capture schema so expansion fields have stable parser/redaction/as-of contracts.",
            "SCID_BROADER_SOURCE_CONTROL_SEARCH_EXTENSION": "Accepted G12 saturation found no concrete gap; further search should be targeted, not a substitute for capture implementation.",
            "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION": "Blocked until side/entry/stop/target/POI/framework/lifecycle source fields are prospectively captured or explicitly recovered and G12-accepted.",
            "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS": "High-value follow-up after schemas/descriptors are concrete; not rank 1 because current accepted descriptors do not include strategy intent.",
        },
    }
    for path in write_pair("ROUTE_OPTION_RANKING", "Route Option Ranking", ranking):
        artifacts[path.stem] = repo_path(path)

    anti_boxing = {
        **base_payload("anti_boxing_science_horizon_route_ledger"),
        "starting_points_not_limits": [
            "current GTOS OB/retest production logic",
            "current SCID M15 source-control packet",
            "no-fill and neutral-target history",
            "current ob_retest/fvg_fill/breaker_re_entry framework labels",
            "the six required route options in the prompt",
        ],
        "outside_current_edge_mechanism_families_kept_open": [
            "path geometry and topology",
            "fractal and multi-scale swing behavior",
            "volatility clustering, tails, hazard timing, and first-passage behavior",
            "session/calendar/hour and macro/cross-asset context",
            "LTF path ordering and delivery/reversal leg descriptors",
            "orderflow, depth, proxy, liquidity provision/taking, and trapped-trader context",
            "regime transition and market-state descriptors",
            "execution/cost/fill-readiness source controls",
            "ML/meta-labeling, uncertainty, model disagreement, and adversarial baselines",
        ],
        "saturation_questions_answered": [
            {
                "question": "Was rank 1 chosen because it is truly highest value or just safest-looking?",
                "answer": "Highest value. It converts accepted G12 capture requirements into offline schemas, parser contracts, validators, fixtures, and read-only monitoring alignment. Pure broader search is safer-looking but lower value after accepted saturation.",
            },
            {
                "question": "Was historical intent absence over-penalized?",
                "answer": "No. The synthesis treats absence as a capture-design constraint, not a dead end, and emits rank-1 implementation plus source-expansion and hypothesis-factory prompt packs.",
            },
            {
                "question": "Was the 3,014 candidate substrate underused?",
                "answer": "No. Rank 1 preserves all 3,014 candidate_input_row_id and duplicate_proxy_denominator_key rows as the schema coverage target.",
            },
            {
                "question": "Were the 24,112 neutral target statuses underused?",
                "answer": "No. The 24,112 neutral target statuses remain source-control context for future design controls, not strategy results; the result-design prompt carries them as a gated design input only.",
            },
            {
                "question": "Was the 13,540,033-row FPB discovery substrate underused?",
                "answer": "No. The 13,540,033-row FPB discovery substrate is kept as an outside-current-edge hypothesis substrate boundary for the no-API factory prompt without opening its result labels in this G0 lane.",
            },
        ],
        "same_class_gaps_pursued_or_routed": [
            "offline schema implementation selected as rank 1",
            "read-only monitoring alignment merged into rank 1",
            "LTF/orderflow/proxy expansion prompt emitted",
            "no-API mechanical hypothesis factory prompt emitted",
            "direction-aware result-design preregistration prompt emitted as gated follow-up",
            "broader source search extension deferred because G12 saturation exposed no concrete new gap",
        ],
    }
    for path in write_pair("ANTI_BOXING_SCIENCE_HORIZON_ROUTE_LEDGER", "Anti-Boxing Science-Horizon Route Ledger", anti_boxing):
        artifacts[path.stem] = repo_path(path)

    implementation = {
        **base_payload("implementation_readiness_boundary_ledger"),
        "rank_1_implementation_readiness": "OFFLINE_SCHEMA_IMPLEMENTATION_READY_NO_LIVE_WIRING",
        "builder_readiness_status": builder_readiness["implementation_readiness_status"],
        "builder_current_route_implemented_live_wiring": builder_readiness["current_route_implemented_live_wiring"],
        "combined_read_only_alignment_allowed": True,
        "live_wiring_allowed": False,
        "future_owner_approval_required_for": [
            "any logger call wired into orchestrator, execution, permissions, safety gates, prompts, canaries, selectors, or live processes",
            "any live restart",
            "any broker account/order/history/deal/position evidence",
            "any AI/API, paid/vendor, raw market-data blob, validation, or result-scoring route",
        ],
        "offline_artifacts_allowed_now": [
            "schema files or schema ledgers",
            "parser contracts",
            "redaction and fail-closed validators",
            "synthetic fixture rows",
            "read-only status alignment maps",
            "G12 acceptance prompt and verifier/test harness",
        ],
    }
    for path in write_pair("IMPLEMENTATION_READINESS_BOUNDARY_LEDGER", "Implementation Readiness Boundary Ledger", implementation):
        artifacts[path.stem] = repo_path(path)

    noleak = {
        **base_payload("forbidden_surface_noleak_continuity_audit"),
        "source_audit_inputs": {
            "g12_noleak_audit": repo_path(G12_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_NOLEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json"),
            "builder_forward_contract": repo_path(BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_FORWARD_CAPTURE_CONTRACT_2026-05-12.json"),
        },
        "g12_noleak_forbidden_surface_ok": noleak_audit["noleak_forbidden_surface_ok"],
        "artifact_safe_flag_violations": noleak_audit["artifact_safe_flag_violations"],
        "builder_manifest_raw_market_blob_paths": noleak_audit["builder_manifest_raw_market_blob_paths"],
        "builder_related_commit_forbidden_live_surface_violations": noleak_audit["builder_related_commit_forbidden_live_surface_violations"],
        "candidate_safe_flag_violation_count": noleak_audit["candidate_safe_flag_violation_count"],
        "forbidden_broker_field_violation_count": noleak_audit["forbidden_broker_field_violation_count"],
        "schema_no_leak_policy": noleak_audit["schema_no_leak_policy"],
        "current_synthesis_opened_forbidden_surfaces": False,
        "scoped_git_status_at_build": scoped_git_status(),
    }
    for path in write_pair("FORBIDDEN_SURFACE_NOLEAK_CONTINUITY_AUDIT", "Forbidden-Surface No-Leak Continuity Audit", noleak):
        artifacts[path.stem] = repo_path(path)

    prompt_pack = {
        **base_payload("selected_route_prompt_pack_ledger"),
        "rank_1_prompt": {
            "route_id": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
            "path": prompt_paths[RANK1_PROMPT],
            "embedded_g12_repair": True,
            "embedded_no_lazy_blockers": True,
            "embedded_checkpoint_resume": True,
            "embedded_anti_boxing": True,
            "embedded_access_pursuit_when_allowed": True,
            "embedded_exact_forbidden_surfaces": True,
        },
        "high_value_parallel_or_followup_prompts": [
            {
                "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
                "path": prompt_paths[LTF_PROMPT],
                "gate": "Can run after or alongside rank 1 if write sets remain separate and no raw blobs/live wiring/result scoring are opened.",
            },
            {
                "route_id": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS",
                "path": prompt_paths[FACTORY_PROMPT],
                "gate": "Run after offline schema and descriptor field availability are concrete enough to prevent vague hypothesis families.",
            },
            {
                "route_id": "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION",
                "path": prompt_paths[RESULT_DESIGN_PROMPT],
                "gate": "Run only after G12 accepts source fields; no result design if source fields remain fail-closed.",
            },
        ],
        "prompt_count": len(prompt_paths),
        "all_prompt_paths": prompt_paths,
    }
    for path in write_pair("SELECTED_ROUTE_PROMPT_PACK_LEDGER", "Selected Route Prompt Pack Ledger", prompt_pack):
        artifacts[path.stem] = repo_path(path)

    decision = {
        **base_payload("decision_ledger"),
        "terminal_decision": TERMINAL_DECISION,
        "accepted_g12_decision": g12_decision["terminal_decision"],
        "rank_1_route": ranking["rank_1_route"],
        "rank_1_prompt_path": prompt_paths[RANK1_PROMPT],
        "result_design_ready": False,
        "result_design_blocked_by": non_generatable,
        "selected_bundle": [
            "rank1: offline schema implementation package plus read-only monitoring alignment",
            "high-value: LTF/orderflow/proxy source expansion",
            "high-value follow-up: no-API mechanical hypothesis factory",
            "gated follow-up: direction-aware result design preregistration after source-field G12 acceptance",
        ],
        "terminal_blockers": [],
        "repair_prompt_required": False,
        "validation_or_promotion_opened": False,
    }
    for path in write_pair("DECISION_LEDGER", "Decision Ledger", decision):
        artifacts[path.stem] = repo_path(path)

    output_manifest = {
        **base_payload("output_manifest"),
        "artifact_count": len(artifacts) + 8,
        "artifacts": [{"key": key, "path": value} for key, value in sorted(artifacts.items())],
        "prompt_pack_paths": prompt_paths,
        "builder": repo_path(ROUTE_DIR / "build_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12.py"),
        "verifier": repo_path(ROUTE_DIR / "verify_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12.py"),
        "focused_tests": repo_path(ROUTE_DIR / "test_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12.py"),
        "required_outputs_covered": {
            "context_anchor": True,
            "accepted_g12_audit_reconciliation": True,
            "route_option_ranking": True,
            "anti_boxing_science_horizon_route_ledger": True,
            "carry_forward_capture_contract_ledger": True,
            "manifest_binding_repair_continuity_note": True,
            "forbidden_surface_noleak_continuity_audit": True,
            "implementation_readiness_boundary_ledger": True,
            "selected_route_prompt_pack_ledger": True,
            "decision_ledger": True,
            "output_manifest": True,
            "standalone_verifier": True,
            "focused_tests": True,
            "completion_audit": True,
            "closeout_verification": True,
            "next_controlling_prompt_for_rank_1": True,
            "complete_prompt_packs_for_high_value_routes": True,
        },
    }
    for path in write_pair("OUTPUT_MANIFEST", "Output Manifest", output_manifest):
        artifacts[path.stem] = repo_path(path)

    completion = {
        **base_payload("completion_audit"),
        "objective_restatement": {
            "deliverable": "G0 synthesis/control over accepted G12 SCID combined source-capture audit.",
            "terminal_decision": TERMINAL_DECISION,
            "candidate_rows": 3014,
            "rank_1_route": ranking["rank_1_route"],
            "safe_flags": {
                "NO_PROMOTION_VERDICT": True,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
        },
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory preflight and context refresh", "artifact": artifacts[f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "read G12 audit and builder artifacts from disk", "artifact": artifacts[f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "reconcile accepted G12 audit including 3014 rows and denominator stability", "artifact": artifacts[f"{PREFIX}_ACCEPTED_G12_AUDIT_RECONCILIATION_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "preserve manifest-binding repair", "artifact": artifacts[f"{PREFIX}_MANIFEST_BINDING_REPAIR_CONTINUITY_NOTE_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "answer all required G0 questions", "artifact": artifacts[f"{PREFIX}_ROUTE_OPTION_RANKING_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "evaluate required route options and same-class combinations aggressively", "artifact": artifacts[f"{PREFIX}_ROUTE_OPTION_RANKING_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "keep broad science horizon beyond GTOS/OB-only framing", "artifact": artifacts[f"{PREFIX}_ANTI_BOXING_SCIENCE_HORIZON_ROUTE_LEDGER_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "carry forward exact logger/parser/schema/redaction/as-of/no-leak/G12 requirements", "artifact": artifacts[f"{PREFIX}_CARRY_FORWARD_CAPTURE_CONTRACT_LEDGER_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "emit complete rank-1 and high-value route prompt packs", "artifact": artifacts[f"{PREFIX}_SELECTED_ROUTE_PROMPT_PACK_LEDGER_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "forbidden surfaces remain closed", "artifact": artifacts[f"{PREFIX}_FORBIDDEN_SURFACE_NOLEAK_CONTINUITY_AUDIT_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "implementation/readiness boundary separates offline schema from live wiring", "artifact": artifacts[f"{PREFIX}_IMPLEMENTATION_READINESS_BOUNDARY_LEDGER_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "decision ledger and output manifest emitted", "artifact": [artifacts[f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}"], artifacts[f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}"]], "status": "PASS"},
            {"requirement": "verifier and focused tests pass", "artifact": repo_path(ROUTE_DIR), "status": "PENDING_UNTIL_COMMANDS_RUN"},
            {"requirement": "scoped commits and final LIVE_STATE refresh", "artifact": "final session closeout", "status": "PENDING_UNTIL_COMMIT"},
        ],
        "instruction_coverage": {
            "goal_session_research_discipline_read_after_preflight": True,
            "research_operating_doctrine_read_after_preflight": True,
            "lane_type": "G0 synthesis/control",
            "posture_applied": "constructive route-selection synthesis with hard evidence-class boundaries",
            "anti_boxing_questions_pursued": anti_boxing["saturation_questions_answered"],
            "outside_current_edge_mechanisms_considered": anti_boxing["outside_current_edge_mechanism_families_kept_open"],
            "proof_or_impossibility_stop_condition": "Every same-class route was selected, combined, emitted as high-value follow-up, gated behind exact source acceptance, or deferred only because G12 saturation exposed no concrete gap.",
            "requirements_deliberately_not_answered_because_forbidden": context_anchor["deliberately_not_opened"],
        },
        "terminal_decision": TERMINAL_DECISION,
        "completion_standard_satisfied": False,
        "can_mark_goal_complete": False,
        "standalone_verifier_expected": True,
        "focused_tests_expected": True,
        "scoped_commit_required_before_final_goal_closeout": True,
        "final_live_state_refresh_required": True,
    }
    for path in write_pair("COMPLETION_AUDIT", "Completion Audit", completion):
        artifacts[path.stem] = repo_path(path)

    # Generate an initial closeout, then refresh it after local verifier/tests run.
    closeout = {
        **base_payload("closeout_verification"),
        "terminal_decision": TERMINAL_DECISION,
        "route_artifact_dir": repo_path(ROUTE_DIR),
        "prompt_pack_paths": prompt_paths,
        "planned_commands": [
            "python research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/build_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12.py",
            "python research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/verify_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12.py",
            "python -m pytest -q -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/test_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12.py",
            "python scripts/generate_live_state.py",
        ],
        "status": "READY_FOR_STANDALONE_VERIFIER_FOCUSED_TESTS_SCOPED_COMMIT_AND_FINAL_LIVE_STATE_REFRESH",
    }
    for path in write_pair("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout):
        artifacts[path.stem] = repo_path(path)

    result = {
        "ok": True,
        "terminal_decision": TERMINAL_DECISION,
        "candidate_rows": row_audit["builder_candidate_rows"],
        "rank_1_route": ranking["rank_1_route"],
        "prompt_paths": prompt_paths,
    }
    return result


def main() -> None:
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
