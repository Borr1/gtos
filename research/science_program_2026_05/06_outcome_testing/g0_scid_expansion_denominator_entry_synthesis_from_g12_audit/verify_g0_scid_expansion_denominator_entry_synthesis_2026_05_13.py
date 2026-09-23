"""Verifier for the G0 expansion denominator-entry synthesis package."""

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
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"

DATE_TAG = "2026-05-13"
PREFIX = "G0_SCID_EXPANSION_DENOM_ENTRY_SYNTHESIS"
ROUTE_ID = "G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_FROM_G12_AUDIT"
EVIDENCE_CLASS = "G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_WITH_QUARANTINED_ROUTE_PLAN"

REQUIRED_JSON_STEMS = [
    "DECISION_LEDGER",
    "ROUTE_FAMILY_LEDGER",
    "RANKED_ROUTE_PLAN",
    "PROMPT_PACKS",
    "DENOMINATOR_QUARANTINE_PROOF",
    "BLOCKER_PURSUIT_LEDGER",
    "EXPANSION_OVERFLOW_LEDGER",
    "PARALLELIZATION_PLAN",
    "SATURATION_SELF_RED_TEAM",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
]
REQUIRED_MD_STEMS = [
    "DECISION_LEDGER",
    "ROUTE_FAMILY_LEDGER",
    "RANKED_ROUTE_PLAN",
    "PROMPT_PACKS",
    "DENOMINATOR_QUARANTINE_PROOF",
    "BLOCKER_PURSUIT_LEDGER",
    "EXPANSION_OVERFLOW_LEDGER",
    "PARALLELIZATION_PLAN",
    "SATURATION_SELF_RED_TEAM",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
]
REQUIRED_PY = [
    "build_g0_scid_expansion_denominator_entry_synthesis_2026_05_13.py",
    "verify_g0_scid_expansion_denominator_entry_synthesis_2026_05_13.py",
    "test_g0_scid_expansion_denominator_entry_synthesis_2026_05_13.py",
]
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
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "credentials_touched",
    "changes_trading_risk_safety_prompt_decision_behavior",
]
SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    **{flag: False for flag in SAFE_FALSE_FLAGS},
}
EXPECTED_CANDIDATE_IDS = {
    "EXP-DENOM-001",
    "EXP-MISS-001",
    "EXP-POI-001",
    "EXP-LTF-001",
    "EXP-PROXY-001",
    "EXP-LIFE-001",
    "EXP-CAL-001",
    "EXP-ADV-001",
    "G0-EXP-PARTITION-001",
    "G0-EXP-DOMAIN-MISSINGNESS-001",
    "G0-EXP-NEGCTRL-001",
    "G0-EXP-ROWSET-001",
    "R4-EXP-ROOT-001",
    "R4-EXP-PARSER-001",
    "R4-EXP-CAPGROUP-001",
    "R4-EXP-CLOCK-001",
    "R4-EXP-ALIAS-001",
    "R4-EXP-BASIS-001",
    "R4-EXP-NEG-001",
    "R4-EXP-MLDATA-001",
    "R4-EXP-COSTSRC-001",
    "R4-EXP-NEWSMACRO-001",
    "R4-EXP-PLACEBO-001",
    "R4-EXP-CODEHIST-001",
}


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
    failures: list[str] = []
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
        "research/science_program_2026_05/06_outcome_testing/g0_scid_expansion_denominator_entry_synthesis_from_g12_audit/",
        "research/science_program_2026_05/04_goal_prompts/G0EXP_",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "run_agent.py")
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


def all_safe(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        failures.append("promotion_verdict is not NO_PROMOTION_VERDICT")
    for flag in SAFE_FALSE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(f"{flag} is not false")
    return failures


def refresh_completion(result: dict[str, Any], mark_focused_tests_ok: bool) -> None:
    path = artifact_path("COMPLETION_AUDIT")
    md_path = artifact_path("COMPLETION_AUDIT", ".md")
    if not path.exists():
        return
    completion = read_json(path)
    completion["standalone_verifier_ok"] = result["ok"]
    completion["standalone_verifier_failures"] = result["failures"]
    if mark_focused_tests_ok:
        completion["focused_tests_ok"] = True
    for row in completion.get("prompt_to_artifact_checklist", []):
        if row.get("requirement") == "standalone verifier and focused tests pass":
            row["satisfied"] = result["ok"] and bool(mark_focused_tests_ok)
            row["evidence"] = rel(artifact_path("VERIFICATION_RESULT"))
    non_commit_rows = [
        row
        for row in completion.get("prompt_to_artifact_checklist", [])
        if row.get("requirement") != "scoped artifacts committed"
    ]
    completion["completion_standard_satisfied_before_commit"] = all(row.get("satisfied") is True for row in non_commit_rows)
    completion["completion_standard_satisfied"] = all(
        row.get("satisfied") is True for row in completion.get("prompt_to_artifact_checklist", [])
    )
    completion["can_mark_goal_complete"] = completion["completion_standard_satisfied_before_commit"]
    write_json(path, completion)
    md_path.write_text(
        "\n".join(
            [
                "# Completion Audit",
                "",
                f"- **route_id:** `{ROUTE_ID}`",
                f"- **evidence_class:** `{EVIDENCE_CLASS}`",
                "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
                "- **validation_safe:** `false`",
                "- **outcome_review_opened:** `false`",
                "- **live_effect:** `false`",
                "",
                "```json",
                json.dumps(completion, indent=2, sort_keys=True, ensure_ascii=True),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def refresh_output_manifest(result: dict[str, Any]) -> None:
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    manifest_md_path = artifact_path("OUTPUT_MANIFEST", ".md")
    if not manifest_path.exists():
        return
    excluded = {manifest_path.resolve(), manifest_md_path.resolve()}
    paths: set[Path] = set()
    for path in ROUTE_DIR.iterdir():
        if path.is_file() and path.resolve() not in excluded and path.suffix.lower() in {".json", ".md", ".py", ".txt"}:
            paths.add(path)
    prompt_manifest = read_json(artifact_path("PROMPT_PACKS"))
    for row in prompt_manifest.get("prompt_packs", []):
        prompt_path = ROOT / row.get("prompt_path", "")
        if prompt_path.exists():
            paths.add(prompt_path)
    manifest = read_json(manifest_path)
    manifest["artifact_count"] = len(paths)
    manifest["artifacts"] = [
        {"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in sorted(paths)
    ]
    manifest["verification_result"] = {
        "path": rel(artifact_path("VERIFICATION_RESULT")),
        "ok": result["ok"],
        "failure_count": result["failure_count"],
        "can_mark_goal_complete": result["can_mark_goal_complete"],
    }
    write_json(manifest_path, manifest)
    manifest_md_path.write_text(
        "\n".join(
            [
                "# Output Manifest",
                "",
                f"- **route_id:** `{ROUTE_ID}`",
                f"- **evidence_class:** `{EVIDENCE_CLASS}`",
                "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
                "- **validation_safe:** `false`",
                "- **outcome_review_opened:** `false`",
                "- **live_effect:** `false`",
                "",
                "```json",
                json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def verify(mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}

    for stem in REQUIRED_JSON_STEMS:
        path = artifact_path(stem)
        if not path.exists():
            failures.append(f"missing json artifact: {rel(path)}")
            continue
        loaded[stem] = read_json(path)
    for stem in REQUIRED_MD_STEMS:
        path = artifact_path(stem, ".md")
        if not path.exists():
            failures.append(f"missing markdown artifact: {rel(path)}")
    for name in REQUIRED_PY:
        path = ROUTE_DIR / name
        if not path.exists():
            failures.append(f"missing python artifact: {rel(path)}")

    if not failures:
        for stem, payload in loaded.items():
            if stem != "VERIFICATION_RESULT":
                failures.extend(f"{stem}: {failure}" for failure in all_safe(payload))

        decision = loaded["DECISION_LEDGER"]
        if decision.get("terminal_decision") != TERMINAL_DECISION:
            failures.append("decision: terminal decision mismatch")
        facts = decision.get("accepted_audit_facts", {})
        if facts.get("total_quarantined_expansion_candidates") != 24:
            failures.append("decision: total quarantined candidate count is not 24")
        if facts.get("accepted_40_overlap") != 0:
            failures.append("decision: accepted 40 overlap is nonzero")
        if facts.get("accepted_40_count") != 40:
            failures.append("decision: accepted 40 count is not 40")

        ledger = loaded["ROUTE_FAMILY_LEDGER"]
        rows = ledger.get("rows", [])
        candidate_ids = {row.get("candidate_id") for row in rows}
        if candidate_ids != EXPECTED_CANDIDATE_IDS:
            failures.append(f"route ledger: candidate ids mismatch {sorted(candidate_ids ^ EXPECTED_CANDIDATE_IDS)}")
        if ledger.get("accepted_count") != 24 or ledger.get("deferred_count") != 0 or ledger.get("rejected_count") != 0:
            failures.append("route ledger: accepted/deferred/rejected counts unexpected")
        if any(row.get("accepted_40_card_denominator_inclusion") is not False for row in rows):
            failures.append("route ledger: a candidate is included in accepted 40")
        if any(row.get("may_open_results_now") is not False for row in rows):
            failures.append("route ledger: may_open_results_now not false")
        if any(not row.get("exact_next_prompt") or not row.get("exact_next_starter") for row in rows):
            failures.append("route ledger: missing exact prompt/starter")

        plan = loaded["RANKED_ROUTE_PLAN"]
        packs = plan.get("ranked_route_packs", [])
        pack_ids = [pack.get("route_id") for pack in packs]
        if plan.get("route_pack_count") != 6 or len(pack_ids) != len(set(pack_ids)):
            failures.append("ranked plan: expected six unique route packs")
        covered = [cid for pack in packs for cid in pack.get("candidate_ids", [])]
        if set(covered) != EXPECTED_CANDIDATE_IDS or len(covered) != 24:
            failures.append("ranked plan: candidate coverage is not exactly 24 once")
        if plan.get("immediate_result_execution_allowed") is not False:
            failures.append("ranked plan: result execution is allowed")

        prompts = loaded["PROMPT_PACKS"].get("prompt_packs", [])
        if len(prompts) != 6:
            failures.append("prompt packs: expected six packs")
        for row in prompts:
            prompt_path = ROOT / row.get("prompt_path", "")
            starter_path = ROOT / row.get("starter_path", "")
            if not prompt_path.exists() or not starter_path.exists():
                failures.append(f"prompt packs: missing prompt/starter for {row.get('route_id')}")
                continue
            prompt_text = prompt_path.read_text(encoding="utf-8")
            starter_text = starter_path.read_text(encoding="utf-8").strip()
            for phrase in [
                "Do not rely on chat memory",
                "NO_PROMOTION_VERDICT",
                "validation_safe=false",
                "outcome_review_opened=false",
                "live_effect=false",
                "accepted-40 denominator quarantine",
                "Completion Standard",
            ]:
                if phrase not in prompt_text and phrase not in starter_text:
                    failures.append(f"prompt packs: {row.get('route_id')} missing phrase {phrase}")
            if "\n" in starter_text:
                failures.append(f"prompt packs: starter is not one physical line for {row.get('route_id')}")
            if len(starter_text) >= 4000:
                failures.append(f"prompt packs: starter too long for {row.get('route_id')}")

        quarantine = loaded["DENOMINATOR_QUARANTINE_PROOF"]
        if quarantine.get("candidate_overlap_count") != 0:
            failures.append("quarantine: candidate overlap count is nonzero")
        if quarantine.get("accepted_40_count_recomputed_from_g12") != 40:
            failures.append("quarantine: accepted 40 recomputation count is not 40")
        if quarantine.get("all_route_family_rows_denominator_inclusion_false") is not True:
            failures.append("quarantine: route-family inclusion guard failed")
        if quarantine.get("all_overflow_rows_denominator_inclusion_false") is not True:
            failures.append("quarantine: overflow inclusion guard failed")

        overflow = loaded["EXPANSION_OVERFLOW_LEDGER"]
        overflow_rows = overflow.get("rows", [])
        if overflow.get("overflow_count") != 40 or len(overflow_rows) != 40:
            failures.append("overflow: expected forty anti-boxing overflow rows")
        if overflow.get("accepted_support_count", 0) < 12:
            failures.append("overflow: accepted support count is too narrow")
        if not all(str(row.get("overflow_candidate_id", "")).startswith("OVF-ANTI-") for row in overflow_rows):
            failures.append("overflow: namespace guard prefix missing")
        if any(row.get("accepted_40_card_denominator_inclusion") is not False for row in overflow_rows):
            failures.append("overflow: denominator inclusion guard failed")

        blocker = loaded["BLOCKER_PURSUIT_LEDGER"]
        if len(blocker.get("candidate_blocker_rows", [])) != 24:
            failures.append("blocker pursuit: not all 24 candidates have blocker rows")
        if any(row.get("source_materialization_status") != "EXACT_RUNNABLE_PROMPT_EMITTED" for row in blocker.get("candidate_blocker_rows", [])):
            failures.append("blocker pursuit: not all blockers reduced to exact prompt")

        saturation_text = artifact_path("SATURATION_SELF_RED_TEAM", ".md").read_text(encoding="utf-8")
        for phrase in ["OB-only", "accepted 40", "blocker classification", "anti-boxing", "No."]:
            if phrase not in saturation_text:
                failures.append(f"saturation: missing {phrase}")

        parallel = loaded["PARALLELIZATION_PLAN"]
        if len(parallel.get("wave_1_parallelizable_route_packs", [])) != 3:
            failures.append("parallelization: wave 1 should include three route packs")
        if len(parallel.get("wave_2_parallelizable_route_packs_after_wave_1_source_hash_contracts", [])) != 3:
            failures.append("parallelization: wave 2 should include three route packs")

        completion = loaded["COMPLETION_AUDIT"]
        non_commit = [
            row
            for row in completion.get("prompt_to_artifact_checklist", [])
            if row.get("requirement") not in {"standalone verifier and focused tests pass", "scoped artifacts committed"}
        ]
        if not all(row.get("satisfied") is True for row in non_commit):
            failures.append("completion: a prompt-to-artifact checklist row before verification is unsatisfied")

    syntax = syntax_parse([ROUTE_DIR / name for name in REQUIRED_PY if (ROUTE_DIR / name).exists()])
    if not syntax["ok"]:
        failures.extend(f"syntax: {failure}" for failure in syntax["failures"])
    git_status = scoped_git_status()
    if not git_status["no_scoped_forbidden_live_surface"]:
        failures.append("git status: scoped forbidden live-surface file present")
    if not git_status["no_scoped_raw_market_blob"]:
        failures.append("git status: scoped raw market blob present")

    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "candidate_count_verified": len(loaded.get("ROUTE_FAMILY_LEDGER", {}).get("rows", [])),
        "route_pack_count_verified": loaded.get("RANKED_ROUTE_PLAN", {}).get("route_pack_count"),
        "overflow_count_verified": loaded.get("EXPANSION_OVERFLOW_LEDGER", {}).get("overflow_count"),
        "accepted_40_overlap_verified": loaded.get("DENOMINATOR_QUARANTINE_PROOF", {}).get("candidate_overlap_count"),
        "syntax_parse": syntax,
        "git_status": git_status,
        **SAFE_FLAGS,
    }
    result["can_mark_goal_complete"] = result["ok"] and (mark_focused_tests_ok or bool(loaded.get("COMPLETION_AUDIT", {}).get("focused_tests_ok")))

    write_json(artifact_path("VERIFICATION_RESULT"), result)
    artifact_path("VERIFICATION_RESULT", ".md").write_text(
        "\n".join(
            [
                "# Verification Result",
                "",
                f"- **route_id:** `{ROUTE_ID}`",
                f"- **evidence_class:** `{EVIDENCE_CLASS}`",
                f"- **ok:** `{str(result['ok']).lower()}`",
                f"- **failure_count:** `{result['failure_count']}`",
                "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
                "- **validation_safe:** `false`",
                "- **outcome_review_opened:** `false`",
                "- **live_effect:** `false`",
                "",
                "```json",
                json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    refresh_completion(result, mark_focused_tests_ok=mark_focused_tests_ok)
    refresh_output_manifest(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
