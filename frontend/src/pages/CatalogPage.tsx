import { useEffect, useMemo, useState } from 'react';

import { listProducts, type ProductSummary } from '../api/modules/catalog';
import { ProductCard } from '../components/catalog';
import { Footer, Navbar } from '../components/layout';
import { Button, Pagination } from '../components/ui';
import { usePagination } from '../hooks/usePagination';

const CATALOG_PAGE_SIZE = 12;

export function CatalogPage() {
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [category, setCategory] = useState('Todos');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    listProducts()
      .then((response) => {
        if (active) setProducts(response.items);
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : 'No pudimos cargar el catálogo.');
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [retry]);

  const categories = useMemo(
    () => ['Todos', ...new Set(products.map((product) => product.category))],
    [products],
  );
  const filtered = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase('es');
    return products.filter((product) => (
      (category === 'Todos' || product.category === category)
      && `${product.name} ${product.description}`.toLocaleLowerCase('es').includes(needle)
    ));
  }, [category, products, query]);
  const { page, pageItems, setPage, totalPages } = usePagination(filtered, CATALOG_PAGE_SIZE);

  return (
    <>
      <Navbar />
      <main className="catalog-page">
        <div className="page-banner">
          <span className="kicker">CATÁLOGO</span>
          <h1>Muebles que se adaptan<br />a tu forma de vivir.</h1>
          <p>Explora algunos de nuestros diseños. Cada proyecto puede personalizarse para ti.</p>
        </div>
        <div className="catalog-tools">
          <div className="filters" role="tablist" aria-label="Categorías">
            {categories.map((item) => (
              <button
                key={item}
                role="tab"
                aria-selected={category === item}
                onClick={() => {
                  setCategory(item);
                  setPage(1);
                }}
                className={category === item ? 'selected' : ''}
              >
                {item}
              </button>
            ))}
          </div>
          <label className="search">
            <span>⌕</span>
            <input
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(1);
              }}
              placeholder="Buscar muebles..."
              aria-label="Buscar muebles"
            />
          </label>
        </div>
        {loading && <div className="empty" role="status">Cargando catálogo…</div>}
        {error && (
          <div className="empty" role="alert">
            <b>{error}</b>
            <p>Verifica que la API esté disponible y vuelve a intentarlo.</p>
            <Button onClick={() => setRetry((value) => value + 1)}>Reintentar</Button>
          </div>
        )}
        {!loading && !error && (
          <>
            <p className="results">
              {filtered.length} {filtered.length === 1 ? 'diseño encontrado' : 'diseños encontrados'}
            </p>
            <div className="product-grid">
              {pageItems.map((product) => <ProductCard product={product} key={product.id} />)}
            </div>
            <Pagination
              page={page}
              totalPages={totalPages}
              totalItems={filtered.length}
              onPageChange={setPage}
              label="diseños"
            />
            {filtered.length === 0 && (
              <div className="empty">
                <b>No encontramos ese diseño.</b>
                <p>Prueba con otra búsqueda o explora todas las categorías.</p>
              </div>
            )}
          </>
        )}
      </main>
      <Footer />
    </>
  );
}
