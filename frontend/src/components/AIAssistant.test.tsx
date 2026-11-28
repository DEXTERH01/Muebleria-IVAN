import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { chatWithAssistant } from '../api/modules/assistant';
import { listProducts } from '../api/modules/catalog';
import { AIAssistant } from './AIAssistant';

vi.mock('../api/modules/assistant', () => ({ chatWithAssistant: vi.fn() }));
vi.mock('../api/modules/catalog', () => ({ listProducts: vi.fn() }));

const mockedChatWithAssistant = vi.mocked(chatWithAssistant);
const mockedListProducts = vi.mocked(listProducts);
const ropero = {
  id: '40000000-0000-4000-8000-000000000001',
  slug: 'ropero-alba',
  name: 'Ropero Alba',
  description: 'Ropero de dos puertas con repisas ajustables.',
  category: 'Roperos',
  basePriceMinor: 129900,
  minProductionDays: 8,
  maxProductionDays: 14,
  primaryImage: null,
};

afterEach(cleanup);

describe('AIAssistant', () => {
  beforeEach(() => {
    mockedListProducts.mockReset();
    mockedChatWithAssistant.mockReset();
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
      configurable: true,
      value: vi.fn(() => Promise.resolve()),
    });
  });

  it('reintenta el catálogo en vivo cuando el primer intento falla', async () => {
    mockedListProducts
      .mockRejectedValueOnce(new Error('Render tardó en responder'))
      .mockResolvedValueOnce({ items: [ropero], page: 1, pageSize: 100, total: 1 });

    render(<AIAssistant orders={[]} />);
    fireEvent.click(screen.getByRole('button', { name: 'Abrir asistente virtual' }));
    expect(await screen.findByText('Catálogo sin conexión')).toBeInTheDocument();

    fireEvent.change(screen.getByRole('textbox', { name: 'Escribe tu consulta' }), {
      target: { value: 'Quiero un ropero' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar mensaje' }));

    expect(await screen.findByText(/precio base publicado de Ropero Alba/i)).toBeInTheDocument();
    expect(mockedListProducts).toHaveBeenCalledTimes(2);
  });

  it('abre el catálogo con una navegación normal si tampoco logra conectarse', async () => {
    mockedListProducts
      .mockRejectedValueOnce(new Error('Render tardó en responder'))
      .mockRejectedValueOnce(new Error('Servicio no disponible'));

    render(<AIAssistant orders={[]} />);
    fireEvent.click(screen.getByRole('button', { name: 'Abrir asistente virtual' }));
    expect(await screen.findByText('Catálogo sin conexión')).toBeInTheDocument();
    fireEvent.change(screen.getByRole('textbox', { name: 'Escribe tu consulta' }), {
      target: { value: 'Quiero un ropero' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar mensaje' }));

    const catalogLink = await screen.findByRole('link', { name: 'Abrir catálogo' });
    expect(catalogLink).toHaveAttribute('href', '/catalogo');
  });

  it('consulta Groq para una pregunta abierta y conserva el bot local como fallback', async () => {
    mockedListProducts.mockResolvedValue({ items: [ropero], page: 1, pageSize: 100, total: 1 });
    mockedChatWithAssistant.mockResolvedValue({
      message: 'Los tonos nogal combinan bien con paredes crema y aportan calidez.',
      provider: 'groq',
      model: 'openai/gpt-oss-20b',
    });

    render(<AIAssistant orders={[]} />);
    fireEvent.click(screen.getByRole('button', { name: 'Abrir asistente virtual' }));
    fireEvent.change(screen.getByRole('textbox', { name: 'Escribe tu consulta' }), {
      target: { value: '¿Qué color de madera combina con paredes crema?' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar mensaje' }));

    expect(await screen.findByText(/tonos nogal combinan bien/i)).toBeInTheDocument();
    expect(mockedChatWithAssistant).toHaveBeenCalledWith(
      '¿Qué color de madera combina con paredes crema?',
    );
  });
});
