from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_broader_origin_ohlc_context_replay_verifier"
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent

LEDGER_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_CONTRACT_LEDGER_{DATE}.jsonl"
)
SUMMARY_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_REPLAY_SUMMARY_{DATE}.json"
)
PATHS_READ_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_PATHS_READ_{DATE}.json"
)
OUTPUT_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_VERIFICATION_RESULT_{DATE}.json"
)

TARGET_FAMILIES = {
    "liquidity_sweep_reclaim",
    "displacement_continuation",
    "volatility_compression_expansion",
    "session_open_range_break",
    "regime_transition_break",
    "news_volatility_reprice",
    "cross_asset_lead_lag",
    "structural_distance_extreme",
    "continuation_no_retrace",
}
REQUIRED_READ_ROLES = {
    "existing_stage02_builder",
    "existing_stage04_builder",
    "stage05_shard_manifest",
    "stage10_market_awareness_feature_ledger",
    "stage10_ml_feature_ledger",
    "stage10_router_replay_ledger",
    "source_capability_ledger",
    "origin_registry",
}
BROAD_AVAILABLE_TOKENS = {
    "available",
    "broad_available",
    "available_without_rows",
    "source_available_only",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def fnum(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def main() -> None:
    failures: list[str] = []
    warnings: list[str] = []

    if not LEDGER_PATH.exists():
        failures.append(f"missing_ledger:{rel(LEDGER_PATH)}")
        ledger_rows: list[dict[str, Any]] = []
    else:
        ledger_rows = list(iter_jsonl(LEDGER_PATH))
    if not SUMMARY_PATH.exists():
        failures.append(f"missing_summary:{rel(SUMMARY_PATH)}")
        summary: dict[str, Any] = {}
    else:
        summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    if not PATHS_READ_PATH.exists():
        failures.append(f"missing_paths_read:{rel(PATHS_READ_PATH)}")
        paths_read: dict[str, Any] = {}
    else:
        paths_read = json.loads(PATHS_READ_PATH.read_text(encoding="utf-8"))

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    row_type_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    activation_ready_rows = 0
    prototype_replay_rows = 0
    for row in ledger_rows:
        family = str(row.get("origin_family"))
        by_family[family].append(row)
        row_type_counts[str(row.get("row_type"))] += 1
        blocker_counts[str(row.get("activation_ready_blocker_class"))] += 1
        if row.get("activation_ready"):
            activation_ready_rows += 1
            if not row.get("origin_native_dynamic_replay_exists"):
                failures.append(f"activation_ready_without_origin_native_dynamic_replay:{row.get('row_id')}")
            if fnum(row.get("origin_native_dynamic_final_r")) is None:
                failures.append(f"activation_ready_without_origin_native_dynamic_final_r:{row.get('row_id')}")
            dynamic = row.get("origin_native_dynamic_policy_replay") or {}
            if dynamic.get("selected_policy_same_bar_ambiguity") is True:
                failures.append(f"activation_ready_with_selected_policy_same_bar_ambiguity:{row.get('row_id')}")
        generation_status = str(row.get("generation_status"))
        if generation_status in BROAD_AVAILABLE_TOKENS:
            failures.append(f"broad_available_generation_status:{family}:{row.get('row_id')}")
        if row.get("row_type") == "candidate_contract":
            required = ("decision_time_utc", "symbol", "side", "entry_price", "source_path", "source_sha256")
            missing = [field for field in required if row.get(field) in (None, "")]
            if missing:
                failures.append(f"candidate_contract_missing_fields:{row.get('row_id')}:{','.join(missing)}")
            if row.get("prototype_fixed_r_replay_exists"):
                prototype_replay_rows += 1
            if (
                not row.get("activation_ready")
                and not row.get("exact_blocker_required_for_activation", {}).get("blocker_class")
            ):
                failures.append(f"candidate_contract_missing_exact_activation_blocker:{row.get('row_id')}")
        elif row.get("row_type") == "family_blocker":
            if not row.get("activation_ready_blocker_class") or not row.get("activation_ready_blocker_detail"):
                failures.append(f"family_blocker_without_exact_blocker:{family}:{row.get('row_id')}")

    missing_families = TARGET_FAMILIES - set(by_family)
    if missing_families:
        failures.append("missing_required_origin_families:" + ",".join(sorted(missing_families)))
    extra_families = set(by_family) - TARGET_FAMILIES
    if extra_families:
        warnings.append("extra_origin_families_present:" + ",".join(sorted(extra_families)))

    family_status: dict[str, dict[str, Any]] = {}
    for family in sorted(TARGET_FAMILIES):
        rows = by_family.get(family, [])
        candidate_rows = [row for row in rows if row.get("row_type") == "candidate_contract"]
        blocker_rows = [row for row in rows if row.get("row_type") == "family_blocker"]
        if not candidate_rows and not blocker_rows:
            failures.append(f"family_without_executable_rows_or_exact_blocker:{family}")
        if not candidate_rows and any(str(row.get("generation_status")) in BROAD_AVAILABLE_TOKENS for row in rows):
            failures.append(f"family_left_as_broad_available_without_rows:{family}")
        family_status[family] = {
            "rows": len(rows),
            "candidate_contract_rows": len(candidate_rows),
            "family_blocker_rows": len(blocker_rows),
            "prototype_replay_rows": sum(1 for row in rows if row.get("prototype_fixed_r_replay_exists")),
            "activation_ready_rows": sum(1 for row in rows if row.get("activation_ready")),
            "origin_native_dynamic_replay_rows": sum(
                1 for row in rows if row.get("origin_native_dynamic_replay_exists")
            ),
            "blocker_classes": dict(Counter(str(row.get("activation_ready_blocker_class")) for row in rows)),
        }

    summary_counts = summary.get("row_counts") or {}
    if summary_counts.get("ledger_rows") != len(ledger_rows):
        failures.append(
            f"summary_ledger_row_mismatch:{summary_counts.get('ledger_rows')}!={len(ledger_rows)}"
        )
    if summary_counts.get("activation_ready_rows") != activation_ready_rows:
        failures.append(
            "summary_activation_ready_row_mismatch:"
            f"{summary_counts.get('activation_ready_rows')}!={activation_ready_rows}"
        )
    summary_dynamic_rows = summary_counts.get("origin_native_dynamic_replay_rows")
    if summary_dynamic_rows is not None:
        actual_dynamic_rows = sum(
            1 for row in ledger_rows if row.get("origin_native_dynamic_replay_exists")
        )
        if summary_dynamic_rows != actual_dynamic_rows:
            failures.append(
                "summary_origin_native_dynamic_row_mismatch:"
                f"{summary_dynamic_rows}!={actual_dynamic_rows}"
            )

    read_roles = {str(row.get("read_role")) for row in paths_read.get("paths_read", [])}
    missing_roles = REQUIRED_READ_ROLES - read_roles
    if missing_roles:
        failures.append("missing_required_read_roles:" + ",".join(sorted(missing_roles)))

    result = {
        "schema_version": "vnext_replacement_stage13_broader_origin_verification_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": utc_now(),
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "warnings": warnings,
        "checked_files": {
            "ledger": rel(LEDGER_PATH),
            "summary": rel(SUMMARY_PATH),
            "paths_read": rel(PATHS_READ_PATH),
        },
        "ledger_rows": len(ledger_rows),
        "row_type_counts": dict(row_type_counts),
        "activation_ready_rows": activation_ready_rows,
        "prototype_replay_rows": prototype_replay_rows,
        "blocker_counts": dict(blocker_counts),
        "family_status": family_status,
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
