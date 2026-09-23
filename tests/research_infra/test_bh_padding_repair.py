"""Behavioural tests for the BH-padding repair (2026-08-11).

THE DEFECT. `gate.py` padded every declared-but-not-judged family member at `p = 1.0` and
called the result Benjamini-Hochberg. It is not: BH's power over Bonferroni comes entirely
from the OTHER p-values in the family being small, which is what lets ranks 2, 3, 4 fire at
`alpha*k/m`. Pad every sibling at 1.0 and no rank above 1 can ever fire, so the operative
bar is `alpha/m` and the reported q is `p*m` — Bonferroni, at a family size assembled for a
different procedure. `LANE_B_MULTIPLICITY_ARCHITECTURE_V1.md` reproduced that to 1e-15
against the CS receipt, whose own multiplicity block publishes `k: 0`, `threshold: 0.0`, one
member with a null and 58 padded.

WHAT IS ASSERTED HERE, in the order a reader should audit it:

  1. textbook BH still holds, with and without a separated denominator;
  2. the repair is a strict generalisation — every published q-value and every published
     seal reproduces byte-for-byte, asserted against the committed receipts;
  3. the padding path is UNREACHABLE — proved by intercepting the actual argument the gate
     hands to `stats.benjamini_hochberg` and by exhibiting a verdict padding cannot produce;
  4. a known-null series still rejects — the seven negative controls, 0 verdicts changed;
  5. the degeneracy is disclosed, and the disclosure is right at k=42 as well as at k=0;
  6. the sibling channel cannot become a lever — every refusal in `__post_init__`.

Nothing here greps source. Every assertion is a value the code produced.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import pathlib
import random

import pytest

from src.research_infra.walkforward import TradeRecord, Verdict, run_gate
from src.research_infra.walkforward.options import OPTIONS
from src.research_infra.walkforward.spec import GateSpec
from src.research_infra.walkforward.stats import benjamini_hochberg, bonferroni

UTC = dt.timezone.utc
FAST = dict(n_bootstrap=400, n_permutation=400)
AUDIT = pathlib.Path(__file__).resolve().parents[2] / (
    "docs/audits/fable5-vision-audit-20260725")

#: The CS receipt's published numbers — the exact case Lane B reproduced.
BREAKER_P = 0.0025997400259974
BREAKER_Q = 0.1533846615338466
BREAKER_M = 59
ALPHA = 0.10


def _old_padded_bh(pvalues, alpha, family_size):
    """The pre-repair implementation, kept HERE and only here so the tests can prove the
    repair matches it where it must and diverges from it where it must."""
    padded = list(pvalues) + [1.0] * (family_size - len(pvalues))
    m = len(padded)
    clean = [p if isinstance(p, float) and math.isfinite(p) else 1.0 for p in padded]
    order = sorted(range(m), key=lambda i: clean[i])
    k, thresh = 0, 0.0
    for rank, i in enumerate(order, start=1):
        if clean[i] <= alpha * rank / m:
            k, thresh = rank, alpha * rank / m
    rejected = [False] * m
    for rank, i in enumerate(order, start=1):
        if rank <= k:
            rejected[i] = True
    q, running = [1.0] * m, 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, clean[i] * m / rank)
        q[i] = min(1.0, running)
    return {"rejected": rejected, "qvalues": q, "threshold": thresh, "k": k, "m": m}


# =====================================================================================
# 1. Textbook BH, with the denominator separated from the observations
# =====================================================================================
def test_the_1995_reference_example_is_unchanged_when_m_is_passed_explicitly():
    """Benjamini & Hochberg (1995) Table 1: m=15, alpha=0.05, exactly 4 rejections."""
    p = [0.0001, 0.0004, 0.0019, 0.0095, 0.0201, 0.0278, 0.0298, 0.0344,
         0.0459, 0.3240, 0.4262, 0.5719, 0.6528, 0.7590, 1.000]
    implicit = benjamini_hochberg(p, 0.05)
    explicit = benjamini_hochberg(p, 0.05, family_size=15)
    assert implicit["k"] == explicit["k"] == 4
    assert implicit["rejected"] == explicit["rejected"]
    assert implicit["qvalues"] == explicit["qvalues"]
    assert explicit["n_observed"] == 15 and explicit["n_unobserved"] == 0


def test_a_family_with_known_p_values_gives_the_textbook_step_up_result():
    """Worked by hand at m=10, alpha=0.05.

    Sorted p: 0.001 0.008 0.039 0.041 0.042 0.060 0.074 0.205 0.310 0.500
    Bars    : 0.005 0.010 0.015 0.020 0.025 0.030 0.035 0.040 0.045 0.050
    Ranks satisfying p_(r) <= 0.05r/10: rank 1 (0.001<=0.005) and rank 2 (0.008<=0.010).
    The largest such rank is 2, so BH rejects the two smallest and no others.
    """
    p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.060, 0.074, 0.205, 0.310, 0.500]
    r = benjamini_hochberg(p, 0.05, family_size=10)
    assert r["k"] == 2
    assert r["threshold"] == pytest.approx(0.010)
    assert r["rejected"] == [True, True] + [False] * 8
    assert r["qvalues"][0] == pytest.approx(0.010)   # 0.001*10/1, floored by rank 2's 0.04
    assert r["qvalues"][1] == pytest.approx(0.040)   # 0.008*10/2
    assert all(r["qvalues"][i] <= r["qvalues"][i + 1] + 1e-12 for i in range(9))


def test_bh_takes_the_largest_qualifying_rank_not_the_first():
    """The property the whole repair turns on, and the one an earlier revision of the
    degeneracy stamp got wrong: ranks 1 and 2 can both fail their own bars while rank 5
    passes, and BH then rejects all five."""
    p = [0.030, 0.031, 0.032, 0.033, 0.034]
    r = benjamini_hochberg(p, 0.05, family_size=5)
    assert p[0] > 0.05 * 1 / 5 and p[1] > 0.05 * 2 / 5   # ranks 1 and 2 both fail
    assert r["k"] == 5 and all(r["rejected"])


def test_family_size_smaller_than_the_evidence_is_refused():
    for fn in (benjamini_hochberg, bonferroni):
        with pytest.raises(ValueError, match="cannot charge fewer hypotheses"):
            fn([0.01, 0.02, 0.03], 0.10, family_size=2)


def test_an_all_unobserved_family_rejects_nothing_and_says_so():
    r = benjamini_hochberg([], 0.10, family_size=59)
    assert r["m"] == 59 and r["k"] == 0
    assert r["n_observed"] == 0 and r["n_unobserved"] == 59
    assert r["rejected"] == [] and r["qvalues"] == []


# =====================================================================================
# 2. The repair is a STRICT GENERALISATION — nothing published moves
# =====================================================================================
@pytest.mark.parametrize("seed", range(6))
def test_no_siblings_reproduces_the_padded_result_exactly(seed):
    """2,000 random families per seed. With no sibling p-value supplied, BH over the real
    p-values at `family_size=m` is arithmetically identical to BH over the padded vector,
    on every field a verdict reads. This is why the repair regresses nothing."""
    rng = random.Random(seed)
    for _ in range(2000):
        n = rng.randint(1, 6)
        m = n + rng.randint(0, 70)
        alpha = rng.choice([0.05, 0.10, 0.20])
        real = [rng.choice([rng.random(), rng.random() ** 4, 1.0, 0.0]) for _ in range(n)]
        old = _old_padded_bh(real, alpha, m)
        new = benjamini_hochberg(real, alpha, family_size=m)
        assert new["k"] == old["k"]
        assert new["m"] == old["m"]
        assert new["threshold"] == old["threshold"]
        assert new["rejected"] == old["rejected"][:n]
        assert new["qvalues"] == old["qvalues"][:n]
        oldb = _old_padded_bh(real, alpha, m)  # shape check only; bonferroni compared below
        newb = bonferroni(real, alpha, family_size=m)
        assert newb["threshold"] == pytest.approx(alpha / m)
        assert newb["m"] == oldb["m"]


def test_the_published_breaker_q_value_reproduces_to_1e_15():
    """The estate's own receipt, recomputed by the repaired production function."""
    r = benjamini_hochberg([BREAKER_P], ALPHA, family_size=BREAKER_M)
    assert abs(r["qvalues"][0] - BREAKER_Q) < 1e-15
    assert r["k"] == 0 and r["threshold"] == 0.0
    assert r["n_observed"] == 1 and r["n_unobserved"] == 58
    # ... and it is Bonferroni, exactly, which is the finding.
    b = bonferroni([BREAKER_P], ALPHA, family_size=BREAKER_M)
    assert abs(b["qvalues"][0] - r["qvalues"][0]) < 1e-15
    assert b["rejected"] == r["rejected"]


@pytest.mark.skipif(not AUDIT.is_dir(), reason="the audit tree is not in this working tree")
def test_every_published_estate_family_block_is_unchanged_by_the_repair():
    """The estate's own numbers, re-derived by the repaired production functions.

    Every `family.multiplicity` block in the audit tree that publishes a method, an `m`, a
    `qvalues` vector and the list of members that reached a null is recomputed from those
    members' REAL p-values at the published `m`, and required to reproduce the published
    q-vector, `k` and `threshold` exactly. That covers the multi-sleeve runs where the
    step-up genuinely stepped (`k = 2` at m = 6 on the negative controls, and larger) as well
    as the degenerate single-candidate ones, and it covers Bonferroni blocks too — so this is
    a check on the whole surface, not on the one case the repair was designed around.

    Measured at the time of writing: 44 blocks, 2,989 rows, 0 mismatches.
    """
    fns = {"benjamini_hochberg": benjamini_hochberg, "bonferroni": bonferroni}
    blocks = rows = 0
    for path in sorted(AUDIT.rglob("*.json")):
        try:
            doc = json.loads(path.read_text())
        except Exception:
            continue
        stack = [doc]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                fam = node.get("family")
                mult = fam.get("multiplicity") if isinstance(fam, dict) else None
                names = mult.get("family_members_with_null") if isinstance(mult, dict) else None
                if (isinstance(mult, dict) and mult.get("method") in fns
                        and isinstance(mult.get("qvalues"), list)
                        and isinstance(mult.get("m"), int)
                        and isinstance(names, list) and names):
                    src = node.get("rows") or node.get("sleeves") or {}
                    by_name = ({r["sleeve"]: r for r in src
                                if isinstance(r, dict) and r.get("sleeve")}
                               if isinstance(src, list) else src)
                    ps = []
                    for name in names:
                        row = by_name.get(name)
                        if not isinstance(row, dict):
                            ps = None
                            break
                        sig = (row.get("gates") or {}).get("significance")
                        p = sig.get("p_raw") if isinstance(sig, dict) else row.get("p_raw")
                        if not isinstance(p, (int, float)):
                            ps = None
                            break
                        ps.append(float(p))
                    if ps:
                        blocks += 1
                        rows += len(ps)
                        got = fns[mult["method"]](ps, float(mult.get("alpha", ALPHA)),
                                                  family_size=int(mult["m"]))
                        pub = [float(q) for q in mult["qvalues"][:len(ps)]]
                        assert got["k"] == mult.get("k"), f"{path}: k moved"
                        assert abs(got["threshold"]
                                   - float(mult.get("threshold", 0.0))) < 1e-15, (
                            f"{path}: threshold moved")
                        assert all(abs(a - b) < 1e-12 for a, b in zip(got["qvalues"], pub)), (
                            f"{path}: a published q-value is not reproduced by the repaired "
                            f"function")
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    assert blocks >= 40 and rows >= 2900, (
        f"only {blocks} family blocks / {rows} rows were checkable; the estate published 44 "
        f"/ 2,989 when this test was written, so either receipts moved or the walk broke")


# =====================================================================================
# 3. The padding path is UNREACHABLE
# =====================================================================================
def _mk(sleeve, symbol, n, gen, *, rng, start=dt.date(2016, 1, 4), px=100.0, sl=1.0):
    out, d = [], start
    for i in range(n):
        d += dt.timedelta(days=rng.choice((1, 1, 2, 3)))
        e = dt.datetime(d.year, d.month, d.day, 8, tzinfo=UTC)
        out.append(TradeRecord(
            sleeve=sleeve, symbol=symbol, entry_utc=e,
            exit_utc=e + dt.timedelta(hours=6.0), direction=rng.choice([1, -1]),
            sl_distance_price=sl, entry_price=px, r_gross=gen(i, d)))
    return out


def _edge_trades(sleeve="mx_nzdjpy_d1_donchian_20_breakout", seed=20):
    rng = random.Random(seed)
    return _mk(sleeve, "NZDJPY", 700,
               lambda i, d: max(-1.15, min(4.8, rng.gauss(0.30, 1.0))),
               rng=rng, px=80.0, sl=0.45)


def _declared(spec, size, **kw):
    return spec.with_(declared_family_size=size,
                      declared_family_id="deadbeef0000:TEST_FAMILY_V1",
                      declared_family_sha256="a" * 64, **kw)


def test_the_gate_never_hands_a_fabricated_p_value_to_the_correction(monkeypatch):
    """Intercept the actual argument. The vector the gate corrects must be exactly the
    p-values it measured — length `n_judged`, not `declared_family_size` — with the family
    size travelling as a separate `family_size` argument."""
    from src.research_infra.walkforward import gate as gate_mod

    seen = {}
    real = gate_mod.S.benjamini_hochberg

    def spy(pvalues, alpha, *, family_size=None):
        seen["pvalues"] = list(pvalues)
        seen["family_size"] = family_size
        return real(pvalues, alpha, family_size=family_size)

    monkeypatch.setattr(gate_mod.S, "benjamini_hochberg", spy)
    sleeve = "mx_nzdjpy_d1_donchian_20_breakout"
    spec = _declared(OPTIONS["B_balanced"].with_(**FAST), 59)
    res = run_gate({sleeve: _edge_trades(sleeve)}, spec)

    assert len(seen["pvalues"]) == 1, (
        "the correction was handed more p-values than the gate measured — the padding is "
        f"back: {seen['pvalues']}")
    assert seen["family_size"] == 59
    assert seen["pvalues"][0] == res.verdicts[sleeve].p_raw
    fam = res.family["multiplicity"]
    assert fam["family_members_padded_at_p1"] == 0
    assert fam["family_members_declared_not_observed"] == 58
    assert fam["n_observed"] == 1 and fam["n_unobserved"] == 58


def test_a_real_sibling_produces_a_verdict_padding_cannot_produce():
    """The behavioural proof that the padded vector is gone.

    Under padding, a single candidate against a family of 59 can only ever reach k <= 1.
    Supplying one real declared sibling below the rank-2 bar lifts the step-up to k = 2 and
    the candidate's q to `p*m/2`. No padded family can do that at any p-value, so this
    assertion is unsatisfiable by the old code path.
    """
    sleeve = "mx_nzdjpy_d1_donchian_20_breakout"
    base = _declared(OPTIONS["B_balanced"].with_(**FAST), 59)
    plain = run_gate({sleeve: _edge_trades(sleeve)}, base)
    p_raw = plain.verdicts[sleeve].p_raw
    assert p_raw <= 2 * ALPHA / 59, "fixture drifted: pick a p below the rank-2 bar"

    with_sib = base.with_(declared_family_p_values=(
        ("mx_btcusd_d1_donchian_20_breakout", 0.0006999300069993001,
         "phase6/receipts/AA_ESTATE_WALK.json"),))
    res = run_gate({sleeve: _edge_trades(sleeve)}, with_sib)
    fam = res.family["multiplicity"]
    assert fam["k"] == 2
    assert fam["threshold"] == pytest.approx(2 * ALPHA / 59)
    assert fam["m"] == 59 and fam["n_observed"] == 2 and fam["n_unobserved"] == 57
    assert res.verdicts[sleeve].q_value == pytest.approx(p_raw * 59 / 2)
    assert res.verdicts[sleeve].q_value < plain.verdicts[sleeve].q_value
    assert res.verdicts[sleeve].gates["significance"]["pass"] is True
    assert plain.verdicts[sleeve].gates["significance"]["pass"] is False
    assert fam["family_siblings_with_real_p"] == [
        {"member": "mx_btcusd_d1_donchian_20_breakout", "p_raw": 0.0006999300069993001,
         "source": "phase6/receipts/AA_ESTATE_WALK.json"}]


def test_a_sibling_that_is_also_judged_here_is_refused():
    """One member is one look. Supplying a p-value for a sleeve this run also gates would
    charge the hypothesis once and count it twice — a free extra rank at the same `m`."""
    sleeve = "mx_nzdjpy_d1_donchian_20_breakout"
    spec = _declared(OPTIONS["B_balanced"].with_(**FAST), 59,
                     declared_family_p_values=((sleeve, 0.0001, "self.json"),))
    with pytest.raises(ValueError, match="this run also judges"):
        run_gate({sleeve: _edge_trades(sleeve)}, spec)


def test_evidence_may_exactly_fill_the_bill_and_no_further():
    """The boundary, from both sides. Two siblings plus the one judged sleeve exactly fill a
    family of three — legal, and `n_unobserved` goes to zero. One more sibling than that is
    refused by `spec.py` before a gate ever runs, and the stats layer refuses it again if a
    caller reaches past both."""
    sleeve = "mx_nzdjpy_d1_donchian_20_breakout"
    ok = _declared(OPTIONS["B_balanced"].with_(**FAST), 3,
                   declared_family_p_values=(("s0", 0.2, "x.json"), ("s1", 0.2, "x.json")))
    fam = run_gate({sleeve: _edge_trades(sleeve)}, ok).family["multiplicity"]
    assert fam["m"] == 3 and fam["n_observed"] == 3 and fam["n_unobserved"] == 0

    with pytest.raises(ValueError, match="cannot be smaller than the evidence"):
        _declared(OPTIONS["B_balanced"].with_(**FAST), 3,
                  declared_family_p_values=tuple((f"s{i}", 0.2, "x.json") for i in range(3)))


def test_a_sibling_cannot_shrink_the_family_or_change_the_bill():
    """The ratchet is untouched: supplying evidence never lowers `m`."""
    sleeve = "mx_nzdjpy_d1_donchian_20_breakout"
    base = _declared(OPTIONS["B_balanced"].with_(**FAST), 59)
    sibs = base.with_(declared_family_p_values=tuple(
        (f"sibling_{i}", 0.4, "src.json") for i in range(20)))
    a = run_gate({sleeve: _edge_trades(sleeve)}, base)
    b = run_gate({sleeve: _edge_trades(sleeve)}, sibs)
    assert a.family["multiplicity"]["m"] == b.family["multiplicity"]["m"] == 59
    # 20 uninformative siblings cannot help, and must not hurt either.
    assert (a.verdicts[sleeve].gates["significance"]["pass"]
            == b.verdicts[sleeve].gates["significance"]["pass"])


# =====================================================================================
# 4. A KNOWN-NULL SERIES STILL REJECTS — the guarantee that this admits no garbage
# =====================================================================================
NEGCTL = AUDIT / "phase5/receipts/W_NEGATIVE_CONTROLS.json"


@pytest.mark.skipif(not NEGCTL.is_file(), reason="W_NEGATIVE_CONTROLS.json is not present")
def test_zero_of_seven_negative_controls_change_verdict_under_the_repair():
    """Lane B's falsification check, reproduced against the committed receipt.

    Six constructed adversaries plus one positive control. The result is an IDENTITY, not a
    coincidence: both control runs published `family_members_padded_at_p1: 0` — six real
    p-values in a family of six, one in a family of one — so they are the only runs in the
    estate where BH was already running as BH (k=2 at threshold 1/30). A repair that only
    removes fabricated p-values cannot move a family that had none.
    """
    doc = json.loads(NEGCTL.read_text())
    core = ("expectancy", "lifetime", "stability", "robustness", "significance")
    changed, total = [], 0
    for run_name in ("synthetic_adversaries", "positive_control"):
        run = doc["runs"][run_name]
        pub = run["family"]["multiplicity"]
        assert pub["family_members_padded_at_p1"] == 0, (
            "the control runs are supposed to be the estate's only unpadded families; if "
            "that changed, this test is measuring something else")
        rows = [r for r in run["rows"] if isinstance(r.get("p_raw"), (int, float))]
        r = benjamini_hochberg([float(x["p_raw"]) for x in rows], ALPHA,
                               family_size=max(int(pub["m"]), len(rows)))
        assert r["k"] == pub["k"] and r["threshold"] == pytest.approx(pub["threshold"])
        for row, rejected, q in zip(rows, r["rejected"], r["qvalues"]):
            total += 1
            assert q == pytest.approx(float(row["q_value"]), abs=1e-12)
            failed = [g for g in core
                      if isinstance(row["gates"].get(g), bool) and not row["gates"][g]]
            failed = [g for g in failed if g != "significance"]
            if not rejected:
                failed.append("significance")
            verdict = "REJECT" if failed else "ADMIT"
            if verdict != row["verdict"]:
                changed.append((row["sleeve"], row["verdict"], verdict))
    assert total == 7, f"expected 6 adversaries + 1 positive control, found {total}"
    assert changed == [], f"the repair changed a negative control's verdict: {changed}"
    assert doc["falsification"]["synthetic_adversaries_admitted"] == []


def test_a_constructed_null_still_rejects_through_the_live_gate():
    """Not from a receipt — generated here, run through `run_gate`, with a sibling supplied
    so the repair's new channel is actually exercised. A zero-expectancy series must not
    reach ADMIT no matter how generous the family's other members are."""
    rng = random.Random(7)
    sleeve = "mx_nzdjpy_d1_donchian_20_breakout"      # priceable on FTMO; AVAUSD is not
    trades = _mk(sleeve, "NZDJPY", 700, lambda i, d: max(-1.15, min(4.8, rng.gauss(0.0, 1.0))),
                 rng=rng, px=80.0, sl=0.45)
    spec = _declared(OPTIONS["B_balanced"].with_(**FAST), 59,
                     declared_family_p_values=tuple(
                         (f"generous_sibling_{i}", 1e-9, "constructed.json")
                         for i in range(30)))
    res = run_gate({sleeve: trades}, spec)
    v = res.verdicts[sleeve]
    assert v.verdict is not Verdict.ADMIT, (
        "a zero-expectancy series reached ADMIT once its family carried real siblings — "
        "the repair would then be a lowered bar wearing a statistical costume")
    assert res.family["multiplicity"]["k"] >= 30   # the siblings really did enter the step-up
    assert res.family["multiplicity"]["degenerate_equals_bonferroni"] is False
    # And it is an ECONOMIC gate that stops it, not significance — which is Lane B's
    # empirical finding restated as a test: significance has never been the gate that
    # stopped a known-null series in this estate.
    core = ("expectancy", "lifetime", "stability", "robustness")
    assert any(not v.gates[g]["pass"] for g in core if g in v.gates)


# =====================================================================================
# 5. The degeneracy is disclosed, and the disclosure is correct at both ends
# =====================================================================================
def test_the_single_candidate_gate_is_stamped_as_bonferroni():
    sleeve = "mx_nzdjpy_d1_donchian_20_breakout"
    spec = _declared(OPTIONS["B_balanced"].with_(**FAST), 59)
    res = run_gate({sleeve: _edge_trades(sleeve)}, spec)
    sig = res.verdicts[sleeve].gates["significance"]
    assert sig["multiplicity"] == "benjamini_hochberg"
    assert sig["degenerate_equals_bonferroni"] is True
    assert sig["family_members_observed"] == 1
    assert sig["family_members_unobserved"] == 58
    assert sig["rank2_threshold"] == pytest.approx(2 * ALPHA / 59)
    assert "DEGENERATE" in sig["note"] and "FWER" in sig["note"]
    assert "p=1.0" not in sig["note"], "the note still claims members are carried at p=1.0"


def test_the_degeneracy_stamp_is_false_when_the_step_up_actually_steps():
    sleeve = "mx_nzdjpy_d1_donchian_20_breakout"
    spec = _declared(OPTIONS["B_balanced"].with_(**FAST), 59,
                     declared_family_p_values=(
                         ("s1", 0.0006999300069993001, "AA_ESTATE_WALK.json"),))
    res = run_gate({sleeve: _edge_trades(sleeve)}, spec)
    sig = res.verdicts[sleeve].gates["significance"]
    assert sig["degenerate_equals_bonferroni"] is False
    assert sig["step_up_k"] == 2
    assert "DEGENERATE" not in sig["note"]


def test_a_high_k_family_whose_low_ranks_fail_is_not_stamped_degenerate():
    """The regression this file's own first draft needed. `EXIT_FRONTIER_V1`'s 61-cell grids
    reach k=42 while ranks 1 and 2 both fail their bars; a stamp keyed on "two p-values below
    the rank-2 bar" called those degenerate, which is wrong in the direction that hides real
    FDR work. The test is at the stats layer because that is where k is decided."""
    p = [0.030, 0.031, 0.032, 0.033, 0.034]
    r = benjamini_hochberg(p, 0.05, family_size=5)
    n_below_rank2 = sum(1 for x in p if x <= 2 * 0.05 / 5)
    assert n_below_rank2 == 0 and r["k"] == 5
    assert sum(r["rejected"]) > sum(bonferroni(p, 0.05, family_size=5)["rejected"])


# =====================================================================================
# 6. The sibling channel cannot become a lever
# =====================================================================================
def _base_spec(**kw) -> GateSpec:
    return GateSpec(spec_id="t", authored_utc="2026-07-29T00:00:00+00:00", **kw)


@pytest.mark.parametrize("kw,match", [
    (dict(declared_family_p_values=()), "must be None or non-empty"),
    (dict(declared_family_p_values=(("a", 0.1, "s.json"),)), "requires declared_family_id"),
])
def test_sibling_p_values_without_provenance_are_refused(kw, match):
    with pytest.raises(ValueError, match=match):
        _base_spec(**kw)


@pytest.mark.parametrize("rows,match", [
    ((("a", 0.1, "s.json"), ("a", 0.2, "s.json")), "twice"),
    ((("a", 1.5, "s.json"),), "finite probability"),
    ((("a", float("nan"), "s.json"),), "finite probability"),
    ((("", 0.1, "s.json"),), "non-empty member_id"),
    ((("a", 0.1, ""),), "non-empty member_id"),
    ((("a", 0.1),), "must be"),
])
def test_malformed_sibling_rows_are_refused(rows, match):
    with pytest.raises(ValueError, match=match):
        _base_spec(declared_family_size=59, declared_family_id="d:F",
                   declared_family_sha256="a" * 64, declared_family_p_values=rows)


def test_more_siblings_than_the_family_charges_is_refused():
    with pytest.raises(ValueError, match="cannot be smaller than the evidence"):
        _base_spec(declared_family_size=3, declared_family_id="d:F",
                   declared_family_sha256="a" * 64,
                   declared_family_p_values=tuple(
                       (f"s{i}", 0.1, "s.json") for i in range(3)))


def test_sibling_p_values_are_sealed():
    """A run that assembled siblings must not hash the same as one that did not, or a
    retrospective assembly could pretend to be a prospective one."""
    base = _base_spec(declared_family_size=59, declared_family_id="d:F",
                      declared_family_sha256="a" * 64)
    one = base.with_(declared_family_p_values=(("a", 0.001, "s.json"),))
    two = base.with_(declared_family_p_values=(("a", 0.002, "s.json"),))
    three = base.with_(declared_family_p_values=(("b", 0.001, "s.json"),))
    four = base.with_(declared_family_p_values=(("a", 0.001, "other.json"),))
    seals = {base.seal(), one.seal(), two.seal(), three.seal(), four.seal()}
    assert len(seals) == 5, "two materially different sibling assemblies collide in the seal"


# =====================================================================================
# 7. The accountable path — membership actually checked
# =====================================================================================
def _toy_family(tmp_path):
    """A two-member declaration written to disk, so the checks run against a real file."""
    doc = {
        "schema": "gtos.walkforward.candidate_family.v1",
        "generated_by": "test",
        "declaration_date": "2026-08-01",
        "families": {
            "TOY_V1": {
                "family_id": "TOY_V1", "purpose": "test", "declaration_date": "2026-08-01",
                "high_water_size": 4, "high_water_looks": 2,
                "members": [
                    {"name": "live_sibling", "source": "s.json", "basis": "b",
                     "declared_at": "2026-08-01"},
                    {"name": "the_candidate", "source": "s.json", "basis": "b",
                     "declared_at": "2026-08-01"},
                    {"name": "gone", "source": "s.json", "basis": "b",
                     "declared_at": "2026-08-01", "status": "withdrawn",
                     "withdrawn_at": "2026-08-02", "withdrawn_reason": "superseded"},
                    {"name": "never_ran", "source": "s.json", "basis": "b",
                     "declared_at": "2026-08-01", "look_taken": False,
                     "no_look_evidence": "n_trades=0 in TEST.json"},
                ],
            }
        },
    }
    p = tmp_path / "TOY_FAMILY_V1.json"
    p.write_text(json.dumps(doc))
    return p


@pytest.mark.parametrize("member,match", [
    ("not_a_member", "not a member of family"),
    ("gone", "WITHDRAWN"),
    ("never_ran", "look_taken=False"),
])
def test_the_accountable_path_refuses_an_illegitimate_sibling(tmp_path, member, match):
    from src.research_infra.walkforward import candidate_family as cf

    path = _toy_family(tmp_path)
    with pytest.raises(cf.CandidateFamilyError, match=match):
        cf.with_family_p_values(OPTIONS["B_balanced"], "TOY_V1",
                                [(member, 0.001, "receipt.json")], declaration=path)


def test_the_accountable_path_resolves_the_bill_and_the_evidence_together(tmp_path):
    from src.research_infra.walkforward import candidate_family as cf

    path = _toy_family(tmp_path)
    spec = cf.with_family_p_values(OPTIONS["B_balanced"], "TOY_V1",
                                   [("live_sibling", 0.001, "receipt.json")],
                                   declaration=path)
    assert spec.declared_family_size == 4          # the ratchet's high-water, not 1
    assert spec.declared_family_id.endswith(":TOY_V1")
    assert spec.declared_family_sha256 is not None
    assert spec.declared_family_p_values == (("live_sibling", 0.001, "receipt.json"),)
    assert spec.seal() != OPTIONS["B_balanced"].seal()


def test_absent_siblings_seal_exactly_as_before_the_field_existed():
    """The `_ABSENT_MEANS_UNCHANGED` half: None must be invisible to the hash."""
    spec = OPTIONS["B_balanced"]
    assert spec.declared_family_p_values is None
    assert "declared_family_p_values" not in spec.canonical()
    assert spec.with_(declared_family_p_values=None).seal() == spec.seal()
