"""Parseo, validación y marcado de tasks.md.

Formato esperado (checklist anidado; las hojas son las tareas ejecutables):

    - [ ] 1. Modelo de datos
      - [ ] 1.1 Dataclass Pedido con validación de montos
        - Detalle de qué hacer
        - _Requisitos: 1.1, 1.2_
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

TASK_LINE = re.compile(r"^(\s*)- \[([ xX])\] (\d+(?:\.\d+)*)\.?\s+(.+?)\s*$")
REFS_LINE = re.compile(r"_Requisitos?:\s*([\d.,\s]+)_", re.IGNORECASE)
CHECKBOX = re.compile(r"^(\s*- )\[[ xX]\]", re.MULTILINE)


@dataclass
class Task:
    task_id: str
    title: str
    line: int
    indent: int
    done: bool
    refs: list[str] = field(default_factory=list)
    children: list[str] = field(default_factory=list)

    @property
    def is_leaf(self) -> bool:
        return not self.children


def normalize(text: str) -> str:
    """Texto con todas las casillas sin marcar: marcar tareas no invalida la aprobación."""
    return CHECKBOX.sub(r"\1[ ]", text)


def parse(text: str) -> dict[str, Task]:
    tasks: dict[str, Task] = {}
    stack: list[Task] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        match = TASK_LINE.match(line)
        if match:
            indent, mark, task_id, title = match.groups()
            task = Task(task_id, title, lineno, len(indent), mark.lower() == "x")
            while stack and stack[-1].indent >= task.indent:
                stack.pop()
            if stack:
                stack[-1].children.append(task_id)
            stack.append(task)
            tasks[task_id] = task
            continue
        refs = REFS_LINE.search(line)
        if refs and stack:
            stack[-1].refs.extend(r.strip().rstrip(".") for r in refs.group(1).split(",") if r.strip())
    return tasks


def _covers(ref: str, criterion: str) -> bool:
    return ref == criterion or criterion.startswith(ref + ".")


def validate(text: str, criteria: set[str]) -> list[str]:
    tasks = parse(text)
    if not tasks:
        return ["No hay tareas: usa líneas '- [ ] 1.1 <descripción>'."]
    errors: list[str] = []
    all_refs: list[str] = []
    for task in tasks.values():
        if task.is_leaf and not task.refs:
            errors.append(f"Tarea {task.task_id} (línea {task.line}) sin '_Requisitos: X.Y_'.")
        for ref in task.refs:
            if not any(_covers(ref, c) for c in criteria):
                errors.append(f"Tarea {task.task_id} referencia '{ref}', que no existe en requirements.md.")
        all_refs.extend(task.refs)
    uncovered = sorted(c for c in criteria if not any(_covers(r, c) for r in all_refs))
    if uncovered:
        errors.append("Criterios sin ninguna tarea que los cubra: " + ", ".join(uncovered))
    return errors


def next_pending(text: str) -> Task | None:
    return next((t for t in parse(text).values() if t.is_leaf and not t.done), None)


def progress(text: str) -> tuple[int, int]:
    leaves = [t for t in parse(text).values() if t.is_leaf]
    return sum(t.done for t in leaves), len(leaves)


def mark_done(text: str, task_id: str) -> str:
    """Marca la tarea y, en cascada, los padres cuyas subtareas quedaron todas hechas."""
    tasks = parse(text)
    lines = text.splitlines(keepends=True)
    _check(lines, tasks[task_id])
    for parent in _ancestors(tasks, task_id):
        if all(tasks[c].done for c in parent.children):
            _check(lines, parent)
    return "".join(lines)


def _check(lines: list[str], task: Task) -> None:
    lines[task.line - 1] = re.sub(r"- \[[ xX]\]", "- [x]", lines[task.line - 1], count=1)
    task.done = True


def _ancestors(tasks: dict[str, Task], task_id: str) -> list[Task]:
    parts = task_id.split(".")
    ids = [".".join(parts[:i]) for i in range(len(parts) - 1, 0, -1)]
    return [tasks[i] for i in ids if i in tasks]
