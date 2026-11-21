# Backend de Mueblería Iván

## Preparación en PowerShell

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

## Desarrollo

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Para activar la Fase 2 configura en `backend/.env` una URL PostgreSQL con el driver `postgresql+psycopg://` y la URL del proyecto Supabase. Usa `backend/.env.example` como plantilla. El endpoint `GET /api/v1/auth/me` exige un JWT de Supabase y lee `app.profiles(user_id, role, active)`; esos nombres de columnas deben coincidir con la migración que implementa Cristian.

Las cargas firmadas de media requieren `MUEBLERIA_CLOUDINARY_CLOUD_NAME`, `MUEBLERIA_CLOUDINARY_API_KEY` y `MUEBLERIA_CLOUDINARY_API_SECRET`. El secreto solo se usa en el backend. Los tests de integración PostgreSQL se activan con `SUPABASE_TEST_DATABASE_URL` apuntando a una base local migrada y sembrada.

Para validar una base Supabase publicada sin conservar datos de prueba, configura
`MUEBLERIA_DATABASE_URL` y ejecuta:

```powershell
.\.venv\Scripts\python.exe scripts\run_remote_pgtap.py
```

Las suites SQL administran su propia transacción y terminan con `ROLLBACK`.

Las sesiones SQLAlchemy se cierran al terminar la solicitud. Los servicios que escriban datos deben confirmar explícitamente sus transacciones; esta capa no crea ni modifica tablas. Las migraciones SQL viven en `supabase/migrations/`.

Servicios locales:

- API: `http://127.0.0.1:8000`
- Salud: `http://127.0.0.1:8000/health`
- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Verificación

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

Para ejecutar la integración completa de la Fase 4 contra el entorno local de
Supabase, primero aplica migraciones y seed con `supabase db reset`. Después
carga los datos locales sin imprimir las claves y ejecuta la prueba:

```powershell
$supabaseLocal = supabase status -o json | ConvertFrom-Json
$env:SUPABASE_TEST_DATABASE_URL = $supabaseLocal.DB_URL -replace '^postgresql://', 'postgresql+psycopg://'
$env:SUPABASE_TEST_URL = $supabaseLocal.API_URL
$env:SUPABASE_TEST_PUBLISHABLE_KEY = $supabaseLocal.PUBLISHABLE_KEY
.\.venv\Scripts\python.exe -m pytest tests\integration\test_phase4_workflow_postgres.py
```

La prueba crea usuarios y registros únicos en el entorno local. Como auditoría,
historial y pagos son inmutables, usa `supabase db reset` para limpiar esos datos
de prueba cuando termines.

## Actualizar el contrato del frontend

Después de modificar rutas o esquemas, desde la raíz del repositorio:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\export_openapi.py --output contracts\openapi.json
```

El archivo generado `contracts/openapi.json` debe incluirse en el mismo commit que el cambio de API.
