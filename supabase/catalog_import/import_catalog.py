"""Idempotently import the approved demo catalog and its Cloudinary images."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("products.csv")
DEMO_HOST = "aws-0-us-east-2.pooler.supabase.com"
DESCRIPTION = (
    "Modelo de referencia de demo. Precio, plazos y medidas son referenciales "
    "y deben confirmarse antes de su uso comercial."
)
DEMO_MARKER = "son referenciales y deben confirmarse"
IMAGE_PREFIX = "muebleria-ivan/products/"
REQUIRED_COLUMNS = {
    "code",
    "name",
    "category",
    "product_slug",
    "local_file",
    "cloudinary_public_id",
    "secure_url",
    "alt_text",
    "display_order",
    "image_width_px",
    "image_height_px",
    "sha256",
    "base_price_minor",
    "min_production_days",
    "max_production_days",
    "min_width_mm",
    "max_width_mm",
    "min_height_mm",
    "max_height_mm",
    "min_depth_mm",
    "max_depth_mm",
}
PRODUCT_FIELDS = (
    "base_price_minor",
    "min_production_days",
    "max_production_days",
    "min_width_mm",
    "max_width_mm",
    "min_height_mm",
    "max_height_mm",
    "min_depth_mm",
    "max_depth_mm",
)


def read_backend_env() -> dict[str, str]:
    env_path = ROOT / "backend" / ".env"
    if not env_path.is_file():
        raise SystemExit("No se encontró backend/.env; consulta supabase/catalog_import/README.md.")

    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip(chr(34)).strip(chr(39))
    return values


def read_manifest() -> list[dict[str, str]]:
    if not MANIFEST.is_file():
        raise SystemExit("No se encontró el manifiesto del catálogo.")

    with MANIFEST.open(encoding="utf-8-sig", newline="") as manifest_file:
        reader = csv.DictReader(manifest_file)
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise SystemExit("El manifiesto no contiene todas las columnas requeridas.")
        rows = list(reader)

    if len(rows) != 46:
        raise SystemExit(f"Se esperaban 46 productos; el manifiesto tiene {len(rows)}.")
    if len({row["product_slug"] for row in rows}) != len(rows):
        raise SystemExit("El manifiesto contiene slugs duplicados.")
    if len({row["code"] for row in rows}) != len(rows):
        raise SystemExit("El manifiesto contiene códigos duplicados.")

    for row in rows:
        slug = row["product_slug"]
        expected_public_id = f"{IMAGE_PREFIX}{slug}/{row['code'].lower()}"
        if row["cloudinary_public_id"] != expected_public_id:
            raise SystemExit(f"Ruta Cloudinary incorrecta para {slug}.")
        if not row["secure_url"].startswith("https://res.cloudinary.com/"):
            raise SystemExit(f"URL Cloudinary inválida para {slug}.")
        if not row["alt_text"].strip() or len(row["sha256"]) != 64:
            raise SystemExit(f"Metadatos de imagen incompletos para {slug}.")
        for field in REQUIRED_COLUMNS - {
            "code",
            "name",
            "category",
            "product_slug",
            "local_file",
            "cloudinary_public_id",
            "secure_url",
            "alt_text",
            "sha256",
        }:
            if not row[field].strip():
                raise SystemExit(f"Falta {field} para {slug}.")
        if int(row["display_order"]) < 1:
            raise SystemExit(f"Posición de imagen inválida para {slug}.")
        if int(row["base_price_minor"]) < 0:
            raise SystemExit(f"Precio base inválido para {slug}.")
        if int(row["min_production_days"]) < 1 or int(row["max_production_days"]) < int(
            row["min_production_days"]
        ):
            raise SystemExit(f"Plazo de fabricación inválido para {slug}.")
        for dimension in ("width", "height", "depth"):
            low = int(row[f"min_{dimension}_mm"])
            high = int(row[f"max_{dimension}_mm"])
            if low < 1 or high < low:
                raise SystemExit(f"Rango de medidas inválido para {slug}.")
        if int(row["image_width_px"]) < 1 or int(row["image_height_px"]) < 1:
            raise SystemExit(f"Dimensiones de imagen inválidas para {slug}.")

    return rows


def import_catalog(rows: list[dict[str, str]]) -> None:
    config = read_backend_env()
    database_url = config.get("MUEBLERIA_DATABASE_URL", "")
    if config.get("MUEBLERIA_ENVIRONMENT") != "demo":
        raise SystemExit("Se canceló: MUEBLERIA_ENVIRONMENT debe ser demo.")
    parsed_url = make_url(database_url) if database_url else None
    if (
        parsed_url is None
        or parsed_url.host != DEMO_HOST
        or parsed_url.database != "postgres"
    ):
        raise SystemExit("Se canceló: la conexión no coincide con la base demo esperada.")

    engine = create_engine(
        database_url,
        connect_args={"sslmode": "require"},
        pool_pre_ping=True,
    )
    inserted_products = 0
    inserted_images = 0
    slugs = [row["product_slug"] for row in rows]
    expected_by_slug: dict[str, tuple[Any, ...]] = {}
    product_values: list[dict[str, Any]] = []
    for row in rows:
        expected_by_slug[row["product_slug"]] = (
            row["name"],
            row["category"],
            *(int(row[field]) for field in PRODUCT_FIELDS),
        )
        product_values.append(
            {
                "slug": row["product_slug"],
                "name": row["name"],
                "description": DESCRIPTION,
                "category": row["category"],
                **{field: int(row[field]) for field in PRODUCT_FIELDS},
            }
        )

    with engine.begin() as connection:
        if connection.execute(text("select current_database()")).scalar_one() != "postgres":
            raise SystemExit("Se canceló: la base de datos no es la esperada.")

        existing_products = connection.execute(
            text(
                """select id, slug::text as slug, name, category, base_price_minor,
                          min_production_days, max_production_days, min_width_mm,
                          max_width_mm, min_height_mm, max_height_mm, min_depth_mm,
                          max_depth_mm, description
                   from app.products where slug::text = any(cast(:slugs as text[]))"""
            ),
            {"slugs": slugs},
        ).mappings().all()
        existing_by_slug = {str(product["slug"]): product for product in existing_products}
        for slug, product in existing_by_slug.items():
            actual = (
                product["name"],
                product["category"],
                *(product[field] for field in PRODUCT_FIELDS),
            )
            if actual != expected_by_slug[slug] or DEMO_MARKER not in product["description"]:
                raise SystemExit(
                    f"Se canceló: {slug} ya existe con datos diferentes; no se sobrescribió."
                )

        missing_products = [
            values for values in product_values if values["slug"] not in existing_by_slug
        ]
        if missing_products:
            connection.execute(
                text(
                    """insert into app.products (
                        slug, name, description, category, base_price_minor, active,
                        min_production_days, max_production_days, min_width_mm,
                        max_width_mm, min_height_mm, max_height_mm, min_depth_mm, max_depth_mm
                    ) values (
                        :slug, :name, :description, :category, :base_price_minor, true,
                        :min_production_days, :max_production_days, :min_width_mm,
                        :max_width_mm, :min_height_mm, :max_height_mm, :min_depth_mm, :max_depth_mm
                    ) on conflict (slug) do nothing"""
                ),
                missing_products,
            )
            inserted_products = len(missing_products)

        product_rows = connection.execute(
            text(
                "select id, slug::text as slug from app.products "
                "where slug::text = any(cast(:slugs as text[]))"
            ),
            {"slugs": slugs},
        ).all()
        product_ids = {slug: product_id for product_id, slug in product_rows}
        if len(product_ids) != len(rows):
            raise SystemExit("Se canceló: no se pudieron resolver todos los productos.")

        connection.execute(
            text(
                """insert into app.product_materials (product_id, material_id, is_default)
                   select p.id, m.id, m.code::text = 'MEL-18'
                   from app.products p cross join app.materials m
                   where p.slug::text = any(cast(:slugs as text[])) and m.active and m.available
                   on conflict do nothing"""
            ),
            {"slugs": slugs},
        )
        connection.execute(
            text(
                """insert into app.product_finishes (product_id, finish_id, is_default)
                   select p.id, f.id, f.code::text = 'NATURAL'
                   from app.products p cross join app.finishes f
                   where p.slug::text = any(cast(:slugs as text[])) and f.active and f.available
                   on conflict do nothing"""
            ),
            {"slugs": slugs},
        )
        connection.execute(
            text(
                """insert into app.product_accessories (product_id, accessory_id, is_default)
                   select p.id, a.id, false
                   from app.products p cross join app.accessories a
                   where p.slug::text = any(cast(:slugs as text[])) and a.active and a.available
                   on conflict do nothing"""
            ),
            {"slugs": slugs},
        )

        public_ids = [row["cloudinary_public_id"] for row in rows]
        existing_images = connection.execute(
            text(
                """select product_id, public_id, secure_url, alt_text, position, width, height
                   from app.product_images where public_id = any(cast(:public_ids as text[]))"""
            ),
            {"public_ids": public_ids},
        ).mappings().all()
        existing_by_public_id = {image["public_id"]: image for image in existing_images}
        missing_images: list[dict[str, Any]] = []
        for row in rows:
            slug = row["product_slug"]
            position = int(row["display_order"]) - 1
            product_id = product_ids[slug]
            expected_image = (
                str(product_id),
                row["secure_url"],
                row["alt_text"],
                position,
                int(row["image_width_px"]),
                int(row["image_height_px"]),
            )
            existing_image = existing_by_public_id.get(row["cloudinary_public_id"])
            if existing_image:
                actual_image = (
                    str(existing_image["product_id"]),
                    existing_image["secure_url"],
                    existing_image["alt_text"],
                    existing_image["position"],
                    existing_image["width"],
                    existing_image["height"],
                )
                if actual_image != expected_image:
                    raise SystemExit(
                        f"Se canceló: la imagen de {slug} ya está asociada con otros datos."
                    )
                continue

            missing_images.append(
                {
                    "product_id": product_id,
                    "public_id": row["cloudinary_public_id"],
                    "secure_url": row["secure_url"],
                    "alt_text": row["alt_text"],
                    "position": position,
                    "width": int(row["image_width_px"]),
                    "height": int(row["image_height_px"]),
                    "metadata": json.dumps(
                        {
                            "catalog_code": row["code"],
                            "catalog_category": row["category"],
                            "source_sha256": row["sha256"],
                            "source_archive": "Banco_Muebleria_Ivan_Final.zip",
                        }
                    ),
                }
            )

        if missing_images:
            occupied = connection.execute(
                text(
                    """select p.slug::text
                       from app.products p join app.product_images i on i.product_id = p.id
                       where p.slug::text = any(cast(:slugs as text[]))
                         and i.position = any(cast(:positions as integer[]))"""
                ),
                {
                    "slugs": slugs,
                    "positions": sorted({image["position"] for image in missing_images}),
                },
            ).all()
            if occupied:
                raise SystemExit("Se canceló: una posición de imagen del catálogo está ocupada.")
            connection.execute(
                text(
                    """insert into app.product_images (
                        product_id, public_id, secure_url, alt_text, position,
                        width, height, metadata
                    ) values (
                        :product_id, :public_id, :secure_url, :alt_text, :position,
                        :width, :height, cast(:metadata as jsonb)
                    ) on conflict (public_id) do nothing"""
                ),
                missing_images,
            )
            inserted_images = len(missing_images)

        verified = connection.execute(
            text(
                """select count(distinct p.slug)
                   from app.products p join app.product_images i on i.product_id = p.id
                   where p.slug = any(cast(:slugs as text[])) and i.public_id like :prefix"""
            ),
            {"slugs": slugs, "prefix": f"{IMAGE_PREFIX}%"},
        ).scalar_one()
        if verified != len(rows):
            raise SystemExit("Se canceló: no quedaron vinculados todos los productos e imágenes.")

    engine.dispose()
    print(f"Productos añadidos: {inserted_products}; imágenes vinculadas: {inserted_images}.")
    print(f"Vínculos verificados: {len(rows)}. Repetir la importación no duplica registros.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="aplica los cambios a backend/.env solo si el entorno es demo",
    )
    args = parser.parse_args()
    rows = read_manifest()
    if not args.apply:
        print(f"Manifiesto válido: {len(rows)} productos e imágenes.")
        print("Modo de revisión: no se abrió una conexión ni se modificó la base.")
        print("Añade --apply para importar en la base demo verificada.")
        return
    import_catalog(rows)


if __name__ == "__main__":
    main()
