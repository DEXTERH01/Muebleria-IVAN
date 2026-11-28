"""Invite team members through Supabase Auth and assign their application role."""

from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.audit_log import AuditLog
from app.models.profile import Profile


class UserInvitationError(Exception):
    """An invitation failure with a safe message suitable for an API response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


async def invite_user(
    *,
    email: str,
    full_name: str,
    role: str,
    actor_user_id: UUID | None,
    session: Session,
    settings: Settings,
) -> dict[str, str]:
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise UserInvitationError(
            503,
            "Las invitaciones no están configuradas en el servidor.",
        )

    secret_key = settings.supabase_secret_key.get_secret_value()
    invite_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/invite"
    headers = {
        "apikey": secret_key,
        "Authorization": f"Bearer {secret_key}",
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                invite_url,
                params={"redirect_to": settings.supabase_invite_redirect_url},
                headers=headers,
                json={"email": email, "data": {"full_name": full_name}},
            )
    except httpx.HTTPError as error:
        raise UserInvitationError(
            502,
            "No pudimos conectar con el servicio de invitaciones.",
        ) from error

    if response.status_code in {400, 422}:
        raise UserInvitationError(
            409,
            "No se pudo invitar ese correo. Verifica que no tenga ya una cuenta.",
        )
    if response.status_code >= 400:
        raise UserInvitationError(
            502,
            "El servicio de correo no pudo enviar la invitación.",
        )

    try:
        user_id = UUID(response.json()["id"])
    except (ValueError, KeyError, TypeError):
        raise UserInvitationError(
            502,
            "La invitación se envió, pero no pudimos completar el perfil.",
        ) from None

    profile = session.get(Profile, user_id)
    if profile is None:
        raise UserInvitationError(
            502,
            "La invitación se envió, pero no pudimos completar el perfil.",
        )

    previous_role = profile.role
    profile.role = role
    profile.full_name = full_name
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action="user.invited",
            entity_type="user_role",
            entity_id=user_id,
            old_values={"role": previous_role},
            new_values={"role": role},
        )
    )
    session.commit()
    return {"email": email, "full_name": full_name, "role": role}
