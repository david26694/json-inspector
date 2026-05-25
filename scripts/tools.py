from __future__ import annotations
import json
from pathlib import Path


def _load(samples_path: Path, schemas_path: Path) -> tuple[dict, dict]:
    with samples_path.open() as f:
        samples = json.load(f)
    with schemas_path.open() as f:
        schemas = json.load(f)
    return samples, schemas


def _flatten_keys(obj: dict | list, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            full = f"{prefix}.{k}" if prefix else k
            paths.append(full)
            if isinstance(v, (dict, list)):
                paths.extend(_flatten_keys(v, full))
    elif isinstance(obj, list) and obj and isinstance(obj[0], (dict, list)):
        paths.extend(_flatten_keys(obj[0], prefix))
    return paths


def _get_nested(obj: dict, dotted_path: str) -> object:
    cur: object = obj
    for part in dotted_path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def list_tables(samples_path: Path, schemas_path: Path) -> list[str]:
    samples, _ = _load(samples_path, schemas_path)
    return list(samples.keys())


def list_fields(
    table_name: str,
    samples_path: Path,
    schemas_path: Path,
    source: str = "schema",
) -> list[str]:
    samples, schemas = _load(samples_path, schemas_path)
    if source == "schema":
        if table_name not in schemas:
            return [f"Table '{table_name}' not found in schemas"]
        return [f["name"] for f in schemas[table_name]]
    if table_name not in samples:
        return [f"Table '{table_name}' not found in samples"]
    return _flatten_keys(samples[table_name])


def get_field_info(
    table_name: str,
    field_name: str,
    samples_path: Path,
    schemas_path: Path,
) -> dict:
    _, schemas = _load(samples_path, schemas_path)
    if table_name not in schemas:
        return {"error": f"Table '{table_name}' not found"}
    match = [f for f in schemas[table_name] if f["name"] == field_name]
    if not match:
        return {"error": f"Field '{field_name}' not found in '{table_name}'"}
    return match[0]


def get_field_value(
    table_name: str,
    field_path: str,
    samples_path: Path,
    schemas_path: Path,
) -> object:
    samples, _ = _load(samples_path, schemas_path)
    if table_name not in samples:
        return {"error": f"Table '{table_name}' not found"}
    value = _get_nested(samples[table_name], field_path)
    if value is None:
        return {"error": f"Path '{field_path}' not found in sample for '{table_name}'"}
    return value


def find_field(
    field_name: str,
    samples_path: Path,
    schemas_path: Path,
) -> list[dict]:
    samples, schemas = _load(samples_path, schemas_path)
    needle = field_name.lower()
    results = []
    for table in schemas:
        schema_hits = {f["name"] for f in schemas[table] if needle in f["name"].lower()}
        sample_paths = set(_flatten_keys(samples.get(table, {})))
        sample_hits = {p for p in sample_paths if needle in p.lower()}
        all_hits = sorted(schema_hits | sample_hits)
        if all_hits:
            results.append({"table": table, "matching_fields": all_hits})
    return results or [{"message": f"No field matching '{field_name}' found"}]
