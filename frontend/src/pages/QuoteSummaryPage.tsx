import { useState } from 'react';

import type { QuoteData } from '../api/modules/quotes';
import { Footer, Navbar, navigate } from '../components/layout';
import { Button, Modal } from '../components/ui';
import { moneyMinor } from '../utils/format';

export function QuoteSummaryPage({ quote }: { quote: QuoteData | null }) {
  const [modal, setModal] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!quote || !quote.items[0]) {
    return (
      <>
        <Navbar />
        <main className="summary-page">
          <div className="empty">
            <b>Aún no has enviado una cotización.</b>
            <p>Configura tu mueble para obtener un precio referencial.</p>
            <Button onClick={() => navigate('/cotizador')}>Empezar cotización</Button>
          </div>
        </main>
        <Footer />
      </>
    );
  }

  const item = quote.items[0];
  const expiry = new Intl.DateTimeFormat('es-PE', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  }).format(new Date(quote.expiresAt));
  const message = `Hola, envié una cotización en Mueblería Iván.\n\nProyecto: ${item.productName}\nMedidas: ${item.widthMm / 10} x ${item.heightMm / 10} x ${item.depthMm / 10} cm\nMaterial: ${item.material?.name ?? 'Por definir'}\nAcabado: ${item.finish?.name ?? 'Por definir'}\nPrecio referencial: ${moneyMinor(quote.totalMinor)}\n\nCódigo de cotización: ${quote.code}\n\nQuisiera recibir más información.`;
  const copy = async () => {
    await navigator.clipboard?.writeText(message);
    setCopied(true);
  };

  return (
    <>
      <Navbar />
      <main className="summary-page">
        <div className="summary-success">
          <span>✓</span>
          <div>
            <p>COTIZACIÓN ENVIADA</p>
            <h1>¡Tu proyecto está tomando forma!</h1>
            <small>{quote.code} · Válida hasta el {expiry}</small>
          </div>
        </div>
        <div className="summary-layout">
          <section className="summary-card">
            <h2>Resumen de tu proyecto</h2>
            <div className="summary-project">
              <div className="mini-project">⌂</div>
              <div>
                <span className="eyebrow">{item.productName}</span>
                <h3>Proyecto personalizado</h3>
                <p>{item.widthMm / 10} × {item.heightMm / 10} × {item.depthMm / 10} cm</p>
              </div>
            </div>
            <dl className="summary-details">
              <div><dt>Material</dt><dd>{item.material?.name ?? 'Por definir'}</dd></div>
              <div><dt>Color / acabado</dt><dd>{item.finish?.name ?? 'Por definir'}</dd></div>
              <div>
                <dt>Accesorios</dt>
                <dd>{item.accessories.length ? item.accessories.map((option) => option.name).join(', ') : 'Sin accesorios adicionales'}</dd>
              </div>
              <div><dt>Contacto</dt><dd>{quote.contactEmail ?? quote.contactPhone}</dd></div>
            </dl>
            <Button variant="secondary" onClick={() => navigate('/cotizador')}>
              ← Crear otra cotización
            </Button>
          </section>
          <aside className="quote-total-card">
            <span className="estimate-label">PRECIO REFERENCIAL</span>
            <strong>{moneyMinor(quote.totalMinor)}</strong>
            <div className="split-payment">
              <div>
                <span>50%</span>
                <p>Anticipo para iniciar</p>
                <b>{moneyMinor(quote.depositMinor)}</b>
              </div>
              <div>
                <span>50%</span>
                <p>Saldo contra entrega</p>
                <b>{moneyMinor(quote.totalMinor - quote.depositMinor)}</b>
              </div>
            </div>
            <p className="estimate-note">
              El precio se confirma luego de validar tus medidas y requerimientos.
            </p>
            <Button onClick={() => setModal(true)}>Enviar por WhatsApp</Button>
          </aside>
        </div>
      </main>
      <Modal open={modal} onClose={() => setModal(false)} title="Mensaje para WhatsApp">
        <p className="modal-description">
          Copia este mensaje y envíalo a Mueblería Iván por WhatsApp.
        </p>
        <textarea className="message-box" value={message} readOnly aria-label="Mensaje generado" />
        <div className="modal-actions">
          <Button variant="secondary" onClick={() => setModal(false)}>Cerrar</Button>
          <Button onClick={copy}>{copied ? '✓ Mensaje copiado' : 'Copiar mensaje'}</Button>
        </div>
      </Modal>
      <Footer />
    </>
  );
}
