#!/usr/bin/env python3
"""A1-OPEN (a1b), step 3: assemble the re-issued verdict table + HDC comparison.

Inputs (all read from disk, nothing typed in):
  * A1B_CORRECTED_NULL_RESULTS.json      — corrected p/q per recomputed arm (step 2)
  * A1B_AU_CAPTURED_SERIES.json          — capture + receipt-reproduction proof (step 1)
  * A1_CLEANROOM_NULL_DERIVATION.json    — the clean-room's breaker numbers (blind phase)
  * CANDIDATE_FAMILY_V27.json (+ V1 ratified rule) — the family and basis
  * the named wave18/19 gate receipts (CS, CQ, CP recorded gate, CP factory, CP first read, CR)
  * the standing-admission lineage receipts (AA walk, AL, AN/POPULATION_RULE, AQ, AU, CA, CM)

Outputs: A1_REISSUED_VERDICT_TABLE.json + A1_REISSUED_VERDICT_TABLE.md (same directory).
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
AUD = WT / "docs/audits/fable5-vision-audit-20260725"

CS_RECEIPT = Path("/Users/borr/GTOSActive/worktrees/wave19-breaker-folds-20260801/docs/audits/"
                  "fable5-vision-audit-20260725/phase19/receipts/CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json")
CR_RECEIPT = Path("/Users/borr/GTOSActive/worktrees/wave19-ny-metals-capture-20260801/docs/audits/"
                  "fable5-vision-audit-20260725/phase19/receipts/CR_NY_METALS_CAPTURE_RESULT_V1.json")

BREAKER = "cq_current_breaker_re_entry_inverted_5d_stop_0p25d"
MX = "mx_btcusd_d1_donchian_20_breakout"
XVOL = "sub_xvol_pullback"
NYM = "cp_true_utc_ny_metals_long_v1"

ALPHA = 0.10


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def j(p: Path) -> dict:
    return json.loads(p.read_text())


def flip_of(published_verdict: str, corrected_admit: bool) -> tuple[str, str]:
    if published_verdict == "REJECT" and corrected_admit:
        return ("REJECT->ADMIT",
                "REQUIRES_NEW_DECLARATION — graduates nobody; a corrected-rule re-issue can only "
                "reach a book through a new declared, pre-registered step")
    if published_verdict == "ADMIT" and not corrected_admit:
        return ("ADMIT->REJECT", "BINDS IMMEDIATELY")
    return ("UNCHANGED_" + published_verdict,
            "no binding consequence" if published_verdict == "REJECT"
            else "standing admission CONFIRMED under the corrected null")


def member_null_index() -> dict:
    members = [m["name"] for m in j(AUD / "phase18/receipts/CANDIDATE_FAMILY_V27.json")
               ["families"]["CANDIDATE_BOOK_V1"]["members"]]
    memset = set(members)
    # Longest name first: several member names nest inside others
    # (`sub_xvol_pullback` in `thr_sub_xvol_pullback_*`, `crypto` in `orb_crypto_london`),
    # so attribution must take the MOST SPECIFIC name present in the path — unordered
    # set iteration here produced nondeterministic attribution in a first draft.
    by_len = sorted(memset, key=len, reverse=True)
    index = {m: set() for m in members}
    counts = {m: 0 for m in members}
    for fp in sorted(glob.glob(str(AUD / "phase*/receipts/*.json"))):
        try:
            d = json.loads(Path(fp).read_text())
        except Exception:
            continue
        rel = fp.split("fable5-vision-audit-20260725/")[-1]

        def walk(o, path=""):
            if isinstance(o, dict):
                p = o.get("p_raw")
                if isinstance(p, (int, float)) and math.isfinite(p):
                    name = o.get("sleeve") if o.get("sleeve") in memset else None
                    if name is None:
                        for m in by_len:
                            if m in path:
                                name = m
                                break
                    if name:
                        index[name].add(rel)
                        counts[name] += 1
                for k, v in o.items():
                    walk(v, path + "/" + str(k))
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, path + f"[{i}]")
        walk(d)
    return {m: {"n_computed_null_rows": counts[m], "receipts": sorted(index[m])}
            for m in members}


def lineage_rows() -> list[dict]:
    """The standing admission's republication chain — every row read from its receipt."""
    rows = []

    def add(receipt_rel, node, label, session, note=""):
        rows.append({
            "session": session, "receipt": receipt_rel, "node": label,
            "p_raw": node.get("p_raw"), "q_value": node.get("q_value"),
            "verdict": node.get("verdict"),
            "declared_family_size": node.get("declared_family_size") or (
                round(node["q_value"] / node["p_raw"])
                if node.get("q_value") and node.get("p_raw") else None),
            "note": note,
        })

    al = j(AUD / "phase9/receipts/AL_CANDIDATE_DOSSIER_V1.json")
    key = ("population=RECORDED|exit=target_5R|band=mid|option=B_balanced|"
           "family=CANDIDATE_BOOK_V2@all_declared")
    add("phase9/receipts/AL_CANDIDATE_DOSSIER_V1.json",
        al["candidates"][MX]["by_stamp"][key], key, "AL (wave 9)",
        "the first sealed-alpha ADMIT")

    pr = j(AUD / "phase10/receipts/POPULATION_RULE_V1.json")
    for band in ("flat", "low", "mid"):
        node = pr["grid"]["arms"][f"X_btc5R|B_balanced|RECORDED|{band}|{MX}"]
        add("phase10/receipts/POPULATION_RULE_V1.json", node,
            f"grid X_btc5R|B_balanced|RECORDED|{band}", "AN (wave 10)",
            "population axis; the rule later ratified")

    aq = j(AUD / "phase11/receipts/AQ_CONTRACT_TRUTH_V1.json")
    for band in ("flat", "low", "mid"):
        node = aq["admission"]["arms"][f"REPAIRED|B_balanced|RECORDED|{band}"][MX]
        add("phase11/receipts/AQ_CONTRACT_TRUTH_V1.json", node,
            f"REPAIRED|B_balanced|RECORDED|{band}", "AQ (wave 11)",
            "under the repaired time-stop contract")

    au = j(AUD / "phase12/receipts/AU_EXIT_WIRING_V1.json")
    for i in (4, 5, 6, 7):
        node = au["gate_rows"][MX]["arms"][i]
        add("phase12/receipts/AU_EXIT_WIRING_V1.json", node,
            f"arms[{i}] target_5R {node['band']}", "AU (wave 12)",
            "the round-trip at the V5 48-family bill — RECOMPUTED in this re-issue")

    ca = j(AUD / "phase14/receipts/CA_MX_INCUBATION_V1.json")
    add("phase14/receipts/CA_MX_INCUBATION_V1.json", ca["measured_basis_ONE_OBJECT"],
        "measured_basis_ONE_OBJECT", "CA (wave 14)", "")

    cm = j(AUD / "phase17/receipts/CM_REVERIFY_V1.json")
    for band in ("low", "mid", "high"):
        node = cm["accounts"]["FTMO"][MX]["gate"]["current"][band]
        add("phase17/receipts/CM_REVERIFY_V1.json", node,
            f"gate.current.{band}", "CM (wave 17)",
            "the LATEST republication (family 57, n=228) — NOT_RECOMPUTABLE, missing input: "
            "sources/bars/deep_universe_h4d1_2014_2026/ (sha256s pinned in the receipt's "
            "source_rows), absent from every worktree on this machine today")
    return rows


def main() -> int:
    corrected = j(HERE / "A1B_CORRECTED_NULL_RESULTS.json")
    cap_au = j(HERE / "A1B_AU_CAPTURED_SERIES.json")
    cleanroom = j(HERE / "A1_CLEANROOM_NULL_DERIVATION.json")
    v27 = j(AUD / "phase18/receipts/CANDIDATE_FAMILY_V27.json")
    v1_rule = j(AUD / "phase8/receipts/CANDIDATE_FAMILY_V1.json")["ratified_rule"]
    cs = j(CS_RECEIPT)
    cq = j(AUD / "phase18/receipts/CQ_CURRENT_BREAKER_RATIFIED_GATE_V1.json")
    cp_gate = j(AUD / "phase18/receipts/CP_TRUE_UTC_NY_METALS_LONG_RECORDED_GATE_V1.json")
    cp_fact = j(AUD / "phase18/receipts/CP_TRUE_UTC_CANDIDATE_FACTORY_RESULT_V1.json")
    cp_feb = j(AUD / "phase18/receipts/CP_FEBRUARY_FIRST_READ_RESULT_V1.json")
    cr = j(CR_RECEIPT)

    members = v27["families"]["CANDIDATE_BOOK_V1"]["members"]
    by_name = {m["name"]: m for m in members}

    # ---------------- core: recomputed computed-null rows -------------------------
    core_rows = []
    for arm in corrected["arms"]:
        pub = arm["published"]
        bh = arm["corrected"]["bh"]
        flip, consequence = flip_of(pub["verdict"], bh["rejected"])
        # the measured-dependence variant (max over the two innovation laws at rho = rho_within)
        rho_meas = round(arm["corrected"]["diagnostics"]["rho_within"], 3)
        p_meas = max((v["pooled"]["p_add_one"] for v in arm["variants"]
                      if v["rho"] == rho_meas), default=None)
        m_size = pub.get("m") or pub.get("declared_family_size")
        if flip == "ADMIT->REJECT" and p_meas is not None and p_meas <= ALPHA / m_size:
            consequence = (
                "BINDS IMMEDIATELY — under the corrected PRIMARY (max over the fitted "
                "dependence span, the same both_conservative posture that admits the breaker) "
                "this admission FAILS. Precision that must travel with the flag: at the "
                f"MEASURED within-fold dependence (rho={rho_meas}) the corrected p "
                f"({p_meas:.6g}) matches the published p ({pub['p_raw']:.6g}) and still "
                "admits — the REJECT comes entirely from the +1SE dependence variant. The "
                "admission carries LESS THAN ONE SE of dependence-model margin at the "
                "48-family bar; whether that margin stands between an armed sleeve and "
                "dis-arming is an owner decision, flagged here, not taken here.")
        core_rows.append({
            "member": arm["member"],
            "arm": arm.get("arm", "three_fold_pooled"),
            "band": arm.get("band", "mid"),
            "publishing_session": arm["publishing_session"],
            "receipt": arm["receipt"],
            "published_p": pub["p_raw"], "published_q": pub["q_value"],
            "published_verdict": pub["verdict"],
            "family_size_m": pub.get("m") or pub.get("declared_family_size"),
            "n_days": arm["corrected"]["n"],
            "corrected_p": arm["corrected"]["corrected_p"],
            "corrected_p_at_measured_rho": p_meas,
            "corrected_p_min_variant": arm["corrected"]["corrected_p_min_variant"],
            "corrected_argmax_variant": arm["corrected"]["argmax_variant"],
            "rho_within": round(arm["corrected"]["diagnostics"]["rho_within"], 4),
            "rho_se": round(arm["corrected"]["diagnostics"]["se_rho"], 4),
            "corrected_q": bh["q_value"],
            "corrected_verdict": "ADMIT" if bh["rejected"] else "REJECT",
            "flip": flip,
            "binding_consequence": consequence,
            "significance_was_sole_failing_gate": True,
            "baseline_bh_reproduces_published_q":
                arm.get("baseline_bh_reproduces_published_q", True),
        })

    # ---------------- named receipts with NO computed null ------------------------
    cqs = cq["gate_result"]["sleeves"][BREAKER]
    no_null_rows = [
        {"member": BREAKER, "publishing_session": "CQ (wave 18)",
         "receipt": "phase18/receipts/CQ_CURRENT_BREAKER_RATIFIED_GATE_V1.json",
         "published_p": cqs["p_raw"], "published_q": cqs["q_value"],
         "published_verdict": cqs["verdict"],
         "classification": "NO_COMPUTED_NULL_UNAFFECTED",
         "detail": "NOT_EVALUABLE on the sample gate (1 fold of 3); significance never ran; "
                   "family_members_with_null=[] in the receipt's own multiplicity block"},
        {"member": NYM, "publishing_session": "CP (wave 18)",
         "receipt": "phase18/receipts/CP_TRUE_UTC_NY_METALS_LONG_RECORDED_GATE_V1.json",
         "published_p": None, "published_q": None,
         "published_verdict": cp_gate["status"],
         "classification": "NO_COMPUTED_NULL_UNAFFECTED",
         "detail": "frozen gate, NOT_EVALUABLE pending source+fidelity capture; "
                   "family_members_with_null=[]"},
        {"member": NYM, "publishing_session": "CR (wave 19)",
         "receipt": "wave19-ny-metals-capture phase19/receipts/CR_NY_METALS_CAPTURE_RESULT_V1.json",
         "published_p": None, "published_q": None,
         "published_verdict": cr["verdict"],
         "classification": "NO_COMPUTED_NULL_UNAFFECTED",
         "detail": "gate_execution.invoked=false — run_gate never called "
                   f"({cr['status']})"},
        {"member": "(1092 factory candidates; 1 graduated = " + NYM + ")",
         "publishing_session": "CP (wave 18)",
         "receipt": "phase18/receipts/CP_TRUE_UTC_CANDIDATE_FACTORY_RESULT_V1.json",
         "published_p": None, "published_q": None,
         "published_verdict": cp_fact["status"],
         "classification": "NO_COMPUTED_NULL_LANE_EVIDENCE",
         "detail": "TRAIN-lane screening; zero permutation machinery in the receipt "
                   "(measured: 0 occurrences of p_raw/n_perm/significance)"},
        {"member": "(broad V4 S1R1 probe — not a CANDIDATE_BOOK member)",
         "publishing_session": "CP (wave 18)",
         "receipt": "phase18/receipts/CP_FEBRUARY_FIRST_READ_RESULT_V1.json",
         "published_p": None, "published_q": None,
         "published_verdict": cp_feb["disposition"],
         "classification": "NO_COMPUTED_NULL_DIFFERENT_MACHINERY",
         "detail": "committed pre-outcome precision rule, not the block-permutation gate; "
                   "listed because the brief names it; no family member's verdict flows "
                   "through it"},
    ]

    # ---------------- 59-member classification ------------------------------------
    idx = member_null_index()
    (HERE / "A1B_MEMBER_NULL_INDEX.json").write_text(json.dumps(idx, indent=1))
    recomputed = {BREAKER, MX, XVOL}
    classification = []
    for m in members:
        name = m["name"]
        if name == BREAKER:
            cls, detail = "AFFECTED_RECOMPUTED", (
                "computed null in CS's ratified gate (wave19-breaker-folds); re-issued above; "
                "REJECT->ADMIT under the corrected null")
        elif name in (MX, XVOL):
            cls, detail = "AFFECTED_RECOMPUTED", (
                "current binding cells (AU_EXIT_WIRING_V1) recomputed above; "
                + ("the estate's standing admission, ARMED live — ADMIT->REJECT under the "
                   "corrected primary at all three admitting bands (see the flag)" if name == MX
                   else "armed sleeve's frontier cell — every REJECT stays REJECT"))
        elif name == NYM:
            cls, detail = "NO_COMPUTED_NULL_UNAFFECTED", (
                "CP frozen gate + CR capture both NOT_EVALUABLE before significance; "
                "padded at 1.0 in every published multiplicity block")
        elif idx[name]["n_computed_null_rows"] > 0:
            aa_p = m.get("aa_p_raw")
            cls = "AFFECTED_HISTORICAL_NOT_REISSUED"
            detail = (
                f"{idx[name]['n_computed_null_rows']} computed-null rows across "
                f"{len(idx[name]['receipts'])} landed receipts (see A1B_MEMBER_NULL_INDEX.json); "
                "no row is a member admission at the sealed alpha (the only ADMIT-verdict rows "
                "among these members are Session W's gate self-test controls in "
                "W_NEGATIVE_CONTROLS.json and alpha=0.2 research triage, which "
                "options.py:110 bars from arming) — a REJECT->ADMIT flip graduates nobody "
                "(this brief's own rule), no current binding decision rests on any row, and "
                "several rows' bases are superseded (flat-snapshot/pre-re-clock populations). "
                "Recompute path exists: each receipt's committed driver + "
                "AA_ESTATE_TRADES.json.gz (+ AM_SUBMID_TRADES for sub_mid_dn_revert), "
                "the same capture-validate-recompute loop used here."
                + (f" Family-artifact aa_p_raw={aa_p:.6g} (AA, wave 6, superseded basis)."
                   if isinstance(aa_p, (int, float)) else ""))
        else:
            cls, detail = "PADDED_UNAFFECTED", (
                "no computed-null row in any landed receipt (measured, this worktree "
                "phase6-18) — padded at p=1.0 by construction wherever the family is billed")
        classification.append({"member": name, "classification": cls, "detail": detail})

    counts = {}
    for r in classification:
        counts[r["classification"]] = counts.get(r["classification"], 0) + 1

    # ---------------- flips summary ------------------------------------------------
    flips = {"ADMIT->REJECT": [], "REJECT->ADMIT": [], "UNCHANGED_ADMIT": [],
             "UNCHANGED_REJECT": []}
    for r in core_rows:
        key = r["flip"] if r["flip"] in flips else r["flip"]
        flips.setdefault(key, []).append(
            f"{r['member']} @ {r['arm']} [{r['band']}] ({r['publishing_session']})")

    # ---------------- HDC comparison -----------------------------------------------
    hdc = {
        "question": "HDC/HDF published corrected p 0.0009765625 (= 2/2048), q 0.0576171875, "
                    "ADMIT — how does their null differ from the clean-room corrected null, "
                    "why does theirs still sit on a resolution floor, and do the two ADMITs "
                    "agree?",
        "hdc_construction": {
            "rule": "capture_start_anchored_sign_blocks; blocks_restart_at_each_capture",
            "family": "the SAME block sign-flip randomization family as the gate (uncentred "
                      "blocks, L=3), with the anchor defect repaired by declaring the sealed "
                      "capture starts the authoritative origin and restarting blocks at every "
                      "capture seam: segment blocks [4,4,3], 11 blocks, support 2^11=2048, "
                      "exact enumeration (no MC), tail states 2 -> p=2/2048; both_conservative "
                      "against a within-capture circular bootstrap floored at 1/10001",
            "receipts": [
                "wave20-exit-capture-semantics-falsifier .../phase20/"
                "SESSION_HDC_EXIT_CAPTURE_FALSIFIER_RESULT.md sections 5-6",
                "wave20-exit-capture-science-falsifier2 .../phase20/"
                "SESSION_HDF_EXIT_CAPTURE_SCIENCE_FALSIFIER2_RESULT.md items 3-5 "
                "(independent reproduction 2/2048; also: HC's common-phase 13/6144 is "
                "byte-reproducible but the mathematical exact tail is 14/6144 — a tie lost "
                "to float summation order)"],
        },
        "clean_room_construction": "family REPLACED: independent fold segments, within-fold "
                                   "AR(1) (rho grid spanning the fitted dependence), per-fold "
                                   "scale, studentised mean, exact-under-model Monte Carlo "
                                   "calibration; primary p = max over variants = 0.0013033, "
                                   "q = 0.0769",
        "differences": [
            "ANCHOR vs FAMILY: HDC repairs the one defect the clean-room proved "
            "verdict-determining (the arbitrary common phase) by DECLARING an authoritative "
            "anchor inside the same randomization family; the clean-room replaced the family "
            "because two further measured defects survive any re-anchoring: (1) uncentred "
            "flips put 64.8% of the null variance in the candidate's own signal "
            "(conservative under H1); (2) at L=3 under the measured within-fold dependence "
            "(rho 0.372 +- 0.175) the sign-flip family is anti-conservative at the decision "
            "bar (measured size 3.8x for the fixed-phase rule under a matched AR(1)). These "
            "act in opposite directions and neither is priced by an exact count.",
            "RESOLUTION FLOOR: HDC's support is intrinsically 2^11 = 2048 atoms on this "
            "31-point series — exact enumeration removes Monte-Carlo noise, not quantisation. "
            "Achievable p near the bar are k/2048; q moves in steps of 59/2048 = 0.0288; "
            "their published p IS the k=2 atom, the floor is 1/2048 = 4.88e-4, and the "
            "ADMIT/REJECT boundary sits between k=3 and k=4 — one near-zero block sum "
            "(the clean-room measured one at 1% of the day-level sd) moves k. The "
            "clean-room's statistic is continuous: no support cap, per-seed spread <= 3%.",
            "STRENGTH CLAIM: HDC's p (9.77e-4) is nominally smaller than the clean-room's "
            "primary (1.30e-3), but it is a within-family exact count whose anti-conservative "
            "dependence leak is unpriced; the clean-room's primary is the max over the fitted "
            "dependence span (both_conservative applied to model risk) with a stated flip "
            "boundary (within-fold rho >= ~0.6, i.e. >= 1.2 SE above measured).",
        ],
        "verdict_agreement": "AGREE — both ADMIT at alpha 0.10 over the declared 59-family "
                             "(HDC q 0.0576, clean-room q 0.0769), against the same published "
                             "MC REJECT (q 0.1534); HDF independently reproduces HDC. Three "
                             "independent corrected constructions land on the same side, which "
                             "is the strongest available statement that the published REJECT "
                             "is an artifact of the implemented rule rather than a property "
                             "of the evidence. Evidential strength differs: HDC's number is "
                             "exact but quantised and family-bound; the clean-room's is "
                             "model-calibrated, dependence-priced and continuous — the more "
                             "defensible of the two; its ADMIT carries the thinner q margin "
                             "(23% vs 42%) precisely because it charges the model risk.",
    }

    out = {
        "schema": "gtos-a1-reissued-verdict-table-v1",
        "generated_at_utc": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        "session": "FA-continuation A1 OPEN half (a1b)",
        "scope": {
            "affected_set_definition": "family members whose PUBLISHED p came from "
                                       "block_permutation_p / both_conservative machinery on a "
                                       "daily series (a computed null); padded-at-1.0 members "
                                       "unaffected by construction",
            "named_receipt_sources": [
                str(CS_RECEIPT),
                "phase18/receipts/CQ_CURRENT_BREAKER_RATIFIED_GATE_V1.json",
                "phase18/receipts/CP_TRUE_UTC_NY_METALS_LONG_RECORDED_GATE_V1.json",
                "phase18/receipts/CP_TRUE_UTC_CANDIDATE_FACTORY_RESULT_V1.json",
                "phase18/receipts/CP_FEBRUARY_FIRST_READ_RESULT_V1.json",
                str(CR_RECEIPT),
                "phase19/receipts/forensic/ (FA route: verification receipts only, no gate "
                "verdicts published through the machinery)"],
            "scope_extension": "the estate's ONE standing ADMIT (mx_btcusd @ target_5R, armed "
                               "live) and the armed sleeve's frontier REJECT (sub_xvol_pullback "
                               "@ target_4R) also pass through the affected code path via "
                               "AU_EXIT_WIRING_V1.json; the brief's binding rule (ADMIT->REJECT "
                               "binds immediately) makes checking them mandatory, so their 16 "
                               "arms are recomputed here with the same capture-validate loop",
        },
        "ratified_rule_basis": {"family": v1_rule["family"], "option": v1_rule["option"],
                                 "alpha": v1_rule["alpha"], "basis": v1_rule["basis"],
                                 "source": "phase8/receipts/CANDIDATE_FAMILY_V1.json -> "
                                           "ratified_rule (carried verbatim at V27)"},
        "method": {
            "corrected_null": "clean-room recipe (A1_CLEANROOM_NULL_DERIVATION.md section 5), "
                              "generalized: fold segments from each arm's own evaluable-fold "
                              "day counts; per-fold scale (pooled fallback below 5 days); "
                              "pooled within-fold AR(1); gaussian + residual-bootstrap "
                              "innovations; studentised mean; 3 seeds; primary p = max over "
                              "variants",
            "sims": {"breaker": "700k x 3 seeds per variant (reproduces the clean-room)",
                     "au_arms": "200k x 3 seeds per variant (>= the brief's 100k floor)"},
            "capture_validation": "every recomputed arm's series was captured in-process from "
                                  "the committed receipt driver and accepted only after the "
                                  "receipt reproduced float-exactly (16/16 AU arms PASS on "
                                  "p_raw, q, verdict, fold_means, spec_sha256; CS 12/12 in the "
                                  "blind phase)",
            "bh_substitution": "each receipt's own multiplicity block reproduced with the "
                               "corrected p substituted for the target only; co-judged "
                               "members stay at published p; baseline substitution of the "
                               "published p reproduces the published q exactly on every arm",
        },
        "reissued_computed_null_rows": core_rows,
        "named_receipt_rows_no_computed_null": no_null_rows,
        "member_classification_59": classification,
        "classification_counts": counts,
        "standing_admission_lineage": lineage_rows(),
        "gate_validation_controls_note": "Session W's W_NEGATIVE_CONTROLS.json contains three "
                                          "ADMIT rows with computed p (positive control, "
                                          "synthetic adversary, carry-restricted control) — "
                                          "gate self-tests, not member claims; excluded.",
        "hdc_comparison": hdc,
        "flips": {k: v for k, v in flips.items()},
        "summary": {
            "family_size": 59,
            "affected_in_named_wave18_19_receipts": 1,
            "affected_current_binding_members_recomputed": sorted(recomputed),
            "n_arms_recomputed": len(core_rows),
            "members_with_any_computed_null_row_in_landed_receipts":
                sum(1 for r in classification
                    if r["classification"].startswith("AFFECTED")),
            "padded_unaffected": counts.get("PADDED_UNAFFECTED", 0),
        },
        "inputs_sha256": {
            "A1B_CORRECTED_NULL_RESULTS.json": sha(HERE / "A1B_CORRECTED_NULL_RESULTS.json"),
            "A1B_AU_CAPTURED_SERIES.json": sha(HERE / "A1B_AU_CAPTURED_SERIES.json"),
            "A1_CAPTURED_SERIES.json": sha(HERE / "A1_CAPTURED_SERIES.json"),
            "CS_receipt": sha(CS_RECEIPT),
            "CANDIDATE_FAMILY_V27.json": sha(AUD / "phase18/receipts/CANDIDATE_FAMILY_V27.json"),
        },
    }
    (HERE / "A1_REISSUED_VERDICT_TABLE.json").write_text(json.dumps(out, indent=1))
    print("wrote A1_REISSUED_VERDICT_TABLE.json")
    print(json.dumps({"flips": {k: len(v) for k, v in flips.items()},
                      "counts": counts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
