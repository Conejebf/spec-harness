---
name: spec-tasks
description: Fase 3 del flujo de specs. Con design.md aprobado, genera specs/<feature>/tasks.md con tareas atómicas en checklist, cada una con los requisitos que cubre, y se detiene a pedir aprobación.
argument-hint: <feature>
disable-model-invocation: true
---

# Fase 3 · Tareas

Feature: `$ARGUMENTS`

## Pasos

1. **Compuerta.** `python .claude/spec_harness/cli.py status <feature>`: `design.md` debe estar
   `aprobada`. Si no, detente.
2. **Leer** `requirements.md` y `design.md` de la feature.
3. **Escribir** `specs/<feature>/tasks.md` con [plantilla.md](plantilla.md):
   - Checklist anidado: `- [ ] 1. Grupo` y subtareas `  - [ ] 1.1 Tarea`. Las hojas son las tareas
     ejecutables; un grupo se marca solo cuando todas sus subtareas están hechas.
   - **Atómicas:** cada hoja se hace en una sesión corta, toca pocos archivos y deja los tests en verde.
     Si una tarea dice "y", probablemente son dos.
   - **Prueba primero:** cada hoja que agrega comportamiento incluye escribir o ajustar su prueba.
   - **Orden incremental:** de adentro hacia afuera (modelos → lógica → adaptadores → entrada), sin
     tareas que dependan de una posterior. Nada queda sin conectar al final.
   - Cada hoja lleva una línea `_Requisitos: 1.1, 2.3_` con los criterios que cubre. Todos los criterios
     de requirements.md deben quedar cubiertos (el hook lo valida).
   - Solo tareas de código y pruebas. Nada de "desplegar", "recoger feedback" o "documentar en Confluence".
4. **Validar:** `python .claude/spec_harness/cli.py check <feature> tasks`.
5. **DETENTE.** Muestra el número de tareas y el orden a grandes rasgos, y pide aprobación: el usuario
   responde **`aprobado`**. Después se ejecutan una por una con `/spec-run <feature>`.
