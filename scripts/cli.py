#!/usr/bin/env python3
"""CLI fallback for json-inspector — mirrors the five MCP tools."""
import argparse
import os
import sys
from pathlib import Path

# Make scripts/ importable regardless of CWD
sys.path.insert(0, str(Path(__file__).parent))
from tools import list_tables, list_fields, get_field_info, get_field_value, find_field


def _resolve_paths() -> tuple[Path, Path]:
    samples = os.environ.get("JSON_INSPECTOR_SAMPLES")
    schemas = os.environ.get("JSON_INSPECTOR_SCHEMAS")
    missing = [name for name, val in [("JSON_INSPECTOR_SAMPLES", samples), ("JSON_INSPECTOR_SCHEMAS", schemas)] if not val]
    if missing:
        print(f"Error: missing environment variable(s): {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    return Path(samples), Path(schemas)


def cmd_list_tables(args):
    samples, schemas = _resolve_paths()
    tables = list_tables(samples, schemas)
    for t in tables:
        print(t)


def cmd_list_fields(args):
    samples, schemas = _resolve_paths()
    fields = list_fields(args.table, samples, schemas, source=args.source)
    for f in fields:
        print(f)


def cmd_get_field_info(args):
    samples, schemas = _resolve_paths()
    info = get_field_info(args.table, args.field, samples, schemas)
    if isinstance(info, dict) and "error" not in info:
        print(f"name:        {info.get('name')}")
        print(f"type:        {info.get('type')}")
        print(f"description: {info.get('description')}")
    else:
        print(info if isinstance(info, str) else info.get("error", info), file=sys.stderr)
        sys.exit(1)


def cmd_get_field_value(args):
    samples, schemas = _resolve_paths()
    value = get_field_value(args.table, args.field_path, samples, schemas)
    print(value)


def cmd_find_field(args):
    samples, schemas = _resolve_paths()
    results = find_field(args.field_name, samples, schemas)
    for entry in results:
        if "message" in entry:
            print(entry["message"])
        else:
            print(f"\n{entry['table']}")
            for f in entry["matching_fields"]:
                print(f"  {f}")


def main():
    parser = argparse.ArgumentParser(description="Inspect JSON data sources from the command line")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-tables", help="List all available tables")

    p_lf = sub.add_parser("list-fields", help="List fields in a table")
    p_lf.add_argument("table")
    p_lf.add_argument("--source", choices=["schema", "sample"], default="schema")

    p_gfi = sub.add_parser("get-field-info", help="Get type and description of a field")
    p_gfi.add_argument("table")
    p_gfi.add_argument("field")

    p_gfv = sub.add_parser("get-field-value", help="Get sample value for a field (dot notation supported)")
    p_gfv.add_argument("table")
    p_gfv.add_argument("field_path")

    p_ff = sub.add_parser("find-field", help="Find all tables containing a field name")
    p_ff.add_argument("field_name")

    dispatch = {
        "list-tables": cmd_list_tables,
        "list-fields": cmd_list_fields,
        "get-field-info": cmd_get_field_info,
        "get-field-value": cmd_get_field_value,
        "find-field": cmd_find_field,
    }

    args = parser.parse_args()
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
