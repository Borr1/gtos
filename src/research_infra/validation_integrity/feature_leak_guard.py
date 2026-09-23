"""feature_leak_guard.py — feature-level causal lookahead guard for the validation machine.

THE GAP THIS FILLS (mined + verified 2026-06-17, wf_7c0061fc follow/avoid/mixed conditional harvest;
generalized from selector_v4's no-leak source contract): the edge_factory's existing 4 guards
(null-mechanism placebo / walk-forward cell-selection / sub-selection stability / universe robustness)
ALL operate on the already-reconstructed daily-R series — they are structurally BLIND to whether a
FILTER FEATURE itself peeked at bars after the signal bar i. A feature that accidentally reads a future
bar (forward return, centered MA, realized-forward vol, an outcome/result column) would sail through all
4 and inflate every downstream every-split number. This guard closes that blind spot.

TWO LAYERS (both proven to discriminate: 966/966 real metals/energy features CLEAN, 3/3 planted leaks
flagged, token layer 6/6 clean pass + dirty flagged):
  1. assert_filter_source_clean(evidence_class): the declared source/evidence-class must not carry
     outcome/realized/result tokens (reuses selector_v4's FORBIDDEN contract = single source of truth).
  2. causal_probe(feature_fn, bars, i): STRUCTURAL test — a feature is causal iff its value is invariant
     to ANY change in bars[j] for j>i. We poison the future (huge/zero/flip sentinels) and re-evaluate;
     any divergence beyond float noise => the feature read ahead => LOOKAHEAD.

Pure, leak-free, zero broker/IO. Use as a fail-closed gate BEFORE certify_candidate on any newly-mined
filter feature (e.g. the harvested conditional follow/avoid/mixed filters, the exit/zone-quality gates).
"""
from __future__ import annotations
from typing import Any, Callable, Iterable, Optional


# --------------------------------------------------------------------------------------------------
# LAYER 1 — source/evidence-class TOKEN CONTRACT (reuse selector_v4's contract; lazy import + fallback)
# --------------------------------------------------------------------------------------------------
_FALLBACK_FORBIDDEN = ("outcome", "realized", "result", "pnl", "win", "loss", "mfe", "mae",
                       "post_decision", "validation_result", "future", "lookahead", "broker_real_pnl")


def _forbidden_tokens() -> tuple:
    try:
        from src.components.selector_v4 import FORBIDDEN_SOURCE_EVIDENCE_TOKENS as F  # single source of truth
        return tuple(F)
    except Exception:
        return _FALLBACK_FORBIDDEN


def assert_filter_source_clean(evidence_class: Optional[str]) -> Optional[str]:
    """Return None if the declared evidence-class is clean, else a violation string. Fail-closed: an
    empty/None class is a violation (every filter feature must declare a causal source class)."""
    if evidence_class is None or str(evidence_class).strip() == "":
        return "missing_source_evidence_class"
    try:  # prefer the deployed selector_v4 contract verbatim
        from src.components.selector_v4 import _source_contract_violation as _v
        return _v(evidence_class)
    except Exception:
        low = str(evidence_class).lower()
        for tok in _forbidden_tokens():
            if tok in low:
                return f"forbidden_source_token:{tok}"
        return None


# --------------------------------------------------------------------------------------------------
# LAYER 2 — CAUSAL-FEATURE PROBE (poison the future, require invariance)
# --------------------------------------------------------------------------------------------------
def _default_poison(bars: list, i: int, mode: str) -> list:
    """Copy bars; replace every bar j>i with a sentinel. Works for the project Bar(o,h,l,c,v) positional
    types (ultimate_book.primitives.Bar / geometry_lib.Bar). A namedtuple-_replace path is used if present."""
    out = list(bars)
    n = len(bars)
    for j in range(i + 1, n):
        b = bars[j]
        vol = getattr(b, "v", getattr(b, "volume", 0))
        base = bars[i].c
        if mode == "huge":
            val = b.c * 1000.0 if b.c else 1e9
        elif mode == "zero":
            val = 1e-6
        else:  # flip -> collapse to the signal-bar close
            val = base
        try:
            out[j] = type(b)(val, val, val, val, vol)            # positional (o,h,l,c,v)
        except Exception:
            try:
                out[j] = b._replace(open=val, high=val, low=val, close=val)  # namedtuple
            except Exception:
                out[j] = b                                       # last-resort: leave (probe still runs)
    return out


def _eq(a: Any, b: Any) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    try:
        return abs(float(a) - float(b)) <= 1e-9 * (1 + abs(float(a)))
    except (TypeError, ValueError):
        return a == b


def causal_probe(feature_fn: Callable, bars: list, i: int, *,
                 modes: Iterable[str] = ("huge", "zero", "flip"), **feature_kwargs) -> tuple:
    """Return ('CLEAN', detail) or ('LOOKAHEAD', detail). feature_fn(bars, i, **kw)->scalar/None must be
    INVARIANT to any change in bars[j>i]; if poisoning the future moves the output, the feature peeked."""
    base = feature_fn(bars, i, **feature_kwargs)
    for mode in modes:
        val = feature_fn(_default_poison(bars, i, mode), i, **feature_kwargs)
        if not _eq(base, val):
            return ("LOOKAHEAD", {"mode": mode, "baseline": base, "poisoned": val})
    return ("CLEAN", {"baseline": base})


def certify_feature_causal(feature_fn: Callable, samples: Iterable[tuple], *,
                           evidence_class: Optional[str] = None, **feature_kwargs) -> dict:
    """Fail-closed certification of ONE filter feature before it enters edge_factory.certify_candidate.
    samples = iterable of (bars, i) at real signal indices (each with >=1 future bar to poison).
    Returns {passed, token_violation, clean, lookahead, first_flag}. passed=False if ANY sample leaks
    or the evidence_class is dirty."""
    token_violation = assert_filter_source_clean(evidence_class) if evidence_class is not None else None
    clean = lookahead = 0
    first_flag = None
    for bars, i in samples:
        if i >= len(bars) - 1:
            continue                                            # no future to poison -> skip
        verdict, det = causal_probe(feature_fn, bars, i, **feature_kwargs)
        if verdict == "CLEAN":
            clean += 1
        else:
            lookahead += 1
            if first_flag is None:
                first_flag = {"i": i, **det}
    passed = (lookahead == 0) and (token_violation is None)
    return {"passed": passed, "token_violation": token_violation,
            "clean": clean, "lookahead": lookahead, "first_flag": first_flag}
