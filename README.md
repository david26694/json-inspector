# json-inspector

A Claude Code plugin for inspecting nested JSON data sources — schemas and sample records — via natural language. No manual greps required.

## What it does

Ask Claude questions like:
- "Which tables have a field called price_usd?"
- "List all nested fields in the products table"
- "What type is customer_id and which tables have it?"
- "Show me a sample value for shipping.state"

Claude uses five MCP tools under the hood to answer precisely.

## Prerequisites

- [Claude Code](https://claude.ai/code) installed
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed (handles Python automatically)

Install `uv` with one command:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

```bash
# Register the marketplace (once)
claude plugin marketplace add david26694/json-inspector

# Install the plugin
claude plugin install json-inspector
```

## Configuration

After installing, warm up the plugin's virtual environment once:

```bash
uv run --project ~/.claude/plugins/cache/json-inspector/json-inspector/0.3.0 python -c "import mcp"
```

Then create a `.mcp.json` file in your **project root** pointing directly to the venv's Python:

```json
{
  "mcpServers": {
    "json-inspector": {
      "command": "/Users/you/.claude/plugins/cache/json-inspector/json-inspector/0.3.0/.venv/bin/python3",
      "args": ["/Users/you/.claude/plugins/cache/json-inspector/json-inspector/0.3.0/scripts/server.py"],
      "env": {
        "JSON_INSPECTOR_SAMPLES": "/absolute/path/to/sample_records.json",
        "JSON_INSPECTOR_SCHEMAS": "/absolute/path/to/schemas.json"
      }
    }
  }
}
```

Replace:
- `/Users/you` → your actual home directory (`echo $HOME`)
- `0.3.0` → the version you installed (check `~/.claude/plugins/cache/json-inspector/json-inspector/`)
- `JSON_INSPECTOR_SAMPLES` → absolute path to your `sample_records.json`
- `JSON_INSPECTOR_SCHEMAS` → absolute path to your `schemas.json`

Add to `.gitignore` (paths are machine-specific):
```
.mcp.json
```

Claude Code automatically picks up `.mcp.json` from the project root. When prompted to approve the project's MCP servers, click **Allow**. Each developer on the team creates their own copy.

> **Why point to the venv Python directly?** Using `uv run` at session startup can be slow or unreliable when a project venv is already active (`VIRTUAL_ENV` set). The venv Python is already warm, starts instantly, and has `mcp` installed.

> **After `claude plugin update json-inspector@json-inspector`:** re-run the warm-up command with the new version number, then update `command` and `args` in `.mcp.json` to match.

---

Both JSON files must be valid:
- `sample_records.json`: `{"table.name": {"field": value, ...}, ...}`
- `schemas.json`: `{"table.name": [{"name": "field", "type": "STRING", "description": "..."}, ...], ...}`

## JSON file format

**sample_records.json** — one sample row per table, nested objects allowed:
```json
{
  "trendy.catalog.products": {
    "product_id": "PROD_US_78234",
    "brand": "Everlane",
    "attributes": {"size": "M", "color": "black"}
  },
  "trendy.orders.purchases": {
    "order_id": "ORD_US_5512893",
    "status": "SHIPPED",
    "shipping": {"city": "New York", "state": "NY"}
  }
}
```

**schemas.json** — flat list of field definitions per table:
```json
{
  "trendy.catalog.products": [
    {"name": "product_id", "type": "STRING", "description": "Unique product identifier"},
    {"name": "price_usd", "type": "FLOAT", "description": "Retail price in USD"}
  ]
}
```

## Generating your JSON files from BigQuery

Run this script once to produce `sample_records.json` and `schemas.json` from your BQ tables.
Requires `google-cloud-bigquery` (`pip install google-cloud-bigquery`).

```python
import json
from google.cloud import bigquery

TABLE_IDS = [
    "project.dataset.table1",
    "project.dataset.table2",
]

client = bigquery.Client()
schemas = {}
samples = {}

for table_id in TABLE_IDS:
    # Schema — get_table() includes field descriptions, INFORMATION_SCHEMA does not
    table = client.get_table(table_id)
    schemas[table_id] = [
        {
            "name": field.name,
            "type": field.field_type,
            "description": field.description or "",
        }
        for field in table.schema
    ]

    # Sample row — TO_JSON_STRING handles nested RECORDs, ARRAYs, and timestamps
    rows = list(
        client.query(
            f"SELECT TO_JSON_STRING(t) AS row FROM `{table_id}` AS t LIMIT 1"
        ).result()
    )
    if rows:
        samples[table_id] = json.loads(rows[0]["row"])

with open("schemas.json", "w") as f:
    json.dump(schemas, f, indent=2)

with open("sample_records.json", "w") as f:
    json.dump(samples, f, indent=2, default=str)

print(f"Done — {len(TABLE_IDS)} tables written.")
```

Re-run this whenever your table schemas change to keep the files up to date.

## How it works

The plugin runs a Python MCP server (`scripts/server.py`) in an isolated virtual environment managed by `uv`. After warming up the venv once, the server is invoked directly via the venv's Python — no `pip install` or manual environment management needed. The server exposes five tools that Claude calls natively via the MCP protocol; no Anthropic API key is required from users.

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

## Contributing

```bash
git clone https://github.com/david26694/json-inspector
cd json-inspector
uv sync --extra dev
uv run pytest
```

## License

MIT
