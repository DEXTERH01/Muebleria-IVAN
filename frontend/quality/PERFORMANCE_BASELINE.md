# Línea base local de rendimiento

Fecha de medición: 2026-11-21. La API FastAPI se ejecutó localmente en `demo` y consultó la base de prueba de Supabase. Se enviaron 12 solicitudes secuenciales por endpoint desde PowerShell antes y después de agrupar las consultas del catálogo; las solicitudes GET y de estimación solo leyeron datos. No se crearon cotizaciones, pedidos ni pagos.

| Operación | Muestras por etapa | Errores antes/después | P50 antes → después (ms) | P95 antes → después (ms) |
| --- | ---: | ---: | ---: | ---: |
| `GET /api/v1/products?page=1&pageSize=100` | 12 | 0/12 → 0/12 | 3728.2 → 1016.2 | 4069.1 → 1636.5 |
| `GET /api/v1/products/ropero-andino` | 12 | 0/12 → 0/12 | 899.3 → 842.4 | 920.2 → 871.9 |
| `POST /api/v1/quotes/estimate` | 12 | 0/12 → 0/12 | 723.5 → 710.4 | 771.4 → 745.3 |

P50 y P95 usan el rango más cercano sobre la muestra ordenada. En la lista, agrupar las consultas redujo P50 en 72.7% y P95 en 59.8%. Es una comparación exploratoria de baja concurrencia: incluye la latencia del cliente PowerShell, el backend local y la conexión a Supabase demo. No representa la experiencia de una persona usuaria ni una prueba de carga.

## Muestra de la API publicada

Fecha: 2026-11-28. Se enviaron 12 solicitudes secuenciales por ruta desde esta estación con `curl.exe` a Render, sin escribir datos. La estimación usó el producto `centro-tv-flotante` con medidas mínimas válidas (1200 × 450 × 300 mm). P50 y P95 se calcularon por rango más cercano sobre las duraciones totales de `curl` ordenadas. Los códigos HTTP distintos de 200 cuentan como errores.

| Operación | Muestras | Errores | P50 (ms) | P95 (ms) |
| --- | ---: | ---: | ---: | ---: |
| `GET /api/v1/products?page=1&pageSize=100` | 12 | 0 | 707.5 | 1452.9 |
| `GET /api/v1/products/centro-tv-flotante` | 12 | 0 | 627.3 | 680.3 |
| `POST /api/v1/quotes/estimate` | 12 | 0 | 603.4 | 912.6 |

La muestra incluye red, proxy, Render y PostgreSQL. No aísla la latencia del servidor ni mide concurrencia; tampoco es comparable directamente con la medición local anterior. La lista de catálogo supera el objetivo de referencia de P95 menor a 700 ms para lecturas simples. La página publicada de Netlify respondió HTTP 200 en `/`, `/catalogo` y `/cotizador`; esto comprueba la entrega de la SPA, no el recorrido funcional en navegador.

La inferencia ML ya tiene endpoints en FastAPI, pero requiere rol operador o administrador y registra cada predicción en la base. Su latencia sigue pendiente de medir en un entorno de prueba controlado, junto con una muestra mayor y concurrente de las rutas públicas. No se debe presentar esta muestra pequeña como prueba de rendimiento de producción.
