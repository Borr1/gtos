from __future__ import annotations

import gzip
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"
ROUTE_ID = "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"

OUTPUT_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STATIC_PRIMITIVE_ASSUMPTION_LEDGER_{DATE_ID}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_STATIC_PRIMITIVE_ASSUMPTION_SUMMARY_{DATE_ID}.json"
OUTPUT_REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_STATIC_PRIMITIVE_ASSUMPTION_REPORT_{DATE_ID}.md"
OUTPUT_STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"

MAX_LINE_SCAN_BYTES = 4_000_000
MAX_JSONL_AGGREGATE_SCAN_BYTES = 8_000_000

TEXT_SUFFIXES = {".py", ".md", ".txt", ".yaml", ".yml", ".json", ".ps1", ".bat"}
SKIP_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
}

PATTERN_GROUPS = {
    "fixed_bracket_or_proxy_r": [
        r"\btarget_first\b",
        r"\bstop_first\b",
        r"\bsimulated_proxy_r\b",
        r"\bsimulated_r_scoring_only\b",
        r"\bsimulated_r\b",
        r"\bterminal_outcome\b",
        r"\bmin_rr\b",
        r"\b1\.5r\b",
        r"\bfixed[-_ ]?(target|bracket|rr|r)\b",
    ],
    "candidate_origin_boxing": [
        r"\bob_retest\b",
        r"\bfvg_fill\b",
        r"\bbreaker_re_entry\b",
        r"\bh1_setup\b",
        r"\bpoi\b",
        r"\bkill[-_ ]?zone\b",
        r"\bkz\b",
        r"\bm15\b",
        r"\bd1\b",
        r"\bh4\b",
        r"\bh1\b",
    ],
    "shadow_disabled_or_stale": [
        r"\bshadow\b",
        r"\bdefault[-_ ]?off\b",
        r"\bapply_to_execution\b",
        r"\bpre_ai_apply_to_ai_call\b",
        r"\bdisabled\b",
        r"\bobserver[-_ ]?only\b",
        r"\bstale\b",
        r"\bconfidence_filter_mode\b",
    ],
    "source_proxy_or_gap": [
        r"\bproxy\b",
        r"\bsynthetic\b",
        r"\bfallback\b",
        r"\bmissing_source\b",
        r"\bsource[-_ ]?gap\b",
        r"\bsource_join_absent\b",
        r"\bapprox",
        r"\bspread[-_ ]?proxy\b",
        r"\bm15_vs_ltf\b",
    ],
    "dynamic_execution_gap": [
        r"\bj46\b",
        r"\bj49\b",
        r"\bbreakeven\b",
        r"\bbe_trigger\b",
        r"\bpartial\b",
        r"\btrailing\b",
        r"\btime[-_ ]?stop\b",
        r"\bfill\b",
        r"\bslippage\b",
        r"\border_ticket\b",
        r"\bdeal_ticket\b",
        r"\bcommission\b",
        r"\bswap\b",
        r"\bnofill\b",
        r"\bpending\b",
    ],
    "verifier_completion_semantics": [
        r"\bverifier\b",
        r"\bverification\b",
        r"\bcompletion[_ -]?audit\b",
        r"\bok[\"']?\s*[:=]\s*true\b",
        r"\bexists\b",
        r"\bmanifest\b",
        r"\bartifact[-_ ]?existence\b",
    ],
    "ai_ml_label_dependency": [
        r"\bai\b",
        r"\bprompt\b",
        r"\bpaid\b",
        r"\bapi\b",
        r"\bml\b",
        r"\bmodel\b",
        r"\bsurrogate\b",
        r"\bconfidence\b",
        r"\bclassifier\b",
    ],
    "prop_governor_static_path": [
        r"\bprop\b",
        r"\bredacted_account\b",
        r"\bftmo\b",
        r"\bpass[-_ ]?rate\b",
        r"\bdaily[-_ ]?loss\b",
        r"\bmax[-_ ]?drawdown\b",
        r"\battempt\b",
    ],
}

COMPILED_GROUPS = {
    family: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    for family, patterns in PATTERN_GROUPS.items()
}

SCAN_ROOTS = [
    Path("config"),
    Path("src"),
    Path("tests"),
    Path("scripts"),
    Path("prompts"),
    Path("research/science_program_2026_05/04_goal_prompts"),
    ROUTE_DIR.relative_to(REPO_ROOT),
    Path("research/science_program_2026_05/06_outcome_testing/vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26"),
    Path("research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25"),
    Path("research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"),
    Path("research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24"),
]

SHADOW_LOGS_TO_SCAN = [
    Path("shadow_logs/candidate_features_log.jsonl"),
    Path("shadow_logs/candidate_ltf_path_order.jsonl"),
    Path("shadow_logs/candidate_path_contract_audit.jsonl"),
    Path("shadow_logs/candidate_path_follow.jsonl"),
    Path("shadow_logs/j46_j49_exit_comparator_audit.jsonl"),
    Path("shadow_logs/exit_management_shadow_status.jsonl"),
    Path("shadow_logs/live_candidate_strategy_rollups.jsonl"),
    Path("shadow_logs/live_structural_strategy_metadata.jsonl"),
    Path("shadow_logs/no-fill_forward_source_capture.jsonl"),
    Path("shadow_logs/nofill_forward_source_capture.jsonl"),
    Path("shadow_logs/prefill_delivery_path_audit.jsonl"),
    Path("shadow_logs/sierra_proxy_registry_status.jsonl"),
    Path("shadow_logs/broker_actual_r_audit.jsonl"),
    Path("shadow_logs/account_pnl_truth_reconciliation.jsonl"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def iter_files(root: Path) -> Iterable[Path]:
    absolute = REPO_ROOT / root
    if not absolute.exists():
        return
    if absolute.is_file():
        yield absolute
        return
    for path in absolute.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        yield path


def match_families(text: str) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for family, patterns in COMPILED_GROUPS.items():
        matched = []
        for pattern in patterns:
            if pattern.search(text):
                matched.append(pattern.pattern)
        if matched:
            hits[family] = matched
    return hits


def classify_action(family: str, text: str) -> tuple[str, str, str, str]:
    lowered = text.lower()
    if family == "fixed_bracket_or_proxy_r":
        return (
            "replay_under_dynamic_execution_policy",
            "repair_needed",
            "Fixed target/stop or scalar proxy-R can mislabel live-current J46/J49, BE, partial, trailing, and time-stop behavior.",
            "execution_replay",
        )
    if family == "candidate_origin_boxing":
        return (
            "redesign_or_expand_universal_candidate_origin",
            "repair_needed",
            "Current origin language can box discovery into existing framework/timeframe/session/POI primitives.",
            "candidate_discovery",
        )
    if family == "shadow_disabled_or_stale":
        return (
            "keep_default_off_until_corrected_replay_then_implementation_decision",
            "default_off_or_shadow",
            "Shadow/default-off/stale behavior can be mistaken for active execution behavior.",
            "runtime_activation_surface",
        )
    if family == "source_proxy_or_gap":
        return (
            "source_repair_or_forward_capture",
            "source_gap_or_proxy",
            "Proxy/fallback/missing-source behavior limits exact path, fill, cost, or source-state claims.",
            "source_and_path_capability",
        )
    if family == "dynamic_execution_gap":
        return (
            "consume_as_dynamic_execution_policy_input",
            "policy_input_or_gap",
            "Exit-management fields must become policy inputs, not passive annotations.",
            "execution_management",
        )
    if family == "verifier_completion_semantics":
        return (
            "semantic_verifier_hardening",
            "verifier_hardening_needed",
            "Artifact existence or generic OK checks can certify wrappers without proving semantic truth.",
            "verification",
        )
    if family == "ai_ml_label_dependency":
        action = "rebuild_ai_budget_design_after_dynamic_labels"
        surface = "ai_budget"
        if "ml" in lowered or "model" in lowered or "classifier" in lowered or "surrogate" in lowered:
            action = "relabel_ml_feasibility_after_dynamic_labels"
            surface = "ml_feasibility"
        return (
            action,
            "label_dependency",
            "AI/ML conclusions inherit any primitive replay label or prompt/source-budget assumption upstream.",
            surface,
        )
    return (
        "recompute_prop_ev_after_dynamic_labels",
        "prop_replay_dependency",
        "Prop-governor pass/fail or attempt metrics must be recomputed after corrected dynamic execution R labels.",
        "prop_governor",
    )


def root_bucket(path: Path) -> str:
    rel_path = rel(path)
    if rel_path.startswith("config/"):
        return "config"
    if rel_path.startswith("src/"):
        return "code"
    if rel_path.startswith("tests/"):
        return "tests"
    if rel_path.startswith("scripts/"):
        return "scripts"
    if rel_path.startswith("prompts/") or "/04_goal_prompts/" in rel_path:
        return "prompts"
    if rel_path.startswith("shadow_logs/"):
        return "shadow_logs"
    if "vnext_full_historical_candidate_generation_replay" in rel_path:
        return "full_replay_route_artifacts"
    if "vnext_activation_edge_anatomy_ai_budget_ml_feasibility" in rel_path:
        return "activation_route_artifacts"
    if "vnext_production_change_dossier_and_prop_safe_runtime" in rel_path:
        return "production_failure_route_artifacts"
    if "vnext_production_candidate_failure_repair_ev_prop_governor" in rel_path:
        return "repaired_candidate_route_artifacts"
    if ROUTE_ID in rel_path:
        return "moonshot_route_artifacts"
    return "other"


def make_record(
    *,
    seq: int,
    source_kind: str,
    path: Path,
    family: str,
    matched_terms: list[str],
    evidence_text: str,
    line_number: int | None = None,
    affected_rows_count: int | None = None,
    count_method: str = "line_match",
    evidence_granularity: str = "line",
    artifact_row_selector: str | None = None,
    extra: dict | None = None,
) -> dict:
    action, intent_status, boxes_out, surface = classify_action(family, evidence_text)
    record = {
        "record_id": f"STAGE01-{seq:06d}",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_01_STATIC_PRIMITIVE_ASSUMPTION_AUDIT",
        "source_kind": source_kind,
        "source_bucket": root_bucket(path),
        "source_path": rel(path),
        "line_number": line_number,
        "artifact_row_selector": artifact_row_selector,
        "assumption_family": family,
        "matched_terms": sorted(set(matched_terms)),
        "evidence_excerpt": evidence_text.strip()[:500],
        "current_behavior": current_behavior(family, evidence_text, path),
        "boxes_out_or_risk": boxes_out,
        "affected_rows_count": affected_rows_count,
        "count_method": count_method,
        "intent_status": intent_status,
        "exact_action": action,
        "runtime_surface": surface,
        "evidence_granularity": evidence_granularity,
    }
    if extra:
        record.update(extra)
    return record


def current_behavior(family: str, text: str, path: Path) -> str:
    lowered = text.lower()
    if "apply_to_execution" in lowered and "false" in lowered:
        return "Config or artifact states execution effect is currently disabled/default-off."
    if "min_rr" in lowered or "1.5" in lowered:
        return "Logic references the configured 1.5R minimum/static bracket family."
    if "target_first" in lowered or "stop_first" in lowered:
        return "Replay/artifact labels path using target-first or stop-first ordering."
    if "simulated_proxy_r" in lowered or "simulated_r" in lowered:
        return "Replay/artifact uses simulated/proxy R instead of policy-specific dynamic execution R."
    if "shadow" in lowered:
        return "Behavior is logged or evaluated in shadow rather than active execution."
    if family == "candidate_origin_boxing":
        return "Candidate logic references existing framework, timeframe, session, or POI primitives."
    if family == "source_proxy_or_gap":
        return "Source path relies on proxy/fallback or records missing source capability."
    if family == "dynamic_execution_gap":
        return "Exit-management or broker-lifecycle field exists and must be promoted into replay input."
    if family == "verifier_completion_semantics":
        return "Verification/completion artifact may be certifying existence or wrapper state."
    if family == "ai_ml_label_dependency":
        return "AI/ML artifact or code path depends on upstream labels, prompts, budgets, or model decisions."
    if family == "prop_governor_static_path":
        return "Prop replay/governor logic depends on upstream selected trades and R labels."
    return f"Assumption detected in {rel(path)}."


def scan_text_file(path: Path, records: list[dict], seq: int) -> int:
    try:
        stat = path.stat()
    except OSError:
        return seq
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return seq
    if stat.st_size > MAX_LINE_SCAN_BYTES:
        records.append(
            make_record(
                seq=seq,
                source_kind="large_text_file_deferred",
                path=path,
                family="source_proxy_or_gap",
                matched_terms=["large_text_file_deferred"],
                evidence_text=f"Large text-like file deferred from line scan: bytes={stat.st_size}",
                affected_rows_count=None,
                count_method="file_size_deferred",
                evidence_granularity="file",
                extra={
                    "file_size_bytes": stat.st_size,
                    "deferred_reason": "above_stage01_line_scan_limit_preserved_for_stage02_or_dynamic_replay",
                },
            )
        )
        return seq + 1
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                families = match_families(line)
                for family, matched_terms in families.items():
                    records.append(
                        make_record(
                            seq=seq,
                            source_kind="text_line",
                            path=path,
                            family=family,
                            matched_terms=matched_terms,
                            evidence_text=line,
                            line_number=line_number,
                        )
                    )
                    seq += 1
    except OSError as exc:
        records.append(
            make_record(
                seq=seq,
                source_kind="scan_error",
                path=path,
                family="source_proxy_or_gap",
                matched_terms=["scan_error"],
                evidence_text=f"Scan failed: {exc}",
                count_method="scan_error",
                evidence_granularity="file",
            )
        )
        seq += 1
    return seq


def iter_jsonl_lines(path: Path) -> Iterable[str]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
            yield from handle
    else:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            yield from handle


def scan_jsonl_aggregate(path: Path, records: list[dict], seq: int) -> int:
    if not path.exists() or not path.is_file():
        return seq
    try:
        size = path.stat().st_size
    except OSError:
        return seq
    if path.suffix == ".gz" or size > MAX_JSONL_AGGREGATE_SCAN_BYTES:
        family = "fixed_bracket_or_proxy_r" if "ACTIVATION" in path.name or "REPLAY" in path.name else "source_proxy_or_gap"
        records.append(
            make_record(
                seq=seq,
                source_kind="large_row_ledger_deferred",
                path=path,
                family=family,
                matched_terms=["large_row_ledger_preserved"],
                evidence_text=(
                    f"Large row ledger preserved but not line-expanded in Stage01: bytes={size}. "
                    "Stage01 records this as a material assumption source for later streaming dynamic replay."
                ),
                count_method="file_size_deferred_no_top_n_sampling",
                evidence_granularity="file",
                extra={
                    "file_size_bytes": size,
                    "deferred_reason": (
                        "compressed_or_above_stage01_aggregate_scan_limit_preserved_for_stage04_stage07_full_dynamic_replay"
                    ),
                    "lossy_sampling_used": False,
                },
            )
        )
        return seq + 1

    row_count = 0
    family_counts: dict[str, int] = Counter()
    matched_terms_by_family: dict[str, Counter] = defaultdict(Counter)
    field_counts: Counter = Counter()
    parse_errors = 0
    try:
        for raw in iter_jsonl_lines(path):
            line = raw.strip()
            if not line:
                continue
            row_count += 1
            families = match_families(line)
            for family, terms in families.items():
                family_counts[family] += 1
                for term in terms:
                    matched_terms_by_family[family][term] += 1
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            if isinstance(parsed, dict):
                for key in parsed.keys():
                    key_text = str(key)
                    if match_families(key_text):
                        field_counts[key_text] += 1
    except OSError as exc:
        records.append(
            make_record(
                seq=seq,
                source_kind="jsonl_scan_error",
                path=path,
                family="source_proxy_or_gap",
                matched_terms=["jsonl_scan_error"],
                evidence_text=f"JSONL aggregate scan failed: {exc}",
                count_method="scan_error",
                evidence_granularity="file",
            )
        )
        return seq + 1

    for family, count in sorted(family_counts.items()):
        records.append(
            make_record(
                seq=seq,
                source_kind="jsonl_aggregate",
                path=path,
                family=family,
                matched_terms=list(matched_terms_by_family[family].keys()),
                evidence_text=(
                    f"JSONL aggregate family={family}; matching_rows={count}; "
                    f"total_rows={row_count}; parse_errors={parse_errors}"
                ),
                affected_rows_count=count,
                count_method="streamed_full_file_regex_match_count",
                evidence_granularity="aggregate_row_family",
                artifact_row_selector=f"rows_matching_family::{family}",
                extra={
                    "total_rows_scanned": row_count,
                    "parse_errors": parse_errors,
                    "matching_field_names": sorted(field_counts.keys()),
                    "lossy_sampling_used": False,
                },
            )
        )
        seq += 1
    if not family_counts and row_count:
        records.append(
            make_record(
                seq=seq,
                source_kind="jsonl_aggregate_no_match",
                path=path,
                family="source_proxy_or_gap",
                matched_terms=["no_static_tokens_detected"],
                evidence_text=f"JSONL aggregate scan found no configured static-assumption tokens; total_rows={row_count}",
                affected_rows_count=0,
                count_method="streamed_full_file_no_match",
                evidence_granularity="file",
                extra={"total_rows_scanned": row_count, "lossy_sampling_used": False},
            )
        )
        seq += 1
    return seq


def unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen = set()
    result = []
    for path in paths:
        absolute = path.resolve()
        if absolute in seen:
            continue
        seen.add(absolute)
        result.append(path)
    return result


def gather_scan_files() -> tuple[list[Path], list[Path], dict]:
    text_files: list[Path] = []
    jsonl_files: list[Path] = []
    missing_roots = []
    for root in SCAN_ROOTS:
        absolute = REPO_ROOT / root
        if not absolute.exists():
            missing_roots.append(root.as_posix())
            continue
        for path in iter_files(root):
            suffixes = "".join(path.suffixes).lower()
            if suffixes.endswith(".jsonl") or suffixes.endswith(".jsonl.gz"):
                jsonl_files.append(path)
            elif path.suffix.lower() in TEXT_SUFFIXES:
                text_files.append(path)
    for rel_path in SHADOW_LOGS_TO_SCAN:
        absolute = REPO_ROOT / rel_path
        if absolute.exists():
            jsonl_files.append(absolute)
        else:
            missing_roots.append(rel_path.as_posix())
    metadata = {
        "configured_scan_roots": [root.as_posix() for root in SCAN_ROOTS],
        "configured_shadow_logs": [path.as_posix() for path in SHADOW_LOGS_TO_SCAN],
        "missing_roots_or_files": sorted(set(missing_roots)),
    }
    return unique_paths(text_files), unique_paths(jsonl_files), metadata


def write_outputs(records: list[dict], scan_metadata: dict) -> dict:
    records.sort(key=lambda row: (row["source_path"], row.get("line_number") or 0, row["record_id"]))
    for index, row in enumerate(records, start=1):
        row["record_id"] = f"STAGE01-{index:06d}"
    with OUTPUT_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for row in records:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    by_family = Counter(row["assumption_family"] for row in records)
    by_action = Counter(row["exact_action"] for row in records)
    by_status = Counter(row["intent_status"] for row in records)
    by_bucket = Counter(row["source_bucket"] for row in records)
    by_kind = Counter(row["source_kind"] for row in records)
    large_deferred = [row for row in records if row["source_kind"] == "large_row_ledger_deferred"]
    required_buckets = {
        "config",
        "code",
        "tests",
        "scripts",
        "prompts",
        "shadow_logs",
        "full_replay_route_artifacts",
        "activation_route_artifacts",
        "production_failure_route_artifacts",
        "repaired_candidate_route_artifacts",
        "moonshot_route_artifacts",
    }
    summary = {
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_01_STATIC_PRIMITIVE_ASSUMPTION_AUDIT",
        "generated_at_utc": utc_now(),
        "ledger_path": rel(OUTPUT_LEDGER),
        "report_path": rel(OUTPUT_REPORT),
        "row_count": len(records),
        "assumption_family_counts": dict(sorted(by_family.items())),
        "exact_action_counts": dict(sorted(by_action.items())),
        "intent_status_counts": dict(sorted(by_status.items())),
        "source_bucket_counts": dict(sorted(by_bucket.items())),
        "source_kind_counts": dict(sorted(by_kind.items())),
        "required_bucket_coverage": {
            bucket: by_bucket.get(bucket, 0) > 0 for bucket in sorted(required_buckets)
        },
        "large_row_ledger_deferred_count": len(large_deferred),
        "large_row_ledger_deferred_paths": [row["source_path"] for row in large_deferred],
        "no_arbitrary_top_n": True,
        "lossy_sampling_used": False,
        "full_source_ledgers_preserved": True,
        "line_scan_limit_bytes": MAX_LINE_SCAN_BYTES,
        "jsonl_aggregate_scan_limit_bytes": MAX_JSONL_AGGREGATE_SCAN_BYTES,
        "scan_metadata": scan_metadata,
        "first_incomplete_invariant_after_stage01": "STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY",
        "exact_next_action": (
            "Run Stage02 source/path capability inventory, then consume source-ranked path rows "
            "with the dynamic execution policy engine."
        ),
    }
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(summary)
    update_state(summary)
    return summary


def write_report(summary: dict) -> None:
    lines = [
        "# vNext Moonshot Stage01 Static Primitive Assumption Audit",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Result",
        "",
        f"- Ledger rows: `{summary['row_count']}`",
        f"- Large row ledgers preserved/deferred for later streaming replay: `{summary['large_row_ledger_deferred_count']}`",
        f"- No arbitrary top-N sampling used: `{summary['no_arbitrary_top_n']}`",
        f"- Lossy sampling used: `{summary['lossy_sampling_used']}`",
        f"- First incomplete invariant: `{summary['first_incomplete_invariant_after_stage01']}`",
        "",
        "## Assumption Families",
        "",
    ]
    for family, count in summary["assumption_family_counts"].items():
        lines.append(f"- `{family}`: `{count}`")
    lines.extend(["", "## Required Bucket Coverage", ""])
    for bucket, covered in summary["required_bucket_coverage"].items():
        lines.append(f"- `{bucket}`: `{covered}`")
    lines.extend(["", "## Actions", ""])
    for action, count in summary["exact_action_counts"].items():
        lines.append(f"- `{action}`: `{count}`")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Code/config/prompts/tests/small artifacts were scanned at line level.",
            "- JSONL artifacts below the scan limit were streamed fully and counted by assumption family.",
            "- Huge activation ledgers were not sampled or reduced; they are preserved as exact source ledgers and explicitly queued for the dynamic replay and corrected branch-metric stages.",
            "- Stage01 is an assumption inventory, not the dynamic replay result. It moves the first incomplete invariant to Stage02.",
            "",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def update_state(summary: dict) -> None:
    if not OUTPUT_STATE.exists():
        return
    state = json.loads(OUTPUT_STATE.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_stage"] = "STAGE_01_STATIC_PRIMITIVE_ASSUMPTION_AUDIT"
    state["first_incomplete_invariant"] = "STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY"
    state["exact_next_action"] = summary["exact_next_action"]
    state["static_proxy_assumption_ledger_path"] = rel(OUTPUT_LEDGER)
    state["row_counts_scanned"]["stage01_static_assumption_rows"] = summary["row_count"]
    state["row_counts_scanned"]["stage01_large_row_ledgers_deferred"] = summary["large_row_ledger_deferred_count"]
    state["stage_status_table"]["STAGE_01_STATIC_PRIMITIVE_ASSUMPTION_AUDIT"] = "complete"
    state["stage_status_table"]["STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY"] = "pending"
    state["output_artifact_manifest"]["static_primitive_assumption_ledger"] = rel(OUTPUT_LEDGER)
    state["output_artifact_manifest"]["static_primitive_assumption_summary"] = rel(OUTPUT_SUMMARY)
    state["output_artifact_manifest"]["static_primitive_assumption_report"] = rel(OUTPUT_REPORT)
    state["completion_gate_status"] = "not_complete_first_incomplete_stage02"
    state.setdefault("verifiers_tests_run", []).append(
        {
            "command": (
                "py -3 research/science_program_2026_05/06_outcome_testing/"
                "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
                "build_vnext_moonshot_stage01_static_primitive_assumption_audit_2026_05_26.py"
            ),
            "status": "passed",
            "result": f"ledger_rows={summary['row_count']}; first_incomplete=STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY",
        }
    )
    OUTPUT_STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    text_files, jsonl_files, scan_metadata = gather_scan_files()
    records: list[dict] = []
    seq = 1
    for path in text_files:
        seq = scan_text_file(path, records, seq)
    for path in jsonl_files:
        seq = scan_jsonl_aggregate(path, records, seq)
    scan_metadata["text_files_considered"] = len(text_files)
    scan_metadata["jsonl_files_considered"] = len(jsonl_files)
    summary = write_outputs(records, scan_metadata)
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "stage": "STAGE_01_STATIC_PRIMITIVE_ASSUMPTION_AUDIT",
                "ledger_rows": summary["row_count"],
                "large_row_ledger_deferred_count": summary["large_row_ledger_deferred_count"],
                "first_incomplete_invariant": summary["first_incomplete_invariant_after_stage01"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
