"""Synchronize public catalog descriptions and base prices with PostgreSQL."""

import csv
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.catalog import Product


def load_catalog_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as source:
        rows = {row["slug"]: row for row in csv.DictReader(source)}
    if not rows:
        raise SystemExit("El archivo de contenido del catálogo está vacío.")
    return rows


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[2]
    content_path = repository_root / "data" / "catalog" / "catalog_merchandising.csv"
    rows = load_catalog_rows(content_path)
    settings = Settings()
    if not settings.database_url:
        raise SystemExit("MUEBLERIA_DATABASE_URL no está configurada.")

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with Session(engine) as session:
        products = session.scalars(select(Product).where(Product.slug.in_(rows))).all()
        found_slugs = {str(product.slug) for product in products}
        missing_slugs = sorted(set(rows) - found_slugs)
        if missing_slugs:
            raise SystemExit(f"No se encontraron productos para: {', '.join(missing_slugs)}")

        updated_at = datetime.now(UTC)
        for product in products:
            row = rows[str(product.slug)]
            product.description = row["description"].strip()
            product.base_price_minor = int(row["base_price_minor"])
            product.updated_at = updated_at
        session.commit()

    print(f"Productos actualizados: {len(products)}")
