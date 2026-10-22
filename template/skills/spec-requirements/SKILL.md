---
name: spec-requirements
description: Fase 1 del flujo de specs. Genera specs/<feature>/requirements.md con historias de usuario y criterios de aceptación EARS en español, y se detiene a pedir aprobación.
argument-hint: <feature-en-kebab-case> [descripción de lo que se quiere]
disable-model-invocation: true
---

# Fase 1 · Requisitos

Argumentos: `$ARGUMENTS` → la primera palabra es el nombre de la feature (kebab-case); el resto,
la descripción. Si falta la descripción, pregúntala antes de seguir.

## Pasos

1. **Contexto.** Ya tienes el steering (product/tech/structure) en contexto desde el inicio de la
   sesión. Revisa además el código relacionado con la feature (`Grep`/`Glob`) para no pedir algo
   que ya existe.
2. **Crear la carpeta:** `python .claude/spec_harness/cli.py new <feature>`.
   Si ya existía y tiene `requirements.md`, edítalo en lugar de reescribirlo desde cero.
3. **Dudas de negocio.** Si hay ambigüedades que cambian los requisitos (alcance, reglas, casos
   límite, volumen de datos), haz hasta 5 preguntas concretas y espera respuesta. Lo que sea una
   suposición razonable, regístralo en la sección "Supuestos" en vez de preguntar.
4. **Escribir** `specs/<feature>/requirements.md` siguiendo [plantilla.md](plantilla.md):
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
6. **DETENTE.** Muestra un resumen (requisitos y número de criterios, supuestos, preguntas abiertas) y
   pide aprobación: el usuario aprueba respondiendo **`aprobado`**. No escribas `design.md`. Si pide
   cambios, edita el archivo y vuelve a pedir aprobación.

Nunca intentes aprobar tú: el comando `approve` y el `.state.json` están bloqueados para ti.
