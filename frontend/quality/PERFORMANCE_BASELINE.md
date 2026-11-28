# Línea base local de rendimiento

Fecha de medición: 2026-11-21. La API FastAPI se ejecutó localmente en `demo` y consultó la base de prueba de Supabase. Se enviaron 12 solicitudes secuenciales por endpoint desde PowerShell antes y después de agrupar las consultas del catálogo; las solicitudes GET y de estimación solo leyeron datos. No se crearon cotizaciones, pedidos ni pagos.

| Operación | Muestras por etapa | Errores antes/después | P50 antes → después (ms) | P95 antes → después (ms) |
| --- | ---: | ---: | ---: | ---: |
| `GET /api/v1/products?page=1&pageSize=100` | 12 | 0/12 → 0/12 | 3728.2 → 1016.2 | 4069.1 → 1636.5 |
| `GET /api/v1/products/ropero-andino` | 12 | 0/12 → 0/12 | 899.3 → 842.4 | 920.2 → 871.9 |
| `POST /api/v1/quotes/estimate` | 12 | 0/12 → 0/12 | 723.5 → 710.4 | 771.4 → 745.3 |

P50 y P95 usan el rango más cercano sobre la muestra ordenada. En la lista, agrupar las consultas redujo P50 en 72.7% y P95 en 59.8%. Es una comparación exploratoria de baja concurrencia: incluye la latencia del cliente PowerShell, el backend local y la conexión a Supabase demo. No representa la experiencia de una persona usuaria ni una prueba de carga.

La inferencia ML no se midió: la fase 6 sigue asignada a Dexter y todavía no hay un endpoint de inferencia que se pueda medir en esta demo. Repetir las mediciones con mayor muestra y concurrencia en un entorno de despliegue controlado antes de afirmar objetivos de rendimiento.
