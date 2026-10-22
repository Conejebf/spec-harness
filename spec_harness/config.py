"""Configuración: defaults + .claude/spec-harness.toml del proyecto."""

from __future__ import annotations

import copy
import os
import tomllib
from pathlib import Path

CONFIG_REL = Path(".claude") / "spec-harness.toml"

DEFAULTS: dict = {
    "paths": {"specs_dir": "specs", "steering_dir": ".claude/steering"},
    "tests": {
        "full_cmd": "python -m pytest -q",
        "related_cmd": "python -m pytest -q -x {tests}",
        "related_patterns": [
            "tests/test_{stem}.py",
            "{dir}/test_{stem}.py",
            "{dir}/tests/test_{stem}.py",
        ],
        "timeout": 300,
    },
    "lint": {
        "python_cmd": "ruff check {file}",
        "sql_cmd": "sqlfluff lint {file} --dialect redshift --nocolor",
        "timeout": 60,
    },
    "approval": {"phrases": ["aprobado", "aprobada", "apruebo", "approved", "lgtm"]},
    "stop": {"max_retries": 3},
    "steering": {"max_chars": 30000},
}


def project_root(cwd: str | None = None) -> Path:
    """Instalado en <proyecto>/.claude/spec_harness/ la raíz es fija; si no, env o cwd."""
    package = Path(__file__).resolve().parent
    if package.parent.name == ".claude":
        return package.parent.parent
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(env or cwd or os.getcwd()).resolve()


def _merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load(root: Path) -> dict:
    path = root / CONFIG_REL
    if not path.is_file():
        return copy.deepcopy(DEFAULTS)
    with path.open("rb") as fh:
        return _merge(DEFAULTS, tomllib.load(fh))


def specs_dir(root: Path, cfg: dict) -> Path:
    return root / cfg["paths"]["specs_dir"]


def steering_dir(root: Path, cfg: dict) -> Path:
    return root / cfg["paths"]["steering_dir"]
