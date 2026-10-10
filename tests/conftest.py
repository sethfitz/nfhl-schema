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


def modelled(table: str) -> Layer:
    return next(lyr for lyr in LAYERS if lyr.table == table)


def fixture_cases(name: str) -> list[dict[str, Any]]:
    payload = json.loads((FIXTURES / name).read_text())
    cases: list[dict[str, Any]] = payload["cases"]
    return cases


@pytest.fixture(scope="session")
def layer() -> Layer:
    """Flood Hazard Zones, which most of the tests are about."""
    return modelled("S_Fld_Haz_Ar")


@pytest.fixture(scope="session")
def bfe_layer() -> Layer:
    return modelled("S_BFE")


@pytest.fixture(scope="session")
def xs_layer() -> Layer:
    return modelled("S_XS")


@pytest.fixture(scope="session")
def profile_layer() -> Layer:
    return modelled("S_Profil_Basln")


@pytest.fixture(scope="session")
def station_layer() -> Layer:
    return modelled("S_Stn_Start")


@pytest.fixture(scope="session")
def mark_layer() -> Layer:
    return modelled("S_Riv_Mrk")


@pytest.fixture(scope="session")
def cases() -> list[dict[str, Any]]:
    return fixture_cases("flood_hazard_zones.json")


@pytest.fixture(scope="session")
def bfe_cases() -> list[dict[str, Any]]:
    return fixture_cases("base_flood_elevations.json")


@pytest.fixture(scope="session")
def xs_cases() -> list[dict[str, Any]]:
    return fixture_cases("cross_sections.json")


@pytest.fixture(scope="session")
def profile_cases() -> list[dict[str, Any]]:
    return fixture_cases("profile_baselines.json")


@pytest.fixture(scope="session")
def station_cases() -> list[dict[str, Any]]:
    return fixture_cases("station_starts.json")


@pytest.fixture(scope="session")
def mark_cases() -> list[dict[str, Any]]:
    return fixture_cases("river_marks.json")


@pytest.fixture(scope="session")
def water_cases() -> list[dict[str, Any]]:
    return fixture_cases("water_lines.json")


@pytest.fixture
def valid_feature(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """A fresh copy of a real feature that validates, to mutate in a test."""
    case = next(c for c in cases if c["name"] == "ae_static_bfe")
    feature: dict[str, Any] = copy.deepcopy(case["feature"])
    return feature
