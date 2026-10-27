---
name: spec-status
description: Muestra el estado de las specs (fases aprobadas, desactualizadas, avance de tareas, tarea en curso, modo de ejecución).
argument-hint: [feature]
disable-model-invocation: true
---

Corre `python .claude/spec_harness/cli.py status $ARGUMENTS` y muestra el resultado. Para cada feature con
algo pendiente, indica que `/spec <feature>` la retoma justo donde se quedó.
