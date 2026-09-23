"""B8 — the paired-treatment shadow harness.

WHY THIS EXISTS
---------------
`LANE_4_BREADTH_AND_THROTTLES_V1.md` §7.1 measured that the armed book cannot answer its
own questions: a six-week answer needs 17.4x its effective breadth and no rearrangement of
the 29-sleeve estate supplies it (iso-IR law, slope -0.425 +/- 0.148, p 0.008).  It also
measured the one channel that does convert breadth into speed -- a **paired treatment**,
the same decision scored two ways, whose difference-SD is 0.3437 R against the unpaired
1.4566 R.

This package is that channel, built.  It takes the estate's own decisions, evaluates each
one under N treatment arms that differ in exactly one dimension, and reports the paired
difference with an honest error bar, a sequential stopping rule and a multiplicity ledger.

WHAT IS AND IS NOT PAIRED, AND WHY THE DISTINCTION IS THE WHOLE INSTRUMENT
--------------------------------------------------------------------------
A paired design that silently correlates its arms produces confident nonsense: if two arms
are the same contract under two names, every delta is 0, the SD is 0, and the harness
reports infinite power on a question it never asked.  So pairing here is *typed*, and each
type carries its own effective-n rule (:mod:`paired_stats`):

``TRADE_PAIRED``
    Same intent, same bars, same entry; the exit contract or the charged cost differs.
    Every intent contributes a delta.  This is the class Lane 4 priced at 4.25x noise
    reduction and it is the only class that gets it.

``ENTRY_PAIRED``
    Same *signal*; the entry instant differs, so the two arms do not share a fill.  The
    common-cause cancellation is weaker and the harness prices a grid confound explicitly
    with a third arm (see :mod:`questions`, ``entry_hour``).

``SELECTION_PAIRED``
    The treatment *removes* decisions.  Concordant trades contribute an exact 0 and carry
    no information; the whole signal lives in the discordant set.  Counting the zeros as
    sample size is the single easiest way to manufacture a fake answer here, so this class
    reports ``n_informative`` and powers off it.

``BOOK_PAIRED``
    A portfolio throttle (the cluster cap).  Pairing is at the day level after the book is
    constructed, and the unit of resampling is the day.

ZERO BROKER MUTATION, BY CONSTRUCTION
--------------------------------------
Nothing in this package imports ``MetaTrader5``, constructs an order request, or reaches a
network.  The live-shadow entry point reuses ``ShadowReadOnlyMT5Adapter`` whose
``order_send`` raises (``mt5_read_only.py:216``), and :mod:`controls` proves both the
static and the dynamic half rather than asserting them.
"""

__all__ = ["substrate", "arms", "paired_stats", "questions", "evaluate", "controls"]
