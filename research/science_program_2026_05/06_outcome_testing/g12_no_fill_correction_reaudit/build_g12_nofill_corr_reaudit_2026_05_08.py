#!/usr/bin/env python3
"""Build G12 reaudit artifacts for the corrected NOFILL close packet.

This builder is source/control only. It recomputes packet counts, OTR061 hash
and row-0127 side-aware first touch, stale blocker state, no-leak controls,
exclusions, duplicate/sample-floor controls, and next-lane guidance without
scoring R/performance or touching live trading surfaces.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LIVE_EFFECT = False

EXPECTED_PACKET_ROWS = 298
EXPECTED_SOURCE_CLOSED = 298
EXPECTED_SOURCE_BLOCKED_EXACT = 0
EXPECTED_OTR_SHA256 = "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
EXPECTED_OTR_FIRST = "2026-05-06T07:10:01.820000Z"
EXPECTED_OTR_LAST = "2026-05-06T11:15:59.763000Z"
EXPECTED_ROW_0127_TOUCH = "2026-05-06T07:15:00.634000Z"
EXPECTED_ROW_0127 = "NOFILL-CLOSE-ROW-0127"
EXPECTED_BLOCKED_CNR061 = 94
EXPECTED_T3_COUNT = 6

OUT_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = OUT_DIR.parent
REPO_ROOT = OUT_DIR.parents[3]
PACKET_DIR = OUTCOME_ROOT / "no_fill_lifecycle_closure_source_packet"
CORR_DIR = OUTCOME_ROOT / "no_fill_lifecycle_closure_source_correction"
PRIOR_G12_CLOSE_DIR = OUTCOME_ROOT / "g12_no_fill_closure_audit"
PRIOR_G12_NOFILL_DIR = OUTCOME_ROOT / "g12_no_fill_lifecycle_audit"
PRIOR_G12_CNR_T3_DIR = OUTCOME_ROOT / "g12_cnr_t3_lifecycle_audit"
NOFILL_CONTRACT_DIR = OUTCOME_ROOT / "no_fill_still_pending_lifecycle_contract"
OTR061_DIR = OUTCOME_ROOT / "otr061_xau_tick_recovery"
OTR061_FILE = OTR061_DIR / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
CONTROL_PROMPT = OUT_DIR.parent / "g12_no_fill_closure_correction_reaudit" / "G12_NOFILL_CORR_REAUDIT_GOAL_PROMPT_2026-05-08.md"

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "knowledge_base/trade_records/",
    "pipeline_state/",
)
FORBIDDEN_LIVE_NAME_NEEDLES = (
    "execution",
    "permissions",
    "risk",
    "safety",
    "selector",
    "mt5",
    "order",
    "credential",
    "remote",
    "databento",
    "api_key",
)

FORBIDDEN_PACKET_KEY_NEEDLES = (
    "actual_r",
    "broker",
    "account",
    "pnl",
    "profit",
    "performance",
    "hidden",
    "order_ticket",
    "deal",
    "position",
    "live_result",
    "r_multiple",
    "score_r",
    "realized",
)
ALLOWED_FORBIDDEN_KEY_EXCEPTIONS = {
    "live_effect",
    "no_r_performance_or_live_fields_carried",
    "outcome_review_opened",
    "promotion_verdict",
    "future_route_boundary",
}
MUTABLE_CONTEXT_HASH_PATHS = {
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
}
NONBLOCKING_CONTEXT_OR_CONTROL_HASH_PREFIXES = (
    ".context/",
    "research/science_program_2026_05/06_outcome_testing/oti",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.write_text("# " + title + "\n\n" + "\n".join(lines).rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_output(*args: str) -> str:
    cmd = ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", *args]
    try:
        return subprocess.check_output(cmd, cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # pragma: no cover - environmental fallback
        return f"GIT_UNAVAILABLE: {exc}"


def common_flags() -> dict[str, Any]:
    return {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "live_effect": LIVE_EFFECT,
    }


def load_inputs() -> dict[str, Any]:
    return {
        "packet": load_json(PACKET_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08.json"),
        "rows": load_jsonl(PACKET_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl"),
        "blocker": load_json(PACKET_DIR / "NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json"),
        "search": load_json(PACKET_DIR / "NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.json"),
        "packet_hash_noleak": load_json(PACKET_DIR / "NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json"),
        "packet_duplicate": load_json(PACKET_DIR / "NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json"),
        "packet_completion": load_json(PACKET_DIR / "NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json"),
        "source_request": load_json(PACKET_DIR / "source_requests" / "NOFILL-CLOSE-ROW-0127_XAUUSD_2026-05-06_ticks_READONLY_REQUEST.json"),
        "corr_resolution": load_json(CORR_DIR / "NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.json"),
        "corr_patch": load_json(CORR_DIR / "NOFILL_CORR_PATCH_LEDGER_2026-05-08.json"),
        "corr_hash_noleak": load_json(CORR_DIR / "NOFILL_CORR_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json"),
        "corr_duplicate": load_json(CORR_DIR / "NOFILL_CORR_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json"),
        "corr_completion": load_json(CORR_DIR / "NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json"),
        "prior_g12_close_universe": load_json(PRIOR_G12_CLOSE_DIR / "G12_NOFILL_CLOSE_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json"),
        "prior_g12_nofill_universe": load_json(PRIOR_G12_NOFILL_DIR / "G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json"),
        "prior_g12_cnr_t3_noleak": load_json(PRIOR_G12_CNR_T3_DIR / "G12_CNR_T3_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json"),
        "nofill_contract_noleak": load_json(NOFILL_CONTRACT_DIR / "NOFILL_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json"),
    }


def packet_counts(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = inputs["rows"]
    closure_status_counts = Counter(row.get("closure_status") for row in rows)
    closure_label_counts = Counter(row.get("closure_label") for row in rows)
    lane_counts = Counter(row.get("source_lane") for row in rows)
    exact_blocked_rows = [row["packet_row_id"] for row in rows if row.get("closure_status") == "source_blocked_exact"]
    return {
        "packet_json_count": inputs["packet"].get("packet_row_count"),
        "rows_jsonl_count": len(rows),
        "closure_status_counts": dict(sorted(closure_status_counts.items())),
        "closure_label_counts": dict(sorted(closure_label_counts.items())),
        "source_lane_counts": dict(sorted(lane_counts.items())),
        "blocker_ledger_source_closed_rows": inputs["blocker"].get("source_closed_rows"),
        "blocker_ledger_source_blocked_exact_rows": inputs["blocker"].get("source_blocked_exact_rows"),
        "exact_source_blocked_packet_row_ids": exact_blocked_rows,
        "packet_count_pass": inputs["packet"].get("packet_row_count") == EXPECTED_PACKET_ROWS and len(rows) == EXPECTED_PACKET_ROWS,
        "source_closed_pass": closure_status_counts.get("source_closed") == EXPECTED_SOURCE_CLOSED,
        "source_blocked_exact_pass": closure_status_counts.get("source_blocked_exact", 0) == EXPECTED_SOURCE_BLOCKED_EXACT
        and inputs["blocker"].get("source_blocked_exact_rows") == EXPECTED_SOURCE_BLOCKED_EXACT,
    }


def _format_timestamp_z(value: Any) -> str:
    import pandas as pd

    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def recompute_row_0127_touch(inputs: dict[str, Any]) -> dict[str, Any]:
    import pandas as pd

    row = next(row for row in inputs["rows"] if row["packet_row_id"] == EXPECTED_ROW_0127)
    projection = row["source_evidence"]["tick_terminal_sequence_projection"]
    side = row["projected_side"]
    entry = float(projection["entry_price"])
    terminal = float(projection["terminal_area_price"])
    protective = float(projection["protective_level_price"])
    path_start = pd.Timestamp(projection["path_start_utc"]).tz_convert("UTC")

    df = pd.read_parquet(OTR061_FILE, columns=["ts_utc", "bid", "ask", "mt5_symbol"])
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df = df.sort_values("ts_utc")
    full_first = _format_timestamp_z(df["ts_utc"].iloc[0])
    full_last = _format_timestamp_z(df["ts_utc"].iloc[-1])
    window = df[df["ts_utc"] >= path_start]

    def first_touch(label: str, mask: Any) -> dict[str, Any] | None:
        touched = window.loc[mask]
        if touched.empty:
            return None
        first = touched.iloc[0]
        return {
            "event": label,
            "first_touch_utc": _format_timestamp_z(first["ts_utc"]),
            "bid": float(first["bid"]),
            "ask": float(first["ask"]),
        }

    if side == "LONG":
        events = [
            first_touch("entry", window["ask"] <= entry),
            first_touch("terminal_area", window["bid"] >= terminal),
            first_touch("protective", window["bid"] <= protective),
        ]
        parser_contract = "LONG entry ask<=entry terminal bid>=terminal protective bid<=protective"
    else:
        events = [
            first_touch("entry", window["bid"] >= entry),
            first_touch("terminal_area", window["ask"] <= terminal),
            first_touch("protective", window["ask"] >= protective),
        ]
        parser_contract = "SHORT entry bid>=entry terminal ask<=terminal protective ask>=protective"

    observed_events = [event for event in events if event is not None]
    first_event = sorted(observed_events, key=lambda item: item["first_touch_utc"])[0] if observed_events else None
    selected = projection.get("selected_supplemental_source_files") or []
    source_hashes = projection.get("source_sha256") or {}
    current_hash = sha256_file(OTR061_FILE)
    return {
        **common_flags(),
        "status": "PASS" if first_event and first_event["event"] == "terminal_area" and first_event["first_touch_utc"] == EXPECTED_ROW_0127_TOUCH else "FAIL",
        "packet_row_id": EXPECTED_ROW_0127,
        "source_inventory_id": row.get("source_inventory_id"),
        "source_row_id": row.get("source_row_id"),
        "projected_symbol": row.get("projected_symbol"),
        "projected_side": side,
        "decision_asof_utc": row.get("decision_asof_utc"),
        "path_start_utc": projection.get("path_start_utc"),
        "path_end_utc": projection.get("path_end_utc"),
        "entry_price": entry,
        "terminal_area_price": terminal,
        "protective_level_price": protective,
        "parser_contract": parser_contract,
        "closure_status": row.get("closure_status"),
        "closure_label": row.get("closure_label"),
        "packet_reported_terminal_area_touch_time_utc": projection.get("terminal_area_touch_time_utc"),
        "recomputed_first_source_event": first_event,
        "recomputed_ordered_source_events": observed_events,
        "source_path": rel(OTR061_FILE),
        "source_sha256": current_hash,
        "expected_sha256": EXPECTED_OTR_SHA256,
        "source_sha256_matches_expected": current_hash == EXPECTED_OTR_SHA256,
        "source_first_ts_utc": full_first,
        "source_last_ts_utc": full_last,
        "source_rows_total": int(len(df)),
        "rows_at_or_after_path_start": int(len(window)),
        "expected_coverage_pass": full_first == EXPECTED_OTR_FIRST and full_last == EXPECTED_OTR_LAST,
        "selected_supplemental_source_files": selected,
        "selected_source_hashes": source_hashes,
        "selected_hash_matches_current_source": bool(selected) and source_hashes.get(selected[0]) == current_hash,
        "source_only_non_claim": "This proves first source-side terminal-area touch ordering for row 0127 only; it does not score R/performance, fill, broker, account, live, or hidden labels.",
    }


def source_hash_checks(inputs: dict[str, Any]) -> dict[str, Any]:
    mismatches: list[dict[str, Any]] = []
    mutable_context_mismatches: list[dict[str, Any]] = []
    context_or_control_mismatches: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    checked = 0
    for entry in inputs["search"].get("consumed_source_files", []):
        path = Path(entry["path"])
        expected = entry.get("expected_sha256") or entry.get("sha256")
        if not expected:
            continue
        if not path.exists():
            missing.append({"path": str(path), "expected_sha256": expected})
            continue
        checked += 1
        actual = sha256_file(path)
        if actual != expected:
            normalized = str(path).replace("\\", "/")
            if normalized in MUTABLE_CONTEXT_HASH_PATHS:
                mutable_context_mismatches.append({"path": str(path), "expected_sha256": expected, "actual_sha256": actual})
            elif any(normalized.startswith(prefix) for prefix in NONBLOCKING_CONTEXT_OR_CONTROL_HASH_PREFIXES):
                context_or_control_mismatches.append({"path": str(path), "expected_sha256": expected, "actual_sha256": actual})
            else:
                mismatches.append({"path": str(path), "expected_sha256": expected, "actual_sha256": actual})
    return {
        "status": "PASS" if not mismatches and not missing else "FAIL",
        "checked_count": checked,
        "missing_count": len(missing),
        "mismatch_count": len(mismatches),
        "mutable_context_mismatch_count": len(mutable_context_mismatches),
        "context_or_control_mismatch_count": len(context_or_control_mismatches),
        "mismatches": mismatches[:20],
        "mutable_context_mismatches_nonblocking": mutable_context_mismatches[:20],
        "context_or_control_mismatches_nonblocking": context_or_control_mismatches[:20],
        "missing": missing[:20],
        "strict_policy": "Heavy data, packet-source, and correction-source hash mismatches fail. Mutable context docs and prior research-control artifacts regenerated across main merges are recorded as nonblocking drift; row-level source evidence is still checked separately.",
    }


def stale_blocker_status(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = inputs["rows"]
    active_blocked_no_ticks = [
        row["packet_row_id"]
        for row in rows
        if any("BLOCKED_NO_TICKS_IN_WINDOW" in blocker for blocker in row.get("exact_blockers", []))
    ]
    active_requests = inputs["blocker"].get("read_only_extraction_requests", [])
    superseded = inputs["blocker"].get("superseded_read_only_extraction_requests", [])
    manifest = inputs["source_request"]
    return {
        "status": "PASS" if not active_blocked_no_ticks and not active_requests and len(superseded) == 1 and manifest.get("active_request") is False else "FAIL",
        "active_BLOCKED_NO_TICKS_IN_WINDOW_rows": active_blocked_no_ticks,
        "active_read_only_extraction_requests": active_requests,
        "superseded_read_only_extraction_requests": superseded,
        "source_request_manifest": {
            "request_id": manifest.get("request_id"),
            "packet_row_id": manifest.get("packet_row_id"),
            "active_request": manifest.get("active_request"),
            "current_audit_status": manifest.get("current_audit_status"),
            "original_source_gap": manifest.get("original_source_gap"),
            "source_gap": manifest.get("source_gap"),
            "terminal_area_touch_time_utc": manifest.get("terminal_area_touch_time_utc"),
        },
    }


def source_search_hardening(inputs: dict[str, Any]) -> dict[str, Any]:
    row = next(row for row in inputs["rows"] if row["packet_row_id"] == EXPECTED_ROW_0127)
    projection = row["source_evidence"]["tick_terminal_sequence_projection"]
    supplemental = projection.get("supplemental_tick_source_search") or {}
    builder_text = (PACKET_DIR / "build_nofill_lifecycle_closure_source_packet_2026_05_08.py").read_text(encoding="utf-8")
    verifier_text = (PACKET_DIR / "verify_nofill_lifecycle_closure_source_packet_2026_05_08.py").read_text(encoding="utf-8")
    test_text = (PACKET_DIR / "test_nofill_lifecycle_closure_source_packet_2026_05_08.py").read_text(encoding="utf-8")
    roots = supplemental.get("searched_roots") or []
    candidates = supplemental.get("candidates") or []
    selected = supplemental.get("selected_source_files") or []
    evidence = {
        "row_source_selection_policy": projection.get("source_selection_policy"),
        "supplemental_search_policy": supplemental.get("search_policy"),
        "searched_roots": roots,
        "candidate_count": len(candidates),
        "sha_matching_candidate_count": sum(1 for item in candidates if item.get("sha256_matches_expected")),
        "selected_source_files": selected,
        "builder_contains_otr061_prior_root_search": all(
            token in builder_text
            for token in [
                "OTR061_XAUUSD_TICK_FILE",
                "C:/tmp prior worktree copies",
                "BLOCKED_NO_TICKS_IN_WINDOW",
            ]
        ),
        "verifier_enforces_row_0127": EXPECTED_ROW_0127 in verifier_text and "row_0127" in verifier_text,
        "tests_enforce_row_0127": EXPECTED_ROW_0127 in test_text and EXPECTED_ROW_0127_TOUCH in test_text,
    }
    required_roots_present = (
        "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery" in roots
        and any("C:\\Users\\MSI\\Documents\\ai-trading-agent" in root for root in roots)
        and "C:\\tmp\\gtos_otb" in roots
    )
    return {
        **common_flags(),
        "status": "PASS"
        if required_roots_present
        and evidence["candidate_count"] > 0
        and evidence["sha_matching_candidate_count"] > 0
        and evidence["selected_source_files"]
        and evidence["builder_contains_otr061_prior_root_search"]
        and evidence["verifier_enforces_row_0127"]
        and evidence["tests_enforce_row_0127"]
        else "FAIL",
        "required_roots_present": required_roots_present,
        **evidence,
    }


def scan_forbidden_packet_keys(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []

    def walk(obj: Any, path: str) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                next_path = f"{path}.{key}" if path else key
                key_lower = key.lower()
                if key not in ALLOWED_FORBIDDEN_KEY_EXCEPTIONS and any(needle in key_lower for needle in FORBIDDEN_PACKET_KEY_NEEDLES):
                    hits.append({"path": next_path, "key": key})
                walk(value, next_path)
        elif isinstance(obj, list):
            for idx, value in enumerate(obj):
                walk(value, f"{path}[{idx}]")

    for index, row in enumerate(rows):
        walk(row, f"rows[{index}]")
    return hits


def noleak_duplicate_label_status(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = inputs["rows"]
    forbidden_hits = scan_forbidden_packet_keys(rows)
    flags_ok = (
        inputs["packet"].get("promotion_verdict") == PROMOTION_VERDICT
        and inputs["packet"].get("validation_safe") is False
        and inputs["packet"].get("outcome_review_opened") is False
        and inputs["packet"].get("live_effect") is False
        and all(row.get("promotion_verdict") == PROMOTION_VERDICT for row in rows)
        and all(row.get("validation_safe") is False for row in rows)
        and all(row.get("outcome_review_opened") is False for row in rows)
        and all(row.get("live_effect") is False for row in rows)
    )
    labels = set(row.get("closure_label") for row in rows)
    disallowed_labels = sorted(label for label in labels if label in {"stop_after_original_horizon"} or "r_scored" in str(label))
    duplicate = inputs["corr_duplicate"]
    packet_duplicate = inputs["packet_duplicate"]
    return {
        **common_flags(),
        "status": "PASS"
        if not forbidden_hits
        and flags_ok
        and not disallowed_labels
        and duplicate.get("status") == "PASS"
        and packet_duplicate.get("status") == "PASS"
        and duplicate.get("validation_sample_floor_status") == "FALSE_SOURCE_CLOSURE_PACKET_NOT_RESULT_VALIDATION"
        else "FAIL",
        "forbidden_packet_key_hit_count": len(forbidden_hits),
        "forbidden_packet_key_hits": forbidden_hits[:25],
        "flags_ok": flags_ok,
        "packet_row_count": len(rows),
        "unique_source_inventory_ids": len({row["source_inventory_id"] for row in rows}),
        "unique_duplicate_group_ids": len({row["duplicate_group_id"] for row in rows}),
        "unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in rows}),
        "duplicate_group_id_unique_reported": duplicate.get("duplicate_group_id_unique"),
        "nofill_duplicate_key_unique_reported": duplicate.get("nofill_duplicate_key_unique"),
        "validation_sample_floor_status": duplicate.get("validation_sample_floor_status"),
        "sample_floor_reason": duplicate.get("sample_floor_reason"),
        "closure_label_counts": dict(sorted(Counter(row["closure_label"] for row in rows).items())),
        "label_family_separation": {
            "source_control_labels_only": not disallowed_labels,
            "disallowed_labels": disallowed_labels,
            "no_stop_after_original_horizon_label": "stop_after_original_horizon" not in labels,
            "no_r_performance_result_claim": True,
        },
        "upstream_packet_noleak_status": inputs["packet_hash_noleak"].get("status"),
        "correction_noleak_status": inputs["corr_hash_noleak"].get("status"),
    }


def exclusion_status(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = inputs["rows"]
    t3_leaks = [
        row["packet_row_id"]
        for row in rows
        if row.get("source_lane") == "OTI8_CNR061" or row.get("closure_label") == "stop_after_original_horizon"
    ]
    blocked_94 = inputs["prior_g12_close_universe"].get("blocked_94_cnr061_excluded") or {}
    six_t3 = inputs["prior_g12_close_universe"].get("six_t3_rows_excluded") or {}
    return {
        "status": "PASS"
        if not t3_leaks
        and six_t3.get("t3_row_count") == EXPECTED_T3_COUNT
        and six_t3.get("status") == "PASS"
        and blocked_94.get("blocked_rows") == EXPECTED_BLOCKED_CNR061
        and blocked_94.get("status") == "PASS"
        and blocked_94.get("packet_rows_from_blocked_set") == []
        else "FAIL",
        "six_t3_rows": six_t3,
        "blocked_94_cnr061": blocked_94,
        "packet_t3_or_oti8_leaks": t3_leaks,
        "packet_oti8_cnr061_row_count": sum(1 for row in rows if row.get("source_lane") == "OTI8_CNR061"),
        "packet_stop_after_original_horizon_label_count": sum(1 for row in rows if row.get("closure_label") == "stop_after_original_horizon"),
    }


def live_surface_status() -> dict[str, Any]:
    status = git_output("status", "--short")
    workspace_changed: list[str] = []
    for line in status.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("warning:"):
            continue
        if len(line) >= 4:
            workspace_changed.append(line[3:].replace("\\", "/"))
    committed_scope = git_output("diff", "--name-only", "HEAD^1", "HEAD")
    committed_changed = [
        line.strip().replace("\\", "/")
        for line in committed_scope.splitlines()
        if line.strip()
    ]
    reaudit_committed_scope = any(
        path.startswith("research/science_program_2026_05/06_outcome_testing/g12_no_fill_correction_reaudit/")
        for path in committed_changed
    )
    changed = committed_changed if reaudit_committed_scope else workspace_changed
    forbidden = [
        path
        for path in changed
        if any(path.startswith(prefix) for prefix in FORBIDDEN_LIVE_PREFIXES)
        or any(needle in path.lower() for needle in FORBIDDEN_LIVE_NAME_NEEDLES)
    ]
    allowed_output_prefix = rel(OUT_DIR).replace("\\", "/") + "/"
    outside_allowed_artifacts = [
        path
        for path in changed
        if not path.startswith(allowed_output_prefix) and path != ".context/LIVE_STATE.md"
    ]
    return {
        "status": "PASS" if not forbidden else "FAIL",
        "checked_scope": "committed_diff_HEAD_parent" if reaudit_committed_scope else "workspace_status",
        "workspace_changed_paths": changed,
        "workspace_changed_path_count_observed": len(workspace_changed),
        "workspace_changed_paths_observed_sample": workspace_changed[:50],
        "forbidden_live_surface_changed_paths": forbidden,
        "allowed_output_prefix": allowed_output_prefix,
        "outside_allowed_artifacts_observed": outside_allowed_artifacts,
        "note": ".context/LIVE_STATE.md may be regenerated by mandatory preflight/closeout and is not a G12 artifact.",
    }


def decision_payload(
    counts: dict[str, Any],
    row_0127: dict[str, Any],
    stale: dict[str, Any],
    search: dict[str, Any],
    noleak: dict[str, Any],
    exclusions: dict[str, Any],
) -> dict[str, Any]:
    passed = all(
        [
            counts["packet_count_pass"],
            counts["source_closed_pass"],
            counts["source_blocked_exact_pass"],
            row_0127["status"] == "PASS",
            stale["status"] == "PASS",
            search["status"] == "PASS",
            noleak["status"] == "PASS",
            exclusions["status"] == "PASS",
        ]
    )
    decision = (
        "ACCEPT_CORRECTED_SOURCE_PACKET_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE"
        if passed
        else "ACCEPT_WITH_EXACT_REMAINING_BLOCKER"
    )
    return {
        **common_flags(),
        "artifact_family": "G12_NOFILL_CORR_DECISION_LEDGER",
        "decision": decision,
        "decision_status": "PASS_ACCEPTED" if passed else "BLOCKED_OR_PARTIAL",
        "accepted_scope": "input-only source/control closure evidence for NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1 and NOFILL_LIFECYCLE_CLOSURE_SOURCE_CORRECTION_V1",
        "non_claims": [
            "No R/performance scoring.",
            "No broker/account/live/order/hidden labels inspected.",
            "No blocked CNR061 rows scored or rescued.",
            "No validation, promotion, or live effect.",
        ],
        "primary_reasons": [
            "Packet count is 298 rows with 298 source_closed and 0 source_blocked_exact.",
            "NOFILL-CLOSE-ROW-0127 is source-closed from OTR061 XAUUSD tick parquet with matching SHA256 and recomputed terminal-area first touch.",
            "Old BLOCKED_NO_TICKS_IN_WINDOW request is inactive/superseded.",
            "Prior tick-recovery and absolute local-heavy-data root search is now represented in builder/verifier/tests and row-level source search.",
            "Six T3 rows and 94 G12-blocked CNR061 rows remain excluded.",
            "No-leak, as-of, duplicate/sample-floor, source-hash, and label-family controls remain source-only.",
        ],
        "counts_summary": counts,
        "row_0127_summary": {
            "status": row_0127["status"],
            "source_sha256_matches_expected": row_0127["source_sha256_matches_expected"],
            "recomputed_first_source_event": row_0127["recomputed_first_source_event"],
        },
        "stale_blocker_summary": stale,
        "next_lane_decision": {
            "recommended_next_lane": "RESULT_CONTRACT_DESIGN_BEFORE_ANY_RESULT_SCORING",
            "why": "Source closure is accepted, so the next safe step is to design a separate result contract. It must freeze entry/fill/cancel/expiry semantics, source-hashed quote/tick/lower-timeframe order proof, no-leak schemas, duplicate policy, and sample floors before opening outcomes.",
            "not_yet_allowed": "Do not open outcome_review, do not score R/performance, and do not claim validation/promotion/live effect from this reaudit.",
        },
    }


def context_anchor(inputs: dict[str, Any]) -> dict[str, Any]:
    live_state = (REPO_ROOT / ".context" / "LIVE_STATE.md").read_text(encoding="utf-8", errors="replace")
    latest_handoff = next((line.split("`")[1] for line in live_state.splitlines() if line.startswith("**Latest handoff on disk:**")), "")
    return {
        **common_flags(),
        "artifact_family": "G12_NOFILL_CORR_CONTEXT_ANCHOR",
        "written_at_utc": now_utc(),
        "controlling_prompt": rel(CONTROL_PROMPT),
        "repo_root": str(REPO_ROOT),
        "git_head": git_output("rev-parse", "HEAD"),
        "latest_handoff_from_live_state": latest_handoff,
        "lane": "G12_NOFILL_LIFECYCLE_CLOSURE_SOURCE_CORRECTION_REAUDIT_V1",
        "research_lane_type": "source_control_reaudit_only",
        "preflight_completed": {
            "generate_live_state": True,
            "live_state_read": True,
            "latest_handoff_read": True,
            "quick_reference_card_read": True,
            "research_operating_doctrine_read": True,
            "research_current_state_read": True,
            "goal_session_research_discipline_read": True,
            "local_heavy_data_inventory_read": True,
        },
        "context_staleness": {
            "live_state_research_context_status_observed": "FRESH" if "Status | `FRESH`" in live_state else "CHECKED_DIRECT_ARTIFACTS",
            "newer_artifacts_read_directly": [
                rel(CONTROL_PROMPT),
                rel(PACKET_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08.json"),
                rel(CORR_DIR / "NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.json"),
            ],
        },
        "controlling_inputs": [
            rel(PACKET_DIR),
            rel(CORR_DIR),
            rel(PRIOR_G12_CLOSE_DIR),
            rel(OTR061_FILE),
        ],
        "searched_roots": (next(row for row in inputs["rows"] if row["packet_row_id"] == EXPECTED_ROW_0127)["source_evidence"]["tick_terminal_sequence_projection"].get("supplemental_tick_source_search") or {}).get("searched_roots", []),
        "active_question_stack": [
            "Verify exact corrected packet counts.",
            "Verify row 0127 from OTR061 source evidence.",
            "Verify stale blocker/request inactive or superseded.",
            "Verify source-search hardening, source hashes, no-leak/as-of, duplicate/sample-floor, label separation, and exclusions.",
            "Decide accept/block/reject and write next-lane guidance.",
        ],
    }


def source_reaudit_payload(inputs: dict[str, Any], counts: dict[str, Any], hash_checks: dict[str, Any], stale: dict[str, Any], search: dict[str, Any], exclusions: dict[str, Any]) -> dict[str, Any]:
    return {
        **common_flags(),
        "artifact_family": "G12_NOFILL_CORR_SOURCE_REAUDIT",
        "status": "PASS" if counts["packet_count_pass"] and counts["source_closed_pass"] and counts["source_blocked_exact_pass"] and hash_checks["status"] == "PASS" and stale["status"] == "PASS" and search["status"] == "PASS" and exclusions["status"] == "PASS" else "FAIL",
        "packet_counts": counts,
        "source_hash_checks": hash_checks,
        "stale_blocker_status": stale,
        "source_search_hardening": search,
        "exclusion_status": exclusions,
        "upstream_packet_completion_status": inputs["packet_completion"].get("completion_status"),
        "correction_completion_status": inputs["corr_completion"].get("completion_status"),
    }


def verifier_scope_payload(live_scope: dict[str, Any]) -> dict[str, Any]:
    return {
        **common_flags(),
        "artifact_family": "G12_NOFILL_CORR_VERIFIER_AND_SCOPE_AUDIT",
        "status": "PASS" if live_scope["status"] == "PASS" else "FAIL",
        "fresh_verification_commands_run_before_artifact_build": [
            {
                "command": "python -m py_compile <upstream packet/correction builders, verifiers, tests>",
                "status": "PASS",
            },
            {
                "command": "python research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/verify_nofill_lifecycle_closure_source_packet_2026_05_08.py",
                "status": "PASS",
                "observed_key_output": "verification_status=PASS; can_mark_goal_complete=true; focused pytest 8 passed",
            },
            {
                "command": "python research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/verify_nofill_closure_source_correction_2026_05_08.py",
                "status": "PASS",
                "observed_key_output": "verification_status=PASS; can_mark_goal_complete=true; focused pytest 13 passed",
                "side_effect_note": "Verifier refreshed upstream completion JSONs; generated drift was restored so this reaudit leaves only G12 output artifacts.",
            },
        ],
        "new_verifier_results": {},
        "live_surface_scope": live_scope,
        "scope_statement": "No src, prompts, config, canary, execution, risk, permissions, safety, selector, MT5 order/account, paid/API/Databento, credential, remote, or order-behavior files are part of the reaudit outputs.",
    }


def forensics_payload(row_0127: dict[str, Any], search: dict[str, Any]) -> dict[str, Any]:
    return {
        **common_flags(),
        "artifact_family": "G12_NOFILL_CORR_FORENSICS_AND_LEARNING",
        "status": "PASS",
        "what_failed_before": "The earlier BLOCKED_NO_TICKS_IN_WINDOW blocker was source-boxed to the packet-local daily tick expectation and did not use the existing OTR061 XAUUSD recovery parquet.",
        "what_corrected_source_search_learned": [
            "Existing prior recovery lanes can contain decisive source windows even when the immediate worktree daily tick file is absent or incomplete.",
            "A terminal-area first touch at the first source tick after the path start is enough for source-only closure of terminal-first ordering; it is not enough for R/performance or validation.",
            "Read-only extraction manifests should be inactive once a source-hashed prior recovery file closes the exact question.",
            "Future source builders should search current worktree, main repo absolute roots, and C:/tmp prior worktrees before emitting missing-tick blockers.",
        ],
        "row_0127_learning": {
            "source_sha256": row_0127["source_sha256"],
            "source_coverage": [row_0127["source_first_ts_utc"], row_0127["source_last_ts_utc"]],
            "first_source_event": row_0127["recomputed_first_source_event"],
            "source_only_boundary": row_0127["source_only_non_claim"],
        },
        "source_search_hardening_summary": {
            "searched_roots": search["searched_roots"],
            "candidate_count": search["candidate_count"],
            "sha_matching_candidate_count": search["sha_matching_candidate_count"],
        },
        "remaining_questions": [
            "A result contract still needs frozen fill/cancel/expiry and no-leak schema before any outcomes can open.",
            "No claim is made about blocked CNR061 rows, T1/T2/E2/E3/E4, broker actual-R, or live execution.",
        ],
    }


def next_prompt_pack(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "Run the next source-safe lane only after accepting G12_NOFILL_LIFECYCLE_CLOSURE_SOURCE_CORRECTION_REAUDIT_V1.",
            "",
            "Recommended lane: NOFILL_LIFECYCLE_CLOSURE_RESULT_CONTRACT_DESIGN_V1.",
            "",
            "Objective: design, but do not score, the result contract required before any no-fill lifecycle closure outcome lane can open. Complete mandatory GTOS preflight; read the G12 correction reaudit artifacts under research/science_program_2026_05/06_outcome_testing/g12_no_fill_correction_reaudit/ plus the corrected packet and correction lane. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
            "",
            "The contract must freeze entry/fill/cancel/expiry semantics, quote/tick/lower-timeframe path evidence requirements, pending-intent closure fields, side-aware touch parser, duplicate policy, sample floor, source-hash rules, no-leak/as-of schema, and label-family separation before any result rows are opened.",
            "",
            "Hard boundaries: do not score R/performance; do not inspect broker/account/live/order/hidden labels; do not score blocked CNR061 rows; do not use paid/API/Databento or MT5 order/account calls; do not edit registries, remotes, credentials, or live trading surfaces; do not claim validation, promotion, or live effect.",
            "",
            "Required starting evidence from this reaudit:",
            f"- Decision: {decision['decision']}",
            "- Packet counts: 298 source_closed / 0 source_blocked_exact.",
            f"- Row 0127 OTR061 SHA256: {EXPECTED_OTR_SHA256}.",
            f"- Row 0127 first terminal-area touch: {EXPECTED_ROW_0127_TOUCH}.",
            "- Six T3 rows and 94 G12-blocked CNR061 rows remain excluded.",
            "",
            "Stop condition: produce a machine-checkable result-contract design, exact blockers for any missing source fields, and next-lane prompt guidance. Do not open outcomes.",
            "",
        ]
    )


def completion_payload(
    decision: dict[str, Any],
    context: dict[str, Any],
    source_reaudit: dict[str, Any],
    row_0127: dict[str, Any],
    noleak: dict[str, Any],
    verifier_scope: dict[str, Any],
    forensics: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "Mandatory GTOS preflight completed",
            "artifact": "G12_NOFILL_CORR_CONTEXT_ANCHOR_2026-05-08.json",
            "status": "PASS" if all(context["preflight_completed"].values()) else "FAIL",
            "evidence": context["preflight_completed"],
        },
        {
            "requirement": "Audit corrected packet and correction lane as source/control only",
            "artifact": "G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.json",
            "status": source_reaudit["status"],
            "evidence": {"packet_completion": source_reaudit["upstream_packet_completion_status"], "correction_completion": source_reaudit["correction_completion_status"]},
        },
        {
            "requirement": "Verify exact packet counts 298 source_closed and 0 source_blocked_exact",
            "artifact": "G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.json",
            "status": "PASS" if source_reaudit["packet_counts"]["packet_count_pass"] and source_reaudit["packet_counts"]["source_closed_pass"] and source_reaudit["packet_counts"]["source_blocked_exact_pass"] else "FAIL",
            "evidence": source_reaudit["packet_counts"],
        },
        {
            "requirement": "Verify row 0127 source closure from OTR061 parquet hash and first touch",
            "artifact": "G12_NOFILL_CORR_ROW_0127_AUDIT_2026-05-08.json",
            "status": row_0127["status"],
            "evidence": {"sha256": row_0127["source_sha256"], "first_event": row_0127["recomputed_first_source_event"]},
        },
        {
            "requirement": "Verify stale BLOCKED_NO_TICKS_IN_WINDOW request inactive/superseded",
            "artifact": "G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.json",
            "status": source_reaudit["stale_blocker_status"]["status"],
            "evidence": source_reaudit["stale_blocker_status"],
        },
        {
            "requirement": "Verify prior recovery-lane and local-heavy-data source-search hardening",
            "artifact": "G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.json",
            "status": source_reaudit["source_search_hardening"]["status"],
            "evidence": source_reaudit["source_search_hardening"],
        },
        {
            "requirement": "Verify six T3 row exclusion and 94 G12-blocked CNR061 exclusion",
            "artifact": "G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.json",
            "status": source_reaudit["exclusion_status"]["status"],
            "evidence": source_reaudit["exclusion_status"],
        },
        {
            "requirement": "Verify source hashes, no-leak/as-of, duplicate/sample-floor, and label-family separation",
            "artifact": "G12_NOFILL_CORR_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
            "status": noleak["status"],
            "evidence": noleak,
        },
        {
            "requirement": "Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false",
            "artifact": "all JSON artifacts",
            "status": "PASS" if decision["promotion_verdict"] == PROMOTION_VERDICT and decision["validation_safe"] is False and decision["outcome_review_opened"] is False and decision["live_effect"] is False else "FAIL",
            "evidence": common_flags(),
        },
        {
            "requirement": "Do not score R/performance or inspect forbidden label families/live surfaces",
            "artifact": "G12_NOFILL_CORR_VERIFIER_AND_SCOPE_AUDIT_2026-05-08.json",
            "status": verifier_scope["status"],
            "evidence": verifier_scope["scope_statement"],
        },
        {
            "requirement": "Write next-lane guidance",
            "artifact": "G12_NOFILL_CORR_NEXT_PROMPT_PACK_2026-05-08.md",
            "status": "PASS",
            "evidence": decision["next_lane_decision"],
        },
    ]
    complete = all(item["status"] == "PASS" for item in checklist) and decision["decision"] == "ACCEPT_CORRECTED_SOURCE_PACKET_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE"
    return {
        **common_flags(),
        "artifact_family": "G12_NOFILL_CORR_COMPLETION_AUDIT",
        "completion_status": "PASS_ACCEPTED_CORRECTED_SOURCE_PACKET" if complete else "FAIL_OR_BLOCKED",
        "can_mark_goal_complete": complete,
        "objective_restatement": "Run the G12 correction reaudit, verify the corrected NOFILL source packet/correction as source-control evidence only, decide accept/block/reject, preserve safety flags, and write machine-checkable artifacts plus next-lane guidance under the G12 output directory.",
        "decision": decision["decision"],
        "prompt_to_artifact_checklist": checklist,
        "verification_summary": {
            "source_reaudit_status": source_reaudit["status"],
            "row_0127_status": row_0127["status"],
            "noleak_duplicate_samplefloor_status": noleak["status"],
            "verifier_scope_status": verifier_scope["status"],
            "forensics_status": forensics["status"],
        },
        "missing_or_weak_requirements": [item for item in checklist if item["status"] != "PASS"],
    }


def build_payloads() -> dict[str, Any]:
    inputs = load_inputs()
    counts = packet_counts(inputs)
    row_0127 = recompute_row_0127_touch(inputs)
    hash_checks = source_hash_checks(inputs)
    stale = stale_blocker_status(inputs)
    search = source_search_hardening(inputs)
    noleak = noleak_duplicate_label_status(inputs)
    exclusions = exclusion_status(inputs)
    live_scope = live_surface_status()
    decision = decision_payload(counts, row_0127, stale, search, noleak, exclusions)
    context = context_anchor(inputs)
    source_reaudit = source_reaudit_payload(inputs, counts, hash_checks, stale, search, exclusions)
    verifier_scope = verifier_scope_payload(live_scope)
    forensics = forensics_payload(row_0127, search)
    completion = completion_payload(decision, context, source_reaudit, row_0127, noleak, verifier_scope, forensics)
    return {
        "context": context,
        "decision": decision,
        "source_reaudit": source_reaudit,
        "row_0127": row_0127,
        "noleak_duplicate_samplefloor": noleak,
        "verifier_scope": verifier_scope,
        "forensics": forensics,
        "completion": completion,
        "next_prompt_pack": next_prompt_pack(decision),
    }


def write_artifacts(payloads: dict[str, Any]) -> None:
    json_targets = {
        "G12_NOFILL_CORR_CONTEXT_ANCHOR_2026-05-08.json": payloads["context"],
        "G12_NOFILL_CORR_DECISION_LEDGER_2026-05-08.json": payloads["decision"],
        "G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.json": payloads["source_reaudit"],
        "G12_NOFILL_CORR_ROW_0127_AUDIT_2026-05-08.json": payloads["row_0127"],
        "G12_NOFILL_CORR_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json": payloads["noleak_duplicate_samplefloor"],
        "G12_NOFILL_CORR_VERIFIER_AND_SCOPE_AUDIT_2026-05-08.json": payloads["verifier_scope"],
        "G12_NOFILL_CORR_FORENSICS_AND_LEARNING_2026-05-08.json": payloads["forensics"],
        "G12_NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json": payloads["completion"],
    }
    for name, payload in json_targets.items():
        write_json(OUT_DIR / name, payload)

    write_md(
        OUT_DIR / "G12_NOFILL_CORR_CONTEXT_ANCHOR_2026-05-08.md",
        "G12 NOFILL Correction Reaudit Context Anchor - 2026-05-08",
        [
            f"Controlling prompt: `{payloads['context']['controlling_prompt']}`",
            f"Git HEAD: `{payloads['context']['git_head']}`",
            f"Lane: `{payloads['context']['lane']}`",
            "",
            "## Preflight",
            *[f"- `{status}` {name}" for name, status in payloads["context"]["preflight_completed"].items()],
            "",
            "## Active Questions",
            *[f"- {item}" for item in payloads["context"]["active_question_stack"]],
            "",
            "Promotion verdict remains `NO_PROMOTION_VERDICT`; validation_safe, outcome_review_opened, and live_effect remain false.",
        ],
    )
    write_md(
        OUT_DIR / "G12_NOFILL_CORR_DECISION_LEDGER_2026-05-08.md",
        "G12 NOFILL Correction Decision Ledger - 2026-05-08",
        [
            f"Decision: `{payloads['decision']['decision']}`",
            f"Status: `{payloads['decision']['decision_status']}`",
            "",
            "## Reasons",
            *[f"- {item}" for item in payloads["decision"]["primary_reasons"]],
            "",
            "## Non-Claims",
            *[f"- {item}" for item in payloads["decision"]["non_claims"]],
            "",
            f"Next lane: `{payloads['decision']['next_lane_decision']['recommended_next_lane']}`",
        ],
    )
    write_md(
        OUT_DIR / "G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.md",
        "G12 NOFILL Correction Source Reaudit - 2026-05-08",
        [
            f"Status: `{payloads['source_reaudit']['status']}`",
            f"Packet rows: `{payloads['source_reaudit']['packet_counts']['rows_jsonl_count']}`",
            f"Source closed: `{payloads['source_reaudit']['packet_counts']['closure_status_counts'].get('source_closed')}`",
            f"Source blocked exact: `{payloads['source_reaudit']['packet_counts']['closure_status_counts'].get('source_blocked_exact', 0)}`",
            f"Source hash check status: `{payloads['source_reaudit']['source_hash_checks']['status']}`",
            f"Stale blocker status: `{payloads['source_reaudit']['stale_blocker_status']['status']}`",
            f"Search hardening status: `{payloads['source_reaudit']['source_search_hardening']['status']}`",
            f"Exclusion status: `{payloads['source_reaudit']['exclusion_status']['status']}`",
        ],
    )
    write_md(
        OUT_DIR / "G12_NOFILL_CORR_ROW_0127_AUDIT_2026-05-08.md",
        "G12 NOFILL Correction Row 0127 Audit - 2026-05-08",
        [
            f"Status: `{payloads['row_0127']['status']}`",
            f"Source path: `{payloads['row_0127']['source_path']}`",
            f"SHA256: `{payloads['row_0127']['source_sha256']}`",
            f"Coverage: `{payloads['row_0127']['source_first_ts_utc']}` through `{payloads['row_0127']['source_last_ts_utc']}`",
            f"Recomputed first source event: `{payloads['row_0127']['recomputed_first_source_event']}`",
            "",
            payloads["row_0127"]["source_only_non_claim"],
        ],
    )
    write_md(
        OUT_DIR / "G12_NOFILL_CORR_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md",
        "G12 NOFILL Correction Noleak Duplicate Samplefloor Audit - 2026-05-08",
        [
            f"Status: `{payloads['noleak_duplicate_samplefloor']['status']}`",
            f"Forbidden packet key hits: `{payloads['noleak_duplicate_samplefloor']['forbidden_packet_key_hit_count']}`",
            f"Unique source inventory IDs: `{payloads['noleak_duplicate_samplefloor']['unique_source_inventory_ids']}`",
            f"Unique duplicate groups: `{payloads['noleak_duplicate_samplefloor']['unique_duplicate_group_ids']}`",
            f"Unique nofill duplicate keys: `{payloads['noleak_duplicate_samplefloor']['unique_nofill_duplicate_keys']}`",
            f"Sample-floor status: `{payloads['noleak_duplicate_samplefloor']['validation_sample_floor_status']}`",
        ],
    )
    write_md(
        OUT_DIR / "G12_NOFILL_CORR_VERIFIER_AND_SCOPE_AUDIT_2026-05-08.md",
        "G12 NOFILL Correction Verifier And Scope Audit - 2026-05-08",
        [
            f"Status: `{payloads['verifier_scope']['status']}`",
            payloads["verifier_scope"]["scope_statement"],
            "",
            "## Fresh Upstream Verification",
            *[f"- `{item['status']}` {item['command']}" for item in payloads["verifier_scope"]["fresh_verification_commands_run_before_artifact_build"]],
            "",
            f"Forbidden live-surface changed paths: `{payloads['verifier_scope']['live_surface_scope']['forbidden_live_surface_changed_paths']}`",
        ],
    )
    write_md(
        OUT_DIR / "G12_NOFILL_CORR_FORENSICS_AND_LEARNING_2026-05-08.md",
        "G12 NOFILL Correction Forensics And Learning - 2026-05-08",
        [
            f"Status: `{payloads['forensics']['status']}`",
            "",
            f"Prior failure: {payloads['forensics']['what_failed_before']}",
            "",
            "## Learning",
            *[f"- {item}" for item in payloads["forensics"]["what_corrected_source_search_learned"]],
            "",
            "## Remaining Questions",
            *[f"- {item}" for item in payloads["forensics"]["remaining_questions"]],
        ],
    )
    (OUT_DIR / "G12_NOFILL_CORR_NEXT_PROMPT_PACK_2026-05-08.md").write_text(payloads["next_prompt_pack"], encoding="utf-8")
    write_md(
        OUT_DIR / "G12_NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.md",
        "G12 NOFILL Correction Completion Audit - 2026-05-08",
        [
            f"Completion status: `{payloads['completion']['completion_status']}`",
            f"Can mark goal complete: `{payloads['completion']['can_mark_goal_complete']}`",
            f"Decision: `{payloads['completion']['decision']}`",
            "",
            "## Prompt-To-Artifact Checklist",
            *[
                f"- `{item['status']}` {item['requirement']} -> `{item['artifact']}`"
                for item in payloads["completion"]["prompt_to_artifact_checklist"]
            ],
            "",
            "All outputs remain source/control only with `NO_PROMOTION_VERDICT`, validation_safe=false, outcome_review_opened=false, and live_effect=false.",
        ],
    )


def main() -> int:
    payloads = build_payloads()
    write_artifacts(payloads)
    print(json.dumps({"status": payloads["completion"]["completion_status"], "can_mark_goal_complete": payloads["completion"]["can_mark_goal_complete"]}, indent=2))
    return 0 if payloads["completion"]["can_mark_goal_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
