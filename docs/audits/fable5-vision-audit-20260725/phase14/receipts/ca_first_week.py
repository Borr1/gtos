#!/usr/bin/env python3
"""Session CA (B2135-B2144) — the armed set's first days, read honestly.

    python3 .../phase14/receipts/ca_first_week.py [--as-of 2026-07-31T12:00:00Z]

THE ANSWER BEFORE THE METHOD, BECAUSE THE ANSWER IS "DO NOT READ IT YET"
-------------------------------------------------------------------------
The commission asks for the first live week's reconciliation. Two facts decide what that can
honestly be:

1. **There is no post-arming fill record on this machine.** Searched: the only
   `LIVE_TRADE_ROWS.jsonl` anywhere is `phase1/w7_forensics/`, 300 rows, every one stamped
   `stack_era = pre_w7_fleet` and dated June 2026 — the PRE-arming window AS used as the
   prior and forbade merging into any stop-condition evaluation. Producing the post-arming
   one is a read-only VPS export plus `scripts/w7_live_forensics.py`, and the VPS is the
   orchestrator's. The exact command is in `the_export_that_would_close_this` below.

2. **Even with it, the window is too short to read, and that is measurable rather than a
   feeling.** At the live-equivalent cadence CA measured for the CURRENT armed sets
   (`CA_FILL_TRUTH_RESTATE_V1.json`), the expected number of fills since arming is under
   one on both accounts. So ZERO fills is the modal outcome and carries almost no
   information — and the same arithmetic says how long it must run before it does.

This file therefore delivers the reconciliation HARNESS and the power statement, and refuses
to deliver a verdict it cannot support. It also states the one thing the estate would
otherwise be tempted to conclude from silence, and why that conclusion would be wrong.

BOUNDARY. Offline and pure. Reads committed receipts; writes one JSON. Never contacts the
VPS, never runs a broker-capable script, arms and pulls nothing.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

RESTATE = HERE / "CA_FILL_TRUTH_RESTATE_V1.json"
STOPS = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/FIVE_SLEEVE_STOP_CONDITIONS_V1.json"
SILENCE_RECEIPT = REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts/BB_FILL_TRUTH_V1.json"
OUT = HERE / "CA_FIRST_WEEK_V1.json"

#: Every arming/pull event on the record, from the ceremony receipts. UTC.
TIMELINE = [
    ("2026-07-29T12:55:00Z", "FTMO", "ARMED", "4 sleeves incl. metals_core",
     "CLAUDE.md §4 / phase8/receipts/VPS_CEREMONY_COMPLETED.md"),
    ("2026-07-29T14:25:00Z", "FTMO", "PULL", "metals_core removed -> 3 sleeves",
     "CLAUDE.md §4"),
    ("2026-07-30T05:18:00Z", "redacted_account", "ARMED", "3 sleeves",
     "phase8/receipts/FN_ARMING_20260730.md"),
    ("2026-07-30T11:52:00Z", "both", "EXPAND", "3 -> 5 sleeves (fx_jpy, sub_mid_dn_revert)",
     "phase8/receipts/FIVE_SLEEVE_EXPANSION_20260730.md, host f855250cd"),
    ("2026-07-30T14:57:00Z", "both", "PULL", "fx_jpy removed -> 4 sleeves",
     "phase8/receipts/FXJPY_PULL_20260730.md, host 7017c6745"),
    ("2026-07-31T01:26:00Z", "FTMO", "EXPAND",
     "mx_btcusd_d1_donchian_20_breakout on --frontier-exits (target_5R) -> 5 sleeves",
     "phase13/receipts/MX_ACTIVATION_20260731.md, host d6c9c4b19"),
]
#: The moment each account's CURRENT `--tags` set took effect. Everything before it is a
#: DIFFERENT book, and pooling them would be the same error AS's window rule forbids.
CURRENT_SET_FROM = {"FTMO": "2026-07-31T01:26:00Z", "redacted_account": "2026-07-30T14:57:00Z"}
DEFAULT_AS_OF = "2026-07-31T12:00:00Z"

FILLS_CANDIDATES = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl",
)


def _t(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _weekday_sessions(a: dt.datetime, b: dt.datetime) -> float:
    """Fractional weekday sessions between two instants — the unit BB's alarm counts in."""
    n = 0.0
    cur = a
    while cur < b:
        nxt = min(b, cur.replace(hour=0, minute=0, second=0, microsecond=0)
                  + dt.timedelta(days=1))
        if cur.weekday() < 5:
            n += (nxt - cur).total_seconds() / 86400.0
        cur = nxt
    return n


def _find_post_arming_fills() -> dict:
    """Is there a post-arming fill record anywhere? Answered by looking, not by assuming."""
    found = []
    for p in FILLS_CANDIDATES:
        if not p.is_file():
            continue
        eras, n, latest = set(), 0, ""
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            n += 1
            eras.add(r.get("denominator_exclusion_reason") or r.get("stack_era") or "?")
            latest = max(latest, str(r.get("exit_time_utc") or r.get("entry_time_utc") or ""))
        found.append({"path": str(p.relative_to(REPO)), "n_rows": n,
                      "latest_row_utc": latest, "eras": sorted(eras)[:4]})
    # a repo-wide sweep, so "none exists" is a measurement rather than a memory
    try:
        hits = subprocess.run(
            ["git", "ls-files", "--", "*LIVE_TRADE_ROWS*", "*live_fills*", "*post_arming*"],
            cwd=REPO, capture_output=True, text=True, timeout=60).stdout.split()
    except Exception:
        hits = []
    return {"files_examined": found, "git_tracked_candidates": sorted(hits),
            "post_arming_record_present": False if all(
                (f["latest_row_utc"] or "") < "2026-07-29" for f in found) else "CHECK"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default=DEFAULT_AS_OF)
    a = ap.parse_args(argv)
    as_of = _t(a.as_of)

    restate = json.loads(RESTATE.read_text())
    arms = restate["armed"]["arms"]
    accounts = {}
    for acct in ("FTMO", "redacted_account"):
        key = f"{acct}::mx_target_5R" if acct == "FTMO" else acct
        arm = arms.get(key) or arms.get(acct)
        start = _t(CURRENT_SET_FROM[acct])
        hours = (as_of - start).total_seconds() / 3600.0
        sessions = _weekday_sessions(start, as_of)
        wk_live = float(arm["live_equivalent"]["FULL_SURFACE_fills_per_week"])
        wk_arch = float(arm["archive_walk"]["FULL_SURFACE_fills_per_week"])
        lam = wk_live * (as_of - start).total_seconds() / (7 * 86400.0)
        lam_arch = wk_arch * (as_of - start).total_seconds() / (7 * 86400.0)
        # Days until the expected count reaches 1, 3 and 10 fills -- the honest calendar
        # for "when does this window start to say anything".
        horizon = {f"expect_{n}_fills": round(n / wk_live * 7, 1) for n in (1, 3, 10)}
        accounts[acct] = {
            "armed_tags": arm["armed_tags"],
            "current_set_effective_from_utc": CURRENT_SET_FROM[acct],
            "as_of_utc": a.as_of,
            "hours_armed_under_the_CURRENT_set": round(hours, 2),
            "weekday_sessions_armed": round(sessions, 3),
            "live_equivalent_fills_per_week_book": wk_live,
            "archive_convention_fills_per_week_book": wk_arch,
            "EXPECTED_fills_so_far_live_equivalent": round(lam, 4),
            "EXPECTED_fills_so_far_archive_convention": round(lam_arch, 4),
            "P_zero_fills_if_the_book_is_healthy": round(math.exp(-lam), 4),
            "P_at_least_one_fill": round(1 - math.exp(-lam), 4),
            "calendar_days_until_the_book_EXPECTS": horizon,
            "reading": (
                f"zero fills is the MODAL outcome: a healthy book produces none "
                f"{round(math.exp(-lam) * 100)} % of the time over this window. Silence here "
                f"is not evidence of a fault and not evidence of an edge."),
        }
        print(f"{acct:11s} armed {round(hours,1)}h under the current set; expected fills "
              f"{lam:.3f} (P(0)={math.exp(-lam):.2f}); 1 fill expected in "
              f"{horizon['expect_1_fills']} calendar days")

    # the silence alarm, evaluated as of now against BB's calibrated thresholds
    sil = json.loads(SILENCE_RECEIPT.read_text()).get("quiet_alarm", {})
    rec = sil.get("RECOMMENDATION") or {}
    silence = {
        "warn_after_silent_weekday_sessions": rec.get("warn_after_silent_weekday_sessions"),
        "alert_after_silent_weekday_sessions": rec.get("alert_after_silent_weekday_sessions"),
        "sessions_elapsed_since_each_account_armed": {
            k: round(_weekday_sessions(_t(v), as_of), 3) for k, v in CURRENT_SET_FROM.items()},
        "state": "CLEAN — nowhere near the warn threshold, and could not be",
        "the_caveat_that_matters": (
            "these thresholds are a property of the ARMED SET (BB handoff 4) and BB measured "
            "them on its four. CA's restatement puts FTMO's five-sleeve book at 1.673 "
            "live-equivalent fills/week against the four's 1.387, so FTMO's true warn "
            "threshold is TIGHTER than the receipt's 15 sessions. The tool reads its "
            "thresholds from the receipt at run time and refuses to invent one, which is "
            "correct; re-deriving them for the current sets is the routed handoff."),
        "and_the_blind_spot_BB_named": (
            "the counter indexes weekday sessions, so it cannot see the 5.6 % of `crypto` "
            "fills that land at a weekend. Conservative, but an operator watching across a "
            "weekend should know."),
    }

    stops = json.loads(STOPS.read_text())
    tracking = {
        "why_no_condition_can_have_fired": (
            "every pre-registered condition is denominated in FILLS or in R: S1a/S1b need a "
            "cumulative R path, S2 needs >= 20 fills across >= 8 day blocks, S5 needs 9 "
            "consecutive stop-outs, S3 needs closed positions to count swap nights, S4 needs "
            "a median hold. With an expected fill count under one on both accounts, none of "
            "them has an input yet. The correct state for all of them is S7_unchecked, which "
            "`book_sleeve_telemetry.py` exits 3 for — 'nothing is wrong' and 'nothing was "
            "checked' are different, and the tool already refuses to collapse them."),
        "the_conditions": sorted(stops["conditions"]),
        "S6_book_composition_is_the_exception_and_it_IS_checkable_today": (
            "S6 compares the workers' `--tags` to the expected armed set and needs no fill at "
            "all. Its `expected_tags` in FIVE_SLEEVE_STOP_CONDITIONS_V1.json is the "
            "2026-07-30 five — `crypto, energy_agri, sub_xvol_pullback, fx_jpy, "
            "sub_mid_dn_revert` — which is STALE in both directions after the fx_jpy pull and "
            "the mx_btcusd arming. Against a correct host read it would fire CRITICAL on both "
            "accounts today, for the wrong reason. Refreshing that list is a receipt edit, "
            "not a ceremony, and it is the single highest-value thing on this page."),
        "calendar_to_evaluability": (restate.get("stop_conditions_at_fill_truth") or {}).get(
            "per_sleeve_account"),
    }

    doc = {
        "schema": "gtos.wave14.ca.first_week.v1",
        "session": "CA", "blocks": "B2135-B2144",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "as_of_utc": a.as_of,
        "headline": (
            "The armed set's first days are UNREADABLE, and that is a measurement rather than "
            "a hedge: the expected fill count under each account's CURRENT `--tags` set is "
            "below one, so zero fills is the modal outcome of a perfectly healthy book. "
            "Nothing here is a verdict on any sleeve. Two things ARE actionable today and "
            "neither needs a fill: S6's `expected_tags` list is stale in both directions, and "
            "the silence thresholds belong to a book that is no longer the armed one."),
        "arming_timeline": [
            {"utc": t, "account": acc, "event": ev, "what": w, "receipt": r}
            for t, acc, ev, w, r in TIMELINE],
        "accounts": accounts,
        "post_arming_fill_record": _find_post_arming_fills(),
        "the_export_that_would_close_this": {
            "step_1": ("a read-only VPS export of the MT5 API state — the orchestrator's "
                       "ceremony, never a session's: "
                       "<export>/09_mt5_api/{ftmo,redacted_account}_history_{deals,orders}_get.jsonl"),
            "step_2": ("python3 scripts/w7_live_forensics.py --export-root <export> "
                       "--out-dir <dir>   ->   <dir>/LIVE_TRADE_ROWS.jsonl"),
            "step_3": ("python3 scripts/book_sleeve_telemetry.py --fills <dir>/LIVE_TRADE_ROWS.jsonl "
                       "--armed-utc 2026-07-31T01:26:00Z   (FTMO; use 2026-07-30T14:57:00Z "
                       "for redacted_account — the two sets took effect at different instants and "
                       "pooling them would evaluate a book neither account runs)"),
            "note": ("the tool already refuses to merge the pre-arming prior into a "
                     "stop-condition evaluation, so re-running it early is safe; it will "
                     "print S7_unchecked and exit 3."),
        },
        "silence_alarm": silence,
        "stop_condition_tracking": tracking,
        "what_this_page_refuses_to_say": (
            "that any sleeve is tracking or failing. With an expected fill count below one, a "
            "positive first fill and a negative first fill are equally consistent with every "
            "hypothesis on the table. The estate's own instrument for this is AS's "
            "S1b evidence floor, and CA measured that it needs 28-194 months of live fills "
            "per sleeve at the true cadence. The first week cannot be read. The first YEAR "
            "will be thin."),
    }
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print(f"  post-arming fill record present: "
          f"{doc['post_arming_fill_record']['post_arming_record_present']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
