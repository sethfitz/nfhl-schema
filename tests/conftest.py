from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from nfhl.spec_source import LAYERS, Layer, SpecReader

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def reader() -> SpecReader:
    return SpecReader()


@pytest.fixture(scope="session")
def layer() -> Layer:
    (only,) = LAYERS
    return only


@pytest.fixture(scope="session")
def cases() -> list[dict[str, Any]]:
    payload = json.loads((FIXTURES / "flood_hazard_zones.json").read_text())
    cases: list[dict[str, Any]] = payload["cases"]
    return cases


@pytest.fixture
def valid_feature(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real feature that validates, to mutate in a test."""
    case = next(c for c in cases if c["name"] == "ae_static_bfe")
    feature: dict[str, Any] = copy.deepcopy(case["feature"])
    return feature
