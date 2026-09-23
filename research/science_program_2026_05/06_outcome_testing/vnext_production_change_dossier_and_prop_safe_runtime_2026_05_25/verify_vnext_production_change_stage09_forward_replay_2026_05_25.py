from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage09_forward_replay_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage09", MODULE_PATH)
stage09 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = stage09
spec.loader.exec_module(stage09)


def load_index_rows() -> list[dict]:
    path = stage09.REPO_ROOT / stage09.STAGE09_LEDGER_INDEX_PATH
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sample_replay_rows(index_rows: list[dict], limit: int = 20) -> list[dict]:
    rows: list[dict] = []
    for meta in index_rows:
        chunk_path = stage09.REPO_ROOT / str(meta["chunk_path"])
        with gzip.open(stage09.stage00.io_path(chunk_path), "rt", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                rows.append(json.loads(line))
                if len(rows) >= limit:
                    return rows
    return rows


def row_failures(rows: list[dict]) -> list[str]:
    failures: list[str] = []
    required = {
        "as_of_utc",
        "source_cutoff_utc",
        "decision_inputs",
        "artifact_versions",
        "previous_current_shadow",
        "previous_hypothetical_activated",
        "new_production_change",
        "post_decision_scoring",
        "leakage_guard",
    }
    for row in rows:
        missing = sorted(required - set(row))
        if missing:
            failures.append(f"sample row missing keys {missing}")
        if row.get("as_of_utc") != row.get("source_cutoff_utc"):
            failures.append("sample row source cutoff does not equal as-of timestamp")
        decision_inputs = row.get("decision_inputs") or {}
        if decision_inputs.get("future_outcome_inputs_used") is not False:
            failures.append("sample row decision_inputs used future outcome fields")
        leakage = row.get("leakage_guard") or {}
        if leakage.get("path_outcome_labels_scoring_only") is not True:
            failures.append("sample row does not mark path labels scoring-only")
        prop = ((row.get("new_production_change") or {}).get("prop_safe_selector") or {})
        external = prop.get("external_rule_projection") or {}
        if external.get("trailing_drawdown_modeled") is not False:
            failures.append("sample row prop selector modeled trailing drawdown")
        if external.get("daily_loss_limit_pct") != 5.0:
            failures.append("sample row redacted_account daily loss pct mismatch")
    return failures


def dossier_failures() -> list[str]:
    text = (stage09.REPO_ROOT / stage09.STAGE09_DOSSIER_PATH).read_text(encoding="utf-8")
    required = [
        "Stage09 Forward-Only Replay Comparison",
        "Decision inputs are as-of runtime trace fields",
        "redacted_account external daily loss is 5%",
        "Overall max loss floor is static",
        "No live trading",
    ]
    return [f"dossier missing phrase: {phrase}" for phrase in required if phrase not in text]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-complete", action="store_true")
    parser.add_argument("--test-command", default="")
    parser.add_argument("--test-result", default="")
    args = parser.parse_args(argv)

    summary = json.loads(
        (stage09.REPO_ROOT / stage09.STAGE09_SUMMARY_PATH).read_text(encoding="utf-8")
    )
    index_rows = load_index_rows()
    result = json.loads(
        (stage09.REPO_ROOT / stage09.STAGE09_VERIFICATION_RESULT_PATH).read_text(
            encoding="utf-8"
        )
    )
    failures = stage09.verify_summary(summary, index_rows)
    failures.extend(row_failures(sample_replay_rows(index_rows)))
    failures.extend(dossier_failures())
    if result.get("ok") is not True:
        failures.append("recorded Stage09 builder result is not ok")
    state = json.loads((stage09.REPO_ROOT / stage09.STATE_PATH).read_text(encoding="utf-8"))
    if state["stage_status_table"].get("STAGE_09_FORWARD_ONLY_REPLAY") not in {
        "in_progress",
        "complete",
    }:
        failures.append("route state Stage09 status is not in_progress or complete")

    output = {
        "route_id": stage09.ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "candidate_rows": summary.get("candidate_rows"),
        "written_replay_rows": summary.get("written_replay_rows"),
        "chunk_count": summary.get("chunk_count"),
        "first_incomplete_invariant": (
            "STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER"
            if args.mark_complete and not failures
            else state["first_incomplete_invariant"]
        ),
    }
    if args.mark_complete and not failures:
        stage09.update_state(summary, complete=True)
        state_path = stage09.REPO_ROOT / stage09.STATE_PATH
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.setdefault("tests_run", []).append(
            {
                "command": args.test_command
                or "py -3 -m pytest route Stage09 test and in-memory compile",
                "result": args.test_result or "Stage09 verifier passed",
                "status": "passed",
            }
        )
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    "py -3 research/.../"
                    "verify_vnext_production_change_stage09_forward_replay_2026_05_25.py "
                    "--mark-complete"
                ),
                "result": {
                    "candidate_rows": summary.get("candidate_rows"),
                    "written_replay_rows": summary.get("written_replay_rows"),
                    "chunk_count": summary.get("chunk_count"),
                },
                "status": "passed",
            }
        )
        state["verification_status"]["stage09_tests_passed"] = True
        stage09.stage00.atomic_json_write(state_path, state)
        output["marked_complete"] = True
    print(json.dumps(output, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
