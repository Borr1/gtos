"""Pydantic models for Market State Object (Component 2 output).

Written to pipeline_state/02_market_state.json by Component 2.
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class Swing(BaseModel):
    index: int
    type: Literal["high", "low"]
    price: float
    time: str


class StructureEvent(BaseModel):
    type: Literal["BOS", "CHoCH"]
    direction: Literal["bullish", "bearish"]
    level_broken: float
    close_price: float
    candle_index: int
    time: str
    displacement_present: Optional[bool] = False
    displacement_ratio: float = Field(
        default=0.0,
        description="Body of BOS candle / avg candle body",
    )


class StructureAnalysis(BaseModel):
    direction: Optional[Literal["bullish", "bearish", "transitional", "insufficient_data"]] = None
    protected_swing: Optional[Swing] = None
    swing_sequence: list[str] = Field(
        default_factory=list,
        description='e.g. ["HH", "HL", "HH", "HL"]',
    )
    hh_count: int = 0
    hl_count: int = 0
    lh_count: int = 0
    ll_count: int = 0


class OrderBlock(BaseModel):
    type: Literal["bullish", "bearish"]
    high: float
    low: float
    open: float
    close: float
    formation_index: int
    formation_time: str
    causing_bos_index: int
    mitigated: bool = False
    causing_event_type: str = "BOS"  # "BOS" or "CHoCH"
    # Multi-touch tracking — count of candles AFTER formation that overlap the
    # zone (candle.high >= low AND candle.low <= high). Formation candle excluded.
    # Evidence: Touch-1 WR 72.7% (n=23,575) vs Touch-2+ WR 31.5% (n=82,572) —
    # see research/diagnostics/zone_age_analysis/ob_zone_age_v1.md.
    # Default 0 preserves backward compatibility for callers that build OBs
    # without populating the field.
    touch_count: int = 0


class BreakerBlock(BaseModel):
    """A failed order block that flipped into a retest zone."""
    zone_high: float
    zone_low: float
    direction: str  # "bullish" or "bearish" — the BREAKER direction
    original_ob_direction: str  # the OB that failed
    formation_time: str  # when the original OB formed
    mitigation_time: str  # when the OB was broken through
    causing_event: str  # "BOS", "CHoCH", or "price_action"
    is_retested: bool = False  # has price come back to this zone?
    timeframe: str = "H1"


class FairValueGap(BaseModel):
    type: Literal["bullish", "bearish"]
    top: float
    bottom: float
    midpoint: float
    candle_indices: list[int]
    formation_time: str
    filled: bool = False
    timeframe: str = "M15"
    poi_id: str = ""
    source_candle_times: list[str] = Field(default_factory=list)
    created_at_utc: str = ""
    state_asof_utc: str = ""
    age_hours: float = 0.0
    touch_count: int = 0
    overlap_bar_count: int = 0
    touch_episode_count: int = 0
    max_mitigation_fraction: float = 0.0
    first_touch_time_utc: str = ""
    last_touch_time_utc: str = ""
    mitigation_status: str = "untouched"
    invalidated: bool = False
    invalidation_time_utc: str = ""
    invalidation_reason: str = ""
    terminal_time_utc: str = ""
    terminal_reason: str = ""
    terminal_frozen: bool = False
    poi_state_hash_sha256: str = ""
    poi_state_contract_status: str = ""
    poi_state: dict[str, Any] = Field(default_factory=dict)


class PriceZone(BaseModel):
    top: float
    bottom: float


class PremiumDiscount(BaseModel):
    impulse_low: float
    impulse_high: float
    equilibrium_50: float
    fib_62: float
    fib_79: float
    discount_zone: PriceZone
    premium_zone: PriceZone
    ote_zone: PriceZone


class EqualLevel(BaseModel):
    price: float
    count: int
    candle_indices: list[int]


class LiquidityPool(BaseModel):
    type: Literal[
        "asian_high", "asian_low", "pdh", "pdl",
        "equal_highs", "equal_lows", "session_high", "session_low",
        "london_high", "london_low",
    ]
    price: float
    side: Literal["high", "low"]


class LiquiditySweep(BaseModel):
    pool: LiquidityPool
    sweep_type: Literal["sweep", "run"]
    wick_extreme: float
    body_close: float
    candle_index: int
    time: str


class EconEvent(BaseModel):
    name: str
    time: str
    importance: int


class DataQuality(BaseModel):
    all_timeframes_complete: bool
    spread_normal: bool
    mt5_connected: bool
    timestamp_utc: str


class TimeframeState(BaseModel):
    swings: list[Swing] = Field(default_factory=list)
    structure: StructureAnalysis
    structure_events: list[StructureEvent] = Field(default_factory=list)
    order_blocks: list[OrderBlock] = Field(default_factory=list)
    breaker_blocks: list[BreakerBlock] = Field(default_factory=list)
    fair_value_gaps: list[FairValueGap] = Field(default_factory=list)
    premium_discount: Optional[PremiumDiscount] = None
    avg_candle_body: float = 0.0
    atr_14: float = 0.0
    # Order-flow proxies (CLV + BVC) — computed from OHLCV, no tick data required
    clv_current: Optional[float] = None    # Close Location Value of current candle [-1, +1]
    clv_avg_5: Optional[float] = None      # Mean CLV over last 5 candles
    bvc_buy_fraction: Optional[float] = None   # BVC buy fraction for current candle [0, 1]
    net_flow_5: Optional[float] = None     # Cumulative BVC net flow over last 5 candles
    # Session-specific ATR (XAUUSD M15 only — Ibikunle 2018 W-shaped intraday vol)
    atr_session: Optional[float] = None    # ATR(14) for the current session window
    session_vol_ratio: Optional[float] = None  # atr_session / atr_14 (>1 = elevated vol)


class SessionLevels(BaseModel):
    asian_high: float
    asian_low: float
    pdh: float
    pdl: float
    session_high: Optional[float] = None
    session_low: Optional[float] = None
    london_high: Optional[float] = None
    london_low: Optional[float] = None


class MarketStateObject(BaseModel):
    timestamp_utc: str
    timeframes: dict[str, TimeframeState]
    session_levels: SessionLevels
    equal_highs: list[EqualLevel] = Field(default_factory=list)
    equal_lows: list[EqualLevel] = Field(default_factory=list)
    liquidity_pools: list[LiquidityPool] = Field(default_factory=list)
    detected_sweeps: list[LiquiditySweep] = Field(default_factory=list)
    spread_cents: Optional[float] = None
    high_impact_events: Optional[list[EconEvent]] = None
    data_quality: DataQuality
