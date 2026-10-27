---
name: spec-design
description: Fase 2 del flujo de specs. Con requirements.md aprobado, genera specs/<feature>/design.md y pide aprobación con opciones para hacer clic.
argument-hint: <feature>
disable-model-invocation: true
---

Feature: `$ARGUMENTS`

Lee `.claude/spec_harness/fases/design.md` y síguelo al pie de la letra. Al aprobarse, el hook te indica
el archivo de la siguiente fase: continúa con él en el mismo turno.
