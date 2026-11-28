import { useEffect, useState, type FormEvent, type ReactNode } from 'react';

import { useAuth } from './AuthProvider';
import { Button } from '../components/ui';
import { Footer, Navbar, navigate } from '../components/layout';
import { BrandMark } from '../components/BrandMark';

type AuthMode = 'login' | 'register' | 'recovery' | 'update-password';

function safeRedirect(fallback: string): string {
  const target = new URLSearchParams(window.location.search).get('redirect');
  return target?.startsWith('/') && !target.startsWith('//') ? target : fallback;
}

export function AuthPage({ mode }: { mode: AuthMode }) {
  const auth = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      if (!auth?.configured) throw new Error('El inicio de sesión no está configurado todavía.');
      if (mode === 'login') {
        const profile = await auth.signIn(email.trim(), password);
        const destination = profile && (profile.role === 'admin' || profile.role === 'operator')
          ? '/admin'
          : '/mi-cuenta';
        navigate(safeRedirect(destination));
      } else if (mode === 'register') {
        const hasSession = await auth.signUp(email.trim(), password, fullName);
        setMessage(
          hasSession
            ? 'Tu cuenta está lista. Ya puedes consultar tus cotizaciones.'
            : 'Revisa tu correo y confirma la cuenta para iniciar sesión.',
        );
        if (hasSession) navigate('/mi-cuenta');
      } else if (mode === 'recovery') {
        await auth.requestPasswordReset(email.trim());
        setMessage('Si el correo está registrado, recibirás un enlace para recuperar el acceso.');
      } else {
        if (password !== confirmPassword) throw new Error('Las contraseñas no coinciden.');
        await auth.updatePassword(password);
        setMessage('Contraseña actualizada. Ya puedes continuar.');
        window.setTimeout(() => navigate('/mi-cuenta'), 900);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No pudimos completar la solicitud.');
    } finally {
      setBusy(false);
    }
  };

  const titles: Record<AuthMode, string> = {
    login: 'Inicia sesión',
    register: 'Crea tu cuenta',
    recovery: 'Recupera tu acceso',
    'update-password': 'Elige una contraseña nueva',
  };
  const descriptions: Record<AuthMode, string> = {
    login: 'Consulta tus cotizaciones y sigue tus proyectos desde un solo lugar.',
    register: 'Regístrate para consultar tus cotizaciones y proyectos.',
    recovery: 'Te enviaremos un enlace para crear una contraseña nueva.',
    'update-password': 'La contraseña debe tener al menos ocho caracteres.',
  };

  return (
    <>
      <Navbar />
      <main className="auth-page">
        <div className="auth-layout">
          <aside className="auth-showcase" aria-label="Beneficios del portal de Mueblería Iván">
            <div className="auth-showcase-brand">
              <span className="auth-showcase-logo" aria-hidden="true">
                <BrandMark animated />
              </span>
              <span>Mueblería Iván</span>
            </div>
            <div className="auth-showcase-copy">
              <span className="auth-showcase-kicker">TU PROYECTO, SIEMPRE A MANO</span>
              <h2>Del diseño a la entrega, todo en un solo lugar.</h2>
              <p>Consulta avances y decisiones de tu mueble con información clara y ordenada.</p>
            </div>
            <ul className="auth-benefits">
              <li><span>01</span><div><strong>Cotizaciones claras</strong><small>Revisa tus propuestas y detalles.</small></div></li>
              <li><span>02</span><div><strong>Seguimiento sencillo</strong><small>Conoce en qué etapa está tu proyecto.</small></div></li>
              <li><span>03</span><div><strong>Acceso protegido</strong><small>Tu información permanece vinculada a tu cuenta.</small></div></li>
            </ul>
            <p className="auth-showcase-note"><span aria-hidden="true">●</span> Portal seguro para clientes y equipo autorizado</p>
          </aside>
          <section className="auth-card">
            <div className="auth-card-heading">
              <span className="kicker">PORTAL MUEBLERÍA IVÁN</span>
              <h1>{titles[mode]}</h1>
              <p>{descriptions[mode]}</p>
            </div>
          {!auth?.configured && (
            <div className="form-error" role="alert">
              Configura <code>VITE_SUPABASE_URL</code> y <code>VITE_SUPABASE_ANON_KEY</code> para habilitar Supabase Auth.
            </div>
          )}
          {auth?.profileError && mode === 'login' && (
            <div className="form-error" role="alert">{auth.profileError}</div>
          )}
          <form className="auth-form" onSubmit={submit}>
            {mode === 'register' && (
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
            )}
            {(mode === 'login' || mode === 'register' || mode === 'recovery') && (
              <label>
                Correo electrónico
                <input
                  type="email"
                  autoComplete={mode === 'login' ? 'username' : 'email'}
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </label>
            )}
            {(mode === 'login' || mode === 'register' || mode === 'update-password') && (
              <label>
                {mode === 'update-password' ? 'Nueva contraseña' : 'Contraseña'}
                <span className="auth-password-field">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    minLength={8}
                    required
                  />
                  <button
                    type="button"
                    className="auth-password-toggle"
                    aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                    aria-pressed={showPassword}
                    onClick={() => setShowPassword((visible) => !visible)}
                  >
                    {showPassword ? 'Ocultar' : 'Mostrar'}
                  </button>
                </span>
              </label>
            )}
            {mode === 'update-password' && (
              <label>
                Repite la contraseña
                <span className="auth-password-field">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    minLength={8}
                    required
                  />
                </span>
              </label>
            )}
            {error && <div className="form-error" role="alert">{error}</div>}
            {message && <div className="form-success" role="status">{message}</div>}
            <Button type="submit" disabled={busy || !auth?.configured}>
              {busy ? 'Un momento…' : mode === 'login' ? 'Entrar' : mode === 'register' ? 'Crear cuenta' : mode === 'recovery' ? 'Enviar enlace' : 'Actualizar contraseña'}
            </Button>
          </form>
          <div className="auth-links">
            {mode === 'login' && <>
              <button onClick={() => navigate('/crear-cuenta')}>Crear cuenta</button>
              <button onClick={() => navigate('/recuperar-contrasena')}>Olvidé mi contraseña</button>
            </>}
            {mode === 'register' && <button onClick={() => navigate('/iniciar-sesion')}>Ya tengo una cuenta</button>}
            {mode === 'recovery' && <button onClick={() => navigate('/iniciar-sesion')}>Volver al inicio de sesión</button>}
          </div>
          </section>
        </div>
      </main>
      <Footer />
    </>
  );
}

export function AuthGuard({
  children,
  roles,
}: {
  children: ReactNode;
  roles: string[];
}) {
  const auth = useAuth();
  useEffect(() => {
    if (auth && !auth.loading && !auth.session) {
      navigate(`/iniciar-sesion?redirect=${encodeURIComponent(window.location.pathname)}`);
    }
  }, [auth]);
  if (!auth || auth.loading) {
    return <main className="auth-page"><p role="status">Comprobando tu sesión…</p></main>;
  }
  if (!auth.session) {
    return <main className="auth-page"><p role="status">Te llevamos al inicio de sesión…</p></main>;
  }
  if (!auth.profile && auth.profileError) {
    return (
      <main className="auth-page">
        <section className="auth-card" role="alert">
          <h1>No pudimos validar tu perfil</h1>
          <p>{auth.profileError}</p>
          <Button onClick={() => void auth.signOut().then(() => navigate('/iniciar-sesion'))}>
            Cerrar sesión
          </Button>
        </section>
      </main>
    );
  }
  if (!auth.profile) return <main className="auth-page"><p role="status">Cargando tu perfil…</p></main>;
  if (!roles.includes(auth.profile.role)) {
    return (
      <main className="auth-page">
        <section className="auth-card" role="alert">
          <h1>Esta sección no está disponible para tu cuenta</h1>
          <p>Tu perfil no tiene permiso para entrar aquí.</p>
          <Button onClick={() => navigate('/mi-cuenta')}>Ir a mi cuenta</Button>
        </section>
      </main>
    );
  }
  return <>{children}</>;
}
