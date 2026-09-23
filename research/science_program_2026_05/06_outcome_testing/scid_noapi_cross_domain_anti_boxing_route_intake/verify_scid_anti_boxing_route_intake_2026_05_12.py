"""Verifier for the SCID no-API cross-domain anti-boxing route intake."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "SCID_ANTI_BOXING"
EVIDENCE_CLASS = "SCID_NOAPI_CROSS_DOMAIN_ROUTE_INTAKE_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

REQUIRED_JSON_STEMS = [
    "ROUTE_FAMILY_INVENTORY",
    "SOURCE_CONTRACT_TEMPLATES",
    "CANDIDATE_ACCEPTANCE_REJECTION_CRITERIA",
    "ROUTE_RANKING_MATRIX",
    "NEGATIVE_EVIDENCE_LEDGER",
    "DOMAIN_COVERAGE_AND_GAP_LEDGER",
    "PROMPT_PACK_MANIFEST",
    "COMPLETION_AUDIT",
    "VERIFICATION_RESULT",
    "CONTEXT_ANCHOR",
    "OUTPUT_MANIFEST",
]
REQUIRED_MD_STEMS = ["SATURATION_SELF_RED_TEAM"]
REQUIRED_PY = [
    "build_scid_anti_boxing_route_intake_2026_05_12.py",
    "verify_scid_anti_boxing_route_intake_2026_05_12.py",
    "test_scid_anti_boxing_route_intake_2026_05_12.py",
]
REQUIRED_DOMAINS = {
    "geometry_topology_path_shape",
    "stochastic_tail_hazard",
    "auction_microstructure_orderflow_liquidity",
    "behavioral_game_theory_session_participants",
    "macro_calendar_cross_asset",
    "execution_fillability_spread_slippage",
    "ml_meta_labeling_uncertainty",
    "adversarial_baselines_placebos",
    "source_missingness_denominator_controls",
    "failure_anatomy_derived_hypotheses",
}
SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "may_open_outcomes_or_results_in_this_route",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "credentials_touched",
    "changes_trading_risk_safety_prompt_decision_behavior",
]
REQUIRED_FAMILY_FIELDS = [
    "route_family_id",
    "science_domain",
    "hypothesis_mechanism",
    "source_requirements",
    "as_of_no_leak_policy",
    "duplicate_denominator_policy",
    "likely_row_universe",
    "forbidden_fields",
    "blockers",
    "g12_g0_gates",
    "why_not_current_gtos_ob_framing",
    "accepted_40_relationship",
    "route_can_run_now_without_scoring",
    "rank_score",
]


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{rel(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/",
        "research/science_program_2026_05/04_goal_prompts/SCID_ANTI_BOXING_",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
    raw_blob_suffixes = (".scid", ".depth", ".parquet", ".jsonl.gz", ".zip", ".bin")
    entries = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in allowed_prefixes)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(forbidden_live_prefixes),
                "scoped_raw_market_blob": scoped and path.endswith(raw_blob_suffixes),
            }
        )
    scoped_entries = [row for row in entries if row["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "scoped_entries": scoped_entries,
        "unscoped_entry_count": len(entries) - len(scoped_entries),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def safe_flags_ok(payload: dict[str, Any]) -> list[str]:
    failures = []
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        failures.append("promotion_verdict is not NO_PROMOTION_VERDICT")
    if payload.get("evidence_class") != EVIDENCE_CLASS:
        failures.append(f"evidence_class mismatch: {payload.get('evidence_class')}")
    for flag in SAFE_FALSE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(f"{flag} is not false")
    return failures


def refresh_completion_and_manifest(result: dict[str, Any], mark_focused_tests_ok: bool) -> None:
    completion_path = artifact_path("COMPLETION_AUDIT")
    if completion_path.exists():
        completion = read_json(completion_path)
        completion["standalone_verifier_ok"] = result["ok"]
        completion["standalone_verifier_failures"] = result["failures"]
        if mark_focused_tests_ok:
            completion["focused_tests_ok"] = True
            for row in completion.get("prompt_to_artifact_checklist", []):
                if row.get("requirement") == "builder, verifier, focused tests, and saturation/self-red-team exist":
                    row["satisfied"] = result["ok"]
        completion["all_checklist_items_satisfied"] = all(
            row.get("satisfied") for row in completion.get("prompt_to_artifact_checklist", [])
        )
        write_json(completion_path, completion)

    manifest_path = artifact_path("OUTPUT_MANIFEST")
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        files = manifest.get("files", [])
        known_paths = {row["path"] for row in files}
        for stem in ["COMPLETION_AUDIT", "VERIFICATION_RESULT", "OUTPUT_MANIFEST"]:
            path = artifact_path(stem)
            if rel(path) not in known_paths:
                files.append({"path": rel(path), "exists": path.exists(), "sha256": None})
        for row in files:
            path = ROOT / row["path"]
            row["exists"] = path.exists()
            row["sha256"] = sha256_file(path)
        manifest["files"] = files
        manifest["file_count"] = len(files)
        write_json(manifest_path, manifest)


def verify(mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[str] = []

    required_json_paths = [artifact_path(stem) for stem in REQUIRED_JSON_STEMS]
    required_md_paths = [artifact_path(stem, ".md") for stem in REQUIRED_MD_STEMS]
    required_py_paths = [ROUTE_DIR / filename for filename in REQUIRED_PY]
    for path in required_json_paths + required_md_paths + required_py_paths:
        if not path.exists():
            failures.append(f"missing required file: {rel(path)}")

    payloads: dict[str, Any] = {}
    for stem, path in zip(REQUIRED_JSON_STEMS, required_json_paths):
        if path.exists():
            try:
                payloads[stem] = read_json(path)
            except json.JSONDecodeError as exc:
                failures.append(f"invalid json {rel(path)}: {exc}")

    for stem, payload in payloads.items():
        failures.extend(f"{stem}: {failure}" for failure in safe_flags_ok(payload))

    inventory = payloads.get("ROUTE_FAMILY_INVENTORY", {})
    upstream = inventory.get("upstream_reconstruction", {})
    if upstream.get("accepted_card_count") != 40:
        failures.append("accepted 40 reconstruction count mismatch")
    if upstream.get("ready_card_count") != 8:
        failures.append("ready 8 reconstruction count mismatch")
    if upstream.get("blocked_card_count") != 32:
        failures.append("blocked 32 reconstruction count mismatch")
    if upstream.get("preserved_target_expansion_candidate_count", 0) < 8:
        failures.append("preserved expansion candidate count below 8")
    if upstream.get("g0_discovered_expansion_candidate_count") != 4:
        failures.append("G0 discovered expansion candidate count mismatch")
    if upstream.get("all_expansion_candidates_denominator_inclusion_false") is not True:
        failures.append("expansion candidates are not all denominator-excluded")

    families = inventory.get("route_families", [])
    if inventory.get("route_family_count") != len(families):
        failures.append("route family count field does not match route_families length")
    if len(families) < 40:
        failures.append("route family count below 40")
    domains = {row.get("science_domain") for row in families}
    if not REQUIRED_DOMAINS.issubset(domains):
        failures.append(f"missing required domains: {sorted(REQUIRED_DOMAINS - domains)}")
    for row in families:
        missing = [field for field in REQUIRED_FAMILY_FIELDS if not row.get(field)]
        if missing:
            failures.append(f"{row.get('route_family_id', '<unknown>')} missing fields: {missing}")
        if row.get("may_open_outcomes_or_results_in_this_route") is not False:
            failures.append(f"{row.get('route_family_id')} may open outcomes/results")
        if row.get("opens_broker_account_order_history_deal_position_evidence") is not False:
            failures.append(f"{row.get('route_family_id')} opens broker evidence")

    source_contracts = payloads.get("SOURCE_CONTRACT_TEMPLATES", {})
    templates = source_contracts.get("templates", [])
    if source_contracts.get("template_count") != len(templates):
        failures.append("source template count mismatch")
    if len(templates) < 10:
        failures.append("source template count below 10")
    for template in templates:
        for field in [
            "template_id",
            "source_family",
            "required_fields",
            "as_of_rule",
            "duplicate_policy",
            "forbidden_fields",
            "searched_root_expectations",
            "hash_deferral_policy",
            "no_leak_rules",
            "fail_closed_statuses",
        ]:
            if not template.get(field):
                failures.append(f"source template missing {field}: {template.get('template_id')}")

    ranking = payloads.get("ROUTE_RANKING_MATRIX", {})
    ranked_rows = ranking.get("ranked_route_families", [])
    if len(ranked_rows) != len(families):
        failures.append("ranking row count does not match family count")
    rank_scores = [row.get("rank_score") for row in ranked_rows]
    if rank_scores != sorted(rank_scores, reverse=True):
        failures.append("ranking rows are not sorted by descending rank_score")

    domain = payloads.get("DOMAIN_COVERAGE_AND_GAP_LEDGER", {})
    if domain.get("all_required_domains_have_new_route_family") is not True:
        failures.append("not all required domains are covered by route families")

    negative = payloads.get("NEGATIVE_EVIDENCE_LEDGER", {})
    if negative.get("negative_evidence_count", 0) < 6:
        failures.append("negative evidence count below 6")
    if not any(row.get("status") == "REJECTED_AS_BOXED" for row in negative.get("negative_evidence_rows", [])):
        failures.append("negative evidence ledger lacks boxed-route rejection")

    prompt_manifest = payloads.get("PROMPT_PACK_MANIFEST", {})
    prompt_packs = prompt_manifest.get("prompt_packs", [])
    if prompt_manifest.get("prompt_pack_count") != len(prompt_packs):
        failures.append("prompt pack count mismatch")
    if len(prompt_packs) < len(REQUIRED_DOMAINS):
        failures.append("prompt pack count below required domain count")
    if prompt_manifest.get("all_required_domains_have_prompt_pack") is not True:
        failures.append("not all domains have prompt packs")
    for pack in prompt_packs:
        prompt_path = ROOT / pack.get("prompt_path", "")
        starter_path = ROOT / pack.get("starter_path", "")
        if not prompt_path.exists():
            failures.append(f"missing prompt pack prompt: {pack.get('prompt_path')}")
            continue
        if not starter_path.exists():
            failures.append(f"missing prompt pack starter: {pack.get('starter_path')}")
            continue
        prompt_text = prompt_path.read_text(encoding="utf-8")
        starter_text = starter_path.read_text(encoding="utf-8")
        for phrase in [
            "Do not rely on chat memory",
            "Current GTOS OB/retest logic is not the research horizon",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "Completion Standard",
        ]:
            if phrase not in prompt_text:
                failures.append(f"prompt {pack.get('prompt_path')} missing phrase: {phrase}")
        if "\n" in starter_text.strip():
            failures.append(f"starter is not one physical line: {pack.get('starter_path')}")
        if not starter_text.startswith("/goal Follow the full controlling prompt"):
            failures.append(f"starter does not bind controlling prompt: {pack.get('starter_path')}")

    completion = payloads.get("COMPLETION_AUDIT", {})
    if completion.get("all_checklist_items_satisfied") is not True:
        failures.append("completion audit checklist is not fully satisfied")
    required_completion_keys = [
        "stayed_open_beyond_current_ob_gtos_framing",
        "new_domains_or_mechanisms_found",
        "rejected_with_evidence",
        "preserved_for_future_g12_g0_filtering",
        "immediate_parallel_routes_that_can_run_next",
    ]
    for key in required_completion_keys:
        if key not in completion.get("completion_questions", {}):
            failures.append(f"completion audit missing completion question: {key}")

    saturation_path = artifact_path("SATURATION_SELF_RED_TEAM", ".md")
    if saturation_path.exists():
        saturation = saturation_path.read_text(encoding="utf-8")
        for phrase in [
            "OB/retest logic",
            "accepted 40",
            "passive waiting",
            "No outcome/result",
            "broker account/order/history/deal/position",
        ]:
            if phrase not in saturation:
                failures.append(f"saturation ledger missing phrase: {phrase}")

    syntax = syntax_parse([path for path in required_py_paths if path.exists()])
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    git_status = scoped_git_status()
    if not git_status["no_scoped_forbidden_live_surface"]:
        failures.append("scoped changes include forbidden live surface")
    if not git_status["no_scoped_raw_market_blob"]:
        failures.append("scoped changes include raw market blob")

    result = {
        "artifact_family": "verification_result",
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        **{flag: False for flag in SAFE_FALSE_FLAGS},
        "ok": not failures,
        "failures": failures,
        "can_mark_goal_complete": not failures and bool(mark_focused_tests_ok),
        "accepted_card_count_verified": upstream.get("accepted_card_count"),
        "ready_card_count_verified": upstream.get("ready_card_count"),
        "blocked_card_count_verified": upstream.get("blocked_card_count"),
        "route_family_count_verified": len(families),
        "required_domain_count_verified": len(domains & REQUIRED_DOMAINS),
        "source_contract_template_count_verified": len(templates),
        "prompt_pack_count_verified": len(prompt_packs),
        "negative_evidence_count_verified": negative.get("negative_evidence_count"),
        "syntax_parse": syntax,
        "scoped_git_status": git_status,
    }
    refresh_completion_and_manifest(result, mark_focused_tests_ok=mark_focused_tests_ok)
    write_json(artifact_path("VERIFICATION_RESULT"), result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
