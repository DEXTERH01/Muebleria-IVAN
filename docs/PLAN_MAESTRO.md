# Plan maestro de Mueblería Iván

## Propósito y decisión principal

Mueblería Iván es el negocio objetivo de este proyecto de transformación digital. El sistema integrará una experiencia web funcional, una API desacoplada, persistencia en la nube, gestión de imágenes, autenticación, algoritmos de búsqueda y modelos de machine learning.

Las reglas contenidas en este plan constituyen los requisitos oficiales del proyecto. El prototipo deberá ejecutar procesos reales de catálogo, cotización, pedidos, producción, pagos y seguimiento. Durante desarrollo y evaluación se utilizarán datos controlados de prueba; los indicadores comerciales solo se considerarán operativos cuando provengan de transacciones registradas por el sistema.

La decisión técnica base es construir un monolito modular con React y TypeScript en el frontend, Python y FastAPI en el backend, PostgreSQL y Auth en Supabase, imágenes en Cloudinary, frontend en Cloudflare Pages y backend en Render. No se usarán microservicios en esta etapa.

## Cómo se usará este plan

Este archivo es la fuente principal para alcance, reglas, arquitectura y orden de implementación. El avance diario se registrará en `docs/SEGUIMIENTO.md`.

Se aplicarán estas reglas de trabajo:

1. No iniciar una fase si no se cumplen los criterios de salida de la fase anterior.
2. No agregar funcionalidades fuera del alcance sin registrar primero la decisión.
3. Distinguir los datos controlados de prueba de los datos operativos de la empresa.
4. No mostrar métricas de ML escritas manualmente en la interfaz.
5. Toda funcionalidad debe tener una prueba o una evidencia verificable.
6. Los cambios de arquitectura, reglas de negocio o contratos deben actualizar este plan.
7. OpenAPI será el contrato ejecutable entre frontend y backend.

## Estado actual

El repositorio ya contiene un frontend React con:

- Página principal y catálogo.
- Detalle de producto.
- Cotizador referencial.
- Resumen de cotización y mensaje para WhatsApp.
- Panel administrativo.
- Pedidos y tablero de producción.
- Clientes y control de pagos.
- Analítica heurística.
- Asistente conversacional basado en reglas.

Las limitaciones actuales son:

- Los datos están escritos en archivos TypeScript.
- Los pedidos se guardan en `localStorage`.
- El backend solo cuenta con la base técnica y aún no implementa los módulos comerciales.
- No existe autenticación real.
- No existe base de datos remota integrada.
- La analítica utiliza fórmulas y valores simulados.
- No existen A*, Hill Climbing ni modelos ML entrenados.
- No existen pruebas automatizadas suficientes.
- No existe evidencia de pruebas con usuarios.

## Objetivo académico

El sistema deberá demostrar de forma integrada:

- Cloud y DevOps.
- Arquitectura desacoplada.
- Algoritmos de búsqueda A* y Hill Climbing.
- Regresión, clasificación y clustering.
- Comparación de algoritmos como KNN, SVM, árboles de decisión, K-Means y DBSCAN.
- Pruebas funcionales, de usuario, rendimiento y ML.
- Métricas calculadas y reproducibles.
- Un plan de mejora basado en resultados y limitaciones conocidas.

## Problema que resolverá el prototipo

Mueblería Iván necesita centralizar cotizaciones, pedidos, pagos y producción para evitar información dispersa en mensajes, hojas de cálculo y registros manuales. El sistema permitirá conocer el estado de los pedidos, estimar fechas, controlar saldos y decidir qué fabricar primero.

La plataforma de Mueblería Iván centralizará:

- Catálogo y captación de clientes.
- Cotización referencial de muebles personalizados.
- Seguimiento de pedidos.
- Control de producción.
- Registro de pagos.
- Priorización de trabajo y entregas.
- Analítica y predicciones de apoyo.

El sistema no tomará decisiones comerciales automáticamente. Las predicciones y optimizaciones serán recomendaciones que una persona podrá aceptar o ignorar.

## Usuarios y necesidades

### Visitante

Necesita conocer los productos, entender las opciones disponibles y obtener una estimación sin llamar primero a la mueblería.

### Cliente

Necesita guardar una cotización, consultar sus pedidos, conocer el avance y revisar su estado de pago.

### Operador

Necesita actualizar la producción, registrar actividades, consultar información del cliente y registrar pagos autorizados.

### Administrador

Necesita gestionar catálogo, precios, usuarios, cotizaciones, pedidos, pagos, producción, analítica y configuraciones.

### Evaluador académico

No será un rol de producción. Accederá a una cuenta demostrativa y a evidencias de pruebas, métricas, arquitectura y despliegue.

## Roles y permisos del sistema

| Acción | Visitante | Cliente | Operador | Administrador |
| --- | --- | --- | --- | --- |
| Ver catálogo | Sí | Sí | Sí | Sí |
| Calcular estimación | Sí | Sí | Sí | Sí |
| Enviar cotización | Sí | Sí | Sí | Sí |
| Ver cotizaciones propias | No | Sí | No | Sí |
| Ver pedidos propios | No | Sí | No | Sí |
| Ver todos los pedidos | No | No | Sí | Sí |
| Cambiar etapa de producción | No | No | Sí | Sí |
| Registrar pago | No | No | Sí | Sí |
| Anular o corregir pago | No | No | No | Sí |
| Gestionar catálogo y precios | No | No | No | Sí |
| Gestionar usuarios y roles | No | No | No | Sí |
| Ver analítica y optimizadores | No | No | Sí | Sí |
| Entrenar o activar modelos | No | No | No | Sí |

Supabase Auth gestionará la identidad. El frontend enviará el JWT a FastAPI y el backend verificará identidad y rol antes de ejecutar operaciones protegidas.

## Roles del equipo

Una persona puede ocupar varios roles, pero cada responsabilidad debe tener un responsable asignado en `docs/SEGUIMIENTO.md`.

| Rol de trabajo | Responsabilidad |
| --- | --- |
| Product owner y analista | Mantener alcance, requisitos, flujos y prioridades |
| UX y frontend | Interfaces, accesibilidad, consumo de API y experiencia de usuario |
| Backend y datos | API, reglas de negocio, base de datos, migraciones y seguridad |
| IA y datos | Dataset, algoritmos, entrenamiento, evaluación y versionado de modelos |
| DevOps y QA | CI/CD, despliegues, pruebas, observabilidad y rendimiento |
| Documentación y exposición | Evidencias, informe, diapositivas, guion y demostración |

## Requisitos de negocio establecidos

| ID | Requisito obligatorio |
| --- | --- |
| RN-01 | Mueblería Iván fabrica muebles personalizados y muestra modelos de referencia en su catálogo |
| RN-02 | El esquema de pago es 50% de anticipo y 50% de saldo antes de completar la entrega |
| RN-03 | La moneda de trabajo es el sol peruano, código PEN |
| RN-04 | El usuario ingresa medidas en centímetros y la API las normaliza a milímetros |
| RN-05 | Las etapas son confirmado, materiales, corte, armado, acabado, listo, entregado e instalado |
| RN-06 | Los operadores actualizan producción y registran pagos, pero no modifican precios ni roles |
| RN-07 | Una cotización referencial tiene una vigencia de siete días |
| RN-08 | Los vouchers se almacenan como recursos privados |
| RN-09 | El cliente se autentica por correo en la primera versión |
| RN-10 | Las predicciones y optimizaciones apoyan la decisión humana y no ejecutan cambios automáticos |
| RN-11 | Los cambios sensibles deben registrar usuario, fecha, valor anterior y valor nuevo |
| RN-12 | Los clientes solo pueden consultar sus propias cotizaciones y pedidos |

## Alcance del Avance 3

### Incluido

- Catálogo público conectado al backend.
- Cotizador con reglas de precios centralizadas.
- Autenticación y autorización por roles.
- Cotizaciones persistentes.
- Pedidos y seguimiento de producción.
- Clientes y pagos 50/50.
- Imágenes de productos y vouchers mediante Cloudinary.
- Dashboard con datos provenientes de PostgreSQL.
- A* para optimización demostrativa de entregas.
- Hill Climbing para ordenar la producción.
- Regresión para estimar días de fabricación.
- Clasificación para riesgo de retraso.
- Clustering para segmentar clientes.
- Dataset inicial de prueba reproducible y claramente separado de los datos operativos.
- Pruebas automatizadas y pruebas con usuarios.
- Despliegue público y CI/CD.

### Fuera del alcance

- Pasarela de pago real.
- Facturación electrónica o integración con SUNAT.
- Optimización industrial certificada de cortes de tableros.
- GPS y tráfico en tiempo real.
- Integración automática con WhatsApp Business.
- Gestión contable completa.
- Inventario o compras tipo ERP.
- Aplicación móvil nativa.
- Certificación comercial de modelos con historial operativo de largo plazo.
- Decisiones de crédito, precios o empleo tomadas automáticamente.

## Flujos principales

### Cotización a pedido

1. El visitante explora el catálogo.
2. Selecciona un producto o tipo de mueble.
3. Ingresa medidas, material, acabado, accesorios y distrito.
4. El backend calcula el precio referencial y el intervalo de entrega.
5. El visitante envía la cotización con sus datos de contacto.
6. El administrador revisa y aprueba, rechaza o ajusta la cotización.
7. Una cotización aprobada se convierte en pedido.
8. El anticipo se registra antes de iniciar la producción, salvo una excepción auditada.

### Producción y entrega

1. El pedido se confirma.
2. Se verifica o compra el material.
3. El pedido pasa por corte, armado y acabado.
4. El sistema calcula riesgo de retraso en cada actualización.
5. Cuando está listo, se registra o verifica el saldo.
6. El pedido se entrega y posteriormente se marca como instalado.
7. Cada cambio queda en un historial inmutable.

### Optimización del taller

1. El operador selecciona pedidos activos.
2. Hill Climbing genera una secuencia sugerida.
3. La interfaz compara la secuencia actual y la propuesta.
4. El operador acepta o descarta la propuesta.
5. La decisión y la mejora calculada quedan registradas para la demostración.

### Optimización de entregas

1. El operador selecciona pedidos listos.
2. A* evalúa rutas usando un grafo o matriz de distancias del prototipo.
3. La interfaz muestra distancia, costo, nodos explorados y tiempo de ejecución.
4. La ruta se presenta como recomendación, no como navegación real.

## Reglas de negocio

1. Una estimación no es una cotización aprobada ni un contrato.
2. El precio se calcula en el backend; el frontend solo presenta el resultado.
3. Los importes se transmiten como enteros en céntimos para evitar errores de punto flotante.
4. Las dimensiones canónicas se almacenan como enteros en milímetros.
5. El anticipo predeterminado es 50% del total.
6. El saldo es total menos pagos verificados y nunca puede ser negativo.
7. Un mismo pago no puede registrarse dos veces; se utilizará una clave de idempotencia.
8. Un pago registrado no se elimina. Una corrección se realiza mediante reversión auditada.
9. Los estados solo pueden avanzar mediante transiciones permitidas.
10. Un pedido no se marca como instalado con saldo pendiente, salvo excepción del administrador con motivo registrado.
11. Los códigos visibles son diferentes de los UUID internos.
12. Toda actualización sensible registra usuario, fecha y cambio realizado.
13. Ninguna predicción modifica por sí sola un pedido, pago o precio.

## Estados canónicos

### Cotización

`draft`, `submitted`, `reviewing`, `approved`, `rejected`, `expired`, `converted`.

### Pedido

`confirmed`, `materials_pending`, `cutting`, `assembly`, `finishing`, `ready`, `delivered`, `installed`, `cancelled`.

La migración desde el prototipo actual será:

| Estado actual | Estado nuevo |
| --- | --- |
| `material-pendiente` | `materials_pending` |
| `corte` | `cutting` |
| `armado` | `assembly` |
| `listo` | `ready` |
| `instalado` | `installed` |

### Pago del pedido

`pending_deposit`, `deposit_paid`, `partial`, `paid`, `voided`.

## Identidad visual

El nombre público y oficial de la empresa dentro del sistema es **Mueblería Iván** y será el único nombre utilizado en interfaces, documentación y metadatos públicos.

El recurso oficial es `frontend/public/assets/brand/muebleria-ivan-logo.svg`: una marca de línea inspirada en un mueble, utilizada en navegación, panel administrativo y favicon. El nombre Mueblería Iván se presenta como texto accesible fuera del ícono.

La paleta principal usa marrón nogal `#3B2416`, madera cálida `#7A5136`, arena `#DCC3A4` y fondo crema. El logo se mostrará sobre fondos claros y conservará su transparencia, proporción y espacio libre. No se deformará, recoloreará ni acompañará con otro nombre comercial.

## Arquitectura

```text
Navegador
  |
  | HTTPS, JSON, JWT
  v
React + TypeScript + Vite en Cloudflare Pages
  |                     |
  | autenticación       | carga directa firmada
  v                     v
Supabase Auth        Cloudinary
  |
  | JWT
  v
FastAPI en Render
  |-- catálogo y cotizaciones
  |-- pedidos, producción y pagos
  |-- firmas de Cloudinary
  |-- A* y Hill Climbing
  |-- inferencia de modelos ML
  |
  v
PostgreSQL en Supabase
```

El frontend no accederá directamente a las tablas comerciales. Solo utilizará Supabase desde el navegador para autenticación. FastAPI será el punto de entrada de las reglas de negocio.

## Tecnologías aprobadas

| Capa | Tecnología |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| Estilos | CSS existente, diseño responsive |
| API | Python, FastAPI, Pydantic |
| Persistencia | PostgreSQL en Supabase |
| ORM y migraciones | SQLAlchemy como ORM; Supabase CLI y SQL como sistema único de migraciones |
| Autenticación | Supabase Auth y JWT |
| Imágenes | Cloudinary |
| ML | Scikit-learn, CatBoost opcional, Prophet cuando corresponda |
| Asistente generativo | Groq mediante FastAPI, con bot local como fallback |
| Pruebas frontend | Vitest, Testing Library y Playwright |
| Pruebas backend | Pytest y HTTPX |
| CI/CD | GitHub Actions |
| Hosting frontend | Cloudflare Pages |
| Hosting backend | Render |
| Contrato | OpenAPI 3.1 generado por FastAPI |

## Estructura objetivo del repositorio

```text
Muebleria Ivan/
|-- frontend/
|   |-- public/
|   |-- src/
|   |-- package.json
|   `-- vite.config.ts
|-- backend/
|   |-- app/
|   |   |-- api/v1/
|   |   |-- core/
|   |   |-- domain/
|   |   |-- models/
|   |   |-- schemas/
|   |   |-- repositories/
|   |   |-- services/
|   |   |-- algorithms/
|   |   `-- ml/
|   |-- tests/
|   `-- pyproject.toml
|-- supabase/
|   |-- migrations/
|   |-- seed.sql
|   `-- tests/
|-- data/
|   |-- synthetic/
|   `-- README.md
|-- contracts/
|   `-- openapi.json
|-- docs/
|   |-- PLAN_MAESTRO.md
|   |-- PLAN_TRABAJO_PARALELO.md
|   |-- FRONTEND_ROADMAP.md
|   `-- SEGUIMIENTO.md
|-- scripts/
|-- .github/workflows/
|-- AGENTS.md
`-- README.md
```

## Módulos y pantallas

### Experiencia pública

- Inicio.
- Catálogo y filtros.
- Detalle de producto y galería.
- Cotizador.
- Resultado de cotización.
- Registro e inicio de sesión.
- Consulta de seguimiento autenticada.
- Asistente Mía híbrido: reglas para datos del catálogo y pedidos, y Groq para orientación general; nunca envía credenciales ni datos privados de pedidos al proveedor.

### Portal del cliente

- Cotizaciones propias.
- Pedidos propios.
- Detalle y línea de tiempo.
- Estado de pago.
- Datos personales básicos.

### Administración

- Dashboard.
- Cotizaciones.
- Pedidos.
- Tablero de producción.
- Clientes.
- Pagos.
- Catálogo, materiales, acabados y accesorios.
- Analítica.
- Optimización de producción.
- Optimización de entregas.
- Usuarios y roles.

## Modelo de datos inicial

| Tabla | Propósito |
| --- | --- |
| `profiles` | Datos públicos mínimos y rol de usuarios autenticados |
| `customers` | Datos del cliente asociados a un perfil o contacto |
| `delivery_locations` | Direcciones y coordenadas autorizadas para entregas y A* |
| `products` | Productos o modelos de referencia |
| `product_images` | Metadatos y orden de imágenes en Cloudinary |
| `materials` | Materiales, costo base y disponibilidad |
| `finishes` | Acabados disponibles |
| `accessories` | Accesorios y costo |
| `product_materials`, `product_finishes`, `product_accessories` | Opciones permitidas por producto |
| `pricing_rules` | Reglas versionadas para estimar precios |
| `quotes` | Cabecera, contacto, estado y totales de cotización |
| `quote_items` | Configuración y desglose de cada mueble cotizado |
| `orders` | Pedido, fechas, total, estado y versión de concurrencia |
| `order_items` | Snapshot inmutable de productos y precios aprobados |
| `order_status_events` | Historial de etapas y duración |
| `production_jobs` | Planificación y tiempos de producción |
| `deliveries` | Ventanas y secuencias de entrega optimizadas |
| `payments` | Pagos, método, monto, voucher e idempotencia |
| `media_assets` | Identificador, tipo, acceso y propietario del recurso |
| `customer_events` | Eventos autorizados para recomendaciones y análisis |
| `model_versions` | Algoritmo, versión, métricas y fecha de activación |
| `predictions` | Entrada resumida, salida, modelo y resultado real posterior |
| `optimization_runs` | Algoritmo, entrada, resultado, mejora y tiempo de ejecución |
| `audit_logs` | Cambios sensibles realizados por usuarios |

Las tablas de negocio estarán en un esquema no expuesto directamente al navegador. Se aplicarán restricciones, índices, claves foráneas y migraciones reproducibles. Los campos, controles, permisos, seed y criterio de finalización se especifican en `docs/BASE_DATOS.md`.

## Contrato de API

### Convenciones

- Prefijo: `/api/v1`.
- JSON en `camelCase`.
- Base de datos en `snake_case`.
- UUID para identificadores internos.
- Códigos visibles como `COT-2026-0001` y `PED-2026-0001`.
- Dinero en céntimos mediante campos terminados en `Minor`.
- Medidas en milímetros mediante campos terminados en `Mm`.
- Fechas civiles en `YYYY-MM-DD`.
- Instantes en UTC con ISO 8601.
- Paginación con `page`, `pageSize` y `total`.
- `Idempotency-Key` obligatorio para registrar pagos y conversiones críticas.
- Campo `version` para detectar actualizaciones concurrentes.

Respuesta exitosa:

```json
{
  "data": {}
}
```

Respuesta de error:

```json
{
  "error": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "El pedido no puede pasar a la etapa solicitada.",
    "details": {},
    "requestId": "uuid"
  }
}
```

### Endpoints mínimos

| Método | Ruta | Acceso | Función |
| --- | --- | --- | --- |
| `GET` | `/health` | Público | Salud del servicio |
| `GET` | `/api/v1/products` | Público | Catálogo paginado |
| `GET` | `/api/v1/products/{slug}` | Público | Detalle de producto |
| `POST` | `/api/v1/quotes/estimate` | Público | Estimar precio y entrega |
| `POST` | `/api/v1/quotes` | Público o cliente | Enviar cotización |
| `GET` | `/api/v1/quotes/{id}` | Propietario o admin | Consultar cotización |
| `PATCH` | `/api/v1/quotes/{id}/status` | Admin | Revisar cotización |
| `POST` | `/api/v1/quotes/{id}/convert` | Admin | Convertir a pedido |
| `GET` | `/api/v1/orders` | Operador o admin | Listar pedidos |
| `GET` | `/api/v1/orders/{id}` | Autorizado | Detalle de pedido |
| `PATCH` | `/api/v1/orders/{id}/status` | Operador o admin | Cambiar etapa |
| `POST` | `/api/v1/orders/{id}/payments` | Operador o admin | Registrar pago |
| `POST` | `/api/v1/payments/{id}/void` | Admin | Revertir pago |
| `POST` | `/api/v1/media/signature` | Autenticado | Firmar carga a Cloudinary |
| `GET` | `/api/v1/analytics/overview` | Operador o admin | Indicadores reales |
| `POST` | `/api/v1/optimizations/production` | Operador o admin | Ejecutar Hill Climbing |
| `POST` | `/api/v1/optimizations/delivery` | Operador o admin | Ejecutar A* |
| `GET` | `/api/v1/ml/models` | Admin | Ver modelos y métricas |

Los endpoints técnicos de predicción no serán consumidos directamente por el cliente. La cotización y el detalle del pedido incluirán las predicciones pertinentes.

## Algoritmos de búsqueda

### A* para entregas

El estado representará la ubicación actual y los puntos pendientes de visita. El costo acumulado será la distancia recorrida y la heurística será una cota inferior calculada con distancias directas entre puntos.

La demostración deberá reportar:

- Ruta inicial y ruta recomendada.
- Distancia total.
- Nodos explorados.
- Tiempo de ejecución.
- Mejora frente a una ruta base.

El prototipo utilizará coordenadas o una matriz de distancias sintética. No afirmará usar tráfico real.

### Hill Climbing para producción

Cada estado será un orden posible de los pedidos activos. Un vecino se obtendrá intercambiando dos pedidos. La función objetivo inicial será:

```text
puntaje = 10 * días_de_retraso
        + 3 * cambios_de_material
        + 2 * horas_ociosas
```

Los pesos son parámetros iniciales de la política de priorización y serán configurables por un administrador. El algoritmo deberá registrar estado inicial, iteraciones, resultado, mejora y motivo de parada. Se incluirán reinicios aleatorios para reducir el efecto de máximos o mínimos locales.

## Machine learning

### Dataset

Se generará un dataset inicial reproducible de 500 pedidos de prueba con semilla fija para comprobar el pipeline antes de contar con suficiente historial digital. Incluirá relaciones controladas entre complejidad, dimensiones, accesorios, carga del taller, duración y retraso.

Todo gráfico o resultado obtenido de ese conjunto mostrará la etiqueta `Datos de prueba`. Los registros creados por la operación del sistema se almacenarán por separado y reemplazarán progresivamente el conjunto inicial para futuras evaluaciones.

### Regresión

Objetivo: predecir `production_days`.

Modelos candidatos:

- Regresión lineal como línea base.
- Árbol de decisión.
- Random Forest.
- CatBoost si mejora de manera válida el resultado.

Métricas: MAE, RMSE y R². La interfaz mostrará un intervalo y nivel de confianza, no una fecha exacta sin incertidumbre.

### Clasificación

Objetivo: predecir `is_delayed`.

Modelos candidatos:

- Regresión logística como línea base.
- KNN.
- SVM.
- Árbol de decisión.

Métricas: precision, recall, F1, matriz de confusión, ROC-AUC y calibración. Se priorizará detectar retrasos sin generar un número excesivo de falsas alertas.

### Clustering

Objetivo: encontrar grupos descriptivos de clientes.

Modelos candidatos:

- K-Means.
- DBSCAN.

Variables: frecuencia, recencia, gasto total, ticket promedio y categorías compradas. Métricas: Silhouette Score y Davies-Bouldin, complementadas con interpretación humana.

Los clusters no se usarán para negar atención, alterar precios individualmente ni tomar decisiones sensibles.

### Pronóstico de demanda

Prophet se incorporará solamente si el dataset disponible contiene una serie temporal con historial y estacionalidad suficientes. Mientras tanto se mostrará una línea base reproducible como promedio móvil o tendencia lineal, claramente identificada.

### Entrenamiento y servicio

- El entrenamiento ocurrirá fuera de las solicitudes web.
- Los modelos se versionarán junto con sus métricas y columnas de entrada.
- El backend cargará únicamente un modelo aprobado.
- Toda predicción registrará `modelVersion`.
- Si el modelo no está disponible, se aplicarán reglas de respaldo.
- Un modelo nuevo no se activa si no supera la línea base en datos de prueba separados.

## Seguridad y privacidad

- Ningún secreto se guardará en el repositorio.
- Las variables con prefijo `VITE_` solo contendrán valores públicos.
- Las claves de base de datos y Cloudinary existirán únicamente en el backend y plataformas de despliegue.
- El backend verificará JWT, rol y propiedad de cada recurso.
- CORS permitirá únicamente dominios conocidos y desarrollo local.
- Los vouchers serán privados y se entregarán mediante URLs firmadas.
- Se validarán tipo, tamaño y formato de archivos.
- Se aplicará rate limiting a login, cotizaciones y firma de archivos.
- No se usarán nombre, teléfono, correo o dirección exacta como características de ML.
- Los logs evitarán información personal y tokens.
- Las cuentas de demostración no compartirán credenciales de producción.

## DevOps y entornos

### Entornos

| Entorno | Uso |
| --- | --- |
| Local | Desarrollo con servicios configurables y datos de prueba |
| Preview | Validación de cambios antes de unirlos a `main` |
| Demo | Despliegue estable para exposición y pruebas de usuario |

### Flujo Git

- `main` debe mantenerse desplegable.
- Cada cambio se realiza en una rama corta.
- Antes de integrar se ejecutan build, lint y pruebas.
- Los commits describen una unidad de cambio.
- No se suben `.env`, datasets con datos personales, modelos temporales ni artefactos grandes.

### Pipeline mínimo

1. Instalar dependencias.
2. Validar formato y tipos del frontend.
3. Ejecutar pruebas unitarias del frontend.
4. Construir el frontend.
5. Validar formato y tipos del backend.
6. Ejecutar pruebas del backend.
7. Verificar migraciones.
8. Exportar y comparar OpenAPI.
9. Ejecutar pruebas de algoritmos y ML.
10. Desplegar únicamente después de aprobar el pipeline.

Render gratuito puede presentar arranque en frío y almacenamiento efímero. El sistema no dependerá de archivos locales persistentes y medirá el arranque en frío por separado del rendimiento normal.

## Pruebas y métricas

### Pruebas funcionales críticas

- Consultar catálogo.
- Calcular y enviar cotización.
- Autenticarse con cada rol.
- Convertir cotización en pedido.
- Aplicar transiciones válidas e impedir transiciones inválidas.
- Registrar un pago una sola vez.
- Rechazar un monto mayor al saldo.
- Subir imagen con firma válida.
- Aislar los datos de cada cliente.
- Ejecutar A* y Hill Climbing.
- Obtener una predicción con versión de modelo.
- Aplicar reglas de respaldo cuando no haya modelo.

### Métricas técnicas

- Porcentaje de pruebas críticas aprobadas.
- Cobertura de código como referencia, no como único indicador.
- P50 y P95 de endpoints principales.
- Tasa de errores HTTP.
- Tiempo de carga del catálogo.
- Tiempo de inferencia.
- Tiempo y nodos explorados por A*.
- Iteraciones y mejora de Hill Climbing.

### Métricas de ML

- Regresión: MAE, RMSE y R².
- Clasificación: precision, recall, F1, ROC-AUC y matriz de confusión.
- Clustering: Silhouette y Davies-Bouldin.
- Comparación obligatoria contra una línea base.

### Pruebas con usuarios

Se probará con cinco a ocho participantes usando tareas definidas. Se medirá:

- Tasa de tareas completadas.
- Tiempo por tarea.
- Errores y solicitudes de ayuda.
- Puntaje SUS.
- Comentarios cualitativos.

Objetivos de referencia:

- Todos los flujos críticos automatizados deben aprobar.
- Al menos 80% de tareas de usuario completadas.
- SUS igual o superior a 75.
- P95 menor a 700 ms para endpoints calientes de lectura simple.
- Inferencia menor a 300 ms en el entorno de demostración.

Si no se alcanzan, se reportará el resultado real y se creará una acción de mejora. Los objetivos no se reemplazarán por datos inventados.

## Plan de implementación por fases

### Fase 0. Definición y control

Entregables:

- Plan maestro.
- Seguimiento por fases.
- Roles y responsables asignados.
- Alcance revisado por el equipo.

Criterio de salida: el equipo puede explicar qué se construirá, qué no se construirá y cuáles son los requisitos oficiales del sistema.

### Fase 1. Base técnica

Entregables:

- Estructura de backend.
- Configuración tipada por entorno.
- FastAPI con `/health` y `/docs`.
- Pruebas iniciales.
- Pipeline básico.

Criterio de salida: frontend y backend construyen y sus pruebas se ejecutan localmente.

### Fase 2. Base de datos y autenticación

Entregables:

- Migraciones iniciales.
- Seed reproducible.
- Supabase Auth.
- Roles y autorización.
- Pruebas de acceso permitido y denegado.

Criterio de salida: visitante, cliente, operador y administrador tienen permisos comprobados.

### Fase 3. Catálogo y cotizaciones

Entregables:

- Catálogo desde PostgreSQL.
- CRUD administrativo del catálogo.
- Reglas de precio backend.
- Cotizaciones persistentes.
- Cliente TypeScript generado desde OpenAPI.

Criterio de salida: no quedan productos ni precios dependientes de archivos TypeScript para el flujo principal.

### Fase 4. Operación del taller

Entregables:

- Conversión a pedido.
- Producción e historial de estados.
- Clientes.
- Pagos idempotentes.
- Cloudinary para productos y vouchers.

Criterio de salida: el flujo cotización, pedido, producción, pago e instalación funciona de extremo a extremo.

### Fase 5. Algoritmos de búsqueda

Entregables:

- A* con pruebas y visualización.
- Hill Climbing con reinicios y pruebas.
- Persistencia de ejecuciones.
- Comparación contra soluciones base.

Criterio de salida: ambos algoritmos producen resultados reproducibles y métricas visibles.

### Fase 6. Machine learning

Entregables:

- Generador de dataset sintético.
- Pipeline de preparación y separación de datos.
- Comparación de modelos.
- Registro de métricas y versión.
- Inferencia en FastAPI con fallback.

Criterio de salida: cada modelo activo supera su línea base en el conjunto de prueba y sus resultados no están escritos manualmente.

### Fase 7. Calidad y experiencia

Entregables:

- Pruebas unitarias, integración y E2E.
- Accesibilidad y responsive.
- Pruebas con usuarios.
- Correcciones priorizadas.
- Medición de rendimiento.

Criterio de salida: flujos críticos aprobados y resultados documentados.

### Fase 8. Despliegue y presentación

Entregables:

- Frontend en Cloudflare Pages.
- Backend en Render.
- Supabase y Cloudinary configurados.
- Pipeline de despliegue.
- Informe de métricas.
- Guion y evidencia de demostración.

Criterio de salida: una persona externa puede abrir las URLs, ejecutar el guion y verificar los resultados.

## Guion de demostración

1. Abrir la web pública y explorar el catálogo.
2. Crear una cotización personalizada.
3. Mostrar precio y entrega estimada con fuente de la estimación.
4. Iniciar sesión como administrador.
5. Revisar y convertir la cotización.
6. Registrar anticipo y mover el pedido en producción.
7. Mostrar la predicción de retraso y su explicación.
8. Ejecutar Hill Climbing y comparar la secuencia.
9. Seleccionar entregas y ejecutar A*.
10. Mostrar clustering y métricas de ML.
11. Abrir Swagger, Supabase y el pipeline para evidenciar integración.
12. Presentar pruebas, limitaciones y plan de mejora.

## Riesgos y respuestas

| Riesgo | Respuesta |
| --- | --- |
| Historial digital insuficiente al inicio | Datos controlados de prueba, captura operativa y reglas de respaldo |
| Resultados ML artificialmente altos | Separación temporal, línea base y transparencia |
| Alcance excesivo | Respetar fases y fuera de alcance |
| Render entra en reposo | Medir cold start y mostrar estado de carga |
| Pérdida de datos en planes gratuitos | Migraciones, seed y exportaciones antes de la demo |
| Exposición de secretos | Variables de entorno y revisión del repositorio |
| Fallo durante exposición | Datos seed, capturas y video corto de respaldo |
| Algoritmos poco útiles | Mostrar problema, entrada, comparación y decisión humana |

## Definición de terminado

Una funcionalidad está terminada únicamente cuando:

- Cumple un caso de uso de este plan.
- Tiene contrato y validaciones definidos.
- Respeta roles y seguridad.
- Persiste correctamente cuando corresponde.
- Maneja errores y estados de carga.
- Tiene pruebas automatizadas proporcionales al riesgo.
- No contiene métricas o datos engañosos.
- Está documentada en OpenAPI o en la guía correspondiente.
- Funciona en el entorno de demostración.
- Su evidencia se registra en `docs/SEGUIMIENTO.md`.

## Control de cambios

Las decisiones importantes se registrarán en la tabla de decisiones de `docs/SEGUIMIENTO.md` con fecha, motivo, impacto y responsable. Este plan se actualizará cuando una decisión aceptada cambie alcance, arquitectura, reglas, roles o fases.

No se cambiará una regla solo para facilitar una implementación sin analizar antes sus consecuencias en datos, contratos, pruebas y demostración.
