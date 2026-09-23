"""
Export MT5 historical data to CSV files for simulation.
Usage: python scripts/export_mt5_historical.py
Output: data/historical/<SYMBOL>_<TF>.csv (20 files)
"""

import sys
import os
from datetime import datetime, timedelta, timezone

import MetaTrader5 as mt5
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from src.utils.broker_clock import (  # noqa: E402
    broker_epoch_to_utc,
    resolve_rule,
    utc_to_broker_naive,
)
from src.utils.research_timebase import write_sidecar  # noqa: E402

# F7: MT5 bar epochs are the BROKER SERVER's wall clock, not UTC. This script wrote
# data/historical_2026 --- the directory most research code reads --- with
# ``fromtimestamp(ts, tz=utc)`` and no offset, so every stamp in it is 2-3 h ahead of
# real UTC. See src/utils/broker_clock.py for the measured rule (US DST calendar, NOT
# the EET/EEST one the audits asserted). Both the request window and the output stamps
# have to be translated; correcting only the stamps shifts the covered range instead.
BROKER_SERVER = os.environ.get("GTOS_EXPORT_BROKER_SERVER", "FTMO-Server3")
BROKER_CLOCK = resolve_rule(BROKER_SERVER)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

START_DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)
END_DATE   = datetime(2026, 4, 25, tzinfo=timezone.utc)  # exclusive upper bound

SYMBOLS = {
    # --- Already live / observer (re-export for freshness) ---
    "XAUUSD":     "XAUUSD",
    "US30_cash":  "US30.cash",
    "USDJPY":     "USDJPY",
    "GBPJPY":     "GBPJPY",
    "GBPUSD":     "GBPUSD",
    "EURUSD":     "EURUSD",
    "NAS100":     "US100.cash",
    # --- FX majors ---
    "AUDUSD":     "AUDUSD",
    "USDCAD":     "USDCAD",
    "USDCHF":     "USDCHF",
    "NZDUSD":     "NZDUSD",
    # --- FX crosses ---
    "EURJPY":     "EURJPY",
    "AUDJPY":     "AUDJPY",
    "EURGBP":     "EURGBP",
    "CHFJPY":     "CHFJPY",
    # --- Commodities ---
    "XAGUSD":     "XAGUSD",
    "USOIL_cash": "USOIL.cash",
    "UKOIL_cash": "UKOIL.cash",
    # --- Indices ---
    "SPX500":     "US500.cash",
    "GER40":      "GER40.cash",
    "UK100":      "UK100.cash",
    "JP225":      "JP225.cash",
    # --- Crypto ---
    "BTCUSD":     "BTCUSD",
    "ETHUSD":     "ETHUSD",
}

TIMEFRAMES = {
    "M15": 15,
    "H1":  16385,
    "H4":  16388,
    "D1":  16408,
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "historical_2026")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    terminal_path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    if not mt5.initialize(path=terminal_path):
        # fallback: try without explicit path
        if not mt5.initialize():
            print(f"ERROR: MT5 initialize() failed — error {mt5.last_error()}")
            sys.exit(1)

    print(f"MT5 connected: {mt5.terminal_info().name}")
    print(f"Exporting {START_DATE.date()} -> {END_DATE.date()}\n")

    results = []
    errors  = []

    for alias, mt5_symbol in SYMBOLS.items():
        # Ensure the symbol is enabled in Market Watch for this session —
        # some brokers (e.g., FTMO demo) require explicit symbol_select
        # before copy_rates_range returns data even though the symbol is
        # live-quoted in the GUI Market Watch. Silently succeeds for already
        # enabled symbols.
        if not mt5.symbol_select(mt5_symbol, True):
            print(f"  WARN  {alias:12s} — symbol_select failed "
                  f"(error: {mt5.last_error()})")

        for tf_name, tf_const in TIMEFRAMES.items():

            # Request in broker wall clock. The UTC -> broker map is exact and
            # monotonic, so no widening is needed; the true-UTC trim below is exact.
            rates = mt5.copy_rates_range(
                mt5_symbol,
                tf_const,
                utc_to_broker_naive(START_DATE, BROKER_CLOCK).replace(tzinfo=timezone.utc),
                utc_to_broker_naive(END_DATE, BROKER_CLOCK).replace(tzinfo=timezone.utc),
            )

            if rates is None or len(rates) == 0:
                msg = (f"  WARN  {alias:12s} {tf_name:4s} — no data "
                       f"(mt5 error: {mt5.last_error()})")
                print(msg)
                errors.append(msg)
                continue

            df = pd.DataFrame(rates)[["time", "open", "high", "low", "close", "tick_volume"]]
            df.rename(columns={"tick_volume": "volume"}, inplace=True)

            df["time_utc"] = df["time"].apply(lambda ts: broker_epoch_to_utc(ts, BROKER_CLOCK))
            # Trim in true UTC so START_DATE/END_DATE mean what they say. A D1 bar is a
            # BROKER day, so its true-UTC open is 02:00/03:00 of the previous calendar
            # day --- the date label necessarily moves for daily bars, which is the
            # single largest semantic consequence of this repair.
            df = df[(df["time_utc"] >= START_DATE) & (df["time_utc"] < END_DATE)]
            if df.empty:
                msg = f"  WARN  {alias:12s} {tf_name:4s} — no bars inside the true-UTC window"
                print(msg)
                errors.append(msg)
                continue

            # D1 is written with a FULL timestamp, not a bare date. A broker daily bar
            # opens at 00:00 SERVER, which is 21:00/22:00 UTC on the PREVIOUS calendar
            # day, so a bare "%Y-%m-%d" would throw away the time-of-day the correction
            # just produced and a reader would parse it back as midnight --- a silent
            # 21-22 h error, and worse than the uncorrected file. The sidecar declares
            # the basis; the stamp has to be able to express it.
            fmt = "%Y-%m-%d %H:%M:%S"
            offsets = sorted({
                int((datetime.fromtimestamp(ts, tz=timezone.utc) - u).total_seconds())
                for ts, u in zip(df["time"], df["time_utc"])
            })
            df["time"] = df["time_utc"].apply(lambda u: u.strftime(fmt))
            df = df.drop(columns=["time_utc"])

            df.sort_values("time", inplace=True)

            fname = f"{alias}_{tf_name}.csv"
            fpath = os.path.join(OUTPUT_DIR, fname)
            df.to_csv(fpath, index=False)
            write_sidecar(
                fpath,
                basis="true_utc",
                rule=BROKER_CLOCK,
                evidence=(
                    f"Broker epochs corrected to true UTC at export time using "
                    f"{BROKER_CLOCK.name} for {BROKER_SERVER}. Offsets applied (s): {offsets}."
                ),
                server=BROKER_SERVER,
                extra={"broker_offset_seconds_applied": offsets,
                       "export_tool": "scripts/export_mt5_historical.py"},
            )

            first = df["time"].iloc[0]
            last  = df["time"].iloc[-1]
            n     = len(df)
            print(f"  OK    {alias:12s} {tf_name:4s}  {n:5d} candles  {first}  ->  {last}")
            results.append((alias, tf_name, n, first, last))

    mt5.shutdown()

    print(f"\n{'='*60}")
    print(f"Done.  {len(results)} files written, {len(errors)} skipped.")
    if errors:
        print("\nSkipped:")
        for e in errors:
            print(e)


if __name__ == "__main__":
    main()
