# Instrucciones de trabajo para Codex

## Lectura obligatoria

Antes de modificar el repositorio, leer en este orden:

1. `docs/PLAN_MAESTRO.md`
2. `docs/PLAN_TRABAJO_PARALELO.md`
3. `docs/SEGUIMIENTO.md`
4. El README de la carpeta que se va a modificar

## Arquitectura y propiedad

- La propiedad se asigna por módulo y tarea activa, no por una carpeta completa.
- Dexter lidera plataforma backend, autenticación, pedidos, pagos, algoritmos, ML y DevOps.
- Cristian Gonza lidera frontend, base de datos, catálogo y cotizaciones, incluyendo sus módulos backend.
- `supabase/migrations/`: Cristian crea la migración base; después solo una persona modifica migraciones en cada tarea.
- `contracts/openapi.json`: lo genera Dexter al integrar cambios de API; frontend lo consume.
- `.github/`, `scripts/`, `netlify.toml` y documentación raíz: cambios coordinados por Dexter.
- `docs/SEGUIMIENTO.md`: puede actualizarlo quien termina una tarea, pero solo en las filas de su tarea.

Consultar la matriz vigente en `docs/PLAN_TRABAJO_PARALELO.md`. No editar simultáneamente el mismo módulo o archivo. No ejecutar formateos masivos en carpetas compartidas.

## Reglas de integración

1. `main` debe permanecer compilable y con pruebas aprobadas.
2. Cada persona trabaja en su propia rama `codex/<area>-<tarea>`.
3. Una rama debe resolver una tarea concreta y producir commits pequeños.
4. Antes de comenzar y antes de abrir un PR, actualizar la rama con `main`.
5. No usar `git push --force` sobre ramas compartidas.
6. No mezclar refactors, nuevas funciones y cambios de formato en el mismo commit.
7. No editar manualmente `contracts/openapi.json`; se genera desde FastAPI.
8. No editar manualmente archivos bajo `frontend/src/api/generated/`.
9. No subir `.env`, credenciales, `.venv`, `node_modules`, `dist`, datos personales ni modelos temporales.
10. Conservar `output/` y `tmp/`; no incluirlos en commits salvo acuerdo explícito.

## Contrato entre frontend y backend

- FastAPI y los esquemas Pydantic son la fuente ejecutable de la API.
- Un cambio de endpoint debe incluir actualización de pruebas y `contracts/openapi.json`.
- Un cambio incompatible requiere aviso en `docs/PLAN_TRABAJO_PARALELO.md` antes de implementarse.
- Frontend no debe inventar campos que no existan en OpenAPI.
- Backend no debe renombrar campos consumidos por frontend sin coordinar la migración.

## Verificación obligatoria

Frontend:

```powershell
cd frontend
npm run test
npm run build
```

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

Repositorio completo:

```powershell
.\scripts\verify.ps1
```

Antes de cada commit ejecutar `git diff --check` y revisar `git status --short`.

## Convención de commits

- `feat(frontend): ...`
- `feat(backend): ...`
- `fix(frontend): ...`
- `fix(backend): ...`
- `test: ...`
- `docs: ...`
- `chore: ...`

El mensaje debe describir el resultado, no la actividad. Ejemplo: `feat(frontend): add accessible customer login form`.

## Restricciones del proyecto

- No mostrar métricas de ML escritas manualmente como si fueran resultados reales.
- Los importes viajan como enteros en céntimos y las medidas canónicas en milímetros.
- Las decisiones de ML son consultivas y no modifican pedidos ni pagos automáticamente.
- El frontend accede a datos comerciales mediante FastAPI; Supabase en navegador se limita a autenticación.
- Mantener español en la interfaz y nombres técnicos estables en inglés dentro de contratos.

