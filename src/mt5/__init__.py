"""MT5 abstraction layer — factory and public exports."""

from .mt5_interface import MT5Interface, MAGIC_NUMBER, TickData, PositionInfo, OrderResult
from .mt5_mock import MockMT5

#: Modes that open a real MetaTrader connection. Anything outside
#: ``{"mock", *_REAL_MODES}`` is rejected rather than defaulted to real.
_REAL_MODES = frozenset({"demo", "live"})


def create_mt5(mode: str = "mock", **kwargs) -> MT5Interface:
    """Factory: create MT5 connection based on mode.

    mode="mock": MockMT5 for development/testing (macOS)
    mode="demo": RealMT5 connecting to demo account (Windows)
    mode="live": RealMT5 connecting to live account (Windows)
    """
    if mode == "mock":
        return MockMT5(**kwargs)
    if mode not in _REAL_MODES:
        # Previously any unrecognised mode fell through to RealMT5, so a typo
        # ("mok", "simulate", "") opened a real broker connection. Unknown modes
        # now fail closed.
        raise ValueError(
            f"unknown mt5 mode {mode!r}; expected one of "
            f"{sorted({'mock', *_REAL_MODES})}"
        )
    from .mt5_real import RealMT5  # Lazy import — only works on Windows
    return RealMT5(**kwargs)
