# Despliegue de la demo

## Orden recomendado

1. Integrar los PR #16 y #17 en `main`, en ese orden.
2. En Render, crear un Blueprint desde `render.yaml` y conectar el repositorio.
3. Ingresar en el servicio Render los valores secretos solicitados.
4. En Netlify, importar el mismo repositorio. El archivo `netlify.toml` configura `frontend/` como directorio base, el build y la publicación de `dist/`.
5. Configurar las variables de build de Netlify y volver a desplegar el frontend.
6. Copiar la URL final de Netlify a `MUEBLERIA_CORS_ORIGINS` en Render y volver a desplegar el backend.
7. Añadir la URL pública de Netlify a Supabase Auth → URL Configuration → Site URL y Redirect URLs.

## Variables de Netlify

Configurar en Site configuration → Environment variables antes de desplegar:

| Variable | Valor |
| --- | --- |
| `VITE_API_BASE_URL` | URL pública del backend Render, por ejemplo `https://muebleria-ivan-api.onrender.com`, sin `/` final |
| `VITE_SUPABASE_URL` | URL pública del proyecto Supabase |
| `VITE_SUPABASE_ANON_KEY` | Clave pública `anon` o publishable de Supabase |

Las variables `VITE_*` se incluyen en el JavaScript público. Nunca usar aquí la clave `service_role`, la contraseña de PostgreSQL ni secretos de Cloudinary. El frontend falla con un mensaje claro si la URL de API no está definida en producción.

## Variables de Render

El Blueprint solicita estos valores al crear el servicio:

| Variable | Valor |
| --- | --- |
| `MUEBLERIA_DATABASE_URL` | Cadena PostgreSQL de Supabase, con esquema `postgresql+psycopg://`; utilizar el pooler si el entorno no permite IPv6 |
| `MUEBLERIA_SUPABASE_URL` | URL del proyecto Supabase, sin `/auth/v1` |
| `MUEBLERIA_CORS_ORIGINS` | JSON con orígenes exactos permitidos, por ejemplo `["https://<sitio>.netlify.app"]` |
| `MUEBLERIA_CLOUDINARY_CLOUD_NAME` | Nombre del cloud de Cloudinary |
| `MUEBLERIA_CLOUDINARY_API_KEY` | API Key de Cloudinary |
| `MUEBLERIA_CLOUDINARY_API_SECRET` | API Secret de Cloudinary |

Cloudinary puede quedar vacío para el primer despliegue; las cargas de imágenes y vouchers permanecerán deshabilitadas hasta configurarlo. La API requiere base de datos y Supabase para los flujos autenticados.

## Comprobación manual de disponibilidad

Después de los despliegues, abrir:

- `https://<backend>.onrender.com/health`
- `https://<backend>.onrender.com/docs`
- `https://<frontend>.netlify.app/`

Verificar catálogo, registro/inicio de sesión, cotización y un flujo administrativo. La primera petición a una instancia gratuita de Render puede tardar porque el servicio entra en reposo tras inactividad.

El Blueprint usa el plan gratuito de Render para la demo académica. Puede entrar en reposo y no se recomienda como alojamiento de producción comercial.
