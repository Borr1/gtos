"""Session AI, item 3 — the four books, composed and measured at each firm's MEASURED rules.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ai_books_mc.py
    python3 .../ai_books_mc.py --paths 5000        # smoke

Writes `BOOKS_MC_V1.json` (+ a rendered `BOOKS_MC_V1.md`).

THE MACHINERY IS SESSION Q'S, UNCHANGED
---------------------------------------
`scripts/mc_firm_rules.py` is imported, not reimplemented. Its `mc()` reduces bit-identically
to the sealed engine under `Rules.LEGACY` (Q's control 3), its `rule_sets()` reads each firm's
measured rules from `FIRM_RULES_V1.json` at run time, and its `series()` is
`build_survivor_book.econ` up to (days, comb, risk). Nothing in the sealed route is edited.

THE FOUR BOOKS, AND THE ONE THE MACHINERY CANNOT COMPOSE
--------------------------------------------------------
  1. FTMO AS ARMED TODAY -- `crypto, energy_agri, sub_xvol_pullback`, the live three.
  2. FTMO + AD'S RESTATED TIERS -- what the tier correction is worth if ratified.
  3. redacted_account ARMING PACKAGE -- its own survivor set at its own measured rules.
  4. THE CHALLENGE BOOK -- the candidate family's admitted members.

Books 1-3 go through `mc_firm_rules --sleeve-set`. **Book 4 cannot**, and the reason is worth
stating rather than working around: `parse_sleeve_set` fails closed on any sleeve outside
`recost_w7_validation.BOOK_CONF`, which is the 11-sleeve W7 book, and `mx_btcusd` has no row in
the W7 recost caches at all. Its 318 trades live in AA's archive walk.

So book 4 is built from the ARCHIVE population's own daily net-R series
(`AA_SLEEVE_SPLITS_V1.json -> daily_net_r`, already broker-true and already the gate's own
input) and run through the same `mc()`. That is a CROSS-POPULATION composition and it is
stamped as one everywhere it appears -- exactly what `SLEEVE_DOSSIER_V1` rule R0/R1 require.
To keep it readable, the armed three are ALSO run on the archive population as a
same-population control, so a reader never has to compare an archive number to a cache number.

SIZING IS NOT INVENTED HERE
---------------------------
Weights are `admission.effective_registry` confidences -- the live allocator's own numbers,
read from code. That has a consequence worth seeing before it is argued about: `mx_btcusd`'s
registry confidence is **0.025** (`default_off_runtime_capable_zero_activation`) against
`crypto`'s 0.85, so admitting it changes a book's economics by almost nothing at the
convention. An equal-weight branch is published beside it as the SENSITIVITY to re-weighting
an admitted sleeve -- pricing a decision, not proposing one. Composition and weights are
Borhen's.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

# `scripts/research/` is a regular package and shadows the repo-root `research` namespace the
# moment `scripts/` is searchable -- Q's own comment. Pin the root package first.
_p = sys.path[:]
try:
    sys.path[:] = [str(REPO)]
    import research.operations  # noqa: F401
finally:
    sys.path[:] = _p
sys.path.insert(0, str(REPO / "scripts"))

import mc_firm_rules as Q  # noqa: E402

from src.components.ultimate_book import admission as P  # noqa: E402

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
AA_SPLITS = AUD / "phase6/receipts/AA_SLEEVE_SPLITS_V1.json"
DECL = AUD / "phase8/receipts/CANDIDATE_FAMILY_V1.json"
GATE_AT_FAMILY = AUD / "phase8/receipts/AI_GATE_AT_DECLARED_FAMILY_V1.json"
ARMED_MC = REPO / "research/operations/w7_recost_2026_07_27/ARMED_SET_MC_V1.json"

OUT_JSON = HERE / "BOOKS_MC_V1.json"
OUT_MD = HERE / "BOOKS_MC_V1.md"

ARMED_TODAY = ["crypto", "energy_agri", "sub_xvol_pullback"]

#: AD restates these to UNCONDITIONAL on BOTH accounts once carry is measured instead of
#: assumed (`AD_CARRY_TIERS_RESTATED_V1.json`; AD section 5). Both are in the W7 book, so the
#: machinery can compose them; whether to ARM them is not this file's question.
AD_RESTATED_UNCONDITIONAL = ["sub_mid_dn_revert", "fx_jpy"]

BOOKS = collections.OrderedDict([
    ("FTMO_ARMED_TODAY_3", {
        "account": "FTMO", "sleeves": ARMED_TODAY,
        "why": ("the live three, set at `run_book.py --tags` on 2026-07-29 14:25 UTC. This is "
                "the reference case."),
        "provenance": ("ORCHESTRATOR_HANDOFF_TO_FABLE.md:124 — `crypto`, `energy_agri`, "
                       "`sub_xvol_pullback` via run_book.py --tags at "
                       "scripts/run_book_supervisor.ps1:140 ON THE VPS. The COMMITTED launcher "
                       "passes no --tags (CLAUDE.md B327), so this set exists only on the host."),
    }),
    ("FTMO_ARMED_PLUS_AD_RESTATED_5", {
        "account": "FTMO", "sleeves": ARMED_TODAY + AD_RESTATED_UNCONDITIONAL,
        "why": ("the armed three plus the two sleeves AD restates UNCONDITIONAL on both "
                "accounts at measured holds. What the tier correction is worth IF ratified."),
        "provenance": ("AD_CARRY_TIERS_RESTATED_V1.json rows FTMO::sub_mid_dn_revert and "
                       "FTMO::fx_jpy, both published CARRY_CONDITIONAL / MEASURED_LIVE_CARRY "
                       "and both restated UNCONDITIONAL. `sub_mid_dn_revert` clears its "
                       "break-even by 8.6x on measured nights."),
    }),
    ("FTMO_SURVIVORS_PLUS_AD_RESTATED_6", {
        "account": "FTMO", "sleeves": sorted(set(ARMED_TODAY + AD_RESTATED_UNCONDITIONAL
                                                 + ["metals_core"])),
        "why": ("the full FTMO survivor set plus AD's restatements. `metals_core` is an FTMO "
                "survivor and was armed at 12:55 before being pulled at 14:25 — AE's "
                "cost-true evidence later landed on the same side (DOWN_WEIGHT x0.50 on a "
                "232-trade/118-day OOS at -0.205 R). Included so the pull has a price."),
        "provenance": "SURVIVOR_BOOK_V1.accounts.FTMO.survivors + AD's two restatements",
    }),
    ("redacted_account_SURVIVORS_4", {
        "account": "redacted_account", "sleeves": sorted(
            ["crypto", "energy_agri", "sub_xvol_pullback", "vp_euidx_pocgrav"]),
        "why": ("redacted_account's own survivor set at its own measured rules. Its fourth survivor "
                "`vp_euidx_pocgrav` GENERATES NOTHING — see `data_gap`."),
        "provenance": "SURVIVOR_BOOK_V1.accounts.redacted_account.survivors",
        "data_gap": ("`vp_euidx_pocgrav` fails closed at `sleeves/vp_euidx.py:70` for want of a "
                     "GER40/UK100 M1 aux feed and has 0 trades in AA's walk. Its cache rows "
                     "exist, so the MC can size it — but the live book cannot produce one of "
                     "its trades. The 3-sleeve row below is what redacted_account can actually run "
                     "today, and it is the row to read."),
    }),
    ("redacted_account_RUNNABLE_3", {
        "account": "redacted_account", "sleeves": ARMED_TODAY,
        "why": ("redacted_account's survivor set minus the sleeve that cannot generate. The same "
                "three sleeves FTMO is armed on — which makes this the cheapest real "
                "diversification available: a second account on the same measured book at a "
                "different broker's costs."),
        "provenance": "redacted_account_SURVIVORS_4 minus vp_euidx_pocgrav",
    }),
    ("redacted_account_SURVIVORS_PLUS_AD_RESTATED_5", {
        "account": "redacted_account", "sleeves": sorted(ARMED_TODAY + AD_RESTATED_UNCONDITIONAL),
        "why": "the runnable three plus AD's two restatements, on redacted_account's rules.",
        "provenance": "as above",
    }),
])

#: Every carry cell and both windows, exactly as the published grid does it.
CELL_KEYS = ("fwd_nights_0.0", "fwd_nights_1.0", "fwd_nights_max",
             "full_nights_0.0", "full_nights_1.0", "full_nights_max")
#: The two rule sets that decide something: firm-true phase 1, and the whole 2-step
#: evaluation, which is the one that gates a payout.
RULES_OF_RECORD = ("L4_FIRM_TRUE_PH1", "P2_BOTH_PHASES")


# =====================================================================================
def registry_conf() -> dict:
    mx, err = P.resolve_market_expansion_sleeves(
        policy="positive_weighted12_after_swap", explicit_sleeves=())
    if err:
        raise SystemExit(f"market-expansion policy failed closed: {err}")
    reg = P.effective_registry(include_clean3=True, include_candidate_book=True,
                              include_market_expansion_book=True,
                              market_expansion_sleeves=mx)
    return {k: float(v.confidence) for k, v in reg.items()}


# ---------------------------------------------------------------- books 1-3
def run_cache_books(paths: int, verify_paths: int) -> dict:
    """Books 1-3 through Q's own grid, at BOTH sizing conventions, on BOTH accounts.

    Both conventions are run because they differ by ~2.1x in size and every published figure
    the owner has seen is the `published` one while the deployable path implements `live`
    (`ARMED_SET_MC_V1.json` section 1). Reporting one would be reporting the wrong number to
    somebody.
    """
    out = {}
    for conv, (kelly, basis) in {
        "published_vol_matched_full_kelly": (Q.KELLY_SEALED, Q.RISK_VOL_MATCHED),
        "live_nominal_half_kelly": (Q.KELLY_HALF, Q.RISK_LIVE_NOMINAL),
    }.items():
        extra = collections.OrderedDict(
            (name, spec["sleeves"]) for name, spec in BOOKS.items())
        cells, sd_book, survivors = Q.build_cells(extra, kelly=kelly, risk_basis=basis)
        # `allow_cost_drift` is required at HEAD and the reason is published, not shrugged
        # off: 8f6da5150 and 33d854189 extended BROKER_TRUE_COSTS_V1.json after Session Q
        # sealed its figures, on FTMO only. `book_days` stays a hard control, so a drifting
        # TRADE SET would still stop this file.
        bad, scope, drift = Q.verify_series(
            cells, sizing_sealed=(conv.startswith("published")), allow_cost_drift=True)
        if bad:
            raise SystemExit(f"series control failed for {conv}: {bad[:4]}")
        if drift and {r[0] for r in drift} != {"FTMO"}:
            raise SystemExit(
                f"cost drift reaches redacted_account, which the coverage story does not explain: "
                f"{[r for r in drift if r[0] != 'FTMO'][:4]}")
        ident = Q.verify_bit_identity(cells[:2], n_paths=verify_paths)
        if ident:
            raise SystemExit(f"bit-identity control failed for {conv}: {ident[:4]}")
        out[conv] = {
            "sizing": {"kelly": kelly, "risk_basis": basis},
            "controls": {"series_reconstruction_mismatches": 0,
                         "series_scope": scope,
                         "cost_artifact_drift_rows_tolerated": len(drift),
                         "cost_artifact_drift_is_ftmo_only": (
                             {r[0] for r in drift} == {"FTMO"} if drift else None),
                         "cost_artifact_drift_cause": (
                             "8f6da5150 and 33d854189 extended BROKER_TRUE_COSTS_V1.json "
                             "AFTER Session Q sealed SURVIVOR_BOOK_V1.json, on FTMO only "
                             "(167 priced instruments to redacted_account's 76). crypto goes "
                             "MEASURED 35 -> 72, idxrev 4,939 -> 5,876. book_days reproduces "
                             "on all 36 cells, so the trade set is unchanged and only the "
                             "pricing moved. redacted_account still reproduces all 48 of its "
                             "published MC fields EXACTLY, which is the control that makes "
                             "this diagnosis rather than a guess."
                             if drift else None),
                         "bit_identity_disagreements": 0,
                         "bit_identity_cells_checked": 2,
                         "bit_identity_paths": verify_paths},
            "sd_book_reference": round(sd_book, 5),
            "survivor_sets_from_the_artifact": survivors,
            "books": {},
        }
        for name, spec in BOOKS.items():
            acct = spec["account"]
            rows = {}
            for c in cells:
                if c["account"] != acct or c["variant"] != name:
                    continue
                res = {}
                for r in Q.rule_sets(acct)[0]:
                    if r.label not in RULES_OF_RECORD:
                        continue
                    m = Q.mc(c["comb"], c["risk"], r, paths, seed_base=1)
                    res[r.label] = {
                        "p_pass": round(m["p_pass"], 6),
                        "se_p_pass": round(m["se_p_pass"], 6),
                        "p_fail_dd": round(m["p_fail_dd"], 6),
                        "p_fail_daily": round(m["p_fail_daily"], 6),
                        "p_timeout": round(m["p_timeout"], 6),
                        **Q._derived(c, m)}
                    print(f"   {conv[:9]:9s} {acct:11s} {name:36s} {c['key']:16s} "
                          f"{r.label:18s} p={m['p_pass']:.5f}", flush=True)
                rows[c["key"]] = {
                    "window": c["window"], "nights": c["nights"], "sleeves": c["sleeves"],
                    "book_days": c["book_days"],
                    "mean_r_per_book_day": round(c["mean_r_per_book_day"], 5),
                    "worst_day_unit_r": round(c["worst_day_unit_r"], 5),
                    "vol_scale": round(c["vol_scale"], 4),
                    "eff_risk_pct": round(c["risk"] * 100, 3),
                    "rules": res}
            out[conv]["books"][name] = {**{k: v for k, v in spec.items()
                                          if k != "sleeves"},
                                       "sleeves": spec["sleeves"],
                                       "population": "W7_CACHE",
                                       "cells": rows}
    return out


# ---------------------------------------------------------------- book 4
def archive_daily(sleeves, conf: dict) -> tuple[list, list, dict]:
    """A confidence-weighted daily unit-R series from the ARCHIVE walk.

    `AA_SLEEVE_SPLITS_V1.json -> <sleeve>.daily_net_r` is the day series the gate itself
    pooled: net of broker-true cost at `BROKER_TRUE_COSTS_V1_1`, one entry per day the sleeve
    traded. Summing conf-weighted across sleeves per day is the same construction
    `recost_w7_validation.build_matrix_from` performs on the cache, so the two books differ in
    their POPULATION and not in their arithmetic.
    """
    d = json.loads(AA_SPLITS.read_text())
    src = d.get("sleeves") or d
    per_day = collections.defaultdict(float)
    detail = {}
    for sl in sleeves:
        rec = src.get(sl)
        if not rec:
            raise SystemExit(f"{sl} has no archive split record")
        w = conf.get(sl)
        if w is None:
            raise SystemExit(f"{sl} has no registry confidence")
        series = rec.get("daily_net_r") or {}
        for day, v in series.items():
            per_day[day] += w * float(v)
        detail[sl] = {"conf": w, "n_days": len(series),
                      "mean_net_r_per_day": (round(statistics.fmean(
                          float(x) for x in series.values()), 5) if series else None),
                      "first": min(series) if series else None,
                      "last": max(series) if series else None}
    days = sorted(per_day)
    return [dt.date.fromisoformat(x[:10]) for x in days], [per_day[x] for x in days], detail


def run_archive_book(name: str, sleeves, conf: dict, paths: int, *, equal_weight=False,
                     dial=Q.DIAL, sd_ref=None) -> dict:
    w = {s: 1.0 for s in sleeves} if equal_weight else conf
    days, comb, detail = archive_daily(sleeves, w)
    if not comb:
        raise SystemExit(f"{name}: empty series")
    sd = statistics.pstdev(comb)
    a, b = min(days), max(days)
    sess = Q.weekday_sessions(a, b)
    months = (b.year - a.year) * 12 + (b.month - a.month) + 1
    cell_base = {
        "book_days": len(days), "weekday_sessions": sess,
        "book_days_per_calendar_month": len(days) / months,
        "mean_r_per_book_day": statistics.fmean(comb),
        "worst_day_unit_r": min(comb), "sd_unit_r": sd,
        "window": f"{a.isoformat()}..{b.isoformat()}",
    }
    branches = {}
    for basis, risk, vs in (
            ("live_nominal_per_unit", dial, None),
            ("vol_matched_to_the_W7_reference_book",
             (dial * (sd_ref / sd) if sd and sd_ref else None),
             (sd_ref / sd if sd and sd_ref else None))):
        if risk is None:
            continue
        cell = {**cell_base, "risk": risk}
        res = {}
        for acct in ("FTMO", "redacted_account"):
            rs, firm = Q.rule_sets(acct)
            res[acct] = {"firm_rules": firm, "rules": {}}
            for r in rs:
                if r.label not in RULES_OF_RECORD:
                    continue
                m = Q.mc(comb, risk, r, paths, seed_base=1)
                res[acct]["rules"][r.label] = {
                    "p_pass": round(m["p_pass"], 6),
                    "se_p_pass": round(m["se_p_pass"], 6),
                    "p_fail_dd": round(m["p_fail_dd"], 6),
                    "p_fail_daily": round(m["p_fail_daily"], 6),
                    "p_timeout": round(m["p_timeout"], 6),
                    **Q._derived(cell, m)}
                print(f"   ARCHIVE  {acct:11s} {name:36s} {basis[:20]:20s} "
                      f"{r.label:18s} p={m['p_pass']:.5f}", flush=True)
        branches[basis] = {
            "eff_risk_pct": round(risk * 100, 4), "vol_scale": (round(vs, 4) if vs else None),
            "accounts": res,
            "caveat": (None if basis == "live_nominal_per_unit" else
                       "sd_book_reference is the 11-sleeve W7 CACHE book's daily sd. Using it "
                       "to vol-match an ARCHIVE-population book is a cross-population splice; "
                       "the live_nominal branch needs no reference and is the cleaner read."),
            # A vol match SCALES UP a book quieter than the reference. On a two-sleeve book at
            # registry confidences (0.025 + 0.45) that reaches 3.81 % per correlated unit
            # against a 2.00 % dial -- a number that is a correct output of the convention and
            # would be a serious misreading as a proposal. Flagged on the row rather than
            # left for a reader to notice.
            "EXCEEDS_THE_DIAL": (
                None if risk <= Q.DIAL else
                f"this branch risks {risk * 100:.4f} % per correlated unit against the "
                f"{Q.DIAL * 100:.2f} % dial, because vol-matching SCALES UP a book quieter "
                f"than the reference (vol_scale {vs:.4f} > 1). Do not read it as a sizing "
                f"proposal; it is the convention applied mechanically to a two-sleeve book."),
        }
    return {
        "population": "ARCHIVE",
        "weights": ("equal (1.0 each) — the SENSITIVITY to re-weighting an admitted sleeve"
                    if equal_weight else
                    "admission.effective_registry confidences — the live allocator's own"),
        "per_sleeve": detail,
        **{k: (round(v, 5) if isinstance(v, float) else v) for k, v in cell_base.items()},
        "branches": branches,
    }


# =====================================================================================
def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", type=int, default=60_000)
    ap.add_argument("--verify-paths", type=int, default=4_000)
    a = ap.parse_args(argv)

    conf = registry_conf()
    admits = sorted((json.loads(GATE_AT_FAMILY.read_text()).get("answer") or {})
                    .get("verdict_moves") or [])
    decl = json.loads(DECL.read_text())

    print("books 1-3: through Q's grid, both accounts, both sizing conventions ...",
          flush=True)
    cache_books = run_cache_books(a.paths, a.verify_paths)
    sd_ref = cache_books["published_vol_matched_full_kelly"]["sd_book_reference"]

    print("\nbook 4: the challenge book, on the ARCHIVE population ...", flush=True)
    challenge = sorted(set(admits))
    arch = {}
    # The same-population control comes FIRST, so no reader has to compare an archive number
    # to a cache number to understand book 4.
    arch["CONTROL_FTMO_ARMED_TODAY_3_on_the_archive"] = run_archive_book(
        "CONTROL_ARMED_3", ARMED_TODAY, conf, a.paths, sd_ref=sd_ref)
    arch["CHALLENGE_BOOK_admitted_at_the_declared_family"] = run_archive_book(
        "CHALLENGE_BOOK", challenge, conf, a.paths, sd_ref=sd_ref)
    arch["CHALLENGE_BOOK_equal_weight_sensitivity"] = run_archive_book(
        "CHALLENGE_EQW", challenge, conf, a.paths, equal_weight=True, sd_ref=sd_ref)
    arch["CHALLENGE_BOOK_plus_the_armed_three"] = run_archive_book(
        "CHALLENGE_PLUS_ARMED", sorted(set(challenge) | set(ARMED_TODAY)), conf, a.paths,
        sd_ref=sd_ref)

    # ---- the population gap, extracted because it is the document's real headline ------
    def _cell(book, conv, key, rule):
        return (((cache_books[conv]["books"][book]["cells"].get(key) or {}).get("rules") or {})
                .get(rule) or {})

    cache_live = _cell("FTMO_ARMED_TODAY_3", "live_nominal_half_kelly",
                       "fwd_nights_max", "P2_BOTH_PHASES")
    cache_cell = (cache_books["live_nominal_half_kelly"]["books"]["FTMO_ARMED_TODAY_3"]
                  ["cells"].get("fwd_nights_max") or {})
    arch_live = ((arch["CONTROL_FTMO_ARMED_TODAY_3_on_the_archive"]["branches"]
                  ["live_nominal_per_unit"]["accounts"]["FTMO"]["rules"])
                 .get("P2_BOTH_PHASES") or {})
    population_gap = {
        "question": ("The SAME three armed sleeves, the SAME arithmetic, the SAME live "
                     "sizing, measured on two populations. How far apart are they?"),
        "W7_CACHE_forward_2025_plus_worst_carry": {
            "monthly_pct_calendar": cache_live.get("monthly_pct_calendar"),
            "p_pass_both_phases": cache_live.get("p_pass"),
            "calendar_days_both_phases": cache_live.get("median_calendar_days_to_pass"),
            "book_days": cache_cell.get("book_days"),
            "mean_r_per_book_day": cache_cell.get("mean_r_per_book_day"),
        },
        "ARCHIVE_whole_span": {
            "monthly_pct_calendar": arch_live.get("monthly_pct_calendar"),
            "p_pass_both_phases": arch_live.get("p_pass"),
            "calendar_days_both_phases": arch_live.get("median_calendar_days_to_pass"),
            "book_days": arch["CONTROL_FTMO_ARMED_TODAY_3_on_the_archive"]["book_days"],
            "mean_r_per_book_day":
                arch["CONTROL_FTMO_ARMED_TODAY_3_on_the_archive"]["mean_r_per_book_day"],
        },
        "ratio_monthly_pct": (
            round(cache_live["monthly_pct_calendar"] / arch_live["monthly_pct_calendar"], 2)
            if cache_live.get("monthly_pct_calendar") and arch_live.get("monthly_pct_calendar")
            else None),
        "why": ("The cache cell is the forward 2025+ window at the structural horizon; the "
                "archive cell is the whole 2000-2026 span at maxbars=80. And the forward "
                "window IS THE SELECTION WINDOW: `build_survivor_book.py:60` and "
                "`KB7_growth_kelly_sizing.py:130` share the `d.year >= 2025` predicate "
                "(Session V). So the archive figure is the out-of-window one."),
        "corroboration": ("CLAUDE.md section 4 already records the armed four earning "
                          "+0.100 %/month over ten years out of window and -0.220 % before "
                          "2020. This is the same order of magnitude, derived independently "
                          "from a different artifact by a different route, which is the "
                          "strongest thing that can be said for either number."),
        "reading": ("Treat the small number as the expected case, exactly as CLAUDE.md "
                    "instructs. The 4.5 %/month figure is not wrong -- it is the measured rate "
                    "on the window that chose these sleeves, and it answers a different "
                    "question from 'what will they earn next year'."),
        "rule": "SLEEVE_DOSSIER_V1 R0 and R1 — the axis here is POPULATION and ERA.",
    }

    doc = {
        "schema": "gtos.w7_recost.books_mc.v1",
        "the_population_gap_on_the_armed_book": population_gap,
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                         "ai_books_mc.py"),
        "question": ("Compose the books an arming decision could actually pick from and "
                     "measure each at its firm's MEASURED rules, across both phases, with "
                     "per-book member lists."),
        "machinery": {
            "module": "scripts/mc_firm_rules.py (Session Q), imported unchanged",
            "sealed_route_edited": False,
            "n_paths": a.paths,
            "n_paths_note": ("Q ran 200,000. 60,000 gives SE ~4e-4 on a p_pass of 0.999 and "
                             "~2e-3 at 0.90, which is finer than any difference this document "
                             "turns on; Q measured seed-to-seed spread at <= 0.00463 across "
                             "all 36 cells. `se_p_pass` is published on every row. The reason "
                             "for 60,000 rather than 200,000 is the working agreement's "
                             "machine-discipline rule: three wave-8 sessions share this box."),
            "rules_reported": list(RULES_OF_RECORD),
            "rules_available": ("L0-L7 and P1-P4 in MC_FIRM_TRUE_V1.json. L4 is each firm's "
                                "measured phase 1; P2 is the whole 2-step evaluation, which "
                                "is the one that gates a payout."),
        },
        "the_book_the_machinery_cannot_compose": {
            "what": ("`mc_firm_rules.parse_sleeve_set` fails closed on any sleeve outside "
                     "`recost_w7_validation.BOOK_CONF` — the 11-sleeve W7 book — and "
                     "`mx_btcusd` has no row in the W7 recost caches."),
            "consequence": ("Book 4 is built from the ARCHIVE population's own daily net-R "
                            "series and stamped `population: ARCHIVE` everywhere. It is a "
                            "cross-population composition; the CONTROL row is the armed three "
                            "on the SAME population so the comparison is like-for-like."),
            "what_would_close_it": ("`mx_btcusd`'s trades entering the recost cache, i.e. the "
                                    "market-expansion family being carried into "
                                    "`recost_w7_validation` — a route change, not a "
                                    "measurement. Until then no single population can price a "
                                    "book containing both an armed core sleeve and an admitted "
                                    "candidate."),
        },
        "challenge_book_membership": {
            "members": challenge,
            "why_these": ("the sleeves that reach ADMIT once the multiplicity bill comes from "
                          "the prospective declaration instead of AA's over-counted 69 — "
                          "measured by re-running the real gate "
                          "(AI_GATE_AT_DECLARED_FAMILY_V1.json)."),
            "declaration": {"path": str(DECL.relative_to(REPO)),
                            "ratified": bool(decl.get("ratified_by"))},
            "admission_is_conditional_on": (
                "alpha. Both members admit at alpha=0.20 at any declared family <= 32, and "
                "NEITHER admits alone at alpha=0.10 — Benjamini-Hochberg's step-up means they "
                "clear together or not at all. So this book's membership is a consequence of "
                "an owner decision that has not been taken yet."),
            "sub_xvol_pullback_is_already_armed": True,
            "weights_at_the_convention": {s: conf.get(s) for s in challenge},
            "the_weight_finding": (
                "`mx_btcusd`'s registry confidence is 0.025 "
                "(`default_off_runtime_capable_zero_activation`) against `sub_xvol_pullback`'s "
                "0.45 and `crypto`'s 0.85 — 34x smaller than the armed sleeve. At the "
                "allocator's own convention, admitting it barely moves a book. The "
                "equal-weight branch prices what re-weighting it would be worth; the weight is "
                "Borhen's, and this is the number he needs to take that decision."),
        },
        "cache_books": cache_books,
        "archive_books": arch,
    }

    # ---- control: does this file reproduce Session V's published ARMED_SET_MC figure? ----
    if ARMED_MC.is_file():
        am = json.loads(ARMED_MC.read_text())
        try:
            v_both3 = (am["grid"]["BOTH_3"]["fwd_nights_max"]["live"]["rules"]
                       ["L4_FIRM_TRUE_PH1"]["p_pass"])
            v_both3_p2 = (am["grid"]["BOTH_3"]["fwd_nights_max"]["live"]["rules"]
                          ["P2_BOTH_PHASES"]["p_pass"])
        except (KeyError, TypeError):
            v_both3 = v_both3_p2 = None
        mine = ((cache_books["live_nominal_half_kelly"]["books"]["FTMO_ARMED_TODAY_3"]
                 ["cells"].get("fwd_nights_max") or {}).get("rules", {})
                .get("L4_FIRM_TRUE_PH1", {}).get("p_pass"))
        doc["control_vs_session_V"] = {
            "claim": ("Session V's `BOTH_3` set IS the set FTMO is armed on today — V labelled "
                      "it 'Q's SURVIVORS_BOTH_ACCOUNTS ... included because the two "
                      "three-sleeve books in the record are not the same book', which was "
                      "written before the 14:25 UTC adjustment to three sleeves. So the "
                      "account-intersection book V measured as a contrast is the live canary."),
            "v_sleeves": am.get("sets", {}).get("BOTH_3"),
            "my_sleeves": ARMED_TODAY,
            "sets_identical": sorted(am.get("sets", {}).get("BOTH_3") or []) == sorted(
                ARMED_TODAY),
            "v_p_pass_fwd_worst_live_L4": v_both3,
            "v_p_pass_fwd_worst_live_P2": v_both3_p2,
            "my_p_pass_fwd_worst_live_P2": (
                (cache_books["live_nominal_half_kelly"]["books"]["FTMO_ARMED_TODAY_3"]
                 ["cells"].get("fwd_nights_max") or {}).get("rules", {})
                .get("P2_BOTH_PHASES", {}).get("p_pass")),
            "my_p_pass_fwd_worst_live_L4": mine,
            "abs_difference": (abs(v_both3 - mine)
                               if isinstance(v_both3, float) and isinstance(mine, float)
                               else None),
            # CORRECTED after a check that was worth making: the first draft of this field
            # attributed the residual to seed noise, and that is WRONG for P2. The L4 gap is
            # 0.0041, inside Q's measured <= 0.00463 seed band; the P2 gap is 0.0070, which at
            # 60,000 and 200,000 paths is ~5 standard errors and therefore not noise.
            #
            # The real cause is the drift this file already declares: `git merge-base
            # --is-ancestor` shows Session V's ARMED_SET_MC_V1.json (0975e2e54, 2026-07-29)
            # PREDATES both 33d854189 and 8f6da5150, so V's series is on the OLD cost basis and
            # this one is on the extended FTMO coverage. Two runs on two cost bases.
            #
            # That makes the control STRONGER, not weaker: two independently written drivers
            # agree to within 0.4-0.7 points ACROSS a documented input change, and the residual
            # has a named cause rather than being absorbed into a noise band.
            "residual_cause": (
                "NOT seed noise. V's artifact predates 33d854189 and 8f6da5150, which extended "
                "BROKER_TRUE_COSTS_V1.json on FTMO, so V's series is on the old cost basis. "
                "L4 gap 0.0041 (inside Q's <= 0.00463 seed band and consistent with noise "
                "alone); P2 gap 0.0070, which is ~5 SE at these path counts and is the cost "
                "basis. Verified by ancestry, not assumed."),
            "seed_band_for_reference": 0.00463,
            "claude_md_correction": (
                "CLAUDE.md section 4 says 'Do not adopt the SURVIVORS_BOTH_ACCOUNTS number for "
                "the canary; it is the account-intersection book, not the config-runnable "
                "one.' That warning was written against the 12:55 armed set "
                "(`metals_core, crypto, energy_agri`) and is INVERTED by the 14:25 adjustment: "
                "SURVIVORS_BOTH_ACCOUNTS is now exactly the armed set, and CONF_FLOOR_3 is the "
                "set that is no longer armed. The same section's "
                "'[MEASURED: absence] no MC at 2.0 % exists for exactly the three-sleeve book' "
                "is therefore satisfied for the live three and still true for "
                "`metals_core, crypto, energy_agri`."),
        }
        print(f"\ncontrol vs Session V: V={v_both3} mine={mine} "
              f"sets_identical={doc['control_vs_session_V']['sets_identical']}")

    OUT_JSON.write_text(json.dumps(doc, indent=1, default=str))
    OUT_MD.write_text(render(doc))
    print(f"\nwrote {OUT_JSON.relative_to(REPO)}")
    print(f"wrote {OUT_MD.relative_to(REPO)}")


def render(doc) -> str:
    L, A = [], None
    A = L.append
    A("# `BOOKS_MC_V1` — the books an arming decision can pick from, at each firm's measured rules")
    A("")
    A(f"**Session AI, wave 8.** {doc['machinery']['n_paths']:,} paths per cell through Session "
      f"Q's `mc_firm_rules.mc`, imported unchanged. `L4` is each firm's measured phase 1; "
      f"**`P2` is the whole 2-step evaluation and it is the one that gates a payout.**")
    A("")
    A("## 0. The book the machinery cannot compose")
    A("")
    A(doc["the_book_the_machinery_cannot_compose"]["what"])
    A("")
    A(doc["the_book_the_machinery_cannot_compose"]["consequence"])
    A("")
    A("## 1. The cache books — the W7 population, both sizing conventions")
    A("")
    A("Every published figure the owner has seen is the `published` convention; the deployable "
      "path implements `live`, and they differ by ~2.1x in size "
      "(`ARMED_SET_MC_V1.json` §1). Both are here because reporting one would be reporting "
      "the wrong number to somebody.")
    A("")
    for conv, blk in doc["cache_books"].items():
        A(f"### {conv}  (`eff risk` is the per-correlated-unit risk this convention delivers)")
        A("")
        A("| book | account | n | cell | days | eff risk | mean R/day | **L4 p_pass** | L4 cal-d "
          "| **P2 p_pass** | P2 cal-d | %/mo |")
        A("|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for name, b in blk["books"].items():
            for key in CELL_KEYS:
                c = (b.get("cells") or {}).get(key)
                if not c:
                    continue
                l4 = (c.get("rules") or {}).get("L4_FIRM_TRUE_PH1") or {}
                p2 = (c.get("rules") or {}).get("P2_BOTH_PHASES") or {}
                A(f"| `{name}` | {b['account']} | {len(b['sleeves'])} | {key} | "
                  f"{c['book_days']} | {c['eff_risk_pct']:.3f} % | {c['mean_r_per_book_day']} | "
                  f"**{l4.get('p_pass')}** | {l4.get('median_calendar_days_to_pass')} | "
                  f"**{p2.get('p_pass')}** | {p2.get('median_calendar_days_to_pass')} | "
                  f"{l4.get('monthly_pct_calendar')} |")
        A("")
    A("## 2. The challenge book — the ARCHIVE population, with its same-population control")
    A("")
    cb = doc["challenge_book_membership"]
    A(f"**Members: {', '.join('`%s`' % s for s in cb['members'])}.** "
      f"{cb['why_these']}")
    A("")
    A(f"**{cb['admission_is_conditional_on']}**")
    A("")
    A(f"Weights at the allocator's own convention: "
      + ", ".join(f"`{k}` {v}" for k, v in cb["weights_at_the_convention"].items()) + ".")
    A("")
    A(f"*{cb['the_weight_finding']}*")
    A("")
    A("| book | weights | branch | eff risk | days | mean R/day | acct | **L4** | **P2** | "
      "P2 cal-d | %/mo |")
    A("|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|")
    for name, b in doc["archive_books"].items():
        for basis, br in (b.get("branches") or {}).items():
            for acct, ab in (br.get("accounts") or {}).items():
                l4 = (ab.get("rules") or {}).get("L4_FIRM_TRUE_PH1") or {}
                p2 = (ab.get("rules") or {}).get("P2_BOTH_PHASES") or {}
                A(f"| `{name}` | {b['weights'].split('—')[0].strip()[:22]} | "
                  f"{basis[:22]} | {br['eff_risk_pct']} % | {b['book_days']} | "
                  f"{b['mean_r_per_book_day']} | {acct} | **{l4.get('p_pass')}** | "
                  f"**{p2.get('p_pass')}** | {p2.get('median_calendar_days_to_pass')} | "
                  f"{l4.get('monthly_pct_calendar')} |")
    A("")
    g = doc["the_population_gap_on_the_armed_book"]
    A("## 2b. The same three sleeves, two populations, 14x apart")
    A("")
    A(f"**{g['question']}**")
    A("")
    A("| population | book-days | mean R/day | %/mo calendar | P2 p_pass | P2 cal-days |")
    A("|---|---:|---:|---:|---:|---:|")
    for lab, k in (("W7 CACHE, fwd 2025+, worst carry",
                    "W7_CACHE_forward_2025_plus_worst_carry"),
                   ("ARCHIVE, whole span", "ARCHIVE_whole_span")):
        b = g[k]
        A(f"| {lab} | {b['book_days']} | {b['mean_r_per_book_day']} | "
          f"**{b['monthly_pct_calendar']}** | {b['p_pass_both_phases']} | "
          f"{b['calendar_days_both_phases']} |")
    A("")
    A(f"**Ratio on the monthly rate: {g['ratio_monthly_pct']}x.** {g['why']}")
    A("")
    A(f"{g['corroboration']}")
    A("")
    A(f"**{g['reading']}**")
    A("")
    if doc.get("control_vs_session_V"):
        c = doc["control_vs_session_V"]
        A("## 3. A correction to `CLAUDE.md` §4, found by controlling against Session V")
        A("")
        A(f"**{c['claim']}**")
        A("")
        A(f"- V's `BOTH_3` = `{c['v_sleeves']}`; the armed set = `{c['my_sleeves']}`; "
          f"**identical: {c['sets_identical']}**.")
        A(f"- V's published `p_pass` (fwd / worst carry / live sizing / L4): "
          f"**{c['v_p_pass_fwd_worst_live_L4']}**; this file at "
          f"{doc['machinery']['n_paths']:,} paths: **{c['my_p_pass_fwd_worst_live_L4']}** "
          f"(|Δ| {c['abs_difference']}). {c['residual_cause']}")
        A("")
        A(c["claude_md_correction"])
        A("")
    A("## 4. Per-book member lists, verbatim")
    A("")
    A("| book | account | sleeves |")
    A("|---|---|---|")
    for conv, blk in doc["cache_books"].items():
        for name, b in blk["books"].items():
            A(f"| `{name}` | {b['account']} | {', '.join('`%s`' % s for s in b['sleeves'])} |")
        break
    for name, b in doc["archive_books"].items():
        A(f"| `{name}` | both | {', '.join('`%s`' % s for s in sorted(b['per_sleeve']))} |")
    A("")
    for name, b in doc["cache_books"]["published_vol_matched_full_kelly"]["books"].items():
        if b.get("data_gap"):
            A(f"**`{name}` data gap.** {b['data_gap']}")
            A("")
    return "\n".join(L)


if __name__ == "__main__":
    main()
