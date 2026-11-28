import { useState, type FormEvent } from 'react';

import { inviteTeamMember, type TeamRole, type UserInvitation } from '../../api/modules/users';
import { AdminLayout } from '../../components/layout';
import { Button } from '../../components/ui';

const roleLabels: Record<TeamRole, string> = {
  admin: 'Administrador',
  operator: 'Operador',
  customer: 'Cliente',
};

export function TeamPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<TeamRole>('operator');
  const [sentInvitations, setSentInvitations] = useState<UserInvitation[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      const result = await inviteTeamMember({ fullName: fullName.trim(), email: email.trim(), role });
      const invitation = result.data;
      setSentInvitations((current) => [invitation, ...current]);
      setMessage(`Invitación enviada a ${invitation.email}. La persona definirá su contraseña desde el correo.`);
      setFullName('');
      setEmail('');
      setRole('operator');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No pudimos enviar la invitación.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <AdminLayout title="Equipo y accesos" subtitle="ADMINISTRACIÓN DE USUARIOS">
      <div className="team-page">
        <section className="admin-card team-invite-card">
          <div className="card-title">
            <div>
              <h2>Invitar a una persona</h2>
              <p>Enviaremos un enlace para que configure su propia contraseña.</p>
            </div>
          </div>
          <form className="team-invite-form" onSubmit={submit}>
            <label>
              Nombre completo
              <input
                autoComplete="name"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                minLength={2}
                maxLength={120}
                required
              />
            </label>
            <label>
              Correo electrónico
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                maxLength={254}
                required
              />
            </label>
            <label>
              Rol de acceso
              <select value={role} onChange={(event) => setRole(event.target.value as TeamRole)}>
                <option value="operator">Operador · pedidos y taller</option>
                <option value="admin">Administrador · acceso completo</option>
                <option value="customer">Cliente · cotizaciones propias</option>
              </select>
            </label>
            {error && <p className="form-error" role="alert">{error}</p>}
            {message && <p className="form-success" role="status">{message}</p>}
            <Button type="submit" disabled={busy}>
              {busy ? 'Enviando invitación…' : 'Enviar invitación'}
            </Button>
          </form>
          <p className="team-security-note">
            Asigna Administrador solo a personas que deban gestionar accesos, catálogo y cotizaciones.
          </p>
        </section>

        <section className="admin-card team-invitations-card">
          <div className="card-title">
            <div>
              <h2>Invitaciones enviadas en esta sesión</h2>
              <p>La lista se reinicia al cerrar o recargar esta página.</p>
            </div>
          </div>
          {sentInvitations.length === 0 ? (
            <p className="team-empty">Las invitaciones que envíes aparecerán aquí.</p>
          ) : (
            <ul className="team-invitation-list">
              {sentInvitations.map((invitation) => (
                <li key={invitation.email}>
                  <span className="team-avatar" aria-hidden="true">
                    {invitation.fullName.split(' ').slice(0, 2).map((part) => part[0]).join('').toUpperCase()}
                  </span>
                  <span className="team-person">
                    <strong>{invitation.fullName}</strong>
                    <small>{invitation.email}</small>
                  </span>
                  <span className="team-role">{roleLabels[invitation.role]}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </AdminLayout>
  );
}
