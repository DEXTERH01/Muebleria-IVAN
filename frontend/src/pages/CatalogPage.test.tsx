import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { listProducts } from '../api/modules/catalog';
import { CatalogPage } from './CatalogPage';

vi.mock('../api/modules/catalog', () => ({
  listProducts: vi.fn(),
}));

const mockedListProducts = vi.mocked(listProducts);

describe('CatalogPage', () => {
  beforeEach(() => {
    cleanup();
    mockedListProducts.mockReset();
  });

  it('renders products loaded from FastAPI', async () => {
    mockedListProducts.mockResolvedValue({
      items: [{
        id: '40000000-0000-4000-8000-000000000002',
        slug: 'escritorio-lima',
        name: 'Escritorio Lima',
        description: 'Escritorio compacto con cajonera.',
        category: 'Oficina',
        basePriceMinor: 78000,
        minProductionDays: 7,
        maxProductionDays: 12,
        primaryImage: null,
      }],
      page: 1,
      pageSize: 100,
      total: 1,
    });

    render(<CatalogPage />);

    expect(screen.getByRole('status')).toHaveTextContent('Cargando catálogo');
    expect(await screen.findByRole('heading', { name: 'Escritorio Lima' })).toBeInTheDocument();
    expect(screen.getByText(/Precio base/)).toHaveTextContent(/S\/\s*780/);
    expect(screen.getByRole('tab', { name: 'Oficina' })).toBeInTheDocument();
  });

  it('offers a retry when the API is unavailable', async () => {
    mockedListProducts.mockRejectedValue(new Error('Servicio no disponible'));

    render(<CatalogPage />);

    expect(await screen.findByRole('alert')).toHaveTextContent('Servicio no disponible');
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument();
  });

  it('paginates the public catalog after twelve designs', async () => {
    mockedListProducts.mockResolvedValue({
      items: Array.from({ length: 13 }, (_, index) => ({
        id: `40000000-0000-4000-8000-${String(index).padStart(12, '0')}`,
        slug: `diseno-${index + 1}`,
        name: `Diseño ${index + 1}`,
        description: 'Mueble personalizado.',
        category: 'Sala',
        basePriceMinor: 100000,
        minProductionDays: 7,
        maxProductionDays: 12,
        primaryImage: null,
      })),
      page: 1,
      pageSize: 100,
      total: 13,
    });

    render(<CatalogPage />);

    expect(await screen.findByRole('heading', { name: 'Diseño 12' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Diseño 13' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Página siguiente' }));
    expect(screen.getByRole('heading', { name: 'Diseño 13' })).toBeInTheDocument();
    expect(screen.getByText('13 diseños · Página 2 de 2')).toBeInTheDocument();
  });
});
