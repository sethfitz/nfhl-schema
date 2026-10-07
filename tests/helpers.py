"""What the model tests and the rule-count tests both use."""

from __future__ import annotations

import json
import warnings
from typing import Any

from pydantic import ValidationError

from nfhl.legacy import LegacyValueWarning
from nfhl.models import FloodHazardZone


def validate(feature: dict[str, Any]) -> FloodHazardZone:
    # From JSON text, never a dict: the Feature envelope unwraps only in JSON mode.
    return FloodHazardZone.model_validate_json(json.dumps(feature))


def rejected_by(feature: dict[str, Any]) -> set[str]:
    """Wire field names (or rule names) that reject `feature`; empty if it is valid."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", LegacyValueWarning)
            validate(feature)
    except ValidationError as e:
        return {
            str(err["loc"][0]) if err["loc"] else err["msg"].split("`")[-2]
            for err in e.errors()
        }
    return set()


DUAL_NOT_T = "@forbid_if(dual_zone) [A, AE, AH, AO]"
DUAL_MISSING = "@require_if(dual_zone) [A, AE, AH, AO]"
DUAL_NOT_F = "@forbid_if(dual_zone) [X]"
DUAL_MISSING_X = "@require_if(dual_zone) [X]"
