"""J46-J49 v2 policy helpers (pure functions, no I/O).

Validated configuration: partial=0%, BE immediate-on-TP1, time-stop 12 M15
bars, TP1 at 3.0R, higher target at 6.0R. Validation: n=321, p=3.3e-20,
+0.742R/trade vs production. See commit be33522 for sweep semantics and
124de56 for SHIP recap.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def _section(config: dict) -> dict:
    pm = config.get("position_mgmt", {}) if isinstance(config, dict) else {}
    return pm.get("j46_j49_v2", {}) if isinstance(pm, dict) else {}


def is_enabled(config: dict) -> bool:
    return bool(_section(config).get("enabled", False))


def get_policy_params(config: dict) -> dict:
    section = _section(config)
    return {
        "partial_close_ratio": float(section.get("partial_close_ratio", 0.0)),
        "be_trigger": str(section.get("be_trigger", "immediate_on_tp1")),
        "time_stop_bars": int(section.get("time_stop_bars", 12)),
        "tp1_distance_r": float(section.get("tp1_distance_r", 3.0)),
        "higher_target_r": float(section.get("higher_target_r", 6.0)),
    }


def compute_targets(
    entry: float,
    sl_distance: float,
    direction: str,
    config: dict,
) -> tuple[float, float]:
    """Returns (tp1_at_3r, tp2_at_6r)."""
    params = get_policy_params(config)
    tp1_r = params["tp1_distance_r"]
    tp2_r = params["higher_target_r"]
    if direction == "LONG":
        return (entry + tp1_r * sl_distance, entry + tp2_r * sl_distance)
    return (entry - tp1_r * sl_distance, entry - tp2_r * sl_distance)


def bars_elapsed_since_fill(
    entry_time: datetime,
    now: Optional[datetime] = None,
) -> int:
    """M15 bars elapsed since fill, integer floor."""
    if now is None:
        now = datetime.now(timezone.utc)
    if entry_time.tzinfo is None:
        entry_time = entry_time.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    delta_seconds = (now - entry_time).total_seconds()
    if delta_seconds <= 0:
        return 0
    return int(delta_seconds // (15 * 60))
