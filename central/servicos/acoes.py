"""Funções (tools) que o bot pode chamar. Cada uma devolve um dict serializável."""
import json
import re
from datetime import datetime, timedelta

from django.utils import timezone

from ..models import Agendamento, Chamado, Pedido

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_pedido",
            "description": "Consulta o status, a previsão de entrega e o código de rastreio de um pedido pelo número (ex.: AUR-10421).",
            "parameters": {
                "type": "object",
                "properties": {"numero": {"type": "string", "description": "Número do pedido, formato AUR-12345"}},
                "required": ["numero"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "agendar",
            "description": "Agenda retirada na loja ou visita técnica. Pergunte tipo, data e período ao cliente antes de chamar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["retirada", "visita_tecnica"]},
                    "data": {"type": "string", "description": "Data no formato AAAA-MM-DD"},
                    "periodo": {"type": "string", "enum": ["manha", "tarde"]},
                    "referencia": {"type": "string", "description": "Número do pedido ou assunto, opcional"},
                },
                "required": ["tipo", "data", "periodo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "abrir_chamado",
            "description": "Abre um chamado para o time de suporte (defeito, problema que o bot não resolve).",
            "parameters": {
                "type": "object",
                "properties": {
                    "assunto": {"type": "string"},
                    "descricao": {"type": "string"},
                    "prioridade": {"type": "string", "enum": ["baixa", "normal", "alta"]},
                },
                "required": ["assunto", "descricao"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transferir_humano",
            "description": "Transfere a conversa para um atendente humano. Use quando não houver resposta nos artigos, o cliente pedir ou estiver insatisfeito.",
            "parameters": {
                "type": "object",
                "properties": {"motivo": {"type": "string"}},
                "required": ["motivo"],
            },
        },
    },
]

ROTULOS = {
    "consultar_pedido": "Consultou pedido",
    "agendar": "Agendou",
    "abrir_chamado": "Abriu chamado",
    "transferir_humano": "Transferiu para humano",
}
RE_PEDIDO = re.compile(r"\bAUR[-\s]?(\d{4,6})\b", re.I)


def extrair_numero_pedido(texto):
    m = RE_PEDIDO.search(texto or "")
    return f"AUR-{m.group(1)}" if m else None


def consultar_pedido(numero="", **_):
    numero = (numero or "").strip().upper().replace(" ", "")
    if re.fullmatch(r"AUR\d{4,6}", numero):
        numero = "AUR-" + numero[3:]
    p = Pedido.objects.filter(numero=numero).first()
    if not p:
        return {"ok": False, "erro": f"Pedido {numero or '(vazio)'} não encontrado."}
    return {
        "ok": True,
        "numero": p.numero,
        "status": p.get_status_display(),
        "itens": p.itens,
        "previsao_entrega": p.previsao_entrega.strftime("%d/%m/%Y") if p.previsao_entrega else None,
        "rastreio": p.rastreio or None,
    }


def agendar(conversa=None, tipo="", data="", periodo="manha", referencia="", **_):
    if tipo not in ("retirada", "visita_tecnica"):
        return {"ok": False, "erro": "Tipo inválido: use retirada ou visita_tecnica."}
    if periodo not in ("manha", "tarde"):
        periodo = "manha"
    try:
        d = datetime.strptime(str(data)[:10], "%Y-%m-%d").date()
    except ValueError:
        return {"ok": False, "erro": "Data inválida. Use AAAA-MM-DD."}
    hoje = timezone.localdate()
    if d <= hoje or d > hoje + timedelta(days=30):
        return {"ok": False, "erro": "Escolha uma data entre amanhã e os próximos 30 dias."}
    if d.weekday() == 6:
        return {"ok": False, "erro": "Não atendemos aos domingos."}
    a = Agendamento.objects.create(
        conversa=conversa, tipo=tipo, data=d, periodo=periodo, referencia=str(referencia or "")[:120]
    )
    return {
        "ok": True,
        "id": a.pk,
        "tipo": a.get_tipo_display(),
        "data": d.strftime("%d/%m/%Y"),
        "periodo": "manhã" if periodo == "manha" else "tarde",
        "unidade": a.unidade,
    }


def abrir_chamado(conversa=None, assunto="", descricao="", prioridade="normal", **_):
    assunto = str(assunto or "").strip()[:160]
    if not assunto:
        return {"ok": False, "erro": "Assunto obrigatório."}
    if prioridade not in ("baixa", "normal", "alta"):
        prioridade = "normal"
    c = Chamado.objects.create(
        conversa=conversa, assunto=assunto, descricao=str(descricao or "")[:1000], prioridade=prioridade
    )
    return {"ok": True, "protocolo": c.protocolo, "prioridade": prioridade}


def executar(nome, argumentos, conversa):
    """Executa uma tool com argumentos vindos da IA (json em string ou dict). Nunca lança."""
    if isinstance(argumentos, str):
        try:
            argumentos = json.loads(argumentos or "{}")
        except ValueError:
            argumentos = {}
    if not isinstance(argumentos, dict):
        argumentos = {}
    argumentos.pop("conversa", None)
    try:
        if nome == "consultar_pedido":
            return consultar_pedido(**argumentos)
        if nome == "agendar":
            return agendar(conversa=conversa, **argumentos)
        if nome == "abrir_chamado":
            return abrir_chamado(conversa=conversa, **argumentos)
    except TypeError:
        return {"ok": False, "erro": "Argumentos inválidos."}
    return {"ok": False, "erro": "Função desconhecida."}


def resumo_acao(nome, resultado):
    """Texto curto para o chip da conversa."""
    if not resultado.get("ok"):
        return f"{ROTULOS.get(nome, nome)}: {resultado.get('erro', 'falhou')}"
    if nome == "consultar_pedido":
        return f"Pedido {resultado['numero']}: {resultado['status']}"
    if nome == "agendar":
        return f"{resultado['tipo']} em {resultado['data']} ({resultado['periodo']})"
    if nome == "abrir_chamado":
        return f"Chamado {resultado['protocolo']} aberto"
    return ROTULOS.get(nome, nome)
