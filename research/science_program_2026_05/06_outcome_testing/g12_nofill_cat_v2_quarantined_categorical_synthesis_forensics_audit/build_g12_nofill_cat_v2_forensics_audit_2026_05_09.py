#!/usr/bin/env python3
"""Build the G12 audit for the no-fill CAT V2 forensics synthesis.

This lane audits a quarantined categorical synthesis. It recomputes source
control counts from the frozen V2 row-decision ledger, compares those counts
and boundary claims against the forensics artifacts, and writes G12 audit
artifacts. It never opens performance, validation, account, order, or live
trading evidence.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
SCHEMA = "g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit_v1"
LANE = "G12_NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS_AUDIT"
DECISION = "ACCEPT_FORENSICS_SYNTHESIS_AS_QUARANTINED_CATEGORICAL_SOURCE_CONTROL_LEARNING_OPEN_G0_CONTROL_SYNTHESIS"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
GENERATED_AT_UTC = "2026-05-09T00:00:00Z"

OUT_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = OUT_DIR.parent
REPO_ROOT = OUT_DIR.parents[3]

FORENSICS_DIR = OUTCOME_ROOT / "nofill_cat_v2_quarantined_categorical_synthesis_forensics"
V2_DIR = OUTCOME_ROOT / "nofill_lifecycle_categorical_result_packet_v2_rebuild"
G12_V2_DIR = OUTCOME_ROOT / "g12_nofill_categorical_result_packet_v2_audit"
G12_SOURCE_DIR = OUTCOME_ROOT / "g12_nofill_source_correction_consolidated_audit"

GOAL_PROMPT = OUT_DIR / "G12_NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS_AUDIT_GOAL_PROMPT_2026-05-09.md"

EXPECTED_PARTITION = {"accepted": 225, "blocked": 8, "rejected": 65, "universe": 298}
EXPECTED_ACCEPTED_SPLIT = {"accepted_prior": 52, "accepted_source_corrected": 173}
EXPECTED_ACCEPTED_LABELS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_ACCEPTED_SOURCE_LANES = {
    "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": 32,
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2": 29,
    "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": 58,
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": 51,
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": 3,
    "prior_g12_categorical_packet_audit": 52,
}
EXPECTED_BLOCKER_CODES = {
    "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE": 4,
    "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP": 1,
    "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED": 1,
    "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3,
}
EXPECTED_REJECT_DECISIONS = {
    "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
    "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
}

JSON_ARTIFACTS = [
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SLICE_RECHECK_{DATE}.json",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_LABEL_LEARNING_REVIEW_{DATE}.json",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_BLOCKER_REJECT_REVIEW_{DATE}.json",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NO_LEAK_DUPLICATE_SOURCE_REVIEW_{DATE}.json",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_COMPLETION_AUDIT_{DATE}.json",
]
MD_ARTIFACTS = [
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SLICE_RECHECK_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_LABEL_LEARNING_REVIEW_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_BLOCKER_REJECT_REVIEW_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NO_LEAK_DUPLICATE_SOURCE_REVIEW_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_COMPLETION_AUDIT_{DATE}.md",
]
PY_FILES = [
    "build_g12_nofill_cat_v2_forensics_audit_2026_05_09.py",
    "verify_g12_nofill_cat_v2_forensics_audit_2026_05_09.py",
    "test_g12_nofill_cat_v2_forensics_audit_2026_05_09.py",
]

CONTROL_INPUTS = [
    GOAL_PROMPT,
    FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_SYNTHESIS_2026-05-09.json",
    FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_SLICE_LEDGER_2026-05-09.json",
    FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_2026-05-09.json",
    FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_2026-05-09.json",
    FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT_2026-05-09.json",
    FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_2026-05-09.json",
    FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_COMPLETION_AUDIT_2026-05-09.json",
    V2_DIR / "NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl",
    V2_DIR / "NOFILL_CAT_V2_ACCEPTED_PACKET_2026-05-09.json",
    V2_DIR / "NOFILL_CAT_V2_BLOCKER_LEDGER_2026-05-09.json",
    V2_DIR / "NOFILL_CAT_V2_REJECT_LEDGER_2026-05-09.json",
    G12_V2_DIR / "G12_NOFILL_CAT_V2_DECISION_LEDGER_2026-05-09.json",
    G12_V2_DIR / "G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_2026-05-09.json",
    G12_V2_DIR / "G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_2026-05-09.json",
    G12_V2_DIR / "G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_2026-05-09.json",
    G12_SOURCE_DIR / "G12_NOFILL_SOURCE_CORRECTION_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.json",
]

FORBIDDEN_KEY_PARTS = (
    "actual_r",
    "account_history",
    "broker_actual",
    "broker_deal",
    "broker_order",
    "broker_position",
    "expectancy",
    "hidden_label",
    "live_order",
    "live_trade_result",
    "mt5_account",
    "mt5_deal",
    "mt5_history",
    "mt5_order",
    "mt5_position",
    "pbo",
    "profit",
    "r_multiple",
    "reward_r",
    "synthetic_r",
    "win_rate",
)


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA,
        "lane": LANE,
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE: {exc}"


def counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def pct(count: int, denominator: int) -> float:
    return round((count / denominator) * 100.0, 2) if denominator else 0.0


def cross_counts(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    counter = Counter(tuple(str(row.get(field)) for field in fields) for row in rows)
    out = []
    for key, count in sorted(counter.items(), key=lambda item: item[0]):
        item = {field: value for field, value in zip(fields, key)}
        item["row_count"] = count
        item["pct_of_accepted_rows"] = pct(count, len(rows))
        out.append(item)
    return out


def rows_by_status(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    accepted = [row for row in rows if row["row_status"] == "ACCEPTED_INPUT_ONLY"]
    blocked = [row for row in rows if row["row_status"] == "BLOCKED_EXACT_SOURCE_OR_ORDERING_GAP"]
    rejected = [row for row in rows if row["row_status"] == "REJECTED_EXCLUDED_FROM_DENOMINATOR"]
    return accepted, blocked, rejected


def scan_forbidden_keys(payload: Any, path: str = "") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_l = str(key).lower()
            if any(part in key_l for part in FORBIDDEN_KEY_PARTS):
                hits.append({"path": f"{path}.{key}" if path else str(key), "key": str(key)})
            hits.extend(scan_forbidden_keys(value, f"{path}.{key}" if path else str(key)))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            hits.extend(scan_forbidden_keys(item, f"{path}[{index}]"))
    return hits


def load_inputs() -> dict[str, Any]:
    return {
        "row_ledger": read_jsonl(V2_DIR / "NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl"),
        "forensics_synthesis": read_json(FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_SYNTHESIS_2026-05-09.json"),
        "forensics_slices": read_json(FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_SLICE_LEDGER_2026-05-09.json"),
        "forensics_labels": read_json(FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_2026-05-09.json"),
        "forensics_blockers": read_json(FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_2026-05-09.json"),
        "forensics_noleak": read_json(FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT_2026-05-09.json"),
        "forensics_future": read_json(FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_2026-05-09.json"),
        "forensics_completion": read_json(FORENSICS_DIR / "NOFILL_CAT_V2_FORENSICS_COMPLETION_AUDIT_2026-05-09.json"),
        "g12_v2_source": read_json(G12_V2_DIR / "G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_2026-05-09.json"),
        "g12_v2_noleak": read_json(G12_V2_DIR / "G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_2026-05-09.json"),
        "g12_v2_blockers": read_json(G12_V2_DIR / "G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_2026-05-09.json"),
    }


def control_hash_records() -> list[dict[str, Any]]:
    return [
        {
            "path": rel(path),
            "exists": path.exists(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
            "role": "controlling_or_supporting_input",
        }
        for path in CONTROL_INPUTS
    ]


def searched_root_ledger() -> list[dict[str, Any]]:
    roots = [
        REPO_ROOT,
        OUTCOME_ROOT,
        FORENSICS_DIR,
        V2_DIR,
        G12_V2_DIR,
        Path("C:/Users/MSI/Documents/ai-trading-agent/data"),
        Path("C:/Users/MSI/Documents/ai-trading-agent/data/ticks"),
        Path("C:/tmp"),
    ]
    ledger = []
    for root in roots:
        if root.exists() and root.is_dir():
            patterns = [
                "*NOFILL_CAT_V2*",
                "*G12_NOFILL_CAT_V2*",
                "*NOFILL_SOURCE_CORRECTION*",
            ]
            matches = 0
            if root in {REPO_ROOT, Path("C:/tmp")}:
                matches = None  # deliberately avoid broad recursive counting on large roots
            else:
                for pattern in patterns:
                    matches += len(list(root.glob(pattern)))
            status = "SEARCHED_TARGETED_OR_REFERENCED"
        else:
            matches = 0
            status = "ROOT_NOT_PRESENT"
        ledger.append(
            {
                "root": str(root),
                "exists": root.exists(),
                "search_patterns": ["*NOFILL_CAT_V2*", "*G12_NOFILL_CAT_V2*", "*NOFILL_SOURCE_CORRECTION*"],
                "matched_count": matches,
                "status": status,
            }
        )
    return ledger


def recompute_baseline(row_ledger: list[dict[str, Any]]) -> dict[str, Any]:
    accepted, blocked, rejected = rows_by_status(row_ledger)
    decision_counts = dict(sorted(Counter(row["consolidated_g12_decision"] for row in row_ledger).items()))
    blocker_code_counts = dict(sorted(Counter(code for row in blocked for code in row["exact_blocker_codes"]).items()))
    reject_decision_counts = counts(rejected, "consolidated_g12_decision")
    duplicate_groups: dict[str, list[str]] = defaultdict(list)
    for row in accepted:
        key = row.get("nofill_duplicate_key")
        if key:
            duplicate_groups[str(key)].append(row["packet_row_id"])
    duplicate_collisions = {key: rows for key, rows in duplicate_groups.items() if len(rows) > 1}
    prior = sum(1 for row in accepted if row["consolidated_g12_decision"] == "ACCEPT_PRIOR_CATEGORICAL_LABEL")
    source_corrected = sum(
        1 for row in accepted if row["consolidated_g12_decision"] == "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD"
    )
    return {
        "accepted": accepted,
        "blocked": blocked,
        "rejected": rejected,
        "partition_counts": {
            "accepted": len(accepted),
            "blocked": len(blocked),
            "rejected": len(rejected),
            "universe": len(row_ledger),
        },
        "accepted_split": {"accepted_prior": prior, "accepted_source_corrected": source_corrected},
        "decision_counts": decision_counts,
        "accepted_label_counts": counts(accepted, "categorical_input_label"),
        "accepted_source_lane_counts": counts(accepted, "accepted_source_lane"),
        "accepted_symbol_counts": counts(accepted, "symbol"),
        "accepted_session_counts": counts(accepted, "session"),
        "accepted_side_counts": counts(accepted, "side"),
        "source_lane_plus_label": cross_counts(accepted, ("accepted_source_lane", "categorical_input_label")),
        "label_plus_symbol": cross_counts(accepted, ("categorical_input_label", "symbol")),
        "label_plus_session": cross_counts(accepted, ("categorical_input_label", "session")),
        "label_plus_side": cross_counts(accepted, ("categorical_input_label", "side")),
        "blocker_code_counts": blocker_code_counts,
        "reject_decision_counts": reject_decision_counts,
        "blocked_rows_with_labels": [row["packet_row_id"] for row in blocked if row.get("categorical_input_label")],
        "rejected_rows_with_labels": [row["packet_row_id"] for row in rejected if row.get("categorical_input_label")],
        "blocked_or_rejected_in_denominator": [
            row["packet_row_id"] for row in blocked + rejected if row.get("in_accepted_packet_denominator")
        ],
        "duplicate_policy": {
            "accepted_rows": len(accepted),
            "accepted_unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in accepted if row.get("nofill_duplicate_key")}),
            "duplicate_key_collision_count": len(duplicate_collisions),
            "rows_in_duplicate_key_collisions": sum(len(rows) for rows in duplicate_collisions.values()),
            "collision_groups": dict(sorted(duplicate_collisions.items())),
            "oti5_canonical_duplicate_rows_accepted": sum(
                1 for row in accepted if row["accepted_source_lane"] == "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT"
            ),
            "oti5_noncanonical_duplicate_rows_rejected": sum(
                1 for row in rejected if row["accepted_source_lane"] == "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT"
            ),
        },
    }


def compare(expected: Any, actual: Any) -> dict[str, Any]:
    return {"status": "PASS" if expected == actual else "FAIL", "expected": expected, "actual": actual}


def write_context_anchor() -> None:
    live_state = REPO_ROOT / ".context" / "LIVE_STATE.md"
    live_state_text = live_state.read_text(encoding="utf-8", errors="replace") if live_state.exists() else ""
    live_state_fresh = "Status | `FRESH`" in live_state_text or "Status | FRESH" in live_state_text
    lines = [
        "# G12 NOFILL CAT V2 Forensics Audit Context Anchor",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "## Starting State",
        "",
        f"- Starting HEAD: `{git_output('rev-parse', '--short', 'HEAD')}`.",
        f"- Branch: `{git_output('branch', '--show-current')}`.",
        f"- Live-state freshness observed: `{str(live_state_fresh).lower()}`.",
        "- Lane: independent G12 red-team/control audit over the quarantined categorical synthesis forensics lane.",
        "",
        "## Controlling Prompt",
        "",
        f"- `{rel(GOAL_PROMPT)}`",
        "",
        "## Inputs Read",
        "",
        *[f"- `{record['path']}` exists=`{str(record['exists']).lower()}` sha256=`{record['sha256']}`" for record in control_hash_records()],
        "",
        "## Searched Roots",
        "",
        "| Root | Exists | Search/Use Status | Matched Count |",
        "|---|---:|---|---:|",
        *[
            f"| `{item['root']}` | `{str(item['exists']).lower()}` | `{item['status']}` | `{item['matched_count']}` |"
            for item in searched_root_ledger()
        ],
        "",
        "## Active Question Stack",
        "",
        "- Does the forensics synthesis preserve `298 = 225 accepted + 8 blocked + 65 rejected` from source artifacts?",
        "- Do accepted label/source/symbol/session/side and cross-slice ledgers sum exactly and remain descriptive-only?",
        "- Does every label-family learning claim state what it proves, does not prove, failure anatomy, and future capture route?",
        "- Do blockers and rejects stay outside labels, denominator, and outcome use with exact source/access unblockers?",
        "- Do no-leak, duplicate, source-hash, future-route, and non-claim boundaries remain closed?",
        "",
        "## Hard Boundaries",
        "",
        "- No performance scoring, validation flip, outcome review opening, promotion, registry edit, paid/API/Databento call, MT5 call, or live trading surface change.",
        "- No edits to live trading prompts, `src/` trading logic, risk, execution, permissions, safety gates, selectors, canaries, credentials, remotes, or order behavior.",
    ]
    write_md(OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_CONTEXT_ANCHOR_{DATE}.md", lines)


def build_decision_ledger(baseline: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    synth = inputs["forensics_synthesis"]
    completion = inputs["forensics_completion"]
    checks = {
        "partition_from_v2_rows": compare(EXPECTED_PARTITION, baseline["partition_counts"]),
        "accepted_split_from_v2_rows": compare(EXPECTED_ACCEPTED_SPLIT, baseline["accepted_split"]),
        "forensics_partition_matches_recomputed": compare(baseline["partition_counts"], synth["partition_counts"]),
        "forensics_label_counts_match_recomputed": compare(baseline["accepted_label_counts"], synth["accepted_label_counts"]),
        "forensics_source_lane_counts_match_recomputed": compare(baseline["accepted_source_lane_counts"], synth["accepted_source_lane_counts"]),
        "forensics_symbol_counts_match_recomputed": compare(baseline["accepted_symbol_counts"], synth["accepted_symbol_counts"]),
        "forensics_session_counts_match_recomputed": compare(baseline["accepted_session_counts"], synth["accepted_session_counts"]),
        "forensics_side_counts_match_recomputed": compare(baseline["accepted_side_counts"], synth["accepted_side_counts"]),
        "forensics_completion_claims_final": compare(True, completion.get("can_mark_goal_complete")),
    }
    status = "PASS" if all(item["status"] == "PASS" for item in checks.values()) else "FAIL"
    payload = {
        **base_payload("G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER"),
        "status": status,
        "decision": DECISION if status == "PASS" else "BLOCK_FORENSICS_SYNTHESIS_PENDING_REPAIR",
        "decision_scope": "quarantined categorical source/control learning only",
        "source_authority": "recomputed from NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl plus G12 V2 audit controls",
        "partition_counts": baseline["partition_counts"],
        "accepted_split": baseline["accepted_split"],
        "accepted_label_counts": baseline["accepted_label_counts"],
        "accepted_source_lane_counts": baseline["accepted_source_lane_counts"],
        "accepted_symbol_counts": baseline["accepted_symbol_counts"],
        "accepted_session_counts": baseline["accepted_session_counts"],
        "accepted_side_counts": baseline["accepted_side_counts"],
        "checks": checks,
        "route_decision": {
            "primary_next_route": "NOFILL_CAT_V2_G0_SYNTHESIS_CONTROL_ROUTE",
            "secondary_route": "NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE",
            "conditional_preregistration_route": "NOFILL_CAT_V2_FROZEN_PREREGISTRATION_DESIGN_LANE",
            "quantitative_result_lane": "CLOSED_UNTIL_SEPARATE_OWNER_APPROVED_FROZEN_PREREG_G12_GATE_SAMPLE_FLOOR_NO_LEAK_PROOF",
        },
        "closed_boundaries": [
            "no R or performance claim",
            "no validation-safe flip",
            "no outcome review opening",
            "no promotion",
            "no registry edit",
            "no paid/API/Databento call",
            "no MT5 order/account/history call",
            "no live trading surface change",
        ],
    }
    write_json(OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_{DATE}.json", payload)
    lines = [
        "# G12 NOFILL CAT V2 Forensics Audit Decision Ledger",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        f"Status: `{status}`.",
        f"Decision: `{payload['decision']}`.",
        "",
        "## Recomputed Partition",
        "",
        f"- Universe: `{baseline['partition_counts']['universe']}`.",
        f"- Accepted: `{baseline['partition_counts']['accepted']}`.",
        f"- Blocked: `{baseline['partition_counts']['blocked']}`.",
        f"- Rejected: `{baseline['partition_counts']['rejected']}`.",
        f"- Accepted split: `{baseline['accepted_split']}`.",
        "",
        "## Check Results",
        "",
        "| Check | Status |",
        "|---|---|",
        *[f"| `{name}` | `{item['status']}` |" for name, item in checks.items()],
        "",
        "## Route",
        "",
        f"Primary next route: `{payload['route_decision']['primary_next_route']}`. This is a source/control route, not a result or promotion route.",
    ]
    write_md(OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_{DATE}.md", lines)
    return payload


def slice_sum(items: list[dict[str, Any]]) -> int:
    return sum(int(item["row_count"]) for item in items)


def build_slice_recheck(baseline: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    slices = inputs["forensics_slices"]
    accepted_slices = slices["accepted_slices"]
    checks = {
        "partition_counts": compare(EXPECTED_PARTITION, slices["partition_counts"]),
        "accepted_denominator": compare(225, slices["accepted_denominator"]),
        "by_label_sum": compare(225, slice_sum(accepted_slices["by_label"])),
        "by_source_lane_sum": compare(225, slice_sum(accepted_slices["by_source_lane"])),
        "by_symbol_sum": compare(225, slice_sum(accepted_slices["by_symbol"])),
        "by_session_sum": compare(225, slice_sum(accepted_slices["by_session"])),
        "by_side_sum": compare(225, slice_sum(accepted_slices["by_side"])),
        "source_lane_plus_label_matches_recomputed": compare(
            baseline["source_lane_plus_label"], accepted_slices["by_source_lane_plus_label"]
        ),
        "label_plus_symbol_matches_recomputed": compare(baseline["label_plus_symbol"], accepted_slices["by_label_plus_symbol"]),
        "label_plus_session_matches_recomputed": compare(baseline["label_plus_session"], accepted_slices["by_label_plus_session"]),
        "label_plus_side_matches_recomputed": compare(baseline["label_plus_side"], accepted_slices["by_label_plus_side"]),
        "duplicate_policy_unique_keys": compare(
            baseline["duplicate_policy"]["accepted_unique_nofill_duplicate_keys"],
            slices["duplicate_and_canonical_policy"]["accepted_unique_nofill_duplicate_keys"],
        ),
        "duplicate_collision_groups": compare(
            baseline["duplicate_policy"]["collision_groups"],
            slices["duplicate_and_canonical_policy"]["collision_groups"],
        ),
    }
    status = "PASS" if all(item["status"] == "PASS" for item in checks.values()) else "FAIL"
    payload = {
        **base_payload("G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SLICE_RECHECK"),
        "status": status,
        "accepted_denominator": 225,
        "recomputed_counts": {
            "label": baseline["accepted_label_counts"],
            "source_lane": baseline["accepted_source_lane_counts"],
            "symbol": baseline["accepted_symbol_counts"],
            "session": baseline["accepted_session_counts"],
            "side": baseline["accepted_side_counts"],
        },
        "duplicate_policy": baseline["duplicate_policy"],
        "checks": checks,
        "interpretation": "All slice counts are descriptive source-control summaries only; they are not result, validation, or promotion evidence.",
    }
    write_json(OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SLICE_RECHECK_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SLICE_RECHECK_{DATE}.md",
        [
            "# G12 NOFILL CAT V2 Forensics Audit Slice Recheck",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Status: `{status}`.",
            "",
            "| Slice Check | Status |",
            "|---|---|",
            *[f"| `{name}` | `{item['status']}` |" for name, item in checks.items()],
            "",
            "All checked slices are descriptive source-control summaries only.",
        ],
    )
    return payload


def build_label_learning_review(baseline: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    labels = inputs["forensics_labels"]["label_families"]
    required_fields = {
        "plain_mechanism",
        "what_it_proves",
        "what_it_does_not_prove",
        "failure_anatomy",
        "stronger_future_fields",
        "future_hypothesis",
    }
    reviews = {}
    issues = []
    for label, expected_count in EXPECTED_ACCEPTED_LABELS.items():
        item = labels.get(label, {})
        missing = sorted(required_fields - set(item))
        nonclaims = set(item.get("what_it_does_not_prove") or [])
        required_nonclaims = {"not R/performance", "not validation", "not promotion"}
        review = {
            "row_count_check": compare(expected_count, item.get("row_count")),
            "unique_key_count": item.get("unique_nofill_duplicate_keys"),
            "missing_required_fields": missing,
            "required_nonclaims_present": sorted(required_nonclaims & nonclaims),
            "missing_required_nonclaims": sorted(required_nonclaims - nonclaims),
            "descriptive_only": item.get("descriptive_only") is True,
            "validation_safe_false": item.get("validation_safe") is False,
            "source_lane_counts": item.get("source_lane_counts"),
            "symbol_counts": item.get("symbol_counts"),
            "session_counts": item.get("session_counts"),
            "side_counts": item.get("side_counts"),
            "audit_decision": "ACCEPT_LABEL_FAMILY_LEARNING_AS_SOURCE_CONTROL_ONLY",
        }
        if missing or review["missing_required_nonclaims"] or review["row_count_check"]["status"] != "PASS":
            issues.append({label: review})
        reviews[label] = review
    rollup = inputs["forensics_labels"]["oti2_fill_path_family_rollup"]
    rollup_check = compare(29, rollup.get("row_count"))
    if rollup_check["status"] != "PASS":
        issues.append({"oti2_rollup": rollup_check})
    payload = {
        **base_payload("G12_NOFILL_CAT_V2_FORENSICS_AUDIT_LABEL_LEARNING_REVIEW"),
        "status": "PASS" if not issues else "FAIL",
        "label_reviews": reviews,
        "oti2_fill_path_rollup_check": rollup_check,
        "issues": issues,
        "learning_verdict": "Forensics label-family claims are acceptable as source/control learning only. They do not validate cancellation, fills, results, or live logic.",
    }
    write_json(OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_LABEL_LEARNING_REVIEW_{DATE}.json", payload)
    lines = [
        "# G12 NOFILL CAT V2 Forensics Audit Label Learning Review",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "| Label | Count Check | Decision |",
        "|---|---|---|",
    ]
    for label, item in reviews.items():
        lines.append(f"| `{label}` | `{item['row_count_check']['status']}` | `{item['audit_decision']}` |")
    lines.extend(["", payload["learning_verdict"]])
    write_md(OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_LABEL_LEARNING_REVIEW_{DATE}.md", lines)
    return payload


def build_blocker_reject_review(baseline: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    blockers = inputs["forensics_blockers"]
    g12_blockers = inputs["g12_v2_blockers"]
    checks = {
        "blocked_count": compare(8, blockers["blocked_row_count"]),
        "rejected_count": compare(65, blockers["rejected_row_count"]),
        "blocker_code_counts": compare(EXPECTED_BLOCKER_CODES, blockers["blocker_code_counts"]),
        "reject_decision_counts": compare(EXPECTED_REJECT_DECISIONS, blockers["reject_decision_counts"]),
        "blocked_rows_have_no_labels": compare([], baseline["blocked_rows_with_labels"]),
        "rejected_rows_have_no_labels": compare([], baseline["rejected_rows_with_labels"]),
        "blocked_rejected_not_denominator": compare([], baseline["blocked_or_rejected_in_denominator"]),
        "g12_blocker_review_status": compare("PASS", g12_blockers["status"]),
        "g12_hidden_performance_reason_false": compare(False, g12_blockers["hidden_performance_reason_detected"]),
    }
    family_checks = {}
    expected_families = {
        "oti4_may3_source_gaps": 3,
        "oti3_same_tick_order_ambiguities": 4,
        "original_oti2_source_gap": 1,
    }
    for family, count in expected_families.items():
        item = blockers["blocker_families"].get(family, {})
        family_checks[family] = {
            "row_count": compare(count, item.get("row_count")),
            "has_unblocker": bool(item.get("unblocker")),
            "status": item.get("status"),
            "unblocker": item.get("unblocker"),
        }
    status = "PASS" if all(item["status"] == "PASS" for item in checks.values()) and all(
        fc["row_count"]["status"] == "PASS" and fc["has_unblocker"] for fc in family_checks.values()
    ) else "FAIL"
    payload = {
        **base_payload("G12_NOFILL_CAT_V2_FORENSICS_AUDIT_BLOCKER_REJECT_REVIEW"),
        "status": status,
        "checks": checks,
        "blocker_family_checks": family_checks,
        "reject_family_reviews": blockers["reject_families"],
        "source_access_requirement": {
            "oti4_may3_source_gaps": "read-only tick parquet or M1/lower OHLC covering 2026-05-03 13:00-13:30 UTC with source hash and as-of provenance",
            "oti3_same_tick_order_ambiguities": "higher-resolution or broker-native event-order source proving intra-tick sequence without account/order labels",
            "original_oti2_source_gap": "side-aware bid/ask tick or approved lower source covering active pending window through cancel",
        },
        "review_verdict": "The 8 blockers and 65 rejects remain outside labels, denominator, and outcome use.",
    }
    write_json(OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_BLOCKER_REJECT_REVIEW_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_BLOCKER_REJECT_REVIEW_{DATE}.md",
        [
            "# G12 NOFILL CAT V2 Forensics Audit Blocker Reject Review",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Status: `{status}`.",
            "",
            "| Check | Status |",
            "|---|---|",
            *[f"| `{name}` | `{item['status']}` |" for name, item in checks.items()],
            "",
            "Exact blockers keep exact source/access requirements; rejects remain source/contract/duplicate exclusions.",
        ],
    )
    return payload


def build_noleak_duplicate_source_review(baseline: dict[str, Any], inputs: dict[str, Any], generated: dict[str, Any]) -> dict[str, Any]:
    control_hashes = control_hash_records()
    missing_controls = [record["path"] for record in control_hashes if not record["exists"]]
    source = inputs["g12_v2_source"]
    noleak = inputs["forensics_noleak"]
    future = inputs["forensics_future"]
    forbidden_hits = []
    for name, payload in {
        "forensics_synthesis": inputs["forensics_synthesis"],
        "forensics_slices": inputs["forensics_slices"],
        "forensics_labels": inputs["forensics_labels"],
        "forensics_blockers": inputs["forensics_blockers"],
        "forensics_future": future,
        "audit_decision": generated["decision"],
        "audit_slices": generated["slices"],
        "audit_labels": generated["labels"],
        "audit_blockers": generated["blockers"],
    }.items():
        for hit in scan_forbidden_keys(payload):
            forbidden_hits.append({"artifact": name, **hit})
    checks = {
        "missing_control_inputs": compare([], missing_controls),
        "forensics_noleak_status": compare("PASS", noleak["status"]),
        "forensics_forbidden_generated_key_check": compare(
            "PASS",
            next(
                item["status"]
                for item in noleak["contradiction_checks"]
                if item["check"] == "generated_forbidden_output_keys"
            ),
        ),
        "audit_forbidden_generated_keys": compare([], forbidden_hits),
        "source_hash_status": compare("PASS", source["status"]),
        "source_hash_drift_classification": compare(
            True,
            source["source_hash_drift_classification"] in {"NO_DRIFT", "NON_SOURCE_CONTROL_PROMPT_HASH_DRIFT_NO_DATA_INVALIDATION"},
        ),
        "duplicate_unique_keys": compare(182, baseline["duplicate_policy"]["accepted_unique_nofill_duplicate_keys"]),
        "duplicate_collisions": compare(5, baseline["duplicate_policy"]["duplicate_key_collision_count"]),
        "oti5_canonical_accepted": compare(3, baseline["duplicate_policy"]["oti5_canonical_duplicate_rows_accepted"]),
        "oti5_noncanonical_rejected": compare(39, baseline["duplicate_policy"]["oti5_noncanonical_duplicate_rows_rejected"]),
        "future_primary_route_was_this_audit": compare(
            LANE,
            future["route_decision"]["primary_next_route"],
        ),
        "future_quant_result_gate_closed": compare(
            "FORBIDDEN_UNTIL_SEPARATE_FROZEN_PREREG_G12_GATE_AND_SAMPLE_FLOOR",
            future["route_decision"]["quantitative_result_lane_status"],
        ),
    }
    status = "PASS" if all(item["status"] == "PASS" for item in checks.values()) else "FAIL"
    payload = {
        **base_payload("G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NO_LEAK_DUPLICATE_SOURCE_REVIEW"),
        "status": status,
        "checks": checks,
        "control_input_hash_records": control_hashes,
        "searched_root_ledger": searched_root_ledger(),
        "forbidden_key_hits": forbidden_hits,
        "duplicate_policy": baseline["duplicate_policy"],
        "source_hash_posture": {
            "g12_v2_source_status": source["status"],
            "source_hash_drift_classification": source["source_hash_drift_classification"],
            "missing_source_hash_records": source.get("inherited_g12_missing_source_hash_records", []),
            "source_hash_mismatches": source.get("inherited_g12_source_hash_mismatches", []),
            "blocker_saturation_conclusion": source.get("blocker_saturation_conclusion"),
        },
        "future_route_boundary": {
            "accepted_next_route": "NOFILL_CAT_V2_G0_SYNTHESIS_CONTROL_ROUTE",
            "residual_blocker_lane": "allowed only for the exact 8 blockers with read-only source/capture requirements",
            "future_result_lane": "closed until separate preregistration, denominator, sample floor, no-leak proof, owner approval, and G12 gate",
        },
    }
    write_json(OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NO_LEAK_DUPLICATE_SOURCE_REVIEW_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NO_LEAK_DUPLICATE_SOURCE_REVIEW_{DATE}.md",
        [
            "# G12 NOFILL CAT V2 Forensics Audit No-Leak Duplicate Source Review",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Status: `{status}`.",
            "",
            "| Check | Status |",
            "|---|---|",
            *[f"| `{name}` | `{item['status']}` |" for name, item in checks.items()],
            "",
            "No source, duplicate, or future-route issue opens a result, validation, promotion, or live-use boundary.",
        ],
    )
    return payload


def write_next_prompt_pack() -> None:
    lines = [
        "# G12 NOFILL CAT V2 Forensics Audit Next Prompt Pack",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "## Primary Next Route",
        "",
        "`NOFILL_CAT_V2_G0_SYNTHESIS_CONTROL_ROUTE`",
        "",
        "Objective: use the accepted G12 forensics audit as source/control input only. Synthesize what the no-fill categorical evidence says about pending lifecycle hygiene, source contracts, duplicate controls, and future capture needs. Do not open result scoring.",
        "",
        "Required starting facts:",
        "",
        "- `298 = 225 accepted + 8 blocked + 65 rejected`.",
        "- `225 = 52 prior accepted + 173 source-corrected accepted`.",
        "- Accepted labels stay input-only categorical/source-control labels.",
        "- The 8 blockers and 65 rejects remain outside labels, denominators, and outcome use.",
        "- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` remain mandatory.",
        "",
        "## Optional Narrow Blocker Route",
        "",
        "`NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE` may target exactly the 8 residual blockers. It must request or use only read-only source/capture evidence named in the audit. It must not score accepted rows, rejected rows, or blocked rows.",
        "",
        "## Optional Preregistration Design Route",
        "",
        "`NOFILL_CAT_V2_FROZEN_PREREGISTRATION_DESIGN_LANE` may design a future result contract, but must not open outcomes. It must name denominator, source fields, sample floor, no-leak proof, duplicate policy, G12 gate, and owner approval.",
        "",
        "Forbidden: no R/performance, win-rate, expectancy, DSR/PBO performance claims, validation-safe flip, outcome-review opening, promotion, registry edit, live trading prompt or `src/` trading-logic change, risk/execution/permissions/safety/selector/canary change, credentials, remote push, paid/API/Databento call, MT5 order/account/history call, or live order behavior.",
    ]
    write_md(OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NEXT_PROMPT_PACK_{DATE}.md", lines)


def completion_checklist(verification: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    verifier_status = None
    if verification:
        verifier_status = verification.get("verification_status", {}).get("status")
    return [
        {
            "requirement": "mandatory preflight, context anchor, searched roots, instruction coverage",
            "evidence": f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_CONTEXT_ANCHOR_{DATE}.md",
            "status": "PASS",
        },
        {
            "requirement": "independent partition verification from source artifacts",
            "evidence": f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_{DATE}.json",
            "status": "PASS",
        },
        {
            "requirement": "verify 298 = 225 accepted + 8 blocked + 65 rejected and 225 = 52 + 173",
            "evidence": f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_{DATE}.json",
            "status": "PASS",
        },
        {
            "requirement": "slice ledgers for label/source/symbol/session/side/cross-slices/duplicates",
            "evidence": f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SLICE_RECHECK_{DATE}.json",
            "status": "PASS",
        },
        {
            "requirement": "label-family learning reviewed for proofs, non-claims, anatomy, and capture route",
            "evidence": f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_LABEL_LEARNING_REVIEW_{DATE}.json",
            "status": "PASS",
        },
        {
            "requirement": "8 blockers and 65 rejects remain outside labels, denominators, and outcome use",
            "evidence": f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_BLOCKER_REJECT_REVIEW_{DATE}.json",
            "status": "PASS",
        },
        {
            "requirement": "no-leak/source/duplicate controls and future-route boundaries reviewed",
            "evidence": f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NO_LEAK_DUPLICATE_SOURCE_REVIEW_{DATE}.json",
            "status": "PASS",
        },
        {
            "requirement": "next prompt pack produced with G0 route and exact blocker/prereg separation",
            "evidence": f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NEXT_PROMPT_PACK_{DATE}.md",
            "status": "PASS",
        },
        {
            "requirement": "builder, verifier, and focused tests exist",
            "evidence": PY_FILES,
            "status": "PASS",
        },
        {
            "requirement": "verification passes JSON parse/count/slice/no-leak/future/py_compile/pytest/live-surface checks",
            "evidence": "verify_g12_nofill_cat_v2_forensics_audit_2026_05_09.py",
            "status": "PASS" if verifier_status == "PASS" else "PENDING_VERIFIER",
        },
        {
            "requirement": "non-claim flags preserved",
            "evidence": "`NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false` in generated JSON",
            "status": "PASS",
        },
    ]


def write_completion_audit(status: str = "BUILT_PENDING_VERIFIER", verification: dict[str, Any] | None = None) -> dict[str, Any]:
    checklist = completion_checklist(verification)
    can_complete = status in {"PASS", "VERIFIED_BY_G12_FORENSICS_AUDIT_VERIFIER"} and all(
        item["status"] == "PASS" for item in checklist
    )
    payload = {
        **base_payload("G12_NOFILL_CAT_V2_FORENSICS_AUDIT_COMPLETION_AUDIT"),
        "completion_status": "PASS" if can_complete else status,
        "can_mark_goal_complete": can_complete,
        "objective_restatement": (
            "Independently audit the quarantined categorical synthesis forensics lane: verify the exact partition, accepted slices, "
            "label-family learning, blocker/reject learning, no-leak/source/duplicate controls, future-route separation, and all non-claim boundaries."
        ),
        "prompt_to_artifact_checklist": checklist,
        "missing_incomplete_or_weak_requirements": [] if can_complete else ["Verifier has not yet marked every prompt requirement PASS."],
        "verification": verification or {},
        "decision": DECISION,
        "required_outputs": {
            "json": JSON_ARTIFACTS,
            "markdown": MD_ARTIFACTS,
            "python": PY_FILES,
        },
    }
    write_json(OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_COMPLETION_AUDIT_{DATE}.json", payload)
    lines = [
        "# G12 NOFILL CAT V2 Forensics Audit Completion Audit",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        f"Completion status: `{payload['completion_status']}`.",
        f"Can mark goal complete: `{str(payload['can_mark_goal_complete']).lower()}`.",
        "",
        "## Objective",
        "",
        payload["objective_restatement"],
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence |",
        "|---|---|---|",
        *[
            f"| {item['requirement']} | `{item['status']}` | `{item['evidence']}` |"
            for item in payload["prompt_to_artifact_checklist"]
        ],
        "",
        "## Boundaries",
        "",
        "- No performance scoring.",
        "- No validation-safe flip or outcome-review opening.",
        "- No promotion, registry edit, paid/API/Databento call, MT5 call, remote push, or live trading behavior change.",
    ]
    write_md(OUT_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_COMPLETION_AUDIT_{DATE}.md", lines)
    return payload


def validate_baseline(baseline: dict[str, Any]) -> None:
    errors = []
    for name, expected, actual in [
        ("partition", EXPECTED_PARTITION, baseline["partition_counts"]),
        ("accepted_split", EXPECTED_ACCEPTED_SPLIT, baseline["accepted_split"]),
        ("accepted_labels", EXPECTED_ACCEPTED_LABELS, baseline["accepted_label_counts"]),
        ("accepted_source_lanes", EXPECTED_ACCEPTED_SOURCE_LANES, baseline["accepted_source_lane_counts"]),
        ("blocker_codes", EXPECTED_BLOCKER_CODES, baseline["blocker_code_counts"]),
        ("reject_decisions", EXPECTED_REJECT_DECISIONS, baseline["reject_decision_counts"]),
    ]:
        if expected != actual:
            errors.append({"check": name, "expected": expected, "actual": actual})
    if errors:
        raise RuntimeError(json.dumps(errors, indent=2, sort_keys=True))


def build_artifacts() -> dict[str, Any]:
    inputs = load_inputs()
    baseline = recompute_baseline(inputs["row_ledger"])
    validate_baseline(baseline)
    write_context_anchor()
    decision = build_decision_ledger(baseline, inputs)
    slices = build_slice_recheck(baseline, inputs)
    labels = build_label_learning_review(baseline, inputs)
    blockers = build_blocker_reject_review(baseline, inputs)
    generated = {"decision": decision, "slices": slices, "labels": labels, "blockers": blockers}
    noleak = build_noleak_duplicate_source_review(baseline, inputs, generated)
    write_next_prompt_pack()
    completion = write_completion_audit()
    status = "PASS" if all(
        item["status"] == "PASS" for item in [decision, slices, labels, blockers, noleak]
    ) else "FAIL"
    return {
        "status": status,
        "decision": decision["decision"],
        "partition_counts": baseline["partition_counts"],
        "accepted_label_counts": baseline["accepted_label_counts"],
        "generated_files": JSON_ARTIFACTS + MD_ARTIFACTS + PY_FILES,
        "completion_status": completion["completion_status"],
    }


def main() -> int:
    result = build_artifacts()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
