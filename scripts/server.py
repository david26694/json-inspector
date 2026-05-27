# /// script
# dependencies = ["mcp>=1.0"]
# ///
"""MCP server entry point for json-inspector plugin.

Reads JSON_INSPECTOR_DATA_SOURCES env var for the data sources file path.
Run with: uv run scripts/server.py
"""
from __future__ import annotations
import argparse as _argparse
import sys
import sys as _sys
from pathlib import Path
from pathlib import Path as _Path
import os as _os


def _validate_env() -> str:
    data_sources = _os.environ.get("JSON_INSPECTOR_DATA_SOURCES")

    if not data_sources:
        print("json-inspector: JSON_INSPECTOR_DATA_SOURCES environment variable is not set", file=_sys.stderr)
        _sys.exit(1)
    if not _Path(data_sources).exists():
        print(f"json-inspector: JSON_INSPECTOR_DATA_SOURCES file not found: {data_sources}", file=_sys.stderr)
        _sys.exit(1)

    return data_sources


_parser = _argparse.ArgumentParser(add_help=False)
_parser.add_argument("--validate-only", action="store_true")
_args, _ = _parser.parse_known_args()

_data_sources_path_str = _validate_env()

if _args.validate_only:
    print("json-inspector: configuration OK", file=_sys.stderr)
    _sys.exit(0)

# Allow importing tools.py from the same scripts/ directory
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from tools import find_field, get_field_info, get_field_value, list_fields, list_tables

_data_sources = Path(_data_sources_path_str)

mcp = FastMCP("json-inspector")


@mcp.tool()
def list_tables_tool() -> list[str]:
    """Return all available table names (fully-qualified IDs)."""
    return list_tables(_data_sources)


@mcp.tool()
def list_fields_tool(table_name: str, source: str = "schema") -> list[str]:
    """List fields for a table.

    Args:
        table_name: Table name as returned by list_tables_tool.
        source: 'schema' for top-level field names (default),
                'sample' for recursively discovered nested paths.
    """
    return list_fields(table_name, _data_sources, source=source)


@mcp.tool()
def get_field_info_tool(table_name: str, field_name: str) -> dict:
    """Get schema metadata (type, description, null_pct, n_distinct) for a field.

    Args:
        table_name: Table name as returned by list_tables_tool.
        field_name: Field name or dot-notation path (e.g. 'shipping.state').
    """
    return get_field_info(table_name, field_name, _data_sources)


@mcp.tool()
def get_field_value_tool(table_name: str, field_path: str) -> object:
    """Get the example value for a field. Supports dot-notation for nested access.

    Args:
        table_name: Table name as returned by list_tables_tool.
        field_path: Dot-separated path, e.g. 'customer.email' or 'status'.
    """
    return get_field_value(table_name, field_path, _data_sources)


@mcp.tool()
def find_field_tool(field_name: str) -> list[dict]:
    """Find all tables containing a field name (case-insensitive substring).

    Searches top-level and nested field paths.

    Args:
        field_name: Field name or partial name to search for.
    """
    return find_field(field_name, _data_sources)


if __name__ == "__main__":
    mcp.run()
