"""Chart renderer for M15 candlestick charts with SMC annotations.

Produces TradingView-style dark-background charts with order block zones,
structure break levels, and session levels overlaid. Used for vision-enhanced
AI analysis.

Requires: plotly, kaleido
"""

from __future__ import annotations

import base64
from typing import Optional

import plotly.graph_objects as go


# ── Color palette (dark theme, trader-standard) ────────────────────────
_BG_COLOR = "#131722"        # TradingView dark bg
_GRID_COLOR = "#1e222d"
_TEXT_COLOR = "#d1d4dc"
_CANDLE_UP = "#26a69a"       # green
_CANDLE_DOWN = "#ef5350"     # red
_OB_BULLISH = "rgba(38, 166, 154, 0.18)"    # teal, transparent
_OB_BEARISH = "rgba(239, 83, 80, 0.18)"     # red, transparent
_OB_BORDER_BULL = "rgba(38, 166, 154, 0.5)"
_OB_BORDER_BEAR = "rgba(239, 83, 80, 0.5)"
_LEVEL_ASIAN = "#2962ff"     # blue
_LEVEL_PDH = "#ab47bc"       # purple
_LEVEL_LONDON = "#ff9800"    # orange
_BREAK_LINE = "#ffeb3b"      # yellow
_PD_DISCOUNT = "rgba(38, 166, 154, 0.06)"
_PD_PREMIUM = "rgba(239, 83, 80, 0.06)"
_PD_OTE = "rgba(255, 235, 59, 0.08)"


def render_chart(
    m15_candles: list[dict],
    order_blocks: list[dict] | None = None,
    structure_breaks: list[dict] | None = None,
    session_levels: dict | None = None,
    premium_discount: dict | None = None,
    kill_zone: str = "london",
    current_price: float = 0.0,
    save_path: str | None = None,
) -> bytes:
    """Render an annotated M15 candlestick chart. Returns PNG bytes.

    Parameters
    ----------
    m15_candles : list of dicts with keys: time, open, high, low, close
    order_blocks : list of dicts with keys: type, high, low, causing_event_type
    structure_breaks : list of dicts with keys: type, direction, level_broken, time
    session_levels : dict with keys: asian_high, asian_low, pdh, pdl, london_high, london_low
    premium_discount : dict with keys: equilibrium_50, fib_62, fib_79 (optional)
    kill_zone : "london" or "ny"
    current_price : float, last close price
    save_path : if set, also saves PNG to this path
    """
    if not m15_candles:
        raise ValueError("No candle data provided")

    order_blocks = order_blocks or []
    structure_breaks = structure_breaks or []
    session_levels = session_levels or {}

    # Parse candle data
    times = [c["time"] for c in m15_candles]
    opens = [c["open"] for c in m15_candles]
    highs = [c["high"] for c in m15_candles]
    lows = [c["low"] for c in m15_candles]
    closes = [c["close"] for c in m15_candles]

    # Use integer indices for x-axis (avoids time gaps)
    x_indices = list(range(len(m15_candles)))

    # Build tick labels (show every 4th time)
    tick_vals = x_indices[::4]
    tick_labels = [times[i][-8:-3] if len(times[i]) >= 8 else times[i] for i in tick_vals]

    fig = go.Figure()

    # ── Candlesticks ──────────────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=x_indices,
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        increasing_line_color=_CANDLE_UP,
        decreasing_line_color=_CANDLE_DOWN,
        increasing_fillcolor=_CANDLE_UP,
        decreasing_fillcolor=_CANDLE_DOWN,
        line=dict(width=1),
        name="M15",
        showlegend=False,
    ))

    # Price range for y-axis
    y_min = min(lows) - (max(highs) - min(lows)) * 0.05
    y_max = max(highs) + (max(highs) - min(lows)) * 0.05
    x_min = -0.5
    x_max = len(m15_candles) - 0.5

    # ── Order Block zones ─────────────────────────────────────────────
    for ob in order_blocks:
        is_bull = ob.get("type") == "bullish"
        fill_color = _OB_BULLISH if is_bull else _OB_BEARISH
        border_color = _OB_BORDER_BULL if is_bull else _OB_BORDER_BEAR
        event_type = ob.get("causing_event_type", "BOS")
        label = f"OB ({event_type})"

        ob_high = ob["high"]
        ob_low = ob["low"]

        # Only draw if visible in price range
        if ob_high < y_min or ob_low > y_max:
            continue

        fig.add_shape(
            type="rect",
            x0=x_min, x1=x_max,
            y0=ob_low, y1=ob_high,
            fillcolor=fill_color,
            line=dict(color=border_color, width=1),
            layer="below",
        )
        # Label
        fig.add_annotation(
            x=x_max - 1, y=(ob_high + ob_low) / 2,
            text=label,
            showarrow=False,
            font=dict(size=9, color=border_color),
            xanchor="right",
        )

    # ── Structure break levels ────────────────────────────────────────
    for sb in structure_breaks:
        level = sb.get("level_broken", 0)
        if level < y_min or level > y_max:
            continue
        sb_type = sb.get("type", "BOS")
        sb_dir = sb.get("direction", "")
        label = f"{sb_type} {sb_dir}"

        fig.add_hline(
            y=level,
            line=dict(color=_BREAK_LINE, width=1.5, dash="dot"),
            annotation_text=label,
            annotation_position="top left",
            annotation_font=dict(size=9, color=_BREAK_LINE),
        )

    # ── Session levels ────────────────────────────────────────────────
    level_specs = [
        ("asian_high", "Asian H", _LEVEL_ASIAN, "dash"),
        ("asian_low", "Asian L", _LEVEL_ASIAN, "dash"),
        ("pdh", "PDH", _LEVEL_PDH, "dash"),
        ("pdl", "PDL", _LEVEL_PDH, "dash"),
    ]
    if kill_zone == "ny":
        level_specs.extend([
            ("london_high", "London H", _LEVEL_LONDON, "dash"),
            ("london_low", "London L", _LEVEL_LONDON, "dash"),
        ])

    for key, label, color, dash in level_specs:
        val = session_levels.get(key)
        if val is None or val == 0 or val < y_min or val > y_max:
            continue
        fig.add_hline(
            y=val,
            line=dict(color=color, width=1, dash=dash),
            annotation_text=label,
            annotation_position="top right",
            annotation_font=dict(size=8, color=color),
        )

    # ── Premium / Discount zones (optional) ───────────────────────────
    if premium_discount:
        eq = premium_discount.get("equilibrium_50", 0)
        f62 = premium_discount.get("fib_62", 0)
        f79 = premium_discount.get("fib_79", 0)

        if eq > 0 and y_min < eq < y_max:
            fig.add_hline(
                y=eq,
                line=dict(color="rgba(255,255,255,0.3)", width=0.5, dash="dot"),
                annotation_text="EQ 50%",
                annotation_position="bottom right",
                annotation_font=dict(size=7, color="rgba(255,255,255,0.4)"),
            )

    # ── Current price marker ──────────────────────────────────────────
    if current_price > 0:
        fig.add_annotation(
            x=len(m15_candles) - 1, y=current_price,
            text=f"▸ {current_price:.2f}",
            showarrow=False,
            font=dict(size=9, color="#ffffff"),
            xanchor="left",
            xshift=10,
        )

    # ── Layout ────────────────────────────────────────────────────────
    kz_label = "London Open" if kill_zone == "london" else "NY Open"
    date_label = times[0][:10] if times else ""

    fig.update_layout(
        title=dict(
            text=f"XAUUSD M15 — {kz_label} — {date_label}",
            font=dict(size=13, color=_TEXT_COLOR),
            x=0.5,
        ),
        template="plotly_dark",
        paper_bgcolor=_BG_COLOR,
        plot_bgcolor=_BG_COLOR,
        width=800,
        height=500,
        margin=dict(l=60, r=80, t=40, b=40),
        xaxis=dict(
            showgrid=False,
            rangeslider=dict(visible=False),
            tickvals=tick_vals,
            ticktext=tick_labels,
            tickfont=dict(size=8, color=_TEXT_COLOR),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=_GRID_COLOR,
            tickfont=dict(size=9, color=_TEXT_COLOR),
            side="right",
        ),
        showlegend=False,
    )

    # ── Export ─────────────────────────────────────────────────────────
    png_bytes = fig.to_image(format="png", scale=2)

    if save_path:
        from pathlib import Path
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        Path(save_path).write_bytes(png_bytes)

    return png_bytes


def chart_to_base64(png_bytes: bytes) -> str:
    """Convert PNG bytes to base64 string for Claude vision API."""
    return base64.b64encode(png_bytes).decode("utf-8")


def render_chart_from_mso(mso, m15_candles: list[dict], kill_zone: str,
                          save_path: str | None = None) -> bytes:
    """Convenience: render chart from MSO + raw M15 candles.

    Parameters
    ----------
    mso : MarketStateObject (or dict with same structure)
    m15_candles : raw M15 candle list for this session window
    kill_zone : "london" or "ny"
    save_path : optional path to save PNG
    """
    # Extract from MSO (handle both Pydantic and dict)
    if hasattr(mso, "timeframes"):
        tfs = mso.timeframes
        h1 = tfs.get("H1")
        sl = mso.session_levels
    else:
        tfs = mso.get("timeframes", {})
        h1 = tfs.get("H1", {})
        sl = mso.get("session_levels", {})

    # Order blocks
    if h1 and hasattr(h1, "order_blocks"):
        obs = h1.order_blocks
    elif isinstance(h1, dict):
        obs = h1.get("order_blocks", [])
    else:
        obs = []

    def _get(obj, key, default=None):
        """Get attribute from Pydantic model or dict."""
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    order_blocks = [
        {
            "type": _get(ob, "type", ""),
            "high": _get(ob, "high", 0),
            "low": _get(ob, "low", 0),
            "causing_event_type": _get(ob, "causing_event_type", "BOS"),
        }
        for ob in obs
        if not _get(ob, "mitigated", False)
    ]

    # Structure breaks
    if h1 and hasattr(h1, "structure_events"):
        events = h1.structure_events
    elif isinstance(h1, dict):
        events = h1.get("structure_events", [])
    else:
        events = []

    structure_breaks = [
        {
            "type": _get(ev, "type", ""),
            "direction": _get(ev, "direction", ""),
            "level_broken": _get(ev, "level_broken", 0),
        }
        for ev in events
    ]

    # Session levels
    if hasattr(sl, "asian_high"):
        session_levels = {
            "asian_high": sl.asian_high,
            "asian_low": sl.asian_low,
            "pdh": sl.pdh,
            "pdl": sl.pdl,
            "london_high": getattr(sl, "london_high", None),
            "london_low": getattr(sl, "london_low", None),
        }
    elif isinstance(sl, dict):
        session_levels = sl
    else:
        session_levels = {}

    # Premium/discount
    pd_data = None
    if h1:
        pd_raw = getattr(h1, "premium_discount", None) if hasattr(h1, "premium_discount") else (h1.get("premium_discount") if isinstance(h1, dict) else None)
        if pd_raw:
            pd_data = {
                "equilibrium_50": _get(pd_raw, "equilibrium_50", 0),
                "fib_62": _get(pd_raw, "fib_62", 0),
                "fib_79": _get(pd_raw, "fib_79", 0),
            }

    current_price = m15_candles[-1]["close"] if m15_candles else 0

    return render_chart(
        m15_candles=m15_candles[-40:],
        order_blocks=order_blocks,
        structure_breaks=structure_breaks[-5:],  # last 5 breaks
        session_levels=session_levels,
        premium_discount=pd_data,
        kill_zone=kill_zone,
        current_price=current_price,
        save_path=save_path,
    )
