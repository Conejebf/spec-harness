"""Estado de cada feature en specs/<feature>/.state.json.

Una aprobación guarda el hash del documento y el del documento anterior en la cadena.
Si cualquiera de los dos cambia, la fase deja de estar aprobada: editar requirements.md ya
aprobado invalida en cascada design y tasks sin que nadie tenga que acordarse.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from spec_harness import design, requirements, tasks

PHASES = ["requirements", "design", "tasks"]
FILES = {p: f"{p}.md" for p in PHASES}
STATE_FILE = ".state.json"
FEATURE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")

STATUS_LABEL = {
    "falta": "no existe",
    "borrador": "borrador, sin aprobar",
    "aprobada": "aprobada",
    "desactualizada": "cambió después de aprobarse; requiere reaprobación",
}


def _hash(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:16]


@dataclass
class Feature:
    root: Path

    @property
    def name(self) -> str:
        return self.root.name

    def doc_path(self, phase: str) -> Path:
        return self.root / FILES[phase]

    def read(self, phase: str) -> str | None:
        path = self.doc_path(phase)
        return path.read_text(encoding="utf-8") if path.is_file() else None

    def doc_hash(self, phase: str) -> str | None:
        text = self.read(phase)
        if text is None:
            return None
        return _hash(tasks.normalize(text) if phase == "tasks" else text)

    # --- persistencia -------------------------------------------------------------
    def load(self) -> dict:
        path = self.root / STATE_FILE
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        data.setdefault("feature", self.name)
        data.setdefault("approvals", {})
        for key in ("awaiting", "current_task", "last_done", "paused"):
            data.setdefault(key, None)
        data.setdefault("stop_blocks", 0)
        return data

    def save(self, data: dict) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        (self.root / STATE_FILE).write_text(text, encoding="utf-8")

    # --- fases --------------------------------------------------------------------
    def status(self, phase: str, data: dict | None = None) -> str:
        data = data or self.load()
        current = self.doc_hash(phase)
        if current is None:
            return "falta"
        approval = data["approvals"].get(phase)
        if not approval:
            return "borrador"
        upstream_ok = approval.get("upstream") == self._upstream_hash(phase)
        if approval.get("hash") == current and upstream_ok and self._upstream_approved(phase, data):
            return "aprobada"
        return "desactualizada"

    def _upstream_hash(self, phase: str) -> str | None:
        idx = PHASES.index(phase)
        return self.doc_hash(PHASES[idx - 1]) if idx else None

    def _upstream_approved(self, phase: str, data: dict) -> bool:
        idx = PHASES.index(phase)
        return idx == 0 or self.status(PHASES[idx - 1], data) == "aprobada"

    def prerequisite_error(self, phase: str) -> str | None:
        """None si la fase anterior está aprobada; si no, el motivo para no avanzar."""
        idx = PHASES.index(phase)
        if idx == 0:
            return None
        prev = PHASES[idx - 1]
        status = self.status(prev)
        if status == "aprobada":
            return None
        return f"{prev}.md de '{self.name}' está en estado: {STATUS_LABEL[status]}. Primero debe aprobarse."

    def first_unapproved(self) -> str | None:
        """Motivo por el que la feature no está lista para ejecutarse, o None si las 3 fases están aprobadas."""
        data = self.load()
        for phase in PHASES:
            status = self.status(phase, data)
            if status != "aprobada":
                return f"{phase}.md de '{self.name}' está en estado: {STATUS_LABEL[status]}."
        return None

    def validate(self, phase: str) -> list[str]:
        text = self.read(phase)
        if text is None:
            return [f"No existe {FILES[phase]}."]
        if phase == "requirements":
            return requirements.validate(text)
        criteria = requirements.criterion_ids(self.read("requirements") or "")
        if phase == "design":
            return design.validate(text, criteria)
        return tasks.validate(text, criteria)

    def approve(self, phase: str) -> None:
        data = self.load()
        data["approvals"][phase] = {
            "hash": self.doc_hash(phase),
            "upstream": self._upstream_hash(phase),
            "at": datetime.now().isoformat(timespec="seconds"),
        }
        if data.get("awaiting") == phase:
            data["awaiting"] = None
        self.save(data)


def find_features(specs_root: Path) -> list[Feature]:
    if not specs_root.is_dir():
        return []
    return [Feature(p) for p in sorted(specs_root.iterdir()) if p.is_dir()]


def feature_of(path: Path, specs_root: Path) -> tuple[Feature, str] | None:
    """(feature, nombre de archivo) si path es un documento dentro de specs/<feature>/."""
    try:
        rel = path.resolve().relative_to(specs_root.resolve())
    except ValueError:
        return None
    if len(rel.parts) != 2:
        return None
    return Feature(specs_root / rel.parts[0]), rel.parts[1]
