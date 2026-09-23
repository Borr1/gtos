from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterator


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage13_broader_origin_candidate_replay"
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
MOONSHOT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)

ORIGIN_REGISTRY = MOONSHOT_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_{DATE}.jsonl"
OUTPUT_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_REPLAY_LEDGER_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_REPLAY_SUMMARY_{DATE}.json"
)
OUTPUT_VERIFIER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_REPLAY_VERIFIER_{DATE}.json"
)
CURRENT_ORIGINS = {"ob_retest", "fvg_fill", "breaker_re_entry"}
REQUIRED_POLICY_KEYS = {
    "legacy_fixed_1.5r",
    "live_current_j46_j49",
    "be_after_trigger",
}


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def non_current_registry_names() -> set[str]:
    names = set()
    for row in iter_jsonl(ORIGIN_REGISTRY):
        name = row.get("name")
        if name and name not in CURRENT_ORIGINS:
            names.add(str(name))
    return names


def verify() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if not OUTPUT_LEDGER.exists():
        issues.append({"code": "missing_ledger", "path": rel(OUTPUT_LEDGER)})
        rows: list[dict[str, Any]] = []
    else:
        rows = list(iter_jsonl(OUTPUT_LEDGER))
    if not OUTPUT_SUMMARY.exists():
        issues.append({"code": "missing_summary", "path": rel(OUTPUT_SUMMARY)})
        summary: dict[str, Any] = {}
    else:
        summary = read_json(OUTPUT_SUMMARY)

    registry_names = non_current_registry_names()
    families_in_rows = {str(row.get("origin_family")) for row in rows if row.get("origin_family")}
    families_in_summary = set(summary.get("family_summary") or {})
    missing_family_rows = sorted(registry_names - families_in_rows)
    missing_family_summary = sorted(registry_names - families_in_summary)
    if missing_family_rows:
        issues.append({"code": "missing_family_rows", "families": missing_family_rows})
    if missing_family_summary:
        issues.append({"code": "missing_family_summary", "families": missing_family_summary})

    row_type_counts = Counter(row.get("row_type") for row in rows)
    if row_type_counts.get("candidate_replay", 0) <= 0:
        issues.append({"code": "no_candidate_replay_rows"})
    if row_type_counts.get("proof", 0) <= 0:
        issues.append({"code": "no_proof_rows"})

    candidate_replay_by_family: defaultdict[str, int] = defaultdict(int)
    dynamic_by_family: defaultdict[str, int] = defaultdict(int)
    proof_by_family: defaultdict[str, int] = defaultdict(int)
    for row in rows:
        family = str(row.get("origin_family"))
        if row.get("route_id") != ROUTE_ID:
            issues.append({"code": "wrong_route_id", "row": row.get("candidate_replay_row_id") or row.get("row_type")})
        if row.get("stage_id") != STAGE_ID:
            issues.append({"code": "wrong_stage_id", "row": row.get("candidate_replay_row_id") or row.get("row_type")})
        if row.get("row_type") == "candidate_replay":
            candidate_replay_by_family[family] += 1
            replay = row.get("dynamic_policy_replay") or {}
            results = replay.get("policy_results") or {}
            if replay.get("replay_attempted") and not REQUIRED_POLICY_KEYS.issubset(results):
                issues.append(
                    {
                        "code": "dynamic_policy_results_missing_required_keys",
                        "family": family,
                        "row_id": row.get("candidate_replay_row_id"),
                        "keys": sorted(results),
                    }
                )
            if replay.get("replay_attempted"):
                dynamic_by_family[family] += 1
            candidate = row.get("candidate_row") or {}
            for key in ("candidate_id", "symbol", "side", "entry_reference", "stop_or_invalidation", "target_reference"):
                if candidate.get(key) in (None, ""):
                    issues.append(
                        {
                            "code": "candidate_geometry_field_missing",
                            "field": key,
                            "family": family,
                            "row_id": row.get("candidate_replay_row_id"),
                        }
                    )
                    break
            if not (row.get("candidate_generation_source") or {}).get("generated_from_repo_local_ohlc_or_feature"):
                issues.append(
                    {
                        "code": "candidate_generation_source_not_repo_local",
                        "family": family,
                        "row_id": row.get("candidate_replay_row_id"),
                    }
                )
        elif row.get("row_type") == "proof":
            proof_by_family[family] += 1
            if not row.get("proof_class") or not row.get("exact_blocker"):
                issues.append({"code": "proof_missing_class_or_blocker", "family": family})
            evidence = row.get("evidence")
            if not isinstance(evidence, dict) or not evidence:
                issues.append({"code": "proof_missing_evidence_payload", "family": family})

    for family in registry_names:
        if candidate_replay_by_family[family] == 0 and proof_by_family[family] == 0:
            issues.append({"code": "family_has_neither_replay_nor_proof", "family": family})

    expected_row_counts = summary.get("row_counts") or {}
    actual_counts = {
        "ledger_rows": len(rows),
        "candidate_replay_rows": row_type_counts.get("candidate_replay", 0),
        "proof_rows": row_type_counts.get("proof", 0),
        "dynamic_policy_rows_replayed": sum(dynamic_by_family.values()),
    }
    for key, actual in actual_counts.items():
        expected = expected_row_counts.get(key)
        if expected != actual:
            issues.append({"code": "summary_count_mismatch", "field": key, "summary": expected, "actual": actual})

    summary_dynamic = set(summary.get("families_with_dynamic_policy_replay") or [])
    actual_dynamic = {family for family, count in dynamic_by_family.items() if count > 0}
    if summary_dynamic != actual_dynamic:
        issues.append(
            {
                "code": "dynamic_family_set_mismatch",
                "summary": sorted(summary_dynamic),
                "actual": sorted(actual_dynamic),
            }
        )

    result = {
        "schema_version": "vnext_replacement_stage13_broader_origin_candidate_replay_verifier_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "status": "passed" if not issues else "failed",
        "ok": not issues,
        "issues": issues[:50],
        "issue_count": len(issues),
        "ledger_path": rel(OUTPUT_LEDGER),
        "summary_path": rel(OUTPUT_SUMMARY),
        "registry_path": rel(ORIGIN_REGISTRY),
        "registry_non_current_family_count": len(registry_names),
        "row_type_counts": dict(sorted(row_type_counts.items())),
        "families_with_candidate_replay": sorted(
            family for family, count in candidate_replay_by_family.items() if count > 0
        ),
        "families_with_dynamic_policy_replay": sorted(actual_dynamic),
        "families_with_proof_rows": sorted(family for family, count in proof_by_family.items() if count > 0),
    }
    OUTPUT_VERIFIER.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 2)


if __name__ == "__main__":
    main()
