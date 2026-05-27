#!/usr/bin/env python3
"""End-to-end health check for json-inspector configuration."""
import argparse
import json
import os
import sys
from pathlib import Path


def _check(condition: bool, message: str, fatal: bool = True) -> bool:
    status = "OK  " if condition else ("FAIL" if fatal else "WARN")
    print(f"  [{status}] {message}")
    if not condition and fatal:
        sys.exit(1)
    return condition


def main():
    parser = argparse.ArgumentParser(description="Validate json-inspector setup")
    parser.add_argument("--check-mcp", action="store_true", help="Also check for .mcp.json")
    parser.add_argument("--mcp-dir", default=".", help="Directory to look for .mcp.json (default: cwd)")
    args = parser.parse_args()

    print("json-inspector: running configuration checks\n")

    # 1. Environment variable
    data_sources_path = os.environ.get("JSON_INSPECTOR_DATA_SOURCES")
    _check(bool(data_sources_path), "JSON_INSPECTOR_DATA_SOURCES is set")
    if not data_sources_path:
        sys.exit(1)

    # 2. File exists
    _check(Path(data_sources_path).exists(), f"data sources file exists: {data_sources_path}")

    # 3. Valid JSON
    try:
        json.loads(Path(data_sources_path).read_text())
        _check(True, "data sources file is valid JSON")
    except json.JSONDecodeError as e:
        _check(False, f"invalid JSON in data sources file ({data_sources_path}): {e}")

    # 4. Optional: .mcp.json presence
    if args.check_mcp:
        mcp_file = Path(args.mcp_dir) / ".mcp.json"
        exists = mcp_file.exists()
        _check(exists, f".mcp.json found at {mcp_file}", fatal=False)
        if exists:
            try:
                cfg = json.loads(mcp_file.read_text())
                has_server = "mcpServers" in cfg and "json-inspector" in cfg["mcpServers"]
                _check(has_server, ".mcp.json contains json-inspector server entry", fatal=False)
            except json.JSONDecodeError:
                _check(False, ".mcp.json is valid JSON", fatal=False)

    print("\njson-inspector: all checks OK")


if __name__ == "__main__":
    main()
