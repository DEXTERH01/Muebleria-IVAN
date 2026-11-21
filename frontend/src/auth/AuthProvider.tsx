import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { Session } from '@supabase/supabase-js';

import type { components } from '../api/generated/schema';
import { apiRequest, setAccessTokenProvider } from '../api/client/http';
import { isSupabaseConfigured, supabase } from '../api/client/supabase';

export type UserProfile = components['schemas']['MeData'];

export interface AuthContextValue {
  configured: boolean;
  loading: boolean;
  session: Session | null;
  profile: UserProfile | null;
  profileError: string | null;
  signIn(email: string, password: string): Promise<void>;
  signUp(email: string, password: string, fullName: string): Promise<boolean>;
  signOut(): Promise<void>;
  requestPasswordReset(email: string): Promise<void>;
  updatePassword(password: string): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);
type MeResponse = components['schemas']['MeResponse'];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }
    let active = true;
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (active) setSession(nextSession);
    });
    supabase.auth.getSession()
      .then(({ data, error }) => {
        if (error) throw error;
        if (active) setSession(data.session);
      })
      .catch((error: unknown) => {
        if (active) setProfileError(error instanceof Error ? error.message : 'No pudimos leer tu sesión.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, []);

  useEffect(() => {
    if (!session) {
      setProfile(null);
      setProfileError(null);
      return;
    }
    let active = true;
    setProfile(null);
    setProfileError(null);
    apiRequest<MeResponse>('/api/v1/auth/me', {
      headers: { Authorization: `Bearer ${session.access_token}` },
    })
      .then(({ data }) => {
        if (active) setProfile(data);
      })
      .catch((error: unknown) => {
        if (active) {
          setProfileError(
            error instanceof Error
              ? error.message
              : 'No pudimos validar tu perfil. Inténtalo nuevamente.',
          );
        }
      });
    return () => {
      active = false;
    };
  }, [session]);

  useEffect(() => {
    setAccessTokenProvider(() => session?.access_token ?? null);
    return () => setAccessTokenProvider(null);
  }, [session]);

  const value = useMemo<AuthContextValue>(() => ({
    configured: isSupabaseConfigured,
    loading,
    session,
    profile,
    profileError,
    async signIn(email, password) {
      if (!supabase) throw new Error('Configura Supabase para habilitar el inicio de sesión.');
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
    },
    async signUp(email, password, fullName) {
      if (!supabase) throw new Error('Configura Supabase para habilitar el registro.');
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: { data: { full_name: fullName.trim() } },
      });
      if (error) throw error;
      return Boolean(data.session);
    },
    async signOut() {
      if (!supabase) return;
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
    },
    async requestPasswordReset(email) {
      if (!supabase) throw new Error('Configura Supabase para recuperar el acceso.');
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/restablecer-contrasena`,
      });
      if (error) throw error;
    },
    async updatePassword(password) {
      if (!supabase) throw new Error('Configura Supabase para actualizar la contraseña.');
      const { error } = await supabase.auth.updateUser({ password });
      if (error) throw error;
    },
  }), [loading, session, profile, profileError]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue | null {
  return useContext(AuthContext);
}
