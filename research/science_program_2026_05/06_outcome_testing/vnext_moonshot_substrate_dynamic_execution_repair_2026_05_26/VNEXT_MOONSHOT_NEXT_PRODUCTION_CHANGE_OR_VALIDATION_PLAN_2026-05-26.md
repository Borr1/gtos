# Next Production Change Or Validation Plan

1. Keep all moonshot router flags default-off. Do not activate without owner approval.
2. Forward-capture broker lifecycle fields: order/deal tickets, fill/close prices and times, commissions, swaps, slippage, partial exits, BE/trailing/time-stop modify results, pending lifecycle, and source join IDs.
3. Run a default-off shadow validation of `be_after_trigger` prop-pass default versus `condition_asof_displacement_v1` challenger on forward-captured rows.
4. Add ordered tick/LTF path adjudication only where it can be joined to exact entry/stop/target and broker lifecycle truth.
5. Re-run prop EV with condition router after exact transition traces exist; reject it again if pass efficiency stays below BE, or promote default-off if prop and row evidence both win.
6. Expand candidate-origin validation beyond OB/FVG/breaker only where source-safe local or forward-captured data can produce row-level evidence.
7. Keep AI constrained to ambiguity/source/policy conflict strata; keep ML shadow-only until sealed validation shows stable lift.
