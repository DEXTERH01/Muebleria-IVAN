# Supabase

Esta carpeta es la fuente reproducible de PostgreSQL para Mueblería Iván.
Las tablas comerciales viven en `app`, un esquema que no se publica mediante
PostgREST. El navegador usa Supabase solo para autenticación; FastAPI accede a
los datos comerciales y RLS actúa como defensa adicional.

Cristian Gonza lidera la migración base y Dexter realiza la revisión de
arquitectura y seguridad. No se editan migraciones ya compartidas; una
corrección se realiza con una migración nueva. El diseño obligatorio está en
`../docs/BASE_DATOS.md`.

## Requisitos

- Supabase CLI v3 o posterior.
- Docker Desktop, Rancher Desktop, Podman u otro runtime compatible con Docker.

No se requieren credenciales remotas para ejecutar el entorno local.

## Crear y probar desde cero

Desde la raíz del repositorio:

```powershell
supabase start
supabase db reset
supabase test db
supabase db lint --schema app --level error --fail-on error
```

Si la CLI está instalada como dependencia npm, anteponga `npx` a los comandos.
`db reset` aplica las migraciones en orden y después ejecuta `seed.sql`. Cada
prueba pgTAP corre en una transacción que se revierte al terminar.

## Contenido

- `migrations/20261121000100_initial_schema.sql`: esquema, tipos, tablas,
  restricciones, índices, triggers, permisos y políticas RLS.
- `seed.sql`: datos ficticios deterministas para desarrollo.
- `tests/database/`: pruebas pgTAP de estructura, restricciones y aislamiento.
- `SCHEMA.md`: diagrama y diccionario resumido de datos.

## Identidades del seed

El seed agrega cuatro filas ficticias a `auth.users` para sostener relaciones y
pruebas RLS. No tienen contraseña ni se pueden usar para iniciar sesión:

- `admin@muebleria-ivan.test`
- `operador@muebleria-ivan.test`
- `cliente.ana@example.test`
- `cliente.luis@example.test`

Para una cuenta de demostración capaz de iniciar sesión, créela mediante
Supabase Studio (`Authentication > Users`) o Auth Admin desde un entorno de
confianza. El trigger `app.handle_new_auth_user` crea el perfil con rol
`customer`; la elevación a `operator` o `admin` debe realizarse por el flujo
administrativo del backend. No se aceptan roles desde `raw_user_meta_data`.

## Seguridad

- `app` queda fuera de `api.schemas` en `config.toml`.
- Toda tabla de negocio tiene RLS habilitado.
- Los clientes solo leen sus perfiles, cotizaciones, pedidos y pagos.
- Operadores leen la operación y actualizan producción mediante el backend.
- Administradores gestionan catálogo y reglas de precio.
- Historial de estados, artículos aprobados y auditoría son append-only.
- Los pagos no se eliminan y la clave de idempotencia es única.

No ejecute `db reset` contra un proyecto remoto: elimina datos. Para validar una
base enlazada sin destruirla, use migraciones revisadas y el flujo de despliegue
del equipo.
