"""Persistence queries for products and their allowed options."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.catalog import (
    Accessory,
    Finish,
    Material,
    Product,
    ProductAccessory,
    ProductFinish,
    ProductImage,
    ProductMaterial,
)


@dataclass(frozen=True)
class OptionRecord:
    option: Material | Finish | Accessory
    is_default: bool


@dataclass(frozen=True)
class ProductAggregate:
    product: Product
    images: list[ProductImage]
    materials: list[OptionRecord]
    finishes: list[OptionRecord]
    accessories: list[OptionRecord]


class CatalogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_active(
        self,
        *,
        page: int,
        page_size: int,
        category: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Product], int]:
        filters = [Product.active.is_(True)]
        if category:
            filters.append(func.lower(Product.category) == category.strip().lower())
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(or_(Product.name.ilike(pattern), Product.description.ilike(pattern)))

        total = self.session.scalar(
            select(func.count()).select_from(Product).where(*filters)
        ) or 0
        products = list(
            self.session.scalars(
                select(Product)
                .where(*filters)
                .order_by(Product.category, Product.name, Product.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return products, total

    def get_by_slug(self, slug: str, *, active_only: bool = True) -> Product | None:
        statement = select(Product).where(Product.slug == slug)
        if active_only:
            statement = statement.where(Product.active.is_(True))
        return self.session.scalar(statement)

    def get_by_id(self, product_id: UUID, *, active_only: bool = True) -> Product | None:
        statement = select(Product).where(Product.id == product_id)
        if active_only:
            statement = statement.where(Product.active.is_(True))
        return self.session.scalar(statement)

    def get_aggregate(self, product: Product, *, available_only: bool = True) -> ProductAggregate:
        availability_filter = []
        if available_only:
            availability_filter = [Material.active.is_(True), Material.available.is_(True)]
        materials = [
            OptionRecord(option=row[0], is_default=row[1])
            for row in self.session.execute(
                select(Material, ProductMaterial.is_default)
                .join(ProductMaterial, ProductMaterial.material_id == Material.id)
                .where(ProductMaterial.product_id == product.id, *availability_filter)
                .order_by(ProductMaterial.is_default.desc(), Material.name)
            ).all()
        ]

        availability_filter = []
        if available_only:
            availability_filter = [Finish.active.is_(True), Finish.available.is_(True)]
        finishes = [
            OptionRecord(option=row[0], is_default=row[1])
            for row in self.session.execute(
                select(Finish, ProductFinish.is_default)
                .join(ProductFinish, ProductFinish.finish_id == Finish.id)
                .where(ProductFinish.product_id == product.id, *availability_filter)
                .order_by(ProductFinish.is_default.desc(), Finish.name)
            ).all()
        ]

        availability_filter = []
        if available_only:
            availability_filter = [Accessory.active.is_(True), Accessory.available.is_(True)]
        accessories = [
            OptionRecord(option=row[0], is_default=row[1])
            for row in self.session.execute(
                select(Accessory, ProductAccessory.is_default)
                .join(ProductAccessory, ProductAccessory.accessory_id == Accessory.id)
                .where(ProductAccessory.product_id == product.id, *availability_filter)
                .order_by(ProductAccessory.is_default.desc(), Accessory.name)
            ).all()
        ]

        images = list(
            self.session.scalars(
                select(ProductImage)
                .where(ProductImage.product_id == product.id)
                .order_by(ProductImage.position, ProductImage.id)
            ).all()
        )
        return ProductAggregate(
            product=product,
            images=images,
            materials=materials,
            finishes=finishes,
            accessories=accessories,
        )

    def add(self, product: Product) -> None:
        self.session.add(product)
        self.session.flush()

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
