import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { listProducts } from '../api/modules/catalog';
import { AIAssistant } from './AIAssistant';

vi.mock('../api/modules/catalog', () => ({ listProducts: vi.fn() }));

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
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
      configurable: true,
      value: vi.fn(),
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
});
