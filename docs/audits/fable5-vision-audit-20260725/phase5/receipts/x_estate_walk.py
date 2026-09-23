"""The estate walk: the gate on everything generatable, the merged book, the diversifier test.

    python3 docs/audits/fable5-vision-audit-20260725/phase5/receipts/x_estate_walk.py

Reads `X_ESTATE_TRADES.json.gz` (produced by `x_estate_generate.py`) and answers four
questions in one run so that the multiplicity correction sees one family, not four slices:

  1. **The gate, on the whole estate.** Session W scored the 12 live market-expansion
     sleeves. This adds the H4 core book — including three of the four sleeves the funded
     account is being armed on — and the M15 session sleeves, under one sealed spec.
  2. **The merged book.** Sleeves composed through the production sizer against one equity
     curve (`walkforward/book_replay.py`), which nothing in this programme has ever run.
  3. **The diversifier certification.** `validation_integrity/portfolio_contribution.py`
     exists, is written, and had no caller. It asks the second honest question: does a sleeve
     that fails standalone still RAISE the book's Sharpe? None of its six conditions is
     relaxed here; if nothing certifies, that is the answer.
  4. **Where the next capture pays.** Which sleeves fail only for want of data, and which
     data.

MULTIPLICITY ACROSS SESSIONS IS CHARGED, NOT ASSUMED AWAY
----------------------------------------------------------
W tested 12 sleeves. This run tests the union. Reporting the winners of the union while
correcting only within this run would be exactly the error the correction exists to prevent,
so `declared_family_size` is set to the union of every sleeve any wave-5 session has put
through this gate — the 12 of `W_MX_PILOT.json` plus everything judged here — and the gate
uses `max(judged_here, declared)` (`gate.py:711`).

THE COST LOOK-AHEAD IS INHERITED, NOT DROPPED
----------------------------------------------
`BROKER_TRUE_COSTS_V1.json` measures spread over 37 days in 2026 and charges it as a
constant to a panel running 2004-2026. Spreads compressed, so every net number below is
optimistic by an unmeasured amount. `gate._cost_window_note()` stamps it on every result and
this driver re-states it rather than letting it sit in a footnote.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import math
import statistics
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.validation_integrity import dsr as _dsr  # noqa: E402
from src.research_infra.validation_integrity import perm_null as _perm  # noqa: E402
from src.research_infra.validation_integrity import regime_inflation as _regime  # noqa: E402
from src.research_infra.validation_integrity.portfolio_contribution import (  # noqa: E402
    certify_diversifier,
    incremental_sharpe,
)
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward.diversifier import (  # noqa: E402
    DiversifierEvidence,
    certify_guarded,
)
from src.research_infra.walkforward.book_replay import (  # noqa: E402
    BookConfig,
    BookTrade,
    book_daily_series,
    book_stats,
    replay_book,
)
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import build_daily_panel, price_trades  # noqa: E402
from src.research_infra.walkforward.registry import build_symbol_allowlist  # noqa: E402
from src.research_infra.walkforward.spec import GateSpec  # noqa: E402

IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts/X_ESTATE_TRADES.json.gz"
OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts/X_ESTATE_WALK.json"

#: The four sleeves the brief names as the armed set. `sub_xvol_pullback` is NOT in the live
#: active book at HEAD — `config/agent_config.yaml:1270` sets `include_clean3: false` — which
#: is a finding in its own right and is measured, not asserted, below.
ARMED4 = ("metals_core", "crypto", "energy_agri", "sub_xvol_pullback")
LIVE_ARMED3 = ("metals_core", "crypto", "energy_agri")

#: Every sleeve any wave-5 session has put through this gate. See the module docstring.
W_PILOT_FAMILY = 12


def _dt(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s)


def load() -> dict:
    with gzip.open(IN, "rt") as fh:
        return json.load(fh)


def to_records(raw: dict) -> dict[str, list[TradeRecord]]:
    out: dict[str, list[TradeRecord]] = {}
    for sleeve, rows in raw["trades"].items():
        recs = []
        for r in rows:
            recs.append(TradeRecord(
                sleeve=r["sleeve"], symbol=r["symbol"],
                entry_utc=_dt(r["entry_utc"]), exit_utc=_dt(r["exit_utc"]),
                direction=int(r["direction"]),
                sl_distance_price=float(r["sl_distance_price"]),
                entry_price=float(r["entry_price"]), r_gross=float(r["r_gross"]),
                features={"decision_day": r["decision_day"],
                          "timeframe": r["timeframe"],
                          "hold_hours": r["hold_hours"]},
            ))
        out[sleeve] = recs
    return out


# =====================================================================================
# 1. the gate


def run_estate_gate(records: dict, allowlist: dict, declared: int) -> dict:
    runs = {}
    for name, base in OPTIONS.items():
        spec = base.with_(
            spec_id=f"{base.spec_id}_x_estate",
            sleeve_symbol_allowlist=allowlist,
            declared_family_size=declared,
        )
        res = run_gate(records, spec)
        rows = []
        for s, v in sorted(res.verdicts.items()):
            rows.append({
                "sleeve": s, "verdict": v.verdict.value, "n_trades": v.n_trades,
                "pooled_oos_mean_r": v.pooled_oos_mean_r,
                "oos_mean_r_per_trade": v.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
                "lifetime_mean_r": v.gates.get("lifetime", {}).get("mean_r_net_per_trade_all_folds"),
                "p_raw": v.p_raw, "q_value": v.q_value,
                "oos_positive_fold_frac": v.gates.get("stability", {}).get("oos_positive_fold_frac"),
                "drop_best_retention": v.gates.get("robustness", {}).get("retention"),
                "coverage_frac": v.gates.get("cost_coverage", {}).get("coverage_frac"),
                "n_folds_evaluable": v.gates.get("sample", {}).get("n_folds_evaluable"),
                "regime_contamination": (v.telemetry.get("regime_inflation") or {}).get(
                    "contamination_flag"),
                "regime_basis": (v.telemetry.get("regime_inflation") or {}).get("inflation_basis"),
                "universe_restriction": (v.universe_restriction or {}).get("dropped_symbols"),
                "first_reason": (v.reasons[0] if v.reasons else None),
            })
        runs[name] = {
            "spec_sha256": spec.seal(), "spec_id": spec.spec_id,
            "admitted": res.admitted, "rejected": res.rejected,
            "not_evaluable": res.not_evaluable,
            "family": {k: v for k, v in res.family.items() if k != "n_trials_basis"},
            "rows": rows,
        }
        print(f"\n--- {name} (family {spec.declared_family_size}) ---")
        print(f"{'sleeve':40s} {'verdict':14s} {'n':>6s} {'R/day':>9s} {'R/trade':>9s} "
              f"{'q':>8s} {'pos':>5s}")
        for r in rows:
            f = lambda x, w=9, p=5: ("-" if x is None else f"{x:.{p}f}")  # noqa: E731
            pf = "-" if r["oos_positive_fold_frac"] is None else f"{r['oos_positive_fold_frac']:.0%}"
            q = "-" if r["q_value"] is None else f"{r['q_value']:.4g}"
            print(f"{r['sleeve']:40s} {r['verdict']:14s} {r['n_trades']:6d} "
                  f"{f(r['pooled_oos_mean_r']):>9s} {f(r['oos_mean_r_per_trade']):>9s} "
                  f"{q:>8s} {pf:>5s}")
        print(f"  ADMIT({len(res.admitted)}): {res.admitted}")
    return runs


# =====================================================================================
# 2. the merged book


def priced_book_trades(records: dict, spec: GateSpec) -> tuple[dict, dict]:
    """Price every trade once, and drop the symbols broker truth cannot price.

    A book that carried unpriceable trades at gross would be F38 with extra steps; a book
    that priced them with a plausible number would be F38 exactly. So the unpriceable
    SYMBOLS leave the book's universe entirely and the restriction is published — the same
    treatment `coverage_policy="restrict_to_priced"` gives a single sleeve, applied to the
    composition instead of to a verdict.
    """
    out: dict[str, list[BookTrade]] = {}
    dropped: dict[str, dict] = {}
    for sleeve, recs in records.items():
        if not recs:
            continue
        priced, cov = price_trades(recs, spec)
        keep, drop_syms, n_drop = [], set(), 0
        for p in priced:
            if p.status != "priced" or p.r_net is None:
                if p.status == "unpriced":
                    drop_syms.add(p.trade.symbol)
                n_drop += 1
                continue
            t = p.trade
            keep.append(BookTrade(
                sleeve=t.sleeve, symbol=t.symbol,
                symbol_canonical=t.features.get("symbol_canonical", t.symbol),
                entry_utc=t.entry_utc, exit_utc=t.exit_utc, direction=t.direction,
                stop_dist=t.sl_distance_price, entry_price=t.entry_price,
                r_net=float(p.r_net), decision_day=str(t.features.get("decision_day")),
                decision_bar_iso=str(t.features.get("decision_bar_iso") or ""),
                timeframe=t.features.get("timeframe"),
            ))
        out[sleeve] = keep
        c = cov.get(sleeve)
        dropped[sleeve] = {
            "n_kept": len(keep), "n_dropped": n_drop,
            "dropped_symbols": sorted(drop_syms),
            "coverage_frac": round(c.coverage_frac, 5) if c else None,
            "n_blackout": c.n_blackout_dropped if c else 0,
        }
    return out, dropped


def _halted(book_dict: dict) -> bool:
    """Did the governor's max-drawdown ENTRY BLOCK stop this book rather than the data?

    `admission.py:1290-1292` blocks new entries once equity falls `max_dd_entry_block_pct`
    below `max_dd_reference_equity`, and that reference is the STATIC initial balance
    (`governor_state.py:280-282`) — it does not trail up. So a book that draws down 9% never
    trades again, and its remaining calendar is unmeasured rather than flat.
    """
    rej = book_dict.get("rejections") or {}
    blocked = sum(v for k, v in rej.items() if "max_dd" in k)
    return blocked > 0.5 * max(1, book_dict.get("n_candidates") or 1)


def run_book(book_trades: dict, runtime: dict, sleeves, label: str,
             floating: str = "none") -> dict:
    flat = [t for s in sleeves for t in book_trades.get(s, [])]
    cfg = BookConfig(runtime=runtime, sleeves=tuple(sleeves), label=label, floating=floating)
    res = replay_book(flat, cfg)
    d = res.as_dict()
    d["daily_series_len"] = len(book_daily_series(res))
    return {"result": res, "dict": d}


# =====================================================================================
# 3. the diversifier certification


def standalone_edge(daily: dict, *, block: int = 5) -> dict:
    """Condition 1, computed exactly as `portfolio_contribution` says the caller must.

    "PSR-vs-zero significant AND block-permutation directional p<0.05"
    (`portfolio_contribution.py:142-146`). PBO is a multi-strategy concept and the module
    says it is not required for a single diversifier sleeve; it is reported at family level
    by the gate instead.
    """
    xs = [v for _d, v in sorted(daily.items())]
    if len(xs) < 8:
        return {"ok": False, "reason": f"only {len(xs)} daily observations"}
    psr = _dsr.probabilistic_sharpe_ratio(xs, 0.0)
    perm = _perm.block_permutation_test(xs, block=block, n_perm=10000, stat="mean", seed=20260729)
    ok = bool(psr["psr"] >= 0.95 and perm["p_value"] < 0.05)
    return {"ok": ok, "psr": psr["psr"], "sr_per_period": psr["sr_per_period"],
            "perm_p": perm["p_value"], "n_days": len(xs), "block": block}


def regime_clean(daily: dict, sealed_start: dt.date) -> dict:
    ds = sorted(daily.items())
    if len(ds) < 30:
        return {"ok": False, "reason": f"only {len(ds)} daily observations"}
    try:
        r = _regime.regime_inflation_diagnostic(ds, sealed_start, 128)
    except (ValueError, ZeroDivisionError, KeyError) as e:
        return {"ok": False, "reason": f"{type(e).__name__}: {e}"}
    return {"ok": not bool(r["contamination_flag"]),
            "contamination_flag": r["contamination_flag"],
            "inflation_basis": r.get("inflation_basis"),
            "fwd_all_mean_ratio": r["fwd_all_mean_ratio"],
            "haircut": r["recommended_magnitude_haircut"]}


def paired_block_ci(a: dict, b: dict, *, n_boot: int = 2000, block: int = 5,
                    seed: int = 20260729) -> dict:
    """CI on (mean(a) - mean(b)) and on the Sharpe difference, over a shared day calendar.

    THE NULL THE COMPOSITION COMPARISON AND THE LEAVE-ONE-OUT BOTH NEED. An adversarial
    refuter measured what their absence costs: over 20,000 replications with all 32 sleeves
    carrying EXACTLY zero edge, picking the best of six book compositions buys
    **+0.527 annualised Sharpe** of pure winner's curse (+0.726 over all 38 variants
    compared), and a leave-one-out over four provably worthless and interchangeable sleeves
    **names a scapegoat 99.2% of the time**, at an average apparent damage of −0.385
    annualised Sharpe.

    So neither "composition C is best" nor "sleeve S is dragging the book" is reportable
    without an interval. This is a paired day-block bootstrap on the union calendar: a day
    absent from one book contributes 0 there, which is what "flat that day" means.
    """
    days = sorted(set(a) | set(b))
    n = len(days)
    if n < 2 * block:
        return {"n_days": n, "ci_mean_delta": None, "ci_sharpe_delta": None,
                "note": f"only {n} days; no interval is estimable at block {block}"}
    xa = [a.get(d, 0.0) for d in days]
    xb = [b.get(d, 0.0) for d in days]

    def _stats(u, v):
        du = [x - y for x, y in zip(u, v)]
        m = statistics.fmean(du)
        sa = statistics.pstdev(u) if len(u) > 1 else 0.0
        sb = statistics.pstdev(v) if len(v) > 1 else 0.0
        sha = (statistics.fmean(u) / sa) if sa > 0 else 0.0
        shb = (statistics.fmean(v) / sb) if sb > 0 else 0.0
        return m, sha - shb

    obs_mean, obs_sharpe = _stats(xa, xb)
    mult, inc, mod = 1664525, 1013904223, 2 ** 32
    state = seed & 0xFFFFFFFF
    means, sharpes = [], []
    nb = max(1, n // block)
    for _ in range(n_boot):
        ua, ub = [], []
        for _k in range(nb + 1):
            state = (mult * state + inc) % mod
            i = state % n
            for j in range(block):
                ua.append(xa[(i + j) % n]); ub.append(xb[(i + j) % n])
        m, s = _stats(ua[:n], ub[:n])
        means.append(m); sharpes.append(s)
    means.sort(); sharpes.sort()
    lo, hi = int(0.025 * n_boot), int(0.975 * n_boot)
    return {
        "n_days": n, "block": block, "n_boot": n_boot,
        "observed_mean_delta": round(obs_mean, 8),
        "ci_mean_delta": [round(means[lo], 8), round(means[hi], 8)],
        "observed_sharpe_delta": round(obs_sharpe, 6),
        "ci_sharpe_delta": [round(sharpes[lo], 6), round(sharpes[hi], 6)],
        "sharpe_delta_significant": bool(sharpes[lo] > 0 or sharpes[hi] < 0),
    }


def corr_ci(book: dict, cand: dict, *, n_boot: int = 2000, block: int = 5,
            seed: int = 20260729) -> dict:
    """Correlation on the overlap, WITH the sample size that produced it.

    Prompt trap 5: these sleeves trade ~7 days a month, so a correlation ceiling built on 20
    overlapping observations is weak evidence and must be reported as such. The block
    bootstrap here is over the OVERLAPPING days only, so the CI widens exactly as the
    overlap thins.
    """
    common = sorted(set(book) & set(cand))
    n = len(common)
    if n < 6:
        return {"corr": None, "n_overlap": n, "ci": None,
                "note": "fewer than 6 overlapping days; no correlation is estimable"}
    b = [book[d] for d in common]
    c = [cand[d] for d in common]

    def _r(bb, cc):
        mb, mc = statistics.fmean(bb), statistics.fmean(cc)
        sb, sc = statistics.pstdev(bb), statistics.pstdev(cc)
        if sb == 0 or sc == 0:
            return 0.0
        return sum((x - mb) * (y - mc) for x, y in zip(bb, cc)) / (len(bb) * sb * sc)

    obs = _r(b, c)
    a, cc_, m = 1664525, 1013904223, 2 ** 32
    state = seed & 0xFFFFFFFF
    boots = []
    nb = max(1, n // block)
    for _ in range(n_boot):
        bb, cb = [], []
        for _k in range(nb + 1):
            state = (a * state + cc_) % m
            i = state % n
            for j in range(block):
                bb.append(b[(i + j) % n]); cb.append(c[(i + j) % n])
        boots.append(_r(bb[:n], cb[:n]))
    boots.sort()
    return {"corr": round(obs, 5), "n_overlap": n,
            "ci": [round(boots[int(0.025 * n_boot)], 5), round(boots[int(0.975 * n_boot)], 5)],
            "evidence": ("weak — a correlation ceiling on this few overlapping days cannot "
                         "discriminate a diversifier from a duplicate" if n < 30 else "usable"),
            "block": block, "n_boot": n_boot}


# =====================================================================================


def main() -> dict:
    raw = load()
    print(f"loaded {IN.name}: {sum(len(v) for v in raw['trades'].values())} trades over "
          f"{len(raw['trades'])} sleeves")
    records = to_records(raw)
    # keep the canonical symbol on the record so the book can rebuild the live intent
    for sleeve, rows in raw["trades"].items():
        by_key = {(r["symbol"], r["entry_utc"]): r for r in rows}
        for rec in records[sleeve]:
            src = by_key.get((rec.symbol, rec.entry_utc.isoformat()))
            if src:
                rec.features["symbol_canonical"] = src["symbol_canonical"]
                rec.features["decision_bar_iso"] = src["decision_bar_iso"]

    allowlist = build_symbol_allowlist()
    # `sub_xvol_pullback` and friends are absent from the LIVE allowlist because the live
    # config does not resolve them. Supplying no entry means the gate records the symbol
    # check as skipped for those sleeves rather than passing it silently; add them from the
    # research registry so the check is real for every sleeve judged.
    from src.components.ultimate_book.admission import effective_registry  # noqa: PLC0415
    from src.components.ultimate_book.symbol_map import (  # noqa: PLC0415
        build_broker_symbol_resolver,
    )
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    resolve = build_broker_symbol_resolver(prof)
    for name, spec in effective_registry(include_clean3=True).items():
        allowlist.setdefault(name, tuple(sorted({resolve(s) for s in (spec.symbols or ())})))

    judged = sorted(records)
    w_pilot = set()
    wp = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts/W_MX_PILOT.json"
    if wp.is_file():
        w_pilot = set(json.load(open(wp)).get("market_expansion_sleeves_live", []))
    # LOOK EVENTS, not distinct sleeves. An earlier revision computed
    # `len(set(judged) | w_pilot)`, and because all 12 of W's sleeves are re-judged here that
    # is exactly `len(judged)` — so `declared_family_size` added ZERO and the module's claim
    # to charge cross-session multiplicity was arithmetically a no-op. An adversarial refuter
    # measured the consequence: P(>=1 false admission | either session) 0.076-0.098 against
    # the 0.05 the option nominally controls.
    #
    # The right count is the number of TESTS, not the number of hypotheses: W looked at those
    # 12 once and this run looks at them again, and a second look at the same hypothesis is a
    # second chance to be wrong about it.
    declared = len(judged) + len(w_pilot)
    print(f"family: {len(judged)} sleeves judged here + {len(w_pilot)} prior looks in W's "
          f"pilot = declared_family_size {declared} LOOK EVENTS")

    gate_runs = run_estate_gate(records, allowlist, declared)

    # ---- 2. the merged book --------------------------------------------------------------
    spec_for_cost = OPTIONS["B_balanced"].with_(spec_id="x_book_cost")
    book_trades, restriction = priced_book_trades(records, spec_for_cost)
    base_rt = dict(yaml.safe_load(open(REPO / "config/agent_config.yaml"))
                   .get("gtos_vnext_runtime") or {})
    research_rt = dict(base_rt)
    research_rt["ultimate_book_include_clean3"] = True

    have = {s for s, v in book_trades.items() if v}
    compositions = {
        "live_armed3": [s for s in LIVE_ARMED3 if s in have],
        "armed4_intended": [s for s in ARMED4 if s in have],
        "core8_live": sorted(s for s in have if s in {
            "metals_core", "metals_softband", "crypto", "energy_agri", "idxrev",
            "metals_ob_micro", "fx_jpy", "fx_jpy_ny"}),
        "core8_plus_clean3": sorted(s for s in have if s in {
            "metals_core", "metals_softband", "crypto", "energy_agri", "idxrev",
            "metals_ob_micro", "fx_jpy", "fx_jpy_ny",
            "sub_xvol_pullback", "sub_mid_dn_revert", "vp_euidx_pocgrav"}),
        "armed4_plus_mx12": sorted(set(ARMED4) & have
                                   | {s for s in have if s.startswith("mx_")}),
        "everything_generatable": sorted(have),
    }
    books: dict[str, dict] = {}
    for label, sl in compositions.items():
        if not sl:
            continue
        for floating in ("none", "worst_case"):
            key = f"{label}|{floating}"
            books[key] = run_book(book_trades, research_rt, sl, key, floating)
            st = books[key]["dict"]["stats"]
            print(f"  book {key:38s} n={st['n_placed']:5d} ret={st['total_return_pct']:9.2f}% "
                  f"maxDD={st['max_drawdown_pct']:6.2f}% sharpe={st['book_daily_sharpe']:.4f}")

    # leave-one-out at BOOK level for the armed set, WITH the null it needs.
    # Refuter-measured: over four provably worthless and interchangeable sleeves a LOO names
    # a scapegoat 99.2% of the time at an average apparent damage of -0.385 annualised
    # Sharpe. A delta without an interval is not a finding.
    loo = {}
    base_key = "armed4_intended|none"
    if base_key in books:
        full = compositions["armed4_intended"]
        base_st = books[base_key]["dict"]["stats"]
        base_daily_x = book_daily_series(books[base_key]["result"], key="entry")
        for drop in full:
            keep = [s for s in full if s != drop]
            if not keep:
                continue
            r = run_book(book_trades, research_rt, keep, f"loo_minus_{drop}")
            st = r["dict"]["stats"]
            ci = paired_block_ci(base_daily_x, book_daily_series(r["result"], key="entry"))
            loo[drop] = {
                "without": st,
                "delta_return_pct": round(
                    base_st["total_return_pct"] - st["total_return_pct"], 3),
                "delta_maxdd_pct": round(
                    base_st["max_drawdown_pct"] - st["max_drawdown_pct"], 3),
                "delta_sharpe": round(
                    base_st["book_daily_sharpe"] - st["book_daily_sharpe"], 5),
                "paired_block_ci": ci,
                "supported": bool(ci.get("sharpe_delta_significant")),
            }
            sig = "SUPPORTED" if loo[drop]["supported"] else "not supported by its own CI"
            print(f"  LOO -{drop:22s} dRet={loo[drop]['delta_return_pct']:+9.2f}pp "
                  f"dDD={loo[drop]['delta_maxdd_pct']:+6.2f}pp "
                  f"dSharpe={loo[drop]['delta_sharpe']:+.5f}  [{sig}]")

    # composition ranking, WITH the same null. "Best of six" bought +0.527 annualised Sharpe
    # of pure winner's curse on a zero-edge estate in the refuter's simulation, so every
    # pairwise claim against the base composition carries an interval.
    comp_null = {}
    if base_key in books:
        base_daily_x = book_daily_series(books[base_key]["result"], key="entry")
        for key, r in books.items():
            if key == base_key or key.endswith("|worst_case"):
                continue
            comp_null[key] = paired_block_ci(
                book_daily_series(r["result"], key="entry"), base_daily_x)
        n_sig = sum(1 for v in comp_null.values() if v.get("sharpe_delta_significant"))
        print(f"  composition ranking vs {base_key}: {n_sig} of {len(comp_null)} "
              f"differences clear their own paired block-bootstrap CI")

    # ---- 3. the diversifier certification -------------------------------------------------
    base_res = books.get(base_key, books.get("live_armed3|none"))
    base_governed = book_daily_series(base_res["result"], key="entry")
    base_stats = book_stats(base_res["result"])
    base_sleeves = set(base_res["result"].config.sleeves)

    # THE BASE BOOK FOR THE DIVERSIFIER IS NOT THE GOVERNED EQUITY PATH, and that is a
    # correction to this driver's first revision rather than a preference.
    #
    # Measured: every composition runs into the FTMO max-drawdown ENTRY BLOCK
    # (`admission.py:1290-1292`, 9% against the STATIC 100k reference,
    # `governor_state.py:280-282`) and stops permanently. The armed-4 book placed 66 trades,
    # died in 2014 and produced a 63-day series — so 12 of the 22 years were never traded and
    # every candidate's overlap with it was 0 to 7 days. Correlations came back `nan`, and a
    # certification computed on that is a statement about the governor's halt, not about
    # diversification.
    #
    # `portfolio_contribution` asks a Fundamental-Law question about RETURN SERIES
    # (IR ~ IC x sqrt(breadth)); it takes `Dict[str, float]` of daily returns and has no
    # concept of an equity path. So the base book here is the confidence-weighted daily net R
    # of the armed sleeves, using the production `confidence_for` weights and the production
    # day panel — no governor, no compounding, no halt. The GOVERNED book is reported
    # separately, in `book`, because it answers a different and equally real question.
    from src.components.ultimate_book.admission import confidence_for  # noqa: PLC0415

    daily_panels: dict[str, dict] = {}
    for sleeve, recs in records.items():
        if not recs:
            continue
        priced, _c = price_trades(recs, spec_for_cost)
        d, _n = build_daily_panel(priced, spec_for_cost)
        if d.get(sleeve):
            daily_panels[sleeve] = d[sleeve]

    reg_all = effective_registry(include_clean3=True)
    base_daily: dict = {}
    weights = {}
    for s in sorted(base_sleeves):
        w = confidence_for(s, reg_all)
        weights[s] = w
        for day, r in (daily_panels.get(s) or {}).items():
            base_daily[day] = base_daily.get(day, 0.0) + w * r
    if not base_daily:
        base_daily = dict(base_governed)

    # sealed split: mechanical, book-level, outcome-independent — the 75% point of the BASE
    # BOOK's own calendar span, floored to a month start, and identical for every candidate.
    days = sorted(base_daily)
    if days:
        lo, hi = days[0], days[-1]
        cut = lo + dt.timedelta(days=int(0.75 * (hi - lo).days))
        sealed = dt.date(cut.year, cut.month, 1)
    else:
        sealed = dt.date(2024, 1, 1)
    print(f"\nbase book {sorted(base_sleeves)} weights={weights}")
    print(f"  confidence-weighted daily-R series: {len(base_daily)} trading days "
          f"{days[0]} .. {days[-1]}; sealed_start={sealed}")
    print(f"  (the GOVERNED equity-path book produced only {len(base_governed)} days before "
          f"the max-DD entry block halted it — reported separately, not used here)")

    # `portfolio_contribution` declares `Dict[str, float]` and `split_robust_contribution`
    # compares `d < sealed_start` directly (`:128-131`). With `datetime.date` keys and a
    # string `sealed_start` that raises TypeError; with date keys and a date sealed_start it
    # works but violates the declared contract. Both sides are put on ISO strings, which are
    # lexicographically ordered and are what the module says it takes.
    def _iso(d: dict) -> dict:
        return {k.isoformat() if hasattr(k, "isoformat") else str(k): v for k, v in d.items()}

    base_daily_iso = _iso(base_daily)
    sealed_iso = sealed.isoformat()

    certs: dict[str, dict] = {}
    # Per-sleeve evidence the raw certification cannot see. Computed once, from the same
    # priced/coverage pass the gate used, so the two doors are looking at one population.
    gate_rows = {r["sleeve"]: r for r in gate_runs["B_balanced"]["rows"]}
    for cand in sorted(daily_panels):
        if cand in base_sleeves:
            continue
        cd = daily_panels[cand]
        cd_iso = _iso(cd)
        edge = standalone_edge(cd)
        rc = regime_clean(cd, sealed)
        # The MEASURED merged book with the candidate in it — the candidate's presence also
        # changes the Kelly conviction count and what the gross cap sheds, so this is
        # stronger than a synthetic blend.
        with_cand = run_book(book_trades, research_rt,
                             sorted(base_sleeves | {cand}), f"base_plus_{cand}")
        priced_c, cov_c = price_trades(records[cand], spec_for_cost)
        cov = cov_c.get(cand)
        all_net = [p.r_net for p in priced_c if p.status == "priced" and p.r_net is not None]
        row = gate_rows.get(cand, {})
        ev = DiversifierEvidence(
            sleeve=cand,
            gate_verdict=str(row.get("verdict") or "UNKNOWN"),
            gate_reasons=(str(row.get("first_reason") or ""),),
            coverage_frac=float(cov.coverage_frac if cov else 0.0),
            coverage_floor=float(spec_for_cost.cost_coverage_floor),
            blackout_r_gross=float(cov.blackout_r_gross if cov else 0.0),
            n_blackout_trades=int(cov.n_blackout_dropped if cov else 0),
            lifetime_mean_r=(math.fsum(all_net) / len(all_net)) if all_net else float("nan"),
            n_trades_total=int(cov.n_total if cov else 0),
            n_trades_priced=len(all_net),
            base_book_stats=base_stats,
            with_candidate_book_stats=with_cand["dict"]["stats"],
            with_candidate_rejections=with_cand["dict"]["rejections"],
            # Both books halting on the max-DD entry block makes the return comparison a
            # statement about the governor, not about the candidate. Measured: at the live
            # 2.0% ceiling dial EVERY composition halts, so this is False for this whole run
            # and the guard refuses on ABSENT rather than adverse evidence.
            book_evidence_informative=not (
                _halted(base_res["dict"]) and _halted(with_cand["dict"])),
        )
        g = certify_guarded(
            base_daily_iso, cd_iso, ev,
            standalone_edge_ok=bool(edge.get("ok")),
            regime_clean=bool(rc.get("ok")),
            sealed_start=sealed_iso, weight=0.5, corr_ceiling=0.35, n_boot=3000,
        )
        out_c = g.as_dict()
        out_c["standalone_edge_detail"] = edge
        out_c["regime_detail"] = rc
        out_c["correlation_detail"] = corr_ci(base_daily_iso, cd_iso)
        certs[cand] = out_c
        chk = g.raw["checks"]
        cr = chk["low_correlation"]["corr"]
        print(f"  cert {cand:42s} {g.verdict:22s} "
              f"dSharpe={g.raw['incremental']['delta']:+.5f} "
              f"corr={(cr if cr is not None else float('nan')):+.3f} "
              f"n_ov={chk['low_correlation']['n_overlap']:5d} "
              f"raw_failed={g.raw['failed_checks']} guards_failed={g.failed_guards}")

    # a sanity floor: the same test run on the base book's OWN members must not certify them
    # as diversifiers of themselves (corr 1.0 by construction) — a cheap control that the
    # correlation ceiling is doing work.
    self_control = {}
    for s in sorted(base_sleeves):
        if s not in daily_panels:
            continue
        c = certify_diversifier(base_daily_iso, _iso(daily_panels[s]), standalone_edge_ok=True,
                                regime_clean=True, sealed_start=sealed_iso,
                                weight=0.5, corr_ceiling=0.35, n_boot=500)
        self_control[s] = {"verdict": c["verdict"], "corr": c["corr_to_book"],
                           "failed": c["failed_checks"]}

    out = {
        "schema": "gtos.walkforward.estate_walk.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase5/receipts/x_estate_walk.py",
        "source": str(IN.relative_to(REPO)),
        "source_generated_by": raw.get("generated_by"),
        "research_overrides": raw.get("research_overrides"),
        "family": {
            "judged_here": judged,
            "w_pilot_mx_sleeves": sorted(w_pilot),
            "declared_family_size_wave5_union": declared,
            "fidelity_refused": raw.get("fidelity_refused_sleeves"),
        },
        "gate": gate_runs,
        "book": {
            "compositions": compositions,
            "universe_restriction": restriction,
            "runs": {k: v["dict"] for k, v in books.items()},
            "leave_one_out_armed4": loo,
            "composition_vs_base_paired_ci": comp_null,
            "sealed_start": sealed.isoformat(),
            "base_book": {"sleeves": sorted(base_sleeves), "stats": base_stats,
                          "n_trading_days": len(base_daily)},
        },
        "diversifier": {
            "module": "src/research_infra/validation_integrity/portfolio_contribution.py",
            "base_book_basis": (
                "confidence-weighted daily net R of the armed sleeves (admission.confidence_for "
                "weights, walkforward.panel.build_daily_panel days) — NOT the governed equity "
                "path, which halts at the max-DD entry block after 63 trading days and would "
                "make every overlap 0-7 days."),
            "base_book_weights": weights,
            "base_book_n_days": len(base_daily),
            "governed_base_book_n_days": len(base_governed),
            "weight": 0.5, "corr_ceiling": 0.35,
            "no_risk_regression_basis": (
                "MEASURED max-drawdown delta of the REAL merged book with the candidate in "
                "it, not a synthetic blend — so the candidate's effect on the Kelly "
                "conviction count and on what the gross cap sheds is included."),
            "guards": ("src/research_infra/walkforward/diversifier.py — nine refusals the raw "
                       "certification cannot make for itself. An adversarial refuter reached "
                       "CERTIFIED_DIVERSIFIER on a sleeve that lost 8,583.8 R without them."),
            "certifications": certs,
            "self_control": self_control,
        },
        "cost_look_ahead": {
            "measured_window": ["2026-06-18", "2026-07-24"],
            "applied_to": "every trade in a 2004-2026 panel",
            "direction": "spreads compressed; pre-2026 trades are UNDER-costed, so every net "
                         "number here is optimistic by an unmeasured amount",
        },
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    main()
