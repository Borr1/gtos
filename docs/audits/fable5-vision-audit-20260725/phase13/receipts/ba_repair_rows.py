"""Session BA's repair-queue rows: the weekend policy's own findings, and its own defect.

    python3 docs/audits/fable5-vision-audit-20260725/phase13/receipts/ba_repair_rows.py

Writes `REPAIR_QUEUE_BA.json` (authoritative for BA's rows) and appends the same rows to the
shared append-only sidecar `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl`. A landed row in the
sidecar is never rewritten (AP §7.2); a correction is an errata row.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
ART = HERE / "BA_WEEKEND_V1.json"
OUT = HERE / "REPAIR_QUEUE_BA.json"
SIDECAR = AUD / "phase6/receipts/REPAIR_QUEUE_APPEND.jsonl"

SESSION, BLOCKS = "BA", "B1900-B1949"


def rows(doc: dict) -> list[dict]:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    cen, ident, book = doc["census"], doc["identity"], doc["book"]
    ec = ident["early_close_weeks"]
    oos = book["arms"]

    def cell(pop_arm: str, acct: str = "redacted_account") -> dict:
        return oos[pop_arm]["accounts"][acct]["rules"]["P2_BOTH_PHASES"]

    def row(**kw) -> dict:
        return {"session": SESSION, "appended_utc": now, **kw}

    out = [
        row(prescription="WEEKEND_HOLDING_POLICY_BUILT_AND_PRICED",
            sleeve="crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert",
            component="run_book.py --weekend-flat / weekend_policy.py",
            verdict="BUILT_DEFAULT_OFF", is_primary=True, gate=None,
            margin=-0.7753,
            action=("redacted_account prohibits weekend holding on the FUNDED account and permits it in "
                    "the Challenge, so this blocker fires the moment the armed redacted_account account "
                    "PASSES. The mechanism is `run_book.py --weekend-flat <sleeves>` plus three "
                    "dials, all default-off, no config byte (both live config files are hashed into "
                    "an activation token digest). Priced at the ratified rule on the armed four: "
                    "-0.7753 R/day, 42.8 % of their +1.8098, and at redacted_account's measured 2-step "
                    "rules 0.7345 -> 0.6282 p_pass with median days-to-pass 494 -> 689. "
                    "Flattening beats dropping at THREE of the four cost bands for every sleeve; "
                    "the exception is `crypto` at the HIGH band, where the calendar flatten takes "
                    "it to -0.0382 (+0.1815 under the market-close reading) and its funded-book "
                    "membership becomes a real question. The DELTA is band-invariant and the "
                    "LEVEL is not, and a drop-or-keep decision reads the level. Arming is "
                    "Borhen's; the measurement is not."),
            evidence={"artifact": str(ART.relative_to(REPO)),
                      "owner_package": "phase13/BA_WEEKEND_POLICY_OWNER_PACKAGE.md",
                      "r_per_day_base": 1.8098, "r_per_day_flat": 1.0345,
                      "p_pass_base": cell("RECORDED_oos_only/as_walked")["p_pass"],
                      "p_pass_flat": cell("RECORDED_oos_only/flat_calendar_m0")["p_pass"],
                      "bill_share": {"sub_xvol_pullback": 0.663, "crypto": 0.283,
                                     "energy_agri": 0.031, "sub_mid_dn_revert": 0.023},
                      "post_flatten_level_by_band": {
                          "bands": ["flat_37_day_snapshot", "low", "mid", "high"],
                          "crypto": [0.0737, 0.0470, 0.0419, -0.0382],
                          "energy_agri": [0.3453, 0.3949, 0.3823, 0.3611],
                          "sub_xvol_pullback": [0.4897, 0.5134, 0.5076, 0.4990],
                          "sub_mid_dn_revert": [0.2128, 0.1295, 0.1026, 0.0611],
                          "book_sum": [1.1214, 1.0847, 1.0345, 0.8830]}}),
        row(prescription="OWNER_QUESTION__DOES_THE_WEEKEND_RULE_REACH_A_24_7_INSTRUMENT",
            sleeve="crypto", component="FIRM_RULES_V1.json firms.redacted_account.weekend_holding",
            verdict="OPEN_OWNER_DECISION", is_primary=True, gate=None, margin=0.2197,
            action=("BTCUSD gapped the weekend in only 43.8 % of its weeks and quoted straight "
                    "through the other 56.2 %, so 'the weekend' is a property of (symbol, week) "
                    "and not of the calendar. Under the conservative CALENDAR reading 45.9 % of "
                    "`crypto` trades are affected and the sleeve costs 0.2192 R/day; under the "
                    "market-close reading 15.5 % are affected and it costs 0.0005. That is 28.3 % "
                    "of the whole compliance bill, +11.7 pp of p_pass and 78 fewer days to a "
                    "payout, and it is decided by ONE support ticket. Default to the conservative "
                    "reading until the answer arrives -- `--weekend-exempt` exists for the answer, "
                    "not for an inference."),
            evidence={"btcusd_weekend_gap_frac_of_weeks": 0.43775,
                      "frac_crossing_calendar": cen["sleeves"]["crypto"]["frac_crossing_calendar"],
                      "frac_crossing_grid": cen["sleeves"]["crypto"]["frac_crossing_grid"],
                      "p_pass_calendar": cell("RECORDED_oos_only/flat_calendar_m0")["p_pass"],
                      "p_pass_grid": cell("RECORDED_oos_only/flat_grid_m0")["p_pass"]}),
        row(prescription="HOLIDAY_FRIDAY_DEFEATS_A_SATURDAY_ANCHORED_DEADLINE",
            sleeve="ALL_GOVERNED", component="weekend_policy.next_weekend_boundary_utc",
            verdict="MITIGATED_NOT_CLOSED", is_primary=True, gate=None, margin=None,
            action=("Found by this session's own identity check, and it is a BREACH class rather "
                    "than a cost class: when Friday is a market holiday the week's last close is "
                    "Friday 00:00 broker, and a Saturday-anchored deadline aims 20 h into a market "
                    "that already shut. 7 of the archive's 271 weekend-flat exits (2.6 %) are that "
                    "shape, all Christmas or New Year. Two mitigations ship: "
                    "`--weekend-early-close` (a 13-date derived list closes the residual to ZERO "
                    "over all 271) and `--weekend-flatten-before-hours 24` (automatic, costs an "
                    "extra 0.1167 R/day). NEITHER IS THE DURABLE FIX: bar absence cannot "
                    "distinguish a market holiday from an archive coverage gap, and the shipped "
                    "list is HISTORICAL with no future date in it."),
            evidence={"n_mismatched": ident["n_mismatched_total"],
                      "n_weekend_flat_exits": ident["n_weekend_flat_exits_total"],
                      "residual_with_derived_list":
                          ident["with_derived_list"]["n_live_deadline_LATER_than_the_replay_exit"],
                      "derived_dates": ec["dates"],
                      "n_candidate_dates_before_filters": ec["n_candidate_dates"]}),
        row(prescription="CAPTURE_THE_BROKER_TRADING_SESSION_TABLE",
            sleeve="ALL", component="src/mt5/mt5_real.py + broker_net_cost_engine.py:44-45",
            verdict="OPEN", is_primary=False, gate=None, margin=None,
            action=("The durable fix for the row above, and it retires the operator's holiday list "
                    "permanently. `broker_net_cost_engine.py:44-45` already names "
                    "`symbol_info_session_trade` / `symbol_info_session_quote` as source authority "
                    "it does not have, and `src/mt5/mt5_real.py` exposes no sessions API at all. "
                    "With the table the weekly close is read from the broker instead of inferred "
                    "from bar absence, and the same capture would also let the session-anchored "
                    "sleeves stop inferring their own session boundaries."),
            evidence={"named_absent_at": "src/components/broker_net_cost_engine.py:44-45"}),
        row(prescription="CARRY_BROKER_CLOCK_TO_THE_HOST_BEFORE_ARMING",
            sleeve="ALL_GOVERNED", component="src/utils/broker_clock.py",
            verdict="OPEN_CARRY", is_primary=True, gate=None, margin=None,
            action=("`src/utils/broker_clock.py` was ABSENT from the live host as of the "
                    "2026-07-26 VPS export (`packet_economics.py:41-49` is optional-by-"
                    "construction for exactly that reason), and it is this policy's ONLY clock. "
                    "`run_book.py` therefore returns 5 and notifies CRITICAL rather than starting "
                    "with a guard that cannot locate the weekend -- a compliance guard degrading "
                    "to 'nothing is due' is a funded account holding through one while every "
                    "indicator reads normal. The carry is a precondition of arming, not of "
                    "landing: with the policy off, nothing reads the module."),
            evidence={"absent_on_host_at": "vps-export-20260725, 20_src/utils/",
                      "refusal": "run_book.py weekend_policy_preflight -> return 5"}),
        row(prescription="THE_ENTRY_EMBARGO_IS_REFUTED_AS_A_REPAIR",
            sleeve="crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert",
            component="phase13/receipts/BA_WEEKEND_V1.json embargo",
            verdict="REFUTED", is_primary=False, gate=None, margin=-0.4147,
            action=("The commission asked for the entry embargo to be priced and it does not pay. "
                    "On three of four sleeves it makes the flatten WORSE; where the combination "
                    "looks better (48 h, -0.4147 R/day against the flatten's -0.7753) it gets "
                    "there by halving the number of book days, so the daily mean is restored and "
                    "the median calendar days to a payout go 689 -> 832 with a WORSE %/month "
                    "(0.229 -> 0.236 against the do-nothing 0.408). p_pass is blind to speed, "
                    "which is exactly how this option reads free. Default 0, recommend 0. The "
                    "`embargo_only` arms are published as information and are NOT legal: an "
                    "embargo without a flatten does not make the account compliant."),
            evidence={"r_per_day_flat_only": 1.0345, "r_per_day_flat_plus_48h": 1.3950,
                      "days_flat_only": cell("RECORDED_oos_only/flat_calendar_m0")[
                          "median_calendar_days_to_pass"],
                      "days_flat_plus_48h": cell(
                          "RECORDED_oos_only/flat_calendar_m0_embargo_48h")[
                          "median_calendar_days_to_pass"]}),
        row(prescription="A_COST_DELTA_IS_NOT_A_BAND_QUANTITY",
            sleeve="ALL", component="src/research_infra/walkforward/gate.py spread_band",
            verdict="MEASURED_STANDARD", is_primary=False, gate=None, margin=None,
            action=("Publishable standard, measured here: the flatten's delta is IDENTICAL to "
                    "eight decimal places at all four cost bands, because it changes gross R and "
                    "swap while leaving the trade SET -- and therefore the spread charge -- "
                    "untouched. Any cell that drops trades (an embargo, a wide margin) does vary "
                    "by band. So the ratified 'admits at N of 3 bands' phrasing applies to a "
                    "LEVEL and not to a same-population cost delta; publishing the band column "
                    "for a delta is still right, and reading a spread across it as evidence would "
                    "be wrong."),
            evidence={"delta_m0_by_band_sub_xvol": [-0.51388] * 4,
                      "delta_m24h_by_band_crypto": [-0.321787, -0.324622, -0.324973, -0.354427]}),
        row(prescription="THE_CENSUS_CROSSED_VS_NOT_COMPARISON_IS_SURVIVORSHIP",
            sleeve="ALL", component="phase13/receipts/BA_WEEKEND_V1.json census",
            verdict="MEASURED_TRAP", is_primary=False, gate=None, margin=None,
            action=("Weekend-crossing trades average +1.04 to +1.90 R gross against +0.21 to "
                    "+0.48 for non-crossing ones on three of the four armed sleeves, and reading "
                    "that as 'weekend holding is where the edge is' would be wrong by "
                    "construction: a trade still open on Friday night is a trade that did not "
                    "stop out earlier in the week. Crossing is an OUTCOME, not a treatment. Only "
                    "the counterfactual replay prices the policy. `energy_agri` inverts (-0.14 "
                    "crossed vs +1.44) which is what makes the confound visible rather than "
                    "plausible."),
            evidence={s: {"mean_r_crossed": r["mean_r_gross_crossed"],
                          "mean_r_not_crossed": r["mean_r_gross_not_crossed"]}
                      for s, r in cen["sleeves"].items()}),
    ]
    return out


def main() -> int:
    doc = json.loads(ART.read_text(encoding="utf-8"))
    rs = rows(doc)
    OUT.write_text(json.dumps({
        "schema": "gtos.repair_queue.session_copy.v1",
        "session": SESSION, "blocks": BLOCKS, "n_rows": len(rs),
        "note": ("this file is regenerated in full and is AUTHORITATIVE for BA's rows; the shared "
                 "sidecar is append-only and a landed row there is never rewritten (AP §7.2) — a "
                 "correction is an errata row."),
        "rows": rs,
    }, indent=1, sort_keys=True))
    append = rs
    if "--errata" in sys.argv:
        # AP §7.2: a landed sidecar row is never rewritten. This session's first row landed
        # saying "all four sleeves stay POSITIVE under the flatten", which an adversarial pass
        # then measured to be true at three of four cost bands and FALSE for `crypto` at the
        # high band. The authoritative session copy above carries the corrected text; the
        # sidecar gets the correction as its own row.
        append = [{"session": SESSION, "appended_utc": rs[0]["appended_utc"],
                   "prescription": "ERRATA__BA_ROW_1_ALL_FOUR_POSITIVE_IS_THREE_OF_FOUR_BANDS",
                   "sleeve": "crypto", "component": "REPAIR_QUEUE_BA.json row 1",
                   "verdict": "ERRATA", "is_primary": False, "gate": None, "margin": -0.0382,
                   "action": ("Corrects this session's own first row. It said 'all four sleeves "
                              "stay POSITIVE under the flatten'; measured by band, that holds at "
                              "the flat/low/mid bands and FAILS for `crypto` at the HIGH band, "
                              "where the calendar flatten leaves -0.0382 (against +0.1815 under "
                              "the market-close reading). The flatten's DELTA is band-invariant "
                              "-- it moves gross R and swap, not the spread charge -- so the "
                              "error was reading a band-invariant delta as if the LEVEL it left "
                              "behind were band-invariant too. A drop-or-keep decision reads the "
                              "level. Ties directly to OD-BA-1: the one sleeve that turns "
                              "negative is the one an exemption would rescue."),
                   "evidence": {"crypto_post_flatten_by_band":
                                [0.0737, 0.0470, 0.0419, -0.0382],
                                "crypto_post_flatten_high_band_grid_reading": 0.1815,
                                "corrects_row": "WEEKEND_HOLDING_POLICY_BUILT_AND_PRICED"}}]
    with SIDECAR.open("a", encoding="utf-8") as fh:
        for r in append:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"wrote {OUT.relative_to(REPO)} ({len(rs)} rows) and appended {len(append)} row(s) to "
          f"{SIDECAR.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
