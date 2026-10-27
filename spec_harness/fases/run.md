# Ejecución de tareas

Entrada: nombre de la feature. Las tareas se corren **siempre en orden**: `start` solo acepta la
siguiente pendiente.

Hay dos modos, y los elige el usuario con un clic (nunca tú):
- **Una tarea:** haces la siguiente, la cierras y preguntas qué sigue.
- **Todas (modo automático):** haces una tras otra sin preguntar. Solo te detienes si te atoras.
  Un hook no te deja terminar el turno mientras queden tareas en este modo.

## Ciclo por tarea

1. **Tomar la tarea:** `python .claude/spec_harness/cli.py start <feature>`.
   - Si responde "Sin autorización", pregunta con AskUserQuestion, `header` = nombre de la feature, con
     estas opciones exactas y espera la elección:
     - `Correr la siguiente tarea`
     - `Correr todas las restantes (solo pregunto si me atoro)`
     - `Parar aquí`
   - Si falla por otra razón (specs sin aprobar, todo hecho), díselo al usuario y detente.
2. **Contexto mínimo.** Lee los criterios citados en `requirements.md` y la parte de `design.md` del
   componente que toca la tarea. No hagas nada de otras tareas.
3. **Prueba primero.** Escribe o ajusta la prueba que demuestra los criterios de la tarea y comprueba
   que falla por la razón correcta.
4. **Implementar** solo lo que pide la tarea, siguiendo el diseño. Cada vez que editas un archivo, el
   hook corre su lint y sus tests relacionados; si te devuelve errores, corrígelos.
5. **Cerrar:** `python .claude/spec_harness/cli.py done <feature>`. Corre la suite completa y, solo si
   pasa, marca la tarea `[x]` en `tasks.md`. Nunca marques casillas a mano: está bloqueado.
6. **Qué sigue** — lo dice la salida de `done`:
   - **Modo automático:** vuelve al paso 1 con la siguiente tarea, sin preguntar. Al final, reporta todo.
   - **Una tarea:** reporta en pocas líneas (qué se hizo con `ruta:línea`, criterios cubiertos y cómo los
     prueba el test, resultado de tests) y pregunta con las opciones del paso 1.
   - **Sin tareas pendientes:** reporta el resultado final.

## Si te atoras

Te atoras si los tests no pasan después de 3 intentos de corrección, si el diseño resulta inviable o
incompleto para la tarea, o si necesitas una decisión de negocio. Entonces NO improvises:

1. `python .claude/spec_harness/cli.py pause <feature> "<motivo>"`. Esto también apaga el modo automático.
2. Explica el problema y pregunta con AskUserQuestion, `header` = nombre de la feature:
   - `Reintentar la tarea`
   - `Reintentar y seguir con todas`
   - `Ajustar la spec`. Propón el cambio a requirements/design/tasks; al editarlo, esa fase y las
     siguientes vuelven a pedir aprobación.
   - `Parar aquí`

No hagas commit en ningún momento: los cambios quedan para revisión del usuario.
