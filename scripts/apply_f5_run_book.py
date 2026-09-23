"""Add DISPLACEMENT_BUILT to F5 run_book.py known-sleeve union. Idempotent."""
from __future__ import annotations

from pathlib import Path

P = Path(r"host-local\redacted_host\repo\run_book.py")
text = P.read_text(encoding="utf-8")
changed = []

old_imp = (
    "        BUILT as _BUILT_SLEEVES, CANDIDATE_BUILT as _CAND_SLEEVES,\n"
    "        MARKET_EXPANSION_BUILT as _MX_SLEEVES, WIDEN_BUILT as _WIDEN_SLEEVES,\n"
)
new_imp = (
    "        BUILT as _BUILT_SLEEVES, CANDIDATE_BUILT as _CAND_SLEEVES,\n"
    "        MARKET_EXPANSION_BUILT as _MX_SLEEVES, WIDEN_BUILT as _WIDEN_SLEEVES,\n"
    "        DISPLACEMENT_BUILT as _DSP_SLEEVES,\n"
)
if "DISPLACEMENT_BUILT as _DSP_SLEEVES" not in text:
    if old_imp not in text:
        raise SystemExit("import needle missing")
    text = text.replace(old_imp, new_imp, 1)
    changed.append("import")

old_k = (
    "    _known_sleeves = (set(_BUILT_SLEEVES) | set(_CAND_SLEEVES) | set(_MX_SLEEVES)\n"
    "                      | set(_WIDEN_SLEEVES))\n"
)
new_k = (
    "    _known_sleeves = (set(_BUILT_SLEEVES) | set(_CAND_SLEEVES) | set(_MX_SLEEVES)\n"
    "                      | set(_WIDEN_SLEEVES) | set(_DSP_SLEEVES))\n"
)
if "| set(_DSP_SLEEVES)" not in text:
    if old_k not in text:
        raise SystemExit("known needle missing")
    text = text.replace(old_k, new_k, 1)
    changed.append("known")

old_tf = "{**_BUILT_SLEEVES, **_CAND_SLEEVES, **_MX_SLEEVES}.items()"
new_tf = "{**_BUILT_SLEEVES, **_CAND_SLEEVES, **_MX_SLEEVES, **_DSP_SLEEVES}.items()"
if new_tf not in text:
    if old_tf not in text:
        raise SystemExit("timeframe needle missing")
    text = text.replace(old_tf, new_tf, 1)
    changed.append("tf")

P.write_text(text, encoding="utf-8")
print("run_book", ",".join(changed) if changed else "already")
