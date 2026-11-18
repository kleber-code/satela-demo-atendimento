import json

import httpx
from django.test import TestCase, override_settings

from central.models import Artigo, Configuracao, Pedido
from central.servicos import ia

CHAVE = "chave-secreta-de-teste-123"


class SemRedeReal:
    """Qualquer chamada HTTP não mockada derruba o teste: nunca falamos com a API real."""

    def __call__(self, request):
        raise AssertionError(f"Chamada HTTP real bloqueada nos testes: {request.url}")


def resposta_chat(content="", tool_calls=None):
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"choices": [{"message": msg}]}


def tool_call(nome, args, id_="call_1"):
    return {"id": id_, "type": "function", "function": {"name": nome, "arguments": json.dumps(args)}}


class BaseTest(TestCase):
    def setUp(self):
        self.chamadas = []
        self._fila = []
        ia._transport = httpx.MockTransport(SemRedeReal())
        Configuracao.carregar()
        self.artigo = Artigo.objects.create(
            titulo="Prazos e frete de entrega", categoria="Entrega",
            palavras_chave="prazo, entrega, frete, interior",
            conteudo="Capitais: 2 a 5 dias úteis. Interior: de 5 a 10 dias úteis.",
        )
        Pedido.objects.create(
            numero="AUR-10421", cliente_nome="Fulana", itens="Air Fryer", valor=100, status="em_rota", rastreio="AN1BR"
        )

    def tearDown(self):
        ia._transport = None

    def mock_ia(self, *respostas, status=200):
        """Enfileira respostas da IA (dicts) para as próximas chamadas; registra o que foi enviado."""
        fila = list(respostas)

        def handler(request):
            self.chamadas.append(json.loads(request.content))
            if status != 200:
                return httpx.Response(status, json={"erro": "x"})
            item = fila.pop(0) if len(fila) > 1 else fila[0]
            return httpx.Response(200, json=item)

        ia._transport = httpx.MockTransport(handler)


com_chave = override_settings(SATELA_API_KEY=CHAVE)
