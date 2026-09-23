"""Verification runner for the scoped G12 G3/G6 packet-builder audit."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
DATE_STAMP = "2026-05-07"
OUT = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_command(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": " ".join(args),
        "returncode": proc.returncode,
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(path: Path, data: dict[str, Any]) -> None:
    lines = [
        "# G12 G3/G6 Verification Results - 2026-05-07",
        "",
        f"Promotion verdict: `{data['promotion_verdict']}`",
        f"Validation safe: `{data['validation_safe']}`",
        f"Outcome review opened: `{data['outcome_review_opened']}`",
        f"Overall status: `{data['summary']['overall_status']}`",
        "",
        "## Commands",
        "",
        "| Status | Command |",
        "| --- | --- |",
    ]
    for row in data["commands"]:
        lines.append(f"| `{row['status']}` | `{row['command']}` |")
    lines.extend(["", "## Static Checks", "", "| Status | Check | Evidence |", "| --- | --- | --- |"])
    for row in data["static_checks"]:
        lines.append(f"| `{row['status']}` | {row['check']} | {row['evidence']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def static_checks() -> list[dict[str, Any]]:
    checks = []
    required_json = [
        OUT / f"G12_G3_G6_PACKET_BUILDER_DECISION_LEDGER_{DATE_STAMP}.json",
        OUT / f"G12_G3_G6_ACCEPTED_PACKET_SHORTLIST_{DATE_STAMP}.json",
        OUT / f"G12_G3_G6_BLOCKED_REJECTED_QUESTION_LEDGER_{DATE_STAMP}.json",
        OUT / f"G12_G3_G6_LEAKAGE_NOLEAK_REVIEW_{DATE_STAMP}.json",
        OUT / f"G12_G3_G6_DUPLICATE_DENOMINATOR_REVIEW_{DATE_STAMP}.json",
        OUT / f"G12_G3_G6_LABEL_FAMILY_REVIEW_{DATE_STAMP}.json",
        OUT / f"G12_G3_G6_SOURCE_HASH_REPRODUCIBILITY_REVIEW_{DATE_STAMP}.json",
        OUT / f"G12_G3_G6_SAME_BAR_TIMING_REVIEW_{DATE_STAMP}.json",
        OUT / f"G12_G3_G6_SOURCE_FRESHNESS_STALENESS_REVIEW_{DATE_STAMP}.json",
        OUT / f"G12_G3_G6_NEXT_LANE_RECOMMENDATION_{DATE_STAMP}.json",
        OUT / f"G12_G3_G6_COMPLETION_AUDIT_{DATE_STAMP}.json",
    ]
    parsed = []
    for path in required_json:
        try:
            parsed.append((path, read_json(path)))
        except Exception as exc:  # pragma: no cover - diagnostic path
            checks.append({"check": f"parse {rel(path)}", "status": "FAIL", "evidence": repr(exc)})
    if not checks:
        checks.append({"check": "required JSON artifacts parse", "status": "PASS", "evidence": f"{len(parsed)} files"})

    unsafe_hits = []
    for path, data in parsed:
        if isinstance(data, dict):
            if data.get("promotion_verdict") != PROMOTION_VERDICT:
                unsafe_hits.append(f"{rel(path)} promotion_verdict={data.get('promotion_verdict')}")
            if data.get("validation_safe") is not False:
                unsafe_hits.append(f"{rel(path)} validation_safe={data.get('validation_safe')}")
            if data.get("outcome_review_opened") is not False:
                unsafe_hits.append(f"{rel(path)} outcome_review_opened={data.get('outcome_review_opened')}")
    checks.append(
        {
            "check": "no-promotion and unsafe flags preserved",
            "status": "PASS" if not unsafe_hits else "FAIL",
            "evidence": "no unsafe hits" if not unsafe_hits else "; ".join(unsafe_hits[:20]),
        }
    )

    decision = read_json(OUT / f"G12_G3_G6_PACKET_BUILDER_DECISION_LEDGER_{DATE_STAMP}.json")
    decisions = decision.get("packet_decisions", [])
    checks.append(
        {
            "check": "decision coverage",
            "status": "PASS" if len(decisions) == 8 else "FAIL",
            "evidence": f"{len(decisions)} packet decisions",
        }
    )
    checks.append(
        {
            "check": "no forbidden record keys",
            "status": "PASS"
            if read_json(OUT / f"G12_G3_G6_LEAKAGE_NOLEAK_REVIEW_{DATE_STAMP}.json").get("total_forbidden_record_key_hits") == 0
            else "FAIL",
            "evidence": f"hits={read_json(OUT / f'G12_G3_G6_LEAKAGE_NOLEAK_REVIEW_{DATE_STAMP}.json').get('total_forbidden_record_key_hits')}",
        }
    )
    checks.append(
        {
            "check": "source hash recomputation",
            "status": "PASS"
            if read_json(OUT / f"G12_G3_G6_SOURCE_HASH_REPRODUCIBILITY_REVIEW_{DATE_STAMP}.json").get("failure_count") == 0
            else "FAIL",
            "evidence": f"failure_count={read_json(OUT / f'G12_G3_G6_SOURCE_HASH_REPRODUCIBILITY_REVIEW_{DATE_STAMP}.json').get('failure_count')}",
        }
    )
    checks.append(
        {
            "check": "no result/outcome execution flags",
            "status": "PASS"
            if not any(
                decision.get(key)
                for key in [
                    "outcomes_run",
                    "r_result_values_inspected",
                    "broker_actual_r_inspected",
                    "blocked_packet_outcomes_inspected",
                    "paid_network_api_databento_mt5_calls",
                    "live_surface_changes",
                ]
            )
            else "FAIL",
            "evidence": "all execution/opening flags false",
        }
    )
    return checks


def main() -> None:
    commands = [
        [sys.executable, "-m", "py_compile", rel(OUT / f"build_g12_g3_g6_packet_builder_audit_{DATE_STAMP.replace('-', '_')}.py")],
        [sys.executable, "-m", "py_compile", rel(OUT / f"verify_g12_g3_g6_packet_builder_audit_{DATE_STAMP.replace('-', '_')}.py")],
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/build_otb2r_g3_geometry_input_packet_builders_2026_05_07.py",
        ],
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/build_otb2r_g6_local_ohlc_momentum_reversion_packets_2026_05_07.py",
        ],
        [
            sys.executable,
            "-m",
            "pytest",
            rel(OUT / f"test_g12_g3_g6_packet_builder_audit_{DATE_STAMP.replace('-', '_')}.py"),
            "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/test_otb2r_g6_local_ohlc_momentum_reversion_packets_2026_05_07.py",
            "tests/test_science_goal_program.py",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
    ]
    command_results = [run_command(args) for args in commands]
    checks = static_checks()
    overall = "PASS" if all(row["status"] == "PASS" for row in command_results + checks) else "FAIL"
    data = {
        "artifact_family": "G12_G3_G6_VERIFICATION_RESULTS",
        "generated_at_utc": now_utc(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "commands": command_results,
        "static_checks": checks,
        "summary": {
            "overall_status": overall,
            "command_failures": [row["command"] for row in command_results if row["status"] != "PASS"],
            "static_check_failures": [row["check"] for row in checks if row["status"] != "PASS"],
        },
    }
    write_json(OUT / f"G12_G3_G6_VERIFICATION_RESULTS_{DATE_STAMP}.json", data)
    write_md(OUT / f"G12_G3_G6_VERIFICATION_RESULTS_{DATE_STAMP}.md", data)
    print(json.dumps(data["summary"], indent=2, sort_keys=True))
    raise SystemExit(0 if overall == "PASS" else 1)


if __name__ == "__main__":
    main()
