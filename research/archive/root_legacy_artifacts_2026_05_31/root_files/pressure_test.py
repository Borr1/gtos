import os, pandas as pd, json, numpy as np

base = "exports/multi_instrument"

# CHECK 1: XAUUSD Calibration Data
print("=== CHECK 1: XAUUSD Calibration ===")
for tf in ["H1", "H4", "D1"]:
    f = f"{base}/XAUUSD_{tf}.csv"
    if os.path.exists(f):
        df = pd.read_csv(f)
        print(f"  OK {tf}: {len(df)} rows")
    else:
        print(f"  CRITICAL: {f} MISSING")

# CHECK 2: All Files Have Correct Columns
print("\n=== CHECK 2: Column Check ===")
expected = {"time", "open", "high", "low", "close"}
files = sorted([f for f in os.listdir(base) if f.endswith(".csv")])
col_issues = []
for fn in files:
    df = pd.read_csv(os.path.join(base, fn), nrows=5)
    missing = expected - set(df.columns)
    if missing:
        col_issues.append(f"  X {fn}: MISSING {missing}")
if col_issues:
    for c in col_issues:
        print(c)
else:
    print(f"  OK All {len(files)} files have required columns")

# CHECK 3: Time Column Format
print("\n=== CHECK 3: Time Format ===")
sample_files = [f for f in os.listdir(base) if f.endswith("_H1.csv")][:3]
time_is_string = False
for fn in sample_files:
    df = pd.read_csv(os.path.join(base, fn), nrows=3)
    first = df["time"].iloc[0]
    if isinstance(first, str) and "-" in str(first):
        time_is_string = True
        print(f"  WARN {fn}: time='{first}' is datetime STRING, not Unix timestamp")
        print(f"       Screening needs pd.to_datetime(df['time']) without unit='s'")
    else:
        try:
            parsed = pd.to_datetime(first, unit="s")
            print(f"  OK {fn}: time={first} -> {parsed} (Unix seconds)")
        except:
            print(f"  X {fn}: time={first} - cannot parse")

# CHECK 4: Data Coverage
print("\n=== CHECK 4: Data Coverage ===")
h1_files = sorted([f for f in os.listdir(base) if f.endswith("_H1.csv")])
coverage = {}
for fn in h1_files:
    sym = fn.replace("_H1.csv", "")
    df = pd.read_csv(os.path.join(base, fn))
    try:
        df["dt"] = pd.to_datetime(df["time"], unit="s")
    except:
        df["dt"] = pd.to_datetime(df["time"])
    n = len(df)
    days = df["dt"].dt.date.nunique()
    coverage[sym] = {"rows": n, "start": str(df["dt"].min().date()), "end": str(df["dt"].max().date()), "days": days}
    s = "OK" if n >= 2000 else ("WARN" if n >= 500 else "X")
    print(f"  {s} {sym}: {n} candles, {days} days ({df['dt'].min().date()} to {df['dt'].max().date()})")

# CHECK 5 & 6: H4 and D1 for all H1
print("\n=== CHECK 5: H4 Coverage ===")
h1_syms = set(f.replace("_H1.csv", "") for f in os.listdir(base) if f.endswith("_H1.csv"))
h4_syms = set(f.replace("_H4.csv", "") for f in os.listdir(base) if f.endswith("_H4.csv"))
d1_syms = set(f.replace("_D1.csv", "") for f in os.listdir(base) if f.endswith("_D1.csv"))

missing_h4 = h1_syms - h4_syms
if missing_h4:
    print(f"  WARN Missing H4: {missing_h4}")
else:
    print(f"  OK H4 exists for all {len(h4_syms)} instruments")

print("\n=== CHECK 6: D1 Coverage ===")
missing_d1 = h1_syms - d1_syms
if missing_d1:
    print(f"  X Missing D1: {missing_d1}")
else:
    print(f"  OK D1 exists for all {len(d1_syms)} instruments")

# CHECK 7: Spread Data
print("\n=== CHECK 7: Spread Data ===")
summary_file = os.path.join(base, "extraction_summary.json")
spread_data = {}
if os.path.exists(summary_file):
    with open(summary_file) as f:
        summary = json.load(f)
    spread_data = summary.get("spread_samples", {})
    print(f"  Spread data for {len(spread_data)} instruments:")
    for sym in sorted(h1_syms):
        if sym in spread_data:
            s = spread_data[sym]
            print(f"    OK {sym}: median={s['median_spread']:.6f}, n={s['n_bars']} bars, {s.get('n_trading_days','?')} days")
        else:
            print(f"    WARN {sym}: NO spread data")

    if "XAUUSD" in spread_data:
        xau_sp = spread_data["XAUUSD"]["median_spread"]
        if 0.10 <= xau_sp <= 2.00:
            print(f"  OK XAUUSD spread ${xau_sp:.2f} looks reasonable")
        else:
            print(f"  WARN XAUUSD spread ${xau_sp:.2f} unusual (expected $0.30-$0.50)")

    for sym, s in spread_data.items():
        m = s["median_spread"]
        if m == 0:
            print(f"  X {sym}: median_spread=0 - data issue")
        elif m > 0 and m == round(m):
            print(f"  WARN {sym}: median={m} is round number - might be raw points")
else:
    print("  X extraction_summary.json MISSING")

# CHECK 8: OHLC Integrity
print("\n=== CHECK 8: OHLC Integrity ===")
integrity_issues = []
for fn in sorted([f for f in os.listdir(base) if f.endswith("_H1.csv")]):
    df = pd.read_csv(os.path.join(base, fn))
    bad = df[(df["low"] > df["open"]) | (df["low"] > df["close"]) |
             (df["high"] < df["open"]) | (df["high"] < df["close"]) | (df["low"] > df["high"])]
    if len(bad) > 0:
        integrity_issues.append(f"  X {fn}: {len(bad)} OHLC violations ({len(bad)/len(df)*100:.1f}%)")
    zero = df[(df["open"] <= 0) | (df["high"] <= 0) | (df["low"] <= 0) | (df["close"] <= 0)]
    if len(zero) > 0:
        integrity_issues.append(f"  X {fn}: {len(zero)} zero/negative prices")
    if df["time"].duplicated().any():
        integrity_issues.append(f"  WARN {fn}: {df['time'].duplicated().sum()} duplicate timestamps")

if integrity_issues:
    for i in integrity_issues:
        print(i)
else:
    print("  OK All H1 files pass OHLC integrity check")

# CHECK 9: Timezone Verification
print("\n=== CHECK 9: Timezone (Weekend Gaps) ===")
for ref_file in ["EURUSD_H1.csv", "XAUUSD_H1.csv"]:
    fp = os.path.join(base, ref_file)
    if os.path.exists(fp):
        df = pd.read_csv(fp)
        try:
            df["dt"] = pd.to_datetime(df["time"], unit="s")
        except:
            df["dt"] = pd.to_datetime(df["time"])
        df["gap_h"] = df["dt"].diff().dt.total_seconds() / 3600
        gaps = df[df["gap_h"] > 24]
        if len(gaps) > 0:
            friday_idxs = gaps.index - 1
            friday_idxs = friday_idxs[friday_idxs >= 0]
            friday_hours = df.loc[friday_idxs, "dt"].dt.hour.values
            med_hour = int(np.median(friday_hours))
            print(f"  {ref_file}: median Friday close hour = {med_hour}:00")
            if 20 <= med_hour <= 23:
                offset = med_hour - 21
                if offset == 0:
                    print(f"  OK Server appears to be UTC")
                else:
                    print(f"  INFO Server offset: UTC+{offset} (Friday close at {med_hour}:00)")
                    print(f"  Screening session windows need adjustment by -{offset}h")
            else:
                print(f"  WARN Unusual Friday close hour {med_hour}:00")
            for _, row in gaps.head(3).iterrows():
                pidx = df.index[df.index.get_loc(row.name) - 1]
                pt = df.loc[pidx, "dt"]
                print(f"    {pt} ({pt.strftime('%A')}) -> {row['dt']} ({row['dt'].strftime('%A')}), gap={row['gap_h']:.1f}h")
        break

# CHECK 10: Final Summary
print("\n=== CHECK 10: Final Summary ===")
all_f = os.listdir(base)
csv_f = [f for f in all_f if f.endswith(".csv")]
h1_c = len([f for f in csv_f if "_H1.csv" in f])
h4_c = len([f for f in csv_f if "_H4.csv" in f])
d1_c = len([f for f in csv_f if "_D1.csv" in f])
m15_c = len([f for f in csv_f if "_M15.csv" in f])
total_mb = sum(os.path.getsize(os.path.join(base, f)) for f in all_f) / 1024 / 1024

print(f"  H1: {h1_c}, H4: {h4_c}, D1: {d1_c}, M15: {m15_c}")
print(f"  Total: {len(all_f)} files, {total_mb:.1f} MB")

checks = {
    "XAUUSD H1 exists": os.path.exists(f"{base}/XAUUSD_H1.csv"),
    "XAUUSD H4 exists": os.path.exists(f"{base}/XAUUSD_H4.csv"),
    "XAUUSD D1 exists": os.path.exists(f"{base}/XAUUSD_D1.csv"),
    "extraction_summary.json": os.path.exists(f"{base}/extraction_summary.json"),
    "At least 5 H1 instruments": h1_c >= 5,
    "H4 matches H1 count": h4_c == h1_c,
    "D1 matches H1 count": d1_c == h1_c,
    "Spread data >= 50%": len(spread_data) >= h1_c * 0.5,
}
all_pass = True
for chk, ok in checks.items():
    print(f"  {'OK' if ok else 'X'} {chk}")
    if not ok:
        all_pass = False

if all_pass:
    print(f"\n  ALL CHECKS PASS - data ready for transfer to Mac")
else:
    print(f"\n  SOME CHECKS FAILED - fix before transferring")
