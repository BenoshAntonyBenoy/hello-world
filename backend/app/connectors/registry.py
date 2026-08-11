"""Connector registry.

Sources register themselves at import time; ingestion asks for the ones named
in ``ENABLED_CONNECTORS``. Adding a source means writing the class and adding
one ``register()`` call — no changes to the ingestion code.
"""

from __future__ import annotations

from app.config import settings
from app.connectors.base import JobDataConnector

_REGISTRY: dict[str, JobDataConnector] = {}


def register(connector: JobDataConnector) -> JobDataConnector:
    if not connector.key:
        raise ValueError(f"{type(connector).__name__} must define a non-empty key")
    if connector.key in _REGISTRY:
        raise ValueError(f"Connector {connector.key!r} is already registered")
    _REGISTRY[connector.key] = connector
    return connector


def get(key: str) -> JobDataConnector:
    try:
        return _REGISTRY[key]
    except KeyError:
        known = ", ".join(sorted(_REGISTRY)) or "none"
        raise KeyError(f"Unknown connector {key!r}. Registered: {known}") from None


def all_connectors() -> list[JobDataConnector]:
    return list(_REGISTRY.values())


def enabled_connectors() -> list[JobDataConnector]:
    """Connectors named in configuration, in the order given."""
    return [get(key) for key in settings.connector_list]


def bootstrap() -> None:
    """Import connector modules so their ``register()`` calls run."""
    from app.connectors import synthetic, user_submitted  # noqa: F401
