"""Queries against FEMA's NFHL map service.

`scripts/snapshot-spec` records what these return; `scripts/count-broken-rules
--live` asks the service again instead of reading that record.
"""

from __future__ import annotations

import json
import subprocess
import urllib.parse
from typing import Any

SERVICE = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer"
TIMEOUT = 600


def fetch(url: str, params: dict[str, str] | None = None) -> bytes:
    """GET with curl.

    curl rather than urllib because fema.gov's CDN answers 403 to urllib's
    User-Agent, and to a spoofed browser one, while serving curl's own. Checked
    2026-10-04; do not "fix" a 403 here by impersonating a browser.
    """
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    result = subprocess.run(
        ["curl", "-fsSL", "--max-time", str(TIMEOUT), url],
        check=True,
        capture_output=True,
    )
    return result.stdout


def fetch_json(url: str, params: dict[str, str]) -> Any:
    payload = json.loads(fetch(url, params))
    if isinstance(payload, dict) and "error" in payload:
        raise RuntimeError(f"{url}: {payload['error']}")
    return payload


def query_url(layer_id: int) -> str:
    return f"{SERVICE}/{layer_id}/query"


def row_count(layer_id: int, where: str = "1=1") -> int:
    payload = fetch_json(
        query_url(layer_id), {"where": where, "returnCountOnly": "true", "f": "json"}
    )
    count: int = payload["count"]
    return count


def grouped(
    layer_id: int, group_by: list[str], where: str = "1=1"
) -> list[dict[str, Any]]:
    """Row counts per distinct combination of `group_by` among the rows `where`
    selects, each count as `n`.

    An entry of `group_by` may be a SQL expression rather than a field name; the
    service names its column `Expr<k>`, which `grouped` renames to the
    expression itself, so every entry of `group_by` is a key of every row. A
    field's column must match its name, ignoring case.
    """
    stats = fetch_json(
        query_url(layer_id),
        {
            "where": where,
            "outStatistics": json.dumps(
                [
                    {
                        "statisticType": "count",
                        "onStatisticField": "OBJECTID",
                        "outStatisticFieldName": "n",
                    }
                ]
            ),
            "groupByFieldsForStatistics": ",".join(group_by),
            "f": "json",
        },
    )
    if stats.get("exceededTransferLimit"):
        raise RuntimeError(f"layer {layer_id}: grouping by {group_by} was truncated")
    # The response lists its columns in `group_by` order, then `n`.
    columns = [f["name"] for f in stats["fields"]]
    if len(columns) != len(group_by) + 1:
        raise RuntimeError(f"layer {layer_id}: expected {group_by}, got {columns}")
    rename = {columns[-1]: "n"}
    for column, entry in zip(columns, group_by, strict=False):
        if entry.isidentifier() and column.lower() != entry.lower():
            raise RuntimeError(f"layer {layer_id}: expected {entry}, got {column}")
        rename[column] = entry
    return [
        {rename[k]: v for k, v in f["attributes"].items()} for f in stats["features"]
    ]
