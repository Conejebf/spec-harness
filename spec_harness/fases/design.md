# Fase 2 · Diseño

Entrada: nombre de la feature.

## Pasos

1. **Compuerta.** Corre `python .claude/spec_harness/cli.py status <feature>`. Si `requirements.md` no
   aparece como `aprobada`, detente y dile al usuario qué falta. (Un hook también bloquea escribir
   `design.md` sin requisitos aprobados.)
2. **Leer** `specs/<feature>/requirements.md` completo y el steering (`tech.md`, `structure.md`).
3. **Investigar el código.** Busca módulos, funciones, tablas y patrones que el diseño debe reutilizar
   o respetar. Cita rutas concretas. Si hace falta conocer datos reales (esquemas de base de datos,
   colecciones), consúltalos con herramientas de solo lectura.
4. **Escribir** `specs/<feature>/design.md` con [plantilla-design.md](plantilla-design.md). Secciones
   obligatorias (el hook las valida): Resumen, Arquitectura, Componentes e interfaces, Modelos de datos,
   Manejo de errores, Estrategia de pruebas.
   - Cada componente indica qué criterios cubre (`cubre 1.1, 1.3`). Todo criterio debe quedar cubierto
     por algún componente; si uno no encaja, dilo.
   - Interfaces con firmas reales (funciones, CLI, tablas/columnas, formatos de archivo).
   - Separa I/O de lógica: la lógica recibe datos y devuelve datos, para que se pueda probar sin BD.
   - La estrategia de pruebas dice qué se prueba con pytest (unitarias, fixtures) y, para SQL, qué
     validaciones se corren (conteos, duplicados, totales contra fuente).
   - Decisiones con alternativas descartadas y por qué, en pocas líneas.
5. **Validar:** `python .claude/spec_harness/cli.py check <feature> design`.
6. **Pedir aprobación con un clic.** Resume (componentes, decisiones clave, riesgos) y pregunta con
   AskUserQuestion, `header` = nombre de la feature, con estas opciones exactas:
   - `Aprobar y seguir con las tareas`
   - `Aprobar y parar aquí`
   - `Pedir cambios`

   El hook registra la elección y te dice qué sigue. No escribas `tasks.md` ni código antes de eso.
