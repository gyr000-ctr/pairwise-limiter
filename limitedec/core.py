"""limitedec 核心 API。"""

import operator
import threading

__all__ = ["LimitedDecoder"]


class LimitedDecoder:
    """可提前停止的样本解码器。

    样本在构造时被固化（元组），因此：

    * ``decode(n)`` 只复制前 ``n`` 个样本，耗时与 ``n`` 成正比，
      与“已经解过多少”无关；
    * 每次调用都返回新的列表，内部不保留解码产物，反复调用不会增长内存；
    * 只有 ``decoded()`` 的高水位计数需要加锁更新，解码本身不共享可变状态，
      同一对象可被多个线程并发调用。
    """

    __slots__ = ("_samples", "_total", "_decoded", "_lock")

    def __init__(self, samples):
        """构造解码器；``samples`` 可以是任意可迭代对象。"""
        self._samples = tuple(samples)
        self._total = len(self._samples)
        self._decoded = 0
        self._lock = threading.Lock()

    def decode(self, n=None):
        """解码前 ``n`` 个样本并返回列表；``n`` 为 ``None`` 表示全部。

        ``n == 0`` 直接返回空列表，不会触碰任何样本。
        """
        if n is None:
            n = self._total
        else:
            try:
                n = operator.index(n)
            except TypeError:
                raise TypeError(
                    "n must be an integer or None, got %r" % (type(n).__name__,)
                ) from None
            if n < 0:
                raise ValueError("n must be non-negative, got %d" % (n,))
            if n > self._total:
                raise ValueError(
                    "n=%d exceeds the total number of samples (%d)"
                    % (n, self._total)
                )

        if n == 0:
            return []

        # 只复制前 n 项：O(n)，且不依赖已解数量。
        result = list(self._samples[:n])

        with self._lock:
            if n > self._decoded:
                self._decoded = n

        return result

    def decoded(self):
        """返回已解码样本数（历史高水位）。"""
        with self._lock:
            return self._decoded

    def reset(self):
        """重置已解码计数；解码器本身可继续使用。"""
        with self._lock:
            self._decoded = 0
