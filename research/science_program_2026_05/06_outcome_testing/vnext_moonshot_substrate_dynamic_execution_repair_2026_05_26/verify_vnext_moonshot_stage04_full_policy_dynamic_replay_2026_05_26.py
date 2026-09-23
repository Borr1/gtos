from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"

SHARD_INDEX = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SHARD_INDEX_{DATE_ID}.jsonl"
SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SUMMARY_{DATE_ID}.json"
REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_REPORT_{DATE_ID}.md"
STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"
VERIFY_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_VERIFICATION_RESULT_{DATE_ID}.json"

REQUIRED_POLICIES = {
    "legacy_fixed_1.5r",
    "ai_target",
    "live_current_j46_j49",
    "partial_be_runner",
    "be_after_trigger",
    "trailing_runner",
    "time_stop_only",
    "early_cut_if_no_progress",
    "path_aware_runner",
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


def count_output_rows(index_rows: list[dict]) -> tuple[int, Counter]:
    total = 0
    policy_presence = Counter()
    for index_row in index_rows:
        output_path = ROUTE_DIR.parents[4] / index_row["output_chunk_path"]
        # The path above is awkward for absolute execution; fall back to cwd-relative.
        if not output_path.exists():
            output_path = Path(index_row["output_chunk_path"])
        with output_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                total += 1
                policy_presence.update(row.get("policy_results", {}).keys())
    return total, policy_presence


def main() -> None:
    failures = []
    index_rows = load_jsonl(SHARD_INDEX) if SHARD_INDEX.exists() else []
    summary = json.loads(SUMMARY.read_text(encoding="utf-8")) if SUMMARY.exists() else {}
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    output_rows, policy_presence = count_output_rows(index_rows)
    replayable_from_index = sum(row.get("replayable_candidate_rows", 0) for row in index_rows)
    policies_in_summary = set(summary.get("policy_names", []))

    if len(index_rows) != summary.get("input_stage04_shards"):
        failures.append("summary input_stage04_shards mismatch")
    if output_rows != replayable_from_index:
        failures.append(f"output row count mismatch: {output_rows} != {replayable_from_index}")
    if output_rows != summary.get("replayable_candidate_rows"):
        failures.append("summary replayable candidate count mismatch")
    missing_policies = sorted(REQUIRED_POLICIES - policies_in_summary)
    if missing_policies:
        failures.append(f"missing policies in summary: {missing_policies}")
    for policy in REQUIRED_POLICIES:
        if policy_presence[policy] != output_rows:
            failures.append(f"policy {policy} missing from some output rows: {policy_presence[policy]} of {output_rows}")
    if summary.get("forbidden_boundaries_crossed"):
        failures.append("summary says forbidden boundaries crossed")
    if state.get("first_incomplete_invariant") != "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER":
        failures.append("state did not advance to Stage05")
    if not REPORT.exists() or REPORT.stat().st_size < 500:
        failures.append("Stage04 report missing or too small")

    result = {
        "checked_at_utc": utc_now(),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "index_shards": len(index_rows),
        "output_rows": output_rows,
        "policy_presence": dict(sorted(policy_presence.items())),
        "replayable_candidates": summary.get("replayable_candidate_rows"),
        "policy_expectancy_r": summary.get("policy_expectancy_r"),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
