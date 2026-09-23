"""Session AR, work order AR-1b — the PROSPECTIVE declaration of the `vr` sizing tilt.

    python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/ar_tilt_declaration.py

WHY THIS FILE EXISTS AND WHY IT IS COMMITTED ALONE
--------------------------------------------------
Session AO measured `vr` monotone in `sub_xvol_pullback`'s net R inside the sleeve's own
firing range (Spearman +0.4073, permutation p 0.00025, tertile net R/trade
0.512 -> 1.111 -> 2.124) and routed it to SIZING, because a level tilt costs no sample
while an admission filter costs the resolution that would justify it (AO section 0, third
refutation).

AO also did the harder half: it went looking for a cut on that axis and reported that the
only one it had was **the sample's own median**, which is post-hoc, and that the one
alternative it could name was `vr >= 2.0` — stamped in its own artifact as

    "AB_REGIME_DIALS_V1.json's own VOL_REGIME `bands` dict names xhi: 2.0. No
     implementation cuts there ... so 2.0 is a published-but-unimplemented boundary
     rather than a number this session chose"

and handed forward as *"the strongest candidate for the next session's pre-declaration."*

This file is that pre-declaration, and it is committed in a commit that contains **no
economics for the tilt** so that "declared before it was priced" is checkable in git rather
than asserted. The pattern is `ao_family_v3.py`'s (committed at `84e39021b`, a commit with no
gate result in it).

THE ONE CONSTANT THE TILT IS BUILT ON, AND WHERE IT COMES FROM
--------------------------------------------------------------
`vr` is ATR(14) over its own 100-bar mean (`primitives.vol_ratio`). `sub_xvol_pullback` pins
`vol=xhi`, which `substrate_engine._bucket_vr` implements as `vr >= 1.6` **with no ceiling**,
so every trade the sleeve has ever produced sits in one bucket and a bucket gate on it is the
identity filter (AO section 1: 88 of 88). The LEVEL inside that bucket is a different object,
and AR section 1 measures that it is fully free: **88 distinct values over 88 trades**, range
[1.6001, 2.3747].

The tilt therefore needs an interior reference inside `[1.6, inf)`. Exactly one exists that is
not a property of this sample:

    src/research_infra/regime_spine/dials.py:143
        bands={"lo": 0.85, "mid": 1.15, "hi": 1.6, "xhi": 2.0}

`2.0` is Session AB's published value for the `xhi` band, in production source, echoed in
`AB_REGIME_DIALS_V1.json`. Nothing implements a cut there — every bucketiser cuts hi/xhi at
1.6 — which is precisely what makes it usable here: it was never chosen to separate any
outcome, by AB or by anyone else. It is the tilt's unit-multiplier point.

WHAT IS DECLARED, IN FULL, WITH NOTHING LEFT TO CHOOSE LATER
------------------------------------------------------------
    mult(vr) = clamp(vr / 2.0, 0.80, 1.20)          applied to sub_xvol_pullback only

Every term:

  * **the ratio form** — the measured structure is a rank correlation over a continuum, not a
    bucket effect, so the faithful consumer is continuous. Exponent 1 is the
    least-assumption choice and is declared as 1 rather than fitted.
  * **the centre 2.0** — above. `mult(2.0) == 1.0` exactly.
  * **the clamp [0.80, 1.20]** — a SAFETY bound, not a shaping device, and the difference is
    checkable: over the 88 observed trades `vr / 2.0` runs [0.80005, 1.18735], so the clamp
    binds on **zero** trades. If a future bar arrives at vr 4.0 the tilt asks for 1.20, not
    2.00. The width is the declared damping level (see below).
  * **the damping, stated as a choice** — the measured tertile spread is 4.1x. A tilt that
    tracked it would ask for ~4x of size dispersion. This asks for 1.5x
    (1.20/0.80), i.e. about a third of the measured effect in log terms. That is the same
    posture `KELLY_LITE_BINS_HALF` takes against `KELLY_LITE_BINS` (`admission.py:915-917`):
    deploy the direction, damp the magnitude, because the magnitude is measured in-sample on
    the window that selected the sleeve and the risk caps are real.
  * **the scope** — `sub_xvol_pullback` only. Not a general regime dial. `crypto` and
    `energy_agri`, the other two armed sleeves, do not compute `vr` in their generators at
    all, so the tilt cannot reach them even by accident; the fail-closed behaviour when `vr`
    is absent is multiplier 1.0 (declared below).
  * **default OFF**, and the switch is `run_book.py --vol-level-tilt`, never a byte of
    `config/agent_config.yaml` or `config/profiles/redacted_account.yaml` (both carry live
    activation-token digests). Same mechanism as `--tags` and `--recover-pre-gap-bar`.

WHAT IS *NOT* DECLARED AS A CLAIM, AND THE PRICE OF THAT CHOICE
---------------------------------------------------------------
The sensitivities below are declared HERE, before any of them is computed, so that the
published set is the declared set and not the surviving set. None of them is a second claim
and none can admit anything — see `multiplicity` below.

A sizing tilt is **not** a member of `CANDIDATE_FAMILY`, and the reason is mechanical rather
than convenient: every family rule AL section 6.3 and AO section 6 state turns on *which
trades exist*. A threshold variant fires on a superset; a regime cell on a subset; a pool is a
new series. A sizing tilt changes **no trade's existence and no trade's R** — it changes the
weight the book puts on trades that are already there. It cannot produce an ADMIT or a REJECT,
so there is no p for a family to correct and no rank for it to consume. The bill it would cost
if a reader disagrees is priced anyway in `multiplicity.if_you_disagree`.

Offline, pure, no broker import, no config edit, no market data read.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

HERE = Path(__file__).resolve().parent
OUT = HERE / "VOL_LEVEL_TILT_DECLARATION_V1.json"

#: THE DECLARED TILT. These four numbers are the whole hypothesis. `admission.py` imports
#: nothing from this file — it carries its own literals — and
#: `tests/research_infra/test_ar_vol_level_tilt.py` asserts the two agree, so a later edit to
#: either one fails loudly rather than silently re-fitting the deployed tilt.
TILT_SLEEVE = "sub_xvol_pullback"
TILT_CENTRE = 2.0
TILT_MIN = 0.80
TILT_MAX = 1.20
TILT_EXPONENT = 1


def declaration() -> dict:
    return {
        "schema": "gtos.wave11.ar.vol_level_tilt_declaration.v1",
        "generated_by": str(Path(__file__).resolve().relative_to(REPO)),
        "session": "AR",
        "blocks": "B1450-B1499",
        "declaration_date": "2026-07-30",
        "declared_before": (
            "any economic measurement of the tilt. This file is committed in a commit that "
            "contains no tilt A/B, no book replay and no fold table, so the ordering is a "
            "property of git history rather than a claim in prose. The pattern is "
            "`ao_family_v3.py` at commit 84e39021b."
        ),
        "the_tilt": {
            "formula": "mult(vr) = clamp((vr / centre) ** exponent, min, max)",
            "sleeve": TILT_SLEEVE,
            "centre": TILT_CENTRE,
            "exponent": TILT_EXPONENT,
            "min": TILT_MIN,
            "max": TILT_MAX,
            "unit_point": f"mult({TILT_CENTRE}) == 1.0 exactly",
            "fail_closed": (
                "vr absent (None) or non-finite or <= 0 -> multiplier 1.0, i.e. the tilt is a "
                "no-op rather than a guess. A generator that has not populated vr must size "
                "exactly as it does today; this is the same convention the A8 metals "
                "confluence gate uses for its absent features (`admission.py:989-990`)."
            ),
            "default": "OFF",
        },
        "provenance_of_every_number": {
            "centre_2.0": {
                "source": "src/research_infra/regime_spine/dials.py:143",
                "literal": {"lo": 0.85, "mid": 1.15, "hi": 1.6, "xhi": 2.0},
                "echoed_in": (
                    "docs/audits/fable5-vision-audit-20260725/phase6/receipts/"
                    "AB_REGIME_DIALS_V1.json dials[1].bands"
                ),
                "why_it_is_not_a_sample_property": (
                    "AB published it as the `xhi` band's value in wave 6. No bucketiser "
                    "anywhere cuts there — `substrate_engine._bucket_vr` and "
                    "`af_repairs.bucket` both cut hi/xhi at 1.6 — so 2.0 has never been used "
                    "to separate an outcome by AB, AF, AH or AO. AO surfaced it explicitly as "
                    "'a published-but-unimplemented boundary rather than a number this "
                    "session chose' and handed it forward as 'the strongest candidate for the "
                    "next session's pre-declaration' "
                    "(phase10/receipts/ao_regime_conditioning.py, cell "
                    "`vr>=2.0_AB_published_xhi_band`, and section 10 item 4 of AO's result "
                    "doc). This file executes that hand-off."
                ),
            },
            "exponent_1": (
                "the least-assumption monotone form. Not fitted: no exponent other than 1 was "
                "computed before this file was committed, and the sensitivity list below is "
                "the complete set that will be reported."
            ),
            "clamp_0.80_1.20": {
                "role": "SAFETY bound, not a shaping device",
                "check_that_makes_the_distinction_real": (
                    "over the 88 archive trades `vr / 2.0` runs "
                    "[0.800068352096, 1.187367042136] (AR section 1, from "
                    "`AL_XVOL_REACHABLE_STATE_V1.json.gz` joined on the production "
                    "population), so the clamp binds on ZERO of them. It exists for the bar "
                    "that has not happened yet."
                ),
                "and_the_direction_of_the_declared_tilt_is_DOWN": (
                    "read before anything else: the multiplier's MEAN over those 88 trades is "
                    "0.924633 and its median 0.919052, because `vol=xhi` starts at 1.6 and "
                    "the centre is 2.0, so most of the sleeve's own firing range sits BELOW "
                    "the unit point. The declared tilt is therefore a net DE-RISK of about "
                    "7.5 % on `sub_xvol_pullback`, with the size-up reserved for the most "
                    "expanded ~20 % of its bars. That is a property of the formula and the vr "
                    "distribution — it carries no outcome information and is stated here, in "
                    "the declaration, so that nobody reads 'sizing tilt' as 'size up'. It is "
                    "also the conservative direction for a sleeve that is trading real money "
                    "on two funded accounts today."
                ),
                "width_is_the_declared_damping": (
                    "1.20/0.80 = 1.5x of deployed size dispersion against a measured 4.1x "
                    "tertile spread — about a third of the effect in log terms. Declared as a "
                    "choice, with its reason: the 4.1x is in-sample on the window that "
                    "selected this sleeve (Session V measured the `d.year >= 2025` predicate "
                    "shared by `build_survivor_book.py:60` and `KB7_growth_kelly_sizing.py:130`), "
                    "n is 78 priced trades, and OVERLAY_SIZEUP_MAX exists because unit risk is "
                    "capped. Same posture as KELLY_LITE_BINS_HALF vs KELLY_LITE_BINS."
                ),
            },
            "scope_one_sleeve": (
                "`sub_xvol_pullback` is where the structure was measured and it is the only "
                "sleeve whose generator computes `vr` at all "
                "(`substrate.py:_generate` -> `substrate_engine.compute_state`). The two other "
                "armed sleeves, `crypto` and `energy_agri`, cannot reach the tilt even by "
                "accident. `sub_mid_dn_revert` DOES compute vr and is deliberately excluded: "
                "AO's pre-declared direction there is NEGATIVE (calmer is better inside "
                "`vol=mid`) and its per-trade rho is -0.0062 at permutation p 0.88, so there "
                "is no measured level structure to consume. Extending the tilt to it would be "
                "a new hypothesis needing its own declaration."
            ),
        },
        "sensitivities_declared_now_so_the_published_set_is_the_declared_set": [
            {
                "name": "step_form_at_the_same_cut",
                "what": (
                    "the two-bin step the codebase's existing consumers look like: "
                    "mult = 1.0 for vr < 2.0, mult = 1.20 for vr >= 2.0."
                ),
                "why_reported": (
                    "it is the discrete reading of the same published boundary, and a reader "
                    "who distrusts continuous tilts should be able to see what the discrete "
                    "one costs without asking for a re-run."
                ),
                "admissible": False,
            },
            {
                "name": "clamp_width_envelope",
                "what": "the same ratio form at clamps [0.90, 1.10] and [0.70, 1.30].",
                "why_reported": (
                    "the damping level is the one free choice in the declaration, so its "
                    "envelope travels with the result instead of being defended in prose."
                ),
                "admissible": False,
            },
            {
                "name": "sample_median_centre",
                "what": "the same ratio form centred on the sample median vr instead of 2.0.",
                "why_reported": (
                    "AO's own post-hoc alternative, reported so the cost of the honest cut is "
                    "visible. If the median centre is much better, that is a fact a reader is "
                    "entitled to, and it is disclosed as post-hoc rather than adopted."
                ),
                "admissible": False,
            },
            {
                "name": "zero_tilt_control",
                "what": "the tilt OFF. The A/B baseline and the default-path identity check.",
                "admissible": True,
                "note": "the control is the thing the deployed book already does.",
            },
        ],
        "multiplicity": {
            "joins_candidate_family": False,
            "why_not": (
                "every family rule in AL section 6.3 and AO section 6 turns on which trades "
                "exist: a threshold variant fires on a superset, a regime cell on a subset, a "
                "pool is a new series. A sizing tilt changes no trade's existence and no "
                "trade's R — it changes the weight the book puts on trades already there. It "
                "produces no p, holds no BH rank, and cannot ADMIT or REJECT anything. "
                "`CANDIDATE_FAMILY_V3` is unchanged by this work order and its sha256 travels "
                "on every arm."
            ),
            "if_you_disagree": (
                "the tilt is one hypothesis with one declared parameterisation. Declaring it "
                "would move `CANDIDATE_BOOK_V1` 39 -> 40 all-declared, which tightens BH rank "
                "1 at alpha 0.10 from 0.002564 to 0.002500 (-2.5 %) and rank 2 from 0.005128 "
                "to 0.005000. `mx_btcusd @ target_5R` at p 0.0011 survives that with room, so "
                "the disagreement is affordable and is priced here rather than argued."
            ),
            "trial_ledger": (
                "every arm — deployed form, all three sensitivity families, and the control — "
                "is recorded in research/operations/trial_budget/TRIAL_LEDGER.jsonl under "
                "mechanism `vol_level_sizing_tilt`. A look that changes no p is still a look."
            ),
        },
        "what_would_falsify_it": (
            "the tilt is a claim about the ORDERING of net R in vr, deployed as a claim about "
            "the SIZE the book should put behind that ordering. It is falsified if the "
            "cost-true book A/B is negative — i.e. if reallocating risk toward the more "
            "expanded half of the sleeve's own firing range loses money at broker-true cost on "
            "a shared equity curve — and it is NOT rescued by the rank correlation if that "
            "happens, because the rank correlation is the input, not the result. It is "
            "separately falsified, and more importantly, if the improvement lives only in the "
            "EARLY chronological folds: AN measured a 7.6x decay on the estate's one "
            "admission, so the recent folds are the expectancy basis for anything that will be "
            "sized (wave-11 agreement section 1)."
        ),
        "not_an_owner_decision_yet": (
            "this file declares a hypothesis and nothing else. Building the switch is AR-1c, "
            "pricing it is AR-1d, and ARMING it is Borhen's, on the number AR-1d publishes."
        ),
        "constants": {
            "TILT_SLEEVE": TILT_SLEEVE, "TILT_CENTRE": TILT_CENTRE,
            "TILT_MIN": TILT_MIN, "TILT_MAX": TILT_MAX, "TILT_EXPONENT": TILT_EXPONENT,
        },
    }


def main() -> int:
    d = declaration()
    body = json.dumps(d, indent=2, sort_keys=True)
    d["self_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    OUT.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    print(f"  tilt: mult(vr) = clamp((vr/{TILT_CENTRE})**{TILT_EXPONENT}, "
          f"{TILT_MIN}, {TILT_MAX}) on {TILT_SLEEVE}, default OFF")
    print(f"  declaration sha256 {d['self_sha256'][:16]}")
    print(f"  sensitivities declared: "
          f"{[s['name'] for s in d['sensitivities_declared_now_so_the_published_set_is_the_declared_set']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
