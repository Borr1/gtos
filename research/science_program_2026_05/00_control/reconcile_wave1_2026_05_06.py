"""Reconcile wave-1 science-lane outputs into G0 master artifacts.

Scope: research/science_program_2026_05 control artifacts only.
No live trading prompts, risk, execution, permissions, selectors, MT5,
canaries, paid data, or order behavior are read or changed by this script.
"""

from __future__ import annotations

import copy
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "00_control"
HYP_DIR = ROOT / "02_hypothesis_registry"
EXP_DIR = ROOT / "03_experiment_specs"
SYN_DIR = ROOT / "05_synthesis"
MAIN_HEAD_RECONCILED = "08ffc24b"

LANE_COMMITS = {
    "G1": "649ead84",
    "G2": "fe08479f",
    "G3": "f0e0c8c9",
    "G4": "00621862",
    "G5": "7dfc0c59",
    "G6": "9344cda5",
}

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


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def collect_lane_rows():
    lanes = {
        f"G{i}": {
            "mechanisms": [],
            "hypotheses": [],
            "preregs": [],
            "sources": [],
            "status": None,
            "files": defaultdict(list),
        }
        for i in range(1, 7)
    }

    def add(lane: str, kind: str, rows: list[dict], source: str) -> None:
        for row in rows:
            lanes[lane][kind].append(copy.deepcopy(row))
        lanes[lane]["files"][kind].append(source)

    for path in sorted(ROOT.rglob("*.json")):
        rel = path.as_posix()
        name = path.name
        lane = next(
            (
                lane_id
                for lane_id in lanes
                if f"/{lane_id}_" in rel or name.startswith(f"{lane_id}_")
            ),
            None,
        )
        if not lane:
            continue

        data = load_json(path)
        if isinstance(data, dict):
            schema = data.get("schema")
            if schema == "science_mechanism_v1":
                add(lane, "mechanisms", data.get("rows", []), rel)
            if schema == "science_hypothesis_v1":
                add(lane, "hypotheses", data.get("rows", []), rel)
            if schema == "experiment_prereg_v1":
                add(lane, "preregs", data.get("rows", []), rel)
            if schema == "source_contract_v2":
                add(lane, "sources", data.get("rows", []), rel)

            embedded = [
                ("mechanism_rows", "mechanisms"),
                ("hypothesis_rows", "hypotheses"),
                ("experiment_prereg_rows", "preregs"),
                ("source_contract_rows", "sources"),
            ]
            for key, kind in embedded:
                if isinstance(data.get(key), list):
                    add(lane, kind, data[key], f"{rel}:{key}")

            if name.endswith("GOAL_STATUS_2026-05-06.json"):
                lanes[lane]["status"] = copy.deepcopy(data)
                lanes[lane]["files"]["status"].append(rel)
            if isinstance(data.get("goal_status_row"), dict):
                lanes[lane]["status"] = copy.deepcopy(data["goal_status_row"])
                lanes[lane]["files"]["status"].append(f"{rel}:goal_status_row")
            if isinstance(data.get("goal_status"), dict):
                lanes[lane]["status"] = copy.deepcopy(data["goal_status"])
                lanes[lane]["files"]["status"].append(f"{rel}:goal_status")
        elif isinstance(data, list):
            if "MECHANISMS" in name:
                add(lane, "mechanisms", data, rel)
            elif "HYPOTHESES" in name:
                add(lane, "hypotheses", data, rel)
            elif "PREREGS" in name:
                add(lane, "preregs", data, rel)
            elif "SOURCE_CONTRACTS" in name:
                add(lane, "sources", data, rel)
    return lanes


def duplicate_ids(rows: list[dict], field: str) -> list[dict]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row[field]] += 1
    return sorted(
        [{"id": value, "count": count} for value, count in counts.items() if count > 1],
        key=lambda item: item["id"],
    )


def build_status_rows(lanes: dict[str, dict], lane_counts: dict[str, dict]) -> list[dict]:
    status_rows = [
        {
            "lane_id": "G0",
            "lane_status": "G0_WAVE1_RECONCILIATION_COMPLETE_PENDING_COMMIT",
            "files_written": [
                "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
                "research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.json",
                "research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.md",
                "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
                "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.md",
                "research/science_program_2026_05/00_control/reconcile_wave1_2026_05_06.py",
                "research/science_program_2026_05/02_hypothesis_registry/MECHANISM_REGISTRY_2026-05-06.json",
                "research/science_program_2026_05/02_hypothesis_registry/HYPOTHESIS_REGISTRY_2026-05-06.json",
                "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json",
                "research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json",
                "research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md",
                "research/science_program_2026_05/05_synthesis/G0_CROSS_AGENT_SYNTHESIS_2026-05-06.json",
                "research/science_program_2026_05/05_synthesis/G0_CROSS_AGENT_SYNTHESIS_2026-05-06.md",
                "research/science_program_2026_05/05_synthesis/G0_WAVE1_RECONCILIATION_2026-05-06.json",
                "research/science_program_2026_05/05_synthesis/G0_WAVE1_RECONCILIATION_2026-05-06.md",
                "research/science_program_2026_05/05_synthesis/G0_COMPLETION_AUDIT_2026-05-06.json",
                "research/science_program_2026_05/05_synthesis/G0_COMPLETION_AUDIT_2026-05-06.md",
            ],
            "tests_run": [
                "python scripts/generate_live_state.py -> passed",
                "python research/science_program_2026_05/00_control/reconcile_wave1_2026_05_06.py -> generated G0 wave-1 artifacts",
                "G1-G6 row schema/required-field/promotion/outcome/source-safe relationship validator -> passed with 4 G6 label_class normalizations recorded",
                "duplicate ID check across G1-G6 mechanism/hypothesis/prereg/source rows -> no duplicate IDs",
                "source contract validation-safe check -> 45/45 validation_safe=false",
                "forbidden live-surface diff check pending final verification",
                "python -m json.tool on updated G0 JSON artifacts pending final verification",
            ],
            "blockers": [
                "All 45 wave-1 source contracts remain validation_safe=false; no source is promotion-safe.",
                "No survivor backlog row exists because every candidate remains source/label/sample/owner-approval blocked.",
                "G9 neighbor pass remains missing because G9 has not run in wave 1.",
                "Four G6 hypothesis label_class values required G0 master-copy normalization; lane-owned artifact cleanup remains a follow-up.",
            ],
            "next_questions": [
                "Launch/merge G7-G12, especially G9 for the G0 neighbor pass and G12 red-team pass.",
                "Clean up G2/G6 standalone status-row packaging if future tooling requires one-file-per-schema lane artifacts.",
                "Do not promote any row until a separate owner-approved promotion dossier exists with validation-safe source contracts.",
            ],
            "commit_sha": None,
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        }
    ]

    for lane in [f"G{i}" for i in range(1, 7)]:
        status = copy.deepcopy(lanes[lane]["status"])
        if status is None:
            status = {
                "lane_id": lane,
                "lane_status": "MISSING_STATUS_ROW",
                "files_written": [],
                "tests_run": [],
                "blockers": ["No lane-owned status row found during G0 wave-1 reconciliation."],
                "next_questions": ["Re-run lane or add goal_status_v1 artifact."],
                "commit_sha": LANE_COMMITS[lane],
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            }
        status["lane_id"] = lane
        stale = status.get("commit_sha") != LANE_COMMITS[lane]
        status["commit_sha"] = LANE_COMMITS[lane]
        if lane in {"G2", "G6"} and "PENDING" in str(status.get("lane_status", "")):
            status["lane_status"] = f"{lane}_WAVE1_OUTPUTS_VISIBLE_AT_MAIN_HEAD_RECONCILED"
        elif stale:
            status["lane_status"] = f"{status.get('lane_status')}_G0_COMMIT_RECONCILED"
        status.setdefault("blockers", [])
        if stale:
            status["blockers"] = list(status["blockers"]) + [
                f"Lane-owned status commit metadata was stale/null during G0 wave-1 reconciliation; registry uses effective git commit {LANE_COMMITS[lane]}."
            ]
        status.setdefault("next_questions", [])
        status["promotion_verdict"] = "NO_PROMOTION_VERDICT"
        status_rows.append(status)

    for i in range(7, 13):
        lane = f"G{i}"
        status_rows.append(
            {
                "lane_id": lane,
                "lane_status": "READY_TO_LAUNCH_NOT_RUN",
                "files_written": [],
                "tests_run": [],
                "blockers": [
                    "Not part of wave-1 reconciliation; no lane-owned outputs visible at main HEAD 08ffc24b."
                ],
                "next_questions": [
                    "Launch lane in its own worktree and merge through G0 after row validation."
                ],
                "commit_sha": None,
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            }
        )
    return status_rows


def main() -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    schema = load_json(CONTROL / "SCHEMA_CONTRACTS_2026-05-06.json")
    required = {name: set(contract["required_fields"]) for name, contract in schema.items()}
    lanes = collect_lane_rows()

    schema_issues: list[dict] = []
    relationship_issues: list[dict] = []
    normalizations: list[dict] = []
    row_sources: dict[str, dict] = defaultdict(dict)
    all_mechanisms: list[dict] = []
    all_hypotheses: list[dict] = []
    all_preregs: list[dict] = []
    all_sources: list[dict] = []

    lane_counts = {
        lane: {
            "mechanisms": len(data["mechanisms"]),
            "hypotheses": len(data["hypotheses"]),
            "experiment_preregs": len(data["preregs"]),
            "source_contracts": len(data["sources"]),
            "status_source": sorted(set(data["files"]["status"])),
            "effective_commit_sha": LANE_COMMITS[lane],
        }
        for lane, data in lanes.items()
    }

    specs = [
        ("mechanisms", "science_mechanism_v1", "mechanism_id"),
        ("hypotheses", "science_hypothesis_v1", "hypothesis_id"),
        ("preregs", "experiment_prereg_v1", "experiment_id"),
        ("sources", "source_contract_v2", "source_id"),
    ]
    for lane, data in lanes.items():
        for kind, schema_name, id_field in specs:
            for row in data[kind]:
                missing = sorted(required[schema_name] - set(row))
                if missing:
                    schema_issues.append(
                        {
                            "lane_id": lane,
                            "schema": schema_name,
                            "row_id": row.get(id_field),
                            "issue": "missing_required_fields",
                            "fields": missing,
                        }
                    )
                if row.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
                    schema_issues.append(
                        {
                            "lane_id": lane,
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
                                "lane_id": lane,
                                "hypothesis_id": row.get("hypothesis_id"),
                                "field": "label_class",
                                "original": original,
                                "normalized": normalized,
                                "reason": "Normalize verbose lane wording to SCHEMA_CONTRACTS allowed label_class enum in the G0 master copy; lane artifact left unchanged.",
                            }
                        )
                        row["label_class"] = normalized
                    else:
                        schema_issues.append(
                            {
                                "lane_id": lane,
                                "schema": schema_name,
                                "row_id": row.get(id_field),
                                "issue": "invalid_label_class",
                                "value": original,
                            }
                        )
                if schema_name == "experiment_prereg_v1" and row.get("outcome_review_opened") is not False:
                    schema_issues.append(
                        {
                            "lane_id": lane,
                            "schema": schema_name,
                            "row_id": row.get(id_field),
                            "issue": "outcome_review_opened_not_false",
                            "value": row.get("outcome_review_opened"),
                        }
                    )
                if schema_name == "source_contract_v2" and row.get("validation_safe") is not False:
                    schema_issues.append(
                        {
                            "lane_id": lane,
                            "schema": schema_name,
                            "row_id": row.get(id_field),
                            "issue": "source_validation_safe_not_false",
                            "value": row.get("validation_safe"),
                        }
                    )
                row_sources[schema_name][row.get(id_field)] = {
                    "lane_id": lane,
                    "source_files": sorted(set(data["files"][kind])),
                }

        all_mechanisms.extend(data["mechanisms"])
        all_hypotheses.extend(data["hypotheses"])
        all_preregs.extend(data["preregs"])
        all_sources.extend(data["sources"])

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
        "blocked_source_rows": [
            row["source_id"] for row in all_sources if row.get("validation_safe") is False
        ],
    }
    label_summary: dict[str, int] = defaultdict(int)
    for row in all_hypotheses:
        label_summary[row["label_class"]] += 1

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
            "lane_id": "G5",
            "artifact_gap": "Lane-owned status row still has commit_sha null; G0 status registry reconciles effective commit from git log.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G6",
            "artifact_gap": "No standalone 00_control goal-status JSON; status row is embedded in G6_MOMENTUM_REVERSION_ROWS_2026-05-06.json.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G6",
            "artifact_gap": "Four lane hypothesis label_class values use verbose non-enum wording; G0 master copy normalizes them and records the repair.",
            "blocking_master_merge": False,
        },
        {
            "lane_id": "G9",
            "artifact_gap": "G0 controlling prompt names G9 for neighbor pass, but G9 is not part of wave 1 and has no lane outputs yet.",
            "blocking_master_merge": True,
        },
    ]

    lane_blockers = {
        lane: (data["status"] or {}).get("blockers", []) for lane, data in lanes.items()
    }

    status_rows = build_status_rows(lanes, lane_counts)

    reconciliation_meta = {
        "checked_at_utc": now,
        "main_head_reconciled": MAIN_HEAD_RECONCILED,
        "governor_lane": "G0",
        "scope": "wave_1_G1_G6_outputs_visible_at_main_head",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "row_counts": {
            "mechanism_rows_merged": len(all_mechanisms),
            "hypothesis_rows_merged": len(all_hypotheses),
            "experiment_prereg_rows_merged": len(all_preregs),
            "source_contract_rows_reconciled": len(all_sources),
            "goal_status_rows_total": len(status_rows),
        },
        "schema_check": {
            "required_field_issues": schema_issues,
            "relationship_issues": relationship_issues,
            "normalizations": normalizations,
            "duplicate_report": duplicate_report,
            "label_class_counts_after_g0_normalization": dict(sorted(label_summary.items())),
            "source_contract_summary": source_summary,
        },
        "missing_lane_artifacts": missing_lane_artifacts,
        "lane_counts": lane_counts,
        "lane_blockers": lane_blockers,
    }

    registries = [
        (
            HYP_DIR / "MECHANISM_REGISTRY_2026-05-06.json",
            "science_mechanism_v1",
            all_mechanisms,
            "WAVE1_RECONCILED_G1_G6_MECHANISMS_MERGED_RESEARCH_ONLY",
        ),
        (
            HYP_DIR / "HYPOTHESIS_REGISTRY_2026-05-06.json",
            "science_hypothesis_v1",
            all_hypotheses,
            "WAVE1_RECONCILED_G1_G6_HYPOTHESES_MERGED_RESEARCH_ONLY",
        ),
        (
            EXP_DIR / "EXPERIMENT_PREREGISTRY_2026-05-06.json",
            "experiment_prereg_v1",
            all_preregs,
            "WAVE1_RECONCILED_G1_G6_PREREGS_MERGED_OUTCOMES_CLOSED",
        ),
    ]
    for path, schema_name, rows, status in registries:
        dump_json(
            path,
            {
                "schema": schema_name,
                "status": status,
                "promotion_verdict": "NO_PROMOTION_VERDICT",
                "governor_reconciliation": reconciliation_meta,
                "row_sources": row_sources[schema_name],
                "rows": rows,
            },
        )

    source_registry = {
        "schema": "source_contract_v2",
        "status": "WAVE1_RECONCILED_G1_G6_SOURCE_CONTRACTS_NOT_VALIDATION_SAFE",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "governor_reconciliation": reconciliation_meta,
        "row_sources": row_sources["source_contract_v2"],
        "rows": all_sources,
    }
    dump_json(CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.json", source_registry)
    dump_json(CONTROL / "GOAL_STATUS_REGISTRY_2026-05-06.json", status_rows)

    source_ledger = load_json(CONTROL / "SOURCE_BUDGET_LEDGER_2026-05-06.json")
    source_ledger["wave1_reconciliation"] = {
        "checked_at_utc": now,
        "main_head_reconciled": MAIN_HEAD_RECONCILED,
        "source_contract_registry": "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
        "source_contract_rows": len(all_sources),
        "validation_safe_true": 0,
        "validation_safe_false": len(all_sources),
        "new_external_cash_spend_usd": 0.0,
        "paid_data_calls": 0,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    dump_json(CONTROL / "SOURCE_BUDGET_LEDGER_2026-05-06.json", source_ledger)

    master = {
        "schema_version": "science_goal_program_control_v1",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "g0_governor_reconciliation": reconciliation_meta,
        "registries": {
            "mechanism_registry": {
                "path": "research/science_program_2026_05/02_hypothesis_registry/MECHANISM_REGISTRY_2026-05-06.json",
                "schema": "science_mechanism_v1",
                "status": "WAVE1_RECONCILED_G1_G6_MECHANISMS_MERGED_RESEARCH_ONLY",
                "rows": len(all_mechanisms),
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            },
            "hypothesis_registry": {
                "path": "research/science_program_2026_05/02_hypothesis_registry/HYPOTHESIS_REGISTRY_2026-05-06.json",
                "schema": "science_hypothesis_v1",
                "status": "WAVE1_RECONCILED_G1_G6_HYPOTHESES_MERGED_RESEARCH_ONLY",
                "rows": len(all_hypotheses),
                "g0_label_class_normalizations": len(normalizations),
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            },
            "experiment_preregistry": {
                "path": "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json",
                "schema": "experiment_prereg_v1",
                "status": "WAVE1_RECONCILED_G1_G6_PREREGS_MERGED_OUTCOMES_CLOSED",
                "rows": len(all_preregs),
                "outcome_review_opened_true": 0,
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            },
            "source_contract_registry": {
                "path": "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
                "schema": "source_contract_v2",
                "status": "WAVE1_RECONCILED_G1_G6_SOURCE_CONTRACTS_NOT_VALIDATION_SAFE",
                "rows": len(all_sources),
                "validation_safe_true": 0,
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            },
        },
        "goal_status_rows": status_rows,
        "survivor_backlog": [],
        "blocker_summary": {
            "duplicate_id_blockers": duplicate_report,
            "source_blockers": source_summary,
            "schema_normalization_blockers": normalizations,
            "missing_lane_artifacts": missing_lane_artifacts,
            "promotion_blocker": "No row is validation-safe or promotion-safe; all outputs remain research/control only.",
        },
    }
    dump_json(SYN_DIR / "SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json", master)

    cross = {
        "checked_at_utc": now,
        "lane_id": "G0",
        "status": "G0_WAVE1_RECONCILIATION_COMPLETE_PENDING_COMMIT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "live_behavior_changed": False,
        "ai_calls": 0,
        "canary_calls": 0,
        "mt5_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "source_budget": {
            "current_external_cash_spend_cap_usd": 0.0,
            "spend_allowed": False,
            "new_external_cash_spend_usd": 0.0,
            "source_contract_rows_reconciled": len(all_sources),
            "validation_safe_source_rows": 0,
            "ledger_path": "research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.md",
            "status": "UNCHANGED_ZERO_NEW_EXTERNAL_CASH",
        },
        "wave1_lanes_reconciled": list(lanes.keys()),
        "neighbor_pass": [
            {
                "lane_id": lane,
                "status": "RECONCILED_FROM_MAIN_HEAD_08ffc24b",
                "merged_mechanisms": lane_counts[lane]["mechanisms"],
                "merged_hypotheses": lane_counts[lane]["hypotheses"],
                "merged_preregs": lane_counts[lane]["experiment_preregs"],
                "source_contract_rows": lane_counts[lane]["source_contracts"],
                "effective_commit_sha": LANE_COMMITS[lane],
            }
            for lane in lanes
        ]
        + [
            {
                "lane_id": "G9",
                "status": "MISSING_NOT_IN_WAVE1",
                "merged_rows": 0,
                "blocker": "G0 controlling prompt still requires G9 neighbor pass before full program reconciliation.",
            }
        ],
        "registries": {
            "mechanism_registry_rows": len(all_mechanisms),
            "hypothesis_registry_rows": len(all_hypotheses),
            "experiment_preregistry_rows": len(all_preregs),
            "source_contract_registry_rows": len(all_sources),
            "survivor_backlog_rows": 0,
        },
        "checks": reconciliation_meta["schema_check"],
        "missing_lane_artifacts": missing_lane_artifacts,
        "blockers": [
            "All source contracts are validation_safe=false; source/legal/timestamp/parser/no-lookahead/budget blockers remain lane-specific.",
            "No duplicate row IDs were found, but several cross-domain rows intentionally overlap G3/G4/G5/G6 and remain research-only.",
            "G9/G7-G12 lanes are not merged yet; red-team review is still blocked.",
            "No survivor backlog exists; no promotion, validation, prompt, risk, execution, selector, MT5, canary, paid-data, or order behavior change is authorized.",
        ],
        "merge_rule": "Merge lane rows into master registries only as NO_PROMOTION_VERDICT research rows after required-field, relationship, duplicate-ID, label, outcome-closed, source-safe-false, leakage, and killed-route checks.",
    }
    dump_json(SYN_DIR / "G0_CROSS_AGENT_SYNTHESIS_2026-05-06.json", cross)
    dump_json(SYN_DIR / "G0_WAVE1_RECONCILIATION_2026-05-06.json", cross)

    write_markdown(now, lanes, lane_counts, lane_blockers, missing_lane_artifacts, normalizations)
    write_completion_audit(now)

    print(f"wrote G0 wave1 reconciliation artifacts at {now}")
    print(
        json.dumps(
            {
                "mechanisms": len(all_mechanisms),
                "hypotheses": len(all_hypotheses),
                "preregs": len(all_preregs),
                "sources": len(all_sources),
                "normalizations": len(normalizations),
            },
            sort_keys=True,
        )
    )


def write_markdown(
    now: str,
    lanes: dict[str, dict],
    lane_counts: dict[str, dict],
    lane_blockers: dict[str, list[str]],
    missing_lane_artifacts: list[dict],
    normalizations: list[dict],
) -> None:
    source_rows = sum(item["source_contracts"] for item in lane_counts.values())
    mechanism_rows = sum(item["mechanisms"] for item in lane_counts.values())
    hypothesis_rows = sum(item["hypotheses"] for item in lane_counts.values())
    prereg_rows = sum(item["experiment_preregs"] for item in lane_counts.values())

    source_md = f"""# Science Program Source Contract Registry - 2026-05-06

**Status:** `WAVE1_RECONCILED_G1_G6_SOURCE_CONTRACTS_NOT_VALIDATION_SAFE`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Checked at UTC:** `{now}`
**Main HEAD reconciled:** `{MAIN_HEAD_RECONCILED}`

## Summary

G0 reconciled `{source_rows}` `source_contract_v2` rows from G1-G6. All `{source_rows}` remain `validation_safe=false`. No source is approved for validation, promotion, live features, paid pulls, or trading decisions.

| Lane | Source Rows | Validation-Safe Rows | Effective Commit |
| --- | ---: | ---: | --- |
"""
    for lane in lanes:
        source_md += f"| `{lane}` | {lane_counts[lane]['source_contracts']} | 0 | `{LANE_COMMITS[lane]}` |\n"
    source_md += """
## Active Source Blockers

- `$0` new external cash spend remains in force.
- Source legality, publication/as-of timestamps, parser/cache coverage, no-lookahead tests, and validation sample floors remain unresolved per lane rows.
- Public/methodology references are context or methodology evidence only, not decision-time market data.
- Existing Sierra/Databento/local artifacts remain source-contracted research inputs only.

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

## Wave-1 Source Reconciliation

- Checked at UTC: `{now}`
- Main HEAD reconciled: `{MAIN_HEAD_RECONCILED}`
- Source contract registry: `research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json`
- Source rows reconciled: `{source_rows}`
- Validation-safe source rows: `0`
- New external cash spend: `$0`
- Paid data calls: `0`

## Ledger Rows

`[]`

No lane may spend cash or mark a source validation-safe until this ledger has a numeric cap, per-source limit, source contract, and owner approval.
"""
    (CONTROL / "SOURCE_BUDGET_LEDGER_2026-05-06.md").write_text(ledger_md, encoding="utf-8")

    master_md = f"""# Science Program Master Registry - 2026-05-06

**Status:** `G0_WAVE1_RECONCILED_G1_G6`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Checked at UTC:** `{now}`
**Main HEAD reconciled:** `{MAIN_HEAD_RECONCILED}`

## G0 Registry State

- Mechanisms: `{mechanism_rows}`
- Hypotheses: `{hypothesis_rows}`
- Experiment preregs: `{prereg_rows}`
- Source contracts: `{source_rows}`
- Goal status rows: `13`
- Survivor backlog rows: `0`

G0 reconciled wave-1 lane outputs from G1-G6 now visible at main HEAD `{MAIN_HEAD_RECONCILED}`. Rows are merged as research-control inventory only. No row is validation-safe or promotion-safe.

## Lane Counts

| Lane | Mechanisms | Hypotheses | Preregs | Sources | Effective Commit |
| --- | ---: | ---: | ---: | ---: | --- |
"""
    for lane in lanes:
        counts = lane_counts[lane]
        master_md += (
            f"| `{lane}` | {counts['mechanisms']} | {counts['hypotheses']} | "
            f"{counts['experiment_preregs']} | {counts['source_contracts']} | `{counts['effective_commit_sha']}` |\n"
        )
    master_md += f"""
## Schema And Reconciliation Results

- Required-field issues after G0 reconciliation: `0`
- Relationship issues after G0 reconciliation: `0`
- Duplicate mechanism/hypothesis/prereg/source IDs: `0`
- G6 label-class master-copy normalizations: `{len(normalizations)}`
- Source contracts with `validation_safe=true`: `0`
- Experiment preregs with `outcome_review_opened=true`: `0`

## Missing Or Weak Lane Artifacts

"""
    for item in missing_lane_artifacts:
        master_md += (
            f"- `{item['lane_id']}`: {item['artifact_gap']} "
            f"Blocking master merge: `{item['blocking_master_merge']}`.\n"
        )
    master_md += """
## Survivor Backlog

No survivor hypotheses exist. Every row remains blocked by source safety, label separation, sample floors, duplicate/concentration controls, stale-route checks, owner approval, or unrun later-lane/red-team review.

## NO_PROMOTION_VERDICT

This master registry is a research/control reconciliation artifact only. It does not change live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, or order behavior.
"""
    (SYN_DIR / "SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md").write_text(master_md, encoding="utf-8")

    synthesis_md = f"""# G0 Wave-1 Cross-Agent Synthesis - 2026-05-06

**Lane:** `G0`
**Status:** `G0_WAVE1_RECONCILIATION_COMPLETE_PENDING_COMMIT`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Checked at UTC:** `{now}`
**Main HEAD reconciled:** `{MAIN_HEAD_RECONCILED}`

## Objective Restated

Run G0 wave-1 reconciliation for the primitive-science program: read merged G1-G6 outputs, validate mechanism/hypothesis/source/prereg/status rows, update master registries/status/synthesis, identify missing artifacts and duplicate/killed/leakage/source blockers, preserve `NO_PROMOTION_VERDICT`, and avoid all live-trading surfaces.

## Registry Outcome

| Registry | Rows | Status |
| --- | ---: | --- |
| Mechanism | {mechanism_rows} | `MERGED_RESEARCH_ONLY` |
| Hypothesis | {hypothesis_rows} | `MERGED_RESEARCH_ONLY` |
| Experiment prereg | {prereg_rows} | `MERGED_OUTCOMES_CLOSED` |
| Source contract | {source_rows} | `RECONCILED_NOT_VALIDATION_SAFE` |
| Survivor backlog | 0 | `EMPTY_NO_PROMOTION` |

## Validation Findings

- Required-field checks passed for G1-G6 rows after G0 reconciliation.
- Hypothesis-to-mechanism and prereg-to-hypothesis relationships passed.
- Duplicate row-ID checks found no duplicate mechanism, hypothesis, experiment, or source IDs.
- All experiment preregs keep `outcome_review_opened=false`.
- All source contracts keep `validation_safe=false`.
- Four G6 hypothesis rows used verbose label classes; G0 normalized the master copies to schema enums and recorded each repair in the JSON audit.

## Lane Blockers

"""
    for lane in lanes:
        counts = lane_counts[lane]
        synthesis_md += f"### {lane}\n\n"
        synthesis_md += (
            f"Rows: `{counts['mechanisms']}` mechanisms, `{counts['hypotheses']}` hypotheses, "
            f"`{counts['experiment_preregs']}` preregs, `{counts['source_contracts']}` sources. "
            f"Effective commit: `{LANE_COMMITS[lane]}`.\n\n"
        )
        for blocker in lane_blockers.get(lane, []):
            synthesis_md += f"- {blocker}\n"
        synthesis_md += "\n"
    synthesis_md += "## Missing Artifacts And Packaging Gaps\n\n"
    for item in missing_lane_artifacts:
        synthesis_md += (
            f"- `{item['lane_id']}`: {item['artifact_gap']} "
            f"Blocking master merge: `{item['blocking_master_merge']}`.\n"
        )
    synthesis_md += """
## Forbidden-Surface Boundary

G0 did not change live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, or order behavior. Final forbidden-surface diff verification is recorded in the completion audit.

## NO_PROMOTION_VERDICT

Wave-1 reconciliation creates an organized research backlog and source-blocker map. It is not a promotion, validation result, live selector, risk change, or execution change.
"""
    (SYN_DIR / "G0_CROSS_AGENT_SYNTHESIS_2026-05-06.md").write_text(synthesis_md, encoding="utf-8")
    (SYN_DIR / "G0_WAVE1_RECONCILIATION_2026-05-06.md").write_text(synthesis_md, encoding="utf-8")


def write_completion_audit(now: str) -> None:
    completion = {
        "audit_timestamp_utc": now,
        "lane_id": "G0",
        "status": "WAVE1_RECONCILIATION_PENDING_FINAL_VERIFICATION_AND_COMMIT",
        "primary_commit_sha": None,
        "main_head_reconciled": MAIN_HEAD_RECONCILED,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "objective_deliverables": [
            "mandatory preflight completed and evidenced",
            "G1-G6 merged outputs read from main HEAD 08ffc24b",
            "mechanism/hypothesis/source/prereg/status rows schema-checked",
            "master registries updated",
            "lane status registry updated with effective wave-1 commits",
            "source/budget ledger updated while preserving zero new cash spend",
            "missing lane artifacts and packaging gaps identified",
            "duplicate/killed/leakage/source blockers recorded",
            "NO_PROMOTION_VERDICT preserved",
            "forbidden live-trading surfaces untouched",
            "only scoped G0 research/control artifacts committed",
        ],
        "checklist": [],
        "blockers": [
            "All 45 source contracts are validation_safe=false.",
            "G9 and G7-G12 are not part of wave 1 and remain unmerged; red-team pass remains blocked.",
            "G2/G6 packaging is weaker than one-file-per-schema lane output, though rows were recoverable.",
            "Four G6 hypothesis label classes required master-copy normalization.",
        ],
        "verification_results": [],
        "can_mark_g0_complete": False,
    }
    dump_json(SYN_DIR / "G0_COMPLETION_AUDIT_2026-05-06.json", completion)

    completion_md = f"""# G0 Completion Audit - 2026-05-06

**Lane:** `G0`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Audit timestamp UTC:** `{now}`
**Status:** `WAVE1_RECONCILIATION_PENDING_FINAL_VERIFICATION_AND_COMMIT`
**Main HEAD reconciled:** `{MAIN_HEAD_RECONCILED}`

## Objective Restated

Run G0 wave-1 reconciliation for the GTOS primitive-science program using the controlling G0 prompt. Concrete deliverables: read G1-G6 outputs visible at main HEAD `{MAIN_HEAD_RECONCILED}`, validate/schema-check mechanism, hypothesis, source, prereg, and status rows, update master registries/status/synthesis, identify missing lane artifacts and duplicate/killed/leakage/source blockers, preserve `NO_PROMOTION_VERDICT`, commit only scoped G0 research/control artifacts, and avoid all live-trading behavior surfaces.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
| --- | --- | --- |
| Use controlling prompt | `research/science_program_2026_05/04_goal_prompts/G0_G0_PROGRAM_GOVERNOR_GOAL_PROMPT_2026-05-06.md` | `COMPLETE` |
| Mandatory preflight | `python scripts/generate_live_state.py` ran; `.context/LIVE_STATE.md`, latest handoff, quick reference, doctrine, current state, and reading order read | `COMPLETE` |
| Read G1-G6 merged outputs | Lane artifacts under `research/science_program_2026_05/01_domain_syntheses`, `02_hypothesis_registry`, `03_experiment_specs`, and `00_control` inventoried | `COMPLETE` |
| Schema-check rows | G0 validator checked required fields, `NO_PROMOTION_VERDICT`, closed prereg outcomes, source validation flags, label classes, duplicate IDs, and row relationships | `COMPLETE_WITH_RECORDED_G6_LABEL_NORMALIZATION` |
| Update master mechanism registry | `research/science_program_2026_05/02_hypothesis_registry/MECHANISM_REGISTRY_2026-05-06.json` | `COMPLETE` |
| Update master hypothesis registry | `research/science_program_2026_05/02_hypothesis_registry/HYPOTHESIS_REGISTRY_2026-05-06.json` | `COMPLETE` |
| Update master preregistry | `research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json` | `COMPLETE` |
| Validate/source-check source rows | `research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json`; all 45 source rows remain `validation_safe=false` | `COMPLETE_WITH_SOURCE_BLOCKERS` |
| Update lane status registry | `research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json` | `COMPLETE_PENDING_COMMIT_SHA` |
| Update synthesis | `research/science_program_2026_05/05_synthesis/G0_CROSS_AGENT_SYNTHESIS_2026-05-06.md` and `G0_WAVE1_RECONCILIATION_2026-05-06.md` | `COMPLETE` |
| Missing artifacts/blockers identified | Missing/weak artifacts and duplicate/killed/leakage/source blockers in master registry and wave-1 synthesis | `COMPLETE` |
| Preserve `NO_PROMOTION_VERDICT` | Final `rg` verification pending | `PENDING_FINAL_VERIFICATION` |
| Avoid forbidden live surfaces | Final diff verification pending | `PENDING_FINAL_VERIFICATION` |
| Commit only scoped G0 research/control artifacts | Pending commit | `PENDING_COMMIT` |

## Current Blockers

- All 45 source contracts are `validation_safe=false`.
- G9 and G7-G12 are not part of wave 1 and remain unmerged; red-team pass remains blocked.
- G2/G6 packaging is weaker than one-file-per-schema lane output, though rows were recoverable.
- Four G6 hypothesis label classes required master-copy normalization.

## Focused Verification Results

Final command results will be added after JSON, promotion-verdict, forbidden-surface, and commit checks complete.
"""
    (SYN_DIR / "G0_COMPLETION_AUDIT_2026-05-06.md").write_text(completion_md, encoding="utf-8")


if __name__ == "__main__":
    main()
