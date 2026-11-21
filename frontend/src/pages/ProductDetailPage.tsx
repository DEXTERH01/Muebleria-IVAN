import { useEffect, useState } from 'react';

import { getProduct, type ProductDetail } from '../api/modules/catalog';
import { productVisual } from '../components/catalog';
import { Footer, Navbar, navigate } from '../components/layout';
import { Button, ProductVisual } from '../components/ui';
import { moneyMinor } from '../utils/format';

export function ProductDetailPage({ id }: { id: string }) {
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    getProduct(id)
      .then((value) => {
        if (active) setProduct(value);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : 'No pudimos cargar el producto.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [id, retry]);

  const visual = product ? productVisual(product.category, product.slug) : 'hero';

  return (
    <>
      <Navbar />
      <main className="detail-page">
        <button className="breadcrumb" onClick={() => navigate('/catalogo')}>
          ← Volver al catálogo
        </button>
        {loading && <div className="empty" role="status">Cargando producto…</div>}
        {error && (
          <div className="empty" role="alert">
            <b>{error}</b>
            <p>El diseño puede no estar disponible en este momento.</p>
            <Button onClick={() => setRetry((value) => value + 1)}>Reintentar</Button>
          </div>
        )}
        {product && !loading && !error && (
          <div className="detail-layout">
            <div className="detail-gallery">
              <ProductVisual kind={visual} className="detail-main-visual" />
              <div className="thumbnails">
                <button className="selected" aria-label="Vista del producto">
                  <ProductVisual kind={visual} />
                </button>
              </div>
            </div>
            <article className="detail-info">
              <span className="eyebrow">{product.category}</span>
              <h1>{product.name}</h1>
              <p className="detail-description">{product.description}</p>
              <strong className="price">Desde {moneyMinor(product.basePriceMinor)}</strong>
              <span className="ref-label">Precio referencial</span>
              <hr />
              <dl>
                <div>
                  <dt>Material base</dt>
                  <dd>{product.materials.find((option) => option.isDefault)?.name ?? 'A elegir'}</dd>
                </div>
                <div>
                  <dt>Acabado base</dt>
                  <dd>{product.finishes.find((option) => option.isDefault)?.name ?? 'A elegir'}</dd>
                </div>
              </dl>
              <div className="features">
                <h3>Personalización disponible</h3>
                <ul>
                  <li>{product.materials.length} opciones de material</li>
                  <li>{product.finishes.length} opciones de acabado</li>
                  <li>{product.accessories.length} accesorios compatibles</li>
                  <li>Fabricación estimada de {product.minProductionDays} a {product.maxProductionDays} días</li>
                </ul>
              </div>
              <p className="notice">
                Este precio es referencial. El backend calcula la estimación según medidas,
                materiales y accesorios seleccionados.
              </p>
              <div className="detail-actions">
                <Button onClick={() => navigate(`/cotizador?producto=${product.slug}`)}>
                  Personalizar y cotizar
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => navigator.clipboard?.writeText(`Hola, me interesa el ${product.name}.`)}
                >
                  Consultar por WhatsApp
                </Button>
              </div>
            </article>
          </div>
        )}
      </main>
      <Footer />
    </>
  );
}
