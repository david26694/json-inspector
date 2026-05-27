# /// script
# dependencies = ["mcp>=1.0"]
# ///
"""MCP server entry point for json-inspector plugin.

Reads JSON_INSPECTOR_SAMPLES and JSON_INSPECTOR_SCHEMAS env vars for file paths.
Run with: uv run scripts/server.py
"""
from __future__ import annotations
import argparse as _argparse
import os
import os as _os
import sys
import sys as _sys
from pathlib import Path
from pathlib import Path as _Path


def _validate_env() -> tuple[str, str]:
    errors = []
    samples = _os.environ.get("JSON_INSPECTOR_SAMPLES")
    schemas = _os.environ.get("JSON_INSPECTOR_SCHEMAS")

    if not samples:
        errors.append("JSON_INSPECTOR_SAMPLES environment variable is not set")
    elif not _Path(samples).exists():
        errors.append(f"JSON_INSPECTOR_SAMPLES file not found: {samples}")

    if not schemas:
        errors.append("JSON_INSPECTOR_SCHEMAS environment variable is not set")
    elif not _Path(schemas).exists():
        errors.append(f"JSON_INSPECTOR_SCHEMAS file not found: {schemas}")

    if errors:
        for msg in errors:
            print(f"json-inspector: {msg}", file=_sys.stderr)
        _sys.exit(1)

    return samples, schemas


_parser = _argparse.ArgumentParser(add_help=False)
_parser.add_argument("--validate-only", action="store_true")
_args, _ = _parser.parse_known_args()

_samples_path, _schemas_path = _validate_env()

if _args.validate_only:
    print("json-inspector: configuration OK", file=_sys.stderr)
    _sys.exit(0)

# Allow importing tools.py from the same scripts/ directory
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from tools import find_field, get_field_info, get_field_value, list_fields, list_tables

_samples = Path(_samples_path)
_schemas = Path(_schemas_path)

mcp = FastMCP("json-inspector")


@mcp.tool()
def list_tables_tool() -> list[str]:
    """Return all available table names (fully-qualified IDs)."""
    return list_tables(_samples, _schemas)


@mcp.tool()
def list_fields_tool(table_name: str, source: str = "schema") -> list[str]:
    """List fields for a table.

    Args:
        table_name: Table name as returned by list_tables_tool.
        source: 'schema' for typed top-level fields (default),
                'sample' for recursively discovered nested paths.
    """
    return list_fields(table_name, _samples, _schemas, source=source)


@mcp.tool()
def get_field_info_tool(table_name: str, field_name: str) -> dict:
    """Get schema metadata (type, description) for a field.

    Args:
        table_name: Table name as returned by list_tables_tool.
        field_name: Top-level field name.
    """
    return get_field_info(table_name, field_name, _samples, _schemas)


@mcp.tool()
def get_field_value_tool(table_name: str, field_path: str) -> object:
    """Get the sample value for a field. Supports dot-notation for nested access.

    Args:
        table_name: Table name as returned by list_tables_tool.
        field_path: Dot-separated path, e.g. 'customer.email' or 'status'.
    """
    return get_field_value(table_name, field_path, _samples, _schemas)


@mcp.tool()
def find_field_tool(field_name: str) -> list[dict]:
    """Find all tables containing a field name (case-insensitive substring).

    Searches top-level schema fields and nested sample paths.

    Args:
        field_name: Field name or partial name to search for.
    """
    return find_field(field_name, _samples, _schemas)


if __name__ == "__main__":
    mcp.run()
