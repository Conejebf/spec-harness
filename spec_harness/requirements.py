"""Parseo y validación de requirements.md (historias de usuario + criterios EARS en español).

Formato esperado:

    ### Requisito 1: <título>
    **Historia de usuario:** Como <rol>, quiero <capacidad>, para <beneficio>.
    #### Criterios de aceptación
    1. CUANDO <disparador>, EL SISTEMA DEBERÁ <respuesta>.

El criterio N del requisito R tiene id "R.N".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

REQ_HEADING = re.compile(r"^###\s+Requisito\s+(\d+)\s*[:.\-–]\s*(.+?)\s*$", re.IGNORECASE)
STORY = re.compile(r"Como\s+.+?,\s*quiero\s+.+?,\s*para\s+.+", re.IGNORECASE)
CRITERION = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")
CRITERIA_HEADING = re.compile(r"^#{4,}\s+Criterios de aceptaci[oó]n", re.IGNORECASE)

_SUBJECT = r"(?:EL|LA|LOS|LAS)\s+.+?\s+DEBER[AÁ]N?\s+.+"
EARS_PATTERNS = {
    "ubicuo": re.compile(rf"^{_SUBJECT}$"),
    "evento": re.compile(rf"^CUANDO\s+.+?,\s*{_SUBJECT}$"),
    "estado": re.compile(rf"^MIENTRAS\s+.+?,\s*(?:CUANDO\s+.+?,\s*)?{_SUBJECT}$"),
    "no deseado": re.compile(rf"^SI\s+.+?,\s*ENTONCES\s+{_SUBJECT}$"),
    "opcional": re.compile(rf"^DONDE\s+.+?,\s*{_SUBJECT}$"),
}


@dataclass
class Requirement:
    number: int
    title: str
    line: int
    has_story: bool = False
    criteria: dict[str, str] = field(default_factory=dict)


def ears_kind(text: str) -> str | None:
    for kind, pattern in EARS_PATTERNS.items():
        if pattern.match(text):
            return kind
    return None


def parse(text: str) -> list[Requirement]:
    reqs: list[Requirement] = []
    in_criteria = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        heading = REQ_HEADING.match(line)
        if heading:
            reqs.append(Requirement(int(heading.group(1)), heading.group(2), lineno))
            in_criteria = False
            continue
        if not reqs:
            continue
        current = reqs[-1]
        if line.startswith("#"):
            in_criteria = bool(CRITERIA_HEADING.match(line))
            continue
        if STORY.search(line):
            current.has_story = True
        crit = CRITERION.match(line)
        if in_criteria and crit:
            current.criteria[f"{current.number}.{crit.group(1)}"] = crit.group(2)
    return reqs


def criterion_ids(text: str) -> set[str]:
    return {cid for req in parse(text) for cid in req.criteria}


def validate(text: str) -> list[str]:
    reqs = parse(text)
    if not reqs:
        return ["No hay requisitos: usa encabezados '### Requisito N: <título>'."]
    errors: list[str] = []
    seen: set[int] = set()
    for req in reqs:
        errors.extend(_validate_requirement(req, seen))
    return errors


def _validate_requirement(req: Requirement, seen: set[int]) -> list[str]:
    where = f"Requisito {req.number} (línea {req.line})"
    errors: list[str] = []
    if req.number in seen:
        errors.append(f"{where}: número repetido.")
    seen.add(req.number)
    if not req.has_story:
        errors.append(f"{where}: falta la historia 'Como <rol>, quiero <capacidad>, para <beneficio>'.")
    if not req.criteria:
        errors.append(f"{where}: sin criterios bajo '#### Criterios de aceptación'.")
    for cid, crit in req.criteria.items():
        if ears_kind(crit) is None:
            errors.append(f"Criterio {cid} no sigue EARS: «{crit}»")
    return errors
