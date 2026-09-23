"""Verifier for the SCID no-API 40-card prereg/replay-input design route."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN"

EXPECTED_DOMAINS = {
    "geometry_topology_path_shape",
    "stochastic_tail_hazard_first_passage",
    "microstructure_orderflow_liquidity_trapped_flow",
    "behavioral_game_theory_session_participant_constraints",
    "macro_session_calendar_cross_asset_context",
    "execution_science_spread_slippage_fillability",
    "ml_meta_labeling_model_disagreement_uncertainty_controls",
    "adversarial_baselines_placebo_explanations",
}
EXPECTED_READINESS_SPLIT = {
    "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8,
    "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
    "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
}
SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "credentials_touched",
    "changes_trading_risk_safety_prompt_decision_behavior",
]
REQUIRED_JSON_STEMS = [
    "CONTEXT_ANCHOR",
    "SOURCE_FIELD_MAPPING_MATRIX",
    "PER_CARD_TERMINAL_STATUS_LEDGER",
    "REPLAY_INPUT_PACKET_DESIGN_LEDGER",
    "BLOCKED_CARD_DEPENDENCY_LEDGER",
    "SAME_EVIDENCE_CLASS_BLOCKER_PURSUIT_LEDGER",
    "EXPANSION_CANDIDATE_LEDGER",
    "PARTITION_AND_FORWARD_CAPTURE_DEPENDENCY_LEDGER",
    "NEGATIVE_EVIDENCE_AND_ANTI_BOXING_LEDGER",
    "SATURATION_LEDGER",
    "SATURATION_SELF_REDTEAM_AND_ANTI_CEILING_LEDGER",
    "FOCUSED_TEST_RESULT",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
]
REQUIRED_ROW_FILES = [
    "SOURCE_FIELD_MAPPING_MATRIX_ROWS",
    "REPLAY_INPUT_PACKET_DESIGN_ROWS",
    "BLOCKED_CARD_DEPENDENCY_ROWS",
    "EXPANSION_CANDIDATE_ROWS",
]


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(stem: str) -> dict[str, Any]:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def load_jsonl(stem: str) -> list[dict[str, Any]]:
    path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_md(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        "\n".join(
            [
                "# Verification Result",
                "",
                f"- **ok:** `{str(payload['ok']).lower()}`",
                f"- **failure_count:** `{payload['failure_count']}`",
                f"- **can_mark_goal_complete:** `{str(payload['can_mark_goal_complete']).lower()}`",
                "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
                "- **validation_safe:** `false`",
                "- **outcome_review_opened:** `false`",
                "- **live_effect:** `false`",
                "",
                "```json",
                json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{repo_path(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def verify() -> dict[str, Any]:
    failures: list[str] = []
    missing_files = []
    for stem in REQUIRED_JSON_STEMS:
        for suffix in (".json", ".md"):
            path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"
            if not path.exists():
                missing_files.append(repo_path(path))
    for stem in REQUIRED_ROW_FILES:
        path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.jsonl"
        if not path.exists():
            missing_files.append(repo_path(path))
    if missing_files:
        failures.extend(f"missing artifact: {path}" for path in missing_files)
        return {
            "ok": False,
            "failure_count": len(failures),
            "failures": failures,
            "can_mark_goal_complete": False,
        }

    payloads = {stem: load_json(stem) for stem in REQUIRED_JSON_STEMS}
    mapping = payloads["SOURCE_FIELD_MAPPING_MATRIX"]
    terminal = payloads["PER_CARD_TERMINAL_STATUS_LEDGER"]
    replay = payloads["REPLAY_INPUT_PACKET_DESIGN_LEDGER"]
    blocked = payloads["BLOCKED_CARD_DEPENDENCY_LEDGER"]
    expansion = payloads["EXPANSION_CANDIDATE_LEDGER"]
    saturation = payloads["SATURATION_LEDGER"]
    self_redteam = payloads["SATURATION_SELF_REDTEAM_AND_ANTI_CEILING_LEDGER"]
    completion = payloads["COMPLETION_AUDIT"]
    anti_boxing = payloads["NEGATIVE_EVIDENCE_AND_ANTI_BOXING_LEDGER"]

    for stem, payload in payloads.items():
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{stem} promotion_verdict is not NO_PROMOTION_VERDICT")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{stem} safe flag {flag} is not false")

    rows = mapping.get("rows", [])
    if len(rows) != 40:
        failures.append(f"mapping row count {len(rows)} != 40")
    card_ids = [row.get("card_id") for row in rows]
    if len(set(card_ids)) != 40:
        failures.append("mapping card IDs are not unique")
    domain_counts = Counter(row.get("science_domain") for row in rows)
    if set(domain_counts) != EXPECTED_DOMAINS:
        failures.append(f"domain set mismatch: {sorted(domain_counts)}")
    if any(count != 5 for count in domain_counts.values()):
        failures.append(f"not all domains have 5 cards: {dict(domain_counts)}")
    readiness_split = Counter(row.get("accepted_readiness") for row in rows)
    if dict(readiness_split) != EXPECTED_READINESS_SPLIT:
        failures.append(f"readiness split mismatch: {dict(readiness_split)}")
    outside_count = sum(bool(row.get("outside_current_gtos_ob_framing")) for row in rows)
    if outside_count != 33:
        failures.append(f"outside-current-GTOS/OB count {outside_count} != 33")

    terminal_rows = terminal.get("rows", [])
    if len(terminal_rows) != 40:
        failures.append(f"terminal row count {len(terminal_rows)} != 40")
    if sorted(row["card_id"] for row in terminal_rows) != sorted(card_ids):
        failures.append("terminal ledger card IDs do not match mapping")
    if not all(row.get("terminal_status") for row in terminal_rows):
        failures.append("terminal ledger has empty terminal_status")

    packet_rows = replay.get("rows", [])
    if len(packet_rows) != 8:
        failures.append(f"replay packet row count {len(packet_rows)} != 8")
    prereg_cards = sorted(
        row["card_id"]
        for row in rows
        if row["accepted_readiness"] == "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY"
    )
    if sorted(row["card_id"] for row in packet_rows) != prereg_cards:
        failures.append("replay packet card IDs do not match preregisterable-now accepted cards")
    for row in packet_rows:
        if row.get("source_group") != "baseline_control_fields":
            failures.append(f"{row.get('card_id')} packet source group is not baseline_control_fields")
        if not row.get("forbidden_fields"):
            failures.append(f"{row.get('card_id')} packet lacks forbidden field list")

    blocked_rows = blocked.get("rows", [])
    if len(blocked_rows) != 32:
        failures.append(f"blocked dependency row count {len(blocked_rows)} != 32")
    blocked_cards = sorted(
        row["card_id"]
        for row in rows
        if row["accepted_readiness"] != "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY"
    )
    if sorted(row["card_id"] for row in blocked_rows) != blocked_cards:
        failures.append("blocked dependency card IDs do not match blocked accepted cards")

    expansion_rows = expansion.get("rows", [])
    if len(expansion_rows) < 5:
        failures.append("expansion candidate ledger has fewer than 5 candidates")
    if not all(row.get("accepted_40_card_denominator_inclusion") is False for row in expansion_rows):
        failures.append("one or more expansion candidates are mixed into the accepted denominator")

    saturation_ids = sorted(row["card_id"] for row in saturation.get("card_assignments", []))
    if saturation_ids != sorted(card_ids):
        failures.append("saturation ledger does not account for every accepted card exactly once")
    if anti_boxing.get("outside_current_gtos_ob_framing_count") != 33:
        failures.append("anti-boxing ledger did not preserve 33/40 outside-current framing fact")
    if self_redteam.get("treated_accepted_40_as_floor_not_ceiling") is not True:
        failures.append("self-red-team ledger did not prove accepted 40 treated as floor not ceiling")
    for flag in ["not_activation_only", "not_ob_only", "not_current_field_only", "not_passive_waiting"]:
        if self_redteam.get(flag) is not True:
            failures.append(f"self-red-team ledger flag {flag} is not true")
    if completion.get("can_mark_goal_complete") is not True:
        failures.append("completion audit does not allow goal completion")
    if completion.get("validation_result_scoring_closed") is not True:
        failures.append("completion audit does not close validation/result scoring")

    syntax = syntax_parse(
        [
            ROUTE_DIR / "build_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
            ROUTE_DIR / "verify_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
            ROUTE_DIR / "test_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
        ]
    )
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    result = {
        "route_id": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN",
        "evidence_class": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_ONLY",
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "can_mark_goal_complete": not failures,
        "card_count": len(rows),
        "domain_count": len(domain_counts),
        "domain_counts": dict(sorted(domain_counts.items())),
        "readiness_split": dict(sorted(readiness_split.items())),
        "outside_current_gtos_ob_framing_count": outside_count,
        "replay_packet_count": len(packet_rows),
        "blocked_dependency_count": len(blocked_rows),
        "expansion_candidate_count": len(expansion_rows),
        "syntax_parse": syntax,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_validation": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_trading_behavior": False,
    }
    return result


def refresh_manifest_with_verification(result: dict[str, Any]) -> None:
    manifest = load_json("OUTPUT_MANIFEST")
    verification_json = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
    verification_md = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.md"
    artifacts = []
    for path in ROUTE_DIR.iterdir():
        if path.is_file() and (
            path.name == ".gitignore" or path.suffix in {".json", ".jsonl", ".md", ".py"}
        ):
            artifacts.append(
                {
                    "path": repo_path(path),
                    "sha256": sha256_file(path),
                    "artifact_type": path.suffix.lstrip(".") or "gitignore",
                    "bytes": path.stat().st_size,
                }
            )
    manifest["artifact_count"] = len(artifacts)
    manifest["artifacts"] = sorted(artifacts, key=lambda row: row["path"])
    manifest["verification_result"] = {
        "path": repo_path(verification_json),
        "ok": result["ok"],
        "failure_count": result["failure_count"],
        "can_mark_goal_complete": result["can_mark_goal_complete"],
    }
    manifest_path = ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()

    result = verify()
    if not args.no_write:
        result_json = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
        result_md = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.md"
        result_json.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
        write_md(result_md, result)
        refresh_manifest_with_verification(result)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    elif result["ok"]:
        print("OK")
    else:
        print("FAILED")
        for failure in result["failures"]:
            print(f"- {failure}")
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
