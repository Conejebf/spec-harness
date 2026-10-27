from conftest import DESIGN, REQUIREMENTS, TASKS

from spec_harness import design, flow, requirements, tasks

CRITERIA = {"1.1", "1.2", "2.1"}


def test_requirements_valid():
    assert requirements.validate(REQUIREMENTS) == []
    assert requirements.criterion_ids(REQUIREMENTS) == CRITERIA


def test_ears_patterns():
    ok = [
        "EL SISTEMA DEBERÁ exportar un CSV.",
        "LA API DEBERA responder 404.",
        "CUANDO llega un pedido, EL SISTEMA DEBERÁ registrarlo.",
        "MIENTRAS el túnel esté caído, EL SISTEMA DEBERÁ reintentar.",
        "MIENTRAS haya lag, CUANDO se pida un total, EL REPORTE DEBERÁ advertirlo.",
        "SI falta la llave, ENTONCES EL SISTEMA DEBERÁ fallar con mensaje claro.",
        "DONDE exista caché, EL SISTEMA DEBERÁ usarla.",
    ]
    bad = ["El sistema exporta un CSV.", "CUANDO llega un pedido se registra.", "SI falla, EL SISTEMA DEBERÁ x."]
    assert all(requirements.ears_kind(t) for t in ok)
    assert not any(requirements.ears_kind(t) for t in bad)


def test_requirements_errors():
    text = REQUIREMENTS.replace("**Historia de usuario:** Como analista, quiero contar pedidos, para medir volumen.", "")
    text = text.replace("EL SISTEMA DEBERÁ devolver 0", "devuelve 0")
    errors = requirements.validate(text)
    assert any("historia" in e for e in errors)
    assert any("1.2" in e and "EARS" in e for e in errors)
    assert requirements.validate("# nada") != []


def test_design_sections_and_refs():
    assert design.validate(DESIGN, CRITERIA) == []
    errors = design.validate("## Resumen\nx", CRITERIA)
    assert any("Arquitectura" in e for e in errors)
    assert any("referencia" in e for e in errors)


def test_tasks_validation_and_coverage():
    assert tasks.validate(TASKS, CRITERIA) == []
    errors = tasks.validate(TASKS.replace("_Requisitos: 2.1_", "_Requisitos: 9.9_"), CRITERIA)
    assert any("9.9" in e for e in errors)
    assert any("2.1" in e and "sin ninguna tarea" in e for e in errors)
    assert any("sin '_Requisitos" in e for e in tasks.validate("- [ ] 1. Algo\n", CRITERIA))


def test_tasks_parent_ref_covers_children():
    text = "- [ ] 1. Todo\n  - _Requisitos: 1_\n"
    assert tasks.validate(text, {"1.1", "1.2"}) == []


def test_mark_done_cascades_to_parent():
    text = tasks.mark_done(TASKS, "1.1")
    assert "- [x] 1.1" in text and "- [ ] 1. Conteo" in text
    assert tasks.next_pending(text).task_id == "1.2"
    text = tasks.mark_done(text, "1.2")
    assert "- [x] 1. Conteo" in text
    assert tasks.next_pending(text) is None
    assert tasks.progress(text) == (2, 2)
    assert tasks.normalize(text) == tasks.normalize(TASKS)


def test_classify_choices():
    phrases = ["aprobado"]
    c = flow.classify("Aprobar y seguir con el diseño", phrases)
    assert c.approve and c.proceed and c.run is None
    c = flow.classify("Aprobar y parar aquí", phrases)
    assert c.approve and not c.proceed
    c = flow.classify("Aprobar y correr todas (solo pregunto si me atoro)", phrases)
    assert c.approve and c.run == "all"
    assert flow.classify("Correr la siguiente tarea", phrases).run == "one"
    assert flow.classify("Reintentar y seguir con todas", phrases).run == "all"
    assert flow.classify("Reintentar la tarea", phrases).run == "one"
    assert flow.classify("Aprobado.", phrases).proceed
    for label in ("Pedir cambios", "Parar aquí", "Ajustar la spec"):
        assert flow.classify(label, phrases).empty
