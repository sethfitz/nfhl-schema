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
from dataclasses import dataclass, field
from typing import Any, override

from overture.schema.system.model_constraint import (
    Condition,
    ForbidIfConstraint,
    RequireAnyTrueConstraint,
    RequireIfConstraint,
    apply_alias,
)
from pydantic import BaseModel
from pydantic.config import JsonDict
from pydantic_core import to_jsonable_python


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


def spoken(values: tuple[Any, ...], conjunction: str) -> str:
    """`A`, `A or B`, `A, B or C`: values as the reference docs read them."""
    shown = [str(getattr(v, "value", v)) for v in values]
    if len(shown) == 1:
        return shown[0]
    return f"{', '.join(shown[:-1])} {conjunction} {shown[-1]}"


@dataclass(frozen=True, slots=True)
class OneOf(Condition):
    """True when `field_name` holds one of `values`; false when it holds none.

    The system's `FieldEqCondition` takes one value, and its JSON Schema does
    not require the property, so an absent field would satisfy it there while
    failing it in Python. This one requires the property in both.
    """

    field_name: str
    values: tuple[Any, ...]
    # How the reference docs read the condition, when listing `values` would
    # say less than naming the rule they come from.
    label: str | None = field(default=None, compare=False)

    def __str__(self) -> str:
        if self.label is not None:
            return self.label
        return f"{self.field_name} is {spoken(self.values, 'or')}"

    @override
    def validate_class(self, model_class: type[BaseModel]) -> None:
        Absent(self.field_name).validate_class(model_class)
        if not self.values:
            raise ValueError(f"OneOf({self.field_name!r}) lists no values")

    @override
    def eval(self, model_instance: BaseModel) -> bool:
        if Absent(self.field_name).eval(model_instance):
            return False
        return getattr(model_instance, self.field_name) in self.values

    @override
    def json_schema(self, model_class: type[BaseModel]) -> JsonDict:
        alias = apply_alias(model_class, self.field_name)
        return {
            "required": [alias],
            "properties": {
                alias: {"enum": [to_jsonable_python(v) for v in self.values]}
            },
        }


@dataclass(frozen=True, slots=True)
class NoneOf(Condition):
    """True when `field_name` holds none of `values`, or nothing. Negates `OneOf`.

    Its own class rather than `~OneOf(...)` so the rule reads as a sentence in
    the generated reference.
    """

    field_name: str
    values: tuple[Any, ...]

    def __str__(self) -> str:
        if len(self.values) == 2:
            return f"{self.field_name} is neither {spoken(self.values, 'nor')}"
        return f"{self.field_name} is not {spoken(self.values, 'or')}"

    @override
    def validate_class(self, model_class: type[BaseModel]) -> None:
        OneOf(self.field_name, self.values).validate_class(model_class)

    @override
    def eval(self, model_instance: BaseModel) -> bool:
        return not OneOf(self.field_name, self.values).eval(model_instance)

    @override
    def negate(self) -> Condition:
        return OneOf(self.field_name, self.values)

    @override
    def json_schema(self, model_class: type[BaseModel]) -> JsonDict:
        return {"not": OneOf(self.field_name, self.values).json_schema(model_class)}


Decorator = Callable[[type[BaseModel]], type[BaseModel]]


def _rule_name(kind: str, field_names: list[str], qualifier: str | None) -> str:
    name = f"@{kind}({', '.join(field_names)})"
    return f"{name} [{qualifier}]" if qualifier else name


def forbid_if(
    field_names: list[str], condition: Condition, qualifier: str | None = None
) -> Decorator:
    """The system's `forbid_if`, under a name unique to its fields.

    Each system decorator subclasses the model and registers its check as a
    Pydantic validator keyed by the constraint's name, which for every
    `forbid_if` is the same string, `@forbid_if`. A second `forbid_if` on one
    class therefore replaces the first one's validator: both still reach the
    JSON Schema, and only the outermost runs in Python. Naming each instance for
    its fields keeps both. `_create_internal` is the factory the system's own
    decorators use; `tests/test_constraints.py` asserts every stacked rule
    fires, so a change there fails loudly.

    Two rules on the same fields need a `qualifier` to tell them apart; it is
    appended to the name, which is what a validation error reports.
    """
    name = _rule_name("forbid_if", field_names, qualifier)
    return ForbidIfConstraint._create_internal(name, field_names, condition).decorate


def require_if(
    field_names: list[str], condition: Condition, qualifier: str | None = None
) -> Decorator:
    """The system's `require_if`, uniquely named for the reason `forbid_if` is."""
    name = _rule_name("require_if", field_names, qualifier)
    return RequireIfConstraint._create_internal(name, field_names, condition).decorate


def require_any_true(
    field_names: list[str], *conditions: Condition, qualifier: str | None = None
) -> Decorator:
    """The system's `require_any_true`, uniquely named for the reason `forbid_if`
    is. `field_names` only names the rule.

    The rule for a required field: `forbid_if` and `require_if` accept only
    optional ones. "When A, then B" is "not A, or B".
    """
    name = _rule_name("require_any_true", field_names, qualifier)
    return RequireAnyTrueConstraint._create_internal(name, *conditions).decorate


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
