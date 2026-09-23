#!/usr/bin/env python3
"""l6 shared helpers over l6_GATEFRAME_V1.jsonl.gz."""
import gzip, json, os

D = os.path.dirname(os.path.abspath(__file__))
FRAME = os.path.join(D, "l6_GATEFRAME_V1.jsonl.gz")


def load(path=FRAME):
    out = []
    with gzip.open(path, "rt") as f:
        for ln in f:
            if ln.strip():
                out.append(json.loads(ln))
    return out


def mean(v):
    v = [x for x in v if x is not None]
    return round(sum(v) / len(v), 5) if v else None


def total(v):
    v = [x for x in v if x is not None]
    return round(sum(v), 3) if v else 0.0


def q(v, p):
    v = [x for x in v if x is not None]
    if not v:
        return None
    s = sorted(v)
    return round(s[min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))], 5)


def cost_frozen(r):
    return r.get("expected_cost_r") or 0.0


def cost_corr(r, div=7.3):
    """Frozen cost with the spread limb divided by the measured over-charge factor."""
    sp = r.get("spread_r") or 0.0
    return (cost_frozen(r) - sp) + sp / div


def stats(rows, label=None):
    """Outcome block for a set of rows. eng_* = pool's own walked gross (contaminated by
    untakeable rows); h*_ = honest no-look-ahead contract on the takeable subset."""
    n = len(rows)
    tk = [r for r in rows if r.get("takeable")]
    ps = [r for r in rows if r.get("born") == "born_past_stop"]
    nf = [r for r in rows if r.get("born") != "born_past_stop" and not r.get("filled")]
    hr = [r["hr"] for r in tk]
    out = {
        "n": n,
        "eng_gross_mean": mean([r.get("gross_r") for r in rows]),
        "eng_gross_total": total([r.get("gross_r") for r in rows]),
        "eng_win_pct": round(100 * sum(1 for r in rows if (r.get("gross_r") or 0) > 0) / n, 2) if n else None,
        "past_stop_n": len(ps),
        "past_stop_pct": round(100 * len(ps) / n, 2) if n else None,
        "nofill_n": len(nf),
        "takeable_n": len(tk),
        "takeable_pct": round(100 * len(tk) / n, 2) if n else None,
        "h_gross_mean": mean(hr),
        "h_gross_total": total(hr),
        "h_win_pct": round(100 * sum(1 for x in hr if x > 0) / len(hr), 2) if hr else None,
        "h_target_pct": round(100 * sum(1 for r in tk if r["hreason"] == "target") / len(tk), 2) if tk else None,
        "h_stop_pct": round(100 * sum(1 for r in tk if r["hreason"] in ("stop", "same_bar")) / len(tk), 2) if tk else None,
        # PORTFOLIO contract: over every non-past-stop row, an unfilled limit books 0 R and
        # 0 cost ("if it does not fill we simply do not trade"). This is the honest currency
        # for any gate whose refused set has a low fill rate.
        "h_all_n": len(tk) + len(nf),
        "h_all_mean": mean([r["hr"] for r in tk] + [0.0] * len(nf)),
        "h_all_total": total([r["hr"] for r in tk]),
        "h_all_net_corr73_mean": mean([r["hr"] - cost_corr(r, 7.3) for r in tk] + [0.0] * len(nf)),
        "h_all_net_corr73_total": total([r["hr"] - cost_corr(r, 7.3) for r in tk]),
        "fill_rate_pct": round(100 * len(tk) / (len(tk) + len(nf)), 2) if (len(tk) + len(nf)) else None,
        "cost_frozen_mean": mean([cost_frozen(r) for r in tk]),
        "cost_corr73_mean": mean([cost_corr(r, 7.3) for r in tk]),
        "h_net_frozen_mean": mean([r["hr"] - cost_frozen(r) for r in tk]),
        "h_net_corr73_mean": mean([r["hr"] - cost_corr(r, 7.3) for r in tk]),
        "h_net_corr73_total": total([r["hr"] - cost_corr(r, 7.3) for r in tk]),
    }
    if label is not None:
        out["value"] = label
    return out
