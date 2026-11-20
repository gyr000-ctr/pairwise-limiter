"""提前停止（limit）相关的约束测试：正确性、边界、并发、内存与耗时。"""

import gc
import statistics
import threading
import time
import tracemalloc

import pytest

import limitedec

DATA = [float(i) / 10 for i in range(200)]


def _decoder(samples=None):
    return limitedec.LimitedDecoder(DATA if samples is None else samples)


def test_limit_prefix_matches_full_decode():
    full = _decoder().decode()
    for n in (0, 1, 2, 7, 50, len(DATA)):
        assert _decoder().decode(n) == full[:n]


def test_limit_zero_does_no_decoding():
    dec = _decoder()
    assert dec.decode(0) == []
    assert dec.decode(0) == []
    assert dec.decoded() == 0


def test_limit_exceeds_total_raises_clear_error():
    dec = _decoder()
    with pytest.raises(ValueError, match=r"exceeds the total number of samples \(200\)"):
        dec.decode(len(DATA) + 1)
    with pytest.raises(ValueError):
        dec.decode(-1)
    # 报错后对象仍然可用
    assert dec.decode(3) == DATA[:3]


def test_limit_reusable_and_repeatable_after_stop():
    dec = _decoder()
    assert dec.decode(5) == DATA[:5]
    assert dec.decode(5) == DATA[:5]
    assert dec.decode(3) == DATA[:3]
    assert dec.decoded() == 5
    dec.reset()
    assert dec.decoded() == 0
    assert dec.decode(0) == []
    assert dec.decode(2) == DATA[:2]
    assert dec.decoded() == 2


def test_limit_concurrent_calls_match_serial():
    dec = _decoder()
    calls = [7, 0, 200, 1, 50, 7, 0, 13] * 25
    serial = [_decoder().decode(n) for n in calls]
    expected = {n: DATA[:n] for n in calls}

    results = [None] * len(calls)

    def worker(indices):
        for i in indices:
            results[i] = dec.decode(calls[i])

    threads = [
        threading.Thread(target=worker, args=(range(0, len(calls), 2),)),
        threading.Thread(target=worker, args=(range(1, len(calls), 2),)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results == serial
    for n, got in zip(calls, results):
        assert got == expected[n]
    assert dec.decoded() == max(calls)


def test_limit_memory_stable_after_1000_decodes():
    dec = _decoder()
    for _ in range(50):
        dec.decode(100)
    gc.collect()
    tracemalloc.start()
    try:
        gc.collect()
        base = tracemalloc.take_snapshot()
        for _ in range(1000):
            dec.decode(100)
        gc.collect()
        after = tracemalloc.take_snapshot()
        growth = sum(s.size_diff for s in after.compare_to(base, "filename"))
    finally:
        tracemalloc.stop()
    assert growth < 200 * 1024, "memory grew by %d bytes" % growth


def test_limit_call_cost_independent_of_decoded_count():
    def median_cost(dec, n, repeat=400):
        dec.decode(n)  # 预热
        samples = []
        for _ in range(repeat):
            t0 = time.perf_counter_ns()
            dec.decode(n)
            samples.append(time.perf_counter_ns() - t0)
        return statistics.median(samples)

    fresh = _decoder()
    early = median_cost(fresh, 8)
    fresh.decode(len(DATA))  # 已解样本数处于高位
    late = median_cost(fresh, 8)

    # 允许 3 倍抖动，任何与已解数量相关的累积实现都会超出该界限。
    assert late <= early * 3 + 5_000, (early, late)
