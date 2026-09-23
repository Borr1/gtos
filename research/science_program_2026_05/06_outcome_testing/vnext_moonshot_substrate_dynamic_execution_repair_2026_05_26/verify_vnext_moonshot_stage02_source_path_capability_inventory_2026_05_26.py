from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"

CAPABILITY = ROUTE_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_LEDGER_{DATE_ID}.jsonl"
SEARCH = ROUTE_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_SEARCH_LEDGER_{DATE_ID}.jsonl"
SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_{DATE_ID}.json"
FORWARD = ROUTE_DIR / f"VNEXT_MOONSHOT_FORWARD_CAPTURE_REQUIREMENTS_{DATE_ID}.jsonl"
STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"
VERIFY_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE02_VERIFICATION_RESULT_{DATE_ID}.json"

REQUIRED_SOURCE_FAMILIES = {
    "ohlc_bars",
    "tick_parquet",
    "sierra_source",
    "shadow_log",
    "trade_record",
    "news_calendar",
    "route_artifact",
}

REQUIRED_ROOTS = {
    "repo_data",
    "repo_ticks",
    "repo_shadow_logs",
    "repo_exports",
    "repo_trade_records",
    "repo_pipeline_state",
    "repo_route_moonshot",
    "repo_route_activation_anatomy",
    "repo_route_repaired_candidate",
    "repo_route_full_replay",
    "absolute_tmp",
    "absolute_sierrachart",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> None:
    failures = []
    capability_rows = load_jsonl(CAPABILITY) if CAPABILITY.exists() else []
    search_rows = load_jsonl(SEARCH) if SEARCH.exists() else []
    forward_rows = load_jsonl(FORWARD) if FORWARD.exists() else []
    summary = json.loads(SUMMARY.read_text(encoding="utf-8")) if SUMMARY.exists() else {}
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}

    source_families = Counter(row.get("source_family") for row in capability_rows)
    roots = Counter(row.get("root_id") for row in search_rows)
    dynamic_usable = sum(1 for row in capability_rows if row.get("dynamic_execution_usable") is True)
    hashed = sum(1 for row in capability_rows if row.get("sha256_status") == "computed")
    missing_families = sorted(REQUIRED_SOURCE_FAMILIES - set(source_families))
    missing_roots = sorted(REQUIRED_ROOTS - set(roots))
    if missing_families:
        failures.append(f"missing source families: {missing_families}")
    if missing_roots:
        failures.append(f"missing searched roots: {missing_roots}")
    if len(capability_rows) < 100:
        failures.append(f"capability ledger too small: {len(capability_rows)}")
    if len(search_rows) != len(REQUIRED_ROOTS):
        failures.append(f"search ledger row count mismatch: {len(search_rows)}")
    if len(forward_rows) < 20:
        failures.append(f"forward capture requirements too small: {len(forward_rows)}")
    if dynamic_usable <= 0:
        failures.append("no dynamic execution usable sources found")
    if hashed <= 0:
        failures.append("no source files hashed")
    if summary.get("source_capability_rows") != len(capability_rows):
        failures.append("summary source_capability_rows mismatch")
    if summary.get("search_rows") != len(search_rows):
        failures.append("summary search_rows mismatch")
    if summary.get("forward_capture_requirement_rows") != len(forward_rows):
        failures.append("summary forward_capture_requirement_rows mismatch")
    if summary.get("forbidden_boundaries_crossed"):
        failures.append("summary says forbidden boundaries crossed")
    if state.get("first_incomplete_invariant") != "STAGE_03_DYNAMIC_EXECUTION_POLICY_ENGINE":
        failures.append("state did not advance first incomplete invariant to Stage03")
    if state.get("source_gap_ledger_path") is None:
        failures.append("state missing source_gap_ledger_path")

    result = {
        "checked_at_utc": utc_now(),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "source_capability_rows": len(capability_rows),
        "search_rows": len(search_rows),
        "forward_capture_requirement_rows": len(forward_rows),
        "source_family_counts": dict(sorted(source_families.items())),
        "searched_root_counts": dict(sorted(roots.items())),
        "dynamic_execution_usable_rows": dynamic_usable,
        "hashed_source_rows": hashed,
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
