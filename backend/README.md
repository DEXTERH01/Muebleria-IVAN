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

## Actualizar el contrato del frontend

Después de modificar rutas o esquemas, desde la raíz del repositorio:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\export_openapi.py
```

El archivo generado `contracts/openapi.json` debe incluirse en el mismo commit que el cambio de API.
