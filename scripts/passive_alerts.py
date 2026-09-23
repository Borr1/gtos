"""
Layer 1 Passive Alerts — Real-time price event detection.
Runs alongside trading processes. Logs events to JSONL. Zero AI calls.

Usage:
  python scripts/passive_alerts.py --symbol XAUUSD

Runs continuously during kill zones, sleeps between them.
"""

import MetaTrader5 as mt5
import json
import os
import time
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MSO_PATH = PROJECT_ROOT / "knowledge_base" / "pipeline_state" / "02_market_state.json"
CONFIG_PATH = PROJECT_ROOT / "config" / "agent_config.yaml"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _load_config(symbol: str) -> dict:
    """Return the instrument-level config block for *symbol*."""
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    return cfg.get("instruments", {}).get(symbol, {})


def _kill_zone_windows(inst_cfg: dict) -> list[tuple[int, int]]:
    """Return list of (start_hour_utc, end_hour_utc) from config kill zones."""
    windows = []
    kzs = inst_cfg.get("market", {}).get("kill_zones", {})
    for _name, kz in kzs.items():
        start = int(kz["start_utc"].split(":")[0])
        end = int(kz["end_utc"].split(":")[0])
        if end == 0:
            end = 24
        windows.append((start, end))
    return windows


def _in_kill_zone(windows: list[tuple[int, int]], now_utc: datetime) -> bool:
    h = now_utc.hour
    m = now_utc.minute
    t = h + m / 60.0
    for start, end in windows:
        if start <= t < end:
            return True
    return False


# ------------------------------------------------------------------
# Monitor
# ------------------------------------------------------------------

class PassiveAlertMonitor:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.inst_cfg = _load_config(symbol)
        self.mt5_symbol = (
            self.inst_cfg.get("market", {}).get("mt5_symbol")
            or self.inst_cfg.get("market", {}).get("symbol", symbol)
        )
        self.kz_windows = _kill_zone_windows(self.inst_cfg)
        self.poll_interval = 10  # seconds

        self.log_dir = PROJECT_ROOT / "knowledge_base" / "live_alerts" / symbol
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Reference levels — refreshed from MSO every 15 min
        self.ob_zones: list[dict] = []
        self.session_levels: dict = {}
        self.h1_atr: float = 0.0
        self.m15_atr: float = 0.0

        # Runtime state
        self._recent_prices: list[float] = []
        self._alert_cooldowns: dict[str, float] = {}
        self._last_level_refresh: float = 0.0

    # ---- Reference level loading ----

    def load_reference_levels(self) -> None:
        """Load OB zones, session levels and ATR from the latest MSO."""
        if not MSO_PATH.exists():
            return
        try:
            with open(MSO_PATH) as f:
                mso = json.load(f)

            # H1 order blocks — fields: high, low, type, mitigated
            h1 = mso.get("timeframes", {}).get("H1", {})
            self.ob_zones = [
                {"high": ob["high"], "low": ob["low"], "type": ob["type"]}
                for ob in h1.get("order_blocks", [])
                if not ob.get("mitigated", True)
            ]
            self.h1_atr = h1.get("atr_14", 0.0)

            m15 = mso.get("timeframes", {}).get("M15", {})
            self.m15_atr = m15.get("atr_14", 0.0) if m15 else 0.0

            # Session levels — all optional floats
            self.session_levels = mso.get("session_levels", {})

            logger.info(
                "Loaded %d OB zones, H1 ATR=%.2f, M15 ATR=%.2f",
                len(self.ob_zones), self.h1_atr, self.m15_atr,
            )
        except Exception as e:
            logger.warning("Failed to load reference levels: %s", e)

    # ---- Event detection ----

    def check_events(self, price: float) -> list[dict]:
        events: list[dict] = []

        # 1. OB zone touches
        for ob in self.ob_zones:
            if ob["low"] <= price <= ob["high"]:
                events.append({
                    "type": "OB_ZONE_TOUCH",
                    "ob_high": ob["high"],
                    "ob_low": ob["low"],
                    "ob_type": ob["type"],
                    "price": price,
                })

        # 2. Session level proximity (within 5% of H1 ATR)
        if self.h1_atr > 0:
            threshold = self.h1_atr * 0.05
            for name, lvl in self.session_levels.items():
                if not isinstance(lvl, (int, float)) or lvl <= 0:
                    continue
                dist = abs(price - lvl)
                if dist < threshold:
                    events.append({
                        "type": "LEVEL_PROXIMITY",
                        "level_name": name,
                        "level_price": lvl,
                        "price": price,
                        "distance": round(dist, 4),
                    })

        # 3. Flash displacement (60s move > 2x M15 ATR)
        if len(self._recent_prices) >= 6 and self.m15_atr > 0:
            price_60s_ago = self._recent_prices[-6]
            move = abs(price - price_60s_ago)
            if move > 2.0 * self.m15_atr:
                events.append({
                    "type": "FLASH_DISPLACEMENT",
                    "magnitude_atr": round(move / self.m15_atr, 2),
                    "direction": "bullish" if price > price_60s_ago else "bearish",
                    "move_points": round(move, 4),
                    "price_from": price_60s_ago,
                    "price_to": price,
                })

        # 4. Open trade stress (MAE > 0.5R)
        try:
            positions = mt5.positions_get(symbol=self.mt5_symbol)
            if positions:
                for pos in positions:
                    sl = pos.sl
                    if not sl or sl <= 0:
                        continue
                    entry = pos.price_open
                    sl_distance = abs(entry - sl)
                    if sl_distance <= 0:
                        continue
                    # type 0 = BUY, type 1 = SELL
                    if pos.type == 0:
                        current_r = (price - entry) / sl_distance
                    else:
                        current_r = (entry - price) / sl_distance
                    if current_r < -0.5:
                        events.append({
                            "type": "TRADE_STRESS",
                            "ticket": pos.ticket,
                            "current_r": round(current_r, 3),
                            "entry": entry,
                            "current": price,
                            "sl": sl,
                        })
        except Exception:
            pass  # MT5 not available in tests

        return events

    # ---- Logging ----

    def log_event(self, event: dict) -> None:
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        event["symbol"] = self.symbol

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        file_path = self.log_dir / f"{date_str}.jsonl"

        with open(file_path, "a") as f:
            f.write(json.dumps(event) + "\n")

        logger.info("ALERT: %s", json.dumps(event, default=str)[:200])

    def _cooldown_ok(self, event: dict) -> bool:
        """Return True if this event type hasn't fired in the last 5 min."""
        key = f"{event['type']}_{event.get('ob_high', event.get('level_name', ''))}"
        last = self._alert_cooldowns.get(key, 0)
        if time.time() - last > 300:
            self._alert_cooldowns[key] = time.time()
            return True
        return False

    # ---- Main loop ----

    def run(self) -> None:
        if not mt5.initialize():
            logger.error("MT5 initialization failed")
            return

        logger.info(
            "Passive alert monitor started for %s (mt5=%s), %d KZ windows",
            self.symbol, self.mt5_symbol, len(self.kz_windows),
        )

        try:
            while True:
                now = datetime.now(timezone.utc)

                if not _in_kill_zone(self.kz_windows, now):
                    time.sleep(60)
                    continue

                # Refresh reference levels every 15 min
                if time.time() - self._last_level_refresh > 900:
                    self.load_reference_levels()
                    self._last_level_refresh = time.time()

                # Get current price
                tick = mt5.symbol_info_tick(self.mt5_symbol)
                if not tick:
                    time.sleep(self.poll_interval)
                    continue

                price = (tick.bid + tick.ask) / 2

                self._recent_prices.append(price)
                if len(self._recent_prices) > 60:
                    self._recent_prices = self._recent_prices[-60:]

                events = self.check_events(price)
                for event in events:
                    if self._cooldown_ok(event):
                        event["spread"] = round(tick.ask - tick.bid, 4)
                        self.log_event(event)

                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            logger.info("Passive alert monitor stopped")
        finally:
            mt5.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Passive price alert monitor")
    parser.add_argument("--symbol", required=True, help="Instrument symbol (e.g. XAUUSD)")
    args = parser.parse_args()

    monitor = PassiveAlertMonitor(args.symbol)
    monitor.run()
