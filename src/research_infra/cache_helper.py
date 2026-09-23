"""1-hour TTL cache helper for research/backtest workloads (T0.3, Phase 1).

Purpose
-------
Anthropic's prompt-caching default is 5-minute TTL (``cache_control: {"type":
"ephemeral"}``). For research backtests that stream the same system prompt at
50-1000+ requests in a single batch run, 5-minute TTL forces repeated cache
*creation* (writes cost 1.25x base for 5m, 2x base for 1h), eating most of the
savings. The 1-hour TTL costs 2x base on write but only 0.10x base on read,
so the break-even is **2 reads** — research workloads cross that bar trivially.

Production live trading is on a separate cadence (one prompt every 15 min) and
remains pinned at the 5-minute default. Wiring this helper into production is a
**separate ticket** that requires explicit CEO authorization.

Pricing reference (Anthropic, Sonnet/Opus class):
    base input        : 1.00x
    cache write 5m    : 1.25x base
    cache write 1h    : 2.00x base
    cache read        : 0.10x base   (same for both TTLs)
    output            : ~5.00x base  (unchanged by caching)

What this module provides
-------------------------
1. ``build_cache_control(ttl)`` -> dict | None
       Single source of truth for the cache_control payload shape.
2. ``annotate_system_blocks(blocks, ttl)`` -> list[dict]
       Pure helper that takes the existing system-block shape used in
       ``src/components/primary_analyzer.py:215-221`` and returns a
       cache-annotated copy. **Does not mutate the caller's input.**
3. ``CacheMetrics``
       Lightweight accumulator over Anthropic ``response.usage`` blocks.
       Reports hit-rate + token totals + back-of-envelope savings estimate.

Contract
--------
- ``ttl="5m"`` returns ``{"type": "ephemeral"}`` (the default; written
  explicitly so callers can be unambiguous).
- ``ttl="1h"`` returns ``{"type": "ephemeral", "ttl": "1h"}``.
- ``ttl="none"`` returns ``None``. Callers receiving ``None`` should OMIT the
  ``cache_control`` key from the block entirely (do NOT serialize ``None``
  into the request — Anthropic will reject it).

All functions are pure (no I/O, no API calls). The module never imports from
``src/components/`` and is safe to load from research scripts and notebooks.
"""

from __future__ import annotations

import copy
from typing import Literal

# Public TTL labels. Keep the list closed so typos surface at call sites.
TTL = Literal["5m", "1h", "none"]


def build_cache_control(ttl: TTL = "5m") -> dict | None:
    """Return the ``cache_control`` payload for a given TTL label.

    Parameters
    ----------
    ttl :
        ``"5m"``  -> Anthropic's ephemeral default (5-minute TTL). Returned
                     explicitly so request bodies don't rely on implicit
                     defaults.
        ``"1h"``  -> 1-hour TTL. ~2x write cost, 0.10x read cost. Use for
                     research/backtest batches that hit the same system
                     prompt many times.
        ``"none"`` -> Returns ``None``. The caller is expected to OMIT
                     ``cache_control`` from the block entirely (do not
                     serialize ``None``).

    Returns
    -------
    dict | None
        ``{"type": "ephemeral"}`` for 5m, ``{"type": "ephemeral", "ttl": "1h"}``
        for 1h, or ``None`` for "none".

    Raises
    ------
    ValueError
        If ``ttl`` is not one of the documented labels.
    """
    if ttl == "5m":
        return {"type": "ephemeral"}
    if ttl == "1h":
        return {"type": "ephemeral", "ttl": "1h"}
    if ttl == "none":
        return None
    raise ValueError(
        f"build_cache_control: ttl must be one of '5m', '1h', 'none' (got {ttl!r})"
    )


def annotate_system_blocks(
    system_blocks: list[dict] | str,
    ttl: TTL,
) -> list[dict]:
    """Return a cache-annotated copy of the system blocks.

    Mirrors the shape used by ``src/components/primary_analyzer.py``::

        self._cached_system_blocks = [
            {
                "type": "text",
                "text": <system_text>,
                "cache_control": {"type": "ephemeral"},
            },
        ]

    Behaviour
    ---------
    - String input is wrapped into a single-block list:
      ``[{"type": "text", "text": <s>, "cache_control": ...}]``.
    - List input is **deep-copied** (no input mutation), and only the LAST
      block in the list receives ``cache_control``. Prior blocks have any
      existing ``cache_control`` key removed.
    - ``ttl="none"`` strips ``cache_control`` from every block (the result is
      a clean, uncached request body).

    Why annotate the last block? Anthropic's prompt-cache reads the
    ``cache_control`` marker on each block as a cache breakpoint. Putting it
    on the LAST block caches the entire concatenated system prompt up to that
    point — exactly what we want for the static portion that doesn't change
    candle to candle.

    Parameters
    ----------
    system_blocks :
        Either a plain string OR a list of Anthropic content blocks
        (typically ``[{"type": "text", "text": "..."}]``).
    ttl :
        ``"5m"``, ``"1h"``, or ``"none"`` — passed straight to
        :func:`build_cache_control`.

    Returns
    -------
    list[dict]
        New list-of-blocks with the cache annotation applied. Always returns
        a list, even for string input.
    """
    cc = build_cache_control(ttl)

    # String input -> wrap into a single text block.
    if isinstance(system_blocks, str):
        block: dict = {"type": "text", "text": system_blocks}
        if cc is not None:
            block["cache_control"] = cc
        return [block]

    # List input -> deep-copy so the caller's data is untouched.
    if not isinstance(system_blocks, list):
        raise TypeError(
            f"annotate_system_blocks: expected str or list[dict], got {type(system_blocks).__name__}"
        )
    if not system_blocks:
        raise ValueError("annotate_system_blocks: system_blocks list must be non-empty")

    annotated = copy.deepcopy(system_blocks)

    # Strip any pre-existing cache_control from non-last blocks for hygiene
    # (mixed annotations confuse the cache and produce surprising bills).
    for block in annotated[:-1]:
        block.pop("cache_control", None)

    last = annotated[-1]
    if cc is None:
        last.pop("cache_control", None)
    else:
        last["cache_control"] = cc

    return annotated


# ---------------------------------------------------------------------------
# CacheMetrics
# ---------------------------------------------------------------------------

# Token-cost multipliers vs base input (matches Anthropic public pricing,
# Sonnet/Opus class). Output is excluded — it isn't affected by caching.
_BASE_MULT_UNCACHED = 1.00
_BASE_MULT_WRITE_5M = 1.25
_BASE_MULT_WRITE_1H = 2.00
_BASE_MULT_READ = 0.10


class CacheMetrics:
    """Accumulate Anthropic ``response.usage`` blocks and report cache stats.

    Designed to be fed the ``message.usage`` dict from
    ``anthropic.Anthropic().messages.create(...)``. Each call to
    :meth:`record` adds the block's token counts to running totals.

    Hit-rate formula
    ----------------
    ``hit_rate = cache_read / (cache_read + cache_create + uncached_input)``

    The denominator is the total input tokens *charged* in some form
    (uncached + cache-write + cache-read). Cache-creation tokens count as
    "not a hit" — they are the cost of populating the cache the first time.
    Cache-read tokens are the wins.

    Pure denominator caveat: we are NOT subtracting the write-overhead bonus
    (the 0.25x or 1.00x premium on top of base for the write). The ratio is
    a *token* ratio, not a cost ratio. Use :meth:`summary` for the cost
    estimate, which weighs each bucket by the appropriate multiplier.

    Edge case: if no input tokens have been recorded, ``hit_rate()`` returns
    ``0.0`` (avoids ZeroDivisionError).
    """

    __slots__ = (
        "uncached_input",
        "cache_create",  # combined 5m + 1h create totals (we don't get split)
        "cache_read",
        "output",
        "calls",
    )

    def __init__(self) -> None:
        self.uncached_input: int = 0
        self.cache_create: int = 0
        self.cache_read: int = 0
        self.output: int = 0
        self.calls: int = 0

    def record(self, usage_block: dict) -> None:
        """Add a single Anthropic usage block to the running totals.

        Recognised keys (any may be missing — Anthropic omits zeros):
        - ``input_tokens``                    -> uncached input
        - ``cache_creation_input_tokens``     -> cache-write
        - ``cache_read_input_tokens``         -> cache-read (the wins)
        - ``output_tokens``                   -> output (carried for cost calc)
        """
        if not isinstance(usage_block, dict):
            raise TypeError(
                f"CacheMetrics.record: expected dict, got {type(usage_block).__name__}"
            )
        self.uncached_input += int(usage_block.get("input_tokens", 0) or 0)
        self.cache_create += int(usage_block.get("cache_creation_input_tokens", 0) or 0)
        self.cache_read += int(usage_block.get("cache_read_input_tokens", 0) or 0)
        self.output += int(usage_block.get("output_tokens", 0) or 0)
        self.calls += 1

    def hit_rate(self) -> float:
        """Return the cache hit-rate ratio in ``[0.0, 1.0]``.

        ``hit_rate = cache_read / (cache_read + cache_create + uncached_input)``

        Returns 0.0 if no input tokens have been recorded.
        """
        denom = self.cache_read + self.cache_create + self.uncached_input
        if denom == 0:
            return 0.0
        return self.cache_read / denom

    def summary(self, ttl_used: TTL = "1h") -> dict:
        """Return a token + cost summary dict.

        ``ttl_used`` selects the write multiplier for the savings estimate
        (5m -> 1.25x, 1h -> 2.00x). For "none", the multiplier collapses to
        1.00x (creation tokens were billed at base — i.e., uncached).

        Cost is reported in "base-input-token equivalents" — multiply by your
        model's per-token base-input price to get USD. Output cost is
        included (~5x base) but unaffected by caching, so it appears in
        both ``estimated_cost_no_cache`` and ``estimated_cost_with_cache``.

        If a richer cost helper becomes available (e.g., ``cost_tracker`` from
        T0.2), this method can be extended later — currently we ship the
        token-equivalent number to keep this branch independent.
        """
        if ttl_used == "1h":
            write_mult = _BASE_MULT_WRITE_1H
        elif ttl_used == "5m":
            write_mult = _BASE_MULT_WRITE_5M
        else:
            # "none" -> creation tokens were actually uncached, but the bucket
            # should be empty anyway. Use base multiplier to be safe.
            write_mult = _BASE_MULT_UNCACHED

        # Output cost: Sonnet/Opus charge ~5x base on output. Constant across
        # cached/uncached so include it in both totals for a fair comparison.
        output_mult = 5.0

        cost_with_cache = (
            self.uncached_input * _BASE_MULT_UNCACHED
            + self.cache_create * write_mult
            + self.cache_read * _BASE_MULT_READ
            + self.output * output_mult
        )
        # No-cache equivalent: every input token would have been billed at
        # base (uncached). cache_read tokens were repeated reads of the same
        # cached prefix — without caching they would have been re-sent every
        # call as uncached input.
        cost_no_cache = (
            (self.uncached_input + self.cache_create + self.cache_read)
            * _BASE_MULT_UNCACHED
            + self.output * output_mult
        )
        savings = cost_no_cache - cost_with_cache
        savings_pct = (savings / cost_no_cache) if cost_no_cache > 0 else 0.0

        return {
            "calls": self.calls,
            "uncached_input_tokens": self.uncached_input,
            "cache_creation_tokens": self.cache_create,
            "cache_read_tokens": self.cache_read,
            "output_tokens": self.output,
            "hit_rate": self.hit_rate(),
            "ttl_used": ttl_used,
            # Costs in "base-input-token equivalents" (multiply by base
            # input $/token to get USD).
            "estimated_cost_with_cache": cost_with_cache,
            "estimated_cost_no_cache": cost_no_cache,
            "estimated_savings": savings,
            "estimated_savings_pct": savings_pct,
        }


__all__ = [
    "TTL",
    "build_cache_control",
    "annotate_system_blocks",
    "CacheMetrics",
]
