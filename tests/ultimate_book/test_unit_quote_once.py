"""One terminal quote per symbol per cycle, including when slots ask together."""

import threading

from src.components.ultimate_book.book_engine import UltimateBookLiveEngine, _CHALLENGE_NS


class _QuoteBook:
    def __init__(self):
        self.calls = []
        self._namespace = _CHALLENGE_NS
        self._unit_quote_lock = threading.Lock()

    def _broker_symbol(self, symbol):
        return symbol

    def _unit_number(self, value):
        if value is None:
            return None
        return float(value)

    def get_tick(self, symbol):
        self.calls.append(symbol)
        return {"bid": 1.0, "ask": 1.1}

    _mt5 = property(lambda self: self)


def test_parallel_slots_share_one_quote():
    book = _QuoteBook()
    errors = []

    def ask():
        try:
            UltimateBookLiveEngine._unit_quote(book, "EURUSD")
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=ask) for _ in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    assert book.calls == ["EURUSD"]
    assert UltimateBookLiveEngine._unit_quote(book, "XAUUSD") == (1.0, 1.1)
    assert book.calls == ["EURUSD", "XAUUSD"]


def test_prime_reads_each_symbol_once():
    book = _QuoteBook()
    book._slot_fetch_count = lambda spec: 4
    book._closed_series = lambda *args, **kwargs: None
    book._unit_quote = lambda symbol: UltimateBookLiveEngine._unit_quote(book, symbol)

    class _Spec:
        timeframe = 15

    slots = [(_Spec(), "EURUSD"), (_Spec(), "EURUSD"), (_Spec(), "XAUUSD")]
    UltimateBookLiveEngine._prime_challenge_reads(book, slots, None, {})
    assert book.calls == ["EURUSD", "XAUUSD"]
