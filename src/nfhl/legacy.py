"""Warn when a feature holds a legacy value.

A legacy value is one the NFHL holds and the reference the models track does not
list, common enough in the data that rejecting it would reject a large share of
real features (`spec/legacy.json` sets the threshold and records the counts).
The generated enums give each one a member whose description begins `Legacy:`,
so the status is in the schema and the docs; this module adds the runtime half,
a `LegacyValueWarning` per use.

It is a warning, not a rule: the feature validates. That is why it is a
validator rather than a constraint -- there is nothing for the JSON Schema or
the docs to enforce, only something for a Python caller to hear about.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable, Collection
from enum import Enum

from pydantic import BaseModel


class LegacyValueWarning(UserWarning):
    """A field holds a value the current reference does not list."""


def warn_on_legacy_values[M: BaseModel](
    legacy: Collection[Enum], edition: str
) -> Callable[[M], M]:
    """An after-validator that warns once per field holding a member of `legacy`.

    Filter with `warnings.simplefilter("error", LegacyValueWarning)` to reject
    legacy values, or `"ignore"` to accept them silently.
    """

    # By enum and member, not by value: the enums are `str` enums, so
    # `LocAccuracy.NP == StudyTyp.NP`, and only the first is legacy.
    members = frozenset((type(m), m.name) for m in legacy)

    def check(model: M) -> M:
        for name, info in type(model).model_fields.items():
            value = getattr(model, name, None)
            if isinstance(value, Enum) and (type(value), value.name) in members:
                warnings.warn(
                    f"{info.alias or name}={value.value!r} is a legacy value, not "
                    f"in FEMA's {edition} Domain Tables Technical Reference",
                    LegacyValueWarning,
                    # Past this function and pydantic's entry point, to the caller.
                    stacklevel=3,
                )
        return model

    return check
