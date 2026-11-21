# Mueblería Iván

![Logo de Mueblería Iván](frontend/public/assets/brand/muebleria-ivan-logo.png)

Plataforma web desacoplada para gestionar el catálogo, las cotizaciones, los pedidos, la producción y los pagos de Mueblería Iván. El repositorio también servirá como prototipo académico de Cloud, DevOps, algoritmos de búsqueda y machine learning.

## Arquitectura

- `frontend/`: React, TypeScript y Vite; despliegue en Netlify.
- `backend/`: Python y FastAPI; despliegue previsto en Render.
- `supabase/`: migraciones, pruebas SQL y datos iniciales de PostgreSQL/Auth.
- `contracts/`: contrato OpenAPI generado por FastAPI.
- `data/`: datasets reproducibles para algoritmos y ML.
- `docs/`: requisitos, seguimiento y coordinación del equipo.
- `scripts/`: verificaciones comunes del repositorio.

El navegador usa Supabase directamente solo para autenticación. Los datos comerciales y las reglas de negocio pasan por FastAPI. Las imágenes se integrarán mediante Cloudinary.

## Inicio rápido

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Vite mostrará la URL del frontend, normalmente `http://localhost:5173`. La documentación Swagger estará en `http://127.0.0.1:8000/docs`.

## Verificación

Desde la raíz:

```powershell
.\scripts\verify.ps1
```

También se puede verificar una sola área con `-Scope frontend` o `-Scope backend`.

## Trabajo en equipo

Antes de modificar el proyecto, leer:

1. [`AGENTS.md`](AGENTS.md): instrucciones obligatorias para integrantes y Codex.
2. [`docs/PLAN_MAESTRO.md`](docs/PLAN_MAESTRO.md): alcance y arquitectura.
3. [`docs/PLAN_TRABAJO_PARALELO.md`](docs/PLAN_TRABAJO_PARALELO.md): ramas, propiedad y rutina diaria.
4. [`docs/BASE_DATOS.md`](docs/BASE_DATOS.md): diseño y criterio de finalización de PostgreSQL/Supabase.
5. [`docs/SEGUIMIENTO.md`](docs/SEGUIMIENTO.md): estado y evidencias.
6. [`docs/FRONTEND_ROADMAP.md`](docs/FRONTEND_ROADMAP.md): evolución visual y funcional.

No se trabaja directamente sobre `main`. Cada cambio se desarrolla en una rama `codex/<area>-<tarea>` y se integra mediante una revisión pequeña.

## Estado funcional actual

El frontend ya incluye catálogo, cotizador, seguimiento de pedidos, administración, producción, pagos y panel analítico con datos locales. El backend dispone de configuración, documentación OpenAPI, endpoint de salud y pruebas iniciales. Las siguientes fases reemplazarán progresivamente los datos locales por Supabase y reglas ejecutadas por FastAPI.

Los resultados de ML se presentarán como resultados de datos controlados de prueba hasta que exista suficiente historial operativo; nunca se mostrarán métricas inventadas como si fueran reales.
