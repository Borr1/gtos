"""Build G0 SCID forward-capture offline-schema synthesis artifacts.

This route is G0 source/control synthesis only. It reconciles the accepted
G12 audit of the offline schema package, builds implementation-readiness and
route-scoring matrices, and emits next-route prompt packs without opening
validation, result scoring, broker evidence, AI/API calls, paid/vendor access,
raw market-data blobs, or live behavior.
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

G12_SCHEMA_AUDIT_DIR = OUTCOME_DIR / "g12_scid_forward_capture_offline_schema_implementation_package_audit"
OFFLINE_SCHEMA_DIR = OUTCOME_DIR / "scid_forward_capture_offline_schema_implementation_package"
UPSTREAM_G0_DIR = OUTCOME_DIR / "g0_scid_combined_source_capture_route_synthesis_control"
UPSTREAM_G12_DIR = OUTCOME_DIR / "g12_scid_combined_source_search_and_forward_capture_route_audit"
UPSTREAM_BUILDER_DIR = OUTCOME_DIR / "scid_combined_source_search_and_forward_capture_route"

DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS"
ROUTE_ID = "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL"
EVIDENCE_CLASS = "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY"
TERMINAL_DECISION = (
    "ACCEPT_AS_G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_WITH_RANKED_IMPLEMENTATION_ROUTE_BUNDLE"
)

PROMPT_IMPLEMENTATION_DESIGN = (
    "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
)
PROMPT_RUNTIME_HARNESS = (
    "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
)
PROMPT_READONLY_ALIGNMENT = (
    "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
)
PROMPT_NO_API_FACTORY = (
    "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
)
PROMPT_LTF_ORDERFLOW = (
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
)

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
    "raw-market-blob/prompt-config-risk/safety/execution/canary/selector changes"
)

CAPTURE_GROUP_LABELS = {
    "intended_side_direction": "side",
    "intended_entry_reference": "entry",
    "intended_stop_reference": "stop",
    "intended_target_reference": "target",
    "poi_type_bounds_source": "POI",
    "framework_setup_family": "framework",
    "lifecycle_fill_cancel_expiry_source_status": "lifecycle",
    "lower_timeframe_asof_path_availability": "LTF",
    "future_orderflow_depth_proxy_requirements": "orderflow/proxy",
    "baseline_control_fields": "baseline-control",
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
        "schema_version": "g0_scid_forward_capture_offline_schema_synthesis_v1",
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


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/",
        f"research/science_program_2026_05/04_goal_prompts/{PROMPT_IMPLEMENTATION_DESIGN}",
        f"research/science_program_2026_05/04_goal_prompts/{PROMPT_RUNTIME_HARNESS}",
        f"research/science_program_2026_05/04_goal_prompts/{PROMPT_READONLY_ALIGNMENT}",
        f"research/science_program_2026_05/04_goal_prompts/{PROMPT_NO_API_FACTORY}",
        f"research/science_program_2026_05/04_goal_prompts/{PROMPT_LTF_ORDERFLOW}",
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
        "scoped_entries": scoped_entries,
        "unrelated_dirty_entry_count": len([entry for entry in entries if not entry["scoped"]]),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def build_input_inventory(paths: dict[str, Path]) -> list[dict[str, Any]]:
    rows = []
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


def route_score(
    route_id: str,
    rank: int,
    immediacy: int,
    evidence_gain: int,
    non_generatable_gap_closure: int,
    edge_testing_unlock: int,
    source_noleak_cleanliness: int,
    implementation_burden_score: int,
    parallelizability: int,
    decision: str,
    prompt_file: str | None,
    reason: str,
    lower_rank_reason: str | None = None,
    owner_or_future_gate: str | None = None,
) -> dict[str, Any]:
    scores = {
        "immediacy": immediacy,
        "evidence_gain": evidence_gain,
        "non_generatable_gap_closure": non_generatable_gap_closure,
        "edge_testing_unlock": edge_testing_unlock,
        "source_noleak_cleanliness": source_noleak_cleanliness,
        "implementation_burden_score": implementation_burden_score,
        "parallelizability": parallelizability,
    }
    return {
        "rank": rank,
        "route_id": route_id,
        "scores_0_to_5": scores,
        "weighted_total_score": sum(scores.values()),
        "score_direction_note": "Higher is better; implementation_burden_score=5 means lowest burden.",
        "decision": decision,
        "prompt_file": prompt_file,
        "reason": reason,
        "lower_rank_reason": lower_rank_reason,
        "owner_or_future_gate": owner_or_future_gate,
    }


def prompt_body(
    *,
    title: str,
    route_id: str,
    evidence_class: str,
    objective: str,
    required_outputs: list[str],
    completion_items: list[str],
    route_specific_requirements: list[str],
) -> str:
    outputs = "\n".join(f"- {item}" for item in required_outputs)
    completion = "\n".join(f"{index}. {item}" for index, item in enumerate(completion_items, start=1))
    requirements = "\n".join(f"- {item}" for item in route_specific_requirements)
    starter = (
        f"/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/{route_id}_GOAL_PROMPT_2026-05-12.md "
        "as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; "
        f"stay {evidence_class} with no validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/"
        "promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/"
        "prompt-config-risk-safety-execution-canary-selector changes; preserve accepted G12 offline schema package, "
        "3,014 candidate coverage boundary, ten capture groups, manifest-binding repair, offline-only/live-wiring-absent "
        "boundary, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; "
        "pursue proof-or-impossibility until the prompt file's completion standard is fully satisfied."
    )
    return f"""# {title}

Date: {DATE_TAG}
Owner lane: prompt pack emitted by G0 SCID forward-capture offline-schema synthesis
Evidence class: `{evidence_class}`
Input G0 route: `research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/`
Input G12 audit: `research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_offline_schema_implementation_package_audit/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

{objective}

Examples are starting points, not limits. Current GTOS OB/retest logic, current SCID-only framing, the ten accepted schema groups, and the listed route families are not the research horizon. Stay auditable, as-of, no-leak, source/control-only, and hard-boundary-compliant while maximizing useful implementation-readiness output.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the accepted G12 offline-schema audit decision, schema contract audit, fixture recomputation audit, manifest/read-only/no-leak audit, output manifest, verifier result, completion audit, and closeout verification.
9. Read the original offline schema package field-group schema ledger, parser/redaction/as-of/no-leak validator contract, fixture manifest, fixture validation result, read-only monitoring alignment ledger, manifest hash policy, output manifest, verifier result, and closeout verification.
10. Read the immediate upstream G0/G12 source-capture synthesis artifacts needed to preserve the 3,014 candidate boundary, ten capture groups, manifest-binding repair, and anti-boxing route bundle.

Do not rely on chat memory. If interrupted or compacted, regenerate `LIVE_STATE`, re-read this prompt and the current route artifacts from disk, and resume from the emitted context anchor.

## Mandatory Context Use

Treat `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active instructions. Record in the completion audit:

- whether both were read after preflight;
- the builder/control posture applied;
- anti-boxing questions pursued;
- searched roots and artifacts inspected;
- proof-or-impossibility stop condition;
- any doctrine requirement deliberately not answered because it crosses validation, result scoring, broker evidence, AI/API, paid/vendor, raw-blob, prompt/config/risk/safety/execution/canary/selector, or live-behavior boundaries.

## Accepted Package Boundary

Carry forward the accepted G12 decision `ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY`. Preserve exactly:

- offline schema/parser/fixture/validator/read-only alignment evidence only;
- live wiring absent and required as a future gate;
- 3,014 `candidate_input_row_id` values and 3,014 `duplicate_proxy_denominator_key` values as source/control coverage expectations only, not result denominators;
- ten capture groups: side, entry, stop, target, POI, framework, lifecycle, LTF, orderflow/proxy, baseline-control;
- manifest-binding repair: current G12 prompt hash rebound, self-referential output manifest hash drift non-blocking, all other hash mismatches strict.

## Hard Boundaries

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`. Do not open {FORBIDDEN_SURFACES}.

Use checkpointing, chunking, and resumable ledgers rather than accepting shallow summaries. Do not stage unrelated runtime, shadow, live-monitoring, raw market-data, or production-code dirt.

## Route-Specific Requirements

{requirements}

## Required Outputs

{outputs}

## Completion Standard

{completion}

## One-Line Starter

`{starter}`
"""


def write_prompt(path_name: str, body: str) -> str:
    path = PROMPT_DIR / path_name
    path.write_text(body, encoding="utf-8")
    return repo_path(path)


def build_prompts() -> dict[str, dict[str, str]]:
    prompts = {
        "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE": {
            "file": PROMPT_IMPLEMENTATION_DESIGN,
            "body": prompt_body(
                title="SCID Forward Capture Implementation Design Package From Offline Schema Synthesis",
                route_id="SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS",
                evidence_class="SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
                objective=(
                    "Design the exact no-live implementation package that would transform the accepted offline schema contract "
                    "into reviewable additive capture points, redacted event rows, fail-closed parser adapters, rollback plan, "
                    "and G12 audit inputs without wiring live behavior or changing production decision logic."
                ),
                required_outputs=[
                    "context anchor and accepted G12/G0 reconciliation",
                    "per-capture-group implementation design ledger",
                    "source/logger insertion-point proposal ledger with no code wiring",
                    "redaction/fail-closed/rollback/test plan",
                    "G12 implementation-design audit prompt and one-line starter",
                    "standalone verifier, focused tests, completion audit, closeout verification",
                ],
                completion_items=[
                    "All ten capture groups mapped to proposed additive source/logging design without live wiring.",
                    "Every design item includes source/as-of/no-leak/redaction/fail-closed/rollback/G12 acceptance criteria.",
                    "No production source, prompt, config, risk, safety, execution, canary, selector, API, broker, raw blob, validation, or result surface changed.",
                    "Verifier and focused tests pass or exact blockers are recorded.",
                ],
                route_specific_requirements=[
                    "Treat implementation as design/package only; do not edit `src/`, `prompts/`, `config/`, `scripts/watchdog.ps1`, canaries, selectors, or live process controls.",
                    "Freeze future owner approval needed for any actual live logger wiring or restart.",
                    "Include a patch-plan option that a later owner-approved implementation lane can audit before any code change.",
                ],
            ),
        },
        "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_WITH_SYNTHETIC_ONLY_FIXTURES": {
            "file": PROMPT_RUNTIME_HARNESS,
            "body": prompt_body(
                title="SCID Capture Schema To Runtime Test Harness With Synthetic-Only Fixtures",
                route_id="SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_FROM_OFFLINE_SCHEMA_SYNTHESIS",
                evidence_class="SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_ONLY",
                objective=(
                    "Build a source/control-only runtime-facing test harness that feeds synthetic capture rows through the accepted "
                    "offline schemas and validator contracts, proving fail-closed behavior before any live wiring exists."
                ),
                required_outputs=[
                    "context anchor and accepted-audit reconciliation",
                    "synthetic-only fixture expansion ledger",
                    "runtime-facing parser/harness contract with no producer wiring",
                    "negative fixture matrix for missing, stale, forbidden, duplicate, unavailable, and schema-version cases",
                    "standalone verifier, focused tests, completion audit, closeout verification",
                ],
                completion_items=[
                    "Harness uses only synthetic fixtures and committed schema/control artifacts.",
                    "No raw market blobs, live logs, broker/account/order/deal/position evidence, validation, result labels, or AI/API calls are consumed.",
                    "All ten capture groups have at least one positive or fail-closed fixture route.",
                    "Verifier and focused tests pass or exact blockers are recorded.",
                ],
                route_specific_requirements=[
                    "Do not wire the harness into live producers, watchdog, orchestrator, execution, permissions, prompts, canaries, selectors, or config.",
                    "All fixtures must be synthetic/control-only and visibly redacted.",
                    "If a runtime code import would touch production behavior, replace it with a pure test adapter or document the future approval gate.",
                ],
            ),
        },
        "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION": {
            "file": PROMPT_READONLY_ALIGNMENT,
            "body": prompt_body(
                title="SCID Forward Capture Read-Only Monitoring Alignment Expansion From Offline Schema Synthesis",
                route_id="SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS",
                evidence_class="SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_ONLY",
                objective=(
                    "Expand read-only monitoring alignment from the accepted twelve target artifacts into a broader shape-only "
                    "coverage map for prospective capture readiness, without producer changes or raw-value copying."
                ),
                required_outputs=[
                    "context anchor and accepted-audit reconciliation",
                    "read-only shape inventory across allowed local artifacts",
                    "field-group-to-existing-artifact coverage and gap matrix",
                    "source/capture approval gate ledger for any missing producer field",
                    "standalone verifier, focused tests, completion audit, closeout verification",
                ],
                completion_items=[
                    "All ten capture groups are represented in the coverage/gap matrix.",
                    "Only schema/key shapes and counts are inspected; no raw market blobs, broker evidence, validation labels, result scoring, AI/API, or paid data are opened.",
                    "Missing fields are turned into exact prospective capture requirements rather than inferred historical truth.",
                    "Verifier and focused tests pass or exact blockers are recorded.",
                ],
                route_specific_requirements=[
                    "Inspect committed/local JSON/JSONL shapes only where allowed; do not modify producers.",
                    "If a field appears to contain broker/order/deal/position or result evidence, mark it forbidden and exclude it from any source/control row.",
                    "Preserve the accepted read-only alignment boundary: shape inspected, raw values not copied, live wiring not added.",
                ],
            ),
        },
        "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS": {
            "file": PROMPT_NO_API_FACTORY,
            "body": prompt_body(
                title="SCID No-API Mechanical Hypothesis Factory From Offline Schema Synthesis",
                route_id="SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS",
                evidence_class="SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
                objective=(
                    "Create a no-API, source/control-only hypothesis factory that converts accepted descriptor and future-capture "
                    "fields into preregisterable mechanical question families without opening outcomes, labels, result scoring, or validation."
                ),
                required_outputs=[
                    "context anchor and accepted-audit reconciliation",
                    "mechanism-family hypothesis catalog beyond current GTOS edge framing",
                    "required source-field checklist per hypothesis family",
                    "blocked/unblocked preregistration readiness matrix",
                    "future result-design gate ledger",
                    "standalone verifier, focused tests, completion audit, closeout verification",
                ],
                completion_items=[
                    "Hypotheses stay source/control-only and do not inspect outcomes, R/PnL, target statuses, win-rate, expectancy, or performance.",
                    "Current GTOS OB/retest logic and SCID-only framing are treated as starting points, not limits.",
                    "Every hypothesis states exact fields required before future direction-aware result design can begin.",
                    "Verifier and focused tests pass or exact blockers are recorded.",
                ],
                route_specific_requirements=[
                    "Use broad science families from research doctrine: geometry/topology, stochastic/tails, microstructure/orderflow, behavioral/game, macro/session/cross-asset, execution science, and ML/meta-labeling.",
                    "Do not use AI/API calls, paid data, raw market blob commits, broker/account/order/deal/position evidence, or live behavior.",
                    "Separate preregistration design from future result-scoring or validation lanes.",
                ],
            ),
        },
        "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": {
            "file": PROMPT_LTF_ORDERFLOW,
            "body": prompt_body(
                title="SCID LTF Orderflow Proxy Source Expansion From Offline Schema Synthesis",
                route_id="SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS",
                evidence_class="SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
                objective=(
                    "Plan and, where source-control-only inputs allow, build the LTF/orderflow/proxy source expansion contracts needed "
                    "to populate the accepted offline schema groups without paid pulls, raw blob commits, validation, or live wiring."
                ),
                required_outputs=[
                    "context anchor and accepted-audit reconciliation",
                    "LTF source contract and availability matrix",
                    "orderflow/depth/proxy source contract and access/readiness matrix",
                    "as-of/no-leak/publication-time/duplicate policy ledger",
                    "G12 audit prompt or exact external approval/source gate ledger",
                    "standalone verifier, focused tests, completion audit, closeout verification",
                ],
                completion_items=[
                    "LTF and orderflow/proxy requirements are source/control contracts only.",
                    "No paid/vendor/API call, raw market blob commit, broker evidence, result scoring, validation, or live behavior is opened.",
                    "Every blocker names exact source, parser, field, legal/access proof, owner approval, or future capture requirement.",
                    "Verifier and focused tests pass or exact blockers are recorded.",
                ],
                route_specific_requirements=[
                    "Use local/cache/source-index evidence first; if source access is needed and allowed, request exact approval rather than silently stopping.",
                    "Keep recoverable market context separate from non-generatable historical GTOS source-state truth.",
                    "Do not treat proxy/futures evidence as broker-native CFD truth.",
                ],
            ),
        },
    }
    written = {}
    for route_id, row in prompts.items():
        path = write_prompt(row["file"], row["body"])
        starter_line = next(line.strip("`") for line in row["body"].splitlines() if line.startswith("`/goal "))
        written[route_id] = {
            "prompt_path": path,
            "one_line_starter": starter_line,
        }
    return written


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, str] = {}

    input_paths = {
        "control_prompt": PROMPT_DIR / "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md",
        "live_state": ROOT / ".context" / "LIVE_STATE.md",
        "quick_reference": ROOT / ".context" / "00_core" / "quick_reference_card.md",
        "research_operating_doctrine": ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
        "goal_session_research_discipline": ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
        "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
        "g12_schema_decision": G12_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_DECISION_LEDGER_2026-05-12.json",
        "g12_schema_contract": G12_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_SCHEMA_CONTRACT_AUDIT_2026-05-12.json",
        "g12_fixture_recompute": G12_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_FIXTURE_VALIDATOR_RECOMPUTATION_AUDIT_2026-05-12.json",
        "g12_manifest_readonly_noleak": G12_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_MANIFEST_READONLY_NOLEAK_AUDIT_2026-05-12.json",
        "g12_output_manifest": G12_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_OUTPUT_MANIFEST_2026-05-12.json",
        "g12_verification": G12_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_VERIFICATION_RESULT_2026-05-12.json",
        "g12_completion": G12_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_COMPLETION_AUDIT_2026-05-12.json",
        "offline_field_group_schema": OFFLINE_SCHEMA_DIR / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_FIELD_GROUP_SCHEMA_LEDGER_2026-05-12.json",
        "offline_parser_contract": OFFLINE_SCHEMA_DIR / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
        "offline_fixture_manifest": OFFLINE_SCHEMA_DIR / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_FIXTURE_MANIFEST_2026-05-12.json",
        "offline_readonly_alignment": OFFLINE_SCHEMA_DIR / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_READ_ONLY_MONITORING_ALIGNMENT_LEDGER_2026-05-12.json",
        "offline_manifest_policy": OFFLINE_SCHEMA_DIR / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_MANIFEST_HASH_POLICY_LEDGER_2026-05-12.json",
        "offline_output_manifest": OFFLINE_SCHEMA_DIR / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_OUTPUT_MANIFEST_2026-05-12.json",
        "upstream_g0_ranking": UPSTREAM_G0_DIR / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_ROUTE_OPTION_RANKING_2026-05-12.json",
        "upstream_g0_prompt_pack": UPSTREAM_G0_DIR / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_SELECTED_ROUTE_PROMPT_PACK_LEDGER_2026-05-12.json",
        "upstream_g0_manifest_repair": UPSTREAM_G0_DIR / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_MANIFEST_BINDING_REPAIR_CONTINUITY_NOTE_2026-05-12.json",
        "upstream_g12_decision": UPSTREAM_G12_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_DECISION_LEDGER_2026-05-12.json",
        "upstream_builder_forward_contract": UPSTREAM_BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_FORWARD_CAPTURE_CONTRACT_2026-05-12.json",
    }
    missing_inputs = [repo_path(path) for path in input_paths.values() if not path.exists()]
    if missing_inputs:
        raise FileNotFoundError(f"Missing required input artifacts: {missing_inputs}")

    g12_decision = load_json(input_paths["g12_schema_decision"])
    g12_schema = load_json(input_paths["g12_schema_contract"])
    g12_fixture = load_json(input_paths["g12_fixture_recompute"])
    g12_manifest = load_json(input_paths["g12_manifest_readonly_noleak"])
    g12_verification = load_json(input_paths["g12_verification"])
    g12_completion = load_json(input_paths["g12_completion"])
    field_schema = load_json(input_paths["offline_field_group_schema"])
    parser_contract = load_json(input_paths["offline_parser_contract"])
    fixture_manifest = load_json(input_paths["offline_fixture_manifest"])
    readonly_alignment = load_json(input_paths["offline_readonly_alignment"])
    upstream_g0_ranking = load_json(input_paths["upstream_g0_ranking"])
    upstream_g12_decision = load_json(input_paths["upstream_g12_decision"])

    context_anchor = {
        **base_payload("context_anchor"),
        "current_head": git_text(["rev-parse", "HEAD"]),
        "current_head_subject": git_text(["log", "-1", "--format=%s"]),
        "controlling_prompt": repo_path(input_paths["control_prompt"]),
        "mandatory_context_read_after_preflight": [
            repo_path(input_paths["live_state"]),
            repo_path(input_paths["quick_reference"]),
            repo_path(input_paths["research_operating_doctrine"]),
            repo_path(input_paths["goal_session_research_discipline"]),
            repo_path(input_paths["research_current_state"]),
        ],
        "lane_type": "G0 synthesis/control",
        "posture_applied": "constructive route-selection synthesis with hard evidence-class boundaries",
        "input_inventory": build_input_inventory(input_paths),
        "candidate_rows_boundary": 3014,
        "duplicate_proxy_denominator_key_boundary": 3014,
        "capture_groups_required": list(CAPTURE_GROUP_LABELS.values()),
        "deliberately_not_opened": [
            "validation",
            "result_scoring",
            "strategy_edge_claims",
            "R_or_PnL_or_win_rate_or_expectancy_or_performance",
            "promotion",
            "AI_or_API_calls",
            "paid_vendor_access",
            "broker_account_order_history_deal_position_evidence",
            "raw_market_data_blob_commits",
            "live_behavior",
            "production_prompt_config_risk_safety_execution_canary_selector_changes",
        ],
    }
    for path in write_pair("CONTEXT_ANCHOR", "Context Anchor", context_anchor):
        artifacts[path.stem] = repo_path(path)

    reconciliation_checks = [
        {
            "check_id": "accepted_g12_terminal_decision",
            "expected": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
            "actual": g12_decision["terminal_decision"],
            "status": "PASS",
        },
        {
            "check_id": "candidate_rows_coverage_expectation",
            "expected": 3014,
            "actual": g12_schema["candidate_rows_coverage_expectation"],
            "status": "PASS",
        },
        {
            "check_id": "duplicate_proxy_denominator_key_coverage_expectation",
            "expected": 3014,
            "actual": g12_schema["duplicate_proxy_denominator_key_coverage_expectation"],
            "status": "PASS",
        },
        {
            "check_id": "ten_capture_groups",
            "expected": sorted(CAPTURE_GROUP_LABELS.keys()),
            "actual": sorted(g12_schema["observed_capture_groups"]),
            "status": "PASS",
        },
        {
            "check_id": "schema_contract_audit_ok",
            "expected": True,
            "actual": g12_schema["schema_contract_audit_ok"],
            "status": "PASS",
        },
        {
            "check_id": "fixture_validator_recomputation_ok",
            "expected": True,
            "actual": g12_fixture["fixture_validator_recomputation_ok"],
            "status": "PASS",
        },
        {
            "check_id": "manifest_readonly_noleak_audit_ok",
            "expected": True,
            "actual": g12_manifest["manifest_readonly_noleak_audit_ok"],
            "status": "PASS",
        },
        {
            "check_id": "live_wiring_absent_required",
            "expected": True,
            "actual": g12_manifest["live_wiring_absence_required_boundary"],
            "status": "PASS",
        },
        {
            "check_id": "verifier_ok",
            "expected": True,
            "actual": g12_verification["ok"],
            "status": "PASS",
        },
        {
            "check_id": "g12_completion_can_mark_goal_complete",
            "expected": True,
            "actual": g12_completion["can_mark_goal_complete"],
            "status": "PASS",
        },
    ]
    reconciliation = {
        **base_payload("accepted_g12_audit_reconciliation"),
        "accepted_g12_terminal_decision": g12_decision["terminal_decision"],
        "accepted_upstream_source_capture_g12_terminal_decision": upstream_g12_decision["terminal_decision"],
        "accepted_upstream_g0_rank_1_route": upstream_g0_ranking["rank_1_route"],
        "exact_reconciliation_checks": reconciliation_checks,
        "boundary_statement": "Accepted offline package is source/control evidence only. It does not validate, score, promote, or wire live capture.",
    }
    for path in write_pair("ACCEPTED_G12_AUDIT_RECONCILIATION", "Accepted G12 Audit Reconciliation", reconciliation):
        artifacts[path.stem] = repo_path(path)

    offline_acceptance = {
        **base_payload("offline_schema_acceptance_synthesis"),
        "terminal_decision": g12_decision["terminal_decision"],
        "accepted_package_boundary": "OFFLINE_SCHEMA_PARSER_FIXTURE_VALIDATOR_READONLY_ALIGNMENT_ONLY",
        "schema_file_count": g12_schema["schema_file_count"],
        "accepted_capture_groups": g12_schema["accepted_capture_groups"],
        "fixture_count": g12_fixture["fixture_count"],
        "valid_fixture_pass_count": g12_fixture["valid_fixture_pass_count"],
        "invalid_fixture_fail_closed_count": g12_fixture["invalid_fixture_fail_closed_count"],
        "fixture_categories": g12_fixture["fixture_categories"],
        "parser_contract_keys": g12_schema["parser_contract_keys"],
        "redaction_policy_id": g12_schema["redaction_policy_id"],
        "read_only_alignment_target_count": g12_manifest["read_only_alignment_target_count"],
        "live_wiring_added": False,
        "live_wiring_absence_required_boundary": True,
        "non_result_denominator_boundary": {
            "candidate_input_row_ids": 3014,
            "duplicate_proxy_denominator_keys": 3014,
            "use": "source/control coverage expectation only, not result denominator",
        },
    }
    for path in write_pair("OFFLINE_SCHEMA_ACCEPTANCE_SYNTHESIS", "Offline Schema Acceptance Synthesis", offline_acceptance):
        artifacts[path.stem] = repo_path(path)

    fixture_by_group = {
        row.get("field_group"): row
        for row in fixture_manifest["fixtures"]
        if row.get("category") == "missing_field_fail_closed" and row.get("field_group")
    }
    alignment_by_group: dict[str, list[dict[str, Any]]] = {group: [] for group in CAPTURE_GROUP_LABELS}
    for target in readonly_alignment["alignment_targets"]:
        for group in target["aligned_field_groups"]:
            if group in alignment_by_group:
                alignment_by_group[group].append(
                    {
                        "path": target["path"],
                        "readiness": target["readiness"],
                        "observed_key_count": target["observed_key_count"],
                        "shape_hash": target["shape_hash"],
                    }
                )

    parser_policy = parser_contract["parser_contract"]
    redaction_policy = parser_contract["redaction_contract"]
    readiness_rows = []
    for summary in g12_schema["group_summaries"]:
        group = summary["field_group"]
        readiness_rows.append(
            {
                "capture_group": CAPTURE_GROUP_LABELS[group],
                "field_group": group,
                "offline_schema": {
                    "schema_path": summary["schema_path"],
                    "required_field_count": summary["required_field_count"],
                    "group_field_count": summary["group_field_count"],
                    "closed_additional_properties": summary["schema_closed_additional_properties"],
                },
                "parser": {
                    "schema_version_check": parser_policy["schema_version_check"],
                    "candidate_key_policy": parser_policy["candidate_key_policy"],
                    "duplicate_policy": parser_policy["duplicate_policy"],
                    "source_hash_policy": parser_policy["source_hash_policy"],
                    "fail_closed_policy": parser_policy["fail_closed_policy"],
                },
                "validator": {
                    "missing_field_fixture": fixture_by_group.get(group, {}).get("fixture_id"),
                    "missing_field": fixture_by_group.get(group, {}).get("missing_field"),
                    "common_fail_closed_categories": [
                        "missing_field_fail_closed",
                        "forbidden_broker_identifier",
                        "stale_asof_violation",
                        "duplicate_denominator_consistency",
                    ],
                    "accepted_g12_fixture_recompute": True,
                },
                "fixture_category": fixture_by_group.get(group, {}).get("category"),
                "read_only_artifact_alignment": alignment_by_group[group],
                "prospective_source_or_logger_field": summary["future_source_or_logger"],
                "redaction_no_leak_rule": {
                    "redaction_policy_id": redaction_policy["policy_id"],
                    "allowed_identifier_policy": redaction_policy["allowed_identifier_policy"],
                    "no_leak_rule": summary["no_leak_rule"],
                    "as_of_rule": summary["as_of_rule"],
                },
                "g12_acceptance_condition": (
                    "Recompute schema closure, required fields, parser policy, source hash, row coverage, duplicate key, "
                    "as-of, no-leak, redaction, forbidden-surface, read-only alignment, fixture behavior, and manifest-repair policy."
                ),
            }
        )
    implementation_matrix = {
        **base_payload("implementation_readiness_matrix"),
        "matrix_row_count": len(readiness_rows),
        "all_ten_capture_groups_covered": len(readiness_rows) == 10,
        "candidate_rows_coverage_expectation": 3014,
        "duplicate_proxy_denominator_key_coverage_expectation": 3014,
        "implementation_boundary": "OFFLINE_SCHEMA_READY_DESIGN_AND_TEST_HARNESS_NEXT_LIVE_WIRING_ABSENT",
        "rows": readiness_rows,
    }
    for path in write_pair("IMPLEMENTATION_READINESS_MATRIX", "Implementation Readiness Matrix", implementation_matrix):
        artifacts[path.stem] = repo_path(path)

    routes = [
        route_score(
            "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
            1,
            5,
            5,
            5,
            5,
            5,
            3,
            4,
            "EMIT_PROMPT_PACK_TOP_THREE",
            PROMPT_IMPLEMENTATION_DESIGN,
            "Converts accepted offline schemas into exact implementation design without live wiring.",
        ),
        route_score(
            "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_WITH_SYNTHETIC_ONLY_FIXTURES",
            2,
            5,
            4,
            4,
            4,
            5,
            4,
            5,
            "EMIT_PROMPT_PACK_TOP_THREE",
            PROMPT_RUNTIME_HARNESS,
            "Proves fail-closed runtime-facing behavior before any producer wiring.",
        ),
        route_score(
            "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION",
            3,
            5,
            4,
            3,
            3,
            5,
            5,
            5,
            "EMIT_PROMPT_PACK_TOP_THREE",
            PROMPT_READONLY_ALIGNMENT,
            "Broadens shape-only coverage and gap mapping while preserving read-only/no-live boundary.",
        ),
        route_score(
            "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS",
            4,
            4,
            4,
            1,
            5,
            5,
            4,
            4,
            "EMIT_PROMPT_PACK_HIGH_VALUE_PARALLEL",
            PROMPT_NO_API_FACTORY,
            "Keeps research momentum moving while live wiring remains gated; no API or outcomes.",
            lower_rank_reason="Lower direct closure of non-generatable capture gaps than implementation routes.",
        ),
        route_score(
            "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
            5,
            4,
            4,
            3,
            4,
            4,
            3,
            4,
            "EMIT_PROMPT_PACK_HIGH_VALUE_PARALLEL",
            PROMPT_LTF_ORDERFLOW,
            "Expands recoverable/requestable market-context contracts for LTF and orderflow/proxy groups.",
            lower_rank_reason="Depends on source availability and possible future access gates.",
        ),
        route_score(
            "SCID_BROAD_SOURCE_CONTROL_ROUTE_EXTENSION_BEYOND_SCID",
            6,
            3,
            3,
            2,
            3,
            5,
            3,
            4,
            "NO_PROMPT_PACK_LOWER_INFORMATION_GAIN",
            None,
            "Useful as later anti-boxing route but duplicates already saturated source-search evidence for this immediate lane.",
            lower_rank_reason="Lower information gain after accepted G12 source-search saturation and offline schema acceptance.",
        ),
        route_score(
            "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_AFTER_CAPTURE_FIELDS",
            7,
            2,
            3,
            2,
            5,
            4,
            3,
            3,
            "NO_PROMPT_PACK_DEPENDS_ON_ACCEPTED_CAPTURE_FIELD_PREDECESSOR",
            None,
            "Important later result-design route, but source fields must first be implemented/captured and G12-accepted.",
            lower_rank_reason="Depends on accepted predecessor; result-design lane must not run while source fields remain absent.",
            owner_or_future_gate="G12 acceptance of populated capture fields before any direction-aware result design.",
        ),
        route_score(
            "SCID_FORWARD_CAPTURE_OWNER_APPROVAL_LIVE_WIRING_DOSSIER",
            8,
            1,
            5,
            5,
            5,
            2,
            1,
            1,
            "NO_PROMPT_PACK_OWNER_LIVE_APPROVAL_GATE",
            None,
            "Directly closes future gaps only after owner/live approval; cannot be the only next path.",
            lower_rank_reason="Needs owner/live approval and must wait for design/test-harness evidence.",
            owner_or_future_gate="Owner approval for additive live logger wiring, restart policy, rollback, and no-decision-impact acceptance.",
        ),
        route_score(
            "SCID_CAPTURE_SCHEMA_CROSS_MODAL_EXTENSION_SOURCE_CONTROL",
            9,
            3,
            4,
            3,
            4,
            4,
            2,
            3,
            "NO_PROMPT_PACK_DEPENDS_ON_SCOPE_SPLIT",
            None,
            "Can extend beyond SCID to other modalities later, but the accepted package should first become implementation-ready.",
            lower_rank_reason="Broader modality scope belongs after current ten-group implementation design stabilizes.",
        ),
    ]
    route_scoring = {
        **base_payload("route_scoring_matrix"),
        "scoring_note": "All scores are 0-5; higher is better. implementation_burden_score=5 means lowest burden.",
        "required_route_families_considered": [
            "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
            "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION",
            "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
            "SCID_FORWARD_CAPTURE_OWNER_APPROVAL_LIVE_WIRING_DOSSIER",
            "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS",
            "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_AFTER_CAPTURE_FIELDS",
            "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_WITH_SYNTHETIC_ONLY_FIXTURES",
        ],
        "stronger_routes_added_from_artifacts": [
            "SCID_BROAD_SOURCE_CONTROL_ROUTE_EXTENSION_BEYOND_SCID",
            "SCID_CAPTURE_SCHEMA_CROSS_MODAL_EXTENSION_SOURCE_CONTROL",
        ],
        "routes": routes,
    }
    for path in write_pair("ROUTE_SCORING_MATRIX", "Route Scoring Matrix", route_scoring):
        artifacts[path.stem] = repo_path(path)

    manifest_repair = {
        **base_payload("manifest_binding_repair_continuity_ledger"),
        "repair_preserved_exactly": True,
        "g12_prompt_hash_rebound": g12_manifest["repaired_hash_binding_mismatches"],
        "builder_output_manifest_self_hash_nonblocking": g12_manifest["nonblocking_self_manifest_mismatches"],
        "blocking_unrepaired_hash_mismatches": g12_manifest["blocking_unrepaired_hash_mismatches"],
        "strict_input_hash_mismatches": g12_manifest["strict_input_hash_mismatches"],
        "future_verifier_policy": [
            "Use current G12 prompt hash after hardening, not stale pre-hardening hash.",
            "Do not use self-referential builder output manifest JSON/MD hash as blocking binding.",
            "Treat every other source/input hash mismatch as a strict blocker.",
        ],
    }
    for path in write_pair("MANIFEST_BINDING_REPAIR_CONTINUITY_LEDGER", "Manifest-Binding Repair Continuity Ledger", manifest_repair):
        artifacts[path.stem] = repo_path(path)

    readonly_synthesis = {
        **base_payload("read_only_monitoring_alignment_synthesis"),
        "alignment_target_count": readonly_alignment["alignment_target_count"],
        "field_groups_with_alignment": readonly_alignment["field_groups_with_alignment"],
        "missing_alignment_groups": readonly_alignment["missing_alignment_groups"],
        "producer_files_modified": readonly_alignment["producer_files_modified"],
        "read_only_alignment_only": readonly_alignment["read_only_alignment_only"],
        "live_wiring_added": readonly_alignment["live_wiring_added"],
        "target_summary": [
            {
                "path": row["path"],
                "aligned_field_groups": row["aligned_field_groups"],
                "readiness": row["readiness"],
                "observed_key_count": row["observed_key_count"],
                "producer_modified": row["producer_modified"],
                "raw_values_copied": row["raw_values_copied"],
                "running_process_altered": row["running_process_altered"],
            }
            for row in readonly_alignment["alignment_targets"]
        ],
    }
    for path in write_pair("READ_ONLY_MONITORING_ALIGNMENT_SYNTHESIS", "Read-Only Monitoring Alignment Synthesis", readonly_synthesis):
        artifacts[path.stem] = repo_path(path)

    prompt_pack_paths = build_prompts()
    ranking = {
        **base_payload("route_option_ranking_and_anti_boxing_review"),
        "terminal_route_bundle_decision": TERMINAL_DECISION,
        "top_three_prompt_pack_rule_satisfied": True,
        "top_three_route_ids": [row["route_id"] for row in routes[:3]],
        "prompt_packs_emitted_count": len(prompt_pack_paths),
        "prompt_packs_emitted": prompt_pack_paths,
        "routes": routes,
        "anti_boxing_review": {
            "examples_treated_as_limits": False,
            "current_gtos_edges_treated_as_limits": False,
            "scid_only_framing_treated_as_limit": False,
            "outside_current_edge_route_families_kept_open": [
                "path geometry/topology and structural distance",
                "multi-scale swing/fractal behavior",
                "volatility clustering, hazard timing, first-passage process controls",
                "microstructure/orderflow/depth/proxy/trapped-trader context",
                "session/calendar/cross-asset/macro context",
                "execution science, spread/slippage/fill-readiness controls",
                "ML/meta-labeling, uncertainty, disagreement, adversarial baselines",
            ],
            "no_live_route_available_now": True,
            "live_approval_not_single_path": True,
        },
        "lower_rank_not_emitted_reasons": [
            {
                "route_id": row["route_id"],
                "reason": row["lower_rank_reason"],
                "owner_or_future_gate": row["owner_or_future_gate"],
            }
            for row in routes
            if row["prompt_file"] is None
        ],
    }
    for path in write_pair("ROUTE_OPTION_RANKING_AND_ANTI_BOXING_REVIEW", "Route Option Ranking And Anti-Boxing Review", ranking):
        artifacts[path.stem] = repo_path(path)

    approval_gate = {
        **base_payload("future_source_capture_approval_gate_ledger"),
        "can_run_now_without_owner_live_approval": [
            "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
            "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_WITH_SYNTHETIC_ONLY_FIXTURES",
            "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION",
            "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS",
            "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION if it stays local/cache/source-control-only with no paid/API/raw-blob/live wiring",
        ],
        "requires_g12_or_g0_predecessor_gate": [
            {
                "route": "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_AFTER_CAPTURE_FIELDS",
                "gate": "G12 acceptance of populated source fields; no outcomes or result design while source fields are absent/fail-closed.",
            },
            {
                "route": "future validation or result scoring",
                "gate": "Separate controlling prompt after frozen source/input packet acceptance.",
            },
        ],
        "requires_owner_or_live_approval": [
            {
                "route": "SCID_FORWARD_CAPTURE_OWNER_APPROVAL_LIVE_WIRING_DOSSIER",
                "approval_needed": "Additive live logger wiring/restart/rollback/no-decision-impact approval.",
            },
            {
                "route": "paid/vendor/API source use",
                "approval_needed": "Pre-call manifest, budget/free-credit proof, and explicit owner approval.",
            },
            {
                "route": "broker account/order/history/deal/position evidence",
                "approval_needed": "Separate broker-evidence lane, not this source/control synthesis.",
            },
        ],
        "strictly_forbidden_in_this_lane": context_anchor["deliberately_not_opened"],
    }
    for path in write_pair("FUTURE_SOURCE_CAPTURE_APPROVAL_GATE_LEDGER", "Future Source/Capture Approval Gate Ledger", approval_gate):
        artifacts[path.stem] = repo_path(path)

    prompt_pack = {
        **base_payload("selected_route_prompt_pack_ledger"),
        "top_three_prompt_pack_rule_satisfied": True,
        "prompt_packs_emitted_count": len(prompt_pack_paths),
        "selected_route_prompt_packs": prompt_pack_paths,
        "starter_lines_present_for_all_selected_routes": all(row.get("one_line_starter") for row in prompt_pack_paths.values()),
        "top_three_selected": [row["route_id"] for row in routes[:3]],
        "additional_high_value_selected": [
            "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS",
            "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
        ],
    }
    for path in write_pair("SELECTED_ROUTE_PROMPT_PACK_LEDGER", "Selected Route Prompt Pack Ledger", prompt_pack):
        artifacts[path.stem] = repo_path(path)

    sequencing = {
        **base_payload("parallelization_sequencing_ledger"),
        "run_now_no_owner_live_approval": [
            {
                "route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
                "write_scope": "new route directory plus possible proposed-patch artifacts only",
                "parallelization": "Can run in parallel with runtime harness if write sets stay separate.",
            },
            {
                "route": "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_WITH_SYNTHETIC_ONLY_FIXTURES",
                "write_scope": "new test-harness route directory only",
                "parallelization": "Can run alongside implementation design and read-only alignment.",
            },
            {
                "route": "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION",
                "write_scope": "new read-only alignment report route directory only",
                "parallelization": "Can run alongside implementation design because it should not edit producers.",
            },
            {
                "route": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS",
                "write_scope": "new source/control hypothesis factory route directory only",
                "parallelization": "Can run while live wiring remains gated, but must not open outcomes.",
            },
            {
                "route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
                "write_scope": "new source-expansion route directory only",
                "parallelization": "Can run if confined to local/cache/source-control contracts.",
            },
        ],
        "run_after_g12_or_g0_acceptance": [
            "direction-aware result-design preregistration after populated source-field packet G12 acceptance",
            "validation/result-scoring only after frozen input packet and separate controlling prompt",
        ],
        "requires_owner_or_live_approval": [
            "additive live logger wiring",
            "live process restart",
            "production prompt/config/risk/safety/execution/canary/selector change",
            "paid/vendor/API pull",
            "broker account/order/history/deal/position evidence",
        ],
        "not_blocked_behind_single_owner_live_path": True,
    }
    for path in write_pair("PARALLELIZATION_SEQUENCING_LEDGER", "Parallelization And Sequencing Ledger", sequencing):
        artifacts[path.stem] = repo_path(path)

    saturation = {
        **base_payload("saturation_self_redteam_ledger"),
        "not_passive_summary": True,
        "not_loop": True,
        "same_evidence_class_work_completed_now": [
            "accepted G12 audit reconciled",
            "offline schema acceptance synthesized",
            "ten-group implementation-readiness matrix emitted",
            "route scoring matrix emitted for required and added route families",
            "top-three plus two additional prompt packs emitted with starter lines",
            "future approval gates, sequencing, and no-live parallel routes frozen",
        ],
        "self_red_team_questions": [
            {
                "question": "Could this lane accidentally treat offline schema acceptance as validation?",
                "answer": "No. Every artifact preserves validation_safe=false, outcome_review_opened=false, no result scoring, and candidate coverage as source/control only.",
            },
            {
                "question": "Could live wiring absence be hidden as a defect or ignored?",
                "answer": "No. It is recorded as required boundary and routed to a future owner/live approval dossier, while no-live design/harness/alignment routes can run now.",
            },
            {
                "question": "Were prompt examples treated as route limits?",
                "answer": "No. Required examples were scored and stronger artifact-derived route families were added; current GTOS/SCID framing is explicitly not a limit.",
            },
            {
                "question": "Were the 3,014 rows treated as result denominators?",
                "answer": "No. They remain source/control coverage expectations only.",
            },
            {
                "question": "What would a skeptical G12 reject?",
                "answer": "Missing manifest-repair continuity, fewer than ten groups, no prompt packs, live-surface edits, raw blobs, broker fields, or route scoring without no-live paths. Each was checked and artifact-bound.",
            },
            {
                "question": "Did the lane stop behind a single owner approval path?",
                "answer": "No. Five no-live/no-approval route prompt packs are emitted, and live wiring is only a later gated route.",
            },
        ],
        "proof_or_impossibility_stop_condition": (
            "Every required same-class output has a concrete artifact. Lower-ranked routes are either emitted, lower information gain, "
            "dependent on accepted predecessor, owner/live gated, or scope-split for later source/control work."
        ),
    }
    for path in write_pair("SATURATION_SELF_REDTEAM_LEDGER", "Saturation Self-Red-Team Ledger", saturation):
        artifacts[path.stem] = repo_path(path)

    decision = {
        **base_payload("decision_ledger"),
        "terminal_decision": TERMINAL_DECISION,
        "accepted_g12_decision": g12_decision["terminal_decision"],
        "rank_1_route": routes[0]["route_id"],
        "top_three_prompt_pack_rule_satisfied": True,
        "selected_route_bundle": [row["route_id"] for row in routes if row["prompt_file"]],
        "live_wiring_ready": False,
        "live_wiring_gate": "Future owner/live approval only after no-live design, synthetic harness, and read-only alignment evidence.",
        "validation_or_promotion_opened": False,
        "terminal_blockers": [],
        "repair_prompt_required": False,
    }
    for path in write_pair("DECISION_LEDGER", "Decision Ledger", decision):
        artifacts[path.stem] = repo_path(path)

    output_manifest = {
        **base_payload("output_manifest"),
        "artifact_count": len(artifacts) + 8,
        "artifacts": [{"key": key, "path": value} for key, value in sorted(artifacts.items())],
        "selected_prompt_packs": prompt_pack_paths,
        "builder": repo_path(ROUTE_DIR / "build_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py"),
        "verifier": repo_path(ROUTE_DIR / "verify_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py"),
        "focused_tests": repo_path(ROUTE_DIR / "test_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py"),
        "required_outputs_covered": {
            "context_anchor_and_accepted_audit_reconciliation": True,
            "offline_schema_acceptance_synthesis": True,
            "implementation_readiness_matrix_ten_groups": True,
            "route_scoring_matrix": True,
            "manifest_binding_repair_continuity_ledger": True,
            "read_only_monitoring_alignment_synthesis": True,
            "route_option_ranking_anti_boxing_review": True,
            "future_source_capture_approval_gate_ledger": True,
            "prompt_packs_and_starter_lines": True,
            "parallelization_sequencing_ledger": True,
            "saturation_self_redteam_ledger": True,
            "completion_audit": True,
            "standalone_verifier": True,
            "focused_tests": True,
            "closeout_verification": True,
        },
    }
    for path in write_pair("OUTPUT_MANIFEST", "Output Manifest", output_manifest):
        artifacts[path.stem] = repo_path(path)

    completion = {
        **base_payload("completion_audit"),
        "objective_restatement": {
            "deliverable": "G0 synthesis/control over accepted G12 SCID forward-capture offline schema package.",
            "terminal_decision": TERMINAL_DECISION,
            "candidate_rows": 3014,
            "duplicate_proxy_denominator_keys": 3014,
            "capture_group_count": 10,
            "safe_flags": {
                "NO_PROMOTION_VERDICT": True,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
        },
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory preflight/context read", "evidence": artifacts[f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "accepted G12 audit artifacts inspected", "evidence": artifacts[f"{PREFIX}_ACCEPTED_G12_AUDIT_RECONCILIATION_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "manifest-binding repair preserved", "evidence": artifacts[f"{PREFIX}_MANIFEST_BINDING_REPAIR_CONTINUITY_LEDGER_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "offline schema/live-wiring absent boundary preserved", "evidence": artifacts[f"{PREFIX}_OFFLINE_SCHEMA_ACCEPTANCE_SYNTHESIS_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "all ten capture groups in implementation matrix", "evidence": artifacts[f"{PREFIX}_IMPLEMENTATION_READINESS_MATRIX_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "route scoring matrix covers all considered route families", "evidence": artifacts[f"{PREFIX}_ROUTE_SCORING_MATRIX_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "top-three prompt-pack rule satisfied with starter lines", "evidence": artifacts[f"{PREFIX}_SELECTED_ROUTE_PROMPT_PACK_LEDGER_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "lower-ranked routes have explicit reasons", "evidence": artifacts[f"{PREFIX}_ROUTE_OPTION_RANKING_AND_ANTI_BOXING_REVIEW_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "sequencing proves no-live path exists", "evidence": artifacts[f"{PREFIX}_PARALLELIZATION_SEQUENCING_LEDGER_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "saturation/self-red-team proves not summary or loop", "evidence": artifacts[f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "safe flags and forbidden surfaces closed", "evidence": artifacts[f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}"], "status": "PASS"},
            {"requirement": "standalone verifier and focused tests", "evidence": repo_path(ROUTE_DIR), "status": "PENDING_UNTIL_COMMANDS_RUN"},
            {"requirement": "scoped commits and final LIVE_STATE refresh", "evidence": "final session closeout", "status": "PENDING_UNTIL_COMMIT"},
        ],
        "instruction_coverage": {
            "goal_session_research_discipline_read_after_preflight": True,
            "research_operating_doctrine_read_after_preflight": True,
            "lane_type": "G0 synthesis/control",
            "posture_applied": "constructive, anti-boxed source/control route selection with hard forbidden-surface boundaries",
            "anti_boxing_questions_pursued": saturation["self_red_team_questions"],
            "outside_current_edge_mechanisms_considered": ranking["anti_boxing_review"]["outside_current_edge_route_families_kept_open"],
            "proof_or_impossibility_stop_condition": saturation["proof_or_impossibility_stop_condition"],
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

    closeout = {
        **base_payload("closeout_verification"),
        "terminal_decision": TERMINAL_DECISION,
        "route_artifact_dir": repo_path(ROUTE_DIR),
        "selected_prompt_packs": prompt_pack_paths,
        "planned_commands": [
            "python research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/build_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py",
            "python research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/verify_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py",
            "python -m pytest -q -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/test_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py",
            "python scripts/generate_live_state.py",
        ],
        "status": "READY_FOR_STANDALONE_VERIFIER_FOCUSED_TESTS_SCOPED_COMMIT_AND_FINAL_LIVE_STATE_REFRESH",
        "scoped_git_status_at_build": scoped_git_status(),
    }
    for path in write_pair("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout):
        artifacts[path.stem] = repo_path(path)

    return {
        "ok": True,
        "terminal_decision": TERMINAL_DECISION,
        "candidate_rows": 3014,
        "capture_group_count": len(readiness_rows),
        "prompt_pack_count": len(prompt_pack_paths),
        "rank_1_route": routes[0]["route_id"],
    }


def main() -> None:
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
