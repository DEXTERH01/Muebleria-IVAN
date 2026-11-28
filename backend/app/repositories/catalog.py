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
from app.models.media_asset import MediaAsset


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

    def get_aggregates(
        self,
        products: list[Product],
        *,
        available_only: bool = True,
    ) -> list[ProductAggregate]:
        if not products:
            return []

        product_ids = [product.id for product in products]
        materials: dict[UUID, list[OptionRecord]] = {product_id: [] for product_id in product_ids}
        finishes: dict[UUID, list[OptionRecord]] = {product_id: [] for product_id in product_ids}
        accessories: dict[UUID, list[OptionRecord]] = {product_id: [] for product_id in product_ids}
        images: dict[UUID, list[ProductImage]] = {product_id: [] for product_id in product_ids}

        material_filters = (
            [Material.active.is_(True), Material.available.is_(True)] if available_only else []
        )
        for product_id, option, is_default in self.session.execute(
            select(ProductMaterial.product_id, Material, ProductMaterial.is_default)
            .join(ProductMaterial, ProductMaterial.material_id == Material.id)
            .where(ProductMaterial.product_id.in_(product_ids), *material_filters)
            .order_by(ProductMaterial.product_id, ProductMaterial.is_default.desc(), Material.name)
        ).all():
            materials[product_id].append(OptionRecord(option, is_default))

        finish_filters = (
            [Finish.active.is_(True), Finish.available.is_(True)] if available_only else []
        )
        for product_id, option, is_default in self.session.execute(
            select(ProductFinish.product_id, Finish, ProductFinish.is_default)
            .join(ProductFinish, ProductFinish.finish_id == Finish.id)
            .where(ProductFinish.product_id.in_(product_ids), *finish_filters)
            .order_by(ProductFinish.product_id, ProductFinish.is_default.desc(), Finish.name)
        ).all():
            finishes[product_id].append(OptionRecord(option, is_default))

        accessory_filters = (
            [Accessory.active.is_(True), Accessory.available.is_(True)] if available_only else []
        )
        for product_id, option, is_default in self.session.execute(
            select(ProductAccessory.product_id, Accessory, ProductAccessory.is_default)
            .join(ProductAccessory, ProductAccessory.accessory_id == Accessory.id)
            .where(ProductAccessory.product_id.in_(product_ids), *accessory_filters)
            .order_by(
                ProductAccessory.product_id,
                ProductAccessory.is_default.desc(),
                Accessory.name,
            )
        ).all():
            accessories[product_id].append(OptionRecord(option, is_default))

        for image in self.session.scalars(
            select(ProductImage)
            .where(ProductImage.product_id.in_(product_ids))
            .order_by(ProductImage.product_id, ProductImage.position, ProductImage.id)
        ).all():
            images[image.product_id].append(image)

        return [
            ProductAggregate(
                product=product,
                images=images[product.id],
                materials=materials[product.id],
                finishes=finishes[product.id],
                accessories=accessories[product.id],
            )
            for product in products
        ]

    def add(self, product: Product) -> None:
        self.session.add(product)
        self.session.flush()

    def get_media_asset(self, asset_id: UUID) -> MediaAsset | None:
        return self.session.get(MediaAsset, asset_id)

    def add_image(self, image: ProductImage) -> None:
        self.session.add(image)
        self.session.flush()

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
