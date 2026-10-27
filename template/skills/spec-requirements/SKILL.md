---
name: spec-requirements
description: Fase 1 del flujo de specs. Genera specs/<feature>/requirements.md con historias de usuario y criterios EARS en español, y pide aprobación con opciones para hacer clic.
argument-hint: <feature-en-kebab-case> [descripción de lo que se quiere]
disable-model-invocation: true
---

Argumentos: `$ARGUMENTS` → la primera palabra es la feature; el resto, la descripción.

Lee `.claude/spec_harness/fases/requirements.md` y síguelo al pie de la letra. Al aprobarse cada fase,
el hook te indica el archivo de la siguiente (`fases/design.md`, `fases/tasks.md`, `fases/run.md`):
continúa con él en el mismo turno.
