# Especificación de base de datos

## Objetivo y fuente de verdad

PostgreSQL en Supabase almacenará la operación completa de Mueblería Iván: identidad, catálogo, cotizaciones, pedidos, producción, pagos, archivos, auditoría, algoritmos y ML. Este documento define qué significa “base de datos completa” para el prototipo.

La migración SQL versionada es la fuente estructural de verdad. Los modelos SQLAlchemy deben reflejarla, no crear una estructura distinta. Los tipos de API se derivan desde Pydantic/OpenAPI.

## Separación y seguridad

- `auth`: esquema gestionado por Supabase Auth.
- `app`: esquema de negocio usado por FastAPI y no consultado directamente por el navegador.
- El frontend utilizará Supabase directamente solo para autenticación.
- FastAPI verificará el JWT, el rol y la propiedad antes de acceder a datos comerciales.
- RLS se mantendrá como defensa adicional para registros asociados a usuarios.
- Credenciales, tokens, vouchers y datos personales no se incluirán en seeds ni commits.

## Tipos controlados

| Tipo | Valores iniciales |
| --- | --- |
| `user_role` | `customer`, `operator`, `admin` |
| `quote_status` | `draft`, `submitted`, `reviewing`, `approved`, `rejected`, `expired`, `converted` |
| `order_status` | `confirmed`, `materials_pending`, `cutting`, `assembly`, `finishing`, `ready`, `delivered`, `installed`, `cancelled` |
| `payment_status` | `recorded`, `voided` |
| `payment_method` | `cash`, `bank_transfer`, `card`, `other` |
| `asset_access` | `public`, `private` |
| `model_status` | `candidate`, `approved`, `active`, `retired` |

Los estados se modifican mediante migraciones. No se guardan traducciones visibles dentro de los enums.

## Tablas de identidad y clientes

### `app.profiles`

- `user_id` UUID, PK y FK a `auth.users.id`.
- Nombre, teléfono, rol, estado activo y marcas de tiempo.
- Un trigger crea el perfil mínimo al registrar un usuario.
- Solo un administrador puede cambiar roles.

### `app.customers`

- Identificador UUID y vínculo opcional único con `profiles`.
- Nombre, correo, teléfono, documento opcional, dirección, distrito y notas.
- Permite clientes creados por un operador aunque todavía no tengan cuenta.
- Correo normalizado e índices de búsqueda; no se exige correo cuando existe teléfono.

### `app.delivery_locations`

- Cliente, etiqueta, dirección, distrito, referencia y coordenadas opcionales.
- Coordenadas válidas: latitud entre -90 y 90, longitud entre -180 y 180.
- Proporciona los nodos para la demostración de A*.

## Tablas de catálogo y precios

### `app.products`

- Slug único, nombre, descripción, categoría, precio base en céntimos y estado activo.
- Días mínimos/máximos de fabricación y rango permitido de medidas.
- Borrado lógico mediante `active`; un producto utilizado no se elimina físicamente.

### `app.product_images`

- Producto, identificador público de Cloudinary, URL segura, texto alternativo y posición.
- Posición única por producto; dimensiones y metadatos opcionales.

### `app.materials`, `app.finishes`, `app.accessories`

- Código único, nombre, descripción, ajuste de precio en céntimos o porcentaje y estado.
- Disponibilidad separada de borrado lógico.

### Tablas de disponibilidad

- `app.product_materials`
- `app.product_finishes`
- `app.product_accessories`

Cada tabla usa clave compuesta y puede marcar una opción como predeterminada. Solo puede existir una opción predeterminada de cada tipo por producto.

### `app.pricing_rules`

- Nombre, versión, prioridad, vigencia, condiciones y operación en JSONB validado por el servicio.
- Una regla activa no se modifica; se crea una versión nueva.
- Registra quién la creó y cuándo.

## Cotizaciones

### `app.quotes`

- UUID, código visible único, cliente opcional y usuario propietario opcional.
- Snapshot de nombre, correo y teléfono para solicitudes de visitantes.
- Estado, moneda `PEN`, subtotal, ajustes, total, anticipo, vencimiento y versión.
- Totales no negativos; el total debe coincidir con subtotal más ajustes.
- Vigencia inicial de siete días y control de concurrencia mediante `version`.

### `app.quote_items`

- Cotización, producto, cantidad, ancho/alto/profundidad en milímetros.
- Material, acabado, accesorios y configuración adicional.
- Snapshot del nombre, precio base y desglose de cálculo en JSONB.
- Cantidad y medidas positivas; importes no negativos.

## Pedidos, producción y entregas

### `app.orders`

- UUID, código visible único, cotización de origen única y cliente.
- Estado, moneda, total, anticipo requerido, pagado, saldo y versión.
- Fechas prometida, entrega e instalación; dirección de entrega como snapshot.
- El pago acumulado no puede ser negativo ni superar el total sin una excepción registrada.

### `app.order_items`

- Copia inmutable de los artículos aprobados al convertir una cotización.
- Conserva configuración, medidas, cantidades y precios aunque cambie el catálogo.

### `app.order_status_events`

- Pedido, estado anterior/nuevo, actor, fecha y nota.
- Es append-only y constituye la línea de tiempo del cliente.

### `app.production_jobs`

- Pedido, etapa, prioridad, complejidad, horas estimadas/reales y fechas planificadas/reales.
- Contiene los datos necesarios para Hill Climbing y medición posterior.

### `app.deliveries`

- Pedido, ubicación, ventana programada, secuencia, distancia estimada y estado.
- Conserva la entrada y resultado aceptado de la planificación de rutas.

## Pagos y archivos

### `app.payments`

- Pedido, monto en céntimos, método, referencia, fecha, estado y actor.
- `idempotency_key` única para evitar cobros duplicados.
- Un pago no se elimina. Una reversión crea un nuevo registro relacionado y marca el original.
- Restricción de monto positivo y moneda `PEN`.

### `app.media_assets`

- Proveedor, identificador externo, tipo, acceso, propietario, hash y metadatos.
- Imágenes de catálogo son públicas; vouchers son privados.
- Un pago referencia el asset privado del voucher, no una URL pública permanente.

## Analítica, algoritmos y ML

### `app.customer_events`

- Evento autorizado, cliente o sesión seudónima, fecha y propiedades mínimas.
- No registra texto libre sensible ni eventos sin finalidad definida.

### `app.model_versions`

- Problema, algoritmo, versión, ruta/hash del artefacto, parámetros, métricas y estado.
- Solo una versión activa por problema.

### `app.predictions`

- Modelo, entidad relacionada, entrada resumida, salida, confianza opcional y resultado real posterior.
- Permite medir regresión y clasificación después de la operación.

### `app.optimization_runs`

- Algoritmo (`astar` o `hill_climbing`), entrada, línea base, resultado, mejora, semilla y duración.
- Los resultados son recomendaciones y no cambian pedidos automáticamente.

### `app.audit_logs`

- Actor, acción, entidad, identificador, valores anterior/nuevo, request ID, fecha e IP resumida.
- Append-only; registra roles, precios, estados, pagos, reversiones y activación de modelos.

## Restricciones e índices obligatorios

- UUID generado en PostgreSQL para claves internas.
- `created_at` y `updated_at` en UTC; trigger uniforme para actualizaciones.
- Dinero como `bigint` en céntimos y medidas como enteros en milímetros.
- Claves foráneas explícitas con política de borrado conservadora.
- Códigos, slugs, correos normalizados e idempotency keys con índices únicos.
- Índices para estados y fechas de cotizaciones, pedidos, producción y pagos.
- Índices para todas las claves foráneas usadas en listados.
- Índices parciales para productos activos, pedidos abiertos y modelos activos.
- Checks para importes, medidas, coordenadas, rangos de fechas y versiones positivas.

## Matriz mínima de acceso

| Recurso | Cliente | Operador | Administrador |
| --- | --- | --- | --- |
| Perfil propio | Leer/editar datos permitidos | Propio | Todos y roles |
| Cotización propia | Leer | Consultar para operación | Todo |
| Pedido propio | Leer | Leer y cambiar producción | Todo |
| Pagos propios | Leer resumen | Registrar | Registrar y revertir |
| Catálogo activo | Leer | Leer | Administrar |
| Reglas de precio | No | No | Administrar |
| Analítica/optimizaciones | No | Leer | Administrar |
| Auditoría | No | No | Leer |

La API aplica esta matriz y las pruebas RLS verifican aislamiento entre dos clientes distintos.

## Seed de desarrollo

El seed debe ser determinista y contener únicamente datos ficticios:

- Un administrador y un operador creados mediante el procedimiento documentado de Auth.
- Dos clientes ficticios independientes.
- Al menos seis productos con opciones e imágenes de ejemplo.
- Materiales, acabados, accesorios y una versión de reglas de precio.
- Cotizaciones, pedidos y pagos que cubran estados importantes.
- Eventos de producción suficientes para probar dashboard y algoritmos.

El dataset grande para ML se genera en `data/synthetic/`; no se inserta completo en el seed operativo.

## Orden de migración

1. Extensiones, esquema `app`, funciones y tipos.
2. Identidad y clientes.
3. Catálogo, opciones y precios.
4. Cotizaciones e items.
5. Pedidos, producción y entregas.
6. Pagos y recursos multimedia.
7. Analítica, modelos, predicciones y auditoría.
8. Índices, triggers, permisos y RLS.
9. Seed y pruebas SQL.

## Criterio de finalización

La base se considera completa cuando:

1. `supabase db reset` crea todo desde cero sin pasos manuales ocultos.
2. El seed termina correctamente y utiliza solo datos ficticios.
3. Las restricciones rechazan importes, medidas, estados y referencias inválidas.
4. Dos clientes no pueden consultar recursos del otro.
5. Operador y administrador cumplen la matriz de permisos.
6. Los pagos duplicados son detenidos por idempotencia.
7. Cotización, pedido, producción, pago y auditoría funcionan en una prueba integral.
8. Los modelos SQLAlchemy y la migración coinciden.
9. Existe un diagrama actualizado y un diccionario de datos verificable.
10. CI ejecuta las pruebas de base de datos y backend.
