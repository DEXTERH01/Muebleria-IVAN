# Seguimiento de Mueblería Iván

## Estado general

- Fecha de referencia: 2026-11-21.
- Fase actual: Fase 2, base de datos y autenticación.
- Estado: Fase 2 sigue abierta hasta validar Supabase publicado y sus permisos reales. La integración React Auth ya está en `main`. En la última validación backend pasaron 70 pruebas por grupos, se omitieron 3 de PostgreSQL por falta de `SUPABASE_TEST_DATABASE_URL` y se excluyó 1 prueba HTTP de catálogo cuyo proceso queda esperando al finalizar en Windows. Los modelos coinciden con las columnas declaradas en la migración. Las Fases 3 y 4 tienen sus flujos principales implementados y la Fase 5 solo conserva la visualización administrativa y la validación PostgreSQL.
- Fuente de alcance: `docs/PLAN_MAESTRO.md`.
- Próxima puerta de control: publicar Supabase, aplicar migración y seed, ejecutar pgTAP y `backend/tests/integration/` con `SUPABASE_TEST_DATABASE_URL`; en paralelo, Cristian completa la visualización frontend de algoritmos.
- Avance global: 9 fases numeradas (0–8); Fase 1 está cumplida, Fase 0 está definida pero conserva dos pendientes administrativos (fecha/formato de entrega y duración de exposición), Fase 2 está activa y quedan 6 fases posteriores (3–8). En total, 7 fases numeradas siguen abiertas o por iniciar si se cuenta también la fase activa.

## Cómo actualizar este seguimiento

1. Marcar una tarea solo cuando exista evidencia.
2. Añadir la ruta, URL, prueba o captura en la columna de evidencia.
3. No marcar una fase como terminada si falta su criterio de salida.
4. Registrar decisiones que cambien el plan.
5. Registrar bloqueos con una acción concreta, no solo con una descripción.

## Responsables

| Rol | Responsable |
| --- | --- |
| Product owner y analista | Dexter |
| UX y frontend | Cristian Gonza |
| Backend | Dexter y Cristian Gonza, separados por módulo |
| Base de datos | Cristian Gonza, revisión de Dexter |
| IA y datos | Dexter, revisión compartida |
| DevOps y QA | Dexter, validación compartida |
| Documentación y exposición | Equipo completo |

## Fase 0. Definición y control

| Estado | Tarea | Evidencia |
| --- | --- | --- |
| Hecho | Revisar el estado técnico actual | `README.md`, `frontend/src/` |
| Hecho | Crear el plan maestro | `docs/PLAN_MAESTRO.md` |
| Hecho | Crear el seguimiento por fases | `docs/SEGUIMIENTO.md` |
| Hecho | Definir e integrar la identidad visual | `frontend/public/assets/brand/` |
| Hecho | Revisar y aprobar los requisitos con el equipo | `docs/PLAN_MAESTRO.md` |
| Hecho | Asignar responsables y zonas de trabajo | Tabla de responsables, `docs/PLAN_TRABAJO_PARALELO.md` |
| Hecho | Separar frontend, backend, contratos, datos y Supabase | Estructura raíz del repositorio |
| Pendiente | Confirmar fecha y formato de entrega del Avance 3 | Por registrar |
| Pendiente | Definir duración disponible para la exposición | Por registrar |

Criterio de salida: el alcance es entendido, los responsables están asignados y los requisitos oficiales están aprobados.

## Fase 1. Base técnica

- [x] Crear `backend/` y configuración del proyecto Python. Evidencia: `backend/pyproject.toml`, `backend/app/`.
- [x] Implementar `/health`. Evidencia: `backend/app/api/routes/health.py`.
- [x] Habilitar documentación OpenAPI. Evidencia: `backend/app/main.py`.
- [x] Añadir configuración por variables de entorno. Evidencia: `backend/app/core/config.py`, `backend/.env.example`.
- [x] Añadir prueba inicial de API. Evidencia: `backend/tests/`.
- [x] Añadir Vitest al frontend. Evidencia: `frontend/src/pages/HomePage.test.tsx`, `frontend/vite.config.ts`.
- [x] Crear pipeline inicial de frontend y backend. Evidencia: `.github/workflows/ci.yml`.
- [x] Documentar comandos locales. Evidencia: `README.md`, `backend/README.md`.

Criterio de salida: frontend y backend construyen y sus pruebas se ejecutan localmente.

## Fase 2. Base de datos y autenticación

- [x] Definir el modelo completo y sus criterios. Responsable: equipo. Evidencia: `docs/BASE_DATOS.md`.
- [ ] Crear proyecto de Supabase para demo. Responsable: Cristian.
- [x] Crear migración base completa. Responsable: Cristian; revisión: Dexter. Evidencia: `supabase/migrations/20261121000100_initial_schema.sql`; ejecución local pendiente.
- [x] Crear seed reproducible. Responsable: Cristian. Evidencia: `supabase/seed.sql`; ejecución local pendiente.
- [x] Implementar RLS, perfiles y roles. Responsable: Cristian; revisión: Dexter. Evidencia: migración y pruebas `supabase/tests/database/03_rls_test.sql`; ejecución pgTAP pendiente.
- [x] Preparar conexión, sesiones y modelo de perfil SQLAlchemy. Responsable: Dexter. Evidencia: `backend/app/core/database.py`, `backend/app/models/profile.py`, `backend/tests/test_security.py`. `Profile` coincide con `app.profiles`: enum `app.user_role`, columnas `text`, timestamps no nulos y FK a `auth.users`.
- [x] Integrar Supabase Auth en React. Responsable: Cristian. Evidencia: `frontend/src/auth/`, `frontend/src/api/client/supabase.ts`, `frontend/.env.example`; prueba de UI en `frontend/src/auth/AuthPage.test.tsx`. Falta validar con proyecto Supabase real.
- [x] Verificar JWT de firma asimétrica en FastAPI y rol desde perfil. Responsable: Dexter. Evidencia: `backend/app/core/security.py`, `backend/app/api/v1/auth.py`, `backend/tests/test_security.py`, `backend/tests/test_auth_endpoint.py`. CurrentUser incluye `full_name`, `phone`, `created_at`. Pendiente prueba con proyecto Supabase real.
- [ ] Probar permisos de visitante, cliente, operador y administrador. Responsable: ambos.
- [ ] Probar aislamiento entre clientes. Responsable: ambos.

Integración PostgreSQL añadida en `backend/tests/integration/test_profile_postgres.py`; sus tres casos se omiten si no se define `SUPABASE_TEST_DATABASE_URL`. En esta verificación no estaban disponibles Supabase CLI, Docker ni `psql`, y la variable no está configurada, por lo que no se pudo ejecutar la migración ni las pruebas de base de datos. La migración, seed y pruebas pgTAP de Cristian están integradas desde `codex/database-catalog` (`1f4480e`).

Criterio de salida: todos los roles tienen permisos comprobados mediante pruebas positivas y negativas.

## Fase 3. Catálogo y cotizaciones

- [x] Migrar productos a PostgreSQL.
- [x] Implementar endpoints de catálogo.
- [x] Implementar administración del catálogo.
- [x] Migrar reglas del cotizador al backend.
- [x] Persistir cotizaciones.
- [x] Generar cliente TypeScript desde OpenAPI. Evidencia: `frontend/src/api/generated/schema.d.ts`, `frontend/src/api/modules/`.
- [x] Reemplazar datos locales del catálogo.
- [x] Añadir pruebas del cálculo de precios.

Criterio de salida: catálogo y cotización funcionan sin depender de datos escritos en el frontend.

## Fase 4. Operación del taller

Avance local: están implementados clientes, conversión de cotizaciones aprobadas a pedidos, lectura y transiciones de pedidos con historial, pagos idempotentes con reversión auditada y endpoints para firmar cargas y registrar vouchers privados de Cloudinary. El frontend permite consultar cotizaciones propias, revisar y aprobar cotizaciones como administrador y convertirlas con dirección de entrega. La instalación con saldo pendiente requiere administrador y motivo. Falta validar cargas reales con Cloudinary, asociar imágenes a productos y probar el flujo completo contra Supabase.

- [x] Convertir cotización a pedido. Evidencia: `backend/app/api/v1/orders.py`, `backend/app/schemas/order.py`, `backend/tests/test_operations_api.py`.
- [x] Implementar estados y transiciones. Evidencia: `backend/app/api/v1/orders.py`, `backend/tests/test_operations_api.py`.
- [x] Guardar historial de estados. Evidencia: `backend/app/models/order_status_event.py`, `backend/app/api/v1/orders.py`.
- [x] Implementar clientes. Evidencia: `backend/app/api/v1/customers.py`, `backend/app/schemas/customer.py`.
- [x] Implementar pagos con idempotencia. Evidencia: `backend/app/api/v1/payments.py`, `backend/tests/test_operations_api.py`.
- [x] Implementar reversión de pagos. Evidencia: `backend/app/api/v1/payments.py`, `backend/app/models/audit_log.py`.
- [x] Integrar Cloudinary para productos. Evidencia: `backend/app/api/v1/catalog.py`, `frontend/src/api/modules/media.ts`, `frontend/src/pages/admin/CatalogAdminPage.tsx`. Validación con cuenta real pendiente.
- [x] Integrar Cloudinary privado para vouchers. Evidencia: `backend/app/api/v1/media.py`, `backend/tests/test_operations_api.py`.
- [x] Sustituir `localStorage` por la API FastAPI de pedidos y pagos. Evidencia: `frontend/src/hooks/useOrders.ts`, `frontend/src/api/modules/orders.ts`.
- [x] Probar el flujo completo. Evidencia: `backend/tests/integration/test_phase4_workflow_postgres.py`; ejecutado contra Supabase local con JWT real y PostgreSQL migrado, desde cotización hasta instalación con aislamiento entre clientes, conversión idempotente, 8 eventos de estado, 2 pagos y saldo final cero.

Criterio de salida: cotización, pedido, producción, pago e instalación funcionan de extremo a extremo.

## Fase 5. Algoritmos de búsqueda

- Avance local: A* y Hill Climbing ya están conectados a endpoints consultivos y cada ejecución se guarda en `app.optimization_runs`. A* usa matrices simétricas de distancias y Hill Climbing aplica la función documentada con reinicios aleatorios reproducibles. Ninguno modifica pedidos automáticamente y las distancias no representan tráfico real. Falta la visualización administrativa y la prueba contra PostgreSQL publicado.
- [x] Definir dataset de rutas y distancias. Evidencia: `backend/app/algorithms/route_dataset.py`.
- [x] Implementar A*. Evidencia: `backend/app/algorithms/astar.py`.
- [x] Crear línea base para rutas. Evidencia: el orden recibido se usa como ruta inicial en `optimize_route`.
- [x] Medir ruta, nodos y tiempo. Evidencia: `AStarRouteResult` en `backend/app/algorithms/astar.py`.
- [x] Definir función objetivo de producción. Evidencia: `ProductionWeights` y `score_sequence` en `backend/app/algorithms/hill_climbing.py`.
- [x] Implementar Hill Climbing. Evidencia: `backend/app/algorithms/hill_climbing.py`.
- [x] Añadir reinicios aleatorios. Evidencia: semilla y reinicios configurables en `optimize_production_sequence`.
- [x] Comparar secuencia inicial y optimizada. Evidencia: `HillClimbingResult` y `POST /api/v1/optimizations/production`.
- [ ] Crear visualizaciones en administración.
- [x] Persistir ejecuciones y métricas. Evidencia: `backend/app/api/v1/optimizations.py`, `app.optimization_runs`.

Criterio de salida: A* y Hill Climbing tienen pruebas, resultados reproducibles y comparación contra una línea base.

## Fase 6. Machine learning

- [ ] Crear generador reproducible de 500 pedidos sintéticos.
- [ ] Documentar columnas y relaciones del dataset.
- [ ] Separar entrenamiento, validación y prueba.
- [ ] Entrenar modelos de regresión.
- [ ] Entrenar modelos de clasificación.
- [ ] Ejecutar K-Means y DBSCAN.
- [ ] Calcular métricas adecuadas.
- [ ] Comparar contra líneas base.
- [ ] Versionar el modelo aprobado.
- [ ] Servir inferencia desde FastAPI.
- [ ] Implementar fallback a reglas.
- [ ] Etiquetar resultados obtenidos con datos de prueba.

Criterio de salida: modelos reproducibles, evaluados, versionados e integrados sin métricas hardcodeadas.

## Fase 7. Calidad y experiencia

- [ ] Cubrir flujos críticos con pruebas unitarias.
- [ ] Añadir pruebas de integración de API y base de datos.
- [ ] Añadir pruebas E2E con Playwright.
- [ ] Revisar responsive.
- [ ] Revisar accesibilidad.
- [ ] Preparar protocolo de prueba de usuario.
- [ ] Ejecutar pruebas con cinco a ocho participantes.
- [ ] Calcular SUS y tasa de tareas completadas.
- [ ] Medir P50, P95, errores e inferencia.
- [ ] Corregir problemas prioritarios.

Criterio de salida: flujos críticos aprobados y resultados reales documentados.

## Fase 8. Despliegue y presentación

- [ ] Desplegar frontend en Netlify.
- [ ] Desplegar backend en Render.
- [ ] Configurar Supabase y Cloudinary de demo.
- [ ] Configurar variables y CORS.
- [ ] Validar pipeline de despliegue.
- [ ] Ejecutar smoke test en producción de demo.
- [ ] Preparar informe de métricas.
- [ ] Preparar arquitectura final.
- [ ] Preparar guion de demostración.
- [ ] Preparar capturas y video de respaldo.
- [ ] Ensayar la exposición completa.

Criterio de salida: una persona externa puede verificar el prototipo y repetir el guion.

## Registro de decisiones

| ID | Fecha | Decisión | Motivo | Impacto | Responsable |
| --- | --- | --- | --- | --- | --- |
| D-001 | 2026-11-21 | Usar React y TypeScript para el frontend | El prototipo existente ya utiliza estas tecnologías | Se conserva y adapta el frontend actual | Cristian Gonza |
| D-002 | 2026-11-21 | Usar Python y FastAPI para el backend | Favorece OpenAPI, rapidez de desarrollo y ML | Se implementó la base técnica del backend | Dexter |
| D-003 | 2026-11-21 | Usar un monolito modular | Reduce complejidad operativa y académica | No se crearán microservicios | Equipo completo |
| D-004 | 2026-11-21 | Utilizar un dataset inicial controlado de prueba | Todavía no existe suficiente historial digital | Las métricas iniciales validan el prototipo y no reemplazan métricas operativas | Dexter |
| D-005 | 2026-11-21 | Mantener las decisiones ML bajo supervisión humana | Evita automatización engañosa o sensible | ML será consultivo | Equipo completo |
| D-006 | 2026-11-21 | Adoptar Mueblería Iván como identidad pública única | Unificar empresa, web y presentación | Se actualizan interfaz, recursos y documentación | Equipo completo |
| D-007 | 2026-11-21 | Organizar el repositorio por frontend, backend, contratos, Supabase y datos | Permitir desarrollo paralelo con límites claros | Cristian trabaja en `frontend/`; el responsable principal en backend y datos | Equipo completo |
| D-008 | 2026-11-21 | Versionar OpenAPI como frontera entre ambos frentes | Evitar contratos verbales y cambios incompatibles | Backend genera el contrato y frontend lo consume | Equipo completo |
| D-009 | 2026-11-21 | Dividir el trabajo por módulos verticales y no por carpetas completas | Permite que ambos aporten a backend sin editar los mismos archivos | Cristian asume base de datos, catálogo y cotizaciones; Dexter plataforma, operación e IA | Equipo completo |
| D-010 | 2026-11-21 | Usar migraciones SQL de Supabase como única fuente de DDL | Auth, RLS, funciones y políticas requieren SQL específico de PostgreSQL; dos sistemas producirían divergencias | SQLAlchemy será ORM, pero no administrará migraciones con Alembic | Equipo completo |

## Bloqueos

| Fecha | Bloqueo | Impacto | Próxima acción | Responsable | Estado |
| --- | --- | --- | --- | --- | --- |
| 2026-11-21 | No existe suficiente historial digital para ML | Los primeros modelos no pueden validarse comercialmente | Usar datos de prueba, registrar operaciones y reevaluar modelos | Dexter | Abierto |
| 2026-11-21 | No se conoce la fecha exacta ni duración de exposición | Dificulta priorizar entregables | Confirmar con el docente | Equipo completo | Abierto |

## Evidencias finales esperadas

- URL pública del frontend.
- URL pública de Swagger.
- Repositorio con pipeline aprobado.
- Diagrama de arquitectura.
- Migraciones y seed reproducibles.
- Reporte de pruebas funcionales.
- Reporte de pruebas con usuarios.
- Reporte comparativo de algoritmos.
- Métricas reales de rendimiento.
- Capturas o video de respaldo.
- Lista de limitaciones y mejoras.
