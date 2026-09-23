"""Session AN — the placebo that decides whether the ECON population rule is a cost rule
or a calendar restriction wearing a cost argument. [B1275-B1279]

    python3 docs/audits/fable5-vision-audit-20260725/phase10/receipts/an_econ_placebo.py

THE ATTACK, ON MY OWN PROPOSAL
------------------------------
`--stage econ` of `an_population_rule.py` measures that `RECORDED AND |cost_r(high) -
cost_r(low)| <= tau` ADMITs `mx_btcusd @ target_5R` at **every** tau in [0.02, 0.50] with
p 0.0008 against full RECORDED's 0.0011 — better, on 221 of 232 trades, with a plateau from
0.05 upward so no tau is doing any work.

Then the adversarial check on it came back badly. The criterion is verified to be a function of
`(symbol, entry_utc, sl_distance_price)` alone — the swap and commission terms are
band-independent so they cancel exactly in the range, max |total_range - spread_range| =
2.2e-16 over 232 trades — so it cannot READ a return. But at tau = 0.05 the 20 trades it drops
average **-0.1000 R gross** against the 212 it keeps at **+1.1301 R**, win rate 15.0 % against
36.3 %, and all 20 sit in exactly two calendar years (2018: 9, 2020: 11).

That is outcome-INDEPENDENT in assignment and not outcome-NEUTRAL, which is the precise
distinction Session AL §3.3 drew against `era_class` — and it applies with equal force to a
rule I am proposing. So the improvement has two candidate causes and they are not the same
finding:

  H_cost      the rule removes trades whose cost genuinely cannot be pinned in R, and the
              p improvement is information;
  H_calendar  the rule removes 20 trades from two bad years, and ANY 20-trade removal from
              those years would do the same, so the p improvement is selection.

TWO PLACEBOS, AND ONLY THE SECOND ONE DISCRIMINATES
---------------------------------------------------
P1  drop 20 trades uniformly at random from the 232. Tests "does dropping any 20 help?" —
    a weak control: it will fail to reproduce the effect for reasons that include the
    calendar, so passing it proves little.
P2  drop 20 trades at random **matched to the year histogram of the econ-dropped set**
    (9 from 2018, 11 from 2020). This holds the calendar block fixed and varies only WHICH
    trades inside those years are removed. If P2 reproduces p 0.0008, the rule is a calendar
    restriction and H_cost is refuted. If P2's distribution sits well above it, the cost
    criterion is picking something the year alone does not.

Gated SOLO, on AM's own established grounds (`am_submid_reclock.do_gate_solo`): every
per-sleeve verdict input is computed from that sleeve's own trades, and only `q_value` and the
`significance` gate read the family. `p_raw` is what this file compares, so the solo gate is
exact for the purpose. The control is that the unrestricted RECORDED arm must reproduce the
family run's p_raw, which it does.
"""

from __future__ import annotations

import collections
import gzip
import json
import random
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
AD_DIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
sys.path.insert(0, str(AD_DIR))

import ad_exit_sweep as AD  # noqa: E402

from src.costs import cost_r  # noqa: E402
from src.costs.spread_model import load_spread_model  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as EP  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

HERE = Path(__file__).resolve().parent
P9 = REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts"
DECL = P9 / "CANDIDATE_FAMILY_V2.json"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
OUT = HERE / "AN_ECON_PLACEBO_V1.json"

BTC = "mx_btcusd_d1_donchian_20_breakout"
SERVER, ACCOUNT = "FTMO-Server3", "FTMO"
TAU = 0.05          # fixed BEFORE the placebos run; the sweep's plateau starts here
N_DRAWS = 40
#: Seeded so the whole test reproduces byte-for-byte. `Math.random`-style nondeterminism in an
#: adversarial control is how a refutation becomes unfalsifiable.
SEED = 20260730


def _p(recs: list, spec, costs, ledger=None, note: str = "") -> tuple[float | None, str, int]:
    res = run_gate({BTC: recs}, spec, costs=costs, server=SERVER, diagnose=False)
    sv = res.verdicts.get(BTC)
    if sv is None:
        return None, "ABSENT", 0
    if ledger is not None:
        ledger.record(
            mechanism="econ_population_placebo", sleeve=BTC,
            variant={"arm": note, "band": "mid", "option": "B_balanced",
                     "exit": "target_5R", "n_trades": sv.n_trades},
            window="full_archive", spec_sha256=spec.seal(),
            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                     "NOT_EVALUABLE": "not_evaluable"}.get(sv.verdict.value, "evaluated"),
            metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
            note=f"AN econ placebo, {note}")
    return sv.p_raw, sv.verdict.value, sv.n_trades


def main() -> dict:
    t0 = time.time()
    rng = random.Random(SEED)
    sm = load_spread_model()
    fam = CF.load_candidate_family(DECL)
    # Every gate run is a look, including a placebo draw. The ledger's own rule is that a look
    # taken cannot be un-taken, and inflating the DSR trial count with 80 RANDOM draws is the
    # conservative direction, so they go in rather than being argued out.
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AN")
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule(SERVER)
    series, index, _ = AD.load_bars()
    al = AD.allowlist()

    raw = json.load(gzip.open(AA_IN, "rt"))
    v5 = AD.Variant(name="target_5R", family="target", target_mode="fixed_r", target_r=5.0)
    rows, _ = AD.resimulate(raw["trades"][BTC], v5, series, index, costs, ACCOUNT, rule)
    recorded, _ = EP.filter_records("RECORDED", AD.to_records(rows), ACCOUNT, model=sm)
    print(f"substrate {time.time()-t0:.0f}s; RECORDED population {len(recorded)}", flush=True)

    o = OPTIONS["B_balanced"]
    base_spec = o.with_(spec_id=f"{o.spec_id}_an_placebo", spread_band="mid",
                        sleeve_symbol_allowlist={BTC: al[BTC]})
    base_spec = CF.with_declared_family(base_spec, "CANDIDATE_BOOK_V1", loaded=fam)

    # ---- the cost range, and the econ-dropped set ------------------------------------
    def crange(rec) -> float:
        a = dict(sl_distance_price=rec.sl_distance_price, entry_price=rec.entry_price,
                 side=("LONG" if rec.direction > 0 else "SHORT"), entry_utc=rec.entry_utc,
                 costs=costs)
        lo = cost_r(rec.symbol, ACCOUNT, rec.features["hold_hours"], spread_band="low", **a)
        hi = cost_r(rec.symbol, ACCOUNT, rec.features["hold_hours"], spread_band="high", **a)
        return abs(hi.total_r.value - lo.total_r.value)

    ranges = {i: crange(r) for i, r in enumerate(recorded)}
    dropped_idx = {i for i, v in ranges.items() if v > TAU}
    kept = [r for i, r in enumerate(recorded) if i not in dropped_idx]
    year_hist = collections.Counter(recorded[i].entry_utc.year for i in dropped_idx)
    print(f"econ rule at tau={TAU}: keeps {len(kept)}, drops {len(dropped_idx)} "
          f"from years {dict(sorted(year_hist.items()))}", flush=True)

    # ---- the three reference points ---------------------------------------------------
    p_full, v_full, n_full = _p(recorded, base_spec, costs, ledger, "reference_recorded_all")
    p_econ, v_econ, n_econ = _p(kept, base_spec, costs, ledger,
                                f"reference_recorded_and_econ_tau{TAU:g}")
    print(f"  RECORDED (all {n_full}):        p {p_full}  {v_full}")
    print(f"  RECORDED & econ (n {n_econ}):   p {p_econ}  {v_econ}", flush=True)

    by_year = collections.defaultdict(list)
    for i, r in enumerate(recorded):
        by_year[r.entry_utc.year].append(i)

    # ---- P1: uniform ------------------------------------------------------------------
    p1 = []
    for d in range(N_DRAWS):
        drop = set(rng.sample(sorted(ranges), len(dropped_idx)))
        pp, vv, nn = _p([r for i, r in enumerate(recorded) if i not in drop], base_spec, costs,
                        ledger, f"P1_uniform_draw{d}")
        p1.append({"draw": d, "p_raw": pp, "verdict": vv, "n": nn})
        if (d + 1) % 10 == 0:
            print(f"    P1 {d+1}/{N_DRAWS}", flush=True)

    # ---- P2: year-matched -------------------------------------------------------------
    p2 = []
    for d in range(N_DRAWS):
        drop: set[int] = set()
        for yr, k in year_hist.items():
            pool = [i for i in by_year[yr] if i not in drop]
            if len(pool) < k:
                raise RuntimeError(
                    f"year {yr} has {len(pool)} candidates for {k} draws; the first version "
                    f"used min(k, len(pool)) and would have silently under-drawn, making the "
                    f"placebo delete FEWER trades than the econ rule and so not a matched "
                    f"control at all")
            drop |= set(rng.sample(pool, k))
        pp, vv, nn = _p([r for i, r in enumerate(recorded) if i not in drop], base_spec, costs,
                        ledger, f"P2_year_matched_draw{d}")
        p2.append({"draw": d, "p_raw": pp, "verdict": vv, "n": nn,
                   "mean_gross_dropped": statistics.fmean(recorded[i].r_gross for i in drop)})
        if (d + 1) % 10 == 0:
            print(f"    P2 {d+1}/{N_DRAWS}", flush=True)

    # A SILENT NULL HERE INVERTS THE PUBLISHED CONCLUSION, so it is guarded rather than
    # defaulted. Found by a completeness critic over this session's own adversarial file
    # (B1267). `_p()` returns None by design when a sleeve is ABSENT, and the first version of
    # `summarise` wrote `p <= (p_econ or 0)`: with p_econ None that is `p <= 0`, which no
    # permutation p satisfies, so `atleast` goes 10 -> 0 and placebo_p 0.2683 -> 0.0244 --
    # flipping "H_calendar NOT REFUTED" to "H_calendar REFUTED at the 0.10 level" and with it
    # the routing decision (repair vs rule). Measured on this artifact's own 40 P2 draws. An
    # adversarial control that fails silently in the direction of its own thesis is worse than
    # no control.
    if p_econ is None or p_full is None:
        raise RuntimeError(
            f"a reference arm produced no p_raw (full={p_full!r}, econ={p_econ!r}); every "
            f"placebo comparison below is against it, so there is nothing to compare and the "
            f"conclusion must not be computed. Verdicts were {v_full!r} / {v_econ!r}."
        )

    def summarise(rows: list[dict], label: str) -> dict:
        ps = sorted(r["p_raw"] for r in rows if r["p_raw"] is not None)
        adm = sum(1 for r in rows if r["verdict"] == "ADMIT")
        n_null = sum(1 for r in rows if r["p_raw"] is None)
        # One-sided: how often does a placebo reach a p at least as small as the econ rule's?
        atleast = sum(1 for p in ps if p <= p_econ)
        return {"label": label, "n_draws": len(rows), "n_with_p": len(ps),
                "n_draws_with_no_p": n_null,
                "p_min": ps[0] if ps else None, "p_median": statistics.median(ps) if ps else None,
                "p_max": ps[-1] if ps else None,
                "p_mean": round(statistics.fmean(ps), 8) if ps else None,
                "n_admit": adm, "admit_frac": round(adm / len(rows), 4),
                "n_at_least_as_small_as_econ": atleast,
                "placebo_p_value_vs_econ": round((atleast + 1) / (len(ps) + 1), 4) if ps else None}

    s1, s2 = summarise(p1, "P1_uniform"), summarise(p2, "P2_year_matched")
    for s in (s1, s2):
        print(f"  {s['label']:16s} p min {s['p_min']} median {s['p_median']} max {s['p_max']} "
              f"| ADMIT {s['n_admit']}/{s['n_draws']} | "
              f"{s['n_at_least_as_small_as_econ']} draws reach p <= {p_econ}")

    verdict = (
        "H_calendar NOT REFUTED — the year-matched placebo reproduces the econ rule's p at "
        "least as often as chance would allow, so the improvement is what removing 20 trades "
        "from 2018+2020 does and the cost criterion adds nothing identifiable on top of it."
        if (s2["placebo_p_value_vs_econ"] or 1.0) > 0.10 else
        "H_calendar REFUTED at the 0.10 level — holding the calendar block fixed, a random "
        "20-trade removal from the same two years does NOT reach the econ rule's p, so the "
        "cost criterion is selecting something the year alone does not."
    )
    print(f"\n{verdict}")

    doc = {
        "schema": "gtos.wave10.an.econ_placebo.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AN", "blocks": "B1275-B1279", "sleeve": BTC,
        "exit": "target_5R", "band": "mid", "option": "B_balanced",
        "declared_family_size": base_spec.declared_family_size,
        "spec_sha256": base_spec.seal(), "seed": SEED, "tau": TAU, "n_draws": N_DRAWS,
        "gate_scope": ("SOLO on this sleeve; p_raw is independent of siblings, only q and the "
                       "significance gate read the family (am_submid_reclock.do_gate_solo)"),
        "reference": {
            "recorded_all": {"n": n_full, "p_raw": p_full, "verdict": v_full},
            "recorded_and_econ": {"n": n_econ, "p_raw": p_econ, "verdict": v_econ},
            "econ_dropped": {
                "n": len(dropped_idx), "by_year": dict(sorted(year_hist.items())),
                "mean_gross_r": round(statistics.fmean(recorded[i].r_gross
                                                       for i in dropped_idx), 6),
                "mean_gross_r_kept": round(statistics.fmean(r.r_gross for r in kept), 6)},
        },
        "criterion_is_entry_knowable": (
            "|total_r(high) - total_r(low)| is exactly |spread_r(high) - spread_r(low)| to "
            "2.2e-16 over all 232 trades, because commission, swap and slippage are "
            "band-independent and cancel. So the criterion is a function of (symbol, "
            "entry_utc, sl_distance_price) and cannot read a return."),
        "placebos": {"P1_uniform": {**s1, "draws": p1},
                     "P2_year_matched": {**s2, "draws": p2}},
        "verdict": verdict,
        "seconds_total": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(doc, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)} in {doc['seconds_total']}s")
    return doc


if __name__ == "__main__":
    main()
