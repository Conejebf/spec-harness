# Tecnología

<!-- Se carga en cada sesión. Llénalo con /spec-steering o a mano. Máx. ~60 líneas. -->

## Stack

- Python <versión>; librerías clave: <...>
- SQL: Redshift (dialecto `redshift`)

## Comandos

- Tests: `python -m pytest -q`
- Lint: `ruff check .` · `sqlfluff lint <archivo> --dialect redshift`

## Restricciones

- No agregar dependencias sin preguntar.
- Acceso a datos sólo de lectura (MCP `redshift` / `mongo`).
