# MuebleFlow Iván

Prototipo académico de transformación digital para una mueblería familiar de Lima, Perú. Permite explorar un catálogo, crear cotizaciones referenciales y gestionar pedidos, producción y pagos 50/50 desde un panel interno.

## Tecnologías

- React + TypeScript
- Vite
- CSS moderno responsive
- `localStorage` para persistencia local de pedidos y pagos

## Instalación

```bash
npm install
npm run dev
```

Abre la dirección mostrada por Vite (normalmente `http://localhost:5173`).

## Estructura

- `src/pages`: experiencia del cliente y administración.
- `src/components`: layout, interfaz y catálogo reutilizables.
- `src/data`: productos, pedidos y clientes simulados.
- `src/hooks/useOrders.ts`: persistencia y lógica de pedidos/pagos.
- `src/types`: contratos TypeScript del prototipo.

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

## Flujo de demostración

1. Entra al catálogo y abre **Closet Siena**.
2. Personaliza el diseño en el cotizador y consulta la cotización.
3. Revisa el anticipo y saldo, luego copia el mensaje de WhatsApp.
4. Cambia a **Vista administrador**.
5. Abre el tablero de Producción y ubica `PED-001` (María López).
6. Muévelo hasta **Listo para entrega**. Se mostrará la alerta por saldo pendiente.
7. Registra el saldo final desde el detalle o Control de pagos: el pedido pasará a **Pagado** y el saldo será S/ 0.

> Este proyecto corresponde a un prototipo académico de transformación digital y utiliza información simulada para demostrar sus funcionalidades.
