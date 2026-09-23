#!/usr/bin/env python3
"""Session AV — the label store on the JPY/M15 surface, and §4.8's first honest gate (AV-3).

    python3 .../phase12/receipts/av_metalabel_fx_jpy.py --stage store      # B1623-B1630
    ...                                                 --stage metalabel  # B1631-B1638
    ...                                                 --stage gate       # B1639-B1646
    ...                                                 --stage all        # default

WHY THIS IS THE CENTREPIECE
---------------------------
`fx_jpy` has been ARMED on both live accounts since the five-sleeve expansion
(2026-07-30 ~11:52Z). `FOURTH_REVIEW` §4.8 names it as one of three immediate customers for
the meta-label overlay and AD routed it there explicitly: it needs a 1.89x gross multiple at a
2x stop and delivers 0.175x, so *"its next prescription is the §4.8 meta-label entry filter,
not another stop cell"*. AP then measured why nobody could act on that: the label store is a
741-row H4 pilot over the armed FOUR, with **zero `fx_jpy` rows and zero JPY symbols**. The
route was correct and the substrate did not exist.

THREE THINGS THIS FIXES IN THE STORE IT EXTENDS
-----------------------------------------------
1. **Surface.** H4 / armed-four -> M15 / GBPJPY+USDJPY, through the production generator
   (`sleeves/fx_jpy.generate_fx_jpy`), so what is stored is what the live book would have
   intended --- not a re-implementation.
2. **Cost.** `AB_LABEL_STORE_V1` records `cost_charged: 0.0` on all 741 rows: R is GROSS. A
   label store for an entry-quality filter that cannot see cost would train a model to prefer
   trades whose edge the spread eats, and `fx_jpy`'s whole diagnosis is that commission is
   41 % of its gross. Every row here carries broker-true net R at all four bands.
3. **Contract.** The label is replayed at the sleeve's OWN live exit contract ---
   `SLEEVE_EXIT_PROFILES["fx_jpy"]`, `time_stop` / `final_target_r 2.5` /
   `time_stop_bars 48` --- so a model trained on it is trained on the trade the book runs.
   AQ's whole session is what happens when that is not true.

THE MODEL, AND WHY ITS SCORES ARE OUT OF SAMPLE BY CONSTRUCTION
---------------------------------------------------------------
An expanding-window walk-forward logistic regression on standardised decision-time features.
For intent *k*, the fit uses only trades whose **exit** is strictly before *k*'s **entry**,
minus an embargo of one maximum hold. So:

* no trade can train on its own outcome;
* no trade can train on an outcome that had not happened when it was entered;
* the overlap between a training trade's holding period and the scored trade's is embargoed,
  which is the purge/embargo §4.8 requires;
* and there is no separate "test set" to leak through, because **every** score is produced by
  a model that could have existed at that instant.

The quantile cuts are taken on the TRAINING window's score distribution, never the scored
one --- a quantile over the trades being scored is a peek at the thing being scored.

MULTIPLICITY
------------
The five cuts were declared in `CANDIDATE_FAMILY_V6.json` by `av_family_v6.py`, committed
before this file ran and importing nothing from it. Every arm is gated at the raised bill and
at V5's un-raised one, and the filter-grid Bonferroni (alpha/5) travels beside the BH bar.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import json
import math
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_M15, decision_day_of  # noqa: E402
from src.components.ultimate_book.execution_packets import SLEEVE_EXIT_PROFILES  # noqa: E402
from src.components.ultimate_book.sleeves import fx_jpy as FJ  # noqa: E402
from src.costs.model import cost_r, load_broker_true_costs  # noqa: E402
from src.research_infra.regime_spine import dials as D  # noqa: E402
from src.research_infra.regime_spine import normalize as N  # noqa: E402
from src.research_infra.regime_spine.archive import frames_for  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as EP  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import TradeRecord  # noqa: E402

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
STORE = HERE / "AV_LABEL_STORE_V2_JPY.jsonl.gz"
OUT = HERE / "AV_METALABEL_FX_JPY_V1.json"
FAMILY_V6 = HERE / "CANDIDATE_FAMILY_V6.json"
FAMILY_V5 = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/CANDIDATE_FAMILY_V5.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"

SLEEVE = "fx_jpy"
SURFACE = FJ.ON_SURFACE                       # ("GBPJPY", "USDJPY")
SERVER = "FTMO-Server3"
ACCOUNT = "FTMO"
BANDS = (None, "low", "mid", "high")
WARMUP_M15 = FJ._WARMUP_JPY                   # 100, the generator's own guard
LOOKBACK = 300                                # bars handed to the generator per evaluation

#: The sleeve's OWN live exit contract, read from the packet table rather than typed. AQ's
#: session is the argument for reading it: a horizon that disagrees with the live one produces
#: economics for a trade the book cannot run.
EXIT = SLEEVE_EXIT_PROFILES[SLEEVE]
TIME_STOP_M15 = int(EXIT["time_stop_bars"])
FINAL_TARGET_R = float(EXIT["final_target_r"])

#: Declared in CANDIDATE_FAMILY_V6.json before this file ran. Absolute cuts and quantile cuts
#: are handled differently on purpose: a quantile is taken on the TRAINING window.
ABSOLUTE_CUTS = {"p_ge_0p50": 0.50, "p_ge_0p55": 0.55, "p_ge_0p60": 0.60}
QUANTILE_CUTS = {"top75": 0.25, "top50": 0.50}   # name -> quantile of the TRAIN scores to cut at

#: Features handed to the model. Deliberately small and all decision-time: `feature_row`
#: computes them from index <= i only, and the three session features below are read from the
#: intent the generator already produced, so nothing here can see a bar the generator could not.
MODEL_FEATURES = (
    "vol_regime", "vol_regime_pct_1000", "persistence_ac60",
    "trend_slope20_atr", "trend_slope50_atr", "range_position_50",
    "compression_5_over_20", "htf_trend_sign", "horizon_conflict",
    "session_impulse_atr", "direction", "broker_hour", "day_of_week",
)

#: One maximum hold, in hours. The embargo: a training trade whose life overlaps the scored
#: trade's entry is excluded, because its outcome was not knowable then.
EMBARGO_HOURS = TIME_STOP_M15 * 0.25


# =====================================================================================
# stage: store
# =====================================================================================

def build_store(costs) -> list[dict]:
    """One row per `fx_jpy` intent over the matched FTMO M15 archive, features + label."""
    t0 = time.time()
    frames = frames_for(SURFACE, TF_M15)
    N.attach_ranks(frames, ["vr"], window=1000)
    missing = [s for s in SURFACE if s not in frames]
    if missing:
        raise SystemExit(f"no M15 archive series for {missing} -- refusing to publish a "
                         "partial-surface store as if it were the sleeve")

    rows: list[dict] = []
    seen_day: set[tuple[str, str]] = set()
    dropped = collections.Counter()
    for canon, f in sorted(frames.items()):
        bars, times = f.bars, f.times_utc
        for i in range(max(WARMUP_M15, 200) - 1, len(bars) - 1):
            lo = max(0, i - LOOKBACK + 1)
            day = decision_day_of(times[i])
            intent = FJ.generate_fx_jpy(canon, bars[lo:i + 1], day,
                                        bar_time=times[i], bar_times=times[lo:i + 1])
            if intent is None:
                continue
            # The live book takes ONE trade per symbol per day; the generator's
            # `_CATCHUP_GRACE` lets the same signal re-fire on the next two session bars, so
            # a raw walk would store the same decision up to three times and triple-count it
            # in every downstream count. Keep the first, and record how many were dropped.
            if (canon, day) in seen_day:
                dropped["catchup_grace_duplicate"] += 1
                continue
            seen_day.add((canon, day))

            d = int(intent.direction)
            sd = float(intent.stop_dist)
            if d not in (1, -1) or not (sd > 0):
                dropped["degenerate_intent"] += 1
                continue
            td = float(intent.target_dist) if intent.target_dist else None
            pr = replay(bars, i, d, stop_dist=sd,
                        policy=ExitPolicy(target_dist=td, maxbars=TIME_STOP_M15,
                                          label=f"{SLEEVE}_live_contract"))
            feat = D.feature_row(f, i, canonical=canon)
            entry_utc = times[i]
            exit_utc = times[pr.exit_index]
            hold_h = (pr.exit_index - i) * 0.25
            broker_local = FJ._to_server_local(entry_utc)

            # fx_jpy's own session geometry, from the intent the generator produced.
            feat["session_impulse_atr"] = (
                (float(intent.target_dist) / sd) if (intent.target_dist and sd) else None)
            feat["direction"] = d
            feat["broker_hour"] = broker_local.hour if broker_local else None
            feat["day_of_week"] = entry_utc.weekday()

            r_gross = float(winsorize_R(pr.r_gross))
            net = {}
            for band in ("flat", "low", "mid", "high"):
                c = cost_r(f.symbol, ACCOUNT, hold_h,
                           sl_distance_price=sd, entry_price=float(bars[i].c),
                           side=("LONG" if d > 0 else "SHORT"),
                           entry_utc=entry_utc,
                           spread_band=(None if band == "flat" else band),
                           costs=costs)
                tot = float(c.total_r.value)
                net[band] = {
                    "cost_r": tot, "r_net": r_gross - tot,
                    "coverage": getattr(c.total_r.coverage, "name", str(c.total_r.coverage)),
                    "commission_r": float(c.commission_r.value),
                    "spread_r": float(c.spread_r.value),
                    "swap_r": float(c.swap_r.value),
                    "slippage_r": float(c.slippage_r.value),
                }
            rows.append({
                "features": feat,
                "intent": {"sleeve": SLEEVE, "direction": d,
                           "stop_dist_price": sd, "target_dist_price": td,
                           "symbol_broker": f.symbol, "symbol_canonical": canon},
                "label": {
                    "r_gross_winsorised": r_gross,
                    "exit_reason": pr.exit_reason,
                    "exit_bar_offset": pr.exit_index - i,
                    "hold_hours": hold_h,
                    "mfe_r": round(pr.mfe_r, 6), "mae_r": round(pr.mae_r, 6),
                    "entry_utc": entry_utc.isoformat(),
                    "exit_utc": exit_utc.isoformat(),
                    "net_by_band": net,
                    "maxbars": TIME_STOP_M15,
                },
                "provenance": {
                    "schema": "gtos.wave12.av.label_store.v2",
                    "generator": "src/components/ultimate_book/sleeves/fx_jpy.generate_fx_jpy",
                    "exit_contract": dict(EXIT),
                    "feed": "vps-bars-20260727 FTMO M15, via CsvBarSource (sidecar-declared)",
                    "cost_artifact": str(COSTS.relative_to(REPO)),
                },
            })
    rows.sort(key=lambda r: (r["label"]["entry_utc"], r["intent"]["symbol_canonical"]))
    with gzip.open(STORE, "wt") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
    print(f"store: {len(rows)} rows -> {STORE.name} "
          f"(dropped {dict(dropped)}) in {time.time()-t0:.1f}s")
    return rows


def load_store() -> list[dict]:
    with gzip.open(STORE, "rt") as fh:
        return [json.loads(line) for line in fh]


ESTATE = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"


def reconcile_against_estate(rows) -> dict:
    """The control that makes a live-money claim about an ARMED sleeve readable.

    A new stream that disagrees with the estate's own walk is measuring the driver. So every
    decision is matched on `(symbol, decision_day)` and compared on the four things generation
    decides --- bar, direction, stop distance, realized R --- and every difference is
    attributed rather than tolerated.

    It also measures something nobody asked for and which turns out to matter more than the
    reconciliation: the estate's `fx_jpy` stream holds **three rows per decision**. The
    generator's `_CATCHUP_GRACE = 2` re-fires the SAME 4th-session-bar signal on the next two
    M15 bars --- by design, so a missed bar during downtime can still be taken --- and a walk
    with no per-day cap keeps all three. Live, the book takes one trade per symbol per day.
    """
    est = json.load(gzip.open(ESTATE, "rt"))["trades"]["fx_jpy"]
    by = collections.defaultdict(list)
    for r in est:
        by[(r["symbol_canonical"], r["decision_day"])].append(r)
    first = {k: sorted(v, key=lambda x: x["decision_bar_iso"])[0] for k, v in by.items()}
    mine = {(r["intent"]["symbol_canonical"], r["features"]["decision_day"]): r for r in rows}
    shared = sorted(set(first) & set(mine))

    def agree(k, field, mine_val, tol=1e-9):
        return abs(float(first[k][field]) - float(mine_val)) < tol

    diffs = [{"key": list(k), "estate_r": first[k]["r_gross"],
              "av_r": mine[k]["label"]["r_gross_winsorised"],
              "estate_exit": first[k]["exit_reason"],
              "av_exit": mine[k]["label"]["exit_reason"]}
             for k in shared
             if not agree(k, "r_gross", mine[k]["label"]["r_gross_winsorised"])]
    per_day = collections.Counter(len(v) for v in by.values())
    within_day_disagree = sum(
        1 for v in by.values() if len({round(x["r_gross"], 9) for x in v}) > 1)
    return {
        "estate_artifact": str(ESTATE.relative_to(REPO)),
        "estate_rows": len(est),
        "estate_distinct_decisions": len(by),
        "estate_rows_per_decision": dict(per_day),
        "the_triplication": {
            "what": ("the estate's fx_jpy stream carries exactly 3 rows for every "
                     "(symbol, decision_day): the generator's `_CATCHUP_GRACE = 2` re-fires "
                     "the SAME signal on the next two M15 bars, and a walk with no per-day cap "
                     "keeps all three. The live book takes one trade per symbol per day."),
            "n_decisions_with_a_within_day_r_disagreement": within_day_disagree,
            "share": round(within_day_disagree / max(1, len(by)), 4),
            "estate_gross_mean_all_rows": statistics.fmean(r["r_gross"] for r in est),
            "estate_gross_mean_first_only": statistics.fmean(
                first[k]["r_gross"] for k in first),
            "why_it_is_not_a_harmless_duplicate": (
                "the copies enter one and two bars later on the same signal, so they are not "
                "duplicates but three different entries of one decision, and 36 % of decisions "
                "resolve differently across them. Averaging them is neither the live contract "
                "nor a defensible estimator, and it understates the sleeve's own gross."),
        },
        "match": {
            "n_shared_decisions": len(shared),
            "only_in_estate": [list(k) for k in sorted(set(first) - set(mine))],
            "only_in_av": [list(k) for k in sorted(set(mine) - set(first))],
            "same_decision_bar": sum(
                1 for k in shared
                if first[k]["decision_bar_iso"] == mine[k]["features"]["bar_time_utc"]),
            "same_direction": sum(
                1 for k in shared if first[k]["direction"] == mine[k]["intent"]["direction"]),
            "same_stop_distance": sum(
                1 for k in shared if agree(k, "sl_distance_price",
                                           mine[k]["intent"]["stop_dist_price"])),
            "same_r_gross": len(shared) - len(diffs),
            "r_gross_differences": diffs,
            "why_the_differences": (
                "every one is the sleeve's own LIVE time stop, which the estate walk did not "
                "apply --- its artifact says so: exit_contracts.fx_jpy.time_stop_bars_applied "
                "is False and it ran maxbars 80 where the packet declares time_stop_bars 48. "
                "The decisive case is USDJPY 2025-11-04: +2.50 R at 80 bars, +0.44 R at 48. "
                "This store is the one that describes the contract the book runs."),
        },
    }


# =====================================================================================
# stage: metalabel -- expanding-window walk-forward logistic regression
# =====================================================================================

def _design(rows, band: str):
    """`(X, y, t_entry, t_exit)` with non-finite features imputed to the TRAIN mean later."""
    X, y, te, tx = [], [], [], []
    for r in rows:
        f = r["features"]
        vec = []
        for k in MODEL_FEATURES:
            v = f.get(k)
            vec.append(float(v) if isinstance(v, (int, float)) and math.isfinite(float(v))
                       else float("nan"))
        X.append(vec)
        y.append(1.0 if r["label"]["net_by_band"][band]["r_net"] > 0 else 0.0)
        te.append(dt.datetime.fromisoformat(r["label"]["entry_utc"]))
        tx.append(dt.datetime.fromisoformat(r["label"]["exit_utc"]))
    return X, y, te, tx


def _fit_logistic(X, y, *, l2=1.0, iters=200):
    """Plain IRLS-free gradient descent with L2. No sklearn dependency; deterministic.

    Ridge is not decoration: with ~13 features and a few hundred training rows the
    unpenalised fit separates on the tail and the scores collapse to 0/1, which would make
    every absolute cut behave like a quantile cut and quietly merge two declared cells.
    """
    n, p = len(X), len(X[0])
    if n == 0:
        return [0.0] * p, 0.0
    mu = [statistics.fmean([r[j] for r in X if math.isfinite(r[j])] or [0.0]) for j in range(p)]
    sd = []
    for j in range(p):
        col = [r[j] for r in X if math.isfinite(r[j])]
        s = statistics.pstdev(col) if len(col) > 1 else 0.0
        sd.append(s if s > 1e-12 else 1.0)
    Z = [[((r[j] if math.isfinite(r[j]) else mu[j]) - mu[j]) / sd[j] for j in range(p)] for r in X]
    w = [0.0] * p
    b = math.log(max(1e-6, sum(y)) / max(1e-6, n - sum(y))) if 0 < sum(y) < n else 0.0
    lr = 0.5
    for _ in range(iters):
        gw = [0.0] * p
        gb = 0.0
        for zi, yi in zip(Z, y):
            z = b + sum(wj * zij for wj, zij in zip(w, zi))
            pr = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
            e = pr - yi
            gb += e
            for j in range(p):
                gw[j] += e * zi[j]
        for j in range(p):
            w[j] = w[j] - lr * (gw[j] / n + l2 * w[j] / n)
        b -= lr * gb / n
    return (w, b, mu, sd)


def _predict(model, row):
    w, b, mu, sd = model
    z = b + sum(wj * (((v if math.isfinite(v) else mu[j]) - mu[j]) / sd[j])
                for j, (wj, v) in enumerate(zip(w, row)))
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))


def walk_forward_scores(rows, band: str, *, min_train=120, refit_every=25) -> dict:
    """One OOS `p_win` per row, plus the TRAIN-window quantiles each cut needs.

    The model at row k has seen only rows whose exit precedes row k's entry by at least
    `EMBARGO_HOURS`. Refitting every `refit_every` rows rather than every row is a compute
    choice, not a leak: the model in force at row k is always fitted on a strict subset of
    what row k could have known.
    """
    X, y, te, tx = _design(rows, band)
    n = len(rows)
    scores: list[float | None] = [None] * n
    train_q: list[dict | None] = [None] * n
    model = None
    train_idx: list[int] = []
    n_since_fit = 0
    for k in range(n):
        cutoff = te[k] - dt.timedelta(hours=EMBARGO_HOURS)
        train_idx = [j for j in range(k) if tx[j] <= cutoff]
        if len(train_idx) < min_train:
            continue
        if model is None or n_since_fit >= refit_every:
            Xt = [X[j] for j in train_idx]
            yt = [y[j] for j in train_idx]
            if 0 < sum(yt) < len(yt):
                model = _fit_logistic(Xt, yt)
                tr_scores = sorted(_predict(model, X[j]) for j in train_idx)
                train_q[k] = {q: tr_scores[min(len(tr_scores) - 1, int(qv * (len(tr_scores) - 1)))]
                              for q, qv in (("q25", 0.25), ("q50", 0.50))}
                n_since_fit = 0
                last_q = train_q[k]
            else:
                continue
        else:
            train_q[k] = last_q
        n_since_fit += 1
        scores[k] = _predict(model, X[k])
    n_scored = sum(1 for s in scores if s is not None)
    return {"scores": scores, "train_quantiles": train_q, "n_scored": n_scored,
            "n_unscored_warmup": n - n_scored,
            "min_train": min_train, "refit_every": refit_every,
            "embargo_hours": EMBARGO_HOURS,
            "base_rate_win": (statistics.fmean(y) if y else None)}


def apply_cuts(rows, wf: dict) -> dict[str, list[bool]]:
    """The five DECLARED cuts, as per-row keep masks. An unscored row is never kept."""
    scores, tq = wf["scores"], wf["train_quantiles"]
    masks: dict[str, list[bool]] = {}
    for name, thr in ABSOLUTE_CUTS.items():
        masks[name] = [s is not None and s >= thr for s in scores]
    for name, qv in QUANTILE_CUTS.items():
        key = "q25" if qv == 0.25 else "q50"
        masks[name] = [s is not None and q is not None and s >= q[key]
                       for s, q in zip(scores, tq)]
    # The control is the SAME scored population with no filter: comparing a filtered arm
    # against the whole store would confound the filter with the model's warmup.
    masks["control_scored_unfiltered"] = [s is not None for s in scores]
    return masks


def identity_filter_check(rows, wf) -> dict:
    """Wave-11 §2: prove the score is not simply re-deriving something the sleeve pins.

    Run at BOTH layers, per the wave-12 delta: the LEVEL (max |delta| of each feature over
    all trades) and the BUCKET (how many trades disagree with the modal bucket). A filter on
    a coordinate the sleeve already pins is a no-op that reads as a result.
    """
    out = {}
    for k in MODEL_FEATURES:
        vals = [r["features"].get(k) for r in rows]
        num = [float(v) for v in vals if isinstance(v, (int, float)) and math.isfinite(float(v))]
        if not num:
            out[k] = {"pinned": True, "why": "no finite values"}
            continue
        lo, hi = min(num), max(num)
        buckets = collections.Counter(round(v, 6) for v in num)
        modal, n_modal = buckets.most_common(1)[0]
        out[k] = {
            "level_max_abs_delta": hi - lo,
            "level_pinned": (hi - lo) < 1e-9,
            "bucket_disagreement_count": len(num) - n_modal,
            "bucket_pinned": (len(num) - n_modal) == 0,
            "n_finite": len(num),
        }
    pinned = [k for k, v in out.items() if v.get("level_pinned") or v.get("bucket_pinned")]
    return {"per_feature": out, "pinned_features": pinned,
            "verdict": ("SOME_FEATURES_PINNED" if pinned else "NO_FEATURE_IS_PINNED"),
            "note": ("a pinned feature contributes nothing and its weight is unidentified; "
                     "it is reported rather than silently dropped so the model's inputs are "
                     "the ones a reader can check")}


# =====================================================================================
# stage: gate
# =====================================================================================

def to_records(rows, keep, sleeve_name, band) -> dict:
    out = collections.defaultdict(list)
    for r, k in zip(rows, keep):
        if not k:
            continue
        lab, itn = r["label"], r["intent"]
        out[sleeve_name].append(TradeRecord(
            sleeve=sleeve_name, symbol=itn["symbol_broker"],
            entry_utc=dt.datetime.fromisoformat(lab["entry_utc"]),
            exit_utc=dt.datetime.fromisoformat(lab["exit_utc"]),
            direction=int(itn["direction"]),
            sl_distance_price=float(itn["stop_dist_price"]),
            entry_price=float(r["features"]["close"]),
            r_gross=float(lab["r_gross_winsorised"]),
            features={"decision_day": r["features"]["decision_day"],
                      "hold_hours": lab["hold_hours"],
                      "symbol_canonical": itn["symbol_canonical"],
                      "decision_bar_iso": r["features"]["bar_time_utc"],
                      "exit_reason": lab["exit_reason"],
                      "mfe_r": lab["mfe_r"], "mae_r": lab["mae_r"]}))
    return dict(out)


def maxbars_share(rows, keep) -> float | None:
    sel = [r for r, k in zip(rows, keep) if k]
    if not sel:
        return None
    return round(sum(1 for r in sel if r["label"]["exit_reason"] == "maxbars") / len(sel), 6)


def stage_gate(rows, masks, costs, ledger) -> dict:
    fam6 = CF.load_candidate_family(FAMILY_V6)
    fam5 = CF.load_candidate_family(FAMILY_V5)
    arms = {}
    for cut, keep in sorted(masks.items()):
        n_keep = sum(keep)
        if n_keep == 0:
            arms[f"{cut}|-|-"] = {"cut": cut, "verdict": "NOT_EVALUABLE",
                                  "reasons": ["the cut keeps zero trades"], "n_trades": 0}
            continue
        for band in BANDS:
            for bill_name, loaded in (("declared_V6", fam6), ("unraised_V5", fam5)):
                o = OPTIONS["B_balanced"]
                spec = o.with_(spec_id=f"{o.spec_id}_av_metalabel_{cut}_{bill_name}",
                               sleeve_symbol_allowlist={SLEEVE: tuple(sorted(
                                   {r["intent"]["symbol_broker"] for r, k in zip(rows, keep) if k}))},
                               spread_band=band)
                spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=loaded)
                recs0 = to_records(rows, keep, SLEEVE, band)
                recs, spec, mix = EP.apply("RECORDED", dict(recs0), spec, account=ACCOUNT,
                                           band=(band or "mid"))
                t0 = time.time()
                res = run_gate(recs, spec, costs=costs, server=SERVER, diagnose=True)
                el = time.time() - t0
                wipe = res.family.get("wipeout") or {}
                if wipe.get("wiped_out"):
                    # Recorded, not raised. AQ's guard (B1435) exists so a wall of nulls
                    # cannot be tabulated AS a verdict grid; here the grid is per-cut and one
                    # cut failing to score IS the finding for that cut. Raising would discard
                    # the four cuts that did score. It is stamped so it can never read as a
                    # measured REJECT.
                    arms[f"{cut}|{band or 'flat'}|{bill_name}"] = {
                        "cut": cut, "band": band or "flat_37_day_snapshot", "bill": bill_name,
                        "verdict": "NOT_EVALUABLE", "wipeout": wipe,
                        "n_kept_by_cut": n_keep,
                        "reasons": sorted({r for v in res.verdicts.values() for r in v.reasons}),
                        "note": ("no sleeve in this arm reached a null; this is the harness "
                                 "reporting that the cut leaves nothing scoreable, NOT a "
                                 "measured rejection"),
                    }
                    continue
                for sleeve, sv in res.verdicts.items():
                    st = sv.gates.get("stability", {})
                    fl = (sv.telemetry or {}).get("p_floor", {}) or {}
                    diag = sv.telemetry or {}
                    arms[f"{cut}|{band or 'flat'}|{bill_name}"] = {
                        "cut": cut, "band": band or "flat_37_day_snapshot",
                        "band_is_control": band is None, "bill": bill_name,
                        "sleeve": sleeve, "population": "RECORDED", "option": "B_balanced",
                        "alpha": spec.alpha,
                        "declared_family_size": spec.declared_family_size,
                        "declared_family_id": spec.declared_family_id,
                        "bh_rank1_bar": round(spec.alpha / spec.declared_family_size, 8),
                        "filter_grid_bonferroni_bar": round(spec.alpha / len(ABSOLUTE_CUTS | QUANTILE_CUTS), 8),
                        "spec_sha256": spec.seal(), "population_mix": mix,
                        "verdict": sv.verdict.value, "n_trades": sv.n_trades,
                        "n_kept_by_cut": n_keep,
                        "pooled_oos_mean_r": sv.pooled_oos_mean_r,
                        "oos_mean_r_per_trade":
                            sv.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
                        "p_raw": sv.p_raw, "q_value": sv.q_value,
                        "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                                           "robustness", "significance")
                                               if not sv.gates.get(g, {}).get("pass")],
                        "fold_means": st.get("fold_means"),
                        "oos_positive_fold_frac": st.get("oos_positive_fold_frac"),
                        "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
                        "n_thin_folds": sv.gates.get("sample", {}).get("n_thin_folds"),
                        "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
                        "coverage_frac": (sv.coverage or {}).get("coverage_frac"),
                        "p_floor": fl.get("p_floor"), "n_blocks": fl.get("n_blocks"),
                        "p_floor_headroom": ((sv.p_raw / fl["p_floor"])
                                             if (sv.p_raw is not None and fl.get("p_floor"))
                                             else None),
                        "regime_inflation_flag":
                            (diag.get("regime_inflation") or {}).get("contamination_flag"),
                        "regime_inflation_haircut":
                            (diag.get("regime_inflation") or {}).get("recommended_magnitude_haircut"),
                        "in_sample_mean_r": (diag.get("in_sample") or {}).get("mean_is_r"),
                        "maxbars_share": maxbars_share(rows, keep),
                        "folds": sv.folds, "reasons": list(sv.reasons),
                        "seconds": round(el, 2),
                    }
                    if ledger is not None:
                        ledger.record(
                            mechanism="metalabel_overlay", sleeve=f"{SLEEVE}@{cut}",
                            variant={"cut": cut, "band": band or "flat", "bill": bill_name,
                                     "population": "RECORDED", "option": "B_balanced"},
                            window="m15_2024_2026_matched", spec_sha256=spec.seal(),
                            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                     "NOT_EVALUABLE": "not_evaluable"}.get(
                                         sv.verdict.value, "evaluated"),
                            metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                            note="AV §4.8 meta-label overlay on fx_jpy")
        print(f"  gated {cut} (n={n_keep})", flush=True)
    return arms


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", choices=("store", "metalabel", "gate", "all"))
    ap.add_argument("--band", default="mid", help="cost band the LABEL (win/loss) is defined at")
    ap.add_argument("--no-ledger", action="store_true")
    args = ap.parse_args()

    costs = load_broker_true_costs(COSTS)
    ledger = None if args.no_ledger else TrialLedger(DEFAULT_TRIAL_LEDGER, session="AV")
    t0 = time.time()

    rows = build_store(costs) if (args.stage in ("store", "all") or not STORE.is_file()) \
        else load_store()
    if args.stage == "store":
        return

    wf = walk_forward_scores(rows, args.band)
    masks = apply_cuts(rows, wf)
    ident = identity_filter_check(rows, wf)

    scored = [(r, s) for r, s in zip(rows, wf["scores"]) if s is not None]
    disc = {}
    if scored:
        wins = [s for r, s in scored if r["label"]["net_by_band"][args.band]["r_net"] > 0]
        loss = [s for r, s in scored if r["label"]["net_by_band"][args.band]["r_net"] <= 0]
        # AUC by the Mann-Whitney identity --- the honest single number for a ranker, and it
        # is computed on the OOS scores only, which is the only place it means anything.
        auc = None
        if wins and loss:
            allp = sorted([(s, 1) for s in wins] + [(s, 0) for s in loss])
            ranks, i = {}, 0
            while i < len(allp):
                j = i
                while j + 1 < len(allp) and allp[j + 1][0] == allp[i][0]:
                    j += 1
                avg = (i + j) / 2.0 + 1
                for k in range(i, j + 1):
                    ranks[k] = avg
                i = j + 1
            rsum = sum(ranks[k] for k, (_, lab) in enumerate(allp) if lab == 1)
            auc = (rsum - len(wins) * (len(wins) + 1) / 2.0) / (len(wins) * len(loss))
        disc = {"n_scored": len(scored), "n_win": len(wins), "n_loss": len(loss),
                "oos_auc": auc,
                "mean_score_wins": statistics.fmean(wins) if wins else None,
                "mean_score_losses": statistics.fmean(loss) if loss else None}

    per_cut = {}
    for cut, keep in sorted(masks.items()):
        sel = [r for r, k in zip(rows, keep) if k]
        nets = [r["label"]["net_by_band"][args.band]["r_net"] for r in sel]
        per_cut[cut] = {
            "n_kept": len(sel),
            "keep_frac_of_scored": (len(sel) / disc["n_scored"]) if disc.get("n_scored") else None,
            "mean_net_r": statistics.fmean(nets) if nets else None,
            "win_rate": (sum(1 for x in nets if x > 0) / len(nets)) if nets else None,
            "maxbars_share": maxbars_share(rows, keep),
        }

    gate = {} if args.stage == "metalabel" else stage_gate(rows, masks, costs, ledger)

    payload = {
        "schema": "gtos.wave12.av.metalabel_fx_jpy.v1",
        "session": "AV", "blocks": "B1623-B1646",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "sleeve": SLEEVE, "surface": list(SURFACE),
        "label_band": args.band,
        "exit_contract": dict(EXIT),
        "store": {
            "path": str(STORE.relative_to(REPO)),
            "n_rows": len(rows),
            "window": [rows[0]["label"]["entry_utc"], rows[-1]["label"]["entry_utc"]] if rows else None,
            "symbols": sorted({r["intent"]["symbol_canonical"] for r in rows}),
            "what_it_fixes_in_AB_LABEL_STORE_V1": [
                "surface: H4/armed-four -> M15/GBPJPY+USDJPY (AB had zero fx_jpy rows and zero JPY symbols)",
                "cost: AB records cost_charged 0.0 on all 741 rows; every row here carries broker-true net R at four bands",
                "contract: the label is replayed at SLEEVE_EXIT_PROFILES['fx_jpy'], the sleeve's own live exit",
            ],
        },
        "reconciliation_against_the_estate_walk": reconcile_against_estate(rows),
        "model": {k: v for k, v in wf.items() if k not in ("scores", "train_quantiles")},
        "model_features": list(MODEL_FEATURES),
        "discrimination": disc,
        "identity_filter_check": ident,
        "declared_cuts": {**{k: f">= {v}" for k, v in ABSOLUTE_CUTS.items()},
                          **{k: f">= TRAIN q{int((1-v)*100)}" for k, v in QUANTILE_CUTS.items()}},
        "per_cut": per_cut,
        "gate": gate,
        "seconds_total": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print(json.dumps({"store_rows": len(rows), "model": payload["model"],
                      "discrimination": disc, "per_cut": per_cut,
                      "identity": ident["verdict"]}, indent=2, default=str))


if __name__ == "__main__":
    main()
