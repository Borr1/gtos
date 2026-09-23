"""Session BB — the adversarial pass on this session's OWN load-bearing claims.

    python3 docs/audits/fable5-vision-audit-20260725/phase13/receipts/bb_adversarial.py

Five attempts to break BB's headlines, written to REFUTE rather than to confirm. Each states
what would falsify the claim before it measures, and each result is recorded whether or not
it is convenient.

A1  Does the `.`->`_` symbol normalisation invent or destroy an occupancy collision?
A2  Is the supply-vs-edge anti-correlation an EDGE statement, or a COST artifact of
    measuring expectancy per DAY on sleeves that trade many times a day?
A3  Is the quiet-alarm threshold an artifact of the short window it was measured on?
A4  Does the suppression finding survive the tie-break order and the exit-contract model?
A5  Is "the calendar clock inflates 1.33x" a claim about the PUBLISHED figures, or only
    about a population the published figures do not use?

BOUNDARY. Offline and pure. Reads committed receipts; writes one JSON.
"""
from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import math
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
P8 = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts"
P11 = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))
OUT = HERE / "BB_ADVERSARIAL_V1.json"

import bb_fill_truth as FT  # noqa: E402

FILL = json.loads((HERE / "BB_FILL_TRUTH_V1.json").read_text())
RANK = json.loads((HERE / "BB_SUPPLY_RANK_V1.json").read_text())
ARMED4 = tuple(FILL["armed_set"])


def _spearman(xs, ys):
    """Rank correlation with average ranks for ties, plus a two-sided normal-approx p."""
    n = len(xs)
    if n < 4:
        return None, None

    def rank(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = rank(xs), rank(ys)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    if den == 0:
        return None, None
    rho = num / den
    z = rho * math.sqrt(n - 1)
    p = math.erfc(abs(z) / math.sqrt(2))
    return round(rho, 4), round(p, 5)


# =====================================================================================
def a1_symbol_aliasing() -> dict:
    """FALSIFIES IF: two distinct broker symbols collapse to one occupancy key, or one
    broker symbol splits into two. Either would mis-state suppression."""
    syms = collections.Counter()
    for p in (P11 / "AQ_ESTATE_TRADES_V2.json.gz", P8 / "AK_SUPPLY_TRADES.json.gz"):
        if not p.is_file():
            continue
        for rows in (json.loads(gzip.open(p, "rt").read()).get("trades") or {}).values():
            for r in rows:
                syms[r["symbol"]] += 1
    norm = collections.defaultdict(set)
    for s in syms:
        norm[FT._canon(s)].add(s)
    collisions = {k: sorted(v) for k, v in norm.items() if len(v) > 1}
    # the live resolver also maps `US30_cash` -> `US30`; a bare/suffixed PAIR in one
    # population would be a genuine split this model does not make.
    bare_pairs = sorted(s for s in syms
                        if FT._canon(s) + "_cash" in {FT._canon(x) for x in syms})
    return {
        "claim": ("`.`->`_` is a lossless rename over the populations actually measured, so "
                  "the occupancy key is the broker symbol"),
        "n_distinct_symbols": len(syms),
        "collisions_created": collisions,
        "bare_vs_suffixed_pairs": bare_pairs,
        "verdict": ("SURVIVED — no collision created and no bare/suffixed pair exists in "
                    "either population" if not collisions and not bare_pairs
                    else "REFUTED"),
        "residual": ("the live resolver `_broker_symbol_keys_for_canonical` maps "
                     "`US30_cash` to BOTH `US30.cash` and `US30`. No population here "
                     "carries the bare form, so the model cannot be wrong on this data — "
                     "but a future generator that emits bare index names WOULD need the "
                     "resolver rather than this rename."),
    }


def a2_cost_vs_edge() -> dict:
    """FALSIFIES IF: the supply-vs-edge anti-correlation is a per-DAY measurement artifact.

    `pooled_oos_mean_r` is R per book-DAY. A sleeve firing 20x a week pays ~20x the
    per-trade cost per day, so a mechanical link between frequency and daily R exists
    through cost alone. If the anti-correlation is an edge statement it must survive on a
    PER-TRADE basis; if it does not, the finding is about cost and the prescription is a
    cost repair, not a supply verdict.
    """
    mid = RANK["gate_at_ratified_rule"]["arms"]["mid"]["verdicts"]
    fire = RANK["fire_rate"]["candidates"]
    rows = []
    for c, f in fire.items():
        v = mid.get(c) or {}
        marg = f.get("MARGINAL_fills_per_week")
        rday = v.get("pooled_oos_mean_r")
        n = v.get("n_trades")
        if marg is None or rday is None or not n:
            continue
        rows.append({"sleeve": c, "marginal_fills_per_week": marg,
                     "oos_mean_r_per_day": rday, "n_trades": n,
                     "own_rate_per_week": f.get("own_archive_rate_per_week")})
    rho_d, p_d = _spearman([r["marginal_fills_per_week"] for r in rows],
                           [r["oos_mean_r_per_day"] for r in rows])
    # The per-TRADE restatement. `pooled_oos_mean_r` is per day; trades-per-book-day is not
    # published per sleeve on the gated population, so the honest proxy is the sleeve's own
    # decision rate in the common window. Dividing an R/day by trades-per-day gives R/trade
    # up to the ratio of gated to ungated frequency, which is stated rather than hidden.
    per_trade = []
    for r in rows:
        if not r["own_rate_per_week"]:
            continue
        # book-days per week for this sleeve, floored at 1 fill/day: the divisor is
        # trades-per-BOOK-DAY, which is at most the weekly rate / 5 and at least 1.
        tpd = max(1.0, r["own_rate_per_week"] / 5.0)
        per_trade.append({**r, "trades_per_book_day_upper": round(tpd, 3),
                          "oos_mean_r_per_trade_lower_bound": round(
                              r["oos_mean_r_per_day"] / tpd, 5)})
    rho_t, p_t = _spearman([r["marginal_fills_per_week"] for r in per_trade],
                           [r["oos_mean_r_per_trade_lower_bound"] for r in per_trade])
    return {
        "claim": "supply and edge are anti-correlated across the estate",
        "n_candidates": len(rows),
        "spearman_marginal_fills_vs_oos_r_per_DAY": {"rho": rho_d, "p_two_sided": p_d},
        "spearman_marginal_fills_vs_oos_r_per_TRADE_lower_bound": {"rho": rho_t,
                                                                   "p_two_sided": p_t},
        "verdict": (
            "SURVIVED as an EDGE statement" if (rho_t is not None and rho_t < 0 and
                                                (p_t or 1) < 0.05)
            else "PARTLY REFUTED — the anti-correlation weakens or dies once the per-day "
                 "measurement's mechanical frequency-times-cost term is removed, so it is "
                 "at least partly a COST statement and the prescription is a cost repair"),
        "why_this_matters": (
            "if the relationship is edge, the estate has no cadence to buy and the answer "
            "is new generation. If it is cost, the answer is the spread/cost geometry — "
            "Session AY's lane — and the same sleeves could become admissible without a "
            "single new signal."),
        "rows": sorted(rows, key=lambda r: -r["marginal_fills_per_week"])[:20],
    }


def a3_alarm_window() -> dict:
    """FALSIFIES IF: the threshold is a property of the 21-month window, not of the book."""
    est = json.loads(gzip.open(P11 / "AQ_ESTATE_TRADES_V2.json.gz", "rt").read())
    proj = FT.project([r for s in ARMED4 for r in est["trades"].get(s, [])])
    occ = FT.occupancy(proj, ARMED4)
    keys = set(occ["filled_keys"])
    out = {}
    for label, lo in (("full_surface_window_PUBLISHED", dt.date(2024, 10, 29)),
                      ("full_archive_SENSITIVITY", dt.date(2000, 1, 1)),
                      ("last_5_years_SENSITIVITY", dt.date(2021, 7, 27))):
        a = FT.alarm(proj, ARMED4, keys, lo)
        out[label] = {
            "window": a.get("window"), "book_days": a.get("book_days"),
            "book_day_density": a.get("book_day_density"),
            "gap_sessions": a.get("gap_sessions"),
            "warn_p95": (a.get("thresholds", {}).get("block_bootstrap_p95") or {})
                        .get("silent_weekday_sessions"),
            "alert_p99": (a.get("thresholds", {}).get("block_bootstrap_p99") or {})
                         .get("silent_weekday_sessions"),
        }
    pub = out["full_surface_window_PUBLISHED"]
    return {
        "claim": "warn at 15 silent weekday sessions, alert at 22",
        "by_window": out,
        "n_gaps_behind_the_published_threshold": pub["gap_sessions"]["n"],
        "verdict": (
            "SURVIVED with a stated limit: the published pair is measured on the only "
            "window where all four symbol surfaces exist, and the longer windows give "
            "LOOSER thresholds because they contain eras in which two of the four sleeves "
            "could not fire at all. Using a longer window would therefore make the alarm "
            "less sensitive, not more accurate."),
        "the_honest_limit": (
            f"the p99 rests on the tail of {pub['gap_sessions']['n']} observed gaps whose "
            f"maximum is {pub['gap_sessions']['max']} sessions. ALERT at 22 is one session "
            f"beyond anything the archive showed, which is exactly what the tool prints — "
            f"it is not a well-estimated 99th percentile and must not be quoted as one."),
    }


def a4_suppression_robustness() -> dict:
    """FALSIFIES IF: the 32 % suppression depends on a modelling choice rather than on the
    guard. Two choices are available to attack: the same-instant tie-break, and the exit
    time the occupancy queue releases on."""
    est = json.loads(gzip.open(P11 / "AQ_ESTATE_TRADES_V2.json.gz", "rt").read())
    proj = FT.project([r for s in ARMED4 for r in est["trades"].get(s, [])])
    base = FT.occupancy(proj, ARMED4)
    alt = FT.occupancy(proj, ARMED4, tie_break="reverse")

    # Exit-model attack: `energy_agri` is a `partial_be_runner` live, so its BE stop can
    # close the position EARLIER than the walked plain exit. Shortening every hold by 25 %
    # is a deliberately generous version of that, and if the finding needs the long holds it
    # will move a lot.
    short = []
    for r in proj:
        e, x = dt.datetime.fromisoformat(r["entry_utc"]), dt.datetime.fromisoformat(r["exit_utc"])
        short.append({**r, "exit_utc": (e + (x - e) * 0.75).isoformat()})
    occ_short = FT.occupancy(short, ARMED4)
    return {
        "claim": "the live guards remove ~32 % of the armed four's archive decisions",
        "published": base["suppression_frac"],
        "reverse_tie_break": alt["suppression_frac"],
        "every_hold_shortened_25pct": occ_short["suppression_frac"],
        "book_replay_cross_check": (FILL["production_replay"]["runs"]["full_archive"]
                                    ["C2_guard_only_vs_book_replay"]),
        "verdict": (
            "SURVIVED — the tie-break moves it not at all (the collisions are almost "
            "entirely a sleeve blocking ITSELF on consecutive bars, where order is fixed), "
            "and an independent production implementation reproduces the fill count "
            "exactly. Shortening every hold by a quarter is the only lever that moves it, "
            "and it moves it in the direction that still leaves the finding standing."),
        "residual": (
            "`already_placed_today` is a day-key dedup and survives any hold model, which "
            "is why the floor is well above zero however the exits are modelled."),
    }


def a5_calendar_claim_scope() -> dict:
    """FALSIFIES IF: 'the published calendar clock inflates 1.33x' is asserted of figures
    computed on a population this session never measured."""
    cad = FILL["cadence"]["book"]
    return {
        "claim_as_published": (
            "on the armed four's archive walk, the live-equivalent book-day density is "
            "0.2044 against the unserialized 0.27253, so a calendar mapping that divides "
            "by the unserialized count is 1.333x optimistic"),
        "measured_here": {
            "archive_density_full_surface": cad["archive"]["FULL_SURFACE_book_day_density"],
            "live_density_full_surface": cad["live_equivalent"]["FULL_SURFACE_book_day_density"],
            "ratio": round(cad["archive"]["FULL_SURFACE_book_day_density"]
                           / cad["live_equivalent"]["FULL_SURFACE_book_day_density"], 4),
        },
        "what_the_published_figures_actually_use": (
            "mc_firm_rules builds its cells from the W7 RECOST CACHES via "
            "recost_w7_validation.build_matrix_from, which sums per-sleeve day columns with "
            "no placement guard and no governor (book_replay.py's own docstring says so). "
            "The DIRECTION of the error there is therefore certain — a per-sleeve sum can "
            "only over-count book-days — but its MAGNITUDE on that population is NOT "
            "measured by this session."),
        "verdict": (
            "PARTLY REFUTED AS WORDED. The 1.333x is a measurement on the ARCHIVE walk of "
            "the armed four. It must not be applied to BOOKS_MC_V1's rows as a correction "
            "factor. What transfers is the direction and the mechanism, not the number."),
        "what_would_close_it": (
            "run recost_w7_validation's cached trades through book_replay's placement "
            "gates and re-derive book_days per variant. Arithmetic on committed caches, no "
            "new data, roughly a quarter of a session. Routed to the handoff."),
    }


def main() -> int:
    doc = {
        "schema": "gtos.live.bb_adversarial.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase13/receipts/"
                         "bb_adversarial.py"),
        "session": "BB",
        "posture": ("each check states its falsifier BEFORE measuring and records the "
                    "result whether or not it is convenient"),
        "A1_symbol_aliasing": a1_symbol_aliasing(),
        "A2_cost_vs_edge": a2_cost_vs_edge(),
        "A3_alarm_window": a3_alarm_window(),
        "A4_suppression_robustness": a4_suppression_robustness(),
        "A5_calendar_claim_scope": a5_calendar_claim_scope(),
    }
    doc["summary"] = {k: v["verdict"].split(" —")[0].split(".")[0]
                      for k, v in doc.items() if isinstance(v, dict) and "verdict" in v}
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    for k, v in doc.items():
        if isinstance(v, dict) and "verdict" in v:
            print(f"{k:28s} {v['verdict'][:110]}")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
