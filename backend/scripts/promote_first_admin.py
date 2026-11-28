"""Promote one confirmed Supabase Auth account to the first application admin.

Invite the person through Supabase Dashboard first. This one-time command is run
by the project owner from a trusted terminal with the database owner connection.
"""

import argparse
import sys

from sqlalchemy import create_engine, text

from app.core.config import Settings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email", help="Correo confirmado que ya aceptó la invitación")
    parser.add_argument("--full-name", required=True, help="Nombre que verá el equipo")
    args = parser.parse_args()

    email = args.email.strip().lower()
    full_name = " ".join(args.full_name.split())
    if not full_name or len(full_name) > 120:
        parser.error("El nombre debe tener entre 1 y 120 caracteres.")

    database_url = Settings().database_url
    if not database_url:
        print("Configura MUEBLERIA_DATABASE_URL en backend/.env.", file=sys.stderr)
        return 1

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            account = connection.execute(
                text(
                    """
                    select id
                    from auth.users
                    where lower(email) = :email and email_confirmed_at is not null
                    """
                ),
                {"email": email},
            ).one_or_none()
            if account is None:
                print(
                    "No existe una cuenta confirmada con ese correo. Invítala y acepta "
                    "el enlace antes de asignar el rol de administrador.",
                    file=sys.stderr,
                )
                return 1

            previous_role = connection.execute(
                text("select role::text from app.profiles where user_id = :user_id"),
                {"user_id": account.id},
            ).scalar_one_or_none()
            if previous_role is None:
                message = "La cuenta no tiene un perfil de aplicación; no se asignó el rol."
                print(message, file=sys.stderr)
                return 1

            profile = connection.execute(
                text(
                    """
                    update app.profiles
                    set role = 'admin', full_name = :full_name, active = true,
                        updated_at = timezone('utc', now())
                    where user_id = :user_id
                    returning role
                    """
                ),
                {"full_name": full_name, "user_id": account.id},
            ).one_or_none()
            if profile is None:
                message = "La cuenta no tiene un perfil de aplicación; no se asignó el rol."
                print(message, file=sys.stderr)
                return 1

            connection.execute(
                text(
                    """
                    insert into app.audit_logs (
                      actor_user_id, action, entity_type, entity_id,
                      old_values, new_values
                    ) values (
                      null, 'user.first_admin_promoted', 'user_role', :user_id,
                      jsonb_build_object('role', :previous_role),
                      '{"role":"admin"}'::jsonb
                    )
                    """
                ),
                {"user_id": account.id, "previous_role": previous_role},
            )
    finally:
        engine.dispose()

    print(f"Administrador inicial configurado para {email}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
