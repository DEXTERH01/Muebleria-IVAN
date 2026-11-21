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

## Cuentas de demostración por rol

El seed SQL crea perfiles ficticios, pero no cuentas capaces de iniciar sesión. Para crear o
actualizar cuentas reales de Supabase Auth y sincronizar sus roles en app.profiles, ejecuta el
script desde una terminal. Solicita de forma oculta una clave secreta sb_secret_... o la antigua
service_role; nunca uses la clave publishable/anon. También solicita una contraseña común de al
menos ocho caracteres. El script actualiza la contraseña de estas cuentas cada vez que se ejecuta.

Desde la raíz del repositorio, en PowerShell; cuando la solicite, ingresa la clave secreta del
proyecto Supabase y luego la contraseña temporal que usarán todas las cuentas:

~~~powershell
backend\.venv\Scripts\python.exe backend\scripts\bootstrap_demo_accounts.py
~~~

El script lee MUEBLERIA_SUPABASE_URL y MUEBLERIA_DATABASE_URL desde backend/.env, no imprime
la clave ni la contraseña, no las guarda y puede repetirse para reparar perfiles. Crea estas
cuentas con la misma contraseña temporal indicada:

| Correo | Rol |
| --- | --- |
| admin.demo@example.com | Administrador (admin) |
| operador.demo@example.com | Operador (operator) |
| cliente.ana.demo@example.com | Cliente (customer) |
| cliente.luis.demo@example.com | Cliente (customer) |

No guardes estas credenciales en el repositorio ni configures la clave secreta en Netlify o Render.
Para una exposición pública, usa una contraseña temporal y cámbiala o elimina las cuentas al terminar.

## Machine learning con datos de prueba

El entrenamiento se ejecuta fuera de las solicitudes web. Para reproducir los 500 pedidos sintéticos, comparar los modelos, generar los artefactos versionados y registrar sus métricas en Supabase:

```powershell
.\.venv\Scripts\python.exe scripts\generate_ml_dataset.py
.\.venv\Scripts\python.exe scripts\train_ml.py
.\.venv\Scripts\python.exe scripts\register_ml_models.py
```

El manifiesto en `artifacts/ml/manifest.json` contiene hashes SHA-256, columnas, separación 70/15/15 y métricas calculadas. La regresión, clasificación y segmentación son consultivas; sus respuestas se etiquetan `Datos de prueba` y nunca modifican pedidos ni precios.

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
