from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-27"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
SUMMARY = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_FREQUENCY_TRADE_R_SUMMARY_{DATE}.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_manifest(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def line_count(path: Path) -> int:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def prior_intelligence_semantics(path: Path) -> dict[str, Any]:
    rows = 0
    blank_required = 0
    blank_retained_production = 0
    replacement_status_counts: dict[str, int] = {}
    disposition_counts: dict[str, int] = {}
    examples: list[dict[str, Any]] = []
    required = (
        "consumption_target",
        "answer",
        "status",
        "ledger_row_type",
        "row_level_classification",
    )
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            rows += 1
            disposition = str(row.get("consumption_disposition") or "")
            disposition_counts[disposition] = disposition_counts.get(disposition, 0) + 1
            missing = [
                field
                for field in required
                if row.get(field) is None or (isinstance(row.get(field), str) and not row.get(field).strip())
            ]
            if missing:
                blank_required += 1
                if len(examples) < 5:
                    examples.append(
                        {
                            "line_number": line_number,
                            "missing_fields": missing,
                            "source_name": row.get("source_name"),
                            "source_schema_version": row.get("source_schema_version"),
                            "source_record_type": row.get("source_record_type"),
                            "question_id": row.get("question_id"),
                            "consumption_disposition": disposition,
                        }
                    )
            if (
                row.get("source_name") == "production_replacement_activation"
                and row.get("source_record_type") == "question_closure"
            ):
                status = str(row.get("status") or "")
                replacement_status_counts[status] = replacement_status_counts.get(status, 0) + 1
                if disposition == "retained_as_prior_row_level_evidence_reference" and missing:
                    blank_retained_production += 1
    return {
        "rows": rows,
        "blank_required_rows": blank_required,
        "blank_retained_production_question_closure_rows": blank_retained_production,
        "replacement_question_closure_status_counts": dict(sorted(replacement_status_counts.items())),
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "examples": examples,
    }


def selected_metrics(manifest_path: Path) -> dict[str, Any]:
    rows = 0
    total = 0.0
    wins = losses = breakevens = 0
    components: dict[str, int] = {}
    for manifest_row in iter_manifest(manifest_path):
        shard = REPO_ROOT / manifest_row["path"]
        if sha256_file(shard) != manifest_row.get("sha256"):
            raise AssertionError(f"selected shard hash mismatch:{manifest_row['path']}")
        observed = 0
        with gzip.open(shard, "rt", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                observed += 1
                rows += 1
                value = float(row["r_multiple"])
                total += value
                if value > 0:
                    wins += 1
                elif value < 0:
                    losses += 1
                else:
                    breakevens += 1
                comp = str(row.get("selector_component"))
                components[comp] = components.get(comp, 0) + 1
        if observed != int(manifest_row.get("rows") or 0):
            raise AssertionError(f"selected shard row mismatch:{manifest_row['path']}")
    return {
        "rows": rows,
        "total_r": total,
        "wins": wins,
        "losses": losses,
        "breakevens": breakevens,
        "component_counts": components,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.check:
        raise SystemExit("--check is required; verifier is non-mutating")

    issues: list[str] = []
    summary = read_json(SUMMARY)
    selected_manifest = REPO_ROOT / summary["output_paths"]["canonical_selected_trade_shard_manifest"]
    membership_manifest = REPO_ROOT / summary["output_paths"]["membership_audit_shard_manifest"]
    frequency = REPO_ROOT / summary["output_paths"]["frequency_r_distribution_ledger"]
    prior = REPO_ROOT / summary["output_paths"]["prior_intelligence_consumption_ledger"]
    try:
        selected = selected_metrics(selected_manifest)
    except AssertionError as exc:
        issues.append(str(exc))
        selected = {"rows": 0, "total_r": 0.0, "wins": 0, "losses": 0, "breakevens": 0, "component_counts": {}}

    expected_rows = int(summary["selector_counts"]["combined_selected_rows"])
    if selected["rows"] != expected_rows:
        issues.append(f"selected_rows:{selected['rows']} != {expected_rows}")
    if round(float(selected["total_r"]), 9) != round(float(summary["selector_metrics"]["total_r"]), 9):
        issues.append("selected_total_r_mismatch")
    for component, expected in summary["selected_component_counts"].items():
        if int(selected["component_counts"].get(component, 0)) != int(expected):
            issues.append(f"component_count:{component}")

    membership_rows = 0
    for row in iter_manifest(membership_manifest):
        shard = REPO_ROOT / row["path"]
        if sha256_file(shard) != row.get("sha256"):
            issues.append(f"membership_shard_hash:{row['path']}")
        observed = line_count(shard)
        membership_rows += observed
        if observed != int(row.get("rows") or 0):
            issues.append(f"membership_shard_rows:{row['path']}")
    if membership_rows != int(summary["membership_audit"]["row_count"]):
        issues.append("membership_total_rows_mismatch")

    frequency_rows = line_count(frequency)
    if frequency_rows != int(summary["frequency_distribution_rows"]):
        issues.append("frequency_rows_mismatch")
    prior_semantics = prior_intelligence_semantics(prior)
    prior_rows = int(prior_semantics["rows"])
    if prior_rows != int(summary["prior_intelligence_consumption"]["total_rows"]):
        issues.append("prior_intelligence_rows_mismatch")
    if prior_semantics["blank_required_rows"]:
        issues.append(f"prior_intelligence_blank_required_rows:{prior_semantics['blank_required_rows']}")
    if prior_semantics["blank_retained_production_question_closure_rows"]:
        issues.append(
            "retained_production_question_closure_blank_classification_rows:"
            f"{prior_semantics['blank_retained_production_question_closure_rows']}"
        )
    replacement_counts = prior_semantics["replacement_question_closure_status_counts"]
    if replacement_counts and sum(replacement_counts.values()) != summary["prior_intelligence_consumption"]["source_counts"].get(
        "production_replacement_activation"
    ):
        issues.append("production_replacement_question_closure_status_count_mismatch")
    for status in ("answered_with_disk_evidence", "source_capture_required", "implemented"):
        if replacement_counts and status not in replacement_counts:
            issues.append(f"production_replacement_question_closure_status_missing:{status}")

    result = {
        "mode": "check",
        "status": "passed" if not issues else "failed",
        "issue_count": len(issues),
        "issues": issues,
        "selected_rows": selected["rows"],
        "membership_rows": membership_rows,
        "frequency_rows": frequency_rows,
        "prior_intelligence_rows": prior_rows,
        "prior_intelligence_semantics": prior_semantics,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
