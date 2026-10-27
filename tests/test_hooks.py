from conftest import DESIGN, REQUIREMENTS, TASKS, run_hook, write

from spec_harness.state import Feature


def _deny_reason(out):
    assert out and out["hookSpecificOutput"]["permissionDecision"] == "deny", out
    return out["hookSpecificOutput"]["permissionDecisionReason"]


def _edit(path, **extra):
    return {"tool_name": extra.pop("tool", "Write"), "tool_input": {"file_path": str(path), **extra}}


def test_session_start_injects_steering_and_status(project, feature_dir):
    write(project / ".claude" / "steering" / "tech.md", "Usamos pytest.")
    write(project / ".claude" / "steering" / "product.md", "Producto X.")
    write(feature_dir / "requirements.md", REQUIREMENTS)
    ctx = run_hook("session-start", {}, project)["hookSpecificOutput"]["additionalContext"]
    assert ctx.index("Producto X.") < ctx.index("Usamos pytest.")
    assert "Feature 'conteo'" in ctx and "borrador" in ctx


def test_pretool_phase_gate(project, feature_dir):
    write(feature_dir / "requirements.md", REQUIREMENTS)
    reason = _deny_reason(run_hook("pretool", _edit(feature_dir / "design.md"), project))
    assert "requirements.md" in reason
    Feature(feature_dir).approve("requirements")
    assert run_hook("pretool", _edit(feature_dir / "design.md"), project) is None
    assert run_hook("pretool", _edit(feature_dir / "tasks.md"), project) is not None


def test_pretool_blocks_self_approval_and_state(project, feature_dir):
    bash = {"tool_name": "Bash", "tool_input": {"command": "python .claude/spec_harness/cli.py approve conteo design"}}
    assert "usuario" in _deny_reason(run_hook("pretool", bash, project))
    _deny_reason(run_hook("pretool", _edit(feature_dir / ".state.json"), project))
    ok = {"tool_name": "Bash", "tool_input": {"command": "python .claude/spec_harness/cli.py status"}}
    assert run_hook("pretool", ok, project) is None


def test_pretool_blocks_manual_checkbox(project, feature_dir):
    feat = Feature(feature_dir)
    for phase, text in (("requirements", REQUIREMENTS), ("design", DESIGN), ("tasks", TASKS)):
        write(feature_dir / f"{phase}.md", text)
        feat.approve(phase)
    edit = _edit(feature_dir / "tasks.md", tool="Edit", old_string="- [ ] 1.1 Función", new_string="- [x] 1.1 Función")
    assert "done" in _deny_reason(run_hook("pretool", edit, project))
    real = _edit(feature_dir / "tasks.md", tool="Edit", old_string="Excluir cancelados", new_string="Excluir anulados")
    assert run_hook("pretool", real, project) is None


def test_posttool_validates_spec_and_sets_awaiting(project, feature_dir):
    path = write(feature_dir / "requirements.md", REQUIREMENTS.replace("EL SISTEMA DEBERÁ devolver 0", "da 0"))
    out = run_hook("posttool", _edit(path), project)
    assert out["decision"] == "block" and "EARS" in out["reason"]
    write(path, REQUIREMENTS)
    out = run_hook("posttool", _edit(path), project)
    assert "DETENTE" in out["hookSpecificOutput"]["additionalContext"]
    assert Feature(feature_dir).load()["awaiting"] == "requirements"


def test_posttool_runs_related_tests(project):
    code = write(project / "conteo.py", "def contar(x):\n    return len(x)\n")
    write(project / "tests" / "test_conteo.py", "from conteo import contar\n\ndef test_c():\n    assert contar([1]) == 2\n")
    write(project / "pytest.ini", "[pytest]\npythonpath = .\n")
    out = run_hook("posttool", _edit(code), project)
    assert out["decision"] == "block" and "tests relacionados" in out["reason"]
    write(project / "tests" / "test_conteo.py", "from conteo import contar\n\ndef test_c():\n    assert contar([1]) == 1\n")
    assert run_hook("posttool", _edit(code), project) is None


def test_prompt_approval_only_from_user_phrase(project, feature_dir):
    write(feature_dir / "requirements.md", REQUIREMENTS)
    data = Feature(feature_dir).load()
    data["awaiting"] = "requirements"
    Feature(feature_dir).save(data)
    assert run_hook("prompt", {"prompt": "aprobado pero cambia el 2"}, project) is None
    assert Feature(feature_dir).status("requirements") == "borrador"
    out = run_hook("prompt", {"prompt": "Aprobado."}, project)
    assert "fases/design.md" in out["hookSpecificOutput"]["additionalContext"]
    assert Feature(feature_dir).status("requirements") == "aprobada"


def _ask(feature: str, answer: str, via: str = "response") -> dict:
    question = {"question": "¿Apruebas?", "header": feature,
                "options": [{"label": "Aprobar y seguir con el diseño"}, {"label": "Pedir cambios"}]}
    payload = {"tool_name": "AskUserQuestion", "tool_input": {"questions": [question]}}
    if via == "response":
        payload["tool_response"] = {"questions": [question], "answers": {"¿Apruebas?": answer}}
    else:
        payload["tool_response"] = f'User has answered your questions: "¿Apruebas?"="{answer}".'
    return payload


def _awaiting(feature_dir, phase):
    feat = Feature(feature_dir)
    data = feat.load()
    data["awaiting"] = phase
    feat.save(data)
    return feat


def test_click_approve_and_continue(project, feature_dir):
    write(feature_dir / "requirements.md", REQUIREMENTS)
    feat = _awaiting(feature_dir, "requirements")
    out = run_hook("posttool", _ask("conteo", "Aprobar y seguir con el diseño"), project)
    assert "fases/design.md" in out["hookSpecificOutput"]["additionalContext"]
    assert feat.status("requirements") == "aprobada"


def test_click_parsed_from_text_response(project, feature_dir):
    write(feature_dir / "requirements.md", REQUIREMENTS)
    feat = _awaiting(feature_dir, "requirements")
    out = run_hook("posttool", _ask("conteo", "Aprobar y parar aquí", via="text"), project)
    assert "parar" in out["hookSpecificOutput"]["additionalContext"]
    assert feat.status("requirements") == "aprobada"


def test_unselected_options_do_not_approve(project, feature_dir):
    write(feature_dir / "requirements.md", REQUIREMENTS)
    feat = _awaiting(feature_dir, "requirements")
    assert run_hook("posttool", _ask("conteo", "Pedir cambios"), project) is None
    assert feat.status("requirements") == "borrador"


def test_click_approve_tasks_and_run_all(project, feature_dir):
    feat = Feature(feature_dir)
    for phase, text in (("requirements", REQUIREMENTS), ("design", DESIGN)):
        write(feature_dir / f"{phase}.md", text)
        feat.approve(phase)
    write(feature_dir / "tasks.md", TASKS)
    _awaiting(feature_dir, "tasks")
    out = run_hook("posttool", _ask("conteo", "Aprobar y correr todas (solo pregunto si me atoro)"), project)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "TODAS" in ctx and "fases/run.md" in ctx
    assert feat.status("tasks") == "aprobada" and feat.load()["run_mode"] == "auto"
    assert run_hook("stop", {}, project)["decision"] == "block"  # no se detiene con tareas pendientes


def test_click_run_one_task(project, feature_dir):
    feat = Feature(feature_dir)
    for phase, text in (("requirements", REQUIREMENTS), ("design", DESIGN), ("tasks", TASKS)):
        write(feature_dir / f"{phase}.md", text)
        feat.approve(phase)
    out = run_hook("posttool", _ask("conteo", "Correr la siguiente tarea"), project)
    assert "UNA tarea" in out["hookSpecificOutput"]["additionalContext"]
    data = feat.load()
    assert data["run_credits"] == 1 and data["run_mode"] is None
    assert run_hook("stop", {}, project) is None  # en modo "una tarea" sí puede detenerse


def test_stop_blocks_while_task_in_progress(project, feature_dir):
    feat = Feature(feature_dir)
    data = feat.load()
    data["current_task"] = "1.1"
    feat.save(data)
    for _ in range(3):
        assert run_hook("stop", {}, project)["decision"] == "block"
    assert "tope" in run_hook("stop", {}, project)["systemMessage"]
    data = feat.load()
    data.update(current_task=None, stop_blocks=0)
    feat.save(data)
    assert run_hook("stop", {}, project) is None
