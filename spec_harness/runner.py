"""Ejecuta lint y tests configurados en spec-harness.toml."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

PYTEST_NO_TESTS = 5
TAIL_LINES = 60


@dataclass
class Result:
    label: str
    ok: bool
    output: str = ""
    skipped: bool = False

    def tail(self) -> str:
        lines = self.output.strip().splitlines()
        return "\n".join(lines[-TAIL_LINES:])


def _tool_available(cmd: str) -> bool:
    first = cmd.split()[0] if cmd.strip() else ""
    return bool(first) and shutil.which(first) is not None


def run(label: str, cmd: str, root: Path, timeout: int) -> Result:
    if not _tool_available(cmd):
        return Result(label, True, f"'{cmd.split()[0] if cmd else ''}' no está instalado; se omite.", skipped=True)
    try:
        proc = subprocess.run(
            cmd, check=False, shell=True, cwd=root, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return Result(label, False, f"Se agotó el tiempo ({timeout} s): {cmd}")
    output = (proc.stdout or "") + (proc.stderr or "")
    ok = proc.returncode == 0 or (label.startswith("tests") and proc.returncode == PYTEST_NO_TESTS)
    return Result(label, ok, output)


def _quote(path: Path) -> str:
    return f'"{path.as_posix()}"'


def related_tests(path: Path, root: Path, cfg: dict) -> list[Path]:
    rel = path.resolve().relative_to(root.resolve())
    if rel.name.startswith("test_") and rel.suffix == ".py":
        return [path]
    found = []
    for pattern in cfg["tests"]["related_patterns"]:
        candidate = root / pattern.format(stem=rel.stem, dir=rel.parent.as_posix())
        if candidate.is_file() and candidate not in found:
            found.append(candidate)
    return found


def lint_file(path: Path, root: Path, cfg: dict) -> Result | None:
    key = {".py": "python_cmd", ".sql": "sql_cmd"}.get(path.suffix.lower())
    template = cfg["lint"].get(key) if key else None
    if not template:
        return None
    return run(f"lint {path.name}", template.format(file=_quote(path)), root, cfg["lint"]["timeout"])


def test_related(path: Path, root: Path, cfg: dict) -> Result | None:
    if path.suffix.lower() != ".py":
        return None
    tests = related_tests(path, root, cfg)
    if not tests:
        return None
    cmd = cfg["tests"]["related_cmd"].format(tests=" ".join(_quote(t) for t in tests))
    return run("tests relacionados", cmd, root, cfg["tests"]["timeout"])


def test_full(root: Path, cfg: dict) -> Result:
    return run("tests (suite completa)", cfg["tests"]["full_cmd"], root, cfg["tests"]["timeout"])
