import os
import subprocess
import sys

from scripts.tools import list_tables, list_fields, get_field_info, get_field_value, find_field


def test_list_tables_returns_all_keys(data_sources):
    result = list_tables(data_sources)
    assert set(result) == {"trendy.catalog.products", "trendy.orders.purchases"}


def test_list_tables_empty_files(tmp_path):
    p = tmp_path / "ds.json"
    p.write_text("{}")
    assert list_tables(p) == []


def test_list_fields_schema_source(data_sources):
    result = list_fields("trendy.catalog.products", data_sources, source="schema")
    assert result == ["product_id", "sku", "brand", "category", "price_usd", "attributes", "inventory", "updated_at"]


def test_list_fields_sample_source_includes_nested(data_sources):
    result = list_fields("trendy.catalog.products", data_sources, source="sample")
    assert "attributes.size" in result
    assert "inventory.in_stock" in result


def test_list_fields_unknown_table(data_sources):
    result = list_fields("does.not.exist", data_sources)
    assert "not found" in result[0]


def test_get_field_info_returns_metadata(data_sources):
    result = get_field_info("trendy.catalog.products", "brand", data_sources)
    assert result["type"] == "STRING"
    assert "brand" in result["description"].lower()


def test_get_field_info_missing_field(data_sources):
    result = get_field_info("trendy.catalog.products", "nonexistent", data_sources)
    assert "error" in result


def test_get_field_value_top_level(data_sources):
    result = get_field_value("trendy.orders.purchases", "status", data_sources)
    assert result == "SHIPPED"


def test_get_field_value_nested(data_sources):
    result = get_field_value("trendy.orders.purchases", "shipping.state", data_sources)
    assert result == "NY"


def test_get_field_value_missing_path(data_sources):
    result = get_field_value("trendy.orders.purchases", "does.not.exist", data_sources)
    assert isinstance(result, dict) and "error" in result


def test_find_field_exact_match_across_tables(data_sources):
    result = find_field("updated_at", data_sources)
    tables = [r["table"] for r in result]
    assert "trendy.catalog.products" in tables
    assert "trendy.orders.purchases" in tables


def test_find_field_partial_match(data_sources):
    result = find_field("usd", data_sources)
    assert len(result) == 2


def test_find_field_nested_path(data_sources):
    result = find_field("state", data_sources)
    tables = [r["table"] for r in result]
    assert "trendy.orders.purchases" in tables
    hits = next(r["matching_fields"] for r in result if r["table"] == "trendy.orders.purchases")
    assert "shipping.state" in hits


def test_find_field_no_match(data_sources):
    result = find_field("zzznomatch", data_sources)
    assert "message" in result[0]


def test_server_exits_if_data_sources_missing(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "JSON_INSPECTOR_DATA_SOURCES"}
    result = subprocess.run(
        [sys.executable, "scripts/server.py", "--validate-only"],
        capture_output=True, text=True, env=env, timeout=5,
    )
    assert result.returncode != 0
    assert "JSON_INSPECTOR_DATA_SOURCES" in result.stderr


def test_server_exits_if_file_not_found(tmp_path):
    env = {**os.environ, "JSON_INSPECTOR_DATA_SOURCES": "/nonexistent/data_sources.json"}
    result = subprocess.run(
        [sys.executable, "scripts/server.py", "--validate-only"],
        capture_output=True, text=True, env=env, timeout=5,
    )
    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "JSON_INSPECTOR_DATA_SOURCES" in result.stderr


def test_server_validate_only_succeeds(tmp_path):
    ds = tmp_path / "data_sources.json"
    ds.write_text("{}")
    env = {**os.environ, "JSON_INSPECTOR_DATA_SOURCES": str(ds)}
    result = subprocess.run(
        [sys.executable, "scripts/server.py", "--validate-only"],
        capture_output=True, text=True, env=env, timeout=5,
    )
    assert result.returncode == 0
    assert "configuration OK" in result.stderr
