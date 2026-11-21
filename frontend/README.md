# Frontend de Mueblería Iván

Aplicación React, TypeScript y Vite desplegada en Netlify.

## Responsable principal

Cristian Gonza. Leer `../AGENTS.md`, `../docs/PLAN_TRABAJO_PARALELO.md` y `../docs/FRONTEND_ROADMAP.md` antes de modificar esta carpeta.

## Desarrollo

```powershell
cd frontend
npm install
npm run dev
```

## Verificación

```powershell
npm run test
npm run build
```

## Límites

- No guardar secretos en variables `VITE_`.
- No consultar tablas comerciales de Supabase directamente.
- No editar manualmente tipos generados desde OpenAPI.
- No incorporar datos hardcodeados nuevos; los existentes se retirarán por fases.

