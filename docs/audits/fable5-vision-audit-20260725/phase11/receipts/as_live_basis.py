#!/usr/bin/env python3
"""AS-1 — the measured basis for the ARMED FIVE-sleeve book, and the stop conditions derived from it.

Two artifacts, both generated and neither transcribed:

  AS_LIVE_SLEEVE_BASIS_V1.json      per (sleeve, account): the live exit contract read out of the
                                    RUNNING module, the archive-walk economics, AD's measured carry,
                                    and — where it exists — the sleeve's own LIVE-FILL prior.
  FIVE_SLEEVE_STOP_CONDITIONS_V1.json
                                    the pre-registered stop conditions, every threshold DERIVED from
                                    a basis field with the field named, so no number here is a
                                    preference.

Why this exists: the expansion to five sleeves (`phase8/receipts/FIVE_SLEEVE_EXPANSION_20260730.md`)
armed `fx_jpy` and `sub_mid_dn_revert` on the owner's explicit risk acceptance rather than on a
passed gate. A risk acceptance without a pre-registered exit is not a decision, it is a hope. These
are the exits, written BEFORE the first post-arming fill exists so they cannot be chosen to fit it.

The one statistical rule this file enforces on itself: the dependence unit for these sleeves is the
DECISION DAY, not the fill (Session R measured lag-1 rho 0.511 on `sub_xvol_pullback`; the live
`fx_jpy` corpus puts up to 4 fills on one day). So every economic statement is made BOTH
trade-weighted and day-weighted, and every inferential claim is an exact sign-flip permutation over
day blocks with its own resolution floor reported (wave-11 agreement §2).

Read-only. No broker, no VPS, no config write.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

AUDIT = ROOT / "docs/audits/fable5-vision-audit-20260725"
OUT_DIR = AUDIT / "phase11/receipts"

CARRY_TIERS = AUDIT / "phase7/receipts/AD_CARRY_TIERS_RESTATED_V1.json"
LIVE_ROWS = AUDIT / "phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl"
EXPANSION_RECEIPT = AUDIT / "phase8/receipts/FIVE_SLEEVE_EXPANSION_20260730.md"
CONTRACT_TRUTH = AUDIT / "phase11/receipts/AQ_CONTRACT_TRUTH_V1.json"

#: The armed set, in the order `--tags` carries it on both hosts. Source: the expansion receipt,
#: host commit f855250cd. NOT a preference of this file — asserted against the receipt below.
ARMED_TAGS: tuple[str, ...] = (
    "crypto", "energy_agri", "sub_xvol_pullback", "fx_jpy", "sub_mid_dn_revert",
)
#: Armed 2026-07-29 12:55 UTC (three sleeves), five sleeves from ~11:52 UTC 2026-07-30.
ARMED_UTC = {"FTMO": "2026-07-30T11:52:00Z", "redacted_account": "2026-07-30T11:52:00Z"}
ACCOUNTS = ("FTMO", "redacted_account")
#: `LIVE_TRADE_ROWS.jsonl` labels accounts lower-case; AD's carry rows use the display names.
ACCOUNT_KEY = {"FTMO": "ftmo", "redacted_account": "redacted_account"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# the sign-flip permutation — ONE implementation, imported from the tool that consumes this artifact
# ---------------------------------------------------------------------------
# Deliberately not re-implemented here. Two copies of a permutation test drift, and when they do the
# artifact and the page disagree about the same fills with nothing to say which is right.
def _load_signflip():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_as_telemetry", ROOT / "scripts/book_sleeve_telemetry.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.signflip_p


signflip_p = _load_signflip()


# ---------------------------------------------------------------------------
# the false-trip bootstrap — what a floor actually costs in false alarms
# ---------------------------------------------------------------------------
#: A stop condition without a measured false-alarm rate is a number somebody liked. These are the
#: constants of that measurement, named so the artifact can publish them.
POWER_HORIZON_FILLS = 60          #: ~2 years of fills for the thinnest armed sleeve
FALSE_TRIP_TARGET = 0.10          #: the evidence floor's ceiling on false alarms
BOOTSTRAP_DRAWS = 20_000
BOOTSTRAP_SEED = 20260730         #: fixed, so every number here is reproducible


def archive_r_dispersion() -> dict:
    """Each armed sleeve's OWN per-trade R distribution, centred, from its own archive population.

    `sub_mid_dn_revert` uses AQ-3's re-clocked V2 population, the same substitution AN and AQ made:
    AA's rows for that sleeve were produced by a session-hour clock defect and judging them would
    be judging the defect.
    """
    import gzip
    aa = AUDIT / "phase6/receipts/AA_ESTATE_TRADES.json.gz"
    v2 = AUDIT / "phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
    if not aa.is_file():
        return {}
    trades = json.loads(gzip.open(aa, "rt").read())["trades"]
    if v2.is_file():
        sub = json.loads(gzip.open(v2, "rt").read())["trades"].get("sub_mid_dn_revert")
        if sub:
            trades["sub_mid_dn_revert"] = sub
    out = {}
    for tag in ARMED_TAGS:
        rows = trades.get(tag) or []
        rs = [r.get("r_gross") for r in rows if r.get("r_gross") is not None]
        if len(rs) < 20:
            out[tag] = {"n": len(rs), "sd": None, "centred_r": None,
                        "reason": "fewer than 20 archive trades; no dispersion estimate"}
            continue
        m = st.mean(rs)
        out[tag] = {"n": len(rs), "sd": st.pstdev(rs), "mean_r_gross": m,
                    "centred_r": [x - m for x in rs],
                    "population": ("AQ_ESTATE_TRADES_V2 (re-clocked)"
                                   if tag == "sub_mid_dn_revert" else "AA_ESTATE_TRADES")}
    return out


def false_trip_probability(centred, true_mean, floor, n_fills, draws=BOOTSTRAP_DRAWS,
                           seed=BOOTSTRAP_SEED):
    """P(cumulative net R touches `floor` within `n_fills` | the sleeve runs at `true_mean`).

    The step distribution is the sleeve's own centred archive R, so the dispersion is measured and
    not assumed normal — these distributions are strongly non-normal (a stop-out mass at -1 R and a
    long right tail), and a normal approximation would understate the left tail exactly where this
    question lives.
    """
    if not centred or floor is None:
        return None
    import random
    rng = random.Random(seed)
    hits = 0
    for _ in range(draws):
        cum = 0.0
        for _ in range(n_fills):
            cum += true_mean + rng.choice(centred)
            if cum <= floor:
                hits += 1
                break
    return round(hits / draws, 4)


def solve_evidence_floor(centred, true_mean, *, start, step=0.5, limit=-80.0):
    """The deepest 0.5 R step whose false-trip rate is at or under the target."""
    if not centred:
        return None, None
    floor = float(start)
    while floor > limit:
        p = false_trip_probability(centred, true_mean, floor, POWER_HORIZON_FILLS, draws=4000)
        if p is not None and p <= FALSE_TRIP_TARGET:
            break
        floor -= step
    return round(floor, 2), false_trip_probability(centred, true_mean, floor, POWER_HORIZON_FILLS)


# ---------------------------------------------------------------------------
# the live exit contract, read out of the running module
# ---------------------------------------------------------------------------
def live_contract() -> dict:
    from src.components.ultimate_book.execution_packets import (
        DEFAULT_EXIT_PROFILE, M15_BARS_PER, SLEEVE_EXIT_PROFILES,
    )
    from src.components.ultimate_book.admission import CLEAN3_REGISTRY, SLEEVE_REGISTRY

    conf = {}
    for reg in (SLEEVE_REGISTRY, CLEAN3_REGISTRY):
        for name, spec in reg.items():
            conf[name] = float(spec.confidence)

    # AQ's own per-sleeve contract audit, so the fidelity answer is READ and not re-derived here.
    fidelity = {}
    if CONTRACT_TRUTH.is_file():
        fidelity = (json.loads(CONTRACT_TRUTH.read_text()).get("spec_audit") or {}).get("sleeves", {})

    out = {}
    for tag in ARMED_TAGS:
        prof = dict(SLEEVE_EXIT_PROFILES.get(tag, DEFAULT_EXIT_PROFILE))
        tsb = prof.get("time_stop_bars")
        fid = fidelity.get(tag) or {}
        grid = "M15" if fid.get("m15_per_own_bar_calendar") == 1 else (
            "H4" if fid.get("m15_per_own_bar_calendar") == M15_BARS_PER["H4"] else None)
        out[tag] = {
            "policy": prof.get("policy"),
            "final_target_r": prof.get("final_target_r"),
            "final_from_intent": bool(prof.get("final_from_intent", False)),
            "time_stop_bars_m15": tsb,
            # `time_stop_bars` counts PRINTED M15 bars, so this is TRADING hours, not calendar
            # hours. On a 5-day symbol 320 trading hours is ~1.9 calendar weeks. Conflating the two
            # is the unit trap AQ measured at B1400; the field name says which one this is.
            "time_stop_trading_hours": (tsb * 0.25) if tsb is not None else None,
            "decision_grid": grid,
            "time_stop_own_bars": fid.get("live_time_stop_own_bars_exact"),
            "research_maxbars_own_bars": 80,
            "time_stop_as_frac_of_research_horizon":
                (fid.get("live_time_stop_own_bars_exact") / 80.0
                 if fid.get("live_time_stop_own_bars_exact") is not None else None),
            "contract_fidelity_class": fid.get("classification"),
            "frac_trades_the_time_stop_would_truncate":
                fid.get("frac_trades_the_time_stop_would_truncate"),
            "binds_before_maxbars": fid.get("binds_before_maxbars"),
            "registry_confidence": conf.get(tag),
            "provenance": "src/components/ultimate_book/execution_packets.py::SLEEVE_EXIT_PROFILES "
                          "+ admission.py::SLEEVE_REGISTRY/CLEAN3_REGISTRY, read at generation; "
                          "fidelity class from phase11/receipts/AQ_CONTRACT_TRUTH_V1.json"
                          "::spec_audit.sleeves",
        }
    return out


# ---------------------------------------------------------------------------
# the archive walk + AD's measured carry
# ---------------------------------------------------------------------------
def carry_basis() -> dict:
    d = json.loads(CARRY_TIERS.read_text())
    rows, nights = d["rows"], d["measured_nights_by_sleeve"]
    out = {}
    for acct in ACCOUNTS:
        for tag in ARMED_TAGS:
            row = rows.get(f"{acct}::{tag}")
            if row is None:
                out[f"{acct}::{tag}"] = {"present": False}
                continue
            fixed = row.get("inputs_held_fixed") or {}
            nm = (nights.get(tag) or {}).get("by_account", {}).get(acct) or {}
            out[f"{acct}::{tag}"] = {
                "present": True,
                "published_tier": row.get("published_tier"),
                "restated_tier": row.get("restated_tier"),
                "tier_moved": row.get("tier_moved"),
                "archive_gross_r_per_trade": fixed.get("gross_r"),
                "true_cost_ex_swap_r": fixed.get("true_cost_ex_swap_r"),
                "swap_r_per_night": fixed.get("swap_r_per_night"),
                "break_even_nights": fixed.get("break_even_nights"),
                "measured_nights_mean": nm.get("mean"),
                "measured_nights_p90": nm.get("p90"),
                "measured_nights_max": nm.get("max"),
                "measured_frac_zero_nights": nm.get("frac_zero"),
                "median_hold_hours": (nights.get(tag) or {}).get("median_hold_hours"),
                "p90_hold_hours": (nights.get(tag) or {}).get("p90_hold_hours"),
                "max_hold_hours": (nights.get(tag) or {}).get("max_hold_hours"),
                "n_archive_trades": (nights.get(tag) or {}).get("n_trades"),
                "provenance": "phase7/receipts/AD_CARRY_TIERS_RESTATED_V1.json",
                "PROVENANCE_WARNING": "this block mixes TWO archives, and AD's artifact does so at "
                                      "source: `archive_gross_r_per_trade` comes from the W7 "
                                      "recost cache (SURVIVOR_BOOK_V1.json) while `n_archive_"
                                      "trades` and the hold/nights come from the AA estate walk. "
                                      "For fx_jpy the AA walk's own gross is 0.067174 against the "
                                      "W7 cache's 0.28235 — a 4.2x difference on the SAME sleeve. "
                                      "Every expectancy and floor here uses the W7 figure, which "
                                      "is the more FAVOURABLE of the two; the conservative reading "
                                      "makes fx_jpy's expectancy smaller still and the asymmetry "
                                      "worse. Found by an adversarial pass.",
            }
    return out


# ---------------------------------------------------------------------------
# the live-fill prior, per (sleeve, account)
# ---------------------------------------------------------------------------
def live_prior() -> dict:
    if not LIVE_ROWS.is_file():
        return {"available": False, "reason": f"absent: {LIVE_ROWS}"}
    rows = [json.loads(line) for line in LIVE_ROWS.read_text().splitlines() if line.strip()]
    per = {}
    for acct in ACCOUNTS:
        akey = ACCOUNT_KEY[acct]
        for tag in ARMED_TAGS:
            fills = [r for r in rows
                     if r.get("sleeve_id") == tag and r.get("account") == akey]
            key = f"{acct}::{tag}"
            if not fills:
                per[key] = {"n_fills": 0,
                            "note": "no live fill of this sleeve exists on this account in the "
                                    "2026-07-25 export — the ONLY live corpus on this machine"}
                continue
            byday = defaultdict(list)
            for r in fills:
                byday[r.get("day_key_broker_server")].append(r)
            days = sorted(byday)
            g_day = [st.mean([x.get("gross_r") or 0.0 for x in byday[d]]) for d in days]
            n_day = [st.mean([x.get("realized_r") or 0.0 for x in byday[d]]) for d in days]
            g_all = [r.get("gross_r") or 0.0 for r in fills]
            n_all = [r.get("realized_r") or 0.0 for r in fills]
            holds = sorted((r.get("holding_seconds") or 0) / 3600.0 for r in fills)
            reasons = defaultdict(int)
            for r in fills:
                reasons[str(r.get("close_reason"))] += 1
            eras = sorted({str(r.get("stack_era")) for r in fills})
            per[key] = {
                "n_fills": len(fills),
                "n_day_blocks": len(days),
                "span_utc": [min(r["entry_time_utc"] for r in fills),
                             max(r["entry_time_utc"] for r in fills)],
                "stack_eras": eras,
                "sleeve_resolution": sorted({str(r.get("sleeve_resolution")) for r in fills}),
                "gross_r_total": sum(g_all),
                "net_r_total": sum(n_all),
                "gross_r_per_fill_trade_weighted": st.mean(g_all),
                "gross_r_per_fill_day_weighted": st.mean(g_day),
                "net_r_per_fill_trade_weighted": st.mean(n_all),
                "net_r_per_fill_day_weighted": st.mean(n_day),
                "net_r_per_day": sum(n_all) / len(days),
                "cost_r_per_fill": st.mean([abs(r.get("cost_r") or 0.0) for r in fills]),
                "n_swap_nonzero": sum(1 for r in fills if (r.get("swap") or 0) != 0),
                "median_hold_hours": st.median(holds),
                "max_hold_hours": holds[-1],
                "close_reasons": dict(sorted(reasons.items())),
                "n_gross_positive": sum(1 for x in g_all if x > 0),
                "n_days_negative": sum(1 for x in g_day if x < 0),
                "provenance": "phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl "
                              "(w7_live_forensics.py over the 2026-07-25 read-only VPS export)",
            }
    return {"available": True, "source_sha256": sha256_file(LIVE_ROWS),
            "n_rows_in_corpus": len(rows), "per_sleeve_account": per}


# ---------------------------------------------------------------------------
# the assertion that keeps this file honest about the armed set
# ---------------------------------------------------------------------------
def assert_armed_set_matches_receipt() -> str:
    text = EXPANSION_RECEIPT.read_text()
    joined = ",".join(ARMED_TAGS)
    if joined not in text:
        raise SystemExit(
            f"ARMED_TAGS {joined!r} does not appear in {EXPANSION_RECEIPT.name}. This file must "
            f"never be the source of truth for what is armed — fix ARMED_TAGS or the receipt."
        )
    return sha256_file(EXPANSION_RECEIPT)


# ---------------------------------------------------------------------------
# the stop conditions, DERIVED
# ---------------------------------------------------------------------------
def stop_conditions(basis: dict, dispersion: dict) -> dict:
    """Every threshold names the basis field it comes from and the multiple applied.

    The multiples themselves are the only free choices, and each carries the reason it is the number
    it is. They are deliberately coarse: a tripwire that needs three decimal places to be right is
    a tripwire nobody will trust at 2 a.m.
    """
    contract = basis["live_contract"]
    carry = basis["carry_basis"]
    prior = basis["live_prior"].get("per_sleeve_account", {})

    conds = {}

    # -- S1: TWO floors, because "what am I willing to lose" and "what would tell me something"
    # -- are different questions and one number cannot answer both. -----------------------------
    #
    # A first cut had ONE floor at -max(3.0, 12 x |expectancy|), justified by a power claim that
    # was never computed. It is computed now, and it REFUTED the claim: on three of five armed
    # sleeves that floor fires **35-76 % of the time** on a sleeve running at exactly its own
    # archive expectancy. A tripwire that fires three times in four on a healthy sleeve is a coin
    # flip wearing a threshold's clothes.
    #
    # The cause is structural and is itself the finding: `fx_jpy`'s expectancy is +0.041 R/trade
    # against a per-trade dispersion of 1.61 R. A near-zero-drift walk with that step size passes
    # -3 R almost surely. **There is no threshold on that sleeve that is both tight and sound.**
    # So both numbers are published, each answering its own question, and the risk floor now
    # carries its measured false-alarm rate instead of an uncomputed claim about one.
    s1a, s1b = {}, {}
    for key, row in carry.items():
        if not row.get("present"):
            continue
        gross = row.get("archive_gross_r_per_trade") or 0.0
        cost = row.get("true_cost_ex_swap_r") or 0.0
        swap_n = row.get("swap_r_per_night") or 0.0
        nights = row.get("measured_nights_mean") or 0.0
        net_expect = gross - cost - swap_n * nights
        sleeve = key.split("::")[1]
        shape = (dispersion.get(sleeve) or {}).get("centred_r")
        risk_floor = -max(3.0, 12.0 * abs(net_expect))
        p_risk = false_trip_probability(shape, net_expect, risk_floor, POWER_HORIZON_FILLS)
        ev_floor, p_ev = solve_evidence_floor(shape, net_expect, start=risk_floor)
        s1a[key] = {
            "archive_net_r_per_trade_at_measured_carry": round(net_expect, 5),
            "cumulative_net_r_floor": round(risk_floor, 3),
            "derivation": "-max(3.0, 12 * |archive_gross - cost_ex_swap - swap_per_night * "
                          "measured_nights_mean|). A STATEMENT OF TOLERANCE, not a test.",
            "measured_false_trip_probability_within_60_fills": p_risk,
            "false_trip_note":
                None if (p_risk is None or p_risk <= 0.15) else
                f"this floor fires {p_risk:.0%} of the time on a sleeve running at exactly its own "
                f"archive expectancy. A trip says the owner has paid what he pre-registered; it "
                f"says NOTHING about the sleeve.",
            "fills_to_trip_at_archive_expectancy":
                None if net_expect <= 0 else round(abs(risk_floor) / net_expect, 1),
            "fills_to_trip_at_live_prior":
                (round(abs(risk_floor)
                       / abs(prior.get(key, {}).get("net_r_per_fill_trade_weighted") or 0), 1)
                 if (prior.get(key, {}).get("net_r_per_fill_trade_weighted") or 0) < 0 else None),
        }
        s1b[key] = {
            "evidence_floor_r": ev_floor,
            "measured_false_trip_probability_within_60_fills": p_ev,
            "archive_r_dispersion_sd": (dispersion.get(sleeve) or {}).get("sd"),
            "n_archive_trades": (dispersion.get(sleeve) or {}).get("n"),
            "derivation": f"the deepest 0.5 R step at which P(cumulative net R touches the floor "
                          f"within {POWER_HORIZON_FILLS} fills | true mean = the archive "
                          f"expectancy) <= {FALSE_TRIP_TARGET:.2f}, by bootstrap over the sleeve's "
                          f"OWN centred archive R distribution",
            "ratio_to_risk_floor": (round(ev_floor / risk_floor, 2)
                                    if (ev_floor and risk_floor) else None),
        }
    conds["S1a_risk_floor"] = {
        "what": "cumulative NET R since arming falls below the floor the owner pre-registered",
        "class": "RISK_BOUND_not_inference",
        "action": "remove the sleeve from --tags on that account (orchestrator ceremony)",
        "why_not_inference": "twelve fills cannot establish an edge and this does not claim to. It "
                             "bounds what the owner pays to find out — and where its measured "
                             "false-trip rate is high, the row says so rather than burying it.",
        "per_sleeve_account": s1a,
    }
    conds["S1b_evidence_floor"] = {
        "what": "cumulative NET R falls below the level at which a trip is INFORMATIVE",
        "class": "INFERENCE",
        "action": "a trip here is evidence the sleeve is not running at its archive expectancy. It "
                  "is still not a significance test — read it with the day-blocked p S2 publishes.",
        "method": {
            "bootstrap": "resample the sleeve's OWN centred archive r_gross distribution, add the "
                         "archive net expectancy as drift, walk fills, record first touch",
            "horizon_fills": POWER_HORIZON_FILLS,
            "target_false_trip_rate": FALSE_TRIP_TARGET,
            "draws": BOOTSTRAP_DRAWS, "seed": BOOTSTRAP_SEED,
            "population": "AA_ESTATE_TRADES.json.gz, with sub_mid_dn_revert replaced by AQ-3's "
                          "re-clocked AQ_ESTATE_TRADES_V2.json.gz population",
            "assumption_disclosed": "the dispersion is the sleeve's GROSS r distribution; net "
                                    "dispersion is very slightly tighter, so this floor is "
                                    "marginally conservative (deeper) than a net-based one",
        },
        "per_sleeve_account": s1b,
    }

    # -- S2: gross-negative tripwire ------------------------------------------------------------
    # The C3 shape from `CANARY_OPERATOR_PAGE.md`, with the one repair the live corpus forced:
    # it must fire on BOTH weightings. `fx_jpy`'s 32 historical live fills are -0.2897 R/fill
    # trade-weighted and +0.0563 day-weighted — the losing days carry up to 4 fills and the winning
    # days carry 1. A trade-weighted-only tripwire would have called that sleeve dead on a number
    # its own day structure does not support.
    conds["S2_gross_negative"] = {
        "what": "cumulative GROSS R (before any cost) negative on BOTH the trade-weighted and the "
                "day-weighted mean, over >= 20 fills spanning >= 8 day blocks",
        "class": "RISK_BOUND_not_inference",
        "min_fills": 20,
        "min_day_blocks": 8,
        "requires_both_weightings": True,
        "action": "remove from --tags; a sleeve losing before cost cannot be rescued by a better "
                  "cost model",
        "derivation": "C3 of phase4/CANARY_OPERATOR_PAGE.md, amended by the fx_jpy live corpus: "
                      "on FTMO the same 21 fills read -0.2487 R/fill trade-weighted and -0.1450 "
                      "day-weighted, a 42 % attenuation, because the losing days carry up to 4 "
                      "fills and the winning days carry 1. Both weightings are computed PER "
                      "ACCOUNT: pooling the two accounts into one day block mixes two independent "
                      "books and flips the pooled day-weighted figure positive (+0.0563), which is "
                      "an artifact of the pooling and not a property of either account.",
        "power_disclosure": "every evaluation reports the exact sign-flip p over day blocks against "
                            "BOTH null means (0 and the archive gross) and its resolution floor",
    }

    # -- S3: carry surprise ---------------------------------------------------------------------
    s3 = {}
    for key, row in carry.items():
        if not row.get("present"):
            continue
        p90 = row.get("measured_nights_p90")
        be = row.get("break_even_nights")
        s3[key] = {
            "measured_nights_p90": p90,
            "break_even_nights": be,
            "alert_mean_nights_above": p90,
            "stop_mean_nights_above": be,
            "derivation": "alert at AD's measured p90 nights; stop at break_even_nights — the "
                          "point past which the sleeve's own arithmetic says the carry has eaten "
                          "the edge. NOT min(be, 2 x p90): a first cut used that and it collapses "
                          "to 0.0 for a zero-carry sleeve, which is the degenerate case rather "
                          "than the strict one.",
            "zero_carry_sleeve": (p90 == 0),
            "note": (None if p90 != 0 else
                     "this sleeve's archive p90 is ZERO nights and its break-even is under one "
                     "night, so ANY sustained carry is a stop condition, not a surprise. That is "
                     "the arithmetic, not a tight threshold."),
        }
    conds["S3_carry_surprise"] = {
        "what": "mean swap nights per closed position exceeds the sleeve's measured p90 (alert) or "
                "its break-even (stop)",
        "class": "ECONOMIC",
        "action": "alert: read it. stop: remove from --tags — the tier restatement is void.",
        "per_sleeve_account": s3,
    }

    # -- S4: hold-time surprise -----------------------------------------------------------------
    s4 = {}
    for tag in ARMED_TAGS:
        row = carry.get(f"FTMO::{tag}") or {}
        med = row.get("median_hold_hours")
        c = contract.get(tag) or {}
        own = c.get("time_stop_own_bars")
        trunc = c.get("frac_trades_the_time_stop_would_truncate")
        s4[tag] = {
            "archive_median_hold_hours": med,
            "archive_p90_hold_hours": row.get("p90_hold_hours"),
            "live_time_stop_own_bars": own,
            "research_maxbars_own_bars": 80,
            "alert_median_hold_hours_above": (3.0 * med) if med else None,
            "derivation": "3x the archive median. A hold distribution 3x its own basis means the "
                          "exit contract the economics were measured under is not the one running.",
            # The unit-correct statement compares OWN BARS to `maxbars`, not clock hours to clock
            # hours: `time_stop_bars` counts printed M15 bars and the archive hold is calendar.
            "time_stop_vs_research_horizon":
                (None if own is None else
                 ("EQUALS the research maxbars — it can only bind where the walk already truncated"
                  if own == 80 else
                  f"TIGHTER than the research maxbars ({own:.0f} of 80 own bars); AQ measured the "
                  f"resulting truncation at {trunc:.1%} of walked trades" if own < 80 else
                  f"LOOSER than the research maxbars ({own:.0f} of 80 own bars)")),
            "contract_fidelity_class": c.get("contract_fidelity_class"),
        }
    conds["S4_hold_time_surprise"] = {
        "what": "median hold since arming exceeds 3x the sleeve's archive median",
        "class": "CONTRACT_FIDELITY",
        "action": "alert. The published economics describe a different contract; re-price before "
                  "acting on them.",
        "per_sleeve": s4,
    }

    # -- S5: the stop-out run -------------------------------------------------------------------
    # A run is the one signal available before any R total is meaningful. The threshold is set from
    # the live corpus: `fx_jpy` closed 24 of 32 at the stop, so a 24/32 base rate makes runs of 6
    # unremarkable and runs of 9 a ~3.5 % event under independence.
    conds["S5_stop_out_run"] = {
        "what": "9 consecutive closes at the stop on one sleeve on one account",
        "class": "RISK_BOUND_not_inference",
        "alert_run": 6,
        "stop_run": 9,
        "action": "alert at 6: look. stop at 9: remove from --tags.",
        "derivation": "the live fx_jpy corpus closes 24 of 32 at the stop (0.75); under "
                      "independence a run of 9 is 0.75^9 = 0.075 per starting position and a run "
                      "of 6 is 0.178 — 6 is a look, 9 is an act",
        "caveat": "these fills are day-clustered, so independence understates the run probability. "
                  "The threshold is deliberately loose for that reason.",
    }

    # -- S6: the two conditions that are NOT about a sleeve -------------------------------------
    conds["S6_book_composition"] = {
        "what": "the workers' --tags do not equal the armed five, on either account",
        "class": "CRITICAL",
        "action": "stop and read the launch command before believing anything else on the page",
        "derivation": "book_engine.py:493 intersects --tags with the include-flag registry; "
                      "run_book.py treats --tags '' as falsy and runs ALL BUILT sleeves "
                      "(fail-OPEN). An all-typo --tags stands down silently every tick.",
        "expected_tags": list(ARMED_TAGS),
    }
    conds["S7_unchecked"] = {
        "what": "any condition above could not be evaluated (no fills file, no export, no basis)",
        "class": "UNCHECKED",
        "action": "exit code 3, never 0. 'nothing is wrong' and 'nothing was checked' are "
                  "different, and collapsing them is how .tools/monitor_books.py sat mute through "
                  "the window it was meant to be watching.",
    }
    return conds


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    receipt_sha = assert_armed_set_matches_receipt()
    disp = archive_r_dispersion()

    basis = {
        "schema": "gtos.live.armed_sleeve_basis.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase11/receipts/as_live_basis.py",
        "session": "AS",
        "blocks": "B1500-B1509",
        "armed_tags": list(ARMED_TAGS),
        "armed_utc": ARMED_UTC,
        "armed_set_provenance": {
            "receipt": "phase8/receipts/FIVE_SLEEVE_EXPANSION_20260730.md",
            "sha256": receipt_sha,
            "host_commit": "f855250cd",
            "asserted": "the ARMED_TAGS string appears verbatim in the receipt",
        },
        "live_contract": live_contract(),
        "carry_basis": carry_basis(),
        "live_prior": live_prior(),
        "archive_r_dispersion": {
            k: {kk: vv for kk, vv in v.items() if kk != "centred_r"}
            for k, v in disp.items()
        },
    }

    # the inferential statements about the live prior, computed here so the page never invents one
    prior = basis["live_prior"].get("per_sleeve_account", {})
    rows = [json.loads(l) for l in LIVE_ROWS.read_text().splitlines() if l.strip()] \
        if LIVE_ROWS.is_file() else []
    tests = {}
    for key, blk in prior.items():
        if not blk.get("n_fills"):
            continue
        acct, tag = key.split("::")
        fills = [r for r in rows if r.get("sleeve_id") == tag
                 and r.get("account") == ACCOUNT_KEY[acct]]
        byday = defaultdict(list)
        for r in fills:
            byday[r.get("day_key_broker_server")].append(r.get("gross_r") or 0.0)
        dmeans = [st.mean(byday[d]) for d in sorted(byday)]
        arch = (basis["carry_basis"].get(key) or {}).get("archive_gross_r_per_trade")
        tests[key] = {
            "vs_zero": signflip_p(dmeans, 0.0),
            "vs_archive_gross": signflip_p(dmeans, arch) if arch is not None else None,
            "day_means_gross_r": [round(x, 6) for x in dmeans],
        }
    basis["live_prior_significance"] = {
        "note": "the honest reading of the live prior. A trade-weighted total is what the account "
                "lost; a day-blocked permutation is what it establishes. Both are reported and "
                "they disagree in sign for fx_jpy.",
        "per_sleeve_account": tests,
    }

    # every armed sleeve must appear in the basis or the artifact refuses to publish
    missing = [t for t in ARMED_TAGS if t not in basis["live_contract"]]
    if missing:
        raise SystemExit(f"armed sleeves absent from the live contract read: {missing}")

    basis_path = args.out_dir / "AS_LIVE_SLEEVE_BASIS_V1.json"
    basis_path.write_text(json.dumps(basis, indent=1, sort_keys=False) + "\n")

    conds = {
        "schema": "gtos.live.stop_conditions.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase11/receipts/as_live_basis.py",
        "session": "AS",
        "blocks": "B1510-B1519",
        "pre_registered_utc": "2026-07-30",
        "window": "POST-ARMING ONLY. The pre-arming live prior is reported alongside and NEVER "
                  "merged into a stop-condition evaluation — it is evidence the owner already had "
                  "when he accepted the risk.",
        "armed_tags": list(ARMED_TAGS),
        "basis_artifact": "phase11/receipts/AS_LIVE_SLEEVE_BASIS_V1.json",
        "basis_sha256": hashlib.sha256(basis_path.read_bytes()).hexdigest(),
        "de_arm_mechanism": {
            "how": "remove the sleeve from `--tags` in scripts/run_book_supervisor.ps1 on the host "
                   "and restart the supervisor (the orchestrator's ceremony)",
            "what_it_stops": "NEW generation only — book_engine.py:493 applies tags",
            "what_it_does_NOT_stop": "exit management of an already-open position. "
                                     "`_manageable_pairs` (book_owner.py:2694) calls "
                                     "active_specs(None, ...) with tags NOT applied, and its "
                                     "consumers are manage_open_positions (:1985) and "
                                     "_alert_out_of_universe (:2093) — so a de-tagged sleeve's "
                                     "open position stays adopted and exit-managed. This is the "
                                     "SAFE direction and is why de-arming does not need a flatten.",
            "citation_corrected": "a first cut also cited book_owner.py:503 (`_manageable_symbols`). "
                                  "That function has ZERO callers repo-wide — `b5d1b20d3` replaced "
                                  "its call with `_manageable_pairs` — so it is dead code and "
                                  "carries none of the claim. Found by an adversarial pass; the "
                                  "conclusion is unchanged because :2694 alone establishes it.",
            "the_orphan_this_does_NOT_cover": "de-arming via the INCLUDE FLAGS rather than --tags "
                                              "(ultimate_book_include_candidate_book / "
                                              "_include_market_expansion_book / the "
                                              "market-expansion allowlist) DOES drop a sleeve from "
                                              "_manageable_pairs (:2696-2699), so its open "
                                              "position would be orphaned. --tags is the safe "
                                              "mechanism; an include-flag flip is not.",
            "same_day_size_consequence":
                "narrowing --tags mid-day does NOT reduce that day's Kelly-lite conviction count: "
                "RunningConvictionLedger.update_and_count unions the day's firing sleeves and "
                "admission.py:1210 takes na = max(na, override). The other four sleeves keep the "
                "5-sleeve multiplier until the decision day rolls. De-arm at a day boundary if the "
                "size step matters.",
            "same_day_size_consequence_is_gated_on":
                "the running-count override exists only when BOTH ultimate_book_kelly_running_count "
                "AND ultimate_book_kelly_lite are true (book_engine.py:892 returns None otherwise). "
                "Both are true on the live hosts (agent_config.yaml:1303, :1305), so the claim "
                "holds today — but it is a property of that config, not of the code.",
            "never": "do NOT reach for live_broker_authority: false — H8. At HEAD the flatten "
                     "suppression is book_owner.py:2382 (the marker row; the return follows) and "
                     "the observe-only degradation is :2544. Flatten first, confirm flat, THEN "
                     "shut a gate. (CLAUDE.md's :2364-2373 / :2526 are one commit stale; the "
                     "behaviour is unchanged.)",
        },
        "conditions": stop_conditions(basis, disp),
    }
    (args.out_dir / "FIVE_SLEEVE_STOP_CONDITIONS_V1.json").write_text(
        json.dumps(conds, indent=1, sort_keys=False) + "\n")

    print(f"wrote {basis_path.relative_to(ROOT)}")
    print(f"wrote {(args.out_dir / 'FIVE_SLEEVE_STOP_CONDITIONS_V1.json').relative_to(ROOT)}")
    for key, blk in sorted(prior.items()):
        if blk.get("n_fills"):
            t = tests[key]
            print(f"  live prior {key}: n={blk['n_fills']} "
                  f"gross/fill trade-wt {blk['gross_r_per_fill_trade_weighted']:+.4f} "
                  f"day-wt {blk['gross_r_per_fill_day_weighted']:+.4f} "
                  f"| p vs 0 = {t['vs_zero']['p']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
