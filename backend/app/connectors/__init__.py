"""Job data connectors — one interface per source of postings."""

from app.connectors.base import JobDataConnector, RawPosting, SourceDescriptor
from app.connectors.registry import (
    all_connectors,
    bootstrap,
    enabled_connectors,
    get,
    register,
)

__all__ = [
    "JobDataConnector",
    "RawPosting",
    "SourceDescriptor",
    "all_connectors",
    "bootstrap",
    "enabled_connectors",
    "get",
    "register",
]
