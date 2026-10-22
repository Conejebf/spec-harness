"""Hooks de Claude Code del harness de specs.

    python .claude/spec_harness/hooks.py <session-start|pretool|posttool|prompt|stop>

Lee el JSON del evento por stdin y responde con el JSON que Claude Code espera.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from spec_harness import config, runner, tasks
from spec_harness.cli import describe
from spec_harness.state import (
    FILES,
    PHASES,
    STATE_FILE,
    Feature,
    feature_of,
    find_features,
)

DOC_PHASE = {v: k for k, v in FILES.items()}
EDIT_TOOLS = {"Write", "Edit", "MultiEdit"}
STEERING_FIRST = ["product.md", "tech.md", "structure.md"]


# --- utilidades -----------------------------------------------------------------------
def _context(event: str, text: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}


def _deny(reason: str) -> dict:
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason,
    }}


def _block(reason: str) -> dict:
    return {"decision": "block", "reason": reason}


def _target(payload: dict, root: Path) -> Path | None:
    raw = (payload.get("tool_input") or {}).get("file_path")
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_absolute() else root / path


# --- SessionStart: steering + estado de las specs --------------------------------------
def session_start(payload: dict, root: Path, cfg: dict) -> dict | None:
    parts = [_steering(root, cfg), _specs_summary(root, cfg)]
    text = "\n\n".join(p for p in parts if p)
    return _context("SessionStart", text) if text else None


def _steering(root: Path, cfg: dict) -> str:
    folder = config.steering_dir(root, cfg)
    if not folder.is_dir():
        return ""
    first = [folder / n for n in STEERING_FIRST if (folder / n).is_file()]
    files = first + sorted(p for p in folder.glob("*.md") if p.name not in STEERING_FIRST)
    chunks = [f"### {p.name}\n{p.read_text(encoding='utf-8').strip()}" for p in files]
    body = "\n\n".join(c for c in chunks if c.strip())
    limit = cfg["steering"]["max_chars"]
    if len(body) > limit:
        body = body[:limit] + "\n[... steering truncado: reduce los archivos de .claude/steering/]"
    return f"## Steering del proyecto (contexto permanente)\n\n{body}" if body else ""


def _specs_summary(root: Path, cfg: dict) -> str:
    feats = find_features(config.specs_dir(root, cfg))
    if not feats:
        return ""
    return "## Estado de las specs\n" + "\n".join(describe(f) for f in feats)


# --- PreToolUse: compuertas de fase y anti-trampas -------------------------------------
def pretool(payload: dict, root: Path, cfg: dict) -> dict | None:
    tool = payload.get("tool_name", "")
    if tool == "Bash":
        return _check_bash((payload.get("tool_input") or {}).get("command", ""))
    if tool not in EDIT_TOOLS:
        return None
    path = _target(payload, root)
    located = feature_of(path, config.specs_dir(root, cfg)) if path else None
    if not located:
        return None
    feat, filename = located
    if filename == STATE_FILE:
        return _deny("El estado de las specs sólo lo cambian el CLI y la aprobación del usuario.")
    phase = DOC_PHASE.get(filename)
    if phase is None:
        return None
    blocker = feat.prerequisite_error(phase)
    if blocker:
        return _deny(f"Compuerta de fase: {blocker} Pide al usuario que lo apruebe antes de seguir.")
    if phase == "tasks" and _only_checkboxes(tool, payload.get("tool_input") or {}):
        return _deny("No marques tareas a mano: usa `python .claude/spec_harness/cli.py done <feature>`, "
                     "que corre los tests antes de marcar.")
    return None


def _check_bash(command: str) -> dict | None:
    if "spec_harness" in command and re.search(r"\bapprove\b", command):
        return _deny("Aprobar una fase le corresponde al usuario: pídele que responda 'aprobado'.")
    if STATE_FILE in command:
        return _deny("No modifiques .state.json; usa el CLI del harness.")
    return None


def _only_checkboxes(tool: str, tool_input: dict) -> bool:
    edits = tool_input.get("edits") if tool == "MultiEdit" else [tool_input] if tool == "Edit" else []
    if not edits:
        return False
    return all(
        e.get("old_string") != e.get("new_string")
        and tasks.normalize(e.get("old_string", "")) == tasks.normalize(e.get("new_string", ""))
        for e in edits
    )


# --- PostToolUse: validar specs; lint + tests del archivo editado ----------------------
def posttool(payload: dict, root: Path, cfg: dict) -> dict | None:
    if payload.get("tool_name") not in EDIT_TOOLS:
        return None
    path = _target(payload, root)
    if path is None or not path.is_file():
        return None
    located = feature_of(path, config.specs_dir(root, cfg))
    if located:
        feat, filename = located
        return _after_spec_edit(feat, DOC_PHASE[filename]) if filename in DOC_PHASE else None
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    return None if ".claude" in rel.parts else _after_code_edit(path, root, cfg)


def _after_spec_edit(feat: Feature, phase: str) -> dict:
    errors = feat.validate(phase)
    if errors:
        return _block(f"{phase}.md no pasa la validación:\n" + "\n".join(f"- {e}" for e in errors))
    data = feat.load()
    data["awaiting"] = phase
    feat.save(data)
    stale = [p for p in PHASES[PHASES.index(phase) + 1:] if p in data["approvals"] and feat.read(p) is not None]
    note = f" Ojo: {', '.join(stale)} quedaron desactualizados y habrá que reaprobarlos." if stale else ""
    return _context("PostToolUse", (
        f"{phase}.md de '{feat.name}' es válido.{note} Cuando termines de editarlo, DETENTE: resume el "
        "documento y pide aprobación al usuario (responde 'aprobado' para aprobar). No avances de fase."
    ))


def _after_code_edit(path: Path, root: Path, cfg: dict) -> dict | None:
    results = [r for r in (runner.lint_file(path, root, cfg), runner.test_related(path, root, cfg)) if r]
    failed = [r for r in results if not r.ok]
    if not failed:
        return None
    report = "\n\n".join(f"[{r.label}] falló:\n{r.tail()}" for r in failed)
    return _block(f"{path.name}: corrige antes de seguir.\n\n{report}")


# --- UserPromptSubmit: la aprobación sólo la puede dar el usuario ----------------------
def prompt(payload: dict, root: Path, cfg: dict) -> dict | None:
    text = (payload.get("prompt") or "").strip().lower()
    phrases = "|".join(re.escape(p.lower()) for p in cfg["approval"]["phrases"])
    match = re.fullmatch(rf"(?:{phrases})(?:\s+([a-z0-9-]+))?[\s.!]*", text)
    if not match:
        return None
    waiting = [f for f in find_features(config.specs_dir(root, cfg)) if f.load()["awaiting"]]
    if match.group(1):
        waiting = [f for f in waiting if f.name == match.group(1)]
    if len(waiting) != 1:
        names = ", ".join(f.name for f in waiting) or "ninguna"
        return _context("UserPromptSubmit", f"El usuario quiso aprobar, pero hay {len(waiting)} specs esperando "
                        f"aprobación ({names}). Pídele que responda 'aprobado <feature>'.")
    return _approve(waiting[0])


def _approve(feat: Feature) -> dict:
    phase = feat.load()["awaiting"]
    problems = [p for p in [feat.prerequisite_error(phase)] if p] or feat.validate(phase)
    if problems:
        return _context("UserPromptSubmit", f"No se aprobó {phase}.md de '{feat.name}': " + "; ".join(problems))
    feat.approve(phase)
    nxt = {"requirements": "/spec-design", "design": "/spec-tasks", "tasks": "/spec-run"}[phase]
    return _context("UserPromptSubmit", (
        f"[spec-harness] El usuario APROBÓ {phase}.md de '{feat.name}' (quedó registrado). Confírmalo en una "
        f"línea e indícale que el siguiente paso es `{nxt} {feat.name}`. No lo empieces por tu cuenta."
    ))


# --- Stop: una tarea en curso no puede quedar a medias ---------------------------------
def stop(payload: dict, root: Path, cfg: dict) -> dict | None:
    for feat in find_features(config.specs_dir(root, cfg)):
        data = feat.load()
        if not data["current_task"]:
            continue
        if data["stop_blocks"] >= cfg["stop"]["max_retries"]:
            return {"systemMessage": f"spec-harness: la tarea {data['current_task']} de '{feat.name}' sigue "
                                     "en curso sin cerrar (se alcanzó el tope de reintentos)."}
        data["stop_blocks"] += 1
        feat.save(data)
        return _block(
            f"La tarea {data['current_task']} de '{feat.name}' sigue en curso. Termínala y corre "
            f"`python .claude/spec_harness/cli.py done {feat.name}` (corre los tests y marca tasks.md). "
            f"Si no puedes terminarla o necesitas al usuario, corre "
            f"`python .claude/spec_harness/cli.py pause {feat.name} \"<motivo>\"` y explícale por qué."
        )
    return None


HANDLERS = {
    "session-start": session_start, "pretool": pretool, "posttool": posttool, "prompt": prompt, "stop": stop,
}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in HANDLERS:
        print(f"uso: hooks.py <{'|'.join(HANDLERS)}>", file=sys.stderr)
        return 1
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    payload = json.loads(raw) if raw.strip() else {}
    root = config.project_root(payload.get("cwd"))
    out = HANDLERS[argv[0]](payload, root, config.load(root))
    if out:
        print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
