"""
例外模組
"""

class SyncException(Exception):
    """
    同步資料時觸發的例外
    """
    def __init__(self, reason):
        self.reason = reason

class NetworkException(SyncException):
    """
    因網路問題觸發的例外
    """

class InvalidDataException(SyncException):
    """
    因無效資料問題觸發的例外
    """
