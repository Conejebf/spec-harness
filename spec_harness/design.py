"""Validación de design.md: secciones obligatorias y trazabilidad a requisitos."""

from __future__ import annotations

import re
import unicodedata

REQUIRED_SECTIONS = [
    "Resumen",
    "Arquitectura",
    "Componentes e interfaces",
    "Modelos de datos",
    "Manejo de errores",
    "Estrategia de pruebas",
]
REQ_REF = re.compile(r"\b(\d+\.\d+)\b")


def _norm(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return plain.strip().lower()


def headings(text: str) -> set[str]:
    return {_norm(m.group(1)) for m in re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE)}


def validate(text: str, criteria: set[str]) -> list[str]:
    found = headings(text)
    errors = [f"Falta la sección '## {s}'." for s in REQUIRED_SECTIONS if _norm(s) not in found]
    refs = set(REQ_REF.findall(text)) & criteria
    if criteria and not refs:
        errors.append("El diseño no referencia ningún criterio de requirements.md (ej. 'cubre 1.2').")
    return errors
