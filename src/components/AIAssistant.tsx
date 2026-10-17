import { useEffect, useRef, useState } from 'react';
import { navigate } from './layout';
import { money, orderStatusLabel, paymentStatusLabel } from '../utils/format';
import type { Order } from '../types';

interface ChatMessage {
  id: number;
  role: 'assistant' | 'user';
  text: string;
  action?: { label: string; path: string };
}

const suggestions = ['Cotizar un closet', 'Consultar PED-001', 'Formas de pago', 'Tiempo de entrega'];

const containsAny = (text: string, terms: string[]) => terms.some((term) => text.includes(term));

function orderReply(text: string, orders: Order[]): Omit<ChatMessage, 'id' | 'role'> | null {
  const code = text.toUpperCase().match(/PED-\d{3}/)?.[0];
  const namedOrder = orders.find((item) => text.includes(item.customerName.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')));
  if (!code && !namedOrder) return null;
  const order = namedOrder ?? orders.find((item) => item.id === code);
  if (!order) return { text: `No encontré el pedido ${code}. Verifica el código o comunícate con nosotros por WhatsApp.` };
  return {
    text: `${order.id} corresponde a ${order.productType}. Estado: ${orderStatusLabel[order.status]}. Entrega: ${new Intl.DateTimeFormat('es-PE', { day: '2-digit', month: 'long', year: 'numeric' }).format(new Date(`${order.deliveryDate}T12:00:00`))}. Estado de pago: ${paymentStatusLabel[order.paymentStatus]}. Saldo: ${money(order.remainingBalance)}.`,
    action: { label: 'Ver detalle del pedido', path: `/admin/pedido/${order.id}` },
  };
}

function smartReply(input: string, orders: Order[]): Omit<ChatMessage, 'id' | 'role'> {
  const text = input.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  const orderResponse = orderReply(text, orders);
  if (orderResponse) return orderResponse;
  if (containsAny(text, ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'hey'])) {
    return { text: '¡Hola! Soy Mía. Puedo ayudarte a elegir un diseño, comparar materiales, calcular una cotización o consultar el avance de tu pedido. ¿Qué necesitas hoy?' };
  }
  if (containsAny(text, ['gracias', 'muchas gracias'])) {
    return { text: '¡Con gusto! Cuando quieras podemos continuar con tu proyecto. Estoy aquí para ayudarte.' };
  }
  if (containsAny(text, ['closet', 'ropero'])) {
    return { text: 'Para un closet recomiendo medir ancho, alto y profundidad del espacio. Puedes elegir distribución interior, cajones, barras, iluminación y tipo de puertas. El Closet Siena es una excelente referencia.', action: { label: 'Cotizar un closet', path: '/cotizador?producto=closet-siena' } };
  }
  if (containsAny(text, ['cocina', 'repostero'])) {
    return { text: 'Diseñamos cocinas según el espacio disponible, ubicación de electrodomésticos y necesidades de almacenamiento. La cotización considera módulos, material, herrajes y accesorios.', action: { label: 'Ver cocinas', path: '/catalogo' } };
  }
  if (containsAny(text, ['escritorio', 'oficina'])) {
    return { text: 'Podemos adaptar escritorios para estudio, trabajo o espacios compactos. Indica el ancho disponible y si necesitas cajones, repisas o pasacables.', action: { label: 'Explorar escritorios', path: '/catalogo' } };
  }
  if (containsAny(text, ['television', 'tv', 'sala'])) {
    return { text: 'Los muebles de TV pueden incluir panel, cajones, puertas y canaletas para ocultar cables. Te recomiendo definir primero el ancho del televisor y la pared disponible.', action: { label: 'Ver muebles de sala', path: '/catalogo' } };
  }
  if (containsAny(text, ['cotiz', 'presupuesto', 'calcular'])) {
    return { text: '¡Claro! Para calcular tu proyecto necesito el tipo de mueble, medidas, material, acabado y accesorios. Obtendrás el total estimado y la distribución de pago 50/50.', action: { label: 'Empezar cotización', path: '/cotizador' } };
  }
  if (containsAny(text, ['material', 'melamina', 'mdf'])) {
    return { text: 'Para uso diario recomiendo melamina de 18 mm. La melamina premium ofrece mejores acabados; el MDF es ideal cuando buscas superficies pintadas o detalles especiales.' };
  }
  if (containsAny(text, ['color', 'acabado', 'roble', 'nogal', 'blanco', 'gris', 'negro', 'natural'])) {
    return { text: 'Tenemos acabados Roble, Nogal, Blanco, Gris, Negro y Natural. Roble aporta calidez, Blanco amplía visualmente el ambiente y Nogal ofrece un estilo más elegante.' };
  }
  if (containsAny(text, ['medida', 'medir', 'ancho', 'alto', 'profundidad'])) {
    return { text: 'Mide el ancho, alto y profundidad en centímetros. Toma cada medida en dos puntos y usa la menor para evitar desniveles. Para proyectos empotrados recomendamos una validación final en el domicilio.' };
  }
  if (containsAny(text, ['accesorio', 'corredera', 'bisagra', 'tirador', 'led', 'organizador'])) {
    return { text: 'Puedes agregar correderas telescópicas, bisagras de cierre suave, tiradores premium, iluminación LED y organizadores interiores. El cotizador suma cada opción automáticamente.' };
  }
  if (containsAny(text, ['precio', 'cuanto', 'costo', 'vale'])) {
    return { text: 'El precio depende de medidas, material y accesorios. Nuestro cotizador genera una referencia y separa automáticamente el 50% de anticipo y el 50% contra entrega.', action: { label: 'Calcular precio', path: '/cotizador' } };
  }
  if (containsAny(text, ['pago', 'yape', 'plin', 'transferencia', 'efectivo', 'anticipo', 'saldo'])) {
    return { text: 'Trabajamos con el esquema 50/50: 50% de anticipo para iniciar la fabricación y 50% contra entrega o instalación. Puedes pagar con Yape, Plin, transferencia o efectivo.' };
  }
  if (containsAny(text, ['demora', 'tiempo', 'entrega', 'dias', 'cuando'])) {
    return { text: 'El tiempo depende del tipo y complejidad del mueble. Luego de confirmar medidas y anticipo te indicamos una fecha de entrega, y podrás seguir cada etapa desde material comprado hasta instalación.' };
  }
  if (containsAny(text, ['pedido', 'estado', 'seguimiento'])) {
    return { text: 'Escribe tu código de pedido, por ejemplo PED-001, y te mostraré su etapa de producción, fecha de entrega y estado de pago.' };
  }
  if (containsAny(text, ['whatsapp', 'contacto', 'asesor', 'persona', 'llamar'])) {
    return { text: 'Al terminar tu cotización encontrarás la opción “Enviar por WhatsApp”. Prepararé todos los detalles del proyecto en un mensaje para que un asesor continúe la atención.' };
  }
  if (containsAny(text, ['direccion', 'ubicacion', 'lima', 'donde'])) {
    return { text: 'Atendemos proyectos en Lima. La dirección de instalación se confirma al registrar el pedido y coordinamos la visita directamente contigo.' };
  }
  if (containsAny(text, ['catalogo', 'modelos', 'diseños', 'muebles'])) {
    return { text: 'Nuestro catálogo incluye cocinas, closets, centros de TV y escritorios. Todos los modelos pueden personalizarse según tu espacio.', action: { label: 'Ver catálogo', path: '/catalogo' } };
  }
  return { text: 'Puedo ayudarte con diseños, materiales, medidas, cotizaciones, pagos, entregas y seguimiento. También puedes escribir un código como PED-001 para consultar un pedido.' };
}

export function AIAssistant({ orders }: { orders: Order[] }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: 1, role: 'assistant', text: '¡Hola! Soy Mía, la asistente virtual de MuebleFlow. ¿Qué mueble tienes en mente?' },
  ]);
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages, thinking]);

  const send = (raw: string) => {
    const text = raw.trim();
    if (!text || thinking) return;
    setMessages((current) => [...current, { id: Date.now(), role: 'user', text }]);
    setInput('');
    setThinking(true);
    window.setTimeout(() => {
      setMessages((current) => [...current, { id: Date.now() + 1, role: 'assistant', ...smartReply(text, orders) }]);
      setThinking(false);
    }, 650);
  };

  return <div className="ai-assistant">
    {open && <section className="ai-chat" aria-label="Asistente virtual Mía">
      <header>
        <div className="ai-avatar">M</div>
        <div><strong>Mía · Asistente virtual</strong><span><i /> Disponible ahora</span></div>
        <button onClick={() => setOpen(false)} aria-label="Cerrar asistente">×</button>
      </header>
      <div className="ai-messages">
        {messages.map((message) => <div className={`ai-message ${message.role}`} key={message.id}>
          <p>{message.text}</p>
          {message.action && <button onClick={() => navigate(message.action!.path)}>{message.action.label} →</button>}
        </div>)}
        {thinking && <div className="ai-typing" aria-label="Mía está escribiendo"><i/><i/><i/></div>}
        <div ref={endRef}/>
      </div>
      <div className="ai-suggestions">{suggestions.map((item) => <button key={item} onClick={() => send(item)}>{item}</button>)}</div>
      <form onSubmit={(event) => { event.preventDefault(); send(input); }}>
        <input aria-label="Escribe tu consulta" value={input} onChange={(event) => setInput(event.target.value)} placeholder="Escribe tu consulta..." />
        <button type="submit" aria-label="Enviar mensaje">↑</button>
      </form>
    </section>}
    <button className="ai-launcher" onClick={() => setOpen((value) => !value)} aria-label={open ? 'Cerrar asistente virtual' : 'Abrir asistente virtual'}>
      {open ? '×' : <><span>✦</span><i /></>}
    </button>
  </div>;
}
