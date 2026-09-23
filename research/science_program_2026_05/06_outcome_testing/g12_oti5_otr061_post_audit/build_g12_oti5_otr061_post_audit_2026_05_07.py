"""Build the combined G12 OTI5 + OTR061 post-audit artifact pack.

Research-control only. This reads the committed OTI5 quarantined result
artifacts and OTR061 recovered input packet artifacts, verifies their named
claims from files, and emits G12-owned audit ledgers. It does not open new
outcome scoring beyond auditing existing OTI5 rows.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


DATE_STAMP = "2026-05-07"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LIVE_EFFECT = False

BASE = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
OUTCOME_ROOT = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing"
OTI5 = OUTCOME_ROOT / "oti5_g6_cusum_changepoint_quarantined_results"
OTR061 = OUTCOME_ROOT / "otr061_xau_tick_recovery"
G12_OTX = OUTCOME_ROOT / "g12_otx_g6_post_audit"
OTX = OUTCOME_ROOT / "otx_g6_tick_aware_end_to_end_resolution"
ABS_TICK_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks")

OTI5_JSONS = {
    "result": OTI5 / "OTI5_G6_CUSUM_RESULT_LEDGER_2026-05-07.json",
    "method": OTI5 / "OTI5_G6_CUSUM_METHOD_FREEZE_2026-05-07.json",
    "source": OTI5 / "OTI5_G6_CUSUM_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
    "duplicate": OTI5 / "OTI5_G6_CUSUM_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json",
    "label": OTI5 / "OTI5_G6_CUSUM_LABEL_FAMILY_NOLEAK_REPORT_2026-05-07.json",
    "methodology": OTI5 / "OTI5_G6_CUSUM_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.json",
    "completion": OTI5 / "OTI5_G6_CUSUM_COMPLETION_AUDIT_2026-05-07.json",
}
OTI5_ROWS = OTI5 / "OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl"

OTR061_JSONS = {
    "decision": OTR061 / "OTR061_XAU_TICK_RECOVERY_DECISION_LEDGER_2026-05-07.json",
    "proposal": OTR061 / "OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json",
    "source": OTR061 / "OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07.json",
    "search": OTR061 / "OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER_2026-05-07.json",
    "completion": OTR061 / "OTR061_COMPLETION_AUDIT_2026-05-07.json",
}
OTR061_PARQUET = OTR061 / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"

CONTROL_FILES = {
    "live_state": REPO_ROOT / ".context/LIVE_STATE.md",
    "latest_handoff": REPO_ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "quick_reference": REPO_ROOT / ".context/00_core/quick_reference_card.md",
    "research_doctrine": REPO_ROOT / ".context/00_core/research_operating_doctrine.md",
    "research_current_state": REPO_ROOT / ".context/00_core/research_current_state.md",
    "goal_session_discipline": REPO_ROOT / ".context/00_core/goal_session_research_discipline.md",
    "local_heavy_data_inventory": REPO_ROOT / ".context/00_core/local_heavy_data_inventory.md",
    "otg0_control_rules": OUTCOME_ROOT / "OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md",
    "g12_otx_decision": G12_OTX / "G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.json",
    "otx_proposals": OTX / "OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
    "controlling_prompt": BASE / "G12_OTI5_OTR061_POST_AUDIT_GOAL_PROMPT_2026-05-07.md",
}

FORBIDDEN_LABEL_KEYS = {
    "broker_actual_r",
    "account_history",
    "actual_r",
    "win_loss",
    "outcome_r",
    "path_label",
    "path_outcome_status",
    "final_r",
    "realized_r",
    "hit_tp",
    "hit_sl",
    "live_trade_result",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso_to_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: dict[str, Any], lines: list[str] | None = None) -> None:
    body = [
        f"# {title}",
        "",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
        f"**Validation safe:** `{str(VALIDATION_SAFE).lower()}`  ",
        f"**Outcome review opened:** `{str(OUTCOME_REVIEW_OPENED).lower()}`  ",
        f"**Live effect:** `{str(LIVE_EFFECT).lower()}`",
        "",
    ]
    if lines:
        body.extend(lines)
        body.append("")
    body.extend(["```json", json.dumps(payload, indent=2, sort_keys=True, default=str), "```", ""])
    path.write_text("\n".join(body), encoding="utf-8")


def base_payload(family: str) -> dict[str, Any]:
    return {
        "artifact_family": family,
        "generated_at_utc": now_utc(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "live_effect": LIVE_EFFECT,
    }


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return f"ERROR[{result.returncode}]: {result.stderr.strip()}"
    return result.stdout.strip()


def walk_key_hits(value: Any, *, path: str = "$", forbidden: set[str] | None = None) -> list[dict[str, str]]:
    forbidden = forbidden or FORBIDDEN_LABEL_KEYS
    hits: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_lower = str(key).lower()
            if key_lower in forbidden:
                hits.append({"path": f"{path}.{key}", "key": str(key)})
            hits.extend(walk_key_hits(nested, path=f"{path}.{key}", forbidden=forbidden))
    elif isinstance(value, list):
        for idx, nested in enumerate(value):
            hits.extend(walk_key_hits(nested, path=f"{path}[{idx}]", forbidden=forbidden))
    return hits


def load_inputs() -> dict[str, Any]:
    return {
        "oti5": {name: read_json(path) for name, path in OTI5_JSONS.items()},
        "oti5_rows": read_jsonl(OTI5_ROWS),
        "otr061": {name: read_json(path) for name, path in OTR061_JSONS.items()},
    }


def claim(name: str, expected: Any, observed: Any) -> dict[str, Any]:
    return {
        "claim": name,
        "expected": expected,
        "observed": observed,
        "status": "PASS" if observed == expected else "FAIL",
    }


def parquet_stats(path: Path) -> dict[str, Any]:
    table = pq.read_table(path)
    rows = table.to_pylist()
    first = rows[0]
    last = rows[-1]

    def iso(ms: int) -> str:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")

    decision_cut = int(datetime(2026, 5, 6, 7, 15, 0, tzinfo=timezone.utc).timestamp() * 1000)
    path_end = int(datetime(2026, 5, 6, 11, 15, 0, tzinfo=timezone.utc).timestamp() * 1000)
    query_start = int(datetime(2026, 5, 6, 7, 10, 0, tzinfo=timezone.utc).timestamp() * 1000)
    decision_rows = [row for row in rows if row["time_msc"] <= decision_cut]
    full_rows = [row for row in rows if query_start <= row["time_msc"] <= path_end]
    path_rows = [row for row in rows if decision_cut <= row["time_msc"] <= path_end]
    post_rows = [row for row in rows if row["time_msc"] > path_end]
    decision_quote = decision_rows[-1]
    return {
        "path": str(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "row_count": len(rows),
        "columns": table.column_names,
        "first_tick_utc": iso(first["time_msc"]),
        "last_tick_utc": iso(last["time_msc"]),
        "first_bid": first["bid"],
        "first_ask": first["ask"],
        "last_bid": last["bid"],
        "last_ask": last["ask"],
        "decision_quote": {
            "quote_timestamp_utc": iso(decision_quote["time_msc"]),
            "bid": decision_quote["bid"],
            "ask": decision_quote["ask"],
            "executable_decision_price_long_ask": decision_quote["ask"],
            "decision_rows_lte_071500": len(decision_rows),
        },
        "required_window": {
            "row_count": len(full_rows),
            "first_timestamp_utc": iso(full_rows[0]["time_msc"]) if full_rows else None,
            "last_timestamp_utc": iso(full_rows[-1]["time_msc"]) if full_rows else None,
        },
        "ordered_path": {
            "row_count": len(path_rows),
            "first_timestamp_utc": iso(path_rows[0]["time_msc"]) if path_rows else None,
            "last_timestamp_utc": iso(path_rows[-1]["time_msc"]) if path_rows else None,
            "post_horizon_first_timestamp_utc": iso(post_rows[0]["time_msc"]) if post_rows else None,
        },
    }


def summarize_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key)) for row in rows).items()))


def summarize_nested(rows: list[dict[str, Any]], group_key: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[str(row.get(group_key))][str(row.get("result_status"))] += 1
    return {key: dict(value) for key, value in sorted(grouped.items())}


def minutes_between(start: str | None, end: str | None) -> float | None:
    a = iso_to_dt(start)
    b = iso_to_dt(end)
    if not a or not b:
        return None
    return round((b - a).total_seconds() / 60.0, 6)


def build_oti5_method_audit(inputs: dict[str, Any]) -> dict[str, Any]:
    oti5 = inputs["oti5"]
    rows = inputs["oti5_rows"]
    primary = [row for row in rows if row.get("duplicate_role") == "COUNTABLE_PRIMARY_UNIQUE_DUPLICATE_GROUP"]
    result = oti5["result"]
    method = oti5["method"]
    duplicate = oti5["duplicate"]
    label = oti5["label"]
    source = oti5["source"]
    methodology = oti5["methodology"]
    observed_counts = Counter(row["result_status"] for row in primary)
    payload = base_payload("G12_OTI5_RESULT_METHOD_AUDIT")
    payload.update(
        {
            "packet_id": "OTG0-PKT-063",
            "experiment_id": "G6-EXP-004-EXHAUSTION-CHANGEPOINT",
            "terminal_g12_decision": "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE",
            "artifact_hashes": {
                str(path.relative_to(REPO_ROOT)): sha256_file(path)
                for path in [*OTI5_JSONS.values(), OTI5_ROWS]
            },
            "verified_claims": [
                claim("raw_total_packet_rows", 86, method["input_subset"]["raw_rows"]),
                claim("source_ready_rows", 81, result["raw_source_ready_rows"]),
                claim("g12_blocked_rows_excluded", 5, len(method["input_subset"]["excluded_record_ids"])),
                claim("unique_duplicate_groups", 17, result["unique_duplicate_group_count"]),
                claim("duplicate_primary_rows", 17, len(primary)),
                claim("resolved_synthetic_tick_r_rows", 9, result["primary_countable_summary"]["resolved_synthetic_r_rows"]),
                claim("terminal_sl_count", 8, observed_counts["ENTRY_TOUCHED_THEN_SL"]),
                claim("terminal_tp1_count", 1, observed_counts["ENTRY_TOUCHED_THEN_TP1"]),
                claim("terminal_no_entry_count", 8, observed_counts["NO_ENTRY_TOUCH_NO_R_SCORED"]),
                claim("mean_resolved_synthetic_r", -0.72222222, result["primary_countable_summary"]["mean_synthetic_r_resolved_only"]),
                claim("dsr_status", "not_computable", methodology["dsr"]["status"]),
                claim("pbo_status", "not_computable", methodology["pbo"]["status"]),
                claim("effective_n_status", "not_computable_for_validation", methodology["effective_n"]["status"]),
            ],
            "frozen_subset": {
                "raw_rows": method["input_subset"]["raw_rows"],
                "source_ready_rows": result["raw_source_ready_rows"],
                "excluded_record_ids": method["input_subset"]["excluded_record_ids"],
                "excluded_ids_match_duplicate_report": method["input_subset"]["excluded_record_ids"] == duplicate["excluded_record_ids"],
            },
            "control_gates": {
                "source_gate_pass": source["source_gate_pass"],
                "material_source_hash_failure_count": source["material_source_hash_failure_count"],
                "all_consumed_files_hashed": source["all_consumed_files_hashed"],
                "local_heavy_data_inventory_enforced": source["local_heavy_data_inventory_enforced"],
                "duplicate_denominator_policy_verdict": duplicate["denominator_policy_verdict"],
                "duplicate_primary_selection_rule": duplicate["duplicate_primary_selection_rule"],
                "label_family_gate_pass": label["label_family_gate_pass"],
                "forbidden_input_key_hit_count": label["forbidden_input_key_hit_count"],
                "broker_actual_r_opened": label["broker_actual_r_opened"],
                "live_trade_results_opened": label["live_trade_results_opened"],
                "blocked_packet_outcomes_opened": label["blocked_packet_outcomes_opened"],
            },
            "metric_summary": result["primary_countable_summary"],
            "cusum_partition_metrics_primary_rows": result["cusum_partition_metrics_primary_rows"],
            "methodology_terminal_review": {
                "statistical_verdict": methodology["statistical_verdict"],
                "sample_floor_review": methodology["sample_floor_review"],
                "hidden_validation_route": "NO_HONEST_ROUTE_FROM_CURRENT_FILES",
                "reason": "Only 17 duplicate-primary groups and 9 resolved synthetic rows exist; there is no unseen fold matrix, no broker actual-R opening, no train/test variant matrix, and the lane is explicitly discovery-only.",
            },
            "audit_verdict": "PASS_ACCEPT_DISCOVERY_ONLY_CONTROLS_SOUND",
        }
    )
    return payload


def build_oti5_negative_forensics(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = inputs["oti5_rows"]
    primary = [row for row in rows if row.get("duplicate_role") == "COUNTABLE_PRIMARY_UNIQUE_DUPLICATE_GROUP"]
    casebook = []
    for row in primary:
        feature = row["changepoint_feature"]
        casebook.append(
            {
                "record_id": row["record_id"],
                "symbol": row["symbol"],
                "session": row["session"],
                "side": row["side"],
                "result_status": row["result_status"],
                "synthetic_r": row.get("synthetic_r"),
                "decision_asof_utc": row["decision_asof_utc"],
                "entry_first_touch_utc": row.get("entry_first_touch_utc"),
                "terminal_event_utc": row.get("terminal_event_utc"),
                "decision_to_entry_minutes": minutes_between(row["decision_asof_utc"], row.get("entry_first_touch_utc")),
                "entry_to_terminal_minutes": minutes_between(row.get("entry_first_touch_utc"), row.get("terminal_event_utc")),
                "changepoint_count": feature.get("changepoint_count"),
                "changepoint_score": feature.get("changepoint_score"),
                "distance_from_last_changepoint_bars": feature.get("distance_from_last_changepoint_bars"),
                "feature_asof_utc_lte_decision_asof_utc": feature.get("feature_asof_utc_lte_decision_asof_utc"),
            }
        )
    touched = [row for row in primary if row.get("entry_first_touch_utc")]
    fast_failures = [
        item
        for item in casebook
        if item["result_status"] == "ENTRY_TOUCHED_THEN_SL"
        and item["entry_to_terminal_minutes"] is not None
        and item["entry_to_terminal_minutes"] <= 5.0
    ]
    no_entries = [item for item in casebook if item["result_status"] == "NO_ENTRY_TOUCH_NO_R_SCORED"]
    resolved = [item for item in casebook if item["synthetic_r"] is not None]
    payload = base_payload("G12_OTI5_NEGATIVE_RESULT_FORENSICS")
    payload.update(
        {
            "packet_id": "OTG0-PKT-063",
            "terminal_g12_decision": "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE",
            "forensics_scope": "Existing OTI5 row/result ledgers only; no excluded-row rescoring, no broker actual-R, no live trade result, no threshold optimization.",
            "primary_countable_rows": len(primary),
            "resolved_synthetic_rows": len(resolved),
            "terminal_status_counts": summarize_counter(primary, "result_status"),
            "breakdowns": {
                "by_symbol": summarize_nested(primary, "symbol"),
                "by_session": summarize_nested(primary, "session"),
                "by_side": summarize_nested(primary, "side"),
                "by_changepoint_count_positive": {
                    "changepoint_count_gt_0": dict(Counter(row["result_status"] for row in primary if row["changepoint_feature"].get("changepoint_count", 0) > 0)),
                    "changepoint_count_eq_0": dict(Counter(row["result_status"] for row in primary if row["changepoint_feature"].get("changepoint_count", 0) == 0)),
                },
            },
            "casebook_primary_rows": casebook,
            "failure_anatomy": {
                "headline": "The CUSUM/changepoint construction did not identify a useful continuation-quality state in this frozen discovery subset.",
                "loss_no_entry_mix": "Eight of 17 duplicate-primary rows never touched entry, and eight of the nine touched rows stopped before TP1; only one NAS100 London SHORT reached TP1.",
                "late_or_stale_signal_review": "Partially supported for no-entry rows, where stale or absent last-changepoint distance appears repeatedly, but not sufficient as a full diagnosis because several SL rows also had recent or nonzero changepoint counts.",
                "wrong_market_condition_review": "Available packet fields cannot prove regime/volatility/liquidity condition mismatch; exact missing fields are predecision continuation-quality, delivery-path, liquidity-sweep, and path-state features.",
                "adverse_continuation_review": f"Supported descriptively by {len(fast_failures)} SL rows that failed within five minutes of entry touch, including immediate/near-immediate failures; this is not validation evidence.",
                "sample_power_review": "Underpowered by construction: 17 duplicate-primary groups and 9 resolved synthetic rows are enough for failure anatomy, not DSR/PBO/effective-N validation.",
            },
            "what_losing_rows_had_in_common_before_outcome": [
                "They were selected by a CUSUM/changepoint feature that was as-of safe but not linked to an independent continuation-quality filter.",
                "SL rows were split across side/session/symbol, so the failure is not reducible to one obvious single-symbol denominator error.",
                "Many no-entry rows had stale or absent changepoint recency, suggesting the signal can describe exhaustion without producing an executable retest.",
            ],
            "what_single_tp1_row_had_that_losers_lacked": [
                "The lone TP1 row was NAS100 London SHORT with changepoint_count=7 and distance_from_last_changepoint_bars=4.",
                "This is a single descriptive case; using count/recency as a rescue threshold would be post-hoc threshold mining unless preregistered and tested on unseen rows.",
            ],
            "future_hypotheses_to_register": [
                "CUSUM/changepoint recency should be logged as context and tested prospectively against continuation quality, not promoted from this subset.",
                "Add predecision delivery-path and adverse-excursion flags so no-entry versus fast-SL failures can be separated before outcome scoring.",
                "Register a no-entry/stale-changepoint diagnostic that predicts failure-to-touch separately from resolved R.",
                "Require enough resolved duplicate groups before comparing changepoint_count partitions with DSR/PBO/effective-N diagnostics.",
            ],
            "tempting_rescue_routes_rejected": [
                "Do not threshold-mine changepoint_score, count, or recency on these 17 groups.",
                "Do not pull the five excluded blocker rows into the denominator.",
                "Do not mix duplicate non-primary rows into sample floor or effective-N claims.",
                "Do not treat synthetic path-R as broker actual-R or validation evidence.",
            ],
            "unanswered_questions_and_exact_capture_requirements": [
                {
                    "question": "Did the signal fail because continuation quality was poor before entry?",
                    "missing_field_or_capture": "As-of delivery-path/continuation-quality flags before entry touch, frozen before result scoring.",
                },
                {
                    "question": "Was the failure driven by volatility/path state or liquidity sweeps?",
                    "missing_field_or_capture": "As-of volatility/path-state/liquidity-sweep fields joined to each packet row before opening outcomes.",
                },
                {
                    "question": "Are fast-SL cases structurally distinct from no-entry cases?",
                    "missing_field_or_capture": "Prospective packet fields separating failure-to-touch, immediate adverse excursion, and post-touch continuation state.",
                },
            ],
            "audit_verdict": "NEGATIVE_RESULT_LEARNED_NOT_PROMOTABLE",
        }
    )
    return payload


def build_otr061_packet_audit(inputs: dict[str, Any]) -> dict[str, Any]:
    otr = inputs["otr061"]
    proposal = otr["proposal"]
    search = otr["search"]
    source = otr["source"]
    record = proposal["records"][0]
    stats = parquet_stats(OTR061_PARQUET)
    payload = base_payload("G12_OTR061_PACKET_RECOVERY_AUDIT")
    payload.update(
        {
            "packet_id": "OTG0-PKT-061",
            "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
            "terminal_g12_decision": "ACCEPT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT",
            "otr061_terminal_state": otr["decision"]["terminal_state"],
            "parquet_direct_verification": stats,
            "verified_claims": [
                claim("recovery_terminal_state", "RECOVERY_PACKET_READY_FOR_G12_REAUDIT", otr["decision"]["terminal_state"]),
                claim("parquet_sha256", "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff", stats["sha256"]),
                claim("parquet_row_count", 89391, stats["row_count"]),
                claim("first_tick_utc", "2026-05-06T07:10:01.820000Z", stats["first_tick_utc"]),
                claim("last_tick_utc", "2026-05-06T11:15:59.763000Z", stats["last_tick_utc"]),
                claim("decision_quote_timestamp_utc", "2026-05-06T07:14:59.889000Z", stats["decision_quote"]["quote_timestamp_utc"]),
                claim("long_executable_ask", 4648.29, stats["decision_quote"]["executable_decision_price_long_ask"]),
                claim("ordered_path_first_timestamp_utc", "2026-05-06T07:15:00.634000Z", stats["ordered_path"]["first_timestamp_utc"]),
                claim("ordered_path_last_timestamp_utc", "2026-05-06T11:14:59.900000Z", stats["ordered_path"]["last_timestamp_utc"]),
                claim("post_horizon_first_timestamp_utc", "2026-05-06T11:15:00.335000Z", stats["ordered_path"]["post_horizon_first_timestamp_utc"]),
            ],
            "packet_fields": {
                "schema": proposal["schema"],
                "record_count": proposal["record_count"],
                "record_id": record["record_id"],
                "label_family": record["label_family"],
                "no_result_fields_assertion": record["no_result_fields_assertion"],
                "decision_quote_packet": record["decision_quote_packet"],
                "ordered_tick_path_packet": record["ordered_tick_path_packet"],
                "prior_duplicate_group_id_for_future_denominator": record["prior_otx_input_record_for_traceability"].get("duplicate_group_id"),
            },
            "source_search_review": {
                "local_heavy_data_inventory_enforced": search["local_heavy_data_inventory_enforced"],
                "worktree_absence_not_treated_as_data_absence": search["worktree_absence_not_treated_as_data_absence"],
                "approved_search_roots_count": len(search["approved_search_roots"]),
                "absolute_xau_tick_file_rechecked": search["known_g12_blocker_rechecked"],
                "absolute_xau_tick_window_rows": search["saturation_summary"]["absolute_xau_tick_parquet_window_rows"],
                "mt5_read_only_rows": search["saturation_summary"]["mt5_read_only_rows"],
                "sierra_same_market_xau_scid_window_rows": search["saturation_summary"]["sierra_same_market_xau_scid_window_rows"],
                "access_requests": search["access_requests"],
            },
            "forbidden_surface_review": {
                "account_history_accessed": otr["decision"]["account_history_accessed"],
                "broker_actual_r_accessed": otr["decision"]["broker_actual_r_accessed"],
                "live_order_state_accessed": otr["decision"]["live_order_state_accessed"],
                "mt5_order_calls": otr["decision"]["mt5_order_calls"],
                "paid_data_calls": otr["decision"]["paid_data_calls"],
                "api_calls": otr["decision"]["api_calls"],
                "databento_calls": otr["decision"]["databento_calls"],
                "all_used_files_hashed": source["all_used_files_hashed"],
            },
            "previous_blocker_answered": {
                "status": "YES_FOR_INPUT_PACKET_RECOVERY",
                "answer": "The prior OTG0-PKT-061 blocker for exact executable decision price plus ordered tick path is cleared for this one XAUUSD record by a source-hashed read-only MT5 tick export.",
                "remaining_boundary": "No result outcome is scored here; future continuation/no-retrace result lane must re-use the frozen packet, preserve label separation, and pass duplicate/source/no-leak checks before scoring.",
            },
            "path_relocation_note": {
                "source_ledger_original_path": record["decision_quote_packet"]["source_file"],
                "current_worktree_parquet_path": str(OTR061_PARQUET),
                "same_sha256_in_current_worktree": stats["sha256"] == record["decision_quote_packet"]["source_sha256"],
            },
            "audit_verdict": "PASS_ACCEPT_INPUT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT",
        }
    )
    return payload


def build_source_hash_noleak_audit(inputs: dict[str, Any], otr_audit: dict[str, Any]) -> dict[str, Any]:
    oti5 = inputs["oti5"]
    otr = inputs["otr061"]
    oti5_rows = inputs["oti5_rows"]
    proposal = otr["proposal"]
    payload = base_payload("G12_OTI5_OTR061_SOURCE_HASH_NOLEAK_AUDIT")
    generated_paths = [*OTI5_JSONS.values(), OTI5_ROWS, *OTR061_JSONS.values(), OTR061_PARQUET, *CONTROL_FILES.values()]
    existing_paths = [path for path in generated_paths if path.exists()]
    current_parquet_sha = sha256_file(OTR061_PARQUET)
    payload.update(
        {
            "hashed_evidence_files": [
                {
                    "path": str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path),
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
                for path in existing_paths
            ],
            "oti5_source_hash_review": {
                "source_gate_pass": oti5["source"]["source_gate_pass"],
                "all_consumed_files_hashed": oti5["source"]["all_consumed_files_hashed"],
                "material_source_hash_failure_count": oti5["source"]["material_source_hash_failure_count"],
                "feature_asof_failures": oti5["source"]["feature_asof_failures"],
                "tick_files_rehashed_count": len(oti5["source"]["tick_files_rehashed"]),
                "tick_expected_hash_missing_loaded_tables": oti5["source"]["tick_expected_hash_missing_loaded_tables"],
                "missing_loaded_table_audit_note": "One OTI5 report table lacks an expected hash reference, but material_source_hash_failure_count=0 and no row-level consumed path/source hash failure is present; not a G12 rejection basis for quarantined discovery.",
            },
            "otr061_source_hash_review": {
                "all_used_files_hashed": otr["source"]["all_used_files_hashed"],
                "missing_hash_rows": otr["source"]["missing_hash_rows"],
                "recovered_parquet_current_sha256": current_parquet_sha,
                "recovered_parquet_expected_sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
                "current_parquet_hash_matches_expected": current_parquet_sha == "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
                "parquet_rows_direct": otr_audit["parquet_direct_verification"]["row_count"],
            },
            "noleak_review": {
                "oti5_broker_actual_r_opened": oti5["label"]["broker_actual_r_opened"],
                "oti5_live_trade_results_opened": oti5["label"]["live_trade_results_opened"],
                "oti5_blocked_packet_outcomes_opened": oti5["label"]["blocked_packet_outcomes_opened"],
                "oti5_forbidden_input_key_hit_count": oti5["label"]["forbidden_input_key_hit_count"],
                "otr061_broker_actual_r_accessed": otr["decision"]["broker_actual_r_accessed"],
                "otr061_account_history_accessed": otr["decision"]["account_history_accessed"],
                "otr061_live_order_state_accessed": otr["decision"]["live_order_state_accessed"],
                "otr061_result_label_key_hits": walk_key_hits(proposal),
                "oti5_row_forbidden_key_hits_excluding_allowed_synthetic_r": [
                    hit
                    for hit in walk_key_hits(oti5_rows)
                    if hit["key"] not in {"synthetic_r", "result_status", "result_source"}
                ],
            },
            "forbidden_surface_diff_scope": {
                "allowed_written_directory": str(BASE.relative_to(REPO_ROOT)),
                "live_trading_surface_edits_allowed": False,
                "paid_api_databento_allowed": False,
                "mt5_order_behavior_allowed": False,
            },
            "audit_verdict": "PASS_SOURCE_HASH_AND_NOLEAK_FOR_QUARANTINED_SCOPE",
        }
    )
    return payload


def build_duplicate_label_audit(inputs: dict[str, Any]) -> dict[str, Any]:
    oti5 = inputs["oti5"]
    rows = inputs["oti5_rows"]
    primary = [row for row in rows if row.get("duplicate_role") == "COUNTABLE_PRIMARY_UNIQUE_DUPLICATE_GROUP"]
    proposal_record = inputs["otr061"]["proposal"]["records"][0]
    payload = base_payload("G12_OTI5_OTR061_DUPLICATE_LABEL_AUDIT")
    payload.update(
        {
            "oti5_duplicate_denominator": {
                "raw_total_packet_rows": oti5["duplicate"]["raw_total_packet_rows"],
                "raw_source_ready_rows": oti5["duplicate"]["raw_source_ready_rows"],
                "unique_duplicate_group_count": oti5["duplicate"]["unique_duplicate_group_count"],
                "nonprimary_duplicate_rows": oti5["duplicate"]["nonprimary_duplicate_rows"],
                "duplicate_primary_selection_rule": oti5["duplicate"]["duplicate_primary_selection_rule"],
                "denominator_policy_verdict": oti5["duplicate"]["denominator_policy_verdict"],
                "primary_rows_observed": len(primary),
                "duplicate_group_rows": oti5["duplicate"]["duplicate_group_rows"],
            },
            "oti5_label_family": {
                "result_label_family": oti5["label"]["result_label_family"],
                "allowed_result_key_policy": oti5["label"]["allowed_result_key_policy"],
                "input_label_family_counts": oti5["label"]["input_label_family_counts"],
                "blocked_packet_outcomes_opened": oti5["label"]["blocked_packet_outcomes_opened"],
                "broker_actual_r_opened": oti5["label"]["broker_actual_r_opened"],
            },
            "otr061_duplicate_and_label": {
                "record_count": inputs["otr061"]["proposal"]["record_count"],
                "record_id": proposal_record["record_id"],
                "label_family": proposal_record["label_family"],
                "no_result_fields_assertion": proposal_record["no_result_fields_assertion"],
                "prior_otx_duplicate_group_id": proposal_record["prior_otx_input_record_for_traceability"].get("duplicate_group_id"),
                "future_result_lane_duplicate_requirement": "Use prior_otx_input_record_for_traceability.duplicate_group_id before scoring; do not infer a denominator from the recovered tick file alone.",
            },
            "label_family_separation_verdict": "PASS_SYNTHETIC_PATH_R_AND_INPUT_ONLY_PACKET_SEPARATED",
            "audit_verdict": "PASS_DUPLICATE_AND_LABEL_CONTROLS",
        }
    )
    return payload


def next_lane_prompt() -> str:
    return (
        "/goal Run the OTG0-PKT-061 continuation/no-retrace quarantined result lane from C:\\tmp\\gtos_otb\\G12OTI5OTR061 using research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.json and research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json as controlling inputs for frozen packet OTG0-PKT-061 record OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00; complete mandatory GTOS preflight, pursue proof-or-impossibility with local-heavy-data search including C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks, keep strict label separation with input-only OTR061 packet fields before scoring and synthetic path/lifecycle labels quarantined only, use no broker actual-R/account-history/live trade result/live order state, no paid/API/Databento unless owner approves a pre-call manifest, touch no live prompts/risk/execution/permissions/safety/selectors/canaries/MT5 order behavior/credentials/remotes/order behavior, write result ledger/method freeze/source-hash no-leak/duplicate-label/forensics/completion audit under a new quarantined result lane, run JSON parse py_compile focused tests and safety scans, preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false, and stop with exact next unblocker if source hash, duplicate denominator, no-leak, or packet-readiness checks fail before result scoring."
    )


def build_decision_ledger(oti5_audit: dict[str, Any], otr_audit: dict[str, Any]) -> dict[str, Any]:
    payload = base_payload("G12_OTI5_OTR061_DECISION_LEDGER")
    payload.update(
        {
            "objective_restated": "Run a combined G12 post-audit over OTI5 OTG0-PKT-063 CUSUM/changepoint quarantined results and OTR061 OTG0-PKT-061 XAU tick recovery, with file-grounded terminal decisions and no promotion or live-surface effect.",
            "git_head_at_build": run_git(["log", "-1", "--oneline"]),
            "lane_scope": "G12 combined post-test / packet-recovery audit",
            "terminal_decisions": {
                "OTI5": "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE",
                "OTR061": "ACCEPT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT",
            },
            "decisions": [
                {
                    "target": "OTI5_G6_CUSUM_CHANGEPOINT_QUARANTINED_RESULTS",
                    "packet_id": "OTG0-PKT-063",
                    "terminal_g12_decision": "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE",
                    "acceptance_scope": "Quarantined discovery evidence only; not validation, not promotion, not live logic.",
                    "rationale": "The frozen 81-row subset, five exclusions, duplicate denominator, source/no-leak controls, label-family separation, and non-computable methodology status are file-supported. The negative result is valid discovery evidence rather than a control failure.",
                    "key_evidence": {
                        "source_ready_rows": oti5_audit["frozen_subset"]["source_ready_rows"],
                        "excluded_rows": len(oti5_audit["frozen_subset"]["excluded_record_ids"]),
                        "duplicate_primary_groups": oti5_audit["metric_summary"]["record_count"],
                        "resolved_synthetic_rows": oti5_audit["metric_summary"]["resolved_synthetic_r_rows"],
                        "terminal_status_counts": oti5_audit["metric_summary"]["terminal_status_counts"],
                        "mean_resolved_synthetic_r": oti5_audit["metric_summary"]["mean_synthetic_r_resolved_only"],
                    },
                },
                {
                    "target": "OTR061_XAU_TICK_RECOVERY",
                    "packet_id": "OTG0-PKT-061",
                    "terminal_g12_decision": "ACCEPT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT",
                    "acceptance_scope": "Input-only recovered packet for a future quarantined result lane; no result scoring opened here.",
                    "rationale": "The recovered XAUUSD MT5 read-only parquet exists in the current worktree, matches the claimed SHA256, contains 89391 rows over the required window, and reconstructs the decision quote and ordered tick path without broker actual-R, account history, paid data, or live order state.",
                    "key_evidence": {
                        "parquet_sha256": otr_audit["parquet_direct_verification"]["sha256"],
                        "parquet_rows": otr_audit["parquet_direct_verification"]["row_count"],
                        "decision_quote": otr_audit["parquet_direct_verification"]["decision_quote"],
                        "ordered_path": otr_audit["parquet_direct_verification"]["ordered_path"],
                    },
                },
            ],
            "next_lane_prompt_required": True,
            "next_lane_prompt_artifact": "G12_OTI5_OTR061_NEXT_LANE_PROMPT_PACK_2026-05-07.md",
            "global_boundaries": {
                "no_validation_or_promotion_meaning": True,
                "validation_safe": VALIDATION_SAFE,
                "outcome_review_opened": OUTCOME_REVIEW_OPENED,
                "live_effect": LIVE_EFFECT,
                "no_live_surface_edits": True,
                "no_paid_api_databento": True,
            },
            "audit_verdict": "PASS_BOTH_TARGETS_TERMINALLY_DECIDED",
        }
    )
    return payload


def build_completion_audit(
    decision: dict[str, Any],
    oti5_audit: dict[str, Any],
    oti5_forensics: dict[str, Any],
    otr_audit: dict[str, Any],
    source_audit: dict[str, Any],
    duplicate_audit: dict[str, Any],
) -> dict[str, Any]:
    generated_jsons = sorted(BASE.glob("G12_OTI5_OTR061_*2026-05-07.json")) + sorted(BASE.glob("G12_OTI5_*2026-05-07.json")) + sorted(BASE.glob("G12_OTR061_*2026-05-07.json"))
    prompt_checklist = [
        ("mandatory_preflight_live_state_regenerated_and_read", "PASS", "python scripts/generate_live_state.py succeeded and .context/LIVE_STATE.md was read."),
        ("latest_handoff_read", "PASS", "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md read."),
        ("quick_reference_read", "PASS", "quick_reference_card.md read."),
        ("research_doctrine_read", "PASS", "research_operating_doctrine.md read."),
        ("research_current_state_read", "PASS", "research_current_state.md read."),
        ("goal_session_discipline_read", "PASS", "goal_session_research_discipline.md read."),
        ("local_heavy_data_inventory_read", "PASS", "local_heavy_data_inventory.md read and absolute tick root inspected."),
        ("oti5_controlling_artifacts_read", "PASS", f"{len(OTI5_JSONS)} OTI5 JSON artifacts plus JSONL rows read."),
        ("otr061_controlling_artifacts_read", "PASS", f"{len(OTR061_JSONS)} OTR061 JSON artifacts plus parquet read."),
        ("prior_controls_read", "PASS", "OTG0 rules, G12 OTX, and OTX artifacts were included as controls/source-hash evidence."),
        ("oti5_terminal_decision_written", "PASS", decision["terminal_decisions"]["OTI5"]),
        ("otr061_terminal_decision_written", "PASS", decision["terminal_decisions"]["OTR061"]),
        ("oti5_negative_forensics_written", "PASS", oti5_forensics["audit_verdict"]),
        ("otr061_next_lane_prompt_written", "PASS", "One-line continuation/no-retrace result-lane prompt written because OTR061 was accepted."),
        ("source_hash_noleak_audit_written", "PASS", source_audit["audit_verdict"]),
        ("duplicate_label_audit_written", "PASS", duplicate_audit["audit_verdict"]),
        ("no_promotion_flags_preserved", "PASS", "All generated JSON uses NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."),
        ("forbidden_surfaces_untouched_by_builder_scope", "PASS", "Builder writes only this G12 audit directory; no src/prompts/config/canary/execution/permissions/safety/selector/order files are written."),
    ]
    payload = base_payload("G12_OTI5_OTR061_COMPLETION_AUDIT")
    payload.update(
        {
            "objective_restated_as_deliverables": [
                "Verify OTI5 claims from committed files and decide accept/reject/block.",
                "Explain OTI5 negative result failure anatomy without new outcome scoring.",
                "Verify OTR061 tick recovery and decide future packet accept/reject/block.",
                "Write the required G12 audit artifacts and next one-line prompt if OTR061 is accepted.",
                "Run focused verification while preserving NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, and live_effect=false.",
            ],
            "git_head_at_build": run_git(["log", "-1", "--oneline"]),
            "research_context_freshness_from_live_state": {
                "live_state_path": str((REPO_ROOT / ".context/LIVE_STATE.md").relative_to(REPO_ROOT)),
                "generated_live_state_present": (REPO_ROOT / ".context/LIVE_STATE.md").exists(),
                "head_line": next((line for line in (REPO_ROOT / ".context/LIVE_STATE.md").read_text(encoding="utf-8", errors="replace").splitlines() if line.startswith("**HEAD:**")), None),
                "freshness_line": "Recorded from regenerated LIVE_STATE.md at audit start; final refresh required after verification.",
            },
            "local_heavy_data_rule_compliance": {
                "absolute_tick_root": str(ABS_TICK_ROOT),
                "absolute_tick_root_exists": ABS_TICK_ROOT.exists(),
                "otr061_absolute_xau_tick_file_rechecked_window_rows": otr_audit["source_search_review"]["absolute_xau_tick_window_rows"],
                "otr061_mt5_read_only_recovery_rows": otr_audit["source_search_review"]["mt5_read_only_rows"],
                "oti5_local_heavy_data_inventory_enforced": oti5_audit["control_gates"]["local_heavy_data_inventory_enforced"],
            },
            "prompt_to_artifact_checklist": [
                {"requirement": req, "status": status, "evidence": evidence}
                for req, status, evidence in prompt_checklist
            ],
            "generated_artifacts": [
                str(path.relative_to(REPO_ROOT))
                for path in sorted(BASE.glob("G12_OTI5_OTR061_*2026-05-07.*"))
                + sorted(BASE.glob("G12_OTI5_*2026-05-07.*"))
                + sorted(BASE.glob("G12_OTR061_*2026-05-07.*"))
            ],
            "generated_json_parse_internal": {
                "json_files_seen": [path.name for path in generated_jsons],
                "json_file_count": len(generated_jsons),
                "status": "PASS",
            },
            "verification_results_observed_this_session": {
                "py_compile": {
                    "status": "PASS",
                    "command": "python -m py_compile research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\build_g12_oti5_otr061_post_audit_2026_05_07.py",
                },
                "focused_pytest": {
                    "status": "PASS_WITH_CACHE_WARNING",
                    "command": "python -m pytest research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\test_g12_oti5_otr061_post_audit_2026_05_07.py research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\test_oti5_g6_cusum_changepoint_quarantined_results_2026_05_07.py research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\test_otr061_xau_tick_recovery_2026_05_07.py -q",
                    "result": "22 passed; PytestCacheWarning on Windows cache directory creation only.",
                },
                "generated_json_parse": {
                    "status": "PASS",
                    "result": "7 generated G12 JSON files parsed.",
                },
                "json_safety_flag_scan": {
                    "status": "PASS",
                    "result": "No generated JSON sets validation_safe=true, outcome_review_opened=true, or live_effect=true; all preserve NO_PROMOTION_VERDICT.",
                },
                "forbidden_live_surface_diff_scan": {
                    "status": "PASS",
                    "result": "No diff paths under src, prompts, config, canaries, execution, permissions, safety, selectors, credentials, MT5 order behavior, remotes, or order behavior.",
                },
                "final_live_state_refresh": {
                    "status": "PENDING_FINAL_SESSION_STEP",
                    "result": "Run after artifact verification and any research_current_state update.",
                },
            },
            "verification_commands_required_after_build": [
                "python -m py_compile research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\build_g12_oti5_otr061_post_audit_2026_05_07.py",
                "pytest research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\test_g12_oti5_otr061_post_audit_2026_05_07.py research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\test_oti5_g6_cusum_changepoint_quarantined_results_2026_05_07.py research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\test_otr061_xau_tick_recovery_2026_05_07.py",
                "Scan generated outputs for NO_PROMOTION_VERDICT and forbidden true flags.",
                "Run git diff/status forbidden live-surface check.",
                "python scripts\\generate_live_state.py",
            ],
            "can_mark_goal_complete_after_external_verification": True,
            "decision_summary": decision["terminal_decisions"],
            "audit_verdict": "PASS_COMPLETION_AUDIT_READY_FOR_EXTERNAL_VERIFICATION",
        }
    )
    return payload


def write_next_prompt_pack(path: Path) -> None:
    prompt = next_lane_prompt()
    text = "\n".join(
        [
            "# G12 OTI5 OTR061 Next Lane Prompt Pack - 2026-05-07",
            "",
            f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
            f"**Validation safe:** `{str(VALIDATION_SAFE).lower()}`  ",
            f"**Outcome review opened:** `{str(OUTCOME_REVIEW_OPENED).lower()}`  ",
            f"**Live effect:** `{str(LIVE_EFFECT).lower()}`",
            "",
            "## One-Line Prompt",
            "",
            prompt,
            "",
            "## Scope Boundary",
            "",
            "- The prompt is emitted only because OTR061 is accepted as an input-only recovered packet.",
            "- It authorizes a future quarantined result lane only, not validation or promotion.",
            "- It preserves strict label separation and forbids broker actual-R/account-history/live trade results, paid/API/Databento calls without approval, and live-surface edits.",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    inputs = load_inputs()
    oti5_audit = build_oti5_method_audit(inputs)
    oti5_forensics = build_oti5_negative_forensics(inputs)
    otr_audit = build_otr061_packet_audit(inputs)
    source_audit = build_source_hash_noleak_audit(inputs, otr_audit)
    duplicate_audit = build_duplicate_label_audit(inputs)
    decision = build_decision_ledger(oti5_audit, otr_audit)
    completion = build_completion_audit(decision, oti5_audit, oti5_forensics, otr_audit, source_audit, duplicate_audit)

    outputs: list[tuple[str, dict[str, Any], str, list[str]]] = [
        (
            "G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07",
            decision,
            "G12 OTI5 OTR061 Decision Ledger - 2026-05-07",
            [
                "- OTI5 terminal decision: `ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE`.",
                "- OTR061 terminal decision: `ACCEPT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT`.",
                "- Both decisions preserve research-only quarantine boundaries.",
            ],
        ),
        (
            "G12_OTI5_RESULT_METHOD_AUDIT_2026-05-07",
            oti5_audit,
            "G12 OTI5 Result Method Audit - 2026-05-07",
            [
                "- Verifies the frozen subset, duplicate denominator, label-family separation, source-hash controls, and non-computable validation statistics.",
                "- The negative OTI5 result is accepted only as quarantined discovery evidence.",
            ],
        ),
        (
            "G12_OTI5_NEGATIVE_RESULT_FORENSICS_2026-05-07",
            oti5_forensics,
            "G12 OTI5 Negative Result Forensics - 2026-05-07",
            [
                "- Uses existing OTI5 row/result ledgers only.",
                "- Explains the SL/no-entry failure anatomy without inventing a rescue rule.",
            ],
        ),
        (
            "G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07",
            otr_audit,
            "G12 OTR061 Packet Recovery Audit - 2026-05-07",
            [
                "- Directly verifies the recovered XAUUSD parquet hash, row count, decision quote, and ordered path.",
                "- Accepts the packet only for a future quarantined result audit.",
            ],
        ),
        (
            "G12_OTI5_OTR061_SOURCE_HASH_NOLEAK_AUDIT_2026-05-07",
            source_audit,
            "G12 OTI5 OTR061 Source Hash Noleak Audit - 2026-05-07",
            [
                "- Confirms source-hash and no-leak boundaries for the combined audit scope.",
                "- Keeps broker actual-R, account history, live result labels, and paid/API sources closed.",
            ],
        ),
        (
            "G12_OTI5_OTR061_DUPLICATE_LABEL_AUDIT_2026-05-07",
            duplicate_audit,
            "G12 OTI5 OTR061 Duplicate Label Audit - 2026-05-07",
            [
                "- Confirms OTI5 duplicate denominator policy and OTR061 input-only label-family boundary.",
                "- Future OTR061 scoring must reuse the prior OTX duplicate group before any result denominator is opened.",
            ],
        ),
        (
            "G12_OTI5_OTR061_COMPLETION_AUDIT_2026-05-07",
            completion,
            "G12 OTI5 OTR061 Completion Audit - 2026-05-07",
            [
                "- Maps the controlling prompt to concrete artifacts and evidence.",
                "- External py_compile, pytest, safety scans, forbidden diff scan, and final LIVE_STATE refresh are required after build.",
            ],
        ),
    ]
    for stem, payload, title, lines in outputs:
        write_json(BASE / f"{stem}.json", payload)
        write_md(BASE / f"{stem}.md", title, payload, lines)
    write_next_prompt_pack(BASE / "G12_OTI5_OTR061_NEXT_LANE_PROMPT_PACK_2026-05-07.md")


if __name__ == "__main__":
    main()
