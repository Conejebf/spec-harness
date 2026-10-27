---
name: spec-tasks
description: Fase 3 del flujo de specs. Con design.md aprobado, genera specs/<feature>/tasks.md y pide aprobación ofreciendo correr una tarea o todas.
argument-hint: <feature>
disable-model-invocation: true
---

Feature: `$ARGUMENTS`

Lee `.claude/spec_harness/fases/tasks.md` y síguelo al pie de la letra. Al aprobarse, el hook te indica
cómo seguir.
