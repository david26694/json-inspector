import subprocess
import sys
import os
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
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    return result


def test_validate_missing_data_sources_fails():
    r = _run_validate({"JSON_INSPECTOR_DATA_SOURCES": None})
    assert r.returncode != 0
    assert "JSON_INSPECTOR_DATA_SOURCES" in r.stdout + r.stderr


def test_validate_bad_json_fails(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    r = _run_validate({"JSON_INSPECTOR_DATA_SOURCES": str(bad)})
    assert r.returncode != 0
    assert "invalid json" in r.stdout.lower() + r.stderr.lower()


def test_validate_good_config_passes(tmp_path):
    ds = tmp_path / "data_sources.json"
    ds.write_text('{"my.table": {"fields": [{"name": "id", "type": "INTEGER", "description": "pk", "example": 1}]}}')
    r = _run_validate({"JSON_INSPECTOR_DATA_SOURCES": str(ds)})
    assert r.returncode == 0
    assert "OK" in r.stdout or "ok" in r.stdout.lower()


def test_validate_mcp_json_check(tmp_path):
    """--check-mcp flag reports missing .mcp.json as a warning, not error."""
    ds = tmp_path / "data_sources.json"
    ds.write_text("{}")
    r = _run_validate(
        {"JSON_INSPECTOR_DATA_SOURCES": str(ds)},
        extra_args=["--check-mcp", "--mcp-dir", str(tmp_path)],
    )
    assert r.returncode == 0
    assert "mcp" in r.stdout.lower() or "warn" in r.stdout.lower()
