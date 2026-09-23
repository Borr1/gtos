# Market Expansion Conditioned Sizing Refinement

Decision: `MARKET_EXPANSION_CONDITIONED_SIZING_REFINEMENT_BUILT_DEFAULT_OFF_NOT_LIVE_AUTHORITY`

Runtime effect: `none_conditioned_sizing_refinement_only`

## Result

- Replay policy rows: `26`.
- Daily replay rows: `1679`.
- Best monthly policy: `positive_weighted12_after_swap` at weight `0.25`, monthly `5.09`.
- Best drawdown policy: `robust6_every_split_positive` at weight `0.4`, maxDD `7.956872`.

This route shows market expansion should not be treated as a flat all-sleeve
overlay. The useful form is conditioned/default-off: stronger candidates can be
preserved for activation audit, while weaker candidates become context, veto,
sizing, or redesign inputs. No live authority or config activation is claimed.
