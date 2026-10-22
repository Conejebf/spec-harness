---
name: spec-design
description: Fase 2 del flujo de specs. Con requirements.md aprobado, genera specs/<feature>/design.md (arquitectura, componentes e interfaces, modelos de datos, manejo de errores, estrategia de pruebas) y se detiene a pedir aprobación.
argument-hint: <feature>
disable-model-invocation: true
---

# Fase 2 · Diseño

Feature: `$ARGUMENTS`

## Pasos

1. **Compuerta.** Corre `python .claude/spec_harness/cli.py status <feature>`. Si `requirements.md` no
   aparece como `aprobada`, detente y dile al usuario qué falta. (Un hook también bloquea escribir
   `design.md` sin requisitos aprobados.)
2. **Leer** `specs/<feature>/requirements.md` completo y el steering (`tech.md`, `structure.md`).
3. **Investigar el código.** Busca módulos, funciones, tablas y patrones que el diseño debe reutilizar
   o respetar. Cita rutas concretas. Si hace falta conocer datos reales (esquemas de Redshift, colecciones
   de Mongo), consúltalos con las herramientas MCP de solo lectura.
4. **Escribir** `specs/<feature>/design.md` con [plantilla.md](plantilla.md). Secciones obligatorias
   (el hook las valida): Resumen, Arquitectura, Componentes e interfaces, Modelos de datos, Manejo de
   errores, Estrategia de pruebas.
   - Cada componente indica qué criterios cubre (`cubre 1.1, 1.3`). Todo criterio debe quedar cubierto
     por algún componente; si uno no encaja, dilo.
   - Interfaces con firmas reales (funciones, CLI, tablas/columnas, formatos de archivo).
   - Separa I/O de lógica: la lógica recibe datos y devuelve datos, para que se pueda probar sin BD.
   - La estrategia de pruebas dice qué se prueba con pytest (unitarias, fixtures) y, para SQL, qué
     validaciones se corren (conteos, duplicados, totales contra fuente).
   - Decisiones con alternativas descartadas y por qué, en pocas líneas.
5. **Validar:** `python .claude/spec_harness/cli.py check <feature> design`.
6. **DETENTE.** Resume el diseño (componentes, decisiones clave, riesgos) y pide aprobación: el usuario
   responde **`aprobado`**. No escribas `tasks.md` ni código.
