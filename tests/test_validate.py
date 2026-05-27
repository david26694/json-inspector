import subprocess
import sys
import os
import json
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


def test_validate_missing_samples_fails():
    r = _run_validate({"JSON_INSPECTOR_SAMPLES": None, "JSON_INSPECTOR_SCHEMAS": None})
    assert r.returncode != 0
    assert "JSON_INSPECTOR_SAMPLES" in r.stdout + r.stderr


def test_validate_bad_json_fails(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    good = tmp_path / "good.json"
    good.write_text("{}")
    r = _run_validate(
        {
            "JSON_INSPECTOR_SAMPLES": str(bad),
            "JSON_INSPECTOR_SCHEMAS": str(good),
        }
    )
    assert r.returncode != 0
    assert "invalid json" in r.stdout.lower() + r.stderr.lower()


def test_validate_good_config_passes(tmp_path):
    samples = tmp_path / "s.json"
    schemas = tmp_path / "sc.json"
    samples.write_text('{"my.table": {"id": 1}}')
    schemas.write_text(
        '{"my.table": [{"name": "id", "type": "INTEGER", "description": "pk"}]}'
    )
    r = _run_validate(
        {
            "JSON_INSPECTOR_SAMPLES": str(samples),
            "JSON_INSPECTOR_SCHEMAS": str(schemas),
        }
    )
    assert r.returncode == 0
    assert "OK" in r.stdout or "ok" in r.stdout.lower()


def test_validate_mcp_json_check(tmp_path):
    """--check-mcp flag reports missing .mcp.json as a warning, not error."""
    samples = tmp_path / "s.json"
    schemas = tmp_path / "sc.json"
    samples.write_text("{}")
    schemas.write_text("{}")
    r = _run_validate(
        {
            "JSON_INSPECTOR_SAMPLES": str(samples),
            "JSON_INSPECTOR_SCHEMAS": str(schemas),
        },
        extra_args=["--check-mcp", "--mcp-dir", str(tmp_path)],
    )
    # Missing .mcp.json is a warning, not failure
    assert r.returncode == 0
    assert "mcp" in r.stdout.lower() or "warn" in r.stdout.lower()
