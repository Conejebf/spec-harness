---
name: spec-status
description: Muestra el estado de las specs (fases aprobadas, desactualizadas, avance de tareas, tarea en curso).
argument-hint: [feature]
disable-model-invocation: true
---

Corre `python .claude/spec_harness/cli.py status $ARGUMENTS` y muestra el resultado. Después indica el
siguiente paso de cada feature:

- falta o borrador de requirements → `/spec-requirements <feature>`, o responder `aprobado`
- design pendiente → `/spec-design <feature>`
- tasks pendiente → `/spec-tasks <feature>`
- tareas pendientes → `/spec-run <feature>`
- algo "desactualizada" → revisar el cambio y volver a aprobar esa fase
