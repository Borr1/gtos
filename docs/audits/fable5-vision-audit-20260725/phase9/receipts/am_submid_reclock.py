"""Re-derive `sub_mid_dn_revert` on the repaired session clock — generation, gate, carry tier.

    python3 docs/audits/fable5-vision-audit-20260725/phase9/receipts/am_submid_reclock.py
    AM_STAGE=generate|gate|carry python3 .../am_submid_reclock.py     # one stage at a time

WHY A RE-DERIVATION AND NOT A RESCALE
--------------------------------------
`substrate._session_hour` read the raw UTC hour until B1200 and `substrate_engine._bucket_session`
cuts it on 8/16 — boundaries copied from a route that parsed naive MT5 CSV stamps, i.e. BROKER wall
clock. `sub_mid_dn_revert` carries `session=ny` as one of seven cell conditions, so the bucket is
part of its firing rule and the repair changes **which trades exist**.

Measured on the archive's grid: H4 opens are server 00/04/08/12/16/20 and exactly three change
bucket, so `session=ny` moves from server {20, 00} to server {16, 20}. The two populations share
only the server-20 bars. Every downstream number therefore has to be re-derived:

  * `AA_ESTATE_TRADES.json.gz` holds 503 trades at +0.3996 R/trade gross — on the wrong clock;
  * `AA_ESTATE_WALK.json`'s verdict and q for the sleeve — on the wrong clock;
  * `EXIT_FRONTIER_V1.json`'s frontier for the sleeve — on the wrong clock;
  * `SURVIVOR_BOOK_V1.json`'s CARRY_CONDITIONAL tier and AD's B753 UNCONDITIONAL restatement of it
    — the restatement's `nights_measured` come from AA's holds, i.e. from the wrong clock.

THE CONTROL THAT MAKES THE A/B A MEASUREMENT
---------------------------------------------
The `authored_utc` arm is generated through the SAME driver with `supply.authored_clock("substrate")`
and is then checked trade-for-trade against AA's own 503 rows on count and summed R. If that parity
holds, the only thing separating the two arms is the clock — the driver, the grid, the reachability
rule, the labelling and the exit contract are all identical by construction. This is AH's
`parity_vs_af` discipline applied to a clock instead of an entry instant.

Generation goes through `GenerationPort` on the same union H4 close grid AA used, over the same
symbol set (all nine H4 sleeves' surfaces), because engine reachability depends on which other
symbols share the launcher — restricting the grid to this sleeve's own 18 symbols would change which
bars are reachable and break the parity that makes the A/B readable.

Offline and pure: reads gzipped CSV bars through `CsvBarSource`, imports no broker module, and does
not touch `config/agent_config.yaml` (the clean_3 flag is flipped in the config DICT handed to
`GenerationPort`, exactly as AA did it — the file is H1-bound and the live token binds its digest).
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import os
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"))

import yaml  # noqa: E402

import ad_carry_tiers as ADC  # noqa: E402  — the tier rule, imported so it is ONE implementation
import ad_exit_sweep as ADX  # noqa: E402  — allowlist + TradeRecord conversion
import aa_estate_generate as AA  # noqa: E402  — the estate generation path, verbatim
from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_H4  # noqa: E402
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.sleeves.registry import active_specs  # noqa: E402
from src.components.ultimate_book.book_engine import (  # noqa: E402
    _candidate_book_sleeves,
    _market_expansion_sleeves,
)
from src.components.ultimate_book.sleeves._server_clock import server_hour  # noqa: E402
from src.costs import load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import supply as SUP  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.stats import benjamini_hochberg  # noqa: E402

SLEEVE = "sub_mid_dn_revert"
CLOCKS = ("server_repaired", "authored_utc")

AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
AA_WALK = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_WALK.json"
AD_FRONTIER = REPO / ("docs/audits/fable5-vision-audit-20260725/phase7/receipts/"
                      "EXIT_FRONTIER_V1.json")
AD_TIERS = REPO / ("docs/audits/fable5-vision-audit-20260725/phase7/receipts/"
                   "AD_CARRY_TIERS_RESTATED_V1.json")
FAMILY_DECL = REPO / ("docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                      "CANDIDATE_FAMILY_V1.json")

OUT_TRADES = HERE / "AM_SUBMID_TRADES.json.gz"
OUT = HERE / "SUBMID_RECLOCK_V1.json"

SERVER = "FTMO-Server3"
#: AA's declared bill, held so the verdict is an A/B against `AA_ESTATE_WALK.json`. The wave-8
#: declared family (`CANDIDATE_BOOK_V1` = 32) is reported beside it, and so is AF's 276.
AA_DECLARED = 69


# =====================================================================================
# generation
# =====================================================================================

def _h4_grid_and_port(overrides: dict):
    """AA's H4 union close grid and a `GenerationPort` built on AA's own config dict.

    Replicated from `aa_estate_generate.main` rather than imported because AA builds the grid
    inline. The symbol set is the union of every H4 sleeve's surface — NOT this sleeve's 18 —
    because `engine_reachable` depends on which symbols share the launcher (AF §1.2), so a
    narrower grid would silently change which bars are reachable and break the AA parity.
    """
    cfg, prof, res, files, src, port = AA.build(overrides)
    active = set(port.active_sleeve_names())
    surface_of: dict[str, tuple] = {}
    tf_of: dict[str, int] = {}
    for spec in active_specs(
        None,
        include_candidate_book=bool(cfg.get("ultimate_book_include_candidate_book", False)),
        candidate_book_sleeves=_candidate_book_sleeves(cfg) or None,
        include_market_expansion_book=bool(
            cfg.get("ultimate_book_include_market_expansion_book", False)),
        market_expansion_sleeves=_market_expansion_sleeves(cfg) or None,
    ):
        if spec.tag in active:
            tf_of[spec.tag] = spec.timeframe
            surface_of[spec.tag] = tuple(spec.on_surface)
    h4 = sorted(s for s, t in tf_of.items() if t == TF_H4)
    wanted = {res(s) for name in h4 for s in surface_of[name]}

    series: dict[tuple, tuple[list[Bar], list[dt.datetime]]] = {}
    index: dict[tuple, dict[dt.datetime, int]] = {}
    stamps: set[dt.datetime] = set()
    for key in files:
        if key[1] != TF_H4:
            continue
        rows = src._load(key)
        if not rows:
            continue
        bars = [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
                for r in rows]
        times = [dt.datetime.fromisoformat(r["time"]) for r in rows]
        series[key] = (bars, times)
        index[key] = {ts: i for i, ts in enumerate(times)}
        if key[0] in wanted:
            stamps.update(times)
    grid = sorted(t + dt.timedelta(minutes=240) for t in stamps)
    return port, res, series, index, grid, h4


def _label(c, series, index, res) -> dict | None:
    """AA's labelling for this sleeve, verbatim: stop/target/MAXBARS-80 on H4 bars."""
    key = (res(c.symbol), TF_H4)
    if key not in index or not c.decision_bar_iso:
        return None
    i = index[key].get(dt.datetime.fromisoformat(c.decision_bar_iso))
    bars, times = series[key]
    if i is None or i + 2 >= len(bars):
        return None
    pol = ExitPolicy(target_dist=c.target_dist, maxbars=AA.MAXBARS, label="plain")
    pr = replay(bars, i, c.direction, stop_dist=c.stop_dist, policy=pol)
    ivl = dt.timedelta(minutes=240)
    entry_utc = times[i] + ivl
    return {
        "sleeve": SLEEVE,
        "symbol": res(c.symbol),
        "symbol_canonical": c.symbol,
        "entry_utc": entry_utc.isoformat(),
        "exit_utc": (times[pr.exit_index] + ivl).isoformat(),
        "direction": int(c.direction),
        "sl_distance_price": float(c.stop_dist),
        "entry_price": float(bars[i].c),
        "r_gross": float(winsorize_R(pr.r_gross)),
        "r_gross_plain": float(winsorize_R(pr.r_gross)),
        "exit_policy": "plain",
        "exit_reason": pr.exit_reason,
        "mfe_r": round(pr.mfe_r, 6),
        "mae_r": round(pr.mae_r, 6),
        "bars_to_mfe": int(pr.bars_to_mfe),
        "timeframe": int(TF_H4),
        "decision_bar_iso": c.decision_bar_iso,
        "decision_day": c.decision_day,
        "target_dist": (float(c.target_dist) if c.target_dist else None),
        "intra_size": float(c.intra_size or 1.0),
        "exit_bar_offset": int(pr.exit_index - i),
        "hold_hours": round((pr.exit_index - i) * 4.0, 4),
        "decision_bar_server_hour": server_hour(times[i]),
        "decision_bar_utc_hour": times[i].hour,
        "entry_server_hour": server_hour(entry_utc),
        "entry_utc_hour": entry_utc.hour,
    }


def _summary(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    r = [x["r_gross"] for x in rows]
    return {
        "n": len(rows),
        "mean_r_gross": round(statistics.fmean(r), 6),
        "sum_r_gross": round(sum(r), 3),
        "median_r_gross": round(statistics.median(r), 6),
        "win_frac": round(sum(1 for x in r if x > 0) / len(r), 5),
        "mean_mfe_r": round(statistics.fmean(x["mfe_r"] for x in rows), 5),
        "mean_mae_r": round(statistics.fmean(x["mae_r"] for x in rows), 5),
        "capture_ratio": (round(statistics.fmean(r) / statistics.fmean(x["mfe_r"] for x in rows), 5)
                          if statistics.fmean(x["mfe_r"] for x in rows) else None),
        "median_hold_hours": round(statistics.median(x["hold_hours"] for x in rows), 4),
        "p90_hold_hours": round(ADC.q([x["hold_hours"] for x in rows], 0.90), 4),
        "first": min(x["entry_utc"] for x in rows)[:10],
        "last": max(x["entry_utc"] for x in rows)[:10],
        "n_long": sum(1 for x in rows if x["direction"] > 0),
        "n_short": sum(1 for x in rows if x["direction"] < 0),
        "exit_reasons": dict(collections.Counter(x["exit_reason"] for x in rows)),
        "decision_bar_server_hours": dict(sorted(collections.Counter(
            x["decision_bar_server_hour"] for x in rows).items())),
        "entry_server_hours": dict(sorted(collections.Counter(
            x["entry_server_hour"] for x in rows).items())),
        "by_symbol": dict(sorted(collections.Counter(
            x["symbol_canonical"] for x in rows).items())),
        "mean_r_gross_by_symbol": {
            s: round(statistics.fmean(x["r_gross"] for x in rows
                                      if x["symbol_canonical"] == s), 5)
            for s in sorted({x["symbol_canonical"] for x in rows})},
    }


def _key(rows: list[dict]) -> set[tuple]:
    return {(r["symbol_canonical"], r["decision_bar_iso"], r["direction"]) for r in rows}


def do_generate() -> dict:
    t_start = time.time()
    overrides = {"ultimate_book_include_clean3": True}
    port, res, series, index, grid, h4 = _h4_grid_and_port(overrides)
    print(f"H4 sleeves in the active book: {h4}")
    print(f"H4 union grid: {len(grid)} closes {grid[0].date()} .. {grid[-1].date()}")

    arms: dict[str, list[dict]] = {}
    for clock in CLOCKS:
        t0 = time.time()
        ctx = (SUP.authored_clock("substrate") if clock == "authored_utc"
               else _nullcontext())
        rows: list[dict] = []
        seen: set = set()
        with ctx:
            for n, ts in enumerate(grid):
                for c in port.generate(ts, tags=[SLEEVE]).candidates:
                    k = (c.sleeve, c.symbol, c.decision_bar_iso)
                    if k in seen:
                        continue
                    seen.add(k)
                    row = _label(c, series, index, res)
                    if row is not None:
                        rows.append(row)
                if (n + 1) % 10000 == 0:
                    el = time.time() - t0
                    print(f"    [{clock}] {n+1}/{len(grid)} {el:.0f}s "
                          f"eta {el/(n+1)*(len(grid)-n-1):.0f}s kept={len(rows)}", flush=True)
        rows.sort(key=lambda r: r["entry_utc"])
        arms[clock] = rows
        print(f"  {clock:16s} {len(rows):5d} trades in {time.time()-t0:.0f}s", flush=True)

    art = {
        "schema": "gtos.am.submid_reclock_trades.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "session": "AM", "blocks": "B1200-B1249",
        "sleeve": SLEEVE,
        "bars_archive": AA.BARS,
        "maxbars": AA.MAXBARS,
        "research_overrides": {"config": overrides, "why": (
            "config/agent_config.yaml:1270 sets ultimate_book_include_clean3: false. Flipped in "
            "the config DICT handed to GenerationPort; the file on disk is untouched.")},
        "h4_grid": {"n_closes": len(grid), "first": grid[0].isoformat(),
                    "last": grid[-1].isoformat(), "symbol_surface_from_sleeves": h4},
        "clocks": {
            "server_repaired": ("substrate._session_hour -> _server_clock.server_hour (B1200). "
                                "The clock the cell was mined on."),
            "authored_utc": ("substrate._session_hour reverted to the raw UTC hour via "
                             "walkforward.supply.authored_clock('substrate'). What the sleeve "
                             "would have done live before B1200."),
        },
        "n_by_clock": {k: len(v) for k, v in arms.items()},
        "seconds": round(time.time() - t_start, 1),
        "trades": arms,
    }
    with gzip.open(OUT_TRADES, "wt") as fh:
        json.dump(art, fh)
    print(f"wrote {OUT_TRADES.relative_to(REPO)} "
          f"({OUT_TRADES.stat().st_size/1e6:.1f} MB) in {art['seconds']}s")
    return art


class _nullcontext:
    def __enter__(self):
        return None

    def __exit__(self, *a):
        return False


# =====================================================================================
# the A/B, and the control against AA
# =====================================================================================

def parity_vs_aa(arms: dict[str, list[dict]]) -> dict:
    """The `authored_utc` arm must BE AA's population for this sleeve.

    Checked on count, summed R and the trade KEY set. If this holds, the driver reproduces AA
    exactly under the old clock, so the whole A/B is attributable to the clock and to nothing
    about how this script walks the archive.
    """
    aa = json.load(gzip.open(AA_IN, "rt"))["trades"][SLEEVE]
    mine = arms["authored_utc"]
    ka, km = _key(aa), _key(mine)
    return {
        "n_aa": len(aa), "n_mine": len(mine),
        "exact_count": len(aa) == len(mine),
        "sum_r_aa": round(sum(t["r_gross"] for t in aa), 6),
        "sum_r_mine": round(sum(t["r_gross"] for t in mine), 6),
        "exact_sum_r": abs(sum(t["r_gross"] for t in aa)
                           - sum(t["r_gross"] for t in mine)) < 1e-6,
        "trade_keys_identical": ka == km,
        "n_only_aa": len(ka - km), "n_only_mine": len(km - ka),
        "only_aa_sample": sorted(f"{s}|{b}|{d}" for s, b, d in list(ka - km))[:8],
        "only_mine_sample": sorted(f"{s}|{b}|{d}" for s, b, d in list(km - ka))[:8],
        "why": ("AA generated this sleeve through the same GenerationPort on the same grid, on the "
                "raw-UTC clock. Reproducing it exactly is what makes the clock the only "
                "difference between the two arms."),
    }


def clock_ab(arms: dict[str, list[dict]]) -> dict:
    rep, aut = arms["server_repaired"], arms["authored_utc"]
    kr, ka = _key(rep), _key(aut)
    shared = kr & ka
    by_key_r = {(r["symbol_canonical"], r["decision_bar_iso"], r["direction"]): r for r in rep}
    by_key_a = {(r["symbol_canonical"], r["decision_bar_iso"], r["direction"]): r for r in aut}
    shared_r = [by_key_r[k]["r_gross"] for k in sorted(shared)]
    shared_a = [by_key_a[k]["r_gross"] for k in sorted(shared)]
    only_r = [by_key_r[k] for k in sorted(kr - ka)]
    only_a = [by_key_a[k] for k in sorted(ka - kr)]
    return {
        "server_repaired": _summary(rep),
        "authored_utc": _summary(aut),
        "n_shared": len(shared),
        "n_only_repaired": len(kr - ka),
        "n_only_authored": len(ka - kr),
        "jaccard": round(len(shared) / max(1, len(kr | ka)), 5),
        "shared_trades_are_identical_r": (
            all(abs(a - b) < 1e-9 for a, b in zip(shared_r, shared_a))),
        "shared_mean_r_gross": (round(statistics.fmean(shared_r), 6) if shared_r else None),
        "only_repaired_mean_r_gross": (round(statistics.fmean(x["r_gross"] for x in only_r), 6)
                                       if only_r else None),
        "only_authored_mean_r_gross": (round(statistics.fmean(x["r_gross"] for x in only_a), 6)
                                       if only_a else None),
        "only_repaired_server_hours": dict(sorted(collections.Counter(
            x["decision_bar_server_hour"] for x in only_r).items())),
        "only_authored_server_hours": dict(sorted(collections.Counter(
            x["decision_bar_server_hour"] for x in only_a).items())),
        "what": ("the repair moves the session=ny bucket from server {20, 00} to server {16, 20}, "
                 "so the shared set is exactly the server-20 bars and each arm carries one "
                 "exclusive hour. A shared trade is byte-identical in both arms by construction "
                 "(same decision bar, same geometry, same labelling), which is the check above."),
    }


# =====================================================================================
# the gate
# =====================================================================================

def _verdict_row(sv) -> dict:
    d = sv.diagnostics or {}
    cd = d.get("cost_decomposition") or {}
    hold = d.get("holds") or {}
    exc = d.get("excursion") or {}
    return {
        "verdict": sv.verdict.value,
        "n_trades": sv.n_trades,
        "pooled_oos_mean_r": sv.pooled_oos_mean_r,
        "p_raw": sv.p_raw, "q_value": sv.q_value,
        "gates": {g: bool(v.get("pass")) for g, v in sorted(sv.gates.items())},
        "failing_gates": [g for g in ("expectancy", "lifetime", "stability", "robustness",
                                      "significance")
                          if not sv.gates.get(g, {}).get("pass")],
        "oos_positive_fold_frac": sv.gates.get("stability", {}).get("oos_positive_fold_frac"),
        "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
        "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
        "coverage_frac": sv.gates.get("cost_coverage", {}).get("coverage_frac"),
        "oos_mean_r_per_trade": sv.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
        "lifetime_mean_r_per_trade": sv.gates.get("lifetime", {}).get(
            "mean_r_net_per_trade_all_folds"),
        "mean_gross_r": cd.get("mean_gross_r"),
        "mean_cost_r": cd.get("mean_cost_r"),
        "cost_pct_of_abs_gross": cd.get("cost_pct_of_abs_gross"),
        "largest_cost_term": cd.get("largest_term"),
        "cost_terms_mean_r": {k: (v or {}).get("mean_r")
                              for k, v in sorted((cd.get("terms") or {}).items())},
        "median_hold_hours": hold.get("median_hours"),
        "mean_mfe_r": exc.get("mean_mfe_r"),
        "capture_ratio_pooled": exc.get("capture_ratio_pooled"),
        "by_fold": (d.get("by_fold") or {}),
        "by_symbol": (d.get("by_symbol") or {}),
        "primary_prescription": d.get("primary_prescription"),
        "prescriptions": d.get("prescriptions"),
        "fidelity": sv.fidelity,
        "reasons": list(sv.reasons),
    }


def _q_at(p_by: dict, alpha: float, n_judged: int, m: int) -> dict:
    """BH q at one declared family size, padded exactly as `gate.py:797-799` pads.

    Reproduced rather than approximated: the gate corrects at `max(n_judged, declared_family_size)`
    and carries the difference at `p = 1.0`, so a sleeve that never reached a null cannot shrink the
    family. AK's `ak_supply_gate.q_at`, same arithmetic.
    """
    names = [s for s, v in p_by.items() if v is not None]
    eff = max(n_judged, m)
    padded = [p_by[s] for s in names] + [1.0] * (eff - len(names))
    corr = benjamini_hochberg(padded, alpha)
    return {s: {"q": corr["qvalues"][i], "rejected": bool(corr["rejected"][i]),
                "family_size": corr["m"]}
            for i, s in enumerate(names)}


def do_gate_solo(arms: dict[str, list[dict]]) -> dict:
    """Gate THIS SLEEVE ALONE under both clocks, with the family-comparable BH q reconstructed.

    Why this and not the whole 32-sleeve family: the family run is what makes a q directly comparable
    to `AA_ESTATE_WALK.json`, and it costs ~30 machine-minutes per clock because it re-diagnoses the
    other 31 sleeves — which this session does not change. Every per-sleeve verdict input (expectancy,
    lifetime, stability, robustness, coverage, `p_raw` and the whole diagnostics block) is computed
    from that sleeve's own trades and is independent of its siblings; only `q_value` and the
    `significance` gate read the family. So the sleeve is gated alone at the same option and the same
    `declared_family_size`, and the comparable q is rebuilt from AA's OWN published p-values for the
    other 31 sleeves with the gate's padding rule.

    The control that makes this legitimate: the `authored_utc` arm must reproduce AA's published
    verdict for this sleeve exactly. It does — pooled and `p_raw` to full precision, and q 1.0.
    """
    costs = load_broker_true_costs(ADC.COSTS)
    base = OPTIONS["B_balanced"]
    aa_rows = {r["sleeve"]: r for r in
               json.loads(AA_WALK.read_text())["runs"]["B_balanced|v1_1"]["rows"]}
    fam_decl = CF.load_candidate_family(FAMILY_DECL)
    declared_v8 = fam_decl.family("CANDIDATE_BOOK_V1").size_for(CF.ALL_DECLARED)
    runs: dict[str, dict] = {}
    for clock in CLOCKS:
        spec = base.with_(spec_id=f"{base.spec_id}_am_submid_solo_{clock}",
                          sleeve_symbol_allowlist={SLEEVE: ADX.allowlist()[SLEEVE]},
                          declared_family_size=AA_DECLARED)
        t0 = time.time()
        res = run_gate({SLEEVE: ADX.to_records(arms[clock])}, spec, costs=costs,
                       diagnose=True, server=SERVER)
        sv = res.verdicts[SLEEVE]
        row = _verdict_row(sv)
        row.update({"clock": clock, "seconds": round(time.time() - t0, 2),
                    "spec_id": spec.spec_id, "spec_sha256": spec.seal(),
                    "declared_family_size": AA_DECLARED})
        p_by = {s: r.get("p_raw") for s, r in aa_rows.items() if s != SLEEVE}
        p_by[SLEEVE] = sv.p_raw
        n_judged = sum(1 for v in p_by.values() if v is not None)
        for alpha in (0.05, 0.10, 0.20):
            row[f"q_in_aa_family_alpha_{alpha}"] = _q_at(p_by, alpha, n_judged,
                                                         AA_DECLARED).get(SLEEVE)
        if sv.p_raw:
            row["multiplicity_sensitivity"] = CF.sensitivity(
                sv.p_raw, (declared_v8, AA_DECLARED, 276))
            row["max_family_that_admits"] = {
                str(a): CF.max_size_that_admits(sv.p_raw, a) for a in (0.05, 0.10, 0.20)}
        runs[clock] = row
        print(f"  {clock:16s} {row['verdict']:8s} n {row['n_trades']:4d} pooled "
              f"{row['pooled_oos_mean_r']} p {row['p_raw']} folds+ "
              f"{row['oos_positive_fold_frac']} failing {row['failing_gates']}", flush=True)
    a = runs["authored_utc"]
    pub = aa_rows.get(SLEEVE) or {}
    control = {
        "aa_published": {k: pub.get(k) for k in
                         ("verdict", "pooled_oos_mean_r", "p_raw", "q_value", "n_trades")},
        "authored_arm_here": {"verdict": a["verdict"], "pooled_oos_mean_r": a["pooled_oos_mean_r"],
                              "p_raw": a["p_raw"], "n_trades": a["n_trades"]},
        "verdict_identical": a["verdict"] == pub.get("verdict"),
        "pooled_identical": (pub.get("pooled_oos_mean_r") is not None
                             and abs(a["pooled_oos_mean_r"] - pub["pooled_oos_mean_r"]) < 1e-12),
        "p_identical": (pub.get("p_raw") is not None
                        and abs(a["p_raw"] - pub["p_raw"]) < 1e-12),
        "why": ("this is what makes a 1-sleeve gate legitimate as a stand-in for the family run: the "
                "authored-clock arm reproduces AA's own published verdict for this sleeve to full "
                "precision, so the only thing the repaired arm changes is the clock"),
    }
    print(f"  control vs AA: verdict {control['verdict_identical']}, "
          f"pooled {control['pooled_identical']}, p {control['p_identical']}")
    return {
        "gate": {"option": "B_balanced", "account": base.account, "server": SERVER,
                 "cost_artifact": str(ADC.COSTS.relative_to(REPO)),
                 "scope": "SOLO — this sleeve alone; see do_gate_solo's docstring",
                 "declared_family_size": AA_DECLARED,
                 "declared_family_v8": {"family_id": "CANDIDATE_BOOK_V1", "size": declared_v8,
                                        "sha256": fam_decl.sha256}},
        "control_vs_aa": control,
        "runs": runs,
    }


def do_gate(arms: dict[str, list[dict]]) -> dict:
    """Both clocks through `run_gate(..., diagnose=True)` inside AA's own 32-sleeve family."""
    aa = json.load(gzip.open(AA_IN, "rt"))
    costs = load_broker_true_costs(ADC.COSTS)
    base = OPTIONS["B_balanced"]
    fam = CF.load_candidate_family(FAMILY_DECL)
    declared_v8 = fam.family("CANDIDATE_BOOK_V1").size_for(CF.ALL_DECLARED)
    nt = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    print(f"declared: AA {AA_DECLARED}; CANDIDATE_BOOK_V1 {declared_v8}; "
          f"measured n_trials {nt['n_trials']}")

    runs: dict[str, dict] = {}
    for clock in CLOCKS:
        rows = {s: list(v) for s, v in aa["trades"].items()}
        rows[SLEEVE] = arms[clock]
        spec = base.with_(spec_id=f"{base.spec_id}_am_submid_{clock}",
                          sleeve_symbol_allowlist=ADX.allowlist(),
                          declared_family_size=AA_DECLARED)
        t0 = time.time()
        res = run_gate({s: ADX.to_records(v) for s, v in rows.items()},
                       spec, costs=costs, diagnose=True, server=SERVER)
        sv = res.verdicts.get(SLEEVE)
        # Parity on the OTHER 31 sleeves: their rows are untouched, so anything that moves moved
        # because this sleeve's rows changed the family's BH ranks — which the report must say.
        aa_rows = {r["sleeve"]: r for r in
                   json.loads(AA_WALK.read_text())["runs"]["B_balanced|v1_1"]["rows"]}
        moved = {}
        for s, v in res.verdicts.items():
            if s == SLEEVE or s not in aa_rows:
                continue
            a = aa_rows[s]
            if a["verdict"] != v.verdict.value or (
                    a.get("q_value") is not None and v.q_value is not None
                    and abs(a["q_value"] - v.q_value) > 1e-9):
                moved[s] = {"aa_verdict": a["verdict"], "here": v.verdict.value,
                            "aa_q": a.get("q_value"), "here_q": v.q_value}
        runs[clock] = {
            "spec_id": spec.spec_id, "spec_sha256": spec.seal(),
            "declared_family_size": AA_DECLARED,
            "seconds": round(time.time() - t0, 1),
            "sleeve": (_verdict_row(sv) if sv else None),
            "family_admitted": sorted(res.admitted),
            "n_other_sleeves_moved_vs_aa": len(moved),
            "other_sleeves_moved_vs_aa": moved,
        }
        print(f"  {clock:16s} verdict {runs[clock]['sleeve']['verdict'] if sv else 'ABSENT'} "
              f"pooled {runs[clock]['sleeve']['pooled_oos_mean_r'] if sv else None} "
              f"p {runs[clock]['sleeve']['p_raw'] if sv else None} "
              f"({len(moved)} siblings moved)", flush=True)

    # the multiplicity surface, so the verdict does not depend on a typed number
    p_rep = (runs["server_repaired"]["sleeve"] or {}).get("p_raw")
    sens = (CF.sensitivity(p_rep, (declared_v8, AA_DECLARED, 276, int(nt["n_trials"])))
            if p_rep else [])
    return {
        "gate": {"option": "B_balanced", "account": base.account, "server": SERVER,
                 "cost_artifact": str(ADC.COSTS.relative_to(REPO)),
                 "family": ("AA's 32 sleeves at AA's declared_family_size=69, with only this "
                            "sleeve's rows swapped — so the verdict is an A/B against "
                            "AA_ESTATE_WALK.json"),
                 "declared_family_v8": {"family_id": "CANDIDATE_BOOK_V1", "size": declared_v8,
                                        "sha256": fam.sha256},
                 "n_trials_measured": int(nt["n_trials"])},
        "runs": runs,
        "multiplicity_sensitivity_repaired_clock": sens,
        "max_family_that_admits_repaired": (
            {str(a): CF.max_size_that_admits(p_rep, a) for a in (0.05, 0.10, 0.20)}
            if p_rep else None),
    }


# =====================================================================================
# the carry tier
# =====================================================================================

def do_carry(arms: dict[str, list[dict]]) -> dict:
    """AD's B753 restatement, re-run per clock with only this sleeve's holds replaced.

    `ad_carry_tiers`' rule and helpers are imported, not reimplemented, so a difference here is a
    difference in the holds. AD's own published row is carried alongside as the third column: it
    used AA's holds, which are the authored-clock holds, so the `authored_utc` column here should
    reproduce it — and that reproduction is the control on this half.
    """
    book = json.loads(ADC.BOOK.read_text())
    costs_doc = json.loads(ADC.COSTS.read_text())
    ad_published = {k: v for k, v in json.loads(AD_TIERS.read_text())["rows"].items()
                    if v.get("sleeve") == SLEEVE}

    out: dict = {"rows": {}, "ad_published_rows": ad_published,
                 "method": {
                     "changed": "charged swap nights only, from THIS clock's holds",
                     "held_fixed": ["gross_r", "true_cost_ex_swap_r", "swap_r_per_night",
                                    "the tier rule itself"],
                     "tier_rule_source": ("scripts/recost_w7_validation.py:1062-1073 via "
                                          "ad_carry_tiers.tier_of — imported, not reimplemented"),
                     "population_caveat": (
                         "the edge terms are the survivor book's, measured on the W7 validation "
                         "CACHES, which were built on the AUTHORED clock. The holds are this "
                         "clock's. So the repaired column mixes a repaired hold distribution with "
                         "an unrepaired edge estimate — strictly better than the modelled "
                         "held-to-horizon night count it replaces, and NOT a single-population "
                         "measurement. Stated because it is the load-bearing weakness."),
                 }}
    for clock in CLOCKS:
        rows = arms[clock]
        per_acct: dict[str, list[float]] = {"FTMO": [], "redacted_account": []}
        for r in rows:
            entry = dt.datetime.fromisoformat(r["entry_utc"])
            hold = float(r["hold_hours"])
            for acct in ("FTMO", "redacted_account"):
                wd = ADC.swap3(costs_doc, acct, r["symbol"])
                per_acct[acct].append(ADC.rollover_nights(
                    entry, hold, server=SERVER, rollover3days_weekday=wd)[0])
        for acct in ("FTMO", "redacted_account"):
            rec = ((book["accounts"][acct].get("sleeves") or {}).get(SLEEVE) or {})
            gross, ex, pn = (rec.get("gross_r"), rec.get("true_cost_ex_swap_r"),
                             rec.get("swap_r_per_night"))
            if gross is None or ex is None or pn is None:
                continue
            v = per_acct[acct]
            mean_n, p99_n = statistics.fmean(v), ADC.q(v, 0.99)
            live_n = rec.get("measured_carry_nights")
            repro = ADC.tier_of(gross, ex, pn, rec["horizon_mean_nights"], rec["max_nights"],
                                SLEEVE, live_n)
            rest = ADC.tier_of(gross, ex, pn, mean_n, p99_n, SLEEVE, live_n)
            be = ((gross - ex) / pn) if pn > 1e-12 else None
            out["rows"][f"{clock}::{acct}"] = {
                "clock": clock, "account": acct,
                "published_tier": rec.get("survivor_tier"),
                "rule_reproduced_from_artifact_inputs": repro,
                "rule_replication_ok": repro == rec.get("survivor_tier"),
                "restated_tier": rest,
                "tier_moved_vs_published": rest != rec.get("survivor_tier"),
                "n_trades": len(rows),
                "nights_measured": {"mean": round(mean_n, 4),
                                    "median": round(statistics.median(v), 4),
                                    "p90": round(ADC.q(v, 0.90), 4),
                                    "p99": round(p99_n, 4), "max": round(max(v), 4),
                                    "frac_zero": round(sum(1 for x in v if x == 0) / len(v), 4)},
                "nights_modelled": {"mean_held_to_horizon": rec["horizon_mean_nights"],
                                    "max_held_to_horizon": rec["max_nights"],
                                    "basis": rec.get("carry_basis")},
                "inputs_held_fixed": {"gross_r": gross, "true_cost_ex_swap_r": ex,
                                      "swap_r_per_night": pn,
                                      "break_even_nights": (round(be, 3) if be else None)},
                "net_r_at_measured_mean_nights": round(gross - ex - pn * mean_n, 5),
                "net_r_at_measured_p99_nights": round(gross - ex - pn * p99_n, 5),
                "carry_headroom_measured": (round(be / mean_n, 3) if be and mean_n else None),
                "median_hold_hours_measured": round(
                    statistics.median(x["hold_hours"] for x in rows), 3),
                "hold_as_frac_of_horizon": (
                    round(statistics.median(x["hold_hours"] for x in rows)
                          / rec["horizon_hours"], 4) if rec.get("horizon_hours") else None),
            }
    return out


# =====================================================================================
# main
# =====================================================================================

def _load_trades() -> dict:
    with gzip.open(OUT_TRADES, "rt") as fh:
        return json.load(fh)


def main() -> dict:
    stage = os.environ.get("AM_STAGE") or "all"
    t0 = dt.datetime.now(dt.timezone.utc)
    if (stage == "generate" or not OUT_TRADES.is_file()
            or (stage == "all" and os.environ.get("AM_REGENERATE"))):
        art = do_generate()
    else:
        art = _load_trades()
        print(f"reusing {OUT_TRADES.name}: {art['n_by_clock']}")
    if stage == "generate":
        return art

    arms = art["trades"]
    par = parity_vs_aa(arms)
    print(f"\nparity vs AA on the authored-UTC arm: count {par['exact_count']}, "
          f"sumR {par['exact_sum_r']}, keys {par['trade_keys_identical']} "
          f"({par['n_mine']} vs {par['n_aa']})")
    ab = clock_ab(arms)
    print(f"clock A/B: repaired n={ab['server_repaired']['n']} "
          f"mean {ab['server_repaired']['mean_r_gross']} | "
          f"authored n={ab['authored_utc']['n']} mean {ab['authored_utc']['mean_r_gross']} | "
          f"shared {ab['n_shared']}")

    doc: dict = {
        "schema": "gtos.am.submid_reclock.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "generated_utc": t0.isoformat(),
        "session": "AM", "blocks": "B1200-B1249",
        "sleeve": SLEEVE,
        "question": (
            "substrate._session_hour read the raw UTC hour and _bucket_session cuts it on 8/16 — "
            "boundaries mined on the broker clock. session=ny is one of this sleeve's seven cell "
            "conditions, so the repair changes WHICH TRADES EXIST. Everything published about the "
            "sleeve — AA's population and verdict, AD's exit frontier, SURVIVOR_BOOK_V1's carry "
            "tier and AD's B753 restatement of it — was measured on the wrong clock."),
        "trades_artifact": str(OUT_TRADES.relative_to(REPO)),
        "trades_generated_utc": art.get("generated_utc"),
        "clocks": art["clocks"],
        "parity_vs_aa_authored_arm": par,
        "clock_ab": ab,
    }
    if stage in ("all", "gate", "solo"):
        scope = os.environ.get("AM_GATE_SCOPE") or ("solo" if stage in ("all", "solo") else "family")
        print(f"\n=== gate, both clocks, diagnostic mode, scope={scope} ===", flush=True)
        doc.update(do_gate_solo(arms) if scope == "solo" else do_gate(arms))
    if stage in ("all", "carry", "solo"):
        print("\n=== carry tier restatement, both clocks ===", flush=True)
        doc["carry"] = do_carry(arms)
        for k, r in doc["carry"]["rows"].items():
            print(f"  {k:34s} published {str(r['published_tier']):22s} "
                  f"restated {str(r['restated_tier']):22s} "
                  f"n_mean {r['nights_measured']['mean']:6.3f} "
                  f"p99 {r['nights_measured']['p99']:6.2f} "
                  f"BE {str(r['inputs_held_fixed']['break_even_nights']):>8s}")

    OUT.write_text(json.dumps(doc, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.2f} MB)")

    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AM")
    for clock in CLOCKS:
        sv = ((doc.get("runs") or {}).get(clock) or {}).get("sleeve") or {}
        ledger.record(
            mechanism="substrate_cell_reclock", sleeve=SLEEVE,
            variant={"session_clock": clock, "maxbars": AA.MAXBARS, "timeframe": "H4",
                     "declared_family_size": AA_DECLARED,
                     "archive": "vps-bars-20260727-FTMO"},
            window=f"{ab[clock]['first']}..{ab[clock]['last']}" if ab[clock].get("n") else "",
            outcome=("positive" if (sv.get("pooled_oos_mean_r") or 0) > 0 else "negative"),
            metric=sv.get("pooled_oos_mean_r"), metric_name="pooled_oos_mean_r",
            spec_sha256=((doc.get("runs") or {}).get(clock) or {}).get("spec_sha256"),
            note=("AM B1200 — sub_mid_dn_revert re-derived on the repaired session clock; the "
                  "authored_utc arm is the control that reproduces AA"))
    print(f"ledger: {ledger.n_written} rows, {ledger.write_errors} errors")
    return doc


if __name__ == "__main__":
    main()
