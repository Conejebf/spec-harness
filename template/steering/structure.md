# Estructura

<!-- Se carga en cada sesión. Llénalo con /spec-steering o a mano. Máx. ~60 líneas. -->

## Carpetas

- `<paquete>/` — <qué vive aquí>
- `sql/` — <queries>
- `tests/` — pruebas pytest, una por módulo: `tests/test_<modulo>.py`
- `specs/<feature>/` — requirements.md, design.md, tasks.md

## Convenciones

- Nombres: <snake_case, prefijos, etc.>
- La lógica no hace I/O: recibe datos y devuelve datos; las conexiones viven en adaptadores.
