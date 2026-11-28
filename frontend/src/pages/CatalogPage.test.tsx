import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { listProducts } from '../api/modules/catalog';
import { CatalogPage } from './CatalogPage';

vi.mock('../api/modules/catalog', () => ({
  listProducts: vi.fn(),
}));

const mockedListProducts = vi.mocked(listProducts);

describe('CatalogPage', () => {
  beforeEach(() => {
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
});
