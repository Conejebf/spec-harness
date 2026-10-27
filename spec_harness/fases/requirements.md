# Fase 1 · Requisitos

Entrada: nombre de la feature (kebab-case) y la descripción de lo que se quiere. Si falta la
descripción, pregúntala antes de seguir.

## Pasos

1. **Contexto.** Ya tienes el steering (product/tech/structure) en contexto desde el inicio de la
   sesión. Revisa además el código relacionado con la feature (`Grep`/`Glob`) para no pedir algo
   que ya existe.
2. **Crear la carpeta:** `python .claude/spec_harness/cli.py new <feature>`.
   Si ya existía y tiene `requirements.md`, edítalo en lugar de reescribirlo desde cero.
3. **Dudas de negocio.** Si hay ambigüedades que cambian los requisitos (alcance, reglas, casos
   límite, volumen de datos), haz hasta 4 preguntas concretas con AskUserQuestion. Lo que sea una
   suposición razonable, regístralo en la sección "Supuestos" en vez de preguntar.
4. **Escribir** `specs/<feature>/requirements.md` siguiendo
   [plantilla-requirements.md](plantilla-requirements.md):
   - Un `### Requisito N: <título>` por capacidad, cada uno con su historia de usuario.
   - Criterios numerados bajo `#### Criterios de aceptación`, **todos en EARS**:

     | Tipo | Forma |
     |---|---|
     | Ubicuo | `EL SISTEMA DEBERÁ <respuesta>` |
     | Evento | `CUANDO <disparador>, EL SISTEMA DEBERÁ <respuesta>` |
     | Estado | `MIENTRAS <estado>, EL SISTEMA DEBERÁ <respuesta>` |
     | No deseado | `SI <condición>, ENTONCES EL SISTEMA DEBERÁ <respuesta>` |
     | Opcional | `DONDE <característica>, EL SISTEMA DEBERÁ <respuesta>` |

     Se puede nombrar un sujeto concreto (`EL REPORTE DEBERÁ`, `LA API DEBERÁ`).
   - Cada criterio debe ser verificable con una prueba: valores, umbrales y mensajes concretos.
     Cubre el camino feliz, los errores y los casos límite (vacíos, duplicados, nulos, permisos).
5. **Validar.** El hook valida el archivo al guardarlo; si te devuelve errores, corrígelos. Puedes
   revalidar con `python .claude/spec_harness/cli.py check <feature> requirements`.
6. **Pedir aprobación con un clic.** Resume (requisitos, número de criterios, supuestos) y pregunta con
   AskUserQuestion, `header` = nombre de la feature, con estas opciones exactas:
   - `Aprobar y seguir con el diseño`
   - `Aprobar y parar aquí`
   - `Pedir cambios`

   Lo que elija el usuario lo registra un hook, que te dice qué sigue. Si pide cambios, pregunta
   cuáles, edita y vuelve a preguntar. No escribas `design.md` hasta que el hook confirme la
   aprobación.

Nunca intentes aprobar tú: el comando `approve` y el `.state.json` están bloqueados para ti.
