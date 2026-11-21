from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.catalog import (
    DuplicateProductError,
    InvalidCatalogMediaError,
    ProductNotFoundError,
)
from app.models.catalog import Material, Product, ProductImage
from app.models.media_asset import MediaAsset
from app.repositories.catalog import OptionRecord, ProductAggregate
from app.schemas.catalog import (
    ProductCreateRequest,
    ProductImageAttachRequest,
    ProductUpdateRequest,
)
from app.services.catalog import CatalogService


def aggregate(*, active: bool = True) -> ProductAggregate:
    now = datetime.now(UTC)
    product = Product(
        id=uuid4(),
        slug="escritorio-prueba",
        name="Escritorio prueba",
        description="Descripción",
        category="Oficina",
        base_price_minor=80_000,
        active=active,
        min_production_days=5,
        max_production_days=9,
        min_width_mm=900,
        max_width_mm=1800,
        min_height_mm=700,
        max_height_mm=900,
        min_depth_mm=450,
        max_depth_mm=800,
        created_at=now,
        updated_at=now,
    )
    image = ProductImage(
        id=uuid4(),
        product_id=product.id,
        public_id="demo/image",
        secure_url="https://example.test/image.jpg",
        alt_text="Escritorio",
        position=0,
        width=1200,
        height=900,
        metadata_={},
        created_at=now,
        updated_at=now,
    )
    material = Material(
        id=uuid4(),
        code="MEL-18",
        name="Melamina",
        description="",
        price_adjustment_minor=0,
        price_adjustment_percent=Decimal(0),
        active=True,
        available=True,
        created_at=now,
        updated_at=now,
    )
    return ProductAggregate(product, [image], [OptionRecord(material, True)], [], [])


class FakeRepository:
    def __init__(self, value: ProductAggregate | None = None) -> None:
        self.value = value
        self.media_asset = None
        self.commits = 0

    def list_active(self, **_filters):
        return ([self.value.product], 1) if self.value else ([], 0)

    def get_by_slug(self, slug, *, active_only=True):
        if self.value and self.value.product.slug == slug:
            if active_only and not self.value.product.active:
                return None
            return self.value.product
        return None

    def get_by_id(self, product_id, *, active_only=True):
        if self.value and self.value.product.id == product_id:
            if active_only and not self.value.product.active:
                return None
            return self.value.product
        return None

    def get_aggregate(self, product, *, available_only=True):
        if self.value and self.value.product.id == product.id:
            return self.value
        return ProductAggregate(product, [], [], [], [])

    def get_aggregates(self, products, *, available_only=True):
        return [self.get_aggregate(product, available_only=available_only) for product in products]

    def add(self, product):
        self.value = ProductAggregate(product, [], [], [], [])

    def get_media_asset(self, asset_id):
        if self.media_asset and self.media_asset.id == asset_id:
            return self.media_asset
        return None

    def add_image(self, image):
        self.value.images.append(image)

    def flush(self):
        return None

    def commit(self):
        self.commits += 1

    def rollback(self):
        return None


def test_catalog_maps_active_products_images_and_options() -> None:
    repository = FakeRepository(aggregate())
    service = CatalogService(repository)

    page = service.list_products(page=1, page_size=20)
    detail = service.product_by_slug("escritorio-prueba")

    assert page.total == 1
    assert page.items[0].primary_image.alt_text == "Escritorio"
    assert detail.materials[0].is_default is True
    assert detail.measurement_limits.min_width_mm == 900


def test_catalog_creates_updates_and_soft_deletes_product() -> None:
    repository = FakeRepository()
    service = CatalogService(repository)
    created = service.create_product(
        ProductCreateRequest(
            slug="mesa-prueba",
            name="Mesa prueba",
            category="Comedor",
            base_price_minor=100_000,
            min_production_days=5,
            max_production_days=10,
            min_width_mm=1000,
            max_width_mm=2000,
            min_height_mm=700,
            max_height_mm=900,
            min_depth_mm=600,
            max_depth_mm=1000,
        )
    )
    updated = service.update_product(
        created.id,
        ProductUpdateRequest(name="Mesa prueba actualizada", base_price_minor=110_000),
    )
    service.deactivate_product(created.id)

    assert updated.name == "Mesa prueba actualizada"
    assert updated.base_price_minor == 110_000
    assert repository.value.product.active is False
    assert repository.commits == 3


def test_catalog_rejects_duplicate_slug_and_missing_product() -> None:
    repository = FakeRepository(aggregate())
    service = CatalogService(repository)
    with pytest.raises(DuplicateProductError):
        service.create_product(
            ProductCreateRequest(
                slug="escritorio-prueba",
                name="Duplicado",
                category="Oficina",
                base_price_minor=1,
                min_production_days=1,
                max_production_days=1,
                min_width_mm=1,
                max_width_mm=1,
                min_height_mm=1,
                max_height_mm=1,
                min_depth_mm=1,
                max_depth_mm=1,
            )
        )
    with pytest.raises(ProductNotFoundError):
        service.product_by_slug("no-existe")


def test_catalog_attaches_verified_cloudinary_asset() -> None:
    repository = FakeRepository(aggregate())
    repository.value.images.clear()
    repository.media_asset = MediaAsset(
        id=uuid4(),
        provider="cloudinary",
        external_id="muebleria-ivan/catalog/admin/image-id",
        media_type="image/webp",
        access="public",
        owner_user_id=uuid4(),
        metadata_json={
            "purpose": "catalog_image",
            "version": 123,
            "format": "webp",
            "resource_type": "image",
        },
    )
    service = CatalogService(repository)

    product = service.attach_image(
        repository.value.product.id,
        ProductImageAttachRequest(
            asset_id=repository.media_asset.id,
            alt_text="Escritorio de melamina",
            position=0,
            width=1200,
            height=900,
        ),
        cloud_name="demo-cloud",
    )

    assert product.images[0].secure_url == (
        "https://res.cloudinary.com/demo-cloud/image/upload/"
        "v123/muebleria-ivan/catalog/admin/image-id.webp"
    )
    assert product.images[0].alt_text == "Escritorio de melamina"


def test_catalog_rejects_unverified_product_image() -> None:
    repository = FakeRepository(aggregate())
    service = CatalogService(repository)

    with pytest.raises(InvalidCatalogMediaError):
        service.attach_image(
            repository.value.product.id,
            ProductImageAttachRequest(
                asset_id=uuid4(),
                alt_text="Imagen inválida",
            ),
            cloud_name="demo-cloud",
        )
