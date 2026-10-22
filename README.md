# Spec Harness para Claude Code

Desarrollo guiado por specs, al estilo de Kiro: **requisitos → diseño → tareas → ejecución**, con
una compuerta de aprobación tuya entre cada fase y una tarea a la vez en la ejecución. Las reglas no
dependen de que Claude "se acuerde": las hacen cumplir hooks deterministas.

Es independiente de cualquier otro harness y solo se instala en un proyecto cuando tú lo pides.

## Instalar / desinstalar

```bash
python install.py "C:/ruta/al/proyecto"
python install.py "C:/ruta/al/proyecto" --uninstall
```

Después de instalar, **reinicia la sesión de Claude Code** en ese proyecto para que cargue hooks y
skills. Reinstalar es idempotente: actualiza código y skills sin pisar tu config, tu steering, tus
specs ni hooks ajenos. Desinstalar quita código, skills, hooks y el bloque de `CLAUDE.md`, y conserva
`specs/`, `.claude/steering/` y `.claude/spec-harness.toml`.

Qué deja en el proyecto:

| Ruta | Qué es |
|---|---|
| `.claude/spec_harness/` | Código (CLI + hooks), solo librería estándar de Python 3.11+ |
| `.claude/skills/spec-*/` | Los slash commands y sus plantillas |
| `.claude/steering/{product,tech,structure}.md` | Contexto permanente (plantillas si no existían) |
| `.claude/spec-harness.toml` | Config: comandos de tests y lint, frases de aprobación |
| `.claude/settings.json` | Hooks, fusionados con los que ya tengas |
| `CLAUDE.md` | Bloque `<!-- spec-harness:start/end -->` con las reglas del flujo |
| `specs/<feature>/` | requirements.md, design.md, tasks.md y `.state.json` (se crean al usarlo) |

## Flujo

```
/spec-steering                         (una vez) redacta product/tech/structure.md
/spec-requirements <feature> <qué>     → requirements.md  → tú: "aprobado"
/spec-design <feature>                 → design.md        → tú: "aprobado"
/spec-tasks <feature>                  → tasks.md         → tú: "aprobado"
/spec-run <feature> [id]               → implementa UNA tarea, corre tests, la marca, se detiene
/spec-run <feature>                    → la siguiente… (tú revisas entre cada una)
/spec-status [feature]                 → dónde va cada spec
```

### 1. Requisitos — `/spec-requirements`
Historias de usuario (`Como <rol>, quiero <capacidad>, para <beneficio>`) y criterios de aceptación
en **EARS en español**. El criterio N del requisito R se identifica como `R.N`.

| Tipo | Forma |
|---|---|
| Ubicuo | `EL SISTEMA DEBERÁ …` |
| Evento | `CUANDO …, EL SISTEMA DEBERÁ …` |
| Estado | `MIENTRAS …, EL SISTEMA DEBERÁ …` |
| No deseado | `SI …, ENTONCES EL SISTEMA DEBERÁ …` |
| Opcional | `DONDE …, EL SISTEMA DEBERÁ …` |

El sujeto puede ser concreto (`EL REPORTE DEBERÁ`, `LA API DEBERÁ`). Un criterio fuera de EARS no
pasa la validación.

### 2. Diseño — `/spec-design`
Secciones obligatorias: Resumen, Arquitectura, Componentes e interfaces, Modelos de datos, Manejo de
errores, Estrategia de pruebas. Cada componente cita los criterios que cubre (`cubre 1.2`).

### 3. Tareas — `/spec-tasks`
Checklist anidado. Las hojas son las tareas ejecutables y cada una lleva `_Requisitos: 1.1, 2.3_`.
Se valida que cada referencia exista y que **todos** los criterios queden cubiertos por alguna tarea.

### 4. Ejecución — `/spec-run`
Toma la siguiente tarea pendiente (o la que indiques), escribe primero la prueba, implementa, cierra
con `cli.py done` (corre la suite completa y solo si pasa marca `[x]`, en cascada al grupo) y se
detiene a reportar. No hace commit ni avanza sola a la siguiente tarea.

## Aprobaciones

Al terminar una fase, Claude se detiene. **Apruebas respondiendo exactamente `aprobado`** (o
`aprobada`, `apruebo`, `lgtm`; con varias specs pendientes, `aprobado <feature>`). Un mensaje como
"aprobado pero cambia X" **no** aprueba: es una petición de cambios.

- La aprobación la registra el hook `UserPromptSubmit` a partir de **tu** mensaje. Claude no puede
  aprobar: el comando `approve` y cualquier escritura a `.state.json` están bloqueados para él.
- Cada aprobación guarda el hash del documento y del anterior en la cadena. Si editas un
  `requirements.md` ya aprobado, `design` y `tasks` quedan **desactualizados** solos y hay que
  reaprobarlos. Marcar casillas en `tasks.md` no invalida nada.
- También puedes aprobar desde tu terminal:
  `python .claude/spec_harness/cli.py approve <feature> <requirements|design|tasks>`.

## Hooks

| Evento | Qué hace |
|---|---|
| `SessionStart` | Inyecta `.claude/steering/*.md` (product, tech y structure primero) y el estado de las specs |
| `UserPromptSubmit` | Registra tu aprobación cuando respondes `aprobado` |
| `PreToolUse` | Compuerta de fase (no hay design sin requirements aprobado, ni tasks sin design); bloquea autoaprobarse, tocar `.state.json` y marcar casillas a mano |
| `PostToolUse` | Spec editada → la valida (EARS, secciones, cobertura). Código editado → lint del archivo (ruff / sqlfluff) y sus tests relacionados (`tests/test_<nombre>.py`); si fallan, Claude debe corregir |
| `Stop` | No deja cerrar el turno con una tarea en curso: hay que terminarla (`done`) o pausarla (`pause`). Se rinde tras `max_retries` y te avisa |

Lint o tests que no estén instalados se omiten sin bloquear.

## CLI

```bash
python .claude/spec_harness/cli.py status [feature]
python .claude/spec_harness/cli.py check <feature> <fase>
python .claude/spec_harness/cli.py start <feature> [id]      # lo usa /spec-run
python .claude/spec_harness/cli.py done <feature>            # tests + marcar tasks.md
python .claude/spec_harness/cli.py pause <feature> "<motivo>"
python .claude/spec_harness/cli.py approve <feature> <fase>  # solo tú
```

## Configuración — `.claude/spec-harness.toml`

```toml
[tests]
full_cmd = "python -m pytest -q"                    # la corre `done`
related_cmd = "python -m pytest -q -x {tests}"       # la corre el hook al editar un .py
related_patterns = ["tests/test_{stem}.py", "{dir}/test_{stem}.py", "{dir}/tests/test_{stem}.py"]

[lint]
python_cmd = "ruff check {file}"
sql_cmd = "sqlfluff lint {file} --dialect redshift --nocolor"

[approval]
phrases = ["aprobado", "aprobada", "apruebo", "approved", "lgtm"]
```

## Desarrollo

```bash
python -m pytest -q     # 25 tests: validadores, estado, CLI, los 5 hooks e instalador
ruff check .
```
