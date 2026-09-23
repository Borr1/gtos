"""Build OTG0 research-control artifacts for the GTOS science program.

This builder reads only governance registries and synthesis/control files. It
does not read outcome result files, run replay/backtests, call MT5, call paid
data, or open any outcome review flag.
"""

from __future__ import annotations

import collections
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = Path(__file__).resolve().parent
VERSION_DATE = "2026-05-07"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

OWNER_REVIEW = REPO_ROOT / "research/science_program_2026_05/05_synthesis/G0_G12_OWNER_FULL_RESEARCH_REVIEW_2026-05-06.md"
MASTER_REGISTRY_MD = REPO_ROOT / "research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md"
SOURCE_REGISTRY_MD = REPO_ROOT / "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.md"
SOURCE_REGISTRY_JSON = REPO_ROOT / "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json"
CD2_RECONCILIATION = REPO_ROOT / "research/science_program_2026_05/05_synthesis/G0_CD2_RECONCILIATION_2026-05-06.md"
G12_REVIEW = REPO_ROOT / "research/science_program_2026_05/05_synthesis/G12_RED_TEAM_REVIEW_2026-05-06.md"
RESEARCH_CURRENT_STATE = REPO_ROOT / ".context/00_core/research_current_state.md"
SCHEMA_CONTRACTS = REPO_ROOT / "research/science_program_2026_05/00_control/SCHEMA_CONTRACTS_2026-05-06.md"
SOURCE_BUDGET_LEDGER = REPO_ROOT / "research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.md"
PREREGISTRY_JSON = REPO_ROOT / "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json"
HYPOTHESIS_REGISTRY_JSON = REPO_ROOT / "research/science_program_2026_05/02_hypothesis_registry/HYPOTHESIS_REGISTRY_2026-05-06.json"
MECHANISM_REGISTRY_JSON = REPO_ROOT / "research/science_program_2026_05/02_hypothesis_registry/MECHANISM_REGISTRY_2026-05-06.json"
G12_LABEL_REVIEW = REPO_ROOT / "research/science_program_2026_05/05_synthesis/G12_LABEL_SEPARATION_REVIEW_2026-05-06.md"
G12_SOURCE_REVIEW = REPO_ROOT / "research/science_program_2026_05/05_synthesis/G12_SOURCE_VALIDITY_REVIEW_2026-05-06.md"
G12_DUP_REVIEW = REPO_ROOT / "research/science_program_2026_05/05_synthesis/G12_DUPLICATE_COUNTING_REVIEW_2026-05-06.md"
G12_LEAKAGE_LEDGER = REPO_ROOT / "research/science_program_2026_05/05_synthesis/G12_LEAKAGE_LEDGER_2026-05-06.md"
G12_SURVIVOR_DECISIONS = REPO_ROOT / "research/science_program_2026_05/05_synthesis/G12_SURVIVOR_BLOCKER_DECISIONS_2026-05-06.md"

CONTROLLING_INPUTS = [
    OWNER_REVIEW,
    MASTER_REGISTRY_MD,
    SOURCE_REGISTRY_MD,
    SOURCE_REGISTRY_JSON,
    CD2_RECONCILIATION,
    G12_REVIEW,
    RESEARCH_CURRENT_STATE,
    SCHEMA_CONTRACTS,
    SOURCE_BUDGET_LEDGER,
    PREREGISTRY_JSON,
    HYPOTHESIS_REGISTRY_JSON,
    MECHANISM_REGISTRY_JSON,
    G12_LABEL_REVIEW,
    G12_SOURCE_REVIEW,
    G12_DUP_REVIEW,
    G12_LEAKAGE_LEDGER,
    G12_SURVIVOR_DECISIONS,
]

OWNER_CLASS_TO_OTG0 = {
    "EXISTING_DATA_LIFECYCLE_OR_NO_FILL_CANDIDATE": {
        "otg0_class": "lifecycle_no_fill_existing_data_audit",
        "packet_status": "PACKET_AUDIT_REQUIRED_BEFORE_ANY_LIFECYCLE_OUTCOME_REVIEW",
        "next_lane": "OTL1",
    },
    "EXISTING_DATA_SYNTHETIC_REPLAY_CANDIDATE": {
        "otg0_class": "synthetic_replay_existing_data_audit",
        "packet_status": "PACKET_AUDIT_REQUIRED_BEFORE_ANY_SYNTHETIC_REPLAY",
        "next_lane": "OTL2",
    },
    "SOURCE_ASOF_CLEANUP_BEFORE_OUTCOME_TEST": {
        "otg0_class": "source_asof_cleanup_first",
        "packet_status": "SOURCE_ASOF_CLEANUP_REQUIRED_NO_OUTCOME_TEST",
        "next_lane": "OTL3",
    },
    "FORWARD_SHADOW_OR_PROSPECTIVE": {
        "otg0_class": "forward_shadow_prospective",
        "packet_status": "FORWARD_CAPTURE_OR_PROSPECTIVE_REPLAY_SPEC_REQUIRED",
        "next_lane": "OTL-FORWARD",
    },
    "BROKER_ACTUAL_R_SEPARATE_OR_BLOCKED": {
        "otg0_class": "broker_actual_r_blocked",
        "packet_status": "BROKER_ACTUAL_R_SAMPLE_AND_COST_BLOCKED",
        "next_lane": "OTL-BROKER-R",
    },
    "CONTROL_OR_OBSERVATION_ONLY": {
        "otg0_class": "control_only",
        "packet_status": "CONTROL_OR_OBSERVATION_ONLY_NO_R_BACKTEST",
        "next_lane": "OTL-CONTROL",
    },
}

EXPECTED_OWNER_COUNTS = {
    "BROKER_ACTUAL_R_SEPARATE_OR_BLOCKED": 10,
    "CONTROL_OR_OBSERVATION_ONLY": 33,
    "EXISTING_DATA_LIFECYCLE_OR_NO_FILL_CANDIDATE": 10,
    "EXISTING_DATA_SYNTHETIC_REPLAY_CANDIDATE": 16,
    "FORWARD_SHADOW_OR_PROSPECTIVE": 7,
    "SOURCE_ASOF_CLEANUP_BEFORE_OUTCOME_TEST": 21,
}

CLASS_REQUIRED_FIELDS = {
    "lifecycle_no_fill_existing_data_audit": [
        "packet_id",
        "experiment_id",
        "hypothesis_id",
        "setup_id_or_candidate_id",
        "symbol",
        "session",
        "side",
        "decision_asof_utc",
        "source_capture_utc",
        "pending_created_utc_if_applicable",
        "lifecycle_event_id",
        "lifecycle_state",
        "fill_or_no_fill_state",
        "cancel_expiry_or_wrong_side_reason",
        "duplicate_group_id",
        "label_family=lifecycle_no_fill",
        "forbidden_primary_fields_absent=broker_actual_r,synthetic_path_r,win_loss,outcome_r",
    ],
    "synthetic_replay_existing_data_audit": [
        "packet_id",
        "experiment_id",
        "hypothesis_id",
        "setup_id",
        "symbol",
        "session",
        "side",
        "decision_asof_utc",
        "ordered_path_source_id",
        "path_start_utc",
        "path_end_utc",
        "entry_sl_tp_or_level_packet",
        "same_bar_ambiguity_policy",
        "cost_model_version",
        "duplicate_group_id",
        "label_family=synthetic_path_r",
        "broker_actual_r_absent_from_primary_metric=true",
    ],
    "source_asof_cleanup_first": [
        "packet_id",
        "experiment_id",
        "hypothesis_id",
        "source_id",
        "url_or_vendor",
        "cache_path",
        "source_fetch_or_file_asof_utc",
        "source_hash",
        "parser_version",
        "publication_asof_timestamp_rule",
        "vintage_or_revision_rule_if_applicable",
        "license_or_access_state",
        "no_lookahead_fixture_status",
        "outcome_columns_absent=true",
    ],
    "forward_shadow_prospective": [
        "packet_id",
        "experiment_id",
        "hypothesis_id",
        "capture_start_not_before_frozen_at_utc",
        "decision_asof_utc",
        "source_capture_utc",
        "schema_version",
        "duplicate_group_id",
        "label_family_declared_before_followup",
        "outcome_review_opened=false_until_packet_allows",
    ],
    "broker_actual_r_blocked": [
        "packet_id",
        "experiment_id",
        "hypothesis_id",
        "position_id_or_order_ticket",
        "candidate_or_setup_id_link",
        "account_history_exported_utc",
        "entry_fill_utc",
        "close_fill_utc",
        "commission_swap_spread_slippage_fields",
        "intended_entry_sl_tp_fields",
        "manual_trade_exclusion_or_tag",
        "duplicate_group_id",
        "label_family=broker_actual_r",
        "synthetic_path_r_separate_comparator_only",
    ],
    "control_only": [
        "packet_id",
        "experiment_id",
        "hypothesis_id",
        "audit_unit_id",
        "asof_or_control_timestamp",
        "source_or_manifest_id",
        "status_or_blocker_code",
        "duplicate_group_id_if_repeated_status",
        "label_family=context_only_or_observation_only",
        "r_outcome_columns_absent=true",
    ],
}

GLOBAL_PACKET_FIELDS = [
    "experiment_id",
    "hypothesis_id",
    "frozen_at_utc",
    "outcome_review_opened=false",
    "promotion_verdict=NO_PROMOTION_VERDICT",
    "metric",
    "null",
    "alternative",
    "sample_floor",
    "duplicate_policy",
    "label_separation_policy",
    "source_contract_or_blocker_refs",
    "result_quarantine_path",
]

LABEL_FAMILY_RULES = {
    "broker_actual_r": "Account-history realized R only; cost/slippage/close-side evidence required; never pooled with synthetic path-R or lifecycle/no-fill.",
    "synthetic_path_r": "Research-only ordered-path label; can be discovery evidence, never broker-realized validation or promotion evidence.",
    "lifecycle_no_fill": "Fill/no-fill/cancel/expiry/wrong-side/tick-missing states; no-fill is not a loss and must not be ranked by R.",
    "fill_no_fill": "Alias family for lifecycle fill/no-fill states; keep denominators separate from R labels.",
    "context_only": "Source, eligibility, provenance, regime, or audit context; no return outcome.",
    "observation_only": "Operational/audit/behavioral observation; no trading-edge backtest.",
}

RESULT_QUARANTINE_RULES = [
    "OTG0 itself may not create result files beyond packet/control/audit artifacts.",
    "Future OTL result files must live under research/science_program_2026_05/06_outcome_testing/quarantine/<lane_id>/ until G12 audits implementation validity.",
    "Every future result file must carry RESULT_QUARANTINED_DISCOVERY_ONLY and NO_PROMOTION_VERDICT.",
    "No future result may edit master registries, source validation flags, risk, prompts, selectors, permissions, execution, MT5, canaries, credentials, remote state, or order behavior.",
    "Broker actual-R, synthetic path-R, lifecycle/no-fill, and context/observation outputs must be separate files or separate tables with non-overlapping denominators.",
]

ACCEPTANCE_RULES = [
    "Accept OTG0 as complete only if all 97 owner-review preregs parse and match the master experiment preregistry exactly.",
    "Accept packet freeze only if outcome_review_opened remains false in both owner-review table and JSON preregistry.",
    "Accept source gating only if every source_contract_v2 row remains validation_safe=false and all source/as-of gaps are blockers, not silent assumptions.",
    "Accept lifecycle/synthetic lanes only for packet audit; outcome tests remain blocked until the packet audit verifies required fields, duplicate keys, no-leak fields, and source/as-of availability without reading results early.",
    "Accept broker actual-R lanes only as blocked unless account-history sample floors, fill/cost/close-side joins, and label-family separation are proven in a later frozen packet.",
    "Accept control-only rows only as audit/source/telemetry governance; they cannot become R-backtests without a new prereg.",
]

BLOCKER_RULES = [
    "If a data source has no registered source_contract_v2 row, create a source-registration blocker and do not use it as validation evidence.",
    "If source publication/as-of time is unknown, date-only, revised without vintage, or parser/cache/hash is missing, route to OTL3 source/as-of cleanup first.",
    "If no_leak_fields contain forbidden outcome/future names, block outcome opening until G0/G12 cleanup replaces them with as-of feature whitelists.",
    "If duplicate_group_id or independent unit is missing, block sample-floor, effective-N, DSR, PBO, and any confirm/kill language.",
    "If a packet mixes broker actual-R with synthetic path-R or lifecycle/no-fill in one primary metric, quarantine and fail the packet.",
    "If a future lane sees attractive results before packet freeze, label those results contaminated and discovery-only; do not move them into the acceptance path.",
]


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def clean_cell(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`"):
        value = value[1:-1]
    return value.strip()


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def parse_owner_experiment_table() -> list[dict[str, Any]]:
    text = OWNER_REVIEW.read_text(encoding="utf-8")
    section = text.split("## Appendix C - Experiment Preregistry Inventory: 97 Rows", 1)[1]
    section = section.split("## Appendix D - Source Contract Inventory", 1)[0]
    rows: list[dict[str, Any]] = []
    for line in section.splitlines():
        if not line.startswith("| "):
            continue
        if line.startswith("|---") or "| # |" in line:
            continue
        cells = [clean_cell(cell) for cell in line.strip().strip("|").split("|")]
        if len(cells) != 13:
            raise ValueError(f"Owner appendix C row has {len(cells)} cells, expected 13: {line[:180]}")
        rows.append(
            {
                "owner_row_number": int(cells[0]),
                "experiment_id": cells[1],
                "lane": cells[2],
                "hypothesis_id": cells[3],
                "owner_testing_class": cells[4],
                "metric": cells[5],
                "cohort": cells[6],
                "label_separation": cells[7],
                "duplicate_policy": cells[8],
                "cost_slippage_assumptions": cells[9],
                "outcome_opened": cells[10] == "True",
                "recommendation": cells[11],
                "current_blocker_or_status": cells[12],
            }
        )
    return rows


def source_refs_for(hypothesis: dict[str, Any] | None, mechanism: dict[str, Any] | None, sources: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    explicit_source_refs: list[str] = []
    required_data_refs: list[str] = []
    descriptive: list[str] = []
    if hypothesis:
        explicit_source_refs.extend(as_list(hypothesis.get("source_ids")))
    if mechanism:
        explicit_source_refs.extend(as_list(mechanism.get("source_ids")))
        required_data_refs.extend(as_list(mechanism.get("required_data")))
    registered: list[str] = []
    unresolved: list[str] = []
    for ref in explicit_source_refs:
        item = ref.strip()
        if not item:
            continue
        if item in sources:
            registered.append(item)
        else:
            unresolved.append(item)
    for ref in required_data_refs:
        item = ref.strip()
        if not item:
            continue
        if item in sources:
            registered.append(item)
        else:
            descriptive.append(item)
    return sorted(set(registered)), sorted(set(unresolved)), sorted(set(descriptive))


def compact_source_contract(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": source.get("source_id"),
        "url_or_vendor": source.get("url_or_vendor"),
        "cache_path": source.get("cache_path"),
        "allowed_feature_role": source.get("allowed_feature_role"),
        "publication_asof_timestamp_rule": source.get("publication_asof_timestamp_rule"),
        "validation_safe": source.get("validation_safe"),
        "validation_safe_blockers": source.get("validation_safe_blockers", []),
    }


def packet_blockers(
    owner_row: dict[str, Any],
    prereg: dict[str, Any] | None,
    hypothesis: dict[str, Any] | None,
    mechanism: dict[str, Any] | None,
    registered_sources: list[str],
    unresolved_source_refs: list[str],
    source_ref_issues: list[dict[str, Any]],
    no_leak_blockers: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    if prereg is None:
        blockers.append(
            {
                "blocker_id": "OTG0-BLK-MISSING-PREREG",
                "status": "BLOCKS_PACKET",
                "question": f"Why is {owner_row['experiment_id']} present in owner review but absent from EXPERIMENT_PREREGISTRY?",
            }
        )
    if hypothesis is None:
        blockers.append(
            {
                "blocker_id": "OTG0-BLK-MISSING-HYPOTHESIS",
                "status": "BLOCKS_PACKET",
                "question": f"Which master hypothesis row owns {owner_row['experiment_id']} and its null definition?",
            }
        )
    if prereg and prereg.get("outcome_review_opened") is not False:
        blockers.append(
            {
                "blocker_id": "OTG0-BLK-OUTCOME-OPENED",
                "status": "BLOCKS_OTG0",
                "question": f"Who opened outcome_review for {owner_row['experiment_id']} and where is the frozen packet authorization?",
            }
        )
    if owner_row["outcome_opened"]:
        blockers.append(
            {
                "blocker_id": "OTG0-BLK-OWNER-OUTCOME-OPENED",
                "status": "BLOCKS_OTG0",
                "question": f"Why does owner Appendix C show outcome opened for {owner_row['experiment_id']}?",
            }
        )
    if not registered_sources:
        blockers.append(
            {
                "blocker_id": "OTG0-BLK-NO-REGISTERED-SOURCE-CONTRACT",
                "status": "BLOCKS_OUTCOME_TEST",
                "question": f"Which concrete source_contract_v2 rows and cache paths supply {owner_row['experiment_id']} without outcome leakage?",
            }
        )
    if unresolved_source_refs:
        blockers.append(
            {
                "blocker_id": "OTG0-BLK-UNRESOLVED-SOURCE-REF",
                "status": "BLOCKS_SOURCE_VALIDITY",
                "question": f"Resolve non-source-contract refs for {owner_row['experiment_id']}: {', '.join(unresolved_source_refs[:5])}.",
            }
        )
    if hypothesis and hypothesis["hypothesis_id"] in no_leak_blockers:
        blockers.append(
            {
                "blocker_id": "OTG0-BLK-G12-NOLEAK-SEMANTIC-INVERSION",
                "status": "BLOCKS_OUTCOME_OPENING",
                "question": f"Replace forbidden no_leak_fields for {hypothesis['hypothesis_id']} with decision-time/as-of feature names before any outcome opening.",
            }
        )
    if source_ref_issues:
        blockers.append(
            {
                "blocker_id": "OTG0-BLK-G12-SOURCE-REFERENCE-ISSUE",
                "status": "BLOCKS_SOURCE_VALIDITY",
                "question": f"Move placeholder/literature/dependency refs for {owner_row['experiment_id']} into evidence/dependency fields before source use.",
            }
        )
    if owner_row["owner_testing_class"] == "BROKER_ACTUAL_R_SEPARATE_OR_BLOCKED":
        blockers.append(
            {
                "blocker_id": "OTG0-BLK-BROKER-ACTUAL-R-SAMPLE-FLOOR",
                "status": "BLOCKS_ACTUAL_R_CLAIMS",
                "question": "Where is the account-history realized-R cohort with fill, close-side cost, duplicate, and sample-floor evidence?",
            }
        )
    if owner_row["owner_testing_class"] in {
        "EXISTING_DATA_LIFECYCLE_OR_NO_FILL_CANDIDATE",
        "EXISTING_DATA_SYNTHETIC_REPLAY_CANDIDATE",
    }:
        blockers.append(
            {
                "blocker_id": "OTG0-BLK-PACKET-AUDIT-FIRST",
                "status": "BLOCKS_TEST_IMPLEMENTATION_UNTIL_AUDITED",
                "question": "Do the frozen data packets actually contain every required field, source hash, duplicate key, label-family boundary, and no-leak timestamp before any result is read?",
            }
        )
    if owner_row["owner_testing_class"] == "SOURCE_ASOF_CLEANUP_BEFORE_OUTCOME_TEST":
        blockers.append(
            {
                "blocker_id": "OTG0-BLK-SOURCE-ASOF-CLEANUP-FIRST",
                "status": "BLOCKS_OUTCOME_TEST",
                "question": "Which parser/cache/hash/publication-as-of/no-lookahead tests clear this source before any metric sees outcomes?",
            }
        )
    if owner_row["owner_testing_class"] == "CONTROL_OR_OBSERVATION_ONLY":
        blockers.append(
            {
                "blocker_id": "OTG0-BLK-CONTROL-ONLY-NO-R-BACKTEST",
                "status": "BLOCKS_R_OUTCOME_TEST",
                "question": "If an R or outcome claim is desired later, what new prereg changes this from control-only into an outcome-bearing row?",
            }
        )
    return blockers


def build_artifacts() -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    head = git_head()
    input_inventory = [
        {
            "path": rel(path),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in CONTROLLING_INPUTS
    ]

    owner_rows = parse_owner_experiment_table()
    preregistry = read_json(PREREGISTRY_JSON)
    hypothesis_registry = read_json(HYPOTHESIS_REGISTRY_JSON)
    mechanism_registry = read_json(MECHANISM_REGISTRY_JSON)
    source_registry = read_json(SOURCE_REGISTRY_JSON)
    preregs = {row["experiment_id"]: row for row in preregistry["rows"]}
    hypotheses = {row["hypothesis_id"]: row for row in hypothesis_registry["rows"]}
    mechanisms = {row["mechanism_id"]: row for row in mechanism_registry["rows"]}
    sources = {row["source_id"]: row for row in source_registry["rows"]}
    schema_check = source_registry.get("governor_reconciliation", {}).get("schema_check", {})
    no_leak_blockers = {
        row.get("hypothesis_id"): row
        for row in schema_check.get("no_leak_semantic_blockers", [])
        if row.get("hypothesis_id")
    }
    source_ref_issues_by_row: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for issue in schema_check.get("source_reference_issues", []):
        if issue.get("row_id"):
            source_ref_issues_by_row[issue["row_id"]].append(issue)

    owner_ids = {row["experiment_id"] for row in owner_rows}
    prereg_ids = set(preregs)
    owner_counts = collections.Counter(row["owner_testing_class"] for row in owner_rows)
    duplicate_hypotheses = {
        hypothesis_id: sorted(row["experiment_id"] for row in rows)
        for hypothesis_id, rows in collections.defaultdict(list, {}).items()
    }
    hypothesis_to_experiments: dict[str, list[str]] = collections.defaultdict(list)
    for row in preregistry["rows"]:
        hypothesis_to_experiments[row["hypothesis_id"]].append(row["experiment_id"])
    duplicate_hypotheses = {
        hypothesis_id: sorted(experiment_ids)
        for hypothesis_id, experiment_ids in hypothesis_to_experiments.items()
        if len(experiment_ids) > 1
    }

    classification_rows: list[dict[str, Any]] = []
    packets: list[dict[str, Any]] = []
    for owner_row in owner_rows:
        prereg = preregs.get(owner_row["experiment_id"])
        hypothesis = hypotheses.get(owner_row["hypothesis_id"])
        mechanism = mechanisms.get(hypothesis.get("mechanism_id")) if hypothesis else None
        mapping = OWNER_CLASS_TO_OTG0[owner_row["owner_testing_class"]]
        otg0_class = mapping["otg0_class"]
        registered_sources, unresolved_source_refs, descriptive_source_requirements = source_refs_for(hypothesis, mechanism, sources)
        source_contracts = [compact_source_contract(sources[source_id]) for source_id in registered_sources]
        related_source_issues = []
        if hypothesis:
            related_source_issues.extend(source_ref_issues_by_row.get(hypothesis["hypothesis_id"], []))
        if mechanism:
            related_source_issues.extend(source_ref_issues_by_row.get(mechanism["mechanism_id"], []))
        blockers = packet_blockers(
            owner_row,
            prereg,
            hypothesis,
            mechanism,
            registered_sources,
            unresolved_source_refs,
            related_source_issues,
            no_leak_blockers,
        )
        source_gate_status = "VALIDATION_SAFE_FALSE_RESEARCH_ONLY"
        if unresolved_source_refs or related_source_issues:
            source_gate_status = "BLOCKED_UNREGISTERED_OR_PLACEHOLDER_SOURCE_REFS"
        elif not registered_sources:
            source_gate_status = "BLOCKED_NO_REGISTERED_SOURCE_CONTRACT"
        elif any(sources[source_id].get("validation_safe") is True for source_id in registered_sources):
            source_gate_status = "INVALID_OTG0_SOURCE_VALIDATION_SAFE_TRUE"

        packet = {
            "packet_id": f"OTG0-PKT-{owner_row['owner_row_number']:03d}",
            "experiment_id": owner_row["experiment_id"],
            "hypothesis_id": owner_row["hypothesis_id"],
            "lane": owner_row["lane"],
            "owner_testing_class": owner_row["owner_testing_class"],
            "otg0_testing_lane": otg0_class,
            "next_lane": mapping["next_lane"],
            "packet_status": mapping["packet_status"],
            "metric_preregistered": owner_row["metric"],
            "cohort_preregistered": owner_row["cohort"],
            "label_family_from_hypothesis": hypothesis.get("label_class") if hypothesis else None,
            "label_separation_policy": prereg.get("label_separation_policy") if prereg else owner_row["label_separation"],
            "duplicate_policy": prereg.get("duplicate_policy") if prereg else owner_row["duplicate_policy"],
            "cost_slippage_assumptions": prereg.get("cost_slippage_assumptions") if prereg else owner_row["cost_slippage_assumptions"],
            "null_definition": hypothesis.get("null") if hypothesis else None,
            "alternative_definition": hypothesis.get("alternative") if hypothesis else None,
            "test_method": hypothesis.get("test_method") if hypothesis else None,
            "sample_floor": hypothesis.get("sample_floor") if hypothesis else None,
            "no_leak_fields_from_hypothesis": hypothesis.get("no_leak_fields", []) if hypothesis else [],
            "promotion_blockers_from_hypothesis": hypothesis.get("promotion_blockers", []) if hypothesis else [],
            "required_packet_fields": GLOBAL_PACKET_FIELDS + CLASS_REQUIRED_FIELDS[otg0_class],
            "registered_source_contracts": source_contracts,
            "descriptive_source_requirements_from_mechanism": descriptive_source_requirements,
            "unresolved_source_refs": unresolved_source_refs,
            "source_gate_status": source_gate_status,
            "source_path_policy": "Paths are listed from source contracts only; OTG0 does not read source data rows or outcome files.",
            "result_quarantine_path": f"research/science_program_2026_05/06_outcome_testing/quarantine/{mapping['next_lane']}/{owner_row['experiment_id']}/",
            "outcome_review_opened_owner_review": owner_row["outcome_opened"],
            "outcome_review_opened_preregistry": prereg.get("outcome_review_opened") if prereg else None,
            "promotion_verdict": PROMOTION_VERDICT,
            "blockers": blockers,
        }
        packets.append(packet)
        classification_rows.append(
            {
                "experiment_id": owner_row["experiment_id"],
                "lane": owner_row["lane"],
                "hypothesis_id": owner_row["hypothesis_id"],
                "owner_testing_class": owner_row["owner_testing_class"],
                "otg0_testing_lane": otg0_class,
                "packet_id": packet["packet_id"],
                "packet_status": packet["packet_status"],
                "next_lane": mapping["next_lane"],
                "metric": owner_row["metric"],
                "outcome_review_opened": False,
                "promotion_verdict": PROMOTION_VERDICT,
            }
        )

    category_counts = collections.Counter(row["otg0_testing_lane"] for row in classification_rows)
    owner_count_mismatch = {
        cls: {"expected": expected, "actual": owner_counts.get(cls, 0)}
        for cls, expected in EXPECTED_OWNER_COUNTS.items()
        if owner_counts.get(cls, 0) != expected
    }

    blocker_ledger = [
        {
            "blocker_id": "OTG0-BLK-001",
            "name": "Owner classification is routing only",
            "evidence": rel(OWNER_REVIEW),
            "next_exact_question": "For each row, does the packet audit prove the required fields before any outcome result is read?",
        },
        {
            "blocker_id": "OTG0-BLK-002",
            "name": "No source contract is validation safe",
            "evidence": rel(SOURCE_REGISTRY_MD),
            "next_exact_question": "Which source-specific legal/cache/parser/publication/as-of/no-lookahead dossier clears a source while preserving validation_safe=false until owner approval?",
        },
        {
            "blocker_id": "OTG0-BLK-003",
            "name": "G11 no-leak semantic inversion",
            "evidence": rel(G12_LEAKAGE_LEDGER),
            "next_exact_question": "Which G0/G12 cleanup artifact replaces the 8 forbidden no_leak_fields with as-of feature whitelists without opening outcomes?",
        },
        {
            "blocker_id": "OTG0-BLK-004",
            "name": "Unregistered source placeholders and literature refs",
            "evidence": rel(G12_SOURCE_REVIEW),
            "next_exact_question": "Which source IDs stay in source_ids, and which move to evidence_refs, neighbor_lane_dependency, or blocked_dependency_refs?",
        },
        {
            "blocker_id": "OTG0-BLK-005",
            "name": "Duplicate hypothesis families",
            "evidence": "EXPERIMENT_PREREGISTRY_2026-05-06.json duplicate hypothesis scan",
            "next_exact_question": "Are CD2/original experiments for the same hypothesis mutually exclusive tests, parent-child packets, or duplicate routes that must share a denominator?",
        },
        {
            "blocker_id": "OTG0-BLK-006",
            "name": "Existing-data packet existence is unverified",
            "evidence": "OTG0 deliberately did not inspect outcome/source data rows",
            "next_exact_question": "Do OTL1/OTL2 packet audits find concrete packet files with required fields, source hashes, duplicate keys, and no-leak timestamps?",
        },
        {
            "blocker_id": "OTG0-BLK-007",
            "name": "Broker actual-R sample and close-cost scarcity",
            "evidence": rel(G12_SURVIVOR_DECISIONS),
            "next_exact_question": "Which account-history and close-side cost join packet reaches the preregistered actual-R floor without synthetic label pooling?",
        },
        {
            "blocker_id": "OTG0-BLK-008",
            "name": "Path/lifecycle packet fields missing in CD2-06 family",
            "evidence": rel(G12_REVIEW),
            "next_exact_question": "Where are source_hash, source_symbol, ordered prefill candles/ticks, pending-native fields, spread/tick, trade IDs, and strict packet-family separation stored?",
        },
        {
            "blocker_id": "OTG0-BLK-009",
            "name": "Macro/vol source publication/as-of unresolved",
            "evidence": rel(G12_SOURCE_REVIEW),
            "next_exact_question": "What exact COT/FRED/BIS/Cboe/VRP parser and vintage/cache rules prove feature_asof_utc <= decision_time_utc?",
        },
        {
            "blocker_id": "OTG0-BLK-010",
            "name": "Result quarantine before G12 audit",
            "evidence": "OTG0 result quarantine rules",
            "next_exact_question": "Does each later result file remain quarantined with DISCOVERY_ONLY_NOT_VALIDATION until G12 audits implementation validity?",
        },
    ]

    followup_prompts = [
        {
            "lane": "OTL1",
            "title": "Lifecycle packet audit",
            "one_line_goal_prompt": "Run /goal OTL1 lifecycle/no-fill packet audit for OTG0 using the 10 lifecycle/no-fill existing-data packets in research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json, complete GTOS preflight, feed all OTG0/G12/source context into the analysis, crawl local/source evidence or public docs only when needed and cache it, aggressively resolve every missing lifecycle/source/as-of/duplicate/no-leak/null/label ambiguity into repo evidence or a named blocker with the next exact question, do not run outcome tests or inspect R results, and stop only after every lifecycle packet is PASS_PACKET_READY_FOR_TEST_IMPLEMENTATION or BLOCKED_WITH_EXACT_FIELDS.",
        },
        {
            "lane": "OTL2",
            "title": "Synthetic replay packet audit",
            "one_line_goal_prompt": "Run /goal OTL2 synthetic replay packet audit for OTG0 using the 16 synthetic replay existing-data packets in research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json, complete GTOS preflight, feed all OTG0/G12/source context, inspect only packet schemas/manifests/code paths before any result rows, crawl source caches/web/PDF/docs when source-contract meaning is ambiguous and save evidence, hunt same-dataset contamination, same-bar ambiguity, duplicate hypothesis families, cost-model gaps, and synthetic-vs-broker label mixing, and stop only after every synthetic packet is PASS_PACKET_READY_FOR_TEST_IMPLEMENTATION or BLOCKED_WITH_EXACT_FIELDS without running replay outcomes.",
        },
        {
            "lane": "OTL3",
            "title": "Source/as-of cleanup triage",
            "one_line_goal_prompt": "Run /goal OTL3 source/as-of cleanup triage for OTG0 over all SOURCE_ASOF_CLEANUP_BEFORE_OUTCOME_TEST rows plus any packet source blockers, complete GTOS preflight, feed G12 source/leakage/no-leak reviews and the source registry, crawl local caches, vendor/exchange/regulator docs, PDFs, sitemaps, or public web only as needed with saved raw evidence, and stop only when each source has a legal/cache/parser/hash/publication/vintage/no-lookahead status of CLEAR_FOR_RESEARCH_PACKET_USE, CONTEXT_ONLY, or BLOCKED_WITH_NEXT_EXACT_QUESTION while validation_safe remains false.",
        },
        {
            "lane": "OTL4-OTL5",
            "title": "Later test implementation lanes",
            "one_line_goal_prompt": "Run /goal later OTG0 test implementation only for packets already marked PASS_PACKET_READY_FOR_TEST_IMPLEMENTATION by OTL1/OTL2/OTL3, complete GTOS preflight, re-feed the frozen packet, source/as-of dossier, duplicate/no-leak/label rules, and result-quarantine rules, implement the smallest research-only harness without touching live trading surfaces, actively search for hidden leakage or stale context before reading outcomes, write quarantined DISCOVERY_ONLY_NOT_VALIDATION results with no promotion language, and stop only after tests, blockers, result hashes, and G12 audit inputs are complete.",
        },
        {
            "lane": "G12-post-test",
            "title": "G12 post-test audit",
            "one_line_goal_prompt": "Run /goal G12 post-test audit on quarantined OTG0/OTL result artifacts only after implementation lanes finish, complete GTOS preflight, feed every frozen packet, packet audit, source evidence cache, harness diff, test output, and ambiguity ledger, adversarially inspect leakage, duplicate counting, label mixing, stale source/as-of rules, synthetic-vs-actual confusion, null drift, metric drift, and result cherry-picking, crawl source evidence when needed, and stop only after each result is ACCEPT_RESEARCH_DISCOVERY_ONLY, REJECT_INVALID_TEST, or BLOCKED_WITH_NEXT_EXACT_QUESTION.",
        },
        {
            "lane": "G0-outcome-synthesis",
            "title": "G0 outcome synthesis",
            "one_line_goal_prompt": "Run /goal G0 outcome synthesis after G12 post-test audit, complete GTOS preflight, feed OTG0 packets, OTL audits, quarantined results, G12 validity decisions, and research_current_state, synthesize only audited research-control conclusions with label-family separation and source/as-of caveats, preserve NO_PROMOTION_VERDICT unless a separate owner-approved promotion dossier exists, update registries/context only for scoped research-control status, and stop only after every prereg is mapped to tested-discovery, invalid-test, source-blocked, forward-shadow, broker-actual-R-blocked, or control-only with exact next actions.",
        },
    ]

    common = {
        "artifact_family": "OTG0_OUTCOME_TESTING_GOVERNOR_CONTROL",
        "generated_at_utc": generated_at,
        "version_date": VERSION_DATE,
        "git_head_at_generation": head,
        "promotion_verdict": PROMOTION_VERDICT,
        "outcome_review_opened": False,
        "validation_safe": False,
        "access_scope": "Governance/control registries only; no outcome tests run; no outcome result rows inspected.",
        "controlling_inputs": input_inventory,
    }

    classification_ledger = {
        **common,
        "summary": {
            "owner_rows_parsed": len(owner_rows),
            "master_prereg_rows": len(preregistry["rows"]),
            "owner_class_counts": dict(sorted(owner_counts.items())),
            "otg0_class_counts": dict(sorted(category_counts.items())),
            "owner_expected_count_mismatch": owner_count_mismatch,
        },
        "class_mapping": OWNER_CLASS_TO_OTG0,
        "duplicate_hypothesis_families": duplicate_hypotheses,
        "rows": classification_rows,
    }

    packet_manifest = {
        **common,
        "packet_manifest_status": "FROZEN_PACKET_CONTROL_ONLY_OUTCOMES_CLOSED",
        "universal_packet_fields": GLOBAL_PACKET_FIELDS,
        "class_required_fields": CLASS_REQUIRED_FIELDS,
        "label_family_rules": LABEL_FAMILY_RULES,
        "packets": packets,
    }

    control_rules = {
        **common,
        "acceptance_rules": ACCEPTANCE_RULES,
        "blocker_rules": BLOCKER_RULES,
        "result_quarantine_rules": RESULT_QUARANTINE_RULES,
        "label_family_rules": LABEL_FAMILY_RULES,
        "class_required_fields": CLASS_REQUIRED_FIELDS,
        "blocker_ledger": blocker_ledger,
        "test_status_policy": {
            "OTG0": "CONTROL_ARTIFACTS_ONLY_NO_TESTS_RUN",
            "OTL1": "LIFECYCLE_PACKET_AUDIT_BEFORE_TESTS",
            "OTL2": "SYNTHETIC_PACKET_AUDIT_BEFORE_TESTS",
            "OTL3": "SOURCE_ASOF_CLEANUP_BEFORE_TESTS",
            "later_implementation": "QUARANTINED_DISCOVERY_ONLY_AFTER_PACKET_PASS",
            "G12_post_test": "VALIDITY_AUDIT_BEFORE_ANY_SYNTHESIS",
            "G0_outcome_synthesis": "AUDITED_RESEARCH_CONTROL_SYNTHESIS_ONLY",
        },
    }

    prompts = {
        **common,
        "prompt_policy": "Each prompt is exactly one line in the JSON field and requires deep ambiguity pursuit, context feeding, source crawling when needed, and no lazy stopping condition.",
        "followup_goal_prompts": followup_prompts,
    }

    audit_checks = [
        {
            "requirement": "Mandatory controlling inputs present",
            "status": "PASS" if all(path.exists() for path in CONTROLLING_INPUTS) else "FAIL",
            "evidence": [rel(path) for path in CONTROLLING_INPUTS],
        },
        {
            "requirement": "Owner review Appendix C parsed 97 preregs",
            "status": "PASS" if len(owner_rows) == 97 else "FAIL",
            "evidence": f"parsed={len(owner_rows)}",
        },
        {
            "requirement": "Owner prereg IDs match master experiment preregistry",
            "status": "PASS" if owner_ids == prereg_ids else "FAIL",
            "evidence": {
                "owner_not_in_master": sorted(owner_ids - prereg_ids),
                "master_not_in_owner": sorted(prereg_ids - owner_ids),
            },
        },
        {
            "requirement": "Owner classification counts match corrective synthesis",
            "status": "PASS" if not owner_count_mismatch else "FAIL",
            "evidence": dict(sorted(owner_counts.items())),
        },
        {
            "requirement": "All outcome_review_opened flags remain false",
            "status": "PASS"
            if all(not row["outcome_opened"] for row in owner_rows)
            and all(row.get("outcome_review_opened") is False for row in preregistry["rows"])
            else "FAIL",
            "evidence": {
                "owner_true_count": sum(1 for row in owner_rows if row["outcome_opened"]),
                "json_true_count": sum(1 for row in preregistry["rows"] if row.get("outcome_review_opened") is True),
            },
        },
        {
            "requirement": "All source_contract_v2 validation_safe flags remain false",
            "status": "PASS" if all(row.get("validation_safe") is False for row in source_registry["rows"]) else "FAIL",
            "evidence": {
                "source_rows": len(source_registry["rows"]),
                "validation_safe_true": sum(1 for row in source_registry["rows"] if row.get("validation_safe") is True),
            },
        },
        {
            "requirement": "Every packet has metric, null, duplicate policy, label policy, and test status",
            "status": "PASS"
            if all(
                packet.get("metric_preregistered")
                and packet.get("null_definition")
                and packet.get("duplicate_policy")
                and packet.get("label_separation_policy")
                and packet.get("packet_status")
                for packet in packets
            )
            else "FAIL",
            "evidence": [
                packet["experiment_id"]
                for packet in packets
                if not (
                    packet.get("metric_preregistered")
                    and packet.get("null_definition")
                    and packet.get("duplicate_policy")
                    and packet.get("label_separation_policy")
                    and packet.get("packet_status")
                )
            ],
        },
        {
            "requirement": "No outcome tests run or results inspected by OTG0",
            "status": "PASS",
            "evidence": "Builder reads only governance/control registries listed in controlling_inputs.",
        },
        {
            "requirement": "Follow-up prompts are exact one-line goal prompts",
            "status": "PASS"
            if all("\n" not in item["one_line_goal_prompt"] for item in followup_prompts)
            else "FAIL",
            "evidence": {item["lane"]: len(item["one_line_goal_prompt"]) for item in followup_prompts},
        },
    ]

    completion_audit = {
        **common,
        "objective_restatement": [
            "Create research-only OTG0 control artifacts under 06_outcome_testing before any outcome review.",
            "Classify all 97 owner-review preregs into six testing/control lanes.",
            "Define frozen cohort packet, source/as-of, label-family, duplicate, no-leak, metric, test-status, result-quarantine, acceptance, and blocker rules.",
            "Produce one-line follow-up /goal prompts for OTL1, OTL2, OTL3, later implementation lanes, G12 post-test audit, and G0 outcome synthesis.",
            "Preserve NO_PROMOTION_VERDICT, validation_safe=false, and outcome_review_opened=false.",
        ],
        "prompt_to_artifact_checklist": audit_checks,
        "duplicate_hypothesis_families": duplicate_hypotheses,
        "standing_blockers": blocker_ledger,
        "can_mark_otg0_control_artifacts_complete": all(check["status"] == "PASS" for check in audit_checks),
    }

    return {
        "classification": classification_ledger,
        "packets": packet_manifest,
        "control": control_rules,
        "prompts": prompts,
        "audit": completion_audit,
    }


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def md_table(rows: list[list[Any]]) -> str:
    if not rows:
        return ""
    header = rows[0]
    out = ["| " + " | ".join(str(x) for x in header) + " |"]
    out.append("|" + "|".join("---" for _ in header) + "|")
    for row in rows[1:]:
        out.append("| " + " | ".join(str(x).replace("\n", " ").replace("|", "\\|") for x in row) + " |")
    return "\n".join(out)


def write_markdown_files(artifacts: dict[str, Any]) -> None:
    classification = artifacts["classification"]
    packets = artifacts["packets"]
    control = artifacts["control"]
    prompts = artifacts["prompts"]
    audit = artifacts["audit"]

    class_rows = [["OTG0 lane", "Count"]]
    for lane, count in sorted(classification["summary"]["otg0_class_counts"].items()):
        class_rows.append([f"`{lane}`", count])
    owner_rows = [["Owner class", "OTG0 lane", "Count", "Next lane"]]
    for owner_class, mapping in OWNER_CLASS_TO_OTG0.items():
        owner_rows.append(
            [
                f"`{owner_class}`",
                f"`{mapping['otg0_class']}`",
                classification["summary"]["owner_class_counts"].get(owner_class, 0),
                f"`{mapping['next_lane']}`",
            ]
        )
    priority_rows = [["Packet", "Experiment", "Lane", "OTG0 lane", "Status"]]
    for packet in packets["packets"]:
        if packet["next_lane"] in {"OTL1", "OTL2", "OTL3"}:
            priority_rows.append(
                [
                    f"`{packet['packet_id']}`",
                    f"`{packet['experiment_id']}`",
                    f"`{packet['lane']}`",
                    f"`{packet['otg0_testing_lane']}`",
                    f"`{packet['packet_status']}`",
                ]
            )
    classification_md = f"""# OTG0 Prereg Classification Ledger - {VERSION_DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Outcome review opened:** `false`  
**Validation safe:** `false`  
**Generated at UTC:** `{classification['generated_at_utc']}`  
**Git HEAD at generation:** `{classification['git_head_at_generation']}`

## Scope

This ledger classifies all `97` owner-review preregs from `{rel(OWNER_REVIEW)}` into OTG0 testing/control lanes. It is routing metadata only. It is not an outcome test, validation result, source-safety flip, or promotion artifact.

## Counts

{md_table(class_rows)}

## Owner Class Mapping

{md_table(owner_rows)}

## Immediate Packet-Audit Queue

{md_table(priority_rows)}

## Duplicate Hypothesis Families

Two master hypothesis IDs have both an original and CD2 experiment row. They must share a duplicate/parent-child policy before any test implementation:

```json
{json.dumps(classification['duplicate_hypothesis_families'], indent=2, sort_keys=True)}
```

## NO_PROMOTION_VERDICT

All rows remain research-control only. Every packet keeps `outcome_review_opened=false` and every source contract keeps `validation_safe=false`.
"""
    (OUT_DIR / f"OTG0_PREREG_CLASSIFICATION_LEDGER_{VERSION_DATE}.md").write_text(classification_md, encoding="utf-8")

    packet_rows = [["Packet", "Experiment", "Class", "Sources", "Blockers"]]
    for packet in packets["packets"]:
        packet_rows.append(
            [
                f"`{packet['packet_id']}`",
                f"`{packet['experiment_id']}`",
                f"`{packet['otg0_testing_lane']}`",
                len(packet["registered_source_contracts"]),
                len(packet["blockers"]),
            ]
        )
    packet_md = f"""# OTG0 Frozen Cohort Packet Manifest - {VERSION_DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Manifest status:** `{packets['packet_manifest_status']}`  
**Outcome review opened:** `false`  
**Validation safe:** `false`

## Rule

These are frozen packet definitions, not outcome packets with results. OTG0 lists source paths from source contracts and required fields from preregs/hypotheses, but it does not inspect source data rows or outcome rows.

## Universal Packet Fields

{chr(10).join('- `' + field + '`' for field in packets['universal_packet_fields'])}

## Class Field Profiles

```json
{json.dumps(packets['class_required_fields'], indent=2, sort_keys=True)}
```

## Packet Index

{md_table(packet_rows)}

## Full Machine Manifest

See `OTG0_FROZEN_COHORT_PACKET_MANIFEST_{VERSION_DATE}.json` for all `97` packet definitions, source contracts, no-leak fields, nulls, metrics, duplicate policy, and blockers.

## NO_PROMOTION_VERDICT

Packet readiness is not test readiness. OTL1/OTL2/OTL3 must audit packet fields and source/as-of boundaries before any test implementation can read outcomes.
"""
    (OUT_DIR / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{VERSION_DATE}.md").write_text(packet_md, encoding="utf-8")

    blocker_rows = [["Blocker", "Name", "Next exact question"]]
    for blocker in control["blocker_ledger"]:
        blocker_rows.append([f"`{blocker['blocker_id']}`", blocker["name"], blocker["next_exact_question"]])
    control_md = f"""# OTG0 Outcome Testing Control Rules - {VERSION_DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Outcome review opened:** `false`  
**Validation safe:** `false`

## Acceptance Rules

{chr(10).join('- ' + rule for rule in control['acceptance_rules'])}

## Blocker Rules

{chr(10).join('- ' + rule for rule in control['blocker_rules'])}

## Result Quarantine

{chr(10).join('- ' + rule for rule in control['result_quarantine_rules'])}

## Label Families

```json
{json.dumps(control['label_family_rules'], indent=2, sort_keys=True)}
```

## Standing Blockers

{md_table(blocker_rows)}

## NO_PROMOTION_VERDICT

These rules authorize only research-control packet audits and later quarantined discovery tests after packet readiness passes. They authorize no live trading, prompt, risk, execution, selector, safety-gate, MT5, canary, paid-data, credential, remote, order-behavior, source-validation, or promotion change.
"""
    (OUT_DIR / f"OTG0_OUTCOME_TESTING_CONTROL_RULES_{VERSION_DATE}.md").write_text(control_md, encoding="utf-8")

    prompt_rows = [["Lane", "Prompt"]]
    for item in prompts["followup_goal_prompts"]:
        prompt_rows.append([f"`{item['lane']}`", item["one_line_goal_prompt"]])
    prompts_md = f"""# OTG0 Follow-Up Goal Prompts - {VERSION_DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Policy:** each prompt below is a one-line `/goal` prompt and requires deep ambiguity pursuit, context feeding, source crawling when needed, and no lazy stopping condition.

{md_table(prompt_rows)}

## NO_PROMOTION_VERDICT

These prompts launch research-control or quarantined discovery lanes only. They do not authorize promotion or live behavior changes.
"""
    (OUT_DIR / f"OTG0_FOLLOWUP_GOAL_PROMPTS_{VERSION_DATE}.md").write_text(prompts_md, encoding="utf-8")

    audit_rows = [["Requirement", "Status", "Evidence"]]
    for check in audit["prompt_to_artifact_checklist"]:
        evidence = check["evidence"]
        if not isinstance(evidence, str):
            evidence = json.dumps(evidence, sort_keys=True)
        audit_rows.append([check["requirement"], f"`{check['status']}`", evidence])
    audit_md = f"""# OTG0 Completion Audit - {VERSION_DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Outcome review opened:** `false`  
**Validation safe:** `false`  
**Can mark OTG0 control artifacts complete:** `{str(audit['can_mark_otg0_control_artifacts_complete']).lower()}`

## Objective Restatement

{chr(10).join('- ' + item for item in audit['objective_restatement'])}

## Prompt-To-Artifact Checklist

{md_table(audit_rows)}

## Standing Blockers

{md_table(blocker_rows)}

## NO_PROMOTION_VERDICT

OTG0 created packet/control artifacts only. It did not run outcome tests, inspect outcome results, mark sources validation-safe, open outcome reviews, or change live trading behavior.
"""
    (OUT_DIR / f"OTG0_COMPLETION_AUDIT_{VERSION_DATE}.md").write_text(audit_md, encoding="utf-8")

    readme_md = f"""# Outcome Testing Governor OTG0 - {VERSION_DATE}

Research-only control artifacts for the primitive-science outcome-testing phase.

## Files

- `build_otg0_control_artifacts_2026_05_07.py`
- `OTG0_PREREG_CLASSIFICATION_LEDGER_{VERSION_DATE}.md/json`
- `OTG0_FROZEN_COHORT_PACKET_MANIFEST_{VERSION_DATE}.md/json`
- `OTG0_OUTCOME_TESTING_CONTROL_RULES_{VERSION_DATE}.md/json`
- `OTG0_FOLLOWUP_GOAL_PROMPTS_{VERSION_DATE}.md/json`
- `OTG0_COMPLETION_AUDIT_{VERSION_DATE}.md/json`

## Boundary

OTG0 is a governor/control phase. It opens no outcome review, runs no outcome tests, inspects no outcome result rows, and preserves `NO_PROMOTION_VERDICT`, `validation_safe=false`, and `outcome_review_opened=false`.
"""
    (OUT_DIR / f"README_{VERSION_DATE}.md").write_text(readme_md, encoding="utf-8")


def main() -> int:
    artifacts = build_artifacts()
    write_json(OUT_DIR / f"OTG0_PREREG_CLASSIFICATION_LEDGER_{VERSION_DATE}.json", artifacts["classification"])
    write_json(OUT_DIR / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{VERSION_DATE}.json", artifacts["packets"])
    write_json(OUT_DIR / f"OTG0_OUTCOME_TESTING_CONTROL_RULES_{VERSION_DATE}.json", artifacts["control"])
    write_json(OUT_DIR / f"OTG0_FOLLOWUP_GOAL_PROMPTS_{VERSION_DATE}.json", artifacts["prompts"])
    write_json(OUT_DIR / f"OTG0_COMPLETION_AUDIT_{VERSION_DATE}.json", artifacts["audit"])
    write_markdown_files(artifacts)
    audit_ok = artifacts["audit"]["can_mark_otg0_control_artifacts_complete"]
    print(
        json.dumps(
            {
                "status": "OK" if audit_ok else "ISSUES",
                "output_dir": rel(OUT_DIR),
                "packets": len(artifacts["packets"]["packets"]),
                "promotion_verdict": PROMOTION_VERDICT,
                "outcome_review_opened": False,
                "validation_safe": False,
            },
            sort_keys=True,
        )
    )
    return 0 if audit_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
