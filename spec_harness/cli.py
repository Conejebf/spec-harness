"""CLI del harness de specs.

    python .claude/spec_harness/cli.py new <feature>
    python .claude/spec_harness/cli.py status [<feature>]
    python .claude/spec_harness/cli.py check <feature> <requirements|design|tasks>
    python .claude/spec_harness/cli.py start <feature> [<tarea>]
    python .claude/spec_harness/cli.py done <feature>
    python .claude/spec_harness/cli.py pause <feature> "<motivo>"
    python .claude/spec_harness/cli.py approve <feature> <fase>     (sólo el usuario)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from spec_harness import config, runner, tasks
from spec_harness.state import (
    FEATURE_NAME,
    PHASES,
    STATUS_LABEL,
    Feature,
    find_features,
)

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


def _feature(root: Path, cfg: dict, name: str, must_exist: bool = True) -> Feature:
    feat = Feature(config.specs_dir(root, cfg) / name)
    if must_exist and not feat.root.is_dir():
        sys.exit(f"No existe la feature '{name}' en {cfg['paths']['specs_dir']}/.")
    return feat


def cmd_new(root: Path, cfg: dict, args) -> int:
    if not FEATURE_NAME.match(args.feature):
        sys.exit("El nombre de la feature debe ser kebab-case: minúsculas, dígitos y guiones.")
    feat = _feature(root, cfg, args.feature, must_exist=False)
    if feat.root.is_dir():
        print(f"La feature '{args.feature}' ya existe.")
        return 0
    feat.save(feat.load())
    print(f"Creada {feat.root.relative_to(root).as_posix()}/")
    return 0


def describe(feat: Feature) -> str:
    data = feat.load()
    lines = [f"Feature '{feat.name}':"]
    for phase in PHASES:
        lines.append(f"  - {phase}.md: {STATUS_LABEL[feat.status(phase, data)]}")
    text = feat.read("tasks")
    if text:
        done, total = tasks.progress(text)
        lines.append(f"  - avance: {done}/{total} tareas")
    if data["awaiting"]:
        lines.append(f"  - esperando aprobación del usuario: {data['awaiting']}.md")
    if data["current_task"]:
        lines.append(f"  - tarea en curso: {data['current_task']}")
    if data["paused"]:
        lines.append(f"  - pausada: {data['paused']['task']} ({data['paused']['reason']})")
    return "\n".join(lines)


def cmd_status(root: Path, cfg: dict, args) -> int:
    feats = [_feature(root, cfg, args.feature)] if args.feature else find_features(config.specs_dir(root, cfg))
    if not feats:
        print("No hay specs todavía. Empieza con /spec-requirements <feature>.")
    for feat in feats:
        print(describe(feat))
    return 0


def cmd_check(root: Path, cfg: dict, args) -> int:
    feat = _feature(root, cfg, args.feature)
    errors = feat.validate(args.phase)
    if errors:
        print(f"{args.phase}.md tiene {len(errors)} problema(s):")
        print("\n".join(f"  - {e}" for e in errors))
        return 1
    print(f"{args.phase}.md es válido.")
    return 0


def cmd_approve(root: Path, cfg: dict, args) -> int:
    feat = _feature(root, cfg, args.feature)
    blocker = feat.prerequisite_error(args.phase)
    errors = [blocker] if blocker else feat.validate(args.phase)
    if errors:
        print("No se puede aprobar:\n" + "\n".join(f"  - {e}" for e in errors))
        return 1
    feat.approve(args.phase)
    print(f"{args.phase}.md de '{feat.name}' aprobado.")
    return 0


def cmd_start(root: Path, cfg: dict, args) -> int:
    feat = _feature(root, cfg, args.feature)
    blocker = feat.first_unapproved()
    if blocker:
        print(f"No se puede ejecutar: {blocker}")
        return 1
    data = feat.load()
    if data["current_task"] and data["current_task"] != (args.task or data["current_task"]):
        print(f"Ya hay una tarea en curso ({data['current_task']}). Termínala con 'done' o 'pause'.")
        return 1
    task = _pick_task(feat.read("tasks") or "", args.task or data["current_task"])
    if isinstance(task, str):
        print(task)
        return 1
    data.update(current_task=task.task_id, paused=None, stop_blocks=0)
    feat.save(data)
    print(_task_brief(feat, task))
    return 0


def _pick_task(text: str, task_id: str | None):
    parsed = tasks.parse(text)
    if task_id is None:
        task = tasks.next_pending(text)
        return task or "Todas las tareas están hechas."
    task = parsed.get(task_id)
    if task is None:
        return f"No existe la tarea {task_id}."
    if not task.is_leaf:
        return f"La tarea {task_id} tiene subtareas; ejecuta una subtarea ({', '.join(task.children)})."
    return f"La tarea {task_id} ya está hecha." if task.done else task


def _task_brief(feat: Feature, task: tasks.Task) -> str:
    detail = []
    for line in (feat.read("tasks") or "").splitlines()[task.line:]:
        indent = len(line) - len(line.lstrip())
        if tasks.TASK_LINE.match(line) or (line.strip() and indent <= task.indent):
            break
        detail.append(line)
    return (
        f"Tarea en curso: {task.task_id} {task.title}\n" + "\n".join(detail) + "\n"
        f"Requisitos que cubre: {', '.join(task.refs) or '(ninguno)'}"
    )


def cmd_done(root: Path, cfg: dict, args) -> int:
    feat = _feature(root, cfg, args.feature)
    data = feat.load()
    task_id = data["current_task"]
    if not task_id:
        print("No hay tarea en curso. Usa 'start' primero.")
        return 1
    result = runner.test_full(root, cfg)
    if not result.ok:
        print(f"Los tests fallan; la tarea {task_id} NO se marca.\n{result.tail()}")
        return 1
    path = feat.doc_path("tasks")
    path.write_text(tasks.mark_done(path.read_text(encoding="utf-8"), task_id), encoding="utf-8")
    data.update(current_task=None, last_done=task_id, stop_blocks=0)
    feat.save(data)
    text = path.read_text(encoding="utf-8")
    done, total = tasks.progress(text)
    nxt = tasks.next_pending(text)
    summary = (result.tail().splitlines() or ["ok"])[-1]
    print(f"Tarea {task_id} marcada como hecha ({done}/{total}). Tests: {summary}")
    print(f"Siguiente: {nxt.task_id} {nxt.title}" if nxt else "No quedan tareas pendientes.")
    return 0


def cmd_pause(root: Path, cfg: dict, args) -> int:
    feat = _feature(root, cfg, args.feature)
    data = feat.load()
    if not data["current_task"]:
        print("No hay tarea en curso.")
        return 1
    data.update(paused={"task": data["current_task"], "reason": args.reason}, current_task=None, stop_blocks=0)
    feat.save(data)
    print(f"Tarea {data['paused']['task']} pausada: {args.reason}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spec_harness")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("new").add_argument("feature")
    sub.add_parser("status").add_argument("feature", nargs="?")
    for name in ("check", "approve"):
        p = sub.add_parser(name)
        p.add_argument("feature")
        p.add_argument("phase", choices=PHASES)
    p = sub.add_parser("start")
    p.add_argument("feature")
    p.add_argument("task", nargs="?")
    sub.add_parser("done").add_argument("feature")
    p = sub.add_parser("pause")
    p.add_argument("feature")
    p.add_argument("reason")
    return parser


COMMANDS = {
    "new": cmd_new, "status": cmd_status, "check": cmd_check, "approve": cmd_approve,
    "start": cmd_start, "done": cmd_done, "pause": cmd_pause,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = config.project_root()
    return COMMANDS[args.cmd](root, config.load(root), args)


if __name__ == "__main__":
    sys.exit(main())
