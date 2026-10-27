---
name: spec
description: Punto de entrada único del flujo de specs. Retoma una feature donde se quedó (requisitos, diseño, tareas o ejecución) o empieza una nueva.
argument-hint: <feature> [descripción si es nueva]
disable-model-invocation: true
---

Argumentos: `$ARGUMENTS` → feature y, si es nueva, la descripción.

1. Corre `python .claude/spec_harness/cli.py status <feature>` (si la feature no existe, es nueva).
2. Según el estado, lee y sigue el archivo correspondiente de `.claude/spec_harness/fases/`:
   - nueva, o `requirements.md` falta / en borrador / desactualizada → `requirements.md`
   - `design.md` falta / en borrador / desactualizada → `design.md`
   - `tasks.md` falta / en borrador / desactualizada → `tasks.md`
   - todo aprobado con tareas pendientes → `run.md`
   - todo hecho → repórtalo y termina.
   Si una fase existe en borrador y está completa, no la reescribas: resúmela y pide aprobación con las
   opciones que indica su archivo.
3. Al aprobarse cada fase, el hook te indica el archivo siguiente: continúa con él en el mismo turno.
