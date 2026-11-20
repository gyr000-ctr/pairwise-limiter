"""limitedec 核心 API（初始未实现）。"""


class LimitedDecoder:
    def __init__(self, samples):
        """构造解码器"""
        raise NotImplementedError

    def decode(self, n=None):
        """解码前 n 个"""
        raise NotImplementedError

    def decoded(self):
        """已解数量"""
        raise NotImplementedError

    def reset(self):
        """重置"""
        raise NotImplementedError
