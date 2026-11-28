import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { HomePage } from './HomePage';

describe('HomePage', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/');
  });

  it('presenta la marca y el acceso al catálogo', () => {
    render(<HomePage />);

    expect(screen.getByRole('button', { name: /Mueblería Iván.*DISEÑO A TU MEDIDA/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Tu espacio merece un mueble que sí encaje/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Explorar diseños' })).toBeInTheDocument();
  });
});
