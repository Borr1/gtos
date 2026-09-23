"""SURVIVOR_BOOK_V1 -- the cost-true W7 book, per account, with its uncertainty stated.

    python3 scripts/build_survivor_book.py

Consumes `scripts/recost_w7_validation.py` and emits
`research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json`.

TWO BASES, BOTH REPORTED, BECAUSE THEY DISAGREE BY 1.7x
-------------------------------------------------------
`INTEG_W7_final_book.grid` reports `monthly_pct = mean_per_book_day * risk * 21`. That is
correct only if the book fires on ~21 days a calendar month. Measured: it fires on **12.26**
over the full 2015-2026 window (57.0% of weekday sessions) and on **21.2** in the 2025-2026
forward window (101.3%). So the headline basis is right for the recent regime and overstates
the full window by 1.71x. Both are published; neither is called "the" number.

The distinction is not cosmetic here. The survivor subset looks far better *per book-day*
and far worse *per calendar month*, because what it drops is most of the book's frequency.
A reader given only the per-book-day column would reach the opposite conclusion.

THIS FILE DOES NOT CHOOSE THE BOOK
----------------------------------
Sleeve composition and the risk dial are Borhen's decisions at OD-3 (WAVE_3_WORKING_AGREEMENT
§4). `SURVIVORS_ONLY` is a measurement of what the cost-surviving subset does, presented
next to the full book of record so the two can be compared. It is an input, not a proposal.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
# `scripts/research/` is a REGULAR package (it has an __init__.py) and a regular package
# beats a namespace portion at ANY sys.path position -- so the moment `scripts/` is
# searchable, `import research` resolves there and `research.operations.*` stops resolving
# for the whole process. Python puts the script's own directory on sys.path automatically,
# so appending is not enough either. Pin the repo-root package first, with sys.path
# temporarily restricted to the repo root, and everything after it is harmless.
# Session V's full-suite A/B measured the alternative as 6 unexplained regressions in
# tests/test_audit_b6_* and tests/test_b7_5_*.
_sys_path = sys.path[:]
try:
    sys.path[:] = [str(REPO)]
    import research.operations  # noqa: E402,F401
finally:
    sys.path[:] = _sys_path
sys.path.insert(0, str(REPO / "scripts"))

import recost_w7_validation as M  # noqa: E402

DIAL = 0.020  # config/agent_config.yaml profile clean3_w7_ceiling_nom2p00 -- 2.0% nominal


def weekday_sessions(a, b):
    return sum(1 for i in range((b - a).days + 1)
               if (a + dt.timedelta(days=i)).weekday() < 5)


def econ(sub, acct, cm, nights, sd_book, W2, dial=DIAL, forward=False):
    for r in sub:
        n = M.SLEEVE_MAX_NIGHTS[r["sleeve"]] if nights == "max" else nights
        c, _ = M.row_cost(r, acct, n, "sleeve_median", cm)
        r["R_s"] = None if c is None else r["R_gross"] - c
    days, _, Mx, _ = M.build_matrix_from(sub, "R_s")
    nact = [sum(1 for v in row if abs(v) > 1e-9) for row in Mx]
    Mk = [[v * M.kelly_mult(nact[i]) for v in Mx[i]] for i in range(len(Mx))]
    comb = [sum(r) for r in Mk]
    if forward:
        pair = [(v, d) for v, d in zip(comb, days) if d.year >= 2025]
        comb = [v for v, _ in pair]
        days = [d for _, d in pair]
    sd = statistics.pstdev(comb)
    vs = sd_book / sd if sd else 0.0
    res = W2.mc_series(comb, dial * vs, seed_base=1)
    a, b = min(days), max(days)
    sess = weekday_sessions(a, b)
    months = (b.year - a.year) * 12 + (b.month - a.month) + 1
    bdpm = len(days) / months
    mu = statistics.fmean(comb)
    return dict(
        window=("forward_2025+" if forward else "full_2015_2026"),
        nights=("sleeve_max" if nights == "max" else nights),
        book_days=len(days), weekday_sessions=sess,
        density_pct=round(100.0 * len(days) / sess, 1),
        book_days_per_calendar_month=round(bdpm, 2),
        mean_r_per_book_day=round(mu, 5), vol_scale=round(vs, 4),
        eff_risk_pct=round(dial * vs * 100, 3),
        p_pass=round(res["p_pass"], 5), p_fail_dd=round(res["p_fail_dd"], 5),
        p_fail_daily=round(res["p_fail_daily"], 5),
        median_book_days_to_pass=res["med_days_pass"],
        median_calendar_days_to_pass=(round(res["med_days_pass"] * sess / len(days))
                                      if res["med_days_pass"] else None),
        monthly_pct_headline_x21=round(mu * dial * vs * 21 * 100, 3),
        monthly_pct_calendar=round(mu * dial * vs * bdpm * 100, 3))


#: Where the committed artifact of record lives. Overwriting it is now opt-in.
COMMITTED_OUT = "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"


def main(argv=None):
    # WHY THIS ARGUMENT EXISTS (added 2026-07-30, Session AI, after it bit me)
    # ----------------------------------------------------------------------
    # This script took NO arguments and wrote unconditionally to the committed
    # `SURVIVOR_BOOK_V1.json` -- an owner-facing artifact that ten downstream documents cite
    # and that `MC_FIRM_TRUE_V1` uses as its own reconstruction control. Running it to CHECK
    # whether it still reproduces therefore destroyed the thing being checked, and passing
    # `--out /tmp/...` was silently ignored because there was nothing to parse it. It cost a
    # `git checkout` to undo and it would have cost a lot more if the session had committed
    # first.
    #
    # It does NOT reproduce at HEAD any more, and the cause is benign: `8f6da5150` and
    # `33d854189` extended `BROKER_TRUE_COSTS_V1.json` after Session Q sealed its figures, so
    # FTMO now carries 167 priced instruments against redacted_account's 76 and the FTMO half of the
    # book re-prices. `crypto` goes MEASURED 35 -> 72, `idxrev` 4,939 -> 5,876. Nothing is
    # wrong; the artifact is simply older than its inputs. So the default is to write NOWHERE
    # near the committed path unless asked.
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None,
                    help="where to write. Default: print a summary and write nothing.")
    ap.add_argument("--write-committed", action="store_true",
                    help=f"overwrite {COMMITTED_OUT}. Requires --out to be unset and is the "
                         f"ONLY way to touch the artifact of record.")
    a = ap.parse_args(argv)
    if a.write_committed and a.out:
        raise SystemExit("--write-committed and --out are mutually exclusive")

    st = M.build([])
    rows = st["rows"]
    W2 = M._route_mc()
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = M.build_matrix_from(rows, "R_legacy")

    out = dict(
        schema="gtos.w7_recost.survivor_book.v1",
        generated_by="scripts/build_survivor_book.py",
        dial_nominal_pct=DIAL * 100,
        dial_provenance=("config/agent_config.yaml:1246-1394 profile "
                         "clean3_w7_ceiling_nom2p00 -- 2.0% nominal per account"),
        sd_book_reference=round(sd_book, 5),
        boundary=("Sleeve composition and the risk dial are Borhen's decisions at OD-3. "
                  "SURVIVORS_ONLY is a measurement of the cost-surviving subset, not a "
                  "proposal to trade it."),
        accounts={})

    for acct in ("FTMO", "redacted_account"):
        pool = collections.defaultdict(list)
        for r in rows:
            c = r[f"cost_{acct}"]
            if c["status"] == "priced":
                pool[r["sleeve"]].append(c["cost_ex_swap_r"])
        cm = {k: statistics.median(v) for k, v in pool.items()}
        tab = M.sleeve_table(rows, acct, cm)
        surv = [sl for sl, v in tab.items() if v["survives_at_max_carry"]]
        dead = [sl for sl, v in tab.items() if not v["survives_at_max_carry"]]
        acc = dict(sleeves=tab, survivors=surv, killed=dead,
                   killed_reason={sl: ("negative before any cost"
                                       if tab[sl]["cached_net_r"] <= 0 else
                                       "carry break-even below the sleeve's exit horizon")
                                  for sl in dead},
                   variants={})
        for label, keep in (("ALL_11_BOOK_OF_RECORD", list(tab)), ("SURVIVORS_ONLY", surv)):
            sub = [r for r in rows if r["sleeve"] in keep]
            acc["variants"][label] = {
                f"{'fwd' if fwd else 'full'}_nights_{n if n != 'max' else 'max'}":
                    econ(sub, acct, cm, n, sd_book, W2, forward=fwd)
                for fwd in (False, True) for n in (0.0, 1.0, "max")}
        out["accounts"][acct] = acc

    blob = json.dumps(out, indent=1, default=str)
    if a.write_committed:
        p = REPO / COMMITTED_OUT
        p.write_text(blob)
        print(f"wrote {p.relative_to(REPO)}  (THE COMMITTED ARTIFACT OF RECORD)")
    elif a.out:
        p = Path(a.out)
        p.write_text(blob)
        print(f"wrote {p}")
    else:
        import hashlib
        cur = REPO / COMMITTED_OUT
        same = (cur.read_bytes() == blob.encode()) if cur.is_file() else None
        print(f"wrote nothing. sha256 of this build: "
              f"{hashlib.sha256(blob.encode()).hexdigest()[:16]}  ({len(blob)} B)")
        print(f"reproduces the committed artifact: {same}")
        if same is False:
            print("  -> expected at HEAD: 8f6da5150 and 33d854189 extended "
                  "BROKER_TRUE_COSTS_V1.json after this artifact was sealed. Diff the "
                  "`coverage` blocks before concluding anything is broken.")
        print("  pass --out PATH to write a copy, or --write-committed to replace the "
              "artifact of record.")
    return out


if __name__ == "__main__":
    main()
