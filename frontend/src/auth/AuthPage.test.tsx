import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { AuthPage, AuthGuard } from './AuthPage';
import { useAuth } from './AuthProvider';

vi.mock('./AuthProvider', () => ({
  useAuth: vi.fn(),
}));

const mockedUseAuth = vi.mocked(useAuth);
const signIn = vi.fn();

describe('Supabase Auth pages and role guard', () => {
  afterEach(cleanup);

  beforeEach(() => {
    window.history.replaceState({}, '', '/iniciar-sesion');
    signIn.mockReset();
    signIn.mockResolvedValue({ userId: 'user-id', role: 'customer' });
    mockedUseAuth.mockReturnValue({
      configured: true,
      loading: false,
      session: null,
      profile: null,
      profileError: null,
      signIn,
      signUp: vi.fn(),
      signOut: vi.fn(),
      requestPasswordReset: vi.fn(),
      updatePassword: vi.fn(),
    });
  });

  it('authenticates with the email and password then redirects to the customer portal', async () => {
    render(<AuthPage mode="login" />);

    expect(screen.queryByText('Vista admin')).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Correo electrónico'), {
      target: { value: 'ana@example.test' },
    });
    fireEvent.change(screen.getByLabelText('Contraseña'), {
      target: { value: 'clave-segura-123' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }));

    await waitFor(() => expect(signIn).toHaveBeenCalledWith('ana@example.test', 'clave-segura-123'));
    await waitFor(() => expect(window.location.pathname).toBe('/mi-cuenta'));
  });

  it('lets the user reveal and hide the password', () => {
    render(<AuthPage mode="login" />);

    const password = screen.getByLabelText('Contraseña');
    expect(password).toHaveAttribute('type', 'password');
    fireEvent.click(screen.getByRole('button', { name: 'Mostrar contraseña' }));
    expect(password).toHaveAttribute('type', 'text');
    fireEvent.click(screen.getByRole('button', { name: 'Ocultar contraseña' }));
    expect(password).toHaveAttribute('type', 'password');
  });

  it('redirects authorized staff to the administrative panel', async () => {
    signIn.mockResolvedValue({ userId: 'staff-id', role: 'admin' });
    render(<AuthPage mode="login" />);

    fireEvent.change(screen.getByLabelText('Correo electrónico'), {
      target: { value: 'admin@example.test' },
    });
    fireEvent.change(screen.getByLabelText('Contraseña'), {
      target: { value: 'clave-segura-123' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }));

    await waitFor(() => expect(window.location.pathname).toBe('/admin'));
  });

  it('does not render protected content for a role without permission', () => {
    mockedUseAuth.mockReturnValue({
      configured: true,
      loading: false,
      session: { access_token: 'token' } as never,
      profile: { userId: 'user-id', role: 'customer' },
      profileError: null,
      signIn,
      signUp: vi.fn(),
      signOut: vi.fn(),
      requestPasswordReset: vi.fn(),
      updatePassword: vi.fn(),
    });

    render(<AuthGuard roles={['admin', 'operator']}><div>Contenido privado</div></AuthGuard>);

    expect(screen.queryByText('Contenido privado')).not.toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Tu perfil no tiene permiso');
  });
});
