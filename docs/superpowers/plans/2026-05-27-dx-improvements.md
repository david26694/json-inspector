# DX Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the "Claude had to spawn a subagent" failure mode by adding a CLI fallback, a setup generator, server startup validation, and a health-check command.

**Architecture:** Four independent improvements: (1) a CLI script exposing all five MCP tools on the command line, (2) a Justfile that wraps them, (3) early-exit validation inside the MCP server so it fails loudly instead of silently, and (4) a `validate` command that checks the whole stack end-to-end.

**Tech Stack:** Python 3.11, `argparse`, `uv`, FastMCP (existing), pytest

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `scripts/cli.py` | CLI entry point — same 5 ops as MCP tools |
| Create | `Justfile` | `just inspect <cmd>` shortcuts |
| Modify | `scripts/server.py` | Validate env vars + file existence at startup |
| Create | `scripts/validate.py` | End-to-end health check (config + server reachability) |
| Modify | `tests/test_tools.py` | Tests for new CLI behaviour |
| Create | `tests/test_cli.py` | Tests for CLI argument parsing + output |

---

### Task 1: CLI script — core five operations

**Files:**
- Create: `scripts/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_cli.py
import subprocess, sys, json, os, pytest

SAMPLES = "tests/fixtures/sample_records.json"
SCHEMAS = "tests/fixtures/schemas.json"

def _run(*args):
    env = {**os.environ, "JSON_INSPECTOR_SAMPLES": SAMPLES, "JSON_INSPECTOR_SCHEMAS": SCHEMAS}
    result = subprocess.run(
        [sys.executable, "scripts/cli.py", *args],
        capture_output=True, text=True, env=env,
    )
    return result

def test_list_tables_exit_zero():
    r = _run("list-tables")
    assert r.returncode == 0

def test_list_tables_output_contains_table():
    r = _run("list-tables")
    assert "trendy.catalog.products" in r.stdout

def test_find_field_exit_zero():
    r = _run("find-field", "price")
    assert r.returncode == 0

def test_find_field_matches():
    r = _run("find-field", "price")
    assert "price_usd" in r.stdout

def test_list_fields_schema():
    r = _run("list-fields", "trendy.catalog.products")
    assert "price_usd" in r.stdout

def test_list_fields_sample():
    r = _run("list-fields", "trendy.catalog.products", "--source", "sample")
    assert "attributes.size" in r.stdout

def test_get_field_info():
    r = _run("get-field-info", "trendy.catalog.products", "price_usd")
    assert "FLOAT" in r.stdout

def test_get_field_value():
    r = _run("get-field-value", "trendy.catalog.products", "attributes.size")
    assert r.returncode == 0

def test_missing_env_exits_nonzero():
    env = {k: v for k, v in os.environ.items()
           if k not in ("JSON_INSPECTOR_SAMPLES", "JSON_INSPECTOR_SCHEMAS")}
    result = subprocess.run(
        [sys.executable, "scripts/cli.py", "list-tables"],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode != 0
    assert "JSON_INSPECTOR_SAMPLES" in result.stderr or "JSON_INSPECTOR_SCHEMAS" in result.stderr
```

The tests rely on the fixture files used by the existing test suite. Check their location first:

```bash
grep -r "sample_records\|schemas" tests/conftest.py
```

If `conftest.py` builds them as tmp files, the CLI tests need the same fixture. Create `tests/fixtures/` with the same data:

```bash
mkdir -p tests/fixtures
```

Then copy fixture data from `conftest.py` into:
- `tests/fixtures/sample_records.json`
- `tests/fixtures/schemas.json`

Using the data already in `conftest.py` (products + purchases tables).

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/david.masip/Documents/Workspace/json-inspector
uv run pytest tests/test_cli.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError` or `FileNotFoundError` — `scripts/cli.py` doesn't exist yet.

- [ ] **Step 3: Create fixture files**

`tests/fixtures/sample_records.json`:
```json
{
  "trendy.catalog.products": {
    "product_id": "P-001",
    "sku": "SKU-ABC",
    "brand": "AcmeCo",
    "category": "Apparel",
    "price_usd": 29.99,
    "attributes": {"size": "M", "color": "blue", "material": "cotton"},
    "inventory": {"in_stock": true, "units_available": 42}
  },
  "trendy.orders.purchases": {
    "order_id": "O-999",
    "customer_id": "C-123",
    "status": "shipped",
    "total_usd": 59.98,
    "shipping": {"address": "1 Main St", "city": "Springfield", "state": "IL", "zip": "62701"}
  }
}
```

`tests/fixtures/schemas.json`:
```json
{
  "trendy.catalog.products": [
    {"name": "product_id", "type": "STRING",    "description": "Unique product identifier"},
    {"name": "sku",        "type": "STRING",    "description": "Stock keeping unit"},
    {"name": "brand",      "type": "STRING",    "description": "Brand name"},
    {"name": "category",   "type": "STRING",    "description": "Product category"},
    {"name": "price_usd",  "type": "FLOAT",     "description": "Price in US dollars"},
    {"name": "attributes", "type": "RECORD",    "description": "Product attributes"},
    {"name": "inventory",  "type": "RECORD",    "description": "Inventory info"}
  ],
  "trendy.orders.purchases": [
    {"name": "order_id",    "type": "STRING",    "description": "Unique order identifier"},
    {"name": "customer_id", "type": "STRING",    "description": "Customer identifier"},
    {"name": "status",      "type": "STRING",    "description": "Order status"},
    {"name": "total_usd",   "type": "FLOAT",     "description": "Total order amount in USD"},
    {"name": "shipping",    "type": "RECORD",    "description": "Shipping details"}
  ]
}
```

- [ ] **Step 4: Create `scripts/cli.py`**

```python
#!/usr/bin/env python3
"""CLI fallback for json-inspector — mirrors the five MCP tools."""
import argparse
import os
import sys
from pathlib import Path

# Make scripts/ importable regardless of CWD
sys.path.insert(0, str(Path(__file__).parent))
from tools import list_tables, list_fields, get_field_info, get_field_value, find_field


def _resolve_paths() -> tuple[str, str]:
    samples = os.environ.get("JSON_INSPECTOR_SAMPLES")
    schemas = os.environ.get("JSON_INSPECTOR_SCHEMAS")
    missing = [name for name, val in [("JSON_INSPECTOR_SAMPLES", samples), ("JSON_INSPECTOR_SCHEMAS", schemas)] if not val]
    if missing:
        print(f"Error: missing environment variable(s): {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    return samples, schemas


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
```

- [ ] **Step 5: Run tests — expect pass**

```bash
uv run pytest tests/test_cli.py -v
```

Expected: all 9 tests pass.

- [ ] **Step 6: Commit**

```bash
git add scripts/cli.py tests/test_cli.py tests/fixtures/
git commit -m "feat: add CLI fallback mirroring all five MCP tools"
```

---

### Task 2: Justfile with `inspect` shortcuts

**Files:**
- Create: `Justfile`

No tests needed — this is a thin wrapper over Task 1.

- [ ] **Step 1: Create `Justfile`**

```makefile
# json-inspector Justfile
# Run any recipe with: just <recipe> [args]

samples := env_var_or_default("JSON_INSPECTOR_SAMPLES", "sample_records.json")
schemas := env_var_or_default("JSON_INSPECTOR_SCHEMAS", "schemas.json")

# Run the test suite
test:
    uv run pytest tests/ -v

# List all available tables
inspect-list-tables:
    JSON_INSPECTOR_SAMPLES={{samples}} JSON_INSPECTOR_SCHEMAS={{schemas}} \
        uv run scripts/cli.py list-tables

# List fields in a table  (usage: just inspect-list-fields "my.table.name")
inspect-list-fields table source="schema":
    JSON_INSPECTOR_SAMPLES={{samples}} JSON_INSPECTOR_SCHEMAS={{schemas}} \
        uv run scripts/cli.py list-fields "{{table}}" --source {{source}}

# Get type and description for a field  (usage: just inspect-get-field-info "table" "field")
inspect-get-field-info table field:
    JSON_INSPECTOR_SAMPLES={{samples}} JSON_INSPECTOR_SCHEMAS={{schemas}} \
        uv run scripts/cli.py get-field-info "{{table}}" "{{field}}"

# Get sample value for a field path  (usage: just inspect-get-field-value "table" "nested.path")
inspect-get-field-value table field_path:
    JSON_INSPECTOR_SAMPLES={{samples}} JSON_INSPECTOR_SCHEMAS={{schemas}} \
        uv run scripts/cli.py get-field-value "{{table}}" "{{field_path}}"

# Find tables containing a field name  (usage: just inspect-find-field "price")
inspect-find-field field_name:
    JSON_INSPECTOR_SAMPLES={{samples}} JSON_INSPECTOR_SCHEMAS={{schemas}} \
        uv run scripts/cli.py find-field "{{field_name}}"

# Validate MCP config and server reachability
validate:
    uv run scripts/validate.py
```

- [ ] **Step 2: Smoke-test manually**

```bash
cd /Users/david.masip/Documents/Workspace/json-inspector
export JSON_INSPECTOR_SAMPLES=tests/fixtures/sample_records.json
export JSON_INSPECTOR_SCHEMAS=tests/fixtures/schemas.json
just inspect-list-tables
just inspect-find-field price
just inspect-list-fields "trendy.catalog.products" sample
```

Expected output for `list-tables`:
```
trendy.catalog.products
trendy.orders.purchases
```

- [ ] **Step 3: Commit**

```bash
git add Justfile
git commit -m "feat: add Justfile with inspect shortcuts and validate recipe"
```

---

### Task 3: Server startup validation

**Files:**
- Modify: `scripts/server.py`
- Modify: `tests/test_tools.py` (add startup validation test)

- [ ] **Step 1: Read current `scripts/server.py`**

```bash
cat scripts/server.py
```

Understand exactly where the MCP server object is created and where tools are registered, so the validation block can go at the very top — before any FastMCP setup.

- [ ] **Step 2: Write failing test**

Add to `tests/test_tools.py`:

```python
import subprocess, sys, os

def test_server_exits_if_samples_missing(tmp_path):
    schemas = tmp_path / "schemas.json"
    schemas.write_text("{}")
    env = {
        **os.environ,
        "JSON_INSPECTOR_SCHEMAS": str(schemas),
    }
    env.pop("JSON_INSPECTOR_SAMPLES", None)
    result = subprocess.run(
        [sys.executable, "scripts/server.py", "--validate-only"],
        capture_output=True, text=True, env=env, timeout=5,
    )
    assert result.returncode != 0
    assert "JSON_INSPECTOR_SAMPLES" in result.stderr

def test_server_exits_if_samples_file_not_found(tmp_path):
    schemas = tmp_path / "schemas.json"
    schemas.write_text("{}")
    env = {
        **os.environ,
        "JSON_INSPECTOR_SAMPLES": "/nonexistent/path/samples.json",
        "JSON_INSPECTOR_SCHEMAS": str(schemas),
    }
    result = subprocess.run(
        [sys.executable, "scripts/server.py", "--validate-only"],
        capture_output=True, text=True, env=env, timeout=5,
    )
    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "JSON_INSPECTOR_SAMPLES" in result.stderr

def test_server_validate_only_succeeds(tmp_path):
    samples = tmp_path / "samples.json"
    schemas = tmp_path / "schemas.json"
    samples.write_text("{}")
    schemas.write_text("{}")
    env = {
        **os.environ,
        "JSON_INSPECTOR_SAMPLES": str(samples),
        "JSON_INSPECTOR_SCHEMAS": str(schemas),
    }
    result = subprocess.run(
        [sys.executable, "scripts/server.py", "--validate-only"],
        capture_output=True, text=True, env=env, timeout=5,
    )
    assert result.returncode == 0
```

- [ ] **Step 3: Run to confirm failure**

```bash
uv run pytest tests/test_tools.py -k "server_exits" -v
```

Expected: FAIL — no `--validate-only` flag exists yet.

- [ ] **Step 4: Add startup validation to `server.py`**

Add this block at the top of `scripts/server.py`, before `from mcp ...` or FastMCP instantiation — insert after imports:

```python
import argparse as _argparse
import os as _os
import sys as _sys
from pathlib import Path as _Path


def _validate_env() -> tuple[str, str]:
    """Check required env vars and file existence. Print to stderr and exit(1) on failure."""
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


# Parse --validate-only before starting the MCP server (used by health checks)
_parser = _argparse.ArgumentParser(add_help=False)
_parser.add_argument("--validate-only", action="store_true")
_args, _ = _parser.parse_known_args()

_validate_env()

if _args.validate_only:
    print("json-inspector: configuration OK", file=_sys.stderr)
    _sys.exit(0)
```

- [ ] **Step 5: Run tests**

```bash
uv run pytest tests/test_tools.py -v
```

Expected: all tests (including the 3 new ones) pass.

- [ ] **Step 6: Commit**

```bash
git add scripts/server.py tests/test_tools.py
git commit -m "feat: add startup validation and --validate-only flag to server"
```

---

### Task 4: Health-check / validate script

**Files:**
- Create: `scripts/validate.py`
- Create: `tests/test_validate.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_validate.py
import subprocess, sys, os, json
from pathlib import Path

def _run_validate(env_overrides=None, extra_args=None):
    env = {**os.environ}
    if env_overrides:
        for k, v in env_overrides.items():
            if v is None:
                env.pop(k, None)
            else:
                env[k] = v
    result = subprocess.run(
        [sys.executable, "scripts/validate.py", *(extra_args or [])],
        capture_output=True, text=True, env=env, timeout=10,
    )
    return result

def test_validate_missing_samples_fails():
    r = _run_validate({"JSON_INSPECTOR_SAMPLES": None, "JSON_INSPECTOR_SCHEMAS": None})
    assert r.returncode != 0
    assert "JSON_INSPECTOR_SAMPLES" in r.stdout + r.stderr

def test_validate_bad_json_fails(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    good = tmp_path / "good.json"
    good.write_text("{}")
    r = _run_validate({
        "JSON_INSPECTOR_SAMPLES": str(bad),
        "JSON_INSPECTOR_SCHEMAS": str(good),
    })
    assert r.returncode != 0
    assert "invalid json" in r.stdout.lower() + r.stderr.lower()

def test_validate_good_config_passes(tmp_path):
    samples = tmp_path / "s.json"
    schemas = tmp_path / "sc.json"
    samples.write_text('{"my.table": {"id": 1}}')
    schemas.write_text('{"my.table": [{"name": "id", "type": "INTEGER", "description": "pk"}]}')
    r = _run_validate({
        "JSON_INSPECTOR_SAMPLES": str(samples),
        "JSON_INSPECTOR_SCHEMAS": str(schemas),
    })
    assert r.returncode == 0
    assert "OK" in r.stdout or "ok" in r.stdout.lower()

def test_validate_mcp_json_check(tmp_path):
    """--check-mcp flag reports missing .mcp.json as a warning, not error."""
    samples = tmp_path / "s.json"
    schemas = tmp_path / "sc.json"
    samples.write_text("{}")
    schemas.write_text("{}")
    r = _run_validate(
        {"JSON_INSPECTOR_SAMPLES": str(samples), "JSON_INSPECTOR_SCHEMAS": str(schemas)},
        extra_args=["--check-mcp", "--mcp-dir", str(tmp_path)],
    )
    # Missing .mcp.json is a warning, not failure
    assert r.returncode == 0
    assert "mcp" in r.stdout.lower() or "warn" in r.stdout.lower()
```

- [ ] **Step 2: Run to confirm failure**

```bash
uv run pytest tests/test_validate.py -v
```

Expected: FAIL — `scripts/validate.py` doesn't exist yet.

- [ ] **Step 3: Create `scripts/validate.py`**

```python
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

    # 1. Environment variables
    samples_path = os.environ.get("JSON_INSPECTOR_SAMPLES")
    schemas_path = os.environ.get("JSON_INSPECTOR_SCHEMAS")

    _check(bool(samples_path), "JSON_INSPECTOR_SAMPLES is set")
    _check(bool(schemas_path), "JSON_INSPECTOR_SCHEMAS is set")

    if not samples_path or not schemas_path:
        sys.exit(1)

    # 2. Files exist
    _check(Path(samples_path).exists(), f"samples file exists: {samples_path}")
    _check(Path(schemas_path).exists(), f"schemas file exists: {schemas_path}")

    # 3. Valid JSON
    for label, path in [("samples", samples_path), ("schemas", schemas_path)]:
        try:
            json.loads(Path(path).read_text())
            _check(True, f"{label} file is valid JSON")
        except json.JSONDecodeError as e:
            _check(False, f"invalid JSON in {label} file ({path}): {e}")

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
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_validate.py -v
```

Expected: all 4 tests pass.

- [ ] **Step 5: Smoke-test manually**

```bash
export JSON_INSPECTOR_SAMPLES=tests/fixtures/sample_records.json
export JSON_INSPECTOR_SCHEMAS=tests/fixtures/schemas.json
uv run scripts/validate.py
uv run scripts/validate.py --check-mcp --mcp-dir .
```

- [ ] **Step 6: Commit**

```bash
git add scripts/validate.py tests/test_validate.py
git commit -m "feat: add validate script for end-to-end health checks"
```

---

### Task 5: Full test suite pass + README update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Run full test suite**

```bash
uv run pytest tests/ -v
```

Expected: all tests pass. If any fail, fix them before proceeding.

- [ ] **Step 2: Update README**

Add a **"Troubleshooting"** section after the installation instructions:

```markdown
## Troubleshooting

### MCP tools not showing up in Claude

Run the health check to diagnose:

```bash
export JSON_INSPECTOR_SAMPLES=/path/to/sample_records.json
export JSON_INSPECTOR_SCHEMAS=/path/to/schemas.json
uv run scripts/validate.py --check-mcp
```

### CLI fallback (no MCP required)

All five MCP tools are also available on the command line:

```bash
just inspect-list-tables
just inspect-find-field "price"
just inspect-list-fields "my.schema.table" --source sample
just inspect-get-field-info "my.schema.table" "field_name"
just inspect-get-field-value "my.schema.table" "nested.path"
```

Or directly via `uv run scripts/cli.py <command> --help`.
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add troubleshooting section and CLI fallback docs"
```
