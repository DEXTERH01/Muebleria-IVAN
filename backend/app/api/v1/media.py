"""Signed Cloudinary uploads and protected media metadata."""

import hashlib
import hmac
import time
from urllib.parse import urlencode
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user, require_roles
from app.models.media_asset import MediaAsset
from app.schemas.media import (
    MediaAssetConfirm,
    MediaAssetOut,
    MediaAssetResponse,
    MediaSignatureData,
    MediaSignatureRequest,
    MediaSignatureResponse,
)

router = APIRouter(prefix="/media", tags=["media"])
PRIVATE_URL_TTL_SECONDS = 600


def cloudinary_signature(params: dict[str, str | int], api_secret: str, algorithm: str) -> str:
    payload = "&".join(f"{key}={params[key]}" for key in sorted(params))
    digest = hashlib.new(algorithm, f"{payload}{api_secret}".encode())
    return digest.hexdigest()


def verify_cloudinary_upload_signature(
    public_id: str,
    version: int,
    signature: str,
    api_secret: str,
    algorithm: str,
) -> bool:
    expected = cloudinary_signature(
        {"public_id": public_id, "version": version}, api_secret, algorithm
    )
    return hmac.compare_digest(expected, signature.lower())


def _credentials(settings: Settings) -> tuple[str, str, str]:
    if not all(
        (
            settings.cloudinary_cloud_name,
            settings.cloudinary_api_key,
            settings.cloudinary_api_secret,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary no está configurado.",
        )
    return (
        settings.cloudinary_cloud_name,
        settings.cloudinary_api_key,
        settings.cloudinary_api_secret,
    )


@router.post(
    "/signature",
    response_model=MediaSignatureResponse,
    summary="Obtener firma de carga a Cloudinary",
)
def get_upload_signature(
    payload: MediaSignatureRequest,
    user: CurrentUser = Depends(require_roles("operator", "admin")),
    settings: Settings = Depends(get_settings),
) -> MediaSignatureResponse:
    cloud_name, api_key, api_secret = _credentials(settings)
    folder = "catalog" if payload.purpose == "catalog_image" else "vouchers"
    public_id = f"muebleria-ivan/{folder}/{user.user_id}/{uuid4()}"
    resource_type = "raw" if payload.format == "pdf" else "image"
    if resource_type == "raw":
        public_id = f"{public_id}.pdf"
    delivery_type = "private" if payload.purpose == "payment_voucher" else "upload"
    timestamp = int(time.time())
    signed_params: dict[str, str | int] = {
        "public_id": public_id,
        "timestamp": timestamp,
        "type": delivery_type,
    }
    signature = cloudinary_signature(
        signed_params, api_secret, settings.cloudinary_signature_algorithm
    )
    return MediaSignatureResponse(
        data=MediaSignatureData(
            cloud_name=cloud_name,
            api_key=api_key,
            timestamp=timestamp,
            signature=signature,
            public_id=public_id,
            resource_type=resource_type,
            delivery_type=delivery_type,
            format=payload.format,
            upload_url=(
                f"https://api.cloudinary.com/v1_1/{cloud_name}/{resource_type}/upload"
            ),
        )
    )


@router.post(
    "/assets",
    response_model=MediaAssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar carga completada",
)
def confirm_upload(
    payload: MediaAssetConfirm,
    user: CurrentUser = Depends(require_roles("operator", "admin")),
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
) -> MediaAssetResponse:
    cloud_name, _api_key, api_secret = _credentials(settings)
    folder = "catalog" if payload.purpose == "catalog_image" else "vouchers"
    prefix = f"muebleria-ivan/{folder}/{user.user_id}/"
    if not payload.public_id.startswith(prefix) or ".." in payload.public_id:
        raise HTTPException(status_code=403, detail="El recurso no corresponde a esta sesión.")

    if not verify_cloudinary_upload_signature(
        payload.public_id,
        payload.version,
        payload.signature,
        api_secret,
        settings.cloudinary_signature_algorithm,
    ):
        raise HTTPException(status_code=422, detail="La firma de carga no es válida.")

    is_private = payload.purpose == "payment_voucher"
    media = MediaAsset(
        provider="cloudinary",
        external_id=payload.public_id,
        media_type=("application/pdf" if payload.format == "pdf" else f"image/{payload.format}"),
        access="private" if is_private else "public",
        owner_user_id=user.user_id,
        metadata_json={
            "purpose": payload.purpose,
            "version": payload.version,
            "format": payload.format,
            "resource_type": payload.resource_type,
            "delivery_type": "private" if is_private else "upload",
            "bytes": payload.bytes,
        },
    )
    session.add(media)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="El recurso ya fue registrado.") from exc
    session.refresh(media)
    url = None if is_private else _public_url(cloud_name, media)
    return MediaAssetResponse(
        data=MediaAssetOut(
            id=media.id,
            external_id=media.external_id,
            media_type=media.media_type,
            access=media.access,
            created_at=media.created_at,
            url=url,
        )
    )


def _public_url(cloud_name: str, media: MediaAsset) -> str | None:
    if media.access != "public":
        return None
    metadata = media.metadata_json
    return (
        f"https://res.cloudinary.com/{cloud_name}/image/upload/"
        f"v{metadata['version']}/{media.external_id}.{metadata['format']}"
    )


def _private_download_url(settings: Settings, media: MediaAsset) -> str:
    cloud_name, api_key, api_secret = _credentials(settings)
    metadata = media.metadata_json
    timestamp = int(time.time())
    params: dict[str, str | int] = {
        "public_id": media.external_id,
        "format": metadata["format"],
        "timestamp": timestamp,
        "expires_at": timestamp + PRIVATE_URL_TTL_SECONDS,
    }
    signature = cloudinary_signature(
        params, api_secret, settings.cloudinary_signature_algorithm
    )
    query = urlencode({**params, "api_key": api_key, "signature": signature})
    return (
        f"https://api.cloudinary.com/v1_1/{cloud_name}/"
        f"{metadata['resource_type']}/download?{query}"
    )


@router.get(
    "/{asset_id}", response_model=MediaAssetResponse, summary="Metadatos del recurso multimedia"
)
def get_asset(
    asset_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
) -> MediaAssetResponse:
    media = session.get(MediaAsset, asset_id)
    if media is None:
        raise HTTPException(status_code=404, detail="No se encontró el recurso multimedia.")
    if (
        media.access == "private"
        and media.owner_user_id != user.user_id
        and user.role not in {"operator", "admin"}
    ):
        raise HTTPException(status_code=404, detail="No se encontró el recurso multimedia.")
    if media.access == "private":
        download_url = _private_download_url(settings, media)
        url = None
    else:
        cloud_name, _, _ = _credentials(settings)
        download_url = None
        url = _public_url(cloud_name, media)
    return MediaAssetResponse(
        data=MediaAssetOut(
            id=media.id,
            external_id=media.external_id,
            media_type=media.media_type,
            access=media.access,
            created_at=media.created_at,
            url=url,
            download_url=download_url,
        )
    )
