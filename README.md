# json-inspector

A Claude Code plugin for inspecting nested JSON data sources — schemas and example values — via natural language. No manual greps required.

## What it does

Ask Claude questions like:
- "Which tables have a field called price_usd?"
- "List all nested fields in the products table"
- "What type is customer_id and which tables have it?"
- "Show me an example value for shipping.state"

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
uv run --project ~/.claude/plugins/cache/json-inspector/json-inspector/0.5.0 python -c "import mcp"
```

Then create a `.mcp.json` file in your **project root** pointing directly to the venv's Python:

```json
{
  "mcpServers": {
    "json-inspector": {
      "command": "/Users/you/.claude/plugins/cache/json-inspector/json-inspector/0.5.0/.venv/bin/python3",
      "args": ["/Users/you/.claude/plugins/cache/json-inspector/json-inspector/0.5.0/scripts/server.py"],
      "env": {
        "JSON_INSPECTOR_DATA_SOURCES": "/absolute/path/to/data_sources.json"
      }
    }
  }
}
```

Replace:
- `/Users/you` → your actual home directory (`echo $HOME`)
- `0.5.0` → the version you installed (check `~/.claude/plugins/cache/json-inspector/json-inspector/`)
- `JSON_INSPECTOR_DATA_SOURCES` → absolute path to your `data_sources.json`

Add to `.gitignore` (paths are machine-specific):
```
.mcp.json
```

Claude Code automatically picks up `.mcp.json` from the project root. When prompted to approve the project's MCP servers, click **Allow**. Each developer on the team creates their own copy.

> **Why point to the venv Python directly?** Using `uv run` at session startup can be slow or unreliable when a project venv is already active (`VIRTUAL_ENV` set). The venv Python is already warm, starts instantly, and has `mcp` installed.

> **After `claude plugin update json-inspector@json-inspector`:** re-run the warm-up command with the new version number, then update `command` and `args` in `.mcp.json` to match.

---

## JSON file format

A single `data_sources.json` file contains schema metadata and example values for all tables:

```json
{
  "my.project.table": {
    "fields": [
      {
        "name": "order_id",
        "type": "STRING",
        "description": "Unique order identifier",
        "null_pct": 0.0,
        "n_distinct": 10000,
        "example": "ORD_US_5512893"
      },
      {
        "name": "shipping",
        "type": "RECORD",
        "description": "Shipping address details",
        "null_pct": 0.0,
        "example": {"city": "New York", "state": "NY"},
        "fields": [
          {"name": "city",  "type": "STRING", "description": "City",  "null_pct": 0.0, "example": "New York"},
          {"name": "state", "type": "STRING", "description": "State", "null_pct": 0.0, "example": "NY"}
        ]
      }
    ]
  }
}
```

**Field properties:**

| Property | Required | Description |
|---|---|---|
| `name` | ✅ | Field name |
| `type` | ✅ | BigQuery type: `STRING`, `FLOAT`, `INTEGER`, `BOOLEAN`, `RECORD`, `TIMESTAMP`, … |
| `description` | ✅ | Human-readable description |
| `null_pct` | optional | Fraction of NULL values (0.0–1.0) |
| `n_distinct` | optional | Approximate number of distinct values |
| `example` | optional | A representative value (used by `get-field-value`) |
| `fields` | optional | Nested fields for `RECORD` types |

## Generating your data_sources.json from BigQuery

Run this script once to produce `data_sources.json` from your BQ tables.
Requires `google-cloud-bigquery` (`pip install google-cloud-bigquery`).

```python
import json
from google.cloud import bigquery

TABLE_IDS = [
    "project.dataset.table1",
    "project.dataset.table2",
]

client = bigquery.Client()
data_sources = {}

def schema_to_fields(bq_fields) -> list:
    result = []
    for field in bq_fields:
        entry = {
            "name": field.name,
            "type": field.field_type,
            "description": field.description or "",
        }
        if field.field_type == "RECORD" and field.fields:
            entry["fields"] = schema_to_fields(field.fields)
        result.append(entry)
    return result

for table_id in TABLE_IDS:
    table = client.get_table(table_id)
    fields = schema_to_fields(table.schema)

    # Fetch one sample row to populate example values
    rows = list(
        client.query(
            f"SELECT TO_JSON_STRING(t) AS row FROM `{table_id}` AS t LIMIT 1"
        ).result()
    )
    sample = json.loads(rows[0]["row"]) if rows else {}

    # Attach example values to top-level fields
    for f in fields:
        if f["name"] in sample:
            f["example"] = sample[f["name"]]

    data_sources[table_id] = {"fields": fields}

with open("data_sources.json", "w") as f:
    json.dump(data_sources, f, indent=2, default=str)

print(f"Done — {len(TABLE_IDS)} tables written.")
```

Re-run this whenever your table schemas change to keep the file up to date.

## How it works

The plugin runs a Python MCP server (`scripts/server.py`) in an isolated virtual environment managed by `uv`. After warming up the venv once, the server is invoked directly via the venv's Python — no `pip install` or manual environment management needed. The server exposes five tools that Claude calls natively via the MCP protocol; no Anthropic API key is required from users.

## Troubleshooting

### MCP tools not showing up in Claude

Run the health check to diagnose:

```bash
export JSON_INSPECTOR_DATA_SOURCES=/path/to/data_sources.json
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
