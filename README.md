# Mueblería Iván

![Logo de Mueblería Iván](public/assets/brand/muebleria-ivan-logo.png)

Plataforma de transformación digital para Mueblería Iván, un negocio familiar de Lima, Perú. Permite explorar el catálogo, crear cotizaciones, gestionar pedidos, supervisar la producción y controlar pagos 50/50 desde un solo lugar.

## Tecnologías

- React + TypeScript
- Vite
- Python + FastAPI
- Pydantic Settings
- Pytest, Ruff y Vitest
- CSS moderno responsive
- `localStorage` como persistencia temporal mientras se implementa Supabase

## Instalación

```bash
npm install
npm run dev
```

Abre la dirección mostrada por Vite (normalmente `http://localhost:5173`).

### Backend

La preparación completa del entorno Python se encuentra en [backend/README.md](backend/README.md). Después de instalarlo, la API se inicia desde `backend/` con:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Swagger estará disponible en `http://127.0.0.1:8000/docs`.

## Pruebas

```powershell
npm run test
npm run build
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

## Plan del proyecto

El alcance, las reglas, la arquitectura y el orden obligatorio de implementación se encuentran en [docs/PLAN_MAESTRO.md](docs/PLAN_MAESTRO.md). El progreso y las evidencias de cada fase se registran en [docs/SEGUIMIENTO.md](docs/SEGUIMIENTO.md).

## Estructura

- `src/pages`: experiencia del cliente y administración.
- `src/components`: layout, interfaz y catálogo reutilizables.
- `src/data`: productos, pedidos y clientes iniciales.
- `src/hooks/useOrders.ts`: persistencia y lógica de pedidos/pagos.
- `src/types`: contratos TypeScript de la plataforma.
- `backend/app`: API y módulos de negocio en Python.
- `backend/tests`: pruebas del backend.
- `.github/workflows/ci.yml`: validación automática de frontend y backend.

## Funcionalidades

- Catálogo filtrable con búsqueda y detalles de producto.
- Cotizador dinámico con medidas, materiales, acabados y accesorios.
- Cálculo referencial de anticipo 50% y saldo 50%.
- Mensaje generado para WhatsApp con opción de copiar.
- Dashboard, pedidos, detalle de pedido, clientes y control de pagos.
- Tablero de producción con movimiento de pedidos por etapa.
- Alerta de saldo pendiente al dejar un pedido listo para entrega.
- Registro de pago con previsualización local de voucher.
- Persistencia de cambios mediante `localStorage`.
- Asistente virtual con respuestas contextuales para clientes.
- Panel de análisis predictivo con proyección lineal, demanda por categoría y riesgo de retraso.

## Inteligencia artificial

La plataforma incorpora **Mía**, una asistente capaz de orientar sobre productos, materiales, medidas, pagos y entregas, además de consultar pedidos en tiempo real. El panel administrativo incluye proyección de demanda, recomendaciones de producción y detección de riesgo según etapa, fecha y estado de pago.

## Flujo principal

1. Entra al catálogo y abre **Closet Siena**.
2. Personaliza el diseño en el cotizador y consulta la cotización.
3. Revisa el anticipo y saldo, luego copia el mensaje de WhatsApp.
4. Cambia a **Vista administrador**.
5. Abre el tablero de Producción y ubica `PED-001` (María López).
6. Muévelo hasta **Listo para entrega**. Se mostrará la alerta por saldo pendiente.
7. Registra el saldo final desde el detalle o Control de pagos: el pedido pasará a **Pagado** y el saldo será S/ 0.

