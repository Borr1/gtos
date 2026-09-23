"""The prospective half of the trial-budget ledger.

`WAVE_6_WORKING_AGREEMENT.md` §3 makes this mandatory and insists it is not a brake, so
the two properties under test are (a) it records what was evaluated, faithfully, and
(b) it can never fail a caller's measurement — a ledger that raises would become the brake
the agreement forbids.
"""

from __future__ import annotations

import json
import os

import pytest

from src.research_infra.validation_integrity.trial_budget_ledger import (
    DSR_TRIAL_FLOOR,
    TrialLedger,
    measured_n_trials,
    variant_hash,
)


def test_records_and_summarises(tmp_path):
    p = tmp_path / "TRIAL_LEDGER.jsonl"
    led = TrialLedger(p, session="AA", run_id="r1")
    for stop in (1.0, 1.25, 1.5, 1.75, 2.0):
        led.record(mechanism="stop_width_sweep", sleeve="fx_jpy",
                   variant={"stop_atr": stop}, window="2024-2026",
                   outcome="evaluated", metric=0.01 * stop, metric_name="oos_mean_r")
    led.record(mechanism="stop_width_sweep", sleeve="fx_jpy",
               variant={"stop_atr": 1.5}, window="2024-2026", outcome="rejected")
    s = led.summary()
    assert s["n_trials"] == 6
    # a re-look at the SAME variant is a second chance to be wrong: counted in n_trials,
    # not in distinct variants.
    assert s["n_distinct_variants"] == 5
    assert s["by_mechanism"]["stop_width_sweep"] == 6
    assert s["by_session"]["AA"] == 6
    assert s["by_outcome"] == {"evaluated": 5, "rejected": 1}
    assert s["write_errors_this_process"] == 0

    lines = p.read_text().strip().split("\n")
    assert len(lines) == 6
    row = json.loads(lines[0])
    assert row["schema"] == "gtos.validation_integrity.trial_ledger_row.v1"
    assert row["session"] == "AA" and row["run_id"] == "r1"
    assert row["variant"] == {"stop_atr": 1.0}


def test_is_append_only_across_instances(tmp_path):
    p = tmp_path / "L.jsonl"
    TrialLedger(p, session="AA").record(mechanism="m", sleeve="s")
    TrialLedger(p, session="AB").record(mechanism="m", sleeve="s2")
    TrialLedger(p, session="AG").record(mechanism="m", sleeve="s3")
    s = TrialLedger(p, autocreate=False).summary()
    assert s["n_trials"] == 3
    assert set(s["by_session"]) == {"AA", "AB", "AG"}


def test_never_raises_into_a_callers_measurement(tmp_path):
    """A ledger that can fail a run is a brake, and §3 says it must not be one."""
    d = tmp_path / "ro"
    d.mkdir()
    p = d / "L.jsonl"
    led = TrialLedger(p, session="AA")
    os.chmod(d, 0o500)  # read+execute only: the append will fail
    try:
        row = led.record(mechanism="m", sleeve="s")  # must NOT raise
        assert row["mechanism"] == "m"
        assert led.summary()["write_errors_this_process"] >= 1
    finally:
        os.chmod(d, 0o700)


def test_unparseable_rows_are_counted_not_fatal(tmp_path):
    p = tmp_path / "L.jsonl"
    led = TrialLedger(p, session="AA")
    led.record(mechanism="m", sleeve="s")
    with p.open("a") as fh:
        fh.write('{"torn": tru\n')
    led.record(mechanism="m", sleeve="s2")
    s = led.summary()
    assert s["n_trials"] == 2
    assert s["n_unparseable_rows"] == 1


def test_variant_hash_is_order_independent_and_stable():
    a = variant_hash({"stop": 1.5, "session": "london"})
    b = variant_hash({"session": "london", "stop": 1.5})
    assert a == b and len(a) == 12
    assert variant_hash({"stop": 1.6, "session": "london"}) != a


def test_measured_n_trials_takes_the_max_and_names_its_basis(tmp_path):
    p = tmp_path / "L.jsonl"
    led = TrialLedger(p, session="AA")
    for i in range(5):
        led.record(mechanism="m", sleeve=f"s{i}")

    # small ledger, no scan: the FLOOR still governs, because the ledger only counts from
    # the day it was wired and the estate's own history predates it.
    m = measured_n_trials(ledger_paths=[p])
    assert m["n_trials"] == DSR_TRIAL_FLOOR
    assert m["basis"] == "floor"
    assert m["n_prospective_look_events"] == 5

    # a retrospective scan that exceeds the floor wins
    m2 = measured_n_trials(ledger_paths=[p],
                           scan_summary={"recommended_n_trials_for_dsr": 400})
    assert m2["n_trials"] == 400 and m2["basis"] == "retrospective_scan"

    # a big campaign ledger wins over both
    for i in range(600):
        led.record(mechanism="sweep", sleeve="x", variant={"k": i})
    m3 = measured_n_trials(ledger_paths=[p],
                           scan_summary={"recommended_n_trials_for_dsr": 400})
    assert m3["n_trials"] == 605 and m3["basis"] == "prospective_ledger"


def test_missing_ledger_reads_as_zero_not_an_error(tmp_path):
    m = measured_n_trials(ledger_paths=[tmp_path / "nope.jsonl"])
    assert m["n_prospective_look_events"] == 0
    assert m["n_trials"] == DSR_TRIAL_FLOOR


def test_unknown_outcome_is_normalised_rather_than_rejected(tmp_path):
    p = tmp_path / "L.jsonl"
    led = TrialLedger(p, session="AA")
    r = led.record(mechanism="m", sleeve="s", outcome="banana")
    assert r["outcome"] == "evaluated"
