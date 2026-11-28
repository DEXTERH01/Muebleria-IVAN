import { useEffect, useMemo, useState } from 'react';

import { listProducts, type ProductSummary } from '../api/modules/catalog';
import { Footer, Navbar, navigate } from '../components/layout';
import { Button } from '../components/ui';
import { moneyMinor } from '../utils/format';

const preferredCategories = [
  'Dormitorio',
  'Comedor',
  'Escritorios',
  'Centros de entretenimiento',
];

function featuredProducts(products: ProductSummary[]): ProductSummary[] {
  const preferred = preferredCategories
    .map((category) => products.find((product) => (
      product.category === category && product.primaryImage
    )))
    .filter((product): product is ProductSummary => Boolean(product));
  const selected = new Set(preferred.map((product) => product.id));
  const additional = products.filter((product) => product.primaryImage && !selected.has(product.id));
  return [...preferred, ...additional].slice(0, 4);
}

export function HomePage() {
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [catalogAvailable, setCatalogAvailable] = useState(true);

  useEffect(() => {
    let active = true;
    listProducts()
      .then((response) => {
        if (active) setProducts(response.items);
      })
      .catch(() => {
        if (active) setCatalogAvailable(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const featured = useMemo(() => featuredProducts(products), [products]);
  const heroProduct = products.find((product) => product.slug === 'ropero-andino')
    ?? featured[0];
  const ctaProduct = featured[1] ?? heroProduct;

  return <>
    <Navbar />
    <main className="home-modern">
      <section className="home-hero">
        <div className="home-hero-copy">
          <span className="home-overline">MUEBLERÍA IVÁN · DISEÑO EN LIMA</span>
          <h1>Tu espacio merece un mueble que <i>sí encaje.</i></h1>
          <p>Explora diseños reales, personaliza medidas y recibe una cotización calculada para tu proyecto.</p>
          <div className="home-hero-actions">
            <Button onClick={() => navigate('/catalogo')}>Explorar diseños</Button>
            <Button variant="secondary" onClick={() => navigate('/cotizador')}>Crear mi cotización</Button>
          </div>
          <div className="home-proof" aria-label="Características del servicio">
            <span><b>01</b> Medidas personalizables</span>
            <span><b>02</b> Seguimiento por etapas</span>
          </div>
        </div>
        <figure className={`home-hero-media ${heroProduct?.primaryImage ? '' : 'is-loading'}`}>
          {heroProduct?.primaryImage ? <img
            src={heroProduct.primaryImage.secureUrl}
            alt={heroProduct.primaryImage.altText || heroProduct.name}
          /> : <div className="home-image-placeholder"><span>MI</span><p>Preparando inspiración para tu espacio</p></div>}
          {heroProduct && <figcaption>
            <div><span>{heroProduct.category}</span><b>{heroProduct.name}</b></div>
            <strong>Precio base {moneyMinor(heroProduct.basePriceMinor)}</strong>
          </figcaption>}
        </figure>
      </section>

      <section className="home-service-strip" aria-label="Características de la plataforma">
        <div><span>Diseños publicados</span><b>{products.length || '—'}</b></div>
        <div><span>Cotización</span><b>Calculada en línea</b></div>
        <div><span>Producción</span><b>Seguimiento por etapas</b></div>
        <div><span>Atención</span><b>Lima, Perú</b></div>
      </section>

      <section className="home-collection">
        <header className="home-section-heading">
          <div><span className="home-overline">UNA CASA, MUCHAS POSIBILIDADES</span><h2>Diseños reales para inspirar tu proyecto.</h2></div>
          <Button variant="secondary" onClick={() => navigate('/catalogo')}>Ver catálogo completo</Button>
        </header>
        {!catalogAvailable && <p className="home-catalog-notice">El catálogo está temporalmente fuera de línea. Aún puedes iniciar una cotización.</p>}
        <div className="home-product-grid">
          {featured.map((product) => <article className="home-product-card" key={product.id}>
            <button onClick={() => navigate(`/producto/${product.slug}`)} aria-label={`Ver ${product.name}`}>
              <img
                src={product.primaryImage!.secureUrl}
                alt={product.primaryImage!.altText || product.name}
                loading="lazy"
              />
              <span className="home-product-shade" />
              <span className="home-product-copy"><small>{product.category}</small><b>{product.name}</b><em>{moneyMinor(product.basePriceMinor)}</em></span>
            </button>
          </article>)}
          {featured.length === 0 && catalogAvailable && Array.from({ length: 4 }, (_, index) => (
            <div className="home-product-skeleton" key={index} aria-hidden="true" />
          ))}
        </div>
      </section>

      <section className="home-process" id="como-funciona">
        <div className="home-process-intro">
          <span className="home-overline">DEL DISEÑO AL TALLER</span>
          <h2>Un proceso claro, sin perderte en el camino.</h2>
          <p>La web conecta el catálogo, la cotización y el seguimiento de tu pedido en un mismo lugar.</p>
          <Button onClick={() => navigate('/cotizador')}>Empezar ahora</Button>
        </div>
        <div className="home-process-list">
          <article><span>Explora</span><h3>Encuentra un punto de partida</h3><p>Compara modelos y precios base publicados en el catálogo.</p></article>
          <article><span>Personaliza</span><h3>Adapta medidas y acabados</h3><p>Configura el mueble para tu ambiente y conoce la estimación.</p></article>
          <article><span>Da seguimiento</span><h3>Consulta el avance del taller</h3><p>Revisa cotizaciones, pedidos, pagos y etapas desde tu cuenta.</p></article>
        </div>
      </section>

      <section className="home-final-cta">
        {ctaProduct?.primaryImage && <img src={ctaProduct.primaryImage.secureUrl} alt="" aria-hidden="true" loading="lazy" />}
        <div className="home-final-overlay" />
        <div className="home-final-copy"><span className="home-overline">TU PROYECTO EMPIEZA AQUÍ</span><h2>Convierte una idea en una cotización concreta.</h2><p>Elige un diseño, ingresa las medidas de tu espacio y personaliza los detalles.</p><Button onClick={() => navigate('/cotizador')}>Cotizar mi mueble</Button></div>
      </section>
    </main>
    <Footer />
  </>;
}
