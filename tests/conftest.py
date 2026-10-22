from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

REQUIREMENTS = """# Requisitos: conteo

## Introducción

Cuenta pedidos.

## Requisitos

### Requisito 1: Contar pedidos

**Historia de usuario:** Como analista, quiero contar pedidos, para medir volumen.

#### Criterios de aceptación

1. CUANDO se pasa una lista de pedidos, EL SISTEMA DEBERÁ devolver cuántos hay.
2. SI la lista está vacía, ENTONCES EL SISTEMA DEBERÁ devolver 0.

### Requisito 2: Ignorar cancelados

**Historia de usuario:** Como analista, quiero excluir cancelados, para no inflar el conteo.

#### Criterios de aceptación

1. EL SISTEMA DEBERÁ excluir los pedidos con estado 'cancelado'.
"""

DESIGN = """# Diseño: conteo

## Resumen
Una función pura.

## Arquitectura
Un módulo.

## Componentes e interfaces
`conteo.contar(pedidos) -> int` — cubre 1.1, 1.2, 2.1

## Modelos de datos
Lista de dicts con `estado`.

## Manejo de errores
Lista vacía devuelve 0 (1.2).

## Estrategia de pruebas
pytest sobre `contar`.
"""

TASKS = """# Tareas: conteo

- [ ] 1. Conteo
  - [ ] 1.1 Función contar con lista vacía y normal
    - Prueba primero en tests/test_conteo.py
    - _Requisitos: 1.1, 1.2_
  - [ ] 1.2 Excluir cancelados
    - _Requisitos: 2.1_
"""


@pytest.fixture
def project(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def feature_dir(project: Path) -> Path:
    folder = project / "specs" / "conteo"
    folder.mkdir(parents=True)
    return folder


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run_hook(event: str, payload: dict, project: Path) -> dict | None:
    proc = subprocess.run(
        [sys.executable, str(REPO / "spec_harness" / "hooks.py"), event],
        input=json.dumps({"cwd": str(project), **payload}).encode("utf-8"),
        capture_output=True, env={**_env(), "CLAUDE_PROJECT_DIR": str(project)}, check=True,
    )
    out = proc.stdout.decode("utf-8").strip()
    return json.loads(out) if out else None


def run_cli(args: list[str], project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO / "spec_harness" / "cli.py"), *args],
        capture_output=True, text=True, encoding="utf-8", check=False,
        env={**_env(), "CLAUDE_PROJECT_DIR": str(project)}, cwd=project,
    )


def _env() -> dict:
    return dict(os.environ)
