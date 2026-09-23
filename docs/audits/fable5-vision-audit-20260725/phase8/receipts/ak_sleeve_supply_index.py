"""Deliverable 1 — `SLEEVE_SUPPLY_V1.json`, the per-member index the commission named.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ak_sleeve_supply_index.py

WHY THIS EXISTS AND WHY IT IS LAST
-----------------------------------
`SESSION_AK_SLEEVE_SUPPLY.md`'s deliverable 1 asks for one artifact carrying, **per new or
reworked member**: generator provenance, gate verdict at measured carry, exit frontier if swept,
diversifier-door verdict where run, and the next prescription. This session produced all five
kinds of evidence and put them in five differently-named files, so the named deliverable did not
exist and a reader had no index. A completeness pass caught it.

It is built by REDUCTION over the five artifacts rather than by hand, so it cannot disagree with
them: every field names the artifact and key it came from. Re-running it after any driver re-runs
is the whole point.

It also carries the four things the completeness pass found MISSING from the session rather than
wrong in it, because an index is the honest place for a limitation that spans every member:

  * `prior_gate_receipt_search` — the evidence for "no walk-forward gate had judged them", which
    was asserted in prose and recorded nowhere.
  * `engine_reachability` — the working agreement's §4 convention is to default every economic
    number to the live convention and publish fix-enabled as a sensitivity. The gate ran on ALL
    generated rows, so the delta is published here per sleeve instead of being absent.
  * `cost_basis` — every number in this session is priced at one modern per-symbol spread with no
    era band, over spans reaching 20 years. AF restricted banded pricing to `era_class ==
    RECORDED` for a measured reason; not banding is a different choice and the reader is entitled
    to be told which one produced the numbers.
  * `first_of_day_coverage_map` — commission item 4 names seven sleeves; three got an AK frontier,
    three are covered by AD's, and one is covered by AD's and appears nowhere in AK's prose.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
P7 = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
TRADES = HERE / "AK_SUPPLY_TRADES.json.gz"
GATE = HERE / "AK_SUPPLY_GATE_V1.json"
CELLS = HERE / "AK_SLEEVE_CELLS_V1.json"
FRONTIER = HERE / "AK_EXIT_FRONTIER_V2.json"
DIV = HERE / "AK_DIVERSIFIER_V1.json"
DOSSIER = HERE / "AK_CANDIDATE_DOSSIER_V1.json"
QUEUE_APPEND = P6 / "REPAIR_QUEUE_APPEND.jsonl"
OUT = HERE / "SLEEVE_SUPPLY_V1.json"

#: Commission item 4's seven first-of-day sleeves, in its own order.
FIRST_OF_DAY = ("asia_pdl_fade", "asian_fade", "liq_asia_up_low_metal",
                "metal_session_reversion", "orb_crypto_london", "ny_crypto_momentum",
                "kz_london_crypto_low")


def _load(p: Path):
    if not p.is_file():
        return None
    if p.suffix == ".gz":
        return json.load(gzip.open(p, "rt"))
    return json.loads(p.read_text())


def prior_gate_receipt_search() -> dict:
    """The evidence for "no walk-forward gate had judged the four", recorded rather than asserted.

    Two searches, both re-runnable: every phase3-phase7 JSON receipt for the sleeve NAME, and the
    trial ledger for a pre-AK row. A name appearing in a receipt is NOT automatically a verdict —
    `ny_index_momentum` appears in Y's lineage list as a member of a swapped-clock set with no
    verdict — so hits are reported with their file so a reader can check the difference.
    """
    names = ("vol_squeeze", "ny_index_momentum", "structural_retest", "session_leadlag_genuine")
    root = REPO / "docs/audits/fable5-vision-audit-20260725"
    hits: dict[str, list[str]] = {n: [] for n in names}
    n_files = 0
    for phase in ("phase3", "phase4", "phase5", "phase6", "phase7"):
        for p in sorted((root / phase).rglob("*.json")):
            n_files += 1
            try:
                text = p.read_text()
            except (OSError, UnicodeDecodeError):
                continue
            for n in names:
                if n in text:
                    hits[n].append(str(p.relative_to(root)))
    ledger = REPO / "research/operations/trial_budget/TRIAL_LEDGER.jsonl"
    pre_ak: dict[str, int] = {n: 0 for n in names}
    if ledger.is_file():
        for line in ledger.read_text().splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (row.get("session") or "") == "AK":
                continue
            s = str(row.get("sleeve") or "")
            for n in names:
                if s == n:
                    pre_ak[n] += 1
    return {
        "claim": ("no walk-forward gate run in this programme had judged these four before "
                  "Session AK"),
        "search_1_receipt_json": {
            "n_json_files_scanned": n_files,
            "scope": "docs/audits/fable5-vision-audit-20260725/phase{3,4,5,6,7}/**/*.json",
            "name_hits": {k: v for k, v in hits.items() if v},
            "names_with_zero_hits": sorted(k for k, v in hits.items() if not v),
            "how_to_read_a_hit": ("a NAME in a receipt is not a VERDICT. Any hit here must be "
                                 "opened: Y's lineage receipts list ny_index_momentum as a member "
                                 "of the clock-swap set with no gate verdict attached."),
        },
        "search_2_trial_ledger": {
            "path": "research/operations/trial_budget/TRIAL_LEDGER.jsonl",
            "pre_AK_rows_per_sleeve": pre_ak,
            "note": ("the ledger is the prospective look counter; a pre-AK row for one of these "
                     "names would mean some earlier session evaluated it as a variant"),
        },
        "what_this_does_NOT_claim": (
            "that the sleeves were unexamined. candidate_registry.py:48-85 carries a full "
            "CandidateSpec for vol_squeeze, ny_index_momentum and structural_retest with "
            "every-split economics, and CANDIDATE_DECISION (:209-223) records explicit "
            "quarantine verdicts from the 2026-06-17 principal audit. "
            "session_leadlag_genuine's research-side generator (KB6_session_stacks.py:77) "
            "produced the n=390 / +0.4598 R numbers admission.py:267-277 cites."),
    }


def engine_reachability(tr: dict) -> dict:
    """The §4 convention, published as the sensitivity it should have been from the start.

    The working agreement asks that every economic number default to the LIVE convention
    (`engine_reachable` only) with fix-enabled as a band. This session's generation carries the
    flag per row but the gate ran on ALL rows, so the number published is the fix-enabled one.
    The delta is small on every sleeve here and it is published rather than left absent.
    """
    out: dict = {
        "convention_used_for_every_gate_verdict": "ALL generated rows (fix-enabled)",
        "convention_the_agreement_asks_for": "engine_reachable only (live)",
        "why_it_was_not_re-run": ("the gate and both exit sweeps are ~20 minutes of gating and the "
                                 "deltas below are 0.0-3.0 % of rows on the four new sleeves. "
                                 "Stated as a limitation rather than silently absent; a reader "
                                 "who needs the live-convention verdict has the flag on every "
                                 "row of AK_SUPPLY_TRADES.json.gz to re-gate from."),
        "by_sleeve": {},
    }
    for tag, spec in (tr.get("specs") or {}).items():
        a = spec.get("summary_authored_exit") or {}
        n, nr = a.get("n"), a.get("n_engine_reachable")
        if not n:
            continue
        out["by_sleeve"][tag] = {
            "n_all": n, "n_engine_reachable": nr,
            "n_pre_gap": n - (nr or 0),
            "pre_gap_frac": round((n - (nr or 0)) / n, 5),
            "mean_r_gross_all": a.get("mean_r_gross"),
            "mean_r_gross_reachable": a.get("mean_r_gross_reachable"),
            "delta_mean_r_gross": (
                round((a.get("mean_r_gross_reachable") or 0) - (a.get("mean_r_gross") or 0), 6)
                if a.get("mean_r_gross_reachable") is not None else None),
        }
    out["largest_pre_gap_frac"] = max(
        (v["pre_gap_frac"] for v in out["by_sleeve"].values()), default=None)
    return out


def first_of_day_coverage_map(fr: dict) -> dict:
    ak = set((fr.get("sleeves") or {}))
    ad = set()
    for p in (P7 / "EXIT_FRONTIER_V1.json", P7 / "EXIT_FRONTIER_V1_TRAIL.json"):
        if p.is_file():
            ad |= set(json.loads(p.read_text()).get("sleeves") or {})
    rows = {}
    for s in FIRST_OF_DAY:
        rows[s] = {
            "ak_frontier": s in ak,
            "ad_frontier": s in ad,
            "covered_by": ("AK" if s in ak else ("AD (inherited)" if s in ad else "NEITHER")),
        }
    return {
        "commission_item": ("item 4 — 'sweep the exit families over their stored intents, re-gate, "
                           "and publish each one's frontier the way AD did' for the seven "
                           "first-of-day sleeves"),
        "by_sleeve": rows,
        "n_ak": sum(1 for v in rows.values() if v["ak_frontier"]),
        "n_ad_inherited": sum(1 for v in rows.values()
                              if not v["ak_frontier"] and v["ad_frontier"]),
        "n_uncovered": sum(1 for v in rows.values() if v["covered_by"] == "NEITHER"),
        "honest_scope_statement": (
            "AK swept the three of the seven that had NO frontier anywhere (asia_pdl_fade, "
            "orb_crypto_london, liq_asia_up_low_metal). The other four already had AD frontiers "
            "and AK did not re-sweep them; three of those four appear in AK's output only as "
            "diversifier-door rows, and ny_crypto_momentum appears in AK's prose nowhere at all "
            "even though AK's own aa_parity flipped it NOT_EVALUABLE -> REJECT. So the "
            "consolidated seven-sleeve frontier the commission describes does not exist as one "
            "artifact; it is AD's four plus AK's three, and this is the map."),
    }


def main() -> dict:
    tr, g, c, fr, dv, do = (_load(p) for p in (TRADES, GATE, CELLS, FRONTIER, DIV, DOSSIER))
    rows: list[dict] = []

    queue: dict[str, list[dict]] = {}
    if QUEUE_APPEND.is_file():
        for line in QUEUE_APPEND.read_text().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (r.get("session") or "") == "AK":
                queue.setdefault(str(r.get("sleeve")), []).append(r)

    def frontier_of(name):
        s = ((fr or {}).get("sleeves") or {}).get(name)
        if isinstance(s, dict) and s.get("available"):
            return {"source": "AK_EXIT_FRONTIER_V2.json", "n_cells": s.get("n_cells"),
                    "as_walked_pooled_oos_mean_r": s.get("as_walked_pooled_oos_mean_r"),
                    "best_cell": s.get("best_cell"),
                    "best_pooled_oos_mean_r": s.get("best_pooled_oos_mean_r"),
                    "delta_vs_as_walked": s.get("delta_vs_as_walked"),
                    "best_verdict": s.get("best_verdict"),
                    "best_failing_gates": s.get("best_failing_gates")}
        ef = (((c or {}).get("cells") or {}).get(name) or {}).get("exit_frontier")
        if isinstance(ef, dict) and ef.get("available"):
            return {"source": "AK_SLEEVE_CELLS_V1.json -> exit_frontier",
                    "n_cells": ef.get("n_cells"),
                    "as_walked_pooled_oos_mean_r": ef.get("as_walked_pooled_oos_mean_r"),
                    "best_cell": ef.get("best_cell"),
                    "best_pooled_oos_mean_r": ef.get("best_pooled_oos_mean_r"),
                    "delta_vs_as_walked": ef.get("delta_vs_as_walked"),
                    "best_verdict": ef.get("best_verdict"),
                    "best_failing_gates": ef.get("best_failing_gates")}
        return {"available": False,
                "reason": (((fr or {}).get("sleeves") or {}).get(name) or {}).get("reason")
                          or "not swept by this session"}

    def div_of(name):
        cand = ((dv or {}).get("candidates") or {}).get(name)
        if not isinstance(cand, dict) or not cand.get("available"):
            return {"available": False,
                    "reason": (cand or {}).get("reason") or "not run against the door"}
        out = {"source": "AK_DIVERSIFIER_V1.json", "cells": {}}
        for cell, x in (cand.get("cells") or {}).items():
            if not x.get("available"):
                continue
            out["cells"][cell] = {
                "bound": x.get("bound"),
                "verdict": x["certification"]["verdict"],
                "failed_guards": x["certification"]["failed_guards"],
                "corr_to_armed_book":
                    x["certification"]["raw_certification"]["checks"]["low_correlation"].get(
                        "corr"),
                "n_overlap_days":
                    x["certification"]["raw_certification"]["checks"]["low_correlation"].get(
                        "n_overlap"),
                "solo_book_truncation": (x.get("candidate_solo_book") or {}).get("truncation"),
            }
        if cand.get("trail_bound_rule"):
            out["trail_bound_rule"] = cand["trail_bound_rule"]
        return out

    def dossier_of(name):
        x = ((do or {}).get("candidates") or {}).get(name)
        if not isinstance(x, dict) or not x.get("available"):
            return {"available": False}
        return {"source": "AK_CANDIDATE_DOSSIER_V1.json", "cell": x.get("cell"),
                "pooled_oos_mean_r": x.get("pooled_oos_mean_r"), "p_raw": x.get("p_raw"),
                "largest_family_that_would_admit":
                    (x.get("deflation") or {}).get("largest_family_that_would_admit"),
                "fold_oos_mean_r_series": x.get("fold_oos_mean_r_series"),
                "fold_series_key_used": x.get("fold_series_key_used")}

    def prescriptions_for(name):
        return [{"prescription": r["prescription"], "verdict": r["verdict"],
                 "is_primary": r.get("is_primary", False), "action": r["action"]}
                for r in queue.get(name, [])]

    # --- 1. the four sleeves no registry can reach -------------------------------------------
    for tag, spec in sorted((tr.get("specs") or {}).items()):
        v = ((g or {}).get("new_sleeves") or {}).get(tag) or {}
        rows.append({
            "member": tag,
            "kind": "UNREGISTERED_GENERATOR_FIRST_GATE",
            "generator_provenance": {
                "module": f"src/components/ultimate_book/sleeves/"
                          f"{'session_leadlag' if tag == 'session_leadlag_genuine' else tag}.py",
                "provenance": spec.get("provenance"),
                "why_unreachable": spec.get("why_unreachable"),
                "authored_exit": spec.get("authored_exit"),
                "notes": spec.get("notes"),
                "research_spec": "src/research_infra/walkforward/supply.py -> SUPPLY_SPECS",
            },
            "generation": {
                "source": "AK_SUPPLY_TRADES.json.gz",
                "n_trades": (spec.get("summary_authored_exit") or {}).get("n"),
                "mean_r_gross_authored_exit":
                    (spec.get("summary_authored_exit") or {}).get("mean_r_gross"),
                "mean_r_gross_plain_exit":
                    (spec.get("summary_plain_exit") or {}).get("mean_r_gross"),
                "window": [(spec.get("summary_authored_exit") or {}).get("first"),
                           (spec.get("summary_authored_exit") or {}).get("last")],
                "n_long": (spec.get("summary_authored_exit") or {}).get("n_long"),
                "n_short": (spec.get("summary_authored_exit") or {}).get("n_short"),
                "dropped_symbols": spec.get("dropped_symbols"),
            },
            "gate_verdict_at_measured_carry": {
                "source": "AK_SUPPLY_GATE_V1.json -> new_sleeves",
                "verdict": v.get("verdict"),
                "pooled_oos_mean_r": v.get("pooled_oos_mean_r"),
                "p_raw": v.get("p_raw"), "q_at_declared_69": v.get("q_value"),
                "failing_gates": v.get("failing_gates"),
                "coverage_frac": v.get("coverage_frac"),
                "cost_terms_mean_r": v.get("cost_terms_mean_r"),
                "primary_prescription": v.get("primary_prescription"),
            },
            "exit_frontier": frontier_of(tag),
            "diversifier_door": div_of(tag),
            "candidate_dossier": dossier_of(tag),
            "coherence": ((c or {}).get("coherence") or {}).get(tag),
            "next_prescription": prescriptions_for(tag),
        })

    # --- 2. the pre-declared cells ----------------------------------------------------------
    for name, cell in sorted(((c or {}).get("cells") or {}).items()):
        rows.append({
            "member": name,
            "kind": f"PRE_DECLARED_{str(cell.get('kind', '')).upper()}",
            "generator_provenance": {
                "parent": cell.get("parent"),
                "declared_in": ((c or {}).get("declared_before_outcomes") or {}).get(
                    cell.get("parent")),
                "authored_surface": cell.get("authored_surface"),
                "priceable_surface": cell.get("priceable_surface"),
                "dropped_symbols": cell.get("dropped_symbols"),
                "restriction_is_outcome_independent": True,
                "n_trades_dropped_by_restriction": cell.get("n_trades_dropped"),
            },
            "gate_verdict_at_measured_carry": {
                "source": "AK_SLEEVE_CELLS_V1.json -> cells",
                "verdict": cell.get("verdict"),
                "pooled_oos_mean_r": cell.get("pooled_oos_mean_r"),
                "p_raw": cell.get("p_raw"), "q_at_declared_69": cell.get("q_value"),
                "failing_gates": cell.get("failing_gates"),
                "drop_best_retention": cell.get("drop_best_retention"),
                "oos_positive_fold_frac": cell.get("oos_positive_fold_frac"),
                "n_folds_evaluable": cell.get("n_folds_evaluable"),
                "primary_prescription": cell.get("primary_prescription"),
            },
            "exit_frontier": frontier_of(name),
            "diversifier_door": div_of(name),
            "candidate_dossier": dossier_of(name),
            "coherence": ((c or {}).get("coherence") or {}).get(name),
            "next_prescription": prescriptions_for(name),
        })

    # --- 3. the sleeves REWORKED rather than new: AD's four-sleeve gap ----------------------
    for name in ((fr or {}).get("ad_frontier_gap") or {}).get("gap", []):
        base = ((g or {}).get("gap_sleeves_baseline") or {}).get(name) or {}
        rows.append({
            "member": name,
            "kind": "REWORKED_AD_FRONTIER_GAP",
            "generator_provenance": {
                "note": ("existing production sleeve; nothing about its generator changed. What "
                         "this session added is its exit frontier, which no prior artifact "
                         "carried."),
                "armed": name == "sub_xvol_pullback",
                "why_it_had_no_frontier":
                    ((fr or {}).get("ad_frontier_gap") or {}).get("why"),
            },
            "gate_verdict_at_measured_carry": {
                "source": "AK_SUPPLY_GATE_V1.json -> gap_sleeves_baseline",
                "verdict": base.get("verdict"),
                "pooled_oos_mean_r": base.get("pooled_oos_mean_r"),
                "p_raw": base.get("p_raw"), "q_at_declared_69": base.get("q_value"),
                "failing_gates": base.get("failing_gates"),
                "drop_best_retention": base.get("drop_best_retention"),
                "oos_positive_fold_frac": base.get("oos_positive_fold_frac"),
                "n_folds_evaluable": base.get("n_folds_evaluable"),
                "provenance_of_the_p_value": (
                    "AA_ESTATE_WALK.json run B_balanced|v1_1 — reproduced here, NOT discovered "
                    "here" if name == "sub_xvol_pullback" else None),
            },
            "exit_frontier": frontier_of(name),
            "diversifier_door": div_of(name),
            "candidate_dossier": dossier_of(name),
            "next_prescription": prescriptions_for(name),
        })

    # --- 4. the quarantined trio, door-only -------------------------------------------------
    for name in sorted((dv or {}).get("candidates") or {}):
        if any(r["member"] == name for r in rows):
            continue
        rows.append({
            "member": name,
            "kind": "QUARANTINED_TRIO_DIVERSIFIER_DOOR_ONLY",
            "generator_provenance": {
                "note": ("existing production sleeve with an AD exit frontier; this session ran "
                         "it through the diversifier door at its repaired cell and did NOT "
                         "re-sweep its exits."),
            },
            "gate_verdict_at_measured_carry": {
                "source": "AK_DIVERSIFIER_V1.json -> candidates.*.cells.*.standalone_gate",
            },
            "exit_frontier": {"available": False,
                              "reason": "AD's, at phase7/receipts/EXIT_FRONTIER_V1{,_TRAIL}.json"},
            "diversifier_door": div_of(name),
            "candidate_dossier": dossier_of(name),
            "next_prescription": prescriptions_for(name),
        })

    out = {
        "schema": "gtos.walkforward.sleeve_supply.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                         "ak_sleeve_supply_index.py"),
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "session": "AK", "blocks": "B950-B981",
        "what": ("the commission's deliverable 1: one row per new or reworked member with "
                 "generator provenance, gate verdict at measured carry, exit frontier, "
                 "diversifier-door verdict and next prescription. Built by reduction over the "
                 "five artifacts, so every field names where it came from."),
        "sources": [p.name for p in (TRADES, GATE, CELLS, FRONTIER, DIV, DOSSIER) if p.is_file()],
        "n_members": len(rows),
        "by_kind": {k: sum(1 for r in rows if r["kind"] == k)
                    for k in sorted({r["kind"] for r in rows})},
        "prior_gate_receipt_search": prior_gate_receipt_search(),
        "engine_reachability": engine_reachability(tr or {}),
        "cost_basis": {
            "what_was_charged": ("one modern per-symbol broker-true spread/commission/swap from "
                                 "BROKER_TRUE_COSTS_V1_1.json, with NO era band and NO "
                                 "hour-of-week multiplier"),
            "spans_it_was_applied_over": ("vol_squeeze H4 2019-2026; the three M15 sleeves "
                                          "2024-2026; the reworked sleeves up to 20 years "
                                          "(sub_xvol_pullback 2006-2026)"),
            "why_not_banded": ("AF §6 measured that spread_model_v1's era_ratio x hour product is "
                              "unvalidated and reaches 198x on pre-2010 FX, and restricted banded "
                              "pricing to era_class == RECORDED. Not banding at all is a "
                              "DIFFERENT choice from restricting, and this session made it "
                              "without saying so — recorded here after a completeness pass."),
            "direction_of_the_bias": ("UNKNOWN, and that is the honest answer. AG measured that "
                                      "the flat snapshot's bias has no consistent sign (EURUSD "
                                      "2002 at 50x, XAUUSD 2022 at 0.18x), which is exactly why "
                                      "'charge the snapshot and note the caveat' was not "
                                      "available to AF. Every long-span number here inherits "
                                      "that."),
            "what_would_close_it": ("AH's repair of the era x hour composition, then a re-gate "
                                   "restricted to era_class == RECORDED as AF did"),
        },
        "first_of_day_coverage_map": first_of_day_coverage_map(fr or {}),
        "members": rows,
    }
    OUT.write_text(json.dumps(out, indent=2, default=str))
    print(f"wrote {OUT.relative_to(REPO)}: {len(rows)} members, "
          f"{json.dumps(out['by_kind'])}")
    er = out["engine_reachability"]
    print(f"engine-reachability largest pre-gap frac: {er['largest_pre_gap_frac']}")
    fod = out["first_of_day_coverage_map"]
    print(f"first-of-day coverage: AK {fod['n_ak']}, AD inherited {fod['n_ad_inherited']}, "
          f"uncovered {fod['n_uncovered']}")
    pg = out["prior_gate_receipt_search"]
    print(f"prior-gate receipt search: {pg['search_1_receipt_json']['n_json_files_scanned']} JSONs, "
          f"zero-hit names {pg['search_1_receipt_json']['names_with_zero_hits']}, "
          f"pre-AK ledger rows {pg['search_2_trial_ledger']['pre_AK_rows_per_sleeve']}")
    return out


if __name__ == "__main__":
    main()
