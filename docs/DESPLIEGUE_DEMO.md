# Despliegue de la demo: Render y Cloudflare Pages

El frontend se publica en Cloudflare Pages y el backend continúa en Render. Durante
el cambio, Netlify se conserva como rollback; no se elimina hasta aprobar el smoke
test del nuevo origen.

## Configuración preparada en el repositorio

- `frontend/.node-version` fija Node.js 22.12.0.
- `frontend/public/_redirects` reescribe `/*` a `/index.html` con estado 200 para
  que las rutas de la SPA funcionen al abrirlas o recargarlas directamente.
- El build continúa siendo `npm run build` y genera `frontend/dist/`.
- FastAPI continúa desplegado en `https://muebleria-ivan.onrender.com`.

## 1. Crear el proyecto en Cloudflare Pages

1. Entrar a Cloudflare Dashboard → **Workers & Pages**.
2. Seleccionar **Create application** → **Pages** → **Import an existing Git repository**.
3. Autorizar GitHub y elegir `DEXTERH01/Muebleria-IVAN`.
4. Configurar exactamente estos valores:

| Campo | Valor |
| --- | --- |
| Project name | `muebleria-ivan` (o el nombre disponible elegido) |
| Production branch | `main` |
| Framework preset | `React (Vite)` |
| Root directory | `frontend` |
| Build command | `npm run build` |
| Build output directory | `dist` |

5. En **Settings → Builds → Branch control**, dejar `main` como producción. Para
   la migración inicial, seleccionar **None** para preview branches; así no se crean
   orígenes temporales que todavía no estén autorizados en Render y Supabase.
6. Crear el proyecto. Si el primer deploy ocurre antes de configurar variables,
   continuar con la siguiente sección y después seleccionar **Retry deployment**.

Cloudflare usa `frontend/` como raíz del monorepo; por eso `dist` es relativo a esa
carpeta. La configuración coincide con la guía oficial de
[builds de Pages](https://developers.cloudflare.com/pages/configuration/build-configuration/).

## 2. Configurar variables del frontend

En el proyecto Pages, abrir **Settings → Environment variables** y añadir estos
valores al entorno **Production**:

| Variable | Valor |
| --- | --- |
| `VITE_API_BASE_URL` | `https://muebleria-ivan.onrender.com` |
| `VITE_SUPABASE_URL` | La URL pública actual del proyecto Supabase |
| `VITE_SUPABASE_ANON_KEY` | La clave pública publishable/`anon` actual |

No añadir la clave `service_role`, `sb_secret_...`, la contraseña PostgreSQL ni
secretos de Cloudinary. Las variables `VITE_*` se integran en el JavaScript público.

Guardar y ejecutar un nuevo deployment de `main`. Anotar la URL final completa,
por ejemplo `https://muebleria-ivan.pages.dev`; en los pasos siguientes se denomina
`<ORIGEN_PAGES>`. Debe escribirse sin `/` final.

## 3. Autorizar Cloudflare Pages en Render

En Render → servicio `muebleria-ivan` → **Environment**, cambiar
`MUEBLERIA_CORS_ORIGINS` conservando temporalmente Netlify:

```json
["https://muebleriaivan.netlify.app","<ORIGEN_PAGES>"]
```

Ejemplo si Cloudflare asignó el nombre previsto:

```json
["https://muebleriaivan.netlify.app","https://muebleria-ivan.pages.dev"]
```

Guardar y desplegar nuevamente el servicio Render. Los orígenes deben ser exactos,
usar HTTPS y no terminar en `/`.

Las demás variables de Render no cambian:

| Variable | Uso |
| --- | --- |
| `MUEBLERIA_DATABASE_URL` | PostgreSQL de Supabase con `postgresql+psycopg://` |
| `MUEBLERIA_SUPABASE_URL` | URL del proyecto Supabase |
| `MUEBLERIA_CLOUDINARY_CLOUD_NAME` | Nombre del cloud |
| `MUEBLERIA_CLOUDINARY_API_KEY` | API key del backend |
| `MUEBLERIA_CLOUDINARY_API_SECRET` | API secret del backend |
| `MUEBLERIA_GROQ_API_KEY` | API key secreta de Groq; solo backend |
| `MUEBLERIA_GROQ_MODEL` | `openai/gpt-oss-20b` |
| `MUEBLERIA_ASSISTANT_REQUESTS_PER_MINUTE` | `10` para proteger la cuota gratuita |

## 4. Actualizar Supabase Auth

En Supabase Dashboard → **Authentication → URL Configuration**:

1. Cambiar **Site URL** a `<ORIGEN_PAGES>`.
2. Añadir a **Redirect URLs**:

```text
<ORIGEN_PAGES>/restablecer-contrasena
```

3. Conservar temporalmente la URL equivalente de Netlify para poder volver atrás.
4. Para desarrollo local, conservar `http://localhost:5173/**` si ya está registrada.

La recuperación de contraseña construye el retorno con `window.location.origin`,
por lo que la ruta exacta de Cloudflare debe estar permitida. Supabase recomienda
URLs exactas en producción; los comodines se reservan para previews. Véase
[Redirect URLs de Supabase](https://supabase.com/docs/guides/auth/redirect-urls).

## 5. Smoke test obligatorio

Ejecutar estas comprobaciones usando `<ORIGEN_PAGES>`:

1. Abrir `/` y confirmar que carga la portada.
2. Abrir directamente `/catalogo`, recargar y confirmar HTTP 200.
3. Abrir directamente `/producto/<slug-valido>` y recargar.
4. Confirmar en DevTools → Network que `/api/v1/products` responde desde Render
   sin error CORS.
5. Crear una cotización de prueba.
6. Iniciar sesión con una cuenta demo y abrir `/mi-cuenta`.
7. Iniciar sesión como operador o administrador y abrir `/admin`.
8. Solicitar recuperación de contraseña y confirmar que el enlace vuelve a
   `<ORIGEN_PAGES>/restablecer-contrasena`.
9. Abrir `https://muebleria-ivan.onrender.com/health` y confirmar HTTP 200.
10. Preguntar a Mía por una recomendación abierta y confirmar en DevTools que
    `POST /api/v1/assistant/chat` responde HTTP 200 sin exponer la API key.

Cloudflare desplegará automáticamente cada cambio enviado a `main` y puede crear
previews cuando se vuelvan a habilitar las ramas. Esto corresponde a la
[integración Git oficial](https://developers.cloudflare.com/pages/configuration/git-integration/).

## 6. Dominio propio opcional

En Pages → **Custom domains** → **Set up a domain**, asociar el dominio final antes
de cambiar DNS manualmente. Para un dominio raíz, la zona y sus nameservers deben
estar en Cloudflare; para un subdominio se puede usar un CNAME hacia el hostname
`*.pages.dev`. Seguir la guía oficial de
[custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/).

Si se añade un dominio propio, repetir los pasos 3 y 4 usando ese dominio como
origen final y como Site URL. Mantener también `<ORIGEN_PAGES>` hasta aprobar el
smoke test del dominio.

## 7. Cerrar Netlify después de validar

Solo después de aprobar todo el smoke test:

1. Desactivar los deploys automáticos del sitio en Netlify.
2. Retirar `https://muebleriaivan.netlify.app` de `MUEBLERIA_CORS_ORIGINS` en Render.
3. Retirar las URLs de Netlify de Supabase Auth.
4. Archivar o eliminar el sitio en Netlify.
5. Eliminar `netlify.toml` del repositorio en un commit posterior.

## Rollback

Si Cloudflare falla antes de retirar Netlify:

1. Restaurar la Site URL de Supabase a `https://muebleriaivan.netlify.app`.
2. Mantener ambos orígenes en `MUEBLERIA_CORS_ORIGINS`.
3. Volver a usar la URL de Netlify mientras se corrige el deployment de Pages.

No es necesario cambiar Render, la base de datos, Cloudinary ni las migraciones
para realizar este rollback.
