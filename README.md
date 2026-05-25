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

Add two environment variables to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export JSON_INSPECTOR_SAMPLES="/absolute/path/to/sample_records.json"
export JSON_INSPECTOR_SCHEMAS="/absolute/path/to/schemas.json"
```

Then reload your shell (`source ~/.zshrc`) and restart Claude Code. No plugin files need to be edited — `${CLAUDE_PLUGIN_ROOT}` is injected automatically by Claude Code, and the two path variables are read from your shell environment.

Both files must be valid JSON:
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

## How it works

The plugin runs a Python MCP server (`scripts/server.py`) via `uv run` — no manual `pip install` needed. `uv` creates an isolated virtual environment automatically on first run. The server exposes five tools that Claude calls natively; no Anthropic API key is required from users.

## Contributing

```bash
git clone https://github.com/david26694/json-inspector
cd json-inspector
uv sync --extra dev
uv run pytest
```

## License

MIT
