"""Field metadata for values whose meaning is held in another field.

GATIS puts a unit in the field name (`width_in`), so the unit is fixed by the
schema. The FIRM Database cannot: `STATIC_BFE` is in whatever `LEN_UNIT` says on
the same feature, and is measured from whatever `V_DATUM` says. Neither the
service nor the reference makes that link machine-readable -- it is one sentence
in each unit field's description -- so `UnitIn` and `DatumIn` declare it on the
measured field, where a consumer converting units has to look.

Neither participates in validation. Read them with `field_units` and
`field_datums`, or from `typing.get_type_hints(..., include_extras=True)`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any, get_args, get_origin, get_type_hints

from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class UnitIn:
    """This value's unit is the value of `field` on the same feature."""

    field: str

    def __str__(self) -> str:
        # The Overture markdown generator renders unknown metadata with str().
        return f"unit given by {self.field}"


@dataclass(frozen=True, slots=True)
class DatumIn:
    """This elevation is measured from the vertical datum named in `field`."""

    field: str

    def __str__(self) -> str:
        return f"vertical datum given by {self.field}"


def field_units(model: type[BaseModel]) -> dict[str, UnitIn]:
    """Wire name of each field that declares where its unit is held."""
    return _annotations_of(model, UnitIn)


def field_datums(model: type[BaseModel]) -> dict[str, DatumIn]:
    """Wire name of each field that declares where its vertical datum is held."""
    return _annotations_of(model, DatumIn)


def _annotations_of(model: type[BaseModel], kind: type[Any]) -> dict[str, Any]:
    found = {}
    hints = get_type_hints(model, include_extras=True)
    for name, info in model.model_fields.items():
        for metadata in [*info.metadata, *_unwrap(hints.get(name))]:
            if isinstance(metadata, kind):
                found[info.alias or name] = metadata
                break
    return found


def _unwrap(hint: Any) -> list[Any]:
    """Annotated metadata, looking through unions."""
    if hint is None:
        return []
    if get_origin(hint) is Annotated:
        args = get_args(hint)
        return [*args[1:], *_unwrap(args[0])]
    return [item for arg in get_args(hint) for item in _unwrap(arg)]
