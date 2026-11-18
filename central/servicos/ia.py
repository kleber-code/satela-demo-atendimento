"""Cliente mínimo da Satela AI (API compatível com OpenAI), feito com httpx.

Nunca loga nem devolve a chave. Qualquer falha vira IAIndisponivel para o chamador
cair no fallback.
"""
import json

import httpx
from django.conf import settings

_transport = None  # os testes injetam httpx.MockTransport aqui; em produção fica None


class IAIndisponivel(Exception):
    pass


def configurada():
    return bool(settings.SATELA_API_KEY)


def _cliente():
    return httpx.Client(
        transport=_transport,
        timeout=httpx.Timeout(settings.IA_TIMEOUT, connect=5.0),
    )


def _headers():
    return {"Authorization": f"Bearer {settings.SATELA_API_KEY}", "Content-Type": "application/json"}


def _url(caminho):
    return settings.SATELA_API_URL.rstrip("/") + caminho


def chat(mensagens, tools=None, stream=None, temperature=0.3, max_tokens=None):
    """Chama /ai/v1/chat/completions. Retorna {'content': str, 'tool_calls': list}."""
    if not configurada():
        raise IAIndisponivel("sem chave")
    stream = settings.IA_STREAM if stream is None else stream
    corpo = {
        "model": settings.SATELA_MODEL,
        "messages": mensagens,
        "temperature": temperature,
        "max_tokens": max_tokens or settings.IA_MAX_TOKENS,
        "stream": bool(stream),
    }
    if tools:
        corpo["tools"] = tools
    try:
        with _cliente() as c:
            if not stream:
                r = c.post(_url("/ai/v1/chat/completions"), headers=_headers(), json=corpo)
                if r.status_code != 200:
                    raise IAIndisponivel(f"http {r.status_code}")
                msg = r.json()["choices"][0]["message"]
                return {"content": msg.get("content") or "", "tool_calls": msg.get("tool_calls") or []}
            return _consumir_stream(c, corpo)
    except IAIndisponivel:
        raise
    except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError) as e:
        raise IAIndisponivel(type(e).__name__) from e


def _consumir_stream(c, corpo):
    texto, chamadas = [], {}
    with c.stream("POST", _url("/ai/v1/chat/completions"), headers=_headers(), json=corpo) as r:
        if r.status_code != 200:
            raise IAIndisponivel(f"http {r.status_code}")
        for linha in r.iter_lines():
            if not linha.startswith("data:"):
                continue
            dado = linha[5:].strip()
            if dado == "[DONE]":
                break
            delta = json.loads(dado)["choices"][0].get("delta", {})
            if delta.get("content"):
                texto.append(delta["content"])
            for tc in delta.get("tool_calls") or []:
                slot = chamadas.setdefault(tc.get("index", 0), {"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                slot["id"] = tc.get("id") or slot["id"]
                f = tc.get("function") or {}
                slot["function"]["name"] += f.get("name") or ""
                slot["function"]["arguments"] += f.get("arguments") or ""
    return {"content": "".join(texto), "tool_calls": [chamadas[k] for k in sorted(chamadas)]}


def embeddings(textos):
    if not configurada():
        raise IAIndisponivel("sem chave")
    try:
        with _cliente() as c:
            r = c.post(
                _url("/ai/v1/embeddings"),
                headers=_headers(),
                json={"model": settings.SATELA_EMBED_MODEL, "input": textos},
            )
            if r.status_code != 200:
                raise IAIndisponivel(f"http {r.status_code}")
            return [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]
    except IAIndisponivel:
        raise
    except (httpx.HTTPError, KeyError, ValueError, TypeError) as e:
        raise IAIndisponivel(type(e).__name__) from e
