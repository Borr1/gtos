"""The actuator's backtest half, on Session AA's cost-true splits instead of the legacy cost map.

Two jobs.

**1. The loader is right.** The partition is disjoint, every emitted split carries a day count, and
the means reproduce an independent recomputation straight out of the artifact.

**2. THE TRIPWIRE THAT REPLACED THE COST-TRUE VETO.** R bolted `cost_true_survivor is False ->
block any size-up` onto the rule because the every-split evidence was the CP4/CP5 replay at the cost
map F38 (zero commission) and F39 (wrong sign on tick erosion) discredited: `metals_softband` scored
SIZE_UP x1.22 from those splits while the broker-true re-cost killed it on both accounts. Session AE
retired the veto, and the property it protected — **no size-up on cost-discredited evidence** — must
now hold *by construction*, because the evidence itself is priced at broker truth.

`test_no_cost_discredited_sleeve_is_sized_up` is that property, asserted against the real artifact
rather than a synthetic flag. If a future change to the rule, the loader or the estate walk lets a
CARRY_CONDITIONAL or DEAD_BEFORE_COST sleeve out with a multiplier above 1.0, this fails — which is
exactly what the veto used to prevent, now measured instead of patched.

Behavioural throughout: every assertion runs the production loader and the production `recommend()`.
"""
import json
from pathlib import Path

import pytest

from src.components.ultimate_book.cost_true_splits import (
    DEFAULT_SPLITS,
    SPLIT_NAMES,
    build_cost_true_evidence,
    load_splits,
    partition_days,
    sleeve_splits,
)
from src.components.ultimate_book.learning_actuator import (
    MIN_N,
    _backtest_verdict,
    recommend,
)


def _backtest_only(ev, *, day_blocked: bool):
    """The every-split rule at one floor, with no live composition — for A/B-ing the floors."""
    return _backtest_verdict(ev, ev.evaluable_splits(day_blocked=day_blocked))

REPO = Path(__file__).resolve().parents[2]
SURVIVOR = REPO / "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"

# Tiers that clear broker-true cost outright. The three CARRY_CONDITIONAL tiers turn on a holding
# time no cache records (CLAUDE.md section 4) and DEAD_BEFORE_COST is what it says; both are
# "cost-discredited" for the purpose of permitting a size-up.
SURVIVING_TIERS = {"UNCONDITIONAL", "MEASURED_LIVE_CARRY", "CARRY_CONDITIONAL_LIVE_SUPPORTED"}

pytestmark = pytest.mark.skipif(not DEFAULT_SPLITS.is_file(),
                                reason="AA_SLEEVE_SPLITS_V1.json not in this tree")


@pytest.fixture(scope="module")
def doc():
    return load_splits()


@pytest.fixture(scope="module")
def evidence(doc):
    return build_cost_true_evidence(doc)


def _tiers() -> dict:
    """{account: {sleeve: tier}} from whichever cost-true artifact this tree carries."""
    if SURVIVOR.is_file():
        book = json.loads(SURVIVOR.read_text())
        return {a: {s: r.get("survivor_tier") for s, r in b["sleeves"].items()}
                for a, b in book["accounts"].items()}
    from src.components.ultimate_book.live_evidence import load_calibration
    cal = load_calibration()
    return {a: {s: r.get("survivor_tier") for s, r in sleeves.items()}
            for a, sleeves in (cal.get("accounts") or {}).items()}


# ---------------------------------------------------------------------- 1. the loader is right

def test_the_three_splits_are_disjoint_for_every_sleeve(doc):
    """A day counted in two splits would let one observation clear the every-split bar twice."""
    for name, sleeve in (doc["sleeves"]).items():
        if not sleeve.get("available"):
            continue
        p = partition_days(sleeve)
        a, b, c = set(p["train"]), set(p["oos"]), set(p["sealed"])
        assert not (a & b) and not (a & c) and not (b & c), name
        assert a and b and c, f"{name} has an empty split: {len(a)}/{len(b)}/{len(c)}"


def test_splits_are_ordered_in_time(doc):
    """train < oos < sealed. `sealed` is the LAST forward fold and must actually be last."""
    for name, sleeve in (doc["sleeves"]).items():
        if not sleeve.get("available"):
            continue
        st = sleeve_splits(sleeve)
        assert st["train"].last_day <= st["oos"].first_day, name
        assert st["oos"].last_day <= st["sealed"].first_day, name


def test_means_reproduce_an_independent_recomputation(doc):
    """Known-answer: recompute every split from the raw day series and compare to the loader."""
    for name, sleeve in (doc["sleeves"]).items():
        if not sleeve.get("available"):
            continue
        p = partition_days(sleeve)
        st = sleeve_splits(sleeve)
        for split in SPLIT_NAMES:
            days = [d for d in p[split] if d in sleeve["daily_net_r"]]
            n_tr = sum(int(sleeve["daily_trade_counts"][d]) for d in days)
            total = sum(float(sleeve["daily_net_r"][d]) for d in days)
            assert st[split].n_days == len(days), (name, split)
            assert st[split].n_trades == n_tr, (name, split)
            if n_tr:
                assert abs(st[split].mean_r - total / n_tr) < 1e-12, (name, split)


def test_every_emitted_split_carries_a_day_count(evidence):
    """The production loader must never fall through to the permissive trade-count path.

    `SleeveEvidence` admits on trade count when no day count is supplied, which is looser — it
    exists only for hand-entered legacy triples. If this ever fails, the day-blocked sample floor
    has silently stopped binding on real evidence.
    """
    for name, ev in evidence.items():
        for n_tr, n_d in ((ev.train_n, ev.train_days), (ev.oos_n, ev.oos_days),
                          (ev.sealed_n, ev.sealed_days)):
            assert n_d > 0, f"{name}: {n_tr} trades on 0 recorded days"
            assert n_d <= n_tr, f"{name}: {n_d} days but only {n_tr} trades"
        assert ev.evidence_basis.startswith("cost_true:")


def test_a_sleeve_that_generated_nothing_is_omitted_not_zero_filled(doc, evidence):
    """`vp_euidx_pocgrav` is redacted_account's fourth UNCONDITIONAL survivor and generates nothing today.

    Emitting it with `mean_r = 0.0` on `n = 0` would read as a measured flat result, and a flat
    result on every split is what the every-split bar GATES. Unmeasured must not become dead.
    """
    absent = [n for n, s in doc["sleeves"].items() if not s.get("available")]
    assert "vp_euidx_pocgrav" in absent
    for name in absent:
        assert name not in evidence


# -------------------------------------------- 2. the tripwire that replaced the cost-true veto

def test_no_cost_discredited_sleeve_is_sized_up(evidence):
    """The property the retired veto protected, now holding by construction.

    Every sleeve the broker-true re-cost does NOT clear must come out of the rule at x1.00 or
    below, on cost-true evidence alone, with no veto in the path.
    """
    tiers = _tiers()
    checked = 0
    for account, by_sleeve in tiers.items():
        for sleeve, tier in by_sleeve.items():
            ev = evidence.get(sleeve)
            if ev is None or tier is None or tier in SURVIVING_TIERS:
                continue
            checked += 1
            r = recommend(ev)
            assert r.conf_mult <= 1.0, (
                f"{account}/{sleeve} is {tier} at broker truth and the rule recommends "
                f"x{r.conf_mult:.3f} ({r.verdict}) on cost-true splits: {r.reason}"
            )
    assert checked >= 6, f"tripwire covered only {checked} cost-discredited sleeve-accounts"


def test_metals_softband_is_the_case_the_veto_was_written_for(evidence):
    """R's worked example: SIZE_UP x1.22 off the legacy splits, killed by carry on both accounts.

    On cost-true splits it does not reach a size-up at all, so the veto has nothing to veto.
    """
    r = recommend(evidence["metals_softband"])
    assert r.verdict != "SIZE_UP" and r.conf_mult <= 1.0


def test_the_day_blocked_floor_actually_binds(evidence):
    """`sub_xvol_pullback` clears 30 TRADES on two splits and 30 DAYS on none.

    It is the sleeve FOURTH_REVIEW's own concentration warning names (46.9 % of the survivor book's
    edge on 194 trades, concentrated here and in `crypto`), and it is armed. Counting its 37 sealed
    trades on 13 days as 37 observations is how a concentrated sleeve buys a size-up.
    """
    ev = evidence["sub_xvol_pullback"]
    assert ev.oos_n >= MIN_N and ev.sealed_n >= MIN_N
    assert ev.oos_days < MIN_N and ev.sealed_days < MIN_N
    assert recommend(ev).verdict == "INSUFFICIENT_EVIDENCE"


def test_the_day_blocked_floor_never_withdraws_a_brake(evidence):
    """The floor is asymmetric, and this is the fail-open it closes.

    Day-blocking the sample floor is right for a size-up and wrong for a brake. Measured on the
    real artifact: `kz_london_crypto_low` is negative on all three splits and only its 167-day oos
    clears 30 DAYS, so a symmetric day-blocked floor turned its GATE into INSUFFICIENT_EVIDENCE —
    a brake withdrawn because the evidence was day-thin, which is exactly the wrong direction.
    `recommend()` therefore evaluates both floors and takes the more conservative.

    The property, over every sleeve: the shipped verdict is never a WEAKER action than what the
    looser trade-count floor alone would have recommended.
    """
    checked = 0
    for name, ev in evidence.items():
        loose = _backtest_only(ev, day_blocked=False)
        shipped = recommend(ev)
        assert shipped.conf_mult <= loose.conf_mult + 1e-12, (
            f"{name}: day-blocking weakened the recommendation from x{loose.conf_mult} to "
            f"x{shipped.conf_mult}")
        checked += 1
    assert checked >= 25
    assert recommend(evidence["kz_london_crypto_low"]).verdict == "GATE"


def test_metals_core_no_longer_rests_on_a_discarded_negative_split(evidence):
    """R section 4 item 15, answered by evidence rather than by a MIN_N rule change.

    On the legacy CP4/CP5 splits `metals_core` scored SIZE_UP x1.15 on FTMO, and only because its
    one negative split (oos -0.061 on n=24) fell under MIN_N and was dropped. On cost-true splits
    the negative is the 232-trade / 118-day oos, which no sample floor can discard, and the sleeve
    is down-weighted rather than sized up. It is armed on FTMO.
    """
    r = recommend(evidence["metals_core"])
    assert r.verdict == "DOWN_WEIGHT" and r.conf_mult < 1.0


# ---------------------------------------------------------------------------------
# The materiality band on the sign test — AE §5, adopted by Session AP (B1350-B1399)
#
# These live in the COST-TRUE file deliberately. AP's first attempt at this rule was measured only
# on the 7 legacy CP4/CP5 fixtures, where it moved one sleeve; on THIS basis — the one
# `scripts/rerate_book_from_live.py:121` actually feeds — that version WITHDREW the gate from four
# sleeves, including one losing 0.3749 R/trade on its train split. An adversarial pass caught it.
# So the band's regression tests belong where the production basis is.
# ---------------------------------------------------------------------------------


def test_the_band_never_withdraws_a_gate_on_the_production_basis(evidence):
    """The property AP's first version broke. A sleeve negative on EVERY admitted split must gate
    whatever the magnitudes — no near-zero split may excuse a ruinous one."""
    checked = 0
    for name, ev in evidence.items():
        means = [m for _n, m, _e in ev.evaluable_splits(day_blocked=False)]
        if len(means) < 2 or not all(m <= 0.0 for m in means):
            continue
        r = recommend(ev)
        assert r.verdict == "GATE" and r.gate is True, (
            f"{name}: negative on every admitted split {[round(m, 4) for m in means]} and NOT "
            f"gated — got {r.verdict} x{r.conf_mult}. This is the fail-open AP's first band "
            f"introduced; `vss_fxcross_london_up_low` (train -0.3749, oos -0.0377) is the case.")
        checked += 1
    assert checked >= 3, f"only {checked} all-negative sleeves found; the fixture no longer probes"


def test_a_near_zero_positive_split_no_longer_withdraws_a_gate(evidence):
    """AE's own instance, on AE's own numbers, closed.

    `idxrev` is -0.0243 / -0.0124 / **+0.0079** and `metal_session_reversion` is
    -0.3208 / -0.2227 / **+0.0001**. Under the bare sign test each of those trailing positives
    vetoed `every_neg` and the sleeves escaped with HOLD_FLAG x1.00 and DOWN_WEIGHT x0.5. A mean of
    one ten-thousandth of an R excusing -0.32 is the defect, stated at its most vivid.
    """
    for name in ("idxrev", "metal_session_reversion"):
        if name not in evidence:
            pytest.skip(f"{name} absent from the cost-true artifact")
        ev = evidence[name]
        means = [m for _n, m, _e in ev.evaluable_splits(day_blocked=False)]
        assert any(m > 0 for m in means), (
            f"{name} has no positive split any more, so this test no longer probes the band")
        assert max(means) <= 0.05, f"{name}'s best split is now MATERIALLY positive; re-derive"
        r = recommend(ev)
        assert r.verdict == "GATE" and r.gate is True, (name, r.verdict, r.reason)
        assert "MATERIALITY BAND" in r.reason, name


def test_the_band_gates_nothing_that_shows_a_material_positive(evidence):
    """The other edge: a sleeve with any admitted split above +0.05 is never gated by this rule."""
    for name, ev in evidence.items():
        means = [m for _n, m, _e in ev.evaluable_splits(day_blocked=False)]
        if len(means) < 2 or max(means, default=0.0) <= 0.05:
            continue
        r = recommend(ev)
        assert not (r.gate and r.backtest_verdict == "GATE"), (
            f"{name}: has a materially positive split {max(means):.4f} and the BACKTEST half "
            f"gated it — the band must not reach a sleeve with real positive evidence")
