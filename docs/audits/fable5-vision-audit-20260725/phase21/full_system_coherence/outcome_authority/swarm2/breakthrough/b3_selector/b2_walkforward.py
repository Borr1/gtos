#!/usr/bin/env python3
"""B3 step 2 -- the walk-forward daily refit for every declared arm.

    python3 b2_walkforward.py <stage>       stage in {W1,W2,W3,W4}

Discipline (PREREG_V1 s walk_forward_protocol): on each of the 105 sealed
trading days every model in the stage is refitted from scratch on the bootstrap
plus every STRICTLY PRIOR day, then predicts that day's candidates.  Nothing
from day D or later can reach a fit that scores day D.

Resumable: predictions and the last completed day are checkpointed after every
single day, so an interrupted run restarts from where it stopped.
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

import b3_lib as L

STAGES = {
    "W1": ["A0", "A1", "A2", "A10"],
    "W2": ["A3", "A4", "A5", "A6", "A7"],
    "W3": ["A8"],
    "W4": ["A9", "A11"],
    # PREREG_V1_1 negative controls: the KILLED same-day regime construction,
    # plus the T2 past/future split arms built on identical scored subsets.
    "W5": ["A10L", "A11L", "A10P", "A10F"],
    # PREREG_V1_2: the fill x cost ablation (sibling-lane hypothesis)
    "W6": ["A12", "A12H"],
    # PREREG_V1_3 Q3: the label-availability embargo on the one surviving arm
    "W7": ["A1E", "A1E7"],
    # PREREG_V1 learning_curve: the DATA-VOLUME axis on the surviving arm.
    # Most-recent-first subsample, so the curve also tests recency vs volume.
    "W8": ["A1_f0125", "A1_f025", "A1_f05"],
}
FRACTIONS = {"A1_f0125": 0.125, "A1_f025": 0.25, "A1_f05": 0.5}
# A12's reduced basis: cost + fillability + the two identity fields that decide
# order type.  Nothing from the M15 source block, no POI, no session, no clock.
FC_CAT = ["proposed_order_type", "origin_family", "limit_marketable_at_decision"]
FC_NUM = ["cost_r", "spread_r", "expected_slippage_r", "swap_cost_r", "commission_r",
          "distance_to_limit_atr", "distance_to_limit_risk", "risk_over_atr"]
IPCW_CLIP = 10.0          # declared implementation constant, never tuned
T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def main() -> None:
    stage = sys.argv[1]
    arms = STAGES[stage]
    with (L.OUT / "dataset.pkl").open("rb") as fh:
        data = pickle.load(fh)
    meta, frame, by_cday, cdays = data["meta"], data["frame"], data["by_cday"], data["cdays"]
    n = len(meta)

    res = np.asarray([m["res"] for m in meta])
    fil = np.asarray([m["fil"] for m in meta])
    net = np.asarray([m["net"] for m in meta], dtype=float)
    dc = np.asarray([m["dc"] for m in meta], dtype=float)
    c5 = np.asarray([m["c5"] for m in meta])
    cday = np.asarray([m["cday"] for m in meta])
    t_end = np.asarray([str(m["t1"])[:19] for m in meta], dtype="datetime64[s]")
    win_w = None  # per-subset, computed lazily

    F0 = L.CAT0 + L.NUM0
    F1 = L.CAT0 + L.CAT1 + L.NUM0 + L.NUM1
    hgb0 = frame[F0]
    hgb1 = frame[F1]
    rid0 = L.ridge_frame(frame, L.CAT0, L.NUM0)
    rid1 = L.ridge_frame(frame, L.CAT0 + L.CAT1, L.NUM0 + L.NUM1)

    if stage == "W6":
        hgbFC = frame[FC_CAT + FC_NUM]
        ridFC = L.ridge_frame(frame, FC_CAT, FC_NUM)

    if stage == "W5":
        with (L.OUT / "leak_features.pkl").open("rb") as fh:
            lk = pickle.load(fh)
        REG8 = ["reg_vol", "reg_ccvol", "reg_comp", "reg_spread", "reg_cost",
                "reg_risk", "reg_trendshare", "reg_upshare"]
        MOM = ["fam_mom5", "fam_mom10", "fam_mom20", "pool_mom10"]
        variants = {}
        for tag in ("LEAK", "PAST", "FUTURE"):
            f = frame[L.CAT0 + L.NUM0 + MOM].copy()
            for key in REG8:
                f[key] = lk["cols"][f"{key}__{tag}"]
            if tag == "LEAK":
                f["family_x_volbucket"] = pd.Categorical(lk["family_x_volbucket__LEAK"])
                f["family_x_trendbucket"] = pd.Categorical(lk["family_x_trendbucket__LEAK"])
            variants[tag] = f
        catsL = L.CAT0 + (L.CAT1 if True else [])
        ridL = {t: L.ridge_frame(variants[t], L.CAT0 + (L.CAT1 if t == "LEAK" else []),
                                 L.NUM0 + MOM + REG8) for t in variants}

    ck_path = L.OUT / f"ck_{stage}.json"
    pr_path = L.OUT / f"preds_{stage}.npz"
    preds = {a: np.full(n, np.nan) for a in arms}
    done = []
    if ck_path.exists() and pr_path.exists():
        state = json.loads(ck_path.read_text())
        blob = np.load(pr_path)
        for a in arms:
            if a in blob:
                preds[a] = blob[a]
        done = state.get("days_done", [])
        log(stage=stage, resumed_after=len(done))

    sealed = [d for d in cdays if d.startswith("0002-")]
    for di, day in enumerate(sealed):
        if day in done:
            continue
        prior = np.asarray(cday) < day
        test = np.asarray(by_cday[day])
        if not len(test):
            done.append(day)
            continue

        if stage == "W7":
            # EMBARGO: a row may enter training only once its label span has
            # closed strictly before the scored day begins.  `emb` is the
            # 1-day embargo (label closed before day start); `emb7` additionally
            # requires 7 calendar days, a deliberately over-strict control.
            day_start = np.datetime64(day[5:] + "T00:00:00")
            emb = prior & (t_end < day_start)
            emb7 = prior & (t_end < day_start - np.timedelta64(7, "D"))
        tr_res = np.flatnonzero(prior & res)
        tr_fil = np.flatnonzero(prior & fil)
        tr_all = np.flatnonzero(prior)
        w_res = L.window_weights(meta, tr_res)
        w_fil = L.window_weights(meta, tr_fil)
        w_all = L.window_weights(meta, tr_all)

        if stage == "W1":
            m = L.make_ridge(L.CAT0, L.NUM0)
            m.fit(rid0.iloc[tr_res], net[tr_res], ridge__sample_weight=w_res)
            preds["A0"][test] = m.predict(rid0.iloc[test])
            m = L.make_ridge(L.CAT0, L.NUM0)
            m.fit(rid0.iloc[tr_fil], net[tr_fil], ridge__sample_weight=w_fil)
            a1 = m.predict(rid0.iloc[test])
            preds["A1"][test] = a1
            m = L.make_ridge(L.CAT0, L.NUM0)
            m.fit(rid0.iloc[tr_res], fil[tr_res].astype(float), ridge__sample_weight=w_res)
            pfill = np.clip(m.predict(rid0.iloc[test]), 0.0, 1.0)
            preds["A2"][test] = pfill * a1
            m = L.make_ridge(L.CAT0 + L.CAT1, L.NUM0 + L.NUM1)
            m.fit(rid1.iloc[tr_fil], net[tr_fil], ridge__sample_weight=w_fil)
            preds["A10"][test] = m.predict(rid1.iloc[test])

        elif stage == "W2":
            m = L.make_hgb_reg()
            m.fit(hgb0.iloc[tr_res], net[tr_res], sample_weight=w_res)
            preds["A3"][test] = m.predict(hgb0.iloc[test])
            m = L.make_hgb_reg()
            m.fit(hgb0.iloc[tr_fil], net[tr_fil], sample_weight=w_fil)
            a4 = m.predict(hgb0.iloc[test])
            preds["A4"][test] = a4
            c = L.make_hgb_clf()
            c.fit(hgb0.iloc[tr_res], fil[tr_res], sample_weight=w_res)
            pfill = c.predict_proba(hgb0.iloc[test])[:, list(c.classes_).index(True)]
            preds["A5"][test] = pfill * a4
            m = L.make_hgb_reg(columns=F0, monotone=True)
            m.fit(hgb0.iloc[tr_fil], net[tr_fil], sample_weight=w_fil)
            preds["A6"][test] = pfill * m.predict(hgb0.iloc[test])
            c = L.make_hgb_clf()
            c.fit(hgb0.iloc[tr_res], (net[tr_res] > 0), sample_weight=w_res)
            preds["A7"][test] = c.predict_proba(hgb0.iloc[test])[:, list(c.classes_).index(True)]

        elif stage == "W3":
            c = L.make_hgb_clf()
            c.fit(hgb0.iloc[tr_all], c5[tr_all], sample_weight=w_all)
            proba = c.predict_proba(hgb0.iloc[test])
            classes = list(c.classes_)
            gross = {}
            for k in ("TARGET", "STOP", "TIME_STOP"):
                sel = tr_all[c5[tr_all] == k]
                gross[k] = float(np.mean(net[sel] + dc[sel])) if len(sel) else 0.0
            stat = np.zeros(len(test))
            for k, cl in enumerate(classes):
                if cl in gross:
                    stat += proba[:, k] * (gross[cl] - dc[test])
            preds["A8"][test] = stat
            if "A8_wc" not in preds:
                preds["A8_wc"] = np.full(n, np.nan)
            wc = stat.copy()
            if "CENSORED" in classes:
                wc = wc + proba[:, classes.index("CENSORED")] * (-1.0 - dc[test])
            preds["A8_wc"][test] = wc

        elif stage == "W4":
            c = L.make_hgb_clf()
            c.fit(hgb0.iloc[tr_all], (~res[tr_all]), sample_weight=w_all)
            idx_true = list(c.classes_).index(True)
            pc_fil = c.predict_proba(hgb0.iloc[tr_fil])[:, idx_true]
            pc_res = c.predict_proba(hgb0.iloc[tr_res])[:, idx_true]
            ip_fil = np.clip(1.0 / np.clip(1.0 - pc_fil, 1e-3, 1.0), None, IPCW_CLIP)
            ip_res = np.clip(1.0 / np.clip(1.0 - pc_res, 1e-3, 1.0), None, IPCW_CLIP)
            m = L.make_hgb_reg()
            m.fit(hgb0.iloc[tr_fil], net[tr_fil], sample_weight=w_fil * ip_fil)
            r9 = m.predict(hgb0.iloc[test])
            cc = L.make_hgb_clf()
            cc.fit(hgb0.iloc[tr_res], fil[tr_res], sample_weight=w_res * ip_res)
            p9 = cc.predict_proba(hgb0.iloc[test])[:, list(cc.classes_).index(True)]
            preds["A9"][test] = p9 * r9
            m = L.make_hgb_reg()
            m.fit(hgb1.iloc[tr_fil], net[tr_fil], sample_weight=w_fil)
            r11 = m.predict(hgb1.iloc[test])
            cc = L.make_hgb_clf()
            cc.fit(hgb1.iloc[tr_res], fil[tr_res], sample_weight=w_res)
            p11 = cc.predict_proba(hgb1.iloc[test])[:, list(cc.classes_).index(True)]
            preds["A11"][test] = p11 * r11

        elif stage == "W5":
            REG8 = ["reg_vol", "reg_ccvol", "reg_comp", "reg_spread", "reg_cost",
                    "reg_risk", "reg_trendshare", "reg_upshare"]
            MOM = ["fam_mom5", "fam_mom10", "fam_mom20", "pool_mom10"]
            for arm, tag in (("A10L", "LEAK"), ("A10P", "PAST"), ("A10F", "FUTURE")):
                cats = L.CAT0 + (L.CAT1 if tag == "LEAK" else [])
                m = L.make_ridge(cats, L.NUM0 + MOM + REG8)
                m.fit(ridL[tag].iloc[tr_fil], net[tr_fil], ridge__sample_weight=w_fil)
                preds[arm][test] = m.predict(ridL[tag].iloc[test])
            hgbL = variants["LEAK"]
            m = L.make_hgb_reg()
            m.fit(hgbL.iloc[tr_fil], net[tr_fil], sample_weight=w_fil)
            rL = m.predict(hgbL.iloc[test])
            cc = L.make_hgb_clf()
            cc.fit(hgbL.iloc[tr_res], fil[tr_res], sample_weight=w_res)
            pL = cc.predict_proba(hgbL.iloc[test])[:, list(cc.classes_).index(True)]
            preds["A11L"][test] = pL * rL

        elif stage == "W8":
            for arm, frac in FRACTIONS.items():
                k = max(2000, int(round(len(tr_fil) * frac)))
                sub = tr_fil[-k:]          # most recent first
                m = L.make_ridge(L.CAT0, L.NUM0)
                m.fit(rid0.iloc[sub], net[sub], ridge__sample_weight=L.window_weights(meta, sub))
                preds[arm][test] = m.predict(rid0.iloc[test])

        elif stage == "W7":
            for arm, mask in (("A1E", emb), ("A1E7", emb7)):
                sub = np.flatnonzero(mask & fil)
                if len(sub) < 2000:
                    continue
                m = L.make_ridge(L.CAT0, L.NUM0)
                m.fit(rid0.iloc[sub], net[sub], ridge__sample_weight=L.window_weights(meta, sub))
                preds[arm][test] = m.predict(rid0.iloc[test])

        elif stage == "W6":
            m = L.make_ridge(FC_CAT, FC_NUM)
            m.fit(ridFC.iloc[tr_fil], net[tr_fil], ridge__sample_weight=w_fil)
            r12 = m.predict(ridFC.iloc[test])
            m = L.make_ridge(FC_CAT, FC_NUM)
            m.fit(ridFC.iloc[tr_res], fil[tr_res].astype(float), ridge__sample_weight=w_res)
            p12 = np.clip(m.predict(ridFC.iloc[test]), 0.0, 1.0)
            preds["A12"][test] = p12 * r12
            m = L.make_hgb_reg()
            m.fit(hgbFC.iloc[tr_fil], net[tr_fil], sample_weight=w_fil)
            r12h = m.predict(hgbFC.iloc[test])
            cc = L.make_hgb_clf()
            cc.fit(hgbFC.iloc[tr_res], fil[tr_res], sample_weight=w_res)
            p12h = cc.predict_proba(hgbFC.iloc[test])[:, list(cc.classes_).index(True)]
            preds["A12H"][test] = p12h * r12h

        done.append(day)
        np.savez_compressed(pr_path, **preds)
        ck_path.write_text(json.dumps({"stage": stage, "arms": arms, "days_done": done,
                                       "prereg_sha256": L.PREREG_SHA}, indent=1))
        log(stage=stage, day=day, i=di + 1, of=len(sealed), n_test=int(len(test)),
            n_train_res=int(len(tr_res)), n_train_fil=int(len(tr_fil)))

    log(stage=stage, status="DONE", days=len(done))


if __name__ == "__main__":
    main()
