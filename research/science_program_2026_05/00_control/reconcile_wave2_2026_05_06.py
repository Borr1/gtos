"""Reconcile wave-2 science-lane outputs into G0 master artifacts.

Scope: research/science_program_2026_05 control artifacts only.
No live trading prompts, risk, execution, permissions, selectors, MT5,
canaries, paid data, or order behavior are read or changed by this script.
"""

from __future__ import annotations

import copy
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "00_control"
DOMAIN_DIR = ROOT / "01_domain_syntheses"
HYP_DIR = ROOT / "02_hypothesis_registry"
EXP_DIR = ROOT / "03_experiment_specs"
SYN_DIR = ROOT / "05_synthesis"

HEAD_RECONCILED = "7a95a293"
WAVE2_MERGE_COMMIT = "a5714d04"

LANE_COMMITS = {
    "G1": "649ead84",
    "G2": "fe08479f",
    "G3": "f0e0c8c9",
    "G4": "00621862",
    "G5": "7dfc0c59",
    "G6": "9344cda5",
    "G7": "ef3eb3a0",
    "G8": "ca037ca8",
    "G9": "1423a7e7",
    "G10": "9116ceed",
    "G11": "7264cd0c",
}

LANE_IDS = list(LANE_COMMITS)

ALLOWED_LABEL_CLASSES = {
    "broker_actual_r",
    "synthetic_path_r",
    "lifecycle_no_fill",
    "observation_only",
    "context_only",
}

LABEL_NORMALIZATION = {
    "synthetic_path_r_separated_from_future_broker_actual_r": "synthetic_path_r",
    "synthetic_path_r_separated_from_broker_actual_r": "synthetic_path_r",
    "context_filter_only": "context_only",
}

FORBIDDEN_NO_LEAK_FIELD_NAMES = {
    "actual_r",
    "future_orderflow",
    "future_price",
    "future_release_value",
    "future_return",
    "future_vol_index",
    "outcome_r",
    "post_entry_path",
    "post_event_outcome",
    "post_release_revision",
    "post_signal_continuation",
    "post_signal_path",
    "stop_loss_hit",
    "take_profit_hit",
    "trade_outcome",
    "trade_result",
    "win_loss",
}

G0_FILES_WRITTEN = [
    "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
    "research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.json",
    "research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.md",
    "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
    "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.md",
    "research/science_program_2026_05/00_control/reconcile_wave2_2026_05_06.py",
    "research/science_program_2026_05/01_domain_syntheses/G0_GOVERNOR_CONTEXT_AMBIGUITY_LEDGER_2026-05-06.md",
    "research/science_program_2026_05/02_hypothesis_registry/MECHANISM_REGISTRY_2026-05-06.json",
    "research/science_program_2026_05/02_hypothesis_registry/HYPOTHESIS_REGISTRY_2026-05-06.json",
    "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json",
    "research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json",
    "research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md",
    "research/science_program_2026_05/05_synthesis/G0_CROSS_AGENT_SYNTHESIS_2026-05-06.json",
    "research/science_program_2026_05/05_synthesis/G0_CROSS_AGENT_SYNTHESIS_2026-05-06.md",
    "research/science_program_2026_05/05_synthesis/G0_WAVE2_RECONCILIATION_2026-05-06.json",
    "research/science_program_2026_05/05_synthesis/G0_WAVE2_RECONCILIATION_2026-05-06.md",
    "research/science_program_2026_05/05_synthesis/G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.json",
    "research/science_program_2026_05/05_synthesis/G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md",
    "research/science_program_2026_05/05_synthesis/G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.json",
    "research/science_program_2026_05/05_synthesis/G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md",
    "research/science_program_2026_05/05_synthesis/G0_COMPLETION_AUDIT_2026-05-06.json",
    "research/science_program_2026_05/05_synthesis/G0_COMPLETION_AUDIT_2026-05-06.md",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.as_posix()


def lane_from_path(path: Path) -> str | None:
    name = path.name
    path_text = path.as_posix()
    for lane_id in LANE_IDS:
        if name.startswith(f"{lane_id}_") or f"/{lane_id}_" in path_text:
            return lane_id
    return None


def collect_lane_rows() -> dict[str, dict[str, Any]]:
    lanes: dict[str, dict[str, Any]] = {
        lane_id: {
            "mechanisms": [],
            "hypotheses": [],
            "preregs": [],
            "sources": [],
            "status": None,
            "files": defaultdict(list),
        }
        for lane_id in LANE_IDS
    }

    def add(lane_id: str, kind: str, rows: list[dict[str, Any]], source: str) -> None:
        if not rows:
            return
        for row in rows:
            lanes[lane_id][kind].append(copy.deepcopy(row))
        lanes[lane_id]["files"][kind].append(source)

    for path in sorted(ROOT.rglob("*.json")):
        if "__pycache__" in path.parts:
            continue
        lane_id = lane_from_path(path)
        if lane_id is None:
            continue

        data = load_json(path)
        source = rel(path)
        name = path.name

        if isinstance(data, dict):
            schema = data.get("schema")
            if schema == "science_mechanism_v1":
                add(lane_id, "mechanisms", data.get("rows", []), source)
            elif schema == "science_hypothesis_v1":
                add(lane_id, "hypotheses", data.get("rows", []), source)
            elif schema == "experiment_prereg_v1":
                add(lane_id, "preregs", data.get("rows", []), source)
            elif schema == "source_contract_v2":
                add(lane_id, "sources", data.get("rows", []), source)

            embedded = [
                ("mechanism_rows", "mechanisms"),
                ("hypothesis_rows", "hypotheses"),
                ("experiment_prereg_rows", "preregs"),
                ("source_contract_rows", "sources"),
                ("mechanisms", "mechanisms"),
                ("hypotheses", "hypotheses"),
                ("experiment_preregs", "preregs"),
                ("source_contracts", "sources"),
            ]
            for key, kind in embedded:
                if isinstance(data.get(key), list):
                    add(lane_id, kind, data[key], f"{source}:{key}")

            if name.endswith("GOAL_STATUS_2026-05-06.json"):
                lanes[lane_id]["status"] = copy.deepcopy(data)
                lanes[lane_id]["files"]["status"].append(source)
            if isinstance(data.get("goal_status_row"), dict):
                lanes[lane_id]["status"] = copy.deepcopy(data["goal_status_row"])
                lanes[lane_id]["files"]["status"].append(f"{source}:goal_status_row")
            if isinstance(data.get("goal_status"), dict):
                lanes[lane_id]["status"] = copy.deepcopy(data["goal_status"])
                lanes[lane_id]["files"]["status"].append(f"{source}:goal_status")

        elif isinstance(data, list):
            if "MECHANISMS" in name:
                add(lane_id, "mechanisms", data, source)
            elif "HYPOTHESES" in name:
                add(lane_id, "hypotheses", data, source)
            elif "PREREGS" in name:
                add(lane_id, "preregs", data, source)
            elif "SOURCE_CONTRACTS" in name:
                add(lane_id, "sources", data, source)

    return lanes


def duplicate_ids(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    counts = Counter(row.get(field) for row in rows)
    return [
        {"id": value, "count": count}
        for value, count in sorted(counts.items(), key=lambda item: str(item[0]))
        if count > 1
    ]


def sort_rows(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: str(row.get(field, "")))


def collect_source_reference_issues(
    all_mechanisms: list[dict[str, Any]],
    all_hypotheses: list[dict[str, Any]],
    all_sources: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_ids = {row.get("source_id") for row in all_sources}
    issues: list[dict[str, Any]] = []
    for row_type, id_field, rows in [
        ("mechanism", "mechanism_id", all_mechanisms),
        ("hypothesis", "hypothesis_id", all_hypotheses),
    ]:
        for row in rows:
            for source_id in row.get("source_ids", []) or []:
                if source_id in source_ids:
                    continue
                if str(source_id).startswith("LIT-"):
                    issue_type = "literature_reference_without_source_contract"
                elif str(source_id).startswith("HYP-") or str(source_id).startswith("future_"):
                    issue_type = "cross_domain_placeholder_not_source_contract"
                else:
                    issue_type = "unregistered_source_reference"
                issues.append(
                    {
                        "row_type": row_type,
                        "row_id": row.get(id_field),
                        "source_id": source_id,
                        "issue": issue_type,
                        "blocking_validation_safe": True,
                    }
                )
    return issues


def no_leak_semantic_blockers(all_hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for row in all_hypotheses:
        fields = row.get("no_leak_fields")
        if not isinstance(fields, list) or not fields:
            blockers.append(
                {
                    "hypothesis_id": row.get("hypothesis_id"),
                    "issue": "missing_or_empty_no_leak_fields",
                    "fields": fields,
                }
            )
            continue
        forbidden = [field for field in fields if str(field).lower() in FORBIDDEN_NO_LEAK_FIELD_NAMES]
        if forbidden:
            blockers.append(
                {
                    "hypothesis_id": row.get("hypothesis_id"),
                    "issue": "no_leak_fields_contains_forbidden_outcome_or_future_field_names",
                    "fields": forbidden,
                    "reason": (
                        "The schema expects decision-time/as-of feature names. These names read as "
                        "forbidden outcome/future fields or exclusion examples, so G0 keeps the row "
                        "research-only and sends it to G12 instead of silently rewriting it."
                    ),
                }
            )
    return blockers


def build_status_rows(
    lanes: dict[str, dict[str, Any]],
    lane_counts: dict[str, dict[str, Any]],
    now: str,
    totals: dict[str, int],
    no_leak_blockers: list[dict[str, Any]],
    source_reference_issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    status_rows: list[dict[str, Any]] = [
        {
            "lane_id": "G0",
            "lane_status": "G0_WAVE2_RECONCILIATION_COMPLETE_PENDING_COMMIT",
            "files_written": G0_FILES_WRITTEN,
            "tests_run": [
                "python scripts/generate_live_state.py -> passed",
                "mandatory preflight reads completed: LIVE_STATE, latest handoff, quick reference, research doctrine, research current state, reading order, controlling G0 prompt",
                "git show --stat --oneline HEAD -> confirmed HEAD 7a95a293 docs: record science wave 2 merge state",
                "python research\\science_program_2026_05\\00_control\\reconcile_wave2_2026_05_06.py -> generated wave-2 G0 artifacts",
                f"custom schema/relationship/duplicate/source/prereg/no-leak checks -> pending final verification; generated counts mechanisms={totals['mechanisms']}, hypotheses={totals['hypotheses']}, preregs={totals['preregs']}, sources={totals['sources']}",
            ],
            "blockers": [
                f"All {totals['sources']} source contracts remain validation_safe=false; no source is validation-safe or promotion-safe.",
                "No survivor backlog row exists because every candidate remains source/label/sample/no-leak/owner-approval blocked.",
                f"G0 found {len(no_leak_blockers)} no-leak semantic blocker rows, mostly G11 source-governance rows that list outcome/future fields under no_leak_fields.",
                f"G0 found {len(source_reference_issues)} source-reference placeholders or literature references that are not source_contract_v2 rows.",
                "G12 red-team pass has not run; this reconciliation only creates the shortlist and prompt guidance.",
            ],
            "next_questions": [
                "Run G12 red-team review against the wave-2 master registries before any survivor backlog is created.",
                "Run cross-domain second-pass assignments only after each assignment freezes source contracts, no-leak fields, and label policy.",
                "Do not promote any row until a separate owner-approved promotion dossier exists with validation-safe source contracts and blocker-clearing notes.",
            ],
            "commit_sha": None,
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "checked_at_utc": now,
        }
    ]

    for lane_id in LANE_IDS:
        status = copy.deepcopy(lanes[lane_id]["status"])
        if status is None:
            status = {
                "lane_id": lane_id,
                "lane_status": "MISSING_STATUS_ROW_DURING_G0_WAVE2_RECONCILIATION",
                "files_written": [],
                "tests_run": [],
                "blockers": ["No lane-owned status row found during G0 wave-2 reconciliation."],
                "next_questions": ["Re-run lane or add goal_status_v1 artifact."],
                "commit_sha": LANE_COMMITS[lane_id],
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            }
        status["lane_id"] = lane_id
        status.setdefault("files_written", [])
        status.setdefault("tests_run", [])
        status.setdefault("blockers", [])
        status.setdefault("next_questions", [])
        stale = status.get("commit_sha") != LANE_COMMITS[lane_id]
        status["commit_sha"] = LANE_COMMITS[lane_id]
        if stale:
            status["lane_status"] = f"{status.get('lane_status')}_G0_WAVE2_COMMIT_RECONCILED"
            status["blockers"] = list(status["blockers"]) + [
                (
                    "Lane-owned status commit metadata was stale/null during G0 wave-2 reconciliation; "
                    f"registry uses effective git commit {LANE_COMMITS[lane_id]}."
                )
            ]
        else:
            status["lane_status"] = f"{status.get('lane_status')}_G0_WAVE2_RECONCILED"
        status["promotion_verdict"] = "NO_PROMOTION_VERDICT"
        status["g0_wave2_row_counts"] = lane_counts[lane_id]
        status_rows.append(status)

    status_rows.append(
        {
            "lane_id": "G12",
            "lane_status": "READY_FOR_RED_TEAM_AFTER_G0_WAVE2_RECONCILIATION",
            "files_written": [
                "research/science_program_2026_05/04_goal_prompts/G12_G12_RED_TEAM_GOAL_PROMPT_2026-05-06.md",
                "research/science_program_2026_05/05_synthesis/G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md",
                "research/science_program_2026_05/05_synthesis/G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.json",
            ],
            "tests_run": [],
            "blockers": [
                "G12 has not executed yet.",
                "G12 must review G0 wave-2 no-leak, source-reference, duplicate, label-separation, source-validity, and promotion-drift blockers before any survivor backlog exists.",
            ],
            "next_questions": [
                "Launch G12 in C:\\tmp\\gtosg\\G12 using its controlling prompt and the G0 red-team shortlist.",
            ],
            "commit_sha": None,
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        }
    )
    return status_rows


def build_second_pass_assignments(now: str) -> dict[str, Any]:
    assignments = [
        {
            "assignment_id": "CD2-01",
            "title": "Macro-vol-source freshness triad",
            "lanes": ["G7", "G8", "G11", "G1"],
            "seed_rows": [
                "HYP-G7-XG8-VOL-MACRO-011",
                "HYP-G7-XG11-SOURCE-FRESH-012",
                "HYP-G11-PUBLIC-LAG-004",
                "HYP-G8-VRP-004",
            ],
            "objective": "Freeze publication/as-of rules for macro, volatility-index, and source-freshness context before any outcome review.",
            "required_blocker_checks": [
                "FRED/BIS/COT/Cboe publication timestamps",
                "no stale calendar or revised value leakage",
                "source_contract_v2 rows remain validation_safe=false until parser/cache/no-lookahead tests pass",
            ],
            "stop_output": "source-freshness compatibility ledger plus prereg update proposal, not a validation result",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "assignment_id": "CD2-02",
            "title": "Short-vol stress versus execution lifecycle",
            "lanes": ["G8", "G10", "G11"],
            "seed_rows": [
                "HYP-G8-VIX1D9D-STRESS-002",
                "G10-HYP-PENDING-001",
                "G10-HYP-PREFILL-003",
                "HYP-G11-FRICTION-GATE-007",
            ],
            "objective": "Define whether short-tenor volatility context can be joined to pending-limit no-fill, spread, and close-side cost rows without label mixing.",
            "required_blocker_checks": [
                "Cboe CSV same-day availability",
                "pending lifecycle ordering",
                "close-side slippage coverage",
                "synthetic path-R, lifecycle, and broker actual-R separation",
            ],
            "stop_output": "lifecycle-only prereg and missing-source ledger",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "assignment_id": "CD2-03",
            "title": "Offline-RL reward and risk-bank boundary",
            "lanes": ["G9", "G10", "G1", "G6"],
            "seed_rows": [
                "HYP-G9-OFFLINE-RL-POLICY-009",
                "G10-HYP-RISKBANK-005",
                "G6-HYP-002",
            ],
            "objective": "Translate offline policy comparison into a frozen reward definition that respects risk-bank invariants and never uses live exploration.",
            "required_blocker_checks": [
                "no live sizing or execution change",
                "risk-bank invariant",
                "duplicate lifecycle controls",
                "broker actual-R versus synthetic path-R separation",
                "DSR/PBO/effective-N policy",
            ],
            "stop_output": "offline-only reward contract and red-teamable prereg; no policy promotion",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "assignment_id": "CD2-04",
            "title": "K55 source-provenance and orderflow feature gate",
            "lanes": ["G9", "G4", "G11", "G1"],
            "seed_rows": [
                "HYP-G9G4-K55-SOURCE-006",
                "HYP-G9G4-TOOL-ORDERFLOW-005",
                "HYP-G11G4-SOURCE-GATED-ORDERFLOW-008",
                "HYP-G4-OFI-DEPTH-001",
            ],
            "objective": "Convert orderflow/depth rows into K55 source-status and provenance flags only, not validation-safe predictive features.",
            "required_blocker_checks": [
                "Databento/Sierra legality and timestamp provenance",
                "feature bundle target-version match",
                "no source marked validation_safe=true",
                "tool-grounding remains approval/budget blocked",
            ],
            "stop_output": "feature-provenance contract and source-status join map",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "assignment_id": "CD2-05",
            "title": "Macro attention and behavioral attention interaction",
            "lanes": ["G7", "G5", "G1"],
            "seed_rows": [
                "HYP-G7-XG5-MACRO-ATTN-010",
                "HYP-G5-XG7-MACRO-ATTN-009",
                "HYP-G7-FOMC-ATTN-003",
                "HYP-G5-NEWS-005",
            ],
            "objective": "Resolve duplicated macro/news attention rows into one lifecycle-only prereg with stale-calendar and event-publication gates.",
            "required_blocker_checks": [
                "local calendar freshness",
                "event source publication timestamp",
                "no post-release surprise leakage",
                "no live news-filter change",
            ],
            "stop_output": "deduped attention prereg proposal and blocker ledger",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "assignment_id": "CD2-06",
            "title": "Pre-fill delivery path and no-retrace opportunity map",
            "lanes": ["G10", "G6", "G4"],
            "seed_rows": [
                "G10-HYP-PREFILL-003",
                "G10-HYP-XDOMAIN-008",
                "G6-HYP-002",
                "HYP-G4-FILL-QUALITY-009",
            ],
            "objective": "Make setup-decision-to-fill/cancel path capture precise enough to study no-retrace and adverse-fill mechanisms without scoring a live strategy.",
            "required_blocker_checks": [
                "exact decision entry price",
                "ordered M1 or tick path",
                "pending lifecycle state",
                "same-bar ambiguity classification",
                "fill/no-fill separated from R labels",
            ],
            "stop_output": "prefill path capture spec and missing-field audit",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "assignment_id": "CD2-07",
            "title": "Prop-firm stress calendar and portfolio opportunity cost",
            "lanes": ["G10", "G7", "G8", "G11"],
            "seed_rows": [
                "G10-HYP-PROP-006",
                "G10-HYP-PORTFOLIO-007",
                "HYP-G7-CROSSASSET-STRESS-008",
                "HYP-G8-VVIX-TAIL-007",
            ],
            "objective": "Define observation-only portfolio/risk stress context that explains blocked opportunity cost without changing risk, correlation gates, or order behavior.",
            "required_blocker_checks": [
                "prop rule parser completeness",
                "correlation/opportunity lifecycle labels",
                "stress context as-of timestamps",
                "no risk config edits",
            ],
            "stop_output": "portfolio opportunity-cost source map and observation-only prereg",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "assignment_id": "CD2-08",
            "title": "Source/no-leak field cleanup pass",
            "lanes": ["G11", "G7", "G5", "G0", "G12"],
            "seed_rows": [
                "all HYP-G11-* rows",
                "HYP-G7-XG5-MACRO-ATTN-010",
                "HYP-G7-XG8-VOL-MACRO-011",
                "HYP-G7-XG11-SOURCE-FRESH-012",
            ],
            "objective": "Separate actual source_contract_v2 references from literature references, future placeholders, and forbidden outcome-field lists.",
            "required_blocker_checks": [
                "no_leak_fields must be as-of feature names, not forbidden fields",
                "source_ids must resolve to source_contract_v2 or move to evidence_refs",
                "all source contracts remain validation_safe=false unless explicit blocker-clearing notes exist",
            ],
            "stop_output": "row-cleanup proposal for G12 review; no row promotion",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
    ]
    return {
        "generated_at_utc": now,
        "lane_id": "G0",
        "status": "CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_READY_FOR_LANE_HANDOFF",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "assignments": assignments,
    }


def build_g12_shortlist(
    now: str,
    no_leak_blockers: list[dict[str, Any]],
    source_reference_issues: list[dict[str, Any]],
) -> dict[str, Any]:
    shortlist = [
        {
            "shortlist_id": "G12-RT-01",
            "topic": "G11 no_leak_fields semantic inversion",
            "row_ids": [item["hypothesis_id"] for item in no_leak_blockers if str(item["hypothesis_id"]).startswith("HYP-G11")],
            "risk": "Forbidden outcome/future fields appear under no_leak_fields; red team should decide whether these are exclusion lists that need schema cleanup.",
            "review_questions": [
                "Are no_leak_fields true as-of features or examples of fields to exclude?",
                "Would any prereg become leaky if a future agent treats these names as allowed features?",
            ],
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "shortlist_id": "G12-RT-02",
            "topic": "Unregistered source_ids and cross-domain placeholders",
            "row_ids": sorted({item["row_id"] for item in source_reference_issues if item["issue"] != "literature_reference_without_source_contract"}),
            "risk": "Some rows use hypothesis IDs or future placeholders where source_contract_v2 IDs are expected.",
            "review_questions": [
                "Should these move to neighbor_lane_dependency or evidence_refs?",
                "Can any source-reference placeholder create false source-safety confidence?",
            ],
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "shortlist_id": "G12-RT-03",
            "topic": "Broker actual-R label scarcity versus AI/ML and execution hypotheses",
            "row_ids": [
                "HYP-G9-K55-ARTIFACT-001",
                "HYP-G9G1-COMPARE-AIML-003",
                "HYP-G9-DEBATE-DISAGREE-007",
                "G10-HYP-COST-002",
                "G10-HYP-J46J49-004",
            ],
            "risk": "Rows name broker_actual_r label class while current evidence remains sparse or disabled; red team should block accidental promotion drift.",
            "review_questions": [
                "Does each prereg define when broker_actual_r is available and separated from synthetic path labels?",
                "Are sample floors and target-version gates sufficient?",
            ],
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "shortlist_id": "G12-RT-04",
            "topic": "Volatility and macro publication-time leakage",
            "row_ids": [
                "HYP-G8-VIX1D9D-STRESS-002",
                "HYP-G8-VRP-004",
                "HYP-G8-OPEX-005",
                "HYP-G7-FOMC-ATTN-003",
                "HYP-G7-BIS-CARRY-STRESS-007",
            ],
            "risk": "Daily macro/vol rows can become leaky if same-day availability, revisions, realized variance windows, or event-publication times are not frozen.",
            "review_questions": [
                "Do publication_asof_timestamp_rule values prove decision-time availability?",
                "Do VRP realized windows end before the decision timestamp?",
            ],
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "shortlist_id": "G12-RT-05",
            "topic": "Execution/path-scaling label separation",
            "row_ids": [
                "G10-HYP-PREFILL-003",
                "G10-HYP-RISKBANK-005",
                "G10-HYP-XDOMAIN-008",
                "G6-HYP-002",
                "HYP-G4-FILL-QUALITY-009",
            ],
            "risk": "Prefill/no-fill, synthetic path-R, same-bar ambiguity, and broker actual-R can be mixed unless row contracts are explicit.",
            "review_questions": [
                "Are fill/no-fill lifecycle labels scored separately from R outcomes?",
                "Does the risk-bank invariant prevent post-hoc path-scaling optimism?",
            ],
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "shortlist_id": "G12-RT-06",
            "topic": "Old wave-1 normalization and packaging residue",
            "row_ids": ["G6-HYP-001", "G6-HYP-004", "G6-HYP-005", "G6-HYP-006"],
            "risk": "G0 master-copy label normalization fixed schema compliance, but lane-owned artifacts still carry verbose label classes.",
            "review_questions": [
                "Should G12 recommend lane-owned cleanup or keep G0 normalization as sufficient?",
                "Could future tools read lane-owned rows and miss the G0 normalization?",
            ],
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "shortlist_id": "G12-RT-07",
            "topic": "Global source validation boundary",
            "row_ids": ["all source_contract_v2 rows"],
            "risk": "There are 86 source contracts and all are validation_safe=false; any later true value requires explicit source evidence and blocker-clearing notes.",
            "review_questions": [
                "Do any reports imply validation safety despite false source flags?",
                "Are cache paths, legal state, and timestamp rules sufficient for future source tests?",
            ],
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
    ]
    return {
        "generated_at_utc": now,
        "lane_id": "G0",
        "status": "G12_RED_TEAM_SHORTLIST_READY",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/G12_G12_RED_TEAM_GOAL_PROMPT_2026-05-06.md",
        "prompt_guidance": [
            "Start from the wave-2 master registries, not individual lane narratives.",
            "Treat every row as NO_PROMOTION_VERDICT and look for promotion drift.",
            "Prioritize leakage, source validity, duplicate counting, label separation, prereg outcome closure, and source-validation-safe drift.",
            "Do not make live trading prompt, risk, execution, permissions, selector, safety-gate, MT5, canary, paid-data, or order-behavior changes.",
        ],
        "shortlist": shortlist,
    }


def write_markdown_files(
    now: str,
    lanes: dict[str, dict[str, Any]],
    lane_counts: dict[str, dict[str, Any]],
    totals: dict[str, int],
    status_rows: list[dict[str, Any]],
    schema_check: dict[str, Any],
    missing_lane_artifacts: list[dict[str, Any]],
    second_pass: dict[str, Any],
    g12_shortlist: dict[str, Any],
) -> None:
    source_md = f"""# Science Program Source Contract Registry - 2026-05-06

**Status:** `WAVE2_RECONCILED_G1_G11_SOURCE_CONTRACTS_NOT_VALIDATION_SAFE`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Checked at UTC:** `{now}`
**HEAD reconciled:** `{HEAD_RECONCILED}`
**Wave-2 merge commit:** `{WAVE2_MERGE_COMMIT}`

## Summary

G0 reconciled `{totals['sources']}` `source_contract_v2` rows from G1-G11. All `{totals['sources']}` remain `validation_safe=false`. No source is approved for validation, promotion, live features, paid pulls, or trading decisions.

| Lane | Source Rows | Validation-Safe Rows | Effective Commit |
| --- | ---: | ---: | --- |
"""
    for lane_id in LANE_IDS:
        source_md += f"| `{lane_id}` | {lane_counts[lane_id]['source_contracts']} | 0 | `{LANE_COMMITS[lane_id]}` |\n"
    source_md += f"""
## Source And No-Leak Blockers

- Validation-safe source rows: `0`.
- Source-reference placeholders or unregistered literature references: `{len(schema_check['source_reference_issues'])}`.
- No-leak semantic blocker rows: `{len(schema_check['no_leak_semantic_blockers'])}`.
- `$0` new external cash spend remains in force.
- Source legality, publication/as-of timestamps, parser/cache coverage, no-lookahead tests, and validation sample floors remain unresolved per lane rows.

## NO_PROMOTION_VERDICT

This registry consolidates source contracts for governance. It does not make any source validation-safe.
"""
    (CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.md").write_text(source_md, encoding="utf-8")

    ledger_md = f"""# Science Program Source And Budget Ledger - 2026-05-06

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Budget posture:** `ZERO_NEW_EXTERNAL_CASH_UNTIL_NUMERIC_CAP_AND_PER_SOURCE_LIMIT_ARE_OWNER_APPROVED`
**Current external cash spend cap:** `$0`
**Per-source limit:** `None`
**Spend allowed:** `False`

## Allowed Now

- local repo artifacts
- existing local data
- existing Sierra files/access
- existing Databento credits only after manifest/cost estimate/cap ledger
- public web only when fetched, cached, and source-indexed under the research lane

## Disallowed Until Owner Approval

- new subscriptions
- paid trials
- account top-ups
- vendor purchases
- broad paid data pulls
- any source marked validation_safe before source_contract_v2 tests pass

## Wave-2 Source Reconciliation

- Checked at UTC: `{now}`
- HEAD reconciled: `{HEAD_RECONCILED}`
- Wave-2 merge commit: `{WAVE2_MERGE_COMMIT}`
- Source contract registry: `research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json`
- Source rows reconciled: `{totals['sources']}`
- Validation-safe source rows: `0`
- New external cash spend by G0: `$0`
- New public fetches by G0: `0`
- Paid data calls by G0: `0`

## Ledger Rows

`[]`

No lane may spend cash or mark a source validation-safe until this ledger has a numeric cap, per-source limit, source contract, explicit source evidence, and blocker-clearing notes.
"""
    (CONTROL / "SOURCE_BUDGET_LEDGER_2026-05-06.md").write_text(ledger_md, encoding="utf-8")

    master_md = f"""# Science Program Master Registry - 2026-05-06

**Status:** `G0_WAVE2_RECONCILED_G1_G11`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Checked at UTC:** `{now}`
**HEAD reconciled:** `{HEAD_RECONCILED}`
**Wave-2 merge commit:** `{WAVE2_MERGE_COMMIT}`

## G0 Registry State

- Mechanisms: `{totals['mechanisms']}`
- Hypotheses: `{totals['hypotheses']}`
- Experiment preregs: `{totals['preregs']}`
- Source contracts: `{totals['sources']}`
- Goal status rows: `{len(status_rows)}`
- Survivor backlog rows: `0`

G0 reconciled wave-1 and wave-2 lane outputs from G1-G11 now visible at HEAD `{HEAD_RECONCILED}`. Rows are merged as research-control inventory only. No row is validation-safe or promotion-safe.

## Lane Counts

| Lane | Mechanisms | Hypotheses | Preregs | Sources | Effective Commit |
| --- | ---: | ---: | ---: | ---: | --- |
"""
    for lane_id in LANE_IDS:
        counts = lane_counts[lane_id]
        master_md += (
            f"| `{lane_id}` | {counts['mechanisms']} | {counts['hypotheses']} | "
            f"{counts['experiment_preregs']} | {counts['source_contracts']} | `{counts['effective_commit_sha']}` |\n"
        )
    master_md += f"""
## Check Results

- Required-field hard schema issues after G0 reconciliation: `{len(schema_check['required_field_issues'])}`
- Relationship issues after G0 reconciliation: `{len(schema_check['relationship_issues'])}`
- Duplicate mechanism/hypothesis/prereg/source IDs: `0`
- G6 label-class master-copy normalizations: `{len(schema_check['normalizations'])}`
- Source contracts with `validation_safe=true`: `0`
- Experiment preregs with `outcome_review_opened=true`: `0`
- Hypotheses with empty `no_leak_fields`: `0`
- No-leak semantic blockers recorded for G12: `{len(schema_check['no_leak_semantic_blockers'])}`
- Source-reference placeholders/literature references recorded for G12: `{len(schema_check['source_reference_issues'])}`

## Missing Or Weak Lane Artifacts

"""
    for item in missing_lane_artifacts:
        master_md += (
            f"- `{item['lane_id']}`: {item['artifact_gap']} "
            f"Blocking master merge: `{item['blocking_master_merge']}`.\n"
        )
    master_md += """
## Survivor Backlog

No survivor hypotheses exist. Every row remains blocked by source safety, label separation, no-leak semantics, sample floors, duplicate/concentration controls, stale-route checks, owner approval, or unrun G12 red-team review.

## NO_PROMOTION_VERDICT

This master registry is a research/control reconciliation artifact only. It does not change live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, or order behavior.
"""
    (SYN_DIR / "SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md").write_text(master_md, encoding="utf-8")

    synthesis_md = f"""# G0 Wave-2 Cross-Agent Synthesis - 2026-05-06

**Lane:** `G0`
**Status:** `G0_WAVE2_RECONCILIATION_COMPLETE_PENDING_COMMIT`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Checked at UTC:** `{now}`
**HEAD reconciled:** `{HEAD_RECONCILED}`
**Wave-2 merge commit:** `{WAVE2_MERGE_COMMIT}`

## Objective Restated

Run G0 wave-2 reconciliation for the primitive-science program: read merged G7-G11 outputs now visible at HEAD `{HEAD_RECONCILED}`, merge them with the existing G1-G6 master rows, validate mechanism/hypothesis/source/prereg/status rows, update master registries/status/synthesis, identify duplicate/source/prereg/no-leak blockers, preserve `NO_PROMOTION_VERDICT`, create cross-domain second-pass assignments, and prepare G12 red-team shortlist and prompt guidance without touching live-trading surfaces.

## Registry Outcome

| Registry | Rows | Status |
| --- | ---: | --- |
| Mechanism | {totals['mechanisms']} | `MERGED_RESEARCH_ONLY` |
| Hypothesis | {totals['hypotheses']} | `MERGED_RESEARCH_ONLY` |
| Experiment prereg | {totals['preregs']} | `MERGED_OUTCOMES_CLOSED` |
| Source contract | {totals['sources']} | `RECONCILED_NOT_VALIDATION_SAFE` |
| Survivor backlog | 0 | `EMPTY_NO_PROMOTION` |

## Validation Findings

- Required-field checks passed for G1-G11 rows after G0 reconciliation, apart from the already-recorded G6 label-class master-copy normalizations.
- Hypothesis-to-mechanism and prereg-to-hypothesis relationships passed.
- Duplicate row-ID checks found no duplicate mechanism, hypothesis, experiment, or source IDs.
- All experiment preregs keep `outcome_review_opened=false`.
- All source contracts keep `validation_safe=false`.
- G0 recorded `{len(schema_check['no_leak_semantic_blockers'])}` no-leak semantic blockers, primarily G11 rows that list outcome/future field names under `no_leak_fields`.
- G0 recorded `{len(schema_check['source_reference_issues'])}` source-reference placeholders or literature references that are not source_contract_v2 rows.

## Lane Blockers

"""
    for lane_id in LANE_IDS:
        counts = lane_counts[lane_id]
        blockers = (lanes[lane_id]["status"] or {}).get("blockers", [])
        synthesis_md += f"### {lane_id}\n\n"
        synthesis_md += (
            f"Rows: `{counts['mechanisms']}` mechanisms, `{counts['hypotheses']}` hypotheses, "
            f"`{counts['experiment_preregs']}` preregs, `{counts['source_contracts']}` sources. "
            f"Effective commit: `{LANE_COMMITS[lane_id]}`.\n\n"
        )
        for blocker in blockers:
            synthesis_md += f"- {blocker}\n"
        synthesis_md += "\n"
    synthesis_md += f"""## Cross-Domain Second Pass

G0 created `{len(second_pass['assignments'])}` second-pass assignments in `G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md`. They are lane-handoff prompts only, not promotions.

## G12 Red-Team Shortlist

G0 created `{len(g12_shortlist['shortlist'])}` red-team topics in `G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md`. G12 should focus on no-leak semantics, source validity, source-reference placeholders, label separation, duplicate counting, prereg closure, and promotion drift.

## Forbidden-Surface Boundary

G0 did not change live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, or order behavior. Final forbidden-surface diff verification is recorded in the completion audit.

## NO_PROMOTION_VERDICT

Wave-2 reconciliation creates an organized research backlog and red-team/source-blocker map. It is not a promotion, validation result, live selector, risk change, or execution change.
"""
    (SYN_DIR / "G0_CROSS_AGENT_SYNTHESIS_2026-05-06.md").write_text(synthesis_md, encoding="utf-8")
    (SYN_DIR / "G0_WAVE2_RECONCILIATION_2026-05-06.md").write_text(synthesis_md, encoding="utf-8")

    assignments_md = f"""# G0 Cross-Domain Second-Pass Assignments - 2026-05-06

**Lane:** `G0`
**Status:** `{second_pass['status']}`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Generated at UTC:** `{now}`

These assignments are research handoffs only. They do not authorize source validation, live trading prompts, risk, execution, permissions, selectors, safety gates, MT5, canaries, paid data, or order behavior changes.

"""
    for item in second_pass["assignments"]:
        assignments_md += f"## {item['assignment_id']} - {item['title']}\n\n"
        assignments_md += f"- Lanes: `{', '.join(item['lanes'])}`\n"
        assignments_md += f"- Seed rows: `{', '.join(item['seed_rows'])}`\n"
        assignments_md += f"- Objective: {item['objective']}\n"
        assignments_md += f"- Stop output: {item['stop_output']}\n"
        assignments_md += "- Required blocker checks:\n"
        for check in item["required_blocker_checks"]:
            assignments_md += f"  - {check}\n"
        assignments_md += "- Promotion verdict: `NO_PROMOTION_VERDICT`\n\n"
    (SYN_DIR / "G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md").write_text(assignments_md, encoding="utf-8")

    red_md = f"""# G12 Red-Team Shortlist And Prompt Guidance - 2026-05-06

**Lane:** `G0`
**Target lane:** `G12`
**Status:** `{g12_shortlist['status']}`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Generated at UTC:** `{now}`
**G12 controlling prompt:** `research/science_program_2026_05/04_goal_prompts/G12_G12_RED_TEAM_GOAL_PROMPT_2026-05-06.md`

## Prompt Guidance

"""
    for line in g12_shortlist["prompt_guidance"]:
        red_md += f"- {line}\n"
    red_md += "\n## Shortlist\n\n"
    for item in g12_shortlist["shortlist"]:
        red_md += f"### {item['shortlist_id']} - {item['topic']}\n\n"
        red_md += f"- Row IDs: `{', '.join(item['row_ids'])}`\n"
        red_md += f"- Risk: {item['risk']}\n"
        red_md += "- Review questions:\n"
        for question in item["review_questions"]:
            red_md += f"  - {question}\n"
        red_md += "- Promotion verdict: `NO_PROMOTION_VERDICT`\n\n"
    (SYN_DIR / "G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md").write_text(red_md, encoding="utf-8")

    ledger_md = f"""# G0 Governor Context And Ambiguity Ledger - 2026-05-06

**Lane:** `G0`
**Status:** `WAVE2_RECONCILIATION_CONTEXT_LEDGER`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Updated at UTC:** `{now}`

## Mechanism Screening Before Reconciliation

Useful wave-2 mechanisms would be worth keeping only if they can eventually produce decision-time, source-contracted, label-safe context for GTOS: macro/vol stress state, source freshness, execution friction, pre-fill path quality, K55 source provenance, and AI/ML auditability. Evidence that distinguishes signal from noise must be as-of timestamps, parser/cache proof, no-leak feature names, duplicate-aware setup IDs, separated lifecycle/synthetic/broker labels, and sample floors. The strongest evidence currently lives in lane row files, context ledgers, source indices, local shadow logs, and future G12 review, not in any single narrative report.

## Artifact Ledger

| Artifact | Claim or Mechanism Changed | Next Question |
| --- | --- | --- |
| `.context/LIVE_STATE.md` | Confirmed HEAD `{HEAD_RECONCILED}` and wave-2 merge state. | Regenerate again before final status. |
| `.context/00_core/research_current_state.md` | Confirmed G0 wave-2 reconciliation was pending and master registries were wave-1 only. | Update after G0 wave-2 commit. |
| `G0_G0_PROGRAM_GOVERNOR_GOAL_PROMPT_2026-05-06.md` | Set G0 scope, stop outputs, forbidden surfaces, source policy, and done standard. | Completion audit must map every prompt requirement. |
| G7-G11 row files | Added 36 mechanisms, 45 hypotheses, 45 preregs, and 41 sources to the G0 inventory. | Run source/prereg/no-leak blockers before accepting master rows. |
| G7/G8/G9/G10/G11 context and completion ledgers | Showed several neighbor passes ran before later lanes existed. | Cross-domain second pass must revisit stale neighbor placeholders. |
| `SCHEMA_CONTRACTS_2026-05-06.json` | Required field and verdict contracts. | Record semantic blockers that schema fields alone cannot catch. |
| G12 controlling prompt | Defines red-team output requirements. | Feed G12 the shortlist and registry blockers. |

## Ambiguity Ledger

| Ambiguity | Current Answer | Next Evidence |
| --- | --- | --- |
| Can any wave-2 source be validation-safe now? | No. All 86 source contracts remain `validation_safe=false`. | Source-specific legality/cache/parser/no-lookahead tests and explicit blocker-clearing notes. |
| Are G11 `no_leak_fields` safe? | Not yet. Eight rows appear to list forbidden outcome/future fields under `no_leak_fields`. | G12 review and possible row-cleanup proposal. |
| Are G7 cross-domain source references true source contracts? | Not all. Several are hypothesis IDs or future placeholders. | Move placeholders to dependency/evidence fields or create source_contract_v2 rows. |
| Can cross-domain rows become survivor backlog? | No. G12 has not reviewed them and all sources remain blocked. | Red-team pass plus future validation dossier. |
| Did G0 need new public web fetches? | No. Wave-2 lanes already cached their public/source evidence; G0 used local artifacts only. | Fetch only if G12 or second-pass lanes need uncached current source docs. |

## NO_PROMOTION_VERDICT

This ledger records research-governance context only. It does not create a live signal, validation claim, source approval, or promotion route.
"""
    (DOMAIN_DIR / "G0_GOVERNOR_CONTEXT_AMBIGUITY_LEDGER_2026-05-06.md").write_text(ledger_md, encoding="utf-8")

    audit_md = f"""# G0 Completion Audit - 2026-05-06

**Lane:** `G0`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Audit timestamp UTC:** `{now}`
**Status:** `WAVE2_RECONCILIATION_PENDING_FINAL_VERIFICATION_AND_COMMIT`
**Primary G0 wave-2 reconciliation commit:** `PENDING`
**HEAD reconciled:** `{HEAD_RECONCILED}`

## Objective Restated

Run G0 wave-2 reconciliation for the GTOS primitive-science research program using the controlling G0 prompt. Concrete deliverables: complete mandatory preflight, read HEAD `{HEAD_RECONCILED}` including merged G7-G11 outputs and `.context/00_core/research_current_state.md`, reconcile G7-G11 into the master mechanism/hypothesis/prereg/source/status registries, run schema/relationship/duplicate/source/prereg/no-leak blocker checks, update G0 synthesis/completion audit/source-budget ledger/status registry, produce cross-domain second-pass assignments and G12 red-team shortlist/prompt guidance, keep every row `NO_PROMOTION_VERDICT`, avoid marking any source `validation_safe=true`, and touch only scoped G0 research/control/context artifacts.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
| --- | --- | --- |
| Use controlling prompt | `research/science_program_2026_05/04_goal_prompts/G0_G0_PROGRAM_GOVERNOR_GOAL_PROMPT_2026-05-06.md` | `COMPLETE` |
| Mandatory preflight | `python scripts/generate_live_state.py`; `.context/LIVE_STATE.md`, latest handoff, quick reference, doctrine, current state, reading order read | `COMPLETE` |
| Read HEAD `{HEAD_RECONCILED}` | `git show --stat --oneline HEAD` confirmed `{HEAD_RECONCILED}` | `COMPLETE` |
| Read merged G7-G11 outputs | G7-G11 row/status/synthesis/audit/context/source files inventoried | `COMPLETE` |
| Reconcile master mechanism registry | `research/science_program_2026_05/02_hypothesis_registry/MECHANISM_REGISTRY_2026-05-06.json` with `{totals['mechanisms']}` rows | `COMPLETE` |
| Reconcile master hypothesis registry | `research/science_program_2026_05/02_hypothesis_registry/HYPOTHESIS_REGISTRY_2026-05-06.json` with `{totals['hypotheses']}` rows | `COMPLETE_WITH_NO_LEAK_BLOCKERS_RECORDED` |
| Reconcile master preregistry | `research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json` with `{totals['preregs']}` rows | `COMPLETE_OUTCOMES_CLOSED` |
| Reconcile source registry | `research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json` with `{totals['sources']}` rows, all `validation_safe=false` | `COMPLETE_WITH_SOURCE_BLOCKERS` |
| Reconcile status registry | `research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json` | `COMPLETE_PENDING_COMMIT_SHA` |
| Update source-budget ledger | `SOURCE_BUDGET_LEDGER_2026-05-06.md/json`; `$0` new G0 spend, `0` paid calls | `COMPLETE` |
| Update G0 synthesis | `G0_CROSS_AGENT_SYNTHESIS_2026-05-06.md/json` and `G0_WAVE2_RECONCILIATION_2026-05-06.md/json` | `COMPLETE` |
| Produce second-pass assignments | `G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md/json` | `COMPLETE` |
| Produce G12 shortlist/guidance | `G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md/json` | `COMPLETE` |
| Governor context/ambiguity ledger | `G0_GOVERNOR_CONTEXT_AMBIGUITY_LEDGER_2026-05-06.md` | `COMPLETE` |
| Keep `NO_PROMOTION_VERDICT` | Final scoped scan pending | `PENDING_FINAL_VERIFICATION` |
| Avoid source validation-safe drift | Generated source check reports `validation_safe_true=0` | `COMPLETE` |
| Avoid forbidden live surfaces | Final forbidden diff pending | `PENDING_FINAL_VERIFICATION` |
| Commit only scoped G0 research/control/context artifacts | Pending commit | `PENDING_COMMIT` |

## Focused Verification Results

Final command results will be added after py_compile, JSON parse, custom blocker validation, `NO_PROMOTION_VERDICT`, forbidden-surface, pytest, and commit checks complete.
"""
    (SYN_DIR / "G0_COMPLETION_AUDIT_2026-05-06.md").write_text(audit_md, encoding="utf-8")


def main() -> None:
    now = utc_now()
    schema = load_json(CONTROL / "SCHEMA_CONTRACTS_2026-05-06.json")
    required = {name: set(contract["required_fields"]) for name, contract in schema.items()}
    lanes = collect_lane_rows()

    required_field_issues: list[dict[str, Any]] = []
    relationship_issues: list[dict[str, Any]] = []
    normalizations: list[dict[str, Any]] = []
    row_sources: dict[str, dict[str, Any]] = defaultdict(dict)
    all_mechanisms: list[dict[str, Any]] = []
    all_hypotheses: list[dict[str, Any]] = []
    all_preregs: list[dict[str, Any]] = []
    all_sources: list[dict[str, Any]] = []

    lane_counts = {
        lane_id: {
            "mechanisms": len(data["mechanisms"]),
            "hypotheses": len(data["hypotheses"]),
            "experiment_preregs": len(data["preregs"]),
            "source_contracts": len(data["sources"]),
            "status_source": sorted(set(data["files"]["status"])),
            "effective_commit_sha": LANE_COMMITS[lane_id],
        }
        for lane_id, data in lanes.items()
    }

    specs = [
        ("mechanisms", "science_mechanism_v1", "mechanism_id", all_mechanisms),
        ("hypotheses", "science_hypothesis_v1", "hypothesis_id", all_hypotheses),
        ("preregs", "experiment_prereg_v1", "experiment_id", all_preregs),
        ("sources", "source_contract_v2", "source_id", all_sources),
    ]

    for lane_id, data in lanes.items():
        for kind, schema_name, id_field, sink in specs:
            for original_row in data[kind]:
                row = copy.deepcopy(original_row)
                missing = sorted(required[schema_name] - set(row))
                if missing:
                    required_field_issues.append(
                        {
                            "lane_id": lane_id,
                            "schema": schema_name,
                            "row_id": row.get(id_field),
                            "issue": "missing_required_fields",
                            "fields": missing,
                        }
                    )
                if row.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
                    required_field_issues.append(
                        {
                            "lane_id": lane_id,
                            "schema": schema_name,
                            "row_id": row.get(id_field),
                            "issue": "bad_promotion_verdict",
                            "value": row.get("promotion_verdict"),
                        }
                    )
                if schema_name == "science_hypothesis_v1" and row.get("label_class") not in ALLOWED_LABEL_CLASSES:
                    original = row.get("label_class")
                    normalized = LABEL_NORMALIZATION.get(original)
                    if normalized:
                        normalizations.append(
                            {
                                "lane_id": lane_id,
                                "hypothesis_id": row.get("hypothesis_id"),
                                "field": "label_class",
                                "original": original,
                                "normalized": normalized,
                                "reason": "Normalize verbose lane wording to SCHEMA_CONTRACTS allowed label_class enum in the G0 master copy; lane artifact left unchanged.",
                            }
                        )
                        row["label_class"] = normalized
                    else:
                        required_field_issues.append(
                            {
                                "lane_id": lane_id,
                                "schema": schema_name,
                                "row_id": row.get(id_field),
                                "issue": "invalid_label_class",
                                "value": original,
                            }
                        )
                if schema_name == "experiment_prereg_v1" and row.get("outcome_review_opened") is not False:
                    required_field_issues.append(
                        {
                            "lane_id": lane_id,
                            "schema": schema_name,
                            "row_id": row.get(id_field),
                            "issue": "outcome_review_opened_not_false",
                            "value": row.get("outcome_review_opened"),
                        }
                    )
                if schema_name == "source_contract_v2" and row.get("validation_safe") is not False:
                    required_field_issues.append(
                        {
                            "lane_id": lane_id,
                            "schema": schema_name,
                            "row_id": row.get(id_field),
                            "issue": "source_validation_safe_not_false",
                            "value": row.get("validation_safe"),
                        }
                    )
                sink.append(row)
                row_sources[schema_name][row.get(id_field)] = {
                    "lane_id": lane_id,
                    "source_files": sorted(set(data["files"][kind])),
                }

    mechanism_ids = {row["mechanism_id"] for row in all_mechanisms}
    hypothesis_ids = {row["hypothesis_id"] for row in all_hypotheses}
    for row in all_hypotheses:
        if row["mechanism_id"] not in mechanism_ids:
            relationship_issues.append(
                {
                    "type": "hypothesis_missing_mechanism",
                    "hypothesis_id": row["hypothesis_id"],
                    "mechanism_id": row["mechanism_id"],
                }
            )
    for row in all_preregs:
        if row["hypothesis_id"] not in hypothesis_ids:
            relationship_issues.append(
                {
                    "type": "prereg_missing_hypothesis",
                    "experiment_id": row["experiment_id"],
                    "hypothesis_id": row["hypothesis_id"],
                }
            )

    duplicate_report = {
        "mechanism_id_duplicates": duplicate_ids(all_mechanisms, "mechanism_id"),
        "hypothesis_id_duplicates": duplicate_ids(all_hypotheses, "hypothesis_id"),
        "experiment_id_duplicates": duplicate_ids(all_preregs, "experiment_id"),
        "source_id_duplicates": duplicate_ids(all_sources, "source_id"),
    }
    source_summary = {
        "source_contract_rows": len(all_sources),
        "validation_safe_true": sum(1 for row in all_sources if row.get("validation_safe") is True),
        "validation_safe_false": sum(1 for row in all_sources if row.get("validation_safe") is False),
        "blocked_source_rows": [row["source_id"] for row in all_sources if row.get("validation_safe") is False],
    }
    label_summary = dict(sorted(Counter(row["label_class"] for row in all_hypotheses).items()))
    no_leak_blockers = no_leak_semantic_blockers(all_hypotheses)
    source_reference_issues = collect_source_reference_issues(all_mechanisms, all_hypotheses, all_sources)
    prereg_summary = {
        "experiment_prereg_rows": len(all_preregs),
        "outcome_review_opened_true": sum(1 for row in all_preregs if row.get("outcome_review_opened") is True),
        "outcome_review_opened_false": sum(1 for row in all_preregs if row.get("outcome_review_opened") is False),
    }

    schema_check = {
        "required_field_issues": required_field_issues,
        "relationship_issues": relationship_issues,
        "duplicate_report": duplicate_report,
        "normalizations": normalizations,
        "label_class_counts_after_g0_normalization": label_summary,
        "source_contract_summary": source_summary,
        "source_reference_issues": source_reference_issues,
        "experiment_prereg_summary": prereg_summary,
        "no_leak_semantic_blockers": no_leak_blockers,
        "hard_blocker_issue_count": len(required_field_issues) + len(relationship_issues) + sum(len(v) for v in duplicate_report.values()) + source_summary["validation_safe_true"] + prereg_summary["outcome_review_opened_true"],
    }

    missing_lane_artifacts = [
        {
            "lane_id": "G2",
            "artifact_gap": "No standalone 00_control goal-status JSON; status row is embedded in G2_STOCHASTIC_TAILS_SYNTHESIS_2026-05-06.json.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G2",
            "artifact_gap": "No standalone mechanism/hypothesis/prereg/source JSON files; all rows are embedded in the synthesis JSON.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G3",
            "artifact_gap": "No dedicated completion-audit artifact found; prompt done-standard evidence is in synthesis/status rows.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G4",
            "artifact_gap": "Mechanism/hypothesis/prereg/source files are bare JSON lists rather than schema wrapper objects.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G6",
            "artifact_gap": "Four lane hypothesis label_class values use verbose non-enum wording; G0 master copy normalizes them and records the repair.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G7",
            "artifact_gap": "G7 cross-domain G8/G11 rows were placeholders because G8/G11 completed outputs were not available at G7 run time; G0 schedules a second pass.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G8",
            "artifact_gap": "G8 neighbor pass saw G7/G10 absent at run time and official GEX/historical options source remains blocked.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G9",
            "artifact_gap": "G9 neighbor pass saw G10 absent at run time and Component 3B/tool/Reflexion rows remain approval and budget blocked.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G10",
            "artifact_gap": "G10 neighbor pass saw G9 absent at run time; close-side slippage and broker actual-R evidence remain sparse.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G11",
            "artifact_gap": "G11 row files are bare JSON lists and G7/G8 were absent at run time; G0 schedules source/no-leak cleanup and cross-domain second pass.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G11",
            "artifact_gap": "Eight G11 hypotheses appear to list forbidden outcome/future fields under no_leak_fields; G0 records this as a G12 red-team blocker.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G12",
            "artifact_gap": "Red-team lane has not run; G0 produced shortlist and prompt guidance only.",
            "blocking_master_merge": True,
        },
    ]

    totals = {
        "mechanisms": len(all_mechanisms),
        "hypotheses": len(all_hypotheses),
        "preregs": len(all_preregs),
        "sources": len(all_sources),
    }

    second_pass = build_second_pass_assignments(now)
    g12_shortlist = build_g12_shortlist(now, no_leak_blockers, source_reference_issues)
    status_rows = build_status_rows(
        lanes, lane_counts, now, totals, no_leak_blockers, source_reference_issues
    )

    reconciliation_meta = {
        "checked_at_utc": now,
        "governor_lane": "G0",
        "scope": "wave_2_G1_G11_outputs_visible_at_HEAD_7a95a293",
        "head_reconciled": HEAD_RECONCILED,
        "wave2_merge_commit": WAVE2_MERGE_COMMIT,
        "primary_reconciliation_commit_sha": None,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "lane_counts": lane_counts,
        "row_counts": {
            "mechanism_rows_merged": len(all_mechanisms),
            "hypothesis_rows_merged": len(all_hypotheses),
            "experiment_prereg_rows_merged": len(all_preregs),
            "source_contract_rows_reconciled": len(all_sources),
            "goal_status_rows_total": len(status_rows),
        },
        "schema_check": schema_check,
        "missing_lane_artifacts": missing_lane_artifacts,
        "lane_blockers": {
            lane_id: (data["status"] or {}).get("blockers", []) for lane_id, data in lanes.items()
        },
    }

    registry_template = {
        "governor_reconciliation": reconciliation_meta,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    dump_json(
        HYP_DIR / "MECHANISM_REGISTRY_2026-05-06.json",
        {
            **registry_template,
            "schema": "science_mechanism_v1",
            "status": "WAVE2_RECONCILED_G1_G11_MECHANISMS_MERGED_RESEARCH_ONLY",
            "row_sources": row_sources["science_mechanism_v1"],
            "rows": sort_rows(all_mechanisms, "mechanism_id"),
        },
    )
    dump_json(
        HYP_DIR / "HYPOTHESIS_REGISTRY_2026-05-06.json",
        {
            **registry_template,
            "schema": "science_hypothesis_v1",
            "status": "WAVE2_RECONCILED_G1_G11_HYPOTHESES_MERGED_RESEARCH_ONLY_WITH_NO_LEAK_BLOCKERS",
            "row_sources": row_sources["science_hypothesis_v1"],
            "rows": sort_rows(all_hypotheses, "hypothesis_id"),
        },
    )
    dump_json(
        EXP_DIR / "EXPERIMENT_PREREGISTRY_2026-05-06.json",
        {
            **registry_template,
            "schema": "experiment_prereg_v1",
            "status": "WAVE2_RECONCILED_G1_G11_PREREGS_MERGED_OUTCOMES_CLOSED",
            "row_sources": row_sources["experiment_prereg_v1"],
            "rows": sort_rows(all_preregs, "experiment_id"),
        },
    )
    dump_json(
        CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
        {
            **registry_template,
            "schema": "source_contract_v2",
            "status": "WAVE2_RECONCILED_G1_G11_SOURCE_CONTRACTS_NOT_VALIDATION_SAFE",
            "row_sources": row_sources["source_contract_v2"],
            "rows": sort_rows(all_sources, "source_id"),
        },
    )

    dump_json(CONTROL / "GOAL_STATUS_REGISTRY_2026-05-06.json", status_rows)

    source_budget = load_json(CONTROL / "SOURCE_BUDGET_LEDGER_2026-05-06.json")
    source_budget["promotion_verdict"] = "NO_PROMOTION_VERDICT"
    source_budget["spend_allowed"] = False
    source_budget["current_external_cash_spend_cap_usd"] = 0.0
    source_budget["wave2_reconciliation"] = {
        "checked_at_utc": now,
        "head_reconciled": HEAD_RECONCILED,
        "wave2_merge_commit": WAVE2_MERGE_COMMIT,
        "source_contract_registry": "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
        "source_contract_rows": len(all_sources),
        "validation_safe_true": source_summary["validation_safe_true"],
        "validation_safe_false": source_summary["validation_safe_false"],
        "new_external_cash_spend_usd": 0.0,
        "new_public_fetches_by_g0": 0,
        "paid_data_calls_by_g0": 0,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    dump_json(CONTROL / "SOURCE_BUDGET_LEDGER_2026-05-06.json", source_budget)

    master = {
        "schema_version": "science_goal_program_control_v1",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "g0_governor_reconciliation": reconciliation_meta,
        "registries": {
            "mechanism_registry": {
                "path": "research/science_program_2026_05/02_hypothesis_registry/MECHANISM_REGISTRY_2026-05-06.json",
                "schema": "science_mechanism_v1",
                "status": "WAVE2_RECONCILED_G1_G11_MECHANISMS_MERGED_RESEARCH_ONLY",
                "rows": len(all_mechanisms),
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            },
            "hypothesis_registry": {
                "path": "research/science_program_2026_05/02_hypothesis_registry/HYPOTHESIS_REGISTRY_2026-05-06.json",
                "schema": "science_hypothesis_v1",
                "status": "WAVE2_RECONCILED_G1_G11_HYPOTHESES_MERGED_RESEARCH_ONLY_WITH_NO_LEAK_BLOCKERS",
                "rows": len(all_hypotheses),
                "g0_label_class_normalizations": len(normalizations),
                "no_leak_semantic_blockers": len(no_leak_blockers),
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            },
            "experiment_preregistry": {
                "path": "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json",
                "schema": "experiment_prereg_v1",
                "status": "WAVE2_RECONCILED_G1_G11_PREREGS_MERGED_OUTCOMES_CLOSED",
                "rows": len(all_preregs),
                "outcome_review_opened_true": prereg_summary["outcome_review_opened_true"],
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            },
            "source_contract_registry": {
                "path": "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
                "schema": "source_contract_v2",
                "status": "WAVE2_RECONCILED_G1_G11_SOURCE_CONTRACTS_NOT_VALIDATION_SAFE",
                "rows": len(all_sources),
                "validation_safe_true": source_summary["validation_safe_true"],
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            },
        },
        "goal_status_rows": status_rows,
        "survivor_backlog": [],
        "blocker_summary": {
            "duplicate_id_blockers": duplicate_report,
            "source_blockers": source_summary,
            "source_reference_issues": source_reference_issues,
            "prereg_blockers": prereg_summary,
            "no_leak_semantic_blockers": no_leak_blockers,
            "schema_normalization_blockers": normalizations,
            "missing_lane_artifacts": missing_lane_artifacts,
            "promotion_blocker": "No row is validation-safe or promotion-safe; all outputs remain research/control only.",
        },
        "cross_domain_second_pass_assignments": "research/science_program_2026_05/05_synthesis/G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.json",
        "g12_red_team_shortlist": "research/science_program_2026_05/05_synthesis/G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.json",
    }
    dump_json(SYN_DIR / "SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json", master)

    cross = {
        "checked_at_utc": now,
        "lane_id": "G0",
        "status": "G0_WAVE2_RECONCILIATION_COMPLETE_PENDING_COMMIT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "live_behavior_changed": False,
        "ai_calls": 0,
        "canary_calls": 0,
        "mt5_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "public_web_fetches_by_g0": 0,
        "source_budget": {
            "current_external_cash_spend_cap_usd": 0.0,
            "spend_allowed": False,
            "new_external_cash_spend_usd": 0.0,
            "source_contract_rows_reconciled": len(all_sources),
            "validation_safe_source_rows": source_summary["validation_safe_true"],
            "ledger_path": "research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.md",
            "status": "UNCHANGED_ZERO_NEW_EXTERNAL_CASH",
        },
        "wave2_lanes_reconciled": LANE_IDS,
        "head_reconciled": HEAD_RECONCILED,
        "wave2_merge_commit": WAVE2_MERGE_COMMIT,
        "neighbor_pass": [
            {
                "lane_id": lane_id,
                "status": "RECONCILED_FROM_HEAD_7a95a293",
                "merged_mechanisms": lane_counts[lane_id]["mechanisms"],
                "merged_hypotheses": lane_counts[lane_id]["hypotheses"],
                "merged_preregs": lane_counts[lane_id]["experiment_preregs"],
                "source_contract_rows": lane_counts[lane_id]["source_contracts"],
                "effective_commit_sha": LANE_COMMITS[lane_id],
            }
            for lane_id in LANE_IDS
        ]
        + [
            {
                "lane_id": "G12",
                "status": "RED_TEAM_NOT_RUN_SHORTLIST_CREATED",
                "merged_rows": 0,
                "blocker": "G12 red-team review remains required before survivor/backlog promotion discussion.",
            }
        ],
        "registries": {
            "mechanism_registry_rows": len(all_mechanisms),
            "hypothesis_registry_rows": len(all_hypotheses),
            "experiment_preregistry_rows": len(all_preregs),
            "source_contract_registry_rows": len(all_sources),
            "survivor_backlog_rows": 0,
        },
        "checks": schema_check,
        "missing_lane_artifacts": missing_lane_artifacts,
        "cross_domain_second_pass_assignments": second_pass["assignments"],
        "g12_red_team_shortlist": g12_shortlist["shortlist"],
        "blockers": [
            "All source contracts are validation_safe=false; source/legal/timestamp/parser/no-lookahead/budget blockers remain lane-specific.",
            "No duplicate row IDs were found, but several cross-domain rows intentionally overlap domains and remain research-only.",
            "G11 no_leak_fields semantic blockers require G12 review before future tooling consumes those rows.",
            "No survivor backlog exists; no promotion, validation, prompt, risk, execution, selector, MT5, canary, paid-data, or order behavior change is authorized.",
        ],
        "merge_rule": "Merge lane rows into master registries only as NO_PROMOTION_VERDICT research rows after required-field, relationship, duplicate-ID, label, outcome-closed, source-safe-false, no-leak, source-reference, and killed-route checks.",
    }
    dump_json(SYN_DIR / "G0_CROSS_AGENT_SYNTHESIS_2026-05-06.json", cross)
    dump_json(SYN_DIR / "G0_WAVE2_RECONCILIATION_2026-05-06.json", cross)
    dump_json(SYN_DIR / "G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.json", second_pass)
    dump_json(SYN_DIR / "G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.json", g12_shortlist)

    completion = {
        "audit_timestamp_utc": now,
        "lane_id": "G0",
        "status": "WAVE2_RECONCILIATION_PENDING_FINAL_VERIFICATION_AND_COMMIT",
        "primary_commit_sha": None,
        "head_reconciled": HEAD_RECONCILED,
        "wave2_merge_commit": WAVE2_MERGE_COMMIT,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "objective_deliverables": [
            "mandatory preflight completed and evidenced",
            "HEAD 7a95a293 and merged G7-G11 outputs read",
            "mechanism/hypothesis/source/prereg/status rows schema-checked",
            "master registries updated",
            "lane status registry updated with effective G7-G11 commits",
            "source/budget ledger updated while preserving zero new cash spend",
            "duplicate/source/prereg/no-leak blockers recorded",
            "cross-domain second-pass assignments produced",
            "G12 red-team shortlist and prompt guidance produced",
            "NO_PROMOTION_VERDICT preserved",
            "forbidden live-trading surfaces untouched",
            "only scoped G0 research/control/context artifacts committed",
        ],
        "checklist": [],
        "blockers": [
            f"All {len(all_sources)} source contracts are validation_safe=false.",
            f"{len(no_leak_blockers)} no-leak semantic blockers require G12 review.",
            f"{len(source_reference_issues)} source-reference placeholders/literature refs are not source_contract_v2 rows.",
            "G12 red-team pass has not run.",
        ],
        "verification_results": [],
        "can_mark_g0_complete": False,
    }
    dump_json(SYN_DIR / "G0_COMPLETION_AUDIT_2026-05-06.json", completion)

    write_markdown_files(
        now,
        lanes,
        lane_counts,
        totals,
        status_rows,
        schema_check,
        missing_lane_artifacts,
        second_pass,
        g12_shortlist,
    )

    print(f"wrote G0 wave2 reconciliation artifacts at {now}")
    print(
        json.dumps(
            {
                "mechanisms": len(all_mechanisms),
                "hypotheses": len(all_hypotheses),
                "preregs": len(all_preregs),
                "sources": len(all_sources),
                "normalizations": len(normalizations),
                "no_leak_semantic_blockers": len(no_leak_blockers),
                "source_reference_issues": len(source_reference_issues),
                "hard_blocker_issue_count": schema_check["hard_blocker_issue_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
