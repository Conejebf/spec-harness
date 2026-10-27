"""Decisiones del usuario -> aprobación de fases y autorización para correr tareas.

El usuario decide con un clic en las opciones que Claude le ofrece (AskUserQuestion) o
escribiendo "aprobado". Este módulo interpreta esa respuesta y la registra en el estado; Claude no
tiene otra vía para aprobar ni para autorizarse a correr tareas.

Etiquetas que entiende (sin importar mayúsculas ni acentos):
- empieza con "Aprobar"                  -> aprueba la fase pendiente
- contiene "seguir"                      -> además, continúa con la siguiente fase
- contiene "correr todas" / "todas las"  -> modo automático: todas las tareas en orden
- contiene "correr una" / "siguiente tarea" / "reintentar" -> autoriza una tarea
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from spec_harness import tasks
from spec_harness.state import Feature

NEXT_PHASE = {"requirements": "design", "design": "tasks"}
RUN_ALL = ("correr todas", "todas las restantes", "seguir con todas")
RUN_ONE = ("correr una", "siguiente tarea", "reintentar")

OPTIONS_HINT = (
    "Pregunta con AskUserQuestion ofreciendo: 'Correr la siguiente tarea', "
    "'Correr todas las restantes (solo pregunto si me atoro)' y 'Parar aquí'."
)
APPROVAL_OPTIONS = {
    "requirements": ["Aprobar y seguir con el diseño", "Aprobar y parar aquí", "Pedir cambios"],
    "design": ["Aprobar y seguir con las tareas", "Aprobar y parar aquí", "Pedir cambios"],
    "tasks": [
        "Aprobar y correr una tarea",
        "Aprobar y correr todas (solo pregunto si me atoro)",
        "Aprobar y parar aquí",
        "Pedir cambios",
    ],
}


def approval_hint(feature: str, phase: str) -> str:
    options = ", ".join(f"'{o}'" for o in APPROVAL_OPTIONS[phase])
    return (f"pide aprobación con AskUserQuestion (header '{feature}'), ofreciendo exactamente estas opciones: "
            f"{options}. Si elige 'Pedir cambios', pregunta qué cambiar.")


@dataclass
class Choice:
    approve: bool = False
    proceed: bool = False
    run: str | None = None  # "one" | "all"

    @property
    def empty(self) -> bool:
        return not (self.approve or self.run)


def _norm(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", plain).strip().lower()


def classify(label: str, phrases: list[str]) -> Choice:
    text = _norm(label)
    typed = text.rstrip(" .!") in {_norm(p) for p in phrases}
    choice = Choice(approve=text.startswith("aprobar") or typed)
    choice.proceed = choice.approve and ("seguir" in text or typed)
    if any(k in text for k in RUN_ALL):
        choice.run = "all"
    elif any(k in text for k in RUN_ONE):
        choice.run = "one"
    return choice


def _mentioned(feats: list[Feature], hint: str) -> list[Feature]:
    named = [f for f in feats if f.name in hint]
    return named or feats


def _runnable(feat: Feature) -> bool:
    text = feat.read("tasks")
    return feat.first_unapproved() is None and bool(text) and tasks.next_pending(text) is not None


def apply(choice: Choice, feats: list[Feature], hint: str = "") -> str | None:
    """Registra la decisión y devuelve la instrucción para Claude (o None si no hay nada que hacer)."""
    if choice.empty:
        return None
    pool = _mentioned(feats, hint)
    notes: list[str] = []
    if choice.approve:
        note = _approve(pool, choice)
        if note.startswith("!"):
            return note[1:]
        notes.append(note)
    if choice.run:
        notes.append(_grant(pool, choice.run))
    return "[spec-harness] " + " ".join(notes)


def _approve(pool: list[Feature], choice: Choice) -> str:
    waiting = [f for f in pool if f.load()["awaiting"]]
    if len(waiting) != 1:
        names = ", ".join(f.name for f in waiting) or "ninguna"
        return (f"!El usuario quiso aprobar, pero hay {len(waiting)} specs esperando aprobación ({names}). "
                "Pregúntale cuál, con AskUserQuestion.")
    feat = waiting[0]
    phase = feat.load()["awaiting"]
    problems = [p for p in [feat.prerequisite_error(phase)] if p] or feat.validate(phase)
    if problems:
        return f"!No se aprobó {phase}.md de '{feat.name}': " + "; ".join(problems)
    feat.approve(phase)
    head = f"El usuario APROBÓ {phase}.md de '{feat.name}' (quedó registrado)."
    if phase == "tasks":
        return head if choice.run else f"{head} {OPTIONS_HINT}"
    if choice.proceed:
        return f"{head} Sigue AHORA con la siguiente fase: lee `.claude/spec_harness/fases/{NEXT_PHASE[phase]}.md` y síguelo para '{feat.name}'."
    return f"{head} Pidió parar aquí: confírmalo en una línea y termina el turno."


def _grant(pool: list[Feature], mode: str) -> str:
    runnable = [f for f in pool if _runnable(f)]
    if len(runnable) != 1:
        names = ", ".join(f.name for f in runnable) or "ninguna"
        return f"No se autorizó correr tareas: hay {len(runnable)} specs listas para ejecutar ({names})."
    feat = runnable[0]
    data = feat.load()
    data.update(run_mode="auto" if mode == "all" else None, run_credits=1 if mode == "one" else 0)
    feat.save(data)
    scope = ("TODAS las tareas pendientes, en orden; no preguntes entre tareas, solo si te atoras"
             if mode == "all" else "UNA tarea (la siguiente en orden)")
    return (f"En '{feat.name}', el usuario autorizó correr {scope}. "
            "Lee `.claude/spec_harness/fases/run.md` y síguelo ahora.")


def extract_answers(payload: dict) -> list[str]:
    """Respuestas elegidas en AskUserQuestion, sin incluir las opciones que no se eligieron."""
    found: list[str] = []
    answers = (payload.get("tool_input") or {}).get("answers")
    if isinstance(answers, dict):
        found.extend(str(v) for v in answers.values())
    response = payload.get("tool_response")
    if isinstance(response, dict) and isinstance(response.get("answers"), dict):
        found.extend(str(v) for v in response["answers"].values())
    elif isinstance(response, str):
        found.extend(re.findall(r'"[^"]*"="([^"]*)"', response))
    return list(dict.fromkeys(found))


def question_text(payload: dict) -> str:
    questions = (payload.get("tool_input") or {}).get("questions") or []
    return " ".join(f"{q.get('header', '')} {q.get('question', '')}" for q in questions if isinstance(q, dict))
