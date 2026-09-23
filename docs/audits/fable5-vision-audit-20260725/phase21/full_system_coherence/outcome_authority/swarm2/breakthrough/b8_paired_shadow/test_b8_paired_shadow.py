"""Behavioural pins for the paired harness.

These are deliberately BEHAVIOURAL, not source-string assertions: a test that greps for a
substring passes against a wrong implementation (CLAUDE.md §6).  Every test here constructs
inputs and checks what the harness DOES with them.

Run standalone (no repo pytest config needed):

    PYTHONPATH=<repo>:<breakthrough dir> python3 -m pytest b8_paired_shadow/test_b8_paired_shadow.py -q
"""

from __future__ import annotations

import math

import pytest

from b8_paired_shadow.causality import (
    AsOf,
    CausalityRefused,
    InfoInput,
    InformationSet,
    within_day_split,
)
from b8_paired_shadow.evaluate import pairing_proof
from b8_paired_shadow.paired_stats import (
    MultiplicityLedger,
    SequentialMonitor,
    n_to_detect,
    obf_boundary,
    paired_summary,
    time_to_answer,
    z_for_two_sided_alpha,
)


# ------------------------------------------------------------------ statistics -------------
def test_identical_arms_are_inert_and_carry_no_p_value():
    """The single most important pin: an A/A pair must never produce a t."""
    s = paired_summary([0.0] * 200, [f"d{i // 5}" for i in range(200)])
    assert s.verdict == "INERT"
    assert s.p_block is None and s.t_block is None and s.t_iid is None
    assert s.discordance == 0.0


def test_near_inert_is_labelled_however_large_n():
    """3 informative rows in 1,000 must be stamped, not reported as n = 1,000."""
    deltas = [0.0] * 997 + [5.0, -4.0, 6.0]
    s = paired_summary(deltas, [f"d{i // 10}" for i in range(1000)])
    assert s.verdict == "NEAR_INERT"
    assert s.discordance == pytest.approx(0.003)
    assert any("rests on" in n for n in s.notes)


def test_concentration_is_surfaced():
    deltas = [0.0001] * 99 + [50.0]
    s = paired_summary(deltas, [f"d{i}" for i in range(100)])
    assert s.top1pct_share is not None and s.top1pct_share > 0.9
    assert any("concentration" in n for n in s.notes)


def test_selection_class_does_not_change_the_power_basis():
    """The 1/discordance^2 bug: the SD must be over ALL arrivals in both modes."""
    deltas = [0.0] * 700 + [1.0] * 300
    blocks = [f"d{i // 20}" for i in range(1000)]
    a = paired_summary(deltas, blocks, informative_only=False)
    b = paired_summary(deltas, blocks, informative_only=True)
    assert a.sd == pytest.approx(b.sd)
    assert a.mean == pytest.approx(b.mean)
    assert b.n_informative == 300 and a.n_informative == 1000


def test_block_bootstrap_widens_when_deltas_cluster_by_day():
    """Perfectly clustered days must not be priced as independent trades."""
    deltas, blocks = [], []
    for d in range(40):
        v = 1.0 if d % 2 else -1.0
        deltas += [v] * 25
        blocks += [f"day{d}"] * 25
    s = paired_summary(deltas, blocks, resamples=400)
    assert s.se_block > s.se_iid * 2, (s.se_block, s.se_iid)


def test_power_arithmetic_matches_the_declared_design():
    # n = 7.8489 (sd/effect)^2 at alpha 0.05, power 80 %.
    assert n_to_detect(1.0, 0.1) == pytest.approx(784.8932, rel=1e-6)
    t = time_to_answer(1.0, 0.1, 100.0)
    assert t["months"] == pytest.approx(7.848932, rel=1e-6)
    assert "discordance" not in t


def test_obf_boundary_is_strict_early_and_nominal_at_the_horizon():
    assert obf_boundary(1.0, 0.05) == pytest.approx(z_for_two_sided_alpha(0.05), abs=1e-3)
    assert obf_boundary(0.25, 0.05) > obf_boundary(0.5, 0.05) > obf_boundary(1.0, 0.05)
    assert obf_boundary(0.1, 0.05) > 4.0


def test_sequential_monitor_does_not_stop_on_a_nominal_z_at_low_information():
    s = paired_summary([0.05] * 40 + [-0.03] * 40, [f"d{i // 4}" for i in range(80)])
    mon = SequentialMonitor("q", planned_n=10_000)
    rec = mon.look(s)
    assert rec["information_fraction"] < 0.01
    assert rec["z_boundary_obf"] > rec["nominal_z_at_alpha"]
    assert rec["decision"] == "CONTINUE"


def test_multiplicity_family_includes_untested_arms(tmp_path):
    led = MultiplicityLedger.load(tmp_path / "led.jsonl", alpha=0.10)
    led.register("tested", question="q", dimension="d", declared_at="x", rationale="r",
                 p_value=0.02, reported=True)
    for i in range(19):
        led.register(f"declared_{i}", question="q", dimension="d", declared_at="x",
                     rationale="an arm registered and never reported is still a look")
    bh = led.benjamini_hochberg()
    assert bh["declared_family_size"] == 20
    assert bh["n_with_p_value"] == 1
    # 0.02 > 0.10 * 1/20 = 0.005, so a p that would admit alone does not admit in family.
    assert bh["results"]["tested"]["admits"] is False


def test_multiplicity_ledger_is_append_only_across_loads(tmp_path):
    p = tmp_path / "led.jsonl"
    a = MultiplicityLedger.load(p)
    a.register("arm_a", question="q", dimension="d", declared_at="x", rationale="r")
    a.flush()
    b = MultiplicityLedger.load(p)
    b.register("arm_b", question="q", dimension="d", declared_at="x", rationale="r")
    b.flush()
    assert MultiplicityLedger.load(p).benjamini_hochberg()["declared_family_size"] == 2


# ------------------------------------------------------------------ pairing proof -----------
def test_pairing_proof_variance_identity_holds_exactly():
    import random

    rng = random.Random(7)
    a = [rng.gauss(0, 1) for _ in range(500)]
    b = [x * 0.9 + rng.gauss(0, 0.3) for x in a]
    pr = pairing_proof(a, b, [y - x for x, y in zip(a, b)])
    assert pr["variance_identity_holds"] is True
    assert pr["verdict"] == "PAIRED"
    assert pr["noise_reduction_x"] > 1.0


def test_pairing_proof_flags_independent_arms_as_suspect():
    import random

    rng = random.Random(11)
    a = [rng.gauss(0, 1) for _ in range(500)]
    b = [rng.gauss(0, 1) for _ in range(500)]
    pr = pairing_proof(a, b, [y - x for x, y in zip(a, b)])
    assert pr["verdict"] == "SUSPECT_INDEPENDENT"


def test_pairing_proof_flags_identical_arms_as_inert():
    a = [1.0, -1.0, 2.0, 0.5] * 25
    pr = pairing_proof(a, list(a), [0.0] * len(a))
    assert pr["verdict"] == "INERT_ARMS"


# ------------------------------------------------------------------ causality ---------------
def test_post_decision_input_is_refused_at_declaration():
    info = InformationSet(inputs=(InfoInput("tomorrow's close", AsOf.POST_DECISION),))
    with pytest.raises(CausalityRefused):
        info.validate("bad_arm")


def test_same_day_aggregate_without_a_cutoff_is_refused():
    info = InformationSet(inputs=(
        InfoInput("day_regime_mean", AsOf.PRE_DECISION, same_day_aggregate=True),))
    with pytest.raises(CausalityRefused) as exc:
        info.validate("leaky_arm")
    assert "cutoff_discipline" in str(exc.value)


def test_same_day_aggregate_with_a_declared_cutoff_registers_and_demands_companions():
    info = InformationSet(inputs=(
        InfoInput("day_regime_mean", AsOf.PRE_DECISION, same_day_aggregate=True,
                  cutoff_discipline="strictly earlier decisions only"),))
    rec = info.validate("ok_arm")
    assert rec["verdict"] == "CAUSAL"
    assert rec["temporal_companion_required"] is True


def test_full_history_fitted_input_is_flagged_not_refused():
    info = InformationSet(inputs=(InfoInput("spread_model", AsOf.FITTED_ON_FULL_HISTORY),))
    rec = info.validate("cost_arm")
    assert rec["verdict"] == "CAUSAL_WITH_MODEL_IN_SAMPLE_FLAG"
    assert rec["fitted_on_full_history_inputs"] == ["spread_model"]


def test_arm_construction_refuses_a_future_reading_treatment():
    from b8_paired_shadow.arms import Arm

    with pytest.raises(CausalityRefused):
        Arm(name="cheat", dimension="d", rationale="r", declared_at="x",
            fn=lambda it, sub: None,
            information_set=InformationSet(
                inputs=(InfoInput("realised_r", AsOf.POST_DECISION),)))


def test_within_day_split_detects_a_late_half_only_effect():
    """The synthetic leak: an effect that exists only for late-in-day decisions."""
    deltas, instants, days = [], [], []
    for d in range(30):
        for k in range(10):
            deltas.append(0.0 if k < 5 else 1.0)
            instants.append(f"2026-01-{d + 1:02d}T{k:02d}:00:00+00:00")
            days.append(f"2026-01-{d + 1:02d}")
    out = within_day_split(deltas, instants, days)
    assert out["early_half"]["mean"] == pytest.approx(0.0)
    assert out["late_half"]["mean"] == pytest.approx(1.0)
    assert out["late_minus_early"] == pytest.approx(1.0)


def test_within_day_split_flags_a_sign_disagreement():
    deltas, instants, days = [], [], []
    for d in range(20):
        for k in range(4):
            deltas.append(-1.0 if k < 2 else 1.0)
            instants.append(f"2026-02-{d + 1:02d}T{k:02d}:00:00+00:00")
            days.append(f"2026-02-{d + 1:02d}")
    assert within_day_split(deltas, instants, days)["flag"] == "SIGN_DISAGREEMENT"


# ------------------------------------------------------------------ read-only ---------------
def test_package_contains_no_mutation_call_outside_the_declared_probe():
    from b8_paired_shadow.controls import control_read_only

    res = control_read_only()
    assert res["static_mutation_call_sites_in_package"] == []
    assert res["banned_imports_present"] == []
    assert len(res["deliberate_refusal_probes"]) == 1
    assert res["shadow_adapter_order_send_raises"]["order_send_raised"] is True


def test_preflight_refuses_rather_than_measuring_nothing(tmp_path):
    from b8_paired_shadow.live_shadow import PreflightFailed, preflight

    with pytest.raises(PreflightFailed) as exc:
        preflight(tmp_path, strict=True)
    assert "Refusing to start" in str(exc.value)


# ------------------------------------------------------------------ book layer -------------
def _mk(sleeve, symbol, bar, day="2026-01-05"):
    from b8_paired_shadow.substrate import Intent

    return Intent(sleeve, symbol, 16388, bar, 1, 1.0, 2.0, day, f"{day}T12:00:00+00:00",
                  math.nan, "x")


def test_cluster_cap_allows_same_bar_unit_members():
    """`placement_ledger.cluster_placed_today_other_bar:181` allows the SAME bar's unit."""
    from b8_paired_shadow.questions import cap_builder

    clusters = {"a": "metals", "b": "metals"}
    same_bar = [_mk("a", "XAUUSD", "2026-01-05T09:00:00+00:00"),
                _mk("b", "XAGUSD", "2026-01-05T09:00:00+00:00")]
    later_bar = [_mk("a", "XAUUSD", "2026-01-05T09:00:00+00:00"),
                 _mk("b", "XAGUSD", "2026-01-05T13:00:00+00:00")]
    cap = cap_builder(per_sleeve_symbol_day=True, per_cluster_day=True, clusters=clusters)
    assert len(cap(same_bar)) == 2, "same-bar unit members must both place"
    assert len(cap(later_bar)) == 1, "a later-bar same-cluster re-fire must be blocked"


def test_cluster_cap_exemption_is_honoured():
    from b8_paired_shadow.questions import cap_builder

    clusters = {"a": "jpy", "b": "jpy"}
    rows = [_mk("a", "USDJPY", "2026-01-05T09:00:00+00:00"),
            _mk("b", "EURJPY", "2026-01-05T13:00:00+00:00")]
    cap = cap_builder(per_sleeve_symbol_day=True, per_cluster_day=True, clusters=clusters,
                      cluster_exempt=frozenset({"jpy"}))
    assert len(cap(rows)) == 2


def test_merge_forward_refuses_duplicate_decisions():
    from b8_paired_shadow.live_shadow import merge_forward
    from b8_paired_shadow.substrate import Intent

    a = Intent("s", "EURUSD", 16388, "2026-01-01T00:00:00+00:00", 1, 1.0, 2.0,
               "2026-01-01", "2026-01-01T04:00:00+00:00", math.nan, "x")
    assert len(merge_forward([a], [a, a])) == 1


def test_emitter_dedupe_key_is_type_stable_across_a_restart():
    """The file stores "H4"; the engine hands back 16388. A restart must still dedupe."""
    from b8_paired_shadow.emit_decisions import _key

    assert _key("s", "EURUSD", "H4", "t") == _key("s", "EURUSD", 16388, "t")
    assert _key("s", "EURUSD", "M15", "t") == _key("s", "EURUSD", 15, "t")
    assert _key("s", "EURUSD", "D1", "t") != _key("s", "EURUSD", 16388, "t")


def test_emitter_config_forces_the_three_live_gates_off():
    from b8_paired_shadow.emit_decisions import runtime_config

    cfg = runtime_config(overrides={"ultimate_book_live_broker_authority": True})
    assert cfg["ultimate_book_live_broker_authority"] is False
    assert cfg["ultimate_book_live_activation_allowed"] is False
    assert cfg["ultimate_book_apply_to_execution"] is False
    assert cfg["ultimate_book_include_clean3"] is True


def test_live_shadow_intake_reads_the_emitter_schema(tmp_path):
    """The emitter's output and the intake's expectations must be one contract."""
    import json as _json

    from b8_paired_shadow.live_shadow import intents_from_shadow_log

    p = tmp_path / "decisions.jsonl"
    p.write_text(_json.dumps({
        "sleeve": "crypto", "symbol": "BTCUSD", "timeframe": "H4",
        "decision_bar_iso": "2026-07-01T17:00:00+00:00", "direction": 1,
        "sl_distance_price": 100.0, "target_dist": 400.0,
        "decision_day": "2026-07-01", "entry_utc": "2026-07-01T21:00:00+00:00"}) + "\n"
        + '{"sleeve": "crypto"}\n')
    rows, drops = intents_from_shadow_log(p)
    assert len(rows) == 1 and rows[0].timeframe == 16388
    assert sum(drops.values()) == 1, drops
