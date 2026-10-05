"""Conditions and input handling the generated models need beyond the system's own.

The rules themselves are the system's `forbid_if` and `require_if`, so they reach
the JSON Schema as well as Python. What they lack is a way to say "this field is
not populated": `FieldEqCondition(field, None)` compares the attribute with
`==`, and an omitted `Omitable` field holds Pydantic's `MISSING` sentinel, not
`None`, so the condition is false exactly when the field is absent -- and every
rule built on it would pass vacuously. `Absent` uses the same test the system's
own group constraints use for "has a value": set explicitly, and not `None`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, override

from overture.schema.system.model_constraint import (
    Condition,
    ForbidIfConstraint,
    RequireIfConstraint,
    apply_alias,
)
from pydantic import BaseModel
from pydantic.config import JsonDict


@dataclass(frozen=True, slots=True)
class Absent(Condition):
    """True when `field_name` holds no value."""

    field_name: str

    def __str__(self) -> str:
        return f"{self.field_name} is not populated"

    @override
    def validate_class(self, model_class: type[BaseModel]) -> None:
        if self.field_name not in model_class.model_fields:
            raise TypeError(f"{model_class.__name__} has no field {self.field_name}")

    @override
    def eval(self, model_instance: BaseModel) -> bool:
        return (
            self.field_name not in model_instance.model_fields_set
            or getattr(model_instance, self.field_name) is None
        )

    @override
    def negate(self) -> Condition:
        return Populated(self.field_name)

    @override
    def json_schema(self, model_class: type[BaseModel]) -> JsonDict:
        # `Omitable` fields reject `null`, so "no value" is "property not present".
        return {"not": {"required": [apply_alias(model_class, self.field_name)]}}


@dataclass(frozen=True, slots=True)
class Populated(Condition):
    """True when `field_name` holds a value. The negation of `Absent`.

    Its own class rather than `~Absent(...)` so the rule reads as a sentence in
    the generated reference, which renders a condition with `str()`.
    """

    field_name: str

    def __str__(self) -> str:
        return f"{self.field_name} is populated"

    @override
    def validate_class(self, model_class: type[BaseModel]) -> None:
        Absent(self.field_name).validate_class(model_class)

    @override
    def eval(self, model_instance: BaseModel) -> bool:
        return not Absent(self.field_name).eval(model_instance)

    @override
    def negate(self) -> Condition:
        return Absent(self.field_name)

    @override
    def json_schema(self, model_class: type[BaseModel]) -> JsonDict:
        return {"required": [apply_alias(model_class, self.field_name)]}


@dataclass(frozen=True, slots=True)
class AllOf(Condition):
    """True when every one of `conditions` is."""

    conditions: tuple[Condition, ...]

    def __init__(self, *conditions: Condition) -> None:
        object.__setattr__(self, "conditions", conditions)

    def __str__(self) -> str:
        return " and ".join(str(c) for c in self.conditions)

    @override
    def validate_class(self, model_class: type[BaseModel]) -> None:
        for condition in self.conditions:
            condition.validate_class(model_class)

    @override
    def eval(self, model_instance: BaseModel) -> bool:
        return all(c.eval(model_instance) for c in self.conditions)

    @override
    def json_schema(self, model_class: type[BaseModel]) -> JsonDict:
        return {"allOf": [c.json_schema(model_class) for c in self.conditions]}


Decorator = Callable[[type[BaseModel]], type[BaseModel]]


def forbid_if(field_names: list[str], condition: Condition) -> Decorator:
    """The system's `forbid_if`, under a name unique to its fields.

    Each system decorator subclasses the model and registers its check as a
    Pydantic validator keyed by the constraint's name, which for every
    `forbid_if` is the same string, `@forbid_if`. A second `forbid_if` on one
    class therefore replaces the first one's validator: both still reach the
    JSON Schema, and only the outermost runs in Python. Naming each instance for
    its fields keeps both. `_create_internal` is the factory the system's own
    decorators use; `tests/test_constraints.py` asserts every stacked rule
    fires, so a change there fails loudly.
    """
    name = f"@forbid_if({', '.join(field_names)})"
    return ForbidIfConstraint._create_internal(name, field_names, condition).decorate


def require_if(field_names: list[str], condition: Condition) -> Decorator:
    """The system's `require_if`, uniquely named for the reason `forbid_if` is."""
    name = f"@require_if({', '.join(field_names)})"
    return RequireIfConstraint._create_internal(name, field_names, condition).decorate


# FIRM Database Technical Reference, section 7.3 "Acceptable Null Values". A
# field that is "required if applicable" and does not apply is written as an
# empty text field or -9999, because "a true Null value cannot be used for some
# fields" in the formats FEMA distributes. The service publishes them as-is.
NULL_TEXT = ""
NULL_NUMBER = -9999
NULL_ENCODING_QUOTE = (
    "Because of limitations in the GIS formats used by FEMA, a true Null value "
    "cannot be used for some fields. The value to use for “Null” fields for each "
    "field type is as follows: Text: Null (or “”, the empty string) Numeric: -9999"
)


def _is_null_encoding(value: Any) -> bool:
    if value is None or value == NULL_TEXT:
        return True
    # bool is an int; never read True as a number.
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and value == NULL_NUMBER
    )


def drop_null_encodings(data: Any) -> Any:
    """Treat the reference's own null encodings as absent properties.

    `STATIC_BFE: -9999` is how the FIRM Database writes "no static BFE"; read as a
    number, it is an elevation 9,999 feet below the datum. Collapsing JSON `null`,
    `""` and numeric `-9999` to "not populated" is what lets the populated-only-if
    rules mean anything, since those rules are about whether a value is there.

    Two neighbouring encodings are deliberately left alone. "Not populated"
    (`NP`, `-8888`, `U`), which section 7.3 lets a Project Officer approve, is a
    value that says something, and stays one. The string `"-9999"` in a text
    field is a numeric null written into the wrong type, and is rejected by the
    field's vocabulary rather than forgiven here.

    A validator rather than a constraint because it rewrites input instead of
    judging it.
    """
    if not isinstance(data, dict):
        return data
    properties = data.get("properties")
    if isinstance(properties, dict):
        return {
            **data,
            "properties": {
                k: v for k, v in properties.items() if not _is_null_encoding(v)
            },
        }
    return {k: v for k, v in data.items() if not _is_null_encoding(v)}
