#!/usr/bin/env python3
"""Session CA (B2148-B2149) — the incubation dossier for the sleeve that is ARMED WITHOUT ONE.

    python3 .../phase14/receipts/ca_mx_incubation.py --check
    python3 .../phase14/receipts/ca_mx_incubation.py --apply    # also amends the conditions

WHY THIS FILE EXISTS, AND WHY IT IS NOT WHAT THE COMMISSION EXPECTED
---------------------------------------------------------------------
CA-2 asks for an incubation dossier for any `REVIVAL_CANDIDATE`. There are none: all three
revival gates came back STAYS_DEAD or NOT_EVALUABLE (`CA_REVIVAL_GATE_V1.json`). Writing
nothing would be the letter of the commission and a waste of the lane it was built for,
because the estate already HAS an incubant and it is running without the paperwork:

**`mx_btcusd_d1_donchian_20_breakout` has been live on FTMO since 2026-07-31 ~01:26 UTC at
registry confidence 0.025, and `FIVE_SLEEVE_STOP_CONDITIONS_V1.json` carries no row for it
at all.** Not a loose one — none. Measured, not asserted:
`tests/ultimate_book/test_book_sleeve_telemetry.py::test_every_armed_sleeve_has_a_live_contract_and_a_floor`
fails on exactly that name the moment the armed set is brought up to date.

The Training Lane constitution ratified 2026-07-31 says, in §4: *"Each incubant carries
pre-registered stop AND promotion rules, written before arming"*. The arming happened first.
The honest repair is not to pretend otherwise — the record says the rules are being written
AFTER, and this file says so in its own artifact — it is to write them now, derived rather
than chosen, and to make the next incubant's paperwork precede its ceremony.

EVERY THRESHOLD IS DERIVED, AND THE PROVENANCE IS BETTER THAN AS's OWN
-----------------------------------------------------------------------
The formulas are Session AS's, imported rather than retyped: `false_trip_probability`,
`solve_evidence_floor`, `POWER_HORIZON_FILLS = 60`, `FALSE_TRIP_TARGET = 0.10`. The INPUTS
are not AS's, and that is deliberate. `AS_LIVE_SLEEVE_BASIS_V1.json` carries its own
`PROVENANCE_WARNING`: its expectancies come from the W7 recost cache while its holds and
nights come from the AA estate walk, and for `fx_jpy` the two disagree by 4.2x on the same
sleeve. `mx_btcusd` has **no W7 cache rows at all**, so that mixture is not even available
here — and the alternative is strictly better: read every input from ONE object, the gate's
own `diagnose=True` cost decomposition at the ratified rule, on the target_5R contract the
book actually runs.

THE PROMOTION RULE IS THE MIRROR OF THE EVIDENCE FLOOR, NOT A HOPE
-------------------------------------------------------------------
A stop rule without a promotion rule turns an incubant into a sleeve that can only ever be
killed. The promotion ceiling here is the shallowest 0.5 R step whose probability of being
reached within the same 60-fill horizon **by a sleeve with true mean ZERO** is at or under
the same 0.10 — the exact mirror of S1b, on the same bootstrap, over the same distribution.
Reaching it is not proof of an edge; it is the level at which luck alone is an unlikely
explanation, which is the most a live stream of this length can offer.

BOUNDARY. Offline and pure. Reads committed artifacts and the read-only bar archive; writes
one JSON and (with --apply) amends one receipt. No broker, no VPS, no config write. Files a
dossier; arming, sizing and promotion are the owner's ceremony every time.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import importlib.util as ilu
import json
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
P7 = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
P11 = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(P7))

COND = P11 / "FIVE_SLEEVE_STOP_CONDITIONS_V1.json"
ESTATE = P11 / "AQ_ESTATE_TRADES_V2.json.gz"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
OUT = HERE / "CA_MX_INCUBATION_V1.json"

SLEEVE = "mx_btcusd_d1_donchian_20_breakout"
ACCOUNT, SERVER = "FTMO", "FTMO-Server3"
KEY = f"{ACCOUNT}::{SLEEVE}"
BAND = "mid"
ARMED_UTC = "2026-07-31T01:26:00Z"
PROMOTION_SEED = 20260731


def _as_module():
    spec = ilu.spec_from_file_location("as_live_basis", P11 / "as_live_basis.py")
    m = ilu.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def _mx_rows_target_5r():
    import ad_exit_sweep as AD
    est = json.loads(gzip.open(ESTATE, "rt").read())
    series, index, _ = AD.load_bars()
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule(SERVER)
    var = AD.Variant(name="target_5R", family="target", target_mode="fixed_r", target_r=5.0)
    rows, tel = AD.resimulate(est["trades"][SLEEVE], var, series, index, costs, ACCOUNT, rule)
    return rows, dict(tel)


def _gate_diagnostics(rows: list[dict]) -> dict:
    """The single object every input below is read from: the gate at the ratified rule."""
    import ad_exit_sweep as AD
    from src.research_infra.walkforward import candidate_family as CF
    from src.research_infra.walkforward import era_population as EP
    from src.research_infra.walkforward import run_gate
    from src.research_infra.walkforward.options import OPTIONS

    o = OPTIONS["B_balanced"]
    spec = o.with_(spec_id=f"{o.spec_id}_ca_mx_incubation",
                   sleeve_symbol_allowlist=AD.allowlist(), spread_band=BAND, account=ACCOUNT)
    spec = CF.with_declared_family(
        spec, "CANDIDATE_BOOK_V1", loaded=CF.load_candidate_family(HERE / "CANDIDATE_FAMILY_V12.json"))
    recs = {SLEEVE: AD.to_records(rows)}
    recs, spec, mix = EP.apply("RECORDED", recs, spec, account=ACCOUNT)
    costs = AD.load_broker_true_costs(COSTS)
    res = run_gate(recs, spec, costs=costs, server=SERVER, diagnose=True)
    v = res.verdicts[SLEEVE]
    # `diagnostics.cost_decomposition.swap_nights` carries mean/median/max/frac_zero but NOT
    # p90, and S3's alert threshold is the p90. AD's `measured_nights_by_sleeve` HAS one for
    # this sleeve (10.0) and it is the wrong contract -- AD walked the committed 2R cell,
    # whose nights mean 4.81 against target_5R's 11.94. So it is computed here, on the
    # population that actually runs, rather than borrowed from a contract the book does not.
    from src.research_infra.walkforward.panel import price_trades
    priced, _cov = price_trades(recs[SLEEVE], spec, costs=costs)
    nights = sorted(p.swap_nights for p in priced
                    if p.status == "priced" and p.swap_nights is not None)
    p90_nights = (nights[min(len(nights) - 1, int(0.9 * len(nights)))] if nights else None)
    d = v.diagnostics or {}
    cd = d.get("cost_decomposition") or {}
    terms = cd.get("terms") or {}
    nights = cd.get("swap_nights") or {}
    hold = d.get("holding") or {}
    return {
        "spec_sha256": spec.seal(), "population_mix": mix,
        "verdict": v.verdict.value, "n_trades": v.n_trades,
        "pooled_oos_mean_r_per_day": v.pooled_oos_mean_r,
        "p_raw": v.p_raw, "q_value": v.q_value,
        "oos_mean_r_per_trade": v.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
        "mean_gross_r": cd.get("mean_gross_r"),
        "mean_net_r": cd.get("mean_net_r"),
        "mean_total_cost_r": cd.get("mean_total_cost_r"),
        "cost_terms_mean_r": {k: (terms.get(k) or {}).get("mean_r")
                              for k in ("commission_r", "spread_r", "slippage_r", "swap_r")},
        "swap_nights": {**{k: (cd.get("swap_nights") or {}).get(k)
                           for k in ("n", "mean", "median", "max", "frac_zero")},
                        "p90": (None if p90_nights is None else round(float(p90_nights), 4)),
                        "p90_basis": ("computed here from price_trades on the target_5R "
                                      "population; the diagnostics block carries no p90 and "
                                      "AD's 10.0 is the committed 2R contract's")},
        "holding": {k: hold.get(k) for k in ("median_hours", "p90_hours", "frac_over_24h")},
        "fold_table": [{k: f.get(k) for k in ("fold_id", "status", "oos_start", "oos_end",
                                              "n_test_trades", "oos_mean_r_per_day")}
                       for f in (v.folds or [])],
    }


def _promotion_ceiling(centred, n_fills, target, draws=20000, seed=PROMOTION_SEED):
    """Shallowest 0.5 R step a ZERO-mean sleeve reaches within `n_fills` with prob <= target."""
    rng = random.Random(seed)

    def p_reach(ceil_):
        hits = 0
        for _ in range(draws):
            cum = 0.0
            for _ in range(n_fills):
                cum += rng.choice(centred)          # true mean ZERO — the null being excluded
                if cum >= ceil_:
                    hits += 1
                    break
        return hits / draws

    ceil_ = 0.5
    while ceil_ < 200.0:
        p = p_reach(ceil_)
        if p <= target:
            return round(ceil_, 2), round(p, 4)
        ceil_ += 0.5
    return None, None


def build() -> dict:
    AS = _as_module()
    rows, tel = _mx_rows_target_5r()
    diag = _gate_diagnostics(rows)

    rs = [float(r["r_gross"]) for r in rows if r.get("r_gross") is not None]
    mean_r = statistics.fmean(rs)
    centred = [x - mean_r for x in rs]
    sd = statistics.pstdev(rs)

    # THE EXPECTANCY THE FLOORS ARE BUILT ON. AS's shape, one object's inputs:
    #   net = mean_gross - cost_ex_swap - swap_per_night * measured_nights_mean
    gross = float(diag["mean_gross_r"])
    t = diag["cost_terms_mean_r"]
    # SIGN, stated because a first cut got it backwards and it doubled the expectancy.
    # `diagnostics.terms.*.mean_r` are POSITIVE COST MAGNITUDES -- the block's own
    # `mean_net_r = mean_gross_r - total` (diagnostics.py:251) settles it -- so every term is
    # SUBTRACTED here. Read as signed R the net came out 1.2907 against a true 0.7574, which
    # is 1.7x, and every floor derived from it would have been 1.7x too loose on live money.
    # The check that caught it: mean_gross_r - sum(terms) must equal `mean_net_r`, asserted
    # below rather than eyeballed.
    cost_ex_swap = sum(float(t.get(k) or 0.0)
                       for k in ("commission_r", "spread_r", "slippage_r"))
    nights_mean = float(diag["swap_nights"]["mean"] or 0.0)
    swap_mean_r = float(t.get("swap_r") or 0.0)
    swap_per_night = (swap_mean_r / nights_mean) if nights_mean else 0.0
    net_expect = gross - cost_ex_swap - swap_per_night * nights_mean
    recomputed_net = gross - (cost_ex_swap + swap_mean_r)
    if abs(net_expect - recomputed_net) > 1e-6:
        raise SystemExit(f"cost-term sign check failed: {net_expect} != {recomputed_net}")
    if diag.get("mean_net_r") is not None and abs(net_expect - float(diag["mean_net_r"])) > 1e-5:
        raise SystemExit(
            f"net expectancy {net_expect} disagrees with the gate's own mean_net_r "
            f"{diag['mean_net_r']}; the decomposition's sign convention has moved.")

    risk_floor = -max(3.0, 12.0 * abs(net_expect))
    p_risk = AS.false_trip_probability(centred, net_expect, risk_floor, AS.POWER_HORIZON_FILLS)
    ev_floor, p_ev = AS.solve_evidence_floor(centred, net_expect, start=risk_floor)
    ceil_r, p_ceil = _promotion_ceiling(centred, AS.POWER_HORIZON_FILLS, AS.FALSE_TRIP_TARGET)

    # S3/S4 inputs, same object
    be_nights = (net_expect / swap_per_night) if swap_per_night > 0 else None
    med_hold = float(diag["holding"]["median_hours"] or 0.0)

    dossier = {
        "schema": "gtos.wave14.ca.incubation_dossier.v1",
        "session": "CA", "blocks": "B2148-B2149",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "sleeve": SLEEVE, "account": ACCOUNT, "armed_utc": ARMED_UTC,
        "the_honest_header": (
            "WRITTEN AFTER ARMING. The Training Lane constitution (§4, ratified 2026-07-31) "
            "requires pre-registered stop AND promotion rules written BEFORE arming; this "
            "sleeve was armed at ~01:26Z the same day with no row in "
            "FIVE_SLEEVE_STOP_CONDITIONS_V1.json at all. The rules below are derived, not "
            "chosen, and no live fill exists yet for them to have been fitted to — the "
            "expected fill count since arming is 0.105 (CA_FIRST_WEEK_V1.json) — but the "
            "ORDER was wrong and the record says so."),
        "why_it_is_armed": (
            "the estate's only admission at the sealed alpha: RECORDED population, "
            "B_balanced alpha 0.10, CANDIDATE_BOOK_V1, admits at two of three cost bands. "
            "Registry confidence 0.025 (0.32 % of book weight) — economically small BY "
            "DESIGN; the forward record is the point (OD-AI-5: admission = eligibility)."),
        "proposed_weight_class": {
            "current_registry_confidence": 0.025,
            "incubation_ceiling": 0.05,
            "note": ("Training Lane §4 caps an incubant at the 0.05 class and at most 5 "
                     "concurrent incubants. This sleeve is at HALF the ceiling and is the "
                     "estate's only incubant, so nothing here proposes a change. Any move "
                     "off 0.025 is an owner ceremony and needs the promotion rule below to "
                     "have fired first."),
        },
        "contract_it_runs": {
            "cell": "target_5R", "mechanism": "--frontier-exits (run_book.py, default OFF)",
            "committed_profile_final_target_r": 2.0,
            "frontier_final_target_r": 5.0,
            "time_stop_bars_m15": 7680,
            "both_repairs_it_is_contingent_on": [
                "AQ's time-stop unit repair (96 -> 7680; 96 was the M15-per-D1 RATIO)",
                "AU's --frontier-exits wiring, proved trade-by-trade identical to the "
                "research cell (318/318)"],
            "relabel_telemetry": tel,
        },
        "measured_basis_ONE_OBJECT": {
            "source": ("run_gate(diagnose=True) at the ratified rule, band mid, FTMO, on the "
                       "target_5R rows — every input below comes from this one call, which "
                       "is why no PROVENANCE_WARNING of the AS kind applies here"),
            **diag,
            "archive_r_dispersion_sd": round(sd, 6),
            "n_archive_trades": len(rs),
            "mean_r_gross_unpriced": round(mean_r, 6),
            "cost_ex_swap_r": round(cost_ex_swap, 6),
            "swap_r_per_night": round(swap_per_night, 6),
            "archive_net_r_per_trade_at_measured_carry": round(net_expect, 6),
        },
        "STOP_RULES": {
            "S1a_risk_floor": {
                "cumulative_net_r_floor": round(risk_floor, 3),
                "derivation": ("-max(3.0, 12 * |mean_gross - cost_ex_swap - swap_per_night * "
                               "measured_nights_mean|) — Session AS's formula, this session's "
                               "inputs. A STATEMENT OF TOLERANCE, not a test."),
                "measured_false_trip_probability_within_60_fills": p_risk,
                "fills_to_trip_at_archive_expectancy": (
                    None if net_expect <= 0 else round(abs(risk_floor) / net_expect, 1)),
                "class": "RISK_BOUND_not_inference",
                "action": "remove from --tags on FTMO (orchestrator ceremony)",
            },
            "S1b_evidence_floor": {
                "evidence_floor_r": ev_floor,
                "measured_false_trip_probability_within_60_fills": p_ev,
                "derivation": (f"the deepest 0.5 R step at which P(cumulative net R touches "
                               f"the floor within {AS.POWER_HORIZON_FILLS} fills | true mean "
                               f"= the archive expectancy) <= {AS.FALSE_TRIP_TARGET:.2f}, by "
                               f"bootstrap over this sleeve's OWN centred archive R "
                               f"distribution at the target_5R contract"),
                "class": "INFERENCE",
            },
            "S2_gross_negative": {
                "min_fills": 20, "min_day_blocks": 8, "requires_both_weightings": True,
                "class": "RISK_BOUND_not_inference",
                "note": "inherited unchanged from the family-wide S2; no per-sleeve number",
            },
            "S3_carry_surprise": {
                "measured_nights_p90": diag["swap_nights"]["p90"],
                "break_even_nights": (None if be_nights is None else round(be_nights, 3)),
                "alert_mean_nights_above": diag["swap_nights"]["p90"],
                "stop_mean_nights_above": (None if be_nights is None else round(be_nights, 3)),
                "zero_carry_sleeve": bool(nights_mean < 0.05),
                "derivation": ("alert at the measured p90 nights; stop at break-even = "
                               "net_expect / swap_per_night — the point past which the "
                               "sleeve's own arithmetic says carry has eaten the edge"),
            },
            "S4_hold_time_surprise": {
                "archive_median_hold_hours": med_hold,
                "archive_p90_hold_hours": diag["holding"]["p90_hours"],
                "alert_median_hold_hours_above": round(3.0 * med_hold, 2),
                "derivation": "3x the archive median, family-wide rule",
                "contract_fidelity_class": (
                    "UNIT_CORRECT_AFTER_AQ — time_stop_bars 7680 M15 = 80 D1 bars = the "
                    "research maxbars, so the live stop can only bind where the walk already "
                    "truncated. Before AQ's repair it was 96 M15 = ONE D1 bar and 82.3 % of "
                    "this sleeve's trades would have been cut at ~24 h."),
                "the_open_hazard": (
                    "B1452: an open mx_* position asks for 7,744 M15 bars per tick. If the "
                    "terminal returns fewer than 7,680 CLOSED M15 bars the count can never "
                    "reach the budget and the time stop never fires at all — INERT, not "
                    "late, and the wall-clock fallback does not catch it. Measure the "
                    "terminal's copy_rates ceiling; this sleeve is the first of its cohort "
                    "ever armed."),
            },
            "S5_stop_out_run": {"alert_run": 6, "stop_run": 9,
                                "note": "inherited unchanged from the family-wide S5"},
        },
        "PROMOTION_RULE": {
            "cumulative_net_r_ceiling": ceil_r,
            "horizon_fills": AS.POWER_HORIZON_FILLS,
            "measured_false_promotion_probability": p_ceil,
            "derivation": (f"the shallowest 0.5 R step a sleeve with true mean ZERO reaches "
                           f"within {AS.POWER_HORIZON_FILLS} fills with probability <= "
                           f"{AS.FALSE_TRIP_TARGET:.2f}, by bootstrap over this sleeve's own "
                           f"centred archive R distribution. The exact mirror of S1b."),
            "what_reaching_it_means": (
                "that luck alone is an unlikely explanation of the live record — NOT that "
                "the edge is established. It is the most a stream this short can offer."),
            "what_reaching_it_AUTHORISES": (
                "a request to Borhen to move the sleeve off the 0.025 class toward the 0.05 "
                "incubation ceiling. Nothing automatic: arming, sizing and promotion are an "
                "owner ceremony every time (Training Lane §4)."),
            "the_calendar_this_implies": (
                "at the live-equivalent fill rate CA measured for this sleeve (0.270 "
                "fills/week), 60 fills is about 51 months. The promotion rule is therefore "
                "NOT a plan to promote — it is the honest price of promotion on evidence, "
                "and the estate should read it as an argument for a cheaper instrument "
                "rather than as a schedule."),
        },
        "expected_economics_on_RECENT_folds": {
            "planning_number_r_per_day": 0.198,
            "basis": ("the RECENT folds, per the ratified population rule's sizing clause — "
                      "never the +0.982 full-window mean. AN measured a 7.6x chronological "
                      "decay on this admission (recent +0.198 = 13.2 % of the early folds' "
                      "+1.504) and no gate can see decay by construction."),
            "fold_table": diag["fold_table"],
            "at_registry_confidence_0.025": (
                "0.32 % of book weight — AI measured that admitting this sleeve at this "
                "weight is economically INERT. Re-weighting is a separate owner decision."),
        },
        "the_fill_truth_this_sleeve_lives_under": {
            "own_archive_decisions": 318,
            "own_live_equivalent_fills_at_target_5R": 134,
            "own_suppression_frac": 0.579,
            "note": ("57.9 % of this sleeve's decisions never become fills: one open position "
                     "per broker symbol across the whole book, and it trades BTCUSD which "
                     "`crypto` also trades. At its committed 2R contract the suppression is "
                     "43.4 % — the frontier's longer holds cost it 46 of its own fills and "
                     "cost `crypto` 5 more. Source: CA_FILL_TRUTH_RESTATE_V1.json."),
        },
        "what_this_dossier_does_NOT_do": (
            "it arms nothing, promotes nothing and changes no weight. It supplies the rows "
            "that were missing from a live sleeve's monitoring, and it records that they "
            "were written after the ceremony rather than before it."),
    }
    return dossier


def amend_conditions(d: dict) -> None:
    """Add the derived rows to the live conditions artifact, per account key."""
    doc = json.loads(COND.read_text())
    C = doc["conditions"]
    S = d["STOP_RULES"]
    C["S1a_risk_floor"]["per_sleeve_account"][KEY] = {
        "archive_net_r_per_trade_at_measured_carry":
            d["measured_basis_ONE_OBJECT"]["archive_net_r_per_trade_at_measured_carry"],
        "cumulative_net_r_floor": S["S1a_risk_floor"]["cumulative_net_r_floor"],
        "derivation": S["S1a_risk_floor"]["derivation"],
        "measured_false_trip_probability_within_60_fills":
            S["S1a_risk_floor"]["measured_false_trip_probability_within_60_fills"],
        "false_trip_note": None,
        "fills_to_trip_at_archive_expectancy":
            S["S1a_risk_floor"]["fills_to_trip_at_archive_expectancy"],
        "fills_to_trip_at_live_prior": None,
        "added_by": "Session CA (wave 14) — see phase14/receipts/CA_MX_INCUBATION_V1.json",
    }
    C["S1b_evidence_floor"]["per_sleeve_account"][KEY] = {
        "evidence_floor_r": S["S1b_evidence_floor"]["evidence_floor_r"],
        "measured_false_trip_probability_within_60_fills":
            S["S1b_evidence_floor"]["measured_false_trip_probability_within_60_fills"],
        "archive_r_dispersion_sd": d["measured_basis_ONE_OBJECT"]["archive_r_dispersion_sd"],
        "n_archive_trades": d["measured_basis_ONE_OBJECT"]["n_archive_trades"],
        "derivation": S["S1b_evidence_floor"]["derivation"],
        "added_by": "Session CA (wave 14)",
    }
    C["S3_carry_surprise"]["per_sleeve_account"][KEY] = {
        **{k: v for k, v in S["S3_carry_surprise"].items()},
        "note": None, "added_by": "Session CA (wave 14)"}
    C["S4_hold_time_surprise"]["per_sleeve"][SLEEVE] = {
        "archive_median_hold_hours": S["S4_hold_time_surprise"]["archive_median_hold_hours"],
        "archive_p90_hold_hours": S["S4_hold_time_surprise"]["archive_p90_hold_hours"],
        "live_time_stop_own_bars": 80.0, "research_maxbars_own_bars": 80,
        "alert_median_hold_hours_above":
            S["S4_hold_time_surprise"]["alert_median_hold_hours_above"],
        "derivation": S["S4_hold_time_surprise"]["derivation"],
        "time_stop_vs_research_horizon":
            "EQUALS the research maxbars after AQ's unit repair (7680 M15 = 80 D1 bars)",
        "contract_fidelity_class": S["S4_hold_time_surprise"]["contract_fidelity_class"],
        "the_open_hazard": S["S4_hold_time_surprise"]["the_open_hazard"],
        "added_by": "Session CA (wave 14)",
    }
    C.setdefault("P1_promotion", {
        "what": ("cumulative NET R since arming rises above the level a ZERO-mean sleeve "
                 "reaches with probability <= 0.10 over the same 60-fill horizon"),
        "class": "INFERENCE",
        "action": ("authorises a REQUEST to Borhen to move the sleeve toward the 0.05 "
                   "incubation ceiling. Nothing automatic — promotion is an owner ceremony."),
        "why_it_exists": ("Training Lane §4: an incubant carries pre-registered stop AND "
                          "promotion rules. Without the second half an incubant can only "
                          "ever be killed, which is not an incubation lane."),
        "per_sleeve_account": {},
    })["per_sleeve_account"][KEY] = d["PROMOTION_RULE"]
    doc.setdefault("amendments", []).append({
        "at": "2026-07-31", "by": "Session CA (wave 14), blocks B2148-B2149",
        "fields": [f"conditions.S1a_risk_floor.per_sleeve_account.{KEY}",
                   f"conditions.S1b_evidence_floor.per_sleeve_account.{KEY}",
                   f"conditions.S3_carry_surprise.per_sleeve_account.{KEY}",
                   f"conditions.S4_hold_time_surprise.per_sleeve.{SLEEVE}",
                   f"conditions.P1_promotion.per_sleeve_account.{KEY}"],
        "why": ("mx_btcusd was armed on FTMO 2026-07-31 ~01:26Z with NO row in this artifact. "
                "These rows are ADDED, not amended — no existing threshold moves. Derived by "
                "phase14/receipts/ca_mx_incubation.py from ONE object (the gate's own "
                "diagnose=True decomposition at the ratified rule on the target_5R contract), "
                "using Session AS's formulas imported rather than retyped."),
        "written_after_arming": True,
        "no_live_fill_existed_when_written": ("expected fill count since arming 0.105 — "
                                              "CA_FIRST_WEEK_V1.json"),
    })
    COND.write_text(json.dumps(doc, indent=1, sort_keys=False, default=str) + "\n")
    print(f"amended {COND.relative_to(REPO)}: 5 rows ADDED for {SLEEVE}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d = build()
    OUT.write_text(json.dumps(d, indent=1, sort_keys=False, default=str) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    b = d["measured_basis_ONE_OBJECT"]
    print(f"  gate: {b['verdict']} n={b['n_trades']} R/day={b['pooled_oos_mean_r_per_day']} "
          f"p={b['p_raw']}")
    print(f"  net expectancy/trade {b['archive_net_r_per_trade_at_measured_carry']}  "
          f"sd {b['archive_r_dispersion_sd']}  nights_mean {b['swap_nights']['mean']}")
    print(f"  S1a risk floor   {d['STOP_RULES']['S1a_risk_floor']['cumulative_net_r_floor']} R "
          f"(false trip {d['STOP_RULES']['S1a_risk_floor']['measured_false_trip_probability_within_60_fills']})")
    print(f"  S1b evidence     {d['STOP_RULES']['S1b_evidence_floor']['evidence_floor_r']} R "
          f"(false trip {d['STOP_RULES']['S1b_evidence_floor']['measured_false_trip_probability_within_60_fills']})")
    print(f"  P1 promotion     +{d['PROMOTION_RULE']['cumulative_net_r_ceiling']} R "
          f"(false promotion {d['PROMOTION_RULE']['measured_false_promotion_probability']})")
    if a.apply:
        amend_conditions(d)
    else:
        print("\n--check only; the conditions artifact is untouched. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
