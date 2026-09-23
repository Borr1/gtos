#!/usr/bin/env python3
"""l3_rank - rank EVERY field by its power to separate the 3,072 full-target winners from
the 15,057 full stops. Effect sizes, not p-values: win-share lift, mean difference,
Cohen's d, AUC, and Information Value (IV) computed identically for numeric (decile-binned)
and categorical fields so one ranking covers all of them.

Two populations are reported for every field:
  RAW       3,072 vs 15,057  (as briefed)
  TAKEABLE  3,069 vs 11,534  (born_past_stop dropped: 3,513 of the stops were never takeable)
And every field is stamped PRE (known at the decision instant) or POST (path/outcome-derived,
i.e. leakage). Only PRE fields can be used to select a trade.
"""
import json, os, math
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR","/tmp"), "l3_frame.pkl"))

POST = {"gross_r","outcome_band","opportunity_net_proxy_r","mfe_r","mae_r","bars_to_mfe","bars_to_mae",
 "bars_to_target","bars_to_stop","which_came_first","bars_to_entry_touch","entry_touched",
 "entry_touch_before_target","entry_touch_same_bar_as_target","plain_walk_r","fill_honest_which_came_first",
 "fill_honest_walk_r","r_at_path_end","path_bars","path_minutes","first_bar_utc","last_bar_utc",
 "mfe_r_after_stop","bars_to_mfe_after_stop","mae_r_before_target","mfe_r_before_stop","bars_to_fav",
 "bars_to_adv","path_horizon_end_utc","setup_dup_count","mkt_r_close","mkt_r_high","mkt_r_low"}
POST |= {c for c in df.columns if c.startswith(("r_at_bar_","mfe_r_by_bar_","mae_r_by_bar_"))}
SKIP = {"candidate_id","decision_time_utc","path_source_path","path_arm_id","path_source_timeframe",
 "missed_opportunity_r_scoreability_status","missed_opportunity_non_executable_diagnostic_scoreable",
 "anchor_bar_time","anchor_exact","takeable","is_first_emission"}

def iv_from_counts(w, l):
    """Information Value over aligned level count vectors."""
    W, L = w.sum(), l.sum()
    if W == 0 or L == 0: return 0.0
    pw = (w + 0.5) / (W + 0.5*len(w)); pl = (l + 0.5) / (L + 0.5*len(l))
    return float(np.sum((pw - pl) * np.log(pw / pl)))

def cramers_v(w, l):
    tab = np.vstack([w, l]).astype(float)
    tab = tab[:, tab.sum(0) > 0]
    if tab.shape[1] < 2: return 0.0
    chi2 = stats.chi2_contingency(tab, correction=False)[0]
    n = tab.sum()
    return float(math.sqrt(chi2 / (n * (min(tab.shape) - 1))))

def auc(a, b):
    """P(random winner ranks above random stop). a=winner values, b=stop values."""
    a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
    if len(a) < 5 or len(b) < 5: return None
    try:
        u = stats.mannwhitneyu(a, b, alternative="two-sided")
        return float(u.statistic / (len(a)*len(b)))
    except Exception: return None

def analyse(sub, tag):
    W = sub["outcome_band"] == "ge_target"; L = sub["outcome_band"] == "full_stop"
    base = W.sum() / (W.sum() + L.sum())
    out = {}
    for c in sub.columns:
        if c in SKIP: continue
        s = sub[c]
        fv = s.dropna()
        if len(fv) and isinstance(fv.iloc[0], (list, dict)):
            out[c] = {"kind":"container_skipped","pos":"POST" if c in POST else "PRE"}; continue
        if s.notna().sum() == 0:
            out[c] = {"kind":"unpopulated"}; continue
        numericish = pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)
        rec = {"pos": "POST" if c in POST else "PRE",
               "n_nonnull": int(s.notna().sum()), "n_null": int(s.isna().sum()),
               "n_distinct": int(s.nunique(dropna=True))}
        if rec["n_distinct"] <= 1 and rec["n_null"] == 0:
            rec["kind"] = "constant"; rec["value"] = str(s.dropna().iloc[0]); out[c] = rec; continue
        if numericish and rec["n_distinct"] > 12:
            aw = s[W].to_numpy(dtype=float); al = s[L].to_numpy(dtype=float)
            mw, ml = np.nanmean(aw), np.nanmean(al)
            sw, sl = np.nanstd(aw, ddof=1), np.nanstd(al, ddof=1)
            nw, nl = np.isfinite(aw).sum(), np.isfinite(al).sum()
            sp = math.sqrt(((nw-1)*sw**2 + (nl-1)*sl**2) / max(1, nw+nl-2)) if (nw+nl) > 2 else np.nan
            rec.update(kind="numeric",
                       mean_win=float(mw), mean_stop=float(ml),
                       median_win=float(np.nanmedian(aw)), median_stop=float(np.nanmedian(al)),
                       mean_diff=float(mw-ml),
                       cohens_d=(float((mw-ml)/sp) if sp and np.isfinite(sp) and sp > 0 else None),
                       auc=auc(aw, al), n_win=int(nw), n_stop=int(nl))
            try:
                q = pd.qcut(s[W|L], 10, duplicates="drop")
                lab = q.cat.add_categories(["__NULL__"]).fillna("__NULL__")
                ct = pd.crosstab(lab, np.where(W[W|L], "w", "l"))
                for col in ("w","l"):
                    if col not in ct: ct[col] = 0
                rec["iv"] = iv_from_counts(ct["w"].to_numpy(), ct["l"].to_numpy())
                rec["decile_table"] = [{"bin": str(i), "n": int(ct.loc[i].sum()),
                                        "win": int(ct.loc[i,"w"]), "stop": int(ct.loc[i,"l"]),
                                        "win_share": round(float(ct.loc[i,"w"]/max(1,ct.loc[i].sum())),5)}
                                       for i in ct.index]
            except Exception as e:
                rec["iv"] = 0.0; rec["iv_err"] = str(e)
        else:
            lab = s.astype("object").where(s.notna(), "__NULL__").astype(str)
            vc = lab[W|L].value_counts()
            keep = set(vc[vc >= 25].index)
            lab2 = lab.where(lab.isin(keep), "__OTHER__")
            ct = pd.crosstab(lab2[W|L], np.where(W[W|L], "w", "l"))
            for col in ("w","l"):
                if col not in ct: ct[col] = 0
            rec.update(kind="categorical",
                       iv=iv_from_counts(ct["w"].to_numpy(), ct["l"].to_numpy()),
                       cramers_v=cramers_v(ct["w"].to_numpy(), ct["l"].to_numpy()),
                       levels=sorted([{"level": str(i), "n": int(ct.loc[i].sum()),
                                       "win": int(ct.loc[i,"w"]), "stop": int(ct.loc[i,"l"]),
                                       "win_share": round(float(ct.loc[i,"w"]/max(1,ct.loc[i].sum())),5),
                                       "lift": round(float((ct.loc[i,"w"]/max(1,ct.loc[i].sum()))/base),4)}
                                      for i in ct.index], key=lambda d: -d["n"]))
        out[c] = rec
    return {"base_rate": float(base), "n_win": int(W.sum()), "n_stop": int(L.sum()), "fields": out}

res = {"RAW": analyse(df, "RAW"), "TAKEABLE": analyse(df[df["takeable"]], "TAKEABLE")}
json.dump(res, open(os.path.join(HERE, "l3_FIELD_RANKING_V1.json"), "w"), indent=1, default=str)

for tag in ("RAW","TAKEABLE"):
    f = res[tag]["fields"]
    rk = sorted([(v.get("iv",0), k, v) for k,v in f.items() if v.get("kind") in ("numeric","categorical")],
                reverse=True)
    print(f"=== {tag}  base={res[tag]['base_rate']:.4f} win={res[tag]['n_win']} stop={res[tag]['n_stop']}")
    print(f"{'field':44s} {'pos':4s} {'IV':>7s} {'AUC':>6s} {'d':>7s}")
    for iv,k,v in rk[:26]:
        print(f"{k:44s} {v['pos']:4s} {iv:7.3f} {(v.get('auc') or 0):6.3f} {(v.get('cohens_d') or 0):7.3f}")
