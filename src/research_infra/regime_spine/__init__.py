"""regime_spine — the armed book's qualifying conditions, over the whole archive.

Session AB (wave 6). The problem this package exists for, in one line:

    the armed four's out-of-window record mixes *"the edge failed"* with
    *"the setup never appeared"*, and nothing in the estate could tell them apart.

`SESSION_V_ARMED_SET_MC_RESULT.md` §7 measured the armed four at **+0.100 %/month**
pre-2025 and **−0.220 %/month** over 2015–2019, against **+2.617 %/month** inside the
window that selected them, and observed that the book's density of weekday sessions runs
**0.4 % (2015) → 28.7 % (2025)**. A sleeve that does not fire earns nothing, so averaging
a silent era into "out-of-window return" is not a measurement of the rule.

Separating the two needs the **conditions**, not the intents: for every bar the sleeve
could have looked at, which of its gates passed. `x_estate_generate.py` produces the
intents (the last row of the funnel); this package produces the whole funnel.

    state.py       one pass over a bar series -> every statistic any armed sleeve tests
    conditions.py  the sleeves' gate chains, expressed against a state frame
    ramp.py        the firing-rate decomposition: opportunity x per-gate pass rates
    normalize.py   fixed cut -> trailing-percentile cut (the (b) repair)
    dials.py       the named, monitored regime variables (AJ) + feature rows (AH)
    trials.py      the trial-budget appender every variant here is logged to

FIDELITY IS THE WHOLE POINT, SO IT IS TESTED TWICE
---------------------------------------------------
`state.py` recomputes the production statistics with rolling accumulators because a
sweep needs them thousands of times. That is a re-implementation, which is exactly the
thing this programme keeps getting burned by. Two independent checks, both behavioural:

1. `tests/research_infra/test_regime_spine_state.py` asserts the frame agrees, bar for
   bar, with `primitives.atr14/autocorr/vol_ratio`, `metals.htf_trend/fvg_signal`,
   `substrate_engine.compute_state` and `crypto.crypto_signal` on real archive bars.
2. `tests/research_infra/test_regime_spine_conditions.py` asserts the FIRE set this
   package derives is exactly the set of trades `X_ESTATE_TRADES.json.gz` recorded —
   which were generated through the live `UltimateBookLiveEngine._generate_intents` via
   `GenerationPort`. Agreement there is agreement with production, not with a copy.

Nothing here places, sizes, admits, or touches the broker. It reads gzipped CSV bars and
writes JSON.
"""

from __future__ import annotations

SCHEMA = "gtos.wave6.regime_spine.v1"

__all__ = ["SCHEMA"]
