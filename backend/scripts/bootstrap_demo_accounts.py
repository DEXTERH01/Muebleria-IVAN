"""Create or refresh the demo users in Supabase Auth and assign app roles."""

import base64
import binascii
import getpass
import json
import sys
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import BACKEND_DIR, Settings
from app.models.profile import Profile

AUTH_ACCOUNTS = (
    ("admin.demo@example.com", "Administrador Demo", "admin"),
    ("operador.demo@example.com", "Operador Demo", "operator"),
    ("cliente.ana.demo@example.com", "Ana Cliente Demo", "customer"),
    ("cliente.luis.demo@example.com", "Luis Cliente Demo", "customer"),
)
PAGE_SIZE = 1000


class BootstrapSettings(BaseSettings):
    supabase_service_role_key: SecretStr | None = None
    demo_bootstrap_password: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        env_prefix="MUEBLERIA_",
        case_sensitive=False,
        extra="ignore",
    )


@dataclass(frozen=True)
class DemoAccount:
    email: str
    full_name: str
    role: str
    user_id: UUID


class BootstrapError(RuntimeError):
    """A safe-to-display bootstrap error that never contains a secret."""


def _error_message(body: bytes) -> str:
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "respuesta no válida"
    message = payload.get("msg") or payload.get("message") or payload.get("error")
    if isinstance(message, str):
        return message[:300]
    return "error sin detalle"


def _request_json(
    method: str,
    url: str,
    service_key: str,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=body,
        method=method,
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read())
    except HTTPError as exc:
        raise BootstrapError(
            f"Supabase Auth respondió HTTP {exc.code}: {_error_message(exc.read())}"
        ) from None
    except URLError as exc:
        raise BootstrapError(f"No se pudo conectar con Supabase Auth: {exc.reason}") from None
    except TimeoutError:
        raise BootstrapError("Se agotó el tiempo de conexión con Supabase Auth.") from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise BootstrapError("Supabase Auth devolvió una respuesta no válida.") from None
    if not isinstance(result, dict):
        raise BootstrapError("Supabase Auth devolvió una respuesta no válida.")
    return result


def _validate_service_key(service_key: str) -> None:
    if service_key.startswith("sb_publishable_"):
        raise BootstrapError(
            "La clave configurada es publicable. Usa la clave secreta de Supabase "
            "(sb_secret_...) o la antigua service_role."
        )
    parts = service_key.split(".")
    if len(parts) == 3:
        try:
            payload = parts[1] + "=" * (-len(parts[1]) % 4)
            claims = json.loads(base64.urlsafe_b64decode(payload))
        except (ValueError, binascii.Error, json.JSONDecodeError):
            raise BootstrapError("La clave JWT de Supabase no es válida.") from None
        if not isinstance(claims, dict) or claims.get("role") != "service_role":
            raise BootstrapError("El JWT configurado no tiene el rol service_role.")
    elif not service_key.startswith("sb_secret_"):
        raise BootstrapError(
            "Formato de clave no reconocido. Configura una clave secreta de Supabase."
        )


def _list_users(auth_url: str, service_key: str) -> dict[str, dict[str, object]]:
    users_by_email: dict[str, dict[str, object]] = {}
    page = 1
    while True:
        query = urlencode({"page": page, "per_page": PAGE_SIZE})
        response = _request_json("GET", f"{auth_url}/admin/users?{query}", service_key)
        users = response.get("users")
        if not isinstance(users, list):
            raise BootstrapError("Supabase Auth no devolvió su lista de usuarios.")
        for user in users:
            if isinstance(user, dict) and isinstance(user.get("email"), str):
                users_by_email[user["email"].casefold()] = user
        if len(users) < PAGE_SIZE:
            return users_by_email
        page += 1


def _upsert_auth_account(
    auth_url: str,
    service_key: str,
    password: str,
    email: str,
    full_name: str,
    users_by_email: dict[str, dict[str, object]],
) -> UUID:
    payload: dict[str, object] = {
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"full_name": full_name},
    }
    existing = users_by_email.get(email.casefold())
    if existing:
        user_id = existing.get("id")
        if not isinstance(user_id, str):
            raise BootstrapError(f"Supabase Auth devolvió un ID inválido para {email}.")
        response = _request_json(
            "PUT", f"{auth_url}/admin/users/{user_id}", service_key, payload
        )
    else:
        response = _request_json("POST", f"{auth_url}/admin/users", service_key, payload)

    response_id = response.get("id")
    if not isinstance(response_id, str):
        raise BootstrapError(f"Supabase Auth no confirmó la cuenta {email}.")
    return UUID(response_id)


def _synchronize_profiles(database_url: str, accounts: list[DemoAccount]) -> None:
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with Session(engine) as session, session.begin():
            for account in accounts:
                profile = session.get(Profile, account.user_id)
                if profile is None:
                    profile = Profile(user_id=account.user_id)
                    session.add(profile)
                profile.role = account.role
                profile.full_name = account.full_name
                profile.active = True
    finally:
        engine.dispose()


def _upsert_accounts_through_database(
    database_url: str, password: str
) -> list[DemoAccount]:
    """Recovery path when Auth Admin is unavailable; keep users and identities consistent."""
    engine = create_engine(database_url, pool_pre_ping=True)
    accounts: list[DemoAccount] = []
    try:
        with engine.begin() as connection:
            for email, full_name, role in AUTH_ACCOUNTS:
                user_id = connection.scalar(
                    text("select id from auth.users where lower(email) = lower(:email)"),
                    {"email": email},
                )
                if user_id is None:
                    user_id = uuid4()
                    connection.execute(
                        text(
                            """
                            insert into auth.users (
                              instance_id, id, aud, role, email, encrypted_password,
                              email_confirmed_at, confirmation_token, recovery_token,
                              email_change_token_new, email_change, raw_app_meta_data,
                              raw_user_meta_data, created_at, updated_at
                            )
                            values (
                              '00000000-0000-0000-0000-000000000000', :user_id,
                              'authenticated', 'authenticated', :email,
                              extensions.crypt(:password, extensions.gen_salt('bf')),
                              timezone('utc', now()), '', '', '', '',
                              cast(:app_metadata as jsonb), cast(:user_metadata as jsonb),
                              timezone('utc', now()), timezone('utc', now())
                            )
                            """
                        ),
                        {
                            "user_id": user_id,
                            "email": email,
                            "password": password,
                            "app_metadata": json.dumps(
                                {"provider": "email", "providers": ["email"]}
                            ),
                            "user_metadata": json.dumps({"full_name": full_name}),
                        },
                    )
                else:
                    connection.execute(
                        text(
                            """
                            update auth.users
                            set encrypted_password =
                                  extensions.crypt(:password, extensions.gen_salt('bf')),
                                email_confirmed_at =
                                  coalesce(email_confirmed_at, timezone('utc', now())),
                                raw_app_meta_data = cast(:app_metadata as jsonb),
                                raw_user_meta_data = cast(:user_metadata as jsonb),
                                updated_at = timezone('utc', now()),
                                deleted_at = null,
                                banned_until = null
                            where id = :user_id
                            """
                        ),
                        {
                            "user_id": user_id,
                            "password": password,
                            "app_metadata": json.dumps(
                                {"provider": "email", "providers": ["email"]}
                            ),
                            "user_metadata": json.dumps({"full_name": full_name}),
                        },
                    )

                connection.execute(
                    text(
                        """
                        insert into auth.identities (
                          provider_id, user_id, identity_data, provider,
                          last_sign_in_at, created_at, updated_at
                        )
                        values (
                          cast(:user_id as text), :user_id,
                          cast(:identity_data as jsonb), 'email',
                          timezone('utc', now()), timezone('utc', now()),
                          timezone('utc', now())
                        )
                        on conflict (provider_id, provider) do update
                        set user_id = excluded.user_id,
                            identity_data = excluded.identity_data,
                            updated_at = timezone('utc', now())
                        """
                    ),
                    {
                        "user_id": user_id,
                        "identity_data": json.dumps({"sub": str(user_id), "email": email}),
                    },
                )
                connection.execute(
                    text(
                        """
                        insert into app.profiles (user_id, full_name, role, active)
                        values (:user_id, :full_name, cast(:role as app.user_role), true)
                        on conflict (user_id) do update
                        set full_name = excluded.full_name,
                            role = excluded.role,
                            active = true,
                            updated_at = timezone('utc', now())
                        """
                    ),
                    {"user_id": user_id, "full_name": full_name, "role": role},
                )
                accounts.append(
                    DemoAccount(
                        email=email,
                        full_name=full_name,
                        role=role,
                        user_id=user_id,
                    )
                )
    finally:
        engine.dispose()
    return accounts


def main() -> int:
    database_auth = sys.argv[1:] == ["--database-auth"]
    if sys.argv[1:] and not database_auth:
        raise BootstrapError("Uso: bootstrap_demo_accounts.py [--database-auth]")

    project = Settings()
    if not project.supabase_url:
        raise BootstrapError("Configura MUEBLERIA_SUPABASE_URL en backend/.env.")
    if not project.database_url:
        raise BootstrapError("Configura MUEBLERIA_DATABASE_URL en backend/.env.")

    secrets = BootstrapSettings()
    password = (
        secrets.demo_bootstrap_password.get_secret_value()
        if secrets.demo_bootstrap_password
        else getpass.getpass("Contraseña común para las cuentas demo (no se mostrará): ")
    )

    if not password:
        raise BootstrapError("La contraseña de demo es obligatoria.")
    if len(password) < 8:
        raise BootstrapError("La contraseña de demo debe tener al menos 8 caracteres.")

    if database_auth:
        accounts = _upsert_accounts_through_database(project.database_url, password)
    else:
        service_key = (
            secrets.supabase_service_role_key.get_secret_value()
            if secrets.supabase_service_role_key
            else getpass.getpass("Clave secreta de Supabase (no se mostrará): ")
        )
        if not service_key:
            raise BootstrapError("La clave secreta de Supabase es obligatoria.")
        _validate_service_key(service_key)
        auth_url = f"{project.supabase_url.rstrip('/')}/auth/v1"
        users_by_email = _list_users(auth_url, service_key)
        accounts = [
            DemoAccount(
                email=email,
                full_name=full_name,
                role=role,
                user_id=_upsert_auth_account(
                    auth_url,
                    service_key,
                    password,
                    email,
                    full_name,
                    users_by_email,
                ),
            )
            for email, full_name, role in AUTH_ACCOUNTS
        ]
        _synchronize_profiles(project.database_url, accounts)

    print("Cuentas de demo listas en Supabase Auth y app.profiles:")
    for account in accounts:
        print(f"- {account.email} — {account.role}")
    print("La contraseña común se ingresó de forma oculta o mediante la variable temporal.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BootstrapError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
