"""B5 step 1 — inventory, quality-validate and classify the 166-symbol deep universe.

Reads ONLY:
  /Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/deep_universe_h4d1_2014_2026/*_D1.csv
  (and the matching *_H4.csv row/date bounds)

Writes:
  <OUT>/B5_UNIVERSE_INVENTORY_V1.json   per-symbol quality record + class + archive-level rollups
  <SCRATCH>/panel_d1.pkl                date -> sym -> (o,h,l,c,v)  (validated bars only)

No repo import, no network, no mutation of any source file.
"""
import csv, glob, os, json, pickle, math, sys
from collections import defaultdict, Counter

SRC = "/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/deep_universe_h4d1_2014_2026"
SCRATCH = "/Users/borr/.claude/jobs/adb9e69b/tmp/b5"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "b5_receipts")
os.makedirs(OUT, exist_ok=True)
os.makedirs(SCRATCH, exist_ok=True)

ISO = set("USD EUR GBP JPY CHF CAD AUD NZD SEK NOK DKK PLN CZK HUF TRY ZAR MXN SGD HKD CNH ILS RUB".split())
CRYPTO_PREFIX = set("""BTC ETH LTC XRP BCH ADA DOT LNK LINK SOL DOG DOGE AVA AVAX MAT MATIC UNI AAV AAVE
ALG ALGO ATO ATOM BAT BNB CHZ COM COMP DASH EOS FIL ICP MKR NEO SHB SHIB SUSHI TRX VET XLM XMR XTZ ZEC
CRV ENJ FTM GRT KSM LUNA MANA SAND SNX THETA WAVES YFI ONE EGLD RUNE CAKE AXS FLOW HBAR IOTA KAVA
NEAR QTUM RVN STX ZIL DOTUSD LTCUSD MKRUSD""".split())
INDEX_NAMES = set("""GER40 GER30 UK100 JP225 NAS100 SPX500 US30 US500 US2000 EU50 FRA40 AUS200 HK50 CHINA50
CHINAH ESP35 SWI20 NETH25 US100 USTEC ITA40 DE40 STOXX50 VIX""".split())
ENERGY = set("UKOIL USOIL NGAS WTI BRENT XNGUSD".split())
METALS = set("XAUUSD XAGUSD XPTUSD XPDUSD XAUEUR XAGEUR GOLD SILVER COPPER XCUUSD".split())
SOFTS = set("COCOA COFFEE SUGAR WHEAT CORN SOYBEAN COTTON".split())


def base(sym):
    return sym.replace("_cash", "").replace(".cash", "").replace("_", "").upper()


COMMOD_EXTRA = set("""NATGAS HEATOIL GASOLINE COTTON SUGAR COCOA COFFEE WHEAT CORN SOYBEAN SOYBEANS
XCUUSD XNIUSD XZNUSD XALUSD OJUICE LUMBER RICE OATS PALLADIUM PLATINUM""".split())


def classify(sym, weekend_frac, n):
    b = base(sym)
    if sym.endswith("_c"):           # broker suffix for commodity futures CFDs
        return "commodity"
    if b in METALS or b[:3] in ("XAU", "XAG", "XPT", "XPD"):
        return "commodity"
    if b in ENERGY or b in SOFTS or b in COMMOD_EXTRA or any(b.startswith(e) for e in ENERGY):
        return "commodity"
    if b in INDEX_NAMES or "_cash" in sym or b in ("USTEC", "US100"):
        return "index"
    if len(b) == 6 and b[:3] in ISO and b[3:] in ISO:
        return "fx"
    # crypto: quoted in USD, prefix known, or trades weekends heavily
    if b.endswith("USD") and (b[:-3] in CRYPTO_PREFIX or weekend_frac > 0.15):
        return "crypto"
    if weekend_frac > 0.15:
        return "crypto"
    return "equity"


def read_d1(path):
    rows = []
    bad = Counter()
    with open(path) as f:
        r = csv.reader(f)
        hdr = next(r)
        for row in r:
            if len(row) < 6:
                bad["short_row"] += 1
                continue
            try:
                o, h, l, c, v = (float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5]))
            except ValueError:
                bad["unparseable"] += 1
                continue
            d = row[0][:10]
            if not (o > 0 and h > 0 and l > 0 and c > 0):
                bad["nonpositive_price"] += 1
                continue
            if h < l:
                bad["high_lt_low"] += 1
                continue
            if not (l - 1e-12 <= c <= h + 1e-12) or not (l - 1e-12 <= o <= h + 1e-12):
                bad["ohlc_inconsistent"] += 1
                continue
            rows.append((d, o, h, l, c, v))
    return hdr, rows, bad


def dow(dstr):
    y, m, d = int(dstr[:4]), int(dstr[5:7]), int(dstr[8:10])
    # Zeller-free: use datetime
    import datetime
    return datetime.date(y, m, d).weekday()


def days_between(a, b):
    import datetime
    da = datetime.date(int(a[:4]), int(a[5:7]), int(a[8:10]))
    db = datetime.date(int(b[:4]), int(b[5:7]), int(b[8:10]))
    return (db - da).days


def main():
    paths = sorted(glob.glob(os.path.join(SRC, "*_D1.csv")))
    h4paths = {os.path.basename(p)[:-7]: p for p in glob.glob(os.path.join(SRC, "*_H4.csv"))}
    inv = {}
    panel = defaultdict(dict)
    for p in paths:
        sym = os.path.basename(p)[:-7]
        hdr, rows, bad = read_d1(p)
        if not rows:
            inv[sym] = {"n": 0, "reject": dict(bad)}
            continue
        # duplicate dates -> keep last, count
        seen = {}
        dups = 0
        for rec in rows:
            if rec[0] in seen:
                dups += 1
            seen[rec[0]] = rec
        recs = [seen[d] for d in sorted(seen)]
        dates = [r[0] for r in recs]
        closes = [r[4] for r in recs]
        vols = [r[5] for r in recs]
        wknd = sum(1 for d in dates if dow(d) >= 5)
        # gaps
        gaps = [days_between(dates[i - 1], dates[i]) for i in range(1, len(dates))]
        gap_gt5 = sum(1 for g in gaps if g > 5)
        gap_gt15 = sum(1 for g in gaps if g > 15)
        maxgap = max(gaps) if gaps else 0
        # stale / zero-range
        zero_range = sum(1 for r in recs if r[2] == r[3])
        zero_vol = sum(1 for v in vols if v == 0)
        stale = sum(1 for i in range(1, len(closes)) if closes[i] == closes[i - 1])
        # returns
        lr = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0]
        big15 = sum(1 for x in lr if abs(x) > 0.15)
        big35 = sum(1 for x in lr if abs(x) > 0.35)
        maxlr = max((abs(x) for x in lr), default=0.0)
        sd = (sum(x * x for x in lr) / len(lr)) ** 0.5 if lr else 0.0
        # split candidates: |ret| > 0.35 AND ratio near a simple split ratio
        split_cands = []
        for i in range(1, len(closes)):
            if closes[i - 1] <= 0:
                continue
            ratio = closes[i] / closes[i - 1]
            for num, den in ((1, 2), (1, 3), (1, 4), (1, 5), (1, 10), (1, 20), (2, 1), (3, 1), (4, 1), (5, 1), (10, 1), (20, 1), (2, 3), (3, 2)):
                tgt = num / den
                if tgt != 1.0 and abs(ratio / tgt - 1.0) < 0.04:
                    split_cands.append({"date": dates[i], "ratio": round(ratio, 4), "near": f"{num}:{den}"})
                    break
        wf = wknd / len(dates)
        cls = classify(sym, wf, len(dates))
        rec = {
            "class": cls, "n": len(recs), "first": dates[0], "last": dates[-1],
            "span_years": round(days_between(dates[0], dates[-1]) / 365.25, 2),
            "dup_dates": dups, "reject": dict(bad),
            "weekend_frac": round(wf, 4),
            "zero_range_bars": zero_range, "zero_volume_bars": zero_vol,
            "stale_close_repeats": stale,
            "gaps_gt_5d": gap_gt5, "gaps_gt_15d": gap_gt15, "max_gap_days": maxgap,
            "abs_logret_gt_15pct": big15, "abs_logret_gt_35pct": big35,
            "max_abs_logret": round(maxlr, 4), "daily_logret_sd": round(sd, 5),
            "split_candidates": split_cands[:12], "n_split_candidates": len(split_cands),
        }
        if sym in h4paths:
            nh4 = sum(1 for _ in open(h4paths[sym])) - 1
            rec["h4_rows"] = nh4
        inv[sym] = rec
        for r in recs:
            panel[r[0]][sym] = (r[1], r[2], r[3], r[4], r[5])

    dates = sorted(panel)
    archive_last = max(v["last"] for v in inv.values() if v.get("last"))
    # survivorship: how many symbols stop before the archive end
    ends = Counter()
    for s, v in inv.items():
        if not v.get("last"):
            continue
        lag = days_between(v["last"], archive_last)
        v["days_short_of_archive_end"] = lag
        ends[
            "ends_at_archive_end" if lag <= 7 else ("ends_1_4wk_early" if lag <= 31 else "ends_>1mo_early")
        ] += 1

    cov = defaultdict(list)
    for d in dates:
        cov[d[:4]].append(len(panel[d]))
    cov_by_year = {}
    for y in sorted(cov):
        xs = sorted(cov[y])
        cov_by_year[y] = {"days": len(xs), "median_symbols": xs[len(xs) // 2], "max_symbols": xs[-1]}

    by_class = Counter(v["class"] for v in inv.values())
    roll = {
        "source_dir": SRC,
        "n_symbols": len(inv),
        "archive_first": min(v["first"] for v in inv.values() if v.get("first")),
        "archive_last": archive_last,
        "n_dates": len(dates),
        "by_class": dict(by_class),
        "survivorship": dict(ends),
        "coverage_by_year": cov_by_year,
        "total_d1_bars": sum(v["n"] for v in inv.values()),
        "quality_flags": {
            "symbols_with_dup_dates": sum(1 for v in inv.values() if v.get("dup_dates")),
            "symbols_with_rejected_rows": sum(1 for v in inv.values() if v.get("reject")),
            "symbols_with_split_candidates": sum(1 for v in inv.values() if v.get("n_split_candidates")),
            "symbols_with_gap_gt_15d": sum(1 for v in inv.values() if v.get("gaps_gt_15d")),
            "total_rejected_rows": sum(sum(v.get("reject", {}).values()) for v in inv.values()),
        },
    }
    json.dump({"rollup": roll, "symbols": inv}, open(os.path.join(OUT, "B5_UNIVERSE_INVENTORY_V1.json"), "w"), indent=1, sort_keys=True)
    pickle.dump({"panel": dict(panel), "dates": dates,
                 "cls": {s: v["class"] for s, v in inv.items() if v.get("n")}},
                open(os.path.join(SCRATCH, "panel_d1.pkl"), "wb"))
    print(json.dumps(roll, indent=1))


if __name__ == "__main__":
    main()
