from src.components.ultimate_book.minimal_size import f5_standing_hold_reason as hold

NS = "operator"
book = [
    {"symbol": "EURUSD", "direction": "SHORT", "family": "W7:dsp_walked_h"},
    {"symbol": "GBPJPY", "direction": "LONG", "family": "W7:asia_pdl_fade"},
    {"symbol": "GER40", "direction": "SHORT", "family": "W7:idxrev"},
    {"symbol": "US30", "direction": "SHORT", "family": "W7:idxrev"},
]
occ = [r["symbol"] for r in book]

cases = [
    ("EURUSD", "SHORT", "dsp_c19", "same_symbol_stack_keep_working_ticket"),
    ("USDJPY", "LONG", "dsp_london", "usdjpy_verification_hold_5pip_dsp_stop"),
    ("GBPUSD", "SHORT", "dsp_walked_hi", "same_currency_dsp_stack_one_bet"),
    ("GBPJPY", "SHORT", "dsp_walked_hi", "same_currency_dsp_stack_one_bet"),
    ("GBPUSD", "LONG", "dsp_walked_hi", None),  # opposite
    ("GBPJPY", "LONG", "dsp_walked_hi", None),  # same symbol? GBPJPY is occupied -> same symbol
    ("AUDUSD", "SHORT", "dsp_walked_hi", None),
    ("EURUSD", "SHORT", "asia_pdl_fade", "same_symbol_stack_keep_working_ticket"),
    ("GBPUSD", "SHORT", "asia_pdl_fade", None),  # fade is other card
    ("UK100", "LONG", "idxrev", None),
]
# GBPJPY occupied so any GBPJPY is same-symbol
assert hold(NS, "GBPJPY", occ, direction="LONG", family="dsp_x", occupied_book=book) == "same_symbol_stack_keep_working_ticket"

failed = []
for sym, d, fam, want in cases:
    got = hold(NS, sym, occ, direction=d, family=fam, occupied_book=book)
    if got != want:
        failed.append((sym, d, fam, want, got))
        print("FAIL", sym, d, fam, "want", want, "got", got)
    else:
        print("ok", sym, d, fam, "->", got)
print("failed", len(failed))
raise SystemExit(1 if failed else 0)
