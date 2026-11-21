# Capa de API

Esta carpeta será la única frontera HTTP del frontend.

- `client/`: configuración de URL, JWT y tratamiento uniforme de errores.
- `generated/`: tipos o cliente generados desde `contracts/openapi.json`; no editar manualmente.
- `modules/`: operaciones agrupadas por dominio.

## Generar tipos del contrato

Desde `frontend/`, ejecuta `npm run api:generate`. El comando lee `../contracts/openapi.json`
y genera `src/api/generated/schema.d.ts` con `openapi-typescript`. Vuelve a ejecutarlo
después de integrar cambios en los endpoints o esquemas de FastAPI.

Los componentes visuales no deben llamar `fetch` directamente. Mientras un endpoint no exista, los datos simulados deben estar tipados y quedar claramente identificados como temporales.
