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

Para comprobar la demo publicada con el navegador y la API reales, sin crear cotizaciones ni modificar datos, ejecuta:

```powershell
$env:DEPLOYED_BASE_URL = 'https://muebleria-ivan.pages.dev'
npm run test:e2e -- deployed-smoke.spec.ts
```

Esta prueba revisa catálogo, detalle, estimación y redirección del portal sin sesión. Se omite en la suite local cuando `DEPLOYED_BASE_URL` no está definido. Las acciones de administrador, pagos y recuperación de contraseña requieren una validación integral separada con cuentas de demo.

## Verificación

### Pagos y vouchers

El detalle del pedido y el control de pagos permiten registrar importes con céntimos, fecha y referencia, y adjuntar un voucher opcional JPG, PNG, WebP o PDF de hasta 10 MB. El navegador solicita una firma a FastAPI, carga el archivo como privado y confirma el recurso antes de asociar su UUID al pago. La clave de idempotencia y el archivo confirmado se reutilizan al reintentar la misma operación desde el formulario.

Las pruebas de `PaymentModal.test.tsx`, `payment-media.test.ts` y `e2e/payment-voucher.spec.ts` cubren importes inválidos, error de carga, doble envío y reintento, además de accesibilidad y responsive. Usan respuestas controladas; queda validar la carga real en Cloudinary con las cuentas y configuración de demo.

### Bloque integral local

Estado al guardar el avance (2026-11-28): primera ejecución integral pendiente de completar la descarga e inicio de Supabase local. La corrección de avance de etapas pasó cuatro pruebas de regresión y el build; todavía no hay resultados de navegador ni de latencia ML para este bloque.

Con Python 3.12+, `backend/.venv` preparado y Supabase local migrado y sembrado, ejecuta desde la raíz:

```powershell
./frontend/quality/verify-local.ps1
```

El comando comprueba SQL, frontend, backend, integración de ML y el recorrido real en navegador: inicio de sesión de cliente, envío de cotización, aprobación y conversión por administrador, anticipo, producción, saldo e instalación, con consulta del historial del cliente. Crea cuentas y operaciones ficticias únicamente en Supabase local. No reinicia ni borra la base automáticamente; usa una base desechable preparada con `supabase db reset`.

La medición de ambos endpoints ML guarda 30 muestras calientes por endpoint y la primera solicitud por separado en `output/phase7-ml-performance.json`. Incluye FastAPI TestClient, JWT y persistencia PostgreSQL; no representa latencia del despliegue público. Las pruebas exigen persistencia versionada, deniegan acceso a visitantes/clientes y comprueban que inferencia y fallback no alteren pedidos ni pagos.

```powershell
npm run test
npm run build
```

## Límites

- No guardar secretos en variables `VITE_`.
- No consultar tablas comerciales de Supabase directamente.
- No editar manualmente tipos generados desde OpenAPI.
- No incorporar datos hardcodeados nuevos; los existentes se retirarán por fases.

