"""Guard the live idxrev generation surface = the validated 5 indices. The admission.py confidence-
registry carries a stale 8-symbol metadata tuple (an older research pocket) that is INERT — live
generation + sizing never read it — and it mirrors the locked route twin, so it is intentionally NOT
edited here. This test locks the truth the live book actually trades, so if anyone ever wires the
metadata tuple into generation, or widens IDXREV_ON_SURFACE, it fails loudly."""
from src.components.ultimate_book.sleeves import index_jpy
from src.components.ultimate_book.sleeves.registry import BUILT


VALIDATED_IDXREV = {"SPX500", "UK100", "JP225", "GER40", "US30_cash"}
OFF_SURFACE = ("FRA40_cash", "EU50_cash", "US2000_cash")   # the 3 in the stale 8-tuple, never traded


def test_live_idxrev_surface_is_the_validated_five():
    assert set(index_jpy.IDXREV_ON_SURFACE) == VALIDATED_IDXREV
    # the registry that drives live GENERATION uses the 5-symbol on_surface (not the 8-symbol metadata)
    assert set(BUILT["idxrev"].on_surface) == VALIDATED_IDXREV


def test_off_surface_indices_generate_nothing():
    """The 3 off-surface symbols in the stale metadata tuple must never produce an idxrev intent."""
    for sym in OFF_SURFACE:
        out = index_jpy.generate(sym, [], "2026-06-15", bar_time=None, bar_times=[],
                                 aux_bars=None, aux_times=None)
        assert out is None
