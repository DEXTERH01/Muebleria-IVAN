import { useEffect, useRef, useState } from 'react';
import { navigate } from './layout';

interface ChatMessage {
  id: number;
  role: 'assistant' | 'user';
  text: string;
  action?: { label: string; path: string };
}

const suggestions = ['Quiero cotizar un closet', '¿Qué material me conviene?', 'Consultar mi pedido'];

function smartReply(input: string): Omit<ChatMessage, 'id' | 'role'> {
  const text = input.toLowerCase();
  if (text.includes('closet') || text.includes('cotiz')) {
    return { text: 'Puedo ayudarte. Para una estimación necesito ancho, alto y profundidad. También podrás elegir material, color y accesorios.', action: { label: 'Abrir cotizador', path: '/cotizador?producto=closet-siena' } };
  }
  if (text.includes('material') || text.includes('melamina') || text.includes('mdf')) {
    return { text: 'Para uso diario recomiendo melamina de 18 mm. La melamina premium ofrece mejores acabados; el MDF es ideal cuando buscas superficies pintadas o detalles especiales.' };
  }
  if (text.includes('pedido') || text.includes('estado') || text.includes('seguimiento')) {
    return { text: 'En esta demostración puedes revisar el pedido PED-001 de María López desde el panel. Actualmente se encuentra en armado.', action: { label: 'Ver pedido de demostración', path: '/admin/pedido/PED-001' } };
  }
  if (text.includes('precio') || text.includes('cuánto') || text.includes('cuanto')) {
    return { text: 'El precio depende de medidas, material y accesorios. Nuestro cotizador genera una referencia y separa automáticamente el 50% de anticipo y el 50% contra entrega.', action: { label: 'Calcular precio', path: '/cotizador' } };
  }
  if (text.includes('whatsapp') || text.includes('contact')) {
    return { text: 'Al terminar una cotización generaré un mensaje listo para copiar y enviar por WhatsApp, sin usar ningún número real en este prototipo.' };
  }
  return { text: 'Puedo orientarte sobre diseños, materiales, precios referenciales y seguimiento de pedidos. Prueba preguntándome por un closet o por melamina.' };
}

export function AIAssistant() {
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
      setMessages((current) => [...current, { id: Date.now() + 1, role: 'assistant', ...smartReply(text) }]);
      setThinking(false);
    }, 650);
  };

  return <div className="ai-assistant">
    {open && <section className="ai-chat" aria-label="Asistente virtual simulado">
      <header>
        <div className="ai-avatar">M</div>
        <div><strong>Mía · Asistente virtual</strong><span><i /> Disponible ahora</span></div>
        <button onClick={() => setOpen(false)} aria-label="Cerrar asistente">×</button>
      </header>
      <div className="ai-demo-note"><span>✦</span> Demostración de IA · Respuestas simuladas</div>
      <div className="ai-messages">
        {messages.map((message) => <div className={`ai-message ${message.role}`} key={message.id}>
          <p>{message.text}</p>
          {message.action && <button onClick={() => navigate(message.action!.path)}>{message.action.label} →</button>}
        </div>)}
        {thinking && <div className="ai-typing" aria-label="Mía está escribiendo"><i/><i/><i/></div>}
        <div ref={endRef}/>
      </div>
      {messages.length < 3 && <div className="ai-suggestions">{suggestions.map((item) => <button key={item} onClick={() => send(item)}>{item}</button>)}</div>}
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
