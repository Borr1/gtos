# vNext Replacement Stage06 Legacy-vs-vNext Delta

Generated: `2026-05-26T12:53:18Z`

## Overall Scenarios

- `old_gtos_live_current_j46_j49`: selected `214536`, performance `214536`, total R `38663.27228651521`, expectancy `0.18021810925213116`, WR `0.27971529253831523`, PF `1.2997987090021217`
- `legacy_fixed_1_5r_comparator`: selected `214536`, performance `214536`, total R `80776.05194895045`, expectancy `0.37651513941226855`, WR `0.5534595592348137`, PF `1.8608793715298464`
- `moonshot_be_after_trigger`: selected `214536`, performance `214536`, total R `83555.67921897703`, expectancy `0.3894716001928676`, WR `0.47152459260916585`, PF `2.2869866229361038`
- `condition_router_challenger`: selected `214536`, performance `214536`, total R `89405.9207919812`, expectancy `0.41674087701822166`, WR `0.5055421933847932`, PF `2.161893919734991`
- `activated_default_source_bound_primary`: selected `15799`, performance `15799`, total R `-7197.108134549356`, expectancy `-0.4555420048452026`, WR `0.05747199189822141`, PF `0.15755923195082117`

## Activation Warning

Stage05/Stage06 preserve the current activated default-router projection, but its source-bound primary slice is negative. Stage12 must fail any production activation overlay that uses this default slice without a repaired branch/selector.
