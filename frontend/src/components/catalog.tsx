import { useEffect, useState } from 'react';

import type { ProductImage, ProductSummary } from '../api/modules/catalog';
import { moneyMinor } from '../utils/format';
import { navigate } from './layout';
import { Button, ProductVisual } from './ui';

export function productVisual(category: string, slug: string): string {
  if (category === 'Dormitorio') return 'closet';
  if (category === 'Oficina') return 'desk';
  if (category === 'Sala') return slug.includes('tv') ? 'tv-oak' : 'closet-dark';
  if (category === 'Comedor') return 'desk-light';
  return 'hero';
}

export function CatalogPhoto({
  image,
  fallbackKind,
  className = '',
  eager = false,
  decorative = false,
}: {
  image?: ProductImage | null;
  fallbackKind: string;
  className?: string;
  eager?: boolean;
  decorative?: boolean;
}) {
  const [failed, setFailed] = useState(false);

  useEffect(() => setFailed(false), [image?.secureUrl]);

  if (!image || failed) {
    return <ProductVisual kind={fallbackKind} className={className} />;
  }

  return (
    <img
      className={`catalog-photo ${className}`}
      src={image.secureUrl}
      alt={decorative ? '' : image.altText}
      aria-hidden={decorative || undefined}
      loading={eager ? 'eager' : 'lazy'}
      decoding="async"
      onError={() => setFailed(true)}
    />
  );
}

export function ProductCard({ product }: { product: ProductSummary }) {
  const visual = productVisual(product.category, product.slug);
  return (
    <article className="product-card">
      <CatalogPhoto image={product.primaryImage} fallbackKind={visual} />
      <div className="product-copy">
        <span className="eyebrow">{product.category}</span>
        <h3>{product.name}</h3>
        <p>{product.description}</p>
        <strong>Precio base: {moneyMinor(product.basePriceMinor)}</strong>
        <div className="card-actions">
          <Button variant="secondary" onClick={() => navigate(`/producto/${product.slug}`)}>
            Ver detalle
          </Button>
          <button
            className="text-button"
            onClick={() => navigate(`/cotizador?producto=${product.slug}`)}
          >
            Cotizar similar →
          </button>
        </div>
      </div>
    </article>
  );
}
