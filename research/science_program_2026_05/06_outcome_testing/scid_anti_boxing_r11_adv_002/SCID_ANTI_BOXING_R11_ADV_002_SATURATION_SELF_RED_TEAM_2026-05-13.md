# ADV-002 Saturation And Self-Red-Team

Evidence class: `ADV-002_SOURCE_CONTROL_DESIGN_ONLY`.

No outcome/result labels, broker account/order/history/deal/position evidence, AI/API calls, paid/vendor access, raw market blobs, live restarts, or trading/risk/safety/prompt-decision changes were opened.

## Could source-control evidence be mistaken for result evidence?

No. Every artifact carries may_open_outcomes_or_results_in_this_route=false and the verifier rejects safe-flag drift.

Same-class action: Added explicit future G12/G0 gate prompts rather than scoring anything here.

## Could duplicate rows leak into future sample size?

The policy freezes row-level, duplicate-key, canonical-row, group, and cross-card views before labels open.

Same-class action: Added fail-closed statuses for missing duplicate key, canonical row, and group membership version.

## Could group membership drift silently rewrite a denominator?

The route requires group_membership_version and group_membership_manifest_sha256; current lack of a universal field is an exact blocker.

Same-class action: Recorded ADV002-BLOCKER-GROUP-VERSION with exact future source requirement.

## Could session/symbol/timeframe aliases make one opportunity look like several?

The route binds canonical economic group, symbol/source, session calendar, timeframe, decision_asof_utc, and entry reference time.

Same-class action: Added SESSION_SYMBOL_TIMEFRAME_COLLISION_UNRESOLVED fail-closed status.

## Could EOL friction produce false source mismatches?

Text artifacts require byte and LF-normalized hashes; raw/binary files keep strict hashes only.

Same-class action: Added G12 audit check for text EOL policy without relaxing row_hash/count/as-of checks.

## Did the route collapse to current GTOS OB/retest framing?

No. ADV-002 is an adversarial placebo/control route about denominator artifacts, not an OB mechanism test.

Same-class action: Route decisions and future prompts explicitly preserve this non-OB scope.

## Terminal Posture

`NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` remain closed. Any future scoring must pass through G12/G0 source-control acceptance first.
