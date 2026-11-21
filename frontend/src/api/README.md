# Capa de API

Esta carpeta será la única frontera HTTP del frontend.

- `client/`: configuración de URL, JWT y tratamiento uniforme de errores.
- `generated/`: tipos o cliente generados desde `contracts/openapi.json`; no editar manualmente.
- `modules/`: operaciones agrupadas por dominio.

Los componentes visuales no deben llamar `fetch` directamente. Mientras un endpoint no exista, los datos simulados deben estar tipados y quedar claramente identificados como temporales.
