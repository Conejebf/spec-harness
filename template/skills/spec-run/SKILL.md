---
name: spec-run
description: Modo de ejecución del flujo de specs. Toma UNA tarea de specs/<feature>/tasks.md (la siguiente pendiente o la indicada), la implementa, corre los tests, la marca como hecha y se detiene para revisión.
argument-hint: <feature> [id-de-tarea]
disable-model-invocation: true
---

# Ejecutar una tarea

Argumentos: `$ARGUMENTS` → feature y, opcionalmente, el id de la tarea (`2.1`).

## Pasos

1. **Tomar la tarea:** `python .claude/spec_harness/cli.py start <feature> [id]`.
   Imprime la tarea, su detalle y los requisitos que cubre. Si falla (specs sin aprobar, otra tarea en
   curso, todo hecho), dile al usuario y detente.
2. **Contexto mínimo.** Lee los criterios citados en `requirements.md` y la parte de `design.md` del
   componente que toca la tarea. No leas ni hagas nada de otras tareas.
3. **Prueba primero.** Escribe o ajusta la prueba que demuestra los criterios de la tarea y comprueba
   que falla por la razón correcta.
4. **Implementar** solo lo que pide esta tarea, siguiendo el diseño. Si el diseño resulta inviable o
   incompleto, NO improvises: corre `cli.py pause <feature> "<motivo>"` y explícale al usuario qué cambiar
   en el diseño.
   - Cada vez que editas un archivo, el hook corre su lint y sus tests relacionados; si te devuelve
     errores, corrígelos antes de seguir.
5. **Cerrar:** `python .claude/spec_harness/cli.py done <feature>`. Corre la suite completa y, solo si
   pasa, marca la tarea `[x]` en `tasks.md` (y el grupo si quedó completo). Nunca marques casillas a mano:
   está bloqueado.
6. **DETENTE para revisión.** Reporta en pocas líneas:
   - Qué se hizo y en qué archivos (`ruta:línea`).
   - Qué criterios quedan cubiertos y cómo lo prueba el test.
   - Resultado de los tests.
   - Lo que el usuario debería revisar o decidir.
   No hagas commit ni empieces la siguiente tarea: el usuario corre `/spec-run <feature>` de nuevo.

Un hook impide cerrar el turno con una tarea en curso: siempre termina en `done` o en `pause`.
