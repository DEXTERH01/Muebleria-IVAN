# Frontend de Mueblería Iván

Aplicación React, TypeScript y Vite preparada para desplegarse en Cloudflare Pages.

Cloudflare debe usar `frontend/` como directorio raíz, `npm run build` como comando
de construcción y `dist` como directorio de salida. La versión de Node está fijada
en `.node-version` y `public/_redirects` conserva las rutas de la SPA al abrirlas
directamente.

## Liderazgo

Cristian Gonza lidera este frente, con apoyo de Dexter en tareas acordadas. Leer `../AGENTS.md`, `../docs/PLAN_TRABAJO_PARALELO.md` y `../docs/FRONTEND_ROADMAP.md` antes de modificar esta carpeta.

## Desarrollo

```powershell
cd frontend
npm install
npm run dev
```

Para habilitar inicio de sesión, copia `.env.example` como `.env.local` y completa
la URL de Supabase y su clave `anon` pública. No uses la `service_role` en el frontend.
En Supabase Auth, configura la URL local y `/restablecer-contrasena` como destinos permitidos.

## Recorrido E2E local

La suite E2E usa respuestas de API controladas y una sesión de demostración ficticia; no necesita credenciales de Supabase ni modifica datos. Instala Chromium una vez y ejecuta:

```powershell
npx playwright install chromium
npm run test:e2e
```

Playwright inicia Vite en `http://127.0.0.1:4173` durante la ejecución. La suite cubre el envío de cotización, la aprobación administrativa, accesibilidad de teclado y responsive en 360, 768 y 1440 px.

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

