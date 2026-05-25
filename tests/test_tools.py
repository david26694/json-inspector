from scripts.tools import list_tables, list_fields, get_field_info, get_field_value, find_field


def test_list_tables_returns_all_keys(json_files):
    samples_path, schemas_path = json_files
    result = list_tables(samples_path, schemas_path)
    assert set(result) == {"trendy.catalog.products", "trendy.orders.purchases"}


def test_list_tables_empty_files(tmp_path):
    s = tmp_path / "s.json"
    sc = tmp_path / "sc.json"
    s.write_text("{}")
    sc.write_text("{}")
    assert list_tables(s, sc) == []


def test_list_fields_schema_source(json_files):
    samples_path, schemas_path = json_files
    result = list_fields("trendy.catalog.products", samples_path, schemas_path, source="schema")
    assert result == ["product_id", "sku", "brand", "category", "price_usd", "attributes", "inventory", "updated_at"]


def test_list_fields_sample_source_includes_nested(json_files):
    samples_path, schemas_path = json_files
    result = list_fields("trendy.catalog.products", samples_path, schemas_path, source="sample")
    assert "attributes.size" in result
    assert "inventory.in_stock" in result


def test_list_fields_unknown_table(json_files):
    samples_path, schemas_path = json_files
    result = list_fields("does.not.exist", samples_path, schemas_path)
    assert "not found" in result[0]


def test_get_field_info_returns_metadata(json_files):
    samples_path, schemas_path = json_files
    result = get_field_info("trendy.catalog.products", "brand", samples_path, schemas_path)
    assert result["type"] == "STRING"
    assert "brand" in result["description"].lower()


def test_get_field_info_missing_field(json_files):
    samples_path, schemas_path = json_files
    result = get_field_info("trendy.catalog.products", "nonexistent", samples_path, schemas_path)
    assert "error" in result


def test_get_field_value_top_level(json_files):
    samples_path, schemas_path = json_files
    result = get_field_value("trendy.orders.purchases", "status", samples_path, schemas_path)
    assert result == "SHIPPED"


def test_get_field_value_nested(json_files):
    samples_path, schemas_path = json_files
    result = get_field_value("trendy.orders.purchases", "shipping.state", samples_path, schemas_path)
    assert result == "NY"


def test_get_field_value_missing_path(json_files):
    samples_path, schemas_path = json_files
    result = get_field_value("trendy.orders.purchases", "does.not.exist", samples_path, schemas_path)
    assert isinstance(result, dict) and "error" in result


def test_find_field_exact_match_across_tables(json_files):
    samples_path, schemas_path = json_files
    result = find_field("updated_at", samples_path, schemas_path)
    tables = [r["table"] for r in result]
    assert "trendy.catalog.products" in tables
    assert "trendy.orders.purchases" in tables


def test_find_field_partial_match(json_files):
    samples_path, schemas_path = json_files
    result = find_field("usd", samples_path, schemas_path)
    # price_usd in products, total_usd in purchases
    assert len(result) == 2


def test_find_field_nested_path(json_files):
    samples_path, schemas_path = json_files
    result = find_field("state", samples_path, schemas_path)
    tables = [r["table"] for r in result]
    assert "trendy.orders.purchases" in tables
    hits = next(r["matching_fields"] for r in result if r["table"] == "trendy.orders.purchases")
    assert "shipping.state" in hits


def test_find_field_no_match(json_files):
    samples_path, schemas_path = json_files
    result = find_field("zzznomatch", samples_path, schemas_path)
    assert "message" in result[0]
