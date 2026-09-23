"""l9_lib — shared loader for lane l9 (allocator / selection alpha)."""
import gzip, json, os, sys, collections, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402

ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")


def born_of(mkt_r_prev_close):
    m = mkt_r_prev_close
    if m is None:
        return "unanchored"
    if m <= -1.0:
        return "past_stop"
    if m < -1e-12:
        return "marketable"
    if abs(m) <= 1e-12:
        return "at_limit"
    return "resting"


def load():
    """Working set rows with born_state + mkt_r_prev_close joined on (candidate_id, decision_time_utc)."""
    anch = {}
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            anch[(r["candidate_id"], r["decision_time_utc"])] = r
    rows = w0_ws.load()
    for r in rows:
        a = anch.get((r["candidate_id"], r["decision_time_utc"]))
        r["mkt_r_prev_close"] = a["mkt_r_prev_close"] if a else None
        r["born_state"] = born_of(a["mkt_r_prev_close"]) if a else "unanchored"
        r["takeable"] = r["born_state"] in ("at_limit", "resting", "marketable")
    return rows


def groups(rows, keyf=lambda r: r["decision_time_utc"]):
    g = collections.defaultdict(list)
    for r in rows:
        g[keyf(r)].append(r)
    return g


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def stats(xs):
    xs = [x for x in xs if x is not None]
    n = len(xs)
    if n == 0:
        return {"n": 0}
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
    sd = math.sqrt(v)
    return {"n": n, "mean": m, "sd": sd, "se": sd / math.sqrt(n) if n else None,
            "t": m / (sd / math.sqrt(n)) if n > 1 and sd > 0 else None}


def spearman(pairs):
    """pairs = [(x, y)]. Returns rho and n."""
    pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
    n = len(pairs)
    if n < 3:
        return None, n
    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        rk = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                rk[order[k]] = avg
            i = j + 1
        return rk
    rx = rank([p[0] for p in pairs]); ry = rank([p[1] for p in pairs])
    mx = sum(rx) / n; my = sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx)); dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx == 0 or dy == 0:
        return None, n
    rho = num / (dx * dy)
    z = rho * math.sqrt(n - 1)
    return {"rho": rho, "n": n, "z_approx": z}, n
