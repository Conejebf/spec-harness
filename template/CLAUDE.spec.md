## Desarrollo guiado por specs

Las funcionalidades nuevas siguen el flujo de `specs/<feature>/`, con aprobación del usuario entre fases:

1. `/spec-requirements <feature> <descripción>` → `requirements.md` (historias + criterios EARS)
2. `/spec-design <feature>` → `design.md`
3. `/spec-tasks <feature>` → `tasks.md` (checklist; cada tarea cita sus requisitos)
4. `/spec-run <feature>` → implementa UNA tarea, corre tests, la marca y se detiene

Reglas:
- Al terminar una fase, detente y pide aprobación. El usuario aprueba respondiendo `aprobado`; tú
  nunca apruebas (el comando `approve` y `.state.json` están bloqueados para ti).
- No escribas `design.md` ni `tasks.md` sin la fase anterior aprobada; un hook lo impide.
- Durante `/spec-run`, implementa solo la tarea en curso. Ciérrala con
  `python .claude/spec_harness/cli.py done <feature>` (corre tests y marca `tasks.md`) o pausa con
  `... pause <feature> "<motivo>"`. No marques casillas a mano ni hagas commit.
- Si el diseño no alcanza para la tarea, pausa y propón el cambio a la spec en vez de improvisar.
- El steering (`.claude/steering/`) se carga al iniciar sesión; actualízalo con `/spec-steering`.
- Estado de todo: `python .claude/spec_harness/cli.py status`.
