import type { components } from '../generated/schema';
import { apiRequest } from '../client/http';

type MediaFormat = components['schemas']['MediaSignatureRequest']['format'];
type MediaPurpose = components['schemas']['MediaSignatureRequest']['purpose'];
type MediaSignatureResponse = components['schemas']['MediaSignatureResponse'];
type MediaAssetResponse = components['schemas']['MediaAssetResponse'];

interface CloudinaryUploadResponse {
  public_id: string;
  version: number;
  signature: string;
  format?: MediaFormat;
  resource_type: 'image' | 'raw';
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

export const MAX_VOUCHER_BYTES = 10 * 1024 * 1024;

export function validatePaymentVoucher(file: File): void {
  if (!['image/jpeg', 'image/png', 'image/webp', 'application/pdf'].includes(file.type)) {
    throw new Error('Usa un voucher JPG, PNG, WebP o PDF.');
  }
  if (file.size === 0 || file.size > MAX_VOUCHER_BYTES) {
    throw new Error('El voucher debe tener contenido y pesar como máximo 10 MB.');
  }
}

async function uploadMedia(file: File, purpose: MediaPurpose, format: MediaFormat): Promise<UploadedCatalogImage> {
  const signature = await apiRequest<MediaSignatureResponse>('/api/v1/media/signature', {
    method: 'POST',
    body: JSON.stringify({ purpose, format }),
  });
  const signed = signature.data;
  const expectedType = purpose === 'payment_voucher' ? 'private' : 'upload';
  if (signed.deliveryType !== expectedType) {
    throw new Error('No se pudo preparar la carga con el acceso solicitado.');
  }
  const form = new FormData();
  form.append('file', file);
  form.append('api_key', signed.apiKey);
  form.append('timestamp', String(signed.timestamp));
  form.append('signature', signed.signature);
  form.append('public_id', signed.publicId);
  form.append('type', signed.deliveryType);

  const uploadResponse = await fetch(signed.uploadUrl, { method: 'POST', body: form });
  if (!uploadResponse.ok) throw new Error('No se pudo cargar el archivo. Inténtalo nuevamente.');
  const uploaded = await uploadResponse.json() as CloudinaryUploadResponse;
  const confirmation = await apiRequest<MediaAssetResponse>('/api/v1/media/assets', {
    method: 'POST',
    body: JSON.stringify({
      purpose,
      publicId: uploaded.public_id,
      version: uploaded.version,
      signature: uploaded.signature,
      // Raw PDF responses do not include a format field.
      format: uploaded.format ?? format,
      resourceType: uploaded.resource_type,
      bytes: uploaded.bytes,
    }),
  });
  if (purpose === 'payment_voucher' && confirmation.data.access !== 'private') {
    throw new Error('No se pudo confirmar el voucher como archivo privado.');
  }
  return { asset: confirmation.data, width: uploaded.width, height: uploaded.height };
}

export async function uploadCatalogImage(file: File): Promise<UploadedCatalogImage> {
  return uploadMedia(file, 'catalog_image', imageFormat(file));
}

export async function uploadPaymentVoucher(file: File): Promise<components['schemas']['MediaAssetOut']> {
  validatePaymentVoucher(file);
  const format = file.type === 'application/pdf' ? 'pdf' : imageFormat(file);
  return (await uploadMedia(file, 'payment_voucher', format)).asset;
}
