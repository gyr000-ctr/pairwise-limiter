import math

import pytest

import limitedec

def _raises(fn, exc=ValueError):
    try:
        fn()
    except exc:
        return True
    return False

DATA = [float(i) / 10 for i in range(20)]


def _d(n=None, samples=None):
    dec = limitedec.LimitedDecoder(samples or DATA)
    return dec.decode(n)


def _same_prefix(n):
    full = _d(None)
    return _d(n) == full[:n]

CASES = [
        ("full", lambda: _d() == DATA),
        ("prefix", lambda: _same_prefix(5)),
        ("zero", lambda: _d(0) == []),
        ("one", lambda: _d(1) == [0.0]),
        ("all", lambda: _d(20) == DATA),
        ("too_many", lambda: _raises(lambda: _d(21))),
        ("negative", lambda: _raises(lambda: _d(-1))),
        ("decoded_count", lambda: (lambda d: (d.decode(3), d.decoded() == 3)[1])(limitedec.LimitedDecoder(DATA))),
        ("reset", lambda: (lambda d: (d.decode(3), d.reset(), d.decoded() == 0)[2])(limitedec.LimitedDecoder(DATA))),
        ("empty", lambda: limitedec.LimitedDecoder([]).decode() == []),
        ("prefix_two", lambda: _same_prefix(2)),
        ("type", lambda: isinstance(_d(3), list)),
        ("float", lambda: all(isinstance(v, float) for v in _d(3))),
        ("continue", lambda: (lambda d: (d.decode(2), d.decode(4), d.decoded() == 4)[2])(limitedec.LimitedDecoder(DATA))),
        ("deterministic", lambda: _d(7) == _d(7)),
    ]


@pytest.mark.parametrize("name,check", CASES, ids=[c[0] for c in CASES])
def test_spec(name, check):
    assert check() is True
