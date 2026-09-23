from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"

LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_STATIC_PRIMITIVE_ASSUMPTION_LEDGER_{DATE_ID}.jsonl"
SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_STATIC_PRIMITIVE_ASSUMPTION_SUMMARY_{DATE_ID}.json"
REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_STATIC_PRIMITIVE_ASSUMPTION_REPORT_{DATE_ID}.md"
STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"
VERIFY_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE01_VERIFICATION_RESULT_{DATE_ID}.json"

REQUIRED_FAMILIES = {
    "fixed_bracket_or_proxy_r",
    "candidate_origin_boxing",
    "shadow_disabled_or_stale",
    "source_proxy_or_gap",
    "dynamic_execution_gap",
    "verifier_completion_semantics",
    "ai_ml_label_dependency",
    "prop_governor_static_path",
}

REQUIRED_BUCKETS = {
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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_number"] = line_number
            rows.append(row)
    return rows


def main() -> None:
    failures = []
    if not LEDGER.exists():
        failures.append(f"missing ledger {LEDGER}")
        rows = []
    else:
        rows = load_jsonl(LEDGER)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8")) if SUMMARY.exists() else {}
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}

    family_counts = Counter(row.get("assumption_family") for row in rows)
    bucket_counts = Counter(row.get("source_bucket") for row in rows)
    action_counts = Counter(row.get("exact_action") for row in rows)
    source_kind_counts = Counter(row.get("source_kind") for row in rows)

    missing_families = sorted(REQUIRED_FAMILIES - set(family_counts))
    missing_buckets = sorted(REQUIRED_BUCKETS - set(bucket_counts))
    if missing_families:
        failures.append(f"missing required assumption families: {missing_families}")
    if missing_buckets:
        failures.append(f"missing required source buckets: {missing_buckets}")
    if len(rows) < 50:
        failures.append(f"ledger too small for Stage01 coverage: {len(rows)} rows")
    if summary.get("row_count") != len(rows):
        failures.append(f"summary row_count mismatch: {summary.get('row_count')} != {len(rows)}")
    if not summary.get("no_arbitrary_top_n"):
        failures.append("summary no_arbitrary_top_n is not true")
    if summary.get("lossy_sampling_used"):
        failures.append("lossy sampling was used")
    if summary.get("first_incomplete_invariant_after_stage01") != "STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY":
        failures.append("Stage01 did not advance first incomplete invariant to Stage02")
    if not REPORT.exists() or REPORT.stat().st_size < 500:
        failures.append("Stage01 report missing or too small")
    if state.get("static_proxy_assumption_ledger_path") is None:
        failures.append("session state does not point to static assumption ledger")
    if state.get("first_incomplete_invariant") != "STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY":
        failures.append("session state first incomplete invariant is not Stage02")
    if "large_row_ledger_deferred" not in source_kind_counts:
        failures.append("large row ledger preservation/deferred scan record missing")
    if "replay_under_dynamic_execution_policy" not in action_counts:
        failures.append("dynamic replay action missing from Stage01 ledger")
    if "semantic_verifier_hardening" not in action_counts:
        failures.append("semantic verifier hardening action missing from Stage01 ledger")

    result = {
        "checked_at_utc": utc_now(),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "row_count": len(rows),
        "assumption_family_counts": dict(sorted(family_counts.items())),
        "source_bucket_counts": dict(sorted(bucket_counts.items())),
        "source_kind_counts": dict(sorted(source_kind_counts.items())),
        "exact_action_counts": dict(sorted(action_counts.items())),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
        "no_arbitrary_top_n": summary.get("no_arbitrary_top_n"),
        "lossy_sampling_used": summary.get("lossy_sampling_used"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
