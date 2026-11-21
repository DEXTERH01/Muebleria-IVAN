import { useEffect, useMemo, useState, type FormEvent } from 'react';

import {
  getProduct,
  listProducts,
  type CatalogOption,
  type ProductDetail,
  type ProductSummary,
} from '../api/modules/catalog';
import {
  createQuote,
  estimateQuote,
  type EstimateItemInput,
  type QuoteData,
  type QuoteEstimate,
} from '../api/modules/quotes';
import { Footer, Navbar, navigate } from '../components/layout';
import { Button } from '../components/ui';
import { moneyMinor } from '../utils/format';

type Measure = 'width' | 'height' | 'depth';

function adjustmentLabel(option: CatalogOption): string {
  const parts: string[] = [];
  if (option.priceAdjustmentMinor) parts.push(moneyMinor(option.priceAdjustmentMinor));
  if (Number(option.priceAdjustmentPercent)) parts.push(`${option.priceAdjustmentPercent}%`);
  return parts.length ? `+ ${parts.join(' + ')}` : 'Incluido';
}

function finishColor(code: string): string {
  const colors: Record<string, string> = {
    NATURAL: '#d9c098',
    NOGAL: '#604132',
    BLANCO: '#f1eee7',
  };
  return colors[code] ?? '#9d704d';
}

export function QuotePage({
  onComplete,
  initialType,
}: {
  onComplete: (quote: QuoteData) => void;
  initialType?: string;
}) {
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [productSlug, setProductSlug] = useState(initialType ?? '');
  const [measure, setMeasure] = useState({ width: 0, height: 0, depth: 0 });
  const [materialId, setMaterialId] = useState('');
  const [finishId, setFinishId] = useState('');
  const [accessoryIds, setAccessoryIds] = useState<string[]>([]);
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [estimate, setEstimate] = useState<QuoteEstimate | null>(null);
  const [loading, setLoading] = useState(true);
  const [estimating, setEstimating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    listProducts()
      .then((response) => {
        if (!active) return;
        setProducts(response.items);
        if (response.items.length === 0) {
          setError('No hay productos disponibles para cotizar en este momento.');
          setLoading(false);
          return;
        }
        const requested = response.items.find((item) => item.slug === initialType);
        setProductSlug(requested?.slug ?? response.items[0]?.slug ?? '');
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : 'No pudimos cargar los productos.');
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [initialType]);

  useEffect(() => {
    if (!productSlug) return;
    let active = true;
    setLoading(true);
    setError(null);
    getProduct(productSlug)
      .then((value) => {
        if (!active) return;
        setProduct(value);
        setMeasure({
          width: value.measurementLimits.minWidthMm / 10,
          height: value.measurementLimits.minHeightMm / 10,
          depth: value.measurementLimits.minDepthMm / 10,
        });
        setMaterialId(value.materials.find((option) => option.isDefault)?.id ?? '');
        setFinishId(value.finishes.find((option) => option.isDefault)?.id ?? '');
        setAccessoryIds([]);
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
  }, [productSlug]);

  const item = useMemo<EstimateItemInput | null>(() => {
    if (!product || measure.width <= 0 || measure.height <= 0 || measure.depth <= 0) return null;
    return {
      productId: product.id,
      quantity: 1,
      widthMm: Math.round(measure.width * 10),
      heightMm: Math.round(measure.height * 10),
      depthMm: Math.round(measure.depth * 10),
      ...(materialId ? { materialId } : {}),
      ...(finishId ? { finishId } : {}),
      accessoryIds,
      configuration: {},
    };
  }, [accessoryIds, finishId, materialId, measure, product]);

  useEffect(() => {
    if (!item) return;
    let active = true;
    const timer = window.setTimeout(() => {
      setEstimating(true);
      setError(null);
      estimateQuote([item])
        .then((value) => {
          if (active) setEstimate(value);
        })
        .catch((reason: unknown) => {
          if (active) {
            setEstimate(null);
            setError(reason instanceof Error ? reason.message : 'No pudimos calcular la estimación.');
          }
        })
        .finally(() => {
          if (active) setEstimating(false);
        });
    }, 250);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [item]);

  const toggleAccessory = (id: string) => {
    setAccessoryIds((current) => (
      current.includes(id) ? current.filter((itemId) => itemId !== id) : [...current, id]
    ));
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!item || !estimate) return;
    if (!contactEmail.trim() && !contactPhone.trim()) {
      setError('Escribe un correo o teléfono para que podamos contactarte.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const quote = await createQuote({
        contactName: contactName.trim(),
        ...(contactEmail.trim() ? { contactEmail: contactEmail.trim() } : {}),
        ...(contactPhone.trim() ? { contactPhone: contactPhone.trim() } : {}),
        items: [item],
      });
      onComplete(quote);
      navigate('/cotizacion');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No pudimos guardar la cotización.');
    } finally {
      setSubmitting(false);
    }
  };

  const calculated = estimate?.items[0];
  const limits = product?.measurementLimits;

  return (
    <>
      <Navbar />
      <main className="quote-page">
        <div className="quote-heading">
          <span className="kicker">COTIZADOR PERSONALIZADO</span>
          <h1>Cuéntanos sobre<br />tu proyecto.</h1>
          <p>Completa los detalles y recibe una estimación calculada por nuestro backend.</p>
        </div>
        {loading && <div className="empty" role="status">Preparando el cotizador…</div>}
        {!loading && product && (
          <div className="quote-layout">
            <form id="quote-form" className="quote-form" onSubmit={submit}>
              <fieldset>
                <legend><span>1</span> Modelo de referencia</legend>
                <div className="choice-grid">
                  {products.map((itemProduct) => (
                    <label
                      className={productSlug === itemProduct.slug ? 'choice selected' : 'choice'}
                      key={itemProduct.id}
                    >
                      <input
                        type="radio"
                        checked={productSlug === itemProduct.slug}
                        onChange={() => setProductSlug(itemProduct.slug)}
                        name="product"
                      />
                      <span>{itemProduct.name}</span>
                    </label>
                  ))}
                </div>
              </fieldset>
              <fieldset>
                <legend><span>2</span> Medidas <small>en centímetros</small></legend>
                <div className="measure-grid">
                  {([
                    ['width', 'Ancho', limits?.minWidthMm, limits?.maxWidthMm],
                    ['height', 'Alto', limits?.minHeightMm, limits?.maxHeightMm],
                    ['depth', 'Profundidad', limits?.minDepthMm, limits?.maxDepthMm],
                  ] as const).map(([key, label, minimum, maximum]) => (
                    <label key={key}>
                      {label}
                      <div className="measure-input">
                        <input
                          type="number"
                          min={(minimum ?? 1) / 10}
                          max={(maximum ?? 10000) / 10}
                          value={measure[key as Measure]}
                          onChange={(event) => setMeasure({
                            ...measure,
                            [key]: Number(event.target.value),
                          })}
                          required
                        />
                        <span>cm</span>
                      </div>
                    </label>
                  ))}
                </div>
              </fieldset>
              <fieldset>
                <legend><span>3</span> Material</legend>
                <div className="choice-grid three">
                  {product.materials.map((option) => (
                    <label className={materialId === option.id ? 'choice selected' : 'choice'} key={option.id}>
                      <input
                        type="radio"
                        checked={materialId === option.id}
                        onChange={() => setMaterialId(option.id)}
                        name="material"
                      />
                      <span>{option.name}<small>{adjustmentLabel(option)}</small></span>
                    </label>
                  ))}
                </div>
              </fieldset>
              <fieldset>
                <legend><span>4</span> Acabado o color</legend>
                <div className="swatches">
                  {product.finishes.map((option) => (
                    <button
                      type="button"
                      onClick={() => setFinishId(option.id)}
                      className={finishId === option.id ? 'selected' : ''}
                      key={option.id}
                    >
                      <i style={{ backgroundColor: finishColor(option.code) }} />
                      <span>{option.name}</span>
                    </button>
                  ))}
                </div>
              </fieldset>
              <fieldset>
                <legend><span>5</span> Accesorios <small>opcionales</small></legend>
                <div className="accessories">
                  {product.accessories.map((option) => (
                    <label key={option.id}>
                      <input
                        type="checkbox"
                        checked={accessoryIds.includes(option.id)}
                        onChange={() => toggleAccessory(option.id)}
                      />
                      <span>{option.name}</span>
                      <b>{adjustmentLabel(option)}</b>
                    </label>
                  ))}
                </div>
              </fieldset>
              <fieldset>
                <legend><span>6</span> Datos de contacto</legend>
                <div className="contact-grid">
                  <label>
                    Nombre
                    <input
                      value={contactName}
                      onChange={(event) => setContactName(event.target.value)}
                      minLength={2}
                      maxLength={160}
                      autoComplete="name"
                      required
                    />
                  </label>
                  <label>
                    Correo
                    <input
                      type="email"
                      value={contactEmail}
                      onChange={(event) => setContactEmail(event.target.value)}
                      autoComplete="email"
                      placeholder="nombre@correo.com"
                    />
                  </label>
                  <label>
                    Teléfono
                    <input
                      type="tel"
                      value={contactPhone}
                      onChange={(event) => setContactPhone(event.target.value)}
                      minLength={6}
                      maxLength={40}
                      autoComplete="tel"
                    />
                  </label>
                </div>
                <small className="contact-help">Ingresa al menos un correo o teléfono.</small>
              </fieldset>
              {error && <p className="form-error" role="alert">{error}</p>}
              <Button
                type="submit"
                className="quote-mobile-submit"
                disabled={!estimate || estimating || submitting}
              >
                {submitting ? 'Guardando…' : 'Enviar cotización →'}
              </Button>
            </form>
            <aside className="estimate" aria-live="polite">
              <span className="estimate-label">COTIZACIÓN REFERENCIAL</span>
              <h2>Tu estimación</h2>
              {estimating && <p>Actualizando cálculo…</p>}
              {calculated && estimate && (
                <>
                  <div className="estimate-lines">
                    <p><span>Precio por medidas</span><b>{moneyMinor(calculated.breakdown.sizeAdjustedBaseMinor)}</b></p>
                    <p><span>Material y acabado</span><b>{moneyMinor(calculated.breakdown.materialMinor + calculated.breakdown.finishMinor)}</b></p>
                    <p><span>Accesorios</span><b>{moneyMinor(calculated.breakdown.accessoriesMinor)}</b></p>
                    <p><span>Reglas comerciales</span><b>{moneyMinor(calculated.breakdown.rulesMinor)}</b></p>
                  </div>
                  <div className="estimate-total">
                    <span>Precio estimado</span>
                    <strong>{moneyMinor(estimate.totalMinor)}</strong>
                  </div>
                  <div className="estimate-payment">
                    <p><span>Anticipo para iniciar</span><b>{moneyMinor(estimate.depositMinor)}</b></p>
                    <p><span>Saldo contra entrega</span><b>{moneyMinor(estimate.totalMinor - estimate.depositMinor)}</b></p>
                  </div>
                  <p className="estimate-note">
                    ✦ Fabricación estimada entre {calculated.minProductionDays} y {calculated.maxProductionDays} días.
                  </p>
                </>
              )}
              <Button
                onClick={() => document.querySelector<HTMLFormElement>('#quote-form')?.requestSubmit()}
                disabled={!estimate || estimating || submitting}
              >
                {submitting ? 'Guardando…' : 'Enviar cotización →'}
              </Button>
            </aside>
          </div>
        )}
        {!loading && !product && error && (
          <div className="empty" role="alert"><b>{error}</b></div>
        )}
      </main>
      <Footer />
    </>
  );
}
