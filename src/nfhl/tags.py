"""Tag this package's models so the tools select them with `--tag nfhl`."""

from __future__ import annotations

from collections.abc import Iterable

from overture.schema.system.discovery import ModelKey
from pydantic import BaseModel


def nfhl_provider(
    types: Iterable[type[BaseModel]], key: ModelKey, tags: set[str]
) -> set[str]:
    """Add `nfhl` to every model registered from this package."""
    if key.entry_point.startswith("nfhl."):
        tags.add("nfhl")
    return tags
