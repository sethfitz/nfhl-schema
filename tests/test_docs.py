"""The committed Markdown is what Overture's generator makes of the models."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def tree(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): p.read_text()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_regenerating_the_docs_changes_nothing(tmp_path: Path) -> None:
    out = tmp_path / "docs"
    subprocess.run(
        [str(ROOT / "scripts" / "generate-docs"), "--into", str(out)],
        check=True,
        capture_output=True,
    )
    fresh, committed = tree(out), tree(DOCS)
    assert "models/flood_hazard_zone.md" in committed
    assert fresh.keys() == committed.keys()
    for name in fresh:
        assert fresh[name] == committed[name], f"{name} is stale; run generate-docs"


def test_the_docs_mark_legacy_values() -> None:
    page = (DOCS / "models" / "types" / "study_typ.md").read_text()
    assert "`SFHAs WITH LOW FLOOD RISK` - Legacy:" in page
