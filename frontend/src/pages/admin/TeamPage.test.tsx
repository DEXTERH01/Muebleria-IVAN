import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { inviteTeamMember } from '../../api/modules/users';
import { TeamPage } from './TeamPage';

vi.mock('../../api/modules/users', () => ({ inviteTeamMember: vi.fn() }));
vi.mock('../../components/layout', () => ({
  AdminLayout: ({ children, title }: { children: React.ReactNode; title: string }) => (
    <main><h1>{title}</h1>{children}</main>
  ),
}));

const mockedInvite = vi.mocked(inviteTeamMember);

describe('TeamPage', () => {
  afterEach(cleanup);
  beforeEach(() => mockedInvite.mockReset());

  it('sends an invitation with the selected role and shows confirmation', async () => {
    mockedInvite.mockResolvedValue({
      data: { email: 'ana@example.com', fullName: 'Ana López', role: 'operator' },
      message: 'Invitación enviada por correo.',
    });
    render(<TeamPage />);

    fireEvent.change(screen.getByLabelText('Nombre completo'), { target: { value: 'Ana López' } });
    fireEvent.change(screen.getByLabelText('Correo electrónico'), { target: { value: 'ana@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar invitación' }));

    await waitFor(() => expect(mockedInvite).toHaveBeenCalledWith({
      fullName: 'Ana López',
      email: 'ana@example.com',
      role: 'operator',
    }));
    expect(await screen.findByRole('status')).toHaveTextContent(/Invitación enviada a ana@example\.com/);
    expect(screen.getByText('Operador')).toBeInTheDocument();
  });

  it('keeps the form data and shows an invitation error', async () => {
    mockedInvite.mockResolvedValue(undefined as never);
    render(<TeamPage />);

    fireEvent.change(screen.getByLabelText('Nombre completo'), { target: { value: 'Ana López' } });
    fireEvent.change(screen.getByLabelText('Correo electrónico'), { target: { value: 'ana@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar invitación' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/data/);
    expect(screen.getByLabelText('Nombre completo')).toHaveValue('Ana López');
  });
});
