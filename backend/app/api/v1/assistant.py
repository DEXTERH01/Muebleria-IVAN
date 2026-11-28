"""Public, rate-limited endpoint for Mía's generative fallback."""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.schemas.assistant import AssistantChatData, AssistantChatRequest, AssistantChatResponse
from app.services.assistant import AssistantProviderError, groq_reply

router = APIRouter(prefix="/assistant", tags=["assistant"])
_request_times: dict[str, deque[float]] = defaultdict(deque)
_rate_limit_lock = Lock()


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _check_rate_limit(client_key: str, limit: int) -> None:
    now = monotonic()
    with _rate_limit_lock:
        timestamps = _request_times[client_key]
        while timestamps and timestamps[0] <= now - 60:
            timestamps.popleft()
        if len(timestamps) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Has enviado demasiadas consultas. Inténtalo nuevamente en un minuto.",
            )
        timestamps.append(now)


@router.post("/chat", response_model=AssistantChatResponse)
def assistant_chat(
    payload: AssistantChatRequest,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AssistantChatResponse:
    _check_rate_limit(_client_key(request), settings.assistant_requests_per_minute)
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El asistente generativo no está configurado.",
        )
    try:
        message = groq_reply(
            payload.message,
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            timeout_seconds=settings.groq_timeout_seconds,
        )
    except AssistantProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mía no puede generar una respuesta en este momento.",
        ) from exc
    return AssistantChatResponse(
        data=AssistantChatData(message=message, provider="groq", model=settings.groq_model)
    )
