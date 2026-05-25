---
name: JSON Data Source Inspector
description: >
  Activates when the user asks about tables, fields, schemas, or sample values in
  their JSON data sources. Use when the user asks questions like "which tables have
  a field called X", "list the fields in the products table", "what type is price_usd",
  "show me a sample value for shipping.state", or "find all fields related to inventory".
  Also activates when the user wants to explore nested sub-objects in any table.
version: 1.0.0
---

## How to Inspect JSON Data Sources

You have five MCP tools available from the `json-inspector` server. Always start
with `list_tables_tool` if the user hasn't specified a table — never guess table names.

### Tool decision flow

1. **"What tables are available?"** → `list_tables_tool()`
2. **"What fields does table X have?"** → `list_fields_tool(table_name=X, source="schema")`
   - Use `source="sample"` to discover nested sub-object paths like `shipping.state`
3. **"What type/description does field F have?"** → `get_field_info_tool(table_name, field_name)`
4. **"Show me a sample value for field F"** → `get_field_value_tool(table_name, field_path)`
   - `field_path` supports dot notation: `"shipping.state"`, `"attributes.size"`
5. **"Which tables have a field called F?"** → `find_field_tool(field_name)`
   - Searches both schema-level and nested sample paths; case-insensitive substring match

### Example interactions

**User:** which tables have a price_usd field?
→ Call `find_field_tool("price_usd")` → report which tables and at which paths

**User:** show me all nested fields in the products table
→ Call `list_fields_tool("trendy.catalog.products", source="sample")` → report full dotted paths

**User:** what's the type of customer_id and which tables have it?
→ Call `find_field_tool("customer_id")` to find tables, then
  `get_field_info_tool(table, "customer_id")` for each match → report type + description

**User:** what does the shipping sub-object contain?
→ Call `list_fields_tool(table, source="sample")`, filter paths starting with `shipping.`

### Rules

- Never grep files manually — always use the MCP tools
- If `find_field_tool` returns no match, suggest partial alternatives (e.g., try `"ship"` if `"shipping_address"` failed)
- When multiple tables match, show all of them with their paths
- Use `source="sample"` any time the user asks about nested or sub-object fields
