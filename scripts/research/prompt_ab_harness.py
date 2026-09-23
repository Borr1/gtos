"""L56 — Prompt A/B Harness with pre-registered metrics.

Phase 1 research-program task L56. Unblocks downstream prompt-experiment
tasks (V4/V5/cascade resurrection, B10 ablations).

Goals
=====
1. Reproducible side-by-side comparison of two prompts (system + user
   templates) on the same fixture set.
2. Pre-registered metrics — the metrics YAML is read BEFORE results are
   generated; no metric or threshold added after-the-fact (CLAUDE.md
   "Prohibited behaviors" #5).
3. Realized-R join — when historical trade records are provided, each
   fixture's decision is joined to the realized R from the matching
   trade record (`(symbol, candle_close_time, side)`). This is the
   ONLY metric family that survives the
   feedback_walk_level_evidence_not_predictive.md warning, so the harness
   makes it a first-class feature.
4. Mocked-API by default. Real-API gated behind ``--live`` (NOT used in
   Wave 1; CEO will run separately when the harness is promoted).

NON-GOALS
=========
- Modifying production prompts under ``prompts/``. The harness reads
  prompt files only.
- Modifying ``src/components/primary_analyzer.py`` or any orchestrator
  code. The harness implements its own minimal API call seam that
  intentionally shares the SAME signature as
  ``primary_analyzer._call_claude`` so a future T0.1 batch wrapper can
  drop in without rewrites.
- Implementing a batch wrapper. The seam is the only requirement here.

Inputs
======
``--prompt-a/--prompt-b PATH``:
    Either:
      * a ``.md``/``.txt`` file (treated as the SYSTEM prompt; the user
        template is taken from the fixture's ``user_message`` field), or
      * a ``.yaml`` file with keys ``system`` (str) and optional
        ``user_template`` (str) — when ``user_template`` is present, the
        harness substitutes ``{{fixture_user}}`` with the fixture's
        ``user_message`` so the prompt file can wrap the user message
        in additional scaffolding.

``--fixtures NAME|PATH``:
    ``historical_cands`` loads fixtures derived from
    ``knowledge_base/trade_records/`` where
    ``decision_pipeline.ai_decision == "CANDIDATE"`` (best for realized-R
    join). Or provide a path to a custom JSONL fixture set, one JSON object
    per line.

``--metrics PATH``:
    Pre-registered metrics YAML (see
    ``scripts/research/metrics/prompt_ab_default.yaml`` for schema).

``--realized-r-join PATH``:
    Optional. Either:
      * a directory containing ``knowledge_base/trade_records``-style
        per-trade JSON files, or
      * a path to an ``all_results.json`` style file (T7 simulation)
        which has ``r_multiple`` + ``outcome`` keys.
    The harness joins decisions to realized R by
    ``(symbol, candle_close_time, side)``. Fixtures with no match are
    excluded from realized-R metrics with a logged warning.

``--output PATH``:
    Output directory. Harness writes:
      * ``results.jsonl``       — one row per fixture (decision A, B, R_a, R_b)
      * ``metrics_report.json`` — per-metric statistics
      * ``decision_diff.md``    — human-readable side-by-side
      * ``run_metadata.json``   — CLI args, seed, fixture count, prompt SHAs

Determinism
===========
``--seed`` makes the mocked decision-engine deterministic. Real-API
non-determinism is unavoidable for ``effort=max`` (Anthropic does not
provide a seed parameter for extended thinking budgets); this is logged
in the README addition.

CLI examples
============
    # Self-test (identical prompts, mocked, no real API)
    python scripts/research/prompt_ab_harness.py \\
        --prompt-a prompts/short_validation_batch_prompt.md \\
        --prompt-b prompts/short_validation_batch_prompt.md \\
        --fixtures historical_cands \\
        --metrics scripts/research/metrics/prompt_ab_default.yaml \\
        --output research/prompt_ab_smoke \\
        --seed 1 --dry-run

    # Real prompt vs candidate prompt (mocked still — Wave 1)
    python scripts/research/prompt_ab_harness.py \\
        --prompt-a prompts/v3_baseline.md \\
        --prompt-b prompts/v4_candidate.md \\
        --fixtures historical_cands \\
        --metrics scripts/research/metrics/prompt_ab_default.yaml \\
        --realized-r-join knowledge_base/trade_records \\
        --output research/v3_v4_paired_run \\
        --seed 1
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import logging
import math
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

try:
    from scipy import stats as _scipy_stats  # type: ignore
except ImportError:  # pragma: no cover — exercised only on minimal envs
    _scipy_stats = None  # type: ignore


# ---------------------------------------------------------------------------
# Project root resolution
# ---------------------------------------------------------------------------

# scripts/research/prompt_ab_harness.py → project root is parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRADE_RECORDS_DIR = PROJECT_ROOT / "knowledge_base" / "trade_records"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger("prompt_ab_harness")


def _setup_logging(verbose: bool = False) -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s",
                          datefmt="%H:%M:%S")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class PromptBundle:
    """A loaded prompt — system text + optional user template wrapper."""

    path: str
    system: str
    user_template: str | None = None  # if set, substitutes {{fixture_user}}

    @property
    def sha256(self) -> str:
        h = hashlib.sha256()
        h.update(self.system.encode("utf-8"))
        if self.user_template is not None:
            h.update(b"\n--USER--\n")
            h.update(self.user_template.encode("utf-8"))
        return h.hexdigest()

    def render_user(self, fixture_user: str) -> str:
        if self.user_template is None:
            return fixture_user
        return self.user_template.replace("{{fixture_user}}", fixture_user)


@dataclasses.dataclass
class Fixture:
    """A single A/B input row."""

    label: str
    symbol: str
    candle_time: str  # ISO-8601 UTC
    user_message: str
    expected_decision: str | None = None
    side_hint: str | None = None  # parsed from raw_response when available
    raw: Mapping[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class Decision:
    """The result of evaluating one fixture under one prompt."""

    decision: str  # "CANDIDATE" | "NO_TRADE" | "MALFORMED"
    side: str | None  # "LONG" | "SHORT" | None
    raw_response: str
    error: str | None = None


@dataclasses.dataclass
class PairedResult:
    """A single fixture's paired A/B outcome."""

    fixture_label: str
    symbol: str
    candle_time: str
    decision_a: Decision
    decision_b: Decision
    realized_r_a: float | None = None
    realized_r_b: float | None = None


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------


def load_prompt(path: str | Path) -> PromptBundle:
    """Load a prompt file. Accepts ``.md``/``.txt`` (system-only) or
    ``.yaml``/``.yml`` (system + optional user_template)."""

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Prompt file not found: {p}")

    suffix = p.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        with p.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Prompt YAML must be a mapping at top level: {p}")
        if "system" not in data or not isinstance(data["system"], str):
            raise ValueError(f"Prompt YAML missing required `system: <str>`: {p}")
        return PromptBundle(
            path=str(p),
            system=data["system"],
            user_template=data.get("user_template"),
        )
    # .md / .txt / anything else -> treat as raw system prompt
    return PromptBundle(path=str(p), system=p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------


_NAMED_SETS = {"historical_cands"}


def _resolve_named_set(name: str) -> list[Fixture]:
    """Resolve a named fixture set to a list of Fixture objects."""
    if name == "historical_cands":
        return _load_historical_cand_fixtures()
    raise ValueError(f"Unknown named set: {name}")


def _load_historical_cand_fixtures() -> list[Fixture]:
    """Build fixtures from the trade_records corpus.

    Only records with ``decision_pipeline.ai_decision == "CANDIDATE"`` are
    included, since NO_TRADE records lack a meaningful realized R.
    """
    if not TRADE_RECORDS_DIR.exists():
        logger.warning("No trade records dir at %s — historical_cands empty",
                       TRADE_RECORDS_DIR)
        return []

    fixtures: list[Fixture] = []
    for instrument_dir in sorted(TRADE_RECORDS_DIR.iterdir()):
        if not instrument_dir.is_dir():
            continue
        for json_path in sorted(instrument_dir.glob("*.json")):
            try:
                with json_path.open("r", encoding="utf-8") as fh:
                    rec = json.load(fh)
            except Exception as exc:
                logger.warning("Skipping unreadable trade record %s: %s",
                               json_path, exc)
                continue
            decision = (rec.get("decision_pipeline", {})
                          .get("ai_decision"))
            if decision != "CANDIDATE":
                continue
            meta = rec.get("metadata", {})
            label = meta.get("trade_id", json_path.stem)
            symbol = (meta.get("symbol") or instrument_dir.name).upper()
            candle_time = meta.get("candle_time") or ""
            # Trade records DO NOT store the synthesised system+user prompt
            # used at decision time. The harness uses a placeholder user
            # message constructed from the captured MSO so prompts can be
            # tested against a real-shape input. Note: this is informational
            # only when running the harness in mocked mode; real-API runs
            # would need the actual MSO snapshot rebuilt — out of scope for
            # L56 (Phase 2 work).
            mso = rec.get("mso", {})
            mso_summary = json.dumps(mso, default=str)[:8000]
            user_message = textwrap.dedent(f"""
                ## Historical CAND fixture (rebuilt from trade record)
                Symbol: {symbol}
                Candle: {candle_time}
                Note: full MSO context truncated to 8KB — for mocked runs only.
                MSO snapshot:
                {mso_summary}
            """).strip()
            fixtures.append(Fixture(
                label=label,
                symbol=symbol,
                candle_time=candle_time,
                user_message=user_message,
                expected_decision=decision,
                side_hint=(rec.get("decision_pipeline", {})
                              .get("ai_direction")),
                raw=rec,
            ))
    logger.info("Loaded %d historical CAND fixtures", len(fixtures))
    return fixtures


def _load_custom_jsonl(path: str | Path) -> list[Fixture]:
    """Load a custom JSONL fixture set."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Custom fixture path not found: {p}")
    fixtures: list[Fixture] = []
    with p.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Malformed JSON at {p}:{line_no}: {exc}")
            label = obj.get("label") or f"{p.stem}_row{line_no}"
            user_message = obj.get("user_message") or obj.get("user", "")
            if not user_message:
                logger.warning("Skipping fixture %s: no user_message", label)
                continue
            candle_time = obj.get("candle_time", "")
            symbol = (obj.get("symbol") or _infer_symbol_from_label(label)).upper()
            fixtures.append(Fixture(
                label=label,
                symbol=symbol,
                candle_time=candle_time,
                user_message=user_message,
                expected_decision=obj.get("expected_decision"),
                side_hint=obj.get("side_hint"),
                raw=obj,
            ))
    return fixtures


def load_fixtures(spec: str) -> list[Fixture]:
    """Resolve ``--fixtures`` argument to a fixture list.

    Heuristic for distinguishing "named set typo" from "missing custom file":
      * if ``spec`` contains no path separators and no extension AND it
        does not exist as a file/dir on disk, it is most likely a named
        set typo → raise ``ValueError`` with the legal options listed.
      * otherwise treat as a custom JSONL path.
    """
    if spec in _NAMED_SETS:
        return _resolve_named_set(spec)
    p = Path(spec)
    looks_like_path = (
        os.sep in spec or "/" in spec or p.suffix or p.exists()
    )
    if not looks_like_path:
        raise ValueError(
            f"Unknown fixture set {spec!r}. "
            f"Expected one of {sorted(_NAMED_SETS)} or a path to a JSONL file."
        )
    return _load_custom_jsonl(spec)


# ---------------------------------------------------------------------------
# Decision engines (mocked + real-API seam)
# ---------------------------------------------------------------------------


def _mock_decision(prompt: PromptBundle, fixture: Fixture, *,
                   seed: int) -> Decision:
    """Deterministic mock decision engine.

    Hashes ``(seed, prompt.sha256, fixture.label)`` to derive a stable
    pseudo-random outcome. Two prompts with IDENTICAL system text MUST
    produce IDENTICAL outputs on each fixture (sanity check #1 in tests).
    Two prompts with DIFFERENT text produce different outputs at the
    expected divergence rate (sanity check #2).

    The seed is mixed in deterministically (NOT via rng draw order) so
    that:
      * identical prompts → identical decisions on every fixture for any
        given seed,
      * --seed allows variance estimation across multiple harness runs,
      * the same (seed, prompt, fixture) triple always produces the
        same decision, regardless of evaluation order or batch size.
    """
    seed_material = f"{seed}|{prompt.sha256}|{fixture.label}"
    h = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
    # Use first 8 hex chars as a 32-bit integer
    bucket = int(h[:8], 16)

    # 60% CANDIDATE, 40% NO_TRADE — roughly matches batch CR for
    # CANDIDATE-rich fixture sets.
    decision = "CANDIDATE" if (bucket % 100) < 60 else "NO_TRADE"

    side: str | None = None
    if decision == "CANDIDATE":
        # Pick LONG/SHORT deterministically off a different hash slice.
        side_bit = int(h[8:16], 16) % 2
        side = "LONG" if side_bit == 0 else "SHORT"

    raw = json.dumps({
        "decision": decision,
        "trade_parameters": {"direction": side} if side else None,
        "_mock_engine": True,
        "_prompt_sha": prompt.sha256[:12],
        "_fixture": fixture.label,
    })
    return Decision(decision=decision, side=side, raw_response=raw)


def _real_api_decision(prompt: PromptBundle, fixture: Fixture, *,
                       client) -> Decision:  # pragma: no cover — gated --live
    """Real Anthropic API call. Mirrors primary_analyzer._call_claude
    signature so future T0.1 batch wrapper drops in cleanly.

    NOT wired in Wave 1; CEO will run separately when promoting the
    harness to live use. Tests only exercise the mocked engine.
    """
    if client is None:
        raise RuntimeError(
            "Real-API mode requires a configured Anthropic client. "
            "Pass --live AND ensure ANTHROPIC_API_KEY is set."
        )
    user_message = prompt.render_user(fixture.user_message)
    system_blocks = [
        {
            "type": "text",
            "text": prompt.system,
            "cache_control": {"type": "ephemeral"},
        },
    ]
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        temperature=0,
        system=system_blocks,
        messages=[{"role": "user", "content": user_message}],
    )
    text = response.content[0].text
    return _parse_response(text)


_DECISION_RE = re.compile(r'"decision"\s*:\s*"(CANDIDATE|NO_TRADE)"')
_DIRECTION_RE = re.compile(r'"direction"\s*:\s*"(LONG|SHORT)"')


def _parse_response(text: str) -> Decision:
    """Extract decision + side from a JSON-ish response. Tolerates fenced
    blocks (```json ... ```) and minor formatting drift."""
    m = _DECISION_RE.search(text)
    if m is None:
        return Decision(decision="MALFORMED", side=None, raw_response=text,
                        error="no_decision_field")
    decision = m.group(1)
    side: str | None = None
    if decision == "CANDIDATE":
        sm = _DIRECTION_RE.search(text)
        side = sm.group(1) if sm else None
    return Decision(decision=decision, side=side, raw_response=text)


# ---------------------------------------------------------------------------
# Realized-R join
# ---------------------------------------------------------------------------


def _normalize_candle_time(ts: str) -> str:
    """Normalize ISO-8601 timestamps to a canonical key for joining.

    Trade records use ``2026-04-15T13:15:52.698253+00:00`` (microseconds).
    We normalize to UTC-rounded-down-to-minute since fixtures key off candle
    close.
    """
    if not ts:
        return ""
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(s)
    except ValueError:
        return ts  # fall back to raw — caller will likely miss the join
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    parsed = parsed.astimezone(dt.timezone.utc)
    # Round to whole minute — candle close timestamps are minute-aligned
    parsed = parsed.replace(second=0, microsecond=0)
    return parsed.isoformat()


def _join_key(symbol: str, candle_time: str, side: str | None) -> str:
    return f"{symbol.upper()}|{_normalize_candle_time(candle_time)}|{side or '*'}"


def load_realized_r_index(path: str | Path) -> dict[str, float]:
    """Build a join index from a path that is either:
      * a directory of trade-record JSONs (``knowledge_base/trade_records``),
      * a single ``all_results.json`` style file.

    Returns ``{join_key: r_multiple}``. Missing R is silently dropped.
    Side is included in the key when available so LONG vs SHORT decisions
    on the same candle don't collide. The index also stores a side-less
    fallback key (``side='*'``) so direction-mismatched lookups still
    succeed when the trade record only has one side recorded.
    """
    p = Path(path)
    index: dict[str, float] = {}

    def _record(symbol: str, candle_time: str, side: str | None,
                r_multiple: float) -> None:
        if r_multiple is None or not isinstance(r_multiple, (int, float)):
            return
        if not symbol or not candle_time:
            return
        key = _join_key(symbol, candle_time, side)
        index[key] = float(r_multiple)
        # Also store side-less fallback (* matches any side)
        index[_join_key(symbol, candle_time, None)] = float(r_multiple)

    if p.is_dir():
        for instrument_dir in sorted(p.iterdir()):
            if not instrument_dir.is_dir():
                continue
            for json_path in instrument_dir.glob("*.json"):
                try:
                    with json_path.open("r", encoding="utf-8") as fh:
                        rec = json.load(fh)
                except Exception:
                    continue
                meta = rec.get("metadata", {})
                symbol = (meta.get("symbol") or instrument_dir.name).upper()
                candle_time = meta.get("candle_time") or ""
                pipeline = rec.get("decision_pipeline", {})
                side = pipeline.get("ai_direction")
                # Trade records may not have realized_r — pull from outcome
                # field if present (shape: ``{"outcome": "WIN"|"LOSS",
                # "r_multiple": 1.5}``).
                outcome = pipeline.get("outcome", {}) or {}
                r_multiple = outcome.get("r_multiple")
                if r_multiple is None:
                    # also try top-level fields (T7 sim has these flat)
                    r_multiple = rec.get("r_multiple")
                if r_multiple is not None:
                    _record(symbol, candle_time, side, r_multiple)
    elif p.is_file():
        with p.open("r", encoding="utf-8") as fh:
            obj = json.load(fh)
        records: Iterable[Mapping[str, Any]]
        if isinstance(obj, dict) and "results" in obj:
            records = obj["results"]
        elif isinstance(obj, list):
            records = obj
        else:
            records = []
        for rec in records:
            symbol = (rec.get("symbol") or "").upper()
            candle_time = rec.get("candle_time") or ""
            side = rec.get("direction")
            r_multiple = rec.get("r_multiple")
            if r_multiple is None:
                continue
            _record(symbol, candle_time, side, r_multiple)
    else:
        raise FileNotFoundError(f"Realized-R join path not found: {p}")

    logger.info("Realized-R index built: %d keys from %s", len(index), p)
    return index


def lookup_realized_r(index: Mapping[str, float], symbol: str,
                      candle_time: str, side: str | None) -> float | None:
    """Look up realized R; tries side-specific then side-less fallback."""
    if not index:
        return None
    direct = index.get(_join_key(symbol, candle_time, side))
    if direct is not None:
        return direct
    return index.get(_join_key(symbol, candle_time, None))


# ---------------------------------------------------------------------------
# Statistics — pre-registered tests
# ---------------------------------------------------------------------------


def _wilson_interval(successes: int, n: int,
                     z: float = 1.96) -> tuple[float, float, float]:
    """Wilson 95% CI. Returns (point, low, high). For n=0, returns
    (0.0, 0.0, 0.0)."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = successes / n
    denom = 1 + (z * z) / n
    centre = (p + (z * z) / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + (z * z) / (4 * n * n))) / denom
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def _sign_test(plus: int, minus: int) -> float:
    """Two-sided sign test p-value via binomial CDF. ``plus`` and
    ``minus`` are the counts of (+) vs (-) directions (ties dropped)."""
    n = plus + minus
    if n == 0:
        return 1.0
    k = min(plus, minus)
    # P(K <= k | n, 0.5) via direct binomial CDF
    p_one_tail = 0.0
    for i in range(0, k + 1):
        p_one_tail += math.comb(n, i) * (0.5 ** n)
    return min(1.0, 2.0 * p_one_tail)


def _mcnemar(b: int, c: int) -> float:
    """Continuity-corrected McNemar p-value.

    ``b`` = count where A=CAND & B=NO_TRADE
    ``c`` = count where A=NO_TRADE & B=CAND

    Uses chi-square 1 df with the standard ``(|b-c|-1)^2 / (b+c)``
    continuity correction. For small samples (b+c < 25) we fall back to
    the exact binomial test (k=min(b,c), n=b+c, p=0.5).
    """
    n = b + c
    if n == 0:
        return 1.0
    if n < 25:
        # Exact binomial
        k = min(b, c)
        p_one = 0.0
        for i in range(0, k + 1):
            p_one += math.comb(n, i) * (0.5 ** n)
        return min(1.0, 2.0 * p_one)
    chi_sq = ((abs(b - c) - 1) ** 2) / n
    if _scipy_stats is not None:
        return float(_scipy_stats.chi2.sf(chi_sq, df=1))
    # Crude approximation if scipy unavailable: 1 - erf(sqrt(chi/2))
    return max(0.0, math.erfc(math.sqrt(chi_sq / 2.0)))


def _paired_t(deltas: Sequence[float]) -> tuple[float, float]:
    """Paired t-test on a single delta sequence (already paired). Returns
    ``(t_statistic, p_two_sided)``. For n<2, returns (0.0, 1.0)."""
    n = len(deltas)
    if n < 2:
        return (0.0, 1.0)
    mean = sum(deltas) / n
    var = sum((d - mean) ** 2 for d in deltas) / (n - 1)
    if var == 0:
        return (math.inf if mean != 0 else 0.0, 0.0 if mean != 0 else 1.0)
    se = math.sqrt(var / n)
    t = mean / se if se > 0 else 0.0
    if _scipy_stats is not None:
        p = float(2 * (1 - _scipy_stats.t.cdf(abs(t), df=n - 1)))
    else:
        # crude normal approx for fall-back environments only
        p = math.erfc(abs(t) / math.sqrt(2))
    return (t, max(0.0, min(1.0, p)))


def _wilcoxon(deltas: Sequence[float]) -> float:
    """Wilcoxon signed-rank test. Returns p-value (two-sided)."""
    deltas = [d for d in deltas if d != 0]
    if len(deltas) < 2:
        return 1.0
    if _scipy_stats is not None:
        try:
            res = _scipy_stats.wilcoxon(deltas)
            return float(res.pvalue)
        except Exception:
            return 1.0
    return 1.0  # fall-back


def _fisher_exact(table: tuple[tuple[int, int], tuple[int, int]]) -> float:
    """Fisher exact two-sided p-value on a 2x2."""
    if _scipy_stats is not None:
        try:
            _, p = _scipy_stats.fisher_exact(table)
            return float(p)
        except Exception:
            return 1.0
    return 1.0


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------


def _bonferroni_correct(metrics_specs: Sequence[Mapping[str, Any]]) -> int:
    """Count of metrics with bonferroni_corrected: true. Used as alpha
    divisor. Returns at least 1 to avoid div-by-zero."""
    n = sum(1 for m in metrics_specs
            if bool(m.get("bonferroni_corrected", False)))
    return max(1, n)


def compute_metrics(paired: Sequence[PairedResult],
                    metrics_specs: Sequence[Mapping[str, Any]],
                    *, has_realized_r: bool) -> dict[str, Any]:
    """Apply every pre-registered metric to the paired result set.

    Returns a dict shaped:
      {
        "metrics": [
          {"name": ..., "value": ..., "n": ..., "p_value": ...,
           "test": ..., "underpowered": bool, "significant_raw": bool,
           "significant_corrected": bool, ...},
          ...
        ],
        "bonferroni_denominator": int,
        "n_fixtures": int,
        "n_with_realized_r": int,
      }
    """
    n_fixtures = len(paired)
    bonf_denom = _bonferroni_correct(metrics_specs)

    # Pre-compute commonly-used aggregates
    a_cand = [r for r in paired if r.decision_a.decision == "CANDIDATE"]
    b_cand = [r for r in paired if r.decision_b.decision == "CANDIDATE"]
    both_cand = [r for r in paired
                 if r.decision_a.decision == "CANDIDATE"
                 and r.decision_b.decision == "CANDIDATE"]

    # 2x2 paired confusion: (a_cand_yes/no) x (b_cand_yes/no)
    a_yes_b_yes = sum(1 for r in paired
                      if r.decision_a.decision == "CANDIDATE"
                      and r.decision_b.decision == "CANDIDATE")
    a_yes_b_no = sum(1 for r in paired
                     if r.decision_a.decision == "CANDIDATE"
                     and r.decision_b.decision == "NO_TRADE")
    a_no_b_yes = sum(1 for r in paired
                     if r.decision_a.decision == "NO_TRADE"
                     and r.decision_b.decision == "CANDIDATE")
    a_no_b_no = sum(1 for r in paired
                    if r.decision_a.decision == "NO_TRADE"
                    and r.decision_b.decision == "NO_TRADE")

    # Realized R deltas — only fixtures where BOTH have realized R
    paired_with_r = [r for r in paired
                     if r.realized_r_a is not None
                     and r.realized_r_b is not None]
    deltas = [r.realized_r_a - r.realized_r_b for r in paired_with_r]
    n_with_realized_r = len(paired_with_r)

    out_metrics: list[dict[str, Any]] = []

    for spec in metrics_specs:
        name = spec["name"]
        test = spec["test"]
        min_sample = int(spec.get("min_sample", 1))
        alpha = float(spec.get("significance_threshold", 0.05))
        bonf = bool(spec.get("bonferroni_corrected", False))
        requires_r = bool(spec.get("requires_realized_r", False))

        if requires_r and not has_realized_r:
            out_metrics.append({
                "name": name, "test": test, "skipped": True,
                "skip_reason": "realized_r_join_not_provided",
                "underpowered": False, "n": 0,
                "p_value": None,
                "alpha_raw": alpha,
                "alpha_bonferroni": (alpha / bonf_denom) if bonf else None,
                "significant_raw": False,
                "significant_corrected": False if bonf else None,
                "bonferroni_corrected": bonf,
                "requires_realized_r": requires_r,
            })
            continue

        record: dict[str, Any] = {
            "name": name, "test": test, "skipped": False,
            "definition": spec.get("definition", ""),
            "bonferroni_corrected": bonf,
            "requires_realized_r": requires_r,
        }

        if test == "sign":
            n_used = a_yes_b_no + a_no_b_yes
            p = _sign_test(a_yes_b_no, a_no_b_yes)
            record.update({
                "value": {"a_cand_b_no": a_yes_b_no,
                          "a_no_b_cand": a_no_b_yes},
                "n": n_used, "p_value": p,
                "underpowered": n_used < min_sample,
            })
        elif test == "mcnemar":
            n_used = a_yes_b_no + a_no_b_yes
            p = _mcnemar(a_yes_b_no, a_no_b_yes)
            record.update({
                "value": {
                    "a_cand_b_cand": a_yes_b_yes,
                    "a_cand_b_no": a_yes_b_no,
                    "a_no_b_cand": a_no_b_yes,
                    "a_no_b_no": a_no_b_no,
                },
                "n": n_fixtures, "n_discordant": n_used,
                "p_value": p,
                "underpowered": n_fixtures < min_sample,
            })
        elif test == "paired_t":
            t_stat, p = _paired_t(deltas)
            mean = (sum(deltas) / len(deltas)) if deltas else 0.0
            record.update({
                "value": {"mean_delta_r_a_minus_b": mean,
                          "t_statistic": t_stat},
                "n": len(deltas), "p_value": p,
                "underpowered": len(deltas) < min_sample,
            })
        elif test == "wilcoxon":
            p = _wilcoxon(deltas)
            record.update({
                "value": {"n_nonzero_deltas": sum(1 for d in deltas if d != 0)},
                "n": len(deltas), "p_value": p,
                "underpowered": len(deltas) < min_sample,
            })
        elif test == "wilson_compare":
            # Descriptive: rate or winrate for one prompt
            if name in ("cr_rate_a", "cr_rate_b"):
                successes = len(a_cand) if name == "cr_rate_a" else len(b_cand)
                n_used = n_fixtures
            elif name == "realized_r_winrate_a":
                wins = sum(1 for r in paired
                           if r.decision_a.decision == "CANDIDATE"
                           and r.realized_r_a is not None
                           and r.realized_r_a > 0)
                n_used = sum(1 for r in paired
                             if r.decision_a.decision == "CANDIDATE"
                             and r.realized_r_a is not None)
                successes = wins
            elif name == "realized_r_winrate_b":
                wins = sum(1 for r in paired
                           if r.decision_b.decision == "CANDIDATE"
                           and r.realized_r_b is not None
                           and r.realized_r_b > 0)
                n_used = sum(1 for r in paired
                             if r.decision_b.decision == "CANDIDATE"
                             and r.realized_r_b is not None)
                successes = wins
            else:
                successes, n_used = 0, 0
            p_hat, lo, hi = _wilson_interval(successes, n_used)
            record.update({
                "value": {"point": p_hat, "wilson_low": lo,
                          "wilson_high": hi, "successes": successes,
                          "n": n_used},
                "n": n_used,
                "underpowered": n_used < min_sample,
                "p_value": None, "inferential": False,
            })
        elif test == "fisher_exact":
            # 2x2: (a_long, a_short) x (b_long, b_short) on the
            # both-CAND subset
            a_long_b_long = sum(1 for r in both_cand
                                if r.decision_a.side == "LONG"
                                and r.decision_b.side == "LONG")
            a_long_b_short = sum(1 for r in both_cand
                                 if r.decision_a.side == "LONG"
                                 and r.decision_b.side == "SHORT")
            a_short_b_long = sum(1 for r in both_cand
                                 if r.decision_a.side == "SHORT"
                                 and r.decision_b.side == "LONG")
            a_short_b_short = sum(1 for r in both_cand
                                  if r.decision_a.side == "SHORT"
                                  and r.decision_b.side == "SHORT")
            table = ((a_long_b_long, a_long_b_short),
                     (a_short_b_long, a_short_b_short))
            p = _fisher_exact(table)
            agree = a_long_b_long + a_short_b_short
            n_used = len(both_cand)
            record.update({
                "value": {
                    "table": table,
                    "agreement_count": agree,
                    "agreement_rate": (agree / n_used) if n_used else 0.0,
                },
                "n": n_used, "p_value": p,
                "underpowered": n_used < min_sample,
            })
        else:
            record.update({"value": None, "n": 0,
                           "underpowered": True,
                           "p_value": None,
                           "error": f"unknown test {test}"})

        # Significance flags
        p_val = record.get("p_value")
        record["significant_raw"] = (
            isinstance(p_val, (int, float)) and p_val < alpha
        )
        record["alpha_raw"] = alpha
        if bonf:
            corrected_alpha = alpha / bonf_denom
            record["alpha_bonferroni"] = corrected_alpha
            record["significant_corrected"] = (
                isinstance(p_val, (int, float)) and p_val < corrected_alpha
            )
        else:
            record["alpha_bonferroni"] = None
            record["significant_corrected"] = None

        # If underpowered, suppress significance flags entirely
        if record.get("underpowered"):
            record["significant_raw"] = False
            record["significant_corrected"] = False

        out_metrics.append(record)

    return {
        "metrics": out_metrics,
        "bonferroni_denominator": bonf_denom,
        "n_fixtures": n_fixtures,
        "n_with_realized_r": n_with_realized_r,
    }


# ---------------------------------------------------------------------------
# Run loop
# ---------------------------------------------------------------------------


def evaluate_pair(prompt_a: PromptBundle, prompt_b: PromptBundle,
                  fixtures: Sequence[Fixture], *, seed: int,
                  live: bool, client=None,
                  realized_r_index: Mapping[str, float] | None = None,
                  ) -> list[PairedResult]:
    """Evaluate prompt-A and prompt-B in PAIRED order on each fixture.

    Mocked-mode determinism contract: with ``seed`` fixed, the result is
    a pure function of ``(prompt.sha256, fixture.label)``. Identical
    prompts → identical decisions on every fixture; different prompts →
    diverge at the expected ~50% rate driven by the SHA distance.
    """
    out: list[PairedResult] = []
    for fixture in fixtures:
        if live:
            dec_a = _real_api_decision(prompt_a, fixture, client=client)
            dec_b = _real_api_decision(prompt_b, fixture, client=client)
        else:
            dec_a = _mock_decision(prompt_a, fixture, seed=seed)
            dec_b = _mock_decision(prompt_b, fixture, seed=seed)
        r_a = r_b = None
        if realized_r_index:
            r_a = lookup_realized_r(realized_r_index, fixture.symbol,
                                    fixture.candle_time, dec_a.side)
            r_b = lookup_realized_r(realized_r_index, fixture.symbol,
                                    fixture.candle_time, dec_b.side)
            if dec_a.decision == "CANDIDATE" and r_a is None:
                logger.warning(
                    "No realized R for %s | %s | side=%s — excluded from R metrics",
                    fixture.symbol, fixture.candle_time, dec_a.side)
        out.append(PairedResult(
            fixture_label=fixture.label,
            symbol=fixture.symbol,
            candle_time=fixture.candle_time,
            decision_a=dec_a,
            decision_b=dec_b,
            realized_r_a=r_a,
            realized_r_b=r_b,
        ))
    return out


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _write_results_jsonl(out_path: Path,
                         paired: Sequence[PairedResult]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for r in paired:
            row = {
                "fixture_label": r.fixture_label,
                "symbol": r.symbol,
                "candle_time": r.candle_time,
                "decision_a": r.decision_a.decision,
                "side_a": r.decision_a.side,
                "decision_b": r.decision_b.decision,
                "side_b": r.decision_b.side,
                "realized_r_a": r.realized_r_a,
                "realized_r_b": r.realized_r_b,
            }
            fh.write(json.dumps(row) + "\n")


def _write_metrics_report(out_path: Path,
                          report: Mapping[str, Any]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)


def _write_decision_diff(out_path: Path,
                         paired: Sequence[PairedResult],
                         prompt_a: PromptBundle,
                         prompt_b: PromptBundle) -> None:
    """Side-by-side markdown for diverging fixtures."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    diverging = [
        r for r in paired
        if (r.decision_a.decision != r.decision_b.decision
            or (r.decision_a.decision == "CANDIDATE"
                and r.decision_b.decision == "CANDIDATE"
                and r.decision_a.side != r.decision_b.side))
    ]
    lines: list[str] = []
    lines.append("# Prompt A/B Decision Diff\n")
    lines.append(f"- Prompt A: `{prompt_a.path}` (sha256 `{prompt_a.sha256[:12]}`)")
    lines.append(f"- Prompt B: `{prompt_b.path}` (sha256 `{prompt_b.sha256[:12]}`)")
    lines.append(f"- Fixtures: {len(paired)}  Diverging: {len(diverging)}")
    lines.append("")
    if not diverging:
        lines.append("_No diverging decisions._")
    else:
        lines.append("| Fixture | Symbol | Candle | A decision | A side | B decision | B side | R_a | R_b |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for r in diverging:
            lines.append(
                f"| {r.fixture_label} | {r.symbol} | {r.candle_time} | "
                f"{r.decision_a.decision} | {r.decision_a.side or '-'} | "
                f"{r.decision_b.decision} | {r.decision_b.side or '-'} | "
                f"{r.realized_r_a if r.realized_r_a is not None else '-'} | "
                f"{r.realized_r_b if r.realized_r_b is not None else '-'} |"
            )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _write_run_metadata(out_path: Path, args: argparse.Namespace,
                        prompt_a: PromptBundle, prompt_b: PromptBundle,
                        n_fixtures: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "harness_version": "L56-v1",
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "cli_args": {k: str(v) if isinstance(v, Path) else v
                     for k, v in vars(args).items()},
        "prompt_a": {"path": prompt_a.path, "sha256": prompt_a.sha256},
        "prompt_b": {"path": prompt_b.path, "sha256": prompt_b.sha256},
        "n_fixtures": n_fixtures,
        "live": bool(args.live),
        "seed": int(args.seed),
    }
    out_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prompt_ab_harness",
        description=("L56 prompt A/B harness with pre-registered metrics. "
                     "Mocked-by-default; real-API gated behind --live."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Pre-registration contract:
              The metrics YAML must be authored, frozen, and committed BEFORE
              running the harness on any prompt-A/prompt-B pair you intend to
              use as evidence. Editing the YAML after seeing results is
              POST-HOC HYPOTHESIS FORMATION (CLAUDE.md prohibited #5).
        """).strip(),
    )
    parser.add_argument("--prompt-a", required=True,
                        help="Path to prompt A (.md/.txt or .yaml)")
    parser.add_argument("--prompt-b", required=True,
                        help="Path to prompt B (.md/.txt or .yaml)")
    parser.add_argument("--fixtures", required=True,
                        help=("Named set (historical_cands) or path to a JSONL "
                              "fixture file."))
    parser.add_argument("--metrics", required=True,
                        help="Path to pre-registered metrics YAML.")
    parser.add_argument("--output", required=True,
                        help="Output directory.")
    parser.add_argument("--seed", type=int, default=1,
                        help="Mocked-mode seed (default 1).")
    parser.add_argument("--realized-r-join", default=None,
                        help=("Path to trade-records dir or all_results.json "
                              "for realized-R join."))
    parser.add_argument("--live", action="store_true",
                        help=("Use real Anthropic API. Phase 1 default is "
                              "MOCKED (--live is OFF)."))
    parser.add_argument("--dry-run", action="store_true",
                        help="Print plan and exit without invoking decisions.")
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser


def _run_dry(args: argparse.Namespace, prompt_a: PromptBundle,
             prompt_b: PromptBundle, fixtures: Sequence[Fixture],
             metrics_specs: Sequence[Mapping[str, Any]]) -> int:
    print("=== prompt_ab_harness DRY-RUN PLAN ===")
    print(f"prompt_a: {prompt_a.path}  sha256={prompt_a.sha256[:12]}")
    print(f"prompt_b: {prompt_b.path}  sha256={prompt_b.sha256[:12]}")
    print(f"fixtures: {len(fixtures)} from {args.fixtures!r}")
    print(f"metrics:  {len(metrics_specs)} from {args.metrics!r}")
    for spec in metrics_specs:
        print(f"  - {spec['name']:32s}  test={spec['test']:14s}  "
              f"min_n={spec.get('min_sample', 1):3d}  "
              f"bonf={spec.get('bonferroni_corrected', False)}")
    print(f"realized_r_join: {args.realized_r_join}")
    print(f"output: {args.output}")
    print(f"live: {args.live}  seed: {args.seed}")
    print("(skipping API + write — dry-run)")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    prompt_a = load_prompt(args.prompt_a)
    prompt_b = load_prompt(args.prompt_b)

    with open(args.metrics, "r", encoding="utf-8") as fh:
        metrics_yaml = yaml.safe_load(fh)
    if not isinstance(metrics_yaml, Mapping) or "metrics" not in metrics_yaml:
        logger.error("Metrics YAML missing required `metrics:` key")
        return 2
    metrics_specs = list(metrics_yaml["metrics"])

    fixtures = load_fixtures(args.fixtures)
    if not fixtures:
        logger.error("No fixtures resolved from spec %r", args.fixtures)
        return 2

    if args.dry_run:
        return _run_dry(args, prompt_a, prompt_b, fixtures, metrics_specs)

    realized_r_index: dict[str, float] | None = None
    if args.realized_r_join:
        realized_r_index = load_realized_r_index(args.realized_r_join)

    client = None
    if args.live:  # pragma: no cover — gated --live, not in test suite
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError:
            logger.error("--live requires the `anthropic` SDK installed.")
            return 2
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("--live requires ANTHROPIC_API_KEY env var.")
            return 2
        client = Anthropic(api_key=api_key)

    paired = evaluate_pair(
        prompt_a, prompt_b, fixtures,
        seed=args.seed, live=args.live, client=client,
        realized_r_index=realized_r_index,
    )

    report = compute_metrics(
        paired, metrics_specs,
        has_realized_r=bool(realized_r_index),
    )
    report["prompt_a"] = {"path": prompt_a.path, "sha256": prompt_a.sha256}
    report["prompt_b"] = {"path": prompt_b.path, "sha256": prompt_b.sha256}
    report["metrics_yaml_path"] = args.metrics
    report["fixtures_spec"] = args.fixtures

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    _write_results_jsonl(out_dir / "results.jsonl", paired)
    _write_metrics_report(out_dir / "metrics_report.json", report)
    _write_decision_diff(out_dir / "decision_diff.md", paired, prompt_a, prompt_b)
    _write_run_metadata(out_dir / "run_metadata.json", args, prompt_a, prompt_b,
                        len(fixtures))

    logger.info("Done. Wrote %s", out_dir)
    # Surface a brief summary line
    n_diff = sum(1 for r in paired
                 if r.decision_a.decision != r.decision_b.decision)
    logger.info("Fixtures: %d  divergent decisions: %d  realized-R join: %d",
                len(paired), n_diff, report["n_with_realized_r"])
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
