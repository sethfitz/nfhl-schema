"""The entry point makes the model visible to Overture's tooling."""

from __future__ import annotations

import shutil
import subprocess

from overture.schema.system.discovery import discover_models

from nfhl.models import FloodHazardZone


def test_discovery_finds_the_model_through_the_entry_point() -> None:
    found = discover_models()
    assert FloodHazardZone in found.values()


def test_overture_codegen_lists_the_model() -> None:
    codegen = shutil.which("overture-codegen")
    assert codegen is not None, "overture-codegen not installed; run uv sync --dev"
    listed = subprocess.run(
        [codegen, "list"], check=True, capture_output=True, text=True
    ).stdout.split()
    assert "FloodHazardZone" in listed
