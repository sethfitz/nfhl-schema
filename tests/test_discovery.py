"""The entry point makes the model visible to Overture's tooling."""

from __future__ import annotations

import shutil
import subprocess

from overture.schema.system.discovery import ModelKey, discover_models

from nfhl.models import (
    BaseFloodElevation,
    CrossSection,
    FloodHazardZone,
    ProfileBaseline,
    RiverMark,
    StationStart,
)
from nfhl.tags import nfhl_provider


def test_discovery_finds_the_model_through_the_entry_point() -> None:
    found = discover_models()
    assert {
        FloodHazardZone,
        BaseFloodElevation,
        CrossSection,
        ProfileBaseline,
        StationStart,
        RiverMark,
    } <= set(found.values())


def test_overture_codegen_lists_the_model() -> None:
    codegen = shutil.which("overture-codegen")
    assert codegen is not None, "overture-codegen not installed; run uv sync --dev"
    listed = subprocess.run(
        [codegen, "list"], check=True, capture_output=True, text=True
    ).stdout.split()
    assert {
        "FloodHazardZone",
        "BaseFloodElevation",
        "CrossSection",
        "ProfileBaseline",
        "StationStart",
        "RiverMark",
    } <= set(listed)


def test_the_tag_provider_tags_the_model_nfhl() -> None:
    tagged = {k.name: k.tags for k in discover_models()}
    assert "nfhl" in tagged["nfhl_flood_hazard_zone"]
    assert "nfhl" in tagged["nfhl_base_flood_elevation"]
    assert "nfhl" in tagged["nfhl_cross_section"]
    assert "nfhl" in tagged["nfhl_profile_baseline"]
    assert "nfhl" in tagged["nfhl_station_start"]
    assert "nfhl" in tagged["nfhl_river_mark"]


def test_the_tag_provider_leaves_other_packages_alone() -> None:
    # Only this package's models are installed here, so discovery cannot show it.
    other = ModelKey("place", "my_schema:Place", frozenset())
    assert nfhl_provider([], other, set()) == set()
