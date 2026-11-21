"""Pydantic contracts for public and administrative catalog operations."""

from decimal import Decimal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.common import ApiModel


class MeasurementLimits(ApiModel):
    min_width_mm: int
    max_width_mm: int
    min_height_mm: int
    max_height_mm: int
    min_depth_mm: int
    max_depth_mm: int


class ProductImageData(ApiModel):
    id: UUID
    secure_url: str
    alt_text: str
    position: int
    width: int | None = None
    height: int | None = None


class ProductImageAttachRequest(ApiModel):
    asset_id: UUID
    alt_text: str = Field(min_length=2, max_length=300)
    position: int = Field(default=0, ge=0, le=1000)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)


class CatalogOptionData(ApiModel):
    id: UUID
    code: str
    name: str
    description: str
    price_adjustment_minor: int
    price_adjustment_percent: Decimal
    is_default: bool


class ProductSummaryData(ApiModel):
    id: UUID
    slug: str
    name: str
    description: str
    category: str
    base_price_minor: int
    min_production_days: int
    max_production_days: int
    primary_image: ProductImageData | None = None


class ProductDetailData(ProductSummaryData):
    active: bool
    measurement_limits: MeasurementLimits
    images: list[ProductImageData]
    materials: list[CatalogOptionData]
    finishes: list[CatalogOptionData]
    accessories: list[CatalogOptionData]


class ProductListData(ApiModel):
    items: list[ProductSummaryData]
    page: int
    page_size: int
    total: int


class ProductListResponse(ApiModel):
    data: ProductListData


class ProductResponse(ApiModel):
    data: ProductDetailData


class ProductCreateRequest(ApiModel):
    slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=4000)
    category: str = Field(min_length=2, max_length=80)
    base_price_minor: int = Field(ge=0)
    min_production_days: int = Field(gt=0, le=365)
    max_production_days: int = Field(gt=0, le=365)
    min_width_mm: int = Field(gt=0, le=10000)
    max_width_mm: int = Field(gt=0, le=10000)
    min_height_mm: int = Field(gt=0, le=10000)
    max_height_mm: int = Field(gt=0, le=10000)
    min_depth_mm: int = Field(gt=0, le=10000)
    max_depth_mm: int = Field(gt=0, le=10000)
    active: bool = True

    @model_validator(mode="after")
    def validate_ranges(self) -> "ProductCreateRequest":
        if self.max_production_days < self.min_production_days:
            raise ValueError("maxProductionDays debe ser mayor o igual que minProductionDays.")
        for dimension in ("width", "height", "depth"):
            minimum = getattr(self, f"min_{dimension}_mm")
            maximum = getattr(self, f"max_{dimension}_mm")
            if maximum < minimum:
                raise ValueError(
                    f"max{dimension.capitalize()}Mm debe ser mayor o igual que "
                    f"min{dimension.capitalize()}Mm."
                )
        return self


class ProductUpdateRequest(ApiModel):
    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, min_length=2, max_length=80)
    base_price_minor: int | None = Field(default=None, ge=0)
    min_production_days: int | None = Field(default=None, gt=0, le=365)
    max_production_days: int | None = Field(default=None, gt=0, le=365)
    min_width_mm: int | None = Field(default=None, gt=0, le=10000)
    max_width_mm: int | None = Field(default=None, gt=0, le=10000)
    min_height_mm: int | None = Field(default=None, gt=0, le=10000)
    max_height_mm: int | None = Field(default=None, gt=0, le=10000)
    min_depth_mm: int | None = Field(default=None, gt=0, le=10000)
    max_depth_mm: int | None = Field(default=None, gt=0, le=10000)
    active: bool | None = None

    @model_validator(mode="after")
    def require_change(self) -> "ProductUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("Debe enviar al menos un campo para actualizar.")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Los campos enviados no pueden ser null.")
        return self
