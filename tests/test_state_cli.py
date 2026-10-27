from conftest import DESIGN, REQUIREMENTS, TASKS, run_cli, write

from spec_harness import tasks
from spec_harness.state import Feature


def _approved_feature(feature_dir, **authorization):
    feat = Feature(feature_dir)
    write(feature_dir / "requirements.md", REQUIREMENTS)
    feat.approve("requirements")
    write(feature_dir / "design.md", DESIGN)
    feat.approve("design")
    write(feature_dir / "tasks.md", TASKS)
    feat.approve("tasks")
    if authorization:
        data = feat.load()
        data.update(authorization)
        feat.save(data)
    return feat


def test_phase_chain_and_invalidation(feature_dir):
    feat = _approved_feature(feature_dir)
    assert [feat.status(p) for p in ("requirements", "design", "tasks")] == ["aprobada"] * 3
    write(feature_dir / "requirements.md", REQUIREMENTS + "\n<!-- cambio -->\n")
    assert feat.status("requirements") == "desactualizada"
    assert feat.status("design") == "desactualizada"
    assert feat.status("tasks") == "desactualizada"
    assert "requirements.md" in feat.prerequisite_error("design")


def test_marking_tasks_keeps_approval(feature_dir):
    feat = _approved_feature(feature_dir)
    write(feature_dir / "tasks.md", tasks.mark_done(TASKS, "1.1"))
    assert feat.status("tasks") == "aprobada"


def test_cli_start_requires_user_authorization(project, feature_dir):
    _approved_feature(feature_dir)
    out = run_cli(["start", "conteo"], project)
    assert out.returncode == 1 and "Sin autorización" in out.stdout and "Correr todas" in out.stdout


def test_cli_one_task_consumes_authorization(project, feature_dir):
    feat = _approved_feature(feature_dir, run_credits=1)
    write(project / "tests" / "test_ok.py", "def test_ok():\n    assert True\n")
    started = run_cli(["start", "conteo"], project)
    assert started.returncode == 0, started.stdout
    assert "1.1" in started.stdout and "1.1, 1.2" in started.stdout
    assert run_cli(["start", "conteo", "1.2"], project).returncode == 1  # ya hay una en curso
    done = run_cli(["done", "conteo"], project)
    assert done.returncode == 0, done.stdout
    assert "- [x] 1.1" in (feature_dir / "tasks.md").read_text(encoding="utf-8")
    assert "Siguiente: 1.2" in done.stdout and "AskUserQuestion" in done.stdout
    assert feat.load()["current_task"] is None
    assert "Sin autorización" in run_cli(["start", "conteo"], project).stdout


def test_cli_enforces_order(project, feature_dir):
    _approved_feature(feature_dir, run_credits=1)
    out = run_cli(["start", "conteo", "1.2"], project)
    assert out.returncode == 1 and "la siguiente es 1.1" in out.stdout


def test_cli_auto_mode_runs_all_in_order(project, feature_dir):
    feat = _approved_feature(feature_dir, run_mode="auto")
    write(project / "tests" / "test_ok.py", "def test_ok():\n    assert True\n")
    for expected in ("1.1", "1.2"):
        assert f"Tarea en curso: {expected}" in run_cli(["start", "conteo"], project).stdout
        done = run_cli(["done", "conteo"], project)
        assert done.returncode == 0, done.stdout
    assert "Modo automático" not in done.stdout and "No quedan" in done.stdout
    assert feat.load()["run_mode"] is None
    assert "- [x] 1. Conteo" in (feature_dir / "tasks.md").read_text(encoding="utf-8")


def test_cli_done_refuses_when_tests_fail(project, feature_dir):
    _approved_feature(feature_dir, run_credits=1)
    write(project / "tests" / "test_ko.py", "def test_ko():\n    assert False\n")
    run_cli(["start", "conteo"], project)
    done = run_cli(["done", "conteo"], project)
    assert done.returncode == 1 and "NO se marca" in done.stdout
    assert "- [ ] 1.1" in (feature_dir / "tasks.md").read_text(encoding="utf-8")


def test_cli_start_requires_approval(project, feature_dir):
    write(feature_dir / "requirements.md", REQUIREMENTS)
    out = run_cli(["start", "conteo"], project)
    assert out.returncode == 1 and "requirements.md" in out.stdout


def test_cli_pause_turns_off_auto_and_offers_options(project, feature_dir):
    feat = _approved_feature(feature_dir, run_mode="auto")
    run_cli(["start", "conteo"], project)
    paused = run_cli(["pause", "conteo", "falta definir columnas"], project)
    assert paused.returncode == 0 and "Reintentar la tarea" in paused.stdout
    assert feat.load()["run_mode"] is None
    status = run_cli(["status"], project).stdout
    assert "pausada: 1.1" in status and "0/2" in status


def test_cli_new_validates_name(project):
    assert run_cli(["new", "Mi Feature"], project).returncode != 0
    assert run_cli(["new", "mi-feature"], project).returncode == 0
    assert (project / "specs" / "mi-feature" / ".state.json").is_file()
