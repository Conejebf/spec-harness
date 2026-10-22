"""Instala, actualiza o desinstala el harness de specs en un proyecto.

    python install.py <ruta_proyecto>              # instala o actualiza
    python install.py <ruta_proyecto> --uninstall  # quita código, skills, hooks y bloque de CLAUDE.md

Idempotente: re-ejecutarlo actualiza el código y las skills sin pisar spec-harness.toml, el
steering, las specs ni hooks ajenos. Desinstalar conserva specs/ y .claude/steering/.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
TEMPLATE = REPO / "template"
MARK_START, MARK_END = "<!-- spec-harness:start -->", "<!-- spec-harness:end -->"
HOOK_TAG = ".claude/spec_harness/"
SKILLS = sorted(p.name for p in (TEMPLATE / "skills").iterdir() if p.is_dir())


def log(msg: str) -> None:
    print(f"[spec-harness] {msg}")


# --- instalar ---------------------------------------------------------------------------
def copy_package(target: Path) -> None:
    dest = target / ".claude" / "spec_harness"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(REPO / "spec_harness", dest, ignore=shutil.ignore_patterns("__pycache__"))
    log("código copiado a .claude/spec_harness/")


def copy_skills(target: Path) -> None:
    for name in SKILLS:
        dest = target / ".claude" / "skills" / name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(TEMPLATE / "skills" / name, dest)
    log(f"skills instaladas: {', '.join('/' + s for s in SKILLS)}")


def copy_if_absent(src: Path, dest: Path) -> None:
    if dest.exists():
        log(f"{dest.relative_to(dest.parents[1]).as_posix()} ya existe, no se toca")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    log(f"creado {dest.name}")


def _settings_path(target: Path) -> Path:
    return target / ".claude" / "settings.json"


def _is_ours(entry: dict) -> bool:
    return any(HOOK_TAG in h.get("command", "") for h in entry.get("hooks", []))


def merge_settings(target: Path, add: bool = True) -> None:
    path = _settings_path(target)
    current = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    ours = json.loads((TEMPLATE / "settings.json").read_text(encoding="utf-8"))["hooks"]
    hooks = current.setdefault("hooks", {})
    for event in list(set(hooks) | set(ours)):
        kept = [e for e in hooks.get(event, []) if not _is_ours(e)]
        merged = kept + (ours.get(event, []) if add else [])
        if merged:
            hooks[event] = merged
        else:
            hooks.pop(event, None)
    if not hooks:
        current.pop("hooks")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log("hooks " + ("registrados en" if add else "quitados de") + " .claude/settings.json")


def update_claude_md(target: Path, add: bool = True) -> None:
    path = target / "CLAUDE.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if MARK_START in text and MARK_END in text:
        head, rest = text.split(MARK_START, 1)
        text = head.rstrip("\n") + rest.split(MARK_END, 1)[1]
    if add:
        block = (TEMPLATE / "CLAUDE.spec.md").read_text(encoding="utf-8").strip()
        text = text.rstrip("\n") + ("\n\n" if text.strip() else "") + f"{MARK_START}\n{block}\n{MARK_END}\n"
    if text.strip() or path.is_file():
        path.write_text(text.strip("\n") + "\n" if text.strip() else "", encoding="utf-8")
    log("bloque de CLAUDE.md " + ("actualizado" if add else "quitado"))


def install(target: Path) -> None:
    copy_package(target)
    copy_skills(target)
    for name in ("product.md", "tech.md", "structure.md"):
        copy_if_absent(TEMPLATE / "steering" / name, target / ".claude" / "steering" / name)
    copy_if_absent(TEMPLATE / "spec-harness.toml", target / ".claude" / "spec-harness.toml")
    merge_settings(target)
    update_claude_md(target)
    log("listo. Reinicia la sesión de Claude Code en el proyecto para cargar hooks y skills.")
    log("siguiente paso sugerido: /spec-steering para llenar product/tech/structure.")


# --- desinstalar ------------------------------------------------------------------------
def uninstall(target: Path) -> None:
    shutil.rmtree(target / ".claude" / "spec_harness", ignore_errors=True)
    for name in SKILLS:
        shutil.rmtree(target / ".claude" / "skills" / name, ignore_errors=True)
    if _settings_path(target).is_file():
        merge_settings(target, add=False)
    if (target / "CLAUDE.md").is_file():
        update_claude_md(target, add=False)
    log("desinstalado. Se conservan specs/, .claude/steering/ y .claude/spec-harness.toml.")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", type=Path)
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    target = args.target.resolve()
    if not target.is_dir():
        sys.exit(f"No existe la carpeta {target}")
    if target == REPO:
        sys.exit("No instales el harness sobre su propio repo.")
    uninstall(target) if args.uninstall else install(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
