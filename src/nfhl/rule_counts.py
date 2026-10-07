"""Count the rows of a layer that break each of its model's rules, every rule judged
on its own.

Validation cannot give these counts. Each constraint is its own
`model_validator`, and pydantic stops at the first that raises, so a feature
breaking three rules names one, and a count per rule read from validation errors
undercounts every rule but the first to run. Here every rule runs against every
row.

A rule runs only on rows whose fields it reads all validate. A row whose
`AR_REVERT` is `-9999` written as text is rejected by the field's vocabulary,
and validation never reaches the rules that read `AR_REVERT`; the row counts
against those rules as `blocked`, not `broken`.

The rows come grouped, not one by one: a row of the census is a distinct
combination of the values the rules read, with the number of rows that hold it,
taken from the service's grouped statistics (`fetch_groups`). A numeric field,
and a text field with no vocabulary (`S_XS`'s `XS_LTR`, a letter per cross
section), is grouped by whether it is populated, since that is all any rule asks
of one.
`snapshot-spec` records the groups in `spec/service/observed/`; `--live` on
`scripts/count-broken-rules` asks the service again.

The service groups text ignoring case and trailing blanks (spec/README.md, "Read
a count as the service's"), so a group stands for every variant of its value.
For trailing blanks that matters: `""` is a null and a lone space is a value
the vocabulary rejects, and folded together a velocity without a `VEL_UNIT`
would count as breaking its rule rather than blocked. So the rows are first
split by which fields hold a lone space, which `LIKE ' '` can see, and each
part grouped on its own. Case is still folded: the service shows one variant
of each group of case variants, and the group is judged as that variant.
"""

from __future__ import annotations

import dataclasses
import functools
import json
import types
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any, Union, get_args, get_origin

from overture.schema.system.model_constraint import Condition, ModelConstraint
from pydantic import BaseModel, TypeAdapter, ValidationError

from . import service
from .constraints import NULL_NUMBER, Absent, Populated, drop_null_encodings

# Stand in for any populated value of a field grouped by whether it is set: no
# rule reads the value of a number or of free text.
POPULATED_NUMBER = 1
POPULATED_TEXT = "x"


@dataclass(frozen=True, slots=True)
class RuleFields:
    """The wire names of the fields a model's rules read, by how they are grouped."""

    by_value: tuple[str, ...]  # vocabulary fields: the rules compare their values
    by_populated: tuple[str, ...]  # numeric fields: the rules ask only if set
    # Text fields without a vocabulary: the rules ask only if set.
    by_text_populated: tuple[str, ...] = ()


def populated_sql(field: str) -> str:
    """SQL that is 1 where numeric `field` is populated, 0 where it is a null."""
    return f"CASE WHEN {field} IS NULL OR {field} = {NULL_NUMBER} THEN 0 ELSE 1 END"


def text_populated_sql(field: str) -> str:
    """SQL that is 1 where text `field` is populated, 0 where it is a null.

    `= ''` also matches a lone space, which is a value; `fetch_groups` splits
    the lone spaces off first.
    """
    return f"CASE WHEN {field} IS NULL OR {field} = '' THEN 0 ELSE 1 END"


def lone_space_sql(field: str) -> str:
    return f"{field} LIKE ' '"


def no_lone_space_sql(field: str) -> str:
    return f"({field} IS NULL OR {field} NOT LIKE ' ')"


def group_columns(fields: RuleFields) -> list[str]:
    """What `fetch_groups` groups by: each vocabulary field, and the populated
    SQL of each other field."""
    return [
        *fields.by_value,
        *(populated_sql(f) for f in fields.by_populated),
        *(text_populated_sql(f) for f in fields.by_text_populated),
    ]


def lone_space_parts(
    layer_id: int, fields: tuple[str, ...]
) -> list[tuple[frozenset[str], str]]:
    """The layer's rows split by which of `fields` hold a lone space.

    Each part is the set of fields that do and the `where` clause selecting it;
    parts with no rows are left out. One count per part and field: the rows
    without a lone space are the part's count less the rows with one.
    """
    parts: list[tuple[frozenset[str], list[str], int]] = [
        (frozenset(), [], service.row_count(layer_id))
    ]
    for field in fields:
        split = []
        for spaced, clauses, n in parts:
            with_space = [*clauses, lone_space_sql(field)]
            k = service.row_count(layer_id, " AND ".join(with_space))
            if k:
                split.append((spaced | {field}, with_space, k))
            if n - k:
                split.append((spaced, [*clauses, no_lone_space_sql(field)], n - k))
        parts = split
    return [(spaced, " AND ".join(clauses) or "1=1") for spaced, clauses, _ in parts]


def fetch_groups(layer_id: int, fields: RuleFields) -> list[dict[str, Any]]:
    """Rows per distinct combination of `fields`, from the service.

    Each group maps every field to its value, or for a numeric field to whether
    it is populated, and `count` to its rows. A layer whose model has no rules
    is one group of every row.
    """
    if not group_columns(fields):
        return [{"count": service.row_count(layer_id)}]
    groups = []
    texts = (*fields.by_value, *fields.by_text_populated)
    for spaced, where in lone_space_parts(layer_id, texts):
        for row in service.grouped(layer_id, group_columns(fields), where):
            group = {f: row[f] for f in fields.by_value}
            group |= {f: bool(row[populated_sql(f)]) for f in fields.by_populated}
            group |= {
                f: bool(row[text_populated_sql(f)]) for f in fields.by_text_populated
            }
            # The group may show either blank; the part says it is a lone space,
            # which is a value.
            for f in spaced:
                group[f] = " " if f in fields.by_value else True
            groups.append({**group, "count": row["n"]})
    return sorted(groups, key=lambda g: (-g["count"], json.dumps(g)))


def leaf_conditions(condition: Condition) -> Iterator[Condition]:
    """Every condition under `condition` that reads a field, through `Not`,
    `AllOf` and the like."""
    for f in dataclasses.fields(condition):  # type: ignore[arg-type]
        value = getattr(condition, f.name)
        if f.name == "field_name":
            yield condition
        elif isinstance(value, Condition):
            yield from leaf_conditions(value)
        elif isinstance(value, tuple):
            for item in value:
                if isinstance(item, Condition):
                    yield from leaf_conditions(item)


def constraint_conditions(constraint: ModelConstraint) -> list[Condition]:
    conditions = list(getattr(constraint, "conditions", ()))
    if (condition := getattr(constraint, "condition", None)) is not None:
        conditions.append(condition)
    return conditions


def constraint_fields(constraint: ModelConstraint) -> frozenset[str]:
    """The Python names of the fields `constraint` reads."""
    names = set(getattr(constraint, "field_names", ()))
    for condition in constraint_conditions(constraint):
        names.update(leaf.field_name for leaf in leaf_conditions(condition))  # type: ignore[attr-defined]
    return frozenset(names)


def _holds(annotation: Any, kind: type) -> bool:
    """Whether a field typed `annotation` holds a `kind`, through `Annotated` and
    unions."""
    if get_origin(annotation) in (Union, types.UnionType):
        return any(_holds(a, kind) for a in get_args(annotation))
    if get_origin(annotation) is Annotated:
        return _holds(get_args(annotation)[0], kind)
    return isinstance(annotation, type) and issubclass(annotation, kind)


def check_set_fields_are_only_asked_if_set(
    model: type[BaseModel], set_fields: set[str]
) -> None:
    """Raise if a rule asks a field grouped by whether it is set for more than
    that, which `judge` cannot answer: it substitutes `POPULATED_NUMBER` or
    `POPULATED_TEXT` for any value."""
    for constraint in ModelConstraint.get_model_constraints(model):
        for condition in constraint_conditions(constraint):
            for leaf in leaf_conditions(condition):
                name = leaf.field_name  # type: ignore[attr-defined]
                if name in set_fields and not isinstance(leaf, Absent | Populated):
                    raise ValueError(
                        f"{constraint.name} reads {name} with "
                        f"{type(leaf).__name__}, not only whether it is set"
                    )


def rule_fields(model: type[BaseModel]) -> RuleFields:
    names = set().union(
        *(constraint_fields(c) for c in ModelConstraint.get_model_constraints(model))
    )
    by_value: list[str] = []
    by_populated: list[str] = []
    by_text_populated: list[str] = []
    for name, info in model.model_fields.items():
        if name not in names:
            continue
        wire = info.alias or name
        if _holds(info.annotation, Enum):
            by_value.append(wire)
        elif _holds(info.annotation, str):
            by_text_populated.append(wire)
        else:
            by_populated.append(wire)
    set_fields = {
        name
        for name, info in model.model_fields.items()
        if (info.alias or name) in {*by_populated, *by_text_populated}
    }
    check_set_fields_are_only_asked_if_set(model, set_fields)
    return RuleFields(tuple(by_value), tuple(by_populated), tuple(by_text_populated))


@functools.cache
def _adapter(model: type[BaseModel], name: str) -> TypeAdapter[Any]:
    info = model.model_fields[name]
    if info.metadata:
        return TypeAdapter(Annotated[info.annotation, *info.metadata])
    return TypeAdapter(info.annotation)


@dataclass(frozen=True, slots=True)
class Judgement:
    """What one row does to a model's rules."""

    # wire names whose own type rejects the value; tests check judge's field
    # validation against pydantic's through it
    rejected_fields: frozenset[str]
    broken: frozenset[str]  # rule names
    blocked: frozenset[str]  # rules a rejected field keeps from running


def judge(model: type[BaseModel], properties: dict[str, Any]) -> Judgement:
    """Run every rule of `model` on `properties` (wire names), each on its own."""
    present = drop_null_encodings(properties)
    values, rejected = {}, set()
    for name, info in model.model_fields.items():
        wire = info.alias or name
        if wire not in present:
            continue
        try:
            values[wire] = _adapter(model, name).validate_python(present[wire])
        except ValidationError:
            rejected.add(name)
    instance = model.model_construct(**values)
    broken, blocked = set(), set()
    for constraint in ModelConstraint.get_model_constraints(model):
        if constraint_fields(constraint) & rejected:
            blocked.add(constraint.name)
            continue
        try:
            constraint.validate_instance(instance)
        except ValueError:
            broken.add(constraint.name)
    return Judgement(
        frozenset(model.model_fields[n].alias or n for n in rejected),
        frozenset(broken),
        frozenset(blocked),
    )


@dataclass(frozen=True, slots=True)
class RuleCount:
    """Rows broken and blocked for one rule: blocked rows never ran it, because
    a field it reads was rejected."""

    rule: str
    broken: int
    blocked: int


@dataclass(frozen=True, slots=True)
class Census:
    """Rows per rule of one layer, from its groups."""

    total: int
    rules: tuple[RuleCount, ...]  # in the model's own order
    any_broken: int  # rows breaking at least one rule
    any_blocked: int  # rows at least one rule never reaches


def properties_of(group: dict[str, Any], fields: RuleFields) -> dict[str, Any]:
    """A group as the properties of one row that holds it."""
    properties = {f: group[f] for f in fields.by_value}
    properties |= {f: POPULATED_NUMBER for f in fields.by_populated if group[f]}
    properties |= {f: POPULATED_TEXT for f in fields.by_text_populated if group[f]}
    return properties


def take_census(
    model: type[BaseModel],
    groups: list[dict[str, Any]],
    select: Callable[[str], bool] = lambda rule: True,
) -> Census:
    """Count each rule `select` accepts, then any of them."""
    fields = rule_fields(model)
    names = [
        c.name for c in ModelConstraint.get_model_constraints(model) if select(c.name)
    ]
    broken = dict.fromkeys(names, 0)
    blocked = dict.fromkeys(names, 0)
    any_broken = any_blocked = 0
    for group in groups:
        n = group["count"]
        verdict = judge(model, properties_of(group, fields))
        broken_here = verdict.broken & broken.keys()
        blocked_here = verdict.blocked & blocked.keys()
        for rule in broken_here:
            broken[rule] += n
        for rule in blocked_here:
            blocked[rule] += n
        if broken_here:
            any_broken += n
        if blocked_here:
            any_blocked += n
    return Census(
        total=sum(g["count"] for g in groups),
        rules=tuple(RuleCount(r, broken[r], blocked[r]) for r in names),
        any_broken=any_broken,
        any_blocked=any_blocked,
    )
