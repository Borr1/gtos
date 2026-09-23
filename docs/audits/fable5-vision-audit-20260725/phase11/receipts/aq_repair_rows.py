"""Session AQ — repair-queue rows, read out of this session's own artifacts (B1443-B1447).

    python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/aq_repair_rows.py

Append-only, union-merged at the train. Dedup follows AO's shape — `(session, sleeve,
prescription)` scoped to THIS session's rows, because that triple is not globally unique by
design (AD files one prescription for one sleeve at two accounts). Pre-existing
cross-session collisions are reported, never failed.

Every `evidence` block is read from an artifact on disk. Nothing here is typed twice.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
HERE = AUD / "phase11/receipts"
QUEUE = AUD / "phase6/receipts/REPAIR_QUEUE_APPEND.jsonl"
CT = HERE / "AQ_CONTRACT_TRUTH_V1.json"
EH = HERE / "AQ_ENTRY_HOUR01_V1.json"
EV2 = HERE / "AQ_ESTATE_V2_RECEIPT.json"
SESSION = "AQ"
NOW = dt.datetime.now(dt.timezone.utc).isoformat()


def rows() -> list[dict]:
    ct = json.loads(CT.read_text())
    eh = json.loads(EH.read_text())
    ev2 = json.loads(EV2.read_text())
    audit = ct["spec_audit"]
    per = ct["walk"]["per_sleeve"]
    adm = ct["admission"]["arms"]
    BTC = "mx_btcusd_d1_donchian_20_breakout"
    out: list[dict] = []

    def band(s, b, k):
        return (per[s]["by_band"].get(b) or {}).get(k)

    # ---- 1. the unit defect, per mis-scaled sleeve that generates ----------------------
    for s in audit["the_defect"]["sleeves"]:
        r = per.get(s) or {}
        if not r.get("n_trades_walked"):
            continue
        d = band(s, "mid", "repair_worth_r_per_day")
        favourable = (d is not None and d < 0)
        unmeasured = d is None
        if unmeasured:
            tail = (". NOT MEASURABLE at the ratified rule: only "
                    f"{band(s, 'mid', 'published_n')} of {r['n_trades_walked']} trades "
                    "survive the RECORDED population and they fall in a single evaluable "
                    "fold, so the gate refuses on `insufficient_sample`. The unit repair "
                    "lands on the same evidence as the rest of the cohort; its per-sleeve "
                    "value is unknown and stays unknown until this symbol has era coverage.")
        elif favourable:
            tail = (f", and it is NEGATIVE ({d:+.4f} R/day): the accidental one-bar stop was "
                    "BETTER than the research horizon for this sleeve. The unit repair still "
                    "lands — a spec must mean what it says — but the follow-up is to declare "
                    "a short horizon DELIBERATELY on the evidence rather than inherit one "
                    "from a bug. That is an exit-frontier decision, not a unit one.")
        else:
            tail = (f" worth {d:+.4f} R/day. The published economics are now the live "
                    "contract for this sleeve.")
        out.append({
            "session": SESSION, "sleeve": s,
            "component": "src/components/ultimate_book/execution_packets.py:91-94",
            "prescription": (
                "TIME_STOP_UNIT_REPAIRED_VALUE_NOT_MEASURABLE_ON_RECORDED" if unmeasured
                else "TIME_STOP_UNIT_REPAIRED_BUT_THE_ACCIDENT_WAS_FAVOURABLE" if favourable
                else "TIME_STOP_UNIT_REPAIRED"),
            "gate": "sample" if unmeasured else "", "verdict": "FIXED",
            "is_primary": not (favourable or unmeasured), "margin": d,
            "action": (
                "`time_stop_bars` was 96 — the M15-per-D1 conversion RATIO, not a horizon — "
                "so the live time stop was 1 D1 bar against the 80-D1-bar research horizon "
                "every published number for this sleeve uses. Repaired to 7680 "
                "(`time_stop_m15(80, \"D1\")`), pinned by "
                "tests/ultimate_book/test_time_stop_units.py. Measured at RECORDED/mid the "
                "repair is" + tail),
            "evidence": {
                "artifact": str(CT.relative_to(REPO)),
                "declared_before": 96, "declared_after": 7680,
                "live_time_stop_own_bars": r.get("live_time_stop_own_bars"),
                "repaired_time_stop_own_bars": r.get("repaired_time_stop_own_bars"),
                "published_r_per_day_mid": band(s, "mid", "published_r_per_day"),
                "live_true_r_per_day_mid": band(s, "mid", "live_true_r_per_day"),
                "repair_worth_r_per_day_mid": d,
                "frac_trades_truncated":
                    audit["sleeves"][s]["frac_trades_the_time_stop_would_truncate"],
                "published_median_hold_h": band(s, "mid", "published_median_hold_h"),
                "live_true_median_hold_h": band(s, "mid", "live_true_median_hold_h"),
                "n_trades": r.get("n_trades_walked"),
            },
            "appended_utc": NOW,
        })

    # ---- 2. the other side: unit-correct spec, mislabelled economics -------------------
    for s in audit["unit_correct_but_research_never_applied_it"]["sleeves"]:
        pub, liv = band(s, "mid", "published_r_per_day"), band(s, "mid", "live_true_r_per_day")
        if pub is None or liv is None:
            continue
        err = pub - liv
        out.append({
            "session": SESSION, "sleeve": s,
            "component": "generation port / research labelling",
            "prescription": "RESTAMP_PUBLISHED_ECONOMICS_AT_THE_LIVE_CONTRACT",
            "gate": "", "verdict": "INFORMATIONAL",
            "is_primary": abs(err) > 0.05, "margin": err,
            "action": (
                f"This sleeve's `time_stop_bars` is CORRECTLY scaled — the spec is right and "
                f"the label is wrong. Every published number for it is walked at "
                f"maxbars=80 with the time stop NOT applied, and at RECORDED/mid the "
                f"publication error is {err:+.4f} R/day "
                f"({pub:.4f} published vs {liv:.4f} at its own live contract). AD filed this "
                f"class as INFORMATIONAL from the unit table (B750); this row carries the "
                f"GATED delta at the ratified population and band. Re-stamp before any "
                f"composition decision reads the published figure."),
            "evidence": {
                "artifact": str(CT.relative_to(REPO)),
                "time_stop_bars_m15": audit["sleeves"][s]["declared_time_stop_bars_m15"],
                "time_stop_own_bars": per[s]["live_time_stop_own_bars"],
                "published_r_per_day_mid": pub, "live_true_r_per_day_mid": liv,
                "publication_error_r_per_day": err,
                "frac_trades_truncated":
                    audit["sleeves"][s]["frac_trades_the_time_stop_would_truncate"],
                "n_trades": per[s]["n_trades_walked"],
            },
            "appended_utc": NOW,
        })

    # ---- 3. the admission is contingent on the repair ---------------------------------
    a_rep = adm["REPAIRED|B_balanced|RECORDED|mid"][BTC]
    a_liv = adm["LIVE_TRUE|B_balanced|RECORDED|mid"][BTC]
    out.append({
        "session": SESSION, "sleeve": BTC,
        "component": "the challenge package for the estate's one standing admission",
        "prescription": "THE_ADMISSION_IS_CONTINGENT_ON_THE_TIME_STOP_REPAIR",
        "gate": "significance", "verdict": "OWNER_DECISION",
        "is_primary": True, "margin": a_rep["p_raw"] - a_liv["p_raw"],
        "action": (
            "`target_5R` carries NO time stop and holds 82.3 % of its trades past 24 h. "
            "Under the contract the live book ran until 2026-07-30 those trades close at "
            "~24 h, and the admission does not survive it: p "
            f"{a_rep['p_raw']:.6g} -> {a_liv['p_raw']:.6g} at RECORDED/mid, fold positivity "
            f"{a_rep['oos_positive_fold_frac']} -> {a_liv['oos_positive_fold_frac']} with the "
            "two most recent folds NEGATIVE, and REJECT at all four bands. The unit repair "
            "landed this session, so the admission now describes a contract the book can "
            "run — but any package citing it must name the exit contract AND the repair. "
            "Neither change alone admits: 2R at the repaired horizon is p 0.0064, 5R under "
            "the old time stop is p 0.0564, both together p 0.0011."),
        "evidence": {
            "artifact": str(CT.relative_to(REPO)),
            "dossier": "docs/audits/fable5-vision-audit-20260725/phase11/MX_BTCUSD_CHALLENGE_DOSSIER.md",
            "repaired": {k: a_rep[k] for k in ("verdict", "p_raw", "q_value",
                                               "pooled_oos_mean_r", "n_trades",
                                               "oos_positive_fold_frac")},
            "live_true": {k: a_liv[k] for k in ("verdict", "p_raw", "q_value",
                                                "pooled_oos_mean_r", "n_trades",
                                                "oos_positive_fold_frac")},
            "repaired_fold_means": a_rep["fold_means"],
            "live_true_fold_means": a_liv["fold_means"],
            "declared_family_size": a_rep["declared_family_size"],
        },
        "appended_utc": NOW,
    })

    # ---- 4. downstream artifacts still on the defect clock ----------------------------
    out.append({
        "session": SESSION, "sleeve": "sub_mid_dn_revert",
        "component": ("phase6/receipts/AA_ESTATE_WALK.json, "
                      "phase7/receipts/EXIT_FRONTIER_V1.json, "
                      "phase7/receipts/AD_CARRY_TIERS_RESTATED_V1.json, "
                      "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"),
        "prescription": "REBUILD_THE_DOWNSTREAM_ARTIFACTS_ON_THE_REPAIRED_CLOCK",
        "gate": "", "verdict": "REJECT",
        "is_primary": True, "margin": None,
        "action": (
            "AM repaired `substrate._session_hour` and measured the A/B; the artifact "
            "everything downstream reads was never regenerated. This session publishes "
            f"`{Path(ev2['artifact']).name}` (sha256 {ev2['sha256'][:12]}), AA's estate with "
            f"this sleeve's population replaced — {ev2['what_moved']['n_before']} -> "
            f"{ev2['what_moved']['n_after']} trades, jaccard "
            f"{ev2['what_moved']['jaccard']}, mean R "
            f"{ev2['what_moved']['mean_r_before']} -> {ev2['what_moved']['mean_r_after']} — "
            "with the control that AM's authored-clock arm reproduces AA exactly "
            f"({ev2['control_am_reproduces_aa']['n_aa']} rows, "
            f"{ev2['control_am_reproduces_aa']['n_r_gross_mismatched']} r_gross mismatches). "
            "The four artifacts named above are still built on the 503. Cost to rebuild: "
            "AA_ESTATE_WALK ~2 min from the V2 artifact, EXIT_FRONTIER ~27 min, the carry "
            "tiers and survivor book arithmetic on top."),
        "evidence": {
            "artifact": str(EV2.relative_to(REPO)),
            "estate_v2": ev2["artifact"], "sha256": ev2["sha256"],
            "control": ev2["control_am_reproduces_aa"],
            "what_moved": ev2["what_moved"],
            "gated_at_ratified_rule": {
                b: {k: (ct["walk"]["arms"][f"PUBLISHED|RECORDED|{b}"]["sub_mid_dn_revert"]
                        .get(k))
                    for k in ("verdict", "p_raw", "pooled_oos_mean_r", "n_trades",
                              "drop_best_retention")}
                for b in ("flat", "low", "mid", "high")},
        },
        "appended_utc": NOW,
    })

    # ---- 5. the hour-01 capture requirement -------------------------------------------
    fine = eh["fine"]["summary"]
    out.append({
        "session": SESSION, "sleeve": "__fx_d1_cohort__",
        "component": "the intraday bar archive (/Users/borr/GTOSActive/vps-bars-20260727)",
        "prescription": "CAPTURE_INTRADAY_BARS_TO_VALIDATE_THE_RATIFIED_ENTRY_CONVENTION",
        "gate": "", "verdict": "OWNER_DECISION",
        "is_primary": True,
        "margin": fine["pooled"]["h01_ratified"]["net_delta_vs_h00"],
        "action": (
            "The ratified hour-01 entry convention is CONFIRMED on a three-mechanism exact "
            f"re-derivation — {fine['pooled']['h01_ratified']['net_delta_vs_h00']:+.5f} R/trade "
            f"net against hour 00 and "
            f"{fine['pooled']['h01_ratified']['net_delta_vs_h00'] - fine['pooled']['h04_ah_comparator']['net_delta_vs_h00']:+.5f} "
            "against AH's hour 04 — but only on 2024-01-04..2026-07-23, because an hour-01 "
            "fill needs a bar closing at broker 01:00 and the D1 grid closes at 00:00, the "
            "H4 grid at 00/04/08/12/16/20, and the M15 archive starts 2023-12-31. CAPTURE "
            "REQUIREMENT: M15 or H1 bars for the 14 FX symbols (AUDJPY AUDUSD CADJPY CHFJPY "
            "EURGBP EURJPY EURUSD GBPJPY GBPUSD NZDJPY NZDUSD USDCAD USDCHF USDJPY) back to "
            "2001 would let the convention be validated over the cohort's full 26 years. "
            "Until then the convention rests on 2.5 years and the full-archive arm is "
            "cost-only, which holds gross fixed and cannot see edge."),
        "evidence": {
            "artifact": str(EH.relative_to(REPO)),
            "window": fine["window"],
            "pooled_net_r_per_trade": {a: fine["pooled"][a]["mean_net_r"]
                                       for a in sorted(fine["pooled"])},
            "by_mechanism_delta_vs_h00": {
                m: v["h01_ratified"]["net_delta_vs_h00"]
                for m, v in fine["by_mechanism"].items()},
            "wide_arm_is_cost_only": eh["wide"]["what"][:180],
            "wide_spread_saved_r_per_trade": eh["wide"]["arms"]["h01_ratified"][
                "total_saved_vs_h00"],
            "wide_n_rows": eh["wide"]["n_rows"],
        },
        "appended_utc": NOW,
    })

    # ---- 6. the cohort is confirmed-better and still not admissible -------------------
    g = eh["gate"]["arms"]
    best = min((v for v in g.values() if v["p_raw"] is not None), key=lambda v: v["p_raw"])
    out.append({
        "session": SESSION, "sleeve": "__fx_d1_cohort__",
        "component": "the FX D1 42-member cohort",
        "prescription": "ENTRY_CONVENTION_CONFIRMED_BUT_THE_COHORT_STILL_DOES_NOT_ADMIT",
        "gate": "significance", "verdict": "REJECT",
        "is_primary": False, "margin": best["p_raw"],
        "action": (
            "0 of 72 gated arms admit (3 pooled mechanism families x 3 entry hours x 4 cost "
            f"bands x 2 multiplicity bills). Best p is {best['p_raw']:.4g} on "
            f"`{best['sleeve']}` at {best['arm']}/{best['band']} — an order of magnitude from "
            "the rank-1 bar, so this is not a near miss and no repair on this axis closes "
            "it. `donchian_20_breakout` is the only family whose pooled R/day changes SIGN "
            "at hour 01 (-0.2196 -> +0.0316 at mid) and it is also the mechanism AM's "
            "frontier never covered. The entry convention is a COST repair worth taking; it "
            "is not an edge, and the cohort should not be routed as a candidate on it."),
        "evidence": {
            "artifact": str(EH.relative_to(REPO)),
            "n_arms": len(g), "n_admit": sum(1 for v in g.values() if v["verdict"] == "ADMIT"),
            "n_not_evaluable": sum(1 for v in g.values()
                                   if v["verdict"] == "NOT_EVALUABLE"),
            "best_arm": {k: best[k] for k in ("sleeve", "arm", "band", "bill", "verdict",
                                              "p_raw", "q_value", "pooled_oos_mean_r",
                                              "n_trades")},
            "declared_family": eh["declared_family"],
        },
        "appended_utc": NOW,
    })

    # ---- 7. the wipeout signal --------------------------------------------------------
    out.append({
        "session": SESSION, "sleeve": "__estate__",
        "component": "src/research_infra/walkforward/gate.py",
        "prescription": "A_WHOLE_RUN_OF_NULLS_NOW_FALLS_LOUDLY",
        "gate": "", "verdict": "FIXED",
        "is_primary": False, "margin": None,
        "action": (
            "The first run of this session's entry-hour gate returned 72 arms, every one "
            "NOT_EVALUABLE on `port_fidelity_unmeasured`, because the caller had not wrapped "
            "`run_gate` in `family.fidelity_scope` — which every research cohort outside the "
            "production registry needs. Nothing in the result said so; the arms tabulated "
            "cleanly, one per entry hour and cost band, and read exactly like a measurement. "
            "`GateResult.family['wipeout']` now reports when NOT ONE submitted sleeve "
            "reached a null, names the dominant refusal class, and for the fidelity class "
            "names the fix. It changes no verdict. 7 tests, including one that pins it "
            "SILENT as soon as a single sleeve is scored, so it cannot become noise."),
        "evidence": {
            "artifact": "tests/research_infra/test_gate_wipeout_signal.py",
            "site": "src/research_infra/walkforward/gate.py _wipeout",
            "n_arms_that_were_silently_empty": 72,
            "classes_covered": ["port_fidelity_unmeasured", "port_fidelity_below_floor",
                                "cost_coverage_below_floor",
                                "symbol_outside_registry_universe", "other"],
            "standing_rule": "wave-10 working agreement §2, 'silent nulls fall loudly'",
        },
        "appended_utc": NOW,
    })
    return out


def main() -> None:
    new = rows()
    existing = []
    if QUEUE.is_file():
        existing = [json.loads(l) for l in QUEUE.read_text().splitlines() if l.strip()]
    mine = {(r.get("session"), r.get("sleeve"), r.get("prescription"))
            for r in existing if r.get("session") == SESSION}
    others = {(r.get("sleeve"), r.get("prescription"))
              for r in existing if r.get("session") != SESSION}

    write, dupes, collisions = [], [], []
    seen = set()
    for r in new:
        k = (r["session"], r["sleeve"], r["prescription"])
        if k in mine or k in seen:
            dupes.append(k)
            continue
        if (r["sleeve"], r["prescription"]) in others:
            collisions.append(k)      # reported, not refused — AD files across accounts
        seen.add(k)
        write.append(r)

    with QUEUE.open("a") as fh:
        for r in write:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"appended {len(write)} rows to {QUEUE.relative_to(REPO)} "
          f"(now {len(existing) + len(write)}); {len(dupes)} skipped as this session's own "
          f"duplicates; {len(collisions)} cross-session prescription collisions reported: "
          f"{collisions}")
    for r in write:
        print(f"  {r['verdict']:14s} {r['prescription'][:52]:52s} {r['sleeve']}")


if __name__ == "__main__":
    main()
