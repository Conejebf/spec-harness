# Fase 3 · Tareas

Entrada: nombre de la feature.

## Pasos

1. **Compuerta.** `python .claude/spec_harness/cli.py status <feature>`: `design.md` debe estar
   `aprobada`. Si no, detente.
2. **Leer** `requirements.md` y `design.md` de la feature.
3. **Escribir** `specs/<feature>/tasks.md` con [plantilla-tasks.md](plantilla-tasks.md):
   - Checklist anidado: `- [ ] 1. Grupo` y subtareas `  - [ ] 1.1 Tarea`. Las hojas son las tareas
     ejecutables; un grupo se marca solo cuando todas sus subtareas están hechas.
   - **Atómicas:** cada hoja se hace en una sesión corta, toca pocos archivos y deja los tests en verde.
     Si una tarea dice "y", probablemente son dos.
   - **Prueba primero:** cada hoja que agrega comportamiento incluye escribir o ajustar su prueba.
   - **Orden incremental:** de adentro hacia afuera (modelos → lógica → adaptadores → entrada), sin
     tareas que dependan de una posterior. Las tareas se ejecutan **siempre en este orden**.
   - Cada hoja lleva una línea `_Requisitos: 1.1, 2.3_` con los criterios que cubre. Todos los criterios
     de requirements.md deben quedar cubiertos (el hook lo valida).
   - Solo tareas de código y pruebas. Nada de "desplegar" o "recoger feedback".
4. **Validar:** `python .claude/spec_harness/cli.py check <feature> tasks`.
5. **Pedir aprobación con un clic.** Muestra el número de tareas y el orden a grandes rasgos, y pregunta
   con AskUserQuestion, `header` = nombre de la feature, con estas opciones exactas:
   - `Aprobar y correr una tarea`
   - `Aprobar y correr todas (solo pregunto si me atoro)`
   - `Aprobar y parar aquí`
   - `Pedir cambios`

   El hook registra la aprobación y la autorización para correr, y te dice qué sigue.
