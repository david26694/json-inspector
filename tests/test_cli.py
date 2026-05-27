# tests/test_cli.py
import subprocess, sys, json, os, pytest
from pathlib import Path

_FIXTURES = Path(__file__).parent / "fixtures"
SAMPLES = str(_FIXTURES / "sample_records.json")
SCHEMAS = str(_FIXTURES / "schemas.json")

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

def test_get_field_value_bad_path_exits_nonzero():
    r = _run("get-field-value", "trendy.catalog.products", "nonexistent.path")
    assert r.returncode != 0

def test_missing_env_exits_nonzero():
    env = {k: v for k, v in os.environ.items()
           if k not in ("JSON_INSPECTOR_SAMPLES", "JSON_INSPECTOR_SCHEMAS")}
    result = subprocess.run(
        [sys.executable, "scripts/cli.py", "list-tables"],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode != 0
    assert "JSON_INSPECTOR_SAMPLES" in result.stderr or "JSON_INSPECTOR_SCHEMAS" in result.stderr
