"""e3_lib -- portable month engine for lane e3 (extension of L9-F2, the passivity gradient).

Rebuilds, FROM RAW M1 BARS, everything l9_lib got from the January-only working set:
  * the decision anchor  (last fully-closed M1 bar strictly BEFORE the decision minute)
  * born_state           (past_stop / marketable / at_limit / resting)
  * the fill-honest walk (entry must trade before any excursion counts)
  * dist_r               (signed distance market -> limit, in R) = the passivity axis
  * fp_hat               (execution_fill_probability reconstructed from source formula)

Bar convention (w0-capture, verified): bars are OPEN-STAMPED. The bar stamped at the
decision minute is ENTIRELY POST-DECISION. The anchor is therefore the last bar with
time STRICTLY < decision_time; the path is the bars with time >= decision_time.

fill probability source: src/components/poi_execution_lifecycle.py:161-193
  marketable -> 0.92 ; else 0.70/(1+d_atr^1.35) + 0.30/(1+d_risk^1.10), clamped [0.03,0.95]
"""
from __future__ import annotations
import bisect, csv, gzip, json, math, os, collections

BARS_ROOT = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
             "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
TOL = 1e-12
STOP_R = -1.0
MAX_BARS = 120


# ------------------------------------------------------------------ bars
_cache: dict[str, dict] = {}


def bars(symbol: str, yyyymm: str):
    """M1 OHLC for one symbol/month. Concatenates the month before so a decision on
    day 1 still has an anchor. Returns {'t':[iso], 'o','h','l','c':[float]} or None."""
    k = f"{symbol}|{yyyymm}"
    if k in _cache:
        return _cache[k]
    prev = _prev_month(yyyymm)
    t, o, h, l, c = [], [], [], [], []
    for mm in (prev, yyyymm, _next_month(yyyymm)):
        p = os.path.join(BARS_ROOT, f"bridge_ftmo_m1_{mm}", f"{symbol}_M1.csv")
        if not os.path.isfile(p):
            continue
        with open(p) as fh:
            rd = csv.reader(fh)
            next(rd, None)
            for r in rd:
                t.append(r[0]); o.append(float(r[1])); h.append(float(r[2]))
                l.append(float(r[3])); c.append(float(r[4]))
    if not t:
        _cache[k] = None
        return None
    _cache[k] = {"t": t, "o": o, "h": h, "l": l, "c": c}
    return _cache[k]


def _plus_minutes(iso, mins):
    import datetime
    try:
        return (datetime.datetime.fromisoformat(iso) + datetime.timedelta(minutes=mins)).isoformat()
    except Exception:
        return "9999"


def _minus_minutes(iso, mins):
    import datetime
    try:
        return (datetime.datetime.fromisoformat(iso) - datetime.timedelta(minutes=mins)).isoformat()
    except Exception:
        return "0000"


def _prev_month(m):
    y, mo = int(m[:4]), int(m[4:])
    mo -= 1
    if mo == 0:
        y, mo = y - 1, 12
    return f"{y:04d}{mo:02d}"


def _next_month(m):
    y, mo = int(m[:4]), int(m[4:])
    mo += 1
    if mo == 13:
        y, mo = y + 1, 1
    return f"{y:04d}{mo:02d}"


def drop_cache():
    _cache.clear()


# ------------------------------------------------------------------ geometry
def born_of(m):
    if m is None:
        return "unanchored"
    if m <= -1.0:
        return "past_stop"
    if m < -1e-12:
        return "marketable"
    if abs(m) <= 1e-12:
        return "at_limit"
    return "resting"


def fp_hat(dist_price, unit_risk, atr):
    """Reconstruct execution_fill_probability. dist_price = 0 when marketable."""
    if dist_price <= 0.0:
        return 0.92
    d_atr = (dist_price / atr) if (atr and atr > 0) else None
    d_rsk = (dist_price / unit_risk) if unit_risk > 0 else None
    a = 0.50 if d_atr is None else 1.0 / (1.0 + max(0.0, d_atr) ** 1.35)
    r = 0.50 if d_rsk is None else 1.0 / (1.0 + max(0.0, d_rsk) ** 1.10)
    return max(0.03, min(0.95, a * 0.70 + r * 0.30))


def enrich(row, yyyymm, want_atr=True):
    """Add anchor + path geometry to one pool row IN PLACE. Returns False if unusable."""
    sym = row.get("symbol")
    dt = row.get("decision_time_utc")
    try:
        entry = float(row["entry_price"]); stop = float(row["stop_loss"])
    except Exception:
        return False
    d = abs(entry - stop)
    if not (d > 0) or not dt or not sym:
        return False
    b = bars(sym, yyyymm)
    if b is None:
        return False
    T = b["t"]
    i = bisect.bisect_left(T, dt) - 1          # last bar STRICTLY before decision minute
    if i < 0:
        return False
    side = (row.get("side") or row.get("direction") or "").upper()
    is_long = side == "LONG"
    sgn = 1.0 if is_long else -1.0
    prev_close = b["c"][i]
    mkt_r = sgn * (prev_close - entry) / d      # >0 -> limit is AWAY from market (resting)
    row["risk_distance"] = d
    row["mkt_r_prev_close"] = mkt_r
    row["born_state"] = born_of(mkt_r)
    row["takeable"] = row["born_state"] in ("at_limit", "resting", "marketable")
    row["dist_r"] = mkt_r                        # passivity axis (signed, R units)
    # ---- STALENESS: when did the market last actually trade AT this limit price?
    # w0-capture measured that 51.7-55.7 % of past-stop rows quote a level price has not
    # traded in 24 h. This separates a FAR limit (market never got there) from a STALE
    # limit (market was there, left, and the generator never retired the level).
    back = _minus_minutes(dt, 24 * 60)
    k0 = bisect.bisect_left(T, back)
    last_hit = None
    for j in range(i, k0 - 1, -1):
        if b["l"][j] - 1e-12 <= entry <= b["h"][j] + 1e-12:
            last_hit = j
            break
    row["entry_traded_prior_24h"] = last_hit is not None
    if last_hit is not None:
        row["bars_since_entry_last_traded"] = i - last_hit
    else:
        row["bars_since_entry_last_traded"] = None
    if want_atr:
        n0 = max(0, i - 14 * 15)
        trs = []
        pc = None
        for j in range(n0, i + 1):
            hi, lo, cl = b["h"][j], b["l"][j], b["c"][j]
            trs.append(max(hi - lo, abs(hi - pc), abs(lo - pc)) if pc is not None else hi - lo)
            pc = cl
        atr_m1 = sum(trs[-14:]) / 14.0 if len(trs) >= 14 else None
        row["atr14_m1"] = atr_m1
        row["fp_hat_m1atr"] = fp_hat(max(0.0, mkt_r) * d, d, atr_m1)
    # ---- path: bars stamped STRICTLY AFTER the decision minute, capped at MAX_BARS.
    # Measured: the CQ sidecar's first bar is decision_time + 1 min on 98.25 % of rows,
    # i.e. it skips the bar stamped AT the decision minute. Matching that exactly is what
    # makes this engine's fill_honest_walk_r reproduce the January working set.
    j0 = bisect.bisect_right(T, dt)
    # AND a hard 120-MINUTE wall (REPAIRED_PENDING_EXPIRY_MINUTES = 120,
    # v4_timewarp_simulated_live_research_loop.py:378) -- with M1 gaps the two caps differ.
    wall = _plus_minutes(dt, MAX_BARS)
    j1 = min(len(T), j0 + MAX_BARS, bisect.bisect_right(T, wall))
    tgt = float(row.get("policy_target_r") or 2.0)
    favs, advs, clss = [], [], []
    i_entry = i_tgt = i_stop = None
    for k in range(j0, j1):
        hi, lo, cl = b["h"][k], b["l"][k], b["c"][k]
        if is_long:
            f, a, cr = (hi - entry) / d, (lo - entry) / d, (cl - entry) / d
        else:
            f, a, cr = (entry - lo) / d, (entry - hi) / d, (entry - cl) / d
        f = round(f, 4); a = round(a, 4); cr = round(cr, 4)
        favs.append(f); advs.append(a); clss.append(cr)
        m = k - j0
        if i_tgt is None and f >= tgt - TOL:
            i_tgt = m
        if i_stop is None and a <= STOP_R + TOL:
            i_stop = m
        if i_entry is None and a <= 0.0 + TOL:
            i_entry = m
    if not favs:
        return False
    row["path_bars"] = len(favs)
    row["policy_target_r_used"] = tgt
    row["bars_to_entry_touch"] = (i_entry + 1) if i_entry is not None else None
    if i_stop is not None and (i_tgt is None or i_stop <= i_tgt):
        row["which_came_first"] = "stop"
    elif i_tgt is not None:
        row["which_came_first"] = "target"
    else:
        row["which_came_first"] = "neither"
    fh_which, fh_r = "no_fill", 0.0
    if i_entry is not None:
        jt = js = None
        for j in range(i_entry, len(favs)):
            if jt is None and favs[j] >= tgt - TOL:
                jt = j
            if js is None and advs[j] <= STOP_R + TOL:
                js = j
            if jt is not None or js is not None:
                break
        if js is not None and (jt is None or js <= jt):
            fh_which, fh_r = "stop", STOP_R
        elif jt is not None:
            fh_which, fh_r = "target", tgt
        else:
            fh_which, fh_r = "neither", clss[-1]
    row["fill_honest_which_came_first"] = fh_which
    row["fill_honest_walk_r"] = round(fh_r, 6)
    row["mfe_r"] = round(max(favs), 6)
    row["mae_r"] = round(min(advs), 6)
    try:
        row["gross_r"] = round(float(row["opportunity_net_proxy_r"]) + float(row["cost_r"]), 9)
    except Exception:
        row["gross_r"] = None
    return True


# ------------------------------------------------------------------ stats
def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def stats(xs):
    xs = [x for x in xs if x is not None]
    n = len(xs)
    if n == 0:
        return {"n": 0, "mean": None, "sd": None, "se": None, "t": None}
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
    sd = math.sqrt(v)
    return {"n": n, "mean": m, "sd": sd, "se": sd / math.sqrt(n) if n else None,
            "t": (m / (sd / math.sqrt(n))) if n > 1 and sd > 0 else None}


def groups(rows, keyf=lambda r: r["decision_time_utc"]):
    g = collections.defaultdict(list)
    for r in rows:
        g[keyf(r)].append(r)
    return g


def hz(r):
    """zero-neither convention: value only resolved trades, mark unresolved at 0."""
    w = r.get("fill_honest_which_came_first")
    return 0.0 if w in ("neither", "no_fill") else (r.get("fill_honest_walk_r") or 0.0)


def read_jsonl(path, keep=None):
    if str(path).endswith(".zst"):
        from compression import zstd as _z
        op = _z.open
    elif str(path).endswith(".gz"):
        op = gzip.open
    else:
        op = open
    with op(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                if keep is None or keep(r):
                    yield r


# ------------------------------------------------------------------ the L9 tables
FP_EDGES = [(0.10, "a<0.10"), (0.20, "b0.10-0.20"), (0.30, "c0.20-0.30"), (0.40, "d0.30-0.40"),
            (0.50, "e0.40-0.50"), (0.60, "f0.50-0.60"), (0.70, "g0.60-0.70"), (0.80, "h0.70-0.80"),
            (0.9199, "i0.80-0.92"), (2.0, "j>=0.92")]


def fb(fp):
    if fp is None:
        return "null"
    for hi, lab in FP_EDGES:
        if fp < hi:
            return lab
    return "j>=0.92"


# dist_r bands: the passivity axis expressed in R of distance from market to limit.
DIST_EDGES = [(0.0, "A_at_or_thru"), (0.05, "B_0-0.05"), (0.10, "C_0.05-0.10"), (0.20, "D_0.10-0.20"),
              (0.35, "E_0.20-0.35"), (0.60, "F_0.35-0.60"), (1.00, "G_0.60-1.00"), (1e18, "H_>=1.00")]


def db(dr):
    if dr is None:
        return "null"
    for hi, lab in DIST_EDGES:
        if dr <= hi:
            return lab
    return "H_>=1.00"


def band_table(sub, bandf, key="fill_honest_walk_r"):
    by = collections.defaultdict(list)
    for r in sub:
        by[bandf(r)].append(r)
    out = {}
    for k in sorted(by):
        v = by[k]
        n = len(v)
        wc = collections.Counter(r.get("fill_honest_which_came_first") for r in v)
        res = [r for r in v if r.get("fill_honest_which_came_first") in ("stop", "target")]
        s = stats([r.get(key) for r in v])
        out[k] = {"n": n, "honest": s["mean"], "se": s["se"], "t": s["t"],
                  "zn": mean([hz(r) for r in v]),
                  "pct_target": 100.0 * wc["target"] / n, "pct_stop": 100.0 * wc["stop"] / n,
                  "pct_neither": 100.0 * wc["neither"] / n, "pct_nofill": 100.0 * wc["no_fill"] / n,
                  "resolved_n": len(res),
                  "resolved_mean": mean([r.get(key) for r in res]),
                  "resolved_win": (sum(1 for r in res if r.get("fill_honest_which_came_first") == "target")
                                   / len(res)) if res else None,
                  "gross_r": mean([r.get("gross_r") for r in v]),
                  "mean_rank": mean([r.get("risk_finalizer_rank") for r in v]),
                  "bars_to_entry": mean([r.get("bars_to_entry_touch") for r in v]),
                  "mean_dist_r": mean([r.get("dist_r") for r in v])}
    return out
