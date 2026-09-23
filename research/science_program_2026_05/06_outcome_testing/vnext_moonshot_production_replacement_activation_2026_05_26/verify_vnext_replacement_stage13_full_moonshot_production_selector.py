from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_full_moonshot_production_selector_verifier"
EXPLICIT_24H_SESSION_SYMBOLS = {"BTCUSD", "ETHUSD"}
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent

SUMMARY_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_{DATE}.json"
LEDGER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_LEDGER_{DATE}.jsonl"
ALLOWLIST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_{DATE}.json"
OUTSIDE_SESSION_SUMMARY_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_SUMMARY_{DATE}.json"
OUTPUT_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_VERIFIER_{DATE}.json"
REQUIRED_OUTSIDE_ROW_FIELDS = {
    "candidate_id",
    "symbol",
    "origin_family",
    "side",
    "raw_session",
    "utc_hour_bucket",
    "source_mode",
    "candidate_origin",
    "r_multiple",
    "current_exclusion_reason",
    "repaired_disposition",
    "repaired_proof_class",
    "final_action",
    "proof_class",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_jsonl_gz(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metric_ok(metrics: dict[str, Any]) -> bool:
    exp = metrics.get("expectancy_r")
    pf = metrics.get("profit_factor")
    rows = int(metrics.get("performance_rows") or 0)
    return rows > 0 and exp is not None and exp > 0 and (pf is None or pf > 1)


def main() -> None:
    failures: list[str] = []
    warnings: list[str] = []
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8")) if SUMMARY_PATH.exists() else {}
    ledger_rows = list(iter_jsonl(LEDGER_PATH)) if LEDGER_PATH.exists() else []
    allowlist = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8")) if ALLOWLIST_PATH.exists() else {}
    outside_summary = json.loads(OUTSIDE_SESSION_SUMMARY_PATH.read_text(encoding="utf-8")) if OUTSIDE_SESSION_SUMMARY_PATH.exists() else {}
    outside_manifest_path = ROUTE_DIR / Path(
        ((outside_summary.get("output_paths") or {}).get("row_shard_manifest"))
        or f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_SHARD_MANIFEST_{DATE}.jsonl"
    ).name

    if not summary:
        failures.append(f"missing_summary:{rel(SUMMARY_PATH)}")
    if not ledger_rows:
        failures.append(f"missing_selector_ledger:{rel(LEDGER_PATH)}")
    entries = allowlist.get("entries") if isinstance(allowlist, dict) else None
    if not isinstance(entries, list) or not entries:
        failures.append(f"missing_broader_origin_allowlist_entries:{rel(ALLOWLIST_PATH)}")
        entries = []

    old_rows = int(summary.get("old_three_selected_rows") or 0)
    broader_rows = int(summary.get("broader_origin_selected_rows") or 0)
    combined_rows = int(summary.get("combined_selected_rows") or 0)
    if old_rows != 60748:
        failures.append(f"old_three_selected_rows_changed:{old_rows}!=60748")
    if broader_rows <= 0:
        failures.append("broader_positive_origin_rows_not_activated")
    if combined_rows != old_rows + broader_rows:
        failures.append(f"combined_row_mismatch:{combined_rows}!={old_rows}+{broader_rows}")
    if not metric_ok(summary.get("combined_production_selector_metrics") or {}):
        failures.append("combined_selector_metrics_not_positive")
    if not metric_ok(summary.get("broader_origin_selected_metrics") or {}):
        failures.append("broader_origin_selected_metrics_not_positive")
    outside_expanded_metrics = summary.get("broader_origin_outside_session_expansion_metrics") or {}
    outside_expanded_rows = int(summary.get("broader_origin_outside_session_expanded_rows") or 0)
    outside_expected_expanded_rows = int(
        ((outside_summary.get("selected_outside_session_metrics") or {}).get("performance_rows"))
        or 0
    )
    if outside_expected_expanded_rows <= 0:
        failures.append("outside_session_positive_expansion_summary_missing_or_zero")
    if outside_expanded_rows != outside_expected_expanded_rows:
        failures.append(
            f"outside_session_expanded_row_mismatch:{outside_expanded_rows}!={outside_expected_expanded_rows}"
        )
    if outside_expected_expanded_rows and not metric_ok(outside_expanded_metrics):
        failures.append("outside_session_expansion_metrics_not_positive")
    outside_rows_seen = int(summary.get("broader_origin_outside_session_rows_seen") or 0)
    outside_total_rows = int(((outside_summary.get("row_counts") or {}).get("outside_session_rows")) or 0)
    if outside_rows_seen != outside_total_rows:
        failures.append(f"outside_session_denominator_mismatch:{outside_rows_seen}!={outside_total_rows}")

    manifest_rows = list(iter_jsonl(outside_manifest_path)) if outside_manifest_path.exists() else []
    if not manifest_rows:
        failures.append(f"outside_session_shard_manifest_missing:{rel(outside_manifest_path)}")
    outside_shard_row_count = 0
    outside_shard_dispositions: Counter[str] = Counter()
    outside_required_field_missing: Counter[str] = Counter()
    outside_bad_rows = 0
    for manifest_row in manifest_rows:
        shard_rel = manifest_row.get("path")
        shard_path = REPO_ROOT / shard_rel if shard_rel else None
        if shard_path is None or not shard_path.exists():
            failures.append(f"outside_session_shard_missing:{shard_rel}")
            continue
        expected_size = int(manifest_row.get("size_bytes") or -1)
        if expected_size != shard_path.stat().st_size:
            failures.append(f"outside_session_shard_size_mismatch:{shard_rel}:{expected_size}!={shard_path.stat().st_size}")
        expected_sha = str(manifest_row.get("sha256") or "")
        if not expected_sha:
            failures.append(f"outside_session_shard_sha256_missing:{shard_rel}")
        elif expected_sha != sha256_file(shard_path):
            failures.append(f"outside_session_shard_sha256_mismatch:{shard_rel}")
        shard_rows = 0
        for shard_row in iter_jsonl_gz(shard_path):
            shard_rows += 1
            outside_shard_row_count += 1
            missing = sorted(field for field in REQUIRED_OUTSIDE_ROW_FIELDS if shard_row.get(field) in (None, ""))
            for field in missing:
                outside_required_field_missing[field] += 1
            if missing:
                outside_bad_rows += 1
            disposition = str(shard_row.get("repaired_disposition") or "")
            proof_class = str(shard_row.get("repaired_proof_class") or "")
            final_action = str(shard_row.get("final_action") or "")
            proof = str(shard_row.get("proof_class") or "")
            if disposition != final_action:
                failures.append(f"outside_session_row_disposition_action_mismatch:{shard_rel}:{outside_shard_row_count}")
            if proof_class != proof:
                failures.append(f"outside_session_row_proof_class_mismatch:{shard_rel}:{outside_shard_row_count}")
            if disposition == "expand_production_execution_moonshot_extended_session":
                if proof_class != "positive_outside_session_origin_native_dynamic_replay_row_level_proof":
                    failures.append(f"outside_session_expanded_row_without_positive_proof:{shard_rel}:{outside_shard_row_count}")
            outside_shard_dispositions[disposition] += 1
        expected_rows = int(manifest_row.get("rows") or -1)
        if expected_rows != shard_rows:
            failures.append(f"outside_session_shard_row_count_mismatch:{shard_rel}:{expected_rows}!={shard_rows}")
    if outside_shard_row_count != outside_total_rows:
        failures.append(f"outside_session_shard_total_row_mismatch:{outside_shard_row_count}!={outside_total_rows}")
    outside_summary_dispositions = Counter(outside_summary.get("disposition_counts") or {})
    if outside_shard_dispositions != outside_summary_dispositions:
        failures.append(
            f"outside_session_shard_disposition_mismatch:{dict(outside_shard_dispositions)}!={dict(outside_summary_dispositions)}"
        )
    if outside_bad_rows:
        failures.append(f"outside_session_rows_missing_required_fields:{outside_bad_rows}:{dict(outside_required_field_missing)}")

    row_type_counts = Counter(str(row.get("row_type")) for row in ledger_rows)
    activated_groups = [
        row for row in ledger_rows
        if row.get("row_type") == "broader_origin_group_decision"
        and row.get("final_action") == "activate_broader_origin_group"
    ]
    negative_selected = [
        row for row in activated_groups
        if not metric_ok(row.get("metrics") or {})
    ]
    if negative_selected:
        failures.append(f"negative_or_pf_collapse_group_selected:{len(negative_selected)}")
    if len(activated_groups) != len(entries):
        failures.append(f"allowlist_entry_count_mismatch:{len(entries)}!={len(activated_groups)}")
    if len(entries) != int(summary.get("allowlist_entry_count") or -1):
        failures.append("summary_allowlist_entry_count_mismatch")
    broker_excluded = summary.get("broader_origin_broker_excluded_counts") or {}
    for entry in entries:
        symbol = entry.get("symbol")
        session = entry.get("route_session")
        if symbol in {"GER40", "UKOIL_cash", "USOIL_cash", "UKOIL", "USOIL"}:
            failures.append(f"broker_invalid_symbol_selected:{symbol}")
        if symbol == "US30":
            failures.append("uncanonicalized_us30_symbol_selected")
        if session == "missing_session":
            failures.append(f"missing_session_selected:{symbol}:{entry.get('origin_family')}:{entry.get('side')}")
        if session == "off_configured_session" and symbol not in EXPLICIT_24H_SESSION_SYMBOLS:
            failures.append(f"non_crypto_off_configured_session_selected:{symbol}:{entry.get('origin_family')}:{entry.get('side')}")
        if session == "off_configured_session":
            proof_counts = entry.get("session_proof_class_counts") or {}
            if proof_counts.get("explicit_crypto_24h_contract", 0) <= 0:
                failures.append(f"off_configured_session_without_explicit_24h_proof:{symbol}")
        if str(session or "").startswith("moonshot_h"):
            if not entry.get("utc_hour_bucket"):
                failures.append(f"moonshot_extended_without_utc_hour_bucket:{symbol}:{entry.get('origin_family')}:{entry.get('side')}")
            if entry.get("proof_class") != "positive_outside_session_origin_native_dynamic_replay_row_level_proof":
                failures.append(f"moonshot_extended_without_outside_session_proof:{symbol}:{entry.get('origin_family')}:{entry.get('side')}")
    if not any(str(key).startswith("GER40:") for key in broker_excluded):
        warnings.append("no_ger40_broker_exclusion_seen_in_broader_selector")

    session_reconciliation = summary.get("broader_origin_session_reconciliation_counts") or {}
    if session_reconciliation.get("missing_session_not_production_executable_after_session_merge_repair"):
        failures.append("stale_missing_session_reconciliation_reason_used")
    if session_reconciliation.get("explicit_crypto_24h_contract", 0) <= 0:
        warnings.append("no_explicit_crypto_24h_rows_selected_or_seen")

    old_component_rows = [
        row for row in ledger_rows if row.get("row_type") == "old_three_framework_component"
    ]
    if len(old_component_rows) != 1:
        failures.append(f"old_three_component_rows:{len(old_component_rows)}")

    families = set(summary.get("broader_origin_selected_family_counts") or {})
    if not {"liquidity_sweep_reclaim", "cross_asset_lead_lag", "structural_distance_extreme"}.issubset(families):
        failures.append("strong_positive_broader_families_missing_from_selector")
    outside_action_counts = summary.get("broader_origin_outside_session_action_counts") or {}
    if int(outside_action_counts.get("expand_production_execution_moonshot_extended_session") or 0) != outside_expected_expanded_rows:
        failures.append("outside_session_positive_action_not_fully_expanded")
    if (summary.get("broader_origin_exclusion_proof_counts") or {}).get("outside_configured_session_not_production_executable"):
        failures.append("outside_configured_session_terminal_exclusion_label_still_present")

    result = {
        "schema_version": "vnext_replacement_stage13_full_moonshot_production_selector_verifier_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": utc_now(),
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "warnings": warnings,
        "checked_files": {
            "summary": rel(SUMMARY_PATH),
            "ledger": rel(LEDGER_PATH),
            "allowlist": rel(ALLOWLIST_PATH),
            "outside_session_summary": rel(OUTSIDE_SESSION_SUMMARY_PATH),
        },
        "row_type_counts": dict(row_type_counts),
        "old_three_selected_rows": old_rows,
        "broader_origin_selected_rows": broader_rows,
        "combined_selected_rows": combined_rows,
        "activated_broader_group_count": len(activated_groups),
        "allowlist_entry_count": len(entries),
        "outside_session_expanded_rows": outside_expanded_rows,
        "outside_session_rows_seen": outside_rows_seen,
        "outside_session_shard_rows_checked": outside_shard_row_count,
        "outside_session_shard_disposition_counts": dict(sorted(outside_shard_dispositions.items())),
        "combined_metrics": summary.get("combined_production_selector_metrics"),
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
