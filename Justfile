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
