"""Verifier for the Blocked17 LTF as-of path attachment G12 audit."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import build_g12_scid_blocked17_ltf_asof_path_attachment_repair_audit_2026_05_13 as builder


RESULT_JSON = f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE}.json"
RESULT_MD = f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE}.md"
FOCUSED_JSON = f"{builder.PREFIX}_FOCUSED_TEST_RESULT_{builder.DATE}.json"
FOCUSED_MD = f"{builder.PREFIX}_FOCUSED_TEST_RESULT_{builder.DATE}.md"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_flag_errors(name: str, payload: dict[str, Any]) -> list[str]:
    errors = []
    for key, expected in builder.SAFE_FLAGS.items():
        if payload.get(key) != expected:
            errors.append(f"{name}: {key} expected {expected!r}, got {payload.get(key)!r}")
    if payload.get("route_id") != builder.ROUTE_ID:
        errors.append(f"{name}: route_id mismatch")
    if payload.get("evidence_class") != builder.EVIDENCE_CLASS:
        errors.append(f"{name}: evidence_class mismatch")
    return errors


def scoped_git_status() -> dict[str, Any]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=builder.REPO_ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    entries = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:] if len(line) > 3 else line
        norm = path.replace("\\", "/")
        scoped = norm.startswith(
            "research/science_program_2026_05/06_outcome_testing/"
            "g12_scid_blocked17_ltf_asof_path_attachment_repair_audit/"
        )
        allowed_context_preflight = norm == ".context/LIVE_STATE.md"
        forbidden_live_surface = norm.startswith(("src/", "prompts/", "config/", "run_agent.py", "start_all.bat"))
        raw_blob = Path(norm).suffix.lower() in {".parquet", ".scid", ".depth", ".zst", ".dbn", ".csv"}
        entries.append(
            {
                "raw": line,
                "path": norm,
                "scoped": scoped,
                "allowed_context_preflight": allowed_context_preflight,
                "scoped_forbidden_live_surface": scoped and forbidden_live_surface,
                "scoped_raw_market_blob": scoped and raw_blob,
            }
        )
    return {
        "entries": entries,
        "scoped_entries": [entry for entry in entries if entry["scoped"]],
        "unrelated_dirty_entry_count": len([entry for entry in entries if not entry["scoped"]]),
        "preflight_live_state_dirty": any(entry["allowed_context_preflight"] for entry in entries),
        "no_scoped_forbidden_live_surface": not any(entry["scoped_forbidden_live_surface"] for entry in entries),
        "no_scoped_raw_market_blob": not any(entry["scoped_raw_market_blob"] for entry in entries),
    }


def write_focused_result(*, source_packet_tests_ok: bool, g12_tests_ok: bool) -> None:
    payload = {
        **builder.base_payload("FOCUSED_TEST_RESULT"),
        "source_packet_focused_pytest_ok": source_packet_tests_ok,
        "g12_audit_focused_pytest_ok": g12_tests_ok,
        "source_packet_command": (
            "python -m pytest research/science_program_2026_05/06_outcome_testing/"
            "scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/"
            "test_scid_blocked17_ltf_asof_path_parser_and_candidate_attachment_2026_05_13.py -q"
        ),
        "g12_audit_command": (
            "python -m pytest research/science_program_2026_05/06_outcome_testing/"
            "g12_scid_blocked17_ltf_asof_path_attachment_repair_audit/"
            "test_g12_scid_blocked17_ltf_asof_path_attachment_repair_audit_2026_05_13.py -q"
        ),
    }
    builder.write_json(builder.ROUTE_DIR / FOCUSED_JSON, payload)
    builder.write_md(builder.ROUTE_DIR / FOCUSED_MD, "Focused Test Result", payload)


def update_manifest_with_verifier_outputs() -> None:
    manifest_path = builder.ROUTE_DIR / builder.JSON_OUTPUTS["manifest"]
    if not manifest_path.exists():
        return
    manifest = read_json(manifest_path)
    by_path = {row["path"]: row for row in manifest.get("artifacts", [])}
    for name in (FOCUSED_JSON, FOCUSED_MD, RESULT_JSON, RESULT_MD):
        path = builder.ROUTE_DIR / name
        if path.exists():
            by_path[builder.rel(path)] = builder.file_audit(path)
    manifest["artifacts"] = sorted(by_path.values(), key=lambda row: row["path"])
    manifest["artifact_count"] = len(manifest["artifacts"])
    manifest.setdefault("required_outputs_present", {})["verification_result"] = (builder.ROUTE_DIR / RESULT_JSON).exists()
    manifest["verification_outputs_manifested_by_verifier"] = True
    builder.write_json(manifest_path, manifest)
    builder.write_md(builder.ROUTE_DIR / builder.MD_OUTPUTS["manifest"], "Output Manifest", manifest)


def verify(*, source_packet_tests_ok: bool, g12_tests_ok: bool) -> dict[str, Any]:
    write_focused_result(source_packet_tests_ok=source_packet_tests_ok, g12_tests_ok=g12_tests_ok)
    failures: list[str] = []
    payloads: dict[str, Any] = {}
    for key, filename in builder.JSON_OUTPUTS.items():
        if key == "manifest":
            continue
        path = builder.ROUTE_DIR / filename
        if not path.exists():
            failures.append(f"missing audit artifact {filename}")
            continue
        payload = read_json(path)
        payloads[key] = payload
        failures.extend(safe_flag_errors(key, payload))

    for key in ("source_status", "parser_hash_asof", "missing_exact", "denominator_noleak", "saturation"):
        if payloads.get(key, {}).get("ok") is not True:
            failures.append(f"{key} audit not ok")

    if payloads.get("decision", {}).get("terminal_decision") != builder.TERMINAL_DECISION:
        failures.append("decision ledger did not accept the packet")
    if payloads.get("decision", {}).get("terminal_blockers"):
        failures.append("decision ledger has terminal blockers")

    completion = payloads.get("completion", {})
    if completion.get("completion_standard_satisfied") is not True:
        failures.append("completion audit standard not satisfied")
    if completion.get("missing_incomplete_or_weakly_verified_requirements"):
        failures.append("completion audit has missing or weak requirements")

    packet_verification = read_json(builder.PACKET_INPUTS["packet_verification"])
    if packet_verification.get("ok") is not True:
        failures.append("source packet verification result is not ok")
    if packet_verification.get("source_exists_field_row_count") != 78:
        failures.append("source packet verifier did not confirm 78 field rows")
    if not source_packet_tests_ok:
        failures.append("source packet focused pytest not marked ok")
    if not g12_tests_ok:
        failures.append("G12 focused pytest not marked ok")

    git_status = scoped_git_status()
    if not git_status["no_scoped_forbidden_live_surface"]:
        failures.append("scoped diff touches forbidden live surface")
    if not git_status["no_scoped_raw_market_blob"]:
        failures.append("scoped diff contains raw market blob")

    result = {
        **builder.base_payload("VERIFICATION_RESULT"),
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "terminal_decision": payloads.get("decision", {}).get("terminal_decision"),
        "source_packet_verification_ok": packet_verification.get("ok") is True,
        "source_packet_focused_pytest_ok": source_packet_tests_ok,
        "g12_audit_focused_pytest_ok": g12_tests_ok,
        "source_exists_field_row_count": payloads.get("parser_hash_asof", {}).get("attachment_row_count"),
        "source_exists_card_count": payloads.get("source_status", {}).get("source_exists_card_count"),
        "blocked17_denominator_count": payloads.get("denominator_noleak", {}).get("included_blocked17_count"),
        "scoped_git_status": git_status,
    }
    builder.write_json(builder.ROUTE_DIR / RESULT_JSON, result)
    builder.write_md(builder.ROUTE_DIR / RESULT_MD, "Verification Result", result)
    update_manifest_with_verifier_outputs()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-source-packet-tests-ok", action="store_true")
    parser.add_argument("--mark-g12-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(
        source_packet_tests_ok=args.mark_source_packet_tests_ok,
        g12_tests_ok=args.mark_g12_tests_ok,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
