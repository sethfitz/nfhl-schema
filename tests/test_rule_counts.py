"""Counting the rows that break each rule, every rule run on its own."""

from __future__ import annotations

from collections import Counter
from typing import Any

import pytest
from overture.schema.system.model_constraint import ModelConstraint

from nfhl import service
from nfhl.models import FloodHazardZone
from nfhl.rule_counts import (
    constraint_fields,
    fetch_groups,
    group_columns,
    judge,
    lone_space_sql,
    no_lone_space_sql,
    populated_sql,
    rule_fields,
    take_census,
)
from nfhl.spec_source import Layer, SpecReader

from .helpers import DUAL_MISSING, rejected_by

FIELDS = rule_fields(FloodHazardZone)


def rule(name: str) -> ModelConstraint:
    (found,) = [
        c
        for c in ModelConstraint.get_model_constraints(FloodHazardZone)
        if c.name == name
    ]
    return found


def test_a_rule_reads_its_own_fields_and_its_conditions() -> None:
    assert constraint_fields(rule(DUAL_MISSING)) == {"dual_zone", "ar_revert"}
    assert constraint_fields(rule("@forbid_if(zone_subty) [AH]")) == {
        "zone_subty",
        "fld_zone",
    }
    # require_any_true has no field list of its own to read; only conditions.
    assert constraint_fields(rule("@require_any_true(sfha_tf) [D, X]")) == {
        "fld_zone",
        "sfha_tf",
    }
    assert constraint_fields(rule("@forbid_if(len_unit)")) == {
        "len_unit",
        "static_bfe",
        "depth",
    }


def test_text_fields_are_grouped_by_value_and_numbers_by_being_set() -> None:
    assert set(FIELDS.by_value) == {
        "FLD_ZONE",
        "ZONE_SUBTY",
        "SFHA_TF",
        "V_DATUM",
        "LEN_UNIT",
        "VEL_UNIT",
        "AR_REVERT",
        "AR_SUBTRV",
        "DUAL_ZONE",
    }
    assert set(FIELDS.by_populated) == {
        "STATIC_BFE",
        "DEPTH",
        "VELOCITY",
        "BFE_REVERT",
        "DEP_REVERT",
    }


def test_a_value_its_field_limits_is_rejected_by_the_limit(
    valid_feature: dict[str, Any],
) -> None:
    # The limit is metadata on the field's type, beside the type itself.
    valid_feature["properties"]["DFIRM_ID"] = "1" * 40
    verdict = judge(FloodHazardZone, valid_feature["properties"])
    assert verdict.rejected_fields == {"DFIRM_ID"}


def test_judging_agrees_with_validation_on_every_real_feature(
    cases: list[dict[str, Any]],
) -> None:
    # Validation names the first rule that fails; judging must find it too, and
    # find nothing on a feature that validates.
    rules = {c.name for c in ModelConstraint.get_model_constraints(FloodHazardZone)}
    for case in cases:
        verdict = judge(FloodHazardZone, case["feature"]["properties"])
        if case["expect"] in rules:
            assert case["expect"] in verdict.broken, case["name"]
        elif case["expect"] is None:
            assert verdict.broken == set(), case["name"]
            assert verdict.rejected_fields == set(), case["name"]
        else:
            assert verdict.rejected_fields == {case["expect"]}, case["name"]


def test_a_row_breaking_two_rules_is_counted_against_both(
    valid_feature: dict[str, Any],
) -> None:
    # The 73 live AR_REVERT rows: validation names only one of the two.
    valid_feature["properties"].update(AR_REVERT="A", DUAL_ZONE=None)
    verdict = judge(FloodHazardZone, valid_feature["properties"])
    assert verdict.broken == {"@forbid_if(ar_revert)", DUAL_MISSING}
    assert len(rejected_by(valid_feature)) == 1


def test_a_value_its_field_rejects_blocks_the_rules_that_read_it(
    valid_feature: dict[str, Any],
) -> None:
    valid_feature["properties"]["AR_REVERT"] = "-9999"
    verdict = judge(FloodHazardZone, valid_feature["properties"])
    assert verdict.rejected_fields == {"AR_REVERT"}
    assert verdict.broken == set()
    assert "@forbid_if(ar_revert)" in verdict.blocked
    assert DUAL_MISSING in verdict.blocked
    assert "@forbid_if(bfe_revert)" not in verdict.blocked


@pytest.mark.parametrize(
    ("unit", "broken", "blocked"),
    [(None, True, False), ("", True, False), (" ", False, True)],
)
def test_a_lone_space_is_a_value_and_an_empty_string_a_null(
    valid_feature: dict[str, Any], unit: str | None, broken: bool, blocked: bool
) -> None:
    valid_feature["properties"].update(VELOCITY=2.0, VEL_UNIT=unit)
    verdict = judge(FloodHazardZone, valid_feature["properties"])
    assert ("@require_if(vel_unit)" in verdict.broken) is broken
    assert ("@require_if(vel_unit)" in verdict.blocked) is blocked


# An X zone outside the SFHA, with the subtype X requires.
MINIMAL_X = {
    "FLD_ZONE": "X",
    "ZONE_SUBTY": "AREA OF MINIMAL FLOOD HAZARD",
    "SFHA_TF": "F",
}


def group(count: int, **values: Any) -> dict[str, Any]:
    """A group of FIELDS that breaks no rule unless `values` say otherwise."""
    base = dict.fromkeys(FIELDS.by_value) | MINIMAL_X
    return base | dict.fromkeys(FIELDS.by_populated, False) | values | {"count": count}


def test_a_census_counts_each_rule_and_any_rule() -> None:
    groups = [
        group(5),
        group(3, BFE_REVERT=True),
        group(2, BFE_REVERT=True, DEP_REVERT=True),
        group(7, DEP_REVERT=True, AR_REVERT="-9999"),
    ]
    census = take_census(FloodHazardZone, groups)
    counts = {r.rule: (r.broken, r.blocked) for r in census.rules}
    assert census.total == 17
    assert counts["@forbid_if(bfe_revert)"] == (5, 0)
    assert counts["@forbid_if(dep_revert)"] == (9, 0)
    assert counts["@forbid_if(ar_revert)"] == (0, 7)
    assert (census.any_broken, census.any_blocked) == (12, 7)
    only_bfe = take_census(FloodHazardZone, groups, lambda r: "bfe_revert" in r)
    assert [r.rule for r in only_bfe.rules] == ["@forbid_if(bfe_revert)"]
    assert (only_bfe.any_broken, only_bfe.any_blocked) == (5, 0)


def fold(value: Any) -> Any:
    """A value as the service's grouping compares it: case and trailing blanks
    ignored."""
    return value.rstrip().lower() if isinstance(value, str) else value


class FoldingService:
    """A layer behind the service's collation: grouping folds case and trailing
    blanks, and `where` sees lone spaces, as `LIKE ' '` does."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def selected(self, where: str) -> list[dict[str, Any]]:
        tests = {lone_space_sql(f): f for f in FIELDS.by_value}
        negated = {no_lone_space_sql(f): f for f in FIELDS.by_value}
        rows = self.rows
        for clause in where.split(" AND "):
            if clause in tests:
                rows = [r for r in rows if r[tests[clause]] == " "]
            elif clause in negated:
                rows = [r for r in rows if r[negated[clause]] != " "]
            else:
                assert clause == "1=1", clause
        return rows

    def row_count(self, layer_id: int, where: str = "1=1") -> int:
        return len(self.selected(where))

    def grouped(
        self, layer_id: int, group_by: list[str], where: str = "1=1"
    ) -> list[dict[str, Any]]:
        def column(row: dict[str, Any], entry: str) -> Any:
            for f in FIELDS.by_populated:
                if entry == populated_sql(f):
                    return int(row[f] is not None and row[f] != -9999)
            return row[entry]

        shown: dict[tuple[Any, ...], dict[str, Any]] = {}
        counts: Counter[tuple[Any, ...]] = Counter()
        for row in self.selected(where):
            values = {e: column(row, e) for e in group_by}
            key = tuple(fold(v) for v in values.values())
            shown.setdefault(key, values)  # the first variant met stands for all
            counts[key] += 1
        return [shown[k] | {"n": n} for k, n in counts.items()]


def row(**values: Any) -> dict[str, Any]:
    fields = (*FIELDS.by_value, *FIELDS.by_populated)
    return dict.fromkeys(fields) | MINIMAL_X | values


def test_fetching_groups_keeps_a_lone_space_apart_from_an_empty_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        # A lone space met first, so the folded group would show it for all four.
        row(VELOCITY=2.0, VEL_UNIT=" "),
        row(VELOCITY=2.0, VEL_UNIT=""),
        row(VELOCITY=2.0, VEL_UNIT=""),
        row(VELOCITY=2.0, VEL_UNIT=""),
        row(VELOCITY=-9999, VEL_UNIT=" ", V_DATUM=" "),
        row(LEN_UNIT="Feet", STATIC_BFE=10.0),
    ]
    fake = FoldingService(rows)
    monkeypatch.setattr(service, "row_count", fake.row_count)
    monkeypatch.setattr(service, "grouped", fake.grouped)
    groups = fetch_groups(28, FIELDS)
    assert sum(g["count"] for g in groups) == len(rows)
    blanks = Counter(
        {(g["VEL_UNIT"], g["V_DATUM"], g["VELOCITY"]): g["count"] for g in groups}
    )
    assert blanks == {
        (" ", None, True): 1,
        ("", None, True): 3,
        (" ", " ", False): 1,
        (None, None, False): 1,
    }
    census = take_census(FloodHazardZone, groups, lambda r: "vel_unit" in r)
    assert (census.any_broken, census.any_blocked) == (3, 2)


def test_a_folded_grouping_would_misjudge_the_blanks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The did-happen control for the test above: without the split, the lone
    # space stands for its group, and three nulls are judged as values.
    rows = [row(VELOCITY=2.0, VEL_UNIT=" "), *[row(VELOCITY=2.0, VEL_UNIT="")] * 3]
    fake = FoldingService(rows)
    (folded,) = fake.grouped(28, group_columns(FIELDS))
    assert (folded["VEL_UNIT"], folded["n"]) == (" ", 4)


# -- the snapshot --------------------------------------------------------------


@pytest.fixture(scope="module")
def groups(reader: SpecReader, layer: Layer) -> list[dict[str, Any]]:
    _, groups = reader.rule_groups(layer)
    return groups


def test_the_snapshot_groups_every_field_the_rules_read(
    reader: SpecReader, layer: Layer
) -> None:
    # A new rule reading a new field needs a new snapshot.
    fields, _ = reader.rule_groups(layer)
    assert fields == FIELDS


def folded_marginal(rows: list[dict[str, Any]], *fields: str) -> Counter[Any]:
    """Rows per value of `fields`, compared as the service's grouping compares."""
    counts: Counter[Any] = Counter()
    for r in rows:
        counts[tuple(fold(r[f]) for f in fields)] += r["count"]
    return counts


def test_the_groups_agree_with_every_other_count_in_the_snapshot(
    reader: SpecReader, layer: Layer, groups: list[dict[str, Any]]
) -> None:
    # Taken in separate queries, so a layer that changed between them would
    # show here: every field's and every pair's counts must be the groups'.
    observed = reader.observed(layer)

    assert sum(g["count"] for g in groups) == observed["total"]
    for field in FIELDS.by_value:
        values = [
            {field: v["value"], "count": v["count"]} for v in observed["fields"][field]
        ]
        assert folded_marginal(groups, field) == folded_marginal(values, field), field
    for pair, rows in observed["combinations"].items():
        fields = pair.split(",")
        assert folded_marginal(groups, *fields) == folded_marginal(rows, *fields), pair


def test_the_census_reproduces_the_counts_spec_readme_records(
    groups: list[dict[str, Any]],
) -> None:

    def broken(*texts: str) -> int:
        census = take_census(
            FloodHazardZone, groups, lambda r: any(t in r for t in texts)
        )
        return census.any_broken

    assert broken("bfe_revert") == 12_732
    assert broken("dep_revert") == 17_914
    assert broken("bfe_revert", "dep_revert") == 18_177
    assert broken("@forbid_if(ar_revert)") + broken("@forbid_if(ar_subtrv)") == 79
    assert broken("dual_zone") == 73
    assert broken("@forbid_if(zone_subty)", "@require_if(zone_subty)") == 694
    assert broken("sfha_tf") == 17
    assert broken("@forbid_if(v_datum)") == 16_571
    assert broken("@forbid_if(len_unit)") == 1_468
    # 8,638 velocities without a unit, less the 1,257 lone spaces.
    assert broken("@require_if(vel_unit)") == 7_381
