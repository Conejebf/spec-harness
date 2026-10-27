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
| `.claude/spec_harness/` | Código (CLI + hooks) e instrucciones de cada fase (`fases/`); solo librería estándar de Python 3.11+ |
| `.claude/skills/spec*/` | Los slash commands (atajos a las fases) |
| `.claude/steering/{product,tech,structure}.md` | Contexto permanente (plantillas si no existían) |
| `.claude/spec-harness.toml` | Config: comandos de tests y lint, frases de aprobación |
| `.claude/settings.json` | Hooks, fusionados con los que ya tengas |
| `CLAUDE.md` | Bloque `<!-- spec-harness:start/end -->` con las reglas del flujo |
| `specs/<feature>/` | requirements.md, design.md, tasks.md y `.state.json` (se crean al usarlo) |

## Flujo: escribes un comando, lo demás es con clics

```
/spec-steering                       (una vez) redacta product/tech/structure.md
/spec <feature> <qué se quiere>      empieza una feature, o retoma la que ya existe donde se quedó
```

Al terminar cada fase, Claude te pregunta con opciones y **tú haces clic**; no tienes que escribir el
siguiente comando:

| Al terminar… | Opciones |
|---|---|
| Requisitos | **Aprobar y seguir con el diseño** · Aprobar y parar aquí · Pedir cambios |
| Diseño | **Aprobar y seguir con las tareas** · Aprobar y parar aquí · Pedir cambios |
| Tareas | **Aprobar y correr una tarea** · **Aprobar y correr todas (solo pregunto si me atoro)** · Aprobar y parar aquí · Pedir cambios |
| Cada tarea (modo una) | **Correr la siguiente tarea** · **Correr todas las restantes** · Parar aquí |
| Si se atora | Reintentar la tarea · Reintentar y seguir con todas · Ajustar la spec · Parar aquí |

- **Correr una tarea:** hace la siguiente, corre los tests, la marca y te vuelve a preguntar.
- **Correr todas:** las hace una tras otra **en orden**, sin preguntar entre tareas. Solo se detiene si
  se atora (tests que no pasan tras 3 intentos, diseño insuficiente, decisión de negocio): pausa, sale
  del modo automático y te pregunta con opciones. Un hook no le deja terminar el turno mientras queden
  tareas en este modo.
- **Orden:** `start` solo acepta la siguiente tarea pendiente; nunca se brinca ni reordena.

Los comandos por fase siguen existiendo si quieres entrar directo: `/spec-requirements`,
`/spec-design`, `/spec-tasks`, `/spec-run`, `/spec-status`.

### 1. Requisitos
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

### 2. Diseño
Secciones obligatorias: Resumen, Arquitectura, Componentes e interfaces, Modelos de datos, Manejo de
errores, Estrategia de pruebas. Cada componente cita los criterios que cubre (`cubre 1.2`).

### 3. Tareas
Checklist anidado. Las hojas son las tareas ejecutables y cada una lleva `_Requisitos: 1.1, 2.3_`.
Se valida que cada referencia exista y que **todos** los criterios queden cubiertos por alguna tarea.

### 4. Ejecución
Por tarea: escribe primero la prueba, implementa, cierra con `cli.py done` (corre la suite completa y
solo si pasa marca `[x]`, en cascada al grupo). Nunca hace commit.

## Aprobaciones y autorizaciones

Tu clic es la autorización. Un hook (`PostToolUse` sobre `AskUserQuestion`) lee la opción que
elegiste y la registra en `specs/<feature>/.state.json`. Claude no tiene otra vía:

- No puede aprobar: el comando `approve` y cualquier escritura a `.state.json` están bloqueados para él.
- No puede correr tareas sin tu clic: `start` responde "Sin autorización" si no elegiste correr una o
  todas. "Correr una" autoriza exactamente una tarea; "correr todas" activa el modo automático hasta
  terminar o hasta que se atore.
- **Respaldo escrito:** también puedes responder con texto corto: `aprobado` (aprueba y sigue),
  `correr una`, `correr todas`. Un mensaje como "aprobado pero cambia X" **no** aprueba.
- Cada aprobación guarda el hash del documento y del anterior en la cadena. Si editas un
  `requirements.md` ya aprobado, `design` y `tasks` quedan **desactualizados** solos y hay que
  reaprobarlos. Marcar casillas en `tasks.md` no invalida nada.
- Desde tu terminal: `python .claude/spec_harness/cli.py approve <feature> <requirements|design|tasks>`.

## Hooks

| Evento | Qué hace |
|---|---|
| `SessionStart` | Inyecta `.claude/steering/*.md` (product, tech y structure primero) y el estado de las specs |
| `UserPromptSubmit` | Respaldo escrito: registra `aprobado`, `correr una`, `correr todas` |
| `PreToolUse` | Compuerta de fase (no hay design sin requirements aprobado, ni tasks sin design); bloquea autoaprobarse, tocar `.state.json` y marcar casillas a mano |
| `PostToolUse` | Clic en una opción → registra aprobación / autorización y le dice a Claude qué sigue. Spec editada → la valida (EARS, secciones, cobertura). Código editado → lint del archivo (ruff / sqlfluff) y sus tests relacionados (`tests/test_<nombre>.py`) |
| `Stop` | No deja cerrar el turno con una tarea en curso ni, en modo "correr todas", mientras queden tareas. Se rinde tras `max_retries` y te avisa |

Lint o tests que no estén instalados se omiten sin bloquear.

## CLI

```bash
python .claude/spec_harness/cli.py status [feature]
python .claude/spec_harness/cli.py check <feature> <fase>
python .claude/spec_harness/cli.py start <feature>           # siguiente tarea; requiere tu autorización
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
python -m pytest -q     # 34 tests: validadores, decisiones, estado, CLI, hooks e instalador
ruff check .
```
