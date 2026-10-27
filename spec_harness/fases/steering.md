# Steering del proyecto

Entrada: qué archivos trabajar (product, tech, structure; por defecto los tres).

Los archivos de `.claude/steering/` se inyectan al contexto en cada inicio de sesión (hook
`SessionStart`). Deben ser **cortos y estables**: hechos que no cambian de una feature a otra. Lo
efímero va en las specs.

## Pasos

1. Lee el estado actual de `.claude/steering/*.md`. Si tienen contenido real (no solo la plantilla),
   actualízalos; no los reescribas desde cero.
2. Investiga el repo: README, `pyproject.toml`/`requirements.txt`/`package.json`, estructura de
   carpetas, tests existentes, config de lint, `CLAUDE.md`, y el historial de git reciente.
3. Redacta cada archivo (máx. ~60 líneas cada uno):
   - **product.md:** propósito, usuarios, procesos de negocio que toca, fuentes de datos y reglas de
     negocio que no son obvias.
   - **tech.md:** lenguajes y versiones, librerías clave, cómo se corren tests y lint, conexiones
     (Redshift, Mongo, NetSuite: vía MCP de solo lectura), restricciones (sin dependencias nuevas sin
     preguntar, etc.).
   - **structure.md:** mapa de carpetas, dónde va cada tipo de código, convención de nombres y de
     tests, imports permitidos.
4. Marca con `<!-- VERIFICAR -->` lo que infieras y no puedas confirmar.
5. Muestra un resumen de lo escrito y pregunta con AskUserQuestion: `Están bien así`,
   `Pedir cambios`. Estos archivos no tienen compuerta formal, pero no los des por buenos sin que el
   usuario los vea.
