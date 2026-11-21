# Plan de trabajo paralelo

## Objetivo

Dexter y Cristian Gonza desarrollarán frontend y backend en paralelo. La división será por módulos verticales para aprovechar a ambos sin editar simultáneamente los mismos archivos. OpenAPI, migraciones versionadas, ramas cortas y revisión cruzada serán los puntos de integración.

## Responsabilidades principales

| Integrante | Lidera | También participa |
| --- | --- | --- |
| Dexter | Plataforma FastAPI, autenticación/JWT, pedidos, producción, pagos, algoritmos, ML, CI/CD y despliegue | Revisión de base de datos y apoyo frontend |
| Cristian Gonza | PostgreSQL/Supabase, catálogo, cotizaciones, frontend, UX, accesibilidad y pruebas de interfaz | Endpoints, repositorios, servicios y pruebas backend de sus módulos |

Ninguna carpeta pertenece de forma exclusiva a una persona. La propiedad temporal corresponde a la tarea activa indicada en este plan.

## Entornos de trabajo

Cada integrante debe usar su propio clon o worktree. Dos personas o dos sesiones de Codex no deben trabajar en el mismo directorio porque las ramas y los archivos sin confirmar se comparten.

Antes de comenzar:

```powershell
git remote -v
git fetch origin
git switch main
git pull --ff-only
```

Ramas del primer ciclo:

```powershell
# Dexter
git switch -c codex/backend-auth-platform

# Cristian Gonza, desde su propio clon
git switch -c codex/database-catalog
```

No trabajar directamente en `main`. Una rama resuelve un paquete concreto; no debe convertirse en una rama permanente personal.

## Ciclo 1: base de datos y autenticación

### Cristian — DB-01 Base de datos completa

1. Leer `docs/BASE_DATOS.md`.
2. Configurar el proyecto local de Supabase sin subir credenciales.
3. Crear una migración base con esquemas, tipos, tablas, claves, restricciones e índices.
4. Crear perfiles vinculados a `auth.users`, funciones auxiliares y políticas RLS.
5. Crear un seed pequeño y determinista para desarrollo.
6. Añadir pruebas SQL de restricciones, roles y aislamiento entre clientes.
7. Documentar los comandos de `supabase db reset` y pruebas.

Archivos asignados: `supabase/`, `docs/BASE_DATOS.md` únicamente si se descubre una corrección necesaria.

### Dexter — BE-01 Plataforma y seguridad

1. Añadir SQLAlchemy y el driver PostgreSQL; las migraciones seguirán en `supabase/migrations/`.
2. Configurar la conexión, sesiones y transacciones.
3. Preparar modelos compatibles con el contrato de base de datos aprobado.
4. Verificar JWT de Supabase y crear dependencias de identidad/rol.
5. Implementar pruebas positivas y negativas de autenticación.
6. Preparar manejo uniforme de errores y request ID.

Archivos asignados: `backend/app/core/`, `backend/app/models/`, `backend/tests/core/` y `backend/pyproject.toml`.

### Integración del ciclo 1

Primero se integra DB-01. Dexter actualiza su rama con `main`, ajusta modelos si corresponde y termina BE-01. Ambos ejecutan un reset desde cero y las pruebas de permisos antes de cerrar la Fase 2.

## Ciclo 2: funcionalidades comerciales

### Cristian — BE-02 Catálogo y cotizaciones

- Esquemas Pydantic de productos y cotizaciones.
- Repositorios de catálogo y cotizaciones.
- Servicio de cálculo de precios.
- Endpoints públicos y administrativos correspondientes.
- Pruebas unitarias y de API.
- Integración del frontend con catálogo y cotización reales.

Módulos asignados: `products`, `catalog`, `quotes` y `pricing` en schemas, repositories, services, API y tests.

### Dexter — BE-03 Operación del taller

- Clientes, pedidos y conversión desde cotización.
- Transiciones de producción e historial.
- Pagos idempotentes y reversión auditada.
- Media privada para vouchers.
- Pruebas de concurrencia, permisos y reglas 50/50.

Módulos asignados: `customers`, `orders`, `production`, `payments`, `media` y `audit`.

## Ciclo 3: frontend avanzado, algoritmos y ML

### Cristian

- React Router y estructura por dominios.
- Cliente generado desde OpenAPI.
- Autenticación, portal del cliente y administración conectados.
- Responsive, accesibilidad, Vitest y Playwright.

### Dexter

- A* para entregas y Hill Climbing para producción.
- Dataset sintético reproducible.
- Regresión, clasificación y clustering con líneas base.
- Registro de experimentos, métricas e inferencia en FastAPI.

## Archivos de integración

| Archivo o zona | Integrador | Regla |
| --- | --- | --- |
| `contracts/openapi.json` | Dexter | Se genera después de integrar rutas; nunca se edita a mano |
| `backend/app/api/v1/router.py` | Dexter | Cristian entrega su router de módulo; Dexter lo registra al integrar |
| `backend/app/models/__init__.py` | Dexter | Exportaciones centrales después de integrar la migración |
| `backend/pyproject.toml` | Dexter | Cristian comunica dependencias nuevas en el PR |
| `supabase/migrations/` | Cristian en DB-01 | Una migración nueva por cambio; nunca reescribir una ya compartida |
| `frontend/package-lock.json` | Cristian durante trabajo frontend | No actualizarlo desde tareas backend |
| `.github/workflows/ci.yml` | Dexter | Cambios revisados por Cristian |
| `docs/SEGUIMIENTO.md` | Ambos | Cada uno actualiza únicamente sus tareas y evidencias |

Si ambos necesitan el mismo archivo, el segundo espera a que el primer PR llegue a `main`, actualiza su rama y continúa. No resolver contratos o migraciones eligiendo automáticamente “ours” o “theirs”.

## Rutina diaria

Al iniciar:

```powershell
git status --short
git fetch origin
git rebase origin/main
```

Antes de cada commit:

1. Ejecutar pruebas de la zona modificada.
2. Ejecutar `git diff --check`.
3. Revisar secretos, datos personales y artefactos generados.
4. Actualizar el seguimiento si la tarea terminó.
5. Crear un commit de un solo propósito.

Durante el día:

- Subir commits pequeños y abrir un PR borrador temprano.
- Avisar cuando cambie una migración, variable, endpoint o esquema.
- Revisar el PR del compañero antes de empezar una tarea dependiente.
- No mezclar cambios visuales, migraciones y lógica de negocio en el mismo commit.

Al cerrar:

```powershell
.\scripts\verify.ps1
git fetch origin
git rebase origin/main
git push
```

## Protocolo de API

1. El autor implementa esquema, servicio, endpoint y prueba en su módulo.
2. El PR explica campos nuevos, permisos y posibles incompatibilidades.
3. Dexter integra el router y genera `contracts/openapi.json`.
4. Cristian actualiza o regenera el cliente TypeScript.
5. CI verifica frontend y backend.

Un cambio no comunicado en OpenAPI no forma parte del contrato.

## Criterio para integrar un PR

- Alcance concreto y responsable identificado.
- Sin secretos, datos personales ni artefactos temporales.
- Migración reproducible cuando corresponda.
- Pruebas locales y CI aprobados.
- OpenAPI actualizado cuando corresponde.
- Seguimiento y documentación actualizados.
- Revisión de la otra persona en cambios de seguridad, base de datos o dinero.
