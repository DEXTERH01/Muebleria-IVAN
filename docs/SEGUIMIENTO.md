# Seguimiento de Mueblería Iván

## Estado general

- Fecha de referencia: 2026-11-21.
- Fase actual: Fase 0, definición y control.
- Estado: en curso.
- Fuente de alcance: `docs/PLAN_MAESTRO.md`.
- Próxima puerta de control: revisar el plan y asignar responsables.

## Cómo actualizar este seguimiento

1. Marcar una tarea solo cuando exista evidencia.
2. Añadir la ruta, URL, prueba o captura en la columna de evidencia.
3. No marcar una fase como terminada si falta su criterio de salida.
4. Registrar decisiones que cambien el plan.
5. Registrar bloqueos con una acción concreta, no solo con una descripción.

## Responsables

| Rol | Responsable |
| --- | --- |
| Product owner y analista | Por asignar |
| UX y frontend | Por asignar |
| Backend y datos | Por asignar |
| IA y datos | Por asignar |
| DevOps y QA | Por asignar |
| Documentación y exposición | Por asignar |

## Fase 0. Definición y control

| Estado | Tarea | Evidencia |
| --- | --- | --- |
| Hecho | Revisar el estado técnico actual | `README.md`, `src/` |
| Hecho | Crear el plan maestro | `docs/PLAN_MAESTRO.md` |
| Hecho | Crear el seguimiento por fases | `docs/SEGUIMIENTO.md` |
| Hecho | Definir e integrar la identidad visual | `public/assets/brand/` |
| Pendiente | Revisar y aprobar los requisitos con el equipo | Por registrar |
| Pendiente | Asignar responsables | Tabla de responsables |
| Pendiente | Confirmar fecha y formato de entrega del Avance 3 | Por registrar |
| Pendiente | Definir duración disponible para la exposición | Por registrar |

Criterio de salida: el alcance es entendido, los responsables están asignados y los requisitos oficiales están aprobados.

## Fase 1. Base técnica

- [ ] Crear `backend/` y configuración del proyecto Python.
- [ ] Implementar `/health`.
- [ ] Habilitar documentación OpenAPI.
- [ ] Añadir configuración por variables de entorno.
- [ ] Añadir prueba inicial de API.
- [ ] Añadir Vitest al frontend.
- [ ] Crear pipeline inicial de frontend y backend.
- [ ] Documentar comandos locales.

Criterio de salida: frontend y backend construyen y sus pruebas se ejecutan localmente.

## Fase 2. Base de datos y autenticación

- [ ] Crear proyecto de Supabase para demo.
- [ ] Crear migraciones iniciales.
- [ ] Crear seed reproducible.
- [ ] Implementar perfiles y roles.
- [ ] Integrar Supabase Auth en React.
- [ ] Verificar JWT en FastAPI.
- [ ] Probar permisos de visitante, cliente, operador y administrador.
- [ ] Probar aislamiento entre clientes.

Criterio de salida: todos los roles tienen permisos comprobados mediante pruebas positivas y negativas.

## Fase 3. Catálogo y cotizaciones

- [ ] Migrar productos a PostgreSQL.
- [ ] Implementar endpoints de catálogo.
- [ ] Implementar administración del catálogo.
- [ ] Migrar reglas del cotizador al backend.
- [ ] Persistir cotizaciones.
- [ ] Generar cliente TypeScript desde OpenAPI.
- [ ] Reemplazar datos locales del catálogo.
- [ ] Añadir pruebas del cálculo de precios.

Criterio de salida: catálogo y cotización funcionan sin depender de datos escritos en el frontend.

## Fase 4. Operación del taller

- [ ] Convertir cotización a pedido.
- [ ] Implementar estados y transiciones.
- [ ] Guardar historial de estados.
- [ ] Implementar clientes.
- [ ] Implementar pagos con idempotencia.
- [ ] Implementar reversión de pagos.
- [ ] Integrar Cloudinary para productos.
- [ ] Integrar Cloudinary privado para vouchers.
- [ ] Sustituir `localStorage`.
- [ ] Probar el flujo completo.

Criterio de salida: cotización, pedido, producción, pago e instalación funcionan de extremo a extremo.

## Fase 5. Algoritmos de búsqueda

- [ ] Definir dataset de rutas y distancias.
- [ ] Implementar A*.
- [ ] Crear línea base para rutas.
- [ ] Medir ruta, nodos y tiempo.
- [ ] Definir función objetivo de producción.
- [ ] Implementar Hill Climbing.
- [ ] Añadir reinicios aleatorios.
- [ ] Comparar secuencia inicial y optimizada.
- [ ] Crear visualizaciones en administración.
- [ ] Persistir ejecuciones y métricas.

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
| D-001 | 2026-11-21 | Usar React y TypeScript para el frontend | El prototipo existente ya utiliza estas tecnologías | Se conserva y adapta el frontend actual | Por asignar |
| D-002 | 2026-11-21 | Usar Python y FastAPI para el backend | Favorece OpenAPI, rapidez de desarrollo y ML | Se creará un backend nuevo | Por asignar |
| D-003 | 2026-11-21 | Usar un monolito modular | Reduce complejidad operativa y académica | No se crearán microservicios | Por asignar |
| D-004 | 2026-11-21 | Utilizar un dataset inicial controlado de prueba | Todavía no existe suficiente historial digital | Las métricas iniciales validan el prototipo y no reemplazan métricas operativas | Por asignar |
| D-005 | 2026-11-21 | Mantener las decisiones ML bajo supervisión humana | Evita automatización engañosa o sensible | ML será consultivo | Por asignar |
| D-006 | 2026-11-21 | Adoptar Mueblería Iván como identidad pública única | Unificar empresa, web y presentación | Se actualizan interfaz, recursos y documentación | Por asignar |

## Bloqueos

| Fecha | Bloqueo | Impacto | Próxima acción | Responsable | Estado |
| --- | --- | --- | --- | --- | --- |
| 2026-11-21 | No existe suficiente historial digital para ML | Los primeros modelos no pueden validarse comercialmente | Usar datos de prueba, registrar operaciones y reevaluar modelos | Por asignar | Abierto |
| 2026-11-21 | No se conoce la fecha exacta ni duración de exposición | Dificulta priorizar entregables | Confirmar con el docente | Por asignar | Abierto |

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
