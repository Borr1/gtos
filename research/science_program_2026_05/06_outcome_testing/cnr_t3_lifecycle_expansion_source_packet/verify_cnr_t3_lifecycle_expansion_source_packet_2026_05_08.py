"""Verifier for CNR T3 lifecycle expansion source packet artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE_STAMP = "2026-05-08"
THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[3]

ALLOWED_LABELS = {
    "target_after_original_horizon",
    "stop_after_original_horizon",
    "ambiguous_target_stop_after_original_horizon",
    "still_no_terminal_after_extended_horizon",
    "source_horizon_insufficient",
    "not_packet_eligible",
}

FORBIDDEN_PACKET_ROW_KEYS = {
    "synthetic_r",
    "broker_actual_r",
    "account_history",
    "live_trade_result",
    "live_trade_results",
    "live_order_state",
    "hidden_path_label",
    "promotion_statistic",
    "win_rate",
    "expectancy",
    "dsr",
    "pbo",
    "performance",
}

REQUIRED_STEMS = [
    "CNR_T3_CONTEXT_ANCHOR_2026-05-08",
    "CNR_T3_FROZEN_LIFECYCLE_CONTRACT_2026-05-08",
    "CNR_T3_NO_TERMINAL_CANDIDATE_INVENTORY_2026-05-08",
    "CNR_T3_SEARCHED_ROOT_AND_SOURCE_HASH_LEDGER_2026-05-08",
    "CNR_T3_LIFECYCLE_PACKET_2026-05-08",
    "CNR_T3_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08",
    "CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08",
    "CNR_T3_LIFECYCLE_FORENSICS_AND_LEARNING_2026-05-08",
    "CNR_T3_COMPLETION_AUDIT_2026-05-08",
]


def load_json(name: str) -> Any:
    return json.loads((THIS_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with (THIS_DIR / name).open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def forbidden_keys(obj: Any) -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_l = str(key).lower()
            hits.extend([str(key)] if any(f in key_l for f in FORBIDDEN_PACKET_ROW_KEYS) else [])
            hits.extend(forbidden_keys(value))
    elif isinstance(obj, list):
        for item in obj:
            hits.extend(forbidden_keys(item))
    return hits


def git_changed_files() -> list[str]:
    try:
        output = subprocess.check_output(["git", "diff", "--name-only"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return []
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def main() -> None:
    issues: list[str] = []

    for stem in REQUIRED_STEMS:
        for suffix in (".json", ".md"):
            if not (THIS_DIR / f"{stem}{suffix}").exists():
                issues.append(f"missing required artifact {stem}{suffix}")
    if not (THIS_DIR / "CNR_T3_LIFECYCLE_PACKET_2026-05-08_ROWS.jsonl").exists():
        issues.append("missing lifecycle packet JSONL")
    if not (THIS_DIR / "CNR_T3_G12_AUDIT_PROMPT_PACK_2026-05-08.md").exists():
        issues.append("missing G12 audit prompt pack")

    contract = load_json("CNR_T3_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json")
    inventory = load_json("CNR_T3_NO_TERMINAL_CANDIDATE_INVENTORY_2026-05-08.json")
    source_ledger = load_json("CNR_T3_SEARCHED_ROOT_AND_SOURCE_HASH_LEDGER_2026-05-08.json")
    packet = load_json("CNR_T3_LIFECYCLE_PACKET_2026-05-08.json")
    packet_rows = load_jsonl("CNR_T3_LIFECYCLE_PACKET_2026-05-08_ROWS.jsonl")
    audit = load_json("CNR_T3_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json")
    blockers = load_json("CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json")
    completion = load_json("CNR_T3_COMPLETION_AUDIT_2026-05-08.json")

    if contract.get("contract_id") != "CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1":
        issues.append("wrong contract id")
    if set(contract.get("allowed_labels", [])) != ALLOWED_LABELS:
        issues.append("contract allowed labels mismatch")
    if "before any beyond-original-horizon tick extension scan" not in str(contract.get("freeze_order", "")):
        issues.append("contract freeze order not explicit")

    labels = {row.get("lifecycle_label") for row in packet_rows}
    if not labels.issubset(ALLOWED_LABELS):
        issues.append(f"packet labels outside allowed set: {sorted(labels - ALLOWED_LABELS)}")
    if packet.get("row_count") != len(packet_rows):
        issues.append("packet JSON row_count does not match JSONL rows")
    if packet.get("row_count") != 6:
        issues.append(f"expected 6 packet rows, found {packet.get('row_count')}")
    if packet.get("lifecycle_label_counts", {}).get("stop_after_original_horizon") != 6:
        issues.append("expected all six packet rows to be stop_after_original_horizon")

    for row in packet_rows:
        hits = forbidden_keys(row)
        if hits:
            issues.append(f"forbidden packet row keys in {row.get('input_inventory_id')}: {sorted(set(hits))}")
        for field in ("promotion_verdict", "validation_safe", "outcome_review_opened", "live_effect"):
            if field == "promotion_verdict":
                if row.get(field) != "NO_PROMOTION_VERDICT":
                    issues.append(f"row {row.get('input_inventory_id')} promotion verdict mismatch")
            elif row.get(field) is not False:
                issues.append(f"row {row.get('input_inventory_id')} {field} is not false")
        if not row.get("tick_source_files"):
            issues.append(f"row {row.get('input_inventory_id')} missing tick source hashes")

    candidate_count = inventory.get("candidate_count")
    packetized = packet.get("row_count")
    blocked = blockers.get("blocker_count")
    if candidate_count != packetized + blocked:
        issues.append(f"candidate coverage mismatch: candidates={candidate_count} packet={packetized} blockers={blocked}")
    if not blockers.get("all_candidates_packetized_or_blocked"):
        issues.append("blocker ledger does not mark all candidates packetized or blocked")
    if inventory.get("packet_eligible_count") != 6:
        issues.append(f"expected 6 packet-eligible candidates, found {inventory.get('packet_eligible_count')}")

    if audit.get("forbidden_packet_row_key_status") != "PASS":
        issues.append("no-leak audit forbidden key status not PASS")
    if audit.get("allowed_label_status") != "PASS":
        issues.append("allowed label audit status not PASS")
    if audit.get("sample_floor_for_validation_met") is not False:
        issues.append("sample floor must remain false")
    if audit.get("blocked_94_status") != "PASS":
        issues.append("94 blocked row exclusion status not PASS")

    consumed = source_ledger.get("consumed_tick_file_hashes", [])
    if not consumed:
        issues.append("no consumed tick file hashes recorded")
    for item in consumed:
        path = Path(item["path"])
        if not path.exists():
            issues.append(f"consumed tick file missing on disk: {path}")
        if not item.get("sha256"):
            issues.append(f"consumed tick file missing sha256: {path}")

    for obj_name, obj in {
        "contract": contract,
        "inventory": inventory,
        "source_ledger": source_ledger,
        "packet": packet,
        "audit": audit,
        "blockers": blockers,
        "completion": completion,
    }.items():
        if obj.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            issues.append(f"{obj_name} promotion verdict mismatch")
        if obj.get("validation_safe") is not False:
            issues.append(f"{obj_name} validation_safe not false")
        if obj.get("outcome_review_opened") is not False:
            issues.append(f"{obj_name} outcome_review_opened not false")
        if obj.get("live_effect") is not False:
            issues.append(f"{obj_name} live_effect not false")

    forbidden_prefixes = (
        "src/",
        "prompts/",
        "config/",
        "scripts/canary",
        "knowledge_base/credentials",
    )
    changed = git_changed_files()
    forbidden_changed = [path for path in changed if path.startswith(forbidden_prefixes)]
    if forbidden_changed:
        issues.append(f"forbidden live-surface files changed: {forbidden_changed}")

    status = "PASS" if not issues else "FAIL"
    result = {
        "verification_status": status,
        "issues": issues,
        "packet_rows": len(packet_rows),
        "candidate_count": candidate_count,
        "blocker_count": blocked,
        "changed_files_checked": changed,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
