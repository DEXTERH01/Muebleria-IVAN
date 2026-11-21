import type { components } from '../generated/schema';
import { apiRequest } from '../client/http';

type MediaFormat = Extract<components['schemas']['MediaSignatureRequest']['format'], 'jpg' | 'jpeg' | 'png' | 'webp'>;
type MediaSignatureResponse = components['schemas']['MediaSignatureResponse'];
type MediaAssetResponse = components['schemas']['MediaAssetResponse'];

interface CloudinaryUploadResponse {
  public_id: string;
  version: number;
  signature: string;
  format: MediaFormat;
  resource_type: 'image';
  bytes: number;
  width?: number;
  height?: number;
}

export interface UploadedCatalogImage {
  asset: components['schemas']['MediaAssetOut'];
  width?: number;
  height?: number;
}

function imageFormat(file: File): MediaFormat {
  const formats: Record<string, MediaFormat> = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/webp': 'webp',
  };
  const format = formats[file.type];
  if (!format) throw new Error('Usa una imagen JPG, PNG o WebP.');
  return format;
}

export async function uploadCatalogImage(file: File): Promise<UploadedCatalogImage> {
  const format = imageFormat(file);
  const signature = await apiRequest<MediaSignatureResponse>('/api/v1/media/signature', {
    method: 'POST',
    body: JSON.stringify({ purpose: 'catalog_image', format }),
  });
  const signed = signature.data;
  const form = new FormData();
  form.append('file', file);
  form.append('api_key', signed.apiKey);
  form.append('timestamp', String(signed.timestamp));
  form.append('signature', signed.signature);
  form.append('public_id', signed.publicId);
  form.append('type', signed.deliveryType);

  const uploadResponse = await fetch(signed.uploadUrl, { method: 'POST', body: form });
  if (!uploadResponse.ok) throw new Error('Cloudinary no pudo cargar la imagen.');
  const uploaded = await uploadResponse.json() as CloudinaryUploadResponse;
  const confirmation = await apiRequest<MediaAssetResponse>('/api/v1/media/assets', {
    method: 'POST',
    body: JSON.stringify({
      purpose: 'catalog_image',
      publicId: uploaded.public_id,
      version: uploaded.version,
      signature: uploaded.signature,
      format: uploaded.format,
      resourceType: uploaded.resource_type,
      bytes: uploaded.bytes,
    }),
  });
  return { asset: confirmation.data, width: uploaded.width, height: uploaded.height };
}
