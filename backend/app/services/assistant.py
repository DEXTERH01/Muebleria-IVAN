"""Groq-backed advisory replies for Mía."""

from typing import Any

import httpx

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
SYSTEM_PROMPT = """Eres Mía, asistente virtual de Mueblería Iván en Perú.
Responde siempre en español claro, amable y breve, con un máximo de tres oraciones.
Solo orientas sobre muebles personalizados, medidas, materiales, cuidados, catálogo,
cotizaciones y el proceso de compra. Los precios publicados son bases referenciales en
soles peruanos y el importe final se calcula en el cotizador. La cotización dura siete
días y el esquema normal es 50% de anticipo y 50% antes de completar la entrega.
No inventes productos, precios, existencias, fechas de entrega ni estados de pedidos.
Los pedidos son privados: indica que se debe iniciar sesión para consultarlos.
No solicites contraseñas, datos bancarios ni información sensible. Si la pregunta queda
fuera de este alcance, explica brevemente en qué sí puedes ayudar."""


class AssistantProviderError(RuntimeError):
    """Raised when the external assistant provider cannot return a valid reply."""


def groq_reply(
    message: str,
    *,
    api_key: str,
    model: str,
    timeout_seconds: float,
) -> str:
    try:
        response = httpx.post(
            GROQ_CHAT_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                "temperature": 0.4,
                "max_completion_tokens": 220,
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        content = payload["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise AssistantProviderError("Groq no devolvió una respuesta válida.") from exc

    reply = str(content).strip()
    if not reply:
        raise AssistantProviderError("Groq devolvió una respuesta vacía.")
    return reply[:1200]
