from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROUTE = (
    Path(__file__).resolve().parents[1]
    / "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
)
SCRIPT = ROUTE / "repair_broad_replay_terminal_cost_aliases.py"


def load_repair_module():
    name = "repair_broad_replay_terminal_cost_aliases_test_module"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_staged_repair_changes_only_mismatched_alias_fields(tmp_path: Path) -> None:
    repair = load_repair_module()
    path = tmp_path / "terminal.jsonl"
    exact_raw = (
        b'{"candidate_id":"exact", "expected_cost_r":0.05, "cost_r":0.05}\n'
    )
    mismatch = {
        "candidate_id": "diagnostic-counterfactual",
        "decision_time_utc": "2026-06-04T07:30:00Z",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "expected_cost_r": 0.08456887,
        "cost_r": 0.034568865303,
        "broker_pretrade_cost_r": 0.034568865303,
        "miss_reason": "selected_candidate_diagnostic_fill_realism_counterfactual",
        "opportunity_net_proxy_r": 1.25,
    }
    mismatch_raw = (json.dumps(mismatch) + "\n").encode("utf-8")
    before = exact_raw + mismatch_raw
    path.write_bytes(before)

    staged, result = repair.staged_repair(path)

    assert staged is not None
    try:
        output = staged.read_bytes()
        output_lines = output.splitlines(keepends=True)
        assert output_lines[0] == exact_raw
        changed = json.loads(output_lines[1])
        assert changed["expected_cost_r"] == 0.08456887
        assert changed["cost_r"] == 0.08456887
        assert changed["broker_pretrade_cost_r"] == 0.034568865303
        assert changed["opportunity_net_proxy_r"] == 1.25
        assert changed["candidate_cost_alias_status"] == "materialized_exact_alias"
        assert changed["candidate_cost_alias_conflict"] == {
            "expected_cost_r": 0.08456887,
            "cost_r": 0.034568865303,
        }
        assert repair.semantic_projection(changed) == repair.semantic_projection(
            mismatch
        )
        assert result["row_count"] == 2
        assert result["changed_rows"] == 1
        assert result["unchanged_rows_byte_preserved"] == 1
        assert result["before_sha256"] == hashlib.sha256(before).hexdigest()
        assert result["after_sha256"] == hashlib.sha256(output).hexdigest()
    finally:
        staged.unlink(missing_ok=True)


def test_main_fails_closed_before_commit_on_unexpected_change_count(
    tmp_path: Path, monkeypatch
) -> None:
    repair = load_repair_module()
    prefix = "BROAD_LIVE_AS_IF_REPLAY_FIXTURE"
    monkeypatch.setattr(repair, "ROUTE", tmp_path)
    paths = [tmp_path / f"{prefix}_{suffix}" for suffix in repair.TERMINAL_LEDGER_SUFFIXES]
    mismatch = {
        "candidate_id": "mismatch",
        "expected_cost_r": 0.08,
        "cost_r": 0.03,
        "broker_pretrade_cost_r": 0.03,
    }
    original = (json.dumps(mismatch) + "\n").encode("utf-8")
    paths[0].write_bytes(original)
    paths[1].write_text(
        json.dumps({"candidate_id": "order", "expected_cost_r": 0.04, "cost_r": 0.04})
        + "\n",
        encoding="utf-8",
    )
    paths[2].write_text(
        json.dumps({"candidate_id": "trade", "expected_cost_r": 0.02, "cost_r": 0.02})
        + "\n",
        encoding="utf-8",
    )
    original_bytes = [path.read_bytes() for path in paths]
    monkeypatch.setattr(
        sys,
        "argv",
        [str(SCRIPT), "--broad-prefix", prefix, "--expected-changes", "2"],
    )

    with pytest.raises(ValueError, match="expected=2 actual=1"):
        repair.main()

    assert [path.read_bytes() for path in paths] == original_bytes
    assert not list(tmp_path.glob("*.cost-alias-repair.tmp"))
    assert not (
        tmp_path / f"{prefix}_TERMINAL_CANDIDATE_COST_ALIAS_REPAIR_SUMMARY.json"
    ).exists()

    monkeypatch.setattr(
        sys,
        "argv",
        [str(SCRIPT), "--broad-prefix", prefix, "--expected-changes", "1"],
    )
    assert repair.main() == 0

    repaired = json.loads(paths[0].read_text(encoding="utf-8"))
    assert repaired["expected_cost_r"] == 0.08
    assert repaired["cost_r"] == 0.08
    assert repaired["broker_pretrade_cost_r"] == 0.03
    summary = json.loads(
        (
            tmp_path
            / f"{prefix}_TERMINAL_CANDIDATE_COST_ALIAS_REPAIR_SUMMARY.json"
        ).read_text(encoding="utf-8")
    )
    assert summary["changed_rows"] == 1
    assert summary["row_count"] == 3
    assert summary["behavior_fields_changed"] is False
    assert summary["broker_live_authority"] is False
    assert summary["final_selection_claim"] is False
