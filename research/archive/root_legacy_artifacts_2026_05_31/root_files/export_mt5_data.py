"""Export XAUUSD, EURUSD, DXY data and economic calendar from MT5 to CSV."""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATE_FROM = datetime(2024, 1, 1)
DATE_TO = datetime.now()

TIMEFRAMES = {
    "D1": mt5.TIMEFRAME_D1,
    "H4": mt5.TIMEFRAME_H4,
    "H1": mt5.TIMEFRAME_H1,
    "M15": mt5.TIMEFRAME_M15,
}

results = []


def export_symbol(symbol, timeframes_dict, date_from=DATE_FROM, date_to=DATE_TO):
    """Export symbol data for given timeframes."""
    # Ensure symbol is in Market Watch
    if not mt5.symbol_select(symbol, True):
        print(f"  WARNING: Could not select {symbol} in Market Watch, skipping")
        return

    for tf_name, tf_val in timeframes_dict.items():
        filename = f"{symbol}_{tf_name}.csv"
        filepath = os.path.join(DATA_DIR, filename)

        rates = mt5.copy_rates_range(symbol, tf_val, date_from, date_to)
        if rates is None or len(rates) == 0:
            print(f"  {filename}: No data returned")
            continue

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")

        # Format time to match existing CSVs
        if tf_name == "D1":
            df["time"] = df["time"].dt.strftime("%Y-%m-%d")
        else:
            df["time"] = df["time"].dt.strftime("%Y-%m-%d %H:%M:%S")

        # Use tick_volume as 'volume' to match existing format
        df = df.rename(columns={"tick_volume": "volume"})
        df = df[["time", "open", "high", "low", "close", "volume"]]

        df.to_csv(filepath, index=False)
        date_min = df["time"].iloc[0]
        date_max = df["time"].iloc[-1]
        results.append((filename, len(df), date_min, date_max))
        print(f"  {filename}: {len(df)} rows  [{date_min} -> {date_max}]")


def export_calendar():
    """Try exporting high-impact USD economic calendar events."""
    try:
        events = mt5.calendar_get(DATE_FROM, DATE_TO)
        if events is None or len(events) == 0:
            print("  Calendar: No events returned or API not available")
            return

        df = pd.DataFrame(list(events))

        # Filter high importance USD events
        if "importance" in df.columns and "currency" in df.columns:
            mask = (df["importance"] >= 3) & (df["currency"].str.contains("USD", na=False))
            df = df[mask]
        elif "importance" in df.columns:
            df = df[df["importance"] >= 3]

        if len(df) == 0:
            print("  Calendar: No high-impact USD events found")
            return

        filepath = os.path.join(DATA_DIR, "economic_calendar_usd_high.csv")
        df.to_csv(filepath, index=False)
        results.append(("economic_calendar_usd_high.csv", len(df), str(DATE_FROM.date()), str(DATE_TO.date())))
        print(f"  economic_calendar_usd_high.csv: {len(df)} rows")
    except Exception as e:
        print(f"  Calendar export failed: {e}")


def main():
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        sys.exit(1)

    print(f"MT5 connected: {mt5.terminal_info().name}")
    print(f"Date range: {DATE_FROM.date()} -> {DATE_TO.date()}\n")

    # 1. XAUUSD - all timeframes including M5
    print("=== XAUUSD ===")
    xau_tfs = {**TIMEFRAMES, "M5": mt5.TIMEFRAME_M5}
    export_symbol("XAUUSD", xau_tfs)

    # 2. EURUSD - D1, H4, H1, M15
    print("\n=== EURUSD ===")
    export_symbol("EURUSD", TIMEFRAMES)

    # 3. DXY / USDX - try multiple symbol names
    print("\n=== DXY/USDX ===")
    dxy_exported = False
    for sym in ["USDX", "DXY", "DX", "USDX.f", "DXY.f", "USDX_Index"]:
        info = mt5.symbol_info(sym)
        if info is not None:
            print(f"  Found DXY symbol: {sym}")
            export_symbol(sym, {"D1": mt5.TIMEFRAME_D1})
            # Rename to DXY_D1.csv if needed
            src = os.path.join(DATA_DIR, f"{sym}_D1.csv")
            dst = os.path.join(DATA_DIR, "DXY_D1.csv")
            if os.path.exists(src) and sym != "DXY":
                os.rename(src, dst)
                # Update results entry
                for i, r in enumerate(results):
                    if r[0] == f"{sym}_D1.csv":
                        results[i] = ("DXY_D1.csv", r[1], r[2], r[3])
            dxy_exported = True
            break
    if not dxy_exported:
        print("  No DXY/USDX symbol found, skipping")

    # 4. Economic calendar
    print("\n=== Economic Calendar ===")
    export_calendar()

    # Summary
    print("\n" + "=" * 70)
    print("EXPORT SUMMARY")
    print("=" * 70)
    print(f"{'File':<40} {'Rows':>8}  {'Date Range'}")
    print("-" * 70)
    for fname, rows, dmin, dmax in results:
        print(f"{fname:<40} {rows:>8}  {dmin} -> {dmax}")
    print(f"\nTotal files exported: {len(results)}")

    mt5.shutdown()


if __name__ == "__main__":
    main()
