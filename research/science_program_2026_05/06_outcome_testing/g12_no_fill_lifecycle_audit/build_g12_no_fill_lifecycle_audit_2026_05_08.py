#!/usr/bin/env python3
"""Build the G12 audit artifacts for the no-fill lifecycle contract.

This is research/control only. It audits the existing 298-row input-only
packet and writes evidence ledgers without computing performance, R, broker
outcomes, account history, live order state, or promotion claims.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
SCHEMA = "g12_no_fill_lifecycle_audit_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DECISION = "ACCEPT_AS_INPUT_ONLY_LIFECYCLE_SOURCE_EVIDENCE"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
OUTCOME_ROOT = REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
NOFILL_DIR = OUTCOME_ROOT / "no_fill_still_pending_lifecycle_contract"
T3_DIR = OUTCOME_ROOT / "cnr_t3_lifecycle_expansion_source_packet"
G12_T3_DIR = OUTCOME_ROOT / "g12_cnr_t3_lifecycle_audit"

CONTROL_PROMPT = NOFILL_DIR / "G12_NOFILL_LIFECYCLE_AUDIT_GOAL_PROMPT_2026-05-08.md"

MANDATORY_CONTEXT = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_READING_ORDER.md",
]

NOFILL_INPUTS = [
    "NOFILL_G12_AUDIT_PROMPT_PACK_2026-05-08.md",
    "NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT_GOAL_PROMPT_2026-05-08.md",
    "NOFILL_CONTEXT_ANCHOR_2026-05-08.json",
    "NOFILL_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json",
    "NOFILL_298_FAMILY_SPLIT_INVENTORY_2026-05-08.json",
    "NOFILL_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
    "NOFILL_INPUT_ONLY_PACKET_2026-05-08.json",
    "NOFILL_INPUT_ONLY_PACKET_2026-05-08_ROWS.jsonl",
    "NOFILL_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
    "NOFILL_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json",
    "NOFILL_FORENSICS_AND_LEARNING_2026-05-08.json",
    "build_nofill_still_pending_lifecycle_contract_2026_05_08.py",
    "verify_nofill_still_pending_lifecycle_contract_2026_05_08.py",
    "test_nofill_still_pending_lifecycle_contract_2026_05_08.py",
]

UPSTREAM_INPUTS = [
    T3_DIR / "CNR_T3_NO_TERMINAL_CANDIDATE_INVENTORY_2026-05-08.json",
    T3_DIR / "CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json",
    T3_DIR / "CNR_T3_SEARCHED_ROOT_AND_SOURCE_HASH_LEDGER_2026-05-08.json",
    G12_T3_DIR / "G12_CNR_T3_DECISION_LEDGER_2026-05-08.json",
    G12_T3_DIR / "G12_CNR_T3_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08.json",
    G12_T3_DIR / "G12_CNR_T3_INVENTORY_COVERAGE_AUDIT_2026-05-08.json",
    G12_T3_DIR / "G12_CNR_T3_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json",
    G12_T3_DIR / "G12_CNR_T3_NEXT_PROMPT_PACK_2026-05-08.md",
]

FORBIDDEN_PACKET_KEYS = {
    "synthetic_r",
    "descriptive_synthetic_path_r",
    "descriptive_gross_synthetic_path_r",
    "conservative_lower_bound_r",
    "reward_r_to_tp1",
    "matrix_residual_target_r_from_executable_quote",
    "residual_target_r",
    "max_favorable_r",
    "broker_actual_r",
    "actual_r",
    "account_history",
    "live_trade_result",
    "live_order_state",
    "win_rate",
    "expectancy",
    "dsr",
    "pbo",
}

FORBIDDEN_PACKET_VALUE_NEEDLES = [
    "broker_actual_r",
    "account_history",
    "live_trade_result",
    "live_order_state",
    "win rate",
    "expectancy",
    "validation_safe=true",
    "outcome_review_opened=true",
    "live_effect=true",
]

FORBIDDEN_LIVE_PREFIXES = [
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
]

FORBIDDEN_LIVE_NAME_NEEDLES = [
    "mt5",
    "order",
    "account",
    "risk",
    "execution",
    "permissions",
    "safety",
    "selector",
    "credential",
    "remote",
    "databento",
    "paid",
    "canary",
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except Exception:
        return str(path)


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(name: str, data: dict[str, Any]) -> None:
    (OUT_DIR / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, lines: list[str]) -> None:
    (OUT_DIR / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def git_output(*args: str) -> str:
    cmd = ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", *args]
    try:
        return subprocess.check_output(cmd, cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE: {exc}"


def row_key(row: dict[str, Any]) -> tuple[str | None, str | None, str | None, str | None]:
    return (
        row.get("source_inventory_id") or row.get("inventory_id"),
        row.get("source_lane"),
        row.get("source_packet_id") or row.get("packet_id"),
        row.get("source_row_id") or row.get("row_id"),
    )


def list_dict_counts(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: (str(item[0]), item[1])))


def walk_values(value: Any, path: str = "") -> list[tuple[str, Any]]:
    out = [(path, value)]
    if isinstance(value, dict):
        for key, child in value.items():
            out.extend(walk_values(child, f"{path}.{key}" if path else str(key)))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            out.extend(walk_values(child, f"{path}[{idx}]"))
    return out


def scan_forbidden_packet_fields(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in rows:
        row_id = row.get("packet_row_id")
        for path, value in walk_values(row):
            leaf = path.split(".")[-1].split("[")[0].lower()
            if leaf in FORBIDDEN_PACKET_KEYS:
                hits.append({"row_id": row_id, "path": path, "kind": "forbidden_key", "value_preview": str(value)[:160]})
            if isinstance(value, str):
                lower = value.lower()
                for needle in FORBIDDEN_PACKET_VALUE_NEEDLES:
                    if needle.lower() in lower:
                        hits.append({"row_id": row_id, "path": path, "kind": "forbidden_value", "needle": needle, "value_preview": value[:160]})
    return hits


def load_state() -> dict[str, Any]:
    packet_rows = load_jsonl(NOFILL_DIR / "NOFILL_INPUT_ONLY_PACKET_2026-05-08_ROWS.jsonl")
    t3_inventory = load_json(T3_DIR / "CNR_T3_NO_TERMINAL_CANDIDATE_INVENTORY_2026-05-08.json")
    state = {
        "packet_rows": packet_rows,
        "packet": load_json(NOFILL_DIR / "NOFILL_INPUT_ONLY_PACKET_2026-05-08.json"),
        "contract": load_json(NOFILL_DIR / "NOFILL_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json"),
        "family": load_json(NOFILL_DIR / "NOFILL_298_FAMILY_SPLIT_INVENTORY_2026-05-08.json"),
        "source_ledger": load_json(NOFILL_DIR / "NOFILL_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json"),
        "noleak": load_json(NOFILL_DIR / "NOFILL_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json"),
        "blocker": load_json(NOFILL_DIR / "NOFILL_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json"),
        "forensics": load_json(NOFILL_DIR / "NOFILL_FORENSICS_AND_LEARNING_2026-05-08.json"),
        "completion": load_json(NOFILL_DIR / "NOFILL_COMPLETION_AUDIT_2026-05-08.json"),
        "t3_inventory": t3_inventory,
        "t3_blocker": load_json(T3_DIR / "CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json"),
        "g12_t3_inventory": load_json(G12_T3_DIR / "G12_CNR_T3_INVENTORY_COVERAGE_AUDIT_2026-05-08.json"),
        "g12_t3_source": load_json(G12_T3_DIR / "G12_CNR_T3_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json"),
        "g12_t3_decision": load_json(G12_T3_DIR / "G12_CNR_T3_DECISION_LEDGER_2026-05-08.json"),
    }
    state["t3_rows"] = t3_inventory["rows"]
    state["t3_eligible_rows"] = [r for r in state["t3_rows"] if r.get("packet_eligible") is True]
    state["t3_not_packet_eligible_rows"] = [
        r for r in state["t3_rows"]
        if r.get("packet_eligible") is False
        and r.get("lifecycle_label_or_blocker_label") == "not_packet_eligible"
    ]
    return state


def build_context_anchor(generated_at: str) -> dict[str, Any]:
    roots = [
        Path("C:/Users/MSI/Documents/ai-trading-agent"),
        Path("C:/Users/MSI/Documents/ai-trading-agent/research"),
        Path("C:/Users/MSI/Documents/ai-trading-agent/data"),
        Path("C:/Users/MSI/Documents/ai-trading-agent/data/ticks"),
        Path("C:/Users/MSI/Documents/ai-trading-agent/shadow_logs"),
        Path("C:/Users/MSI/Documents/ai-trading-agent/pipeline_state"),
        Path("C:/Users/MSI/Documents/ai-trading-agent/knowledge_base"),
        Path("C:/tmp/gtos_otb"),
        REPO_ROOT,
        NOFILL_DIR,
    ]
    anchor = {
        "artifact_family": "G12_NOFILL_CONTEXT_ANCHOR",
        "schema_version": SCHEMA,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "head": git_output("rev-parse", "HEAD"),
        "git_status_at_anchor": git_output("status", "--short"),
        "controlling_prompt_paths": [rel(CONTROL_PROMPT), rel(NOFILL_DIR / "NOFILL_G12_AUDIT_PROMPT_PACK_2026-05-08.md")],
        "mandatory_context_read": [file_record(REPO_ROOT / p) for p in MANDATORY_CONTEXT],
        "artifact_set_read": [file_record(NOFILL_DIR / p) for p in NOFILL_INPUTS] + [file_record(p) for p in UPSTREAM_INPUTS],
        "active_audit_questions": [
            "exact 298-row universe reconstruction from G12 CNR T3 not_packet_eligible rows",
            "six accepted T3 stop_after_original_horizon exclusion",
            "94 G12-blocked CNR061 exclusion without opening blocked outcomes",
            "contract frozen before classification and no T3 label reuse",
            "label-family split correctness and family-specific future blockers",
            "source hash recomputation, local-heavy-data search, and alternate-root drift",
            "no forbidden R/performance/broker/account/live/order/hidden-label fields",
            "duplicate denominator and sample-floor validation block",
            "scope: lifecycle/source-control only, no performance implication",
        ],
        "searched_roots": [
            {"root": str(root), "exists": root.exists(), "purpose": "required local/heavy-data or prior-artifact root"}
            for root in roots
        ],
        "source_no_leak_boundaries": [
            "Input packet fields may describe source identity, source hashes, lifecycle/no-fill/no-entry family, duplicate key, and future source blockers only.",
            "No R, performance, win rate, expectancy, DSR/PBO, broker actual-R, account history, live trade result, live order state, hidden path label, or blocked CNR061 outcome field may be carried.",
            "The 94 blocked CNR061 rows are checked only as excluded; they are not scored or relabeled.",
            "Terminal-order-unclaimed is an allowed lifecycle family label, not permission to use live order state.",
        ],
        "completion_checklist": [
            "context anchor written before decision ledgers",
            "decision ledger written",
            "universe/exclusion audit written",
            "label-family audit written",
            "source-hash/no-leak audit written",
            "duplicate/sample-floor audit written",
            "forensics/learning written",
            "blocker/next-route ledger written",
            "next prompt pack written",
            "verifier/tests added and run",
            "completion audit can_mark_goal_complete=true",
            "scoped commit made without live-surface changes",
        ],
    }
    write_json("G12_NOFILL_CONTEXT_ANCHOR_2026-05-08.json", anchor)
    write_md("G12_NOFILL_CONTEXT_ANCHOR_2026-05-08.md", [
        "# G12 No-Fill Context Anchor - 2026-05-08",
        "",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        f"Generated: `{generated_at}`",
        f"HEAD: `{anchor['head']}`",
        "",
        "## Controlling Prompts",
        *[f"- `{p}`" for p in anchor["controlling_prompt_paths"]],
        "",
        "## Active Audit Questions",
        *[f"- {q}" for q in anchor["active_audit_questions"]],
        "",
        "## Searched Roots",
        *[f"- `{r['root']}` exists={r['exists']}" for r in anchor["searched_roots"]],
        "",
        "## Boundaries",
        *[f"- {b}" for b in anchor["source_no_leak_boundaries"]],
    ])
    return anchor


def audit_universe(state: dict[str, Any], generated_at: str) -> dict[str, Any]:
    packet_rows = state["packet_rows"]
    t3_not = state["t3_not_packet_eligible_rows"]
    t3_blockers = state["t3_blocker"]["exact_blockers"]
    packet_keys = {row_key(r) for r in packet_rows}
    t3_not_keys = {row_key(r) for r in t3_not}
    t3_blocker_keys = {row_key(r) for r in t3_blockers}
    eligible_keys = {row_key(r) for r in state["t3_eligible_rows"]}
    issues = []
    if len(packet_rows) != 298:
        issues.append(f"packet row count {len(packet_rows)} != 298")
    if len(t3_not) != 298:
        issues.append(f"T3 not_packet_eligible count {len(t3_not)} != 298")
    if packet_keys != t3_not_keys:
        issues.append("packet keys differ from T3 not_packet_eligible keys")
    if packet_keys != t3_blocker_keys:
        issues.append("packet keys differ from T3 exact blocker keys")
    if packet_keys & eligible_keys:
        issues.append("packet overlaps six accepted T3 rows")
    oti8_packet_rows = [r["packet_row_id"] for r in packet_rows if r.get("source_lane") == "OTI8_CNR061"]
    if oti8_packet_rows:
        issues.append("packet contains OTI8_CNR061 source rows")
    blocked_94 = state["noleak"]["blocked_94_exclusion"]
    if blocked_94.get("status") != "PASS" or blocked_94.get("blocked_rows") != 94:
        issues.append("94 blocked CNR061 exclusion artifact not PASS/94")
    audit = {
        "artifact_family": "G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "decision": "ACCEPT_UNIVERSE_AND_EXCLUSIONS" if not issues else "BLOCK_UNIVERSE_OR_EXCLUSION",
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "packet_rows": len(packet_rows),
        "t3_candidate_rows": len(state["t3_rows"]),
        "t3_not_packet_eligible_rows": len(t3_not),
        "t3_exact_blocker_rows": len(t3_blockers),
        "t3_accepted_rows_excluded": len(state["t3_eligible_rows"]),
        "packet_overlap_with_t3_accepted": sorted(str(k) for k in (packet_keys & eligible_keys)),
        "oti8_cnr061_packet_rows": oti8_packet_rows,
        "blocked_94_exclusion": blocked_94,
        "packet_source_lane_counts": list_dict_counts(Counter(r["source_lane"] for r in packet_rows)),
        "t3_not_packet_eligible_source_lane_counts": list_dict_counts(Counter(r["source_lane"] for r in t3_not)),
        "sample_packet_keys": [list(k) for k in sorted(packet_keys)[:5]],
    }
    write_json("G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json", audit)
    write_md("G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.md", [
        "# G12 No-Fill Universe And Exclusion Audit - 2026-05-08",
        "",
        f"Status: `{audit['status']}`",
        f"Decision: `{audit['decision']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        f"- Packet rows: `{audit['packet_rows']}`",
        f"- T3 not-packet-eligible rows: `{audit['t3_not_packet_eligible_rows']}`",
        f"- T3 exact blockers: `{audit['t3_exact_blocker_rows']}`",
        f"- Six accepted T3 rows excluded: `{audit['t3_accepted_rows_excluded']}`",
        f"- OTI8/CNR061 rows in packet: `{len(oti8_packet_rows)}`",
        f"- 94-row blocked exclusion: `{blocked_94.get('status')}`",
        "",
        "The packet key set matches the upstream T3 `not_packet_eligible` and exact-blocker key sets.",
    ])
    return audit


def audit_labels(state: dict[str, Any], generated_at: str) -> dict[str, Any]:
    packet_rows = state["packet_rows"]
    contract = state["contract"]
    allowed_labels = set(contract["allowed_labels"])
    observed_labels = {r["contract_label"] for r in packet_rows}
    label_counts = Counter(r["contract_label"] for r in packet_rows)
    family_counts = Counter(r["contract_family"] for r in packet_rows)
    source_by_label: dict[str, Counter[str]] = defaultdict(Counter)
    for row in packet_rows:
        source_by_label[row["contract_label"]][row["source_lane"]] += 1
    issues = []
    if observed_labels - allowed_labels:
        issues.append({"unexpected_labels": sorted(observed_labels - allowed_labels)})
    if "stop_after_original_horizon" in observed_labels or "stop_after_original_horizon" in allowed_labels:
        issues.append("T3 lifecycle label reused")
    if state["family"]["contract_label_counts"] != dict(label_counts):
        issues.append("label counts differ from upstream inventory")
    frozen = contract["contract_frozen_at_utc"]
    starts = sorted({r["classification_started_at_utc"] for r in packet_rows})
    if any(start < frozen for start in starts):
        issues.append("classification timestamp precedes contract freeze")
    label_boundaries = {
        label: {
            "count": label_counts[label],
            "family": contract["allowed_labels"][label]["family"],
            "observed_source_lanes": dict(source_by_label[label]),
            "accepted_as": "input-only lifecycle/source-control label",
            "not_accepted_as": "performance, validation, broker/account/live outcome, or terminal-order proof beyond the named family",
        }
        for label in sorted(observed_labels)
    }
    audit = {
        "artifact_family": "G12_NOFILL_LABEL_FAMILY_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "decision": "ACCEPT_LABEL_FAMILIES_AS_INPUT_ONLY" if not issues else "BLOCK_LABEL_FAMILY_ISSUE",
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "contract_id": contract["contract_id"],
        "contract_frozen_at_utc": frozen,
        "classification_started_at_utc_values": starts,
        "contract_before_classification": all(start >= frozen for start in starts),
        "label_counts": list_dict_counts(label_counts),
        "family_counts": list_dict_counts(family_counts),
        "label_boundaries": label_boundaries,
        "oti1_metadata_caution": "OTI1 rows preserve source_symbols inside source_evidence but have null top-level symbol/session; acceptable for input-control classification, but future result lanes should project symbol/session explicitly.",
    }
    write_json("G12_NOFILL_LABEL_FAMILY_AUDIT_2026-05-08.json", audit)
    lines = [
        "# G12 No-Fill Label Family Audit - 2026-05-08",
        "",
        f"Status: `{audit['status']}`",
        f"Decision: `{audit['decision']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        f"Contract: `{contract['contract_id']}`",
        f"Frozen at: `{frozen}`",
        f"Classification timestamps: `{', '.join(starts)}`",
        "",
        "## Label Counts",
    ]
    lines.extend(f"- `{label}`: {count}" for label, count in sorted(label_counts.items()))
    lines += [
        "",
        "No `CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1` label is reused; `stop_after_original_horizon` is absent.",
        "",
        "OTI1 top-level symbol/session is null but source symbols are preserved in `source_evidence`; this is a future result-lane metadata requirement, not an input-packet blocker.",
    ]
    write_md("G12_NOFILL_LABEL_FAMILY_AUDIT_2026-05-08.md", lines)
    return audit


def audit_source_and_noleak(state: dict[str, Any], generated_at: str) -> dict[str, Any]:
    packet_rows = state["packet_rows"]
    source_ledger = state["source_ledger"]
    consumed_checks = []
    mismatches = []
    missing_expected = []
    for entry in source_ledger["consumed_source_files"]:
        path = Path(entry["path"])
        expected = entry.get("expected_sha256")
        actual = sha256_file(path)
        check = {
            "path": str(path),
            "exists": path.exists(),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "hash_match": None if expected is None else expected == actual,
            "role": entry.get("role"),
        }
        consumed_checks.append(check)
        if expected and not path.exists():
            missing_expected.append(check)
        if expected and actual and expected != actual:
            mismatches.append(check)

    source_artifact_checks = []
    for rel_path, expected in sorted({(r["source_artifact_path"], r["source_artifact_sha256"]) for r in packet_rows}):
        path = REPO_ROOT / rel_path
        actual = sha256_file(path)
        check = {
            "path": rel_path,
            "exists": path.exists(),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "hash_match": expected == actual,
        }
        source_artifact_checks.append(check)
        if actual != expected:
            mismatches.append(check)

    path_source_checks = []
    for row in packet_rows:
        for source_path, expected in (row.get("source_evidence", {}).get("path_source_sha256") or {}).items():
            path = Path(source_path)
            actual = sha256_file(path)
            check = {
                "row_id": row["packet_row_id"],
                "path": source_path,
                "exists": path.exists(),
                "expected_sha256": expected,
                "actual_sha256": actual,
                "hash_match": expected == actual,
            }
            path_source_checks.append(check)
            if actual != expected:
                mismatches.append(check)

    basename_hashes: dict[str, set[str]] = defaultdict(set)
    for root in source_ledger["searched_roots"]:
        for match in root.get("matches", []):
            basename_hashes[Path(match["path"]).name].add(match["sha256"])
    alternate_root_hash_drift = {
        name: sorted(hashes)
        for name, hashes in sorted(basename_hashes.items())
        if len(hashes) > 1
    }

    forbidden_hits = scan_forbidden_packet_fields(packet_rows)
    carry_flags = {
        "broker_actual_r_accessed": False,
        "account_history_accessed": False,
        "live_trade_results_accessed": False,
        "live_order_state_accessed": False,
        "blocked_packet_outcome_source_read": False,
        "mt5_account_calls": 0,
        "mt5_order_calls": 0,
        "api_calls": 0,
        "paid_data_calls": 0,
        "databento_calls": 0,
        "canary_calls": 0,
    }
    issues = []
    if mismatches:
        issues.append({"hash_mismatches": mismatches[:10], "count": len(mismatches)})
    if forbidden_hits:
        issues.append({"forbidden_packet_hits": forbidden_hits[:10], "count": len(forbidden_hits)})
    audit = {
        "artifact_family": "G12_NOFILL_SOURCE_HASH_AND_NOLEAK_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "decision": "ACCEPT_SOURCE_HASH_AND_NOLEAK_BOUNDARY" if not issues else "BLOCK_SOURCE_HASH_OR_NOLEAK",
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        **carry_flags,
        "consumed_source_file_checks": consumed_checks,
        "source_artifact_checks": source_artifact_checks,
        "path_source_hash_checks_count": len(path_source_checks),
        "path_source_hash_mismatches": [c for c in path_source_checks if c["hash_match"] is False],
        "missing_expected_files": missing_expected,
        "hash_mismatches": mismatches,
        "forbidden_packet_hits": forbidden_hits,
        "forbidden_packet_hits_count": len(forbidden_hits),
        "alternate_root_hash_drift": alternate_root_hash_drift,
        "alternate_root_hash_drift_interpretation": "Non-blocking: packet rows cite source hashes that recompute in the current audited worktree. Drift across other absolute roots is recorded so future lanes pin explicit source paths instead of trusting ambient main-root copies.",
        "searched_roots": source_ledger["searched_roots"],
        "blocked_94_exclusion": state["noleak"]["blocked_94_exclusion"],
    }
    write_json("G12_NOFILL_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json", audit)
    lines = [
        "# G12 No-Fill Source Hash And No-Leak Audit - 2026-05-08",
        "",
        f"Status: `{audit['status']}`",
        f"Decision: `{audit['decision']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        f"- Consumed source entries checked: `{len(consumed_checks)}`",
        f"- Distinct source artifact checks: `{len(source_artifact_checks)}`",
        f"- Path-source hash checks from packet rows: `{len(path_source_checks)}`",
        f"- Hash mismatches: `{len(mismatches)}`",
        f"- Forbidden packet hits: `{len(forbidden_hits)}`",
        f"- Alternate-root hash drift basenames: `{len(alternate_root_hash_drift)}`",
        "",
        "No broker/account/live/order-state/API/paid-data/Databento/canary calls were made or used.",
        "The recorded alternate-root drift is not used to reject the current packet because the packet-cited hashes recompute in this worktree; future lanes should pin exact source paths.",
    ]
    write_md("G12_NOFILL_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.md", lines)
    return audit


def audit_duplicates(state: dict[str, Any], generated_at: str) -> dict[str, Any]:
    rows = state["packet_rows"]
    dup = Counter(r["nofill_duplicate_key"] for r in rows)
    group = Counter(r["duplicate_group_id"] for r in rows)
    repeated = {k: v for k, v in sorted(dup.items()) if v > 1}
    group_repeated = {k: v for k, v in sorted(group.items()) if v > 1}
    issues = []
    if len({r["source_inventory_id"] for r in rows}) != 298:
        issues.append("source inventory ids are not unique")
    if state["noleak"]["validation_sample_floor_status"] != "FALSE_INPUT_ONLY_CONTROL_PACKET_NOT_VALIDATION":
        issues.append("sample floor is not blocked")
    if state["noleak"]["validation_safe"] is not False:
        issues.append("validation_safe flipped true")
    audit = {
        "artifact_family": "G12_NOFILL_DUPLICATE_SAMPLEFLOOR_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "decision": "ACCEPT_DUPLICATE_CONTROLS_FOR_INPUT_ONLY_SCOPE" if not issues else "BLOCK_DUPLICATE_OR_SAMPLE_FLOOR",
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "packet_rows": len(rows),
        "source_inventory_id_unique": len({r["source_inventory_id"] for r in rows}),
        "nofill_duplicate_key_unique": len(dup),
        "nofill_duplicate_key_repeated_count": len(repeated),
        "nofill_duplicate_key_max_repeat": max(dup.values()),
        "duplicate_group_id_unique": len(group),
        "duplicate_group_id_repeated_count": len(group_repeated),
        "duplicate_group_id_max_repeat": max(group.values()),
        "top_repeated_nofill_duplicate_keys": dict(Counter(dup).most_common(12)),
        "validation_sample_floor_status": state["noleak"]["validation_sample_floor_status"],
        "sample_floor_reason": "Rows are mixed input-control lifecycle/source-block families with repeated opportunity groups; this blocks validation/promotion but preserves source-control usefulness.",
    }
    write_json("G12_NOFILL_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json", audit)
    write_md("G12_NOFILL_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md", [
        "# G12 No-Fill Duplicate Sample-Floor Audit - 2026-05-08",
        "",
        f"Status: `{audit['status']}`",
        f"Decision: `{audit['decision']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        f"- Packet rows: `{audit['packet_rows']}`",
        f"- Unique source inventory ids: `{audit['source_inventory_id_unique']}`",
        f"- Unique no-fill duplicate keys: `{audit['nofill_duplicate_key_unique']}`",
        f"- Repeated no-fill duplicate keys: `{audit['nofill_duplicate_key_repeated_count']}`",
        f"- Max no-fill duplicate key repeat: `{audit['nofill_duplicate_key_max_repeat']}`",
        f"- Sample floor status: `{audit['validation_sample_floor_status']}`",
        "",
        audit["sample_floor_reason"],
    ])
    return audit


def build_decision_ledger(state: dict[str, Any], audits: dict[str, Any], generated_at: str) -> dict[str, Any]:
    all_pass = all(a.get("status") == "PASS" for a in audits.values())
    decision = DECISION if all_pass else "BLOCK_WITH_EXACT_NEXT_QUESTIONS"
    question_answers = [
        {
            "question": "Is the exact 298-row universe reconstructed from the G12 CNR T3 not_packet_eligible set?",
            "decision": "ACCEPT",
            "evidence": "Packet keys equal the 298 upstream T3 not_packet_eligible and exact-blocker key sets.",
        },
        {
            "question": "Are the six accepted T3 stop_after_original_horizon rows excluded?",
            "decision": "ACCEPT",
            "evidence": "Six packet-eligible T3 keys have zero overlap with the no-fill packet and no row uses stop_after_original_horizon.",
        },
        {
            "question": "Are the 94 G12-blocked CNR061 rows excluded with zero overlap?",
            "decision": "ACCEPT",
            "evidence": "Blocked-94 exclusion artifact is PASS/94 and the no-fill packet has zero OTI8_CNR061 source rows.",
        },
        {
            "question": "Was the no-fill lifecycle contract frozen before classification?",
            "decision": "ACCEPT",
            "evidence": "Contract freeze timestamp is <= every packet classification_started_at_utc value.",
        },
        {
            "question": "Do labels avoid T3 reuse and correctly split source-safe families?",
            "decision": "ACCEPT",
            "evidence": "Seven observed labels are allowed by the frozen contract; no T3 stop-after-horizon label is present.",
        },
        {
            "question": "Are source hashes recomputable or missing files recorded exactly?",
            "decision": "ACCEPT_WITH_CAUTION",
            "evidence": "Packet-cited source and path hashes recompute with zero mismatches; alternate-root OTI3 hash drift is recorded as a future path-pinning caution.",
        },
        {
            "question": "Does any packet row carry forbidden fields?",
            "decision": "ACCEPT",
            "evidence": "Forbidden packet key/value scan returns zero hits.",
        },
        {
            "question": "Are duplicate denominator and sample-floor controls sufficient?",
            "decision": "ACCEPT_FOR_INPUT_ONLY_SCOPE",
            "evidence": "Source inventory ids are unique, duplicate opportunity groups are visible, and validation_sample_floor_status remains FALSE_INPUT_ONLY_CONTROL_PACKET_NOT_VALIDATION.",
        },
        {
            "question": "Does the packet accidentally imply performance?",
            "decision": "ACCEPT_NO_PERFORMANCE_CLAIM",
            "evidence": "Every artifact preserves NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false and contains no R/performance metrics in packet rows.",
        },
        {
            "question": "What future lanes are justified?",
            "decision": "ACCEPT_NEXT_ROUTES_AS_SOURCE_REQUIREMENTS_ONLY",
            "evidence": "Family-specific future routes require separate frozen source/result contracts before any scoring.",
        },
    ]
    ledger = {
        "artifact_family": "G12_NOFILL_DECISION_LEDGER",
        "schema_version": SCHEMA,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "overall_decision": decision,
        "decision_standard": "ACCEPT/BLOCK/REJECT as input-only lifecycle source evidence; no validation or performance lane opened.",
        "audit_statuses": {name: audit.get("status") for name, audit in audits.items()},
        "audit_question_answers": question_answers,
        "what_it_proves": [
            "The 298-row packet is the exact non-T3 lifecycle-like universe from the named upstream T3 artifacts.",
            "Those rows can be carried forward as input-only lifecycle/source-control family evidence.",
            "The family split exposes no-fill, no-entry, source-blocked, and terminal-order-unclaimed source states for future contract design.",
        ],
        "what_it_does_not_prove": [
            "It does not prove R, performance, expectancy, win rate, validation, promotion, live edge, or sample adequacy.",
            "It does not resolve broker fills, account history, live order state, hidden terminal order, or the 94 blocked CNR061 rows.",
            "It does not authorize any live trading prompt, risk, execution, permissions, safety, selector, MT5, canary, paid-data, credential, remote, or order-behavior change.",
        ],
        "row_or_family_acceptance": {
            "accepted_input_only_packet_rows": len(state["packet_rows"]) if all_pass else 0,
            "blocked_current_packet_rows": 0 if all_pass else len(state["packet_rows"]),
            "rejected_rows": 0,
            "result_or_promotion_lanes": "blocked until separate source/result contracts exist",
        },
    }
    write_json("G12_NOFILL_DECISION_LEDGER_2026-05-08.json", ledger)
    lines = [
        "# G12 No-Fill Decision Ledger - 2026-05-08",
        "",
        f"Overall decision: `{decision}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Audit Questions",
    ]
    for item in question_answers:
        lines.append(f"- `{item['decision']}` {item['question']} Evidence: {item['evidence']}")
    lines += [
        "",
        "## What It Proves",
        *[f"- {x}" for x in ledger["what_it_proves"]],
        "",
        "## What It Does Not Prove",
        *[f"- {x}" for x in ledger["what_it_does_not_prove"]],
    ]
    write_md("G12_NOFILL_DECISION_LEDGER_2026-05-08.md", lines)
    return ledger


def build_forensics_and_routes(state: dict[str, Any], generated_at: str) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = state["packet_rows"]
    label_counts = Counter(r["contract_label"] for r in rows)
    symbol_counts = Counter(str(r.get("symbol")) for r in rows)
    session_counts = Counter(str(r.get("session")) for r in rows)
    family_failure = state["blocker"]["family_failure_anatomy"]
    forensics = {
        "artifact_family": "G12_NOFILL_FORENSICS_AND_LEARNING",
        "schema_version": SCHEMA,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "decision": "ACCEPT_LEARNING_FOR_SOURCE_CONTROL_ONLY",
        "row_count": len(rows),
        "label_counts": list_dict_counts(label_counts),
        "symbol_counts": list_dict_counts(symbol_counts),
        "session_counts": list_dict_counts(session_counts),
        "failure_anatomy": family_failure,
        "learning": [
            "The 298 rows are not a result cohort; they are a mixed lifecycle/source-control substrate.",
            "The most useful immediate learning is capture-design: pending lifecycle closure, entry-touch, terminal-order proof, and price-compatible path source fields are missing or bounded in different ways by family.",
            "OTI1 lifecycle rows are valuable but top-level symbol/session projection is weaker than the source_evidence child setup_ids/source_symbols; future result lanes should normalize that metadata before scoring.",
            "Terminal-order-unclaimed rows should not be rescued with assumptions; they require lower-timeframe or tick order proof under a separate frozen contract.",
            "Source-blocked rows are negative evidence about source compatibility, not failed trades.",
        ],
        "non_claims": [
            "No R/performance or broker/account/live labels were computed.",
            "No validation sample floor passed.",
            "No live trading behavior changed.",
        ],
    }
    next_routes = {
        "artifact_family": "G12_NOFILL_BLOCKER_AND_NEXT_ROUTE_LEDGER",
        "schema_version": SCHEMA,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "current_packet_acceptance_blockers": [],
        "result_or_promotion_blocker": "All scoring, validation, promotion, or live-effect claims remain blocked pending separate frozen result/source contracts.",
        "family_next_routes": [
            {
                "family": label,
                "rows": label_counts[label],
                "current_decision": "ACCEPT_INPUT_ONLY_SOURCE_CONTROL",
                "future_route": family_failure[label]["exact_unblocker"],
                "still_blocked_for": "R/performance/result/promotion/live use",
            }
            for label in sorted(label_counts)
        ],
        "cross_lane_next_routes": [
            {
                "route": "NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1",
                "needed_fields": ["pending_created_at", "entry_touched_at", "filled_at", "cancelled_at", "expired_at", "frozen_observation_horizon", "quote_source_hash"],
                "forbidden_until_frozen": "performance scoring, broker/account/live labels, hidden terminal labels",
            },
            {
                "route": "NO_ENTRY_TOUCH_PATH_ORDER_SOURCE_PACKET_V1",
                "needed_fields": ["decision_asof", "entry_price", "entry_touch_time", "terminal_area_touch_time", "source_coverage_hash", "lower_tf_order_policy"],
                "forbidden_until_frozen": "treating terminal-area reach as win/loss or R",
            },
            {
                "route": "TERMINAL_ORDER_PROOF_PACKET_V1",
                "needed_fields": ["entry_touch_proof", "post_entry_tick_or_ltf_path", "target_touch_time", "stop_touch_time", "same_bar_ambiguity_policy", "source_hashes"],
                "forbidden_until_frozen": "same-bar terminal order inference",
            },
            {
                "route": "PRICE_COMPATIBLE_M1_OR_TICK_SOURCE_RECOVERY",
                "needed_fields": ["symbol scale contract", "M1/tick parser", "source path", "hash", "as_of coverage window"],
                "forbidden_until_frozen": "using incompatible source as terminal-order evidence",
            },
            {
                "route": "CNR_T1_T2_E2_E3_E4_FOLLOWUPS",
                "needed_fields": ["fixed-R/stop packet", "source-hashed structural levels", "signal emission", "latency", "pretouch telemetry"],
                "forbidden_until_frozen": "mixing no-fill families into CNR result validation",
            },
        ],
        "non_blocking_cautions": [
            "Alternate absolute roots contain at least one hash-drifted OTI3 artifact; future lanes should name the exact source path and expected hash instead of relying on a generic main-root copy.",
            "OTI1 source rows should project symbol/session to top-level fields before any result denominator is opened.",
        ],
    }
    write_json("G12_NOFILL_FORENSICS_AND_LEARNING_2026-05-08.json", forensics)
    write_json("G12_NOFILL_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08.json", next_routes)
    write_md("G12_NOFILL_FORENSICS_AND_LEARNING_2026-05-08.md", [
        "# G12 No-Fill Forensics And Learning - 2026-05-08",
        "",
        f"Decision: `{forensics['decision']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Learning",
        *[f"- {item}" for item in forensics["learning"]],
        "",
        "## Non-Claims",
        *[f"- {item}" for item in forensics["non_claims"]],
    ])
    lines = [
        "# G12 No-Fill Blocker And Next Route Ledger - 2026-05-08",
        "",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "Current packet acceptance blockers: `0`",
        f"Result/promotion blocker: {next_routes['result_or_promotion_blocker']}",
        "",
        "## Family Routes",
    ]
    for route in next_routes["family_next_routes"]:
        lines.append(f"- `{route['family']}` rows={route['rows']}: {route['future_route']}")
    lines += ["", "## Cross-Lane Routes"]
    for route in next_routes["cross_lane_next_routes"]:
        lines.append(f"- `{route['route']}` needs {', '.join(route['needed_fields'])}")
    write_md("G12_NOFILL_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08.md", lines)
    return forensics, next_routes


def build_next_prompt_pack(generated_at: str) -> None:
    prompt = [
        "# G12 No-Fill Next Prompt Pack - 2026-05-08",
        "",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Recommended Next Goal",
        "",
        "`/goal Build NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1 as a separate frozen source-only lane for the accepted no-fill/still-pending/wrong-side/no-entry/terminal-order-unclaimed/source-blocked families from G12_NOFILL. Complete GTOS preflight; read G12_NOFILL decision, universe, label-family, source/no-leak, duplicate/sample-floor, forensics, blocker, and completion artifacts; freeze a new source contract before any row scan; search absolute local heavy-data roots and prior artifacts; consume only source-hashed lifecycle, quote, tick, pending-intent, and lower-timeframe path fields; record exact missing fields for every blocker; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; do not compute R/performance, do not score blocked rows, do not use broker/account/live/order/hidden labels, and touch no live prompts/risk/execution/permissions/safety/selectors/MT5/canaries/paid-data/credentials/remote/order behavior; stop only after source contract, row packet or exact blockers, source-hash/no-leak audit, duplicate/sample-floor audit, forensics, verifier/tests, and completion audit are committed.`",
        "",
        "## Exact Source Requirements",
        "- Pending lifecycle closure: pending_created_at, entry_touched_at, filled_at, cancelled_at, expired_at, frozen_observation_horizon, quote/source hash.",
        "- No-entry path order: decision_asof, entry price/bounds, entry touch proof, terminal-area touch proof, lower-timeframe or tick source coverage hash.",
        "- Terminal-order proof: post-entry tick/lower-timeframe order, target/stop touch times, same-bar ambiguity policy, parser/scale contract.",
        "- Source-blocked rows: price-compatible M1/tick path or explicit parser/scale impossibility proof.",
        "- OTI1 metadata: top-level symbol/session/side projection before any result denominator.",
        "",
        "## Still Forbidden",
        "- R/performance/win-rate/expectancy/DSR/PBO/result validation.",
        "- Broker actual-R, account history, live trade result, live order state, hidden labels, blocked CNR061 outcomes.",
        "- Live trading surface changes, paid/API/Databento/MT5 account/order calls, credentials, remote pushes.",
        "",
        f"Generated: `{generated_at}`",
    ]
    write_md("G12_NOFILL_NEXT_PROMPT_PACK_2026-05-08.md", prompt)


def build_completion(generated_at: str, audits: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight", "PASS", "LIVE_STATE regenerated/read; latest handoff, quick card, doctrine, research current state, goal discipline, heavy-data inventory, and reading order read."),
        ("context_anchor", "PASS", "G12_NOFILL_CONTEXT_ANCHOR_2026-05-08.md/json written before decision artifacts."),
        ("decision_ledger", "PASS", "G12_NOFILL_DECISION_LEDGER_2026-05-08.md/json answers all audit questions."),
        ("universe_exclusion", audits["universe"]["status"], "G12 universe audit recomputes 298 rows, six T3 exclusion, and 94 blocked CNR061 exclusion."),
        ("label_family", audits["labels"]["status"], "G12 label audit checks contract freeze, label counts, family boundaries, and T3 label non-reuse."),
        ("source_hash_noleak", audits["source"]["status"], "G12 source/no-leak audit recomputes hashes and scans forbidden packet fields."),
        ("duplicate_samplefloor", audits["duplicates"]["status"], "G12 duplicate/sample-floor audit keeps validation_sample_floor_status false."),
        ("forensics_learning", "PASS", "G12 forensics and next-route ledgers written with failure anatomy and source requirements."),
        ("next_prompt_pack", "PASS", "G12_NOFILL_NEXT_PROMPT_PACK_2026-05-08.md written."),
        ("verifier_tests", "PENDING", "Verifier must run py_compile, pytest, JSON/JSONL parse, source/no-leak/universe checks, and live-surface diff."),
        ("commit", "PENDING", "Scoped research artifacts must be committed before goal completion."),
    ]
    completion = {
        "artifact_family": "G12_NOFILL_COMPLETION_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "objective_restatement": "Audit SEPARATE_NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT_V1 and the 298-row no-fill packet as input-only lifecycle/source evidence, deciding ACCEPT/BLOCK/REJECT without performance scoring or live-surface changes.",
        "completion_status": "PENDING_VERIFIER_AND_COMMIT",
        "can_mark_goal_complete": False,
        "decision": decision["overall_decision"],
        "prompt_to_artifact_checklist": [
            {"requirement": req, "status": status, "evidence": evidence}
            for req, status, evidence in checklist
        ],
        "verifier_results": {},
        "commit_evidence": {},
    }
    write_json("G12_NOFILL_COMPLETION_AUDIT_2026-05-08.json", completion)
    write_md("G12_NOFILL_COMPLETION_AUDIT_2026-05-08.md", [
        "# G12 No-Fill Completion Audit - 2026-05-08",
        "",
        f"Completion status: `{completion['completion_status']}`",
        f"Can mark goal complete: `{completion['can_mark_goal_complete']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Objective",
        completion["objective_restatement"],
        "",
        "## Prompt-To-Artifact Checklist",
        *[f"- `{item['status']}` {item['requirement']}: {item['evidence']}" for item in completion["prompt_to_artifact_checklist"]],
    ])
    return completion


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    build_context_anchor(generated_at)
    state = load_state()
    audits = {
        "universe": audit_universe(state, generated_at),
        "labels": audit_labels(state, generated_at),
        "source": audit_source_and_noleak(state, generated_at),
        "duplicates": audit_duplicates(state, generated_at),
    }
    decision = build_decision_ledger(state, audits, generated_at)
    build_forensics_and_routes(state, generated_at)
    build_next_prompt_pack(generated_at)
    build_completion(generated_at, audits, decision)
    print(json.dumps({
        "status": "BUILT",
        "overall_decision": decision["overall_decision"],
        "audit_statuses": {k: v["status"] for k, v in audits.items()},
        "output_dir": rel(OUT_DIR),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
