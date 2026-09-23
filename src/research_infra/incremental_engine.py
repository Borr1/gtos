"""Incremental backtest engine (L55, Phase 1).

Re-evaluates only the candles whose AI-evaluation inputs (or the prompt or the
evaluation-relevant config subset) have changed since a prior T7 run, and merges
the fresh results back onto the unchanged ones.

Why this exists
---------------
Phase 1+2 prompt research will iterate. Each T7 full run is currently 30-60 min
sequential or <10 min parallel (L54). But most candle decisions are unchanged
when only the prompt changes — same MSO, same kill zone, same instrument. If
we hash the inputs that drive an AI evaluation, we can answer the question
"would the AI's answer for this candle change?" without calling the API.

Reuse only happens iff ALL THREE of the following match the prior run:
  1. The candle's evaluation inputs (the MSO subset that flows into the prompt)
  2. The prompt file content
  3. A small whitelist of config keys that drive AI behavior

Anything else (logging knobs, telegram channels, watchdog cadences, monthly
caps, etc.) is treated as cache-stable and does NOT bust reuse.

Out of scope
------------
- This module does NOT call the Anthropic API. It plans the diff. The actual
  re-evaluation is delegated to ``scripts/simulate_t7_live_period.py`` via the
  CLI script ``scripts/research/simulate_t7_incremental.py``.
- It does NOT modify production paths. It is additive-only research infra.
- Hash collisions are theoretically possible but the input space is large
  enough (sha256 over canonical JSON) that probabilistic collisions are not a
  practical concern at our 10⁴-10⁵ candles/run scale.

Hashing contract
----------------
``hash_candle_inputs(raw_data)`` hashes a deterministic canonical JSON dump of
a SUBSET of the candle's input dict. The subset is documented in
``CANDLE_INPUT_HASH_KEYS`` below. Anything outside that subset (free-form
metadata, generation timestamps, ad-hoc debug dumps) is intentionally NOT
hashed — including such fields would create false-negative cache misses on
trivial drift.

``hash_prompt(path)`` is a sha256 of the file's bytes (UTF-8 read). Newlines
are normalized to LF before hashing so a Windows-checkout vs Unix-checkout
of the same prompt does not bust reuse.

Config-relevant subset
----------------------
``CONFIG_RELEVANT_KEYS`` is a hand-curated whitelist of agent_config.yaml dotted
key paths whose values flow into AI evaluation. Each entry is annotated with a
brief reason. Adding a new key requires demonstrating that it changes either:
  - the system prompt content (build_system_prompt),
  - the user-message content (mso filter, framework selection, etc.),
  - the model identity / sampling params, or
  - a deterministic gate that runs BEFORE the AI call (prescreen, bias,
    ob_proximity, skip_first_ny).

Keys that gate behavior AFTER the AI emits its decision (L2 verification,
inverted-TP correction, max-trades-per-day) belong in the whitelist too —
because they affect whether the candle's recorded decision would change in
a re-run, even if the AI itself returned the same JSON.

Example
-------
::

    plan = IncrementalRunPlan(
        prior_results_path=Path("research/t7_2026q1_v3/all_results.json"),
        current_prompt_path=Path("src/prompts/primary_analyzer_prompt.py"),
        current_config_path=Path("config/agent_config.yaml"),
    )
    diff = plan.compute_diff()
    print(f"{diff.n_unchanged}/{diff.n_total_candles} unchanged "
          f"({diff.reuse_ratio*100:.1f}%); will re-evaluate {diff.n_changed}.")

    # diff.changed_candles is a list of CandleRef; pass them to the inner sim.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml


# ════════════════════════════════════════════════════════════════════════════
# Hashing — candle inputs
# ════════════════════════════════════════════════════════════════════════════

# The keys we hash from each candle's raw input. Anything outside this set is
# considered "metadata" and does NOT bust reuse. This is the contract that
# documents what an "unchanged input" means.
#
# Rationale per key:
#   candle_time   - identity of the candle being evaluated
#   symbol        - which instrument the AI is reasoning about
#   kill_zone     - prompt section selector + AI context
#   market_state  - the MSO that the AI consumes (swings/OBs/FVGs/liquidity)
#   prescreen     - deterministic pre-AI gate result (pass/fail wording)
#   bias          - deterministic D1/H4 bias output
#   bias_source   - which timeframe(s) the bias was derived from
#   ob_proximity  - whether the OB-distance gate let the call through
#   candle_close  - close price feeds align_context + L2 fill-distance
#
# Excluded by design:
#   cost, decision, p2a_*, l2_*, outcome metadata, run-specific timestamps.
#   These are RESULTS, not INPUTS. Including them would bust reuse on every
#   prompt change (since the recorded decision changes), defeating the point.
CANDLE_INPUT_HASH_KEYS: tuple[str, ...] = (
    "candle_time",
    "symbol",
    "kill_zone",
    "market_state",
    "prescreen",
    "bias",
    "bias_source",
    "ob_proximity",
    "candle_close",
)

# Result-record keys that are STABLE inputs in the all_results.json schema.
# Older fixtures may not carry every CANDLE_INPUT_HASH_KEYS entry (e.g., the
# T7 simulator only began emitting `prescreen` in late April 2026); when a key
# is missing we record it as the sentinel string "<absent>" so the absence is
# itself part of the hash.
_HASH_ABSENT_SENTINEL = "<absent>"


def _canonical(obj: Any) -> Any:
    """Return a canonical, hash-stable form of ``obj``.

    Rules:
      - dicts are returned with sorted string keys
      - tuples become lists (so JSON dump is identity-stable)
      - sets become sorted lists
      - everything else falls through to JSON's default handlers

    The hash function builds a JSON string from this and digests UTF-8 bytes.
    """
    if isinstance(obj, dict):
        return {str(k): _canonical(obj[k]) for k in sorted(obj, key=str)}
    if isinstance(obj, (list, tuple)):
        return [_canonical(x) for x in obj]
    if isinstance(obj, set):
        return sorted([_canonical(x) for x in obj], key=lambda v: json.dumps(v, sort_keys=True))
    return obj


def hash_candle_inputs(raw_data: dict) -> str:
    """Return a deterministic sha256 of the input subset that drives a candle.

    Hashes only the keys in :data:`CANDLE_INPUT_HASH_KEYS`. A key absent from
    ``raw_data`` is folded in as the sentinel ``"<absent>"`` so two candles
    that differ in whether the key is present do NOT produce the same hash.

    The function is deterministic across processes and OSes: keys are sorted,
    nested dicts are canonicalized, JSON is dumped with ``sort_keys=True`` and
    no whitespace, and the digest is UTF-8 sha256.

    Parameters
    ----------
    raw_data :
        A single candle record dict (typically one element of
        ``all_results.json["results"]``). Extra keys outside the hash whitelist
        are silently ignored.

    Returns
    -------
    str
        A 64-char hex sha256 digest.

    Raises
    ------
    TypeError
        If ``raw_data`` is not a mapping.
    """
    if not isinstance(raw_data, dict):
        raise TypeError(
            f"hash_candle_inputs: expected dict, got {type(raw_data).__name__}"
        )

    subset: dict[str, Any] = {}
    for key in CANDLE_INPUT_HASH_KEYS:
        if key in raw_data:
            subset[key] = _canonical(raw_data[key])
        else:
            subset[key] = _HASH_ABSENT_SENTINEL

    payload = json.dumps(subset, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ════════════════════════════════════════════════════════════════════════════
# Hashing — prompt
# ════════════════════════════════════════════════════════════════════════════


def hash_prompt(prompt_path: str | Path) -> str:
    """Return a sha256 over the prompt file's normalized contents.

    Newlines are normalized to ``\\n`` before hashing so a Windows checkout
    (CRLF) and a Unix checkout (LF) of the same source file produce the same
    hash. Trailing whitespace is preserved (it can be load-bearing inside
    here-strings).

    Parameters
    ----------
    prompt_path :
        Filesystem path to the prompt file. Read as UTF-8 with strict mode.

    Returns
    -------
    str
        A 64-char hex sha256 digest.

    Raises
    ------
    FileNotFoundError
        If the file does not exist. The caller is expected to surface this as
        a planning error so the user can fix the path before re-trying.
    """
    p = Path(prompt_path)
    if not p.exists():
        raise FileNotFoundError(f"hash_prompt: prompt file not found: {p}")
    if not p.is_file():
        raise IsADirectoryError(f"hash_prompt: path is not a regular file: {p}")
    text = p.read_text(encoding="utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ════════════════════════════════════════════════════════════════════════════
# Config-relevant subset
# ════════════════════════════════════════════════════════════════════════════

# Whitelist of agent_config.yaml dotted key paths that drive AI evaluation.
# Edits to ANY of these keys force re-evaluation of every candle.
#
# Each entry is annotated with WHY it's evaluation-relevant. Keep this list
# tight: false-positives here cost ~$30 of unnecessary API calls per full
# rerun; false-negatives here mean stale results sneak through unchanged.
#
# Keys NOT in this list (e.g., monitoring.dashboard_port, telegram.*,
# watchdog.*, budget.*, retrieval.*, trade_capture.*) are intentionally
# considered cache-stable.
CONFIG_RELEVANT_KEYS: tuple[str, ...] = (
    # ── Model identity + sampling ────────────────────────────────────────────
    "ai.primary_model",          # which Sonnet/Opus checkpoint the gate calls
    "ai.primary_effort",         # min/max effort changes the answer
    "ai.api_timeout_seconds",    # too-short timeout = systematic empty answers
    # ── Framework selection (changes prompt + L2 path) ───────────────────────
    "model_a.enabled_frameworks",
    "model_a.bias_timeframes",
    "model_a.setup_timeframe",
    "model_a.entry_timeframe",
    "model_a.ote_zone_fib_top",
    "model_a.ote_zone_fib_bottom",
    "model_a.displacement_min_ratio",
    "model_a.equal_level_tolerance",
    # ── Prompt-level substitutions (build_system_prompt) ─────────────────────
    "market.symbol",
    "market.kill_zones",
    "prompt.zone_width_max",
    "prompt.ob_buffer",
    "prompt.price_format",
    "risk.sl_absolute_min",
    "risk.sl_buffer_atr_multiplier",
    "risk.sl_buffer_breaker_atr_multiplier",
    "risk.sl_buffer_min_ticks",
    # ── Pre-AI gates (run BEFORE the AI call) ────────────────────────────────
    "filters.max_gap_pct",                       # OB-gap prescreen
    "skip_first_ny_candle",                      # 13:00 NY skip
    "session_memory_enabled",                    # adds prior-candle context
    "confidence_filter_mode",                    # shadow vs active
    "cross_instrument_context_disabled_for",     # XAU bleed control
    "cross_instrument_context.correlation_gate_threshold",
    "market_state.detector_version",             # v1 vs v2 vs v2_shadow
    # ── Post-AI gates that change the recorded decision in the result ────────
    "verification.enabled",
    "verification.ob_price_tolerance_pct",
    "verification.strict_zone_check",
    "verification.sl_beyond_ob_tick_floor",
    "verification.sl_beyond_ob_tolerance_enabled",
    "gate1.touch_count_reject_threshold",
    "gate1.ob_retest_sl_exception",
    "gate1.ob_retest_sl_min_buffer_atr",
    "gate1.sl_liquidity_cluster_enabled",
    "gate1.sl_liquidity_cluster_margin_atr",
    "risk.min_rr",                               # inverted-TP geometry uses this
    "drawdown_reduction.min_rr",                 # active when DD-mode set
)


def _get_dotted(d: dict, dotted: str) -> Any:
    """Look up ``dotted`` (e.g. ``"risk.min_rr"``) in a nested dict.

    Returns the sentinel ``_CONFIG_KEY_ABSENT`` when any segment is missing,
    so the caller can distinguish "key absent" from "key set to None".
    """
    cur: Any = d
    for seg in dotted.split("."):
        if not isinstance(cur, dict) or seg not in cur:
            return _CONFIG_KEY_ABSENT
        cur = cur[seg]
    return cur


_CONFIG_KEY_ABSENT = object()


def hash_config_subset(config: dict) -> str:
    """Return a sha256 over the config-relevant whitelist subset of ``config``.

    Keys not in :data:`CONFIG_RELEVANT_KEYS` are NOT hashed — edits to them
    leave the digest unchanged and the candle is reusable.

    Absent keys are folded in as the sentinel string ``"<absent>"`` so adding
    a new key in the current config (vs not having it in the prior config)
    busts reuse.
    """
    if not isinstance(config, dict):
        raise TypeError(
            f"hash_config_subset: expected dict, got {type(config).__name__}"
        )

    subset: dict[str, Any] = {}
    for key in CONFIG_RELEVANT_KEYS:
        v = _get_dotted(config, key)
        if v is _CONFIG_KEY_ABSENT:
            subset[key] = _HASH_ABSENT_SENTINEL
        else:
            subset[key] = _canonical(v)

    payload = json.dumps(subset, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ════════════════════════════════════════════════════════════════════════════
# Plan
# ════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CandleRef:
    """Lightweight identity for a candle that needs re-evaluation."""

    candle_time: str         # ISO-8601 close time
    symbol: str
    kill_zone: str
    reason: str              # which check flagged it (input/prompt/config/new)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RunPlan:
    """Output of :meth:`IncrementalRunPlan.compute_diff`.

    Attributes
    ----------
    n_total_candles :
        Union of (prior candles, current candles). Only meaningful relative to
        the prior run window — if the current request expands the window, new
        candles are flagged with ``reason='new'``.
    n_unchanged :
        Candles that match prior on (input hash, prompt hash, config hash).
    n_changed :
        Total candles that need re-evaluation. Equal to
        ``len(changed_candles)``.
    changed_candles :
        Per-candle reasons. Sorted by ``(candle_time, symbol, kill_zone)``.
    reuse_ratio :
        ``n_unchanged / n_total_candles`` in [0.0, 1.0]. 0.0 if total is 0.
    prompt_changed :
        ``True`` when the prompt hash differs from prior.
    config_changed :
        ``True`` when the config-subset hash differs from prior.
    prior_prompt_hash, current_prompt_hash :
        Hex digests for diagnostic logging.
    prior_config_hash, current_config_hash :
        Hex digests for diagnostic logging.
    """

    n_total_candles: int
    n_unchanged: int
    n_changed: int
    changed_candles: list[CandleRef]
    reuse_ratio: float
    prompt_changed: bool
    config_changed: bool
    prior_prompt_hash: str | None
    current_prompt_hash: str | None
    prior_config_hash: str | None
    current_config_hash: str | None

    def to_dict(self) -> dict:
        return {
            "n_total_candles": self.n_total_candles,
            "n_unchanged": self.n_unchanged,
            "n_changed": self.n_changed,
            "reuse_ratio": self.reuse_ratio,
            "prompt_changed": self.prompt_changed,
            "config_changed": self.config_changed,
            "prior_prompt_hash": self.prior_prompt_hash,
            "current_prompt_hash": self.current_prompt_hash,
            "prior_config_hash": self.prior_config_hash,
            "current_config_hash": self.current_config_hash,
            "changed_candles": [c.to_dict() for c in self.changed_candles],
        }


class IncrementalRunPlan:
    """Compute which candles need re-evaluation given prior results + current state.

    Construction is cheap (path validation only). Call :meth:`compute_diff` to
    actually load + hash + diff. The plan is intended to be built once per
    incremental rerun and consumed immediately by the CLI driver.
    """

    def __init__(
        self,
        prior_results_path: str | Path,
        current_prompt_path: str | Path,
        current_config_path: str | Path,
    ) -> None:
        self.prior_results_path = Path(prior_results_path)
        self.current_prompt_path = Path(current_prompt_path)
        self.current_config_path = Path(current_config_path)

    # ── Loading helpers (kept thin so tests can mock individually) ──────────

    def _load_prior_results(self) -> dict:
        """Read and parse ``prior_results_path``.

        Raises
        ------
        FileNotFoundError, ValueError
            With a message that names the path so the CLI can print it.
        """
        if not self.prior_results_path.exists():
            raise FileNotFoundError(
                f"IncrementalRunPlan: prior_results_path not found: "
                f"{self.prior_results_path}"
            )
        try:
            with open(self.prior_results_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"IncrementalRunPlan: prior_results_path is not valid JSON: "
                f"{self.prior_results_path} ({e})"
            ) from e

        if not isinstance(payload, dict):
            raise ValueError(
                f"IncrementalRunPlan: prior_results_path top-level must be a "
                f"dict (got {type(payload).__name__}): {self.prior_results_path}"
            )
        if "results" not in payload or not isinstance(payload["results"], list):
            raise ValueError(
                f"IncrementalRunPlan: prior_results_path missing list-valued "
                f"'results' key: {self.prior_results_path}"
            )
        return payload

    def _load_current_config(self) -> dict:
        if not self.current_config_path.exists():
            raise FileNotFoundError(
                f"IncrementalRunPlan: current_config_path not found: "
                f"{self.current_config_path}"
            )
        with open(self.current_config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(
                f"IncrementalRunPlan: current_config_path must parse to a dict, "
                f"got {type(data).__name__}: {self.current_config_path}"
            )
        return data

    # ── Diff computation ─────────────────────────────────────────────────────

    def compute_diff(self) -> RunPlan:
        """Return a :class:`RunPlan` describing which candles must be re-run.

        Reuse semantics
        ---------------
        A candle is REUSED only if:
          - prior result for its ``(candle_time, symbol, kill_zone)`` triple
            exists,
          - the prior candle's input-hash equals the current input-hash for
            that triple (the inputs themselves are taken from the PRIOR
            record because the current run hasn't been simulated yet — this
            captures whether the input fields recorded last time still match
            the schema this engine reads),
          - the prompt hash matches prior, and
          - the config-subset hash matches prior.

        When prompt or config differs, EVERY prior candle is marked changed
        (the AI may answer differently for any of them). The hashes are still
        included in the plan for diagnostic logging.

        New candles (present in current run window but not in prior) are
        recognised by the caller; this engine only looks at what's in the
        prior file. The CLI driver is responsible for computing the
        post-merge "what's NEW" set if needed.
        """
        prior_payload = self._load_prior_results()
        prior_results: list[dict] = prior_payload["results"]

        # Hashes of the current run state (prompt + config subset).
        current_prompt_hash = hash_prompt(self.current_prompt_path)
        current_config = self._load_current_config()
        current_config_hash = hash_config_subset(current_config)

        # Pull prior hashes from the payload's metadata if the prior run wrote
        # them, otherwise re-derive from the prior result records (best-effort
        # — older prior files may lack the metadata block).
        meta = prior_payload.get("incremental_meta") or {}
        prior_prompt_hash = meta.get("prompt_hash")
        prior_config_hash = meta.get("config_hash")

        # If prior hashes are missing from the file, treat them as "unknown"
        # — the prompt/config diff cannot be detected, so we conservatively
        # mark everything as changed unless the per-candle input hash also
        # carries hash metadata. This keeps incremental safe by default.
        prompt_changed = (
            prior_prompt_hash is None or prior_prompt_hash != current_prompt_hash
        )
        config_changed = (
            prior_config_hash is None or prior_config_hash != current_config_hash
        )

        changed: list[CandleRef] = []
        unchanged_count = 0

        for record in prior_results:
            triple = (
                str(record.get("candle_time", "")),
                str(record.get("symbol", "")),
                str(record.get("kill_zone", "")),
            )
            try:
                input_hash = hash_candle_inputs(record)
            except TypeError:
                # Non-dict record? treat as changed and keep going.
                changed.append(
                    CandleRef(
                        candle_time=triple[0],
                        symbol=triple[1],
                        kill_zone=triple[2],
                        reason="malformed_prior_record",
                    )
                )
                continue

            prior_input_hash = record.get("input_hash")

            input_changed = (
                prior_input_hash is not None and prior_input_hash != input_hash
            )

            if prompt_changed:
                reason = "prompt_changed"
            elif config_changed:
                reason = "config_changed"
            elif input_changed:
                reason = "input_changed"
            else:
                # Survives all three checks. REUSED.
                unchanged_count += 1
                continue

            changed.append(
                CandleRef(
                    candle_time=triple[0],
                    symbol=triple[1],
                    kill_zone=triple[2],
                    reason=reason,
                )
            )

        # Deterministic order: chronological by candle_time, tiebreak symbol+kz.
        changed.sort(key=lambda c: (c.candle_time, c.symbol, c.kill_zone))

        n_total = len(prior_results)
        reuse_ratio = (unchanged_count / n_total) if n_total > 0 else 0.0

        return RunPlan(
            n_total_candles=n_total,
            n_unchanged=unchanged_count,
            n_changed=len(changed),
            changed_candles=changed,
            reuse_ratio=reuse_ratio,
            prompt_changed=prompt_changed,
            config_changed=config_changed,
            prior_prompt_hash=prior_prompt_hash,
            current_prompt_hash=current_prompt_hash,
            prior_config_hash=prior_config_hash,
            current_config_hash=current_config_hash,
        )


# ════════════════════════════════════════════════════════════════════════════
# Merge
# ════════════════════════════════════════════════════════════════════════════


def merge_results(
    prior_results: dict,
    fresh_results: dict[str, dict],
) -> dict:
    """Produce a new ``all_results.json``-shaped dict combining prior + fresh.

    Parameters
    ----------
    prior_results :
        The full payload read from a prior ``all_results.json`` (must contain a
        list-valued ``results`` key).
    fresh_results :
        Mapping ``candle_key -> fresh_record`` where ``candle_key`` is the
        triple ``"{candle_time}|{symbol}|{kill_zone}"``. Records in this map
        OVERRIDE the matching prior record. Records whose key is NOT in this
        map are taken from the prior payload unchanged.

    Returns
    -------
    dict
        A new payload dict with:
          - ``results``: merged list, sorted by ``(candle_time, symbol,
            kill_zone)``.
          - ``start``, ``end``, ``total_cost``: copied from prior, with
            ``total_cost`` augmented by the sum of fresh record costs.
          - ``incremental_meta``: a small block describing the merge
            (counts, hashes if the caller embedded them in fresh_results
            via the special key ``"__meta__"``).

    Behavior notes
    --------------
    - The function is pure: ``prior_results`` is not mutated.
    - When ``fresh_results`` contains a key that does NOT appear in prior, the
      record is treated as a NEW candle and appended.
    - When ``fresh_results`` is partial (covers only a subset of the planned
      changed_candles), the un-covered prior records remain in the output.
      This is the "graceful merge of partial fresh" path the contract
      promises.
    - Output ordering is deterministic: we sort by the triple at the end.
    """
    if not isinstance(prior_results, dict):
        raise TypeError(
            f"merge_results: prior_results must be a dict, got "
            f"{type(prior_results).__name__}"
        )
    if not isinstance(fresh_results, dict):
        raise TypeError(
            f"merge_results: fresh_results must be a dict, got "
            f"{type(fresh_results).__name__}"
        )
    prior_list = prior_results.get("results")
    if not isinstance(prior_list, list):
        raise ValueError(
            "merge_results: prior_results['results'] must be a list"
        )

    # Strip the optional meta key from the fresh map so it does not leak into
    # the merged results array.
    fresh_meta = fresh_results.get("__meta__") if isinstance(fresh_results, dict) else None
    fresh_records = {k: v for k, v in fresh_results.items() if k != "__meta__"}

    merged: list[dict] = []
    seen_keys: set[str] = set()
    for prior_record in prior_list:
        key = candle_key(prior_record)
        if key in fresh_records:
            merged.append(_with_source(fresh_records[key], "fresh"))
        else:
            merged.append(_with_source(prior_record, "prior"))
        seen_keys.add(key)

    # Append any fresh records whose key was NOT in prior (i.e., new candles).
    for k, rec in fresh_records.items():
        if k in seen_keys:
            continue
        merged.append(_with_source(rec, "fresh"))

    # Deterministic order.
    merged.sort(
        key=lambda r: (
            str(r.get("candle_time", "")),
            str(r.get("symbol", "")),
            str(r.get("kill_zone", "")),
        )
    )

    # Cost accounting. Prior total_cost may be missing for very old fixtures.
    fresh_cost = sum(float(r.get("cost", 0) or 0) for r in fresh_records.values())
    prior_cost = float(prior_results.get("total_cost", 0) or 0)
    total_cost = round(prior_cost + fresh_cost, 4)

    out: dict[str, Any] = {
        "start": prior_results.get("start"),
        "end": prior_results.get("end"),
        "total_cost": total_cost,
        "results": merged,
        "incremental_meta": {
            "n_prior": len(prior_list),
            "n_fresh": len(fresh_records),
            "n_merged": len(merged),
            "fresh_cost": round(fresh_cost, 4),
            "prior_cost": round(prior_cost, 4),
        },
    }
    if isinstance(fresh_meta, dict):
        out["incremental_meta"].update(fresh_meta)
    # Preserve any keys we don't explicitly copy (e.g., symbol manifests).
    for k, v in prior_results.items():
        if k not in out and k not in ("results",):
            out[k] = v
    return out


def candle_key(record: dict) -> str:
    """Return the canonical merge key for a candle record.

    The key joins the triple ``(candle_time, symbol, kill_zone)`` with ``|``.
    All-empty triples (e.g., a malformed record) collapse to ``"||"`` and
    will collide — callers must not emit those into ``fresh_results``.
    """
    return "|".join(
        [
            str(record.get("candle_time", "")),
            str(record.get("symbol", "")),
            str(record.get("kill_zone", "")),
        ]
    )


def _with_source(record: dict, source: str) -> dict:
    """Annotate a record with ``incremental_source`` ('prior' | 'fresh').

    Kept additive — does not overwrite an existing source tag if the caller
    set one explicitly (lets a research script tag synthetic records).
    """
    if "incremental_source" in record:
        return record
    out = dict(record)
    out["incremental_source"] = source
    return out


# ════════════════════════════════════════════════════════════════════════════
# Re-export
# ════════════════════════════════════════════════════════════════════════════

__all__ = [
    "CANDLE_INPUT_HASH_KEYS",
    "CONFIG_RELEVANT_KEYS",
    "CandleRef",
    "RunPlan",
    "IncrementalRunPlan",
    "candle_key",
    "hash_candle_inputs",
    "hash_config_subset",
    "hash_prompt",
    "merge_results",
]
