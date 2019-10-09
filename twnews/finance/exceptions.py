class SyncException(Exception):
    """
    """
    def __init__(self, reason):
        self.reason = reason

class NetworkException(SyncException):
    """
    """

class InvalidDataException(SyncException):
    """
    """
