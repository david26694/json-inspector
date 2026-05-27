from __future__ import annotations
import json
from pathlib import Path


def _load(data_sources_path: Path) -> dict:
    with data_sources_path.open() as f:
        return json.load(f)


def _flatten_field_paths(fields: list, prefix: str = "") -> list[str]:
    """Recursively flatten nested fields into dot-notation paths."""
    paths: list[str] = []
    for f in fields:
        full = f"{prefix}.{f['name']}" if prefix else f["name"]
        paths.append(full)
        if f.get("fields"):
            paths.extend(_flatten_field_paths(f["fields"], full))
    return paths


def _find_field_by_path(fields: list, dotted_path: str) -> dict | None:
    """Find a field dict by dot-notation path, traversing nested fields arrays."""
    parts = dotted_path.split(".", 1)
    for f in fields:
        if f["name"] == parts[0]:
            if len(parts) == 1:
                return f
            if f.get("fields"):
                return _find_field_by_path(f["fields"], parts[1])
    return None


def list_tables(data_sources_path: Path) -> list[str]:
    return list(_load(data_sources_path).keys())


def list_fields(
    table_name: str,
    data_sources_path: Path,
    source: str = "schema",
) -> list[str]:
    data = _load(data_sources_path)
    if table_name not in data:
        return [f"Table '{table_name}' not found"]
    fields = data[table_name]["fields"]
    if source == "schema":
        return [f["name"] for f in fields]
    return _flatten_field_paths(fields)


def get_field_info(
    table_name: str,
    field_name: str,
    data_sources_path: Path,
) -> dict:
    data = _load(data_sources_path)
    if table_name not in data:
        return {"error": f"Table '{table_name}' not found"}
    field = _find_field_by_path(data[table_name]["fields"], field_name)
    if field is None:
        return {"error": f"Field '{field_name}' not found in '{table_name}'"}
    return {k: v for k, v in field.items() if k != "fields"}


def get_field_value(
    table_name: str,
    field_path: str,
    data_sources_path: Path,
) -> object:
    data = _load(data_sources_path)
    if table_name not in data:
        return {"error": f"Table '{table_name}' not found"}
    field = _find_field_by_path(data[table_name]["fields"], field_path)
    if field is None or "example" not in field:
        return {"error": f"Path '{field_path}' not found in '{table_name}'"}
    return field["example"]


def find_field(
    field_name: str,
    data_sources_path: Path,
) -> list[dict]:
    data = _load(data_sources_path)
    needle = field_name.lower()
    results = []
    for table, table_data in data.items():
        all_paths = _flatten_field_paths(table_data["fields"])
        hits = sorted(p for p in all_paths if needle in p.lower())
        if hits:
            results.append({"table": table, "matching_fields": hits})
    return results or [{"message": f"No field matching '{field_name}' found"}]
