# Contratos de integración

`openapi.json` es generado desde FastAPI y define la comunicación entre frontend y backend.

Reglas:

- Backend actualiza el contrato junto con rutas, esquemas y pruebas.
- Frontend consume el contrato y no lo modifica manualmente.
- Los cambios incompatibles se coordinan antes de integrarse.
- El contrato debe permanecer versionado en Git.

Para exportarlo:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\export_openapi.py
```

