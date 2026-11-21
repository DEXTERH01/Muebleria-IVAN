# Hoja de ruta del frontend

## Objetivo

Convertir el prototipo visual actual en una aplicación mantenible, accesible y conectada a contratos reales sin perder el diseño logrado.

## Propiedad

Cristian Gonza es el responsable principal de `frontend/`. Cada cambio debe conservar compatibilidad con `contracts/openapi.json` y pasar las pruebas de frontend.

## Prioridades

### FE-01 Estructura y navegación

- Adoptar carpetas por dominio: catálogo, cotizaciones, pedidos, pagos, clientes y analítica.
- Introducir React Router.
- Añadir una página 404.
- Mantener rutas públicas y administrativas actuales.

### FE-02 Capa de API

- Crear `src/api/`.
- Centralizar URL base, headers y manejo de errores.
- Definir estados de carga, vacío, error y reintento.
- Consumir tipos derivados de OpenAPI.
- Evitar llamadas HTTP directas dentro de componentes visuales.

### FE-03 Sistema visual

- Extraer tokens de color, espaciado y tipografía.
- Normalizar botones, formularios, tablas, badges y modales.
- Mantener el símbolo oficial de Mueblería Iván.
- Validar contraste, foco visible y navegación por teclado.

### FE-04 Autenticación y portal del cliente

- Inicio y cierre de sesión.
- Recuperación de acceso.
- Protección de rutas por rol.
- Cotizaciones propias.
- Seguimiento de pedidos y pagos propios.

### FE-05 Administración

- Estados de carga y error en dashboard.
- Filtros persistentes en pedidos.
- Formularios accesibles para catálogo y pagos.
- Confirmaciones antes de acciones sensibles.
- Diseño responsive del kanban y tablas.

### FE-06 Calidad

- Pruebas de componentes y flujos.
- Pruebas E2E para cotización, login y cambio de estado.
- Revisión responsive en 360, 768 y 1440 píxeles.
- Lighthouse y corrección de problemas prioritarios.

## Reglas para mejorar sin generar conflictos

- Un PR por prioridad o pantalla.
- No renombrar contratos del backend desde frontend.
- No migrar todas las páginas en un solo commit.
- Antes de extraer un componente, añadir una prueba del comportamiento actual.
- Conservar la experiencia funcional mientras se reemplaza `localStorage`.

