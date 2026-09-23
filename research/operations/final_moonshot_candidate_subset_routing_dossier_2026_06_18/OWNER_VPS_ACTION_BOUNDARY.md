# Owner/VPS Action Boundary

This route implemented and proved candidate-book allowlist support. Current Mac active config now arms the exact proven full candidate-book sleeve set.
It did not mutate brokers, touch orders, touch credentials, push remotes, or restart VPS processes. VPS process reload remains a separate handoff action.

Active candidate sleeve set:

`ultimate_book_include_candidate_book: true`
`ultimate_book_candidate_book_sleeves: [asia_pdl_fade, asian_fade, kz_london_crypto_low, liq_asia_up_low_metal, metal_session_reversion, ny_crypto_momentum, orb_crypto_london, vol_compression, vss_fxcross_london_up_low]`

Rollback:

`ultimate_book_include_candidate_book: false`
`ultimate_book_candidate_book_sleeves: []`
