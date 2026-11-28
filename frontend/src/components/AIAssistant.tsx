import { useEffect, useRef, useState } from 'react';

import { listProducts, type ProductSummary } from '../api/modules/catalog';
import { useAuth } from '../auth/AuthProvider';
import type { Order } from '../types';
import { money, orderStatusLabel, paymentStatusLabel } from '../utils/format';

interface ChatMessage {
  id: number;
  role: 'assistant' | 'user';
  text: string;
  action?: { label: string; path: string };
}

const suggestions = ['Quiero un ropero', '¿Cuánto cuesta?', 'Consultar mi pedido', 'Cómo cotizo'];
const normalize = (text: string) => text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
const containsAny = (text: string, terms: string[]) => terms.some((term) => text.includes(term));
const catalogTerms = [
  'ropero', 'closet', 'armario', 'comoda', 'dormitorio', 'cocina', 'repostero', 'escritorio',
  'oficina', 'televisor', 'television', 'centro tv', 'comedor', 'mesa', 'zapatera', 'zapatos',
  'mueble', 'catalogo', 'modelos', 'disenos', 'precio', 'cuesta', 'costo', 'vale', 'cotiz',
  'presupuesto', 'comprar', 'busco', 'buscar',
];

function findProduct(text: string, products: ProductSummary[]): ProductSummary | undefined {
  const exact = products.find((product) => normalize(`${product.name} ${product.slug}`)
    .split(' ')
    .some((word) => word.length > 3 && text.includes(word)));
  if (exact) return exact;

  const categoryTerms = [
    { terms: ['closet', 'ropero', 'armario'], matches: ['dormitorio', 'ropero', 'closet'] },
    { terms: ['cocina', 'repostero'], matches: ['cocina', 'repostero'] },
    { terms: ['escritorio', 'oficina'], matches: ['escritorio', 'oficina'] },
    { terms: ['televisor', 'television', 'tv', 'sala'], matches: ['centro tv', 'entretenimiento', 'sala'] },
    { terms: ['comedor', 'mesa'], matches: ['comedor', 'mesa'] },
    { terms: ['zapato', 'zapatera'], matches: ['zapatera', 'zapatos'] },
  ];
  const category = categoryTerms.find(({ terms }) => containsAny(text, terms));
  if (!category) return undefined;
  return products.find((product) => containsAny(
    normalize(`${product.name} ${product.category} ${product.slug}`),
    category.matches,
  ));
}

function orderReply(
  input: string,
  orders: Order[],
  authenticated: boolean,
): Omit<ChatMessage, 'id' | 'role'> | null {
  const code = input.toUpperCase().match(/PED(?:-DEMO)?-\d{4}(?:-\d{4})?|PED-\d{3,}/)?.[0];
  const normalized = normalize(input);
  const namedOrder = orders.find((order) => normalized.includes(normalize(order.customerName)));
  if (!code && !namedOrder) return null;

  const order = namedOrder ?? orders.find((item) => item.id.toUpperCase() === code);
  if (!order) {
    return authenticated
      ? { text: `No encuentro ${code ?? 'ese pedido'} entre los pedidos disponibles en tu cuenta. Revisa el código o entra a Mi cuenta para ver tu historial.`, action: { label: 'Ir a mi cuenta', path: '/mi-cuenta' } }
      : { text: 'Para proteger la información de cada cliente, inicia sesión con la cuenta asociada al pedido y podré mostrarte el seguimiento.', action: { label: 'Iniciar sesión', path: '/iniciar-sesion' } };
  }

  const delivery = order.deliveryDate
    ? new Intl.DateTimeFormat('es-PE', { day: '2-digit', month: 'long', year: 'numeric' })
      .format(new Date(`${order.deliveryDate}T12:00:00`))
    : 'por coordinar';
  return {
    text: `${order.code}: estado ${orderStatusLabel[order.status]}; entrega ${delivery}; pago ${paymentStatusLabel[order.paymentStatus]}; saldo ${money(order.remainingBalance)}.`,
    action: { label: 'Ver mi cuenta', path: '/mi-cuenta' },
  };
}

function smartReply(
  input: string,
  orders: Order[],
  products: ProductSummary[],
  authenticated: boolean,
): Omit<ChatMessage, 'id' | 'role'> {
  const text = normalize(input);
  const status = orderReply(input, orders, authenticated);
  if (status) return status;

  const product = findProduct(text, products);
  if (product) {
    const price = `El precio base publicado de ${product.name} es ${money(product.basePriceMinor / 100)}. La cotización final depende de las medidas y opciones que elijas.`;
    const asksQuote = containsAny(text, ['cotiz', 'presupuesto', 'precio', 'cuanto', 'costo', 'vale', 'comprar']);
    return {
      text: `${price} ${product.description}`,
      action: asksQuote
        ? { label: `Cotizar ${product.name}`, path: `/cotizador?producto=${encodeURIComponent(product.slug)}` }
        : { label: `Ver ${product.name}`, path: `/producto/${encodeURIComponent(product.slug)}` },
    };
  }

  if (containsAny(text, ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'hey'])) {
    return { text: '¡Hola! Puedo ayudarte a encontrar un diseño del catálogo, revisar su precio base, iniciar una cotización o consultar el seguimiento de un pedido de tu cuenta.' };
  }
  if (containsAny(text, ['gracias', 'muchas gracias'])) {
    return { text: '¡Con gusto! Si me dices qué mueble buscas, te muestro opciones disponibles en el catálogo.' };
  }
  if (containsAny(text, ['cotiz', 'presupuesto', 'calcular', 'precio', 'costo', 'vale', 'comprar'])) {
    if (!products.length) {
      return { text: 'Ahora no puedo consultar los diseños ni sus precios. Abre el catálogo para volver a intentarlo; si ya sabes qué mueble buscas, escríbemelo y te indico cómo cotizarlo.', action: { label: 'Abrir catálogo', path: '/catalogo' } };
    }
    return { text: 'Puedo ayudarte. Elige un producto del catálogo y luego introduce ancho, alto, profundidad y acabados. El cotizador calcula el importe con los precios configurados.', action: { label: 'Abrir cotizador', path: '/cotizador' } };
  }
  if (containsAny(text, ['pago', 'yape', 'plin', 'transferencia', 'efectivo', 'anticipo', 'saldo'])) {
    return { text: 'En el detalle de cada cotización verás el anticipo calculado. Cuando la cotización se convierte en pedido, puedes consultar pagos y saldo en Mi cuenta.' };
  }
  if (containsAny(text, ['demora', 'tiempo', 'entrega', 'dias', 'cuando'])) {
    return { text: 'El plazo depende del modelo y la configuración. La fecha se confirma al coordinar el pedido; luego puedes revisar las etapas desde Mi cuenta.' };
  }
  if (containsAny(text, ['pedido', 'estado', 'seguimiento', 'ped-'])) {
    return authenticated
      ? { text: 'Puedo buscar pedidos asociados a tu sesión. Escríbeme el código completo que aparece en Mi cuenta, por ejemplo PED-DEMO-2026-0001.' }
      : { text: 'El seguimiento es privado. Inicia sesión con la cuenta del cliente y luego escribe el código completo del pedido.', action: { label: 'Iniciar sesión', path: '/iniciar-sesion' } };
  }
  if (containsAny(text, ['medida', 'medir', 'ancho', 'alto', 'profundidad'])) {
    return { text: 'Mide el ancho, alto y profundidad en centímetros. Toma cada medida en dos puntos y usa la menor si hay desniveles. El cotizador te pedirá esas medidas para el modelo elegido.', action: { label: 'Ver catálogo', path: '/catalogo' } };
  }
  if (containsAny(text, ['catalogo', 'modelos', 'disenos', 'muebles'])) {
    const count = products.length;
    return { text: count ? `El catálogo tiene ${count} diseños publicados con precio base e imágenes. Dime qué ambiente buscas y te sugiero uno.` : 'El catálogo no está respondiendo en este momento. Puedes volver a intentarlo desde la página de catálogo.', action: { label: 'Abrir catálogo', path: '/catalogo' } };
  }
  if (!products.length) {
    return { text: 'No puedo cargar el catálogo ahora. Prueba de nuevo en unos momentos o abre la página de catálogo.' , action: { label: 'Abrir catálogo', path: '/catalogo' } };
  }
  return { text: 'Puedo buscar diseños, consultar precios base, iniciar cotizaciones y explicar el seguimiento. Prueba con “ropero”, “mesa de comedor” o “cotizar escritorio”.' };
}

export function AIAssistant({ orders }: { orders: Order[] }) {
  const auth = useAuth();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [catalogError, setCatalogError] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: 1, role: 'assistant', text: '¡Hola! Soy Mía. Dime qué mueble buscas o qué necesitas consultar.' },
  ]);
  const endRef = useRef<HTMLDivElement>(null);
  const nextMessageId = useRef(2);
  const catalogRequest = useRef<Promise<ProductSummary[]> | null>(null);

  const loadCatalog = () => {
    if (!catalogRequest.current) {
      const request = listProducts().then((response) => response.items);
      catalogRequest.current = request;
      void request.then(
        () => { if (catalogRequest.current === request) catalogRequest.current = null; },
        () => { if (catalogRequest.current === request) catalogRequest.current = null; },
      );
    }
    return catalogRequest.current.then((items) => {
      setProducts(items);
      setCatalogError(false);
      return items;
    }).catch((error: unknown) => {
      setCatalogError(true);
      throw error;
    });
  };

  useEffect(() => {
    void loadCatalog().catch(() => {});
  }, []);

  useEffect(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages]);

  const send = async (raw: string) => {
    const text = raw.trim();
    if (!text || thinking) return;
    const userMessageId = nextMessageId.current++;
    const assistantMessageId = nextMessageId.current++;
    const userMessage: ChatMessage = { id: userMessageId, role: 'user', text };
    const usesCatalog = containsAny(normalize(text), catalogTerms);
    setInput('');

    if (!usesCatalog) {
      let response: Omit<ChatMessage, 'id' | 'role'>;
      try {
        response = smartReply(text, orders, products, Boolean(auth?.session));
      } catch {
        response = {
          text: 'No pude procesar esa consulta. Inténtalo otra vez o abre el catálogo para encontrar un diseño.',
          action: { label: 'Abrir catálogo', path: '/catalogo' },
        };
      }
      setMessages((current) => [...current, userMessage, { id: assistantMessageId, role: 'assistant', ...response }]);
      return;
    }

    setMessages((current) => [...current, userMessage]);
    setThinking(true);
    let currentProducts = products;
    try {
      currentProducts = await loadCatalog();
    } catch {
      // Keep the last successful catalog so Mía can still answer from cached data.
    }
    let response: Omit<ChatMessage, 'id' | 'role'>;
    try {
      response = smartReply(text, orders, currentProducts, Boolean(auth?.session));
    } catch {
      response = {
        text: 'No pude procesar esa consulta. Inténtalo otra vez o abre el catálogo para encontrar un diseño.',
        action: { label: 'Abrir catálogo', path: '/catalogo' },
      };
    }
    setMessages((current) => [...current, { id: assistantMessageId, role: 'assistant', ...response }]);
    setThinking(false);
  };

  return <div className="ai-assistant">
    {open && <section className="ai-chat" aria-label="Asistente virtual Mía">
      <header>
        <div className="ai-avatar">M</div>
        <div><strong>Mía · Asistente de compras</strong><span><i /> {catalogError ? 'Catálogo sin conexión' : 'Lista para ayudarte'}</span></div>
        <button type="button" onClick={() => setOpen(false)} aria-label="Cerrar asistente">×</button>
      </header>
      <div className="ai-chat-caption">Respuestas basadas en el catálogo publicado y los pedidos de tu sesión.</div>
      <div className="ai-messages" aria-live="polite">
        {messages.map((message) => <div className={`ai-message ${message.role}`} key={message.id}>
          <p>{message.text}</p>
          {message.action && <a href={message.action.path}>{message.action.label}</a>}
        </div>)}
        {thinking && <div className="ai-message assistant" role="status"><p>Consultando el catálogo publicado…</p></div>}
        <div ref={endRef}/>
      </div>
      <div className="ai-suggestions">{suggestions.map((item) => <button type="button" key={item} onClick={() => void send(item)} disabled={thinking}>{item}</button>)}</div>
      <form onSubmit={(event) => { event.preventDefault(); send(input); }}>
        <input aria-label="Escribe tu consulta" value={input} onChange={(event) => setInput(event.target.value)} placeholder="Escribe tu consulta…" />
        <button type="submit" aria-label="Enviar mensaje" disabled={!input.trim() || thinking}>↑</button>
      </form>
    </section>}
    <button className="ai-launcher" onClick={() => setOpen((value) => !value)} aria-label={open ? 'Cerrar asistente virtual' : 'Abrir asistente virtual'}>
      {open ? '×' : <><span>✦</span><i /></>}
    </button>
  </div>;
}
