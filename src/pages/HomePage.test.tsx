import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { HomePage } from './HomePage';

describe('HomePage', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/');
  });

  it('presenta la marca y el acceso al catálogo', () => {
    render(<HomePage />);

    expect(screen.getByRole('button', { name: /Mueblería Iván, ir al inicio/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Muebles hechos\s*para tu espacio/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Ver catálogo' })).toBeInTheDocument();
  });
});
