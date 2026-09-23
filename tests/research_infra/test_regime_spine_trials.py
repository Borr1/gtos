"""The trial ledger has to be countable by the instrument that consumes it.

`WAVE_6_WORKING_AGREEMENT.md` section 3 requires every variant to be logged so admission
statistics deflate against a MEASURED trial count instead of `gate.py:47-48`'s assumed
floor of 128 — a number its own docstring calls one "nobody measured".

`validation_integrity/trial_budget_ledger.py` is a retrospective scanner and Session AA
owns it this wave, so this appender writes a summary the existing scanner already counts
rather than editing it. The load-bearing test is the last one: build the ledger over a
directory holding this session's summary and check `recommended_n_trials_for_dsr` actually
moves. A logging mechanism nobody's deflation reads is decoration.
"""

from __future__ import annotations

import json

from src.research_infra.regime_spine.trials import TrialLedger
from src.research_infra.validation_integrity.trial_budget_ledger import (
    DSR_TRIAL_FLOOR,
    build_trial_budget_ledger,
)


def test_rows_are_one_per_variant_and_carry_the_selectable_metric(tmp_path):
    led = TrialLedger(tmp_path / "l.jsonl", session="TEST")
    for i in range(3):
        led.log("fam", "sleeve_a", f"v{i}", {"k": i}, {"mean_r_net": 0.1 * i})
    led.close()
    rows = [json.loads(x) for x in (tmp_path / "l.jsonl").read_text().splitlines()]
    assert len(rows) == 3
    assert [r["seq"] for r in rows] == [1, 2, 3]
    assert all(r["session"] == "TEST" for r in rows)
    assert rows[2]["metrics"]["mean_r_net"] == 0.2
    assert rows[2]["params"] == {"k": 2}


def test_append_mode_resumes_the_count_across_drivers(tmp_path):
    p = tmp_path / "l.jsonl"
    a = TrialLedger(p, session="TEST")
    a.log("f", "s", "v1", {})
    a.close()
    b = TrialLedger(p, session="TEST", append=True)
    assert b.n_trials == 1, "a second driver must not restart the count"
    b.log("f", "s", "v2", {})
    b.close()
    assert len(p.read_text().splitlines()) == 2
    assert [json.loads(x)["seq"] for x in p.read_text().splitlines()] == [1, 2]


def test_non_append_truncates_so_a_rerun_does_not_double_count(tmp_path):
    p = tmp_path / "l.jsonl"
    a = TrialLedger(p, session="TEST")
    a.log("f", "s", "v1", {})
    a.close()
    b = TrialLedger(p, session="TEST")
    b.log("f", "s", "v1", {})
    b.close()
    assert len(p.read_text().splitlines()) == 1


def test_summary_is_counted_by_the_existing_scanner_without_editing_it(tmp_path):
    """The whole point: the measured count must reach `recommended_n_trials_for_dsr`."""
    route = tmp_path / "route"
    route.mkdir()
    led = TrialLedger(route / "L.jsonl", session="TEST")
    n = DSR_TRIAL_FLOOR + 37
    for i in range(n):
        led.log("sweep", "sleeve_a", f"v{i}", {"i": i}, {"mean_r_net": 0.0})
    led.write_summary(route / "AB_TRIAL_BUDGET_RESULT.json")
    led.close()

    summary = build_trial_budget_ledger(str(route), str(tmp_path / "led.jsonl"),
                                        summary_path=str(tmp_path / "sum.json"))
    assert summary["recommended_n_trials_for_dsr"] >= n, (
        "the session's measured trial count did not reach the DSR deflation — the "
        "appender and the scanner are not connected")
    assert summary["recommended_n_trials_for_dsr"] > DSR_TRIAL_FLOOR


def test_a_session_below_the_floor_does_not_lower_it(tmp_path):
    """Deflation must never get weaker because a session was small."""
    route = tmp_path / "route"
    route.mkdir()
    led = TrialLedger(route / "L.jsonl", session="TEST")
    led.log("sweep", "s", "v1", {})
    led.write_summary(route / "AB_TRIAL_BUDGET_RESULT.json")
    led.close()
    summary = build_trial_budget_ledger(str(route), str(tmp_path / "led.jsonl"),
                                        summary_path=str(tmp_path / "sum.json"))
    assert summary["recommended_n_trials_for_dsr"] == DSR_TRIAL_FLOOR


def test_summary_records_the_counting_rule_it_used(tmp_path):
    led = TrialLedger(tmp_path / "l.jsonl", session="TEST")
    led.log("a", "s", "v", {})
    led.log("b", "s", "v", {})
    s = led.write_summary(tmp_path / "AB_TRIAL_BUDGET_RESULT.json")
    led.close()
    assert s["trials_by_family"] == {"a": 1, "b": 1}
    assert "not trials" in s["counting_rule"]
    assert s["n_trials"] == s["n_variants"] == 2
