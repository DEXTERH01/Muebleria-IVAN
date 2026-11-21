# Catálogo de demostración

`products.csv` es el manifiesto reproducible de los 46 productos y sus imágenes
ya cargadas en Cloudinary. Los precios, plazos y rangos de medidas son valores
referenciales de demo. En las categorías con un equivalente existente se tomó
ese producto como referencia; las categorías nuevas usan valores provisionales.
La descripción de cada producto advierte que esos datos deben confirmarse antes
de uso comercial.

Desde la raíz del repositorio, revisa el manifiesto y luego aplícalo a la base
demo configurada en `backend/.env`:

```powershell
.\backend\.venv\Scripts\python.exe .\supabase\catalog_import\import_catalog.py
.\backend\.venv\Scripts\python.exe .\supabase\catalog_import\import_catalog.py --apply
```

El modo predeterminado solo valida el manifiesto. `--apply` exige
`MUEBLERIA_ENVIRONMENT=demo` y el host de Supabase de demostración esperado; usa
una transacción y aborta si encuentra un slug o una imagen con datos diferentes.
La importación es idempotente. Usa únicamente las URLs ya cargadas; no vuelve a
subir imágenes.

Este manifiesto no es una migración ni parte de `seed.sql`. No lo apliques a
producción. Un `supabase db reset` repone los seis productos del seed; ejecuta
esta importación después del reset para reconstruir el catálogo ampliado.
