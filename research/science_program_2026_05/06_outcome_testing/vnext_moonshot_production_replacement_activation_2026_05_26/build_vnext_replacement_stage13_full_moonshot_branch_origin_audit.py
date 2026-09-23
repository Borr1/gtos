from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from build_vnext_replacement_stage13_full_market_element_audit import (
    ACTIVATED_FRAMEWORKS,
    ACTIVATED_POLICY,
    BROKER_ONBOARDING_LEDGER,
    CONTROL_LEDGER,
    FEATURE_LEDGER,
    MOONSHOT_DIR,
    OUTPUT_MANIFEST,
    OUTPUT_STATE,
    POLICIES,
    REPO_ROOT,
    ROUTE_DIR,
    ROUTE_ID,
    STAGE05_SHARD_MANIFEST,
    STAGE08_MAP,
    Stats,
    append_jsonl,
    fnum,
    iter_gzip_jsonl,
    iter_jsonl,
    kill_zone_bucket,
    load_broker_map,
    load_feature_map,
    load_repo_schedules,
    policy_value,
    prop_action,
    read_json,
    rel,
    route_label,
    write_json,
)


DATE = "2026-05-26"
STAGE_ID = "stage_13_full_moonshot_branch_and_origin_audit"

FULL_MARKET_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MARKET_ELEMENT_AUDIT_SUMMARY_{DATE}.json"
)
ORIGIN_REGISTRY = MOONSHOT_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_{DATE}.jsonl"
ORIGIN_SUMMARY = MOONSHOT_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_SUMMARY_{DATE}.json"
MARKET_AWARENESS_SUMMARY = MOONSHOT_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_SUMMARY_{DATE}.json"
SOURCE_CAPABILITY_SUMMARY = MOONSHOT_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_{DATE}.json"
SOURCE_CAPABILITY_LEDGER = MOONSHOT_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_LEDGER_{DATE}.jsonl"

OUTPUT_BRANCH_LEDGER = (
    ROUTE_DIR
    / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_BRANCH_REPAIR_LEDGER_{DATE}.jsonl"
)
OUTPUT_ORIGIN_LEDGER = (
    ROUTE_DIR
    / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_ORIGIN_CONTRACT_LEDGER_{DATE}.jsonl"
)
OUTPUT_ALLOWLIST = (
    ROUTE_DIR
    / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_REPAIRED_BRANCH_ALLOWLIST_{DATE}.json"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_BRANCH_ORIGIN_AUDIT_SUMMARY_{DATE}.json"
)

REPAIRED_SELECTOR_NAME = (
    "full_moonshot_follow_or_repaired_branch_broker_native_repaired_kz_"
    "be_after_trigger"
)
REPAIRED_BRANCH_ACTION = "MOONSHOT_REPAIRED_FOLLOW"
CURRENT_ORIGIN_NAMES = set(ACTIVATED_FRAMEWORKS)
SOURCE_READY_STATUSES = {
    "available",
    "available_but_parser_or_quote_contract_required",
    "forward_capture_required_for_exact_historical_truth",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _record_counter(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))


@dataclass
class BranchFamily:
    symbol: str
    framework: str
    candidate_origin_family: str
    session_bucket: str
    kill_zone_bucket: str
    broker_contract_status: str
    broker_session_hours_status: str
    schedule_evidence_class: str
    candidate_rows: int = 0
    executable_except_branch_rows: int = 0
    dynamic_available_rows: int = 0
    dynamic_unavailable_rows: int = 0
    branch_label_counts: Counter[str] = field(default_factory=Counter)
    executable_branch_label_counts: Counter[str] = field(default_factory=Counter)
    route_reason_counts: Counter[str] = field(default_factory=Counter)
    executable_route_reason_counts: Counter[str] = field(default_factory=Counter)
    source_window_counts: Counter[str] = field(default_factory=Counter)
    prop_action_counts: Counter[str] = field(default_factory=Counter)
    dynamic_unavailable_reason_counts: Counter[str] = field(default_factory=Counter)
    selected_policy_same_bar_ambiguous_rows: int = 0
    executable_stats: Stats = field(default_factory=Stats)
    follow_stats: Stats = field(default_factory=Stats)
    repaired_branch_stats: Stats = field(default_factory=Stats)

    @property
    def key(self) -> tuple[str, str, str, str, str]:
        return (
            self.symbol,
            self.framework,
            self.candidate_origin_family,
            self.session_bucket,
            self.kill_zone_bucket,
        )

    def positive_executable_except_branch(self) -> bool:
        metrics = self.executable_stats.record()
        expectancy = metrics["expectancy_r"]
        profit_factor = metrics["profit_factor"]
        return bool(
            self.executable_except_branch_rows
            and expectancy is not None
            and expectancy > 0
            and (profit_factor is None or profit_factor >= 1.0)
        )

    def proof_class(self) -> str:
        metrics = self.executable_stats.record()
        expectancy = metrics["expectancy_r"]
        profit_factor = metrics["profit_factor"]
        if self.broker_contract_status != "valid_broker_native_contract":
            return "broker_contract_invalid_or_unavailable"
        if not self.dynamic_available_rows:
            return "dynamic_policy_no_executable_rows"
        if self.kill_zone_bucket.startswith("missing_schedule"):
            return "missing_market_schedule_not_derivable"
        if self.kill_zone_bucket.startswith("outside_"):
            return "outside_configured_kill_zone_after_schedule_repair"
        if not self.executable_except_branch_rows:
            return "same_bar_or_source_path_gate_left_no_executable_rows"
        if expectancy is None or expectancy <= 0 or (
            profit_factor is not None and profit_factor < 1.0
        ):
            return "negative_expectancy_or_profit_factor_collapse"
        if self.follow_stats.count:
            return "positive_executable_follow_selector"
        return "positive_executable_repaired_branch_semantics"

    def final_action(self) -> str:
        proof = self.proof_class()
        if proof == "positive_executable_follow_selector":
            return "activate_existing_follow_semantics"
        if proof == "positive_executable_repaired_branch_semantics":
            return "activate_with_moonshot_repaired_branch_semantics"
        return "exclude_with_exact_proof"

    def record(self) -> dict[str, Any]:
        proof = self.proof_class()
        return {
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "schema_version": "vnext_replacement_stage13_full_moonshot_branch_family_v1",
            "symbol": self.symbol,
            "framework": self.framework,
            "candidate_origin_family": self.candidate_origin_family,
            "session_bucket": self.session_bucket,
            "kill_zone_bucket": self.kill_zone_bucket,
            "dynamic_policy_branch": ACTIVATED_POLICY,
            "broker_contract_status": self.broker_contract_status,
            "broker_session_hours_status": self.broker_session_hours_status,
            "schedule_evidence_class": self.schedule_evidence_class,
            "candidate_rows": self.candidate_rows,
            "dynamic_available_rows": self.dynamic_available_rows,
            "dynamic_unavailable_rows": self.dynamic_unavailable_rows,
            "executable_except_branch_rows": self.executable_except_branch_rows,
            "branch_label_counts": _record_counter(self.branch_label_counts),
            "executable_branch_label_counts": _record_counter(
                self.executable_branch_label_counts
            ),
            "route_reason_counts": _record_counter(self.route_reason_counts),
            "executable_route_reason_counts": _record_counter(
                self.executable_route_reason_counts
            ),
            "source_window_counts": _record_counter(self.source_window_counts),
            "prop_action_counts": _record_counter(self.prop_action_counts),
            "dynamic_unavailable_reason_counts": _record_counter(
                self.dynamic_unavailable_reason_counts
            ),
            "selected_policy_same_bar_ambiguous_rows": (
                self.selected_policy_same_bar_ambiguous_rows
            ),
            "metrics": self.executable_stats.record(),
            "existing_follow_metrics": self.follow_stats.record(),
            "repaired_branch_metrics": self.repaired_branch_stats.record(),
            "final_action": self.final_action(),
            "final_proof_class": proof,
            "repair_mechanism": (
                "derive MOONSHOT_REPAIRED_FOLLOW from broker-native, repaired-KZ, "
                "ordered selected-policy replay, positive family-level BE metrics, "
                "and route_reason/branch labels preserved as prior evidence only"
                if proof == "positive_executable_repaired_branch_semantics"
                else None
            ),
            "old_branch_labels_are_not_executable_trade_labels": proof
            == "positive_executable_repaired_branch_semantics",
            "broad_labels_not_used_as_terminal_proof": True,
        }


def family_key(row: dict[str, Any], kill_bucket: str) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("symbol")),
        str(row.get("framework")),
        str(row.get("candidate_origin_family")),
        str(row.get("session_bucket")),
        kill_bucket,
    )


def get_route_reason(row: dict[str, Any]) -> str:
    runtime = (row.get("runtime_reference") or {}).get("hypothetical_activated_vnext") or {}
    return str(runtime.get("route_reason") or "missing_route_reason")


def source_capability_counts() -> dict[str, int]:
    counts: Counter[str] = Counter()
    if not SOURCE_CAPABILITY_LEDGER.exists():
        return {}
    for row in iter_jsonl(SOURCE_CAPABILITY_LEDGER):
        counts[str(row.get("source_family") or row.get("family") or "unknown_source_family")] += 1
    return _record_counter(counts)


def origin_contract_rows(current_framework_counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    capability_counts = source_capability_counts()
    for row in iter_jsonl(ORIGIN_REGISTRY):
        name = str(row.get("name"))
        source_status = str(row.get("source_availability_status") or "missing")
        current_origin = name in CURRENT_ORIGIN_NAMES
        replay_rows = int(current_framework_counts.get(name, 0)) if current_origin else 0
        if current_origin:
            action = "current_origin_repaired_by_full_market_and_branch_selector"
            proof = "row_level_replay_exists"
            runtime_contract = "existing_model_a_candidate_framework"
        elif source_status == "forward_capture_required_for_exact_historical_truth":
            action = "exclude_until_forward_capture_generates_exact_historical_truth"
            proof = "non_generatable_missing_source_forward_capture_required"
            runtime_contract = "contract_recorded_no_activation_without_future_capture_rows"
        elif source_status == "available_but_parser_or_quote_contract_required":
            action = "exclude_until_parser_or_quote_contract_materializes_replay_rows"
            proof = "source_contract_or_parser_missing_for_row_level_replay"
            runtime_contract = "contract_recorded_no_activation_without_parser_rows"
        elif source_status == "available":
            action = "runtime_replay_contract_created_default_off_no_activation_rows_yet"
            proof = "no_row_level_candidate_replay_or_final_r_exists_in_current_route"
            runtime_contract = "candidate_origin_generator_and_replay_contract_required"
        else:
            action = "exclude_until_source_availability_repaired"
            proof = "missing_source_availability_status"
            runtime_contract = "contract_recorded_source_status_missing"
        rows.append(
            {
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "schema_version": "vnext_replacement_stage13_full_moonshot_origin_contract_v1",
                "registry_id": row.get("registry_id"),
                "origin_name": name,
                "category": row.get("category"),
                "current_gtos_status": row.get("current_gtos_status"),
                "candidate_clock": row.get("candidate_clock"),
                "source_availability_status": source_status,
                "source_requirements": row.get("source_requirements") or [],
                "asof_controls": row.get("asof_controls") or [],
                "next_replay_action": row.get("next_replay_action"),
                "current_route_replay_rows": replay_rows,
                "activation_action": action,
                "proof_class": proof,
                "runtime_replay_contract": runtime_contract,
                "source_capability_ledger": rel(SOURCE_CAPABILITY_LEDGER),
                "source_capability_family_counts_seen": capability_counts,
                "origin_is_positive_excluded_family": False,
                "positive_activation_permitted_now": bool(current_origin and replay_rows),
                "exact_blocker": (
                    "No Stage05 row-level candidates or dynamic final_r rows exist for this "
                    "origin in the current route; activation would be artifact-existence "
                    "substitution until the listed replay contract emits rows."
                    if not current_origin
                    else None
                ),
            }
        )
    return rows


def update_state_manifest(summary: dict[str, Any], generated_at: str) -> None:
    state = read_json(OUTPUT_STATE)
    state["last_updated_utc"] = generated_at
    state["first_incomplete_invariant"] = "stage_13_full_moonshot_runtime_selector_application_pending"
    state["exact_next_action"] = (
        "Patch runtime/config/replay/verifier to apply the full-moonshot "
        "FOLLOW-or-repaired-branch selector and rerun Stage13/Stage12 gates."
    )
    stage_status = state.setdefault("stage_status", {})
    stage_status[STAGE_ID] = "completed_runtime_selector_patch_required"
    rows = state.setdefault("evidence_rows_scanned", {})
    rows["stage13_full_moonshot_branch_family_rows"] = summary["branch_family_rows"]
    rows["stage13_full_moonshot_selected_rows"] = summary["repaired_selector"]["metrics"][
        "selected_count"
    ]
    rows["stage13_full_moonshot_repaired_branch_rows"] = summary["repaired_selector"][
        "repaired_branch_component"
    ]["metrics"]["selected_count"]
    rows["stage13_full_moonshot_origin_contract_rows"] = summary["origin_contract_rows"]
    tests = state.setdefault("tests_verifiers_run", [])
    tests.append(
        {
            "command": rel(Path(__file__)),
            "result": "passed; wrote full-moonshot branch repair and origin contract audit",
            "timestamp_utc": generated_at,
        }
    )
    write_json(OUTPUT_STATE, state)

    manifest = read_json(OUTPUT_MANIFEST)
    outputs = manifest.setdefault("outputs", [])
    existing = {row.get("path") for row in outputs if isinstance(row, dict)}
    for path, row_count, description in [
        (OUTPUT_BRANCH_LEDGER, summary["branch_family_rows"], "full-moonshot branch repair ledger"),
        (OUTPUT_ORIGIN_LEDGER, summary["origin_contract_rows"], "full-moonshot origin contract ledger"),
        (OUTPUT_ALLOWLIST, len(summary["repaired_branch_allowlist"]["entries"]), "runtime repaired-branch allowlist"),
        (OUTPUT_SUMMARY, 1, "full-moonshot branch/origin audit summary"),
    ]:
        rpath = rel(path)
        if rpath not in existing:
            outputs.append(
                {
                    "path": rpath,
                    "stage_id": STAGE_ID,
                    "row_count": row_count,
                    "description": description,
                }
            )
    write_json(OUTPUT_MANIFEST, manifest)

    append_jsonl(
        CONTROL_LEDGER,
        {
            "event": "stage13_full_moonshot_branch_origin_audit_completed",
            "generated_at_utc": generated_at,
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "status": "completed_runtime_selector_patch_required",
            "selector_name": summary["repaired_selector"]["selector_name"],
            "selected_rows": summary["repaired_selector"]["metrics"]["selected_count"],
            "expectancy_r": summary["repaired_selector"]["metrics"]["expectancy_r"],
            "profit_factor": summary["repaired_selector"]["metrics"]["profit_factor"],
            "repaired_branch_rows": summary["repaired_selector"]["repaired_branch_component"][
                "metrics"
            ]["selected_count"],
            "first_incomplete_invariant_after_stage": (
                "stage_13_full_moonshot_runtime_selector_application_pending"
            ),
        },
    )


def write_rows(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> None:
    generated_at = utc_now()
    stage08 = read_json(STAGE08_MAP)
    eligible_symbols = set(stage08["broker_native_activation_eligible_symbols"])
    full_market_summary = read_json(FULL_MARKET_SUMMARY)
    origin_summary = read_json(ORIGIN_SUMMARY)
    market_awareness_summary = read_json(MARKET_AWARENESS_SUMMARY)
    source_capability_summary = read_json(SOURCE_CAPABILITY_SUMMARY)
    features = load_feature_map()
    broker = load_broker_map()
    schedules = load_repo_schedules()

    families: dict[tuple[str, str, str, str, str], BranchFamily] = {}
    selected_stats = {policy: Stats() for policy in POLICIES}
    follow_stats = {policy: Stats() for policy in POLICIES}
    repaired_only_stats = {policy: Stats() for policy in POLICIES}
    selected_symbol_counts: Counter[str] = Counter()
    selected_framework_counts: Counter[str] = Counter()
    selected_session_counts: Counter[str] = Counter()
    selected_kill_zone_counts: Counter[str] = Counter()
    selected_schedule_counts: Counter[str] = Counter()
    selected_branch_label_counts: Counter[str] = Counter()
    selected_route_reason_counts: Counter[str] = Counter()
    selected_source_window_counts: Counter[str] = Counter()
    selected_prop_action_counts: Counter[str] = Counter()
    candidate_rows_scanned = 0
    executable_except_branch_rows = 0
    rows_for_second_pass: list[tuple[dict[str, Any], tuple[str, str, str, str, str], str, str, str, str]] = []

    def get_family(
        row: dict[str, Any],
        key: tuple[str, str, str, str, str],
        schedule_class: str,
    ) -> BranchFamily:
        if key not in families:
            symbol = key[0]
            broker_info = broker.get(symbol, {})
            families[key] = BranchFamily(
                symbol=symbol,
                framework=key[1],
                candidate_origin_family=key[2],
                session_bucket=key[3],
                kill_zone_bucket=key[4],
                broker_contract_status=str(
                    broker_info.get("broker_contract_status") or "missing_broker_onboarding"
                ),
                broker_session_hours_status=str(
                    broker_info.get("session_hours_status") or "missing_session_hours_status"
                ),
                schedule_evidence_class=schedule_class,
            )
        return families[key]

    for manifest_row in iter_jsonl(STAGE05_SHARD_MANIFEST):
        shard_path = REPO_ROOT / manifest_row["output_chunk_path"]
        for row in iter_gzip_jsonl(shard_path):
            candidate_rows_scanned += 1
            symbol = str(row.get("symbol"))
            feature = features.get(str(row.get("candidate_id")), {})
            broker_info = broker.get(symbol, {})
            kill_bucket, schedule_class = kill_zone_bucket(
                symbol=symbol,
                row=row,
                feature=feature,
                schedules=schedules,
                broker_session_hours_status=str(
                    broker_info.get("session_hours_status") or "missing_session_hours_status"
                ),
            )
            key = family_key(row, kill_bucket)
            family = get_family(row, key, schedule_class)
            branch = route_label(row)
            route_reason = get_route_reason(row)
            dynamic = row.get("dynamic_policy_replay") or {}
            available = dynamic.get("available") is True
            value = policy_value(row, ACTIVATED_POLICY)
            family.candidate_rows += 1
            family.branch_label_counts[branch] += 1
            family.route_reason_counts[route_reason] += 1
            family.source_window_counts[str(row.get("source_window_complete"))] += 1
            if feature.get("selected_policy_same_bar_ambiguous"):
                family.selected_policy_same_bar_ambiguous_rows += 1
            if not available:
                family.dynamic_unavailable_rows += 1
                family.dynamic_unavailable_reason_counts[
                    str(dynamic.get("exclusion_reason") or "missing_dynamic_exclusion_reason")
                ] += 1
                continue
            family.dynamic_available_rows += 1
            executable_except_branch = bool(
                symbol in eligible_symbols
                and row.get("framework") in ACTIVATED_FRAMEWORKS
                and kill_bucket.startswith("in_")
                and not feature.get("selected_policy_same_bar_ambiguous")
                and value is not None
            )
            if not executable_except_branch:
                continue
            executable_except_branch_rows += 1
            family.executable_except_branch_rows += 1
            family.executable_branch_label_counts[branch] += 1
            family.executable_route_reason_counts[route_reason] += 1
            family.prop_action_counts[prop_action(row)] += 1
            family.executable_stats.add(value)
            if branch == "FOLLOW":
                family.follow_stats.add(value)
            else:
                family.repaired_branch_stats.add(value)
            rows_for_second_pass.append((row, key, branch, route_reason, schedule_class, kill_bucket))

    allow_keys = {
        key
        for key, family in families.items()
        if family.positive_executable_except_branch()
    }
    allowlist_entries: list[dict[str, Any]] = []
    for key in sorted(allow_keys):
        family = families[key]
        if not family.repaired_branch_stats.count:
            continue
        allowlist_entries.append(
            {
                "symbol": family.symbol,
                "framework": family.framework,
                "candidate_origin_family": family.candidate_origin_family,
                "session_bucket": family.session_bucket,
                "kill_zone_bucket": family.kill_zone_bucket,
                "dynamic_policy_branch": ACTIVATED_POLICY,
                "repaired_branch_action": REPAIRED_BRANCH_ACTION,
                "allowed_prior_branch_labels": [
                    label
                    for label, count in sorted(family.executable_branch_label_counts.items())
                    if label != "FOLLOW" and count
                ],
                "route_reason_counts": _record_counter(family.executable_route_reason_counts),
                "source_window_counts": _record_counter(family.source_window_counts),
                "schedule_evidence_class": family.schedule_evidence_class,
                "metrics": family.executable_stats.record(),
                "repaired_branch_metrics": family.repaired_branch_stats.record(),
                "proof_class": "positive_executable_repaired_branch_semantics",
            }
        )

    for row, key, branch, route_reason, schedule_class, kill_bucket in rows_for_second_pass:
        if key not in allow_keys:
            continue
        value = policy_value(row, ACTIVATED_POLICY)
        if value is None:
            continue
        for policy in POLICIES:
            selected_stats[policy].add(policy_value(row, policy))
            if branch == "FOLLOW":
                follow_stats[policy].add(policy_value(row, policy))
            else:
                repaired_only_stats[policy].add(policy_value(row, policy))
        selected_symbol_counts[str(row.get("symbol"))] += 1
        selected_framework_counts[str(row.get("framework"))] += 1
        selected_session_counts[str(row.get("session_bucket"))] += 1
        selected_kill_zone_counts[kill_bucket] += 1
        selected_schedule_counts[schedule_class] += 1
        selected_branch_label_counts[branch] += 1
        selected_route_reason_counts[route_reason] += 1
        selected_source_window_counts[str(row.get("source_window_complete"))] += 1
        selected_prop_action_counts[prop_action(row)] += 1

    branch_records = [family.record() for family in families.values()]
    branch_records.sort(
        key=lambda row: (
            row["symbol"],
            row["framework"],
            row["candidate_origin_family"],
            row["session_bucket"],
            row["kill_zone_bucket"],
        )
    )
    origin_rows = origin_contract_rows(
        full_market_summary["activated_selector"]["coverage"]["selected_framework_counts"]
    )
    write_rows(OUTPUT_BRANCH_LEDGER, branch_records)
    write_rows(OUTPUT_ORIGIN_LEDGER, origin_rows)
    write_json(
        OUTPUT_ALLOWLIST,
        {
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "schema_version": "vnext_replacement_stage13_repaired_branch_allowlist_v1",
            "generated_at_utc": generated_at,
            "selector_name": REPAIRED_SELECTOR_NAME,
            "repaired_branch_action": REPAIRED_BRANCH_ACTION,
            "selected_policy": ACTIVATED_POLICY,
            "entries": allowlist_entries,
        },
    )

    proof_counts = Counter(row["final_proof_class"] for row in branch_records)
    action_counts = Counter(row["final_action"] for row in branch_records)
    positive_excluded = [
        row
        for row in branch_records
        if row["final_action"] == "exclude_with_exact_proof"
        and row["metrics"]["expectancy_r"] is not None
        and row["metrics"]["expectancy_r"] > 0
    ]
    origin_proof_counts = Counter(row["proof_class"] for row in origin_rows)
    non_current_contracts = [row for row in origin_rows if row["origin_name"] not in CURRENT_ORIGIN_NAMES]
    selected_metrics = selected_stats[ACTIVATED_POLICY].record()
    summary = {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "schema_version": "vnext_replacement_stage13_full_moonshot_branch_origin_audit_summary_v1",
        "generated_at_utc": generated_at,
        "no_top_n_or_lossy_summary": True,
        "input_artifacts": {
            "stage05_shard_manifest": rel(STAGE05_SHARD_MANIFEST),
            "stage08_market_map": rel(STAGE08_MAP),
            "broker_onboarding_ledger": rel(BROKER_ONBOARDING_LEDGER),
            "feature_ledger": rel(FEATURE_LEDGER),
            "full_market_summary": rel(FULL_MARKET_SUMMARY),
            "origin_registry": rel(ORIGIN_REGISTRY),
            "origin_summary": rel(ORIGIN_SUMMARY),
            "market_awareness_summary": rel(MARKET_AWARENESS_SUMMARY),
            "source_capability_summary": rel(SOURCE_CAPABILITY_SUMMARY),
            "source_capability_ledger": rel(SOURCE_CAPABILITY_LEDGER),
        },
        "output_paths": {
            "branch_repair_ledger": rel(OUTPUT_BRANCH_LEDGER),
            "origin_contract_ledger": rel(OUTPUT_ORIGIN_LEDGER),
            "repaired_branch_allowlist": rel(OUTPUT_ALLOWLIST),
            "summary": rel(OUTPUT_SUMMARY),
        },
        "candidate_rows_scanned": candidate_rows_scanned,
        "executable_except_branch_rows": executable_except_branch_rows,
        "branch_family_rows": len(branch_records),
        "origin_contract_rows": len(origin_rows),
        "origin_registry_rows": origin_summary.get("origin_registry_rows"),
        "non_current_origin_contract_rows": len(non_current_contracts),
        "repaired_selector": {
            "selector_name": REPAIRED_SELECTOR_NAME,
            "selected_policy": ACTIVATED_POLICY,
            "activated_frameworks": list(ACTIVATED_FRAMEWORKS),
            "branch_semantics_rule": (
                "FOLLOW rows are executable directly; AVOID/MIXED/LEGACY rows remain "
                "non-executable unless their family appears in the repaired branch "
                "allowlist with positive row-level BE metrics and exact broker/KZ/path proof."
            ),
            "old_branch_labels_treated_as_trade_labels": False,
            "broker_native_required": True,
            "configured_or_repo_repaired_kill_zone_required": True,
            "selected_policy_same_bar_ambiguous_allowed": False,
            "source_window_complete_required_for_selection": False,
            "source_completeness_rule": (
                "source completeness is capture quality evidence, not a selection proxy"
            ),
            "metrics": selected_metrics,
            "coverage": {
                "selected_symbol_counts": _record_counter(selected_symbol_counts),
                "selected_framework_counts": _record_counter(selected_framework_counts),
                "selected_session_counts": _record_counter(selected_session_counts),
                "selected_kill_zone_counts": _record_counter(selected_kill_zone_counts),
                "selected_schedule_evidence_counts": _record_counter(selected_schedule_counts),
                "selected_branch_label_counts": _record_counter(selected_branch_label_counts),
                "selected_route_reason_counts": _record_counter(selected_route_reason_counts),
                "selected_source_window_counts": _record_counter(selected_source_window_counts),
                "selected_prop_action_counts": _record_counter(selected_prop_action_counts),
            },
            "comparator_metrics_on_selected_rows": {
                policy: selected_stats[policy].record() for policy in POLICIES
            },
            "existing_follow_component": {
                "metrics": follow_stats[ACTIVATED_POLICY].record(),
                "comparator_metrics": {policy: follow_stats[policy].record() for policy in POLICIES},
            },
            "repaired_branch_component": {
                "metrics": repaired_only_stats[ACTIVATED_POLICY].record(),
                "comparator_metrics": {
                    policy: repaired_only_stats[policy].record() for policy in POLICIES
                },
            },
            "extends_full_market_follow_selector": (
                selected_metrics["selected_count"]
                > full_market_summary["activated_selector"]["metrics"]["selected_count"]
            ),
            "prior_full_market_follow_rows": full_market_summary["activated_selector"]["metrics"][
                "selected_count"
            ],
        },
        "repaired_branch_allowlist": {
            "path": rel(OUTPUT_ALLOWLIST),
            "entries": allowlist_entries,
            "entry_count": len(allowlist_entries),
        },
        "branch_family_action_counts": dict(sorted(action_counts.items())),
        "branch_family_proof_class_counts": dict(sorted(proof_counts.items())),
        "positive_excluded_after_repair_count": len(positive_excluded),
        "positive_excluded_after_repair_proof_counts": dict(
            sorted(Counter(row["final_proof_class"] for row in positive_excluded).items())
        ),
        "origin_contract_proof_counts": dict(sorted(origin_proof_counts.items())),
        "non_current_origin_activation_summary": {
            "contract_created_rows": len(non_current_contracts),
            "current_route_non_current_origin_replay_rows": sum(
                row["current_route_replay_rows"] for row in non_current_contracts
            ),
            "activation_now_rows": sum(
                1 for row in non_current_contracts if row["positive_activation_permitted_now"]
            ),
            "contract_action_counts": dict(
                sorted(Counter(row["activation_action"] for row in non_current_contracts).items())
            ),
        },
        "market_awareness_rows": market_awareness_summary.get("feature_rows"),
        "source_capability_summary": source_capability_summary,
        "final_repair_action": (
            "patch runtime/config/replay/verifier to apply the full-moonshot "
            "FOLLOW-or-MOONSHOT_REPAIRED_FOLLOW selector; keep non-current "
            "origin contracts default-off until row-level replay exists"
        ),
    }
    write_json(OUTPUT_SUMMARY, summary)
    update_state_manifest(summary, generated_at)
    print(
        json.dumps(
            {
                "status": "completed_runtime_selector_patch_required",
                "selected_rows": selected_metrics["selected_count"],
                "expectancy_r": selected_metrics["expectancy_r"],
                "profit_factor": selected_metrics["profit_factor"],
                "repaired_branch_rows": repaired_only_stats[ACTIVATED_POLICY].count,
                "allowlist_entries": len(allowlist_entries),
                "positive_excluded_after_repair_count": len(positive_excluded),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
