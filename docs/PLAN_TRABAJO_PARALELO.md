# Plan de trabajo paralelo

## Objetivo

Dos integrantes trabajarán en paralelo sin editar los mismos archivos ni romper el contrato entre frontend y backend. La integración se realizará mediante ramas cortas, OpenAPI y revisiones pequeñas durante el día.

## Integrantes y frentes

| Frente | Responsable | Carpetas principales |
| --- | --- | --- |
| Backend, datos y DevOps | Responsable principal | `backend/`, `supabase/`, `contracts/`, `.github/`, `scripts/` |
| Frontend y experiencia de usuario | Cristian Gonza | `frontend/` |
| Arquitectura y alcance | Compartido, decide responsable principal | `docs/PLAN_MAESTRO.md`, `AGENTS.md` |
| Pruebas integrales y exposición | Compartido | `docs/`, evidencias y entorno demo |

## Ramas iniciales

Después del commit que introduce esta estructura:

```powershell
# Responsable backend
git switch -c codex/backend-phase-2

# Cristian Gonza
git switch main
git pull --ff-only
git switch -c codex/frontend-refresh
```

No trabajar directamente en `main`. Cada tarea adicional puede usar una rama más específica, por ejemplo `codex/frontend-auth` o `codex/backend-catalog`.

Cada integrante debe trabajar en su propio clon o worktree. Dos personas o dos sesiones de Codex no deben modificar simultáneamente el mismo directorio de trabajo, aunque usen ramas distintas, porque el cambio de rama y los archivos sin confirmar se comparten dentro de ese directorio.

Antes de iniciar, ambos deben confirmar que su repositorio tiene el mismo remoto y el último commit de `main`:

```powershell
git remote -v
git fetch origin
git switch main
git pull --ff-only
```

## División inmediata

### Responsable backend

1. Crear proyecto Supabase y variables locales.
2. Preparar SQLAlchemy, Alembic y conexión PostgreSQL.
3. Crear migraciones de perfiles y roles.
4. Verificar JWT de Supabase en FastAPI.
5. Implementar pruebas de permisos.
6. Exportar OpenAPI después de cada cambio de contrato.

### Cristian Gonza

1. Reorganizar el frontend por dominios sin cambiar contratos.
2. Introducir React Router y eliminar el enrutador manual progresivamente.
3. Crear capa `src/api/` con estados de carga y error.
4. Preparar pantallas de inicio de sesión y portal del cliente usando datos simulados tipados.
5. Mejorar responsive, accesibilidad y consistencia visual.
6. Añadir pruebas Vitest por cada flujo modificado.

Cristian no conectará Supabase directamente a tablas comerciales. El login utilizará Supabase Auth y el resto de datos llegará mediante FastAPI.

## Archivos compartidos y turnos

| Archivo o zona | Regla |
| --- | --- |
| `contracts/openapi.json` | Lo genera y entrega backend; frontend solo consume |
| `docs/SEGUIMIENTO.md` | Cada integrante actualiza exclusivamente sus tareas terminadas |
| `README.md` | Solo se cambia cuando un PR altera comandos o estructura |
| `.github/workflows/ci.yml` | Responsable principal; Cristian propone cambios en su PR |
| `frontend/package-lock.json` | Solo quien esté trabajando en frontend |
| Migraciones Supabase | Solo backend; una migración por cambio lógico |

Si ambos necesitan el mismo archivo, el segundo espera a que el primer cambio llegue a `main`, actualiza su rama y recién continúa.

## Rutina durante el día

### Inicio de una sesión

```powershell
git status --short
git fetch origin
git rebase origin/main
```

Confirmar que se está en la rama propia y que no existan cambios ajenos sin guardar. Leer mensajes del compañero y seleccionar una tarea del seguimiento.

### Antes de cada commit

1. Ejecutar las pruebas de la zona modificada.
2. Ejecutar `git diff --check`.
3. Revisar que no haya secretos ni archivos generados.
4. Actualizar evidencia en `docs/SEGUIMIENTO.md` si la tarea terminó.
5. Crear un commit con un solo propósito.

### Sincronización intermedia

- Enviar commits pequeños al remoto durante el día.
- Avisar al compañero cuando cambie OpenAPI, una migración o una variable de entorno.
- No esperar al final del día para descubrir conflictos.
- Abrir PR temprano como borrador si la tarea dura varias horas.

### Cierre del día

1. Ejecutar `scripts/verify.ps1` en la rama.
2. Rebasar sobre `main` y resolver conflictos en la rama, nunca en `main`.
3. Subir la rama y abrir o actualizar el PR.
4. Registrar trabajo terminado, pendiente y bloqueos.

## Protocolo de cambio de API

1. Backend modifica esquema, ruta y prueba.
2. Backend ejecuta el exportador OpenAPI.
3. Backend incluye `contracts/openapi.json` en el mismo commit.
4. Cristian actualiza su rama desde `main`.
5. Frontend regenera o adapta sus tipos.
6. CI verifica frontend y backend antes de integrar.

No se aceptan cambios de API comunicados solo por chat: el contrato versionado es la referencia.

## Resolución de conflictos

- No elegir automáticamente “ours” o “theirs” en contratos, migraciones o configuración.
- Entender ambos cambios y conservar el comportamiento requerido.
- Si el conflicto afecta el contrato, backend decide el esquema final y frontend adapta el consumo.
- Después de resolver, ejecutar todas las pruebas, no solo las del archivo conflictivo.
- Registrar una decisión cuando el conflicto cambie alcance o arquitectura.

## Criterio para integrar un PR

- Alcance concreto y explicado.
- Sin secretos ni artefactos temporales.
- Pruebas locales aprobadas.
- CI aprobado.
- OpenAPI actualizado cuando corresponde.
- Documentación y seguimiento actualizados.
- Sin cambios accidentales en carpetas propiedad del compañero.

