---
name: spec-steering
description: Redacta o actualiza los archivos de steering (.claude/steering/product.md, tech.md, structure.md) leyendo el repositorio. Se cargan solos al inicio de cada sesión.
argument-hint: [product|tech|structure]  (vacío = los tres)
disable-model-invocation: true
---

Archivos a trabajar: `$ARGUMENTS` (si está vacío, los tres).

Lee `.claude/spec_harness/fases/steering.md` y síguelo al pie de la letra.
