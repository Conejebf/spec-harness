## Desarrollo guiado por specs

Las funcionalidades nuevas siguen el flujo de `specs/<feature>/`. Las instrucciones de cada fase están en
`.claude/spec_harness/fases/` (requirements, design, tasks, run).

1. Requisitos → `requirements.md` (historias + criterios EARS)
2. Diseño → `design.md`
3. Tareas → `tasks.md` (checklist en orden; cada tarea cita sus requisitos)
4. Ejecución → una tarea o todas, siempre en orden

Reglas:
- Al terminar una fase, pide aprobación con AskUserQuestion usando las opciones exactas de su archivo.
  Un hook registra lo que el usuario elige y te dice qué sigue; si aprobó y eligió seguir, continúa con
  la siguiente fase en el mismo turno. Tú nunca apruebas (`approve` y `.state.json` están bloqueados).
- No escribas `design.md` ni `tasks.md` sin la fase anterior aprobada; un hook lo impide.
- Solo corres tareas con autorización del usuario (un clic: una tarea o todas). En modo "todas" no
  preguntes entre tareas; detente solo si te atoras (`pause`) y entonces pregunta con opciones.
- Cierra cada tarea con `python .claude/spec_harness/cli.py done <feature>` (tests + marca). No marques
  casillas a mano ni hagas commit.
- Si el diseño no alcanza para la tarea, pausa y propón el cambio a la spec en vez de improvisar.
- El steering (`.claude/steering/`) se carga al iniciar sesión; actualízalo con `/spec-steering`.
- Estado: `python .claude/spec_harness/cli.py status`. Retomar cualquier feature: `/spec <feature>`.
