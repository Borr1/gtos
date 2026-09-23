"""Known-answer tests for the Trial-Budget Ledger builder.

Run:
    /opt/homebrew/bin/python3 -m pytest tests/research_infra/test_vig_trial_budget.py -q
or standalone:
    /opt/homebrew/bin/python3 tests/research_infra/test_vig_trial_budget.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    build_trial_budget_ledger,
)


def _write(p: Path, obj) -> None:
    p.write_text(json.dumps(obj), encoding="utf-8")


def _build_fixture(tmp: Path):
    """3 fake RESULT.json:
    1) references forward / 2026  -> scored_against_forward True, no trial count
    2) has 'n_candidates': 50     -> not forward, embedded trial count 50
    3) plain, no forward, no count
    """
    # 1) forward-scored, with a year value too
    _write(
        tmp / "ALPHA_RESULT.json",
        {"forward_all": {"n": 49, "win": 77.6}, "asof": "2026-06-12"},
    )
    # 2) config sweep, NOT forward (no forward tokens, no 2025/2026 anywhere)
    _write(
        tmp / "BETA_RESULT.json",
        {"n_candidates": 50, "best": {"mean_R": 0.31, "n": 120}},
    )
    # 3) plain in-sample-only, no forward token, no config count
    _write(
        tmp / "GAMMA_RESULT.json",
        {"train_all": {"n": 200, "mean_R": -0.21, "win": 44.5}},
    )
    # a non-RESULT file that must be ignored
    _write(tmp / "NOTES.json", {"forward": True, "n_candidates": 9999})


def run_known_answer() -> dict:
    import tempfile

    failures = []
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _build_fixture(tmp)
        out = tmp / "out" / "TRIAL_BUDGET_LEDGER.jsonl"

        # default floor (128): proves recommended >= forward count and floor.
        summary = build_trial_budget_ledger(str(tmp), str(out))

        rows = [
            json.loads(ln)
            for ln in out.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        by_name = {r["filename"]: r for r in rows}

        def check(cond, msg):
            if not cond:
                failures.append(msg)

        # only the 3 *RESULT*.json files, NOTES.json ignored
        check(summary["total_result_files"] == 3,
              f"total_result_files {summary['total_result_files']} != 3")
        check(len(rows) == 3, f"jsonl rows {len(rows)} != 3")
        check("NOTES.json" not in by_name, "NOTES.json should be ignored")

        # forward detection
        check(by_name["ALPHA_RESULT.json"]["scored_against_forward"] is True,
              "ALPHA must be scored_against_forward")
        check(by_name["BETA_RESULT.json"]["scored_against_forward"] is False,
              "BETA must NOT be scored_against_forward")
        check(by_name["GAMMA_RESULT.json"]["scored_against_forward"] is False,
              "GAMMA must NOT be scored_against_forward")
        check(summary["n_scored_against_forward"] == 1,
              f"n_scored_against_forward {summary['n_scored_against_forward']} != 1")

        # embedded trial count: only BETA contributes 50; bare 'n' NOT counted
        check(by_name["BETA_RESULT.json"]["embedded_trial_count"] == 50,
              f"BETA embedded {by_name['BETA_RESULT.json']['embedded_trial_count']} != 50")
        check(by_name["ALPHA_RESULT.json"]["embedded_trial_count"] == 0,
              "ALPHA embedded must be 0 (bare 'n' is trade count, not a trial)")
        check(by_name["GAMMA_RESULT.json"]["embedded_trial_count"] == 0,
              "GAMMA embedded must be 0 (bare 'n' is trade count, not a trial)")
        check(summary["sum_embedded_trial_counts"] == 50,
              f"sum_embedded {summary['sum_embedded_trial_counts']} != 50")

        # recommended >= forward count, and respects the 128 floor by default
        check(summary["recommended_n_trials_for_dsr"] >= summary["n_scored_against_forward"],
              "recommended must be >= forward count")
        check(summary["recommended_n_trials_for_dsr"] == 128,
              f"recommended {summary['recommended_n_trials_for_dsr']} != 128 (floor)")

        # with a low floor, the embedded sweep (50) must drive the recommendation,
        # proving the max() logic isn't just always returning the floor.
        out2 = tmp / "out2" / "L.jsonl"
        summary2 = build_trial_budget_ledger(str(tmp), str(out2), dsr_floor=2)
        check(summary2["recommended_n_trials_for_dsr"] == 50,
              f"low-floor recommended {summary2['recommended_n_trials_for_dsr']} != 50")
        check(summary2["recommended_n_trials_for_dsr"] >= summary2["n_scored_against_forward"],
              "low-floor recommended must be >= forward count")

        # summary file written alongside
        sp = Path(summary["summary_path"])
        check(sp.exists(), "summary JSON not written")

    return {"failures": failures}


# pytest entrypoint
def test_trial_budget_known_answer():
    res = run_known_answer()
    assert not res["failures"], "KNOWN-ANSWER FAILURES:\n" + "\n".join(res["failures"])


if __name__ == "__main__":
    res = run_known_answer()
    if res["failures"]:
        print("FAIL")
        for f in res["failures"]:
            print("  -", f)
        sys.exit(1)
    print("PASS: trial-budget known-answer test")
