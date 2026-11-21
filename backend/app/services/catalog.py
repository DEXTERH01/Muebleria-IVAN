"""Catalog application service and API mapping."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from app.domain.catalog import (
    DuplicateProductError,
    InvalidCatalogMediaError,
    ProductNotFoundError,
)
from app.models.catalog import Product, ProductImage
from app.repositories.catalog import CatalogRepository, OptionRecord, ProductAggregate
from app.schemas.catalog import (
    CatalogOptionData,
    MeasurementLimits,
    ProductCreateRequest,
    ProductDetailData,
    ProductImageAttachRequest,
    ProductImageData,
    ProductListData,
    ProductSummaryData,
    ProductUpdateRequest,
)


class CatalogService:
    def __init__(self, repository: CatalogRepository) -> None:
        self.repository = repository

    def list_products(
        self,
        *,
        page: int,
        page_size: int,
        category: str | None = None,
        search: str | None = None,
    ) -> ProductListData:
        products, total = self.repository.list_active(
            page=page,
            page_size=page_size,
            category=category,
            search=search,
        )
        items = [self._summary(self.repository.get_aggregate(product)) for product in products]
        return ProductListData(items=items, page=page, page_size=page_size, total=total)

    def product_by_slug(self, slug: str) -> ProductDetailData:
        product = self.repository.get_by_slug(slug)
        if product is None:
            raise ProductNotFoundError("El producto solicitado no existe o no está activo.")
        return self._detail(self.repository.get_aggregate(product))

    def create_product(self, request: ProductCreateRequest) -> ProductDetailData:
        if self.repository.get_by_slug(request.slug, active_only=False):
            raise DuplicateProductError("Ya existe un producto con ese slug.")
        now = datetime.now(UTC)
        product = Product(
            id=uuid4(),
            **request.model_dump(),
            created_at=now,
            updated_at=now,
        )
        try:
            self.repository.add(product)
            self.repository.commit()
        except IntegrityError as exc:
            self.repository.rollback()
            raise DuplicateProductError("El slug del producto ya está registrado.") from exc
        return self._detail(self.repository.get_aggregate(product, available_only=False))

    def update_product(
        self, product_id: UUID, request: ProductUpdateRequest
    ) -> ProductDetailData:
        product = self.repository.get_by_id(product_id, active_only=False)
        if product is None:
            raise ProductNotFoundError("El producto solicitado no existe.")

        changes = request.model_dump(exclude_unset=True)
        if "slug" in changes:
            duplicate = self.repository.get_by_slug(changes["slug"], active_only=False)
            if duplicate and duplicate.id != product_id:
                raise DuplicateProductError("Ya existe un producto con ese slug.")

        candidate = {
            field: changes.get(field, getattr(product, field))
            for field in (
                "min_production_days",
                "max_production_days",
                "min_width_mm",
                "max_width_mm",
                "min_height_mm",
                "max_height_mm",
                "min_depth_mm",
                "max_depth_mm",
            )
        }
        self._validate_ranges(candidate)
        for field, value in changes.items():
            setattr(product, field, value)
        product.updated_at = datetime.now(UTC)
        try:
            self.repository.flush()
            self.repository.commit()
        except IntegrityError as exc:
            self.repository.rollback()
            raise DuplicateProductError("El slug del producto ya está registrado.") from exc
        return self._detail(self.repository.get_aggregate(product, available_only=False))

    def deactivate_product(self, product_id: UUID) -> None:
        product = self.repository.get_by_id(product_id, active_only=False)
        if product is None:
            raise ProductNotFoundError("El producto solicitado no existe.")
        product.active = False
        product.updated_at = datetime.now(UTC)
        self.repository.flush()
        self.repository.commit()

    def attach_image(
        self,
        product_id: UUID,
        request: ProductImageAttachRequest,
        *,
        cloud_name: str,
    ) -> ProductDetailData:
        product = self.repository.get_by_id(product_id, active_only=False)
        if product is None:
            raise ProductNotFoundError("El producto solicitado no existe.")
        asset = self.repository.get_media_asset(request.asset_id)
        metadata = asset.metadata_json if asset is not None else {}
        if (
            asset is None
            or asset.provider != "cloudinary"
            or asset.access != "public"
            or metadata.get("purpose") != "catalog_image"
            or metadata.get("resource_type") != "image"
        ):
            raise InvalidCatalogMediaError(
                "El recurso no es una imagen pública verificada del catálogo."
            )
        version = metadata.get("version")
        image_format = metadata.get("format")
        if (
            not isinstance(version, int)
            or image_format not in {"jpg", "jpeg", "png", "webp"}
        ):
            raise InvalidCatalogMediaError("El recurso no contiene metadatos válidos.")
        now = datetime.now(UTC)
        image = ProductImage(
            id=uuid4(),
            product_id=product.id,
            public_id=asset.external_id,
            secure_url=(
                f"https://res.cloudinary.com/{cloud_name}/image/upload/"
                f"v{version}/{asset.external_id}.{image_format}"
            ),
            alt_text=request.alt_text.strip(),
            position=request.position,
            width=request.width,
            height=request.height,
            metadata_={"assetId": str(asset.id), "provider": asset.provider},
            created_at=now,
            updated_at=now,
        )
        try:
            self.repository.add_image(image)
            self.repository.commit()
        except IntegrityError as exc:
            self.repository.rollback()
            raise InvalidCatalogMediaError(
                "La imagen ya está asociada a un producto."
            ) from exc
        return self._detail(self.repository.get_aggregate(product, available_only=False))

    @staticmethod
    def _validate_ranges(values: dict[str, int]) -> None:
        if values["max_production_days"] < values["min_production_days"]:
            raise ValueError("El rango de días de fabricación no es válido.")
        for dimension in ("width", "height", "depth"):
            if values[f"max_{dimension}_mm"] < values[f"min_{dimension}_mm"]:
                raise ValueError(f"El rango de {dimension} no es válido.")

    @staticmethod
    def _image(image: object) -> ProductImageData:
        return ProductImageData.model_validate(image)

    @staticmethod
    def _option(record: OptionRecord) -> CatalogOptionData:
        return CatalogOptionData(
            id=record.option.id,
            code=str(record.option.code),
            name=record.option.name,
            description=record.option.description,
            price_adjustment_minor=record.option.price_adjustment_minor,
            price_adjustment_percent=record.option.price_adjustment_percent,
            is_default=record.is_default,
        )

    def _summary(self, aggregate: ProductAggregate) -> ProductSummaryData:
        product = aggregate.product
        return ProductSummaryData(
            id=product.id,
            slug=str(product.slug),
            name=product.name,
            description=product.description,
            category=product.category,
            base_price_minor=product.base_price_minor,
            min_production_days=product.min_production_days,
            max_production_days=product.max_production_days,
            primary_image=self._image(aggregate.images[0]) if aggregate.images else None,
        )

    def _detail(self, aggregate: ProductAggregate) -> ProductDetailData:
        product = aggregate.product
        summary = self._summary(aggregate)
        return ProductDetailData(
            **summary.model_dump(),
            active=product.active,
            measurement_limits=MeasurementLimits(
                min_width_mm=product.min_width_mm,
                max_width_mm=product.max_width_mm,
                min_height_mm=product.min_height_mm,
                max_height_mm=product.max_height_mm,
                min_depth_mm=product.min_depth_mm,
                max_depth_mm=product.max_depth_mm,
            ),
            images=[self._image(image) for image in aggregate.images],
            materials=[self._option(option) for option in aggregate.materials],
            finishes=[self._option(option) for option in aggregate.finishes],
            accessories=[self._option(option) for option in aggregate.accessories],
        )
