import { useCallback, useEffect, useState } from 'react';

import { attachProductImage, getProduct, listProducts, type ProductSummary } from '../../api/modules/catalog';
import { uploadCatalogImage } from '../../api/modules/media';
import { AdminLayout } from '../../components/layout';
import { Button, Modal, Pagination } from '../../components/ui';
import { usePagination } from '../../hooks/usePagination';
import { moneyMinor } from '../../utils/format';

function ProductImageModal({
  product,
  onClose,
  onSaved,
}: {
  product: ProductSummary | null;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [altText, setAltText] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!product || !file) return;
    setBusy(true);
    setError(null);
    try {
      const detail = await getProduct(product.slug);
      const uploaded = await uploadCatalogImage(file);
      await attachProductImage(product.id, {
        assetId: uploaded.asset.id,
        altText: altText.trim(),
        position: detail.images.length,
        width: uploaded.width ?? null,
        height: uploaded.height ?? null,
      });
      await onSaved();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo guardar la imagen.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={Boolean(product)} onClose={onClose} title="Añadir imagen al producto">
      {product && (
        <form className="quote-convert-form" onSubmit={submit}>
          <p><b>{product.name}</b></p>
          <label>
            Imagen JPG, PNG o WebP
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              required
            />
          </label>
          <label>
            Descripción accesible
            <input
              value={altText}
              onChange={(event) => setAltText(event.target.value)}
              minLength={2}
              maxLength={300}
              placeholder={`Ejemplo: ${product.name} en acabado nogal`}
              required
            />
          </label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <div className="modal-actions">
            <Button variant="secondary" onClick={onClose}>Cancelar</Button>
            <Button type="submit" disabled={busy || !file}>
              {busy ? 'Subiendo…' : 'Subir y asociar'}
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}

export function CatalogAdminPage({ showToast }: { showToast: (message: string) => void }) {
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [selected, setSelected] = useState<ProductSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { page, pageItems, setPage, totalPages } = usePagination(products, 12);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setProducts((await listProducts()).items);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No pudimos cargar el catálogo.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const imageSaved = async () => {
    setSelected(null);
    await load();
    showToast('Imagen asociada al producto.');
  };

  return (
    <AdminLayout title="Catálogo" subtitle="IMÁGENES DE PRODUCTOS">
      {loading && <p className="portal-notice" role="status">Cargando productos…</p>}
      {error && (
        <div className="portal-notice portal-error" role="alert">
          <b>{error}</b>
          <Button onClick={() => void load()}>Reintentar</Button>
        </div>
      )}
      {!loading && !error && (
        <div className="catalog-admin-grid">
          {pageItems.map((product) => (
            <article className="admin-card catalog-admin-card" key={product.id}>
              {product.primaryImage ? (
                <img src={product.primaryImage.secureUrl} alt={product.primaryImage.altText} />
              ) : (
                <div className="catalog-image-empty" aria-hidden="true">Sin imagen</div>
              )}
              <div>
                <span className="kicker">{product.category}</span>
                <h2>{product.name}</h2>
                <p>{moneyMinor(product.basePriceMinor)}</p>
                <Button onClick={() => setSelected(product)}>Añadir imagen</Button>
              </div>
            </article>
          ))}
        </div>
      )}
      {!loading && !error && (
        <Pagination
          page={page}
          totalPages={totalPages}
          totalItems={products.length}
          onPageChange={setPage}
          label="productos"
        />
      )}
      <ProductImageModal
        key={selected?.id ?? 'closed'}
        product={selected}
        onClose={() => setSelected(null)}
        onSaved={imageSaved}
      />
    </AdminLayout>
  );
}
