"""What the model tests and the rule-count tests both use."""

from __future__ import annotations

import copy
import json
import warnings
from typing import Any

from pydantic import BaseModel, ValidationError

from nfhl.legacy import LegacyValueWarning
from nfhl.models import FloodHazardZone


def validate_as[M: BaseModel](model: type[M], feature: dict[str, Any]) -> M:
    # From JSON text, never a dict: the Feature envelope unwraps only in JSON mode.
    return model.model_validate_json(json.dumps(feature))


def validate(feature: dict[str, Any]) -> FloodHazardZone:
    return validate_as(FloodHazardZone, feature)


def rejected_by(
    feature: dict[str, Any], model: type[BaseModel] = FloodHazardZone
) -> set[str]:
    """Wire field names (or rule names) that reject `feature`; empty if it is valid."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", LegacyValueWarning)
            validate_as(model, feature)
    except ValidationError as e:
        return {
            str(err["loc"][0]) if err["loc"] else err["msg"].split("`")[-2]
            for err in e.errors()
        }
    return set()


def legacy_warnings_by(
    feature: dict[str, Any], model: type[BaseModel] = FloodHazardZone
) -> list[str]:
    """The LegacyValueWarning messages validating `feature` raises."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        validate_as(model, feature)
    return [
        str(w.message) for w in caught if issubclass(w.category, LegacyValueWarning)
    ]


def fixture_feature(cases: list[dict[str, Any]], name: str) -> dict[str, Any]:
    """A fresh copy of the named fixture case's feature, to mutate in a test."""
    case = next(c for c in cases if c["name"] == name)
    feature: dict[str, Any] = copy.deepcopy(case["feature"])
    return feature


DUAL_NOT_T = "@forbid_if(dual_zone) [A, AE, AH, AO]"
DUAL_MISSING = "@require_if(dual_zone) [A, AE, AH, AO]"
DUAL_NOT_F = "@forbid_if(dual_zone) [X]"
DUAL_MISSING_X = "@require_if(dual_zone) [X]"
