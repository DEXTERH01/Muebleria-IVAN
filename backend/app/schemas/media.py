from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

MediaPurpose = Literal["catalog_image", "payment_voucher"]
MediaFormat = Literal["jpg", "jpeg", "png", "webp", "pdf"]


class MediaSignatureRequest(BaseModel):
    purpose: MediaPurpose
    format: MediaFormat

    @model_validator(mode="after")
    def restrict_format_by_purpose(self) -> "MediaSignatureRequest":
        if self.purpose == "catalog_image" and self.format == "pdf":
            raise ValueError("El catálogo solo admite imágenes.")
        return self


class MediaSignatureData(BaseModel):
    cloud_name: str = Field(alias="cloudName")
    api_key: str = Field(alias="apiKey")
    timestamp: int
    signature: str
    public_id: str = Field(alias="publicId")
    resource_type: Literal["image", "raw"] = Field(alias="resourceType")
    delivery_type: Literal["upload", "private"] = Field(alias="deliveryType")
    format: MediaFormat
    upload_url: str = Field(alias="uploadUrl")

    model_config = ConfigDict(populate_by_name=True)


class MediaSignatureResponse(BaseModel):
    data: MediaSignatureData


class MediaAssetConfirm(BaseModel):
    purpose: MediaPurpose
    public_id: str = Field(alias="publicId", min_length=1, max_length=500)
    version: int = Field(gt=0)
    signature: str = Field(min_length=40, max_length=64)
    format: MediaFormat
    resource_type: Literal["image", "raw"] = Field(alias="resourceType")
    bytes: int = Field(gt=0)

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_asset_kind(self) -> "MediaAssetConfirm":
        expected = "raw" if self.format == "pdf" else "image"
        if self.resource_type != expected:
            raise ValueError("El tipo de recurso no coincide con el formato.")
        if self.purpose == "catalog_image" and self.format == "pdf":
            raise ValueError("El catálogo solo admite imágenes.")
        return self


class MediaAssetOut(BaseModel):
    id: UUID
    external_id: str = Field(alias="externalId")
    media_type: str = Field(alias="mediaType")
    access: Literal["public", "private"]
    created_at: datetime = Field(alias="createdAt")
    url: str | None = None
    download_url: str | None = Field(default=None, alias="downloadUrl")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MediaAssetResponse(BaseModel):
    data: MediaAssetOut
