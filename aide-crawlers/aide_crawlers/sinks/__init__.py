"""Sinks module

Export all available sinks
"""

from .abstract import AbstractSink, SinkResult
from .db_sink import DBSink
from .local_sink import LocalSink

__all__ = [
    "AbstractSink",
    "SinkResult",
    "DBSink",
    "LocalSink",
]
